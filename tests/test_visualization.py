import copy
from decimal import localcontext
import json
from pathlib import Path
import re
import runpy
import unittest
import xml.etree.ElementTree as ET

from materials_boundaries import evaluate, load_json
from materials_boundaries.visualization import (VisualizationError, _runs, build_comparison,
    comparison_json, compatibility_gate, convert_value, render_html, render_svg, validate_comparison)

ROOT = Path(__file__).resolve().parents[1]

def fixture(name='synthetic-two-phase'):
    return load_json(ROOT / 'examples' / (name + '.json'))

def bundle(**kwargs):
    return build_comparison([fixture()], fractions=[0, 0.5, 1], **kwargs)

class VisualizationTests(unittest.TestCase):
    def test_canonical_values_every_point_and_quantity(self):
        data = bundle()
        for sample in data['cases'][0]['samples']:
            instance = fixture()
            for phase, fraction in zip(instance['phases'], sample['fractions']):
                phase['volume_fraction'] = fraction
            self.assertEqual(sample['evaluation'], evaluate(instance))
        midpoint = {s['claim_id']: s['points'][1] for s in data['series']}
        self.assertEqual(midpoint['hs_bulk_3d_two_phase']['lower'], 16.25)
        self.assertEqual(midpoint['hs_bulk_3d_two_phase']['upper'], 17.5)
        self.assertEqual(len(data['series']), 8)
        self.assertNotIn('model_estimate', [s['semantics'] for s in data['series']])

    def test_deterministic_and_nonmutating(self):
        original = fixture(); before = copy.deepcopy(original)
        data = build_comparison([original])
        self.assertEqual(original, before)
        self.assertEqual(comparison_json(data), comparison_json(build_comparison([original])))
        with localcontext() as ctx:
            ctx.prec = 5
            self.assertEqual(data, build_comparison([original]))
        self.assertEqual(data['cases'][0]['input']['phases'][1]['volume_fraction'], .5)

    def test_stable_case_and_series_ids_when_reordered(self):
        inputs = [fixture(), fixture('literature-epoxy-glass-model')]
        a = build_comparison(inputs, fractions=[0,1]); b = build_comparison(inputs[::-1], fractions=[0,1])
        ids=lambda b: {(s['case_id'],s['claim_id']):s['id'] for s in b['series']}
        self.assertEqual(ids(a), ids(b))

    def test_sources_versions_checks_and_input_provenance(self):
        data = build_comparison([fixture('literature-epoxy-glass-model')], fractions=[0,.2,1])
        case = data['cases'][0]
        self.assertEqual(case['input_provenance']['kind'],'literature_model')
        self.assertIn('temperature_k',case['unknown_context'])
        self.assertIn('genin_birman_2009',{s['id'] for s in data['catalogs']['sources']['records']})
        self.assertEqual(len(data['catalogs']['claims']['records']),8)
        for series in data['series']:
            self.assertTrue(series['claim_version']); self.assertTrue(series['source_ids'])
        for point in case['samples']:
            self.assertTrue(point['evaluation']['evaluations'][0]['checks'])

    def test_unit_conversions_and_dimensionless_poisson(self):
        self.assertEqual(convert_value(1,'GPa','MPa','effective_bulk_modulus'),1000)
        self.assertEqual(convert_value(-.1,'1','1','effective_poissons_ratio'),-.1)
        self.assertIsNone(convert_value(None,'Pa','GPa','effective_shear_modulus'))
        for args in [(1,'1','Pa','effective_bulk_modulus'),(1,'GPa','1','effective_poissons_ratio'),(1,'psi','Pa','effective_shear_modulus')]:
            with self.assertRaises(VisualizationError): convert_value(*args)
        a, b = bundle(),bundle(output_unit='MPa')
        self.assertEqual(a['series'][-1]['points'],b['series'][-1]['points'])
        self.assertEqual(b['series'][0]['points'][1]['lower'],16250)

    def test_unknown_context_never_becomes_equal(self):
        a = bundle()['cases'][0]; b=copy.deepcopy(a);b['id']='second'
        result = compatibility_gate(a,b)
        self.assertEqual(result['status'],'unknown'); self.assertFalse(result['overlay_allowed'])
        self.assertEqual(next(x for x in result['checks'] if x['condition_id']=='context.temperature_k')['state'],'unknown')

    def test_gate_blocks_axis_conditions_quantity_and_unit_mismatch(self):
        a=bundle()['cases'][0]
        for change in ['axis','conditions','quantity','unit','temperature']:
            b=copy.deepcopy(a)
            if change=='axis':b['axis']['phase_id']='another'
            elif change=='conditions':b['conditions']['loading']='dynamic'
            elif change=='quantity':b['quantity_dimensions']['effective_bulk_modulus']='dimensionless'
            elif change=='unit':b['units']['effective_bulk_modulus']='psi'
            else:a['context']['temperature_k']=300;b['context']['temperature_k']=350
            self.assertEqual(compatibility_gate(a,b)['status'],'incompatible')

    def test_unit_equivalent_phase_definition(self):
        a=fixture(); b=fixture(); b['id']='converted'
        for phase in b['phases']:
            for key in ['bulk_modulus','shear_modulus']:
                phase[key]['value']*=1000;phase[key]['unit']='MPa'
        data=build_comparison([a,b],fractions=[0,1])
        checks=data['compatibility'][0]['checks']
        self.assertEqual(next(c for c in checks if c['condition_id']=='phase_definition')['state'],'satisfied')

    def test_violated_points_are_gaps_but_pure_endpoints_remain(self):
        data=fixture();data['phases'][1]['shear_modulus']['value']=1
        result=build_comparison([data],fractions=[0,.5,1])
        hs=result['series'][0]
        self.assertIsNone(hs['points'][1]['lower'])
        self.assertEqual([len(r) for r in _runs(hs['points'],('lower','upper'))],[1,1])
        svg=render_svg(result,data['id'])
        # Each interval endpoint remains a one-point run, never an endpoint-to-endpoint path.
        root=ET.fromstring(svg); group=root.find('.//{*}g')
        self.assertEqual(len(group.findall('{*}polyline')),4)
        self.assertTrue(all(len(p.attrib['points'].split())==1 for p in group.findall('{*}polyline')))

    def test_conditions_enforced_at_pure_endpoints(self):
        data=fixture();data['conditions']['effective_symmetry']=None
        result=build_comparison([data],fractions=[0,.5,1])
        self.assertTrue(all(p['lower'] is None for s in result['series'] for p in s['points']))
        self.assertIn('No applicable values',render_svg(result,data['id']))

    def test_tampered_or_stale_bundles_fail_closed(self):
        for target in ['value','claim','condition','version','metadata']:
            b=bundle()
            if target=='value':b['series'][0]['points'][1]['lower']=999
            elif target=='claim':b['catalogs']['claims']['records'][0]['version']='fake'
            elif target=='condition':b['cases'][0]['conditions']['loading']='dynamic'
            elif target=='version':b['engine_version']='0.0.0'
            else:b['policy']['sample_semantics']='measured'
            with self.assertRaises(VisualizationError):render_html(b)

    def test_extreme_finite_outputs_do_not_make_invalid_svg(self):
        for scale in [1.7e308,1e-290]:
            data=fixture()
            for phase in data['phases']:
                phase['bulk_modulus']={'value':scale,'unit':'Pa'}
                phase['shear_modulus']={'value':scale/2,'unit':'Pa'}
            b=build_comparison([data],fractions=[0,.5,1],output_unit='Pa')
            svg=render_svg(b,data['id'])
            self.assertNotRegex(svg,r'(?i)(?:="|,)(?:nan|inf|-inf)')
            root=ET.fromstring(svg)
            # A tiny constant modulus remains at a readable relative scale.
            point=root.find('.//{*}circle')
            self.assertTrue(42 < float(point.attrib['cy']) < 270)

    def test_numerical_errors_preserved_as_null_gaps(self):
        data=fixture()
        for phase in data['phases']:
            phase['bulk_modulus']={'value':1e308,'unit':'GPa'}
        b=build_comparison([data],fractions=[0,.5,1],output_unit='Pa')
        self.assertTrue(all(p['lower'] is None for p in b['series'][0]['points']))
        self.assertEqual(b['series'][0]['points'][0]['computation'],'numerical_range_error')

    def test_html_escapes_untrusted_labels_and_embedded_data(self):
        payload='</script><script>alert(1)</script><img src=x onerror=alert(1)>'
        data=fixture();data['provenance']['note']=payload
        b=build_comparison([data],fractions=[0,1],labels={data['id']:payload})
        html=render_html(b)
        self.assertNotIn(payload,html);self.assertNotIn('<img src=x',html)
        self.assertIn('&lt;script&gt;',html)
        encoded=re.search(r'<script type="application/json" id="comparison-bundle">(.*?)</script>',html,re.S)[1]
        self.assertEqual(json.loads(encoded),b)
        self.assertEqual(len(re.findall(r'<script\b',html)),1)
        self.assertIn("default-src 'none'",html)

    def test_locales_identical_numeric_payload_and_standalone_svg(self):
        b=bundle(); ids={s['id'] for s in b['series']}
        for lang in ['en','zh','ja','de']:
            html=render_html(b,lang=lang); svg=render_svg(b,b['cases'][0]['id'],lang=lang,width=340)
            self.assertIn(f'lang="{lang}"',html);ET.fromstring(svg)
            embedded=re.search(r'<script type="application/json" id="comparison-bundle">(.*?)</script>',html,re.S)[1]
            self.assertEqual(json.loads(embedded),b)
        with self.assertRaises(VisualizationError):render_html(b,lang='xx')

    def test_optional_reuss_voigt_view_only(self):
        b=bundle();case=b['cases'][0]['id']
        svg=render_svg(b,case,include_classical=False)
        self.assertNotIn('stroke-dasharray',svg)
        self.assertEqual(len(b['series']),8)

    def test_invalid_sweeps_and_duplicate_cases_rejected(self):
        for fractions in [[0],[0,0],[1,0],[0,float('nan')],[0,True],[-.1,1],[0,1.1]]:
            with self.assertRaises(VisualizationError):build_comparison([fixture()],fractions=fractions)
        with self.assertRaises(VisualizationError):build_comparison([fixture(),fixture()])
        with self.assertRaises(VisualizationError):build_comparison([fixture()],labels={'bad':'test'})

    def test_demo_preview_rejects_misleading_case_labels(self):
        helper=runpy.run_path(str(ROOT/'scripts/render_visualization_preview.py'))['compose']
        demo=build_comparison([fixture(),fixture('literature-epoxy-glass-model')],fractions=[0,1])
        self.assertIn('Literature epoxy/glass model',helper(demo,narrow=False))
        custom=fixture();custom['id']='custom-measured';custom['provenance']['kind']='measured'
        with self.assertRaises(ValueError):
            helper(build_comparison([custom],fractions=[0,1]),narrow=False)

    def test_exported_schema_accepts_bundle_rejects_extra(self):
        try:from jsonschema import Draft202012Validator
        except ImportError:self.skipTest('optional jsonschema dev dependency not installed')
        schema=load_json(ROOT/'schemas/comparison.schema.json')
        for name in ['instance','evaluation','claims','sources']:
            self.assertEqual(schema['$defs'][name],load_json(ROOT/'schemas'/(name+'.schema.json')))
        Draft202012Validator.check_schema(schema)
        check=Draft202012Validator(schema);check.validate(bundle())
        bad=bundle();bad['unknown_field']=1
        self.assertTrue(list(check.iter_errors(bad)))

if __name__=='__main__':unittest.main()
