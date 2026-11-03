"""Build and install the frozen r8r11 tables only in a new external directory."""
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
AREA = ROOT / 'experimental/polymer-exploration/20261103'
VERSION = '0.35.0+polymerdelivery.20261103.r8r11'


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
    manifest = read(AREA / 'flexural-strength-native-r1/INSTALL_INPUTS_R1.json')
    for name, expected in manifest['repo_files_sha256'].items():
        assert sha(ROOT / name) == expected, name
    package_inputs = read(args.package_inputs)
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
        assert read(output/'BUILD_INPUTS_R8_R11.json') == binding
    else:
        write(output/'BUILD_INPUTS_R8_R11.json', binding)
    dist = output / 'dist'
    if not args.resume_existing: dist.mkdir()
    build_env = os.environ.copy()
    build_env.update(PYTHONPATH=str(args.build_tools.resolve()), PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    if not args.resume_existing:
        built = subprocess.run([sys.executable,'-B','-c',
            'from setuptools.build_meta import build_wheel; build_wheel('+repr(str(dist))+')'],
            cwd=stage,env=build_env,capture_output=True,encoding='utf-8')
        (output/'wheel-build-r8r11.log').write_text(built.stdout+built.stderr,encoding='utf-8')
        built.check_returncode()
    wheels = list(dist.glob('*.whl'))
    assert len(wheels) == 1
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        payload = {n for n in archive.namelist() if n.startswith('materials_boundaries/') and not n.endswith('/')}
        expected = {n for n in staged_inputs if n.startswith('materials_boundaries/')}
        assert payload == expected, payload ^ expected
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
        (output/'wheel-install-r8r11.log').write_text(install.stdout+install.stderr,encoding='utf-8')
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
rows=list(d.records(quantity='flexural_strength'))
assert len(rows)==6
expected={'PNA-BPF-1':'128.0','PNA-BPF-2':'146.6','PNA-BPF-3':'130.6','PNA-BPF-4':'133.4','PNA-BPF-5':'131.8'}
for row in rows:
    prop=row['property'];assert prop['reported_value']['unit_code']=='MPa'
    assert prop['evaluation_support']=='catalog_only' and prop['engineering_allowable'] is False
    assert prop['method_definition']['extraction_window'] is None
    assert 'criterion' in prop['method_definition']['definition']
    assert 'specified_elongation' not in prop
    if prop['source_id']=='abbasi_2022_manure_phbv':
        assert prop['reported_value']['number']=='20.8' and prop['uncertainty']['number']=='1.4'
        assert prop['summary_statistic']=='reported_mean' and prop['uncertainty_status']=='reported_standard_deviation'
        assert prop['sample_count']['value']==5 and prop['sample_count']['relation']=='at_least'
        assert 'until yield' in prop['method_definition']['definition']
        assert prop['conditions']['loading_rate']['status']=='not_reported_in_inspected_source'
    else:
        label=next(n for n in expected if n in row['state']['name'])
        assert prop['reported_value']['number']==expected[label]
        assert prop['summary_statistic']=='not_stated' and prop['uncertainty'] is None
        assert prop['sample_count']['value'] is None
        assert 'flexural' in row['state']['id'] and '3.6' in row['state']['state']['product_form']['text']
nbr=list(d.records(source='tamas_benyei_santha_2025_nbr_rcf'))
assert len(nbr)==10
ref=next(r['property'] for r in nbr if r['record_id']=='refprop_perbunan3445f_tamas_benyei2025_ref_tensile_strength')
assert ref['reported_value']['number']=='6.01' and ref['uncertainty']['number']=='1.15'
assert ref['summary_statistic']=='reported_mean' and ref['uncertainty_status']=='reported_plus_minus_unspecified' and ref['sample_count']['value'] is None
points=list(d.records(quantity='tensile_stress_at_specified_elongation'));assert len(points)==2
for record in points:
    prop=record['property'];target=prop['specified_elongation']
    assert target['unit_code']=='percent' and target['basis']=='source_reported_percent_elongation'
    assert prop['reported_value']['unit_code']=='MPa'
    assert (target['number'],prop['reported_value']['number'],prop['uncertainty']['number']) in [('100','2.46','0.71'),('200','3.87','1.14')]
    assert prop['sample_count']['value'] is None and prop['uncertainty_status']=='reported_plus_minus_unspecified'
for lang in ('en','zh','ja','de'):
    rendered=render_material_catalog({'schema_version':'1.0.0','records':[r['property'] for r in rows+points]},'reference-properties',lang)
    assert all(t in rendered for t in ('128.0','146.6','130.6','133.4','131.8','20.8','1.4','criterion'))
contracts=d.validate_scientific_contracts()
print(json.dumps({'package_path':str(pathlib.Path(materials_boundaries.__file__).resolve()),
'version':importlib.metadata.version('materials-boundaries'),'snapshot':d.snapshot,
'installed_payload_files_verified':len(payload),'installed_wheel_provenance_verified':True,
'six_flexural_strengths_and_source_specific_unknowns_verified':True,'four_language_rendering':'passed','current_graph_contracts':contracts,
'wheel_metadata_files_verified':metadata_checked,'pip_direct_url_archive_info':direct.get('archive_info'),
'counts':{'identities':len(d.identities),'states':len(d.states),'properties':len(d.properties)},
'polymer':d.summary(category='polymer'),
'source_counts':{s:len(list(d.records(source=s))) for s in ['abbasi_2022_manure_phbv','tarasov_2022_pna_bpf_epoxy','tamas_benyei_santha_2025_nbr_rcf']}}))'''
    result = subprocess.run([str(python),'-I','-X','utf8','-B','-c',probe,str(output/'BUILD_INPUTS_R8_R11.json'),sha(wheel),str(wheel)],cwd=output,env=clean_env,capture_output=True,encoding='utf-8',check=True)
    installed = json.loads(result.stdout)
    assert Path(installed['package_path']).is_relative_to(env_dir.resolve())
    assert installed['version'] == VERSION and installed['snapshot'] == manifest['combined_snapshot']
    assert installed['counts'] == {'identities':5180,'states':5195,'properties':5252}
    frozen_properties = read(args.preview_dir/'reference_properties.json')['records']
    expected_source_counts = {sid:sum(p['source_id']==sid for p in frozen_properties)
                              for sid in installed['source_counts']}
    assert installed['source_counts'] == expected_source_counts
    for source in ('abbasi_2022_manure_phbv','tarasov_2022_pna_bpf_epoxy','tamas_benyei_santha_2025_nbr_rcf'):
        exported = output/('installed-export-'+source)
        for command in [('export','--source',source,'--output',str(exported)),('verify','--snapshot',str(exported))]:
            checked = subprocess.run([str(python),'-I','-X','utf8','-B','-m','materials_boundaries.database',*command],cwd=output,env=clean_env,capture_output=True,encoding='utf-8',check=True)
            response = json.loads(checked.stdout)
            if command[0] == 'verify': assert response['status']=='snapshot_integrity_passed'
            write(output/('installed-'+command[0]+'-'+source+'-r8r11.json'),response)
    # Repository bytes must still be exactly the package baseline.
    for name, expected in package_inputs.items(): assert sha(ROOT/name) == expected, name
    write(output/'INSTALLED_VALIDATION_R8_R11.json', {'schema':'polymer-preview-installed-validation/3',
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
