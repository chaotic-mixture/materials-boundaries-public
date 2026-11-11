"""Freeze exact four-phase content,current install,CLI and historical-byte evidence for review."""
from pathlib import Path
import csv,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EVIDENCE=ROOT.parent/'open-database-evidence';BASELINE='847be1bb03e37e330e8de18341dbfca6715bd8b0';CACHE={}
def read(p):return json.loads(p.read_bytes())
def sha(p):
    p=p.resolve()
    if p not in CACHE:CACHE[p]=hashlib.sha256(p.read_bytes()).hexdigest()
    return CACHE[p]
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASELINE
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='experimental/open-database'
    assert subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0
    application=read(HERE/'APPLICATION_R42_R45.json');approvals=application['phase_approvals']
    for r in ('R42','R43','R44','R45'):
        folder=HERE.parent/('local-acceptance-'+r.lower());entry=folder/('REVIEW_FINAL_INPUTS_'+r+'.json');receipt=folder/('INDEPENDENT_FINAL_REVIEW_'+r+'.json')
        review=read(receipt);assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
        assert approvals[r]==dict(entry_sha256=sha(entry),receipt_sha256=sha(receipt))
    stage=HERE.parent/'local-acceptance-r45';tests=read(stage/'AFFECTED_RESULTS_R1.json');pins=read(stage/'AFFECTED_INPUTS_R1.json')
    assert tests['tests']==246 and tests['successful'] and tests['failures']==tests['errors']==tests['skipped']==0
    assert all(sha(ROOT/n)==h for n,h in pins.items())
    package=read(HERE/'PACKAGE_INPUTS_R42_R45.json');assert len(package)==69 and all(sha(ROOT/n)==h for n,h in package.items())
    installed=read(HERE/'INSTALLED_VALIDATION_R42_R45.json');assert installed['native_package_inputs_unchanged'] and installed['installed_probe']['properties']==5486 and installed['installed_probe']['snapshot']==application['snapshot']
    cli=read(HERE/'DATABASE_CI_LOCAL_EQUIVALENT_R42_R45.json');assert cli['scoped_inputs_still_exact'] and all(c['exit_code']==0 for c in cli['commands'])
    history=read(HERE/'HISTORICAL_INPUT_RESOLUTION_R42_R45_R1.json');assert history['unresolved']==0 and len(history['historical_absence_conditions'])==2
    external=set()
    for context in history['contexts']:
        assert sha(ROOT/context['entry'])==context['entry_sha256']
        for item in context['resolved'].values():
            p=Path(item['resolved_path_hint']);assert sha(p)==item['sha256']
            if not p.is_relative_to(ROOT):external.add(p)
    for folder in (EVIDENCE/'polymer-consolidated-delivery-20261111-r42-r45',EVIDENCE/'polymer-native-acceptance-20261111-delivery-r42-r45'):
        external|={p for p in folder.rglob('*') if p.is_file() and 'venv' not in p.relative_to(folder).parts}
    environment=EVIDENCE/'polymer-native-acceptance-20261111-delivery-r42-r45/installed-check/venv';site=environment/'Lib/site-packages'
    records=list(site.glob('materials_boundaries-*.dist-info/RECORD'));assert len(records)==1
    for row in csv.reader(records[0].read_text('utf-8').splitlines()):
        p=(site/row[0]).resolve();assert p.is_relative_to(environment);external.add(p)
    actual=set()
    for args in (['diff','--name-only','-z'],['ls-files','--others','--exclude-standard','-z']):actual|={n for n in subprocess.check_output(['git',*args],cwd=ROOT).decode().split('\0') if n}
    allowed=set(read(HERE/'BEFORE_NEUTRAL_NAVIGATION_R1.json'))|{'materials_boundaries/_material_derivation.py','materials_boundaries/material_references.py','materials_boundaries/material_presentation.py','materials_boundaries/data/material_locales.json','materials_boundaries/data/materials.json','materials_boundaries/data/reference_properties.json','materials_boundaries/data/sources.json','schemas/materials.schema.json','schemas/reference_properties.schema.json'}
    for n in actual:
        assert n in allowed or n.startswith('tests/test_') or n.startswith('experimental/polymer-exploration/20261111/'),n
        assert (ROOT/n).is_file() and (ROOT/n).suffix.lower() in ('.py','.json','.md','.log') and (ROOT/n).stat().st_size<100*1024*1024,n
    prior=read(stage/'REVIEW_FINAL_INPUTS_R45.json');resolutions={};archives=read(HERE/'BEFORE_NEUTRAL_NAVIGATION_R1.json')
    for n,digest in prior['repo_files_sha256'].items():
        if sha(ROOT/n)==digest:continue
        binding=archives[n];backup=Path(binding['archived_exact_bytes']);assert sha(backup)==digest==binding['before_sha256']
        resolutions[n]=dict(before_sha256=digest,archived_exact_bytes=str(backup),current_sha256=sha(ROOT/n))
    assert len(resolutions)==5
    obj=dict(schema='r42-r45-consolidated-content-review/1',baseline_commit=BASELINE,snapshot=application['snapshot'],repo_files_sha256={n:sha(ROOT/n) for n in sorted(actual)},external_files_sha256={str(p):sha(p) for p in sorted(external)},r45_before_pin_resolutions=resolutions,phase_approvals=approvals,tests_scope='Reuse exact fresh r45 246 checks and114 unchanged execution inputs;three current CLI gates separately executed;no historical test replay',scope='Exact cumulative70property delta,current navigation,historical byte resolution,actual unified wheel and installed content;not commit,push or remote CI',review_constraints='Read-only own hashes/JSON/schema/diff and bounded existing-installed queries;no author helpers,test modules,suites,fullgraph/history,writes/install/push')
    out=HERE/'REVIEW_CONTENT_INPUTS_R42_R45_R1.json'
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(sha256=sha(out),repo=len(actual),external=len(external),history_contexts=history['context_count'],history_bindings=history['bindings'])))
if __name__=='__main__':main()
