"""Freeze current exact cumulative content and verified supporting evidence."""
from pathlib import Path
import csv,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EVIDENCE=ROOT.parent/'open-database-evidence';CACHE={}
BASELINE='ba67983dc11ee8c92ef1c9890b4164adfaf4a83d'
def read(p):return json.loads(p.read_bytes())
def sha(p):
    p=p.resolve()
    if p not in CACHE:CACHE[p]=hashlib.sha256(p.read_bytes()).hexdigest()
    return CACHE[p]
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASELINE
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    assert subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0
    approvals={}
    for stage in ('r39','r40','r41'):
        folder=HERE.parent/('local-acceptance-'+stage);entry=folder/('REVIEW_FINAL_INPUTS_'+stage.upper()+'.json');receipt=folder/('INDEPENDENT_FINAL_REVIEW_'+stage.upper()+'.json')
        review=read(receipt);assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
        approvals[stage]=dict(entry_sha256=sha(entry),receipt_sha256=sha(receipt))
    stage=HERE.parent/'local-acceptance-r41';tests=read(stage/'AFFECTED_RESULTS_R1.json');pins=read(stage/'AFFECTED_INPUTS_R1.json')
    assert tests['tests']==236 and tests['successful'] and tests['failures']==tests['errors']==tests['skipped']==0
    assert all(sha(ROOT/n)==h for n,h in pins.items())
    package=read(HERE/'PACKAGE_INPUTS_R39_R41_R2.json');assert len(package)==69 and all(sha(ROOT/n)==h for n,h in package.items())
    installed=read(HERE/'INSTALLED_VALIDATION_R39_R41_R2.json');assert installed['native_package_inputs_unchanged'] and installed['installed_probe']['properties']==5416
    history=read(HERE/'HISTORICAL_INPUT_RESOLUTION_R39_R41_R2.json');assert history['context_count']==209 and history['bindings']==15712 and history['unresolved']==0 and len(history['historical_absence_conditions'])==2
    external=set()
    for context in history['contexts']:
        assert sha(ROOT/context['entry'])==context['entry_sha256']
        for item in context['resolved'].values():
            p=Path(item['resolved_path_hint']);assert sha(p)==item['sha256']
            if not p.is_relative_to(ROOT):external.add(p)
    for folder in (EVIDENCE/'polymer-consolidated-delivery-20261111-r39-r41',EVIDENCE/'polymer-native-acceptance-20261111-delivery-r39-r41'):
        external|={p for p in folder.rglob('*') if p.is_file() and 'venv' not in p.relative_to(folder).parts}
    for label in ('installed-check','installed-check-r2'):
        env=EVIDENCE/'polymer-native-acceptance-20261111-delivery-r39-r41'/label/'venv';site=env/'Lib/site-packages'
        records=list(site.glob('materials_boundaries-*.dist-info/RECORD'));assert len(records)==1
        for row in csv.reader(records[0].read_text('utf-8').splitlines()):
            p=(site/row[0]).resolve();assert p.is_relative_to(env);external.add(p)
    actual=set()
    for args in (['diff','--name-only','-z'],['ls-files','--others','--exclude-standard','-z']):actual|={n for n in subprocess.check_output(['git',*args],cwd=ROOT).decode().split('\0') if n}
    allowed=set(read(HERE/'BEFORE_DOCUMENT_BYTES_R39_R41.json'))|{'materials_boundaries/_material_derivation.py','materials_boundaries/material_references.py','materials_boundaries/material_presentation.py','materials_boundaries/data/material_locales.json','materials_boundaries/data/materials.json','materials_boundaries/data/reference_properties.json','materials_boundaries/data/sources.json','schemas/materials.schema.json','schemas/reference_properties.schema.json'}
    for n in actual:
        assert n in allowed or n.startswith('tests/test_') or n.startswith('experimental/polymer-exploration/20261111/') or n.startswith('experimental/polymer-exploration/20261104/nr-work-to-break-source-contract-r1/'),n
        assert (ROOT/n).is_file() and (ROOT/n).suffix.lower() in ('.py','.json','.md','.log'),n
    cli=read(HERE/'DATABASE_CI_LOCAL_EQUIVALENT_R39_R41.json');assert cli['scoped_inputs_still_exact'] and all(c['exit_code']==0 for c in cli['commands'])
    obj=dict(schema='r39-r41-consolidated-content-review/1',baseline_commit=BASELINE,snapshot=read(HERE/'APPLICATION_R39_R41.json')['snapshot'],repo_files_sha256={n:sha(ROOT/n) for n in sorted(actual)},external_files_sha256={str(p):sha(p) for p in sorted(external)},phase_approvals=approvals,tests_scope='Reuse exact fresh r41 236 checks and113 unchanged inputs;three current CLI gates separately executed;no historical test replay',scope='Exact cumulative delta,navigation,historical bytes,actual current package and installation;not commit,push or remote CI',review_constraints='Read-only own hashes/JSON/schema/diffs and bounded existing-installed queries;no author helpers,test modules,suites,fullgraph/history,writes/install/push')
    p=HERE/'REVIEW_CONTENT_INPUTS_R39_R41.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(sha256=sha(p),repo=len(actual),external=len(external))))
if __name__=='__main__':main()
