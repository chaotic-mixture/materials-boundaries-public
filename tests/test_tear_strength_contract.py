"""Fictional tear results keep force/length distinct from fracture parameters."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA, validate_material_catalog
from materials_boundaries.material_presentation import material_labels, render_material_catalog
from test_material_reference_contract import synthetic_mean_catalog
from test_specified_elongation_contract import fixture as target_fixture
from test_shore_a_hardness_contract import fixture as hardness_fixture
from test_break_elongation_contract import fixture as elongation_fixture


def fixture(unit='kN/m'):
    m, p, s = synthetic_mean_catalog()
    prop = p['records'][0]
    prop.update(quantity='tear_strength', quantity_dimension='force_per_length',
                source_property_label='Fictional tear strength', summary_statistic='reported_value',
                uncertainty=None, uncertainty_status='not_reported_in_inspected_source')
    prop['reported_value'].update(number='17.25', value_text='17.25', unit_code=unit, unit_text=unit)
    prop['uncertainty_note'] = 'Graphical error bars exist; exact numeric amplitude and bar definition unknown. Null does not mean zero scatter.'
    prop['sample_count'].update(value=None, relation='not_reported', scope='Tear specimen count unknown.',
                                source_statement='Other test counts do not establish tear n.', evidence=[])
    prop['method_definition'].update(definition='Fictional source tear result; notch, force statistic and normalization algorithm unknown.', extraction_window=None)
    prop['scope_note'] = 'Source result only; no fracture-energy, stress-intensity or engineering-allowable conversion.'
    return m, p, s


class TearStrengthContractTests(unittest.TestCase):
    def test_query_export_preserves_value_and_numeric_uncertainty_unknown(self):
        graph = fixture()
        original = deepcopy(graph)
        db = Database(dict(zip(('materials', 'reference_properties', 'sources'), graph)))
        prop = graph[1]['records'][0]
        self.assertEqual([r['property'] for r in db.records(quantity='tear_strength')], [prop])
        for quantity in ('tensile_strength', 'compressive_strength', 'youngs_modulus', 'shore_a_hardness'):
            self.assertEqual(list(db.records(quantity=quantity)), [])
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'tear'
            db.export(dest, quantity='tear_strength')
            self.assertEqual(read_snapshot(dest)[1][prop['id']]['property'], prop)
        self.assertEqual(graph, original)
        self.assertIsNone(prop['uncertainty'])
        self.assertIsNone(prop['sample_count']['value'])

    def test_closed_force_per_length_units_without_automatic_conversion(self):
        for unit in ('kN/m', 'N/m', 'N/mm'):
            graph = fixture(unit)
            validate_material_catalog(*graph)
            Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])
            self.assertEqual(graph[1]['records'][0]['reported_value']['number'], '17.25')
        for unit in ('MPa', 'N', 'N*m', 'J/m^2', 'kJ/m^2', 'MPa*m^0.5', 'percent_elongation', 'shore_a_scale', 'mm'):
            graph = fixture()
            graph[1]['records'][0]['reported_value'].update(unit_code=unit, unit_text=unit)
            # Legacy branch admits registered central units structurally; the
            # scientific validator enforces quantity/dimension compatibility,
            # including registered J/m^2 and kJ/m^2 after Izod vocabulary support.
            if unit in ('N', 'N*m', 'MPa*m^0.5', 'percent_elongation', 'shore_a_scale'):
                self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
            with self.subTest(unit=unit), self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_positive_scalar_interval_and_comparison_keep_legacy_semantics(self):
        for token in ('0', '-1', 'NaN', 'Infinity'):
            graph = fixture()
            graph[1]['records'][0]['reported_value'].update(number=token, value_text=token)
            with self.subTest(token=token), self.assertRaises(ValueError):
                validate_material_catalog(*graph)
        for lower, upper in (('1', '80'), ('0', '80'), ('10', '10'), ('30', '20')):
            graph = fixture()
            prop = graph[1]['records'][0]
            prop['summary_statistic'] = 'not_stated'
            prop['reported_value'] = dict(kind='interval', lower=lower, upper=upper, value_text=lower+' to '+upper,
                                          unit_code='N/mm', unit_text='N/mm', endpoint_semantics='source_reported_not_a_confidence_interval')
            if lower == '1':
                validate_material_catalog(*graph)
            else:
                with self.assertRaises(ValueError): validate_material_catalog(*graph)
        graph = fixture()
        prop = graph[1]['records'][0]
        prop['summary_statistic'] = 'not_stated'
        prop['reported_value'] = dict(kind='comparison', operator='>', number='8', value_text='>8', unit_code='N/m', unit_text='N/m')
        validate_material_catalog(*graph)

    def test_dimension_target_and_catalog_only_flags_reject_invalid_consumption(self):
        mutations = [{'quantity_dimension': 'pressure'},
                     {'specified_elongation': target_fixture()[1]['records'][0]['specified_elongation']},
                     {'engineering_allowable': True}, {'universal_bound': True}, {'evaluation_support': 'evaluator_input'}]
        for mutation in mutations:
            graph = fixture()
            graph[1]['records'][0].update(mutation)
            if 'quantity_dimension' not in mutation:
                self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_four_languages_keep_graphical_uncertainty_caveat_and_unknowns(self):
        graph = fixture()
        data = dict(zip(('materials', 'reference_properties', 'sources'), graph))
        for language in ('en', 'zh', 'ja', 'de'):
            with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: data[name]):
                output = render_material_catalog(graph[1], 'reference-properties', language)
            self.assertIn(material_labels(language)['code_tear_strength'], output)
            for token in ('17.25', 'kN/m', 'Graphical error bars', 'notch', 'unknown'):
                self.assertIn(token, output)

    def test_public_schema_and_other_quantity_domains_remain_closed(self):
        stored = json.loads((Path(__file__).resolve().parents[1] / 'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(stored, _PROPERTIES_SCHEMA)
        self.assertEqual(len(stored['$defs']['property']['oneOf']), 22)
        Draft202012Validator.check_schema(stored)
        for factory in (synthetic_mean_catalog, hardness_fixture, lambda: elongation_fixture('1040'), target_fixture):
            graph = factory()
            validate_material_catalog(*graph)
            graph[1]['records'][0]['reported_value'].update(unit_code='kN/m', unit_text='kN/m')
            # Pressure/target fields share a structural unit enum; dedicated
            # hardness/elongation branches additionally close the shape.
            if graph[1]['records'][0]['quantity'] in ('shore_a_hardness', 'tensile_elongation_at_break'):
                self.assertFalse(Draft202012Validator(stored).is_valid(graph[1]))
            with self.assertRaises(ValueError): validate_material_catalog(*graph)


if __name__ == '__main__':
    unittest.main()
