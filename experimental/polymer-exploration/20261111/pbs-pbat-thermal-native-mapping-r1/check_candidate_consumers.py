"""Complete source joins and export recovery for eight unapplied thermal facts."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-pbs-pbat-thermal-mapping-20261111-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import resolve_material
def read(n):return json.loads((HERE/n).read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not EXT.exists();EXT.mkdir()
    baseline=Database();pins={n:sha(ROOT/'materials_boundaries/data'/n) for n in ('materials.json','reference_properties.json','sources.json')}
    data=deepcopy(baseline.data);states=read('NEW_STATES_R1.json');props=read('NEW_PROPERTIES_R1.json');proposal=read('SOURCE_UPDATE_R1.json');primary=proposal['before']['id']
    assert baseline.sources[primary]==proposal['before']
    data['materials']['records'].extend(states);data['reference_properties']['records'].extend(props);data['sources']['records']=[proposal['after'] if s['id']==primary else s for s in data['sources']['records']]
    db=Database(data);assert db.snapshot==read('VALIDATION_R1.json')['candidate_snapshot']
    sets=[('new-DTG-four',dict(quantity='thermal_degradation_rate_peak_temperature',source=primary),4),('new-Tm-four',dict(quantity='melting_peak_temperature',source=primary),4),('complete-source-seventeen',dict(source=primary),17),('polymer-eight',dict(source=primary,category='polymer'),8),('composite-nine',dict(source=primary,category='composite'),9)]
    checks=[];newids={p['id'] for p in props};seen=set()
    for name,filters,count in sets:
        rows=list(db.records(**filters));assert len(rows)==count,(name,len(rows));expected=deepcopy({r['record_id']:r for r in rows})
        db.export(EXT/name,**filters);assert read_snapshot(EXT/name)[1]==expected
        for row in rows:
            p=row['property'];assert p==db.properties[row['record_id']] and row['state']==db.states[p['material_state_id']]
            if p['id'] not in newids:continue
            seen.add(p['id']);assert {s['id'] for s in row['sources']}=={primary}
            assert p['summary_statistic']=='not_stated' and p['sample_count']['value'] is None and p['uncertainty'] is None
            assert p['uncertainty_status']=='not_reported_in_inspected_source' and p['reported_value']['unit_code']=='degC'
            assert p['conditions']['temperature']['text'] is None and p['conditions']['conditioning']['text'] is None
            additional={a['name']:a['fact'] for a in p['conditions']['additional_conditions']}
            if p['quantity']=='thermal_degradation_rate_peak_temperature':
                assert p['degradation_peak_ordinal']['value'] is None and p['degradation_peak_ordinal']['status']=='not_reported_in_inspected_source'
                assert additional['gas_flow']['text'] is None
            else:
                assert 'degradation_peak_ordinal' not in p and additional['selected_scan']['text']=='Second heating'
                assert additional['gas_flow']['text']=='25mL/min' and additional['cooling_rate']['text'] is None
        rows[0]['property']['reported_value']['number']='999';rows[0]['sources'][0]['claim_notes'].append('detached mutation')
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,complete_join_roundtrip=True,copy_isolation=True))
    assert seen==newids
    for s in states:
        view=resolve_material(s['id'],*(data[n] for n in ('materials','reference_properties','sources')))
        assert len(view['properties'])==1 and {r['id'] for r in view['sources']}=={primary}
        assert s['identity_id'] in baseline.identities and s['grade_id'] is None
    assert all(sha(ROOT/'materials_boundaries/data'/n)==h for n,h in pins.items())
    with (HERE/'CANDIDATE_CONSUMERS_R1.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(candidate_snapshot=db.snapshot,checks=checks,all_eight_new_records_complete=True,all_eight_contexts_resolve=True,sets_overlap_not_independent_samples=True,native_hashes_unchanged=pins,native_applied=False,installation='not_run'),f,ensure_ascii=False,indent=2);f.write('\n')
    print('Five complete thermal/source/category export groups and8state resolutions passed;unknown ordinals/statistics/conditions retained;native unchanged')
if __name__=='__main__':main()
