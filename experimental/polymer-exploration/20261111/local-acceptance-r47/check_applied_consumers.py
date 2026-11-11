"""Complete source joins and export recovery for four unapplied cooling crystallization facts."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r47'
MAPPING=HERE.parent/'pbs-pbat-crystallization-native-mapping-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import resolve_material
def read(n):return json.loads((MAPPING/n).read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert EXT.is_dir()
    baseline=Database();pins={n:sha(ROOT/'materials_boundaries/data'/n) for n in ('materials.json','reference_properties.json','sources.json')}
    data=baseline.data;states=read('NEW_STATES_R1.json');props=read('NEW_PROPERTIES_R1.json');proposal=read('SOURCE_UPDATE_R1.json');primary=proposal['before']['id']
    db=baseline;assert db.sources[primary]==proposal['after'] and db.snapshot==read('VALIDATION_R1.json')['candidate_snapshot']
    sets=[('new-Tcc-four',dict(quantity='crystallization_peak_temperature',source=primary),4),('complete-source-twentyone',dict(source=primary),21),('polymer-nine',dict(source=primary,category='polymer'),9),('composite-twelve',dict(source=primary,category='composite'),12)]
    checks=[];newids={p['id'] for p in props};seen=set()
    for name,filters,count in sets:
        rows=list(db.records(**filters));assert len(rows)==count,(name,len(rows));expected=deepcopy({r['record_id']:r for r in rows})
        db.export(EXT/('accepted-'+name),**filters);assert read_snapshot(EXT/('accepted-'+name))[1]==expected
        assert read_snapshot(ROOT.parent/'open-database-evidence/polymer-pbs-pbat-crystallization-mapping-20261111-r1'/name)[1]==expected
        for row in rows:
            p=row['property'];assert p==db.properties[row['record_id']] and row['state']==db.states[p['material_state_id']]
            if p['id'] not in newids:continue
            seen.add(p['id']);assert {s['id'] for s in row['sources']}=={primary}
            assert p['summary_statistic']=='not_stated' and p['sample_count']['value'] is None and p['uncertainty'] is None
            assert p['uncertainty_status']=='not_reported_in_inspected_source' and p['reported_value']['unit_code']=='degC'
            assert p['conditions']['temperature']['text'] is None and p['conditions']['conditioning']['text'] is None
            additional={a['name']:a['fact'] for a in p['conditions']['additional_conditions']}
            assert p['quantity']=='crystallization_peak_temperature' and p['source_property_label']=='Tcc'
            assert p['thermal_scan_phase']['code']=='cooling' and p['thermal_phase_occurrence_ordinal']['value'] is None
            assert p['thermal_scan_definition']['kind']=='nonisothermal_temperature_scan'
            assert 'degradation_peak_ordinal' not in p
            assert additional['gas_flow']['text']=='25mL/min' and additional['cooling_rate']['text'] is None
            assert any('cold' in d['description'] for d in p['source_discrepancies'])
        rows[0]['property']['reported_value']['number']='999';rows[0]['sources'][0]['claim_notes'].append('detached mutation')
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,complete_join_roundtrip=True,copy_isolation=True))
    assert seen==newids
    for s in states:
        view=resolve_material(s['id'],*(data[n] for n in ('materials','reference_properties','sources')))
        assert len(view['properties'])==1 and {r['id'] for r in view['sources']}=={primary}
        assert s['identity_id'] in baseline.identities and s['grade_id'] is None
    assert all(sha(ROOT/'materials_boundaries/data'/n)==h for n,h in pins.items())
    with (HERE/'APPLIED_CONSUMERS_R47.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(candidate_snapshot=db.snapshot,checks=checks,all_four_new_records_complete=True,all_four_contexts_resolve=True,sets_overlap_not_independent_samples=True,native_hashes_unchanged=pins,native_applied=True,installation='not_run'),f,ensure_ascii=False,indent=2);f.write('\n')
    print('Four complete cooling/source/category export groups and4state resolutions passed;unknown ordinals/statistics/conditions retained;native equals frozen candidate')
if __name__=='__main__':main()
