"""Second-tranche examples never grant admission to the pinned formal release."""
import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient
from materials_project_catalog.catalog import formal_project_catalog
from materials_query.app import create_app
from materials_query.computed_registry import ComputedRegistry


class CombinedAdmissionBoundary(unittest.TestCase):
    def test_second_tranche_admission_does_not_change_formal_counts_or_pins(self):
        example = Path(__file__).resolve().parents[2] / 'examples/reviewed-computed-v2-second'
        review = json.loads((example / 'normalized-review.json').read_bytes())
        pin = json.loads((example / 'acceptance-pin.json').read_bytes())
        input_bytes = (example / 'eligible-metadata-input.json').read_bytes()
        expected = formal_project_catalog()
        second_buckets = {row['conservative_count_bucket'] for row in review['records']}
        self.assertEqual(len(second_buckets), 62)
        with tempfile.TemporaryDirectory() as temporary:
            registry = ComputedRegistry(Path(temporary) / 'second.db', review,
                trusted_review_sha256=pin['canonical_review_sha256'], input_file_bytes=input_bytes)
            before = TestClient(create_app(enable_local_catalog=True, computed_registry=registry))
            self.assertEqual(before.get('/api/computed/status').json()['selected_entry_count'], 0)
            formal_before = before.get('/api/catalog/project/status').json()
            self.assertTrue(formal_before['enabled'])
            admitted = registry.admit([row['candidate_id'] for row in review['records']])
            self.assertEqual(admitted['scoped_accepted_identity_bucket_count'], 62)
            self.assertEqual(before.get('/api/computed/status').json()['selected_entry_count'], 0)
            restarted = TestClient(create_app(enable_local_catalog=True, computed_registry=registry))
            computed = restarted.get('/api/computed/status').json()
            self.assertEqual(computed['selected_entry_count'], 62)
            for client in (before, restarted):
                with self.subTest(process='original' if client is before else 'restarted'):
                    status = client.get('/api/catalog/project/status').json()
                    self.assertEqual(status, formal_before)
                    self.assertEqual(status['counts']['formal_project_admission_count'], 1081)
                    self.assertEqual(status['counts']['reviewed_computed_composition_count'], 24)
                    self.assertEqual(status['counts']['legacy_source_qualified_identity_count'], 1057)
                    self.assertEqual(status['version'], expected['version'])
                    self.assertEqual(status['resource_sha256'], expected['resource_sha256'])
                    self.assertEqual(status['review_sha256'], expected['review_sha256'])
                    self.assertEqual(client.get('/api/catalog/status').json()['counts']['local_catalog_unique_material_count'], 1057)
                    response = client.post('/api/catalog/project/list', json={
                        'version': status['version'], 'partition': 'reviewed-computed', 'limit': 100})
                    self.assertEqual(response.status_code, 200)
                    rows = response.json()['records']
                    self.assertEqual(response.json()['matched_count'], 24)
                    self.assertEqual(rows, [row for row in expected['records'] if row['partition'] == 'reviewed-computed'])
                    self.assertTrue(second_buckets.isdisjoint(row['id'] for row in rows))
            self.assertEqual(formal_project_catalog(), expected)
            default = TestClient(create_app())
            self.assertFalse(default.get('/api/computed/status').json()['enabled'])
            self.assertFalse(default.get('/api/catalog/project/status').json()['enabled'])


if __name__ == '__main__':
    unittest.main()
