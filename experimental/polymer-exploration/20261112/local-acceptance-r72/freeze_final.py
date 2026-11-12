"""Bind actual r72 installation, original source scope and historical inputs."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
BASE=HERE.parent;EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r72'


def main():
    load=lambda p:json.loads(p.read_text('utf-8'))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    def write(p,obj):
        with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    installed=load(HERE/'INSTALLED_VALIDATION_R72.json')
    assert installed['native_package_inputs_unchanged'] and installed['installed_probe']['properties']==5757
    wheel=Path(installed['wheel_path_hint']);assert sha(wheel)==installed['wheel_sha256']
    current=(ROOT/'README.md').read_bytes();staged=(EXT/'installed-check/source/README.md').read_bytes()
    assert current==staged and b'\r' not in current
    with zipfile.ZipFile(wheel) as z:
        metadata=z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA')))
    assert metadata.replace(b'\r\n',b'\n').split(b'\n\n',1)[1]==current
    binding=dict(current_readme_sha256=sha(ROOT/'README.md'),staged_readme_sha256=sha(EXT/'installed-check/source/README.md'),wheel_sha256=sha(wheel),metadata_body_matches_current_readme_after_newline_normalization_only=True)
    if (HERE/'DOCUMENT_PACKAGE_BINDING_R72.json').exists():assert load(HERE/'DOCUMENT_PACKAGE_BINDING_R72.json')==binding
    else:write(HERE/'DOCUMENT_PACKAGE_BINDING_R72.json',binding)
    entries={
        'mapping_r1':BASE/'sec-molar-mass-native-mapping-r1/REVIEW_MAPPING_INPUTS_R1.json',
        'implementation_r2':BASE/'sec-molar-mass-implementation-r2/REVIEW_IMPLEMENTATION_INPUTS_R2.json',
        'implementation_r1':BASE/'sec-molar-mass-implementation-r1/REVIEW_IMPLEMENTATION_INPUTS_R1.json',
        'previous_r71_final':BASE/'local-acceptance-r71/REVIEW_FINAL_INPUTS_R71.json',
    }
    loaded={k:load(p) for k,p in entries.items()};paths=set();external={}
    for label,e in loaded.items():
        paths.update(ROOT/n for n in e['repo_files_sha256']);paths.add(entries[label])
        external.update(e.get('external_files_sha256',{}))
    paths.update(HERE.iterdir())
    paths.update([BASE/'sec-molar-mass-native-mapping-r1/INDEPENDENT_MAPPING_REVIEW_R1.json',BASE/'sec-molar-mass-native-mapping-r1/CURRENT_STATUS.zh.md',BASE/'local-acceptance-r71/INDEPENDENT_FINAL_REVIEW_R71.json',BASE/'local-acceptance-r71/FINAL_STATUS.zh.md'])
    for name in ('AFFECTED_INPUTS_R1.json','PACKAGE_INPUTS_R72.json'):
        for n,h in load(HERE/name).items():
            p=ROOT/n;assert sha(p)==h,n;paths.add(p)
    for p in EXT.rglob('*'):
        if p.is_file() and 'venv' not in p.relative_to(EXT).parts:external[str(p)]=sha(p)
    index={}
    for n,h in external.items():
        p=Path(n);assert p.is_file() and sha(p)==h,n;index.setdefault(h,[]).append(n)
    def comparison(pins):
        drift={};matching=0
        for n,h in pins.items():
            if sha(ROOT/n)==h:matching+=1
            else:
                assert h in index,(n,h)
                drift[n]=dict(sha256=h,resolved_to=index[h][0])
        return dict(original_inputs=len(pins),current_matching=matching,changed_inputs=drift)
    history={}
    for label,e in loaded.items():
        r=comparison({**e['repo_files_sha256'],**e['native_files_sha256']})
        r.update(entry=entries[label].relative_to(ROOT).as_posix(),entry_sha256=sha(entries[label]))
        history[label]=r
    full=comparison(load(BASE/'sec-molar-mass-implementation-r1/AFFECTED_INPUTS_R1.json'))
    assert full['original_inputs']==153 and full['current_matching']==147 and len(full['changed_inputs'])==6
    full['scope']='R1428 passed on5754 baseline/oldstring shapes;147current+6archives,not428rerunon5757'
    targeted=comparison(load(BASE/'sec-molar-mass-implementation-r2/AFFECTED_INPUTS_R2.json'))
    assert targeted['original_inputs']==111 and targeted['current_matching']==109 and len(targeted['changed_inputs'])==2
    targeted['scope']='R2target21 passed on5754 baseline;109current+2nativearchives,not430fullsuite or historicalsum'
    oldpackage=comparison(load(BASE/'local-acceptance-r71/PACKAGE_INPUTS_R71.json'))
    assert set(oldpackage['changed_inputs'])=={'materials_boundaries/_material_derivation.py','materials_boundaries/data/material_locales.json','materials_boundaries/data/materials.json','materials_boundaries/data/reference_properties.json','materials_boundaries/material_presentation.py','materials_boundaries/material_references.py','README.md'}
    app=load(HERE/'APPLICATION_R72.json');assert app['snapshot']=='454ab12d97c41622dac4ed8d604e356537246869e64a0a6ce9ac289143e2a953'
    entry=dict(schema='polymer-r72-final-review/1',baseline_commit='fb996df80be67aba2896169935f997ad08655690',repo_files_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},external_files_sha256=external,native_files_sha256=app['after_sha256'],historical_source_resolutions=history,implementation_428_input_comparison=full,implementation_r2_target21_input_comparison=targeted,r71_package_input_comparison=oldpackage,expected=dict(snapshot=app['snapshot'],properties=5757,states=5433,sources=134,new_properties=3,new_contexts=1,new_identities=0,new_sources=0),scope='Exact3reproducedSECfacts/1context,current5757daily19checks,actual81input77payload installation,full3/15/15consumersandREADMEbinding. KnownGuho2020inheritance preserved;originalprotocol/identitycell/rightsunknown. Historical428/R2target21 resolvedseparately,not430/fullhistory/HTTP/remoteCI',pushed=False)
    write(HERE/'REVIEW_FINAL_INPUTS_R72.json',entry)
    print(json.dumps(dict(entry_sha256=sha(HERE/'REVIEW_FINAL_INPUTS_R72.json'),repo=len(entry['repo_files_sha256']),external=len(external),native=3,drift={k:len(v['changed_inputs']) for k,v in history.items()},historical428=full['current_matching'],historical21=targeted['current_matching'],old_package_changed=len(oldpackage['changed_inputs'])),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
