"""Verify the real append and exact historical recovery, outside frozen root IDs."""
from copy import deepcopy
from hashlib import sha256, sha1
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
import sanchez_al_mea_history as history
import material_append_successors as successors
import jarvis_density_history as jarvis
successors = jarvis.checkpoint_registry()
from material_append_history import encoded, recover_catalogs, recover_file
from materials_boundaries.material_references import (
    material_quota_coverage, merge_material_catalogs, validate_material_catalog,
)

BATCH = ROOT / 'experimental/material-batches/sanchez-al-mea-revised-20261027'


def graph():
    return jarvis.checkpoint_catalogs(ROOT)


def git_bytes(path):
    return subprocess.check_output(['git', 'show', history.BASELINE + ':' + path], cwd=ROOT)


class SanchezRuntimeTests(unittest.TestCase):
    def test_exact_append_preserves_every_predecessor_object(self):
        current = graph()
        validate_material_catalog(current['materials'], current['properties'], current['sources'])
        previous = history.checkpoint_catalogs()
        for key, path in history.CATALOG_PATHS.items():
            self.assertEqual(encoded(previous[key]), git_bytes(path))
        for table, field, count in [('materials', 'identities', 5), ('materials', 'records', 5),
                                     ('properties', 'records', 10), ('sources', 'records', 1)]:
            self.assertEqual(current[table][field][:-count], previous[table][field])
        self.assertEqual(current['materials']['grades'], previous['materials']['grades'])

    def test_real_coverage_has_only_five_new_metal_identities(self):
        current = graph()
        coverage = material_quota_coverage(current['materials'], current['properties'], current['sources'])
        self.assertEqual(coverage['distinct_material_count'], 1180)
        self.assertEqual({k: v['admitted_unique_identity_count'] for k, v in coverage['classes'].items()},
                         {'metal': 37, 'inorganic': 59, 'polymer': 37, 'composite': 37, 'natural': 1010})
        self.assertEqual(len(current['materials']['records']), 1181)
        self.assertEqual(len(current['properties']['records']), 1197)
        self.assertEqual(len(current['sources']['records']), 130)

    def test_reviewed_packet_is_exact_and_reapplication_is_idempotent(self):
        raw = (BATCH / 'candidate.json').read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), '58f418dcfe265b14e296a21be6c28c8531aa91c4c1919889c19d9f91cfc201c4')
        prepared = json.loads((BATCH / 'prepared-packet.json').read_bytes())
        self.assertEqual(prepared['catalogs'], json.loads(raw)['catalogs'])
        current = graph()
        repeated = merge_material_catalogs(current['materials'], current['properties'], current['sources'], prepared['catalogs'])
        self.assertEqual(repeated, current)

    def test_mutated_partial_reordered_or_unknown_graph_cannot_inherit_review(self):
        for mutation in ('partial', 'reordered', 'new_value', 'old_value', 'metadata'):
            current = graph()
            if mutation == 'partial':
                current['materials']['identities'].pop()
            elif mutation == 'reordered':
                current['properties']['records'][-2:] = reversed(current['properties']['records'][-2:])
            elif mutation == 'new_value':
                current['properties']['records'][-1]['reported_value']['number'] = '1'
            elif mutation == 'old_value':
                current['materials']['identities'][0]['name'] += ' changed'
            else:
                current['sources']['unreviewed_extra'] = True
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, current, history.data_ledger())

    def test_all_changed_old_files_recover_exact_bytes_and_unknown_images_fail(self):
        for ledger in [history.file_ledger(), history.registry_ledger()]:
            for path, entry in ledger['updates'].items():
                raw = jarvis.checkpoint_bytes(path, (ROOT / path).read_bytes(), root=ROOT)
                self.assertEqual(recover_file(raw, entry), git_bytes(path))
                for unknown in (raw + b' ', raw[:-1], b'!' + raw[1:]):
                    with self.subTest(path=path), self.assertRaises(AssertionError):
                        recover_file(unknown, entry)

    def test_explicit_successor_chain_is_adjacent_and_predecessor_registry_exact(self):
        self.assertEqual(successors.FROZEN_SUCCESSORS[0]['batch_id'], 'sanchez-al-mea-revised-20261027')
        ledgers = successors.data_ledgers()
        for newer, older in zip(ledgers, ledgers[1:]):
            self.assertEqual(newer['baseline_sha256'], older['current_sha256'])
        previous = history.checkpoint_registry()
        self.assertEqual(successors.FROZEN_SUCCESSORS[1:], previous.FROZEN_SUCCESSORS)

    def test_all_historical_fixture_blobs_are_unchanged(self):
        entries = subprocess.check_output(['git', 'ls-tree', '-r', '-z', history.BASELINE, '--', 'tests/fixtures'], cwd=ROOT)
        checked = 0
        for item in entries.split(b'\0'):
            if not item:
                continue
            meta, path = item.split(b'\t', 1)
            raw = (ROOT / path.decode('utf8')).read_bytes()
            self.assertEqual(sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode(), meta.split()[2])
            checked += 1
        self.assertEqual(checked, 122)

    def test_checkpoint_rereads_exact_raw_bytes_not_only_parsed_json(self):
        original = Path.read_bytes
        for target in history.CATALOG_PATHS.values():
            def altered(path):
                raw = original(path)
                return raw + b' ' if path == ROOT / target else raw
            with self.subTest(path=target), patch.object(Path, 'read_bytes', altered):
                with self.assertRaises(AssertionError):
                    history.checkpoint_catalogs()
        self.assertEqual(len(history.checkpoint_catalogs()['materials']['identities']), 1175)


if __name__ == '__main__':
    unittest.main()
