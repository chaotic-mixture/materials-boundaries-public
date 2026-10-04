"""Current-reviewed test-helper lineage, not independent scientific validation.

Trust is anchored in the reviewed repository snapshot: the helper pins bootstrap
source evidence; this new test pins the separate tail; the tail pins helper and
adapted guard bytes. No file embeds its own cryptographic digest.
"""
import ast
from copy import deepcopy
import difflib
import hashlib
import inspect
import json
from pathlib import Path
from viscoelastic_preservation import pre_viscoelastic_bytes
import unittest
from unittest.mock import patch

import provenance_corrections as history

ROOT = Path(__file__).resolve().parents[1]
HELPER = 'tests/provenance_corrections.py'
DIRECT_GUARD = 'tests/test_temperature_plot_preservation.py'
# The first recorded anchor, not a current/intermediate release resume point.
FIRST_ANCHOR = '4ebebdb77ec12dbb44a2cc9b659f9ce9bd855a21b9b296ed16c8001e5124d730'
TAIL_SHA256 = 'b4ce0814282d40564b97ab6c877c13d83d353a524e2394dc7206740d73246a92'
BRIDGE_CANONICAL_SHA256 = 'f3684e8c8f6ddfbc2fd9bef88bc2918af3a0460eeee6f85cbde9de00b98325ae'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def git_blob(value):
    return hashlib.sha1(b'blob ' + str(len(value)).encode('ascii') + b'\0' + value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def apply_byte_edits(source, edits):
    """Apply bounded exact byte edits, never a fuzzy patch or executable source."""
    result = bytearray()
    end = 0
    for edit in edits:
        if set(edit) != {'offset', 'before', 'after'}:
            raise AssertionError('Unexpected byte-edit fields')
        offset, before, after = edit['offset'], edit['before'].encode('utf-8'), edit['after'].encode('utf-8')
        if (type(offset) is not int or offset < end or offset > len(source)
                or source[offset:offset + len(before)] != before or before == after):
            raise AssertionError('Invalid or out-of-order exact byte edit')
        result.extend(source[end:offset])
        result.extend(after)
        end = offset + len(before)
    result.extend(source[end:])
    return bytes(result)


class HelperLineageTests(unittest.TestCase):
    def test_new_fixture_pins_and_current_review_scope(self):
        bridge = history.HELPER_BOOTSTRAP_BRIDGE
        self.assertEqual(sha(canonical(bridge)), BRIDGE_CANONICAL_SHA256)
        self.assertEqual(sha((ROOT / 'tests/fixtures/helper_maintenance_updates_20261003.json').read_bytes()), TAIL_SHA256)
        self.assertEqual(bridge['scope'], 'test_helper_self_lineage_only')
        self.assertEqual(bridge['review']['kind'], 'current_review_of_reconstructed_public_bootstrap')
        self.assertFalse(bridge['review']['historical_review_claimed'])
        self.assertFalse(history.CURRENT_HELPER_UPDATES['review']['historical_review_claimed'])
        self.assertEqual(bridge['review']['review_date'], '2026-10-03')
        self.assertEqual(history.CURRENT_HELPER_UPDATES['review']['review_date'], '2026-10-03')

    def test_public_source_blob_and_exact_reconstruction(self):
        bridge = history.HELPER_BOOTSTRAP_BRIDGE
        evidence = bridge['evidence']
        public = evidence['public_source_utf8'].encode('utf-8')
        self.assertEqual(evidence['filename'], HELPER)
        self.assertEqual(sha(public), evidence['public_introduction_sha256'])
        self.assertEqual(len(public), evidence['public_introduction_bytes'])
        self.assertEqual(git_blob(public), evidence['public_introduction_blob'])
        self.assertEqual(evidence['public_introduction_commit'], '6476616c662fe6ff5f6b1ecf68800653f9aad166')
        self.assertEqual(evidence['public_introduction_tree'], '421f60c9f204513d09113846907f3eea450c3a52')
        self.assertEqual(evidence['public_parent_commit'], 'e0433e64847f32e9783230fda74c12a7a28a8e21')
        self.assertEqual(evidence['public_parent_contents'], ['LICENSE'])
        self.assertEqual(evidence['pre_observation_parent_blob'], git_blob(public))
        self.assertEqual(evidence['predecessor_origin'], 'reconstructed_from_public_source_not_retrieved_git_blob')
        predecessor = public
        self.assertEqual(len(evidence['reverse_edits']), 4)
        for edit in evidence['reverse_edits']:
            self.assertEqual(set(edit), {'before', 'after'})
            before, after = edit['before'].encode('utf-8'), edit['after'].encode('utf-8')
            self.assertEqual(predecessor.count(before), 1)
            predecessor = predecessor.replace(before, after, 1)
        self.assertEqual(len(predecessor), evidence['predecessor_bytes'])
        self.assertEqual(sha(predecessor), evidence['predecessor_sha256'])
        change, = bridge['approved_test_updates']
        self.assertEqual((change['filename'], change['previous_sha256'], change['sha256']),
                         (HELPER, sha(predecessor), sha(public)))
        self.assertEqual(history.COMPRESSIBILITY_TEST_UPDATES['approved_test_updates'][HELPER]['sha256'], sha(predecessor))
        diff = ''.join(difflib.unified_diff(predecessor.decode().splitlines(keepends=True),
            public.decode().splitlines(keepends=True), fromfile='reconstructed_prepublic.py', tofile='public_v016.py'))
        self.assertEqual(diff, evidence['forward_unified_diff_utf8'])
        self.assertEqual(sha(diff.encode('utf-8')), evidence['forward_unified_diff_sha256'])
        self.assertEqual(evidence['forward_unified_diff_sha256'], 'e3b750841a1754adf3696b18f4f616252de1bf358eef43a00b60bf9816a25562')

    def test_every_later_public_endpoint_matches_exact_bytes_and_old_ledger(self):
        evidence = history.HELPER_BOOTSTRAP_BRIDGE['evidence']
        source = evidence['public_source_utf8'].encode('utf-8')
        self.assertEqual([s['ledger'] for s in evidence['subsequent_public_steps']], [
            'observation_test_updates_v0170.json', 'wave_test_updates_v0180.json',
            'hbn_test_updates_v0190.json', 'pa12_test_updates_v0220.json'])
        for step in evidence['subsequent_public_steps']:
            with self.subTest(commit=step['public_commit']):
                ledger = json.loads((ROOT / 'tests/fixtures' / step['ledger']).read_text())['approved_test_updates'][HELPER]
                self.assertEqual(sha(source), step['previous_sha256'])
                self.assertEqual(ledger['previous_sha256'], sha(source))
                source = apply_byte_edits(source, step['edits'])
                self.assertEqual((len(source), sha(source), git_blob(source)),
                                 (step['bytes'], step['sha256'], step['git_blob']))
                self.assertEqual(ledger['sha256'], sha(source))
                self.assertTrue(ledger['reason'].strip())
        accepted = evidence['accepted_public_helper']
        self.assertEqual((len(source), sha(source), git_blob(source)),
                         (accepted['bytes'], accepted['sha256'], accepted['git_blob']))
        self.assertEqual(evidence['accepted_public_commit'], '6b351cc15126f50563eb18740103760f00b9282a')
        self.assertEqual(evidence['accepted_public_tree'], 'a50b4c986f9d10d61f5aef4cfa0e4a3ad32a12dd')
        current = history.CURRENT_HELPER_UPDATES['approved_test_updates'][0]
        self.assertEqual(current['filename'], HELPER)
        self.assertEqual(current['previous_sha256'], sha(source))

    def test_full_self_traversal_ends_at_actual_current_helper_bytes(self):
        self.assertEqual(history.COMPRESSIBILITY_TEST_UPDATES['approved_test_updates'][HELPER]['previous_sha256'], FIRST_ANCHOR)
        self.assertEqual(history.reviewed_test_hash(HELPER, FIRST_ANCHOR), sha((ROOT / HELPER).read_bytes()))
        source = inspect.getsource(history.reviewed_test_hash)
        self.assertLess(source.index("change = PUBLIC_BASELINE['approved_test_updates']"),
                        source.index('_reviewed_bootstrap_hash(filename, expected)'))
        self.assertLess(source.index('_reviewed_bootstrap_hash(filename, expected)'),
                        source.index("updates = OBSERVATION_TEST_UPDATES['approved_test_updates']"))
        self.assertLess(source.index('expected = reviewed_current_test_hash(filename, expected)'),
                        source.index('return reviewed_paht_test_hash(filename, expected)'))
        self.assertTrue(source.rstrip().endswith('return reviewed_paht_test_hash(filename, expected)'))

    def test_direct_tail_binds_both_actual_files_after_exact_predecessors(self):
        baseline = json.loads((ROOT / 'tests/fixtures/pre_temperature_plot_v0230.json').read_text())
        self.assertEqual(baseline['historical_test_sha256'][HELPER],
                         '5afbaae797599ac9321ea9a59c925f4877d35799dd283338cd70a3facb0f022c')
        for change in history.CURRENT_HELPER_UPDATES['approved_test_updates']:
            with self.subTest(filename=change['filename']):
                actual = sha(pre_viscoelastic_bytes(change['filename'], (ROOT / change['filename']).read_bytes()))
                accepted = history.reviewed_current_test_hash(change['filename'], change['previous_sha256'])
                self.assertEqual(accepted, change['sha256'])
                self.assertEqual(history.reviewed_paht_test_hash(change['filename'], accepted), actual)
        # An arbitrary starting point remains invalid for the *full* traversal.
        with self.assertRaises(AssertionError):
            history.reviewed_test_hash(HELPER, baseline['historical_test_sha256'][HELPER])

    def test_arbitrary_and_intermediate_helper_anchors_fail(self):
        evidence = history.HELPER_BOOTSTRAP_BRIDGE['evidence']
        bad = ['', '0' * 64, evidence['predecessor_sha256'], evidence['public_introduction_sha256'],
               sha((ROOT / HELPER).read_bytes())]
        bad.extend(step['sha256'] for step in evidence['subsequent_public_steps'])
        for anchor in bad:
            with self.subTest(anchor=anchor), self.assertRaises(AssertionError):
                history.reviewed_test_hash(HELPER, anchor)
        for change in history.CURRENT_HELPER_UPDATES['approved_test_updates']:
            for anchor in ('', '0' * 64, FIRST_ANCHOR, change['sha256']):
                with self.subTest(filename=change['filename'], anchor=anchor), self.assertRaises(AssertionError):
                    history.reviewed_current_test_hash(change['filename'], anchor)

    def test_historical_fixture_bytes_and_normalization_functions_are_unchanged(self):
        evidence = history.HELPER_BOOTSTRAP_BRIDGE['evidence']
        for filename, expected in evidence['historical_fixture_sha256'].items():
            with self.subTest(filename=filename):
                self.assertEqual(sha(pre_viscoelastic_bytes(filename, (ROOT / filename).read_bytes())), expected)
        source = (ROOT / HELPER).read_text()
        lines = source.splitlines(keepends=True)
        functions = {node.name: ''.join(lines[node.lineno - 1:node.end_lineno]).encode()
                     for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
        self.assertEqual(set(evidence['unchanged_normalization_function_sha256']), {
            'public_previous_record', 'historical_record', 'historical_temperature_result', 'historical_locales'})
        for name, expected in evidence['unchanged_normalization_function_sha256'].items():
            self.assertEqual(sha(functions[name]), expected, name)

    def test_missing_foreign_duplicate_wrong_or_unreviewed_bridge_fails(self):
        original = history.HELPER_BOOTSTRAP_BRIDGE
        mutations = []
        def altered(label, mutate):
            value = deepcopy(original)
            mutate(value)
            mutations.append((label, value))
        altered('missing entries', lambda v: v.pop('approved_test_updates'))
        altered('empty entries', lambda v: v.__setitem__('approved_test_updates', []))
        altered('duplicate entry', lambda v: v['approved_test_updates'].append(deepcopy(v['approved_test_updates'][0])))
        altered('foreign entry', lambda v: v['approved_test_updates'].append({'filename': 'foreign.py'}))
        for field, value in [('filename', 'foreign.py'), ('previous_sha256', '0' * 64),
                             ('sha256', '0' * 64), ('reason', ' ')]:
            altered(field, lambda v, k=field, x=value: v['approved_test_updates'][0].__setitem__(k, x))
        for field in ('public_introduction_commit', 'public_introduction_tree', 'public_introduction_blob',
                      'public_parent_commit', 'pre_observation_parent_commit', 'pre_observation_parent_blob',
                      'predecessor_origin', 'public_introduction_sha256', 'predecessor_sha256',
                      'forward_unified_diff_sha256', 'filename', 'accepted_public_commit', 'accepted_public_tree'):
            altered(field, lambda v, k=field: v['evidence'].__setitem__(k, 'wrong'))
        for field in ('public_introduction_bytes', 'predecessor_bytes'):
            altered(field, lambda v, k=field: v['evidence'].__setitem__(k, v['evidence'][k] + 1))
        for field in ('public_source_utf8', 'forward_unified_diff_utf8'):
            altered(field, lambda v, k=field: v['evidence'].__setitem__(k, v['evidence'][k] + '\n'))
        altered('missing evidence', lambda v: v.pop('evidence'))
        altered('reversed edits', lambda v: v['evidence']['reverse_edits'].reverse())
        altered('changed reconstruction', lambda v: v['evidence']['reverse_edits'][0].__setitem__('after', ' '))
        altered('changed later bytes', lambda v: v['evidence']['subsequent_public_steps'][0]['edits'][0].__setitem__('after', ' '))
        altered('reversed later chain', lambda v: v['evidence']['subsequent_public_steps'].reverse())
        altered('claims historical review', lambda v: v['review'].__setitem__('historical_review_claimed', True))
        altered('blank review reason', lambda v: v['review'].__setitem__('reason', ' '))
        altered('wrong review date', lambda v: v['review'].__setitem__('review_date', '2000-01-01'))
        for label, value in mutations:
            for filename, anchor in ((HELPER, FIRST_ANCHOR), ('unknown.py', 'unchanged')):
                with self.subTest(mutation=label, filename=filename), patch.object(history, 'HELPER_BOOTSTRAP_BRIDGE', value):
                    with self.assertRaises(AssertionError):
                        history.reviewed_test_hash(filename, anchor)

    def test_current_tail_rejects_missing_duplicate_foreign_entries_and_bad_metadata(self):
        original = history.CURRENT_HELPER_UPDATES
        mutations = []
        for target in (HELPER, DIRECT_GUARD):
            for field, value in [('previous_sha256', '0' * 64), ('reason', ' '), ('sha256', 'not a digest'), ('sha256', 'A' * 64)]:
                mutated = deepcopy(original)
                next(e for e in mutated['approved_test_updates'] if e['filename'] == target)[field] = value
                mutations.append((target + ':' + field, mutated))
        for kind in ('missing', 'duplicate', 'foreign', 'wrong filename', 'extra field', 'wrong review', 'missing review', 'wrong scope'):
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
            else:
                value['scope'] = 'scientific_validation'
            mutations.append((kind, value))
        for label, value in mutations:
            for filename, anchor in ((HELPER, original['approved_test_updates'][0]['previous_sha256']),
                                     ('unknown.py', 'unchanged')):
                with self.subTest(mutation=label, filename=filename), patch.object(history, 'CURRENT_HELPER_UPDATES', value):
                    with self.assertRaises(AssertionError):
                        history.reviewed_current_test_hash(filename, anchor)

    def test_new_fixture_loader_rejects_duplicate_keys_at_any_depth(self):
        for raw in ('{"review": 1, "review": 2}', '{"review": {"kind": 1, "kind": 2}}',
                    '{"approved_test_updates": [{"sha256": "a", "sha256": "b"}]}'):
            with self.subTest(raw=raw), patch.object(Path, 'read_text', return_value=raw):
                with self.assertRaises(AssertionError):
                    history._load_lineage_fixture('not_read_from_disk.json')

    def test_exact_byte_edit_parser_rejects_wrong_offsets_bytes_and_order(self):
        edits = [{'offset': 1, 'before': 'b', 'after': 'B'}, {'offset': 3, 'before': 'd', 'after': 'D'}]
        self.assertEqual(apply_byte_edits(b'abcde', edits), b'aBcDe')
        for bad in ([dict(edits[0], offset=-1)], [dict(edits[0], offset=9)],
                    [dict(edits[0], offset=True)], [dict(edits[0], before='z')],
                    [dict(edits[0], after='b')], list(reversed(edits)),
                    [edits[0], edits[0]], [dict(edits[0], arbitrary='field')]):
            with self.subTest(edits=bad), self.assertRaises(AssertionError):
                apply_byte_edits(b'abcde', bad)

    def test_changed_actual_bytes_and_forged_successors_fail_direct_comparison(self):
        for change in history.CURRENT_HELPER_UPDATES['approved_test_updates']:
            filename = change['filename']
            actual = pre_viscoelastic_bytes(filename, (ROOT / filename).read_bytes())
            accepted = history.reviewed_current_test_hash(filename, change['previous_sha256'])
            expected = history.reviewed_paht_test_hash(filename, accepted)
            for changed in (b'!' + actual[1:], actual + b'\n'):
                with self.subTest(filename=filename), self.assertRaises(AssertionError):
                    self.assertEqual(sha(changed), expected)
            altered = deepcopy(history.CURRENT_HELPER_UPDATES)
            next(e for e in altered['approved_test_updates'] if e['filename'] == filename)['sha256'] = '0' * 64
            with patch.object(history, 'CURRENT_HELPER_UPDATES', altered), self.assertRaises(AssertionError):
                accepted = history.reviewed_current_test_hash(filename, change['previous_sha256'])
                self.assertEqual(sha(actual), history.reviewed_paht_test_hash(filename, accepted))
            self.assertNotEqual(sha((json.dumps(altered, ensure_ascii=False, indent=2) + '\n').encode()), TAIL_SHA256)
        evidence = history.HELPER_BOOTSTRAP_BRIDGE['evidence']
        public = evidence['public_source_utf8'].encode()
        predecessor = public
        for edit in evidence['reverse_edits']:
            predecessor = predecessor.replace(edit['before'].encode(), edit['after'].encode(), 1)
        self.assertNotEqual(sha(public + b'\n'), evidence['public_introduction_sha256'])
        self.assertNotEqual(sha(predecessor + b'\n'), evidence['predecessor_sha256'])

    def test_prior_allowlists_predecessors_and_reasons_still_fail_closed(self):
        specifications = [('LEDGER', 'tests/test_predictions.py'),
            ('DIRECTIONAL_TEST_UPDATES', 'tests/test_catalog_cli.py'),
            ('COMPRESSIBILITY_TEST_UPDATES', HELPER),
            ('OBSERVATION_TEST_UPDATES', HELPER), ('WAVE_TEST_UPDATES', HELPER),
            ('HBN_TEST_UPDATES', HELPER), ('PA12_TEST_UPDATES', HELPER)]
        for ledger_name, filename in specifications:
            original = getattr(history, ledger_name)
            anchor = FIRST_ANCHOR if filename == HELPER else original['approved_test_updates'][filename]['previous_sha256']
            for mutation in ('missing file', 'foreign file', 'wrong predecessor', 'blank reason'):
                altered = deepcopy(original)
                entries = altered['approved_test_updates']
                if mutation == 'missing file':
                    del entries[filename]
                elif mutation == 'foreign file':
                    entries['foreign.py'] = deepcopy(entries[filename])
                else:
                    entries[filename]['previous_sha256' if mutation == 'wrong predecessor' else 'reason'] = ' '
                with self.subTest(ledger=ledger_name, mutation=mutation), patch.object(history, ledger_name, altered):
                    with self.assertRaises(AssertionError):
                        history.reviewed_test_hash(filename, anchor)
        # A missing bridge cannot turn the still-present observation edge optional.
        with patch.object(history, '_reviewed_bootstrap_hash', side_effect=lambda filename, expected: expected):
            with self.assertRaisesRegex(AssertionError, 'Broken observation test-update provenance'):
                history.reviewed_test_hash(HELPER, FIRST_ANCHOR)

    def test_public_baseline_predecessor_and_reason_still_fail_closed(self):
        filename = 'tests/test_release_metadata.py'
        original = history.PUBLIC_BASELINE
        change = original['approved_test_updates'][filename]
        for field in ('previous_sha256', 'reason'):
            altered = deepcopy(original)
            altered['approved_test_updates'][filename][field] = ' '
            with self.subTest(field=field), patch.object(history, 'PUBLIC_BASELINE', altered):
                with self.assertRaisesRegex(AssertionError, 'Broken first-public test-update provenance'):
                    history.reviewed_test_hash(filename, change['previous_sha256'])

    def test_bibliography_reversal_still_rejects_duplicate_corrected_notes(self):
        from materials_boundaries.catalog import read_catalog
        sources = {source['id']: source for source in read_catalog('sources')['records']}
        for identifier, changes in history.PUBLIC_BASELINE['source_corrections'].items():
            for change in changes:
                if change['path'][0] != 'claim_notes':
                    continue
                source = deepcopy(sources[identifier])
                source['claim_notes'].append(change['after'])
                with self.subTest(source=identifier), self.assertRaises(AssertionError):
                    history.public_previous_record('sources', source)

    def test_unknown_paths_receive_no_override(self):
        for filename in ('unknown.py', 'materials_boundaries/engine.py', HELPER + '.backup'):
            self.assertEqual(history.reviewed_current_test_hash(filename, 'unchanged'), 'unchanged')
            self.assertEqual(history.reviewed_test_hash(filename, 'unchanged'), 'unchanged')


if __name__ == '__main__':
    unittest.main()
