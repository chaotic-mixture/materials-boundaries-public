"""Compare actual local native objects to exact pre-r42 published-baseline bytes."""
from pathlib import Path
from collections import Counter
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
BASE=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r42/baseline-tables'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='847be1bb03e37e330e8de18341dbfca6715bd8b0'
    initial=read(HERE.parent/'local-acceptance-r42/APPLICATION_INTENT_R42.json')['before_sha256']
    assert all(sha(BASE/Path(n).name)==h for n,h in initial.items())
    old={n:read(BASE/(n+'.json')) for n in ('materials','reference_properties','sources')}
    current={n:read(ROOT/'materials_boundaries/data'/(n+'.json')) for n in old}
    def index(rows):return {r['id']:r for r in rows}
    a=index(old['reference_properties']['records']);b=index(current['reference_properties']['records'])
    x=index(old['materials']['records']);y=index(current['materials']['records'])
    assert len(a)==5416 and len(b)==5486 and len(x)==5263 and len(y)==5289
    assert all(b[k]==v for k,v in a.items()) and all(y[k]==v for k,v in x.items())
    assert old['materials']['identities']==current['materials']['identities'] and old['materials']['grades']==current['materials']['grades']
    identities=index(current['materials']['identities']);newp=[b[n] for n in sorted(b.keys()-a.keys())];news=[y[n] for n in sorted(y.keys()-x.keys())]
    primary='bianchi_2025_nr_nanoclay';s0=index(old['sources']['records']);s1=index(current['sources']['records'])
    assert set(s1)-set(s0)=={'bianchi_2024_nr_crosslink_methods'} and set(s0)<=set(s1)
    assert all(s1[k]==v for k,v in s0.items() if k!=primary)
    unchanged0={k:v for k,v in s0[primary].items() if k!='claim_notes'};unchanged1={k:v for k,v in s1[primary].items() if k!='claim_notes'}
    assert unchanged0==unchanged1 and s1[primary]['claim_notes'][:len(s0[primary]['claim_notes'])]==s0[primary]['claim_notes']
    quantities=Counter(p['quantity'] for p in newp);categories=Counter(identities[y[p['material_state_id']]['identity_id']]['category'] for p in newp);kinds=Counter(p['evidence_kind'] for p in newp)
    assert quantities==dict(thermal_response_characteristic_time=16,mass_specific_heat_capacity=6,thermal_diffusivity=6,thermal_conductivity=6,tensile_modulus=6,tensile_stress_at_specified_elongation=12,tensile_stress_at_break=6,volumetric_tensile_work_to_break=6,shore_a_hardness=6)
    assert categories==dict(polymer=4,composite=66) and kinds==dict(published_experimental_reference=48,published_measurement_derived_reference=22)
    assert sum(p['sample_count']['value']==5 for p in newp)==36 and sum(p['sample_count']['value'] is None for p in newp)==34
    assert all(p['quantity']!='elongation_at_break' for p in newp)
    manifest=read(HERE.parent/'local-acceptance-r45/APPLICATION_R45.json');assert all(sha(ROOT/n)==h for n,h in manifest['after_sha256'].items())
    result=dict(scope='Actual cumulative native object delta;not unified tests,installation,independent review,commit,push or CI',published_baseline_commit='847be1bb03e37e330e8de18341dbfca6715bd8b0',baseline_sha256=initial,current_sha256=manifest['after_sha256'],current_snapshot=manifest['snapshot'],properties=5486,states=5289,sources=134,new_properties=len(newp),new_context_states=len(news),new_identities=0,new_grades=0,new_method_sources=1,old5416properties_unchanged=True,old5263states_unchanged=True,old_primary_source_fields_except_appended_notes_unchanged=True,other_old_sources_unchanged=True,new_properties_by_quantity=dict(quantities),new_properties_by_category=dict(categories),new_properties_by_evidence_kind=dict(kinds),new_property_ids=[p['id'] for p in newp],new_state_ids=[s['id'] for s in news],method_specific_n5_records=36,unknown_per_cell_n_records=34,counts_not_independent_samples=True,r45_final_review='pending',unified_acceptance='not_run',pushed=False)
    with (HERE/'CUMULATIVE_NATIVE_DELTA_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Actual cumulative delta70properties/26contexts/1method source/0identities;48experimental+22derived,4polymer+66composite;all5416old properties/5263states unchanged;not unified acceptance')
if __name__=='__main__':main()
