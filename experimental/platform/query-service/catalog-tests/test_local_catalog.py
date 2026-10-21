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
        self.assertEqual(self.status['counts']['local_catalog_unique_material_count'],1142)
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

    def test_filament_measured_reference_resolutions(self):
        cases = [('state_aniskevich_2023_ultimaker_pc_filament',
          'mat_aniskevich_2023_ultimaker_pc',
          'polymer',
          None,
          'PC, White 1642',
          (('refprop_aniskevich_2023_ultimaker_pc_filament_tensile_modulus',
            'tensile_modulus',
            '2118.92060622187',
            'MPa'),
           ('refprop_aniskevich_2023_ultimaker_pc_filament_tensile_strength',
            'tensile_strength',
            '62.629195615958977',
            'MPa')),
          ('aniskevich_bulderberga_2023_polymer_mechanical_characterisation',)),
         ('state_aniskevich_2023_ultimaker_pp_filament',
          'mat_aniskevich_2023_ultimaker_pp',
          'polymer',
          None,
          'PP, Natural',
          (('refprop_aniskevich_2023_ultimaker_pp_filament_tensile_modulus',
            'tensile_modulus',
            '413.57473001954821',
            'MPa'),
           ('refprop_aniskevich_2023_ultimaker_pp_filament_tensile_strength',
            'tensile_strength',
            '15.984863319060555',
            'MPa')),
          ('aniskevich_bulderberga_2023_polymer_mechanical_characterisation',)),
         ('state_aniskevich_2023_ultimaker_tpu95a_filament',
          'mat_aniskevich_2023_ultimaker_tpu95a',
          'polymer',
          None,
          'TPU95A, White 1755',
          (('refprop_aniskevich_2023_ultimaker_tpu95a_filament_tensile_modulus',
            'tensile_modulus',
            '141.82919658635231',
            'MPa'),
           ('refprop_aniskevich_2023_ultimaker_tpu95a_filament_tensile_strength',
            'tensile_strength',
            '31.701601361675458',
            'MPa')),
          ('aniskevich_bulderberga_2023_polymer_mechanical_characterisation',)),
         ('state_aniskevich_2023_protopasta_conductive_pla_filament',
          'mat_aniskevich_2023_protopasta_conductive_pla',
          'composite',
          None,
          'PLA conductive, CDP12805 Batch 171201',
          (('refprop_aniskevich_2023_protopasta_conductive_pla_filament_tensile_modulus',
            'tensile_modulus',
            '1664.6684808244395',
            'MPa'),
           ('refprop_aniskevich_2023_protopasta_conductive_pla_filament_tensile_strength',
            'tensile_strength',
            '25.64018578078505',
            'MPa')),
          ('aniskevich_bulderberga_2023_polymer_mechanical_characterisation', 'protopasta_conductive_pla_faq')),
         ('state_aniskevich_2023_kimya_abs_esd_filament',
          'mat_aniskevich_2023_kimya_abs_esd',
          'composite',
          None,
          'ABS ESD',
          (('refprop_aniskevich_2023_kimya_abs_esd_filament_tensile_modulus',
            'tensile_modulus',
            '1346.1998101456204',
            'MPa'),
           ('refprop_aniskevich_2023_kimya_abs_esd_filament_tensile_strength',
            'tensile_strength',
            '28.849993772107013',
            'MPa')),
          ('aniskevich_bulderberga_2023_polymer_mechanical_characterisation',
           'makerbot_method_materials_20191119')),
         ('state_aniskevich_2023_addnorth_koltron_g1_filament',
          'mat_aniskevich_2023_addnorth_koltron_g1',
          'composite',
          None,
          'Koltron G1',
          (('refprop_aniskevich_2023_addnorth_koltron_g1_filament_tensile_modulus',
            'tensile_modulus',
            '1145.4193020117505',
            'MPa'),
           ('refprop_aniskevich_2023_addnorth_koltron_g1_filament_tensile_strength',
            'tensile_strength',
            '23.911741539390583',
            'MPa')),
          ('addnorth_product_catalogue_2022',
           'aniskevich_bulderberga_2023_polymer_mechanical_characterisation')),
         ('state_aniskevich_2023_stratasys_antero800na_filament',
          'mat_aniskevich_2023_stratasys_antero800na',
          'polymer',
          None,
          'PEKK, Antero 800NA',
          (('refprop_aniskevich_2023_stratasys_antero800na_filament_tensile_modulus',
            'tensile_modulus',
            '2916.2651226028183',
            'MPa'),
           ('refprop_aniskevich_2023_stratasys_antero800na_filament_tensile_strength',
            'tensile_strength',
            '82.71385816891096',
            'MPa')),
          ('aniskevich_bulderberga_2023_polymer_mechanical_characterisation',)),
         ('state_aniskevich_2023_stratasys_ultem9085cg_filament',
          'mat_aniskevich_2023_stratasys_ultem9085cg',
          'polymer',
          None,
          'PEI, ULTEM 9085 CG',
          (('refprop_aniskevich_2023_stratasys_ultem9085cg_filament_tensile_modulus',
            'tensile_modulus',
            '2623.780515411815',
            'MPa'),
           ('refprop_aniskevich_2023_stratasys_ultem9085cg_filament_tensile_strength',
            'tensile_strength',
            '82.600893124060548',
            'MPa')),
          ('aniskevich_bulderberga_2023_polymer_mechanical_characterisation',))]
        common = {'evidence_kind': 'published_experimental_reference',
         'reporting_basis': 'reported_summary',
         'summary_statistic': 'reported_mean',
         'determination_basis': 'source_reports_measurement',
         'source_id': 'aniskevich_bulderberga_2023_polymer_mechanical_characterisation',
         'uncertainty': None,
         'uncertainty_status': 'not_reported_in_inspected_source',
         'source_document_sha256': '830b2c9277dcc2d03265b63e311a5e7089c258ebb6a389b45d07601ae4b2e4e7',
         'conditions': {'temperature': {'status': 'not_reported_in_inspected_source', 'text': None},
                        'test_standard': {'status': 'not_reported_in_inspected_source', 'text': None},
                        'test_method': {'status': 'reported',
                                        'text': 'Tensile testing of reference filament 2.8 mm; source reports '
                                                'E-mod and tensile strength'},
                        'direction': {'status': 'not_reported_in_inspected_source', 'text': None},
                        'conditioning': {'status': 'not_reported_in_inspected_source', 'text': None},
                        'loading_rate': {'status': 'reported', 'text': '10 mm/min'}},
         'sample_count': {'value': None, 'relation': 'not_reported'}}
        source_licenses = {'aniskevich_bulderberga_2023_polymer_mechanical_characterisation': {'status': 'explicit_reuse_license_verified',
                                                                             'identifier': 'CC-BY-4.0'},
         'protopasta_conductive_pla_faq': {'status': 'no_explicit_reuse_license_verified_limited_factual_curation_only',
                                           'identifier': None},
         'addnorth_product_catalogue_2022': {'status': 'no_explicit_reuse_license_verified_limited_factual_curation_only',
                                             'identifier': None},
         'makerbot_method_materials_20191119': {'status': 'no_explicit_reuse_license_verified_limited_factual_curation_only',
                                                'identifier': None}}
        formal_status = self.client.get('/api/catalog/project/status').json()
        for state_id, identity_id, category, grade_id, designation, properties, source_ids in cases:
            with self.subTest(filament=state_id):
                response = self.post('resolve', state_id=state_id)
                self.assertEqual(response.status_code, 200)
                value = response.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], category)
                if grade_id is None:
                    self.assertIsNone(value['grade'])
                else:
                    self.assertEqual(value['grade']['id'], grade_id)
                    self.assertEqual(value['grade']['identity_id'], identity_id)
                self.assertEqual(value['state']['id'], state_id)
                self.assertEqual(value['state']['identity_id'], identity_id)
                self.assertEqual(value['state']['grade_id'], grade_id)
                self.assertEqual(value['state']['source_designation'], designation)
                self.assertEqual(value['state']['property_ids'], [row[0] for row in properties])
                self.assertEqual([row['id'] for row in value['sources']], list(source_ids))
                for source in value['sources']:
                    self.assertEqual(source['license'], source_licenses[source['id']])
                self.assertEqual(len(value['properties']), 2)
                for prop, (pid, quantity, number, unit) in zip(value['properties'], properties):
                    self.assertEqual(prop['id'], pid)
                    self.assertEqual(prop['material_state_id'], state_id)
                    self.assertEqual(prop['quantity'], quantity)
                    self.assertEqual(prop['quantity_dimension'], 'pressure')
                    self.assertEqual(prop['reported_value']['number'], number)
                    self.assertEqual(prop['reported_value']['unit_code'], unit)
                    ordinary = set(common) - {'conditions', 'sample_count', 'source_document_sha256'}
                    self.assertEqual({key: prop[key] for key in ordinary}, {key: common[key] for key in ordinary})
                    self.assertEqual({key: {field: item[field] for field in ('status', 'text')}
                                      for key, item in prop['conditions'].items()}, common['conditions'])
                    self.assertEqual({key: prop['sample_count'][key] for key in ('value', 'relation')}, common['sample_count'])
                    self.assertEqual(prop['source_document']['sha256'], common['source_document_sha256'])
                    self.assertIsNone(prop['sample_count']['value'])
                    self.assertEqual(prop['evaluation_support'], 'catalog_only')
                    self.assertFalse(prop['universal_bound'])
                    self.assertFalse(prop['engineering_allowable'])
                    self.assertFalse(prop['verification']['independent_scientific_review'])
                    self.assertFalse(prop['verification']['raw_data_reanalysis'])
                    exact = self.post('record', kind='reference-properties', record_id=pid)
                    self.assertEqual(exact.status_code, 200)
                    self.assertEqual(exact.json()['result'], prop)
                # Exact state IDs are within the bounded API's indexed search fields.
                search = self.post('search', query=state_id, limit=100)
                self.assertEqual(search.status_code, 200)
                self.assertIn(state_id, {row['id'] for row in search.json()['result']['records']})
                self.assertFalse(search.json()['result']['truncated'])
                formal = self.client.post('/api/catalog/project/list', json={
                    'version': formal_status['version'], 'record_id': 'legacy:' + identity_id})
                self.assertEqual(formal.status_code, 200)
                self.assertEqual(formal.json()['matched_count'], 1)
                self.assertEqual(formal.json()['records'][0]['identity'], value['identity'])
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
        self.assertEqual(self.client.get('/api/catalog/project/status').json(), formal_status)

    def test_outokumpu_core_ten_reference_resolutions(self):
        cases = (('304', '304/4301', '1.4301', 'S30400', '200'),
                 ('304ln', '304LN/4311', '1.4311', 'S30453', '200'),
                 ('305', '305/4303', '1.4303', 'S30500', '200'),
                 ('321', '321/4541', '1.4541', 'S32100', '200'),
                 ('347', '347/4550', '1.4550', 'S34700', '200'),
                 ('301ln', '301LN/4318', '1.4318', 'S30153', '200'),
                 ('301', '301/4310', '1.4310', 'S30100', '200'),
                 ('201', '201/4372', '1.4372', 'S20100', '200'),
                 ('201ln', '201LN/4372', '1.4372', 'S20153', '200'),
                 ('4622', '4622', '1.4622', 'S44330', '220'))
        source_id = 'outokumpu_core_1560en4_202211'
        formal_status = self.client.get('/api/catalog/project/status').json()
        for suffix, designation, en, uns, number in cases:
            with self.subTest(formulation=suffix):
                stem = 'outokumpu_' + suffix
                identity_id, grade_id, state_id = 'mat_' + stem, 'grade_' + stem, 'state_' + stem
                property_id = 'refprop_' + stem + '_youngs_modulus'
                response = self.post('resolve', state_id=state_id)
                self.assertEqual(response.status_code, 200)
                value = response.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], 'metal')
                self.assertEqual(value['grade']['id'], grade_id)
                self.assertEqual(value['grade']['identity_id'], identity_id)
                self.assertEqual(value['grade']['authority'], {'kind': 'manufacturer', 'name': 'Outokumpu'})
                self.assertEqual(value['grade']['designation'], 'Core ' + designation)
                self.assertEqual([alias['text'] for alias in value['grade']['aliases']],
                                 ['EN ' + en + ' / UNS ' + uns, 'UNS ' + uns])
                self.assertEqual(value['state']['id'], state_id)
                self.assertEqual(value['state']['identity_id'], identity_id)
                self.assertEqual(value['state']['grade_id'], grade_id)
                self.assertEqual(value['state']['source_designation'], 'Core ' + designation)
                self.assertEqual(value['state']['property_ids'], [property_id])
                composition = value['state']['state']['composition_or_purity']
                self.assertEqual(composition['status'], 'reported')
                self.assertIn('EN ' + en, composition['text'])
                self.assertIn('UNS ' + uns, composition['text'])
                self.assertEqual([source['id'] for source in value['sources']], [source_id])
                self.assertEqual(value['sources'][0]['license']['status'],
                                 'no_explicit_reuse_license_verified_limited_factual_curation_only')
                self.assertIsNone(value['sources'][0]['license']['identifier'])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['material_state_id'], state_id)
                self.assertEqual(prop['quantity'], 'youngs_modulus')
                self.assertEqual(prop['quantity_dimension'], 'pressure')
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'GPa')
                self.assertEqual(prop['evidence_kind'], 'manufacturer_reference')
                self.assertEqual(prop['reporting_basis'], 'not_stated')
                self.assertEqual(prop['summary_statistic'], 'not_stated')
                self.assertEqual(prop['determination_basis'],
                                 'source_reports_measurement' if suffix == '4622' else 'not_stated')
                self.assertEqual(prop['source_id'], source_id)
                self.assertEqual(prop['conditions']['temperature']['status'], 'reported')
                self.assertEqual(prop['conditions']['temperature']['text'], '20 \u00b0C')
                self.assertEqual(prop['conditions']['test_standard']['text'], 'EN 10088-1')
                for field in ('test_method', 'direction', 'conditioning', 'loading_rate'):
                    self.assertEqual(prop['conditions'][field]['status'], 'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][field]['text'])
                self.assertIsNone(prop['density_basis'])
                self.assertIsNone(prop['uncertainty'])
                self.assertEqual(prop['uncertainty_status'], 'not_reported_in_inspected_source')
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                self.assertEqual(prop['source_document']['sha256'],
                                 '91d2f4b1340562b0d692a3921a5b0ea2518ddcb6cbdcc9ec97a3d7ad886d7ad9')
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertFalse(prop['universal_bound'])
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
        # Bounded API search indexes designations, not EN aliases or composition prose.
        # The shared designation fragment 4372 must retain both distinct states.
        shared = self.post('search', query='4372', limit=100)
        self.assertEqual(shared.status_code, 200)
        self.assertEqual({row['id'] for row in shared.json()['result']['records']},
                         {'state_outokumpu_201', 'state_outokumpu_201ln'})
        self.assertFalse(shared.json()['result']['truncated'])
        self.assertEqual(self.client.get('/api/catalog/status').json(), self.status)
        self.assertEqual(self.client.get('/api/catalog/project/status').json(), formal_status)

    def test_nbr_rcf_six_reference_resolutions(self):
        cases = (('5', 'B', '5.26', '0.78'), ('10', 'C', '5.11', '1.27'),
                 ('20', 'D', '5.33', '0.74'), ('30', 'E', '5.47', '1.05'),
                 ('40', 'F', '4.60', '0.68'), ('50', 'G', '4.57', '0.72'))
        source_id = 'tamas_benyei_santha_2025_nbr_rcf'
        formal_status = self.client.get('/api/catalog/project/status').json()
        for loading, label, number, plus_minus in cases:
            with self.subTest(formulation=label):
                stem = 'tamas_benyei2025_nbr_mcf' + loading
                identity_id, state_id = 'mat_' + stem, 'state_' + stem
                property_id = 'refprop_' + stem + '_tensile_strength'
                response = self.post('resolve', state_id=state_id)
                self.assertEqual(response.status_code, 200)
                value = response.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], 'composite')
                self.assertIsNone(value['grade'])
                self.assertEqual(value['state']['id'], state_id)
                self.assertEqual(value['state']['source_designation'], label)
                self.assertEqual(value['state']['state']['composition_or_purity']['text'],
                                 'Recipe (phr, source Table 3): PERBUNAN 3445 F NBR 100; '
                                 'PEG4000 4; mCF ' + loading + '; stearic acid 1; ZnO 5; '
                                 'Sul 1.5; MBTS 2.5. Sul denotes ACTMIX S-80 product input.')
                self.assertEqual([source['id'] for source in value['sources']], [source_id])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['material_state_id'], state_id)
                self.assertEqual(prop['quantity'], 'tensile_strength')
                self.assertEqual(prop['quantity_dimension'], 'pressure')
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'MPa')
                self.assertEqual(prop['reporting_basis'], 'reported_summary')
                self.assertEqual(prop['summary_statistic'], 'reported_mean')
                self.assertIsNone(prop['density_basis'])
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['source_id'], source_id)
                for field in ('temperature', 'conditioning'):
                    self.assertEqual(prop['conditions'][field]['status'],
                                     'not_reported_in_inspected_source')
                    self.assertIsNone(prop['conditions'][field]['text'])
                humidity = prop['conditions']['additional_conditions']
                self.assertEqual([row['name'] for row in humidity], ['test_relative_humidity'])
                self.assertEqual(humidity[0]['fact']['status'], 'not_reported_in_inspected_source')
                self.assertIsNone(humidity[0]['fact']['text'])
                self.assertEqual(prop['conditions']['test_standard']['text'],
                                 'ISO 37; Type 2 dumbbell specimens')
                self.assertEqual(prop['conditions']['loading_rate']['text'],
                                 '500 mm/min crosshead speed')
                self.assertEqual(prop['conditions']['direction']['status'], 'reported')
                self.assertIsNone(prop['sample_count']['value'])
                self.assertEqual(prop['sample_count']['relation'], 'not_reported')
                self.assertEqual(prop['uncertainty_status'], 'reported_plus_minus_unspecified')
                self.assertEqual(prop['uncertainty']['type'], 'reported_plus_minus_unspecified')
                self.assertEqual(prop['uncertainty']['number'], plus_minus)
                self.assertEqual(prop['uncertainty']['unit_code'], 'MPa')
                self.assertIsNone(prop['uncertainty']['coverage_factor'])
                self.assertIsNone(prop['uncertainty']['confidence_level'])
                self.assertEqual(len(prop['source_discrepancies']), 1)
                discrepancy = prop['source_discrepancies'][0]
                self.assertTrue(discrepancy['description'])
                self.assertTrue(discrepancy['disposition'])
                self.assertEqual({row['source_id'] for row in discrepancy['evidence']}, {source_id})
                self.assertTrue(all('source_discrepancy' in row['supports']
                                    for row in discrepancy['evidence']))
                self.assertEqual(prop['source_document']['sha256'],
                                 '6922d25630c21c03062722a3efdf621b87129c40f06097625161364151c87aef')
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
                self.assertFalse(prop['universal_bound'])
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

    def test_nr_nanoclay_six_reference_resolutions(self):
        cases = (('1mmt', 'NR_1MMT', 'MMT', '1.0', '0.960', '0.003'),
                 ('3mmt', 'NR_3MMT', 'MMT', '3.0', '0.973', '0.001'),
                 ('5mmt', 'NR_5MMT', 'MMT', '5.0', '0.981', '0.005'),
                 ('1ommt', 'NR_1O-MMT', 'O-MMT', '1.0', '0.959', '0.001'),
                 ('3ommt', 'NR_3O-MMT', 'O-MMT', '3.0', '0.966', '0.001'),
                 ('5ommt', 'NR_5O-MMT', 'O-MMT', '5.0', '0.971', '0.003'))
        formal_status = self.client.get('/api/catalog/project/status').json()
        for suffix, label, filler, loading, number, plus_minus in cases:
            with self.subTest(formulation=label):
                stem = 'bianchi2025_nr_' + suffix
                identity_id, state_id = 'mat_' + stem, 'state_' + stem
                property_id = 'refprop_' + stem + '_mass_density'
                response = self.post('resolve', state_id=state_id)
                self.assertEqual(response.status_code, 200)
                value = response.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], 'composite')
                self.assertIsNone(value['grade'])
                self.assertEqual(value['state']['source_designation'], label)
                composition = value['state']['state']['composition_or_purity']
                self.assertIn('phr = parts per hundred rubber', composition['text'])
                self.assertIn('SMR 10 natural rubber 100.0; sulfur 1.5; ZnO 5.0; '
                              'stearic acid 2.0; ZDBC 0.7', composition['text'])
                self.assertIn('; ' + filler + ' ' + loading + '.', composition['text'])
                self.assertIn('other nanoclay input with a dash', composition['text'])
                self.assertIn('modifier identity/amount in the finished composite', composition['notes'])
                self.assertIn('not established', composition['notes'])
                self.assertEqual([source['id'] for source in value['sources']],
                                 ['bianchi_2025_nr_nanoclay'])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['quantity'], 'mass_density')
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'g/cm^3')
                self.assertEqual(prop['reporting_basis'], 'reported_summary')
                self.assertEqual(prop['summary_statistic'], 'reported_value')
                self.assertEqual(prop['density_basis'], 'not_stated')
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['conditions']['temperature']['text'],
                                 'Room temperature; numerical temperature unspecified')
                self.assertEqual(prop['sample_count']['value'], 3)
                self.assertEqual(prop['sample_count']['relation'], 'exact')
                self.assertEqual(prop['uncertainty_status'], 'reported_plus_minus_unspecified')
                self.assertEqual(prop['uncertainty']['type'], 'reported_plus_minus_unspecified')
                self.assertEqual(prop['uncertainty']['number'], plus_minus)
                self.assertEqual(prop['uncertainty']['unit_code'], 'g/cm^3')
                self.assertIsNone(prop['uncertainty']['coverage_factor'])
                self.assertIsNone(prop['uncertainty']['confidence_level'])
                if suffix == '3mmt':
                    self.assertIn('NR_3MMsT', [row['text'] for row in value['state']['aliases']])
                    self.assertIn('NR_3MMsT', prop['evidence'][0]['locator'])
                    self.assertTrue(prop['source_discrepancies'])
                    self.assertIn('unique 3 phr natural-MMT formulation in Table 8', prop['source_discrepancies'][0]['disposition'])
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
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

    def test_mtibe_hybrid_three_reference_resolutions(self):
        cases = (('5', '95/5/1.5', '261.88', '14.78'),
                 ('10', '90/10/1.5', '304.52', '5.22'),
                 ('15', '85/15/1.5', '347.44', '16.92'))
        formal_status = self.client.get('/api/catalog/project/status').json()
        for loading, recipe, number, plus_minus in cases:
            with self.subTest(formulation=recipe):
                stem = 'mtibe2022_pbs_pbat_lignin' + loading + '_zno'
                identity_id, state_id = 'mat_' + stem, 'state_' + stem
                property_id = 'refprop_' + stem + '_tensile_modulus'
                response = self.post('resolve', state_id=state_id)
                self.assertEqual(response.status_code, 200)
                value = response.json()['result']
                self.assertEqual(value['identity']['id'], identity_id)
                self.assertEqual(value['identity']['category'], 'composite')
                self.assertIsNone(value['grade'])
                composition = value['state']['state']['composition_or_purity']['text']
                self.assertIn('= ' + recipe + ' as printed', composition)
                self.assertIn('70/30, ratio basis unspecified', composition)
                self.assertIn('entries total 101.5 and the ZnO denominator is unspecified', composition)
                self.assertIn('No normalization is performed.', composition)
                self.assertEqual([source['id'] for source in value['sources']],
                                 ['mtibe_2022_pbs_pbat_lignin_zno'])
                self.assertEqual(len(value['properties']), 1)
                prop = value['properties'][0]
                self.assertEqual(prop['id'], property_id)
                self.assertEqual(prop['quantity'], 'tensile_modulus')
                self.assertEqual(prop['reported_value']['number'], number)
                self.assertEqual(prop['reported_value']['unit_code'], 'MPa')
                self.assertEqual(prop['reporting_basis'], 'reported_summary')
                self.assertEqual(prop['summary_statistic'], 'reported_value')
                self.assertIsNone(prop['density_basis'])
                self.assertEqual(prop['determination_basis'], 'source_reports_measurement')
                self.assertEqual(prop['evidence_kind'], 'published_experimental_reference')
                self.assertEqual(prop['conditions']['temperature']['text'], '25 °C')
                self.assertEqual(prop['conditions']['conditioning']['text'],
                                 '48 h at 25 °C before tensile testing')
                self.assertEqual(prop['sample_count']['value'], 5)
                self.assertEqual(prop['sample_count']['relation'], 'exact')
                self.assertEqual(prop['uncertainty_status'], 'reported_plus_minus_unspecified')
                self.assertEqual(prop['uncertainty']['type'], 'reported_plus_minus_unspecified')
                self.assertEqual(prop['uncertainty']['number'], plus_minus)
                self.assertEqual(prop['uncertainty']['unit_code'], 'MPa')
                self.assertIsNone(prop['uncertainty']['coverage_factor'])
                self.assertIsNone(prop['uncertainty']['confidence_level'])
                self.assertEqual(prop['evaluation_support'], 'catalog_only')
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
