#!/usr/bin/env python3
"""Check a built wheel in a fresh offline venv, never importing the checkout.

Usage: python scripts/check_wheel_metadata.py path/to/materials_boundaries-*.whl
Uses only the standard library plus the venv's bundled pip for installation.
"""
import argparse
import ast
from email.parser import Parser
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import venv
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def literal_version(source):
    assignments = [node for node in ast.parse(source).body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "__version__"
                           for target in node.targets)]
    require(len(assignments) == 1, "expected one software version assignment")
    version = ast.literal_eval(assignments[0].value)
    require(isinstance(version, str) and bool(version), "expected a nonempty literal version")
    return version


def check_metadata(metadata, expected):
    require(metadata["Name"] == "materials-boundaries", "wrong wheel project")
    require(metadata["Version"] == expected, "wheel METADATA version differs from source literal")
    # The only supported dependencies are the explicit dev extra. Fail closed
    # on other or compound markers, including platform-specific runtime deps;
    # --no-deps alone would hide an accidental dependency declaration.
    for requirement in metadata.get_all("Requires-Dist", []):
        _, separator, marker = requirement.partition(";")
        require(separator and re.fullmatch(r'''\s*extra\s*==\s*(['"])dev\1\s*''', marker),
                "wheel declares a non-dev dependency: " + requirement)


INSTALLED_CHECK = r'''
from contextlib import redirect_stdout
from importlib.metadata import distribution
import io
import json
from pathlib import Path
import sys

import materials_boundaries as package
from materials_boundaries.catalog import read_catalog
from materials_boundaries.cli import main
from materials_boundaries.i18n import translate
from materials_boundaries.prediction_visualization import build_prediction_comparison
from materials_boundaries.temperature import evaluate_temperature
from materials_boundaries.temperature_visualization import build_temperature_comparison
from materials_boundaries.visualization import build_comparison

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

expected, instance_path, temperature_path = sys.argv[1:]
require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),
        "package imported from outside the isolated installation")
metadata_version = distribution("materials-boundaries").version
require(metadata_version == package.__version__ == expected,
        "installed METADATA/package version mismatch")
instance = package.load_json(instance_path)
evaluation = package.evaluate(instance)
outputs = {
    "evaluation": evaluation,
    "comparison": build_comparison([instance], fractions=[0, 1]),
    "temperature": evaluate_temperature(package.load_json(temperature_path)),
    "temperature_comparison": build_temperature_comparison(points_per_branch=2),
}
for group in read_catalog("computational_predictions")["comparison_groups"]:
    outputs[group["id"]] = build_prediction_comparison(group["id"])
for name, output in outputs.items():
    require(output["engine_version"] == expected, name + ": stale installed engine label")
for sample in outputs["comparison"]["cases"][0]["samples"]:
    require(sample["evaluation"]["engine_version"] == expected, "stale nested engine label")
languages = ("en", "zh", "ja", "de")
for language in languages:
    for as_json in (False, True):
        stdout = io.StringIO()
        args = ["evaluate", instance_path, "--lang", language] + (["--json"] if as_json else [])
        with redirect_stdout(stdout):
            code = main(args)
        require(code == 0, "installed CLI failed")
        text = stdout.getvalue()
        require(json.loads(text) == evaluation if as_json else translate("summary_title", language) in text,
                "installed CLI output mismatch: " + language)
# Exercise the mixed catalog in the dependency-free installation as well.
from materials_boundaries.catalog import query_catalog
observations = read_catalog("observations")
mos2 = query_catalog("observations", source_id="bertolazzi_brivio_kis_2011")
require(len(mos2["records"]) >= 2, "missing installed MoS2 observations")
for language in languages:
    for filtered in (False, True):
        args = ["catalog", "observations", "--lang", language]
        if filtered:
            args += ["--source-id", "bertolazzi_brivio_kis_2011"]
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(args + (["--json"] if as_json else ["--text"]))
            text = stdout.getvalue()
            require(code == 0 and "[missing:" not in text, "installed observation CLI failed")
            if as_json:
                require(json.loads(text) == (mos2 if filtered else observations), "observation JSON changed by language")
            else:
                for key in ("catalog_mos2_model_notice", "catalog_sd_notice", "catalog_mos2_source_notice",
                            "catalog_mos2_transcription_notice"):
                    require(translate(key, language) in text, "missing installed scientific disclosure: " + key)
                require(translate("catalog_q_used", language) + ": " + translate("unknown", language) in text,
                        "actual fit constant must remain unknown")
                require(text.index(translate("catalog_mos2_model_notice", language)) < text.index("180 ± 60 N/m"),
                        "unresolved model notice must precede MoS2 value")
# Exercise both non-executable wave families in every language and reject
# weakened scientific metadata without installing schema/runtime dependencies.
from copy import deepcopy
from materials_boundaries.catalog_output import render_catalog
wave_ids = ("isotropic_bulk_plane_wave_speeds_and_ratio", "christoffel_tensor_strong_ellipticity")
for identifier in wave_ids:
    wave = query_catalog("claims", record_id=identifier)
    require(wave["records"][0]["evaluation_support"] == "catalog_only", "wave became executable")
    for language in languages:
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["catalog", "claims", "--id", identifier, "--lang", language,
                             "--json" if as_json else "--text"])
            text = stdout.getvalue()
            require(code == 0 and "[missing:" not in text, "installed wave CLI failed")
            if as_json:
                require(json.loads(text) == wave, "wave JSON changed by language")
            else:
                for key in ("notice", "conditions", "normalization", "polarization", "energy", "range", "limits"):
                    require(translate("catalog_wave_" + key, language) in text, "missing wave disclosure: " + key)
    weakened = deepcopy(wave)
    weakened["records"][0]["required_assumptions"]["density"] = "rho>=0"
    try:
        render_catalog(weakened, "claims")
    except ValueError:
        pass
    else:
        raise RuntimeError("installed wave guard accepted non-strict density")
# Falin hBN source components and unknowns must also survive dependency-free installation.
from materials_boundaries._hbn_observation_contract import HBN_SOURCE
hbn = query_catalog("observations", source_id=HBN_SOURCE)
require(len(hbn["records"]) >= 2, "missing installed hBN observations")
for language in languages:
    for record in hbn["records"]:
        selected = {"schema_version": hbn["schema_version"], "records": [record]}
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["catalog", "observations", "--id", record["id"], "--lang", language,
                             "--json" if as_json else "--text"])
            text = stdout.getvalue()
            require(code == 0 and "[missing:" not in text, "installed hBN CLI failed")
            if as_json:
                require(json.loads(text) == selected, "hBN JSON changed by language")
            else:
                for key in ("catalog_hbn_model_notice", "catalog_hbn_sd_notice", "catalog_hbn_count_notice",
                            "catalog_hbn_stress_strain_notice", "catalog_hbn_velocity_notice", "catalog_hbn_rights_notice"):
                    require(translate(key, language) in text, "missing installed hBN disclosure: " + key)
                require("PDF p. 8" in text and "MOESM443_ESM.pdf" in text, "missing SD source component")
        weakened = deepcopy(selected)
        weakened["records"][0]["reported_result"]["uncertainty"]["evidence"]["artifact"] = "publisher_html"
        try:
            render_catalog(weakened, "observations", language)
        except ValueError:
            pass
        else:
            raise RuntimeError("installed hBN guard accepted false SD provenance")
# Observation inspection is presentation-only and must work with no dev extras.
from materials_boundaries.observation_visualization import (
    build_observation_inspection, export_observation_inspection, labels,
    validate_observation_inspection, ObservationInspectionError,
)
inspection = build_observation_inspection()
require(inspection["engine_version"] == expected, "stale installed inspection version")
require(inspection["schema_version"] == "1.1.0", "wrong installed inspection schema")
require(inspection["record_snapshots"] == read_catalog("observations")["records"],
        "installed inspection changed observation snapshots")
inspection_files = {}
for language in languages:
    output = Path(instance_path).parent / "inspection" / language
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(["observation", "inspect", "--output", str(output), "--lang", language])
    report = json.loads(stdout.getvalue())
    require(code == 0 and len(report["artifacts"]) == 5, "installed inspection CLI failed")
    require(set(p.name for p in output.iterdir()) == set(report["artifacts"]), "wrong inspection artifacts")
    for filename in report["artifacts"]:
        text = (output / filename).read_text(encoding="utf-8")
        require("[missing:" not in text, "missing installed inspection labels")
        if filename.endswith((".svg", ".html")):
            require(labels(language)["normalized"] in text, "missing normalized display label")
    inspection_files[language] = [(output / name).read_bytes() for name in
                                 ("observation-inspection.json", "observation-inspection.csv")]
require(all(value == inspection_files["en"] for value in inspection_files.values()),
        "inspection JSON/CSV changed by locale")
weakened = deepcopy(inspection)
weakened["presentation_policy"]["overlay_allowed"] = True
try:
    validate_observation_inspection(weakened)
except ObservationInspectionError:
    pass
else:
    raise RuntimeError("installed inspection guard accepted changed policy")
invalid_output = Path(instance_path).parent / "invalid-inspection"
try:
    export_observation_inspection(invalid_output, record_ids=["not-a-record"])
except ObservationInspectionError:
    pass
else:
    raise RuntimeError("installed inspection accepted an unknown ID")
require(not invalid_output.exists(), "invalid inspection wrote partial files")
# PA12 admission and all inspection formats must work with only the standard library.
import csv
from decimal import Decimal
from html import unescape
from importlib.util import find_spec
import re
import xml.etree.ElementTree as ET
from unittest.mock import patch
from materials_boundaries._pa12_cf15_observation_contract import (
    PA12_FAMILY, PA12_SOURCE, PA12_QUANTITY, validate_pa12_dataset, validate_pa12_sources,
)
from materials_boundaries._observation_contract import validate_observation_records
from materials_boundaries import observation_visualization as observation_view
require(find_spec('jsonschema') is None and find_spec('referencing') is None,
        'wheel smoke accidentally has development dependencies')
all_records = observations['records']
old_records = [r for r in all_records if r.get('method_family') != PA12_FAMILY]
new_records = [r for r in all_records if r.get('method_family') == PA12_FAMILY]
require(len(all_records) == 12 and len(old_records) == len(new_records) == 6,
        'unexpected production observation counts')
require(len(read_catalog('sources')['records']) == 52, 'unexpected production source count')
expected_cells = (('23', '49.07', '0.88', 49070000, 880000),
                  ('40', '40.31', '0.72', 40310000, 720000),
                  ('60', '32.70', '1.18', 32700000, 1180000),
                  ('80', '26.60', '1.15', 26600000, 1150000),
                  ('100', '22.78', '0.97', 22780000, 970000),
                  ('120', '18.68', '0.91', 18680000, 910000))
for record, (temperature, central, sd, pa, pa_sd) in zip(new_records, expected_cells):
    result, u = record['reported_result'], record['reported_result']['uncertainty']
    require((record['conditions']['temperature']['value_string'], result['value_string'],
             u['value_string'], record['si_result']['value'], record['si_result']['uncertainty_value'])
            == (temperature, central, sd, pa, pa_sd), 'source cell changed')
    require(Decimal(central) * Decimal('1000000') == pa
            and Decimal(sd) * Decimal('1000000') == pa_sd, 'SI scaling is not exact')
    require(record['quantity_dimension'] == 'pressure' and record['si_unit'] == 'Pa'
            and result['unit'] == u['unit'] == 'MPa', 'mixed reported/SI units')
    require(record['method']['stress_measure'] is None
            and record['method']['stress_area_basis'] is None
            and result['central_statistic_explicitly_named'] is None
            and result['aggregation_convention'] is None
            and record['conditions']['humidity']['specimen_moisture_content'] is None
            and record['conditions']['temperature']['direct_specimen_temperature_measurement'] is None
            and record['conditions']['temperature']['stability_tolerance'] is None,
            'unknown PA12 metadata acquired a default')
    require(record['sample_metadata']['count'] == 3
            and record['sample_metadata']['scope'] == 'tensile_tests_per_temperature_condition'
            and u['type'] == 'reported_standard_deviation'
            and u['confidence_level'] is None, 'changed count or SD interpretation')
for record in old_records:
    require(record['si_unit'] == record['reported_result']['unit'] == 'N/m', 'old membrane units changed')
old_ids, new_ids = ([r['id'] for r in records] for records in (old_records, new_records))
selected_modes = {'default': None, 'old': old_ids, 'new': new_ids,
                  'mixed': [new_ids[2], old_ids[0]], 'one_temperature': [new_ids[2]]}
catalog_modes = {
    'default': ([], observations),
    'old': (['--observation-type', 'experiment_derived_model_dependent'],
            query_catalog('observations', observation_type='experiment_derived_model_dependent')),
    'new': (['--source-id', PA12_SOURCE], query_catalog('observations', source_id=PA12_SOURCE)),
    'one_temperature': (['--id', new_ids[2]], query_catalog('observations', record_id=new_ids[2])),
}
for language in languages:
    for mode, (filters, selected) in catalog_modes.items():
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(['catalog', 'observations', '--lang', language] + filters
                            + (['--json'] if as_json else ['--text']))
            text = stdout.getvalue()
            require(code == 0 and '[missing:' not in text, 'PA12 catalog CLI failed: ' + mode)
            if as_json:
                require(json.loads(text) == selected, 'catalog JSON changed by locale: ' + mode)
            elif mode != 'old':
                first = next(r for r in selected['records'] if r.get('method_family') == PA12_FAMILY)
                value = first['reported_result']['value_string'] + ' ± ' + first['reported_result']['uncertainty']['value_string'] + ' MPa'
                for key in ('identity', 'temperature', 'process', 'stress', 'sample'):
                    require(text.index(translate('catalog_pa12_' + key, language)) < text.index(value),
                            'essential catalog warning must precede value: ' + key)
                for key in ('source_version', 'rights', 'normalization'):
                    require(translate('catalog_pa12_' + key, language) in text, 'missing PA12 disclosure: ' + key)
    mixed = {'schema_version': observations['schema_version'],
             'records': [r for r in all_records if r['id'] in selected_modes['mixed']]}
    mixed_text = render_catalog(mixed, 'observations', language)
    require('N/m' in mixed_text and '32.70 ± 1.18 MPa' in mixed_text
            and '[missing:' not in mixed_text, 'mixed-unit catalog failed')

export_checks = {}
def compact(value):
    return ''.join(value.split())
for mode, selected_ids in selected_modes.items():
    language_bytes = {}
    for language in languages:
        for grouping in ('study', 'quantity'):
            output = Path(instance_path).parent / 'pa12-inspection' / mode / grouping / language
            args = ['observation', 'inspect', '--output', str(output), '--lang', language,
                    '--group-by', grouping]
            for identifier in reversed(selected_ids or []):
                args += ['--id', identifier]
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(args)
            report = json.loads(stdout.getvalue())
            require(code == 0 and len(report['artifacts']) == 5, 'PA12 inspection CLI failed')
            require(set(p.name for p in output.iterdir()) == set(report['artifacts']), 'unexpected inspection output')
            bundle = json.loads((output / 'observation-inspection.json').read_text())
            selected = [r for r in all_records if selected_ids is None or r['id'] in selected_ids]
            require(bundle['schema_version'] == '1.1.0'
                    and bundle['catalog_schema_versions']['observations'] == '1.3.0', 'stale schema envelope')
            require(bundle['record_snapshots'] == selected, 'selection or immutable snapshot changed')
            require(bundle['selection']['resolved_record_ids'] == [r['id'] for r in selected], 'requested IDs changed source order')
            validate_observation_inspection(bundle)
            rows = list(csv.DictReader(io.StringIO((output / 'observation-inspection.csv').read_text())))
            require(len(rows) == len(selected), 'incorrect CSV row count')
            for row, record in zip(rows, selected):
                require(json.loads(row['record_snapshot_json']) == record, 'CSV lost record snapshot')
                if record.get('method_family') == PA12_FAMILY:
                    require(row['unit'] == 'MPa' and row['si_unit'] == 'Pa'
                            and row['reported_value_string'] == record['reported_result']['value_string']
                            and row['reported_plus_minus_string'] == record['reported_result']['uncertainty']['value_string']
                            and Decimal(row['si_central_value']) == record['si_result']['value']
                            and row['temperature_basis'] == 'reported_chamber_test_condition', 'PA12 CSV contract changed')
                    require(json.loads(row['method_json'])['stress_measure'] is None, 'CSV lost unknown stress convention')
                    columns = list(row)
                    require(columns.index('temperature_basis') < columns.index('central_value')
                            and columns.index('essential_caveats') < columns.index('central_value'), 'CSV warnings follow values')
                else:
                    require(row['unit'] == row['si_unit'] == 'N/m'
                            and row['si_central_value'] == row['central_value']
                            and row['si_plus_minus_value'] == row['plus_minus_value']
                            and row['temperature_value'] == row['dataset_id'] == 'null', 'old CSV fields changed')
            for filename in report['artifacts']:
                text = (output / filename).read_text()
                require('[missing:' not in text, 'missing translation in installed export')
                if filename.endswith('.svg'):
                    xml = ET.fromstring(text)
                    cards = {node.attrib['data-record-id']: ''.join(node.itertext()) for node in xml.iter()
                             if 'data-record-id' in node.attrib}
                    require(not any(node.tag.rsplit('}', 1)[-1] in ('script', 'image', 'circle', 'line', 'polyline', 'path')
                                    for node in xml.iter()), 'inspection gained script, network image or quantitative marks')
                elif filename.endswith('.html'):
                    cards = {unescape(match[1]): unescape(re.sub('<[^>]+>', '', match[2])) for match in
                             re.finditer(r'<article[^>]*data-record-id="([^"]+)"[^>]*>(.*?)</article>', text, re.S)}
                    require('<script' not in text.lower() and '<img' not in text.lower(), 'active/network inspection content')
                else:
                    continue
                require(set(cards) == {r['id'] for r in selected}, 'missing visible cards')
                for record in selected:
                    if record.get('method_family') != PA12_FAMILY:
                        require('N/m' in cards[record['id']], 'old membrane unit missing')
                        continue
                    facet = next(f for f in bundle['facets'] if f['record_id'] == record['id'])
                    visible = compact(cards[record['id']])
                    value_index = visible.index(compact(facet['normalized_display']))
                    require(compact(record['dataset_id']) in visible[:value_index]
                            and compact(record['protocol_id']) in visible[:value_index]
                            and compact(record['conditions']['temperature']['value_string'] + ' °C') in visible[:value_index],
                            'identity/temperature must precede PA12 value')
                    for key in facet['required_caveat_codes']:
                        require(compact(labels(language)[key]) in visible[:value_index], 'warning follows PA12 value: ' + key)
                    require(compact(facet['si_display']) in visible
                            and compact(labels(language)['pa12_version_warning']) in visible
                            and compact(labels(language)['pa12_rights_warning']) in visible, 'PA12 detail disclosure missing')
            language_bytes[(language, grouping)] = [(output / name).read_bytes() for name in
                ('observation-inspection.json', 'observation-inspection.csv')]
    for grouping in ('study', 'quantity'):
        require(all(language_bytes[(lang, grouping)] == language_bytes[('en', grouping)] for lang in languages),
                'PA12 JSON/CSV changed by locale')
    export_checks[mode] = {'languages': list(languages), 'groupings': ['study', 'quantity'], 'files_per_export': 5}

# No schema dependency may be necessary to reject scientific mutations.
def rejects(call, message):
    try:
        call()
    except ValueError:
        return
    raise RuntimeError(message)
mutations = (
    lambda r: r['method'].update(stress_measure='engineering_stress'),
    lambda r: r['reported_result']['uncertainty'].update(confidence_level=0.95),
    lambda r: r['conditions']['temperature'].update(value=True),
    lambda r: r['conditions']['humidity'].update(specimen_moisture_content=0),
    lambda r: r['si_result'].update(value=r['si_result']['value'] + 1),
    lambda r: r.pop('method_family'),
)
for mutate in mutations:
    weakened = deepcopy(new_records[0]); mutate(weakened)
    rejects(lambda: validate_observation_records([weakened]), 'installed record guard accepted scientific mutation')
    rejects(lambda: render_catalog({'schema_version': observations['schema_version'], 'records': [weakened]}, 'observations'),
            'installed catalog renderer accepted scientific mutation')
renamed = deepcopy(new_records[0]); renamed['id'] = 'wheel_renamed_pa12'; renamed['name'] = 'Renamed display only'
validate_observation_records([renamed]); validate_pa12_dataset([renamed], require_complete=False)
rejects(lambda: validate_pa12_dataset(new_records + [renamed], require_complete=True),
        'installed dataset guard accepted duplicate cell with alias ID')
weakened_sources = deepcopy(read_catalog('sources'))
next(s for s in weakened_sources['records'] if s['id'] == PA12_SOURCE)['doi'] = '10.3390/incorrect'
rejects(lambda: validate_pa12_sources(weakened_sources['records']), 'installed source guard accepted DOI mutation')
rejects(lambda: render_catalog(weakened_sources, 'sources'), 'installed source text accepted DOI mutation')
new_bundle = build_observation_inspection(record_ids=new_ids)
for mutate in (
    lambda b: b['facets'][0]['temperature'].update(basis='direct_specimen_measurement'),
    lambda b: b['facets'][0]['normalization'].update(adds_measurement_precision=True),
    lambda b: b.update(schema_version='1.0.0'),
    lambda b: b['record_snapshots'][0]['method'].update(stress_measure='engineering_stress'),
    lambda b: b['source_snapshots'][0].update(doi='10.3390/incorrect'),
):
    weakened = deepcopy(new_bundle); mutate(weakened)
    rejects(lambda: validate_observation_inspection(weakened), 'installed canonical rebuild accepted altered bundle')
# Both a nonexistent directory and existing sentinel remain untouched on invalid input.
invalid_new = Path(instance_path).parent / 'pa12-invalid-new'
rejects(lambda: export_observation_inspection(invalid_new, record_ids=['not-a-record']), 'invalid ID accepted')
require(not invalid_new.exists(), 'invalid PA12 selector created a directory')
sentinel = Path(instance_path).parent / 'pa12-invalid-existing'; sentinel.mkdir()
(sentinel / 'keep.txt').write_text('sentinel')
rejects(lambda: export_observation_inspection(sentinel, record_ids=new_ids, lang='invalid'), 'invalid language accepted')
require([(p.name, p.read_text()) for p in sentinel.iterdir()] == [('keep.txt', 'sentinel')], 'invalid export modified existing target')

# Separate quantitative source-summary route; inspection stays nonquantitative.
from decimal import Context, Inexact, Rounded, getcontext, setcontext
from materials_boundaries import observation_temperature_plot as plot_view
from materials_boundaries._pa12_cf15_observation_contract import PA12_DATASET
from materials_boundaries._observation_temperature_labels import labels as plot_labels
plot_bundle = plot_view.build_observation_temperature_plot(dataset_id=PA12_DATASET)
plot_view.validate_observation_temperature_plot(plot_bundle)
expected_endpoints = [('48.19', '49.95'), ('39.59', '41.03'), ('31.52', '33.88'),
                      ('25.45', '27.75'), ('21.81', '23.75'), ('17.77', '19.59')]
require([(g['derived_lower_string'], g['derived_upper_string']) for g in plot_bundle['glyphs']]
        == expected_endpoints, 'wrong installed plot SD endpoints')
require([g['central_value_string'] for g in plot_bundle['glyphs']]
        == ['49.07', '40.31', '32.70', '26.60', '22.78', '18.68'], 'lost source precision')
context_before = getcontext().copy()
try:
    hostile = Context(prec=2); hostile.traps[Inexact] = True; hostile.traps[Rounded] = True
    setcontext(hostile)
    require(plot_view.build_observation_temperature_plot(dataset_id=PA12_DATASET) == plot_bundle,
            'caller Decimal context affected installed glyph arithmetic')
finally:
    setcontext(context_before)
plot_data = []
for language in languages:
    destination = Path(instance_path).parent / ('temperature-observation-plot-' + language)
    out = io.StringIO()
    with redirect_stdout(out):
        status = main(['observation', 'plot-temperature', '--dataset-id', PA12_DATASET,
                       '--output', str(destination), '--lang', language])
    report = json.loads(out.getvalue())
    require(status == 0 and len(report['artifacts']) == 5, 'installed plot CLI failed')
    require(all(name.startswith('observation-temperature-plot.') for name in report['artifacts']),
            'plot export prefix could overwrite inspection')
    bundle_bytes = (destination / 'observation-temperature-plot.json').read_bytes()
    csv_bytes = (destination / 'observation-temperature-plot.csv').read_bytes()
    plot_data.append((bundle_bytes, csv_bytes))
    require(json.loads(bundle_bytes) == plot_bundle, 'installed export bundle changed')
    rows = list(csv.DictReader(io.StringIO(csv_bytes.decode())))
    require(len(rows) == 6 and rows[2]['source_value_string'] == '32.70 ± 1.18', 'plot CSV lost exact cells')
    for filename in report['artifacts']:
        if filename.endswith('.svg'):
            root = ET.fromstring((destination / filename).read_text())
            require(sum(node.tag.endswith('circle') for node in root.iter()) == 6,
                    'installed source plot must have six equally styled points')
        if filename.endswith(('.svg', '.html')):
            text = (destination / filename).read_text()
            require('[missing:' not in text and '<script' not in text.lower(), 'unsafe or incomplete plot rendering')
            require('32.70' in text and 'CC-BY-4.0' in text, 'missing source precision or rights')
require(all(data == plot_data[0] for data in plot_data), 'locale changed plot JSON or CSV')
for alteration in (
    lambda b: b['glyphs'].reverse(),
    lambda b: b['glyphs'][0].update(derived_lower_string='48.18'),
    lambda b: b['presentation_policy'].update(interpolation_allowed=True),
    lambda b: b['group'].update(profile_version='1.0.1'),
):
    invalid = deepcopy(plot_bundle); alteration(invalid)
    rejects(lambda: plot_view.temperature_observation_plot_json(invalid), 'installed plot accepted tampering')
plot_read = plot_view.read_catalog
reordered = deepcopy(observations); reordered['records'].reverse()
with patch.object(plot_view, 'read_catalog', side_effect=lambda kind: deepcopy(reordered) if kind == 'observations' else plot_read(kind)):
    require(plot_view.build_observation_temperature_plot(dataset_id=PA12_DATASET) == plot_bundle,
            'catalog order leaked into source-ordered plot')
invalid_target = Path(instance_path).parent / 'invalid-temperature-observation-plot'
rejects(lambda: plot_view.export_observation_temperature_plot(invalid_target, dataset_id='wrong'), 'wrong dataset accepted')
require(not invalid_target.exists(), 'invalid plot created output')
require(build_observation_inspection()['presentation_policy']['quantitative_axes_allowed'] is False,
        'separate route weakened generic inspection')

print(json.dumps({"version": expected, "metadata_version": metadata_version,
                  "engine_outputs": sorted(outputs), "languages": languages,
                  "installed_without_dependencies": True, "mixed_observation_catalog_languages": languages, "bulk_wave_catalog_languages": languages, "hbn_observation_languages": languages, "observation_inspection_languages": languages, "observation_inspection_schema": "1.1.0", "pa12_export_checks": export_checks, "pa12_scientific_mutations_rejected": len(mutations), "pa12_exact_selected_cells": len(expected_cells), "temperature_observation_plot_languages": languages, "temperature_observation_plot_schema": "1.0.0", "temperature_observation_plot_cells": len(plot_bundle["glyphs"])}))
'''


def check_wheel(wheel):
    expected = literal_version((ROOT / "materials_boundaries/_version.py").read_text(encoding="utf-8"))
    with ZipFile(wheel) as archive:
        metadata_files = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        require(len(metadata_files) == 1, "wheel must contain one METADATA file")
        metadata = Parser().parsestr(archive.read(metadata_files[0]).decode("utf-8"))
        check_metadata(metadata, expected)
        packaged = literal_version(archive.read("materials_boundaries/_version.py").decode("utf-8"))
        require(packaged == expected, "wheel packaged version differs from source literal")
    # Ignore editable installs and caller Python configuration. -I also ignores
    # Python environment variables and excludes the working directory from imports.
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTHON")}
    with tempfile.TemporaryDirectory(prefix="materials-wheel-check-") as temporary:
        work = Path(temporary)
        venv.EnvBuilder(with_pip=True).create(work / "venv")
        python = work / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(python), "-I", "-m", "pip", "--isolated", "install", "--no-index",
                        "--no-deps", "--disable-pip-version-check", str(wheel)],
                       cwd=work, env=env, check=True, capture_output=True, text=True)
        instance = work / "instance.json"
        instance.write_bytes((ROOT / "examples/synthetic-two-phase.json").read_bytes())
        temperature = work / "temperature.json"
        temperature.write_bytes((ROOT / "examples/temperature/synthetic-linear-50k.json").read_bytes())
        result = subprocess.run([str(python), "-I", "-c", INSTALLED_CHECK, expected,
                                 str(instance), str(temperature)],
                                cwd=work, env=env, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path, help="one built wheel from this release")
    args = parser.parse_args()
    try:
        print(json.dumps(check_wheel(args.wheel.resolve()), indent=2))
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.stderr or exc.stdout or str(exc)) from exc
