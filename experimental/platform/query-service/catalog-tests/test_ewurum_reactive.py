"""Exact reviewed Ewurum reactive formulations through installed API and CLI."""
from hashlib import sha256
from importlib.resources import files
import json
import subprocess
import sys
import unittest

from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query.catalog_snapshot import CatalogSnapshot


SOURCE = 'ewurum_mcdonald_2025_pbs_lignin'
AUTHORS = ['Nnaemeka Ewurum', 'Armando G. McDonald']
SOURCE_SHA256 = '358d6486d107da45ed76c3aa7c7a448213957c7b94afc811e9ad75e294641ca0'
DOCUMENT_SHA256 = '766d17f0e92c7e93cd57a3a5e97dddff0cb66a84bba6bf9118fbd0796d4c2e6f'
FACTS = (
    ('10', '751', '40', 'b\u2032', '4.7'),
    ('20', '716', '49', 'b\u2032', '4.3'),
    ('30', '910', '85', 'b', '12.7'),
    ('45', '1256', '162', 'a', '26.2'),
)
# Literal joins of the reviewed 29a33009 packet and its unchanged baseline,
# independent of the installed snapshot under test. Resolved objects include
# schema_version; these compact canonical hashes do not include a final newline.
RESOLVED_SHA256 = {
    'state_ewurum2025_pbs_lignin_r10_injection_molded': '6fdcd7b0b4a9db42025c0fe56ba15fcf74413618c05013285d7b26bd9d221e13',
    'state_ewurum2025_pbs_lignin_r20_injection_molded': '8c580917ca1c70ceaaa523a1b0b0c8b331014e38547b88abcb526b2867691ac8',
    'state_ewurum2025_pbs_lignin_r30_injection_molded': '6e839e5cc9ef7192bfcc4ade4517b6032948e699055b4d227b4c1c36e14f1015',
    'state_ewurum2025_pbs_lignin_r45_injection_molded': '8e8c5db9d50028ef5d907b34d1079772dea18d61b00cdf76da75358da414b554',
}
OLD_RESOLVED_SHA256 = {
    'state_ewurum2025_biopbs': '8583148c56a9b37c6ca3a7aef525955025f361824de19f0fcd0ae65ee5b76bc1',
    'state_ewurum2025_pbs_lignin20': '5856c7cea340d926fd19006d6a3239667a37bf511a2a732b45e7be55d6bb0745',
    'state_ewurum2025_indulin_at': 'ec200324e45b590292340310b716511a74844b112101f699c1b96dbc9962831d',
    'state_ewurum2025_pbs_lignin10': 'd3520fbc42998adadb058ad81881f75673bc654daebdff18a093c8c1ed5286fe',
    'state_ewurum2025_pbs_lignin30': 'f4d76f238dfaee9fa4f1178e12f798561a7d0975ed67dd5c86d00787d2f1c0c5',
    'state_ewurum2025_pbs_lignin45': 'cec039b50c839f73cf068672a5aa87574f50094f206772e436084f791cbab1c1',
}
SOURCE_PROPERTY_SHA256 = {
    'refprop_ewurum2025_biopbs_youngs_modulus': '0e0fba6474e969f12477273c5581cddadc3677b8fad2ed9efa98151c80bf6a83',
    'refprop_ewurum2025_indulin_at_mass_density': 'ab3f99aae1e38e24846c5eade40a79304ed792a65ccdf68ef2d8666de402a345',
    'refprop_ewurum2025_pbs_lignin10_youngs_modulus': '8a5d487027ff5ad1020903e34cf0e46b13ff2806086685da6bdd2936917b4cd5',
    'refprop_ewurum2025_pbs_lignin20_youngs_modulus': 'b62f9fe6a06fdf704ea85a0ceba161849af4f439ae04f877beb53b476ec7261e',
    'refprop_ewurum2025_pbs_lignin30_youngs_modulus': '675fd2d29906c8890bb7d872ab1e64a3e509819f380ae6613ed2e4f42952938d',
    'refprop_ewurum2025_pbs_lignin45_youngs_modulus': '2fdd0cfdca28371401b4938c901da875464c492434b22980f0beb5fa3e6d0bd8',
    'refprop_ewurum2025_pbs_lignin_r10_youngs_modulus': '43b7ee8cf72faffa348d8a87b5128b4ec51bd170a28704ffdb2c7eb8a4e5133f',
    'refprop_ewurum2025_pbs_lignin_r20_youngs_modulus': '4c14f658b14fee279f56210f5494257f3f4e354bb71dda88ea89c447bb7a1f02',
    'refprop_ewurum2025_pbs_lignin_r30_youngs_modulus': '946c8ef385fe434567a199cb21a3481ada3daa51cc63c2e767743b5da4b9c283',
    'refprop_ewurum2025_pbs_lignin_r45_youngs_modulus': '757a0547c12bbb6a3483a5e616407f1ddfaa49852b525bf603c1a3c5e17d125f',
}
SOURCE_PROPERTY_UNION_SHA256 = 'c633168284f98f6c524907aa9c8053011123bf3d57c15cf70f2a129983b57e76'


def canonical_digest(value, *, newline=False):
    text = json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)
    return sha256((text + ('\n' if newline else '')).encode('utf-8')).hexdigest()


class EwurumReactiveQuery(unittest.TestCase):
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

    def test_four_reactive_formulations_keep_exact_means_sds_and_scope(self):
        self.assertEqual(self.status['counts'], {
            'local_catalog_unique_material_count': 1168,
            'local_material_state_count': 1169,
            'local_reference_property_count': 1180})
        for loading, modulus, sd, tukey, gel in FACTS:
            with self.subTest(formulation='R' + loading):
                identity_id = 'mat_ewurum2025_pbs_lignin_r' + loading
                state_id = 'state_ewurum2025_pbs_lignin_r' + loading + '_injection_molded'
                property_id = 'refprop_ewurum2025_pbs_lignin_r' + loading + '_youngs_modulus'
                resolved = self.post('resolve', state_id=state_id)
                self.assertEqual(canonical_digest(resolved), RESOLVED_SHA256[state_id])
                identity, state = resolved['identity'], resolved['state']
                self.assertEqual(identity['id'], identity_id)
                self.assertEqual(identity['category'], 'composite')
                self.assertIn('(Ewurum 2025)', identity['name'])
                self.assertIn('lignin percentage is relative to total polymer mass', identity['identity_scope'])
                self.assertIn('nominal DCP-containing formulation', identity['identity_scope'])
                self.assertIn('corresponding B-series simple blend', identity['identity_scope'])
                self.assertIn('nonzero gel fraction of ' + gel + '%', identity['identity_scope'])
                self.assertIn('not a certified final network or an extra selected property', identity['identity_scope'])
                self.assertIn('not a pure molecular species', identity['identity_scope'])
                self.assertIn('exact denominator and final retained DCP are not resolved', identity['identity_scope'])
                self.assertIn('hot-pressed DCP cross-linked PBS-lignin material, not the injection-molded tensile dog-bones',
                              identity['identity_scope'])
                self.assertIn('do not determine the tensile specimens\u2019 gel fraction or final network',
                              identity['identity_scope'])
                self.assertIsNone(resolved['grade'])
                self.assertIsNone(state['grade_id'])
                self.assertEqual(state['identity_id'], identity_id)
                self.assertEqual(state['source_designation'], 'R' + loading)
                self.assertEqual(state['property_ids'], [property_id])
                self.assertEqual(state['state']['product_form']['text'],
                                 'Injection-molded microtensile dog-bone specimens')
                self.assertEqual(state['state']['composition_or_purity']['text'],
                    'Nominal PBS / ' + loading + ' wt.% Indulin AT softwood kraft lignin '
                    '(percentage of total polymer mass), source R' + loading +
                    ' reactive series; 0.25 wt.% DCP added to PBS.')
                self.assertIn('BioPBS FZ91PM/FZ91PB without resolving a single grade',
                              state['state']['composition_or_purity']['notes'])
                self.assertIn('Preparation temperatures and drying are not tensile-test conditions',
                              state['state']['processing']['notes'])
                for field in ('conditioning', 'porosity', 'orientation', 'temper_or_heat_treatment'):
                    self.assertEqual(state['state'][field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(state['state'][field]['text'])
                prop, = resolved['properties']
                self.assertEqual((prop['id'], prop['material_state_id'], prop['source_id']),
                                 (property_id, state_id, SOURCE))
                self.assertEqual(prop['quantity'], 'youngs_modulus')
                self.assertEqual(prop['quantity_dimension'], 'pressure')
                self.assertEqual(prop['reported_value'], {'kind': 'scalar', 'unit_text': 'MPa',
                    'unit_code': 'MPa', 'value_text': modulus, 'number': modulus})
                self.assertEqual(prop['source_property_label'], 'Young\u2019s Modulus (MPa)')
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['reporting_basis'], 'reported_summary')
                self.assertEqual(prop['summary_statistic'], 'reported_mean')
                self.assertIsNone(prop['density_basis'])
                uncertainty = prop['uncertainty']
                self.assertEqual(uncertainty['type'], 'reported_standard_deviation')
                self.assertEqual(prop['uncertainty_status'], 'reported_standard_deviation')
                self.assertEqual((uncertainty['number'], uncertainty['value_text']), (sd, sd))
                self.assertEqual((uncertainty['unit_code'], uncertainty['unit_text']), ('MPa', 'MPa'))
                self.assertIsNone(uncertainty['coverage_factor'])
                self.assertIsNone(uncertainty['confidence_level'])
                self.assertIn('superscript ' + tukey + ' is a Tukey group', prop['uncertainty_note'])
                self.assertIn('SD was rounded up to the mean reported precision', prop['uncertainty_note'])
                self.assertIn('No SD-to-SE/CI conversion or derived endpoints', prop['uncertainty_note'])
                self.assertEqual(prop['sample_count']['value'], 10)
                self.assertEqual(prop['sample_count']['relation'], 'exact')
                self.assertIn('independent production-batch count is not reported', prop['sample_count']['scope'])
                self.assertEqual(prop['conditions']['test_standard']['text'],
                                 'ASTM D1708-18 (2018), source-cited edition in reference [32]')
                self.assertIn('Independent standard compliance remains unverified',
                              prop['conditions']['test_standard']['notes'])
                self.assertIn('no specimen dimensions or conditioning are inferred from the standard',
                              prop['conditions']['test_standard']['notes'])
                self.assertEqual(prop['conditions']['loading_rate']['text'], 'Crosshead speed 1 mm/min')
                for field in ('temperature', 'conditioning', 'direction'):
                    self.assertEqual(prop['conditions'][field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][field]['text'])
                humidity, = prop['conditions']['additional_conditions']
                self.assertEqual(humidity['name'], 'test_relative_humidity')
                self.assertEqual(humidity['fact']['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(humidity['fact']['text'])
                self.assertIsNone(prop['method_definition']['extraction_window'])
                self.assertIn('numerical strain-fit window and estimator are not stated',
                              prop['method_definition']['definition'])
                self.assertFalse(prop['universal_bound'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                source, = resolved['sources']
                self.assertEqual(source['id'], SOURCE)
                self.assertEqual(source['doi'], '10.3390/polym17020194')
                self.assertEqual(source['authors'], AUTHORS)
                self.assertEqual(source['license'], {'status': 'explicit_reuse_license_verified',
                                                     'identifier': 'CC-BY-4.0'})
                self.assertEqual(canonical_digest(source, newline=True), SOURCE_SHA256)
                self.assertEqual(prop['source_document']['sha256'], DOCUMENT_SHA256)
                self.assertIn('No new source download', prop['source_document']['inspection_scope'])

    def test_installed_cli_and_api_preserve_exact_objects_and_reused_source_union(self):
        expected_properties = []
        for state_id, digest in {**OLD_RESOLVED_SHA256, **RESOLVED_SHA256}.items():
            with self.subTest(state=state_id):
                resolved = self.post('resolve', state_id=state_id)
                self.assertEqual(canonical_digest(resolved), digest)
                expected_properties.extend(resolved['properties'])
                if state_id in RESOLVED_SHA256:
                    selected = self.cli('materials', '--identity-id', resolved['identity']['id'])
                    self.assertEqual(selected['records'], [resolved['state']])
                    self.assertEqual(selected['identities'], [resolved['identity']])
                    self.assertEqual(selected['grades'], [])
                    self.assertEqual(self.cli('reference-properties', '--id', resolved['properties'][0]['id'])['records'],
                                     resolved['properties'])
        expected_properties.sort(key=lambda row: row['id'])
        self.assertEqual(len(expected_properties), 10)
        self.assertEqual({row['id']: canonical_digest(row) for row in expected_properties}, SOURCE_PROPERTY_SHA256)
        self.assertEqual(canonical_digest(expected_properties), SOURCE_PROPERTY_UNION_SHA256)
        # One reused source owns six unchanged earlier facts plus four R facts.
        selected = self.post('search', kind='reference-properties', query=SOURCE, limit=100)
        self.assertFalse(selected['truncated'])
        self.assertEqual(sorted(selected['records'], key=lambda row: row['id']), expected_properties)
        for language in ('en', 'zh', 'ja', 'de'):
            with self.subTest(language=language):
                self.assertEqual(self.cli('reference-properties', '--source-id', SOURCE,
                                         '--lang', language)['records'], expected_properties)
        source = self.post('record', kind='sources', record_id=SOURCE)
        self.assertEqual(canonical_digest(source, newline=True), SOURCE_SHA256)
        self.assertEqual(self.cli('sources', '--id', SOURCE)['records'], [source])
        self.assertEqual(source['authors'], AUTHORS)

    def test_formal_count_excludes_computed_and_rejects_stale_versions(self):
        status = self.client.get('/api/catalog/project/status').json()
        self.assertTrue(status['enabled'])
        self.assertEqual(status['counts'], {
            'formal_project_admission_count': 1192,
            'legacy_source_qualified_identity_count': 1168,
            'reviewed_computed_composition_count': 24,
            'categories': {'metal': 44, 'inorganic': 71, 'polymer': 30,
                           'composite': 37, 'natural': 1010}})
        query = 'ewurum2025_pbs_lignin_r'
        data = {'version': status['version'], 'query': query,
                'partition': 'legacy-source-qualified', 'limit': 100}
        selected = self.client.post('/api/catalog/project/list', json=data)
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 4)
        self.assertEqual({row['id'] for row in selected.json()['records']}, {
            'legacy:mat_ewurum2025_pbs_lignin_r' + loading for loading, _, _, _, _ in FACTS})
        selected = self.client.post('/api/catalog/project/list', json={**data, 'partition': 'reviewed-computed'})
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 0)
        states = self.post('search', query=query, limit=100)
        self.assertEqual({row['id'] for row in states['records']}, set(RESOLVED_SHA256))
        self.assertFalse(states['truncated'])
        for route, request in (('resolve', {'state_id': 'state_ewurum2025_pbs_lignin_r10_injection_molded'}),
                               ('project/list', {'query': query}),
                               ('record', {'kind': 'sources', 'record_id': SOURCE})):
            with self.subTest(route=route):
                self.assertEqual(self.client.post('/api/catalog/' + route,
                                 json={'version': '0' * 64, **request}).status_code, 409)
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)

    def test_resolved_objects_are_detached_and_cannot_rewrite_qualifications(self):
        snapshot = CatalogSnapshot.from_packaged()
        graph = snapshot._graph
        self.assertEqual({'identity': len(graph['materials']['identities']),
                          'grade': len(graph['materials']['grades']),
                          'state': len(graph['materials']['records']),
                          'property': len(graph['reference_properties']['records']),
                          'source': len(graph['sources']['records'])},
                         {'identity': 1168, 'grade': 31, 'state': 1169, 'property': 1180, 'source': 128})
        state_id = 'state_ewurum2025_pbs_lignin_r10_injection_molded'
        before = snapshot.resolve(state_id)
        self.assertEqual(canonical_digest(before), RESOLVED_SHA256[state_id])
        changed = snapshot.resolve(state_id)
        changed['identity']['aliases'].append({'language': 'und', 'text': 'B10'})
        changed['properties'][0]['uncertainty']['number'] = '0'
        changed['properties'][0]['sample_count']['value'] = 40
        changed['properties'][0]['conditions']['conditioning']['text'] = '80 C for 12 h'
        changed['properties'][0]['conditions']['test_standard']['notes'] = 'Independently verified compliance'
        changed['properties'][0]['method_definition']['extraction_window'] = {'start': 0, 'end': 1}
        changed['state']['state']['composition_or_purity']['text'] = 'Known final DCP mass fraction'
        changed['state']['grade_id'] = 'grade_inferred_fz91pm'
        changed['sources'][0]['authors'].append('Invented Author')
        changed['sources'][0]['license']['identifier'] = 'unverified'
        self.assertEqual(snapshot.resolve(state_id), before)
        self.assertEqual(self.post('resolve', state_id=state_id), before)
        self.assertEqual(canonical_digest(snapshot.record('sources', SOURCE), newline=True), SOURCE_SHA256)

    def test_composite_category_does_not_infer_constituent_membership(self):
        status = self.client.get('/api/catalog/relationships/status').json()
        self.assertTrue(status['enabled'])
        pin = {'version': status['catalog_version'], 'relationship_version': status['relationship_version']}
        self.assertEqual(status['unique_identity_count'], 1168)
        self.assertEqual(status['membership_assertion_count'], 1173)
        self.assertEqual(status['identity_relationship_count'], 1)
        for category, count in {'metal': 32, 'inorganic': 59, 'polymer': 31,
                                'composite': 37, 'natural': 1010}.items():
            self.assertEqual(status['coverage'][category]['supported'], count)
        self.assertEqual(status['new_identities_admitted'], 0)
        self.assertFalse(status['provider_counts_combined'])
        for loading, _, _, _, _ in FACTS:
            identity_id = 'mat_ewurum2025_pbs_lignin_r' + loading
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
        # The older B20 assertion remains specific to B20, not inherited by R20.
        response = self.client.post('/api/catalog/relationships/identity',
            json={**pin, 'identity_id': 'mat_ewurum2025_pbs_lignin20'})
        self.assertEqual(response.status_code, 200)
        existing = response.json()['result']['data']
        self.assertEqual({item['concept'] for item in existing['memberships'] if item['status'] == 'supported'},
                         {'composite', 'polymer'})
        edge, = existing['relationships']
        self.assertEqual((edge['relation'], edge['target_identity_id']),
                         ('has_constituent', 'mat_ewurum2025_indulin_at'))
        self.assertIn('does not imply identity equivalence', edge['scope'])

    def test_read_only_routes_preserve_packaged_resources(self):
        paths = [files('materials_boundaries').joinpath('data', name + '.json')
                 for name in ('materials', 'reference_properties', 'sources')]
        before = [sha256(path.read_bytes()).hexdigest() for path in paths]
        for method in ('PUT', 'PATCH', 'DELETE'):
            for route in ('resolve', 'record', 'project/list', 'relationships/identity'):
                with self.subTest(method=method, route=route):
                    response = self.client.request(method, '/api/catalog/' + route,
                        json={'version': self.version,
                              'state_id': 'state_ewurum2025_pbs_lignin_r10_injection_molded',
                              'reported_value': {'number': '999'}})
                    self.assertEqual(response.status_code, 405)
        self.assertEqual([sha256(path.read_bytes()).hexdigest() for path in paths], before)
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
