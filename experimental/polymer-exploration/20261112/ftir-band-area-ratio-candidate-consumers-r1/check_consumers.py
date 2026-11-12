"""Complete candidate source-normalization records without reconstructing inputs."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries._ftir_band_area_ratio_contract import QUANTITY
def main():
    mapping=HERE.parent/'ftir-band-area-ratio-native-mapping-r1';out=ROOT.parent/'open-database-evidence/polymer-ftir-band-area-ratio-candidate-consumers-20261112-r1';out.mkdir(exist_ok=False)
    before=Database();data=deepcopy(before.data)
    for n,name in [('materials','NEW_STATES_R1.json'),('reference_properties','NEW_PROPERTIES_R1.json')]:data[n]['records'].extend(json.loads((mapping/name).read_bytes()))
    db=Database(data);checks=[]
    for label,filters,count in [('ftir-one',dict(quantity=QUANTITY),1),('phbv-identity-all',dict(query='mat_abbasi2022_manure_phbv39'),12),('phbv-source-all',dict(source='abbasi_2022_manure_phbv'),12)]:
        rows=list(db.records(**filters));expected=deepcopy({x['record_id']:x for x in rows});assert len(rows)==count
        db.export(out/label,**filters);assert read_snapshot(out/label)[1]==expected
        for x in rows:assert x['property']==db.properties[x['record_id']] and x['state']==db.states[x['property']['material_state_id']]
        rows[0]['property']['scope_note']='detached consumer probe';assert {x['record_id']:x for x in db.records(**filters)}==expected
        checks.append(dict(group=label,records=count,full_query_native_export_restore_equal=True,detached_copy=True))
    rows=list(db.records(quantity=QUANTITY));assert len(rows)==1
    p=rows[0]['property'];assert p['reported_value']['number']=='2.35'
    assert p['evidence_kind']=='published_measurement_derived_reference' and p['determination_basis']=='source_reports_calculation'
    assert p['sample_count']['value'] is None and p['uncertainty'] is None
    assert p['derivation']['numerator_band']['number']=='1720' and p['derivation']['denominator_band']['number']=='1740'
    receipt=dict(snapshot=db.snapshot,groups=checks,categories=dict(polymer=1),external_files_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},native_applied=False,installation='not_run',scope='Complete candidate consumers only;not software source calculation,testsuite or scientific approval')
    with (HERE/'CONSUMERS_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(checks))
if __name__=='__main__':main()
