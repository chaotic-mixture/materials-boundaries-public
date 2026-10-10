import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_project_catalog.catalog import RESOURCE_SHA256

class FormalAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client=TestClient(create_app(enable_local_catalog=True))
        cls.status=cls.client.get('/api/catalog/project/status').json()
        cls.version=cls.status['version']

    def post(self,**kw):
        return self.client.post('/api/catalog/project/list',json={'version':self.version,**kw})

    def test_counts_and_no_legacy_rewrite(self):
        self.assertEqual(self.status['counts']['formal_project_admission_count'],1081)
        self.assertEqual(self.client.get('/api/catalog/status').json()['counts']['local_catalog_unique_material_count'],1057)
        self.assertFalse(self.client.get('/api/computed/status').json()['enabled'])

    def test_disabled_by_default(self):
        client=TestClient(create_app())
        self.assertFalse(client.get('/api/catalog/project/status').json()['enabled'])
        self.assertEqual(client.post('/api/catalog/project/list',json={'version':self.version}).status_code,503)

    def test_full_records_and_partitions(self):
        value=self.post(partition='reviewed-computed',limit=100).json()
        self.assertEqual(value['matched_count'],24)
        self.assertEqual(len(value['records']),24)
        self.assertIn('rights',value['records'][0]['model'])
        self.assertIn('overlap_relations',value['records'][0]['model'])
        self.assertEqual(self.post(partition='legacy-source-qualified').json()['matched_count'],1057)

    def test_stale_and_missing_pin(self):
        self.assertEqual(self.post(version='0'*64).status_code,409)
        self.assertEqual(self.client.post('/api/catalog/project/list',json={}).status_code,422)

    def test_bounds_and_injection(self):
        for kw,code in [({'limit':True},422),({'limit':101},422),({'query':'x\n'},400),({'query':' '},400),({'path':'/etc/passwd'},422),({'partition':'experimental'},422),({'record_id':'missing'},404)]:
            self.assertEqual(self.post(**kw).status_code,code)
        for route in ('admit','refresh','upload'):
            self.assertEqual(self.client.post('/api/catalog/project/'+route,json={}).status_code,404)

    def test_drift_disables_only_formal(self):
        with patch.dict(RESOURCE_SHA256,{'formal_computed_review':'0'*64}):
            client=TestClient(create_app(enable_local_catalog=True))
        self.assertFalse(client.get('/api/catalog/project/status').json()['enabled'])
        self.assertTrue(client.get('/api/catalog/status').json()['enabled'])

    def test_ui_safe_rendering_and_visibility(self):
        html=self.client.get('/catalog').text
        js=self.client.get('/static/catalog.js').text
        self.assertIn('Formal project admissions',html)
        self.assertIn('does not assert global physical uniqueness',html)
        self.assertIn('/api/catalog/project/status',js)
        self.assertIn('/api/catalog/project/list',js)
        self.assertNotIn('innerHTML',js)
        self.assertIn('replaceChildren()',js)
        self.assertIn("element('formal-submit').disabled = true",js)
