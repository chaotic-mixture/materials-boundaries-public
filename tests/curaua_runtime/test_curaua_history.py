"""Exact Curaua append preservation and finite historical checkpoint guards."""
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
import curaua_history as history
import ewurum_reactive_history as ewurum
import material_append_successors as successors
from material_append_history import encoded, graph_hashes, recover_catalogs, recover_file

BATCH = 'experimental/material-batches/czlonka-curaua-20261025/'
CANDIDATE_FILES = ('README.md', 'VALIDATION.md', 'build_identity_review.py',
                   'identity-review.json', 'packet-spec.json', 'preparation-receipt.json',
                   'prepared-packet.json', 'source-review.json', 'validation-results.json')


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                          check=True, timeout=30).stdout


def current_graph():
    return ewurum.checkpoint_catalogs()


class CurauaAppendPreservationTests(unittest.TestCase):
    def test_complete_exact_append_recovers_every_original_object_and_order(self):
        current = current_graph()
        ledger = history.data_ledger()
        previous = recover_catalogs(ROOT, current, ledger)
        self.assertEqual(graph_hashes(current), ledger['current_sha256'])
        self.assertEqual(graph_hashes(previous), ledger['baseline_sha256'])
        for table, relative in history.CATALOG_PATHS.items():
            self.assertEqual(encoded(previous[table]), git('show', history.BASELINE + ':' + relative))
        for table, field, delta in (('materials', 'identities', 3), ('materials', 'grades', 0),
                                    ('materials', 'records', 3), ('properties', 'records', 3),
                                    ('sources', 'records', 1)):
            self.assertEqual(current[table][field][:-delta] if delta else current[table][field],
                             previous[table][field])
        self.assertEqual(len(current['materials']['identities']), 1164)
        self.assertEqual(Counter(row['category'] for row in current['materials']['identities']),
                         {'natural':1010, 'metal':32, 'inorganic':59, 'polymer':30, 'composite':33})

    def test_partial_duplicate_reordered_and_mutated_additions_are_rejected(self):
        original = current_graph()
        for mutation in ('partial', 'duplicate', 'reordered', 'value', 'old_object', 'metadata'):
            graph = deepcopy(original)
            if mutation == 'partial': graph['materials']['identities'].pop()
            elif mutation == 'duplicate': graph['materials']['identities'].append(deepcopy(graph['materials']['identities'][-1]))
            elif mutation == 'reordered': graph['properties']['records'][-2:] = reversed(graph['properties']['records'][-2:])
            elif mutation == 'value': graph['properties']['records'][-1]['reported_value']['number'] = '0'
            elif mutation == 'old_object': graph['materials']['identities'][0]['name'] += ' changed'
            else: graph['materials']['unreviewed'] = True
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                recover_catalogs(ROOT, graph, history.data_ledger())

    def test_all_candidate_evidence_and_old_fixture_blobs_are_exact(self):
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

    def test_registry_extends_only_the_reviewed_material_boundary(self):
        current_successors = successors
        successors_checkpoint = ewurum.checkpoint_registry()
        previous = history.checkpoint_registry()
        self.assertEqual(successors_checkpoint.FROZEN_SUCCESSORS[1:], previous.FROZEN_SUCCESSORS)
        self.assertEqual(successors_checkpoint.FROZEN_SUCCESSORS[0]['batch_id'], 'czlonka-curaua-20261025')
        self.assertEqual(successors_checkpoint.data_ledgers(before=successors_checkpoint.CURAUA_BATCH_ID), [])
        self.assertEqual(successors_checkpoint.data_ledgers()[0], history.data_ledger())
        self.assertEqual(successors_checkpoint.data_ledgers()[1:], previous.data_ledgers())
        for relative, entry in history.file_ledger()['updates'].items():
            current = ewurum.checkpoint_bytes(relative)
            self.assertEqual(sha256(current).hexdigest(), entry['sha256'])
            self.assertEqual(recover_file(current, entry), git('show', history.BASELINE + ':' + relative))

        import test_family_adjacency_history as family
        case = family.FamilyAdjacencyHistoryTests()
        verify = case.test_all_material_workflow_views_keep_their_exact_file_pins
        verify()
        descriptors = current_successors.FROZEN_SUCCESSORS
        for altered in (tuple(reversed(descriptors)), descriptors + descriptors[:1],
                        descriptors + ({'batch_id': 'unknown'},)):
            with self.subTest(descriptors=altered), \
                    patch.object(current_successors, 'FROZEN_SUCCESSORS', altered), \
                    self.assertRaises(AssertionError):
                verify()
        original_read = Path.read_bytes
        workflow = '.github/workflows/ci.yml'
        old_workflow = git('show', 'bf1c7a86068c37c2733ac4d25c268144090f9aad:' + workflow)
        for relative, replacement in ((workflow, original_read(ROOT / workflow) + b' '),
                (workflow, old_workflow), ('tests/material_append_successors.py',
                 original_read(ROOT / 'tests/material_append_successors.py') + b' ')):
            def changed(path):
                return replacement if path == ROOT / relative else original_read(path)
            with self.subTest(path=relative, digest=sha256(replacement).hexdigest()), \
                    patch.object(Path, 'read_bytes', changed), self.assertRaises(AssertionError):
                verify()
        verify()

    def test_unknown_file_images_remain_unknown_and_strict_reads_reject_them(self):
        for relative in ('README.md', 'tests/ci_partition_history.py',
                         'tests/history_replay_latest/benchmark_replay_16.py',
                         'tests/history_replay_latest/test_checkout_history.py',
                         'experimental/platform/ci/required_test_ids.json',
                         'materials_boundaries/data/sources.json'):
            raw = (ROOT / relative).read_bytes()
            for changed in (raw + b' ', raw[:-1], b'!' + raw[1:]):
                with self.subTest(path=relative, digest=sha256(changed).hexdigest()):
                    self.assertIs(history.checkpoint_bytes(relative, changed), changed)
                    with self.assertRaises(AssertionError):
                        history.require_checkpoint_bytes(relative, changed)

    def test_input_changes_are_reread_without_cross_call_cache(self):
        before = history.checkpoint_catalogs()
        original = Path.read_bytes
        for target in ('materials_boundaries/data/sources.json',
                       history.DIRECTORY + 'data-history.json', BATCH + 'prepared-packet.json'):
            def changed(path):
                raw = original(path)
                return raw + b' ' if path == ROOT / target else raw
            with self.subTest(target=target), patch.object(Path, 'read_bytes', changed), self.assertRaises(AssertionError):
                history.checkpoint_catalogs()
        self.assertEqual(history.checkpoint_catalogs(), before)


class CurauaCheckpointGuardTests(unittest.TestCase):
    def test_inventory_rejects_unknown_ids_new_files_and_changed_known_additions(self):
        manifest = history.load_frozen(ROOT, history.DIRECTORY + 'checkpoint-inputs.json', history.INPUTS_SHA256)
        relative = 'experimental/platform/query-service/catalog-tests'
        entry = manifest['inventories'][relative]
        current_entry = ewurum.load_frozen(ROOT, ewurum.DIRECTORY + 'checkpoint-inputs.json', ewurum.INPUTS_SHA256)['inventories'][relative]
        current_ids = current_entry['current']
        self.assertEqual(ewurum.checkpoint_inventory(relative, current_ids), entry['current'])
        self.assertEqual(history.checkpoint_inventory(relative, current_ids), entry['previous'])
        for ids in (current_ids[:-1], current_ids + ['unknown.test'], list(reversed(current_ids))):
            with self.assertRaises(AssertionError):
                history.checkpoint_inventory(relative, ids)
        original = Path.read_bytes
        target = ROOT / entry['added_files'][0]
        def changed(path):
            return original(path) + (b' ' if path == target else b'')
        with patch.object(Path, 'read_bytes', changed), self.assertRaises(AssertionError):
            history.checkpoint_inventory(relative, current_ids)
        original_glob = Path.glob
        def extra(path, pattern):
            values = list(original_glob(path, pattern))
            return iter(values + [path / 'test_unreviewed.py']) if path == ROOT / relative else iter(values)
        with patch.object(Path, 'glob', extra), self.assertRaises(AssertionError):
            history.checkpoint_inventory(relative, current_ids)
        self.assertEqual(history.checkpoint_inventory(relative, current_ids), entry['previous'])

        import test_bruns_borosilicate_ci as bruns
        import test_tarasov_pna_bpf_ci as tarasov
        import test_kapoor_phosphate_ci as kapoor
        import run_tian_nano_ti_ci as successor
        successor_declared = successor.declared_test_ids
        successor_validate = successor.validate_inventory
        for module in (bruns, tarasov, kapoor):
            adapter = module.ci.declared_test_ids
            original_declared = module._original_declared_test_ids
            self.assertEqual(adapter(relative), current_ids)
            restored = adapter(relative, regression_checkpoint=True)
            module.ci.validate_inventory('query', restored)
            self.assertIs(module.ci.declared_test_ids, adapter)
            for mutation in ('missing', 'duplicate', 'extra', 'substituted', 'reordered'):
                def altered(path, **kwargs):
                    ids = original_declared(path, **kwargs)
                    if kwargs or path != relative:
                        return ids
                    return {'missing': ids[:-1], 'duplicate': ids + ids[:1],
                            'extra': ids + ['unknown.Case.test_extra'],
                            'substituted': ids[1:] + ['unknown.Case.test_replacement'],
                            'reordered': list(reversed(ids))}[mutation]
                with self.subTest(module=module.__name__, inventory=mutation), \
                        patch.object(module, '_original_declared_test_ids', altered), \
                        self.assertRaises(AssertionError):
                    adapter(relative, regression_checkpoint=True)
                self.assertIs(module.ci.declared_test_ids, adapter)
            with patch.object(Path, 'read_bytes', changed), self.assertRaises(AssertionError):
                adapter(relative, regression_checkpoint=True)
            self.assertIs(module.ci.declared_test_ids, adapter)
            def extra_bytes(path):
                return b'' if path == ROOT / relative / 'test_unreviewed.py' else original(path)
            with patch.object(Path, 'glob', extra), patch.object(Path, 'read_bytes', extra_bytes), \
                    self.assertRaises(AssertionError):
                adapter(relative, regression_checkpoint=True)
            self.assertIs(module.ci.declared_test_ids, adapter)
            with self.assertRaises(RuntimeError):
                adapter(relative, predecessor=True, regression_checkpoint=True)
            self.assertIs(module.ci.declared_test_ids, adapter)
            self.assertEqual(adapter(relative), current_ids)
        self.assertIs(successor.declared_test_ids, successor_declared)
        self.assertIs(successor.validate_inventory, successor_validate)

    def test_document_bridge_retains_false_count_and_unknown_prose_rejection(self):
        import material_bulk_preservation as bulk
        raw = ewurum.require_checkpoint_bytes('README.md')
        normalized = bulk.truthful_readme(raw, bulk.load_ledger())
        ledger = history.load_frozen(ROOT, history.DIRECTORY + 'document-history.json', history.DOCUMENTS_SHA256)
        self.assertEqual(sha256(history.checkpoint_document('README.md', normalized)).hexdigest(),
                         ledger['updates']['README.md']['previous_sha256'])
        unknown = normalized + b'unknown prose\n'
        self.assertIs(history.checkpoint_document('README.md', unknown), unknown)
        false = raw.replace(b'**1164 material identities**', b'**1165 material identities**')
        self.assertNotEqual(false, raw)
        with self.assertRaises(AssertionError):
            bulk.release_bytes('README.md', false)

    def test_historical_tian_payload_restores_its_local_root_on_success_or_failure(self):
        import test_tian_nano_ti_ci as tian
        original = tian.ci.ROOT
        tian.ci.installation_payload()
        self.assertIs(tian.ci.ROOT, original)
        with patch.object(tian, 'require_checkpoint_bytes', side_effect=AssertionError('changed input')):
            with self.assertRaises(AssertionError):
                tian.ci.installation_payload()
        self.assertIs(tian.ci.ROOT, original)

    def test_whole_file_recovery_retains_frozen_core_and_replay_inventory(self):
        manifest = json.loads((ROOT / 'tests/core_partition/manifest.json').read_bytes())
        self.assertEqual((manifest['module_count'], manifest['test_count']), (147, 1887))
        self.assertEqual(manifest['root_inventory_sha256'],
                         '19a735217c29533c1137a6cfd95b2b58cf88e8cf649848e41012c510434446f7')
        for relative in ('tests/material_append_history.py', '.github/workflows/ci.yml',
                         'tests/history_replay_latest/ci-inventory.json',
                         'scripts/run_history_replay_latest_ci.py', 'scripts/run_tian_nano_ti_ci.py'):
            self.assertEqual((ROOT / relative).read_bytes(), git('show', history.BASELINE + ':' + relative))


class CurauaSeventeenLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'tests/history_replay_latest/test_replay_16.py'
        spec = importlib.util.spec_from_file_location('curaua_synthetic_17', path)
        cls.helpers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.helpers)
        cls.previous, cls.current, _ = cls.helpers.adapter.RUNNER.engines()

    def test_seventeen_layer_images_and_source_gaps_match_original_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            case = self.helpers.synthetic.build_chain(Path(directory), 17, {1, 4, 8, 15, 17})
            self.assertEqual(len(case.ledgers), 17)
            for graph in case.graphs:
                for table, filename in self.current.FILES.items():
                    raw = self.current.encoded(graph[table])
                    old = self.previous.project_catalog_bytes_chain(case.root, filename, raw, case.ledgers)
                    new = self.current.project_catalog_bytes_chain(case.root, filename, raw, case.ledgers)
                    self.assertEqual(new, old)

    def test_seventeen_layer_wrong_order_and_unknown_bytes_keep_strict_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            case = self.helpers.synthetic.build_chain(Path(directory), 17, {1, 4, 8, 15, 17})
            for module in (self.previous, self.current):
                raw = b'unknown checkpoint bytes'
                self.assertIs(module.project_catalog_bytes_chain(case.root, 'materials.json', raw, case.ledgers), raw)
                with self.assertRaises(AssertionError):
                    module.project_catalog_bytes_chain(case.root, 'materials.json', raw, list(reversed(case.ledgers)))


if __name__ == '__main__':
    unittest.main()
