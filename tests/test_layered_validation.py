"""Routing and evidence boundaries; no full SCC invocation."""
import json
import io
from contextlib import redirect_stdout
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_layered_validation as layer


class LayeredValidationTests(unittest.TestCase):
    def run_main_fixture(self, temp, inventories, statuses):
        output = Path(temp) / 'report.json'
        records = [{'stage': s, 'status': status} for s, status in statuses]
        with patch.object(sys, 'argv', ['layer', '--baseline', str(Path(temp)/'base.json'),
                                      '--output', str(output)]), \
             patch.object(layer, 'baseline', return_value={'README.md': 'old'}), \
             patch.object(layer, 'inventory', side_effect=inventories), \
             patch.object(layer, 'execute_stage', side_effect=records) as execute, \
             redirect_stdout(io.StringIO()):
            code = layer.main()
        return code, json.loads(output.read_bytes()), execute.call_count

    def test_failed_version_stops_history_and_targeted_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            code, report, calls = self.run_main_fixture(temp, [{'README.md': 'new'}]*2,
                                                       [('version', 'failed')])
            self.assertEqual((code, calls), (2, 1))
            self.assertEqual(report['status'], 'preflight_failed')
            self.assertFalse(report['scc_admitted'])

    def test_input_drift_invalidates_otherwise_passing_result(self):
        with tempfile.TemporaryDirectory() as temp:
            code, report, calls = self.run_main_fixture(temp,
                [{'README.md': 'old'}, {'README.md': 'changed-during-run'}],
                [(s, 'passed') for s in ['version', 'history', 'manifest']])
            self.assertEqual((code, calls), (2, 3))
            self.assertEqual(report['status'], 'input_drift')

    def test_actual_version_assertion_rejects_wrong_readme(self):
        import test_release_metadata as metadata
        original = Path.read_text
        def read(path, *args, **kwargs):
            if path == metadata.ROOT / 'README.md':
                return 'Package version in this local source snapshot: **v0.0.0**'
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            result = unittest.TestResult()
            unittest.TestLoader().loadTestsFromNames([layer.VERSION_IDS[1]]).run(result)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.errors, [])

    def test_actual_history_gate_rejects_tampered_ledger(self):
        import scc_flow_history as scc
        target = layer.ROOT / scc.DIRECTORY / 'files-history.json'
        original = Path.read_bytes
        def read(path):
            raw = original(path)
            return raw + b' ' if path == target else raw
        with patch.object(Path, 'read_bytes', read):
            with self.assertRaisesRegex(AssertionError, 'Unreviewed append-history ledger'):
                layer.history_checks()

    def test_prose_update_has_no_full_suite(self):
        p = layer.plan({'README.md': 'old'}, {'README.md': 'new'})
        self.assertFalse(p['requires_full_acceptance'])
        self.assertFalse(p['full_suite_started'])
        self.assertEqual(p['targeted_modules'], [])

    def test_unknown_science_workflow_and_deleted_paths_require_review(self):
        for name in ['materials_boundaries/data/materials.json', 'schemas/x.json',
                     '.github/workflows/ci.yml', 'tests/test_unknown.py', 'new.txt']:
            with self.subTest(name=name):
                self.assertTrue(layer.plan({}, {name: 'new'})['requires_full_acceptance'])
        self.assertTrue(layer.plan({'README.md': 'old'}, {})['requires_full_acceptance'])

    def test_mixed_changes_do_not_get_document_exemption(self):
        self.assertTrue(layer.plan({}, {'docs/a.md': 'x', 'engine.py': 'y'})['requires_full_acceptance'])

    def test_opt_in_tool_selects_only_its_targeted_tests(self):
        self.assertEqual(layer.plan({}, {'scripts/run_layered_validation.py': 'x'})[
            'targeted_modules'], ['test_layered_validation'])

    def test_inventory_binds_added_deleted_and_modified_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); path = root / 'README.md'; path.write_text('a')
            first = layer.inventory(root); path.write_text('b')
            self.assertNotEqual(layer.fingerprint(first), layer.fingerprint(layer.inventory(root)))
            path.unlink()
            self.assertNotEqual(first, layer.inventory(root))
            (root / 'new.py').write_text('x')
            self.assertIn('new.py', layer.inventory(root))

    def test_baseline_tampering_and_unsafe_paths_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'baseline.json'
            for files, pin in [({'a': 'a'*64}, 'bad'), ({'../a': 'a'*64}, None)]:
                path.write_text(json.dumps({'input_files_sha256': files,
                    'input_fingerprint': pin or layer.fingerprint(files)}))
                with self.assertRaises(ValueError): layer.baseline(path)

    def test_timeout_is_failure_not_skip(self):
        with patch.object(layer.subprocess, 'run', side_effect=subprocess.TimeoutExpired('worker', 1)):
            self.assertEqual(layer.execute_stage('history', 1)['status'], 'timeout')

    def test_stage_command_cannot_invoke_full_partition(self):
        with patch.object(layer.subprocess, 'run') as run:
            run.return_value.returncode = 0
            self.assertEqual(layer.execute_stage('version', 5)['status'], 'passed')
            command = run.call_args.args[0]
            self.assertEqual(command[-2:], ['--worker', 'version'])
            self.assertNotIn('--partition', command)
