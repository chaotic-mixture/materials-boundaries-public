"""Explicit candidate-only source oracles and fail-closed preparation gates.

Run explicitly with unittest discovery in this directory. It is intentionally
outside root discovery; no frozen core or replay inventory is expanded.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.integrate_material_candidates import FILES, PIN_KEYS
from scripts.prepare_formulation_packet import (
    compile_spec, record_sha256, validate_prepared_packet, write_packet,
)

BATCH = ROOT / 'experimental/material-batches/czlonka-curaua-20261025'
BASELINE = ROOT / 'materials_boundaries/data'
BASE_COMMIT = 'ee8c2cd3d410db10449951fa069e746804d1c937'
SOURCE = 'czlonka_2021_curaua_rpuf'
DOI = '10.3390/ijms222011203'
DOCUMENT_HASH = '321d2018f69229320a9a3bfc45686b69a486ff799e1c1414341271ac965f5d17'
XML_HASH = '571bca76ff07f59a4b258697855e00284cc3cb034ef6747709f8f9a9a5c8c0c3'
AUTHORS = [
    'Sylwia Cz\u0142onka', 'Eduardo Fischer Kerche', 'Roberta Motta Neves',
    'Anna Str\u0105kowska', 'Krzysztof Strzelec',
]
BASELINE_HASHES = {
    'materials': '8ad95e381232906bce1c0e2df777ed7856f2ad27e25200913fc3ad50482e5293',
    'reference_properties': '32327221035bd9cc439a2107b4c857629f69276ace7d54df21ce3013720d7c8a',
    'sources': '360d0fc46605805173773ae30a01efcd5ba08cc262b140460a6b39c3b9434bd1',
}
# Independent Table 2 transcription, not obtained from generated packet values.
# Superscripts are called coefficient of variance; no unit is stated there.
ROWS = (
    ('cf0p1', 'CF 0.1', '0.1', '38.4', '0.4', 'C'),
    ('cf0p5', 'CF 0.5', '0.5', '37.9', '0.6', 'B'),
    ('cf1', 'CF 1', '1', '37.6', '0.4', 'A'),
)


def read(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def explicit(spec, kind, record):
    spec['contexts'][kind]['test_explicit'] = {}
    return {'context': 'test_explicit', 'fields': deepcopy(record)}


def git_bytes(path):
    return subprocess.run(
        ['git', 'show', BASE_COMMIT + ':' + path], cwd=ROOT,
        check=True, capture_output=True, timeout=30,
    ).stdout


class CurauaCandidatePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = read(BATCH / 'packet-spec.json')
        cls.saved_packet = read(BATCH / 'prepared-packet.json')
        cls.baseline_bytes = {filename: (BASELINE / filename).read_bytes()
                              for filename in FILES.values()}
        cls.baseline_materials = read(BASELINE / FILES['materials'])
        cls.packet = compile_spec(cls.spec, BASELINE)
        cls.graph = cls.packet['catalogs']
        cls.properties = cls.graph['properties']['records']
        cls.states = cls.graph['materials']['records']
        cls.identities = cls.graph['materials']['identities']

    def test_exact_measured_density_cells_and_source_labels(self):
        self.assertEqual([state['source_designation'] for state in self.states],
                         [row[1] for row in ROWS])
        for (suffix, label, _, density, _, _), prop in zip(ROWS, self.properties):
            with self.subTest(label=label):
                self.assertEqual(prop['id'], 'refprop_czlonka2021_curaua_' + suffix + '_apparent_density')
                self.assertEqual(prop['source_id'], SOURCE)
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value']['kind'], 'scalar')
                self.assertEqual(prop['reported_value']['number'], density)
                self.assertEqual(prop['reported_value']['value_text'], density)
                self.assertEqual(prop['reported_value']['unit_code'], 'kg/m^3')
                self.assertIn('Apparent Density', prop['source_property_label'])
                self.assertNotIn(prop['reported_value']['number'], ('38.1', '485', '470', '450'))

    def test_three_formulations_are_not_specimens_or_processing_states(self):
        self.assertEqual(self.packet['report']['delta'], {
            'identities': 3, 'grades': 0, 'states': 3, 'properties': 3, 'sources': 1,
            'categories': {'metal': 0, 'inorganic': 0, 'polymer': 0, 'composite': 3, 'natural': 0},
        })
        self.assertEqual((len(self.identities), len(self.states), len(self.properties)), (3, 3, 3))
        self.assertEqual(self.graph['materials']['grades'], [])
        self.assertEqual(self.packet['report']['formal_admitted_delta'], 0)
        self.assertEqual(self.spec['review']['formal_admitted_delta'], 0)
        self.assertNotIn('Neat RPUF', [state['source_designation'] for state in self.states])
        for (suffix, label, _, _, _, _), identity, state, prop in zip(
                ROWS, self.identities, self.states, self.properties):
            with self.subTest(label=label):
                self.assertEqual(identity['id'], 'mat_czlonka2021_curaua_' + suffix)
                self.assertEqual(identity['category'], 'composite')
                self.assertIn('2021', identity['name'])
                self.assertEqual(state['id'], 'state_czlonka2021_curaua_' + suffix + '_free_rise')
                self.assertEqual(state['identity_id'], identity['id'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['property_ids'], [prop['id']])
                self.assertEqual(prop['material_state_id'], state['id'])

    def test_nominal_composition_and_selected_facts_are_source_qualified(self):
        facts = self.spec['review']['candidate_facts']
        self.assertEqual(len(facts), 3)
        self.assertEqual(facts, read(BATCH / 'source-review.json')['selected_facts'])
        for fact, (suffix, label, loading, density, coefficient, letter), identity, state in zip(
                facts, ROWS, self.identities, self.states):
            with self.subTest(label=label):
                self.assertEqual(fact['identity_id'], 'mat_czlonka2021_curaua_' + suffix)
                self.assertEqual(fact['table_2_label'], label)
                self.assertEqual(fact['nominal_curaua_wt_percent'], loading)
                self.assertEqual(fact['composition_basis'],
                                 'source_reported_nominal_loading_relative_to_total_rpuf_mass')
                self.assertEqual(fact['density_kg_m3'], density)
                self.assertEqual(fact['selected_column'], 'Apparent Density')
                self.assertEqual(fact['table_coefficient_of_variance_literal'], coefficient)
                self.assertEqual(fact['statistical_group_letter'], letter)
                self.assertIsNone(fact['coefficient_unit'])
                self.assertIsNone(fact['individual_standard_deviation'])
                self.assertEqual(fact['density_samples_per_group'], 10)
                self.assertIsNone(fact['independent_specimen_count'])
                composition = state['state']['composition_or_purity']
                self.assertEqual(composition['status'], 'reported')
                self.assertIn(loading + ' wt%', composition['text'])
                self.assertIn('nominal', composition['text'].casefold())
                self.assertIn('total', (composition['text'] + composition['notes']).casefold())
                self.assertIn('final', composition['notes'].casefold())
                self.assertIn('nominal', identity['identity_scope'].casefold())
                reinforcement = state['state']['reinforcement']
                self.assertEqual(reinforcement['status'], 'reported')
                self.assertIn('bleached', reinforcement['text'].casefold())

    def test_means_density_basis_method_and_ten_samples_are_preserved(self):
        for prop in self.properties:
            with self.subTest(property=prop['id']):
                self.assertEqual(prop['density_basis'], 'apparent')
                self.assertEqual(prop['summary_statistic'], 'reported_mean')
                self.assertEqual(prop['reporting_basis'], 'reported_summary')
                self.assertEqual(prop['sample_count']['value'], 10)
                self.assertEqual(prop['sample_count']['relation'], 'exact')
                standard = prop['conditions']['test_standard']
                self.assertEqual(standard['status'], 'reported')
                self.assertIn('ISO 845', standard['text'])
                method = prop['conditions']['test_method']
                self.assertEqual(method['status'], 'reported')
                self.assertIn('mass', method['text'].casefold())
                self.assertIn('volume', method['text'].casefold())
                self.assertEqual(prop['conditions']['direction']['status'], 'not_applicable')
                self.assertEqual(prop['conditions']['loading_rate']['status'], 'not_applicable')

    def test_variance_superscripts_are_not_standard_deviations(self):
        for (_, label, _, _, coefficient, letter), prop in zip(ROWS, self.properties):
            with self.subTest(label=label):
                self.assertIsNone(prop['uncertainty'])
                self.assertNotEqual(prop['uncertainty_status'], 'reported_standard_deviation')
                note = prop['uncertainty_note']
                self.assertIn(coefficient, note)
                self.assertIn('coefficient of variance', note.casefold())
                self.assertIn('unit', note.casefold())
                scope = json.dumps([prop['scope_note'], prop['source_discrepancies']], ensure_ascii=False)
                self.assertIn('never interpreted as percent, SD, or zero uncertainty', scope)
                self.assertIn(letter, scope)
                self.assertIn('statistical', scope.casefold())

    def test_density_unknown_conditions_and_curing_age_conflict_are_explicit(self):
        for state, prop in zip(self.states, self.properties):
            with self.subTest(property=prop['id']):
                for name in ('temperature', 'conditioning'):
                    fact = prop['conditions'][name]
                    self.assertEqual(fact['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(fact['text'])
                    self.assertIsNone(fact.get('value'))
                self.assertIn('humidity', prop['conditions']['conditioning']['notes'].casefold())
                additional = {entry['name']: entry['fact']
                              for entry in prop['conditions']['additional_conditions']}
                pressure = additional['density_pressure']
                self.assertEqual(pressure['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(pressure['text'])
                discrepancies = json.dumps(prop['source_discrepancies'], ensure_ascii=False).casefold()
                self.assertIn('24', discrepancies)
                self.assertIn('7', discrepancies)
                self.assertIn('age', discrepancies)
                self.assertIn('density', discrepancies)
                state_text = json.dumps(state['state'], ensure_ascii=False).casefold()
                self.assertIn('24', state_text)
                self.assertIn('free', state_text)
                self.assertIn('cut', state_text)

    def test_source_authors_license_and_primary_bytes_are_bound(self):
        source, = self.graph['sources']['records']
        self.assertEqual(source['id'], SOURCE)
        self.assertEqual(source['doi'], DOI)
        for representation in (
                source, self.spec['source_records'][0]['record'],
                self.saved_packet['input']['source_records'][0]['record'],
                self.saved_packet['catalogs']['sources']['records'][0]):
            self.assertEqual(representation['authors'], AUTHORS)
            self.assertNotIn('Xiao Hu', representation['authors'])
            self.assertNotIn('Antonella Piozzi', representation['authors'])
        self.assertEqual(source['license'], {
            'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0',
        })
        self.assertIn('https://creativecommons.org/licenses/by/4.0/', source['urls'])
        self.assertTrue(any('Changes:' in note for note in source['claim_notes']))
        self.assertEqual(record_sha256(source), self.spec['source_records'][0]['sha256'])
        review = read(BATCH / 'source-review.json')
        self.assertEqual(review['authorship']['author_names'], AUTHORS)
        self.assertEqual(review['document']['sha256'], DOCUMENT_HASH)
        self.assertEqual(review['document']['bytes'], 3836264)
        self.assertEqual(review['archive']['sha256'], XML_HASH)
        self.assertEqual(review['archive']['bytes'], 138976)
        self.assertFalse(review['document']['source_asset_redistributed'])
        self.assertFalse(review['archive']['source_asset_redistributed'])
        for prop in self.properties:
            self.assertEqual(prop['source_document']['sha256'], DOCUMENT_HASH)
            self.assertEqual(prop['source_document']['url'],
                             'https://mdpi-res.com/d_attachment/ijms/ijms-22-11203/article_deploy/ijms-22-11203.pdf')
        self.assertFalse(any(path.suffix.casefold() in {'.pdf', '.png', '.jpg', '.xlsx', '.xml'}
                             for path in BATCH.rglob('*')))

    def test_measurement_and_preparation_do_not_grant_scientific_approval(self):
        for prop in self.properties:
            self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
            self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
            self.assertEqual(prop['evaluation_support'], 'catalog_only')
            self.assertFalse(prop['universal_bound'])
            self.assertFalse(prop['engineering_allowable'])
            self.assertFalse(prop['verification']['independent_scientific_review'])
            self.assertFalse(prop['verification']['raw_data_reanalysis'])
        self.assertFalse(self.spec['review']['verification']['independent_scientific_review'])
        self.assertEqual(self.spec['review']['formal_admitted_delta'], 0)

    def test_finite_identity_review_replays_twenty_two_original_inputs(self):
        review = read(BATCH / 'identity-review.json')
        self.assertEqual(review['baseline_commit'], BASE_COMMIT)
        self.assertFalse(review['scientific_review'])
        self.assertFalse(review['scientific_replication'])
        self.assertFalse(review['global_chemical_uniqueness_established'])
        self.assertEqual(review['formal_admitted_delta'], 0)
        descriptors = review['immutable_inputs']
        self.assertEqual(len(descriptors), 22)
        self.assertEqual(len({entry['path'] for entry in descriptors}), 22)
        for descriptor in descriptors:
            path = ROOT / descriptor['path']
            with self.subTest(input=descriptor['path']):
                self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))
                frozen = git_bytes(descriptor['path'])
                self.assertEqual(len(frozen), descriptor['bytes'])
                self.assertEqual(sha256(frozen).hexdigest(), descriptor['sha256'])
                self.assertEqual(path.read_bytes(), frozen)
        helper_spec = importlib.util.spec_from_file_location('curaua_identity_review', BATCH / 'build_identity_review.py')
        helper = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(helper)
        self.assertEqual(encoded(helper.build_review()), (BATCH / 'identity-review.json').read_bytes())

    def test_baseline_counts_and_all_preexisting_files_remain_unchanged(self):
        self.assertEqual(self.spec['baseline_sha256'], BASELINE_HASHES)
        for key, filename in FILES.items():
            with self.subTest(filename=filename):
                self.assertEqual(sha256(self.baseline_bytes[filename]).hexdigest(), BASELINE_HASHES[PIN_KEYS[key]])
                self.assertEqual(self.baseline_bytes[filename], git_bytes('materials_boundaries/data/' + filename))
        self.assertEqual(len(self.baseline_materials['identities']), 1161)
        self.assertEqual(Counter(row['category'] for row in self.baseline_materials['identities']),
                         {'natural': 1010, 'metal': 32, 'inorganic': 59, 'polymer': 30, 'composite': 30})
        self.assertFalse(any(row['id'].startswith('mat_czlonka2021_') for row in self.baseline_materials['identities']))
        self.assertEqual(self.packet['report']['before']['identities'], 1161)
        self.assertEqual(self.packet['report']['after']['identities'], 1164)
        changed_old = subprocess.run(
            ['git', 'diff', BASE_COMMIT, '--name-only', '--diff-filter=CDMRTUXB'],
            cwd=ROOT, check=True, capture_output=True, timeout=30,
        ).stdout
        self.assertEqual(changed_old, b'')
        manifest = read(ROOT / 'tests/core_partition/manifest.json')
        self.assertEqual((manifest['module_count'], manifest['test_count']), (147, 1887))
        self.assertEqual(manifest['root_inventory_sha256'],
                         '19a735217c29533c1137a6cfd95b2b58cf88e8cf649848e41012c510434446f7')
        self.assertFalse((Path(__file__).parent / '__init__.py').exists())

    def test_preparation_receipt_binds_packet_and_every_declared_input(self):
        receipt = read(BATCH / 'preparation-receipt.json')
        self.assertEqual(receipt['baseline_commit'], BASE_COMMIT)
        raw = (BATCH / 'prepared-packet.json').read_bytes()
        self.assertEqual(receipt['prepared_packet_sha256'], sha256(raw).hexdigest())
        self.assertEqual(receipt['prepared_packet_bytes'], len(raw))
        self.assertEqual(receipt['spec_canonical_sha256'], record_sha256(self.spec))
        self.assertTrue(receipt['output_bytes_and_mtime_unchanged'])
        self.assertTrue(receipt['inputs_unchanged'])
        self.assertTrue(receipt['runtime_catalogs_unchanged'])
        self.assertEqual(receipt['report'], self.saved_packet['report'])
        required = {str((BATCH / name).relative_to(ROOT).as_posix()) for name in (
            'packet-spec.json', 'source-review.json', 'identity-review.json', 'build_identity_review.py')}
        required.update('materials_boundaries/data/' + filename for filename in FILES.values())
        self.assertTrue(required.issubset(receipt['inputs']))
        for path, descriptor in receipt['inputs'].items():
            resolved = (ROOT / path).resolve()
            with self.subTest(input=path):
                self.assertTrue(resolved.is_relative_to(ROOT.resolve()))
                data = resolved.read_bytes()
                self.assertEqual(descriptor['bytes'], len(data))
                self.assertEqual(descriptor['sha256'], sha256(data).hexdigest())

    def test_replay_and_idempotent_write_preserve_bytes_and_mtime(self):
        self.assertEqual(self.packet, self.saved_packet)
        self.assertEqual(self.spec, self.packet['input'])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'candidate.json'
            first, created = write_packet(BASELINE, BATCH / 'packet-spec.json', output)
            self.assertTrue(created)
            before = output.read_bytes(), output.stat().st_mtime_ns
            again, created = write_packet(BASELINE, BATCH / 'packet-spec.json', output)
            self.assertFalse(created)
            self.assertEqual(first, again)
            self.assertEqual(before, (output.read_bytes(), output.stat().st_mtime_ns))
            self.assertEqual(output.read_bytes(), (BATCH / 'prepared-packet.json').read_bytes())
            output.write_bytes(b'sentinel\n')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                write_packet(BASELINE, BATCH / 'packet-spec.json', output)
            self.assertEqual(output.read_bytes(), b'sentinel\n')

    def test_baseline_or_source_record_hash_drift_is_refused(self):
        spec = deepcopy(self.spec)
        spec['baseline_sha256']['materials'] = '0' * 64
        with self.assertRaises(ValueError):
            compile_spec(spec, BASELINE)
        spec = deepcopy(self.spec)
        spec['source_records'][0]['record']['title'] += ' unreviewed edit'
        with self.assertRaisesRegex(ValueError, 'source record hash mismatch'):
            compile_spec(spec, BASELINE)

    def test_missing_property_cannot_write_partial_candidate(self):
        spec = deepcopy(self.spec)
        spec['formulations'][0]['states'][0]['properties'] = []
        with tempfile.TemporaryDirectory() as directory:
            path, output = Path(directory) / 'spec.json', Path(directory) / 'packet.json'
            path.write_bytes(encoded(spec))
            with self.assertRaises(ValueError):
                write_packet(BASELINE, path, output)
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_wrong_density_unit_is_rejected(self):
        spec = deepcopy(self.spec)
        prop = deepcopy(self.properties[0])
        prop['reported_value'].update(unit_code='MPa', unit_text='MPa')
        spec['formulations'][0]['states'][0]['properties'][0] = explicit(spec, 'property', prop)
        with self.assertRaises(ValueError):
            compile_spec(spec, BASELINE)

    def test_duplicate_alias_designation_and_identity_do_not_create_growth(self):
        for mutation in ('alias', 'designation', 'identity'):
            spec = deepcopy(self.spec)
            if mutation == 'alias':
                identity = deepcopy(self.identities[1])
                identity['aliases'].append({'language': 'und', 'text': '  CF 0.1  '})
                spec['formulations'][1]['identity'] = explicit(spec, 'identity', identity)
            elif mutation == 'designation':
                state = deepcopy(self.states[1])
                state['source_designation'] = 'CF 0.1'
                spec['formulations'][1]['states'][0]['record'] = explicit(spec, 'state', state)
            else:
                spec['formulations'].append(deepcopy(spec['formulations'][0]))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_spec(spec, BASELINE)

    def test_pending_source_identity_or_license_blocks_handoff(self):
        for gate in ('source', 'identity', 'rights'):
            spec = deepcopy(self.spec)
            if gate == 'source':
                spec['review']['source_reviews'][0]['status'] = 'pending'
            elif gate == 'identity':
                spec['identity_crosswalk'][0]['disposition'] = 'pending'
            else:
                descriptor = spec['source_records'][0]
                descriptor['record']['license'] = {'status': 'unverified', 'identifier': None}
                descriptor['sha256'] = record_sha256(descriptor['record'])
            with self.subTest(gate=gate):
                packet = compile_spec(spec, BASELINE)
                self.assertFalse(packet['report']['handoff_ready'])
                self.assertTrue(packet['report']['pending_gates'])
                self.assertEqual(packet['report']['formal_admitted_delta'], 0)

    def test_forged_cells_count_or_admission_cannot_replace_exact_replay(self):
        for mutation in ('value', 'coefficient_as_value', 'count', 'admission', 'ready'):
            packet = deepcopy(self.saved_packet)
            if mutation in ('value', 'coefficient_as_value'):
                value = '38.1' if mutation == 'value' else '0.4'
                packet['catalogs']['properties']['records'][0]['reported_value'].update(number=value, value_text=value)
            elif mutation == 'count':
                packet['report']['delta']['identities'] = 30
            elif mutation == 'admission':
                packet['report']['formal_admitted_delta'] = 3
            else:
                packet['report']['handoff_ready'] = not packet['report']['handoff_ready']
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'differs from exact replay'):
                validate_prepared_packet(packet, BASELINE)


if __name__ == '__main__':
    unittest.main()
