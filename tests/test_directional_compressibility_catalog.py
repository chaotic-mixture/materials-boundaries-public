from provenance_corrections import public_previous_record
"""Hydrostatic catalog contracts and exact, test-only project algebra.

Finite rational examples corroborate the symbolic proofs in the documentation;
they are not material predictions or independent scientific peer review. Nothing
in this module is installed as a tensor-input, inversion, or numerical API.
"""
import copy
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from materials_boundaries import evaluate, load_json
from materials_boundaries._compressibility_contract import (
    COMPRESSIBILITY_CONTRACTS, DEFINITION_RULE, RANGE_RULE,
    validate_compressibility_records,
)
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs
from catalog_fixtures import EXECUTABLE_IDS
from test_engine import ROOT, example

IDS = ('directional_linear_compressibility_hydrostatic_relation',
       'normalized_directional_compressibility_range')
RULES = tuple(identifier + '_v1' for identifier in IDS)
LABELS = tuple('catalog_compressibility_' + suffix for suffix in (
    'notice', 'conditions', 'limits', 'fixed_tensor', 'range', 'energy', 'symmetry'))
CONTRACT = 'hydrostatic_compressibility_contract'
CURATION_FIELDS = {'evidence', 'verification', 'provenance', 'claim_notes', 'urls'}
CLOSED_FIELDS = ('quantity', 'direction', 'claim_type', 'bound_kind',
                 'quantity_dimension', 'si_unit', 'evaluation_support',
                 'formula_display', 'required_assumptions', 'parameters', CONTRACT)
DERIVATION_STATUS = 'original_project_algebra_not_independent_scientific_peer_review'
# Immutable independent digests of the source-only 2026-10-02 research metadata.
# This projected snapshot excludes later closed scope/source-attribution fields.
RESEARCH_SCIENCE_DIGESTS = {'directional_linear_compressibility_hydrostatic_relation': '4bf9fa5fe967feb071badcf86df74174bee15a8d5fc1031b30ee089d0e5b786d', 'normalized_directional_compressibility_range': '415e7ef725954d666744166b6d2011ac1c9ce8579408608c8b3e01bd4b3ac1e4'}
VOIGT = ((0, 0), (1, 1), (2, 2), (1, 2), (0, 2), (0, 1))
SHEAR_FACTORS = (1, 1, 1, 2, 2, 2)
H = (F(1), F(1), F(1), F(0), F(0), F(0))
DIRECTIONS = ((F(1), F(0), F(0)), (F(0), F(1), F(0)),
              (F(0), F(0), F(1)), (F(3, 5), F(4, 5), F(0)),
              (F(1, 3), F(2, 3), F(2, 3)))


def records(catalogs=None):
    catalog = read_catalog('claims') if catalogs is None else catalogs['claims']
    by_id = {record['id']: record for record in catalog['records']}
    return [by_id[identifier] for identifier in IDS]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def compliance_triplet(r, s0=F(1), t=F(1)):
    """Test-only exact rr^T + tP family, with a strictly positive shear block."""
    r = tuple(map(F, r)); s0, t = F(s0), F(t)
    if sum(r) != 1 or s0 <= 0 or t <= 0:
        raise ValueError('unit-sum triplet and positive scales required')
    result = [[F(0) for _ in range(6)] for _ in range(6)]
    for i in range(3):
        for j in range(3):
            result[i][j] = s0 * (r[i]*r[j] + t*(int(i == j)-F(1, 3)))
        result[i+3][i+3] = s0
    return result


def compliance(q, s0=F(1), t=F(1)):
    q = F(q)
    return compliance_triplet((q, (1-q)/2, (1-q)/2), s0, t)


def bilinear(x, s, y):
    return sum(x[i]*s[i][j]*y[j] for i in range(len(x)) for j in range(len(y)))


def dyad(n):
    return (n[0]**2, n[1]**2, n[2]**2, n[1]*n[2], n[0]*n[2], n[0]*n[1])


def matmul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def transpose(a):
    return list(map(list, zip(*a)))


def inverse(a):
    """Exact test fixture inversion; deliberately not imported from production."""
    n = len(a)
    augmented = [[F(x) for x in row] + [F(i == j) for j in range(n)]
                 for i, row in enumerate(a)]
    for col in range(n):
        pivot = augmented[col][col]
        if not pivot:
            raise ValueError('test fixture has a zero pivot')
        augmented[col] = [x/pivot for x in augmented[col]]
        for row in range(n):
            if row != col:
                scale = augmented[row][col]
                augmented[row] = [x-scale*y for x, y in zip(augmented[row], augmented[col])]
    return [row[n:] for row in augmented]


def ldl_pivots(a):
    """Rational Schur pivots prove SPD for each finite fixture, with no tolerance."""
    work = copy.deepcopy(a); pivots = []
    for k in range(len(work)):
        pivots.append(work[k][k])
        for i in range(k+1, len(work)):
            for j in range(k+1, len(work)):
                work[i][j] -= work[i][k]*work[k][j]/pivots[-1]
    return pivots


def tensor_from_engineering(s):
    raw = {}
    for a, (i, j) in enumerate(VOIGT):
        for b, (k, l) in enumerate(VOIGT):
            value = s[a][b]/(SHEAR_FACTORS[a]*SHEAR_FACTORS[b])
            for ii, jj in {(i, j), (j, i)}:
                for kk, ll in {(k, l), (l, k)}:
                    raw[ii, jj, kk, ll] = value
    return raw


def engineering_from_tensor(raw):
    return [[SHEAR_FACTORS[a]*SHEAR_FACTORS[b]*raw[i, j, k, l]
             for b, (k, l) in enumerate(VOIGT)] for a, (i, j) in enumerate(VOIGT)]


def rotated_tensor(raw, rotation):
    indices = tuple(itertools.product(range(3), repeat=4))
    return {(i, j, k, l): sum(rotation[i][a]*rotation[j][b]*rotation[k][c]*rotation[l][d]
                              * raw[a, b, c, d] for a, b, c, d in indices)
            for i, j, k, l in indices}


def scientific_mutations(value, path=()):
    """Visit every scientific node: omission, foreign keys, values and types."""
    if isinstance(value, dict):
        yield path, 'extra', ('unsupported_science', True)
        yield path, 'replace', []
        for key, child in value.items():
            yield path + (key,), 'delete', None
            yield from scientific_mutations(child, path + (key,))
    elif isinstance(value, list):
        yield path, 'replace', {}
        yield path, 'append', '__unsupported__'
        for i, child in enumerate(value):
            yield path + (i,), 'delete', None
            yield from scientific_mutations(child, path + (i,))
    elif isinstance(value, bool):
        yield path, 'replace', not value
        yield path, 'replace', int(value)  # Python's True == 1 must not weaken JSON.
    elif isinstance(value, str):
        yield path, 'replace', value + '__weakened__'
        yield path, 'replace', 1
    elif value is None:
        yield path, 'replace', 'not_null'
        yield path, 'replace', False
    else:
        yield path, 'replace', value + 1
        yield path, 'replace', str(value)


def apply_mutation(record, path, operation, value):
    if operation in {'extra', 'append'}:
        target = record
        for component in path:
            target = target[component]
        if operation == 'extra':
            target[value[0]] = value[1]
        else:
            target.append(value)
    else:
        target = record
        for component in path[:-1]:
            target = target[component]
        if operation == 'delete':
            del target[path[-1]]
        else:
            target[path[-1]] = value


class CompressibilityAlgebraTests(unittest.TestCase):
    def test_all_finite_rational_targets_fixed_kappa_full_spd_and_inverse(self):
        for q in map(F, (-10**12, -2, -1, 0, '1/3', '1/2', 1, 2, 10**12)):
            for s0 in (F(1, 10**12), F(1), F(10**9)):
                for t in (F(1, 10), F(1), F(3)):
                    with self.subTest(q=q, s0=s0, t=t):
                        s = compliance(q, s0, t)
                        pivots = ldl_pivots(s)
                        self.assertTrue(all(p > 0 for p in pivots))
                        self.assertEqual(pivots[0]*pivots[1]*pivots[2], s0**3*t*t/3)
                        self.assertEqual(matmul(s, inverse(s)),
                                         [[int(i == j) for j in range(6)] for i in range(6)])
                        kappa = bilinear(H, s, H)
                        self.assertEqual(kappa, s0)
                        self.assertEqual(bilinear(dyad(DIRECTIONS[0]), s, H)/kappa, q)
                        self.assertEqual(s[0][0]/s0-q*q, 2*t/3)
                        r = (q, (1-q)/2, (1-q)/2)
                        for x in ((1, 2, 3, 4, 5, 6), H, (0, 0, 0, 1, 0, 0)):
                            mean = sum(x[:3])/F(3)
                            form = s0*(sum(r[i]*x[i] for i in range(3))**2
                                       + t*sum((x[i]-mean)**2 for i in range(3))
                                       + sum(z*z for z in x[3:]))
                            self.assertEqual(bilinear(x, s, x), form)
                            self.assertGreater(form, 0)

    def test_zero_two_negative_and_two_zero_principal_responses_are_full_spd(self):
        for r, negatives, zeros in (((F(0), F(1, 2), F(1, 2)), 0, 1),
                                    ((F(-1), F(-1), F(3)), 2, 0),
                                    ((F(1), F(0), F(0)), 0, 2)):
            s = compliance_triplet(r)
            self.assertTrue(all(p > 0 for p in ldl_pivots(s)))
            betas = [bilinear(dyad(n), s, H) for n in DIRECTIONS[:3]]
            self.assertEqual(betas, list(r)); self.assertEqual(sum(betas), 1)
            self.assertEqual(sum(beta < 0 for beta in betas), negatives)
            self.assertEqual(sum(beta == 0 for beta in betas), zeros)
            self.assertGreater(max(betas), 0)
            self.assertLessEqual(min(betas), F(1, 3)); self.assertGreaterEqual(max(betas), F(1, 3))
        # A principal-value count is not a count of all negative directions.
        s = compliance(-1)
        self.assertTrue(all(bilinear(dyad(n), s, H) < 0 for n in (
            (F(1), 0, 0), (F(4, 5), F(3, 5), 0), (F(4, 5), -F(3, 5), 0),
            (F(4, 5), 0, F(3, 5)), (F(4, 5), 0, -F(3, 5)))))

    def test_same_tensor_strict_energy_and_necessary_not_sufficient(self):
        for q in map(F, (-10**9, -1, 0, '1/3', 1, 10**9)):
            s = compliance(q, F(2, 7), F(1, 10)); kappa = bilinear(H, s, H)
            for n in DIRECTIONS:
                self.assertEqual(sum(x*x for x in n), 1)
                v = dyad(n); beta = bilinear(v, s, H); young = 1/bilinear(v, s, v)
                self.assertGreater(young, 0)
                self.assertLess(beta*beta, kappa/young)
                self.assertLess((beta/kappa)**2, 1/(kappa*young))
        # Substitution of an unrelated modulus invalidates the same-S inequality.
        s = compliance(2); beta = bilinear(dyad(DIRECTIONS[0]), s, H)
        self.assertGreater(beta*beta, bilinear(H, s, H)/F(10))
        # A necessary direction-wise check is not a full six-dimensional SPD test.
        bad = compliance(0); bad[3][3] = -1
        for n in DIRECTIONS[:3]:
            v = dyad(n)
            self.assertLess(bilinear(v, bad, H)**2, bilinear(H, bad, H)*bilinear(v, bad, v))
        self.assertLess(bilinear((0, 0, 0, 1, 0, 0), bad, (0, 0, 0, 1, 0, 0)), 0)
        # Equality occurs only after leaving full SPD in this singular limit.
        singular = [[F(1, 9) if i < 3 and j < 3 else F(i == j)
                     for j in range(6)] for i in range(6)]
        self.assertEqual(bilinear(dyad(DIRECTIONS[0]), singular, H)**2,
                         bilinear(H, singular, H)*singular[0][0])
        self.assertEqual(bilinear((1, -1, 0, 0, 0, 0), singular, (1, -1, 0, 0, 0, 0)), 0)

    def test_full_fourth_order_rotation_and_engineering_hydrostatic_shear_mapping(self):
        rz = [[F(3, 5), -F(4, 5), 0], [F(4, 5), F(3, 5), 0], [0, 0, F(1)]]
        rx = [[F(1), 0, 0], [0, F(5, 13), -F(12, 13)], [0, F(12, 13), F(5, 13)]]
        rotation = matmul(rz, rx)
        self.assertEqual(matmul(rotation, transpose(rotation)), [[int(i == j) for j in range(3)] for i in range(3)])
        r = (F(-1), F(0), F(2)); original = compliance_triplet(r)
        raw = rotated_tensor(tensor_from_engineering(original), rotation)
        s = engineering_from_tensor(raw)
        self.assertTrue(all(p > 0 for p in ldl_pivots(s)))
        b = [[sum(raw[i, j, k, k] for k in range(3)) for j in range(3)] for i in range(3)]
        self.assertEqual(b, matmul(matmul(rotation, [[r[i]*int(i == j) for j in range(3)] for i in range(3)]), transpose(rotation)))
        g = [sum(s[i][j]*H[j] for j in range(6)) for i in range(6)]
        for a, (i, j) in enumerate(VOIGT):
            self.assertEqual(b[i][j], g[a]/SHEAR_FACTORS[a])
        self.assertTrue(all(g[a] != 0 for a in (3, 4, 5)))
        self.assertEqual(s[3][3], 4*raw[1, 2, 1, 2])
        self.assertEqual(s[3][0], 2*raw[1, 2, 0, 0])
        self.assertEqual(sum(b[i][i] for i in range(3)), 1)
        triad = transpose(rotation)
        self.assertEqual([bilinear(dyad(n), s, H) for n in triad], list(r))
        self.assertEqual(sum(bilinear(dyad(n), s, H) for n in triad), 1)
        for n in DIRECTIONS + tuple(map(tuple, triad)):
            direct = sum(n[i]*n[j]*raw[i, j, k, k] for i in range(3) for j in range(3) for k in range(3))
            self.assertEqual(direct, bilinear(dyad(n), s, H))
            self.assertEqual(direct, bilinear(n, b, n))
            self.assertLessEqual(min(r), direct); self.assertLessEqual(direct, max(r))
            self.assertLess(direct*direct, bilinear(H, s, H)*bilinear(dyad(n), s, dyad(n)))

    def test_research_artifact_exact_rotated_negative_direction_case(self):
        rotation = [[F(3, 5), -F(4, 5), 0], [F(4, 5), F(3, 5), 0], [0, 0, F(1)]]
        raw = rotated_tensor(tensor_from_engineering(compliance(-1)), rotation)
        s = engineering_from_tensor(raw)
        b = [[sum(raw[i, j, k, k] for k in range(3)) for j in range(3)] for i in range(3)]
        self.assertEqual(b, [[F(7, 25), -F(24, 25), 0],
                             [-F(24, 25), -F(7, 25), 0], [0, 0, 1]])
        n = (F(3, 5), F(4, 5), F(0))
        g = [sum(s[i][j]*H[j] for j in range(6)) for i in range(6)]
        self.assertEqual(g[5], -F(48, 25))
        self.assertEqual(g[5]/2, b[0][1])
        self.assertEqual(bilinear(dyad(n), s, H), -1)
        self.assertEqual(bilinear(H, s, H), 1)

    def test_isotropic_and_elastically_anisotropic_cubic_are_one_third(self):
        young = F(7)
        for nu in (F(-3, 4), F(0), F(1, 4), F(49, 100)):
            s = [[F(0) for _ in range(6)] for _ in range(6)]
            for i in range(3):
                for j in range(3):
                    s[i][j] = (1 if i == j else -nu)/young
                s[i+3][i+3] = 2*(1+nu)/young
            self.assertTrue(all(p > 0 for p in ldl_pivots(s)))
            kappa = bilinear(H, s, H)
            for n in DIRECTIONS:
                beta = bilinear(dyad(n), s, H)
                self.assertEqual(beta, (1-2*nu)/young)
                self.assertGreater(beta, 0); self.assertEqual(beta/kappa, F(1, 3))
        cubic = [[F(0) for _ in range(6)] for _ in range(6)]
        for i in range(3):
            for j in range(3):
                cubic[i][j] = F(2) if i == j else F(-1, 3)
            cubic[i+3][i+3] = F(5)
        self.assertNotEqual(cubic[3][3], 2*(cubic[0][0]-cubic[0][1]))
        self.assertTrue(all(p > 0 for p in ldl_pivots(cubic)))
        stiffness = inverse(cubic)
        for n in DIRECTIONS:
            beta = bilinear(dyad(n), cubic, H)
            self.assertEqual(beta, 1/(stiffness[0][0]+2*stiffness[0][1]))
            self.assertEqual(beta/bilinear(H, cubic, H), F(1, 3))

    def test_small_pressure_rescaling_retains_infinitesimal_strain(self):
        eta, s0 = F(1, 10**8), F(1, 10**12)
        for q in map(F, (-10**20, 0, 10**20)):
            r = (q, (1-q)/2, (1-q)/2)
            norm_squared = sum(x*x for x in r)
            pressure_squared = eta*eta/(s0*s0*norm_squared)
            self.assertGreater(pressure_squared, 0)
            self.assertEqual(pressure_squared*s0*s0*norm_squared, eta*eta)


class CompressibilityCatalogTests(unittest.TestCase):
    def test_every_pre_v016_scientific_record_and_evidence_is_preserved_by_id(self):
        baseline = load_json(ROOT/'tests/fixtures/pre_compressibility_record_digests.json')
        for kind, expected in baseline.items():
            current = {r['id']: r for r in read_catalog(kind)['records']}
            for identifier, snapshot in expected.items():
                with self.subTest(kind=kind, identifier=identifier):
                    self.assertIn(identifier, current)
                    record = public_previous_record(kind, current[identifier])
                    science = {key: value for key, value in record.items() if key not in CURATION_FIELDS}
                    self.assertEqual(digest(science), snapshot['science_sha256'])
                    for path, old_digests in snapshot['append_only'].items():
                        present = record
                        for key in path.split('.'):
                            present = present[key]
                        self.assertTrue(set(old_digests) <= {digest(item) for item in present})

    def test_research_science_and_project_proofs_have_not_drifted(self):
        self.assertEqual((DEFINITION_RULE, RANGE_RULE), RULES)
        self.assertEqual(set(COMPRESSIBILITY_CONTRACTS), set(RULES))
        for record in records():
            projected = {key: copy.deepcopy(record[key]) for key in CLOSED_FIELDS}
            projected[CONTRACT].pop('scope_exclusions')
            projected[CONTRACT].pop('source_attribution')
            if record['id'] == IDS[0]:
                # Intentional strengthening: positive trace also excludes three
                # nonpositive principal values, including all-zero beta.
                self.assertEqual(projected[CONTRACT]['sign_constraints'].pop(
                    'nonpositive_principal_beta_count_maximum'), 2)
            self.assertEqual(digest(projected), RESEARCH_SCIENCE_DIGESTS[record['id']])
            self.assertEqual(record[CONTRACT]['derivation_status'], DERIVATION_STATUS)
            self.assertTrue(record[CONTRACT]['scope_exclusions'])
            self.assertTrue(record[CONTRACT]['source_attribution'])
            self.assertFalse(record['verification']['independent_scientific_review'])
            self.assertEqual(record['evaluation_support'], 'catalog_only')
        self.assertEqual((records()[0]['quantity_dimension'], records()[0]['si_unit']), ('inverse_pressure', 'Pa^-1'))
        self.assertEqual((records()[1]['quantity_dimension'], records()[1]['si_unit']), ('dimensionless', '1'))

    def test_source_rights_and_review_limits_remain_explicit(self):
        sources = {r['id']: r for r in read_catalog('sources')['records']}
        ortiz = sources['ortiz_2012_anisotropic_mof_elasticity']
        miller = sources['miller_evans_marmier_2015_linear_compressibility']
        for source in (ortiz, miller):
            self.assertIsNone(source['license']['identifier'])
            self.assertEqual(source['bundled_content'], 'bibliographic_metadata_mathematical_formulas_and_original_curation_notes_only')
        self.assertIn('visually_inspected', ortiz['read_status'])
        self.assertIn('no_page_image_verification', miller['read_status'])
        self.assertIn('403', ' '.join(miller['claim_notes']))
        self.assertIn('not source theorems', records()[1]['evidence'][0]['verified_as'])

    def test_all_four_languages_render_names_caveats_and_identical_canonical_json(self):
        canonical = {identifier: [] for identifier in IDS}
        for language in LANGUAGES:
            for index, record in enumerate(records()):
                name = translate('catalog_name_'+record['id'], language)
                self.assertNotIn('[missing:', name)
                self.assertIn(record['id'], {r['id'] for r in query_catalog('claims', query=name)['records']})
                rendered = render_catalog({'records': [record]}, 'claims', language)
                expected = LABELS[:3] + (LABELS[3],)
                if index == 1:
                    expected += LABELS[4:]
                for key in expected:
                    self.assertIn(translate(key, language), rendered)
                self.assertIn(name, rendered); self.assertIn(record['formula_display'], rendered)
                self.assertNotIn('[missing:', rendered)
                result = subprocess.run([sys.executable, '-m', 'materials_boundaries', 'catalog', 'claims',
                                         '--id', record['id'], '--json', '--lang', language],
                                        cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                canonical[record['id']].append(result.stdout)
        self.assertTrue(all(len(set(outputs)) == 1 for outputs in canonical.values()))

    def test_exact_executable_registry_and_catalog_formulas_never_dispatch(self):
        expected_pairs = {(identifier, identifier+'_v1') for identifier in EXECUTABLE_IDS[:6]}
        expected_pairs.update({('youngs_modulus_outer', 'isotropic_youngs_modulus_outer_v1'),
                               ('poissons_ratio_outer', 'isotropic_poissons_ratio_outer_v1')})
        self.assertEqual({tuple(rule[:2]) for rule in (*BASE_RULES, *DERIVED_RULES)}, expected_pairs)
        self.assertEqual(len(BASE_RULES)+len(DERIVED_RULES), 8)
        expected = evaluate(example())
        with patch('materials_boundaries.catalog.read_catalog', side_effect=AssertionError('catalog dispatch prohibited')):
            self.assertEqual(evaluate(example()), expected)
        poisoned = read_catalog('claims')
        for record in poisoned['records']:
            if record['id'] in IDS:
                record.update(formula_display='raise_if_executed()', quantity='poison_compressibility')
        original_read = read_catalog
        with patch('materials_boundaries.visualization.read_catalog',
                   side_effect=lambda kind: poisoned if kind == 'claims' else original_read(kind)):
            bundle = build_comparison([example()], fractions=[0, .5, 1])
        self.assertEqual({(r['id'], r['rule_id']) for r in bundle['catalogs']['claims']['records']}, expected_pairs)
        self.assertEqual(len(bundle['series']), 8)
        rendered = json.dumps(bundle)+render_html(bundle)+render_svg(bundle, bundle['cases'][0]['id'])
        for token in (*IDS, 'raise_if_executed', 'poison_compressibility'):
            self.assertNotIn(token, rendered)

    def test_runtime_catalog_rendering_needs_no_numerical_or_schema_dependency(self):
        code = (
            'import sys; from materials_boundaries.catalog import read_catalog; '
            'from materials_boundaries.catalog_output import render_catalog; '
            "c=read_catalog('claims'); "
            "r=[r for r in c['records'] if 'hydrostatic_compressibility_contract' in r]; "
            "assert len(r)>=2; assert 'beta' in render_catalog({'records':r},'claims'); "
            "assert not {'numpy','scipy','sympy','jsonschema'} & set(sys.modules)"
        )
        result = subprocess.run([sys.executable, '-S', '-c', code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class CompressibilitySchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalogs = load_catalogs(ROOT/'materials_boundaries/data')
        self.validator = Draft202012Validator(load_json(ROOT/'schemas/claims.schema.json'))

    def rejected(self, change, index=0, schema=True):
        candidate = copy.deepcopy(self.catalogs); change(records(candidate)[index])
        if schema:
            self.assertTrue(list(self.validator.iter_errors(candidate['claims'])))
        with self.assertRaises(CatalogValidationError):
            validate_catalogs(candidate)
        with self.assertRaises(ValueError):
            validate_compressibility_records(candidate['claims']['records'], resolve_dependencies=True)
        with self.assertRaises(ValueError):
            render_catalog({'records': [records(candidate)[index]]}, 'claims')

    def test_public_schema_and_embedded_snapshot_are_v110(self):
        self.validator.check_schema(self.validator.schema)
        self.assertEqual(self.catalogs['claims']['schema_version'], '1.10.0')
        self.assertEqual(self.validator.schema['$id'], 'urn:materials-boundaries:schema:claims:1.10.0')
        self.assertEqual(load_json(ROOT/'schemas/comparison.schema.json')['$defs']['claims'], self.validator.schema)
        validate_catalogs(self.catalogs)

    def test_every_scientific_node_rejects_recursive_value_shape_and_type_mutations(self):
        for index, canonical in enumerate(records(self.catalogs)):
            for field in CLOSED_FIELDS:
                mutations = [((field,), 'delete', None)]
                mutations.extend(scientific_mutations(canonical[field], (field,)))
                for path, operation, value in mutations:
                    with self.subTest(index=index, path=path, operation=operation, value=value):
                        mutated = copy.deepcopy(canonical)
                        apply_mutation(mutated, path, operation, value)
                        subset = {'schema_version': '1.10.0', 'records': [mutated]}
                        self.assertTrue(list(self.validator.iter_errors(subset)))
                        with self.assertRaises(ValueError):
                            validate_compressibility_records([mutated])

    def test_identity_routing_foreign_metadata_and_extra_fields_are_rejected(self):
        for index in (0, 1):
            self.rejected(lambda r: r.pop('rule_id'), index)
            for rule in (None, False, 1, [], {}, ''):
                with self.subTest(index=index, rule=rule):
                    self.rejected(lambda r: r.update(rule_id=rule), index)
            for change in (lambda r: r.update(rule_id='unsupported_compressibility_v1'),
                           lambda r: r.update(rule_id=RULES[1-index]),
                           lambda r: r.update(quantity='effective_bulk_modulus'),
                           lambda r: r.update(criterion={}),
                           lambda r: r.update(index_range={}),
                           lambda r: r.update(directional_contract={}),
                           lambda r: r.update(unknown_scientific_field=True)):
                self.rejected(change, index)
        for original in self.catalogs['claims']['records']:
            if original['rule_id'] in RULES:
                continue
            candidate = copy.deepcopy(self.catalogs)
            target = next(r for r in candidate['claims']['records'] if r['id'] == original['id'])
            target[CONTRACT] = copy.deepcopy(records()[0][CONTRACT])
            with self.subTest(identifier=original['id']):
                self.assertTrue(list(self.validator.iter_errors(candidate['claims'])))
                with self.assertRaises(CatalogValidationError): validate_catalogs(candidate)
                with self.assertRaises(ValueError): validate_compressibility_records(candidate['claims']['records'])

    def test_wrong_units_signs_loading_and_energy_attribution_are_rejected(self):
        for index in (0, 1):
            for dimension, unit in (('pressure', 'Pa'), ('inverse_pressure', 'GPa^-1'),
                                    ('dimensionless', 'Pa^-1'), ('inverse_pressure', '1')):
                self.rejected(lambda r: r.update(quantity_dimension=dimension, si_unit=unit), index)
            for key, value in (('stress', 'sigma=p*I'), ('loading', 'hydrostatic_strain'),
                               ('loading', 'static_uniaxial_stress'), ('pressure_sign', 'tension_positive'),
                               ('stability', 'positive_semidefinite'), ('spatial_dimension', 2),
                               ('shear_conversion', 'S_eng_44=S2323')):
                self.rejected(lambda r: r['required_assumptions'].update({key: value}), index)
        for key, value in (('strict', False), ('equality_attained', True),
                           ('sufficient_for_full_SPD', True), ('universal_finite_numerical_bound', True)):
            self.rejected(lambda r: r[CONTRACT]['necessary_energy_constraint'].update({key: value}), 1)
        self.rejected(lambda r: r[CONTRACT].update(source_attribution={'theorem': 'Ortiz and Miller prove all-real range'}), 1)

    def test_dependencies_resolve_by_family_and_allow_only_one_definition(self):
        for value in (None, {}, '', [None], [True], [], [IDS[0], IDS[0]]):
            self.rejected(lambda r: r.update(dependencies=value), 1)
        for value in ([IDS[1]], ['voigt_bulk'], ['missing_definition']):
            self.rejected(lambda r: r.update(dependencies=value), 1, schema=False)
        self.rejected(lambda r: r.update(dependencies=[IDS[1]]))
        for index in (0, 1):
            for change in (lambda r: r.pop('parameters'), lambda r: r['parameters'].pop(),
                           lambda r: r['parameters'].append(copy.deepcopy(r['parameters'][0])),
                           lambda r: r['parameters'][0].update(si_unit='Pa'),
                           lambda r: r['parameters'][0].update(meaning='for an unrelated compliance S')):
                self.rejected(change, index)
        for record in records(self.catalogs): record['parameters'].reverse()
        validate_catalogs(self.catalogs)
        validate_compressibility_records(self.catalogs['claims']['records'], resolve_dependencies=True)

    def test_nonfinite_and_malformed_endpoint_metadata_fail_closed(self):
        for token in ('Infinity', '-Infinity', 'NaN', '1e999'):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'bad.json'; path.write_text('{"value":'+token+'}')
                with self.assertRaises(ValueError): load_json(path)
        for value in (float('inf'), float('-inf'), float('nan'), None, 'Infinity', 1):
            self.rejected(lambda r: r[CONTRACT]['material_class_range']['upper'].update(value=value), 1)
        for change in (lambda c: c['material_class_range']['lower'].update(status='unknown'),
                       lambda c: c['material_class_range']['upper'].update(status='finite', value=1),
                       lambda c: c['material_class_range']['upper'].update(infinity_attained=True),
                       lambda c: c['fixed_tensor_range'].update(finite_and_attained=False),
                       lambda c: c.update(symmetry_warning='Every symmetry class is unbounded')):
            self.rejected(lambda r: change(r[CONTRACT]), 1)

    def test_duplicate_ids_do_not_shadow_malformed_records_in_any_order(self):
        canonical = records()[0]; bad = copy.deepcopy(canonical)
        bad[CONTRACT]['volume_positivity']['strict'] = False
        for supplied in ([bad, canonical], [canonical, bad], [canonical, canonical]):
            with self.assertRaises(ValueError): validate_compressibility_records(supplied)
            with self.assertRaises(ValueError): render_catalog({'records': supplied}, 'claims')

    def test_fresh_sources_curation_and_mixed_open_families_remain_appendable(self):
        candidate = copy.deepcopy(self.catalogs)
        source = copy.deepcopy(candidate['sources']['records'][0])
        source.update(id='synthetic_compressibility_append_source', title='SYNTHETIC TEST ONLY',
                      doi=None, authors=[], year=None, urls=['https://example.invalid/compressibility'],
                      read_status='synthetic_unverified', role='synthetic_test_only',
                      claim_notes=['Synthetic appendability fixture, not scientific evidence.'])
        source['license'] = {'status': 'unknown', 'identifier': None}
        source['provenance'] = {'curation_date': '2026-10-02', 'method': 'Synthetic fixture only.'}
        # Append into the full production catalog, including prior open families.
        # Historical porous records remain explicitly ID-bound in their schema.
        supported_ids = set(IDS) | {
            'directional_poissons_ratio_definition_and_range',
            'directional_poisson_reciprocity_energy_constraint',
            'lefm_central_crack_mode_i_stress_intensity',
            'cubic_born_stability',
        }
        originals = [r for r in candidate['claims']['records'] if r['id'] in supported_ids]
        self.assertEqual({r['id'] for r in originals}, supported_ids)
        id_map = {r['id']: 'synthetic_append_'+r['id'] for r in originals}
        additions = copy.deepcopy(originals)
        for record in additions:
            record['id'] = id_map[record['id']]
            record['name'] = 'SYNTHETIC TEST ONLY '+record['id']
            record['version'] = '0.0.0-synthetic'
            record['dependencies'] = [id_map.get(d, d) for d in record['dependencies']]
            record['evidence'] = [{'source_id': source['id'], 'locator': None,
                                   'verification_status': 'synthetic_unverified',
                                   'verified_as': 'Synthetic fixture, not scientific evidence.'}]
            record['verification'] = {'status': 'synthetic_unverified', 'independent_scientific_review': False,
                                      'gaps': ['No independent source inspection.']}
            record['limits'].append('Synthetic fixture only; no material interpretation.')
            for labels in candidate['locales']['languages'].values():
                labels['catalog_name_'+record['id']] = record['name']
        candidate['sources']['records'].append(source)
        candidate['claims']['records'].extend(additions)
        expected = set(id_map.values())
        for order in ('forward', 'reverse', 'interleaved'):
            ordered = copy.deepcopy(candidate)
            if order == 'reverse':
                ordered['claims']['records'].reverse(); ordered['sources']['records'].reverse()
            elif order == 'interleaved':
                rows = ordered['claims']['records']
                ordered['claims']['records'] = rows[1::2]+rows[::2]
            with self.subTest(order=order):
                validate_catalogs(ordered)
                self.assertTrue(expected <= {r['id'] for r in ordered['claims']['records']})
                validate_compressibility_records(ordered['claims']['records'], resolve_dependencies=True)
        # Rendering a fresh pair with its fresh definition must resolve locally.
        appended = [r for r in additions if r['rule_id'] in RULES]
        rendered = render_catalog({'records': list(reversed(appended))}, 'claims')
        self.assertIn(id_map[IDS[0]], rendered); self.assertIn(id_map[IDS[1]], rendered)

    def test_historical_protected_porous_ids_remain_id_scoped(self):
        protected = ('hs_porous_bulk_3d_solid_void', 'hs_porous_shear_3d_solid_void',
                     'hs_porous_youngs_outer_3d_solid_void')
        for identifier in protected:
            candidate = copy.deepcopy(self.catalogs)
            target = next(r for r in candidate['claims']['records'] if r['id'] == identifier)
            target['id'] = 'unsupported_rename_'+identifier
            with self.subTest(identifier=identifier):
                self.assertTrue(list(self.validator.iter_errors(candidate['claims'])))
                with self.assertRaises(CatalogValidationError):
                    validate_catalogs(candidate)

    def test_new_required_labels_cannot_disappear_in_every_language(self):
        for key in LABELS + tuple('catalog_name_'+identifier for identifier in IDS):
            candidate = copy.deepcopy(self.catalogs)
            for labels in candidate['locales']['languages'].values(): labels.pop(key)
            with self.subTest(key=key), self.assertRaises(CatalogValidationError):
                validate_catalogs(candidate)


if __name__ == '__main__':
    unittest.main()
