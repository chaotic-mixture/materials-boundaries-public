"""Complete lignin TGA candidate records, including uncertainty and existing density."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def main():
    mapping=HERE.parent/'indulin-tga-native-mapping-r1';out=ROOT.parent/'open-database-evidence/polymer-indulin-tga-candidate-consumers-20261112-r1';out.mkdir(exist_ok=False)
    before=Database();data=deepcopy(before.data)
    for n,name in [('materials','NEW_STATES_R1.json'),('reference_properties','NEW_PROPERTIES_R1.json')]:data[n]['records'].extend(json.loads((mapping/name).read_bytes()))
    db=Database(data);checks=[]
    for label,filters,count in [('lignin-tga-three',dict(query='state_ewurum2025_indulin_at_tga'),3),('lignin-identity-four',dict(query='mat_ewurum2025_indulin_at'),4),('pbs-source-all',dict(source='ewurum_mcdonald_2025_pbs_lignin'),170)]:
        rows=list(db.records(**filters));expected=deepcopy({x['record_id']:x for x in rows});assert len(rows)==count,(label,len(rows),count)
        db.export(out/label,**filters);assert read_snapshot(out/label)[1]==expected
        for x in rows:assert x['property']==db.properties[x['record_id']] and x['state']==db.states[x['property']['material_state_id']]
        rows[0]['property']['scope_note']='detached consumer probe';assert {x['record_id']:x for x in db.records(**filters)}==expected
        checks.append(dict(group=label,records=count,full_query_native_export_restore_equal=True,detached_copy=True))
    rows=list(db.records(query='state_ewurum2025_indulin_at_tga'))
    for row in rows:
        p=row['property'];assert row['identity']['category']=='polymer' and p['sample_count']['value'] is None
        assert p['summary_statistic']=='reported_value' and p['uncertainty']['type']=='reported_plus_minus_unspecified'
        if p['quantity']=='thermal_degradation_rate_peak_temperature':assert p['degradation_peak_ordinal']['value'] is None
    receipt=dict(snapshot=db.snapshot,groups=checks,external_files_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},native_applied=False,installation='not_run',scope='Candidate consumer records only;not testsuite,independent specimens or scientific verification')
    with (HERE/'CONSUMERS_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(checks))
if __name__=='__main__':main()
