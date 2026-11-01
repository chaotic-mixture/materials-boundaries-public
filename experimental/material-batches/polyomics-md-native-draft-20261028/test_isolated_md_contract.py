"""Audit a proposed MD method in an isolated stage; never mutate live runtime."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--stage', type=Path, required=True)
args, remaining = parser.parse_known_args()
STAGE = args.stage.resolve()
sys.path[:0] = [str(STAGE), str(STAGE / 'tests')]
import materials_boundaries.material_references as references
from materials_boundaries.material_presentation import material_labels, render_material_catalog, validate_material_locales
from test_material_reference_contract import synthetic_material_catalog

assert Path(references.__file__).resolve().is_relative_to(STAGE)
METHOD = 'source_reported_molecular_simulation_density'


def fixture():
    graph = synthetic_material_catalog()
    graph[2]['records'][0]['role'] = 'Synthetic published molecular-simulation reference; no factual claims'
    prop = graph[1]['records'][0]
    prop.update(evidence_kind='published_computational_reference', determination_basis='source_reports_calculation',
                density_basis='simulation_cell', summary_statistic='reported_value', reporting_basis='not_stated')
    prop['method_definition']['type'] = METHOD
    prop['method_definition']['definition'] = 'Synthetic source-reported molecular-simulation density; test data only'
    prop['method_definition']['evidence'][0]['supports'].append('classification')
    return graph


class IsolatedMDContractTests(unittest.TestCase):
    def test_explicit_simulation_density_class_is_accepted(self):
        references.validate_material_catalog(*fixture())

    def test_other_evidence_classes_cannot_use_md_method(self):
        for kind in references.EVIDENCE_KINDS:
            if kind == 'published_computational_reference':
                continue
            graph = fixture()
            graph[1]['records'][0]['evidence_kind'] = kind
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                references.validate_material_catalog(*graph)

    def test_measurement_or_unknown_determination_is_rejected(self):
        for basis in ['source_reports_measurement', 'source_reports_compiled_measurements', 'not_stated', 'mixed_or_unclear']:
            graph = fixture()
            graph[1]['records'][0]['determination_basis'] = basis
            with self.subTest(basis=basis), self.assertRaises(ValueError):
                references.validate_material_catalog(*graph)

    def test_md_method_and_simulation_cell_basis_are_bidirectionally_bound(self):
        for basis in ['bulk', 'apparent', 'true', 'crystallographic', 'not_stated',
                      'oven_dry_mass_over_fresh_or_water_saturated_volume', None]:
            graph = fixture()
            graph[1]['records'][0]['density_basis'] = basis
            with self.subTest(basis=basis), self.assertRaises(ValueError):
                references.validate_material_catalog(*graph)
        for method in ['source_reported_conventional', 'source_reported_compilation',
                       'source_reported_crystallographic_derivation', 'source_reported_empirical_conversion',
                       'source_reported_computational_structure_density']:
            graph = fixture()
            graph[1]['records'][0]['method_definition']['type'] = method
            with self.subTest(method=method), self.assertRaises(ValueError):
                references.validate_material_catalog(*graph)

    def test_non_mass_density_including_same_dimension_basic_wood_is_rejected(self):
        for quantity, dimension in references.QUANTITY_DIMENSIONS.items():
            if quantity == 'mass_density':
                continue
            graph = fixture()
            prop = graph[1]['records'][0]
            prop.update(quantity=quantity, quantity_dimension=dimension)
            if dimension == 'pressure':
                prop['density_basis'] = None
                prop['reported_value'].update(unit_text='GPa', unit_code='GPa')
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                references.validate_material_catalog(*graph)

    def test_method_classification_evidence_is_still_required(self):
        graph = fixture()
        graph[1]['records'][0]['method_definition']['evidence'][0]['supports'].remove('classification')
        with self.assertRaises(ValueError):
            references.validate_material_catalog(*graph)

    def test_old_measured_and_dft_crystal_classes_remain_distinct(self):
        graph = fixture()
        prop = graph[1]['records'][0]
        prop['density_basis'] = 'crystallographic'
        prop['method_definition']['type'] = 'source_reported_computational_structure_density'
        references.validate_material_catalog(*graph)
        prop['method_definition']['type'] = 'source_reported_crystallographic_derivation'
        with self.assertRaises(ValueError):
            references.validate_material_catalog(*graph)
        prop['evidence_kind'] = 'published_measurement_derived_reference'
        references.validate_material_catalog(*graph)
        prop['method_definition']['type'] = METHOD
        prop['density_basis'] = 'simulation_cell'
        with self.assertRaises(ValueError):
            references.validate_material_catalog(*graph)

    def test_current_3180_record_graph_is_validated_without_mutation(self):
        graph = [json.loads((STAGE / 'materials_boundaries/data' / n).read_bytes()) for n in
                 ['materials.json', 'reference_properties.json', 'sources.json']]
        before = deepcopy(graph)
        references.validate_material_catalog(*graph)
        self.assertEqual(graph, before)
        self.assertEqual(len(graph[0]['identities']), 3180)

    def test_public_schema_and_four_language_label_envelopes_match(self):
        self.assertEqual(json.loads((STAGE / 'schemas/reference_properties.schema.json').read_bytes()), references._PROPERTIES_SCHEMA)
        locales = json.loads((STAGE / 'materials_boundaries/data/material_locales.json').read_bytes())
        validate_material_locales(locales)
        for language in ['en', 'zh', 'ja', 'de']:
            labels = material_labels(language)
            self.assertTrue(labels['code_' + METHOD])
            self.assertTrue(labels['code_simulation_cell'])

    def test_source_preserving_four_language_synthetic_preview(self):
        materials, properties, sources = fixture()
        inputs = {'materials': materials, 'reference_properties': properties, 'sources': sources}
        with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: deepcopy(inputs[name])):
            for language in ['en', 'zh', 'ja', 'de']:
                text = render_material_catalog(properties, 'reference-properties', language)
                self.assertIn(METHOD, text)
                self.assertIn('simulation_cell', text)
                self.assertIn('2.70', text)
                self.assertNotIn('[missing:', text)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])
