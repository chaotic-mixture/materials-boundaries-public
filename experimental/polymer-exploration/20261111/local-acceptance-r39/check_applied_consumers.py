"""Compare actual native complete records with independently approved candidate."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/'open-database-evidence/polymer-native-acceptance-20261111-r39'
CANDIDATE=ROOT.parent/'open-database-evidence/polymer-nr-work-mapping-20261111-r1'
sys.path.insert(0,str(ROOT))
from materials_boundaries.database import Database,read_snapshot
def main():
    receipt=json.loads((HERE/'APPLICATION_R39.json').read_bytes())
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in receipt['after_sha256'].items())
    db=Database();assert db.snapshot==receipt['snapshot'];checks=[]
    for name,filters,count in [('new-work',dict(quantity='volumetric_tensile_work_to_break',source='bianchi_2025_nr_nanoclay'),1),('existing-NR-seven',dict(query='mat_smr10_bianchi2025_nr',source='bianchi_2025_nr_nanoclay'),7),('complete-source-thirteen',dict(source='bianchi_2025_nr_nanoclay'),13)]:
        rows=list(db.records(**filters));assert len(rows)==count
        expected=deepcopy({row['record_id']:row for row in rows})
        assert read_snapshot(CANDIDATE/name)[1]==expected
        db.export(EXT/('accepted-'+name),**filters)
        assert read_snapshot(EXT/('accepted-'+name))[1]==expected
        rows[0]['property']['reported_value']['number']='999'
        assert {row['record_id']:row for row in db.records(**filters)}==expected
        checks.append(dict(name=name,records=count,native_equals_candidate=True,roundtrip=True,copy_isolation=True))
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in receipt['after_sha256'].items())
    with (HERE/'APPLIED_CONSUMERS_R39.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(snapshot=db.snapshot,checks=checks,native_inputs_unchanged=True,installation_final_review='pending',pushed=False),f,indent=2);f.write('\n')
    print('Actual1new/7NR/13source equalcandidate;exports/readback/copyisolation passed')
if __name__=='__main__':main()
