"""Verify all nine added records and fifty affected source joins in real install."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-consolidated-delivery-20261104-r33-r35'
INSTALL = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r35/installed-check'
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert not EXT.exists()
    delta = read(OUT / 'NATIVE_DELTA_R33_R35.json')
    package_inputs = read(OUT.parent / 'local-acceptance-r35/PACKAGE_INPUTS_R35.json')
    assert all(sha(ROOT / n) == h for n, h in package_inputs.items())
    db = Database()
    assert db.snapshot == delta['current_snapshot']
    expected = {sid: list(db.records(source=sid)) for sid in delta['source_updates']}
    assert sum(map(len, expected.values())) == 50
    assert sorted(map(len, expected.values())) == [8, 12, 30]
    assert all(db.properties[n] == row for n, row in delta['new_property_records'].items())
    assert all(db.states[n] == row for n, row in delta['new_state_records'].items())
    EXT.mkdir()
    write(EXT / 'EXPECTED_CURRENT_SOURCE_RECORDS_R33_R35.json', expected)
    write(EXT / 'EXPECTED_CURRENT_ADDITIONS_R33_R35.json', delta)
    probe = r'''from pathlib import Path
from copy import deepcopy
import hashlib,importlib.metadata,json,sys
import materials_boundaries
from materials_boundaries.database import Database,read_snapshot
out=Path(sys.argv[1]);installation=Path(sys.argv[2]);native=Path(sys.argv[3])
assert Path(materials_boundaries.__file__).is_relative_to(installation/'venv')
assert importlib.metadata.version('materials-boundaries')=='0.35.0+polymerlocal.20261104.r35'
delta=json.loads((out/'EXPECTED_CURRENT_ADDITIONS_R33_R35.json').read_bytes())
expected=json.loads((out/'EXPECTED_CURRENT_SOURCE_RECORDS_R33_R35.json').read_bytes())
db=Database();assert db.snapshot==delta['current_snapshot']
for table in ['materials','reference_properties','sources']:
    from importlib.resources import files
    installed=files('materials_boundaries').joinpath('data',table+'.json').read_bytes()
    assert installed==(native/'materials_boundaries/data'/ (table+'.json')).read_bytes()
assert all(db.properties[n]==row for n,row in delta['new_property_records'].items())
assert all(db.states[n]==row for n,row in delta['new_state_records'].items())
counts={}
for sid,rows in expected.items():
    actual=list(db.records(source=sid));assert actual==rows
    export=out/('installed-'+sid);db.export(export,source=sid)
    assert read_snapshot(export)[1]=={row['record_id']:row for row in rows}
    counts[sid]=len(rows)
added={}
for quantity,count in [('dielectric_breakdown_strength',5),('thermal_conductivity',4)]:
    rows=list(db.records(quantity=quantity));assert len(rows)==count
    for row in rows:
        assert row['property']==delta['new_property_records'][row['record_id']]
        assert row['property']['uncertainty'] is None
        assert row['property']['evaluation_support']=='catalog_only'
    original=deepcopy(rows);rows[0]['property']['reported_value']['number']='0'
    assert list(db.records(quantity=quantity))==original
    added[quantity]=len(rows)
print(json.dumps({'snapshot':db.snapshot,'properties':len(db.properties),'states':len(db.states),'all3native_installed_tables_byte_equal':True,'new_records':added,'complete_source_joins':counts,'total_complete_source_records':sum(counts.values()),'source_exports_roundtrip':'exact','copy_isolation':True,'module_path':str(materials_boundaries.__file__)}))
'''
    (EXT / 'actual_installed_consumer.py').write_text(probe, encoding='utf-8', newline='\n')
    result = subprocess.run([str(INSTALL / 'venv/Scripts/python.exe'), '-I', '-X', 'utf8', '-B', str(EXT / 'actual_installed_consumer.py'), str(EXT), str(INSTALL), str(ROOT)], cwd=EXT, capture_output=True)
    (EXT / 'actual-installed-consumer-r33-r35.log').write_bytes(result.stdout + result.stderr)
    result.check_returncode()
    assert all(sha(ROOT / n) == h for n, h in package_inputs.items())
    write(OUT / 'ACTUAL_CONSUMER_R33_R35.json', {'scope': 'Current native versus real already-installed r35 package;not another install or scientific certification', 'exit_code': result.returncode, 'result': json.loads(result.stdout), 'package_inputs_unchanged': True, 'package_manifest_sha256': sha(OUT.parent / 'local-acceptance-r35/PACKAGE_INPUTS_R35.json'), 'external_files_sha256': {str(p): sha(p) for p in EXT.rglob('*') if p.is_file()}, 'full_history': 'not_run', 'HTTP_service': 'not_run', 'pushed': False})
    print(result.stdout.decode('utf-8'), flush=True)


if __name__ == '__main__':
    main()
