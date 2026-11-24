"""Independent v0.14 source transcription, arithmetic and append-only regressions.

Expected coefficients and values are literal source/arithmetic fixtures, never
copied from a live result. Tests select historical IDs without closing the
catalog to later reviewed contributions. Arithmetic is not physical validation.
"""
from decimal import Context, Decimal, localcontext
import json
import math
from pathlib import Path
import unittest

from materials_boundaries.catalog import read_catalog
from materials_boundaries.temperature import evaluate_temperature, get_model
from materials_boundaries.temperature_visualization import build_temperature_comparison

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures'
SOURCE = json.loads((FIXTURES / 'temperature_source_transcription_v014.json').read_text(encoding='utf-8'))
BASELINE = json.loads((FIXTURES / 'pre_temperature_expansion_v014.json').read_text(encoding='utf-8'))


def request(model_id, temperature):
    return {'schema_version': '1.0.0', 'model_id': model_id,
            'temperature': {'value': temperature, 'unit': 'K'}}


def direct_decimal(coefficients, temperature):
    # Independent power sum rather than the production evaluator's Horner path.
    with localcontext(Context(prec=80)):
        t = Decimal(str(temperature))
        return sum(Decimal(value) * t ** power
                   for power, value in enumerate(coefficients))


class TemperatureSourceTests(unittest.TestCase):
    def test_historical_scientific_model_fields_are_preserved(self):
        for original in BASELINE['catalogs']['temperature_models']:
            actual = get_model(original['id'])
            for field, expected in original.items():
                if field != 'reuse':
                    self.assertEqual(actual[field], expected, (original['id'], field))

    def test_all_new_sources_resolve_without_replacing_existing_ids(self):
        live = {record['id']: record for record in read_catalog('sources')['records']}
        old = {record['id'] for record in BASELINE['catalogs']['sources']}
        self.assertTrue(set(SOURCE['new_source_ids']).isdisjoint(old))
        for identifier in SOURCE['new_source_ids']:
            self.assertIn(identifier, live)
            self.assertIsNone(live[identifier]['license']['identifier'])
            self.assertIn('unresolved', live[identifier]['license']['status'])
        for fixture in SOURCE['models']:
            model = get_model(fixture['id'])
            self.assertIn(fixture['source_id'], model['source_ids'])
            self.assertTrue(set(model['source_ids']).issubset(live))
            self.assertIn(fixture['source_url'], live[fixture['source_id']]['urls'])

    def test_exact_independent_source_table_transcription(self):
        for fixture in SOURCE['models']:
            model = get_model(fixture['id'])
            with self.subTest(model=model['id']):
                self.assertEqual(model['equation_display'], SOURCE['equation_display'])
                self.assertEqual(model['coefficient_order'], SOURCE['coefficient_order'])
                self.assertEqual(model['coefficient_units'], SOURCE['coefficient_units'])
                self.assertEqual(model['material'], {
                    'name': fixture['material_name'], 'UNS': fixture['UNS'],
                    'temper': fixture['temper'], 'temper_status': fixture['temper_status']})
                self.assertEqual(model['original_reference']['chart'], fixture['reference_chart'])
                expected_ids = [branch['id'] for branch in fixture['branches']]
                self.assertEqual([branch['id'] for branch in model['branches']], expected_ids)
                for actual, branch in zip(model['branches'], fixture['branches']):
                    for field in ('coefficients_text', 'source_data_range_K', 'equation_range_K'):
                        self.assertEqual(actual[field], branch[field])
                    self.assertEqual(actual['endpoints'], 'inclusive')
                    self.assertEqual(Decimal(str(actual['reported_fit_error']['value'])),
                                     Decimal(branch['source_fit_error_percent_text']))

    def test_independent_decimal_spotchecks_and_both_branch_endpoints(self):
        for fixture in SOURCE['models']:
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
        for fixture in SOURCE['models']:
            branch = fixture['branches'][0]
            temperature = branch['equation_range_K'][0]
            expected = evaluate_temperature(request(fixture['id'], temperature))
            with localcontext() as context:
                context.prec = 3
                self.assertEqual(evaluate_temperature(request(fixture['id'], temperature)), expected)

    def test_each_equation_boundary_and_immediately_adjacent_float(self):
        for fixture in SOURCE['models']:
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

    def test_source_data_only_regions_never_enable_the_excluded_branch(self):
        for fixture in SOURCE['models']:
            for branch in fixture['branches']:
                for temperature in branch['source_data_only_checks_K']:
                    with self.subTest(model=fixture['id'], branch=branch['id'], T_K=temperature):
                        self.assertTrue(branch['source_data_range_K'][0] <= temperature <= branch['source_data_range_K'][1])
                        self.assertFalse(branch['equation_range_K'][0] <= temperature <= branch['equation_range_K'][1])
                        result = evaluate_temperature(request(fixture['id'], temperature))
                        self.assertNotIn(branch['id'], [p['branch_id'] for p in result['predictions']])
                        # Another branch can legitimately apply in a data-only
                        # region of this branch, e.g. 316 at 48 K or 60 K.
                        expected = [b['id'] for b in fixture['branches']
                                    if b['equation_range_K'][0] <= temperature <= b['equation_range_K'][1]]
                        self.assertEqual([p['branch_id'] for p in result['predictions']], expected)

    def test_316_overlap_retains_both_distinct_values(self):
        fixture = SOURCE['shared_endpoint']
        result = evaluate_temperature(request(fixture['model_id'], float(fixture['temperature_K'])))
        expected = {bid: float(value) for bid, value in fixture['branch_values_GPa'].items()}
        self.assertEqual(result['status'], 'ambiguous_overlap')
        self.assertEqual({p['branch_id']: p['value'] for p in result['predictions']}, expected)
        self.assertNotIn('value', result)
        self.assertIsNone(result['uncertainty_band'])
        with localcontext(Context(prec=80)):
            values = list(fixture['branch_values_GPa'].values())
            self.assertEqual(Decimal(values[0]) - Decimal(values[1]), Decimal(fixture['low_minus_high_GPa']))

    def test_nonmonotonic_curves_are_retained_without_smoothing(self):
        # These witnesses establish changes of direction, not exact extrema or
        # a physical mechanism. The 316 upper branch is not claimed nonmonotonic.
        witnesses = [('nist_al5083_o_young_temperature', [2, 20, 77], [1, -1]),
                     ('nist_invar_fe36ni_young_temperature', [3, 20, 100, 298], [1, -1, 1]),
                     ('nist_ss316_young_temperature', [8, 10, 20], [-1, 1])]
        for identifier, temperatures, signs in witnesses:
            values = [evaluate_temperature(request(identifier, t))['predictions'][0]['value']
                      for t in temperatures]
            for left, right, sign in zip(values, values[1:], signs):
                self.assertGreater(sign * (right - left), 0, identifier)

    def test_fit_error_unknowns_and_reuse_do_not_gain_false_certainty(self):
        for fixture in SOURCE['models']:
            model = get_model(fixture['id'])
            self.assertTrue(all(c['value'] is None for c in model['unknown_conditions'].values()))
            self.assertFalse(model['original_reference']['reference_chart_retrieved'])
            self.assertFalse(model['verification']['original_charts_retrieved'])
            self.assertFalse(model['verification']['independent_scientific_review'])
            self.assertIn('unverified', model['reuse']['status'])
            self.assertIn('not a permission grant, public-domain/CC0 claim', model['reuse']['status'])
            self.assertEqual(model['overlap_policy'], 'retain_all_matching_branches_without_selection_averaging_or_smoothing')
            for branch in model['branches']:
                fit = branch['reported_fit_error']
                self.assertEqual(fit['unit'], 'percent_relative_to_source_data')
                for field in ('statistic', 'confidence_level'):
                    self.assertIsNone(fit[field])
                for field in ('is_measurement_uncertainty', 'is_confidence_interval', 'is_validated_maximum_error_bound'):
                    self.assertIs(fit[field], False)
            result = evaluate_temperature(request(fixture['id'], model['branches'][0]['equation_range_K'][0]))
            self.assertEqual(result['specimen_applicability'], 'not_established')
            self.assertIsNone(result['uncertainty_band'])
        aluminum = get_model('nist_al5083_o_young_temperature')
        self.assertIn('not independently verified specimen condition', ' '.join(aluminum['scope_exclusions']))
        self.assertIn('property-page heading', aluminum['range_interpretation'])
        self.assertIn('official material index', aluminum['range_interpretation'])

    def test_default_comparison_uses_current_catalog_without_a_fixed_size(self):
        models = read_catalog('temperature_models')['records']
        bundle = build_temperature_comparison(points_per_branch=2)
        self.assertEqual([case['model_id'] for case in bundle['cases']], [model['id'] for model in models])
        self.assertTrue({model['id'] for model in SOURCE['models']}.issubset(
            {case['model_id'] for case in bundle['cases']}))
        for fixture in SOURCE['models']:
            case = next(case for case in bundle['cases'] if case['model_id'] == fixture['id'])
            self.assertEqual([series['branch_id'] for series in case['series']],
                             [branch['id'] for branch in fixture['branches']])


if __name__ == '__main__':
    unittest.main()
