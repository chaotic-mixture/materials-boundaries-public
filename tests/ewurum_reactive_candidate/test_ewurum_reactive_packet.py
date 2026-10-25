"""Source oracles and preparation gates for four review-only R formulations.

Run this directory explicitly. No frozen root or replay inventory is expanded.
The original 8ccd217 image is recovered through the exact Ewurum successor ledger.
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
sys.path.insert(0, str(ROOT / 'tests'))
from ewurum_reactive_history import checkpoint_catalogs, checkpoint_bytes, checkpoint_changed_paths

from scripts.integrate_material_candidates import FILES, PIN_KEYS
from scripts.prepare_formulation_packet import (
    compile_spec, record_sha256, validate_prepared_packet, write_packet,
)

BATCH = ROOT / 'experimental/material-batches/ewurum-reactive-20261025'
BASELINE = ROOT / 'materials_boundaries/data'
BASE_COMMIT = '8ccd217599fd462d13d7435bdfb02a0825e4eacd'
SOURCE = 'ewurum_mcdonald_2025_pbs_lignin'
SOURCE_HASH = '358d6486d107da45ed76c3aa7c7a448213957c7b94afc811e9ad75e294641ca0'
DOI = '10.3390/polym17020194'
PDF_URL = 'https://mdpi-res.com/d_attachment/polymers/polymers-17-00194/article_deploy/polymers-17-00194.pdf'
PDF_HASH = '766d17f0e92c7e93cd57a3a5e97dddff0cb66a84bba6bf9118fbd0796d4c2e6f'
AUTHORS = ['Nnaemeka Ewurum', 'Armando G. McDonald']
BASELINE_HASHES = {
    'materials': 'f65d332bc0a67838bbba0f936ba8134243e75123d720417fa7af873502c0976b',
    'reference_properties': '1feeaec49643cf3ee560c29f91f91eb7674a8ee769639558930dfc8b4cfbd3c2',
    'sources': 'c5eecc0e7c64d9ef4af623f0800d947cec8a7f91570633b45b053d6ecb0c75aa',
}
# Independent selected Table 6 cells and Table 1 contextual gel fractions.
# Values are source transcriptions, not derived from the prepared packet.
ROWS = (
    ('r10', 'R10', 10, '751', '40', 'b\u2032', '4.7'),
    ('r20', 'R20', 20, '716', '49', 'b\u2032', '4.3'),
    ('r30', 'R30', 30, '910', '85', 'b', '12.7'),
    ('r45', 'R45', 45, '1256', '162', 'a', '26.2'),
)
B_MODULI = {'10': '922', '20': '960', '30': '969', '45': '1206'}


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


class EwurumReactiveCandidatePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global BASELINE
        original_baseline = BASELINE
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.addClassCleanup(lambda: globals().__setitem__('BASELINE', original_baseline))
        BASELINE = Path(directory.name)
        for table, value in checkpoint_catalogs().items():
            (BASELINE / FILES[table]).write_bytes(encoded(value))
        cls.spec = read(BATCH / 'packet-spec.json')
        cls.saved_packet = read(BATCH / 'prepared-packet.json')
        cls.source_review = read(BATCH / 'source-review.json')
        cls.baseline_bytes = {name: (BASELINE / name).read_bytes() for name in FILES.values()}
        cls.baseline_materials = read(BASELINE / FILES['materials'])
        cls.baseline_source = next(
            row for row in read(BASELINE / FILES['sources'])['records'] if row['id'] == SOURCE)
        cls.packet = compile_spec(cls.spec, BASELINE)
        cls.graph = cls.packet['catalogs']
        cls.identities = cls.graph['materials']['identities']
        cls.states = cls.graph['materials']['records']
        cls.properties = cls.graph['properties']['records']

    def test_exact_original_modulus_means_sds_and_tukey_labels(self):
        self.assertEqual([state['source_designation'] for state in self.states],
                         [row[1] for row in ROWS])
        for (suffix, label, _, mean, sd, group, _), prop in zip(ROWS, self.properties):
            with self.subTest(label=label):
                self.assertEqual(prop['id'], 'refprop_ewurum2025_pbs_lignin_' + suffix + '_youngs_modulus')
                self.assertEqual(prop['quantity'], 'youngs_modulus')
                self.assertEqual(prop['quantity_dimension'], 'pressure')
                self.assertIsNone(prop['density_basis'])
                self.assertEqual(prop['source_id'], SOURCE)
                self.assertEqual(prop['reported_value'], {
                    'kind': 'scalar', 'value_text': mean, 'unit_text': 'MPa',
                    'unit_code': 'MPa', 'number': mean,
                })
                self.assertEqual(prop['summary_statistic'], 'reported_mean')
                self.assertEqual(prop['reporting_basis'], 'reported_summary')
                self.assertEqual(prop['uncertainty_status'], 'reported_standard_deviation')
                uncertainty = prop['uncertainty']
                self.assertEqual(uncertainty['type'], 'reported_standard_deviation')
                self.assertEqual((uncertainty['number'], uncertainty['value_text']), (sd, sd))
                self.assertEqual((uncertainty['unit_code'], uncertainty['unit_text']), ('MPa', 'MPa'))
                self.assertIsNone(uncertainty['coverage_factor'])
                self.assertIsNone(uncertainty['confidence_level'])
                self.assertIn(group, prop['uncertainty_note'])
                self.assertIn('Tukey', prop['uncertainty_note'])
                self.assertIn('rounded', prop['uncertainty_note'])
                self.assertNotEqual(mean, B_MODULI[suffix[1:]])

    def test_four_reactive_formulations_have_four_exact_state_property_joins(self):
        self.assertEqual(self.packet['report']['delta'], {
            'identities': 4, 'grades': 0, 'states': 4, 'properties': 4, 'sources': 0,
            'categories': {'metal': 0, 'inorganic': 0, 'polymer': 0, 'composite': 4, 'natural': 0},
        })
        self.assertEqual((len(self.identities), len(self.states), len(self.properties)), (4, 4, 4))
        self.assertEqual(self.graph['materials']['grades'], [])
        self.assertEqual(self.packet['report']['formal_admitted_delta'], 0)
        for (suffix, label, _, _, _, _, _), identity, state, prop in zip(
                ROWS, self.identities, self.states, self.properties):
            with self.subTest(label=label):
                self.assertEqual(identity['id'], 'mat_ewurum2025_pbs_lignin_' + suffix)
                self.assertEqual(identity['category'], 'composite')
                self.assertIn('2025', identity['name'])
                self.assertEqual(state['id'], 'state_ewurum2025_pbs_lignin_' + suffix + '_injection_molded')
                self.assertEqual(state['identity_id'], identity['id'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['property_ids'], [prop['id']])
                self.assertEqual(prop['material_state_id'], state['id'])
        self.assertEqual({p['quantity'] for p in self.properties}, {'youngs_modulus'})
        self.assertNotIn('R0', [s['source_designation'] for s in self.states])

    def test_nominal_loading_dcp_basis_and_contextual_gel_evidence_are_exact(self):
        facts = self.spec['review']['candidate_facts']
        self.assertEqual(facts, self.source_review['selected_facts'])
        self.assertEqual(len(facts), 4)
        for fact, (suffix, label, loading, mean, sd, group, gel), identity, state, prop in zip(
                facts, ROWS, self.identities, self.states, self.properties):
            with self.subTest(label=label):
                self.assertEqual(fact, {
                    'identity_id': identity['id'], 'state_id': state['id'], 'property_id': prop['id'],
                    'table_6_label': label, 'nominal_lignin_wt_percent': loading,
                    'loading_basis': 'total_polymer_mass',
                    'dcp_source_text': '0.25 wt.% DCP added to PBS',
                    'dcp_denominator_resolved': False,
                    'youngs_modulus_mpa': int(mean), 'standard_deviation_mpa': int(sd),
                    'tukey_group': group, 'tensile_replicates': 10, 'gel_fraction_percent': gel,
                })
                composition = state['state']['composition_or_purity']
                self.assertEqual(composition['status'], 'reported')
                self.assertIn(str(loading) + ' wt.%', composition['text'])
                self.assertIn('total polymer mass', composition['text'])
                self.assertIn('0.25 wt.% DCP added to PBS', composition['text'])
                self.assertIn('denominator', composition['notes'])
                self.assertIn('not resolved', composition['notes'])
                scope = identity['identity_scope']
                self.assertIn('DCP', scope)
                self.assertIn('reaction', scope)
                self.assertIn('B-series', scope)
                self.assertIn(gel + '%', scope)
                self.assertIn('not a certified final network', scope)
                self.assertIn('not an analyzed final', state['state']['reinforcement']['notes'])
                for scoped_text in (scope, state['source_scope'], prop['scope_note']):
                    scoped_text = scoped_text.casefold()
                    self.assertIn('hot-pressed', scoped_text)
                    self.assertIn('section 2.4', scoped_text)
                    self.assertRegex(scoped_text, r'not [^.]*tensile dog-bones')
        gel_scope = self.source_review['identity_review']['gel_fraction_scope'].casefold()
        self.assertIn('contextual identity evidence only', gel_scope)
        self.assertIn('hot-pressed', gel_scope)
        self.assertIn('section 2.4', gel_scope)
        self.assertRegex(gel_scope, r'not [^.]*tensile dog-bones')

    def test_existing_b_blends_are_preserved_and_not_renamed_as_r_candidates(self):
        by_id = {row['id']: row for row in self.baseline_materials['identities']}
        old_states = {row['source_designation']: row for row in self.baseline_materials['records']
                      if row['identity_id'].startswith('mat_ewurum2025_pbs_lignin')}
        for suffix, label, loading, _, _, _, _ in ROWS:
            with self.subTest(label=label):
                old = by_id['mat_ewurum2025_pbs_lignin' + str(loading)]
                self.assertIn('not DCP-reactive ' + label, old['identity_scope'])
                self.assertEqual(old_states['B' + str(loading)]['identity_id'], old['id'])
                self.assertNotIn('mat_ewurum2025_pbs_lignin_' + suffix, by_id)
        self.assertIn('R0', ' '.join(self.spec['review']['exclusions']))

    def test_tensile_method_replicates_and_specimen_state_are_source_qualified(self):
        for state, prop in zip(self.states, self.properties):
            with self.subTest(property=prop['id']):
                self.assertEqual(prop['sample_count']['value'], 10)
                self.assertEqual(prop['sample_count']['relation'], 'exact')
                self.assertIn('independent production-batch count is not reported', prop['sample_count']['scope'])
                standard = prop['conditions']['test_standard']
                self.assertEqual(standard['status'], 'reported')
                self.assertEqual(standard['text'],
                                 'ASTM D1708-18 (2018), source-cited edition in reference [32]')
                self.assertEqual([entry['locator'] for entry in standard['evidence']],
                                 ['PDF p.5 section 2.9 and p.15 reference [32]'])
                standard_notes = standard['notes'].casefold()
                self.assertIn('source-cited only', standard_notes)
                self.assertIn('independent standard compliance remains unverified', standard_notes)
                self.assertIn('no specimen dimensions or conditioning are inferred', standard_notes)
                self.assertIn('1 mm/min', prop['conditions']['loading_rate']['text'])
                method = prop['conditions']['test_method']['text']
                for text in ('Instron 5500R-1132', 'Epsilon', '3542', 'dog-bone'):
                    self.assertIn(text, method)
                for description in (method, prop['method_definition']['definition']):
                    self.assertIn('ASTM D1708-18', description)
                    self.assertIn('source-cited', description)
                self.assertIn('Injection-molded', state['state']['product_form']['text'])
                self.assertIn('DCP', state['state']['processing']['text'])
                self.assertIn('separate route', state['state']['processing']['notes'])
        contract = self.source_review['property_contract']
        self.assertEqual(contract['standard'], 'ASTM D1708-18')
        self.assertIs(type(contract['standard_edition']), int)
        self.assertEqual(contract['standard_edition'], 2018)
        self.assertEqual(contract['standard_locator'], 'PDF p.5 section 2.9 and p.15 reference [32]')
        self.assertFalse(contract['standard_compliance_verified'])
        edition_basis = contract['standard_edition_basis'].casefold()
        self.assertIn('source-cited edition only', edition_basis)
        self.assertIn('independent compliance remains unverified', edition_basis)
        self.assertIn('no dimensions or conditioning are inferred', edition_basis)

    def test_grade_test_conditions_and_modulus_fit_unknowns_stay_null(self):
        for identity, state, prop in zip(self.identities, self.states, self.properties):
            with self.subTest(property=prop['id']):
                self.assertIsNone(state['grade_id'])
                self.assertIn('FZ91PM/FZ91PB', identity['identity_scope'])
                self.assertIn('without resolving a single grade', identity['identity_scope'])
                for fact in (prop['conditions']['temperature'], prop['conditions']['conditioning'],
                             state['state']['conditioning']):
                    self.assertEqual(fact['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(fact['text'])
                    self.assertIsNone(fact.get('value'))
                additional = {entry['name']: entry['fact'] for entry in prop['conditions']['additional_conditions']}
                humidity = additional['test_relative_humidity']
                self.assertEqual(humidity['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(humidity['text'])
                self.assertIsNone(prop['method_definition']['extraction_window'])
                self.assertIn('window and estimator are not stated', prop['method_definition']['definition'])
                self.assertIn('not assigned to the test', prop['conditions']['temperature']['notes'])
        contract = self.source_review['property_contract']
        for field in ('test_temperature', 'relative_humidity', 'post_molding_conditioning',
                      'numerical_modulus_fit_interval'):
            self.assertIsNone(contract[field])

    def test_exact_existing_source_authorship_license_and_document_are_reused(self):
        source, = self.graph['sources']['records']
        self.assertEqual(source, self.baseline_source)
        self.assertEqual(record_sha256(source), SOURCE_HASH)
        for representation in (source, self.spec['source_records'][0]['record'],
                               self.saved_packet['input']['source_records'][0]['record'],
                               self.saved_packet['catalogs']['sources']['records'][0]):
            self.assertEqual(representation['id'], SOURCE)
            self.assertEqual(representation['authors'], AUTHORS)
            self.assertNotIn('Luis Alves', representation['authors'])
            self.assertEqual(representation['doi'], DOI)
            self.assertEqual(representation, self.baseline_source)
        self.assertEqual(source['license'], {
            'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0',
        })
        self.assertEqual(self.spec['source_records'][0]['sha256'], SOURCE_HASH)
        self.assertEqual(self.packet['report']['delta']['sources'], 0)
        review = self.source_review
        self.assertEqual(review['source']['authors'], AUTHORS)
        self.assertEqual(review['source']['document_sha256'], PDF_HASH)
        self.assertEqual(review['source']['document_bytes'], 3211541)
        self.assertEqual(review['source']['existing_source_canonical_sha256'], SOURCE_HASH)
        self.assertEqual(review['rights_review']['license_identifier'], 'CC-BY-4.0')
        self.assertEqual(review['rights_review']['license_url'], 'https://creativecommons.org/licenses/by/4.0/')
        self.assertFalse(review['inspection']['raw_assets_published'])
        self.assertFalse(review['rights_review']['project_mit_relicensing_claimed'])
        for prop in self.properties:
            self.assertEqual(prop['source_document']['sha256'], PDF_HASH)
            self.assertEqual(prop['source_document']['url'], PDF_URL)
        self.assertFalse(any(path.suffix.casefold() in {'.pdf', '.png', '.jpg', '.xlsx', '.xml'}
                             for path in BATCH.rglob('*')))

    def test_source_drift_cannot_be_authorized_by_rehashing_existing_record(self):
        for mutation in ('stale_hash', 'authors', 'license', 'doi', 'claim_notes'):
            spec = deepcopy(self.spec)
            descriptor = spec['source_records'][0]
            if mutation == 'authors':
                descriptor['record']['authors'].append('Luis Alves')
            elif mutation == 'license':
                descriptor['record']['license'] = {'status': 'unverified', 'identifier': None}
            elif mutation == 'doi':
                descriptor['record']['doi'] = '10.3390/polym17020195'
            elif mutation == 'claim_notes':
                descriptor['record']['claim_notes'].append('Unreviewed expansion of historical scope.')
            else:
                descriptor['record']['title'] += ' unreviewed edit'
            if mutation != 'stale_hash':
                descriptor['sha256'] = record_sha256(descriptor['record'])
            message = 'source record hash mismatch' if mutation == 'stale_hash' else 'existing source record cannot be rewritten'
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, message):
                compile_spec(spec, BASELINE)

    def test_measured_candidate_preparation_is_not_scientific_or_formal_admission(self):
        self.assertEqual(self.spec['review']['formal_admitted_delta'], 0)
        self.assertFalse(self.spec['review']['verification']['independent_scientific_review'])
        self.assertFalse(self.spec['review']['verification']['raw_data_reanalysis'])
        self.assertEqual(self.source_review['candidate_scope']['actual_admitted_identity_delta'], 0)
        for prop in self.properties:
            self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
            self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
            self.assertEqual(prop['evaluation_support'], 'catalog_only')
            self.assertFalse(prop['universal_bound'])
            self.assertFalse(prop['engineering_allowable'])
            self.assertFalse(prop['verification']['independent_scientific_review'])
            self.assertFalse(prop['verification']['raw_data_reanalysis'])
        for field in ('independent_scientific_review', 'raw_data_reanalysis'):
            spec = deepcopy(self.spec)
            spec['review']['verification'][field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                compile_spec(spec, BASELINE)

    def test_finite_identity_review_replays_twenty_two_direct_baseline_inputs(self):
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
                self.assertEqual(checkpoint_bytes(descriptor['path'], path.read_bytes()), frozen)
                self.assertEqual(len(frozen), descriptor['bytes'])
                self.assertEqual(sha256(frozen).hexdigest(), descriptor['sha256'])
        helper_spec = importlib.util.spec_from_file_location('ewurum_reactive_identity_review', BATCH / 'build_identity_review.py')
        helper = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(helper)
        self.assertEqual(encoded(helper.build_review()), (BATCH / 'identity-review.json').read_bytes())

    def test_baseline_raw_bytes_counts_and_frozen_inventories_are_unchanged(self):
        self.assertEqual(self.spec['baseline_sha256'], BASELINE_HASHES)
        for key, filename in FILES.items():
            with self.subTest(filename=filename):
                self.assertEqual(sha256(self.baseline_bytes[filename]).hexdigest(), BASELINE_HASHES[PIN_KEYS[key]])
                self.assertEqual(self.baseline_bytes[filename], git_bytes('materials_boundaries/data/' + filename))
                self.assertEqual((BASELINE / filename).read_bytes(), self.baseline_bytes[filename])
        self.assertEqual(len(self.baseline_materials['identities']), 1164)
        self.assertEqual(Counter(row['category'] for row in self.baseline_materials['identities']),
                         {'natural': 1010, 'metal': 32, 'inorganic': 59, 'polymer': 30, 'composite': 33})
        self.assertEqual(self.packet['report']['before']['identities'], 1164)
        self.assertEqual(self.packet['report']['after']['identities'], 1168)
        changed_old = subprocess.run(
            ['git', 'diff', BASE_COMMIT, '--name-only', '--diff-filter=CDMRTUXB'],
            cwd=ROOT, check=True, capture_output=True, timeout=30,
        ).stdout
        changed_old = checkpoint_changed_paths(changed_old)
        self.assertEqual(changed_old, b'')
        manifest = read(ROOT / 'tests/core_partition/manifest.json')
        self.assertEqual((manifest['module_count'], manifest['test_count']), (147, 1887))
        self.assertEqual(manifest['root_inventory_sha256'],
                         '19a735217c29533c1137a6cfd95b2b58cf88e8cf649848e41012c510434446f7')
        replay = read(ROOT / 'tests/history_replay_latest/ci-inventory.json')
        self.assertEqual((replay['count'], len(replay['ids'])), (70, 70))
        self.assertEqual(replay['fingerprint'], '90d7b151772f2d39f090ef6d49fdac011a35730072ed1d67f9925570ab3ddaca')
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
        required = {(BATCH / name).relative_to(ROOT).as_posix() for name in (
            'packet-spec.json', 'source-review.json', 'identity-review.json', 'build_identity_review.py')}
        required.update('materials_boundaries/data/' + filename for filename in FILES.values())
        self.assertTrue(required.issubset(receipt['inputs']))
        for relative, descriptor in receipt['inputs'].items():
            path = (ROOT / relative).resolve()
            with self.subTest(input=relative):
                self.assertTrue(path.is_relative_to(ROOT.resolve()))
                data = checkpoint_bytes(relative, path.read_bytes())
                self.assertEqual(descriptor['bytes'], len(data))
                self.assertEqual(descriptor['sha256'], sha256(data).hexdigest())

    def test_replay_and_idempotent_write_preserve_exact_bytes_and_mtime(self):
        self.assertEqual(self.packet, self.saved_packet)
        self.assertEqual(self.packet['input'], self.spec)
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

    def test_missing_property_cannot_write_a_partial_candidate(self):
        spec = deepcopy(self.spec)
        spec['formulations'][0]['states'][0]['properties'] = []
        with tempfile.TemporaryDirectory() as directory:
            path, output = Path(directory) / 'spec.json', Path(directory) / 'packet.json'
            path.write_bytes(encoded(spec))
            with self.assertRaises(ValueError):
                write_packet(BASELINE, path, output)
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_wrong_modulus_or_sd_units_are_rejected(self):
        for field in ('reported_value', 'uncertainty'):
            spec = deepcopy(self.spec)
            prop = deepcopy(self.properties[0])
            prop[field].update(unit_code='kg/m^3', unit_text='kg/m^3')
            spec['formulations'][0]['states'][0]['properties'][0] = explicit(spec, 'property', prop)
            with self.subTest(field=field), self.assertRaises(ValueError):
                compile_spec(spec, BASELINE)

    def test_r_alias_b_alias_designation_and_cloned_identity_cannot_create_growth(self):
        for mutation in ('r_alias', 'b_alias', 'b_designation', 'clone'):
            spec = deepcopy(self.spec)
            if mutation in ('r_alias', 'b_alias'):
                identity = deepcopy(self.identities[1])
                identity['aliases'].append({'language': 'und', 'text': '  r10  ' if mutation == 'r_alias' else '  b10  '})
                spec['formulations'][1]['identity'] = explicit(spec, 'identity', identity)
            elif mutation == 'b_designation':
                state = deepcopy(self.states[0])
                state['source_designation'] = 'B10'
                spec['formulations'][0]['states'][0]['record'] = explicit(spec, 'state', state)
            else:
                spec['formulations'].append(deepcopy(spec['formulations'][0]))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_spec(spec, BASELINE)

    def test_wrong_identity_or_property_state_join_is_rejected(self):
        for mutation in ('identity', 'property'):
            spec = deepcopy(self.spec)
            if mutation == 'identity':
                state = deepcopy(self.states[0])
                state['identity_id'] = self.identities[1]['id']
                spec['formulations'][0]['states'][0]['record'] = explicit(spec, 'state', state)
            else:
                prop = deepcopy(self.properties[0])
                prop['material_state_id'] = self.states[1]['id']
                spec['formulations'][0]['states'][0]['properties'][0] = explicit(spec, 'property', prop)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_spec(spec, BASELINE)

    def test_an_additional_synthetic_state_does_not_add_a_material_identity(self):
        # New IDs alone must not bypass the structural duplicate guard.
        spec = deepcopy(self.spec)
        state, prop = deepcopy(self.states[0]), deepcopy(self.properties[0])
        state['id'] += '_test_repeat'
        prop['id'] += '_test_repeat'
        prop['material_state_id'] = state['id']
        state['property_ids'] = [prop['id']]
        spec['formulations'][0]['states'].append({
            'record': explicit(spec, 'state', state),
            'properties': [explicit(spec, 'property', prop)],
        })
        with self.assertRaisesRegex(ValueError, 'duplicate structural state'):
            compile_spec(spec, BASELINE)
        # Exercise counting with a distinct synthetic state, never persisted or
        # claimed as scientific evidence or additional source support.
        state['state']['product_form']['text'] = 'Synthetic alternative test geometry'
        spec['formulations'][0]['states'][-1]['record'] = explicit(spec, 'state', state)
        packet = compile_spec(spec, BASELINE)
        self.assertEqual(packet['report']['delta']['identities'], 4)
        self.assertEqual(packet['report']['delta']['states'], 5)
        self.assertEqual(packet['report']['delta']['properties'], 5)
        self.assertEqual(packet['report']['delta']['sources'], 0)
        self.assertEqual(packet['report']['formal_admitted_delta'], 0)

    def test_baseline_drift_and_pending_source_or_identity_block_handoff(self):
        spec = deepcopy(self.spec)
        spec['baseline_sha256']['materials'] = '0' * 64
        with self.assertRaises(ValueError):
            compile_spec(spec, BASELINE)
        for gate in ('source', 'identity'):
            spec = deepcopy(self.spec)
            if gate == 'source':
                spec['review']['source_reviews'][0]['status'] = 'pending'
            else:
                spec['identity_crosswalk'][0]['disposition'] = 'pending'
            with self.subTest(gate=gate):
                packet = compile_spec(spec, BASELINE)
                self.assertFalse(packet['report']['handoff_ready'])
                self.assertTrue(packet['report']['pending_gates'])
                self.assertEqual(packet['report']['formal_admitted_delta'], 0)

    def test_forged_values_sds_counts_and_admission_cannot_replace_exact_replay(self):
        for mutation in ('b_value', 'sd', 'count', 'source_count', 'admission', 'ready'):
            packet = deepcopy(self.saved_packet)
            if mutation == 'b_value':
                packet['catalogs']['properties']['records'][0]['reported_value'].update(number='922', value_text='922')
            elif mutation == 'sd':
                packet['catalogs']['properties']['records'][0]['uncertainty'].update(number='77', value_text='77')
            elif mutation == 'count':
                packet['report']['delta']['identities'] = 40
            elif mutation == 'source_count':
                packet['report']['delta']['sources'] = 1
            elif mutation == 'admission':
                packet['report']['formal_admitted_delta'] = 4
            else:
                packet['report']['handoff_ready'] = not packet['report']['handoff_ready']
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'differs from exact replay'):
                validate_prepared_packet(packet, BASELINE)


if __name__ == '__main__':
    unittest.main()
