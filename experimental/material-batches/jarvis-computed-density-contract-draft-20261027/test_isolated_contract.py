"""Exercise an unapplied draft in an explicitly selected external stage."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--stage', type=Path, required=True)
args, remaining = parser.parse_known_args()
STAGE = args.stage.resolve()
sys.path[:0] = [str(STAGE), str(STAGE / 'tests')]
import materials_boundaries.material_references as references
from test_material_reference_contract import synthetic_material_catalog

assert Path(references.__file__).resolve().is_relative_to(STAGE)
METHOD = 'source_reported_computational_structure_density'


def fixture():
    graph = synthetic_material_catalog()
    graph[2]['records'][0]['role'] = 'Synthetic published research reference; test data only'
    prop = graph[1]['records'][0]
    prop['evidence_kind'] = 'published_computational_reference'
    prop['determination_basis'] = 'source_reports_calculation'
    prop['density_basis'] = 'crystallographic'
    prop['summary_statistic'] = 'reported_value'
    prop['method_definition']['type'] = METHOD
    prop['method_definition']['evidence'][0]['supports'].append('classification')
    return graph


class IsolatedComputedDensityContractTests(unittest.TestCase):
    def test_computed_structure_density_is_accepted(self):
        references.validate_material_catalog(*fixture())

    def test_other_evidence_classes_cannot_use_new_method(self):
        for kind in references.EVIDENCE_KINDS:
            if kind == 'published_computational_reference':
                continue
            with self.subTest(kind=kind):
                graph = fixture()
                graph[1]['records'][0]['evidence_kind'] = kind
                with self.assertRaises(ValueError):
                    references.validate_material_catalog(*graph)

    def test_calculation_basis_is_required(self):
        for basis in ['source_reports_measurement', 'source_reports_compiled_measurements',
                      'not_stated', 'mixed_or_unclear']:
            with self.subTest(basis=basis):
                graph = fixture()
                graph[1]['records'][0]['determination_basis'] = basis
                with self.assertRaises(ValueError):
                    references.validate_material_catalog(*graph)

    def test_other_density_bases_are_rejected(self):
        for basis in ['apparent', 'bulk', 'true', 'not_stated', None,
                      'oven_dry_mass_over_fresh_or_water_saturated_volume']:
            with self.subTest(basis=basis):
                graph = fixture()
                graph[1]['records'][0]['density_basis'] = basis
                with self.assertRaises(ValueError):
                    references.validate_material_catalog(*graph)

    def test_non_density_is_rejected_even_with_matching_units(self):
        graph = fixture()
        prop = graph[1]['records'][0]
        prop.update(quantity='tensile_modulus', quantity_dimension='pressure', density_basis=None)
        prop['reported_value'].update(unit_text='GPa', unit_code='GPa')
        with self.assertRaisesRegex(ValueError, 'requires mass density|structural method'):
            references.validate_material_catalog(*graph)

    def test_classification_evidence_remains_required(self):
        graph = fixture()
        graph[1]['records'][0]['method_definition']['evidence'][0]['supports'].remove('classification')
        with self.assertRaises(ValueError):
            references.validate_material_catalog(*graph)

    def test_old_measured_crystal_contract_remains_distinct(self):
        graph = fixture()
        prop = graph[1]['records'][0]
        prop['method_definition']['type'] = 'source_reported_crystallographic_derivation'
        with self.assertRaisesRegex(ValueError, 'measured-input-derived'):
            references.validate_material_catalog(*graph)
        prop['evidence_kind'] = 'published_measurement_derived_reference'
        references.validate_material_catalog(*graph)
        prop['method_definition']['type'] = METHOD
        with self.assertRaisesRegex(ValueError, 'measured-input-derived'):
            references.validate_material_catalog(*graph)

    def test_conventional_method_does_not_unlock_crystal_basis(self):
        graph = fixture()
        graph[1]['records'][0]['method_definition']['type'] = 'source_reported_conventional'
        with self.assertRaises(ValueError):
            references.validate_material_catalog(*graph)

    def test_existing_runtime_graph_is_unchanged_and_valid(self):
        data = STAGE / 'materials_boundaries/data'
        graph = [json.loads((data / name).read_bytes()) for name in
                 ['materials.json', 'reference_properties.json', 'sources.json']]
        before = deepcopy(graph)
        references.validate_material_catalog(*graph)
        self.assertEqual(graph, before)

    def test_public_schema_matches_draft_runtime_schema(self):
        self.assertEqual(json.loads((STAGE / 'schemas/reference_properties.schema.json').read_bytes()),
                         references._PROPERTIES_SCHEMA)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])
