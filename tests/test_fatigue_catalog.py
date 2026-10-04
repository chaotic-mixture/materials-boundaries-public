"""Closed empirical fatigue metadata; all arithmetic here is synthetic, not API."""
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator
from materials_boundaries import evaluate, load_json
from source_evidence_preservation import previous_record
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs
from catalog_fixtures import EXECUTABLE_IDS, evidence_for
from test_engine import ROOT, example

IDS = ('paris_erdogan_intermediate_growth', 'forman_terminal_acceleration_growth')


def selected(catalogs=None):
    records = read_catalog('claims')['records'] if catalogs is None else catalogs['claims']['records']
    lookup = {r['id']: r for r in records}
    return [lookup[i] for i in IDS]


class FatigueCatalogTests(unittest.TestCase):
    def test_preexisting_scientific_metadata_are_preserved(self):
        baseline = load_json(ROOT / 'tests/fixtures/pre_fatigue_records_sha256.json')
        for kind, expected in baseline.items():
            records = {r['id']: previous_record(kind, r) for r in read_catalog(kind)['records']}
            for name, digest in expected.items():
                with self.subTest(kind=kind, name=name):
                    # Evidence/notes may grow; reviewed provenance is guarded separately.
                    excluded = ({'claim_notes','urls','provenance','read_status','license','bundled_content'}
                                if kind == 'sources' else {'evidence','verification'})
                    payload = {k:v for k,v in records[name].items() if k not in excluded}
                    actual = hashlib.sha256(json.dumps(payload, sort_keys=True,
                        ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
                    self.assertEqual(actual, digest)

    def test_two_explicit_estimate_contracts_without_numbers_or_execution(self):
        for r in selected():
            self.assertEqual((r['claim_type'],r['direction'],r['bound_kind'],r['dependencies'],r['evaluation_support']),
                             ('model_estimate','prediction',None,[],'catalog_only'))
            self.assertEqual((r['quantity'],r['quantity_dimension'],r['si_unit']),
                             ('fatigue_crack_growth_rate','length_per_cycle','m/cycle'))
            self.assertFalse(r['verification']['independent_scientific_review'])
            for key in ('value','result','computation','applicability','checks','fit'):
                self.assertNotIn(key,r)
                for p in r['parameters']:
                    self.assertNotIn(key,p)
            self.assertTrue(any('No executable fatigue' in gap for gap in r['verification']['gaps']))
            self.assertTrue(any('safe-life guarantee' in limit for limit in r['limits']))

    def test_coefficient_units_are_exponent_and_equation_dependent(self):
        for r, symbol, exponent, power, unit in zip(selected(), ('C_P','C_F'), ('m','n'), ('-m','1-n'),
                ('m/cycle*(Pa*m^0.5)^(-m)','m/cycle*(Pa*m^0.5)^(1-n)')):
            p = {p['symbol']:p for p in r['parameters']}[symbol]
            self.assertEqual(p['si_unit'],unit)
            self.assertEqual(p['dimension'],'length_per_cycle_times_stress_intensity_power')
            self.assertEqual(p['coefficient_units'], {'rate_unit':'m/cycle', 'stress_intensity_unit':'Pa*m^0.5',
                'exponent_symbol':exponent,'stress_intensity_power':power,
                'cycle_count_convention':'complete_cycles_dimensionless_count'})

    def test_parameter_sets_and_cycle_crack_and_K_conventions(self):
        for r, extra in zip(selected(), ({'C_P','m'},{'C_F','n','Kc'})):
            ps = {p['symbol']:p for p in r['parameters']}
            self.assertEqual(set(ps), {'a','N','DeltaK','R','Kmax','Kmin'} | extra)
            self.assertEqual((ps['a']['quantity'],ps['a']['si_unit']),('crack_tip_advance_coordinate','m'))
            self.assertEqual((ps['N']['dimension'],ps['N']['si_unit']),('dimensionless','1'))
            self.assertIn('complete load cycles',ps['N']['meaning'])
            a = r['required_assumptions']
            self.assertEqual(a['stress_ratio_scope'],'0<=R<1')
            self.assertEqual(a['range_definition'],'DeltaK=Kmax-Kmin=(1-R)*Kmax')
            self.assertEqual(a['stress_ratio_definition'],'R=Kmin/Kmax')
            self.assertEqual(a['stress_intensity_convention'],'modern_K_I_sigma_yy_ahead_of_tip=K_I/sqrt(2*pi*r)')
            self.assertIn('half_length',a['crack_coordinate'])
            self.assertTrue(a['positive_Kmax_and_DeltaK'])

    def test_regime_and_positive_denominator_are_not_optional(self):
        paris, forman = selected()
        self.assertEqual(paris['required_assumptions']['stress_ratio_calibration'],'fixed_calibrated_R')
        self.assertIn('intermediate_region_II',paris['required_assumptions']['growth_regime'])
        self.assertEqual(forman['required_assumptions']['positive_denominator'],
                         '(1-R)*Kc-DeltaK>0_equivalently_Kmax<Kc')
        self.assertEqual(forman['required_assumptions']['instability_pole'],'excluded_not_a_finite_rate_prediction')
        self.assertIn('not_automatically_KIc',forman['required_assumptions']['fracture_toughness'])
        for r in (paris,forman):
            self.assertEqual(r['required_assumptions']['threshold_model'],'none')
            self.assertTrue(any('variable-amplitude' in x for x in r['limits']))
            self.assertTrue(any('No fitted constants' in x for x in r['limits']))

    def test_historical_and_modern_and_scope_evidence_are_separate(self):
        for r, eq, page, historical in zip(selected(), (45,48),(37,40),('paris_erdogan_1963','forman_kearney_engle_1967')):
            modern=evidence_for(r,'wilson_1992_nasa_tm_103591')
            self.assertIn(f'Eq. ({eq})',modern['locator']); self.assertIn(f'p. {page}',modern['locator'])
            old=evidence_for(r,historical)
            self.assertIsNone(old['locator'])
            self.assertEqual(old['verification_status'],'historical_attribution_original_equations_not_inspected')
            scope=evidence_for(r,'astm_e647_24_public_scope')
            self.assertIn('not equation evidence or fit-validation evidence',scope['verified_as'])
            hudson=evidence_for(r,'hudson_1969_nasa_tn_d_5390')
            self.assertIn('p. 8 Eq. (9)',hudson['locator'])
            self.assertIn('no constants transferred',hudson['verified_as'])

    def test_sources_preserve_read_and_license_limits(self):
        s={r['id']:r for r in read_catalog('sources')['records']}
        for name in ('paris_erdogan_1963','forman_kearney_engle_1967'):
            self.assertIn('inaccessible',s[name]['read_status'])
            self.assertIsNone(s[name]['license']['identifier'])
        self.assertEqual(s['afgrow_dtd_handbook_fatigue_growth']['authors'],[])
        self.assertIn('public_html',s['astm_e647_24_public_scope']['read_status'])
        self.assertIn('not_fit_validation',s['astm_e647_24_public_scope']['role'])
        self.assertTrue(any('sqrt(pi)' in x for x in s['hudson_1969_nasa_tn_d_5390']['claim_notes']))

    def test_queries_four_language_labels_and_canonical_JSON(self):
        for lang, query in zip(('en','zh','ja','de'),('fatigue','疲劳','疲労','Ermüdungsriss')):
            result=query_catalog('claims',query=query,claim_type='model_estimate')
            self.assertTrue(set(IDS)<={r['id'] for r in result['records']})
            rendered=render_catalog({'schema_version':read_catalog('claims')['schema_version'],'records':selected()},'claims',lang)
            self.assertNotIn('[missing:',rendered)
            for r in selected():
                self.assertIn(translate('catalog_name_'+r['id'],lang),rendered)
                self.assertIn(r['formula_display'],rendered)
                self.assertIn('m/cycle',rendered)
            self.assertIn(translate('catalog_model_notice',lang),rendered)

    def test_existing_runtime_and_plot_boundary_stays_eight(self):
        result=evaluate(example())
        self.assertEqual(tuple(r['claim_id'] for r in result['evaluations']),EXECUTABLE_IDS)
        bundle=build_comparison([example()])
        self.assertEqual({r['id'] for r in bundle['catalogs']['claims']['records']},set(EXECUTABLE_IDS))
        for lang in LANGUAGES:
            html=render_html(bundle,lang=lang)
            for name in IDS:self.assertNotIn(name,html)
        for name in IDS:self.assertNotIn(name,render_svg(bundle,bundle['cases'][0]['id']))

    def test_synthetic_unit_rescaling_does_not_reuse_coefficients(self):
        # Independent invented arithmetic, not material inputs or production evaluation.
        m,n=3.2,2.7; cp,cf=2e-30,3e-20; dk,kc,r=5e6,30e6,0.2
        paris=cp*dk**m; forman=cf*dk**n/((1-r)*kc-dk)
        s=1e6  # one MPa√m is 10^6 Pa√m
        self.assertAlmostEqual((cp*s**m)*(dk/s)**m/paris,1.0,places=14)
        self.assertAlmostEqual((cf*s**(n-1))*(dk/s)**n/((1-r)*(kc/s)-dk/s)/forman,1.0,places=14)
        self.assertFalse(math.isclose(cp*(dk/s)**m,paris,rel_tol=1e-6,abs_tol=0.0))
        self.assertFalse(math.isclose(cf*(dk/s)**n/((1-r)*(kc/s)-dk/s),forman,rel_tol=1e-6,abs_tol=0.0))

    def test_synthetic_historical_normalization_and_pole_identity(self):
        cp,cf,m,n,dk,kc,r=2.,3.,3.1,2.4,5.,30.,0.2
        scale=math.sqrt(math.pi)
        self.assertAlmostEqual(cp*dk**m,(cp*scale**(-m))*(scale*dk)**m,places=12)
        old=cf*dk**n/((1-r)*kc-dk)
        new=(cf*scale**(1-n))*(scale*dk)**n/((1-r)*(scale*kc)-scale*dk)
        self.assertAlmostEqual(old,new,places=12)
        for kmax in (5,29,30,31):
            delta=(1-r)*kmax
            self.assertAlmostEqual((1-r)*kc-delta,(1-r)*(kc-kmax))
        self.assertGreater((1-r)*kc-(1-r)*29,0)
        self.assertEqual((1-r)*kc-(1-r)*30,0)
        self.assertLess((1-r)*kc-(1-r)*31,0)


class FatigueContractSchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalogs=load_catalogs(ROOT/'materials_boundaries/data')
        self.validator=Draft202012Validator(load_json(ROOT/'schemas/claims.schema.json'))

    def assert_rejected(self, change, index=0):
        c=copy.deepcopy(self.catalogs);change(selected(c)[index])
        self.assertTrue(list(self.validator.iter_errors(c['claims'])))
        with self.assertRaises(CatalogValidationError):validate_catalogs(c)

    def test_new_contract_and_comparison_snapshot_validate(self):
        validate_catalogs(self.catalogs)
        self.assertEqual(self.catalogs['claims']['schema_version'],'1.13.0')
        self.assertEqual(load_json(ROOT/'schemas/comparison.schema.json')['$defs']['claims'],
                         load_json(ROOT/'schemas/claims.schema.json'))

    def test_classification_execution_dimension_and_formula_mutations_fail(self):
        for index in (0,1):
            for key,value in [('claim_type','theoretical_bound'),('direction','upper'),('bound_kind','scalar_modulus_bound'),
                              ('evaluation_support','composite_evaluate'),('quantity_dimension','pressure'),('si_unit','Pa'),
                              ('dependencies',['hs_bulk_3d_two_phase']),('rule_id','unreviewed_growth_v1'),
                              ('formula_display','da/dN=C*DeltaK')]:
                with self.subTest(index=index,key=key):self.assert_rejected(lambda r:r.update({key:value}),index)

    def test_complete_assumption_contract_mutations_fail(self):
        for index,record in enumerate(selected(self.catalogs)):
            for key in record['required_assumptions']:
                with self.subTest(index=index,key=key):
                    self.assert_rejected(lambda r:r['required_assumptions'].pop(key),index)
            for key,value in [('stress_ratio_scope','R<1'),('range_definition','DeltaK=Kmax'),
                              ('stress_intensity_convention','historical_k'),('cycle_count','reversals'),
                              ('loading','variable_amplitude'),('threshold_model','implicit')]:
                with self.subTest(index=index,key=key):self.assert_rejected(lambda r:r['required_assumptions'].update({key:value}),index)
        self.assert_rejected(lambda r:r['required_assumptions'].update(positive_denominator='>=0'),1)

    def test_coefficient_unit_expression_and_metadata_mutations_fail(self):
        for index in (0,1):
            for change in (
                lambda p:p.update(si_unit='1'),
                lambda p:p.update(dimension='dimensionless'),
                lambda p:p.pop('coefficient_units'),
                lambda p:p['coefficient_units'].update(rate_unit='m/s'),
                lambda p:p['coefficient_units'].update(stress_intensity_unit='MPa*m^0.5'),
                lambda p:p['coefficient_units'].update(exponent_symbol='q'),
                lambda p:p['coefficient_units'].update(stress_intensity_power='-n'),
                lambda p:p['coefficient_units'].update(cycle_count_convention='reversals'),
                lambda p:p.update(value=1.0),
            ):
                with self.subTest(index=index,change=change):self.assert_rejected(lambda r:change(r['parameters'][6]),index)
        other=copy.deepcopy(selected(self.catalogs)[1]['parameters'][6])
        self.assert_rejected(lambda r:r['parameters'].__setitem__(6,other))

    def test_parameter_shape_and_foreign_metadata_fail(self):
        for index in (0,1):
            self.assert_rejected(lambda r:r['parameters'].pop(),index)
            self.assert_rejected(lambda r:r['parameters'].append(copy.deepcopy(r['parameters'][0])),index)
            self.assert_rejected(lambda r:r['parameters'][0].update(quantity='total_crack_length'),index)
            self.assert_rejected(lambda r:r['parameters'][1].update(si_unit='s'),index)
            self.assert_rejected(lambda r:r['parameters'][0].update(coefficient_units=copy.deepcopy(r['parameters'][6]['coefficient_units'])),index)

    def test_same_family_new_ID_remains_appendable_with_authored_labels(self):
        for index in (0,1):
            c=copy.deepcopy(self.catalogs);record=copy.deepcopy(selected(c)[index])
            record['id']='synthetic_fatigue_append_'+str(index)
            record['name']='SYNTHETIC TEST ONLY: same reviewed fatigue contract'
            c['claims']['records'].append(record)
            for labels in c['locales']['languages'].values():labels['catalog_name_'+record['id']]='SYNTHETIC TEST ONLY: '+str(index)
            validate_catalogs(c)

    def test_foreign_coefficient_metadata_does_not_broaden_existing_contract(self):
        c=copy.deepcopy(self.catalogs)
        existing=next(r for r in c['claims']['records'] if r['id']=='griffith_central_crack_plane_stress')
        existing['parameters'][0]['coefficient_units']=selected(c)[0]['parameters'][6]['coefficient_units']
        with self.assertRaises(CatalogValidationError):validate_catalogs(c)


if __name__=='__main__':unittest.main()
