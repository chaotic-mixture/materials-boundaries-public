"""Fictional bending-endpoint results remain distinct from tensile elongation."""
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
from test_break_elongation_contract import fixture as tensile_fixture
from test_material_reference_contract import synthetic_mean_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_specified_elongation_contract import fixture as target_fixture
from test_shore_a_hardness_contract import fixture as hardness_fixture
from test_tear_strength_contract import fixture as tear_fixture


def fixture(number='118.25'):
    m, p, s = tensile_fixture(number)
    prop = p['records'][0]
    prop.update(quantity='flexural_elongation_at_break', source_property_label='Fictional flexural elongation at break (%)',
                summary_statistic='not_stated', uncertainty=None, uncertainty_status='not_reported_in_inspected_source')
    prop['uncertainty_note'] = 'Exact aggregation, numeric dispersion and specimen count unknown; no zero-scatter claim.'
    prop['sample_count'].update(value=None, relation='not_reported', scope='Bending specimens unknown.',
                                source_statement='Other-method counts are not bending counts.', evidence=[])
    prop['method_definition'].update(definition='Fictional bending endpoint; actual deflection channel, strain convention and break criterion unknown.', extraction_window=None)
    return m, p, s


class FlexuralElongationContractTests(unittest.TestCase):
    def test_query_and_export_separate_equal_tensile_and_bending_values(self):
        graph = fixture()
        bending = graph[1]['records'][0]
        tensile = deepcopy(bending)
        tensile.update(id=tensile['id']+'_tensile', quantity='tensile_elongation_at_break')
        graph[1]['records'].append(tensile)
        graph[0]['records'][0]['property_ids'].append(tensile['id'])
        db = Database(dict(zip(('materials','reference_properties','sources'), graph)))
        self.assertEqual([r['property'] for r in db.records(quantity='flexural_elongation_at_break')], [bending])
        self.assertEqual([r['property'] for r in db.records(quantity='tensile_elongation_at_break')], [tensile])
        self.assertEqual(list(db.records(quantity='tensile_elongation_at_strength')), [])
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'bending'
            db.export(dest, quantity='flexural_elongation_at_break')
            self.assertEqual(read_snapshot(dest)[1][bending['id']]['property'], bending)
        self.assertEqual(bending['reported_value']['number'], '118.25')
        self.assertIsNone(bending['uncertainty'])

    def test_central_domain_scalar_interval_comparison_does_not_rescale(self):
        for number in ('0', '0.00', '118.25', '1000'):
            validate_material_catalog(*fixture(number))
        for number in ('-0.1', 'NaN', 'Infinity'):
            with self.subTest(number=number), self.assertRaises(ValueError):
                validate_material_catalog(*fixture(number))
        graph = fixture()
        prop = graph[1]['records'][0]
        prop['reported_value'] = dict(kind='interval', lower='0', upper='150', value_text='0 to 150',
            unit_code='percent_elongation', unit_text='%', endpoint_semantics='source_reported_not_a_confidence_interval')
        validate_material_catalog(*graph)
        prop['reported_value'] = dict(kind='comparison', operator='>', number='120', value_text='>120', unit_code='percent_elongation', unit_text='%')
        validate_material_catalog(*graph)
        graph = fixture()
        graph[1]['records'][0]['reported_value']['value_text'] = '1.1825'
        with self.assertRaises(ValueError): validate_material_catalog(*graph)

    def test_units_dimension_target_and_engine_flags_remain_closed(self):
        for code,text in [('percent','%'),('MPa','MPa'),('shore_a_scale','Shore A'),('kN/m','kN/m')]:
            graph = fixture()
            graph[1]['records'][0]['reported_value'].update(unit_code=code, unit_text=text)
            self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
            with self.assertRaises(ValueError): validate_material_catalog(*graph)
        for mutation in [{'quantity_dimension':'pressure'},
                         {'specified_elongation':target_fixture()[1]['records'][0]['specified_elongation']},
                         {'engineering_allowable':True}, {'universal_bound':True}, {'evaluation_support':'evaluator_input'}]:
            graph = fixture()
            graph[1]['records'][0].update(mutation)
            self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
            with self.assertRaises(ValueError): validate_material_catalog(*graph)

    def test_absolute_elongation_points_are_not_relative_percent(self):
        graph = tensile_fixture('118.25')
        prop = graph[1]['records'][0]
        prop['quantity'] = 'flexural_elongation_at_break'
        validate_material_catalog(*graph)
        self.assertEqual(prop['uncertainty']['unit_code'], 'percent_elongation')
        bad = deepcopy(graph)
        bad[1]['records'][0]['uncertainty']['unit_code'] = 'percent'
        with self.assertRaises(ValueError): validate_material_catalog(*bad)
        graph = synthetic_reported_measures_catalog('relative_errors')
        prop = graph[1]['records'][0]
        prop.update(quantity='flexural_elongation_at_break', quantity_dimension='dimensionless')
        prop['reported_value'].update(number='118.25', value_text='118.25', unit_code='percent_elongation', unit_text='%')
        validate_material_catalog(*graph)
        self.assertTrue(all(m['reported_value']['unit_code']=='percent' for m in prop['uncertainty']['measures']))
        prop['uncertainty']['measures'][0]['reported_value']['unit_code'] = 'percent_elongation'
        with self.assertRaises(ValueError): validate_material_catalog(*graph)

    def test_four_language_rendering_retains_percent_and_unknowns(self):
        graph = fixture()
        data = dict(zip(('materials','reference_properties','sources'), graph))
        for language in ('en','zh','ja','de'):
            with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name:data[name]):
                output = render_material_catalog(graph[1], 'reference-properties', language)
            for token in (material_labels(language)['code_flexural_elongation_at_break'], '118.25', '%', 'deflection channel', 'break criterion unknown'):
                self.assertIn(token, output)

    def test_generated_schema_and_existing_quantity_domains_unchanged(self):
        schema = json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(schema, _PROPERTIES_SCHEMA)
        self.assertEqual(len(schema['$defs']['property']['oneOf']), 22)
        Draft202012Validator.check_schema(schema)
        for factory in (synthetic_mean_catalog, tensile_fixture, target_fixture, hardness_fixture, tear_fixture):
            graph = factory()
            Draft202012Validator(schema).validate(graph[1])
            validate_material_catalog(*graph)
        for factory in (synthetic_mean_catalog, tear_fixture):
            graph = factory()
            graph[1]['records'][0]['reported_value'].update(number='0', value_text='0')
            with self.assertRaises(ValueError): validate_material_catalog(*graph)
        validate_material_catalog(*hardness_fixture('0'))
        with self.assertRaises(ValueError): validate_material_catalog(*hardness_fixture('100.01'))


if __name__=='__main__': unittest.main()
