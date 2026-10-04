"""Source-cell admission, unchanged legacy bundles, and additive same-family growth."""
import copy
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
from viscoelastic_preservation import pre_viscoelastic_bytes
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from materials_boundaries import __version__, load_json
from materials_boundaries.catalog import query_catalog, read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.predictions import (
    DEFAULT_GROUP, PredictionError, canonical_json, prediction_labels,
    validate_prediction_catalog, value_evidence,
)
from materials_boundaries.prediction_visualization import (
    build_prediction_comparison, comparison_csv, comparison_json,
    render_prediction_html, render_prediction_svg, validate_prediction_comparison,
)
from scripts.validate_catalogs import load_catalogs, validate_catalogs

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = load_json(ROOT / 'tests/fixtures/nickel_six_source_transcription.json')
BASELINE = load_json(ROOT / 'tests/fixtures/pre_nickel_batch_v0210.json')
GROUP = FIXTURE['group_id']
SOURCE = FIXTURE['source_id']
PROTOCOL = FIXTURE['protocol_id']
LANGUAGES = ('en', 'zh', 'ja', 'de')
IDS = [cell['record_id'] for cell in FIXTURE['selected_cells']]


def digest(value):
    return sha256(canonical_json(value).encode()).hexdigest()


def neutral_digest(text):
    text = text.replace('v' + __version__, 'v<VERSION>')
    text = text.replace('"engine_version": "' + __version__ + '"',
                        '"engine_version": "<VERSION>"')
    text = text.replace('&quot;engine_version&quot;: &quot;' + __version__ + '&quot;',
                        '&quot;engine_version&quot;: &quot;<VERSION>&quot;')
    return sha256(text.encode()).hexdigest()


class NickelBatchSourceTests(unittest.TestCase):
    def test_exact_six_cells_labels_digits_and_model_compositions(self):
        expected_cells = [('Cr', '4.90', 4), ('Mn', '5.12', 5), ('Fe', '5.20', 6),
                          ('Cu', '4.51', 9), ('Si', '4.17', 2), ('Ti', '4.24', 2)]
        self.assertEqual([(c['solute_element'], c['source_value_string'],
                           c['source_cell']['column_from_left_in_described_row_1_based'])
                          for c in FIXTURE['selected_cells']], expected_cells)
        catalog = read_catalog('computational_predictions')
        validate_prediction_catalog(catalog)
        records = {r['id']: r for r in catalog['records']}
        group = next(g for g in catalog['comparison_groups'] if g['id'] == GROUP)
        self.assertEqual(group['record_ids'], IDS)
        self.assertEqual(len(group['record_ids']), 6)
        self.assertEqual([r['id'] for r in catalog['records'] if r['comparison_group_id'] == GROUP], IDS)
        self.assertEqual(len(set(IDS)), 6)
        for cell in FIXTURE['selected_cells']:
            record = records[cell['record_id']]
            symbol = cell['solute_element']
            with self.subTest(symbol=symbol):
                self.assertEqual(record['formula'], 'Ni11' + symbol)
                self.assertEqual(record['cell_composition'], 'Ni11' + symbol)
                self.assertEqual(record['stoichiometry_in_model_cell'], {'Ni': 11, symbol: 1})
                self.assertEqual(record['source_table_label'], cell['source_label_exact'])
                self.assertEqual(record['source_value_string'], cell['source_value_string'])
                self.assertEqual(record['value_GPa'], cell['value_GPa'])
                self.assertEqual(record['reported_decimal_places'], 2)
                self.assertEqual(record['source_id'], SOURCE)
                self.assertEqual(record['protocol_id'], PROTOCOL)
                self.assertEqual(record['source_table'], 'Table 2')
                self.assertEqual(record['source_pdf_page_1_based'], 27)
                evidence = value_evidence(record)
                self.assertIn(cell['source_cell']['row_description'], evidence['locator'])
                self.assertIn('column ' + str(cell['source_cell']['column_from_left_in_described_row_1_based']), evidence['locator'])
                self.assertIn('printed value ' + cell['source_value_string'] + ' GPa', evidence['locator'])
                self.assertEqual(evidence['url'], cell['source_cell']['url'])
                self.assertIn('no pv/sv suffix printed', evidence['locator'])
                self.assertFalse(cell['pseudopotential_label']['printed_suffix_present'])
                self.assertIsNone(cell['pseudopotential_label']['actual_PAW_dataset_identifier'])
                self.assertIsNone(cell['pseudopotential_label']['actual_valence_configuration'])
                self.assertTrue(cell['pseudopotential_label']['absence_does_not_establish_no_semicore_states'])
                self.assertTrue(cell['independent_visual_transcription_agrees'])
                for lang in LANGUAGES:
                    self.assertIn(record['formula'], record['names'][lang])
                    self.assertNotEqual(record['names'][lang], symbol)

    def test_published_method_only_unknown_states_and_no_error_bars(self):
        bundle = build_prediction_comparison(GROUP)
        group, protocol = bundle['group_snapshot'], bundle['protocol_snapshot']
        self.assertEqual(group['verification_level'], 'reported_method_only')
        for flag in ('unknown_conditions_equivalent', 'raw_inputs_audited', 'cross_study_comparison_allowed'):
            self.assertFalse(group[flag])
        self.assertIn('missing table suffix does not prove', group['qualifier'])
        self.assertIn('26 solute supercells', bundle['record_snapshots'][0]['evidence'][1]['locator'])
        self.assertEqual(protocol['geometry']['slip_plane_miller_indices'], [1, 1, 1])
        self.assertEqual(protocol['geometry']['slip_direction_indices'], [1, 1, -2])
        self.assertIn('1992', protocol['calculation']['exchange_correlation_reported'])
        self.assertNotIn('PBE', protocol['calculation']['exchange_correlation_reported'])
        for key in ('physical_temperature_K', 'pressure_GPa', 'magnetic_state', 'spin_polarization'):
            self.assertIsNone(protocol['state_fields'][key])
        self.assertEqual(protocol['numerical_controls']['strength_peak_convergence_reported_GPa'], 0.08)
        self.assertIsNone(bundle['uncertainty_bars'])
        self.assertIsNone(bundle['stress_strain_curve'])
        self.assertFalse(bundle['interpolation'])
        for record in bundle['record_snapshots']:
            self.assertIsNone(record['uncertainty_GPa'])
            self.assertFalse(record['universal_upper_bound'])
            self.assertFalse(record['commercial_alloy_grade'])
            self.assertFalse(record['verification']['raw_inputs_audited'])
            self.assertEqual(record['evidence_type'], 'published_computational_prediction')
        rows = list(csv.DictReader(io.StringIO(comparison_csv(bundle))))
        self.assertEqual([r['source_value_string'] for r in rows], [c['source_value_string'] for c in FIXTURE['selected_cells']])
        for row in rows:
            self.assertEqual(row['predicted_ideal_shear_strength_GPa'], row['source_value_string'])
            self.assertEqual(row['convergence_is_uncertainty'], 'false')
            for key in ('physical_temperature_K', 'pressure_GPa', 'magnetic_state'):
                self.assertEqual(row[key], 'not_verified')
            self.assertEqual(row['uncertainty_GPa'], 'not_established')

    def test_source_query_growth_is_visible_in_all_four_languages(self):
        source_query = query_catalog('predictions', source_id=SOURCE)
        old_ids = list(BASELINE['objects']['records'])
        old_ids = [identifier for identifier in old_ids if identifier.startswith('shimanek')]
        # Require the reviewed nine source records without freezing a growing
        # catalog to nine forever; extra source-matching contributions stay live.
        self.assertTrue(set(old_ids + IDS) <= {r['id'] for r in source_query['records']})
        self.assertEqual(len(old_ids), 3)
        for language in LANGUAGES:
            text = render_catalog(source_query, 'predictions', language)
            self.assertTrue(text.startswith(prediction_labels(language)['catalog'] + ': ' + str(len(source_query['records']))))
            for identifier in old_ids + IDS:
                self.assertEqual(text.count('\n' + identifier + '\n'), 1)
            for cell in FIXTURE['selected_cells']:
                record = next(r for r in source_query['records'] if r['id'] == cell['record_id'])
                self.assertIn(record['names'][language] + ': ' + cell['source_value_string'] + ' GPa', text)
                self.assertEqual(query_catalog('predictions', record_id=record['id'], query=record['names'][language])['records'], [record])
            self.assertIn(prediction_labels(language)['unknown_notice'], text)


class NickelBatchPreservationTests(unittest.TestCase):
    def test_every_original_prediction_object_and_output_is_exact(self):
        catalog = read_catalog('computational_predictions')
        for field, originals in BASELINE['objects'].items():
            actual = {value['id']: value for value in catalog[field]}
            for identifier, expected in originals.items():
                self.assertEqual(digest(actual[identifier]), expected, identifier)
        for group_id, outputs in BASELINE['outputs'].items():
            bundle = build_prediction_comparison(group_id)
            self.assertEqual(neutral_digest(comparison_json(bundle)), outputs['json'])
            self.assertEqual(neutral_digest(comparison_csv(bundle)), outputs['csv'])
            for lang in LANGUAGES:
                self.assertEqual(neutral_digest(render_prediction_html(bundle, lang=lang)), outputs['html_' + lang])
                for width in (360, 380, 1100, 1600):
                    self.assertEqual(neutral_digest(render_prediction_svg(bundle, lang=lang, width=width)), outputs[f'svg_{lang}_{width}'])
        self.assertEqual(DEFAULT_GROUP, 'shimanek_v2_table2_ni_al_co')
        self.assertEqual(len(build_prediction_comparison()['points']), 3)
        self.assertTrue(set(IDS).isdisjoint(p['record_id'] for p in build_prediction_comparison()['points']))

    def test_historical_test_change_is_narrow_and_original_golden_bytes_preserved(self):
        ledger = load_json(ROOT / 'tests/fixtures/nickel_test_updates_v0210.json')
        self.assertEqual(set(ledger['approved_test_updates']), {'tests/test_silicon_predictions.py'})
        for filename, change in ledger['approved_test_updates'].items():
            self.assertEqual(sha256(pre_viscoelastic_bytes(filename, (ROOT / filename).read_bytes())).hexdigest(), change['sha256'])
            self.assertNotEqual(change['previous_sha256'], change['sha256'])
            self.assertTrue(change['reason'])

    def test_new_group_is_ordered_explicitly_and_survives_same_family_append(self):
        catalogs = load_catalogs(ROOT / 'materials_boundaries/data')
        catalog = catalogs['computational_predictions']
        original = build_prediction_comparison(GROUP)
        # A separate same-source/same-protocol group proves appendability does
        # not rely on a fixed catalog size or on global record ordering.
        record = copy.deepcopy(next(r for r in catalog['records'] if r['id'] == IDS[0]))
        group = copy.deepcopy(next(g for g in catalog['comparison_groups'] if g['id'] == GROUP))
        record.update(id='synthetic_nickel_batch_append', comparison_group_id='synthetic_nickel_batch_group', name='SYNTHETIC batch plumbing only')
        record['names'] = {lang: 'SYNTHETIC Ni11Cr plumbing ' + lang for lang in LANGUAGES}
        group.update(id='synthetic_nickel_batch_group', record_ids=[record['id']])
        group['names'] = {lang: 'SYNTHETIC group ' + lang for lang in LANGUAGES}
        catalog['records'].append(record)
        catalog['comparison_groups'].append(group)
        for field in ('records', 'protocols', 'comparison_groups'):
            catalog[field].reverse()
        before = copy.deepcopy(catalogs)
        validate_catalogs(catalogs)
        self.assertEqual(catalogs, before)
        read = lambda name: copy.deepcopy(catalogs[name])
        with patch('materials_boundaries.predictions.read_catalog', side_effect=read), \
             patch('materials_boundaries.prediction_visualization.read_catalog', side_effect=read):
            self.assertEqual(build_prediction_comparison(GROUP), original)
            self.assertEqual([p['record_id'] for p in build_prediction_comparison(group['id'])['points']], [record['id']])
            self.assertIn(record['id'], [r['id'] for r in query_catalog('predictions', source_id=SOURCE)['records']])
        values = [p['value_GPa'] for p in original['points']]
        self.assertNotEqual(values, sorted(values))
        self.assertNotEqual(values, sorted(values, reverse=True))

    def test_new_record_and_group_mutations_still_fail_closed(self):
        original = read_catalog('computational_predictions')
        record = lambda c: next(r for r in c['records'] if r['id'] == IDS[0])
        group = lambda c: next(g for g in c['comparison_groups'] if g['id'] == GROUP)
        mutations = [lambda c: record(c).update(formula='Cr'),
                     lambda c: record(c).update(source_value_string='4.9'),
                     lambda c: record(c).update(uncertainty_GPa=.08),
                     lambda c: record(c).update(universal_upper_bound=True),
                     lambda c: record(c).update(source_table_label='Cr_pv'),
                     lambda c: record(c)['stoichiometry_in_model_cell'].update(Ni=10),
                     lambda c: group(c).update(unknown_conditions_equivalent=True),
                     lambda c: group(c)['record_ids'].append(group(c)['record_ids'][0]),
                     lambda c: group(c)['record_ids'].append(build_prediction_comparison()['points'][0]['record_id'])]
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                candidate = copy.deepcopy(original)
                mutation(candidate)
                with self.assertRaises(PredictionError):
                    validate_prediction_catalog(candidate)


class NickelBatchPresentationTests(unittest.TestCase):
    def test_four_language_wide_narrow_structure_digits_and_full_compositions(self):
        bundle = build_prediction_comparison(GROUP)
        for lang in LANGUAGES:
            for width in (360, 380, 1100, 1600):
                svg = render_prediction_svg(bundle, lang=lang, width=width)
                root = ET.fromstring(svg)
                ns = {'s': 'http://www.w3.org/2000/svg'}
                points = root.findall('.//s:circle', ns)
                self.assertEqual([p.attrib['data-record-id'] for p in points], IDS)
                for tag in ('path', 'polyline', 'polygon'):
                    self.assertEqual(root.findall('.//s:' + tag, ns), [])
                texts = [node.text for node in root.findall('.//s:text', ns)]
                for cell in FIXTURE['selected_cells']:
                    self.assertIn('Ni11' + cell['solute_element'], texts)
                    self.assertIn(cell['source_value_string'], texts)
                self.assertIn(prediction_labels(lang)['unknown_notice'], svg)
                self.assertIn(prediction_labels(lang)['comparison_notice'], svg)
            html = render_prediction_html(bundle, lang=lang)
            self.assertIn('lang="' + lang + '"', html)
            self.assertNotIn('[missing:', html)
            self.assertNotIn('<script', html)
            for cell in FIXTURE['selected_cells']:
                self.assertIn('<td>Ni11' + cell['solute_element'] + '</td>', html)
                self.assertIn(cell['source_value_string'] + ' GPa', html)
            self.assertIn('#page=27', html)
            self.assertIn('#page=5', html)

    def test_cli_group_selection_is_explicit_and_default_stays_original(self):
        with tempfile.TemporaryDirectory() as directory:
            for lang in LANGUAGES:
                target = Path(directory) / lang
                command = [sys.executable, '-m', 'materials_boundaries', 'prediction', 'plot',
                           '--group-id', GROUP, '--output', str(target), '--lang', lang]
                run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                bundle = load_json(target / 'prediction-comparison.json')
                self.assertEqual(bundle['group_id'], GROUP)
                self.assertEqual([p['record_id'] for p in bundle['points']], IDS)
                validate_prediction_comparison(bundle)
                self.assertTrue((target / ('prediction-comparison.' + lang + '.html')).is_file())
            target = Path(directory) / 'default'
            run = subprocess.run([sys.executable, '-m', 'materials_boundaries', 'prediction', 'plot',
                                  '--output', str(target)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(load_json(target / 'prediction-comparison.json')['group_id'], DEFAULT_GROUP)


if __name__ == '__main__':
    unittest.main()
