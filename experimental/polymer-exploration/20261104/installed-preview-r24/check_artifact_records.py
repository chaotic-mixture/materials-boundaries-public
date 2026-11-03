"""Check actual wheel/install RECORDs and complete source export equality."""
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, read_snapshot


def main():
    install = ROOT.parent / 'open-database-evidence/polymer-installed-preview-20261104-r24'
    preview = ROOT.parent / 'open-database-evidence/polymer-epoxy-flexural-elongation-native-20261104-r24/native-tables'
    wheel, = (install / 'dist').glob('*.whl')
    with zipfile.ZipFile(wheel) as archive:
        record, = [n for n in archive.namelist() if n.endswith('.dist-info/RECORD')]
        rows = list(csv.reader(io.StringIO(archive.read(record).decode())))
        assert {r[0] for r in rows} == {n for n in archive.namelist() if not n.endswith('/')}
        checked = 0
        for name, encoded, size in rows:
            if name == record:
                assert not encoded and not size
                continue
            data = archive.read(name)
            assert encoded == 'sha256=' + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
            assert int(size) == len(data)
            checked += 1
    probe = '''import base64,csv,hashlib,importlib.metadata,importlib.util,io,json,marshal,pathlib,sys
d=importlib.metadata.distribution('materials-boundaries')
root=pathlib.Path(sys.prefix).resolve();rows=list(csv.reader(io.StringIO(d.read_text('RECORD'))));checked=0;caches=0
for name,encoded,size in rows:
 p=pathlib.Path(d.locate_file(name)).resolve();assert p.is_relative_to(root),name
 if not encoded:
  assert not size,name
  if name.endswith('.dist-info/RECORD'):continue
  assert '/__pycache__/' in name and name.endswith('.pyc'),name
  source=pathlib.Path(importlib.util.source_from_cache(str(p))).resolve()
  assert source.is_relative_to(root) and source.is_file(),name
  raw=p.read_bytes();assert raw[:4]==importlib.util.MAGIC_NUMBER,name
  code=marshal.loads(raw[16:]);assert code==compile(source.read_bytes(),code.co_filename,'exec',optimize=0),name
  caches+=1
  continue
 data=p.read_bytes();assert encoded=='sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode(),name
 assert int(size)==len(data),name
 checked+=1
print(json.dumps({'installed_RECORD_hashed_files':checked,'installed_RECORD_rows':len(rows),'installer_generated_unhashed_pyc_equal_source':caches}))'''
    result = subprocess.run([str(install / 'venv/Scripts/python.exe'), '-I', '-X', 'utf8', '-B', '-c', probe],
                            cwd=install, capture_output=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stderr)
    installed = json.loads(result.stdout)
    db = Database({name: json.loads((preview / (name + '.json')).read_bytes())
                   for name in ('materials', 'reference_properties', 'sources')})
    _, joined = read_snapshot(install / 'installed-export-tarasov_2022_pna_bpf_epoxy')
    assert joined == {row['property']['id']: row for row in db.records(source='tarasov_2022_pna_bpf_epoxy')}
    assert len(joined) == 30
    value = dict(status='artifact_records_and_complete_export_passed', wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
                 wheel_RECORD_hashed_files=checked, wheel_RECORD_rows=len(rows), **installed,
                 preview_snapshot=db.snapshot, complete_source_export_objects=30,
                 native_applied=False, history_regression='not_run', pushed=False)
    with (install / 'ARTIFACT_RECORDS_AND_EXPORT_R24.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    print(json.dumps(value))


if __name__ == '__main__': main()
