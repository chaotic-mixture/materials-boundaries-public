"""Bind actual phase execution inputs independently of broad review manifests."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent


def main():
    read=lambda p:json.loads(p.read_bytes())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    history=read(HERE/'HISTORICAL_PIN_RESOLUTIONS_R1.json');assert not history['unresolved']
    index={}
    for n,h in history['external_files_sha256'].items():
        assert sha(Path(n))==h,n;index.setdefault(h,n)
    base=HERE.parent
    specifications=[
        ('dsc_impl_r1_392','dsc-crystallinity-implementation-r1','AFFECTED_INPUTS_R1.json','AFFECTED_RESULTS_R1.json'),
        ('dsc_impl_r2_393','dsc-crystallinity-implementation-r2','AFFECTED_INPUTS_R1.json','AFFECTED_RESULTS_R1.json'),
        ('dsc_target_r3_17','dsc-crystallinity-implementation-r3','TARGETED_INPUTS_R3.json','TARGETED_RESULTS_R3.json'),
        ('ftir_impl_409','ftir-band-area-ratio-implementation-r1','AFFECTED_INPUTS_R1.json','AFFECTED_RESULTS_R1.json'),
        ('sec_impl_r1_428','sec-molar-mass-implementation-r1','AFFECTED_INPUTS_R1.json','AFFECTED_RESULTS_R1.json'),
        ('sec_target_r2_21','sec-molar-mass-implementation-r2','AFFECTED_INPUTS_R2.json','AFFECTED_RESULTS_R2.json'),
        *[(f'local_r{phase}_daily19',f'local-acceptance-r{phase}','AFFECTED_INPUTS_R1.json','AFFECTED_RESULTS_R1.json') for phase in (69,70,71,72)],
        *[(f'local_r{phase}_package',f'local-acceptance-r{phase}',f'PACKAGE_INPUTS_R{phase}.json',f'INSTALLED_VALIDATION_R{phase}.json') for phase in (69,70,71,72)],
        ('delivery_actual_package','delivery-r69-r72','PACKAGE_INPUTS_DELIVERY.json','INSTALLED_VALIDATION_DELIVERY.json'),
    ]
    reports=[]
    for phase,folder,inputs,outcome in specifications:
        path=base/folder/inputs;resultpath=base/folder/outcome;pins=read(path);changed=[];matching=0
        for n,h in pins.items():
            if sha(ROOT/n)==h:matching+=1
            else:
                assert h in index,(phase,n,h)
                changed.append(dict(path=n,sha256=h,resolved_external_path=index[h]))
        reports.append(dict(phase=phase,input_manifest=path.relative_to(ROOT).as_posix(),input_manifest_sha256=sha(path),outcome=resultpath.relative_to(ROOT).as_posix(),outcome_sha256=sha(resultpath),original_inputs=len(pins),current_matching=matching,historical_resolutions=changed))
    latest=next(r for r in reports if r['phase']=='local_r72_daily19')
    assert latest['original_inputs']==latest['current_matching']==98
    package=next(r for r in reports if r['phase']=='delivery_actual_package')
    assert package['original_inputs']==package['current_matching']==81
    previous=next(r for r in reports if r['phase']=='local_r72_package')
    assert previous['current_matching']==80 and [r['path'] for r in previous['historical_resolutions']]==['README.md']
    report=dict(bindings=reports,rule='Every execution retains its own original code/data and outcome;matching inputs do not create a rerun;counts never added',
                current_daily19_reused_identical98inputs=True,new_delivery_actual81input_installation=True,
                new_tests='not_run_doc_only_changes',full_history='not_run',HTTP='not_run',remoteCI='pending_exact_commit_push')
    with (HERE/'EXECUTION_SCOPE_BINDINGS_R1.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([dict(phase=r['phase'],inputs=r['original_inputs'],matching=r['current_matching'],archived=len(r['historical_resolutions'])) for r in reports]),flush=True)


if __name__=='__main__':main()
