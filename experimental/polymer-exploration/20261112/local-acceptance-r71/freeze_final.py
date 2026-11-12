"""Bind real r71 installation and resolve historical inputs to preserved bytes."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
BASE=HERE.parent;EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r71'


def main():
    load=lambda p:json.loads(p.read_text('utf-8'))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    def write(p,obj):
        with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    installed=load(HERE/'INSTALLED_VALIDATION_R71.json')
    assert installed['native_package_inputs_unchanged'] and installed['installed_probe']['properties']==5754
    wheel=Path(installed['wheel_path_hint']);assert sha(wheel)==installed['wheel_sha256']
    current=(ROOT/'README.md').read_bytes();staged=(EXT/'installed-check/source/README.md').read_bytes()
    assert current==staged and b'\r' not in current
    with zipfile.ZipFile(wheel) as z:
        metadata=z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA')))
    body=metadata.replace(b'\r\n',b'\n').split(b'\n\n',1)[1]
    assert body==current
    binding=dict(current_readme_sha256=sha(ROOT/'README.md'),staged_readme_sha256=sha(EXT/'installed-check/source/README.md'),wheel_sha256=sha(wheel),metadata_body_matches_current_readme_after_newline_normalization_only=True)
    if (HERE/'DOCUMENT_PACKAGE_BINDING_R71.json').exists():assert load(HERE/'DOCUMENT_PACKAGE_BINDING_R71.json')==binding
    else:write(HERE/'DOCUMENT_PACKAGE_BINDING_R71.json',binding)
    entries={
        'mapping_r2':BASE/'ftir-band-area-ratio-native-mapping-r2/REVIEW_MAPPING_INPUTS_R2.json',
        'implementation_409':BASE/'ftir-band-area-ratio-implementation-r1/REVIEW_IMPLEMENTATION_INPUTS_R1.json',
        'previous_r70_final':BASE/'local-acceptance-r70/REVIEW_FINAL_INPUTS_R70.json',
    }
    loaded={k:load(p) for k,p in entries.items()}
    paths=set();external={}
    for label,e in loaded.items():
        paths.update(ROOT/n for n in e['repo_files_sha256'])
        paths.add(entries[label]);external.update(e.get('external_files_sha256',{}))
    paths.update(HERE.iterdir())
    paths.update([BASE/'ftir-band-area-ratio-native-mapping-r2/INDEPENDENT_MAPPING_REVIEW_R2.json',BASE/'ftir-band-area-ratio-native-mapping-r2/CURRENT_STATUS.zh.md',BASE/'local-acceptance-r70/INDEPENDENT_FINAL_REVIEW_R70.json',BASE/'local-acceptance-r70/FINAL_STATUS.zh.md'])
    for filename in ['AFFECTED_INPUTS_R1.json','PACKAGE_INPUTS_R71.json']:
        for n,h in load(HERE/filename).items():
            p=ROOT/n;assert sha(p)==h,n;paths.add(p)
    for p in EXT.rglob('*'):
        if p.is_file() and 'venv' not in p.relative_to(EXT).parts:external[str(p)]=sha(p)
    # All source archives were already pinned; verify before using any as a resolver.
    index={}
    for n,h in external.items():
        p=Path(n);assert p.is_file() and sha(p)==h,n;index.setdefault(h,[]).append(n)
    history={}
    for label,e in loaded.items():
        pins={**e['repo_files_sha256'],**e['native_files_sha256']};drift={};matching=0
        for n,h in pins.items():
            if sha(ROOT/n)==h:matching+=1
            else:
                assert h in index,(label,n,h)
                drift[n]=dict(sha256=h,resolved_to=index[h][0])
        history[label]=dict(entry=entries[label].relative_to(ROOT).as_posix(),entry_sha256=sha(entries[label]),original_inputs=len(pins),current_matching=matching,changed_inputs=drift)
    # Execution input scope is independent of the larger review manifest.
    execution=load(BASE/'ftir-band-area-ratio-implementation-r1/AFFECTED_INPUTS_R1.json')
    changed={n:dict(sha256=h,resolved_to=index[h][0]) for n,h in execution.items() if sha(ROOT/n)!=h}
    assert set(changed)=={'materials_boundaries/data/materials.json','materials_boundaries/data/reference_properties.json'}
    package=load(BASE/'local-acceptance-r70/PACKAGE_INPUTS_R70.json')
    old_package_drift={n:dict(sha256=h,resolved_to=index[h][0]) for n,h in package.items() if sha(ROOT/n)!=h}
    assert set(old_package_drift)=={'materials_boundaries/_material_derivation.py','materials_boundaries/data/material_locales.json','materials_boundaries/data/materials.json','materials_boundaries/data/reference_properties.json','materials_boundaries/material_presentation.py','materials_boundaries/material_references.py','README.md'}
    app=load(HERE/'APPLICATION_R71.json');assert app['snapshot']=='70d595937504a14a5b93f12906834b5dff2eddefa0cbf4cc4566d5570a09f85d'
    entry=dict(schema='polymer-r71-final-review/1',baseline_commit='fb996df80be67aba2896169935f997ad08655690',repo_files_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},external_files_sha256=external,native_files_sha256=app['after_sha256'],historical_source_resolutions=history,implementation_409_input_comparison=dict(original_inputs=len(execution),current_matching=len(execution)-len(changed),changed_inputs=changed,scope='409 passed on5753 baseline;148current+2archived,not409rerunon5754'),r70_package_input_comparison=dict(original_inputs=len(package),current_matching=len(package)-len(old_package_drift),changed_inputs=old_package_drift),expected=dict(snapshot=app['snapshot'],properties=5754,states=5432,sources=134,new_properties=1,new_contexts=1,new_identities=0,new_sources=0),scope='Exact1FTIRproperty/1context,5754current19checks97stable,actual80input76payload installation,full1/12/12 consumers and README binding. Historical409150inputs resolved,not new fullsuite/history/HTTP/remoteCI',pushed=False)
    write(HERE/'REVIEW_FINAL_INPUTS_R71.json',entry)
    print(json.dumps(dict(entry_sha256=sha(HERE/'REVIEW_FINAL_INPUTS_R71.json'),repo=len(entry['repo_files_sha256']),external=len(external),native=3,drift={k:len(v['changed_inputs']) for k,v in history.items()},old_package_drift=len(old_package_drift)),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
