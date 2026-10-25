"""Exact history-checkout recovery without changing historical assertions.

These tests exercise finite code images and history availability, not full core
or installed-package coverage. No network fetch is performed by this module.
"""
import ast
from copy import deepcopy
from hashlib import sha1, sha256
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import material_append_successors as successors
from material_append_history import recover_file
from curaua_history import checkpoint_bytes
import replay_checkout_history as history
from ci_partition_history import project_partition_file, predecessor_registry

BASE = 'e39b6d8a19576a05408b7da0e3faa8499b9f35f6'
TIAN = '826333c73a420b7d254c469d9f6f65155983cde1'
WORKFLOW = '.github/workflows/ci.yml'
REGISTRY = 'tests/material_append_successors.py'
CALLER = 'tests/test_tian_nano_ti_ci.py'
PINS = {
    WORKFLOW: ('365b7e88441bc038de956f23ea1216cf90129469312330ce23f27d8a17b5e2eb',
               '126dda53574573de098826a39a3d4c6dab373012193563e3760cd84e6f100982'),
    REGISTRY: ('df5250b9d9e7b67bd8ec92cdfbc2d2efce99db5ff1a4dea0631431cbad5d886f',
               '748ecbb5cb2f04ca4ffd7432bded505a6e14d48c2119500e0b8e579346cf56b4'),
    CALLER: ('07cbd6a9c4fead4d3169a541e182d2d4154dd470917f9a76f33afdf53a7e4374',
             '0c1e351ae81ffe7ce1e38d646f5515b80fd1c270a10639bee58dbc3c7bf65de6'),
}
CHECKOUT_BEFORE = ('      - uses: actions/checkout@v4\n'
                   '      - uses: actions/setup-python@v5\n').encode()
CHECKOUT_AFTER = ('      - uses: actions/checkout@v4\n'
                  '        with:\n          fetch-depth: 0\n'
                  '      - uses: actions/setup-python@v5\n').encode()


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True,
                          capture_output=True, timeout=30).stdout


def baseline(path):
    return git('show', BASE + ':' + path)


def checkout_checkpoint_bytes(path):
    """Recover only the reviewed later CI edit before historical assertions."""
    return project_partition_file(path, (ROOT / path).read_bytes())


def jobs(raw):
    matches = list(re.finditer(rb'^  ([a-z0-9-]+):\n', raw, re.MULTILINE))
    return {match[1].decode(): raw[match.start():matches[index + 1].start()
                                 if index + 1 < len(matches) else len(raw)]
            for index, match in enumerate(matches)}


class CheckoutHistoryTests(unittest.TestCase):
    def test_exact_helper_ledger_and_three_whole_file_images_are_pinned(self):
        self.assertEqual(sha256((ROOT / 'tests/replay_checkout_history.py').read_bytes()).hexdigest(),
                         '24d244d06b84142a6633760df977a9fe221c29d2c3eb5ac03cfc2c8756ace38f')
        self.assertEqual(history.LEDGER_SHA256,
                         '847d86d5e5004cdc4ab786f4d3239ec5cb6c6fb3b2ab5acd6a8e5bbcbed42e52')
        ledger = history.code_ledger()
        self.assertEqual(ledger['baseline_commit'], BASE)
        self.assertEqual(set(ledger['updates']), set(PINS))
        for path, (old_pin, new_pin) in PINS.items():
            with self.subTest(path=path):
                entry = ledger['updates'][path]
                old, new = baseline(path), checkout_checkpoint_bytes(path)
                self.assertEqual(sha256(old).hexdigest(), old_pin)
                self.assertEqual(sha256(new).hexdigest(), new_pin)
                self.assertEqual((entry['previous_sha256'], entry['sha256']), (old_pin, new_pin))
                self.assertEqual(recover_file(new, entry), old)
                self.assertIs(history.project_checkout_file(path, old), old)
                self.assertEqual(history.project_checkout_file(path, new), old)

    def test_only_two_generic_checkouts_change_and_all_other_jobs_are_exact(self):
        old, new = baseline(WORKFLOW), checkout_checkpoint_bytes(WORKFLOW)
        self.assertEqual(old.count(CHECKOUT_BEFORE), 2)
        self.assertEqual(new, old.replace(CHECKOUT_BEFORE, CHECKOUT_AFTER))
        old_jobs, new_jobs = jobs(old), jobs(new)
        self.assertEqual(list(new_jobs), list(old_jobs))
        self.assertEqual(len(new_jobs), 21)
        generic = {'unit-and-schema', 'windows-composite'}
        self.assertEqual(len(set(new_jobs) - generic), 19)
        for name, current in new_jobs.items():
            with self.subTest(job=name):
                expected = old_jobs[name]
                if name in generic:
                    self.assertEqual(expected.count(CHECKOUT_BEFORE), 1)
                    expected = expected.replace(CHECKOUT_BEFORE, CHECKOUT_AFTER)
                self.assertEqual(current, expected)
                self.assertEqual(current.count(b'          fetch-depth: 0\n'), 1)
        # These independent workflows retain their previous execution scope.
        for path in ('.github/workflows/history-replay-latest.yml',
                     '.github/workflows/experimental-platform.yml'):
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes(), baseline(path))

    def test_tian_input_wrapper_preserves_every_original_ast_assertion(self):
        class StripWrapper(ast.NodeTransformer):
            imports = 0
            calls = 0
            def visit_ImportFrom(self, node):
                if node.module == 'replay_checkout_history':
                    if [(item.name, item.asname) for item in node.names] != [('project_checkout_file', None)]:
                        raise AssertionError('Unexpected checkout recovery import')
                    self.imports += 1
                    return None
                return node
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id == 'project_checkout_file':
                    if (len(node.args) != 2 or node.keywords
                            or not isinstance(node.args[0], ast.Constant)
                            or node.args[0].value != WORKFLOW):
                        raise AssertionError('Unexpected checkout recovery call')
                    self.calls += 1
                    return node.args[1]
                return node
        transform = StripWrapper()
        projected = transform.visit(ast.parse(checkout_checkpoint_bytes(CALLER)))
        self.assertEqual((transform.imports, transform.calls), (1, 1))
        self.assertEqual(ast.dump(projected), ast.dump(ast.parse(baseline(CALLER))))

    def test_registry_changes_only_the_finite_file_prefix_not_material_chronology(self):
        successors = predecessor_registry()
        old_raw, new_raw = baseline(REGISTRY), checkout_checkpoint_bytes(REGISTRY)
        before = b'    result = [code_ledger()] if before is None else []\n'
        after = (b'    from replay_checkout_history import code_ledger as checkout_code_ledger\n'
                 b'    result = [checkout_code_ledger()] + ([code_ledger()] if before is None else [])\n')
        self.assertEqual(old_raw.count(before), 1)
        self.assertEqual(new_raw, old_raw.replace(before, after))
        old = ModuleType('checkout_predecessor_registry')
        old.__file__ = str(ROOT / REGISTRY)
        exec(compile(old_raw, old.__file__, 'exec'), old.__dict__)
        self.assertEqual(successors.FROZEN_SUCCESSORS, old.FROZEN_SUCCESSORS)
        for boundary in [None] + [item['batch_id'] for item in old.FROZEN_SUCCESSORS]:
            with self.subTest(boundary=boundary):
                self.assertEqual(successors.file_ledgers(before=boundary),
                                 [history.code_ledger()] + old.file_ledgers(before=boundary))
                self.assertEqual(successors.data_ledgers(before=boundary), old.data_ledgers(before=boundary))

    def test_unknown_partial_mutated_and_reordered_workflows_cannot_recover(self):
        raw = checkout_checkpoint_bytes(WORKFLOW)
        entry = history.code_ledger()['updates'][WORKFLOW]
        blocks = jobs(raw)
        first, second = blocks['unit-and-schema'], blocks['windows-composite']
        altered = [b'unknown', raw + b'# unreviewed\n', raw[:-1],
                   raw.replace(CHECKOUT_AFTER, CHECKOUT_BEFORE, 1),
                   raw.replace(first + second, second + first, 1),
                   raw.replace(b'contents: read', b'contents: write', 1),
                   raw.replace(b'fetch-depth: 0', b'fetch-depth: 1', 1)]
        for value in altered:
            with self.subTest(digest=sha256(value).hexdigest()):
                self.assertNotEqual(value, raw)
                self.assertIs(history.project_checkout_file(WORKFLOW, value), value)
                with self.assertRaises(AssertionError):
                    recover_file(history.project_checkout_file(WORKFLOW, value), entry)
        for path in (REGISTRY, CALLER):
            entry = history.code_ledger()['updates'][path]
            value = checkout_checkpoint_bytes(path) + b' changed'
            self.assertIs(history.project_checkout_file(path, value), value)
            with self.assertRaises(AssertionError):
                recover_file(value, entry)
        with patch.object(history, 'code_ledger') as load:
            untouched = b'unrelated bytes'
            self.assertIs(history.project_checkout_file('unrelated.txt', untouched), untouched)
            for name, value in ((None, b''), (WORKFLOW, bytearray(raw)), (WORKFLOW, 'text')):
                with self.subTest(name=name), self.assertRaises(AssertionError):
                    history.project_checkout_file(name, value)
            load.assert_not_called()

    def test_ledger_and_root_are_reread_and_missing_or_changed_inputs_fail_closed(self):
        raw = (ROOT / history.LEDGER_PATH).read_bytes()
        value = history.code_ledger()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / history.LEDGER_PATH
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
            with patch.object(history, 'ROOT', root):
                self.assertEqual(history.code_ledger(), value)
                for changed in (raw + b' ', raw[:-1], b'{}'):
                    path.write_bytes(changed)
                    with self.subTest(size=len(changed)), self.assertRaisesRegex(AssertionError, 'Unreviewed append-history ledger'):
                        history.code_ledger()
                path.write_bytes(raw)
                self.assertEqual(history.code_ledger(), value)
                path.unlink()
                with self.assertRaises(FileNotFoundError):
                    history.code_ledger()
        for key, replacement in (('schema_version', True), ('baseline_commit', '0' * 40),
                                 ('updates', {}), ('extra', 1)):
            changed = deepcopy(value)
            changed[key] = replacement
            with self.subTest(key=key), patch.object(history, 'load_frozen', return_value=changed), \
                    self.assertRaisesRegex(AssertionError, 'Unexpected finite checkout-history ledger'):
                history.code_ledger()

    def test_offset_before_after_and_hash_drift_cannot_pass_exact_round_trip(self):
        for path, entry in history.code_ledger()['updates'].items():
            raw = checkout_checkpoint_bytes(path)
            for field in ('offset', 'before', 'after', 'previous_sha256', 'sha256'):
                changed = deepcopy(entry)
                if field == 'offset': changed['edits'][0][field] += 1
                elif field in ('before', 'after'): changed['edits'][0][field] += '!'
                else: changed[field] = '0' * 64
                with self.subTest(path=path, field=field), self.assertRaises(AssertionError):
                    recover_file(raw, changed)

    def test_unknown_boundaries_precede_loading_and_old_drift_keeps_its_cause(self):
        with patch.object(history, 'code_ledger', side_effect=RuntimeError('unexpected new ledger load')) as load:
            with self.assertRaisesRegex(AssertionError, 'Unknown or duplicate frozen successor batch'):
                successors.file_ledgers(before='unreviewed-boundary')
            with patch.object(successors, 'FROZEN_SUCCESSORS', successors.FROZEN_SUCCESSORS * 2):
                with self.assertRaisesRegex(AssertionError, 'Duplicate frozen successor batch'):
                    successors.file_ledgers()
            load.assert_not_called()
        boundary = 'zenodo-8089569-nylon-followup-20261021'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            changed = root / successors.CODE_FILE_LEDGER
            changed.parent.mkdir(parents=True)
            changed.write_bytes((ROOT / successors.CODE_FILE_LEDGER).read_bytes() + b' ')
            for descriptor in successors._prefix(boundary):
                name = descriptor['files'][0]
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            with patch.object(successors, 'ROOT', root), \
                    patch.object(successors, 'load_frozen', wraps=successors.load_frozen) as load, \
                    self.assertRaisesRegex(AssertionError, '^Unreviewed append-history ledger$'):
                successors.file_ledgers(before=boundary)
            self.assertEqual(load.call_args.args[1], successors.CODE_FILE_LEDGER)
            self.assertFalse((root / history.LEDGER_PATH).exists())

    def test_required_historical_git_objects_exist_without_fetching(self):
        commits = [BASE, TIAN, '5a9a85c573f590d206cddb4cb7c085f334a0fbc0',
                   '196995256836db2d8f870ac9a91f664bfdd03e7f',
                   '7248dcd06e7ab4bc5f3fae1f3f21a7d9e0dbad3c']
        for commit in commits:
            with self.subTest(commit=commit):
                self.assertEqual(git('cat-file', '-t', commit).strip(), b'commit')
                self.assertEqual(git('cat-file', '-t', commit + ':' + WORKFLOW).strip(), b'blob')
        self.assertEqual(git('rev-parse', '--is-shallow-repository').strip(), b'false')

    def test_old_fixtures_engine_and_both_benchmarks_remain_byte_exact(self):
        entries = git('ls-tree', '-r', '-z', TIAN, '--', 'tests/fixtures').split(b'\0')
        entries = [entry for entry in entries if entry]
        self.assertEqual(len(entries), 119)
        for entry in entries:
            metadata, path = entry.split(b'\t', 1)
            mode, kind, expected = metadata.split()
            self.assertEqual(kind, b'blob')
            raw = (ROOT / path.decode()).read_bytes()
            actual = sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode()
            with self.subTest(path=path.decode()):
                self.assertEqual(actual, expected)
        for path in ('tests/material_append_history.py', 'tests/material_append_replay_compat.py',
                     'tests/history_replay/benchmark_replay.py',
                     'tests/history_replay_latest/benchmark_replay_16.py',
                     'tests/fixtures/material_append_replay_16_20261024.json'):
            with self.subTest(path=path):
                self.assertEqual(checkpoint_bytes(path), baseline(path))


if __name__ == '__main__':
    unittest.main()
