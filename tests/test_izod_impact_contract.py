"""Fictional source Izod references never imply notch geometry or fracture Gc."""
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
from test_material_uncertainty_contract import uncertainty_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_specified_elongation_contract import fixture as target_fixture
from test_shore_a_hardness_contract import fixture as hardness_fixture
from test_flexural_elongation_contract import fixture as elongation_fixture
from test_tear_strength_contract import fixture as tear_fixture


def fixture(unit='kJ/m^2', text='kJ/m²'):
    m,p,s=synthetic_mean_catalog()
    prop=p['records'][0]
    prop.update(quantity='izod_impact_strength',quantity_dimension='energy_per_area',source_property_label='Fictional Izod impact strength',
                summary_statistic='not_stated',uncertainty=None,uncertainty_status='not_reported_in_inspected_source')
    prop['reported_value'].update(number='17.35',value_text='17.35',unit_code=unit,unit_text=text)
    prop['sample_count'].update(value=None,relation='not_reported',scope='Izod count unknown.',source_statement='No impact specimen or batch count.',evidence=[])
    prop['uncertainty_note']='Numeric dispersion unknown; no zero-scatter or borrowed-statistic claim.'
    prop['method_definition'].update(definition='Fictional source Izod result; notch status, velocity and normalization algorithm unknown.',extraction_window=None)
    prop['conditions'].setdefault('additional_conditions',[]).append({'name':'notch_status','fact':{
        'status':'not_reported_in_inspected_source','text':None,'evidence':[],
        'notes':'Notched/unnotched status unknown; the standard citation does not choose a mode.'}})
    evidence=deepcopy(prop['evidence']);evidence[0]['supports'].append('source_discrepancy')
    prop['source_discrepancies']=[{'description':'Fictional table and graphic differ.','disposition':'Preserve the selected table literal; no repair or averaging.','evidence':evidence}]
    return m,p,s


class IzodImpactContractTests(unittest.TestCase):
    def test_complete_query_export_keeps_unknown_notch_and_source_conflict(self):
        graph=fixture();expected=deepcopy(graph)
        db=Database(dict(zip(('materials','reference_properties','sources'),graph)))
        prop=graph[1]['records'][0]
        self.assertEqual([r['property'] for r in db.records(quantity='izod_impact_strength')],[prop])
        for quantity in ('tear_strength','tensile_strength','compressive_strength'):
            self.assertEqual(list(db.records(quantity=quantity)),[])
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'izod';db.export(dest,quantity='izod_impact_strength')
            self.assertEqual(read_snapshot(dest)[1][prop['id']]['property'],prop)
        self.assertEqual(graph,expected)
        self.assertIsNone(prop['uncertainty']);self.assertIsNone(prop['sample_count']['value'])

    def test_area_energy_units_spelling_and_no_automatic_rescaling(self):
        for code,spellings in [('kJ/m^2',('kJ/m^2','kJ/m2','kJ/m²')),('J/m^2',('J/m^2','J/m2','J/m²'))]:
            for spelling in spellings:
                graph=fixture(code,spelling);validate_material_catalog(*graph)
                Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])
                self.assertEqual(graph[1]['records'][0]['reported_value']['number'],'17.35')
        for unit in ('J','N','MPa','N/m','percent','percent_elongation','shore_a_scale','J/mm^2'):
            graph=fixture();graph[1]['records'][0]['reported_value'].update(unit_code=unit,unit_text=unit)
            # Registered legacy central units are closed scientifically by dimension.
            with self.subTest(unit=unit),self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture('kJ/m^2','J/m²')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_positive_scalar_interval_and_comparison_roles(self):
        for token in ('0','-1','NaN','Infinity'):
            graph=fixture();graph[1]['records'][0]['reported_value'].update(number=token,value_text=token)
            with self.subTest(token=token),self.assertRaises(ValueError):validate_material_catalog(*graph)
        for lower,upper in [('1','40'),('0','40'),('20','20'),('30','20')]:
            graph=fixture();graph[1]['records'][0]['reported_value']=dict(kind='interval',lower=lower,upper=upper,
                value_text=lower+' to '+upper,unit_code='kJ/m^2',unit_text='kJ/m²',endpoint_semantics='source_reported_not_a_confidence_interval')
            if lower=='1':validate_material_catalog(*graph)
            else:
                with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();graph[1]['records'][0]['reported_value']=dict(kind='comparison',operator='>',number='3',value_text='>3',unit_code='J/m^2',unit_text='J/m²')
        validate_material_catalog(*graph)

    def test_absolute_energy_amplitude_and_relative_percent_stay_distinct(self):
        graph=uncertainty_catalog();prop=graph[1]['records'][0]
        prop.update(quantity='izod_impact_strength',quantity_dimension='energy_per_area')
        prop['reported_value'].update(unit_code='kJ/m^2',unit_text='kJ/m²')
        prop['uncertainty'].update(unit_code='kJ/m^2',unit_text='kJ/m²')
        validate_material_catalog(*graph)
        self.assertEqual(prop['uncertainty']['confidence_level']['unit_code'],'percent')
        bad=deepcopy(graph);bad[1]['records'][0]['uncertainty'].update(unit_code='MPa',unit_text='MPa')
        with self.assertRaises(ValueError):validate_material_catalog(*bad)
        graph=synthetic_reported_measures_catalog('relative_errors');prop=graph[1]['records'][0]
        prop.update(quantity='izod_impact_strength',quantity_dimension='energy_per_area')
        prop['reported_value'].update(unit_code='kJ/m^2',unit_text='kJ/m²')
        validate_material_catalog(*graph)
        self.assertTrue(all(m['reported_value']['unit_code']=='percent' for m in prop['uncertainty']['measures']))
        prop['uncertainty']['measures'][0]['reported_value'].update(unit_code='kJ/m^2',unit_text='kJ/m²')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_actual_four_language_rendering_preserves_conditions_and_conflict(self):
        graph=fixture();data=dict(zip(('materials','reference_properties','sources'),graph))
        for language in ('en','zh','ja','de'):
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):
                output=render_material_catalog(graph[1],'reference-properties',language)
            for token in (material_labels(language)['code_izod_impact_strength'],'17.35','kJ/m²','notch status','unknown','table and graphic differ'):
                self.assertIn(token,output)

    def test_public_schema_legacy_domains_and_no_target_or_engine_use(self):
        schema=json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(schema,_PROPERTIES_SCHEMA);self.assertEqual(len(schema['$defs']['property']['oneOf']),15)
        Draft202012Validator.check_schema(schema)
        for update in [{'specified_elongation':target_fixture()[1]['records'][0]['specified_elongation']},
                       {'quantity':'charpy_impact_strength'},{'quantity':'mode_i_energy_release_rate'},
                       {'engineering_allowable':True},{'universal_bound':True},{'evaluation_support':'evaluator_input'}]:
            graph=fixture();graph[1]['records'][0].update(update)
            self.assertFalse(Draft202012Validator(schema).is_valid(graph[1]))
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();graph[1]['records'][0]['quantity_dimension']='force_per_length'
        with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for factory in (synthetic_mean_catalog,tear_fixture,hardness_fixture,elongation_fixture,target_fixture):
            graph=factory();validate_material_catalog(*graph);Draft202012Validator(schema).validate(graph[1])
        for factory in (synthetic_mean_catalog,tear_fixture):
            graph=factory();graph[1]['records'][0]['reported_value'].update(number='0',value_text='0')
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        validate_material_catalog(*elongation_fixture('0'));validate_material_catalog(*elongation_fixture('1100'))
        with self.assertRaises(ValueError):validate_material_catalog(*hardness_fixture('101'))


if __name__=='__main__':unittest.main()
