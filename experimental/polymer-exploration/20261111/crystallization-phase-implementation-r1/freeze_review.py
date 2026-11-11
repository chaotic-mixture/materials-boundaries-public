"""Freeze implementation evidence without changing any native table."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'pbs-pbat-crystallization-source-proposal-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-crystallization-phase-implementation-20261111-r1'
def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert baseline=='5cc2f28c784b3f457bef025d570161fac0e63e49'
    entry=SOURCE/'REVIEW_INPUTS_R1.json'; approval=read(SOURCE/'INDEPENDENT_SOURCE_CONCEPT_REVIEW_R1.json')
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(entry)
    source=read(entry); before=read(HERE/'BEFORE_IMPLEMENTATION_R1.json'); resolutions={}
    for n,h in source['repo_files_sha256'].items():
        if sha(ROOT/n)==h: continue
        b=before['files'][n]; assert b['before_sha256']==h==sha(Path(b['archived_exact_bytes']))
        resolutions[n]=dict(before_sha256=h,archived_exact_bytes=b['archived_exact_bytes'],current_sha256=sha(ROOT/n))
    assert len(resolutions)==3
    pins=read(HERE/'AFFECTED_INPUTS_R1.json'); tests=read(HERE/'AFFECTED_RESULTS_R1.json')
    assert tests['tests']==266 and tests['successful'] and tests['failures']==tests['errors']==tests['skipped']==0 and tests['inputs_unchanged']
    assert all(sha(ROOT/n)==h for n,h in pins.items())
    native=source['native_files_sha256']; assert all(sha(ROOT/n)==h for n,h in native.items())
    assert read(HERE/'NATIVE_COMPATIBILITY_R1.json')['native_unchanged']
    old=read(Path(before['files']['schemas/reference_properties.schema.json']['archived_exact_bytes']))
    current=read(ROOT/'schemas/reference_properties.schema.json')
    assert current['$defs']['property']['oneOf'][:15]==old['$defs']['property']['oneOf']
    assert len(current['$defs']['property']['oneOf'])==16
    files=set(source['repo_files_sha256'])|set(pins)
    for folder in (SOURCE,HERE,HERE.parent/'polymer-condition-gaps-current-r2'):
        files|={p.relative_to(ROOT).as_posix() for p in folder.iterdir() if p.is_file()}
    external=dict(source['external_files_sha256'])
    for p in EXT.rglob('*'):
        if p.is_file(): external[str(p)]=sha(p)
    assert all(sha(Path(n))==h for n,h in external.items())
    obj=dict(schema='crystallization-phase-implementation-review/1',baseline_commit=baseline,repo_files_sha256={n:sha(ROOT/n) for n in sorted(files)},external_files_sha256=external,native_files_sha256=native,source_before_pin_resolutions=resolutions,scope='Strict nonisothermal phase-qualified sixteenth branch;266 fresh affected checks;unchanged 5494-property native graph;no four-source-cell mapping,installation or admission',review_constraints='Read-only own hashes/JSON/schema/diff and limited self-built fictional small graphs;no authorhelpers,testmodules,suites,fullgraph/history,writes/cache/install/Git/push')
    out=HERE/'REVIEW_IMPLEMENTATION_INPUTS_R1.json'
    with out.open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
    print(json.dumps(dict(sha256=sha(out),repo=len(files),external=len(external),resolutions=len(resolutions))))
if __name__=='__main__': main()
