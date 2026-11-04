"""Verify method context preservation without changing runtime or native data."""
from pathlib import Path
import json,hashlib,io,sys,unittest

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not (OUT/'TEST_RESULTS_R2.json').exists()
    paths=set((ROOT/'materials_boundaries').glob('*.py'))|set((ROOT/'tests').glob('test_*contract.py'))|{ROOT/'tests/test_glass_transition_temperature_contract.py',ROOT/'tests/test_glass_transition_method_context_contract.py',ROOT/'schemas/reference_properties.schema.json',ROOT/'docs/MATERIAL_REFERENCE_CATALOG.md'}
    paths|={ROOT/'materials_boundaries/data'/n for n in ['materials.json','reference_properties.json','sources.json']}
    inputs={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_glass_transition_method_context_contract.py');log=io.StringIO()
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (OUT/'method-context-tests-r2.log').write_text(log.getvalue(),encoding='utf-8',newline='\n')
    assert inputs=={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    record={'scope':'Three fictional method-qualified Tg preservation and structural duplicate checks;not physical comparability or native mapping validation','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'successful':result.wasSuccessful(),'input_sha256_before_and_after':inputs,'inputs_unchanged_during_run':True,'native_data_changed':False,'full_history_regression':'not_run','count_note':'R1 two errors are preserved separately;not added to successful R2 count.','pushed':False}
    with (OUT/'TEST_RESULTS_R2.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    print(log.getvalue());assert result.wasSuccessful() and result.testsRun==3 and not result.skipped

if __name__=='__main__':main()
