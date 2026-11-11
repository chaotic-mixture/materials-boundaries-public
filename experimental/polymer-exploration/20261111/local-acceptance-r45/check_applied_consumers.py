"""Check all new mechanical facts through complete quantity/source exports and state resolution."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r45'
MAPPING=HERE.parent/'nr-clay-mechanical-native-mapping-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import resolve_material
def read(n):return json.loads((MAPPING/n).read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert EXT.is_dir()
    db=Database();pins={n:sha(ROOT/'materials_boundaries/data'/n) for n in ('materials.json','reference_properties.json','sources.json')}
    data=db.data;states=read('NEW_STATES_R1.json');props=read('NEW_PROPERTIES_R1.json');proposal=read('SOURCE_UPDATE_R1.json');primary=proposal['before']['id']
    assert db.sources[primary]==proposal['after'] and db.snapshot==read('VALIDATION_R1.json')['candidate_snapshot']
    quantities=['tensile_modulus','tensile_stress_at_specified_elongation','tensile_stress_at_break','volumetric_tensile_work_to_break','shore_a_hardness']
    sets=[(q,dict(quantity=q,source=primary),14 if q=='tensile_stress_at_specified_elongation' else 7) for q in quantities]+[('complete-source-eightysix',dict(source=primary),86)]
    checks=[];newids={p['id'] for p in props};seen=set()
    for name,filters,count in sets:
        rows=list(db.records(**filters));assert len(rows)==count,(name,len(rows));expected=deepcopy({r['record_id']:r for r in rows})
        db.export(EXT/('accepted-'+name),**filters);assert read_snapshot(EXT/('accepted-'+name))[1]==expected
        candidate=ROOT.parent/'open-database-evidence/polymer-nr-clay-mechanical-mapping-20261111-r1'/name
        assert read_snapshot(candidate)[1]==expected
        for row in rows:
            p=row['property'];assert p==db.properties[row['record_id']] and row['state']==db.states[p['material_state_id']]
            if p['id'] not in newids:continue
            seen.add(p['id']);assert {s['id'] for s in row['sources']}=={primary} and row['identity']['category']=='composite'
            assert p['summary_statistic']=='reported_mean' and p['sample_count']['value']==5 and p['sample_count']['relation']=='exact' and p['uncertainty_status']=='reported_standard_deviation'
            if p['quantity']=='shore_a_hardness':
                assert p['reported_value']['unit_code']=='shore_a_scale' and p['uncertainty']['unit_code']=='shore_a_scale'
                assert p['conditions']['temperature']['text'].startswith('25') and row['state']['state']['processing']['text'] is None and row['state']['state']['temper_or_heat_treatment']['text'] is None
            else:assert p['conditions']['temperature']['text'] is None
            if p['quantity']=='tensile_stress_at_specified_elongation':assert p['specified_elongation']['number'] in ('200','400')
            if p['quantity']=='volumetric_tensile_work_to_break':assert p['work_reference_basis']['text'] is None and p['source_discrepancies']
        rows[0]['property']['reported_value']['number']='999';rows[0]['sources'][0]['claim_notes'].append('detached')
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,complete_join_roundtrip=True,copy_isolation=True))
    assert seen==newids
    for s in states:
        view=resolve_material(s['id'],*(data[n] for n in ('materials','reference_properties','sources')))
        hard=s['id'].endswith('_shore_a_nominal_3mm');assert len(view['properties'])==(1 if hard else 5)
        assert {x['id'] for x in view['sources']}=={primary}
        old=db.states[s['id'].removesuffix('_shore_a_nominal_3mm' if hard else '_quasi_static_tensile')]
        assert s['identity_id']==old['identity_id'] and s['grade_id'] is None
    assert not any(p['quantity']=='elongation_at_break' for p in props)
    assert all(sha(ROOT/'materials_boundaries/data'/n)==h for n,h in pins.items())
    with (HERE/'APPLIED_CONSUMERS_R45.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(candidate_snapshot=db.snapshot,checks=checks,all_thirtysix_new_records_complete=True,all_twelve_contexts_resolve=True,sets_overlap_not_independent_samples=True,native_hashes_unchanged=pins,native_applied=True,installation='not_run'),f,ensure_ascii=False,indent=2);f.write('\n')
    print('Six complete mechanical/source export groups and12state resolutions passed;36facts retain method-specific statistics,unknowns and held elongation;actual native equals frozen candidate')
if __name__=='__main__':main()
