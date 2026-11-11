"""Bounded complete joins/exports for the unapplied four-cell candidate."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-thermal-response-mapping-20261111-r2'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import resolve_material
def read(n):return json.loads((HERE/n).read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    EXT.mkdir(exist_ok=False);before=Database();data=deepcopy(before.data)
    pins={n:sha(ROOT/'materials_boundaries/data'/n) for n in ('materials.json','reference_properties.json','sources.json')}
    props=read('NEW_PROPERTIES_R1.json');states=read('NEW_STATES_R1.json');source=read('SOURCE_UPDATE_R1.json');method=read('NEW_METHOD_SOURCE_R1.json');primary=props[0]['source_id']
    assert before.sources[primary]==source['before']
    data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props)
    data['sources']['records']=[source['after'] if s['id']==primary else s for s in data['sources']['records']]+[method]
    db=Database(data);assert db.snapshot==read('VALIDATION_R1.json')['candidate_snapshot']
    assert not list(db.records(source=method['id']))
    checks=[]
    for name,filters,count in [('new-four',dict(quantity='thermal_response_characteristic_time',source=primary),4),
        ('natural-two',dict(query='state_smr10_bianchi2025_nr_thermal_response_natural_convection'),2),
        ('forced-two',dict(query='state_smr10_bianchi2025_nr_thermal_response_forced_convection'),2),
        ('existing-NR-fourteen',dict(query='mat_smr10_bianchi2025_nr',source=primary),14),
        ('complete-source-twenty',dict(source=primary),20)]:
        rows=list(db.records(**filters));assert len(rows)==count,(name,len(rows))
        expected=deepcopy({r['record_id']:r for r in rows})
        db.export(EXT/name,**filters);assert read_snapshot(EXT/name)[1]==expected
        for row in rows:
            assert row['property']==db.properties[row['record_id']]
            assert row['state']==db.states[row['property']['material_state_id']]
            assert row['identity']==db.identities[row['state']['identity_id']]
            if row['property']['quantity']=='thermal_response_characteristic_time':assert {s['id'] for s in row['sources']}=={primary,method['id']}
        rows[0]['property']['reported_value']['number']='999';rows[0]['sources'][0]['claim_notes'].append('detached')
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,complete_join_roundtrip=True,copy_isolation=True))
    for state in states:
        view=resolve_material(state['id'],*(data[n] for n in ('materials','reference_properties','sources')))
        assert {s['id'] for s in view['sources']}=={primary,method['id']}
        assert len(view['properties'])==2
    assert all(sha(ROOT/'materials_boundaries/data'/n)==h for n,h in pins.items())
    with (HERE/'CANDIDATE_CONSUMERS_R2.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(candidate_snapshot=db.snapshot,checks=checks,context_resolve_complete=True,primary_only_source_filter_preserved=True,all_four_time_records_include_complete_method_source=True,sets_overlap_not_independent_samples=True,native_hashes_unchanged=pins,native_applied=False,installation='not_run'),f,ensure_ascii=False,indent=2);f.write('\n')
    print('Candidate4time/2natural/2forced/14NR/20source completejoins/export/readback/copy passed;primary-source filter preserved,two-source joins/resolve complete;native unchanged')
if __name__=='__main__':main()
