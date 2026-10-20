"""Exact integrated baseline and temporary old-registry compatibility checks."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path, PureWindowsPath
import json
import tempfile
import unittest
from unittest.mock import Mock, patch

from materials_query import computed_registry as registry


OLD_BASELINE = '6ab6a7bcda3f98c33c9c5520b420fdbcc884cd18a10a3235f07ce58e28c5e1a9'
PREVIOUS_BASELINE = 'c03c48c4b0b2196ba77ea439df01d5a5e8191925bbfafaa63ab1212aa2d0335f'
EAF_BASELINE = '8da7a2000110021ad0a20b2a83dc1b02420a0bf9e3d1b68eb71b70f127965efe'
NC2_BASELINE = 'a38937d66a5d6c8f99eae6c05747e60a90f7647a737a1dc4d1cebc983fafcca3'
INTEGRATED_BASELINE = 'f1a1e3e379f9b7befba595b54477f15a26364548798b28dd65be8bc4326c0df4'
PRE_EVIDENCE_BATCH_BASELINE = '3782f403f120f22b5287e01f4e207419e2f576a28dfda33a89a85580b936c0f6'
PRE_GROWTH_BATCH_BASELINE = '8fda4f7a4355c88f0e4e9e713c01f236a907985b4720454e338d8d95eff4770e'
PRE_PUR_BATCH_BASELINE = '0d2f515260b78841249f5b48331f8a80fc9164bd58bb57c592f7adfed3d96277'
PRE_TABLE_BATCH_BASELINE = '73b8b455042290c0f752e784f23687eaf3bbc8dc7631ced311af7af216f08d6e'
PRE_RCA_BATCH_BASELINE = '9090f061483cefde2d6255f057078b7700d3e22c85db7191ec00bc30de78f2ad'
PRE_BINARY_BATCH_BASELINE = '148c38cfa1819b8103ffa6c0f856d824b9fc54a3e9f8a5eecc50943fd19b27bd'
PRE_MTIBE_BATCH_BASELINE = '15c0619c3a55984550ecd564692c4588f777a10d60a4e9a01b91079c12978c2f'
NEW_BASELINE = 'c127bf69ccca825e1b2ca3fd496f6ead65bf68478fc232d27f087b7e551b6909'


class IntegratedBaselineTests(unittest.TestCase):
    def test_installed_package_matches_exact_new_anchor(self):
        self.assertEqual(registry.baseline_digest(), NEW_BASELINE)
        self.assertNotEqual(NEW_BASELINE, OLD_BASELINE)
        self.assertNotEqual(NEW_BASELINE, PREVIOUS_BASELINE)
        self.assertNotEqual(NEW_BASELINE, EAF_BASELINE)
        self.assertNotEqual(NEW_BASELINE, NC2_BASELINE)
        self.assertNotEqual(NEW_BASELINE, INTEGRATED_BASELINE)
        self.assertNotEqual(NEW_BASELINE, PRE_EVIDENCE_BATCH_BASELINE)
        self.assertNotEqual(NEW_BASELINE, PRE_GROWTH_BATCH_BASELINE)
        self.assertNotEqual(NEW_BASELINE, PRE_PUR_BATCH_BASELINE)
        self.assertNotEqual(NEW_BASELINE, PRE_TABLE_BATCH_BASELINE)
        self.assertNotEqual(NEW_BASELINE, PRE_RCA_BATCH_BASELINE)
        self.assertNotEqual(NEW_BASELINE, PRE_BINARY_BATCH_BASELINE)
        self.assertNotEqual(NEW_BASELINE, PRE_MTIBE_BATCH_BASELINE)

    def test_windows_paths_use_the_same_manifest_key(self):
        payload = b'synthetic catalog bytes'
        manifest = {'data/materials.json': sha256(payload).hexdigest()}
        pin_bytes = registry.canonical(manifest) + b'\n'
        pin_root, core_root, traversable, item = Mock(), Mock(), Mock(), Mock()
        pin_root.joinpath.return_value.read_bytes.return_value = pin_bytes
        item.relative_to.return_value = PureWindowsPath('data/materials.json')
        item.suffix = '.json'
        item.is_file.return_value = True
        item.read_bytes.return_value = payload
        traversable.rglob.return_value = [item]
        with patch.object(registry, 'files', side_effect=[pin_root, core_root]), \
                patch.object(registry, 'Path', return_value=traversable), \
                patch.object(registry, 'BASELINE_PIN', sha256(pin_bytes).hexdigest()):
            self.assertEqual(registry.baseline_digest(), registry.digest(manifest))
        item.relative_to.assert_called_once_with(core_root)

    def test_old_database_anchor_is_rejected_without_migration(self):
        # A synthetic empty review is enough to exercise persistent anchors.
        # No existing or user-owned database path is accessed.
        review = {'schema': 'computed-review-recovery/1', 'packet_sha256': '0' * 64,
                  'reviewer': 'Synthetic baseline compatibility test',
                  'rationale': 'No real material admission', 'records': []}
        for old_baseline in (OLD_BASELINE, PREVIOUS_BASELINE, EAF_BASELINE, NC2_BASELINE,
                             INTEGRATED_BASELINE, PRE_EVIDENCE_BATCH_BASELINE, PRE_GROWTH_BATCH_BASELINE, PRE_PUR_BATCH_BASELINE, PRE_TABLE_BATCH_BASELINE, PRE_RCA_BATCH_BASELINE, PRE_BINARY_BATCH_BASELINE, PRE_MTIBE_BATCH_BASELINE):
            with self.subTest(old_baseline=old_baseline):
                with tempfile.TemporaryDirectory() as temporary:
                    database = Path(temporary) / 'old-baseline.db'
                    with patch.object(registry, 'baseline_digest', return_value=old_baseline):
                        old = registry.ComputedRegistry(database, deepcopy(review),
                            trusted_review_sha256=registry.digest(review))
                    before = database.read_bytes()
                    with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                        registry.ComputedRegistry(database, review,
                            trusted_review_sha256=registry.digest(review))
                    self.assertEqual(database.read_bytes(), before)
                    self.assertEqual(old.snapshot()['baseline_version'], old_baseline)
                    self.assertEqual(old.snapshot()['records'], [])

    def test_changed_core_resource_fails_even_with_unchanged_identity_count(self):
        original = Path.read_bytes

        def changed(path):
            raw = original(path)
            if path.name == 'materials.json' and path.parent.name == 'data':
                value = json.loads(raw)
                value['identities'][0]['name'] += ' altered'
                return registry.canonical(value)
            return raw

        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'Installed legacy baseline differs'):
                registry.baseline_digest()


if __name__ == '__main__':
    unittest.main()
