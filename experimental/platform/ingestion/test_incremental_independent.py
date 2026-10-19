"""Independent protocol, pinned-boundary and evidence regression checks.

Synthetic transports exercise failure paths without contacting any provider.
The real packaged review boundary is read only; nothing grants admission.
"""
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import nomad_incremental as inc
from nomad_review_boundary import load_review_boundary
from test_nomad_batch import fixture


def payload(rows, *, total=None, cursor=None):
    pagination = {'total': len({row['entry_id'] for row in rows}) if total is None else total}
    if cursor is not None:
        pagination['next_page_after_value'] = cursor
    return 200, {}, inc.canonical({'data': rows, 'pagination': pagination})


def authors(*entry_ids):
    return payload([{'entry_id': entry_id, 'authors': [{'name': 'Test Scientist'}],
                     'references': ['https://example.org/synthetic-evidence']}
                    for entry_id in entry_ids])


class Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, endpoint, body, limit):
        self.calls.append((endpoint, copy.deepcopy(body), limit))
        if not self.responses:
            raise AssertionError('Unexpected extra public request')
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class IndependentIncrementalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boundary = load_review_boundary()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        # This also checks that readers/writers release Windows SQLite handles.
        self.temp.cleanup()

    def init(self, **kwargs):
        return inc.init_store(self.root, boundary=self.boundary, **kwargs)

    def update(self, *responses):
        transport = Transport(*responses)
        result = inc.update(self.root, transport=transport, clock=lambda: 1_800_000_000)
        self.assertEqual(transport.responses, [], 'A planned request was unexpectedly skipped')
        return result

    def baseline(self):
        with closing(sqlite3.connect(self.root / inc.DB_NAME)) as database:
            value = database.execute("SELECT value FROM metadata WHERE key='baseline'").fetchone()[0]
        return json.loads(value)

    def test_real_boundary_blocks_remapped_entries_without_promoting_examples(self):
        for label in ('formal_admitted24', 'unadmitted_example62', 'legacy_example7'):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                entry_id = next(key for key, labels in self.boundary['entries'].items() if label in labels)
                inc.init_store(directory, boundary=self.boundary, entry_ids=[entry_id])
                row = fixture(entry_id, 'synthetic_changed_provider_identity')
                result = inc.update(directory, transport=Transport(payload([row]), authors(entry_id)))
                self.assertEqual(result['status'], 'complete')
                self.assertEqual(result['formal_project_total'], 1124)
                self.assertEqual(result['admitted_delta'], 0)
                self.assertEqual(result['candidate_packet']['candidates'], [])
                exclusion = result['gate_exclusions'][0]
                self.assertEqual(exclusion['provider_entry_id'], entry_id)
                self.assertIn(label, exclusion['review_boundary_labels'])
                self.assertEqual(result['input_changes'][0]['change'], 'new')
                counts = result['candidate_packet']['counts']
                self.assertEqual(counts['acquired_entry_rows'], 1)
                self.assertEqual(counts['excluded_entry_rows'], 1)

    def test_partial_second_page_keeps_previous_complete_baseline(self):
        self.init(pages=2, page_size=1)
        a, b = fixture('a', 'material_a'), fixture('b', 'material_b')
        first = self.update(payload([a], total=2, cursor='a'), authors('a'),
                            payload([b], total=2), authors('b'))
        self.assertTrue(first['baseline_committed'])
        previous = self.baseline()
        changed = copy.deepcopy(a)
        changed['archive']['results']['properties']['structures']['structure_original']['mass_density'] = 8200
        partial = self.update(payload([changed], total=2, cursor='a'), authors('a'), OSError('interrupted'))
        self.assertEqual(partial['status'], 'paused')
        self.assertFalse(partial['baseline_committed'])
        self.assertEqual(previous, self.baseline())
        self.assertFalse(any('removed' in event['change'] for event in partial['candidate_changes']))
        self.assertFalse(inc.report(self.root)['baseline_committed'])
        complete = self.update(payload([b], total=2), authors('b'))
        self.assertTrue(complete['baseline_committed'])
        self.assertEqual([event['provider_entry_id'] for event in complete['input_changes']], ['a'])
        self.assertEqual(set(self.baseline()['entries']), {'a', 'b'})
        self.assertEqual(inc.report(self.root), complete)

    def test_new_calculation_cannot_repackage_a_remapped_known_group(self):
        self.init()
        known_entry = next(key for key, labels in self.boundary['entries'].items()
                           if 'unadmitted_example62' in labels)
        rows = sorted([fixture(known_entry, 'synthetic_remapped_group'),
                       fixture('zz_synthetic_new_calculation', 'synthetic_remapped_group')],
                      key=lambda row: row['entry_id'])
        result = self.update(payload(rows), authors(*(row['entry_id'] for row in rows)))
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertEqual(result['candidate_packet']['counts']['acquired_entry_rows'], 2)
        self.assertEqual(result['candidate_packet']['counts']['excluded_entry_rows'], 2)
        self.assertEqual(result['admitted_delta'], 0)
        self.assertEqual({row['provider_entry_id'] for row in result['gate_exclusions']},
                         {row['entry_id'] for row in rows})
        # The known entry can later disappear from public results; its last
        # observed group relation must not silently grant a new candidate.
        fresh = fixture('zz_synthetic_new_calculation', 'synthetic_remapped_group')
        later = self.update(payload([fresh]), authors(fresh['entry_id']), payload([]))
        self.assertEqual(later['status'], 'complete')
        self.assertEqual(later['candidate_packet']['candidates'], [])
        self.assertEqual(later['candidate_changes'], [])
        self.assertEqual(later['input_changes'][0]['change'], 'withdrawal_pending_review')

    def test_later_page_cannot_silently_drop_continuation(self):
        self.init(pages=3, page_size=1)
        result = self.update(payload([fixture('a')], total=3, cursor='a'), authors('a'),
                             payload([fixture('b')], total=3))
        self.assertEqual(result['status'], 'blocked')
        self.assertFalse(result['baseline_committed'])
        self.assertEqual(self.baseline()['entries'], {})
        self.assertEqual(self.baseline()['candidates'], {})
        self.assertIn('continuation', result['stop_reason'])

    def test_duplicate_density_and_license_json_keys_fail_before_candidate_staging(self):
        replacements = ((b'"mass_density":8000', b'"mass_density":1,"mass_density":8000'),
                        (b'"license":"CC BY 4.0"', b'"license":"unknown","license":"CC BY 4.0"'))
        for before, after in replacements:
            with self.subTest(key=before), tempfile.TemporaryDirectory() as directory:
                inc.init_store(directory, boundary=self.boundary)
                raw = payload([fixture()])[2]
                self.assertIn(before, raw)
                result = inc.update(directory, transport=Transport((200, {}, raw.replace(before, after))))
                self.assertEqual(result['status'], 'blocked')
                self.assertFalse(result['baseline_committed'])
                self.assertEqual(result['candidate_packet']['candidates'], [])
                with closing(sqlite3.connect(Path(directory) / inc.DB_NAME)) as database:
                    self.assertIsNone(database.execute('SELECT raw FROM attempts').fetchone()[0])

    def test_duplicate_attribution_property_key_does_not_select_last_author(self):
        self.init()
        attribution = authors('entry_1')[2].replace(b'"name":"Test Scientist"',
                                                   b'"name":"First Scientist","name":"Test Scientist"')
        result = self.update(payload([fixture()]), (200, {}, attribution))
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertEqual(self.baseline()['entries'], {})
        self.assertEqual(self.baseline()['candidates'], {})

    def test_identical_author_rows_are_idempotent_but_partial_names_are_held(self):
        self.init()
        author_row = {'entry_id': 'entry_1', 'authors': [{'name': 'Test Scientist'}]}
        initial = self.update(payload([fixture()]), payload([author_row, author_row]))
        self.assertEqual(initial['status'], 'complete')
        self.assertEqual(len(initial['candidate_packet']['candidates']), 1)
        replay = self.update(payload([fixture()]), payload([author_row]))
        self.assertEqual(replay['input_changes'], [])
        self.assertEqual(replay['candidate_changes'], [])
        malformed = {'entry_id': 'entry_1', 'authors': [{'name': 'Test Scientist'}, {'name': ''}]}
        result = self.update(payload([fixture()]), payload([malformed]))
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertIn('missing_attribution', [row['reason'] for row in result['gate_exclusions']])
        self.assertEqual(result['candidate_changes'][0]['change'], 'removed_from_candidate_queue_pending_review')

    def test_report_hashes_bind_exact_public_request_and_geometry_free_response(self):
        self.init(entry_ids=['entry_1'])
        archive_response, attribution_response = payload([fixture()]), authors('entry_1')
        result = self.update(archive_response, attribution_response)
        acquisition = result['acquisition']
        self.assertEqual(len(acquisition), 2)
        self.assertEqual(result['review_boundary_sha256'], self.boundary['sha256'])
        self.assertEqual(result['profile_sha256'], inc.digest(inc.status(self.root)['profile']))
        for record, raw in zip(acquisition, (archive_response[2], attribution_response[2])):
            self.assertEqual(record['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(record['bytes'], len(raw))
            self.assertEqual(record['request_sha256'], inc.digest(record['request']))
            self.assertEqual(record['request']['owner'], 'public')
            self.assertEqual(record['url'], inc.API + record['endpoint'])
            inc.assert_no_geometry(json.loads(raw))
        candidate = result['candidate_packet']['candidates'][0]
        self.assertEqual(candidate['evidence']['sha256'], acquisition[0]['sha256'])
        self.assertEqual(candidate['evidence']['request_sha256'], acquisition[0]['request_sha256'])
        self.assertTrue(candidate['source_url'].endswith('/entry_1'))
        self.assertEqual(candidate['density']['unit'], 'kg/m^3')
        before = (self.root / inc.DB_NAME).read_bytes()
        self.assertEqual(inc.report(self.root), result)
        self.assertEqual(before, (self.root / inc.DB_NAME).read_bytes())

    def test_failed_exact_recheck_never_records_confirmed_withdrawal(self):
        self.init()
        self.update(payload([fixture()]), authors('entry_1'))
        previous = self.baseline()
        partial = self.update(payload([]), OSError('temporary public lookup failure'))
        self.assertFalse(partial['baseline_committed'])
        self.assertEqual(previous, self.baseline())
        self.assertEqual(partial['input_changes'], [])
        result = self.update(payload([]))
        self.assertEqual(result['input_changes'][0]['change'], 'withdrawal_pending_review')
        self.assertIn('not confirmed deletion', result['input_changes'][0]['meaning'])
        self.assertEqual(result['admitted_delta'], 0)


if __name__ == '__main__':
    unittest.main()
