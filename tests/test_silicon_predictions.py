"""Source-led silicon regressions, closed semantics, and additive compatibility.

The transcription fixture comes from the inspected paper's factual audit, not
production objects. The preservation fixture comes from frozen v0.12.0. Neither
fixture specifies the size or ordering of the growing real catalog.
"""
import copy
from provenance_corrections import (historical_record, historical_temperature_result,
                                    historical_locales, reviewed_test_hash)
import csv
from hashlib import sha256
from html.parser import HTMLParser
import io
import json
from pathlib import Path
from viscoelastic_preservation import pre_viscoelastic_bytes
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from materials_boundaries import __version__, evaluate, load_json
from materials_boundaries.catalog import CatalogLookupError, query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.predictions import (
    DEFAULT_GROUP, PredictionError, canonical_json, method_evidence,
    prediction_labels, validate_prediction_catalog, value_evidence,
)
from materials_boundaries.prediction_visualization import (
    build_prediction_comparison, comparison_csv, comparison_json,
    export_prediction_comparison, render_prediction_html, render_prediction_svg,
    validate_prediction_comparison,
)
from materials_boundaries.silicon_predictions import (
    critical_strain_evidence, instability_mode_evidence,
)
from materials_boundaries.temperature import evaluate_temperature
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = load_json(ROOT / 'tests/fixtures/silicon_source_transcription.json')
BASELINE = load_json(ROOT / 'tests/fixtures/pre_silicon_baseline.json')
LANGUAGES = ('en', 'zh', 'ja', 'de')
GROUP = FIXTURE['group_id']
PROTOCOL = FIXTURE['protocol_id']
SOURCE = FIXTURE['source_id']
QUANTITY = FIXTURE['quantity']
FAMILY = FIXTURE['family']
FIRST_RECORD = FIXTURE['records'][0]['id']
SYNTHETIC = {
    'source': 'synthetic_silicon_source_beta',
    'protocol': 'synthetic_silicon_protocol_gamma',
    'group': 'synthetic_silicon_group_delta',
    'record': 'synthetic_silicon_record_epsilon',
}


def digest(value):
    return sha256(canonical_json(value).encode()).hexdigest()


def version_neutral_digest(text):
    text = text.replace('v' + __version__, 'v<VERSION>')
    text = text.replace('"engine_version": "' + __version__ + '"',
                        '"engine_version": "<VERSION>"')
    text = text.replace('&quot;engine_version&quot;: &quot;' + __version__ + '&quot;',
                        '&quot;engine_version&quot;: &quot;<VERSION>&quot;')
    return sha256(text.encode()).hexdigest()


def by_id(items, identifier):
    return next(item for item in items if item['id'] == identifier)


def scientific_objects(catalogs):
    predictions = catalogs['computational_predictions']
    return {
        'record': by_id(predictions['records'], FIRST_RECORD),
        'protocol': by_id(predictions['protocols'], PROTOCOL),
        'group': by_id(predictions['comparison_groups'], GROUP),
    }


def replace_field(catalogs, target, path, value):
    node = scientific_objects(catalogs)[target]
    parts = path.split('.')
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    final = int(parts[-1]) if isinstance(node, list) else parts[-1]
    node[final] = value


def evidence_sets(catalogs, *, synthetic=False):
    predictions = catalogs['computational_predictions']
    record = by_id(predictions['records'], SYNTHETIC['record'] if synthetic else FIRST_RECORD)
    protocol = by_id(predictions['protocols'], SYNTHETIC['protocol'] if synthetic else PROTOCOL)
    return {
        'strength': (record['evidence'], 'reported_tensile_first_instability_strength'),
        'strain': (record['critical_engineering_strain']['evidence'], 'reported_critical_engineering_strain'),
        'mode': (record['first_instability']['evidence'], 'reported_first_instability_mode'),
        'method': (protocol['evidence'], 'cell construction'),
    }


def synthetic_catalogs(catalogs=None):
    """A new source and linked objects, deliberately not another real result."""
    catalogs = (load_catalogs(ROOT / 'materials_boundaries/data') if catalogs is None
                else copy.deepcopy(catalogs))
    predictions = catalogs['computational_predictions']
    source = copy.deepcopy(by_id(catalogs['sources']['records'], SOURCE))
    source.update(
        id=SYNTHETIC['source'], title='SYNTHETIC silicon plumbing fixture only',
        doi=None, urls=['https://example.invalid/synthetic-silicon'],
        read_status='synthetic_not_a_real_source',
        license={'status': 'not_applicable_synthetic', 'identifier': None},
        claim_notes=['SYNTHETIC TEST ONLY; no new paper or scientific result.'],
        provenance={'curation_date': '2026-10-02', 'method': 'Synthetic regression fixture; no source inspection.'},
    )
    protocol = copy.deepcopy(by_id(predictions['protocols'], PROTOCOL))
    protocol.update(id=SYNTHETIC['protocol'], source_id=SYNTHETIC['source'])
    group = copy.deepcopy(by_id(predictions['comparison_groups'], GROUP))
    group.update(id=SYNTHETIC['group'], source_id=SYNTHETIC['source'],
                 protocol_id=SYNTHETIC['protocol'], record_ids=[SYNTHETIC['record']])
    group['names'] = {lang: 'SYNTHETIC silicon group ' + lang for lang in LANGUAGES}
    record = copy.deepcopy(by_id(predictions['records'], FIRST_RECORD))
    record.update(id=SYNTHETIC['record'], source_id=SYNTHETIC['source'],
                  protocol_id=SYNTHETIC['protocol'], comparison_group_id=SYNTHETIC['group'],
                  name='SYNTHETIC silicon result', value_GPa=24.65,
                  source_value_string='24.650', reported_decimal_places=3,
                  source_table='Synthetic Table S8', source_pdf_page_1_based=81)
    record['names'] = {lang: 'SYNTHETIC silicon result ' + lang for lang in LANGUAGES}
    record['descriptions'] = {lang: 'SYNTHETIC plumbing description ' + lang for lang in LANGUAGES}
    record['critical_engineering_strain'].update(value=0.29, source_value_string='29')
    record['first_instability'].update(source_table='Synthetic Table S9', source_pdf_page_1_based=83)
    locators = {
        'strength': 'SYNTHETIC strength, Table S8, PDF page 81',
        'strain': 'SYNTHETIC strain, Table S7, PDF page 82',
        'mode': 'SYNTHETIC mode, Table S9, PDF page 83',
        'method': 'SYNTHETIC method, Section M4, PDF page 84',
    }
    fresh = {'computational_predictions': {'records': [record], 'protocols': [protocol]}}
    for kind, (entries, primary_support) in evidence_sets(fresh, synthetic=True).items():
        for index, entry in enumerate(entries):
            entry.update(source_id=source['id'],
                         locator=locators[kind] if primary_support in entry['supports'] else f'SYNTHETIC auxiliary method {index}',
                         url=f'https://example.invalid/silicon/{kind}' if primary_support in entry['supports'] else f'https://example.invalid/silicon/aux-{index}')
        entries.insert(0, {'source_id': source['id'], 'locator': 'SYNTHETIC decoy first evidence',
                           'url': 'https://example.invalid/decoy', 'supports': ['auxiliary_context_only']})
    # Build final objects before adding them. A complete disposable mixed
    # contribution catalog may already contain this exact approved fixture.
    for sequence, item in ((catalogs['sources']['records'], source),
                           (predictions['protocols'], protocol),
                           (predictions['comparison_groups'], group),
                           (predictions['records'], record)):
        existing = next((r for r in sequence if r['id'] == item['id']), None)
        if existing is None:
            sequence.append(item)
        elif existing != item:
            raise AssertionError('Existing synthetic silicon fixture differs: ' + item['id'])
    return catalogs


class VisibleText(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.parts = []
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href'))

    def handle_data(self, data):
        self.parts.append(data)


def compact(text):
    return ''.join(text.split())


class SiliconPreservationTests(unittest.TestCase):
    def test_every_pre_silicon_scientific_record_and_ni_metadata_is_unchanged(self):
        for kind, historical in BASELINE['records'].items():
            current = {record['id']: record for record in read_catalog(kind)['records']}
            for identifier, expected in historical.items():
                with self.subTest(kind=kind, identifier=identifier):
                    self.assertIn(identifier, current)
                    stable = historical_record(kind, current[identifier])
                    for field, expected_items in expected['additive_item_sha256'].items():
                        items = stable['verification'].pop('gaps') if field == 'verification.gaps' else stable.pop(field)
                        actual_items = [digest(item) for item in items]
                        for expected_item in expected_items:
                            self.assertIn(expected_item, actual_items, identifier + ':' + field)
                    self.assertEqual(digest(stable), expected['stable_sha256'])
        predictions = read_catalog('computational_predictions')
        for field, historical in BASELINE['prediction_metadata'].items():
            current = {item['id']: item for item in predictions[field]}
            for identifier, expected in historical.items():
                self.assertEqual(digest(current[identifier]), expected, identifier)

    def test_legacy_language_values_and_reviewed_test_updates_are_preserved(self):
        for kind, old in BASELINE['legacy_locales'].items():
            current = historical_locales(kind, load_json(ROOT / 'materials_boundaries/data' / (kind + '.json')))
            for key, value in old['envelope'].items():
                self.assertEqual(current[key], value, kind + ':' + key)
            for lang, expected in old['language_sha256'].items():
                projected = {key: current['languages'][lang][key] for key in old['existing_keys']}
                self.assertEqual(digest(projected), expected, kind + ':' + lang)
        for filename, expected in BASELINE['original_tests_and_fixtures'].items():
            update = BASELINE.get('approved_test_updates', {}).get(filename)
            if update is not None:
                self.assertEqual(update['previous_sha256'], expected, filename)
                self.assertTrue(update['reason'].strip())
                expected = update['sha256']
            expected = reviewed_test_hash(filename, expected)
            self.assertEqual(sha256(pre_viscoelastic_bytes(filename, (ROOT / filename).read_bytes())).hexdigest(), expected, filename)

    def test_legacy_evaluations_and_exact_ni_outputs_are_preserved(self):
        for filename, expected in BASELINE['composite_outputs'].items():
            result = evaluate(load_json(ROOT / 'examples' / filename))
            result.pop('engine_version')
            self.assertEqual(digest(result), expected, filename)
        for filename, expected in BASELINE['temperature_outputs'].items():
            result = evaluate_temperature(load_json(ROOT / 'examples/temperature' / filename))
            self.assertEqual(result.pop('id'), digest(result)[:20])
            result.pop('engine_version')
            self.assertEqual(digest(historical_temperature_result(result)), expected, filename)
        bundle = build_prediction_comparison(DEFAULT_GROUP)
        normalized = copy.deepcopy(bundle)
        normalized.pop('engine_version')
        expected = BASELINE['ni_outputs']
        self.assertEqual(digest(normalized), expected['bundle_sha256'])
        self.assertEqual(version_neutral_digest(comparison_csv(bundle)), expected['csv_sha256'])
        old_source = bundle['group_snapshot']['source_id']
        for lang in LANGUAGES:
            # A source query is intentionally additive as new real records arrive.
            # Keep this historical golden scoped to the original explicit group;
            # the six-record batch tests separately assert the broader query.
            original_selection = query_catalog('predictions', source_id=old_source)
            by_record_id = {record['id']: record for record in original_selection['records']}
            original_selection['records'] = [by_record_id[identifier]
                                             for identifier in bundle['group_snapshot']['record_ids']]
            text = render_catalog(original_selection, 'predictions', lang)
            self.assertEqual(version_neutral_digest(text), expected['text_' + lang])
            self.assertEqual(version_neutral_digest(render_prediction_html(bundle, lang=lang)), expected['html_' + lang])
            for width in (360, 380, 1100, 1600):
                svg = render_prediction_svg(bundle, lang=lang, width=width)
                self.assertEqual(version_neutral_digest(svg), expected[f'svg_{lang}_{width}'])


class SiliconSourceAndContractTests(unittest.TestCase):
    def setUp(self):
        self.catalogs = load_catalogs(ROOT / 'materials_boundaries/data')

    def assert_rejected(self, mutation, label):
        candidate = copy.deepcopy(self.catalogs)
        mutation(candidate)
        with self.subTest(case=label, validator='runtime'):
            with self.assertRaises(PredictionError):
                validate_prediction_catalog(candidate['computational_predictions'], candidate['sources'])
        with self.subTest(case=label, validator='development'):
            with self.assertRaises(CatalogValidationError):
                validate_catalogs(candidate)

    def test_independent_source_transcription_and_exact_three_row_real_group(self):
        predictions = self.catalogs['computational_predictions']
        before = copy.deepcopy(self.catalogs)
        validate_prediction_catalog(predictions, self.catalogs['sources'])
        validate_catalogs(self.catalogs)
        self.assertEqual(self.catalogs, before)
        group = by_id(predictions['comparison_groups'], GROUP)
        self.assertEqual(set(group['record_ids']), {r['id'] for r in FIXTURE['records']})
        self.assertEqual(len(group['record_ids']), 3)
        self.assertEqual({r['id'] for r in predictions['records'] if r['source_id'] == SOURCE},
                         {r['id'] for r in FIXTURE['records']})
        source = by_id(self.catalogs['sources']['records'], SOURCE)
        self.assertEqual(source['doi'], FIXTURE['provenance']['doi'])
        self.assertEqual(source['title'], FIXTURE['provenance']['title'])
        self.assertIn(FIXTURE['provenance']['primary_copy_url'], source['urls'])
        for expected in FIXTURE['records']:
            record = by_id(predictions['records'], expected['id'])
            for key in ('id', 'formula', 'source_table_label', 'source_value_string', 'value_GPa',
                        'unit', 'reported_decimal_places', 'reported_strength_definition'):
                self.assertEqual(record[key], expected[key], key)
            for key in ('source_id', 'protocol_id', 'source_table', 'source_pdf_page_1_based'):
                self.assertEqual(record[key], FIXTURE[key], key)
            self.assertEqual(record['comparison_group_id'], GROUP)
            self.assertEqual(record['quantity'], QUANTITY)
            self.assertEqual(record['cell_composition'], 'Si2')
            self.assertEqual(record['stoichiometry_in_model_cell'], {'Si': 2})
            self.assertEqual(record['direction'], {
                'family_indices': expected['loading_direction_family_indices'],
                'display': expected['loading_direction_display'], 'notation': expected['direction_notation'],
            })
            strain = record['critical_engineering_strain']
            self.assertEqual(strain['quantity'], 'critical_engineering_strain_at_first_instability')
            self.assertEqual(strain['value'], expected['engineering_strain_at_reported_strength'])
            self.assertEqual(strain['source_value_string'], expected['source_strain_value_string'])
            self.assertEqual(strain['source_unit'], '%')
            self.assertEqual(strain['unit'], '1')
            self.assertEqual(strain['reported_decimal_places'], 0)
            for key, value in expected['first_instability'].items():
                self.assertEqual(record['first_instability'][key], value)
            self.assertIn('#page=3', value_evidence(record)['url'])
            self.assertIn('stress', value_evidence(record)['locator'])
            self.assertIn('engineering strain', critical_strain_evidence(record)['locator'])
            self.assertIn('Table III', instability_mode_evidence(record)['locator'])

    def test_fixed_transverse_strain_internal_relaxation_and_unknowns(self):
        objects = scientific_objects(self.catalogs)
        protocol, record, group = (objects[k] for k in ('protocol', 'record', 'group'))
        method = FIXTURE['method']
        self.assertEqual(protocol['family'], FAMILY)
        self.assertEqual(protocol['property'], QUANTITY)
        self.assertEqual(protocol['structure']['cell_type_reported'], method['cell_type'])
        self.assertEqual(protocol['structure']['atoms_per_cell'], method['atoms_per_cell'])
        self.assertEqual(protocol['structure']['lattice_constant_reported_bohr'], method['lattice_constant_bohr'])
        self.assertIsNone(protocol['structure']['crystal_structure_reported'])
        self.assertEqual(protocol['structure']['crystal_structure_normalized'], 'diamond_cubic')
        self.assertIn('infer', protocol['structure']['crystal_structure_normalization_status'].lower())
        self.assertIsNone(protocol['structure']['space_group_number'])
        for key, expected in (('fixed_during_relaxation', method['fixed']), ('relaxed', method['relaxed']),
                              ('transverse_strain_constraint', method['transverse_strain_constraint']),
                              ('transverse_stress', method['transverse_stress'])):
            self.assertEqual(protocol['loading'][key], expected)
        self.assertEqual(protocol['loading']['strain_measure_for_tabulated_critical_strain'], 'engineering')
        self.assertIsNone(protocol['loading']['exact_strain_schedule'])
        self.assertIn('no explicit Cauchy/nominal', protocol['loading']['stress_measure'])
        calculation = protocol['calculation']
        self.assertEqual(calculation['software'], method['software'])
        self.assertEqual(calculation['plane_wave_cutoff'], {'value': method['plane_wave_cutoff_hartree'], 'unit': 'hartree'})
        self.assertEqual(calculation['kpoint_mesh'], method['kpoint_mesh'])
        self.assertEqual(calculation['phonon_qpoint_mesh'], method['phonon_qpoint_mesh'])
        self.assertEqual(calculation['smearing']['value'], method['cold_smearing_hartree'])
        self.assertIs(calculation['smearing']['physical_temperature'], False)
        for key in ('physical_temperature_K', 'pressure_GPa', 'magnetic_state', 'spin_polarization'):
            self.assertIsNone(protocol['state_fields'][key])
        self.assertFalse(group['unknown_conditions_equivalent'])
        self.assertFalse(group['cross_study_comparison_allowed'])
        self.assertFalse(record['universal_upper_bound'])
        self.assertFalse(record['verification']['raw_inputs_audited'])
        self.assertFalse(protocol['verification']['independent_scientific_review'])

    def test_numerical_error_is_not_uncertainty_or_relaxed_loading_constraint(self):
        objects = scientific_objects(self.catalogs)
        controls = objects['protocol']['numerical_controls']
        numerical = controls['author_numerical_stress_error_estimate_GPa']
        self.assertEqual(numerical['value'], 0.05)
        self.assertEqual(numerical['qualifier'], 'less_than_approximately')
        self.assertFalse(numerical['is_statistical_or_total_uncertainty'])
        self.assertEqual(controls['relaxed_loading_residual_stress_threshold_GPa'],
                         {'value': 0.02, 'applies_to_this_fixed_lattice_batch': False})
        for key in ('statistical_uncertainty_GPa', 'total_model_uncertainty_GPa'):
            self.assertIsNone(controls[key])
        self.assertIsNone(objects['record']['uncertainty_GPa'])
        self.assertIsNone(objects['record']['critical_engineering_strain']['uncertainty'])
        self.assertIn('not per-record error bars', objects['record']['uncertainty_reason'])

    def test_decimal_context_does_not_change_exact_percentage_validation(self):
        from decimal import localcontext
        with localcontext() as context:
            context.prec = 1
            validate_prediction_catalog(self.catalogs['computational_predictions'], self.catalogs['sources'])
            validate_catalogs(self.catalogs)
            bundle = build_prediction_comparison(GROUP)
            self.assertEqual({s['value'] for s in bundle['associated_critical_strains']}, {0.31, 0.25, 0.19})

    def test_runtime_and_development_reject_scientific_semantic_mutations(self):
        cases = [
            ('record', 'quantity', 'ideal_shear_strength'),
            ('record', 'reported_strength_definition', 'generic_stress_path_maximum'),
            ('record', 'evidence_type', 'experimental_observation'),
            ('record', 'evaluation_support', 'executable'),
            ('record', 'material_representation', 'commercial_silicon_grade'),
            ('record', 'commercial_alloy_grade', True),
            ('record', 'universal_upper_bound', True),
            ('record', 'formula', 'C'), ('record', 'cell_composition', 'Si8'),
            ('record', 'stoichiometry_in_model_cell', {'Si': 8}),
            ('record', 'source_table_label', '⟨100⟩ uniaxial tension'),
            ('record', 'direction.family_indices', [1, 0, -1]),
            ('record', 'direction.family_indices', [True, 0, 0]),
            ('record', 'direction.display', '[100]'),
            ('record', 'direction.notation', 'specific_signed_vector'),
            ('record', 'first_instability.mode', '⟨110⟩ tension'),
            ('record', 'first_instability.type', 'plastic'),
            ('record', 'first_instability.phonon_wavevector_location', 'non_zone_center'),
            ('record', 'verification.independent_scientific_review', True),
            ('protocol', 'family', 'unsupported_silicon_family'),
            ('protocol', 'family', []), ('protocol', 'family', {}),
            ('protocol', 'property', 'ultimate_tensile_strength'),
            ('protocol', 'loading.relaxed', 'atomic positions and transverse lattice vectors'),
            ('protocol', 'loading.transverse_stress', 'relaxed to zero'),
            ('protocol', 'loading.transverse_strain_constraint', 'unconstrained'),
            ('protocol', 'loading.strain_measure_for_tabulated_critical_strain', 'true'),
            ('protocol', 'loading.stress_measure', 'Cauchy'),
            ('protocol', 'structure.atoms_per_cell', 8),
            ('protocol', 'structure.crystal_structure_reported', 'diamond_cubic'),
            ('protocol', 'structure.space_group_number', 227),
            ('protocol', 'calculation.exchange_correlation', 'PBE'),
            ('protocol', 'calculation.smearing.physical_temperature', True),
            ('protocol', 'strength_criterion.reported', 'maximum stress along any path'),
            ('group', 'comparison_axis', 'composition'),
            ('group', 'unknown_conditions_equivalent', True),
            ('group', 'raw_inputs_audited', True),
            ('group', 'cross_study_comparison_allowed', True),
            ('group', 'excluded_interpretations', []),
        ]
        for target, path, value in cases:
            self.assert_rejected(lambda c, t=target, p=path, v=value: replace_field(c, t, p, v),
                                 target + '.' + path)

    def test_wrong_units_percentage_scale_precision_and_numeric_error_guards(self):
        cases = [
            ('unit', 'MPa'), ('value_GPa', True), ('value_GPa', None),
            ('value_GPa', 0), ('value_GPa', -27.8), ('value_GPa', float('nan')),
            ('value_GPa', float('inf')), ('value_GPa', 10 ** 1000),
            ('source_value_string', '27.80'), ('reported_decimal_places', 2),
            ('critical_engineering_strain.unit', '%'),
            ('critical_engineering_strain.source_unit', '1'),
            ('critical_engineering_strain.quantity', 'true_strain'),
            ('critical_engineering_strain.definition', 'strain_at_any_stress_maximum'),
            ('critical_engineering_strain.value', 31),
            ('critical_engineering_strain.value', 0.0031),
            ('critical_engineering_strain.value', True),
            ('critical_engineering_strain.value', None),
            ('critical_engineering_strain.value', 0),
            ('critical_engineering_strain.value', float('nan')),
            ('critical_engineering_strain.value', float('inf')),
            ('critical_engineering_strain.source_value_string', '0.31'),
            ('critical_engineering_strain.source_value_string', '31.0'),
            ('critical_engineering_strain.source_value_string', '31%'),
            ('critical_engineering_strain.source_value_string', '031'),
            ('critical_engineering_strain.reported_decimal_places', 1),
            ('critical_engineering_strain.precision_note', ''),
        ]
        for path, value in cases:
            self.assert_rejected(lambda c, p=path, v=value: replace_field(c, 'record', p, v), path)

    def test_unknown_state_uncertainty_and_false_precision_remain_closed(self):
        cases = [
            ('record', 'uncertainty_GPa', 0.05),
            ('record', 'critical_engineering_strain.uncertainty', 0.01),
            ('protocol', 'state_fields.physical_temperature_K', 0),
            ('protocol', 'state_fields.physical_temperature_K', 77),
            ('protocol', 'state_fields.pressure_GPa', 0),
            ('protocol', 'state_fields.magnetic_state', 'nonmagnetic'),
            ('protocol', 'state_fields.spin_polarization', False),
            ('protocol', 'numerical_controls.statistical_uncertainty_GPa', 0.05),
            ('protocol', 'numerical_controls.total_model_uncertainty_GPa', 0.05),
            ('protocol', 'numerical_controls.author_numerical_stress_error_estimate_GPa.is_statistical_or_total_uncertainty', True),
            ('protocol', 'numerical_controls.author_numerical_stress_error_estimate_GPa.qualifier', 'exact'),
            ('protocol', 'numerical_controls.relaxed_loading_residual_stress_threshold_GPa.applies_to_this_fixed_lattice_batch', True),
            ('protocol', 'unknown_field_reasons.temperature', ''),
        ]
        for target, path, value in cases:
            self.assert_rejected(lambda c, t=target, p=path, v=value: replace_field(c, t, p, v),
                                 target + '.' + path)

    def test_null_containers_missing_fields_and_bad_references_fail_cleanly(self):
        for target, path in (('record', 'direction'), ('record', 'critical_engineering_strain'),
                             ('record', 'first_instability'), ('record', 'descriptions'),
                             ('protocol', 'state_fields'), ('protocol', 'numerical_controls')):
            self.assert_rejected(lambda c, t=target, p=path: replace_field(c, t, p, None), target + '.' + path)
        for field in ('source_id', 'protocol_id', 'comparison_group_id'):
            self.assert_rejected(lambda c, f=field: scientific_objects(c)['record'].update({f: 'missing'}), field)
        for field in ('critical_engineering_strain', 'first_instability', 'reported_strength_definition'):
            self.assert_rejected(lambda c, f=field: scientific_objects(c)['record'].pop(f), 'missing ' + field)
        for field in ('names', 'descriptions'):
            self.assert_rejected(lambda c, f=field: scientific_objects(c)['record'][f].pop('ja'), field + '.ja')

    def test_cross_family_cross_source_group_and_duplicate_direction_rejections(self):
        ni = by_id(self.catalogs['computational_predictions']['comparison_groups'], DEFAULT_GROUP)
        cases = [
            lambda c: scientific_objects(c)['record'].update(protocol_id=ni['protocol_id']),
            lambda c: scientific_objects(c)['record'].update(comparison_group_id=DEFAULT_GROUP),
            lambda c: scientific_objects(c)['group']['record_ids'].append(ni['record_ids'][0]),
            lambda c: scientific_objects(c)['group'].update(protocol_id=ni['protocol_id']),
            lambda c: scientific_objects(c)['protocol'].update(source_id=ni['source_id']),
            lambda c: scientific_objects(c)['group']['record_ids'].append(FIRST_RECORD),
        ]
        for index, mutation in enumerate(cases):
            self.assert_rejected(mutation, 'cross-family/group ' + str(index))
        def duplicate_direction(catalogs):
            predictions = catalogs['computational_predictions']
            record = copy.deepcopy(scientific_objects(catalogs)['record'])
            record['id'] = 'synthetic_duplicate_silicon_direction'
            predictions['records'].append(record)
            scientific_objects(catalogs)['group']['record_ids'].append(record['id'])
        self.assert_rejected(duplicate_direction, 'different IDs with same direction in one comparison')

    def test_each_semantic_evidence_route_requires_one_primary(self):
        for kind in ('strength', 'strain', 'mode', 'method'):
            for operation in ('remove', 'duplicate', 'wrong_source', 'bad_url', 'blank_locator'):
                def mutate(catalogs, k=kind, op=operation):
                    entries, support = evidence_sets(catalogs)[k]
                    primary = next(entry for entry in entries if support in entry['supports'])
                    if op == 'remove':
                        primary['supports'] = ['auxiliary_only']
                    elif op == 'duplicate':
                        entries.append(copy.deepcopy(primary))
                    elif op == 'wrong_source':
                        primary['source_id'] = 'unrelated_source'
                    elif op == 'bad_url':
                        primary['url'] = 'http://example.invalid/insecure'
                    else:
                        primary['locator'] = ''
                self.assert_rejected(mutate, kind + ':' + operation)

    def test_public_catalog_and_bundle_schema_accept_real_and_synthetic_silicon(self):
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
        names = ('computational_predictions', 'sources', 'prediction_comparison')
        schemas = {name: load_json(ROOT / f'schemas/{name}.schema.json') for name in names}
        registry = Registry().with_resources((schema['$id'], Resource.from_contents(schema)) for schema in schemas.values())
        for schema in schemas.values():
            Draft202012Validator.check_schema(schema)
        validators = {name: Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
                      for name, schema in schemas.items()}
        validators['computational_predictions'].validate(self.catalogs['computational_predictions'])
        validators['prediction_comparison'].validate(build_prediction_comparison(GROUP))
        candidate = synthetic_catalogs()
        validators['computational_predictions'].validate(candidate['computational_predictions'])
        read = lambda name: copy.deepcopy(candidate[name])
        with patch('materials_boundaries.predictions.read_catalog', side_effect=read), \
             patch('materials_boundaries.prediction_visualization.read_catalog', side_effect=read):
            validators['prediction_comparison'].validate(build_prediction_comparison(SYNTHETIC['group']))


class SiliconOutputTests(unittest.TestCase):
    def setUp(self):
        self.bundle = build_prediction_comparison(GROUP)

    def test_discrete_direction_strengths_and_separate_strains_without_interpolation(self):
        self.assertEqual(self.bundle, build_prediction_comparison(GROUP))
        self.assertEqual(self.bundle['schema_version'], '1.1.0')
        self.assertEqual(self.bundle['axis'], {'quantity': QUANTITY, 'unit': 'GPa', 'minimum': 0})
        self.assertEqual(self.bundle['comparison_axis'], 'loading_direction_family')
        self.assertEqual(self.bundle['display'], 'unconnected_categorical_points')
        self.assertIs(self.bundle['interpolation'], False)
        self.assertIsNone(self.bundle['uncertainty_bars'])
        self.assertIsNone(self.bundle['stress_strain_curve'])
        expected = {r['id']: r for r in FIXTURE['records']}
        self.assertEqual({point['record_id'] for point in self.bundle['points']}, set(expected))
        for point in self.bundle['points']:
            self.assertEqual(point['value_GPa'], expected[point['record_id']]['value_GPa'])
            self.assertEqual(point['direction']['display'], expected[point['record_id']]['loading_direction_display'])
            self.assertNotIn('critical_engineering_strain', point)
        strains = {item['record_id']: item for item in self.bundle['associated_critical_strains']}
        for identifier, row in expected.items():
            self.assertEqual(strains[identifier]['value'], row['engineering_strain_at_reported_strength'])
            self.assertEqual(strains[identifier]['unit'], '1')

    def test_all_four_languages_text_svg_html_and_csv_keep_scientific_caveats(self):
        rows = {row['record_id']: row for row in csv.DictReader(io.StringIO(comparison_csv(self.bundle)))}
        for expected in FIXTURE['records']:
            row = rows[expected['id']]
            self.assertEqual(row['predicted_tensile_first_instability_strength_GPa'], expected['source_value_string'])
            self.assertEqual(row['strength_source_value_string'], expected['source_value_string'])
            self.assertEqual(row['critical_engineering_strain'], str(expected['engineering_strain_at_reported_strength']))
            self.assertEqual(row['critical_engineering_strain_unit'], '1')
            self.assertEqual(row['strain_source_value_string'], expected['source_strain_value_string'])
            self.assertEqual(row['strain_source_unit'], '%')
            self.assertEqual(row['loading_direction_family'], expected['loading_direction_display'])
            self.assertEqual(row['classification'], 'published_computational_prediction')
            self.assertEqual(row['strength_definition'], 'computed_stress_at_first_detected_instability')
            self.assertEqual(row['first_instability_mode'], expected['first_instability']['mode'])
            for key in ('physical_temperature_K', 'pressure_GPa', 'magnetic_state'):
                self.assertEqual(row[key], 'not_verified')
            for key in ('uncertainty_GPa', 'critical_strain_uncertainty'):
                self.assertEqual(row[key], 'not_established')
            self.assertEqual(row['numerical_stress_error_estimate_GPa'], '0.05')
            self.assertEqual(row['numerical_stress_error_qualifier'], 'less_than_approximately')
            self.assertEqual(row['numerical_error_is_statistical_or_total_uncertainty'], 'false')
            self.assertNotIn('predicted_ideal_shear_strength_GPa', row)
        for lang in LANGUAGES:
            labels = prediction_labels(lang, family=FAMILY)
            text = render_catalog(query_catalog('predictions', source_id=SOURCE, quantity=QUANTITY), 'predictions', lang)
            html = render_prediction_html(self.bundle, lang=lang)
            html_text = ''.join(VisibleText(html).parts)
            for output in (text, html_text):
                self.assertNotIn('[missing:', output)
                for key in ('model_notice', 'comparison_notice', 'criterion_notice',
                            'unknown_notice', 'convergence_notice', 'precision_notice', 'review_notice'):
                    self.assertIn(compact(labels[key]), compact(output), lang + ':' + key)
                for expected in FIXTURE['records']:
                    self.assertIn(expected['source_value_string'], output)
                    self.assertIn(expected['source_strain_value_string'] + '%', output)
                    self.assertIn(expected['loading_direction_display'], output)
            self.assertNotIn('<script', html)
            self.assertIn('<table>', html)
            self.assertIn('@media', html)
            self.assertIn('#page=3', html)
            for width in (360, 380, 1100, 1600):
                svg = render_prediction_svg(self.bundle, lang=lang, width=width)
                root = ET.fromstring(svg)
                namespace = {'s': 'http://www.w3.org/2000/svg'}
                self.assertEqual(len(root.findall('.//s:circle', namespace)), 3)
                self.assertEqual({circle.attrib['data-record-id'] for circle in root.findall('.//s:circle', namespace)}, set(rows))
                for tag in ('path', 'polyline', 'polygon'):
                    self.assertEqual(root.findall('.//s:' + tag, namespace), [])
                svg_text = ''.join(root.itertext())
                for key in ('criterion_notice', 'convergence_notice', 'unknown_notice', 'points_notice'):
                    self.assertIn(compact(labels[key]), compact(svg_text), lang + ':' + key)
                self.assertEqual(root.attrib['width'], str(width))

    def test_search_id_source_quantity_and_each_authored_language(self):
        catalog = read_catalog('computational_predictions')
        expected_ids = {record['id'] for record in FIXTURE['records']}
        result = query_catalog('predictions', source_id=SOURCE, quantity=QUANTITY)
        self.assertEqual({record['id'] for record in result['records']}, expected_ids)
        self.assertEqual(result['protocols'], catalog['protocols'])
        self.assertEqual(result['comparison_groups'], catalog['comparison_groups'])
        for record in result['records']:
            for lang in LANGUAGES:
                match = query_catalog('predictions', record_id=record['id'], query=record['names'][lang])
                self.assertEqual(match['records'], [record])
                self.assertIn(record['names'][lang], render_catalog(match, 'predictions', lang))
                self.assertIn(record['descriptions'][lang], render_catalog(match, 'predictions', lang))
        self.assertEqual(query_catalog('predictions', source_id=SOURCE, quantity='ideal_shear_strength')['records'], [])
        self.assertEqual(query_catalog('predictions', query='nonexistent-silicon-direction')['records'], [])
        with self.assertRaises(CatalogLookupError):
            query_catalog('predictions', record_id='missing_silicon_prediction')

    def test_tampered_numbers_strains_state_geometry_evidence_and_sources_fail_all_exports(self):
        mutations = [
            lambda b: b['points'][0].update(value_GPa=31),
            lambda b: b['points'][0].update(source_value_string='27.80'),
            lambda b: b['points'][0]['direction'].update(display='[100]'),
            lambda b: b['associated_critical_strains'][0].update(value=31),
            lambda b: b['associated_critical_strains'][0].update(unit='%'),
            lambda b: b['associated_critical_strains'][0]['evidence'][0].update(url='https://example.invalid/tampered'),
            lambda b: b['record_snapshots'][0]['first_instability'].update(mode='shear'),
            lambda b: b['protocol_snapshot']['state_fields'].update(physical_temperature_K=0),
            lambda b: b['protocol_snapshot']['loading'].update(transverse_stress='zero'),
            lambda b: b['source_snapshots'][0].update(title='forged source'),
            lambda b: b.update(interpolation=True),
            lambda b: b.update(uncertainty_bars=0.05),
            lambda b: b.update(stress_strain_curve=[]),
            lambda b: b.update(classification='universal_upper_bound'),
            lambda b: b.update(unknown_conditions_equivalent=True),
            lambda b: b.update(comparison_axis='strain'),
            lambda b: b['axis'].update(quantity='ideal_shear_strength'),
            lambda b: b['associated_critical_strains'].reverse(),
            lambda b: b['record_snapshots'].pop(),
        ]
        for index, mutate in enumerate(mutations):
            candidate = copy.deepcopy(self.bundle)
            mutate(candidate)
            for function in (validate_prediction_comparison, comparison_json, comparison_csv,
                             render_prediction_svg, render_prediction_html):
                with self.subTest(mutation=index, export=function.__name__):
                    with self.assertRaises(PredictionError):
                        function(candidate)

    def test_appendability_changed_ids_values_locators_precision_and_evidence_order(self):
        catalogs = synthetic_catalogs()
        self.assertEqual(synthetic_catalogs(catalogs), catalogs)
        before = copy.deepcopy(catalogs)
        validate_prediction_catalog(catalogs['computational_predictions'], catalogs['sources'])
        validate_catalogs(catalogs)
        self.assertEqual(catalogs, before)
        read = lambda name: copy.deepcopy(catalogs[name])
        with patch('materials_boundaries.predictions.read_catalog', side_effect=read), \
             patch('materials_boundaries.prediction_visualization.read_catalog', side_effect=read):
            bundle = build_prediction_comparison(SYNTHETIC['group'])
            self.assertEqual([point['record_id'] for point in bundle['points']], [SYNTHETIC['record']])
            self.assertEqual(bundle['points'][0]['value_GPa'], 24.65)
            self.assertEqual(bundle['associated_critical_strains'][0]['value'], 0.29)
            self.assertEqual(build_prediction_comparison(), build_prediction_comparison(DEFAULT_GROUP))
            records = query_catalog('predictions', record_id=SYNTHETIC['record'])
            self.assertEqual(len(records['records']), 1)
            row = next(csv.DictReader(io.StringIO(comparison_csv(bundle))))
            self.assertEqual(row['strength_source_value_string'], '24.650')
            self.assertEqual(row['critical_engineering_strain'], '0.29')
            columns = {'strength': ('table_locator', 'value_source_url'),
                       'strain': ('strain_table_locator', 'strain_source_url'),
                       'mode': ('instability_mode_locator', 'instability_mode_source_url'),
                       'method': ('method_locator', 'method_source_url')}
            primary = {}
            for kind, (entries, support) in evidence_sets(catalogs, synthetic=True).items():
                primary[kind] = next(entry for entry in entries if support in entry['supports'])
                locator_column, url_column = columns[kind]
                self.assertEqual(row[locator_column], primary[kind]['locator'])
                self.assertEqual(row[url_column], primary[kind]['url'])
            for lang in LANGUAGES:
                text = render_catalog(records, 'predictions', lang)
                html = render_prediction_html(bundle, lang=lang)
                svg = render_prediction_svg(bundle, lang=lang)
                parsed_html = VisibleText(html)
                outputs = (text, ''.join(parsed_html.parts), ''.join(ET.fromstring(svg).itertext()))
                for output in outputs:
                    self.assertIn('24.650', output)
                    self.assertIn('29%', output)
                    for evidence in primary.values():
                        self.assertIn(compact(evidence['locator']), compact(output))
                        self.assertIn(compact(evidence['url']), compact(output))
                for evidence in primary.values():
                    self.assertIn(evidence['url'], parsed_html.links)
                self.assertNotIn('https://example.invalid/decoy', parsed_html.links)
                self.assertIn('SYNTHETIC silicon result ' + lang, text)
                self.assertEqual(query_catalog('predictions', query='SYNTHETIC silicon result ' + lang)['records'], records['records'])
            original_csv = comparison_csv(bundle)
            for entries, support in evidence_sets(catalogs, synthetic=True).values():
                entries.reverse()
            # Primary selection follows semantics even after independent metadata
            # and evidence ordering changes; canonical bundles are rebuilt.
            catalogs['computational_predictions']['records'].reverse()
            catalogs['computational_predictions']['protocols'].reverse()
            catalogs['computational_predictions']['comparison_groups'].reverse()
            catalogs['sources']['records'].reverse()
            validate_catalogs(catalogs)
            reordered = build_prediction_comparison(SYNTHETIC['group'])
            self.assertEqual(comparison_csv(reordered), original_csv)
            self.assertEqual(reordered['points'], bundle['points'])

    def test_legacy_ni_assertions_work_in_both_synthetic_append_orders(self):
        # Exercise the original Ni mutation assertions with either family last.
        # Stable IDs, not fixture position, must identify their intended target.
        import test_predictions as ni
        catalogs = synthetic_catalogs(ni.contribution_catalogs())
        for silicon_last in (False, True):
            candidate = copy.deepcopy(catalogs)
            for field, ni_id, silicon_id in (
                ('records', 'synthetic_prediction_record', SYNTHETIC['record']),
                ('protocols', 'synthetic_prediction_protocol', SYNTHETIC['protocol']),
                ('comparison_groups', 'synthetic_prediction_group', SYNTHETIC['group']),
            ):
                rows = candidate['computational_predictions'][field]
                by_identifier = {row['id']: row for row in rows}
                tail = [ni_id, silicon_id] if silicon_last else [silicon_id, ni_id]
                candidate['computational_predictions'][field] = [row for row in rows if row['id'] not in tail] + [by_identifier[rid] for rid in tail]
            validate_catalogs(candidate)
            with self.subTest(silicon_last=silicon_last), patch(
                'test_predictions.contribution_catalogs', side_effect=lambda: copy.deepcopy(candidate)
            ):
                case = ni.PredictionCatalogTests()
                case.test_source_specific_groups_reject_cross_source_or_protocol_membership()
                case.test_appended_source_locators_precision_and_evidence_order_are_live()
                visual = ni.PredictionVisualizationTests()
                visual.setUp()
                visual.test_extreme_valid_source_values_fail_plotting_with_structured_range_error()

    def test_cli_language_neutral_json_named_group_exports_and_errors(self):
        def run(*args):
            return subprocess.run([sys.executable, '-m', 'materials_boundaries', *args],
                                  cwd=ROOT, text=True, capture_output=True)
        outputs = []
        for lang in LANGUAGES:
            result = run('catalog', 'predictions', '--source-id', SOURCE, '--quantity', QUANTITY, '--json', '--lang', lang)
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append(result.stdout)
            self.assertEqual({r['id'] for r in json.loads(result.stdout)['records']}, {r['id'] for r in FIXTURE['records']})
            result = run('catalog', 'predictions', '--id', FIRST_RECORD, '--text', '--lang', lang)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('27.8', result.stdout)
            self.assertIn('31%', result.stdout)
            with tempfile.TemporaryDirectory() as tmp:
                result = run('prediction', 'plot', '--group-id', GROUP, '--output', tmp, '--lang', lang)
                self.assertEqual(result.returncode, 0, result.stderr)
                files = {p.name for p in Path(tmp).iterdir()}
                self.assertEqual(files, {'prediction-comparison.json', 'prediction-comparison.csv',
                                        f'prediction-comparison.{lang}.svg', f'prediction-comparison.narrow.{lang}.svg',
                                        f'prediction-comparison.{lang}.html'})
                self.assertEqual(load_json(Path(tmp) / 'prediction-comparison.json'), self.bundle)
                self.assertEqual((Path(tmp) / 'prediction-comparison.csv').read_text(), comparison_csv(self.bundle))
        self.assertEqual(len(set(outputs)), 1)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'must-not-exist'
            result = run('prediction', 'plot', '--group-id', 'missing_silicon_group', '--output', str(target))
            self.assertEqual(result.returncode, 2)
            self.assertFalse(target.exists())
        result = run('catalog', 'predictions', '--id', 'missing_silicon_record')
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
