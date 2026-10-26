"""Reviewed PLA/PCL ratios remain source-qualified across installed API and CLI."""
from hashlib import sha256
from importlib.resources import files
import json
import subprocess
import sys
import unittest

from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query.catalog_snapshot import CatalogSnapshot, LatestCatalog


SOURCE = 'delgado_aguilar_2020_pla_pcl'
AUTHORS = ['Marc Delgado-Aguilar', 'Rita Puig', 'Ilija Sazdovski', 'Pere Fullana-i-Palmer']
FACTS = (('95_5', '3.70', '0.13', '0.054'), ('90_10', '3.60', '0.26', '0.108'),
         ('85_15', '3.38', '0.27', '0.162'), ('80_20', '3.20', '0.19', '0.214'),
         ('60_40', '2.55', '0.09', '0.421'), ('40_60', '1.86', '0.11', '0.621'),
         ('20_80', '1.13', '0.05', '0.814'))
# Literal hashes of resolved joins built from the independently reviewed
# 73a5d872 candidate packet, not from the runtime snapshot under test.
RESOLVED_SHA256 = {'state_delgado2020_pla_pcl_b95_5_injection_molded': '341935d6fdbaa3bdbc9a43543e85946129278f4d5256b08ef74b16e207349541', 'state_delgado2020_pla_pcl_b90_10_injection_molded': '5828569742a2d2e6bcf86a0a2a8ec0a1e8ad085ef2fb2d2902f3a736376ebe4f', 'state_delgado2020_pla_pcl_b85_15_injection_molded': '152810e9f772a91a59df54cd2ac7e3e8e23352e9bd28f27cb72c7ac01ef20752', 'state_delgado2020_pla_pcl_b80_20_injection_molded': '5ba75ac2052712974b7d8f2cdbf3f6d5c3f9e7adb8747e10192282df70894e63', 'state_delgado2020_pla_pcl_b60_40_injection_molded': '36cf8b6f07fd1282a4750249e1ab298dd8a48193ed4168205389deaaf94c3349', 'state_delgado2020_pla_pcl_b40_60_injection_molded': '4ef0afed0459ee3f7808b15f3fa04653907df8568911af711a0205c26070cbf3', 'state_delgado2020_pla_pcl_b20_80_injection_molded': '001d945c588e0204ff476cbffd42c37c560eabc9011fb8b9c34333aa3d900f32'}
SOURCE_SHA256 = '1109e1520adeca2c950528ab98ad7def33971764d57d39240c19a5a7bec3061a'


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def ids(suffix):
    return ('mat_delgado2020_pla_pcl_b' + suffix,
            'state_delgado2020_pla_pcl_b' + suffix + '_injection_molded',
            'refprop_delgado2020_pla_pcl_b' + suffix + '_youngs_modulus')


class DelgadoPlaPclQuery(unittest.TestCase):
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
                                capture_output=True, text=True, encoding='utf-8', check=True,
                                timeout=60)
        return json.loads(result.stdout)

    def test_seven_measured_moduli_keep_gpa_sd_and_unknown_central_statistics(self):
        for suffix, value, sd, volume in FACTS:
            with self.subTest(formulation=suffix):
                identity_id, state_id, property_id = ids(suffix)
                row = self.post('resolve', state_id=state_id)
                self.assertEqual(digest(row), RESOLVED_SHA256[state_id])
                identity, state = row['identity'], row['state']
                self.assertEqual((identity['id'], identity['category']), (identity_id, 'polymer'))
                self.assertIn('(Delgado-Aguilar 2020)', identity['name'])
                self.assertIn('different nominal mass recipes distinguish identities', identity['identity_scope'])
                self.assertIn('not a finished-blend grade', identity['identity_scope'])
                self.assertIsNone(row['grade'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['source_designation'], 'B' + suffix.replace('_', '/'))
                self.assertEqual(state['property_ids'], [property_id])
                self.assertIn('calculated PCL volume fraction ' + volume, state['state']['composition_or_purity']['text'])
                self.assertIn('no universal molding recipe', state['state']['processing']['notes'])
                self.assertIn('post-molding', state['state']['conditioning']['notes'])
                prop, = row['properties']
                self.assertEqual((prop['id'], prop['material_state_id'], prop['source_id']),
                                 (property_id, state_id, SOURCE))
                self.assertEqual(prop['quantity'], 'youngs_modulus')
                self.assertEqual(prop['quantity_dimension'], 'pressure')
                self.assertEqual(prop['reported_value'], {'kind': 'scalar', 'unit_code': 'GPa',
                    'unit_text': 'GPa', 'number': value, 'value_text': value})
                self.assertEqual(prop['source_property_label'], 'E_t^B (GPa)')
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['summary_statistic'], 'not_stated')
                self.assertEqual(prop['reporting_basis'], 'not_stated')
                self.assertEqual(prop['uncertainty_status'], 'reported_measures')
                self.assertEqual(prop['uncertainty']['type'], 'reported_measures')
                measure, = prop['uncertainty']['measures']
                self.assertEqual((measure['kind'], measure['availability'], measure['basis']),
                                 ('standard_deviation', 'numeric_reported', 'absolute'))
                self.assertEqual(measure['reported_value'], {'unit_code': 'GPa', 'unit_text': 'GPa',
                                                             'number': sd, 'value_text': sd})
                self.assertIsNone(measure['confidence_level'])
                self.assertIsNone(measure['coverage_factor'])
                self.assertIn('do not infer mean', measure['note'])
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                self.assertIsNone(prop['method_definition']['extraction_window'])
                self.assertEqual(prop['conditions']['test_standard']['text'], 'ISO 527-1:2012.')
                self.assertEqual(prop['conditions']['loading_rate']['text'], 'Crosshead speed 2 mm/min.')
                self.assertIn('115 mm', prop['conditions']['test_method']['text'])
                for field in ('temperature', 'conditioning', 'direction'):
                    self.assertEqual(prop['conditions'][field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][field]['text'])
                conditions = {item['name']: item['fact'] for item in prop['conditions']['additional_conditions']}
                self.assertEqual(conditions['clamp_separation']['text'], 'Gap between clamps: 115 mm.')
                self.assertIn('not an extensometer gauge length', conditions['clamp_separation']['notes'])
                for field in ('test_relative_humidity', 'test_pressure', 'specimen_type_and_dimensions',
                              'measurement_repetitions'):
                    self.assertIsNone(conditions[field]['text'])
                    self.assertEqual(conditions[field]['status'], 'not_reported_in_inspected_source')
                self.assertFalse(prop['universal_bound'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                self.assertEqual(prop['evaluation_support'], 'catalog_only')

    def test_installed_cli_and_api_preserve_exact_objects_and_property_order(self):
        properties = []
        for suffix, _, _, _ in FACTS:
            identity_id, state_id, property_id = ids(suffix)
            row = self.post('resolve', state_id=state_id)
            self.assertEqual(digest(row), RESOLVED_SHA256[state_id])
            selected = self.cli('materials', '--identity-id', identity_id)
            self.assertEqual(selected['records'], [row['state']])
            self.assertEqual(selected['identities'], [row['identity']])
            self.assertEqual(selected['grades'], [])
            self.assertEqual(self.cli('reference-properties', '--id', property_id)['records'], row['properties'])
            properties.extend(row['properties'])
        properties.sort(key=lambda row: row['id'])
        for language in ('en', 'zh', 'ja', 'de'):
            with self.subTest(language=language):
                self.assertEqual(self.cli('reference-properties', '--source-id', SOURCE,
                                         '--lang', language)['records'], properties)
        self.assertEqual(self.cli('sources', '--id', SOURCE)['records'],
                         [self.post('record', kind='sources', record_id=SOURCE)])

    def test_counts_pagination_and_stale_requests_do_not_inflate_admissions(self):
        self.assertEqual(self.status['counts'], {'local_catalog_unique_material_count': 1175,
            'local_material_state_count': 1176, 'local_reference_property_count': 1187})
        status = self.client.get('/api/catalog/project/status').json()
        self.assertTrue(status['enabled'])
        self.assertEqual(status['counts'], {'formal_project_admission_count': 1199,
            'legacy_source_qualified_identity_count': 1175, 'reviewed_computed_composition_count': 24,
            'categories': {'natural': 1010, 'metal': 44, 'inorganic': 71, 'polymer': 37, 'composite': 37}})
        data = {'version': status['version'], 'query': 'delgado2020_pla_pcl',
                'partition': 'legacy-source-qualified', 'limit': 3}
        rows = []
        for offset in (0, 3, 6):
            response = self.client.post('/api/catalog/project/list', json={**data, 'offset': offset})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['matched_count'], 7)
            rows.extend(response.json()['records'])
        self.assertEqual({row['id'] for row in rows}, {'legacy:' + ids(suffix)[0] for suffix, _, _, _ in FACTS})
        self.assertEqual(len(rows), 7)
        response = self.client.post('/api/catalog/project/list', json={**data, 'partition': 'reviewed-computed'})
        self.assertEqual(response.json()['matched_count'], 0)
        for route, request in (('resolve', {'state_id': ids('95_5')[1]}),
                               ('record', {'kind': 'sources', 'record_id': SOURCE}),
                               ('project/list', {'query': 'delgado2020_pla_pcl'})):
            self.assertEqual(self.client.post('/api/catalog/' + route,
                             json={'version': '0' * 64, **request}).status_code, 409)

    def test_source_rights_and_excluded_endpoints_are_preserved(self):
        source = self.post('record', kind='sources', record_id=SOURCE)
        self.assertEqual(digest(source), SOURCE_SHA256)
        self.assertEqual(source['authors'], AUTHORS)
        self.assertEqual(source['doi'], '10.3390/ma13112655')
        self.assertEqual(source['license'], {'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0'})
        self.assertIn('No original PDF bytes', source['provenance']['method'])
        self.assertIn('reCAPTCHA', source['provenance']['method'])
        self.assertIn('No author or publisher endorsement', ' '.join(source['claim_notes']))
        result = self.post('search', kind='reference-properties', query=SOURCE, limit=100)
        self.assertFalse(result['truncated'])
        self.assertEqual({row['id'] for row in result['records']}, {ids(suffix)[2] for suffix, _, _, _ in FACTS})
        self.assertEqual(len(result['records']), 7)
        for row in result['records']:
            self.assertIn('Exclude neat PLA and neat PCL', row['scope_note'])
            self.assertIn('not new measured properties', row['scope_note'])
        self.assertTrue(self.post('search', query='delgado2020_pla_pcl', limit=3)['truncated'])

    def test_detached_results_do_not_rewrite_unknowns_or_measures(self):
        snapshot = CatalogSnapshot.from_packaged()
        state_id = ids('95_5')[1]
        before = snapshot.resolve(state_id)
        changed = snapshot.resolve(state_id)
        changed['identity']['category'] = 'composite'
        changed['state']['grade_id'] = 'invented'
        changed['properties'][0]['summary_statistic'] = 'reported_mean'
        changed['properties'][0]['sample_count']['value'] = 10
        changed['properties'][0]['uncertainty']['measures'][0]['reported_value']['number'] = '999'
        changed['sources'][0]['authors'].append('Invented author')
        self.assertEqual(snapshot.resolve(state_id), before)
        self.assertEqual(self.post('resolve', state_id=state_id), before)
        self.assertEqual(digest(before), RESOLVED_SHA256[state_id])

    def test_polymer_category_does_not_create_constituents_or_inverse_claims(self):
        status = self.client.get('/api/catalog/relationships/status').json()
        self.assertTrue(status['enabled'])
        self.assertEqual(status['unique_identity_count'], 1175)
        self.assertEqual(status['membership_assertion_count'], 1180)
        self.assertEqual(status['identity_relationship_count'], 1)
        self.assertEqual(status['coverage']['polymer']['supported'], 38)
        self.assertEqual(status['new_identities_admitted'], 0)
        pin = {'version': status['catalog_version'], 'relationship_version': status['relationship_version']}
        for suffix, _, _, _ in FACTS:
            identity_id = ids(suffix)[0]
            response = self.client.post('/api/catalog/relationships/identity', json={**pin, 'identity_id': identity_id})
            self.assertEqual(response.status_code, 200, response.text)
            row = response.json()['result']['data']
            self.assertEqual({item['concept'] for item in row['memberships'] if item['status'] == 'supported'}, {'polymer'})
            self.assertEqual(row['relationships'], [])
            for direction in ('incoming', 'outgoing', 'both'):
                response = self.client.post('/api/catalog/relationships/neighbors',
                    json={**pin, 'identity_id': identity_id, 'direction': direction})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()['result']['data']['records'], [])

    def test_refresh_rejects_stale_selections_without_rewriting_prior_snapshot(self):
        current = CatalogSnapshot.from_packaged()
        graph = {name: json.loads(files('materials_boundaries').joinpath('data', name + '.json').read_bytes())
                 for name in ('materials', 'reference_properties', 'sources')}
        expected = current.resolve(ids('95_5')[1])
        for field in ('identities', 'records'):
            graph['materials'][field] = [row for row in graph['materials'][field] if 'delgado2020_pla_pcl' not in row['id']]
        graph['reference_properties']['records'] = [row for row in graph['reference_properties']['records']
                                                   if row['source_id'] != SOURCE]
        graph['sources']['records'] = [row for row in graph['sources']['records'] if row['id'] != SOURCE]
        previous = CatalogSnapshot(graph['materials'], graph['reference_properties'], graph['sources'])
        latest = LatestCatalog(previous)
        selected = latest.select('materials', 'state_ewurum2025_pbs_lignin_r10_injection_molded')
        old_result = latest.read_selected(selected)
        latest.refresh(*(json.loads(files('materials_boundaries').joinpath('data', name + '.json').read_bytes())
                         for name in ('materials', 'reference_properties', 'sources')))
        with self.assertRaisesRegex(ValueError, 'stale selection'):
            latest.read_selected(selected)
        self.assertEqual(previous.record('materials', selected.record_id), old_result)
        self.assertEqual(latest.current.resolve(ids('95_5')[1]), expected)

    def test_read_only_routes_preserve_packaged_resources(self):
        paths = [files('materials_boundaries').joinpath('data', name + '.json')
                 for name in ('materials', 'reference_properties', 'sources')]
        before = [sha256(path.read_bytes()).hexdigest() for path in paths]
        for method in ('PUT', 'PATCH', 'DELETE'):
            for route in ('resolve', 'record', 'project/list', 'relationships/identity'):
                response = self.client.request(method, '/api/catalog/' + route,
                    json={'version': self.version, 'state_id': ids('95_5')[1], 'reported_value': {'number': '999'}})
                self.assertEqual(response.status_code, 405)
        self.assertEqual([sha256(path.read_bytes()).hexdigest() for path in paths], before)
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
