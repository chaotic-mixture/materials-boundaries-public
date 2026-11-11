"""Fictional Shore A cases verify scale closure, semantic bounds and consumers."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,validate_material_catalog
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from test_material_reference_contract import synthetic_mean_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_break_elongation_contract import fixture as elongation_fixture
from test_specified_elongation_contract import fixture as target_fixture

def fixture(number='38.0'):
    m,p,s=synthetic_mean_catalog();v=p['records'][0]
    v.update(quantity='shore_a_hardness',quantity_dimension='dimensionless',source_property_label='Fictional Shore A reading')
    v['reported_value'].update(number=number,value_text=number,unit_code='shore_a_scale',unit_text='Shore A')
    amplitude='0' if number in ('0','0.00') else '0.8'
    v['uncertainty'].update(number=amplitude,value_text=amplitude,unit_code='shore_a_scale',unit_text='Shore A')
    v['method_definition'].update(definition='Fictional empirical Shore A result; specimen route, calibration and compliance unknown.',extraction_window=None)
    return m,p,s

def interval_fixture(lower='0',upper='100'):
    m,p,s=fixture();v=p['records'][0]
    v.update(summary_statistic='not_stated',uncertainty=None,uncertainty_status='not_reported_in_inspected_source')
    v['reported_value']={'kind':'interval','lower':lower,'upper':upper,'value_text':lower+' to '+upper,'unit_code':'shore_a_scale','unit_text':'Shore A','endpoint_semantics':'source_reported_not_a_confidence_interval'}
    return m,p,s

class ShoreAHardnessContractTests(unittest.TestCase):
    def test_full_query_export_preserves_scale_and_separates_percent_elongation(self):
        m,p,s=fixture();db=Database(dict(zip(('materials','reference_properties','sources'),(m,p,s))))
        self.assertEqual(list(db.records(quantity='shore_a_hardness'))[0]['property'],p['records'][0])
        self.assertEqual(list(db.records(quantity='tensile_elongation_at_break')),[])
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'hardness';db.export(dest,quantity='shore_a_hardness')
            self.assertEqual(read_snapshot(dest)[1][p['records'][0]['id']]['property'],p['records'][0])
        self.assertEqual(p['records'][0]['reported_value']['number'],'38.0')
        self.assertEqual(p['records'][0]['uncertainty']['number'],'0.8')

    def test_central_scalar_interval_domain_and_legacy_positivity(self):
        for n in ('0','0.00','38.00','100','100.0'):
            with self.subTest(number=n):validate_material_catalog(*fixture(n))
        validate_material_catalog(*interval_fixture())
        for n in ('-0.1','100.01','NaN','Infinity'):
            with self.subTest(number=n):
                with self.assertRaises(ValueError):validate_material_catalog(*fixture(n))
        for bounds in [('-1','20'),('20','101'),('50','50'),('60','20')]:
            with self.subTest(bounds=bounds):
                with self.assertRaises(ValueError):validate_material_catalog(*interval_fixture(*bounds))
        # Shape-only JSON Schema does not claim Decimal semantic range checks.
        Draft202012Validator(_PROPERTIES_SCHEMA).validate(fixture('100.01')[1])
        m,p,s=synthetic_mean_catalog();p['records'][0]['reported_value'].update(number='0',value_text='0')
        with self.assertRaises(ValueError):validate_material_catalog(m,p,s)
        validate_material_catalog(*elongation_fixture('0'))
        validate_material_catalog(*elongation_fixture('1040'))

    def test_closed_units_targets_shapes_and_generated_public_schema(self):
        m,p,s=fixture();stored=json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(stored,_PROPERTIES_SCHEMA);Draft202012Validator.check_schema(stored)
        self.assertEqual(len(stored['$defs']['property']['oneOf']),15)
        for unit in [{'unit_code':'percent','unit_text':'%'},{'unit_code':'percent_elongation','unit_text':'%'},{'unit_code':'MPa','unit_text':'MPa'},{'unit_code':'shore_d_scale','unit_text':'Shore D'}]:
            bad=deepcopy(p);bad['records'][0]['reported_value'].update(unit)
            self.assertFalse(Draft202012Validator(stored).is_valid(bad))
            with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)
        for fields in [{'specified_elongation':target_fixture()[1]['records'][0]['specified_elongation']},{'quantity_dimension':'pressure'}]:
            bad=deepcopy(p);bad['records'][0].update(fields)
            self.assertFalse(Draft202012Validator(stored).is_valid(bad))
            with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)
        bad=deepcopy(p);bad['records'][0]['reported_value']={'kind':'comparison','operator':'>','number':'50','value_text':'>50','unit_code':'shore_a_scale','unit_text':'Shore A'}
        self.assertFalse(Draft202012Validator(stored).is_valid(bad))
        with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)
        bad=deepcopy(p);bad['records'][0].update(quantity='tensile_strength',quantity_dimension='pressure')
        self.assertFalse(Draft202012Validator(stored).is_valid(bad))
        with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)

    def test_absolute_scale_points_do_not_accept_relative_or_other_context_units(self):
        m,p,s=fixture()
        for code,text in [('percent','%'),('percent_elongation','%'),('MPa','MPa')]:
            bad=deepcopy(p);bad['records'][0]['uncertainty'].update(unit_code=code,unit_text=text)
            with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)
        m,p,s=synthetic_reported_measures_catalog('relative_errors');v=p['records'][0]
        v.update(quantity='shore_a_hardness',quantity_dimension='dimensionless')
        v['reported_value'].update(number='38.0',value_text='38.0',unit_code='shore_a_scale',unit_text='Shore A')
        validate_material_catalog(m,p,s)
        self.assertTrue(all(x['reported_value']['unit_code']=='percent' for x in v['uncertainty']['measures']))
        bad=deepcopy(p);bad['records'][0]['uncertainty']['measures'][0]['reported_value'].update(unit_code='shore_a_scale',unit_text='Shore A')
        with self.assertRaises(ValueError):validate_material_catalog(m,bad,s)

    def test_four_language_rendering_preserves_source_scale_and_unknowns(self):
        m,p,s=fixture();data=dict(zip(('materials','reference_properties','sources'),(m,p,s)))
        for lang in ('en','zh','ja','de'):
            with self.subTest(language=lang):
                with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):text=render_material_catalog(p,'reference-properties',lang)
                self.assertIn(material_labels(lang)['code_shore_a_hardness'],text)
                for part in ('38.0','0.8','Shore A','calibration and compliance unknown'):self.assertIn(part,text)

if __name__=='__main__':unittest.main()
