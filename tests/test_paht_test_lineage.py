"""Exact additive PAHT test compatibility, anchored at the accepted public tree.

This independent new test pins the successor ledger. The ledger pins five old
files; none embeds its own successor digest. Recorded exact byte edits recover
the accepted predecessor bytes, without replacing any historical fixture.
These source/test hashes are not publisher-artifact hashes or science validation.
"""
import ast
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import provenance_corrections as history
from test_helper_lineage import FIRST_ANCHOR, apply_byte_edits

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = 'tests/fixtures/paht_test_updates_v0240.json'
LEDGER_SHA256 = '0b9979aa3f3e015aad30762d1fa92f554c3411587a8dc6a7effe9c671ad3a411'
HELPER = 'tests/provenance_corrections.py'
PREDECESSORS = {
    HELPER: 'e5bf06ae239c9ea8f7db6d767aa6c35a00f88b85a07830858cbc499a9f4de5fe',
    'tests/test_helper_lineage.py': 'b2af5a64ef777d1aa59e2ff763f7f1b07f7bebc69f541f344921c7f28e9d6ac4',
    'tests/test_temperature_plot_preservation.py': '906da60f3065d901d6d618cdc439bb639beb422e5074e9f026b1a48cf557bc1a',
    'tests/test_pa12_cf15_inspection.py': '7688ab79ec0ab39b00e28f406040363a1238b14c430f2ddd47fc5cdcc1f9f83a',
    'tests/test_pa12_cf15_observations.py': '874539ebb135346d2eeecdc2bbb3cc52a95d9b308e0a91e7a8ebe73a22bf0e4f',
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def recover_predecessor(current, edits):
    reverse = []
    delta = 0
    for edit in edits:
        before, after = edit['before'], edit['after']
        reverse.append({'offset': edit['offset'] + delta, 'before': after, 'after': before})
        delta += len(after.encode('utf-8')) - len(before.encode('utf-8'))
    return apply_byte_edits(current, reverse)


def methods(source):
    result = {}
    lines = source.decode('utf-8').splitlines(keepends=True)
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, ast.FunctionDef):
                    result[node.name + '.' + method.name] = ''.join(lines[method.lineno - 1:method.end_lineno])
    return result


class PAHTTestLineageTests(unittest.TestCase):
    def test_exact_new_ledger_pin_review_and_five_file_allowlist(self):
        ledger = history.PAHT_TEST_UPDATES
        self.assertEqual(sha((ROOT / LEDGER_PATH).read_bytes()), LEDGER_SHA256)
        self.assertEqual(ledger['release'], '0.24.0')
        self.assertEqual(ledger['scope'], 'paht_source_filter_and_test_lineage_only')
        self.assertEqual(ledger['review'], {
            'kind': 'current_paht_compatibility_review', 'review_date': '2026-10-03',
            'baseline_commit': '828ca90a4a32f4744f0e18ea704965cc0ec7f56e',
            'baseline_tree': '200dbdbf7aab4832aa3293aeec1c8e83ac18a9e9',
            'baseline_file_count': 258, 'historical_review_claimed': False})
        entries = ledger['approved_test_updates']
        self.assertEqual(len(entries), 5)
        self.assertEqual({e['filename']: e['previous_sha256'] for e in entries}, PREDECESSORS)
        self.assertNotIn('tests/test_paht_test_lineage.py', PREDECESSORS)
        self.assertNotIn(LEDGER_PATH, PREDECESSORS)

    def test_every_successor_is_actual_and_exact_edits_recover_accepted_bytes(self):
        for change in history.PAHT_TEST_UPDATES['approved_test_updates']:
            with self.subTest(filename=change['filename']):
                actual = (ROOT / change['filename']).read_bytes()
                self.assertEqual(sha(actual), change['sha256'])
                self.assertEqual(history.reviewed_paht_test_hash(change['filename'],
                    PREDECESSORS[change['filename']]), sha(actual))
                before = recover_predecessor(actual, change['edits'])
                self.assertEqual(sha(before), PREDECESSORS[change['filename']])
                self.assertEqual(apply_byte_edits(before, change['edits']), actual)
                self.assertTrue(change['reason'].strip())
                # No source file can authenticate its own current hash.
                self.assertNotIn(change['sha256'].encode('ascii'), actual)

    def test_all_35_preexisting_fixtures_are_byte_identical(self):
        fixtures = history.PAHT_TEST_UPDATES['unchanged_fixture_sha256']
        self.assertEqual(len(fixtures), 35)
        self.assertIn('tests/fixtures/helper_bootstrap_bridge_20261003.json', fixtures)
        self.assertIn('tests/fixtures/helper_maintenance_updates_20261003.json', fixtures)
        for filename, expected in fixtures.items():
            with self.subTest(filename=filename):
                self.assertEqual(sha((ROOT / filename).read_bytes()), expected)

    def test_only_reviewed_test_methods_change_and_no_method_is_dropped(self):
        allowed = {
            'tests/test_helper_lineage.py': {
                'HelperLineageTests.test_full_self_traversal_ends_at_actual_current_helper_bytes',
                'HelperLineageTests.test_direct_tail_binds_both_actual_files_after_exact_predecessors',
                'HelperLineageTests.test_changed_actual_bytes_and_forged_successors_fail_direct_comparison'},
            'tests/test_temperature_plot_preservation.py': {
                'TemperaturePlotPreservationTests.test_historical_tests_and_fixtures_have_only_reviewed_ordering_deltas'},
            'tests/test_pa12_cf15_inspection.py': {
                'PA12InspectionTests.test_default_mixed_subsets_reverse_ids_and_both_groupings'},
            'tests/test_pa12_cf15_observations.py': {
                'PA12SourceTranscriptionTests.test_family_source_dataset_spoofing_cannot_escape_guards',
                'PA12SourceTranscriptionTests.test_legacy_clones_do_not_expand_or_break_the_six_cell_contract',
                'PA12SourceTranscriptionTests.test_actual_source_payload_is_closed_in_runtime',
                'PA12SourceTranscriptionTests.test_catalog_reads_and_source_text_use_dependency_free_guards'},
        }
        for change in history.PAHT_TEST_UPDATES['approved_test_updates']:
            if change['filename'] == HELPER:
                continue
            actual = (ROOT / change['filename']).read_bytes()
            old_methods = methods(recover_predecessor(actual, change['edits']))
            new_methods = methods(actual)
            self.assertEqual(set(new_methods), set(old_methods), change['filename'])
            changed = {name for name in old_methods if old_methods[name] != new_methods[name]}
            self.assertEqual(changed, allowed[change['filename']], change['filename'])
        change = next(e for e in history.PAHT_TEST_UPDATES['approved_test_updates']
                      if e['filename'] == 'tests/test_pa12_cf15_inspection.py')
        actual = (ROOT / change['filename']).read_bytes()
        before = recover_predecessor(actual, change['edits'])
        old = b"view.build_observation_inspection(quantity=PA12_QUANTITY)['facets']"
        new = b"view.build_observation_inspection(quantity=PA12_QUANTITY, source_id=PA12_SOURCE)['facets']"
        self.assertEqual(before.count(old), 1)
        self.assertEqual(before.replace(old, new, 1), actual)

    def test_old_source_family_scopes_are_exactly_four_edits(self):
        change = next(e for e in history.PAHT_TEST_UPDATES['approved_test_updates']
                      if e['filename'] == 'tests/test_pa12_cf15_observations.py')
        actual = (ROOT / change['filename']).read_bytes()
        before = recover_predecessor(actual, change['edits'])
        old = b'if not is_pa12_record(r)'
        new = b'if r["observation_type"] == "experiment_derived_model_dependent"'
        self.assertEqual(before.count(old), 2)
        expected = before.replace(old, new)
        changes = (
            (b'        validate_pa12_sources(self.sources["records"][:-1])',
             b'        validate_pa12_sources([s for s in self.sources["records"] if s["id"] != PA12_SOURCE])'),
            (b'        candidate["records"][-6] = record',
             b'        target = next(i for i, r in enumerate(candidate["records"]) if r["id"] == record["id"])\n'
             b'        candidate["records"][target] = record'),
        )
        for old, new in changes:
            self.assertEqual(before.count(old), 1)
            expected = expected.replace(old, new, 1)
        self.assertEqual(expected, actual)

    def test_helper_keeps_every_prior_function_and_appends_only_the_new_tail(self):
        change = next(e for e in history.PAHT_TEST_UPDATES['approved_test_updates']
                      if e['filename'] == HELPER)
        actual = (ROOT / HELPER).read_bytes()
        before = recover_predecessor(actual, change['edits'])
        def functions(source):
            lines = source.decode('utf-8').splitlines(keepends=True)
            return {node.name: ''.join(lines[node.lineno - 1:node.end_lineno])
                    for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
        old_functions, new_functions = functions(before), functions(actual)
        self.assertEqual(set(new_functions), set(old_functions) | {'reviewed_paht_test_hash'})
        for name, old in old_functions.items():
            with self.subTest(function=name):
                if name == 'reviewed_test_hash':
                    old_tail = '    return reviewed_current_test_hash(filename, expected)\n'
                    new_tail = ('    expected = reviewed_current_test_hash(filename, expected)\n'
                                '    return reviewed_paht_test_hash(filename, expected)\n')
                    self.assertEqual(old.count(old_tail), 1)
                    self.assertEqual(new_functions[name], old.replace(old_tail, new_tail, 1))
                else:
                    self.assertEqual(new_functions[name], old)

    def test_full_chain_and_direct_chain_both_end_at_actual_helper_bytes(self):
        actual = sha((ROOT / HELPER).read_bytes())
        self.assertEqual(history.reviewed_test_hash(HELPER, FIRST_ANCHOR), actual)
        previous = history.CURRENT_HELPER_UPDATES['approved_test_updates'][0]
        accepted = history.reviewed_current_test_hash(HELPER, previous['previous_sha256'])
        self.assertEqual(accepted, PREDECESSORS[HELPER])
        self.assertEqual(history.reviewed_paht_test_hash(HELPER, accepted), actual)
        source = inspect.getsource(history.reviewed_test_hash)
        self.assertLess(source.index("updates = PA12_TEST_UPDATES['approved_test_updates']"),
                        source.index('expected = reviewed_current_test_hash(filename, expected)'))
        self.assertLess(source.index('expected = reviewed_current_test_hash(filename, expected)'),
                        source.index('return reviewed_paht_test_hash(filename, expected)'))
        # The original API still cannot resume from an arbitrary later release.
        for anchor in (PREDECESSORS[HELPER], actual, previous['previous_sha256']):
            with self.subTest(anchor=anchor), self.assertRaises(AssertionError):
                history.reviewed_test_hash(HELPER, anchor)
        with patch.object(history, 'reviewed_current_test_hash', side_effect=lambda filename, expected: expected):
            with self.assertRaisesRegex(AssertionError, 'Broken PAHT test-update provenance'):
                history.reviewed_test_hash(HELPER, FIRST_ANCHOR)

    def test_new_tail_rejects_missing_duplicate_foreign_entries_and_bad_metadata(self):
        original = history.PAHT_TEST_UPDATES
        mutations = []
        for kind in ('missing', 'duplicate', 'foreign', 'wrong filename', 'extra field',
                     'wrong review', 'missing review', 'wrong scope', 'wrong release', 'extra top field'):
            value = deepcopy(original)
            entries = value['approved_test_updates']
            if kind == 'missing':
                entries.pop()
            elif kind == 'duplicate':
                entries[1] = deepcopy(entries[0])
            elif kind == 'foreign':
                entries.append(dict(entries[0], filename='foreign.py'))
            elif kind == 'wrong filename':
                entries[0]['filename'] = 'foreign.py'
            elif kind == 'extra field':
                entries[0]['unreviewed'] = True
            elif kind == 'wrong review':
                value['review']['historical_review_claimed'] = True
            elif kind == 'missing review':
                del value['review']
            elif kind == 'wrong scope':
                value['scope'] = 'scientific_validation'
            elif kind == 'wrong release':
                value['release'] = '0.23.0'
            else:
                value['unreviewed'] = True
            mutations.append((kind, value))
        for target in PREDECESSORS:
            for field, value in (('previous_sha256', '0' * 64), ('reason', ' '),
                                 ('sha256', 'not a digest'), ('sha256', 'A' * 64), ('edits', [])):
                altered = deepcopy(original)
                next(e for e in altered['approved_test_updates'] if e['filename'] == target)[field] = value
                mutations.append((target + ':' + field, altered))
        for field, value in (('offset', -1), ('offset', True), ('before', None),
                             ('after', None), ('unreviewed', 'extra')):
            altered = deepcopy(original)
            altered['approved_test_updates'][0]['edits'][0][field] = value
            mutations.append(('edit:' + field, altered))
        for label, value in mutations:
            for filename, anchor in ((HELPER, PREDECESSORS[HELPER]), ('unknown.py', 'unchanged')):
                with self.subTest(mutation=label, filename=filename), patch.object(history, 'PAHT_TEST_UPDATES', value):
                    with self.assertRaises(AssertionError):
                        history.reviewed_paht_test_hash(filename, anchor)

    def test_changed_bytes_and_forged_successors_fail_even_with_valid_digest_syntax(self):
        for change in history.PAHT_TEST_UPDATES['approved_test_updates']:
            filename = change['filename']
            actual = (ROOT / filename).read_bytes()
            for modified in (b'!' + actual[1:], actual + b'\n'):
                self.assertNotEqual(sha(modified), history.reviewed_paht_test_hash(filename, change['previous_sha256']))
                with self.assertRaises(AssertionError):
                    before = recover_predecessor(modified, change['edits'])
                    self.assertEqual(sha(before), change['previous_sha256'])
            altered = deepcopy(history.PAHT_TEST_UPDATES)
            next(e for e in altered['approved_test_updates'] if e['filename'] == filename)['sha256'] = '0' * 64
            with patch.object(history, 'PAHT_TEST_UPDATES', altered):
                self.assertNotEqual(sha(actual), history.reviewed_paht_test_hash(filename, change['previous_sha256']))
            self.assertNotEqual(sha((json.dumps(altered, ensure_ascii=False, indent=2) + '\n').encode()), LEDGER_SHA256)

    def test_new_tail_accepts_only_exact_predecessors_and_leaves_unknown_paths_unchanged(self):
        for change in history.PAHT_TEST_UPDATES['approved_test_updates']:
            for anchor in ('', '0' * 64, FIRST_ANCHOR, change['sha256']):
                with self.subTest(filename=change['filename'], anchor=anchor), self.assertRaises(AssertionError):
                    history.reviewed_paht_test_hash(change['filename'], anchor)
        for filename in ('unknown.py', 'materials_boundaries/engine.py', HELPER + '.backup'):
            self.assertEqual(history.reviewed_paht_test_hash(filename, 'unchanged'), 'unchanged')
            self.assertEqual(history.reviewed_test_hash(filename, 'unchanged'), 'unchanged')


if __name__ == '__main__':
    unittest.main()
