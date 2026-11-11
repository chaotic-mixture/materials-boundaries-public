"""Bind exactly approved worktree bytes,receipt and manifest for ordinary delivery."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def actual():
    out=set()
    for args in (['diff','--name-only','-z'],['ls-files','--others','--exclude-standard','-z']):out|={n for n in subprocess.check_output(['git',*args],cwd=ROOT).decode().split('\0') if n}
    return out
def main():
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    assert subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0
    entry=HERE/'REVIEW_CONTENT_INPUTS_R39_R41_R2.json';receipt=HERE/'INDEPENDENT_CONTENT_REVIEW_R39_R41_R2.json'
    content=read(entry);review=read(receipt)
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==content['baseline_commit']
    expected=set(content['repo_files_sha256'])|{p.relative_to(ROOT).as_posix() for p in (entry,receipt)}
    assert actual()==expected,(actual()-expected,expected-actual())
    assert all(sha(ROOT/n)==h for n,h in content['repo_files_sha256'].items())
    obj=dict(schema='r39-r41-exact-experimental-delivery-manifest/1',baseline_commit=content['baseline_commit'],snapshot=content['snapshot'],content_entry_sha256=sha(entry),review_receipt_sha256=sha(receipt),files={n:dict(sha256=sha(ROOT/n),bytes=(ROOT/n).stat().st_size) for n in sorted(expected)},file_count_including_manifest=len(expected)+1,manifest_self_not_hashed=True,target_ref='refs/heads/experimental/open-database',main_merge=False,stable_release=False,deployment=False)
    p=HERE/'DELIVERY_MANIFEST_R39_R41.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(content_files=len(content['repo_files_sha256']),total_files=len(expected)+1,manifest_sha256=sha(p))))
if __name__=='__main__':main()
