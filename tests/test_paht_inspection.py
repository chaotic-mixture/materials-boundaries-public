"""Separate PAHT median/SD inspection, source caveats and unchanged old views."""
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from materials_boundaries import observation_visualization as view
from materials_boundaries._paht_cf_observation_contract import PAHT_FAMILY, PAHT_SOURCE, PAHT_DATASET, PAHT_QUANTITY
from materials_boundaries._paht_observation_labels import PAHT_LABELS, PAHT_CAVEATS
from materials_boundaries.catalog import read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.observation_temperature_plot import build_observation_temperature_plot, ObservationTemperaturePlotError
from test_observation_inspection import LANGUAGES, ParsedHTML, catalogs, compact, html_article, svg_card, set_path

ROOT = Path(__file__).resolve().parents[1]
TEMPERATURES = ('25', '50', '100', '150')
IDS = tuple('zach-2025-paht-cf-annealed-uts-' + value + 'c' for value in TEMPERATURES)
MEDIANS = ('58.91', '40.87', '29.64', '19.03')
SD = ('3.44', '4.59', '0.72', '0.67')
PA = (58910000, 40870000, 29640000, 19030000)
PA_SD = (3440000, 4590000, 720000, 670000)
# Pre-edit v0.23 selected output hashes, captured before PAHT was added.
# These identify project output bytes, not publisher artifacts or scientific review.
OLD_IDS = ('lee_2008_graphene_in_plane_stiffness_2d', 'lee_2008_graphene_breaking_strength_2d', 'bertolazzi_2011_mos2_monolayer_in_plane_stiffness_2d', 'bertolazzi_2011_mos2_monolayer_breaking_strength_2d', 'falin_2017_hbn_monolayer_in_plane_stiffness_2d', 'falin_2017_hbn_monolayer_breaking_strength_2d', 'ciganas2026-pa12cf15-uts-23c', 'ciganas2026-pa12cf15-uts-40c', 'ciganas2026-pa12cf15-uts-60c', 'ciganas2026-pa12cf15-uts-80c', 'ciganas2026-pa12cf15-uts-100c', 'ciganas2026-pa12cf15-uts-120c')
OLD_SOURCE_IDS = ('lee_wei_kysar_hone_2008', 'bertolazzi_brivio_kis_2011',
                  'falin_et_al_2017_hbn_mechanical_properties', 'ciganas2026polym18050563')
OLD_OUTPUT_SHA256 = {'bundle.json': 'e382538b64d0a79c190608b0b9e8d1087ec0d7093d01db47b2daffcae317e9fe', 'de.html': 'f54ebd3a4539053566ddaaec355427fd9c4628310b07f656aeee2f59c1e10be2', 'de.narrow.svg': '553a4db501241f8054c0179e9f36dc6d606b7bd132fbc22e50fdc385b273b517', 'de.svg': '698c09490d0094c428ea57cc94cb990e34e6481f01a41d9cea264dd3c5cee9da', 'de.txt': 'c3fc1075bab5393e5ae492dd96072b97c167197937f8b7f336aeda962332925b', 'en.html': 'd3edea4e9806dc0c2c9304917c1f9da461a2fb0ce0c6c79cbe46ba22d4140f73', 'en.narrow.svg': '43c517836360e7ac0cc984346871e77edf87c1a746db6ec097b041e4754e42dc', 'en.svg': 'abe7a5fd9434a2f2f317094a3f4fd3c0dd49b0629bfc2545ce597355e52a008a', 'en.txt': '85e52be0b94f0b6ab034d0efcf2f9277801ff3a09e88e3bd495ebb9a61249ad8', 'inspection.csv': '6238450d4a4f4180d0e4c00c2d968636720e0e4701504531b90122add9653e6f', 'ja.html': '496792d3a10005c72fff0b1355359210032b04642edbda3a783e6d417a0a5310', 'ja.narrow.svg': '3806d7cf25f3c8052aaf098c69ebea527a6bdc4d060c77023125acba84a1fc55', 'ja.svg': '512f57110494dd86c56e4d613eb32bd0349ff34d3272985f8fcf7dc3d8952e66', 'ja.txt': 'e875901db05dc8d83e183ac47825c2acad93d32c2265f024a06a03417c30263c', 'zh.html': '8cb37f970a4f91e0d86a216d180c6cdbaf16f4a7498d3dc36b65aca634ebd004', 'zh.narrow.svg': 'bf09489e20d7c1d4cfc68ab267ddd5a8c94219a0c3ebdd6b97508fc54bdbff60', 'zh.svg': '60eeefc7e35b37c610b628f5b11b5c7d03ef866020b58e1646e1a572b729b0ea', 'zh.txt': '32971f00dbc2f64c6c8c3673c9721eda092d1512d57690f51d7293afd0807119'}


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def fixed_scientific_catalogs(observations, sources):
    """Isolate the named original cells and source order for byte fixtures.

    Live source ordering and additive records are tested independently below.
    Neither reordering nor appending a catalog record changes these fixtures.
    """
    observations, sources = deepcopy(observations), deepcopy(sources)
    by_id = {r['id']: r for r in observations['records']}
    observations['records'] = [by_id[rid] for rid in (*OLD_IDS, *IDS)]
    by_id = {r['id']: r for r in sources['records']}
    sources['records'] = [by_id[sid] for sid in (*OLD_SOURCE_IDS, PAHT_SOURCE)]
    return observations, sources


class PAHTInspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observations, cls.sources = read_catalog('observations'), read_catalog('sources')
        cls.fixture_observations, cls.fixture_sources = fixed_scientific_catalogs(cls.observations, cls.sources)
        with catalogs(cls.fixture_observations, cls.fixture_sources):
            cls.bundle = view.build_observation_inspection(source_id=PAHT_SOURCE)
        schemas = [json.loads((ROOT/'schemas'/name).read_text()) for name in
                   ('observation-inspection.schema.json', 'observations.schema.json', 'sources.schema.json')]
        registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas)
        Draft202012Validator.check_schema(schemas[0])
        cls.validator = Draft202012Validator(schemas[0], registry=registry, format_checker=FormatChecker())

    def setUp(self):
        context = catalogs(self.fixture_observations, self.fixture_sources)
        context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)

    def test_live_and_reversed_catalogs_preserve_their_own_source_order(self):
        reversed_observations, reversed_sources = deepcopy(self.observations), deepcopy(self.sources)
        reversed_observations['records'].reverse()
        reversed_sources['records'].reverse()
        self.assertEqual(fixed_scientific_catalogs(reversed_observations, reversed_sources),
                         (self.fixture_observations, self.fixture_sources))
        original_uts = set(OLD_IDS[6:] + IDS)
        for observations, sources in ((self.observations, self.sources),
                                      (reversed_observations, reversed_sources)):
            with self.subTest(order=[r['id'] for r in observations['records']]), catalogs(observations, sources):
                bundle = view.build_observation_inspection()
                self.assertEqual(bundle['selection']['resolved_record_ids'],
                                 [r['id'] for r in observations['records']])
                selected_sources = {s['id'] for s in bundle['source_snapshots']}
                self.assertEqual([s['id'] for s in bundle['source_snapshots']],
                                 [s['id'] for s in sources['records'] if s['id'] in selected_sources])
                uts = view.build_observation_inspection(quantity=PAHT_QUANTITY)
                self.assertEqual([f['record_id'] for f in uts['facets']],
                                 [r['id'] for r in observations['records'] if r['quantity'] == PAHT_QUANTITY])
                # Exactly ten original UTS cells survive; separately appended
                # same-family records do not become extra historical cells.
                self.assertEqual({f['record_id'] for f in uts['facets'] if f['record_id'] in original_uts},
                                 original_uts)
                self.assertEqual(len(original_uts), 10)
                self.validator.validate(bundle)
                self.validator.validate(uts)

    def test_exact_source_cells_median_and_sd_fields_with_unit_basis(self):
        self.assertEqual(self.bundle['schema_version'], '1.1.0')
        self.assertEqual(self.bundle['selection']['resolved_record_ids'], list(IDS))
        for i, facet in enumerate(self.bundle['facets']):
            self.assertEqual(facet['reported_median_string'], MEDIANS[i])
            self.assertEqual(facet['reported_sd_string'], SD[i])
            self.assertEqual(facet['summary_statistic'], 'median_as_reported')
            self.assertEqual(facet['uncertainty_notation'], 'separate_sd')
            self.assertEqual(facet['si_value'], PA[i])
            self.assertEqual(facet['si_sd_value'], PA_SD[i])
            self.assertEqual(facet['source_cell']['temperature_column'], TEMPERATURES[i])
            self.assertEqual(facet['temperature']['value_string'], TEMPERATURES[i])
            self.assertEqual(facet['temperature_basis'], 'reported_chamber_test_condition')
            self.assertEqual(facet['sd_unit_basis'], 'contextual_inference_from_associated_uts_column')
            self.assertFalse(facet['sd_header_unit_explicit'])
            self.assertEqual(facet['si_sd_unit_basis'], 'conditional_on_contextual_MPa_inference')
            self.assertEqual(facet['sd_unit'], 'MPa')
            self.assertEqual(facet['si_sd_unit'], 'Pa')
            self.assertTrue(facet['normalization']['sd_conversion_is_conditional'])
            self.assertFalse(facet['normalization']['adds_measurement_precision'])
            self.assertEqual(facet['normalized_display'], f'Median: {MEDIANS[i]} MPa; SD: {SD[i]} MPa (unit contextually inferred)')
            self.assertEqual(facet['si_display'], f'Median: {PA[i]} Pa; SD: {PA_SD[i]} Pa (source unit contextually inferred)')
            self.assertFalse(any('plus_minus' in key for key in facet))
            self.assertNotIn(' ± ', facet['normalized_display'])
            self.assertNotIn(' ± ', facet['si_display'])
        self.validator.validate(self.bundle)

    def test_all_ten_same_quantity_cells_are_separate_source_facets(self):
        bundle = view.build_observation_inspection(quantity=PAHT_QUANTITY)
        self.assertEqual(len(bundle['facets']), 10)
        self.assertEqual([f['record_id'] for f in bundle['facets'] if f['method_family'] == PAHT_FAMILY], list(IDS))
        self.assertEqual(len(bundle['groups']), 2)
        for grouping in ('study', 'quantity'):
            b = view.build_observation_inspection(list(reversed(IDS)) + [OLD_IDS[0]], group_by=grouping)
            self.validator.validate(b)
            self.assertEqual(b['selection']['resolved_record_ids'], [OLD_IDS[0], *IDS])
            self.validator.validate(view.build_observation_inspection(group_by=grouping))
        self.assertFalse(bundle['presentation_policy']['ranking_allowed'])
        self.assertFalse(bundle['presentation_policy']['quantitative_axes_allowed'])
        self.assertFalse(bundle['presentation_policy']['uncertainty_endpoints_calculated'])
        with self.assertRaises(ObservationTemperaturePlotError):
            build_observation_temperature_plot(dataset_id=PAHT_DATASET)

    def test_complete_four_language_wording_and_warnings_precede_every_value(self):
        self.assertEqual(set(PAHT_LABELS), set(LANGUAGES))
        for language in LANGUAGES:
            t = PAHT_LABELS[language]
            self.assertEqual(set(t), set(PAHT_LABELS['en']))
            self.assertTrue(all(isinstance(value, str) and value.strip() for value in t.values()))
            self.assertTrue(all(view.labels(language)[key] == value for key, value in t.items()))
            if language != 'en':
                self.assertTrue(all(t[code] != PAHT_LABELS['en'][code] for code in PAHT_CAVEATS))
            html = view.render_observation_html(self.bundle, language)
            svgs = [view.render_observation_svg(self.bundle, language, width) for width in (380, 1100)]
            for i, record in enumerate(self.bundle['record_snapshots']):
                single = {'schema_version': '1.3.0', 'records': [record]}
                texts = [html_article(html, IDS[i]), render_catalog(single, 'observations', language)]
                texts.extend(svg_card(svg, IDS[i]) for svg in svgs)
                for text in texts:
                    text = compact(text)
                    values = [t['paht_reported_median'] + ': ' + MEDIANS[i] + ' MPa',
                              t['paht_reported_sd'] + ': ' + SD[i] + ' MPa',
                              t['paht_si_median'] + ': ' + str(PA[i]) + ' Pa',
                              t['paht_si_sd'] + ': ' + str(PA_SD[i]) + ' Pa']
                    for value in values:
                        index = text.index(compact(value))
                        for warning in PAHT_CAVEATS:
                            self.assertLess(text.index(compact(t[warning])), index)
                        self.assertLess(text.index(compact(t['paht_identity'])), index)
                        self.assertLess(text.index(compact(t['paht_temperature'] + ': ' + TEMPERATURES[i] + ' °C')), index)
                    self.assertNotIn(compact(MEDIANS[i] + ' ± ' + SD[i]), text)
                    self.assertNotIn(compact(str(PA[i]) + ' ± ' + str(PA_SD[i])), text)
                    self.assertNotIn('[missing:', text)
                    # Original context must be visible without expanding the full JSON.
                    for key in ('relative_humidity_percent', 'calibration', 'stress_area_basis',
                                'statistic_evidence', 'header_unit_explicit', 'count_definition_source'):
                        self.assertIn(key, text)
            parsed = ParsedHTML(html)
            self.assertFalse(any(tag in ('script', 'img', 'iframe', 'object') for tag, _ in parsed.tags))
            urls = [attrs['href'] for tag, attrs in parsed.tags if tag == 'a']
            self.assertIn('https://creativecommons.org/licenses/by/4.0/', urls)
            self.assertTrue(any('#sec3dot1-jcs-09-00624' in url for url in urls))
            tags = {node.tag.rsplit('}', 1)[-1] for node in ET.fromstring(svgs[0]).iter()}
            self.assertTrue(tags <= {'svg', 'title', 'desc', 'rect', 'style', 'text', 'a', 'g'})

    def test_csv_separate_median_sd_no_inherited_plus_minus_values(self):
        b = view.build_observation_inspection([OLD_IDS[0], OLD_IDS[-1], *IDS])
        reader = csv.DictReader(io.StringIO(view.inspection_csv(b)))
        fields, rows = reader.fieldnames, list(reader)
        for early in ('essential_caveats', 'sd_unit_basis', 'sd_header_unit_explicit', 'si_sd_unit_basis'):
            for late in ('normalized_display', 'median_value', 'sd_value', 'si_sd_value'):
                self.assertLess(fields.index(early), fields.index(late))
        for row in rows:
            if row['record_id'] not in IDS:
                self.assertEqual(row['median_value'], 'null')
                self.assertEqual(row['sd_value'], 'null')
                self.assertNotEqual(row['plus_minus_value'], 'null')
                continue
            i = IDS.index(row['record_id'])
            for key in ('plus_minus_value', 'reported_plus_minus_string', 'si_plus_minus_value'):
                self.assertEqual(row[key], 'null')
            self.assertEqual(row['reported_median_string'], MEDIANS[i])
            self.assertEqual(row['reported_sd_string'], SD[i])
            self.assertEqual(row['si_median_value'], str(PA[i]))
            self.assertEqual(row['si_sd_value'], str(PA_SD[i]))
            self.assertEqual(row['uncertainty_notation'], 'separate_sd')
            self.assertEqual(row['sd_header_unit_explicit'], 'false')
            self.assertEqual(row['sd_unit_basis'], 'contextual_inference_from_associated_uts_column')
            self.assertEqual(row['si_sd_unit_basis'], 'conditional_on_contextual_MPa_inference')
            self.assertEqual(json.loads(row['record_snapshot_json']), self.bundle['record_snapshots'][i])
            for code in PAHT_CAVEATS:
                self.assertIn(PAHT_LABELS['en'][code], row['essential_caveats'])

    def test_closed_facet_mutations_fail_schema_and_every_renderer(self):
        mutations = [(('facets', 0, 'reported_median_string'), '58.910'),
            (('facets', 0, 'reported_sd_string'), '4.59'),
            (('facets', 0, 'summary_statistic'), 'mean'),
            (('facets', 0, 'uncertainty_notation'), 'plus_minus'),
            (('facets', 0, 'sd_unit_basis'), 'explicit_header'),
            (('facets', 0, 'sd_header_unit_explicit'), True),
            (('facets', 0, 'si_sd_unit_basis'), 'exact_reported_source_unit'),
            (('facets', 0, 'si_sd_value'), 3440001),
            (('facets', 0, 'normalization', 'sd_conversion_is_conditional'), False),
            (('facets', 0, 'normalized_display'), '58.91 ± 3.44 MPa'),
            (('facets', 0, 'source_cell', 'temperature_column'), '50'),
            (('facets', 0, 'temperature', 'value'), 50),
            (('facets', 0, 'required_caveat_codes'), ['pa12_sd_count_warning']),
            (('facets', 0, 'reported_plus_minus_string'), '3.44')]
        for path, value in mutations:
            b = deepcopy(self.bundle); set_path(b, path, value)
            with self.subTest(path=path):
                self.assertTrue(list(self.validator.iter_errors(b)))
                for renderer in (view.validate_observation_inspection, view.inspection_json,
                                 view.inspection_csv, view.render_observation_html, view.render_observation_svg):
                    with self.assertRaises(view.ObservationInspectionError):
                        renderer(b)

    def test_single_cell_alias_still_retains_warnings_and_exact_units(self):
        observation = deepcopy(self.bundle['record_snapshots'][0])
        observation['id'], observation['name'] = 'alias-paht-25c', '<PAHT & source>'
        observation['si_result']['value'] = float(observation['si_result']['value'])
        observation['si_result']['uncertainty_value'] = float(observation['si_result']['uncertainty_value'])
        candidate = {'schema_version': '1.3.0', 'records': [observation]}
        with catalogs(candidate):
            b = view.build_observation_inspection(['alias-paht-25c'])
            self.validator.validate(b)
            self.assertEqual(b['facets'][0]['si_sd_value'], 3440000)
            for language in LANGUAGES:
                html = view.render_observation_html(b, language)
                self.assertIn('&lt;PAHT &amp; source&gt;', html)
                visible = ParsedHTML(html).text
                for code in PAHT_CAVEATS:
                    self.assertIn(PAHT_LABELS[language][code], visible)

    def test_export_deterministic_and_invalid_selection_does_not_touch_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            variants = []
            for language in LANGUAGES:
                target = Path(tmp)/language
                view.export_observation_inspection(target, record_ids=[IDS[0]], lang=language)
                before = {p.name: p.read_bytes() for p in target.iterdir()}
                view.export_observation_inspection(target, record_ids=[IDS[0]], lang=language)
                self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
                variants.append((before['observation-inspection.json'], before['observation-inspection.csv']))
                with self.assertRaises(view.ObservationInspectionError):
                    view.export_observation_inspection(target, record_ids=[IDS[0]], lang='xx')
                self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
            self.assertTrue(all(variant == variants[0] for variant in variants))

    def test_prior_twelve_record_inspection_and_catalog_bytes_are_preserved(self):
        b = view.build_observation_inspection(list(OLD_IDS))
        old = deepcopy(b); old['engine_version'] = '0.23.0'
        # Facets, sources, scientific snapshots, grouping and policies all included.
        canonical = json.dumps(old, ensure_ascii=False)
        self.assertEqual(digest(canonical), OLD_OUTPUT_SHA256['bundle.json'])
        csv_text = view.inspection_csv(b).replace(b['engine_version'], '0.23.0')
        self.assertEqual(digest(csv_text), OLD_OUTPUT_SHA256['inspection.csv'])
        self.assertNotIn('reported_median_string', next(csv.reader(io.StringIO(csv_text))))
        c = read_catalog('observations'); by_id = {r['id']: r for r in c['records']}
        c['records'] = [by_id[rid] for rid in OLD_IDS]
        for language in LANGUAGES:
            outputs = {'html': view.render_observation_html(b, language),
                'svg': view.render_observation_svg(b, language),
                'narrow.svg': view.render_observation_svg(b, language, 380),
                'txt': render_catalog(c, 'observations', language)}
            for suffix, text in outputs.items():
                with self.subTest(language=language, suffix=suffix):
                    self.assertEqual(digest(text.replace(b['engine_version'], '0.23.0')),
                                     OLD_OUTPUT_SHA256[language + '.' + suffix])


if __name__ == '__main__':
    unittest.main()
