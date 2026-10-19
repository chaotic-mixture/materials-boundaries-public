"""Selected PA2200 facts and identity limits, independent of live catalog totals."""
from hashlib import sha256
import json
from pathlib import Path
import unittest

from materials_boundaries.material_references import validate_material_catalog

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'experimental/material-batches/20261019-pa12-source-family'


def canonical_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                     allow_nan=False) + '\n'
    return sha256(raw.encode('utf-8')).hexdigest()


class PA12SourceFamilyPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((PACKET / 'packet-spec.json').read_bytes())
        cls.packet = json.loads((PACKET / 'prepared-packet.json').read_bytes())
        cls.fact = json.loads((ROOT / 'tests/fixtures/pa12_pa2200_source_transcription_20261019.json').read_bytes())
        cls.graph = cls.packet['catalogs']
        cls.identity, = cls.graph['materials']['identities']
        cls.grade, = cls.graph['materials']['grades']
        cls.state, = cls.graph['materials']['records']
        cls.prop, = cls.graph['properties']['records']
        cls.source, = cls.graph['sources']['records']

    def test_compiler_packet_preserves_explicit_input_and_zero_admission(self):
        self.assertEqual(self.packet['schema'], 'formulation-prepared-packet/1')
        self.assertEqual(self.packet['input'], self.spec)
        self.assertEqual(self.packet['spec_sha256'], canonical_hash(self.spec))
        self.assertEqual(self.packet['review'], self.spec['review'])
        self.assertEqual(self.packet['report']['formal_admitted_delta'], 0)
        self.assertEqual(self.packet['review']['formal_admitted_delta'], 0)
        self.assertEqual(self.packet['report']['delta'], {
            'identities': 1, 'grades': 1, 'states': 1, 'properties': 1, 'sources': 1,
            'categories': {'metal': 0, 'inorganic': 0, 'polymer': 1, 'composite': 0, 'natural': 0}})
        validate_material_catalog(self.graph['materials'], self.graph['properties'], self.graph['sources'])

    def test_one_pa12_representative_and_source_designated_grade(self):
        self.assertEqual(self.identity['id'], self.fact['identity_id'])
        self.assertEqual(self.identity['category'], 'polymer')
        self.assertEqual(self.grade['id'], self.fact['grade_id'])
        self.assertEqual(self.grade['identity_id'], self.identity['id'])
        self.assertEqual(self.grade['designation'], 'PA2200')
        self.assertEqual(self.grade['authority']['kind'], 'source_designation')
        self.assertEqual(self.grade['manufacturer']['text'], 'EOS')
        self.assertEqual(self.state['grade_id'], self.grade['id'])
        crosswalk, = self.spec['identity_crosswalk']
        self.assertEqual(crosswalk['identity_id'], self.identity['id'])
        self.assertEqual(crosswalk['source_designations'], [self.state['source_designation']])
        self.assertIn('different manufacturer labels alone', self.identity['identity_scope'])
        self.assertIn('HP PA12 and all other PA12 products remain outside', self.identity['identity_scope'])

    def test_table7_strength_statistics_and_count_match_fixture(self):
        self.assertEqual(self.prop['id'], self.fact['property_id'])
        self.assertEqual(self.prop['material_state_id'], self.fact['state_id'])
        self.assertEqual(self.prop['quantity'], self.fact['quantity'])
        self.assertEqual(self.prop['source_property_label'], self.fact['source_property_label'])
        self.assertEqual(self.prop['reported_value']['number'], self.fact['mean'])
        self.assertEqual(self.prop['reported_value']['unit_code'], self.fact['unit'])
        self.assertEqual(self.prop['summary_statistic'], 'reported_mean')
        self.assertEqual(self.prop['uncertainty']['type'], 'reported_standard_deviation')
        self.assertEqual(self.prop['uncertainty']['number'], self.fact['standard_deviation'])
        self.assertEqual(self.prop['uncertainty']['unit_code'], 'MPa')
        self.assertEqual(self.prop['sample_count']['value'], self.fact['sample_count'])
        self.assertEqual(self.prop['sample_count']['relation'], 'exact')
        self.assertIn('CV ' + self.fact['coefficient_of_variation_percent'] + '%', self.prop['uncertainty_note'])
        self.assertTrue(any(self.fact['source_table_id'] in e['locator']
                            and 'reported_value' in e['supports'] for e in self.prop['evidence']))

    def test_selected_state_and_method_preserve_unknown_conditions(self):
        self.assertEqual(self.state['id'], self.fact['state_id'])
        processing = self.state['state']['processing']['text']
        self.assertIn(self.fact['post_processing_label'], processing)
        self.assertIn(self.fact['dye'], processing)
        self.assertIn('EOS P396', processing)
        self.assertIn('before accelerated ageing', self.state['state']['conditioning']['text'])
        self.assertIn('Horizontal XY', self.state['state']['orientation']['text'])
        conditions = self.prop['conditions']
        self.assertEqual(conditions['temperature']['status'], 'not_reported_in_inspected_source')
        humidity, = conditions['additional_conditions']
        self.assertEqual(humidity['name'], 'test_relative_humidity')
        self.assertEqual(humidity['fact']['status'], 'not_reported_in_inspected_source')
        self.assertIn(self.fact['test_standard'], conditions['test_standard']['text'])
        self.assertIn(self.fact['test_speed'], conditions['loading_rate']['text'])
        definition = self.prop['method_definition']['definition']
        self.assertIn(self.fact['machine'], definition)
        self.assertIn('test section length of 115 mm', definition)
        self.assertIn('not relabeled as a verified extensometer gauge length', definition)
        self.assertIsNone(self.prop['method_definition']['extraction_window'])
        self.assertIn('additive package', self.state['state']['composition_or_purity']['notes'])

    def test_disputed_modulus_and_other_materials_remain_excluded(self):
        conflict = self.fact['excluded_modulus']
        discrepancy = self.prop['source_discrepancies'][0]
        for value in (conflict['mean_GPa'], conflict['standard_deviation_GPa'],
                      conflict['coefficient_of_variation_percent']):
            self.assertIn(value, discrepancy['description'])
        self.assertIn('exclude the modulus', discrepancy['disposition'])
        self.assertIn('E (GPa) Mean/Std/CV', discrepancy['evidence'][0]['locator'])
        self.assertEqual([p['quantity'] for p in self.graph['properties']['records']], ['tensile_strength'])
        self.assertFalse(self.prop['universal_bound'])
        self.assertFalse(self.prop['engineering_allowable'])
        self.assertFalse(self.prop['verification']['independent_scientific_review'])
        self.assertFalse(self.prop['verification']['raw_data_reanalysis'])
        self.assertIn('medical suitability/certification claim', self.prop['scope_note'])
        self.assertIn('Manufacturer-derived Tables 1 and 2', self.packet['review']['excluded'])

    def test_article_attribution_rights_and_asset_boundary(self):
        self.assertEqual(self.source['id'], self.fact['source_id'])
        self.assertEqual(self.source['authors'], self.fact['authors'])
        self.assertEqual(self.source['doi'], self.fact['doi'])
        self.assertEqual(self.source['license']['identifier'], self.fact['license'])
        self.assertEqual(self.prop['source_document']['sha256'], self.fact['retained_xml_sha256'])
        self.assertEqual(self.spec['source_records'][0]['sha256'], canonical_hash(self.source))
        self.assertFalse(self.packet['review']['rights']['assets_included'])
        self.assertFalse(self.packet['review']['rights']['third_party_comparison_content_included'])
        self.assertEqual(self.packet['review']['source_access']['fresh_requests'], 0)
        self.assertFalse(self.packet['review']['source_access']['pdf_visual_inspection'])
        self.assertFalse(any(p.suffix.lower() in {'.xml', '.pdf', '.png', '.jpg'}
                             for p in PACKET.rglob('*') if p.is_file()))


if __name__ == '__main__':
    unittest.main()
