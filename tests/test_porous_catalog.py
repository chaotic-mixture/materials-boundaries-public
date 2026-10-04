"""Porous source-conditioned metadata; test arithmetic is never a runtime rule."""
import copy
from fractions import Fraction as F
import hashlib
import json
import random
import subprocess
import sys
import unittest
from unittest.mock import patch

from materials_boundaries import __version__, evaluate, load_json, ValidationError
from source_evidence_preservation import previous_record
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from catalog_fixtures import expected_evidence, expected_provenance
from test_engine import ROOT, example
from catalog_fixtures import (EXECUTABLE_IDS, GRIFFITH_IDS, MECHANICS_IDS, CORE_STABILITY_IDS,
                              historical_records, select_records, evidence_for, scientific_digest)
try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

IDS = ['hs_porous_bulk_3d_solid_void', 'hs_porous_shear_3d_solid_void',
       'hs_porous_youngs_outer_3d_solid_void']
SOURCE = 'roberts_garboczi_2002_porous'
FIXTURES = {
    'unknown-isotropy.json': '48dc73f58623623da8d9d2504f1b13c15b024573403b7b6f85a93e50786844b9',
    'anisotropic-constituent.json': 'ec5010d7c24b0654e4d18e05676a6d0fbfa670bd0f1188025840cd48f9abf43c',
    'literature-epoxy-glass-model.json': '286a6c67557979eaab3e8f109d8a59f2ee97f7b4804ec171f541f4d59261a568',
    'synthetic-two-phase.json': '957e1871d816862030f806773a1b7c7b77c15af2f8bdfaac2f3d09fe8c8553b3',
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def porous():
    return [query_catalog('claims', record_id=name)['records'][0] for name in IDS]


def upper(k, g, p):
    """Independent exact test arithmetic, not an exported calculator."""
    return (4*k*g*(1-p)/(4*g+3*k*p),
            g*(1-p)*(9*k+8*g)/(9*k+8*g+6*p*(k+2*g)))


def young(k, g):
    return 9*k*g/(3*k+g)


class PorousCatalogTests(unittest.TestCase):
    def test_historical_science_and_porous_ids_are_preserved(self):
        prior_ids = EXECUTABLE_IDS + GRIFFITH_IDS + MECHANICS_IDS + CORE_STABILITY_IDS
        predecessors = [previous_record('claims', record)
                        for record in historical_records('claims', prior_ids)]
        self.assertEqual(scientific_digest(predecessors),
                         '6aeb84933790e78734fd59b4292206be0bf520c575212d6700cbfb79c6d62fa0')
        self.assertEqual([c['id'] for c in porous()], IDS)
        self.assertEqual(query_catalog('sources', record_id=SOURCE)['records'][0]['id'], SOURCE)

    def test_all_eight_results_for_each_existing_fixture_are_unchanged(self):
        for filename, expected in FIXTURES.items():
            result = evaluate(load_json(ROOT/'examples'/filename))
            self.assertEqual(len(result['evaluations']), 8)
            self.assertEqual(result.pop('engine_version'), __version__)
            self.assertEqual(digest(result), expected)

    def test_catalog_only_types_parameters_and_dependencies(self):
        for i, c in enumerate(porous()):
            self.assertEqual(c['evaluation_support'], 'catalog_only')
            self.assertEqual((c['direction'], c['quantity_dimension'], c['si_unit']), ('interval', 'pressure', 'Pa'))
            self.assertEqual(c['claim_type'], 'theoretical_bound' if i < 2 else 'derived_outer_envelope')
            self.assertEqual(c['bound_kind'], 'scalar_modulus_bound' if i < 2 else 'derived_outer_envelope')
            self.assertEqual(c['dependencies'], [] if i < 2 else IDS[:2])
            self.assertEqual([p['symbol'] for p in c['parameters']], ['Ks', 'Gs', 'p'])
            self.assertEqual([(p['dimension'], p['si_unit']) for p in c['parameters']], [('pressure','Pa'),('pressure','Pa'),('dimensionless','1')])
            for key in ('result', 'checks', 'applicability', 'computation', 'value', 'criterion'):
                self.assertNotIn(key, c)

    def test_unique_ids_and_all_references_resolve_without_cycles(self):
        claims = read_catalog('claims')['records']; sources = read_catalog('sources')['records']
        claim_map = {c['id']: c for c in claims}; source_ids = {s['id'] for s in sources}
        self.assertEqual(len(claim_map), len(claims)); self.assertEqual(len(source_ids), len(sources))
        def walk(name, ancestors=()):
            self.assertNotIn(name, ancestors)
            for dep in claim_map[name]['dependencies']:
                self.assertIn(dep, claim_map); walk(dep, ancestors+(name,))
        for c in claims:
            walk(c['id'])
            self.assertTrue(all(e['source_id'] in source_ids for e in c['evidence']))

    def test_isotropy_void_limit_and_geometry_premises_are_explicit(self):
        for c in porous():
            a = c['required_assumptions']
            self.assertEqual(a['dimension'], 3)
            self.assertEqual(a['constituent_symmetry'], 'isotropic_solid')
            self.assertEqual(a['effective_symmetry'], 'isotropic')
            self.assertTrue(a['positive_solid_bulk_modulus']); self.assertTrue(a['positive_solid_shear_modulus'])
            self.assertTrue(a['void_bulk_and_shear_moduli_zero'])
            self.assertEqual(a['pore_surface'], 'traction_free')
            self.assertEqual(a['geometry_class'], 'unrestricted_including_disconnected_solid')
            self.assertIn('isotropy_preserved', a['isotropic_zero_phase_limit'])
            text = ' '.join(c['limits'])
            for token in ('0<p<1', 'p=0', 'p=1', 'disconnected', 'vanishing-positive-stiffness',
                          'low-density', 'simultaneously', 'Unknown or violated', 'mass balance',
                          'contact closure', 'surface elasticity', 'prestress'):
                self.assertIn(token, text + ' ' + a['geometry_class'])
            self.assertEqual(c['verification']['independent_scientific_review'], expected_provenance('claims', c['id'])['verification']['independent_scientific_review'])
        self.assertTrue(porous()[2]['required_assumptions']['compatible_bulk_shear_bounds'])
        self.assertIn('Poisson ratio is not defined', ' '.join(porous()[2]['limits']))

    def test_source_equations_solid_fraction_conversion_and_rights_are_explicit(self):
        source = query_catalog('sources', record_id=SOURCE)['records'][0]
        self.assertEqual(source['doi'], '10.1098/rspa.2001.0900')
        self.assertEqual(source['year'], 2002)
        self.assertEqual(source['bundled_content'], expected_provenance('sources', source['id'])['bundled_content'])
        self.assertEqual(source['license'], expected_provenance('sources', source['id'])['license'])
        self.assertEqual(source['read_status'], expected_provenance('sources', source['id'])['read_status'])
        notes = ' '.join(source['claim_notes'])
        for token in ('issue 2021', 'solid fraction', '1037', 'Royal Society', 'No blanket reuse'):
            self.assertIn(token, notes)
        for c, equation in zip(porous()[:2], ['117', '118']):
            self.assertIn(equation, evidence_for(c, 'kochmann_milton_2014')['locator'])
            self.assertIn('positive-phase limit', evidence_for(c, 'kochmann_milton_2014')['verified_as'])
            self.assertEqual(evidence_for(c, 'hashin_shtrikman_1963')['verification_status'], expected_evidence('claims', c['id'], 'hashin_shtrikman_1963')['verification_status'])
        evidence = evidence_for(porous()[2], SOURCE)
        for token in ('(2.8)', '1037', '1034', '1035'):
            self.assertIn(token, evidence['locator'])
        self.assertIn('source p=1-p_catalog', evidence['verified_as'])

    def test_four_language_labels_queries_and_bound_specific_notice(self):
        for lang in LANGUAGES:
            for c in porous():
                label = translate('catalog_name_'+c['id'], lang)
                self.assertIn(c['id'], [r['id'] for r in query_catalog('claims', query=label)['records']])
                text = render_catalog({'records':[c]}, 'claims', lang)
                for value in (label, c['name'], translate('catalog_bound_notice', lang), translate('catalog_status_catalog_only', lang)):
                    self.assertIn(value, text)
                self.assertNotIn('[missing:', text)
                self.assertNotIn(translate('catalog_model_notice', lang), text)
                self.assertNotIn(translate('catalog_criterion_notice', lang), text)

    def test_cli_canonical_queries_and_no_porous_command(self):
        results = []
        for lang in LANGUAGES:
            run = subprocess.run([sys.executable,'-m','materials_boundaries','catalog','claims','--query','porous','--json','--lang',lang],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(set(IDS) <= {r['id'] for r in json.loads(run.stdout)['records']})
            results.append(run.stdout)
        self.assertEqual(len(set(results)), 1)
        run = subprocess.run([sys.executable,'-m','materials_boundaries','porous','--porosity','0.5'],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(run.returncode, 2); self.assertEqual(run.stdout, '')

    def test_active_zero_moduli_still_block_all_eight_runtime_claims(self):
        for p in (0.01, 0.5, 0.99, 1):
            data = example()
            data['phases'][0]['volume_fraction'] = p
            data['phases'][1]['volume_fraction'] = 1-p
            for key in ('bulk_modulus','shear_modulus'):
                data['phases'][0][key]['value'] = 0
            results = evaluate(data)['evaluations']
            self.assertEqual(len(results), 8)
            self.assertTrue(all(x['applicability']=='violated' and x['result'] is None for x in results))

    def test_absent_void_phase_does_not_block_pure_positive_solid(self):
        data = example(); data['phases'][0]['volume_fraction'] = 0; data['phases'][1]['volume_fraction'] = 1
        for key in ('bulk_modulus','shear_modulus'): data['phases'][0][key]['value'] = 0
        self.assertTrue(all(x['applicability']=='satisfied' and x['computation']=='computed' for x in evaluate(data)['evaluations']))

    def test_poisoned_porous_records_never_execute_join_or_plot(self):
        expected = evaluate(example()); poisoned = read_catalog('claims')
        for c in select_records(poisoned, IDS):
            c.update(rule_id='raise_if_dispatched', formula_display='raise_if_executed()', quantity='poison_porous_quantity')
            c['parameters'] = [{'invalid':'must_not_be_rendered'}]
            c['evidence'] = [{'source_id':'must_not_be_joined'}]
        with patch('materials_boundaries.catalog.read_catalog', side_effect=AssertionError('no runtime catalog dispatch')):
            self.assertEqual(evaluate(example()), expected)
        original = read_catalog
        with patch('materials_boundaries.visualization.read_catalog', side_effect=lambda name:poisoned if name=='claims' else original(name)):
            bundle = build_comparison([example()], fractions=[0,.5,1])
        self.assertEqual(len(bundle['series']), 8)
        self.assertEqual(len(bundle['catalogs']['claims']['records']), 8)
        rendered = json.dumps(bundle)+render_html(bundle)+render_svg(bundle,bundle['cases'][0]['id'])
        for token in IDS+['must_not_be_joined','poison_porous_quantity','must_not_be_rendered']:
            self.assertNotIn(token, rendered)

    def test_synthetic_documentation_fixture_has_correct_edges_and_density(self):
        doc = load_json(ROOT/'examples/catalog/porous-synthetic.json')
        self.assertEqual(doc['classification'], 'project_synthetic_not_measurement')
        self.assertEqual(doc['kind'], 'catalog_documentation_example_not_evaluator_input')
        self.assertEqual(doc['claim_ids'], IDS)
        k,g,rho = (doc['inputs'][x] for x in ('Ks_GPa','Gs_GPa','rho_s_kg_m3'))
        for row in doc['samples']:
            p = row['p']; ku,gu = upper(k,g,p)
            eu = young(ku,gu) if p < 1 else 0
            for key,val in [('K_upper_GPa',ku),('G_upper_GPa',gu),('E_upper_GPa',eu),('rho_eff_kg_m3',rho*(1-p)),
                            ('K_lower_GPa', k if p==0 else 0),('G_lower_GPa',g if p==0 else 0),('E_lower_GPa',young(k,g) if p==0 else 0)]:
                self.assertAlmostEqual(row[key], val, places=12)
        self.assertEqual(doc['samples'][-1]['p'],1)
        with self.assertRaises(ValidationError): evaluate(doc)

    def test_exact_young_outer_matches_source_solid_fraction_form(self):
        for k,g,p in [(F(100),F(40),F(1,4)), (F(3),F(20),F(99,100)), (F(1000),F(1),F(0))]:
            ku,gu=upper(k,g,p); es=young(k,g); nu=(3*k-2*g)/(2*(3*k+g))
            coefficient=(1+nu)*(13-15*nu)/(2*(7-5*nu))
            source_solid_fraction=1-p
            source_upper=es*source_solid_fraction/(1+coefficient*(1-source_solid_fraction))
            self.assertEqual(young(ku,gu),source_upper)
            self.assertGreater(coefficient,0)
        # Empty-domain 0/0 is deliberately not evaluated with young().
        self.assertEqual(upper(F(100),F(40),F(1)),(0,0))

    def test_exact_positive_phase_regularization_converges_and_lower_edge_is_distinct(self):
        k,g,p=F(100),F(40),F(1,4); fs=1-p; target=upper(k,g,p)
        z=g*(9*k+8*g)/(6*(k+2*g))
        previous=(k,g)
        for eta in (F(1,10),F(1,100),F(1,10000),F(1,100000000)):
            kv,gv=eta*k,eta*g
            def bound(a,b,shift): return (a*b+shift*(fs*a+p*b))/(fs*b+p*a+shift)
            regularized=(bound(k,kv,4*g/3),bound(g,gv,z))
            for i in (0,1):
                self.assertGreaterEqual(regularized[i],target[i]); self.assertLessEqual(regularized[i],previous[i])
            previous=regularized
            self.assertGreaterEqual(bound(k,kv,4*gv/3),0)
            self.assertGreaterEqual(bound(g,gv,eta*z),0)
        self.assertLess(float(previous[0]-target[0]),1e-5)
        self.assertLess(float(bound(k,kv,4*gv/3)),1e-5)
        # At p=0, absent-phase removal gives the exact solid lower endpoint.
        self.assertEqual((k*kv+(4*gv/3)*k)/(kv+4*gv/3),k)

    def test_finite_density_upper_is_not_replaced_by_lower_asymptotic_line(self):
        k,g=F(100),F(40)
        for p in (F(1,10),F(1,2),F(9,10)):
            ku,gu=upper(k,g,p); r=1-p
            asymptotic_k=4*k*g*r/(3*k+4*g)
            asymptotic_g=g*(9*k+8*g)*r/(15*k+20*g)
            self.assertGreater(ku,asymptotic_k); self.assertGreater(gu,asymptotic_g)
            self.assertLessEqual(ku,k*r); self.assertLessEqual(gu,g*r)

    def test_positive_upper_forms_are_monotone_and_below_voigt_in_synthetic_samples(self):
        rng=random.Random(6022026)
        for _ in range(100):
            k,g=F(rng.randint(1,1000)),F(rng.randint(1,1000))
            previous=(k,g)
            for p in (F(0),F(1,10),F(1,2),F(9,10),F(1)):
                values=upper(k,g,p)
                for val,old,solid in zip(values,previous,(k,g)):
                    self.assertGreaterEqual(val,0); self.assertLessEqual(val,old); self.assertLessEqual(val,(1-p)*solid)
                previous=values


@unittest.skipIf(Draft202012Validator is None,'optional jsonschema dev dependency not installed')
class PorousSchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalog=read_catalog('claims')
        self.schema=load_json(ROOT/'schemas/claims.schema.json')
        self.validator=Draft202012Validator(self.schema)

    def invalid(self,record_id,mutation):
        bad=copy.deepcopy(self.catalog);mutation(select_records(bad, [record_id])[0])
        self.assertTrue(list(self.validator.iter_errors(bad)))

    def test_catalog_schema_and_embedded_snapshot_validate(self):
        self.validator.check_schema(self.schema);self.validator.validate(self.catalog)
        comparison=load_json(ROOT/'schemas/comparison.schema.json')
        self.assertEqual(comparison['$defs']['claims'],self.schema)
        self.assertEqual(comparison['properties']['catalogs']['properties']['claims']['$ref'],self.schema['$id'])
        reordered=copy.deepcopy(self.catalog)
        for c in select_records(reordered, IDS): c['parameters'].reverse()
        self.validator.validate(reordered)
        self.validator.validate(query_catalog('claims',query='porous'))
        old=copy.deepcopy(self.catalog);old['schema_version']='1.4.0'
        self.assertTrue(list(self.validator.iter_errors(old)))

    def test_catalog_bound_cannot_be_reclassified_or_given_runtime_fields(self):
        for i in IDS:
            for key,value in [('evaluation_support','composite_evaluate'),('direction','upper'),('claim_type','model_estimate'),
                              ('bound_kind',None),('quantity','effective_poissons_ratio'),('quantity_dimension','dimensionless'),
                              ('si_unit','1'),('result',{'value':1}),('applicability','satisfied'),('criterion',{})]:
                with self.subTest(i=i,key=key):self.invalid(i,lambda c:c.update({key:value}))
            self.invalid(i,lambda c:c.pop('parameters'))
            self.invalid(i,lambda c:(c.pop('parameters'),c.update(evaluation_support='composite_evaluate')))
            self.invalid(i,lambda c:c.update(id='unregistered_porous_id'))
            self.invalid(i,lambda c:c.update(rule_id='wrong_rule'))

    def test_missing_wrong_duplicate_parameters_and_assumptions_fail_closed(self):
        for i in IDS:
            self.invalid(i,lambda c:c['parameters'].pop())
            self.invalid(i,lambda c:c['parameters'].append(copy.deepcopy(c['parameters'][0])))
            for j in range(3):
                for key,value in [('quantity','wrong'),('symbol','wrong'),('dimension','length'),('si_unit','m')]:
                    self.invalid(i,lambda c:c['parameters'][j].update({key:value}))
            for key in select_records(self.catalog, [i])[0]['required_assumptions']:
                self.invalid(i,lambda c:c['required_assumptions'].pop(key))
                self.invalid(i,lambda c:c['required_assumptions'].update({key:'unknown'}))
        self.invalid(IDS[0],lambda c:c.update(dependencies=[IDS[1]]))
        self.invalid(IDS[2],lambda c:c.update(dependencies=['hs_bulk_3d_two_phase','hs_shear_3d_two_phase']))
        self.invalid(IDS[2],lambda c:c['dependencies'].pop())


if __name__=='__main__': unittest.main()
