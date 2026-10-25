"""Finite partition-code recovery keeps historical assertions and evidence exact."""
import ast
from copy import deepcopy
from hashlib import sha1, sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import ci_partition_history as history
import material_append_successors as successors
from material_append_history import recover_file
from curaua_history import checkpoint_bytes, checkpoint_registry
successors = checkpoint_registry()

BASE = 'bf1c7a86068c37c2733ac4d25c268144090f9aad'
WORKFLOW = '.github/workflows/ci.yml'
REGISTRY = 'tests/material_append_successors.py'
HELPER_SHA256 = '97b78329023c0ccc7e4ad6fb5bb34ace2b0f3f70df2969dae265dea3927ba878'
LEDGER_SHA256 = '9a6befc0edd6562b7e2149b6197e90d7ee0fd2a8bdff1ddcb00e0247c77e5a30'


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True,
                          capture_output=True, timeout=30).stdout


def baseline(path):
    return git('show', BASE + ':' + path)


class StripHistoricalInputAdapters(ast.NodeTransformer):
    """Remove only the finite new input adapters, never an old assertion."""
    def visit_ImportFrom(self, node):
        return None if node.module == 'ci_partition_history' else node

    def visit_FunctionDef(self, node):
        if node.name == 'checkout_checkpoint_bytes':
            return None
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                and ((node.targets[0].id == 'successors' and node.value.func.id == 'predecessor_registry')
                     or (node.targets[0].id == 'checkout_only' and node.value.func.id == 'project_partition_file'))):
            return None
        return self.generic_visit(node)

    def visit_Tuple(self, node):
        node = self.generic_visit(node)
        node.elts = [item for item in node.elts
                     if not (isinstance(item, ast.Name) and item.id == 'checkout_only')]
        return node

    def visit_Call(self, node):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == 'project_partition_file':
            if len(node.args) != 2 or node.keywords:
                raise AssertionError('Unexpected partition input adapter')
            return node.args[1]
        if isinstance(node.func, ast.Name) and node.func.id == 'checkout_checkpoint_bytes':
            if len(node.args) != 1 or node.keywords:
                raise AssertionError('Unexpected checkpoint input reader')
            return ast.Call(
                func=ast.Attribute(value=ast.BinOp(left=ast.Name(id='ROOT', ctx=ast.Load()),
                                                   op=ast.Div(), right=node.args[0]),
                                   attr='read_bytes', ctx=ast.Load()), args=[], keywords=[])
        return node


class PartitionHistoryTests(unittest.TestCase):
    def test_pinned_helper_ledger_and_all_whole_file_round_trips(self):
        self.assertEqual(sha256(checkpoint_bytes('tests/ci_partition_history.py')).hexdigest(), HELPER_SHA256)
        self.assertEqual(history.LEDGER_SHA256, LEDGER_SHA256)
        ledger = history.code_ledger()
        self.assertEqual(ledger['baseline_commit'], BASE)
        self.assertEqual(set(ledger['updates']), set(history.PATHS))
        self.assertEqual(len(ledger['updates']), 7)
        for path, entry in ledger['updates'].items():
            with self.subTest(path=path):
                old, new = baseline(path), checkpoint_bytes(path)
                self.assertNotEqual(old, new)
                self.assertEqual(sha256(old).hexdigest(), entry['previous_sha256'])
                self.assertEqual(sha256(new).hexdigest(), entry['sha256'])
                self.assertEqual(recover_file(new, entry), old)
                self.assertEqual(history.project_partition_file(path, new), old)
                self.assertIs(history.project_partition_file(path, old), old)
                self.assertEqual(history.require_partition_file(path, new), old)
                with self.assertRaises(AssertionError):
                    history.require_partition_file(path, old)

    def test_current_registry_prefix_is_exact_for_every_boundary(self):
        previous = history.predecessor_registry()
        self.assertEqual(successors.FROZEN_SUCCESSORS, previous.FROZEN_SUCCESSORS)
        for boundary in [None] + [item['batch_id'] for item in previous.FROZEN_SUCCESSORS]:
            with self.subTest(boundary=boundary):
                self.assertEqual(successors.file_ledgers(before=boundary),
                                 [history.code_ledger()] + previous.file_ledgers(before=boundary))
                self.assertEqual(successors.data_ledgers(before=boundary), previous.data_ledgers(before=boundary))
        raw = (ROOT / WORKFLOW).read_bytes()
        for descriptor in successors.FROZEN_SUCCESSORS:
            batch = descriptor['batch_id']
            entry = successors.file_ledger(batch)['updates'][WORKFLOW]
            with self.subTest(batch=batch):
                projected = successors.project_successor_file(WORKFLOW, raw, before=batch)
                self.assertEqual(sha256(projected).hexdigest(), entry['sha256'])
                self.assertEqual(sha256(recover_file(projected, entry)).hexdigest(), entry['previous_sha256'])

    def test_original_caller_assertions_are_unchanged_after_exact_input_adapters(self):
        paths = ('tests/test_tian_nano_ti_ci.py', 'tests/history_replay/test_replay_compat.py',
                 'tests/history_replay_latest/test_checkout_history.py',
                 'tests/history_replay_latest/test_ci_contract.py')
        for path in paths:
            with self.subTest(path=path):
                original = ast.parse(baseline(path))
                current = ast.parse(checkpoint_bytes(path))
                normalized = StripHistoricalInputAdapters().visit(current)
                self.assertEqual(ast.dump(normalized), ast.dump(original))
        old_runner = ast.parse(baseline('scripts/run_history_replay_latest_ci.py'))
        new_runner = ast.parse((ROOT / 'scripts/run_history_replay_latest_ci.py').read_bytes())
        def requires(tree):
            return [ast.dump(node) for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == 'require']
        old_checks, new_checks = requires(old_runner), requires(new_runner)
        self.assertEqual(len(new_checks), len(old_checks) + 1)
        for check in old_checks:
            self.assertEqual(new_checks.count(check), old_checks.count(check))

    def test_unknown_mutated_partial_and_wrong_type_inputs_are_not_recovered(self):
        for path, entry in history.code_ledger()['updates'].items():
            raw = (ROOT / path).read_bytes()
            for value in (b'unknown', raw + b' changed', raw[:-1], raw[1:]):
                with self.subTest(path=path, length=len(value)):
                    self.assertIs(history.project_partition_file(path, value), value)
                    with self.assertRaises(AssertionError):
                        history.require_partition_file(path, value)
                    with self.assertRaises(AssertionError):
                        recover_file(value, entry)
        with patch.object(history, 'code_ledger') as load:
            raw = b'unrelated bytes'
            self.assertIs(history.project_partition_file('unrelated.txt', raw), raw)
            for name, value in ((None, b''), (WORKFLOW, bytearray(b'')), (WORKFLOW, 'text')):
                with self.subTest(name=name), self.assertRaises(AssertionError):
                    history.project_partition_file(name, value)
            with self.assertRaises(AssertionError):
                history.require_partition_file('unrelated.txt', raw)
            load.assert_not_called()

    def test_ledger_root_mutation_and_missing_inputs_are_reread_without_cache(self):
        raw = (ROOT / history.LEDGER_PATH).read_bytes()
        expected = history.code_ledger()
        image = (ROOT / WORKFLOW).read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / history.LEDGER_PATH
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
            with patch.object(history, 'ROOT', root):
                self.assertEqual(history.code_ledger(), expected)
                self.assertEqual(history.require_partition_file(WORKFLOW, image), baseline(WORKFLOW))
                for changed in (raw + b' ', raw[:-1], b'{}'):
                    path.write_bytes(changed)
                    with self.subTest(length=len(changed)), self.assertRaises(AssertionError):
                        history.project_partition_file(WORKFLOW, image)
                path.write_bytes(raw)
                self.assertEqual(history.code_ledger(), expected)
                path.unlink()
                with self.assertRaises(FileNotFoundError):
                    history.code_ledger()
        for field, value in (('schema_version', True), ('baseline_commit', '0' * 40),
                             ('updates', {}), ('extra', 1)):
            altered = deepcopy(expected)
            altered[field] = value
            with self.subTest(field=field), patch.object(history, 'load_frozen', return_value=altered), \
                    self.assertRaisesRegex(AssertionError, 'Unexpected finite CI partition history ledger'):
                history.code_ledger()

    def test_bad_offsets_edits_and_hashes_fail_exact_recovery(self):
        for path, entry in history.code_ledger()['updates'].items():
            raw = (ROOT / path).read_bytes()
            for field in ('offset', 'before', 'after', 'sha256', 'previous_sha256'):
                changed = deepcopy(entry)
                if field == 'offset': changed['edits'][0]['offset'] += 1
                elif field in ('before', 'after'): changed['edits'][0][field] += '!'
                else: changed[field] = '0' * 64
                with self.subTest(path=path, field=field), self.assertRaises(AssertionError):
                    recover_file(raw, changed)

    def test_registry_view_rejects_changed_code_before_compilation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = root / history.LEDGER_PATH
            ledger.parent.mkdir(parents=True)
            ledger.write_bytes((ROOT / history.LEDGER_PATH).read_bytes())
            registry = root / REGISTRY
            registry.parent.mkdir(parents=True, exist_ok=True)
            registry.write_bytes((ROOT / REGISTRY).read_bytes() + b' changed')
            with patch.object(history, 'ROOT', root), patch('builtins.compile') as compile_code, \
                    self.assertRaisesRegex(AssertionError, 'Unreviewed current CI partition history file'):
                history.predecessor_registry()
            compile_code.assert_not_called()
        with patch.object(history, 'code_ledger') as load:
            with self.assertRaises(AssertionError):
                successors.file_ledgers(before='unknown-partition-boundary')
            load.assert_not_called()

    def test_all_old_fixtures_replay_inventory_and_benchmark_inputs_remain_exact(self):
        entries = [entry for entry in git('ls-tree', '-r', '-z',
                   '826333c73a420b7d254c469d9f6f65155983cde1', '--', 'tests/fixtures').split(b'\0') if entry]
        self.assertEqual(len(entries), 119)
        for entry in entries:
            metadata, name = entry.split(b'\t', 1)
            raw = (ROOT / name.decode()).read_bytes()
            actual = sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode()
            with self.subTest(path=name.decode()):
                self.assertEqual(actual, metadata.split()[2])
        for path in ('tests/replay_checkout_history.py',
                     'tests/history_replay_latest/checkout-history.json',
                     'tests/history_replay_latest/ci-inventory.json',
                     'tests/material_append_history.py', 'tests/material_append_replay_compat.py',
                     'tests/history_replay/benchmark_replay.py',
                     'tests/history_replay_latest/benchmark_replay_16.py',
                     'tests/fixtures/material_append_replay_16_20261024.json',
                     '.github/workflows/history-replay-latest.yml'):
            with self.subTest(path=path):
                self.assertEqual(checkpoint_bytes(path), baseline(path))


if __name__ == '__main__':
    unittest.main()
