"""Offline contract tests for the bounded, overlapping catalog view."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query import local_catalog as lc
try:
    from materials_query.catalog_snapshot import CatalogSnapshot
except ModuleNotFoundError as error:
    if error.name != 'materials_boundaries':
        raise
    raise unittest.SkipTest('Optional repository core is not installed') from error
from materials_query import family_relationships as fr


class FamilyRelationshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = CatalogSnapshot.from_packaged()
        cls.index = fr.FamilyRelationships(cls.snapshot)
        cls.client = TestClient(create_app(enable_local_catalog=True))
        cls.status = cls.client.get('/api/catalog/relationships/status').json()
        cls.pin = {'version': cls.status['catalog_version'],
                   'relationship_version': cls.status['relationship_version']}

    def post(self, route, **kwargs):
        return self.client.post('/api/catalog/relationships/' + route, json={**self.pin, **kwargs})

    def row(self, identity_id):
        response = self.post('identity', identity_id=identity_id)
        self.assertEqual(response.status_code, 200)
        return response.json()['result']['data']

    @staticmethod
    def supported(row):
        return {m['concept'] for m in row['memberships'] if m['status'] == 'supported'}

    def test_coverage_exact_and_no_count_inflation(self):
        self.assertEqual(self.status['unique_identity_count'], 1057)
        self.assertEqual(self.status['membership_assertion_count'], 1062)
        self.assertEqual(self.status['identity_relationship_count'], 1)
        expected = dict(metal=14, alloy=2, inorganic=16, ceramic=2, polymer=15,
                        composite=3, natural=1010, semiconductor=0, battery=0,
                        catalyst=0, two_dimensional=0, nanoscale=0)
        for concept, supported in expected.items():
            with self.subTest(concept=concept):
                self.assertEqual(self.status['coverage'][concept]['supported'], supported)
                self.assertEqual(self.status['coverage'][concept]['unknown'], 1057 - supported)
        self.assertEqual(self.status['new_identities_admitted'], 0)
        self.assertFalse(self.status['provider_counts_combined'])

    def test_metal_alloy_overlap(self):
        self.assertEqual(self.supported(self.row('mat_hydro_6061')), {'metal', 'alloy'})
        response = self.post('search', concepts=['metal', 'alloy', 'alloy'], limit=100)
        result = response.json()['result']['data']
        self.assertEqual(result['matching_unique_identity_count'], 14)
        self.assertEqual(len({r['identity_id'] for r in result['records']}), 14)
        self.assertEqual(result['concepts'], ['alloy', 'metal'])
        self.assertFalse(result['truncated'])

    def test_cross_category_polymer_composite_overlap(self):
        row = self.row('mat_ewurum2025_pbs_lignin20')
        self.assertEqual(row['legacy_category'], 'composite')
        self.assertEqual(self.supported(row), {'polymer', 'composite'})
        result = self.post('search', concepts=['polymer', 'composite'], match='all').json()['result']['data']
        self.assertEqual(result['matching_unique_identity_count'], 1)
        self.assertEqual(result['records'][0]['identity_id'], row['identity_id'])

    def test_ceramic_is_not_synonym_for_inorganic(self):
        self.assertEqual(self.supported(self.row('mat_ozog2020_aln90_y6_a4_pressed')), {'inorganic', 'ceramic'})
        self.assertEqual(self.supported(self.row('mat_schott_borofloat_33')), {'inorganic'})

    def test_no_formula_or_supplier_semiconductor_inference(self):
        # Silicon identity mentions Fairchild Semiconductor Company, not a
        # reviewed semiconductor-membership assertion under this policy.
        row = self.row('mat_silicon_crystalline_nbs')
        self.assertEqual(self.supported(row), {'inorganic'})
        for membership in row['memberships']:
            if membership['concept'] in ('semiconductor', 'battery', 'catalyst', 'two_dimensional', 'nanoscale'):
                self.assertEqual(membership['status'], 'unknown')
                self.assertEqual(membership['evidence'], [])
                self.assertIn('not evidence of absence', membership['reason'])

    def test_no_role_inference_from_graphite(self):
        row = self.row('mat_poco_axf_5q')
        self.assertEqual(self.supported(row), {'inorganic'})
        result = self.post('search', concepts=['battery', 'catalyst', 'two_dimensional', 'nanoscale']).json()['result']['data']
        self.assertEqual(result['matching_unique_identity_count'], 0)

    def test_provenance_resolves_and_quotes_match_for_every_assertion(self):
        for identity_id in self.index._rows:
            row = self.index.identity(identity_id)
            identity = self.snapshot.record('identities', identity_id)
            for edge in row['memberships'] + row['relationships']:
                if edge['status'] != 'supported':
                    continue
                self.assertTrue(edge['evidence'])
                for evidence in edge['evidence']:
                    self.assertEqual(evidence['identity_sha256'], fr.digest(identity))
                    self.assertIn(evidence['catalog_quote'], identity[evidence['catalog_field']])
                    source = self.snapshot.record('sources', evidence['source_id'])
                    self.assertEqual(source['id'], evidence['source_id'])
                    self.assertTrue(any(e['source_id'] == evidence['source_id']
                        and e['locator'] == evidence['locator'] and e['url'] == evidence['url']
                        for e in identity['evidence']))

    def test_constituent_is_not_identity_or_property_equivalence(self):
        row = self.row('mat_ewurum2025_pbs_lignin20')
        edge = row['relationships'][0]
        self.assertEqual(edge['relation'], 'has_constituent')
        self.assertEqual(edge['target_identity_id'], 'mat_ewurum2025_indulin_at')
        self.assertIn('does not imply identity equivalence', edge['scope'])
        self.assertEqual(self.supported(self.row(edge['target_identity_id'])), {'polymer'})
        self.assertEqual(self.row(edge['target_identity_id'])['relationships'], [])

    def test_truncation_is_explicit(self):
        result = self.post('search', concepts=['natural'], limit=1).json()['result']['data']
        self.assertEqual(result['matching_unique_identity_count'], 1010)
        self.assertEqual(result['returned_unique_identity_count'], 1)
        self.assertTrue(result['truncated'])

    def test_detached_results(self):
        baseline = self.index.identity('mat_hydro_6061')
        changed = self.index.identity('mat_hydro_6061')
        changed['memberships'][0]['evidence'].clear()
        self.assertEqual(self.index.identity('mat_hydro_6061'), baseline)
        status = self.index.status()
        status['coverage'].clear()
        self.assertTrue(self.index.status()['coverage'])

    def test_both_pins_required_and_stale_rejected(self):
        url = '/api/catalog/relationships/identity'
        for key in self.pin:
            value = {**self.pin, 'identity_id': 'mat_hydro_6061'}
            del value[key]
            self.assertEqual(self.client.post(url, json=value).status_code, 422)
            value[key] = '0' * 64
            self.assertEqual(self.client.post(url, json=value).status_code, 409)

    def test_inputs_and_unknown_identity(self):
        self.assertEqual(self.post('identity', identity_id='missing').status_code, 404)
        for payload in ({'concepts': []}, {'concepts': ['fake']}, {'concepts': ['metal'] * 13},
                        {'concepts': ['metal'], 'limit': True}, {'concepts': ['metal'], 'limit': 101},
                        {'concepts': ['metal'], 'match': 'none'}, {'concepts': ['metal'], 'path': '/tmp/x'}):
            self.assertEqual(self.post('search', **payload).status_code, 422)

    def test_transport_boundaries_inherited(self):
        url = '/api/catalog/relationships/search'
        self.assertEqual(self.client.post(url, content=b'x' * 32769).status_code, 413)
        self.assertEqual(self.client.post(url, json={}, headers={'Origin': 'https://evil.example'}).status_code, 403)
        self.assertEqual(self.client.put(url, json={}).status_code, 405)

    def test_default_disabled(self):
        with patch.object(lc, 'load_installed_snapshot', side_effect=AssertionError('No core load')):
            client = TestClient(create_app())
            self.assertEqual(client.get('/api/catalog/relationships/status').json(), {'enabled': False, 'reason': 'not_enabled'})
            self.assertEqual(client.post('/api/catalog/relationships/search', json={**self.pin, 'concepts': ['metal']}).status_code, 503)

    def test_overlay_drift_fails_closed_without_breaking_legacy(self):
        with patch.object(fr, 'FamilyRelationships', side_effect=ValueError('/private/details')):
            client = TestClient(create_app(enable_local_catalog=True))
            status = client.get('/api/catalog/relationships/status').json()
            self.assertEqual(status, {'enabled': False, 'reason': 'relationship_initialization_failed'})
            self.assertTrue(client.get('/api/catalog/status').json()['enabled'])
            self.assertEqual(client.post('/api/catalog/record', json={'version': self.pin['version'], 'kind': 'identities', 'record_id': 'mat_hydro_6061'}).status_code, 200)
            response = client.post('/api/catalog/relationships/search', json={**self.pin, 'concepts': ['metal']})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('/private', response.text)

    def test_review_pins_reject_changed_evidence(self):
        overlay = json.loads(fr.OVERLAY.read_text())
        for mutate in ('hash', 'quote', 'target', 'duplicate', 'duplicate_edge'):
            value = copy.deepcopy(overlay)
            if mutate == 'hash': value['memberships'][0]['identity_sha256'] = '0' * 64
            elif mutate == 'quote': value['memberships'][0]['quote'] = 'Unsupported claim'
            elif mutate == 'target': value['relationships'][0]['target_identity_sha256'] = '0' * 64
            elif mutate == 'duplicate': value['memberships'].append(value['memberships'][0])
            else:
                edge = copy.deepcopy(value['relationships'][0])
                edge['scope'] += ' changed text'
                value['relationships'].append(edge)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'overlay.json'
                path.write_text(json.dumps(value))
                with patch.object(fr, 'OVERLAY', path), self.assertRaises(ValueError):
                    fr.FamilyRelationships(self.snapshot)

    def test_version_binds_policy_and_is_repeatable(self):
        self.assertEqual(fr.FamilyRelationships(self.snapshot).version, self.index.version)
        overlay = json.loads(fr.OVERLAY.read_text())
        overlay['review_scope'] += ' revised'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'overlay.json'
            path.write_text(json.dumps(overlay))
            with patch.object(fr, 'OVERLAY', path):
                self.assertNotEqual(fr.FamilyRelationships(self.snapshot).version, self.index.version)

    def test_implementation_drift_fails_closed(self):
        with patch.object(fr, '_IMPLEMENTATION_SHA256', '0' * 64), self.assertRaises(ValueError):
            fr.FamilyRelationships(self.snapshot)

    def test_overlay_duplicate_keys_and_unknown_fields_rejected(self):
        original = fr.OVERLAY.read_text()
        for raw in (original.replace('"policy_version":', '"unexpected": 1, "policy_version":', 1),
                    original.replace('"policy_version":', '"policy_version": "duplicate", "policy_version":', 1)):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'overlay.json'
                path.write_text(raw)
                with patch.object(fr, 'OVERLAY', path), self.assertRaises(ValueError):
                    fr.FamilyRelationships(self.snapshot)

    def test_legacy_categories_remain_exclusive_and_unchanged(self):
        from collections import Counter
        from materials_boundaries.catalog import read_catalog
        original = read_catalog('materials')
        self.assertEqual(Counter(i['category'] for i in original['identities']),
                         dict(natural=1010, metal=14, inorganic=16, polymer=14, composite=3))
        for identity in original['identities']:
            self.assertEqual(self.snapshot.record('identities', identity['id']), identity)
            self.assertEqual(self.index.identity(identity['id'])['legacy_category'], identity['category'])


if __name__ == '__main__':
    unittest.main()
