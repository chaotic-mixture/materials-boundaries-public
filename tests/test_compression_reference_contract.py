"""Fictional compression references exercise distinct quantities and consumers."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_presentation import material_labels, render_material_catalog
from materials_boundaries.material_references import _PROPERTIES_SCHEMA, validate_material_catalog
from test_material_uncertainty_contract import uncertainty_catalog
from test_specified_elongation_contract import fixture as target_fixture
from test_shore_a_hardness_contract import fixture as hardness_fixture
from test_break_elongation_contract import fixture as elongation_fixture


QUANTITIES = ('compressive_modulus', 'compressive_strength')


def fixture(quantity=QUANTITIES[0]):
    materials, properties, sources = uncertainty_catalog()
    prop = properties['records'][0]
    prop.update(quantity=quantity, source_property_label='Fictional ' + quantity)
    prop['reported_value'].update(number='71.25', value_text='71.25')
    prop['uncertainty'].update(number='3.50', value_text='3.50')
    prop['sample_count'].update(value=None, relation='not_reported', scope='Compression sample count unknown.',
                                source_statement='No count stated for this fictional result.', evidence=[])
    prop['method_definition'].update(definition='Fictional source compression result; extraction algorithm and window unknown.', extraction_window=None)
    prop['scope_note'] = 'Fictional source-qualified compression result; no Young-modulus conversion or engineering allowable.'
    evidence = deepcopy(prop['evidence'])
    evidence[0]['supports'].append('source_discrepancy')
    prop['source_discrepancies'] = [{'description': 'Fictional source has conflicting range wording.',
                                   'disposition': 'Preserve source values; actual evaluation window unknown.',
                                   'evidence': evidence}]
    return materials, properties, sources


class CompressionReferenceContractTests(unittest.TestCase):
    def test_quantities_query_and_export_without_relabel_or_numerical_repair(self):
        materials, properties, sources = fixture()
        second = deepcopy(properties['records'][0])
        second.update(id=second['id'] + '_strength', quantity=QUANTITIES[1])
        properties['records'].append(second)
        materials['records'][0]['property_ids'].append(second['id'])
        db = Database(dict(zip(('materials', 'reference_properties', 'sources'), (materials, properties, sources))))
        for quantity, expected in zip(QUANTITIES, properties['records']):
            self.assertEqual([r['property'] for r in db.records(quantity=quantity)], [expected])
            with tempfile.TemporaryDirectory() as temp:
                dest = Path(temp) / 'export'
                db.export(dest, quantity=quantity)
                self.assertEqual(read_snapshot(dest)[1][expected['id']]['property'], expected)
            self.assertEqual(expected['reported_value']['number'], '71.25')
            self.assertEqual(expected['uncertainty']['number'], '3.50')
        for other in ('youngs_modulus', 'tensile_modulus', 'tensile_strength', 'tensile_yield_strength',
                      'tensile_stress_at_break', 'tensile_stress_at_specified_elongation', 'shore_a_hardness'):
            self.assertEqual(list(db.records(quantity=other)), [])
        duplicate = deepcopy(second)
        duplicate['id'] += '_duplicate'
        properties['records'].append(duplicate)
        materials['records'][0]['property_ids'].append(duplicate['id'])
        with self.assertRaises(ValueError):
            validate_material_catalog(materials, properties, sources)

    def test_pressure_unit_and_descriptor_closure(self):
        for quantity in QUANTITIES:
            for unit in ('MPa', 'GPa', 'N/mm^2', 'kN/mm^2'):
                graph = fixture(quantity)
                prop = graph[1]['records'][0]
                prop['reported_value'].update(unit_text=unit, unit_code=unit)
                prop['uncertainty'].update(unit_text=unit, unit_code=unit)
                validate_material_catalog(*graph)
            for code, text in [('percent', '%'), ('percent_elongation', '%'), ('shore_a_scale', 'Shore A'), ('mm', 'mm')]:
                graph = fixture(quantity)
                graph[1]['records'][0]['reported_value'].update(unit_code=code, unit_text=text)
                with self.subTest(quantity=quantity, unit=code), self.assertRaises(ValueError):
                    validate_material_catalog(*graph)
            graph = fixture(quantity)
            graph[1]['records'][0]['quantity_dimension'] = 'dimensionless'
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)
            graph = fixture(quantity)
            graph[1]['records'][0]['specified_elongation'] = target_fixture()[1]['records'][0]['specified_elongation']
            self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_existing_pressure_positivity_and_value_shapes(self):
        for quantity in QUANTITIES:
            for number in ('0', '-1', 'NaN', 'Infinity'):
                graph = fixture(quantity)
                graph[1]['records'][0]['reported_value'].update(number=number, value_text=number)
                with self.subTest(quantity=quantity, number=number), self.assertRaises(ValueError):
                    validate_material_catalog(*graph)
            for bounds in (('1', '100'), ('0', '100'), ('-1', '100'), ('20', '20'), ('30', '20')):
                graph = fixture(quantity)
                prop = graph[1]['records'][0]
                prop.update(summary_statistic='not_stated', uncertainty=None,
                            uncertainty_status='not_reported_in_inspected_source')
                prop['reported_value'] = {'kind': 'interval', 'lower': bounds[0], 'upper': bounds[1],
                                          'value_text': ' to '.join(bounds), 'unit_code': 'MPa', 'unit_text': 'MPa',
                                          'endpoint_semantics': 'source_reported_not_a_confidence_interval'}
                if bounds == ('1', '100'):
                    validate_material_catalog(*graph)
                else:
                    with self.assertRaises(ValueError):
                        validate_material_catalog(*graph)
            graph = fixture(quantity)
            prop = graph[1]['records'][0]
            prop.update(summary_statistic='not_stated', uncertainty=None, uncertainty_status='not_reported_in_inspected_source')
            prop['reported_value'] = {'kind': 'comparison', 'operator': '>', 'number': '40', 'value_text': '>40',
                                      'unit_code': 'MPa', 'unit_text': 'MPa'}
            validate_material_catalog(*graph)

    def test_pressure_CI_and_confidence_level_keep_distinct_roles(self):
        for quantity in QUANTITIES:
            graph = fixture(quantity)
            original = deepcopy(graph)
            validate_material_catalog(*graph)
            self.assertEqual(graph, original)
            prop = graph[1]['records'][0]
            self.assertEqual(prop['summary_statistic'], 'reported_value')
            self.assertIsNone(prop['sample_count']['value'])
            self.assertIsNone(prop['method_definition']['extraction_window'])
            self.assertEqual(prop['uncertainty']['confidence_level']['unit_code'], 'percent')
            for key in ('estimand', 'construction'):
                self.assertIsNone(prop['uncertainty'][key]['text'])
            bad = deepcopy(graph)
            bad[1]['records'][0]['uncertainty'].update(unit_code='percent', unit_text='%')
            with self.assertRaises(ValueError):
                validate_material_catalog(*bad)
            bad = deepcopy(graph)
            bad[1]['records'][0]['uncertainty']['confidence_level']['unit_code'] = 'MPa'
            with self.assertRaises(ValueError):
                validate_material_catalog(*bad)

    def test_four_language_rendering_keeps_values_labels_and_unknowns(self):
        for quantity in QUANTITIES:
            graph = fixture(quantity)
            data = dict(zip(('materials', 'reference_properties', 'sources'), graph))
            for language in ('en', 'zh', 'ja', 'de'):
                with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: data[name]):
                    output = render_material_catalog(graph[1], 'reference-properties', language)
                self.assertIn(material_labels(language)['code_' + quantity], output)
                for part in ('71.25', '3.50', '95%', 'MPa', 'unknown', 'conflicting range wording'):
                    self.assertIn(part, output)

    def test_public_schema_legacy_domains_and_catalog_only_gate(self):
        stored = json.loads((Path(__file__).resolve().parents[1] / 'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(stored, _PROPERTIES_SCHEMA)
        self.assertEqual(len(stored['$defs']['property']['oneOf']), 22)
        Draft202012Validator.check_schema(stored)
        for factory in (fixture, lambda: fixture(QUANTITIES[1]), hardness_fixture, lambda: elongation_fixture('1040'), target_fixture):
            graph = factory()
            Draft202012Validator(stored).validate(graph[1])
            validate_material_catalog(*graph)
        for quantity in QUANTITIES:
            for field, value in [('engineering_allowable', True), ('universal_bound', True), ('evaluation_support', 'evaluator_input')]:
                graph = fixture(quantity)
                graph[1]['records'][0][field] = value
                self.assertFalse(Draft202012Validator(stored).is_valid(graph[1]))
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)


if __name__ == '__main__':
    unittest.main()
