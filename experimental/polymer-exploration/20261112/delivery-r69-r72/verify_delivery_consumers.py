"""Recover all 17 additions through complete source-qualified native exports."""
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261112-r69-r72'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot


def main():
    read=lambda p:json.loads(p.read_bytes())
    prep=read(HERE/'PREPARATION_R1.json');db=Database();assert db.snapshot==prep['snapshot']
    expected={};states={}
    for name in ('dsc-crystallinity-native-mapping-r2','indulin-tga-native-mapping-r1','ftir-band-area-ratio-native-mapping-r2','sec-molar-mass-native-mapping-r1'):
        folder=HERE.parent/name
        for p in read(folder/'NEW_PROPERTIES_R1.json'):
            assert p['id'] not in expected;expected[p['id']]=p
            assert db.properties[p['id']]==p
        for s in read(folder/'NEW_STATES_R1.json'):
            assert s['id'] not in states;states[s['id']]=s
            assert db.states[s['id']]==s
    assert set(expected)==set(prep['new_property_ids']) and len(expected)==17
    assert set(states)==set(prep['new_state_ids']) and len(states)==13
    checks=[];seen=set()
    groups=[('pbs-source-all',{'source':'ewurum_mcdonald_2025_pbs_lignin'},170),('phbv-source-all',{'source':'abbasi_2022_manure_phbv'},15)]
    for name,filters,count in groups:
        rows=list(db.records(**filters));assert len(rows)==count
        full=deepcopy({r['record_id']:r for r in rows});target=EXT/('accepted-'+name)
        db.export(target,**filters);assert read_snapshot(target)[1]==full
        for row in rows:
            assert row['property']==db.properties[row['record_id']]
            assert row['state']==db.states[row['property']['material_state_id']]
            if row['record_id'] in expected:
                seen.add(row['record_id']);assert row['property']==expected[row['record_id']]
        rows[0]['property']['scope_note']='detached';rows[0]['sources'][0]['claim_notes'].append('detached')
        assert {r['record_id']:r for r in db.records(**filters)}==full
        checks.append(dict(name=name,filters=filters,records=count,full_query_export_restore_equal=True,copy_isolation=True))
    assert seen==set(expected)
    with (EXT/'EXPECTED_NEW_RECORDS_DELIVERY.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(expected,ensure_ascii=False,indent=2)+'\n')
    receipt=dict(snapshot=db.snapshot,groups=checks,all17newproperties_match_approved_mappings=True,all13newstates_match_approved_mappings=True,all17covered_by_full_source_exports=True,
                 external_files_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in EXT.rglob('*') if p.is_file() and p.name in ('manifest.json','records.jsonl','EXPECTED_NEW_RECORDS_DELIVERY.json')},
                 scope='Complete170/15 source objects cover exact17 additions;185propertyrecords,not sample/material/experiment counts;not new tests or scientific certification')
    with (HERE/'CONSUMERS_DELIVERY.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(groups=checks,new_properties_covered=len(seen))),flush=True)


if __name__=='__main__':main()
