"""Full object recovery for the candidate without modifying native tables."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r48'
MAPPING=HERE.parent/'pbs-pbat-hybrid-mechanical-mapping-r2'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import resolve_material
def read(n):return json.loads((MAPPING/n).read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert EXT.is_dir();base=Database();data=base.data
    pins={n:sha(ROOT/'materials_boundaries/data'/n) for n in ('materials.json','reference_properties.json','sources.json')}
    props=read('NEW_PROPERTIES_R1.json');updates=read('STATE_UPDATES_R1.json')
    assert all(base.states[s['after']['id']]==s['after'] for s in updates)
    db=base;assert db.snapshot==read('VALIDATION_R1.json')['candidate_snapshot']
    sid='mtibe_2022_pbs_pbat_lignin_zno';checks=[];ids={p['id'] for p in props};seen=set()
    for name,filters,count in [('yield-five',dict(source=sid,quantity='tensile_yield_strength'),5),('elongation-five',dict(source=sid,quantity='tensile_elongation_at_break'),5),('source-twentyseven',dict(source=sid),27),('composite-eighteen',dict(source=sid,category='composite'),18)]:
        rows=list(db.records(**filters));assert len(rows)==count
        expected=deepcopy({r['record_id']:r for r in rows});db.export(EXT/('accepted-'+name),**filters);assert read_snapshot(EXT/('accepted-'+name))[1]==expected
        assert read_snapshot(ROOT.parent/'open-database-evidence/polymer-pbs-pbat-hybrid-mechanical-mapping-20261111-r2'/name)[1]==expected
        for r in rows:
            p=r['property'];assert p==db.properties[r['record_id']] and r['state']==db.states[p['material_state_id']]
            if p['id'] not in ids:continue
            seen.add(p['id']);assert {s['id'] for s in r['sources']}=={sid}
            assert p['sample_count']['value']==5 and p['sample_count']['relation']=='exact'
            assert p['summary_statistic']=='reported_value' and p['uncertainty_status']=='reported_plus_minus_unspecified'
            assert p['conditions']['temperature']['text']=='25 °C' and p['conditions']['loading_rate']['text'] is None
            assert '48 h' in p['conditions']['conditioning']['text'] and 'Relative humidity' in p['conditions']['conditioning']['notes']
            assert r['identity']['category']=='composite'
            if p['quantity']=='tensile_yield_strength':assert p['source_discrepancies']
            else:assert p['reported_value']['unit_code']==p['uncertainty']['unit_code']=='percent_elongation'
        rows[0]['property']['reported_value']['number']='999';rows[0]['sources'][0]['claim_notes'].append('copy test')
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,full_join_recovery=True,copy_isolation=True))
    assert seen==ids
    for s in updates:
        view=resolve_material(s['after']['id'],*(data[n] for n in ('materials','reference_properties','sources')))
        assert len(view['properties'])==3 and all(p in db.properties for p in s['after']['property_ids'])
    assert all(sha(ROOT/'materials_boundaries/data'/n)==h for n,h in pins.items())
    out=dict(snapshot=db.snapshot,checks=checks,six_new_records_complete=True,three_existing_states_resolve=True,sets_overlap_not_independent_samples=True,native_unchanged=pins,native_applied=True,installation='not_run')
    with (HERE/'APPLIED_CONSUMERS_R48.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Four5/5/27/18 full-object export/recovery/copy groups and3existing-state joins passed;native equals frozen candidate')
if __name__=='__main__':main()
