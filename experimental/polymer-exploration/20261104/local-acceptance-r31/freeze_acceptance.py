"""Freeze actual DMA Tg local acceptance and cumulative unpushed progress."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
AREA=OUT.parent
EXT=ROOT.parent/'open-database-evidence'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    target=OUT/'REVIEW_INPUTS_R31.json';assert not target.exists()
    app=read(OUT/'APPLICATION_R31.json');tests=read(OUT/'DAILY_TEST_RESULTS_R31.json');delta=read(OUT/'CUMULATIVE_LOCAL_DELTA_R29_R31.json')
    assert tests['successful'] and tests['tests_run']==22 and app['after_snapshot']==tests['snapshot']==delta['current_snapshot']
    folders=['phbv39-thermal-provenance-followup-r1','phbv39-prior-version-comparison-r1','pbs-existing-dsc-source-r1','pbs-existing-dsc-native-r1','installed-preview-r29','local-acceptance-r29','condition-gaps-native-r29','pbs-existing-dma-tg-source-r1','pbs-existing-dma-tg-native-r1','pbs-existing-dma-tg-method-checks-r1','installed-preview-r30','local-acceptance-r30','condition-gaps-native-r30','pbs-existing-flexural-source-r1','pbs-existing-flexural-native-r1','installed-preview-r31','local-acceptance-r31','condition-gaps-native-r31']
    repo={p for n in folders for p in (AREA/n).rglob('*') if p.is_file()}
    repo|={ROOT/n for n in ['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_REFERENCE_CATALOG.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md','experimental/platform/query-service/materials_query/catalog_snapshot.py']}
    recipe=read(AREA/'installed-preview-r31/PACKAGE_INPUTS_R31.json');repo|={ROOT/n for n in recipe}|set((ROOT/'schemas').glob('*.schema.json'))|set((ROOT/'tests').glob('test_database*.py'))|{ROOT/'tests/test_glass_transition_method_context_contract.py'}
    external={Path(n) for n in read(AREA/'installed-preview-r31/REVIEW_INPUTS_R31.json')['external_files_sha256']}
    external|={p for p in (EXT/'polymer-native-acceptance-20261104-r31').rglob('*') if p.is_file()}
    for c in read(OUT/'CONTEXT_RESOLUTION_R31.json')['contexts']:
        for b in c['bindings'].values():
            p=Path(b['resolved_path'])
            assert sha(p)==b['sha256']
            if not p.is_relative_to(ROOT):external.add(p)
    for name,h in app['native_table_sha256'].items():assert sha(ROOT/'materials_boundaries/data'/name)==h
    entry={'schema':'existing-PBS-flexural-local-native-acceptance-review/1','baseline_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'baseline_snapshot':app['before_snapshot'],'current_snapshot':app['after_snapshot'],'repo_files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(repo)},'external_files_sha256':{str(p):sha(p) for p in sorted(external)},'native_applied':True,'pushed':False,'remote_CI':'not_run_for_uncommitted_batch','full_history_regression':'not_run','review_scope':'Actual r31 native acceptance,18mean/SD properties and9unresolved test contexts,22 fresh checks,installed inheritance,current docs/gaps/CLI,cumulative r29-r31 delta andhistorical resolution;no physical-coverage orrelease certification'}
    with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(entry,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'review_inputs_sha256':sha(target),'repo_files':len(entry['repo_files_sha256']),'external_files':len(entry['external_files_sha256'])}))
if __name__=='__main__':main()
