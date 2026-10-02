"""Synthetic polynomial contracts, independent arithmetic and honest static exports."""
import copy
import csv
from decimal import localcontext
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from materials_boundaries.catalog import read_catalog
from materials_boundaries.temperature import (TemperatureError, evaluate_temperature, get_model,
                                             render_prediction, validate_model_catalog)
from materials_boundaries.temperature_visualization import (build_temperature_comparison, comparison_csv,
    comparison_json, labels, render_temperature_html, render_temperature_svg, validate_temperature_comparison)
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs
from test_engine import ROOT, example
from materials_boundaries import evaluate, load_json

LINEAR='synthetic_linear_temperature'; OVERLAP='synthetic_overlap_temperature'


def request(mid=LINEAR, value=50):
    return {'schema_version':'1.0.0','model_id':mid,'temperature':{'value':value,'unit':'K'}}


class TemperatureTests(unittest.TestCase):
    def test_original_catalog_science_and_evidence_remain(self):
        baseline=load_json(ROOT/'tests/fixtures/pre_temperature_records.json')
        for kind,records in baseline.items():
            live={r['id']:r for r in read_catalog(kind)['records']}
            for r in records:
                for k,v in r.items():
                    if k in ('evidence','claim_notes','urls'):
                        for entry in v:self.assertIn(entry,live[r['id']][k])
                    else:self.assertEqual(v,live[r['id']][k])

    def test_all_independent_decimal_arithmetic_fixtures(self):
        fixture=load_json(ROOT/'tests/fixtures/temperature_arithmetic.json')
        for f in fixture['synthetic_checks']:
            result=evaluate_temperature(request(f['model_id'],float(f['T_K'])))
            prediction=next(p for p in result['predictions'] if p['branch_id']==f['branch_id'])
            self.assertAlmostEqual(prediction['value'],float(f['E_GPa_decimal']),places=11)

    def test_exact_authored_coefficient_digits(self):
        self.assertEqual(get_model(LINEAR)['branches'][0]['coefficients_text'],
                         ['10','0.1','0','0','0'])
        self.assertEqual(get_model(OVERLAP)['branches'][0]['coefficients_text'],
                         ['20','0.1','0','0','0'])
        self.assertEqual(get_model(OVERLAP)['branches'][1]['coefficients_text'],
                         ['30','0.05','0','0','0'])

    def test_artificial_ranges_are_inclusive_and_never_extrapolated(self):
        for mid,value in [(LINEAR,0),(LINEAR,9.999),(LINEAR,100.001),(LINEAR,110),
                          (OVERLAP,19.999),(OVERLAP,100.001)]:
            r=evaluate_temperature(request(mid,value));self.assertEqual(r['status'],'out_of_range');self.assertEqual(r['predictions'],[])
        for mid,value in [(LINEAR,10),(LINEAR,100),(OVERLAP,20),(OVERLAP,100)]:
            self.assertEqual(evaluate_temperature(request(mid,value))['status'],'prediction')
        branch=get_model(LINEAR)['branches'][0]
        self.assertIsNone(branch['source_data_range_K'])
        self.assertEqual(branch['range_status'],'artificial_demonstration_interval')

    def test_overlap_both_predictions_never_one_selected(self):
        r=evaluate_temperature(request(OVERLAP,50))
        self.assertEqual(r['status'],'ambiguous_overlap');self.assertEqual(len(r['predictions']),2)
        self.assertEqual([p['value'] for p in r['predictions']],[25,32.5])
        self.assertNotIn('value',r);self.assertIsNone(r['uncertainty_band'])
        self.assertEqual([p['branch_id'] for p in evaluate_temperature(request(OVERLAP,49.999))['predictions']],['synthetic_overlap_20_50'])
        self.assertEqual([p['branch_id'] for p in evaluate_temperature(request(OVERLAP,50.001))['predictions']],['synthetic_overlap_50_100'])

    def test_strict_finite_inputs(self):
        for value in (True,False,None,'57',float('nan'),float('inf'),-1,10**400):
            with self.subTest(value=str(value)[:30]),self.assertRaises(TemperatureError):evaluate_temperature(request(OVERLAP,value))
        for mutation in (lambda x:x['temperature'].update(unit='C'), lambda x:x.update(extra=1),
                         lambda x:x['temperature'].update(extra=1),lambda x:x.update(model_id='missing'),
                         lambda x:x.update(schema_version='2.0.0')):
            x=request();mutation(x)
            with self.assertRaises(TemperatureError):evaluate_temperature(x)

    def test_input_snapshot_independence_and_decimal_context(self):
        x=request(OVERLAP,50);before=copy.deepcopy(x);r=evaluate_temperature(x)
        self.assertEqual(x,before)
        with localcontext() as context:
            context.prec=4
            self.assertEqual(r,evaluate_temperature(x))
        r['model_snapshot']['material']['temper']='invented'
        self.assertIsNone(evaluate_temperature(x)['model_snapshot']['material']['temper'])

    def test_text_prediction_rejects_boolean_numeric_alias_tampering(self):
        for field,value in [('independent_scientific_review',0),('synthetic_arithmetic_checked',1)]:
            r=evaluate_temperature(request());r['model_snapshot']['verification'][field]=value
            with self.assertRaises(TemperatureError):render_prediction(r)
        r=evaluate_temperature(request());r['model_snapshot']['branches'][0]['reported_fit_error']['value']=True
        with self.assertRaises(TemperatureError):render_prediction(r)

    def test_synthetic_provenance_and_absent_uncertainty_retained(self):
        for mid in (LINEAR,OVERLAP):
            model=get_model(mid)
            self.assertTrue(all(v['value'] is None for v in model['unknown_conditions'].values()))
            self.assertFalse(model['verification']['independent_scientific_review'])
            self.assertFalse(model['verification']['empirical_validation'])
            self.assertFalse(model['author_provenance']['is_empirical'])
            self.assertFalse(model['author_provenance']['derived_from_measurements'])
            self.assertNotIn('original_reference',model)
            for b in model['branches']:
                fit=b['reported_fit_error'];self.assertIsNone(fit['value']);self.assertIsNone(fit['unit'])
                self.assertIsNone(fit['statistic']);self.assertEqual(fit['status'],'not_applicable_synthetic_demo')
                self.assertFalse(fit['is_validated_maximum_error_bound']);self.assertFalse(fit['is_confidence_interval'])
            self.assertEqual(evaluate_temperature(request(mid))['specimen_applicability'],'not_applicable_synthetic_demo')

    def test_bad_model_contracts_fail_closed(self):
        changes=[lambda m:m.update(equation_family='eval_anything'),lambda m:m.update(output_unit='Pa'),
                 lambda m:m.update(equation_display='__import__("os")'),lambda m:m['branches'][0].update(coefficients_text=['NaN']*5),
                 lambda m:m['branches'][0].update(equation_range_K=[100,10]),
                 lambda m:m['branches'][0]['reported_fit_error'].update(is_confidence_interval=True),
                 lambda m:m['descriptions'].pop('ja')]
        for change in changes:
            catalog=read_catalog('temperature_models');change(catalog['records'][0])
            with self.assertRaises(TemperatureError):validate_model_catalog(catalog)

    def test_nonfinite_or_nonpositive_polynomial_outputs_fail_closed(self):
        for coefficients in (['0','0','0','0','0'], ['-1','0','0','0','0'],
                             ['0','0','0','0','1e308']):
            catalog=read_catalog('temperature_models')
            catalog['records'][0]['branches'][0]['coefficients_text']=coefficients
            with patch('materials_boundaries.temperature.read_catalog',return_value=catalog):
                with self.assertRaises(TemperatureError):evaluate_temperature(request())

    def test_source_reference_schema_and_cross_catalog_ids(self):
        original=load_catalogs(ROOT/'materials_boundaries/data')
        changes=[lambda c:c['temperature_models']['records'][0]['source_ids'].append('missing'),
                 lambda c:c['temperature_models']['records'][0].update(id='voigt_bulk'),
                 lambda c:c['temperature_models']['records'][0].update(unreviewed=1),
                 lambda c:c['temperature_models']['records'][0]['unknown_conditions']['pressure'].update(value=101325),
                 lambda c:c['temperature_models']['records'][0]['verification'].update(independent_scientific_review=True)]
        for change in changes:
            candidate=copy.deepcopy(original);change(candidate)
            with self.assertRaises(CatalogValidationError):validate_catalogs(candidate)

    def test_required_scientific_notice_cannot_vanish_from_all_languages(self):
        catalogs=load_catalogs(ROOT/'materials_boundaries/data')
        for labels_ in catalogs['temperature_locales']['languages'].values():labels_.pop('fit_notice')
        with self.assertRaises(CatalogValidationError):validate_catalogs(catalogs)

    def test_local_comparison_and_input_schemas(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        schemas=[load_json(ROOT/f'schemas/{name}.schema.json') for name in ('temperature_models','temperature_input','temperature_comparison')]
        registry=Registry().with_resources((s['$id'],Resource.from_contents(s)) for s in schemas)
        Draft202012Validator(schemas[1],registry=registry).validate(request())
        Draft202012Validator(schemas[2],registry=registry).validate(build_temperature_comparison(points_per_branch=3))

    def test_supported_temperature_family_appendable(self):
        catalogs=load_catalogs(ROOT/'materials_boundaries/data');new=copy.deepcopy(catalogs['temperature_models']['records'][0])
        new['id']='synthetic_temperature_append';new['branches'][0]['id']='synthetic_temperature_branch'
        new['name']='SYNTHETIC appendability fixture only'
        catalogs['temperature_models']['records'].append(new);validate_catalogs(catalogs)
        before=evaluate(example())
        with patch('materials_boundaries.temperature.read_catalog', side_effect=lambda n:copy.deepcopy(catalogs[n])):
            r=evaluate_temperature(request(new['id']))
            self.assertEqual(r['predictions'][0]['value'],15)
        self.assertEqual(before,evaluate(example()))

    def test_locale_key_parity_and_four_language_prediction(self):
        for lang in ('en','zh','ja','de'):
            self.assertEqual(set(labels(lang)),set(labels('en')))
            text=render_prediction(evaluate_temperature(request(OVERLAP,50)),lang)
            self.assertIn('25',text);self.assertIn(labels(lang)['fit_notice'],text)
            self.assertIn(labels(lang)['endpoint_notice'],text);self.assertNotIn('[missing:',text)


class TemperatureVisualizationTests(unittest.TestCase):
    def setUp(self):self.bundle=build_temperature_comparison([LINEAR,OVERLAP],points_per_branch=11)

    def test_deterministic_comparison_and_no_composite_change(self):
        self.assertEqual(self.bundle,build_temperature_comparison([LINEAR,OVERLAP],points_per_branch=11))
        self.assertEqual(len(evaluate(example())['evaluations']),8)
        self.assertFalse(self.bundle['overlay_allowed']);self.assertIsNone(self.bundle['uncertainty_band'])

    def test_exact_branch_endpoints_and_overlap_in_every_grid(self):
        for count in [2,3,101,501]:
            b=build_temperature_comparison(points_per_branch=count)
            for case in b['cases']:
                for series in case['series']:
                    self.assertEqual([series['points'][0]['temperature_K'],series['points'][-1]['temperature_K']],series['equation_range_K'])
                    self.assertEqual(len(series['points']),count)
            overlap=next(c for c in b['cases'] if c['model_id']==OVERLAP)['overlaps'][0]
            self.assertEqual(overlap['temperature_K'],50);self.assertEqual(len(overlap['predictions']),2)

    def test_invalid_sampling_and_ids(self):
        for count in [True,1,502,2.5,'10']:
            with self.assertRaises(TemperatureError):build_temperature_comparison(points_per_branch=count)
        for ids in [[],[LINEAR,LINEAR],['unknown'],'bad']:
            with self.assertRaises(TemperatureError):build_temperature_comparison(ids)

    def test_tampered_snapshots_results_status_metadata_and_extra_keys_rejected(self):
        changes=[lambda b:b['cases'][0]['series'][0]['points'][0].update(value_GPa=0),
                 lambda b:b['cases'][1]['overlaps'][0]['predictions'].pop(),
                 lambda b:b['cases'][0]['model_snapshot']['material'].update(temper='T651'),
                 lambda b:b['cases'][0]['source_snapshots'][0].update(title='fake'),
                 lambda b:b.update(overlay_allowed=True),lambda b:b.update(extra=1),
                 lambda b:b['cases'][0]['series'][0]['points'][0].update(temperature_K=float('nan'))]
        for change in changes:
            candidate=copy.deepcopy(self.bundle);change(candidate)
            for fn in [validate_temperature_comparison,comparison_json,comparison_csv,render_temperature_html,render_temperature_svg]:
                with self.assertRaises(TemperatureError):fn(candidate)

    def test_csv_retains_both_shared_endpoint_rows_and_units(self):
        rows=list(csv.DictReader(io.StringIO(comparison_csv(self.bundle))))
        overlap=[r for r in rows if r['model_id']==OVERLAP and float(r['temperature_K'])==50]
        self.assertEqual(len(overlap),2);self.assertTrue(all(r['status']=='ambiguous_overlap' for r in overlap))
        self.assertNotEqual(overlap[0]['predicted_youngs_modulus_GPa'],overlap[1]['predicted_youngs_modulus_GPa'])

    def test_static_svg_structure_branch_separation_and_four_languages(self):
        for lang in ('en','zh','ja','de'):
            for width in (380,1100):
                svg=render_temperature_svg(self.bundle,lang=lang,width=width);root=ET.fromstring(svg)
                ns={'s':'http://www.w3.org/2000/svg'}
                self.assertEqual(len(root.findall('.//s:polyline',ns)),3)
                self.assertEqual(len(root.findall('.//s:circle',ns)),6)
                self.assertEqual(len(root.findall('.//s:polygon',ns)),0)
                self.assertIn(labels(lang)['x_axis'],svg);self.assertIn(labels(lang)['y_axis'],svg)
                self.assertIn('25.000000',svg);self.assertIn('32.500000',svg)
                html=render_temperature_html(self.bundle,lang=lang)
                self.assertNotIn('<script',html);self.assertNotIn('[missing:',html)
                self.assertIn('materials_boundaries_synthetic_temperature_demo',html)

    def test_checked_in_synthetic_exports_are_canonical_and_reproducible(self):
        # Preserve the published v0.16.0 artifacts byte-for-byte. Rebuild with
        # only that historical engine label; no values, snapshots or conditions
        # are normalized. Current engine labels are checked in release metadata.
        with patch('materials_boundaries.__version__', '0.16.0'):
            # Pin this published sample by ID; additions to the live catalog remain welcome.
            for folder,ids in [('visualization',[LINEAR,OVERLAP]),('catalog-visualization',[LINEAR,OVERLAP,'synthetic_quadratic_temperature','synthetic_quartic_temperature','synthetic_interval_temperature'])]:
                target=ROOT/'examples/temperature'/folder
                bundle=build_temperature_comparison(ids,points_per_branch=101)
                self.assertEqual((target/'temperature-comparison.json').read_text(),comparison_json(bundle))
                self.assertEqual((target/'temperature-comparison.csv').read_text(),comparison_csv(bundle))
                for lang in ('en','zh','ja','de'):
                    self.assertEqual((target/f'temperature-comparison.{lang}.html').read_text(),render_temperature_html(bundle,lang=lang))
                    self.assertEqual((target/f'temperature-comparison.{lang}.svg').read_text(),render_temperature_svg(bundle,lang=lang))
                    self.assertEqual((target/f'temperature-comparison.narrow.{lang}.svg').read_text(),render_temperature_svg(bundle,lang=lang,width=380))

    def test_cli_files_errors_and_output(self):
        def run(*args):return subprocess.run([sys.executable,'-m','materials_boundaries',*args],cwd=ROOT,text=True,capture_output=True)
        r=run('temperature','evaluate','examples/temperature/synthetic-overlap-50k.json','--json')
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['status'],'ambiguous_overlap')
        r=run('temperature','evaluate','examples/temperature/synthetic-linear-outside-5k.json','--json')
        self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout)['predictions'],[])
        with tempfile.TemporaryDirectory() as tmp:
            r=run('temperature','plot','--output',tmp,'--points','3','--lang','de')
            self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(len(list(Path(tmp).iterdir())),5)
            file=Path(tmp)/'bad.json';file.write_text('{"schema_version":"1.0.0","model_id":"x","temperature":{"value":NaN,"unit":"K"}}')
            r=run('temperature','evaluate',str(file),'--json');self.assertEqual(r.returncode,2)
        r=run('temperature','plot','--output','/tmp/unused-temperature','--points','1');self.assertEqual(r.returncode,2)
        for lang in ('en','zh','ja','de'):
            r=run('temperature','--lang',lang,'evaluate','--help');self.assertEqual(r.returncode,0);self.assertNotIn('[missing:',r.stdout)


if __name__=='__main__':unittest.main()
