"""Fictional source endsets; unknown criteria never create extra coverage."""
from copy import deepcopy
from decimal import localcontext
import unittest
from unittest.mock import patch
from test_crystallization_phase_contract import fixture as scan_fixture
from test_tga_endpoint_contract import add_clone
from materials_boundaries.material_references import validate_material_catalog
from materials_boundaries.material_presentation import material_labels,render_material_catalog

def fixture():
    graph=scan_fixture();p=graph[1]['records'][0]
    p['quantity']='thermal_degradation_endset_temperature'
    p['source_property_label']='Fictional source endset'
    p.pop('thermal_scan_phase');p.pop('thermal_phase_occurrence_ordinal')
    p['degradation_endset_definition']=dict(status='not_verified',text=None,evidence=deepcopy(p['thermal_scan_definition']['evidence']),notes='Fictional unknown endset criterion;not zero mass.')
    return graph

class EndsetContractTests(unittest.TestCase):
    def test_explicit_unknown_and_reported_criteria(self):
        for known in (False,True):
            graph=fixture();p=graph[1]['records'][0]
            if known:p['degradation_endset_definition'].update(status='reported',text='Fictional source endset algorithm')
            before=deepcopy(graph);validate_material_catalog(*graph);self.assertEqual(graph,before)

    def test_missing_program_and_bad_unknowns_rejected(self):
        for field in ('thermal_scan_definition','degradation_endset_definition'):
            graph=fixture();graph[1]['records'][0].pop(field)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for status,text in [('not_applicable',None),('not_verified','invented'),('reported',None),('reported',' ')]:
            graph=fixture();graph[1]['records'][0]['degradation_endset_definition'].update(status=status,text=text)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_primary_document_roles_required(self):
        for field in ('thermal_scan_definition','degradation_endset_definition'):
            graph=fixture();graph[1]['records'][0][field]['evidence']=[]
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_definition_enrichment_and_numeric_zeros_duplicate_both_orders(self):
        for reverse in (False,True):
            graph=fixture();clone=add_clone(graph);clone['reported_value']['number']='149.000'
            clone['degradation_endset_definition'].update(status='reported',text='Fictional source algorithm')
            if reverse:graph[1]['records'].reverse()
            with localcontext() as context:
                context.prec=2
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_four_language_rendering_retains_unknown_without_phase_fields(self):
        graph=fixture();resources=dict(zip(('materials','reference_properties','sources'),graph))
        for language in ('en','zh','ja','de'):
            labels=material_labels(language)
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda name:deepcopy(resources[name])):
                text=render_material_catalog(graph[1],'reference-properties',language)
            for key in ('code_thermal_degradation_endset_temperature','degradation_endset_definition','code_not_verified','code_nonisothermal_temperature_scan'):self.assertIn(labels[key],text)
            self.assertIn('Fictional unknown endset criterion',text)

class EndsetAmplitudeUnitTests(unittest.TestCase):
    def test_same_code_and_cross_code_for_both_amplitude_representations(self):
        from test_material_uncertainty_contract import uncertainty_catalog
        from test_material_reported_measures_contract import synthetic_reported_measures_catalog
        for measures in (False,True):
            for central in ('degC','K'):
                graph=synthetic_reported_measures_catalog('unnamed_center_sd') if measures else uncertainty_catalog()
                p=graph[1]['records'][0]
                p.update(quantity='thermal_degradation_endset_temperature',quantity_dimension='temperature')
                p['reported_value'].update(number='333',value_text='333',unit_code=central,unit_text='°C' if central=='degC' else 'K')
                evidence=deepcopy(p['method_definition']['evidence'])
                for e in evidence:e['supports']=['method','condition']
                p['thermal_scan_definition']=dict(kind='nonisothermal_temperature_scan',evidence=evidence,notes='Fictional source nonisothermal scan.')
                p['degradation_endset_definition']=dict(status='not_verified',text=None,evidence=deepcopy(evidence),notes='Fictional unknown endset criterion.')
                amplitude=p['uncertainty']['measures'][0]['reported_value'] if measures else p['uncertainty']
                amplitude.update(unit_code=central,unit_text='°C' if central=='degC' else 'K')
                validate_material_catalog(*graph)
                other='K' if central=='degC' else 'degC'
                amplitude.update(unit_code=other,unit_text='K' if other=='K' else '°C')
                with self.assertRaises(ValueError):validate_material_catalog(*graph)
                p['quantity']='glass_transition_temperature';p.pop('thermal_scan_definition');p.pop('degradation_endset_definition')
                validate_material_catalog(*graph)

if __name__=='__main__':unittest.main()
