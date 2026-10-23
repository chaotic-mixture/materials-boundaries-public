"""Bounded Bruns 2020 candidate checks; no runtime or scientific admission."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

import material_append_successors as successors
from material_append_history import recover_catalogs

from scripts.integrate_material_candidates import (
    FILES, PIN_KEYS, TABLES, build_package, write_package,
)
from scripts.prepare_formulation_packet import (
    compile_spec, record_sha256, validate_prepared_packet, write_packet,
)

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'experimental/material-batches/bruns-nbs2-borosilicate-20261023'
BASELINE = ROOT / 'materials_boundaries/data'
SOURCE = 'bruns_2020_alumina_borosilicate'
DOCUMENT_HASH = 'c6268f9f14320e9355bfe04bf02f47eb3d7ca00e30c7281a16fd3b1289913da6'
BASELINE_HASHES = {
    'materials': 'd228c3b8f0c45fd56809891213d1d1acd73964357b579c51f8b9c731031a3ec5',
    'reference_properties': '66802278a29cdcc4a5fe468b5681d87893a8a10a7c6c4c57f83c4753fe807839',
    'sources': '67e068041af0cd8dbaba1126e6ffe2e39d2f8d26f8d2c8ceefc42240e5eefe76',
}
# Independent, visually checked transcription oracle: Table 1 and Table 3.
ROWS = (
    ('1p0', '1.0', ('74.00', '20.70', '4.30', '1.00'), ('69.75', '25.59', '3.32', '1.33'), '2.131', '0.006'),
    ('1p5', '1.5', ('73.62', '20.60', '4.28', '1.50'), ('68.34', '26.35', '3.47', '1.82'), '2.133', '0.010'),
    ('2p0', '2.0', ('73.25', '20.49', '4.26', '2.00'), ('68.60', '25.77', '3.34', '2.28'), '2.130', '0.002'),
    ('4p0', '4.0', ('71.76', '20.07', '4.17', '4.00'), ('68.22', '24.57', '3.40', '3.81'), '2.137', '0.004'),
)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


class BrunsBorosilicatePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = read(BATCH / 'packet-spec.json')
        cls.packet = read(BATCH / 'prepared-packet.json')
        cls.current = {key: read(BASELINE / filename) for key, filename in FILES.items()}
        cls.baseline = recover_catalogs(ROOT, cls.current, successors.data_ledger(BATCH.name))
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.baseline_dir = Path(temporary.name)
        for key, filename in FILES.items():
            (cls.baseline_dir / filename).write_bytes(encoded(cls.baseline[key]))
        cls.package = build_package(cls.baseline_dir, BATCH / 'integration.json')

    def test_frozen_packet_matches_four_source_recipes_and_density_cells(self):
        self.assertEqual(self.spec['baseline_sha256'], BASELINE_HASHES)
        self.assertEqual(self.packet['report']['delta'], {
            'identities': 4, 'grades': 0, 'states': 4, 'properties': 4, 'sources': 1,
            'categories': {'metal': 0, 'inorganic': 4, 'polymer': 0, 'composite': 0, 'natural': 0},
        })
        self.assertEqual(self.packet['report']['formal_admitted_delta'], 0)
        self.assertTrue(self.packet['report']['handoff_ready'])
        graph = self.packet['catalogs']
        self.assertEqual(len(graph['materials']['identities']), 4)
        self.assertEqual(len(graph['materials']['records']), 4)
        self.assertEqual(graph['materials']['grades'], [])
        self.assertEqual(len(graph['properties']['records']), 4)
        self.assertEqual(len(graph['sources']['records']), 1)
        for index, (code, label, nominal, assay, mean, sd) in enumerate(ROWS):
            identity = graph['materials']['identities'][index]
            state = graph['materials']['records'][index]
            prop = graph['properties']['records'][index]
            facts = self.spec['review']['candidate_facts'][index]
            with self.subTest(row=label):
                self.assertEqual(identity['id'], 'mat_bruns2020_nbs2_al' + code)
                self.assertEqual(identity['category'], 'inorganic')
                self.assertEqual(state['identity_id'], identity['id'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(prop['material_state_id'], state['id'])
                self.assertEqual(state['property_ids'], [prop['id']])
                self.assertEqual(prop['reported_value']['value_text'], mean)
                self.assertEqual(prop['reported_value']['number'], mean)
                self.assertEqual(prop['uncertainty']['value_text'], sd)
                self.assertEqual(prop['uncertainty']['number'], sd)
                self.assertEqual(prop['reported_value']['unit_code'], 'g/cm^3')
                self.assertEqual(prop['uncertainty']['unit_code'], 'g/cm^3')
                self.assertEqual(prop['summary_statistic'], 'reported_mean')
                self.assertEqual(prop['uncertainty']['type'], 'reported_standard_deviation')
                self.assertIsNone(prop['uncertainty']['confidence_level'])
                self.assertIsNone(prop['uncertainty']['coverage_factor'])
                self.assertEqual(tuple(facts['nominal_oxide_mol_percent'].values()), nominal)
                self.assertEqual(tuple(facts['icp_oes_oxide_mol_percent'].values()), assay)
                self.assertEqual(sum(map(Decimal, nominal)), Decimal('100'))
                composition = state['state']['composition_or_purity']['text']
                self.assertIn('Nominal mol%', composition)
                self.assertIn('Separately reported ICP-OES mol%', composition)
                self.assertTrue(prop['source_discrepancies'])
                self.assertEqual(facts['table_3_label'], label)
                self.assertIn('without qu.', facts['density_locator'])
                self.assertTrue(any('PDF p.8 Table 3' in e['locator'] for e in prop['evidence']))

    def test_count_method_unknowns_and_four_percent_cooling_exception(self):
        for index, prop in enumerate(self.packet['catalogs']['properties']['records']):
            with self.subTest(index=index):
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                self.assertIn('at least five pieces', prop['sample_count']['source_statement'])
                self.assertIn('not asserted to be five independent', prop['sample_count']['scope'])
                self.assertEqual(prop['conditions']['test_method']['text'], 'Archimedes method in toluene.')
                for field in ('temperature', 'conditioning', 'test_standard'):
                    self.assertEqual(prop['conditions'][field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][field]['text'])
                pressure = prop['conditions']['additional_conditions'][0]['fact']
                self.assertEqual(pressure['status'], 'not_reported_in_inspected_source')
                self.assertEqual(prop['density_basis'], 'not_stated')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertFalse(prop['universal_bound'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
        states = self.packet['catalogs']['materials']['records']
        for state in states[:3]:
            self.assertIn('500 °C', state['state']['temper_or_heat_treatment']['text'])
            self.assertIn('30 K/h', state['state']['temper_or_heat_treatment']['text'])
        special = states[-1]['state']['temper_or_heat_treatment']
        self.assertIn('too viscous to pour', special['text'])
        self.assertIn('crucible', special['text'])
        self.assertIn('drilled', special['text'])
        for forbidden in ('500', '30 K/h', 'graphite'):
            self.assertNotIn(forbidden, special['text'])
        self.assertIn('No graphite-mold casting', special['notes'])

    def test_source_attribution_hash_and_candidate_receipt_remain_bound(self):
        source = self.packet['catalogs']['sources']['records'][0]
        self.assertEqual(source['id'], SOURCE)
        self.assertEqual(source['doi'], '10.3389/fmats.2020.00189')
        self.assertEqual(source['license'], {'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0'})
        self.assertIn('https://creativecommons.org/licenses/by/4.0/', source['urls'])
        self.assertEqual(len(source['authors']), 7)
        self.assertTrue(any('Changes:' in note for note in source['claim_notes']))
        self.assertEqual(record_sha256(source), self.spec['source_records'][0]['sha256'])
        self.assertEqual(read(BATCH / 'source-review.json')['source'], source)
        for prop in self.packet['catalogs']['properties']['records']:
            self.assertEqual(prop['source_document']['sha256'], DOCUMENT_HASH)
        for filename, descriptor in read(BATCH / 'preparation-receipt.json')['bound_files'].items():
            raw = (BATCH / filename).read_bytes()
            self.assertEqual(sha256(raw).hexdigest(), descriptor['sha256'])
            self.assertEqual(len(raw), descriptor['bytes'])
        self.assertFalse(any(p.suffix in ('.pdf', '.png', '.jpg') for p in BATCH.rglob('*')))

    def test_isolated_integration_preserves_every_predecessor_record_and_byte(self):
        self.assertEqual(self.current, self.package['catalogs'])
        report = self.package['report']
        self.assertEqual(report['delta'], self.packet['report']['delta'])
        self.assertEqual(report['after']['identities'], 1148)
        self.assertEqual(report['after']['states'], 1149)
        self.assertEqual(report['after']['properties'], 1160)
        self.assertEqual(report['after']['sources'], 124)
        self.assertEqual(report['released_main_count'], 1081)
        self.assertEqual(report['formal_admitted_delta'], 0)
        recovered = deepcopy(self.package['catalogs'])
        for _, (section, collection) in TABLES.items():
            baseline_rows = self.baseline[section][collection]
            self.assertEqual(recovered[section][collection][:len(baseline_rows)], baseline_rows)
            recovered[section][collection] = recovered[section][collection][:len(baseline_rows)]
        for section, filename in FILES.items():
            original = (self.baseline_dir / filename).read_bytes()
            self.assertEqual(encoded(recovered[section]), original)
            self.assertEqual(sha256(original).hexdigest(), BASELINE_HASHES[PIN_KEYS[section]])
        self.assertEqual(read(BATCH / 'integration-report.json'), report)

    def test_compiler_and_integrator_replay_are_deterministic_immutable_and_detached(self):
        before = {filename: (self.baseline_dir / filename).read_bytes() for filename in FILES.values()}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'packet.json'
            packet, created = write_packet(self.baseline_dir, BATCH / 'packet-spec.json', output)
            self.assertTrue(created)
            self.assertEqual(output.read_bytes(), (BATCH / 'prepared-packet.json').read_bytes())
            self.assertFalse(write_packet(self.baseline_dir, BATCH / 'packet-spec.json', output)[1])
            integrated = Path(directory) / 'integrated.json'
            package, created = write_package(self.baseline_dir, BATCH / 'integration.json', integrated)
            self.assertTrue(created)
            self.assertEqual(package, self.package)
            self.assertFalse(write_package(self.baseline_dir, BATCH / 'integration.json', integrated)[1])
            output.write_text('sentinel\n')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                write_packet(self.baseline_dir, BATCH / 'packet-spec.json', output)
            self.assertEqual(output.read_text(), 'sentinel\n')
            integrated.write_text('sentinel\n')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                write_package(self.baseline_dir, BATCH / 'integration.json', integrated)
            self.assertEqual(integrated.read_text(), 'sentinel\n')
        self.assertEqual(before, {filename: (self.baseline_dir / filename).read_bytes() for filename in FILES.values()})

    def test_bad_pin_owner_unit_and_statistic_refuse_atomic_output(self):
        for mutation in ('baseline_pin', 'source_pin', 'owner', 'unit', 'sd_as_value', 'scientific_upgrade'):
            spec = deepcopy(self.spec)
            prop = spec['formulations'][-1]['states'][0]['properties'][0]['fields']
            if mutation == 'baseline_pin':
                spec['baseline_sha256']['materials'] = '0' * 64
            elif mutation == 'source_pin':
                spec['source_records'][0]['sha256'] = '0' * 64
            elif mutation == 'owner':
                prop['material_state_id'] = self.packet['catalogs']['materials']['records'][0]['id']
            elif mutation == 'unit':
                prop['reported_value'].update(unit_text='MPa', unit_code='MPa')
            elif mutation == 'sd_as_value':
                spec['contexts']['property']['archimedes_density']['summary_statistic'] = 'reported_value'
            else:
                spec['review']['verification']['independent_scientific_review'] = True
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'spec.json'
                path.write_bytes(encoded(spec))
                output = Path(directory) / 'packet.json'
                with self.assertRaises(ValueError):
                    write_packet(self.baseline_dir, path, output)
                self.assertFalse(output.exists())
                self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_pending_identity_source_and_rights_cannot_integrate(self):
        for mutation in ('identity', 'transcription', 'rights'):
            spec = deepcopy(self.spec)
            if mutation == 'identity':
                spec['identity_crosswalk'][-1]['disposition'] = 'pending'
            elif mutation == 'transcription':
                spec['review']['source_reviews'][0]['status'] = 'pending'
            else:
                descriptor = spec['source_records'][0]
                descriptor['record']['license'] = {'status': 'unverified', 'identifier': None}
                descriptor['sha256'] = record_sha256(descriptor['record'])
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                batch = root / 'experimental/material-batches/check'
                batch.mkdir(parents=True)
                path = batch / 'spec.json'
                path.write_bytes(encoded(spec))
                packet, _ = write_packet(self.baseline_dir, path, batch / 'packet.json', repository_root=root)
                self.assertFalse(packet['report']['handoff_ready'])
                self.assertTrue(packet['report']['pending_gates'])
                manifest = read(BATCH / 'integration.json')
                manifest['batches'][0]['packet'] = {'path': 'packet.json', 'sha256': sha256((batch / 'packet.json').read_bytes()).hexdigest()}
                (batch / 'integration.json').write_bytes(encoded(manifest))
                with self.assertRaisesRegex(ValueError, 'pending identity/source review'):
                    write_package(self.baseline_dir, batch / 'integration.json', root / 'output.json', repository_root=root)
                self.assertFalse((root / 'output.json').exists())

    def test_forged_packet_and_source_scoped_collision_cannot_upgrade(self):
        packet = deepcopy(self.packet)
        packet['report']['formal_admitted_delta'] = 4
        with self.assertRaisesRegex(ValueError, 'differs from exact replay'):
            validate_prepared_packet(packet, self.baseline_dir)
        spec = deepcopy(self.spec)
        spec['formulations'][1]['states'][0]['record']['fields']['source_designation'] = spec['formulations'][0]['states'][0]['record']['fields']['source_designation']
        with self.assertRaises(ValueError):
            compile_spec(spec, self.baseline_dir)
        with self.assertRaisesRegex(ValueError, 'outside baseline'):
            write_packet(self.baseline_dir, BATCH / 'packet-spec.json', self.baseline_dir / 'forbidden.json')
        with self.assertRaisesRegex(ValueError, 'formal catalog data'):
            write_package(self.baseline_dir, BATCH / 'integration.json', ROOT / 'formal-catalog/materials_project_catalog/data/forbidden.json')


if __name__ == '__main__':
    unittest.main()
