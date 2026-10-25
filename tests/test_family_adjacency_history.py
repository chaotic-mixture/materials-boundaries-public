"""Exact workflow history for a code-only relationship query successor.

The bridge cannot authorize a material append or relax an older file check.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

import material_append_successors as successors
from material_append_history import load_frozen, recover_file
from curaua_history import checkpoint_registry, require_checkpoint_bytes


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '7248dcd06e7ab4bc5f3fae1f3f21a7d9e0dbad3c'
LATEST_MATERIAL_BATCH = 'zenodo-8089569-nylon-followup-20261021'
WORKFLOW = '.github/workflows/ci.yml'


def baseline_bytes(filename):
    return subprocess.check_output(
        ['git', 'show', BASE_COMMIT + ':' + filename], cwd=ROOT, timeout=30)


class FamilyAdjacencyHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = load_frozen(ROOT, successors.CODE_FILE_LEDGER,
                                 successors.CODE_FILE_SHA256)

    def test_code_only_workflow_round_trip_retains_old_rejection(self):
        entry = self.ledger['updates'][WORKFLOW]
        current = recover_file(
            successors.project_successor_file(
                WORKFLOW, (ROOT / WORKFLOW).read_bytes(), before=successors.BRUNS_BATCH_ID),
            successors.file_ledger(successors.BRUNS_BATCH_ID)['updates'][WORKFLOW])
        baseline = baseline_bytes(WORKFLOW)
        self.assertEqual(recover_file(current, entry), baseline)
        self.assertEqual(recover_file(baseline, entry), baseline)
        self.assertEqual(successors.project_successor_file(
            WORKFLOW, current, before=LATEST_MATERIAL_BATCH), baseline)
        # Unknown bytes pass to the unchanged historical caller and still fail.
        altered = current + b'# unreviewed workflow change\n'
        projected = successors.project_successor_file(
            WORKFLOW, altered, before=LATEST_MATERIAL_BATCH)
        self.assertEqual(projected, altered)
        old_entry = successors.file_ledger(LATEST_MATERIAL_BATCH)['updates'][WORKFLOW]
        with self.assertRaises(AssertionError):
            recover_file(projected, old_entry)

    def test_all_material_workflow_views_keep_their_exact_file_pins(self):
        current = (ROOT / WORKFLOW).read_bytes()
        historical = checkpoint_registry()
        curaua = {'batch_id': successors.CURAUA_BATCH_ID,
                  'data': (successors.CURAUA_DATA_LEDGER, successors.CURAUA_DATA_SHA256),
                  'files': (successors.CURAUA_FILE_LEDGER, successors.CURAUA_FILE_SHA256)}
        self.assertEqual(successors.FROZEN_SUCCESSORS, (curaua,) + historical.FROZEN_SUCCESSORS)
        # Curaua leaves this workflow unchanged; it has no material-edit entry.
        # Verify that exact boundary separately, then retain every older pin.
        self.assertEqual(current, require_checkpoint_bytes(WORKFLOW, current))
        for descriptor in historical.FROZEN_SUCCESSORS:
            batch_id = descriptor['batch_id']
            entry = successors.file_ledger(batch_id)['updates'][WORKFLOW]
            with self.subTest(batch_id=batch_id):
                projected = successors.project_successor_file(
                    WORKFLOW, current, before=batch_id)
                self.assertEqual(sha256(projected).hexdigest(), entry['sha256'])
                self.assertEqual(sha256(recover_file(projected, entry)).hexdigest(),
                                 entry['previous_sha256'])

    def test_data_registry_and_every_material_ledger_remain_unchanged(self):
        previous = types.ModuleType('family_adjacency_predecessor_registry')
        previous.__file__ = str(ROOT / 'tests/material_append_successors.py')
        code = baseline_bytes('tests/material_append_successors.py')
        exec(compile(code, previous.__file__, 'exec'), previous.__dict__)
        checkpoint = successors._index(successors.BRUNS_BATCH_ID)
        self.assertEqual(successors.FROZEN_SUCCESSORS[checkpoint]["batch_id"], successors.BRUNS_BATCH_ID)
        self.assertEqual(successors.FROZEN_SUCCESSORS[checkpoint + 1:], previous.FROZEN_SUCCESSORS)
        self.assertEqual(successors.data_ledgers()[checkpoint + 1:], previous.data_ledgers())
        self.assertEqual(successors.data_ledger(LATEST_MATERIAL_BATCH), previous.data_ledger())
        self.assertEqual(successors.file_ledger(LATEST_MATERIAL_BATCH), previous.file_ledger())
        for descriptor in previous.FROZEN_SUCCESSORS:
            batch_id = descriptor['batch_id']
            with self.subTest(batch_id=batch_id):
                self.assertEqual(successors.data_ledgers(before=batch_id)[checkpoint + 1:],
                                 previous.data_ledgers(before=batch_id))
                self.assertEqual(successors.file_ledger(batch_id),
                                 previous.file_ledger(batch_id))

    def test_only_one_workflow_has_a_pinned_code_successor(self):
        self.assertEqual(set(self.ledger), {'schema_version', 'baseline_commit', 'updates'})
        self.assertEqual(self.ledger['schema_version'], 1)
        self.assertEqual(self.ledger['baseline_commit'], BASE_COMMIT)
        self.assertEqual(set(self.ledger['updates']), {WORKFLOW})
        self.assertEqual(successors.file_ledgers(before=LATEST_MATERIAL_BATCH),
                         successors.file_ledgers(before=successors.BRUNS_BATCH_ID)
                         + [successors.file_ledger(successors.BRUNS_BATCH_ID), self.ledger])
        untouched = b'An unrelated file is not a workflow successor.\n'
        self.assertEqual(successors.project_successor_file(
            'unrelated.txt', untouched, before=LATEST_MATERIAL_BATCH), untouched)
        # Code-only history does not invent an additional material batch name.
        with self.assertRaises(AssertionError):
            successors.data_ledger('family-adjacency-20261023')

    def test_unknown_boundaries_and_ledger_or_edit_drift_are_rejected(self):
        with self.assertRaises(AssertionError):
            successors.file_ledgers(before='unknown-unreviewed-batch')
        entry = deepcopy(self.ledger['updates'][WORKFLOW])
        entry['edits'][0]['offset'] += 1
        with self.assertRaises(AssertionError):
            recover_file((ROOT / WORKFLOW).read_bytes(), entry)
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            path = temporary / successors.CODE_FILE_LEDGER
            path.parent.mkdir(parents=True)
            path.write_bytes((ROOT / successors.CODE_FILE_LEDGER).read_bytes() + b' ')
            # Copy the complete newer prefix so the intentional code-ledger
            # hash drift, rather than a missing successor file, causes failure.
            for descriptor in successors._prefix(LATEST_MATERIAL_BATCH):
                filename = descriptor['files'][0]
                target = temporary / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / filename).read_bytes())
            with patch.object(successors, 'ROOT', temporary), self.assertRaises(AssertionError):
                successors.file_ledgers(before=LATEST_MATERIAL_BATCH)


if __name__ == '__main__':
    unittest.main()
