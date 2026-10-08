import concurrent.futures
import copy
from pathlib import Path
from threading import Event
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query import local_catalog as lc
try:
    from materials_query import catalog_snapshot as cs
except ModuleNotFoundError as error:
    if error.name != 'materials_boundaries': raise
    raise unittest.SkipTest('Optional repository core is not installed; see LOCAL_CATALOG.md') from error

class CatalogAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spy = patch.object(cs.contracts, 'validate_material_catalog', wraps=cs.contracts.validate_material_catalog)
        cls.validator = cls.spy.start()
        cls.app = create_app(enable_local_catalog=True)
        cls.client = TestClient(cls.app)
        cls.status = cls.client.get('/api/catalog/status').json()
        assert cls.status['enabled'], cls.status
        cls.version = cls.status['version']
        cls.first = cls.client.post('/api/catalog/search', json={'version':cls.version,'query':'a','limit':1}).json()['result']['records'][0]

    @classmethod
    def tearDownClass(cls): cls.spy.stop()
    def post(self, route, **data): return self.client.post('/api/catalog/'+route, json={'version':self.version, **data})
    def test_01_validation_once(self):
        self.assertEqual(self.validator.call_count,1)
        for _ in range(10): self.post('resolve',state_id=self.first['id']).raise_for_status()
        self.assertEqual(self.validator.call_count,1)
    def test_02_metadata_counts_and_versions(self):
        self.assertEqual(self.client.get('/api/health').json()['service_version'],'0.2.0.dev0')
        self.assertEqual(self.client.get('/openapi.json').json()['info']['version'],'0.2.0.dev0')
        from materials_platform import __version__ as umbrella_version
        self.assertEqual(umbrella_version,'0.2.0.dev0')
        self.assertEqual(self.status['counts']['local_catalog_unique_material_count'],1057)
        self.assertFalse(self.status['provider_counts_combined'])
        for name in ('version','content_digest','runtime_digest'): self.assertRegex(self.status[name],r'^[a-f0-9]{64}$')
    def test_03_exact_baseline_parity(self):
        from materials_boundaries.catalog import query_catalog
        for kind,rid in [('materials',self.first['id']),('reference-properties',self.first['property_ids'][0])]:
            response=self.post('exact',kind=kind,record_id=rid)
            self.assertEqual(response.json()['result'],query_catalog(kind,record_id=rid))
    def test_04_resolution_baseline_parity(self):
        from materials_boundaries.material_references import resolve_material
        from materials_boundaries.catalog import read_catalog
        self.assertEqual(self.post('resolve',state_id=self.first['id']).json()['result'],resolve_material(self.first['id'],*(read_catalog(k) for k in ('materials','reference_properties','sources'))))
    def test_05_copy_isolation(self):
        expected=self.post('resolve',state_id=self.first['id']).json()
        mutated=copy.deepcopy(expected); mutated['result']['state'].clear();mutated['result']['sources'].clear()
        self.assertEqual(expected,self.post('resolve',state_id=self.first['id']).json())
        meta=self.client.get('/api/catalog/status').json();meta['counts'].clear()
        self.assertEqual(self.status,self.client.get('/api/catalog/status').json())
    def test_06_record_kinds(self):
        resolved=self.post('resolve',state_id=self.first['id']).json()['result']
        for kind,row in [('identities',resolved['identity']),('materials',resolved['state']),('reference-properties',resolved['properties'][0]),('sources',resolved['sources'][0])]:
            self.assertEqual(self.post('record',kind=kind,record_id=row['id']).json()['result'],row)
        if resolved['grade']:self.assertEqual(self.post('record',kind='grades',record_id=resolved['grade']['id']).json()['result'],resolved['grade'])
    def test_07_stale_pin(self):
        self.assertEqual(self.client.post('/api/catalog/search',json={'version':'0'*64,'query':'wood'}).status_code,409)
    def test_08_missing_pin(self): self.assertEqual(self.client.post('/api/catalog/search',json={'query':'wood'}).status_code,422)
    def test_09_unknown_id(self): self.assertEqual(self.post('resolve',state_id='unknown').status_code,404)
    def test_10_invalid_search(self):
        for q,code in [('',422),(' '*3,400),('x'*257,422),(' '.join(['a']*17),400)]:self.assertEqual(self.post('search',query=q).status_code,code)
        for limit in (0,101,True,1.0):self.assertEqual(self.post('search',query='wood',limit=limit).status_code,422)
    def test_11_no_paths_mutation_or_extra_fields(self):
        self.assertEqual(self.post('search',query='wood',path='/tmp/x').status_code,422)
        for route in ('refresh','reload','upload'):self.assertEqual(self.post(route).status_code,404)
        self.assertEqual(self.client.put('/api/catalog/status',json={}).status_code,405)
    def test_12_parallel_reads(self):
        def read(_):
            response=self.post('resolve',state_id=self.first['id'])
            return response.status_code,response.json()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(read,range(32)))
        expected=self.post('resolve',state_id=self.first['id']).json()
        self.assertTrue(any(code==200 for code,_ in results))
        for code,value in results:self.assertIn(code,(200,429));self.assertTrue(code==429 or value==expected)
    def test_13_concurrency_bound_release(self):
        entered=[Event(),Event()];release=Event();counter=[]
        original=cs.CatalogSnapshot.resolve
        def blocked(snapshot,state):
            index=len(counter);counter.append(index);entered[index].set();release.wait(5);return original(snapshot,state)
        with patch.object(cs.CatalogSnapshot,'resolve',blocked):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                a=pool.submit(self.post,'resolve',state_id=self.first['id']);self.assertTrue(entered[0].wait(3))
                b=pool.submit(self.post,'resolve',state_id=self.first['id']);self.assertTrue(entered[1].wait(3))
                try:self.assertEqual(self.post('resolve',state_id=self.first['id']).status_code,429)
                finally:release.set()
                self.assertEqual(a.result().status_code,200);self.assertEqual(b.result().status_code,200)
        self.assertEqual(self.post('resolve',state_id=self.first['id']).status_code,200)
    def test_14_local_origin_and_body_bounds(self):
        self.assertEqual(self.client.post('/api/catalog/search',json={},headers={'Origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/catalog/search',content=b'x'*32769).status_code,413)
    def test_15_ui_static(self):
        self.assertEqual(self.client.get('/catalog').status_code,200)
        js=self.client.get('/static/catalog.js').text
        self.assertNotIn('innerHTML',js);self.assertIn('textContent',js);self.assertIn('value.version !== version',js)
    def test_16_disabled_mp_unchanged(self):
        self.assertEqual(self.client.post('/api/search',json={'provider':'materials_project','formula':'Si'}).status_code,503)
        self.assertIsNone(self.client.post('/api/demo',json={'provider':'nomad'}).json()['counts']['unique_material_count'])

class Initialization(unittest.TestCase):
    def test_default_no_core_load(self):
        with patch.object(lc,'load_installed_snapshot',side_effect=AssertionError('must not load')):
            self.assertEqual(TestClient(create_app()).get('/api/catalog/status').json()['reason'],'not_enabled')
    def test_missing_core_disabled(self):
        with patch.object(lc,'find_spec',return_value=None):
            client=TestClient(create_app(enable_local_catalog=True))
            self.assertEqual(client.get('/api/catalog/status').json()['reason'],'core_not_installed')
            self.assertEqual(client.post('/api/catalog/search',json={'version':'0'*64,'query':'wood'}).status_code,503)
            self.assertEqual(client.get('/api/health').status_code,200)
    def test_import_discovery_failure_disabled(self):
        with patch.object(lc,'find_spec',side_effect=ValueError('invalid import state')):
            self.assertEqual(TestClient(create_app(enable_local_catalog=True)).get('/api/catalog/status').json()['reason'],'core_initialization_failed')
    def test_validation_failure_disabled(self):
        with patch.object(cs.CatalogSnapshot,'from_packaged',side_effect=ValueError('/private/path broken')):
            client=TestClient(create_app(enable_local_catalog=True));response=client.get('/api/catalog/status')
            self.assertEqual(response.json()['reason'],'core_initialization_failed');self.assertNotIn('/private',response.text)
    def test_revision_module_byte_parity(self):
        import hashlib
        self.assertEqual(hashlib.sha256(Path(cs.__file__).read_bytes()).hexdigest(),'75f63efb42f419eeae0fd08db63369350d603c52f01c4149915f048d74d6cc12')
