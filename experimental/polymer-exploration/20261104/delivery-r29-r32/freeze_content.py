"""Freeze the complete reviewable experimental delivery content and package plan."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
BASE='1893455b0dc75d9ac7e7c27fc798efd7de8a0d04'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==BASE
    assert not subprocess.check_output(['git','diff','--cached','--name-only'])
    accepted=OUT.parent/'local-acceptance-r32'
    review=read(accepted/'INDEPENDENT_ACCEPTANCE_REVIEW_R32.json');assert review['decision']=='clear' and review['review_inputs_sha256']==sha(accepted/'REVIEW_INPUTS_R32.json')
    allowed=set(read(accepted/'REVIEW_INPUTS_R32.json')['repo_files_sha256'])|{(accepted/n).relative_to(ROOT).as_posix() for n in ['REVIEW_INPUTS_R32.json','INDEPENDENT_ACCEPTANCE_REVIEW_R32.json']}
    tests=read(OUT/'SCOPED_TESTS_R29_R32.json');assert tests['successful'] and tests['tests_run']==183 and not any(tests[k] for k in ['failures','errors','skipped'])
    assert read(OUT/'HISTORICAL_INPUT_RESOLUTION_R29_R32.json')['unresolved_entries']==0
    recipe=read(OUT/'PACKAGE_INPUTS_R29_R32.json');assert len(recipe)==69 and all(sha(ROOT/n)==h for n,h in recipe.items())
    raw=subprocess.check_output(['git','status','--porcelain=v1','-z','--untracked-files=all']);entries=[e for e in raw.split(b'\0') if e]
    assert not any(e[:2] in [b'R ',b' R',b'C ',b' C'] for e in entries)
    paths=[e[3:].decode('utf-8').replace('\\','/') for e in entries];assert len(paths)==len(set(paths));prefix=OUT.relative_to(ROOT).as_posix()+'/'
    for name in paths:
        p=(ROOT/name).resolve();assert p.is_relative_to(ROOT) and p.is_file() and (name in allowed or name.startswith(prefix)),name
        assert p.stat().st_size<100*1024*1024 and p.suffix.lower() not in ['.pdf','.xml','.png','.html','.xlsx','.whl','.zip']
    value={'schema':'r29-r32-consolidated-content-review/1','baseline_commit':BASE,'branch':'experimental/open-database','native_snapshot':read(OUT/'NATIVE_DELTA_R29_R32.json')['current_snapshot'],'repo_files_sha256':{n:sha(ROOT/n) for n in sorted(paths)},'fresh_tests':tests,'scope':'Four accepted rounds,full pending Git delta,source/condition boundaries,current183checks,graph/CLI,docs,exact history/externalbindings and prospective accepted-native package/consumer helpers. Not finalinstallation or Git approval.','final_install':'not_run_pending_content_approval','remote_CI':'pending_exact_commit','full_history_regression':'not_run','HTTP':'not_run','pushed':False,'merged_main':False,'deployed':False}
    with (OUT/'REVIEW_INPUTS_R29_R32.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'content_files':len(paths),'entry_sha256':sha(OUT/'REVIEW_INPUTS_R29_R32.json')}))
if __name__=='__main__':main()
