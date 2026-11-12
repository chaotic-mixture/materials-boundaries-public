"""Complete candidate source-normalization records without reconstructing inputs."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries._dsc_crystallinity_contract import QUANTITY
def main():
    mapping=HERE.parent/'dsc-crystallinity-native-mapping-r1';out=ROOT.parent/'open-database-evidence/polymer-dsc-crystallinity-candidate-consumers-20261112-r1';out.mkdir(exist_ok=False)
    before=Database();data=deepcopy(before.data)
    for n,name in [('materials','NEW_STATES_R1.json'),('reference_properties','NEW_PROPERTIES_R1.json')]:data[n]['records'].extend(json.loads((mapping/name).read_bytes()))
    db=Database(data);checks=[]
    for label,filters,count in [('crystallinity-ten',dict(quantity=QUANTITY),10),('pbs-source-all',dict(source='ewurum_mcdonald_2025_pbs_lignin'),167),('phbv-source-all',dict(source='abbasi_2022_manure_phbv'),11)]:
        rows=list(db.records(**filters));expected=deepcopy({x['record_id']:x for x in rows});assert len(rows)==count
        db.export(out/label,**filters);assert read_snapshot(out/label)[1]==expected
        for x in rows:assert x['property']==db.properties[x['record_id']] and x['state']==db.states[x['property']['material_state_id']]
        rows[0]['property']['scope_note']='detached consumer probe';assert {x['record_id']:x for x in db.records(**filters)}==expected
        checks.append(dict(group=label,records=count,full_query_native_export_restore_equal=True,detached_copy=True))
    rows=list(db.records(quantity=QUANTITY));assert sum(x['identity']['category']=='polymer' for x in rows)==2
    assert sum(x['identity']['category']=='composite' for x in rows)==8
    for x in rows:
        p=x['property'];assert p['evidence_kind']=='published_measurement_derived_reference' and p['determination_basis']=='source_reports_calculation' and p['derivation']['executor']=='source_reported_only'
        assert p['sample_count']['value'] is None and p['uncertainty'] is None
        if p['source_id']=='abbasi_2022_manure_phbv':assert p['derivation']['cycle_assignment']['status']=='conflicting_source_statements' and len(p['derivation']['cycle_assignment']['claims'])==2
    receipt=dict(snapshot=db.snapshot,groups=checks,categories=dict(polymer=2,composite=8),external_files_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},native_applied=False,installation='not_run',scope='Complete candidate consumers only;not software source calculation,testsuite or scientific approval')
    with (HERE/'CONSUMERS_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(checks))
if __name__=='__main__':main()
