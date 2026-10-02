"""Closed catalog-only anisotropy contracts; rational arithmetic is synthetic only."""
import copy
from provenance_corrections import historical_record, historical_temperature_result
from fractions import Fraction as F
import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from materials_boundaries import evaluate, load_json
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.temperature import evaluate_temperature
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs
from catalog_fixtures import EXECUTABLE_IDS
from test_engine import ROOT, example

IDS = ('zener_cubic_elastic_anisotropy_index', 'universal_elastic_anisotropy_index')
PRL = 'ranganathan_ostoja_starzewski_2008_anisotropy'
JAM = 'ranganathan_ostoja_starzewski_ferrari_2011_anisotropy'
BOOK = 'zener_1948_elasticity_anelasticity'
KH = 'knowles_howie_2015_cubic_shear'


def records(catalogs=None):
    claims = read_catalog('claims') if catalogs is None else catalogs['claims']
    index = {r['id']:r for r in claims['records']}
    return [index[i] for i in IDS]


def synthetic_cubic(c11, c12, c44):
    """Test-only exact rational formulas; never parse or execute catalog strings."""
    c11,c12,c44 = map(F, (c11,c12,c44))
    d = c11-c12
    if min(d,c11+2*c12,c44) <= 0:
        raise ValueError('outside strictly stable cubic test domain')
    kv = kr = (c11+2*c12)/3
    gv = (d+3*c44)/5
    gr = 5*d*c44/(4*c44+3*d)
    a = 2*c44/d
    au = 5*gv/gr+kv/kr-6
    return a,au,kv,gv,gr


class AnisotropyCatalogTests(unittest.TestCase):
    def test_prior_science_and_existing_evidence_preserved(self):
        before=load_json(ROOT/'tests/fixtures/pre_anisotropy_records.json')
        for kind,previous in before.items():
            current={r['id']:historical_record(kind, r) for r in read_catalog(kind)['records']}
            for r in previous:
                for key,value in r.items():
                    with self.subTest(kind=kind,id=r['id'],key=key):
                        if key in ('evidence','claim_notes','urls'):
                            for entry in value:self.assertIn(entry,current[r['id']][key])
                        else:self.assertEqual(value,current[r['id']][key])

    def test_preexisting_numeric_outputs_and_temperature_behavior_unchanged(self):
        fixture=load_json(ROOT/'tests/fixtures/pre_anisotropy_outputs.json')
        def digest(value):
            return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,
                separators=(',',':'),allow_nan=False).encode()).hexdigest()
        for name,old in fixture['composite'].items():
            new=evaluate(load_json(ROOT/'examples'/name))
            new.pop('engine_version');self.assertEqual(digest(new),old)
        for case in fixture['temperature']:
            new=evaluate_temperature(case['input'])
            # The existing content-addressed result ID incorporates engine_version.
            new.pop('engine_version');new.pop('id')
            self.assertEqual(digest(historical_temperature_result(new)),case['sha256'])

    def test_definitions_are_dimensionless_catalog_only_relations(self):
        for r in records():
            self.assertEqual((r['claim_type'],r['direction'],r['bound_kind'],r['dependencies']),
                             ('model_relation','relation',None,[]))
            self.assertEqual((r['evaluation_support'],r['quantity_dimension'],r['si_unit']),
                             ('catalog_only','dimensionless','1'))
            self.assertFalse(r['verification']['independent_scientific_review'])
            for key in ('result','value','fit','computation','applicability','checks','criterion'):
                self.assertNotIn(key,r)
            self.assertTrue(all(p['dimension']=='pressure' and p['si_unit']=='Pa' for p in r['parameters']))
        self.assertEqual(records()[0]['formula_display'],'A=2*C44/(C11-C12)')
        self.assertEqual(records()[1]['formula_display'],'AU=5*GV/GR+KV/KR-6')

    def test_open_and_closed_zero_unbounded_and_isotropy_are_separate(self):
        for index,r in enumerate(records()):
            range_=r['index_range']
            self.assertEqual(range_['lower'],{'status':'finite','value':0,'inclusive':bool(index)})
            self.assertEqual(range_['upper'],{'status':'unbounded','scope':'stated_positive_definite_elastic_tensor_class'})
            self.assertEqual(range_['isotropy'],{'value':1-index,'condition':'if_and_only_if_elastic_isotropy_within_stated_scope'})
            self.assertNotIn('value',range_['upper']);self.assertNotIn('inclusive',range_['upper'])
            self.assertIn('not assert physical realization',' '.join(r['limits']))
            self.assertIn('sampled extrema',' '.join(r['limits']))
        self.assertEqual(records()[0]['index_range']['basis'],'derived_from_definition_and_strict_cubic_stability')
        self.assertEqual(records()[1]['index_range']['basis'],'source_stated_nonnegative_range_and_isotropy_equality')

    def test_complete_stability_and_voigt_domains(self):
        for r in records():
            a=r['required_assumptions']
            self.assertEqual(a['spatial_dimension'],3)
            self.assertEqual(a['stability'],'strictly_positive_definite_on_symmetric_strains')
            self.assertEqual(a['elastic_tensor'],'finite_real_with_minor_and_major_symmetries')
            self.assertEqual(a['reference_state'],'stress_free_equilibrium')
            self.assertEqual(a['stiffness_convention'],'engineering_voigt_order_11_22_33_23_13_12')
            self.assertIn('2epsilon_23',a['strain_vector'])
            self.assertNotIn('2sigma',a['stress_vector'])
            for token in ('positive-semidefinite','complex viscoelastic','2D','prestress','phonon','Kelvin/Mandel','S44=4*S2323'):
                self.assertIn(token,' '.join(r['limits']))
        self.assertEqual(records()[0]['required_assumptions']['axes'],'natural_cubic_crystallographic_100_axes')
        self.assertEqual(records()[0]['required_assumptions']['strict_cubic_conditions'],
                         'C11-C12>0_and_C11+2*C12>0_and_C44>0')

    def test_universal_full_inverse_separate_full_orientation_average(self):
        r=records()[1];a=r['required_assumptions']
        self.assertEqual(a['orientation_average'],'uniform_normalized_SO3_full_orientation_average')
        self.assertEqual(a['averaging_order'],'average_C_and_its_full_inverse_S_separately')
        self.assertEqual(a['compliance'],'full_tensor_inverse_equivalently_full_6_by_6_engineering_matrix_inverse')
        self.assertEqual(a['isotropic_projections'],'CV=3*KV*J+2*GV*D_and_SR=J/(3*KR)+D/(2*GR)')
        self.assertEqual({p['symbol'] for p in r['parameters']},{'GV','GR','KV','KR'})
        for token in ('texture-weighted','directions-only','Young moduli','not <C>^-1','two-phase composite'):
            self.assertIn(token,' '.join(r['limits']))

    def test_original_book_is_not_claimed_read_and_review_doi_not_misattributed(self):
        sources={s['id']:s for s in read_catalog('sources')['records']}
        book=sources[BOOK];self.assertIsNone(book['doi']);self.assertEqual(book['year'],1948)
        self.assertIn('original_book_not_inspected',book['read_status'])
        self.assertIsNone(book['license']['identifier'])
        evidence=next(e for e in records()[0]['evidence'] if e['source_id']==BOOK)
        self.assertIsNone(evidence['locator']);self.assertIn('not_inspected',evidence['verification_status'])
        self.assertFalse(any(s['doi']=='10.1021/j150474a017' for s in sources.values()))
        self.assertEqual(sources[PRL]['doi'],'10.1103/PhysRevLett.101.055504')
        self.assertEqual(sources[JAM]['doi'],'10.1115/1.4004553')
        self.assertEqual(sources[KH]['doi'],'10.1007/s10659-014-9506-1')
        for sid in (PRL,JAM,KH):self.assertIsNone(sources[sid]['license']['identifier'])
        self.assertIn('064501',' '.join(sources[JAM]['claim_notes']))
        self.assertIn('version unspecified',sources[KH]['license']['status'])

    def test_source_locator_and_visual_extraction_trap_preserved(self):
        u=records()[1]
        e=next(e for e in u['evidence'] if e['source_id']==JAM)
        self.assertIn('064501-1',e['locator']);self.assertIn('064501-2',e['locator'])
        self.assertIn('incorrectly rendered infinity as 1',e['verified_as'])
        self.assertIn('page_image',e['verification_status'])
        e=next(e for e in u['evidence'] if e['source_id']==PRL)
        self.assertIn('Eq. (10)',e['locator']);self.assertIn('published cubic',e['verified_as'])

    def test_rational_synthetic_cases_reciprocity_and_strict_boundaries(self):
        self.assertEqual(synthetic_cubic(200,100,50),(1,0,F(400,3),50,50))
        self.assertEqual(synthetic_cubic(200,100,25),(F(1,2),F(3,5),F(400,3),35,F(125,4)))
        self.assertEqual(synthetic_cubic(200,100,100),(2,F(3,5),F(400,3),80,F(500,7)))
        for inputs in ((200,100,0),(100,100,50),(100,-60,40),(100,120,50)):
            with self.assertRaises(ValueError):synthetic_cubic(*inputs)
        for t in (F(1,10**8),F(1,2),F(1),F(2),F(10**8)):
            a,au,*_=synthetic_cubic(200,100,50*t)
            self.assertEqual(a,t);self.assertEqual(au,F(6,5)*(t+1/t-2))
            self.assertEqual(au,synthetic_cubic(200,100,50/t)[1]);self.assertGreaterEqual(au,0)
        # Finite examples exceeding arbitrary test values are not a proof by sampling.
        self.assertGreater(synthetic_cubic(200,100,50*10**8)[1],10**8)
        self.assertGreater(synthetic_cubic(200,100,F(50,10**8))[1],10**8)

    def test_synthetic_shear_scaling_inverse_and_pressure_unit_invariance(self):
        for factor in (F(1,10**9),F(10**9)):
            self.assertEqual(synthetic_cubic(200*factor,100*factor,25*factor)[:2],(F(1,2),F(3,5)))
        # Kelvin C44 is 2G. Raw substitution would turn isotropic A=1 into 2.
        d,g=F(100),F(50)
        self.assertEqual(2*g/d,1);self.assertEqual(2*(2*g)/d,2)
        # Engineering S44=1/G while full tensor S2323=1/(4G).
        self.assertEqual(F(1,g),4*F(1,4*g))
        # Even scalar projection illustrates why inverse and averaging differ.
        self.assertNotEqual((F(1,2)+F(1,8))/2,1/((F(2)+F(8))/2))

    def test_canonical_queries_and_four_language_display(self):
        for lang in LANGUAGES:
            for r in records():
                label=translate('catalog_name_'+r['id'],lang)
                self.assertIn(r['id'],{x['id'] for x in query_catalog('claims',query=label)['records']})
                text=render_catalog({'records':[r]},'claims',lang)
                self.assertIn(label,text);self.assertIn(r['formula_display'],text)
                self.assertIn(translate('catalog_index_notice',lang),text)
                self.assertIn(translate('catalog_index_upper_unbounded',lang),text)
                self.assertNotIn('[missing:',text)
                self.assertNotIn(translate('catalog_model_notice',lang),text)
                self.assertIn('[0, infinity)' if r['id']==IDS[1] else '(0, infinity)',text)
        results=[]
        for lang in LANGUAGES:
            run=subprocess.run([sys.executable,'-m','materials_boundaries','catalog','claims','--query','anisotropy',
                '--claim-type','model_relation','--json','--lang',lang],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr);results.append(run.stdout)
            self.assertTrue(set(IDS)<={r['id'] for r in json.loads(run.stdout)['records']})
        self.assertEqual(len(set(results)),1)

    def test_poisoned_index_metadata_never_execute_join_or_plot(self):
        expected=evaluate(example());poisoned=read_catalog('claims')
        for r in poisoned['records']:
            if r['id'] in IDS:
                r.update(rule_id='raise_if_dispatched',formula_display='raise_if_executed()',quantity='poison_quantity')
                r['index_range']={'poison':'must_not_be_rendered'};r['evidence']=[{'source_id':'must_not_be_joined'}]
        original=read_catalog
        with patch('materials_boundaries.catalog.read_catalog',side_effect=AssertionError('no catalog dispatch')):
            self.assertEqual(evaluate(example()),expected)
        with patch('materials_boundaries.visualization.read_catalog',side_effect=lambda n:poisoned if n=='claims' else original(n)):
            bundle=build_comparison([example()],fractions=[0,.5,1])
        self.assertEqual({r['id'] for r in bundle['catalogs']['claims']['records']},set(EXECUTABLE_IDS))
        self.assertEqual(len(bundle['series']),8)
        serialized=json.dumps(bundle)+render_html(bundle)+render_svg(bundle,bundle['cases'][0]['id'])
        for token in (*IDS,'must_not_be_rendered','poison_quantity','must_not_be_joined'):
            self.assertNotIn(token,serialized)
        for args in [('anisotropy',IDS[0]),('evaluate','examples/synthetic-two-phase.json','--index',IDS[0])]:
            run=subprocess.run([sys.executable,'-m','materials_boundaries',*args],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode,2);self.assertEqual(run.stdout,'')


class AnisotropySchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalogs=load_catalogs(ROOT/'materials_boundaries/data')
        self.validator=Draft202012Validator(load_json(ROOT/'schemas/claims.schema.json'))

    def rejected(self,change,index=0):
        c=copy.deepcopy(self.catalogs);change(records(c)[index])
        self.assertTrue(list(self.validator.iter_errors(c['claims'])))
        with self.assertRaises(CatalogValidationError):validate_catalogs(c)

    def test_catalog_closed_families_and_comparison_schema_snapshot(self):
        self.validator.check_schema(self.validator.schema);validate_catalogs(self.catalogs)
        self.assertEqual(self.catalogs['claims']['schema_version'],'1.10.0')
        self.assertEqual(load_json(ROOT/'schemas/comparison.schema.json')['$defs']['claims'],self.validator.schema)
        for r in records(self.catalogs):r['parameters'].reverse()
        validate_catalogs(self.catalogs)

    def test_classification_formula_identity_execution_mutations_fail(self):
        for index in (0,1):
            for key,value in [('claim_type','theoretical_bound'),('claim_type','model_estimate'),('direction','upper'),
                ('direction','prediction'),('bound_kind','scalar_modulus_bound'),('dependencies',['voigt_shear']),
                ('evaluation_support','composite_evaluate'),('quantity_dimension','pressure'),('si_unit','Pa'),
                ('rule_id','unreviewed_index_v1'),('formula_display','A=1'),('value',1),('result',0)]:
                with self.subTest(index=index,key=key):self.rejected(lambda r:r.update({key:value}),index)
        self.rejected(lambda r:r.update(quantity=records()[1]['quantity']))

    def test_every_required_assumption_is_exact_and_mandatory(self):
        for index,record in enumerate(records(self.catalogs)):
            for key in record['required_assumptions']:
                with self.subTest(index=index,key=key):
                    self.rejected(lambda r:r['required_assumptions'].pop(key),index)
                    self.rejected(lambda r:r['required_assumptions'].update({key:'weakened'}),index)
            self.rejected(lambda r:r['required_assumptions'].update(extra=True),index)
            self.rejected(lambda r:r['required_assumptions'].update(spatial_dimension=True),index)
        for key,value in [('orientation_average','texture_weighted'),('compliance','componentwise_reciprocal'),
                          ('averaging_order','invert_averaged_C'),('stability','positive_semidefinite')]:
            self.rejected(lambda r:r['required_assumptions'].update({key:value}),1)

    def test_range_endpoint_status_inclusion_and_isotropy_mutations_fail(self):
        for index in (0,1):
            for change in (lambda r:r.pop('index_range'),
                lambda r:r['index_range'].update(classification='sampled_maximum'),
                lambda r:r['index_range'].update(basis='empirical_fit'),
                lambda r:r['index_range']['lower'].update(value=1),
                lambda r:r['index_range']['lower'].update(value=False),
                lambda r:r['index_range']['lower'].update(inclusive=1),
                lambda r:r['index_range']['lower'].update(inclusive=not bool(index)),
                lambda r:r['index_range']['upper'].update(status='unknown'),
                lambda r:r['index_range']['upper'].update(status='finite',value=1,inclusive=True),
                lambda r:r['index_range'].update(upper=None),
                lambda r:r['index_range']['upper'].update(value='Infinity'),
                lambda r:r['index_range']['upper'].update(value=float('inf')),
                lambda r:r['index_range']['upper'].update(value=float('nan')),
                lambda r:r['index_range']['upper'].update(scope='all_real_materials'),
                lambda r:r['index_range']['isotropy'].update(value=2),
                lambda r:r['index_range']['isotropy'].update(condition='sufficient_only'),
                lambda r:r['index_range'].update(independent_scientific_review=True)):
                with self.subTest(index=index,change=change):self.rejected(change,index)

    def test_parameter_units_identities_missing_duplicates_and_foreign_metadata_fail(self):
        for index in (0,1):
            for change in (lambda r:r.pop('parameters'),lambda r:r['parameters'].pop(),
                lambda r:r['parameters'].append(copy.deepcopy(r['parameters'][0])),
                lambda r:r['parameters'].__setitem__(1,copy.deepcopy(r['parameters'][0])),
                lambda r:r['parameters'][0].update(symbol='wrong'),
                lambda r:r['parameters'][0].update(si_unit='GPa'),
                lambda r:r['parameters'][0].update(dimension='dimensionless'),
                lambda r:r['parameters'][0].update(quantity='strength'),
                lambda r:r['parameters'][0].update(value=1),
                lambda r:r['parameters'][0].update(coefficient_units={'rate_unit':'m/cycle'})):
                with self.subTest(index=index,change=change):self.rejected(change,index)

    def test_index_range_cannot_be_attached_to_any_other_family(self):
        for old in self.catalogs['claims']['records']:
            if old['rule_id'] in {r['rule_id'] for r in records(self.catalogs)}:continue
            c=copy.deepcopy(self.catalogs)
            target=next(r for r in c['claims']['records'] if r['id']==old['id'])
            target['index_range']=copy.deepcopy(records()[0]['index_range'])
            with self.subTest(id=old['id']):
                self.assertTrue(list(self.validator.iter_errors(c['claims'])))
                with self.assertRaises(CatalogValidationError):validate_catalogs(c)

    def test_fresh_ids_sources_labels_and_evidence_append_under_exact_contract(self):
        for index in (0,1):
            c=copy.deepcopy(self.catalogs);r=copy.deepcopy(records(c)[index]);r['id']='synthetic_anisotropy_append_'+str(index)
            r['name']='SYNTHETIC TEST ONLY: existing index contract'
            source=copy.deepcopy(c['sources']['records'][-1]);source.update(id='synthetic_anisotropy_source_'+str(index),
                title='SYNTHETIC TEST ONLY; not literature',authors=[],year=None,doi=None,urls=['https://example.invalid/synthetic-anisotropy'],
                read_status='synthetic_fixture_not_a_paper',role='synthetic_test_only',claim_notes=['Not scientific evidence.'])
            source['license']={'status':'unknown','identifier':None}
            source['provenance']={'curation_date':'2026-10-02','method':'Synthetic fixture only; no source inspection.'}
            source['bundled_content']='Synthetic test data only.'
            r['verification']={'status':'synthetic_fixture_not_scientific_evidence','independent_scientific_review':False,
                               'gaps':['Appendability plumbing only; not a new scientific record.']}
            r['evidence']=[{'source_id':source['id'],'locator':None,'verification_status':'synthetic_unverified',
                           'verified_as':'Plumbing only; no scientific source inspection.'}]
            c['sources']['records'].append(source);c['claims']['records'].append(r)
            for labels in c['locales']['languages'].values():labels['catalog_name_'+r['id']]='SYNTHETIC TEST ONLY '+str(index)
            validate_catalogs(c)
            for language in LANGUAGES:
                broken=copy.deepcopy(c);broken['locales']['languages'][language].pop('catalog_name_'+r['id'])
                with self.assertRaises(CatalogValidationError):validate_catalogs(broken)
            broken=copy.deepcopy(c);broken['claims']['records'][-1]['evidence'][0]['source_id']='missing'
            with self.assertRaises(CatalogValidationError):validate_catalogs(broken)

    def test_parity_preserving_required_index_label_removal_fails(self):
        for key in ('catalog_index_range','catalog_index_isotropy',
                    'catalog_index_upper_unbounded','catalog_index_notice'):
            c=copy.deepcopy(self.catalogs)
            for labels in c['locales']['languages'].values():labels.pop(key)
            with self.subTest(key=key),self.assertRaisesRegex(CatalogValidationError,'required anisotropy display'):
                validate_catalogs(c)

    def test_strict_json_loader_rejects_nonfinite_range_numbers(self):
        for token in ('Infinity','NaN','1e999'):
            with tempfile.TemporaryDirectory() as directory:
                path=ROOT.__class__(directory)/'bad.json';path.write_text('{"index_range":{"upper":{"value":'+token+'}}}')
                with self.assertRaises(ValueError):load_json(path)


if __name__=='__main__':unittest.main()
