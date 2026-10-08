import sys,json,unittest,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'query-service'))
import httpx
from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_federation.providers import NomadAdapter
ROOT=Path(__file__).resolve().parents[1]/'query-service'
RAW=json.loads((ROOT/'materials_query/fixtures/nomad_archive_projected.json').read_text())
class Review(unittest.TestCase):
 def client(self,payload):
  self.calls=[]
  def t(r):self.calls.append(r);return httpx.Response(200,json=payload)
  return TestClient(create_app(NomadAdapter(transport=httpx.MockTransport(t),fixture=True)),raise_server_exceptions=False)
 def query(self,c,**kw):return c.post('/api/search',json={'formula':'CaFe2Re','limit':1,**kw})
 def test_bounded_cursor_counts(self):
  c=self.client({'data':[RAW],'pagination':{'total':73,'next_page_after_value':'opaque'}})
  d=self.query(c).json();self.assertEqual(len(self.calls),1);self.assertEqual(self.calls[0].url.params['page_size'],'1');self.assertEqual(self.calls[0].url.params['owner'],'public');self.assertEqual(d['page']['next_cursor'],'opaque');self.assertTrue(d['page']['possibly_truncated']);self.assertEqual(d['counts'],{'matching_provider_entries':73,'fetched_entries':1,'returned_entries':1,'unique_material_count':None,'admitted_material_count':0,'quota_credit':0})
 def test_empty_is_success(self):
  c=self.client({'data':[],'pagination':{'total':0}});d=self.query(c).json();self.assertEqual(d['status'],'success');self.assertEqual(d['counts']['returned_entries'],0);self.assertFalse(d['page']['possibly_truncated'])
 def test_health_capabilities_no_upstream(self):
  c=self.client({});self.assertEqual(c.get('/api/health').json()['upstream_health'],'not_checked');x=c.get('/api/capabilities').json();self.assertEqual(x['bounds']['concurrent_operations'],2);self.assertEqual(x['providers']['materials_project'],'not_configured');self.assertEqual(len(self.calls),0)
 def test_demo_export_versions_provenance(self):
  c=self.client({})
  for p in ['nomad','materials_project']:
   d=c.post('/api/demo',json={'provider':p}).json();self.assertEqual(d['schema_version'],'query_service/0.1.0');self.assertTrue(d['page']['fixture']);x=d['page']['candidates'][0];self.assertTrue(x['source']['fixture']);self.assertIsNone(x['canonical_material_id']);self.assertEqual(x['review_status'],'pending_review');self.assertEqual(x['quota_credit'],0);self.assertEqual(x['schema_version'],'0.1.0');self.assertEqual(c.get('/api/records/'+x['snapshot_id']).json(),x)
   for prop in x['properties']:self.assertTrue(prop['provenance']['field_path']);self.assertTrue(prop['unit']);self.assertIsNone(prop['uncertainty'])
  self.assertFalse(self.calls)
 def test_mp_live_never_demo(self):
  c=self.client({});r=self.query(c,provider='materials_project');self.assertEqual(r.status_code,503);self.assertEqual(r.json()['status'],'not_configured');self.assertNotIn('page',r.json());self.assertFalse(self.calls)
 def test_partial_failed_batch(self):
  c=self.client({'data':[RAW]})
  for qs,status in [([{'formula':'CaFe2Re','limit':1},{'formula':'Fe','provider':'materials_project'}],'partial'),([{'formula':'Fe','provider':'materials_project'}],'failed')]:
   r=c.post('/api/batch',json={'queries':qs});self.assertEqual(r.status_code,200);d=r.json();self.assertEqual(d['status'],status);self.assertEqual(d['schema_version'],'query_batch/0.1.0');self.assertEqual([x['query']['formula'] for x in d['results']],[x['formula'] for x in qs])
 def test_filter_preserves_unfiltered_total(self):
  c=self.client({'data':[RAW],'pagination':{'total':73}});d=self.query(c,evidence_kind='experimental').json();self.assertEqual(d['counts']['returned_entries'],0);self.assertEqual(d['counts']['fetched_entries'],1);self.assertEqual(d['counts']['matching_provider_entries'],73)
 def test_concurrency_recovers(self):
  start=threading.Barrier(3);release=threading.Event()
  class A:
   def search(self,q):
    start.wait(timeout=5);release.wait(timeout=5)
    return NomadAdapter(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[]})),fixture=True).search(q)
  c=TestClient(create_app(A()))
  with ThreadPoolExecutor(2) as ex:
   f=[ex.submit(self.query,c) for _ in range(2)];start.wait(timeout=5)
   self.assertEqual(self.query(c).status_code,429);release.set()
   self.assertTrue(all(x.result().status_code==200 for x in f))
  self.assertEqual(c.post('/api/search',json={'formula':'Fe','provider':'materials_project'}).status_code,503)
 def test_malformed_pagination_fails_closed(self):
  c=self.client({'data':[RAW],'pagination':'schema changed'})
  self.assertEqual(self.query(c).status_code,502)
if __name__=='__main__':unittest.main(verbosity=2)
