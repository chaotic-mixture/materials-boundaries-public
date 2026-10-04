from provenance_corrections import public_previous_record
"""Directional catalog contracts and exact project algebra, never a tensor API."""
import copy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from materials_boundaries import evaluate, load_json
from materials_boundaries._directional_contract import (
    DEFINITION_RULE, PAIR_RULE, DIRECTIONAL_CONTRACTS, validate_directional_records)
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs
from catalog_fixtures import EXECUTABLE_IDS
from test_engine import ROOT, example

IDS = ('directional_poissons_ratio_definition_and_range',
       'directional_poisson_reciprocity_energy_constraint')
LABELS = ('catalog_directional_notice', 'catalog_directional_conditions',
          'catalog_directional_limits', 'catalog_directional_range',
          'catalog_directional_fixed_tensor', 'catalog_directional_pair',
          'catalog_status_directional_poissons_ratio')


def records(catalogs=None):
    catalog = read_catalog('claims') if catalogs is None else catalogs['claims']
    index = {r['id']: r for r in catalog['records']}
    return [index[i] for i in IDS]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def compliance(q, s0=F(1)):
    """Exact test-only construction, not an installed numerical service."""
    q, s0 = F(q), F(s0)
    if s0 <= 0:
        raise ValueError('positive compliance scale required')
    s = [[s0 * int(i == j) for j in range(6)] for i in range(6)]
    s[0][1] = s[1][0] = -q * s0
    s[1][1] = (1 + q*q) * s0
    return s


def quadratic(x, s, y):
    return sum(x[i] * s[i][j] * y[j] for i in range(6) for j in range(6))


def dyad_stress(n):
    return [n[0]**2, n[1]**2, n[2]**2, n[1]*n[2], n[0]*n[2], n[0]*n[1]]


class DirectionalAlgebraTests(unittest.TestCase):
    def test_arbitrary_finite_rational_q_construction_and_full_inverse(self):
        for q in map(F, (-10**12, -2, -1, '-0.1', 0, '0.5', 1, 4, 10**12)):
            for s0 in (F(1, 10**9), F(1), F(10**9)):
                s = compliance(q, s0)
                # Closed inverse of the full 6x6 matrix, including shear blocks.
                c = [[F(int(i == j), s0) for j in range(6)] for i in range(6)]
                c[0][0] = (1+q*q)/s0; c[0][1] = c[1][0] = q/s0
                for i in range(6):
                    for j in range(6):
                        self.assertEqual(sum(s[i][k]*c[k][j] for k in range(6)), int(i == j))
                self.assertEqual(-s[1][0]/s[0][0], q)
                e1, e2 = 1/s[0][0], 1/s[1][1]
                nu12, nu21 = q, q/(1+q*q)
                self.assertEqual(nu12/e1, nu21/e2)
                self.assertLess(nu12*nu12, e1/e2)
                self.assertGreaterEqual(nu12*nu21, 0)
                self.assertLess(nu12*nu21, 1)
                # The completed-square identity is exact, not evidence by sampling.
                for x in ([F(i+1) for i in range(6)], [q, F(1), 0, 0, 0, 0]):
                    form = s0*((x[0]-q*x[1])**2+sum(v*v for v in x[1:]))
                    self.assertEqual(quadratic(x, s, x), form)
                    self.assertGreater(form, 0)

    def test_isotropic_endpoints_are_valid_anisotropic_values(self):
        for q in (F(-1), F(1,2)):
            s = compliance(q)
            self.assertEqual(s[0][0]*s[1][1]-s[0][1]**2, 1)
            self.assertEqual(-s[1][0]/s[0][0], q)
        self.assertEqual(compliance(0)[0][1], 0)

    def test_small_strain_rescaling_exact_squared_norm(self):
        eta, s0 = F(1,10**8), F(1,10**9)
        for q in (F(-10**20), F(0), F(10**20)):
            t_squared = eta**2/(s0**2*(1+q*q))
            self.assertEqual(s0**2*t_squared*(1+q*q), eta**2)

    def test_general_direction_reciprocity_strict_pair_and_tensor_shear_factor(self):
        pairs = [((F(1),0,0),(0,F(1),0)),
                 ((F(3,5),F(4,5),0),(-F(4,5),F(3,5),0)),
                 ((0,F(3,5),F(4,5)),(0,-F(4,5),F(3,5)))]
        indices = [(0,0),(1,1),(2,2),(1,2),(0,2),(0,1)]
        for q in (F(-7), F(0), F(5)):
            s = compliance(q)
            raw = {}
            for I,(i,j) in enumerate(indices):
                for J,(k,l) in enumerate(indices):
                    v = s[I][J]/((1 if I<3 else 2)*(1 if J<3 else 2))
                    for a,b in {(i,j),(j,i)}:
                        for c,d in {(k,l),(l,k)}:raw[a,b,c,d] = v
            self.assertEqual(s[3][3], 4*raw[1,2,1,2])
            for n,m in pairs:
                self.assertEqual(sum(x*y for x,y in zip(n,m)),0)
                self.assertEqual(sum(x*x for x in n),1); self.assertEqual(sum(x*x for x in m),1)
                A,B = dyad_stress(n),dyad_stress(m)
                a,b,c = quadratic(A,s,A),quadratic(B,s,A),quadratic(B,s,B)
                raw_b = sum(m[i]*m[j]*raw[i,j,k,l]*n[k]*n[l]
                            for i in range(3) for j in range(3) for k in range(3) for l in range(3))
                self.assertEqual(b,raw_b); self.assertLess(b*b,a*c)
                nu,nur,En,Em = -b/a,-b/c,1/a,1/c
                self.assertEqual(nu/En,nur/Em); self.assertLess(nu*nu,En/Em)
                self.assertLess(nu*nur,1); self.assertGreaterEqual(nu*nur,0)
                self.assertEqual(nu == 0,nur == 0)

    def test_pair_constraints_are_not_full_stability_certificate(self):
        # Every coordinate pair has positive 2x2 compliance minor, but the
        # normal 3x3 block with off-diagonal -9/10 is indefinite.
        s = [[F(int(i==j)) for j in range(6)] for i in range(6)]
        for i in range(3):
            for j in range(3):
                if i != j:s[i][j] = F(-9,10)
        for i in range(3):
            for j in range(i+1,3):self.assertLess(s[i][j]**2,s[i][i]*s[j][j])
        self.assertLess(quadratic([1,1,1,0,0,0],s,[1,1,1,0,0,0]),0)
        # Equality has a nonzero zero-energy vector and is outside strict SPD.
        self.assertEqual(quadratic([1,-1,0,0,0,0],[[F(1) if i<2 and j<2 else F(i==j)
                         for j in range(6)] for i in range(6)],[1,-1,0,0,0,0]),0)


class DirectionalCatalogTests(unittest.TestCase):
    def test_accepted_v014_scientific_records_preserved_by_id(self):
        baseline = load_json(ROOT/'tests/fixtures/pre_directional_record_digests.json')
        for kind, snapshots in baseline.items():
            current = {r['id']: r for r in read_catalog(kind)['records']}
            for identifier, expected in snapshots.items():
                with self.subTest(kind=kind,id=identifier):
                    # Existing scientific fields and old evidence entries stay
                    # intact; later independent evidence/curation may accumulate.
                    r = public_previous_record(kind, current[identifier])
                    projection = {k:v for k,v in r.items() if k not in {'evidence','verification','provenance','claim_notes','urls'}}
                    self.assertEqual(digest(projection), expected['science_sha256'])
                    for key, old_digests in expected['append_only'].items():
                        self.assertTrue(set(old_digests) <= {digest(x) for x in r[key]})

    def test_closed_material_class_and_fixed_tensor_scopes(self):
        first,second = records()
        for r in (first,second):
            self.assertEqual(r['quantity'],'directional_poissons_ratio')
            self.assertEqual(r['evaluation_support'],'catalog_only')
            self.assertEqual(r['claim_type'],'model_relation');self.assertIsNone(r['bound_kind'])
            self.assertFalse(r['verification']['independent_scientific_review'])
            self.assertNotIn('index_range',r)
        c=first['directional_contract'];v=c['material_class_range']
        self.assertEqual(v['values'],'all_finite_real_numbers')
        self.assertFalse(v['infinite_values_attained'])
        self.assertEqual(v['lower'],{'status':'unbounded_below'})
        self.assertEqual(v['upper'],{'status':'unbounded_above'})
        self.assertTrue(c['fixed_tensor_extrema']['minimum_attained'])
        self.assertTrue(c['fixed_tensor_extrema']['maximum_attained'])
        self.assertEqual(second['directional_contract']['stability_implication'],'necessary_not_sufficient_for_full_SPD')

    def test_source_attribution_and_project_derivations_not_peer_review(self):
        sources={r['id']:r for r in read_catalog('sources')['records']}
        for sid in ('ting_chen_2005_poisson_unbounded','norris_2006_cubic_poisson','norris_2006_anisotropic_extrema'):
            self.assertIn(sid,sources);self.assertIsNone(sources[sid]['license']['identifier'])
        self.assertIn('abstract',sources['ting_chen_2005_poisson_unbounded']['read_status'])
        self.assertIn('full_text_not_inspected',sources['ting_chen_2005_poisson_unbounded']['read_status'])
        for r in records():self.assertIn('original_project_algebra',r['directional_contract']['derivation_status'])
        doc=(ROOT/'docs/DIRECTIONAL_POISSON.md').read_text()
        for token in ('1+q²','Cauchy','compact','S_eng','Lempriere'):
            self.assertIn(token,doc)

    def test_four_language_catalog_names_conditions_limits_and_json(self):
        canonical=[]
        for language in LANGUAGES:
            for r in records():
                label=translate('catalog_name_'+r['id'],language)
                self.assertIn(r['id'],{x['id'] for x in query_catalog('claims',query=label)['records']})
                text=render_catalog({'records':[r]},'claims',language)
                for key in ('catalog_directional_notice','catalog_directional_conditions','catalog_directional_limits'):
                    self.assertIn(translate(key,language),text)
                self.assertIn(label,text);self.assertIn(r['formula_display'],text);self.assertNotIn('[missing:',text)
            run=subprocess.run([sys.executable,'-m','materials_boundaries','catalog','claims','--id',IDS[0],
                                '--json','--lang',language],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr);canonical.append(run.stdout)
        self.assertEqual(len(set(canonical)),1)

    def test_exact_eight_rule_registry_and_no_directional_dispatch_or_plot(self):
        self.assertEqual({r[0] for r in (*BASE_RULES,*DERIVED_RULES)},set(EXECUTABLE_IDS))
        self.assertEqual(len(BASE_RULES)+len(DERIVED_RULES),8)
        expected=evaluate(example());poison=read_catalog('claims')
        for r in poison['records']:
            if r['id'] in IDS:r.update(formula_display='raise_if_executed()',quantity='poison_quantity')
        original=read_catalog
        with patch('materials_boundaries.catalog.read_catalog',side_effect=AssertionError('no catalog dispatch')):
            self.assertEqual(evaluate(example()),expected)
        with patch('materials_boundaries.visualization.read_catalog',side_effect=lambda n:poison if n=='claims' else original(n)):
            bundle=build_comparison([example()],fractions=[0,.5,1])
        self.assertEqual({r['id'] for r in bundle['catalogs']['claims']['records']},set(EXECUTABLE_IDS))
        self.assertEqual(len(bundle['series']),8)
        text=json.dumps(bundle)+render_html(bundle)+render_svg(bundle,bundle['cases'][0]['id'])
        for token in (*IDS,'poison_quantity','raise_if_executed'):self.assertNotIn(token,text)


class DirectionalSchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalogs=load_catalogs(ROOT/'materials_boundaries/data')
        self.validator=Draft202012Validator(load_json(ROOT/'schemas/claims.schema.json'))

    def rejected(self,change,index=0,schema=True):
        c=copy.deepcopy(self.catalogs);change(records(c)[index])
        if schema:self.assertTrue(list(self.validator.iter_errors(c['claims'])))
        with self.assertRaises(CatalogValidationError):validate_catalogs(c)
        with self.assertRaises(ValueError):validate_directional_records(c['claims']['records'],resolve_dependencies=True)
        with self.assertRaises(ValueError):render_catalog({'records':[records(c)[index]]},'claims')

    def test_schema_snapshot_and_parameter_reordering(self):
        self.validator.check_schema(self.validator.schema);validate_catalogs(self.catalogs)
        self.assertEqual(self.catalogs['claims']['schema_version'],'1.12.0')
        self.assertEqual(load_json(ROOT/'schemas/comparison.schema.json')['$defs']['claims'],self.validator.schema)
        records(self.catalogs)[1]['parameters'].reverse();validate_catalogs(self.catalogs)

    def test_identity_formula_quantity_and_execution_mutations(self):
        for index in (0,1):
            for key,value in [('quantity','effective_poissons_ratio'),('claim_type','theoretical_bound'),
                              ('direction','interval'),('bound_kind','derived_outer_envelope'),
                              ('quantity_dimension','pressure'),('si_unit','Pa'),('evaluation_support','composite_evaluate'),
                              ('formula_display','nu(n,m)=nu(m,n)'),('rule_id','unreviewed_directional_v1'),
                              ('value',float('inf')),('criterion',{})]:
                with self.subTest(index=index,key=key):self.rejected(lambda r:r.update({key:value}),index)
            self.rejected(lambda r:r.pop('directional_contract'),index)
            self.rejected(lambda r:r.update(index_range=next(x for x in read_catalog('claims')['records'] if x['id']=='universal_elastic_anisotropy_index')['index_range']),index)

    def test_every_assumption_is_mandatory_and_exact(self):
        for index,r in enumerate(records(self.catalogs)):
            for key in r['required_assumptions']:
                with self.subTest(index=index,key=key):
                    self.rejected(lambda r:r['required_assumptions'].pop(key),index)
                    self.rejected(lambda r:r['required_assumptions'].update({key:'weakened'}),index)
            self.rejected(lambda r:r['required_assumptions'].update(extra=True),index)
        for key,value in [('loading','uniaxial_strain'),('spatial_dimension',2),('stability','positive_semidefinite'),
                          ('directions','arbitrary_nonorthogonal'),('compliance','componentwise_reciprocals'),
                          ('shear_conversion','S_eng_44=S2323')]:
            self.rejected(lambda r:r['required_assumptions'].update({key:value}))

    def test_scope_endpoints_unknown_and_fake_infinity_rejected(self):
        changes=[lambda c:c['material_class_range'].update(scope='one_fixed_tensor'),
                 lambda c:c['material_class_range'].update(values='extended_reals'),
                 lambda c:c['material_class_range'].update(infinite_values_attained=True),
                 lambda c:c['material_class_range']['lower'].update(status='unknown'),
                 lambda c:c['material_class_range']['upper'].update(status='finite',value=0.5),
                 lambda c:c['fixed_tensor_extrema'].update(values='unbounded'),
                 lambda c:c['fixed_tensor_extrema'].update(minimum_attained=False),
                 lambda c:c['fixed_tensor_extrema'].update(maximum_attained=False)]
        for value in ('Infinity','NaN',None,float('inf'),float('nan')):
            changes.append(lambda c,v=value:c['material_class_range']['upper'].update(value=v))
        for change in changes:self.rejected(lambda r:change(r['directional_contract']))
        for change in (lambda c:c['magnitude_constraint'].update(strict=False),
                       lambda c:c['magnitude_constraint'].update(equality_attained=True),
                       lambda c:c['pair_product']['lower'].update(inclusive=False),
                       lambda c:c['pair_product']['upper'].update(inclusive=True),
                       lambda c:c['pair_product']['upper'].update(value=True),
                       lambda c:c.update(stability_implication='sufficient'),
                       lambda c:c.update(universal_finite_numerical_bound=True),
                       lambda c:c['reciprocity'].update(expression='nu(n,m)=nu(m,n)')):
            self.rejected(lambda r:change(r['directional_contract']),1)

    def test_pair_parameters_and_dependency_family_are_closed(self):
        for change in (lambda r:r.pop('parameters'),lambda r:r['parameters'].pop(),
                       lambda r:r['parameters'].append(copy.deepcopy(r['parameters'][0])),
                       lambda r:r['parameters'][0].update(si_unit='GPa'),
                       lambda r:r['parameters'][0].update(meaning='other material modulus'),
                       lambda r:r.update(dependencies=[]),lambda r:r.update(dependencies=[IDS[0],IDS[0]])):
            self.rejected(change,1)
        self.rejected(lambda r:r.update(dependencies=['poissons_ratio_outer']),1,schema=False)
        self.rejected(lambda r:r.update(dependencies=['missing']),1,schema=False)
        self.rejected(lambda r:r.update(dependencies=[IDS[1]]),1,schema=False)
        self.rejected(lambda r:r.update(dependencies=[IDS[1]]))

    def test_directional_metadata_cannot_attach_to_other_families(self):
        for old in self.catalogs['claims']['records']:
            if old['rule_id'] in DIRECTIONAL_CONTRACTS:continue
            c=copy.deepcopy(self.catalogs)
            target=next(r for r in c['claims']['records'] if r['id']==old['id'])
            target['directional_contract']=copy.deepcopy(records()[0]['directional_contract'])
            with self.subTest(id=old['id']):
                self.assertTrue(list(self.validator.iter_errors(c['claims'])))
                with self.assertRaises(CatalogValidationError):validate_catalogs(c)
                with self.assertRaises(ValueError):validate_directional_records(c['claims']['records'])

    def test_fresh_ids_sources_and_evidence_append_and_reorder(self):
        c=copy.deepcopy(self.catalogs);definition,pair=copy.deepcopy(records(c))
        definition['id']='synthetic_directional_definition';pair['id']='synthetic_directional_pair'
        pair['dependencies']=[definition['id']]
        source=copy.deepcopy(next(s for s in c['sources']['records'] if s['id']=='norris_2006_anisotropic_extrema'))
        source.update(id='synthetic_directional_source',title='SYNTHETIC TEST ONLY',doi=None,authors=[],year=None,
                      urls=['https://example.invalid/directional'],read_status='synthetic_unverified',role='synthetic_test_only',
                      claim_notes=['Not scientific evidence.'])
        source['license']={'status':'unknown','identifier':None}
        source['provenance']={'curation_date':'2026-10-02','method':'Synthetic appendability test only.'}
        for r in (definition,pair):
            r['name']='SYNTHETIC TEST ONLY';r['evidence']=[{'source_id':source['id'],'locator':None,
                'verification_status':'synthetic_unverified','verified_as':'Not scientific evidence.'}]
            r['verification']={'status':'synthetic_unverified','independent_scientific_review':False,'gaps':['No source inspection.']}
            for labels in c['locales']['languages'].values():labels['catalog_name_'+r['id']]='SYNTHETIC TEST ONLY'
        c['sources']['records'].append(source);c['claims']['records'].extend([pair,definition])
        c['claims']['records'].reverse();c['sources']['records'].reverse();validate_catalogs(c)
        # Required-label omissions fail even if all four languages omit the key.
        for key in LABELS:
            broken=copy.deepcopy(c)
            for labels in broken['locales']['languages'].values():labels.pop(key)
            with self.assertRaises(CatalogValidationError):validate_catalogs(broken)

    def test_strict_json_nonfinite_numbers_fail(self):
        for token in ('Infinity','-Infinity','NaN','1e999'):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'bad.json';p.write_text('{"directional_contract":{"value":'+token+'}}')
                with self.assertRaises(ValueError):load_json(p)

    def test_duplicate_ids_cannot_shadow_malformed_rendered_metadata(self):
        canonical = records()[0]
        bad = copy.deepcopy(canonical)
        bad['directional_contract']['material_class_range']['infinite_values_attained'] = True
        for supplied in ([bad, canonical], [canonical, bad], [canonical, canonical]):
            with self.assertRaises(ValueError):
                render_catalog({'records': supplied}, 'claims')
            with self.assertRaises(ValueError):
                validate_directional_records(supplied)


if __name__=='__main__':unittest.main()
