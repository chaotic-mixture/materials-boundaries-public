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
from materials_query.computed_registry import ComputedRegistry, digest
from materials_query.computed_schema_v2 import reduced_composition, composition_bucket

EXAMPLE=Path(__file__).resolve().parents[2]/'examples/reviewed-computed-v2'


class ReviewedTrancheTests(unittest.TestCase):
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
        self.assertEqual(sha256(self.input_bytes).hexdigest(),'c4130e39d4b698b233fdcf07ad5c3325391479902f41a5a2b80f8d802f6f7ef2')
        self.assertEqual(self.pin['input_file_sha256'],sha256(self.input_bytes).hexdigest())
        self.assertEqual(self.pin['canonical_review_sha256'],digest(self.review))
        self.assertEqual(self.pin['normalized_review_file_sha256'],sha256((EXAMPLE/'normalized-review.json').read_bytes()).hexdigest())
        old=EXAMPLE.parent/'reviewed-computed-seed'
        self.assertEqual(sha256((old/'scoped-review-input.json').read_bytes()).hexdigest(),
            '298e94d77f5166650f66c17ff83e859c6e654f6739745d779a4461310437bb33')

    def test_lossless_transcription_all_24(self):
        self.assertEqual(len(self.review['records']),24)
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
        self.assertEqual(s['scoped_accepted_identity_bucket_count'],24)
        self.assertEqual(s['selected_model_count'],24);self.assertEqual(s['selected_entry_count'],24)
        self.assertEqual(s['related_source_provider_group_count'],30)
        self.assertEqual(s['related_source_calculation_count'],118)
        self.assertEqual(s['legacy_unique_material_count'],1057)
        self.assertFalse(s['cross_namespace_equivalence'])
        self.assertEqual(sum(r['primary_category']=='metal' for r in s['records']),12)
        self.assertEqual(sum(r['primary_category']=='inorganic' for r in s['records']),12)
        self.assertEqual(sum(len(r['overlap_relations']['same_composition_provider_groups'])==2 for r in s['records']),6)
        self.assertEqual(sum(r['formula']!=r['conservative_count_bucket'].split(':',1)[1] for r in s['records']),6)

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
                self.assertFalse(set(value)&{'positions','lattice_vectors','cell_vectors','cartesian_site_positions','fractional_site_positions','raw_archive','potential_files'})
                for v in value.values():no_geometry(v)
            elif isinstance(value,list):
                for v in value:no_geometry(v)
        no_geometry(export.json())

if __name__=='__main__':unittest.main()
