"""Verify applied candidates and complete native joined exports before installation."""
from pathlib import Path
from copy import deepcopy
import json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def main():
    read=lambda p:json.loads(p.read_bytes())
    app=read(HERE/'APPLICATION_R67.json');db=Database();assert db.snapshot==app['snapshot']
    mapping=HERE.parent/'pbs-gel-fraction-native-mapping-r3'
    for p in read(mapping/'NEW_PROPERTIES_R1.json'):assert db.properties[p['id']]==p
    for s in read(mapping/'NEW_STATES_R1.json'):assert db.states[s['id']]==s
    ext=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261112-r67'
    groups=[('gel-four',{'quantity':'solvent_extraction_gel_fraction_percentage','source':'ewurum_mcdonald_2025_pbs_lignin'},4),('source-all',{'source':'ewurum_mcdonald_2025_pbs_lignin'},122),('density-ten',{'source':'ewurum_mcdonald_2025_pbs_lignin','quantity':'mass_density'},10)]
    checks=[]
    for name,filters,count in groups:
        rows=list(db.records(**filters));assert len(rows)==count
        expected=deepcopy({r['record_id']:r for r in rows})
        db.export(ext/('accepted-'+name),**filters)
        assert read_snapshot(ext/('accepted-'+name))[1]==expected
        rows[0]['property']['reported_value']['number']='999'
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,full_joined_export_exact=True,copy_isolation=True))
    with (HERE/'CONSUMERS_R67.json').open('x',encoding='utf-8') as f:json.dump(dict(snapshot=db.snapshot,exports=checks),f,indent=2)
    print(json.dumps(checks))
if __name__=='__main__':main()
