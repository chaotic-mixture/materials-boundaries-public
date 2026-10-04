"""Independent A01--A30 acceptance corpus for the offline composite workflow.

Expected numbers below come from original rational examples, not copied engine
outputs. This suite tests software scope/preservation, never scientific review.
Browser keyboard and narrow-viewport visual QA remain a separate release gate;
static HTML checks here must not be described as completed browser testing.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Inexact, localcontext
from fractions import Fraction
import hashlib
import io
from html.parser import HTMLParser
import json
import os
from pathlib import Path
from source_evidence_preservation import previous_record
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from materials_boundaries import ValidationError, evaluate, load_json
from materials_boundaries.catalog import read_catalog
from materials_boundaries.composite import (
    CompositeReplayError, build_composite_report, validate_composite_report,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/composite-acceptance.json').read_text())
LANGUAGES = ('en', 'zh', 'ja', 'de')
IDS = (
    'hs_bulk_3d_two_phase', 'reuss_bulk', 'voigt_bulk',
    'hs_shear_3d_two_phase', 'reuss_shear', 'voigt_shear',
    'youngs_modulus_outer', 'poissons_ratio_outer',
)
CONDITIONS = {
    'dimension': 3, 'constituent_symmetry': 'isotropic',
    'effective_symmetry': 'isotropic', 'kinematics': 'small_strain',
    'constitutive_law': 'linear_elastic', 'loading': 'static',
    'interface': 'perfectly_bonded',
}
STATUS = {
    'S': ('satisfied', 'computed'), 'U': ('unknown', 'not_computed'),
    'V': ('violated', 'not_computed'), 'N': ('satisfied', 'numerical_range_error'),
}
ARTIFACTS = {'input.json', 'evaluation.json', 'bundle.json', 'report.txt', 'report.html', 'manifest.json'}


def case():
    return deepcopy(FIXTURE['input'])


def rows(bundle):
    return bundle['evaluation']['evaluations']


def by_id(bundle):
    return {row['claim_id']: row for row in rows(bundle)}


def set_pair(instance, k, g, unit='GPa'):
    for phase in instance['phases']:
        phase['bulk_modulus'] = {'value': k, 'unit': unit}
        phase['shear_modulus'] = {'value': g, 'unit': unit}
    return instance


def model_case():
    """A fictitious model-evidence contract, intentionally not real literature."""
    data = case()
    source_id = 'original_unresolved_contract_fixture'
    data['id'] = 'original-hypothetical-model-contract'
    for phase, k, g in zip(data['phases'], (14, 56), (8.4, 33.6)):
        phase['bulk_modulus']['value'] = k
        phase['shear_modulus']['value'] = g
    data['provenance'] = {
        'kind': 'literature_model', 'source_ids': [source_id],
        'note': 'Fictitious contract test. No publication or measured material is represented.',
        'model_evidence': {
            'source_id': source_id,
            'locator': 'Original hypothetical contract-test input; no real source location.',
            'parameter_basis': 'literature_model_inputs',
            'raw_parameters': [
                {'phase_id': p['id'], 'youngs_modulus': {'value': e, 'unit': 'GPa'}, 'poissons_ratio': .25}
                for p, e in zip(data['phases'], (21, 84))
            ],
            'conversion_rule_id': 'isotropic_young_poisson_to_bulk_shear_v1',
            'condition_basis': {key: 'source_model' if key in ('constituent_symmetry', 'constitutive_law')
                                else 'calculator_assumption' for key in CONDITIONS},
            'fraction_basis': 'calculator_choice', 'temperature_k': None,
            'material_grade': None, 'cure_state': None, 'measurement_uncertainty': None,
            'scope_note': 'Original synthetic values exercise the import contract only.',
        },
    }
    return data


def cli(*args):
    return subprocess.run([sys.executable, '-m', 'materials_boundaries', 'composite', *map(str, args)],
                          cwd=ROOT, text=True, capture_output=True, timeout=30)


class StaticReportParser(HTMLParser):
    """Inspect inert HTML without treating a closed disclosure as visible prose.

    ``content`` is all body text, including raw records in disclosures.
    ``visible_content`` excludes every details subtree, including its summary;
    essential scientific caveats must be ordinary visible report content.
    This static structure check is not browser accessibility/layout testing.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.links = []
        self.content = []
        self.visible_content = []
        self.attrs = []
        self.details = []
        self.result_rows = []
        self.sections = []
        self.audit_records = []
        self._section = None
        self._heading = None
        self._audit_pre = None
        self._in_body = False
        self._details_stack = []
        self._summary_depth = 0
        self._article = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        self.attrs.append((tag, attrs))
        if 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'body':
            self._in_body = True
        elif self._in_body and tag == 'details':
            self.details.append({'attrs': attrs, 'summary': [], 'content': []})
            self._details_stack.append(len(self.details) - 1)
        elif self._in_body and tag == 'summary' and self._details_stack:
            self._summary_depth += 1
        elif self._in_body and tag == 'article' and not self._details_stack:
            self._article = []
        elif self._in_body and tag in ('h1', 'h2', 'h3', 'h4') and not self._details_stack:
            self._section = {'heading': [], 'content': []}
            self.sections.append(self._section)
            self._heading = tag
        elif self._in_body and tag == 'pre' and self._details_stack:
            self._audit_pre = []

    def handle_endtag(self, tag):
        if tag == 'body':
            self._in_body = False
        elif tag == 'details' and self._details_stack:
            self._details_stack.pop()
        elif tag == 'summary' and self._summary_depth:
            self._summary_depth -= 1
        elif tag == 'article' and self._article is not None:
            self.result_rows.append('\n'.join(self._article))
            self._article = None
        elif tag == self._heading:
            self._heading = None
        elif tag == 'pre' and self._audit_pre is not None:
            self.audit_records.append(''.join(self._audit_pre))
            self._audit_pre = None

    def handle_data(self, data):
        if not self._in_body:
            return
        self.content.append(data)
        if self._details_stack:
            detail = self.details[self._details_stack[-1]]
            detail['content'].append(data)
            if self._audit_pre is not None:
                self._audit_pre.append(data)
            if self._summary_depth:
                detail['summary'].append(data)
        else:
            self.visible_content.append(data)
            if self._section is not None:
                self._section['content'].append(data)
                if self._heading is not None:
                    self._section['heading'].append(data)
            if self._article is not None:
                self._article.append(data)


class CompositeAcceptanceTests(unittest.TestCase):
    maxDiff = 2000

    def assert_report(self, data, status='SSSSSSSS', unit='GPa', *, render=True):
        before = deepcopy(data)
        bundle = build_composite_report(data, output_unit=unit)
        self.assertEqual(data, before, 'builder changed caller input')
        self.assertEqual(bundle['input'], before)
        self.assertEqual(bundle['evaluation'], evaluate(before, output_unit=unit),
                         'wrapper changed the existing evaluation contract')
        self.assertEqual(tuple(r['claim_id'] for r in rows(bundle)), IDS)
        self.assertEqual([(r['applicability'], r['computation']) for r in rows(bundle)],
                         [STATUS[s] for s in status])
        for row, expected in zip(rows(bundle), status):
            self.assertEqual(row['result'] is None, expected != 'S')
            self.assertEqual(row['error'] is not None, expected == 'N')
        self.assertFalse(bundle['policy']['independent_scientific_review'])
        self.assertEqual(bundle['policy']['joint_attainability'], 'not_asserted')
        validate_composite_report(bundle)
        self.assertEqual(bundle['input'], before)
        if render:
            self.assert_renders(bundle)
        return bundle

    def assert_renders(self, bundle):
        from materials_boundaries.composite_render import render_composite_report
        snapshot = deepcopy(bundle)
        for lang in LANGUAGES:
            with self.subTest(lang=lang, case=bundle['instance_id']):
                text = render_composite_report(bundle, lang=lang, format='text')
                document = render_composite_report(bundle, lang=lang, format='html')
                self.assertEqual(bundle, snapshot, 'render changed canonical language-independent core')
                parser = StaticReportParser()
                parser.feed(document)
                visible = '\n'.join(parser.visible_content)
                complete_body = '\n'.join(parser.content)
                self.assertIn(bundle['instance_id'], text)
                self.assertIn(bundle['instance_id'], visible)
                self.assertIn(f'lang="{lang}"', document)
                self.assertEqual(parser.tags.count('h1'), 1)
                self.assertEqual(parser.tags.count('main'), 1)
                self.assertEqual(parser.tags.count('article'), 8)
                self.assertEqual(len(parser.result_rows), 8)
                self.assertTrue(parser.details, 'raw audit records need closed disclosures')
                self.assertEqual(len(parser.audit_records), 1)
                self.assertEqual(json.loads(parser.audit_records[0]), bundle, 'audit disclosure lost canonical data')
                for detail in parser.details:
                    self.assertNotIn('open', detail['attrs'], 'raw audit details opened by default')
                    self.assertTrue(''.join(detail['summary']).strip(), 'disclosure needs a visible summary')
                for row, visible_row in zip(rows(bundle), parser.result_rows):
                    for token in (row['claim_id'], row['applicability'], row['computation']):
                        self.assertIn(token, visible_row)
                    if row['result']:
                        for side in ('lower', 'upper'):
                            if side in row['result']:
                                self.assertIn(side + ' ≈ ' + repr(row['result'][side]), visible_row)
                        self.assertIn(row['result']['unit'], visible_row)
                self.assertIn('width=device-width', document)
                self.assertIn('overflow-wrap:anywhere', document)
                self.assertIn('@media(max-width:', document)
                for row in rows(bundle):
                    for output in (text, visible):
                        self.assertIn(row['claim_id'], output)
                        self.assertIn(row['rule_id'], output)
                        self.assertIn(row['applicability'], output)
                        self.assertIn(row['computation'], output)
                    if row['result']:
                        for side in ('lower', 'upper'):
                            if side in row['result']:
                                for output in (text, visible):
                                    self.assertIn(repr(row['result'][side]), output)
                        self.assertIn(row['result']['unit'], text)
                        self.assertIn(row['result']['unit'], visible)
                    if 'dependencies' in row:
                        for output in (text, visible):
                            self.assertIn(row['dependencies']['joint_attainability'], output)
                            for identifier in row['dependencies']['claim_ids']:
                                self.assertIn(identifier, output)
                from materials_boundaries._composite_labels import label
                for key in ('scope_notice', 'source_notice', 'numerical_notice', 'joint_notice',
                            'unknown_notice', 'review_state', 'translation_notice', 'comparison_notice',
                            'rights_notice', 'replay_notice', 'hash_notice'):
                    for output in (text, visible):
                        self.assertIn(label(key, lang), output, 'essential warning hidden in audit details')
                for key in ('structure', 'applicability', 'availability', 'review'):
                    self.assertIn(label(key, lang), text)
                    self.assertIn(label(key, lang), visible)
                gaps = {gap for claim in bundle['catalogs']['claims']['records']
                        for gap in claim['verification']['gaps']}
                for gap in gaps:
                    self.assertEqual(text.count(gap), 1, 'show each original evidence gap once')
                    self.assertEqual(visible.count(gap), 1, 'evidence gap hidden or repeated in visible report')
                for source in bundle['catalogs']['sources']['records']:
                    heading = source['id'] + ' · ' + source['title']
                    sections = [section for section in parser.sections if ''.join(section['heading']) == heading]
                    self.assertEqual(len(sections), 1, 'one visible, source-specific evidence section')
                    source_html = '\n'.join(sections[0]['content'])
                    source_start = text.index(heading)
                    other_headers = [other['id'] + ' · ' + other['title']
                                     for other in bundle['catalogs']['sources']['records'] if other != source]
                    ends = [text.index(other) for other in other_headers if text.index(other) > source_start]
                    ends.append(text.index(label('review_gaps', lang), source_start))
                    source_text = text[source_start:min(ends)]
                    evidence_entries = [entry for claim in bundle['catalogs']['claims']['records']
                                        for entry in claim['evidence'] if entry['source_id'] == source['id']]
                    for evidence in evidence_entries:
                        locator = 'locator=' + ('null' if evidence['locator'] is None else evidence['locator'])
                        for source_section in (source_text, source_html):
                            self.assertIn(locator, source_section, 'source locator moved, fabricated or hidden')
                            self.assertIn(evidence['verification_status'], source_section)
                            self.assertIn(evidence['verified_as'], source_section)
                if 'note' in bundle['input']['provenance']:
                    self.assertIn(bundle['input']['provenance']['note'], text)
                    self.assertIn(bundle['input']['provenance']['note'], complete_body)
                for source in bundle['catalogs']['sources']['records']:
                    self.assertIn(source['title'], text)
                    self.assertIn(source['title'], visible)
                for source_id in bundle['catalogs']['unresolved_source_ids']:
                    self.assertIn(source_id, text)
                    self.assertIn(source_id, visible)
                self.assertFalse({'script', 'iframe', 'object', 'embed', 'form', 'img', 'link'} & set(parser.tags))
                self.assertFalse(any(name.lower().startswith('on') for _, a in parser.attrs for name in a))
                self.assertNotRegex(document.lower(), r'@import|url\s*\(')
                self.assertTrue(all(url.startswith(('https://', 'http://')) or url.startswith('#') for url in parser.links))
        return bundle

    def test_A01_original_rational_answer_and_single_evaluation(self):
        data = case()
        with patch('materials_boundaries.composite.evaluate', wraps=evaluate) as run:
            bundle = build_composite_report(data)
            self.assertEqual(run.call_count, 1)
        for row in rows(bundle):
            self.assertEqual(set(row['result']) - {'unit'}, set(FIXTURE['exact_endpoints'][row['claim_id']]))
            for side, rational in FIXTURE['exact_endpoints'][row['claim_id']].items():
                self.assertEqual(row['result'][side], float(Fraction(rational)))
        self.assert_report(data)
        from materials_boundaries.composite_render import render_composite_report
        text = render_composite_report(bundle)
        self.assertIn('conditional', text.lower())
        self.assertIn('approximate', text.lower())
        self.assertIn('software replay only; does not verify the physical sample or prove a theorem', text)

    def test_A01_standard_demo_is_compact_without_dropping_result_rows(self):
        from materials_boundaries.composite_render import render_composite_report
        bundle = build_composite_report(case())
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                text = render_composite_report(bundle, lang=lang, format='text')
                # This ceiling applies only to the ordinary demo. Arbitrary
                # user notes and imported evidence must never be truncated to
                # fit it; hostile/long inputs are checked separately below.
                self.assertLessEqual(len(text.splitlines()), 180)
                self.assertLessEqual(len(text), 18000)
                for identifier in IDS:
                    matching = [line for line in text.splitlines() if '[' + identifier + ']' in line]
                    self.assertEqual(len(matching), 1, 'one readable result row per canonical claim')
                self.assertNotIn('required_assumptions.', text)
                self.assertNotIn('verification.gaps.[', text)
                self.assertIn(bundle['input']['provenance']['note'], text)

    def test_A02_pair_reversal_mixed_units_and_output_scale(self):
        reference = self.assert_report(case())
        reverse = case(); reverse['phases'].reverse()
        mixed = case()
        mixed['phases'][0]['bulk_modulus'] = {'value': 12000, 'unit': 'MPa'}
        mixed['phases'][1]['shear_modulus'] = {'value': 18000000000, 'unit': 'Pa'}
        for instance in (reverse, mixed):
            result = self.assert_report(instance)
            self.assertEqual([r['result'] for r in rows(result)], [r['result'] for r in rows(reference)])
        mpa = self.assert_report(mixed, unit='MPa')
        for old, new in zip(rows(reference), rows(mpa)):
            for side in ('lower', 'upper'):
                if side in old['result']:
                    factor = 1 if old['quantity'] == 'effective_poissons_ratio' else 1000
                    self.assertAlmostEqual(new['result'][side], old['result'][side] * factor, places=9)
        self.assertEqual(rows(mpa)[-1]['result']['unit'], '1')

    def test_A03_equal_bulk_does_not_collapse_other_quantities(self):
        data = case(); data['phases'][1]['bulk_modulus']['value'] = 12
        result = self.assert_report(data)
        for row in rows(result)[:3]:
            self.assertTrue(all(v == 12 for k, v in row['result'].items() if k != 'unit'))
        for index in (3, 6, 7):
            self.assertLess(rows(result)[index]['result']['lower'], rows(result)[index]['result']['upper'])

    def test_A04_equal_shear_conditional_collapse(self):
        data = case(); data['phases'][1]['shear_modulus']['value'] = 6
        result = self.assert_report(data)
        self.assertEqual(rows(result)[0]['result'], {'lower': float(Fraction(336, 13)), 'upper': float(Fraction(336, 13)), 'unit': 'GPa'})
        self.assertEqual(rows(result)[1]['result']['lower'], 24)
        self.assertEqual(rows(result)[2]['result']['upper'], 30)
        for index in (3, 6, 7):
            r = rows(result)[index]['result']; self.assertEqual(r['lower'], r['upper'])
        self.assertEqual(rows(result)[3]['result']['lower'], 6)

    def test_A05_identical_parameters_keep_two_phase_records(self):
        for f in (0, .125, .25, .9, 1):
            data = set_pair(case(), 12, 6)
            data['phases'][0]['volume_fraction'] = f
            data['phases'][1]['volume_fraction'] = 1 - f
            result = self.assert_report(data)
            for row in rows(result):
                expected = {**dict.fromkeys(IDS[:3], 12), **dict.fromkeys(IDS[3:6], 6),
                            IDS[6]: float(Fraction(108, 7)), IDS[7]: float(Fraction(2, 7))}[row['claim_id']]
                for k, value in row['result'].items():
                    if k != 'unit': self.assertEqual(value, expected)
            self.assertEqual(len(result['input']['phases']), 2)

    def test_A06_zero_fraction_is_inactive_not_a_missing_record(self):
        data = case()
        data['phases'][0]['volume_fraction'] = 1
        data['phases'][1].update(volume_fraction=0, bulk_modulus=None, shear_modulus=None)
        result = self.assert_report(data)
        self.assertEqual(rows(result)[0]['result']['lower'], 12)
        absent = deepcopy(data); absent['phases'].pop()
        self.assert_report(absent, 'VVVVVVVV')
        malformed = deepcopy(data); malformed['phases'][1]['bulk_modulus'] = {'value': None, 'unit': 'psi'}
        with self.assertRaises(ValidationError): build_composite_report(malformed)
        data['conditions']['effective_symmetry'] = None
        self.assert_report(data, 'UUUUUUUU')

    def test_A07_tiny_positive_fraction_is_still_active(self):
        data = case(); data['phases'][0]['volume_fraction'] = 1
        data['phases'][1].update(volume_fraction=1e-299, bulk_modulus=None, shear_modulus=None)
        result = self.assert_report(data, 'UUUUUUUU')
        for row in rows(result):
            check = next(c for c in row['checks'] if c['condition_id'] == 'positive_bulk_moduli')
            self.assertEqual(check['observed'][-1], {'phase_id': 'phase_b', 'value_pa': None})
        self.assertEqual(result['input']['phases'][1]['volume_fraction'], 1e-299)

    def test_A08_negative_and_zero_poisson_are_valid_dimensionless(self):
        for k, expected_nu, expected_e in ((2, -.25, 9), (4, 0, 12)):
            result = self.assert_report(set_pair(case(), k, 6))
            self.assertEqual(rows(result)[7]['result'], {'lower': expected_nu, 'upper': expected_nu, 'unit': '1'})
            self.assertEqual(rows(result)[6]['result']['lower'], expected_e)

    def test_A09_unknown_effective_isotropy_null_and_omitted(self):
        for omitted in (False, True):
            data = case()
            if omitted: del data['conditions']['effective_symmetry']
            else: data['conditions']['effective_symmetry'] = None
            result = self.assert_report(data, 'UUUUUUUU')
            self.assertTrue(all(next(c for c in r['checks'] if c['condition_id'] == 'effective_symmetry')['state'] == 'unknown' for r in rows(result)))
            self.assertEqual('effective_symmetry' in result['input']['conditions'], not omitted)

    def test_A10_missing_active_shear_blocks_even_bulk_classical_rules(self):
        for missing in (None, {'value': None, 'unit': 'GPa'}):
            data = case(); data['phases'][1]['shear_modulus'] = missing
            result = self.assert_report(data, 'UUUUUUUU')
            self.assertIsNone(rows(result)[1]['result']); self.assertIsNone(rows(result)[2]['result'])

    def test_A11_no_complement_or_mass_fraction_conversion(self):
        for first in (.25, 1):
            for omitted in (False, True):
                data = case(); data['phases'][0]['volume_fraction'] = first
                if omitted: del data['phases'][1]['volume_fraction']
                else: data['phases'][1]['volume_fraction'] = None
                result = self.assert_report(data, 'UUUUUUUU')
                self.assertIsNone(result['evaluation']['fraction_normalization']['normalized_fractions'])
        data = case(); data['phases'][1]['mass_fraction'] = .75
        with self.assertRaises(ValidationError): build_composite_report(data)

    def test_A12_crossed_order_keeps_classical_bounds_only(self):
        data = case()
        data['phases'][0]['shear_modulus']['value'] = 18
        data['phases'][1]['shear_modulus']['value'] = 6
        result = self.assert_report(data, 'VSSVSSVV')
        for identifier, side, value in (('reuss_bulk', 'lower', 24), ('voigt_bulk', 'upper', 30),
                                        ('reuss_shear', 'lower', 7.2), ('voigt_shear', 'upper', 9)):
            self.assertEqual(by_id(result)[identifier]['result'][side], value)
        for row in rows(result)[6:]: self.assertEqual(row['dependencies']['claim_ids'], [IDS[0], IDS[3]])

    def test_A13_constituent_and_effective_symmetry_are_independent(self):
        data = case(); data['conditions']['constituent_symmetry'] = 'anisotropic'
        result = self.assert_report(data, 'VVVVVVVV')
        checks = {c['condition_id']: c for c in rows(result)[0]['checks']}
        self.assertEqual(checks['constituent_symmetry']['state'], 'violated')
        self.assertEqual(checks['effective_symmetry']['state'], 'satisfied')

    def test_A14_known_violation_dominates_but_does_not_erase_unknown(self):
        data = case(); data['conditions']['loading'] = 'dynamic'; data['phases'][0]['shear_modulus'] = None
        result = self.assert_report(data, 'VVVVVVVV')
        for row in rows(result):
            checks = {c['condition_id']: c for c in row['checks']}
            self.assertEqual(checks['loading']['state'], 'violated')
            self.assertEqual(checks['positive_shear_moduli']['state'], 'unknown')
        supplied_g = deepcopy(data); supplied_g['phases'][0]['shear_modulus'] = {'value': 6, 'unit': 'GPa'}
        self.assert_report(supplied_g, 'VVVVVVVV')

    def test_A15_unsupported_regimes_and_phase_counts_stay_explicit(self):
        for key, value in (('dimension', 2), ('kinematics', 'finite_strain'), ('interface', 'imperfect'),
                           ('constitutive_law', 'viscoelastic'), ('effective_symmetry', 'anisotropic')):
            data = case(); data['conditions'][key] = value
            self.assert_report(data, 'VVVVVVVV')
        one = case(); one['phases'] = one['phases'][:1]; one['phases'][0]['volume_fraction'] = 1
        three = case(); three['phases'].append(deepcopy(three['phases'][0])); three['phases'][2]['id'] = 'phase_c'
        for phase, f in zip(three['phases'], (.25, .5, .25)): phase['volume_fraction'] = f
        for data in (one, three): self.assert_report(data, 'VVVVVVVV')
        data = case(); data['conditions']['dimension'] = 2; data['phases'][0]['bulk_modulus']['unit'] = 'N/m'
        with self.assertRaises(ValidationError): build_composite_report(data)

    def test_A16_active_zero_or_negative_stiffness_is_never_repaired(self):
        for prop in ('bulk_modulus', 'shear_modulus'):
            for value in (0, -1, -1e-300):
                data = case(); data['phases'][1][prop]['value'] = value
                self.assert_report(data, 'VVVVVVVV')

    def test_A17_strict_invalid_json_rejected_without_output_every_language(self):
        raw = json.dumps(case())
        invalid = {
            'duplicate_root': raw.replace('"schema_version": "1.0.0"', '"schema_version": "1.0.0", "schema_version": "1.0.0"'),
            'duplicate_nested': raw.replace('"value": 12', '"value": 12, "value": 12'),
            'nan': raw.replace('"value": 12', '"value": NaN'),
            'infinity': raw.replace('"value": 12', '"value": Infinity'),
            'negative_infinity': raw.replace('"value": 12', '"value": -Infinity'),
            'overflow': raw.replace('"value": 12', '"value": 1e400'),
            'underflow': raw.replace('"value": 12', '"value": 1e-400'),
            'boolean': raw.replace('"value": 12', '"value": true'),
            'duplicate_phase': raw.replace('phase_b', 'phase_a'),
            'unsupported_unit': raw.replace('GPa', 'psi'),
            'trailing': raw + ' false', 'root_array': '[]', 'truncated': raw[:-1],
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, content in invalid.items():
                source = root / (name + '.json'); source.write_text(content)
                for lang in LANGUAGES:
                    with self.subTest(variant=name, lang=lang):
                        dest = root / (name + '-' + lang)
                        run = cli('report', source, '--output', dest, '--lang', lang)
                        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                        self.assertFalse(dest.exists(), 'invalid input created a report')
                        self.assertNotIn('Traceback', run.stderr)

    def test_A18_fraction_tolerance_is_bookkeeping_with_raw_inputs_preserved(self):
        data = case(); data['phases'][0]['volume_fraction'] = .2500000000002
        result = self.assert_report(data)
        normalization = result['evaluation']['fraction_normalization']
        self.assertTrue(normalization['performed'])
        self.assertEqual(normalization['original_sum'], '1.0000000000002')
        self.assertEqual(normalization['absolute_tolerance'], '1e-12')
        self.assertEqual(result['input']['phases'][0]['volume_fraction'], .2500000000002)
        self.assertNotEqual(normalization['normalized_fractions'], ['0.2500000000002', '0.75'])
        data['phases'][0]['volume_fraction'] = .250000000002
        with self.assertRaises(ValidationError): build_composite_report(data)

    def test_A19_numeric_range_reports_are_complete_and_replayable(self):
        from materials_boundaries.composite_export import export_composite_report
        for value, raw_unit, output_unit in ((1e307, 'GPa', 'Pa'), (1e-323, 'Pa', 'GPa')):
            data = set_pair(case(), value, value, raw_unit)
            bundle = self.assert_report(data, 'NNNNNNNN', output_unit)
            self.assertTrue(all(r['applicability'] == 'satisfied' for r in rows(bundle)))
            with tempfile.TemporaryDirectory() as temp:
                dest = Path(temp) / 'report'
                self.assertEqual(export_composite_report(data, dest, output_unit=output_unit)['exit_code'], 3)
                self.assertEqual({p.name for p in dest.iterdir()}, ARTIFACTS)
                run = cli('verify', dest / 'bundle.json', '--json')
                self.assertEqual(run.returncode, 0, run.stderr)
                input_path = Path(temp) / 'range.json'; input_path.write_text(json.dumps(data))
                run = cli('report', input_path, '--output', Path(temp) / 'cli-report', '--unit', output_unit)
                self.assertEqual(run.returncode, 3, run.stdout + run.stderr)
                self.assertTrue((Path(temp) / 'cli-report/manifest.json').is_file())

    def test_A20_poisson_boundary_rounding_does_not_destroy_other_results(self):
        for k, g in ((1e90, 2), (2, 1e90)):
            self.assert_report(set_pair(case(), k, g), 'SSSSSSSN')
        # Interior binary floats must not be rounded by human formatting onto
        # excluded boundaries, even when twelve significant digits would do so.
        for k, g in ((1e15, 2), (2, 1e15)):
            result = self.assert_report(set_pair(case(), k, g))
            nu = rows(result)[-1]['result']['lower']
            self.assertTrue(-1 < nu < .5)
            self.assertNotEqual(float(format(nu, '.12g')), nu)

    def test_A21_arbitrary_precision_integer_pairing_survives_file_roundtrip(self):
        from materials_boundaries.composite_export import export_composite_report
        data = case()
        for phase, k, g in zip(data['phases'], (10**110, 10**110 + 3), (9, 4)):
            phase['bulk_modulus']['value'] = k; phase['shear_modulus']['value'] = g
        result = self.assert_report(data, 'VSSVSSVV')
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / 'report'; export_composite_report(data, dest)
            for name in ('input.json', 'bundle.json'):
                self.assertIn(str(10**110 + 3), (dest / name).read_text())
            saved = load_json(dest / 'bundle.json')
            self.assertEqual(saved, result); validate_composite_report(saved)
            self.assertEqual(saved['input']['phases'][1]['bulk_modulus']['value'] - saved['input']['phases'][0]['bulk_modulus']['value'], 3)

    def test_A22_literature_model_contract_separates_raw_derived_and_effective(self):
        data = model_case(); bundle = self.assert_report(data)
        self.assertEqual(bundle['catalogs']['unresolved_source_ids'], ['original_unresolved_contract_fixture'])
        self.assertEqual(bundle['input']['provenance']['model_evidence'], data['provenance']['model_evidence'])
        self.assertEqual([r['youngs_modulus']['value'] for r in data['provenance']['model_evidence']['raw_parameters']], [21, 84])
        self.assertNotIn(rows(bundle)[6]['result']['lower'], (21, 84))
        for field in ('temperature_k', 'material_grade', 'cure_state', 'measurement_uncertainty'):
            self.assertIsNone(bundle['input']['provenance']['model_evidence'][field])
        for mode in ('derived', 'phase', 'source', 'missing', 'basis', 'fraction_basis', 'promote_measured'):
            altered = model_case(); evidence = altered['provenance']['model_evidence']
            if mode == 'derived': altered['phases'][0]['bulk_modulus']['value'] = 15
            elif mode == 'phase': evidence['raw_parameters'][0]['phase_id'] = 'missing_phase'
            elif mode == 'source': evidence['source_id'] = 'missing_source'
            elif mode == 'missing': del altered['provenance']['model_evidence']
            elif mode == 'basis': evidence['condition_basis']['effective_symmetry'] = 'unknown'
            elif mode == 'fraction_basis': evidence['fraction_basis'] = 'measured'
            else: altered['provenance']['kind'] = 'measured'
            with self.subTest(mode=mode), self.assertRaises(ValidationError): build_composite_report(altered)
        data['conditions']['effective_symmetry'] = None
        data['provenance']['model_evidence']['condition_basis']['effective_symmetry'] = 'unknown'
        self.assert_report(data, 'UUUUUUUU')

    def test_A23_measured_input_label_never_upgrades_scientific_verification(self):
        data = case(); data['provenance']['kind'] = 'measured'
        data['provenance']['note'] = 'User-supplied measured-input label; no sample metadata supplied.'
        bundle = self.assert_report(data)
        self.assertEqual(bundle['evaluation']['input_provenance']['kind'], 'measured')
        self.assertFalse(bundle['policy']['independent_scientific_review'])
        self.assertEqual([r['result'] for r in rows(bundle)], [r['result'] for r in rows(build_composite_report(case()))])
        for claim in bundle['catalogs']['claims']['records']:
            self.assertFalse(claim['verification']['independent_scientific_review'])

    def test_A24_no_measured_composite_scoring_or_theorem_refutation_api(self):
        from materials_boundaries.composite_render import render_composite_report
        bundle = self.assert_report(case())
        text = render_composite_report(bundle).lower()
        for phrase in ('confidence interval', 'uncertainty', 'measurement', 'fractions', 'premises'):
            self.assertIn(phrase, text)
        for observation in (35, 100):
            data = case(); data['effective_youngs_modulus'] = {'value': observation, 'unit': 'GPa'}
            with self.assertRaises(ValidationError): build_composite_report(data)
        self.assertNotIn('p_value', bundle); self.assertNotIn('safety_margin', bundle)

    def test_A25_same_case_hs_dependencies_and_independent_corner_arithmetic(self):
        bundle = self.assert_report(case()); r = by_id(bundle)
        kl, ku = Fraction(336, 13), Fraction(192, 7)
        gl, gu = Fraction(411, 31), Fraction(267, 19)
        young = lambda k, g: 9 * k * g / (3 * k + g)
        poisson = lambda k, g: (3 * k - 2 * g) / (2 * (3 * k + g))
        self.assertEqual(r[IDS[6]]['result']['lower'], float(young(kl, gl)))
        self.assertEqual(r[IDS[6]]['result']['upper'], float(young(ku, gu)))
        self.assertEqual(r[IDS[7]]['result']['lower'], float(poisson(kl, gu)))
        self.assertEqual(r[IDS[7]]['result']['upper'], float(poisson(ku, gl)))
        for row in rows(bundle)[6:]:
            self.assertEqual(row['dependencies']['instance_id'], bundle['instance_id'])
            self.assertEqual(row['dependencies']['claim_ids'], [IDS[0], IDS[3]])
            self.assertEqual(row['dependencies']['joint_attainability'], 'not_asserted')
        altered = deepcopy(bundle)
        altered['evaluation']['evaluations'][6]['dependencies']['instance_id'] = 'another-case'
        with self.assertRaises(CompositeReplayError): validate_composite_report(altered)

    def test_A26_frozen_engine_catalog_and_claim_level_evidence_gaps(self):
        for path, digest in FIXTURE['frozen_files'].items():
            with self.subTest(path=path): self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
        # Supported contribution workflows append independent records/labels.
        # Freeze every original record/value, not the complete growing file;
        # the eight executable claims and their evidence are never relaxed.
        def digest(value):
            raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode('utf-8')
            return hashlib.sha256(raw).hexdigest()

        for name, frozen in FIXTURE['frozen_catalogs'].items():
            catalog = read_catalog(name)
            with self.subTest(catalog=name, section='metadata'):
                self.assertEqual(digest({key: value for key, value in catalog.items() if key != 'records'}),
                                 frozen['metadata_sha256'])
            records = {record['id']: record for record in catalog['records']}
            self.assertEqual(len(records), len(catalog['records']), 'duplicate catalog record ID')
            self.assertEqual([record['id'] for record in catalog['records'] if record['id'] in frozen['records_sha256']],
                             frozen['record_order'])
            for identifier, expected in frozen['records_sha256'].items():
                with self.subTest(catalog=name, record=identifier):
                    self.assertIn(identifier, records)
                    record = previous_record(name, records[identifier])
                    # Established contribution tests may append independent
                    # evidence to catalog-only claims. Keep every original
                    # evidence entry, its multiplicity and relative order;
                    # reconstruct the complete pinned record before hashing.
                    # Executable claims have no evidence exception at all.
                    if identifier in frozen.get('evidence_digests', {}):
                        original = frozen['evidence_digests'][identifier]
                        selected = [entry for entry in record['evidence'] if digest(entry) in original]
                        self.assertEqual([digest(entry) for entry in selected], original,
                                         'original evidence was removed, changed, duplicated or reordered')
                        record['evidence'] = selected
                    self.assertEqual(digest(record), expected)
        locale = read_catalog('locales')
        frozen = FIXTURE['frozen_locales']
        self.assertEqual(digest({key: value for key, value in locale.items() if key != 'languages'}),
                         frozen['metadata_sha256'])
        for lang, values in frozen['values_sha256'].items():
            self.assertIn(lang, locale['languages'])
            for key, expected in values.items():
                with self.subTest(lang=lang, label=key):
                    self.assertIn(key, locale['languages'][lang])
                    self.assertEqual(digest(locale['languages'][lang][key]), expected)
        bundle = self.assert_report(case())
        all_claims = {r['id']: r for r in read_catalog('claims')['records']}
        self.assertEqual(bundle['catalogs']['claims']['records'], [all_claims[key] for key in IDS])
        self.assertEqual(len(bundle['catalogs']['sources']['records']), 3)
        claims = {c['id']: c for c in bundle['catalogs']['claims']['records']}
        for identifier in (IDS[0], IDS[3]):
            evidence = next(e for e in claims[identifier]['evidence'] if e['source_id'] == 'hashin_shtrikman_1963')
            self.assertIsNone(evidence['locator'])
            self.assertEqual(evidence['verification_status'], 'original_equation_not_inspected')
        for identifier in ('reuss_bulk', 'reuss_shear'):
            self.assertEqual(claims[identifier]['evidence'][0]['verification_status'], 'standard_formula_with_context_source')
        for identifier in IDS[6:]:
            self.assertTrue(any('project' in e['verified_as'] and 'derivation' in e['verified_as'] for e in claims[identifier]['evidence']))
            self.assertTrue(any('visual' in gap and 'not completed' in gap for gap in previous_record('claims', claims[identifier])['verification']['gaps']))
            self.assertFalse(any('visual' in gap and 'not completed' in gap for gap in claims[identifier]['verification']['gaps']))

    def test_A27_unresolved_user_source_never_manufactures_bibliography(self):
        data = case(); data['provenance']['source_ids'] = ['user_note_unknown_source', 'javascript:alert(1)']
        bundle = self.assert_report(data)
        self.assertEqual(bundle['catalogs']['unresolved_source_ids'], ['javascript:alert(1)', 'user_note_unknown_source'])
        self.assertEqual(bundle['catalogs']['sources'], build_composite_report(case())['catalogs']['sources'])
        from materials_boundaries.composite_render import render_composite_report
        for lang in LANGUAGES:
            parser = StaticReportParser(); parser.feed(render_composite_report(bundle, lang=lang, format='html'))
            self.assertFalse(any('javascript:' in link for link in parser.links))

    def test_A28_language_independent_core_determinism_and_explicit_rejection(self):
        from materials_boundaries.composite_render import render_composite_report
        from materials_boundaries.composite_export import export_composite_report
        bundle = self.assert_report(case())
        with localcontext() as context:
            context.prec = 2; context.Emax = 2; context.Emin = -2; context.traps[Inexact] = True
            self.assertEqual(build_composite_report(case()), bundle)
        with tempfile.TemporaryDirectory() as temp:
            cores = []; evaluations = []; inputs = []
            for lang in LANGUAGES:
                directory = Path(temp) / lang
                export_composite_report(case(), directory, lang=lang)
                cores.append((directory / 'bundle.json').read_bytes())
                evaluations.append((directory / 'evaluation.json').read_bytes())
                inputs.append((directory / 'input.json').read_bytes())
            self.assertEqual(len(set(cores)), 1); self.assertEqual(len(set(evaluations)), 1); self.assertEqual(len(set(inputs)), 1)
        for kwargs in ({'lang': 'xx'}, {'format': 'csv'}):
            with self.assertRaises(ValueError): render_composite_report(bundle, **kwargs)
        # Every numbered scenario remains discoverable rather than replaced by
        # a generic happy-path smoke check. Each valid variant above uses all
        # four render languages; malformed variants use localized CLI errors.
        expected = {s['id'] for s in FIXTURE['scenarios']}
        actual = {name.split('_')[1] for name in dir(self) if re.match(r'test_A\d\d_', name)}
        self.assertEqual(actual, expected)


    def test_A28_static_parser_does_not_count_hidden_audit_data_as_visible(self):
        parser = StaticReportParser()
        parser.feed('<html><head><title>HEAD</title><style>STYLE</style></head><body>'
                    '<p>VISIBLE</p><details><summary>SUMMARY</summary><p>HIDDEN</p>'
                    '<details open><summary>NESTED</summary><p>DEEP</p></details></details>'
                    '<article>ROW</article></body></html>')
        visible = '\n'.join(parser.visible_content)
        self.assertIn('VISIBLE', visible); self.assertIn('ROW', visible)
        for hidden in ('HEAD', 'STYLE', 'SUMMARY', 'HIDDEN', 'NESTED', 'DEEP'):
            self.assertNotIn(hidden, visible)
        self.assertIn('HIDDEN', '\n'.join(parser.content))
        self.assertNotIn('HEAD', '\n'.join(parser.content))
        self.assertEqual(parser.result_rows, ['ROW'])
        self.assertNotIn('open', parser.details[0]['attrs'])
        self.assertIn('open', parser.details[1]['attrs'])

    def test_A29_replay_rebuilds_full_core_and_fails_closed_on_tampering(self):
        bundle = self.assert_report(case())
        mutations = {
            'endpoint': ('evaluation', 'evaluations', 0, 'result', 'lower'),
            'output_unit': ('output_unit',), 'result_unit': ('evaluation', 'evaluations', 0, 'result', 'unit'),
            'condition': ('input', 'conditions', 'loading'), 'fraction': ('input', 'phases', 0, 'volume_fraction'),
            'root_id': ('instance_id',), 'input_id': ('input', 'id'), 'evaluation_id': ('evaluation', 'instance_id'),
            'dependency': ('evaluation', 'evaluations', 6, 'dependencies', 'instance_id'),
            'rule': ('evaluation', 'evaluations', 0, 'rule_id'),
            'claim_id': ('evaluation', 'evaluations', 0, 'claim_id'),
            'claim_review': ('catalogs', 'claims', 'records', 0, 'verification', 'independent_scientific_review'),
            'source_gap': ('catalogs', 'claims', 'records', 0, 'verification', 'gaps', 0),
            'source_locator': ('catalogs', 'claims', 'records', 0, 'evidence', 0, 'locator'),
            'source_status': ('catalogs', 'sources', 'records', 0, 'read_status'),
            'source_title': ('catalogs', 'sources', 'records', 0, 'title'),
            'policy': ('policy', 'joint_attainability'), 'review_policy': ('policy', 'independent_scientific_review'),
            'version': ('engine_version',), 'report_version': ('report_version',), 'schema_version': ('schema_version',),
            'digest': ('digests', 'input'), 'canonicalization': ('digests', 'serialization'),
            'check_observed_id': ('evaluation', 'evaluations', 6, 'checks', -1, 'observed', 'instance_id'),
        }
        for name, path in mutations.items():
            altered = deepcopy(bundle); target = altered
            for key in path[:-1]: target = target[key]
            value = target[path[-1]]
            if name in ('output_unit', 'result_unit'): replacement = 'MPa'
            elif name == 'condition': replacement = 'dynamic'
            elif name == 'fraction': replacement = .2500000000001
            elif name == 'digest': replacement = '0' * 64
            elif isinstance(value, bool): replacement = not value
            elif isinstance(value, (int, float)): replacement = value + 1
            else: replacement = 'altered-' + value
            target[path[-1]] = replacement
            snapshot = deepcopy(altered)
            with self.subTest(target=name), self.assertRaises(CompositeReplayError): validate_composite_report(altered)
            self.assertEqual(altered, snapshot, 'verifier silently rewrote a bad bundle')
        # Updating hashes does not legitimize forged evaluation or evidence.
        forged = deepcopy(bundle); forged['evaluation']['evaluations'][0]['result']['lower'] = 999
        forged['digests']['evaluation'] = hashlib.sha256(json.dumps(forged['evaluation'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with self.assertRaises(CompositeReplayError): validate_composite_report(forged)
        from materials_boundaries.composite_render import render_composite_report
        for lang in LANGUAGES:
            with self.assertRaises(CompositeReplayError): render_composite_report(forged, lang=lang)
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'bundle.json'
            for data, exit_code in ((bundle, 0), (forged, 4), ({'kind': 'composite_report'}, 2)):
                file.write_text(json.dumps(data))
                before = file.read_bytes(); run = cli('verify', file, '--json')
                self.assertEqual(run.returncode, exit_code, run.stdout + run.stderr)
                self.assertEqual(file.read_bytes(), before)
                json.loads(run.stderr if exit_code == 2 else run.stdout)
        unknown = case(); unknown['conditions'] = {}
        self.assert_report(unknown, 'UUUUUUUU')
        # Whole internally consistent replacement is replayable; hashes are not
        # authentication or a record of which input the author originally used.
        replaced = case(); replaced['id'] = 'different-whole-bundle'
        validate_composite_report(build_composite_report(replaced))

    def test_A30_hostile_labels_safe_local_deterministic_export_and_rollback(self):
        from materials_boundaries import composite_export as export
        stage_backend = export
        if os.name == 'nt':
            from materials_boundaries import _composite_windows as stage_backend
        payload = '</script><script>alert("X")</script></pre><img src=x onerror=alert(1)>漢字 Ä "\''
        data = case(); data['id'] = '../' + payload
        data['phases'][0]['id'] = payload
        data['provenance']['note'] = payload + ' LONG ' + 'λ' * 12000
        self.assert_report(data)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); output = root / 'report'
            result = export.export_composite_report(data, output)
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual(set(result['artifacts']), ARTIFACTS)
            self.assertEqual({p.name for p in output.iterdir()}, ARTIFACTS)
            self.assertEqual(load_json(output / 'input.json'), data)
            manifest = load_json(output / 'manifest.json')
            self.assertEqual(set(manifest['files']), ARTIFACTS - {'manifest.json'})
            for name, record in manifest['files'].items():
                content = (output / name).read_bytes()
                self.assertEqual(record['sha256'], hashlib.sha256(content).hexdigest())
                self.assertEqual(record['bytes'], len(content))
            again = root / 'again'; export.export_composite_report(data, again)
            self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, {p.name: p.read_bytes() for p in again.iterdir()})
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            with self.assertRaises((ValidationError, OSError)): export.export_composite_report(data, output)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
            marker = root / 'occupied'; marker.mkdir(); (marker / 'keep.txt').write_text('unrelated')
            with self.assertRaises((ValidationError, OSError)): export.export_composite_report(data, marker)
            self.assertEqual((marker / 'keep.txt').read_text(), 'unrelated')
            outside = root / 'outside'; outside.mkdir(); symlink = root / 'alias'
            if os.name == 'nt':
                subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(symlink), str(outside)],
                               check=True, capture_output=True)
            else:
                symlink.symlink_to(outside, target_is_directory=True)
            for target in (symlink, symlink / 'nested', root / '..' / root.name / 'escape'):
                with self.assertRaises((ValidationError, OSError)): export.export_composite_report(data, target)
            self.assertEqual(list(outside.iterdir()), [])
            # Inject a failure at each publish link, including manifest-last.
            real_link = export.os.link
            for fail_at in range(1, 7):
                target = root / ('fail-link-' + str(fail_at)); calls = []
                def failing_link(*args, **kwargs):
                    calls.append(Path(args[0]).name)
                    if len(calls) == fail_at: raise OSError('injected publish failure')
                    return real_link(*args, **kwargs)
                with patch.object(export.os, 'link', side_effect=failing_link), self.assertRaises(OSError):
                    export.export_composite_report(case(), target)
                self.assertFalse(target.exists() and list(target.iterdir()), 'partial export survived ordinary failure')
                if fail_at == 6: self.assertEqual(calls[-1], 'manifest.json')
            # An already-existing empty output directory is preserved on failure.
            target = root / 'empty'; target.mkdir()
            with patch.object(stage_backend, '_stage_file', side_effect=OSError('injected stage failure')), self.assertRaises(OSError):
                export.export_composite_report(case(), target)
            self.assertTrue(target.is_dir()); self.assertEqual(list(target.iterdir()), [])
            invalid = case(); invalid['phases'][0]['bulk_modulus']['unit'] = 'psi'
            with self.assertRaises(ValidationError): export.export_composite_report(invalid, root / 'invalid')
            self.assertFalse((root / 'invalid').exists())


    def test_A30_intake_explicit_blank_edit_back_and_interrupt_every_prompt(self):
        from materials_boundaries.composite_intake import (
            IntakeCancelled, blank_composite_instance, interactive_composite_instance,
            original_demo_instance,
        )

        class TTY(io.StringIO):
            def isatty(self):
                return True

        class InterruptTTY(TTY):
            def __init__(self, text, interrupt_at):
                super().__init__(text)
                self.index = 0
                self.interrupt_at = interrupt_at

            def readline(self, *args):
                self.index += 1
                if self.index == self.interrupt_at:
                    raise KeyboardInterrupt
                return super().readline(*args)

        answers = ['acceptance-intake', '1', 'phase_a', '1', '0.25', '12 GPa', '6 GPa',
                   'phase_b', '1', '0.75', '36 GPa', '18 GPa', *(['1'] * 7), '', '', '/save']
        self.assertEqual(original_demo_instance(), case())
        blank = blank_composite_instance()
        self.assertTrue(all(value is None for value in blank['conditions'].values()))
        self.assertEqual(blank['provenance']['kind'], 'unspecified')
        self.assert_report(blank, 'UUUUUUUU')
        for lang in LANGUAGES:
            text = '\n'.join(answers) + '\n'
            draft = interactive_composite_instance(lang=lang, input_stream=TTY(text), output_stream=TTY())
            self.assertEqual(draft['conditions'], CONDITIONS)
            self.assertEqual(draft['phases'], case()['phases'])
            # Blank on an edited observation explicitly clears it, not silently
            # accepting the displayed previous value or a supported default.
            edits = answers[:-1] + ['/edit 13', '', '/edit 4', '1', '', '/save']
            cleared = interactive_composite_instance(lang=lang, input_stream=TTY('\n'.join(edits) + '\n'), output_stream=TTY())
            self.assertIsNone(cleared['conditions']['effective_symmetry'])
            self.assertIsNone(cleared['phases'][0]['volume_fraction'])
            self.assertEqual(cleared['phases'][1]['volume_fraction'], .75)
            # Back from an uncommitted review edit preserves the reviewed field.
            back = answers[:-1] + ['/edit 5', '/back', '/save']
            unchanged = interactive_composite_instance(lang=lang, input_stream=TTY('\n'.join(back) + '\n'), output_stream=TTY())
            self.assertEqual(unchanged, draft)
            for index in range(1, len(answers) + 1):
                with self.subTest(lang=lang, prompt=index), self.assertRaises(IntakeCancelled):
                    interactive_composite_instance(lang=lang, input_stream=InterruptTTY(text, index), output_stream=TTY())
                # Explicit cancel at every happy-path question also discards.
                cancelled = answers[:index - 1] + ['/cancel']
                with self.subTest(lang=lang, cancel=index), self.assertRaises(IntakeCancelled):
                    interactive_composite_instance(lang=lang, input_stream=TTY('\n'.join(cancelled) + '\n'), output_stream=TTY())
            for suffix in (['/edit', '/cancel'], ['/edit', '5', '/cancel'], ['/edit 4', '1', '/cancel']):
                with self.assertRaises(IntakeCancelled):
                    interactive_composite_instance(lang=lang, input_stream=TTY('\n'.join(answers[:-1] + suffix) + '\n'), output_stream=TTY())
        with self.assertRaises(ValidationError):
            interactive_composite_instance(input_stream=io.StringIO('\n'.join(answers)), output_stream=TTY())
        with self.assertRaises(ValidationError):
            interactive_composite_instance(input_stream=TTY('\n'.join(answers)), output_stream=io.StringIO())
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'non-tty.json'
            run = cli('init', '--interactive', '--output', destination)
            self.assertEqual(run.returncode, 2)
            self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
