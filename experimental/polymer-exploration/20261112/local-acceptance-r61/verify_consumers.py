"""Compare complete accepted closed-cell consumers with reviewed mapping exports."""
from pathlib import Path
from copy import deepcopy
import json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def main():
    ext=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r61'
    candidate=ROOT.parent/'open-database-evidence/polymer-pur-closed-cell-mapping-20261112-r1'
    db=Database();source='ivdre_2024_lpo_rigid_pur';results=[]
    for name,filters,count in [('closed-four',dict(quantity='closed_cell_content_volume_percentage'),4),('source-fortyeight',dict(source=source),48),('water-four',dict(source=source,quantity='water_absorption_volume_percentage'),4)]:
        rows=list(db.records(**filters));assert len(rows)==count
        expected=deepcopy({r['record_id']:r for r in rows});assert read_snapshot(candidate/name)[1]==expected
        db.export(ext/('accepted-'+name),**filters);assert read_snapshot(ext/('accepted-'+name))[1]==expected
        rows[0]['property']['reported_value']['number']='999';assert {r['record_id']:r for r in db.records(**filters)}==expected
        results.append(dict(name=name,records=count,candidate_native_equal=True,copy_isolation=True))
    with (HERE/'CONSUMERS_R61.json').open('x',encoding='utf-8') as f:json.dump(results,f,indent=2);f.write('\n')
    print(json.dumps(results))
if __name__=='__main__':main()
