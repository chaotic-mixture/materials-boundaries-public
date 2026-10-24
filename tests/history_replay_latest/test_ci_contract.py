"""Exact CI discovery, result and workflow boundaries for replay-only checks."""
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('replay_latest_ci', ROOT / 'scripts/run_history_replay_latest_ci.py')
ci = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci)


def fixture_manifest():
    ids = sorted([*ci.EXPLICIT_IDS, 'test_example.Example.test_one'])
    return {'schema_version': 1, 'baseline_commit': ci.BASE_COMMIT,
            'directories': list(ci.DIRECTORIES), 'explicit_ids': list(ci.EXPLICIT_IDS),
            'ids': ids, 'count': len(ids), 'fingerprint': ci.fingerprint(ids)}


class ReplayLatestCIContracts(unittest.TestCase):
    def test_frozen_inventory_explicitly_discovers_both_directories_and_four_old_methods(self):
        manifest = ci.load_manifest()
        ids = list(ci.test_ids(ci.load_suite()))
        ci.validate_discovery(ids, manifest)
        self.assertEqual(set(ci.EXPLICIT_IDS), set(manifest['explicit_ids']))
        self.assertEqual(len(ci.EXPLICIT_IDS), 4)
        self.assertEqual(manifest['directories'], ['tests/history_replay', 'tests/history_replay_latest'])
        self.assertIn(self.id(), ids)
        for relative in ci.DIRECTORIES:
            self.assertFalse((ROOT / relative / '__init__.py').exists())

    def test_missing_duplicate_extra_substituted_and_reordered_manifest_ids_fail_closed(self):
        good = fixture_manifest()
        ci.validate_manifest(good)
        for kind in ('missing', 'duplicate', 'extra', 'substitute', 'reverse'):
            altered = deepcopy(good)
            if kind == 'missing': altered['ids'].pop()
            elif kind == 'duplicate': altered['ids'].append(altered['ids'][0])
            elif kind == 'extra': altered['ids'].append('unreviewed.Test.test_extra')
            elif kind == 'substitute': altered['ids'][0] = 'unreviewed.Test.test_one'
            else: altered['ids'].reverse()
            with self.subTest(kind=kind), self.assertRaises(RuntimeError):
                ci.validate_manifest(altered)
        for ids in (good['ids'][:-1], good['ids'] + [good['ids'][0]],
                    good['ids'][:-1] + ['unreviewed.Test.test_one']):
            with self.subTest(ids=ids), self.assertRaises(RuntimeError):
                ci.validate_discovery(ids, good)
        self.assertEqual(ci.fingerprint(reversed(good['ids'])), good['fingerprint'])

    def test_manifest_bytes_shape_and_exact_historical_selection_are_pinned(self):
        raw = (ROOT / ci.MANIFEST_PATH).read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / ci.MANIFEST_PATH
            path.parent.mkdir(parents=True)
            for changed in (raw + b' ', raw[:-1], b'{}'):
                path.write_bytes(changed)
                with self.subTest(length=len(changed)), patch.object(ci, 'ROOT', root), self.assertRaises(RuntimeError):
                    ci.load_manifest()
        for key, value in (('schema_version', True), ('baseline_commit', '0' * 40),
                           ('directories', ['tests']), ('explicit_ids', []), ('count', True),
                           ('fingerprint', '0' * 64), ('extra', 1)):
            bad = fixture_manifest(); bad[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                ci.validate_manifest(bad)
        with self.assertRaises(RuntimeError):
            ci.unique_keys([('ids', []), ('ids', [])])

    def test_workflow_executes_tests_and_keeps_existing_full_ci_unchanged(self):
        raw = (ROOT / ci.WORKFLOW_PATH).read_bytes()
        self.assertEqual(raw, ci.WORKFLOW.encode())
        self.assertIn(b'python scripts/run_history_replay_latest_ci.py --tests\n', raw)
        self.assertIn(b'fetch-depth: 0\n', raw)
        self.assertIn(b'persist-credentials: false\n', raw)
        self.assertIn(b"python-version: '3.11'", raw)
        self.assertIn(b"python-version: '3.12'", raw)
        self.assertIn(b'contents: read\n', raw)
        prior = ci.git('show', ci.BASE_COMMIT + ':.github/workflows/ci.yml')
        self.assertEqual((ROOT / '.github/workflows/ci.yml').read_bytes(), prior)
        self.assertNotIn(ci.BRANCH_REF.encode(), prior)
        # Existing generic jobs are intentionally still eligible on this push.
        self.assertEqual(prior.count(b"github.event_name != 'push' ||"), 2)
        self.assertIn(b'python -m unittest discover -s tests -v', prior)

    def test_hosted_context_rejects_wrong_event_branch_sha_or_dirty_tree(self):
        expected = {'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_NAME': 'push',
                    'GITHUB_REF': ci.BRANCH_REF, 'GITHUB_SHA': 'f' * 40}
        original_workflow = (ROOT / '.github/workflows/ci.yml').read_bytes()
        def fake_git(*args):
            if args[0] == 'show': return original_workflow
            if args[0] == 'rev-parse': return b'f' * 40
            return b''
        with patch.dict(ci.os.environ, expected, clear=True), patch.object(ci, 'git', side_effect=fake_git):
            ci.validate_context()
            for key, value in (('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_REF', 'refs/heads/main'),
                               ('GITHUB_SHA', 'e' * 40)):
                with self.subTest(key=key), patch.dict(ci.os.environ, {key: value}), self.assertRaises(RuntimeError):
                    ci.validate_context()
            def dirty_git(*args): return b' M file\n' if args[0] == 'status' else fake_git(*args)
            with patch.object(ci, 'git', side_effect=dirty_git), self.assertRaises(RuntimeError):
                ci.validate_context()

    def test_actual_unittest_failures_subtests_skips_and_expected_failures_are_rejected(self):
        def passing(self): pass
        def failing(self): self.fail('intentional fixture')
        def subtest(self):
            with self.subTest(case='intentional fixture'): self.fail('intentional fixture')
        def skipped(self): self.skipTest('intentional fixture')
        def error(self): raise RuntimeError('intentional fixture')
        @unittest.expectedFailure
        def expected_failure(self): self.fail('intentional fixture')
        @unittest.expectedFailure
        def unexpected_success(self): pass
        cases = [('pass', passing), ('failure', failing), ('subtest_failure', subtest),
                 ('error', error), ('skip', skipped), ('expected_failure', expected_failure),
                 ('unexpected_success', unexpected_success)]
        for label, method in cases:
            cls = type('ResultFixture', (unittest.TestCase,), {'test_case': method})
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(cls)
            ids = list(ci.test_ids(suite))
            result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=ci.ExactResult).run(suite)
            with self.subTest(label=label):
                if label == 'pass': ci.validate_result(result, ids)
                else:
                    with self.assertRaises(RuntimeError): ci.validate_result(result, ids)

    def test_incomplete_or_substituted_success_cannot_pass_or_claim_full_coverage(self):
        good = SimpleNamespace(testsRun=1, started_ids=['test.x'], passed_ids=['test.x'],
                               failures=[], errors=[], skipped=[], expectedFailures=[],
                               unexpectedSuccesses=[], wasSuccessful=lambda: True)
        ci.validate_result(good, ['test.x'])
        for key, value in (('testsRun', 0), ('testsRun', True), ('started_ids', []),
                           ('passed_ids', ['different.x']), ('errors', [('test.x', 'error')])):
            bad = deepcopy(good); setattr(bad, key, value)
            with self.subTest(key=key, value=value), self.assertRaises(RuntimeError):
                ci.validate_result(bad, ['test.x'])


if __name__ == '__main__':
    unittest.main()
