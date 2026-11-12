"""Fictional temperature response fits;no source data or fit reconstruction."""
from copy import deepcopy
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from jsonschema import Draft202012Validator
from materials_boundaries.database import Database,read_snapshot,ValidationSession
from materials_boundaries.material_references import _PROPERTIES_SCHEMA,validate_material_catalog,resolve_material
from materials_boundaries.material_presentation import material_labels,render_material_catalog
from materials_boundaries._material_derivation import FIT_PROFILE,FIT_METHOD,FIT_EXPRESSION,FIT_UNKNOWNS,validate_derivation
from test_thermal_conductivity_contract import fixture as direct_fixture
from test_thermal_transport_derivation_contract import fixture as product_fixture
from test_material_derivation_contract import synthetic_derived_catalog
from test_material_uncertainty_contract import uncertainty_catalog
from test_tga_endpoint_contract import add_clone

def fixture():
    graph=direct_fixture();p=graph[1]['records'][0];primary=graph[2]['records'][0]
    primary['doi']='10.9999/fictional-primary-fit'
    p.update(quantity='thermal_response_characteristic_time',quantity_dimension='time',evidence_kind='published_measurement_derived_reference',determination_basis='source_reports_calculation',source_property_label='Fictional source temperature-response fit')
    p['reported_value'].update(number='13.400',value_text='13.400',unit_code='s',unit_text='s')
    p['source_document'].update(sha256='b'*64,hash_status='recorded',hash_note=None)
    p['method_definition'].update(type=FIT_METHOD,definition='Fictional source delegates its fit model to an inspected method reference.')
    p['method_definition']['evidence'][0]['supports'].append('classification')
    second=deepcopy(primary);second.update(id='fictional_cited_method',title='Fictional method-only reference',doi='10.9999/fictional-fit-method',urls=['https://example.org/cited-method.pdf'])
    graph[2]['records'].append(second)
    def ev(source,url,tag):return dict(source_id=source,url=url,locator='Fictional selected source paragraph or table',supports=[tag])
    condition=ev(primary['id'],p['source_document']['url'],'condition')
    p['thermal_response_phase']=dict(code='post_stretching_hold',evidence=[condition],notes='Fictional stage,not a new specimen.')
    p['thermal_convection']=dict(status='reported',regime='forced_convection',evidence=[deepcopy(condition)],notes='Fictional boundary,air velocity unspecified.')
    p['derivation']=dict(schema_version='1.0.0',profile_id=FIT_PROFILE,profile_version='1.0.0',kind='source_reported_temperature_response_fit',model=FIT_EXPRESSION,definition='absolute_temperature_deviation_to_fluid_decays_to_initial_divided_by_e',
        primary_delegation=dict(primary_doi=primary['doi'],cited_source_id=second['id'],cited_doi=second['doi'],cited_document_url=second['urls'][0],cited_document_sha256='a'*64,evidence=[ev(primary['id'],p['source_document']['url'],'method')]),
        method_reference=dict(source_id=second['id'],doi=second['doi'],url=second['urls'][0],sha256='a'*64,inspected_on='2026-11-11',inspection_scope='Fictional definition only,not numeric input or current protocol.',use_role='method_definition_only_not_current_protocol_or_numeric_input',evidence=[ev(second['id'],second['urls'][0],'method')]),
        model_context=dict(fluid_temperature='reference_model_assumes_constant',heat_transfer_coefficient='reference_model_assumes_uniform_constant',radiation='reference_model_neglects_radiation',actual_applicability_certified=False),
        unverified_fit_inputs={**{k:None for k in FIT_UNKNOWNS},'unknown_scope_note':'Fictional raw curves,fit settings,baseline treatment,aggregation and per-cell fit count unknown.'},software_fit_performed=False,software_inverse_performed=False)
    return graph

class ThermalResponseFitTests(unittest.TestCase):
    def test_incremental_validation_rechecks_changed_method_source(self):
        graph=fixture();resources=dict(zip(('materials','reference_properties','sources'),graph))
        session=ValidationSession(Database(resources))
        self.assertEqual(session.validate(Database(resources))['reused_property_checks'],1)
        bad=deepcopy(resources);bad['sources']['records'][1]['doi']='10.9999/other'
        with self.assertRaises(ValueError):session.validate(Database(bad))
        changed=deepcopy(resources);changed['sources']['records'][1]['claim_notes'].append('Fictional bibliographic note')
        result=session.validate(Database(changed));self.assertTrue(result['sources_changed']);self.assertEqual(result['executed_property_checks'],1);self.assertEqual(result['reused_property_checks'],0)

    def test_public_schema_and_prior_fourteen_branches_profiles_preserved(self):
        schema=json.loads((Path(__file__).resolve().parents[1]/'schemas/reference_properties.schema.json').read_bytes());self.assertEqual(schema,_PROPERTIES_SCHEMA)
        Draft202012Validator.check_schema(schema)
        digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        old=deepcopy(schema['$defs']['property']['oneOf'][:14]);self.assertEqual(len(schema['$defs']['property']['oneOf']),22)
        for b in old:
            methods=b['properties']['method_definition']['properties']['type']['enum'];self.assertEqual(methods.count(FIT_METHOD),1);methods.remove(FIT_METHOD)
        self.assertEqual(digest(old),'36512d8c2704d24d8f7eff64e71cbfbe9f0e0435b13a5105010eee537dbddcc4')
        self.assertEqual(digest(schema['$defs']['derivation']['oneOf'][:2]),'2d6a65ba81d9b1edaed7f0f26dd74caed5fb847f71ce43e9df35df7439f29d31')
        for graph in (fixture(),product_fixture(),synthetic_derived_catalog(),direct_fixture()):
            Draft202012Validator(schema).validate(graph[1]);validate_material_catalog(*graph)

    def test_positive_scalar_time_and_exact_multiplier_amplitudes(self):
        for unit in ('s','ms'):
            graph=fixture();p=graph[1]['records'][0];p['reported_value'].update(unit_code=unit,unit_text=unit);original=deepcopy(graph)
            validate_material_catalog(*graph);self.assertEqual(graph,original)
        for change in [dict(number='0',value_text='0'),dict(number='-1',value_text='-1'),dict(unit_code='Hz',unit_text='Hz'),dict(unit_text='ms')]:
            graph=fixture();graph[1]['records'][0]['reported_value'].update(change)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=fixture();p=graph[1]['records'][0]
        amp=deepcopy(uncertainty_catalog('reported_plus_minus_unspecified')[1]['records'][0]['uncertainty']);amp.update(number='0',value_text='0',unit_code='s',unit_text='s')
        p.update(uncertainty=amp,uncertainty_status='reported_plus_minus_unspecified');validate_material_catalog(*graph)
        p['uncertainty'].update(unit_code='ms',unit_text='ms')
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_required_relevant_exclusive_phase_and_boundary(self):
        for change in [lambda p:p.pop('thermal_response_phase'),lambda p:p.pop('thermal_convection'),
            lambda p:p['thermal_response_phase'].update(code='during_any_test'),
            lambda p:p['thermal_convection'].update(status='not_applicable'),
            lambda p:p['thermal_convection'].update(status='not_reported_in_inspected_source',regime=None,notes=' ')]:
            graph=fixture();change(graph[1]['records'][0])
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        graph=direct_fixture();graph[1]['records'][0]['thermal_response_phase']=fixture()[1]['records'][0]['thermal_response_phase']
        with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_bidirectional_quantity_method_profile_classification(self):
        changes=[lambda p:p.update(quantity='thermal_conductivity'),lambda p:p['method_definition'].update(type='source_reported_conventional'),
            lambda p:p.update(evidence_kind='published_experimental_reference',determination_basis='source_reports_measurement'),
            lambda p:p.update(density_basis='apparent'),lambda p:p.pop('derivation')]
        for change in changes:
            graph=fixture();p=graph[1]['records'][0];change(p)
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
            with self.assertRaises(ValueError):validate_derivation(p)

    def test_complete_cited_document_doi_hash_role_and_registry_binding(self):
        changes=[lambda d:d['method_reference'].update(sha256='c'*64),
            lambda d:d['method_reference'].update(doi='10.9999/other'),
            lambda d:d['method_reference'].update(use_role='numeric_input'),
            lambda d:d['primary_delegation'].update(cited_document_url='https://example.org/other.pdf'),
            lambda d:d['primary_delegation'].update(primary_doi='10.9999/other'),
            lambda d:d['method_reference'].update(inspected_on='2026-02-30'),
            lambda d:d['method_reference'].update(number='1')]
        for change in changes:
            graph=fixture();change(graph[1]['records'][0]['derivation'])
            with self.assertRaises(ValueError):validate_material_catalog(*graph)
        for edit in ('doi','url','missing'):
            graph=fixture()
            if edit=='doi':graph[2]['records'][1]['doi']='10.9999/other'
            elif edit=='url':graph[2]['records'][1]['urls']=['https://example.org/other.pdf']
            else:graph[2]['records'].pop()
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_primary_phase_delegation_and_secondary_method_evidence_roles(self):
        for part in ('phase','boundary','delegation','method'):
            for key,value in [('source_id','foreign_source'),('url','https://example.org/foreign.pdf'),('supports',['uncertainty'])]:
                graph=fixture();p=graph[1]['records'][0]
                group={'phase':p['thermal_response_phase']['evidence'],'boundary':p['thermal_convection']['evidence'],'delegation':p['derivation']['primary_delegation']['evidence'],'method':p['derivation']['method_reference']['evidence']}[part]
                group[0][key]=value
                with self.assertRaises(ValueError):validate_material_catalog(*graph)

    def test_complete_two_source_query_export_resolve_copy_and_languages(self):
        graph=fixture();resources=dict(zip(('materials','reference_properties','sources'),graph));db=Database(resources)
        rows=list(db.records(quantity='thermal_response_characteristic_time'));expected=deepcopy({r['record_id']:r for r in rows})
        self.assertEqual({s['id'] for s in rows[0]['sources']},{s['id'] for s in graph[2]['records']})
        view=resolve_material(graph[0]['records'][0]['id'],*graph);self.assertEqual({s['id'] for s in view['sources']},{s['id'] for s in graph[2]['records']})
        with tempfile.TemporaryDirectory() as folder:
            db.export(Path(folder)/'fit',quantity='thermal_response_characteristic_time');self.assertEqual(read_snapshot(Path(folder)/'fit')[1],expected)
        rows[0]['property']['derivation']['method_reference']['sha256']='f'*64;rows[0]['sources'][1]['claim_notes'].append('detached')
        self.assertEqual({r['record_id']:r for r in db.records()},expected)
        for lang in ('en','zh','ja','de'):
            with patch('materials_boundaries.catalog.read_catalog',side_effect=lambda n:deepcopy(resources[n])):text=render_material_catalog(graph[1],'reference-properties',lang)
            labels=material_labels(lang)
            for key in ('code_thermal_response_characteristic_time','code_post_stretching_hold','code_forced_convection','thermal_response_fit_notice'):self.assertIn(labels[key],text)
            self.assertIn('13.400',text);self.assertIn('10.9999/fictional-fit-method',text);self.assertNotIn(labels['derived_notice'],text);self.assertNotIn(labels['source_product_notice'],text)

    def test_unknown_statistics_and_semantic_phase_boundary_deduplication(self):
        graph=fixture();p=graph[1]['records'][0];self.assertEqual(p['summary_statistic'],'not_stated');self.assertIsNone(p['sample_count']['value']);self.assertIsNone(p['uncertainty'])
        p['thermal_convection'].update(status='not_reported_in_inspected_source',regime=None,evidence=[],notes='Unknown boundary.')
        clone=add_clone(graph);clone['thermal_convection'].update(status='not_verified',notes='Another unknown wording.')
        with self.assertRaisesRegex(ValueError,'duplicate source fact'):validate_material_catalog(*graph)
        graph=fixture();clone=add_clone(graph);clone['thermal_response_phase']['code']='post_retraction_recovery';validate_material_catalog(*graph)
        graph=fixture();clone=add_clone(graph);clone['thermal_convection']['regime']='natural_convection';validate_material_catalog(*graph)

    def test_no_fit_inverse_or_current_model_certification(self):
        graph=fixture()
        with patch('materials_boundaries._material_derivation.Decimal',side_effect=AssertionError('No fit arithmetic')):validate_material_catalog(*graph)
        for change in [lambda d:d.update(software_fit_performed=True),lambda d:d.update(software_inverse_performed=0),
            lambda d:d['model_context'].update(actual_applicability_certified=True),
            lambda d:d['unverified_fit_inputs'].update(fit_window='0-60s'),
            lambda d:d['unverified_fit_inputs'].update(per_cell_fit_count=6),
            lambda d:d['model_context'].update(heat_transfer_coefficient='verified_uniform')]:
            graph=fixture();change(graph[1]['records'][0]['derivation'])
            with self.assertRaises(ValueError):validate_material_catalog(*graph)

if __name__=='__main__':unittest.main()
