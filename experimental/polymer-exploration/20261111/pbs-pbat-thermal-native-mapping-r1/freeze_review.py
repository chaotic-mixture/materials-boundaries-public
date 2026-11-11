"""Freeze exact eight-cell mapping against the approved implementation and unchanged native baseline."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
IMPL=HERE.parent/'dtg-unknown-ordinal-implementation-r1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    entry=IMPL/'REVIEW_IMPLEMENTATION_INPUTS_R1.json';pins=read(entry);review=read(IMPL/'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json')
    assert sha(entry)=='fa0df5f235265210d50bfec99dfa8510e94a7668543bf3a1963511cc79572357' and review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    assert all(sha(ROOT/n)==h for n,h in pins['repo_files_sha256'].items())
    assert all(sha(Path(n))==h for n,h in pins['external_files_sha256'].items())
    assert all(sha(ROOT/n)==h for n,h in pins['native_files_sha256'].items())
    assert read(HERE/'CANDIDATE_CONSUMERS_R1.json')['all_eight_new_records_complete']
    files=set(pins['repo_files_sha256'])
    for folder in (HERE,IMPL):files|={p.relative_to(ROOT).as_posix() for p in folder.iterdir() if p.is_file()}
    external=dict(pins['external_files_sha256'])
    for p in (ROOT.parent/'open-database-evidence/polymer-pbs-pbat-thermal-mapping-20261111-r1').rglob('*'):
        if p.is_file():external[str(p)]=sha(p)
    obj=dict(schema='PBS-PBAT-thermal-native-mapping-review/1',repo_files_sha256={n:sha(ROOT/n) for n in sorted(files)},external_files_sha256=external,native_files_sha256=pins['native_files_sha256'],scope='Eight exact thermal mappings and8TGA/DSC contexts under approved unknown ordinal implementation,complete consumers;no actual native write,install,commit,push or CI',review_constraints='Read-only ownhash/JSON/schema/visual/diff and own small graph checks;no authorhelpers,testmodules,suites,fullgraph/history,writes/install/push')
    out=HERE/'REVIEW_INPUTS_R1.json'
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(sha256=sha(out),repo=len(files),external=len(external),native=3)))
if __name__=='__main__':main()
