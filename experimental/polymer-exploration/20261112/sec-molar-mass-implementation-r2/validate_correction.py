"""Focused SEC string correction checks and one current native graph validation."""
from pathlib import Path
import hashlib,io,json,sys,unittest
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
def main():
 suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_sec_molar_mass_contract.py')
 paths=set((ROOT/'materials_boundaries').rglob('*.py'))|set((ROOT/'materials_boundaries/data').glob('*.json'))|set((ROOT/'schemas').glob('*.json'))|{Path(__file__),ROOT/'tests/fixtures/sec_molar_mass_schema_baseline.json'}
 for module in list(sys.modules.values()):
  name=getattr(module,'__file__',None)
  if name:
   path=Path(name).resolve()
   if path.is_relative_to(ROOT) and path.is_file():paths.add(path)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 pins={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
 def write(path,x):
  with path.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
 write(HERE/'AFFECTED_INPUTS_R2.json',pins)
 log=io.StringIO();r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
 (HERE/'affected-tests-r2.log').write_text(log.getvalue(),encoding='utf-8',newline='\n')
 stable=all(sha(ROOT/n)==h for n,h in pins.items())
 result=dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),successful=r.wasSuccessful(),stable_inputs=len(pins),inputs_unchanged=stable,scope='Focused21 SEC checks incl2stringedge tests;not new430/428 fullsuite or historicalsum')
 write(HERE/'AFFECTED_RESULTS_R2.json',result);print(json.dumps(result),flush=True)
 assert r.wasSuccessful() and r.testsRun==21 and not r.skipped and stable
 from materials_boundaries.database import Database
 from materials_boundaries.material_references import validate_material_catalog
 db=Database();validate_material_catalog(*(db.data[n] for n in ('materials','reference_properties','sources')))
 assert len(db.properties)==5754 and len(db.states)==5432 and len(db.sources)==134
 assert all(sha(ROOT/n)==h for n,h in pins.items())
 write(HERE/'CURRENT_GRAPH_R2.json',dict(snapshot=db.snapshot,properties=len(db.properties),states=len(db.states),sources=len(db.sources),full_scientific_graph='passed_once',native_applied=False,stable_inputs=len(pins),scope='Current native graph only;no SEC candidate mapping orhistory replay'))
 print('Current native5754/5432/134 graph validated once',flush=True)
if __name__=='__main__':main()
