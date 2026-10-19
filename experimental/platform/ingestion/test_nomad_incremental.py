"""Offline protocol, crash recovery, budgets and review-gate regression tests."""
import copy
from contextlib import closing
from email.utils import formatdate
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import nomad_incremental as inc
from nomad_review_boundary import BASELINE_COMMIT, LEGACY, SOURCES
from test_nomad_batch import fixture

BOUNDARY = {'provider_material_ids': [], 'provider_entry_ids': [], 'sha256': 'test-boundary',
            'baseline_commit': BASELINE_COMMIT, 'formal_project_total': 1108,
            'formal_legacy_count': 1084, 'formal_computed_composition_count': 24,
            'excluded_example_count': 62, 'legacy_example_count': 7,
            'source_sha256': {LEGACY[0]: LEGACY[1],
                              **{path: expected for path, expected, _ in SOURCES.values()}}}


def response(rows, total=None, after=None):
    pagination = {'total': len({row['entry_id'] for row in rows}) if total is None else total}
    if after is not None:
        pagination['next_page_after_value'] = after
    return 200, {}, inc.canonical({'data': rows, 'pagination': pagination})


def attribution(*ids):
    return response([{'entry_id': eid, 'authors': [{'name': 'Scientist'}], 'datasets': []} for eid in ids])


class QueueTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, endpoint, body, limit):
        self.calls.append((endpoint, copy.deepcopy(body), limit))
        if not self.responses:
            raise AssertionError('Unexpected network request')
        result = self.responses.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


class Crash(BaseException):
    pass


class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.now = 1_800_000_000

    def tearDown(self):
        self.tmp.cleanup()

    def init(self, **kwargs):
        inc.init_store(self.root, boundary=BOUNDARY, **kwargs)

    def update(self, transport, **kwargs):
        return inc.update(self.root, transport=transport, clock=lambda: self.now, **kwargs)

    def first_cycle(self, row=None):
        row = row or fixture()
        return self.update(QueueTransport(response([row]), attribution(row['entry_id'])))

    def test_new_unchanged_and_changed_input(self):
        self.init()
        first = self.first_cycle()
        self.assertEqual(first['input_changes'][0]['change'], 'new')
        self.assertEqual(first['candidate_changes'][0]['change'], 'new')
        self.now += 100
        second = self.first_cycle()
        self.assertEqual(second['input_changes'], [])
        self.assertEqual(second['candidate_changes'], [])
        row = fixture()
        row['archive']['results']['properties']['structures']['structure_original']['mass_density'] += 1
        third = self.first_cycle(row)
        self.assertEqual(third['input_changes'][0]['change'], 'changed')
        self.assertEqual(third['candidate_changes'][0]['change'], 'changed')
        self.assertEqual(third['admitted_delta'], 0)
        self.assertEqual(third['formal_project_total'], 1108)

    def test_crash_after_archive_response_is_reused(self):
        self.init()
        def crash(kind, key):
            raise Crash()
        with self.assertRaises(Crash):
            self.update(QueueTransport(response([fixture()])), after_cache=crash)
        transport = QueueTransport(attribution('entry_1'))
        result = self.update(transport)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual([call[0] for call in transport.calls], [inc.ATTRIBUTION])
        self.assertEqual(result['budget']['requests'], 2)

    def test_crash_after_attribution_response_is_reused(self):
        self.init()
        def crash(kind, key):
            if kind == inc.ATTRIBUTION:
                raise Crash()
        with self.assertRaises(Crash):
            self.update(QueueTransport(response([fixture()]), attribution('entry_1')), after_cache=crash)
        result = self.update(QueueTransport())
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['budget']['requests'], 2)

    def test_partial_failure_does_not_commit_baseline(self):
        self.init()
        partial = self.update(QueueTransport(response([fixture()]), OSError('offline')))
        self.assertEqual(partial['status'], 'paused')
        self.assertFalse(partial['baseline_committed'])
        result = self.update(QueueTransport(attribution('entry_1')))
        self.assertEqual(result['input_changes'][0]['change'], 'new')
        self.assertEqual(result['budget']['requests'], 3)

    def test_duplicate_identical_rows_are_coalesced(self):
        self.init()
        result = self.update(QueueTransport(response([fixture(), fixture()]), attribution('entry_1')))
        self.assertEqual(len(result['candidate_packet']['candidates']), 1)
        self.assertEqual(result['diagnostics'][0]['reason'], 'identical_duplicate_coalesced')

    def test_conflicting_duplicates_quarantined_without_order_dependence(self):
        row = fixture()
        row['archive']['results']['properties']['structures']['structure_original']['mass_density'] = 9000
        reports = []
        for rows in ([fixture(), row], [row, fixture()]):
            with tempfile.TemporaryDirectory() as directory:
                inc.init_store(directory, boundary=BOUNDARY)
                reports.append(inc.update(directory, transport=QueueTransport(response(rows), attribution('entry_1'))))
        self.assertEqual(reports[0]['input_changes'], reports[1]['input_changes'])
        self.assertEqual(reports[0]['gate_exclusions'], reports[1]['gate_exclusions'])
        self.assertEqual(reports[0]['candidate_packet']['candidates'], [])

    def test_conflicting_authors_quarantined(self):
        self.init()
        authors = [{'entry_id': 'entry_1', 'authors': [{'name': name}]} for name in ('One', 'Two')]
        result = self.update(QueueTransport(response([fixture()]), response(authors)))
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertEqual(result['gate_exclusions'][0]['reason'], 'conflicting_duplicate_entry')

    def test_material_group_normalization_across_pages(self):
        self.init(pages=2, page_size=1)
        result = self.update(QueueTransport(response([fixture('a')], total=2, after='a'), attribution('a'),
                                             response([fixture('b')], total=2), attribution('b')))
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(result['candidate_packet']['candidates']), 1)
        self.assertEqual(result['candidate_packet']['candidates'][0]['dedup']['sample_entry_count'], 2)

    def test_previous_id_outside_window_is_directly_rechecked(self):
        self.init(page_size=1)
        self.first_cycle()
        transport = QueueTransport(response([fixture('entry_2', 'material_2')]), attribution('entry_2'),
                                   response([fixture()]), attribution('entry_1'))
        result = self.update(transport)
        self.assertEqual(transport.calls[2][1]['query'], {'entry_id': {'any': ['entry_1']}})
        self.assertEqual(len(result['candidate_packet']['candidates']), 2)
        self.assertNotIn('withdrawal_pending_review', [event['change'] for event in result['input_changes']])

    def test_withdrawal_pending_then_reappeared(self):
        self.init()
        self.first_cycle()
        result = self.update(QueueTransport(response([]), response([])))
        self.assertEqual(result['input_changes'][0]['change'], 'withdrawal_pending_review')
        self.assertEqual(result['candidate_changes'][0]['change'], 'removed_from_candidate_queue_pending_review')
        unchanged = self.update(QueueTransport(response([]), response([])))
        self.assertEqual(unchanged['input_changes'], [])
        again = self.first_cycle()
        self.assertEqual(again['input_changes'][0]['change'], 'reappeared')

    def test_incomplete_exact_id_response_cannot_withdraw(self):
        self.init()
        self.first_cycle()
        result = self.update(QueueTransport(response([]), response([], total=1)))
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['input_changes'], [])
        self.assertFalse(result['baseline_committed'])

    def test_missing_density_changes_input_and_removes_candidate(self):
        self.init()
        self.first_cycle()
        row = fixture()
        del row['archive']['results']['properties']['structures']['structure_original']['mass_density']
        result = self.first_cycle(row)
        self.assertEqual(result['input_changes'][0]['change'], 'changed')
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertTrue(result['gate_exclusions'])
        self.assertEqual(result['candidate_changes'][0]['change'], 'removed_from_candidate_queue_pending_review')

    def test_rights_change_quarantines_previous_candidate(self):
        self.init()
        self.first_cycle()
        row = fixture()
        row['archive']['metadata']['license'] = 'unknown'
        result = self.first_cycle(row)
        self.assertEqual(result['gate_exclusions'][0]['reason'], 'rights_quarantine')
        self.assertEqual(result['candidate_packet']['candidates'], [])

    def test_missing_attribution_never_admitted(self):
        self.init()
        result = self.update(QueueTransport(response([fixture()]), response([])))
        self.assertEqual(result['gate_exclusions'][0]['reason'], 'missing_attribution')
        self.assertEqual(result['admitted_delta'], 0)

    def test_rate_limit_cooldown_and_retry_budget_persist(self):
        self.init(retries=1)
        first = self.update(QueueTransport((429, {'Retry-After': '120'}, b'limited')))
        self.assertEqual(first['status'], 'cooldown')
        blocked = self.update(QueueTransport())
        self.assertEqual(blocked['budget']['requests'], 1)
        self.now += 120
        second = self.update(QueueTransport((503, {'Retry-After': '1'}, b'busy')))
        self.assertEqual(second['budget']['retries_used'], 1)
        self.now += 1
        exhausted = self.update(QueueTransport())
        self.assertEqual(exhausted['status'], 'exhausted')
        self.assertEqual(exhausted['budget']['requests'], 2)

    def test_http_date_retry_after_survives_abandon(self):
        self.init()
        date = formatdate(self.now + 60, usegmt=True)
        self.update(QueueTransport((429, {'retry-after': date}, b'')))
        inc.abandon(self.root, 'Test explicit abandonment', clock=lambda: self.now)
        paused = self.update(QueueTransport())
        self.assertEqual(paused['status'], 'cooldown')
        self.assertEqual(paused['budget']['requests'], 0)

    def test_unrepresentable_retry_after_blocks_without_resuming_or_committing(self):
        cases = [('addition_overflow', 429, '9' * 400, None),
                 ('utc_overflow', 503, str(10 ** 20), None),
                 ('integer_digit_limit', 429, '9' * 5000, None),
                 ('platform_utc_oserror', 429, str(10 ** 12), OSError),
                 ('platform_utc_valueerror', 503, str(10 ** 12), ValueError)]
        now = float(self.now)
        original_utc = inc.utc
        for label, code, value, utc_error in cases:
            with self.subTest(case=label):
                store = self.root / label
                inc.init_store(store, boundary=BOUNDARY, retries=3)
                row = fixture()
                initial = inc.update(store, transport=QueueTransport(response([row]),
                    attribution(row['entry_id'])), clock=lambda: now)
                self.assertTrue(initial['baseline_committed'])
                with inc.connect(store, readonly=True) as db:
                    baseline = inc.meta(db, 'baseline')

                def checked_utc(seconds):
                    if utc_error and seconds > now + 10 ** 11:
                        raise utc_error('Synthetic platform timestamp limit')
                    return original_utc(seconds)

                transport = QueueTransport((code, {'Retry-After': value}, b'{}'))
                with patch.object(inc, 'utc', side_effect=checked_utc):
                    blocked = inc.update(store, transport=transport, clock=lambda: now + 100)
                self.assertEqual(blocked['status'], 'blocked')
                self.assertFalse(blocked['baseline_committed'])
                self.assertEqual(blocked['budget'], {'requests': 1, 'bytes_charged': 2, 'retries_used': 0})
                self.assertEqual(blocked['admitted_delta'], 0)
                attempt = blocked['acquisition'][0]
                self.assertEqual(attempt['status'], 'rejected')
                self.assertEqual(attempt['http_status'], code)
                self.assertEqual(attempt['error'], 'Retry-After seconds exceed supported UTC range')
                self.assertNotIn('retry_after_utc', attempt)
                self.assertIsNone(blocked['not_before_utc'])
                # Reopen after a plausible fallback delay; a rejected cooldown
                # must not become a retry even though three retries are allowed.
                resumed = inc.update(store, transport=transport, clock=lambda: now + 1000)
                self.assertEqual(resumed, blocked)
                self.assertEqual(len(transport.calls), 1)
                with inc.connect(store, readonly=True) as db:
                    self.assertEqual(inc.meta(db, 'baseline'), baseline)
                    self.assertEqual(inc.meta(db, 'not_before'), 0)
                    cycle = inc.latest(db)
                    self.assertEqual((cycle['phase'], cycle['page'], cycle['cursor']),
                                     ('scan_archive', 0, None))

    def test_crash_during_network_reserves_attempt_and_bytes(self):
        self.init(retries=0, max_response=1000)
        with self.assertRaises(Crash):
            self.update(QueueTransport(Crash()))
        result = self.update(QueueTransport())
        self.assertEqual(result['status'], 'exhausted')
        self.assertEqual(result['budget']['requests'], 1)
        self.assertEqual(result['budget']['bytes_charged'], 1000)

    def test_budget_exhaustion_requires_explicit_abandon(self):
        self.init(max_requests=1)
        first = self.update(QueueTransport(response([fixture()])))
        self.assertEqual(first['status'], 'exhausted')
        self.assertEqual(self.update(QueueTransport())['cycle_id'], 1)
        inc.abandon(self.root, 'Budget deliberately too small for test')
        result = self.update(QueueTransport(response([])))
        self.assertEqual(result['cycle_id'], 2)
        self.assertEqual(result['input_changes'], [])

    def test_malformed_pagination_is_blocked_without_baseline_commit(self):
        self.init()
        result = self.update(QueueTransport(response([fixture()], total=10, after='wrong_cursor')))
        self.assertEqual(result['status'], 'blocked')
        self.assertFalse(result['baseline_committed'])
        self.assertEqual(result['candidate_packet']['candidates'], [])

    def test_hash_tampering_fails_closed_offline(self):
        self.init()
        self.first_cycle()
        with closing(sqlite3.connect(self.root / inc.DB_NAME)) as db, db:
            db.execute('UPDATE attempts SET raw=? WHERE id=1', (b'{}',))
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            inc.report(self.root)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.update(QueueTransport())

    def test_geometry_is_not_cached(self):
        self.init()
        row = fixture()
        row['archive']['run'] = []
        result = self.update(QueueTransport(response([row])))
        self.assertEqual(result['status'], 'blocked')
        with closing(sqlite3.connect(self.root / inc.DB_NAME)) as db, db:
            self.assertIsNone(db.execute('SELECT raw FROM attempts').fetchone()[0])

    def test_redirect_and_compression_are_rejected(self):
        for code, headers in [(302, {'location': 'https://example.com'}), (200, {'content-encoding': 'gzip'})]:
            with tempfile.TemporaryDirectory() as directory:
                inc.init_store(directory, boundary=BOUNDARY)
                result = inc.update(directory, transport=QueueTransport((code, headers, b'')))
                self.assertEqual(result['status'], 'blocked')

    def test_oversized_response_is_rejected_and_charged(self):
        self.init(max_response=10)
        result = self.update(QueueTransport((200, {}, b'x' * 11)))
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['budget']['bytes_charged'], 11)

    def test_profile_cannot_be_overwritten(self):
        self.init()
        with self.assertRaisesRegex(ValueError, 'already initialized'):
            self.init()

    def test_offline_status_report_do_not_mutate_store(self):
        self.init()
        self.first_cycle()
        before = (self.root / inc.DB_NAME).read_bytes()
        self.assertEqual(inc.status(self.root)['cycle']['status'], 'complete')
        self.assertTrue(inc.report(self.root)['complete'])
        self.assertEqual(before, (self.root / inc.DB_NAME).read_bytes())

    def test_exact_cohort_query_and_validation(self):
        self.init(entry_ids=['entry_1'])
        transport = QueueTransport(response([fixture()]), attribution('entry_1'))
        self.update(transport)
        self.assertEqual(transport.calls[0][1]['query'], {'entry_id': {'any': ['entry_1']}})
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'one page'):
                inc.init_store(directory, boundary=BOUNDARY, entry_ids=['a', 'b'], page_size=1)

    def test_known_entry_remapped_to_new_material_still_held(self):
        boundary = dict(BOUNDARY, provider_entry_ids=['entry_1'], entries={'entry_1': ['unadmitted_example62']})
        inc.init_store(self.root, boundary=boundary)
        result = self.first_cycle(fixture(mid='new_upstream_identity'))
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertEqual(result['gate_exclusions'][0]['reason'], 'known_review_boundary_entry_overlap')
        self.assertEqual(result['gate_exclusions'][0]['review_boundary_labels'], ['unadmitted_example62'])
        self.assertEqual(result['input_changes'][0]['change'], 'new')
        self.assertEqual(result['candidate_packet']['counts']['acquired_entry_rows'], 1)

    def test_known_material_and_composition_are_distinct_gates(self):
        boundary = dict(BOUNDARY, provider_material_ids=['material_1'], compositions={'FeNi': ['formal_admitted24']})
        inc.init_store(self.root, boundary=boundary)
        held = self.first_cycle()
        self.assertEqual(held['gate_exclusions'][0]['reason'], 'known_review_boundary_material_overlap')
        row = fixture(mid='material_2')
        candidate = self.first_cycle(row)['candidate_packet']['candidates'][0]
        self.assertIn('composition_overlap_advisory', candidate)

    def test_explicit_wrong_density_unit_is_quarantined(self):
        self.init()
        row = fixture()
        row['archive']['results']['properties']['structures']['structure_original']['mass_density_unit'] = 'g/cm^3'
        result = self.first_cycle(row)
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertIn('density', result['gate_exclusions'][0]['reason'])

    def test_first_page_missing_continuation_is_blocked(self):
        self.init()
        result = self.update(QueueTransport(response([fixture()], total=10)))
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('continuation', result['stop_reason'])

    def test_nonfinite_json_is_not_cached(self):
        self.init()
        raw = b'{"data":[],"pagination":{"total":NaN}}'
        result = self.update(QueueTransport((200, {}, raw)))
        self.assertEqual(result['status'], 'blocked')

    def test_duplicate_json_property_keys_are_refused(self):
        self.init()
        raw = response([fixture()])[2].replace(b'"mass_density":8000', b'"mass_density":1,"mass_density":8000')
        result = self.update(QueueTransport((200, {}, raw)))
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('Duplicate JSON', result['stop_reason'])

    def test_store_lock_prevents_competing_updates(self):
        self.init()
        with inc.locked(self.root):
            with self.assertRaisesRegex(ValueError, 'already being updated'):
                self.update(QueueTransport())

    def test_early_missing_continuation_on_later_page_is_blocked(self):
        self.init(pages=3, page_size=1)
        result = self.update(QueueTransport(response([fixture('a')], total=3, after='a'), attribution('a'),
                                             response([fixture('b')], total=3)))
        self.assertEqual(result['status'], 'blocked')
        self.assertFalse(result['baseline_committed'])

    def test_previous_cycle_report_and_history_are_offline(self):
        self.init()
        first = self.first_cycle()
        self.first_cycle()
        self.assertEqual(inc.report(self.root, cycle=1), first)
        self.assertEqual(len(inc.status(self.root)['history']), 2)
        with self.assertRaisesRegex(ValueError, 'does not exist'):
            inc.report(self.root, cycle=999)

    def test_null_nested_source_sections_are_gate_failures(self):
        self.init()
        row = fixture()
        row['archive']['results'] = None
        result = self.first_cycle(row)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertTrue(result['gate_exclusions'])

    def test_known_entry_material_remap_hold_survives_later_omission(self):
        boundary = dict(BOUNDARY, provider_entry_ids=['entry_1'], entries={'entry_1': ['unadmitted_example62']})
        inc.init_store(self.root, boundary=boundary)
        self.first_cycle(fixture(mid='remapped_group'))
        transport = QueueTransport(response([fixture('entry_2', 'remapped_group')]), attribution('entry_2'), response([]))
        result = self.update(transport)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['candidate_packet']['candidates'], [])
        self.assertEqual(result['gate_exclusions'][0]['reason'], 'known_review_boundary_material_overlap')
        self.assertIn('unadmitted_example62', result['gate_exclusions'][0]['review_boundary_labels'])

    def test_new_store_requires_exact_current_catalog_scope_before_creation(self):
        mutations = [('formal_project_total', 1081), ('formal_project_total', 1104),
                     ('formal_project_total', 1107), ('formal_legacy_count', 1083),
                     ('formal_project_total', 1103), ('formal_legacy_count', 1079),
                     ('formal_legacy_count', 1057), ('formal_computed_composition_count', 62),
                     ('excluded_example_count', 0), ('legacy_example_count', 0),
                     ('baseline_commit', '4c5656cf6ba0ad1a54b736e0568e97abe4815c29'),
                     ('baseline_commit', 'a592c89ede0dcced22579e56fc68b6fab4c55f49'),
                     ('baseline_commit', '5396fd1cc9df72507785a112a21c2990fb4a7c50'),
                     ('source_sha256', {**BOUNDARY['source_sha256'], LEGACY[0]: '0' * 64})]
        for index, (key, value) in enumerate(mutations):
            root = self.root / str(index)
            boundary = dict(BOUNDARY, **{key: value})
            with self.subTest(field=key, value=value):
                with self.assertRaisesRegex(ValueError, 'initialize a new state directory'):
                    inc.init_store(root, boundary=boundary)
                self.assertFalse(root.exists())

    def test_historical_store_rejects_mutation_without_relabeling_read_only_reports(self):
        self.init()
        self.first_cycle()
        # Retag only this synthetic fixture as a store created by the earlier
        # checkout. No historical user store or published report is modified.
        with inc.connect(self.root) as db, db:
            boundary = inc.meta(db, 'review_boundary')
            boundary.update(baseline_commit='4c5656cf6ba0ad1a54b736e0568e97abe4815c29',
                            formal_project_total=1081, formal_legacy_count=1057,
                            sha256='synthetic-historical-boundary')
            boundary['source_sha256'][LEGACY[0]] = 'ffd27ae7a927494083cbdcb173847502283f9ff0f69b8b7321abe0b042824dc1'
            inc.set_meta(db, 'review_boundary', boundary)
            inc.set_meta(db, 'boundary_sha256', inc.digest(boundary))
            cycle = inc.latest(db)
            cycle['report']['formal_project_total'] = 1081
            cycle['report']['review_boundary_sha256'] = boundary['sha256']
            cycle['report']['candidate_packet']['baseline_commit'] = boundary['baseline_commit']
            inc.save_cycle(db, cycle)
            saved_report = copy.deepcopy(cycle['report'])
        before = (self.root / inc.DB_NAME).read_bytes()
        before_status = inc.status(self.root)
        transport = QueueTransport()
        with self.assertRaisesRegex(ValueError, 'initialize a new state directory'):
            self.update(transport)
        with self.assertRaisesRegex(ValueError, 'initialize a new state directory'):
            inc.abandon(self.root, 'Synthetic request must not migrate old state')
        self.assertEqual(transport.calls, [])
        self.assertEqual((self.root / inc.DB_NAME).read_bytes(), before)
        self.assertEqual(inc.status(self.root), before_status)
        self.assertEqual(before_status['formal_project_total'], 1081)
        self.assertEqual(inc.report(self.root, cycle=1), saved_report)
        self.assertEqual(saved_report['formal_project_total'], 1081)
        self.assertEqual(saved_report['excluded_example_count'], 62)
        self.assertEqual((self.root / inc.DB_NAME).read_bytes(), before)

    def test_a592_predecessor_scope_stays_read_only_without_migration(self):
        self.assert_predecessor_scope_stays_read_only(
            'a592c89ede0dcced22579e56fc68b6fab4c55f49', 1103, 1079,
            'd078f1fb726289bdd6c7faff6f9a4a84d46eed5cd83ba586cd9c2f6ae0256739')

    def test_evidence_batch_predecessor_scope_stays_read_only_without_migration(self):
        # The 12cb checkout used the earlier 5396 boundary origin label.
        self.assert_predecessor_scope_stays_read_only(
            '5396fd1cc9df72507785a112a21c2990fb4a7c50', 1107, 1083,
            '193f431190af502eb5c2121ff077bf59ddc9b708ae5ad786160bdc8287c83c83')

    def assert_predecessor_scope_stays_read_only(self, origin, total, legacy_count, materials_sha256):
        from nomad_review_boundary import load_review_boundary

        current = load_review_boundary()
        self.assertEqual(current['baseline_commit'], 'e2a8bc7f7297c95b9ddd883275a1c807ff4b038d')
        self.assertEqual(current['formal_legacy_count'], 1084)
        self.assertEqual(current['formal_project_total'], 1108)
        self.init()
        self.assertEqual(self.first_cycle()['status'], 'complete')
        self.now += 100
        self.assertEqual(self.first_cycle()['status'], 'complete')
        # Explicitly synthetic predecessor store; no real archive is relabeled.
        with inc.connect(self.root) as db, db:
            predecessor = copy.deepcopy(inc.meta(db, 'review_boundary'))
            predecessor.update(baseline_commit=origin,
                               formal_project_total=total, formal_legacy_count=legacy_count)
            predecessor['source_sha256'][LEGACY[0]] = materials_sha256
            predecessor.pop('sha256')
            predecessor['sha256'] = inc.digest(predecessor)
            inc.set_meta(db, 'review_boundary', predecessor)
            inc.set_meta(db, 'boundary_sha256', inc.digest(predecessor))
            saved_reports = {}
            for row in db.execute('SELECT state FROM cycles').fetchall():
                cycle = inc.decode(row['state'])
                cycle['report']['formal_project_total'] = total
                cycle['report']['review_boundary_sha256'] = predecessor['sha256']
                cycle['report']['candidate_packet']['baseline_commit'] = predecessor['baseline_commit']
                inc.save_cycle(db, cycle)
                saved_reports[cycle['id']] = copy.deepcopy(cycle['report'])

        def snapshot():
            return {str(path.relative_to(self.root)): path.read_bytes()
                    for path in self.root.rglob('*') if path.is_file()}

        before = snapshot()
        before_status = inc.status(self.root)
        before_comparison = inc.compare(self.root, before=1, after=2)
        self.assertEqual(before_status['formal_project_total'], total)
        self.assertEqual(before_comparison['formal_project_total'], total)
        self.assertEqual(before_comparison['excluded_example_count'], 62)
        self.assertEqual(before_comparison['review_boundary_sha256'], predecessor['sha256'])
        self.assertEqual(before_comparison['review_boundary_content_sha256'], inc.digest(predecessor))
        for cycle_id, saved_report in saved_reports.items():
            self.assertEqual(inc.report(self.root, cycle=cycle_id), saved_report)
            self.assertEqual(saved_report['formal_project_total'], total)
            self.assertEqual(saved_report['excluded_example_count'], 62)
            self.assertEqual(saved_report['candidate_packet']['baseline_commit'], predecessor['baseline_commit'])
        self.assertEqual(snapshot(), before)

        transport = QueueTransport()
        with self.assertRaisesRegex(ValueError, 'initialize a new state directory'):
            self.update(transport)
        with self.assertRaisesRegex(ValueError, 'initialize a new state directory'):
            inc.abandon(self.root, 'Synthetic request must not migrate predecessor state')
        fresh = self.root / 'rejected-predecessor-store'
        with self.assertRaisesRegex(ValueError, 'initialize a new state directory'):
            inc.init_store(fresh, boundary=predecessor)
        self.assertFalse(fresh.exists())
        with self.assertRaisesRegex(ValueError, 'already initialized'):
            inc.init_store(self.root)
        self.assertEqual(transport.calls, [])
        self.assertEqual(snapshot(), before)
        self.assertEqual(inc.status(self.root), before_status)
        self.assertEqual(inc.compare(self.root, before=1, after=2), before_comparison)
        for cycle_id, saved_report in saved_reports.items():
            self.assertEqual(inc.report(self.root, cycle=cycle_id), saved_report)
        self.assertEqual(snapshot(), before)


if __name__ == '__main__':
    unittest.main()
