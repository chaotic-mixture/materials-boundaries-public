"""Closed-pair descriptive presentation QA, not scientific/translation review.

Independent pre-existing source transcriptions pin the ten cells. The new
fixture pins the separate presentation contract without changing any historical
fixture, source payload, test helper, inspection route or single-study plot.
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

from materials_boundaries import observation_study_comparison as view
from materials_boundaries.catalog import read_catalog
from materials_boundaries.cli import main
from materials_boundaries.validation import ValidationError

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('en', 'zh', 'ja', 'de')
SVG = '{http://www.w3.org/2000/svg}'
PREFIX = 'observation-study-comparison'
PROFILE = 'ciganas-zach-uts-temperature-v1'


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
        return 'invented known condition'
    if type(value) is bool:
        return not value
    if type(value) in (int, float):
        return value + 1
    return value + ' unreviewed'


def compact(text):
    return ''.join(text.split())


@contextmanager
def catalogs(observations=None, sources=None):
    values = {
        'observations': deepcopy(read_catalog('observations') if observations is None else observations),
        'sources': deepcopy(read_catalog('sources') if sources is None else sources),
    }
    def reader(name):
        if name not in values:
            raise AssertionError('Unexpected catalog: ' + name)
        return deepcopy(values[name])
    with patch.object(view, 'read_catalog', side_effect=reader):
        yield


class ParsedHTML(HTMLParser):
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.tags, self.visible, self.text = [], [], []
        self.pre_contents, self._pre_id = {}, None
        self._details_depth = self._nonvisible_depth = 0
        self.feed(value)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        self._details_depth += tag == 'details'
        self._nonvisible_depth += tag in ('style', 'script')
        if tag == 'pre' and dict(attrs).get('id'):
            self._pre_id = dict(attrs)['id']
            self.pre_contents[self._pre_id] = []

    def handle_endtag(self, tag):
        self._details_depth -= tag == 'details'
        self._nonvisible_depth -= tag in ('style', 'script')
        if tag == 'pre': self._pre_id = None

    def handle_data(self, value):
        self.text.append(value)
        if self._pre_id is not None: self.pre_contents[self._pre_id].append(value)
        if not self._details_depth and not self._nonvisible_depth:
            self.visible.append(value)


def by_class(root, name):
    return [node for node in root.iter() if name in node.attrib.get('class', '').split()]


class ObservationStudyComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observations = read_catalog('observations')
        cls.sources = read_catalog('sources')
        cls.fixture = json.loads((ROOT/'tests/fixtures/study_comparison_profile_v0250.json').read_text())
        cls.source_fixtures = [json.loads((ROOT/'tests/fixtures'/p['fixture']).read_text())
                               for p in cls.fixture['panels']]
        cls.bundle = view.build_observation_study_comparison(profile_id=PROFILE)
        cls.ids = cls.bundle['selection']['resolved_record_ids']
        cls.outputs = (view.validate_observation_study_comparison,
                       view.observation_study_comparison_json,
                       view.observation_study_comparison_csv,
                       view.render_observation_study_comparison_svg,
                       view.render_observation_study_comparison_html)

    def assert_rejected_by_outputs(self, value):
        for output in self.outputs:
            with self.subTest(output=output.__name__), self.assertRaises(view.ObservationStudyComparisonError):
                output(value)

    def test_exact_closed_pair_profile_order_versions_and_digests(self):
        from materials_boundaries import __version__
        b, f = self.bundle, self.fixture
        self.assertTrue(issubclass(view.ObservationStudyComparisonError, ValidationError))
        self.assertEqual(b['kind'], 'observation_study_comparison')
        self.assertEqual(b['schema_version'], f['schema_version'])
        self.assertEqual(b['engine_version'], __version__)
        self.assertEqual(b['catalog_schema_versions'], {'observations': '1.3.0', 'sources': '1.0.0'})
        self.assertEqual(b['selection']['profile_id'], f['profile_id'])
        self.assertEqual(b['selection']['profile_version'], f['profile_version'])
        self.assertEqual(b['comparison_scope'], f['comparison_scope'])
        self.assertIs(b['matched_conditions_established'], False)
        self.assertIs(b['unknown_conditions_equivalent'], False)
        self.assertEqual(len(b['panels']), 2)
        self.assertEqual(len(b['record_snapshots']), 10)
        self.assertEqual(len(b['source_snapshots']), 2)
        self.assertEqual(self.ids, [r['id'] for r in b['record_snapshots']])
        self.assertEqual(b['selection']['resolved_source_cells'], [r['source_cell'] for r in b['record_snapshots']])
        self.assertEqual([s['id'] for s in b['source_snapshots']], [p['study_id'] for p in f['panels']])
        self.assertEqual(b['policy_digest_sha256'], digest(b['presentation_policy']))
        for r, d in zip(b['record_snapshots'], b['record_digests']):
            self.assertEqual(d, {'record_id': r['id'], 'record_version': r['version'], 'sha256': digest(r)})
        for s, d in zip(b['source_snapshots'], b['source_digests']):
            self.assertEqual(d, {'source_id': s['id'], 'sha256': digest(s)})
        self.assertNotIn('glyphs', b)
        for panel, expected in zip(b['panels'], f['panels']):
            for key in ('panel_id', 'study_id', 'dataset_id', 'protocol_id', 'method_family'):
                self.assertEqual(panel[key], expected[key])
            self.assertEqual(panel['quantity'], 'ultimate_tensile_strength_as_reported_3d')
            self.assertEqual(panel['warning_codes'], list(view.WARNING_CODES))
            self.assertEqual([fact['fact_id'] for fact in panel['protocol_facts']], f['protocol_fact_ids'])

    def test_independent_exact_ten_cells_statistic_sd_provenance_and_scoped_counts(self):
        original = {r['id']: r for r in self.observations['records']}
        by_id = {r['id']: r for r in self.bundle['record_snapshots']}
        for panel, expected, source in zip(self.bundle['panels'], self.fixture['panels'], self.source_fixtures):
            self.assertEqual(len(panel['points']), len(source['cells']))
            for p, cell in zip(panel['points'], source['cells']):
                r = by_id[p['record_id']]
                self.assertEqual(r, original[r['id']])
                for path, value in source.get('facts_by_record_path', {}).items():
                    self.assertEqual(lookup(r, path.split('/')), value, path)
                self.assertEqual(p['source_cell'], r['source_cell'])
                self.assertEqual(p['source_cell']['temperature_column'], cell['temperature'])
                self.assertEqual(p['temperature'], r['conditions']['temperature'])
                self.assertEqual(p['temperature']['value_string'], cell['temperature'])
                self.assertEqual(p['temperature']['unit'], 'degC')
                self.assertEqual(p['temperature']['basis'], 'reported_chamber_test_condition')
                self.assertEqual(p['central_value_string'], cell[expected['central_field']])
                self.assertEqual(p['central_unit'], 'MPa')
                self.assertEqual(p['summary_statistic'], expected['summary_statistic'])
                self.assertEqual(p['central_statistic_explicitly_named'], expected['central_statistic_explicitly_named'])
                self.assertEqual(p['reported_sd'], r['reported_result']['uncertainty'])
                self.assertEqual(p['reported_sd']['value_string'], cell['sd'])
                self.assertEqual(p['reported_sd']['notation'], expected['sd_notation'])
                self.assertEqual(p['reported_sd']['type'], 'reported_standard_deviation')
                self.assertEqual(p['reported_sd']['unit'], 'MPa')
                self.assertEqual(p['sd_unit_presentation']['kind'], 'curated_presentation_interpretation')
                self.assertEqual(p['sd_unit_presentation']['evidence'], p['reported_sd']['evidence'])
                self.assertEqual(p['sample_metadata']['count'], expected['sample_count'])
                self.assertEqual(p['sample_metadata']['scope'], expected['sample_scope'])
                self.assertIsNone(p['sample_metadata']['replicate_independence'])
                self.assertEqual(p['si_result'], r['si_result'])
                self.assertEqual(p['si_result']['value'], cell['pa'])
                self.assertEqual(p['si_result']['uncertainty_value'], cell[expected['si_sd_field']])
                for key in ('derived_lower_string', 'derived_upper_string', 'mean', 'sem', 'ci', 'rank', 'ratio', 'delta', 'x', 'y'):
                    self.assertNotIn(key, p)
                if panel['panel_id'] == 'ciganas':
                    self.assertEqual(p['source_value_string'], cell['central'] + ' ± ' + cell['sd'])
                    self.assertNotIn('header_unit_explicit', p['reported_sd'])
                    self.assertNotIn('unit_basis', p['reported_sd'])
                    self.assertIn('Table_3', p['sd_unit_presentation']['basis'])
                else:
                    self.assertEqual(p['source_value_string'], cell['median'])
                    self.assertNotIn('±', p['source_value_string'])
                    self.assertIs(p['reported_sd']['header_unit_explicit'], False)
                    self.assertIsNone(p['reported_sd']['source_unit_string'])
                    self.assertEqual(p['reported_sd']['unit_basis'], 'contextual_inference_from_associated_uts_column')
                    self.assertEqual(p['si_result']['uncertainty_unit_basis'], 'conditional_on_contextual_MPa_inference')
                    self.assertIn('No new plot', canonical(r))
            record = by_id[panel['points'][0]['record_id']]
            for fact in panel['protocol_facts']:
                self.assertEqual(fact['evidence_values'], [lookup(record, path.split('.')) for path in fact['evidence_paths']])

    def test_fixed_display_padding_and_no_endpoints_pooling_prediction_or_ranking(self):
        p, f = self.bundle['presentation_policy'], self.fixture
        self.assertEqual(p['axes']['x']['domain'], f['x_domain'])
        self.assertEqual(p['axes']['y']['domain'], f['y_domain'])
        self.assertEqual(p['axes']['x']['ticks'], f['x_ticks'])
        self.assertEqual(p['axes']['y']['ticks'], f['y_ticks'])
        self.assertEqual((p['axes']['x']['unit'], p['axes']['y']['unit']), ('degC', 'MPa'))
        self.assertEqual(p['axes']['x']['scale'], 'linear')
        self.assertEqual(p['axes']['y']['scale'], 'linear')
        self.assertEqual(p['evaluation_support'], 'catalog_only')
        for key in ('matched_conditions_established', 'unknown_conditions_equivalent',
                    'statistical_independence_established', 'sd_is_uncertainty_of_central_statistic',
                    'uncertainty_endpoints_calculated', 'temperature_whiskers_allowed', 'overlay_allowed',
                    'additional_groups_allowed', 'fit_allowed', 'connecting_lines_allowed',
                    'interpolation_allowed', 'extrapolation_allowed', 'pooling_allowed',
                    'normalization_allowed', 'retention_ratios_allowed', 'deltas_allowed',
                    'ranking_allowed', 'significance_test_allowed', 'material_prediction_allowed',
                    'design_allowable_allowed', 'geometry_or_thickness_conversion_allowed', 'formula_execution_allowed'):
            self.assertIs(p[key], False, key)
        self.assertIs(p['axis_domains_are_display_padding_not_validated_ranges_or_material_limits'], True)
        self.assertIs(p['axis_ticks_are_reference_coordinates_not_observations'], True)
        self.assertEqual(p['sd_display'], 'always_visible_separate_source_exact_column')
        self.assertEqual(p['profile_scope'], 'separately_curated_presentation_preserves_historical_source_snapshots')

    def test_explicit_profile_only_without_subsets_cross_products_or_custom_axes(self):
        with self.assertRaises(TypeError):
            view.build_observation_study_comparison()
        for profile in ('', 'all', 'ciganas', PROFILE + ' ', PROFILE.upper(), None, True, 1, [], {}, [PROFILE]):
            with self.subTest(profile=profile), self.assertRaises(view.ObservationStudyComparisonError):
                view.build_observation_study_comparison(profile_id=profile)
        for kwargs in ({'record_ids': self.ids[:1]}, {'source_id': self.fixture['panels'][0]['study_id']},
                       {'dataset_id': self.fixture['panels'][0]['dataset_id']}, {'x_domain': [0, 200]}, {'hide_sd': True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(TypeError):
                view.build_observation_study_comparison(profile_id=PROFILE, **kwargs)

    def test_catalog_reorder_and_all_display_id_name_changes_preserve_source_order(self):
        observations, sources = deepcopy(self.observations), deepcopy(self.sources)
        observations['records'].reverse(); sources['records'].reverse()
        before = canonical([observations, sources])
        with catalogs(observations, sources):
            self.assertEqual(view.build_observation_study_comparison(profile_id=PROFILE), self.bundle)
        self.assertEqual(canonical([observations, sources]), before)
        names = {}
        for r in observations['records']:
            if r.get('dataset_id') in {p['dataset_id'] for p in self.fixture['panels']}:
                new_id = 'renamed_' + r['source_cell']['temperature_column'] + '_' + r['study_id']
                names[r['id']] = new_id
                r['id'], r['name'] = new_id, '=literal, "renamed" <UTS & source> ' + 'x' * 120
        with catalogs(observations, sources):
            b = view.build_observation_study_comparison(profile_id=PROFILE)
            self.assertEqual(b['selection']['resolved_record_ids'], [names[rid] for rid in self.ids])
            self.assertEqual(b['selection']['resolved_source_cells'], self.bundle['selection']['resolved_source_cells'])
            for output in self.outputs:
                output(b)
            self.assert_rejected_by_outputs(self.bundle)
            rows = list(csv.DictReader(io.StringIO(view.observation_study_comparison_csv(b))))
            for row, record in zip(rows, b['record_snapshots']):
                self.assertEqual(json.loads(row['record_snapshot_json']), record)

    def test_unrelated_supported_family_appends_do_not_affect_closed_membership(self):
        # Positive source/family selection avoids treating every future record as
        # legacy, and imposes no fixed total catalog/source count.
        markers = (('lee_wei_kysar_hone_2008', None),
                   ('bertolazzi_brivio_kis_2011', 'bertolazzi_2011_mos2_monolayer_indentation_v1'),
                   ('falin_et_al_2017_hbn_mechanical_properties', 'falin_2017_hbn_monolayer_indentation_v1'))
        fresh = []
        for study, family in markers:
            original = next(r for r in self.observations['records'] if r['study_id'] == study and r.get('method_family') == family)
            clone = deepcopy(original); clone['id'] += '_comparison_appendability'; clone['name'] += ' appendability fixture'
            fresh.append(clone)
        changed = deepcopy(self.observations)
        changed['records'] = fresh + list(reversed(changed['records']))
        with catalogs(changed):
            b = view.build_observation_study_comparison(profile_id=PROFILE)
            self.assertEqual(b, self.bundle)
            self.assertEqual(view.observation_study_comparison_json(b), view.observation_study_comparison_json(self.bundle))
            self.assertTrue(set(r['id'] for r in fresh).isdisjoint(b['selection']['resolved_record_ids']))

    def test_missing_extra_duplicate_alias_and_laundered_group_cells_fail_closed(self):
        for panel in self.bundle['panels']:
            rid = panel['points'][0]['record_id']
            cases = []
            changed = deepcopy(self.observations)
            changed['records'] = [r for r in changed['records'] if r['id'] != rid]
            cases.append(('missing', changed))
            for mode in ('duplicate_id', 'alias', 'extra_temperature', 'other_family', 'other_quantity'):
                changed = deepcopy(self.observations)
                r = deepcopy(next(r for r in changed['records'] if r['id'] == rid))
                if mode != 'duplicate_id': r['id'] = mode + '_extra'
                if mode == 'extra_temperature': r['source_cell']['temperature_column'] = '200'
                if mode == 'other_family': r['method_family'] = 'unreviewed_family'
                if mode == 'other_quantity': r['quantity'] = 'youngs_modulus_3d'
                changed['records'].append(r); cases.append((mode, changed))
            for key in ('method_family', 'study_id', 'dataset_id', 'protocol_id', 'source_cell'):
                for mode in ('remove', 'alter'):
                    changed = deepcopy(self.observations)
                    r = next(r for r in changed['records'] if r['id'] == rid)
                    if mode == 'remove': del r[key]
                    else: r[key] = 'unreviewed'
                    cases.append((mode + '_' + key, changed))
            for mode, changed in cases:
                with self.subTest(panel=panel['panel_id'], mode=mode), catalogs(changed), self.assertRaises(view.ObservationStudyComparisonError):
                    view.build_observation_study_comparison(profile_id=PROFILE)

    def test_every_selected_scientific_record_and_source_leaf_is_admission_closed(self):
        for panel in self.bundle['panels']:
            rid = panel['points'][0]['record_id']
            record = next(r for r in self.observations['records'] if r['id'] == rid)
            for path, value in leaves(record):
                if path[0] in ('id', 'name'): continue
                changed = deepcopy(self.observations)
                target = next(r for r in changed['records'] if r['id'] == rid)
                replace(target, path, altered(value))
                with self.subTest(record=rid, path=path), catalogs(changed), self.assertRaises(view.ObservationStudyComparisonError):
                    view.build_observation_study_comparison(profile_id=PROFILE)
            for key in record:
                changed = deepcopy(self.observations)
                next(r for r in changed['records'] if r['id'] == rid).pop(key)
                with self.subTest(record=rid, missing=key), catalogs(changed), self.assertRaises(view.ObservationStudyComparisonError):
                    view.build_observation_study_comparison(profile_id=PROFILE)
            changed = deepcopy(self.observations)
            next(r for r in changed['records'] if r['id'] == rid)['unreviewed_model'] = True
            with catalogs(changed), self.assertRaises(view.ObservationStudyComparisonError):
                view.build_observation_study_comparison(profile_id=PROFILE)
        for source in self.bundle['source_snapshots']:
            for path, value in leaves(source):
                changed = deepcopy(self.sources)
                target = next(s for s in changed['records'] if s['id'] == source['id'])
                replace(target, path, altered(value))
                with self.subTest(source=source['id'], path=path), catalogs(sources=changed), self.assertRaises(view.ObservationStudyComparisonError):
                    view.build_observation_study_comparison(profile_id=PROFILE)
            for mode in ('missing', 'duplicate', 'alias', 'extra_key'):
                changed = deepcopy(self.sources)
                if mode == 'missing': changed['records'] = [s for s in changed['records'] if s['id'] != source['id']]
                elif mode == 'extra_key': next(s for s in changed['records'] if s['id'] == source['id'])['extra'] = True
                else:
                    duplicate = deepcopy(source)
                    if mode == 'alias': duplicate['id'] += '_alias'
                    changed['records'].append(duplicate)
                with self.subTest(source=source['id'], mode=mode), catalogs(sources=changed), self.assertRaises(view.ObservationStudyComparisonError):
                    view.build_observation_study_comparison(profile_id=PROFILE)

    def test_every_policy_point_protocol_and_identity_leaf_rejects_even_rehashed_forgeries(self):
        # Recomputing a checksum cannot authorize new science or display policy.
        for section in ('presentation_policy', 'selection'):
            for path, value in leaves(self.bundle[section]):
                b = deepcopy(self.bundle); replace(b[section], path, altered(value))
                if section == 'presentation_policy': b['policy_digest_sha256'] = digest(b[section])
                with self.subTest(section=section, path=path), self.assertRaises(view.ObservationStudyComparisonError):
                    view.validate_observation_study_comparison(b)
        for index, panel in enumerate(self.bundle['panels']):
            for path, value in leaves(panel):
                b = deepcopy(self.bundle); replace(b['panels'][index], path, altered(value))
                with self.subTest(panel=index, path=path), self.assertRaises(view.ObservationStudyComparisonError):
                    view.validate_observation_study_comparison(b)
        for section, digest_key in (('record_snapshots', 'record_digests'), ('source_snapshots', 'source_digests')):
            for index in (0, len(self.bundle[section]) - 1):
                b = deepcopy(self.bundle)
                key = 'name' if section == 'record_snapshots' else 'title'
                b[section][index][key] += ' forged'
                b[digest_key][index]['sha256'] = digest(b[section][index])
                with self.subTest(section=section, index=index): self.assert_rejected_by_outputs(b)

    def test_extra_stale_and_reordered_bundle_data_fail_every_output(self):
        for key in self.bundle:
            changed = deepcopy(self.bundle); del changed[key]
            with self.subTest(missing=key): self.assert_rejected_by_outputs(changed)
        changes = [(('schema_version',), '0.0.0'), (('engine_version',), '0.0.0'),
                   (('kind',), 'observation_inspection'), (('extra',), True),
                   (('panels',), list(reversed(self.bundle['panels']))),
                   (('source_snapshots',), list(reversed(self.bundle['source_snapshots']))),
                   (('record_snapshots',), self.bundle['record_snapshots'][:-1]),
                   (('selection', 'extra'), 'unreviewed'),
                   (('panels', 0, 'points', 0, 'derived_lower_string'), '48.19'),
                   (('panels', 1, 'points', 0, 'source_value_string'), '58.91 ± 3.44'),
                   (('panels', 0, 'points', 0, 'summary_statistic'), 'mean'),
                   (('panels', 1, 'plot_policy', 'uncertainty_endpoints_calculated'), True),
                   (('panels', 0, 'protocol_facts', 0, 'extra'), True),
                   (('record_digests', 0, 'sha256'), '0' * 64),
                   (('source_digests', 0, 'sha256'), '0' * 64)]
        for path, value in changes:
            b = deepcopy(self.bundle); replace(b, path, value)
            with self.subTest(path=path): self.assert_rejected_by_outputs(b)
        for panel in self.bundle['panels']:
            observations, sources = deepcopy(self.observations), deepcopy(self.sources)
            next(r for r in observations['records'] if r['id'] == panel['points'][0]['record_id'])['reported_result']['value'] += 1
            next(s for s in sources['records'] if s['id'] == panel['study_id'])['doi'] = '10.0000/unreviewed'
            for kwargs in ({'observations': observations}, {'sources': sources}):
                with self.subTest(panel=panel['panel_id'], catalogs=tuple(kwargs)), catalogs(**kwargs):
                    self.assert_rejected_by_outputs(self.bundle)

    def test_malformed_nonjson_nonfinite_boolean_and_xml_values_reject_every_output(self):
        for value in (None, [], '', True, 0, {'selection': []}):
            self.assert_rejected_by_outputs(value)
        for value in (float('nan'), float('inf'), -float('inf'), True, object(), {'set'}, b'23'):
            b = deepcopy(self.bundle); b['panels'][0]['points'][0]['sample_metadata']['count'] = value
            with self.subTest(value=repr(value)): self.assert_rejected_by_outputs(b)
        for value in ('\x00', '\x01', '\ud800', '\uffff'):
            b = deepcopy(self.bundle); b['record_snapshots'][0]['name'] += value
            with self.subTest(xml=repr(value)): self.assert_rejected_by_outputs(b)
        b = deepcopy(self.bundle); b[1] = 'non-string key'
        self.assert_rejected_by_outputs(b)

    def test_catalog_schema_xml_booleans_nonfinite_and_unsafe_links_are_rejected(self):
        for kind in ('observations', 'sources'):
            for version in ('', '0.0.0', None, True, 1, [], {}):
                changed = deepcopy(getattr(self, kind)); changed['schema_version'] = version
                with self.subTest(kind=kind, version=version), catalogs(**{kind: changed}), self.assertRaises(view.ObservationStudyComparisonError):
                    view.build_observation_study_comparison(profile_id=PROFILE)
        for panel in self.bundle['panels']:
            rid = panel['points'][0]['record_id']
            for field in ('id', 'name'):
                for value in ('\x00', '\x01', '\ud800', '\uffff'):
                    changed = deepcopy(self.observations)
                    next(r for r in changed['records'] if r['id'] == rid)[field] += value
                    with self.subTest(field=field, value=repr(value)), catalogs(changed), self.assertRaises(view.ObservationStudyComparisonError):
                        view.build_observation_study_comparison(profile_id=PROFILE)
            for path in (('sample_metadata', 'count'), ('conditions', 'temperature', 'value'), ('reported_result', 'value'), ('si_result', 'value')):
                for value in (True, float('nan'), float('inf')):
                    changed = deepcopy(self.observations)
                    replace(next(r for r in changed['records'] if r['id'] == rid), path, value)
                    with self.subTest(path=path, value=repr(value)), catalogs(changed), self.assertRaises(view.ObservationStudyComparisonError):
                        view.build_observation_study_comparison(profile_id=PROFILE)
            for url in ('javascript:alert(1)', 'data:text/html,bad', 'file:///tmp/bad', 'https://user:pass@example.test/', 'https://example.test/ bad', 'https://example.test:bad/'):
                changed = deepcopy(self.sources)
                next(s for s in changed['records'] if s['id'] == panel['study_id'])['urls'] = [url]
                with self.subTest(url=url), catalogs(sources=changed), self.assertRaises(view.ObservationStudyComparisonError):
                    view.build_observation_study_comparison(profile_id=PROFILE)
                changed = deepcopy(self.observations)
                next(r for r in changed['records'] if r['id'] == rid)['evidence'][0]['source_url'] = url
                with catalogs(changed), self.assertRaises(view.ObservationStudyComparisonError):
                    view.build_observation_study_comparison(profile_id=PROFILE)

    def test_no_public_output_mutates_input_and_decimal_context_is_irrelevant(self):
        b = deepcopy(self.bundle); before = canonical(b)
        for output in self.outputs:
            output(b)
            self.assertEqual(canonical(b), before, output.__name__)
        with localcontext() as ctx:
            ctx.prec = 1; ctx.Emax = 1; ctx.Emin = -1
            ctx.traps[Inexact] = True; ctx.traps[Rounded] = True
            actual = view.build_observation_study_comparison(profile_id=PROFILE)
            self.assertEqual(actual, self.bundle)
            for output in self.outputs: output(actual)

    def test_json_csv_deterministic_source_exact_long_form_and_snapshot_round_trips(self):
        encoded = view.observation_study_comparison_json(self.bundle)
        self.assertTrue(encoded.endswith('\n'))
        self.assertEqual(json.loads(encoded), self.bundle)
        self.assertEqual(list(json.loads(encoded)), sorted(self.bundle))
        self.assertEqual(encoded, view.observation_study_comparison_json(deepcopy(self.bundle)))
        text = view.observation_study_comparison_csv(self.bundle)
        self.assertEqual(text, view.observation_study_comparison_csv(deepcopy(self.bundle)))
        self.assertNotIn('\r\n', text)
        reader = csv.DictReader(io.StringIO(text)); columns, rows = reader.fieldnames, list(reader)
        self.assertEqual(tuple(columns), view.CSV_COLUMNS)
        self.assertEqual(len(rows), 10)
        for early in ('study_id', 'dataset_id', 'protocol_id', 'method_family', 'source_cell_json',
                      'required_warning_codes_json', 'essential_caveats', 'protocol_facts_json',
                      'summary_statistic', 'sd_notation', 'sd_unit_presentation_json', 'sample_count_scope', 'replicate_independence'):
            for late in ('temperature_value_string', 'central_value_string', 'sd_value_string'):
                self.assertLess(columns.index(early), columns.index(late))
        points = [point for panel in self.bundle['panels'] for point in panel['points']]
        for row, p, r in zip(rows, points, self.bundle['record_snapshots']):
            self.assertEqual(row['record_id'], r['id'])
            self.assertEqual(row['central_value_string'], p['central_value_string'])
            self.assertEqual(row['sd_value_string'], p['reported_sd']['value_string'])
            self.assertEqual(row['source_value_string'], p['source_value_string'])
            self.assertEqual(row['temperature_value_string'], p['temperature']['value_string'])
            self.assertEqual(row['sample_count'], str(p['sample_metadata']['count']))
            for key in ('temperature_uncertainty', 'replicate_independence', 'scalar_missing_convention'):
                self.assertEqual(row[key], 'null')
            self.assertEqual(row['central_statistic_explicitly_named'], 'null' if p['central_statistic_explicitly_named'] is None else 'median')
            for field, expected in (('record_snapshot_json', r), ('source_snapshots_json', self.bundle['source_snapshots']),
                                    ('source_cell_json', p['source_cell']), ('si_result_json', p['si_result']),
                                    ('sd_source_metadata_json', p['reported_sd']), ('sd_unit_presentation_json', p['sd_unit_presentation']),
                                    ('selection_json', self.bundle['selection']), ('presentation_policy_json', self.bundle['presentation_policy'])):
                self.assertEqual(json.loads(row[field]), expected)
            self.assertEqual(row['record_snapshot_sha256'], digest(r))
        self.assertEqual([r['panel_id'] for r in rows], ['ciganas'] * 6 + ['zach'] * 4)
        self.assertEqual(sum(r['temperature_value_string'] == '100' for r in rows), 2)
        for forbidden in ('derived_lower_string', 'derived_upper_string', 'delta', 'pooled', 'rank', 'retention_ratio'):
            self.assertNotIn(forbidden, columns)

    def test_render_language_and_width_are_strict(self):
        for lang in ('xx', '', None, True, 1, [], {}):
            for render in (view.render_observation_study_comparison_svg, view.render_observation_study_comparison_html):
                with self.subTest(lang=lang, render=render.__name__), self.assertRaises(view.ObservationStudyComparisonError):
                    render(self.bundle, lang=lang)
        for width in (True, False, 319, 1601, 1100.0, '1100', None, [], float('nan'), float('inf')):
            with self.subTest(width=repr(width)), self.assertRaises(view.ObservationStudyComparisonError):
                view.render_observation_study_comparison_svg(self.bundle, width=width)
        for width in (320, 380, 899, 900, 1100, 1600):
            root = ET.fromstring(view.render_observation_study_comparison_svg(self.bundle, width=width))
            self.assertEqual(float(root.attrib['width']), width)

    def test_export_determinism_locale_independent_data_and_preserved_prior_artifacts(self):
        variants = []
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            sentinels = ('observation-inspection.json', 'observation-temperature-plot.en.svg')
            for name in sentinels: (target/name).write_text('prior output ' + name)
            for lang in LANGUAGES:
                paths = view.export_observation_study_comparison(target, profile_id=PROFILE, lang=lang)
                expected = {PREFIX + suffix for suffix in ('.json', '.csv', '.' + lang + '.svg', '.narrow.' + lang + '.svg', '.' + lang + '.html')}
                self.assertEqual(set(paths), expected)
                before = {p.name: p.read_bytes() for p in target.iterdir()}
                view.export_observation_study_comparison(target, profile_id=PROFILE, lang=lang)
                self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
                variants.append((before[PREFIX + '.json'], before[PREFIX + '.csv']))
            self.assertEqual(len([p for p in target.iterdir() if p.name.startswith(PREFIX)]), 14)
            self.assertTrue(all(value == variants[0] for value in variants))
            for name in sentinels: self.assertEqual((target/name).read_text(), 'prior output ' + name)

    def test_preflight_errors_leave_absent_and_existing_targets_untouched(self):
        invalid = ({'profile_id': 'all'}, {'profile_id': None}, {'profile_id': PROFILE, 'lang': 'xx'},
                   {'profile_id': PROFILE, 'lang': None}, {'profile_id': PROFILE, 'lang': True})
        with tempfile.TemporaryDirectory() as tmp:
            for exists in (False, True):
                target = Path(tmp)/str(exists)
                if exists:
                    target.mkdir()
                    for suffix in ('.json', '.csv', '.en.svg', '.narrow.en.svg', '.en.html'):
                        (target/(PREFIX + suffix)).write_text('sentinel ' + suffix)
                before = {p.name: p.read_bytes() for p in target.iterdir()} if exists else None
                def unchanged():
                    self.assertEqual(target.exists(), exists)
                    if exists: self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
                for kwargs in invalid:
                    with self.subTest(exists=exists, kwargs=kwargs), self.assertRaises(view.ObservationStudyComparisonError):
                        view.export_observation_study_comparison(target, **kwargs)
                    unchanged()
                with self.assertRaises(TypeError): view.export_observation_study_comparison(target)
                unchanged()
                changed = deepcopy(self.observations)
                next(r for r in changed['records'] if r['id'] == self.ids[-1])['sample_metadata']['count'] = 99
                with catalogs(changed), self.assertRaises(view.ObservationStudyComparisonError):
                    view.export_observation_study_comparison(target, profile_id=PROFILE)
                unchanged()
                for function in ('observation_study_comparison_json', 'observation_study_comparison_csv',
                                 'render_observation_study_comparison_svg', 'render_observation_study_comparison_html'):
                    with patch.object(view, function, side_effect=view.ObservationStudyComparisonError('preflight')), self.assertRaises(view.ObservationStudyComparisonError):
                        view.export_observation_study_comparison(target, profile_id=PROFILE)
                    unchanged()

    def test_cli_required_options_final_language_precedence_all_four_and_help(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'missing'
            for args in (['observation', 'compare-temperature-studies', '--output', str(target)],
                         ['observation', 'compare-temperature-studies', '--profile-id', PROFILE]):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                    main(args)
                self.assertEqual(caught.exception.code, 2)
                self.assertFalse(target.exists())
            data = []
            for lang in LANGUAGES:
                target = Path(tmp)/lang
                args = ['--lang', 'zh', 'observation', '--lang', 'ja', 'compare-temperature-studies',
                        '--lang', 'en', '--profile-id', PROFILE, '--output', str(target), '--lang', lang]
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()): result = main(args)
                self.assertIn(result, (0, None))
                for suffix in ('.svg', '.html'): self.assertTrue((target/(PREFIX + '.' + lang + suffix)).is_file())
                data.append(((target/(PREFIX + '.json')).read_bytes(), (target/(PREFIX + '.csv')).read_bytes()))
                help_text = io.StringIO()
                with redirect_stdout(help_text), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                    main(['observation', 'compare-temperature-studies', '--lang', lang, '--help'])
                self.assertEqual(caught.exception.code, 0)
                self.assertIn('--profile-id', help_text.getvalue())
                self.assertNotIn('[missing:', help_text.getvalue())
                from materials_boundaries._observation_study_comparison_labels import labels
                self.assertIn(compact(labels(lang)['profile_id']), compact(help_text.getvalue()))
                self.assertIn(compact(labels(lang)['compare_temperature_studies']), compact(help_text.getvalue()))
            self.assertTrue(all(value == data[0] for value in data))

    def test_old_single_study_and_inspection_remain_separate_nonexpanded_contracts(self):
        from materials_boundaries.observation_temperature_plot import build_observation_temperature_plot, ObservationTemperaturePlotError
        from materials_boundaries.observation_visualization import build_observation_inspection
        old = build_observation_temperature_plot(dataset_id=self.fixture['panels'][0]['dataset_id'])
        self.assertEqual(old['presentation_policy']['axes']['x']['domain'], [15, 125])
        self.assertEqual(old['presentation_policy']['axes']['y']['domain'], [0, 55])
        self.assertEqual(len(old['glyphs']), 6)
        with self.assertRaises(ObservationTemperaturePlotError):
            build_observation_temperature_plot(dataset_id=self.fixture['panels'][1]['dataset_id'])
        inspection = build_observation_inspection(quantity='ultimate_tensile_strength_as_reported_3d')
        self.assertIs(inspection['presentation_policy']['quantitative_axes_allowed'], False)
        self.assertIs(inspection['presentation_policy']['uncertainty_endpoints_calculated'], False)

    def test_runtime_standard_library_only_without_engine_evaluation_or_old_glyphs(self):
        script = (
            'import sys; sys.modules["jsonschema"] = None; sys.modules["referencing"] = None; '
            'from materials_boundaries.observation_study_comparison import *; '
            f'b=build_observation_study_comparison(profile_id={PROFILE!r}); '
            'validate_observation_study_comparison(b); observation_study_comparison_json(b); '
            'observation_study_comparison_csv(b); render_observation_study_comparison_svg(b); '
            'render_observation_study_comparison_html(b); print("ok")'
        )
        result = subprocess.run([sys.executable, '-S', '-c', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'ok')
        with patch('materials_boundaries.engine.evaluate', side_effect=AssertionError('No evaluation')), \
             patch('materials_boundaries.observation_temperature_plot._glyph', side_effect=AssertionError('No historical endpoints')):
            b = view.build_observation_study_comparison(profile_id=PROFILE)
            for output in self.outputs: output(b)

    def test_public_schema_accepts_canonical_and_closes_policy_points_and_snapshots(self):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
            from referencing import Registry, Resource
        except ImportError:
            self.skipTest('jsonschema is optional development QA; runtime remains standard-library only')
        schemas = [json.loads((ROOT/'schemas'/name).read_text()) for name in
                   ('observation-study-comparison.schema.json', 'observations.schema.json', 'sources.schema.json')]
        registry = Registry().with_resources((schema['$id'], Resource.from_contents(schema)) for schema in schemas)
        Draft202012Validator.check_schema(schemas[0])
        validator = Draft202012Validator(schemas[0], registry=registry, format_checker=FormatChecker())
        validator.validate(self.bundle)
        changes = [(('kind',), 'observation_inspection'), (('extra',), True),
                   (('selection', 'profile_id'), 'all'), (('panels',), self.bundle['panels'][:1]),
                   (('panels', 0, 'points'), self.bundle['panels'][0]['points'][:5]),
                   (('panels', 0, 'points', 0, 'central_value_string'), '49.070'),
                   (('panels', 0, 'points', 0, 'summary_statistic'), 'mean'),
                   (('panels', 1, 'points', 0, 'summary_statistic'), 'reported_central_value'),
                   (('panels', 1, 'points', 0, 'reported_sd', 'notation'), 'plus_minus'),
                   (('panels', 1, 'points', 0, 'reported_sd', 'header_unit_explicit'), True),
                   (('panels', 1, 'points', 0, 'sample_metadata', 'count'), True),
                   (('panels', 0, 'points', 0, 'derived_lower_string'), '48.19'),
                   (('panels', 0, 'protocol_facts', 0, 'extra'), True),
                   (('record_snapshots', 0, 'sample_metadata', 'count'), True),
                   (('source_snapshots', 0, 'extra'), True)]
        for path, value in changes:
            b = deepcopy(self.bundle); replace(b, path, value)
            with self.subTest(path=path): self.assertFalse(validator.is_valid(b))
        for path, value in leaves(self.bundle['presentation_policy']):
            b = deepcopy(self.bundle); replace(b['presentation_policy'], path, altered(value))
            with self.subTest(policy=path): self.assertFalse(validator.is_valid(b))


    def test_exact_six_four_equal_svg_dots_fixed_linear_transforms_and_responsive_order(self):
        for lang in LANGUAGES:
            for width in (320, 380, 899, 900, 1100, 1600):
                with self.subTest(lang=lang, width=width):
                    root = ET.fromstring(view.render_observation_study_comparison_svg(self.bundle, lang=lang, width=width))
                    charts = by_class(root, 'temperature-plot')
                    panels = by_class(root, 'study-panel')
                    self.assertEqual([p.attrib['data-panel-id'] for p in panels], ['ciganas', 'zach'])
                    self.assertEqual(len(charts), 2)
                    all_centers = list(root.iter(SVG + 'circle'))
                    self.assertEqual(len(all_centers), 10)
                    self.assertEqual(len({c.attrib['r'] for c in all_centers}), 1)
                    self.assertEqual(len({c.attrib['fill'] for c in all_centers}), 1)
                    self.assertEqual(len({c.attrib.get('opacity') for c in all_centers}), 1)
                    chart_extents = []
                    for chart, panel, expected, source in zip(charts, self.bundle['panels'], self.fixture['panels'], self.source_fixtures):
                        self.assertEqual(chart.attrib['data-x-domain'], '15,155')
                        self.assertEqual(chart.attrib['data-y-domain'], '0,65')
                        left, right, top, bottom = [float(chart.attrib['data-plot-' + key]) for key in ('left', 'right', 'top', 'bottom')]
                        self.assertGreater(right, left)
                        self.assertGreater(bottom, top)
                        chart_extents.append((left, right, top, bottom))
                        centers = by_class(chart, 'observation-center')
                        self.assertEqual(len(centers), len(source['cells']))
                        self.assertEqual([''.join(n.itertext()) for n in by_class(chart, 'x-tick')], ['20', '40', '60', '80', '100', '120', '140'])
                        self.assertEqual([''.join(n.itertext()) for n in by_class(chart, 'y-tick')], ['0', '10', '20', '30', '40', '50', '60'])
                        self.assertFalse(any(n.tag.rsplit('}', 1)[-1] in ('path', 'polyline', 'polygon') for n in chart.iter()))
                        for forbidden in ('sd-whisker', 'sd-cap', 'temperature-whisker', 'fit', 'connector', 'interval'):
                            self.assertFalse(by_class(chart, forbidden))
                        # Any plot line must be an axis/grid reference, never a
                        # connector, uncertainty glyph or filled observed area.
                        self.assertTrue(all(n.attrib.get('class') in ('y-grid', 'y-axis', 'x-axis', 'x-tick-mark') for n in chart.iter(SVG + 'line')))
                        xs = []
                        for point, cell, center in zip(panel['points'], source['cells'], centers):
                            x = left + (float(cell['temperature']) - 15) / 140 * (right - left)
                            y = bottom - float(cell[expected['central_field']]) / 65 * (bottom - top)
                            self.assertEqual(center.attrib['data-record-id'], point['record_id'])
                            self.assertEqual(center.attrib['data-temperature'], cell['temperature'])
                            self.assertEqual(center.attrib['data-central-value'], cell[expected['central_field']])
                            self.assertEqual(json.loads(center.attrib['data-source-cell']), point['source_cell'])
                            self.assertAlmostEqual(float(center.attrib['cx']), x, delta=.00001)
                            self.assertAlmostEqual(float(center.attrib['cy']), y, delta=.00001)
                            self.assertTrue(left < x < right and top < y < bottom)
                            xs.append(float(center.attrib['cx']))
                        expected_ratio = 17 / 20 if panel['panel_id'] == 'ciganas' else 25 / 50
                        self.assertAlmostEqual((xs[1] - xs[0]) / (xs[2] - xs[1]), expected_ratio, delta=.00001)
                    first, second = chart_extents
                    self.assertAlmostEqual(first[1] - first[0], second[1] - second[0], delta=.00001)
                    self.assertAlmostEqual(first[3] - first[2], second[3] - second[2], delta=.00001)
                    if width < 900:
                        self.assertEqual(first[0], second[0])
                        self.assertGreater(second[2], first[3])
                    else:
                        self.assertGreater(second[0], first[1])
                        self.assertAlmostEqual(first[2], second[2], delta=.00001)

    def test_four_authored_locales_complete_context_before_first_numeric_property(self):
        from materials_boundaries._observation_study_comparison_labels import LABELS, SCOPE_KEYS, FACT_IDS, labels
        self.assertEqual(set(LABELS), set(LANGUAGES))
        self.assertEqual(tuple(view.WARNING_CODES), SCOPE_KEYS)
        self.assertEqual(list(FACT_IDS), self.fixture['protocol_fact_ids'])
        for lang in LANGUAGES:
            t = labels(lang)
            self.assertEqual(set(t), set(LABELS['en']))
            self.assertTrue(all(type(value) is str and value.strip() for value in t.values()))
            if lang != 'en':
                for key in (*SCOPE_KEYS, 'review', 'glyph_legend', 'profile_id', 'compare_temperature_studies'):
                    self.assertNotEqual(t[key], LABELS['en'][key])
            html = view.render_observation_study_comparison_html(self.bundle, lang=lang)
            parsed = ParsedHTML(html)
            ids = [attrs['id'] for _, attrs in parsed.tags if 'id' in attrs]
            self.assertEqual(len(ids), len(set(ids)), 'HTML IDs must be unique')
            for earlier, later in (('essential-scope', 'protocol-facts'), ('protocol-facts', 'glyph-legend'),
                                   ('glyph-legend', 'temperature-plot-ciganas'),
                                   ('temperature-plot-ciganas', 'exact-source-table-ciganas'),
                                   ('exact-source-table-ciganas', 'temperature-plot-zach'),
                                   ('temperature-plot-zach', 'exact-source-table-zach')):
                self.assertLess(ids.index(earlier), ids.index(later))
            self.assertEqual([attrs['data-fact-id'] for _, attrs in parsed.tags if 'data-fact-id' in attrs], list(FACT_IDS))
            self.assertEqual([attrs['data-warning-code'] for _, attrs in parsed.tags if 'data-warning-code' in attrs], list(SCOPE_KEYS))
            variants = [('HTML', ' '.join(parsed.visible))]
            for width in (320, 380, 1100):
                root = ET.fromstring(view.render_observation_study_comparison_svg(self.bundle, lang=lang, width=width))
                nodes = list(root.iter())
                before = [n for n in nodes if n.attrib.get('id') in ('essential-scope', 'protocol-facts', 'glyph-legend')]
                self.assertEqual(len(before), 3)
                first_circle = next(n for n in nodes if n.tag == SVG + 'circle')
                self.assertTrue(all(nodes.index(n) < nodes.index(first_circle) for n in before))
                self.assertEqual([n.attrib['data-fact-id'] for n in nodes if 'data-fact-id' in n.attrib], list(FACT_IDS))
                self.assertEqual([n.attrib['data-warning-code'] for n in nodes if 'data-warning-code' in n.attrib], list(SCOPE_KEYS))
                variants.append((str(width), ' '.join(''.join(n.itertext()) for n in root.iter(SVG + 'text'))))
            for mode, text in variants:
                with self.subTest(lang=lang, mode=mode):
                    visible = compact(text)
                    first_value = min(visible.index('49.07'), visible.index('58.91'))
                    for key in (*SCOPE_KEYS, 'review', 'glyph_legend', 'axis_notice',
                                *(pid + '_' + fact for fact in FACT_IDS for pid in ('ciganas', 'zach'))):
                        self.assertIn(compact(t[key]), visible, key)
                        self.assertLess(visible.index(compact(t[key])), first_value, key)
                    for pid in ('ciganas', 'zach'):
                        for key in ('product', 'count', 'sd_notice', 'y_axis', 'table_central', 'table_sd'):
                            self.assertIn(compact(t[pid + '_' + key]), visible, pid + '_' + key)
                    for key in ('pdf_notice', 'adaptation', 'metadata_notice', 'ciganas_discrepancy', 'zach_discrepancy'):
                        self.assertIn(compact(t[key]), visible, key)
                    for source in self.source_fixtures:
                        for cell in source['cells']:
                            self.assertIn(cell.get('central', cell.get('median')), visible)
                            self.assertIn(cell['sd'], visible)
                    self.assertNotIn(compact('58.91 ± 3.44'), visible)
                    self.assertNotIn('[missing:', visible)
                    # Numeric SI metadata must not become another visible series.
                    for r in self.bundle['record_snapshots']:
                        self.assertNotIn(str(r['si_result']['value']), text)
        self.assertIn('Natural-convection cooling to room temperature in a vacuum-sealed dehumidified container', LABELS['en']['zach_preparation'])
        self.assertNotIn('controlled cooling', LABELS['en']['zach_preparation'].lower())
        self.assertIn('three tensile tests per temperature condition', LABELS['en']['ciganas_statistic'])
        self.assertIn('five specimens per orientation × temperature × annealing group', LABELS['en']['zach_statistic'])
        self.assertNotIn('mean', LABELS['en']['ciganas_table_central'].lower())

    def test_accessible_always_visible_exact_three_column_tables_and_source_attribution(self):
        from materials_boundaries._observation_study_comparison_labels import labels
        for lang in LANGUAGES:
            t = labels(lang)
            html = view.render_observation_study_comparison_html(self.bundle, lang=lang)
            parsed = ParsedHTML(html)
            for panel, expected, fixture in zip(self.bundle['panels'], self.fixture['panels'], self.source_fixtures):
                pid = panel['panel_id']
                fragment = html.split('<table id="exact-source-table-' + pid + '"', 1)[1].split('</table>', 1)[0]
                table = ParsedHTML('<table' + fragment + '</table>')
                self.assertEqual(sum(tag == 'th' and attrs.get('scope') == 'col' for tag, attrs in table.tags), 3)
                self.assertEqual(sum(tag == 'th' and attrs.get('scope') == 'row' for tag, attrs in table.tags), len(fixture['cells']))
                self.assertEqual(sum(tag == 'td' for tag, _ in table.tags), len(fixture['cells']) * 2)
                self.assertTrue(all('headers' in attrs for tag, attrs in table.tags if tag == 'td'))
                self.assertFalse(any(tag == 'details' for tag, _ in table.tags))
                values = [text.strip() for text in table.visible if text.strip()]
                self.assertEqual(values[:4], [t['table_heading'], t['temperature'], t[pid + '_table_central'], t[pid + '_table_sd']])
                self.assertEqual(values[4:], [value for cell in fixture['cells'] for value in
                                              (cell['temperature'], cell[expected['central_field']], cell['sd'])])
            for width in (320, 380, 1100):
                root = ET.fromstring(view.render_observation_study_comparison_svg(self.bundle, lang=lang, width=width))
                self.assertEqual(root.attrib['role'], 'img')
                self.assertIsNotNone(root.find(SVG + 'title'))
                self.assertIsNotNone(root.find(SVG + 'desc'))
                raw_description = ''.join(root.find(SVG + 'desc').itertext())
                description = compact(raw_description)
                actual_rows = [line for line in raw_description.splitlines() if line.startswith(t['temperature'] + ': ')]
                expected_rows = []
                for expected, fixture in zip(self.fixture['panels'], self.source_fixtures):
                    pid = expected['panel_id']
                    for cell in fixture['cells']:
                        expected_rows.append('; '.join((t['temperature'] + ': ' + cell['temperature'],
                            t[pid + '_table_central'] + ': ' + cell[expected['central_field']],
                            t[pid + '_table_sd'] + ': ' + cell['sd'])))
                self.assertEqual(actual_rows, expected_rows)
                from materials_boundaries._observation_study_comparison_labels import SCOPE_KEYS, FACT_IDS
                first_value = min(description.index('49.07'), description.index('58.91'))
                for key in (*SCOPE_KEYS, 'review', 'glyph_legend', 'axis_notice',
                            *(pid + '_' + fact for fact in FACT_IDS for pid in ('ciganas', 'zach'))):
                    self.assertIn(compact(t[key]), description)
                    self.assertLess(description.index(compact(t[key])), first_value)
                for source in self.source_fixtures:
                    for cell in source['cells']:
                        self.assertIn(cell.get('central', cell.get('median')), description)
                        self.assertIn(cell['sd'], description)
                self.assertNotIn('record_snapshots', description)
                for panel, expected, fixture in zip(self.bundle['panels'], self.fixture['panels'], self.source_fixtures):
                    table = next(n for n in root.iter() if n.attrib.get('id') == 'exact-source-table-' + panel['panel_id'])
                    self.assertEqual(table.attrib['role'], 'table')
                    self.assertEqual(sum(n.attrib.get('role') == 'columnheader' for n in table.iter()), 3)
                    rows = by_class(table, 'source-row')
                    self.assertEqual(len(rows), len(fixture['cells']))
                    for row, point, cell in zip(rows, panel['points'], fixture['cells']):
                        self.assertEqual(row.attrib['data-record-id'], point['record_id'])
                        self.assertEqual([''.join(n.itertext()).strip() for n in row.iter() if n.attrib.get('role') == 'cell'],
                                         [cell['temperature'], cell[expected['central_field']], cell['sd']])
                source_context = next(n for n in root.iter() if n.attrib.get('id') == 'source-context')
                visible = compact(''.join(source_context.itertext()))
                for source in self.bundle['source_snapshots']:
                    self.assertIn(compact(source['title']), visible)
                    self.assertIn(source['doi'], visible)
                for panel in self.bundle['panels']:
                    cell = panel['points'][0]['source_cell']
                    for key in ('table_container_id', 'expanded_table_id'):
                        self.assertIn(cell[key], visible)
                hrefs = [n.attrib['href'] for n in root.iter() if 'href' in n.attrib]
                self.assertIn('https://creativecommons.org/licenses/by/4.0/', hrefs)
                self.assertIn('https://doi.org/10.3390/polym18050563', hrefs)
                self.assertIn('https://doi.org/10.3390/jcs9110624', hrefs)
            audit = next(attrs for tag, attrs in parsed.tags if tag == 'details')
            self.assertEqual(audit.get('id'), 'audit-details')
            self.assertNotIn('open', audit)
            self.assertIn('@media print', html)
            self.assertIn('@media(max-width:899px)', html)
            self.assertIn(':focus-visible', html)

    def test_html_and_svg_are_offline_inert_and_escape_formula_like_display_identity(self):
        observations = deepcopy(self.observations)
        attack = '=literal, "quote" </pre><script>alert(1)</script><img src=x onerror=alert(2)> & Ω'
        rid = 'cell_<"&>\' onload="alert(3)' + 'x' * 120
        record = next(r for r in observations['records'] if r['id'] == self.ids[0])
        record['id'], record['name'] = rid, attack
        with catalogs(observations):
            b = view.build_observation_study_comparison(profile_id=PROFILE)
            row = next(csv.DictReader(io.StringIO(view.observation_study_comparison_csv(b))))
            self.assertEqual(row['record_id'], rid)
            self.assertEqual(json.loads(row['record_snapshot_json'])['name'], attack)
            self.assertIn('formula', b['presentation_policy']['csv_text_import_required'])
            for lang in LANGUAGES:
                html = view.render_observation_study_comparison_html(b, lang=lang)
                parsed = ParsedHTML(html)
                audit = json.loads(''.join(parsed.pre_contents['study-comparison-json']))
                self.assertEqual(audit, b)
                self.assertEqual(audit['record_snapshots'][0]['name'], attack)
                self.assertNotIn('<script', html)
                self.assertIn('&lt;script&gt;', html)
                self.assertFalse(any(tag in ('script', 'img', 'iframe', 'object', 'embed', 'link') for tag, _ in parsed.tags))
                self.assertFalse(any(key.lower().startswith('on') for _, attrs in parsed.tags for key in attrs))
                self.assertNotIn('@import', html)
                self.assertNotIn('url(', html)
                self.assertTrue(all(attrs['href'].startswith(('https://', 'http://', '#')) for _, attrs in parsed.tags if 'href' in attrs))
                for width in (320, 1100):
                    root = ET.fromstring(view.render_observation_study_comparison_svg(b, lang=lang, width=width))
                    self.assertEqual(by_class(root, 'observation-center')[0].attrib['data-record-id'], rid)
                    self.assertFalse(any(n.tag.rsplit('}', 1)[-1] in ('script', 'image', 'foreignObject', 'iframe') for n in root.iter()))
                    self.assertFalse(any(key.lower().startswith('on') for n in root.iter() for key in n.attrib))
                    self.assertTrue(all(n.attrib['href'].startswith(('https://', 'http://')) for n in root.iter() if 'href' in n.attrib))
                    # Text line anchors remain on-page; font-shape/clipping and
                    # actual HTML zoom/print are separately checked in browser QA.
                    for node in root.iter(SVG + 'text'):
                        self.assertGreaterEqual(float(node.attrib['font-size']), 10)
                        self.assertTrue(0 <= float(node.attrib['x']) <= width)
                        self.assertTrue(0 <= float(node.attrib['y']) <= float(root.attrib['height']))


    def test_responsive_html_points_retain_the_same_numeric_coordinate_transform(self):
        for lang in LANGUAGES:
            parsed = ParsedHTML(view.render_observation_study_comparison_html(self.bundle, lang=lang))
            charts = [attrs for tag, attrs in parsed.tags if tag == 'svg' and 'temperature-plot' in attrs.get('class', '').split()]
            self.assertEqual(len(charts), 2)
            centers = [attrs for tag, attrs in parsed.tags if tag == 'circle']
            self.assertEqual(len(centers), 10)
            self.assertEqual(len({c['r'] for c in centers}), 1)
            self.assertEqual(len({c['fill'] for c in centers}), 1)
            points = [p for panel in self.bundle['panels'] for p in panel['points']]
            for center, point in zip(centers, points):
                self.assertEqual(center['class'], 'observation-center')
                self.assertEqual(center['data-record-id'], point['record_id'])
                self.assertEqual(json.loads(center['data-source-cell']), point['source_cell'])
                self.assertTrue(center['cx'].endswith('%'))
                expected_x = (float(point['temperature']['value_string']) - 15) / 140 * 100
                self.assertAlmostEqual(float(center['cx'][:-1]), expected_x, delta=.00001)
                self.assertAlmostEqual(float(center['cy']), 270 - float(point['central_value_string']) / 65 * 260, delta=.00001)
            for chart in charts:
                self.assertEqual(chart['data-x-domain'], '15,155')
                self.assertEqual(chart['data-y-domain'], '0,65')
                self.assertEqual(chart['data-plot-left'], '0')
                self.assertEqual(chart['data-plot-right'], '100%')
            self.assertFalse(any(tag in ('path', 'polyline', 'polygon') for tag, _ in parsed.tags))

    def test_invalid_cli_profile_language_and_unrequested_options_never_write_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            for exists in (False, True):
                target = Path(tmp)/str(exists)
                if exists:
                    target.mkdir(); (target/(PREFIX + '.json')).write_text('unchanged')
                before = {p.name: p.read_bytes() for p in target.iterdir()} if exists else None
                base = ['observation', 'compare-temperature-studies', '--output', str(target)]
                for options in (['--profile-id', 'all'], ['--profile-id', PROFILE, '--lang', 'xx'],
                                ['--profile-id', PROFILE, '--record-ids', self.ids[0]],
                                ['--profile-id', PROFILE, '--width', '1000'],
                                ['--profile-id', PROFILE, '--hide-sd']):
                    with self.subTest(exists=exists, options=options), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                        main(base + options)
                    self.assertEqual(caught.exception.code, 2)
                    self.assertEqual(target.exists(), exists)
                    if exists: self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
