"""Offline artifact-binding regressions, not scientific review of source records.

Real fixtures are the existing exact pinned metadata excerpts. Altered documents
and optional artifact payloads are synthetic test cases, never new admissions.
"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import formal_review_gaps as gaps
from nomad_batch import canonical, digest

SYNTHETIC_BYTES = b'Synthetic evidence-binding fixture only; not a source or review receipt.\n'


class FormalReviewGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parents = {key: (gaps.ROOT / value['path']).read_bytes() for key, value in gaps.PARENT.items()}
        cls.boundary = gaps.load_review_boundary()

    @contextmanager
    def changed_parent_bytes(self, changes):
        original = Path.read_bytes
        by_path = {gaps.ROOT / gaps.PARENT[key]['path']: value for key, value in changes.items()}
        def read(path):
            return by_path[path] if path in by_path else original(path)
        with patch.object(Path, 'read_bytes', read):
            yield

    @contextmanager
    def synthetic_profile(self, mutate=None):
        """Independent synthetic expected pins let tests reach cross-file guards."""
        source, review, pin = (json.loads(self.parents[key]) for key in ('input', 'review', 'acceptance_pin'))
        expected_payload = hashlib.sha256(SYNTHETIC_BYTES).hexdigest()
        for candidate_id in gaps.SELECTED:
            for document in (source, review):
                row = next(r for r in document['records'] if r['candidate_id'] == candidate_id)
                for label in gaps.RECORD_EVIDENCE:
                    row['evidence'][label] = expected_payload
        raw_input = canonical(source)
        review['input_file_sha256'] = hashlib.sha256(raw_input).hexdigest()
        raw_review = canonical(review)
        pin.update(input_file_sha256=hashlib.sha256(raw_input).hexdigest(),
                   normalized_review_file_sha256=hashlib.sha256(raw_review).hexdigest(),
                   canonical_review_sha256=digest(review), candidate_file_sha256=expected_payload,
                   source_unit_definition_snapshot_sha256=expected_payload)
        if mutate:
            mutate(source, review, pin)
        raw = {'input': canonical(source), 'review': canonical(review), 'acceptance_pin': canonical(pin)}
        parent = {key: dict(gaps.PARENT[key], sha256=hashlib.sha256(value).hexdigest()) for key, value in raw.items()}
        selected = {key: dict(value, canonical_sha256=digest(review['records'][value['review_index']]))
                    for key, value in gaps.SELECTED.items()}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for key, value in raw.items():
                path = root / parent[key]['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)
            with patch.object(gaps, 'PARENT', parent), patch.object(gaps, 'SELECTED', selected), \
                 patch.object(gaps, 'CANONICAL_REVIEW_SHA256', digest(review)), \
                 patch.object(gaps, 'load_review_boundary', return_value=deepcopy(self.boundary)):
                yield root

    def assert_held(self, report):
        self.assertEqual(report['formal_release']['state'], 'held')
        self.assertEqual(report['formal_release']['admitted_delta'], 0)
        self.assertFalse(report['formal_release']['automatic_admission'])
        self.assertEqual(len(report['gaps']), 6)
        self.assertEqual({gap['status'] for gap in report['gaps']}, {'unverified_for_new_release'})
        for gap in report['gaps']:
            self.assertEqual(set(gap['candidate_ids']), set(gaps.SELECTED))
            self.assertTrue(set(gap['related_evidence_labels']) <= {row['label'] for row in report['evidence_observations']})

    def test_exact_existing_subset_is_deterministic_and_held(self):
        report = gaps.build_report()
        self.assertEqual(canonical(report), canonical(gaps.build_report()))
        self.assert_held(report)
        self.assertEqual(report['review_boundary']['formal_project_total'], 1188)
        self.assertEqual(report['review_boundary']['excluded_example_count'], 62)
        self.assertEqual(report['historical_acceptance']['decision'], 'accepted_exact_scoped_metadata_only')
        self.assertEqual(report['historical_acceptance']['persistent_admissions'], 0)
        self.assertEqual([r['source_review_decision'] for r in report['selected_records']], ['accepted', 'accepted'])
        unsigned = deepcopy(report)
        self.assertEqual(unsigned.pop('report_sha256'), digest(unsigned))

    def test_each_parent_byte_drift_is_rejected(self):
        for key, value in self.parents.items():
            with self.subTest(parent=key), self.changed_parent_bytes({key: value + b' '}):
                with self.assertRaisesRegex(ValueError, 'Parent artifact hash mismatch'):
                    gaps.build_report()

    def test_self_consistent_rewritten_parents_do_not_replace_trust_anchors(self):
        source, review, pin = (json.loads(self.parents[key]) for key in ('input', 'review', 'acceptance_pin'))
        source['synthetic_unreviewed_change'] = True
        raw_input = canonical(source)
        review['input_file_sha256'] = hashlib.sha256(raw_input).hexdigest()
        review['rationale'] = 'Synthetic replacement, not an authorized review'
        raw_review = canonical(review)
        pin.update(input_file_sha256=review['input_file_sha256'],
                   normalized_review_file_sha256=hashlib.sha256(raw_review).hexdigest(),
                   canonical_review_sha256=digest(review))
        with self.changed_parent_bytes({'input': raw_input, 'review': raw_review, 'acceptance_pin': canonical(pin)}):
            with self.assertRaisesRegex(ValueError, 'Parent artifact hash mismatch'):
                gaps.build_report()

    def test_cross_file_pin_mismatch_fails_after_independent_byte_binding(self):
        for field in ('input_file_sha256', 'normalized_review_file_sha256', 'canonical_review_sha256'):
            def mutate(source, review, pin):
                pin[field] = '0' * 64
            with self.subTest(field=field), self.synthetic_profile(mutate) as root:
                with self.assertRaisesRegex(ValueError, 'binding mismatch'):
                    gaps.build_report(root)

    def test_selection_rejects_unknown_duplicate_and_partial_ids(self):
        ids = list(gaps.SELECTED)
        for invalid in ([ids[0], 'unreviewed_candidate'], [ids[0], ids[0]], ids[:1], []):
            with self.subTest(ids=invalid), self.assertRaisesRegex(ValueError, 'exactly the two pinned'):
                gaps.build_report(candidate_ids=invalid)
        self.assertEqual(gaps.build_report(candidate_ids=list(reversed(ids))), gaps.build_report())

    def test_selected_record_binding_rejects_stale_index_and_hash(self):
        for field, value in [('review_index', 3), ('canonical_sha256', '0' * 64)]:
            selection = deepcopy(gaps.SELECTED)
            selection[next(iter(selection))][field] = value
            with self.subTest(field=field), patch.object(gaps, 'SELECTED', selection):
                with self.assertRaisesRegex(ValueError, 'Selected canonical record binding mismatch'):
                    gaps.build_report()

    def test_parent_record_cardinality_and_duplicate_ids_fail_closed(self):
        for duplicate in (False, True):
            def mutate(source, review, pin):
                if duplicate:
                    review['records'][-1]['candidate_id'] = review['records'][0]['candidate_id']
                else:
                    review['records'].pop()
                pin['normalized_review_file_sha256'] = hashlib.sha256(canonical(review)).hexdigest()
                pin['canonical_review_sha256'] = digest(review)
            with self.subTest(duplicate=duplicate), self.synthetic_profile(mutate) as root:
                with self.assertRaisesRegex(ValueError, 'cardinality or identity'):
                    gaps.build_report(root)

    def test_mismatched_shared_source_reference_is_not_silently_coalesced(self):
        def mutate(source, review, pin):
            candidate_id = list(gaps.SELECTED)[1]
            for document in (source, review):
                row = next(r for r in document['records'] if r['candidate_id'] == candidate_id)
                row['evidence']['archive_response_sha256'] = 'c' * 64
            review['input_file_sha256'] = hashlib.sha256(canonical(source)).hexdigest()
            pin.update(input_file_sha256=review['input_file_sha256'],
                       normalized_review_file_sha256=hashlib.sha256(canonical(review)).hexdigest(),
                       canonical_review_sha256=digest(review))
        with self.synthetic_profile(mutate) as root:
            with self.assertRaisesRegex(ValueError, 'Selected source evidence hashes differ'):
                gaps.build_report(root)

    def test_source_formula_density_and_allowed_unknowns_are_preserved(self):
        report = gaps.build_report()
        source_review = json.loads(self.parents['review'])
        for selected in report['selected_records']:
            original = source_review['records'][int(selected['review_pointer'].split('/')[-1])]
            self.assertEqual(selected['record'], original)
            self.assertEqual(original['density']['unit'], 'kg/m^3')
            self.assertEqual(original['density']['evidence_kind'], 'computed')
            for condition in ('temperature_K', 'pressure_Pa'):
                self.assertIsNone(original['material_scope'][condition])
            for state in ('experimental_existence', 'phase_stability', 'equilibrium', 'convergence'):
                self.assertEqual(original['material_scope'][state], 'unknown')
            self.assertEqual(original['electronic_behavior'], 'unknown')
        oxide = report['selected_records'][1]['record']
        self.assertEqual(oxide['formula'], 'O8Re2Ru4')
        self.assertEqual(oxide['conservative_count_bucket'], 'computed-composition:O4ReRu2')
        self.assertNotIn('unknown_conditions', {gap['id'] for gap in report['gaps']})

    def test_historical_checks_and_confidence_do_not_authenticate_review(self):
        report = gaps.build_report()
        self.assertFalse(report['historical_acceptance']['reviewer_authenticated_by_this_report'])
        self.assertFalse(report['historical_acceptance']['current_scientific_verification'])
        for selected in report['selected_records']:
            self.assertEqual(selected['basis'], 'historical_parent_review')
            self.assertFalse(selected['current_scientific_verification'])
            self.assertTrue(all(v for v in selected['record']['checks'].values() if type(v) is bool))
        self.assert_held(report)

    def test_unprovided_missing_and_mismatched_evidence_are_distinct_observations(self):
        report = gaps.build_report()
        self.assertEqual({r['availability'] for r in report['evidence_observations']}, {'reference_only_not_provided'})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mismatch = root / 'synthetic.dat'
            mismatch.write_bytes(SYNTHETIC_BYTES)
            report = gaps.build_report(local_artifacts={'archive_response_sha256': root / 'missing.dat',
                                                        'attribution_response_sha256': mismatch})
            observations = {row['label']: row for row in report['evidence_observations']}
            self.assertEqual(observations['archive_response_sha256']['availability'], 'missing')
            self.assertEqual(observations['attribution_response_sha256']['availability'], 'digest_mismatch')
            self.assert_held(report)
            output = canonical(report).decode()
            self.assertNotIn(str(root), output)
            self.assertNotIn(root.as_posix(), output)
            self.assertNotIn(SYNTHETIC_BYTES.decode().strip(), output)

    def test_all_matching_artifact_bytes_still_leave_every_review_gate_open(self):
        with self.synthetic_profile() as root:
            artifact = root / 'private-fixture.dat'
            artifact.write_bytes(SYNTHETIC_BYTES)
            labels = set(gaps.RECORD_EVIDENCE) | {'source_unit_definition_snapshot_sha256', 'acceptance_candidate_file_sha256'}
            paths = {label: artifact for label in labels}
            report = gaps.build_report(root, local_artifacts=paths)
            self.assertEqual({row['availability'] for row in report['evidence_observations']}, {'digest_match'})
            self.assertEqual({row['bytes_read'] for row in report['evidence_observations']}, {len(SYNTHETIC_BYTES)})
            self.assert_held(report)
            self.assertFalse(report['historical_acceptance']['reviewer_authenticated_by_this_report'])
            self.assertEqual(report, gaps.build_report(root, local_artifacts=paths))
            self.assertNotIn(str(root), canonical(report).decode())

    def test_candidate_packet_and_acceptance_candidate_file_remain_distinct(self):
        observations = {r['label']: r for r in gaps.build_report()['evidence_observations']}
        packet = observations['candidate_packet_sha256']
        candidate_file = observations['acceptance_candidate_file_sha256']
        self.assertNotEqual(packet['expected_sha256'], candidate_file['expected_sha256'])
        self.assertTrue(all(r['artifact'] == 'review' for r in packet['references']))
        self.assertEqual(candidate_file['references'], [{'artifact': 'acceptance_pin', 'pointer': '/candidate_file_sha256'}])

    def test_artifact_size_and_read_error_are_bounded_and_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / 'sensitive-filename.dat'
            artifact.write_bytes(SYNTHETIC_BYTES)
            with patch.object(gaps, 'MAX_ARTIFACT_BYTES', 4):
                report = gaps.build_report(local_artifacts={'archive_response_sha256': artifact})
            row = next(r for r in report['evidence_observations'] if r['label'] == 'archive_response_sha256')
            self.assertEqual(row['availability'], 'size_limit_exceeded')
            self.assertEqual(row['bytes_read'], 5)
            report = gaps.build_report(local_artifacts={'archive_response_sha256': root})
            row = next(r for r in report['evidence_observations'] if r['label'] == 'archive_response_sha256')
            self.assertEqual(row['availability'], 'not_regular_file')
            self.assertNotIn(str(root), canonical(report).decode())
            self.assert_held(report)

    def test_nonregular_file_is_refused_before_open(self):
        with patch.object(Path, 'stat', return_value=SimpleNamespace(st_mode=stat.S_IFIFO)), \
             patch.object(Path, 'open', side_effect=AssertionError('FIFO must not be opened')):
            observation = gaps.observe_artifact('synthetic', '0' * 64, [], 'synthetic-pipe')
        self.assertEqual(observation['availability'], 'not_regular_file')
        self.assertIsNone(observation['bytes_read'])

    def test_artifact_os_error_is_sanitized(self):
        with patch.object(Path, 'stat', side_effect=PermissionError('private absolute location')):
            observation = gaps.observe_artifact('synthetic', '0' * 64, [], 'private absolute location')
        self.assertEqual(observation['availability'], 'read_error')
        self.assertNotIn('private absolute location', canonical(observation).decode())

    def test_unknown_artifact_label_is_refused_without_reading_path(self):
        with self.assertRaisesRegex(ValueError, 'Unknown local evidence label'):
            gaps.build_report(local_artifacts={'unscoped_private_asset': 'must-not-be-read'})

    def test_reads_are_detached_and_formal_boundary_unchanged(self):
        before = gaps.load_review_boundary()
        report = gaps.build_report()
        report['selected_records'][0]['record']['material_scope']['temperature_K'] = 300
        report['historical_acceptance']['count_policy']['rule'] = 'synthetic mutation'
        after = gaps.build_report()
        self.assertIsNone(after['selected_records'][0]['record']['material_scope']['temperature_K'])
        self.assertEqual(before, gaps.load_review_boundary())
        for label, raw in self.parents.items():
            self.assertEqual(raw, (gaps.ROOT / gaps.PARENT[label]['path']).read_bytes())

    def test_cli_held_success_and_fail_closed_exit_codes(self):
        command = [sys.executable, str(Path(gaps.__file__))]
        result = subprocess.run(command, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_held(json.loads(result.stdout))
        result = subprocess.run(command + ['--artifact', 'unknown=private-location'], capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertNotIn(b'private-location', result.stderr)


if __name__ == '__main__':
    unittest.main()
