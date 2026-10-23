"""Exact Tarasov append and predecessor recovery, without scientific approval."""
from collections import Counter
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
BATCH_ID = 'tarasov-pna-bpf-20261023'
PREVIOUS = 'bruns-nbs2-borosilicate-20261023'
BASE_COMMIT = 'faa002c55b7ad2d1bd962e905275894231ab8350'
CANDIDATE_COMMIT = '97f45f07fcdc7ef6f1b0cc72d8d68491438abab4'
EXPECTED_IDS = {
    'identities': ['mat_tarasov2022_pna_bpf_' + str(i) for i in range(1, 6)],
    'grades': [],
    'states': ['state_tarasov2022_pna_bpf_' + str(i) + '_dds_cured' for i in range(1, 6)],
    'properties': ['refprop_tarasov2022_pna_bpf_' + str(i) + '_tensile_strength' for i in range(1, 6)],
    'sources': ['tarasov_2022_pna_bpf_epoxy'],
}


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)


class TarasovPnaBpfPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = successors.data_ledger(BATCH_ID)
        cls.current = {name: json.loads((ROOT / 'materials_boundaries/data' / filename).read_bytes())
                       for name, filename in FILES.items()}
        cls.current = successors.project_successor_catalogs(cls.current, before=BATCH_ID)
        cls.baseline = recover_catalogs(ROOT, cls.current, cls.ledger)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_exact_append_preserves_every_predecessor_byte_and_identity(self):
        self.assertEqual(self.ledger['baseline_commit'], BASE_COMMIT)
        self.assertEqual({name: [row['id'] for row in rows] for name, rows in self.additions.items()}, EXPECTED_IDS)
        self.assertEqual(graph_hashes(self.current), self.ledger['current_sha256'])
        self.assertEqual(graph_hashes(self.baseline), self.ledger['baseline_sha256'])
        self.assertEqual(successors.project_successor_catalogs(self.current, before=PREVIOUS), self.baseline)
        self.assertEqual({name: len(self.current[section][field]) for name, (section, field) in TABLES.items()},
                         {'identities': 1153, 'grades': 31, 'states': 1154, 'properties': 1165, 'sources': 125})
        self.assertEqual(Counter(row['category'] for row in self.current['materials']['identities']),
                         {'natural': 1010, 'metal': 32, 'inorganic': 53, 'polymer': 30, 'composite': 28})
        for name, (section, field) in TABLES.items():
            with self.subTest(collection=name):
                self.assertEqual(self.current[section][field], self.baseline[section][field] + self.additions[name])
        for name, filename in FILES.items():
            previous = git_bytes(BASE_COMMIT, 'materials_boundaries/data/' + filename)
            with self.subTest(filename=filename):
                current_raw = successors.project_successor_catalog_bytes(
                    filename, (ROOT / 'materials_boundaries/data' / filename).read_bytes(), before=BATCH_ID)
                self.assertEqual(sha256(current_raw).hexdigest(), self.ledger['current_sha256'][name])
                self.assertEqual(current_raw, encoded(self.current[name]))
                self.assertEqual(encoded(self.baseline[name]), previous)
                self.assertEqual(successors.project_successor_catalog_bytes(
                    filename, current_raw, before=PREVIOUS), previous)

    def test_partial_reordered_duplicate_and_fact_drift_fail_closed(self):
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
        for mutation in ('owner', 'unit', 'value', 'rights', 'order', 'predecessor', 'metadata'):
            graph = deepcopy(self.current)
            prop = graph['properties']['records'][-1]
            if mutation == 'owner':
                prop['material_state_id'] = graph['materials']['records'][0]['id']
            elif mutation == 'unit':
                prop['reported_value']['unit_code'] = 'GPa'
            elif mutation == 'value':
                prop['reported_value']['number'] = '727'
            elif mutation == 'rights':
                graph['sources']['records'][-1]['license']['identifier'] = 'CC0-1.0'
            elif mutation == 'order':
                graph['materials']['identities'][-5:] = reversed(graph['materials']['identities'][-5:])
            elif mutation == 'predecessor':
                graph['materials']['identities'][0]['name'] += ' altered'
            else:
                graph['materials']['unreviewed_metadata'] = True
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, graph, self.ledger)

    def test_file_ledger_restores_exact_predecessor_files_and_rejects_drift(self):
        ledger = successors.file_ledger(BATCH_ID)
        self.assertEqual(ledger['baseline_commit'], BASE_COMMIT)
        self.assertEqual(set(ledger['updates']), {
            'README.md', 'THIRD_PARTY_NOTICES.md', '.github/workflows/ci.yml',
            'formal-catalog/materials_project_catalog/catalog.py',
            'experimental/platform/query-service/materials_query/pins/legacy_baseline.json',
        })
        for filename, entry in ledger['updates'].items():
            raw = successors.project_successor_file(filename, (ROOT / filename).read_bytes(), before=BATCH_ID)
            previous = git_bytes(BASE_COMMIT, filename)
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
                         successors.file_ledgers(before=BATCH_ID) + [ledger])

    def test_registry_preserves_all_predecessor_descriptors_and_chronology(self):
        old = types.ModuleType('tarasov_predecessor_registry')
        old.__file__ = str(ROOT / 'tests/material_append_successors.py')
        exec(compile(git_bytes(BASE_COMMIT, 'tests/material_append_successors.py'),
                     old.__file__, 'exec'), old.__dict__)
        checkpoint = successors._index(BATCH_ID)
        self.assertEqual(successors.FROZEN_SUCCESSORS[checkpoint + 1:], old.FROZEN_SUCCESSORS)
        self.assertEqual(successors.FROZEN_SUCCESSORS[checkpoint]['batch_id'], BATCH_ID)
        self.assertEqual(successors.data_ledgers()[checkpoint + 1:], old.data_ledgers())
        for descriptor in old.FROZEN_SUCCESSORS:
            batch = descriptor['batch_id']
            with self.subTest(batch=batch):
                self.assertEqual(successors.data_ledger(batch), old.data_ledger(batch))
                self.assertEqual(successors.file_ledger(batch), old.file_ledger(batch))
        nylon = 'zenodo-8089569-nylon-followup-20261021'
        self.assertEqual(successors.file_ledgers(before=nylon),
                         successors.file_ledgers(before=PREVIOUS) + old.file_ledgers(before=nylon))
        with patch.object(successors, 'FROZEN_SUCCESSORS', successors.FROZEN_SUCCESSORS * 2):
            with self.assertRaises(AssertionError):
                successors.data_ledger()
        with patch.object(successors, 'FROZEN_SUCCESSORS', tuple(reversed(successors.FROZEN_SUCCESSORS))):
            with self.assertRaises(AssertionError):
                successors.project_successor_catalogs(self.current)
        with self.assertRaises(AssertionError):
            successors.file_ledgers(before='unreviewed-tarasov-successor')

    def test_candidate_artifacts_and_computed_reviews_remain_unchanged(self):
        batch = ROOT / 'experimental/material-batches' / BATCH_ID
        for filename in ('INTEGRATION_HANDOFF.md', 'README.md', 'VALIDATION.md', 'identity-review.json',
                         'integration-report.json', 'integration.json', 'packet-spec.json',
                         'preparation-receipt.json', 'prepared-packet.json', 'source-review.json',
                         'validation-results.json'):
            with self.subTest(filename=filename):
                git_path = (batch / filename).relative_to(ROOT).as_posix()
                self.assertEqual(git_path, f'experimental/material-batches/{BATCH_ID}/{filename}')
                self.assertEqual((batch / filename).read_bytes(), git_bytes(CANDIDATE_COMMIT, git_path))
        reviews = {}
        for path, expected_count in (
                ('formal-catalog/materials_project_catalog/data/formal_computed_review.json', 24),
                ('experimental/platform/examples/reviewed-computed-v2/normalized-review.json', 24),
                ('experimental/platform/examples/reviewed-computed-v2-second/normalized-review.json', 62),
                ('experimental/platform/examples/reviewed-computed-seed/scoped-review-input.json', 7)):
            with self.subTest(path=path):
                raw = (ROOT / path).read_bytes()
                self.assertEqual(raw, git_bytes(BASE_COMMIT, path))
                reviews[expected_count] = json.loads(raw)['records']
                self.assertEqual(len(reviews[expected_count]), expected_count)
        admitted = {row['candidate_id'] for row in reviews[24]}
        excluded = {row['candidate_id'] for row in reviews[62]}
        self.assertEqual((len(admitted), len(excluded)), (24, 62))
        self.assertFalse(admitted & excluded)
        self.assertFalse((admitted | excluded) & {row['id'] for row in self.current['materials']['identities']})
        self.assertFalse(any(path.suffix.lower() in ('.pdf', '.png', '.jpg', '.xlsx') for path in batch.rglob('*')))
        for prop in self.additions['properties']:
            with self.subTest(property=prop['id']):
                self.assertIs(prop['verification']['independent_scientific_review'], False)
                self.assertIs(prop['verification']['raw_data_reanalysis'], False)


if __name__ == '__main__':
    unittest.main()
