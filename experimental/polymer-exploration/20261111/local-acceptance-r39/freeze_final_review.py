"""Bind actual r39 native/install evidence and resolve before-application pins."""
from pathlib import Path
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
MAPPING=HERE.parent/'nr-work-native-mapping-r1'
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r39'
CACHE={}
def read(p):return json.loads(p.read_bytes())
def sha(p):
    p=p.resolve()
    if p not in CACHE:CACHE[p]=hashlib.sha256(p.read_bytes()).hexdigest()
    return CACHE[p]
def write(n,v):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    mapping_entry=MAPPING/'REVIEW_INPUTS_R1.json';original=read(mapping_entry)
    receipt=MAPPING/'INDEPENDENT_MAPPING_REVIEW_R1.json';assert read(receipt)['decision']=='approved' and read(receipt)['review_inputs_sha256']==sha(mapping_entry)
    application=read(HERE/'APPLICATION_R39.json');assert all(sha(ROOT/n)==h for n,h in application['after_sha256'].items())
    results=read(HERE/'AFFECTED_RESULTS_R1.json');assert results['successful'] and results['tests']==222 and results['inputs_unchanged']
    inputs=read(HERE/'AFFECTED_INPUTS_R1.json');assert all(sha(ROOT/n)==h for n,h in inputs.items())
    resolutions=[]
    for field in ['repo_files_sha256','native_files_sha256']:
        for n,h in original[field].items():
            current=ROOT/n;resolved=current
            if sha(current)!=h:
                resolved=EXT/'baseline-tables'/Path(n).name
                assert n in application['after_sha256']
            assert sha(resolved)==h,n
            resolutions.append(dict(field=field,path=n,expected_sha256=h,resolved_path=str(resolved)))
    write('MAPPING_BEFORE_INPUT_RESOLUTION_R39.json',dict(entry_sha256=sha(mapping_entry),bindings=resolutions,unresolved=0,original_entry_rewritten=False))
    installed=read(HERE/'INSTALLED_VALIDATION_R39.json');assert installed['installed_probe']['snapshot']==application['snapshot']
    assert [c['records'] for c in installed['installed_probe']['exports']]==[1,7,13]
    repo={ROOT/n for n in original['repo_files_sha256']}|{ROOT/n for n in inputs}|{mapping_entry,receipt}
    repo|={p for p in HERE.iterdir() if p.is_file()}
    repo|={p for p in MAPPING.iterdir() if p.is_file()}
    external={Path(n) for n in original['external_files_sha256']}
    for folder in [EXT,ROOT.parent/'open-database-evidence/polymer-nr-work-mapping-20261111-r1']:
        for p in folder.rglob('*'):
            if p.is_file() and 'venv' not in p.relative_to(folder).parts:external.add(p)
    site=EXT/'installed-check/venv/Lib/site-packages'
    record=site/'materials_boundaries-0.35.0+polymerlocal.20261111.r39.dist-info/RECORD'
    for row in csv.reader(record.read_text(encoding='utf-8').splitlines()):
        p=(site/row[0]).resolve();assert p.is_relative_to(EXT/'installed-check/venv');external.add(p)
    entry=dict(schema='NR-work-actual-application-install-review/1',repo_files_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(repo)},external_files_sha256={str(p):sha(p) for p in sorted(external)},snapshot=application['snapshot'],tests=results,scope='Actual applied1property/existingstate/source/current isolated install;not remoteCI',review_constraints='Readonly ownhash/JSON/wheel-RECORD/bounded existing-installed queries only;no authorhelpers/tests/suites/fullgraph/history/writes/install/push')
    write('REVIEW_FINAL_INPUTS_R39.json',entry)
    print(json.dumps(dict(sha256=sha(HERE/'REVIEW_FINAL_INPUTS_R39.json'),repo=len(repo),external=len(external))))
if __name__=='__main__':main()
