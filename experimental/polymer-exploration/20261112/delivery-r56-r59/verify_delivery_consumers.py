"""Check current graph, exact joined delivery consumers and CLI export integrity."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-consolidated-delivery-20261112-r56-r59'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def main():
    db=Database();graph=db.validate_scientific_contracts();results=[]
    for name,filters,count in json.loads((HERE/'CONSUMER_GROUPS_R1.json').read_bytes()):
        rows=list(db.records(**filters));assert len(rows)==count
        expected=deepcopy({r['record_id']:r for r in rows});db.export(EXT/('accepted-'+name),**filters)
        assert read_snapshot(EXT/('accepted-'+name))[1]==expected
        rows[0]['property']['reported_value']['number']='999'
        assert {r['record_id']:r for r in db.records(**filters)}==expected
        results.append(dict(name=name,records=count,complete_recovery=True,copy_isolation=True))
    env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1');receipts=[]
    for args in [['export','--query','C11000','--quantity','mass_density','--output',str(EXT/'database-example')],['verify','--snapshot',str(EXT/'database-example')]]:
        p=subprocess.run([sys.executable,'-X','utf8','-B','-m','materials_boundaries.database',*args],cwd=ROOT,env=env,capture_output=True)
        (EXT/(args[0]+'-delivery.log')).write_bytes(p.stdout+p.stderr);p.check_returncode();receipts.append(dict(command=args,exit_code=p.returncode,result=json.loads(p.stdout)))
    assert receipts[-1]['result']['status']=='snapshot_integrity_passed'
    with (HERE/'GRAPH_EXPORT_VALIDATION_R1.json').open('x',encoding='utf-8') as f:json.dump(dict(graph=graph,exports=results,cli_commands=receipts),f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(graph='passed',joined_consumer_groups=len(results),cli_export_verify='passed')))
if __name__=='__main__':main()
