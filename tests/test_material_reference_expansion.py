"""Generic compilation/derived-method contracts plus source-preserving typography.

Synthetic fixtures test capability without becoming production coverage. Source
truth still requires independent readback; the runtime validates the declared
provenance graph rather than interpreting arbitrary bibliographic prose.
"""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from materials_boundaries.material_references import (
    _PROPERTIES_SCHEMA, _numeric_token_matches, validate_material_catalog,
)
from test_material_reference_contract import synthetic_material_catalog

ROOT = Path(__file__).resolve().parents[1]


def compilation_catalog():
    graph = synthetic_material_catalog()
    prop = graph[1]['records'][0]
    prop.update(evidence_kind='published_handbook_reference',
                determination_basis='source_reports_compiled_measurements',
                reporting_basis='reported_summary', summary_statistic='reported_mean',
                quantity='flexural_modulus', quantity_dimension='pressure', density_basis=None,
                source_property_label='Synthetic bending modulus',
                basis_note='Synthetic compiled measurements, adjusted to a stated reference condition.')
    prop['reported_value'].update(value_text='12,600', number='12600', unit_text='MPa', unit_code='MPa')
    prop['evidence'][0]['supports'].append('summary_statistic')
    prop['method_definition'].update(type='source_reported_compilation',
        definition='Synthetic compilation of prior bending measurements including shear deflection; no new experiment.')
    prop['method_definition']['evidence'][0]['supports'].append('classification')
    graph[2]['records'][0]['role'] = 'published handbook reference (synthetic)'
    return graph


def crystallographic_catalog():
    graph = synthetic_material_catalog()
    prop = graph[1]['records'][0]
    prop.update(evidence_kind='published_measurement_derived_reference',
                determination_basis='source_reports_calculation', density_basis='crystallographic',
                reporting_basis='reported_summary', summary_statistic='reported_value',
                basis_note='Synthetic density derived from experimental cell dimensions and adopted atomic mass.')
    prop['reported_value'].update(unit_text='grams per cubic centimeter')
    prop['method_definition'].update(type='source_reported_crystallographic_derivation',
        definition='Synthetic measured diffraction cell dimension a, with adopted cell content Z and atomic mass M; density = Z M / (N_A a^3).')
    prop['method_definition']['evidence'][0]['supports'].append('classification')
    graph[2]['records'][0]['role'] = 'published measured-input-derived reference (synthetic)'
    return graph


class MaterialReferenceExpansionTests(unittest.TestCase):
    def assert_invalid(self, make, mutate):
        graph = make()
        mutate(*graph)
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_new_classes_are_valid_and_schema_representable(self):
        import jsonschema
        for make in (compilation_catalog, crystallographic_catalog):
            graph = make()
            before = deepcopy(graph)
            validate_material_catalog(*graph)
            jsonschema.Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])
            self.assertEqual(graph, before)

    def test_compilation_cannot_become_original_experiment(self):
        for fields in (
            {'evidence_kind': 'published_experimental_reference'},
            {'evidence_kind': 'published_experimental_reference', 'determination_basis': 'source_reports_measurement'},
            {'determination_basis': 'source_reports_measurement'},
            {'evidence_kind': 'manufacturer_reference'},
            {'evidence_kind': 'published_computational_reference', 'determination_basis': 'source_reports_calculation'},
        ):
            with self.subTest(fields=fields):
                self.assert_invalid(compilation_catalog, lambda m,p,s: p['records'][0].update(fields))
        self.assert_invalid(compilation_catalog, lambda m,p,s: p['records'][0]['method_definition'].update(type='source_reported_conventional'))

    def test_measured_derived_cannot_be_direct_or_computational_measurement(self):
        for fields in (
            {'evidence_kind': 'published_experimental_reference', 'determination_basis': 'source_reports_measurement'},
            {'evidence_kind': 'published_computational_reference'},
            {'determination_basis': 'source_reports_measurement'},
            {'determination_basis': 'not_stated'},
            {'evidence_kind': 'technical_association_reference'},
        ):
            with self.subTest(fields=fields):
                self.assert_invalid(crystallographic_catalog, lambda m,p,s: p['records'][0].update(fields))
        self.assert_invalid(crystallographic_catalog, lambda m,p,s: p['records'][0]['method_definition'].update(type='source_reported_conventional'))

    def test_crystallographic_cannot_be_bulk_true_or_non_density(self):
        for basis in ('bulk', 'true', 'apparent', 'not_stated', None):
            with self.subTest(basis=basis):
                self.assert_invalid(crystallographic_catalog, lambda m,p,s: p['records'][0].update(density_basis=basis))
        def non_density(m,p,s):
            prop=p['records'][0]
            prop.update(quantity='youngs_modulus',quantity_dimension='pressure',density_basis=None)
            prop['reported_value'].update(unit_text='GPa',unit_code='GPa')
        self.assert_invalid(crystallographic_catalog, non_density)
        self.assert_invalid(synthetic_material_catalog, lambda m,p,s: p['records'][0].update(density_basis='crystallographic'))

    def test_new_method_classes_need_primary_method_and_classification_support(self):
        for make in (compilation_catalog, crystallographic_catalog):
            for tag in ('method','classification'):
                def remove(m,p,s):
                    p['records'][0]['method_definition']['evidence'][0]['supports'].remove(tag)
                self.assert_invalid(make,remove)
            self.assert_invalid(make,lambda m,p,s: p['records'][0]['evidence'][0]['supports'].remove('classification'))
            self.assert_invalid(make,lambda m,p,s: p['records'][0]['method_definition']['evidence'][0].update(source_id='absent_source'))

    def test_wrong_basis_pairings_and_unsupported_method_are_closed(self):
        self.assert_invalid(synthetic_material_catalog,lambda m,p,s: p['records'][0].update(determination_basis='source_reports_compiled_measurements'))
        self.assert_invalid(crystallographic_catalog,lambda m,p,s: p['records'][0]['method_definition'].update(type='source_reported_other_derivation'))
        self.assert_invalid(compilation_catalog,lambda m,p,s: p['records'][0]['method_definition'].update(type='source_reported_crystallographic_derivation'))

    def test_fractional_digit_spacing_is_narrow_and_precision_preserving(self):
        for source,number in (('2.329 1289','2.3291289'),('0.123 450','0.123450'),
                              ('12.345 678 90','12.34567890'),('2.329 1','2.3291')):
            with self.subTest(source=source):
                self.assertTrue(_numeric_token_matches(source,number))
                graph=synthetic_material_catalog()
                graph[1]['records'][0]['reported_value'].update(value_text=source,number=number)
                validate_material_catalog(*graph)
                self.assertEqual(graph[1]['records'][0]['reported_value']['value_text'],source)
        for source in ('2.329  1289','2.329\t1289','2.329\n1289','2 .329 1289',
                       '2. 329 1289','2.32 91289','2.329 12 89','2.329\u00a01289',
                       '2,329 1289','+2.329 1289','2.329 1289e0','2.329 +1289',
                       '02.329 1289','2.329 1289.0','2.329 12890'):
            with self.subTest(source=source):
                self.assertFalse(_numeric_token_matches(source,'2.3291289'))
        self.assertFalse(_numeric_token_matches('2.329 1280','2.329128'))
        self.assertFalse(_numeric_token_matches('2.329 128','2.3291280'))

    def test_spelled_unit_is_not_a_conversion_or_general_unit_parser(self):
        graph=crystallographic_catalog();validate_material_catalog(*graph)
        self.assertEqual(graph[1]['records'][0]['reported_value']['unit_code'],'g/cm^3')
        for spelling in ('grams per cubic meter','gram per cubic centimeter','GRAMS PER CUBIC CENTIMETER'):
            self.assert_invalid(crystallographic_catalog,lambda m,p,s:p['records'][0]['reported_value'].update(unit_text=spelling))
        self.assert_invalid(crystallographic_catalog,lambda m,p,s:p['records'][0]['reported_value'].update(unit_code='kg/m^3'))

    def test_linked_reference_condition_keeps_both_sources(self):
        graph=synthetic_material_catalog();m,p,s=graph;prop=p['records'][0]
        companion=deepcopy(s['records'][0]);companion.update(id='synthetic_companion',urls=['https://example.invalid/companion.pdf']);s['records'].append(companion)
        prop['conditions']['temperature']={'status':'reported','text':'20 °C reference basis, not every measurement temperature',
            'notes':'Direct reference statement belongs to companion; primary report recalculates the same objects.',
            'evidence':[{'source_id':prop['source_id'],'url':prop['source_document']['url'],
                         'locator':'Synthetic primary introduction: corrections to same objects in companion, not a direct temperature statement','supports':['condition']},
                        {'source_id':companion['id'],'url':companion['urls'][0],
                         'locator':'Synthetic companion §2: direct 20 °C reference-volume statement','supports':['condition']}]}
        validate_material_catalog(*graph)
        # A secondary statement alone cannot acquire primary provenance.
        prop['conditions']['temperature']['evidence'].pop(0)
        with self.assertRaises(ValueError):validate_material_catalog(*graph)


if __name__ == '__main__':
    unittest.main()
