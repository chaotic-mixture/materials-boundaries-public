"""Freeze actual work implementation and evidence; no native/Git writes."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'experimental/polymer-exploration/20261104/nr-work-to-break-source-contract-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-nr-work-contract-20261111-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    result=read(HERE/'AFFECTED_RESULTS_R1.json');assert result['successful'] and result['tests']==222
    inputs=read(HERE/'AFFECTED_INPUTS_R1.json');assert all(sha(ROOT/n)==h for n,h in inputs.items())
    approval=read(SOURCE/'INDEPENDENT_SOURCE_CONCEPT_REVIEW_R1.json')
    assert approval['decision']=='approved' and approval['review_inputs_sha256']==sha(SOURCE/'REVIEW_INPUTS_R1.json')
    native=read(SOURCE/'VALIDATION_R1.json')['native_before_sha256'];assert all(sha(ROOT/n)==h for n,h in native.items())
    files={ROOT/n for n in inputs}|{p for p in HERE.iterdir() if p.is_file()}|{p for p in SOURCE.iterdir() if p.is_file()}
    external={p for p in EXT.rglob('*') if p.is_file()}
    original=read(SOURCE/'REVIEW_INPUTS_R1.json')
    external|={Path(n) for n in original['external_files_sha256']}
    entry={'schema':'NR-work-concrete-implementation-review/1','repo_files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},
      'external_files_sha256':{str(p):sha(p) for p in sorted(external)},'native_files_sha256':native,
      'scope':'Production contract/schema/render/locales/tests only;not NR mapping/install/admission',
      'tests':result,'review_constraints':'Readonly own hashes/diff/schema/limited synthetic probes;no author helpers/tests/suites/fullgraph/history/writes/install/push'}
    p=HERE/'REVIEW_IMPLEMENTATION_INPUTS_R1.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(entry,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'sha256':sha(p),'repo':len(files),'external':len(external)}))
if __name__=='__main__':main()
