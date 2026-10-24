#!/usr/bin/env python3
"""Explicit, exact-inventory execution of the package-less replay test suites.

This additional workflow does not disable or replace any existing CI job.
A future push also triggers general CI, with full-history generic checkouts.
This runner claims neither full core nor installed-package coverage.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '826333c73a420b7d254c469d9f6f65155983cde1'
BRANCH_REF = 'refs/heads/experiment/test-history-replay-tian-20261024'
DIRECTORIES = ('tests/history_replay', 'tests/history_replay_latest')
EXPLICIT_IDS = (
    'test_kapoor_phosphate_preservation.KapoorPhosphatePreservationTests.test_six_finite_descriptors_preserve_one_packet_and_runtime_id_order',
    'test_tian_nano_ti_preservation.TianNanoTiPreservationTests.test_single_descriptor_preserves_exact_packet_and_runtime_order',
    'test_tian_nano_ti_ci.TianNanoTiCITests.test_complete_inventories_preserve_every_predecessor_and_new_test',
    'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_targeted_inventory_is_all_cases_from_exact_complete_modules',
    'test_tian_nano_ti_ci.TianNanoTiCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated',
)
MANIFEST_PATH = 'tests/history_replay_latest/ci-inventory.json'
INVENTORY_SHA256 = 'fe852dfb4c050813f640cd3cf2e8d5b1d162b5eb0508251e509a4c2d3c61b7fc'
WORKFLOW_PATH = '.github/workflows/history-replay-latest.yml'
WORKFLOW = '''name: history-replay-latest
on:
  push:
    branches: [experiment/test-history-replay-tian-20261024]
permissions:
  contents: read
jobs:
  replay-targeted:
    runs-on: ${{ matrix.os }}
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: ubuntu-latest
            python-version: '3.11'
          - os: windows-latest
            python-version: '3.12'
    env:
      PYTHONUTF8: '1'
      PYTHONDONTWRITEBYTECODE: '1'
    steps:
      - run: git config --global core.autocrlf false
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install -e '.[dev]'
      - run: python scripts/run_history_replay_latest_ci.py --validate-inventory
      - run: python scripts/run_history_replay_latest_ci.py --tests
'''


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True,
                          capture_output=True, timeout=30).stdout


def unique_keys(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'Duplicate replay CI manifest key')
        value[key] = item
    return value


def fingerprint(ids):
    return sha256(('\n'.join(sorted(ids)) + '\n').encode('utf-8')).hexdigest()


def validate_manifest(manifest):
    require(type(manifest) is dict and set(manifest) == {
        'schema_version', 'baseline_commit', 'directories', 'explicit_ids',
        'ids', 'count', 'fingerprint'}, 'Unexpected replay CI manifest shape')
    require(type(manifest['schema_version']) is int and manifest['schema_version'] == 1,
            'Unknown replay CI manifest version')
    require(manifest['baseline_commit'] == BASE_COMMIT, 'Unexpected replay CI baseline')
    require(manifest['directories'] == list(DIRECTORIES), 'Replay discovery directories changed')
    require(manifest['explicit_ids'] == list(EXPLICIT_IDS), 'Explicit historical checks changed')
    ids = manifest['ids']
    require(type(ids) is list and ids and all(type(i) is str for i in ids),
            'Invalid replay method inventory')
    require(ids == sorted(set(ids)), 'Replay inventory must be unique and sorted')
    require(type(manifest['count']) is int and manifest['count'] == len(ids),
            'Replay method count differs from its frozen inventory')
    require(manifest['fingerprint'] == fingerprint(ids), 'Replay ID fingerprint differs')
    require(set(EXPLICIT_IDS).issubset(ids), 'A required historical check is missing')
    return manifest


def load_manifest():
    raw = (ROOT / MANIFEST_PATH).read_bytes()
    require(sha256(raw).hexdigest() == INVENTORY_SHA256, 'Unreviewed replay CI inventory bytes')
    return validate_manifest(json.loads(raw, object_pairs_hook=unique_keys))


def test_ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_ids(item)
        else:
            yield item.id()


def load_suite():
    # Each directory needs explicit discovery: ordinary core discovery does not
    # descend into these package-less directories. No __init__.py is added.
    for path in (ROOT, ROOT / 'tests'):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    suite = unittest.TestSuite()
    for relative in DIRECTORIES:
        path = ROOT / relative
        require(path.is_dir() and not (path / '__init__.py').exists(),
                'Replay directory must retain its explicit-discovery contract')
        loader = unittest.TestLoader()
        selected = loader.discover(str(path), pattern='test_*.py')
        require(not loader.errors, 'Replay directory test loading failed')
        found = list(test_ids(selected))
        require(found, 'Replay discovery found no tests')
        for identifier in found:
            module = sys.modules.get(identifier.split('.')[0])
            require(module is not None and Path(module.__file__).resolve().parent == path.resolve(),
                    'Replay method loaded from an unexpected directory')
        suite.addTests(selected)
    loader = unittest.TestLoader()
    historical = loader.loadTestsFromNames(EXPLICIT_IDS)
    require(not loader.errors and list(test_ids(historical)) == list(EXPLICIT_IDS),
            'Explicit historical test loading changed')
    suite.addTests(historical)
    return suite


def validate_discovery(ids, manifest):
    require(len(ids) == len(set(ids)) == manifest['count'], 'Duplicate or missing discovered methods')
    require(sorted(ids) == manifest['ids'] and fingerprint(ids) == manifest['fingerprint'],
            'Discovered methods differ from the exact frozen replay inventory')


def validate_context():
    require((ROOT / WORKFLOW_PATH).read_bytes() == WORKFLOW.encode('utf-8'),
            'Replay workflow differs from its exact execution contract')
    require(general_workflow_predecessor((ROOT / '.github/workflows/ci.yml').read_bytes()) ==
            git('show', BASE_COMMIT + ':.github/workflows/ci.yml'),
            'General CI must recover its exact predecessor')
    head = git('rev-parse', 'HEAD').decode().strip()
    git('merge-base', '--is-ancestor', BASE_COMMIT, head)
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        require(os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Replay CI requires a push event')
        require(os.environ.get('GITHUB_REF') == BRANCH_REF, 'Replay CI requires its exact branch')
        require(os.environ.get('GITHUB_SHA') == head, 'Replay checkout differs from the pushed SHA')
        require(not git('status', '--porcelain', '--untracked-files=normal'),
                'Hosted replay checkout must be clean')


def general_workflow_predecessor(raw):
    """Require the corrected whole image before testing historical equality."""
    if str(ROOT / 'tests') not in sys.path:
        sys.path.insert(0, str(ROOT / 'tests'))
    from replay_checkout_history import code_ledger, project_checkout_file
    path = '.github/workflows/ci.yml'
    entry = code_ledger()['updates'][path]
    require(type(raw) is bytes and sha256(raw).hexdigest() == entry['sha256'],
            'General CI requires the exact full-history checkout correction')
    return project_checkout_file(path, raw)


class ExactResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started_ids = []
        self.passed_ids = []

    def startTest(self, test):
        self.started_ids.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)


def validate_result(result, expected):
    require(type(result.testsRun) is int and result.testsRun == len(expected),
            'Replay run did not complete its selected method count')
    require(result.started_ids == expected and result.passed_ids == expected,
            'Replay started or passed IDs differ from discovery')
    require(result.wasSuccessful() and not (result.failures or result.errors or result.skipped
            or result.expectedFailures or result.unexpectedSuccesses),
            'Replay failure, error, skip, or unexpected result')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--validate-inventory', action='store_true')
    mode.add_argument('--tests', action='store_true')
    args = parser.parse_args(argv)
    validate_context()
    manifest = load_manifest()
    suite = load_suite()
    ids = list(test_ids(suite))
    validate_discovery(ids, manifest)
    if args.validate_inventory:
        print(json.dumps({'status': 'inventory-validated', 'count': len(ids),
                          'fingerprint': fingerprint(ids), 'tests_executed': 0}))
        return 0
    result = unittest.TextTestRunner(verbosity=2, resultclass=ExactResult).run(suite)
    validate_result(result, ids)
    print('HISTORY_REPLAY_LATEST_COMPLETE ' + json.dumps({
        'coverage': 'explicit-replay-directories-and-five-historical-methods',
        'passed': len(ids), 'passed_ids': ids, 'failures': 0, 'errors': 0, 'skipped': 0,
        'fingerprint': fingerprint(ids), 'full_core_run': False, 'installed_package_run': False,
        'existing_general_workflow': 'full-history generic checkouts; all existing job conditions preserved; generic jobs remain eligible'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
