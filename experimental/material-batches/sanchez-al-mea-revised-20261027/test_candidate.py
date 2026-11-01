"""Scientific scope checks for the held primary-source candidate."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from build_candidate import build, validate_material_catalog
from materials_boundaries.material_references import _numeric_token_matches


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

    def test_sd_definition_and_literal_integers_are_preserved(self):
        expected = {'fe': ('04', '4'), 'ni': ('17', '17'), 'cr': ('03', '3'), 'mn': ('02', '2'), 'zr': ('27', '27')}
        for p in self.packet['catalogs']['properties']['records']:
            self.assertEqual(p['summary_statistic'], 'not_stated')
            if p['quantity'] == 'youngs_modulus':
                suffix = next(k for k in expected if '_'+k+'_' in p['id'])
                self.assertEqual(p['uncertainty']['type'], 'reported_measures')
                sd = p['uncertainty']['measures'][0]
                self.assertEqual(sd['kind'], 'standard_deviation')
                value = sd['reported_value']
                self.assertEqual((value['value_text'], value['number']), expected[suffix])
                self.assertEqual(value['unit_code'], 'GPa')
            else:
                self.assertIsNone(p['uncertainty'])

    def test_as_cast_and_qualitative_porosity_are_retained(self):
        for state in self.packet['catalogs']['materials']['records']:
            facts = state['state']
            self.assertEqual(facts['temper_or_heat_treatment']['status'], 'reported')
            self.assertIn('as-cast', facts['temper_or_heat_treatment']['text'])
            if '_ni_' in state['id']:
                self.assertEqual(facts['porosity']['status'], 'not_reported_in_inspected_source')
            elif '_cr_' in state['id']:
                self.assertEqual(facts['porosity']['status'], 'reported')
                self.assertIn('Figure 2(e)', facts['porosity']['text'])
                self.assertIn('not a measurement of globally zero', facts['porosity']['notes'])
            else:
                self.assertEqual(facts['porosity']['status'], 'reported')
                self.assertIn('Shrinkage porosity', facts['porosity']['text'])

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

    def test_leading_zero_integer_never_becomes_fractional_sd(self):
        for source, canonical in [('04', '4'), ('03', '3'), ('02', '2'), ('000', '0')]:
            self.assertTrue(_numeric_token_matches(source, canonical))
        for source, canonical in [('04', '0.4'), ('04', '4.0'), ('004.0', '4.0'),
                                  ('04 2', '42'), ('04x', '4'), ('0' * 97, '0')]:
            self.assertFalse(_numeric_token_matches(source, canonical), (source, canonical))
        c = deepcopy(self.packet['catalogs'])
        sd = c['properties']['records'][1]['uncertainty']['measures'][0]
        sd['reported_value']['number'] = '0.4'
        with self.assertRaisesRegex(ValueError, 'source text'):
            validate_material_catalog(c['materials'], c['properties'], c['sources'])


if __name__ == '__main__':
    unittest.main()
