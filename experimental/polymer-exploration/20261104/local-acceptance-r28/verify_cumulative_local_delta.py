"""Compare actual r28 native objects to the last published local Git commit."""
from copy import deepcopy
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database
BASE_COMMIT='4d4f8fa84451ab0481ec6c2cfbe3495209dad4b8'
TARGET='19079de9d0a0ad0808d77f9dc2c7681c88c1facc4c43e72ae7980eb64f35c491'
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert head==BASE_COMMIT
    native=Database();assert native.snapshot==TARGET
    data={};blob_hashes={}
    for name in native.data:
        raw=subprocess.check_output(['git','show',BASE_COMMIT+':materials_boundaries/data/'+name+'.json'],cwd=ROOT)
        data[name]=json.loads(raw);blob_hashes[name]=hashlib.sha256(raw).hexdigest()
    before=Database(data)
    assert len(before.properties)==5327 and len(before.states)==5212
    assert all(native.properties[k]==v for k,v in before.properties.items())
    assert all(native.states[k]==v for k,v in before.states.items())
    assert native.identities==before.identities and native.grades==before.grades
    assert set(native.sources)==set(before.sources)
    new_props={k:v for k,v in native.properties.items() if k not in before.properties}
    new_states={k:v for k,v in native.states.items() if k not in before.states}
    assert len(new_props)==8 and len(new_states)==6
    assert sum(p['quantity']=='glass_transition_temperature' for p in new_props.values())==6
    assert sum(p['quantity']=='melting_peak_temperature' for p in new_props.values())==2
    source_delta={}
    for sid,old in before.sources.items():
        new=native.sources[sid]
        if new==old:continue
        assert {k for k in new if new[k]!=old[k]}=={'claim_notes'}
        assert new['claim_notes'][:len(old['claim_notes'])]==old['claim_notes']
        restored=deepcopy(new);restored['claim_notes']=deepcopy(old['claim_notes']);assert restored==old
        source_delta[sid]=len(new['claim_notes'])-len(old['claim_notes'])
    assert source_delta=={'tarasov_2022_pna_bpf_epoxy':1,'abbasi_2022_manure_phbv':2}
    value=dict(status='cumulative_local_r26_r28_growth_verified',baseline_git_head=BASE_COMMIT,
        baseline_snapshot=before.snapshot,current_snapshot=native.snapshot,baseline_git_blob_sha256=blob_hashes,
        all_5327_published_property_objects_complete_unchanged=True,all_5212_published_state_objects_complete_unchanged=True,
        identity_and_grade_objects_complete_unchanged=True,new_identities_grades_sources=0,
        new_property_ids=sorted(new_props),new_state_ids=sorted(new_states),new_properties=8,new_states=6,
        new_properties_by_quantity={'glass_transition_temperature':6,'melting_peak_temperature':2},
        source_claim_notes_append_only=source_delta,
        note='One read-only published-checkpoint object comparison,not a historical test/commit replay or release approval.',
        committed_this_batch=False,pushed_this_batch=False,merged_main=False,deployed=False)
    target=Path(__file__).resolve().parent/'CUMULATIVE_LOCAL_DELTA_R26_R28.json'
    with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(status=value['status'],properties=8,states=6,published_old_properties_unchanged=5327)))
if __name__=='__main__':main()
