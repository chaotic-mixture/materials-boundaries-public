"""Narrow exact source-notation support, without a formula evaluator or conversion."""
from copy import deepcopy
from decimal import localcontext
import unittest

from materials_boundaries.material_references import (
    _numeric_token_matches, _scientific_token_matches, validate_material_catalog,
)
from test_material_reported_measures_contract import synthetic_reported_measures_catalog


class MaterialScientificNotationContractTests(unittest.TestCase):
    def test_admitted_caret_and_superscript_spellings_preserve_source_and_precision(self):
        pairs = (
            ('10.21 × 10^3', '10210'), ('19.23 × 10^3', '19230'),
            ('10.21 × 10³', '10210'), ('19.23 × 10³', '19230'),
            ('1.2340 × 10^2', '123.40'), ('1.2340 × 10²', '123.40'),
            ('1.2300 × 10^-2', '0.012300'), ('1.2300 × 10⁻²', '0.012300'),
            ('1.2300 × 10^0', '1.2300'), ('1.2300 × 10⁰', '1.2300'),
            ('999999999999999999999999 × 10^0', '999999999999999999999999'),
            ('0.000000000000000000000001 × 10^24', '1'),
            ('1 × 10^-24', '0.000000000000000000000001'),
            ('1 × 10²³', '100000000000000000000000'),
            ('1 × 10⁻²⁴', '0.000000000000000000000001'),
            ('0.123456789012345678901234 × 10^23', '12345678901234567890123.4'),
        )
        for text, number in pairs:
            with self.subTest(text=text):
                self.assertTrue(_numeric_token_matches(text, number))
                graph = synthetic_reported_measures_catalog('scientific_notation')
                graph[1]['records'][0]['reported_value'].update(value_text=text, number=number)
                before = deepcopy(graph)
                with localcontext() as context:
                    context.prec = 2
                    validate_material_catalog(*graph)
                self.assertEqual(graph, before)
                self.assertEqual(graph[1]['records'][0]['reported_value']['value_text'], text)

    def test_mismatched_expansion_precision_expression_injection_and_spelling_rejected(self):
        pairs = (
            ('10.21 × 10^3', '10.21'), ('19.23 × 10^3', '19231'),
            ('19.23 × 10^3', '19230.0'), ('19.23 × 10³', '19.23'),
            ('1.2340 × 10^2', '123.4'), ('1.2300 × 10^-2', '0.0123'),
            ('1e3', '1000'), ('1E3', '1000'), ('1 * 10^3', '1000'), ('1 x 10^3', '1000'),
            ('1 × 10**3', '1000'), ('1 × 10^+3', '1000'), ('1 × 10^-0', '1'),
            ('1 × 10^03', '1000'), ('1 × 10⁰³', '1000'), ('1 × 10⁻⁰', '1'),
            ('+1 × 10^3', '1000'), ('-1 × 10^3', '1000'), ('01 × 10^3', '1000'),
            ('1,2 × 10^3', '1200'), ('1. × 10^3', '1000'), ('.1 × 10^3', '100'),
            ('1×10^3', '1000'), ('1  × 10^3', '1000'), ('1 ×  10^3', '1000'),
            ('1\u00a0× 10^3', '1000'), ('1 × 10 ^3', '1000'),
            (' 1 × 10^3', '1000'), ('1 × 10^3 ', '1000'), ('1 × 10^3\n', '1000'),
            ('1 × 10^3; print(1)', '1000'), ('1 × 10^(2+1)', '1000'),
            ('1 × 10^3 + 1', '1001'), ('1 × 10^3 MPa', '1000'),
            ('NaN × 10^3', '1000'), ('Infinity × 10^3', '1000'),
            ('1 × 10^3\x1b[31m', '1000'), ('1 × 10³\ud800', '1000'),
        )
        for text, number in pairs:
            with self.subTest(text=text, number=number):
                self.assertFalse(_numeric_token_matches(text, number))
                graph = synthetic_reported_measures_catalog('scientific_notation')
                graph[1]['records'][0]['reported_value'].update(value_text=text, number=number)
                with self.assertRaises(ValueError):
                    validate_material_catalog(*graph)

    def test_mantissa_exponent_expansion_and_canonical_resource_limits(self):
        for text in ('1 × 10^999999999', '1 × 10^-999999999', '0 × 10^25',
                     '0 × 10^-25', '1 × 10^24', '1 × 10^-24',
                     '1' * 25 + ' × 10^0', '0.' + '1' * 25 + ' × 10^0',
                     '0.000000000000000000000001 × 10^-1',
                     '999999999999999999999999 × 10^1',
                     '1 × 10²⁵', '1 × 10⁻²⁵'):
            self.assertFalse(_numeric_token_matches(text, '1000'))
        for canonical in ('1e3', '+1000', 'NaN', '1' * 25, '0.' + '1' * 25):
            self.assertFalse(_scientific_token_matches('1 × 10^3', canonical))
        # Exponent is independently bounded even when its zero result would fit.
        self.assertFalse(_numeric_token_matches('0 × 10^25', '0'))
        self.assertFalse(_numeric_token_matches('0.0 × 10^-24', '0.' + '0' * 25))

    def test_unit_change_shortcuts_and_scientific_metadata_do_not_gain_units(self):
        for code, text in (('g/cm^3', 'kg m−3'), ('kg/m^3', 'g/cm³'),
                           ('kg/m^3', '10^3 kg/m³'), ('MPa', 'kg m−3'),
                           ('percent', '%')):
            graph = synthetic_reported_measures_catalog('scientific_notation')
            graph[1]['records'][0]['reported_value'].update(unit_code=code, unit_text=text)
            with self.assertRaises(ValueError):
                validate_material_catalog(*graph)
        graph = synthetic_reported_measures_catalog('cv')
        graph[1]['records'][0]['uncertainty']['measures'][0]['qualifier'] = '1 × 10^3'
        with self.assertRaises(ValueError):
            validate_material_catalog(*graph)

    def test_previous_plain_grouped_and_fractional_group_precision_rules_remain(self):
        for text, number in ((' 2.70 ', '2.70'), ('1,000.00', '1000.00'),
                             ('1.000,00', '1000.00'), ('1 000.00', '1000.00'),
                             ('1.234 567', '1.234567')):
            self.assertTrue(_numeric_token_matches(text, number))
        for text, number in (('2.700', '2.70'), ('1 00', '100'), ('1e3', '1000'),
                             ('+0', '0'), ('1.234  567', '1.234567')):
            self.assertFalse(_numeric_token_matches(text, number))
