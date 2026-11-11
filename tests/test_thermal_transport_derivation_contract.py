"""Fictional source-product provenance;never reconstruct raw thermal inputs."""
from copy import deepcopy
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from jsonschema import Draft202012Validator
from materials_boundaries._material_derivation import TRANSPORT_PROFILE,TRANSPORT_METHOD,TRANSPORT_KIND,TRANSPORT_EXPRESSION,TRANSPORT_ROLES,TRANSPORT_UNKNOWNS
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,validate_material_catalog
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from materials_boundaries.database import Database,read_snapshot
from test_thermal_conductivity_contract import fixture as direct_fixture
from test_material_derivation_contract import synthetic_derived_catalog
from test_material_uncertainty_contract import uncertainty_catalog
from test_tga_endpoint_contract import add_clone

def fixture():
    graph=direct_fixture('W/(m*K)','0.1230');p=graph[1]['records'][0]
    p.update(evidence_kind='published_measurement_derived_reference',determination_basis='source_reports_calculation')
    p['method_definition'].update(type=TRANSPORT_METHOD,definition='Fictional source explicitly calculates conductivity from measured thermal inputs;actual paired inputs unknown.')
    p['method_definition']['evidence'][0]['supports'].append('classification')
    p['basis_note']='Fictional source calculation,not an independently measured heat-flow-plate result.'
    def ev(tag):return dict(source_id=p['source_id'],url=p['source_document']['url'],locator='Fictional selected table or method',supports=[tag])
    p['derivation']=dict(schema_version='1.0.0',profile_version='1.0.0',profile_id=TRANSPORT_PROFILE,kind=TRANSPORT_KIND,
        formula=dict(expression=TRANSPORT_EXPRESSION,evidence=[ev('method')]),
        contextual_inputs={q:dict(quantity=q,role='source_context_not_verified_actual_input',source_property_label='Fictional '+q,evidence=[ev('reported_value')]) for q in TRANSPORT_ROLES},
        input_provenance={**{n:None for n in TRANSPORT_UNKNOWNS},'unknown_scope_note':'Fictional actual inputs,pairing,temperature,order,covariance and propagation unknown.'},
        software_calculation_performed=False,software_uncertainty_propagation_performed=False)
    return graph

class ThermalTransportDerivationTests(unittest.TestCase):
    def test_source_unit_typography_preserves_role_and_multiplier(self):
        graph=fixture();p=graph[1]['records'][0]
        p['reported_value']['unit_text']='W/m·K';validate_material_catalog(*graph)
        for mutation in [dict(unit_code='mW/(m*K)'),dict(unit_text='mW/m·K'),dict(unit_text='W/mK')]:
            bad=deepcopy(graph);bad[1]['records'][0]['reported_value'].update(mutation)
            with self.assertRaises(ValueError):validate_material_catalog(*bad)

    def test_disjoint_schema_preserves_old_wood_profile(self):
        schema=json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes())
        self.assertEqual(schema,_PROPERTIES_SCHEMA);Draft202012Validator.check_schema(schema)
        old,new,fit=schema['$defs']['derivation']['oneOf']
        self.assertEqual(fit['properties']['profile_id']['const'],'thermal_temperature_decay_fit_with_cited_method_v1')
        self.assertEqual(hashlib.sha256(json.dumps(old,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'cc60366b0c11aaaf5aaaa30e6f9d43e8db3c57a2e0eedb9802acb4513945df21')
        original_branches=deepcopy(schema['$defs']['property']['oneOf'][:14])
        for branch in original_branches:
            methods=branch['properties']['method_definition']['properties']['type']['enum']
            self.assertEqual(methods.count(TRANSPORT_METHOD),1);methods.remove(TRANSPORT_METHOD)
            self.assertEqual(methods.count('source_reported_thermal_response_fit'),1);methods.remove('source_reported_thermal_response_fit')
        self.assertEqual(hashlib.sha256(json.dumps(original_branches,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'da4c82b36aa69587077b5023afe935aebc94ed6769a1abc613d91bfb374f55bc')
        for graph in (fixture(),synthetic_derived_catalog(),direct_fixture()):
            Draft202012Validator(schema).validate(graph[1]);validate_material_catalog(*graph)

    def test_bidirectional_method_profile_and_classification(self):
        changes=[lambda p:p.pop('derivation'),lambda p:p['method_definition'].update(type='source_reported_conventional'),
            lambda p:p.update(evidence_kind='published_experimental_reference',determination_basis='source_reports_measurement'),
            lambda p:p.update(evidence_kind='published_computational_reference'),
            lambda p:p.update(density_basis='apparent'),lambda p:p.update(quantity='mass_density'),
            lambda p:p['derivation'].update(profile_id='unreviewed'),lambda p:p['derivation'].update(kind='conversion_derived_estimate_from_measured_input')]
        for change in changes:
            graph=fixture();change(graph[1]['records'][0])
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        wood=synthetic_derived_catalog();wood[1]['records'][0]['derivation']=fixture()[1]['records'][0]['derivation']
        with self.assertRaises(ValueError):validate_material_catalog(*wood)
        product=fixture();product[1]['records'][0]['derivation']=synthetic_derived_catalog()[1]['records'][0]['derivation']
        with self.assertRaises(ValueError):validate_material_catalog(*product)

    def test_closed_context_rejects_actual_inputs_pairing_and_calculation(self):
        changes=[lambda d:d['contextual_inputs'].pop('mass_density'),
            lambda d:d['contextual_inputs']['mass_density'].update(number='0.9'),
            lambda d:d['contextual_inputs']['mass_density'].update(quantity='thermal_diffusivity'),
            lambda d:d['input_provenance'].update(actual_paired_input_values=[1,2,3]),
            lambda d:d['input_provenance'].update(actual_specimen_pairing=True),
            lambda d:d['input_provenance'].update(density_temperature_alignment='20C'),
            lambda d:d['input_provenance'].update(unknown_scope_note=' '),
            lambda d:d.update(software_calculation_performed=True),
            lambda d:d.update(software_uncertainty_propagation_performed=True),
            lambda d:d['formula'].update(expression='lambda = alpha * cp'),
            lambda d:d['formula'].update(coefficient='1')]
        for change in changes:
            graph=fixture();change(graph[1]['records'][0]['derivation'])
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_primary_document_evidence_required_for_every_context(self):
        for role in ('formula',*TRANSPORT_ROLES):
            for key,value in [('url','https://example.org/other'),('source_id','other'),('supports',['condition'])]:
                graph=fixture();d=graph[1]['records'][0]['derivation']
                evidence=d['formula']['evidence'] if role=='formula' else d['contextual_inputs'][role]['evidence']
                evidence[0][key]=value
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_complete_queries_exports_copy_and_four_language_notice(self):
        graph=fixture();resources=dict(zip(('materials','reference_properties','sources'),graph));db=Database(resources)
        expected=deepcopy({r['record_id']:r for r in db.records(quantity='thermal_conductivity')})
        with tempfile.TemporaryDirectory() as folder:
            db.export(Path(folder)/'product',quantity='thermal_conductivity');self.assertEqual(read_snapshot(Path(folder)/'product')[1],expected)
        row=next(db.records());row['property']['derivation']['input_provenance']['unknown_scope_note']='detached'
        self.assertEqual({r['record_id']:r for r in db.records()},expected)
        for lang in ('en','zh','ja','de'):
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:deepcopy(resources[n])):
                rendered=render_material_catalog(graph[1],'reference-properties',lang)
            labels=material_labels(lang)
            for key in ('code_source_reported_thermal_transport_product','source_product_derivation','source_product_notice'):self.assertIn(labels[key],rendered)
            self.assertNotIn(labels['derived_notice'],rendered);self.assertIn('0.1230',rendered)

    def test_source_statistics_and_amplitudes_not_inferred_from_formula(self):
        graph=fixture();p=graph[1]['records'][0]
        amplitude=deepcopy(uncertainty_catalog('reported_plus_minus_unspecified')[1]['records'][0]['uncertainty'])
        amplitude.update(unit_code='W/(m*K)',unit_text='W/(m·K)')
        p.update(uncertainty=amplitude,uncertainty_status='reported_plus_minus_unspecified')
        original=deepcopy(graph);validate_material_catalog(*graph);self.assertEqual(graph,original)
        self.assertEqual(p['summary_statistic'],'not_stated');self.assertIsNone(p['sample_count']['value'])
        p['uncertainty'].update(unit_code='mW/(m*K)',unit_text='mW/(m·K)')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_no_arithmetic_or_note_based_duplicate_facts(self):
        graph=fixture()
        with patch('materials_boundaries._material_derivation.Decimal',side_effect=AssertionError('No thermal product arithmetic')):
            validate_material_catalog(*graph)
        clone=add_clone(graph);clone['derivation']['input_provenance']['unknown_scope_note']='Different unknown wording'
        with self.assertRaisesRegex(ValueError,'duplicate source fact'):validate_material_catalog(*graph)

if __name__=='__main__':unittest.main()
