"""Freeze observed r48 application,regression and actual install for review."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r48'
MAPPING=HERE.parent/'pbs-pbat-hybrid-mechanical-mapping-r2'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    mapping=read(MAPPING/'REVIEW_INPUTS_R1.json')
    files=set(mapping['repo_files_sha256'])|set(mapping['native_files_sha256'])
    prior=HERE.parent/'pbs-pbat-hybrid-mechanical-mapping-r1'
    files|={p.relative_to(ROOT).as_posix() for p in prior.iterdir() if p.is_file()}
    docs=read(HERE/'DOCUMENT_BINDINGS_R48.json')
    for n,b in docs.items():assert sha(ROOT/n)==b['after_sha256'] and sha(Path(b['archived_exact_bytes']))==b['before_sha256']
    files.update(docs)
    files|={p.relative_to(ROOT).as_posix() for p in HERE.iterdir() if p.is_file()}
    files|={p.relative_to(ROOT).as_posix() for p in MAPPING.iterdir() if p.is_file()}
    external=dict(mapping['external_files_sha256'])
    external.update(read(prior/'REVIEW_INPUTS_R1.json')['external_files_sha256'])
    for p in EXT.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(EXT).as_posix()
        if '/__pycache__/' in rel:continue
        if rel.startswith('installed-check') and '/venv/' in rel:
            package=rel.split('/site-packages/',1)
            if len(package)!=2 or not package[1].startswith(('materials_boundaries/','materials_boundaries-')):continue
        external[str(p)]=sha(p)
    resolutions={}
    for n,digest in {**mapping['repo_files_sha256'],**mapping['native_files_sha256']}.items():
        if sha(ROOT/n)==digest:continue
        backup=EXT/'baseline-tables'/Path(n).name
        assert backup.is_file() and sha(backup)==digest,n
        resolutions[n]=dict(before_sha256=digest,archived_exact_bytes=str(backup),current_sha256=sha(ROOT/n))
    assert len(resolutions)==2
    tests=read(HERE/'AFFECTED_RESULTS_R1.json');installed=read(HERE/'INSTALLED_VALIDATION_R48.json')
    assert tests['successful'] and tests['tests']==19 and tests['inputs_unchanged']
    assert installed['native_package_inputs_unchanged'] and installed['installed_probe']['snapshot']==read(HERE/'APPLICATION_R48.json')['snapshot']
    entry=dict(schema='PBS-PBAT-hybrid-mechanical-local-final-review/1',repo_files_sha256={n:sha(ROOT/n) for n in sorted(files)},external_files_sha256=external,
        native_files_sha256=read(HERE/'APPLICATION_R48.json')['after_sha256'],mapping_before_pin_resolutions=resolutions,
        scope='Exact r48 local application,19 fresh daily database integration checks and real offline installation;not commit,push or remote CI',
        review_constraints='Read-only ownhash/JSON/schema/diff/limited installed queries and exports;no authorhelpers,testmodules,suites,fullgraph/history,writes/install/push')
    p=HERE/'REVIEW_FINAL_INPUTS_R48.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(entry,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(sha256=sha(p),repo=len(files),external=len(external),before_pin_resolutions=len(resolutions))))
if __name__=='__main__':main()
