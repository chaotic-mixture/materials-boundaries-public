"""Build and install the frozen r27 tables only in a new external directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv
import zipfile

ROOT = Path(__file__).resolve().parents[4]
AREA = ROOT / 'experimental/polymer-exploration/20261104'
VERSION = '0.35.0+polymerpreview.20261104.r27'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-inputs', type=Path, required=True)
    parser.add_argument('--preview-dir', type=Path, required=True)
    parser.add_argument('--build-tools', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--resume-existing', action='store_true', help='Verify and resume this exact interrupted build; never rebuild')
    parser.add_argument('--accepted-native', action='store_true', help='Package current native bytes after checking semantic equality to the reviewed preview')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    assert not output.is_relative_to(ROOT)
    assert output.exists() == args.resume_existing
    manifest = read(AREA / 'phbv39-tg-native-r1/REVIEW_INPUTS_R1.json')
    review = read(AREA / 'phbv39-tg-native-r1/INDEPENDENT_MAPPING_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(AREA / 'phbv39-tg-native-r1/REVIEW_INPUTS_R1.json')
    for name, expected in manifest['repo_files_sha256'].items():
        assert sha(ROOT / name) == expected, name
    package_inputs = read(args.package_inputs)
    assert package_inputs == read(Path(__file__).resolve().parent/'PACKAGE_INPUTS_R27.json')
    assert package_inputs == manifest['package_inputs_sha256']
    assert set(package_inputs) == set(read(ROOT/'experimental/polymer-exploration/20261104/delivery-r23-r25/PACKAGE_INPUTS_R23_R25.json'))
    assert len(package_inputs) == 69
    for name, expected in package_inputs.items():
        source = (ROOT / name).resolve()
        assert source.is_relative_to(ROOT) and sha(source) == expected, name
    for name, expected in manifest['external_preview_files_sha256'].items():
        assert name in ('materials.json','reference_properties.json','sources.json')
        assert sha(args.preview_dir / name) == expected, name
    stage = output / 'source'
    if not args.resume_existing:
        output.mkdir(parents=True)
        stage.mkdir()
        for name in package_inputs:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        for name in manifest['external_preview_files_sha256']:
            if args.accepted_native:
                assert read(ROOT/'materials_boundaries/data'/name)==read(args.preview_dir/name)
            else:
                shutil.copyfile(args.preview_dir / name, stage / 'materials_boundaries/data' / name)
        version_file = stage / 'materials_boundaries/_version.py'
        original_version = version_file.read_text(encoding='utf-8')
        assert original_version.count('__version__ = "0.35.0"') == 1
        version_file.write_text(original_version.replace('__version__ = "0.35.0"', f'__version__ = "{VERSION}"'), encoding='utf-8')
    staged_inputs = {name:sha(stage/name) for name in package_inputs}
    changed_inputs = sorted(name for name in package_inputs if staged_inputs[name] != package_inputs[name])
    expected_changes = ['materials_boundaries/_version.py']
    if not args.accepted_native: expected_changes += ['materials_boundaries/data/'+n for n in manifest['external_preview_files_sha256']]
    assert changed_inputs == sorted(expected_changes)
    binding = {'baseline_inputs':package_inputs,'staged_inputs':staged_inputs,
          'changed_staged_inputs':changed_inputs,'version_scope':'local preview only; repository version unchanged',
          'preview_snapshot':manifest['combined_snapshot']}
    if args.resume_existing:
        assert read(output/'BUILD_INPUTS_R27.json') == binding
    else:
        write(output/'BUILD_INPUTS_R27.json', binding)
    dist = output / 'dist'
    if not args.resume_existing: dist.mkdir()
    build_env = os.environ.copy()
    build_env.update(PYTHONPATH=str(args.build_tools.resolve()), PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    if not args.resume_existing:
        built = subprocess.run([sys.executable,'-B','-c',
            'from setuptools.build_meta import build_wheel; build_wheel('+repr(str(dist))+')'],
            cwd=stage,env=build_env,capture_output=True,encoding='utf-8')
        (output/'wheel-build-r27.log').write_text(built.stdout+built.stderr,encoding='utf-8')
        built.check_returncode()
    wheels = list(dist.glob('*.whl'))
    assert len(wheels) == 1
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        payload = {n for n in archive.namelist() if n.startswith('materials_boundaries/') and not n.endswith('/')}
        expected = {n for n in staged_inputs if n.startswith('materials_boundaries/')}
        assert payload == expected, payload ^ expected
        assert len(payload) == len(expected) == 65
        assert len([n for n in archive.namelist() if '.dist-info/' in n and not n.endswith(('/', '/RECORD'))]) == 6
        for name in payload:
            assert hashlib.sha256(archive.read(name)).hexdigest() == staged_inputs[name], name
        assert not any(n.lower().endswith(('.pdf','.xml','.xlsx')) or n.startswith('experimental/') for n in archive.namelist())
    print('Wheel artifact and payload hashes verified', flush=True)
    env_dir = output/'venv'
    if not args.resume_existing: venv.EnvBuilder(with_pip=True).create(env_dir)
    python = env_dir/('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    clean_env = os.environ.copy()
    clean_env.pop('PYTHONPATH', None)
    clean_env.pop('PYTHONHOME', None)
    clean_env.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    if not args.resume_existing:
        install = subprocess.run([str(python),'-I','-X','utf8','-m','pip','--isolated','--disable-pip-version-check',
            'install','--no-index','--no-deps','--no-cache-dir',str(wheel)],
            cwd=output,env=clean_env,capture_output=True,encoding='utf-8')
        (output/'wheel-install-r27.log').write_text(install.stdout+install.stderr,encoding='utf-8')
        install.check_returncode()
    probe = '''import json, pathlib, importlib.metadata, materials_boundaries, sys, hashlib, zipfile
from urllib.parse import urlsplit
from urllib.request import url2pathname
from materials_boundaries.database import Database
distribution=importlib.metadata.distribution('materials-boundaries')
expected=json.loads(pathlib.Path(sys.argv[1]).read_bytes())['staged_inputs']
payload={n:h for n,h in expected.items() if n.startswith('materials_boundaries/')}
for name, digest in payload.items():
    assert hashlib.sha256(distribution.locate_file(name).read_bytes()).hexdigest()==digest,name
direct=json.loads(distribution.read_text('direct_url.json'))
assert urlsplit(direct['url']).scheme=='file'
assert pathlib.Path(url2pathname(urlsplit(direct['url']).path)).resolve()==pathlib.Path(sys.argv[3]).resolve()
assert hashlib.sha256(pathlib.Path(sys.argv[3]).read_bytes()).hexdigest()==sys.argv[2]
metadata_checked=0
with zipfile.ZipFile(sys.argv[3]) as archive:
    for name in archive.namelist():
        if '.dist-info/' in name and not name.endswith(('/','/RECORD')):
            assert distribution.locate_file(name).read_bytes()==archive.read(name),name
            metadata_checked+=1
d=Database()
from materials_boundaries.material_presentation import render_material_catalog
facts=json.loads(pathlib.Path(sys.argv[4]).read_bytes())
rows=list(facts['property_records'].values())
assert len(rows)==1 and len(facts['state_records'])==1
for p in rows:
 assert d.properties[p['id']]==p
 assert p['quantity']=='glass_transition_temperature' and p['reported_value']['unit_code']=='degC'
 assert p['conditions']['loading_rate']['status']=='not_applicable'
 assert next(c['fact'] for c in p['conditions']['additional_conditions'] if c['name']=='Tg_extraction_criterion')['status']=='reported'
 assert p['summary_statistic']=='not_stated' and p['uncertainty'] is None and p['sample_count']['value'] is None
 assert p['evaluation_support']=='catalog_only' and not p['engineering_allowable'] and not p['universal_bound']
for sid,state in facts['state_records'].items():assert d.states[sid]==state
src=facts['source_record'];assert d.sources[src['id']]==src
assert {r['property']['id']:r['property'] for r in d.records(quantity='glass_transition_temperature',source='abbasi_2022_manure_phbv')}==facts['property_records']
assert {r['property']['id']:r['property'] for r in d.records(quantity='glass_transition_temperature')}==facts['all_Tg_property_records']
for lang in ('en','zh','ja','de'):
 text=render_material_catalog({'schema_version':'1.0.0','records':rows},'reference-properties',lang)
 assert all(p['reported_value']['number'] in text for p in rows)
 assert all(t in text for t in ('°C','−5.3','inflection','second heating','Guho','unknown','duplicate'))
assert metadata_checked==6
contracts=d.validate_scientific_contracts()
print(json.dumps({'package_path':str(pathlib.Path(materials_boundaries.__file__).resolve()),
'version':importlib.metadata.version('materials-boundaries'),'snapshot':d.snapshot,
'installed_payload_files_verified':len(payload),'installed_wheel_provenance_verified':True,
'exact_one_PHBV_Tg_and_all_six_Tg_objects_verified':True,'four_language_rendering':'passed','current_graph_contracts':contracts,
'wheel_metadata_files_verified':metadata_checked,'pip_direct_url_archive_info':direct.get('archive_info'),
'counts':{'identities':len(d.identities),'states':len(d.states),'properties':len(d.properties)},
'polymer':d.summary(category='polymer'),
'source_counts':{s:len(list(d.records(source=s))) for s in ['abbasi_2022_manure_phbv',]}}))'''
    result = subprocess.run([str(python),'-I','-X','utf8','-B','-c',probe,str(output/'BUILD_INPUTS_R27.json'),sha(wheel),str(wheel),str(AREA/'phbv39-tg-native-r1/MAPPING_FACTS_R1.json')],cwd=output,env=clean_env,capture_output=True,encoding='utf-8',check=True)
    installed = json.loads(result.stdout)
    assert Path(installed['package_path']).is_relative_to(env_dir.resolve())
    assert installed['version'] == VERSION and installed['snapshot'] == manifest['combined_snapshot']
    assert installed['counts'] == {'identities':5180,'states':5218,'properties':5333}
    frozen_properties = read(args.preview_dir/'reference_properties.json')['records']
    expected_source_counts = {sid:sum(p['source_id']==sid for p in frozen_properties)
                              for sid in installed['source_counts']}
    assert installed['source_counts'] == expected_source_counts
    for source in ('abbasi_2022_manure_phbv',):
        exported = output/('installed-export-'+source)
        for command in [('export','--source',source,'--output',str(exported)),('verify','--snapshot',str(exported))]:
            checked = subprocess.run([str(python),'-I','-X','utf8','-B','-m','materials_boundaries.database',*command],cwd=output,env=clean_env,capture_output=True,encoding='utf-8',check=True)
            response = json.loads(checked.stdout)
            if command[0] == 'verify': assert response['status']=='snapshot_integrity_passed'
            write(output/('installed-'+command[0]+'-'+source+'-r27.json'),response)
    # Repository bytes must still be exactly the package baseline.
    for name, expected in package_inputs.items(): assert sha(ROOT/name) == expected, name
    write(output/'INSTALLED_VALIDATION_R27.json', {'schema':'polymer-preview-installed-validation/3',
          'stage':'isolated_candidate_install_not_acceptance','wheel_name':wheel.name,'wheel_sha256':sha(wheel),
          'version':VERSION,'package_payload_files_verified':len(payload),'staged_input_files':len(staged_inputs),
          'installed':installed,'install':('existing_install_payload_and_wheel_provenance_verified_no_reinstall' if args.resume_existing else 'passed_no_index_no_deps_no_cache'),
          'resume_existing':args.resume_existing,
          'accepted_native_input_mode':args.accepted_native,
          'installed_export_verify':'passed','repository_package_inputs_unchanged':len(package_inputs),
          'independent_review':'pending','full_history_regression':'not_run','published':False})
    print(json.dumps({'status':'isolated_candidate_install_passed','wheel_sha256':sha(wheel),
                     'snapshot':installed['snapshot'],'installed_counts':installed['counts']}),flush=True)


if __name__ == '__main__':
    main()
