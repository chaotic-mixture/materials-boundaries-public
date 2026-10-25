"""Exact source-qualified Tarasov recipes through installed query and CLI APIs.

Resolution hashes freeze the approved candidate objects, including every
condition, unknown and discrepancy. Numerical expectations are explicit Table 7
transcriptions; nominal feed labels do not establish final composition.
"""
from hashlib import sha256
import json
import subprocess
import sys
import unittest

from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query.catalog_snapshot import CatalogSnapshot


SOURCE = 'tarasov_2022_pna_bpf_epoxy'
FACTS = ((1, '1:8:16', '66.7'), (2, '1:9:16', '66.0'),
         (3, '1:12:16', '70.2'), (4, '1:18:16', '74.5'),
         (5, '1:24:16', '72.7'))
RESOLVED_SHA256 = {
    'state_tarasov2022_pna_bpf_1_dds_cured': '529097aa68b55900b3b3906921d319924774c6eb5b5a8eadad30711ea765b916',
    'state_tarasov2022_pna_bpf_2_dds_cured': 'f5961ff67f70284f8940eaee0aaf777796e918e9d4df15c972c980fbed9626cd',
    'state_tarasov2022_pna_bpf_3_dds_cured': 'c756aec296f802b0e41748f8747cfea6af233d1cad67c047e0c25d5b7cf94cbd',
    'state_tarasov2022_pna_bpf_4_dds_cured': 'd108e6a8014bd616d98b209a33a2f683c51412ec42af3471d3b4f3440fbb4326',
    'state_tarasov2022_pna_bpf_5_dds_cured': 'b9e35b095de17c25b5532cf5a183c25649251d10062dd544e6d260a5e3da7786',
}


class TarasovPNABPFQuery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(create_app(enable_local_catalog=True))
        cls.status = cls.client.get('/api/catalog/status').json()
        assert cls.status['enabled'], cls.status
        cls.version = cls.status['version']

    def post(self, route, **data):
        response = self.client.post('/api/catalog/' + route,
                                   json={'version': self.version, **data})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['result']

    def cli(self, kind, *args):
        result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'materials_boundaries',
                                 'catalog', kind, '--json', *args],
                                capture_output=True, text=True, encoding='utf-8', check=True)
        return json.loads(result.stdout)

    def test_five_nominal_recipes_keep_exact_measured_joins_and_unknowns(self):
        self.assertEqual(self.status['counts'], {
            'local_catalog_unique_material_count': 1164,
            'local_material_state_count': 1165,
            'local_reference_property_count': 1176})
        for number, ratio, value in FACTS:
            with self.subTest(recipe=number):
                identity_id = f'mat_tarasov2022_pna_bpf_{number}'
                state_id = f'state_tarasov2022_pna_bpf_{number}_dds_cured'
                property_id = f'refprop_tarasov2022_pna_bpf_{number}_tensile_strength'
                resolved = self.post('resolve', state_id=state_id)
                canonical = json.dumps(resolved, sort_keys=True, separators=(',', ':'),
                                       ensure_ascii=False, allow_nan=False).encode()
                self.assertEqual(sha256(canonical).hexdigest(), RESOLVED_SHA256[state_id])
                identity, state = resolved['identity'], resolved['state']
                self.assertEqual(identity['id'], identity_id)
                self.assertEqual(identity['category'], 'polymer')
                self.assertIn('not pure molecular species', identity['identity_scope'])
                self.assertIn(ratio, identity['identity_scope'])
                self.assertIsNone(resolved['grade'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['identity_id'], identity_id)
                self.assertEqual(state['source_designation'], f'PNA-BPF-{number}')
                self.assertEqual(state['property_ids'], [property_id])
                self.assertEqual(state['state']['temper_or_heat_treatment']['text'],
                                 'Cured at 180 deg C for 8 h.')
                self.assertEqual(state['state']['reinforcement']['status'], 'not_applicable')
                self.assertIn('100 mm Hg', state['state']['processing']['text'])
                self.assertIn('20-40 min', state['state']['processing']['text'])
                self.assertIn('125 deg C', state['state']['processing']['text'])
                self.assertEqual(len(resolved['properties']), 1)
                prop = resolved['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['material_state_id'], state_id)
                self.assertEqual(prop['source_id'], SOURCE)
                self.assertEqual(prop['quantity'], 'tensile_strength')
                self.assertEqual(prop['reported_value'], {
                    'kind': 'scalar', 'unit_text': 'MPa', 'unit_code': 'MPa',
                    'value_text': value, 'number': value})
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['summary_statistic'], 'not_stated')
                self.assertEqual(prop['reporting_basis'], 'not_stated')
                self.assertIsNone(prop['uncertainty'])
                self.assertEqual(prop['uncertainty_status'], 'not_reported_in_inspected_source')
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                self.assertIsNone(prop['method_definition']['extraction_window'])
                self.assertEqual(prop['conditions']['test_standard']['text'],
                                 'GOST 11262-2017 (ISO 527-2:2012).')
                self.assertEqual(prop['conditions']['loading_rate']['text'],
                                 'Stretching speed 10 mm/min.')
                for key in ('temperature', 'conditioning', 'direction'):
                    self.assertEqual(prop['conditions'][key]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][key]['text'])
                additional = {row['name']: row['fact'] for row in prop['conditions']['additional_conditions']}
                self.assertIsNone(additional['relative_humidity']['text'])
                self.assertEqual(additional['specimen_plate_thickness']['text'], '4 mm-thick plate.')
                self.assertEqual(len(prop['source_discrepancies']), 3)
                discrepancies = json.dumps(prop['source_discrepancies'])
                for literal in ('1:24:16', '35 (0.086)', '35 (0.101)', 'potassium hydroxide', 'NaOH'):
                    self.assertIn(literal, discrepancies)
                self.assertFalse(prop['universal_bound'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertEqual([row['id'] for row in resolved['sources']], [SOURCE])
                source = resolved['sources'][0]
                self.assertEqual(source['doi'], '10.3390/polym14214547')
                self.assertEqual(source['license']['identifier'], 'CC-BY-4.0')
                self.assertEqual(prop['source_document']['sha256'],
                                 '1f06bc0667c7c5575a0e88772868a95cd27ba01a264d3b3a0b9c859a8a6423aa')

    def test_installed_cli_and_api_preserve_exact_objects_and_source_precision(self):
        for number, _, _ in FACTS:
            with self.subTest(recipe=number):
                resolved = self.post('resolve', state_id=f'state_tarasov2022_pna_bpf_{number}_dds_cured')
                selected = self.cli('materials', '--identity-id', resolved['identity']['id'])
                self.assertEqual(selected['records'], [resolved['state']])
                self.assertEqual(selected['identities'], [resolved['identity']])
                self.assertEqual(selected['grades'], [])
                selected = self.cli('reference-properties', '--id', resolved['properties'][0]['id'])
                self.assertEqual(selected['records'], resolved['properties'])
        expected = [self.post('resolve', state_id=f'state_tarasov2022_pna_bpf_{n}_dds_cured')['properties'][0]
                    for n, _, _ in FACTS]
        for language in ('en', 'zh', 'ja', 'de'):
            with self.subTest(language=language):
                self.assertEqual(self.cli('reference-properties', '--source-id', SOURCE,
                                          '--lang', language)['records'], expected)
        self.assertEqual(self.cli('sources', '--id', SOURCE)['records'], resolved['sources'])

    def test_formal_count_uses_five_identities_and_excludes_controls_and_computed(self):
        status = self.client.get('/api/catalog/project/status').json()
        self.assertTrue(status['enabled'])
        self.assertEqual(status['counts'], {
            'formal_project_admission_count': 1188,
            'legacy_source_qualified_identity_count': 1164,
            'reviewed_computed_composition_count': 24,
            'categories': {'metal': 44, 'inorganic': 71, 'polymer': 30,
                           'composite': 33, 'natural': 1010}})
        data = {'version': status['version'], 'query': 'tarasov2022_pna_bpf',
                'partition': 'legacy-source-qualified', 'limit': 100}
        selected = self.client.post('/api/catalog/project/list', json=data)
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 5)
        self.assertEqual({row['id'] for row in selected.json()['records']}, {
            f'legacy:mat_tarasov2022_pna_bpf_{n}' for n, _, _ in FACTS})
        self.assertTrue(all(row['category'] == 'polymer' for row in selected.json()['records']))
        selected = self.client.post('/api/catalog/project/list', json={**data, 'partition': 'reviewed-computed'})
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 0)
        states = self.post('search', query='tarasov2022_pna_bpf', limit=100)
        self.assertEqual({row['id'] for row in states['records']}, set(RESOLVED_SHA256))
        self.assertFalse(states['truncated'])
        for excluded in ('PNA-BPF-S', 'DGEBA', 'DGEBF'):
            selected = self.post('search', query='tarasov2022_pna_bpf ' + excluded, limit=100)
            self.assertEqual(selected['records'], [])
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)

    def test_resolved_objects_are_detached_and_cannot_rewrite_qualifications(self):
        snapshot = CatalogSnapshot.from_packaged()
        state_id = 'state_tarasov2022_pna_bpf_2_dds_cured'
        before = snapshot.resolve(state_id)
        changed = snapshot.resolve(state_id)
        changed['identity']['category'] = 'composite'
        changed['properties'][0]['reported_value']['number'] = '66'
        changed['properties'][0]['source_discrepancies'].clear()
        changed['properties'][0]['uncertainty'] = {'number': '0'}
        changed['state']['state']['composition_or_purity']['text'] = 'Validated exact composition'
        changed['sources'][0]['license']['identifier'] = 'unverified'
        self.assertEqual(snapshot.resolve(state_id), before)
        self.assertEqual(self.post('resolve', state_id=state_id), before)
