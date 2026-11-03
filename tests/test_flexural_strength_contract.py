"""Fictional bending strengths exercise type separation and public data paths."""
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


def fixture():
    m, p, s = synthetic_mean_catalog()
    prop = p['records'][0]
    prop.update(quantity='flexural_strength', source_property_label='Fictional flexural strength')
    prop['method_definition']['definition'] = 'Fictional bending procedure; strength extraction criterion unknown.'
    prop['method_definition']['extraction_window'] = None
    return m, p, s


class FlexuralStrengthContractTests(unittest.TestCase):
    def test_query_export_preserves_strength_and_unknown_criterion(self):
        m, p, s = fixture()
        db = Database({'materials': m, 'reference_properties': p, 'sources': s})
        validate_material_catalog(m, p, s)
        self.assertEqual(len(list(db.records(quantity='flexural_strength'))), 1)
        for other in ('flexural_modulus', 'tensile_strength', 'tensile_yield_strength', 'youngs_modulus'):
            self.assertEqual(list(db.records(quantity=other)), [])
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'export'
            db.export(dest, quantity='flexural_strength')
            record = read_snapshot(dest)[1][p['records'][0]['id']]['property']
            self.assertEqual(record, p['records'][0])
            self.assertIn('criterion unknown', record['method_definition']['definition'])

    def test_four_language_canonical_rendering(self):
        m, p, s = fixture()
        data = dict(zip(('materials', 'reference_properties', 'sources'), (m, p, s)))
        for language in ('en', 'zh', 'ja', 'de'):
            with self.subTest(language=language):
                self.assertTrue(material_labels(language)['code_flexural_strength'])
                with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda name: data[name]):
                    output = render_material_catalog(p, 'reference-properties', language)
                self.assertIn('criterion unknown', output)
                self.assertIn(material_labels(language)['code_flexural_strength'], output)

    def test_pressure_units_and_closed_descriptor_boundary(self):
        m, p, s = fixture()
        for unit in ('MPa', 'GPa', 'N/mm^2', 'kN/mm^2'):
            q = deepcopy(p)
            q['records'][0]['reported_value'].update(unit_text=unit, unit_code=unit)
            q['records'][0]['uncertainty'].update(unit_text=unit, unit_code=unit)
            validate_material_catalog(m, q, s)
        bad = deepcopy(p)
        bad['records'][0]['reported_value'].update(unit_text='kg/m^3', unit_code='kg/m^3')
        with self.assertRaises(ValueError):
            validate_material_catalog(m, bad, s)
        bad = deepcopy(p)
        bad['records'][0]['specified_elongation'] = {'number': '100'}
        self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(bad))
        with self.assertRaises(ValueError):
            validate_material_catalog(m, bad, s)

    def test_quantity_separates_same_numeric_fact_from_modulus(self):
        m, p, s = fixture()
        modulus = deepcopy(p['records'][0])
        modulus.update(id=modulus['id'] + '_modulus', quantity='flexural_modulus')
        p['records'].append(modulus)
        m['records'][0]['property_ids'].append(modulus['id'])
        validate_material_catalog(m, p, s)
        duplicate = deepcopy(p['records'][0])
        duplicate['id'] += '_duplicate'
        p['records'].append(duplicate)
        m['records'][0]['property_ids'].append(duplicate['id'])
        with self.assertRaises(ValueError):
            validate_material_catalog(m, p, s)

    def test_public_schema_and_legacy_shape_remain_consistent(self):
        public = json.loads((Path(__file__).resolve().parents[1] / 'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(public, _PROPERTIES_SCHEMA)
        for factory in (synthetic_mean_catalog, fixture):
            m, p, s = factory()
            Draft202012Validator(public).validate(p)
            validate_material_catalog(m, p, s)
            self.assertNotIn('specified_elongation', p['records'][0])


if __name__ == '__main__':
    unittest.main()
