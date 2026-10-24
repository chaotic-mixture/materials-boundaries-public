"""Exact Kapoor analyzed glasses through installed query and CLI APIs.

Resolution hashes bind the unchanged reviewed candidate objects. Table 1
reports analyzed compositions and density, not nominal feeds or known means.
"""
from hashlib import sha256
import json
import subprocess
import sys
import unittest

from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query.catalog_snapshot import CatalogSnapshot


SOURCE = 'kapoor_2019_calcium_aluminophosphate'
FACTS = (
    ('P60', ('0', '40.4', '59.6'), '2.521'),
    ('P50', ('0', '49.9', '50.1'), '2.654'),
    ('P46', ('0', '53.9', '46.1'), '2.718'),
    ('Al5', ('5.0', '40.2', '54.8'), '2.614'),
    ('Al10', ('10.0', '30.1', '59.9'), '2.585'),
    ('Al15', ('14.8', '20.0', '65.2'), '2.583'),
)
RESOLVED_SHA256 = {
    'state_kapoor2019_p60_as_prepared': '2fcaaf4ca2295a7f66684c5c57ceca1a144df67cd8cbef6690f51acf20cdfd60',
    'state_kapoor2019_p50_as_prepared': '25687e621eb12953fca53708f91211b3b09e57f25c3be269dd77b9cda0621991',
    'state_kapoor2019_p46_as_prepared': 'a4b642fb8117b6a8e06d2ddbb8566ef10b95637275095bb6a472e00cd1ea91d4',
    'state_kapoor2019_al5_as_prepared': 'b88e50024441e2549065c410aa2d41c842a828c45d49259a9ecc177f86ad1192',
    'state_kapoor2019_al10_as_prepared': '602dded75b1cbde3633ea7d75d42fc41a3ee3f571f6a6dbb3897c0c6363ebaf7',
    'state_kapoor2019_al15_as_prepared': 'f0d096c338f09850e13a1323494d89cd0e065d6816cfa22db9caadb94b5d1803',
}


class KapoorPhosphateQuery(unittest.TestCase):
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

    def test_six_analyzed_glasses_keep_exact_density_joins_and_unknowns(self):
        self.assertEqual(self.status['counts'], {
            'local_catalog_unique_material_count': 1159,
            'local_material_state_count': 1160,
            'local_reference_property_count': 1171})
        for label, composition, value in FACTS:
            with self.subTest(glass=label):
                key = label.lower()
                identity_id = 'mat_kapoor2019_' + key
                state_id = 'state_kapoor2019_' + key + '_as_prepared'
                property_id = 'refprop_kapoor2019_' + key + '_mass_density'
                resolved = self.post('resolve', state_id=state_id)
                canonical = json.dumps(resolved, sort_keys=True, separators=(',', ':'),
                                       ensure_ascii=False, allow_nan=False).encode()
                self.assertEqual(sha256(canonical).hexdigest(), RESOLVED_SHA256[state_id])
                identity, state = resolved['identity'], resolved['state']
                self.assertEqual(identity['id'], identity_id)
                self.assertEqual(identity['category'], 'inorganic')
                self.assertIn('(Kapoor 2019)', identity['name'])
                self.assertEqual(identity['aliases'], [{'language': 'und', 'text': label + ' glass (Kapoor 2019)'}])
                self.assertIsNone(resolved['grade'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['identity_id'], identity_id)
                self.assertEqual(state['source_designation'], label)
                self.assertEqual(state['property_ids'], [property_id])
                self.assertEqual(state['state']['composition_or_purity']['text'],
                                 'Analyzed ICP-OES mol%: Al2O3 {}; CaO {}; P2O5 {}.'.format(*composition))
                self.assertIn('not nominal batch recipes', identity['identity_scope'])
                self.assertIn('reannealed', state['state']['temper_or_heat_treatment']['text'])
                self.assertIsNone(state['state']['porosity']['text'])
                self.assertEqual(len(resolved['properties']), 1)
                prop = resolved['properties'][0]
                self.assertEqual((prop['id'], prop['material_state_id'], prop['source_id']),
                                 (property_id, state_id, SOURCE))
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value'], {'kind': 'scalar', 'unit_text': 'g/cm3',
                    'unit_code': 'g/cm^3', 'value_text': value, 'number': value})
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['summary_statistic'], 'not_stated')
                self.assertEqual(prop['reporting_basis'], 'not_stated')
                self.assertEqual(prop['density_basis'], 'not_stated')
                self.assertIsNone(prop['uncertainty'])
                self.assertIn('source-wide maximum standard-deviation bound of <=0.002 g/cm3', prop['uncertainty_note'])
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                self.assertEqual(prop['conditions']['temperature']['text'], 'Room temperature.')
                self.assertEqual(prop['conditions']['test_method']['text'],
                                 'Archimedes method: weighing in air, then suspended in ethanol at room temperature.')
                for field in ('test_standard', 'conditioning'):
                    self.assertEqual(prop['conditions'][field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][field]['text'])
                extra = {row['name']: row['fact'] for row in prop['conditions']['additional_conditions']}
                self.assertIsNone(extra['density_pressure']['text'])
                self.assertEqual(extra['measurement_repetitions']['text'], 'At least 10 repetitions per sample.')
                self.assertFalse(prop['universal_bound'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertEqual([row['id'] for row in resolved['sources']], [SOURCE])
                self.assertEqual(resolved['sources'][0]['doi'], '10.3389/fmats.2019.00063')
                self.assertEqual(resolved['sources'][0]['license']['identifier'], 'CC-BY-4.0')
                self.assertEqual(prop['source_document']['sha256'],
                                 'ca831de841ebc22e52157474e491ca2151d8e4f6d68576a75376af47203d38a0')

    def test_installed_cli_and_api_preserve_exact_objects_and_source_precision(self):
        for label, _, _ in FACTS:
            with self.subTest(glass=label):
                resolved = self.post('resolve', state_id='state_kapoor2019_' + label.lower() + '_as_prepared')
                selected = self.cli('materials', '--identity-id', resolved['identity']['id'])
                self.assertEqual(selected['records'], [resolved['state']])
                self.assertEqual(selected['identities'], [resolved['identity']])
                self.assertEqual(selected['grades'], [])
                self.assertEqual(self.cli('reference-properties', '--id', resolved['properties'][0]['id'])['records'],
                                 resolved['properties'])
        expected = [self.post('resolve', state_id='state_kapoor2019_' + label.lower() + '_as_prepared')['properties'][0]
                    for label, _, _ in FACTS]
        expected.sort(key=lambda row: row['id'])
        for language in ('en', 'zh', 'ja', 'de'):
            with self.subTest(language=language):
                self.assertEqual(self.cli('reference-properties', '--source-id', SOURCE,
                                          '--lang', language)['records'], expected)
        self.assertEqual(self.cli('sources', '--id', SOURCE)['records'], resolved['sources'])

    def test_formal_count_excludes_computed_overlap_and_rejects_stale_versions(self):
        status = self.client.get('/api/catalog/project/status').json()
        self.assertTrue(status['enabled'])
        self.assertEqual(status['counts'], {
            'formal_project_admission_count': 1183,
            'legacy_source_qualified_identity_count': 1159,
            'reviewed_computed_composition_count': 24,
            'categories': {'metal': 44, 'inorganic': 71, 'polymer': 30,
                           'composite': 28, 'natural': 1010}})
        data = {'version': status['version'], 'query': 'kapoor2019',
                'partition': 'legacy-source-qualified', 'limit': 100}
        selected = self.client.post('/api/catalog/project/list', json=data)
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 6)
        self.assertEqual({row['id'] for row in selected.json()['records']}, {
            'legacy:mat_kapoor2019_' + label.lower() for label, _, _ in FACTS})
        selected = self.client.post('/api/catalog/project/list', json={**data, 'partition': 'reviewed-computed'})
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 0)
        states = self.post('search', query='kapoor2019', limit=100)
        self.assertEqual({row['id'] for row in states['records']}, set(RESOLVED_SHA256))
        self.assertFalse(states['truncated'])
        self.assertEqual(self.post('resolve', state_id='state_bianchi2022_epdm_h_p60')['identity']['id'],
                         'mat_bianchi2022_epdm_h_p60')
        for route, request in (('resolve', {'state_id': 'state_kapoor2019_p60_as_prepared'}),
                               ('project/list', {'query': 'kapoor2019'})):
            with self.subTest(route=route):
                self.assertEqual(self.client.post('/api/catalog/' + route,
                                 json={'version': '0' * 64, **request}).status_code, 409)
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)

    def test_resolved_objects_are_detached_and_cannot_rewrite_qualifications(self):
        snapshot = CatalogSnapshot.from_packaged()
        state_id = 'state_kapoor2019_p60_as_prepared'
        before = snapshot.resolve(state_id)
        changed = snapshot.resolve(state_id)
        changed['identity']['aliases'].append({'language': 'und', 'text': 'P60'})
        changed['properties'][0]['uncertainty'] = {'number': '0.002'}
        changed['properties'][0]['sample_count']['value'] = 10
        changed['properties'][0]['summary_statistic'] = 'mean'
        changed['state']['state']['composition_or_purity']['text'] = 'Validated exact stoichiometry'
        changed['sources'][0]['license']['identifier'] = 'unverified'
        self.assertEqual(snapshot.resolve(state_id), before)
        self.assertEqual(self.post('resolve', state_id=state_id), before)
