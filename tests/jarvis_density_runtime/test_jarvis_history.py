"""Verify the real JARVIS working append and strict historical checkpoint wiring."""
import ast
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
import jarvis_density_history as history
import polyomics_md_history as polyomics
history = polyomics.jarvis_test_scope(history)
import sanchez_al_mea_history as sanchez
successors = polyomics.checkpoint_registry()
from material_append_history import encoded, recover_catalogs, recover_file
from materials_boundaries.material_references import validate_material_catalog
from materials_boundaries.material_presentation import render_material_catalog

BATCH = ROOT / 'experimental/material-batches/jarvis-density-native-draft-20261028'


def graph():
    return polyomics.checkpoint_catalogs()


class JarvisHistoryTests(unittest.TestCase):
    def test_real_graph_and_exact_predecessor_objects_order_and_metadata(self):
        current = graph()
        validate_material_catalog(current['materials'], current['properties'], current['sources'])
        previous = history.checkpoint_catalogs()
        for table, fields in [('materials', ['identities', 'grades', 'records']), ('properties', ['records']), ('sources', ['records'])]:
            for field in fields:
                self.assertEqual(current[table][field][:len(previous[table][field])], previous[table][field])
            self.assertEqual({k: v for k, v in current[table].items() if k not in fields},
                             {k: v for k, v in previous[table].items() if k not in fields})
        self.assertEqual([len(current['materials'][k]) for k in ['identities', 'grades', 'records']], [3180, 31, 3181])
        self.assertEqual(len(current['properties']['records']), 3197)
        self.assertEqual(len(current['sources']['records']), 131)
        self.assertEqual(len(previous['materials']['identities']), 1180)
        self.assertEqual(len(sanchez.checkpoint_catalogs()['materials']['identities']), 1175)

    def test_exact_frozen_native_additions_and_source_density_literals(self):
        raw = (BATCH / 'native-candidate.json').read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), '82a2d8332f934b31567cac4d50960871792841321a94bd4357500604f6184e85')
        native = json.loads(raw)
        current = graph()
        indices = {name: {r['id']: r for r in current[name]['records']} for name in ['properties', 'sources']}
        indices['identities'] = {r['id']: r for r in current['materials']['identities']}
        indices['states'] = {r['id']: r for r in current['materials']['records']}
        for name, rows in [('identities', native['catalogs']['materials']['identities']),
                           ('states', native['catalogs']['materials']['records']),
                           ('properties', native['catalogs']['properties']['records']),
                           ('sources', native['catalogs']['sources']['records'])]:
            for row in rows:
                self.assertEqual(indices[name][row['id']], row)
        decisions = json.loads((BATCH / 'identity-taxonomy-decisions.json').read_bytes())
        self.assertEqual(len({r['conservative_composition_key'] for r in decisions['rows']}), 2000)
        self.assertTrue(all(r['electronic_behavior'] == 'unknown' for r in decisions['rows']))

    def test_frozen_registry_and_full_adjacent_catalog_file_chains(self):
        self.assertEqual(successors.FROZEN_SUCCESSORS[0]['batch_id'], history.BATCH_ID)
        self.assertEqual(history.predecessor_descriptors(successors.FROZEN_SUCCESSORS), history.checkpoint_registry().FROZEN_SUCCESSORS)
        data = successors.data_ledgers()
        for newer, older in zip(data, data[1:]):
            self.assertEqual(newer['baseline_sha256'], older['current_sha256'])
        ledgers = successors.file_ledgers()
        for path in history.file_ledger()['updates']:
            entries = [l['updates'][path] for l in ledgers if path in l['updates']]
            for newer, older in zip(entries, entries[1:]):
                self.assertEqual(newer['previous_sha256'], older['sha256'], path)
        altered = deepcopy(successors.FROZEN_SUCCESSORS)
        altered[0]['batch_id'] += '_changed'
        with self.assertRaises(AssertionError):
            history.predecessor_descriptors(altered)

    def test_old_files_and_registry_recover_only_exact_pinned_images(self):
        for ledger in [history.file_ledger(), history.registry_ledger()]:
            for path, entry in ledger['updates'].items():
                raw = polyomics.checkpoint_bytes(path, (ROOT / path).read_bytes())
                previous = recover_file(raw, entry)
                self.assertEqual(sha256(previous).hexdigest(), entry['previous_sha256'])
                self.assertEqual(history.checkpoint_bytes(path, raw), previous)
                for bad in [raw + b' ', raw[:-1], b'!' + raw[1:]]:
                    with self.assertRaises(AssertionError):
                        recover_file(bad, entry)

    def test_current_catalog_requires_current_complete_disk_graph(self):
        original = Path.read_bytes
        previous = history.checkpoint_catalogs()
        old = {ROOT / path: encoded(previous[key]) for key, path in history.CATALOG_PATHS.items()}
        path = history.CATALOG_PATHS['materials']
        current_raw = (ROOT / path).read_bytes()
        with patch.object(Path, 'read_bytes', lambda p: old[p] if p in old else original(p)):
            with self.assertRaises(AssertionError):
                history.checkpoint_bytes(path, current_raw)
        for target in history.CATALOG_PATHS.values():
            with patch.object(Path, 'read_bytes', lambda p: original(p) + b' ' if p == ROOT / target else original(p)):
                with self.assertRaises(AssertionError):
                    history.checkpoint_catalogs()

    def test_partial_mutated_reordered_or_unknown_graphs_are_rejected(self):
        current = graph()
        for name in ['partial', 'old_record', 'new_record', 'order', 'metadata']:
            mutated = deepcopy(current)
            if name == 'partial':
                mutated['materials']['identities'].pop()
            elif name == 'old_record':
                mutated['materials']['identities'][0]['name'] += ' changed'
            elif name == 'new_record':
                mutated['properties']['records'][-1]['reported_value']['number'] = '1'
            elif name == 'order':
                mutated['materials']['records'][-2:] = reversed(mutated['materials']['records'][-2:])
            else:
                mutated['sources']['unreviewed_extra'] = True
            with self.subTest(name=name), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, mutated, history.data_ledger())

    def test_existing_sanchez_assertions_and_all_122_old_fixtures_remain(self):
        path = 'tests/sanchez_al_mea_runtime/test_sanchez_runtime.py'
        current = (ROOT / path).read_bytes()
        previous = recover_file(current, history.file_ledger()['updates'][path])
        assertions = lambda raw: [ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(raw))
                                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith('assert')]
        self.assertEqual(assertions(current), assertions(previous))
        tree = subprocess.check_output(['git', 'ls-tree', '-r', '-z', 'f13586759af6a391635fa81da20c73eb6a6c1c6c', '--', 'tests/fixtures'], cwd=ROOT)
        checked = 0
        for row in tree.split(b'\0'):
            if not row:
                continue
            meta, filename = row.split(b'\t', 1)
            raw = (ROOT / filename.decode('utf8')).read_bytes()
            self.assertEqual(sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode(), meta.split()[2])
            checked += 1
        self.assertEqual(checked, 122)

    def test_real_source_presentation_preserves_new_method_in_four_languages(self):
        current = graph()
        selected = [r for r in current['properties']['records'] if r['source_id'] == 'jarvis_dft_figshare_v11_2025_3d'][:1]
        catalog = {'schema_version': '1.0.0', 'records': selected}
        for language in ['en', 'zh', 'ja', 'de']:
            text = render_material_catalog(catalog, 'reference-properties', language)
            self.assertIn('source_reported_computational_structure_density', text)
            self.assertIn(selected[0]['reported_value']['value_text'], text)
            self.assertNotIn('[missing:', text)


if __name__ == '__main__':
    unittest.main()
