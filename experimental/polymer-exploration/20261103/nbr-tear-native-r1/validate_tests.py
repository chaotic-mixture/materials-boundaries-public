"""Run current tear and legacy contract tests with stable input bindings."""
from pathlib import Path
import hashlib,io,json,os,sys,unittest
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    patterns=['test_database*.py','test_material_reference_contract.py','test_material_presentation_fast_path.py','test_material_reference_expansion.py','test_material_uncertainty_contract.py','test_material_reported_measures_contract.py','test_material_scientific_notation_contract.py','test_specified_elongation_contract.py','test_flexural_strength_contract.py','test_tensile_break_stress_contract.py','test_break_elongation_contract.py','test_strength_elongation_contract.py','test_shore_a_hardness_contract.py','test_compression_reference_contract.py','test_tear_strength_contract.py']
    package=json.loads((ROOT/'experimental/polymer-exploration/20261103/delivery-r15-r18/PACKAGE_INPUTS_R15_R18.json').read_bytes())
    paths={ROOT/n for n in package}|{p for pattern in patterns for p in (ROOT/'tests').glob(pattern)}|set((ROOT/'schemas').glob('*.schema.json'))|{ROOT/'docs/MATERIAL_REFERENCE_CATALOG.md'}
    before={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    suite=unittest.TestSuite()
    for pattern in patterns:suite.addTests(unittest.TestLoader().discover(str(ROOT/'tests'),pattern=pattern))
    log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (OUT/'scoped-tests-r23.log').write_text(log.getvalue(),encoding='utf-8',newline='\n')
    after={p.relative_to(ROOT).as_posix():sha(p) for p in paths};assert before==after
    record={'scope':patterns,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'successful':result.wasSuccessful(),'input_sha256_before_and_after':before,'inputs_unchanged_during_run':True,'count_scope':'Fresh152 includes6tear tests;not added to standalone trials or historical146.','full_history_regression':'not_run'}
    with (OUT/'TEST_RESULTS_R23.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    assert result.wasSuccessful() and result.testsRun==152 and len(result.skipped)==0
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'stable_inputs':len(before)}))
if __name__=='__main__':main()
