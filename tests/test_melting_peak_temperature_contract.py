"""Fictional source-labelled melting peaks are separate catalogue objects."""
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
from test_glass_transition_temperature_contract import fixture as tg_fixture
from test_material_reference_contract import synthetic_mean_catalog
from test_material_uncertainty_contract import uncertainty_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_specified_elongation_contract import fixture as target_fixture


def fixture(number='25.00',unit='degC',text=None):
    graph=tg_fixture(number,unit,text);prop=graph[1]['records'][0]
    prop.update(quantity='melting_peak_temperature',source_property_label='Fictional Tm1 endothermic peak')
    prop['method_definition']['definition']='Fictional second-heating endothermic peak; precise algorithm unknown.'
    prop['conditions'].setdefault('additional_conditions',[]).append(dict(name='thermal_peak_label',fact=dict(
        status='reported',text='Tm1',evidence=[dict(source_id=prop['source_id'],url=prop['source_document']['url'],
            locator='Fictional source peak-label declaration',supports=['condition'])],notes='Source label only,not onset/endset or another material.')))
    return graph


def two_peaks():
    graph=fixture();first=graph[1]['records'][0];second=deepcopy(first)
    second['id']=first['id']+'_upper_peak';second['source_property_label']='Fictional Tm2 endothermic peak'
    second['reported_value'].update(number='35.00',value_text='35.00')
    second['conditions']['additional_conditions'][0]['fact']['text']='Tm2'
    graph[1]['records'].append(second)
    state=next(s for s in graph[0]['records'] if s['id']==first['material_state_id'])
    state['property_ids'].append(second['id'])
    return graph


class MeltingPeakTemperatureContractTests(unittest.TestCase):
    def test_same_state_same_quantity_query_export_keeps_both_complete_peaks(self):
        graph=two_peaks();original=deepcopy(graph)
        db=Database(dict(zip(('materials','reference_properties','sources'),graph)))
        selected=list(db.records(quantity='melting_peak_temperature'))
        expected={p['id']:p for p in graph[1]['records']}
        self.assertEqual({r['property']['id']:r['property'] for r in selected},expected)
        self.assertEqual(list(db.records(quantity='glass_transition_temperature')),[])
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'peaks';db.export(dest,quantity='melting_peak_temperature')
            self.assertEqual(read_snapshot(dest)[1],{r['record_id']:r for r in selected})
        self.assertEqual(graph,original)

    def test_signed_coordinates_and_temperature_floors_are_reused(self):
        for number,unit,text in [('-273.15','degC','−273.15'),('-0.00','degC','−0.00'),('0','K','0'),('270.00','K','270.00')]:
            validate_material_catalog(*fixture(number,unit,text))
        for number,unit,text in [('-273.151','degC','−273.151'),('-0.01','K','−0.01'),('-10.00','degC','10.00'),('-10.00','degC','−10.0')]:
            with self.assertRaises(ValueError):validate_material_catalog(*fixture(number,unit,text))
        for text in ('−20.0 to −10.0','−20.0–−10.0'):
            graph=fixture();graph[1]['records'][0]['reported_value']=dict(kind='interval',lower='-20.0',upper='-10.0',value_text=text,unit_code='degC',unit_text='°C',endpoint_semantics='source_reported_not_a_confidence_interval')
            validate_material_catalog(*graph)

    def test_closed_quantity_units_and_target_roles(self):
        for update in ({'quantity':'melting_temperature'},{'quantity':'crystallization_temperature'},
                       {'quantity_dimension':'pressure'},{'engineering_allowable':True},{'evaluation_support':'evaluator_input'}):
            graph=fixture();graph[1]['records'][0].update(update)
            self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for unit in ('MPa','percent','percent_elongation','shore_a_scale','kJ/m^2','degF'):
            graph=fixture();graph[1]['records'][0]['reported_value'].update(unit_code=unit,unit_text=unit)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();graph[1]['records'][0]['specified_elongation']=target_fixture()[1]['records'][0]['specified_elongation']
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_absolute_uncertainty_keeps_difference_role_without_offset(self):
        for central_unit,central_text,amplitude_unit,amplitude_text in [('degC','°C','K','K'),('K','K','degC','°C')]:
            graph=uncertainty_catalog();prop=graph[1]['records'][0]
            prop.update(quantity='melting_peak_temperature',quantity_dimension='temperature')
            prop['reported_value'].update(number='250.00',value_text='250.00',unit_code=central_unit,unit_text=central_text)
            prop['uncertainty'].update(number='0.50',value_text='0.50',unit_code=amplitude_unit,unit_text=amplitude_text)
            validate_material_catalog(*graph)
            self.assertEqual(prop['reported_value']['number'],'250.00');self.assertEqual(prop['uncertainty']['number'],'0.50')
            prop['uncertainty'].update(number='-0.50',value_text='−0.50')
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=synthetic_mean_catalog();graph[1]['records'][0]['uncertainty'].update(unit_code='K',unit_text='K')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_relative_measures_require_source_scale_or_unknown_origin_note(self):
        graph=synthetic_reported_measures_catalog('relative_errors');prop=graph[1]['records'][0]
        prop.update(quantity='melting_peak_temperature',quantity_dimension='temperature')
        prop['reported_value'].update(number='25.0',value_text='25.0',unit_code='degC',unit_text='°C')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for measure in prop['uncertainty']['measures']:measure['note']='Source relative descriptor; reference scale/origin unknown; no recomputed CV.'
        validate_material_catalog(*graph)

    def test_four_language_rendering_retains_source_glyph_and_peak_labels(self):
        graph=two_peaks();graph[1]['records'][0]['reported_value'].update(number='-10.00',value_text='−10.00')
        data=dict(zip(('materials','reference_properties','sources'),graph))
        for language in ('en','zh','ja','de'):
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:data[n]):
                text=render_material_catalog(graph[1],'reference-properties',language)
            for token in (material_labels(language)['code_melting_peak_temperature'],'−10.00','35.00','Tm1','Tm2','endothermic peak','unknown'):
                self.assertIn(token,text)

    def test_two_peaks_are_two_properties_not_two_materials_or_implicit_interval(self):
        graph=two_peaks();db=Database(dict(zip(('materials','reference_properties','sources'),graph)))
        result=db.summary(quantity='melting_peak_temperature')
        self.assertEqual((result['property_records'],result['material_identities'],result['material_states']),(2,1,1))
        selected=list(db.records(quantity='melting_peak_temperature'));selected[0]['property']['reported_value']['number']='999'
        self.assertNotIn('999',[r['property']['reported_value']['number'] for r in db.records(quantity='melting_peak_temperature')])
        for p in graph[1]['records']:
            self.assertEqual(p['reported_value']['kind'],'scalar');self.assertIsNone(p['sample_count']['value']);self.assertIsNone(p['uncertainty'])

    def test_generated_schema_retains_five_branches_and_existing_Tg(self):
        schema=json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(schema,_PROPERTIES_SCHEMA);self.assertEqual(len(schema['$defs']['property']['oneOf']),24)
        Draft202012Validator.check_schema(schema)
        for graph in (fixture(),two_peaks(),tg_fixture(),synthetic_mean_catalog(),target_fixture()):
            Draft202012Validator(schema).validate(graph[1]);validate_material_catalog(*graph)


if __name__=='__main__':unittest.main()
