"""Fictional heat-flow records; no laboratory or engineering assertions."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator, ValidationError
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA, validate_material_catalog
from materials_boundaries.material_presentation import material_labels, render_material_catalog
from test_material_reference_contract import synthetic_mean_catalog, synthetic_material_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_dielectric_breakdown_strength_contract import fixture as electric_fixture


def unit_label(code):
    return code.replace('*', '·')


def fixture(unit='mW/(m*K)', number='19.8400'):
    graph = synthetic_mean_catalog()
    prop = graph[1]['records'][0]
    prop.update(quantity='thermal_conductivity', quantity_dimension='power_per_length_temperature',
                source_property_label='Fictional plate thermal conductivity', reporting_basis='not_stated',
                summary_statistic='not_stated', uncertainty=None,
                uncertainty_status='not_reported_in_inspected_source')
    prop['reported_value'].update(number=number, value_text=number, unit_code=unit, unit_text=unit_label(unit))
    prop['uncertainty_note'] = 'No numeric dispersion; mean apparatus temperature is not a group mean.'
    prop['method_definition'].update(definition='Fictional heat-flow plate result; direction relative to foam rise and moisture unknown.', extraction_window=None)
    prop['sample_count'].update(value=None, relation='not_reported', scope='Fictional thermal measurement count unknown.', source_statement='No thermal n in fictional source.', evidence=[])
    return graph


def shape(graph):
    Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])


class ThermalConductivityContractTests(unittest.TestCase):
    def test_query_export_preserves_precision_original_units_and_unknowns(self):
        for unit in ['W/(m*K)', 'mW/(m*K)']:
            graph = fixture(unit)
            original = deepcopy(graph)
            shape(graph)
            validate_material_catalog(*graph)
            db = Database(dict(zip(('materials', 'reference_properties', 'sources'), graph)))
            records = list(db.records(quantity='thermal_conductivity'))
            self.assertEqual([row['property'] for row in records], graph[1]['records'])
            prop = records[0]['property']
            self.assertEqual(prop['reported_value']['value_text'], '19.8400')
            self.assertEqual(prop['reported_value']['unit_text'], unit_label(unit))
            self.assertIsNone(prop['uncertainty'])
            self.assertIsNone(prop['sample_count']['value'])
            self.assertEqual(prop['summary_statistic'], 'not_stated')
            self.assertEqual(prop['evaluation_support'], 'catalog_only')
            with tempfile.TemporaryDirectory() as folder:
                destination = Path(folder) / 'conductivity'
                db.export(destination, quantity='thermal_conductivity')
                self.assertEqual(read_snapshot(destination)[1], {row['record_id']: row for row in records})
            self.assertEqual(graph, original)

    def test_positive_scalar_interval_and_comparison_source_forms(self):
        values = [dict(kind='scalar', number='2.500', value_text='2.500'),
                  dict(kind='interval', lower='2.00', upper='3.00', value_text='2.00–3.00', endpoint_semantics='source_reported_not_a_confidence_interval'),
                  dict(kind='comparison', operator='>=', number='2.00', value_text='≥2.00')]
        for value in values:
            graph = fixture()
            graph[1]['records'][0]['reported_value'] = {**value, 'unit_code': 'mW/(m*K)', 'unit_text': 'mW/(m·K)'}
            shape(graph)
            validate_material_catalog(*graph)

    def test_nonpositive_centres_and_precision_rewrites_are_rejected(self):
        for number, displayed in [('0', '0'), ('-1.00', '-1.00'), ('19.8400', '19.84'), ('2.00', '2.00 approximate')]:
            graph = fixture(number=number)
            graph[1]['records'][0]['reported_value']['value_text'] = displayed
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_heat_flux_conductance_resistance_temperature_and_unreviewed_units_rejected(self):
        for unit in ['W', 'W/(m^2*K)', 'W/K', 'K/W', 'J/(kg*K)', 'degC', 'K', 'MPa', 'kV/mm', 'kW/(m*K)', 'W/(mm*K)']:
            graph = fixture(unit)
            with self.assertRaises(ValidationError):
                shape(graph)
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)
        for dimension in ['electric_field', 'pressure', 'temperature', 'mass_per_volume', 'dimensionless']:
            graph = fixture()
            graph[1]['records'][0]['quantity_dimension'] = dimension
            with self.assertRaises(ValidationError):
                shape(graph)
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_thermal_units_and_dimension_do_not_enter_legacy_or_electric_quantities(self):
        for make in [synthetic_mean_catalog, synthetic_material_catalog, electric_fixture]:
            for unit in ['W/(m*K)', 'mW/(m*K)']:
                graph = make()
                graph[1]['records'][0]['reported_value'].update(unit_code=unit, unit_text=unit_label(unit))
                with self.assertRaises(ValidationError):
                    shape(graph)
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)
            graph = make()
            graph[1]['records'][0]['quantity_dimension'] = 'power_per_length_temperature'
            with self.assertRaises(ValidationError):
                shape(graph)
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_absolute_sd_zero_allowed_but_negative_or_different_scale_rejected(self):
        graph = fixture()
        prop = graph[1]['records'][0]
        prop.update(summary_statistic='reported_mean', reporting_basis='reported_summary', uncertainty_status='reported_standard_deviation')
        prop['uncertainty'] = deepcopy(synthetic_mean_catalog()[1]['records'][0]['uncertainty'])
        prop['uncertainty'].update(number='0.00', value_text='0.00', unit_code='mW/(m*K)', unit_text='mW/(m·K)')
        shape(graph)
        validate_material_catalog(*graph)
        for unit in ['W/(m*K)', 'MPa', 'kV/mm']:
            bad = deepcopy(graph)
            bad[1]['records'][0]['uncertainty'].update(unit_code=unit, unit_text=unit_label(unit))
            with self.assertRaises(ValueError):
                validate_material_catalog(*bad)
        bad = deepcopy(graph)
        bad[1]['records'][0]['uncertainty'].update(number='-0.01', value_text='-0.01')
        with self.assertRaises(ValueError):
            validate_material_catalog(*bad)

    def test_reported_measure_envelope_preserves_unknown_estimator_and_absolute_role(self):
        graph = synthetic_reported_measures_catalog('unnamed_center_sd')
        prop = graph[1]['records'][0]
        prop.update(quantity='thermal_conductivity', quantity_dimension='power_per_length_temperature', source_property_label='Fictional heat-flow result')
        prop['reported_value'].update(unit_code='mW/(m*K)', unit_text='mW/(m·K)')
        amplitudes = [m for m in prop['uncertainty']['measures'] if m['basis'] == 'absolute' and m['availability'] == 'numeric_reported']
        self.assertTrue(amplitudes)
        for amplitude in amplitudes:
            amplitude['reported_value'].update(unit_code='mW/(m*K)', unit_text='mW/(m·K)')
        shape(graph)
        validate_material_catalog(*graph)
        self.assertEqual(prop['summary_statistic'], 'not_stated')
        bad = deepcopy(graph)
        next(m for m in bad[1]['records'][0]['uncertainty']['measures'] if m['basis'] == 'absolute' and m['availability'] == 'numeric_reported')['reported_value'].update(unit_code='W/(m*K)', unit_text='W/(m·K)')
        with self.assertRaises(ValueError):
            validate_material_catalog(*bad)

    def test_typographic_aliases_cannot_reinterpret_unit_scale_or_add_temperature_offsets(self):
        for spelling in ['mW/(m·K)', 'mW/(m*K)']:
            graph = fixture()
            graph[1]['records'][0]['reported_value']['unit_text'] = spelling
            validate_material_catalog(*graph)
        for spelling in ['W/(m·K)', 'MW/(m·K)', 'mW/(m·°C)', 'mW/mK']:
            graph = fixture()
            graph[1]['records'][0]['reported_value']['unit_text'] = spelling
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_irrelevant_descriptors_and_engineering_claims_rejected(self):
        for field, value in [('specified_elongation', {'number': '100'}), ('density_basis', 'bulk'), ('engineering_allowable', True), ('universal_bound', True)]:
            graph = fixture()
            graph[1]['records'][0][field] = value
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_four_language_render_keeps_original_middle_dot_units_and_unknown_method(self):
        graph = fixture()
        resources = dict(zip(('materials', 'reference_properties', 'sources'), graph))
        for language in ['en', 'zh', 'ja', 'de']:
            labels = material_labels(language)
            with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: deepcopy(resources[name])):
                rendered = render_material_catalog(graph[1], 'reference-properties', language)
            self.assertIn(labels['code_thermal_conductivity'] + ' [thermal_conductivity]', rendered)
            self.assertIn('19.8400', rendered)
            self.assertIn('mW/(m·K)', rendered)
            self.assertIn('direction relative to foam rise and moisture unknown', rendered)


if __name__ == '__main__':
    unittest.main()
