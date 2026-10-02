"""Offline inspection presentation tests, not a scientific reanalysis.

The public schema is a development check. Runtime admission must independently
rebuild every output against the selected current catalog snapshots.
"""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from copy import deepcopy
import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from materials_boundaries import evaluate, load_json
from materials_boundaries.catalog import read_catalog
from materials_boundaries.cli import main
from materials_boundaries.i18n import translate
from materials_boundaries import observation_visualization as view
from materials_boundaries._observation_inspection_labels import LABELS
from materials_boundaries._hbn_observation_contract import HBN_REVIEW
from materials_boundaries.visualization import build_comparison, render_html, render_svg
from test_engine import ROOT, example

IDS = (
    'lee_2008_graphene_in_plane_stiffness_2d',
    'lee_2008_graphene_breaking_strength_2d',
    'bertolazzi_2011_mos2_monolayer_in_plane_stiffness_2d',
    'bertolazzi_2011_mos2_monolayer_breaking_strength_2d',
    'falin_2017_hbn_monolayer_in_plane_stiffness_2d',
    'falin_2017_hbn_monolayer_breaking_strength_2d',
)
DISPLAYS = ('340 ± 50 N/m', '42 ± 4 N/m', '180 ± 60 N/m',
            '15 ± 3 N/m', '289 ± 24 N/m', '23.6 ± 1.8 N/m')
LANGUAGES = ('en', 'zh', 'ja', 'de')
SVG_NS = '{http://www.w3.org/2000/svg}'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def baseline_observations():
    """Explicit six-record fixture, independent of actual package ordering/growth."""
    actual = read_catalog('observations')
    index = {r['id']: r for r in actual['records']}
    return {'schema_version': actual['schema_version'],
            'records': [deepcopy(index[rid]) for rid in IDS]}


def compact(value):
    return ''.join(value.split())


def set_path(value, path, replacement):
    for part in path[:-1]:
        value = value[part]
    value[path[-1]] = replacement


@contextmanager
def catalogs(observations=None, sources=None):
    values = {'observations': deepcopy(observations or read_catalog('observations')),
              'sources': deepcopy(sources or read_catalog('sources'))}
    def reader(name):
        if name not in values:
            raise AssertionError('Unexpected catalog read: ' + name)
        return deepcopy(values[name])
    with patch.object(view, 'read_catalog', side_effect=reader) as mocked:
        yield mocked


class ParsedHTML(HTMLParser):
    """Separate visible prose from the inert embedded JSON, preserving attrs."""
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.visible = []
        self.embedded = []
        self.in_json = False
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == 'pre' and attrs.get('id') == 'inspection-json':
            self.in_json = True

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.in_json = False

    def handle_data(self, data):
        (self.embedded if self.in_json else self.visible).append(data)

    @property
    def text(self):
        return ' '.join(self.visible)


def svg_text(markup):
    return ' '.join(''.join(node.itertext()) for node in ET.fromstring(markup).iter(SVG_NS + 'text'))


def html_article(markup, record_id):
    for fragment in re.findall(r'<article\b[^>]*>.*?</article>', markup, flags=re.S):
        parsed = ParsedHTML(fragment)
        if any(tag == 'article' and attrs.get('data-record-id') == record_id for tag, attrs in parsed.tags):
            return parsed.text
    raise AssertionError('Missing article ' + record_id)


def svg_card(markup, record_id):
    for node in ET.fromstring(markup).iter(SVG_NS + 'g'):
        if node.attrib.get('data-record-id') == record_id:
            return ' '.join(''.join(t.itertext()) for t in node.iter(SVG_NS + 'text'))
    raise AssertionError('Missing card ' + record_id)


class ObservationInspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observations = baseline_observations()
        cls.sources = read_catalog('sources')
        with catalogs(cls.observations, cls.sources):
            cls.bundle = view.build_observation_inspection(list(IDS))

    def setUp(self):
        # Exercise a named fixture without freezing the live catalog size/order.
        context = catalogs(self.observations, self.sources)
        context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)

    def test_exact_six_selected_values_in_packaged_order(self):
        b = self.bundle
        self.assertEqual(b['schema_version'], '1.0.0')
        self.assertEqual(b['kind'], 'observation_inspection')
        self.assertEqual(b['selection'], dict(requested_record_ids=list(IDS), source_id=None,
                         quantity=None, resolved_record_ids=list(IDS)))
        self.assertEqual([f['normalized_display'] for f in b['facets']], list(DISPLAYS))
        self.assertEqual([f['record_id'] for f in b['facets']], list(IDS))
        for f in b['facets']:
            self.assertEqual(f['unit'], 'N/m')
            self.assertEqual(f['display_basis'],
                'catalog_reported_result_value_and_uncertainty_value_in_N_per_m_not_verbatim_source')
            self.assertNotIn('GPa', f['normalized_display'])
        self.assertNotIn('23.600', canonical(b['facets']))

    def test_complete_unchanged_snapshots_versions_and_metadata_digests(self):
        b = self.bundle
        self.assertEqual(b['record_snapshots'], self.observations['records'])
        referenced = {r['study_id'] for r in b['record_snapshots']}
        referenced.update(e['source_id'] for r in b['record_snapshots'] for e in r['evidence'])
        self.assertEqual(b['source_snapshots'], [s for s in self.sources['records'] if s['id'] in referenced])
        self.assertEqual(b['catalog_schema_versions'], {'observations':'1.2.0','sources':'1.0.0'})
        self.assertEqual(b['record_digests'], [dict(record_id=r['id'], record_version=r['version'], sha256=digest(r)) for r in b['record_snapshots']])
        self.assertEqual(b['source_digests'], [dict(source_id=s['id'], sha256=digest(s)) for s in b['source_snapshots']])
        for s in b['source_snapshots']:
            self.assertNotIn('version', s)
        self.assertIn('metadata_not_original_source_artifact_bytes', b['presentation_policy']['snapshot_digests_identify'])

    def test_primary_display_does_not_reconstruct_or_replace_source_wording(self):
        records = self.bundle['record_snapshots']
        for r in records[:2]:
            self.assertNotIn('source_value_string', r['reported_result'])
            self.assertNotIn('summary_statistic', r['reported_result'])
        self.assertEqual(records[-1]['reported_result']['source_value_string'], '70.5±5.5 GPa (23.6±1.8 N m−1)')
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                html = ParsedHTML(view.render_observation_html(self.bundle, lang)).text
                svg = svg_text(view.render_observation_svg(self.bundle, lang))
                for text in (html, svg):
                    self.assertIn(compact(LABELS[lang]['normalized']), compact(text))
                    self.assertIn(compact(LABELS[lang]['normalized_notice']), compact(text))
                    self.assertIn(compact(LABELS[lang]['source_wording_absent']), compact(text))
                    for r in records[2:]:
                        self.assertIn(compact(r['reported_result']['source_value_string']), compact(text))

    def test_all_locales_complete_and_identity_and_numbers_unchanged(self):
        self.assertEqual(set(LABELS), set(LANGUAGES))
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                self.assertEqual(set(LABELS[lang]), set(LABELS['en']))
                self.assertTrue(all(isinstance(value,str) and value.strip() for value in LABELS[lang].values()))
                if lang != 'en':
                    for key in ('title','normalized','translation_notice','mos2_warning','graphene_warning','hbn_strength_warning'):
                        self.assertNotEqual(LABELS[lang][key], LABELS['en'][key])
                html = view.render_observation_html(self.bundle, lang)
                self.assertIn('<html lang="' + lang + '">', html)
                for markup in (html, view.render_observation_svg(self.bundle, lang),
                               view.render_observation_svg(self.bundle, lang, width=380)):
                    self.assertNotIn('[missing:', markup)
                    visible = ParsedHTML(markup).text if markup.startswith('<!doctype') else svg_text(markup)
                    for rid in IDS:
                        self.assertIn(compact(rid), compact(visible))
                    for value in DISPLAYS:
                        self.assertIn(compact(value), compact(visible))
                    self.assertIn(compact(LABELS[lang]['translation_notice']), compact(visible))

    def test_required_warnings_precede_every_value_even_strength_only(self):
        for lang in LANGUAGES:
            for selected in (None, [IDS[3]], [IDS[5]], [IDS[1]]):
                with self.subTest(lang=lang, selected=selected):
                    b = view.build_observation_inspection(record_ids=selected)
                    html = view.render_observation_html(b, lang)
                    svgs = [view.render_observation_svg(b, lang, width=w) for w in (380,1100)]
                    for facet in b['facets']:
                        texts = [html_article(html, facet['record_id'])] + [svg_card(s, facet['record_id']) for s in svgs]
                        for text in texts:
                            text = compact(text)
                            display_at = text.index(compact(facet['normalized_display']))
                            for code in facet['required_caveat_codes']:
                                warning = translate(code,lang) if code.startswith('catalog_') else LABELS[lang][code]
                                self.assertLess(text.index(compact(warning)), display_at)
                            self.assertLess(text.index(compact(LABELS[lang]['normalized_notice'])), display_at)

    def test_graphene_uncertainty_distribution_and_sample_scope(self):
        stiffness, strength = self.bundle['record_snapshots'][:2]
        for record in (stiffness, strength):
            u = record['reported_result']['uncertainty']
            self.assertEqual(u['type'], 'reported_plus_minus_unspecified')
            self.assertIsNone(u['coverage_factor']); self.assertIsNone(u['confidence_level'])
            self.assertEqual(record['method']['stress_measure'], 'second_piola_kirchhoff')
            self.assertEqual(record['method']['strain_measure'], 'lagrangian')
        self.assertEqual(stiffness['sample_metadata']['counts'], {'force_displacement_fits':67,'membranes':23,'flakes':2})
        self.assertEqual(stiffness['sample_metadata']['fitted_distribution'], {'mean':342,'standard_deviation':30,'unit':'N/m'})
        self.assertIsNone(strength['sample_metadata'])
        b = view.build_observation_inspection([IDS[1]])
        row = next(csv.DictReader(io.StringIO(view.inspection_csv(b))))
        self.assertEqual(row['sample_metadata_json'], 'null')
        self.assertEqual(row['uncertainty_evidence_json'], 'null')
        self.assertEqual(row['source_value_string'], 'null')
        self.assertEqual(row['summary_statistic'], 'null')
        self.assertIn('unverified statistical meaning', row['essential_caveats'])
        visible = ParsedHTML(view.render_observation_html(b)).text
        for phrase in ('67', '342 N/m', '30 N/m', 'SD definition on PDF p. 4'):
            self.assertNotIn(phrase, visible)

    def test_mos2_proof_artifact_uncertainty_and_q_are_not_corrected(self):
        for record in self.bundle['record_snapshots'][2:4]:
            q = record['method']['q_source_report']
            self.assertEqual(q['q_as_printed'], .95)
            self.assertEqual(q['nu_as_printed'], .27)
            self.assertEqual(q['audit_arithmetic_value'], 1.002168693051764)
            self.assertIsNone(q['fit_constant_actually_used'])
            self.assertIsNone(record['method']['stress_measure'])
            self.assertIsNone(record['method']['strain_measure'])
            self.assertEqual(record['verification']['source_inspection']['artifact'], 'epfl_institutional_main_text')
            self.assertFalse(record['verification']['source_inspection']['publisher_final_text_identity_verified'])
            counts = record['sample_metadata']['counts']
            self.assertEqual(counts['study_monolayer_membranes'], 9)
            for key in ('force_displacement_curves','distinct_parent_flakes','failure_events'):
                self.assertIsNone(counts[key])
        b = view.build_observation_inspection([IDS[3]])
        row = next(csv.DictReader(io.StringIO(view.inspection_csv(b))))
        ev = json.loads(row['uncertainty_evidence_json'])
        self.assertIn('PDF p. 4 (D)', ev['locator'])
        self.assertNotIn('peer_review', canonical(ev))
        self.assertEqual(json.loads(row['method_json'])['inference_model'], 'finite_spherical_tip_large_load_maximum_local_stress')
        for text in (ParsedHTML(view.render_observation_html(b)).text, svg_text(view.render_observation_svg(b))):
            for phrase in ('unresolved printed-q discrepancy', 'actual fitted q is unknown', 'no refit or correction', 'PDF p. 5 (E)', '1.002168693051764'):
                self.assertIn(compact(phrase), compact(text))

    def test_hbn_sd_count_and_strength_use_distinct_artifacts_and_models(self):
        for r in self.bundle['record_snapshots'][4:]:
            u = r['reported_result']['uncertainty']
            self.assertEqual(u['type'],'reported_standard_deviation')
            self.assertEqual(u['evidence']['source_url'],HBN_REVIEW)
            self.assertEqual(u['evidence']['artifact'],'peer_review_author_response')
            self.assertIn('PDF p. 8, Reviewer #1 question 3',u['evidence']['locator'])
            sample = r['sample_metadata']
            self.assertEqual(sample['count_definition_source']['source_url'],HBN_REVIEW)
            self.assertEqual(sample['counts']['study_monolayer_tested_sheets'],11)
            for k in ('force_displacement_curves_acquired','force_displacement_curves_retained','force_displacement_curves_excluded','distinct_parent_flakes','failure_events'):
                self.assertIsNone(sample['counts'][k])
            self.assertEqual(sample['typical_protocol']['indentations_per_sheet_typically'],5)
            self.assertIs(sample['typical_protocol']['exact_count'],False)
            self.assertIsNone(r['method']['stress_measure']);self.assertIsNone(r['method']['strain_measure'])
        strength = self.bundle['record_snapshots'][5]
        self.assertNotIn('tested_sheets_explicitly_associated_with_stiffness_average',strength['sample_metadata']['counts'])
        self.assertIsNone(strength['reported_result']['central_statistic_explicitly_named'])
        self.assertEqual(strength['method']['finite_element_model']['strength_reduction'], 'volume_average_of_under_indenter_element_stresses_at_experimental_fracture_load')
        self.assertIsNone(strength['method']['finite_element_model']['reported_stress_component_or_invariant_for_this_average'])
        b = view.build_observation_inspection([IDS[5]])
        row = next(csv.DictReader(io.StringIO(view.inspection_csv(b))))
        self.assertEqual(json.loads(row['uncertainty_evidence_json']),strength['reported_result']['uncertainty']['evidence'])
        self.assertIn('23.6 ± 1.8 N/m',row['normalized_display'])
        self.assertEqual(row['summary_statistic'],'reported_strength_summary')
        self.assertNotIn('mos2_warning', row['required_caveat_codes_json'])
        for text in (ParsedHTML(view.render_observation_html(b)).text, svg_text(view.render_observation_svg(b))):
            for phrase in ('volume-averaged','exact central-statistic label','stress component','maximum Von Mises','Supplementary Figure S5','25.7%','peer_review_author_response','PDF p. 8','typically','55-curve'):
                self.assertIn(compact(phrase),compact(text))

    def test_known_and_unknown_conditions_remain_source_scoped(self):
        for record in self.bundle['record_snapshots']:
            c=record['conditions']
            for key in ('temperature','atmosphere','humidity'):
                self.assertIsNone(c[key])
        for r in self.bundle['record_snapshots'][2:4]:
            self.assertEqual(r['conditions']['loading_rate']['quantity'],'vertical_probe_translation_speed')
            self.assertEqual(r['conditions']['loading_rate']['value'],2)
        for r in self.bundle['record_snapshots'][4:]:
            self.assertEqual(r['conditions']['environment_description'],'ambient conditions')
            self.assertEqual(r['conditions']['loading_rate']['quantity'],'reported_loading_and_unloading_translation_velocity')
            self.assertEqual(r['conditions']['loading_rate']['value'],.5)
            self.assertIsNone(r['conditions']['loading_rate']['strain_rate'])
            self.assertIsNone(r['conditions']['pressure'])
        for text in (ParsedHTML(view.render_observation_html(self.bundle)).text, svg_text(view.render_observation_svg(self.bundle))):
            for phrase in ('0.1 nm','100 nm','0.334 nm','0.48 nm'):
                self.assertIn(compact(phrase),compact(text))

    def test_explicit_inspection_policy_forbids_quantitative_operations(self):
        policy=self.bundle['presentation_policy']
        for key in ('overlay_allowed','aggregation_allowed','unknown_conditions_equivalent','ranking_allowed',
                    'quantitative_axes_allowed','uncertainty_endpoints_calculated','thickness_conversion_allowed',
                    'formula_execution_allowed','associated_study_summaries_are_independent_replications'):
            self.assertIs(policy[key],False)
        self.assertIs(policy['quantities_remain_distinct'],True)
        self.assertEqual(policy['purpose'],'inspection_only')
        self.assertEqual(policy['evaluation_support'],'catalog_only')
        for facet in self.bundle['facets']:
            for key in ('lower','upper','mean','ratio','rank','x','y','point','bar','scale'):
                self.assertNotIn(key,facet)
        tree=ET.fromstring(view.render_observation_svg(self.bundle))
        self.assertFalse(any(node.tag.rsplit('}',1)[-1] in ('line','path','circle','ellipse','polyline','polygon') for node in tree.iter()))

    def test_csv_caveat_columns_precede_values_and_snapshots_round_trip(self):
        reader=csv.DictReader(io.StringIO(view.inspection_csv(self.bundle)))
        columns=reader.fieldnames
        for before in ('classification','evaluation_support','method_family','model_status','required_caveat_codes_json','essential_caveats','presentation_policy_json'):
            for after in ('normalized_display','central_value','plus_minus_value'):
                self.assertLess(columns.index(before),columns.index(after))
        rows=list(reader)
        self.assertEqual(len(rows),6)
        for row,r,f in zip(rows,self.bundle['record_snapshots'],self.bundle['facets']):
            self.assertEqual(row['normalized_display'],f['normalized_display'])
            self.assertEqual(row['central_value'],str(r['reported_result']['value']))
            self.assertEqual(row['plus_minus_value'],str(r['reported_result']['uncertainty']['value']))
            self.assertEqual(row['scalar_missing_convention'],'null')
            self.assertEqual(json.loads(row['record_snapshot_json']),r)
            self.assertEqual(json.loads(row['sample_metadata_json']),r['sample_metadata'])
            self.assertEqual(json.loads(row['conditions_json']),r['conditions'])
            self.assertEqual(json.loads(row['evidence_json']),r['evidence'])
            self.assertEqual(json.loads(row['verification_json']),r['verification'])
            self.assertEqual(row['record_snapshot_sha256'],digest(r))
            self.assertEqual(json.loads(row['selection_json']),self.bundle['selection'])
            source_ids={r['study_id'],*(e['source_id'] for e in r['evidence'])}
            self.assertEqual({s['id'] for s in json.loads(row['source_snapshots_json'])},source_ids)

    def test_grouping_changes_navigation_only_and_preserves_stable_facet_ids(self):
        study=self.bundle
        quantity=view.build_observation_inspection(list(IDS), group_by='quantity')
        self.assertEqual(study['facets'],quantity['facets'])
        for key in ('record_snapshots','source_snapshots','record_digests','source_digests','selection','presentation_policy'):
            self.assertEqual(study[key],quantity[key])
        self.assertEqual([g['identity'] for g in study['groups']],list(dict.fromkeys(r['study_id'] for r in study['record_snapshots'])))
        self.assertEqual([g['identity'] for g in quantity['groups']],list(view.QUANTITIES))
        for group in quantity['groups']:
            self.assertEqual(group['facet_ids'],[f['id'] for f in study['facets'] if f['quantity']==group['identity']])
        subset=view.build_observation_inspection([IDS[-1],IDS[0]])
        self.assertEqual(subset['selection']['requested_record_ids'],[IDS[-1],IDS[0]])
        self.assertEqual(subset['selection']['resolved_record_ids'],[IDS[0],IDS[-1]])
        self.assertEqual(subset['facets'],[study['facets'][0],study['facets'][-1]])

    def test_exact_selection_filters_combine_with_and_and_prune_sources(self):
        source=self.bundle['record_snapshots'][2]['study_id']
        b=view.build_observation_inspection([IDS[0],IDS[3],IDS[2]],source_id=source,quantity=view.QUANTITIES[1])
        self.assertEqual(b['selection']['resolved_record_ids'],[IDS[3]])
        self.assertEqual([s['id'] for s in b['source_snapshots']],[source])
        self.assertEqual(len(b['record_digests']),1)
        self.assertEqual(len(b['source_digests']),1)
        self.assertEqual(view.build_observation_inspection(tuple(IDS[:2]))['selection']['requested_record_ids'],list(IDS[:2]))

    def test_invalid_empty_duplicate_unknown_selectors_fail_closed(self):
        invalid=[dict(record_ids=[]),dict(record_ids=IDS[0]),dict(record_ids={IDS[0]}),dict(record_ids=[IDS[0],IDS[0]]),
                 dict(record_ids=['missing']),dict(record_ids=[IDS[0], 'missing']),dict(record_ids=[None]),dict(record_ids=[True]),
                 dict(record_ids=['']),dict(record_ids=[' '+IDS[0]]),dict(record_ids=[IDS[0]+'\n']),dict(record_ids=[IDS[0]+'\x7f']),
                 dict(source_id='missing'),dict(source_id=''),dict(source_id=True),dict(quantity='youngs_modulus'),
                 dict(quantity=' '+view.QUANTITIES[0]),dict(quantity=True),dict(group_by='material'),dict(group_by=None),
                 dict(record_ids=[IDS[0]],quantity=view.QUANTITIES[1]),dict(record_ids=[IDS[0]],source_id=self.bundle['record_snapshots'][2]['study_id'])]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs),self.assertRaises(view.ObservationInspectionError):
                view.build_observation_inspection(**kwargs)

    def test_same_supported_family_new_ids_are_appendable_and_not_ranked(self):
        changed=deepcopy(self.observations)
        fresh=[]
        for index in (0,2,4):
            record=deepcopy(changed['records'][index]);record['id']='future_copy_'+str(index)
            record['name']='Future same-family presentation fixture '+str(index)
            fresh.append(record)
        changed['records']=fresh+changed['records']
        with catalogs(changed):
            b=view.build_observation_inspection([r['id'] for r in reversed(fresh)])
            self.assertEqual(b['selection']['resolved_record_ids'],[r['id'] for r in fresh])
            self.assertEqual([f['normalized_display'] for f in b['facets']],[DISPLAYS[i] for i in (0,2,4)])
            self.assertEqual(len(set(f['id'] for f in b['facets'])),3)
            view.validate_observation_inspection(b)
            self.assertIn('future_copy_4',view.render_observation_html(b))

    def test_unsupported_families_cannot_inherit_material_name_dispatch(self):
        for index in (0,2,4):
            changed=deepcopy(self.observations)
            changed['records'][index]['method_family']='unreviewed_indentation_family'
            with self.subTest(index=index),catalogs(changed),self.assertRaises(view.ObservationInspectionError):
                view.build_observation_inspection()
        changed=deepcopy(self.observations)
        del changed['records'][4]['method_family']
        with catalogs(changed),self.assertRaises(view.ObservationInspectionError):
            view.build_observation_inspection()

    def test_unsupported_quantity_unit_classification_and_duplicate_catalog_ids_rejected(self):
        for path,value in ((('quantity',),'youngs_modulus'),(('si_unit',),'GPa'),(('reported_result','unit'),'GPa'),
                           (('reported_result','uncertainty','unit'),'GPa'),(('observation_type',),'raw_measurement'),
                           (('evaluation_support',),'executable')):
            changed=deepcopy(self.observations);set_path(changed['records'][0],path,value)
            with self.subTest(path=path),catalogs(changed),self.assertRaises(view.ObservationInspectionError):
                view.build_observation_inspection()
        changed=deepcopy(self.observations);changed['records'].append(deepcopy(changed['records'][0]))
        with catalogs(changed),self.assertRaises(view.ObservationInspectionError):view.build_observation_inspection()
        changed=deepcopy(self.sources);changed['records'].append(deepcopy(changed['records'][0]))
        with catalogs(sources=changed),self.assertRaises(view.ObservationInspectionError):view.build_observation_inspection()

    def test_tampered_and_stale_bundle_rejected_before_every_serializer(self):
        mutations=[
            (('schema_version',),'2.0.0'),(('kind',),'comparison'),(('engine_version',),'0.0.0'),
            (('catalog_schema_versions','observations'),'1.1.0'),(('catalog_schema_versions','sources'),'9.0.0'),
            (('facets',0,'normalized_display'),'341 ± 50 N/m'),(('facets',2,'required_caveat_codes'),[]),
            (('facets',5,'display_basis'),'source_quote'),(('facets',0,'id'),'observation-'+'0'*64),
            (('record_snapshots',0,'reported_result','value'),341),
            (('record_snapshots',5,'reported_result','source_value_string'),'23.6 N/m'),
            (('record_snapshots',0,'material','layer_count'),True),
            (('record_snapshots',2,'sample_metadata','counts','failure_events'),9),
            (('record_snapshots',0,'version'),'2.0.0'),(('source_snapshots',0,'title'),'Altered source'),
            (('record_digests',0,'sha256'),'0'*64),(('source_digests',0,'sha256'),'0'*64),
            (('presentation_policy','aggregation_allowed'),True),
            (('presentation_policy','unknown_conditions_equivalent'),True),
            (('selection','resolved_record_ids'),list(reversed(IDS))),
            (('selection','requested_record_ids'),[IDS[0]]),
            (('groups',0,'facet_ids'),[]),
            (('extra_metadata',),{'safe_looking':True}),
            (('facets',0,'extra_metadata'),'undeclared'),
            (('record_snapshots',0,'extra_metadata'),'undeclared'),
            (('source_snapshots',0,'extra_metadata'),'undeclared'),
        ]
        outputs=(view.validate_observation_inspection,view.inspection_json,view.inspection_csv,
                 view.render_observation_html,view.render_observation_svg)
        for path,replacement in mutations:
            bad=deepcopy(self.bundle);set_path(bad,path,replacement)
            for output in outputs:
                with self.subTest(path=path,output=output.__name__),self.assertRaises(view.ObservationInspectionError):output(bad)

    def test_stale_current_catalog_snapshot_requires_regeneration(self):
        changed=deepcopy(self.sources)
        next(s for s in changed['records'] if s['id']==self.bundle['source_snapshots'][0]['id'])['title']+=' (updated metadata)'
        with catalogs(sources=changed):
            with self.assertRaisesRegex(view.ObservationInspectionError,'stale|regenerate'):
                view.validate_observation_inspection(self.bundle)
            fresh=view.build_observation_inspection()
            view.validate_observation_inspection(fresh)
            self.assertNotEqual(fresh['source_digests'],self.bundle['source_digests'])

    def test_boolean_nonfinite_and_non_json_values_rejected(self):
        for value in (True,False,float('nan'),float('inf'),float('-inf'),10**1000):
            for field in ('value','uncertainty'):
                changed=deepcopy(self.observations)
                path=('reported_result','value') if field=='value' else ('reported_result','uncertainty','value')
                set_path(changed['records'][0],path,value)
                with self.subTest(value=repr(value),field=field),catalogs(changed),self.assertRaises(view.ObservationInspectionError):
                    view.build_observation_inspection()
        for value in (float('nan'),float('inf'),{1:'non-string key'},('tuple',),object()):
            bad=deepcopy(self.bundle);bad['extra']=value
            with self.subTest(value=repr(value)),self.assertRaises(view.ObservationInspectionError):
                view.validate_observation_inspection(bad)
        changed=deepcopy(self.sources);changed['records'][0]['year']=float('nan')
        with catalogs(sources=changed),self.assertRaises(view.ObservationInspectionError):view.build_observation_inspection()

    def test_unsupported_catalog_schema_versions_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'unsupported-schema'
            for kind in ('observations','sources'):
                for version in ('9.0.0',None,True):
                    observations=deepcopy(self.observations);sources=deepcopy(self.sources)
                    (observations if kind=='observations' else sources)['schema_version']=version
                    with self.subTest(kind=kind,version=version),catalogs(observations,sources):
                        with self.assertRaises(view.ObservationInspectionError):view.build_observation_inspection()
                        with self.assertRaises(view.ObservationInspectionError):view.export_observation_inspection(target)
                    self.assertFalse(target.exists())

    def test_builder_reads_only_observations_and_sources_and_never_evaluates(self):
        with catalogs() as reader,patch('materials_boundaries.engine.evaluate',side_effect=AssertionError('No evaluation')), \
             patch('materials_boundaries.evaluate',side_effect=AssertionError('No evaluation')), \
             patch('materials_boundaries.visualization.build_comparison',side_effect=AssertionError('No comparison')):
            b=view.build_observation_inspection()
            self.assertEqual([call.args[0] for call in reader.call_args_list],['observations','sources'])
            view.inspection_json(b);view.inspection_csv(b)
            view.render_observation_html(b);view.render_observation_svg(b)
            self.assertEqual({call.args[0] for call in reader.call_args_list},{'observations','sources'})

    def test_runtime_needs_no_jsonschema_or_nonstandard_dependency(self):
        script=('import sys; sys.modules["jsonschema"] = None; sys.modules["referencing"] = None; '
                'from materials_boundaries.observation_visualization import *; '
                'b=build_observation_inspection(); validate_observation_inspection(b); '
                'inspection_json(b); inspection_csv(b); render_observation_html(b); render_observation_svg(b); print("ok")')
        result=subprocess.run([sys.executable,'-S','-c',script],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'ok')

    def test_html_svg_escaping_inert_json_and_no_executable_network_dependencies(self):
        changed=deepcopy(self.observations);sources=deepcopy(self.sources)
        attack='</pre><script src="https://example.test/payload.js">alert(1)</script><img src=x onerror=alert(2)> & " Ω'
        changed['records'][0]['name']=attack
        # IDs need not be limited to a historical whitelist, so attributes must escape them.
        changed['records'][0]['id']='future_<"&>'+'x'*220
        rid=changed['records'][0]['id']
        source=next(s for s in sources['records'] if s['id']==changed['records'][0]['study_id'])
        source['title']=attack
        source['urls'].append('https://example.test/a?x="quoted"&long='+'a'*240)
        with catalogs(changed,sources):
            b=view.build_observation_inspection([rid])
            html=view.render_observation_html(b)
            parsed=ParsedHTML(html)
            self.assertEqual(json.loads(''.join(parsed.embedded)),b)
            self.assertIn(attack,parsed.text)
            self.assertNotIn('<script',html)
            self.assertIn('&lt;script',html)
            allowed={'html','head','meta','title','style','body','header','p','h1','h2','h3','main','section','div','article','a','details','summary','pre'}
            for tag,attrs in parsed.tags:
                self.assertIn(tag,allowed)
                self.assertFalse(any(k.startswith('on') or k in ('src','srcset') for k in attrs))
                if 'href' in attrs:self.assertRegex(attrs['href'],r'^https?://')
            for width in (320,380,1100):
                svg=view.render_observation_svg(b,width=width)
                tree=ET.fromstring(svg)
                self.assertIn(compact(attack),compact(svg_text(svg)))
                card=next(node for node in tree.iter(SVG_NS+'g') if node.attrib.get('data-record-id')==rid)
                self.assertEqual(card.attrib['id'],b['facets'][0]['id'])
                for node in tree.iter():
                    self.assertNotIn(node.tag.rsplit('}',1)[-1],('script','image','foreignObject','iframe','use'))
                    self.assertFalse(any(k.startswith('on') for k in node.attrib))
                    if 'href' in node.attrib:self.assertRegex(node.attrib['href'],r'^https?://')
            self.assertNotRegex(html,r'(?i)@import|url\(|<link\b|<iframe\b|<object\b')

    def test_unsafe_source_links_rejected_in_source_and_evidence(self):
        for unsafe in ('javascript:alert(1)','data:text/html,test','file:///tmp/test','//example.test/path',
                       'https://user:password@example.test/','https://example.test/has space','https://example.test/\nnext','https://example.test:bad/'):
            sources=deepcopy(self.sources)
            next(s for s in sources['records'] if s['id']==self.bundle['source_snapshots'][0]['id'])['urls']=[unsafe]
            with self.subTest(unsafe=unsafe),catalogs(sources=sources),self.assertRaises(view.ObservationInspectionError):
                view.build_observation_inspection()
            changed=deepcopy(self.observations);changed['records'][2]['evidence'][0]['source_url']=unsafe
            with self.subTest(evidence=unsafe),catalogs(changed),self.assertRaises(view.ObservationInspectionError):
                view.build_observation_inspection()

    def test_width_and_locale_validation_and_svg_text_inside_canvas(self):
        for width in (True,False,319,1601,380.0,None):
            with self.subTest(width=width),self.assertRaises(view.ObservationInspectionError):view.render_observation_svg(self.bundle,width=width)
        for lang in ('fr','EN',None,True):
            for output in (view.render_observation_html,view.render_observation_svg):
                with self.subTest(lang=lang,output=output.__name__),self.assertRaises(view.ObservationInspectionError):output(self.bundle,lang=lang)
        for lang in LANGUAGES:
            for width in (320,380,1100):
                root=ET.fromstring(view.render_observation_svg(self.bundle,lang,width))
                height=float(root.attrib['height'])
                for node in root.iter(SVG_NS+'text'):
                    self.assertGreaterEqual(float(node.attrib['x']),0)
                    self.assertLess(float(node.attrib['x']),width)
                    self.assertGreater(float(node.attrib['y']),0)
                    self.assertLess(float(node.attrib['y']),height)

    def test_exports_deterministic_locale_independent_json_and_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=[]
            for lang in LANGUAGES:
                target=Path(tmp)/lang
                names=view.export_observation_inspection(target,record_ids=list(IDS),lang=lang)
                expected={'observation-inspection.json','observation-inspection.csv',f'observation-inspection.{lang}.svg',f'observation-inspection.narrow.{lang}.svg',f'observation-inspection.{lang}.html'}
                self.assertEqual(set(names),expected)
                self.assertEqual({p.name for p in target.iterdir()},expected)
                before={name:(target/name).read_bytes() for name in names}
                self.assertEqual(json.loads(before['observation-inspection.json']),self.bundle)
                view.export_observation_inspection(target,record_ids=list(IDS),lang=lang)
                self.assertEqual(before,{name:(target/name).read_bytes() for name in names})
                data.append((before['observation-inspection.json'],before['observation-inspection.csv']))
            self.assertTrue(all(pair==data[0] for pair in data))
        self.assertEqual(view.inspection_json(self.bundle),view.inspection_json(view.build_observation_inspection(list(IDS))))
        self.assertNotIn('generated_at',view.inspection_json(self.bundle))

    def test_invalid_exports_and_late_render_failure_do_not_write_any_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'never-created'
            for kwargs in (dict(record_ids=[]),dict(record_ids=['unknown']),dict(lang='fr'),dict(group_by='magnitude')):
                with self.subTest(kwargs=kwargs),self.assertRaises(view.ObservationInspectionError):view.export_observation_inspection(target,**kwargs)
                self.assertFalse(target.exists())
            with patch.object(view,'render_observation_html',side_effect=view.ObservationInspectionError('late renderer error')):
                with self.assertRaises(view.ObservationInspectionError):view.export_observation_inspection(target)
                self.assertFalse(target.exists())
                target.mkdir();(target/'observation-inspection.json').write_text('keep existing',encoding='utf-8')
                with self.assertRaises(view.ObservationInspectionError):view.export_observation_inspection(target)
                self.assertEqual({p.name:p.read_text() for p in target.iterdir()},{'observation-inspection.json':'keep existing'})

    def test_catalog_files_evaluations_and_existing_visualization_unchanged(self):
        paths=list((ROOT/'materials_boundaries/data').glob('*.json'))
        before={p:p.read_bytes() for p in paths}
        expected_evaluation=evaluate(example())
        expected_comparison=build_comparison([example()],fractions=[0,.5,1])
        case=expected_comparison['cases'][0]['id']
        expected_html=render_html(expected_comparison)
        expected_svg=render_svg(expected_comparison,case)
        with tempfile.TemporaryDirectory() as tmp:view.export_observation_inspection(tmp)
        self.assertEqual(before,{p:p.read_bytes() for p in paths})
        self.assertEqual(evaluate(example()),expected_evaluation)
        comparison=build_comparison([example()],fractions=[0,.5,1])
        self.assertEqual(comparison,expected_comparison)
        self.assertEqual(render_html(comparison),expected_html)
        self.assertEqual(render_svg(comparison,case),expected_svg)
        self.assertEqual(len(expected_evaluation['evaluations']),8)
        self.assertEqual(len(comparison['series']),8)
        for rid in IDS:self.assertNotIn(rid,expected_html+expected_svg)


    def test_default_selection_includes_all_current_supported_records_in_catalog_order(self):
        with catalogs():
            b=view.build_observation_inspection()
        expected=read_catalog('observations')['records']
        self.assertIsNone(b['selection']['requested_record_ids'])
        self.assertEqual(b['selection']['resolved_record_ids'],[r['id'] for r in expected])
        self.assertEqual(b['record_snapshots'],expected)
        self.assertEqual([g['identity'] for g in b['groups']],list(dict.fromkeys(r['study_id'] for r in expected)))
        with catalogs():
            grouped=view.build_observation_inspection(group_by='quantity')
        self.assertEqual(grouped['facets'],b['facets'])
        for group in grouped['groups']:
            self.assertEqual(group['facet_ids'],[f['id'] for f in b['facets'] if f['quantity']==group['identity']])

    def test_source_defined_payload_cannot_be_reinterpreted_by_patched_catalog(self):
        changes=[
            (0,('reported_result','uncertainty','confidence_level'),.95),
            (0,('reported_result','uncertainty','coverage_factor'),2),
            (0,('method','stress_measure'),'cauchy'),
            (0,('method','strain_measure'),'engineering_strain'),
            (0,('sample_metadata','counts','force_displacement_fits'),True),
            (0,('reported_result','uncertainty','type'),'reported_standard_error'),
            (2,('reported_result','uncertainty','interpretation'),'Certified uncertainty bounds'),
            (2,('method','inference'),'Corrected indentation model'),
            (2,('evidence',0,'locator'),'Publisher final p. 999'),
            (2,('conditions','loading_rate','value'),99),
            (2,('verification','gaps'),[]),
        ]
        for index,path,value in changes:
            changed=deepcopy(self.observations);set_path(changed['records'][index],path,value)
            with self.subTest(index=index,path=path),catalogs(changed),self.assertRaises(view.ObservationInspectionError):
                view.build_observation_inspection()

    def test_source_model_assumptions_and_hbn_q_are_visible(self):
        html=view.render_observation_html(self.bundle)
        svg=view.render_observation_svg(self.bundle)
        for record in self.bundle['record_snapshots']:
            for text in (html_article(html,record['id']),svg_card(svg,record['id'])):
                self.assertIn(compact(str(record['method']['poissons_ratio_assumed'])),compact(text))
                for assumption in record['method']['model_assumptions']:
                    self.assertIn(compact(assumption),compact(text))
        hbn=self.bundle['record_snapshots'][4]
        for text in (html_article(html,hbn['id']),svg_card(svg,hbn['id'])):
            for value in (hbn['method']['q_source_report']['formula_as_printed'],
                          hbn['method']['fit_force_law']['source_locator']):
                self.assertIn(compact(value),compact(text))
        stiff=html_article(html,IDS[0])
        self.assertIn('342 N/m',stiff);self.assertIn('30 N/m',stiff)
        self.assertNotIn('[missing:',stiff)

    def test_xml_illegal_text_rejected_before_export_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'invalid-text'
            for value in ('illegal\x00text','illegal\x01text','illegal\ud800text','illegal\ufffetext'):
                changed=deepcopy(self.observations);changed['records'][0]['name']=value
                with self.subTest(value=repr(value)),catalogs(changed):
                    with self.assertRaises(view.ObservationInspectionError):view.build_observation_inspection()
                    with self.assertRaises(view.ObservationInspectionError):view.export_observation_inspection(target)
                self.assertFalse(target.exists())
            sources=deepcopy(self.sources)
            sources['records'][0]['title']='source\x00title'
            with catalogs(sources=sources),self.assertRaises(view.ObservationInspectionError):view.export_observation_inspection(target)
            self.assertFalse(target.exists())


class ObservationInspectionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=load_json(ROOT/'schemas/observation-inspection.schema.json')
        dependencies=[load_json(ROOT/'schemas'/name) for name in ('observations.schema.json','sources.schema.json')]
        registry=Registry().with_resources((s['$id'],Resource.from_contents(s)) for s in [cls.schema]+dependencies)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator=Draft202012Validator(cls.schema,registry=registry,format_checker=FormatChecker())
        cls.observations=baseline_observations()
        cls.sources=read_catalog('sources')
        with catalogs(cls.observations,cls.sources):
            cls.bundle=view.build_observation_inspection(list(IDS))

    def setUp(self):
        context = catalogs(self.observations, self.sources)
        context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)

    def test_current_full_subset_and_grouped_bundles_validate(self):
        self.validator.validate(self.bundle)
        for rid in IDS:
            self.validator.validate(view.build_observation_inspection([rid]))
        self.validator.validate(view.build_observation_inspection(group_by='quantity'))
        changed=deepcopy(read_catalog('observations'))
        changed['records'][4]['id']='future_hbn_same_family_id'
        with catalogs(changed):self.validator.validate(view.build_observation_inspection())

    def test_every_new_object_structure_is_closed(self):
        def walk(schema):
            if isinstance(schema,dict):
                if schema.get('type')=='object':
                    self.assertIs(schema.get('additionalProperties'),False)
                    self.assertEqual(set(schema['required']),set(schema['properties']))
                for value in schema.values():walk(value)
            elif isinstance(schema,list):
                for value in schema:walk(value)
        walk(self.schema)
        refs=[self.schema['properties'][key]['items']['$ref'] for key in ('record_snapshots','source_snapshots')]
        self.assertEqual(refs,['urn:materials-boundaries:schema:observations:1.2.0#/properties/records/items',
                               'urn:materials-boundaries:schema:sources:1.0.0#/properties/records/items'])

    def test_extra_fields_rejected_at_every_snapshot_object_depth(self):
        paths=[]
        def walk(value,path=()):
            if isinstance(value,dict):
                paths.append(path)
                for key,item in value.items():walk(item,path+(key,))
            elif isinstance(value,list):
                for index,item in enumerate(value):walk(item,path+(index,))
        walk(self.bundle)
        self.assertGreater(len(paths),100)
        for path in paths:
            bad=deepcopy(self.bundle);target=bad
            for part in path:target=target[part]
            target['undeclared_extra_metadata']=True
            with self.subTest(path=path):self.assertFalse(self.validator.is_valid(bad))

    def test_schema_rejects_policy_caveats_types_and_unsupported_snapshot_family(self):
        mutations=[(('presentation_policy','overlay_allowed'),True),
                   (('catalog_schema_versions','observations'),'9.0.0'),
                   (('facets',0,'required_caveat_codes'),['sd_warning']),
                   (('facets',5,'required_caveat_codes'),['hbn_stiffness_warning','catalog_hbn_sd_notice','sd_warning']),
                   (('facets',0,'method_family'),'unknown'),
                   (('record_snapshots',0,'reported_result','value'),True),
                   (('record_snapshots',4,'method_family'),'unknown'),
                   (('source_digests',0,'sha256'),'not-a-digest'),
                   (('source_snapshots',0,'version'),'invented'),
                   (('selection','requested_record_ids'),[IDS[0],IDS[0]]),
                   (('selection','resolved_record_ids'),[])]
        for path,value in mutations:
            bad=deepcopy(self.bundle);set_path(bad,path,value)
            with self.subTest(path=path):self.assertFalse(self.validator.is_valid(bad))


class ObservationInspectionCLITests(unittest.TestCase):
    def setUp(self):
        context = catalogs(baseline_observations())
        context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)

    def invoke(self,args):
        stdout,stderr=io.StringIO(),io.StringIO()
        with redirect_stdout(stdout),redirect_stderr(stderr):
            try:code=main(args)
            except SystemExit as exc:code=exc.code
        return code,stdout.getvalue(),stderr.getvalue()

    def test_cli_four_locales_exact_subset_and_language_independent_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_data=[];csv_data=[]
            for lang in LANGUAGES:
                target=Path(tmp)/lang
                args=['observation','inspect','--output',str(target),'--id',IDS[5],'--id',IDS[3],
                      '--quantity','breaking_strength_2d','--group-by','quantity','--lang',lang]
                code,out,err=self.invoke(args)
                self.assertEqual(code,0,err)
                self.assertEqual(len(json.loads(out)['artifacts']),5)
                b=json.loads((target/'observation-inspection.json').read_text())
                self.assertEqual(b['selection']['resolved_record_ids'],[IDS[3],IDS[5]])
                self.assertEqual(b['selection']['requested_record_ids'],[IDS[5],IDS[3]])
                self.assertEqual(b['group_by'],'quantity')
                self.assertIn(LABELS[lang]['title'],(target/f'observation-inspection.{lang}.html').read_text())
                json_data.append((target/'observation-inspection.json').read_bytes())
                csv_data.append((target/'observation-inspection.csv').read_bytes())
            self.assertTrue(all(x==json_data[0] for x in json_data))
            self.assertTrue(all(x==csv_data[0] for x in csv_data))

    def test_cli_source_filter_and_invalid_inputs_do_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'filtered'
            source='bertolazzi_brivio_kis_2011'
            code,out,err=self.invoke(['observation','inspect','--output',str(target),'--source-id',source])
            self.assertEqual(code,0,err)
            self.assertEqual(json.loads((target/'observation-inspection.json').read_text())['selection']['resolved_record_ids'],list(IDS[2:4]))
            for extras in (['--id','missing'],['--id',IDS[0],'--id',IDS[0]],['--quantity','3d_strength'],['--group-by','rank'],['--lang','fr']):
                invalid=Path(tmp)/'invalid'
                code,out,err=self.invoke(['observation','inspect','--output',str(invalid)]+extras)
                self.assertNotEqual(code,0)
                self.assertFalse(invalid.exists())

    def test_cli_help_is_complete_in_four_languages(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                code,out,err=self.invoke(['observation','inspect','--lang',lang,'--help'])
                self.assertEqual(code,0,err)
                self.assertIn(LABELS[lang]['inspect'],out)
                self.assertNotIn('[missing:',out)
                for flag in ('--output','--id','--source-id','--quantity','--group-by','--lang'):
                    self.assertIn(flag,out)


if __name__=='__main__':
    unittest.main()
