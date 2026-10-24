#!/usr/bin/env python3
"""Run complete-module core partitions and verify their complete CI union.

This runner changes process/global ordering across partitions. Inside each
partition it filters canonical unittest discovery without splitting modules or
classes. Receipts describe actual outcomes; absent or cancelled work never
becomes a skip. The separate replay inventory is not part of this core manifest.
"""
import argparse
import ast
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = 'bf1c7a86068c37c2733ac4d25c268144090f9aad'
MANIFEST_PATH = 'tests/core_partition/manifest.json'
MANIFEST_SHA256 = '7f12617c6e56d426368940dc8d517bb04e2201435ee841c62376a28244882f95'
MANIFEST_CONTENT_SHA256 = 'f6ee629dc252d8027e68ede24a5529797bcfc3d95f6145b497a5fed97d8e40d4'
ROOT_INVENTORY_SHA256 = '19a735217c29533c1137a6cfd95b2b58cf88e8cf649848e41012c510434446f7'
PYTHON_VERSIONS = ('3.11', '3.12')
PARTITIONS = (0, 1, 2, 3)
PARTITION_METHOD_COUNTS = (459, 492, 417, 519)
PARTITION_MODULE_COUNTS = (39, 36, 30, 42)
RUN_JOB = 'unit-and-schema'
AGGREGATE_JOB = 'unit-and-schema-aggregate'
CONTEXT_KEYS = frozenset({
    'sha', 'tree', 'run_id', 'run_attempt', 'python_version',
    'python_full_version', 'platform', 'manifest_sha256', 'runner_sha256',
    'wood_review_dossier_present',
})
RECEIPT_KEYS = frozenset({
    'schema_version', 'context', 'partition', 'expected_ids', 'declared_ids',
    'discovered_ids', 'started_ids', 'completed', 'fixture_errors',
    'subtest_errors', 'protocol_errors', 'terminal', 'terminal_status',
    'journal_sha256',
})


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique_keys)


def fingerprint(ids):
    return sha256(('\n'.join(sorted(ids)) + '\n').encode('utf-8')).hexdigest()


def manifest_ids(manifest):
    return [identifier for module in manifest['modules']
            for identifier in module['test_ids']]


def partition_ids(manifest, partition):
    require(type(partition) is int and partition in PARTITIONS, 'Unknown partition')
    return [identifier for module in manifest['modules']
            if module['partition'] == partition for identifier in module['test_ids']]


def validate_manifest(manifest):
    keys = {
        'schema_version', 'baseline_commit', 'root_inventory_sha256',
        'module_count', 'test_count', 'partition_count',
        'partition_method_counts', 'partition_module_counts',
        'partition_algorithm', 'modules', 'skip_rules', 'canonical_ids',
    }
    require(type(manifest) is dict and set(manifest) == keys, 'Unexpected manifest shape')
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    require(sha256(canonical).hexdigest() == MANIFEST_CONTENT_SHA256,
            'Frozen manifest content changed')
    require(type(manifest['schema_version']) is int and manifest['schema_version'] == 1,
            'Unknown manifest version')
    require(manifest['baseline_commit'] == BASELINE_COMMIT, 'Wrong frozen baseline')
    for key, expected in (('module_count', 147), ('test_count', 1887), ('partition_count', 4)):
        require(type(manifest[key]) is int and manifest[key] == expected, 'Wrong ' + key)
    require(manifest['root_inventory_sha256'] == ROOT_INVENTORY_SHA256,
            'Wrong complete core fingerprint')
    require(manifest['partition_method_counts'] == list(PARTITION_METHOD_COUNTS)
            and manifest['partition_module_counts'] == list(PARTITION_MODULE_COUNTS),
            'Frozen partition counts changed')
    require(manifest['partition_algorithm'] == 'sha256_utf8_module_name_big_endian_modulo_4',
            'Frozen partition algorithm changed')
    modules = manifest['modules']
    require(type(modules) is list and len(modules) == 147, 'Missing or extra modules')
    names = []
    for module in modules:
        require(type(module) is dict and set(module) == {'name', 'path', 'partition', 'test_ids'},
                'Unexpected module entry')
        name = module['name']
        require(type(name) is str and re.fullmatch(r'test\w+', name), 'Invalid module name')
        require(module['path'] == 'tests/' + name + '.py', 'Wrong module source path')
        expected_partition = int.from_bytes(sha256(name.encode('utf-8')).digest(), 'big') % 4
        require(type(module['partition']) is int and module['partition'] == expected_partition,
                'Module partition changed')
        ids = module['test_ids']
        require(type(ids) is list and ids and all(type(i) is str and i.startswith(name + '.') for i in ids),
                'Invalid module methods')
        require(ids == sorted(set(ids)), 'Module IDs are not unique canonical order')
        names.append(name)
    require(names == sorted(set(names)), 'Module order or uniqueness changed')
    ids = manifest_ids(manifest)
    require(len(ids) == len(set(ids)) == 1887 and ids == manifest['canonical_ids'],
            'Full canonical ID list changed')
    require(fingerprint(ids) == ROOT_INVENTORY_SHA256, 'Full inventory differs from reviewed IDs')
    for partition in PARTITIONS:
        require(len(partition_ids(manifest, partition)) == PARTITION_METHOD_COUNTS[partition],
                'Partition method count changed')
        require(sum(m['partition'] == partition for m in modules) == PARTITION_MODULE_COUNTS[partition],
                'Partition module count changed')
    flattened = [identifier for partition in PARTITIONS for identifier in partition_ids(manifest, partition)]
    require(len(flattened) == len(set(flattened)) and set(flattened) == set(ids),
            'Partitions do not form a disjoint complete union')
    rules = manifest['skip_rules']
    require(type(rules) is list and len(rules) == 2, 'Unexpected skip policy')
    expected_rules = {
        'native_windows_absent': (17, 'requires actual native Windows on local NTFS'),
        'wood_dossier_absent': (1, 'external frozen source-cache integration is opt-in'),
    }
    conditions, skip_ids = [], []
    for rule in rules:
        require(type(rule) is dict and set(rule) == {'condition', 'test_ids', 'reason'},
                'Unexpected skip rule shape')
        condition = rule['condition']
        require(condition in expected_rules, 'Unknown skip condition')
        count, reason = expected_rules[condition]
        require(rule['reason'] == reason and type(rule['test_ids']) is list
                and rule['test_ids'] == sorted(set(rule['test_ids']))
                and len(rule['test_ids']) == count and set(rule['test_ids']).issubset(ids),
                'Skip policy IDs, count or reason changed')
        conditions.append(condition)
        skip_ids.extend(rule['test_ids'])
    require(set(conditions) == set(expected_rules) and len(skip_ids) == len(set(skip_ids)),
            'Duplicate skip condition or ID')
    return manifest


def load_manifest(root=ROOT):
    path = Path(root) / MANIFEST_PATH
    require(path.is_file() and not path.is_symlink(), 'Missing or linked frozen manifest')
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == MANIFEST_SHA256, 'Unreviewed manifest bytes')
    return validate_manifest(json.loads(raw, object_pairs_hook=unique_keys))


def declared_inventory(root=ROOT):
    """Independently declare IDs from source, without importing/executing tests."""
    entries = []
    for path in sorted((Path(root) / 'tests').glob('test*.py')):
        require(path.is_file() and not path.is_symlink(), 'Linked or missing root test module')
        tree = ast.parse(path.read_bytes(), filename=path.name)
        require(not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name == 'load_tests' for node in tree.body),
                'Unreviewed module load_tests hook')
        classes = sorted((node for node in tree.body if isinstance(node, ast.ClassDef)),
                         key=lambda node: node.name)
        for node in classes:
            for method in sorted((method for method in node.body
                                  if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                                  and method.name.startswith('test')), key=lambda method: method.name):
                entries.append(path.stem + '.' + node.name + '.' + method.name)
    return entries


def test_ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_ids(item)
        else:
            yield item.id()


def validate_declarations(manifest, root=ROOT):
    root = Path(root).resolve()
    paths = sorted(path.relative_to(root).as_posix() for path in (root / 'tests').glob('test*.py'))
    require(paths == [module['path'] for module in manifest['modules']],
            'Root test module set changed, including empty modules')
    ids = declared_inventory(root)
    require(ids == manifest_ids(manifest), 'Independent declarations differ from frozen IDs')
    return ids


def discover_inventory(manifest, root=ROOT):
    validate_manifest(manifest)
    root = Path(root).resolve()
    expected = manifest_ids(manifest)
    validate_declarations(manifest, root)
    for path in (root, root / 'tests'):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    loader = unittest.TestLoader()
    suite = loader.discover(str(root / 'tests'), pattern='test*.py', top_level_dir=str(root / 'tests'))
    require(not loader.errors, 'Full unittest discovery reported loading errors')
    ids = list(test_ids(suite))
    require(ids == expected and len(ids) == len(set(ids)), 'Canonical discovery differs from frozen IDs')
    for module in manifest['modules']:
        loaded = sys.modules.get(module['name'])
        require(loaded is not None and Path(loaded.__file__).resolve() == root / module['path'],
                'Test module was imported from an unexpected source')
    return suite, ids


def select_partition(suite, manifest, partition):
    """Filter canonical discovery, retaining suite nesting and whole modules.

    The production caller has validated the complete frozen manifest and suite.
    This pure filter also permits tiny manifest-shaped fixtures in contract tests.
    """
    require(list(test_ids(suite)) == manifest_ids(manifest), 'Cannot filter noncanonical discovery')
    selected_ids = partition_ids(manifest, partition)
    wanted = set(selected_ids)

    def filtered(container):
        require(type(container) is unittest.TestSuite, 'Unreviewed custom suite behavior')
        result = unittest.TestSuite()
        for item in container:
            if isinstance(item, unittest.TestSuite):
                nested = filtered(item)
                if nested.countTestCases():
                    result.addTest(nested)
            elif item.id() in wanted:
                result.addTest(item)
        return result

    selected = filtered(suite)
    require(list(test_ids(selected)) == selected_ids, 'Partition lost canonical relative order')
    return selected


def skip_contract(manifest, dossier_present):
    require(type(dossier_present) is bool, 'Dossier policy must be a boolean, never a path')
    result = {}
    for rule in manifest['skip_rules']:
        if rule['condition'] == 'native_windows_absent' or not dossier_present:
            for identifier in rule['test_ids']:
                require(identifier not in result, 'Duplicate policy ID')
                result[identifier] = rule['reason']
    return result


def validate_context_data(context):
    require(type(context) is dict and set(context) == CONTEXT_KEYS, 'Unexpected receipt context')
    for key in ('sha', 'tree'):
        require(type(context[key]) is str and re.fullmatch(r'[0-9a-f]{40}', context[key]), 'Invalid ' + key)
    for key in ('run_id', 'run_attempt'):
        require(type(context[key]) is str and re.fullmatch(r'[1-9][0-9]*', context[key]), 'Invalid ' + key)
    require(context['python_version'] in PYTHON_VERSIONS, 'Unsupported Python version')
    require(type(context['python_full_version']) is str and re.fullmatch(
        re.escape(context['python_version']) + r'\.[0-9]+', context['python_full_version']),
        'Python version metadata disagrees')
    require(context['platform'] == {'system': 'Linux', 'os_name': 'posix',
                                    'sys_platform': 'linux', 'machine': 'x86_64'},
            'General core receipts require the actual Linux runner platform')
    for key in ('manifest_sha256', 'runner_sha256'):
        require(type(context[key]) is str and re.fullmatch(r'[0-9a-f]{64}', context[key]),
                'Invalid ' + key)
    require(context['manifest_sha256'] == MANIFEST_SHA256, 'Wrong receipt manifest bytes')
    require(type(context['wood_review_dossier_present']) is bool, 'Invalid environment skip profile')
    return context


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True,
                          timeout=30).stdout


def production_context(root=ROOT, *, role, allowed_untracked=()):
    root = Path(root).resolve()
    require(os.environ.get('GITHUB_ACTIONS') == 'true', 'Production receipts require GitHub Actions')
    require(role in ('run', 'aggregate'), 'Unknown receipt role')
    expected_job = RUN_JOB if role == 'run' else AGGREGATE_JOB
    require(os.environ.get('GITHUB_JOB') == expected_job, 'Unexpected workflow job')
    head = git(root, 'rev-parse', 'HEAD').decode('ascii').strip()
    tree = git(root, 'rev-parse', 'HEAD^{tree}').decode('ascii').strip()
    require(os.environ.get('GITHUB_SHA') == head, 'Checkout differs from GitHub SHA')
    git(root, 'merge-base', '--is-ancestor', BASELINE_COMMIT, head)
    git(root, 'diff', '--exit-code', 'HEAD', '--')
    allowed = [Path(path).resolve() for path in allowed_untracked]
    for path in allowed:
        require(path != root and path.is_relative_to(root), 'Artifacts must stay inside the checkout')
    untracked = git(root, 'ls-files', '--others', '--exclude-standard', '-z').decode('utf-8').split('\0')
    for name in filter(None, untracked):
        path = (root / name).resolve()
        require(any(path == directory or path.is_relative_to(directory) for directory in allowed),
                'Untracked checkout input outside receipt artifacts: ' + name)
    for relative in (MANIFEST_PATH, 'scripts/run_full_core_partition_ci.py'):
        require(git(root, 'show', head + ':' + relative) == (root / relative).read_bytes(),
                'Receipt input differs from committed tree: ' + relative)
    result = {
        'sha': head, 'tree': tree,
        'run_id': os.environ.get('GITHUB_RUN_ID'),
        'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
        'python_version': '.'.join(map(str, sys.version_info[:2])),
        'python_full_version': platform.python_version(),
        'platform': {'system': platform.system(), 'os_name': os.name,
                     'sys_platform': sys.platform, 'machine': platform.machine()},
        'manifest_sha256': sha256((root / MANIFEST_PATH).read_bytes()).hexdigest(),
        'runner_sha256': sha256((root / 'scripts/run_full_core_partition_ci.py').read_bytes()).hexdigest(),
        'wood_review_dossier_present': bool(os.environ.get('WOOD_REVIEW_DOSSIER')),
    }
    return validate_context_data(result)


def new_receipt(manifest, partition, context, discovered_ids):
    validate_manifest(manifest)
    validate_context_data(context)
    return {
        'schema_version': 1, 'context': deepcopy(context), 'partition': partition,
        'expected_ids': partition_ids(manifest, partition),
        'declared_ids': manifest_ids(manifest), 'discovered_ids': list(discovered_ids),
        'started_ids': [], 'completed': [], 'fixture_errors': [],
        'subtest_errors': [], 'protocol_errors': [], 'terminal': False,
        'terminal_status': 'running', 'journal_sha256': None,
    }


def error_description(err):
    message = str(err[1])
    return {'type': type(err[1]).__name__, 'message': message[:2000],
            'message_truncated': len(message) > 2000}


class ReceiptResult(unittest.TextTestResult):
    """Keep method, fixture and subtest failures distinct and fail closed."""
    def __init__(self, stream, descriptions, verbosity, *, expected_ids, journal=None):
        super().__init__(stream, descriptions, verbosity)
        self.expected_ids = list(expected_ids)
        self.started_ids = []
        self.completed = []
        self.fixture_errors = []
        self.subtest_errors = []
        self.protocol_errors = []
        self._outcomes = {}
        self._journal = journal

    def _event(self, event, **fields):
        if self._journal is not None:
            self._journal({'event': event, **fields})

    def startTest(self, test):
        identifier = test.id()
        if identifier not in self.expected_ids or identifier in self.started_ids:
            self.protocol_errors.append({'test_id': identifier, 'error': 'unknown or duplicate start'})
        self.started_ids.append(identifier)
        self._outcomes[identifier] = []
        self._event('started', test_id=identifier)
        super().startTest(test)

    def _record(self, test, status, reason=None):
        identifier = test.id()
        record = {'test_id': identifier, 'status': status, 'reason': reason}
        if identifier not in self._outcomes:
            self.fixture_errors.append(record)
            self._event('fixture_error', **record)
        else:
            self._outcomes[identifier].append(record)
            self._event('outcome', **record)

    def addSuccess(self, test):
        self._record(test, 'passed')
        super().addSuccess(test)

    def addSkip(self, test, reason):
        self._record(test, 'skipped', reason)
        super().addSkip(test, reason)

    def addFailure(self, test, err):
        self._record(test, 'failure')
        self._event('failure_detail', test_id=test.id(), detail=error_description(err))
        super().addFailure(test, err)

    def addError(self, test, err):
        self._record(test, 'error')
        self._event('error_detail', test_id=test.id(), detail=error_description(err))
        super().addError(test, err)

    def addExpectedFailure(self, test, err):
        self._record(test, 'expected_failure')
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self._record(test, 'unexpected_success')
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            record = {'test_id': test.id(), 'subtest_id': subtest.id(),
                      'detail': error_description(err)}
            self.subtest_errors.append(record)
            self._record(test, 'subtest_error')
            self._event('subtest_error', **record)
        super().addSubTest(test, subtest, err)

    def stopTest(self, test):
        identifier = test.id()
        outcomes = self._outcomes.get(identifier, [])
        if len(outcomes) == 1:
            record = outcomes[0]
        else:
            record = {'test_id': identifier, 'status': 'invalid_outcome', 'reason': None}
            self.protocol_errors.append({'test_id': identifier, 'error': 'missing or multiple outcomes'})
        if any(item['test_id'] == identifier for item in self.completed):
            self.protocol_errors.append({'test_id': identifier, 'error': 'duplicate completion'})
        self.completed.append(record)
        self._event('completed', **record)
        super().stopTest(test)


def finish_receipt(receipt, result, terminal_status='completed'):
    output = deepcopy(receipt)
    output.update(started_ids=list(result.started_ids), completed=deepcopy(result.completed),
                  fixture_errors=deepcopy(result.fixture_errors),
                  subtest_errors=deepcopy(result.subtest_errors),
                  protocol_errors=deepcopy(result.protocol_errors),
                  terminal=True, terminal_status=terminal_status)
    return output


def validate_receipt(receipt, manifest, context, expected_python=None):
    validate_manifest(manifest)
    validate_context_data(context)
    require(type(receipt) is dict and set(receipt) == RECEIPT_KEYS, 'Unexpected receipt shape')
    require(type(receipt['schema_version']) is int and receipt['schema_version'] == 1,
            'Unknown receipt version')
    actual = validate_context_data(receipt['context'])
    for key in ('sha', 'tree', 'run_id', 'run_attempt', 'platform', 'manifest_sha256',
                'runner_sha256', 'wood_review_dossier_present'):
        require(actual[key] == context[key], 'Receipt context mismatch: ' + key)
    if expected_python is not None:
        require(actual['python_version'] == expected_python, 'Receipt Python partition mismatch')
    selected = partition_ids(manifest, receipt['partition'])
    full = manifest_ids(manifest)
    require(receipt['expected_ids'] == selected and receipt['declared_ids'] == full
            and receipt['discovered_ids'] == full, 'Receipt inventory evidence differs')
    require(receipt['terminal'] is True and receipt['terminal_status'] == 'completed',
            'Receipt is missing a successful terminal execution')
    require(type(receipt['journal_sha256']) is str
            and re.fullmatch(r'[0-9a-f]{64}', receipt['journal_sha256']), 'Missing journal binding')
    require(receipt['started_ids'] == selected, 'Started methods differ from the exact partition')
    for key in ('fixture_errors', 'subtest_errors', 'protocol_errors'):
        require(type(receipt[key]) is list and not receipt[key], 'Receipt contains ' + key)
    completed = receipt['completed']
    require(type(completed) is list and len(completed) == len(selected), 'Incomplete method results')
    allowed = skip_contract(manifest, actual['wood_review_dossier_present'])
    required_skips = {identifier: allowed[identifier] for identifier in selected if identifier in allowed}
    observed_ids, passed, skipped = [], [], {}
    for record in completed:
        require(type(record) is dict and set(record) == {'test_id', 'status', 'reason'},
                'Unexpected completed outcome shape')
        identifier = record['test_id']
        require(type(identifier) is str and identifier not in observed_ids, 'Duplicate completed method')
        observed_ids.append(identifier)
        if record['status'] == 'passed':
            require(record['reason'] is None and identifier not in required_skips,
                    'Passed outcome bypasses required skip or contains a reason')
            passed.append(identifier)
        elif record['status'] == 'skipped':
            require(identifier in required_skips and record['reason'] == required_skips[identifier],
                    'Unexpected skip ID or reason')
            skipped[identifier] = record['reason']
        else:
            raise RuntimeError('Non-successful method outcome: ' + str(record['status']))
    require(observed_ids == selected and skipped == required_skips,
            'Completed order or exact environment skip policy differs')
    return {'python_version': actual['python_version'], 'partition': receipt['partition'],
            'passed': len(passed), 'skipped': len(skipped), 'completed': len(completed),
            'passed_ids': passed, 'skipped_ids': list(skipped),
            'skipped_reasons': skipped, 'completed_ids': observed_ids}


def aggregate_receipts(receipts, manifest, context, matrix_result):
    require(matrix_result == 'success', 'The complete matrix did not succeed, including later steps')
    validate_manifest(manifest)
    validate_context_data(context)
    require(type(receipts) is list and len(receipts) == 8, 'Exactly eight partition receipts are required')
    expected_pairs = {(version, partition) for version in PYTHON_VERSIONS for partition in PARTITIONS}
    found, summaries, versions = set(), [], {}
    for receipt in receipts:
        summary = validate_receipt(receipt, manifest, context)
        pair = (summary['python_version'], summary['partition'])
        require(pair in expected_pairs and pair not in found, 'Duplicate or unexpected version/partition')
        found.add(pair)
        summaries.append(summary)
        versions.setdefault(pair[0], set()).add(receipt['context']['python_full_version'])
    require(found == expected_pairs and all(len(items) == 1 for items in versions.values()),
            'Missing partition or inconsistent Python interpreter versions')
    totals = []
    full = manifest_ids(manifest)
    allowed = skip_contract(manifest, context['wood_review_dossier_present'])
    for version in PYTHON_VERSIONS:
        selected = [summary for summary in summaries if summary['python_version'] == version]
        completed = [identifier for summary in selected for identifier in summary['completed_ids']]
        skipped = {identifier: reason for summary in selected for identifier, reason in summary['skipped_reasons'].items()}
        require(len(completed) == len(set(completed)) == 1887 and set(completed) == set(full),
                'Python-version partitions do not cover the complete disjoint inventory')
        require(skipped == allowed, 'Aggregate environment skip policy differs')
        totals.append({'python_version': version, 'completed': 1887,
                       'passed': 1887 - len(skipped), 'skipped': len(skipped),
                       'skipped_ids': sorted(skipped), 'not_completed': 0})
    return {'schema_version': 1, 'terminal': True, 'terminal_status': 'completed',
            'context': deepcopy(context), 'matrix_result': matrix_result,
            'root_inventory_sha256': ROOT_INVENTORY_SHA256,
            'versions': totals, 'receipt_count': 8,
            'explicit_replay_inventory_included': False}


def atomic_json(path, value):
    path = Path(path)
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=path.name + '.', suffix='.tmp', dir=path.parent,
                                         delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


class Journal:
    def __init__(self, path):
        self.path = Path(path)
        self.handle = self.path.open('x', encoding='utf-8', newline='\n')
        self.sequence = 0

    def __call__(self, event):
        record = {'sequence': self.sequence, 'monotonic_ns': time.monotonic_ns(), **event}
        self.handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')
        self.handle.flush()
        self.sequence += 1
        if event.get('event') in ('started', 'completed', 'terminal'):
            print('CORE_PARTITION_PROGRESS ' + json.dumps(record, sort_keys=True), flush=True)

    def close(self):
        self.handle.flush()
        self.handle.close()


class CancelledRun(BaseException):
    pass


def run_partition(partition, output_dir, root=ROOT):
    root = Path(root).resolve()
    output_dir = Path(output_dir).resolve()
    require(output_dir != root and output_dir.is_relative_to(root) and not output_dir.exists(),
            'Run output directory must be new and inside the checkout')
    manifest = load_manifest(root)
    context = production_context(root, role='run')
    receipt = new_receipt(manifest, partition, context, [])
    receipt['declared_ids'] = []
    output_dir.mkdir(parents=True)
    journal = Journal(output_dir / 'journal.jsonl')
    journal({'event': 'header', 'context': context, 'partition': partition})
    atomic_json(output_dir / 'receipt.json', receipt)
    result = None
    previous_term = signal.getsignal(signal.SIGTERM)

    def cancelled(signum, frame):
        raise CancelledRun('Termination signal received')

    signal.signal(signal.SIGTERM, cancelled)
    exit_code = 1
    try:
        suite, discovered = discover_inventory(manifest, root)
        receipt['declared_ids'] = declared_inventory(root)
        receipt['discovered_ids'] = discovered
        selected = select_partition(suite, manifest, partition)
        atomic_json(output_dir / 'receipt.json', receipt)

        def result_factory(stream, descriptions, verbosity):
            nonlocal result
            result = ReceiptResult(stream, descriptions, verbosity,
                                   expected_ids=receipt['expected_ids'], journal=journal)
            return result

        unittest.TextTestRunner(verbosity=2, failfast=False, resultclass=result_factory).run(selected)
        receipt = finish_receipt(receipt, result)
        require(production_context(root, role='run', allowed_untracked=(output_dir,)) == context,
                'Checkout or execution context drifted while tests ran')
        journal.handle.flush()
        # Validate semantics before writing the single terminal journal event.
        # This temporary prefix digest is never published as the final binding.
        receipt['journal_sha256'] = sha256(journal.path.read_bytes()).hexdigest()
        validate_receipt(receipt, manifest, context, context['python_version'])
        journal({'event': 'terminal', 'terminal_status': 'completed'})
        exit_code = 0
    except BaseException as error:
        interrupted = isinstance(error, (CancelledRun, KeyboardInterrupt))
        if result is not None:
            receipt = finish_receipt(receipt, result, 'cancelled' if interrupted else 'failed')
        else:
            receipt.update(terminal=True, terminal_status='cancelled' if interrupted else 'failed')
        receipt['protocol_errors'].append({'event': 'runner_exception',
                                           'type': type(error).__name__, 'message': str(error)[:2000]})
        journal({'event': 'terminal', 'terminal_status': receipt['terminal_status'],
                 'error_type': type(error).__name__})
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr, flush=True)
        exit_code = 130 if interrupted else 1
    finally:
        signal.signal(signal.SIGTERM, previous_term)
        journal.close()
        receipt['journal_sha256'] = sha256(journal.path.read_bytes()).hexdigest()
        atomic_json(output_dir / 'receipt.json', receipt)
    return exit_code


def load_receipts(receipts_dir, context):
    """Accept only the eight named current-run artifact directories and two files."""
    directory = Path(receipts_dir)
    require(directory.is_dir() and not directory.is_symlink(), 'Missing or linked receipt directory')
    names = {f"full-core-{version}-{partition}-{context['run_id']}-{context['run_attempt']}":
             (version, partition) for version in PYTHON_VERSIONS for partition in PARTITIONS}
    children = list(directory.iterdir())
    require({path.name for path in children} == set(names) and len(children) == 8,
            'Missing, extra or stale receipt artifact directories')
    receipts = []
    for child in sorted(children):
        require(child.is_dir() and not child.is_symlink(), 'Linked or invalid receipt artifact')
        entries = list(child.iterdir())
        require({path.name for path in entries} == {'receipt.json', 'journal.jsonl'} and len(entries) == 2,
                'Missing or extra artifact files')
        require(all(path.is_file() and not path.is_symlink() for path in entries),
                'Linked or invalid receipt/journal file')
        receipt = read_json(child / 'receipt.json')
        version, partition = names[child.name]
        require(type(receipt) is dict and receipt.get('partition') == partition
                and type(receipt.get('context')) is dict
                and receipt['context'].get('python_version') == version,
                'Artifact name disagrees with receipt identity')
        journal = (child / 'journal.jsonl').read_bytes()
        require(receipt.get('journal_sha256') == sha256(journal).hexdigest(), 'Journal bytes differ from receipt')
        require(journal.endswith(b'\n'), 'Truncated journal')
        events = [json.loads(line, object_pairs_hook=unique_keys) for line in journal.splitlines()]
        require(events and all(type(event) is dict and type(event.get('sequence')) is int
                               and event['sequence'] == index
                               and type(event.get('monotonic_ns')) is int
                               and event['monotonic_ns'] >= 0
                               for index, event in enumerate(events)), 'Invalid journal sequence')
        require([event['monotonic_ns'] for event in events] ==
                sorted(event['monotonic_ns'] for event in events), 'Journal clock moved backwards')
        require(events[0].get('event') == 'header' and events[0].get('context') == receipt['context']
                and events[0].get('partition') == partition, 'Journal context differs')
        require(events[-1].get('event') == 'terminal'
                and events[-1].get('terminal_status') == receipt.get('terminal_status'),
                'Missing or mismatched terminal journal event')
        require(sum(event.get('event') == 'header' for event in events) == 1
                and sum(event.get('event') == 'terminal' for event in events) == 1,
                'Repeated journal header or terminal event')
        base_keys = {'sequence', 'monotonic_ns', 'event'}
        require(set(events[0]) == base_keys | {'context', 'partition'}
                and set(events[-1]) == base_keys | {'terminal_status'},
                'Unexpected journal header or terminal fields')
        require(all(event.get('event') in {'header', 'started', 'outcome', 'completed', 'terminal'}
                    for event in events), 'Journal contains non-success execution events')
        require([event.get('test_id') for event in events if event.get('event') == 'started'] ==
                receipt.get('started_ids'), 'Journal started IDs differ from receipt')
        for event_name in ('outcome', 'completed'):
            observed = [{key: event.get(key) for key in ('test_id', 'status', 'reason')}
                        for event in events if event.get('event') == event_name]
            require(observed == receipt.get('completed'), 'Journal outcomes differ from receipt')
        completed = receipt.get('completed')
        require(type(completed) is list and len(events) == 2 + 3 * len(completed),
                'Journal lacks exact per-method execution records')
        for index, record in enumerate(completed):
            started, outcome, finished = events[1 + 3 * index:4 + 3 * index]
            require(started['event'] == 'started' and outcome['event'] == 'outcome'
                    and finished['event'] == 'completed', 'Journal method event ordering changed')
            require(set(started) == base_keys | {'test_id'}
                    and set(outcome) == base_keys | {'test_id', 'status', 'reason'}
                    and set(finished) == base_keys | {'test_id', 'status', 'reason'},
                    'Unexpected method journal fields')
            require(started['test_id'] == record['test_id'] and all(
                event[key] == record[key] for event in (outcome, finished)
                for key in ('test_id', 'status', 'reason')), 'Journal method records disagree')
        receipts.append(receipt)
    return receipts


def aggregate_directory(receipts_dir, matrix_result, output, root=ROOT):
    root = Path(root).resolve()
    output = Path(output).resolve()
    require(output != root and output.is_relative_to(root) and not output.exists(),
            'Aggregate output must be new and inside the checkout')
    report = {'schema_version': 1, 'terminal': False, 'terminal_status': 'validating',
              'matrix_result': matrix_result}
    try:
        manifest = load_manifest(root)
        validate_declarations(manifest, root)
        context = production_context(root, role='aggregate', allowed_untracked=(receipts_dir,))
        report['context'] = context
        require(matrix_result == 'success', 'The complete matrix did not succeed, including later steps')
        receipts = load_receipts(receipts_dir, context)
        report = aggregate_receipts(receipts, manifest, context, matrix_result)
        atomic_json(output, report)
        print(json.dumps({'event': 'FULL_CORE_PARTITIONS_COMPLETE', **report}, sort_keys=True))
        return 0
    except BaseException as error:
        report.update(terminal=True, terminal_status='failed', error_type=type(error).__name__,
                      error=str(error)[:2000])
        atomic_json(output, report)
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr, flush=True)
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('run')
    run.add_argument('--partition', type=int, choices=PARTITIONS, required=True)
    run.add_argument('--output-dir', type=Path, required=True)
    aggregate = commands.add_parser('aggregate')
    aggregate.add_argument('--receipts-dir', type=Path, required=True)
    aggregate.add_argument('--matrix-result', required=True)
    aggregate.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'run':
        return run_partition(args.partition, args.output_dir)
    return aggregate_directory(args.receipts_dir, args.matrix_result, args.output)


if __name__ == '__main__':
    raise SystemExit(main())
