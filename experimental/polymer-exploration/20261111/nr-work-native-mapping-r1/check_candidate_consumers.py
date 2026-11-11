"""Bounded full joins/exports for the unapplied candidate; no native writes."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-nr-work-mapping-20261111-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def read(n):return json.loads((HERE/n).read_bytes())
def main():
    EXT.mkdir(exist_ok=False)
    before=Database();data=deepcopy(before.data)
    pins={n:hashlib.sha256((ROOT/'materials_boundaries/data'/n).read_bytes()).hexdigest() for n in ['materials.json','reference_properties.json','sources.json']}
    change=read('STATE_UPDATE_R1.json');source=read('SOURCE_UPDATE_R1.json');prop=read('NEW_PROPERTY_R1.json')
    assert before.states[change['before']['id']]==change['before']
    assert before.sources[source['source_id']]==source['baseline_source']
    data['materials']['records']=[change['after'] if s['id']==change['before']['id'] else s for s in data['materials']['records']]
    data['sources']['records']=[source['proposed_source'] if s['id']==source['source_id'] else s for s in data['sources']['records']]
    data['reference_properties']['records'].append(prop)
    db=Database(data);assert db.snapshot==read('VALIDATION_R1.json')['candidate_snapshot']
    checks=[]
    for name,filters,count in [('new-work',dict(quantity='volumetric_tensile_work_to_break',source=prop['source_id']),1),
        ('existing-NR-seven',dict(query='mat_smr10_bianchi2025_nr',source=prop['source_id']),7),
        ('complete-source-thirteen',dict(source=prop['source_id']),13)]:
        rows=list(db.records(**filters));assert len(rows)==count
        expected=deepcopy({r['record_id']:r for r in rows})
        db.export(EXT/name,**filters);assert read_snapshot(EXT/name)[1]==expected
        for row in rows:
            assert row['property']==db.properties[row['record_id']]
            assert row['state']==db.states[row['property']['material_state_id']]
            assert row['identity']==db.identities[row['state']['identity_id']]
        rows[0]['property']['reported_value']['number']='999'
        rows[0]['sources'][0]['claim_notes'].append('detached mutation')
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,complete_join_roundtrip=True,copy_isolation=True))
    assert all(hashlib.sha256((ROOT/'materials_boundaries/data'/n).read_bytes()).hexdigest()==h for n,h in pins.items())
    with (HERE/'CANDIDATE_CONSUMERS_R1.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(candidate_snapshot=db.snapshot,checks=checks,native_hashes_unchanged=pins,native_applied=False,installation='not_run'),f,indent=2);f.write('\n')
    print('Candidate1new/7NR/13source completejoins/export/readback/copyisolation passed;native unchanged')
if __name__=='__main__':main()
