"""Exact, test-only predecessor recovery for the evidence-signature correction."""
from copy import deepcopy
from pathlib import Path
import unittest

import evidence_dedup_preservation as successor
import material_batch_preservation as batch
import material_bulk_preservation as bulk
from presentation_fast_path_preservation import ALLOWED_PATHS as PRESENTATION_PATHS, pre_presentation_fast_path_bytes

ROOT = Path(__file__).resolve().parents[1]
HELPER_SHA256 = '4c6c17b3310057faf4b7d80dd9bfc77ec5fdc6f28fe8f0ef102c2ebe85c8b245'
LEDGER_SHA256 = '3c7ecc146f216e113a99c636815cce7df9b4c1ee06ec55a736cc781f16c77890'


class EvidenceDedupPreservationTests(unittest.TestCase):
    def test_helper_ledger_and_five_exact_predecessors_are_pinned(self):
        self.assertEqual(successor.digest((ROOT / 'tests/evidence_dedup_preservation.py').read_bytes()), HELPER_SHA256)
        self.assertEqual(successor.digest((ROOT / successor.LEDGER_PATH).read_bytes()), LEDGER_SHA256)
        entries = successor.validate_ledger(successor.load_ledger())
        self.assertEqual(len(entries), 5)
        for name, entry in entries.items():
            with self.subTest(filename=name):
                current = (ROOT / name).read_bytes()
                if name in PRESENTATION_PATHS:
                    current = pre_presentation_fast_path_bytes(name, current)
                previous = successor.pre_evidence_dedup_bytes(name, current)
                self.assertEqual(successor.digest(current), entry['sha256'])
                self.assertEqual(successor.digest(previous), entry['previous_sha256'])
                self.assertEqual(successor.apply_exact_edits(previous, entry['edits']), current)
                self.assertEqual(successor.pre_evidence_dedup_bytes(name, previous), previous)

    def test_existing_355_and_402_file_pins_remain_exact(self):
        for history, reverse in ((batch, batch.pre_material_batch_bytes),
                                 (bulk, bulk.pre_material_bulk_bytes)):
            ledger = history.load_ledger()
            for name, expected in ledger['baseline_sha256'].items():
                with self.subTest(release=history.BASELINE_FILE_COUNT, filename=name):
                    self.assertEqual(successor.digest(reverse(name, (ROOT / name).read_bytes())), expected)

    def test_unreviewed_successors_inputs_and_edit_mutations_fail_closed(self):
        for name, entry in successor.validate_ledger(successor.load_ledger()).items():
            current = (ROOT / name).read_bytes()
            if name in PRESENTATION_PATHS:
                current = pre_presentation_fast_path_bytes(name, current)
            previous = successor.pre_evidence_dedup_bytes(name, current)
            for bad in (current + b'!', current[:-1], b'arbitrary replacement', current.decode('utf-8')):
                with self.subTest(filename=name, operation='bad_bytes'):
                    with self.assertRaises(AssertionError):
                        successor.pre_evidence_dedup_bytes(name, bad)
            for mutate in (lambda x: x[0].update(offset=True),
                           lambda x: x[0].update(offset=len(previous) + 1),
                           lambda x: x[0].update(before=x[0]['before'] + '!'),
                           lambda x: x.append(deepcopy(x[0]))):
                edits = deepcopy(entry['edits']); mutate(edits)
                with self.subTest(filename=name, operation='bad_edits'):
                    with self.assertRaises(AssertionError):
                        successor.apply_exact_edits(previous, edits)
        for name in ('README.md', '../materials_boundaries/material_references.py', None, []):
            with self.assertRaises(AssertionError):
                successor.pre_evidence_dedup_bytes(name, b'unknown')

    def test_ledger_drift_and_duplicate_keys_are_rejected_without_mutation(self):
        original = successor.load_ledger(); before = deepcopy(original)
        mutations = (lambda x: x.update(extra=True),
                     lambda x: x.update(schema_version=True),
                     lambda x: x.update(baseline_commit='0' * 40),
                     lambda x: x['updates'].pop(),
                     lambda x: x['updates'].append(deepcopy(x['updates'][0])),
                     lambda x: x['updates'][0].update(filename='README.md'),
                     lambda x: x['updates'][0].update(sha256='0' * 64),
                     lambda x: x['updates'][0]['edits'][0].update(offset=x['updates'][0]['edits'][0]['offset'] + 1),
                     lambda x: x['updates'][0]['edits'][0].update(offset=0))
        for mutate in mutations:
            bad = deepcopy(original); mutate(bad)
            with self.assertRaises(AssertionError):
                successor.validate_ledger(bad)
        with self.assertRaises(AssertionError):
            successor.unique_keys([('updates', []), ('updates', [])])
        self.assertEqual(original, before)


if __name__ == '__main__':
    unittest.main()
