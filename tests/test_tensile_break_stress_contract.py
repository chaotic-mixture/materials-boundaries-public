"""Fictional break and peak stresses exercise distinct consumer data paths."""
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


def fixture():
    m, p, s = synthetic_mean_catalog()
    prop = p['records'][0]
    prop.update(quantity='tensile_stress_at_break', source_property_label='Fictional stress at break')
    prop['method_definition']['definition'] = 'Fictional tensile break stress; fracture detection and stress convention unknown.'
    prop['method_definition']['extraction_window'] = None
    return m, p, s


class TensileBreakStressContractTests(unittest.TestCase):
    def test_break_and_strength_query_export_keep_distinct_facts(self):
        m, p, s = fixture()
        # Same number/locator cannot make two different measured quantities equivalent.
        strength = deepcopy(p['records'][0])
        strength.update(id=strength['id'] + '_strength', quantity='tensile_strength')
        p['records'].append(strength)
        m['records'][0]['property_ids'].append(strength['id'])
        validate_material_catalog(m, p, s)
        db = Database(dict(zip(('materials', 'reference_properties', 'sources'), (m, p, s))))
        self.assertEqual(len(list(db.records(quantity='tensile_stress_at_break'))), 1)
        self.assertEqual(len(list(db.records(quantity='tensile_strength'))), 1)
        self.assertEqual(list(db.records(quantity='tensile_stress_at_specified_elongation')), [])
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'break-export'
            db.export(dest, quantity='tensile_stress_at_break')
            record = read_snapshot(dest)[1][p['records'][0]['id']]['property']
            self.assertEqual(record, p['records'][0])
            self.assertIn('fracture detection', record['method_definition']['definition'])

    def test_strict_four_language_actual_rendering(self):
        m, p, s = fixture()
        data = dict(zip(('materials', 'reference_properties', 'sources'), (m, p, s)))
        for lang in ('en', 'zh', 'ja', 'de'):
            with self.subTest(language=lang):
                label = material_labels(lang)['code_tensile_stress_at_break']
                with patch('materials_boundaries.catalog.read_catalog', side_effect=lambda n: data[n]):
                    output = render_material_catalog(p, 'reference-properties', lang)
                self.assertIn(label, output)
                self.assertIn('fracture detection and stress convention unknown', output)

    def test_pressure_closed_target_boundary_and_schema_consistency(self):
        m, p, s = fixture()
        public = json.loads((Path(__file__).resolve().parents[1] / 'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(public, _PROPERTIES_SCHEMA)
        Draft202012Validator(public).validate(p)
        bad = deepcopy(p)
        bad['records'][0]['reported_value'].update(unit_code='kg/m^3', unit_text='kg/m^3')
        with self.assertRaises(ValueError):
            validate_material_catalog(m, bad, s)
        bad = deepcopy(p)
        bad['records'][0]['specified_elongation'] = target_fixture()[1]['records'][0]['specified_elongation']
        self.assertFalse(Draft202012Validator(public).is_valid(bad))
        with self.assertRaises(ValueError):
            validate_material_catalog(m, bad, s)


if __name__ == '__main__':
    unittest.main()
