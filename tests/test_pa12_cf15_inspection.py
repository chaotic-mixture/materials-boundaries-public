"""Pressure-valued source-cell inspection; no temperature model or comparison."""
from copy import deepcopy
import csv
from html import escape
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from materials_boundaries import observation_visualization as view
from materials_boundaries.catalog import read_catalog
from materials_boundaries._observation_inspection_labels import LABELS
from materials_boundaries._pa12_cf15_observation_contract import PA12_FAMILY, PA12_SOURCE, PA12_QUANTITY
from test_observation_inspection import (IDS as OLD_IDS, DISPLAYS as OLD_DISPLAYS,
    LANGUAGES, SVG_NS, ParsedHTML, catalogs, compact, html_article, svg_card, set_path)

ROOT = Path(__file__).resolve().parents[1]
TEMPERATURES = ('23', '40', '60', '80', '100', '120')
IDS = tuple('ciganas2026-pa12cf15-uts-' + value + 'c' for value in TEMPERATURES)
CENTRAL = ('49.07', '40.31', '32.70', '26.60', '22.78', '18.68')
SD = ('0.88', '0.72', '1.18', '1.15', '0.97', '0.91')
PA = (49070000, 40310000, 32700000, 26600000, 22780000, 18680000)
PA_SD = (880000, 720000, 1180000, 1150000, 970000, 910000)


class PA12InspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observations = read_catalog('observations')
        cls.sources = read_catalog('sources')
        cls.bundle = view.build_observation_inspection(source_id=PA12_SOURCE)
        schemas = [json.loads((ROOT/'schemas'/name).read_text()) for name in
                   ('observation-inspection.schema.json', 'observations.schema.json', 'sources.schema.json')]
        registry = Registry().with_resources((s['$id'], Resource.from_contents(s)) for s in schemas)
        Draft202012Validator.check_schema(schemas[0])
        cls.validator = Draft202012Validator(schemas[0], registry=registry, format_checker=FormatChecker())

    def test_default_mixed_subsets_reverse_ids_and_both_groupings(self):
        b = view.build_observation_inspection()
        self.assertEqual(b['selection']['resolved_record_ids'], [r['id'] for r in read_catalog('observations')['records']])
        self.assertEqual(b['schema_version'], '1.1.0')
        self.assertEqual(b['catalog_schema_versions'], {'observations': '1.3.0', 'sources': '1.0.0'})
        old_displays = dict(zip(OLD_IDS, OLD_DISPLAYS))
        self.assertEqual({f['record_id']: f['normalized_display'] for f in b['facets'] if f['record_id'] in OLD_IDS}, old_displays)
        for grouping in ('study', 'quantity'):
            for requested in (list(reversed(IDS)), [IDS[2]], [IDS[5], OLD_IDS[0], IDS[0]]):
                with self.subTest(grouping=grouping, requested=requested):
                    subset = view.build_observation_inspection(requested, group_by=grouping)
                    expected = [r['id'] for r in read_catalog('observations')['records'] if r['id'] in requested]
                    self.assertEqual(subset['selection']['resolved_record_ids'], expected)
                    self.validator.validate(subset)
            self.validator.validate(view.build_observation_inspection(group_by=grouping))
        self.assertEqual(view.build_observation_inspection(quantity=PA12_QUANTITY)['facets'], self.bundle['facets'])
        with self.assertRaises(view.ObservationInspectionError):
            view.build_observation_inspection([OLD_IDS[0]], source_id=PA12_SOURCE)

    def test_six_exact_reported_strings_and_separate_si_facets(self):
        for position, facet in enumerate(self.bundle['facets']):
            index = IDS.index(facet['record_id'])
            with self.subTest(temperature=TEMPERATURES[index]):
                self.assertEqual(facet['record_id'], IDS[index])
                self.assertEqual(facet['temperature']['value_string'], TEMPERATURES[index])
                self.assertEqual(facet['temperature']['unit'], 'degC')
                self.assertEqual(facet['temperature_basis'], 'reported_chamber_test_condition')
                self.assertEqual(facet['quantity_dimension'], 'pressure')
                self.assertEqual(facet['unit'], 'MPa')
                self.assertEqual(facet['si_unit'], 'Pa')
                self.assertEqual(facet['normalized_display'], CENTRAL[index] + ' ± ' + SD[index] + ' MPa')
                self.assertEqual(facet['reported_value_string'], CENTRAL[index])
                self.assertEqual(facet['reported_plus_minus_string'], SD[index])
                self.assertEqual(facet['si_value'], PA[index])
                self.assertEqual(facet['si_uncertainty_value'], PA_SD[index])
                self.assertEqual(facet['si_display'], str(PA[index]) + ' ± ' + str(PA_SD[index]) + ' Pa')
                self.assertEqual(facet['normalization'], self.bundle['record_snapshots'][position]['si_result']['normalization'])
                self.assertEqual(facet['uncertainty_type'], 'reported_standard_deviation')
                self.assertEqual(facet['observation_type'], 'experiment_derived_tensile_test_summary')
        self.validator.validate(self.bundle)

    def test_warnings_identity_and_temperature_precede_values_in_every_locale_and_layout(self):
        for lang in LANGUAGES:
            t = LABELS[lang]
            html = view.render_observation_html(self.bundle, lang)
            svgs = [view.render_observation_svg(self.bundle, lang, width) for width in (380, 1100)]
            for facet in self.bundle['facets']:
                index = IDS.index(facet['record_id'])
                texts = [html_article(html, IDS[index])] + [svg_card(svg, IDS[index]) for svg in svgs]
                for text in texts:
                    text = compact(text)
                    result = text.index(compact(facet['normalized_display']))
                    si = text.index(compact(facet['si_display']))
                    self.assertLess(result, si)
                    for value in (t['pa12_identity'], t['pa12_classification'],
                                  facet['dataset_id'], facet['protocol_id'],
                                  t['pa12_temperature'] + ': ' + TEMPERATURES[index] + ' °C',
                                  t['pa12_temperature_basis'],
                                  *(t[code] for code in facet['required_caveat_codes'])):
                        self.assertLess(text.index(compact(value)), result, (lang, IDS[index], value))
                    for forbidden in ('normalized_notice', 'original_context', 'classification', 'stiffness', 'strength'):
                        self.assertNotIn(compact(t[forbidden]), text)
                    for required in ('pa12_version_warning', 'pa12_rights_warning', 'pa12_standard_warning'):
                        self.assertIn(compact(t[required]), text)
                    self.assertNotIn('[missing:', text)
            # No quantitative geometry or executable/automatic external resources.
            tags = {node.tag.rsplit('}', 1)[-1] for node in ET.fromstring(svgs[0]).iter()}
            self.assertTrue(tags <= {'svg', 'title', 'desc', 'rect', 'style', 'text', 'a', 'g'})
            parsed = ParsedHTML(html)
            self.assertFalse(any(tag in ('script', 'img', 'iframe', 'object') for tag, _ in parsed.tags))
            urls = [attrs['href'] for tag, attrs in parsed.tags if tag == 'a']
            self.assertIn('https://creativecommons.org/licenses/by/4.0/', urls)
            self.assertFalse(any('iso.org' in url for url in urls))

    def test_single_temperature_repeats_essential_context(self):
        b = view.build_observation_inspection([IDS[2]])
        for lang in LANGUAGES:
            article = html_article(view.render_observation_html(b, lang), IDS[2])
            self.assertIn('60 °C', article)
            for code in view.PA12_CAVEATS:
                self.assertIn(LABELS[lang][code], article)
            self.assertIn('32.70 ± 1.18 MPa', article)
            self.assertIn('32700000 ± 1180000 Pa', article)

    def test_csv_explicit_units_temperature_nulls_and_original_snapshots(self):
        b = view.build_observation_inspection(list(OLD_IDS + IDS))
        reader = csv.DictReader(io.StringIO(view.inspection_csv(b)))
        columns, rows = reader.fieldnames, list(reader)
        for early in ('dataset_id', 'protocol_id', 'source_cell_json', 'temperature_value',
                      'temperature_value_string', 'temperature_unit', 'temperature_basis',
                      'temperature_json', 'essential_caveats', 'required_caveat_codes_json'):
            for late in ('normalized_display', 'central_value', 'plus_minus_value',
                         'reported_value_string', 'reported_plus_minus_string',
                         'si_central_value', 'si_plus_minus_value'):
                self.assertLess(columns.index(early), columns.index(late))
        for i, row in enumerate(rows):
            self.assertEqual(json.loads(row['record_snapshot_json']), b['record_snapshots'][i])
            if row['record_id'] in OLD_IDS:
                self.assertEqual(row['unit'], 'N/m')
                self.assertEqual(row['si_unit'], 'N/m')
                self.assertEqual(row['si_central_value'], row['central_value'])
                self.assertEqual(row['si_plus_minus_value'], row['plus_minus_value'])
                self.assertEqual(json.loads(row['normalization_json'])['kind'], 'identity_no_unit_conversion')
                for key in ('dataset_id', 'protocol_id', 'source_cell_json', 'temperature_value',
                            'temperature_value_string', 'temperature_unit', 'temperature_basis',
                            'temperature_json', 'reported_value_string', 'reported_plus_minus_string'):
                    self.assertEqual(row[key], 'null')
            else:
                j = IDS.index(row['record_id'])
                self.assertEqual(row['unit'], 'MPa')
                self.assertEqual(row['si_unit'], 'Pa')
                self.assertEqual(row['reported_value_string'], CENTRAL[j])
                self.assertEqual(row['reported_plus_minus_string'], SD[j])
                self.assertEqual(row['temperature_value_string'], TEMPERATURES[j])
                self.assertEqual(row['temperature_basis'], 'reported_chamber_test_condition')
                self.assertEqual(row['si_central_value'], str(PA[j]))
                self.assertEqual(row['si_plus_minus_value'], str(PA_SD[j]))
                self.assertEqual(json.loads(row['normalization_json'])['factor_string'], '1000000')

    def test_new_facets_are_closed_source_cells_not_cartesian_combinations(self):
        mutations = [(('facets', 0, 'unit'), 'N/m'), (('facets', 0, 'si_unit'), 'MPa'),
            (('facets', 0, 'quantity'), 'breaking_strength_2d'),
            (('facets', 0, 'method_family'), 'lee_2008_legacy_indentation_v1'),
            (('facets', 0, 'normalized_display'), '32.70 ± 1.18 MPa'),
            (('facets', 0, 'reported_value_string'), '49.070'),
            (('facets', 0, 'si_value'), 49070001),
            (('facets', 0, 'normalization', 'factor_string'), '1e6'),
            (('facets', 0, 'source_cell', 'temperature_column'), '40'),
            (('facets', 0, 'temperature', 'value'), 40),
            (('facets', 0, 'temperature_basis'), 'measured_specimen_temperature'),
            (('facets', 0, 'required_caveat_codes'), ['graphene_warning'])]
        for path, value in mutations:
            changed = deepcopy(self.bundle); set_path(changed, path, value)
            with self.subTest(path=path):
                self.assertTrue(list(self.validator.iter_errors(changed)))
                with self.assertRaises(view.ObservationInspectionError):
                    view.validate_observation_inspection(changed)
        changed = deepcopy(self.bundle); changed['facets'][0]['interpolation'] = True
        self.assertTrue(list(self.validator.iter_errors(changed)))
        # The legacy branch cannot accept a new quantity merely through enum growth.
        changed = view.build_observation_inspection([OLD_IDS[0]])
        changed['facets'][0]['quantity'] = PA12_QUANTITY
        self.assertTrue(list(self.validator.iter_errors(changed)))

    def test_all_derived_fields_and_snapshots_rebuild_fail_closed(self):
        mutations = [(('schema_version',), '1.0.0'),
            (('catalog_schema_versions', 'observations'), '1.2.0'),
            (('facets', 0, 'si_display'), '49070000.0 ± 880000.0 Pa'),
            (('facets', 0, 'temperature', 'control_description'), 'direct specimen temperature'),
            (('record_snapshots', 0, 'conditions', 'humidity', 'specimen_moisture_content'), 0),
            (('source_snapshots', 0, 'doi'), '10.0000/changed'),
            (('record_digests', 0, 'sha256'), '0' * 64),
            (('source_digests', 0, 'sha256'), '0' * 64),
            (('selection', 'resolved_record_ids'), list(reversed(self.bundle['selection']['resolved_record_ids']))),
            (('presentation_policy', 'quantitative_axes_allowed'), True)]
        for path, value in mutations:
            changed = deepcopy(self.bundle); set_path(changed, path, value)
            for fn in (view.validate_observation_inspection, view.inspection_json,
                       view.inspection_csv, view.render_observation_html, view.render_observation_svg):
                with self.subTest(path=path, output=fn.__name__):
                    with self.assertRaises(view.ObservationInspectionError):
                        fn(changed)

    def test_unknown_families_never_inherit_graphene_caveats(self):
        r = deepcopy(self.bundle['record_snapshots'][0]); r['method_family'] = 'unknown_family'
        with self.assertRaises(view.ObservationInspectionError):
            view._caveats(r)

    def test_source_mutations_rejected_on_inspection_even_when_reader_mocked(self):
        for key, value in (('doi', '10.0000/changed'), ('title', 'Other article')):
            changed = deepcopy(self.sources)
            source = next(s for s in changed['records'] if s['id'] == PA12_SOURCE)
            source[key] = value
            with self.subTest(key=key), catalogs(sources=changed):
                with self.assertRaises(view.ObservationInspectionError):
                    view.build_observation_inspection([IDS[0]])

    def test_alias_subset_and_integral_float_representation_preserve_science(self):
        changed = deepcopy(self.observations)
        original = deepcopy(next(r for r in self.bundle['record_snapshots'] if r['id'] == IDS[0]))
        original['id'] = 'renamed-23c'; original['name'] = '<PA12 & inspection>'
        original['si_result']['value'] = float(original['si_result']['value'])
        original['si_result']['uncertainty_value'] = float(original['si_result']['uncertainty_value'])
        original['conditions']['temperature']['value'] = 23.0
        original['conditions']['temperature']['stabilization_duration_min'] = 30.0
        changed['records'] = [original]
        with catalogs(changed):
            b = view.build_observation_inspection(['renamed-23c'])
            self.validator.validate(b)
            self.assertEqual(b['facets'][0]['si_display'], '49070000 ± 880000 Pa')
            row = next(csv.DictReader(io.StringIO(view.inspection_csv(b))))
            self.assertEqual(row['si_central_value'], '49070000')
            self.assertEqual(row['temperature_value'], '23')
            html = view.render_observation_html(b)
            self.assertIn('&lt;PA12 &amp; inspection&gt;', html)
            self.assertNotIn('<PA12 & inspection>', html)

    def test_invalid_export_preserves_absent_and_existing_targets(self):
        invalid = ({'lang': 'xx'}, {'record_ids': ['absent']}, {'quantity': 'temperature_law'},
                   {'record_ids': [IDS[0], IDS[0]]}, {'group_by': 'temperature'})
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'output'
            for kwargs in invalid:
                with self.subTest(kwargs=kwargs), self.assertRaises(view.ObservationInspectionError):
                    view.export_observation_inspection(target, **kwargs)
                self.assertFalse(target.exists())
            target.mkdir(); (target/'observation-inspection.json').write_text('sentinel')
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            for kwargs in invalid:
                with self.assertRaises(view.ObservationInspectionError):
                    view.export_observation_inspection(target, **kwargs)
                self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
            changed = deepcopy(self.observations)
            next(r for r in changed['records'] if r['id'] == IDS[0])['conditions']['temperature']['basis'] = 'measured'
            with catalogs(changed), self.assertRaises(view.ObservationInspectionError):
                view.export_observation_inspection(target)
            self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)

    def test_export_deterministic_data_across_four_languages(self):
        variants = []
        with tempfile.TemporaryDirectory() as tmp:
            for lang in LANGUAGES:
                target = Path(tmp)/lang
                view.export_observation_inspection(target, record_ids=[IDS[2]], lang=lang)
                before = {p.name: p.read_bytes() for p in target.iterdir()}
                view.export_observation_inspection(target, record_ids=[IDS[2]], lang=lang)
                self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
                variants.append((before['observation-inspection.json'], before['observation-inspection.csv']))
            self.assertTrue(all(value == variants[0] for value in variants))


if __name__ == '__main__':
    unittest.main()
