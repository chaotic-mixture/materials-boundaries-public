"""Closed yield-criterion metadata and original test-only exact algebra.

Synthetic tensors supplement the written proof; no material evaluator is added.
"""
import copy
from fractions import Fraction as F
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from materials_boundaries import evaluate, load_json
from materials_boundaries._yield_contract import (
    VON_MISES_RULE, TRESCA_RULE, RATIO_RULE, YIELD_CONTRACTS, validate_yield_records,
)
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES
from materials_boundaries.i18n import translate
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs
from test_bulk_wave_catalog import scientific_mutations, apply_mutation

ROOT = Path(__file__).resolve().parents[1]
IDS = ('von_mises_initial_yield_relation', 'tresca_initial_yield_relation',
       'tresca_von_mises_equivalent_stress_ratio_bound')
RULES = (VON_MISES_RULE, TRESCA_RULE, RATIO_RULE)
SOURCES = ('giraldo_londono_paulino_2020_yield_criteria',
           'wierzbicki_2013_structural_plasticity')
CONTRACT = 'yield_criterion_contract'
WARNINGS = tuple('catalog_yield_'+key for key in
                 ('notice', 'tensor', 'normalization', 'math_scope',
                  'physical_scope', 'attribution', 'limits'))


def records(catalogs=None):
    rows = read_catalog('claims')['records'] if catalogs is None else catalogs['claims']['records']
    index = {row['id']: row for row in rows}
    return [index[identifier] for identifier in IDS]


def synthetic_yield_catalogs(catalogs):
    """Fresh-ID triple for disposable appendability rehearsals, never evidence."""
    result = copy.deepcopy(catalogs)
    source_id = 'synthetic_yield_append_source'
    if any(s['id'] == source_id for s in result['sources']['records']):
        return result
    source = copy.deepcopy(result['sources']['records'][0])
    source.update(id=source_id, title='SYNTHETIC TEST ONLY yield append', authors=[],
                  year=None, doi=None, urls=['https://example.invalid/yield'],
                  read_status='synthetic_unverified', role='synthetic_test_only',
                  claim_notes=['Appendability fixture, not scientific evidence.'],
                  license={'status': 'unknown', 'identifier': None},
                  provenance={'curation_date': '2026-10-04', 'method': 'Synthetic fixture only.'},
                  bundled_content='synthetic_test_only')
    result['sources']['records'].append(source)
    additions = copy.deepcopy(records(result))
    for row in additions:
        row['id'] = 'synthetic_append_'+row['id']
        row['name'] = 'SYNTHETIC TEST ONLY '+row['id']
        row['version'] = '0.0.0-synthetic'
        row['dependencies'] = ['synthetic_append_'+d for d in reversed(row['dependencies'])]
        row['parameters'].reverse()
        row['evidence'] = [{'source_id': source_id, 'locator': None,
                            'verification_status': 'synthetic_unverified',
                            'verified_as': 'Fixture only, not scientific evidence.'}]
        row['verification'] = {'status': 'synthetic_unverified',
                               'independent_scientific_review': False,
                               'gaps': ['No source inspection or scientific validation.']}
        row['limits'] = ['SYNTHETIC TEST ONLY.']
        for labels in result['locales']['languages'].values():
            labels['catalog_name_'+row['id']] = row['name']
    result['claims']['records'].extend(additions)
    return result


def principal_values_squared(values):
    """Test-only q_VM^2 and q_T^2 from synthetic exact principal stresses."""
    a, b, c = values
    return ((a-b)**2+(b-c)**2+(c-a)**2)/2, (max(values)-min(values))**2


def tensor_qvm_squared(sigma):
    mean = sum(sigma[i][i] for i in range(3))/3
    s = [[sigma[i][j]-mean*int(i==j) for j in range(3)] for i in range(3)]
    return F(3, 2)*sum(s[i][j]**2 for i in range(3) for j in range(3))


class YieldOriginalAlgebraTests(unittest.TestCase):
    def test_exact_gap_identities_and_endpoint_conditions(self):
        for i, j in itertools.product(range(21), repeat=2):
            a, b = F(i, 7), F(j, 11)
            qvm2, qt2 = a*a+a*b+b*b, (a+b)**2
            self.assertEqual(qt2-qvm2, a*b)
            self.assertEqual(F(4, 3)*qvm2-qt2, (a-b)**2/3)
            self.assertLessEqual(qvm2, qt2)
            self.assertLessEqual(qt2, F(4, 3)*qvm2)
            if a+b:
                self.assertEqual(qt2==qvm2, a*b==0)
                self.assertEqual(qt2==F(4, 3)*qvm2, a==b)

    def test_uniaxial_pure_shear_and_hydrostatic_endpoints(self):
        for magnitude in (F(1, 3), F(1), F(19)):
            self.assertEqual(principal_values_squared((magnitude,F(0),F(0))),
                             (magnitude*magnitude,magnitude*magnitude))
            self.assertEqual(principal_values_squared((magnitude,F(0),-magnitude)),
                             (3*magnitude*magnitude,4*magnitude*magnitude))
        for p in (F(-19),F(0),F(7,13)):
            self.assertEqual(principal_values_squared((p,p,p)),(0,0))
        # Approaches to the hydrostatic point have different ratios: no unique
        # extension at zero follows from continuity of the separate functions.
        self.assertEqual(principal_values_squared((F(1,10**9),F(0),F(0)))[0], F(1,10**18))
        self.assertNotEqual(1, F(4,3))

    def test_sign_permutation_and_hydrostatic_shift_invariance(self):
        for values in ((F(7),F(2),F(-3)),(F(4,9),F(4,9),F(-5,7)),(F(0),)*3):
            expected=principal_values_squared(values)
            for perm in itertools.permutations(values):
                for sign in (-1,1):
                    for shift in (F(-9,2),F(0),F(11)):
                        self.assertEqual(principal_values_squared(tuple(sign*v+shift for v in perm)),expected)

    def test_orthogonal_rotation_and_tensor_shear_convention(self):
        # Rational orthogonal matrix with a fully three-dimensional direction.
        u=(F(1,3),F(2,3),F(2,3))
        rotation=[[F(int(i==j))-2*u[i]*u[j] for j in range(3)] for i in range(3)]
        for i,j in itertools.product(range(3),repeat=2):
            self.assertEqual(sum(rotation[i][k]*rotation[j][k] for k in range(3)),int(i==j))
        for principal in ((F(8),F(3),F(-5)),(F(2),F(0),F(-2)),(F(9),)*3):
            sigma=[[sum(rotation[i][k]*principal[k]*rotation[j][k] for k in range(3))
                    for j in range(3)] for i in range(3)]
            self.assertEqual(tensor_qvm_squared(sigma),principal_values_squared(principal)[0])
            # Eigenvalues are known by construction; rotation cannot change q_T.
            for k in range(3):
                for i in range(3):
                    self.assertEqual(sum(sigma[i][j]*rotation[j][k] for j in range(3)),
                                     principal[k]*rotation[i][k])
        shear=[[F(0),F(5),F(0)],[F(5),F(0),F(0)],[F(0)]*3]
        self.assertEqual(tensor_qvm_squared(shear),75)

    def test_same_Y_local_proportional_ray_and_different_shear_calibration(self):
        for a,b in ((F(0),F(2)),(F(3),F(3)),(F(2),F(7))):
            qvm,qt=math.sqrt(a*a+a*b+b*b),a+b
            for y in (0.5,9.0):
                lambda_t,lambda_vm=y/float(qt),y/qvm
                self.assertAlmostEqual(lambda_vm/lambda_t,float(qt)/qvm)
                self.assertTrue(1<=lambda_vm/lambda_t<=2/math.sqrt(3)+1e-14)
        tau_c=4.0
        y_t,y_vm=2*tau_c,math.sqrt(3)*tau_c
        self.assertNotEqual(y_t,y_vm)
        self.assertEqual(y_t/2,tau_c)
        self.assertEqual(y_vm/math.sqrt(3),tau_c)


class YieldCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs=load_catalogs(ROOT/'materials_boundaries/data')
        cls.schema=load_json(ROOT/'schemas/claims.schema.json')
        cls.validator=Draft202012Validator(cls.schema)

    def rejected(self,change,index=0,*,schema=True,dependency=False):
        candidate=copy.deepcopy(self.catalogs);row=records(candidate)[index];change(row)
        if schema:self.assertTrue(list(self.validator.iter_errors(candidate['claims'])))
        with self.assertRaises(CatalogValidationError):validate_catalogs(candidate)
        with self.assertRaises(ValueError):validate_yield_records(candidate['claims']['records'],resolve_dependencies=True)
        with patch('materials_boundaries.catalog.files') as resource:
            resource.return_value.joinpath.return_value.read_text.return_value=json.dumps(candidate['claims'])
            with self.assertRaises(ValueError):read_catalog('claims')
        with self.assertRaises(ValueError):
            render_catalog(candidate['claims'] if dependency else {'records':[row]},'claims')

    def test_schema_and_eight_executable_boundary(self):
        self.validator.check_schema(self.schema)
        self.assertEqual(self.catalogs['claims']['schema_version'],'1.13.0')
        self.assertEqual(self.schema['$id'],'urn:materials-boundaries:schema:claims:1.13.0')
        comparison=load_json(ROOT/'schemas/comparison.schema.json')
        self.assertEqual(comparison['$defs']['claims'],self.schema)
        validate_catalogs(self.catalogs)
        self.assertEqual(len(BASE_RULES)+len(DERIVED_RULES),8)
        for row in records(self.catalogs):
            self.assertEqual(row['evaluation_support'],'catalog_only')
            self.assertNotIn(row['rule_id'],(*BASE_RULES,*DERIVED_RULES))
        output=evaluate(load_json(ROOT/'examples/synthetic-two-phase.json'))
        self.assertEqual(len(output['evaluations']),8)
        self.assertTrue(set(IDS).isdisjoint(e['claim_id'] for e in output['evaluations']))

    def test_every_closed_scientific_node_rejects_mutation(self):
        for row in records(self.catalogs):
            for field in YIELD_CONTRACTS[row['rule_id']]:
                changes=[((field,),'delete',None),*scientific_mutations(row[field],(field,))]
                for path,operation,value in changes:
                    with self.subTest(id=row['id'],path=path,operation=operation):
                        candidate=copy.deepcopy(row);apply_mutation(candidate,path,operation,value)
                        self.assertTrue(list(self.validator.iter_errors({'schema_version':'1.13.0','records':[candidate]})))
                        with self.assertRaises(ValueError):validate_yield_records([candidate])

    def test_scientific_distinctions_reject_all_public_paths(self):
        for index in (0,1,2):
            for key in records(self.catalogs)[index]['required_assumptions']:
                self.rejected(lambda r,key=key:r['required_assumptions'].pop(key),index)
            for change in (
                lambda r:r[CONTRACT]['source_normalization'].update(source_sigma_eq='sigma_eq=q_in_Pa'),
                lambda r:r[CONTRACT]['stress_conventions'].update(tensor_shear='engineering_shear'),
                lambda r:r[CONTRACT]['catalog_boundary'].update(numerical_evaluator=True),
                lambda r:r[CONTRACT]['physical_interpretation'].update(common_calibration='different_Y_allowed'),
                lambda r:r.update(evaluation_support='composite_evaluate'),
                lambda r:r.update(rule_id='unknown_yield_relation_v1'),
            ):self.rejected(change,index)
        self.rejected(lambda r:r[CONTRACT]['range']['lower'].update(inclusive=False),2)
        self.rejected(lambda r:r[CONTRACT]['range']['upper'].update(exact_value='sqrt(3)/2'),2)
        self.rejected(lambda r:r[CONTRACT]['hydrostatic_behavior'].update(ratio_at_zero=1),2)
        self.rejected(lambda r:r[CONTRACT]['mathematical_domain'].update(yield_calibration_Y_required=True),2)
        self.rejected(lambda r:r[CONTRACT]['conditional_loading_consequence'].update(path='arbitrary_load_path'),2)
        self.rejected(lambda r:r[CONTRACT]['definition'].update(ordered_form='q_T=tau_max'),1)
        self.rejected(lambda r:r[CONTRACT]['definition'].update(equivalent_stress='q_VM=3*J2'),0)

    def test_definition_dependencies_and_fresh_family_resolution(self):
        for index in (0,1):self.rejected(lambda r:r.update(dependencies=[IDS[2]]),index)
        for value in ([],[IDS[0]],[IDS[0],IDS[0]],[IDS[0],IDS[2]],['voigt_bulk',IDS[1]],['missing',IDS[1]]):
            self.rejected(lambda r,value=value:r.update(dependencies=value),2,
                          schema=len(value)!=2 or len(set(value))!=len(value),dependency=True)
        self.assertIn(IDS[2],render_catalog({'records':[records(self.catalogs)[2]]},'claims'))
        candidate=synthetic_yield_catalogs(self.catalogs)
        self.assertEqual(synthetic_yield_catalogs(candidate),candidate)
        for order in ('normal','reverse','interleaved'):
            c=copy.deepcopy(candidate)
            for kind in ('claims','sources'):
                if order=='reverse':c[kind]['records'].reverse()
                elif order=='interleaved':c[kind]['records']=c[kind]['records'][1::2]+c[kind]['records'][::2]
            validate_catalogs(c)
            validate_yield_records(c['claims']['records'],resolve_dependencies=True)
        additions=[r for r in candidate['claims']['records'] if r['id'].startswith('synthetic_append_') and r['rule_id'] in RULES]
        self.assertEqual(len(additions),3)
        self.assertIn(additions[2]['id'],render_catalog({'records':additions[::-1]},'claims'))

    def test_foreign_metadata_and_units_cannot_expand_older_families(self):
        j2=next(p for p in records(self.catalogs)[0]['parameters'] if p['symbol']=='J2')
        for original in self.catalogs['claims']['records']:
            if original['rule_id'] in RULES:continue
            for change in (lambda r:r.update(yield_criterion_contract={}),
                           lambda r:r.update(bound_kind='criterion_function_comparison'),
                           lambda r:r.update(parameters=[copy.deepcopy(j2)])):
                row=copy.deepcopy(original);change(row)
                with self.subTest(id=original['id']):
                    self.assertTrue(list(self.validator.iter_errors({'schema_version':'1.13.0','records':[row]})))
                    with self.assertRaises(ValueError):validate_yield_records([row])
        for index in (0,1,2):
            for key in ('criterion','index_range','directional_contract','bulk_wave_contract','viscoelastic_contract'):
                self.rejected(lambda r,key=key:r.update({key:{}}),index)

    def test_duplicate_ids_parameters_and_wrong_numeric_types(self):
        row=records(self.catalogs)[0]
        with self.assertRaises(ValueError):validate_yield_records([row,row])
        for value in (True,None,'1',float('inf'),float('nan')):
            self.rejected(lambda r,value=value:r[CONTRACT]['range']['lower'].update(value=value),2)
        for index in (0,1,2):
            self.rejected(lambda r:r['parameters'].append(copy.deepcopy(r['parameters'][0])),index)

    def test_four_language_inspection_and_source_search(self):
        for language in ('en','zh','ja','de'):
            for row in records(self.catalogs):
                text=render_catalog({'records':[row]},'claims',language)
                self.assertNotIn('[missing:',text)
                self.assertIn(row['formula_display'],text)
                for key in WARNINGS:self.assertIn(translate(key,language),text)
                self.assertIn('sigma_eq_VM=q_VM/Y',text)
                self.assertIn('undefined_0/0',text)
                for mode in ('--text','--json'):
                    result=subprocess.run([sys.executable,'-m','materials_boundaries','catalog','claims','--id',row['id'],mode,'--lang',language],cwd=ROOT,capture_output=True,text=True)
                    self.assertEqual(result.returncode,0,result.stderr)
                    if mode=='--json':self.assertEqual(json.loads(result.stdout)['records'],[row])
            for source in SOURCES:
                self.assertEqual({r['id'] for r in query_catalog('claims',source_id=source)['records']},set(IDS))
                self.assertNotIn('[missing:',render_catalog(query_catalog('sources',record_id=source),'sources',language))

    def test_required_four_language_labels_cannot_disappear(self):
        for key in WARNINGS+tuple('catalog_name_'+i for i in IDS):
            candidate=copy.deepcopy(self.catalogs)
            for labels in candidate['locales']['languages'].values():labels.pop(key)
            with self.subTest(key=key),self.assertRaises(CatalogValidationError):validate_catalogs(candidate)

    def test_source_rights_hashes_and_proof_attribution(self):
        sources={r['id']:r for r in self.catalogs['sources']['records']}
        for identifier,sha in zip(SOURCES,('ca6e6d895fd16caa46ad3f68bcd1272425317c268cd332b837732d362bec482c', 'b4a19b30e6fa5a7f79ed8e003b06b4c434799ebc44c016aeb751e498f126ea49')):
            # Exact source artifact identities are metadata, not bundled assets.
            text=json.dumps(sources[identifier])
            self.assertIn('SHA-256',text)
            self.assertIn(sha,text)
            self.assertEqual(sources[identifier]['bundled_content'],'bibliographic_metadata_mathematical_facts_and_original_curation_only')
        self.assertIsNone(sources[SOURCES[0]]['license']['identifier'])
        self.assertEqual(sources[SOURCES[1]]['license']['identifier'],'CC-BY-NC-SA-4.0')
        for row in records(self.catalogs):
            self.assertIs(row['verification']['independent_scientific_review'],False)
            self.assertEqual(row[CONTRACT]['source_attribution']['comparison_proof'],'original_project_algebra_not_a_separately_printed_source_theorem')
            self.assertFalse(row[CONTRACT]['source_attribution']['scientific_peer_review_certified'])
        ratio=records(self.catalogs)[2][CONTRACT]
        self.assertFalse(ratio['mathematical_domain']['yield_calibration_Y_required'])
        self.assertFalse(ratio['mathematical_domain']['physical_isotropy_required'])
        self.assertFalse(ratio['range']['actual_material_yield_bracket'])
        self.assertFalse(ratio['synthetic_examples']['measured_data'])


if __name__=='__main__':unittest.main()
