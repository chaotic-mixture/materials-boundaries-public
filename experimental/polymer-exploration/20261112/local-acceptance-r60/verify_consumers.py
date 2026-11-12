"""Recover complete joined PLA/PCL objects after the reviewed revisions."""
from pathlib import Path
from copy import deepcopy
import json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def main():
    ext=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r60'
    candidate=ROOT.parent/'open-database-evidence/polymer-pla-pcl-evidence-revisions-20261112-r1/source-twentyfive'
    expected_all=read_snapshot(candidate)[1];db=Database();source='delgado_aguilar_2020_pla_pcl';results=[]
    groups=[('source-twentyfive',dict(source=source),25),('young-seven',dict(source=source,quantity='youngs_modulus'),7),('strength-seven',dict(source=source,quantity='tensile_strength'),7),('break-four',dict(source=source,quantity='tensile_elongation_at_break'),4),('strength-elongation-seven',dict(source=source,quantity='tensile_elongation_at_strength'),7)]
    for name,filters,count in groups:
        rows=list(db.records(**filters));assert len(rows)==count
        expected=deepcopy({r['record_id']:r for r in rows});assert all(expected_all[k]==v for k,v in expected.items())
        db.export(ext/('accepted-'+name),**filters);assert read_snapshot(ext/('accepted-'+name))[1]==expected
        rows[0]['property']['reported_value']['number']='999'
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        results.append(dict(name=name,records=count,candidate_native_equal=True,copy_isolation=True))
    with (HERE/'CONSUMERS_R60.json').open('x',encoding='utf-8') as f:json.dump(results,f,indent=2);f.write('\n')
    print(json.dumps(results))
if __name__=='__main__':main()
