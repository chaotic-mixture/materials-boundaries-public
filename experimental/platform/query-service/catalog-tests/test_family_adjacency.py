"""Offline single-hop navigation contracts, also run against installed wheels.

Synthetic identities below exercise graph shapes only. Their invalid-domain
evidence is never a catalog contribution or a scientific assertion.
"""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from materials_boundaries.catalog import CatalogLookupError
from materials_query.app import create_app
from materials_query.catalog_snapshot import CatalogSnapshot
from materials_query import family_relationships as fr
from materials_query import local_catalog as lc


SOURCE = 'mat_ewurum2025_pbs_lignin20'
TARGET = 'mat_ewurum2025_indulin_at'
ISOLATED = 'mat_hydro_6061'
ROUTE = '/api/catalog/relationships/neighbors'


class SyntheticSnapshot:
    """Small, explicit test double; no full catalog copies for graph shapes."""

    def __init__(self, identifiers):
        self.version = 'a' * 64
        self.identities = {
            identifier: {
                'id': identifier,
                'name': 'Synthetic ' + identifier,
                'category': 'composite' if identifier == 'a' else 'polymer',
                'identity_scope': 'Synthetic graph-shape fixture only: ' + identifier,
                'evidence': [{
                    'source_id': 'synthetic_graph_source',
                    'url': 'https://example.invalid/synthetic-graph',
                    'locator': 'Synthetic fixture, not source-reviewed science',
                }],
            }
            for identifier in identifiers
        }
        self._graph = {'materials': {'identities': list(self.identities.values())}}

    def record(self, kind, identifier):
        if kind != 'identities':
            raise AssertionError('Unexpected synthetic record kind')
        return copy.deepcopy(self.identities[identifier])


def synthetic_graph(edges):
    identifiers = sorted({identifier for edge in edges for identifier in edge} | {'isolated'})
    snapshot = SyntheticSnapshot(identifiers)
    overlay = {
        'policy_version': fr.POLICY_VERSION,
        'baseline_commit': 'synthetic-not-a-production-baseline',
        'review_scope': 'Synthetic graph-shape test only; no admission or scientific review',
        'memberships': [],
        'relationships': [],
    }
    for source_id, target_id in edges:
        source = snapshot.identities[source_id]
        target = snapshot.identities[target_id]
        overlay['relationships'].append({
            'identity_id': source_id,
            'identity_sha256': fr.digest(source),
            'field': 'identity_scope',
            'quote': source['identity_scope'],
            'target_identity_id': target_id,
            'target_identity_sha256': fr.digest(target),
            'relation': 'has_constituent',
            'scope': 'Synthetic navigation only; no identity equivalence or property inheritance',
        })
    return snapshot, overlay


def build_synthetic(snapshot, overlay):
    with patch.object(fr, '_load_overlay', return_value=copy.deepcopy(overlay)):
        return fr.FamilyRelationships(snapshot)


class FamilyAdjacencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Build the real installed snapshot once and reuse it between app
        # instances. Additional full-catalog materialization is unnecessary.
        cls.snapshot = CatalogSnapshot.from_packaged()
        cls.index = fr.FamilyRelationships(cls.snapshot)
        with patch.object(lc, 'load_installed_snapshot', return_value=(cls.snapshot, None)):
            cls.client = TestClient(create_app(enable_local_catalog=True))
        cls.pin = {'version': cls.snapshot.version,
                   'relationship_version': cls.index.version}

    def post(self, **kwargs):
        return self.client.post(ROUTE, json={**self.pin, **kwargs})

    def data(self, **kwargs):
        response = self.post(**kwargs)
        self.assertEqual(response.status_code, 200, response.text)
        envelope = response.json()
        self.assertEqual(envelope['version'], self.snapshot.version)
        self.assertEqual(envelope['content_digest'], self.snapshot.content_digest)
        self.assertEqual(envelope['runtime_digest'], self.snapshot.runtime_digest)
        self.assertEqual(envelope['result']['relationship_version'], self.index.version)
        return envelope['result']['data']

    def test_incoming_preserves_original_assertion_and_evidence(self):
        outgoing = self.data(identity_id=SOURCE, direction='outgoing')['records'][0]
        incoming = self.data(identity_id=TARGET, direction='incoming')['records'][0]
        self.assertEqual(outgoing['relation_key'], incoming['relation_key'])
        self.assertRegex(outgoing['relation_key'], r'^family-relation:[0-9a-f]{64}$')
        legacy = self.index.identity(SOURCE)['relationships'][0]
        for record in (outgoing, incoming):
            self.assertEqual(record['source_identity_id'], SOURCE)
            self.assertEqual(record['target_identity_id'], TARGET)
            self.assertEqual(record['relation'], 'has_constituent')
            self.assertEqual({key: record[key] for key in legacy}, legacy)
            self.assertEqual(record['source_identity_sha256'],
                             fr.digest(self.snapshot.record('identities', SOURCE)))
            self.assertEqual(record['target_identity_sha256'],
                             fr.digest(self.snapshot.record('identities', TARGET)))
            for evidence in record['evidence']:
                self.assertEqual(evidence['catalog_record_id'], SOURCE)
                self.assertEqual(evidence['identity_sha256'], record['source_identity_sha256'])
                self.assertTrue(self.snapshot.record('sources', evidence['source_id']))
        self.assertEqual(outgoing['neighbor_identity_id'], TARGET)
        self.assertEqual(incoming['neighbor_identity_id'], SOURCE)
        self.assertEqual(outgoing['traversal_directions'], ['outgoing'])
        self.assertEqual(incoming['traversal_directions'], ['incoming'])

    def test_default_both_and_single_hop_scope_are_explicit(self):
        default = self.data(identity_id=TARGET)
        self.assertEqual(default, self.data(identity_id=TARGET, direction='both'))
        self.assertEqual(default['identity_id'], TARGET)
        self.assertEqual(default['direction'], 'both')
        self.assertEqual(default['max_hops'], 1)
        self.assertEqual(default['matching_relation_count'], 1)
        self.assertEqual(default['returned_relation_count'], 1)
        self.assertFalse(default['truncated'])
        self.assertIn('not material identities', default['count_scope'])
        self.assertIn('no inverse assertions', default['traversal_scope'])
        self.assertIn('membership propagation', default['traversal_scope'])

    def test_known_empty_is_not_unknown_identity(self):
        for direction in ('outgoing', 'incoming', 'both'):
            with self.subTest(direction=direction):
                empty = self.data(identity_id=ISOLATED, direction=direction)
                self.assertEqual(empty['records'], [])
                self.assertEqual(empty['matching_relation_count'], 0)
                self.assertEqual(empty['returned_relation_count'], 0)
                self.assertFalse(empty['truncated'])
        self.assertEqual(self.post(identity_id='unknown_material').status_code, 404)
        with self.assertRaises(CatalogLookupError):
            self.index.neighbors('unknown_material')
        self.assertEqual(self.data(identity_id=SOURCE, direction='incoming')['records'], [])
        self.assertEqual(self.data(identity_id=TARGET, direction='outgoing')['records'], [])

    def test_direction_filters_mixed_graph_without_reversing_predicates(self):
        snapshot, overlay = synthetic_graph([('a', 'b'), ('c', 'a'), ('b', 'c')])
        index = build_synthetic(snapshot, overlay)
        outgoing = index.neighbors('a', direction='outgoing')
        incoming = index.neighbors('a', direction='incoming')
        both = index.neighbors('a', direction='both')
        pair = lambda row: (row['source_identity_id'], row['target_identity_id'])
        self.assertEqual([pair(row) for row in outgoing['records']], [('a', 'b')])
        self.assertEqual([pair(row) for row in incoming['records']], [('c', 'a')])
        self.assertEqual([pair(row) for row in both['records']], [('a', 'b'), ('c', 'a')])
        self.assertTrue(all(row['relation'] == 'has_constituent' for row in both['records']))
        self.assertEqual(both['matching_relation_count'], 2)
        self.assertEqual(both['returned_relation_count'], 2)

    def test_both_deduplicates_self_edge_with_both_navigation_directions(self):
        snapshot, overlay = synthetic_graph([('a', 'a'), ('a', 'b'), ('b', 'a')])
        index = build_synthetic(snapshot, overlay)
        both = index.neighbors('a', direction='both')
        self.assertEqual(both['matching_relation_count'], 3)
        self.assertEqual(both['returned_relation_count'], 3)
        self.assertEqual(len({row['relation_key'] for row in both['records']}), 3)
        self_edge, = [row for row in both['records']
                      if row['source_identity_id'] == row['target_identity_id']]
        self.assertEqual(self_edge['neighbor_identity_id'], 'a')
        self.assertEqual(self_edge['traversal_directions'], ['outgoing', 'incoming'])
        for direction in ('outgoing', 'incoming'):
            directed = index.neighbors('a', direction=direction)
            self.assertEqual(directed['matching_relation_count'], 2)
            single, = [row for row in directed['records']
                       if row['source_identity_id'] == row['target_identity_id']]
            self.assertEqual(single['relation_key'], self_edge['relation_key'])
            self.assertEqual(single['traversal_directions'], [direction])

    def test_stable_keys_and_order_survive_overlay_order_changes(self):
        snapshot, overlay = synthetic_graph([('d', 'a'), ('a', 'c'), ('a', 'b'), ('b', 'a')])
        baseline = build_synthetic(snapshot, overlay).neighbors('a', limit=2)
        overlay['relationships'].reverse()
        reordered = build_synthetic(snapshot, overlay).neighbors('a', limit=2)
        self.assertEqual(reordered, baseline)
        self.assertEqual([(row['source_identity_id'], row['target_identity_id'])
                          for row in baseline['records']], [('a', 'b'), ('a', 'c')])
        self.assertEqual(baseline['matching_relation_count'], 4)
        self.assertEqual(baseline['returned_relation_count'], 2)
        self.assertTrue(baseline['truncated'])

    def test_single_hop_does_not_expand_chain_or_cycle(self):
        snapshot, overlay = synthetic_graph([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')])
        index = build_synthetic(snapshot, overlay)
        before = {identifier: index.identity(identifier) for identifier in snapshot.identities}
        result = index.neighbors('a', direction='both')
        self.assertEqual({row['neighbor_identity_id'] for row in result['records']}, {'b', 'd'})
        self.assertEqual(result['matching_relation_count'], 2)
        self.assertNotIn('c', {row['neighbor_identity_id'] for row in result['records']})
        self.assertEqual({identifier: index.identity(identifier) for identifier in snapshot.identities}, before)
        self.assertEqual(index.status()['identity_relationship_count'], 4)

    def test_default_and_maximum_limits_bound_output_not_matching_count(self):
        snapshot, overlay = synthetic_graph([('a', 'node_' + str(i).zfill(3)) for i in range(103)])
        index = build_synthetic(snapshot, overlay)
        for supplied, expected in (({}, 20), ({'limit': 1}, 1), ({'limit': 100}, 100)):
            with self.subTest(supplied=supplied):
                result = index.neighbors('a', **supplied)
                self.assertEqual(result['matching_relation_count'], 103)
                self.assertEqual(result['returned_relation_count'], expected)
                self.assertEqual(len(result['records']), expected)
                self.assertEqual(len({row['relation_key'] for row in result['records']}), expected)
                self.assertTrue(result['truncated'])

    def test_direct_query_rejects_invalid_values(self):
        for identity in (None, True, 1, [], {}, '', 'x' * 513):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                self.index.neighbors(identity)
        for direction in (None, True, [], {}, '', 'reverse', 'OUTGOING'):
            with self.subTest(direction=direction), self.assertRaises(ValueError):
                self.index.neighbors(SOURCE, direction=direction)
        for limit in (None, True, False, 0, -1, 101, 1.0, '1'):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.index.neighbors(SOURCE, limit=limit)

    def test_http_request_is_closed_and_strictly_bounded(self):
        invalid = [
            {'identity_id': ''}, {'identity_id': 'x' * 513}, {'identity_id': 1},
            {'direction': 'reverse'}, {'direction': 'OUTGOING'}, {'direction': None},
            {'limit': True}, {'limit': 0}, {'limit': -1}, {'limit': 101},
            {'limit': 1.0}, {'limit': '1'}, {'limit': None},
            {'max_hops': 2}, {'path': '/private/unused'}, {'relation': 'is_constituent_of'},
        ]
        for payload in invalid:
            with self.subTest(payload=payload):
                self.assertEqual(self.post(**{'identity_id': SOURCE, **payload}).status_code, 422)
        self.assertEqual(self.client.post(ROUTE, json=self.pin).status_code, 422)
        self.assertEqual(self.post(identity_id=SOURCE, limit=100).status_code, 200)

    def test_both_version_pins_are_required_and_stale_pins_conflict(self):
        for key in self.pin:
            with self.subTest(key=key):
                value = {**self.pin, 'identity_id': SOURCE}
                del value[key]
                self.assertEqual(self.client.post(ROUTE, json=value).status_code, 422)
                value[key] = '0' * 64
                self.assertEqual(self.client.post(ROUTE, json=value).status_code, 409)
                value[key] = 'bad-pin'
                self.assertEqual(self.client.post(ROUTE, json=value).status_code, 422)

    def test_key_is_assertion_identity_not_evidence_revision(self):
        snapshot, overlay = synthetic_graph([('a', 'b'), ('b', 'a')])
        original = build_synthetic(snapshot, overlay)
        baseline = original.neighbors('a', direction='outgoing')['records'][0]
        overlay['relationships'][0]['field'] = 'name'
        overlay['relationships'][0]['quote'] = snapshot.identities['a']['name']
        overlay['relationships'][0]['scope'] += '; revised evidence context'
        revised = build_synthetic(snapshot, overlay)
        changed = revised.neighbors('a', direction='outgoing')['records'][0]
        self.assertEqual(baseline['relation_key'], changed['relation_key'])
        self.assertNotEqual(baseline['evidence'], changed['evidence'])
        self.assertNotEqual(baseline['scope'], changed['scope'])
        self.assertNotEqual(original.version, revised.version)
        self.assertEqual(original.catalog_version, revised.catalog_version)
        reverse_assertion = revised.neighbors('a', direction='incoming')['records'][0]
        self.assertNotEqual(changed['relation_key'], reverse_assertion['relation_key'])

    def test_source_target_and_quote_drift_reject_index_construction(self):
        snapshot, overlay = synthetic_graph([('a', 'b')])
        for field, value in (
                ('identity_sha256', '0' * 64),
                ('target_identity_sha256', '0' * 64),
                ('quote', 'Not present in the captured identity'),
                ('field', 'category'),
                ('relation', 'is_constituent_of')):
            changed = copy.deepcopy(overlay)
            changed['relationships'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_synthetic(snapshot, changed)

    def test_duplicate_assertions_remain_an_error_not_silent_review_merging(self):
        snapshot, overlay = synthetic_graph([('a', 'b')])
        duplicate = copy.deepcopy(overlay['relationships'][0])
        duplicate['scope'] += '; different scope must not bypass assertion uniqueness'
        overlay['relationships'].append(duplicate)
        with self.assertRaises(ValueError):
            build_synthetic(snapshot, overlay)

    def test_missing_source_evidence_rejects_index_construction(self):
        snapshot, overlay = synthetic_graph([('a', 'b')])
        snapshot.identities['a']['evidence'] = []
        overlay['relationships'][0]['identity_sha256'] = fr.digest(snapshot.identities['a'])
        with self.assertRaises(ValueError):
            build_synthetic(snapshot, overlay)

    def test_overlay_drift_disables_neighbors_but_preserves_catalog_api(self):
        overlay = json.loads(fr.OVERLAY.read_text(encoding='utf-8'))
        overlay['relationships'][0]['target_identity_sha256'] = '0' * 64
        with patch.object(lc, 'load_installed_snapshot', return_value=(self.snapshot, None)), \
                patch.object(fr, '_load_overlay', return_value=overlay):
            client = TestClient(create_app(enable_local_catalog=True))
        self.assertEqual(client.get('/api/catalog/relationships/status').json(),
                         {'enabled': False, 'reason': 'relationship_initialization_failed'})
        response = client.post(ROUTE, json={**self.pin, 'identity_id': TARGET})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(str(fr.OVERLAY.parent), response.text)
        legacy = client.post('/api/catalog/record', json={
            'version': self.snapshot.version, 'kind': 'identities', 'record_id': TARGET})
        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(legacy.json()['result'], self.snapshot.record('identities', TARGET))

    def test_revised_overlay_requires_new_relationship_pin(self):
        overlay = json.loads(fr.OVERLAY.read_text(encoding='utf-8'))
        overlay['review_scope'] += '; synthetic revision for pin validation only'
        with patch.object(lc, 'load_installed_snapshot', return_value=(self.snapshot, None)), \
                patch.object(fr, '_load_overlay', return_value=overlay):
            client = TestClient(create_app(enable_local_catalog=True))
        status = client.get('/api/catalog/relationships/status').json()
        self.assertEqual(status['catalog_version'], self.snapshot.version)
        self.assertNotEqual(status['relationship_version'], self.index.version)
        self.assertEqual(client.post(ROUTE, json={**self.pin, 'identity_id': TARGET}).status_code, 409)
        accepted = client.post(ROUTE, json={**self.pin, 'identity_id': TARGET,
                                          'relationship_version': status['relationship_version']})
        self.assertEqual(accepted.status_code, 200)

    def test_captured_query_has_no_disk_reads_or_overlay_refresh(self):
        baseline = self.index.neighbors(TARGET)
        with patch.object(fr, '_load_overlay', side_effect=AssertionError('Unexpected refresh')), \
                patch.object(Path, 'read_bytes', side_effect=AssertionError('Unexpected disk read')), \
                patch.object(Path, 'read_text', side_effect=AssertionError('Unexpected disk read')):
            self.assertEqual(self.index.neighbors(TARGET), baseline)
            self.assertEqual(self.index.neighbors(SOURCE)['matching_relation_count'], 1)
        with patch.object(fr, '_IMPLEMENTATION_SHA256', '0' * 64), self.assertRaises(ValueError):
            fr.FamilyRelationships(self.snapshot)

    def test_nested_results_are_defensive_copies(self):
        baseline = self.index.neighbors(TARGET)
        changed = self.index.neighbors(TARGET)
        changed['records'][0]['evidence'][0]['locator'] = 'Changed by a caller'
        changed['records'][0]['traversal_directions'].clear()
        changed['records'][0]['scope'] = 'Changed by a caller'
        changed['records'][0]['relation_key'] = 'caller-forged-key'
        changed['records'].append({'caller': 'record'})
        changed['matching_relation_count'] = 999
        self.assertEqual(self.index.neighbors(TARGET), baseline)
        self.assertEqual(self.data(identity_id=TARGET), baseline)

    def test_queries_do_not_change_legacy_assertions_memberships_or_counts(self):
        before_status = self.index.status()
        before_rows = {identity: self.index.identity(identity) for identity in (SOURCE, TARGET, ISOLATED)}
        for identity in before_rows:
            for direction in ('outgoing', 'incoming', 'both'):
                self.index.neighbors(identity, direction=direction)
                self.data(identity_id=identity, direction=direction)
        self.assertEqual(self.index.status(), before_status)
        self.assertEqual(before_status['unique_identity_count'], 1148)
        self.assertEqual(before_status['identity_relationship_count'], 1)
        self.assertEqual(before_status['membership_assertion_count'], 1153)
        self.assertEqual(before_status['new_identities_admitted'], 0)
        self.assertFalse(before_status['provider_counts_combined'])
        for identity, before in before_rows.items():
            self.assertEqual(self.index.identity(identity), before)
            response = self.client.post('/api/catalog/relationships/identity',
                                        json={**self.pin, 'identity_id': identity})
            self.assertEqual(response.json()['result']['data'], before)
        self.assertEqual(before_rows[TARGET]['relationships'], [])
        self.assertEqual({item['concept'] for item in before_rows[TARGET]['memberships']
                          if item['status'] == 'supported'}, {'polymer'})
        self.assertFalse(any(key in record for record in self.index.neighbors(TARGET)['records']
                             for key in ('properties', 'memberships', 'property_ids')))

    def test_transport_boundaries_apply_to_neighbors(self):
        self.assertEqual(self.client.post(ROUTE, content=b'x' * 32769).status_code, 413)
        self.assertEqual(self.client.post(ROUTE, json={},
                         headers={'Origin': 'https://evil.example'}).status_code, 403)
        self.assertEqual(self.client.put(ROUTE, json={}).status_code, 405)

    def test_default_disabled_does_not_load_core(self):
        with patch.object(lc, 'load_installed_snapshot', side_effect=AssertionError('Unexpected core load')):
            client = TestClient(create_app())
        self.assertEqual(client.post(ROUTE, json={**self.pin, 'identity_id': SOURCE}).status_code, 503)

    def test_existing_concurrency_guard_bounds_neighbor_operations(self):
        class BusySlots:
            def __init__(self):
                self.attempts = 0

            def acquire(self, blocking):
                self.assert_nonblocking = blocking is False
                self.attempts += 1
                return False

            def release(self):
                raise AssertionError('An unacquired slot must not be released')

        slots = BusySlots()
        with patch.object(lc, 'load_installed_snapshot', return_value=(self.snapshot, None)), \
                patch.object(lc, 'BoundedSemaphore', return_value=slots):
            client = TestClient(create_app(enable_local_catalog=True))
        response = client.post(ROUTE, json={**self.pin, 'identity_id': SOURCE})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(slots.attempts, 1)
        self.assertTrue(slots.assert_nonblocking)


if __name__ == '__main__':
    unittest.main()
