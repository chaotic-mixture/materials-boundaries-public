"""Nine reviewed fourth-batch facts, without material-specific runtime gates.

The fixture freezes selected source transcriptions, not all future catalog IDs.
Source-dependent semantic errors cannot be decided by a generic JSON schema;
explicit source-fact comparisons below keep those limits out of production code.
"""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import unittest

from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.cli import main
from materials_boundaries.material_references import validate_material_catalog, resolve_material

ROOT = Path(__file__).resolve().parents[1]
AZ91 = 'refprop_puga2015_az91d_as_cast_non_us_tensile_strength'
ZINC = 'refprop_kulczyk2022_zinc_annealed_tensile_strength'
AZ31 = 'refprop_chen2023_az31_as_extruded_tensile_strength'
MO = 'refprop_cezairliyan1970_molybdenum_tube_mass_density'
W = 'refprop_cezairliyan1971_tungsten_tube_mass_density'
FLAX = 'refprop_stochioiu2024_flax_technical_fiber_youngs_modulus'
HEMP = 'refprop_stochioiu2024_hemp_technical_fiber_youngs_modulus'
SILK = 'refprop_cheng2019_bombyx_mori_silk_strain932_control_tensile_strength'
WOOL = 'refprop_arbelaiz2024_latxa_wool_soap_cleaned_tensile_strength'
SELECTED = (AZ91, ZINC, AZ31, MO, W, FLAX, HEMP, SILK, WOOL)
NUMBERS = {AZ91: ('160', '160', 'MPa'), ZINC: ('60', '60', 'MPa'),
           AZ31: ('274', '274', 'MPa'), MO: ('10210', '10.21 × 10^3', 'kg/m^3'),
           W: ('19230', '19.23 × 10^3', 'kg/m^3'), FLAX: ('31.75', '31.75', 'GPa'),
           HEMP: ('22.63', '22.63', 'GPa'), SILK: ('332', '332', 'MPa'),
           WOOL: ('163', '163', 'MPa')}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def indexed(rows):
    return {row['id']: row for row in rows}


def assert_reviewed_subset(test, materials, properties, sources, fixture):
    """Keep exact reviewed facts while permitting genuinely new source facts."""
    props = indexed(properties['records'])
    states = indexed(materials['records'])
    identities = indexed(materials['identities'])
    for item in fixture['records']:
        test.assertEqual(props[item['property_id']], item['expected_property'])
        actual = deepcopy(states[item['state_id']])
        expected = deepcopy(item['expected_material_state'])
        # Additional independently reviewed properties can extend the same state.
        test.assertTrue(set(expected.pop('property_ids')).issubset(actual.pop('property_ids')))
        test.assertEqual(actual, expected)
        test.assertEqual(identities[item['identity_id']], item['expected_identity'])
    for expected in fixture['sources']:
        test.assertEqual(indexed(sources['records'])[expected['id']], expected)
    for expected in fixture['grades']:
        test.assertEqual(indexed(materials['grades'])[expected['id']], expected)


class FourthMaterialBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials = read_catalog('materials')
        cls.properties = read_catalog('reference_properties')
        cls.sources = read_catalog('sources')
        cls.props = indexed(cls.properties['records'])
        cls.states = indexed(cls.materials['records'])
        cls.identities = indexed(cls.materials['identities'])
        cls.fixture = json.loads((ROOT / 'tests/fixtures/fourth_batch_source_transcription_v0320.json').read_text())

    def test_nine_distinct_source_qualified_identities_with_nine_exact_values(self):
        validate_material_catalog(self.materials, self.properties, self.sources)
        identities, sources = set(), set()
        for key in SELECTED:
            p = self.props[key]
            state = self.states[p['material_state_id']]
            identities.add(state['identity_id']); sources.add(p['source_id'])
            self.assertIn(key, state['property_ids'])
            number, text, unit = NUMBERS[key]
            self.assertEqual((p['reported_value']['number'], p['reported_value']['value_text'],
                              p['reported_value']['unit_code']), (number, text, unit))
            self.assertEqual(p['reported_value']['kind'], 'scalar')
            self.assertEqual(p['evidence_kind'], 'published_experimental_reference')
            self.assertEqual(p['determination_basis'], 'source_reports_measurement')
            self.assertEqual(p['evaluation_support'], 'catalog_only')
            self.assertIs(p['universal_bound'], False)
            self.assertIs(p['engineering_allowable'], False)
            self.assertIs(p['verification']['independent_scientific_review'], False)
            self.assertIs(p['verification']['raw_data_reanalysis'], False)
        self.assertEqual(len(identities), 9)
        self.assertEqual(len(sources), 8)
        # The nine selected records constitute this batch, not a permanent cap.
        self.assertEqual({r['property_id'] for r in self.fixture['records']}, set(SELECTED))

    def test_existing_objects_remain_unchanged(self):
        catalogs = {'materials': self.materials, 'reference_properties': self.properties,
                    'sources': self.sources}
        for name, collections in self.fixture['baseline_sha256'].items():
            for collection, records in collections.items():
                actual = indexed(catalogs[name][collection])
                for record_id, digest in records.items():
                    self.assertEqual(hashlib.sha256(canonical(actual[record_id])).hexdigest(), digest)

    def test_full_reviewed_transcriptions_and_source_scopes_are_preserved(self):
        assert_reviewed_subset(self, self.materials, self.properties, self.sources, self.fixture)

    def test_legitimate_future_appends_do_not_fail_source_fixture_gate(self):
        materials = deepcopy(self.materials)
        properties = deepcopy(self.properties)
        sources = deepcopy(self.sources)
        # Synthetic new source fact for an existing state. This is only a test
        # fixture, not a real measurement or an admitted catalog contribution.
        future = deepcopy(self.props[AZ91])
        future['id'] = 'refprop_future_synthetic_test_only'
        future['reported_value'].update(number='161', value_text='161')
        future['evidence'][0]['locator'] = 'Synthetic future separate source result, Table 99, control row'
        properties['records'].append(future)
        st = indexed(materials['records'])[future['material_state_id']]
        st['property_ids'].append(future['id'])
        validate_material_catalog(materials, properties, sources)
        assert_reviewed_subset(self, materials, properties, sources, self.fixture)

    def test_az91_control_and_zinc_unknown_statistics_are_not_upgraded(self):
        a, z = self.props[AZ91], self.props[ZINC]
        self.assertEqual(a['summary_statistic'], 'reported_mean')
        self.assertEqual(a['sample_count']['value'], 10)
        self.assertIsNone(a['uncertainty'])
        self.assertEqual(a['uncertainty_status'], 'not_reported_in_inspected_source')
        self.assertIn('0.02 s^-1', a['conditions']['loading_rate']['text'])
        self.assertIn('without ultrasonic', self.states[a['material_state_id']]['state']['processing']['text'])
        self.assertEqual(z['summary_statistic'], 'not_stated')
        self.assertIsNone(z['sample_count']['value'])
        self.assertEqual(z['uncertainty']['type'], 'reported_plus_minus_unspecified')
        self.assertEqual(z['uncertainty']['number'], '6')
        self.assertIn('0.008 s^-1', z['conditions']['loading_rate']['text'])
        purity = self.states[z['material_state_id']]['state']['composition_or_purity']
        self.assertEqual(purity['text'], 'Zinc purity 99.9%')
        self.assertIn('percentage basis', purity['notes'])
        for p in (a, z, self.props[AZ31]):
            self.assertEqual(p['conditions']['temperature']['text'], 'Room temperature')
            self.assertIn('No numeric temperature', p['conditions']['temperature']['notes'])

    def test_az31_study_process_context_is_not_comparator_protocol_or_test_rate(self):
        p = self.props[AZ31]
        s = self.states[p['material_state_id']]
        self.assertEqual(s['name'], 'Unreinforced as-extruded AZ31 comparator')
        self.assertNotIn('sps', s['id'])
        self.assertEqual(s['state']['processing']['text'], 'Unreinforced as-extruded comparator')
        self.assertIn('study-process', self.identities[s['identity_id']]['identity_scope'])
        self.assertIn('not independently restated', s['state']['processing']['notes'])
        self.assertEqual(s['state']['temper_or_heat_treatment']['status'], 'not_reported_in_inspected_source')
        self.assertEqual(p['conditions']['loading_rate']['status'], 'not_reported_in_inspected_source')
        self.assertIn('6 mm/s', p['conditions']['loading_rate']['notes'])
        self.assertEqual(p['summary_statistic'], 'reported_mean')
        self.assertEqual(p['sample_count']['value'], 3)
        self.assertEqual(p['uncertainty']['type'], 'reported_plus_minus_unspecified')
        self.assertEqual(p['uncertainty']['number'], '4.9')
        self.assertIn('clean and legible', p['source_discrepancies'][0]['description'])

    def test_nbs_scientific_notation_and_independent_relative_measures_survive(self):
        mo, w = self.props[MO], self.props[W]
        self.assertEqual(mo['conditions']['temperature']['text'], '298 K')
        self.assertEqual(w['conditions']['temperature']['text'], '293 K')
        self.assertEqual(mo['conditions']['test_method']['text'], 'Water displacement in a pycnometer')
        self.assertEqual(w['conditions']['test_method']['status'], 'not_reported_in_inspected_source')
        self.assertIsNone(w['conditions']['test_method']['text'])
        self.assertEqual(mo['summary_statistic'], 'reported_mean')
        self.assertEqual(mo['sample_count']['value'], 4)
        self.assertIn('determinations', mo['sample_count']['scope'])
        self.assertIn('not asserted', mo['sample_count']['scope'])
        self.assertIsNone(w['sample_count']['value'])
        self.assertEqual(w['summary_statistic'], 'reported_value')
        self.assertIsNone(w['uncertainty'])
        measures = mo['uncertainty']['measures']
        self.assertEqual([(m['kind'], m['reported_value']['number'], m['qualifier']) for m in measures],
                         [('standard_error_of_mean', '0.02', 'not_qualified_in_source'),
                          ('estimated_inaccuracy', '0.1', 'approximately')])
        for measure in measures:
            self.assertEqual(measure['reported_value']['unit_code'], 'percent')
            self.assertEqual(measure['basis'], 'relative_to_reported_value')
            self.assertIsNone(measure['confidence_level']); self.assertIsNone(measure['coverage_factor'])
        for key, total in ((MO, '360 < Total < 560'), (W, '450 < Total < 740')):
            s = self.states[self.props[key]['material_state_id']]
            self.assertIn(total, s['state']['composition_or_purity']['text'])
            self.assertEqual(s['state']['temper_or_heat_treatment']['status'], 'not_reported_in_inspected_source')
            self.assertIn('purity', s['state']['composition_or_purity']['notes'])
            extras = {e['name']: e['fact'] for e in self.props[key]['conditions']['additional_conditions']}
            self.assertEqual(extras['pressure']['status'], 'not_reported_in_inspected_source')

    def test_flax_and_hemp_are_prepared_bundles_with_cv_and_exact_chord_method(self):
        for key, cv, supplier, year in ((FLAX, '56.12', 'Faltin', '2022'),
                                         (HEMP, '72.02', 'HempFlax', '2023')):
            p = self.props[key]; s = self.states[p['material_state_id']]
            identity = self.identities[s['identity_id']]
            self.assertEqual(identity['category'], 'composite')
            self.assertIn('natural lignocellulosic', identity['identity_scope'])
            self.assertIn(supplier, identity['identity_scope']); self.assertIn(year, identity['identity_scope'])
            self.assertEqual(p['summary_statistic'], 'reported_mean')
            self.assertEqual(p['sample_count']['value'], 25)
            m, = p['uncertainty']['measures']
            self.assertEqual(m['kind'], 'coefficient_of_variation')
            self.assertEqual(m['reported_value']['number'], cv)
            self.assertEqual(m['reported_value']['unit_code'], 'percent')
            window = p['method_definition']['extraction_window']
            self.assertEqual(window['text'], 'Chord Young’s modulus over 0.1–0.2% strain')
            self.assertIn('p.8', window['evidence'][0]['locator'])
            self.assertIn('Figure 6 p.7', window['evidence'][0]['locator'])
            self.assertIn('ignoring lumen', p['method_definition']['definition'])
            self.assertIn('slack-corrected', p['method_definition']['definition'])
            self.assertIn('No test-frame compliance', p['method_definition']['definition'])
            self.assertEqual(p['conditions']['temperature']['status'], 'not_reported_in_inspected_source')
            self.assertIn('C1557-03', p['source_discrepancies'][0]['description'])
            self.assertIn('2020', p['source_discrepancies'][0]['description'])

    def test_silk_graphical_sd_preserves_five_cocoons_and_no_digitization(self):
        p = self.props[SILK]; m, = p['uncertainty']['measures']
        self.assertEqual(p['summary_statistic'], 'reported_mean')
        self.assertEqual(p['sample_count']['value'], 30)
        self.assertIn('five chosen cocoons', p['sample_count']['scope'])
        self.assertEqual(m['kind'], 'standard_deviation')
        self.assertEqual(m['availability'], 'graphical_only')
        self.assertEqual(m['basis'], 'absolute')
        self.assertIsNone(m['reported_value'])
        self.assertIn('Figure 4b', m['evidence'][0]['locator'])
        self.assertIn('No numerical amplitude was transcribed or digitized', m['note'])
        extras = {e['name']: e['fact'] for e in p['conditions']['additional_conditions']}
        self.assertIn('intraspecific and intraindividual', extras['cocoon_sampling']['notes'])
        self.assertEqual(extras['cross_section_model']['status'], 'not_reported_in_inspected_source')
        self.assertEqual(p['conditions']['temperature']['text'], 'Ambient conditions')
        self.assertEqual(p['conditions']['loading_rate']['status'], 'not_reported_in_inspected_source')
        self.assertIn('ANOVA', p['source_discrepancies'][0]['description'])
        self.assertIn('t-test', p['source_discrepancies'][0]['description'])

    def test_wool_sd_does_not_establish_mean_or_transfer_composite_conditions(self):
        p = self.props[WOOL]; m, = p['uncertainty']['measures']
        self.assertEqual(p['summary_statistic'], 'not_stated')
        self.assertEqual(m['kind'], 'standard_deviation')
        self.assertEqual(m['availability'], 'numeric_reported')
        self.assertEqual(m['reported_value']['number'], '23')
        self.assertEqual(m['reported_value']['unit_code'], 'MPa')
        self.assertIn('central strength aggregation is not stated', m['note'])
        self.assertEqual(p['sample_count']['value'], 15)
        self.assertEqual(p['conditions']['temperature']['status'], 'not_reported_in_inspected_source')
        self.assertEqual(p['conditions']['loading_rate']['text'], '1 mm/min')
        self.assertEqual(p['conditions']['test_standard']['status'], 'not_reported_in_inspected_source')
        self.assertIn('ASTM D638-10', p['conditions']['test_standard']['notes'])
        self.assertIn('cylindrical', p['method_definition']['definition'])
        s = self.states[p['material_state_id']]
        self.assertIn('55 °C', s['state']['processing']['text'])
        self.assertIn('not tensile-test temperature', s['state']['processing']['notes'])
        self.assertEqual(self.identities[s['identity_id']]['category'], 'polymer')
        self.assertIn('lanolin', s['source_scope'])

    def test_sources_keep_recorded_pdf_identity_and_six_cc_two_nbs_rights(self):
        sources = indexed(self.sources['records'])
        selected = {self.props[k]['source_id'] for k in SELECTED}
        cc, nbs = [], []
        for sid in selected:
            s = sources[sid]
            self.assertTrue(s['authors']); self.assertTrue(s['title']); self.assertTrue(s['doi'])
            self.assertIn('no_source_assets', s['bundled_content'])
            self.assertNotIn('/workspace/', json.dumps(s))
            if s['license']['identifier'] == 'CC-BY-4.0': cc.append(sid)
            else:
                nbs.append(sid)
                notes = ' '.join(s['claim_notes'])
                self.assertIn('Republished courtesy of the National Institute of Standards and Technology.', notes)
                self.assertIn('not CC licensing or Standard Reference Database permission', notes)
        self.assertEqual(len(cc), 6); self.assertEqual(len(nbs), 2)
        for key in SELECTED:
            p = self.props[key]; d = p['source_document']
            self.assertEqual(d['hash_status'], 'recorded')
            self.assertRegex(d['sha256'], r'^[0-9a-f]{64}$')
            self.assertIn(d['url'], sources[p['source_id']]['urls'])
            self.assertIn(d['sha256'], ' '.join(sources[p['source_id']]['claim_notes']))
        self.assertIn('independent review', ' '.join(sources[self.props[ZINC]['source_id']]['claim_notes']))

    def test_four_language_names_and_cli_keep_source_precision_and_semantics(self):
        for key in SELECTED:
            p = self.props[key]; state = self.states[p['material_state_id']]
            identity = self.identities[state['identity_id']]
            self.assertEqual(set(identity['names']), {'en', 'zh', 'ja', 'de'})
            self.assertEqual(set(state['names']), {'en', 'zh', 'ja', 'de'})
            for lang in ('en', 'zh', 'ja', 'de'):
                selected = query_catalog('reference-properties', record_id=key)
                text = render_catalog(selected, 'reference-properties', lang)
                self.assertIn(p['reported_value']['value_text'], text)
                self.assertIn(p['uncertainty_note'], text)
                self.assertIn(p['sample_count']['scope'], text)
                for flag in ('--text', '--json'):
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        code = main(['catalog', 'reference-properties', '--id', key, flag, '--lang', lang])
                    self.assertEqual(code, 0)
                    if flag == '--json': self.assertEqual(json.loads(stdout.getvalue()), selected)
                    else: self.assertEqual(stdout.getvalue().rstrip('\n'), text)

    def test_source_conditioned_negative_mutations_reject_unsupported_interpretations(self):
        cases = [
            (AZ91, lambda p: p['sample_count'].update(value=5)),
            (AZ91, lambda p: p['conditions']['temperature'].update(text='23 °C')),
            (ZINC, lambda p: p.update(summary_statistic='reported_mean')),
            (ZINC, lambda p: p['uncertainty'].update(type='reported_standard_deviation')),
            (ZINC, lambda p: p['conditions']['loading_rate'].update(text='0 s^-1')),
            (AZ31, lambda p: p['conditions']['loading_rate'].update(status='reported', text='6 mm/s')),
            (AZ31, lambda p: p['uncertainty'].update(type='reported_standard_deviation')),
            (MO, lambda p: p['sample_count'].update(scope='Four independent specimens')),
            (MO, lambda p: p['uncertainty']['measures'][0].update(kind='standard_deviation')),
            (MO, lambda p: p['uncertainty']['measures'][1].update(qualifier='not_qualified_in_source')),
            (MO, lambda p: p['uncertainty']['measures'].pop()),
            (MO, lambda p: p['reported_value'].update(value_text='10210')),
            (W, lambda p: p['conditions']['temperature'].update(text='298 K')),
            (W, lambda p: p['conditions']['test_method'].update(status='reported', text='Water displacement in a pycnometer')),
            (W, lambda p: p['reported_value'].update(value_text='19230')),
            (FLAX, lambda p: p['uncertainty']['measures'][0].update(kind='standard_deviation')),
            (HEMP, lambda p: p['method_definition']['extraction_window'].update(text='Chord modulus over 0.1–0.2 strain')),
            (SILK, lambda p: p['sample_count'].update(scope='Thirty independent cocoons')),
            (SILK, lambda p: p['uncertainty']['measures'][0].update(reported_value={'number': '0', 'value_text': '0', 'unit_code': 'MPa', 'unit_text': 'MPa'})),
            (SILK, lambda p: p.update(uncertainty=None, uncertainty_status='not_reported_in_inspected_source')),
            (WOOL, lambda p: p.update(summary_statistic='reported_mean')),
            (WOOL, lambda p: p['conditions']['temperature'].update(status='reported', text='55 °C')),
            (WOOL, lambda p: p['conditions']['test_standard'].update(status='reported', text='ASTM D638-10')),
        ]
        for key, mutate in cases:
            changed = deepcopy(self.properties)
            mutate(indexed(changed['records'])[key])
            with self.subTest(property=key, mutation=mutate), self.assertRaises(AssertionError):
                assert_reviewed_subset(self, self.materials, changed, self.sources, self.fixture)
        # Composition/processing errors are source-conditioned too; these do
        # not turn into generic production bans on material names or values.
        for key, field, text in ((AZ31, 'processing', 'AZ31-specific SPS protocol independently verified'),
                                 (MO, 'composition_or_purity', 'Certified 99.99% pure molybdenum'),
                                 (W, 'temper_or_heat_treatment', 'Density measured after annealing'),
                                 (WOOL, 'conditioning', 'Dried at 100 °C for 12 h before fiber test')):
            changed = deepcopy(self.materials)
            indexed(changed['records'])[self.props[key]['material_state_id']]['state'][field].update(status='reported', text=text)
            with self.subTest(property=key, field=field), self.assertRaises(AssertionError):
                assert_reviewed_subset(self, changed, self.properties, self.sources, self.fixture)

    def test_selected_evidence_stays_registered_and_bound_to_the_inspected_document(self):
        for key in SELECTED:
            for mutation in ('unknown_source', 'wrong_document', 'missing_primary_method'):
                altered = deepcopy(self.properties)
                p = indexed(altered['records'])[key]
                if mutation == 'unknown_source': p['evidence'][0]['source_id'] = 'unknown_fourth_batch_source'
                elif mutation == 'wrong_document': p['source_document']['url'] = 'https://example.invalid/wrong.pdf'
                else: p['method_definition']['evidence'] = []
                with self.subTest(property=key, mutation=mutation), self.assertRaises(ValueError):
                    validate_material_catalog(self.materials, altered, self.sources)
        for key in (MO, FLAX, HEMP, SILK, WOOL):
            altered = deepcopy(self.properties)
            p = indexed(altered['records'])[key]
            p['uncertainty']['measures'][0]['evidence'][0]['locator'] = 'Different unsupported Table 99'
            with self.assertRaises(ValueError):
                validate_material_catalog(self.materials, altered, self.sources)


if __name__ == '__main__':
    unittest.main()
