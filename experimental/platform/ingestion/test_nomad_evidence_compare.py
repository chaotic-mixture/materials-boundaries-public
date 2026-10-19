"""Offline review comparisons preserve source differences without admission.

All stores are created by the existing incremental collector using synthetic
responses. No test contacts a provider or edits a packaged material record.
"""
import copy
from contextlib import closing, contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import nomad_evidence_compare as comparison
import nomad_incremental as inc
from test_nomad_batch import fixture
from test_nomad_incremental import BOUNDARY, QueueTransport, response


DENSITY = '/archive/results/properties/structures/structure_original/mass_density'
STRUCTURE = '/archive/results/properties/structures/structure_original'
MATERIAL = '/archive/results/material'
METHOD = '/archive/results/method'


def author(entry_id='entry_1', name='Scientist'):
    return {'entry_id': entry_id, 'authors': [{'name': name}], 'datasets': []}


def structure(row):
    return row['archive']['results']['properties']['structures']['structure_original']


def files_snapshot(root):
    return {str(path.relative_to(root)): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in root.rglob('*') if path.is_file()}


def set_scalar(row, pointer, value):
    """Set one explicit fixture pointer, creating only its required containers."""
    tokens = pointer.lstrip('/').split('/')
    node = row
    for index, token in enumerate(tokens[:-1]):
        container = [] if tokens[index + 1].isdigit() else {}
        if isinstance(node, list):
            position = int(token)
            while len(node) <= position:
                node.append(copy.deepcopy(container))
            node = node[position]
        else:
            node = node.setdefault(token, container)
    if isinstance(node, list):
        position = int(tokens[-1])
        while len(node) <= position:
            node.append(None)
        node[position] = value
    else:
        node[tokens[-1]] = value


class EvidenceComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        inc.init_store(self.root, boundary=BOUNDARY)
        self.now = 1_800_000_000

    def tearDown(self):
        self.temp.cleanup()

    def cycle(self, rows=None, authors=None, extra=()):
        rows = [fixture()] if rows is None else rows
        replies = [response(rows)]
        if rows:
            authors = ([author(eid) for eid in sorted({row['entry_id'] for row in rows})]
                       if authors is None else authors)
            replies.append(response(authors))
        replies.extend(extra)
        transport = QueueTransport(*replies)
        self.now += 10
        result = inc.update(self.root, transport=transport, clock=lambda: self.now)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(transport.responses, [], 'The synthetic response plan must be consumed')
        return result

    def compare(self, before=1, after=2):
        return comparison.compare(self.root, before=before, after=after)

    def entry(self, result, entry_id='entry_1'):
        matches = [row for row in result['entry_changes'] if row['provider_entry_id'] == entry_id]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def field(self, entry, pointer, source='archive'):
        matches = [row for row in entry['fields']
                   if row['source'] == source and row['pointer'] == pointer]
        self.assertEqual(len(matches), 1, (source, pointer, entry['fields']))
        return matches[0]

    def assert_value(self, view, value, kind):
        self.assertTrue(view['present'])
        self.assertEqual(view['type'], kind)
        self.assertEqual(view['sha256'], inc.digest(value))
        self.assertEqual(view['value'], value)

    def test_density_change_has_source_values_and_separate_candidate_change(self):
        first = fixture()
        second = copy.deepcopy(first)
        structure(second)['mass_density'] = 8100
        old = self.cycle([first])
        new = self.cycle([second])
        result = self.compare()
        self.assertEqual(result['schema'], 'nomad-evidence-compare/1')
        entry = self.entry(result)
        self.assertEqual(entry['change'], 'changed')
        self.assertEqual(entry['source_comparison'], 'unique')
        self.assertEqual(entry['before']['archive_sha256'], [inc.digest(first)])
        self.assertEqual(entry['after']['archive_sha256'], [inc.digest(second)])
        change = self.field(entry, DENSITY)
        self.assert_value(change['before'], 8000, 'integer')
        self.assert_value(change['after'], 8100, 'integer')
        self.assertEqual(result['candidate_changes'], [{
            'provider_material_id': 'material_1', 'change': 'changed',
            'old_sha256': inc.digest({key: value for key, value in
                old['candidate_packet']['candidates'][0].items() if key != 'evidence'}),
            'new_sha256': inc.digest({key: value for key, value in
                new['candidate_packet']['candidates'][0].items() if key != 'evidence'})}])
        self.assertEqual(result['formal_project_total'], 1116)
        self.assertEqual(result['admitted_delta'], 0)
        self.assertIs(result['release_authorized'], False)

    def test_saved_historical_scope_is_preserved_and_report_count_drift_rejected(self):
        self.cycle()
        self.cycle()
        # This is an explicitly synthetic old-store fixture, not a migration.
        with inc.connect(self.root) as db, db:
            boundary = inc.meta(db, 'review_boundary')
            boundary.update(formal_project_total=1081, formal_legacy_count=1057,
                            baseline_commit='4c5656cf6ba0ad1a54b736e0568e97abe4815c29',
                            sha256='synthetic-historical-boundary')
            boundary['source_sha256']['materials_boundaries/data/materials.json'] = (
                'ffd27ae7a927494083cbdcb173847502283f9ff0f69b8b7321abe0b042824dc1')
            inc.set_meta(db, 'review_boundary', boundary)
            inc.set_meta(db, 'boundary_sha256', inc.digest(boundary))
            for row in db.execute('SELECT state FROM cycles').fetchall():
                cycle = inc.decode(row['state'])
                cycle['report']['formal_project_total'] = 1081
                cycle['report']['review_boundary_sha256'] = boundary['sha256']
                cycle['report']['candidate_packet']['baseline_commit'] = boundary['baseline_commit']
                inc.save_cycle(db, cycle)
        before = files_snapshot(self.root)
        result = self.compare()
        self.assertEqual(result['formal_project_total'], 1081)
        self.assertEqual(result['excluded_example_count'], 62)
        self.assertEqual(result['admitted_delta'], 0)
        self.assertEqual(result['review_boundary_sha256'], 'synthetic-historical-boundary')
        self.assertEqual(files_snapshot(self.root), before)
        with inc.connect(self.root) as db, db:
            cycle = inc.latest(db)
            cycle['report']['formal_project_total'] = 1103
            inc.save_cycle(db, cycle)
        with self.assertRaisesRegex(ValueError, 'scope binding mismatch'):
            self.compare()

    def test_selected_method_formula_provenance_and_attribution_are_expanded(self):
        self.cycle()
        row = fixture(formula='FeNi2')
        row['archive']['metadata']['nomad_commit'] = 'next-commit'
        method = row['archive']['results']['method']
        method['simulation']['program_name'] = 'Quantum ESPRESSO'
        method['simulation']['program_version'] = '7.3'
        attribution = author(name='Another Scientist')
        attribution['references'] = ['https://example.org/traceable-scalar']
        attribution['datasets'] = [{'dataset_id': 'dataset_1', 'dataset_name': 'Scalar evidence'}]
        self.cycle([row], [attribution])
        entry = self.entry(self.compare())
        expected = [(MATERIAL + '/chemical_formula_hill', 'FeNi2'),
                    ('/archive/metadata/nomad_commit', 'next-commit'),
                    (METHOD + '/simulation/program_name', 'Quantum ESPRESSO'),
                    (METHOD + '/simulation/program_version', '7.3')]
        for pointer, value in expected:
            with self.subTest(pointer=pointer):
                self.assert_value(self.field(entry, pointer)['after'], value, 'string')
        self.assert_value(self.field(entry, '/authors/0/name', 'attribution')['after'],
                          'Another Scientist', 'string')
        reference = self.field(entry, '/references/0', 'attribution')['after']
        self.assertTrue(reference['present'])
        self.assertEqual(reference['type'], 'string')
        self.assertEqual(reference['sha256'], inc.digest('https://example.org/traceable-scalar'))
        self.assertNotIn('value', reference)
        self.assertTrue(reference['value_omitted'])
        self.assert_value(self.field(entry, '/datasets/0/dataset_name', 'attribution')['after'],
                          'Scalar evidence', 'string')

    def test_license_change_preserves_recorded_gate_and_removes_only_candidate(self):
        self.cycle()
        row = fixture()
        row['archive']['metadata']['license'] = 'unknown'
        report = self.cycle([row])
        result = self.compare()
        entry = self.entry(result)
        self.assertEqual(entry['before']['gate_reasons'], [])
        self.assertEqual(entry['after']['gate_reasons'], ['rights_quarantine'])
        self.assertEqual(entry['after']['gate_sha256'], inc.digest(report['gate_exclusions']))
        self.assert_value(self.field(entry, '/archive/metadata/license')['after'], 'unknown', 'string')
        self.assertEqual(result['candidate_changes'][0]['change'], 'removed_from_candidate_queue')
        self.assertIsNone(result['candidate_changes'][0]['new_sha256'])
        self.assertEqual(result['admitted_delta'], 0)

    def test_missing_density_and_null_density_remain_distinct(self):
        missing, null = fixture(), fixture()
        del structure(missing)['mass_density']
        structure(null)['mass_density'] = None
        self.cycle([missing])
        self.cycle([null])
        result = self.compare()
        change = self.field(self.entry(result), DENSITY)
        self.assertEqual(change['before'], {'present': False})
        self.assert_value(change['after'], None, 'null')
        self.assertEqual(result['candidate_changes'], [])

    def test_equal_numeric_value_with_different_json_type_is_a_source_change(self):
        self.cycle()
        row = fixture()
        structure(row)['mass_density'] = 8000.0
        self.cycle([row])
        change = self.field(self.entry(self.compare()), DENSITY)
        self.assert_value(change['before'], 8000, 'integer')
        self.assert_value(change['after'], 8000.0, 'number')
        self.assertNotEqual(change['before']['sha256'], change['after']['sha256'])

    def test_boolean_dimensions_and_wrong_units_keep_gate_reasons(self):
        self.cycle()
        row = fixture()
        structure(row)['mass_density_unit'] = 'g/cm^3'
        structure(row)['dimension_types'] = [True, 1, 1]
        self.cycle([row])
        entry = self.entry(self.compare())
        self.assertIn('not_three_dimensional', entry['after']['gate_reasons'])
        self.assert_value(self.field(entry, STRUCTURE + '/mass_density_unit')['after'],
                          'g/cm^3', 'string')
        changed_dimensions = [field for field in entry['fields']
                              if field['pointer'].startswith(STRUCTURE + '/dimension_types')]
        self.assertTrue(changed_dimensions)

    def test_wrong_unit_is_not_reinterpreted_or_converted(self):
        self.cycle()
        row = fixture()
        structure(row)['mass_density_unit'] = 'g/cm^3'
        structure(row)['mass_density'] = 8
        self.cycle([row])
        entry = self.entry(self.compare())
        self.assertEqual(entry['after']['gate_reasons'], ['unsupported_density_unit'])
        self.assert_value(self.field(entry, DENSITY)['after'], 8, 'integer')

    def test_author_list_order_is_preserved(self):
        a = author()
        a['authors'] = [{'name': 'Alpha'}, {'name': 'Beta'}]
        b = copy.deepcopy(a)
        b['authors'].reverse()
        self.cycle(authors=[a])
        self.cycle(authors=[b])
        entry = self.entry(self.compare())
        self.assert_value(self.field(entry, '/authors/0/name', 'attribution')['before'],
                          'Alpha', 'string')
        self.assert_value(self.field(entry, '/authors/0/name', 'attribution')['after'],
                          'Beta', 'string')
        self.assert_value(self.field(entry, '/authors/1/name', 'attribution')['after'],
                          'Alpha', 'string')
        self.assertEqual(entry['before']['attribution_sha256'], [inc.digest(a)])
        self.assertEqual(entry['after']['attribution_sha256'], [inc.digest(b)])

    def test_element_list_order_is_detected_without_claiming_a_new_material(self):
        self.cycle()
        row = fixture()
        row['archive']['results']['material']['elements'].reverse()
        self.cycle([row])
        result = self.compare()
        entry = self.entry(result)
        self.assert_value(self.field(entry, MATERIAL + '/elements/0')['before'], 'Fe', 'string')
        self.assert_value(self.field(entry, MATERIAL + '/elements/0')['after'], 'Ni', 'string')
        self.assert_value(self.field(entry, MATERIAL + '/elements/1')['after'], 'Fe', 'string')
        self.assertEqual(result['candidate_changes'], [])
        parent = self.field(entry, MATERIAL + '/elements')
        self.assertNotIn('value', parent['before'])
        self.assertNotIn('value', parent['after'])

    def test_method_name_change_keeps_unsupported_method_review_gate(self):
        self.cycle()
        row = fixture()
        row['archive']['results']['method']['method_name'] = 'GW'
        self.cycle([row])
        entry = self.entry(self.compare())
        self.assert_value(self.field(entry, METHOD + '/method_name')['before'], 'DFT', 'string')
        self.assert_value(self.field(entry, METHOD + '/method_name')['after'], 'GW', 'string')
        self.assertEqual(entry['after']['gate_reasons'], ['unsupported_method'])

    def test_nonrepresentative_calculation_change_is_not_hidden_by_same_candidate(self):
        a, z = fixture('entry_a'), fixture('entry_z')
        structure(z)['mass_density'] = 8200
        first = self.cycle([a, z])
        structure(z)['mass_density'] = 8300
        second = self.cycle([a, z])
        self.assertEqual(first['candidate_packet']['candidates'][0]['provider_entry_id'], 'entry_a')
        self.assertEqual(second['candidate_changes'], [])
        result = self.compare()
        self.assertEqual([row['provider_entry_id'] for row in result['entry_changes']], ['entry_z'])
        self.assert_value(self.field(self.entry(result, 'entry_z'), DENSITY)['after'], 8300, 'integer')
        self.assertEqual(result['candidate_changes'], [])

    def test_identical_duplicates_do_not_create_false_source_or_candidate_change(self):
        self.cycle([fixture(), fixture()], [author(), author()])
        self.cycle()
        result = self.compare()
        self.assertEqual(result['entry_changes'], [])
        self.assertEqual(result['candidate_changes'], [])
        self.assertEqual(result['ambiguous_entries'], [])

    def test_conflicting_archive_variants_are_not_arbitrarily_paired(self):
        self.cycle()
        changed = fixture()
        structure(changed)['mass_density'] = 8100
        self.cycle([fixture(), changed])
        result = self.compare()
        entry = self.entry(result)
        self.assertEqual(entry['source_comparison'], 'ambiguous_variants')
        self.assertEqual(entry['fields'], [])
        self.assertEqual(entry['after']['archive_sha256'], sorted([inc.digest(fixture()), inc.digest(changed)]))
        self.assertEqual(entry['after']['gate_reasons'], ['conflicting_duplicate_entry'])
        self.assertTrue(result['ambiguous_entries'])
        self.assertEqual(result['candidate_changes'][0]['change'], 'removed_from_candidate_queue')

    def test_conflicting_attribution_suppresses_even_unique_archive_field_pairing(self):
        self.cycle()
        row = fixture()
        structure(row)['mass_density'] = 8100
        authors = [author(name='First'), author(name='Second')]
        self.cycle([row], authors)
        result = self.compare()
        entry = self.entry(result)
        self.assertEqual(entry['source_comparison'], 'ambiguous_variants')
        self.assertEqual(entry['fields'], [])
        self.assertEqual(entry['after']['attribution_sha256'], sorted(map(inc.digest, authors)))
        self.assertTrue(result['ambiguous_entries'])

    def test_identical_conflicts_across_cycles_have_no_new_change(self):
        row = fixture()
        structure(row)['mass_density'] = 8100
        self.cycle([fixture(), row])
        self.cycle([row, fixture()])
        result = self.compare()
        self.assertEqual(result['entry_changes'], [])
        self.assertEqual(result['candidate_changes'], [])
        self.assertTrue(result['ambiguous_entries'])

    def test_withdrawal_and_reappearance_are_observations_without_admission(self):
        self.cycle()
        self.cycle([], extra=[response([])])
        self.cycle()
        withdrawn = self.compare(1, 2)
        returned = self.compare(2, 3)
        self.assertEqual(self.entry(withdrawn)['change'], 'observed_only_before')
        self.assertIs(self.entry(withdrawn)['after']['present'], False)
        self.assertEqual(withdrawn['candidate_changes'][0]['change'], 'removed_from_candidate_queue')
        self.assertEqual(self.entry(returned)['change'], 'observed_only_after')
        self.assertIs(self.entry(returned)['before']['present'], False)
        self.assertEqual(returned['candidate_changes'][0]['change'], 'added_to_candidate_queue')
        self.assertEqual(self.compare(1, 3)['entry_changes'], [])
        self.assertEqual(self.compare(1, 3)['candidate_changes'], [])
        for report in (withdrawn, returned):
            self.assertEqual(report['admitted_delta'], 0)
            self.assertIs(report['release_authorized'], False)

    def test_identical_cycles_are_deterministic_and_leave_store_and_lock_unchanged(self):
        self.cycle()
        self.cycle()
        before = files_snapshot(self.root)
        with patch.object(inc, 'public_transport', side_effect=AssertionError('Network is forbidden')):
            first = inc.canonical(self.compare())
            second = inc.canonical(self.compare())
        self.assertEqual(first, second)
        result = json.loads(first)
        self.assertEqual(result['entry_changes'], [])
        self.assertEqual(result['candidate_changes'], [])
        self.assertEqual(files_snapshot(self.root), before)
        with inc.locked(self.root):
            self.assertEqual(inc.canonical(self.compare()), first)
        self.assertEqual(files_snapshot(self.root), before)

    def test_one_readonly_snapshot_and_archived_gates_are_used(self):
        self.cycle()
        row = fixture()
        row['archive']['metadata']['license'] = 'unknown'
        self.cycle([row])
        calls = []
        connect = inc.connect

        @contextmanager
        def observed_connect(root, readonly=False):
            calls.append(readonly)
            with connect(root, readonly=readonly) as database:
                yield database

        with patch.object(inc, 'connect', observed_connect), \
                patch.object(inc, 'normalize', side_effect=AssertionError('Do not rerun scientific gates')), \
                patch.object(inc, 'assemble_report', side_effect=AssertionError('Use archived reports')):
            result = self.compare()
        self.assertEqual(calls, [True])
        self.assertEqual(self.entry(result)['after']['gate_reasons'], ['rights_quarantine'])

        def assert_wal_refused(store):
            before = files_snapshot(store)
            with patch.object(inc, 'connect', side_effect=AssertionError('Do not open SQLite for WAL stores')):
                with self.assertRaisesRegex(ValueError, 'rollback-journal store'):
                    comparison.compare(store, before=1, after=2)
            command = [sys.executable, str(Path(inc.__file__).resolve()), 'compare', str(store),
                       '--before', '1', '--after', '2']
            completed = subprocess.run(command, capture_output=True, timeout=30)
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(completed.stdout, b'')
            self.assertIn(b'rollback-journal store', completed.stderr)
            self.assertNotIn(str(store).encode(), completed.stderr)
            self.assertEqual(files_snapshot(store), before)

        original_database = (self.root / inc.DB_NAME).read_bytes()
        active = self.root / 'active-wal'
        active.mkdir()
        (active / inc.DB_NAME).write_bytes(original_database)
        with closing(sqlite3.connect(active / inc.DB_NAME)) as writer:
            self.assertEqual(writer.execute('PRAGMA journal_mode=WAL').fetchone()[0], 'wal')
            writer.execute("UPDATE metadata SET value=value WHERE key='schema'")
            writer.commit()
            self.assertTrue((active / (inc.DB_NAME + '-wal')).is_file())
            self.assertTrue((active / (inc.DB_NAME + '-shm')).is_file())
            with self.subTest(wal='active_with_coordination_files'):
                assert_wal_refused(active)
            without_shm = self.root / 'wal-without-shm'
            without_shm.mkdir()
            for name in (inc.DB_NAME, inc.DB_NAME + '-wal'):
                (without_shm / name).write_bytes((active / name).read_bytes())
            self.assertFalse((without_shm / (inc.DB_NAME + '-shm')).exists())
            with self.subTest(wal='copied_without_shm'):
                assert_wal_refused(without_shm)

        closed = self.root / 'closed-wal'
        closed.mkdir()
        (closed / inc.DB_NAME).write_bytes(original_database)
        with closing(sqlite3.connect(closed / inc.DB_NAME)) as writer:
            self.assertEqual(writer.execute('PRAGMA journal_mode=WAL').fetchone()[0], 'wal')
        self.assertEqual((closed / inc.DB_NAME).read_bytes()[18:20], b'\x02\x02')
        self.assertFalse((closed / (inc.DB_NAME + '-wal')).exists())
        self.assertFalse((closed / (inc.DB_NAME + '-shm')).exists())
        with self.subTest(wal='closed_without_coordination_files'):
            assert_wal_refused(closed)

    def test_cycle_bindings_match_exact_archived_state_report_and_attempts(self):
        self.cycle()
        self.cycle()
        result = self.compare()
        with inc.connect(self.root, readonly=True) as db:
            for side, cycle_id in [('before_cycle', 1), ('after_cycle', 2)]:
                with self.subTest(side=side):
                    state_text = db.execute('SELECT state FROM cycles WHERE id=?', (cycle_id,)).fetchone()[0]
                    state = json.loads(state_text)
                    binding = result[side]
                    self.assertEqual(binding['id'], cycle_id)
                    self.assertEqual(binding['state_sha256'], hashlib.sha256(state_text.encode()).hexdigest())
                    self.assertEqual(binding['report_sha256'], inc.digest(state['report']))
                    self.assertEqual(len(binding['evidence']), 2)
                    bound_hashes = {item['response_sha256'] for item in binding['evidence']}
                    expected = {json.loads(row[0])['sha256'] for row in db.execute(
                        'SELECT record FROM attempts WHERE cycle=? AND raw IS NOT NULL', (cycle_id,))}
                    self.assertEqual(bound_hashes, expected)

    def test_unknown_source_fields_are_not_exported_and_remain_explicitly_unexpanded(self):
        self.cycle()
        token = 'SYNTHETIC-NOT-A-CREDENTIAL-Do-Not-Echo-93827'
        row = fixture()
        row['archive']['metadata']['private_internal_comment'] = token
        row['archive']['unknown_envelope'] = {'nested': token}
        attribution = author()
        attribution['authors'][0]['unselected_email'] = token
        self.cycle([row], [attribution])
        result = self.compare()
        entry = self.entry(result)
        serialized = inc.canonical(result).decode()
        self.assertNotIn(token, serialized)
        self.assertNotIn('private_internal_comment', serialized)
        self.assertNotIn('unknown_envelope', serialized)
        self.assertEqual([(item['source'], item['pointer']) for item in entry['fields']],
                         [('attribution', '/authors')])
        self.assertNotIn('value', entry['fields'][0]['before'])
        self.assertNotIn('value', entry['fields'][0]['after'])
        self.assertIs(entry['unexpanded_source_change'], True)
        self.assertNotEqual(entry['before']['archive_sha256'], entry['after']['archive_sha256'])
        self.assertNotEqual(entry['before']['attribution_sha256'], entry['after']['attribution_sha256'])

        # Independently enumerate the selected field classes so a future export
        # expansion requires an explicit privacy regression, including malformed
        # string values at normally numeric or identifier locations.
        archive_paths = [
            '/archive/metadata/' + key for key in (
                'license', 'external_db', 'upload_id', 'mainfile', 'nomad_version',
                'nomad_commit', 'last_processing_time', 'references/0')]
        archive_paths += [MATERIAL + '/' + key for key in (
            'material_id', 'chemical_formula_hill', 'elements/0', 'structural_type',
            'symmetry/space_group_number')]
        archive_paths += [METHOD + '/' + key for key in (
            'method_name', 'simulation/program_name', 'simulation/program_version')]
        archive_paths += [STRUCTURE + '/' + key for key in (
            'mass_density', 'mass_density_unit', 'unit', 'dimension_types/0')]
        attribution_paths = ['/authors/0/name', '/references/0', '/datasets/0/dataset_id',
                             '/datasets/0/dataset_name', '/datasets/0/doi']
        self.assertEqual(set(archive_paths),
                         {'/' + path.replace('*', '0') for path in comparison.ARCHIVE_FIELDS})
        self.assertEqual(set(attribution_paths),
                         {'/' + path.replace('*', '0') for path in comparison.ATTRIBUTION_FIELDS})
        payloads = [
            (r'C:\SyntheticPrivate\PRIVATE_WINDOWS_MARKER\calculation.in', 'PRIVATE_WINDOWS_MARKER'),
            ('/synthetic/private/PRIVATE_POSIX_MARKER/scalar.dat', 'PRIVATE_POSIX_MARKER'),
            ('https://synthetic_user:SYNTHETIC_PASSWORD_MARKER@example.invalid/scalar'
             '?token=SYNTHETIC_QUERY_MARKER', 'SYNTHETIC_PASSWORD_MARKER'),
            ('Bearer SYNTHETIC_BEARER_MARKER', 'SYNTHETIC_BEARER_MARKER'),
            ('file:///synthetic/private/PRIVATE_FILE_MARKER', 'PRIVATE_FILE_MARKER'),
            ('api_key=SYNTHETIC_ASSIGNMENT_MARKER', 'SYNTHETIC_ASSIGNMENT_MARKER'),
            ('unsafe\nSYNTHETIC_CONTROL_MARKER', 'SYNTHETIC_CONTROL_MARKER'),
            ('ghp_SYNTHETIC_GITHUB_PREFIX_MARKER', 'SYNTHETIC_GITHUB_PREFIX_MARKER'),
            ('sk-SYNTHETIC_KEY_PREFIX_MARKER', 'SYNTHETIC_KEY_PREFIX_MARKER'),
            ('password SYNTHETIC_PASSWORD_WORD_MARKER', 'SYNTHETIC_PASSWORD_WORD_MARKER'),
        ]
        cases = []
        for index, (source, pointer) in enumerate(
                [('archive', path) for path in archive_paths] +
                [('attribution', path) for path in attribution_paths]):
            value, marker = payloads[index % len(payloads)]
            if pointer == MATERIAL + '/material_id':
                value, marker = payloads[0]  # Deliberately invalid provider identity.
            cases.append((source, pointer, value, marker))
        cases.extend(('archive', METHOD + '/simulation/program_version', value, marker)
                     for value, marker in payloads)
        for source, pointer, value, marker in cases:
            with self.subTest(source=source, pointer=pointer, shape=marker):
                row, attribution = fixture(), author()
                set_scalar(row if source == 'archive' else attribution, pointer, value)
                cycle = self.cycle([row], [attribution])
                before = files_snapshot(self.root)
                result = self.compare(1, cycle['cycle_id'])
                view = self.field(self.entry(result), pointer, source)['after']
                self.assertTrue(view['present'])
                self.assertEqual(view['type'], 'string')
                self.assertEqual(view['sha256'], inc.digest(value))
                self.assertNotIn('value', view)
                self.assertTrue(view['value_omitted'])
                self.assertIs(self.entry(result)['unexpanded_source_change'], True)
                self.assertNotIn(marker, inc.canonical(result).decode('utf-8'))
                command = [sys.executable, str(Path(inc.__file__).resolve()), 'compare', str(self.root),
                           '--before', '1', '--after', str(cycle['cycle_id'])]
                completed = subprocess.run(command, capture_output=True, timeout=30)
                self.assertEqual(completed.returncode, 0)
                self.assertEqual(completed.stderr, b'')
                self.assertEqual(json.loads(completed.stdout), result)
                self.assertNotIn(marker.encode(), completed.stdout)
                self.assertNotIn(marker.encode(), completed.stderr)
                self.assertNotIn(inc.canonical(str(self.root))[1:-1], completed.stdout)
                self.assertEqual(files_snapshot(self.root), before)

        # Structured identifiers are also output surfaces. Credential-shaped
        # identifiers must fail cleanly instead of bypassing scalar redaction.
        for location in ('entry', 'material'):
            with self.subTest(identifier_location=location):
                store = self.root / ('credential-shaped-' + location)
                inc.init_store(store, boundary=BOUNDARY)
                marker = 'ghp_SYNTHETIC_IDENTIFIER_MARKER'
                initial = fixture()
                changed = fixture(marker) if location == 'entry' else fixture(mid=marker)
                rows = [initial, changed] if location == 'entry' else [changed]
                for batch in ([initial], rows):
                    names = [author(row['entry_id']) for row in batch]
                    transport = QueueTransport(response(batch), response(names))
                    report = inc.update(store, transport=transport, clock=lambda: self.now)
                    self.assertEqual(report['status'], 'complete')
                    self.assertEqual(transport.responses, [])
                before = files_snapshot(store)
                with self.assertRaises(ValueError) as caught:
                    comparison.compare(store, before=1, after=2)
                self.assertNotIn(marker, str(caught.exception))
                command = [sys.executable, str(Path(inc.__file__).resolve()), 'compare', str(store),
                           '--before', '1', '--after', '2']
                completed = subprocess.run(command, capture_output=True, timeout=30)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, b'')
                self.assertTrue(completed.stderr)
                self.assertNotIn(marker.encode(), completed.stderr)
                self.assertNotIn(b'Traceback', completed.stderr)
                self.assertEqual(files_snapshot(store), before)

    def test_oversized_selected_scalar_is_hash_only(self):
        self.cycle()
        row = fixture()
        value = 'Synthetic public provenance ' * 100
        self.assertGreater(len(inc.canonical(value)), 2048)
        row['archive']['metadata']['nomad_commit'] = value
        self.cycle([row])
        result = self.compare()
        view = self.field(self.entry(result), '/archive/metadata/nomad_commit')['after']
        self.assertTrue(view['present'])
        self.assertEqual(view['type'], 'string')
        self.assertEqual(view['sha256'], inc.digest(value))
        self.assertNotIn('value', view)
        self.assertTrue(view['value_omitted'])
        self.assertNotIn(value, inc.canonical(result).decode())

    def test_unexpected_object_at_scalar_path_never_exports_arbitrary_values(self):
        self.cycle()
        marker = 'SYNTHETIC-UNSELECTED-OBJECT-CONTENT-7926'
        row = fixture()
        structure(row)['mass_density'] = {'value': 8, 'unit': 'g/cm^3', 'internal_note': marker}
        self.cycle([row])
        result = self.compare()
        view = self.field(self.entry(result), DENSITY)['after']
        self.assertEqual(view['type'], 'object')
        self.assertEqual(view['sha256'], inc.digest(structure(row)['mass_density']))
        self.assertNotIn('value', view)
        self.assertTrue(view['value_omitted'])
        self.assertNotIn(marker, inc.canonical(result).decode())

    def test_large_selected_list_stays_hash_only_instead_of_expanding_without_bound(self):
        marker = 'SYNTHETIC-LIST-PAYLOAD-NOT-FOR-EXPORT-'
        first = author()
        first['references'] = [marker + str(index) for index in range(101)]
        second = copy.deepcopy(first)
        second['references'].reverse()
        self.cycle(authors=[first])
        self.cycle(authors=[second])
        result = self.compare()
        fields = self.entry(result)['fields']
        self.assertEqual([(row['source'], row['pointer']) for row in fields],
                         [('attribution', '/references')])
        for side, source in [('before', first), ('after', second)]:
            self.assertEqual(fields[0][side]['sha256'], inc.digest(source['references']))
            self.assertNotIn('value', fields[0][side])
            self.assertTrue(fields[0][side]['value_omitted'])
        self.assertNotIn(marker, inc.canonical(result).decode())

    def test_natural_large_report_fails_before_returning_partial_json(self):
        store = self.root / 'large-report'
        inc.init_store(store, boundary=BOUNDARY, page_size=80,
                       max_response=3_000_000, max_bytes=5_000_000)
        for label in ('before-', 'after--'):
            rows = []
            for index in range(80):
                row = fixture(f'entry_{index:03d}', f'material_{index:03d}')
                # Keep the legitimate long label readable under the privacy
                # guard; output bounding still must reject the full report.
                value = label + 'ordinary ' * 221
                for key in ('mainfile', 'nomad_version', 'nomad_commit',
                            'last_processing_time', 'upload_id'):
                    row['archive']['metadata'][key] = value
                row['archive']['results']['method']['simulation'].update(
                    program_name=value, program_version=value)
                rows.append(row)
            authors = [author(row['entry_id']) for row in rows]
            transport = QueueTransport(response(rows), response(authors))
            report = inc.update(store, transport=transport, clock=lambda: self.now)
            self.assertEqual(report['status'], 'complete')
            self.assertEqual(transport.responses, [])
        before = files_snapshot(store)
        with self.assertRaisesRegex(ValueError, 'output limit'):
            comparison.compare(store, before=1, after=2)
        command = [sys.executable, str(Path(inc.__file__).resolve()), 'compare', str(store),
                   '--before', '1', '--after', '2']
        result = subprocess.run(command, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'output limit', result.stderr)
        self.assertEqual(files_snapshot(store), before)

    def test_cycle_ids_must_be_positive_explicit_integers_in_chronological_order(self):
        self.cycle()
        self.cycle()
        for before, after in [(0, 2), (-1, 2), (True, 2), (1.0, 2), ('1', 2),
                              (1, None), (1, False), (1, 2.0), (2, 1), (1, 1), (1, 99)]:
            with self.subTest(before=before, after=after), self.assertRaises(ValueError):
                self.compare(before, after)
        with self.assertRaises(TypeError):
            comparison.compare(self.root)

    def test_incomplete_cycle_is_refused_without_implicit_latest_fallback(self):
        self.cycle()
        paused = inc.update(self.root, transport=QueueTransport(response([fixture()]), OSError('offline')))
        self.assertEqual(paused['status'], 'paused')
        before = files_snapshot(self.root)
        with self.assertRaises(ValueError):
            self.compare()
        self.assertEqual(files_snapshot(self.root), before)

    def test_missing_store_is_not_created(self):
        missing = self.root / 'missing-store'
        with self.assertRaises(ValueError):
            comparison.compare(missing, before=1, after=2)
        self.assertFalse(missing.exists())

    def test_invalid_sqlite_file_fails_as_a_clean_cli_error_without_store_writes(self):
        store = self.root / 'invalid-sqlite'
        store.mkdir()
        (store / inc.DB_NAME).write_bytes(b'Synthetic invalid SQLite header\n')
        before = files_snapshot(store)
        with self.assertRaisesRegex(ValueError, 'Cannot read comparison store'):
            comparison.compare(store, before=1, after=2)
        command = [sys.executable, str(Path(inc.__file__).resolve()), 'compare', str(store),
                   '--before', '1', '--after', '2']
        result = subprocess.run(command, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        self.assertEqual(result.stderr.strip(), b'Cannot read comparison store')
        self.assertEqual(files_snapshot(store), before)

    def test_corrupt_raw_evidence_fails_closed_without_partial_result(self):
        self.cycle()
        self.cycle()
        with closing(sqlite3.connect(self.root / inc.DB_NAME)) as db, db:
            db.execute('UPDATE attempts SET raw=? WHERE id=(SELECT MIN(id) FROM attempts)', (b'{}',))
        before = files_snapshot(self.root)
        with self.assertRaisesRegex(ValueError, 'Evidence hash mismatch'):
            self.compare()
        self.assertEqual(files_snapshot(self.root), before)

    def test_missing_archived_report_fails_instead_of_rebuilding_it(self):
        self.cycle()
        self.cycle()
        with closing(sqlite3.connect(self.root / inc.DB_NAME)) as db, db:
            state = json.loads(db.execute('SELECT state FROM cycles WHERE id=1').fetchone()[0])
            del state['report']
            db.execute('UPDATE cycles SET state=? WHERE id=1', (inc.canonical(state).decode(),))
        with self.assertRaises(ValueError):
            self.compare()

    def test_saved_batch_references_and_observed_ids_cannot_omit_or_reuse_evidence(self):
        self.cycle()
        self.cycle()
        with inc.connect(self.root, readonly=True) as db:
            original = json.loads(db.execute('SELECT state FROM cycles WHERE id=1').fetchone()[0])
        for label in ('missing_batches', 'missing_attribution', 'reused_batch', 'wrong_seen', 'seen_absent',
                      'candidate_identifier', 'gate_reason', 'input_event', 'input_identifier'):
            with self.subTest(label=label):
                state = copy.deepcopy(original)
                if label == 'missing_batches':
                    state['batches'] = []
                elif label == 'missing_attribution':
                    state['batches'][0]['attribution'] = None
                elif label == 'reused_batch':
                    state['batches'].append(copy.deepcopy(state['batches'][0]))
                elif label == 'wrong_seen':
                    state['seen'] = ['other_entry']
                elif label == 'seen_absent':
                    state['absent'] = ['entry_1']
                elif label == 'candidate_identifier':
                    state['report']['candidate_packet']['candidates'][0]['provider_material_id'] = (
                        'ghp_SYNTHETIC_REPORT_IDENTIFIER_MARKER')
                elif label == 'gate_reason':
                    state['report']['gate_exclusions'] = [{'provider_entry_id': 'entry_1',
                        'reason': '/synthetic/private/SYNTHETIC_REPORT_GATE_MARKER'}]
                elif label == 'input_event':
                    state['report']['input_changes'][0]['change'] = (
                        'file:///synthetic/private/SYNTHETIC_REPORT_EVENT_MARKER')
                else:
                    state['report']['input_changes'][0]['provider_entry_id'] = (
                        'ghp_SYNTHETIC_REPORT_INPUT_MARKER')
                with closing(sqlite3.connect(self.root / inc.DB_NAME)) as db, db:
                    db.execute('UPDATE cycles SET state=? WHERE id=1', (inc.canonical(state).decode(),))
                before = files_snapshot(self.root)
                with self.assertRaises(ValueError):
                    self.compare()
                if label in ('candidate_identifier', 'gate_reason', 'input_event', 'input_identifier'):
                    command = [sys.executable, str(Path(inc.__file__).resolve()), 'compare', str(self.root),
                               '--before', '1', '--after', '2']
                    completed = subprocess.run(command, capture_output=True, timeout=30)
                    self.assertEqual(completed.returncode, 2)
                    self.assertEqual(completed.stdout, b'')
                    self.assertTrue(completed.stderr)
                    self.assertNotIn(b'SYNTHETIC_REPORT', completed.stderr)
                    self.assertNotIn(b'Traceback', completed.stderr)
                self.assertEqual(files_snapshot(self.root), before)

    def test_cli_success_outputs_only_deterministic_json_and_preserves_store(self):
        self.cycle()
        row = fixture()
        structure(row)['mass_density'] = 8100
        self.cycle([row])
        before = files_snapshot(self.root)
        command = [sys.executable, str(Path(inc.__file__).resolve()), 'compare', str(self.root),
                   '--before', '1', '--after', '2']
        first = subprocess.run(command, capture_output=True, timeout=30)
        second = subprocess.run(command, capture_output=True, timeout=30)
        self.assertEqual(first.returncode, 0, first.stderr.decode(errors='replace'))
        self.assertEqual(second.returncode, 0, second.stderr.decode(errors='replace'))
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stderr, b'')
        self.assertEqual(second.stderr, b'')
        self.assertEqual(json.loads(first.stdout), self.compare())
        self.assertEqual(files_snapshot(self.root), before)

    def test_cli_rejects_missing_invalid_and_incomplete_cycle_arguments(self):
        self.cycle()
        inc.update(self.root, transport=QueueTransport(response([fixture()]), OSError('offline')))
        base = [sys.executable, str(Path(inc.__file__).resolve()), 'compare', str(self.root)]
        for args in [[], ['--before', '1'], ['--before', '0', '--after', '2'],
                     ['--before', '2', '--after', '1'], ['--before', 'one', '--after', '2'],
                     ['--before', '1', '--after', '2'], ['--before', '1', '--after', '99']]:
            with self.subTest(args=args):
                result = subprocess.run(base + args, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b'')
                self.assertTrue(result.stderr)

    def test_cli_uses_utf8_even_with_ascii_python_stdout_encoding(self):
        self.cycle()
        name = '\u6750\u6599\u7814\u7a76\u8005'
        row = fixture()
        row['archive']['metadata']['mainfile'] = r'C:\SyntheticPrivate\UNICODE_CLI_PRIVATE_MARKER\input'
        self.cycle([row], authors=[author(name=name)])
        before = files_snapshot(self.root)
        command = [sys.executable, str(Path(inc.__file__).resolve()), 'compare', str(self.root),
                   '--before', '1', '--after', '2']
        environment = dict(os.environ, PYTHONIOENCODING='ascii')
        result = subprocess.run(command, env=environment, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        self.assertEqual(result.stderr, b'')
        self.assertIn(name.encode('utf-8'), result.stdout)
        self.assertEqual(json.loads(result.stdout.decode('utf-8')), self.compare())
        self.assertNotIn(b'UNICODE_CLI_PRIVATE_MARKER', result.stdout)
        self.assertNotIn(b'UNICODE_CLI_PRIVATE_MARKER', result.stderr)
        self.assertEqual(files_snapshot(self.root), before)


if __name__ == '__main__':
    unittest.main()
