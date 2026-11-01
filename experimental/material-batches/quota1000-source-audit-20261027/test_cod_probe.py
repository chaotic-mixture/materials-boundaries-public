import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import audit_cod_probe as audit


class CodProbeTests(unittest.TestCase):
    def test_coefficient_scaled_and_decimal_formulas_group_without_float(self):
        base = audit.formula_ratio_key('- Ca O3 Ti -')
        self.assertEqual(base, audit.formula_ratio_key('- Ti2 O6 Ca2 -'))
        self.assertEqual(base, audit.formula_ratio_key('- Ca0.5 O1.5 Ti0.5 -'))

    def test_distinct_stoichiometry_not_collapsed(self):
        self.assertNotEqual(audit.formula_ratio_key('- Fe O -'),
                            audit.formula_ratio_key('- Fe2 O3 -'))

    def test_invalid_or_ambiguous_formula_rejected(self):
        for formula in ('', '- -', 'Fe0 O', 'Fe2 Fe3 O4', 'Fe(OH)2', 'Fe? O'):
            with self.subTest(formula=formula), self.assertRaises(ValueError):
                audit.formula_ratio_key(formula)

    def test_changed_metadata_and_archive_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'metadata checksum mismatch'):
            audit.inspect(b'changed', b'changed')
        metadata = b'[]'
        with patch.object(audit, 'METADATA_SHA256', hashlib.sha256(metadata).hexdigest()):
            with self.assertRaisesRegex(ValueError, 'archive checksum mismatch'):
                audit.inspect(metadata, b'changed')

    def test_frozen_probe_is_not_identity_or_density_approval(self):
        d = json.loads(Path(__file__).with_name('cod-source-probe.json').read_text(encoding='utf8'))
        self.assertEqual(d['metadata_records'], 3902)
        self.assertEqual(d['exact_rational_formula_ratio_groups'], 2788)
        self.assertEqual(d['probe_cif_files'], 50)
        self.assertEqual(d['probe_files_with_density_tag_lines'], 8)
        self.assertIsNone(d['canonical_material_identity_count'])
        self.assertEqual(d['revision_mismatches'], [])
        self.assertEqual(d['admitted_increment'], 0)


if __name__ == '__main__':
    unittest.main()
