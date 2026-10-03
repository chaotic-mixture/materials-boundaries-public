"""Closed six-cell descriptive plot checks, not scientific/statistical validation.

The fixture is an independent source transcription. The new plot is deliberately
separate from inspection-only cards and executable temperature/material models.
"""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from copy import deepcopy
from decimal import Inexact, Rounded, localcontext
import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from materials_boundaries import observation_temperature_plot as plot
from materials_boundaries import observation_visualization as inspection
from materials_boundaries._pa12_cf15_observation_contract import (
    PA12_ARTIFACT, PA12_DATASET, PA12_FAMILY, PA12_PROTOCOL, PA12_QUANTITY, PA12_SOURCE,
)
from materials_boundaries._version import __version__
from materials_boundaries.catalog import read_catalog
from materials_boundaries.cli import main
from materials_boundaries.validation import ValidationError

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('en', 'zh', 'ja', 'de')
SVG = '{http://www.w3.org/2000/svg}'
PREFIX = 'observation-temperature-plot'
LOWER = ('48.19', '39.59', '31.52', '25.45', '21.81', '17.77')
UPPER = ('49.95', '41.03', '33.88', '27.75', '23.75', '19.59')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def lookup(value, path):
    for key in path:
        value = value[key]
    return value


def replace(value, path, replacement):
    lookup(value, path[:-1])[path[-1]] = replacement


def leaves(value, prefix=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, prefix + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, prefix + (index,))
    else:
        yield prefix, value


def altered(value):
    if value is None:
        return 0
    if type(value) is bool:
        return not value
    if type(value) in (int, float):
        return value + 1
    return value + ' unreviewed'


@contextmanager
def catalogs(observations=None, sources=None):
    values = {
        'observations': deepcopy(read_catalog('observations') if observations is None else observations),
        'sources': deepcopy(read_catalog('sources') if sources is None else sources),
    }
    def reader(name):
        if name not in values:
            raise AssertionError('Unexpected catalog read: ' + name)
        return deepcopy(values[name])
    with patch.object(plot, 'read_catalog', side_effect=reader):
        yield


class ParsedHTML(HTMLParser):
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.text = []
        self.visible = []
        self.pre_contents = {}
        self.pre_in_details = set()
        self._details_depth = 0
        self._nonvisible_depth = 0
        self._pre_id = None
        self.feed(value)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == 'details':
            self._details_depth += 1
        if tag in ('style', 'script'):
            self._nonvisible_depth += 1
        if tag == 'pre' and 'id' in attrs:
            self._pre_id = attrs['id']
            self.pre_contents[self._pre_id] = []
            if self._details_depth:
                self.pre_in_details.add(self._pre_id)

    def handle_endtag(self, tag):
        if tag == 'details':
            self._details_depth -= 1
        if tag in ('style', 'script'):
            self._nonvisible_depth -= 1
        if tag == 'pre':
            self._pre_id = None

    def handle_data(self, data):
        self.text.append(data)
        if not self._details_depth and not self._nonvisible_depth:
            self.visible.append(data)
        if self._pre_id is not None:
            self.pre_contents[self._pre_id].append(data)


def by_class(root, name):
    return [node for node in root.iter() if name in node.attrib.get('class', '').split()]


class ObservationTemperaturePlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observations = read_catalog('observations')
        cls.sources = read_catalog('sources')
        cls.fixture = json.loads((ROOT / 'tests/fixtures/pa12_cf15_source_transcription.json').read_text())
        cls.bundle = plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)
        cls.ids = [r['id'] for r in cls.bundle['record_snapshots']]
        cls.outputs = (plot.validate_observation_temperature_plot,
                       plot.temperature_observation_plot_json,
                       plot.temperature_observation_plot_csv,
                       plot.render_observation_temperature_svg,
                       plot.render_observation_temperature_html)

    def assert_rejected_by_outputs(self, value):
        for output in self.outputs:
            with self.subTest(output=output.__name__):
                with self.assertRaises(plot.ObservationTemperaturePlotError):
                    output(value)

    def test_exact_closed_group_selection_source_snapshots_and_versions(self):
        b = self.bundle
        self.assertTrue(issubclass(plot.ObservationTemperaturePlotError, ValidationError))
        self.assertEqual(b['kind'], 'observation_temperature_plot')
        self.assertEqual(b['schema_version'], '1.0.0')
        self.assertEqual(b['engine_version'], __version__)
        self.assertEqual(b['catalog_schema_versions'], {'observations': '1.3.0', 'sources': '1.0.0'})
        self.assertEqual(b['selection']['dataset_id'], PA12_DATASET)
        self.assertEqual(b['selection']['resolved_record_ids'], self.ids)
        self.assertEqual(b['selection']['resolved_source_cells'], [r['source_cell'] for r in b['record_snapshots']])
        self.assertEqual(len(b['record_snapshots']), 6)
        self.assertEqual(b['source_snapshots'], [next(s for s in self.sources['records'] if s['id'] == PA12_SOURCE)])
        self.assertEqual(b['group']['study_id'], PA12_SOURCE)
        self.assertEqual(b['group']['dataset_id'], PA12_DATASET)
        self.assertEqual(b['group']['protocol_id'], PA12_PROTOCOL)
        self.assertEqual(b['group']['method_family'], PA12_FAMILY)
        self.assertEqual(b['group']['quantity'], PA12_QUANTITY)
        for key in ('profile_id', 'profile_version', 'compatibility_basis', 'limitations'):
            self.assertTrue(b['group'][key])
        self.assertNotIn('groups', b)
        for r, d in zip(b['record_snapshots'], b['record_digests']):
            self.assertEqual(d['record_id'], r['id'])
            self.assertEqual(d['sha256'], digest(r))
        self.assertEqual(b['source_digests'][0]['sha256'], digest(b['source_snapshots'][0]))

    def test_exact_source_strings_endpoints_si_and_every_fixture_fact(self):
        b = self.bundle
        self.assertEqual(len(b['glyphs']), 6)
        original = {r['id']: r for r in self.observations['records']}
        for i, (cell, r, g) in enumerate(zip(self.fixture['cells'], b['record_snapshots'], b['glyphs'])):
            with self.subTest(temperature=cell['temperature']):
                self.assertEqual(r, original[r['id']])
                for path, expected in self.fixture['facts_by_record_path'].items():
                    self.assertEqual(lookup(r, path.split('/')), expected, path)
                self.assertEqual(g['record_id'], r['id'])
                self.assertEqual(g['source_cell'], r['source_cell'])
                self.assertEqual(g['temperature_value_string'], cell['temperature'])
                self.assertEqual(g['temperature_unit'], 'degC')
                self.assertEqual(g['central_value_string'], cell['central'])
                self.assertEqual(g['sd_value_string'], cell['sd'])
                self.assertEqual(g['source_value_string'], cell['central'] + ' ± ' + cell['sd'])
                self.assertEqual(g['unit'], 'MPa')
                self.assertEqual(g['uncertainty_type'], 'reported_standard_deviation')
                self.assertEqual(g['sample_count'], 3)
                self.assertIsNone(g['temperature_uncertainty'])
                self.assertEqual(g['derived_lower_string'], LOWER[i])
                self.assertEqual(g['derived_upper_string'], UPPER[i])
                self.assertEqual(g['derivation'], 'decimal_central_plus_minus_reported_sd_for_glyph_only')
                self.assertEqual(r['si_result']['value'], cell['pa'])
                self.assertEqual(r['si_result']['uncertainty_value'], cell['sd_pa'])
                self.assertEqual(r['sample_metadata']['scope'], 'tensile_tests_per_temperature_condition')
                self.assertIsNone(r['sample_metadata']['replicate_independence'])
                for forbidden in ('mean', 'sem', 'ci', 'rank', 'ratio', 'si_glyph'):
                    self.assertNotIn(forbidden, g)

    def test_fresh_decimal_context_is_independent_of_caller_precision_and_traps(self):
        expected = plot.temperature_observation_plot_json(self.bundle)
        with localcontext() as ctx:
            ctx.prec = 1
            ctx.Emax = 1
            ctx.Emin = -1
            ctx.traps[Inexact] = True
            ctx.traps[Rounded] = True
            actual = plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)
            self.assertEqual(plot.temperature_observation_plot_json(actual), expected)
            for width in (320, 380, 1100, 1600):
                ET.fromstring(plot.render_observation_temperature_svg(actual, width=width))

    def test_fixed_axes_and_scientific_presentation_restrictions(self):
        p = self.bundle['presentation_policy']
        self.assertEqual(p['axes']['x']['domain'], [15, 125])
        self.assertEqual(p['axes']['x']['ticks'], [23, 40, 60, 80, 100, 120])
        self.assertEqual(p['axes']['x']['unit'], 'degC')
        self.assertEqual(p['axes']['y']['domain'], [0, 55])
        self.assertEqual(p['axes']['y']['ticks'], [0, 10, 20, 30, 40, 50])
        self.assertEqual(p['axes']['y']['unit'], 'MPa')
        self.assertEqual(p['axes']['y']['quantity'], PA12_QUANTITY)
        self.assertEqual(p['axes']['x']['scale'], 'linear')
        self.assertEqual(p['axes']['y']['scale'], 'linear')
        self.assertEqual(p['evaluation_support'], 'catalog_only')
        self.assertIs(p['whiskers_required'], True)
        self.assertIsNone(p['temperature_uncertainty'])
        self.assertIsNone(p['central_statistic_explicitly_named'])
        self.assertIsNone(p['aggregation_convention'])
        self.assertIsNone(p['replicate_independence'])
        for key in ('derived_glyph_endpoints_are_observations', 'unknown_conditions_equivalent',
                    'standard_deviation_is_sem', 'standard_deviation_is_confidence_interval',
                    'standard_deviation_is_observed_min_max', 'standard_deviation_is_hard_bound',
                    'standard_deviation_asserts_coverage', 'overlay_allowed', 'additional_groups_allowed',
                    'fit_allowed', 'connecting_lines_allowed', 'interpolation_allowed',
                    'extrapolation_allowed', 'aggregation_allowed', 'normalization_allowed',
                    'ranking_allowed', 'percent_change_allowed', 'significance_test_allowed',
                    'material_prediction_allowed', 'design_allowable_allowed', 'safety_claim_allowed',
                    'formula_execution_allowed', 'geometry_or_thickness_conversion_allowed',
                    'second_plotted_series_allowed'):
            self.assertIs(p[key], False, key)
        self.assertEqual(self.bundle['policy_digest_sha256'], digest(p))

    def test_explicit_selector_rejects_missing_unknown_partial_or_nonscalar_inputs(self):
        with self.assertRaises(TypeError):
            plot.build_observation_temperature_plot()
        for dataset in ('', 'all', PA12_SOURCE, PA12_DATASET + ' ', ' ' + PA12_DATASET,
                        PA12_DATASET.upper(), None, True, 1, [], {}, [PA12_DATASET]):
            with self.subTest(dataset=dataset), self.assertRaises(plot.ObservationTemperaturePlotError):
                plot.build_observation_temperature_plot(dataset_id=dataset)
        with self.assertRaises(TypeError):
            plot.build_observation_temperature_plot(dataset_id=PA12_DATASET, record_ids=self.ids[:1])

    def test_reversed_catalog_order_restores_table_order_without_mutation(self):
        changed = deepcopy(self.observations)
        changed['records'].reverse()
        before = deepcopy(changed)
        with catalogs(changed):
            actual = plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)
            self.assertEqual(actual, self.bundle)
            self.assertEqual(plot.temperature_observation_plot_json(actual), plot.temperature_observation_plot_json(self.bundle))
        self.assertEqual(changed, before)

    def test_approved_ids_and_names_can_change_without_creating_cells(self):
        changed = deepcopy(self.observations)
        records = sorted((r for r in changed['records'] if r.get('dataset_id') == PA12_DATASET),
                         key=lambda r: int(r['source_cell']['temperature_column']))
        for i, r in enumerate(records):
            r['id'] = 'renamed-temperature-cell-' + str(i)
            r['name'] = '=literal, "renamed" <PA12 & source> ' + str(i)
        with catalogs(changed):
            b = plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)
            self.assertEqual(b['selection']['resolved_record_ids'], [r['id'] for r in records])
            self.assertEqual([g['source_cell'] for g in b['glyphs']], [g['source_cell'] for g in self.bundle['glyphs']])
            rows = list(csv.DictReader(io.StringIO(plot.temperature_observation_plot_csv(b))))
            for r, row in zip(records, rows):
                self.assertEqual(json.loads(row['record_snapshot_json']), r)
            html = plot.render_observation_temperature_html(b)
            svg = plot.render_observation_temperature_svg(b)
            self.assertIn('&lt;PA12 &amp; source&gt;', html)
            self.assertIn('&lt;PA12 &amp; source&gt;', svg)
            self.assertNotIn('<PA12 & source>', html)
            ET.fromstring(svg)

    def test_partial_duplicate_extra_and_family_marker_evasion_rejected(self):
        baseline = deepcopy(self.observations)
        records = [r for r in baseline['records'] if r.get('dataset_id') == PA12_DATASET]
        mutations = []
        partial = deepcopy(baseline)
        partial['records'] = [r for r in partial['records'] if r['id'] != self.ids[-1]]
        mutations.append(('partial', partial))
        for name, adjust in (
            ('alias', lambda r: r.update(id='duplicate-source-cell', name='Unreviewed alias')),
            ('seventh', lambda r: r['source_cell'].update(temperature_column='140')),
            ('other_quantity', lambda r: r.update(quantity='youngs_modulus_3d')),
            ('other_family', lambda r: r.update(method_family='unreviewed_family')),
        ):
            data = deepcopy(baseline); alias = deepcopy(records[0])
            alias['id'] = name + '-unreviewed-cell'
            adjust(alias)
            data['records'].append(alias); mutations.append((name, data))
        for key in ('method_family', 'study_id', 'dataset_id', 'protocol_id', 'source_cell'):
            data = deepcopy(baseline)
            next(r for r in data['records'] if r['id'] == self.ids[0]).pop(key)
            mutations.append(('removed_' + key, data))
        data = deepcopy(baseline)
        disguised = next(r for r in data['records'] if r['id'] == self.ids[0])
        for key in ('method_family', 'study_id', 'dataset_id', 'protocol_id', 'source_cell'):
            disguised.pop(key)
        disguised['quantity'] = 'generic_pressure_shaped_value'
        mutations.append(('removed_all_identity_markers', data))
        for name, data in mutations:
            with self.subTest(name=name), catalogs(data):
                with self.assertRaises(plot.ObservationTemperaturePlotError):
                    plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)

    def test_current_payload_edits_reject_admission_including_unknowns_and_process(self):
        paths = [
            ('source_cell', 'temperature_column'), ('reported_result', 'value_string'),
            ('reported_result', 'source_value_string'), ('reported_result', 'value'),
            ('reported_result', 'uncertainty', 'type'), ('reported_result', 'uncertainty', 'value'),
            ('reported_result', 'summary_statistic'), ('reported_result', 'aggregation_convention'),
            ('sample_metadata', 'count'), ('sample_metadata', 'scope'),
            ('sample_metadata', 'replicate_independence'), ('conditions', 'temperature', 'value'),
            ('conditions', 'temperature', 'direct_specimen_temperature_measurement'),
            ('conditions', 'humidity', 'specimen_moisture_content'),
            ('method', 'stress_area_basis'), ('method', 'stress_measure'),
            ('method', 'loading_rate', 'value'), ('method', 'specimen', 'thickness_mm'),
            ('method', 'preparation', 'printing_parameters', 'raster_methods_description'),
            ('method', 'preparation', 'printing_parameters', 'build_orientation'),
            ('method', 'preparation', 'printing_parameters', 'infill_setting_percent'),
            ('method', 'preparation', 'filament_drying', 'duration', 'value'),
            ('material', 'reinforcement_mass_fraction', 'value'), ('material', 'measured_porosity'),
            ('verification', 'source_inspection', 'pdf_equivalence_claimed'),
            ('verification', 'source_inspection', 'raw_data_reanalysis'),
            ('verification', 'rights', 'source_assets_redistributed'),
            ('verification', 'rights', 'license_identifier'), ('quantity',), ('quantity_dimension',),
            ('si_result', 'normalization', 'factor_string'), ('version',),
        ]
        for path in paths:
            data = deepcopy(self.observations)
            record = next(r for r in data['records'] if r['id'] == self.ids[0])
            replace(record, path, altered(lookup(record, path)))
            with self.subTest(path=path), catalogs(data):
                with self.assertRaises(plot.ObservationTemperaturePlotError):
                    plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)

    def test_stale_catalog_admission_is_rechecked_by_every_output_and_export(self):
        data = deepcopy(self.observations)
        next(r for r in data['records'] if r['id'] == self.ids[0])['reported_result']['value'] += 1
        source_data = deepcopy(self.sources)
        next(s for s in source_data['records'] if s['id'] == PA12_SOURCE)['doi'] = '10.0000/unreviewed'
        for changes in ({'observations': data}, {'sources': source_data}):
            with self.subTest(changes=tuple(changes)), catalogs(**changes):
                self.assert_rejected_by_outputs(self.bundle)
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / 'new'
                    with self.assertRaises(plot.ObservationTemperaturePlotError):
                        plot.export_observation_temperature_plot(target, dataset_id=PA12_DATASET)
                    self.assertFalse(target.exists())

    def test_actual_referenced_source_removal_and_unsafe_urls_rejected(self):
        for key, value in (('doi', '10.0000/unreviewed'), ('title', 'Different paper'),
                           ('urls', ['javascript:alert(1)']), ('urls', ['data:text/html,unsafe']),
                           ('urls', ['https://user:password@example.test/'])):
            data = deepcopy(self.sources)
            source = next(s for s in data['records'] if s['id'] == PA12_SOURCE)
            source[key] = value
            with self.subTest(key=key, value=value), catalogs(sources=data):
                with self.assertRaises(plot.ObservationTemperaturePlotError):
                    plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)
        data = deepcopy(self.sources)
        data['records'] = [s for s in data['records'] if s['id'] != PA12_SOURCE]
        with catalogs(sources=data), self.assertRaises(plot.ObservationTemperaturePlotError):
            plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)

    def test_every_policy_and_group_leaf_is_closed_even_with_matching_snapshot_digests(self):
        for section in ('presentation_policy', 'group'):
            for path, value in leaves(self.bundle[section]):
                changed = deepcopy(self.bundle)
                replace(changed[section], path, altered(value))
                if section == 'presentation_policy':
                    changed['policy_digest_sha256'] = digest(changed[section])
                with self.subTest(section=section, path=path), self.assertRaises(plot.ObservationTemperaturePlotError):
                    plot.validate_observation_temperature_plot(changed)
        for section, index, path in (
            ('record_snapshots', 0, ('conditions', 'humidity', 'specimen_moisture_content')),
            ('record_snapshots', 0, ('reported_result', 'uncertainty', 'type')),
            ('record_snapshots', 0, ('name',)),
            ('source_snapshots', 0, ('doi',)),
            ('source_snapshots', 0, ('title',)),
        ):
            changed = deepcopy(self.bundle)
            snapshot = changed[section][index]
            replace(snapshot, path, altered(lookup(snapshot, path)))
            digest_section = 'record_digests' if section == 'record_snapshots' else 'source_digests'
            changed[digest_section][index]['sha256'] = digest(snapshot)
            with self.subTest(section=section, path=path):
                self.assert_rejected_by_outputs(changed)

    def test_bundle_versions_orders_extra_groups_endpoints_and_uncertainty_are_closed(self):
        changes = [
            (('kind',), 'observation_inspection'), (('schema_version',), '0.0.0'),
            (('engine_version',), '0.0.0'), (('catalog_schema_versions', 'observations'), '1.2.0'),
            (('catalog_schema_versions', 'sources'), '0.0.0'),
            (('selection', 'dataset_id'), 'all'),
            (('selection', 'resolved_record_ids'), list(reversed(self.ids))),
            (('selection', 'resolved_source_cells'), list(reversed(self.bundle['selection']['resolved_source_cells']))),
            (('record_snapshots',), list(reversed(self.bundle['record_snapshots']))),
            (('glyphs',), list(reversed(self.bundle['glyphs']))),
            (('glyphs', 0, 'derived_lower_string'), '48.18'),
            (('glyphs', 0, 'derived_upper_string'), '49.96'),
            (('glyphs', 0, 'central_value_string'), '49.070'),
            (('glyphs', 0, 'sd_value_string'), '0.00'),
            (('glyphs', 0, 'uncertainty_type'), 'confidence_interval'),
            (('glyphs', 0, 'sample_count'), True),
            (('glyphs', 0, 'temperature_uncertainty'), 0),
            (('glyphs', 0, 'source_cell', 'temperature_column'), '40'),
            (('glyphs', 0, 'derivation'), 'normal_95_percent_ci'),
            (('record_digests', 0, 'sha256'), '0' * 64),
            (('source_digests', 0, 'sha256'), '0' * 64),
            (('groups',), [self.bundle['group'], self.bundle['group']]),
            (('unreviewed',), True),
        ]
        for path, value in changes:
            changed = deepcopy(self.bundle); replace(changed, path, value)
            with self.subTest(path=path):
                self.assert_rejected_by_outputs(changed)

    def test_malformed_nonfinite_nonjson_and_boolean_numeric_bundles_rejected(self):
        for value in (None, [], '', True, 0, {'selection': []}):
            self.assert_rejected_by_outputs(value)
        for value in (float('nan'), float('inf'), -float('inf'), True, object(), {'nonjson'}, b'23'):
            changed = deepcopy(self.bundle)
            changed['glyphs'][0]['sample_count'] = value
            with self.subTest(value=repr(value)):
                self.assert_rejected_by_outputs(changed)
        changed = deepcopy(self.bundle); changed[1] = 'non-string-key'
        self.assert_rejected_by_outputs(changed)

    def test_xml_illegal_catalog_name_or_id_rejected_without_output(self):
        for field in ('name', 'id'):
            for suffix in ('\x00', '\x01', '\ud800', '\uffff'):
                data = deepcopy(self.observations)
                record = next(r for r in data['records'] if r['id'] == self.ids[0])
                record[field] += suffix
                with self.subTest(field=field, suffix=repr(suffix)), catalogs(data):
                    with self.assertRaises(plot.ObservationTemperaturePlotError):
                        plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)

    def test_catalog_display_names_and_identifiers_are_inert_escaped_strings(self):
        data = deepcopy(self.observations)
        r = next(record for record in data['records'] if record['id'] == self.ids[0])
        attack = '=literal, "quote" </pre><script>alert(1)</script><img src=x onerror=alert(2)> & Ω'
        r['name'] = attack
        r['id'] = 'cell_<"&>\' onload="alert(3)' + 'x' * 120
        with catalogs(data):
            b = plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)
            row = next(csv.DictReader(io.StringIO(plot.temperature_observation_plot_csv(b))))
            self.assertEqual(json.loads(row['record_snapshot_json'])['name'], attack)
            self.assertEqual(row['record_id'], r['id'])
            markup = plot.render_observation_temperature_html(b)
            parsed = ParsedHTML(markup)
            self.assertIn(attack, ''.join(parsed.text))
            self.assertNotIn('<script', markup)
            self.assertIn('&lt;script&gt;', markup)
            self.assertFalse(any(tag in ('script', 'img') for tag, _ in parsed.tags))
            self.assertFalse(any(key.startswith('on') for _, attrs in parsed.tags for key in attrs))
            for width in (320, 1100):
                svg = plot.render_observation_temperature_svg(b, width=width)
                root = ET.fromstring(svg)
                self.assertIn(''.join(attack.split()), ''.join(''.join(root.itertext()).split()))
                centers = by_class(root, 'observation-center')
                self.assertEqual(centers[0].attrib['data-record-id'], r['id'])
                self.assertFalse(any(n.tag.rsplit('}', 1)[-1] in ('script', 'image', 'foreignObject') for n in root.iter()))
                self.assertFalse(any(key.startswith('on') for n in root.iter() for key in n.attrib))

    def test_runtime_needs_only_the_standard_library(self):
        script = (
            'import sys; sys.modules["jsonschema"] = None; sys.modules["referencing"] = None; '
            'from materials_boundaries.observation_temperature_plot import *; '
            f'b = build_observation_temperature_plot(dataset_id={PA12_DATASET!r}); '
            'validate_observation_temperature_plot(b); temperature_observation_plot_json(b); '
            'temperature_observation_plot_csv(b); render_observation_temperature_svg(b); '
            'render_observation_temperature_html(b); print("ok")'
        )
        result = subprocess.run([sys.executable, '-S', '-c', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'ok')

    def test_input_bundle_is_not_mutated_by_any_public_output(self):
        value = deepcopy(self.bundle)
        before = canonical(value)
        for output in self.outputs:
            output(value)
            self.assertEqual(canonical(value), before, output.__name__)

    def test_json_is_sorted_deterministic_round_trippable_and_terminated(self):
        value = plot.temperature_observation_plot_json(self.bundle)
        self.assertTrue(value.endswith('\n'))
        self.assertEqual(json.loads(value), self.bundle)
        self.assertEqual(value, plot.temperature_observation_plot_json(deepcopy(self.bundle)))
        self.assertEqual(value, plot.temperature_observation_plot_json(plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)))
        self.assertEqual(list(json.loads(value)), sorted(self.bundle))
        self.assertIn('32.70', value)
        self.assertIn('26.60', value)
        self.assertNotIn('NaN', value)

    def test_csv_exact_strings_nulls_evidence_and_complete_snapshots_round_trip(self):
        value = plot.temperature_observation_plot_csv(self.bundle)
        self.assertNotIn('\r\n', value)
        self.assertTrue(value.endswith('\n'))
        self.assertEqual(value, plot.temperature_observation_plot_csv(deepcopy(self.bundle)))
        reader = csv.DictReader(io.StringIO(value))
        columns = reader.fieldnames
        self.assertEqual(tuple(columns), plot.CSV_COLUMNS)
        for early in ('classification', 'evaluation_support', 'dataset_id', 'protocol_id',
                      'source_cell_json', 'required_warning_codes_json', 'essential_caveats',
                      'uncertainty_type', 'sample_count_scope', 'replicate_independence'):
            for late in ('temperature_value_string', 'central_value_string', 'sd_value_string',
                         'si_central_value', 'derived_glyph_lower_string'):
                self.assertLess(columns.index(early), columns.index(late))
        rows = list(reader)
        self.assertEqual(len(rows), 6)
        for i, (row, cell, record) in enumerate(zip(rows, self.fixture['cells'], self.bundle['record_snapshots'])):
            self.assertEqual(row['record_id'], record['id'])
            self.assertEqual(row['temperature_value_string'], cell['temperature'])
            self.assertEqual(row['central_value_string'], cell['central'])
            self.assertEqual(row['sd_value_string'], cell['sd'])
            self.assertEqual(row['source_value_string'], cell['central'] + ' ± ' + cell['sd'])
            self.assertEqual(row['derived_glyph_lower_string'], LOWER[i])
            self.assertEqual(row['derived_glyph_upper_string'], UPPER[i])
            self.assertEqual(row['si_central_value'], str(cell['pa']))
            self.assertEqual(row['si_sd_value'], str(cell['sd_pa']))
            self.assertEqual(row['si_unit'], 'Pa')
            self.assertEqual(row['sample_count'], '3')
            self.assertEqual(row['sample_count_scope'], 'tensile_tests_per_temperature_condition')
            self.assertEqual(row['uncertainty_type'], 'reported_standard_deviation')
            self.assertEqual(row['source_artifact'], PA12_ARTIFACT)
            self.assertEqual(row['temperature_basis'], 'reported_chamber_test_condition')
            for key in ('temperature_uncertainty', 'central_statistic_explicitly_named',
                        'aggregation_convention', 'stress_measure', 'stress_area_basis',
                        'replicate_independence', 'scalar_missing_convention'):
                self.assertEqual(row[key], 'null', key)
            for column, key in (('source_cell_json', 'source_cell'), ('conditions_json', 'conditions'),
                                ('method_json', 'method'), ('sample_metadata_json', 'sample_metadata'),
                                ('evidence_json', 'evidence')):
                self.assertEqual(json.loads(row[column]), record[key])
            self.assertEqual(json.loads(row['uncertainty_evidence_json']), record['reported_result']['uncertainty']['evidence'])
            self.assertEqual(json.loads(row['rights_json']), record['verification']['rights'])
            self.assertEqual(json.loads(row['source_inspection_json']), record['verification']['source_inspection'])
            self.assertEqual(json.loads(row['record_snapshot_json']), record)
            self.assertEqual(json.loads(row['source_snapshots_json']), self.bundle['source_snapshots'])
            self.assertEqual(json.loads(row['source_snapshot_digests_json']), self.bundle['source_digests'])
            self.assertEqual(row['record_snapshot_sha256'], digest(record))
            for column, key in (('selection_json', 'selection'), ('group_json', 'group'),
                                ('presentation_policy_json', 'presentation_policy')):
                self.assertEqual(json.loads(row[column]), self.bundle[key])

    def test_six_svg_centers_sd_whiskers_and_caps_follow_fixed_numeric_transform(self):
        for lang in LANGUAGES:
            for width in (320, 380, 1100):
                with self.subTest(lang=lang, width=width):
                    root = ET.fromstring(plot.render_observation_temperature_svg(self.bundle, lang=lang, width=width))
                    chart = next(node for node in root.iter() if node.attrib.get('id') == 'temperature-plot')
                    self.assertEqual(chart.attrib['data-x-domain'], '15,125')
                    self.assertEqual(chart.attrib['data-y-domain'], '0,55')
                    left, right, top, bottom = [float(chart.attrib['data-plot-' + key]) for key in ('left', 'right', 'top', 'bottom')]
                    self.assertGreater(right, left)
                    self.assertAlmostEqual(bottom - top, 340)
                    centers, stems, caps = [by_class(chart, name) for name in ('observation-center', 'sd-whisker', 'sd-cap')]
                    self.assertEqual((len(centers), len(stems), len(caps)), (6, 6, 12))
                    self.assertEqual(len(list(root.iter(SVG + 'circle'))), 6)
                    self.assertFalse(any(node.tag.rsplit('}', 1)[-1] in ('path', 'polyline', 'polygon') for node in chart.iter()))
                    self.assertEqual(len({n.attrib['r'] for n in centers}), 1)
                    self.assertEqual(len({n.attrib.get('fill') for n in centers}), 1)
                    self.assertEqual(len({n.attrib.get('opacity') for n in centers}), 1)
                    xs = []
                    cap_widths = []
                    for i, (cell, center, stem) in enumerate(zip(self.fixture['cells'], centers, stems)):
                        x = left + (float(cell['temperature']) - 15) / 110 * (right - left)
                        y = lambda value: bottom - float(value) / 55 * (bottom - top)
                        self.assertEqual(center.attrib['data-record-id'], self.ids[i])
                        self.assertEqual(center.attrib['data-temperature'], cell['temperature'])
                        self.assertEqual(center.attrib['data-central-value'], cell['central'])
                        self.assertAlmostEqual(float(center.attrib['cx']), x, delta=.01)
                        self.assertAlmostEqual(float(center.attrib['cy']), y(cell['central']), delta=.01)
                        self.assertAlmostEqual(float(stem.attrib['x1']), x, delta=.01)
                        self.assertAlmostEqual(float(stem.attrib['x2']), x, delta=.01)
                        self.assertEqual(stem.attrib['data-record-id'], self.ids[i])
                        self.assertAlmostEqual(min(float(stem.attrib['y1']), float(stem.attrib['y2'])), y(UPPER[i]), delta=.01)
                        self.assertAlmostEqual(max(float(stem.attrib['y1']), float(stem.attrib['y2'])), y(LOWER[i]), delta=.01)
                        own_caps = [n for n in caps if n.attrib['data-record-id'] == self.ids[i]]
                        self.assertEqual(len(own_caps), 2)
                        self.assertEqual(len({n.attrib['y1'] for n in own_caps}), 2)
                        for cap in own_caps:
                            x1, x2, y1, y2 = [float(cap.attrib[k]) for k in ('x1', 'x2', 'y1', 'y2')]
                            self.assertEqual(y1, y2)
                            self.assertAlmostEqual((x1 + x2) / 2, x, delta=.01)
                            self.assertTrue(left <= x1 < x2 <= right)
                            self.assertTrue(top <= y1 <= bottom)
                            cap_widths.append(round(x2 - x1, 2))
                        self.assertTrue(top <= y(UPPER[i]) < y(cell['central']) < y(LOWER[i]) <= bottom)
                        xs.append(float(center.attrib['cx']))
                    self.assertEqual(len(set(cap_widths)), 1)
                    self.assertAlmostEqual((xs[1] - xs[0]) / (xs[2] - xs[1]), 17 / 20, delta=.001)
                    self.assertEqual([''.join(n.itertext()) for n in by_class(chart, 'x-tick')], ['23', '40', '60', '80', '100', '120'])
                    self.assertEqual([''.join(n.itertext()) for n in by_class(chart, 'y-tick')], ['0', '10', '20', '30', '40', '50'])

    def test_all_locales_have_visible_scope_before_plot_exact_table_and_inert_safe_markup(self):
        from materials_boundaries._observation_temperature_labels import labels
        label_sets = [set(labels(lang)) for lang in LANGUAGES]
        self.assertTrue(all(keys == label_sets[0] for keys in label_sets))
        compact = lambda text: ''.join(text.split())
        for lang in LANGUAGES:
            t = labels(lang)
            html = plot.render_observation_temperature_html(self.bundle, lang=lang)
            parsed = ParsedHTML(html)
            ids = [attrs['id'] for _, attrs in parsed.tags if 'id' in attrs]
            self.assertLess(ids.index('essential-scope'), ids.index('glyph-legend'))
            self.assertLess(ids.index('glyph-legend'), ids.index('temperature-plot'))
            self.assertLess(ids.index('temperature-plot'), ids.index('exact-source-table'))
            self.assertTrue(any(tag == 'table' and attrs.get('id') == 'exact-source-table' for tag, attrs in parsed.tags))
            self.assertGreaterEqual(sum(tag == 'th' for tag, _ in parsed.tags), 4)
            self.assertFalse(any(tag in ('script', 'img', 'iframe', 'object', 'embed', 'link') for tag, _ in parsed.tags))
            self.assertFalse(any(key.lower().startswith('on') for _, attrs in parsed.tags for key in attrs))
            self.assertNotIn('@import', html)
            hrefs = [attrs['href'] for tag, attrs in parsed.tags if tag == 'a']
            self.assertTrue(all(href.startswith(('https://', 'http://', '#')) for href in hrefs))
            self.assertIn('https://creativecommons.org/licenses/by/4.0/', hrefs)
            self.assertIn('https://doi.org/10.3390/polym18050563', hrefs)
            visible_variants = [' '.join(parsed.text)]
            for width in (320, 380, 1100):
                markup = plot.render_observation_temperature_svg(self.bundle, lang=lang, width=width)
                root = ET.fromstring(markup)
                nodes = list(root.iter())
                scope = next(n for n in nodes if n.attrib.get('id') == 'essential-scope')
                legend = next(n for n in nodes if n.attrib.get('id') == 'glyph-legend')
                chart = next(n for n in nodes if n.attrib.get('id') == 'temperature-plot')
                table = next(n for n in nodes if n.attrib.get('id') == 'exact-source-table')
                self.assertLess(nodes.index(scope), nodes.index(legend))
                self.assertLess(nodes.index(legend), nodes.index(chart))
                self.assertLess(nodes.index(chart), nodes.index(table))
                for code in plot.WARNING_CODES:
                    self.assertIn(compact(t[code]), compact(''.join(scope.itertext())))
                self.assertIsNotNone(root.find(SVG + 'title'))
                self.assertIsNotNone(root.find(SVG + 'desc'))
                self.assertFalse(any(n.tag.rsplit('}', 1)[-1] in ('script', 'image', 'foreignObject', 'iframe') for n in nodes))
                visible_variants.append(' '.join(''.join(n.itertext()) for n in root.iter(SVG + 'text')))
            for text in visible_variants:
                for code in plot.WARNING_CODES:
                    self.assertIn(compact(t[code]), compact(text))
                for record, cell in zip(self.bundle['record_snapshots'], self.fixture['cells']):
                    self.assertIn(compact(cell['central'] + ' ± ' + cell['sd']), compact(text))
                    self.assertIn(record['id'], text)
                self.assertIn('CC BY 4.0', text)
                self.assertNotIn('[missing:', text)

    def test_compact_svg_preserves_visible_context_without_dumping_raw_metadata(self):
        from materials_boundaries._observation_temperature_labels import labels
        compact = lambda text: ''.join(text.split())
        omitted_raw_fields = (
            'record_digests:', 'source_digests:', 'verification.source_inspection:',
            'conditions.temperature:', 'method.preparation:',
            'material.reinforcement_mass_fraction:',
            'reported_result.central_statistic_explicitly_named:', '"record_snapshots":',
        )
        for lang in LANGUAGES:
            t = labels(lang)
            for width in (320, 380, 1100):
                with self.subTest(lang=lang, width=width):
                    root = ET.fromstring(plot.render_observation_temperature_svg(self.bundle, lang=lang, width=width))
                    # Only SVG text nodes count as visible prose, not titles,
                    # descriptions, attributes or metadata hidden from sight.
                    visible = ' '.join(''.join(n.itertext()) for n in root.iter(SVG + 'text'))
                    ids = {node.attrib.get('id') for node in root.iter()}
                    self.assertTrue({'shared-source-locators', 'protocol-summary', 'source-summary'} <= ids)
                    for key in (*plot.WARNING_CODES, 'glyph_legend', 'protocol_geometry',
                                'protocol_unknowns', 'revision', 'adaptation', 'si_notice'):
                        self.assertIn(compact(t[key]), compact(visible), key)
                    for key in omitted_raw_fields:
                        self.assertNotIn(key, visible)
                    for record in self.bundle['record_snapshots']:
                        # Existing exact Pa metadata still belongs in JSON/CSV,
                        # rather than six extra numerical listings in the SVG.
                        self.assertNotIn(str(record['si_result']['value']), visible)
                    rows = by_class(root, 'source-row')
                    self.assertEqual(len(rows), 6)
                    for row, glyph in zip(rows, self.bundle['glyphs']):
                        row_text = ' '.join(''.join(n.itertext()) for n in row.iter(SVG + 'text'))
                        self.assertEqual(row.attrib['data-record-id'], glyph['record_id'])
                        self.assertIn(compact(glyph['source_value_string']), compact(row_text))
                        self.assertIn(glyph['record_id'], compact(row_text))
                        self.assertIn(glyph['temperature_value_string'], row_text)
                        self.assertIn(glyph['sd_value_string'], row_text)
                        self.assertIn('3', [''.join(n.itertext()) for n in row.iter(SVG + 'text')])
                        self.assertIn(compact(t['table_column'] + ': ' + glyph['source_cell']['temperature_column']), compact(row_text))
                    cell = self.bundle['glyphs'][0]['source_cell']
                    for key in ('row', 'table_container_id', 'expanded_table_id'):
                        self.assertIn(compact(cell[key]), compact(visible), key)
                    for value in ('150 mm', '80 mm', '3 mm', '10/20 mm', '110 mm',
                                  'ISO 527', 'CC BY 4.0', '2026', '1 MPa = 1000000 Pa'):
                        self.assertIn(compact(value), compact(visible), value)
                    # A generous ceiling detects accidental full metadata dumps
                    # while leaving room for readable multilingual wrapping.
                    if width == 1100:
                        self.assertLessEqual(float(root.attrib['height']), 3000)
                    sizes = [float(node.attrib['font-size']) for node in root.iter(SVG + 'text')]
                    self.assertTrue(all(size >= 11 for size in sizes))

    def test_html_collapses_raw_audit_metadata_without_hiding_essential_context(self):
        from materials_boundaries._observation_temperature_labels import labels
        compact = lambda text: ''.join(text.split())
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                parsed = ParsedHTML(plot.render_observation_temperature_html(self.bundle, lang=lang))
                visible = ' '.join(parsed.visible)
                audit_details = [attrs for tag, attrs in parsed.tags if tag == 'details' and attrs.get('id') == 'audit-details']
                self.assertEqual(len(audit_details), 1)
                self.assertNotIn('open', audit_details[0])
                self.assertIn('temperature-plot-json', parsed.pre_in_details)
                audit = ''.join(parsed.pre_contents['temperature-plot-json'])
                self.assertEqual(json.loads(audit), self.bundle)
                for prefix in ('record_digests:', 'source_digests:', 'verification.source_inspection:',
                               'conditions.temperature:', 'method.preparation:',
                               'material.reinforcement_mass_fraction:'):
                    self.assertNotIn(prefix, visible)
                t = labels(lang)
                for key in (*plot.WARNING_CODES, 'glyph_legend', 'protocol_geometry',
                            'protocol_unknowns', 'revision', 'adaptation'):
                    self.assertIn(compact(t[key]), compact(visible), key)
                for glyph in self.bundle['glyphs']:
                    self.assertIn(glyph['source_value_string'], visible)
                    self.assertIn(glyph['record_id'], visible)
                self.assertFalse(any(tag in ('script', 'iframe', 'object', 'embed') for tag, _ in parsed.tags))

    def test_export_is_deterministic_across_all_locales_and_preserves_inspection_files(self):
        variants = []
        with tempfile.TemporaryDirectory() as tmp:
            for lang in LANGUAGES:
                target = Path(tmp) / lang
                target.mkdir()
                old = target / 'observation-inspection.json'; old.write_text('inspection sentinel')
                plot.export_observation_temperature_plot(target, dataset_id=PA12_DATASET, lang=lang)
                expected = {PREFIX + suffix for suffix in ('.json', '.csv', '.' + lang + '.svg', '.narrow.' + lang + '.svg', '.' + lang + '.html')}
                self.assertEqual({p.name for p in target.iterdir()}, expected | {old.name})
                self.assertEqual(old.read_text(), 'inspection sentinel')
                before = {p.name: p.read_bytes() for p in target.iterdir()}
                plot.export_observation_temperature_plot(target, dataset_id=PA12_DATASET, lang=lang)
                self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
                variants.append((before[PREFIX + '.json'], before[PREFIX + '.csv']))
            self.assertTrue(all(value == variants[0] for value in variants))

    def test_bad_options_and_changed_science_preserve_absent_and_existing_targets(self):
        invalid = ({'dataset_id': 'all'}, {'dataset_id': None},
                   {'dataset_id': PA12_DATASET, 'lang': 'xx'},
                   {'dataset_id': PA12_DATASET, 'lang': None},
                   {'dataset_id': PA12_DATASET, 'lang': True})
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'output'
            for kwargs in invalid:
                with self.subTest(kwargs=kwargs), self.assertRaises(plot.ObservationTemperaturePlotError):
                    plot.export_observation_temperature_plot(target, **kwargs)
                self.assertFalse(target.exists())
            target.mkdir()
            for filename in (PREFIX + '.json', PREFIX + '.csv', PREFIX + '.en.svg', PREFIX + '.en.html'):
                (target / filename).write_text('sentinel ' + filename)
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            for kwargs in invalid:
                with self.assertRaises(plot.ObservationTemperaturePlotError):
                    plot.export_observation_temperature_plot(target, **kwargs)
                self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
            data = deepcopy(self.observations)
            next(r for r in data['records'] if r['id'] == self.ids[0])['sample_metadata']['count'] = 4
            with catalogs(data), self.assertRaises(plot.ObservationTemperaturePlotError):
                plot.export_observation_temperature_plot(target, dataset_id=PA12_DATASET)
            self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)

    def test_render_language_and_width_are_strict(self):
        for lang in ('xx', '', None, True, 1, [], {}):
            for render in (plot.render_observation_temperature_svg, plot.render_observation_temperature_html):
                with self.subTest(lang=lang, render=render.__name__), self.assertRaises(plot.ObservationTemperaturePlotError):
                    render(self.bundle, lang=lang)
        for width in (True, False, 319, 1601, 1100.0, '1100', None, [], float('nan'), float('inf')):
            with self.subTest(width=repr(width)), self.assertRaises(plot.ObservationTemperaturePlotError):
                plot.render_observation_temperature_svg(self.bundle, width=width)
        for width in (320, 380, 1100, 1600):
            root = ET.fromstring(plot.render_observation_temperature_svg(self.bundle, width=width))
            self.assertEqual(float(root.attrib['width']), width)

    def test_inspection_policy_stays_nonquantitative_for_old_new_mixed_and_single(self):
        old_ids = [r['id'] for r in self.observations['records'] if r.get('dataset_id') != PA12_DATASET]
        for selected in (old_ids, self.ids, [old_ids[0], self.ids[0]], [self.ids[2]]):
            b = inspection.build_observation_inspection(selected)
            policy = b['presentation_policy']
            self.assertEqual(b['schema_version'], '1.1.0')
            self.assertEqual(policy['purpose'], 'inspection_only')
            self.assertIs(policy['quantitative_axes_allowed'], False)
            self.assertIs(policy['uncertainty_endpoints_calculated'], False)
            for facet in b['facets']:
                for key in ('lower', 'upper', 'derived_lower_string', 'derived_upper_string', 'mean', 'x', 'y'):
                    self.assertNotIn(key, facet)
            root = ET.fromstring(inspection.render_observation_svg(b))
            self.assertFalse(any(node.tag.rsplit('}', 1)[-1] in ('line', 'circle', 'path', 'polyline', 'polygon') for node in root.iter()))

    def test_cli_requires_dataset_and_output_and_uses_final_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'missing'
            for args in (
                ['observation', 'plot-temperature', '--output', str(target)],
                ['observation', 'plot-temperature', '--dataset-id', PA12_DATASET],
            ):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                    main(args)
                self.assertEqual(caught.exception.code, 2)
                self.assertFalse(target.exists())
            target = Path(tmp) / 'final-lang'
            args = ['--lang', 'zh', 'observation', '--lang', 'ja', 'plot-temperature',
                    '--lang', 'en', '--dataset-id', PA12_DATASET, '--output', str(target), '--lang', 'de']
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                result = main(args)
            self.assertIn(result, (None, 0))
            self.assertTrue((target / (PREFIX + '.de.svg')).is_file())
            self.assertFalse((target / (PREFIX + '.en.svg')).exists())

    def test_optional_json_schema_accepts_only_closed_plot_bundle(self):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
            from referencing import Registry, Resource
        except ImportError:
            self.skipTest('jsonschema is optional development QA; runtime remains dependency-free')
        schemas = [json.loads((ROOT / 'schemas' / name).read_text()) for name in
                   ('observation-temperature-plot.schema.json', 'observations.schema.json', 'sources.schema.json')]
        registry = Registry().with_resources((schema['$id'], Resource.from_contents(schema)) for schema in schemas)
        Draft202012Validator.check_schema(schemas[0])
        validator = Draft202012Validator(schemas[0], registry=registry, format_checker=FormatChecker())
        validator.validate(self.bundle)
        for path, value in (
            (('kind',), 'observation_inspection'), (('glyphs',), self.bundle['glyphs'][:1]),
            (('glyphs', 0, 'sample_count'), True), (('glyphs', 0, 'temperature_uncertainty'), 0),
            (('glyphs', 0, 'uncertainty_type'), 'confidence_interval'),
            (('glyphs', 0, 'source_cell', 'row'), 'Elastic modulus'), (('extra',), True),
        ):
            changed = deepcopy(self.bundle); replace(changed, path, value)
            with self.subTest(path=path):
                self.assertFalse(validator.is_valid(changed))


if __name__ == '__main__':
    unittest.main()
