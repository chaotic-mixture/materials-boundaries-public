"""Independent transcription, growth-safe contracts and trustworthy point exports."""
import copy
from provenance_corrections import historical_record, historical_temperature_result
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from materials_boundaries import evaluate, load_json
from materials_boundaries.catalog import CatalogLookupError, query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.predictions import (DEFAULT_GROUP, PredictionError, canonical_json,
    prediction_labels, validate_prediction_catalog)
from materials_boundaries.prediction_visualization import (build_prediction_comparison, comparison_json,
    comparison_csv, export_prediction_comparison, render_prediction_html, render_prediction_svg,
    validate_prediction_comparison)
from materials_boundaries.temperature import evaluate_temperature
from scripts.validate_catalogs import CatalogValidationError, load_catalogs, validate_catalogs
from test_engine import ROOT, example

FIXTURE=load_json(ROOT/'tests/fixtures/prediction_source_transcription.json')

def contribution_catalogs():
    """Idempotent synthetic same-family addition; never a fourth real result."""
    catalogs=load_catalogs(ROOT/'materials_boundaries/data')
    catalog=catalogs['computational_predictions']
    source=copy.deepcopy(next(s for s in catalogs['sources']['records'] if s['id']==FIXTURE['source_id']))
    source.update(id='synthetic_prediction_source',title='SYNTHETIC prediction plumbing only',doi=None,
                  urls=['https://example.invalid/prediction'],read_status='synthetic_not_a_real_source',
                  license={'status':'not_applicable_synthetic','identifier':None},
                  claim_notes=['SYNTHETIC TEST ONLY; no paper inspection or real added prediction.'],
                  provenance={'curation_date':'2026-10-02','method':'Synthetic plumbing fixture; not source verification.'})
    protocol=copy.deepcopy(next(p for p in catalog['protocols'] if p['id']==FIXTURE['protocol_id']))
    protocol.update(id='synthetic_prediction_protocol',source_id=source['id'])
    for e in protocol['evidence']:e.update(source_id=source['id'],url='https://example.invalid/method',locator='SYNTHETIC method copy, not inspected')
    group=copy.deepcopy(next(g for g in catalog['comparison_groups'] if g['id']==DEFAULT_GROUP))
    group.update(id='synthetic_prediction_group',source_id=source['id'],protocol_id=protocol['id'],record_ids=['synthetic_prediction_record'])
    group['names']={lang:'SYNTHETIC TEST '+lang for lang in ('en','zh','ja','de')}
    record=copy.deepcopy(next(r for r in catalog['records'] if r['id']==FIXTURE['records'][0]['id']))
    record.update(id='synthetic_prediction_record',source_id=source['id'],protocol_id=protocol['id'],comparison_group_id=group['id'],name='SYNTHETIC TEST ONLY')
    record['names']={lang:'SYNTHETIC TEST '+lang for lang in ('en','zh','ja','de')}
    for e in record['evidence']:e.update(source_id=source['id'],url='https://example.invalid/value',locator='SYNTHETIC value copy, not inspected')
    for sequence,item in ((catalogs['sources']['records'],source),(catalog['protocols'],protocol),(catalog['comparison_groups'],group),(catalog['records'],record)):
        old=next((r for r in sequence if r['id']==item['id']),None)
        if old is None:sequence.append(item)
        elif old!=item:raise AssertionError('Existing synthetic prediction fixture differs')
    return catalogs


class PredictionCatalogTests(unittest.TestCase):
    def test_independent_transcription_fixture_and_geometry(self):
        c=read_catalog('computational_predictions');validate_prediction_catalog(c)
        records={r['id']:r for r in c['records']}
        for expected in FIXTURE['records']:
            record=records[expected['id']]
            for key,value in expected.items():self.assertEqual(record[key],value)
            for key in ('source_id','protocol_id','source_table','source_pdf_page_1_based'):
                self.assertEqual(record[key],FIXTURE[key])
            self.assertEqual(record['reported_decimal_places'],2)
            self.assertEqual(record['comparison_group_id'],FIXTURE['group_id'])
            self.assertIn(FIXTURE['source_version'].split(':')[1],record['evidence'][0]['url'])
        p=next(p for p in c['protocols'] if p['id']==FIXTURE['protocol_id'])
        self.assertEqual(p['geometry']['slip_plane_miller_indices'],FIXTURE['plane'])
        self.assertEqual(p['geometry']['slip_direction_indices'],FIXTURE['direction'])
        self.assertEqual(sum(a*b for a,b in zip(FIXTURE['plane'],FIXTURE['direction'])),0)
        self.assertIn('1992',p['calculation']['exchange_correlation_reported'])
        self.assertNotIn('PBE',p['calculation']['exchange_correlation_reported'])
        for key in ('physical_temperature_K','pressure_GPa','magnetic_state','spin_polarization'):
            self.assertIsNone(p['state_fields'][key])
        self.assertEqual(p['numerical_controls']['strength_peak_convergence_reported_GPa'],.08)
        self.assertIsNone(p['numerical_controls']['statistical_uncertainty'])

    def test_previous_scientific_records_and_runtime_outputs_are_exact(self):
        baseline=load_json(ROOT/'tests/fixtures/pre_prediction_baseline.json')
        digest=lambda v:sha256(canonical_json(v).encode()).hexdigest()
        for kind, expected in baseline['records'].items():
            current={r['id']:r for r in read_catalog(kind)['records']}
            for rid,contract in expected.items():
                stable=historical_record(kind, current[rid])
                for field,expected_items in contract['additive_item_sha256'].items():
                    if field=='verification.gaps':items=stable['verification'].pop('gaps')
                    else:items=stable.pop(field)
                    actual=[digest(item) for item in items]
                    for expected_item in expected_items:self.assertIn(expected_item,actual,rid+' '+field)
                self.assertEqual(digest(stable),contract['stable_sha256'],rid)
        for filename,hash_ in baseline['composite_outputs'].items():
            result=evaluate(load_json(ROOT/'examples'/filename));result.pop('engine_version')
            self.assertEqual(digest(result),hash_,filename)
        for filename,hash_ in baseline['temperature_outputs'].items():
            result=evaluate_temperature(load_json(ROOT/'examples/temperature'/filename))
            self.assertEqual(result.pop('id'),digest(result)[:20])
            result.pop('engine_version')
            self.assertEqual(digest(historical_temperature_result(result)),hash_,filename)
        original=read_catalog
        def no_predictions(name):
            if name=='computational_predictions':raise AssertionError('legacy evaluation touched predictions')
            return original(name)
        with patch('materials_boundaries.catalog.read_catalog',side_effect=no_predictions),patch('materials_boundaries.temperature.read_catalog',side_effect=no_predictions):
            self.assertEqual(len(evaluate(example())['evaluations']),8)
            evaluate_temperature(load_json(ROOT/'examples/temperature/synthetic-linear-50k.json'))

    def test_runtime_contract_mutations_fail_closed(self):
        original=read_catalog('computational_predictions')
        r=lambda c:c['records'][0];p=lambda c:c['protocols'][0];g=lambda c:c['comparison_groups'][0]
        mutations=[lambda c:r(c).update(value_GPa=5.14),lambda c:r(c).update(source_value_string='5.130'),
            lambda c:r(c).update(value_GPa=10**1000),lambda c:r(c).update(value_GPa=True),lambda c:r(c).update(value_GPa=float('nan')),
            lambda c:r(c).update(uncertainty_GPa=.08),lambda c:r(c).update(universal_upper_bound=True),
            lambda c:r(c).update(commercial_alloy_grade=True),lambda c:r(c).update(evidence_type='experiment'),
            lambda c:r(c).update(unit='MPa'),lambda c:r(c).update(protocol_id='missing'),
            lambda c:r(c).update(comparison_group_id='missing'),lambda c:r(c).update(source_id='missing'),
            lambda c:r(c)['names'].pop('ja'),lambda c:r(c)['stoichiometry_in_model_cell'].update(Ni=11),
            lambda c:r(c).update(formula='Al'),lambda c:p(c)['geometry'].update(slip_direction_indices=[1,-1,2]),
            lambda c:p(c)['calculation'].update(exchange_correlation_reported='PBE'),
            lambda c:p(c)['state_fields'].update(physical_temperature_K=0),
            lambda c:p(c)['state_fields'].update(pressure_GPa=0),lambda c:p(c)['state_fields'].update(magnetic_state='ferromagnetic'),
            lambda c:p(c)['verification'].update(raw_inputs_audited=True),
            lambda c:p(c)['unknown_field_reasons'].update(temperature=''),lambda c:g(c).update(unknown_conditions_equivalent=True),
            lambda c:g(c).update(record_ids=[r(c)['id'],r(c)['id']]),lambda c:g(c).update(record_ids=['missing']),
            lambda c:g(c).update(verification_level='input_level'),lambda c:g(c)['record_ids'].pop(),
            lambda c:c['protocols'].append(copy.deepcopy(p(c))),lambda c:c['records'].append(copy.deepcopy(r(c))),
            lambda c:c['comparison_groups'].append(copy.deepcopy(g(c))),lambda c:p(c).update(extra=True)]
        for i,mutate in enumerate(mutations):
            with self.subTest(i=i):
                candidate=copy.deepcopy(original);mutate(candidate)
                with self.assertRaises(PredictionError):validate_prediction_catalog(candidate)

    def test_source_specific_groups_reject_cross_source_or_protocol_membership(self):
        c=contribution_catalogs();r=next(r for r in c['computational_predictions']['records'] if r['id']=='synthetic_prediction_record')
        r['protocol_id']=FIXTURE['protocol_id']
        with self.assertRaises(PredictionError):validate_prediction_catalog(c['computational_predictions'],c['sources'])

    def test_developer_checks_schema_sources_namespace_and_required_notices(self):
        c=load_catalogs(ROOT/'materials_boundaries/data')
        mutations=[lambda c:c['computational_predictions']['records'][0].update(extra=1),
                   lambda c:c['computational_predictions']['protocols'][0].update(id='voigt_bulk'),
                   lambda c:c['computational_predictions']['records'][0]['evidence'][0].update(url='invalid URL'),
                   lambda c:c['prediction_locales']['languages'].pop('ja')]
        for mutate in mutations:
            candidate=copy.deepcopy(c);mutate(candidate)
            with self.assertRaises(CatalogValidationError):validate_catalogs(candidate)
        for t in c['prediction_locales']['languages'].values():t.pop('unknown_notice')
        with self.assertRaises(CatalogValidationError):validate_catalogs(c)

    def test_appendability_across_all_new_paths_without_new_real_science(self):
        c=contribution_catalogs();before=copy.deepcopy(c);validate_catalogs(c);self.assertEqual(c,before)
        read=lambda name:copy.deepcopy(c[name])
        with patch('materials_boundaries.predictions.read_catalog',side_effect=read),patch('materials_boundaries.prediction_visualization.read_catalog',side_effect=read):
            result=query_catalog('predictions',record_id='synthetic_prediction_record')
            self.assertEqual(len(result['records']),1)
            for lang in ('en','zh','ja','de'):
                self.assertIn('SYNTHETIC TEST '+lang,render_catalog(result,'predictions',lang))
                self.assertEqual(query_catalog('predictions',query='SYNTHETIC TEST '+lang)['records'],result['records'])
            new=build_prediction_comparison('synthetic_prediction_group')
            self.assertEqual(len(new['points']),1)
            expected_group=next(g for g in c['computational_predictions']['comparison_groups'] if g['id']==DEFAULT_GROUP)
            self.assertEqual([p['record_id'] for p in build_prediction_comparison()['points']],expected_group['record_ids'])
            self.assertIn('example.invalid/value',render_prediction_html(new))
            self.assertIn('synthetic_prediction_record',comparison_csv(new))
        self.assertEqual(len(evaluate(example())['evaluations']),8)

    def test_appended_source_locators_precision_and_evidence_order_are_live(self):
        c=contribution_catalogs();r=next(r for r in c['computational_predictions']['records'] if r['id']=='synthetic_prediction_record')
        p=next(p for p in c['computational_predictions']['protocols'] if p['id']=='synthetic_prediction_protocol')
        r.update(source_value_string='5.130',reported_decimal_places=3,source_table='Table 9',source_pdf_page_1_based=99)
        r['evidence'][0]['locator']='Table 9, PDF page 99; source cell Ni, pure'
        r['evidence'].insert(0,{'source_id':r['source_id'],'locator':'Auxiliary model setup',
            'url':'https://example.invalid/setup','supports':['model_setup']})
        p['evidence'][0]['locator']='Method section 8, PDF page 88'
        p['evidence'].reverse()
        validate_catalogs(c)
        read=lambda name:copy.deepcopy(c[name])
        with patch('materials_boundaries.predictions.read_catalog',side_effect=read),patch('materials_boundaries.prediction_visualization.read_catalog',side_effect=read):
            b=build_prediction_comparison('synthetic_prediction_group')
            for lang in ('en','zh','ja','de'):
                text=render_catalog(query_catalog('predictions',record_id=r['id']),'predictions',lang)
                html=render_prediction_html(b,lang=lang)
                for output in (text,html):
                    self.assertIn('Table 9, PDF page 99',output)
                    self.assertIn('Method section 8, PDF page 88',output)
                    self.assertIn('5.130',output)
                self.assertIn('<td>Ni12</td>',html)
            row=list(csv.DictReader(io.StringIO(comparison_csv(b))))[0]
            self.assertEqual(row['value_source_url'],'https://example.invalid/value')
            self.assertEqual(row['table_locator'],'Table 9, PDF page 99; source cell Ni, pure')
        bad=copy.deepcopy(c['computational_predictions'])
        target=next(x for x in bad['records'] if x['id']==r['id'])
        target['evidence']=[target['evidence'][0]]
        with self.assertRaises(PredictionError):validate_prediction_catalog(bad,c['sources'])

    def test_queries_four_language_aliases_and_original_metadata(self):
        expected=read_catalog('computational_predictions')
        self.assertEqual(query_catalog('predictions'),expected)
        for lang in ('en','zh','ja','de'):
            for r in expected['records']:
                match=query_catalog('predictions',record_id=r['id'],query=r['names'][lang])
                self.assertEqual(match['records'],[r])
                self.assertEqual(match['comparison_groups'],expected['comparison_groups'])
                text=render_catalog(match,'predictions',lang)
                self.assertIn(r['source_value_string'],text);self.assertIn(prediction_labels(lang)['unknown_notice'],text)
                self.assertNotIn('[missing:',text)
        self.assertEqual(query_catalog('predictions',query='no-such-term')['records'],[])
        self.assertEqual(query_catalog('predictions',quantity='wrong')['records'],[])
        self.assertEqual(query_catalog('predictions',source_id='missing')['records'],[])
        with self.assertRaises(CatalogLookupError):query_catalog('predictions',record_id='missing')
        with self.assertRaises(ValueError):query_catalog('predictions',direction='prediction')


class PredictionVisualizationTests(unittest.TestCase):
    def setUp(self):self.bundle=build_prediction_comparison()

    def test_determinism_and_source_digits_in_csv_with_caveats(self):
        self.assertEqual(self.bundle,build_prediction_comparison())
        rows=list(csv.DictReader(io.StringIO(comparison_csv(self.bundle))))
        by_id={r['record_id']:r for r in rows}
        for expected in FIXTURE['records']:self.assertEqual(by_id[expected['id']]['source_value_string'],expected['source_value_string'])
        for r in rows:
            self.assertEqual(r['classification'],'published_computational_prediction')
            self.assertEqual(r['physical_temperature_K'],'not_verified')
            self.assertEqual(r['pressure_GPa'],'not_verified')
            self.assertEqual(r['magnetic_state'],'not_verified')
            self.assertEqual(r['uncertainty_GPa'],'not_established')
            self.assertEqual(r['convergence_is_uncertainty'],'false')
            self.assertIn('reported_method_only',r['comparison_scope'])
            self.assertIn('12-atom',r['finite_cell_caveat'])

    def test_tampered_snapshot_numbers_geometry_classification_and_flags_fail(self):
        changes=[lambda b:b['points'][0].update(value_GPa=9),lambda b:b['points'][0].update(source_value_string='5.130'),
                 lambda b:b['protocol_snapshot']['geometry'].update(slip_direction_indices=[1,-1,2]),
                 lambda b:b['source_snapshots'][0].update(title='forged'),lambda b:b.update(uncertainty_bars=.08),
                 lambda b:b.update(interpolation=True),lambda b:b.update(classification='bound'),
                 lambda b:b['record_snapshots'].pop(),lambda b:b.update(unknown_conditions_equivalent=True),
                 lambda b:b.update(extra=1),lambda b:b.update(engine_version='old')]
        for change in changes:
            candidate=copy.deepcopy(self.bundle);change(candidate)
            for fn in (validate_prediction_comparison,comparison_json,comparison_csv,render_prediction_html,render_prediction_svg):
                with self.assertRaises(PredictionError):fn(candidate)

    def test_static_structure_all_languages_and_narrow_layouts(self):
        for lang in ('en','zh','ja','de'):
            self.assertEqual(set(prediction_labels(lang)),set(prediction_labels('en')))
            for width in (360,380,1100,1600):
                svg=render_prediction_svg(self.bundle,lang=lang,width=width);root=ET.fromstring(svg);ns={'s':'http://www.w3.org/2000/svg'}
                self.assertEqual(len(root.findall('.//s:circle',ns)),len(self.bundle['points']))
                for tag in ('polyline','polygon','path'):self.assertEqual(len(root.findall('.//s:'+tag,ns)),0)
                self.assertIn('5.13',svg);self.assertIn('4.58',svg);self.assertIn('5.46',svg)
                self.assertIn(prediction_labels(lang)['unknown_notice'],svg) # full accessible desc
                self.assertIn(prediction_labels(lang)['comparison_notice'],svg)
                self.assertIn('[1,1,-2]',svg)
            html=render_prediction_html(self.bundle,lang=lang)
            self.assertNotIn('<script',html);self.assertNotIn('[missing:',html)
            self.assertIn('#page=27',html);self.assertIn('#page=5',html)
            self.assertIn('@media',html);self.assertIn('<table>',html)
        for width in (True,359,1601,'380'):
            with self.assertRaises(PredictionError):render_prediction_svg(self.bundle,width=width)

    def test_extreme_valid_source_values_fail_plotting_with_structured_range_error(self):
        c=contribution_catalogs();r=next(r for r in c['computational_predictions']['records'] if r['id']=='synthetic_prediction_record')
        r.update(value_GPa=1.6e308,source_value_string=format(1.6e308,'.2f'))
        # Decimal text represents the displayed float exactly in decimal notation.
        from decimal import Decimal
        r['source_value_string']=format(Decimal(str(r['value_GPa'])),'.2f')
        validate_catalogs(c)
        read=lambda name:copy.deepcopy(c[name])
        with patch('materials_boundaries.predictions.read_catalog',side_effect=read),patch('materials_boundaries.prediction_visualization.read_catalog',side_effect=read):
            b=build_prediction_comparison('synthetic_prediction_group')
            with self.assertRaisesRegex(PredictionError,'plotting numeric range'):render_prediction_svg(b)

    def test_comparison_and_catalog_public_schemas(self):
        from jsonschema import Draft202012Validator,FormatChecker
        from referencing import Registry,Resource
        names=('computational_predictions','sources','prediction_comparison')
        schemas=[load_json(ROOT/f'schemas/{n}.schema.json') for n in names]
        registry=Registry().with_resources((s['$id'],Resource.from_contents(s)) for s in schemas)
        for s in schemas:Draft202012Validator.check_schema(s)
        Draft202012Validator(schemas[0],registry=registry,format_checker=FormatChecker()).validate(read_catalog(names[0]))
        Draft202012Validator(schemas[2],registry=registry,format_checker=FormatChecker()).validate(self.bundle)

    def test_cli_exact_errors_export_integrity_and_language_stability(self):
        def run(*args):return subprocess.run([sys.executable,'-m','materials_boundaries',*args],cwd=ROOT,text=True,capture_output=True)
        outputs=[]
        for lang in ('en','zh','ja','de'):
            r=run('catalog','predictions','--json','--lang',lang);self.assertEqual(r.returncode,0,r.stderr);outputs.append(r.stdout)
            r=run('--lang',lang,'prediction','plot','--help');self.assertEqual(r.returncode,0);self.assertIn(prediction_labels(lang)['output'],r.stdout)
        self.assertEqual(len(set(outputs)),1)
        for args in (('catalog','predictions','--id','missing'),('catalog','predictions','--direction','prediction')):
            self.assertEqual(run(*args).returncode,2)
        with tempfile.TemporaryDirectory() as tmp:
            r=run('prediction','plot','--output',tmp,'--lang','ja');self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(len(list(Path(tmp).iterdir())),5)
            validate_prediction_comparison(load_json(Path(tmp)/'prediction-comparison.json'))
            missing=Path(tmp)/'should-not-exist'
            r=run('prediction','plot','--output',str(missing),'--group-id','missing');self.assertEqual(r.returncode,2);self.assertFalse(missing.exists())


if __name__=='__main__':unittest.main()
