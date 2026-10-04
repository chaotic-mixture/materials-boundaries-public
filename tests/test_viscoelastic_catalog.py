"""Closed scalar viscoelastic metadata and test-only analytic synthetic checks.

No constitutive solver, fit, measured data or numerical material API is added.
The written original proof supplies the general argument; examples are checks.
"""
import copy
from fractions import Fraction as F
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from materials_boundaries._viscoelastic_contract import (
    DEFINITION_RULE, PRODUCT_RULE, VISCOELASTIC_CONTRACTS, validate_viscoelastic_records,
)
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES
from materials_boundaries.i18n import translate
from materials_boundaries.validation import load_json
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs
from test_bulk_wave_catalog import scientific_mutations, apply_mutation

ROOT = Path(__file__).resolve().parents[1]
IDS = ('scalar_viscoelastic_creep_relaxation_duality',
       'scalar_viscoelastic_creep_relaxation_product_bound')
RULES = (DEFINITION_RULE, PRODUCT_RULE)
SOURCES = ('hanyga2018scalar_anisotropic_duality', 'hanyga2019newtonian_relaxation')
CONTRACT = 'viscoelastic_contract'
WARNINGS = tuple('catalog_viscoelastic_'+k for k in
                 ('notice', 'conditions', 'regularity', 'attribution', 'range', 'limits'))


def records(catalogs=None):
    rows = read_catalog('claims')['records'] if catalogs is None else catalogs['claims']['records']
    index = {record['id']: record for record in rows}
    return [index[identifier] for identifier in IDS]


def synthetic_viscoelastic_catalogs(catalogs):
    """Idempotent fresh-ID pair for disposable appendability rehearsals only."""
    result = copy.deepcopy(catalogs)
    source_id = 'synthetic_viscoelastic_append_source'
    if any(s['id'] == source_id for s in result['sources']['records']):
        return result
    source = copy.deepcopy(result['sources']['records'][0])
    source.update(id=source_id, title='SYNTHETIC TEST ONLY viscoelastic append', authors=[],
                  year=None, doi=None, urls=['https://example.invalid/viscoelastic'],
                  read_status='synthetic_unverified', role='synthetic_test_only',
                  claim_notes=['Appendability fixture, not scientific evidence.'],
                  license={'status': 'unknown', 'identifier': None},
                  provenance={'curation_date': '2026-10-03', 'method': 'Synthetic fixture only.'},
                  bundled_content='synthetic_test_only')
    result['sources']['records'].append(source)
    additions = copy.deepcopy(records(result))
    for record in additions:
        record['id'] = 'synthetic_append_'+record['id']
        record['name'] = 'SYNTHETIC TEST ONLY '+record['id']
        record['version'] = '0.0.0-synthetic'
        record['dependencies'] = ['synthetic_append_'+d for d in record['dependencies']]
        record['parameters'].reverse()
        record['evidence'] = [{'source_id': source_id, 'locator': None,
                               'verification_status': 'synthetic_unverified',
                               'verified_as': 'Fixture only, not scientific evidence.'}]
        record['verification'] = {'status': 'synthetic_unverified',
                                  'independent_scientific_review': False,
                                  'gaps': ['No source inspection or scientific validation.']}
        record['limits'] = ['SYNTHETIC TEST ONLY.']
        for labels in result['locales']['languages'].values():
            labels['catalog_name_'+record['id']] = record['name']
    result['claims']['records'].extend(additions)
    return result


def simpson(function, t, n=2000):
    """Test-only quadrature of smooth analytic synthetic pairs, not a runtime API."""
    h = t/n
    return h/3*(function(0)+function(t)+sum(
        (4 if i % 2 else 2)*function(i*h) for i in range(1, n)))


class ViscoelasticAnalyticTests(unittest.TestCase):
    def test_maxwell_exact_laplace_identity(self):
        for p in (F(1, 7), F(1), F(8)):
            for r0 in (F(1, 2), F(5)):
                for tau in (F(1, 3), F(2), F(9)):
                    a = 1/tau
                    rhat = r0/(p+a)
                    jhat = (1/p+a/p**2)/r0
                    self.assertEqual(p*p*rhat*jhat, 1)

    def test_sls_exact_laplace_identity(self):
        for p in (F(1, 7), F(1), F(8)):
            for e in (F(1, 2), F(5)):
                for tau in (F(1, 3), F(2), F(9)):
                    a = 1/tau
                    rhat = e*(1/p+1/(p+a))
                    jhat = (1/p-F(1, 2)/(p+a/2))/e
                    self.assertEqual(p*p*rhat*jhat, 1)

    def test_direct_convolution_and_initial_jump(self):
        for t in (0.01, 0.2, 1.0, 4.0):
            for tau in (0.5, 2.0):
                r0, e = 7.0, 3.0
                pairs = ((lambda s: r0*math.exp(-s/tau),
                          lambda s: (1+s/tau)/r0,
                          lambda s: 1/(r0*tau), 1/r0),
                         (lambda s: e*(1+math.exp(-s/tau)),
                          lambda s: (1-0.5*math.exp(-s/(2*tau)))/e,
                          lambda s: math.exp(-s/(2*tau))/(4*e*tau), 1/(2*e)))
                for r, j, jp, j0 in pairs:
                    self.assertAlmostEqual(simpson(lambda s: r(t-s)*j(s), t), t, places=10)
                    derivative_convolution = simpson(lambda s: r(t-s)*jp(s), t)
                    self.assertAlmostEqual(j0*r(t)+derivative_convolution, 1, places=10)
                    # Dropping J0*R(t) gives a different answer in both pairs.
                    self.assertGreater(1-derivative_convolution, 0)
                    gap = simpson(lambda s: (r(t-s)-r(t))*jp(s), t)
                    self.assertAlmostEqual(gap, 1-r(t)*j(t), places=10)
                    self.assertGreater(r(t)*j(t), 0)
                    self.assertLessEqual(r(t)*j(t), 1)

    def test_maxwell_class_sharpness_and_elastic_endpoint(self):
        values = [(1+x)*math.exp(-x) for x in (0.001, 0.1, 1, 5, 20)]
        self.assertTrue(all(0<v<1 for v in values))
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertLess(values[-1], 1e-6)
        for r0 in (F(1, 3), F(1), F(19)):
            self.assertEqual(r0*(1/r0), 1)
        # Every target in (0,1) has a Maxwell x: continuous strictly decreasing
        # map, with endpoints 1 and 0. Bisection verifies representative targets.
        for target in (0.01, 0.25, 0.9):
            lo, hi = 0.0, 50.0
            for _ in range(80):
                x = (lo+hi)/2
                if (1+x)*math.exp(-x)>target: lo=x
                else: hi=x
            self.assertAlmostEqual((1+x)*math.exp(-x), target, places=14)

    def test_sls_exact_gap_and_nonmonotone_product(self):
        for q in (F(1, 20), F(1, 3), F(2, 3), F(19, 20)):
            product = (1+q*q)*(1-q/2)
            self.assertEqual(1-product, q*(1-q)**2/2)
            self.assertTrue(0<product<1)
        values = [(1+math.exp(-t))*(1-0.5*math.exp(-t/2)) for t in (0.01, 2*math.log(3), 15)]
        self.assertGreater(values[0], values[1])
        self.assertGreater(values[2], values[1])

    def test_unbounded_initial_slope_is_compatible_with_AC(self):
        # J(t)=J0+a sqrt(t) is Bernstein and AC. Substitution s=u^2 turns
        # its derivative integral into the constant a du, avoiding a fake
        # finite derivative value at zero. This is a regularity illustration.
        for t in (0.001, 0.5, 7):
            j0, a = 2.0, 3.0
            integral = simpson(lambda u: a, math.sqrt(t))
            self.assertAlmostEqual(j0+integral, j0+a*math.sqrt(t), places=11)
        self.assertGreater(3/(2*math.sqrt(1e-20)), 1e9)
        for row in records():
            self.assertIs(row[CONTRACT]['finite_interval_regularity']['finite_initial_slope_required'], False)
            self.assertIn('J0*delta_0', row[CONTRACT]['causal_conventions']['initial_creep_jump'])


class ViscoelasticCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs = load_catalogs(ROOT/'materials_boundaries/data')
        cls.schema = load_json(ROOT/'schemas/claims.schema.json')
        cls.validator = Draft202012Validator(cls.schema)

    def rejected(self, change, index=0, *, schema=True, dependency=False):
        candidate = copy.deepcopy(self.catalogs)
        row = records(candidate)[index]
        change(row)
        if schema:
            self.assertTrue(list(self.validator.iter_errors(candidate['claims'])))
        with self.assertRaises(CatalogValidationError): validate_catalogs(candidate)
        with self.assertRaises(ValueError):
            validate_viscoelastic_records(candidate['claims']['records'], resolve_dependencies=True)
        with patch('materials_boundaries.catalog.files') as resource:
            resource.return_value.joinpath.return_value.read_text.return_value = json.dumps(candidate['claims'])
            with self.assertRaises(ValueError): read_catalog('claims')
        # Render path independently validates a supplied malformed subset. A
        # malformed dependency resolves against a full supplied catalog here.
        with self.assertRaises(ValueError):
            render_catalog(candidate['claims'] if dependency else {'records':[row]}, 'claims')

    def test_current_schema_and_exact_eight_executable_pairs(self):
        self.validator.check_schema(self.schema)
        self.assertEqual(self.catalogs['claims']['schema_version'], '1.13.0')
        self.assertEqual(self.schema['$id'], 'urn:materials-boundaries:schema:claims:1.13.0')
        self.assertEqual(load_json(ROOT/'schemas/comparison.schema.json')['$defs']['claims'], self.schema)
        validate_catalogs(self.catalogs)
        self.assertEqual(len(BASE_RULES)+len(DERIVED_RULES), 8)
        for row in records(self.catalogs):
            self.assertEqual(row['evaluation_support'], 'catalog_only')
            self.assertNotIn(row['rule_id'], (*BASE_RULES, *DERIVED_RULES))
        self.assertEqual(records(self.catalogs)[1]['dependencies'], [IDS[0]])

    def test_every_closed_scientific_node_rejects_mutation(self):
        # A valid schema envelope is supplied for every mutation. Wrong-version
        # rejection must never stand in for checking the scientific mutation.
        for row in records(self.catalogs):
            for field in VISCOELASTIC_CONTRACTS[row['rule_id']]:
                changes = [((field,), 'delete', None), *scientific_mutations(row[field], (field,))]
                for path, operation, value in changes:
                    with self.subTest(id=row['id'], path=path, operation=operation):
                        mutated = copy.deepcopy(row)
                        apply_mutation(mutated, path, operation, value)
                        subset = {'schema_version': '1.13.0', 'records': [mutated]}
                        self.assertTrue(list(self.validator.iter_errors(subset)))
                        with self.assertRaises(ValueError): validate_viscoelastic_records([mutated])

    def test_required_scope_and_meaning_reject_all_public_paths(self):
        for index in (0, 1):
            for key in records(self.catalogs)[index]['required_assumptions']:
                self.rejected(lambda r, key=key: r['required_assumptions'].pop(key), index)
            for change in (
                lambda r: r[CONTRACT]['finite_interval_regularity'].update(finite_initial_slope_required=True),
                lambda r: r[CONTRACT]['causal_conventions'].update(initial_creep_jump='D(HJ)=H*J_prime'),
                lambda r: r[CONTRACT]['source_attribution'].update(passivity_equivalence_claimed=True),
                lambda r: r[CONTRACT]['source_attribution'].update(scientific_peer_review_certified=True),
                lambda r: r['parameters'][2].update(si_unit='1'),
                lambda r: r['parameters'][3].update(dimension='time'),
                lambda r: r.update(evaluation_support='composite_evaluate'),
                lambda r: r.update(rule_id='unknown_viscoelastic_relation_v1'),
            ): self.rejected(change, index)
        self.rejected(lambda r: r[CONTRACT]['range']['lower'].update(inclusive=True), 1)
        self.rejected(lambda r: r[CONTRACT]['range']['upper'].update(value=2), 1)

    def test_dependency_family_is_required_and_cannot_cycle(self):
        for value in ([], [IDS[1]], ['voigt_bulk'], ['missing'], [IDS[0], IDS[0]]):
            self.rejected(lambda r, value=value: r.update(dependencies=value), 1,
                          schema=len(value)!=1, dependency=True)
        self.rejected(lambda r: r.update(dependencies=[IDS[1]]), 0)
        # Filtering the admitted product alone resolves its packaged duality.
        self.assertIn(IDS[1], render_catalog({'records':[records(self.catalogs)[1]]}, 'claims'))

    def test_foreign_fields_bound_kind_and_time_units_cannot_expand_old_families(self):
        for original in self.catalogs['claims']['records']:
            if original['rule_id'] in RULES: continue
            for change in (
                lambda r: r.update(viscoelastic_contract=copy.deepcopy(records(self.catalogs)[0][CONTRACT])),
                lambda r: r.update(bound_kind='dimensionless_response_product_bound'),
                lambda r: r.update(parameters=[copy.deepcopy(records(self.catalogs)[0]['parameters'][2])]),
            ):
                candidate=copy.deepcopy(original); change(candidate)
                with self.subTest(id=original['id']):
                    self.assertTrue(list(self.validator.iter_errors({'schema_version':'1.13.0','records':[candidate]})))
                    with self.assertRaises(ValueError): validate_viscoelastic_records([candidate])
        for index in (0,1):
            for key in ('criterion','index_range','directional_contract','hydrostatic_compressibility_contract','bulk_wave_contract'):
                self.rejected(lambda r,key=key:r.update({key:{}}), index)

    def test_duplicate_ids_nonfinite_endpoints_and_parameter_duplicates_rejected(self):
        row=records(self.catalogs)[0]
        with self.assertRaises(ValueError): validate_viscoelastic_records([row,row])
        for value in (None, False, '0', float('inf'), float('nan')):
            self.rejected(lambda r,value=value:r[CONTRACT]['range']['lower'].update(value=value), 1)
        for index in (0,1):
            self.rejected(lambda r:r['parameters'].append(copy.deepcopy(r['parameters'][0])),index)

    def test_fresh_pair_sources_and_four_labels_remain_appendable(self):
        candidate=synthetic_viscoelastic_catalogs(self.catalogs)
        self.assertEqual(synthetic_viscoelastic_catalogs(candidate), candidate)
        for order in ('normal','reverse','interleaved'):
            ordered=copy.deepcopy(candidate)
            for kind in ('claims','sources'):
                rows=ordered[kind]['records']
                if order=='reverse':rows.reverse()
                elif order=='interleaved':ordered[kind]['records']=rows[1::2]+rows[::2]
            validate_catalogs(ordered)
            validate_viscoelastic_records(ordered['claims']['records'],resolve_dependencies=True)
        additions=[r for r in candidate['claims']['records'] if r['id'].startswith('synthetic_append_scalar_viscoelastic')]
        self.assertEqual(len(additions),2)
        self.assertIn(additions[1]['id'],render_catalog({'records':list(reversed(additions))},'claims'))

    def test_all_four_language_inspection_and_search_preserve_canonical_math(self):
        for lang in ('en','zh','ja','de'):
            for row in records(self.catalogs):
                text=render_catalog({'records':[row]},'claims',lang)
                self.assertNotIn('[missing:',text)
                self.assertIn(row['formula_display'],text)
                for key in WARNINGS:self.assertIn(translate(key,lang),text)
                self.assertIn('J0*delta_0',text)
                self.assertIn('finite_initial_slope_required',text)
            result=subprocess.run([sys.executable,'-m','materials_boundaries','catalog','claims',
                '--id',IDS[1],'--text','--lang',lang],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('0<R(t)*J(t)<=1',result.stdout)
        for source in SOURCES:
            self.assertEqual({r['id'] for r in query_catalog('claims',source_id=source)['records']},set(IDS))

    def test_required_warnings_may_not_disappear_from_all_languages(self):
        for key in WARNINGS+tuple('catalog_name_'+i for i in IDS):
            candidate=copy.deepcopy(self.catalogs)
            for labels in candidate['locales']['languages'].values():labels.pop(key)
            with self.subTest(key=key), self.assertRaises(CatalogValidationError):validate_catalogs(candidate)

    def test_source_versions_rights_and_original_proof_roles_are_explicit(self):
        source_index={r['id']:r for r in self.catalogs['sources']['records']}
        for identifier,version in zip(SOURCES,('1805.07275v1','1903.03814v8')):
            source=source_index[identifier]
            text=json.dumps(source)
            self.assertIn(version,text)
            self.assertIn('SHA-256',text)
            self.assertIsNone(source['license']['identifier'])
            self.assertEqual(source['license']['status'],'arxiv_nonexclusive_distribution_license')
            self.assertIn('no source PDF',text)
        for row in records(self.catalogs):
            self.assertIs(row['verification']['independent_scientific_review'],False)
            self.assertIn('original_project_proof',row[CONTRACT]['source_attribution']['product_bound'])
            self.assertIs(row[CONTRACT]['synthetic_examples']['measured_data'],False) if row['id']==IDS[1] else None


if __name__ == '__main__':
    unittest.main()
