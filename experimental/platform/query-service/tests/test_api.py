import json
from pathlib import Path
import unittest
import httpx
from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_federation.providers import NomadAdapter, ProviderError

RAW=json.loads((Path(__file__).parents[1]/'materials_query/fixtures/nomad_archive_projected.json').read_text())
class ApiTests(unittest.TestCase):
 def setUp(self):
  self.calls=[]
  def transport(request):
   self.calls.append(request)
   if request.method=='POST':return httpx.Response(200,json={'data':{'archive':RAW}})
   return httpx.Response(200,json={'data':[RAW], 'pagination':{'total':73,'next_page_after_value':'opaque'}})
  self.client=TestClient(create_app(NomadAdapter(transport=httpx.MockTransport(transport),fixture=True)))
 def query(self,**kw):return self.client.post('/api/search',json={'formula':'CaFe2Re','limit':1,**kw})
 def test_health_not_upstream(self):
  self.assertEqual(self.client.get('/api/health').json()['upstream_health'],'not_checked');self.assertFalse(self.calls)
 def test_query_count_not_materials(self):
  r=self.query();self.assertEqual(r.status_code,200);d=r.json();self.assertEqual(d['counts']['matching_provider_entries'],73);self.assertIsNone(d['counts']['unique_material_count']);self.assertEqual(d['counts']['quota_credit'],0)
 def test_source_units_and_export(self):
  c=self.query().json()['page']['candidates'][0];r=self.client.get('/api/records/'+c['snapshot_id']);self.assertEqual(r.json(),c);self.assertEqual(c['structure'],RAW['results']['properties']['structures']['structure_original']);self.assertIsNone(c['canonical_material_id']);self.assertEqual(c['properties'][0]['unit'],'kg/m^3');self.assertEqual(c['review_status'],'pending_review')
 def test_experimental_not_inferred(self):
  d=self.query(evidence_kind='experimental').json();self.assertEqual(d['page']['candidates'],[]);self.assertEqual(d['counts']['fetched_entries'],1);self.assertEqual(d['counts']['matching_provider_entries'],73)
 def test_computed_filter(self):self.assertEqual(self.query(evidence_kind='computed').json()['counts']['returned_entries'],1)
 def test_unknown_absent_properties(self):
  raw=json.loads(json.dumps(RAW));raw['results']['properties']={}
  c=TestClient(create_app(NomadAdapter(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[raw]})),fixture=True)))
  self.assertEqual(c.post('/api/search',json={'formula':'CaFe2Re','evidence_kind':'unknown'}).json()['counts']['returned_entries'],1)
 def test_mp_not_configured(self):self.assertEqual(self.query(provider='materials_project').status_code,503);self.assertFalse(self.calls)
 def test_fixture_demo_separate(self):
  d=self.client.post('/api/demo',json={'provider':'materials_project'}).json();self.assertTrue(d['page']['fixture']);self.assertTrue(d['page']['candidates'][0]['source']['fixture']);self.assertFalse(self.calls)
 def test_validation(self):
  for update in [{'limit':0},{'limit':26},{'limit':True},{'formula':'*'},{'formula':' '},{'formula':'a\n'},{'provider':'evil'},{'extra':'x'},{'enrich_first':'yes'}]:
   self.assertEqual(self.query(**update).status_code,422,update)
 def test_batch_bounds(self):
  for qs in [[],[{'formula':'Fe'}]*4,[{'formula':'Fe','limit':15}]*2,[{'formula':'Fe','enrich_first':True}]]:
   self.assertEqual(self.client.post('/api/batch',json={'queries':qs}).status_code,422)
 def test_batch_partial(self):
  d=self.client.post('/api/batch',json={'queries':[{'formula':'CaFe2Re','limit':1},{'formula':'Fe','provider':'materials_project'}]}).json();self.assertEqual(d['status'],'partial');self.assertEqual(len(d['results']),2);self.assertIsNone(d['unique_material_count'])
 def test_provider_failure_sanitized(self):
  def fail(r):raise httpx.ReadTimeout('secret-bearing upstream message')
  c=TestClient(create_app(NomadAdapter(transport=httpx.MockTransport(fail))))
  r=c.post('/api/search',json={'formula':'Fe'});self.assertEqual(r.status_code,502);self.assertNotIn('secret',r.text)
 def test_malformed_upstream_pagination(self):
  c=TestClient(create_app(NomadAdapter(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[RAW],'pagination':'schema changed'})))))
  r=c.post('/api/search',json={'formula':'CaFe2Re','limit':1})
  self.assertEqual(r.status_code,502);self.assertEqual(r.json()['status'],'provider_error')
 def test_archive_bounded(self):
  d=self.query(enrich_first=True).json();self.assertEqual(d['status'],'success');self.assertEqual(len(self.calls),2);self.assertTrue(any('search_snapshot_id' in w for w in d['warnings']))
 def test_archive_failure_retains_search(self):
  class Adapter:
   def search(_,q):return NomadAdapter(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[RAW]})),fixture=True).search(q)
   def enrich_archive(_,c):raise ProviderError('no')
  c=TestClient(create_app(Adapter()));d=c.post('/api/search',json={'formula':'CaFe2Re','enrich_first':True}).json();self.assertEqual(d['status'],'success');self.assertIn('Archive enrichment failed',d['warnings'][0])
 def test_missing_record(self):self.assertEqual(self.client.get('/api/records/nope').status_code,404)
 def test_cross_origin_blocked(self):self.assertEqual(self.client.post('/api/demo',json={},headers={'Origin':'https://evil.example'}).status_code,403)
 def test_untrusted_host_blocked(self):self.assertEqual(self.client.get('/api/health',headers={'Host':'evil.example'}).status_code,400)
 def test_body_cap(self):self.assertEqual(self.client.post('/api/search',content='a'*32769).status_code,413)
 def test_batch_client(self):
  import tempfile
  from unittest.mock import patch
  from contextlib import redirect_stdout
  from io import StringIO
  from materials_query.client import main
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'batch.json';target=Path(tmp)/'result.json'
   source.write_text(json.dumps({'queries':[{'formula':'Fe','provider':'materials_project'}]}))
   with patch('sys.argv',['client',str(source),'--output',str(target)]),patch('materials_query.client.httpx.Client',return_value=self.client),redirect_stdout(StringIO()):
    main()
   self.assertEqual(json.loads(target.read_text())['status'],'failed')
 def test_ui_assets(self):
  r=self.client.get('/');self.assertEqual(r.status_code,200);self.assertIn('lang="en"',r.text);self.assertEqual(self.client.get('/static/app.js').status_code,200);self.assertIn("frame-ancestors 'none'",r.headers['content-security-policy'])
if __name__=='__main__':unittest.main()
