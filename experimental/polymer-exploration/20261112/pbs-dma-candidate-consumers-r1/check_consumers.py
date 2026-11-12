"""Complete candidate source-qualified DMA exports and detached-object checks."""
from pathlib import Path
from copy import deepcopy
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def main():
    mapping=HERE.parent/'pbs-dma-native-mapping-r1';out=ROOT.parent/'open-database-evidence/polymer-pbs-dma-candidate-consumers-20261112-r1';out.mkdir(exist_ok=False)
    before=Database();data=deepcopy(before.data)
    for n,name in [('materials','NEW_STATES_R1.json'),('reference_properties','NEW_PROPERTIES_R1.json')]:data[n]['records'].extend(json.loads((mapping/name).read_bytes()))
    db=Database(data);source='ewurum_mcdonald_2025_pbs_lignin';checks=[]
    for label,filters,count in [('storage-eighteen',dict(source=source,quantity='dma_flexural_storage_modulus'),18),('tan-delta-eighteen',dict(source=source,quantity='dma_flexural_loss_tangent'),18),('source-all',dict(source=source),158)]:
        rows=list(db.records(**filters));expected=deepcopy({x['record_id']:x for x in rows});assert len(rows)==count
        db.export(out/label,**filters);assert read_snapshot(out/label)[1]==expected
        for x in rows:assert x['property']==db.properties[x['record_id']] and x['state']==db.states[x['property']['material_state_id']]
        rows[0]['property']['scope_note']='detached copy probe';assert {x['record_id']:x for x in db.records(**filters)}==expected
        checks.append(dict(group=label,records=count,full_query_native_export_recovery_equal=True,detached_copy=True))
    selected=[x for x in db.records(source=source) if x['property']['quantity'].startswith('dma_flexural_')]
    assert len(selected)==36 and len({x['state']['id'] for x in selected})==9
    assert sum(x['identity']['category']=='polymer' for x in selected)==4 and sum(x['identity']['category']=='composite' for x in selected)==32
    assert all(x['property']['sample_count']['value'] is None and x['property']['uncertainty'] is None for x in selected)
    receipt=dict(snapshot=db.snapshot,checks=checks,new_property_categories=dict(polymer=4,composite=32),new_contexts=9,external_files_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},native_applied=False,installation='not_run',scope='Candidate complete consumers only;not test-suite count or scientific validity')
    with (HERE/'CONSUMERS_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(checks))
if __name__=='__main__':main()
