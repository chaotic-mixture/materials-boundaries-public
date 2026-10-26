"""Exact Tian nominal composite density facts through installed API and CLI."""
from hashlib import sha256
import json
import subprocess
import sys
import unittest

from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query.catalog_snapshot import CatalogSnapshot


SOURCE = 'tian_2023_nano_ti_az31'
FACTS = (
    ('0p5wt', '0.5 wt% Ti', '0.5', '1.7425'),
    ('1wt', '1 wt Ti', '1', '1.7442'),
)
AUTHORS = ['Wei Tian', 'Pengfei Gao', 'Shengli Han', 'Xiaohong Chen',
           'Fuwei Zhang', 'Yuhui Zhang', 'Tiegang Luo', 'Kaihong Zheng']
# Canonical hashes of exact resolved objects assembled from approved candidate
# 497dcc8, independent of the installed snapshot under test.
RESOLVED_SHA256 = {'state_tian2023_az31_ti_0p5wt_as_extruded': '4d5521b6548dc5c85d6755f8996fed5ec739f1aa7d1e82f7b780c31e04b84ebf', 'state_tian2023_az31_ti_1wt_as_extruded': '9e7444f8775064e378215ce25f3870353d1502aee73e97984c92693f57f20bac'}


class TianNanoTiQuery(unittest.TestCase):
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

    def test_two_nominal_composites_keep_exact_density_joins_and_unknowns(self):
        self.assertEqual(self.status['counts'], {
            'local_catalog_unique_material_count': 1175,
            'local_material_state_count': 1176,
            'local_reference_property_count': 1187})
        for key, label, loading, density in FACTS:
            with self.subTest(formulation=key):
                identity_id = 'mat_tian2023_az31_ti_' + key
                state_id = 'state_tian2023_az31_ti_' + key + '_as_extruded'
                property_id = 'refprop_tian2023_az31_ti_' + key + '_mass_density'
                resolved = self.post('resolve', state_id=state_id)
                raw = json.dumps(resolved, sort_keys=True, separators=(',', ':'),
                                 ensure_ascii=False, allow_nan=False).encode('utf-8')
                self.assertEqual(sha256(raw).hexdigest(), RESOLVED_SHA256[state_id])
                identity, state = resolved['identity'], resolved['state']
                self.assertEqual(identity['id'], identity_id)
                self.assertEqual(identity['category'], 'composite')
                self.assertIn('(Tian 2023)', identity['name'])
                self.assertIn('nominal', identity['identity_scope'])
                self.assertIsNone(resolved['grade'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['identity_id'], identity_id)
                self.assertEqual(state['source_designation'], label)
                self.assertEqual(state['property_ids'], [property_id])
                self.assertEqual(state['state']['composition_or_purity']['text'],
                                 'Mg-3Al-1Zn (AZ31) matrix with nominal ' + loading + ' wt% nano-Ti addition.')
                self.assertIn('not an analyzed final composition', state['state']['composition_or_purity']['notes'])
                self.assertIsNone(state['state']['porosity']['text'])
                self.assertEqual(len(resolved['properties']), 1)
                prop = resolved['properties'][0]
                self.assertEqual((prop['id'], prop['material_state_id'], prop['source_id']),
                                 (property_id, state_id, SOURCE))
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value'], {'kind': 'scalar', 'unit_text': 'g/cm3',
                    'unit_code': 'g/cm^3', 'value_text': density, 'number': density})
                self.assertEqual(prop['source_property_label'], 'Actual Density (g/cm3)')
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                for field in ('summary_statistic', 'reporting_basis', 'density_basis'):
                    self.assertEqual(prop[field], 'not_stated')
                self.assertIsNone(prop['uncertainty'])
                self.assertEqual(prop['uncertainty_status'], 'not_reported_in_inspected_source')
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                self.assertIn('three tensile specimens', prop['sample_count']['scope'])
                self.assertEqual(prop['conditions']['test_method']['text'], 'Digital densimeter.')
                for field in ('temperature', 'test_standard', 'conditioning'):
                    self.assertEqual(prop['conditions'][field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][field]['text'])
                extra = {row['name']: row['fact'] for row in prop['conditions']['additional_conditions']}
                for field in ('density_pressure', 'measurement_repetitions'):
                    self.assertEqual(extra[field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(extra[field]['text'])
                self.assertIn('1 wt Ti', prop['source_discrepancies'][0]['description'])
                self.assertIn('1 wt%', prop['source_discrepancies'][0]['disposition'])
                self.assertFalse(prop['universal_bound'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                source, = resolved['sources']
                self.assertEqual(source['id'], SOURCE)
                self.assertEqual(source['doi'], '10.3390/ma16062407')
                self.assertEqual(source['authors'], AUTHORS)
                self.assertEqual(source['license']['identifier'], 'CC-BY-4.0')
                self.assertEqual(prop['source_document']['sha256'],
                                 '8df98d0b465e5bef857d9eaa0ff0969e0c22b4f35aa5a7c64e6e59150b08afad')
                self.assertIn('primary-host SHA-256 byte equivalence remain unverified',
                              prop['source_document']['inspection_scope'])

    def test_installed_cli_and_api_preserve_exact_objects_and_authorship(self):
        expected = []
        for key, _, _, _ in FACTS:
            resolved = self.post('resolve', state_id='state_tian2023_az31_ti_' + key + '_as_extruded')
            selected = self.cli('materials', '--identity-id', resolved['identity']['id'])
            self.assertEqual(selected['records'], [resolved['state']])
            self.assertEqual(selected['identities'], [resolved['identity']])
            self.assertEqual(selected['grades'], [])
            self.assertEqual(self.cli('reference-properties', '--id', resolved['properties'][0]['id'])['records'],
                             resolved['properties'])
            expected.extend(resolved['properties'])
        expected.sort(key=lambda row: row['id'])
        for language in ('en', 'zh', 'ja', 'de'):
            with self.subTest(language=language):
                self.assertEqual(self.cli('reference-properties', '--source-id', SOURCE,
                                          '--lang', language)['records'], expected)
        sources = self.cli('sources', '--id', SOURCE)['records']
        self.assertEqual(sources, resolved['sources'])
        self.assertEqual(sources[0]['authors'], AUTHORS)

    def test_formal_count_excludes_computed_and_rejects_stale_versions(self):
        status = self.client.get('/api/catalog/project/status').json()
        self.assertTrue(status['enabled'])
        self.assertEqual(status['counts'], {
            'formal_project_admission_count': 1199,
            'legacy_source_qualified_identity_count': 1175,
            'reviewed_computed_composition_count': 24,
            'categories': {'metal': 44, 'inorganic': 71, 'polymer': 37,
                           'composite': 37, 'natural': 1010}})
        data = {'version': status['version'], 'query': 'tian2023',
                'partition': 'legacy-source-qualified', 'limit': 100}
        selected = self.client.post('/api/catalog/project/list', json=data)
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 2)
        self.assertEqual({row['id'] for row in selected.json()['records']}, {
            'legacy:mat_tian2023_az31_ti_' + key for key, _, _, _ in FACTS})
        selected = self.client.post('/api/catalog/project/list', json={**data, 'partition': 'reviewed-computed'})
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 0)
        states = self.post('search', query='tian2023', limit=100)
        self.assertEqual({row['id'] for row in states['records']}, set(RESOLVED_SHA256))
        self.assertFalse(states['truncated'])
        self.assertEqual(self.post('resolve', state_id='state_chen2023_az31_as_extruded')['identity']['id'],
                         'mat_chen2023_az31')
        for route, request in (('resolve', {'state_id': 'state_tian2023_az31_ti_0p5wt_as_extruded'}),
                               ('project/list', {'query': 'tian2023'})):
            with self.subTest(route=route):
                self.assertEqual(self.client.post('/api/catalog/' + route,
                                 json={'version': '0' * 64, **request}).status_code, 409)
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)

    def test_resolved_objects_are_detached_and_cannot_rewrite_qualifications(self):
        snapshot = CatalogSnapshot.from_packaged()
        state_id = 'state_tian2023_az31_ti_1wt_as_extruded'
        before = snapshot.resolve(state_id)
        changed = snapshot.resolve(state_id)
        changed['identity']['aliases'].append({'language': 'und', 'text': 'AZ31'})
        changed['properties'][0]['uncertainty'] = {'number': '0'}
        changed['properties'][0]['sample_count']['value'] = 3
        changed['properties'][0]['conditions']['temperature']['text'] = 'Room temperature'
        changed['state']['source_designation'] = '1 wt% Ti'
        changed['state']['state']['composition_or_purity']['text'] = 'Analyzed final composition'
        changed['sources'][0]['authors'].append('Bolv Xiao')
        changed['sources'][0]['license']['identifier'] = 'unverified'
        self.assertEqual(snapshot.resolve(state_id), before)
        self.assertEqual(self.post('resolve', state_id=state_id), before)

    def test_composite_category_does_not_infer_alloy_or_nanoscale_membership(self):
        status = self.client.get('/api/catalog/relationships/status').json()
        pin = {'version': status['catalog_version'], 'relationship_version': status['relationship_version']}
        self.assertEqual(status['unique_identity_count'], 1175)
        self.assertEqual(status['membership_assertion_count'], 1180)
        self.assertEqual(status['coverage']['composite']['supported'], 37)
        self.assertEqual(status['coverage']['metal']['supported'], 32)
        self.assertEqual(status['coverage']['alloy']['supported'], 2)
        self.assertEqual(status['coverage']['nanoscale']['supported'], 0)
        for key, _, _, _ in FACTS:
            identity_id = 'mat_tian2023_az31_ti_' + key
            response = self.client.post('/api/catalog/relationships/identity', json={**pin, 'identity_id': identity_id})
            self.assertEqual(response.status_code, 200)
            row = response.json()['result']['data']
            self.assertEqual({item['concept'] for item in row['memberships'] if item['status'] == 'supported'}, {'composite'})
            self.assertEqual(row['relationships'], [])
            for direction in ('incoming', 'outgoing', 'both'):
                response = self.client.post('/api/catalog/relationships/neighbors',
                                            json={**pin, 'identity_id': identity_id, 'direction': direction})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['result']['data']['records'], [])
