"""Offline tests of the fixed admission/example boundary and scalar unit guard."""
from pathlib import Path
import unittest
from unittest.mock import patch

from nomad_review_boundary import ROOT, SOURCES, LEGACY, load_review_boundary
from test_nomad_batch import fixture, run


class ReviewBoundaryTests(unittest.TestCase):
    def test_formal_and_example_counts_remain_separate(self):
        boundary = load_review_boundary()
        self.assertEqual(boundary['formal_project_total'], 1199)
        self.assertEqual(boundary['formal_legacy_count'], 1175)
        self.assertEqual(boundary['baseline_commit'], 'bdb1e081d5860c4c69fbcd4ee41e01450dc7a921')
        self.assertEqual(boundary['source_sha256'][LEGACY[0]],
                         '01e04f88e13685e5e5624abeee4dd0ffce8f6f7e32708e4b30420180c70c5000')
        self.assertEqual(boundary['formal_computed_composition_count'], 24)
        self.assertEqual(boundary['excluded_example_count'], 62)
        self.assertEqual(boundary['legacy_example_count'], 7)
        self.assertFalse(boundary['automatic_admission'])
        self.assertIn('unadmitted_example62', boundary['materials']['kKKhHtu2SdSNPod3lMwT16MAr068'])
        self.assertNotIn('formal_admitted24', boundary['materials']['kKKhHtu2SdSNPod3lMwT16MAr068'])

    def test_related_calculations_are_also_known(self):
        boundary = load_review_boundary()
        self.assertIn('qOMH2nGoASvASE3dXKUi9unjv0JQ', boundary['entries'])
        self.assertGreater(len(boundary['provider_material_ids']), 24 + 62 + 7)
        self.assertEqual(boundary, load_review_boundary())

    def test_unadmitted_example_cannot_be_new_candidate(self):
        boundary = load_review_boundary()
        row = fixture(mid='kKKhHtu2SdSNPod3lMwT16MAr068')
        self.assertEqual(run([row], boundary['provider_material_ids'])['candidates'], [])

    def test_boundary_fails_closed_on_changed_bytes(self):
        original = Path.read_bytes
        for relative in (SOURCES['unadmitted_example62'][0], LEGACY[0]):
            target = ROOT / relative

            def changed(path):
                return original(path) + b' ' if path == target else original(path)

            with self.subTest(resource=relative), patch.object(Path, 'read_bytes', changed):
                with self.assertRaisesRegex(ValueError, 'boundary bytes differ'):
                    load_review_boundary()

    def test_explicit_wrong_units_are_never_relabeled(self):
        for key, value in [('mass_density_unit', 'g/cm^3'), ('unit', 'g/cm^3'),
                           ('unit', None)]:
            with self.subTest(key=key, value=value):
                row = fixture()
                row['archive']['results']['properties']['structures']['structure_original'][key] = value
                self.assertEqual(run([row])['counts']['exclusion_reasons'],
                                 {'unsupported_density_unit': 1})

    def test_quantity_envelope_rejected_without_conversion(self):
        row = fixture()
        row['archive']['results']['properties']['structures']['structure_original']['mass_density'] = {
            'value': 8, 'unit': 'g/cm^3'}
        self.assertEqual(run([row])['counts']['exclusion_reasons'],
                         {'unsupported_density_quantity_shape': 1})

    def test_missing_property_does_not_reuse_old_scalar(self):
        row = fixture()
        del row['archive']['results']['properties']
        self.assertEqual(run([row])['candidates'], [])


if __name__ == '__main__':
    unittest.main()
