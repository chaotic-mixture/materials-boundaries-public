"""Exact Kapoor append, finite ordering and unchanged predecessor evidence."""
import ast
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

import material_append_successors as successors
from material_append_history import (
    FILES, TABLES, appended_rows, encoded, graph_hashes, load_frozen,
    recover_catalogs, recover_file,
)

ROOT = Path(__file__).resolve().parents[1]
BATCH_ID = 'kapoor-phosphate-glasses-20261024'
PREVIOUS = 'tarasov-pna-bpf-20261023'
DATA_BASE_COMMIT = '196995256836db2d8f870ac9a91f664bfdd03e7f'
CANDIDATE_COMMIT = 'c275ae6051277ad6d08077b2937527907eb2380f'
PACKET_PATH = 'experimental/material-batches/' + BATCH_ID + '/prepared-packet.json'
PACKET_SHA256 = '03284799a8d5c34a7927c56823339bb0067d2d98582c57e0e0c52ec701e29c6b'
ENGINE_SHA256 = '38d9b1768121f84cc5b45d21d8d992b8d62cf6ed62ad0ed1ec78f7760ece9ea9'
LABEL_ORDER = ('al10', 'al15', 'al5', 'p46', 'p50', 'p60')
EXPECTED_IDS = {
    'identities': ['mat_kapoor2019_' + label for label in LABEL_ORDER],
    'grades': [],
    'states': ['state_kapoor2019_' + label + '_as_prepared' for label in LABEL_ORDER],
    'properties': ['refprop_kapoor2019_' + label + '_mass_density' for label in LABEL_ORDER],
    'sources': ['kapoor_2019_calcium_aluminophosphate'],
}


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT, timeout=30)


class KapoorPhosphatePreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = successors.data_ledger(BATCH_ID)
        cls.current = {key: json.loads((ROOT / 'materials_boundaries/data' / filename).read_bytes())
                       for key, filename in FILES.items()}
        cls.current = successors.project_successor_catalogs(cls.current, before=BATCH_ID)
        cls.baseline = recover_catalogs(ROOT, cls.current, cls.ledger)
        cls.additions = appended_rows(ROOT, cls.ledger)

    def test_exact_append_preserves_every_predecessor_byte_and_identity(self):
        self.assertEqual(self.ledger['baseline_commit'], DATA_BASE_COMMIT)
        self.assertEqual({name: [row['id'] for row in rows] for name, rows in self.additions.items()}, EXPECTED_IDS)
        self.assertEqual(graph_hashes(self.current), self.ledger['current_sha256'])
        self.assertEqual(graph_hashes(self.baseline), self.ledger['baseline_sha256'])
        self.assertEqual(successors.project_successor_catalogs(self.current, before=PREVIOUS), self.baseline)
        self.assertEqual({name: len(self.current[section][field]) for name, (section, field) in TABLES.items()},
                         {'identities': 1159, 'grades': 31, 'states': 1160, 'properties': 1171, 'sources': 126})
        self.assertEqual(Counter(row['category'] for row in self.current['materials']['identities']),
                         {'natural': 1010, 'metal': 32, 'inorganic': 59, 'polymer': 30, 'composite': 28})
        for name, (section, field) in TABLES.items():
            with self.subTest(collection=name):
                self.assertEqual(self.current[section][field], self.baseline[section][field] + self.additions[name])
        for name, filename in FILES.items():
            previous = git_bytes(DATA_BASE_COMMIT, 'materials_boundaries/data/' + filename)
            with self.subTest(filename=filename):
                raw = successors.project_successor_catalog_bytes(
                    filename, (ROOT / 'materials_boundaries/data' / filename).read_bytes(), before=BATCH_ID)
                self.assertEqual(raw, encoded(self.current[name]))
                self.assertEqual(encoded(self.baseline[name]), previous)
                self.assertEqual(successors.project_successor_catalog_bytes(filename, raw, before=PREVIOUS), previous)

    def test_six_finite_descriptors_preserve_one_packet_and_runtime_id_order(self):
        packet = json.loads((ROOT / PACKET_PATH).read_bytes())
        descriptors = self.ledger['packets']
        self.assertEqual(len(descriptors), 6)
        self.assertEqual({(entry['path'], entry['sha256']) for entry in descriptors}, {(PACKET_PATH, PACKET_SHA256)})
        self.assertEqual(sha256((ROOT / PACKET_PATH).read_bytes()).hexdigest(), PACKET_SHA256)
        # The compiler retains source table order; production merge sorts IDs.
        # Six finite selections preserve that existing contract without editing
        # the candidate packet or the historically pinned recovery engine.
        self.assertEqual([row['source_designation'] for row in packet['catalogs']['materials']['records']],
                         ['P60', 'P50', 'P46', 'Al5', 'Al10', 'Al15'])
        for name, (section, field) in TABLES.items():
            ids = [item for entry in descriptors for item in entry['added_ids'][name]]
            with self.subTest(collection=name):
                self.assertEqual(ids, EXPECTED_IDS[name])
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual(sorted(self.additions[name], key=lambda row: row['id']),
                                 sorted(packet['catalogs'][section][field], key=lambda row: row['id']))
        self.assertEqual([len(entry['added_ids']['sources']) for entry in descriptors], [1, 0, 0, 0, 0, 0])
        for mutation in ('missing', 'duplicate', 'reordered', 'source_duplicated'):
            ledger = deepcopy(self.ledger)
            if mutation == 'missing':
                ledger['packets'].pop()
            elif mutation == 'duplicate':
                ledger['packets'].append(deepcopy(ledger['packets'][0]))
            elif mutation == 'reordered':
                ledger['packets'].reverse()
            else:
                ledger['packets'][1]['added_ids']['sources'] = EXPECTED_IDS['sources']
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'ledger.json'
                path.write_bytes(encoded(ledger))
                with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                    load_frozen(Path(directory), path.name, successors.KAPOOR_DATA_SHA256)
            if mutation != 'reordered':
                with self.subTest(recovery_mutation=mutation), self.assertRaises(AssertionError):
                    recover_catalogs(ROOT, self.current, ledger)
        self.assertEqual(sha256((ROOT / 'tests/material_append_history.py').read_bytes()).hexdigest(), ENGINE_SHA256)

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
                prop['reported_value']['unit_code'] = 'MPa'
            elif mutation == 'value':
                prop['reported_value']['number'] = '0.002'
            elif mutation == 'rights':
                graph['sources']['records'][-1]['license']['identifier'] = 'CC0-1.0'
            elif mutation == 'order':
                graph['materials']['identities'][-6:] = reversed(graph['materials']['identities'][-6:])
            elif mutation == 'predecessor':
                graph['materials']['identities'][0]['name'] += ' altered'
            else:
                graph['materials']['unreviewed_metadata'] = True
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, graph, self.ledger)

    def test_file_ledger_restores_exact_predecessor_files_and_rejects_drift(self):
        ledger = successors.file_ledger(BATCH_ID)
        self.assertEqual(ledger['baseline_commit'], CANDIDATE_COMMIT)
        self.assertEqual(set(ledger['updates']), {
            'README.md', 'THIRD_PARTY_NOTICES.md', '.github/workflows/ci.yml',
            'formal-catalog/materials_project_catalog/catalog.py',
            'experimental/platform/query-service/materials_query/pins/legacy_baseline.json',
            'experimental/platform/ci/required_test_ids.json',
            'scripts/run_bruns_borosilicate_ci.py', 'scripts/run_tarasov_pna_bpf_ci.py',
            'tests/test_tarasov_pna_bpf_ci.py', 'tests/test_kapoor_phosphate_packet.py',
            'tests/legacy_document_recovery.py', 'tests/test_legacy_document_recovery.py',
        })
        for filename, entry in ledger['updates'].items():
            raw = successors.project_successor_file(filename, (ROOT / filename).read_bytes(), before=BATCH_ID)
            previous = git_bytes(CANDIDATE_COMMIT, filename)
            with self.subTest(filename=filename):
                self.assertEqual(recover_file(raw, entry), previous)
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
        old = types.ModuleType('kapoor_predecessor_registry')
        old.__file__ = str(ROOT / 'tests/material_append_successors.py')
        exec(compile(git_bytes(CANDIDATE_COMMIT, 'tests/material_append_successors.py'), old.__file__, 'exec'), old.__dict__)
        checkpoint = successors._index(BATCH_ID)
        self.assertEqual(successors.FROZEN_SUCCESSORS[checkpoint + 1:], old.FROZEN_SUCCESSORS)
        self.assertEqual(successors.data_ledgers()[checkpoint + 1:], old.data_ledgers())
        for descriptor in old.FROZEN_SUCCESSORS:
            batch = descriptor['batch_id']
            with self.subTest(batch=batch):
                self.assertEqual(successors.data_ledger(batch), old.data_ledger(batch))
                self.assertEqual(successors.file_ledger(batch), old.file_ledger(batch))
        with patch.object(successors, 'FROZEN_SUCCESSORS', successors.FROZEN_SUCCESSORS * 2):
            with self.assertRaises(AssertionError):
                successors.data_ledger()
        with patch.object(successors, 'FROZEN_SUCCESSORS', tuple(reversed(successors.FROZEN_SUCCESSORS))):
            with self.assertRaises(AssertionError):
                successors.project_successor_catalogs(self.current)
        with self.assertRaises(AssertionError):
            successors.file_ledgers(before='unreviewed-kapoor-successor')

    def test_candidate_artifacts_and_computed_reviews_remain_unchanged(self):
        batch = ROOT / 'experimental/material-batches' / BATCH_ID
        for filename in ('README.md', 'VALIDATION.md', 'build_identity_review.py', 'identity-review.json',
                         'packet-spec.json', 'preparation-receipt.json', 'prepared-packet.json',
                         'source-review.json', 'validation-results.json'):
            with self.subTest(filename=filename):
                path = (batch / filename).relative_to(ROOT).as_posix()
                self.assertEqual((batch / filename).read_bytes(), git_bytes(CANDIDATE_COMMIT, path))
        for path, expected_count in (
                ('formal-catalog/materials_project_catalog/data/formal_computed_review.json', 24),
                ('experimental/platform/examples/reviewed-computed-v2/normalized-review.json', 24),
                ('experimental/platform/examples/reviewed-computed-v2-second/normalized-review.json', 62),
                ('experimental/platform/examples/reviewed-computed-seed/scoped-review-input.json', 7)):
            with self.subTest(path=path):
                raw = (ROOT / path).read_bytes()
                self.assertEqual(raw, git_bytes(DATA_BASE_COMMIT, path))
                self.assertEqual(len(json.loads(raw)['records']), expected_count)
        self.assertFalse(any(path.suffix.lower() in ('.pdf', '.png', '.jpg', '.xlsx') for path in batch.rglob('*')))
        for prop in self.additions['properties']:
            with self.subTest(property=prop['id']):
                self.assertIs(prop['verification']['independent_scientific_review'], False)
                self.assertIs(prop['verification']['raw_data_reanalysis'], False)

    def test_candidate_adapter_preserves_methods_source_oracles_and_assertions(self):
        filename = 'tests/test_kapoor_phosphate_packet.py'
        current = (ROOT / filename).read_bytes()
        original = git_bytes(CANDIDATE_COMMIT, filename)
        self.assertEqual(recover_file(current, successors.file_ledger(BATCH_ID)['updates'][filename]), original)
        trees = [ast.parse(raw) for raw in (original, current)]
        constants = {'ROWS', 'BASELINE_HASHES', 'BASE_COMMIT', 'SOURCE', 'DOCUMENT_HASH'}
        def assignments(tree):
            return {node.targets[0].id: ast.dump(node) for node in tree.body if isinstance(node, ast.Assign)
                    and isinstance(node.targets[0], ast.Name) and node.targets[0].id in constants}
        self.assertEqual(assignments(trees[0]), assignments(trees[1]))
        def assertions(tree):
            result = {}
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef) or not node.name.startswith('test_'):
                    continue
                calls = []
                for call in ast.walk(node):
                    if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                            and call.func.attr.startswith('assert')):
                        continue
                    call = deepcopy(call)
                    if call.func.attr == 'assertEqual' and len(call.args) == 2:
                        second = call.args[1]
                        checkpoint_input = (node.name == 'test_p60_contextual_collision_stays_source_qualified_and_separate'
                                            and isinstance(second, ast.Name) and second.id == 'baseline')
                        checkpoint_input |= (node.name == 'test_baseline_pins_and_runtime_catalog_bytes_remain_unchanged'
                                             and isinstance(second, ast.Subscript) and isinstance(second.value, ast.Attribute)
                                             and second.value.attr == 'baseline_bytes')
                        if checkpoint_input:
                            call.args[0] = ast.Name(id='strictly_recovered_checkpoint_bytes', ctx=ast.Load())
                    calls.append(ast.dump(call))
                result[node.name] = calls
            return result
        self.assertEqual(len(assertions(trees[0])), 17)
        self.assertEqual(assertions(trees[0]), assertions(trees[1]))


if __name__ == '__main__':
    unittest.main()
