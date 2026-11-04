"""Apply the exact reviewed nine-state DSC supplement locally with recovery copies."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,shutil,sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def bound(entry,review):
    assert review['decision']=='approved' and review['review_inputs_sha256']==sha(entry)
    data=read(entry)
    for key in ['repo_files_sha256','native_files_sha256','external_files_sha256']:
        for name,h in data.get(key,{}).items():assert sha(Path(name) if key=='external_files_sha256' else ROOT/name)==h,name
    return data

def main():
    assert not (OUT/'APPLICATION_INTENT_R30.json').exists() and not (OUT/'APPLICATION_R30.json').exists()
    mapping=AREA/'pbs-existing-dma-tg-native-r1';installation=AREA/'installed-preview-r30'
    manifest=bound(mapping/'REVIEW_INPUTS_R1.json',read(mapping/'INDEPENDENT_MAPPING_REVIEW_R1.json'))
    reviewed=bound(installation/'REVIEW_INPUTS_R30.json',read(installation/'INDEPENDENT_REVIEW_R30.json'))
    install=Path(reviewed['external_install_directory_hint']);preview=EXT/'polymer-pbs-dma-tg-native-preview-20261104-r1/native-tables'
    result=read(install/'INSTALLED_VALIDATION_R30.json');assert result['installed']['snapshot']==manifest['preview_snapshot']
    assert result['installed']['current_graph_contracts']['status']=='material_contracts_passed'
    assert read(install/'ARTIFACT_RECORDS_AND_EXPORT_R30.json')['status']=='artifact_records_and_complete_export_passed'
    consumer=read(install/'consumer/CURRENT_CONSUMER_VALIDATION_R30.json')
    assert consumer['core_snapshot']==manifest['preview_snapshot'] and consumer['complete_resolved_states_equal_core']==9 and consumer['new_properties_exact_record_and_query_equal']==9
    before=Database();assert before.snapshot==manifest['baseline_snapshot']
    after=Database({n:read(preview/(n+'.json')) for n in before.data});assert after.snapshot==manifest['preview_snapshot']
    facts=read(mapping/'MAPPING_FACTS_R1.json');states=facts['state_records'];props=facts['property_records']
    assert len(states)==len(props)==9
    assert set(after.properties)-set(before.properties)==set(props) and set(after.states)-set(before.states)==set(states)
    assert all(after.properties[k]==v for k,v in before.properties.items()) and all(after.states[k]==v for k,v in before.states.items())
    assert after.identities==before.identities and after.grades==before.grades
    assert all(after.properties[k]==v for k,v in props.items()) and all(after.states[k]==v for k,v in states.items())
    sid=facts['source_record']['id'];assert after.sources[sid]==facts['source_record'] and set(after.sources)==set(before.sources)
    restored=deepcopy(after.sources[sid]);restored['claim_notes'].pop();assert restored==before.sources[sid]
    assert all(after.sources[k]==v for k,v in before.sources.items() if k!=sid)
    payload=read(install/'BUILD_INPUTS_R30.json')['staged_inputs']
    site=install/'venv/Lib/site-packages'
    for name,digest in payload.items():
        if name.startswith('materials_boundaries/'):
            assert sha(site/name)==digest,name
            if name!='materials_boundaries/_version.py':
                expected=preview/Path(name).name if name.startswith('materials_boundaries/data/') and Path(name).name in ['materials.json','reference_properties.json','sources.json'] else ROOT/name
                assert sha(expected)==digest,name
    _,exported=read_snapshot(install/('installed-export-'+sid))
    assert exported=={r['property']['id']:r for r in after.records(source=sid)} and len(exported)==37
    backup=EXT/'polymer-native-acceptance-20261104-r30/baseline-tables';backup.mkdir(parents=True,exist_ok=False)
    previous={};target={}
    for name in before.data:
        p=ROOT/'materials_boundaries/data'/(name+'.json');previous[p.name]=sha(p);target[p.name]=sha(preview/p.name)
        shutil.copyfile(p,backup/p.name);assert sha(backup/p.name)==previous[p.name]
    write(OUT/'APPLICATION_INTENT_R30.json',{'baseline_snapshot':before.snapshot,'target_snapshot':after.snapshot,'baseline_table_sha256':previous,'target_table_sha256':target,'recovery_copy_hint':str(backup),'installed_graph_reused_via_exact_bytes':True,'full_history_regression':'not_run'})
    for name in before.data:
        source=preview/(name+'.json');destination=ROOT/'materials_boundaries/data'/source.name
        assert source.resolve().is_relative_to(EXT) and destination.resolve().is_relative_to(ROOT/'materials_boundaries/data')
        shutil.copyfile(source,destination);assert sha(destination)==target[source.name]
    native=Database();assert native.snapshot==after.snapshot and native.data==after.data
    result={'status':'reviewed_candidate_applied_locally','applied_at_utc':datetime.now(timezone.utc).isoformat(),'before_snapshot':before.snapshot,'after_snapshot':native.snapshot,'native_table_sha256':target,'counts':{'identities':len(native.identities),'grades':len(native.grades),'states':len(native.states),'properties':len(native.properties),'sources':len(native.sources)},'all_old_5344_property_objects_unchanged':True,'all_old_5227_state_objects_unchanged':True,'new_properties':9,'new_states':9,'new_identities':0,'source_change':'one appended claim note only','installed_payload_equal_native_except_isolated_version':True,'installed_exports_equal_native':37,'graph_contracts':'reused exact approved installed graph and identical three tables;no redundant graph/history rerun','unit_suites':'pending_scoped_daily_check','pushed':False,'merged_main':False,'deployed':False}
    write(OUT/'APPLICATION_R30.json',result)
    print(json.dumps({'status':result['status'],'snapshot':native.snapshot,'properties':len(native.properties),'states':len(native.states)}))

if __name__=='__main__':main()
