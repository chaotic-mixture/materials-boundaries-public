"""Exact Bruns append and historical predecessor recovery; no scientific approval."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import types
import unittest
from unittest.mock import patch

import material_append_successors as successors
from material_append_history import (
    FILES, TABLES, appended_rows, encoded, graph_hashes, recover_catalogs, recover_file,
)

ROOT = Path(__file__).resolve().parents[1]
BATCH_ID = 'bruns-nbs2-borosilicate-20261023'
PREVIOUS = 'zenodo-8089569-nylon-followup-20261021'
BASE_COMMIT = '46674771ab851d4c267425b985c8f29c8aea25df'


class BrunsBorosilicatePreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = successors.data_ledger(BATCH_ID)
        cls.current = {name: json.loads((ROOT / 'materials_boundaries/data' / filename).read_bytes())
                       for name, filename in FILES.items()}
        cls.baseline = recover_catalogs(ROOT, cls.current, cls.ledger)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_exact_append_and_predecessor_bytes_keep_all_existing_materials(self):
        self.assertEqual(self.ledger['baseline_commit'], BASE_COMMIT)
        self.assertEqual({name: len(rows) for name, rows in self.additions.items()},
                         {'identities': 4, 'grades': 0, 'states': 4, 'properties': 4, 'sources': 1})
        self.assertEqual(graph_hashes(self.current), self.ledger['current_sha256'])
        self.assertEqual(graph_hashes(self.baseline), self.ledger['baseline_sha256'])
        self.assertEqual(successors.project_successor_catalogs(self.current, before=PREVIOUS), self.baseline)
        self.assertEqual(len(self.current['materials']['identities']), 1148)
        for name, filename in FILES.items():
            expected = subprocess.check_output(['git', 'show', BASE_COMMIT + ':materials_boundaries/data/' + filename], cwd=ROOT)
            self.assertEqual(encoded(self.baseline[name]), expected)
            self.assertEqual(successors.project_successor_catalog_bytes(
                filename, encoded(self.current[name]), before=PREVIOUS), expected)
        self.assertEqual({r['category'] for r in self.additions['identities']}, {'inorganic'})
        self.assertEqual({r['id'] for r in self.additions['sources']}, {'bruns_2020_alumina_borosilicate'})

    def test_partial_reordered_owner_unit_and_rights_drift_fail_closed(self):
        for collection, rows in self.additions.items():
            if not rows:
                continue
            section, field = TABLES[collection]
            for mutation in ('missing', 'changed', 'duplicate'):
                graph = deepcopy(self.current)
                selected = next(row for row in graph[section][field] if row['id'] == rows[0]['id'])
                if mutation == 'missing':
                    graph[section][field].remove(selected)
                elif mutation == 'changed':
                    selected['version'] = 'unreviewed'
                else:
                    graph[section][field].append(deepcopy(selected))
                with self.subTest(collection=collection, mutation=mutation), self.assertRaises(AssertionError):
                    recover_catalogs(ROOT, graph, self.ledger)
        for mutation in ('owner', 'unit', 'rights', 'order', 'predecessor'):
            graph = deepcopy(self.current)
            if mutation in ('owner', 'unit'):
                prop = graph['properties']['records'][-1]
                if mutation == 'owner':
                    prop['material_state_id'] = graph['materials']['records'][0]['id']
                else:
                    prop['reported_value']['unit_code'] = 'kg/m^3'
            elif mutation == 'rights':
                graph['sources']['records'][-1]['license']['identifier'] = 'CC0-1.0'
            elif mutation == 'order':
                graph['materials']['identities'][-4:] = reversed(graph['materials']['identities'][-4:])
            else:
                graph['materials']['identities'][0]['name'] += ' altered'
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, graph, self.ledger)

    def test_file_ledger_restores_exact_readme_and_workflow_and_rejects_drift(self):
        ledger = successors.file_ledger(BATCH_ID)
        self.assertEqual(set(ledger['updates']), {'README.md', '.github/workflows/ci.yml'})
        self.assertEqual(ledger['baseline_commit'], BASE_COMMIT)
        self.assertEqual(successors.file_ledgers(before=BATCH_ID), [])
        for filename, entry in ledger['updates'].items():
            raw = (ROOT / filename).read_bytes()
            previous = subprocess.check_output(['git', 'show', BASE_COMMIT + ':' + filename], cwd=ROOT)
            with self.subTest(filename=filename):
                self.assertEqual(recover_file(raw, entry), previous)
                self.assertEqual(sha256(previous).hexdigest(), entry['previous_sha256'])
                self.assertEqual(recover_file(previous, entry), previous)
                with self.assertRaises(AssertionError):
                    recover_file(raw + b' unreviewed', entry)
                changed = deepcopy(entry)
                changed['edits'][0]['offset'] += 1
                with self.assertRaises(AssertionError):
                    recover_file(raw, changed)
        self.assertEqual(successors.file_ledgers(before=PREVIOUS),
                         [ledger, successors.load_frozen(ROOT, successors.CODE_FILE_LEDGER, successors.CODE_FILE_SHA256)])

    def test_finite_registry_preserves_every_preexisting_descriptor_and_boundary(self):
        old = types.ModuleType('bruns_predecessor_registry')
        old.__file__ = str(ROOT / 'tests/material_append_successors.py')
        code = subprocess.check_output(['git', 'show', BASE_COMMIT + ':tests/material_append_successors.py'], cwd=ROOT)
        exec(compile(code, old.__file__, 'exec'), old.__dict__)
        self.assertEqual(successors.FROZEN_SUCCESSORS[1:], old.FROZEN_SUCCESSORS)
        self.assertEqual(successors.FROZEN_SUCCESSORS[0]['batch_id'], BATCH_ID)
        self.assertEqual(successors.data_ledgers()[1:], old.data_ledgers())
        for descriptor in old.FROZEN_SUCCESSORS:
            batch = descriptor['batch_id']
            self.assertEqual(successors.data_ledger(batch), old.data_ledger(batch))
            self.assertEqual(successors.file_ledger(batch), old.file_ledger(batch))
        with patch.object(successors, 'FROZEN_SUCCESSORS', successors.FROZEN_SUCCESSORS * 2):
            with self.assertRaises(AssertionError):
                successors.data_ledger()
        with patch.object(successors, 'FROZEN_SUCCESSORS', tuple(reversed(successors.FROZEN_SUCCESSORS))):
            with self.assertRaises(AssertionError):
                successors.project_successor_catalogs(self.current)
        with self.assertRaises(AssertionError):
            successors.file_ledgers(before='unreviewed-bruns-successor')

    def test_original_candidate_and_source_assets_remain_unchanged(self):
        batch = ROOT / 'experimental/material-batches' / BATCH_ID
        for filename in ('README.md', 'packet-spec.json', 'prepared-packet.json', 'source-review.json',
                         'preparation-receipt.json', 'integration.json', 'integration-report.json',
                         'VALIDATION.md', 'validation-results.json'):
            old = subprocess.check_output(['git', 'show', 'ab458b08d388b0ac4009a7f9c98138211ae46fa4:' + str((batch / filename).relative_to(ROOT))], cwd=ROOT)
            self.assertEqual((batch / filename).read_bytes(), old, filename)
        self.assertFalse(any(path.suffix in ('.pdf', '.png', '.jpg') for path in batch.rglob('*')))
        self.assertFalse(any(row['verification']['independent_scientific_review'] for row in self.additions['properties']))
        self.assertFalse(any(row['verification']['raw_data_reanalysis'] for row in self.additions['properties']))


if __name__ == '__main__':
    unittest.main()
