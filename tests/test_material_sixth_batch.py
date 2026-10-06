"""Selected original-PDF facts, especially unknown statistics and state scope."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from materials_boundaries.catalog import read_catalog
from materials_boundaries.material_references import validate_material_catalog
from test_material_porous_outputs import snapshot_case, digest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FIXTURE_SHA256 = '9eef32526414bf61b76dfba562c4bdfb7ff6f877751e7f14c7114944f665ed51'
FACTS = {
    'ewurum2025_biopbs': ('youngs_modulus', '575', 'MPa', '65', 'reported_mean', 'reported_standard_deviation', 10, 'exact'),
    'ewurum2025_pbs_lignin20': ('youngs_modulus', '960', 'MPa', '77', 'reported_mean', 'reported_standard_deviation', 10, 'exact'),
    'ewurum2025_indulin_at': ('mass_density', '1.226', 'g/cm^3', None, 'reported_value', 'not_reported_in_inspected_source', None, 'not_reported'),
    'abbasi2022_manure_phbv39': ('youngs_modulus', '0.87', 'GPa', '0.04', 'reported_mean', 'reported_standard_deviation', 5, 'at_least'),
    'mtibe2022_pbat_ecoflex_c1200': ('tensile_modulus', '52.01', 'MPa', '28.78', 'reported_value', 'reported_plus_minus_unspecified', 5, 'exact'),
    'mtibe2022_pbs_pbat_70_30': ('tensile_modulus', '253.49', 'MPa', '13.40', 'reported_value', 'reported_plus_minus_unspecified', 5, 'exact'),
}


def assert_source_facts(test, properties):
    index = {p['id']: p for p in properties['records']}
    for suffix, expected in FACTS.items():
        p = index['refprop_' + suffix + '_' + expected[0]]
        test.assertEqual((p['quantity'], p['reported_value']['number'], p['reported_value']['unit_code'],
                          (p['uncertainty'] or {}).get('number'), p['summary_statistic'], p['uncertainty_status'],
                          p['sample_count']['value'], p['sample_count']['relation']), expected)
        test.assertEqual(p['reported_value']['value_text'], expected[1])
        if p['uncertainty']:
            test.assertEqual(p['uncertainty']['value_text'], expected[3])
            test.assertEqual(p['uncertainty']['type'], expected[5])
            test.assertIsNone(p['uncertainty']['confidence_level'])
            test.assertIsNone(p['uncertainty']['coverage_factor'])
        test.assertEqual(p['evaluation_support'], 'catalog_only')
        for flag in ('universal_bound', 'engineering_allowable'):
            test.assertIs(p[flag], False)
        for flag in ('independent_scientific_review', 'raw_data_reanalysis'):
            test.assertIs(p['verification'][flag], False)


class SixthMaterialBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials = read_catalog('materials')
        cls.properties = read_catalog('reference_properties')
        cls.sources = read_catalog('sources')
        cls.states = {r['id']: r for r in cls.materials['records']}
        cls.props = {r['id']: r for r in cls.properties['records']}

    def prop(self, suffix):
        return self.props['refprop_' + suffix + '_' + FACTS[suffix][0]]

    def state(self, suffix):
        return self.states['state_' + suffix]

    def test_six_original_values_statistics_and_scope(self):
        validate_material_catalog(self.materials, self.properties, self.sources)
        assert_source_facts(self, self.properties)
        self.assertEqual(len({self.prop(s)['source_id'] for s in FACTS}), 3)
        for suffix in FACTS:
            self.assertEqual(self.state(suffix)['identity_id'], 'mat_' + suffix)
            self.assertIn(self.prop(suffix)['id'], self.state(suffix)['property_ids'])
            self.assertIsNone(self.prop(suffix)['method_definition']['extraction_window'])

    def test_plausible_but_unsupported_statistical_upgrades_fail_source_guard(self):
        for suffix, field, value in [
            ('abbasi2022_manure_phbv39', 'relation', 'exact'),
            ('ewurum2025_indulin_at', 'value', 2),
            ('mtibe2022_pbat_ecoflex_c1200', 'summary_statistic', 'reported_mean'),
            ('mtibe2022_pbs_pbat_70_30', 'uncertainty_status', 'reported_standard_deviation'),
        ]:
            with self.subTest(suffix=suffix, field=field):
                altered = deepcopy(self.properties)
                p = next(r for r in altered['records'] if r['id'] == self.prop(suffix)['id'])
                if field in ('relation', 'value'):
                    p['sample_count'][field] = value
                else:
                    p[field] = value
                with self.assertRaises(AssertionError):
                    assert_source_facts(self, altered)

    def test_identity_and_grade_ambiguity_is_not_resolved_by_invention(self):
        for suffix in FACTS:
            expected = 'grade_mtibe2022_ecoflex_c1200' if suffix == 'mtibe2022_pbat_ecoflex_c1200' else None
            self.assertEqual(self.state(suffix)['grade_id'], expected)
        for suffix in ('ewurum2025_biopbs', 'ewurum2025_pbs_lignin20'):
            p = self.prop(suffix)
            self.assertIn('FZ91PM/FZ91PB', json.dumps(p['source_discrepancies']))
            self.assertEqual(p['conditions']['temperature']['status'], 'not_reported_in_inspected_source')
            self.assertIn('Acetone/DCP', self.state(suffix)['state']['processing']['notes'])
        blend = self.state('mtibe2022_pbs_pbat_70_30')
        self.assertIn('ratio basis unspecified', blend['state']['composition_or_purity']['text'])
        self.assertIn('do not relabel 70/30 as wt/wt', blend['source_scope'])

    def test_phbv_force_ramp_composition_and_operational_day_are_separate(self):
        suffix = 'abbasi2022_manure_phbv39'
        self.assertIn('3 N/min', self.prop(suffix)['conditions']['loading_rate']['text'])
        self.assertIn('numerical setpoint not reported', self.prop(suffix)['conditions']['temperature']['text'])
        composition = self.state(suffix)['state']['composition_or_purity']
        for token in ('88.5 ± 4.7%', '0.21 ± 0.01'):
            self.assertIn(token, composition['text'])
        self.assertIn('do not transfer the mechanical Table 9 SD footnote', composition['notes'])
        self.assertIn('operational day', self.state(suffix)['source_scope'])

    def test_density_unknowns_and_pbat_known_test_temperature(self):
        p = self.prop('ewurum2025_indulin_at')
        self.assertEqual(p['density_basis'], 'not_stated')
        self.assertIn('Nitrogen gas pycnometry', p['method_definition']['definition'])
        self.assertEqual(p['conditions']['temperature']['status'], 'not_reported_in_inspected_source')
        for suffix in ('mtibe2022_pbat_ecoflex_c1200', 'mtibe2022_pbs_pbat_70_30'):
            p = self.prop(suffix)
            self.assertEqual(p['conditions']['temperature']['text'], '25 °C')
            self.assertEqual(p['conditions']['conditioning']['text'], '48 h at 25 °C before tensile testing')
            self.assertEqual(p['conditions']['loading_rate']['status'], 'not_reported_in_inspected_source')

    def test_article_rights_hashes_and_four_language_names(self):
        expected_hashes = {
            'ewurum_mcdonald_2025_pbs_lignin': '766d17f0e92c7e93cd57a3a5e97dddff0cb66a84bba6bf9118fbd0796d4c2e6f',
            'abbasi_2022_manure_phbv': '31f8fb795385c4755bf17f104bd963cd3e2b107bef4e4ad9a5f34c7a776092ea',
            'mtibe_2022_pbs_pbat_lignin_zno': 'fa72f3441329d8db6348926906817ebac7b3bd7077a90e836f75f8ecdb087287',
        }
        sources = {s['id']: s for s in self.sources['records']}
        identities = {i['id']: i for i in self.materials['identities']}
        for suffix in FACTS:
            p = self.prop(suffix)
            self.assertEqual(p['source_document']['sha256'], expected_hashes[p['source_id']])
            self.assertEqual(sources[p['source_id']]['license'], {'status': 'explicit_reuse_license_verified', 'identifier': 'CC-BY-4.0'})
            for record in (self.state(suffix), identities['mat_' + suffix]):
                self.assertEqual(set(record['names']), {'en', 'zh', 'ja', 'de'})
                self.assertTrue(all(record['names'].values()))

    def test_old_and_new_four_language_detail_outputs(self):
        raw = (ROOT / 'tests/fixtures/material_polymer_outputs_v0340.json').read_bytes()
        self.assertEqual(digest(raw), OUTPUT_FIXTURE_SHA256)
        fixture = json.loads(raw)
        self.assertEqual(fixture['baseline_commit'], '8ed6fa18369b43719174fc407f76bc073e265d7c')
        self.assertEqual(fixture['baseline_tree'], '754ff52504b8f661214a717c35d2155512f3e951')
        self.assertEqual(len(fixture['old_details']), 102)
        self.assertEqual(len(fixture['admitted_details']), 12)
        for case in fixture['old_details'] + fixture['admitted_details']:
            with self.subTest(kind=case['kind'], id=case['id']):
                self.assertEqual(snapshot_case(case['kind'], case['id'], case['source_id']), case)


if __name__ == '__main__':
    unittest.main()
