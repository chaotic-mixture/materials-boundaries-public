"""Derive consolidated checks from exact prior approved delivery/install helpers."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def main():
    previous = HERE.parent / 'delivery-r33-r35/validate_delivery.py'
    baseline = subprocess.check_output(['git', 'show', '13c6fa6480bac5bf1ea63442a571a1658b0e4cf3:' + previous.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert previous.read_bytes() == baseline
    code = previous.read_text(encoding='utf-8').replace("'test_database*.py',", "'test_database*.py', 'test_tga_endpoint_contract.py',", 1)
    code = code.replace('local-acceptance-r35/PACKAGE_INPUTS_R35.json', 'local-acceptance-r37/PACKAGE_INPUTS_R37.json')
    code = code.replace('R33_R35', 'R36_R38').replace('r33-r35', 'r36-r38').replace('current5380property', 'current5412property')
    code = code.replace('203', '218')
    with (HERE / 'validate_delivery.py').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(code)
    installer = HERE.parent / 'local-acceptance-r37/build_install_r37.py'
    entry = json.loads((HERE.parent / 'local-acceptance-r37/REVIEW_ACCEPTANCE_INPUTS_R37_R2.json').read_bytes())
    assert hashlib.sha256(installer.read_bytes()).hexdigest() == entry['repo_files_sha256'][installer.relative_to(ROOT).as_posix()]
    code = installer.read_text(encoding='utf-8')
    start = code.index("rows=list(db.records(query='_tga_platinum_pan'")
    end = code.index("\n'''", start)
    probe = r'''exports=[('new-four-dma',dict(quantity='glass_transition_temperature',source='ivdre_2024_lpo_rigid_pur'),4),
 ('new-twenty-eight',dict(query='_tga_platinum_pan',source='ivdre_2024_lpo_rigid_pur'),28),
 ('complete-source-forty',dict(source='ivdre_2024_lpo_rigid_pur'),40),
 ('epoxy-source-forty',dict(source='tarasov_2022_pna_bpf_epoxy'),40)]
checks=[]
for name,filters,expected in exports:
    rows=list(db.records(**filters));assert len(rows)==expected
    output=folder/('installed-'+name);db.export(output,**filters)
    current={row['record_id']:row for row in rows}
    assert read_snapshot(output)[1]==current
    assert read_snapshot(folder.parent/('accepted-'+name))[1]==current
    for row in rows:
        p=row['property'];assert p==db.properties[row['record_id']]
        assert row['state']==db.states[p['material_state_id']]
        assert row['identity']==db.identities[row['state']['identity_id']]
        assert p['evaluation_support']=='catalog_only' and not p['engineering_allowable'] and not p['universal_bound']
    rows[0]['property']['reported_value']['number']='999'
    rows[0]['sources'][0]['claim_notes'].append('detached mutation')
    assert {row['record_id']:row for row in db.records(**filters)}==current
    checks.append({'name':name,'records':expected,'installed_equals_native_export':True,'copy_isolation':True})
assert len(db.properties)==5412 and len(db.states)==5262
print(json.dumps({'version':distribution.version,'snapshot':db.snapshot,'properties':len(db.properties),'states':len(db.states),'verified_payload_files':len(payload),'installed_record_hashes_checked':checked,'exports':checks,'installed_graph':'passed','joined_export_roundtrip':'exact','module_path':str(materials_boundaries.__file__)}))'''
    code = code[:start] + probe + code[end:]
    code = code.replace('R37', 'R36_R38').replace('r37', 'delivery-r36-r38')
    code = code.replace("VERSION = '0.35.0+polymerlocal.20261104.delivery-r36-r38'", "VERSION = '0.35.0+polymerlocal.20261104.delivery3638'")
    assert "VERSION = '0.35.0+polymerlocal.20261104.delivery3638'" in code
    assert 'accepted-epoxy-source-forty' not in code  # generated uniformly in probe loop
    with (HERE / 'build_install_delivery.py').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(code)
    print('Consolidated218checks and fresh four-export installer prepared')


if __name__ == '__main__':
    main()
