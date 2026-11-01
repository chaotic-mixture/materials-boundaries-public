"""Guard aggregate semantics, upstream-byte pins and computational separation."""
from pathlib import Path
import json
import unittest

import audit_polymer_lineage as audit


class PolymerLineageTests(unittest.TestCase):
    def test_exact_decimal_even_median(self):
        r = audit.aggregate_median('[0.1, 0.2]', '2', '0.15')
        self.assertTrue(r['median_matches'])
        self.assertEqual(r['calculated_median_kelvin'], '0.15')

    def test_count_and_median_mismatches_are_visible(self):
        r = audit.aggregate_median('[300, 310, 400]', '2', '350')
        self.assertFalse(r['count_matches'])
        self.assertFalse(r['median_matches'])

    def test_nonfinite_boolean_and_nonpositive_values_rejected(self):
        for raw in ('[NaN]', '[Infinity]', '[true]', '[0]', '[-3]', '[]', '{}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                audit.aggregate_median(raw, '1', '300')

    def test_source_mutation_rejected_before_parsing(self):
        for profile in audit.PINS:
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                audit.read_rows(b'changed data', profile)

    def test_grea_hold_does_not_clear_other_sources(self):
        rows = [{'meta.tg_values': '', 'meta.source': label, 'meta.reliability': 'black'}
                for label in ['GREA', 'GREA', 'Xie']]
        result = audit.audit_tg(rows)
        self.assertEqual(result['grea_labelled_rows_held_for_upstream_notice'], 2)
        self.assertEqual(result['other_source_label_rows_not_cleared'], 1)
        self.assertEqual(result['admitted_increment'], 0)

    def test_computational_out_of_range_density_is_flagged(self):
        row = dict.fromkeys(('monomer_ID', 'smiles', 'temp', 'press', 'density',
                             'density_min', 'density_max', 'density_std', 'density_count',
                             'tacticity', 'DP', 'n_mol'), '')
        row.update(monomer_ID='synthetic', smiles='*CC*', temp='300', press='1',
                   density='2', density_min='1', density_max='1.5', density_count='5')
        result = audit.audit_radonpy([row])
        self.assertEqual(len(result['density_numeric_consistency_issues']), 1)
        self.assertEqual(result['experimental_rows_selected'], 0)
        self.assertIsNone(result['canonical_polymer_identity_count'])

    def test_frozen_audit_counts_remain_unadmitted(self):
        result = json.loads(Path(__file__).with_name('polymer-lineage-audit.json').read_text(encoding='utf8'))
        self.assertEqual(result['tg']['rows'], 7367)
        self.assertEqual(result['tg']['rows_with_explicit_contributing_values'], 279)
        self.assertEqual(result['tg']['exact_decimal_median_mismatches'], [])
        self.assertEqual(result['radonpy']['rows'], 1077)
        self.assertEqual(result['radonpy']['evidence_kind'], 'published_computational_reference')
        self.assertEqual(result['radonpy']['admitted_increment'], 0)


if __name__ == '__main__':
    unittest.main()
