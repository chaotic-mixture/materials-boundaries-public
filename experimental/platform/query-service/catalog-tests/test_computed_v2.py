"""Synthetic contract cases, not scientific acceptance of any source material."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query.computed_registry import ComputedRegistry, digest, validate_review
from materials_query.computed_schema_v2 import COUNT_POLICY, reduced_composition, composition_bucket

INPUT = b'Synthetic metadata only; not a scientific source packet.\n'


def record_fixture():
    return {
        'candidate_id': 'synthetic1', 'decision': 'accepted', 'reason': 'Synthetic contract fixture only',
        'provider': 'nomad', 'provider_entry_id': 'entry1', 'provider_material_id': 'model1',
        'project_material_id': 'computed:nomad:model1',
        'source_url': 'https://nomad-lab.eu/prod/v1/gui/entry/id/entry1',
        'formula': 'Ba2Ni4O8', 'canonical_composition': {'Ba':1,'Ni':2,'O':4},
        'conservative_count_bucket': 'computed-composition:BaNi2O4',
        'primary_category': 'inorganic', 'category_basis': 'Synthetic carbon-free oxide model',
        'electronic_behavior': 'unknown',
        'material_scope': {'kind':'hypothetical_computed_crystal_model','prototype_aflow_id':'A2BC4_cF56_227_d_a_e',
            'space_group_number_provider_reported':227, 'provider_material_id':'model1',
            'phase_identity_confidence':'Synthetic provider-reported identity; no independent symmetry result',
            'experimental_existence':'unknown','phase_stability':'unknown','equilibrium':'unknown','convergence':'unknown',
            'temperature_K':None,'pressure_Pa':None},
        'density': {'value':1234.567890123,'unit':'kg/m^3','evidence_kind':'computed',
            'source_path':'results.properties.structures.structure_original.mass_density'},
        'method': {'parameter_variation_id':'method1','method_name':'DFT','simulation': {
            'program_name':'Synthetic','program_version':'1','dft': {'basis_set_type':'plane waves',
            'core_electron_treatment':'pseudopotential','scf_threshold_energy_change':1e-23,
            'xc_functional_type':'GGA','xc_functional_names':['GGA_X_PBE','GGA_C_PBE']}}},
        'provenance': {'external_db':'Synthetic','last_processing_time':'2026-01-01T00:00:00',
            'license':'CC BY 4.0','mainfile':'synthetic/OUTCAR','nomad_commit':'00000000','nomad_version':'1',
            'references':['https://example.org/synthetic'],'upload_id':'upload1'},
        'attribution':[{'user_id':'synthetic-author','name':'Synthetic Author'}],
        'rights': {'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
            'scope':'Identity and provenance metadata, scalar density and method; no geometry or raw calculations',
            'changes':'Original synthetic notice preserved', 'project_changes':'Composition reduction, count bucketing and bounded overlap annotation'},
        'checks': {**{k:True for k in ('entry_set_complete','source_formula_and_material_match','formula_site_composition_match',
            'source_density_exact_match','source_method_exact_match','source_symmetry_exact_match','source_license_exact_match',
            'source_mainfile_exact_match','periodic_3d','positions_and_sites_match','finite_geometry','finite_positive_density',
            'density_mass_diagnostic_pass','no_duplicate_periodic_sites')},
            'volume_relative_error':0.0,'atomic_density_relative_error':0.0,'density_mass_diagnostic_relative_error':0.0001,
            'density_mass_diagnostic_tolerance':0.002,'minimum_pair_distance_m':2e-10,'geometry_sha256':'a'*64},
        'overlap_relations': {'same_composition_rows_current_OQMD':2,
            'same_composition_provider_groups': {'model1':['entry1','entry2']},
            'query_complete':True,'query_scope':'Synthetic exact formula spellings only; incomplete globally',
            'group_details':[{'provider_material_id':'model1','entry_count':2,'selected_group':True,'space_groups':[227],'mainfiles':['synthetic/OUTCAR']}],
            'relation_to_other_same_composition_groups':'potential_same_material_or_polymorph; not additional count without structural adjudication',
            'prior_seven_hits':[],'other_batch_same_composition_hits':[],'baseline_identifier_or_formula_hits':[],
            'baseline_comparison_scope':'Synthetic test; no novelty assertion',
            'cross_provider_global_equivalence':'unresolved; no global novelty or universal uniqueness claim'},
        'scientific_confidence': {'traceability':'high','composition_and_cell_density_consistency':'high','real_world_predictive_validity':'unassessed'},
        'evidence': {k:'b'*64 for k in ('candidate_packet_sha256','archive_response_sha256','relations_response_sha256','frozen_source_response_sha256','attribution_response_sha256')},
    }


def review_fixture():
    return {'schema':'computed-review/2','input_file_sha256':sha256(INPUT).hexdigest(), 'reviewer':'Synthetic tests',
        'rationale':'No actual admissions', 'count_policy':deepcopy(COUNT_POLICY), 'records':[record_fixture()]}


class RichRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'v2.db'; self.review=review_fixture()

    def registry(self, review=None, path=None, **kw):
        r=review or self.review
        return ComputedRegistry(path or self.path,r,trusted_review_sha256=digest(r),input_file_bytes=INPUT,**kw)

    def test_round_trip_preserves_every_qualifier(self):
        r=self.registry(); s=r.admit(['synthetic1'])
        self.assertEqual(s['records'],self.review['records'])
        self.assertEqual(s['scoped_accepted_identity_bucket_count'],1)
        self.assertEqual(s['selected_entry_count'],1);self.assertEqual(s['selected_model_count'],1)
        self.assertEqual(s['related_source_calculation_count'],2)
        self.assertNotIn('project_unique_material_count',s)
        self.assertEqual(s['input_file_sha256'],sha256(INPUT).hexdigest())
        self.assertEqual(s['canonical_review_sha256'],digest(self.review))

    def test_composition_reduction(self):
        for formula, expected in [('Ba2Ni4O8','BaNi2O4'),('Be2O8Sc4','BeO4Sc2'),('Be2Ca4O8','BeCa2O4'),
            ('Ag2O8Te4','AgO4Te2'),('Ba2O8Sn4','BaO4Sn2'),('Ba2Na4O8','BaNa2O4')]:
            self.assertEqual(composition_bucket(reduced_composition(formula)),'computed-composition:'+expected)
        for formula in ('Xx2O3','Ba0O','Ba01O','Ba-O','Ba2(O4)','BaBaO','Ba1.5O',''):
            with self.assertRaises(ValueError):reduced_composition(formula)

    def test_extra_same_composition_model_and_calculation_do_not_inflate_bucket(self):
        a=self.review['records'][0];b=deepcopy(a)
        b.update(candidate_id='synthetic2',provider_material_id='model2',project_material_id='computed:nomad:model2',provider_entry_id='entry3',source_url='https://nomad-lab.eu/prod/v1/gui/entry/id/entry3')
        b['material_scope']['provider_material_id']='model2'
        for r in (a,b):
            rel=r['overlap_relations'];rel['same_composition_rows_current_OQMD']=3
            rel['same_composition_provider_groups']['model2']=['entry3']
            rel['group_details'].append({'provider_material_id':'model2','entry_count':1,'selected_group':False,'space_groups':[227],'mainfiles':['synthetic/alternate']})
            for g in rel['group_details']:g['selected_group']=g['provider_material_id']==r['provider_material_id']
        self.review['records'].append(b)
        s=self.registry().admit(['synthetic1','synthetic2'])
        self.assertEqual(s['scoped_accepted_identity_bucket_count'],1)
        self.assertEqual((s['selected_entry_count'],s['selected_model_count'],s['related_source_calculation_count'],s['related_source_provider_group_count']),(2,2,3,2))

    def test_atomic_replay_concurrency(self):
        r=self.registry()
        with self.assertRaises(ValueError):r.admit(['synthetic1','missing'])
        self.assertEqual(r.snapshot()['selected_entry_count'],0)
        with ThreadPoolExecutor(6) as pool:results=list(pool.map(lambda _:r.admit(['synthetic1']),range(12)))
        self.assertTrue(all(s==results[0] for s in results))
        self.assertEqual(self.registry().snapshot(),results[0])

    def test_input_and_review_trust_anchors(self):
        for data in (None,b'changed',INPUT+b' '):
            with self.assertRaises(ValueError):ComputedRegistry(self.path,self.review,trusted_review_sha256=digest(self.review),input_file_bytes=data)
        with self.assertRaises(ValueError):ComputedRegistry(self.path,self.review,trusted_review_sha256='0'*64,input_file_bytes=INPUT)
        self.registry()
        changed=deepcopy(self.review);changed['rationale']='A different review cannot silently replace this DB'
        with self.assertRaises(ValueError):self.registry(changed)

    def test_legacy_database_is_not_silently_migrated(self):
        from test_computed_recovery import review_fixture as legacy
        old=legacy();ComputedRegistry(self.path,old,trusted_review_sha256=digest(old))
        with self.assertRaises(ValueError):self.registry()
        new=self.registry(path=Path(self.temp.name)/'separate-v2.db')
        self.assertEqual(new.snapshot()['selected_entry_count'],0)

    def test_duplicate_candidate_or_selected_entry(self):
        for field,value in [('candidate_id','synthetic1'),('provider_entry_id','entry1')]:
            r=deepcopy(self.review); extra=deepcopy(r['records'][0]);extra['candidate_id']='synthetic2';extra['provider_entry_id']='entry2'
            extra[field]=value;extra['source_url']='https://nomad-lab.eu/prod/v1/gui/entry/id/'+extra['provider_entry_id'];r['records'].append(extra)
            with self.assertRaises(ValueError):validate_review(r)

    def test_nested_unknowns_and_geometry_rejected(self):
        for path in [(),('records',0),('records',0,'method'),('records',0,'method','simulation'),
            ('records',0,'material_scope'),('records',0,'rights'),('records',0,'overlap_relations','group_details',0),('records',0,'checks')]:
            r=deepcopy(self.review);target=r
            for k in path:target=target[k]
            target['positions']=[[0,0,0]]
            with self.assertRaises(ValueError):validate_review(r)

    def test_bad_metadata_fails_closed(self):
        mutations=[(('canonical_composition','Ba'),2),(('conservative_count_bucket',),'computed-composition:Fake'),
            (('density','value'),float('nan')),(('density','value'),True),(('density','value'),0),
            (('primary_category',),'metal'),(('material_scope','temperature_K'),300),
            (('material_scope','pressure_Pa'),0),(('material_scope','phase_stability'),'stable'),
            (('electronic_behavior',),'metallic'),(('source_url',),'https://example.org/entry1'),
            (('overlap_relations','same_composition_rows_current_OQMD'),3),
            (('overlap_relations','group_details',0,'entry_count'),3),
            (('provenance','references'),['javascript:alert(1)']), (('attribution',0,'name'),'x'*4097)]
        for path,value in mutations:
            r=deepcopy(self.review);target=r['records'][0]
            for k in path[:-1]:target=target[k]
            target[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(ValueError):validate_review(r)
        r=deepcopy(self.review);r['count_policy']['max_count_per_composition']=2
        with self.assertRaises(ValueError):validate_review(r)

    def test_storage_tampering(self):
        for sql in ("UPDATE metadata SET value='forged' WHERE key='input_file_sha256'",'DELETE FROM admissions',"UPDATE entries SET payload='{}'"):
            p=Path(self.temp.name)/(str(abs(hash(sql)))+'.db');r=self.registry(path=p);r.admit(['synthetic1'])
            with sqlite3.connect(p) as db:db.execute(sql)
            with self.assertRaises(ValueError):r.snapshot()

    def test_api_preserves_scope_sources_and_process_pin(self):
        self.assertFalse(TestClient(create_app()).get('/api/computed/status').json()['enabled'])
        r=self.registry();r.admit(['synthetic1']);client=TestClient(create_app(computed_registry=r))
        s=client.get('/api/computed/status').json();pin={'namespace':'computed',**{k:s[k] for k in ('baseline_version','overlay_version','review_version')}}
        for route,extra in [('list',{}),('search',{'query':'DFT'}),('exact',{'project_material_id':'computed:nomad:model1'}),
            ('source',{'project_material_id':'computed:nomad:model1'}),('property',{'project_material_id':'computed:nomad:model1','property':'density'})]:
            response=client.post('/api/computed/'+route,json=pin|extra)
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.json()['records'],self.review['records'])
            self.assertEqual(response.json()['count_policy'],COUNT_POLICY)
        out=client.post('/api/computed/export',json=pin).json();self.assertEqual(out['records'],self.review['records'])
        self.assertNotIn('"positions":',json.dumps(out));self.assertNotIn('"cell_vectors":',json.dumps(out))
        self.assertEqual(client.post('/api/computed/list',json=pin|{'review_version':'0'*64}).status_code,409)
        self.assertEqual(client.post('/api/computed/list',json=pin|{'path':'/tmp'}).status_code,422)

    def test_export_budget(self):
        r=deepcopy(self.review)
        r['records'][0]['reason']='x'*4097
        with self.assertRaises(ValueError):validate_review(r)

if __name__=='__main__':unittest.main()
