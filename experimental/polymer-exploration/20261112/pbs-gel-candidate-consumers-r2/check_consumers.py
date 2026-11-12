"""Check detached candidate objects and exact complete exported records."""
from pathlib import Path
from copy import deepcopy
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def main():
    mapping=HERE.parent/'pbs-gel-fraction-native-mapping-r3'
    out=ROOT.parent/'open-database-evidence/polymer-pbs-gel-candidate-consumers-20261112-r2';out.mkdir(exist_ok=False)
    before=Database();data=deepcopy(before.data)
    for n,name in [('materials','NEW_STATES_R1.json'),('reference_properties','NEW_PROPERTIES_R1.json')]:data[n]['records'].extend(json.loads((mapping/name).read_bytes()))
    db=Database(data);checks=[];source='ewurum_mcdonald_2025_pbs_lignin'
    for label,filters,count in [('gel-four',dict(source=source,quantity='solvent_extraction_gel_fraction_percentage'),4),('source-all',dict(source=source),122),('density-ten',dict(source=source,quantity='mass_density'),10)]:
        rows=list(db.records(**filters));expected=deepcopy({x['record_id']:x for x in rows});assert len(rows)==count
        db.export(out/label,**filters);assert read_snapshot(out/label)[1]==expected
        for x in rows:assert x['property']==db.properties[x['record_id']] and x['state']==db.states[x['property']['material_state_id']]
        rows[0]['property']['scope_note']='detached copy probe';assert {x['record_id']:x for x in db.records(**filters)}==expected
        checks.append(dict(group=label,records=count,full_query_native_export_recovery_equal=True,detached_copy=True))
    receipt=dict(snapshot=db.snapshot,checks=checks,external_files_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},native_applied=False,installation='not_run',scope='Candidate consumers only;not test-suite count,independent review or native acceptance',fix='Deepcopy expected objects before mutation;failed earlier shallow-alias probe preserved')
    with (HERE/'CONSUMERS_R2.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(checks))
if __name__=='__main__':main()
