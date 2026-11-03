"""Fictional elongation results exercise contextual percent and consumer gates."""
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
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_specified_elongation_contract import fixture as target_fixture


def fixture(number='125'):
    m,p,s=synthetic_mean_catalog()
    prop=p['records'][0]
    prop.update(quantity='tensile_elongation_at_break',quantity_dimension='dimensionless',source_property_label='Fictional elongation at break (%)')
    prop['reported_value'].update(number=number,value_text=number,unit_code='percent_elongation',unit_text='%')
    amplitude='0' if number in ('0','0.00') else '0.15'
    prop['uncertainty'].update(number=amplitude,value_text=amplitude,unit_code='percent_elongation',unit_text='%')
    prop['method_definition'].update(definition='Fictional source elongation; gauge, convention and fracture selection unknown.',extraction_window=None)
    return m,p,s


class BreakElongationContractTests(unittest.TestCase):
    def test_complete_query_export_keeps_source_percent_scale_and_absolute_SD(self):
        m,p,s=fixture()
        db=Database(dict(zip(('materials','reference_properties','sources'),(m,p,s))))
        rows=list(db.records(quantity='tensile_elongation_at_break'))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['property'],p['records'][0])
        self.assertEqual(list(db.records(quantity='tensile_stress_at_break')),[])
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'elongation'
            db.export(dest,quantity='tensile_elongation_at_break')
            prop=read_snapshot(dest)[1][p['records'][0]['id']]['property']
            self.assertEqual(prop,p['records'][0])
            self.assertEqual(prop['reported_value']['number'],'125')
            self.assertEqual(prop['uncertainty']['number'],'0.15')

    def test_quantity_unit_dimension_and_target_are_closed_in_both_validators(self):
        m,p,s=fixture()
        stored=json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(stored,_PROPERTIES_SCHEMA)
        Draft202012Validator.check_schema(stored)
        Draft202012Validator(stored).validate(p)
        mutations=[{'unit_code':'percent','unit_text':'%'},{'unit_code':'MPa','unit_text':'MPa'}]
        for unit in mutations:
            bad=deepcopy(p)
            bad['records'][0]['reported_value'].update(unit)
            self.assertFalse(Draft202012Validator(stored).is_valid(bad))
            with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)
        for update in ({'quantity':'tensile_strength','quantity_dimension':'pressure'},
                       {'quantity_dimension':'pressure'},
                       {'specified_elongation':target_fixture()[1]['records'][0]['specified_elongation']}):
            bad=deepcopy(p)
            bad['records'][0].update(update)
            self.assertFalse(Draft202012Validator(stored).is_valid(bad))
            with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)

    def test_source_zero_and_above100_do_not_relax_other_quantity_positivity(self):
        for number in ('0','0.00','125','1000'):
            with self.subTest(number=number):validate_material_catalog(*fixture(number))
        for token in ('-1','NaN','Infinity'):
            graph=fixture(token)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        m,p,s=synthetic_mean_catalog()
        p['records'][0]['reported_value'].update(number='0',value_text='0')
        with self.assertRaises(ValueError):validate_material_catalog(m,p,s)
        m,p,s=fixture()
        p['records'][0]['reported_value']['value_text']='1.25'
        with self.assertRaises(ValueError):validate_material_catalog(m,p,s)

    def test_relative_percent_is_not_absolute_elongation_percentage_points(self):
        m,p,s=synthetic_reported_measures_catalog('relative_errors')
        prop=p['records'][0]
        prop.update(quantity='tensile_elongation_at_break',quantity_dimension='dimensionless')
        prop['reported_value'].update(number='12.5',value_text='12.5',unit_code='percent_elongation',unit_text='%')
        validate_material_catalog(m,p,s)
        self.assertTrue(all(v['reported_value']['unit_code']=='percent' for v in prop['uncertainty']['measures']))
        bad=deepcopy(p)
        bad['records'][0]['uncertainty']['measures'][0]['reported_value']['unit_code']='percent_elongation'
        with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)
        m,p,s=fixture()
        p['records'][0]['uncertainty']['unit_code']='percent'
        with self.assertRaises(ValueError):validate_material_catalog(m,p,s)

    def test_four_language_rendering_preserves_original_scale_and_unknowns(self):
        m,p,s=fixture()
        data=dict(zip(('materials','reference_properties','sources'),(m,p,s)))
        for lang in ('en','zh','ja','de'):
            with self.subTest(language=lang):
                label=material_labels(lang)['code_tensile_elongation_at_break']
                with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):
                    text=render_material_catalog(p,'reference-properties',lang)
                self.assertIn(label,text)
                self.assertIn('125',text)
                self.assertIn('0.15',text)
                self.assertIn('fracture selection unknown',text)


if __name__=='__main__':unittest.main()
