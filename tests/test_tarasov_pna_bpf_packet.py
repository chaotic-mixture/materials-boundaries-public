"""Frozen Tarasov 2022 facts and candidate gates; no scientific admission."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.integrate_material_candidates import FILES, PIN_KEYS, TABLES, build_package, write_package
from scripts.prepare_formulation_packet import compile_spec, record_sha256, validate_prepared_packet, write_packet

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'experimental/material-batches/tarasov-pna-bpf-20261023'
BASELINE = ROOT / 'materials_boundaries/data'
BASE_COMMIT = 'faa002c55b7ad2d1bd962e905275894231ab8350'
SOURCE = 'tarasov_2022_pna_bpf_epoxy'
DOCUMENT_HASH = '1f06bc0667c7c5575a0e88772868a95cd27ba01a264d3b3a0b9c859a8a6423aa'
BASELINE_HASHES = {
    'materials': '9df59cfdf94b35854255222d2a75f419859b269c5670c8eb18d8e9dc5eaa7a70',
    'reference_properties': '728c863756c35860b4dee25b64f5df10c1b5273bcb83ed1f35d60cf6ad85aa77',
    'sources': 'c06c9bcee46eac59839c51f84b252970f1da46f98cf2f2c08de0b33479b5ba71',
}
# Independently transcribed from the original PDF, Tables 1 and 7 (pp.4,16).
# These are nominal author labels, not repaired or validated stoichiometry.
ROWS = (
    ('1', '1:8:16', '66.7'),
    ('2', '1:9:16', '66.0'),
    ('3', '1:12:16', '70.2'),
    ('4', '1:18:16', '74.5'),
    ('5', '1:24:16', '72.7'),
)


def read(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def explicit(spec, kind, record):
    spec['contexts'][kind]['test_explicit'] = {}
    return {'context': 'test_explicit', 'fields': deepcopy(record)}


class TarasovPnaBpfPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = read(BATCH / 'packet-spec.json')
        cls.packet = read(BATCH / 'prepared-packet.json')
        cls.baseline = {key: read(BASELINE / filename) for key, filename in FILES.items()}
        cls.package = build_package(BASELINE, BATCH / 'integration.json')

    def test_exact_five_source_rows_and_decimal_precision(self):
        self.assertEqual(self.spec['baseline_sha256'], BASELINE_HASHES)
        self.assertEqual(self.packet['report']['delta'], {
            'identities': 5, 'grades': 0, 'states': 5, 'properties': 5, 'sources': 1,
            'categories': {'metal': 0, 'inorganic': 0, 'polymer': 5, 'composite': 0, 'natural': 0},
        })
        self.assertTrue(self.packet['report']['handoff_ready'])
        self.assertEqual(self.packet['report']['formal_admitted_delta'], 0)
        graph = self.packet['catalogs']
        self.assertEqual(graph['materials']['grades'], [])
        for collection in ('identities', 'records'):
            self.assertEqual(len(graph['materials'][collection]), 5)
        self.assertEqual(len(graph['properties']['records']), 5)
        for index, (code, nominal, strength) in enumerate(ROWS):
            identity = graph['materials']['identities'][index]
            state = graph['materials']['records'][index]
            prop = graph['properties']['records'][index]
            with self.subTest(code=code):
                self.assertEqual(identity['id'], 'mat_tarasov2022_pna_bpf_' + code)
                self.assertEqual(identity['category'], 'polymer')
                self.assertIn('Tarasov', identity['name'])
                self.assertEqual(state['identity_id'], identity['id'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['source_designation'], 'PNA-BPF-' + code)
                self.assertIn(nominal, state['state']['composition_or_purity']['text'])
                self.assertEqual(state['property_ids'], [prop['id']])
                self.assertEqual(prop['material_state_id'], state['id'])
                self.assertEqual(prop['quantity'], 'tensile_strength')
                self.assertEqual(prop['quantity_dimension'], 'pressure')
                self.assertEqual(prop['reported_value'], {
                    'kind': 'scalar', 'value_text': strength, 'number': strength,
                    'unit_code': 'MPa', 'unit_text': 'MPa',
                })
                self.assertTrue(any('Table 7' in e['locator'] for e in prop['evidence']))

    def test_cured_state_and_tensile_method_do_not_supply_missing_statistics(self):
        for state, prop in zip(self.packet['catalogs']['materials']['records'],
                               self.packet['catalogs']['properties']['records']):
            with self.subTest(state=state['id']):
                state_text = json.dumps(state['state'], ensure_ascii=False)
                for text in ('DDS', '180', '8 h', '4 mm', '125', '100 mm Hg', '20-40 min'):
                    self.assertIn(text, state_text)
                self.assertIn('11262-2017', prop['conditions']['test_standard']['text'])
                self.assertIn('527-2:2012', prop['conditions']['test_standard']['text'])
                self.assertIn('10 mm/min', prop['conditions']['loading_rate']['text'])
                self.assertIn('50ST', prop['conditions']['test_method']['text'])
                for field in ('temperature', 'conditioning', 'direction'):
                    self.assertEqual(prop['conditions'][field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][field]['text'])
                self.assertEqual(prop['summary_statistic'], 'not_stated')
                self.assertEqual(prop['reporting_basis'], 'not_stated')
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                self.assertIsNone(prop['uncertainty'])
                self.assertEqual(prop['uncertainty_status'], 'not_reported_in_inspected_source')
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                for field in ('engineering_allowable', 'universal_bound'):
                    self.assertFalse(prop[field])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])

    def test_nominal_formulations_preserve_all_three_source_conflicts_and_exclusions(self):
        for prop in self.packet['catalogs']['properties']['records']:
            conflicts = json.dumps(prop['source_discrepancies'], ensure_ascii=False)
            with self.subTest(prop=prop['id']):
                self.assertEqual(len(prop['source_discrepancies']), 3)
                for token in ('ECH', '0.086', '0.101', 'potassium', 'NaOH'):
                    self.assertIn(token, conflicts)
        review = read(BATCH / 'source-review.json')
        text = json.dumps(review, ensure_ascii=False)
        for excluded in ('PNA-BPF-S', 'DGEBA', 'DGEBF'):
            self.assertIn(excluded, text)
            self.assertNotIn(excluded, [r['source_designation'] for r in self.packet['catalogs']['materials']['records']])
        for identity in self.packet['catalogs']['materials']['identities']:
            self.assertIn('nominal', identity['identity_scope'])
            self.assertIn('no correction, normalized stoichiometry, final network composition, purity, conversion or molecular architecture is inferred', identity['identity_scope'])
            self.assertIn('mixed phosphazene-containing epoxy formulations, not pure molecular species', identity['identity_scope'])

    def test_source_attribution_document_hash_and_finite_identity_review(self):
        source = self.packet['catalogs']['sources']['records'][0]
        self.assertEqual(source['id'], SOURCE)
        self.assertEqual(source['doi'], '10.3390/polym14214547')
        self.assertEqual(source['license'], {'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0'})
        self.assertEqual(len(source['authors']), 5)
        self.assertIn('https://creativecommons.org/licenses/by/4.0/', source['urls'])
        self.assertTrue(any('Changes:' in note for note in source['claim_notes']))
        self.assertEqual(record_sha256(source), self.spec['source_records'][0]['sha256'])
        for prop in self.packet['catalogs']['properties']['records']:
            self.assertEqual(prop['source_document']['sha256'], DOCUMENT_HASH)
        identity_review = read(BATCH / 'identity-review.json')
        self.assertEqual(identity_review['baseline_commit'], BASE_COMMIT)
        self.assertEqual(identity_review['baseline_counts']['new_admissions_in_this_audit'], 0)
        for field in ('scientific_review', 'scientific_replication', 'global_chemical_uniqueness_established'):
            self.assertIs(identity_review[field], False)
        for descriptor in identity_review['immutable_inputs']:
            raw = subprocess.check_output(['git', 'show', BASE_COMMIT + ':' + descriptor['path']], cwd=ROOT)
            with self.subTest(input=descriptor['path']):
                self.assertEqual(len(raw), descriptor['bytes'])
                self.assertEqual(sha256(raw).hexdigest(), descriptor['sha256'])
                self.assertEqual((ROOT / descriptor['path']).read_bytes(), raw)
        crosswalk = self.spec['identity_crosswalk']
        self.assertEqual(len(crosswalk), 5)
        self.assertEqual({r['disposition'] for r in crosswalk}, {'distinct'})
        self.assertEqual({r['source_id'] for r in crosswalk}, {SOURCE})
        self.assertEqual([r['source_designations'] for r in crosswalk], [['PNA-BPF-' + r[0]] for r in ROWS])
        self.assertFalse(any(p.suffix.lower() in ('.pdf', '.png', '.jpg', '.xlsx') for p in BATCH.rglob('*')))

    def test_isolated_report_preserves_all_baseline_bytes_and_does_not_admit(self):
        self.assertEqual(read(BATCH / 'integration-report.json'), self.package['report'])
        self.assertEqual(self.package['status'], 'experimental_only_formal_admission_pending')
        report = self.package['report']
        self.assertEqual(report['before']['identities'], 1148)
        self.assertEqual(report['after']['identities'], 1153)
        self.assertEqual(report['after']['states'], 1154)
        self.assertEqual(report['after']['properties'], 1165)
        self.assertEqual(report['after']['sources'], 125)
        self.assertEqual(report['after']['categories'], {'metal': 32, 'inorganic': 53, 'polymer': 30, 'composite': 28, 'natural': 1010})
        self.assertEqual(report['released_main_count'], 1081)
        self.assertEqual(report['formal_admitted_delta'], 0)
        recovered = deepcopy(self.package['catalogs'])
        for section, collection in TABLES.values():
            old = self.baseline[section][collection]
            self.assertEqual(recovered[section][collection][:len(old)], old)
            recovered[section][collection] = recovered[section][collection][:len(old)]
        for key, filename in FILES.items():
            raw = (BASELINE / filename).read_bytes()
            self.assertEqual(sha256(raw).hexdigest(), BASELINE_HASHES[PIN_KEYS[key]])
            self.assertEqual(encoded(recovered[key]), raw)
            self.assertEqual(subprocess.check_output(['git', 'show', BASE_COMMIT + ':materials_boundaries/data/' + filename], cwd=ROOT), raw)

    def test_receipt_and_candidate_commit_bind_actual_packet_bytes(self):
        receipt = read(BATCH / 'preparation-receipt.json')
        self.assertEqual(receipt['baseline_commit'], BASE_COMMIT)
        self.assertEqual(receipt['report'], self.packet['report'])
        for filename, descriptor in receipt['bound_files'].items():
            raw = (BATCH / filename).read_bytes()
            with self.subTest(file=filename):
                self.assertEqual(len(raw), descriptor['bytes'])
                self.assertEqual(sha256(raw).hexdigest(), descriptor['sha256'])
        manifest = read(BATCH / 'integration.json')
        candidate = manifest['batches'][0]['candidate_commit']
        self.assertNotEqual(candidate, BASE_COMMIT)
        for filename in ('packet-spec.json', 'prepared-packet.json', 'source-review.json', 'identity-review.json'):
            git_path = (BATCH / filename).relative_to(ROOT).as_posix()
            self.assertEqual(subprocess.check_output(['git', 'show', candidate + ':' + git_path], cwd=ROOT),
                             (BATCH / filename).read_bytes())

    def test_replay_is_deterministic_immutable_and_outside_runtime(self):
        before = {f: (BASELINE / f).read_bytes() for f in FILES.values()}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for writer, input_name, output_name in ((write_packet, 'packet-spec.json', 'packet.json'),
                                                    (write_package, 'integration.json', 'integrated.json')):
                output = root / output_name
                first, created = writer(BASELINE, BATCH / input_name, output)
                self.assertTrue(created)
                raw, mtime = output.read_bytes(), output.stat().st_mtime_ns
                again, created = writer(BASELINE, BATCH / input_name, output)
                self.assertFalse(created)
                self.assertEqual(first, again)
                self.assertEqual(output.read_bytes(), raw)
                self.assertEqual(output.stat().st_mtime_ns, mtime)
                if writer is write_packet:
                    self.assertEqual(raw, (BATCH / 'prepared-packet.json').read_bytes())
                output.write_bytes(b'sentinel\n')
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    writer(BASELINE, BATCH / input_name, output)
                self.assertEqual(output.read_bytes(), b'sentinel\n')
        self.assertEqual(before, {f: (BASELINE / f).read_bytes() for f in FILES.values()})
        with self.assertRaisesRegex(ValueError, 'outside baseline'):
            write_packet(BASELINE, BATCH / 'packet-spec.json', BASELINE / 'forbidden.json')

    def test_invalid_pin_owner_missing_property_unit_and_scientific_upgrade_fail_atomically(self):
        for mutation in ('baseline_pin', 'source_pin', 'owner', 'missing_property', 'unit', 'scientific_upgrade'):
            spec = deepcopy(self.spec)
            state = spec['formulations'][0]['states'][0]
            prop = deepcopy(self.packet['catalogs']['properties']['records'][0])
            if mutation == 'baseline_pin':
                spec['baseline_sha256']['materials'] = '0' * 64
            elif mutation == 'source_pin':
                spec['source_records'][0]['sha256'] = '0' * 64
            elif mutation == 'owner':
                prop['material_state_id'] = self.packet['catalogs']['materials']['records'][1]['id']
                state['properties'][0] = explicit(spec, 'property', prop)
            elif mutation == 'missing_property':
                state['properties'] = []
            elif mutation == 'unit':
                prop['reported_value'].update(unit_code='g/cm^3', unit_text='g/cm^3')
                state['properties'][0] = explicit(spec, 'property', prop)
            else:
                spec['review']['verification']['independent_scientific_review'] = True
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'spec.json'
                path.write_bytes(encoded(spec))
                output = Path(directory) / 'packet.json'
                with self.assertRaises(ValueError):
                    write_packet(BASELINE, path, output)
                self.assertFalse(output.exists())
                self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_pending_identity_transcription_and_rights_cannot_integrate(self):
        for mutation in ('identity', 'transcription', 'rights'):
            spec = deepcopy(self.spec)
            if mutation == 'identity':
                spec['identity_crosswalk'][0]['disposition'] = 'pending'
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
                packet, _ = write_packet(BASELINE, path, batch / 'packet.json', repository_root=root)
                self.assertFalse(packet['report']['handoff_ready'])
                self.assertTrue(packet['report']['pending_gates'])
                manifest = read(BATCH / 'integration.json')
                manifest['batches'][0]['packet'] = {'path': 'packet.json', 'sha256': sha256((batch / 'packet.json').read_bytes()).hexdigest()}
                (batch / 'integration.json').write_bytes(encoded(manifest))
                with self.assertRaisesRegex(ValueError, 'pending identity/source review'):
                    write_package(BASELINE, batch / 'integration.json', root / 'output.json', repository_root=root)
                self.assertFalse((root / 'output.json').exists())

    def test_duplicate_alias_or_designation_cannot_manufacture_an_identity(self):
        for mutation in ('alias', 'designation'):
            spec = deepcopy(self.spec)
            if mutation == 'alias':
                identity = deepcopy(self.packet['catalogs']['materials']['identities'][1])
                identity['aliases'].append({'language': 'und', 'text': '  pna-bpf-1  '})
                spec['formulations'][1]['identity'] = explicit(spec, 'identity', identity)
            else:
                state = deepcopy(self.packet['catalogs']['materials']['records'][1])
                state['source_designation'] = 'PNA-BPF-1'
                spec['formulations'][1]['states'][0]['record'] = explicit(spec, 'state', state)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'collides'):
                compile_spec(spec, BASELINE)

    def test_additional_state_does_not_increase_identity_count(self):
        spec = deepcopy(self.spec)
        state = deepcopy(self.packet['catalogs']['materials']['records'][0])
        prop = deepcopy(self.packet['catalogs']['properties']['records'][0])
        # Synthetic plumbing mutation: no new scientific state is asserted.
        state['id'] += '_test_only'
        prop['id'] += '_test_only'
        prop['material_state_id'] = state['id']
        state['property_ids'] = [prop['id']]
        spec['formulations'][0]['states'].append({
            'record': explicit(spec, 'state', state),
            'properties': [explicit(spec, 'property', prop)],
        })
        with self.assertRaisesRegex(ValueError, 'duplicate structural state'):
            compile_spec(spec, BASELINE)
        # A deliberately fictional second specimen form exercises state counting;
        # this altered fixture is never saved as a source-supported candidate.
        state['state']['product_form']['text'] = 'Synthetic alternate specimen form for state-count regression only.'
        spec['formulations'][0]['states'][-1]['record'] = explicit(spec, 'state', state)
        report = compile_spec(spec, BASELINE)['report']
        self.assertEqual(report['delta']['identities'], 5)
        self.assertEqual(report['delta']['states'], 6)
        self.assertEqual(report['delta']['properties'], 6)
        self.assertEqual(report['formal_admitted_delta'], 0)

    def test_forged_values_counts_or_readiness_do_not_replace_replay(self):
        for mutation in ('value', 'count', 'admission', 'ready'):
            packet = deepcopy(self.packet)
            if mutation == 'value':
                packet['catalogs']['properties']['records'][1]['reported_value']['number'] = '660'
            elif mutation == 'count':
                packet['report']['delta']['identities'] = 6
            elif mutation == 'admission':
                packet['report']['formal_admitted_delta'] = 5
            else:
                packet['report']['handoff_ready'] = False
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'differs from exact replay'):
                validate_prepared_packet(packet, BASELINE)


if __name__ == '__main__':
    unittest.main()
