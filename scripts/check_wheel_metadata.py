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
# Scalar viscoelastic records remain metadata-only after a dependency-free install.
from materials_boundaries._viscoelastic_contract import validate_viscoelastic_records
viscoelastic_ids = ('scalar_viscoelastic_creep_relaxation_duality',
                   'scalar_viscoelastic_creep_relaxation_product_bound')
for identifier in viscoelastic_ids:
    selected = query_catalog('claims', record_id=identifier)
    require(len(selected['records']) == 1, 'missing installed viscoelastic record')
    require(selected['records'][0]['evaluation_support'] == 'catalog_only',
            'installed viscoelastic record became executable')
    for language in languages:
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(['catalog', 'claims', '--id', identifier, '--lang', language,
                             '--json' if as_json else '--text'])
            text = stdout.getvalue()
            require(code == 0 and '[missing:' not in text, 'installed viscoelastic CLI failed')
            if as_json:
                require(json.loads(text) == selected, 'viscoelastic JSON changed by language')
            else:
                for key in ('notice', 'conditions', 'regularity', 'attribution', 'range', 'limits'):
                    require(translate('catalog_viscoelastic_' + key, language) in text,
                            'missing installed viscoelastic disclosure: ' + key)
    weakened = deepcopy(selected)
    weakened['records'][0]['required_assumptions']['instantaneous_relaxation'] = 'R0>=0'
    for action in (lambda: validate_viscoelastic_records(weakened['records']),
                   lambda: render_catalog(weakened, 'claims')):
        try:
            action()
        except ValueError:
            pass
        else:
            raise RuntimeError('installed viscoelastic guard accepted non-strict instantaneous modulus')
require(set(viscoelastic_ids).isdisjoint(e['claim_id'] for e in evaluation['evaluations']),
        'installed evaluator dispatched a viscoelastic relation')
require(len(evaluation['evaluations']) == 8 and len(outputs['comparison']['series']) == 8,
        'installed viscoelastic catalog changed the eight-rule boundary')
# Yield criteria are closed metadata, never additional executable material rules.
from materials_boundaries._yield_contract import validate_yield_records
yield_ids = ('von_mises_initial_yield_relation', 'tresca_initial_yield_relation',
             'tresca_von_mises_equivalent_stress_ratio_bound')
for identifier in yield_ids:
    selected = query_catalog('claims', record_id=identifier)
    require(len(selected['records']) == 1, 'missing installed yield record')
    require(selected['records'][0]['evaluation_support'] == 'catalog_only',
            'installed yield record became executable')
    for language in languages:
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(['catalog', 'claims', '--id', identifier, '--lang', language,
                             '--json' if as_json else '--text'])
            text = stdout.getvalue()
            require(code == 0 and '[missing:' not in text, 'installed yield CLI failed')
            if as_json:
                require(json.loads(text) == selected, 'yield JSON changed by language')
            else:
                for key in ('notice', 'tensor', 'normalization', 'math_scope',
                            'physical_scope', 'attribution', 'limits'):
                    require(translate('catalog_yield_' + key, language) in text,
                            'missing installed yield disclosure: ' + key)
    weakened = deepcopy(selected)
    weakened['records'][0]['yield_criterion_contract']['hydrostatic_behavior']['ratio_at_zero'] = 1
    for action in (lambda: validate_yield_records(weakened['records']),
                   lambda: render_catalog(weakened, 'claims')):
        try:
            action()
        except ValueError:
            pass
        else:
            raise RuntimeError('installed yield guard assigned a hydrostatic ratio')
require(set(yield_ids).isdisjoint(e['claim_id'] for e in evaluation['evaluations']),
        'installed evaluator dispatched a yield criterion')
require(len(evaluation['evaluations']) == 8 and len(outputs['comparison']['series']) == 8,
        'installed yield catalog changed the eight-rule boundary')
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
from materials_boundaries._paht_cf_observation_contract import PAHT_FAMILY
def historical_observation_rows(records):
    # Exact accepted membership, while default exports still cover every live row.
    baseline_ids = ('lee_2008_graphene_in_plane_stiffness_2d', 'lee_2008_graphene_breaking_strength_2d', 'bertolazzi_2011_mos2_monolayer_in_plane_stiffness_2d', 'bertolazzi_2011_mos2_monolayer_breaking_strength_2d', 'falin_2017_hbn_monolayer_in_plane_stiffness_2d', 'falin_2017_hbn_monolayer_breaking_strength_2d', 'ciganas2026-pa12cf15-uts-23c', 'ciganas2026-pa12cf15-uts-40c', 'ciganas2026-pa12cf15-uts-60c', 'ciganas2026-pa12cf15-uts-80c', 'ciganas2026-pa12cf15-uts-100c', 'ciganas2026-pa12cf15-uts-120c', 'zach-2025-paht-cf-annealed-uts-25c', 'zach-2025-paht-cf-annealed-uts-50c', 'zach-2025-paht-cf-annealed-uts-100c', 'zach-2025-paht-cf-annealed-uts-150c')
    index = {record['id']: record for record in records}
    require(len(index) == len(records) and set(baseline_ids) <= set(index),
            'missing historical or duplicate installed observation ID')
    baseline = [index[key] for key in baseline_ids]
    old = baseline[:6]
    pa12 = baseline[6:12]
    require(len(baseline) == 16 and len(old) == len(pa12) == 6
            and all(r['observation_type'] == 'experiment_derived_model_dependent' for r in old)
            and all(r.get('method_family') == PA12_FAMILY for r in pa12),
            'changed exact historical observation cohorts')
    return baseline, old, pa12

all_records = observations['records']
baseline_observations, old_records, new_records = historical_observation_rows(all_records)
# Keep the complete accepted v0.28.2 membership while allowing future appends.
baseline_sources_ids = frozenset(['hashin_shtrikman_1963', 'kochmann_milton_2014', 'berger_2017', 'milton_2018_comment', 'berger_2018_reply', 'singh_lai_2024', 'materials_project_elasticity', 'genin_birman_2009', 'meille_garboczi_2001', 'griffith_1921', 'wilson_1992_nasa_tm_103591', 'frenkel_1926', 'shimanek_2022_ideal_shear', 'rose_ferrante_smith_1981', 'van_der_ven_ceder_2004', 'azocar_guzman_2020_hydrogen', 'pierce_sullivan_1969_nasa_tn_d_5140', 'mouhat_coudert_2014_elastic_stability', 'roberts_garboczi_2002_porous', 'lee_wei_kysar_hone_2008', 'paris_erdogan_1963', 'forman_kearney_engle_1967', 'hudson_1969_nasa_tn_d_5390', 'afgrow_dtd_handbook_fatigue_growth', 'astm_e647_24_public_scope', 'nist_cryogenic_al6061_t6', 'nist_cryogenic_ss304', 'nist_cryogenic_reference_list', 'bradley_radebaugh_lewis_2006', 'nist_public_information_reuse', 'zener_1948_elasticity_anelasticity', 'ranganathan_ostoja_starzewski_2008_anisotropy', 'ranganathan_ostoja_starzewski_ferrari_2011_anisotropy', 'knowles_howie_2015_cubic_shear', 'shimanek_2022_arxiv_2108_06412_v2', 'dubois_2006_prb_74_235203', 'nist_cryogenic_al5083', 'nist_cryogenic_invar', 'nist_cryogenic_ss316', 'nist_cryogenic_material_index', 'nist_cryogenic_srd_provenance', 'ting_chen_2005_poisson_unbounded', 'norris_2006_cubic_poisson', 'norris_2006_anisotropic_extrema', 'ortiz_2012_anisotropic_mof_elasticity', 'miller_evans_marmier_2015_linear_compressibility', 'materials_boundaries_synthetic_temperature_demo', 'bertolazzi_brivio_kis_2011', 'chevrot_vanderhilst_2003', 'xiang_qi_wei_2018_arxiv_v2', 'falin_et_al_2017_hbn_mechanical_properties', 'ciganas2026polym18050563', 'zach_dudescu2025jcs9110624', 'hanyga2018scalar_anisotropic_duality', 'hanyga2019newtonian_relaxation', 'giraldo_londono_paulino_2020_yield_criteria', 'wierzbicki_2013_structural_plasticity'])
installed_sources_ids = [record['id'] for record in read_catalog('sources')['records']]
require(baseline_sources_ids <= set(installed_sources_ids)
        and len(installed_sources_ids) == len(set(installed_sources_ids)),
        'missing historical or duplicate installed sources ID')
# Keep the complete accepted v0.28.2 membership while allowing future appends.
baseline_claims_ids = frozenset(['hs_bulk_3d_two_phase', 'reuss_bulk', 'voigt_bulk', 'hs_shear_3d_two_phase', 'reuss_shear', 'voigt_shear', 'youngs_modulus_outer', 'poissons_ratio_outer', 'griffith_central_crack_plane_stress', 'griffith_central_crack_plane_strain', 'frenkel_slip_specific_ideal_shear', 'uber_normal_cohesive_strength', 'lefm_central_crack_mode_i_stress_intensity', 'lefm_mode_i_energy_release_relation', 'lefm_center_crack_finite_width_secant_factor', 'general_stiffness_positive_definite', 'cubic_born_stability', 'hexagonal_born_stability', 'orthorhombic_born_stability', 'hs_porous_bulk_3d_solid_void', 'hs_porous_shear_3d_solid_void', 'hs_porous_youngs_outer_3d_solid_void', 'tetragonal_i_born_stability', 'tetragonal_ii_born_stability', 'rhombohedral_i_born_stability', 'rhombohedral_ii_born_stability', 'paris_erdogan_intermediate_growth', 'forman_terminal_acceleration_growth', 'zener_cubic_elastic_anisotropy_index', 'universal_elastic_anisotropy_index', 'directional_poissons_ratio_definition_and_range', 'directional_poisson_reciprocity_energy_constraint', 'directional_linear_compressibility_hydrostatic_relation', 'normalized_directional_compressibility_range', 'isotropic_bulk_plane_wave_speeds_and_ratio', 'christoffel_tensor_strong_ellipticity', 'scalar_viscoelastic_creep_relaxation_duality', 'scalar_viscoelastic_creep_relaxation_product_bound', 'von_mises_initial_yield_relation', 'tresca_initial_yield_relation', 'tresca_von_mises_equivalent_stress_ratio_bound'])
installed_claims_ids = [record['id'] for record in read_catalog('claims')['records']]
require(baseline_claims_ids <= set(installed_claims_ids)
        and len(installed_claims_ids) == len(set(installed_claims_ids)),
        'missing historical or duplicate installed claims ID')
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
            bundle = json.loads((output / 'observation-inspection.json').read_text(encoding='utf-8'))
            selected = [r for r in all_records if selected_ids is None or r['id'] in selected_ids]
            require(bundle['schema_version'] == '1.1.0'
                    and bundle['catalog_schema_versions']['observations'] == '1.3.0', 'stale schema envelope')
            require(bundle['record_snapshots'] == selected, 'selection or immutable snapshot changed')
            require(bundle['selection']['resolved_record_ids'] == [r['id'] for r in selected], 'requested IDs changed source order')
            validate_observation_inspection(bundle)
            rows = list(csv.DictReader(io.StringIO((output / 'observation-inspection.csv').read_text(encoding='utf-8'))))
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
                elif record.get('method_family') == PAHT_FAMILY:
                    require(row['unit'] == 'MPa' and row['si_unit'] == 'Pa'
                            and row['reported_median_string'] == record['reported_result']['value_string']
                            and row['reported_sd_string'] == record['reported_result']['uncertainty']['value_string']
                            and row['plus_minus_value'] == row['reported_plus_minus_string'] == row['si_plus_minus_value'] == 'null'
                            and row['sd_header_unit_explicit'] == 'false'
                            and row['sd_unit_basis'] == 'contextual_inference_from_associated_uts_column'
                            and row['si_sd_unit_basis'] == 'conditional_on_contextual_MPa_inference',
                            'PAHT CSV median/SD or conditional-unit contract changed')
                else:
                    require(row['unit'] == row['si_unit'] == 'N/m'
                            and row['si_central_value'] == row['central_value']
                            and row['si_plus_minus_value'] == row['plus_minus_value']
                            and row['temperature_value'] == row['dataset_id'] == 'null', 'old CSV fields changed')
            for filename in report['artifacts']:
                text = (output / filename).read_text(encoding='utf-8')
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
                    if record.get('method_family') == PAHT_FAMILY:
                        from materials_boundaries._paht_observation_labels import PAHT_LABELS, PAHT_CAVEATS
                        visible = compact(cards[record['id']])
                        labels_paht = PAHT_LABELS[language]
                        median_display = labels_paht['paht_reported_median'] + ': ' + record['reported_result']['value_string'] + ' MPa'
                        value_index = visible.index(compact(median_display))
                        for code in PAHT_CAVEATS:
                            require(compact(labels_paht[code]) in visible[:value_index], 'PAHT caveat follows value')
                        require(compact(labels_paht['paht_reported_sd'] + ': ' + record['reported_result']['uncertainty']['value_string'] + ' MPa') in visible,
                                'PAHT separate SD missing')
                        continue
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
require([(p.name, p.read_text(encoding='utf-8')) for p in sentinel.iterdir()] == [('keep.txt', 'sentinel')], 'invalid export modified existing target')

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
            root = ET.fromstring((destination / filename).read_text(encoding='utf-8'))
            require(sum(node.tag.endswith('circle') for node in root.iter()) == 6,
                    'installed source plot must have six equally styled points')
        if filename.endswith(('.svg', '.html')):
            text = (destination / filename).read_text(encoding='utf-8')
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

# PAHT median and SD semantics remain separate in the dependency-free wheel.
from materials_boundaries._paht_cf_observation_contract import (
    PAHT_SOURCE, PAHT_DATASET, PAHT_CELLS, validate_paht_dataset, validate_paht_sources,
)
paht = query_catalog('observations', source_id=PAHT_SOURCE)['records']
require(len(paht) == 4, 'missing installed PAHT observations')
validate_paht_dataset(paht, require_complete=True)
validate_paht_sources(read_catalog('sources')['records'])
paht_bundle = build_observation_inspection(source_id=PAHT_SOURCE)
for record in paht:
    r, u = record['reported_result'], record['reported_result']['uncertainty']
    require(r['summary_statistic'] == 'median_as_reported' and u['notation'] == 'separate_sd',
            'installed PAHT statistic changed')
    require(u['header_unit_explicit'] is False and u['unit_basis'] == 'contextual_inference_from_associated_uts_column',
            'installed PAHT SD unit lost contextual basis')
for language in languages:
    text = render_catalog(query_catalog('observations', source_id=PAHT_SOURCE), 'observations', language)
    require('[missing:' not in text and '58.91' in text and '3.44' in text, 'installed PAHT catalog rendering failed')
    html = observation_view.render_observation_html(paht_bundle, language)
    svg = observation_view.render_observation_svg(paht_bundle, language)
    require('[missing:' not in html + svg and '58.91 ± 3.44' not in html + svg,
            'installed PAHT presentation joined median and SD')
rows = list(csv.DictReader(io.StringIO(observation_view.inspection_csv(paht_bundle))))
require(len(rows) == 4 and all(row['plus_minus_value'] == 'null' for row in rows),
        'PAHT CSV entered legacy plus-minus fields')
wrong = deepcopy(paht[0]); wrong['reported_result']['uncertainty']['header_unit_explicit'] = True
rejects(lambda: validate_paht_dataset([wrong]), 'installed PAHT accepted invented SD header unit')
rejects(lambda: plot_view.build_observation_temperature_plot(dataset_id=PAHT_DATASET),
        'installed PAHT entered Ciganas plot')

# New named two-study profile stays closed in a dependency-free installation.
from materials_boundaries import observation_study_comparison as study_view
study_bundle = study_view.build_observation_study_comparison(profile_id=study_view.PROFILE_ID)
study_view.validate_observation_study_comparison(study_bundle)
require(study_bundle['engine_version'] == expected, 'stale installed two-study engine')
require([len(p['points']) for p in study_bundle['panels']] == [6, 4], 'wrong two-study membership')
require(study_bundle['panels'][0]['points'][0]['central_statistic_explicitly_named'] is None,
        'Ciganas central statistic invented')
require(study_bundle['panels'][1]['points'][0]['summary_statistic'] == 'median_as_reported',
        'Zach median label lost')
require(study_bundle['panels'][1]['points'][0]['reported_sd']['header_unit_explicit'] is False,
        'Zach SD unit inference lost')
study_data = []
for language in languages:
    target = Path(instance_path).parent / ('study-comparison-' + language)
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(['observation', 'compare-temperature-studies', '--profile-id', study_view.PROFILE_ID,
                     '--output', str(target), '--lang', language])
    report = json.loads(stdout.getvalue())
    require(code == 0 and len(report['artifacts']) == 5, 'installed two-study CLI failed')
    require(set(p.name for p in target.iterdir()) == set(report['artifacts']), 'extra study files')
    content = [(target / ('observation-study-comparison.' + ext)).read_bytes() for ext in ('json', 'csv')]
    study_data.append(content)
    require(json.loads(content[0]) == study_bundle, 'installed study bundle altered')
    rows = list(csv.DictReader(io.StringIO(content[1].decode())))
    require(len(rows) == 10 and [r['panel_id'] for r in rows] == ['ciganas'] * 6 + ['zach'] * 4,
            'installed study CSV wrong long-form order')
    require(rows[6]['sd_notation'] == 'separate_sd' and rows[6]['central_value_string'] == '58.91',
            'installed study CSV lost median/SD source identity')
    for filename in report['artifacts']:
        text = (target / filename).read_text(encoding='utf-8')
        if filename.endswith(('.svg', '.html')):
            require('[missing:' not in text and '<script' not in text.lower(), 'unsafe study render')
            require('32.70' in text and '58.91' in text and '3.44' in text, 'source strings missing')
        if filename.endswith('.svg'):
            root = ET.fromstring(text)
            require(sum(node.tag.endswith('circle') for node in root.iter()) == 10, 'wrong study dot count')
require(all(v == study_data[0] for v in study_data), 'study machine exports depend on language')
for alteration in (
    lambda b: b['panels'].reverse(),
    lambda b: b['panels'][1]['points'][0]['reported_sd'].update(header_unit_explicit=True),
    lambda b: b['presentation_policy'].update(uncertainty_endpoints_calculated=True),
    lambda b: b.update(matched_conditions_established=True),
):
    bad = deepcopy(study_bundle); alteration(bad)
    for emit in (study_view.observation_study_comparison_json, study_view.observation_study_comparison_csv,
                 study_view.render_observation_study_comparison_svg, study_view.render_observation_study_comparison_html):
        rejects(lambda: emit(bad), 'installed study output accepted forged bundle')
read_study = study_view.read_catalog
with patch.object(study_view, 'read_catalog', side_effect=lambda kind: deepcopy(reordered) if kind == 'observations' else read_study(kind)):
    require(study_view.build_observation_study_comparison(profile_id=study_view.PROFILE_ID) == study_bundle,
            'catalog order changed source panel order')
target = Path(instance_path).parent / 'invalid-study-comparison'
rejects(lambda: study_view.export_observation_study_comparison(target, profile_id='wrong'), 'unreviewed profile accepted')
require(not target.exists(), 'invalid study profile wrote target')
require(build_observation_inspection()['presentation_policy']['quantitative_axes_allowed'] is False,
        'new view relaxed generic inspection')
rejects(lambda: plot_view.build_observation_temperature_plot(dataset_id=PAHT_DATASET), 'new view relaxed old plot')


# A complete dependency-free single-case workflow, independent of old sweeps.
from materials_boundaries.composite import build_composite_report, validate_composite_report, CompositeReplayError
from materials_boundaries.composite_intake import original_demo_instance, blank_composite_instance
from materials_boundaries.composite_render import render_composite_report
from materials_boundaries.composite_export import export_composite_report, ARTIFACTS
import hashlib
original_case = original_demo_instance()
composite_bundle = build_composite_report(original_case)
require(composite_bundle['engine_version'] == expected, 'stale installed composite version')
require(composite_bundle['input'] == original_case, 'single-case input changed')
require([p['volume_fraction'] for p in composite_bundle['input']['phases']] == [0.25, 0.75],
        'single-case fractions replaced by a sweep')
require(len(composite_bundle['evaluation']['evaluations']) == 8, 'composite rule count changed')
validate_composite_report(composite_bundle)
for language in languages:
    target = Path(instance_path).parent / ('composite-' + language)
    result = export_composite_report(original_case, target, lang=language)
    require(result == {'artifacts': list(ARTIFACTS), 'exit_code': 0}, 'installed composite export failed')
    require(json.loads((target/'bundle.json').read_text(encoding='utf-8')) == composite_bundle, 'language changed core')
    manifest = json.loads((target/'manifest.json').read_text(encoding='utf-8'))
    for name, entry in manifest['files'].items():
        data = (target/name).read_bytes()
        require(entry == {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}, 'manifest mismatch')
    for format in ('text', 'html'):
        text = render_composite_report(composite_bundle, lang=language, format=format)
        require('[missing:' not in text and '<script' not in text.lower(), 'unsafe or incomplete report')
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(['composite', 'verify', str(target/'bundle.json'), '--json', '--lang', language])
    require(code == 0 and json.loads(stdout.getvalue())['status'] == 'reproduced', 'installed replay failed')
unknown = build_composite_report(blank_composite_instance())
require(all(r['applicability'] == 'unknown' for r in unknown['evaluation']['evaluations']),
        'blank intake preselected scientific assumptions')
validate_composite_report(unknown)
changed = deepcopy(composite_bundle)
changed['evaluation']['evaluations'][0]['result']['lower'] += 1
try:
    validate_composite_report(changed)
except CompositeReplayError:
    pass
else:
    raise RuntimeError('installed replay accepted an altered endpoint')
require(composite_bundle['policy']['independent_scientific_review'] is False,
        'composite report upgraded scientific review')

# Concrete identities and reference facts remain a separate offline lane.
from materials_boundaries.material_references import validate_material_catalog, material_coverage, resolve_materials
from materials_boundaries.material_presentation import material_labels
materials = read_catalog('materials')
reference_properties = read_catalog('reference_properties')
reference_sources = read_catalog('sources')
validate_material_catalog(materials, reference_properties, reference_sources)
coverage = material_coverage(materials, reference_properties)
require(coverage['material_state_count'] == len(materials['records']) > 0,
        'missing installed concrete material registry')
require(coverage['property_record_count'] == len(reference_properties['records']),
        'incorrect installed material property coverage')
for resolved in resolve_materials([state['id'] for state in materials['records']],
                                  materials, reference_properties, reference_sources):
    require(bool(resolved['properties']) and bool(resolved['sources']),
            'installed material state has no traceable property')
    require(all(p['evaluation_support'] == 'catalog_only' and p['universal_bound'] is False
                and p['engineering_allowable'] is False for p in resolved['properties']),
            'reference data acquired engineering capability')
for kind in ('materials', 'reference-properties'):
    canonical = None
    for language in languages:
        for as_json in (False, True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(['catalog', kind, '--lang', language, '--json' if as_json else '--text'])
            text = stdout.getvalue()
            require(code == 0 and '[missing:' not in text, 'installed material CLI failed')
            if as_json:
                if canonical is None:
                    canonical = text
                require(text == canonical, 'language changed canonical material JSON')
            else:
                labels = material_labels(language)
                require(labels['caveat'] in text and labels['unknown_notice'] in text,
                        'installed material caveat or unknown disclosure missing')
wrong = deepcopy(reference_properties)
wrong['records'][0]['engineering_allowable'] = True
rejects(lambda: validate_material_catalog(materials, wrong, reference_sources),
        'installed material contract accepted an engineering allowable')


# New evidence classes retain their exact method and dimensional meaning after
# installation. Coverage is derived, never inflated by aliases or grade labels.
new_reference_classes = {
    'published_handbook_reference': ('source_reports_compiled_measurements', {'source_reported_compilation'}),
    'published_measurement_derived_reference': ('source_reports_calculation', {
        'source_reported_crystallographic_derivation', 'source_reported_empirical_conversion'}),
}
empirical_profile_negative_checked = False
for evidence_kind, (basis, methods) in new_reference_classes.items():
    selected = query_catalog('reference-properties', evidence_kind=evidence_kind)
    require(bool(selected['records']), 'missing installed expanded evidence class')
    for prop in selected['records']:
        method = prop['method_definition']['type']
        require(prop['determination_basis'] == basis and method in methods,
                'installed reference lost its source method')
        if method == 'source_reported_crystallographic_derivation':
            require(prop['quantity'] == 'mass_density' and prop['density_basis'] == 'crystallographic',
                    'crystallographic density became bulk density')
        elif method == 'source_reported_empirical_conversion':
            require(prop['quantity'] == 'basic_wood_density'
                    and prop['density_basis'] == 'oven_dry_mass_over_fresh_or_water_saturated_volume'
                    and prop['derivation']['profile_id'] == 'gwdd_airdry_sg_to_basic_density_v2_1',
                    'converted basic density lost its typed physical basis')
        # Keep every legacy-row negative check; one new-profile mutation avoids
        # repeating full-graph validation per member of a 1,000-row import.
        if method != 'source_reported_empirical_conversion' or not empirical_profile_negative_checked:
            altered = deepcopy(reference_properties)
            target = next(item for item in altered['records'] if item['id'] == prop['id'])
            target.update(evidence_kind='published_experimental_reference', determination_basis='source_reports_measurement')
            rejects(lambda: validate_material_catalog(materials, altered, reference_sources),
                    'installed expanded provenance accepted direct-experiment relabel')
            if method == 'source_reported_empirical_conversion':
                empirical_profile_negative_checked = True
    for language in languages:
        labels = material_labels(language)
        output = render_catalog(selected, 'reference-properties', language)
        require(labels['code_' + evidence_kind] in output and labels['code_' + basis] in output,
                'missing installed expanded provenance translation')
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(['catalog', 'reference-properties', '--evidence-kind', evidence_kind,
                         '--lang', language, '--json'])
        require(code == 0 and json.loads(stdout.getvalue()) == selected,
                'expanded exact evidence filter changed by language')

# Generic CI and unspecified-± metadata remain lossless in an isolated install.
uncertainty_variants = {'reported_confidence_interval': 'confidence_interval',
                        'reported_plus_minus_unspecified': 'plus_minus_unspecified'}
for uncertainty_kind, label in uncertainty_variants.items():
    selected_rows = [p for p in reference_properties['records']
                     if p['uncertainty_status'] == uncertainty_kind]
    require(bool(selected_rows), 'missing installed uncertainty variant')
    for prop in selected_rows:
        selected = query_catalog('reference-properties', record_id=prop['id'])
        uncertainty = prop['uncertainty']
        require(uncertainty['type'] == uncertainty_kind, 'installed uncertainty type/status mismatch')
        for language in languages:
            labels = material_labels(language)
            text = render_catalog(selected, 'reference-properties', language)
            require(labels[label] + ': ' + uncertainty['value_text'] + ' ' + uncertainty['unit_text'] in text,
                    'installed uncertainty mislabeled or amplitude missing')
            require(labels['standard_deviation'] + ':' not in text and labels['statistics_notice'] not in text,
                    'installed non-SD uncertainty displayed as SD')
            require(prop['uncertainty_note'] in text and prop['sample_count']['scope'] in text,
                    'installed source expression or sample scope lost')
            if uncertainty_kind == 'reported_confidence_interval':
                require(labels['confidence_level'] + ': ' + uncertainty['confidence_level']['value_text'] in text,
                        'installed CI level lost')
                for key in ('estimand', 'construction'):
                    require(labels[key] + ':' in text, 'installed CI definition omitted')
            window = prop['method_definition']['extraction_window']
            if window is not None:
                require(window['text'] in text, 'installed extraction window lost')
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(['catalog', 'reference-properties', '--id', prop['id'], '--lang', language, '--json'])
            require(code == 0 and json.loads(stdout.getvalue()) == selected,
                    'installed uncertainty CLI JSON changed by language')
        for mutation in ('status', 'amplitude', 'unit', 'confidence'):
            altered = deepcopy(reference_properties)
            target = next(p for p in altered['records'] if p['id'] == prop['id'])
            if mutation == 'status': target['uncertainty_status'] = 'not_reported_in_inspected_source'
            elif mutation == 'amplitude': target['uncertainty'] = None
            elif mutation == 'unit': target['uncertainty']['unit_code'] = 'kg/m^3'
            elif uncertainty_kind == 'reported_confidence_interval':
                target['uncertainty']['confidence_level']['number'] = '100'
            else: target['uncertainty']['confidence_level'] = {'value_text':'95%', 'number':'95', 'unit_code':'percent'}
            rejects(lambda: validate_material_catalog(materials, altered, reference_sources),
                    'installed uncertainty malformed pairing accepted')

# Separately typed source-reported measures survive offline installation.
reported_measure_rows = [p for p in reference_properties['records']
                         if p['uncertainty_status'] == 'reported_measures']
require(bool(reported_measure_rows), 'missing installed reported measures')
reported_measure_kinds = set()
for prop in reported_measure_rows:
    selected = query_catalog('reference-properties', record_id=prop['id'])
    measures = prop['uncertainty']['measures']
    reported_measure_kinds.update(m['kind'] for m in measures)
    for language in languages:
        text = render_catalog(selected, 'reference-properties', language)
        require(prop['reported_value']['value_text'] in text and prop['uncertainty_note'] in text,
                'installed source expression or uncertainty explanation lost')
        for measure in measures:
            require(measure['scope'] in text, 'installed measure scope lost')
            if measure['note'] is not None:
                require(measure['note'] in text, 'installed measure qualification lost')
            value = measure['reported_value']
            if value is not None:
                require(value['value_text'] + ' ' + value['unit_text'] in text,
                        'installed separately reported measure amplitude lost')
            for item in measure['evidence']:
                require(item['locator'] in text and item['url'] in text,
                        'installed measure evidence lost')
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(['catalog', 'reference-properties', '--id', prop['id'], '--lang', language, '--json'])
        require(code == 0 and json.loads(stdout.getvalue()) == selected,
                'installed measures JSON changed by language')
    for mutation in ('empty', 'amplitude', 'unit', 'confidence', 'duplicate'):
        altered = deepcopy(reference_properties)
        target = next(p for p in altered['records'] if p['id'] == prop['id'])
        measure = target['uncertainty']['measures'][0]
        if mutation == 'empty': target['uncertainty']['measures'] = []
        elif mutation == 'amplitude':
            if measure['availability'] == 'graphical_only':
                measure['reported_value'] = {'number':'0', 'value_text':'0', 'unit_code':'MPa', 'unit_text':'MPa'}
            else: measure['reported_value'] = None
        elif mutation == 'unit':
            if measure['reported_value'] is None: measure['basis'] = 'relative_to_reported_value'
            else: measure['reported_value']['unit_code'] = 'kg/m^3' if measure['basis'] == 'relative_to_reported_value' else 'percent'
        elif mutation == 'confidence': measure['confidence_level'] = {'value_text':'95%', 'number':'95', 'unit_code':'percent'}
        else: target['uncertainty']['measures'].append(deepcopy(measure))
        rejects(lambda: validate_material_catalog(materials, altered, reference_sources),
                'installed reported measure malformed pairing accepted')
require({'standard_deviation', 'coefficient_of_variation', 'standard_error_of_mean', 'estimated_inaccuracy'} <= reported_measure_kinds,
        'installed typed reported measure family missing')
# A source scientific expression is retained, not rewritten into an integer label.
scientific_rows = [p for p in reference_properties['records'] if ' × 10' in p['reported_value']['value_text']]
require(bool(scientific_rows), 'missing installed source scientific notation')
for prop in scientific_rows:
    for language in languages:
        require(prop['reported_value']['value_text'] in render_catalog(query_catalog('reference-properties', record_id=prop['id']), 'reference-properties', language),
                'installed scientific-notation source precision lost')

# The fifth density batch is a selected source-qualified subset, never a fixed
# size for the live registry. Keep these checks additive to every earlier smoke.
porous_density_facts = {
    'ivdre2024_lpo1_rigid_pur': ('ivdre_2024_lpo_rigid_pur', '43.2', 'kg/m^3',
        'apparent', 'reported_value', None, 'polymer'),
    'kosenko2022_amd5_sps_foam': ('kosenko_2022_sps_al_foam', '0.45', 'g/cm^3',
        'not_stated', 'reported_value', None, 'metal'),
    'prasetia2024_qsuber_reproduction_cork': ('prasetia_2024_cork_physical', '0.17', 'g/cm^3',
        'not_stated', 'reported_value', 10, 'natural'),
    'drury2023_moso_bamboo_culm': ('drury_2023_bamboo_compression', '746', 'kg/m^3',
        'not_stated', 'reported_mean', 6, 'natural'),
    'drury2023_guadua_bamboo_culm': ('drury_2023_bamboo_compression', '655', 'kg/m^3',
        'not_stated', 'reported_mean', 6, 'natural'),
    'saadazzem2022_altaouab_cp_plaster': ('saad_azzem_2022_plaster_wheat_straw', '1103.13', 'kg/m^3',
        'apparent', 'reported_value', None, 'inorganic'),
    'mohajerani2019_boral_control_brick': ('mohajerani_2019_biosolids_bricks', '2122', 'kg/m^3',
        'bulk', 'reported_value', None, 'inorganic'),
    'jonczy2022_k1_quartz_arenite': ('jonczy_mucha_2022_sandstones', '2.34', 'g/cm^3',
        'bulk', 'reported_mean', 5, 'inorganic'),
}
porous_density_caveats = {
    'ivdre2024_lpo1_rigid_pur': ('Lupranol', 'not the suberin-based SPO', 'ISO 845:2006',
        '24 h', 'not total porosity', '40 kg/m³'),
    'kosenko2022_amd5_sps_foam': ('94.8 wt.% Al', '4.8 wt.% Mg', '0.4 wt.% Ti',
        '550 °C', '38 MPa', '5 min', 'paraffin', 'ethanol', 'Underwater Weight',
        'Table 6', 'g/m³', 'not a final bulk chemical assay'),
    'prasetia2024_qsuber_reproduction_cork': ('Do not count boiled cork', 'Ten specimens',
        'no independence of trees', 'KS F 2198', 'volume-measurement subprocedure is not stated',
        'never mean ± SD'),
    'drury2023_moso_bamboo_culm': ('fumigated for up to 24 h', 'Stored for one year',
        'No borax treatment is stated', 'three nodal and three internodal',
        'entire experimental cohort', 'Do not derive density', 'CC BY 3.0', 'CC BY 4.0'),
    'drury2023_guadua_bamboo_culm': ('fumigated for up to 24 h', 'Stored for one year',
        'Dipped in borax', 'internal nodes pierced', 'three nodal and three internodal',
        'entire experimental cohort', 'Do not derive density', 'CC BY 3.0', 'CC BY 4.0'),
    'saadazzem2022_altaouab_cp_plaster': ('Do not call the cured material pure dihydrate',
        '0.7', '72 h', '28 days', 'density-specific specimen dimensions are unknown'),
    'mohajerani2019_boral_control_brick': ('100 wt.%', '0% biosolids', '1100 °C',
        'Do not assign density n=3', 'shrinkage', 'regression-estimated'),
    'jonczy2022_k1_quartz_arenite': ('Five physical-property replicates',
        'without claiming an explicitly specified arithmetic',
        'does not unambiguously select exclusively geometric versus hydrostatic',
        'EN 1926:2007', 'must not be transferred', 'Do not call it SD, SE, CI'),
}
porous_density_cli_outputs = 0
for suffix, facts in porous_density_facts.items():
    source_id, number, unit, basis, statistic, count, category = facts
    property_id, state_id = 'refprop_' + suffix + '_mass_density', 'state_' + suffix
    selected = query_catalog('reference-properties', record_id=property_id, source_id=source_id)
    require([p['id'] for p in selected['records']] == [property_id],
            'missing installed source-qualified fifth-batch property: ' + suffix)
    prop = selected['records'][0]
    state = next(s for s in materials['records'] if s['id'] == state_id)
    identity = next(i for i in materials['identities'] if i['id'] == 'mat_' + suffix)
    require(state['identity_id'] == identity['id'] and state['grade_id'] is None
            and property_id in state['property_ids'] and identity['category'] == category,
            'installed fifth-batch identity/state association changed: ' + suffix)
    require((prop['material_state_id'], prop['quantity'], prop['reported_value']['kind'],
             prop['reported_value']['number'], prop['reported_value']['value_text'],
             prop['reported_value']['unit_code'], prop['density_basis'],
             prop['summary_statistic'], prop['sample_count']['value'])
            == (state_id, 'mass_density', 'scalar', number, number, unit, basis, statistic, count),
            'installed fifth-batch value, unit, density basis or statistic changed: ' + suffix)
    require(prop['conditions']['temperature']['status'] == 'not_reported_in_inspected_source'
            and prop['conditions']['temperature']['text'] is None,
            'installed fifth-batch acquired a density-test setpoint: ' + suffix)
    require(prop['evidence_kind'] == 'published_experimental_reference'
            and prop['determination_basis'] == 'source_reports_measurement'
            and prop['evaluation_support'] == 'catalog_only'
            and prop['universal_bound'] is False and prop['engineering_allowable'] is False
            and prop['verification']['independent_scientific_review'] is False
            and prop['verification']['raw_data_reanalysis'] is False,
            'installed fifth-batch source fact acquired unsupported capability: ' + suffix)
    uncertainty = prop['uncertainty']
    if suffix == 'prasetia2024_qsuber_reproduction_cork':
        require(prop['uncertainty_status'] == uncertainty['type'] == 'reported_measures'
                and len(uncertainty['measures']) == 1, 'installed cork SD envelope changed')
        measure = uncertainty['measures'][0]
        require((measure['kind'], measure['availability'], measure['basis'],
                 measure['reported_value']['number'], measure['reported_value']['value_text'],
                 measure['reported_value']['unit_code'], measure['confidence_level'], measure['coverage_factor'])
                == ('standard_deviation', 'numeric_reported', 'absolute', '0.01', '0.01', 'g/cm^3', None, None),
                'installed cork separate source SD became inferred mean/CI/error')
    elif suffix == 'jonczy2022_k1_quartz_arenite':
        require(prop['uncertainty_status'] == uncertainty['type'] == 'reported_plus_minus_unspecified'
                and (uncertainty['number'], uncertainty['value_text'], uncertainty['unit_code'],
                     uncertainty['confidence_level'], uncertainty['coverage_factor'])
                == ('0.01', '0.01', 'g/cm^3', None, None),
                'installed K1 undefined plus/minus amplitude changed')
    else:
        require(uncertainty is None and prop['uncertainty_status'] == 'not_reported_in_inspected_source',
                'installed fifth-batch unknown uncertainty was invented: ' + suffix)
    for kind, identifier in (('materials', state_id), ('reference-properties', property_id)):
        detail = query_catalog(kind, record_id=identifier, source_id=source_id)
        require([r['id'] for r in detail['records']] == [identifier], 'installed exact selector changed')
        for language in languages:
            labels = material_labels(language)
            for flag in ('--json', '--text'):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = main(['catalog', kind, '--id', identifier, '--source-id', source_id,
                                 '--lang', language, flag])
                text = stdout.getvalue()
                require(code == 0 and '[missing:' not in text, 'installed fifth-batch CLI failed')
                porous_density_cli_outputs += 1
                if flag == '--json':
                    require(json.loads(text) == detail, 'installed fifth-batch JSON changed by locale')
                else:
                    for required in (*porous_density_caveats[suffix], prop['uncertainty_note'],
                                     prop['sample_count']['scope'], prop['source_document']['sha256'],
                                     number + ' ' + prop['reported_value']['unit_text'],
                                     labels['unknown_notice'], labels['caveat'], 'CC-BY-4.0'):
                        require(required in text, 'installed fifth-batch disclosure lost: ' + required)
                    if suffix == 'prasetia2024_qsuber_reproduction_cork':
                        require(labels['central_aggregation_unknown_notice'] in text
                                and labels['standard_deviation'] + ': 0.01 g/cm³' in text,
                                'installed cork central-statistic unknown/SD disclosure lost')
                    elif suffix == 'jonczy2022_k1_quartz_arenite':
                        require(labels['plus_minus_unspecified'] + ': 0.01 g/cm³' in text
                                and labels['standard_deviation'] + ':' not in text,
                                'installed K1 undefined amplitude was relabeled SD')
require(porous_density_cli_outputs == 128, 'installed fifth-batch detail coverage incomplete')

# The six independently source-qualified v0.34 selections stay catalog-only.
polymer_facts = {
    'ewurum2025_biopbs': ('youngs_modulus', '575', 'MPa', '65', 'reported_mean', 'reported_standard_deviation', 10, 'exact'),
    'ewurum2025_pbs_lignin20': ('youngs_modulus', '960', 'MPa', '77', 'reported_mean', 'reported_standard_deviation', 10, 'exact'),
    'ewurum2025_indulin_at': ('mass_density', '1.226', 'g/cm^3', None, 'reported_value', 'not_reported_in_inspected_source', None, 'not_reported'),
    'abbasi2022_manure_phbv39': ('youngs_modulus', '0.87', 'GPa', '0.04', 'reported_mean', 'reported_standard_deviation', 5, 'at_least'),
    'mtibe2022_pbat_ecoflex_c1200': ('tensile_modulus', '52.01', 'MPa', '28.78', 'reported_value', 'reported_plus_minus_unspecified', 5, 'exact'),
    'mtibe2022_pbs_pbat_70_30': ('tensile_modulus', '253.49', 'MPa', '13.40', 'reported_value', 'reported_plus_minus_unspecified', 5, 'exact'),
}
polymer_cli_outputs = 0
for suffix, facts in polymer_facts.items():
    quantity, number, unit, amplitude, statistic, uncertainty_kind, count, relation = facts
    property_id, state_id = 'refprop_' + suffix + '_' + quantity, 'state_' + suffix
    detail = query_catalog('reference-properties', record_id=property_id)
    require(len(detail['records']) == 1, 'missing installed polymer fact: ' + suffix)
    prop = detail['records'][0]
    require((prop['quantity'], prop['reported_value']['number'], prop['reported_value']['unit_code'],
             (prop['uncertainty'] or {}).get('number'), prop['summary_statistic'],
             prop['uncertainty_status'], prop['sample_count']['value'], prop['sample_count']['relation']) == facts,
            'installed polymer source semantics changed: ' + suffix)
    require(prop['evaluation_support'] == 'catalog_only' and prop['universal_bound'] is False
            and prop['engineering_allowable'] is False and prop['verification']['independent_scientific_review'] is False
            and prop['verification']['raw_data_reanalysis'] is False, 'installed polymer capability changed')
    for kind, identifier in (('materials', state_id), ('reference-properties', property_id)):
        selected = query_catalog(kind, record_id=identifier, source_id=prop['source_id'])
        for language in languages:
            for flag in ('--text', '--json'):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = main(['catalog', kind, '--id', identifier, '--source-id', prop['source_id'], '--lang', language, flag])
                rendered = stdout.getvalue()
                require(code == 0 and '[missing:' not in rendered, 'installed polymer CLI failed')
                if flag == '--json':
                    require(json.loads(rendered) == selected, 'installed polymer JSON depends on language')
                else:
                    require(number in rendered and prop['uncertainty_note'] in rendered,
                            'installed polymer result or source caveat lost')
                polymer_cli_outputs += 1
# The reviewed v2 batch is a fixed admission subset, not a live-registry ceiling.
from decimal import Decimal
from materials_boundaries.material_references import material_quota_coverage
from materials_boundaries.wood_bulk_adapter import REVIEWED_BATCH_SHA256
reviewed_wood = [p for p in reference_properties['records']
                 if p.get('derivation', {}).get('provenance', {}).get('reviewed_batch_sha256') == REVIEWED_BATCH_SHA256]
require(len(reviewed_wood) == 1000, 'installed reviewed wood batch is incomplete')
wood_identities = {i['id']: i for i in materials['identities']}
wood_states = {r['id']: r for r in materials['records']}
wood_keys = set()
for prop in reviewed_wood:
    derived = prop['derivation']; formula = derived['formula']; original = derived['input']; output = derived['deposited_output']
    identity = wood_identities[wood_states[prop['material_state_id']]['identity_id']]
    require(identity['category'] == 'natural', 'installed wood identity category changed')
    wood_keys.add(identity['canonical_taxon']['identity_key'])
    require(original['number'] == original['value_text']
            and original['unit_code'] == 'dimensionless'
            and original['evidence_type'] == 'source_reported_measured_input',
            'installed measured original SG string or evidence class changed')
    require(formula['coefficient'] == '0.8281316' and formula['water_density_convention_g_cm3'] == '1'
            and formula['nominal_conversion_moisture_percent'] == '12'
            and formula['measured_specimen_moisture_percent'] is None
            and formula['basis_convention_source_id'] == 'fischer_2026_gwdd_methods',
            'installed conversion coefficient or specimen moisture semantics changed')
    require(abs(Decimal(original['number']) * Decimal('0.8281316') - Decimal(output['number'])) < Decimal('0.005')
            and Decimal(derived['si_output']['number']) == Decimal(output['number']) * 1000,
            'installed deposited conversion or exact SI calculation changed')
    require(any(e['source_id'] == formula['basis_convention_source_id'] for e in derived['evidence'])
            and any(e['source_id'] == formula['basis_convention_source_id'] for e in prop['method_definition']['evidence']),
            'installed basic-density convention lost its source binding')
    require(prop['reported_value']['number'] == output['number']
            and prop['reported_value']['value_text'] == output['number']
            and prop['summary_statistic'] == 'reported_value'
            and prop['uncertainty'] is None and prop['sample_count']['value'] is None,
            'installed converted output became a measurement, species mean or independently counted sample')
    require(derived['specimen_scope']['exact_test_temperature'] is None
            and derived['specimen_scope']['exact_moisture'] is None,
            'installed specimen conditions were inferred')
require(len(wood_keys) == 1000, 'installed reviewed batch double-counts biological identities')
quota = material_quota_coverage(materials, reference_properties, reference_sources)
require(set(quota['classes']) == {'metal', 'inorganic', 'polymer', 'composite', 'natural'}
        and quota['classes']['natural']['admitted_unique_identity_count'] >= 1010,
        'installed five-class coverage is incomplete')
for language in languages:
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(['coverage', '--lang', language, '--json'])
    require(code == 0 and json.loads(stdout.getvalue()) == quota, 'installed quota JSON depends on language')
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(['coverage', '--lang', language, '--text'])
    require(code == 0 and '[missing:' not in stdout.getvalue(), 'installed quota translation missing')
# Repeated valid calls cannot cache acceptance of a later invalid full graph.
resolve_materials([materials['records'][0]['id']], materials, reference_properties, reference_sources)
poisoned = deepcopy(reference_properties); poisoned['records'][-1]['engineering_allowable'] = True
rejects(lambda: resolve_materials([materials['records'][0]['id']], materials, poisoned, reference_sources),
        'installed graph resolver reused stale validation or skipped an unselected invalid row')

print(json.dumps({"version": expected, "metadata_version": metadata_version,
                  "reviewed_wood_batch_sha256": REVIEWED_BATCH_SHA256,
                  "reviewed_wood_identities": len(wood_keys), "reviewed_wood_properties": len(reviewed_wood),
                  "fresh_mutated_graph_rejected": True, "material_quota_languages": languages,
                  "material_polymer_identities": len(polymer_facts),
                  "material_polymer_cli_outputs": polymer_cli_outputs,
                  "material_porous_density_identities": len(porous_density_facts),
                  "material_porous_density_cli_outputs": porous_density_cli_outputs,
                  "material_porous_density_languages": languages,
                  "material_reported_measure_kinds": sorted(reported_measure_kinds), "material_reported_measure_languages": languages,
                  "material_uncertainty_types": sorted(uncertainty_variants), "material_uncertainty_languages": languages,
                  "reported_extraction_windows": sum(p["method_definition"]["extraction_window"] is not None for p in reference_properties["records"]),
                  "engine_outputs": sorted(outputs), "languages": languages,
                  "installed_without_dependencies": True, "composite_report_languages": languages, "composite_report_schema": "1.0.0", "composite_exact_single_case_and_replay": True, "mixed_observation_catalog_languages": languages, "bulk_wave_catalog_languages": languages, "viscoelastic_catalog_languages": languages, "hbn_observation_languages": languages, "observation_inspection_languages": languages, "observation_inspection_schema": "1.1.0", "pa12_export_checks": export_checks, "pa12_scientific_mutations_rejected": len(mutations), "pa12_exact_selected_cells": len(expected_cells), "temperature_observation_plot_languages": languages, "temperature_observation_plot_schema": "1.0.0", "temperature_observation_plot_cells": len(plot_bundle["glyphs"]), "paht_exact_median_sd_cells": len(paht), "paht_four_language_inspection": True, "study_comparison_languages": languages, "study_comparison_schema": "1.0.0", "study_comparison_cells": 10}))
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
        # Windows CreateProcess has a command-line limit below this check's
        # length. Execute its exact UTF-8 bytes as a local isolated script.
        installed_check = work / "installed_check.py"
        installed_check.write_text(INSTALLED_CHECK, encoding="utf-8")
        result = subprocess.run([str(python), "-I", str(installed_check), expected,
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
