"""Fracture definitions remain typed, sourced and separate from execution."""
import copy
import json
import math
import subprocess
import sys
import unittest
from unittest.mock import patch

from materials_boundaries import __version__, evaluate, load_json
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate
from catalog_fixtures import expected_evidence, expected_provenance
from test_engine import ROOT, example
from catalog_fixtures import (EXECUTABLE_IDS, GRIFFITH_IDS, historical_records,
                              select_records, isolated_catalogs, evidence_for)

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

MODEL_IDS = ['griffith_central_crack_plane_stress', 'griffith_central_crack_plane_strain']
EMPTY_DEPENDENCY_FAMILIES = {
    'griffith_central_crack_plane_stress_model_v1', 'griffith_central_crack_plane_strain_model_v1',
    'frenkel_slip_specific_ideal_shear_v1', 'uber_normal_cohesive_strength_v1',
    'lefm_central_crack_mode_i_stress_intensity_v1', 'lefm_mode_i_energy_release_relation_v1',
    'lefm_center_crack_finite_width_secant_factor_v1', 'general_stiffness_positive_definite_v1',
    'cubic_born_stability_v1', 'hexagonal_born_stability_v1', 'orthorhombic_born_stability_v1',
    'tetragonal_i_born_stability_v1', 'tetragonal_ii_born_stability_v1',
    'rhombohedral_i_born_stability_v1', 'rhombohedral_ii_born_stability_v1',
    'paris_erdogan_intermediate_growth_v1', 'forman_terminal_acceleration_growth_v1',
    'zener_cubic_elastic_anisotropy_index_v1', 'universal_elastic_anisotropy_index_v1',
    'directional_poissons_ratio_definition_and_range_v1',
    'directional_linear_compressibility_hydrostatic_relation_v1',
    'isotropic_bulk_plane_wave_speeds_and_ratio_v1',
    'christoffel_tensor_strong_ellipticity_v1',
    'scalar_viscoelastic_creep_relaxation_duality_v1',
    'von_mises_initial_yield_relation_v1', 'tresca_initial_yield_relation_v1',
}


def records(**filters):
    return query_catalog('claims', **filters)['records']


class FractureCatalogTests(unittest.TestCase):
    def test_classification_and_legacy_bound_kind_are_explicit(self):
        # Classifications are open-ended; only the runtime allowlist is closed.
        by_id = {record['id']: record for record in records()}
        for record in records():
            if record['claim_type'] in ('model_estimate', 'model_relation', 'stability_criterion'):
                self.assertIsNone(record['bound_kind'])
                self.assertEqual(record['evaluation_support'], 'catalog_only')
                self.assertEqual(record['direction'], {'model_estimate':'prediction', 'model_relation':'relation', 'stability_criterion':'constraint'}[record['claim_type']])
                # Dependencies are pinned by scientific family, never by catalog
                # position or a blanket assumption that all relations are alike.
                if record['rule_id'] == 'normalized_directional_compressibility_range_v1':
                    self.assertEqual(len(record['dependencies']), 1)
                    definition = by_id[record['dependencies'][0]]
                    self.assertEqual(definition['rule_id'], 'directional_linear_compressibility_hydrostatic_relation_v1')
                elif record['rule_id'] == 'directional_poisson_reciprocity_energy_constraint_v1':
                    self.assertEqual(len(record['dependencies']), 1)
                    definition = by_id[record['dependencies'][0]]
                    self.assertEqual(definition['rule_id'], 'directional_poissons_ratio_definition_and_range_v1')
                else:
                    self.assertIn(record['rule_id'], EMPTY_DEPENDENCY_FAMILIES)
                    self.assertEqual(record['dependencies'], [])
            elif record['rule_id'] == 'scalar_viscoelastic_creep_relaxation_product_bound_v1':
                self.assertEqual(record['claim_type'], 'theoretical_bound')
                self.assertEqual(record['direction'], 'interval')
                self.assertEqual(record['bound_kind'], 'dimensionless_response_product_bound')
                self.assertEqual(record['evaluation_support'], 'catalog_only')
                self.assertEqual(len(record['dependencies']), 1)
                self.assertEqual(by_id[record['dependencies'][0]]['rule_id'],
                                 'scalar_viscoelastic_creep_relaxation_duality_v1')
            elif record['rule_id'] == 'tresca_von_mises_equivalent_stress_ratio_bound_v1':
                self.assertEqual(record['claim_type'], 'theoretical_bound')
                self.assertEqual(record['direction'], 'interval')
                self.assertEqual(record['bound_kind'], 'criterion_function_comparison')
                self.assertEqual(record['evaluation_support'], 'catalog_only')
                self.assertEqual(len(record['dependencies']), 2)
                self.assertEqual({by_id[dependency]['rule_id'] for dependency in record['dependencies']},
                                 {'von_mises_initial_yield_relation_v1', 'tresca_initial_yield_relation_v1'})
            else:
                self.assertEqual(record['evaluation_support'], 'composite_evaluate' if record['id'] in EXECUTABLE_IDS else 'catalog_only')
                self.assertEqual(record['bound_kind'], 'scalar_modulus_bound' if record['claim_type'] == 'theoretical_bound' else record['claim_type'])

    def test_dimensions_are_explicit_and_not_all_pressure(self):
        for record in historical_records('claims', EXECUTABLE_IDS + GRIFFITH_IDS):
            dimensionless = record['quantity'] == 'effective_poissons_ratio'
            self.assertEqual(record['quantity_dimension'], 'dimensionless' if dimensionless else 'pressure')
            self.assertEqual(record['si_unit'], '1' if dimensionless else 'Pa')
        for record in historical_records('claims', MODEL_IDS):
            self.assertEqual(record['quantity'], 'critical_remote_tensile_stress')
            parameters = {p['symbol']: p for p in record['parameters']}
            self.assertEqual((parameters['a']['quantity'], parameters['a']['si_unit']), ('crack_half_length', 'm'))
            self.assertEqual((parameters['Gc']['dimension'], parameters['Gc']['si_unit']), ('energy_per_area', 'J/m^2'))
            self.assertEqual(parameters['E']['si_unit'], 'Pa')

    def test_geometry_plane_state_and_no_default_surface_energy(self):
        for record, plane in zip(historical_records('claims', MODEL_IDS), ['plane_stress', 'plane_strain']):
            assumptions = record['required_assumptions']
            self.assertEqual(assumptions['plane_state'], plane)
            self.assertEqual(assumptions['geometry'], 'infinite_plate_central_through_crack')
            self.assertEqual(assumptions['crack_length_convention'], 'a_is_half_total_length_2a')
            self.assertEqual(assumptions['crack_mode'], 'mode_I')
            self.assertEqual(assumptions['fracture_criterion'], 'G_reaches_supplied_positive_Gc')
            self.assertIn('only in the ideal surface-creation-only', record['formula_display'])
            self.assertEqual([x['symbol'] for x in record['parameters']], ['E', 'Gc', 'a'] + (['nu'] if plane == 'plane_strain' else []))
            self.assertNotIn('gamma', [x['symbol'] for x in record['parameters']])
            self.assertTrue(any('Unknown or violated' in x for x in record['limits']))
            self.assertTrue(any('a->0' in x for x in record['limits']))
            self.assertTrue(any('not a universal tensile-strength upper bound' in x for x in record['limits']))

    @isolated_catalogs()
    def test_model_query_and_bound_queries_do_not_mix(self):
        ids = lambda value: [r['id'] for r in value]
        self.assertEqual(ids(records(claim_type='model_estimate', source_id='wilson_1992_nasa_tm_103591')), MODEL_IDS)
        self.assertEqual(ids(records(direction='prediction', source_id='wilson_1992_nasa_tm_103591')), MODEL_IDS)
        self.assertEqual(ids(records(query='GRIFFITH MODEL_ESTIMATE plane_strain')), MODEL_IDS[1:])
        self.assertEqual(ids(records(claim_type='model_estimate', source_id='wilson_1992_nasa_tm_103591')), MODEL_IDS)
        self.assertEqual(ids(records(claim_type='model_estimate', direction='upper')), [])
        self.assertEqual(ids(records(record_id=MODEL_IDS[0], claim_type='theoretical_bound')), [])
        self.assertTrue(all(r['claim_type'] != 'model_estimate' for r in records(direction='upper')))

    def test_invalid_classification_filters_and_cross_kind_fail(self):
        for value in ('MODEL_ESTIMATE', 'model', '', ' ', [], True, 12):
            with self.subTest(value=value), self.assertRaises(ValueError):
                query_catalog('claims', claim_type=value)
        with self.assertRaises(ValueError):
            query_catalog('sources', claim_type='model_estimate')

    def test_historical_attribution_separate_from_modern_equation_verification(self):
        source_map = {s['id']: s for s in read_catalog('sources')['records']}
        for record in historical_records('claims', MODEL_IDS):
            evidence = {source_id: evidence_for(record, source_id) for source_id in
                        ('wilson_1992_nasa_tm_103591', 'griffith_1921')}
            self.assertEqual(evidence['wilson_1992_nasa_tm_103591']['verification_status'], expected_evidence('claims', record['id'], 'wilson_1992_nasa_tm_103591')['verification_status'])
            self.assertEqual(evidence['griffith_1921']['verification_status'], expected_evidence('claims', record['id'], 'griffith_1921')['verification_status'])
            self.assertIn('p. 198', evidence['griffith_1921']['locator'])
            self.assertEqual(record['verification']['independent_scientific_review'], expected_provenance('claims', record['id'])['verification']['independent_scientific_review'])
            self.assertEqual(record['verification']['status'], expected_provenance('claims', record['id'])['verification']['status'])
        self.assertEqual(source_map['griffith_1921']['role'], 'historical_primary_source')
        self.assertEqual(source_map['wilson_1992_nasa_tm_103591']['role'], 'modern_lefm_equation_source')
        self.assertEqual(source_map['wilson_1992_nasa_tm_103591']['read_status'], expected_provenance('sources', source_map['wilson_1992_nasa_tm_103591']['id'])['read_status'])
        self.assertEqual(source_map['wilson_1992_nasa_tm_103591']['license'], expected_provenance('sources', source_map['wilson_1992_nasa_tm_103591']['id'])['license'])

    def test_existing_evaluator_stays_eight_and_never_dispatches_catalog_models(self):
        result = evaluate(example())
        self.assertEqual(result['schema_version'], '1.1.0')
        self.assertEqual(result['engine_version'], __version__)
        self.assertEqual(len(result['evaluations']), 8)
        self.assertTrue(set(MODEL_IDS).isdisjoint(e['claim_id'] for e in result['evaluations']))
        self.assertEqual([e['claim_id'] for e in result['evaluations']], list(EXECUTABLE_IDS))
        self.assertCountEqual([r['id'] for r in records() if r['evaluation_support'] == 'composite_evaluate'],
                              EXECUTABLE_IDS)
        with patch('materials_boundaries.catalog.read_catalog', side_effect=AssertionError('catalog dispatch is prohibited')):
            self.assertEqual(evaluate(example()), result)

    def test_no_model_numerical_or_applicability_state_in_catalog(self):
        for record in historical_records('claims', MODEL_IDS):
            for forbidden in ('result', 'applicability', 'computation', 'checks', 'value'):
                self.assertNotIn(forbidden, record)
            self.assertTrue(any('No executable fracture calculator' in x for x in record['verification']['gaps']))

    def test_four_language_model_warning_and_metadata(self):
        result = query_catalog('claims', claim_type='model_estimate', source_id='wilson_1992_nasa_tm_103591')
        for lang in LANGUAGES:
            text = render_catalog(result, 'claims', lang)
            for key in ('catalog_model_notice', 'catalog_status_model_estimate', 'catalog_status_catalog_only',
                        'catalog_claim_type', 'catalog_quantity_dimension', 'catalog_parameters', 'catalog_not_applicable'):
                self.assertIn(translate(key, lang), text)
            self.assertNotIn('[missing:', text)
            self.assertIn('Gc', text)
            self.assertIn('2a', text)
            self.assertIn('prediction', text)
            self.assertIn('wilson_1992_nasa_tm_103591', text)

    def test_documented_synthetic_arithmetic_and_half_length_sensitivity(self):
        # Independent arithmetic fixture, not a runtime fracture-model API.
        e, gc, a, nu = 70e9, 2.0, 0.001, 0.22
        stress = math.sqrt(e * gc / (math.pi * a))
        strain = math.sqrt(e * gc / ((1 - nu**2) * math.pi * a))
        self.assertAlmostEqual(stress / 1e6, 6.675581178124545, places=12)
        self.assertAlmostEqual(strain / 1e6, 6.843241471054398, places=12)
        self.assertAlmostEqual(strain / stress, 1 / math.sqrt(1 - nu**2), places=14)
        self.assertAlmostEqual(math.sqrt(e * gc / (math.pi * (2*a))) / stress, 1 / math.sqrt(2), places=14)


class FractureCatalogCLITests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'materials_boundaries', *args], cwd=ROOT, text=True, capture_output=True)

    def test_model_filter_json_canonical_in_four_languages(self):
        outputs = []
        for lang in LANGUAGES:
            result = self.run_cli('catalog', 'claims', '--claim-type', 'model_estimate', '--direction', 'prediction', '--source-id', 'wilson_1992_nasa_tm_103591', '--lang', lang)
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append(result.stdout)
            matched = json.loads(result.stdout)['records']
            self.assertEqual([r['id'] for r in select_records({'records': matched}, MODEL_IDS)], MODEL_IDS)
            self.assertTrue(all(r['claim_type'] == 'model_estimate' and r['direction'] == 'prediction' for r in matched))
        self.assertEqual(len(set(outputs)), 1)

    def test_filters_and_help_are_localized(self):
        for lang in LANGUAGES:
            result = self.run_cli('catalog', '--help', '--lang', lang)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--claim-type', result.stdout)
            self.assertIn('model_estimate', result.stdout)
            self.assertIn(translate('cli_claim_type', lang), result.stdout)

    def test_invalid_filters_and_no_fracture_evaluator_command(self):
        for args in [('catalog', 'claims', '--claim-type', 'strength_bound'),
                     ('catalog', 'sources', '--claim-type', 'model_estimate'),
                     ('model', 'griffith_central_crack_plane_stress'),
                     ('evaluate', 'examples/synthetic-two-phase.json', '--model', MODEL_IDS[0])]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')


@unittest.skipIf(Draft202012Validator is None, 'optional jsonschema dev dependency not installed')
class FractureCatalogSchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalog = read_catalog('claims')
        self.validator = Draft202012Validator(load_json(ROOT / 'schemas/claims.schema.json'))

    def assert_invalid_record(self, mutation, record_id=MODEL_IDS[1]):
        bad = copy.deepcopy(self.catalog)
        record = select_records(bad, [record_id])[0]
        mutation(record)
        self.assertTrue(list(self.validator.iter_errors(bad)), record)

    def test_13_schema_validates_new_catalog_but_rejects_old_envelope(self):
        self.validator.validate(self.catalog)
        old = copy.deepcopy(self.catalog); old['schema_version'] = '1.1.0'
        self.assertTrue(list(self.validator.iter_errors(old)))

    def test_model_cannot_be_mistyped_as_bound_or_executable(self):
        for key, value in [('claim_type', 'theoretical_bound'), ('direction', 'upper'),
                           ('bound_kind', 'scalar_modulus_bound'), ('evaluation_support', 'composite_evaluate'),
                           ('dependencies', ['hs_bulk_3d_two_phase']), ('quantity', 'effective_bulk_modulus')]:
            with self.subTest(key=key):
                self.assert_invalid_record(lambda r: r.update({key: value}))

    def test_quantities_cannot_use_wrong_dimension_or_si_unit(self):
        for record_id in ('hs_bulk_3d_two_phase', 'poissons_ratio_outer', *MODEL_IDS):
            for key, value in [('quantity_dimension', 'length'), ('si_unit', 'm')]:
                self.assert_invalid_record(lambda r: r.update({key: value}), record_id)
        self.assert_invalid_record(lambda r: r.update(quantity_dimension='pressure', si_unit='Pa'), 'poissons_ratio_outer')
        self.assert_invalid_record(lambda r: r.update(quantity_dimension='dimensionless', si_unit='1'), MODEL_IDS[0])

    def test_model_parameter_shape_and_plane_state_are_checked(self):
        self.assert_invalid_record(lambda r: r.pop('parameters'))
        self.assert_invalid_record(lambda r: r['parameters'].pop())
        self.assert_invalid_record(lambda r: r['parameters'][0].update(symbol='Gc'))
        self.assert_invalid_record(lambda r: r['parameters'][1].update(si_unit='Pa'))
        self.assert_invalid_record(lambda r: r['parameters'][2].update(quantity='full_crack_length'))
        self.assert_invalid_record(lambda r: r['required_assumptions'].update(plane_state='unknown'))
        self.assert_invalid_record(lambda r: r['required_assumptions'].pop('plane_state'))
        self.assert_invalid_record(lambda r: r['parameters'].append(copy.deepcopy(r['parameters'][0])), MODEL_IDS[0])
        self.assert_invalid_record(lambda r: r.update(parameters=copy.deepcopy(select_records(self.catalog, [MODEL_IDS[1]])[0]['parameters'])), 'hs_bulk_3d_two_phase')

    def test_classification_metadata_required_and_no_computed_states(self):
        for key in ('claim_type', 'quantity_dimension', 'si_unit', 'evaluation_support'):
            self.assert_invalid_record(lambda r: r.pop(key))
        for key, value in [('applicability', 'satisfied'), ('result', {'value': 123, 'unit': 'Pa'}), ('computation', 'computed')]:
            self.assert_invalid_record(lambda r: r.update({key: value}))


if __name__ == '__main__':
    unittest.main()
