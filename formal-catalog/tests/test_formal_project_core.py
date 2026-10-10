import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from materials_project_catalog.catalog import formal_project_catalog, select_formal_catalog, RESOURCE_SHA256
from materials_boundaries.catalog import read_catalog, CatalogLookupError
from materials_boundaries.material_references import material_quota_coverage

class FormalProjectCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = formal_project_catalog()

    def test_exact_counts_and_categories(self):
        self.assertEqual(self.snapshot['counts'], {'formal_project_admission_count':1081,
            'legacy_source_qualified_identity_count':1057,'reviewed_computed_composition_count':24,
            'categories':{'natural':1010,'metal':26,'inorganic':28,'polymer':14,'composite':3}})
        self.assertEqual(len({r['id'] for r in self.snapshot['records']}),1081)

    def test_full_legacy_identity_parity(self):
        self.assertEqual([r['identity'] for r in self.snapshot['records'] if r['partition']=='legacy-source-qualified'],read_catalog('materials')['identities'])
        coverage=material_quota_coverage(*(read_catalog(k) for k in ('materials','reference_properties','sources')))
        self.assertEqual(coverage['distinct_material_count'],1057)

    def test_exact_normalized_review_bytes(self):
        from importlib.resources import files
        raw=files('materials_project_catalog').joinpath('data','formal_computed_review.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'a285523b2b2fdbf0d750ce6ac56e3abfb80d5c42056229a2352b016a787fd875')
        expected=json.loads(raw)['records']
        actual=[r['model'] for r in self.snapshot['records'] if r['partition']=='reviewed-computed']
        self.assertEqual(actual,expected)
        self.assertEqual(len({r['conservative_count_bucket'] for r in actual}),24)
        self.assertEqual(len({x for r in actual for x in r['overlap_relations']['same_composition_provider_groups']}),30)
        self.assertEqual(len({x for r in actual for v in r['overlap_relations']['same_composition_provider_groups'].values() for x in v}),118)

    def test_computed_unknowns_and_evidence_preserved(self):
        for r in select_formal_catalog(self.snapshot,partition='reviewed-computed')['records']:
            m=r['model']
            self.assertEqual(m['density']['evidence_kind'],'computed')
            for k in ('experimental_existence','phase_stability','equilibrium','convergence'):
                self.assertEqual(m['material_scope'][k],'unknown')
            self.assertIsNone(m['material_scope']['temperature_K'])
            self.assertIsNone(m['material_scope']['pressure_Pa'])
            self.assertEqual(m['electronic_behavior'],'unknown')
            for k in ('attribution','rights','method','provenance','overlap_relations','evidence'):
                self.assertTrue(m[k])

    def test_pagination_complete_and_detached(self):
        rows=[]
        for offset in range(0,1081,100):
            rows.extend(select_formal_catalog(self.snapshot,offset=offset)['records'])
        self.assertEqual(rows,self.snapshot['records'])
        rows[0]['identity'].clear()
        self.assertTrue(self.snapshot['records'][0]['identity'])

    def test_exact_search_and_partitions(self):
        r=select_formal_catalog(self.snapshot,query='Ag2AlCo',partition='reviewed-computed')['records'][0]
        self.assertEqual(select_formal_catalog(self.snapshot,record_id=r['id'])['records'],[r])
        self.assertEqual(select_formal_catalog(self.snapshot,query='Ag2AlCo',partition='legacy-source-qualified')['matched_count'],0)
        with self.assertRaises(CatalogLookupError): select_formal_catalog(self.snapshot,record_id='prior-seven')

    def test_bounds(self):
        for kw in ({'limit':True},{'limit':101},{'offset':-1},{'partition':'experimental'}, {'query':' '},{'query':'x\n'},{'query':'a '*17},{'query':'x'*257}):
            with self.assertRaises(ValueError): select_formal_catalog(self.snapshot,**kw)

    def test_pin_drift_fail_closed(self):
        with patch.dict(RESOURCE_SHA256, {'formal_computed_review':'0'*64}):
            with self.assertRaises(ValueError): formal_project_catalog()

    def test_policy_never_global_uniqueness(self):
        self.assertEqual(self.snapshot['count_policy']['physical_global_uniqueness'],'unasserted')
        self.assertIn('Prior seven',self.snapshot['count_policy']['excluded'])

    def test_cli_status_and_list(self):
        status=subprocess.run([sys.executable,'-m','materials_project_catalog'],capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(status.stdout)['counts'],self.snapshot['counts'])
        selected=subprocess.run([sys.executable,'-m','materials_project_catalog','--partition','reviewed-computed'],capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(selected.stdout)['matched_count'],24)
        invalid=subprocess.run([sys.executable,'-m','materials_project_catalog','--list','--limit','101'],capture_output=True,text=True)
        self.assertEqual(invalid.returncode,2)

    def test_cli_status_cannot_bypass_bounds(self):
        for flags in (['--offset','-1'], ['--limit','999'], ['--query','']):
            result=subprocess.run([sys.executable,'-m','materials_project_catalog',*flags],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
