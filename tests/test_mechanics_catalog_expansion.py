"""Catalog-only strength/LEFM expansion: evidence and executable separation."""
import copy
import json
import math
import subprocess
import sys
import unittest
from unittest.mock import patch

from materials_boundaries import evaluate, load_json
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison
from catalog_fixtures import expected_evidence, expected_provenance
from test_engine import ROOT, example
from catalog_fixtures import (EXECUTABLE_IDS, CORE_STABILITY_IDS,
                              historical_records, select_records, evidence_for, isolated_catalogs)
try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

NEW_IDS = [
    'frenkel_slip_specific_ideal_shear', 'uber_normal_cohesive_strength',
    'lefm_central_crack_mode_i_stress_intensity', 'lefm_mode_i_energy_release_relation',
    'lefm_center_crack_finite_width_secant_factor',
]

def record(name):
    return query_catalog('claims', record_id=name)['records'][0]


class MechanicsCatalogExpansionTests(unittest.TestCase):
    def test_identifiers_references_and_no_implicit_composite_dependencies(self):
        claims, sources = read_catalog('claims'), read_catalog('sources')
        self.assertEqual(claims['schema_version'], '1.11.0')
        self.assertEqual(sources['schema_version'], '1.0.0')
        claim_ids = [r['id'] for r in claims['records']]
        source_ids = [r['id'] for r in sources['records']]
        self.assertEqual(len(set(claim_ids)), len(claim_ids))
        self.assertEqual(len(set(source_ids)), len(source_ids))
        self.assertEqual([r['id'] for r in select_records(claims, NEW_IDS)], NEW_IDS)
        for r in claims['records']:
            self.assertTrue(set(r['dependencies']) <= set(claim_ids))
            self.assertTrue(all(e['source_id'] in source_ids for e in r['evidence']))
        for r in select_records(claims, tuple(NEW_IDS) + CORE_STABILITY_IDS):
            self.assertEqual(r['evaluation_support'], 'catalog_only')
            self.assertIsNone(r['bound_kind'])
            self.assertEqual(r['dependencies'], [])
            self.assertEqual(r['verification']['independent_scientific_review'], expected_provenance('claims', r['id'])['verification']['independent_scientific_review'])
            for key in ('value', 'result', 'checks', 'computation', 'applicability'):
                self.assertNotIn(key, r)

    def test_strength_estimates_are_separate_from_relations_and_theoretical_bounds(self):
        self.assertTrue(set(NEW_IDS[2:]) <= {r['id'] for r in query_catalog('claims', claim_type='model_relation')['records']})
        for name in NEW_IDS[:2]:
            r=record(name)
            self.assertEqual((r['claim_type'], r['direction']), ('model_estimate','prediction'))
            self.assertEqual((r['quantity_dimension'], r['si_unit']), ('pressure', 'Pa'))
        for name in NEW_IDS[2:]:
            r=record(name)
            self.assertEqual((r['claim_type'], r['direction']), ('model_relation', 'relation'))
        self.assertEqual(query_catalog('claims', claim_type='model_relation', direction='upper')['records'], [])
        bound_ids = {r['id'] for r in query_catalog('claims', claim_type='theoretical_bound')['records']}
        self.assertTrue(set(NEW_IDS).isdisjoint(bound_ids))

    def test_slip_geometry_and_modulus_do_not_become_polycrystal_strength(self):
        r=record(NEW_IDS[0]);par={p['symbol']:p for p in r['parameters']}
        self.assertEqual(list(par), ['G_slip', 'b', 'h'])
        self.assertEqual(par['G_slip']['quantity'], 'slip_specific_shear_stiffness')
        self.assertIn('b/(2*pi*h)', r['formula_display'])
        self.assertTrue(any('unless b/h=1' in s for s in r['limits']))
        self.assertTrue(any('Hill/polycrystal' in s for s in r['limits']))
        history=next(e for e in r['evidence'] if e['source_id']=='frenkel_1926')
        self.assertEqual(history['verification_status'], expected_evidence('claims', r['id'], 'frenkel_1926')['verification_status'])
        self.assertIn('2108.06412v2',evidence_for(r, 'shimanek_2022_ideal_shear')['locator'])

    def test_uber_positive_separation_energy_local_opening_and_derivation(self):
        r=record(NEW_IDS[1]); par={p['symbol']:p for p in r['parameters']}
        self.assertEqual(list(par), ['W_sep', 'lambda', 'delta'])
        self.assertIn('e_b(0)=-W_sep',par['W_sep']['meaning'])
        self.assertIn('2*gamma only',par['W_sep']['meaning'])
        self.assertIn('local opening',par['delta']['meaning'])
        self.assertEqual(evidence_for(r, 'azocar_guzman_2020_hydrogen')['verification_status'], expected_evidence('claims', r['id'], 'azocar_guzman_2020_hydrogen')['verification_status'])
        self.assertTrue(any('Pa/m' in s and 'Young modulus' in s for s in r['limits']))
        self.assertTrue(any('sign ambiguity' in s for s in r['limits']))
        self.assertEqual(evidence_for(r, 'rose_ferrante_smith_1981')['verification_status'], expected_evidence('claims', r['id'], 'rose_ferrante_smith_1981')['verification_status'])

    def test_lefm_quantities_units_and_geometry_scope_are_distinct(self):
        intensity,energy,factor=[record(i) for i in NEW_IDS[2:]]
        self.assertEqual((intensity['quantity_dimension'],intensity['si_unit']),('stress_intensity','Pa*m^0.5'))
        self.assertEqual((energy['quantity_dimension'],energy['si_unit']),('energy_per_area','J/m^2'))
        self.assertEqual((factor['quantity_dimension'],factor['si_unit']),('dimensionless','1'))
        self.assertEqual(intensity['required_assumptions']['geometry'],'infinite_plate_central_through_crack')
        self.assertNotIn('geometry',energy['required_assumptions'])
        self.assertEqual(energy['parameters'][0]['quantity'],'mode_i_stress_intensity_factor')
        self.assertIn('plane strain',energy['formula_display'])
        self.assertTrue(any('not a shear modulus' in s for s in energy['limits']))

    def test_finite_width_range_conflict_and_plasticity_are_explicit(self):
        r=record(NEW_IDS[-1]); a=r['required_assumptions']
        self.assertEqual(a['width_convention'],'W_is_full_sheet_width')
        self.assertEqual(a['range'],'0<2a/W<=0.8')
        self.assertEqual(a['plasticity_correction'],'none_a_bar_equals_a')
        self.assertTrue(any('a/W<=0.8' in e['verified_as'] and 'internally inconsistent' in e['verified_as'] for e in r['evidence']))
        self.assertEqual(evidence_for(r, 'pierce_sullivan_1969_nasa_tn_d_5140')['source_id'], 'pierce_sullivan_1969_nasa_tn_d_5140')
        self.assertTrue(any('not an independently certified error bound' in x for x in r['limits']))
        self.assertTrue(any('gross remote tension' in x for x in r['limits']))

    def test_source_versions_reuse_rights_and_no_fulltexts_bundled(self):
        s={r['id']:r for r in read_catalog('sources')['records']}
        self.assertEqual(s['azocar_guzman_2020_hydrogen']['license'], expected_provenance('sources', s['azocar_guzman_2020_hydrogen']['id'])['license'])
        self.assertEqual(s['rose_ferrante_smith_1981']['license'], expected_provenance('sources', s['rose_ferrante_smith_1981']['id'])['license'])
        self.assertEqual(s['shimanek_2022_ideal_shear']['license'], expected_provenance('sources', s['shimanek_2022_ideal_shear']['id'])['license'])
        self.assertEqual(s['shimanek_2022_ideal_shear']['read_status'], expected_provenance('sources', s['shimanek_2022_ideal_shear']['id'])['read_status'])
        historical_sources = ('frenkel_1926', 'shimanek_2022_ideal_shear',
                              'rose_ferrante_smith_1981', 'van_der_ven_ceder_2004',
                              'azocar_guzman_2020_hydrogen', 'pierce_sullivan_1969_nasa_tn_d_5140',
                              'mouhat_coudert_2014_elastic_stability', 'roberts_garboczi_2002_porous',
                              'lee_wei_kysar_hone_2008')
        for r in (s[identifier] for identifier in historical_sources):
            self.assertEqual(r['bundled_content'], expected_provenance('sources', r['id'])['bundled_content'])
            self.assertEqual(r['provenance'], expected_provenance('sources', r['id'])['provenance'])

    def test_curated_names_are_literal_search_aliases_in_all_languages(self):
        names=read_catalog('locales')['languages']
        for lang in LANGUAGES:
            for id in NEW_IDS:
                label=names[lang]['catalog_name_'+id]
                matches=query_catalog('claims',query=label)['records']
                self.assertIn(id, [r['id'] for r in matches])
                text=render_catalog(query_catalog('claims',record_id=id),'claims',lang)
                self.assertIn(label,text)
                self.assertIn(record(id)['name'],text)
                self.assertIn(translate('translation_review_notice',lang),text)
                self.assertNotIn('[missing:',text)
        with isolated_catalogs():
            self.assertEqual(query_catalog('sources',query='有限宽度')['records'],[])
            self.assertEqual(query_catalog('claims',query='有限宽度 missing_term')['records'],[])

    def test_relation_cli_is_canonical_across_languages_and_does_not_execute(self):
        outputs=[]
        for lang in LANGUAGES:
            run=subprocess.run([sys.executable,'-m','materials_boundaries','catalog','claims','--claim-type','model_relation','--direction','relation','--json','--lang',lang],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr);outputs.append(run.stdout)
            matched=json.loads(run.stdout)['records']
            self.assertTrue(set(NEW_IDS[2:]) <= {r['id'] for r in matched})
            self.assertTrue(all(r['claim_type']=='model_relation' and r['direction']=='relation' for r in matched))
        self.assertEqual(len(set(outputs)),1)
        with self.assertRaises(ValueError):query_catalog('sources',claim_type='model_relation')

    def test_evaluator_and_visual_builder_never_execute_or_plot_catalog_only_records(self):
        catalog=read_catalog('claims')
        supported=[r['id'] for r in catalog['records'] if r['evaluation_support']=='composite_evaluate']
        out=evaluate(example());self.assertEqual([e['claim_id'] for e in out['evaluations']],list(EXECUTABLE_IDS))
        self.assertCountEqual(supported,EXECUTABLE_IDS)
        self.assertEqual(len(out['evaluations']),8)
        # Poison all catalog-only metadata. The engine ignores the catalog, and
        # the builder only joins the existing executable output IDs.
        poisoned=copy.deepcopy(catalog)
        for r in (r for r in poisoned['records'] if r['evaluation_support']=='catalog_only'):
            r['quantity']='unsupported_poison';r['formula_display']='raise_if_executed()'
            r['rule_id']='not_registered';r['evidence']=[{'source_id':'must_not_be_dereferenced'}]
        original_read=read_catalog
        with patch('materials_boundaries.visualization.read_catalog',side_effect=lambda name:poisoned if name=='claims' else original_read(name)):
            bundle=build_comparison([example()],fractions=[0,.5,1])
        self.assertEqual(len(bundle['series']),8)
        self.assertEqual([r['id'] for r in bundle['catalogs']['claims']['records']],supported)
        self.assertTrue(set(NEW_IDS).isdisjoint(s['claim_id'] for s in bundle['series']))
        self.assertNotIn('must_not_be_dereferenced',json.dumps(bundle))
        with patch('materials_boundaries.catalog.read_catalog',side_effect=AssertionError('must not dispatch models')):
            self.assertEqual(evaluate(example()),out)

    def test_independent_synthetic_arithmetic_is_not_a_runtime_calculator(self):
        # Arithmetic identities only. These invented inputs are not material data.
        g,b,h=80e9,2.5e-10,2e-10
        self.assertAlmostEqual(g*b/(2*math.pi*h)/1e9,15.915494309189533)
        w,length=2.,1e-10
        traction=lambda d:(w/length)*(d/length)*math.exp(-d/length)
        peak=w/(math.e*length)
        self.assertAlmostEqual(peak/1e9,7.357588823428847)
        self.assertAlmostEqual(traction(length)/peak,1.,places=14)
        self.assertLess(traction(.9*length),peak);self.assertLess(traction(1.1*length),peak)
        self.assertAlmostEqual(math.sqrt(w*(w/length**2))/math.e/peak,1.,places=14)
        sigma,a,e=1e6,.001,70e9
        ki=sigma*math.sqrt(math.pi*a)
        self.assertAlmostEqual(ki**2/e,math.pi*a*sigma**2/e)
        self.assertAlmostEqual(math.sqrt(1/math.cos(math.pi*1e-8)),1,places=14)
        self.assertGreater(math.sqrt(1/math.cos(math.pi*.4)),1)


@unittest.skipIf(Draft202012Validator is None,'optional jsonschema dev dependency not installed')
class ExpansionSchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalog=read_catalog('claims')
        self.validator=Draft202012Validator(load_json(ROOT/'schemas/claims.schema.json'))

    def invalid(self,record_id,mutation):
        bad=copy.deepcopy(self.catalog);mutation(select_records(bad, [record_id])[0])
        self.assertTrue(list(self.validator.iter_errors(bad)))

    def test_new_model_families_are_schema_valid(self):
        self.validator.validate(self.catalog)
        bad=copy.deepcopy(self.catalog);bad['schema_version']='1.2.0'
        self.assertTrue(list(self.validator.iter_errors(bad)))

    def test_parameter_order_is_not_an_executable_argument_contract(self):
        reordered=copy.deepcopy(self.catalog)
        for item in select_records(reordered, NEW_IDS):
            item['parameters'].reverse()
        self.validator.validate(reordered)

    def test_no_new_record_can_claim_bound_or_execution_or_wrong_direction(self):
        for index in NEW_IDS:
            for key,value in [('claim_type','theoretical_bound'),('bound_kind','scalar_modulus_bound'),('evaluation_support','composite_evaluate'),('dependencies',['hs_bulk_3d_two_phase']),('direction','upper')]:
                with self.subTest(index=index,key=key):self.invalid(index,lambda r:r.update({key:value}))
            self.invalid(index,lambda r:r.update(result={'value':1}))
        for index in NEW_IDS[2:]:self.invalid(index,lambda r:r.update(claim_type='model_estimate',direction='prediction'))

    def test_new_dimensions_and_parameter_semantics_fail_closed(self):
        for index in NEW_IDS:
            self.invalid(index,lambda r:r.pop('parameters'))
            self.invalid(index,lambda r:r['parameters'].pop())
            self.invalid(index,lambda r:r['parameters'].append(copy.deepcopy(r['parameters'][0])))
            self.invalid(index,lambda r:r['parameters'][0].update(quantity='not_the_same_quantity'))
            self.invalid(index,lambda r:r['parameters'][0].update(symbol='wrong_symbol'))
            self.invalid(index,lambda r:r['parameters'][0].update(si_unit='wrong_unit'))
        for index in NEW_IDS[2:]:self.invalid(index,lambda r:r.update(si_unit='Pa',quantity_dimension='pressure'))

    def test_defining_geometry_and_energy_conventions_are_required(self):
        for index,key,value in [(NEW_IDS[0],'slip_system','unspecified'),(NEW_IDS[1],'energy_reference','zero_at_equilibrium'),(NEW_IDS[2],'crack_length_convention','a_is_full_length'),(NEW_IDS[3],'plane_state','unknown'),(NEW_IDS[4],'range','0<a/W<=0.8'),(NEW_IDS[4],'width_convention','half_width')]:
            self.invalid(index,lambda r:r['required_assumptions'].update({key:value}))
            self.invalid(index,lambda r:r['required_assumptions'].pop(key))


if __name__=='__main__':unittest.main()
