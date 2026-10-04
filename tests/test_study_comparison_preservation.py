"""New presentation preserves every accepted scientific/old-test/example byte."""
import hashlib
import json
from pathlib import Path
from source_evidence_preservation import previous_catalog
from viscoelastic_preservation import pre_viscoelastic_bytes, historical_claims_envelope
import unittest

from materials_boundaries import observation_visualization as inspection
from materials_boundaries import observation_temperature_plot as single
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES

ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((ROOT / 'tests/fixtures/pre_study_comparison_v0250.json').read_text())


class StudyComparisonPreservationTests(unittest.TestCase):
    def test_all_old_payloads_except_explicit_release_integration_paths_are_identical(self):
        allowed = {'CITATION.cff', 'CONTRIBUTING.md', 'README.md', 'docs/OBSERVATION_INSPECTION.md',
                   'materials_boundaries/_version.py', 'materials_boundaries/cli.py',
                   'scripts/check_wheel_metadata.py', 'scripts/validate_catalogs.py'}
        self.assertEqual(set(BASELINE['allowed_existing_changes']), allowed)
        self.assertEqual(BASELINE['baseline_file_count'], 269)
        self.assertEqual(BASELINE['baseline_tree'], 'c772ff37c1b15671165a9c4d3ea5ad6b1c7c4427')
        for filename, expected in BASELINE['baseline_sha256'].items():
            if filename in allowed or filename.startswith('materials_boundaries/data/'):
                continue
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256(pre_viscoelastic_bytes(filename, (ROOT / filename).read_bytes())).hexdigest(), expected)

    def test_all_existing_catalog_objects_are_unchanged_under_supported_appendability(self):
        def digest(value):
            return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        for filename, fields in BASELINE['catalog_preservation'].items():
            current = previous_catalog(Path(filename).stem,
                json.loads((ROOT / filename).read_text()))
            if filename == 'materials_boundaries/data/claims.json':
                current = historical_claims_envelope(current)
            for key, baseline in fields.items():
                with self.subTest(filename=filename, field=key):
                    if 'record_digests' in baseline:
                        indexed = {r['id']: r for r in current[key]}
                        for identifier, expected in baseline['record_digests'].items():
                            record = indexed[identifier]
                            if filename == 'materials_boundaries/data/claims.json':
                                evidence = {digest(e): e for e in record['evidence']}
                                record = dict(record, evidence=[evidence[h] for h in
                                    BASELINE['claim_evidence_digests'][identifier]])
                            self.assertEqual(digest(record), expected)
                    elif 'locale_label_digests' in baseline:
                        for lang, labels in baseline['locale_label_digests'].items():
                            for label, expected in labels.items():
                                self.assertEqual(digest(current[key][lang][label]), expected)
                    else:
                        self.assertEqual(digest(current[key]), baseline['sha256'])

    def test_no_scientific_rules_or_old_presentation_policies_expand(self):
        self.assertEqual(len(BASE_RULES) + len(DERIVED_RULES), 8)
        for key in ('quantitative_axes_allowed', 'uncertainty_endpoints_calculated', 'overlay_allowed',
                    'aggregation_allowed', 'ranking_allowed', 'thickness_conversion_allowed'):
            self.assertIs(inspection.POLICY[key], False)
        self.assertEqual(single.PROFILE_ID, 'ciganas-pa12-cf15-table3-uts-temperature-v1')
        self.assertEqual(single.POLICY['axes']['x']['domain'], [15, 125])
        self.assertEqual(single.POLICY['axes']['y']['domain'], [0, 55])
        self.assertTrue(single.POLICY['whiskers_required'])
        with self.assertRaises(single.ObservationTemperaturePlotError):
            single.build_observation_temperature_plot(dataset_id='zach-2025-paht-cf-annealed-fff-uts-temperature')


if __name__ == '__main__':
    unittest.main()
