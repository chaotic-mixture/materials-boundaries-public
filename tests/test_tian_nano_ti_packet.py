"""Tian 2023 candidate transcription, unknowns and closed review gates."""
from collections import Counter
from copy import deepcopy
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
BATCH = ROOT / 'experimental/material-batches/tian-nano-ti-composites-20261024'
BASELINE = ROOT / 'materials_boundaries/data'
BASE_COMMIT = '5a9a85c573f590d206cddb4cb7c085f334a0fbc0'
SOURCE = 'tian_2023_nano_ti_az31'
DOCUMENT_HASH = '8df98d0b465e5bef857d9eaa0ff0969e0c22b4f35aa5a7c64e6e59150b08afad'
XML_HASH = '80b9020e8a4878adf439977478551214b1130982331d81a17fc85a072f2ac598'
PDF_MD5 = 'aea07249f6eb98a284067ea7a466012a'
AUTHORS = [
    'Wei Tian', 'Pengfei Gao', 'Shengli Han', 'Xiaohong Chen',
    'Fuwei Zhang', 'Yuhui Zhang', 'Tiegang Luo', 'Kaihong Zheng',
]
BASELINE_HASHES = {
    'materials': 'ec6a73ea89a267a55eb77d8b189f27deee75b5aaabf24941a9b4da5e2ac85c33',
    'reference_properties': '29c826fc9a1bd67d0012384ee956740ab91fd2a87be7ab33aa7cc548c1be3e1f',
    'sources': 'a02ac67aadae86e118065e97cae95013b6d7edd85516e3fcf66396deefdd58c2',
}
# Independent selected-cell oracle. Table 2 omits '%' in the second label;
# Sections 2.1 and 2.2 establish the nominal loading, not final composition.
ROWS = (
    ('0p5wt', '0.5 wt% Ti', '0.5', '1.7425'),
    ('1wt', '1 wt Ti', '1', '1.7442'),
)


def read(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def explicit(spec, kind, record):
    spec['contexts'][kind]['test_explicit'] = {}
    return {'context': 'test_explicit', 'fields': deepcopy(record)}


class TianNanoTiPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = read(BATCH / 'packet-spec.json')
        cls.saved_packet = read(BATCH / 'prepared-packet.json')
        cls.baseline_materials = read(BASELINE / FILES['materials'])
        cls.packet = compile_spec(cls.spec, BASELINE)
        cls.graph = cls.packet['catalogs']
        cls.properties = cls.graph['properties']['records']
        cls.states = cls.graph['materials']['records']
        cls.identities = cls.graph['materials']['identities']

    def test_actual_density_cells_and_literal_source_labels(self):
        self.assertEqual([state['source_designation'] for state in self.states],
                         [row[1] for row in ROWS])
        self.assertEqual(len(self.properties), 2)
        for (suffix, label, _, density), prop in zip(ROWS, self.properties):
            with self.subTest(label=label):
                self.assertEqual(prop['id'], 'refprop_tian2023_az31_ti_' + suffix + '_mass_density')
                self.assertEqual(prop['source_id'], SOURCE)
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value'], {
                    'kind': 'scalar', 'value_text': density, 'number': density,
                    'unit_code': 'g/cm^3', 'unit_text': 'g/cm3',
                })
                self.assertIn('Actual Density', prop['source_property_label'])
                self.assertNotIn(prop['reported_value']['number'], ('1.7857', '1.7808', '1.7214'))

    def test_two_composite_identities_have_one_extruded_state_and_property_each(self):
        self.assertEqual(self.packet['report']['delta'], {
            'identities': 2, 'grades': 0, 'states': 2, 'properties': 2, 'sources': 1,
            'categories': {'metal': 0, 'inorganic': 0, 'polymer': 0, 'composite': 2, 'natural': 0},
        })
        self.assertEqual((len(self.identities), len(self.states), len(self.properties)), (2, 2, 2))
        self.assertEqual(self.graph['materials']['grades'], [])
        self.assertEqual(self.packet['report']['formal_admitted_delta'], 0)
        self.assertEqual(self.spec['review']['formal_admitted_delta'], 0)
        for (suffix, label, _, _), identity, state, prop in zip(
                ROWS, self.identities, self.states, self.properties):
            with self.subTest(label=label):
                self.assertEqual(identity['id'], 'mat_tian2023_az31_ti_' + suffix)
                self.assertEqual(identity['category'], 'composite')
                self.assertIn('Tian', identity['name'])
                self.assertEqual(state['id'], 'state_tian2023_az31_ti_' + suffix + '_as_extruded')
                self.assertEqual(state['identity_id'], identity['id'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['property_ids'], [prop['id']])
                self.assertEqual(prop['material_state_id'], state['id'])
                self.assertIn('extrud', json.dumps(state['state']).casefold())

    def test_nominal_loadings_are_source_qualified_and_not_final_composition(self):
        facts = self.spec['review']['candidate_facts']
        self.assertEqual(len(facts), 2)
        self.assertEqual(facts, read(BATCH / 'source-review.json')['selected_facts'])
        for fact, (suffix, label, loading, density) in zip(facts, ROWS):
            self.assertEqual(fact['identity_id'], 'mat_tian2023_az31_ti_' + suffix)
            self.assertEqual(fact['table_2_label'], label)
            self.assertEqual(fact['nominal_ti_wt_percent'], loading)
            self.assertEqual(fact['composition_basis'], 'source_reported_nominal_loading')
            self.assertEqual(fact['density_g_cm3'], density)
            self.assertEqual(fact['selected_column'], 'Actual Density')
            self.assertEqual(fact['state'], 'as-extruded')
            self.assertIsNone(fact['individual_standard_deviation'])
            self.assertIsNone(fact['independent_specimen_count'])
        for (suffix, _, loading, _), identity, state in zip(ROWS, self.identities, self.states):
            with self.subTest(formulation=suffix):
                composition = state['state']['composition_or_purity']
                self.assertEqual(composition['status'], 'reported')
                self.assertIn(loading + ' wt%', composition['text'])
                self.assertIn('nominal', composition['text'].casefold())
                self.assertIn('not', composition['notes'].casefold())
                self.assertIn('final', composition['notes'].casefold())
                self.assertIn('nominal', identity['identity_scope'].casefold())
                self.assertFalse(any(alias['text'].strip().casefold() in {'az31', 'ti', 'mg-3al-1zn'}
                                     for alias in identity['aliases']))
                self.assertEqual(state['state']['reinforcement']['status'], 'reported')
                self.assertIn('Ti', state['state']['reinforcement']['text'])

    def test_missing_percent_symbol_is_preserved_with_method_qualification(self):
        second = self.states[1]
        self.assertEqual(second['source_designation'], '1 wt Ti')
        self.assertEqual(self.spec['identity_crosswalk'][1]['source_designations'], ['1 wt Ti'])
        self.assertIn('1 wt%', second['state']['composition_or_purity']['text'])
        discrepancy_text = json.dumps(self.properties[1]['source_discrepancies'], ensure_ascii=False)
        self.assertIn('1 wt Ti', discrepancy_text)
        self.assertIn('1 wt%', discrepancy_text)
        self.assertIn('2.2', discrepancy_text)

    def test_density_unknowns_do_not_inherit_tensile_temperature_or_count(self):
        for prop in self.properties:
            with self.subTest(property=prop['id']):
                temperature = prop['conditions']['temperature']
                self.assertEqual(temperature['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(temperature['text'])
                self.assertIsNone(temperature.get('value'))
                self.assertIn('tensile', temperature['notes'].casefold())
                conditioning = prop['conditions']['conditioning']
                self.assertEqual(conditioning['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(conditioning['text'])
                self.assertIn('humidity', conditioning['notes'].casefold())
                count = prop['sample_count']
                self.assertIsNone(count['value'])
                self.assertEqual(count['relation'], 'not_reported')
                self.assertEqual(count['source_statement'],
                                 'Density specimen count is not stated in the selected source.')
                self.assertIn('tensile', count['scope'].casefold())
                additional = {entry['name']: entry['fact'] for entry in prop['conditions']['additional_conditions']}
                for key in ('density_pressure', 'measurement_repetitions'):
                    self.assertEqual(additional[key]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(additional[key]['text'])

    def test_density_statistics_basis_and_porosity_remain_unknown(self):
        for state, prop in zip(self.states, self.properties):
            with self.subTest(property=prop['id']):
                self.assertIsNone(prop['uncertainty'])
                self.assertEqual(prop['uncertainty_status'], 'not_reported_in_inspected_source')
                self.assertEqual(prop['summary_statistic'], 'not_stated')
                self.assertEqual(prop['reporting_basis'], 'not_stated')
                self.assertEqual(prop['density_basis'], 'not_stated')
                self.assertEqual(state['state']['porosity']['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(state['state']['porosity']['text'])
                method = prop['conditions']['test_method']
                self.assertEqual(method['status'], 'reported')
                self.assertIn('digital densimeter', method['text'].casefold())
                self.assertEqual(prop['conditions']['test_standard']['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(prop['conditions']['test_standard']['text'])

    def test_measurement_and_review_are_not_scientific_approval(self):
        for prop in self.properties:
            self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
            self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
            self.assertEqual(prop['evaluation_support'], 'catalog_only')
            self.assertFalse(prop['universal_bound'])
            self.assertFalse(prop['engineering_allowable'])
            self.assertFalse(prop['verification']['independent_scientific_review'])
            self.assertFalse(prop['verification']['raw_data_reanalysis'])
        self.assertFalse(self.spec['review']['verification']['independent_scientific_review'])

    def test_source_license_attribution_and_selected_document_are_bound(self):
        source, = self.graph['sources']['records']
        self.assertEqual(source['id'], SOURCE)
        self.assertEqual(source['doi'], '10.3390/ma16062407')
        # The archive lists Bolv Xiao as contrib-type="editor", not author.
        # This independent eight-name oracle prevents hash-consistent misattribution.
        self.assertEqual(source['authors'], AUTHORS)
        self.assertEqual(self.spec['source_records'][0]['record']['authors'], AUTHORS)
        self.assertEqual(self.saved_packet['input']['source_records'][0]['record']['authors'], AUTHORS)
        self.assertEqual(self.saved_packet['catalogs']['sources']['records'][0]['authors'], AUTHORS)
        review = read(BATCH / 'source-review.json')
        self.assertEqual(review['authorship']['author_names'], AUTHORS)
        self.assertEqual(review['authorship']['non_author_contributors'], [
            {'name': 'Bolv Xiao', 'contrib_type': 'editor', 'role': 'Academic Editor'},
        ])
        self.assertEqual(review['rights']['attribution'], ', '.join(AUTHORS)
                         + ' (2023), Materials 16(6), 2407. Copyright 2023 by the authors.')
        self.assertIn('Tiegang Luo and Kaihong Zheng (2023)',
                      (BATCH / 'README.md').read_text(encoding='utf-8'))
        self.assertEqual(source['license'], {
            'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0',
        })
        self.assertIn('https://creativecommons.org/licenses/by/4.0/', source['urls'])
        self.assertTrue(any('Changes:' in note for note in source['claim_notes']))
        self.assertEqual(record_sha256(source), self.spec['source_records'][0]['sha256'])
        for prop in self.properties:
            self.assertEqual(prop['source_document']['sha256'], DOCUMENT_HASH)
            self.assertIn('pdfs.semanticscholar.org', prop['source_document']['url'])
        self.assertFalse(any(path.suffix.casefold() in {'.pdf', '.png', '.jpg', '.xlsx', '.xml'}
                             for path in BATCH.rglob('*')))

    def test_archive_manifest_corroboration_does_not_claim_primary_pdf_bytes(self):
        review = read(BATCH / 'source-review.json')
        self.assertEqual(review['doi'], '10.3390/ma16062407')
        archive, document = review['archive'], review['document']
        self.assertEqual(archive['url'],
                         'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10054318/fullTextXML')
        self.assertEqual(archive['version'], 'PMC10054318.1')
        self.assertEqual(archive['sha256'], XML_HASH)
        self.assertEqual(archive['bytes'], 143168)
        self.assertEqual(archive['pdf_manifest'], {
            'filename': 'materials-16-02407.pdf', 'bytes': 5497847, 'md5': PDF_MD5,
        })
        self.assertTrue(archive['mirror_matches_manifest_size_and_md5'])
        self.assertEqual(document['sha256'], DOCUMENT_HASH)
        self.assertEqual(document['bytes'], archive['pdf_manifest']['bytes'])
        self.assertEqual(document['md5'], archive['pdf_manifest']['md5'])
        self.assertEqual(document['host_role'], 'third_party_mirror_of_publisher_formatted_pdf')
        self.assertFalse(document['direct_primary_host_pdf_download_verified'])
        self.assertFalse(document['primary_host_pdf_sha256_equivalence_verified'])
        self.assertFalse(document['source_asset_redistributed'])
        self.assertFalse(archive['xml_source_asset_redistributed'])

    def test_comparator_exclusion_and_finite_identity_inputs(self):
        original = next(row for row in self.baseline_materials['identities']
                        if row['id'] == 'mat_chen2023_az31')
        self.assertEqual(original['category'], 'metal')
        self.assertNotIn(original['id'], {identity['id'] for identity in self.identities})
        self.assertNotIn('0 wt% Ti', {state['source_designation'] for state in self.states})
        review = read(BATCH / 'identity-review.json')
        self.assertEqual(review['baseline_commit'], BASE_COMMIT)
        self.assertFalse(review['scientific_review'])
        self.assertFalse(review['scientific_replication'])
        self.assertFalse(review['global_chemical_uniqueness_established'])
        self.assertIn('mat_chen2023_az31', json.dumps(review))
        descriptors = review['immutable_inputs']
        self.assertEqual(len(descriptors), 22)
        self.assertEqual(len({entry['path'] for entry in descriptors}), 22)
        for descriptor in descriptors:
            path = ROOT / descriptor['path']
            with self.subTest(input=descriptor['path']):
                self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))
                frozen = subprocess.run(
                    ['git', 'show', BASE_COMMIT + ':' + descriptor['path']],
                    cwd=ROOT, check=True, capture_output=True, timeout=30,
                ).stdout
                self.assertEqual(len(frozen), descriptor['bytes'])
                self.assertEqual(sha256(frozen).hexdigest(), descriptor['sha256'])
                self.assertEqual(path.read_bytes(), frozen)

    def test_baseline_pins_and_actual_catalog_counts_are_unchanged(self):
        self.assertEqual(self.spec['baseline_sha256'], BASELINE_HASHES)
        for key, filename in FILES.items():
            with self.subTest(filename=filename):
                self.assertEqual(sha256((BASELINE / filename).read_bytes()).hexdigest(),
                                 BASELINE_HASHES[PIN_KEYS[key]])
        self.assertEqual(len(self.baseline_materials['identities']), 1159)
        self.assertEqual(Counter(row['category'] for row in self.baseline_materials['identities']),
                         {'natural': 1010, 'metal': 32, 'inorganic': 59, 'polymer': 30, 'composite': 28})
        self.assertFalse(any(row['id'].startswith('mat_tian2023_')
                             for row in self.baseline_materials['identities']))
        self.assertEqual(self.packet['report']['before']['identities'], 1159)
        self.assertEqual(self.packet['report']['after']['identities'], 1161)
        self.assertEqual(self.packet['report']['formal_admitted_delta'], 0)

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

    def test_duplicate_alias_or_designation_does_not_create_an_identity(self):
        for mutation in ('alias', 'designation'):
            spec = deepcopy(self.spec)
            if mutation == 'alias':
                identity = deepcopy(self.identities[1])
                identity['aliases'].append({'language': 'und', 'text': '  0.5 WT% TI  '})
                spec['formulations'][1]['identity'] = explicit(spec, 'identity', identity)
            else:
                state = deepcopy(self.states[1])
                state['source_designation'] = '0.5 wt% Ti'
                spec['formulations'][1]['states'][0]['record'] = explicit(spec, 'state', state)
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

    def test_forged_values_or_admission_cannot_replace_exact_replay(self):
        for mutation in ('value', 'theoretical_column', 'admission', 'ready'):
            packet = deepcopy(self.saved_packet)
            if mutation in ('value', 'theoretical_column'):
                value = '1.7000' if mutation == 'value' else '1.7857'
                packet['catalogs']['properties']['records'][0]['reported_value'].update(
                    number=value, value_text=value)
            elif mutation == 'admission':
                packet['report']['formal_admitted_delta'] = 2
            else:
                packet['report']['handoff_ready'] = not packet['report']['handoff_ready']
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'differs from exact replay'):
                validate_prepared_packet(packet, BASELINE)


if __name__ == '__main__':
    unittest.main()
