"""Exact Delgado successor recovery and fail-closed historical callers.

This directory is executed explicitly; frozen root and replay IDs stay intact.
No cached graph or scientific inference is introduced by a test-only view.
"""
import ast
from collections import Counter
from copy import deepcopy
from hashlib import sha1, sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import delgado_pla_pcl_history as history
import curaua_history as curaua
import material_append_successors as successors
from material_append_history import encoded, graph_hashes, recover_catalogs, recover_file

BATCH = 'experimental/material-batches/delgado-pla-pcl-20261026/'
CANDIDATE_FILES = ('README.md', 'VALIDATION.md', 'build_identity_review.py',
                   'identity-review.json', 'packet-spec.json', 'preparation-receipt.json',
                   'prepared-packet.json', 'source-review.json', 'validation-results.json')
QUERY = 'experimental/platform/query-service/catalog-tests'


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                          check=True, timeout=30).stdout


def graph():
    return {name: json.loads((ROOT / relative).read_bytes())
            for name, relative in history.CATALOG_PATHS.items()}


def manifest():
    return history.load_frozen(ROOT, history.DIRECTORY + 'checkpoint-inputs.json', history.INPUTS_SHA256)


class DelgadoPlaPclAppendPreservationTests(unittest.TestCase):
    def test_complete_exact_append_recovers_every_old_object_order_and_metadata(self):
        current = graph()
        ledger = history.data_ledger()
        previous = recover_catalogs(ROOT, current, ledger)
        self.assertEqual(graph_hashes(current), ledger['current_sha256'])
        self.assertEqual(graph_hashes(previous), ledger['baseline_sha256'])
        for table, relative in history.CATALOG_PATHS.items():
            self.assertEqual(encoded(previous[table]), git('show', history.BASELINE + ':' + relative))
        for table, field, delta in (('materials', 'identities', 7), ('materials', 'grades', 0),
                                    ('materials', 'records', 7), ('properties', 'records', 7),
                                    ('sources', 'records', 1)):
            self.assertEqual(current[table][field][:-delta] if delta else current[table][field],
                             previous[table][field])
        self.assertEqual(len(current['materials']['identities']), 1175)
        self.assertEqual(Counter(row['category'] for row in current['materials']['identities']),
                         {'natural': 1010, 'metal': 32, 'inorganic': 59, 'polymer': 37, 'composite': 37})
        self.assertEqual(current['sources']['records'][-1]['id'], 'delgado_aguilar_2020_pla_pcl')

    def test_partial_duplicate_reordered_mutated_and_unknown_graphs_are_rejected(self):
        original = graph()
        for mutation in ('partial', 'duplicate', 'reordered', 'value', 'old_object', 'metadata'):
            current = deepcopy(original)
            if mutation == 'partial': current['materials']['identities'].pop()
            elif mutation == 'duplicate': current['materials']['identities'].append(deepcopy(current['materials']['identities'][-1]))
            elif mutation == 'reordered': current['properties']['records'][-2:] = reversed(current['properties']['records'][-2:])
            elif mutation == 'value': current['properties']['records'][-1]['reported_value']['number'] = '0'
            elif mutation == 'old_object': current['materials']['identities'][0]['name'] += ' changed'
            else: current['sources']['unreviewed'] = True
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, current, history.data_ledger())

    def test_nine_candidate_artifacts_and_all_122_old_fixtures_remain_exact(self):
        for filename in CANDIDATE_FILES:
            relative = BATCH + filename
            self.assertEqual((ROOT / relative).read_bytes(), git('show', history.BASELINE + ':' + relative))
        entries = [entry for entry in git('ls-tree', '-r', '-z', history.BASELINE,
                                         '--', 'tests/fixtures').split(b'\0') if entry]
        self.assertEqual(len(entries), 122)
        for entry in entries:
            metadata, path = entry.split(b'\t', 1)
            raw = (ROOT / path.decode()).read_bytes()
            self.assertEqual(sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode(),
                             metadata.split()[2])

    def test_registry_adds_exactly_one_boundary_and_every_file_recovers_exact_bytes(self):
        previous = history.checkpoint_registry()
        descriptor = {'batch_id': successors.DELGADO_PLA_PCL_BATCH_ID,
            'data': (successors.DELGADO_PLA_PCL_DATA_LEDGER, successors.DELGADO_PLA_PCL_DATA_SHA256),
            'files': (successors.DELGADO_PLA_PCL_FILE_LEDGER, successors.DELGADO_PLA_PCL_FILE_SHA256)}
        self.assertEqual(successors.FROZEN_SUCCESSORS, (descriptor,) + previous.FROZEN_SUCCESSORS)
        self.assertEqual(len(previous.FROZEN_SUCCESSORS), 16)
        self.assertEqual(successors.data_ledgers(before=successors.DELGADO_PLA_PCL_BATCH_ID), [])
        self.assertEqual(successors.data_ledgers()[0], history.data_ledger())
        self.assertEqual(successors.data_ledgers()[1:], previous.data_ledgers())
        for ledger in (history.file_ledger(), history.registry_ledger()):
            for relative, entry in ledger['updates'].items():
                raw = (ROOT / relative).read_bytes()
                with self.subTest(path=relative):
                    self.assertEqual(sha256(raw).hexdigest(), entry['sha256'])
                    self.assertEqual(recover_file(raw, entry), git('show', history.BASELINE + ':' + relative))
        self.assertNotIn('.github/workflows/ci.yml', history.file_ledger()['updates'])

    def test_unknown_file_images_pass_unchanged_but_strict_reads_reject_them(self):
        for relative in ('README.md', 'tests/curaua_history.py', 'tests/material_append_successors.py',
                         'experimental/platform/ci/required_test_ids.json',
                         'materials_boundaries/data/sources.json'):
            raw = (ROOT / relative).read_bytes()
            for changed in (raw + b' ', raw[:-1], b'!' + raw[1:]):
                with self.subTest(path=relative):
                    self.assertIs(history.checkpoint_bytes(relative, changed), changed)
                    with self.assertRaises(AssertionError):
                        history.require_checkpoint_bytes(relative, changed)
                    with self.assertRaises(AssertionError):
                        curaua.require_checkpoint_bytes(relative, changed)

    def test_later_calls_reread_graph_ledger_and_packet_without_cross_call_cache(self):
        before = history.checkpoint_catalogs()
        original = Path.read_bytes
        for target in ('materials_boundaries/data/sources.json', history.DIRECTORY + 'data-history.json',
                       BATCH + 'prepared-packet.json'):
            def changed(path):
                return original(path) + (b' ' if path == ROOT / target else b'')
            with self.subTest(path=target), patch.object(Path, 'read_bytes', changed), self.assertRaises(AssertionError):
                history.checkpoint_catalogs()
        self.assertEqual(history.checkpoint_catalogs(), before)
        # Both original complete Curaua/Tian images remain valid inputs;
        # a mixed graph is never treated as an older snapshot.
        oldest = curaua.checkpoint_catalogs()
        for checkpoint in (before, oldest):
            replacements = {ROOT / history.CATALOG_PATHS[key]: encoded(value)
                            for key, value in checkpoint.items()}
            def historical(path):
                return replacements[path] if path in replacements else original(path)
            with patch.object(Path, 'read_bytes', historical):
                self.assertEqual(curaua.checkpoint_catalogs(), oldest)
        replacements = {ROOT / history.CATALOG_PATHS['materials']: encoded(oldest['materials'])}
        def mixed(path):
            return replacements[path] if path in replacements else original(path)
        with patch.object(Path, 'read_bytes', mixed), self.assertRaises(AssertionError):
            curaua.checkpoint_catalogs()


class DelgadoPlaPclCheckpointGuardTests(unittest.TestCase):
    def test_current_inventory_projects_257_to_249_to_233_without_accepting_stale_ids(self):
        entry = manifest()['inventories'][QUERY]
        self.assertEqual((len(entry['current']), len(entry['previous'])), (257, 249))
        ids, paths = history.checkpoint_inventory_view(QUERY, entry['current'])
        self.assertEqual(ids, entry['previous'])
        self.assertEqual(paths, entry['previous_paths'])
        self.assertEqual(len(curaua.checkpoint_inventory(QUERY, entry['current'])), 233)
        previous_bytes = {ROOT / relative: history.require_checkpoint_bytes(relative)
                          for relative in entry['previous_paths']}
        original_read, original_glob = Path.read_bytes, Path.glob
        def predecessor_read(path):
            return previous_bytes[path] if path in previous_bytes else original_read(path)
        def predecessor_paths(path, pattern):
            if path == ROOT / QUERY:
                return iter(ROOT / relative for relative in entry['previous_paths'])
            return original_glob(path, pattern)
        with patch.object(Path, 'read_bytes', predecessor_read), patch.object(Path, 'glob', predecessor_paths):
            self.assertEqual(history.checkpoint_inventory(QUERY, entry['previous']), entry['previous'])
            self.assertEqual(len(curaua.checkpoint_inventory(QUERY, entry['previous'])), 233)
        for ids in (entry['previous'], entry['current'][:-1], entry['current'] + entry['current'][:1],
                    entry['current'] + ['unknown.C.test_extra'], list(reversed(entry['current'])),
                    entry['current'][1:] + ['unknown.C.test_substituted']):
            with self.subTest(ids=ids), self.assertRaises(AssertionError):
                curaua.checkpoint_inventory(QUERY, ids)

    def test_inventory_rejects_changed_known_bytes_and_unlisted_new_files(self):
        entry = manifest()['inventories'][QUERY]
        original = Path.read_bytes
        for target in (QUERY + '/test_delgado_pla_pcl.py', QUERY + '/test_ewurum_reactive.py',
                       QUERY + '/test_baseline_compatibility.py'):
            def changed(path):
                return original(path) + (b' ' if path == ROOT / target else b'')
            with self.subTest(path=target), patch.object(Path, 'read_bytes', changed), self.assertRaises(AssertionError):
                curaua.checkpoint_inventory(QUERY, entry['current'])
        original_glob = Path.glob
        def extra(path, pattern):
            values = list(original_glob(path, pattern))
            return iter(values + [path / 'test_unreviewed.py']) if path == ROOT / QUERY else iter(values)
        with patch.object(Path, 'glob', extra), self.assertRaises(AssertionError):
            curaua.checkpoint_inventory(QUERY, entry['current'])
        self.assertEqual(history.checkpoint_inventory(QUERY, entry['current']), entry['previous'])

    def test_actual_nested_bruns_tarasov_kapoor_calls_keep_all_fixed_fingerprints(self):
        import test_bruns_borosilicate_ci as bruns
        import test_tarasov_pna_bpf_ci as tarasov
        import test_kapoor_phosphate_ci as kapoor
        import run_tian_nano_ti_ci as tian
        original_tian = tian.declared_test_ids, tian.validate_inventory
        expected = manifest()['inventories'][QUERY]['current']
        for module, count in ((bruns, 214), (tarasov, 220), (kapoor, 226)):
            adapter = module.ci.declared_test_ids
            self.assertEqual(adapter(QUERY), expected)
            observed = []
            def validate(group, ids):
                if group == 'query': observed.append(list(ids))
                return original_tian[1](group, ids)
            with self.subTest(module=module.__name__), patch.object(tian, 'validate_inventory', validate):
                old_ids = adapter(QUERY, regression_checkpoint=True)
                self.assertEqual(len(old_ids), count)
                module.ci.validate_inventory('query', old_ids)
                self.assertTrue(observed)
                self.assertTrue(all(len(ids) == 233 for ids in observed))
            self.assertIs(module.ci.declared_test_ids, adapter)
            with self.assertRaises(RuntimeError):
                adapter(QUERY, predecessor=True, regression_checkpoint=True)
            self.assertIs(module.ci.declared_test_ids, adapter)
        self.assertEqual((tian.declared_test_ids, tian.validate_inventory), original_tian)

    def test_actual_family_view_rejects_registry_and_workflow_drift(self):
        import test_family_adjacency_history as family
        verify = family.FamilyAdjacencyHistoryTests().test_all_material_workflow_views_keep_their_exact_file_pins
        verify()
        descriptors = successors.FROZEN_SUCCESSORS
        for altered in (tuple(reversed(descriptors)), descriptors + descriptors[:1], descriptors[1:],
                        descriptors + ({'batch_id': 'unknown'},)):
            with self.subTest(descriptors=altered), patch.object(successors, 'FROZEN_SUCCESSORS', altered), self.assertRaises(AssertionError):
                verify()
        original = Path.read_bytes
        for relative in ('.github/workflows/ci.yml', 'tests/material_append_successors.py'):
            def changed(path):
                return original(path) + (b' ' if path == ROOT / relative else b'')
            with self.subTest(path=relative), patch.object(Path, 'read_bytes', changed), self.assertRaises(AssertionError):
                verify()
        verify()

    def test_document_recovery_does_not_erase_false_counts_or_unknown_prose(self):
        import material_bulk_preservation as bulk
        raw = (ROOT / 'README.md').read_bytes()
        normalized = bulk.truthful_readme(raw, bulk.load_ledger())
        previous = history.checkpoint_document('README.md', normalized)
        ledger = history.load_frozen(ROOT, history.DIRECTORY + 'document-history.json', history.DOCUMENTS_SHA256)
        self.assertEqual(sha256(previous).hexdigest(), ledger['updates']['README.md']['previous_sha256'])
        unknown = normalized + b'unknown prose\n'
        self.assertIs(history.checkpoint_document('README.md', unknown), unknown)
        false = raw.replace(b'**1175 material identities**', b'**1176 material identities**')
        self.assertNotEqual(false, raw)
        with self.assertRaises(AssertionError):
            bulk.release_bytes('README.md', false)

    def test_original_core_replay_workflows_runners_and_inventory_are_unchanged(self):
        paths = ('.github/workflows/ci.yml', '.github/workflows/history-replay-latest.yml',
                 '.github/workflows/curaua-runtime.yml', 'tests/core_partition/manifest.json',
                 'tests/history_replay_latest/ci-inventory.json', 'tests/material_append_history.py',
                 'scripts/run_full_core_partition_ci.py', 'scripts/run_history_replay_latest_ci.py',
                 'scripts/run_bruns_borosilicate_ci.py', 'scripts/run_tarasov_pna_bpf_ci.py',
                 'scripts/run_kapoor_phosphate_ci.py', 'scripts/run_tian_nano_ti_ci.py',
                 'scripts/run_curaua_runtime_ci.py')
        for relative in paths:
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), git('show', history.BASELINE + ':' + relative))
        core = json.loads((ROOT / 'tests/core_partition/manifest.json').read_bytes())
        self.assertEqual((core['module_count'], core['test_count']), (147, 1887))
        self.assertEqual(core['root_inventory_sha256'], '19a735217c29533c1137a6cfd95b2b58cf88e8cf649848e41012c510434446f7')
        replay = json.loads((ROOT / 'tests/history_replay_latest/ci-inventory.json').read_bytes())
        self.assertEqual((replay['count'], len(replay['ids'])), (70, 70))
        self.assertFalse((Path(__file__).parent / '__init__.py').exists())

    def test_repeated_actual_packet_merge_is_byte_idempotent_and_preserves_inputs(self):
        from materials_boundaries.material_references import merge_material_catalogs
        before = history.checkpoint_catalogs()
        packet = json.loads((ROOT / BATCH / 'prepared-packet.json').read_bytes())['catalogs']
        saved_before, saved_packet = deepcopy(before), deepcopy(packet)
        first = merge_material_catalogs(before['materials'], before['properties'], before['sources'], packet)
        self.assertEqual(first, graph())
        again = merge_material_catalogs(first['materials'], first['properties'], first['sources'], packet)
        self.assertEqual({key: encoded(value) for key, value in again.items()},
                         {key: encoded(value) for key, value in first.items()})
        self.assertEqual(before, saved_before)
        self.assertEqual(packet, saved_packet)
        altered = deepcopy(packet)
        altered['materials']['identities'][0]['names']['en'] += ' conflicting replay'
        with self.assertRaisesRegex(ValueError, 'conflicting existing'):
            merge_material_catalogs(first['materials'], first['properties'], first['sources'], altered)
        self.assertEqual(first, graph())

    def test_fresh_process_reverse_import_orders_keep_nested_oracles(self):
        expected = manifest()['inventories'][QUERY]['current']
        names = ['test_bruns_borosilicate_ci', 'test_tarasov_pna_bpf_ci',
                 'test_kapoor_phosphate_ci', 'test_tian_nano_ti_ci']
        for order in (names, list(reversed(names))):
            script = (
                "import importlib,json,sys; from pathlib import Path; "
                "root=Path(sys.argv[1]); sys.path[:0]=[str(root/'tests'),str(root/'scripts'),str(root)]; "
                "mods=[importlib.import_module(n) for n in json.loads(sys.argv[2])]; "
                "expected=json.loads(sys.argv[3]); relative=sys.argv[4]; "
                "counts={'test_bruns_borosilicate_ci':214,'test_tarasov_pna_bpf_ci':220,'test_kapoor_phosphate_ci':226}; "
                "\nfor mod in mods:\n"
                " if mod.__name__ in counts:\n"
                "  assert mod.ci.declared_test_ids(relative)==expected\n"
                "  ids=mod.ci.declared_test_ids(relative,regression_checkpoint=True)\n"
                "  assert len(ids)==counts[mod.__name__]; mod.ci.validate_inventory('query',ids)\n"
                "sys.stdout.buffer.write(b'EXACT_IMPORT_ORDER_PASS\\n')"
            )
            result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', script,
                                     str(ROOT), json.dumps(order), json.dumps(expected), QUERY],
                                    cwd=ROOT, capture_output=True, timeout=180, check=True)
            self.assertEqual(result.stdout, b'EXACT_IMPORT_ORDER_PASS\n')

    def test_historical_payload_restores_root_and_module_after_exceptions(self):
        directory = ROOT / 'tests/ewurum_reactive_ci'
        sys.path.insert(0, str(directory))
        try:
            import test_ewurum_reactive_ci as previous
            import run_ewurum_reactive_runtime_ci as original
            self.assertIsNot(previous.ci, original)
            saved, original_saved = previous.ci.ROOT, original.ROOT
            previous.ci.installation_payload()
            self.assertIs(previous.ci.ROOT, saved)
            with patch.object(previous.delgado, 'require_checkpoint_bytes',
                              side_effect=AssertionError('unrecognized input')):
                with self.assertRaises(AssertionError):
                    previous.ci.installation_payload()
            self.assertIs(previous.ci.ROOT, saved)
            self.assertIs(original.ROOT, original_saved)
        finally:
            sys.path.remove(str(directory))


if __name__ == '__main__':
    unittest.main()
