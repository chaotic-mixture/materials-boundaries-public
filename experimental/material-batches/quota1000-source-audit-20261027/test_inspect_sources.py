"""Checks inventory trust boundaries using synthetic rows, never quota evidence."""
import csv
import hashlib
import io
import unittest
from unittest.mock import patch

import inspect_sources as audit


class InventoryTests(unittest.TestCase):
    def source(self, rows, fields=audit.POLY_FIELDS):
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)
        return stream.getvalue().encode('utf-8')

    def inspect_fixture(self, data):
        pin = ('sha256', hashlib.sha256(data).hexdigest(), len(data))
        with patch.dict(audit.PINS, {'polymetrix': pin}):
            return audit.inspect(data, 'polymetrix')

    def test_changed_source_rejected_before_parse(self):
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            audit.inspect(b'changed or partial source', 'polymetrix')

    def test_duplicate_identity_does_not_inflate_count_or_admit(self):
        row = dict.fromkeys(audit.POLY_FIELDS, '')
        row.update(PSMILES='[*]CC[*]', **{'labels.Exp_Tg(K)': '300',
                                       'meta.std': '0.0', 'meta.num_of_points': '1'})
        summary, records = self.inspect_fixture(self.source([row, row]))
        self.assertEqual(summary['literal_identity_strings'], 1)
        self.assertEqual(summary['repeated_literal_identity_rows'], 1)
        self.assertEqual(summary['admitted_increment'], 0)
        self.assertIsNone(summary['canonical_identity_count'])
        self.assertEqual(records[0]['source_fields']['meta.std'], '0.0')
        self.assertTrue(all(r['status'] == 'held' for r in records))

    def test_missing_fields_rejected(self):
        with self.assertRaisesRegex(ValueError, 'required source fields'):
            self.inspect_fixture(self.source([], ['PSMILES']))

    def test_malformed_row_rejected(self):
        data = self.source([]) + b'one,two\n'
        with self.assertRaisesRegex(ValueError, 'malformed CSV'):
            self.inspect_fixture(data)

    def test_nonfinite_not_accepted_as_positive_numeric_value(self):
        for value in ('NaN', 'Infinity', '-Infinity', '', '-1', '0'):
            self.assertFalse(audit.positive_number(value), value)
        self.assertTrue(audit.positive_number('0.001'))

    def test_experimental_and_calculated_columns_preserved_separately(self):
        fields = ['FORMULA', 'REFERENCE: doi', 'PROPERTY: Exp. Density (g/cm$^3$)',
                  'PROPERTY: Calculated Density (g/cm$^3$)',
                  'PROPERTY: Exp. Young modulus (GPa)',
                  'PROPERTY: Calculated Young modulus (GPa)']
        row = dict.fromkeys(fields, '')
        row.update(FORMULA='Al1 Co1', **{fields[3]: '7.9'})
        data = self.source([row], fields)
        pin = ('sha256', hashlib.sha256(data).hexdigest(), len(data))
        with patch.dict(audit.PINS, {'mpea': pin}):
            summary, records = audit.inspect(data, 'mpea')
        self.assertEqual(records[0]['source_fields'][fields[2]], '')
        self.assertEqual(records[0]['source_fields'][fields[3]], '7.9')
        self.assertEqual(summary['admitted_increment'], 0)


if __name__ == '__main__':
    unittest.main()
