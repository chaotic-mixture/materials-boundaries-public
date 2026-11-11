"""Pin six exact candidates and their unchanged runtime/source baseline."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'pbs-pbat-hybrid-mechanical-source-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-pbs-pbat-hybrid-mechanical-mapping-20261111-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    e=SOURCE/'REVIEW_INPUTS_R1.json';approved=read(SOURCE/'INDEPENDENT_SOURCE_REVIEW_R1.json');pins=read(e)
    assert approved['decision']=='approved' and approved['review_inputs_sha256']==sha(e)
    for field in ('repo_files_sha256','external_files_sha256','native_files_sha256'):
        assert all(sha(Path(n) if field=='external_files_sha256' else ROOT/n)==h for n,h in pins[field].items())
    assert read(HERE/'CONSUMERS_R1.json')['six_new_records_complete']
    files=set(pins['repo_files_sha256'])
    for folder in (HERE,SOURCE):files|={p.relative_to(ROOT).as_posix() for p in folder.iterdir() if p.is_file()}
    files|={p.relative_to(ROOT).as_posix() for p in (ROOT/'materials_boundaries').rglob('*.py')}
    files|={p.relative_to(ROOT).as_posix() for p in (ROOT/'schemas').glob('*.json')}
    files.add('materials_boundaries/data/material_locales.json')
    external=dict(pins['external_files_sha256']);external.update({str(p):sha(p) for p in EXT.rglob('*') if p.is_file()})
    v=dict(schema='PBS-PBAT-hybrid-mechanical-mapping-review/1',repo_files_sha256={n:sha(ROOT/n) for n in sorted(files)},external_files_sha256=external,native_files_sha256=pins['native_files_sha256'],scope='Six real mechanical mappings on3existing revised states;current native unchanged;no application,installation or new test-suite claim',review_constraints='Read-only ownhash/JSON/schema/visual/diff/limited small graph or saved exports;no authorhelpers/testmodules/suites/fullgraph/history/writes/cache/install/Git/push')
    p=HERE/'REVIEW_INPUTS_R1.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(sha256=sha(p),repo=len(files),external=len(external),native=3)))
if __name__=='__main__':main()
