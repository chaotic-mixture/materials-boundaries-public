"""Every v0.22 scientific record/test remains bound to its accepted payload.

The two old test deltas support the reviewed source-cell ordering fix.
A separate current-only maintenance tail binds the test-helper lineage repair.
These are catalog/test metadata hashes, never publisher source-artifact hashes.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from viscoelastic_preservation import pre_viscoelastic_bytes
import unittest

from provenance_corrections import reviewed_current_test_hash, reviewed_paht_test_hash

from source_evidence_preservation import previous_record
from materials_boundaries.catalog import read_catalog
from materials_boundaries.observation_visualization import POLICY as INSPECTION_POLICY
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES

ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((ROOT / 'tests/fixtures/pre_temperature_plot_v0230.json').read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class TemperaturePlotPreservationTests(unittest.TestCase):
    def test_every_prior_scientific_record_is_identical(self):
        for kind, expected in BASELINE['record_sha256'].items():
            current = {record['id']: record for record in read_catalog(kind)['records']}
            for identifier, value in expected.items():
                with self.subTest(kind=kind, identifier=identifier):
                    record = previous_record(kind, current[identifier])
                    if kind == 'claims':
                        evidence = {digest(item): item for item in record['evidence']}
                        record['evidence'] = [evidence[h] for h in BASELINE['claim_evidence_sha256'][identifier]]
                    self.assertEqual(digest(record), value)

    def test_prior_protocols_and_groups_are_identical(self):
        for kind, fields in BASELINE['metadata_sha256'].items():
            current = read_catalog(kind)
            for field, expected in fields.items():
                items = {record['id']: record for record in current[field]}
                for identifier, value in expected.items():
                    with self.subTest(kind=kind, field=field, identifier=identifier):
                        self.assertEqual(digest(items[identifier]), value)

    def test_historical_tests_and_fixtures_have_only_reviewed_ordering_deltas(self):
        updates = BASELINE['approved_test_updates']
        self.assertEqual(set(updates), {'tests/test_pa12_cf15_observations.py',
                                        'tests/test_pa12_cf15_inspection.py'})
        for filename, previous in BASELINE['historical_test_sha256'].items():
            expected = previous
            if filename in updates:
                change = updates[filename]
                self.assertEqual(change['previous_sha256'], previous)
                self.assertTrue(change['reason'].strip())
                expected = change['sha256']
            expected = reviewed_current_test_hash(filename, expected)
            expected = reviewed_paht_test_hash(filename, expected)
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256(pre_viscoelastic_bytes(filename, (ROOT / filename).read_bytes())).hexdigest(), expected)

    def test_eight_rules_and_inspection_policy_are_not_relaxed(self):
        self.assertEqual(len(BASE_RULES) + len(DERIVED_RULES), 8)
        self.assertEqual(INSPECTION_POLICY['purpose'], 'inspection_only')
        for key in ('quantitative_axes_allowed', 'uncertainty_endpoints_calculated',
                    'overlay_allowed', 'aggregation_allowed', 'ranking_allowed',
                    'thickness_conversion_allowed', 'formula_execution_allowed'):
            self.assertIs(INSPECTION_POLICY[key], False)


if __name__ == '__main__':
    unittest.main()
