"""Freeze cumulative experimental paths only after current package verification."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
HEAD='fb996df80be67aba2896169935f997ad08655690'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def gitpaths(*args):return [v.decode('utf-8') for v in git(*args,'-z').split(b'\0') if v]


def main():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    assert git('branch','--show-current').decode().strip()=='experimental/open-database'
    assert not gitpaths('diff','--cached','--name-only'),'freeze requires empty index before collecting scope or writing'
    for phase in ('69','70','71','72'):
        folder=HERE.parent/('local-acceptance-r'+phase);entry=folder/('REVIEW_FINAL_INPUTS_R'+phase+'.json')
        receipt=read(folder/('INDEPENDENT_FINAL_REVIEW_R'+phase+'.json'))
        assert receipt['decision']=='approved' and receipt['review_inputs_sha256']==sha(entry)
    prep=read(HERE/'PREPARATION_R1.json');assert prep['baseline_commit']==HEAD
    assert all(sha(ROOT/n)==h for n,h in prep['after_sha256'].items())
    history=read(HERE/'HISTORICAL_PIN_RESOLUTIONS_R1.json');assert not history['unresolved']
    assert len(history['manifests'])==25 and history['binding_count']==3250 and len(history['resolutions'])==364
    for n,h in history['external_files_sha256'].items():assert sha(Path(n))==h,n
    assert all(sha(ROOT/n)==h for n,h in history['current_dependencies_sha256'].items())
    for name in ('PACKAGE_INPUTS_DELIVERY.json',):
        assert all(sha(ROOT/n)==h for n,h in read(HERE/name).items())
    assert all(sha(ROOT/n)==h for n,h in read(HERE.parent/'local-acceptance-r72/AFFECTED_INPUTS_R1.json').items())
    docs=read(HERE/'DOCUMENT_BINDINGS_R1.json')
    for n,v in docs.items():
        assert sha(ROOT/n)==v['after_sha256'] and sha(Path(v['saved_before']))==v['before_sha256']
    pending=[HERE/'PROSPECTIVE_PATHS_R1.json',HERE/'REVIEW_DELIVERY_INPUTS_R1.json',HERE/'INDEPENDENT_INTEGRATION_REVIEW_R1.json']
    paths=sorted(set(gitpaths('diff','--name-only')+gitpaths('ls-files','--others','--exclude-standard')+[p.relative_to(ROOT).as_posix() for p in pending]))
    sizes={}
    for n in paths:
        assert n.startswith(('experimental/polymer-exploration/20261112/','materials_boundaries/','schemas/','tests/')) or n in ('README.md','HANDOFF.md','docs/DATABASE_COVERAGE.zh.md','docs/MATERIAL_SOURCE_CONDITIONS.zh.md','docs/OPEN_DATABASE_ROADMAP.zh.md'),n
        assert Path(n).suffix.lower() not in {'.pdf','.xml','.png','.jpg','.xlsx','.whl','.zip','.pyc'},n
        p=ROOT/n
        if p.is_file():
            assert not p.is_symlink(),n;sizes[n]=p.stat().st_size
            assert sizes[n]<100*1024*1024,n
    write(HERE/'PROSPECTIVE_PATHS_R1.json',dict(paths=paths,pending_review_files=[p.relative_to(ROOT).as_posix() for p in pending],baseline_commit=HEAD,scope='17newproperties/13contexts/5newquantityroles/4newbranches;no newidentities/grades/sources;no workflowchanges',maximum_existing_file_bytes=max(sizes.values())))
    dependencies=dict(history['current_dependencies_sha256'])
    for n in paths:
        if (ROOT/n).is_file():dependencies[n]=sha(ROOT/n)
    workflow='.github/workflows/database.yml';assert git('show',HEAD+':'+workflow)==(ROOT/workflow).read_bytes();dependencies[workflow]=sha(ROOT/workflow)
    native={f'materials_boundaries/data/{n}.json':sha(ROOT/f'materials_boundaries/data/{n}.json') for n in ('materials','reference_properties','sources')}
    entry=dict(schema='polymer-consolidated-r69-r72-review/1',baseline_commit=HEAD,repo_files_sha256=dependencies,external_files_sha256=history['external_files_sha256'],native_files_sha256=native,prospective_paths=paths,bound_unchanged_workflow=workflow,
               scope='17props/13contexts,old5740props5420states/identities/grades/sources unchanged;old27branches preserved,current31. Currentdaily19exact98inputs reused;new81input77payload installed description andcomplete170/15exports coveringall17. Earlier392/393/17/409/428/21 retainown archivedinputs,no sum/no fullhistory/HTTP/remoteCI certification',
               package=read(HERE/'INSTALLED_VALIDATION_DELIVERY.json'),commit_push='not_done',main_merge=False,deployment=False)
    path=HERE/'REVIEW_DELIVERY_INPUTS_R1.json';write(path,entry)
    print(json.dumps(dict(sha256=sha(path),repo=len(dependencies),external=len(entry['external_files_sha256']),prospective=len(paths),max_bytes=max(sizes.values()))),flush=True)


if __name__=='__main__':main()
