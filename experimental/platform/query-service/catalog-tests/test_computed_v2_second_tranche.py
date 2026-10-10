"""Pinned, metadata-only tranche transcription and local admission checks.

The source input is not a geometry archive. Acceptance is bounded to the review
pin and is not a global scientific uniqueness assertion.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query.computed_registry import ComputedRegistry, digest, validate_review, canonical
from materials_query.computed_schema_v2 import reduced_composition, composition_bucket

EXAMPLE=Path(__file__).resolve().parents[2]/'examples/reviewed-computed-v2-second'


class ReviewedSecondTrancheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_bytes=(EXAMPLE/'eligible-metadata-input.json').read_bytes()
        cls.input=json.loads(cls.input_bytes)
        cls.review=json.loads((EXAMPLE/'normalized-review.json').read_bytes())
        cls.pin=json.loads((EXAMPLE/'acceptance-pin.json').read_bytes())

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.registry=ComputedRegistry(Path(self.temp.name)/'tranche.db',self.review,
            trusted_review_sha256=self.pin['canonical_review_sha256'],input_file_bytes=self.input_bytes)

    def test_exact_input_review_and_prior_seven_pins(self):
        self.assertEqual(sha256(self.input_bytes).hexdigest(),'41d0691a8289c6d30fc24a5ecaef1f3b3e4b3ded57eac15ea8d64adc8a8398d6')
        self.assertEqual(self.pin['input_file_sha256'],sha256(self.input_bytes).hexdigest())
        self.assertEqual(self.pin['canonical_review_sha256'], '318f12f676ff2db9d2429fa1cfb937cb08d9fa89292dff2a46be87171e113115')
        self.assertEqual(self.pin['normalized_review_file_sha256'], 'f47b5612797661aae68f5d360aeee85c7b6eb3945dad4aeb210b65933bfcc279')
        self.assertEqual(self.pin['canonical_review_sha256'],digest(self.review))
        self.assertEqual(self.pin['normalized_review_file_sha256'],sha256((EXAMPLE/'normalized-review.json').read_bytes()).hexdigest())
        old=EXAMPLE.parent/'reviewed-computed-seed'
        self.assertEqual(sha256((old/'scoped-review-input.json').read_bytes()).hexdigest(),
            '298e94d77f5166650f66c17ff83e859c6e654f6739745d779a4461310437bb33')

    def test_lossless_transcription_all_62(self):
        self.assertEqual(len(self.review['records']),62)
        originals={r['candidate_id']:r for r in self.input['records']}
        for actual in self.review['records']:
            with self.subTest(candidate=actual['candidate_id']):
                expected=deepcopy(originals[actual['candidate_id']]);converted=deepcopy(actual)
                for key in ('provider','project_material_id','reason'):converted.pop(key)
                converted['decision']=expected['decision']
                converted['property']=converted.pop('density')
                converted['rights'].pop('project_changes')
                converted['rights']['scope']=expected['rights']['scope']
                self.assertEqual(converted,expected)
                self.assertEqual(actual['canonical_composition'],reduced_composition(actual['formula']))
                self.assertEqual(actual['conservative_count_bucket'],composition_bucket(actual['canonical_composition']))
                self.assertEqual(actual['density']['value'],expected['property']['value'])
                self.assertIsNone(actual['material_scope']['temperature_K'])
                self.assertIsNone(actual['material_scope']['pressure_Pa'])
                for key in ('experimental_existence','phase_stability','equilibrium','convergence'):
                    self.assertEqual(actual['material_scope'][key],'unknown')
                self.assertEqual(actual['electronic_behavior'],'unknown')

    def test_tranche_counts_relations_and_replay(self):
        ids=[r['candidate_id'] for r in self.review['records']]
        s=self.registry.admit(ids)
        self.assertEqual(self.registry.admit(ids),s)
        self.assertEqual(s['scoped_accepted_identity_bucket_count'],62)
        self.assertEqual(s['selected_model_count'],62);self.assertEqual(s['selected_entry_count'],62)
        self.assertEqual(s['related_source_provider_group_count'],133)
        self.assertEqual(s['related_source_calculation_count'],444)
        self.assertEqual(s['legacy_unique_material_count'],1057)
        self.assertFalse(s['cross_namespace_equivalence'])
        self.assertEqual(sum(r['primary_category']=='metal' for r in s['records']),47)
        self.assertEqual(sum(r['primary_category']=='inorganic' for r in s['records']),15)
        self.assertEqual(sum(len(r['overlap_relations']['same_composition_provider_groups'])>1 for r in s['records']),22)
        self.assertEqual(sum(r['formula']!=r['conservative_count_bucket'].split(':',1)[1] for r in s['records']),8)

    def test_all_api_projections_and_process_pinning(self):
        before=TestClient(create_app(computed_registry=self.registry))
        self.registry.admit([r['candidate_id'] for r in self.review['records']])
        self.assertEqual(before.get('/api/computed/status').json()['selected_entry_count'],0)
        client=TestClient(create_app(computed_registry=self.registry))
        s=client.get('/api/computed/status').json()
        pin={'namespace':'computed',**{k:s[k] for k in ('baseline_version','overlay_version','review_version')}}
        listing=client.post('/api/computed/list',json=pin|{'limit':100}).json()['records']
        expected=sorted(self.review['records'],key=lambda r:r['candidate_id'])
        self.assertEqual(listing,expected)
        for record in expected:
            for route in ('exact','property','source'):
                extra={'project_material_id':record['project_material_id']}
                if route=='property':extra['property']='density'
                response=client.post('/api/computed/'+route,json=pin|extra)
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(response.json()['records'],[record])
        export=client.post('/api/computed/export',json=pin)
        self.assertEqual(export.status_code,200)
        self.assertEqual(export.json()['records'],expected)
        self.assertLess(len(export.content),1048576)
        def no_geometry(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&{'positions','lattice_vectors','cell_vectors','cartesian_site_positions','fractional_site_positions','raw_archive','potential_files','species_at_sites','atomic_positions','potentials','raw_files'})
                for v in value.values():no_geometry(v)
            elif isinstance(value,list):
                for v in value:no_geometry(v)
        no_geometry(export.json())

    def prior(self):
        folder=EXAMPLE.parent/'reviewed-computed-v2'
        return json.loads((folder/'normalized-review.json').read_bytes()), (folder/'eligible-metadata-input.json').read_bytes()

    def combined_test_review(self):
        # Disposable structural/dedup fixture only. This is not an accepted
        # combined review, and the second input anchor is not combined provenance.
        prior,_=self.prior()
        review=deepcopy(self.review)
        review['records']=deepcopy(prior['records'])+review['records']
        return review

    def test_cumulative_counts_disposable_fixture_only(self):
        combined=self.combined_test_review()
        registry=ComputedRegistry(Path(self.temp.name)/'test-only-combined.db', combined,
            trusted_review_sha256=digest(combined),input_file_bytes=self.input_bytes)
        ids=[r['candidate_id'] for r in combined['records']]
        snapshot=registry.admit(ids)
        self.assertEqual(registry.admit(ids),snapshot)
        self.assertEqual(snapshot['scoped_accepted_identity_bucket_count'],86)
        self.assertEqual(snapshot['selected_model_count'],86)
        self.assertEqual(snapshot['selected_entry_count'],86)
        self.assertEqual(snapshot['related_source_provider_group_count'],163)
        self.assertEqual(snapshot['related_source_calculation_count'],562)
        self.assertEqual(snapshot['legacy_unique_material_count'],1057)
        self.assertFalse(snapshot['cross_namespace_equivalence'])
        self.assertEqual(len(canonical(snapshot)),self.pin['combined_test_envelope_bytes'])
        self.assertLess(len(canonical(snapshot)),1048576)

    def test_cross_batch_identity_and_relation_disjointness(self):
        prior,_=self.prior()
        for key in ('candidate_id','provider_entry_id','provider_material_id',
                    'project_material_id','conservative_count_bucket'):
            self.assertFalse({r[key] for r in prior['records']} & {r[key] for r in self.review['records']})
        def relations(review):
            groups=set();entries=set()
            for r in review['records']:
                for group,ids in r['overlap_relations']['same_composition_provider_groups'].items():
                    groups.add(group);entries.update(ids)
            return groups,entries
        a,b=relations(prior),relations(self.review)
        self.assertFalse(a[0]&b[0]);self.assertFalse(a[1]&b[1])

    def test_cross_batch_duplicate_candidate_and_entry_rejected(self):
        for key in ('candidate_id','provider_entry_id'):
            with self.subTest(key=key):
                combined=self.combined_test_review()
                combined['records'][24][key]=combined['records'][0][key]
                with self.assertRaisesRegex(ValueError,'Duplicate candidate or selected entry'):
                    validate_review(combined)
        combined=self.combined_test_review()
        combined['records'].append(deepcopy(combined['records'][0]))
        with self.assertRaises(ValueError):validate_review(combined)

    def test_replay_reopen_and_cross_batch_database_isolation(self):
        ids=[r['candidate_id'] for r in self.review['records']]
        snapshot=self.registry.admit(ids)
        reopened=ComputedRegistry(self.registry.database,self.review,
            trusted_review_sha256=self.pin['canonical_review_sha256'],input_file_bytes=self.input_bytes)
        self.assertEqual(reopened.admit(ids),snapshot)
        prior,prior_bytes=self.prior()
        with self.assertRaisesRegex(ValueError,'Initial baseline and review input cannot be replaced'):
            ComputedRegistry(self.registry.database,prior,
                trusted_review_sha256=digest(prior),input_file_bytes=prior_bytes)
        with self.assertRaises(ValueError):self.registry.admit([prior['records'][0]['candidate_id']])
        self.assertEqual(self.registry.snapshot(),snapshot)
        separate=ComputedRegistry(Path(self.temp.name)/'separate-prior.db',prior,
            trusted_review_sha256=digest(prior),input_file_bytes=prior_bytes)
        self.assertEqual(separate.snapshot()['selected_entry_count'],0)

    def test_default_off_and_held_composition_absent(self):
        default=TestClient(create_app())
        self.assertFalse(default.get('/api/computed/status').json()['enabled'])
        self.assertNotIn('computed-composition:CaCo3',
            {r['conservative_count_bucket'] for r in self.review['records']})
        self.registry.admit([r['candidate_id'] for r in self.review['records']])
        self.assertFalse(TestClient(create_app()).get('/api/computed/status').json()['enabled'])
        self.assertEqual(self.registry.snapshot()['legacy_unique_material_count'],1057)

if __name__=='__main__':unittest.main()
