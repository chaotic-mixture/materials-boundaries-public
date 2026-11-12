"""Freeze exact local delivery scope after all four acceptance reviews."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def gitpaths(*args):return [s.decode('utf-8') for s in subprocess.check_output(['git',*args,'-z'],cwd=ROOT).split(b'\0') if s]
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();assert head=='dd91c1841e3630bd7de0cbeb1707ad3276080272'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    assert not gitpaths('diff','--cached','--name-only'), 'freeze requires an empty index'
    for phase,suffix,entry in [('r64','R64_R2','REVIEW_FINAL_INPUTS_R64_R2.json'),('r65','R65','REVIEW_FINAL_INPUTS_R65.json')]:
        folder=HERE.parent/('local-acceptance-'+phase);receipt=read(folder/('INDEPENDENT_FINAL_REVIEW_'+suffix+'.json'))
        assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(folder/entry)
    history=read(HERE/'HISTORICAL_PIN_RESOLUTIONS_R1.json');assert not history['unresolved']
    external=history['external_files_sha256']
    for n,h in external.items():assert sha(Path(n))==h,n
    dependencies={n:sha(ROOT/n) for n in history['current_dependencies_sha256']}
    pending=[HERE/'PROSPECTIVE_PATHS_R1.json',HERE/'REVIEW_DELIVERY_INPUTS_R1.json',HERE/'INDEPENDENT_INTEGRATION_REVIEW_R1.json']
    paths=sorted(set(gitpaths('diff','--name-only')+gitpaths('ls-files','--others','--exclude-standard')+[p.relative_to(ROOT).as_posix() for p in pending]))
    for n in paths:
        assert n.startswith(('experimental/polymer-exploration/20261112/','materials_boundaries/','schemas/','tests/')) or n in ['README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md'],n
        assert Path(n).suffix.lower() not in {'.pdf','.xml','.png','.jpg','.xlsx','.whl','.zip','.pyc'},n
    write(HERE/'PROSPECTIVE_PATHS_R1.json',dict(paths=paths,pending_review_files=[p.relative_to(ROOT).as_posix() for p in pending],baseline_commit=head,scope='27 new properties,9 new rheologycontexts,9 existingDSC context link/version/scope revisions;2 new contracts,no identities/grades/sources'))
    for n in paths:
        if (ROOT/n).is_file():dependencies[n]=sha(ROOT/n)
    workflow='.github/workflows/database.yml';dependencies[workflow]=sha(ROOT/workflow)
    native={f'materials_boundaries/data/{n}.json':sha(ROOT/f'materials_boundaries/data/{n}.json') for n in ['materials','reference_properties','sources']}
    entry=dict(schema='polymer-consolidated-r64-r65-review/1',baseline_commit=head,repo_files_sha256=dependencies,external_files_sha256=external,native_files_sha256=native,prospective_paths=paths,bound_unchanged_workflow=workflow,scope='Current19/93stable,actual76input72payload installation,18/109/9full exports;older356 retains original5673snapshot;exact stage failures/historical pins retained;no commit/push/remoteCI certification')
    p=HERE/'REVIEW_DELIVERY_INPUTS_R1.json';write(p,entry)
    print(json.dumps(dict(sha256=sha(p),repo=len(dependencies),external=len(external),prospective=len(paths))),flush=True)
if __name__=='__main__':main()
