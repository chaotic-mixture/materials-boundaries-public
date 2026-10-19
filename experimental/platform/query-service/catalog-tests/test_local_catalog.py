import concurrent.futures
import copy
from pathlib import Path
from threading import Event
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from materials_query.app import create_app
from materials_query import local_catalog as lc
try:
    from materials_query import catalog_snapshot as cs
except ModuleNotFoundError as error:
    if error.name != 'materials_boundaries': raise
    raise unittest.SkipTest('Optional repository core is not installed; see LOCAL_CATALOG.md') from error

class CatalogAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spy = patch.object(cs.contracts, 'validate_material_catalog', wraps=cs.contracts.validate_material_catalog)
        cls.validator = cls.spy.start()
        cls.app = create_app(enable_local_catalog=True)
        cls.client = TestClient(cls.app)
        cls.status = cls.client.get('/api/catalog/status').json()
        assert cls.status['enabled'], cls.status
        cls.version = cls.status['version']
        cls.first = cls.client.post('/api/catalog/search', json={'version':cls.version,'query':'a','limit':1}).json()['result']['records'][0]

    @classmethod
    def tearDownClass(cls): cls.spy.stop()
    def post(self, route, **data): return self.client.post('/api/catalog/'+route, json={'version':self.version, **data})
    def test_01_validation_once(self):
        self.assertEqual(self.validator.call_count,1)
        for _ in range(10): self.post('resolve',state_id=self.first['id']).raise_for_status()
        self.assertEqual(self.validator.call_count,1)
    def test_02_metadata_counts_and_versions(self):
        self.assertEqual(self.client.get('/api/health').json()['service_version'],'0.5.0.dev0')
        self.assertEqual(self.client.get('/openapi.json').json()['info']['version'],'0.5.0.dev0')
        from materials_platform import __version__ as umbrella_version
        self.assertEqual(umbrella_version,'0.5.0.dev0')
        self.assertEqual(self.status['counts']['local_catalog_unique_material_count'],1109)
        self.assertFalse(self.status['provider_counts_combined'])
        for name in ('version','content_digest','runtime_digest'): self.assertRegex(self.status[name],r'^[a-f0-9]{64}$')
    def test_03_exact_baseline_parity(self):
        from materials_boundaries.catalog import query_catalog
        for kind,rid in [('materials',self.first['id']),('reference-properties',self.first['property_ids'][0])]:
            response=self.post('exact',kind=kind,record_id=rid)
            self.assertEqual(response.json()['result'],query_catalog(kind,record_id=rid))
    def test_04_resolution_baseline_parity(self):
        from materials_boundaries.material_references import resolve_material
        from materials_boundaries.catalog import read_catalog
        self.assertEqual(self.post('resolve',state_id=self.first['id']).json()['result'],resolve_material(self.first['id'],*(read_catalog(k) for k in ('materials','reference_properties','sources'))))
    def test_nbs_source_scoped_density_resolution(self):
        for suffix, number in [('lif_harshaw', '2.638'),
                               ('kcl_mallinckrodt_kyd1', '1.9865'),
                               ('caf2_stockbarger_mit', '3.181')]:
            with self.subTest(material=suffix):
                response = self.post('resolve', state_id='state_nbs1953_' + suffix + '_xrd')
                self.assertEqual(response.status_code, 200)
                value = response.json()['result']
                self.assertEqual(value['identity']['id'], 'mat_nbs1953_' + suffix)
                self.assertEqual(value['identity']['category'], 'inorganic')
                self.assertIsNone(value['grade'])
                self.assertEqual([source['id'] for source in value['sources']],
                                 ['swanson_tatge_1953_nbs_circ539v1'])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'g/cm^3')
                self.assertEqual(prop['density_basis'], 'crystallographic')
                self.assertEqual(prop['evidence_kind'], 'published_measurement_derived_reference')
                self.assertEqual(prop['conditions']['temperature']['text'], '25 \u00b0C')
                self.assertIsNone(prop['uncertainty'])
                self.assertIsNone(prop['sample_count']['value'])
                self.assertFalse(prop['engineering_allowable'])
    def test_pa12_source_family_single_identity_resolution(self):
        identity_id = 'mat_zakrecki2025_pa12_pa2200'
        state_id = 'state_zakrecki2025_pa2200_sls_dyed_reference'
        found = self.post('search', query='PA2200', limit=100)
        self.assertEqual(found.status_code, 200)
        self.assertEqual([row['id'] for row in found.json()['result']['records']], [state_id])
        self.assertFalse(found.json()['result']['truncated'])
        response = self.post('resolve', state_id=state_id)
        self.assertEqual(response.status_code, 200)
        value = response.json()['result']
        self.assertEqual(value['identity']['id'], identity_id)
        self.assertEqual(value['identity']['category'], 'polymer')
        self.assertEqual(value['grade']['id'], 'grade_zakrecki2025_eos_pa2200')
        self.assertEqual(value['grade']['authority']['kind'], 'source_designation')
        self.assertEqual([source['id'] for source in value['sources']],
                         ['zakrecki_cieslik_2025_pa12_ageing'])
        self.assertEqual(len(value['properties']), 1)
        prop = value['properties'][0]
        self.assertEqual(prop['id'], 'refprop_zakrecki2025_pa2200_sls_reference_tensile_strength')
        self.assertEqual(prop['quantity'], 'tensile_strength')
        self.assertEqual(prop['reported_value']['number'], '43.72')
        self.assertEqual(prop['reported_value']['unit_code'], 'MPa')
        self.assertEqual(prop['uncertainty']['type'], 'reported_standard_deviation')
        self.assertEqual(prop['uncertainty']['number'], '1.03')
        self.assertEqual(prop['uncertainty']['unit_code'], 'MPa')
        self.assertEqual(prop['sample_count']['value'], 6)
        self.assertIsNone(prop['conditions']['temperature']['text'])
        self.assertEqual(prop['evaluation_support'], 'catalog_only')
        self.assertFalse(prop['engineering_allowable'])
        self.assertFalse(prop['verification']['independent_scientific_review'])
        self.assertFalse(prop['verification']['raw_data_reanalysis'])
        status = self.client.get('/api/catalog/project/status').json()
        selected = self.client.post('/api/catalog/project/list', json={
            'version': status['version'], 'query': 'PA2200',
            'partition': 'legacy-source-qualified', 'limit': 100})
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()['matched_count'], 1)
        self.assertEqual(selected.json()['records'][0]['identity']['id'], identity_id)

    def test_source_family_growth_six_oxide_resolution(self):
        cases = (
            ('beo', 'beo_brush_1743_1747', '3.008', '26 degrees C'),
            ('mgo', 'mgo_rca', '3.581', '25 degrees C'),
            ('cao', 'cao_baker_121647', '3.345', '27 degrees C'),
            ('tio2', 'tio2_rutile_mp559', '4.250', '26 degrees C'),
            ('cuo', 'cuo_jm3257', '6.51', '26 degrees C'),
            ('ceo2', 'ceo2_nbs419100', '7.215', '26 degrees C'),
        )
        formal_status = self.client.get('/api/catalog/project/status').json()
        for identity_suffix, state_suffix, number, temperature in cases:
            with self.subTest(identity=identity_suffix):
                identity_id = 'mat_nbs1953_' + identity_suffix
                state_id = 'state_nbs1953_' + state_suffix + '_xrd'
                property_id = 'refprop_nbs1953_' + state_suffix + '_crystallographic_density'
                resolved = self.post('resolve', state_id=state_id)
                self.assertEqual(resolved.status_code, 200)
                value = resolved.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], 'inorganic')
                self.assertIsNone(value['grade'])
                self.assertEqual([source['id'] for source in value['sources']],
                                 ['swanson_tatge_1953_nbs_circ539v1'])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'g/cm^3')
                self.assertEqual(prop['conditions']['temperature']['text'], temperature)
                self.assertEqual(prop['density_basis'], 'crystallographic')
                self.assertEqual(prop['determination_basis'], 'source_reports_calculation')
                self.assertEqual(prop['evidence_kind'], 'published_measurement_derived_reference')
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertIsNone(prop['uncertainty'])
                self.assertIsNone(prop['sample_count']['value'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                exact = self.post('record', kind='reference-properties', record_id=property_id)
                self.assertEqual(exact.status_code, 200)
                self.assertEqual(exact.json()['result'], prop)
                formal = self.client.post('/api/catalog/project/list', json={
                    'version': formal_status['version'], 'record_id': 'legacy:' + identity_id})
                self.assertEqual(formal.status_code, 200)
                self.assertEqual(formal.json()['matched_count'], 1)
                self.assertEqual(formal.json()['records'][0]['identity'], value['identity'])
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
        self.assertEqual(self.client.get('/api/catalog/project/status').json(), formal_status)

    def test_pur_formulation_batch_two_property_resolutions(self):
        cases = (('lpo2', '43.5', 'Lupranol 3300 66 g; Lupranol 3422 34 g'),
                 ('spo3', '43.2', 'SA-C_TOFA(50:50)/TMP 40 g'))
        formal_status = self.client.get('/api/catalog/project/status').json()
        for suffix, number, formulation in cases:
            with self.subTest(formulation=suffix):
                identity_id = 'mat_ivdre2024_' + suffix + '_rigid_pur'
                state_id = 'state_ivdre2024_' + suffix + '_rigid_pur'
                property_id = 'refprop_ivdre2024_' + suffix + '_rigid_pur_mass_density'
                response = self.post('resolve', state_id=state_id)
                self.assertEqual(response.status_code, 200)
                value = response.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], 'polymer')
                self.assertIsNone(value['grade'])
                self.assertIn(formulation, value['state']['state']['composition_or_purity']['text'])
                self.assertEqual([source['id'] for source in value['sources']],
                                 ['ivdre_2024_lpo_rigid_pur'])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'kg/m^3')
                self.assertEqual(prop['summary_statistic'], 'reported_value')
                self.assertEqual(prop['density_basis'], 'apparent')
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['conditions']['test_standard']['text'], 'ISO 845:2006')
                self.assertIsNone(prop['conditions']['temperature']['text'])
                self.assertIn('24 h at room temperature', prop['conditions']['conditioning']['text'])
                conditions = {row['name']: row['fact'] for row in prop['conditions']['additional_conditions']}
                for name in ('density_test_humidity', 'density_test_pressure', 'density_specimen_dimensions'):
                    self.assertEqual(conditions[name]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(conditions[name]['text'])
                self.assertIsNone(prop['uncertainty'])
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                exact = self.post('record', kind='reference-properties', record_id=property_id)
                self.assertEqual(exact.status_code, 200)
                self.assertEqual(exact.json()['result'], prop)
                selected = self.client.post('/api/catalog/project/list', json={
                    'version': formal_status['version'], 'record_id': 'legacy:' + identity_id})
                self.assertEqual(selected.status_code, 200)
                self.assertEqual(selected.json()['matched_count'], 1)
                self.assertEqual(selected.json()['records'][0]['identity'], value['identity'])
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
        self.assertEqual(self.client.get('/api/catalog/project/status').json(), formal_status)

    def test_primary_table_growth_eight_salt_resolution(self):
        cases = (
            ('hg2cl2', 'hg2cl2_general1891', '7.176', '26 degrees C'),
            ('hgcl2', 'hgcl2_baker101742', '5.49', '26 degrees C'),
            ('hgi2', 'hgi2_mallinckrodt', '6.325', '26 degrees C'),
            ('pbfcl', 'pbfcl_nbs', '7.13', '26 degrees C'),
            ('kcn', 'kcn_mallinckrodt_gnb', '1.555', '25 degrees C'),
            ('nacn', 'nacn_baker121444_cubic', '1.591', '26 degrees C'),
            ('sr_no3_2', 'sr_no3_2_mallinckrodt', '2.986', '26 degrees C'),
            ('ba_no3_2', 'ba_no3_2_mallinckrodt', '3.244', '26 degrees C'),
        )
        formal_status = self.client.get('/api/catalog/project/status').json()
        for identity_suffix, state_suffix, number, temperature in cases:
            with self.subTest(identity=identity_suffix):
                identity_id = 'mat_nbs1953_' + identity_suffix
                state_id = 'state_nbs1953_' + state_suffix + '_xrd'
                property_id = 'refprop_nbs1953_' + state_suffix + '_crystallographic_density'
                resolved = self.post('resolve', state_id=state_id)
                self.assertEqual(resolved.status_code, 200)
                value = resolved.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], 'inorganic')
                self.assertIsNone(value['grade'])
                if identity_suffix == 'nacn':
                    qualification = value['state']['state']['composition_or_purity']
                    self.assertIn('NaCN 96.2', qualification['text'])
                    self.assertIn('sodium-carbonate reflections', qualification['text'])
                    self.assertIn('orthorhombic NaCN line', qualification['text'])
                    self.assertIn('indexed cubic phase', qualification['notes'])
                self.assertEqual([source['id'] for source in value['sources']],
                                 ['swanson_tatge_1953_nbs_circ539v1'])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'g/cm^3')
                self.assertEqual(prop['conditions']['temperature']['text'], temperature)
                self.assertEqual(prop['density_basis'], 'crystallographic')
                self.assertEqual(prop['determination_basis'], 'source_reports_calculation')
                self.assertEqual(prop['evidence_kind'], 'published_measurement_derived_reference')
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertIsNone(prop['uncertainty'])
                self.assertIsNone(prop['sample_count']['value'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                exact = self.post('record', kind='reference-properties', record_id=property_id)
                self.assertEqual(exact.status_code, 200)
                self.assertEqual(exact.json()['result'], prop)
                formal = self.client.post('/api/catalog/project/list', json={
                    'version': formal_status['version'], 'record_id': 'legacy:' + identity_id})
                self.assertEqual(formal.status_code, 200)
                self.assertEqual(formal.json()['matched_count'], 1)
                self.assertEqual(formal.json()['records'][0]['identity'], value['identity'])
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
        self.assertEqual(self.client.get('/api/catalog/project/status').json(), formal_status)

    def test_rca_table_growth_three_reference_resolutions(self):
        cases = (
            ('znb2o4', 'znb2o4_rca_xii17', '3.605', '26 degrees C'),
            ('mg2sio4', 'mg2sio4_rca_x9', '3.213', '26 degrees C'),
            ('mgwo4', 'mgwo4_rca4', '6.897', '26 degrees C'),
        )
        formal_status = self.client.get('/api/catalog/project/status').json()
        for identity_suffix, state_suffix, number, temperature in cases:
            with self.subTest(identity=identity_suffix):
                identity_id = 'mat_nbs1953_' + identity_suffix
                state_id = 'state_nbs1953_' + state_suffix + '_xrd'
                property_id = 'refprop_nbs1953_' + state_suffix + '_crystallographic_density'
                resolved = self.post('resolve', state_id=state_id)
                self.assertEqual(resolved.status_code, 200)
                value = resolved.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], 'inorganic')
                self.assertIsNone(value['grade'])
                state = value['state']['state']
                phase = {'znb2o4': 'body-centered cubic', 'mg2sio4': 'orthorhombic forsterite',
                         'mgwo4': 'monoclinic'}[identity_suffix]
                self.assertIn(phase, state['product_form']['text'])
                if identity_suffix == 'znb2o4':
                    self.assertEqual(state['processing']['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(state['processing']['text'])
                else:
                    preparation = {'mg2sio4': '1500 degrees C', 'mgwo4': '1000 degrees C'}
                    self.assertIn(preparation[identity_suffix], state['processing']['text'])
                self.assertEqual([source['id'] for source in value['sources']],
                                 ['swanson_tatge_1953_nbs_circ539v1'])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'g/cm^3')
                self.assertEqual(prop['conditions']['temperature']['text'], temperature)
                self.assertEqual(prop['density_basis'], 'crystallographic')
                self.assertEqual(prop['summary_statistic'], 'reported_value')
                self.assertEqual(prop['determination_basis'], 'source_reports_calculation')
                self.assertEqual(prop['evidence_kind'], 'published_measurement_derived_reference')
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertIsNone(prop['uncertainty'])
                self.assertIsNone(prop['sample_count']['value'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                exact = self.post('record', kind='reference-properties', record_id=property_id)
                self.assertEqual(exact.status_code, 200)
                self.assertEqual(exact.json()['result'], prop)
                formal = self.client.post('/api/catalog/project/list', json={
                    'version': formal_status['version'], 'record_id': 'legacy:' + identity_id})
                self.assertEqual(formal.status_code, 200)
                self.assertEqual(formal.json()['matched_count'], 1)
                self.assertEqual(formal.json()['records'][0]['identity'], value['identity'])
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
        self.assertEqual(self.client.get('/api/catalog/project/status').json(), formal_status)

    def test_binary_oxide_growth_six_reference_resolutions(self):
        cases = (
            ('nio', 'nio_matthey3087', '6.806', '26 degrees C'),
            ('geo2', 'geo2_matthey3662', '4.280', '26 degrees C (NBS unit-cell determination)'),
            ('as2o3', 'as2o3_mallinckrodt906487', '3.8654', '25 degrees C'),
            ('seo2', 'seo2_mallinckrodt', '4.16', '26 degrees C'),
            ('sno2', 'sno2_matthey2763', '6.995', '26 degrees C (NBS unit-cell determination)'),
            ('tho2', 'tho2_lindsay', '9.991', '26 degrees C'),
        )
        formal_status = self.client.get('/api/catalog/project/status').json()
        for identity_suffix, state_suffix, number, temperature in cases:
            with self.subTest(identity=identity_suffix):
                identity_id = 'mat_nbs1953_' + identity_suffix
                state_id = 'state_nbs1953_' + state_suffix + '_xrd'
                property_id = 'refprop_nbs1953_' + state_suffix + '_crystallographic_density'
                resolved = self.post('resolve', state_id=state_id)
                self.assertEqual(resolved.status_code, 200)
                value = resolved.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], 'inorganic')
                self.assertIsNone(value['grade'])
                self.assertEqual([source['id'] for source in value['sources']],
                                 ['swanson_tatge_1953_nbs_circ539v1'])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'g/cm^3')
                self.assertEqual(prop['conditions']['temperature']['text'], temperature)
                self.assertEqual(prop['density_basis'], 'crystallographic')
                self.assertEqual(prop['summary_statistic'], 'reported_value')
                self.assertEqual(prop['determination_basis'], 'source_reports_calculation')
                self.assertEqual(prop['evidence_kind'], 'published_measurement_derived_reference')
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertIsNone(prop['uncertainty'])
                self.assertIsNone(prop['sample_count']['value'])
                self.assertFalse(prop['engineering_allowable'])
                self.assertFalse(prop['verification']['independent_scientific_review'])
                self.assertFalse(prop['verification']['raw_data_reanalysis'])
                exact = self.post('record', kind='reference-properties', record_id=property_id)
                self.assertEqual(exact.status_code, 200)
                self.assertEqual(exact.json()['result'], prop)
                formal = self.client.post('/api/catalog/project/list', json={
                    'version': formal_status['version'], 'record_id': 'legacy:' + identity_id})
                self.assertEqual(formal.status_code, 200)
                self.assertEqual(formal.json()['matched_count'], 1)
                self.assertEqual(formal.json()['records'][0]['identity'], value['identity'])
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
        self.assertEqual(self.client.get('/api/catalog/project/status').json(), formal_status)

    def test_05_copy_isolation(self):
        expected=self.post('resolve',state_id=self.first['id']).json()
        mutated=copy.deepcopy(expected); mutated['result']['state'].clear();mutated['result']['sources'].clear()
        self.assertEqual(expected,self.post('resolve',state_id=self.first['id']).json())
        meta=self.client.get('/api/catalog/status').json();meta['counts'].clear()
        self.assertEqual(self.status,self.client.get('/api/catalog/status').json())
    def test_06_record_kinds(self):
        resolved=self.post('resolve',state_id=self.first['id']).json()['result']
        for kind,row in [('identities',resolved['identity']),('materials',resolved['state']),('reference-properties',resolved['properties'][0]),('sources',resolved['sources'][0])]:
            self.assertEqual(self.post('record',kind=kind,record_id=row['id']).json()['result'],row)
        if resolved['grade']:self.assertEqual(self.post('record',kind='grades',record_id=resolved['grade']['id']).json()['result'],resolved['grade'])
    def test_07_stale_pin(self):
        self.assertEqual(self.client.post('/api/catalog/search',json={'version':'0'*64,'query':'wood'}).status_code,409)
    def test_08_missing_pin(self): self.assertEqual(self.client.post('/api/catalog/search',json={'query':'wood'}).status_code,422)
    def test_09_unknown_id(self): self.assertEqual(self.post('resolve',state_id='unknown').status_code,404)
    def test_10_invalid_search(self):
        for q,code in [('',422),(' '*3,400),('x'*257,422),(' '.join(['a']*17),400)]:self.assertEqual(self.post('search',query=q).status_code,code)
        for limit in (0,101,True,1.0):self.assertEqual(self.post('search',query='wood',limit=limit).status_code,422)
    def test_11_no_paths_mutation_or_extra_fields(self):
        self.assertEqual(self.post('search',query='wood',path='/tmp/x').status_code,422)
        for route in ('refresh','reload','upload'):self.assertEqual(self.post(route).status_code,404)
        self.assertEqual(self.client.put('/api/catalog/status',json={}).status_code,405)
    def test_12_parallel_reads(self):
        def read(_):
            response=self.post('resolve',state_id=self.first['id'])
            return response.status_code,response.json()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(read,range(32)))
        expected=self.post('resolve',state_id=self.first['id']).json()
        self.assertTrue(any(code==200 for code,_ in results))
        for code,value in results:self.assertIn(code,(200,429));self.assertTrue(code==429 or value==expected)
    def test_13_concurrency_bound_release(self):
        entered=[Event(),Event()];release=Event();counter=[]
        original=cs.CatalogSnapshot.resolve
        def blocked(snapshot,state):
            index=len(counter);counter.append(index);entered[index].set();release.wait(5);return original(snapshot,state)
        with patch.object(cs.CatalogSnapshot,'resolve',blocked):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                a=pool.submit(self.post,'resolve',state_id=self.first['id']);self.assertTrue(entered[0].wait(3))
                b=pool.submit(self.post,'resolve',state_id=self.first['id']);self.assertTrue(entered[1].wait(3))
                try:self.assertEqual(self.post('resolve',state_id=self.first['id']).status_code,429)
                finally:release.set()
                self.assertEqual(a.result().status_code,200);self.assertEqual(b.result().status_code,200)
        self.assertEqual(self.post('resolve',state_id=self.first['id']).status_code,200)
    def test_14_local_origin_and_body_bounds(self):
        self.assertEqual(self.client.post('/api/catalog/search',json={},headers={'Origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/catalog/search',content=b'x'*32769).status_code,413)
    def test_15_ui_static(self):
        self.assertEqual(self.client.get('/catalog').status_code,200)
        js=self.client.get('/static/catalog.js').text
        self.assertNotIn('innerHTML',js);self.assertIn('textContent',js);self.assertIn('value.version !== version',js)
    def test_16_disabled_mp_unchanged(self):
        self.assertEqual(self.client.post('/api/search',json={'provider':'materials_project','formula':'Si'}).status_code,503)
        self.assertIsNone(self.client.post('/api/demo',json={'provider':'nomad'}).json()['counts']['unique_material_count'])

class Initialization(unittest.TestCase):
    def test_default_no_core_load(self):
        with patch.object(lc,'load_installed_snapshot',side_effect=AssertionError('must not load')):
            self.assertEqual(TestClient(create_app()).get('/api/catalog/status').json()['reason'],'not_enabled')
    def test_missing_core_disabled(self):
        with patch.object(lc,'find_spec',return_value=None):
            client=TestClient(create_app(enable_local_catalog=True))
            self.assertEqual(client.get('/api/catalog/status').json()['reason'],'core_not_installed')
            self.assertEqual(client.post('/api/catalog/search',json={'version':'0'*64,'query':'wood'}).status_code,503)
            self.assertEqual(client.get('/api/health').status_code,200)
    def test_import_discovery_failure_disabled(self):
        with patch.object(lc,'find_spec',side_effect=ValueError('invalid import state')):
            self.assertEqual(TestClient(create_app(enable_local_catalog=True)).get('/api/catalog/status').json()['reason'],'core_initialization_failed')
    def test_validation_failure_disabled(self):
        with patch.object(cs.CatalogSnapshot,'from_packaged',side_effect=ValueError('/private/path broken')):
            client=TestClient(create_app(enable_local_catalog=True));response=client.get('/api/catalog/status')
            self.assertEqual(response.json()['reason'],'core_initialization_failed');self.assertNotIn('/private',response.text)
    def test_revision_module_byte_parity(self):
        import hashlib
        self.assertEqual(hashlib.sha256(Path(cs.__file__).read_bytes()).hexdigest(),'75f63efb42f419eeae0fd08db63369350d603c52f01c4149915f048d74d6cc12')
