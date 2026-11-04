"""Fictional electric-field records; no laboratory or engineering assertions."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator,ValidationError
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,validate_material_catalog
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from test_material_reference_contract import synthetic_mean_catalog,synthetic_material_catalog
from test_material_reported_measures_contract import synthetic_reported_measures_catalog

def fixture(unit='kV/mm',number='23.4500'):
    graph=synthetic_mean_catalog();p=graph[1]['records'][0]
    p.update(quantity='dielectric_breakdown_strength',quantity_dimension='electric_field',source_property_label='Fictional AC breakdown field',reporting_basis='not_stated',summary_statistic='not_stated',uncertainty=None,uncertainty_status='not_reported_in_inspected_source')
    p['reported_value'].update(number=number,value_text=number,unit_text=unit,unit_code=unit)
    p['uncertainty_note']='No numeric dispersion supplied; no boxplot or Weibull inference.'
    p['method_definition'].update(definition='Fictional source-reported AC rapid-rise field in oil;frequency and RMS/peak unknown.',extraction_window=None)
    p['sample_count'].update(value=None,relation='not_reported',scope='Independent synthetic measurement count unknown.',source_statement='Fictional source does not specify n.',evidence=[])
    return graph

def shape(graph):Draft202012Validator(_PROPERTIES_SCHEMA).validate(graph[1])

class DielectricBreakdownStrengthContractTests(unittest.TestCase):
    def test_complete_query_export_preserves_each_original_unit_and_unknowns(self):
        for unit in ['V/m','kV/mm']:
            graph=fixture(unit);saved=deepcopy(graph);shape(graph);validate_material_catalog(*graph)
            db=Database(dict(zip(('materials','reference_properties','sources'),graph)))
            rows=list(db.records(quantity='dielectric_breakdown_strength'))
            self.assertEqual([r['property'] for r in rows],graph[1]['records'])
            self.assertEqual(rows[0]['property']['reported_value']['value_text'],'23.4500')
            self.assertEqual(rows[0]['property']['reported_value']['unit_code'],unit)
            self.assertIsNone(rows[0]['property']['uncertainty'])
            self.assertIsNone(rows[0]['property']['sample_count']['value'])
            self.assertEqual(rows[0]['property']['evaluation_support'],'catalog_only')
            self.assertFalse(rows[0]['property']['engineering_allowable'])
            with tempfile.TemporaryDirectory() as folder:
                dest=Path(folder)/'field';db.export(dest,quantity='dielectric_breakdown_strength')
                self.assertEqual(read_snapshot(dest)[1],{r['record_id']:r for r in rows})
            self.assertEqual(graph,saved)

    def test_positive_scalar_interval_and_comparison_source_forms(self):
        values=[dict(kind='scalar',number='2.500',value_text='2.500'),dict(kind='interval',lower='2.00',upper='3.00',value_text='2.00–3.00',endpoint_semantics='source_reported_not_a_confidence_interval'),dict(kind='comparison',operator='>=',number='2.00',value_text='≥2.00')]
        for value in values:
            graph=fixture();graph[1]['records'][0]['reported_value']={**value,'unit_code':'kV/mm','unit_text':'kV/mm'}
            shape(graph);validate_material_catalog(*graph)

    def test_zero_negative_and_precision_reinterpretations_are_rejected(self):
        for number,text in [('0','0'),('-1.00','-1.00'),('23.4500','23.45'),('2.00','2.00 approximate')]:
            graph=fixture(number=number);graph[1]['records'][0]['reported_value']['value_text']=text
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_electric_quantity_rejects_pressure_voltage_frequency_temperature_units(self):
        for unit in ['MPa','GPa','V','kV','Hz','degC','K','mV/mm','kV/m']:
            graph=fixture(unit)
            with self.assertRaises(ValidationError):shape(graph)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for dimension in ['pressure','temperature','dimensionless','mass_per_volume']:
            graph=fixture();graph[1]['records'][0]['quantity_dimension']=dimension
            with self.assertRaises(ValidationError):shape(graph)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_new_units_and_dimension_do_not_enter_legacy_quantities(self):
        for make in [synthetic_mean_catalog,synthetic_material_catalog]:
            for unit in ['V/m','kV/mm']:
                graph=make();graph[1]['records'][0]['reported_value'].update(unit_code=unit,unit_text=unit)
                with self.assertRaises(ValidationError):shape(graph)
                with self.assertRaises(ValueError):validate_material_catalog(*graph)
            graph=make();graph[1]['records'][0]['quantity_dimension']='electric_field'
            with self.assertRaises(ValidationError):shape(graph)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_absolute_sd_is_nonnegative_and_exact_same_unit_without_conversion(self):
        graph=fixture();p=graph[1]['records'][0];p.update(summary_statistic='reported_mean',reporting_basis='reported_summary',uncertainty_status='reported_standard_deviation')
        p['uncertainty']=deepcopy(synthetic_mean_catalog()[1]['records'][0]['uncertainty'])
        p['uncertainty'].update(number='0.00',value_text='0.00',unit_code='kV/mm',unit_text='kV/mm')
        shape(graph);validate_material_catalog(*graph)
        for unit in ['V/m','MPa']:
            bad=deepcopy(graph);bad[1]['records'][0]['uncertainty'].update(unit_code=unit,unit_text=unit)
            with self.assertRaises(ValueError):validate_material_catalog(*bad)
        bad=deepcopy(graph);bad[1]['records'][0]['uncertainty'].update(number='-0.01',value_text='-0.01')
        with self.assertRaises(ValueError):validate_material_catalog(*bad)

    def test_reported_measure_envelope_reuses_absolute_role_without_conversion(self):
        graph=synthetic_reported_measures_catalog('unnamed_center_sd');p=graph[1]['records'][0]
        p.update(quantity='dielectric_breakdown_strength',quantity_dimension='electric_field',source_property_label='Fictional electric-field result')
        p['reported_value'].update(unit_code='kV/mm',unit_text='kV/mm')
        absolute=[]
        for measure in p['uncertainty']['measures']:
            if measure['basis']=='absolute' and measure['availability']=='numeric_reported':
                measure['reported_value'].update(unit_code='kV/mm',unit_text='kV/mm');absolute.append(measure)
        self.assertTrue(absolute);shape(graph);validate_material_catalog(*graph)
        bad=deepcopy(graph)
        next(m for m in bad[1]['records'][0]['uncertainty']['measures'] if m['basis']=='absolute' and m['availability']=='numeric_reported')['reported_value'].update(unit_code='V/m',unit_text='V/m')
        with self.assertRaises(ValueError):validate_material_catalog(*bad)

    def test_literal_unit_label_must_match_code_without_scale_reinterpretation(self):
        for label in ['V/m','MPa','kv/mm']:
            graph=fixture();graph[1]['records'][0]['reported_value']['unit_text']=label
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_irrelevant_descriptors_and_allowable_claims_are_rejected(self):
        for field,value in [('specified_elongation',{'number':'100'}),('density_basis','bulk'),('engineering_allowable',True),('universal_bound',True)]:
            graph=fixture();graph[1]['records'][0][field]=value
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_four_language_metadata_retains_original_field_unit_and_unknowns(self):
        graph=fixture();resources=dict(zip(('materials','reference_properties','sources'),graph))
        for language in ['en','zh','ja','de']:
            labels=material_labels(language)
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:deepcopy(resources[n])):
                rendered=render_material_catalog(graph[1],'reference-properties',language)
            self.assertIn(labels['code_dielectric_breakdown_strength']+' [dielectric_breakdown_strength]',rendered)
            self.assertIn('23.4500',rendered);self.assertIn('kV/mm',rendered)
            self.assertIn('frequency and RMS/peak unknown',rendered)

if __name__=='__main__':unittest.main()
