import copy
from decimal import Inexact, localcontext
import json
import subprocess
import sys
import unittest

from materials_boundaries import ValidationError, evaluate, load_json, validate_instance
from materials_boundaries.catalog import read_catalog
from materials_boundaries.conversions import CONVERSION_RULE_ID, isotropic_moduli
from materials_boundaries.i18n import LANGUAGES, translate
from catalog_fixtures import expected_provenance
from test_engine import ROOT, bounds


def literature():
    return load_json(ROOT / 'examples/literature-epoxy-glass-model.json')


class LiteratureModelTests(unittest.TestCase):
    def test_literature_fixture_approximate_expected_bounds(self):
        hs, reuss, voigt = bounds(literature())
        self.assertAlmostEqual(hs['result']['lower'], 5.594721790628027, places=12)
        self.assertAlmostEqual(hs['result']['upper'], 9.407756983997828, places=12)
        self.assertAlmostEqual(reuss['result']['lower'], 5.303274288781536, places=12)
        self.assertAlmostEqual(voigt['result']['upper'], 13.6, places=12)

    def test_raw_values_and_derived_moduli(self):
        data=literature(); records=data['provenance']['model_evidence']['raw_parameters']
        self.assertEqual([(p['youngs_modulus']['value'],p['poissons_ratio']) for p in records],[(3.12,0.38),(76,0.25)])
        for phase,raw in zip(data['phases'],records):
            k,g=isotropic_moduli(raw['youngs_modulus']['value'],raw['poissons_ratio'])
            self.assertAlmostEqual(k,phase['bulk_modulus']['value'],places=12)
            self.assertAlmostEqual(g,phase['shear_modulus']['value'],places=12)

    def test_source_parameter_and_calculator_assumptions_separated(self):
        data=literature(); e=data['provenance']['model_evidence']
        self.assertEqual(data['provenance']['kind'],'literature_model')
        self.assertEqual(e['parameter_basis'],'literature_model_inputs')
        self.assertEqual(e['fraction_basis'],'calculator_choice')
        self.assertEqual(e['condition_basis']['constitutive_law'],'source_model')
        self.assertEqual(e['condition_basis']['constituent_symmetry'],'source_model')
        self.assertEqual(e['condition_basis']['effective_symmetry'],'calculator_assumption')
        self.assertEqual(e['condition_basis']['interface'],'calculator_assumption')
        self.assertEqual([p['volume_fraction'] for p in data['phases']],[0.8,0.2])
        for key in ('temperature_k','material_grade','cure_state','measurement_uncertainty'):
            self.assertIsNone(e[key])

    def test_provenance_preserved_in_evaluation(self):
        data=literature()
        self.assertEqual(evaluate(data)['input_provenance'],data['provenance'])

    def test_nested_provenance_snapshot_is_independent(self):
        data=literature(); output=evaluate(data)
        data['provenance']['model_evidence']['raw_parameters'][0]['youngs_modulus']['value']=99
        self.assertEqual(output['input_provenance']['model_evidence']['raw_parameters'][0]['youngs_modulus']['value'],3.12)
        output['input_provenance']['model_evidence']['condition_basis']['interface']='unknown'
        self.assertEqual(data['provenance']['model_evidence']['condition_basis']['interface'],'calculator_assumption')

    def test_source_resolves_and_license_is_not_open(self):
        source_id=literature()['provenance']['model_evidence']['source_id']
        source=next(x for x in read_catalog('sources')['records'] if x['id']==source_id)
        self.assertEqual(source['doi'],'10.1016/j.ijsolstr.2008.08.010')
        self.assertEqual(source['year'],2009)
        self.assertEqual(source['license'], expected_provenance('sources', source['id'])['license'])
        self.assertIn('30 August 2008', ' '.join(source['claim_notes']))

    def test_conversion_domain_and_finiteness(self):
        for e,nu in [(0,0.2),(-1,0.2),(1,-1),(1,0.5),(1,0.6),(True,0.3),(1,False),(float('nan'),0.3),(1,float('inf')),(1,None),(10**400,0.3)]:
            with self.subTest(e=e,nu=nu),self.assertRaises(ValueError):isotropic_moduli(e,nu)

    def test_conversion_uses_independent_decimal_context(self):
        expected=isotropic_moduli(3.12,0.38)
        with localcontext() as ctx:
            ctx.prec=1;ctx.Emax=2;ctx.Emin=-2;ctx.traps[Inexact]=True
            self.assertEqual(isotropic_moduli(3.12,0.38),expected)
            self.assertEqual(evaluate(literature())['evaluations'][0]['applicability'],'satisfied')

    def test_model_requires_complete_structured_evidence(self):
        data=literature();del data['provenance']['model_evidence']
        with self.assertRaises(ValidationError):validate_instance(data)
        for key in literature()['provenance']['model_evidence']:
            data=literature();del data['provenance']['model_evidence'][key]
            with self.subTest(key=key),self.assertRaises(ValidationError):validate_instance(data)

    def test_unknown_condition_remains_unknown(self):
        data=literature();data['conditions']['effective_symmetry']=None
        data['provenance']['model_evidence']['condition_basis']['effective_symmetry']='unknown'
        item=evaluate(data)['evaluations'][0]
        self.assertEqual(item['applicability'],'unknown')
        self.assertIsNone(item['result'])

    def test_inconsistent_condition_basis_rejected(self):
        for condition,basis in [(None,'calculator_assumption'),('isotropic','unknown')]:
            data=literature();data['conditions']['effective_symmetry']=condition
            data['provenance']['model_evidence']['condition_basis']['effective_symmetry']=basis
            with self.assertRaises(ValidationError):validate_instance(data)

    def test_derived_values_cross_checked_in_common_units(self):
        data=literature();data['phases'][0]['bulk_modulus']={'value':4333.333333333334,'unit':'MPa'}
        validate_instance(data)
        data['phases'][0]['bulk_modulus']['value']=5000
        with self.assertRaises(ValidationError):validate_instance(data)

    def test_invalid_references_and_duplicate_raw_phase_rejected(self):
        for mode in ('source','phase','duplicate','missing'):
            data=literature();e=data['provenance']['model_evidence']
            if mode=='source':e['source_id']='not-in-source-ids'
            elif mode=='phase':e['raw_parameters'][0]['phase_id']='absent'
            elif mode=='duplicate':e['raw_parameters'][1]['phase_id']='epoxy_model'
            else:e['raw_parameters'].pop()
            with self.subTest(mode=mode),self.assertRaises(ValidationError):validate_instance(data)

    def test_unsupported_metadata_and_formula_execution_rejected(self):
        for key,value in [('conversion_rule_id','__import__("os").system("false")'),('fraction_basis','measured_specimen'),('parameter_basis','measured'),('temperature_k',0),('extra',True)]:
            data=literature();data['provenance']['model_evidence'][key]=value
            with self.subTest(key=key),self.assertRaises(ValidationError):validate_instance(data)
        data=literature();data['provenance']['kind']='measured'
        with self.assertRaises(ValidationError):validate_instance(data)

    def test_localized_warning_and_canonical_json(self):
        outputs=[]
        for lang in LANGUAGES:
            args=[sys.executable,'-m','materials_boundaries','evaluate','examples/literature-epoxy-glass-model.json','--lang',lang]
            result=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn(translate('literature_model_notice',lang),result.stdout)
            self.assertNotIn(translate('synthetic_notice',lang),result.stdout)
            raw=subprocess.run(args+['--json'],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(raw.returncode,0,raw.stderr);outputs.append(raw.stdout)
        self.assertEqual(len(set(outputs)),1)
        self.assertEqual(json.loads(outputs[0])['input_provenance']['kind'],'literature_model')

if __name__=='__main__':unittest.main()
