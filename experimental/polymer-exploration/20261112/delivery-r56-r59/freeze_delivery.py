"""Freeze current delivery scope and resolve historical pins by exact bytes."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261112-r56-r59'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def gitpaths(*args):return [s.decode('utf-8') for s in subprocess.check_output(['git',*args,'-z'],cwd=ROOT).split(b'\0') if s]
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='3880c8ad4c83d8a3c4decf71e130e021b91a8c0d'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    manifests=[];external={};dependencies={};resolutions=[]
    for p in sorted(HERE.parent.rglob('REVIEW*.json')):
        d=read(p)
        if 'repo_files_sha256' not in d:continue
        manifests.append((p,d));external.update(d.get('external_files_sha256',{}))
    for p in EXT.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        rel=p.relative_to(EXT).as_posix()
        if '/venv/' in '/'+rel and not ('/site-packages/materials_boundaries/' in rel or '/site-packages/materials_boundaries-' in rel):continue
        external[str(p)]=sha(p)
    archives={}
    for n,h in external.items():
        assert sha(Path(n))==h,n
        archives.setdefault(h,n)
    head_archive=EXT/'historical-head-files'
    for p,d in manifests:
        for group in ['repo_files_sha256','native_files_sha256']:
            for n,h in d.get(group,{}).items():
                current=sha(ROOT/n);dependencies[n]=current
                if current==h:continue
                if h not in archives:
                    data=subprocess.check_output(['git','show','HEAD:'+n],cwd=ROOT)
                    assert hashlib.sha256(data).hexdigest()==h,(str(p),n,h)
                    out=head_archive/n;out.parent.mkdir(parents=True,exist_ok=True)
                    if not out.exists():out.write_bytes(data)
                    assert sha(out)==h;archives[h]=str(out);external[str(out)]=h
                resolutions.append(dict(manifest=p.relative_to(ROOT).as_posix(),group=group,original_path=n,sha256=h,resolved_external_path=archives[h]))
    write(HERE/'HISTORICAL_PIN_RESOLUTIONS_R1.json',dict(resolutions=resolutions,rule='Historical stage bytes are not rewritten; exact archived hash only.'))
    pending=[HERE/'PROSPECTIVE_PATHS_R1.json',HERE/'REVIEW_DELIVERY_INPUTS_R1.json',HERE/'INDEPENDENT_INTEGRATION_REVIEW_R1.json']
    paths=sorted(set(gitpaths('diff','--name-only')+gitpaths('ls-files','--others','--exclude-standard')+[p.relative_to(ROOT).as_posix() for p in pending]))
    assert all(n.startswith('experimental/polymer-exploration/20261112/') or n in {'experimental/polymer-exploration/20261111/delivery-r52-r55/CURRENT_STATUS.zh.md','experimental/polymer-exploration/20261111/delivery-r52-r55/REMOTE_DELIVERY_RECEIPT_R1.json'} or n.startswith(('materials_boundaries/','schemas/','tests/')) or n in {'README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md'} for n in paths)
    assert all(Path(n).suffix.lower() not in {'.pdf','.xml','.png','.jpg','.xlsx','.whl','.zip','.pyc'} for n in paths)
    write(HERE/'PROSPECTIVE_PATHS_R1.json',dict(paths=paths,pending_review_files=[p.relative_to(ROOT).as_posix() for p in pending],scope='32 new properties,36 existing property revisions,27 new contexts,5 existing state revisions,3 source notes,2 runtime contracts;not merge or deployment'))
    for n in paths:
        p=ROOT/n
        if p.is_file():dependencies[n]=sha(p)
    for p in HERE.iterdir():
        if p.is_file():dependencies[p.relative_to(ROOT).as_posix()]=sha(p)
    workflow='.github/workflows/database.yml';dependencies[workflow]=sha(ROOT/workflow)
    native={f'materials_boundaries/data/{n}.json':sha(ROOT/f'materials_boundaries/data/{n}.json') for n in ['materials','reference_properties','sources']}
    write(HERE/'REVIEW_DELIVERY_INPUTS_R1.json',dict(schema='polymer-consolidated-r56-r59-review/1',repo_files_sha256=dict(sorted(dependencies.items())),external_files_sha256=dict(sorted(external.items())),native_files_sha256=native,prospective_paths=paths,bound_unchanged_workflow=workflow,scope='Current290 includes daily19,real71input67payload installation,68 exact cohort records and6 full consumer groups;historical failures and unknowns retained. Not exactcommit/push/remoteCI.',constraints='Read-only ownhash/JSON/PDF/OOXML/schema/diff/limitedinstalledqueries/existingexports;no authorhelpers/testmodules/testsuites/fullgraph/history/writes/cache/install/Git/push.'))
    p=HERE/'REVIEW_DELIVERY_INPUTS_R1.json';print(json.dumps(dict(sha256=sha(p),repo=len(dependencies),external=len(external),prospective=len(paths),historical_resolutions=len(resolutions))))
if __name__=='__main__':main()
