"""Run current database behavior checks once after local native acceptance."""
from pathlib import Path
import json,hashlib,io,sys,unittest

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from materials_boundaries.database import Database
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not (OUT/'DAILY_TEST_RESULTS_R29.json').exists()
    db=Database();assert db.snapshot==json.loads((OUT/'APPLICATION_R29.json').read_bytes())['after_snapshot']
    recipe=json.loads((OUT.parent/'installed-preview-r29/PACKAGE_INPUTS_R29.json').read_bytes())
    paths={ROOT/n for n in recipe}|set((ROOT/'tests').glob('test_database*.py'))|set((ROOT/'schemas').glob('*.schema.json'))
    inputs={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_database*.py')
    log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (OUT/'daily-tests-r29.log').write_text(log.getvalue(),encoding='utf-8')
    assert inputs=={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    record={'scope':'test_database*.py on current accepted native snapshot;not full historical or full platform regression','snapshot':db.snapshot,'properties':len(db.properties),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'successful':result.wasSuccessful(),'input_sha256_before_and_after':inputs,'inputs_unchanged_during_run':True,'full_history_regression':'not_run','HTTP':'not_run','remote_CI_for_this_uncommitted_batch':'not_run','pushed':False}
    with (OUT/'DAILY_TEST_RESULTS_R29.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    assert result.wasSuccessful() and result.testsRun==19 and not result.skipped
    print(json.dumps({k:record[k] for k in ['snapshot','tests_run','failures','errors','skipped','successful']}))

if __name__=='__main__':main()
