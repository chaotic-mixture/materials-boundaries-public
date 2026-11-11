"""Complete joins/export recovery and unknown preservation for eighteen unapplied LFA cells."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r44'
MAPPING=HERE.parent/'nr-clay-lfa-native-mapping-r1'
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
    sets=[(q,dict(quantity=q,source=primary),7) for q in ('mass_specific_heat_capacity','thermal_diffusivity','thermal_conductivity')]+[('complete-source-fifty',dict(source=primary),50)]
    sets += [(s['id'],dict(query=s['id']),3) for s in states];checks=[]
    for name,filters,count in sets:
        rows=list(db.records(**filters));assert len(rows)==count,(name,len(rows));expected=deepcopy({r['record_id']:r for r in rows})
        db.export(EXT/('accepted-'+name),**filters);assert read_snapshot(EXT/('accepted-'+name))[1]==expected
        candidate=ROOT.parent/'open-database-evidence/polymer-nr-clay-lfa-mapping-20261111-r1'/name
        assert read_snapshot(candidate)[1]==expected
        for row in rows:
            p=row['property'];assert p==db.properties[row['record_id']] and row['state']==db.states[p['material_state_id']]
            if p['quantity'] in ('mass_specific_heat_capacity','thermal_diffusivity','thermal_conductivity'):
                assert {s['id'] for s in row['sources']}=={primary}
                assert p['summary_statistic']=='not_stated' and p['sample_count']['value'] is None and p['uncertainty_status']=='reported_plus_minus_unspecified'
                if p['quantity']=='thermal_conductivity':
                    assert p['evidence_kind']=='published_measurement_derived_reference'
                    assert p['derivation']['software_calculation_performed'] is False and p['derivation']['software_uncertainty_propagation_performed'] is False
                    assert all(v is None for k,v in p['derivation']['input_provenance'].items() if k!='unknown_scope_note')
                else:assert p['evidence_kind']=='published_experimental_reference'
        rows[0]['property']['reported_value']['number']='999';rows[0]['sources'][0]['claim_notes'].append('detached')
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,complete_join_roundtrip=True,copy_isolation=True))
    for s in states:
        view=resolve_material(s['id'],*(data[n] for n in ('materials','reference_properties','sources')))
        assert len(view['properties'])==3 and {x['id'] for x in view['sources']}=={primary}
        old=db.states[s['id'].removesuffix('_lfa')];assert s['identity_id']==old['identity_id'] and s['grade_id'] is None
        assert db.identities[s['identity_id']]['category']=='composite'
    assert all(sha(ROOT/'materials_boundaries/data'/n)==h for n,h in pins.items())
    with (HERE/'APPLIED_CONSUMERS_R44.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(candidate_snapshot=db.snapshot,checks=checks,all_eighteen_new_records_complete=True,context_resolve_complete=True,sets_overlap_not_independent_samples=True,native_hashes_unchanged=pins,native_applied=True,installation='not_run'),f,ensure_ascii=False,indent=2);f.write('\n')
    print('Ten overlapping candidate thermal/source/context query-export-restore sets passed;18new cells preserve classification,unknown statistics and unpaired-input boundaries;actual native equals frozen candidate')
if __name__=='__main__':main()
