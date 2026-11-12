"""Resolve every new frozen review's exact bytes, never rewrite old manifests."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261112-r69-r72'
HEAD='fb996df80be67aba2896169935f997ad08655690'


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def main():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    assert git('branch','--show-current').decode().strip()=='experimental/open-database'
    assert not git('diff','--cached','--name-only','-z'),'resolver requires empty index before scope collection'
    names=[s.decode('utf-8') for s in git('ls-files','--others','--exclude-standard','-z').split(b'\0') if s]
    manifests=[];external={}
    for name in names:
        if not Path(name).name.startswith('REVIEW') or not name.endswith('.json'):continue
        if name.startswith(HERE.relative_to(ROOT).as_posix()+'/'):continue
        value=json.loads((ROOT/name).read_bytes())
        if 'repo_files_sha256' not in value:continue
        manifests.append((name,value))
        for n,h in value.get('external_files_sha256',{}).items():
            assert n not in external or external[n]==h,n
            external[n]=h
    # New exact baseline bytes, document backups, package and consumer evidence.
    for p in EXT.rglob('*'):
        if p.is_file() and 'venv' not in p.relative_to(EXT).parts:external[str(p)]=digest(p)
    archives={};cache={};missing=[];resolutions=[];binding_count=0
    for name,h in external.items():
        assert digest(Path(name))==h,name;archives.setdefault(h,name)
    for manifest,value in manifests:
        for group in ('repo_files_sha256','native_files_sha256'):
            for name,h in value.get(group,{}).items():
                binding_count+=1
                if name not in cache:cache[name]=digest(ROOT/name)
                if cache[name]==h:continue
                if h not in archives:
                    result=subprocess.run(['git','show',HEAD+':'+name],cwd=ROOT,capture_output=True)
                    if result.returncode==0 and hashlib.sha256(result.stdout).hexdigest()==h:
                        target=EXT/'historical-head-files'/name;target.parent.mkdir(parents=True,exist_ok=True)
                        if not target.exists():target.write_bytes(result.stdout)
                        assert digest(target)==h
                        archives[h]=str(target);external[str(target)]=h
                    else:
                        missing.append(dict(manifest=manifest,group=group,original_path=name,sha256=h));continue
                resolutions.append(dict(manifest=manifest,group=group,original_path=name,sha256=h,resolved_external_path=archives[h]))
    report=dict(baseline_commit=HEAD,manifests={n:digest(ROOT/n) for n,_ in manifests},binding_count=binding_count,
                resolutions=resolutions,unresolved=missing,external_files_sha256=external,current_dependencies_sha256=cache,
                rule='Exact preserved bytes or exact baseline commit bytes only;no inference or historical manifest rewriting',native_changed=False,pushed=False)
    write(HERE/'HISTORICAL_PIN_RESOLUTIONS_R1.json',report)
    print(json.dumps(dict(manifests=len(manifests),bindings=binding_count,resolutions=len(resolutions),external=len(external),unresolved=len(missing))),flush=True)
    assert not missing


if __name__=='__main__':main()
