"""Independent synthetic construction, arithmetic and append-only regressions.

Literal construction fixtures define authored demonstrations. The independent
power-sum oracle does not call the production Horner evaluator, and is never
presented as measurement, material evidence or scientific validation.
"""
from decimal import Context, Decimal, localcontext
import copy
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from materials_boundaries.catalog import read_catalog
from materials_boundaries.temperature import evaluate_temperature, get_model
from materials_boundaries.temperature_visualization import build_temperature_comparison

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures'
CONSTRUCTION = json.loads((FIXTURES / 'temperature_synthetic_construction.json').read_text(encoding='utf-8'))
BASELINE = json.loads((FIXTURES / 'temperature_synthetic_baseline.json').read_text(encoding='utf-8'))


def request(model_id, temperature):
    return {'schema_version': '1.0.0', 'model_id': model_id,
            'temperature': {'value': temperature, 'unit': 'K'}}


def direct_decimal(coefficients, temperature):
    # Independent power sum rather than the production evaluator's Horner path.
    with localcontext(Context(prec=80)):
        t = Decimal(str(temperature))
        return sum(Decimal(value) * t ** power
                   for power, value in enumerate(coefficients))


class TemperatureConstructionTests(unittest.TestCase):
    def assert_subset(self, actual, expected):
        if isinstance(expected, dict):
            for key, value in expected.items():
                self.assertIn(key, actual)
                self.assert_subset(actual[key], value)
        elif isinstance(expected, list):
            self.assertEqual(len(actual), len(expected))
            for item, value in zip(actual, expected):
                self.assert_subset(item, value)
        else:
            self.assertEqual(actual, expected)

    def test_public_synthetic_baseline_is_preserved_by_id_not_catalog_size(self):
        models = {record['id']: record for record in read_catalog('temperature_models')['records']}
        for original in BASELINE['models']:
            with self.subTest(model=original['id']):
                self.assert_subset(models[original['id']], original)

    def test_original_author_source_resolves_for_every_demonstration(self):
        live = {record['id']: record for record in read_catalog('sources')['records']}
        self.assertIn(CONSTRUCTION['source_id'], live)
        source = live[CONSTRUCTION['source_id']]
        self.assertTrue(source['urls'])
        self.assertIn('synthetic', source['title'].lower())
        for fixture in CONSTRUCTION['models']:
            model = get_model(fixture['id'])
            self.assertEqual(model['source_ids'], [CONSTRUCTION['source_id']])
            self.assertTrue(set(model['source_ids']).issubset(live))

    def test_exact_independent_construction_digits_and_artificial_intervals(self):
        for fixture in CONSTRUCTION['models']:
            model = get_model(fixture['id'])
            with self.subTest(model=model['id']):
                self.assertEqual(model['equation_display'], CONSTRUCTION['equation_display'])
                self.assertEqual(model['coefficient_order'], CONSTRUCTION['coefficient_order'])
                self.assertEqual(model['coefficient_units'], CONSTRUCTION['coefficient_units'])
                self.assertEqual(model['classification'], 'synthetic_demo')
                self.assertEqual(model['material']['identity_status'], 'synthetic_demo')
                self.assertIsNone(model['material']['UNS'])
                self.assertIsNone(model['material']['temper'])
                self.assertEqual([branch['id'] for branch in model['branches']],
                                 [branch['id'] for branch in fixture['branches']])
                for actual, branch in zip(model['branches'], fixture['branches']):
                    for field in ('coefficients_text', 'equation_range_K'):
                        self.assertEqual(actual[field], branch[field])
                    self.assertEqual(actual['endpoints'], 'inclusive')
                    self.assertEqual(actual['range_status'], 'artificial_demonstration_interval')
                    self.assertIsNone(actual['source_data_range_K'])

    def test_independent_decimal_spotchecks_and_both_branch_endpoints(self):
        for fixture in CONSTRUCTION['models']:
            for branch in fixture['branches']:
                checked = {Decimal(t) for t, _ in branch['arithmetic_checks']}
                self.assertTrue(set(map(Decimal, branch['equation_range_K'])).issubset(checked))
                for temperature, expected in branch['arithmetic_checks']:
                    with self.subTest(model=fixture['id'], branch=branch['id'], T_K=temperature):
                        direct = direct_decimal(branch['coefficients_text'], temperature)
                        self.assertEqual(direct, Decimal(expected))
                        result = evaluate_temperature(request(fixture['id'], float(temperature)))
                        actual = next(p for p in result['predictions'] if p['branch_id'] == branch['id'])
                        self.assertEqual(actual['value'], float(direct))
                        self.assertEqual(actual['unit'], 'GPa')

    def test_arithmetic_is_independent_of_ambient_decimal_context(self):
        for fixture in CONSTRUCTION['models']:
            for branch in fixture['branches']:
                temperature = branch['equation_range_K'][0]
                expected = evaluate_temperature(request(fixture['id'], temperature))
                with localcontext() as context:
                    context.prec = 3
                    self.assertEqual(evaluate_temperature(request(fixture['id'], temperature)), expected)

    def test_each_artificial_boundary_and_immediately_adjacent_float(self):
        for fixture in CONSTRUCTION['models']:
            boundaries = {t for branch in fixture['branches'] for t in branch['equation_range_K']}
            for boundary in boundaries:
                for temperature in (math.nextafter(boundary, -math.inf), boundary,
                                    math.nextafter(boundary, math.inf)):
                    expected_ids = [branch['id'] for branch in fixture['branches']
                                    if branch['equation_range_K'][0] <= temperature <= branch['equation_range_K'][1]]
                    with self.subTest(model=fixture['id'], T_K=temperature):
                        result = evaluate_temperature(request(fixture['id'], temperature))
                        self.assertEqual([p['branch_id'] for p in result['predictions']], expected_ids)
                        status = ('ambiguous_overlap' if len(expected_ids) > 1 else
                                  'prediction' if expected_ids else 'out_of_range')
                        self.assertEqual(result['status'], status)

    def test_exclusion_fixture_never_extrapolates_any_model(self):
        fixture = json.loads((FIXTURES/'temperature_arithmetic.json').read_text())
        for row in fixture['out_of_range_exclusion_checks']:
            result = evaluate_temperature(request(row['model_id'], float(row['T_K'])))
            self.assertEqual(result['status'], row['expected_status'])
            self.assertEqual(result['predictions'], [])

    def test_shared_endpoint_retains_both_distinct_values(self):
        fixture = CONSTRUCTION['shared_endpoint']
        result = evaluate_temperature(request(fixture['model_id'], float(fixture['temperature_K'])))
        expected = {bid: float(value) for bid, value in fixture['branch_values_GPa'].items()}
        self.assertEqual(result['status'], 'ambiguous_overlap')
        self.assertEqual({p['branch_id']: p['value'] for p in result['predictions']}, expected)
        self.assertNotIn('value', result)
        self.assertIsNone(result['uncertainty_band'])
        values = list(fixture['branch_values_GPa'].values())
        self.assertEqual(Decimal(values[1])-Decimal(values[0]), Decimal(fixture['high_minus_low_GPa']))

    def test_shared_interval_retains_both_branches_throughout_and_at_endpoints(self):
        fixture = CONSTRUCTION['shared_interval']
        for temperature in (60, 60.0001, 70, 79.9999, 80):
            result = evaluate_temperature(request(fixture['model_id'], temperature))
            self.assertEqual(result['status'], 'ambiguous_overlap')
            self.assertEqual([p['branch_id'] for p in result['predictions']], list(fixture['branch_values_GPa']))
            self.assertNotIn('value', result)
        result = evaluate_temperature(request(fixture['model_id'], float(fixture['temperature_K'])))
        self.assertEqual({p['branch_id']:p['value'] for p in result['predictions']},
                         {bid:float(value) for bid,value in fixture['branch_values_GPa'].items()})

    def test_nonmonotonic_quadratic_is_retained_without_smoothing(self):
        identifier = 'synthetic_quadratic_temperature'
        values = [evaluate_temperature(request(identifier,t))['predictions'][0]['value'] for t in (25,50,75)]
        self.assertEqual(values, [38.125,37.5,38.125])
        series = build_temperature_comparison([identifier],points_per_branch=5)['cases'][0]['series'][0]
        self.assertEqual([p['value_GPa'] for p in series['points'][:3]], values)

    def test_synthetic_provenance_does_not_gain_empirical_certainty(self):
        for fixture in CONSTRUCTION['models']:
            model = get_model(fixture['id'])
            self.assertTrue(all(c['value'] is None for c in model['unknown_conditions'].values()))
            self.assertFalse(model['author_provenance']['is_empirical'])
            self.assertFalse(model['author_provenance']['derived_from_measurements'])
            self.assertFalse(model['verification']['empirical_validation'])
            self.assertFalse(model['verification']['independent_scientific_review'])
            self.assertNotIn('original_reference',model)
            self.assertEqual(model['overlap_policy'], 'retain_all_matching_branches_without_selection_averaging_or_smoothing')
            for branch in model['branches']:
                fit = branch['reported_fit_error']
                for field in ('value','unit','statistic','confidence_level'):
                    self.assertIsNone(fit[field])
                self.assertEqual(fit['status'],'not_applicable_synthetic_demo')
                for field in ('is_measurement_uncertainty','is_confidence_interval','is_validated_maximum_error_bound'):
                    self.assertIs(fit[field], False)
            result = evaluate_temperature(request(fixture['id'],model['branches'][0]['equation_range_K'][0]))
            self.assertEqual(result['specimen_applicability'],'not_applicable_synthetic_demo')
            self.assertIsNone(result['uncertainty_band'])

    def test_default_comparison_uses_current_catalog_without_a_fixed_size(self):
        models = read_catalog('temperature_models')['records']
        bundle = build_temperature_comparison(points_per_branch=2)
        self.assertEqual([case['model_id'] for case in bundle['cases']],[model['id'] for model in models])
        self.assertEqual(bundle['classification'],'synthetic_demo')
        self.assertTrue({model['id'] for model in CONSTRUCTION['models']}.issubset(
            {case['model_id'] for case in bundle['cases']}))
        for fixture in CONSTRUCTION['models']:
            case = next(case for case in bundle['cases'] if case['model_id']==fixture['id'])
            self.assertEqual([series['branch_id'] for series in case['series']],
                             [branch['id'] for branch in fixture['branches']])

    def test_baseline_allows_an_independently_authored_appended_model(self):
        catalogs = {name:read_catalog(name) for name in ('temperature_models','sources')}
        appended = copy.deepcopy(catalogs['temperature_models']['records'][0])
        appended['id']='synthetic_construction_append'
        appended['branches'][0]['id']='synthetic_construction_append_branch'
        appended['branches'][0]['coefficients_text']=['3','0','0','0','0']
        catalogs['temperature_models']['records'].append(appended)
        with patch('materials_boundaries.temperature.read_catalog',side_effect=lambda name:copy.deepcopy(catalogs[name])):
            result=evaluate_temperature(request(appended['id'],50))
            self.assertEqual(result['predictions'][0]['value'],3)
        self.test_public_synthetic_baseline_is_preserved_by_id_not_catalog_size()


if __name__=='__main__':
    unittest.main()
