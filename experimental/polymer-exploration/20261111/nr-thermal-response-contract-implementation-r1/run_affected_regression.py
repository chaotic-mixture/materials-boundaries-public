"""Fresh bounded regression of work and all previously delivered contracts."""
from pathlib import Path
import ast,hashlib,io,json,sys,unittest
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
def main():
    tree=ast.parse((ROOT/'experimental/polymer-exploration/20261104/delivery-r36-r38/validate_delivery.py').read_text(encoding='utf-8'))
    patterns=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='patterns' for t in n.targets))
    patterns.extend(['test_volumetric_work_contract.py','test_thermal_capacity_diffusivity_contract.py','test_thermal_transport_derivation_contract.py','test_thermal_response_fit_contract.py'])
    suite=unittest.TestSuite([unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=p) for p in patterns])
    paths=set((ROOT/'materials_boundaries').rglob('*.py'))|set((ROOT/'materials_boundaries/data').glob('*.json'))|set((ROOT/'schemas').glob('*.json'))|{Path(__file__)}
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            p=Path(name).resolve()
            if p.is_relative_to(ROOT) and p.is_file():paths.add(p)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    with (HERE/'AFFECTED_INPUTS_R1.json').open('x',encoding='utf-8') as f:json.dump(before,f,indent=2)
    log=io.StringIO();r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (HERE/'affected-tests-r1.log').write_text(log.getvalue(),encoding='utf-8',newline='\n')
    stable=all(sha(ROOT/n)==h for n,h in before.items())
    result=dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),successful=r.wasSuccessful(),stable_inputs=len(before),inputs_unchanged=stable,scope='Fresh affected contracts including daily19;not historical sum',installation_native_admission='not_run')
    with (HERE/'AFFECTED_RESULTS_R1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result),flush=True)
    assert r.wasSuccessful() and r.testsRun==245 and stable and not r.skipped
if __name__=='__main__':main()
