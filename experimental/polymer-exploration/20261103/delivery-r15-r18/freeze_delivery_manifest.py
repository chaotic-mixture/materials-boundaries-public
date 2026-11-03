"""Freeze only the independently reviewed content and named final proof artifacts."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
BASE='1d454f99b3baddef0f4b304c27bdb7dd954ee5fa'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def main():
    target=OUT/'DELIVERY_MANIFEST_R15_R18.json';assert not target.exists()
    assert git('rev-parse','HEAD').decode().strip()==BASE and git('branch','--show-current').decode().strip()=='experimental/open-database'
    assert git('diff','--cached','--name-only')==b''
    for entry,receipt in [('REVIEW_INPUTS_R15_R18.json','INDEPENDENT_CONTENT_REVIEW_R15_R18.json'),('REVIEW_INSTALL_INPUTS_R15_R18.json','INDEPENDENT_INSTALL_REVIEW_R15_R18.json')]:
        v=read(OUT/entry);r=read(OUT/receipt);assert r['decision']=='approved' and r['review_inputs_sha256']==sha(OUT/entry)
        for n,h in v['repo_files_sha256'].items():assert sha(ROOT/n)==h,n
    content=read(OUT/'REVIEW_INPUTS_R15_R18.json')
    extras=['REVIEW_INPUTS_R15_R18.json','INDEPENDENT_CONTENT_REVIEW_R15_R18.json','INSTALLED_VALIDATION_R15_R18.json','NATIVE_INSTALLED_EQUIVALENCE_R15_R18.json','verify_native_installed_current.py','REVIEW_INSTALL_INPUTS_R15_R18.json','INDEPENDENT_INSTALL_REVIEW_R15_R18.json','CURRENT_CONSUMER_VALIDATION_R15_R18.json','CURRENT_CONSUMER_EXECUTION_BINDING_R15_R18.json','freeze_delivery_manifest.py']
    allowed=set(content['repo_files_sha256'])|{(OUT/n).relative_to(ROOT).as_posix() for n in extras}
    entries=git('status','--porcelain=v1','-z','--untracked-files=all').split(b'\0');paths=[e[3:].decode('utf-8') for e in entries if e]
    assert len(paths)==len(set(paths)) and set(paths)<=allowed
    assert all((OUT/n).relative_to(ROOT).as_posix() in paths for n in extras)
    consumer=read(OUT/'CURRENT_CONSUMER_VALIDATION_R15_R18.json');assert consumer['complete_resolved_states_equal_core']==22 and consumer['new_properties_exact_record_and_query_equal']==31
    assert sum(consumer['complete_source_query_and_joined_export_counts'].values())==99 and consumer['detached_mutation_isolated'] and consumer['stale_selection_rejected']
    files={n:{'sha256':sha(ROOT/n),'bytes':(ROOT/n).stat().st_size} for n in sorted(paths)}
    assert all(x['bytes']<100*1024*1024 for x in files.values())
    assert not any(Path(n).suffix.lower() in {'.pdf','.xml','.png','.xlsx','.whl','.zip'} for n in files)
    obj={'schema':'polymer-experimental-delivery-manifest/1','baseline_commit':BASE,'branch':'experimental/open-database','native_snapshot':consumer['core_snapshot'],'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'files':files,'file_count_excluding_self':len(files),'content_review_sha256':sha(OUT/'INDEPENDENT_CONTENT_REVIEW_R15_R18.json'),'install_review_sha256':sha(OUT/'INDEPENDENT_INSTALL_REVIEW_R15_R18.json'),'consumer_receipt_sha256':sha(OUT/'CURRENT_CONSUMER_VALIDATION_R15_R18.json'),'fresh_scoped_tests':read(OUT/'SCOPED_TESTS_R15_R18.json'),'validation_python':sys.version.split()[0],'full_history_regression':'not_run','remote_CI':'pending_exact_commit','pushed':False,'merged_main':False,'stable_release':False,'deployed':False,'note':'Self hash is recorded in the external final binding and independent manifest review to avoid recursive manifest hashing.'}
    with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'manifest_sha256':sha(target),'files_excluding_self':len(files),'delivery_paths':len(files)+1}))
if __name__=='__main__':main()
