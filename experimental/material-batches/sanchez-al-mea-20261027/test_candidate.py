"""Scientific scope checks for the held primary-source candidate."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from build_candidate import build, validate_material_catalog


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads(Path(__file__).with_name('candidate.json').read_text(encoding='utf-8'))

    def test_full_candidate_graph_validates_without_granting_admission(self):
        c = self.packet['catalogs']
        validate_material_catalog(c['materials'], c['properties'], c['sources'])
        self.assertEqual(self.packet['admitted_increment'], 0)
        self.assertEqual(self.packet['status'], 'held_pending_independent_review')

    def test_original_compositions_replace_three_bad_compilation_labels(self):
        rows = self.packet['primary_facts']
        self.assertEqual({r['suffix'] for r in rows if r['mpea_formula_mismatch']}, {'cr', 'mn', 'zr'})
        for row in rows:
            if row['suffix'] in {'cr', 'mn', 'zr'}:
                self.assertIn('Al70', row['nominal_composition_at_percent_label'])
                self.assertIn('Si10', row['nominal_composition_at_percent_label'])
                self.assertEqual(row['original_nominal_ratios_relative_to_Al_rounded_3dp']['Si'], '0.143')
                self.assertIn('Si0.231', row['mpea_formula_literal'])

    def test_compression_count_and_rate_do_not_leak_to_density(self):
        for p in self.packet['catalogs']['properties']['records']:
            if p['quantity'] == 'mass_density':
                self.assertIsNone(p['sample_count']['value'])
                self.assertEqual(p['conditions']['loading_rate']['status'], 'not_applicable')
            else:
                self.assertEqual(p['sample_count']['relation'], 'at_least')
                self.assertEqual(p['sample_count']['value'], 5)
                self.assertIn('0.001', p['conditions']['loading_rate']['text'])
                self.assertIn('Compression', p['method_definition']['definition'])

    def test_ambiguous_plus_minus_is_not_fabricated_sd(self):
        for p in self.packet['catalogs']['properties']['records']:
            self.assertIsNone(p['uncertainty'])
            self.assertEqual(p['summary_statistic'], 'not_stated')
            if p['quantity'] == 'youngs_modulus':
                self.assertIn('±', p['uncertainty_note'])
                self.assertIn('unresolved', p['uncertainty_note'])

    def test_rt_not_replaced_by_compilation_numeric_temperature(self):
        for p in self.packet['catalogs']['properties']['records']:
            self.assertIn('RT', p['conditions']['temperature']['text'])
            self.assertNotIn('25', p['conditions']['temperature']['text'])
            self.assertFalse(p['verification']['independent_scientific_review'])
            self.assertFalse(p['verification']['raw_data_reanalysis'])

    def test_changed_primary_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'primary XML checksum mismatch'):
            build(b'changed', b'changed')

    def test_unknown_evidence_source_rejected(self):
        c = deepcopy(self.packet['catalogs'])
        c['properties']['records'][0]['evidence'][0]['source_id'] = 'unknown_source'
        with self.assertRaises(ValueError):
            validate_material_catalog(c['materials'], c['properties'], c['sources'])


if __name__ == '__main__':
    unittest.main()
