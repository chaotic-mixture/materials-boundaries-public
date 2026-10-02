import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from materials_boundaries import evaluate, load_json
from materials_boundaries.catalog import read_catalog
from materials_boundaries.engine import EXPECTED
from materials_boundaries.i18n import LANGUAGES, translate
from catalog_fixtures import expected_provenance
from test_engine import ROOT, example
from catalog_fixtures import HISTORICAL_SOURCE_IDS

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None


class CatalogTests(unittest.TestCase):
    def test_unique_ids_and_evidence_integrity(self):
        sources=read_catalog('sources')['records']; claims=read_catalog('claims')['records']
        ids=[s['id'] for s in sources]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(len({c['id'] for c in claims}),len(claims))
        for claim in claims:
            for evidence in claim['evidence']:
                self.assertIn(evidence['source_id'],ids)
            self.assertFalse(claim['verification']['independent_scientific_review'])
            if claim['evaluation_support'] == 'composite_evaluate':
                for key,value in EXPECTED.items():
                    self.assertEqual(claim['required_assumptions'][key],value)

    def test_registry_matches_claim_records(self):
        rows=[c for c in read_catalog('claims')['records'] if c['evaluation_support'] == 'composite_evaluate']
        self.assertEqual(len(rows), 8)
        claims={c['id']:c for c in rows}
        evaluations=evaluate(example())['evaluations']
        self.assertEqual(len(evaluations), 8)
        self.assertEqual(len(claims), 8)
        self.assertEqual({identifier:x['rule_id'] for identifier,x in claims.items()},
                         {x['claim_id']:x['rule_id'] for x in evaluations})
        for evaluation in evaluations:
            claim=claims[evaluation['claim_id']]
            self.assertEqual(set(claim['required_assumptions']),{x['condition_id'] for x in evaluation['checks']})

    def test_source_records_never_imply_full_original_verification(self):
        sources={s['id']:s for s in read_catalog('sources')['records']}
        self.assertEqual(sources['hashin_shtrikman_1963']['read_status'], expected_provenance('sources', sources['hashin_shtrikman_1963']['id'])['read_status'])
        self.assertEqual(sources['materials_project_elasticity']['read_status'], expected_provenance('sources', sources['materials_project_elasticity']['id'])['read_status'])
        for identifier in HISTORICAL_SOURCE_IDS:
            self.assertEqual(sources[identifier]['bundled_content'], expected_provenance('sources', sources[identifier]['id'])['bundled_content'])

    def test_all_locales_complete_nonempty(self):
        d=read_catalog('locales');languages=d['languages']
        self.assertEqual(set(languages),set(LANGUAGES))
        for lang in LANGUAGES:
            self.assertEqual(set(languages[lang]),set(languages['en']))
            self.assertTrue(all(isinstance(v,str) and v.strip() for v in languages[lang].values()))

    def test_fallback_english_then_visible_marker(self):
        fake={'languages':{'en':{'known':'English'},'zh':{}}}
        with patch('materials_boundaries.i18n.read_catalog',return_value=fake):
            self.assertEqual(translate('known','zh'),'English')
            self.assertEqual(translate('absent','zh'),'[missing:absent]')

    def test_unknown_language_rejected(self):
        with self.assertRaises(ValueError):translate('hs_bulk','fr')

    @unittest.skipIf(Draft202012Validator is None,'optional dev dependency jsonschema is not installed')
    def test_evaluation_schema_rejects_inconsistent_states(self):
        schema=load_json(ROOT/'schemas/evaluation.schema.json')
        validator=Draft202012Validator(schema)
        good=evaluate(example())
        mutations=[]
        for field,value in [('applicability','unknown'),('computation','not_computed'),('result',{'unit':'GPa'}),('error','unexpected'),('rule_id','voigt_bulk_v1')]:
            bad=copy.deepcopy(good); bad['evaluations'][0][field]=value; mutations.append(bad)
        bad=copy.deepcopy(good); bad['evaluations'][0]['checks'][0]['state']='violated';mutations.append(bad)
        unknown=evaluate(load_json(ROOT/'examples/unknown-isotropy.json'))
        unknown['evaluations'][0]['computation']='computed'
        unknown['evaluations'][0]['result']={'lower':999,'upper':1000,'unit':'GPa'}
        mutations.append(unknown)
        for bad in mutations:self.assertTrue(list(validator.iter_errors(bad)))

    @unittest.skipIf(Draft202012Validator is None,'optional dev dependency jsonschema is not installed')
    def test_exported_schemas_examples_catalogs_outputs(self):
        for name in ('instance','claims','sources','evaluation'):
            schema=load_json(ROOT/'schemas'/f'{name}.schema.json')
            Draft202012Validator.check_schema(schema)
            validator=Draft202012Validator(schema,format_checker=FormatChecker())
            if name=='instance':
                docs=[load_json(p) for p in (ROOT/'examples').glob('*.json')]
            elif name=='evaluation':
                docs=[evaluate(load_json(p)) for p in (ROOT/'examples').glob('*.json')]
            else:docs=[read_catalog(name)]
            for doc in docs:validator.validate(doc)


class CLITests(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-m','materials_boundaries',*args],cwd=ROOT,text=True,capture_output=True)

    def test_four_language_human_output(self):
        for lang in LANGUAGES:
            result=self.run_cli('evaluate','examples/synthetic-two-phase.json','--lang',lang)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn(translate('hs_bulk',lang),result.stdout)
            self.assertIn('16.25',result.stdout)
            self.assertIn('17.5',result.stdout)
            self.assertIn(translate('approximate_notice',lang),result.stdout)

    def test_json_output_identical_across_languages(self):
        outputs=[self.run_cli('evaluate','examples/synthetic-two-phase.json','--lang',lang,'--json').stdout for lang in LANGUAGES]
        self.assertEqual(len(set(outputs)),1)
        self.assertEqual(json.loads(outputs[0])['evaluations'][0]['result']['lower'],16.25)

    def test_unknown_and_violated_are_successful_evaluation(self):
        for filename,state in [('unknown-isotropy','unknown'),('anisotropic-constituent','violated')]:
            result=self.run_cli('evaluate',f'examples/{filename}.json','--json')
            self.assertEqual(result.returncode,0)
            self.assertEqual(json.loads(result.stdout)['evaluations'][0]['applicability'],state)

    def test_validate_command(self):
        result=self.run_cli('validate','examples/synthetic-two-phase.json')
        self.assertEqual(result.returncode,0)
        self.assertIn(translate('validation','en') + ': ' + translate('valid','en'),result.stdout)

    def test_missing_input_is_structured_error(self):
        result=self.run_cli('evaluate','does-not-exist.json')
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stderr)['error'],'invalid_input')

    def test_catalog_command(self):
        result=self.run_cli('catalog','claims')
        self.assertEqual(result.returncode,0)
        self.assertEqual(json.loads(result.stdout), read_catalog('claims'))

    def test_unsupported_language(self):
        result=self.run_cli('evaluate','examples/synthetic-two-phase.json','--lang','fr')
        self.assertEqual(result.returncode,2)

if __name__ == '__main__':unittest.main()
