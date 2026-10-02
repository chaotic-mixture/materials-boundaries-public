"""Data-driven four-language labels, source scope and general branch layouts."""
import copy
from contextlib import contextmanager, ExitStack
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from materials_boundaries.temperature import TemperatureError, evaluate_temperature, render_prediction
from materials_boundaries.temperature_presentation import (
    ALIASES, TEMPLATES, labels, presentation_for, validate_temperature_locales,
)
from materials_boundaries.temperature_visualization import (
    build_temperature_comparison, render_temperature_svg, render_temperature_html,
    comparison_csv, _case_layout,
)
from scripts.validate_catalogs import load_catalogs, validate_catalogs, CatalogValidationError

ROOT = Path(__file__).resolve().parents[1]
LINEAR = 'synthetic_linear_temperature'
OVERLAP = 'synthetic_overlap_temperature'
QUADRATIC = 'synthetic_quadratic_temperature'
QUARTIC = 'synthetic_quartic_temperature'
INTERVAL = 'synthetic_interval_temperature'
LANGS = ('en', 'zh', 'ja', 'de')
NS = {'s': 'http://www.w3.org/2000/svg'}


@contextmanager
def candidate_catalogs(catalogs):
    with ExitStack() as stack:
        for module in ('materials_boundaries.catalog', 'materials_boundaries.temperature',
                       'materials_boundaries.temperature_visualization'):
            stack.enter_context(patch(module+'.read_catalog', side_effect=lambda name: copy.deepcopy(catalogs[name])))
        stack.enter_context(patch('materials_boundaries.temperature_presentation.read_locales',
                                 side_effect=lambda: copy.deepcopy(catalogs['temperature_locales'])))
        yield


def synthetic(catalogs, *, localized=False, intervals=((2, 10), (20, 30))):
    model = copy.deepcopy(catalogs['temperature_models']['records'][0])
    model['id'] = 'synthetic_general_temperature'
    model['name'] = 'SYNTHETIC layout fixture'
    model['material']['name'] = 'SYNTHETIC <material> & label'
    original = model['branches'][0]
    model['branches'] = []
    for i, interval in enumerate(intervals):
        branch = copy.deepcopy(original)
        branch.update(id=f'synthetic_branch_{i}', coefficients_text=[str(90+i), '0.01', '0', '0', '0'],
                      equation_range_K=list(interval), source_data_range_K=None)
        model['branches'].append(branch)
    catalogs['temperature_models']['records'].append(model)
    if localized:
        entry = copy.deepcopy(catalogs['temperature_locales']['model_presentation'][LINEAR])
        entry['material_snapshot'] = copy.deepcopy(model['material'])
        entry['names'] = {lang: f'SYNTHETIC {lang} <material> & label' for lang in LANGS}
        catalogs['temperature_locales']['model_presentation'][model['id']] = entry
    return model


class TemperaturePresentationTests(unittest.TestCase):
    def setUp(self):
        self.catalogs = load_catalogs(ROOT/'materials_boundaries/data')

    def test_synthetic_condition_mapping_and_generalized_labels_remain(self):
        metadata=self.catalogs['temperature_locales']['model_presentation']
        for mid in (LINEAR,OVERLAP,QUADRATIC,QUARTIC,INTERVAL):
            self.assertEqual((metadata[mid]['temper_evidence'],metadata[mid]['temper_source_id']),
                             ('synthetic_demo',None))
            self.assertEqual(metadata[mid]['rights_review'],'project_authored_synthetic')
        for lang in LANGS:
            active=labels(lang)
            for old,replacement in ALIASES.items():
                self.assertEqual(active[old],self.catalogs['temperature_locales']['languages'][lang][replacement])
            self.assertNotIn('50',active['overlap_notice'])
            self.assertNotIn('100',active['endpoint_notice'])
            self.assertNotIn('1%',active['fit_notice'])
            self.assertTrue(active['condition_synthetic'])
            self.assertTrue(active['rights_synthetic'])

    def test_lookup_mutations_fail_runtime_and_development(self):
        changes = [lambda e: e.update(extra=1), lambda e: e.pop('names'),
                   lambda e: e['names'].pop('ja'), lambda e: e['names'].update(de=' '),
                   lambda e: e['material_snapshot'].update(temper='T651'),
                   lambda e: e['material_snapshot'].update(extra=1),
                   lambda e: e.update(temper_evidence='specimen_verified'),
                   lambda e: e.update(temper_evidence='not_specified'),
                   lambda e: e.update(temper_source_id='materials_boundaries_synthetic_temperature_demo'),
                   lambda e: e.update(temper_source_id='missing_source'),
                   lambda e: e.update(primary_source_id='not_a_source'),
                   lambda e: e.update(reuse_status_snapshot='public domain'),
                   lambda e: e.update(rights_review='cleared')]
        for change in changes:
            c = copy.deepcopy(self.catalogs)
            change(c['temperature_locales']['model_presentation'][LINEAR])
            with self.subTest(change=change), self.assertRaises(TemperatureError):
                validate_temperature_locales(c['temperature_locales'], c['temperature_models'], c['sources'])
            with self.assertRaises(CatalogValidationError):
                validate_catalogs(c)

    def test_missing_lookup_is_supported_but_malformed_envelopes_fail(self):
        c = copy.deepcopy(self.catalogs)
        c['temperature_locales'].pop('model_presentation')
        validate_catalogs(c)
        for mutation in (lambda x: x.update(extra=True), lambda x: x.update(model_presentation=[]),
                         lambda x: x.update(translation_review='reviewed')):
            x = copy.deepcopy(self.catalogs['temperature_locales']); mutation(x)
            with self.assertRaises(TemperatureError): validate_temperature_locales(x)

    def test_malformed_english_map_fails_even_when_ordered_last(self):
        for bad in (None, False, [], 'bad'):
            c = copy.deepcopy(self.catalogs)
            c['temperature_locales']['languages']['en'] = bad
            c['temperature_locales']['languages'] = {key:c['temperature_locales']['languages'][key] for key in ('zh','ja','de','en')}
            with self.assertRaises(TemperatureError): validate_temperature_locales(c['temperature_locales'])
            with self.assertRaises(CatalogValidationError): validate_catalogs(c)

    def test_format_placeholders_fail_closed_in_every_language(self):
        for lang in LANGS:
            for value in ('bad {source}', 'bad {temperature.real}', 'bad {temperature!r}',
                          'bad {temperature:20}', 'bad {temperature', 'bad {}', 'no placeholder'):
                c = copy.deepcopy(self.catalogs)
                c['temperature_locales']['languages'][lang]['overlap_at'] = value
                with self.subTest(lang=lang, value=value), self.assertRaises(TemperatureError):
                    validate_temperature_locales(c['temperature_locales'])
                with self.assertRaises(CatalogValidationError): validate_catalogs(c)

    def test_unspecified_condition_has_no_format_placeholders(self):
        c = copy.deepcopy(self.catalogs)
        c['temperature_locales']['languages']['en']['condition_unspecified'] = '{unknown}'
        with self.assertRaises(TemperatureError): validate_temperature_locales(c['temperature_locales'])
        with self.assertRaises(CatalogValidationError): validate_catalogs(c)

    def test_appendability_localized_and_fallback_keep_synthetic_status_and_escape_text(self):
        for localized in (False,True):
            c=copy.deepcopy(self.catalogs);model=synthetic(c,localized=localized)
            validate_catalogs(c)
            with candidate_catalogs(c):
                bundle=build_temperature_comparison([model['id']],points_per_branch=3)
                for lang in LANGS:
                    shown=presentation_for(model,bundle['cases'][0]['source_snapshots'],lang)
                    self.assertEqual(shown['condition'],labels(lang)['condition_synthetic'])
                    self.assertEqual(shown['rights'],labels(lang)['rights_synthetic'])
                    self.assertEqual(shown['name'],f'SYNTHETIC {lang} <material> & label' if localized else model['material']['name'])
                    svg=render_temperature_svg(bundle,lang=lang,width=360)
                    html=render_temperature_html(bundle,lang=lang)
                    self.assertIn('&lt;material&gt;',svg);self.assertIn('&lt;material&gt;',html)
                    self.assertNotIn('<material>',html)
                    self.assertNotIn('None%',svg);self.assertNotIn('0%',' '.join(ET.fromstring(svg).itertext()))
                    self.assertIn(labels(lang)['data_not_applicable'],html)
                    text=render_prediction(evaluate_temperature({'schema_version':'1.0.0','model_id':model['id'],
                        'temperature':{'value':5,'unit':'K'}}),lang)
                    self.assertIn(labels(lang)['branch_synthetic'].format(branch='synthetic_branch_0'),text)
                    self.assertNotIn('None%',text)

    def test_five_synthetic_facets_four_languages_and_point_and_interval_overlaps(self):
        mids=[LINEAR,OVERLAP,QUADRATIC,QUARTIC,INTERVAL]
        bundle=build_temperature_comparison(mids,points_per_branch=3)
        for lang in LANGS:
            for width in (360,380,800,1100,1600):
                svg=render_temperature_svg(bundle,lang=lang,width=width)
                root=ET.fromstring(svg)
                self.assertEqual(len(root.findall('.//s:polyline',NS)),7)
                self.assertEqual(len(root.findall('.//s:circle',NS)),14)
                self.assertFalse(root.findall('.//s:polygon',NS))
                groups={g.attrib['data-model-id']:g for g in root.findall('s:g',NS)}
                for mid in mids:
                    group=ET.tostring(groups[mid],encoding='unicode')
                    visible=' '.join(groups[mid].itertext())
                    self.assertIn(self.catalogs['temperature_locales']['model_presentation'][mid]['primary_source_id'],''.join(''.join(groups[mid].itertext()).split()))
                    self.assertNotIn('None%',visible)
                point=ET.tostring(groups[OVERLAP],encoding='unicode')
                self.assertIn('25.000000',point);self.assertIn('32.500000',point)
                interval=ET.tostring(groups[INTERVAL],encoding='unicode')
                for number in ('53.000000','58.500000','54.000000','58.000000'):
                    self.assertIn(number,interval)
                self.assertNotIn('synthetic_overlap_20_50',ET.tostring(groups[QUADRATIC],encoding='unicode'))
        rows=comparison_csv(bundle)
        self.assertIn('50,25.0',rows);self.assertIn('50,32.5',rows)
        self.assertIn('synthetic_demo',rows);self.assertNotIn('empirical_fit_prediction',rows)

    def test_general_overlaps_gaps_identical_nested_unsorted_and_triple(self):
        intervals = ((40,50), (2,10), (8,20), (9,11), (25,30), (25,30), (45,48))
        c = copy.deepcopy(self.catalogs); model = synthetic(c, intervals=intervals)
        with candidate_catalogs(c):
            bundle = build_temperature_comparison([model['id']], points_per_branch=3)
            case = bundle['cases'][0]
            self.assertEqual([row['temperature_K'] for row in case['overlaps']], [8,9,10,11,25,30,45,48])
            for value, expected in ((9.5,3),(15,1),(22,0),(27,2),(46,2),(35,0)):
                result = evaluate_temperature({'schema_version':'1.0.0','model_id':model['id'],'temperature':{'value':value,'unit':'K'}})
                self.assertEqual(len(result['predictions']), expected)
                self.assertEqual(result['status'], 'ambiguous_overlap' if expected>1 else 'prediction' if expected else 'out_of_range')
            for lang in LANGS:
                svg = render_temperature_svg(bundle, lang=lang, width=360)
                root = ET.fromstring(svg)
                self.assertEqual(len(root.findall('.//s:polyline', NS)), len(intervals))
                joined = ' '.join(node.text or '' for node in root.findall('.//s:text', NS))
                for overlap in case['overlaps']:
                    # Text may wrap; every overlap/branch record is still printed.
                    self.assertIn(f'{overlap["temperature_K"]} K', joined)
                    for row in overlap['predictions']:
                        self.assertIn(f'{row["value"]:.6f}', joined)
                layout = _case_layout(case, lang, 312)
                self.assertGreater(layout['height'], 1000)
                group = root.find('s:g', NS); box = group.find('s:rect', NS)
                bottom = float(box.attrib['y'])+float(box.attrib['height'])
                self.assertTrue(all(float(node.attrib['y']) < bottom for node in group.findall('s:text', NS)))

    def test_long_wide_latin_and_cjk_names_are_conservatively_wrapped(self):
        c = copy.deepcopy(self.catalogs)
        model = synthetic(c)
        model['material']['name'] = 'W'*120 + 'M'*120 + '材'*60
        with candidate_catalogs(c):
            bundle = build_temperature_comparison([model['id']], points_per_branch=2)
            for lang in LANGS:
                for width in (360, 380, 800, 1100):
                    facet_width = width-48 if width<800 else (width-76)/2
                    layout = _case_layout(bundle['cases'][0], lang, facet_width)
                    self.assertEqual(''.join(layout['title']), model['material']['name'])
                    self.assertTrue(all(len(line)*18 < facet_width-20 for line in layout['title']))
                    ET.fromstring(render_temperature_svg(bundle, lang=lang, width=width))

    def test_twenty_branch_layout_and_reordered_catalogs(self):
        c = copy.deepcopy(self.catalogs)
        model = synthetic(c, localized=True, intervals=tuple((2+i*12,10+i*12) for i in range(20)))
        c['temperature_models']['records'].reverse(); c['sources']['records'].reverse()
        model['source_ids'].reverse()
        validate_catalogs(c)
        with candidate_catalogs(c):
            bundle = build_temperature_comparison([model['id']], points_per_branch=2)
            for lang in LANGS:
                svg = render_temperature_svg(bundle, lang=lang, width=360)
                root = ET.fromstring(svg)
                self.assertEqual(len(root.findall('.//s:polyline', NS)), 20)
                self.assertIn('synthetic_branch_19', svg)
                self.assertNotIn('None%',svg)
                self.assertIn('synthetic_demo',bundle['classification'])


if __name__ == '__main__': unittest.main()
