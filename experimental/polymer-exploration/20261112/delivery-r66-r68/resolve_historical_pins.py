"""Resolve frozen historical stage bytes without rewriting their manifests."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261112-r66-r68'
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();assert head=='7eed67720c4a7252f84f0e3ed743653f55047042'
    approval=json.loads((HERE.parent/'local-acceptance-r68/INDEPENDENT_FINAL_REVIEW_R68.json').read_bytes());assert approval['decision']=='approved'
    names=[s.decode('utf-8') for s in subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT).split(b'\0') if s]
    manifests=[];external={}
    for n in names:
        if not Path(n).name.startswith('REVIEW') or not n.endswith('.json'):continue
        d=json.loads((ROOT/n).read_bytes())
        if 'repo_files_sha256' not in d:continue
        manifests.append((n,d))
        for p,h in d.get('external_files_sha256',{}).items():
            assert p not in external or external[p]==h,p
            external[p]=h
    EXT.mkdir(exist_ok=False);archives={};cache={};missing=[];resolutions=[]
    for n,h in external.items():
        assert digest(Path(n))==h,n
        archives.setdefault(h,n)
    for manifest,d in manifests:
        for group in ['repo_files_sha256','native_files_sha256']:
            for n,h in d.get(group,{}).items():
                if n not in cache:cache[n]=digest(ROOT/n)
                if cache[n]==h:continue
                if h not in archives:
                    result=subprocess.run(['git','show',head+':'+n],cwd=ROOT,capture_output=True)
                    if result.returncode==0 and hashlib.sha256(result.stdout).hexdigest()==h:
                        out=EXT/'historical-head-files'/n;out.parent.mkdir(parents=True,exist_ok=True)
                        if not out.exists():out.write_bytes(result.stdout)
                        assert digest(out)==h;archives[h]=str(out);external[str(out)]=h
                    else:
                        missing.append(dict(manifest=manifest,group=group,original_path=n,sha256=h));continue
                resolutions.append(dict(manifest=manifest,group=group,original_path=n,sha256=h,resolved_external_path=archives[h]))
    report=dict(baseline_commit=head,manifests={n:digest(ROOT/n) for n,d in manifests},resolutions=resolutions,unresolved=missing,external_files_sha256=external,current_dependencies_sha256=cache,rule='Exact saved bytes or exact baseline commit bytes only; no historical manifest rewriting or inference',native_changed=False,pushed=False)
    write(HERE/'HISTORICAL_PIN_RESOLUTIONS_R1.json',report)
    print(json.dumps(dict(manifests=len(manifests),resolutions=len(resolutions),external=len(external),unresolved=len(missing))),flush=True)
    assert not missing
if __name__=='__main__':main()
