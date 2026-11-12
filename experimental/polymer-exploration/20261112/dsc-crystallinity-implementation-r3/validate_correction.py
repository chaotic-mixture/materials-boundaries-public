"""Run targeted current tests for the localized source-conflict correction."""
from pathlib import Path
import hashlib,io,json,sys,unittest
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
def main():
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_dsc_crystallinity_contract.py')
    paths=set((ROOT/'materials_boundaries').glob('*.py'))|set((ROOT/'materials_boundaries/data').glob('*.json'))|set((ROOT/'schemas').glob('*.json'))|{Path(__file__),ROOT/'tests/fixtures/dsc_crystallinity_schema_baseline.json'}
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            p=Path(name).resolve()
            if p.is_relative_to(ROOT) and p.is_file():paths.add(p)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    def write(n,obj):
        with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')
    write('TARGETED_INPUTS_R3.json',before)
    log=io.StringIO();r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (HERE/'targeted-tests-r3.log').write_text(log.getvalue(),encoding='utf-8',newline='\n')
    stable=all(sha(ROOT/n)==h for n,h in before.items())
    result=dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),successful=r.wasSuccessful(),inputs_unchanged=stable,stable_inputs=len(before),scope='Current17 targetedcases;not current395 or sum with original393;localized conflict predicate only')
    write('TARGETED_RESULTS_R3.json',result)
    assert r.wasSuccessful() and r.testsRun==17 and not r.skipped and stable
    from materials_boundaries.database import Database
    graph=Database().validate_scientific_contracts()
    assert graph['properties']==5740 and all(sha(ROOT/n)==h for n,h in before.items())
    write('CURRENT_GRAPH_R3.json',dict(result=graph,scope='Current native graph once,no Xc records or history replay'))
    print(json.dumps(result))
if __name__=='__main__':main()
