"""Bind the unmodified approved r42 baseline and concrete twelve-cell candidate."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    prior=HERE.parent/'local-acceptance-r42';entry=prior/'REVIEW_FINAL_INPUTS_R42.json'
    assert sha(entry)=='2d0c88fd038773d006268e1d7fc305edaa1c2b9a69e9deb972606c2bb45965b5'
    pins=read(entry);review=read(prior/'INDEPENDENT_FINAL_REVIEW_R42.json')
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    assert all(sha(ROOT/n)==h for n,h in pins['repo_files_sha256'].items())
    assert all(sha(Path(n))==h for n,h in pins['external_files_sha256'].items())
    assert read(HERE/'CANDIDATE_CONSUMERS_R1.json')['all_twelve_new_records_complete']
    files=set(pins['repo_files_sha256'])
    files|={p.relative_to(ROOT).as_posix() for p in prior.iterdir() if p.is_file()}
    files|={p.relative_to(ROOT).as_posix() for p in HERE.iterdir() if p.is_file()}
    external=dict(pins['external_files_sha256'])
    for n in ('16','17'):
        p=ROOT.parent/('open-database-evidence/polymer-nr-notice-damping-20261111-r2/visual2025/page-'+n+'.png');external[str(p)]=sha(p)
    for p in (ROOT.parent/'open-database-evidence/polymer-nr-clay-thermal-response-mapping-20261111-r1').rglob('*'):
        if p.is_file():external[str(p)]=sha(p)
    obj=dict(schema='NR-clay-thermal-response-candidate-review/1',repo_files_sha256={n:sha(ROOT/n) for n in sorted(files)},external_files_sha256=external,native_files_sha256=pins['native_files_sha256'],scope='Twelve source facts,six existing composite identities,concrete unapplied mappings and complete candidate consumers;no runtime contract change,no native write,install,commit,push or remote CI',review_constraints='Read-only ownhash/JSON/schema/visual/diff/limited own small graph or existing-installed queries;no authorhelpers,testmodules,suites,fullgraph/history,writes,install,push')
    out=HERE/'REVIEW_INPUTS_R1.json'
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(sha256=sha(out),repo=len(files),external=len(external),native=3)))
if __name__=='__main__':main()
