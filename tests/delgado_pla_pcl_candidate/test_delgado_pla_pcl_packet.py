"""Independent source oracles and review-only gates for seven PLA/PCL blends.

Run this directory explicitly. It has no package initializer and does not extend
the frozen 1,887-test root inventory or the separate 70-test history inventory.
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

BATCH = ROOT / 'experimental/material-batches/delgado-pla-pcl-20261026'
BASELINE = ROOT / 'materials_boundaries/data'
BASE_COMMIT = '437950c414ea340eda340babe7b63dee9fcee535'
SOURCE = 'delgado_aguilar_2020_pla_pcl'
DOI = '10.3390/ma13112655'
XML_URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7321633/fullTextXML'
XML_HASH = '1fc618818e73292837129bd4bf9885b71982974d5e7fead0056276fb28f8cb6b'
HTML_URL = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7321633/'
HTML_HASH = 'dd24715210b6aae58c9a2c38ec352e03492ff822fd21bc5a275353dc88014d23'
AUTHORS = ['Marc Delgado-Aguilar', 'Rita Puig', 'Ilija Sazdovski', 'Pere Fullana-i-Palmer']
BASELINE_HASHES = {
    'materials': '01e04f88e13685e5e5624abeee4dd0ffce8f6f7e32708e4b30420180c70c5000',
    'reference_properties': '8daa3b067fc166e25bdf89e9585c4ea4b6f421a918780c2a83e395461dc1c454',
    'sources': 'c5eecc0e7c64d9ef4af623f0800d947cec8a7f91570633b45b053d6ecb0c75aa',
}
# Table 1 nominal wt% PLA/PCL -> Table 2 density-calculated V_PCL ->
# experimental modulus and source-reported SD. This oracle is independent of
# the packet generator. Decimal strings deliberately preserve printed precision.
ROWS = (
    ('b95_5', 'B95/5', '95', '5', '0.054', '3.70', '0.13'),
    ('b90_10', 'B90/10', '90', '10', '0.108', '3.60', '0.26'),
    ('b85_15', 'B85/15', '85', '15', '0.162', '3.38', '0.27'),
    ('b80_20', 'B80/20', '80', '20', '0.214', '3.20', '0.19'),
    ('b60_40', 'B60/40', '60', '40', '0.421', '2.55', '0.09'),
    ('b40_60', 'B40/60', '40', '60', '0.621', '1.86', '0.11'),
    ('b20_80', 'B20/80', '20', '80', '0.814', '1.13', '0.05'),
)


def read(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def explicit(spec, kind, record):
    spec['contexts'][kind]['test_explicit'] = {}
    return {'context': 'test_explicit', 'fields': deepcopy(record)}


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True,
                          capture_output=True, timeout=30).stdout


class DelgadoPlaPclCandidatePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = read(BATCH / 'packet-spec.json')
        cls.saved_packet = read(BATCH / 'prepared-packet.json')
        cls.source_review = read(BATCH / 'source-review.json')
        cls.baseline_bytes = {name: (BASELINE / name).read_bytes() for name in FILES.values()}
        cls.baseline = {key: json.loads(cls.baseline_bytes[name]) for key, name in FILES.items()}
        cls.packet = compile_spec(cls.spec, BASELINE)
        cls.graph = cls.packet['catalogs']
        cls.identities = cls.graph['materials']['identities']
        cls.states = cls.graph['materials']['records']
        cls.properties = cls.graph['properties']['records']

    def assert_invalid_property(self, mutation):
        spec = deepcopy(self.spec)
        prop = deepcopy(self.properties[0])
        mutation(prop)
        spec['formulations'][0]['states'][0]['properties'][0] = explicit(spec, 'property', prop)
        with self.assertRaises(ValueError):
            compile_spec(spec, BASELINE)

    def test_exact_experimental_moduli_and_sd_preserve_source_decimal_strings(self):
        self.assertEqual([state['source_designation'] for state in self.states], [row[1] for row in ROWS])
        for (suffix, label, _, _, _, value, sd), prop in zip(ROWS, self.properties):
            with self.subTest(label=label):
                self.assertEqual(prop['id'], 'refprop_delgado2020_pla_pcl_' + suffix + '_youngs_modulus')
                self.assertEqual(prop['quantity'], 'youngs_modulus')
                self.assertEqual(prop['quantity_dimension'], 'pressure')
                self.assertIsNone(prop['density_basis'])
                self.assertEqual(prop['source_id'], SOURCE)
                self.assertEqual(prop['reported_value'], {
                    'kind': 'scalar', 'number': value, 'value_text': value,
                    'unit_code': 'GPa', 'unit_text': 'GPa',
                })
                measure, = prop['uncertainty']['measures']
                self.assertEqual(measure['reported_value'], {
                    'number': sd, 'value_text': sd, 'unit_code': 'GPa', 'unit_text': 'GPa',
                })

    def test_seven_binary_blend_identities_have_exact_state_and_property_joins(self):
        self.assertEqual(self.packet['report']['delta'], {
            'identities': 7, 'grades': 0, 'states': 7, 'properties': 7, 'sources': 1,
            'categories': {'metal': 0, 'inorganic': 0, 'polymer': 7, 'composite': 0, 'natural': 0},
        })
        self.assertEqual((len(self.identities), len(self.states), len(self.properties)), (7, 7, 7))
        self.assertEqual(self.graph['materials']['grades'], [])
        for (suffix, label, _, _, _, _, _), identity, state, prop in zip(
                ROWS, self.identities, self.states, self.properties):
            with self.subTest(label=label):
                self.assertEqual(identity['id'], 'mat_delgado2020_pla_pcl_' + suffix)
                self.assertEqual(identity['category'], 'polymer')
                self.assertIn('Delgado', identity['name'])
                self.assertEqual(state['id'], 'state_delgado2020_pla_pcl_' + suffix + '_injection_molded')
                self.assertEqual(state['identity_id'], identity['id'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['property_ids'], [prop['id']])
                self.assertEqual(prop['material_state_id'], state['id'])
        self.assertEqual({prop['quantity'] for prop in self.properties}, {'youngs_modulus'})
        self.assertEqual([row['source_designations'] for row in self.spec['identity_crosswalk']],
                         [[row[1]] for row in ROWS])

    def test_nominal_mass_recipes_join_exact_volume_rows_without_new_density_properties(self):
        facts = self.spec['review']['candidate_facts']
        self.assertEqual(facts, self.source_review['selected_facts'])
        self.assertEqual(len(facts), 7)
        for fact, (suffix, label, pla, pcl, volume, value, sd), state, prop in zip(
                facts, ROWS, self.states, self.properties):
            with self.subTest(label=label):
                self.assertEqual(fact, {
                    'identity_id': 'mat_delgado2020_pla_pcl_' + suffix,
                    'state_id': 'state_delgado2020_pla_pcl_' + suffix + '_injection_molded',
                    'property_id': 'refprop_delgado2020_pla_pcl_' + suffix + '_youngs_modulus',
                    'table_1_label': label, 'nominal_pla_wt_percent': pla,
                    'nominal_pcl_wt_percent': pcl, 'table_2_v_pcl': volume,
                    'v_pcl_basis': 'source_calculated_from_density_measurements_contextual_join_only',
                    'youngs_modulus_gpa': value, 'standard_deviation_gpa': sd,
                    'source_expression_gpa': value + ' \u00b1 ' + sd,
                    'summary_statistic': 'not_stated', 'sample_count': None,
                })
                self.assertEqual(int(pla) + int(pcl), 100)
                composition = state['state']['composition_or_purity']
                self.assertEqual(composition['status'], 'reported')
                self.assertIn('Nominal PLA/PCL input composition ' + pla + '/' + pcl + ' wt%', composition['text'])
                self.assertIn('calculated PCL volume fraction ' + volume, composition['text'])
                self.assertIn('not a separately measured final composition', composition['notes'])
                for ingredient in ('4043D', 'Capa 6500', 'ingredient context only', 'not a finished-blend grade'):
                    self.assertIn(ingredient, composition['notes'])
                value_evidence = [entry for entry in prop['evidence'] if 'reported_value' in entry['supports']]
                self.assertTrue(value_evidence)
                for entry in value_evidence:
                    self.assertIn('Table 2', entry['locator'])
                    self.assertIn('V_PCL ' + volume + ' row', entry['locator'])
                    self.assertIn('Table 1 ' + label, entry['locator'])
                self.assertIn('not new measured properties', prop['scope_note'])
        exclusions = ' '.join(self.source_review['exclusions'])
        for excluded in ('B100/0', 'B0/100', 'Voigt-Reuss', 'commercial comparison'):
            self.assertIn(excluded, exclusions)

    def test_tensile_method_keeps_clamp_spacing_separate_and_unknown_conditions_unknown(self):
        method_review = self.source_review['tensile_method']
        for key, expected in {
            'standard': 'ISO 527-1:2012', 'instrument': 'Instron 1122',
            'load_cell': '5 kN', 'crosshead_speed': '2 mm/min', 'clamp_separation': '115 mm',
        }.items():
            self.assertEqual(method_review[key], expected)
        for key in ('extensometer_gauge_length', 'modulus_fit_window', 'test_temperature',
                    'test_relative_humidity', 'test_pressure', 'post_molding_conditioning',
                    'specimen_type', 'specimen_dimensions', 'sample_count'):
            self.assertIsNone(method_review[key])
        self.assertFalse(method_review['independent_standard_compliance_verified'])
        for state, prop in zip(self.states, self.properties):
            with self.subTest(property=prop['id']):
                conditions = prop['conditions']
                self.assertEqual(conditions['test_standard']['text'], 'ISO 527-1:2012.')
                self.assertEqual(conditions['loading_rate']['text'], 'Crosshead speed 2 mm/min.')
                definition = prop['method_definition']
                self.assertEqual(definition['type'], 'source_reported_conventional')
                self.assertIsNone(definition['extraction_window'])
                for fact in ('Instron 1122', '5-kN', 'ISO 527-1:2012', '2 mm/min', '115 mm'):
                    self.assertIn(fact, definition['definition'])
                self.assertIn('extensometer gauge length are not stated', definition['definition'])
                extras = {entry['name']: entry['fact'] for entry in conditions['additional_conditions']}
                self.assertEqual(extras['clamp_separation']['text'], 'Gap between clamps: 115 mm.')
                self.assertIn('not an extensometer gauge length', extras['clamp_separation']['notes'])
                unknown = [conditions['temperature'], conditions['direction'], conditions['conditioning'],
                           state['state']['conditioning']]
                unknown.extend(extras[key] for key in ('test_relative_humidity', 'test_pressure',
                               'specimen_type_and_dimensions', 'measurement_repetitions'))
                for fact in unknown:
                    self.assertEqual(fact['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(fact['text'])
                    self.assertEqual(fact['evidence'], [])
                tensile_text = json.dumps(conditions, ensure_ascii=False)
                for unrelated in ('210', '2.16', 'ISO 1133', 'ISO 178', 'ISO 179'):
                    self.assertNotIn(unrelated, tensile_text)

    def test_preparation_retains_variable_molding_settings_without_assigning_a_universal_recipe(self):
        for state, prop in zip(self.states, self.properties):
            with self.subTest(state=state['id']):
                process = state['state']['processing']
                self.assertEqual(process['status'], 'reported')
                for fact in ('190 degrees C', '80 rpm', 'constant torque'):
                    self.assertIn(fact, process['text'])
                for fact in ('175, 180, 185, 185 and 190', '330-600 bar', 'Section 3.1',
                             'temperature and pressure', 'melt flow index', 'per-formulation', 'unresolved'):
                    self.assertIn(fact, process['notes'])
                drying = state['state']['temper_or_heat_treatment']
                self.assertEqual(drying['status'], 'reported')
                self.assertIn('60 degrees C until constant weight', drying['text'])
                self.assertIn('post-molding', drying['notes'])
                self.assertIn('not stated', drying['notes'])
                self.assertTrue(prop['source_discrepancies'])
                self.assertTrue(any('Section 3.1' in entry['description']
                                    for entry in prop['source_discrepancies']))
                self.assertIsNone(prop['conditions']['temperature']['text'])

    def test_reported_sd_does_not_invent_a_mean_sem_confidence_or_sample_count(self):
        for prop in self.properties:
            with self.subTest(property=prop['id']):
                self.assertEqual(prop['summary_statistic'], 'not_stated')
                self.assertEqual(prop['reporting_basis'], 'not_stated')
                self.assertEqual(prop['uncertainty_status'], 'reported_measures')
                self.assertEqual(prop['uncertainty']['type'], 'reported_measures')
                measure, = prop['uncertainty']['measures']
                self.assertEqual(measure['kind'], 'standard_deviation')
                self.assertEqual(measure['availability'], 'numeric_reported')
                self.assertEqual(measure['basis'], 'absolute')
                self.assertEqual(measure['qualifier'], 'not_qualified_in_source')
                self.assertIsNone(measure['coverage_factor'])
                self.assertIsNone(measure['confidence_level'])
                self.assertIsInstance(measure['note'], str)
                self.assertIn('aggregation', measure['note'].casefold())
                self.assertIn('mean', measure['note'].casefold())
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                linked = {(entry['source_id'], entry['url'], entry['locator'])
                          for entry in prop['evidence'] if 'uncertainty' in entry['supports']}
                for entry in measure['evidence']:
                    self.assertEqual(entry['source_id'], SOURCE)
                    self.assertIn('uncertainty', entry['supports'])
                    self.assertIn((entry['source_id'], entry['url'], entry['locator']), linked)

    def test_source_attribution_document_hash_and_rights_are_exact(self):
        source, = self.graph['sources']['records']
        self.assertEqual(source['id'], SOURCE)
        self.assertEqual(source['doi'], DOI)
        self.assertEqual(source['authors'], AUTHORS)
        self.assertEqual(source['license'], {'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0'})
        for url in (XML_URL, HTML_URL, 'https://creativecommons.org/licenses/by/4.0/'):
            self.assertIn(url, source['urls'])
        self.assertEqual(record_sha256(source), self.spec['source_records'][0]['sha256'])
        self.assertTrue(any('Changes:' in note for note in source['claim_notes']))
        for prop in self.properties:
            self.assertEqual(prop['source_document']['url'], XML_URL)
            self.assertEqual(prop['source_document']['sha256'], XML_HASH)
            self.assertFalse(prop['source_document']['url'].casefold().endswith('.pdf'))
        review_text = json.dumps(self.source_review, ensure_ascii=False)
        for fact in (XML_HASH, HTML_HASH, XML_URL, HTML_URL):
            self.assertIn(fact, review_text)
        self.assertIn('captcha', review_text.casefold())
        access = self.source_review['source_access']
        self.assertEqual(access['official_xml']['bytes'], 157502)
        pdf = access['original_pdf']
        self.assertIsNone(pdf['sha256'])
        for key in ('bytes_verified', 'rendered_pixels_verified',
                    'equivalence_to_inspected_xml_or_html_verified', 'bypass_attempted'):
            self.assertFalse(pdf[key])
        self.assertFalse(any(path.suffix.casefold() in {'.pdf', '.png', '.jpg', '.xml', '.html', '.xlsx'}
                             for path in BATCH.rglob('*')))

    def test_identity_audit_replays_twenty_two_frozen_inputs_without_claiming_uniqueness(self):
        review = read(BATCH / 'identity-review.json')
        self.assertEqual(review['baseline_commit'], BASE_COMMIT)
        for key in ('scientific_review', 'scientific_replication', 'global_chemical_uniqueness_established'):
            self.assertFalse(review[key])
        self.assertEqual(review['formal_admitted_delta'], 0)
        self.assertEqual(review['candidate_delta'], {
            'identities': 7, 'polymer': 7, 'grades': 0, 'states': 7, 'properties': 7, 'sources': 1,
        })
        descriptors = review['immutable_inputs']
        self.assertEqual(len(descriptors), 22)
        self.assertEqual(len({entry['path'] for entry in descriptors}), 22)
        for descriptor in descriptors:
            path = (ROOT / descriptor['path']).resolve()
            with self.subTest(input=descriptor['path']):
                self.assertTrue(path.is_relative_to(ROOT.resolve()))
                frozen = git('show', BASE_COMMIT + ':' + descriptor['path'])
                self.assertEqual(path.read_bytes(), frozen)
                self.assertEqual(len(frozen), descriptor['bytes'])
                self.assertEqual(sha256(frozen).hexdigest(), descriptor['sha256'])
        helper_spec = importlib.util.spec_from_file_location('delgado_identity_review', BATCH / 'build_identity_review.py')
        helper = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(helper)
        self.assertEqual(encoded(helper.build_review()), (BATCH / 'identity-review.json').read_bytes())
        review_text = json.dumps(review, ensure_ascii=False).casefold()
        for qualifier in ('tough pla', 'unknown', 'nominal', 'finite'):
            self.assertIn(qualifier, review_text)

    def test_baseline_catalog_bytes_counts_and_current_1192_total_are_unchanged(self):
        self.assertEqual(self.spec['baseline_sha256'], BASELINE_HASHES)
        for key, filename in FILES.items():
            with self.subTest(filename=filename):
                raw = self.baseline_bytes[filename]
                self.assertEqual(sha256(raw).hexdigest(), BASELINE_HASHES[PIN_KEYS[key]])
                self.assertEqual(raw, git('show', BASE_COMMIT + ':materials_boundaries/data/' + filename))
                self.assertEqual((BASELINE / filename).read_bytes(), raw)
        identities = self.baseline['materials']['identities']
        self.assertEqual(len(identities), 1168)
        self.assertEqual(Counter(row['category'] for row in identities),
                         {'natural': 1010, 'metal': 32, 'inorganic': 59, 'polymer': 30, 'composite': 37})
        self.assertEqual(self.packet['report']['before']['identities'], 1168)
        self.assertEqual(self.packet['report']['after']['identities'], 1175)
        self.assertFalse(any(row['id'].startswith('mat_delgado2020_') for row in identities))
        counts = read(BATCH / 'identity-review.json')['baseline_counts']
        self.assertEqual(counts['existing_formal_computed_records'], 24)
        self.assertEqual(counts['experimental_project_total'], 1192)
        self.assertEqual(counts['new_admissions_in_this_audit'], 0)

    def test_all_old_files_and_frozen_test_inventories_remain_unchanged(self):
        tracked = git('ls-tree', '-r', '--name-only', BASE_COMMIT).decode('utf-8').splitlines()
        self.assertEqual(len(tracked), 1057)
        self.assertEqual(sum(path.startswith('tests/fixtures/') for path in tracked), 122)
        self.assertEqual(git('diff', BASE_COMMIT, '--name-only', '--diff-filter=CDMRTUXB'), b'')
        manifest = read(ROOT / 'tests/core_partition/manifest.json')
        self.assertEqual((manifest['module_count'], manifest['test_count']), (147, 1887))
        self.assertEqual(manifest['root_inventory_sha256'],
                         '19a735217c29533c1137a6cfd95b2b58cf88e8cf649848e41012c510434446f7')
        replay = read(ROOT / 'tests/history_replay_latest/ci-inventory.json')
        self.assertEqual((replay['count'], len(replay['ids'])), (70, 70))
        self.assertEqual(replay['fingerprint'], '90d7b151772f2d39f090ef6d49fdac011a35730072ed1d67f9925570ab3ddaca')
        self.assertFalse((Path(__file__).parent / '__init__.py').exists())

    def test_preparation_receipt_binds_packet_spec_and_all_eight_inputs(self):
        receipt = read(BATCH / 'preparation-receipt.json')
        self.assertEqual(receipt['schema'], 'material-batch-preparation-receipt/1')
        self.assertEqual(receipt['batch_id'], 'delgado-pla-pcl-20261026')
        self.assertEqual(receipt['baseline_commit'], BASE_COMMIT)
        packet_raw = (BATCH / 'prepared-packet.json').read_bytes()
        self.assertEqual(receipt['prepared_packet_bytes'], len(packet_raw))
        self.assertEqual(receipt['prepared_packet_sha256'], sha256(packet_raw).hexdigest())
        self.assertEqual(receipt['spec_canonical_sha256'], record_sha256(self.spec))
        self.assertEqual(receipt['spec_canonical_sha256'], self.saved_packet['spec_sha256'])
        self.assertEqual(self.saved_packet['input'], self.spec)
        required = {(BATCH / name).relative_to(ROOT).as_posix() for name in (
            'packet-spec.json', 'source-review.json', 'identity-review.json',
            'build_identity_review.py', 'README.md',
        )}
        required.update('materials_boundaries/data/' + name for name in FILES.values())
        self.assertEqual(set(receipt['inputs']), required)
        self.assertEqual(len(receipt['inputs']), 8)
        for relative, descriptor in receipt['inputs'].items():
            path = (ROOT / relative).resolve()
            with self.subTest(input=relative):
                self.assertTrue(path.is_relative_to(ROOT.resolve()))
                raw = path.read_bytes()
                self.assertEqual(descriptor, {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()})
        for key in ('output_bytes_and_mtime_unchanged', 'inputs_unchanged', 'runtime_catalogs_unchanged'):
            self.assertIs(receipt[key], True)
        self.assertEqual(receipt['report'], self.packet['report'])
        self.assertEqual(receipt['report'], self.saved_packet['report'])
        self.assertEqual(receipt['report']['delta'], {
            'identities': 7, 'grades': 0, 'states': 7, 'properties': 7, 'sources': 1,
            'categories': {'metal': 0, 'inorganic': 0, 'polymer': 7, 'composite': 0, 'natural': 0},
        })
        self.assertEqual(receipt['formal_admitted_delta'], 0)
        self.assertEqual(receipt['report']['formal_admitted_delta'], 0)
        # These independently hashed artifacts concern this exact candidate;
        # they are source/reproducibility evidence, not admission approvals.
        for artifact in (self.source_review, read(BATCH / 'identity-review.json')):
            self.assertEqual(artifact['batch_id'], receipt['batch_id'])
            self.assertEqual(artifact['baseline_commit'], receipt['baseline_commit'])
        self.assertEqual(self.source_review['selected_facts'], self.spec['review']['candidate_facts'])

    def test_replay_and_immutable_write_preserve_exact_bytes_and_mtime(self):
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

    def test_wrong_modulus_sd_units_and_decimal_precision_are_rejected(self):
        for mutation in ('dimension', 'sd_unit', 'unit_text', 'modulus_precision', 'sd_precision'):
            def change(prop):
                measure = prop['uncertainty']['measures'][0]['reported_value']
                if mutation == 'dimension':
                    prop['reported_value'].update(unit_code='kg/m^3', unit_text='kg/m^3')
                elif mutation == 'sd_unit':
                    measure.update(unit_code='MPa', unit_text='MPa')
                elif mutation == 'unit_text':
                    prop['reported_value']['unit_text'] = 'MPa'
                elif mutation == 'modulus_precision':
                    prop['reported_value']['number'] = '3.7'
                else:
                    measure['number'] = '0.130'
            with self.subTest(mutation=mutation):
                self.assert_invalid_property(change)

    def test_sd_metadata_cannot_infer_mean_sem_or_lose_primary_evidence(self):
        for mutation in ('no_note', 'mean', 'sem', 'legacy', 'wrong_locator', 'no_tag', 'duplicate'):
            def change(prop):
                measure = prop['uncertainty']['measures'][0]
                if mutation == 'no_note':
                    measure['note'] = None
                elif mutation == 'mean':
                    prop['summary_statistic'] = 'reported_mean'
                elif mutation == 'sem':
                    measure.update(kind='standard_error_of_mean', basis='relative_to_reported_value')
                    measure['reported_value'].update(unit_code='percent', unit_text='%')
                elif mutation == 'legacy':
                    prop['uncertainty_status'] = 'reported_standard_deviation'
                elif mutation == 'wrong_locator':
                    measure['evidence'][0]['locator'] = 'Table 2, unrelated model column'
                elif mutation == 'no_tag':
                    measure['evidence'][0]['supports'] = ['reported_value']
                else:
                    prop['uncertainty']['measures'].append(deepcopy(measure))
            with self.subTest(mutation=mutation):
                self.assert_invalid_property(change)

    def test_alias_designation_and_cloned_identity_cannot_create_growth(self):
        for mutation in ('alias', 'designation', 'clone'):
            spec = deepcopy(self.spec)
            if mutation == 'alias':
                identity = deepcopy(self.identities[1])
                identity['aliases'].append({'language': 'und', 'text': '  b95/5  '})
                spec['formulations'][1]['identity'] = explicit(spec, 'identity', identity)
            elif mutation == 'designation':
                state = deepcopy(self.states[1])
                state['source_designation'] = 'B95/5'
                spec['formulations'][1]['states'][0]['record'] = explicit(spec, 'state', state)
            else:
                spec['formulations'].append(deepcopy(spec['formulations'][0]))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_spec(spec, BASELINE)

    def test_wrong_identity_property_or_crosswalk_join_is_rejected(self):
        for mutation in ('identity', 'property', 'crosswalk'):
            spec = deepcopy(self.spec)
            if mutation == 'identity':
                state = deepcopy(self.states[0])
                state['identity_id'] = self.identities[1]['id']
                spec['formulations'][0]['states'][0]['record'] = explicit(spec, 'state', state)
            elif mutation == 'property':
                prop = deepcopy(self.properties[0])
                prop['material_state_id'] = self.states[1]['id']
                spec['formulations'][0]['states'][0]['properties'][0] = explicit(spec, 'property', prop)
            else:
                spec['identity_crosswalk'][0]['source_designations'] = ['B90/10']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_spec(spec, BASELINE)

    def test_extra_state_is_not_an_extra_identity_and_structural_clones_are_refused(self):
        spec = deepcopy(self.spec)
        state, prop = deepcopy(self.states[0]), deepcopy(self.properties[0])
        state['id'] += '_synthetic_repeat'
        prop['id'] += '_synthetic_repeat'
        prop['material_state_id'] = state['id']
        state['property_ids'] = [prop['id']]
        spec['formulations'][0]['states'].append({
            'record': explicit(spec, 'state', state),
            'properties': [explicit(spec, 'property', prop)],
        })
        with self.assertRaisesRegex(ValueError, 'duplicate structural state'):
            compile_spec(spec, BASELINE)
        # This detached synthetic alternative exercises count semantics only.
        state['state']['product_form']['text'] = 'Synthetic alternative test geometry'
        spec['formulations'][0]['states'][-1]['record'] = explicit(spec, 'state', state)
        packet = compile_spec(spec, BASELINE)
        self.assertEqual(packet['report']['delta']['identities'], 7)
        self.assertEqual(packet['report']['delta']['states'], 8)
        self.assertEqual(packet['report']['delta']['properties'], 8)
        self.assertEqual(packet['report']['delta']['sources'], 1)
        self.assertEqual(packet['report']['formal_admitted_delta'], 0)

    def test_stale_source_hash_and_rehashed_existing_source_drift_are_rejected(self):
        spec = deepcopy(self.spec)
        spec['source_records'][0]['record']['title'] += ' unreviewed edit'
        with self.assertRaisesRegex(ValueError, 'source record hash mismatch'):
            compile_spec(spec, BASELINE)
        # A new candidate source is reviewed by the explicit source oracle;
        # adding a rehashed rewrite of an existing source cannot bypass its pin.
        spec = deepcopy(self.spec)
        old_source = deepcopy(self.baseline['sources']['records'][0])
        old_source['authors'].append('Unreviewed test author')
        spec['source_records'].append({'record': old_source, 'sha256': record_sha256(old_source)})
        with self.assertRaisesRegex(ValueError, 'existing source record cannot be rewritten'):
            compile_spec(spec, BASELINE)

    def test_baseline_drift_and_pending_identity_source_or_rights_block_handoff(self):
        spec = deepcopy(self.spec)
        spec['baseline_sha256']['materials'] = '0' * 64
        with self.assertRaises(ValueError):
            compile_spec(spec, BASELINE)
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

    def test_forged_values_sds_sources_counts_or_admission_cannot_replace_replay(self):
        for mutation in ('value', 'sd', 'source', 'rehash_source', 'count', 'admission', 'ready'):
            packet = deepcopy(self.saved_packet)
            if mutation == 'value':
                packet['catalogs']['properties']['records'][0]['reported_value'].update(number='3.71', value_text='3.71')
            elif mutation == 'sd':
                packet['catalogs']['properties']['records'][0]['uncertainty']['measures'][0]['reported_value'].update(
                    number='0.14', value_text='0.14')
            elif mutation == 'source':
                packet['catalogs']['sources']['records'][0]['authors'].reverse()
            elif mutation == 'rehash_source':
                descriptor = packet['input']['source_records'][0]
                descriptor['record']['authors'].reverse()
                descriptor['sha256'] = record_sha256(descriptor['record'])
                packet['spec_sha256'] = record_sha256(packet['input'])
            elif mutation == 'count':
                packet['report']['delta']['identities'] = 70
            elif mutation == 'admission':
                packet['report']['formal_admitted_delta'] = 7
            else:
                packet['report']['handoff_ready'] = not packet['report']['handoff_ready']
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'differs from exact replay'):
                validate_prepared_packet(packet, BASELINE)

    def test_candidate_measurements_do_not_claim_scientific_or_formal_admission(self):
        self.assertEqual(self.spec['review']['formal_admitted_delta'], 0)
        self.assertEqual(self.packet['report']['formal_admitted_delta'], 0)
        for prop in self.properties:
            self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
            self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
            self.assertEqual(prop['evaluation_support'], 'catalog_only')
            self.assertFalse(prop['universal_bound'])
            self.assertFalse(prop['engineering_allowable'])
            self.assertFalse(prop['verification']['independent_scientific_review'])
            self.assertFalse(prop['verification']['raw_data_reanalysis'])
        for mutation in ('independent_scientific_review', 'raw_data_reanalysis', 'admission'):
            spec = deepcopy(self.spec)
            if mutation == 'admission':
                spec['review']['formal_admitted_delta'] = 7
            else:
                spec['review']['verification'][mutation] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_spec(spec, BASELINE)


if __name__ == '__main__':
    unittest.main()
