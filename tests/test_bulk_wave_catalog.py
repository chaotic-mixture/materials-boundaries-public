"""Closed bulk-wave catalog metadata and exact, test-only project algebra.

These finite rational checks supplement the written tensor identities. They do
not constitute independent peer review or install a Christoffel/wave solver.
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
from materials_boundaries._wave_contract import (
    CHRISTOFFEL_RULE, ISOTROPIC_RULE, WAVE_CONTRACTS, validate_wave_records,
)
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs
from catalog_fixtures import EXECUTABLE_IDS
from test_engine import ROOT, example

IDS = ('isotropic_bulk_plane_wave_speeds_and_ratio',
       'christoffel_tensor_strong_ellipticity')
RULES = tuple(identifier+'_v1' for identifier in IDS)
CONTRACT = 'bulk_wave_contract'
CLOSED_FIELDS = ('quantity', 'direction', 'claim_type', 'bound_kind',
                 'quantity_dimension', 'si_unit', 'evaluation_support',
                 'formula_display', 'required_assumptions', 'parameters', CONTRACT)
CURATION_FIELDS = {'evidence', 'verification', 'provenance', 'claim_notes', 'urls'}
DIRECTIONS = ((F(1), F(0), F(0)), (F(0), F(1), F(0)),
              (F(0), F(0), F(1)), (F(3, 5), F(4, 5), F(0)),
              (F(1, 3), F(2, 3), F(2, 3)))
INDICES = tuple(itertools.product(range(3), repeat=4))


def records(catalogs=None):
    catalog = read_catalog('claims') if catalogs is None else catalogs['claims']
    by_id = {record['id']: record for record in catalog['records']}
    return [by_id[identifier] for identifier in IDS]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def dot(x, y):
    return sum(a*b for a, b in zip(x, y))


def matvec(matrix, vector):
    return tuple(dot(row, vector) for row in matrix)


def isotropic_tensor(bulk, shear):
    """Exact fourth-order fixture; this function is not production code."""
    bulk, shear = F(bulk), F(shear)
    lame = bulk-F(2, 3)*shear
    return {(i, j, k, l): lame*int(i == j)*int(k == l)
            + shear*(int(i == k)*int(j == l)+int(i == l)*int(j == k))
            for i, j, k, l in INDICES}


def acoustic_tensor(stiffness, n):
    """Q_ik = C_ijkl n_j n_l, intentionally spelled out at test scope."""
    return tuple(tuple(sum(stiffness[i, j, k, l]*n[j]*n[l]
                           for j in range(3) for l in range(3))
                       for k in range(3)) for i in range(3))


def strain_energy(stiffness, strain):
    return sum(strain[i][j]*stiffness[i, j, k, l]*strain[k][l]
               for i, j, k, l in INDICES)/F(2)


def rotated_tensor(stiffness, rotation):
    return {(i, j, k, l): sum(rotation[i][a]*rotation[j][b]*rotation[k][c]*rotation[l][d]
                              * stiffness[a, b, c, d] for a, b, c, d in INDICES)
            for i, j, k, l in INDICES}


def scientific_mutations(value, path=()):
    """Reject omissions, foreign keys, changed values and wrong JSON types."""
    if isinstance(value, dict):
        yield path, 'extra', ('unsupported_science', True)
        yield path, 'replace', []
        for key, child in value.items():
            yield path+(key,), 'delete', None
            yield from scientific_mutations(child, path+(key,))
    elif isinstance(value, list):
        yield path, 'replace', {}
        yield path, 'append', '__unsupported__'
        for index, child in enumerate(value):
            yield path+(index,), 'delete', None
            yield from scientific_mutations(child, path+(index,))
    elif isinstance(value, bool):
        yield path, 'replace', not value
        yield path, 'replace', int(value)
    elif isinstance(value, str):
        yield path, 'replace', value+'__weakened__'
        yield path, 'replace', 1
    elif value is None:
        yield path, 'replace', 'not_null'
        yield path, 'replace', False
    else:
        yield path, 'replace', value+1
        yield path, 'replace', str(value)


def apply_mutation(record, path, operation, value):
    target = record
    if operation in {'extra', 'append'}:
        for component in path:
            target = target[component]
        if operation == 'extra':
            target[value[0]] = value[1]
        else:
            target.append(value)
    else:
        for component in path[:-1]:
            target = target[component]
        if operation == 'delete':
            del target[path[-1]]
        else:
            target[path[-1]] = value


class BulkWaveAlgebraTests(unittest.TestCase):
    def test_isotropic_fourth_order_contraction_and_polarizations(self):
        for bulk, shear, density in ((F(3), F(2), F(5)), (F(1, 7), F(11, 3), F(17)),
                                      (F(10**12), F(1, 10**9), F(10**6))):
            stiffness = isotropic_tensor(bulk, shear)
            for n in DIRECTIONS:
                self.assertEqual(dot(n, n), 1)
                q = acoustic_tensor(stiffness, n)
                expected = tuple(tuple(shear*int(i == k)+(bulk+shear/F(3))*n[i]*n[k]
                                       for k in range(3)) for i in range(3))
                self.assertEqual(q, expected)
                longitudinal = bulk+F(4, 3)*shear
                self.assertEqual(matvec(q, n), tuple(longitudinal*x for x in n))
                # Two independent transverse vectors, including the polar case.
                t1 = (-n[1], n[0], F(0)) if n[0] or n[1] else (F(1), F(0), F(0))
                t2 = (n[1]*t1[2]-n[2]*t1[1], n[2]*t1[0]-n[0]*t1[2],
                      n[0]*t1[1]-n[1]*t1[0])
                for a in (t1, t2):
                    self.assertGreater(dot(a, a), 0)
                    self.assertEqual(dot(n, a), 0)
                    self.assertEqual(matvec(q, a), tuple(shear*x for x in a))
                    gamma_a = tuple(x/density for x in matvec(q, a))
                    self.assertEqual(gamma_a, tuple(shear/density*x for x in a))
                self.assertEqual(dot(t1, t2), 0)

    def test_full_spd_implies_strong_ellipticity_by_symmetric_rank_one_strain(self):
        # Isotropic SPD plus an anisotropic nonnegative square is still SPD:
        # e:C:e = K tr(e)^2 + 2G ||dev(e)||^2 + eta (b:e)^2.
        bulk, shear, eta = F(7, 3), F(5, 2), F(11, 7)
        b = ((F(2), F(1), F(0)), (F(1), F(-1), F(3)), (F(0), F(3), F(4)))
        stiffness = isotropic_tensor(bulk, shear)
        for i, j, k, l in INDICES:
            stiffness[i, j, k, l] += eta*b[i][j]*b[k][l]
        for n in DIRECTIONS+((F(2), F(-3), F(7)),):
            for a in DIRECTIONS+((F(3), F(-5), F(2)),):
                strain = tuple(tuple((a[i]*n[j]+n[i]*a[j])/F(2) for j in range(3))
                               for i in range(3))
                norm_squared = sum(value*value for row in strain for value in row)
                self.assertEqual(norm_squared, (dot(a, a)*dot(n, n)+dot(a, n)**2)/F(2))
                self.assertGreater(norm_squared, 0)
                trace = sum(strain[i][i] for i in range(3))
                dev_norm = sum((strain[i][j]-trace/F(3)*int(i == j))**2
                               for i in range(3) for j in range(3))
                closed_form = bulk*trace**2+2*shear*dev_norm+eta*sum(
                    b[i][j]*strain[i][j] for i in range(3) for j in range(3))**2
                self.assertEqual(2*strain_energy(stiffness, strain), closed_form)
                self.assertEqual(dot(a, matvec(acoustic_tensor(stiffness, n), a)), closed_form)
                self.assertGreater(closed_form, 0)

    def test_strong_ellipticity_counterexample_triple_degeneracy_negative_energy(self):
        for shear, density in ((F(1), F(1)), (F(17, 5), F(19, 3))):
            bulk = -shear/F(3)
            stiffness = isotropic_tensor(bulk, shear)
            self.assertEqual(bulk-F(2, 3)*shear, -shear)
            for n in DIRECTIONS:
                q = acoustic_tensor(stiffness, n)
                self.assertEqual(q, tuple(tuple(shear*int(i == k) for k in range(3)) for i in range(3)))
                for a in DIRECTIONS:
                    self.assertEqual(matvec(q, a), tuple(shear*x for x in a))
                    self.assertGreater(dot(a, matvec(q, a))/density, 0)
            for alpha in (F(-2), F(1, 3), F(5)):
                hydrostatic = tuple(tuple(alpha*int(i == j) for j in range(3)) for i in range(3))
                energy = strain_energy(stiffness, hydrostatic)
                self.assertEqual(energy, F(9, 2)*bulk*alpha**2)
                self.assertEqual(energy, -F(3, 2)*shear*alpha**2)
                self.assertLess(energy, 0)

    def test_zero_bulk_outside_strict_energy_class_but_positive_wave_modes(self):
        shear = F(7, 3)
        stiffness = isotropic_tensor(0, shear)
        self.assertEqual(strain_energy(stiffness, ((1, 0, 0), (0, 1, 0), (0, 0, 1))), 0)
        for n in DIRECTIONS:
            q = acoustic_tensor(stiffness, n)
            self.assertEqual(dot(n, matvec(q, n)), F(4, 3)*shear)
            for a in DIRECTIONS:
                self.assertEqual(dot(a, matvec(q, a)), shear*dot(a, a)+shear/F(3)*dot(a, n)**2)
                self.assertGreater(dot(a, matvec(q, a)), 0)

    def test_zero_wave_eigenvalue_fails_strict_boundary_and_reality_is_insufficient(self):
        for n in DIRECTIONS:
            shear = F(3)
            longitudinal_zero = acoustic_tensor(isotropic_tensor(-F(4, 3)*shear, shear), n)
            self.assertEqual(matvec(longitudinal_zero, n), (0, 0, 0))
            transverse_zero = acoustic_tensor(isotropic_tensor(2, 0), n)
            t = (-n[1], n[0], F(0)) if n[0] or n[1] else (F(1), F(0), F(0))
            self.assertEqual(matvec(transverse_zero, t), (0, 0, 0))
            indefinite = acoustic_tensor(isotropic_tensor(-2*shear, shear), n)
            self.assertEqual(indefinite, tuple(zip(*indefinite)))
            self.assertLess(dot(n, matvec(indefinite, n)), 0)

    def test_rotated_rational_anisotropic_index_contraction_and_covariance(self):
        # A rational orthogonal rotation retains every index without float noise.
        rotation = ((F(3, 5), F(-4, 5), F(0)), (F(4, 5), F(3, 5), F(0)),
                    (F(0), F(0), F(1)))
        for i in range(3):
            for j in range(3):
                self.assertEqual(dot(rotation[i], rotation[j]), int(i == j))
        original = isotropic_tensor(7, 3)
        original[0, 0, 0, 0] += 11  # Positive anisotropic strain-energy square.
        rotated = rotated_tensor(original, rotation)
        for i, j, k, l in INDICES:
            self.assertEqual(rotated[i, j, k, l], rotated[j, i, k, l])
            self.assertEqual(rotated[i, j, k, l], rotated[i, j, l, k])
            self.assertEqual(rotated[i, j, k, l], rotated[k, l, i, j])
        differs = []
        for n in DIRECTIONS:
            rotated_n = matvec(rotation, n)
            q = acoustic_tensor(original, n)
            rotated_q = acoustic_tensor(rotated, rotated_n)
            expected = tuple(tuple(sum(rotation[i][a]*q[a][b]*rotation[k][b]
                                       for a in range(3) for b in range(3))
                                   for k in range(3)) for i in range(3))
            self.assertEqual(rotated_q, expected)
            # Chevrot's Gamma_jk uses n_i n_l. First-pair minor symmetry
            # and relabeling match the project's free indices i,k exactly.
            source_gamma = tuple(tuple(sum(rotated[i, j, k, l]*rotated_n[i]*rotated_n[l]
                                           for i in range(3) for l in range(3))/F(7)
                                       for k in range(3)) for j in range(3))
            self.assertEqual(source_gamma, tuple(tuple(value/F(7) for value in row) for row in rotated_q))
            # C_ijkl n_k n_l is a stress-like contraction, not Q_ik.
            wrong = tuple(tuple(sum(rotated[i, j, k, l]*rotated_n[k]*rotated_n[l]
                                    for k in range(3) for l in range(3))
                                for j in range(3)) for i in range(3))
            differs.append(wrong != rotated_q)
            for a in DIRECTIONS:
                rotated_a = matvec(rotation, a)
                explicit = sum(rotated[i, j, k, l]*rotated_a[i]*rotated_n[j]
                               *rotated_a[k]*rotated_n[l] for i, j, k, l in INDICES)
                self.assertEqual(explicit, dot(rotated_a, matvec(rotated_q, rotated_a)))
                self.assertEqual(explicit, dot(a, matvec(q, a)))
        self.assertTrue(all(differs))

    def test_ratio_open_endpoint_inverse_construction_and_density_cancellation(self):
        for target_ratio in (F(7, 6), F(6, 5), F(2), F(100), F(10**12)):
            self.assertGreater(target_ratio**2, F(4, 3))
            for shear in (F(1, 10**9), F(1), F(10**9)):
                bulk = shear*(target_ratio**2-F(4, 3))
                self.assertGreater(bulk, 0)
                for density in (F(1, 10**7), F(1), F(10**7)):
                    longitudinal_squared = (bulk+F(4, 3)*shear)/density
                    transverse_squared = shear/density
                    self.assertEqual(longitudinal_squared/transverse_squared, target_ratio**2)
        # R^2 - 4/3 = K/G > 0 and tends to zero through finite positive members.
        for denominator in (10, 10**3, 10**12):
            ratio_squared = F(4, 3)+F(1, denominator)
            self.assertGreater(ratio_squared, F(4, 3))
            self.assertEqual(ratio_squared-F(4, 3), F(1, denominator))
        # An arbitrarily large finite target still has finite positive K.
        for target in (F(2), F(10**6), F(10**30)):
            self.assertGreater(target**2-F(4, 3), 0)
        # Strong ellipticity alone admits every positive R, including R <= 1.
        for target in (F(1, 10**9), F(1, 2), F(1), F(2)):
            bulk, shear = target**2-F(4, 3), F(1)
            self.assertGreater(bulk+F(4, 3)*shear, 0)
            self.assertEqual((bulk+F(4, 3)*shear)/shear, target**2)

    def test_si_pressure_over_density_is_speed_squared(self):
        # Exponents are (kg, m, s); n and a are dimensionless.
        pressure, density, speed = (1, -1, -2), (1, -3, 0), (0, 1, -1)
        gamma = tuple(p-r for p, r in zip(pressure, density))
        self.assertEqual(gamma, (0, 2, -2))
        self.assertEqual(gamma, tuple(2*x for x in speed))
        self.assertEqual(tuple(r+2*c for r, c in zip(density, speed)), pressure)
        self.assertEqual(tuple(x-x for x in gamma), (0, 0, 0))


LABELS = tuple('catalog_wave_'+suffix for suffix in (
    'notice', 'conditions', 'normalization', 'polarization', 'energy', 'range', 'limits'))
STATUS_LABELS = tuple('catalog_status_'+suffix for suffix in (
    'mass_density', 'speed', 'speed_squared', 'isotropic_bulk_phase_speed_ratio', 'bulk_phase_speed_squared'))
# A separate snapshot protects against accidentally weakening both the canonical
# data and its generated closed validator in the same change.
SCIENTIFIC_DIGESTS = {
    IDS[0]: 'df3fe39e0d8f2bc0fff38f078197ce06c935cc63cb3caf954315b4fd58a5e16a',
    IDS[1]: 'aaf6c46ea6d9e7487865ae93873483b8b56f28349b0e559e31670e09e12bc8ab',
}


class BulkWaveCatalogTests(unittest.TestCase):
    def test_pre_v018_scientific_records_preserved_by_id_with_appendable_curation(self):
        baseline = load_json(ROOT/'tests/fixtures/pre_bulk_wave_record_digests.json')
        for kind, snapshots in baseline.items():
            current = {r['id']: r for r in read_catalog(kind)['records']}
            for identifier, expected in snapshots.items():
                with self.subTest(kind=kind, identifier=identifier):
                    self.assertIn(identifier, current)
                    record = current[identifier]
                    science = {k: v for k, v in record.items() if k not in CURATION_FIELDS}
                    self.assertEqual(digest(science), expected['science_sha256'])
                    for key, prior_digests in expected['append_only'].items():
                        self.assertTrue(set(prior_digests) <= {digest(item) for item in record[key]})

    def test_scientific_snapshot_units_index_conventions_strictness_and_source_separation(self):
        self.assertEqual((ISOTROPIC_RULE, CHRISTOFFEL_RULE), RULES)
        self.assertEqual(set(WAVE_CONTRACTS), set(RULES))
        for record in records():
            self.assertEqual(digest({key: record[key] for key in (*CLOSED_FIELDS, 'dependencies')}),
                             SCIENTIFIC_DIGESTS[record['id']])
            self.assertEqual(record['claim_type'], 'model_relation')
            self.assertEqual(record['direction'], 'relation')
            self.assertEqual(record['evaluation_support'], 'catalog_only')
            self.assertIsNone(record['bound_kind'])
            self.assertEqual(record['dependencies'], [])
            self.assertFalse(record['verification']['independent_scientific_review'])
            self.assertIn('not_peer_reviewed', record['verification']['status'])
            contract = record[CONTRACT]
            self.assertEqual(contract['derivation_status'],
                             'original_project_algebra_not_independent_scientific_peer_review')
            self.assertFalse(contract['source_attribution']['scientific_peer_review_certified'])
            self.assertFalse(contract['source_attribution']['physical_realizability_certified'])
            self.assertIn('original_project_derivations', contract['source_attribution']['project_results'])
            self.assertEqual(contract['units'], {
                'C_K_G_lambda_Q': 'Pa', 'rho': 'kg m^-3', 'c': 'm s^-1',
                'Gamma_and_c_squared': 'm^2 s^-2', 'n_and_a': '1',
                'dimension_check': 'Pa/(kg m^-3)=m^2 s^-2'})
            self.assertEqual(record['required_assumptions']['tensor_symmetries'],
                             'C_ijkl=C_jikl=C_ijlk=C_klij')
            self.assertEqual(record['required_assumptions']['density'],
                             'finite_constant_scalar_mass_density_rho>0')
        isotropic, christoffel = records()
        interval = isotropic[CONTRACT]['material_class_range']
        self.assertEqual(interval['attainable_set'], '(sqrt(4/3), infinity)')
        self.assertFalse(interval['lower']['inclusive']); self.assertFalse(interval['lower']['attained'])
        self.assertFalse(interval['upper']['finite_bound_exists'])
        self.assertFalse(interval['upper']['infinity_attained']); self.assertTrue(interval['density_cancels'])
        self.assertEqual(christoffel[CONTRACT]['contraction']['unnormalized'], 'Q_ik=C_ijkl*n_j*n_l')
        self.assertEqual(christoffel[CONTRACT]['contraction']['normalized'], 'Gamma_ik=Q_ik/rho')
        self.assertTrue(christoffel[CONTRACT]['strict_criterion']['zero_eigenvalues_excluded'])
        self.assertFalse(christoffel[CONTRACT]['strict_criterion']['nonnegative_is_sufficient'])
        self.assertFalse(christoffel[CONTRACT]['spectrum']['distinct_eigenvalues_required'])
        self.assertFalse(christoffel[CONTRACT]['energy_relation']['converse'])

    def test_sources_retain_version_rights_and_project_derivation_caveats(self):
        sources = {r['id']: r for r in read_catalog('sources')['records']}
        chevrot, xiang = [sources[sid] for sid in ('chevrot_vanderhilst_2003', 'xiang_qi_wei_2018_arxiv_v2')]
        self.assertEqual(chevrot['doi'], '10.1046/j.1365-246X.2003.01865.x')
        self.assertIn('p498_equations', chevrot['read_status'])
        self.assertIn('https://arxiv.org/abs/1708.04876v2', xiang['urls'])
        self.assertIn('preprint', xiang['role'])
        self.assertIn('journal-publication status is not verified', ' '.join(xiang['claim_notes']))
        self.assertIn('K+G/3=0', ' '.join(xiang['claim_notes']))
        for source in (chevrot, xiang):
            self.assertIsNone(source['license']['identifier'])
            self.assertNotEqual(source['license']['status'], 'MIT')
            self.assertIn('original_curation_only', source['bundled_content'])
            notes = ' '.join(source['claim_notes'])
            self.assertIn('not source quotations', notes)
            self.assertIn('no PDF', notes)
        for record in records():
            for item in record['evidence']:
                self.assertIn(item['source_id'], sources)
                self.assertTrue(item['locator'])
                self.assertIn('project_derivation_separate', item['verification_status'])

    def test_all_languages_authored_caveats_search_and_identical_canonical_json(self):
        self.assertEqual(set(LANGUAGES), {'en', 'zh', 'ja', 'de'})
        canonical = {identifier: [] for identifier in IDS}
        for language in LANGUAGES:
            for record in records():
                name = translate('catalog_name_'+record['id'], language)
                self.assertNotIn('[missing:', name)
                self.assertIn(record['id'], {r['id'] for r in query_catalog('claims', query=name)['records']})
                rendered = render_catalog({'records': [record]}, 'claims', language)
                for key in LABELS:
                    if key == 'catalog_wave_range' and record['id'] == IDS[1]:
                        continue
                    self.assertIn(translate(key, language), rendered)
                self.assertIn(name, rendered)
                self.assertIn(record['formula_display'], rendered)
                self.assertNotIn('[missing:', rendered)
                result = subprocess.run([sys.executable, '-m', 'materials_boundaries', 'catalog', 'claims',
                                         '--id', record['id'], '--json', '--lang', language],
                                        cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                canonical[record['id']].append(result.stdout)
            for key in STATUS_LABELS:
                self.assertNotIn('[missing:', translate(key, language))
        self.assertTrue(all(len(set(outputs)) == 1 for outputs in canonical.values()))

    def test_exact_eight_numeric_rules_and_no_wave_formula_dispatch_or_plot(self):
        expected_pairs = {(identifier, identifier+'_v1') for identifier in EXECUTABLE_IDS[:6]}
        expected_pairs.update({('youngs_modulus_outer', 'isotropic_youngs_modulus_outer_v1'),
                               ('poissons_ratio_outer', 'isotropic_poissons_ratio_outer_v1')})
        self.assertEqual({tuple(rule[:2]) for rule in (*BASE_RULES, *DERIVED_RULES)}, expected_pairs)
        self.assertEqual(len(BASE_RULES)+len(DERIVED_RULES), 8)
        expected = evaluate(example())
        with patch('materials_boundaries.catalog.read_catalog', side_effect=AssertionError('no catalog dispatch')):
            self.assertEqual(evaluate(example()), expected)
        poisoned = read_catalog('claims')
        for record in poisoned['records']:
            if record['id'] in IDS:
                record.update(formula_display='raise_if_executed()', quantity='poison_bulk_wave')
        original = read_catalog
        with patch('materials_boundaries.visualization.read_catalog',
                   side_effect=lambda kind: poisoned if kind == 'claims' else original(kind)):
            bundle = build_comparison([example()], fractions=[0, .5, 1])
        self.assertEqual({(r['id'], r['rule_id']) for r in bundle['catalogs']['claims']['records']}, expected_pairs)
        self.assertEqual(len(bundle['series']), 8)
        rendered = json.dumps(bundle)+render_html(bundle)+render_svg(bundle, bundle['cases'][0]['id'])
        for token in (*IDS, 'raise_if_executed', 'poison_bulk_wave'):
            self.assertNotIn(token, rendered)

    def test_runtime_has_no_installed_tensor_solver_or_numerical_dependency(self):
        code = (
            'import sys; import materials_boundaries as mb; '
            'from materials_boundaries.catalog import read_catalog; '
            'from materials_boundaries.catalog_output import render_catalog; '
            'from materials_boundaries import _wave_contract as wc; '
            "c=read_catalog('claims'); r=[r for r in c['records'] if 'bulk_wave_contract' in r]; "
            "assert len(r)>=2; assert 'Gamma' in render_catalog({'records':r},'claims'); "
            "assert not {'numpy','scipy','sympy','jsonschema'} & set(sys.modules); "
            "assert not {'acoustic_tensor','christoffel','wave_speeds','eig','eigh'} & set(vars(wc)); "
            "assert set(mb.__all__) == {'evaluate','ValidationError','load_json','validate_instance'}"
        )
        result = subprocess.run([sys.executable, '-S', '-c', code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class BulkWaveSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs = load_catalogs(ROOT/'materials_boundaries/data')
        cls.validator = Draft202012Validator(load_json(ROOT/'schemas/claims.schema.json'))

    def rejected(self, change, index=0, *, schema=True):
        candidate = copy.deepcopy(self.catalogs)
        change(records(candidate)[index])
        if schema:
            self.assertTrue(list(self.validator.iter_errors(candidate['claims'])))
        with self.assertRaises(CatalogValidationError):
            validate_catalogs(candidate)
        with self.assertRaises(ValueError):
            validate_wave_records(candidate['claims']['records'], resolve_dependencies=True)
        with self.assertRaises(ValueError):
            render_catalog({'records': [records(candidate)[index]]}, 'claims')
        # Exercise the package loader, not just the validator function directly.
        with patch('materials_boundaries.catalog.files') as resources:
            resources.return_value.joinpath.return_value.read_text.return_value = json.dumps(candidate['claims'])
            with self.assertRaises(ValueError):
                read_catalog('claims')

    def test_public_and_embedded_claim_schema_are_v111(self):
        self.validator.check_schema(self.validator.schema)
        self.assertEqual(self.catalogs['claims']['schema_version'], '1.13.0')
        self.assertEqual(self.validator.schema['$id'], 'urn:materials-boundaries:schema:claims:1.13.0')
        self.assertEqual(load_json(ROOT/'schemas/comparison.schema.json')['$defs']['claims'], self.validator.schema)
        validate_catalogs(self.catalogs)

    def test_every_scientific_node_rejects_omissions_shape_values_and_types(self):
        for index, record in enumerate(records(self.catalogs)):
            for field in (*CLOSED_FIELDS, 'dependencies'):
                mutations = [((field,), 'delete', None), *scientific_mutations(record[field], (field,))]
                for path, operation, value in mutations:
                    with self.subTest(index=index, path=path, operation=operation, value=value):
                        mutated = copy.deepcopy(record)
                        apply_mutation(mutated, path, operation, value)
                        subset = {'schema_version': '1.13.0', 'records': [mutated]}
                        self.assertTrue(list(self.validator.iter_errors(subset)))
                        with self.assertRaises(ValueError):
                            validate_wave_records([mutated])

    def test_every_assumption_has_loader_render_and_full_validator_guards(self):
        for index, record in enumerate(records(self.catalogs)):
            for key in record['required_assumptions']:
                with self.subTest(index=index, assumption=key):
                    self.rejected(lambda r, key=key: r['required_assumptions'].pop(key), index)
            self.rejected(lambda r: r['required_assumptions'].update(unknown_condition=True), index)

    def test_density_units_index_symmetry_energy_and_strictness_fail_all_paths(self):
        for index in (0, 1):
            for key, value in (('density', 'rho>=0'), ('density', 'density_normalized_tensor_assumed'),
                               ('tensor_symmetries', 'major_symmetry_only'), ('indices', 'i,j=1,2'),
                               ('reference_state', 'prestressed'), ('spatial_dimension', 2)):
                self.rejected(lambda r, k=key, v=value: r['required_assumptions'].update({k: v}), index)
            for key, value in (('rho', 'kg m^-2'), ('Gamma_and_c_squared', 'Pa'), ('C_K_G_lambda_Q', 'GPa')):
                self.rejected(lambda r, k=key, v=value: r[CONTRACT]['units'].update({k: v}), index)
        changes = (
            lambda c: c['contraction'].update(unnormalized='Q_ij=C_ijkl*n_k*n_l'),
            lambda c: c['contraction'].update(normalized='Gamma=Q'),
            lambda c: c['strict_criterion'].update(nonnegative_is_sufficient=True),
            lambda c: c['strict_criterion'].update(zero_vectors_excluded=False),
            lambda c: c['strict_criterion'].update(zero_eigenvalues_excluded=False),
            lambda c: c['spectrum'].update(distinct_eigenvalues_required=True),
            lambda c: c['energy_relation'].update(converse=True),
            lambda c: c['counterexample'].update(division_by_K_plus_G_over_3=True),
            lambda c: c['source_attribution'].update(scientific_peer_review_certified=True),
        )
        for change in changes:
            self.rejected(lambda r, change=change: change(r[CONTRACT]), 1)
        for change in (lambda c: c['material_class_range']['lower'].update(inclusive=True),
                       lambda c: c['material_class_range']['lower'].update(attained=True),
                       lambda c: c['material_class_range']['upper'].update(infinity_attained=True),
                       lambda c: c['material_class_range'].update(density_cancels=False)):
            self.rejected(lambda r, change=change: change(r[CONTRACT]))

    def test_family_routing_unknown_relation_and_foreign_contracts_are_closed(self):
        for index in (0, 1):
            for value in (None, False, 1, [], {}, '', 'unsupported_bulk_wave_v1', RULES[1-index]):
                self.rejected(lambda r, value=value: r.update(rule_id=value), index)
            for key in ('criterion', 'index_range', 'directional_contract', 'hydrostatic_compressibility_contract',
                        'unknown_scientific_field'):
                self.rejected(lambda r, key=key: r.update({key: {}}), index)
            self.rejected(lambda r: r.pop(CONTRACT), index)
            self.rejected(lambda r: r.update(evaluation_support='composite_evaluate'), index)
            self.rejected(lambda r: r.update(dependencies=[IDS[1-index]]), index)
        for old in self.catalogs['claims']['records']:
            if old['rule_id'] in RULES:
                continue
            candidate = copy.deepcopy(self.catalogs)
            target = next(r for r in candidate['claims']['records'] if r['id'] == old['id'])
            target[CONTRACT] = copy.deepcopy(records(self.catalogs)[0][CONTRACT])
            with self.subTest(identifier=old['id']):
                self.assertTrue(list(self.validator.iter_errors(candidate['claims'])))
                with self.assertRaises(ValueError):
                    validate_wave_records(candidate['claims']['records'])
        # Removing recognizable metadata must not create a generic relation escape.
        candidate = copy.deepcopy(self.catalogs)
        generic = records(candidate)[0]
        generic.pop(CONTRACT)
        generic.update(rule_id='unknown_model_relation_v1', quantity='unknown_relation')
        self.assertTrue(list(self.validator.iter_errors(candidate['claims'])))
        with self.assertRaises(CatalogValidationError):
            validate_catalogs(candidate)

    def test_duplicate_ids_cannot_shadow_malformed_catalog_metadata(self):
        canonical = records(self.catalogs)[1]
        malformed = copy.deepcopy(canonical)
        malformed[CONTRACT]['strict_criterion']['zero_eigenvalues_excluded'] = False
        for supplied in ([malformed, canonical], [canonical, malformed], [canonical, canonical]):
            with self.assertRaises(ValueError):
                validate_wave_records(supplied)
            with self.assertRaises(ValueError):
                render_catalog({'records': supplied}, 'claims')

    def test_nonfinite_infinity_null_endpoints_and_parameter_duplicate_are_rejected(self):
        for token in ('Infinity', '-Infinity', 'NaN', '1e999'):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'bad.json'
                path.write_text('{"value":'+token+'}')
                with self.assertRaises(ValueError):
                    load_json(path)
        for value in (float('inf'), float('-inf'), float('nan'), None, 'Infinity', 0):
            self.rejected(lambda r, value=value: r[CONTRACT]['material_class_range']['upper'].update(value=value))
        for index in (0, 1):
            self.rejected(lambda r: r['parameters'].append(copy.deepcopy(r['parameters'][0])), index)
            self.rejected(lambda r: r['parameters'][0].update(si_unit='GPa'), index)
            self.rejected(lambda r: r['parameters'][0].update(meaning='unrelated quantity'), index)

    def test_fresh_ids_sources_evidence_order_and_parameter_order_remain_appendable(self):
        candidate = copy.deepcopy(self.catalogs)
        source = copy.deepcopy(candidate['sources']['records'][0])
        source.update(id='synthetic_bulk_wave_source', title='SYNTHETIC TEST ONLY', doi=None,
                      authors=[], year=None, urls=['https://example.invalid/bulk-wave'],
                      read_status='synthetic_unverified', role='synthetic_test_only',
                      claim_notes=['Synthetic appendability fixture, not scientific evidence.'])
        source['license'] = {'status': 'unknown', 'identifier': None}
        source['provenance'] = {'curation_date': '2026-10-02', 'method': 'Synthetic fixture only.'}
        additions = copy.deepcopy(records(candidate))
        for record in additions:
            record['id'] = 'synthetic_append_'+record['id']
            record['name'] = 'SYNTHETIC TEST ONLY '+record['id']
            record['version'] = '0.0.0-synthetic'
            record['evidence'].append({'source_id': source['id'], 'locator': None,
                                      'verification_status': 'synthetic_unverified',
                                      'verified_as': 'Not scientific evidence.'})
            record['evidence'].reverse()
            record['parameters'].reverse()
            record['verification'] = {'status': 'synthetic_unverified', 'independent_scientific_review': False,
                                      'gaps': ['No independent source inspection.']}
            record['limits'].append('Synthetic fixture only; no material interpretation.')
            for labels in candidate['locales']['languages'].values():
                labels['catalog_name_'+record['id']] = record['name']
        candidate['sources']['records'].append(source)
        candidate['claims']['records'].extend(additions)
        for ordering in ('forward', 'reverse', 'interleaved'):
            ordered = copy.deepcopy(candidate)
            if ordering == 'reverse':
                ordered['claims']['records'].reverse(); ordered['sources']['records'].reverse()
            elif ordering == 'interleaved':
                for kind in ('claims', 'sources'):
                    rows = ordered[kind]['records']
                    ordered[kind]['records'] = rows[1::2]+rows[::2]
            with self.subTest(ordering=ordering):
                validate_catalogs(ordered)
                validate_wave_records(ordered['claims']['records'], resolve_dependencies=True)
        # Fresh self-contained families also render independently of old IDs.
        rendered = render_catalog({'records': list(reversed(additions))}, 'claims')
        for record in additions:
            self.assertIn(record['id'], rendered)

    def test_required_new_labels_cannot_disappear_in_every_language(self):
        for key in LABELS+STATUS_LABELS+tuple('catalog_name_'+identifier for identifier in IDS):
            candidate = copy.deepcopy(self.catalogs)
            for labels in candidate['locales']['languages'].values():
                labels.pop(key)
            with self.subTest(key=key), self.assertRaises(CatalogValidationError):
                validate_catalogs(candidate)


if __name__ == '__main__':
    unittest.main()
