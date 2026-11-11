"""Derive current installer from exact published consolidated installer."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def main():
    relative='experimental/polymer-exploration/20261104/delivery-r36-r38/build_install_delivery.py'
    raw=subprocess.check_output(['git','show','ba67983dc11ee8c92ef1c9890b4164adfaf4a83d:'+relative],cwd=ROOT)
    assert (ROOT/relative).read_bytes()==raw
    code=raw.decode('utf-8');start=code.index('exports=[');end=code.index("\n'''",start)
    probe=r'''exports=[('new-work',dict(quantity='volumetric_tensile_work_to_break',source='bianchi_2025_nr_nanoclay'),1),
 ('existing-NR-seven',dict(query='mat_smr10_bianchi2025_nr',source='bianchi_2025_nr_nanoclay'),7),
 ('complete-source-thirteen',dict(source='bianchi_2025_nr_nanoclay'),13)]
checks=[]
for name,filters,expected in exports:
    rows=list(db.records(**filters));assert len(rows)==expected
    current=copy.deepcopy({row['record_id']:row for row in rows})
    output=folder/('installed-'+name);db.export(output,**filters)
    assert read_snapshot(output)[1]==current
    assert read_snapshot(folder.parent/('accepted-'+name))[1]==current
    for row in rows:
        assert row['property']==db.properties[row['record_id']]
        assert row['state']==db.states[row['property']['material_state_id']]
    rows[0]['property']['reported_value']['number']='999'
    rows[0]['sources'][0]['claim_notes'].append('detached mutation')
    assert {row['record_id']:row for row in db.records(**filters)}==current
    checks.append(dict(name=name,records=expected,installed_equals_native_export=True,copy_isolation=True))
p=next(db.records(quantity='volumetric_tensile_work_to_break'))['property']
assert p['reported_value']['number']=='32.2' and p['uncertainty']['number']=='6.4'
assert p['summary_statistic']=='reported_mean' and p['sample_count']['value']==5
assert p['work_reference_basis']['text'] is None and p['source_discrepancies']
assert len(db.properties)==5413 and len(db.states)==5262
print(json.dumps(dict(version=distribution.version,snapshot=db.snapshot,properties=len(db.properties),states=len(db.states),verified_payload_files=len(payload),installed_record_hashes_checked=checked,exports=checks,installed_graph='passed',joined_export_roundtrip='exact',module_path=str(materials_boundaries.__file__))))'''
    code=code[:start]+probe+code[end:]
    code=code.replace('R36_R38','R39').replace('delivery-r36-r38','r39').replace('20261104-r39','20261111-r39')
    code=code.replace('0.35.0+polymerlocal.20261104.delivery3638','0.35.0+polymerlocal.20261111.r39')
    code=code.replace("OUT.parent / 'delivery-r29-r32/PACKAGE_INPUTS_R29_R32.json'", "ROOT / 'experimental/polymer-exploration/20261104/delivery-r29-r32/PACKAGE_INPUTS_R29_R32.json'")
    with (HERE/'build_install_r39.py').open('x',encoding='utf-8',newline='\n') as f:f.write(code)
    print('Current r39 installer prepared;published probe replaced in full')
if __name__=='__main__':main()
