"""Run current database behavior checks once after local native acceptance."""
from pathlib import Path
import json,hashlib,io,sys,unittest

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
from materials_boundaries.database import Database
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not (OUT/'DAILY_TEST_RESULTS_R30.json').exists()
    db=Database();assert db.snapshot==json.loads((OUT/'APPLICATION_R30.json').read_bytes())['after_snapshot']
    recipe=json.loads((OUT.parent/'installed-preview-r30/PACKAGE_INPUTS_R30.json').read_bytes())
    paths={ROOT/n for n in recipe}|set((ROOT/'tests').glob('test_database*.py'))|set((ROOT/'tests').glob('test_*contract.py'))|set((ROOT/'schemas').glob('*.schema.json'))|{ROOT/'docs/MATERIAL_REFERENCE_CATALOG.md'}
    inputs={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    suite=unittest.TestSuite([unittest.TestLoader().discover(str(ROOT/'tests'),pattern=p) for p in ['test_database*.py','test_glass_transition_method_context_contract.py']])
    log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (OUT/'daily-tests-r30.log').write_text(log.getvalue(),encoding='utf-8')
    assert inputs=={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    record={'scope':'19 database behavior and3 fictional method-context cases on current accepted native snapshot;not full historical or full platform regression','daily_database_subset':19,'method_context_subset':3,'snapshot':db.snapshot,'properties':len(db.properties),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'successful':result.wasSuccessful(),'input_sha256_before_and_after':inputs,'inputs_unchanged_during_run':True,'full_history_regression':'not_run','HTTP':'not_run','remote_CI_for_this_uncommitted_batch':'not_run','pushed':False}
    with (OUT/'DAILY_TEST_RESULTS_R30.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    assert result.wasSuccessful() and result.testsRun==22 and not result.skipped
    print(json.dumps({k:record[k] for k in ['snapshot','tests_run','failures','errors','skipped','successful']}))

if __name__=='__main__':main()
