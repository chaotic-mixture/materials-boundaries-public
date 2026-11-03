"""Run current integration tests and daily graph/export checks without history."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests'))


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')


def main():
    external=Path(sys.argv[1]).resolve()
    assert not external.exists()
    external.mkdir(parents=True)
    patterns=['test_database*.py','test_material_reference_contract.py','test_material_presentation_fast_path.py','test_material_reference_expansion.py','test_material_uncertainty_contract.py','test_material_reported_measures_contract.py','test_material_scientific_notation_contract.py','test_specified_elongation_contract.py','test_flexural_strength_contract.py','test_tensile_break_stress_contract.py']
    suite=unittest.TestSuite()
    daily=0
    for pattern in patterns:
        tests=unittest.TestLoader().discover(str(ROOT/'tests'),pattern=pattern)
        if pattern=='test_database*.py':daily=tests.countTestCases()
        suite.addTests(tests)
    log=io.StringIO()
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (OUT/'scoped-tests-r12-r14.log').write_text(log.getvalue(),encoding='utf-8')
    write(OUT/'SCOPED_TESTS_R12_R14.json',{'scope':patterns,'execution':'fresh_current_native_and_runtime_integration_run_not_sum_of_old_runs','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'successful':result.wasSuccessful(),'daily_database_subset_tests':daily,'full_history_regression':'not_run'})
    assert result.wasSuccessful() and result.testsRun==127 and daily==19
    env=os.environ.copy()
    env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    commands=[['check','--scientific-contracts'],['export','--query','C11000','--quantity','mass_density','--output',str(external/'database-example')],['verify','--snapshot',str(external/'database-example')]]
    receipts=[]
    for args in commands:
        proc=subprocess.run([sys.executable,'-B','-m','materials_boundaries.database',*args],cwd=ROOT,env=env,capture_output=True,encoding='utf-8')
        (external/(args[0]+'.log')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
        proc.check_returncode()
        response=json.loads(proc.stdout)
        receipts.append({'command':['python','-m','materials_boundaries.database',*args],'exit_code':proc.returncode,'result':response})
    assert receipts[-1]['result']['status']=='snapshot_integrity_passed'
    write(OUT/'DATABASE_CI_LOCAL_EQUIVALENT_R12_R14.json',{'daily_tests':{'executed_as_subset_of_scoped_run':19,'not_additional_to_127':True},'commands':receipts,'full_history_regression':'not_run','remote_CI':'not_yet_run'})
    print(json.dumps({'tests':result.testsRun,'daily_subset':daily,'graph_export_verify':'passed'}),flush=True)


if __name__=='__main__':main()
