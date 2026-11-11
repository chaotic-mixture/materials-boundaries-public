"""Check complete source joins and export recovery of the unapplied twelve-cell candidate."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-nr-clay-thermal-response-mapping-20261111-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import resolve_material
def read(n):return json.loads((HERE/n).read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not EXT.exists();EXT.mkdir()
    baseline=Database();pins={n:sha(ROOT/'materials_boundaries/data'/n) for n in ('materials.json','reference_properties.json','sources.json')}
    data=deepcopy(baseline.data);states=read('NEW_STATES_R1.json');props=read('NEW_PROPERTIES_R1.json');proposal=read('SOURCE_UPDATE_R1.json')
    primary=proposal['before']['id'];secondary='bianchi_2024_nr_crosslink_methods'
    assert baseline.sources[primary]==proposal['before']
    data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props)
    data['sources']['records']=[proposal['after'] if s['id']==primary else s for s in data['sources']['records']]
    db=Database(data);assert db.snapshot==read('VALIDATION_R1.json')['candidate_snapshot']
    sets=[('all-time-sixteen',dict(quantity='thermal_response_characteristic_time',source=primary),16),('complete-source-thirtytwo',dict(source=primary),32)]
    sets += [(s['id'],dict(query=s['id']),2) for s in states]
    checks=[]
    for name,filters,count in sets:
        rows=list(db.records(**filters));assert len(rows)==count,(name,len(rows))
        expected=deepcopy({r['record_id']:r for r in rows})
        db.export(EXT/name,**filters);assert read_snapshot(EXT/name)[1]==expected
        for row in rows:
            p=row['property'];assert p==db.properties[row['record_id']]
            assert row['state']==db.states[p['material_state_id']]
            if p['quantity']=='thermal_response_characteristic_time':
                assert {s['id'] for s in row['sources']}=={primary,secondary}
                assert p['summary_statistic']=='not_stated' and p['sample_count']['value'] is None and p['uncertainty_status']=='reported_plus_minus_unspecified'
        rows[0]['property']['reported_value']['number']='999';rows[0]['sources'][0]['claim_notes'].append('detached')
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,complete_join_roundtrip=True,copy_isolation=True))
    assert not list(db.records(source=secondary))
    for s in states:
        view=resolve_material(s['id'],*(data[n] for n in ('materials','reference_properties','sources')))
        assert len(view['properties'])==2 and {x['id'] for x in view['sources']}=={primary,secondary}
        old=baseline.states[s['id'].removesuffix('_thermal_response_forced_convection')]
        assert s['identity_id']==old['identity_id'] and s['grade_id'] is None
        assert db.identities[s['identity_id']]['category']=='composite'
    assert all(sha(ROOT/'materials_boundaries/data'/n)==h for n,h in pins.items())
    with (HERE/'CANDIDATE_CONSUMERS_R1.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(candidate_snapshot=db.snapshot,checks=checks,all_twelve_new_records_complete=True,context_resolve_dual_sources=True,primary_only_source_filter_preserved=True,sets_overlap_not_independent_samples=True,native_hashes_unchanged=pins,native_applied=False,installation='not_run'),f,ensure_ascii=False,indent=2);f.write('\n')
    print('Eight overlapping candidate query/export/restore sets passed;12new facts,6existing composite identities,dual sources and unknown statistics preserved;native unchanged')
if __name__=='__main__':main()
