"""Independent, test-only arithmetic for four display-only crystal predicates.

No catalog expression is parsed or executed. Fraction-based elimination operates
on separately hand-built numeric matrices; no eigensolver/runtime dependency is
introduced. All coefficients below and in the accompanying fixture are invented.
"""
import copy
from fractions import Fraction
from itertools import combinations
import json
import math
import random
import unittest
from unittest.mock import patch

from materials_boundaries import evaluate, load_json
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from catalog_fixtures import expected_provenance
from test_engine import ROOT, example
from catalog_fixtures import (EXECUTABLE_IDS, GRIFFITH_IDS, MECHANICS_IDS, CORE_STABILITY_IDS,
                              POROUS_IDS, HISTORICAL_SOURCE_IDS, OBSERVATION_IDS,
                              historical_records, select_records, evidence_for, scientific_digest)

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

KINDS = ('tetragonal_i', 'tetragonal_ii', 'rhombohedral_i', 'rhombohedral_ii')
IDS = tuple(kind + '_born_stability' for kind in KINDS)
SOURCE = 'mouhat_coudert_2014_elastic_stability'
SYMBOLS = {
    'tetragonal_i': ('C11', 'C12', 'C13', 'C33', 'C44', 'C66'),
    'tetragonal_ii': ('C11', 'C12', 'C13', 'C33', 'C44', 'C66', 'C16'),
    'rhombohedral_i': ('C11', 'C12', 'C13', 'C33', 'C44', 'C14'),
    'rhombohedral_ii': ('C11', 'C12', 'C13', 'C33', 'C44', 'C14', 'C15'),
}
MATRICES = {
    'tetragonal_i': [
        ['C11', 'C12', 'C13', '0', '0', '0'],
        ['C12', 'C11', 'C13', '0', '0', '0'],
        ['C13', 'C13', 'C33', '0', '0', '0'],
        ['0', '0', '0', 'C44', '0', '0'],
        ['0', '0', '0', '0', 'C44', '0'],
        ['0', '0', '0', '0', '0', 'C66'],
    ],
    'tetragonal_ii': [
        ['C11', 'C12', 'C13', '0', '0', 'C16'],
        ['C12', 'C11', 'C13', '0', '0', '-C16'],
        ['C13', 'C13', 'C33', '0', '0', '0'],
        ['0', '0', '0', 'C44', '0', '0'],
        ['0', '0', '0', '0', 'C44', '0'],
        ['C16', '-C16', '0', '0', '0', 'C66'],
    ],
    'rhombohedral_i': [
        ['C11', 'C12', 'C13', 'C14', '0', '0'],
        ['C12', 'C11', 'C13', '-C14', '0', '0'],
        ['C13', 'C13', 'C33', '0', '0', '0'],
        ['C14', '-C14', '0', 'C44', '0', '0'],
        ['0', '0', '0', '0', 'C44', 'C14'],
        ['0', '0', '0', '0', 'C14', '(C11-C12)/2'],
    ],
    'rhombohedral_ii': [
        ['C11', 'C12', 'C13', 'C14', 'C15', '0'],
        ['C12', 'C11', 'C13', '-C14', '-C15', '0'],
        ['C13', 'C13', 'C33', '0', '0', '0'],
        ['C14', '-C14', '0', 'C44', '0', '-C15'],
        ['C15', '-C15', '0', '0', 'C44', 'C14'],
        ['0', '0', '0', '-C15', 'C14', '(C11-C12)/2'],
    ],
}
LAST_EXPRESSIONS = (
    'C66', 'C66*(C11-C12)-2*C16^2',
    'C44*(C11-C12)-2*C14^2', 'C44*(C11-C12)-2*(C14^2+C15^2)',
)


def records():
    return [query_catalog('claims', record_id=identifier)['records'][0] for identifier in IDS]


def fixtures():
    return load_json(ROOT / 'examples/catalog/crystal-stability-synthetic.json')['fixtures']


def stiffness(kind, p):
    """Independent direct construction, never substitution into catalog strings."""
    a, b, c, d, e = (Fraction(p[name]) for name in ('C11', 'C12', 'C13', 'C33', 'C44'))
    f = Fraction(p['C66']) if kind.startswith('tetragonal') else (a - b) / 2
    matrix = [[a, b, c, 0, 0, 0], [b, a, c, 0, 0, 0],
              [c, c, d, 0, 0, 0], [0, 0, 0, e, 0, 0],
              [0, 0, 0, 0, e, 0], [0, 0, 0, 0, 0, f]]
    if kind == 'tetragonal_ii':
        h = Fraction(p['C16'])
        matrix[0][5] = matrix[5][0] = h
        matrix[1][5] = matrix[5][1] = -h
    if kind.startswith('rhombohedral'):
        g = Fraction(p['C14'])
        matrix[0][3] = matrix[3][0] = g
        matrix[1][3] = matrix[3][1] = -g
        matrix[4][5] = matrix[5][4] = g
    if kind == 'rhombohedral_ii':
        j = Fraction(p['C15'])
        matrix[0][4] = matrix[4][0] = j
        matrix[1][4] = matrix[4][1] = -j
        matrix[3][5] = matrix[5][3] = -j
    return [[Fraction(entry) for entry in row] for row in matrix]


def determinant(matrix):
    """Generic exact Gaussian elimination, including pivot swaps and singularity."""
    m = [[Fraction(entry) for entry in row] for row in matrix]
    product = Fraction(1)
    for col in range(len(m)):
        pivot_row = next((row for row in range(col, len(m)) if m[row][col]), None)
        if pivot_row is None:
            return Fraction(0)
        if pivot_row != col:
            m[pivot_row], m[col] = m[col], m[pivot_row]
            product = -product
        pivot = m[col][col]
        product *= pivot
        for row in range(col + 1, len(m)):
            multiplier = m[row][col] / pivot
            for entry in range(col + 1, len(m)):
                m[row][entry] -= multiplier * m[col][entry]
            m[row][col] = 0
    return product


def minor(matrix, indices):
    return determinant([[matrix[i][j] for j in indices] for i in indices])


def leading_minors(matrix):
    return tuple(minor(matrix, range(size)) for size in range(1, 7))


def principal_minors(matrix):
    return [minor(matrix, indices) for size in range(1, 7)
            for indices in combinations(range(6), size)]


def margins(kind, p):
    """Separately hand-coded predicates, not an application evaluation API."""
    a, b, c, d, e = (Fraction(p[name]) for name in ('C11', 'C12', 'C13', 'C33', 'C44'))
    if kind == 'tetragonal_i':
        last = Fraction(p['C66'])
    elif kind == 'tetragonal_ii':
        last = p['C66'] * (a - b) - 2 * p['C16'] ** 2
    elif kind == 'rhombohedral_i':
        last = e * (a - b) - 2 * p['C14'] ** 2
    else:
        last = e * (a - b) - 2 * (p['C14'] ** 2 + p['C15'] ** 2)
    return (a - abs(b), d * (a + b) - 2 * c * c, e, last)


def expected_leading_minors(kind, p):
    a, b, c, d, e = (Fraction(p[name]) for name in ('C11', 'C12', 'C13', 'C33', 'C44'))
    u, v = a + b, a - b
    n = d * u - 2 * c * c
    if kind == 'tetragonal_i':
        tail = (e * v * n, e * e * v * n, e * e * p['C66'] * v * n)
    elif kind == 'tetragonal_ii':
        tail = (e * v * n, e * e * v * n, e * e * n * (p['C66'] * v - 2 * p['C16'] ** 2))
    else:
        r = p['C14'] ** 2 + (p['C15'] ** 2 if kind == 'rhombohedral_ii' else 0)
        k = e * v - 2 * r
        tail = (n * (e * v - 2 * p['C14'] ** 2), e * n * k, n * k * k / 2)
    return (a, v * u, v * n, *tail)


def characteristic_factorization(kind, p, value):
    a, b, c, d, e = (Fraction(p[name]) for name in ('C11', 'C12', 'C13', 'C33', 'C44'))
    v, u = a - b, a + b
    normal = (u - value) * (d - value) - 2 * c * c
    if kind == 'tetragonal_i':
        return normal * (v - value) * (e - value) ** 2 * (p['C66'] - value)
    if kind == 'tetragonal_ii':
        return normal * ((v - value) * (p['C66'] - value) - 2 * p['C16'] ** 2) * (e - value) ** 2
    r = p['C14'] ** 2 + (p['C15'] ** 2 if kind == 'rhombohedral_ii' else 0)
    return normal * ((v - value) * (e - value) - 2 * r) * ((v / 2 - value) * (e - value) - r)


def shifted(matrix, value):
    return [[entry - (value if i == j else 0) for j, entry in enumerate(row)]
            for i, row in enumerate(matrix)]


def energy(matrix, strain):
    return sum(strain[i] * matrix[i][j] * strain[j] for i in range(6) for j in range(6)) / 2


def rotate_strain(strain, rotation):
    """Tensor rotation independently preserves engineering shear factors."""
    x, y, z, yz, xz, xy = strain
    tensor = [[x, xy / 2, xz / 2], [xy / 2, y, yz / 2], [xz / 2, yz / 2, z]]
    rotated = [[sum(rotation[i][k] * tensor[k][l] * rotation[j][l]
                    for k in range(3) for l in range(3))
                for j in range(3)] for i in range(3)]
    return [rotated[0][0], rotated[1][1], rotated[2][2],
            2 * rotated[1][2], 2 * rotated[0][2], 2 * rotated[0][1]]


class CrystalStabilityCatalogTests(unittest.TestCase):
    def test_historical_science_and_crystal_ids_are_preserved(self):
        prior_ids = EXECUTABLE_IDS + GRIFFITH_IDS + MECHANICS_IDS + CORE_STABILITY_IDS + POROUS_IDS
        self.assertEqual(scientific_digest(historical_records('claims', prior_ids)),
                         '457c411b56a6bb4ce8a1ac46c7874de2bd2a42cfc7da30b8094546b2d855d841')
        self.assertEqual(tuple(c['id'] for c in records()), IDS)
        # Bibliography and observation science stay anchored by ID, without
        # freezing future records or evidence. Provenance has its own fixture.
        bibliography = [{key: record[key] for key in ('id', 'title', 'authors', 'year', 'doi')}
                        for record in historical_records('sources', HISTORICAL_SOURCE_IDS)]
        self.assertEqual(scientific_digest(bibliography),
                         '83aa9e36c344bac2065b7ba504f1d39fba1a0ad5c437c0083031f2dab276e5b7')
        self.assertEqual(scientific_digest(historical_records('observations', OBSERVATION_IDS)),
                         '6816435e75502b64f31676ca8b06e67a4c5cd8e34d3f27c21eb78b3c313a8168')

    def test_exact_templates_independent_parameter_sets_and_coupling_signs(self):
        for kind, record in zip(KINDS, records()):
            with self.subTest(kind=kind):
                self.assertEqual(record['required_assumptions']['elastic_symmetry'], kind)
                self.assertEqual(record['criterion']['stiffness_matrix'], MATRICES[kind])
                self.assertEqual(set(p['symbol'] for p in record['parameters']), set(SYMBOLS[kind]))
                self.assertEqual(len(record['parameters']), len(SYMBOLS[kind]))
                self.assertTrue(all((p['quantity'], p['dimension'], p['si_unit']) ==
                                    ('elastic_stiffness_component', 'pressure', 'Pa')
                                    for p in record['parameters']))

    def test_four_joint_strict_conditions_have_exact_expressions_and_dimensions(self):
        for index, record in enumerate(records()):
            expected = ['C11-abs(C12)', 'C33*(C11+C12)-2*C13^2', 'C44', LAST_EXPRESSIONS[index]]
            found = {item['expression']: item for item in record['criterion']['inequalities']}
            self.assertEqual(set(found), set(expected))
            self.assertEqual(len(record['criterion']['inequalities']), 4)
            for pos, expression in enumerate(expected):
                squared = pos == 1 or (pos == 3 and index != 0)
                self.assertEqual(found[expression], {
                    'expression': expression, 'operator': '>', 'rhs': 0,
                    'dimension': 'pressure_squared' if squared else 'pressure',
                    'si_unit': 'Pa^2' if squared else 'Pa',
                })
            self.assertEqual(record['criterion']['combination'], 'all')
            self.assertEqual(record['criterion']['strict_boundary'], 'equality_does_not_satisfy_strict_stability')

    def test_source_locators_and_unreviewed_display_only_scope(self):
        for record, matrix_eq, criterion_eq in zip(records(), (7, 10, 12, 14), (9, 11, 13, 15)):
            self.assertEqual(record['claim_type'], 'stability_criterion')
            self.assertEqual(record['quantity'], 'homogeneous_elastic_stability')
            self.assertEqual((record['direction'], record['evaluation_support']), ('constraint', 'catalog_only'))
            self.assertEqual((record['quantity_dimension'], record['si_unit']), ('logical_predicate', None))
            self.assertIsNone(record['bound_kind'])
            self.assertEqual(record['dependencies'], [])
            self.assertIn(SOURCE, {item['source_id'] for item in record['evidence']})
            self.assertIn(f'({matrix_eq})', evidence_for(record, SOURCE)['locator'])
            self.assertIn(f'({criterion_eq})', evidence_for(record, SOURCE)['locator'])
            self.assertEqual(record['verification']['status'], expected_provenance('claims', record['id'])['verification']['status'])
            self.assertEqual(record['verification']['independent_scientific_review'], expected_provenance('claims', record['id'])['verification']['independent_scientific_review'])
            text = ' '.join(record['limits'])
            for token in ('stress-free', 'homogeneous', 'harmonic', 'strict', 'positive-semidefinite',
                          'negative eigenvalue', 'higher-order', 'near-zero', 'finite external load',
                          'phonon', 'finite strain', '2D', 'plane-stress', 'display metadata only'):
                self.assertIn(token, text)
            for forbidden in ('result', 'value', 'checks', 'computation', 'applicability'):
                self.assertNotIn(forbidden, record)

    def test_right_handed_cartesian_axes_and_voigt_convention_are_explicit(self):
        for kind, record in zip(KINDS, records()):
            assumptions = record['required_assumptions']
            for name, expected in {'spatial_dimension': 3, 'reference_state': 'stress_free_equilibrium',
                                   'strain_regime': 'infinitesimal', 'energy_approximation': 'harmonic_quadratic',
                                   'perturbation_class': 'homogeneous_strain',
                                   'stiffness_symmetry': 'real_symmetric_6_by_6',
                                   'stiffness_convention': 'engineering_voigt',
                                   'axes': 'aligned_with_declared_symmetry_template',
                                   'stiffness_units': 'common_pressure_unit'}.items():
                self.assertEqual(assumptions[name], expected)
            criterion = record['criterion']
            self.assertEqual(criterion['voigt_order'], ['xx', 'yy', 'zz', 'yz', 'xz', 'xy'])
            self.assertEqual(criterion['strain_vector'], 'e=(epsilon_xx,epsilon_yy,epsilon_zz,2*epsilon_yz,2*epsilon_xz,2*epsilon_xy)')
            self.assertEqual(criterion['stress_vector'], 's=(sigma_xx,sigma_yy,sigma_zz,sigma_yz,sigma_xz,sigma_xy)')
            self.assertEqual(criterion['energy_density'], 'delta_u=(1/2)*e^T*C*e')
            self.assertEqual(criterion['constitutive_relation'], 's=C*e')
            text = ' '.join(record['limits'])
            self.assertIn('right-handed orthonormal Cartesian', text)
            self.assertIn('fourfold' if kind.startswith('tetragonal') else 'threefold', text)
            self.assertIn('Laue', text)
            self.assertIn('transform', text)

    def test_four_language_labels_and_catalog_filters_preserve_new_records(self):
        for record in records():
            self.assertEqual(query_catalog('claims', record_id=record['id'], direction='upper')['records'], [])
            for lang in LANGUAGES:
                label = translate('catalog_name_' + record['id'], lang)
                self.assertFalse(label.startswith('[missing:'))
                self.assertIn(record['id'], [c['id'] for c in query_catalog('claims', query=label)['records']])
                text = render_catalog({'records': [record]}, 'claims', lang)
                self.assertIn(label, text)
                self.assertIn(translate('catalog_criterion_notice', lang), text)
                self.assertIn(translate('catalog_stiffness_matrix', lang), text)
                self.assertIn(translate('catalog_not_applicable', lang), text)
                self.assertNotIn('[missing:', text)

    def test_poisoned_new_formulas_never_execute_or_enter_comparison(self):
        baseline = evaluate(example())
        catalog = read_catalog('claims')
        for record in select_records(catalog, IDS):
            record.update(rule_id='never_dispatch_crystal', formula_display='never_execute_crystal()',
                          quantity='poisoned_crystal_quantity')
            record['criterion'] = {'poisoned_crystal_matrix': True}
            record['evidence'] = [{'source_id': 'never_join_crystal_source'}]
        with patch('materials_boundaries.catalog.read_catalog', side_effect=AssertionError('catalog execution')):
            self.assertEqual(evaluate(example()), baseline)
        original = read_catalog
        with patch('materials_boundaries.visualization.read_catalog',
                   side_effect=lambda name: catalog if name == 'claims' else original(name)):
            bundle = build_comparison([example()], fractions=[0, .5, 1])
        self.assertEqual(len(bundle['series']), 8)
        self.assertEqual(len(bundle['catalogs']['claims']['records']), 8)
        output = json.dumps(bundle) + render_html(bundle) + render_svg(bundle, bundle['cases'][0]['id'])
        for token in (*IDS, 'never_dispatch_crystal', 'never_execute_crystal', 'poisoned_crystal', 'never_join_crystal'):
            self.assertNotIn(token, output)


class CrystalStabilityArithmeticTests(unittest.TestCase):
    def test_exact_determinant_helper_handles_swaps_and_singular_matrices(self):
        self.assertEqual(determinant([[0, 2], [3, 4]]), -6)
        self.assertEqual(determinant([[1, 2], [2, 4]]), 0)
        self.assertEqual(determinant([[Fraction(1, 2), 1], [1, 3]]), Fraction(1, 2))

    def test_synthetic_fixture_scope_inputs_and_exact_margins(self):
        fixture = load_json(ROOT / 'examples/catalog/crystal-stability-synthetic.json')
        self.assertEqual(fixture['kind'], 'synthetic_test_fixtures_not_material_observations')
        self.assertEqual(fixture['stiffness_unit'], 'GPa')
        self.assertEqual(len(fixture['fixtures']), 16)
        for case in fixtures():
            with self.subTest(case=case['id']):
                self.assertEqual(set(case['input']), set(SYMBOLS[case['symmetry']]))
                matrix = stiffness(case['symmetry'], case['input'])
                result = margins(case['symmetry'], case['input'])
                self.assertEqual(list(result), case['expected_margins'])
                self.assertEqual(all(value > 0 for value in result), case['classification'] == 'strictly_positive_definite')
                self.assertEqual(leading_minors(matrix), expected_leading_minors(case['symmetry'], case['input']))

    def test_exact_psd_zero_modes_and_zero_plus_negative_are_distinct(self):
        for case in fixtures():
            if 'exact_eigenvalues' not in case:
                continue
            with self.subTest(case=case['id']):
                matrix = stiffness(case['symmetry'], case['input'])
                roots = case['exact_eigenvalues']
                self.assertEqual(len(roots), 6)
                # Equal degree-six characteristic polynomials at seven distinct
                # rational values prove these spectra, including multiplicities.
                for value in (-3, -1, 0, 1, 2, 7, 11):
                    expected = math.prod(Fraction(root) - value for root in roots)
                    self.assertEqual(determinant(shifted(matrix, value)), expected)
                self.assertEqual(determinant(matrix), 0)
                self.assertFalse(all(value > 0 for value in margins(case['symmetry'], case['input'])))
                all_minors = principal_minors(matrix)
                if case['classification'] == 'positive_semidefinite_with_zero_modes':
                    self.assertTrue(all(value >= 0 for value in all_minors))
                    self.assertEqual(min(roots), 0)
                else:
                    self.assertEqual(case['classification'], 'zero_and_negative_modes')
                    self.assertLess(min(all_minors), 0)
                    self.assertIn(-1, roots)
                    self.assertIn(0, roots)

    def test_tetragonal_c66_is_independent_and_positivity_alone_does_not_control_c16(self):
        p = dict(C11=150, C12=50, C13=40, C33=180, C44=60, C66=35)
        self.assertNotEqual(p['C66'], (p['C11'] - p['C12']) / 2)
        self.assertTrue(all(value > 0 for value in leading_minors(stiffness('tetragonal_i', p))))
        p['C66'] = -1
        self.assertLess(margins('tetragonal_i', p)[-1], 0)
        self.assertLess(determinant(stiffness('tetragonal_i', p)), 0)
        p.update(C66=35, C16=50)
        self.assertGreater(p['C66'], 0)
        self.assertLess(margins('tetragonal_ii', p)[-1], 0)
        self.assertLess(determinant(stiffness('tetragonal_ii', p)), 0)

    def test_factor_two_cannot_be_dropped_from_normal_or_coupled_conditions(self):
        for kind in KINDS:
            p = dict(zip(SYMBOLS[kind], [6, 2, 4, 3, 2] + ([2, 0] if kind == 'tetragonal_ii' else [0, 0] if kind == 'rhombohedral_ii' else [2])))
            self.assertGreater(p['C33'] * (p['C11'] + p['C12']) - p['C13'] ** 2, 0)
            self.assertEqual(margins(kind, p)[1], -8)
            self.assertLess(leading_minors(stiffness(kind, p))[2], 0)
        for kind, coupling in [('tetragonal_ii', 'C16'), ('rhombohedral_i', 'C14'), ('rhombohedral_ii', 'C14')]:
            p = dict(C11=6, C12=2, C13=0, C33=3, C44=3, C66=3, C14=0, C15=0, C16=0)
            p[coupling] = 3
            self.assertEqual(3 * (p['C11'] - p['C12']) - p[coupling] ** 2, 3)
            self.assertEqual(margins(kind, p)[-1], -6)
            self.assertFalse(all(value > 0 for value in leading_minors(stiffness(kind, p))))

    def test_rhombohedral_ii_requires_sum_of_both_squared_couplings(self):
        p = dict(C11=150, C12=50, C13=40, C33=180, C44=60, C14=40, C15=40)
        limit = Fraction(p['C44'] * (p['C11'] - p['C12']), 2)
        self.assertEqual(limit, 3000)
        self.assertLess(p['C14'] ** 2, limit)
        self.assertLess(p['C15'] ** 2, limit)
        self.assertGreater(p['C14'] ** 2 + p['C15'] ** 2, limit)
        self.assertEqual(margins('rhombohedral_ii', p)[-1], -400)
        self.assertFalse(all(value > 0 for value in leading_minors(stiffness('rhombohedral_ii', p))))

    def test_positive_determinant_can_hide_two_negative_modes_in_every_class(self):
        # Both C44 and C55 are negative, so a positive determinant is insufficient.
        for kind in KINDS:
            p = dict(C11=6, C12=2, C13=0, C33=3, C44=-2, C66=2, C14=0, C15=0, C16=0)
            matrix = stiffness(kind, p)
            self.assertGreater(determinant(matrix), 0)
            self.assertLess(energy(matrix, [0, 0, 0, 1, 0, 0]), 0)
            self.assertLess(energy(matrix, [0, 0, 0, 0, 1, 0]), 0)
            self.assertFalse(all(value > 0 for value in margins(kind, p)))
        # With all diagonals positive, the squared rhombohedral coupling margin
        # also conceals two negative eigenvalues in a positive determinant.
        for kind, p in [('rhombohedral_i', dict(C11=150, C12=50, C13=40, C33=180, C44=60, C14=60)),
                        ('rhombohedral_ii', dict(C11=150, C12=50, C13=40, C33=180, C44=60, C14=40, C15=40))]:
            matrix = stiffness(kind, p)
            self.assertTrue(all(matrix[i][i] > 0 for i in range(6)))
            self.assertGreater(determinant(matrix), 0)
            self.assertLess(leading_minors(matrix)[4], 0)
            self.assertLess(margins(kind, p)[-1], 0)

    def test_random_exact_matrix_minors_match_predicates_without_float_tolerance(self):
        rng = random.Random(8041226)
        for kind in KINDS:
            pd_count = 0
            for sample in range(256):
                p = {name: rng.randint(-8, 8) for name in SYMBOLS[kind]}
                if sample >= 64:
                    for name in ('C11', 'C33', 'C44', 'C66'):
                        if name in p:
                            p[name] = rng.randint(1, 15)
                if sample >= 128:
                    for name in p:
                        p[name] = rng.randint(10, 20) if name in ('C11', 'C33', 'C44', 'C66') else rng.randint(-2, 2)
                with self.subTest(kind=kind, sample=sample):
                    matrix_minors = leading_minors(stiffness(kind, p))
                    self.assertEqual(matrix_minors, expected_leading_minors(kind, p))
                    predicate = all(value > 0 for value in margins(kind, p))
                    self.assertEqual(predicate, all(value > 0 for value in matrix_minors))
                    pd_count += predicate
            self.assertGreater(pd_count, 0)
            self.assertLess(pd_count, 256)

    def test_full_characteristic_factorizations_include_all_shear_couplings(self):
        for case in fixtures():
            matrix = stiffness(case['symmetry'], case['input'])
            for value in (-5, -2, 0, 1, 3, 7, 13):
                with self.subTest(case=case['id'], value=value):
                    self.assertEqual(determinant(shifted(matrix, value)),
                                     characteristic_factorization(case['symmetry'], case['input'], value))

    def test_engineering_shear_rotation_energy_matches_declared_symmetry_axes(self):
        z_fourfold = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
        z_threefold = [[-.5, -math.sqrt(3) / 2, 0], [math.sqrt(3) / 2, -.5, 0], [0, 0, 1]]
        x_twofold = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]
        strains = [[Fraction(i == j) for i in range(6)] for j in range(6)]
        strains += [[Fraction(k in (i, j)) for k in range(6)] for i, j in combinations(range(6), 2)]
        for case in (case for case in fixtures() if case['classification'] == 'strictly_positive_definite'):
            kind = case['symmetry']
            matrix = stiffness(kind, case['input'])
            rotation = z_fourfold if kind.startswith('tetragonal') else z_threefold
            for strain in strains:
                with self.subTest(kind=kind, strain=strain):
                    self.assertAlmostEqual(float(energy(matrix, strain)),
                                           float(energy(matrix, rotate_strain(strain, rotation))), places=10)
            differences = [energy(matrix, strain) - energy(matrix, rotate_strain(strain, x_twofold)) for strain in strains]
            self.assertEqual(all(value == 0 for value in differences), kind.endswith('_i'))
            self.assertEqual(energy(matrix, [0, 0, 0, 1, 0, 0]), Fraction(case['input']['C44'], 2))


@unittest.skipIf(Draft202012Validator is None, 'optional jsonschema dev dependency not installed')
class CrystalStabilitySchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = read_catalog('claims')
        cls.validator = Draft202012Validator(load_json(ROOT / 'schemas/claims.schema.json'))

    def invalid(self, record_id, mutation):
        # Validate one complete record envelope to avoid retesting unrelated
        # records for every mutation, with the identical production schema.
        record = copy.deepcopy(select_records(self.catalog, [record_id])[0])
        mutation(record)
        invalid = {'schema_version': self.catalog['schema_version'], 'records': [record]}
        self.assertTrue(list(self.validator.iter_errors(invalid)), record)

    def test_schema_accepts_catalog_and_all_inequality_and_parameter_orderings(self):
        self.validator.check_schema(self.validator.schema)
        self.validator.validate(self.catalog)
        rng = random.Random(107)
        for _ in range(12):
            reordered = copy.deepcopy(self.catalog)
            for record in select_records(reordered, IDS):
                rng.shuffle(record['parameters'])
                rng.shuffle(record['criterion']['inequalities'])
            self.validator.validate(reordered)
        for old_version in ('1.5.0', '1.4.0'):
            old = copy.deepcopy(self.catalog)
            old['schema_version'] = old_version
            self.assertTrue(list(self.validator.iter_errors(old)))

    def test_wrong_missing_and_duplicate_independent_parameters_fail_closed(self):
        for index in IDS:
            for mutation in (lambda r: r.pop('parameters'),
                             lambda r: r['parameters'].pop(),
                             lambda r: r['parameters'].append(copy.deepcopy(r['parameters'][0])),
                             lambda r: r['parameters'][0].update(symbol='C99'),
                             lambda r: r['parameters'][0].update(quantity='strength'),
                             lambda r: r['parameters'][0].update(dimension='dimensionless'),
                             lambda r: r['parameters'][0].update(si_unit='GPa')):
                with self.subTest(index=index, mutation=mutation):
                    self.invalid(index, mutation)
        for index in IDS[2:]:
            self.invalid(index, lambda r: r['parameters'][-1].update(symbol='C66'))
        self.invalid(IDS[0], lambda r: r['parameters'][-1].update(symbol='C14'))
        self.invalid(IDS[1], lambda r: r['parameters'][-1].update(symbol='C15'))

    def test_all_matrix_entries_dimensions_symmetry_and_signs_are_locked(self):
        for index in IDS:
            self.invalid(index, lambda r: r['criterion'].pop('stiffness_matrix'))
            self.invalid(index, lambda r: r['criterion']['stiffness_matrix'].pop())
            self.invalid(index, lambda r: r['criterion']['stiffness_matrix'][0].append('0'))
            self.invalid(index, lambda r: r['criterion']['stiffness_matrix'][0].__setitem__(0, 'C22'))
            self.invalid(index, lambda r: r['criterion']['stiffness_matrix'][0].__setitem__(2, '0'))
            self.invalid(index, lambda r: r['criterion']['stiffness_matrix'][4].__setitem__(4, 'C55'))
        for index in IDS[:2]:
            self.invalid(index, lambda r: r['criterion']['stiffness_matrix'][5].__setitem__(5, '(C11-C12)/2'))
        for index in IDS[2:]:
            self.invalid(index, lambda r: r['criterion']['stiffness_matrix'][5].__setitem__(5, 'C66'))
            self.invalid(index, lambda r: r['criterion']['stiffness_matrix'][1].__setitem__(3, 'C14'))
            self.invalid(index, lambda r: r['criterion']['stiffness_matrix'][4].__setitem__(5, '-C14'))
        self.invalid(IDS[1], lambda r: r['criterion']['stiffness_matrix'][1].__setitem__(5, 'C16'))
        self.invalid(IDS[3], lambda r: r['criterion']['stiffness_matrix'][1].__setitem__(4, 'C15'))
        self.invalid(IDS[3], lambda r: r['criterion']['stiffness_matrix'][3].__setitem__(5, 'C15'))

    def test_inequality_strictness_dimensions_and_full_combined_terms_fail_closed(self):
        for index in IDS:
            for pos in range(4):
                for key, value in [('operator', '>='), ('rhs', 1), ('dimension', 'dimensionless'), ('si_unit', '1')]:
                    with self.subTest(index=index, pos=pos, key=key):
                        self.invalid(index, lambda r: r['criterion']['inequalities'][pos].update({key: value}))
            self.invalid(index, lambda r: r['criterion']['inequalities'].pop())
            self.invalid(index, lambda r: r['criterion']['inequalities'].append(copy.deepcopy(r['criterion']['inequalities'][0])))
            self.invalid(index, lambda r: r['criterion']['inequalities'].__setitem__(3, copy.deepcopy(r['criterion']['inequalities'][2])))
            self.invalid(index, lambda r: r['criterion']['inequalities'][1].update(expression='C33*(C11+C12)-C13^2'))
            self.invalid(index, lambda r: r['criterion']['inequalities'][0].update(expression='C11-C12'))
        self.invalid(IDS[1], lambda r: r['criterion']['inequalities'][3].update(expression='C66*(C11-C12)-C16^2'))
        self.invalid(IDS[2], lambda r: r['criterion']['inequalities'][3].update(expression='C44*(C11-C12)-C14^2'))
        self.invalid(IDS[3], lambda r: r['criterion']['inequalities'][3].update(expression='C44*(C11-C12)-2*C14^2'))
        self.invalid(IDS[3], lambda r: r['criterion']['inequalities'][3].update(expression='C44*(C11-C12)-2*C15^2'))

    def test_scope_conventions_and_catalog_only_classification_cannot_be_weakened(self):
        for index in IDS:
            for key, value in [('spatial_dimension', 2), ('reference_state', 'loaded'), ('strain_regime', 'finite'),
                               ('energy_approximation', 'higher_order'), ('perturbation_class', 'phonon'),
                               ('stiffness_convention', 'Mandel'), ('stiffness_units', 'mixed'),
                               ('stiffness_symmetry', 'general'), ('axes', 'unknown'), ('elastic_symmetry', 'unknown')]:
                self.invalid(index, lambda r: r['required_assumptions'].update({key: value}))
                self.invalid(index, lambda r: r['required_assumptions'].pop(key))
            for key, value in [('combination', 'any'), ('strict_boundary', 'equality_is_stable'),
                               ('strain_vector', 'tensor_shears'), ('stress_vector', 'doubled_stress_shears'),
                               ('energy_density', 'e^T*C*e'), ('voigt_order', ['xx', 'yy', 'zz', 'xy', 'yz', 'xz'])]:
                self.invalid(index, lambda r: r['criterion'].update({key: value}))
            for key, value in [('claim_type', 'theoretical_bound'), ('claim_type', 'model_relation'),
                               ('direction', 'upper'), ('bound_kind', 'scalar_modulus_bound'),
                               ('evaluation_support', 'composite_evaluate'), ('dependencies', ['hs_bulk_3d_two_phase']),
                               ('quantity_dimension', 'pressure'), ('si_unit', 'Pa'), ('si_unit', '1'),
                               ('quantity', 'effective_bulk_modulus'), ('result', True), ('applicability', 'satisfied')]:
                self.invalid(index, lambda r: r.update({key: value}))
            other_kind = KINDS[(IDS.index(index) + 1) % len(KINDS)]
            self.invalid(index, lambda r: r['required_assumptions'].update(elastic_symmetry=other_kind))


if __name__ == '__main__':
    unittest.main()
