"""Bounded full joins/exports for the unapplied candidate; no native writes."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r41'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def read(n):return json.loads((HERE/n).read_bytes())
def main():
    assert EXT.is_dir()
    db=Database();prop=db.properties['refprop_smr10_bianchi2025_nr_thermal_conductivity']
    pins={n:hashlib.sha256((ROOT/'materials_boundaries/data'/n).read_bytes()).hexdigest() for n in ['materials.json','reference_properties.json','sources.json']}
    assert db.snapshot==read('APPLICATION_R41.json')['snapshot']
    checks=[]
    for name,filters,count in [('new-conductivity',dict(quantity='thermal_conductivity',source=prop['source_id']),1),
        ('existing-NR-ten',dict(query='mat_smr10_bianchi2025_nr',source=prop['source_id']),10),
        ('complete-source-sixteen',dict(source=prop['source_id']),16)]:
        rows=list(db.records(**filters));assert len(rows)==count
        expected=deepcopy({r['record_id']:r for r in rows})
        db.export(EXT/('accepted-'+name),**filters);assert read_snapshot(EXT/('accepted-'+name))[1]==expected
        candidate=ROOT.parent/'open-database-evidence/polymer-nr-conductivity-mapping-20261111-r1'/name
        assert read_snapshot(candidate)[1]==expected
        for row in rows:
            assert row['property']==db.properties[row['record_id']]
            assert row['state']==db.states[row['property']['material_state_id']]
            assert row['identity']==db.identities[row['state']['identity_id']]
        rows[0]['property']['reported_value']['number']='999'
        rows[0]['sources'][0]['claim_notes'].append('detached mutation')
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,complete_join_roundtrip=True,copy_isolation=True))
    assert all(hashlib.sha256((ROOT/'materials_boundaries/data'/n).read_bytes()).hexdigest()==h for n,h in pins.items())
    with (HERE/'APPLIED_CONSUMERS_R41.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(candidate_snapshot=db.snapshot,checks=checks,native_hashes_unchanged=pins,native_applied=True,installation='not_run'),f,indent=2);f.write('\n')
    print('Candidate1new/10NR/16source completejoins/export/readback/copyisolation passed;native equals candidate')
if __name__=='__main__':main()
