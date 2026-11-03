"""Endpoint separation and source-percentage consumer behavior, fictional only."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,validate_material_catalog
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from test_break_elongation_contract import fixture as break_fixture
from test_specified_elongation_contract import fixture as target_fixture


def fixture(number='125'):
    m,p,s=break_fixture(number)
    prop=p['records'][0]
    prop.update(quantity='tensile_elongation_at_strength',source_property_label='Fictional elongation at source tensile strength (%)')
    prop['method_definition']['definition']='Fictional strength endpoint; exact peak selection and strain convention unknown.'
    return m,p,s


class StrengthElongationContractTests(unittest.TestCase):
    def test_equal_values_and_locators_keep_two_endpoints_and_full_export(self):
        m,p,s=break_fixture()
        strength=deepcopy(p['records'][0])
        strength.update(id=strength['id']+'_strength_endpoint',quantity='tensile_elongation_at_strength')
        p['records'].append(strength)
        m['records'][0]['property_ids'].append(strength['id'])
        validate_material_catalog(m,p,s)
        db=Database(dict(zip(('materials','reference_properties','sources'),(m,p,s))))
        self.assertEqual(len(list(db.records(quantity='tensile_elongation_at_break'))),1)
        self.assertEqual(len(list(db.records(quantity='tensile_elongation_at_strength'))),1)
        self.assertEqual(list(db.records(quantity='tensile_modulus')),[])
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'strength-elongation'
            db.export(dest,quantity='tensile_elongation_at_strength')
            self.assertEqual(read_snapshot(dest)[1][strength['id']]['property'],strength)
        # Metadata validation does not claim paired raw tests or impose an order.
        strength['reported_value'].update(number='150',value_text='150')
        validate_material_catalog(m,p,s)

    def test_source_domain_and_closed_quantity_units_target(self):
        for number in ('0','0.00','125','1000'):
            with self.subTest(number=number):validate_material_catalog(*fixture(number))
        m,p,s=fixture()
        Draft202012Validator(_PROPERTIES_SCHEMA).validate(p)
        for update in ({'unit_code':'MPa','unit_text':'MPa'},{'unit_code':'percent','unit_text':'%'}):
            bad=deepcopy(p)
            bad['records'][0]['reported_value'].update(update)
            self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(bad))
            with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)
        for update in ({'quantity_dimension':'pressure'},
                       {'specified_elongation':target_fixture()[1]['records'][0]['specified_elongation']}):
            bad=deepcopy(p)
            bad['records'][0].update(update)
            self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(bad))
            with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)
        bad=deepcopy(p)
        bad['records'][0]['uncertainty']['unit_code']='percent'
        with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)

    def test_four_language_actual_rendering_does_not_rescale(self):
        m,p,s=fixture()
        data=dict(zip(('materials','reference_properties','sources'),(m,p,s)))
        for lang in ('en','zh','ja','de'):
            with self.subTest(language=lang):
                label=material_labels(lang)['code_tensile_elongation_at_strength']
                with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):
                    text=render_material_catalog(p,'reference-properties',lang)
                self.assertIn(label,text)
                self.assertIn('125',text)
                self.assertIn('0.15',text)
                self.assertIn('peak selection and strain convention unknown',text)


if __name__=='__main__':unittest.main()
