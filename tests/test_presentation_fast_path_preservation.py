"""Authenticate the finite test-only presentation predecessor bridge."""
import ast
from copy import deepcopy
from pathlib import Path
import unittest

import evidence_dedup_preservation as dedup
import material_bulk_preservation as bulk
import presentation_fast_path_preservation as successor
from material_class_counts_preservation import pre_class_counts_bytes

ROOT = Path(__file__).resolve().parents[1]
HELPER_SHA256 = '38ba1d0fd76af94664b3e6c4288a6b7fe3b335f3055bb357333e68c404ec482f'
LEDGER_SHA256 = 'cb21d602f80d59f66889908de1c8a025de5080570c76db4eb4cf5ae3df437544'


class PresentationFastPathPreservationTests(unittest.TestCase):
    def test_helper_ledger_and_four_exact_predecessors_are_pinned(self):
        helper = pre_class_counts_bytes('tests/presentation_fast_path_preservation.py',
                                       (ROOT / 'tests/presentation_fast_path_preservation.py').read_bytes())
        self.assertEqual(successor.digest(helper), HELPER_SHA256)
        self.assertEqual(successor.digest((ROOT / successor.LEDGER_PATH).read_bytes()), LEDGER_SHA256)
        entries = successor.validate_ledger(successor.load_ledger())
        self.assertEqual(len(entries), 4)
        self.assertEqual(successor.BASELINE_COMMIT, '73f3b0b56f764736e1d4368d0da8fabf1cdf9c7b')
        for name, entry in entries.items():
            with self.subTest(filename=name):
                current = (ROOT / name).read_bytes()
                if name == 'tests/material_bulk_preservation.py':
                    current = pre_class_counts_bytes(name, current)
                previous = successor.pre_presentation_fast_path_bytes(name, current)
                self.assertEqual(successor.digest(current), entry['sha256'])
                self.assertEqual(successor.digest(previous), entry['previous_sha256'])
                self.assertEqual(successor.apply_exact_edits(previous, entry['edits']), current)
                self.assertEqual(successor.pre_presentation_fast_path_bytes(name, previous), previous)

    def test_older_ledger_bytes_and_composed_presentation_pins_remain_exact(self):
        for filename, expected in (
            ('tests/evidence_dedup_preservation.py', '4c6c17b3310057faf4b7d80dd9bfc77ec5fdc6f28fe8f0ef102c2ebe85c8b245'),
            ('tests/fixtures/evidence_dedup_updates_v1.json', '3c7ecc146f216e113a99c636815cce7df9b4c1ee06ec55a736cc781f16c77890'),
            ('tests/fixtures/material_bulk_updates_v0350.json', 'fa5b5d010dff9dd12e859a41ad02077b5350acc01bac50d001e1fa48184747d4'),
        ):
            with self.subTest(filename=filename):
                self.assertEqual(successor.digest((ROOT / filename).read_bytes()), expected)
        filename = 'materials_boundaries/material_presentation.py'
        current = (ROOT / filename).read_bytes()
        original = successor.pre_presentation_fast_path_bytes(filename, current)
        self.assertEqual(bulk.release_bytes(filename, current), bulk.release_bytes(filename, original))
        self.assertEqual(successor.digest(bulk.pre_material_bulk_bytes(filename, current)),
                         bulk.load_ledger()['baseline_sha256'][filename])
        for filename in ('tests/material_bulk_preservation.py', 'tests/test_material_bulk_preservation.py'):
            original = successor.pre_presentation_fast_path_bytes(filename, (ROOT / filename).read_bytes())
            self.assertEqual(successor.digest(original), dedup.validate_ledger(dedup.load_ledger())[filename]['sha256'])

    def test_unreviewed_bytes_types_paths_and_edit_mutations_fail_closed(self):
        for name, entry in successor.validate_ledger(successor.load_ledger()).items():
            current = (ROOT / name).read_bytes()
            previous = successor.pre_presentation_fast_path_bytes(name, current)
            for bad in (current + b'!', current[:-1], b'arbitrary replacement', current.decode('utf-8'),
                        bytearray(current), memoryview(current)):
                with self.subTest(filename=name, operation='bad_bytes', input_type=type(bad).__name__):
                    with self.assertRaises(AssertionError):
                        successor.pre_presentation_fast_path_bytes(name, bad)
            for mutate in (lambda x: x[0].update(offset=True),
                           lambda x: x[0].update(offset=len(previous) + 1),
                           lambda x: x[0].update(before=x[0]['before'] + '!'),
                           lambda x: x.append(deepcopy(x[0]))):
                edits = deepcopy(entry['edits']); mutate(edits)
                with self.subTest(filename=name, operation='bad_edits'):
                    with self.assertRaises(AssertionError):
                        successor.apply_exact_edits(previous, edits)
        for name in ('README.md', '../materials_boundaries/material_presentation.py', None, []):
            with self.assertRaises(AssertionError):
                successor.pre_presentation_fast_path_bytes(name, b'unknown')
        with self.assertRaises(AssertionError):
            bulk.release_bytes('materials_boundaries/material_presentation.py', b'unknown')

    def test_ledger_drift_and_duplicate_keys_are_rejected_without_mutation(self):
        original = successor.load_ledger(); before = deepcopy(original)
        mutations = (lambda x: x.update(extra=True),
                     lambda x: x.update(schema_version=True),
                     lambda x: x.update(baseline_commit='0' * 40),
                     lambda x: x['updates'].pop(),
                     lambda x: x['updates'].append(deepcopy(x['updates'][0])),
                     lambda x: x['updates'][0].update(filename='README.md'),
                     lambda x: x['updates'][0].update(previous_sha256='0' * 64),
                     lambda x: x['updates'][0].update(sha256='0' * 64),
                     lambda x: x['updates'][0]['edits'][0].update(offset=True),
                     lambda x: x['updates'][0]['edits'][0].update(offset=0),
                     lambda x: x['updates'][0]['edits'][0].update(after='unreviewed'),
                     lambda x: x['updates'][0].update(sha256=float('nan')))
        for mutate in mutations:
            bad = deepcopy(original); mutate(bad)
            with self.assertRaises(AssertionError):
                successor.validate_ledger(bad)
        with self.assertRaises(AssertionError):
            successor.unique_keys([('updates', []), ('updates', [])])
        self.assertEqual(original, before)

    def test_existing_test_methods_and_assertions_are_unchanged(self):
        def contracts(raw):
            tree = ast.parse(raw)
            methods = [(node.name, item.name) for node in tree.body if isinstance(node, ast.ClassDef)
                       for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
            calls = []
            class Assertions(ast.NodeVisitor):
                def visit_Call(self, node):
                    if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                            and node.func.value.id == 'self' and node.func.attr.startswith('assert')):
                        calls.append(ast.dump(node, include_attributes=False))
                    self.generic_visit(node)
            Assertions().visit(tree)
            return methods, calls

        for filename in ('tests/test_material_bulk_preservation.py', 'tests/test_evidence_dedup_preservation.py'):
            current = (ROOT / filename).read_bytes()
            previous = successor.pre_presentation_fast_path_bytes(filename, current)
            self.assertEqual(contracts(current), contracts(previous))

    def test_production_never_imports_this_test_only_layer(self):
        for path in (ROOT / 'materials_boundaries').glob('*.py'):
            self.assertNotIn('presentation_fast_path_preservation', path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
