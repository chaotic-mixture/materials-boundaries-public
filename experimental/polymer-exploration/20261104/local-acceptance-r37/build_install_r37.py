"""Build a local experimental wheel and verify its real isolated installation."""
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv
import zipfile

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r37/installed-check'
VERSION = '0.35.0+polymerlocal.20261104.r37'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def command(args, cwd, env, log):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True)
    log.write_bytes(result.stdout + result.stderr)
    result.check_returncode()
    return result


def main():
    resume = sys.argv[1:] == ['--resume-existing']
    assert not sys.argv[1:] or resume
    application = read(OUT / 'APPLICATION_R37.json')
    assert all(sha(ROOT / n) == h for n, h in application['after_sha256'].items())
    assert EXT.exists() == resume
    if not resume:
        EXT.mkdir(parents=True)
    recipe = read(OUT.parent / 'delivery-r29-r32/PACKAGE_INPUTS_R29_R32.json')
    native = {n: sha(ROOT / n) for n in recipe}
    assert len(native) == 69
    if resume:
        assert read(OUT / 'PACKAGE_INPUTS_R37.json') == native
    else:
        write(OUT / 'PACKAGE_INPUTS_R37.json', native)
    stage = EXT / 'source'
    if not resume:
        stage.mkdir()
        for name in native:
            destination = stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
    version_file = stage / 'materials_boundaries/_version.py'
    text = version_file.read_text(encoding='utf-8')
    if not resume:
        assert text.count('__version__ = "0.35.0"') == 1
        version_file.write_text(text.replace('__version__ = "0.35.0"', f'__version__ = "{VERSION}"'), encoding='utf-8', newline='\n')
    staged = {n: sha(stage / n) for n in recipe}
    assert [n for n in recipe if staged[n] != native[n]] == ['materials_boundaries/_version.py']
    binding = {'native': native, 'staged': staged, 'isolated_version_only': VERSION}
    if resume:
        assert read(EXT / 'BUILD_INPUTS_R37.json') == binding
    else:
        write(EXT / 'BUILD_INPUTS_R37.json', binding)
    dist = EXT / 'dist'
    if not resume:
        dist.mkdir()
    env = os.environ.copy()
    env.update(PYTHONPATH=str(ROOT.parent / 'growth-tools/sanchez-wheel-build/site-packages'), PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    if not resume:
        command([sys.executable, '-B', '-c', 'from setuptools.build_meta import build_wheel;build_wheel(' + repr(str(dist)) + ')'], stage, env, EXT / 'build-r37.log')
    wheels = list(dist.glob('*.whl'))
    assert len(wheels) == 1
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        payload = {n for n in archive.namelist() if n.startswith('materials_boundaries/') and not n.endswith('/')}
        assert payload == {n for n in staged if n.startswith('materials_boundaries/')} and len(payload) == 65
        assert all(hashlib.sha256(archive.read(n)).hexdigest() == staged[n] for n in payload)
        assert not any(n.startswith('experimental/') or n.lower().endswith(('.pdf', '.xml', '.png', '.jpg')) for n in archive.namelist())
        record_name = next(n for n in archive.namelist() if n.endswith('.dist-info/RECORD'))
        count = 0
        for name, digest, size in csv.reader(io.StringIO(archive.read(record_name).decode())):
            if name == record_name:
                assert digest == size == ''
                continue
            content = archive.read(name)
            assert digest == 'sha256=' + base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip('=')
            assert len(content) == int(size)
            count += 1
    environment = EXT / 'venv'
    if not resume:
        venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / 'Scripts/python.exe'
    clean = os.environ.copy()
    clean.pop('PYTHONPATH', None)
    clean.pop('PYTHONHOME', None)
    clean.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    if not resume:
        command([str(python), '-I', '-X', 'utf8', '-m', 'pip', '--isolated', '--disable-pip-version-check', 'install', '--no-index', '--no-deps', '--no-cache-dir', '--no-compile', str(wheel)], EXT, clean, EXT / 'install-r37.log')
    probe = r'''import base64,csv,hashlib,importlib.metadata,io,json,pathlib,sys,zipfile
from materials_boundaries.database import Database,read_snapshot
from materials_boundaries.material_references import validate_material_catalog
import materials_boundaries
folder=pathlib.Path(sys.argv[1]);version=sys.argv[2];snapshot=sys.argv[3]
binding=json.loads((folder/'BUILD_INPUTS_R37.json').read_bytes())
distribution=importlib.metadata.distribution('materials-boundaries')
assert distribution.version==version
assert pathlib.Path(materials_boundaries.__file__).is_relative_to(folder/'venv')
payload={n:h for n,h in binding['staged'].items() if n.startswith('materials_boundaries/')}
for n,h in payload.items():assert hashlib.sha256(distribution.locate_file(n).read_bytes()).hexdigest()==h,n
record=distribution.read_text('RECORD');checked=0
for n,digest,size in csv.reader(io.StringIO(record)):
    if not digest:continue
    content=distribution.locate_file(n).read_bytes()
    assert digest=='sha256='+base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip('=')
    assert len(content)==int(size);checked+=1
with zipfile.ZipFile(sys.argv[4]) as wheel:
    for n in wheel.namelist():
        if '.dist-info/' in n and not n.endswith(('/','/RECORD')):assert distribution.locate_file(n).read_bytes()==wheel.read(n)
db=Database();assert db.snapshot==snapshot
validate_material_catalog(*(db.data[n] for n in ('materials','reference_properties','sources')))
rows=list(db.records(query='_tga_platinum_pan',source='ivdre_2024_lpo_rigid_pur'));assert len(rows)==28
for row in rows:
    p=row['property'];assert p['sample_count']['value'] is None and p['summary_statistic']=='not_stated'
    assert p['uncertainty']['type']=='reported_plus_minus_unspecified'
    assert p['uncertainty']['confidence_level'] is None and p['uncertainty']['coverage_factor'] is None
    assert p['conditions']['temperature']['status']=='reported' and p['conditions']['conditioning']['text'] is None
    assert len(row['state']['property_ids'])==7 and p['id'] in row['state']['property_ids']
    if p['quantity'] in ('tga_residue_percentage','temperature_at_specified_mass_loss'):
        assert p['mass_reference_basis']['status']=='not_reported_in_inspected_source' and p['mass_reference_basis']['text'] is None
    assert p['evaluation_support']=='catalog_only' and not p['engineering_allowable'] and not p['universal_bound']
export=folder/'installed-twenty-eight-export';db.export(export,query='_tga_platinum_pan',source='ivdre_2024_lpo_rigid_pur')
assert read_snapshot(export)[1]=={row['record_id']:row for row in rows}
native_evidence=folder.parent
assert read_snapshot(export)[1]==read_snapshot(native_evidence/'accepted-new-twenty-eight')[1]
allsource=list(db.records(source='ivdre_2024_lpo_rigid_pur'));assert len(allsource)==40
full=folder/'installed-source-forty-export';db.export(full,source='ivdre_2024_lpo_rigid_pur')
assert read_snapshot(full)[1]=={row['record_id']:row for row in allsource}
assert read_snapshot(full)[1]==read_snapshot(native_evidence/'accepted-complete-source-forty')[1]
original=list(db.records(query='_tga_platinum_pan',source='ivdre_2024_lpo_rigid_pur'))
rows[0]['property']['reported_value']['number']='999'
assert list(db.records(query='_tga_platinum_pan',source='ivdre_2024_lpo_rigid_pur'))==original
print(json.dumps({'version':distribution.version,'snapshot':db.snapshot,'properties':len(db.properties),'states':len(db.states),'verified_payload_files':len(payload),'installed_record_hashes_checked':checked,'new_TGA_records':len(rows),'complete_source_records':len(allsource),'installed_graph':'passed','joined_export_roundtrip':'exact','installed_exports_equal_accepted_candidates':True,'detached_copy_isolation':True,'module_path':str(materials_boundaries.__file__)}))
'''
    (EXT / 'installed_probe.py').write_text(probe, encoding='utf-8', newline='\n')
    result = command([str(python), '-I', '-X', 'utf8', '-B', str(EXT / 'installed_probe.py'), str(EXT), VERSION, application['snapshot'], str(wheel)], EXT, clean, EXT / 'probe-r37-r1.log')
    assert all(sha(ROOT / n) == h for n, h in native.items())
    summary = {'scope': 'Actual offline experimental wheel and new isolated installation', 'wheel_sha256': sha(wheel), 'wheel_path_hint': str(wheel), 'wheel_record_hashes_checked': count, 'installed_probe': json.loads(result.stdout), 'native_package_inputs_unchanged': True, 'native_version': '0.35.0', 'local_version_only': VERSION, 'resumed_existing_artifact_without_rebuild_reinstall': resume, 'original_pip_exit_code': read(EXT / 'ORIGINAL_INSTALL_EXECUTION_R1.json')['pip_install_exit_code'] if resume else 0, 'full_history': 'not_run', 'HTTP': 'not_run', 'pushed': False}
    write(OUT / 'INSTALLED_VALIDATION_R37.json', summary)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
