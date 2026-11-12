"""Fictional TGA coordinates: never laboratory results or engineering limits."""
from copy import deepcopy
from decimal import localcontext
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator, ValidationError
from materials_boundaries.database import Database, read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA, validate_material_catalog
from materials_boundaries.material_presentation import material_labels, render_material_catalog
from test_glass_transition_temperature_contract import fixture as temperature_fixture
from test_material_uncertainty_contract import uncertainty_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog

QUANTITIES = ('thermal_degradation_onset_temperature', 'temperature_at_specified_mass_loss',
              'thermal_degradation_rate_peak_temperature', 'tga_residue_percentage')


def fixture(quantity=QUANTITIES[0], number='149.00'):
    graph = temperature_fixture(number)
    prop = graph[1]['records'][0]
    prop.update(quantity=quantity, source_property_label='Fictional TGA source endpoint')
    prop['method_definition']['definition'] = 'Fictional TGA under nitrogen; preparation and mass reference unknown.'
    evidence = deepcopy(prop['method_definition']['evidence'])
    for item in evidence:
        item['supports'] = ['condition']
    unknown = {'status': 'not_reported_in_inspected_source', 'text': None,
               'evidence': [], 'notes': 'Initial/as-received/dry mass reference unconfirmed.'}
    if quantity == 'temperature_at_specified_mass_loss':
        prop['specified_mass_loss'] = dict(kind='scalar', value_text='5.00', number='5.00',
            unit_text='%', unit_code='percent_mass_loss', evidence=evidence, notes='Source fractional loss coordinate only.')
        prop['mass_reference_basis'] = unknown
    elif quantity == 'thermal_degradation_rate_peak_temperature':
        prop['degradation_peak_ordinal'] = dict(value=1, evidence=evidence, notes='Source-labelled peak, not a fitted rank.')
    elif quantity == 'tga_residue_percentage':
        prop['quantity_dimension'] = 'dimensionless'
        prop['reported_value'].update(unit_code='percent_tga_residue', unit_text='%')
        prop['residue_endpoint_temperature'] = dict(kind='scalar', value_text='700.00', number='700.00',
            unit_text='°C', unit_code='degC', evidence=evidence, notes='Source residue endpoint, not scan start.')
        prop['mass_reference_basis'] = unknown
    return graph


def shape(graph):
    Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])


def add_clone(graph):
    prop = deepcopy(graph[1]['records'][0])
    prop['id'] += '_another'
    graph[1]['records'].append(prop)
    graph[0]['records'][0]['property_ids'].append(prop['id'])
    return prop


class TgaEndpointContractTests(unittest.TestCase):
    def test_public_schema_and_old_seven_branches_are_preserved(self):
        public = json.loads((Path(__file__).resolve().parents[1] / 'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(public, _PROPERTIES_SCHEMA)
        Draft202012Validator.check_schema(public)
        def digest(obj):
            return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(len(public['$defs']['property']['oneOf']), 22)
        original_branches=deepcopy(public['$defs']['property']['oneOf'][:7])
        for branch in original_branches:
            methods=branch['properties']['method_definition']['properties']['type']['enum']
            self.assertEqual(methods.count('source_reported_thermal_transport_product'),1)
            methods.remove('source_reported_thermal_transport_product')
            self.assertEqual(methods.count('source_reported_thermal_response_fit'),1)
            methods.remove('source_reported_thermal_response_fit')
        self.assertEqual(digest(original_branches), 'efbb98481fda44b3dff58601c05ad5150e2abcdec1b4bf1529c93a8634201aba')
        self.assertEqual(digest(public['$defs']['legacy_reported_value']), '5a77df88c82bf7828bc7ab36226e43e820fe3b4db365662e9710dfe1898a052e')

    def test_complete_query_export_preserves_each_typed_coordinate_and_unknown(self):
        for quantity in QUANTITIES:
            with self.subTest(quantity=quantity):
                graph = fixture(quantity)
                before = deepcopy(graph)
                shape(graph)
                validate_material_catalog(*graph)
                db = Database(dict(zip(('materials', 'reference_properties', 'sources'), graph)))
                rows = list(db.records(quantity=quantity))
                self.assertEqual([row['property'] for row in rows], graph[1]['records'])
                self.assertEqual(rows[0]['property']['summary_statistic'], 'not_stated')
                self.assertIsNone(rows[0]['property']['sample_count']['value'])
                with tempfile.TemporaryDirectory() as folder:
                    destination = Path(folder) / 'tga'
                    db.export(destination, quantity=quantity)
                    self.assertEqual(read_snapshot(destination)[1], {row['record_id']: row for row in rows})
                rows[0]['property']['reported_value']['number'] = '999'
                self.assertEqual(list(db.records(quantity=quantity))[0]['property'], before[1]['records'][0])
                self.assertEqual(graph, before)

    def test_temperature_result_and_endpoint_coordinate_floors(self):
        for quantity in QUANTITIES:
            for unit, text, value, valid in [('K', 'K', '0', True), ('degC', '°C', '-273.15', True),
                    ('K', 'K', '-0.01', False), ('degC', '°C', '-273.16', False)]:
                with self.subTest(quantity=quantity, unit=unit, value=value):
                    graph = fixture(quantity)
                    prop = graph[1]['records'][0]
                    target = prop['residue_endpoint_temperature'] if quantity == 'tga_residue_percentage' else prop['reported_value']
                    target.update(number=value, value_text=value, unit_code=unit, unit_text=text)
                    if valid:
                        shape(graph)
                        validate_material_catalog(*graph)
                    else:
                        with self.assertRaises(ValueError):
                            validate_material_catalog(*graph)

    def test_fractional_loss_closed_positive_domain_and_source_scale(self):
        for value in ['0', '-1', '100.0001', '101', '100', '5.00']:
            graph = fixture('temperature_at_specified_mass_loss')
            target = graph[1]['records'][0]['specified_mass_loss']
            target.update(number=value, value_text=value)
            if value in ['100', '5.00']:
                shape(graph)
                validate_material_catalog(*graph)
                self.assertEqual(target['number'], value)
            else:
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_residue_zero_intervals_and_source_ratio_without_universal_cap(self):
        for value in ['0', '13.700', '101.00']:
            graph = fixture('tga_residue_percentage', value)
            # Admission of a source ratio above100 still needs source review.
            shape(graph)
            validate_material_catalog(*graph)
            self.assertEqual(graph[1]['records'][0]['reported_value']['number'], value)
        graph = fixture('tga_residue_percentage', '-0.1')
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)
        for quantity in QUANTITIES:
            graph = fixture(quantity)
            unit = graph[1]['records'][0]['reported_value']['unit_code']
            text = '%' if unit == 'percent_tga_residue' else '°C'
            graph[1]['records'][0]['reported_value'] = dict(kind='interval', lower='0', upper='10',
                value_text='0–10', unit_code=unit, unit_text=text,
                endpoint_semantics='source_reported_not_a_confidence_interval')
            shape(graph)
            validate_material_catalog(*graph)

    def test_required_coordinates_and_cross_branch_leakage_rejected(self):
        for quantity, fields in [('temperature_at_specified_mass_loss', ['specified_mass_loss', 'mass_reference_basis']),
                ('thermal_degradation_rate_peak_temperature', ['degradation_peak_ordinal']),
                ('tga_residue_percentage', ['residue_endpoint_temperature', 'mass_reference_basis'])]:
            for field in fields:
                graph = fixture(quantity)
                del graph[1]['records'][0][field]
                with self.assertRaises(ValidationError):
                    shape(graph)
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)
        for make in [temperature_fixture, lambda: fixture(QUANTITIES[0])]:
            for field, value in fixture('tga_residue_percentage')[1]['records'][0].items():
                if field in ('residue_endpoint_temperature', 'mass_reference_basis'):
                    graph = make()
                    graph[1]['records'][0][field] = value
                    with self.assertRaises(ValueError):
                        validate_material_catalog(*graph)
        for quantity in QUANTITIES:
            for unit in ['percent_elongation', 'percent_mass_loss', 'percent', 'MPa']:
                graph = fixture(quantity)
                graph[1]['records'][0]['reported_value'].update(unit_code=unit, unit_text='%')
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_primary_descriptor_evidence_and_true_ordinal_required(self):
        for quantity, field in [('temperature_at_specified_mass_loss', 'specified_mass_loss'),
                ('thermal_degradation_rate_peak_temperature', 'degradation_peak_ordinal'),
                ('tga_residue_percentage', 'residue_endpoint_temperature')]:
            for mutation in ('empty', 'tag', 'source', 'document'):
                graph = fixture(quantity)
                target = graph[1]['records'][0][field]
                if mutation == 'empty':
                    target['evidence'] = []
                elif mutation == 'tag':
                    target['evidence'][0]['supports'] = ['reported_value']
                elif mutation == 'source':
                    target['evidence'][0]['source_id'] = 'another_source'
                else:
                    target['evidence'][0]['url'] = 'https://example.org/another-document'
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)
        for value in [0, -1, 1.5, True, '1']:
            graph = fixture('thermal_degradation_rate_peak_temperature')
            graph[1]['records'][0]['degradation_peak_ordinal']['value'] = value
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_basis_reported_needs_condition_evidence_unknown_never_not_applicable(self):
        graph = fixture('tga_residue_percentage')
        basis = graph[1]['records'][0]['mass_reference_basis']
        basis.update(status='reported', text='Fictional source initial sample mass',
                     evidence=deepcopy(graph[1]['records'][0]['residue_endpoint_temperature']['evidence']))
        validate_material_catalog(*graph)
        basis['evidence'][0]['supports'] = ['reported_value']
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)
        graph = fixture('tga_residue_percentage')
        graph[1]['records'][0]['mass_reference_basis']['status'] = 'not_applicable'
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_coordinate_scalar_shapes_and_unit_roles_do_not_leak(self):
        for quantity, field in [('temperature_at_specified_mass_loss', 'specified_mass_loss'),
                ('tga_residue_percentage', 'residue_endpoint_temperature')]:
            for invalid in [{'kind': 'comparison'}, {'unit_code': 'percent_elongation'},
                            {'unit_text': 'wt.%'}, {'kind': 'interval'}]:
                graph = fixture(quantity)
                graph[1]['records'][0][field].update(invalid)
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)
        graph = temperature_fixture()
        graph[1]['records'][0]['reported_value'].update(unit_code='percent_tga_residue', unit_text='%')
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)
        graph = uncertainty_catalog('reported_plus_minus_unspecified')
        graph[1]['records'][0]['uncertainty'].update(unit_code='percent_tga_residue', unit_text='%')
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_loss_threshold_may_precede_onset_without_source_repair(self):
        graph = fixture('temperature_at_specified_mass_loss', '139')
        onset = deepcopy(fixture('thermal_degradation_onset_temperature', '149')[1]['records'][0])
        onset['id'] += '_onset'
        graph[1]['records'].append(onset)
        graph[0]['records'][0]['property_ids'].append(onset['id'])
        validate_material_catalog(*graph)
        self.assertEqual([p['reported_value']['number'] for p in graph[1]['records']], ['139', '149'])

    def test_typed_coordinate_distinctions_and_no_format_or_unknown_note_inflation(self):
        for quantity, field, changed in [('temperature_at_specified_mass_loss', 'specified_mass_loss', '10'),
                ('thermal_degradation_rate_peak_temperature', 'degradation_peak_ordinal', 2),
                ('tga_residue_percentage', 'residue_endpoint_temperature', '600')]:
            graph = fixture(quantity)
            clone = add_clone(graph)
            if isinstance(changed, int):
                clone[field]['value'] = changed
            else:
                clone[field].update(number=changed, value_text=changed)
            validate_material_catalog(*graph)
            graph = fixture(quantity)
            clone = add_clone(graph)
            clone['source_property_label'] += ' reworded'
            clone[field]['notes'] += ' changed descriptor note'
            clone[field]['evidence'][0]['locator'] += ' changed descriptor locator'
            if field != 'degradation_peak_ordinal':
                clone[field]['number'] += '00'
                clone[field]['value_text'] += '00'
            if 'mass_reference_basis' in clone:
                clone['mass_reference_basis']['notes'] = 'Another wording for unknown basis'
            with localcontext() as context:
                context.prec = 2
                with self.assertRaisesRegex(ValueError, 'duplicate source fact'):
                    validate_material_catalog(*graph)

    def test_original_source_cell_still_distinguishes_facts_and_zero_is_canonical(self):
        graph = fixture('temperature_at_specified_mass_loss')
        clone = add_clone(graph)
        for evidence in clone['evidence']:
            if 'reported_value' in evidence['supports']:
                evidence['locator'] += ' separate original source cell'
        validate_material_catalog(*graph)
        graph = fixture('tga_residue_percentage')
        graph[1]['records'][0]['residue_endpoint_temperature'].update(number='0', value_text='0')
        clone = add_clone(graph)
        clone['residue_endpoint_temperature'].update(number='-0.00', value_text='-0.00')
        with self.assertRaisesRegex(ValueError, 'duplicate source fact'):
            validate_material_catalog(*graph)

    def test_unspecified_plus_minus_stays_unspecified_and_temperature_amplitude_is_difference(self):
        for quantity in QUANTITIES:
            graph = fixture(quantity)
            prop = graph[1]['records'][0]
            prop['uncertainty'] = deepcopy(uncertainty_catalog('reported_plus_minus_unspecified')[1]['records'][0]['uncertainty'])
            unit, text = ('percent_tga_residue', '%') if quantity == 'tga_residue_percentage' else ('K', 'K')
            prop['uncertainty'].update(number='2.00', value_text='2.00', unit_code=unit, unit_text=text)
            prop['uncertainty_status'] = 'reported_plus_minus_unspecified'
            shape(graph)
            validate_material_catalog(*graph)
            self.assertEqual(prop['summary_statistic'], 'not_stated')
            self.assertIsNone(prop['sample_count']['value'])
            prop['uncertainty'].update(unit_code='percent_elongation', unit_text='%')
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)

    def test_relative_temperature_measure_requires_origin_caveat(self):
        for quantity in QUANTITIES[:3]:
            graph = fixture(quantity)
            measure_prop = synthetic_reported_measures_catalog('cv')[1]['records'][0]
            prop = graph[1]['records'][0]
            prop.update(uncertainty=deepcopy(measure_prop['uncertainty']), uncertainty_status='reported_measures')
            prop['evidence'].extend(deepcopy(measure_prop['evidence']))
            with self.assertRaisesRegex(ValueError, 'origin caveat'):
                validate_material_catalog(*graph)
            prop['uncertainty']['measures'][0]['note'] = 'Source-relative scale only; Celsius origin makes conversion inappropriate.'
            validate_material_catalog(*graph)

    def test_four_language_render_keeps_all_typed_coordinates_evidence_and_unknowns(self):
        for quantity in QUANTITIES:
            graph = fixture(quantity)
            resources = dict(zip(('materials', 'reference_properties', 'sources'), graph))
            for language in ('en', 'zh', 'ja', 'de'):
                labels = material_labels(language)
                with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: deepcopy(resources[name])):
                    rendered = render_material_catalog(graph[1], 'reference-properties', language)
                self.assertIn(labels['code_' + quantity], rendered)
                self.assertIn(labels['tga_reference_notice'], rendered)
                prop = graph[1]['records'][0]
                for field in ('specified_mass_loss', 'degradation_peak_ordinal', 'residue_endpoint_temperature', 'mass_reference_basis'):
                    if field in prop:
                        self.assertIn(labels[field], rendered)
                        self.assertIn(prop[field]['notes'], rendered)
                self.assertIn('149.00', rendered)


if __name__ == '__main__':
    unittest.main()
