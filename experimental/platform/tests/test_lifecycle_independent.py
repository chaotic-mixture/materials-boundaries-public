"""Independent offline regression expectations; no network or publication."""
import copy, hashlib, json, pathlib, sys, tempfile, unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lifecycle'))
from materials_lifecycle.workflow import Workflow, Response, LifecycleError, canonical, read_json, strict_load, digest
from materials_lifecycle.__main__ import main

class IndependentEdges(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
  self.w=Workflow(self.tmp.name)
  self.entry=json.loads((ROOT/'lifecycle/fixtures/nomad_archive_projected.json').read_bytes())
  self.rid='nomad:'+self.entry['metadata']['entry_id']
 def stage(self):
  raw=canonical({'data':[self.entry],'pagination':{}})
  a=self.w.capture({'formula':'CaFe2Re'},fetch=lambda *a,**k:Response(raw),fixture=True)
  return self.w.stage(a)
 def review(self,b):
  return self.w.review(b,approved_ids=[self.rid],reviewer='reviewer',contributor='contributor',rationale='Offline QA only',rights_evidence='https://example.org/rights',demo=True)
 def build(self,b,d,v='1.0.0'):
  return self.w.build(b,d,trusted_decision_sha256=d.stem,version=v,title='Offline QA',creators=['QA'])
 def test_unknown_license_string_is_held(self):
  self.entry['metadata']['license']='unknown'
  b=self.stage()
  self.assertTrue(read_json(b)['records'][0]['holds'])
  with self.assertRaises(LifecycleError): self.review(b)
 def test_conflicting_lanes_are_held(self):
  self.entry['results']['method']['experimental']={'method':'measurement'}
  b=self.stage()
  self.assertTrue(read_json(b)['records'][0]['holds'])
 def test_erratum_blocks_reuse_pending_correction(self):
  b=self.stage(); d=self.review(b); out=self.build(b,d)
  self.w.status_event(out,record_id=self.rid,kind='erratum',reason='Numerical error under investigation',source_url='https://example.org/erratum')
  with self.assertRaises(LifecycleError):self.build(b,d,'1.0.1')
 def test_empty_fixture_never_calls_live_transport(self):
  path=pathlib.Path(self.tmp.name)/'empty.json';path.write_bytes(b'')
  with patch('materials_lifecycle.workflow.public_fetch',side_effect=RuntimeError('LIVE_TRANSPORT_CALLED')) as live:
   with patch.object(sys,'argv',['materials-lifecycle','--store',self.tmp.name,'capture','--formula','Fe','--fixture',str(path)]):
    try: main()
    except Exception: pass
   live.assert_not_called()
 def test_nonobject_response_fails_with_attempt(self):
  with self.assertRaises(LifecycleError):
   self.w.capture({'formula':'Fe'},fetch=lambda *a,**k:Response(b'[]'),fixture=True)
  self.assertEqual(len(list((pathlib.Path(self.tmp.name)/'attempts').glob('*.json'))),1)
 def test_raw_hash_is_exact_and_selected_is_separate(self):
  raw=b' \n'+canonical({'data':[self.entry],'pagination':{}})
  a=read_json(self.w.capture({'formula':'CaFe2Re'},fetch=lambda *a,**k:Response(raw),fixture=True))
  p=a['pages'][0]
  self.assertEqual(p['raw_sha256'],hashlib.sha256(raw).hexdigest())
  self.assertEqual(p['selected_payload_sha256'],digest(strict_load(raw)))
  self.assertNotEqual(p['raw_sha256'],p['selected_payload_sha256'])
 def test_archive_inventory_and_citation(self):
  import tarfile, io, yaml
  b=self.stage();out=self.build(b,self.review(b));m=read_json(out/'manifest.json')
  for f in m['files']:
   raw=(out/f['path']).read_bytes();self.assertEqual(len(raw),f['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),f['sha256'])
  cff=yaml.safe_load((out/'CITATION.cff').read_text())
  self.assertEqual(cff['type'],'dataset');self.assertNotIn('doi',cff)
  with tarfile.open(out/'dataset.tar') as tar:
   for mem in tar.getmembers():self.assertEqual(tar.extractfile(mem).read(),(out/mem.name).read_bytes())
  self.assertEqual(m['gates']['reviewer_authentication'],'not_run')

if __name__=='__main__':unittest.main(verbosity=2)
