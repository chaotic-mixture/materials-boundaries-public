"""Independent mechanical references and the v0.2 typed/dependent result contract."""
import copy
from decimal import Inexact, localcontext
from fractions import Fraction as F
import json
import math
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from materials_boundaries import ValidationError, __version__, evaluate, load_json
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.cli import _render
from materials_boundaries.i18n import LANGUAGES, translate
from catalog_fixtures import expected_evidence, expected_provenance
from test_engine import ROOT, example

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None


def results(data=None, unit='GPa'):
    return {item['claim_id']: item for item in evaluate(data or example(), output_unit=unit)['evaluations']}


def endpoints(data=None, unit='GPa'):
    return {key: item['result'] for key, item in results(data, unit).items()}


def reference(k1, g1, k2, g2, f1):
    """Independent Fraction reference-phase contrast expressions, not engine R."""
    f2=1-f1
    kl=k1+f2/(1/(k2-k1)+f1/(k1+F(4,3)*g1))
    ku=k2+f1/(1/(k1-k2)+f2/(k2+F(4,3)*g2))
    a1=2*(k1+2*g1)/(5*g1*(k1+F(4,3)*g1))
    a2=2*(k2+2*g2)/(5*g2*(k2+F(4,3)*g2))
    gl=g1+f2/(1/(g2-g1)+f1*a1)
    gu=g2+f1/(1/(g1-g2)+f2*a2)
    e=lambda k,g:9*k*g/(3*k+g)
    nu=lambda k,g:(3*k-2*g)/(2*(3*k+g))
    return {'hs_bulk_3d_two_phase':(kl,ku),'hs_shear_3d_two_phase':(gl,gu),
            'youngs_modulus_outer':(e(kl,gl),e(ku,gu)),
            'poissons_ratio_outer':(nu(kl,gu),nu(ku,gl))}


class MechanicalTests(unittest.TestCase):
    def test_synthetic_exact_rational_references(self):
        r=endpoints()
        expected={'hs_shear_3d_two_phase':(F(310,37),F(190,21)),
                  'youngs_modulus_outer':(F(36270,1691),F(11970,517)),
                  'poissons_ratio_outer':(F(515,1942),F(529,1802))}
        for claim,(lo,hi) in expected.items():
            self.assertEqual(r[claim]['lower'],float(lo))
            self.assertEqual(r[claim]['upper'],float(hi))
        self.assertEqual(r['reuss_shear'],{'lower':7.5,'unit':'GPa'})
        self.assertEqual(r['voigt_shear'],{'upper':10.0,'unit':'GPa'})

    def test_reference_phase_exact_rational_cases(self):
        for k1,g1,k2,g2,f in [(2,1,8,5,F(1,4)),(7,2,19,11,F(3,10)),(1,1,10,10,F(1,2))]:
            data=example()
            for p,k,g,v in zip(data['phases'],(k1,k2),(g1,g2),(f,1-f)):
                p['bulk_modulus']['value']=k;p['shear_modulus']['value']=g;p['volume_fraction']=float(v)
            actual=endpoints(data)
            for claim,(lo,hi) in reference(*map(F,(k1,g1,k2,g2)),f).items():
                self.assertEqual(actual[claim]['lower'],float(lo))
                self.assertEqual(actual[claim]['upper'],float(hi))

    def test_literature_mechanical_results(self):
        r=endpoints(load_json(ROOT/'examples/literature-epoxy-glass-model.json'))
        for claim,expected in {
            'hs_shear_3d_two_phase':(1.6957767868938821,4.5508614156519983),
            'youngs_modulus_outer':(4.6205011542489514,11.756850801553002),
            'poissons_ratio_outer':(.18004295511520440,.41498174666051666)}.items():
            for side,v in zip(('lower','upper'),expected):self.assertAlmostEqual(r[claim][side],v,places=12)

    def test_equal_shear_collapses_shear_and_derived_intervals(self):
        data=example();data['phases'][1]['shear_modulus']['value']=5
        r=endpoints(data)
        for key in ('hs_shear_3d_two_phase','reuss_shear','voigt_shear'):
            for side in ('lower','upper'):
                if side in r[key]:self.assertEqual(r[key][side],5)
        # HS bulk also collapses for equal G, hence the derived interval collapses.
        self.assertEqual(r['youngs_modulus_outer']['lower'],r['youngs_modulus_outer']['upper'])

    def test_equal_bulk_keeps_paired_shear_order(self):
        data=example();data['phases'][1]['bulk_modulus']['value']=10
        r=endpoints(data);data['phases'].reverse()
        self.assertEqual(endpoints(data),r)
        self.assertEqual(r['hs_bulk_3d_two_phase']['lower'],10)
        self.assertLess(r['hs_shear_3d_two_phase']['lower'],r['hs_shear_3d_two_phase']['upper'])

    def test_identical_phases_and_pure_phase_exact_collapse(self):
        for k,g in [(10,5),(2,3),(1,4)]:
            for present in (None,0,1):
                data=example()
                for i,p in enumerate(data['phases']):
                    p['bulk_modulus']['value']=k;p['shear_modulus']['value']=g
                    if present is not None:
                        p['volume_fraction']=int(i==present)
                        if i!=present:p['bulk_modulus']=p['shear_modulus']=None
                r=endpoints(data)
                for claim,value in [('hs_bulk_3d_two_phase',k),('hs_shear_3d_two_phase',g),
                                    ('youngs_modulus_outer',float(F(9*k*g,3*k+g))),
                                    ('poissons_ratio_outer',float(F(3*k-2*g,2*(3*k+g))))]:
                    self.assertEqual(r[claim]['lower'],value)
                    self.assertEqual(r[claim]['upper'],value)

    def test_auxetic_and_zero_poisson_are_not_rejected_as_nonpositive(self):
        for g,expected in [(1.5,0),(6,-.5)]:
            data=example()
            for p in data['phases']:
                p['bulk_modulus']['value']=1;p['shear_modulus']['value']=g
            r=results(data)['poissons_ratio_outer']
            self.assertEqual(r['computation'],'computed')
            self.assertEqual(r['result']['lower'],expected)

    def test_phase_swap_with_unequal_fractions_preserves_pairs(self):
        data=example();data['phases'][0]['volume_fraction']=.23;data['phases'][1]['volume_fraction']=.77
        expected=endpoints(data);data['phases'].reverse()
        self.assertEqual(endpoints(data),expected)

    def test_unknown_and_violated_dependencies_suppress_derived(self):
        for field,value,state in [('effective_symmetry',None,'unknown'),('constituent_symmetry','anisotropic','violated')]:
            data=example();data['conditions'][field]=value
            for item in results(data).values():
                self.assertEqual(item['applicability'],state);self.assertIsNone(item['result'])
                self.assertEqual(item['computation'],'not_computed')
        for prop in ('bulk_modulus','shear_modulus','volume_fraction'):
            data=example();data['phases'][0][prop]=None
            for item in results(data).values():self.assertEqual(item['applicability'],'unknown')

    def test_non_well_ordered_suppresses_both_hs_and_derived_without_fallback(self):
        data=example();data['phases'][1]['shear_modulus']['value']=1
        r=results(data)
        for claim,item in r.items():
            expected='satisfied' if claim.startswith(('reuss_','voigt_')) else 'violated'
            self.assertEqual(item['applicability'],expected)
            if expected=='violated':self.assertIsNone(item['result'])

    def test_violated_dominates_unknown_for_dependent_claims(self):
        data=example();data['phases'][0]['shear_modulus']=None;data['conditions']['loading']='dynamic'
        for claim in ('youngs_modulus_outer','poissons_ratio_outer'):
            r=results(data)[claim];self.assertEqual(r['applicability'],'violated')
            self.assertTrue({'unknown','violated'}.issubset({c['state'] for c in r['checks']}))

    def test_mixed_units_all_outputs(self):
        data=example();data['phases'][0]['shear_modulus']={'value':5000,'unit':'MPa'}
        data['phases'][1]['bulk_modulus']={'value':30000000000,'unit':'Pa'}
        self.assertEqual(endpoints(data),endpoints())
        a,b=endpoints(data),endpoints(data,'MPa')
        for claim in a:
            for side in ('lower','upper'):
                if side in a[claim]:
                    factor=1 if claim=='poissons_ratio_outer' else 1000
                    self.assertAlmostEqual(b[claim][side],factor*a[claim][side],places=10)
            self.assertEqual(b[claim]['unit'],'1' if claim=='poissons_ratio_outer' else 'MPa')

    def test_uniform_scale_changes_moduli_not_poisson(self):
        r=endpoints()
        for scale in (1e-100,1e-6,1e100):
            data=example()
            for p in data['phases']:
                for prop in ('bulk_modulus','shear_modulus'):p[prop]['value']*=scale
            for claim,result in endpoints(data).items():
                for side in ('lower','upper'):
                    if side in result:
                        factor=1 if claim=='poissons_ratio_outer' else scale
                        self.assertAlmostEqual(result[side]/factor,r[claim][side],places=11)

    def test_extreme_contrast_moduli_finite_poisson_boundary_error(self):
        data=example()
        for p,v in zip(data['phases'],(1e-250,1e250)):
            p['bulk_modulus']['value']=p['shear_modulus']['value']=v
        for claim,item in results(data).items():
            if claim=='poissons_ratio_outer':
                self.assertEqual(item['computation'],'numerical_range_error');self.assertIsNone(item['result'])
            else:
                self.assertEqual(item['computation'],'computed')
                for side in ('lower','upper'):
                    if side in item['result']:self.assertTrue(math.isfinite(item['result'][side]) and item['result'][side]>0)

    def test_poisson_open_interval_float_boundary_is_not_clipped(self):
        for k,g in [(1e100,1),(1,1e100)]:
            data=example()
            for p in data['phases']:p['bulk_modulus']['value']=k;p['shear_modulus']['value']=g
            r=results(data)
            self.assertEqual(r['youngs_modulus_outer']['computation'],'computed')
            self.assertEqual(r['poissons_ratio_outer']['applicability'],'satisfied')
            self.assertEqual(r['poissons_ratio_outer']['computation'],'numerical_range_error')
            self.assertIn('no clipping',r['poissons_ratio_outer']['error'])
            self.assertIsNone(r['poissons_ratio_outer']['result'])

    def test_derived_depends_on_available_serialized_hs_bounds(self):
        data=example()
        for p in data['phases']:p['bulk_modulus']['value']=p['shear_modulus']['value']=1e308
        for item in results(data,'Pa').values():
            self.assertEqual(item['applicability'],'satisfied')
            self.assertEqual(item['computation'],'numerical_range_error');self.assertIsNone(item['result'])
        for p in data['phases']:
            for prop in ('bulk_modulus','shear_modulus'):p[prop]={'value':5e-324,'unit':'Pa'}
        self.assertTrue(all(item['computation']=='numerical_range_error' for item in results(data).values()))

    def test_large_integer_ordering_is_checked_before_numeric_rounding(self):
        for unit in ('Pa','GPa'):
            data=example()
            for p,k,g in zip(data['phases'],(10**100,10**100+1),(2,1)):
                p['bulk_modulus']={'value':k,'unit':unit};p['shear_modulus']={'value':g,'unit':unit}
            for claim,item in results(data).items():
                expected='satisfied' if claim.startswith(('reuss_','voigt_')) else 'violated'
                self.assertEqual(item['applicability'],expected)
                if expected=='violated':self.assertIsNone(item['result'])
            data['phases'].reverse()
            self.assertEqual(results(data)['hs_shear_3d_two_phase']['applicability'],'violated')

    def test_nonfinite_inputs_rejected(self):
        for prop in ('bulk_modulus','shear_modulus'):
            for value in (float('nan'),float('inf'),float('-inf')):
                data=example();data['phases'][0][prop]['value']=value
                with self.assertRaises(ValidationError):evaluate(data)

    def test_context_independence_all_mechanical_outputs(self):
        expected=evaluate(example())
        with localcontext() as ctx:
            ctx.prec=2;ctx.Emax=3;ctx.Emin=-3;ctx.traps[Inexact]=True
            self.assertEqual(evaluate(example()),expected)

    def test_random_shear_nesting_and_derived_rectangle_corners(self):
        rng=random.Random(882)
        for _ in range(100):
            data=example();k1,k2=sorted(10**rng.uniform(-2,2) for _ in range(2))
            g1,g2=sorted(10**rng.uniform(-2,2) for _ in range(2));f=rng.uniform(.01,.99)
            for p,k,g,v in zip(data['phases'],(k1,k2),(g1,g2),(f,1-f)):
                p['bulk_modulus']['value']=k;p['shear_modulus']['value']=g;p['volume_fraction']=v
            r=endpoints(data);b=r['hs_bulk_3d_two_phase'];s=r['hs_shear_3d_two_phase'];e=r['youngs_modulus_outer'];n=r['poissons_ratio_outer']
            self.assertLessEqual(r['reuss_shear']['lower'],s['lower']+1e-12)
            self.assertLessEqual(s['lower'],s['upper']+1e-12)
            self.assertLessEqual(s['upper'],r['voigt_shear']['upper']+1e-12)
            for k in (b['lower'],b['upper']):
                for g in (s['lower'],s['upper']):
                    ev=9*k*g/(3*k+g);nv=(3*k-2*g)/(2*(3*k+g))
                    self.assertLessEqual(e['lower']-1e-12,ev);self.assertLessEqual(ev,e['upper']+1e-12)
                    self.assertLessEqual(n['lower']-1e-12,nv);self.assertLessEqual(nv,n['upper']+1e-12)


class MechanicalContractTests(unittest.TestCase):
    def test_typed_schema_versions_and_dependencies(self):
        out=evaluate(example());self.assertEqual(out['schema_version'],'1.1.0')
        self.assertEqual(out['engine_version'],__version__)
        self.assertEqual({e['claim_id'] for e in out['evaluations']}, {
            'hs_bulk_3d_two_phase', 'reuss_bulk', 'voigt_bulk',
            'hs_shear_3d_two_phase', 'reuss_shear', 'voigt_shear',
            'youngs_modulus_outer', 'poissons_ratio_outer'})
        self.assertEqual(len(out['evaluations']), 8)
        for item in out['evaluations']:
            if item['claim_id'].endswith('_outer'):
                self.assertEqual(item['bound_kind'],'derived_outer_envelope')
                d=item['dependencies'];self.assertEqual(d['instance_id'],out['instance_id'])
                self.assertEqual(d['claim_ids'],['hs_bulk_3d_two_phase','hs_shear_3d_two_phase'])
                self.assertEqual(d['joint_attainability'],'not_asserted')
                self.assertTrue(any(c['condition_id']=='compatible_bulk_shear_bounds' for c in item['checks']))
            else:self.assertEqual(item['bound_kind'],'scalar_modulus_bound');self.assertNotIn('dependencies',item)

    @unittest.skipIf(Draft202012Validator is None,'optional dev dependency jsonschema is not installed')
    def test_schema_rejects_mistyped_domains_and_dependency_graph(self):
        validator=Draft202012Validator(load_json(ROOT/'schemas/evaluation.schema.json'));good=evaluate(example());validator.validate(good)
        mutations=[]
        for index,key,value in [(3,'quantity','effective_bulk_modulus'),(6,'bound_kind','scalar_modulus_bound'),(7,'rule_id','hs_bulk_3d_two_phase_v1')]:
            bad=copy.deepcopy(good);bad['evaluations'][index][key]=value;mutations.append(bad)
        for value in (-1,.5):
            bad=copy.deepcopy(good);bad['evaluations'][7]['result']['lower']=value;mutations.append(bad)
        bad=copy.deepcopy(good);bad['evaluations'][7]['result']['unit']='GPa';mutations.append(bad)
        bad=copy.deepcopy(good);bad['evaluations'][6]['result']['lower']=-1;mutations.append(bad)
        bad=copy.deepcopy(good);del bad['evaluations'][6]['dependencies'];mutations.append(bad)
        bad=copy.deepcopy(good);bad['evaluations'][6]['dependencies']['claim_ids'].reverse();mutations.append(bad)
        bad=copy.deepcopy(good);bad['evaluations'][3]=copy.deepcopy(bad['evaluations'][0]);mutations.append(bad)
        bad=copy.deepcopy(good)
        bad['evaluations'][6]['checks']=[c for c in bad['evaluations'][6]['checks'] if c['condition_id']!='compatible_bulk_shear_bounds']
        mutations.append(bad)
        bad=copy.deepcopy(good);bad['evaluations'][0].update(computation='numerical_range_error',result=None,error='out of range')
        mutations.append(bad)
        for bad in mutations:self.assertTrue(list(validator.iter_errors(bad)))
        data=example()
        for p in data['phases']:p['bulk_modulus']['value']=1;p['shear_modulus']['value']=6
        validator.validate(evaluate(data))

    def test_all_new_claims_discoverable_and_source_ids_resolve(self):
        catalog=read_catalog('claims');self.assertEqual(catalog['schema_version'],'1.10.0')
        names={r['id'] for r in catalog['records']};sources={r['id'] for r in read_catalog('sources')['records']}
        for item in catalog['records']:
            self.assertTrue(set(item['dependencies']).issubset(names))
            self.assertTrue(all(e['source_id'] in sources for e in item['evidence']))
        shear_ids = {r['id'] for r in query_catalog('claims',query='effective_shear_modulus')['records']}
        self.assertTrue({'hs_shear_3d_two_phase', 'reuss_shear', 'voigt_shear',
                         'hs_porous_shear_3d_solid_void'} <= shear_ids)
        self.assertIn('poissons_ratio_outer', {r['id'] for r in query_catalog('claims',query='effective_poissons_ratio')['records']})

    def test_identity_evidence_is_distinct_from_derived_envelope(self):
        source=next(s for s in read_catalog('sources')['records'] if s['id']=='meille_garboczi_2001')
        self.assertEqual(source['doi'],'10.1088/0965-0393/9/5/303')
        self.assertEqual(source['read_status'], expected_provenance('sources', source['id'])['read_status'])
        self.assertEqual(source['license'], expected_provenance('sources', source['id'])['license'])
        self.assertEqual(source['role'],'isotropic_elastic_identity_source')
        for claim in ('youngs_modulus_outer','poissons_ratio_outer'):
            record=query_catalog('claims',record_id=claim)['records'][0]
            identity=next(e for e in record['evidence'] if e['source_id']=='meille_garboczi_2001')
            self.assertEqual(identity['verification_status'], expected_evidence('claims', claim, 'meille_garboczi_2001')['verification_status'])
            self.assertIn('project calculation',identity['verified_as'])
            self.assertEqual(record['verification']['independent_scientific_review'], expected_provenance('claims', record['id'])['verification']['independent_scientific_review'])

    def test_four_language_new_labels_warnings_and_catalog_dependencies(self):
        for lang in LANGUAGES:
            run=subprocess.run([sys.executable,'-m','materials_boundaries','evaluate','examples/synthetic-two-phase.json','--lang',lang],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr);self.assertNotIn('[missing:',run.stdout)
            for key in ('hs_shear','reuss_shear','voigt_shear','youngs_modulus_outer','poissons_ratio_outer','derived_outer_notice','poisson_range_notice'):
                self.assertIn(translate(key,lang),run.stdout)
            text=render_catalog(query_catalog('claims',record_id='poissons_ratio_outer'),'claims',lang)
            for key in ('catalog_dependencies','catalog_bound_kind','catalog_status_derived_outer_envelope'):
                self.assertIn(translate(key,lang),text)
            self.assertNotIn('[missing:',text)

    def test_human_poisson_rounding_preserves_strict_range_in_four_languages(self):
        for k,g in ((1e13,1),(1,1e14)):
            data=example()
            for p in data['phases']:p['bulk_modulus']['value']=k;p['shear_modulus']['value']=g
            output=evaluate(data);nu=output['evaluations'][-1]['result']['lower']
            self.assertTrue(-1 < nu < 0.5)
            for lang in LANGUAGES:
                text=_render(output,lang)
                line=next(line for line in text.splitlines() if line.startswith(translate('poissons_ratio_outer',lang)+':'))
                rendered=line.split(': ',1)[1].split(' – ')[0]
                self.assertEqual(float(rendered),nu)
                self.assertTrue(-1 < float(rendered) < 0.5)
                self.assertIn(repr(nu),line)

    def test_new_evidence_statuses_are_localized_in_four_languages(self):
        catalog=query_catalog('sources',record_id='meille_garboczi_2001')
        for lang in LANGUAGES:
            text=render_catalog(catalog,'sources',lang)
            for code in ('primary_paper_extracted_text_equation_checked_visual_not_verified',
                         'copyright_iop_no_open_reuse_license_verified','isotropic_elastic_identity_source'):
                label=translate('catalog_status_'+code,lang)
                self.assertNotIn('[missing:',label);self.assertIn(label,text)

    def test_boundary_numeric_error_cli_exit_three(self):
        data=example()
        for p in data['phases']:p['bulk_modulus']['value']=1e100;p['shear_modulus']['value']=1
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.json';path.write_text(json.dumps(data))
            run=subprocess.run([sys.executable,'-m','materials_boundaries','evaluate',str(path),'--json'],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(run.returncode,3,run.stderr)
        self.assertEqual(json.loads(run.stdout)['evaluations'][-1]['computation'],'numerical_range_error')


if __name__=='__main__':unittest.main()
