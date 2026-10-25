"""Closed Bruns Table 3 facts through local query, core CLI and formal API.

The canonical resolution hashes freeze the approved packet's complete objects,
including qualifications, evidence locators and separate nominal/ICP-OES values.
The expected means/SDs below are explicit, not inferred from the live catalog.
"""
from hashlib import sha256
import json
import subprocess
import sys
import unittest

from fastapi.testclient import TestClient
from materials_query.app import create_app


SOURCE = 'bruns_2020_alumina_borosilicate'
FACTS = (
    ('al1p0', '1.0', '2.131', '0.006'),
    ('al1p5', '1.5', '2.133', '0.010'),
    ('al2p0', '2.0', '2.130', '0.002'),
    ('al4p0', '4.0', '2.137', '0.004'),
)
RESOLVED_SHA256 = {'state_bruns2020_nbs2_al1p0_furnace_cooled': 'ba033ce1acadfaac16b2cf1d56603655d29bc357e0b64ce54389b5ceee92ac9e',
 'state_bruns2020_nbs2_al1p5_furnace_cooled': '7d1818ae87d46990de789906639669aab0aba41e438c0d3bee8d1b2acb4a55ab',
 'state_bruns2020_nbs2_al2p0_furnace_cooled': '9ed26faa14eb7f38b5deed582686bf99d41a33bbe9a306ceb36e00e5d27c8e70',
 'state_bruns2020_nbs2_al4p0_furnace_cooled': '5c949b7996771805adedf177f1702512343ad8a503735bf19345f17396c0e0ae'}


class BrunsBorosilicateQuery(unittest.TestCase):
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

    def test_four_recipes_have_exact_independent_identity_state_property_links(self):
        self.assertEqual(self.status['counts'], {
            'local_catalog_unique_material_count': 1164,
            'local_material_state_count': 1165,
            'local_reference_property_count': 1176})
        expected_states = set()
        identities = set()
        for suffix, label, mean, deviation in FACTS:
            with self.subTest(recipe=suffix):
                identity_id = 'mat_bruns2020_nbs2_' + suffix
                state_id = 'state_bruns2020_nbs2_' + suffix + '_furnace_cooled'
                property_id = 'refprop_bruns2020_nbs2_' + suffix + '_mass_density'
                expected_states.add(state_id)
                resolved = self.post('resolve', state_id=state_id)
                canonical = json.dumps(resolved, sort_keys=True, separators=(',', ':'),
                                       ensure_ascii=False, allow_nan=False).encode()
                self.assertEqual(sha256(canonical).hexdigest(), RESOLVED_SHA256[state_id])
                self.assertEqual(resolved['identity']['id'], identity_id)
                self.assertEqual(resolved['identity']['category'], 'inorganic')
                identities.add(resolved['identity']['id'])
                self.assertIsNone(resolved['grade'])
                self.assertIsNone(resolved['state']['grade_id'])
                self.assertEqual(resolved['state']['identity_id'], identity_id)
                self.assertEqual(resolved['state']['property_ids'], [property_id])
                self.assertEqual(resolved['state']['source_designation'], label + '% Al (furnace cooled)')
                self.assertEqual(len(resolved['properties']), 1)
                prop = resolved['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['material_state_id'], state_id)
                self.assertEqual(prop['source_id'], SOURCE)
                self.assertEqual([row['id'] for row in resolved['sources']], [SOURCE])
                self.assertEqual(resolved['sources'][0]['license']['identifier'], 'CC-BY-4.0')
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value'], {
                    'kind': 'scalar', 'unit_text': 'g/cm³', 'unit_code': 'g/cm^3',
                    'value_text': mean, 'number': mean})
                self.assertEqual(prop['summary_statistic'], 'reported_mean')
                self.assertEqual(prop['uncertainty_status'], 'reported_standard_deviation')
                self.assertEqual(prop['uncertainty']['type'], 'reported_standard_deviation')
                self.assertEqual(prop['uncertainty']['number'], deviation)
                self.assertEqual(prop['uncertainty']['value_text'], deviation)
                self.assertEqual(prop['uncertainty']['unit_code'], 'g/cm^3')
                self.assertIsNone(prop['uncertainty']['confidence_level'])
                self.assertIsNone(prop['uncertainty']['coverage_factor'])
                self.assertEqual(prop['density_basis'], 'not_stated')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['conditions']['test_method']['text'], 'Archimedes method in toluene.')
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                self.assertIsNone(prop['sample_count']['value'])
                for key in ('temperature', 'conditioning', 'test_standard'):
                    self.assertEqual(prop['conditions'][key]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][key]['text'])
                additional = {row['name']: row['fact'] for row in prop['conditions']['additional_conditions']}
                self.assertEqual(additional['density_pressure']['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(additional['density_pressure']['text'])
                self.assertEqual(additional['piece_count_lower_bound']['text'],
                                 'At least five pieces, each weighing 0.1-1.0 g.')
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertFalse(prop['universal_bound'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                self.assertEqual(self.post('record', kind='reference-properties', record_id=property_id), prop)
                self.assertEqual(self.post('record', kind='identities', record_id=identity_id), resolved['identity'])
                selected = self.post('search', query=identity_id, limit=100)
                self.assertEqual([row['id'] for row in selected['records']], [state_id])
                self.assertFalse(selected['truncated'])
                cooling = resolved['state']['state']['temper_or_heat_treatment']
                if suffix == 'al4p0':
                    self.assertIn('together with its crucible', cooling['text'])
                    self.assertNotIn('graphite', cooling['text'])
                    self.assertNotIn('30 K/h', cooling['text'])
                    self.assertNotIn('500', cooling['text'])
                else:
                    self.assertIn('graphite mold preheated to 500', cooling['text'])
                    self.assertIn('30 K/h', cooling['text'])
        self.assertEqual(len(identities), 4)
        search = self.post('search', query='bruns2020_nbs2', limit=100)
        self.assertEqual({row['id'] for row in search['records']}, expected_states)
        self.assertFalse(search['truncated'])

    def test_core_cli_keeps_exact_objects_and_source_qualified_scope(self):
        for suffix, label, mean, deviation in FACTS:
            with self.subTest(recipe=suffix):
                state_id = 'state_bruns2020_nbs2_' + suffix + '_furnace_cooled'
                resolved = self.post('resolve', state_id=state_id)
                selected = self.cli('materials', '--identity-id', resolved['identity']['id'])
                self.assertEqual(selected['records'], [resolved['state']])
                self.assertEqual(selected['identities'], [resolved['identity']])
                self.assertEqual(selected['grades'], [])
                selected = self.cli('reference-properties', '--id', resolved['properties'][0]['id'])
                self.assertEqual(selected['records'], resolved['properties'])
        selected = self.cli('reference-properties', '--source-id', SOURCE)
        self.assertEqual({row['id'] for row in selected['records']}, {
            'refprop_bruns2020_nbs2_' + suffix + '_mass_density' for suffix, *_ in FACTS})
        self.assertEqual(self.cli('sources', '--id', SOURCE)['records'], resolved['sources'])

    def test_formal_api_admits_only_four_legacy_recipe_identities(self):
        status = self.client.get('/api/catalog/project/status').json()
        self.assertTrue(status['enabled'])
        self.assertEqual(status['counts'], {
            'formal_project_admission_count': 1188,
            'legacy_source_qualified_identity_count': 1164,
            'reviewed_computed_composition_count': 24,
            'categories': {'metal': 44, 'inorganic': 71, 'polymer': 30,
                           'composite': 33, 'natural': 1010}})
        selected = self.client.post('/api/catalog/project/list', json={
            'version': status['version'], 'query': 'bruns2020_nbs2',
            'partition': 'legacy-source-qualified', 'limit': 100})
        self.assertEqual(selected.status_code, 200)
        value = selected.json()
        self.assertEqual(value['matched_count'], 4)
        self.assertEqual({row['id'] for row in value['records']}, {
            'legacy:mat_bruns2020_nbs2_' + suffix for suffix, *_ in FACTS})
        for row in value['records']:
            self.assertEqual(row['category'], 'inorganic')
            self.assertEqual(row['identity'], self.post('record', kind='identities',
                                                       record_id=row['identity']['id']))
        excluded = self.client.post('/api/catalog/project/list', json={
            'version': status['version'], 'query': 'bruns2020_nbs2',
            'partition': 'reviewed-computed'})
        self.assertEqual(excluded.json()['matched_count'], 0)
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
