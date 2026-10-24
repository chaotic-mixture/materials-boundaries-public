"""Kapoor 2019 candidate facts and closed review gates; no runtime admission."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.integrate_material_candidates import FILES, PIN_KEYS
from scripts.prepare_formulation_packet import (
    compile_spec, record_sha256, validate_prepared_packet, write_packet,
)

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'experimental/material-batches/kapoor-phosphate-glasses-20261024'
BASELINE = ROOT / 'materials_boundaries/data'
BASE_COMMIT = '196995256836db2d8f870ac9a91f664bfdd03e7f'
SOURCE = 'kapoor_2019_calcium_aluminophosphate'
DOCUMENT_HASH = 'ca831de841ebc22e52157474e491ca2151d8e4f6d68576a75376af47203d38a0'
BASELINE_HASHES = {
    'materials': '93da1d629da8244853b3e6ad30d556137d57e3f639baffdd3c5bc34a3a1c9107',
    'reference_properties': '275671a5f1a447d0cb071de361a8a515f60da60213edd076d725dd03d305b307',
    'sources': '3828f53f5b946a4a90d1cb92630b141d496a02838a9dceb519730831c56cc8c1',
}
# Independent source transcription oracle: ICP-OES oxide mol% and density.
# The source-wide SD ceiling is deliberately absent from these per-row facts.
ROWS = (
    ('P60', ('0', '40.4', '59.6'), '2.521'),
    ('P50', ('0', '49.9', '50.1'), '2.654'),
    ('P46', ('0', '53.9', '46.1'), '2.718'),
    ('Al5', ('5.0', '40.2', '54.8'), '2.614'),
    ('Al10', ('10.0', '30.1', '59.9'), '2.585'),
    ('Al15', ('14.8', '20.0', '65.2'), '2.583'),
)


def read(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def explicit(spec, kind, record):
    spec['contexts'][kind]['test_explicit'] = {}
    return {'context': 'test_explicit', 'fields': deepcopy(record)}


class KapoorPhosphatePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = read(BATCH / 'packet-spec.json')
        cls.saved_packet = read(BATCH / 'prepared-packet.json')
        cls.baseline_bytes = {filename: (BASELINE / filename).read_bytes() for filename in FILES.values()}
        cls.baseline = {key: json.loads(cls.baseline_bytes[filename]) for key, filename in FILES.items()}
        cls.packet = compile_spec(cls.spec, BASELINE)
        cls.graph = cls.packet['catalogs']
        cls.properties = cls.graph['properties']['records']
        cls.states = cls.graph['materials']['records']
        cls.identities = cls.graph['materials']['identities']

    def test_six_labels_and_density_cells_preserve_reported_precision(self):
        self.assertEqual([state['source_designation'] for state in self.states], [row[0] for row in ROWS])
        for (label, _, density), prop in zip(ROWS, self.properties):
            with self.subTest(label=label):
                self.assertEqual(prop['id'], 'refprop_kapoor2019_' + label.lower() + '_mass_density')
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value'], {
                    'kind': 'scalar', 'value_text': density, 'number': density,
                    'unit_code': 'g/cm^3', 'unit_text': 'g/cm3',
                })
                self.assertEqual(prop['source_id'], SOURCE)

    def test_icp_oes_compositions_are_exact_analyzed_mol_percent(self):
        facts = self.spec['review']['candidate_facts']
        self.assertEqual(len(facts), 6)
        by_label = {fact['table_1_label']: fact for fact in facts}
        self.assertEqual(set(by_label), {row[0] for row in ROWS})
        by_identity = {state['identity_id']: state for state in self.states}
        by_property = {prop['id']: prop for prop in self.properties}
        for label, values, density in ROWS:
            fact = by_label[label]
            identity_id = 'mat_kapoor2019_' + label.lower()
            state = by_identity[identity_id]
            prop = by_property[state['property_ids'][0]]
            with self.subTest(label=label):
                self.assertEqual(fact['table_1_label'], label)
                self.assertEqual(fact['identity_id'], identity_id)
                self.assertEqual(fact['density_g_cm3'], density)
                self.assertEqual(fact['icp_oes_oxide_mol_percent'], dict(zip(('Al2O3', 'CaO', 'P2O5'), values)))
                self.assertEqual(fact['composition_basis'], 'analyzed_ICP_OES')
                self.assertEqual(sum(map(Decimal, values)), Decimal('100'))
                composition = state['state']['composition_or_purity']['text']
                self.assertEqual(composition, 'Analyzed ICP-OES mol%: Al2O3 {}; CaO {}; P2O5 {}.'.format(*values))
                self.assertEqual(prop['material_state_id'], state['id'])
                self.assertEqual(prop['reported_value']['number'], density)
                self.assertEqual(prop['reported_value']['value_text'], density)

    def test_one_state_and_property_per_identity_do_not_admit_materials(self):
        self.assertEqual(self.packet['report']['delta'], {
            'identities': 6, 'grades': 0, 'states': 6, 'properties': 6, 'sources': 1,
            'categories': {'metal': 0, 'inorganic': 6, 'polymer': 0, 'composite': 0, 'natural': 0},
        })
        self.assertEqual(self.packet['report']['formal_admitted_delta'], 0)
        self.assertEqual(self.graph['materials']['grades'], [])
        self.assertEqual((len(self.identities), len(self.states), len(self.properties)), (6, 6, 6))
        for (label, _, _), identity, state, prop in zip(ROWS, self.identities, self.states, self.properties):
            with self.subTest(label=label):
                self.assertEqual(identity['id'], 'mat_kapoor2019_' + label.lower())
                self.assertEqual(identity['category'], 'inorganic')
                self.assertEqual(state['id'], 'state_kapoor2019_' + label.lower() + '_as_prepared')
                self.assertEqual(state['identity_id'], identity['id'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['property_ids'], [prop['id']])
                self.assertEqual(prop['material_state_id'], state['id'])

    def test_source_wide_sd_ceiling_is_not_a_row_uncertainty_or_mean(self):
        for prop in self.properties:
            with self.subTest(property=prop['id']):
                self.assertIsNone(prop['uncertainty'])
                self.assertEqual(prop['uncertainty_status'], 'not_reported_in_inspected_source')
                self.assertIn('source-wide', prop['uncertainty_note'])
                self.assertIn('<=0.002 g/cm3', prop['uncertainty_note'])
                self.assertIn('not', prop['uncertainty_note'].casefold())
                self.assertEqual(prop['summary_statistic'], 'not_stated')
                self.assertEqual(prop['reporting_basis'], 'not_stated')

    def test_repeated_measurements_do_not_become_independent_sample_count(self):
        for prop in self.properties:
            with self.subTest(property=prop['id']):
                count = prop['sample_count']
                self.assertIsNone(count['value'])
                self.assertEqual(count['relation'], 'not_reported')
                self.assertIn('10', count['source_statement'])
                self.assertIn('independent', count['scope'].casefold())
                self.assertIn('not', count['scope'].casefold())

    def test_room_temperature_and_prepared_state_do_not_supply_unknown_conditions(self):
        for state, prop in zip(self.states, self.properties):
            with self.subTest(state=state['id']):
                state_text = json.dumps(state['state'], ensure_ascii=False).casefold()
                self.assertIn('anneal', state_text)
                self.assertIn('archimedes', prop['conditions']['test_method']['text'].casefold())
                self.assertIn('ethanol', prop['conditions']['test_method']['text'].casefold())
                temperature = prop['conditions']['temperature']
                self.assertEqual(temperature['status'], 'reported')
                self.assertEqual(temperature['text'], 'Room temperature.')
                self.assertIsNone(temperature.get('value'))
                additional = prop['conditions']['additional_conditions']
                pressure = [entry['fact'] for entry in additional if entry['name'] == 'density_pressure']
                self.assertEqual(len(pressure), 1)
                self.assertEqual(pressure[0]['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(pressure[0]['text'])
                conditioning = prop['conditions']['conditioning']
                self.assertEqual(conditioning['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(conditioning['text'])
                self.assertIn('humidity', conditioning['notes'])
                self.assertIn('hardness', conditioning['notes'])

    def test_measurement_evidence_does_not_claim_scientific_validation(self):
        for prop in self.properties:
            self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
            self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
            self.assertEqual(prop['evaluation_support'], 'catalog_only')
            self.assertFalse(prop['universal_bound'])
            self.assertFalse(prop['engineering_allowable'])
            self.assertFalse(prop['verification']['independent_scientific_review'])
            self.assertFalse(prop['verification']['raw_data_reanalysis'])

    def test_source_attribution_and_original_document_hash_are_bound(self):
        source, = self.graph['sources']['records']
        self.assertEqual(source['id'], SOURCE)
        self.assertEqual(source['doi'], '10.3389/fmats.2019.00063')
        self.assertEqual(source['license'], {'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0'})
        self.assertIn('https://creativecommons.org/licenses/by/4.0/', source['urls'])
        self.assertTrue(any('Changes:' in note for note in source['claim_notes']))
        self.assertEqual(record_sha256(source), self.spec['source_records'][0]['sha256'])
        for prop in self.properties:
            self.assertEqual(prop['source_document']['sha256'], DOCUMENT_HASH)
        self.assertFalse(any(path.suffix.casefold() in {'.pdf', '.png', '.jpg', '.xlsx'} for path in BATCH.rglob('*')))

    def test_p60_contextual_collision_stays_source_qualified_and_separate(self):
        p60 = self.identities[0]
        self.assertIn('Kapoor', p60['name'])
        self.assertNotEqual(p60['name'].strip().casefold(), 'p60')
        self.assertFalse(any(alias['text'].strip().casefold() == 'p60' for alias in p60['aliases']))
        original = next(row for row in self.baseline['materials']['identities']
                        if row['id'] == 'mat_bianchi2022_epdm_h_p60')
        self.assertEqual(original['category'], 'composite')
        self.assertNotEqual(original['id'], p60['id'])
        review = read(BATCH / 'identity-review.json')
        self.assertEqual(review['baseline_commit'], BASE_COMMIT)
        review_text = json.dumps(review, ensure_ascii=False).casefold()
        self.assertIn('bianchi', review_text)
        self.assertIn('p60', review_text)
        self.assertFalse(review['scientific_review'])
        self.assertFalse(review['scientific_replication'])
        self.assertFalse(review['global_chemical_uniqueness_established'])
        descriptors = review['immutable_inputs']
        self.assertEqual(len(descriptors), 22)
        self.assertEqual(len({entry['path'] for entry in descriptors}), 22)
        for descriptor in descriptors:
            path = ROOT / descriptor['path']
            with self.subTest(input=descriptor['path']):
                self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))
                baseline = subprocess.run(
                    ['git', 'show', BASE_COMMIT + ':' + descriptor['path']],
                    cwd=ROOT, check=True, capture_output=True, timeout=30,
                ).stdout
                self.assertEqual(len(baseline), descriptor['bytes'])
                self.assertEqual(sha256(baseline).hexdigest(), descriptor['sha256'])
                self.assertEqual(path.read_bytes(), baseline)
        self.assertEqual([row['source_designations'] for row in self.spec['identity_crosswalk']],
                         [[row[0]] for row in ROWS])

    def test_baseline_pins_and_runtime_catalog_bytes_remain_unchanged(self):
        self.assertEqual(self.spec['baseline_sha256'], BASELINE_HASHES)
        for key, filename in FILES.items():
            with self.subTest(filename=filename):
                self.assertEqual(sha256(self.baseline_bytes[filename]).hexdigest(), BASELINE_HASHES[PIN_KEYS[key]])
                self.assertEqual((BASELINE / filename).read_bytes(), self.baseline_bytes[filename])
        self.assertEqual(len(self.baseline['materials']['identities']), 1153)
        self.assertFalse(any(row['id'].startswith('mat_kapoor2019_') for row in self.baseline['materials']['identities']))

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

    def test_baseline_hash_drift_is_refused(self):
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

    def test_duplicate_source_alias_and_designation_do_not_create_materials(self):
        for mutation in ('alias', 'designation'):
            spec = deepcopy(self.spec)
            if mutation == 'alias':
                identity = deepcopy(self.identities[1])
                identity['aliases'].append({'language': 'und', 'text': '  p60  '})
                spec['formulations'][1]['identity'] = explicit(spec, 'identity', identity)
            else:
                state = deepcopy(self.states[1])
                state['source_designation'] = 'P60'
                spec['formulations'][1]['states'][0]['record'] = explicit(spec, 'state', state)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_spec(spec, BASELINE)

    def test_pending_source_identity_or_rights_never_become_handoff_ready(self):
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

    def test_forged_prepared_values_or_report_cannot_replace_exact_replay(self):
        for mutation in ('value', 'admission', 'ready'):
            packet = deepcopy(self.saved_packet)
            if mutation == 'value':
                packet['catalogs']['properties']['records'][0]['reported_value']['number'] = '2.002'
            elif mutation == 'admission':
                packet['report']['formal_admitted_delta'] = 6
            else:
                packet['report']['handoff_ready'] = not packet['report']['handoff_ready']
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'differs from exact replay'):
                validate_prepared_packet(packet, BASELINE)


if __name__ == '__main__':
    unittest.main()
