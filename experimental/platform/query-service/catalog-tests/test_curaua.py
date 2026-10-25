"""Exact reviewed Curaua apparent-density facts through installed API and CLI."""
from hashlib import sha256
from importlib.resources import files
import json
import subprocess
import sys
import unittest

from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query.catalog_snapshot import CatalogSnapshot


SOURCE = 'czlonka_2021_curaua_rpuf'
FACTS = (
    ('0p1', 'CF 0.1', '0.1', '38.4', '0.4', 'C'),
    ('0p5', 'CF 0.5', '0.5', '37.9', '0.6', 'B'),
    ('1', 'CF 1', '1', '37.6', '0.4', 'A'),
)
AUTHORS = ['Sylwia Cz\u0142onka', 'Eduardo Fischer Kerche', 'Roberta Motta Neves',
           'Anna Str\u0105kowska', 'Krzysztof Strzelec']
# Canonical resolved-object hashes assembled from the exact reviewed candidate
# fa170104 packet, independently of the installed snapshot under test.
RESOLVED_SHA256 = {'state_czlonka2021_curaua_cf0p1_free_rise': '5b8c11ba55daf4f3b1fa57ae1b9219188c3a4ac344915ea7abc7d931c73296cc', 'state_czlonka2021_curaua_cf0p5_free_rise': 'ac527e0278531ecbc452377ae853b6393143c32683024ec4e72baa546c2118ac', 'state_czlonka2021_curaua_cf1_free_rise': '62aa965628c2d0a01fe46a0dbb64be6c0f8eec892e1191d44d2a2e3f16e9fa97'}


class CurauaQuery(unittest.TestCase):
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

    def test_three_nominal_composites_keep_density_cv_and_age_qualifications(self):
        self.assertEqual(self.status['counts'], {
            'local_catalog_unique_material_count': 1164,
            'local_material_state_count': 1165,
            'local_reference_property_count': 1176})
        for key, label, loading, density, cv, group in FACTS:
            with self.subTest(formulation=key):
                identity_id = 'mat_czlonka2021_curaua_cf' + key
                state_id = 'state_czlonka2021_curaua_cf' + key + '_free_rise'
                property_id = 'refprop_czlonka2021_curaua_cf' + key + '_apparent_density'
                resolved = self.post('resolve', state_id=state_id)
                raw = json.dumps(resolved, sort_keys=True, separators=(',', ':'),
                                 ensure_ascii=False, allow_nan=False).encode('utf-8')
                self.assertEqual(sha256(raw).hexdigest(), RESOLVED_SHA256[state_id])
                identity, state = resolved['identity'], resolved['state']
                self.assertEqual(identity['id'], identity_id)
                self.assertEqual(identity['category'], 'composite')
                self.assertIn('(Cz\u0142onka 2021)', identity['name'])
                self.assertIn('relative to total RPUF mass', identity['identity_scope'])
                self.assertIn('not an analyzed final retained composition', identity['identity_scope'])
                self.assertIsNone(resolved['grade'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['identity_id'], identity_id)
                self.assertEqual(state['source_designation'], label)
                self.assertEqual(state['property_ids'], [property_id])
                self.assertEqual(state['state']['composition_or_purity']['text'],
                    'Rigid polyurethane foam formulation with nominal ' + loading +
                    ' wt% bleached Curau\u00e1 fiber relative to total RPUF mass.')
                prop, = resolved['properties']
                self.assertEqual((prop['id'], prop['material_state_id'], prop['source_id']),
                                 (property_id, state_id, SOURCE))
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value'], {'kind': 'scalar', 'unit_text': 'kg m\u22123',
                    'unit_code': 'kg/m^3', 'value_text': density, 'number': density})
                self.assertEqual(prop['source_property_label'], 'Apparent Density (kg m\u22123)')
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['summary_statistic'], 'reported_mean')
                self.assertEqual(prop['density_basis'], 'apparent')
                self.assertIsNone(prop['uncertainty'])
                self.assertEqual(prop['uncertainty_status'], 'not_reported_in_inspected_source')
                self.assertIn('superscript ' + cv + ' is called coefficient of variance', prop['uncertainty_note'])
                self.assertIn('Statistical-group letter ' + group, prop['uncertainty_note'])
                self.assertIn('no unit or percent sign is specified', prop['uncertainty_note'])
                self.assertIn('not absence of source variability information', prop['uncertainty_note'])
                self.assertEqual(prop['sample_count']['value'], 10)
                self.assertEqual(prop['sample_count']['relation'], 'exact')
                self.assertIn('Independent specimens', prop['sample_count']['scope'])
                self.assertEqual(prop['conditions']['test_standard']['text'], 'ISO 845.')
                self.assertEqual(prop['conditions']['test_method']['text'], 'Ratio of foam mass to volume.')
                for field in ('temperature', 'conditioning'):
                    self.assertEqual(prop['conditions'][field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][field]['text'])
                extra = {row['name']: row['fact'] for row in prop['conditions']['additional_conditions']}
                for field in ('density_pressure', 'measurement_repetitions', 'measurement_age'):
                    self.assertEqual(extra[field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(extra[field]['text'])
                self.assertIn('Neither 24 h nor 7 days is assigned as density measurement age',
                              extra['measurement_age']['notes'])
                self.assertFalse(prop['universal_bound'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                source, = resolved['sources']
                self.assertEqual(source['id'], SOURCE)
                self.assertEqual(source['doi'], '10.3390/ijms222011203')
                self.assertEqual(source['authors'], AUTHORS)
                self.assertNotIn('Xiao Hu', source['authors'])
                self.assertNotIn('Antonella Piozzi', source['authors'])
                self.assertEqual(source['license']['identifier'], 'CC-BY-4.0')
                self.assertEqual(prop['source_document']['sha256'],
                                 '321d2018f69229320a9a3bfc45686b69a486ff799e1c1414341271ac965f5d17')
                self.assertIn('Neither an archive version nor a PDF manifest was found',
                              prop['source_document']['inspection_scope'])

    def test_installed_cli_and_api_preserve_exact_objects_and_authorship(self):
        expected = []
        for key, _, _, _, _, _ in FACTS:
            resolved = self.post('resolve', state_id='state_czlonka2021_curaua_cf' + key + '_free_rise')
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
            'formal_project_admission_count': 1188,
            'legacy_source_qualified_identity_count': 1164,
            'reviewed_computed_composition_count': 24,
            'categories': {'metal': 44, 'inorganic': 71, 'polymer': 30,
                           'composite': 33, 'natural': 1010}})
        data = {'version': status['version'], 'query': 'czlonka2021',
                'partition': 'legacy-source-qualified', 'limit': 100}
        selected = self.client.post('/api/catalog/project/list', json=data)
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 3)
        self.assertEqual({row['id'] for row in selected.json()['records']}, {
            'legacy:mat_czlonka2021_curaua_cf' + key for key, _, _, _, _, _ in FACTS})
        selected = self.client.post('/api/catalog/project/list', json={**data, 'partition': 'reviewed-computed'})
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 0)
        states = self.post('search', query='czlonka2021', limit=100)
        self.assertEqual({row['id'] for row in states['records']}, set(RESOLVED_SHA256))
        self.assertFalse(states['truncated'])
        for route, request in (('resolve', {'state_id': 'state_czlonka2021_curaua_cf1_free_rise'}),
                               ('project/list', {'query': 'czlonka2021'})):
            with self.subTest(route=route):
                self.assertEqual(self.client.post('/api/catalog/' + route,
                                 json={'version': '0' * 64, **request}).status_code, 409)
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)

    def test_resolved_objects_are_detached_and_cannot_rewrite_qualifications(self):
        snapshot = CatalogSnapshot.from_packaged()
        state_id = 'state_czlonka2021_curaua_cf1_free_rise'
        before = snapshot.resolve(state_id)
        changed = snapshot.resolve(state_id)
        changed['identity']['aliases'].append({'language': 'und', 'text': 'Pure polyurethane'})
        changed['properties'][0]['uncertainty'] = {'number': '0.4', 'unit': '%'}
        changed['properties'][0]['sample_count']['value'] = 5
        changed['properties'][0]['conditions']['conditioning']['text'] = '7 days'
        changed['state']['state']['composition_or_purity']['text'] = 'Analyzed final composition'
        changed['sources'][0]['authors'].append('Xiao Hu')
        changed['sources'][0]['license']['identifier'] = 'unverified'
        self.assertEqual(snapshot.resolve(state_id), before)
        self.assertEqual(self.post('resolve', state_id=state_id), before)

    def test_composite_category_does_not_infer_constituent_membership(self):
        status = self.client.get('/api/catalog/relationships/status').json()
        pin = {'version': status['catalog_version'], 'relationship_version': status['relationship_version']}
        self.assertEqual(status['unique_identity_count'], 1164)
        self.assertEqual(status['membership_assertion_count'], 1169)
        self.assertEqual(status['coverage']['composite']['supported'], 33)
        self.assertEqual(status['coverage']['natural']['supported'], 1010)
        # The reviewed overlay also supports the existing PBS/lignin composite.
        self.assertEqual(status['coverage']['polymer']['supported'], 31)
        for key, _, _, _, _, _ in FACTS:
            identity_id = 'mat_czlonka2021_curaua_cf' + key
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

    def test_read_only_routes_preserve_packaged_resources(self):
        paths = [files('materials_boundaries').joinpath('data', name + '.json')
                 for name in ('materials', 'reference_properties', 'sources')]
        before = [sha256(path.read_bytes()).hexdigest() for path in paths]
        for method in ('PUT', 'PATCH', 'DELETE'):
            for route in ('resolve', 'project/list', 'relationships/identity'):
                with self.subTest(method=method, route=route):
                    response = self.client.request(method, '/api/catalog/' + route,
                        json={'version': self.version, 'state_id': 'state_czlonka2021_curaua_cf1_free_rise',
                              'reported_value': {'number': '999'}})
                    self.assertEqual(response.status_code, 405)
        self.assertEqual([sha256(path.read_bytes()).hexdigest() for path in paths], before)
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
