"""Fictional temperature coordinates and difference roles never imply DSC truth."""
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
from test_material_uncertainty_contract import uncertainty_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog
from test_specified_elongation_contract import fixture as target_fixture
from test_shore_a_hardness_contract import fixture as hardness_fixture
from test_flexural_elongation_contract import fixture as elongation_fixture
from test_tear_strength_contract import fixture as tear_fixture
from test_izod_impact_contract import fixture as impact_fixture


def fixture(number='-40.00',unit='degC',text=None):
    m,p,s=synthetic_mean_catalog();prop=p['records'][0]
    prop.update(quantity='glass_transition_temperature',quantity_dimension='temperature',source_property_label='Fictional DSC Tg',
        summary_statistic='not_stated',reporting_basis='not_stated',uncertainty=None,uncertainty_status='not_reported_in_inspected_source')
    prop['reported_value'].update(number=number,value_text=number if text is None else text,unit_code=unit,unit_text='°C' if unit=='degC' else 'K')
    prop['sample_count'].update(value=None,relation='not_reported',scope='DSC count unknown.',source_statement='Sample mass is not replicate count.',evidence=[])
    prop['uncertainty_note']='Numerical uncertainty and aggregation unknown; no zero-scatter claim.'
    prop['method_definition'].update(definition='Fictional DSC value; Tg criterion and scan cycle unknown.',extraction_window=None)
    evidence=deepcopy(prop['evidence']);evidence[0]['supports'].append('source_discrepancy')
    prop['source_discrepancies']=[dict(description='Fictional abstract and table disagree.',disposition='Preserve table literal without repair or uncertainty inference.',evidence=evidence)]
    return m,p,s


class GlassTransitionTemperatureContractTests(unittest.TestCase):
    def test_complete_query_export_keeps_negative_coordinate_and_unknowns(self):
        graph=fixture();original=deepcopy(graph);prop=graph[1]['records'][0]
        db=Database(dict(zip(('materials','reference_properties','sources'),graph)))
        self.assertEqual([r['property'] for r in db.records(quantity='glass_transition_temperature')],[prop])
        self.assertEqual(list(db.records(quantity='tensile_strength')),[])
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'tg';db.export(dest,quantity='glass_transition_temperature')
            self.assertEqual(read_snapshot(dest)[1][prop['id']]['property'],prop)
        self.assertEqual(graph,original);self.assertIsNone(prop['uncertainty'])
        self.assertEqual(prop['reported_value']['number'],'-40.00')

    def test_coordinate_boundaries_signed_zero_and_no_conversion(self):
        for number,unit in [('-273.15','degC'),('-40.00','degC'),('-0.00','degC'),('0','degC'),('900','degC'),('0','K'),('-0.0','K'),('233.15','K')]:
            graph=fixture(number,unit);validate_material_catalog(*graph)
            self.assertEqual(graph[1]['records'][0]['reported_value']['number'],number)
        for number,unit in [('-273.151','degC'),('-0.01','K'),('NaN','degC'),('Infinity','K'),('+1','degC'),('1e2','K')]:
            with self.subTest(number=number,unit=unit),self.assertRaises(ValueError):validate_material_catalog(*fixture(number,unit))

    def test_source_polarity_precision_and_signed_intervals(self):
        for number,text in [('-40.00','−40.00'),('-0.00','−0.00'),('40.00','+40.00'),('-120','−1.20 × 10^2')]:
            validate_material_catalog(*fixture(number,text=text))
        for number,text in [('-40.00','40.00'),('40.00','−40.00'),('-0.00','0.00'),('-40.00','−40.0')]:
            with self.assertRaises(ValueError):validate_material_catalog(*fixture(number,text=text))
        for text in ('-90.0 to -50.0','−90.0–−50.0','-90.0 - -50.0'):
            graph=fixture();graph[1]['records'][0]['reported_value']=dict(kind='interval',lower='-90.0',upper='-50.0',value_text=text,
                unit_code='degC',unit_text='°C',endpoint_semantics='source_reported_not_a_confidence_interval')
            validate_material_catalog(*graph)
        for text in ('-90.0--50.0','-90.0 to -50','-50.0 to -90.0'):
            graph=fixture();graph[1]['records'][0]['reported_value']=dict(kind='interval',lower='-90.0',upper='-50.0',value_text=text,
                unit_code='degC',unit_text='°C',endpoint_semantics='source_reported_not_a_confidence_interval')
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();graph[1]['records'][0]['reported_value']=dict(kind='comparison',operator='<=',number='-20.00',value_text='≤ −20.00',unit_code='degC',unit_text='°C')
        validate_material_catalog(*graph)

    def test_temperature_branch_units_target_and_legacy_signed_domains(self):
        for unit in ('MPa','percent','percent_elongation','shore_a_scale','kJ/m^2','degF'):
            graph=fixture();graph[1]['records'][0]['reported_value'].update(unit_code=unit,unit_text=unit)
            self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();graph[1]['records'][0]['specified_elongation']=target_fixture()[1]['records'][0]['specified_elongation']
        self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
        with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for factory in (synthetic_mean_catalog,tear_fixture,impact_fixture,hardness_fixture,elongation_fixture,target_fixture):
            graph=factory();graph[1]['records'][0]['reported_value'].update(number='-1',value_text='-1')
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=synthetic_mean_catalog();graph[1]['records'][0]['reported_value'].update(unit_code='degC',unit_text='°C')
        self.assertFalse(Draft202012Validator(_PROPERTIES_SCHEMA).is_valid(graph[1]))
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_uncertainty_is_unsigned_difference_not_temperature_coordinate(self):
        graph=uncertainty_catalog();prop=graph[1]['records'][0]
        prop.update(quantity='glass_transition_temperature',quantity_dimension='temperature')
        prop['reported_value'].update(number='-40.00',value_text='−40.00',unit_code='degC',unit_text='°C')
        prop['uncertainty'].update(number='0.50',value_text='0.50',unit_code='K',unit_text='K')
        validate_material_catalog(*graph)
        self.assertEqual(prop['reported_value']['number'],'-40.00');self.assertEqual(prop['uncertainty']['number'],'0.50')
        self.assertEqual(prop['uncertainty']['confidence_level']['unit_code'],'percent')
        for amplitude in ('0','400'):
            prop['uncertainty'].update(number=amplitude,value_text=amplitude);validate_material_catalog(*graph)
        # A wide source CI is not silently clipped or recomputed into physical endpoints.
        bad=deepcopy(graph);bad[1]['records'][0]['uncertainty'].update(number='-1',value_text='-1')
        with self.assertRaises(ValueError):validate_material_catalog(*bad)
        bad=deepcopy(graph);bad[1]['records'][0]['uncertainty']['confidence_level']['unit_code']='K'
        with self.assertRaises(ValueError):validate_material_catalog(*bad)
        graph=synthetic_mean_catalog();graph[1]['records'][0]['uncertainty'].update(unit_code='K',unit_text='K')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_reported_absolute_and_relative_measure_roles_keep_scale_caveat(self):
        graph=synthetic_reported_measures_catalog('unnamed_center_sd');prop=graph[1]['records'][0]
        prop.update(quantity='glass_transition_temperature',quantity_dimension='temperature')
        prop['reported_value'].update(number='-40',value_text='-40',unit_code='degC',unit_text='°C')
        prop['uncertainty']['measures'][0]['reported_value'].update(unit_code='K',unit_text='K')
        validate_material_catalog(*graph)
        graph=synthetic_reported_measures_catalog('relative_errors');prop=graph[1]['records'][0]
        prop.update(quantity='glass_transition_temperature',quantity_dimension='temperature')
        prop['reported_value'].update(number='-40',value_text='-40',unit_code='degC',unit_text='°C')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for measure in prop['uncertainty']['measures']:
            measure['note']='Source relative percent descriptor; reference scale/origin unknown, not recalculated.'
        validate_material_catalog(*graph)
        self.assertTrue(all(m['reported_value']['unit_code']=='percent' for m in prop['uncertainty']['measures']))

    def test_four_language_rendering_keeps_raw_negative_value_and_unknown_criterion(self):
        graph=fixture();data=dict(zip(('materials','reference_properties','sources'),graph))
        for language in ('en','zh','ja','de'):
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:data[name]):
                output=render_material_catalog(graph[1],'reference-properties',language)
            for token in (material_labels(language)['code_glass_transition_temperature'],'-40.00','°C','Tg criterion','scan cycle unknown','abstract and table disagree'):
                self.assertIn(token,output)

    def test_generated_schema_fifth_branch_and_catalog_only_contract(self):
        schema=json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(schema,_PROPERTIES_SCHEMA);self.assertEqual(len(schema['$defs']['property']['oneOf']),24)
        Draft202012Validator.check_schema(schema);Draft202012Validator(schema).validate(fixture()[1])
        for update in ({'engineering_allowable':True},{'universal_bound':True},{'evaluation_support':'evaluator_input'},{'quantity_dimension':'pressure'}):
            graph=fixture();graph[1]['records'][0].update(update)
            self.assertFalse(Draft202012Validator(schema).is_valid(graph[1]))
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for factory in (synthetic_mean_catalog,tear_fixture,impact_fixture,hardness_fixture,elongation_fixture,target_fixture):
            graph=factory();Draft202012Validator(schema).validate(graph[1]);validate_material_catalog(*graph)


if __name__=='__main__':unittest.main()
