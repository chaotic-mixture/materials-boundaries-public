"""Display-only strict stability predicates; no stiffness input or runtime solver."""
import copy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from materials_boundaries import evaluate, load_json
from source_evidence_preservation import previous_record
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.i18n import LANGUAGES, translate
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from catalog_fixtures import expected_provenance
from test_engine import ROOT, example
from catalog_fixtures import (EXECUTABLE_IDS, GRIFFITH_IDS, MECHANICS_IDS, CORE_STABILITY_IDS,
                              historical_records, select_records, evidence_for, scientific_digest)
try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

IDS = ['general_stiffness_positive_definite', 'cubic_born_stability',
       'hexagonal_born_stability', 'orthorhombic_born_stability',
       'tetragonal_i_born_stability', 'tetragonal_ii_born_stability',
       'rhombohedral_i_born_stability', 'rhombohedral_ii_born_stability']
SOURCE = 'mouhat_coudert_2014_elastic_stability'


def criteria():
    return historical_records('claims', IDS)


class StabilityCatalogTests(unittest.TestCase):
    def test_historical_science_and_classification_are_preserved(self):
        prior_ids = EXECUTABLE_IDS + GRIFFITH_IDS + MECHANICS_IDS
        predecessors = [previous_record('claims', record)
                        for record in historical_records('claims', prior_ids)]
        self.assertEqual(scientific_digest(predecessors),
                         '413262f21c5a50bac4a304d7042c70c248b952a600f16f8406ee842e50dba100')
        self.assertEqual([r['id'] for r in criteria()], IDS)
        constraint_ids = {r['id'] for r in query_catalog('claims', direction='constraint')['records']}
        self.assertTrue(set(IDS) <= constraint_ids)
        self.assertEqual(query_catalog('claims', claim_type='stability_criterion', direction='upper')['records'], [])
        for c in criteria():
            self.assertEqual((c['quantity_dimension'], c['si_unit']), ('logical_predicate', None))
            self.assertEqual((c['direction'], c['evaluation_support']), ('constraint', 'catalog_only'))
            self.assertIsNone(c['bound_kind']); self.assertEqual(c['dependencies'], [])
            self.assertIn(SOURCE, {e['source_id'] for e in c['evidence']})
            for key in ('result', 'value', 'checks', 'applicability', 'computation'):
                self.assertNotIn(key, c)

    def test_source_exact_version_locator_and_reuse_scope(self):
        source = query_catalog('sources', record_id=SOURCE)['records'][0]
        self.assertEqual(source['doi'], '10.1103/PhysRevB.90.224104')
        self.assertEqual(source['authors'], ['Félix Mouhat', 'François-Xavier Coudert'])
        self.assertIn('https://arxiv.org/abs/1410.0065v3', source['urls'])
        self.assertEqual(source['read_status'], expected_provenance('sources', source['id'])['read_status'])
        self.assertEqual(source['license'], expected_provenance('sources', source['id'])['license'])
        self.assertIn('2014-12-05', ' '.join(source['claim_notes']))
        self.assertIn('not a general CC reuse license', ' '.join(source['claim_notes']))
        self.assertEqual(source['bundled_content'], expected_provenance('sources', source['id'])['bundled_content'])
        for c, number in zip(historical_records('claims', CORE_STABILITY_IDS), ['(2)', '(6)', '(9)', '(18)']):
            self.assertIn(number, evidence_for(c, SOURCE)['locator'])
            self.assertEqual(c['verification']['independent_scientific_review'], expected_provenance('claims', c['id'])['verification']['independent_scientific_review'])

    def test_voigt_stress_strain_energy_and_symmetry_are_explicit(self):
        general, cubic, hexagonal, ortho = historical_records('claims', CORE_STABILITY_IDS)
        self.assertEqual(general['required_assumptions']['axes'], 'orthonormal_cartesian_any_orientation')
        for c in criteria():
            convention = c['criterion']; a = c['required_assumptions']
            self.assertEqual(convention['voigt_order'], ['xx','yy','zz','yz','xz','xy'])
            self.assertIn('2*epsilon_yz', convention['strain_vector'])
            self.assertNotIn('2*sigma', convention['stress_vector'])
            self.assertEqual(convention['energy_density'], 'delta_u=(1/2)*e^T*C*e')
            self.assertEqual((a['reference_state'], a['perturbation_class'], a['energy_approximation']),
                             ('stress_free_equilibrium', 'homogeneous_strain', 'harmonic_quadratic'))
            matrix = convention['stiffness_matrix']
            self.assertEqual(len(matrix), 6)
            self.assertTrue(all(matrix[i][j] == matrix[j][i] for i in range(6) for j in range(6)))
            self.assertTrue(all((p['dimension'], p['si_unit']) == ('pressure', 'Pa') for p in c['parameters']))
        self.assertEqual(cubic['criterion']['stiffness_matrix'][2][2], 'C11')
        self.assertEqual(hexagonal['criterion']['stiffness_matrix'][5][5], '(C11-C12)/2')
        self.assertIn('Laue classes 6/m and 6/mmm', hexagonal['limits'][-1])
        self.assertEqual(len(ortho['parameters']), 9)
        self.assertIn('C23^2', ortho['criterion']['inequalities'][2]['expression'])

    def test_strict_inequality_dimensions_and_scope_exclusions(self):
        for c in criteria():
            self.assertEqual(c['criterion']['combination'], 'all')
            for inequality in c['criterion']['inequalities']:
                self.assertEqual((inequality['operator'], inequality['rhs']), ('>', 0))
            text = ' '.join(c['limits'])
            for token in ('finite external load', 'phonon', '2D', 'near-zero', 'marginal', 'positive-semidefinite stiffness matrix'):
                self.assertIn(token, text)
            self.assertIn('display metadata only', text)
        ortho = historical_records('claims', ['orthorhombic_born_stability'])[0]
        self.assertEqual([x['si_unit'] for x in ortho['criterion']['inequalities']], ['Pa','Pa^2','Pa^3','Pa','Pa','Pa'])

    def test_four_language_labels_search_and_null_unit_render_as_not_applicable(self):
        for lang in LANGUAGES:
            for c in criteria():
                label = translate('catalog_name_' + c['id'], lang)
                self.assertIn(c['id'], [r['id'] for r in query_catalog('claims', query=label)['records']])
                text = render_catalog({'records':[c]}, 'claims', lang)
                for key in ('catalog_criterion_notice', 'catalog_inequalities', 'catalog_stiffness_matrix', 'catalog_status_logical_predicate'):
                    self.assertIn(translate(key, lang), text)
                self.assertIn(label, text); self.assertIn(c['name'], text)
                self.assertIn(translate('catalog_si_unit', lang) + ': ' + translate('catalog_not_applicable', lang), text)
                self.assertNotIn('[missing:', text)
                self.assertNotIn(translate('catalog_model_notice', lang), text)
        source = query_catalog('sources', record_id=SOURCE, query='正交晶系')
        self.assertEqual(source['records'], [])

    def test_cli_canonical_predicate_queries_and_no_new_solver(self):
        results = []
        for lang in LANGUAGES:
            run = subprocess.run([sys.executable,'-m','materials_boundaries','catalog','claims','--claim-type','stability_criterion','--direction','constraint','--json','--lang',lang], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr); results.append(run.stdout)
            matched = json.loads(run.stdout)['records']
            self.assertTrue(set(IDS) <= {c['id'] for c in matched})
            self.assertTrue(all(c['claim_type'] == 'stability_criterion' and c['direction'] == 'constraint' for c in matched))
        self.assertEqual(len(set(results)), 1)
        for args in [('stability','cubic_born_stability'),('evaluate','examples/synthetic-two-phase.json','--criterion','cubic_born_stability'),('catalog','sources','--claim-type','stability_criterion')]:
            run = subprocess.run([sys.executable,'-m','materials_boundaries',*args], cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(run.returncode,2); self.assertEqual(run.stdout,'')

    def test_poisoned_criteria_never_execute_join_or_plot(self):
        expected = evaluate(example())
        poisoned = read_catalog('claims')
        for c in select_records(poisoned, IDS):
            c.update(rule_id='raise_if_dispatched', formula_display='raise_if_executed()', quantity='poison_quantity')
            c['criterion'] = {'invalid':'must_not_be_evaluated_or_rendered'}
            c['evidence'] = [{'source_id':'must_not_be_joined'}]
        original = read_catalog
        with patch('materials_boundaries.catalog.read_catalog', side_effect=AssertionError('no runtime catalog dispatch')):
            self.assertEqual(evaluate(example()), expected)
        with patch('materials_boundaries.visualization.read_catalog', side_effect=lambda name:poisoned if name=='claims' else original(name)):
            bundle = build_comparison([example()], fractions=[0,.5,1])
        self.assertEqual(len(bundle['series']),8)
        self.assertEqual(len(bundle['catalogs']['claims']['records']),8)
        serialized = json.dumps(bundle) + render_html(bundle) + render_svg(bundle,bundle['cases'][0]['id'])
        for token in IDS + ['must_not_be_joined', 'poison_quantity', 'must_not_be_evaluated_or_rendered']:
            self.assertNotIn(token, serialized)

    def test_invented_cubic_and_hexagonal_arithmetic_not_material_measurements(self):
        # Hand-coded arithmetic checks are test fixtures, not parsed catalog formulas.
        def cubic(a,b,c):return (a-b,a+2*b,c)
        self.assertEqual(cubic(200,100,80),(100,400,80))
        self.assertEqual(cubic(100,-60,40),(160,-20,40))
        self.assertEqual(cubic(200,200,80)[0],0)
        def hexagonal(a,b,c,d,e):return (a-abs(b),d*(a+b)-2*c*c,e)
        self.assertEqual(hexagonal(150,50,40,180,60),(100,32800,60))
        self.assertEqual(hexagonal(150,50,150,180,60),(100,-9000,60))
        # Exact boundary: C13^2=18000, without a rounded square root.
        self.assertEqual(180*(150+50)-2*18000,0)
        self.assertEqual((150-50)/2,50)

    def test_orthorhombic_determinant_is_essential_and_equality_not_strict(self):
        def margins(a,b,c,d,e,f):return (a,a*b-d*d,a*b*c+2*d*e*f-a*f*f-b*e*e-c*d*d)
        self.assertEqual(margins(150,120,100,40,30,20),(150,16400,1520000))
        self.assertEqual(margins(100,100,100,80,80,-80),(100,3600,-1944000))
        # All pair minors and commonly misused linear tests can pass while det<0.
        self.assertEqual([100*100-x*x for x in (80,80,-80)], [3600]*3)
        self.assertEqual([200-2*x for x in (80,80,-80)], [40,40,360])
        self.assertEqual(300+2*(80+80-80),460)
        self.assertEqual(margins(100,100,100,0,0,100),(100,10000,0))

    def test_general_positive_diagonals_are_insufficient_and_null_mode_not_strict(self):
        diagonal=[100,100,100,40,50,60]
        self.assertEqual(min(diagonal),40)
        # Normal 2x2 block [[100,120],[120,100]] has eigenvalues 100±120.
        eigenvalues=[100-120,100+120,100,40,50,60]
        self.assertTrue(all(x>0 for x in diagonal));self.assertLess(min(eigenvalues),0)
        diagonal[-1]=0;self.assertEqual(min(diagonal),0)


@unittest.skipIf(Draft202012Validator is None, 'optional jsonschema dev dependency not installed')
class StabilitySchemaTests(unittest.TestCase):
    def setUp(self):
        self.catalog=read_catalog('claims')
        self.validator=Draft202012Validator(load_json(ROOT/'schemas/claims.schema.json'))

    def invalid(self,record_id,mutate):
        bad=copy.deepcopy(self.catalog);mutate(select_records(bad, [record_id])[0])
        self.assertTrue(list(self.validator.iter_errors(bad)))

    def test_catalog_and_unordered_metadata_validate(self):
        self.validator.check_schema(self.validator.schema);self.validator.validate(self.catalog)
        reordered=copy.deepcopy(self.catalog)
        for c in select_records(reordered, CORE_STABILITY_IDS):
            c['parameters'].reverse();c['criterion']['inequalities'].reverse()
        self.validator.validate(reordered)

    def test_predicates_cannot_be_bounds_models_or_runtime_outputs(self):
        for i in CORE_STABILITY_IDS:
            for key,value in [('claim_type','theoretical_bound'),('claim_type','model_relation'),('direction','relation'),('direction','upper'),('bound_kind','scalar_modulus_bound'),('evaluation_support','composite_evaluate'),('dependencies',['hs_bulk_3d_two_phase']),('si_unit','1'),('si_unit','Pa'),('quantity_dimension','dimensionless'),('result',True)]:
                with self.subTest(i=i,key=key,value=value):self.invalid(i,lambda c:c.update({key:value}))
        self.invalid('hs_bulk_3d_two_phase',lambda c:c.update(criterion=criteria()[0]['criterion']))

    def test_missing_wrong_duplicate_parameters_and_matrix_template_fail_closed(self):
        for i in CORE_STABILITY_IDS:
            for key in ('parameters','criterion'):
                self.invalid(i,lambda c:c.pop(key))
            self.invalid(i,lambda c:c['parameters'].pop())
            self.invalid(i,lambda c:c['parameters'].append(copy.deepcopy(c['parameters'][0])))
            self.invalid(i,lambda c:c['parameters'][0].update(symbol='wrong'))
            self.invalid(i,lambda c:c['parameters'][0].update(si_unit='GPa'))
            self.invalid(i,lambda c:c['parameters'][0].update(quantity='strength'))
            self.invalid(i,lambda c:c['criterion']['stiffness_matrix'][0].__setitem__(0,'C99'))
        self.invalid('hexagonal_born_stability',lambda c:c['criterion']['stiffness_matrix'][5].__setitem__(5,'C66'))

    def test_strictness_dimensions_all_conditions_and_conventions_cannot_be_weakened(self):
        for i in CORE_STABILITY_IDS:
            for key,value in [('operator','>='),('rhs',-1),('si_unit','1'),('expression','C11'),('dimension','dimensionless')]:
                if i=='orthorhombic_born_stability' and key=='expression':continue
                self.invalid(i,lambda c:c['criterion']['inequalities'][0].update({key:value}))
            self.invalid(i,lambda c:c['criterion']['inequalities'].pop())
            self.invalid(i,lambda c:c['criterion']['inequalities'].append(copy.deepcopy(c['criterion']['inequalities'][0])))
            for key,value in [('combination','any'),('strain_vector','tensor_shear'),('voigt_order',['xx','yy','zz','xy','yz','xz'])]:
                self.invalid(i,lambda c:c['criterion'].update({key:value}))
            for key,value in [('reference_state','loaded'),('energy_approximation','finite_strain'),('perturbation_class','phonon'),('stiffness_convention','Mandel'),('axes','unknown'),('elastic_symmetry','unknown')]:
                self.invalid(i,lambda c:c['required_assumptions'].update({key:value}))
                self.invalid(i,lambda c:c['required_assumptions'].pop(key))
        self.invalid('orthorhombic_born_stability',lambda c:c['criterion']['inequalities'][2].update(si_unit='Pa'))


if __name__=='__main__':unittest.main()
