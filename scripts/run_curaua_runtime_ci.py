#!/usr/bin/env python3
"""Explicit Curaua runtime checks beside the unchanged complete-core workflow.

The manifest freezes whole source modules and complete installed groups. Test
discovery is not execution; incomplete, skipped or unexpected outcomes cannot
produce a completion record. Actions metadata is validated, not attested.
"""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import venv

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from run_polymer_composites_ci import (
    PACKAGES, clean_env, install_offline_guard, installed_origins,
    require, run, test_ids, verify_wheels,
)

BASE_COMMIT = 'fa170104195e573c868c57006ac77e7d866c28e9'
BRANCH_REF = 'refs/heads/experimental/czlonka2021-curaua-runtime'
BATCH = 'experimental/material-batches/czlonka-curaua-20261025'
PACKET_SHA256 = '272f524862d9dac790dfcf218745627598554c67d4f667c37c40f7adcaa54e43'
MANIFEST_PATH = 'tests/curaua_ci/manifest.json'
MANIFEST_SHA256 = '06896e93f187c13c5b09c0d98c656cd2e9f634208bcb3b04fa213b2b84acf896'
WORKFLOW_PATH = '.github/workflows/curaua-runtime.yml'
SOURCE_GROUPS = ('candidate', 'preservation', 'contracts', 'compatibility', 'partition-contracts')
INSTALLED_GROUPS = ('query', 'formal', 'ingestion', 'relationships', 'provider', 'transport', 'lifecycle', 'integration')
GRAPH_COUNTS = {'identity': 1164, 'grade': 31, 'state': 1165, 'property': 1176, 'source': 128}
DELTA_COUNTS = {'identity': 3, 'grade': 0, 'state': 3, 'property': 3, 'source': 1}
PRIMARY_COUNTS = {'natural': 1010, 'metal': 32, 'inorganic': 59, 'polymer': 30, 'composite': 33}
FORMAL_COUNTS = {'formal_project_admission_count': 1188,
                 'legacy_source_qualified_identity_count': 1164,
                 'reviewed_computed_composition_count': 24,
                 'categories': {'natural': 1010, 'metal': 44, 'inorganic': 71, 'polymer': 30, 'composite': 33}}
CANDIDATE_ARTIFACTS = tuple(BATCH + '/' + name for name in (
    'README.md', 'VALIDATION.md', 'build_identity_review.py', 'identity-review.json',
    'packet-spec.json', 'preparation-receipt.json', 'prepared-packet.json',
    'source-review.json', 'validation-results.json'))
PROTECTED_PATHS = ('.github/workflows/ci.yml', '.github/workflows/history-replay-latest.yml',
                   'tests/core_partition/manifest.json',
                   'experimental/platform/query-service/materials_query/pins/family_relationships.json',
                   'formal-catalog/materials_project_catalog/data/formal_computed_review.json',
                   'materials_boundaries/data/observations.json',
                   'materials_boundaries/data/computational_predictions.json',
                   'experimental/platform/examples/reviewed-computed-v2-second/normalized-review.json',
                   'experimental/platform/examples/reviewed-computed-seed/scoped-review-input.json')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, timeout=60)


def fingerprint(ids):
    return sha256(''.join(identifier + '\n' for identifier in sorted(ids)).encode('utf-8')).hexdigest()


def validate_manifest(value):
    require(type(value) is dict and value.get('schema') == 'curaua-runtime-ci/1', 'Unknown CI manifest')
    require(value.get('baseline_commit') == BASE_COMMIT, 'CI baseline changed')
    require(value.get('frozen_contract') is True, 'CI inventory is not frozen')
    require(set(value['source_groups']) == set(SOURCE_GROUPS), 'Source group set changed')
    require(set(value['installed_groups']) == set(INSTALLED_GROUPS), 'Installed group set changed')
    for group in [*value['source_groups'].values(), *value['installed_groups'].values()]:
        ids = group['ids']
        require(type(ids) is list and ids and all(type(x) is str for x in ids), 'Invalid test IDs')
        require(ids == sorted(set(ids)) and group['count'] == len(ids), 'Duplicate, unordered or missing IDs')
        require(group['sha256'] == fingerprint(ids), 'Test ID digest changed')
        require(type(group['directory']) is str and not Path(group['directory']).is_absolute(), 'Invalid test directory')
        require(group['directory'].split('/')[0] in {'tests', 'experimental', 'formal-catalog'}
                and '..' not in group['directory'].split('/'), 'Unsafe test directory')
        require(type(group['modules']) is list and group['modules'] == sorted(set(group['modules']))
                and all(type(x) is str and x.startswith('test') and '/' not in x and '\\' not in x
                        and '.' not in x for x in group['modules']), 'Invalid module inventory')
    require(value['core_inventory'] == {'modules': 147, 'methods': 1887,
                'sha256': '19a735217c29533c1137a6cfd95b2b58cf88e8cf649848e41012c510434446f7'},
            'Complete core inventory changed')
    require(value['replay_inventory_count'] == 70, 'Replay inventory changed')
    require(type(value['approved_paths']) is list and value['approved_paths'] == sorted(set(value['approved_paths']))
            and value['approved_paths'], 'Approved path inventory is absent or duplicated')
    return value


def load_manifest():
    raw = (ROOT / MANIFEST_PATH).read_bytes()
    require(len(MANIFEST_SHA256) == 64 and sha256(raw).hexdigest() == MANIFEST_SHA256,
            'CI manifest differs from its frozen byte hash')
    return validate_manifest(json.loads(raw))


def validate_paths(paths, manifest, *, root=ROOT):
    require(all(type(path) is str for path in paths), 'Changed paths must be strings')
    require(set(paths) <= set(manifest['approved_paths']), 'Change outside reviewed runtime scope')
    for name in paths:
        path = root / name
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
                'Changed path is deleted, non-file, symlink or outside repository')


def validate_event(head):
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        require(os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Curaua CI requires push event')
        require(os.environ.get('GITHUB_REF') == BRANCH_REF, 'Curaua CI requires exact experimental branch')
        require(os.environ.get('GITHUB_SHA') == head, 'Checkout SHA differs from Actions metadata')
        require(not git('status', '--porcelain', '--untracked-files=normal'), 'Hosted checkout is not clean')


def table_rows(graphs):
    return {'identity': graphs['materials']['identities'], 'grade': graphs['materials']['grades'],
            'state': graphs['materials']['records'], 'property': graphs['properties']['records'],
            'source': graphs['sources']['records']}


def validate_append(candidate, before, current):
    expected = deepcopy(before)
    for name, fields in (('materials', ('identities', 'grades', 'records')),
                         ('properties', ('records',)), ('sources', ('records',))):
        for field in fields:
            old = expected[name][field]
            added = candidate[name][field]
            require(len({row['id'] for row in added}) == len(added), 'Duplicate candidate ID')
            require(not ({row['id'] for row in old} & {row['id'] for row in added}), 'Candidate reuses an existing ID')
            old.extend(sorted(deepcopy(added), key=lambda row: row['id']))
    require(current == expected, 'Runtime is not the complete exact append to the unchanged predecessor')
    require({name: len(rows) for name, rows in table_rows(candidate).items()} == DELTA_COUNTS,
            'Candidate delta differs')
    require({name: len(rows) for name, rows in table_rows(current).items()} == GRAPH_COUNTS,
            'Runtime graph counts differ')
    require(dict(Counter(row['category'] for row in current['materials']['identities'])) == PRIMARY_COUNTS,
            'Primary category counts differ')


def installation_payload(manifest=None):
    manifest = load_manifest() if manifest is None else manifest
    packet_raw = (ROOT / BATCH / 'prepared-packet.json').read_bytes()
    require(sha256(packet_raw).hexdigest() == PACKET_SHA256, 'Reviewed packet changed')
    packet = json.loads(packet_raw)
    before, current = {}, {}
    for key, filename in (('materials', 'materials.json'), ('properties', 'reference_properties.json'), ('sources', 'sources.json')):
        path = 'materials_boundaries/data/' + filename
        old, new = git('show', BASE_COMMIT + ':' + path), (ROOT / path).read_bytes()
        require(sha256(old).hexdigest() == packet['input']['baseline_sha256'][filename[:-5]], 'Baseline resource changed')
        require(sha256(new).hexdigest() == manifest['resource_hashes'][filename], 'Runtime resource hash changed')
        before[key], current[key] = json.loads(old), json.loads(new)
    validate_append(packet['catalogs'], before, current)
    for name in CANDIDATE_ARTIFACTS + PROTECTED_PATHS:
        require((ROOT / name).read_bytes() == git('show', BASE_COMMIT + ':' + name), 'Protected original changed: ' + name)
    for name in git('ls-tree', '-r', '--name-only', BASE_COMMIT, '--', 'tests/fixtures').decode().splitlines():
        require((ROOT / name).read_bytes() == git('show', BASE_COMMIT + ':' + name), 'Historical fixture changed: ' + name)
    for name in git('ls-tree', '-r', '--name-only', BASE_COMMIT, '--', 'scripts').decode().splitlines():
        if Path(name).name.startswith('run_') and name.endswith('_ci.py'):
            require((ROOT / name).read_bytes() == git('show', BASE_COMMIT + ':' + name),
                    'Existing CI runner changed: ' + name)
    integration = json.loads((ROOT / BATCH / 'integration.json').read_bytes())
    require(integration['released_main_count'] == 1081 and integration['status_adjustments'] == [], 'Main or review status changed')
    require(integration['baseline_sha256'] == packet['input']['baseline_sha256'], 'Integration baseline changed')
    require(integration['batches'] == [{'id': 'czlonka-curaua-20261025', 'candidate_commit': BASE_COMMIT,
                'packet': {'path': 'prepared-packet.json', 'sha256': PACKET_SHA256}}], 'Integration packet binding changed')
    require(packet['report']['formal_admitted_delta'] == packet['review']['formal_admitted_delta'] == 0,
            'Candidate history was rewritten as admission')
    pin = ROOT / 'experimental/platform/query-service/materials_query/pins/legacy_baseline.json'
    require(sha256(pin.read_bytes()).hexdigest() == manifest['query_baseline_sha256'], 'Query snapshot pin changed')
    excluded = json.loads((ROOT / PROTECTED_PATHS[-2]).read_bytes())
    require(len(excluded['records']) == 62, 'Unadmitted computed examples changed')
    return {'candidate': packet['catalogs'], 'resource_hashes': manifest['resource_hashes'],
            'graph_counts': GRAPH_COUNTS, 'delta_counts': DELTA_COUNTS, 'primary_counts': PRIMARY_COUNTS,
            'formal_counts': FORMAL_COUNTS, 'query_baseline': manifest['query_baseline_sha256'],
            'packages': [package for _, _, package in PACKAGES], 'excluded_examples': 62, 'released_main_count': 1081}


def validate_workflow(manifest):
    require((ROOT / '.github/workflows/ci.yml').read_bytes() == git('show', BASE_COMMIT + ':.github/workflows/ci.yml'),
            'Complete core partition workflow must remain byte-identical')
    raw = (ROOT / WORKFLOW_PATH).read_bytes()
    require(sha256(raw).hexdigest() == manifest['workflow_sha256'], 'Curaua workflow differs from exact reviewed image')


def validate_scope():
    manifest = load_manifest()
    head = git('rev-parse', 'HEAD').decode().strip()
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE_COMMIT, head], cwd=ROOT, check=True, timeout=60)
    validate_event(head)
    paths = set(git('diff', '--name-only', '--no-renames', BASE_COMMIT, '--').decode().splitlines())
    paths.update(x for x in git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0') if x)
    validate_paths(paths, manifest)
    validate_workflow(manifest)
    installation_payload(manifest)
    print('CURAUA_SCOPE ' + json.dumps({'head': head, 'baseline': BASE_COMMIT,
          'changed_files': sorted(paths), 'general_workflow_unchanged': True, 'candidate_packet_sha256': PACKET_SHA256,
          'graph_counts': GRAPH_COUNTS, 'formal_counts': FORMAL_COUNTS}, sort_keys=True), flush=True)


class ExactResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started_ids, self.passed_ids = [], []

    def startTest(self, test):
        self.started_ids.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)


def validate_result(ids, result):
    require(ids and len(ids) == len(set(ids)), 'Empty or duplicate discovered IDs')
    require(result.testsRun == len(ids) and result.started_ids == ids and result.passed_ids == ids,
            'Discovered, started and passed IDs differ')
    require(result.wasSuccessful() and not (result.failures or result.errors or result.skipped
            or result.expectedFailures or result.unexpectedSuccesses), 'Failure, fixture error, skip or unexpected outcome')
    return {'passed': len(ids), 'failed': 0, 'errors': 0, 'skipped': 0, 'test_ids': ids}


def validate_inventory(group, ids, modules):
    require(sorted(ids) == group['ids'] and len(ids) == len(set(ids)) == group['count'], 'Exact method inventory differs')
    require(fingerprint(ids) == group['sha256'], 'Inventory digest differs')
    require(sorted(modules) == group['modules'], 'Whole-module inventory differs')


def load_group(name, installed=False, manifest=None):
    manifest = load_manifest() if manifest is None else manifest
    group = manifest['installed_groups' if installed else 'source_groups'][name]
    directory = ROOT / group['directory']
    available = sorted(path.stem for path in directory.glob('test*.py'))
    modules = group['modules'] if group.get('selection') == 'explicit_whole_modules' else available
    if group.get('selection') == 'explicit_whole_modules':
        require(set(modules) <= set(available), 'Selected source module is missing')
    else:
        require(modules == group['modules'], 'Complete group module inventory differs')
    sys.path.insert(0, str(directory))
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromName(module) for module in modules)
    require(not loader.errors, 'Test loading errors: ' + '\n'.join(loader.errors))
    for module in modules:
        loaded = sys.modules.get(module)
        require(loaded is not None and Path(loaded.__file__).resolve() == (directory / (module + '.py')).resolve(),
                'Test module imported from an unexpected path')
    ids = list(test_ids(suite))
    validate_inventory(group, ids, modules)
    return suite, ids


def run_group(name, installed=False):
    install_offline_guard()
    if installed:
        require(sys.prefix != sys.base_prefix and str(ROOT) not in sys.path, 'Installed group imports source checkout')
        installed_origins()
    else:
        for path in (ROOT, ROOT / 'tests'):
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
    suite, ids = load_group(name, installed)
    print('DISCOVERED ' + json.dumps({'group': name, 'installed': installed, 'test_ids': ids}, sort_keys=True), flush=True)
    result = unittest.TextTestRunner(verbosity=2, resultclass=ExactResult).run(suite)
    summary = validate_result(ids, result)
    if installed:
        installed_origins()
    print('CURAUA_COMPLETE ' + json.dumps({'group': name, 'installed': installed,
          'full_core_run': False, **summary}, sort_keys=True), flush=True)
    return summary


INSTALLED_SMOKE = r'''
from collections import Counter
from contextlib import redirect_stdout
from hashlib import sha256
from importlib.resources import files
import importlib, io, json, sys
from pathlib import Path

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

expected = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
for name in expected['packages']:
    module = importlib.import_module(name)
    require(Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), 'Checkout package imported')
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.cli import main
from materials_project_catalog.catalog import formal_project_catalog
from materials_query.computed_registry import baseline_digest
for name, digest in expected['resource_hashes'].items():
    require(sha256(files('materials_boundaries').joinpath('data', name).read_bytes()).hexdigest() == digest,
            'Installed resource bytes differ: ' + name)
materials, properties, sources = (read_catalog(n) for n in ('materials', 'reference_properties', 'sources'))
tables = {'identity': materials['identities'], 'grade': materials['grades'], 'state': materials['records'],
          'property': properties['records'], 'source': sources['records']}
candidate = expected['candidate']
frozen = {'identity': candidate['materials']['identities'], 'grade': candidate['materials']['grades'],
          'state': candidate['materials']['records'], 'property': candidate['properties']['records'],
          'source': candidate['sources']['records']}
require({key: len(rows) for key, rows in tables.items()} == expected['graph_counts'], 'Installed graph counts differ')
require(dict(Counter(row['category'] for row in tables['identity'])) == expected['primary_counts'], 'Installed categories differ')
for key, rows in frozen.items():
    for row in rows:
        require([x for x in tables[key] if x['id'] == row['id']] == [row], 'Installed complete candidate object differs')
facts = (('cf0p1', 'CF 0.1', '0.1', '38.4', '0.4', 'C'),
         ('cf0p5', 'CF 0.5', '0.5', '37.9', '0.6', 'B'),
         ('cf1', 'CF 1', '1', '37.6', '0.4', 'A'))
require(len(frozen['identity']) == len(frozen['state']) == len(frozen['property']) == 3 and not frozen['grade'],
        'States or observations inflate identity count')
require(frozen['source'][0]['authors'] == ['Sylwia Cz\u0142onka', 'Eduardo Fischer Kerche', 'Roberta Motta Neves',
        'Anna Str\u0105kowska', 'Krzysztof Strzelec'], 'Exact five-author attribution changed')
identities = {r['id']: r for r in frozen['identity']}
states = {r['id']: r for r in frozen['state']}
props = {r['id']: r for r in frozen['property']}
outputs = 0
for suffix, label, loading, number, cv, letter in facts:
    identity = identities['mat_czlonka2021_curaua_' + suffix]
    state = states['state_czlonka2021_curaua_' + suffix + '_free_rise']
    prop = props['refprop_czlonka2021_curaua_' + suffix + '_apparent_density']
    require(identity['category'] == 'composite' and state['grade_id'] is None
            and state['identity_id'] == identity['id'] and state['property_ids'] == [prop['id']]
            and prop['material_state_id'] == state['id'], 'Candidate joins changed')
    require(state['source_designation'] == label and loading + ' wt%' in state['state']['composition_or_purity']['text'],
            'Literal source label or nominal loading changed')
    require(prop['reported_value']['number'] == prop['reported_value']['value_text'] == number
            and prop['reported_value']['unit_code'] == 'kg/m^3', 'Apparent density value or unit changed')
    require(prop['density_basis'] == 'apparent' and prop['summary_statistic'] == 'reported_mean'
            and prop['sample_count']['value'] == 10 and prop['sample_count']['relation'] == 'exact'
            and 'ISO 845' in prop['conditions']['test_standard']['text'], 'Density method or sample scope changed')
    require(prop['uncertainty'] is None and cv in prop['uncertainty_note']
            and 'coefficient of variance' in prop['uncertainty_note']
            and letter in prop['scope_note'], 'Literal variation observation changed or SD inferred')
    require(prop['conditions']['temperature']['text'] is None and prop['conditions']['conditioning']['text'] is None,
            'Density conditions inferred')
    discrepancy = json.dumps(prop['source_discrepancies'])
    require('24' in discrepancy and '7' in discrepancy and 'age' in discrepancy, 'Density age caveat missing')
    require(prop['evaluation_support'] == 'catalog_only' and not prop['universal_bound']
            and not prop['engineering_allowable'] and not prop['verification']['independent_scientific_review']
            and not prop['verification']['raw_data_reanalysis'], 'Scientific assertions changed')
    selected = query_catalog('reference-properties', record_id=prop['id'])
    for language in ('en', 'zh', 'ja', 'de'):
        for flag in ('--json', '--text'):
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(['catalog', 'reference-properties', '--id', prop['id'], '--lang', language, flag])
            text = output.getvalue()
            require(code == 0 and '[missing:' not in text, 'Installed CLI failed')
            if flag == '--json':
                require(json.loads(text) == selected, 'Complete JSON differs')
            else:
                require(number in text and prop['uncertainty_note'] in text, 'Text value or caveat missing')
            outputs += 1
require(outputs == 24, 'Expected 24 CLI outputs, not unique materials')
formal = formal_project_catalog()
require(formal['counts'] == expected['formal_counts'], 'Installed formal boundary changed')
for row in frozen['identity']:
    require(len([x for x in formal['records'] if x['partition'] == 'legacy-source-qualified'
                 and x['identity']['id'] == row['id']]) == 1, 'Identity contribution duplicated')
require(baseline_digest() == expected['query_baseline'], 'Installed query pin differs')
print(json.dumps({'fresh_install': True, 'graph_counts': expected['graph_counts'],
      'formal_counts': formal['counts'], 'selected_cli_outputs': outputs,
      'cli_check': 'full JSON equality and text value/caveat checks'}))
'''


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob('*.whl')), 'Offline dependencies missing')
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix='curaua-installed-') as temporary:
        work = Path(temporary)
        runtime = work / 'runtime'
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(runtime)
        python = runtime / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        run([python, '-I', '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps', '--find-links', dependency_dir,
             '-r', ROOT / 'experimental/platform/requirements-lock.txt',
             '-r', ROOT / 'experimental/platform/ci/projection-requirements.txt'], cwd=work, env=env)
        run([python, '-I', '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps', *wheels], cwd=work, env=env)
        run([python, '-I', '-m', 'pip', 'check'], cwd=work, env=env)
        expected = work / 'expected.json'
        expected.write_text(json.dumps(installation_payload()), encoding='utf-8')
        smoke = work / 'smoke.py'
        smoke.write_text(inspect.getsource(install_offline_guard) + '\ninstall_offline_guard()\n' + INSTALLED_SMOKE, encoding='utf-8')
        run([python, '-I', smoke, expected], cwd=work, env=env)
        guard = work / 'sitecustomize.py'
        guard.write_text(inspect.getsource(install_offline_guard) + '\ninstall_offline_guard()\n', encoding='utf-8')
        env['PYTHONPATH'] = str(work)
        for group in INSTALLED_GROUPS:
            run([python, '-I', '-B', Path(__file__).resolve(), '--installed-group', group], cwd=work, env=env)
        run([python, '-B', ROOT / 'experimental/platform/ci/check_offline.py', 'installed-smoke'], cwd=work, env=env)
    print('CURAUA_INSTALLED_COMPLETE all eight complete groups and independent CLI/API smoke passed; '
          'no claim about full core, live services, deployment or main.', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--validate-scope', action='store_true')
    mode.add_argument('--validate-inventory', action='store_true')
    mode.add_argument('--source-tests', action='store_true')
    mode.add_argument('--source-group', choices=SOURCE_GROUPS)
    mode.add_argument('--installed-group', choices=INSTALLED_GROUPS)
    mode.add_argument('--wheel-dir', type=Path)
    parser.add_argument('--dependency-dir', type=Path)
    args = parser.parse_args(argv)
    if args.dependency_dir and not args.wheel_dir:
        parser.error('--dependency-dir requires --wheel-dir')
    if args.installed_group:
        run_group(args.installed_group, installed=True)
        return
    if args.source_group:
        run_group(args.source_group)
        return
    validate_scope()
    if args.source_tests:
        for group in SOURCE_GROUPS:
            run([sys.executable, '-X', 'utf8', Path(__file__).resolve(), '--source-group', group], cwd=ROOT, env=clean_env())
    elif args.validate_inventory:
        for path in (ROOT, ROOT / 'tests'):
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
        for name in SOURCE_GROUPS:
            _, ids = load_group(name)
            print('INVENTORY ' + json.dumps({'group': name, 'count': len(ids), 'tests_executed': 0}), flush=True)
    elif args.wheel_dir:
        require(args.dependency_dir is not None, '--wheel-dir requires --dependency-dir')
        check_installed(args.wheel_dir.resolve(), args.dependency_dir.resolve())


if __name__ == '__main__':
    main()
