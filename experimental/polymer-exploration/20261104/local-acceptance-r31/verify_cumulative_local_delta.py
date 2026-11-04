"""Compare accepted r29/r30/r31 additions to unchanged Git baseline without history replay."""
from pathlib import Path
import json,hashlib,subprocess,sys
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
AREA=OUT.parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
def read(p):return json.loads(p.read_bytes())
def main():
    assert not (OUT/'CUMULATIVE_LOCAL_DELTA_R29_R31.json').exists()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert head=='1893455b0dc75d9ac7e7c27fc798efd7de8a0d04'
    data={n:json.loads(subprocess.check_output(['git','show',head+':materials_boundaries/data/'+n+'.json'],cwd=ROOT)) for n in ['materials','reference_properties','sources']}
    old=Database(data);current=Database();assert len(old.properties)==5335 and len(old.states)==5218
    assert current.snapshot=='b4c2f6c279400bd67848c4ec049a7050f9c984ad4c247702693596b1da74a306'
    assert all(current.properties[k]==v for k,v in old.properties.items()) and all(current.states[k]==v for k,v in old.states.items())
    assert current.identities==old.identities and current.grades==old.grades and set(current.sources)==set(old.sources)
    packets=[read(AREA/n/'MAPPING_FACTS_R1.json') for n in ['pbs-existing-dsc-native-r1','pbs-existing-dma-tg-native-r1','pbs-existing-flexural-native-r1']]
    props={k:v for p in packets for k,v in p['property_records'].items()};states={k:v for p in packets for k,v in p['state_records'].items()}
    assert len(props)==36 and len(states)==27
    assert set(current.properties)-set(old.properties)==set(props) and set(current.states)-set(old.states)==set(states)
    assert all(current.properties[k]==v for k,v in props.items()) and all(current.states[k]==v for k,v in states.items())
    sid='ewurum_mcdonald_2025_pbs_lignin';restored=deepcopy(current.sources[sid]);notes=restored['claim_notes'][-3:];restored['claim_notes']=restored['claim_notes'][:-3]
    assert restored==old.sources[sid] and all(current.sources[k]==v for k,v in old.sources.items() if k!=sid)
    result={'baseline_git_commit':head,'baseline_snapshot':old.snapshot,'current_snapshot':current.snapshot,'all_5335_baseline_property_objects_unchanged':True,'all_5218_baseline_state_objects_unchanged':True,'new_property_ids':sorted(props),'new_state_ids':sorted(states),'new_properties':36,'new_states':27,'new_identities_grades_sources':0,'independent_physical_coverage':'not_established;state counts are catalogue records including9unresolved flexural contexts','only_source_change':'Ewurum source appended exactly3 claim notes','appended_source_notes':notes,'full_history_regression':'not_run;three baseline blobs read only','pushed':False}
    with (OUT/'CUMULATIVE_LOCAL_DELTA_R29_R31.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'old_properties_unchanged':5335,'old_states_unchanged':5218,'new_properties':36,'new_states':27}))
if __name__=='__main__':main()
