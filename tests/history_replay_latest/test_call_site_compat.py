"""Two exact caller edits preserve every historical predicate and hash."""
import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
from material_append_history import load_frozen, recover_file
from material_append_replay_compat import project_engine_bytes, PREVIOUS_SHA256

BASE = '826333c73a420b7d254c469d9f6f65155983cde1'
LEDGER = 'tests/fixtures/replay_latest_call_sites_20261024.json'
PIN = '10e738eab93631e41b517e8e80cad8ba3d828554f78171927932cfa3c6ee77dd'
PATHS = {'tests/test_kapoor_phosphate_preservation.py', 'tests/test_tian_nano_ti_preservation.py'}

def baseline(path):
    return subprocess.run(['git', 'show', BASE + ':' + path], cwd=ROOT,
                          check=True, capture_output=True, timeout=30).stdout

class LatestCallerCompatibilityTests(unittest.TestCase):
    def test_two_whole_file_images_and_original_hashes_are_frozen(self):
        ledger = load_frozen(ROOT, LEDGER, PIN)
        self.assertEqual(set(ledger), {'schema_version', 'baseline_commit', 'updates'})
        self.assertEqual(ledger['baseline_commit'], BASE)
        self.assertEqual(set(ledger['updates']), PATHS)
        for path, entry in ledger['updates'].items():
            with self.subTest(path=path):
                raw = (ROOT / path).read_bytes()
                old = baseline(path)
                self.assertEqual(recover_file(raw, entry), old)
                self.assertEqual(sha256(old).hexdigest(), entry['previous_sha256'])
                self.assertEqual(sha256(raw).hexdigest(), entry['sha256'])
                self.assertEqual(len(entry['edits']), 1)
                self.assertIn(('ENGINE_SHA256 = ' + repr(PREVIOUS_SHA256)).encode(), old)
                self.assertIn(('ENGINE_SHA256 = ' + repr(PREVIOUS_SHA256)).encode(), raw)

    def test_only_the_two_input_wrappers_change_and_all_assertions_remain(self):
        class StripWrapper(ast.NodeTransformer):
            count = 0
            def visit_ImportFrom(self, node):
                if node.module == 'material_append_replay_compat':
                    if [(x.name, x.asname) for x in node.names] != [('project_engine_bytes', None)]:
                        raise AssertionError('Unexpected compatibility import')
                    return None
                return node
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id == 'project_engine_bytes':
                    if len(node.args) != 1 or node.keywords:
                        raise AssertionError('Unexpected compatibility wrapper')
                    self.count += 1
                    return node.args[0]
                return node
        for path in sorted(PATHS):
            with self.subTest(path=path):
                transformer = StripWrapper()
                tree = transformer.visit(ast.parse((ROOT/path).read_bytes()))
                self.assertEqual(transformer.count, 1)
                self.assertEqual(ast.dump(tree), ast.dump(ast.parse(baseline(path))))

    def test_mutated_callers_edits_and_engine_bytes_cannot_recover_old_pins(self):
        ledger = load_frozen(ROOT, LEDGER, PIN)
        for path, entry in ledger['updates'].items():
            raw = (ROOT/path).read_bytes()
            for bad in (raw+b'!', raw[:-1], bytearray(raw), b'unknown'):
                with self.subTest(path=path, kind=type(bad).__name__), self.assertRaises(AssertionError):
                    recover_file(bad, entry)
            for field in ('offset', 'before', 'after'):
                changed = deepcopy(entry)
                value = changed['edits'][0][field]
                changed['edits'][0][field] = value+1 if field == 'offset' else value+'!'
                with self.subTest(path=path, field=field), self.assertRaises(AssertionError):
                    recover_file(raw, changed)
        engine = (ROOT/'tests/material_append_history.py').read_bytes()
        self.assertEqual(sha256(project_engine_bytes(engine)).hexdigest(), PREVIOUS_SHA256)
        for bad in (engine+b'!', engine[:-1], b'unknown'):
            self.assertIs(project_engine_bytes(bad), bad)
            with self.assertRaises(AssertionError):
                self.assertEqual(sha256(project_engine_bytes(bad)).hexdigest(), PREVIOUS_SHA256)

if __name__ == '__main__':
    unittest.main()
