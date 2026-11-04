"""Freeze actual local acceptance, current docs and historical byte resolution."""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
AREA=OUT.parent
EXT=ROOT.parent/'open-database-evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())

def main():
    target=OUT/'REVIEW_INPUTS_R29_R2.json';assert not target.exists()
    app=read(OUT/'APPLICATION_R29.json');test=read(OUT/'DAILY_TEST_RESULTS_R29.json')
    assert app['after_snapshot']==test['snapshot'] and test['successful'] and test['tests_run']==19
    folders=['phbv39-thermal-provenance-followup-r1','phbv39-prior-version-comparison-r1','pbs-existing-dsc-source-r1','pbs-existing-dsc-native-r1','installed-preview-r29','condition-gaps-native-r29','local-acceptance-r29']
    repo={p for folder in folders for p in (AREA/folder).rglob('*') if p.is_file()}
    repo|={ROOT/n for n in ['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md','experimental/platform/query-service/materials_query/catalog_snapshot.py']}
    recipe=read(AREA/'installed-preview-r29/PACKAGE_INPUTS_R29.json')
    repo|={ROOT/n for n in recipe}|set((ROOT/'schemas').glob('*.schema.json'))|set((ROOT/'tests').glob('test_database*.py'))
    external={Path(n) for n in read(AREA/'installed-preview-r29/REVIEW_INPUTS_R29.json')['external_files_sha256']}
    external|={p for p in (EXT/'polymer-native-acceptance-20261104-r29').rglob('*') if p.is_file()}
    for p,h in read(OUT/'NATIVE_INSTALLED_EQUIVALENCE_R29.json').get('native_table_sha256',{}).items():assert sha(ROOT/'materials_boundaries/data'/p)==h
    result={'schema':'existing-PBS-DSC-local-native-acceptance-review/1','baseline_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'baseline_snapshot':app['before_snapshot'],'current_snapshot':app['after_snapshot'],'repo_files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(repo)},'external_files_sha256':{str(p):sha(p) for p in sorted(external)},'native_applied':True,'pushed':False,'remote_CI':'not_run_for_uncommitted_batch','full_history_regression':'not_run','review_scope':'Actual native acceptance, full-object preservation, exact installed equivalence,19 daily checks,current docs/gaps/CLI export and preserved source/install input contexts;not scientific/HTTP/platform/release approval'}
    with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'review_inputs_sha256':sha(target),'repo_files':len(result['repo_files_sha256']),'external_files':len(result['external_files_sha256'])}))

if __name__=='__main__':main()
