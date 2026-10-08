"""Exact natural-class migration, provenance boundaries and mutation guards."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from materials_boundaries import material_taxonomy as taxonomy

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = {
    'mat_usda_sugar_maple', 'mat_usda_northern_red_oak', 'mat_usda_sitka_spruce',
    'mat_stochioiu2024_flax_technical_fiber', 'mat_stochioiu2024_hemp_technical_fiber',
    'mat_cheng2019_bombyx_mori_silk_strain932', 'mat_arbelaiz2024_latxa_wool',
    'mat_prasetia2024_qsuber_reproduction_cork', 'mat_drury2023_moso_bamboo_culm',
    'mat_drury2023_guadua_bamboo_culm',
}
LEDGER_SHA256 = '78f2c8f078856568d049aa9649101c0291d1c819e6dbb35e29f26c5da0cb0541'


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def leaf_differences(before, after, path=()):
    if type(before) is dict and type(after) is dict and set(before) == set(after):
        for key in before:
            yield from leaf_differences(before[key], after[key], path + (key,))
    elif type(before) is list and type(after) is list and len(before) == len(after):
        for i, (old, new) in enumerate(zip(before, after)):
            yield from leaf_differences(old, new, path + (i,))
    elif type(before) is not type(after) or before != after:
        yield path, before, after


class MaterialTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = taxonomy.load_taxonomy_migration()
        current = {name: json.loads((ROOT / 'materials_boundaries/data' / (name + '.json')).read_text(encoding='utf-8'))
                   for name in cls.ledger['catalogs']}
        taxonomy.verify_taxonomy_migration(current['materials'], current['reference_properties'])
        # Fixed historical projection, rather than a ceiling on new appends.
        cls.current = {}
        for name, catalog in current.items():
            pin = cls.ledger['catalogs'][name]
            cls.current[name] = deepcopy(pin['metadata'])
            for collection, records in pin['collections'].items():
                index = {row['id']: row for row in catalog[collection]}
                cls.current[name][collection] = [deepcopy(index[key]) for key in records]
        cls.materials = cls.current['materials']
        cls.properties = cls.current['reference_properties']
        cls.old_materials, cls.old_properties = taxonomy.apply_taxonomy_migration(
            cls.materials, cls.properties, reverse=True)

    def test_versioned_ledger_is_pinned_to_explicit_reviewed_migration(self):
        raw = (ROOT / 'materials_boundaries/data' / taxonomy.MIGRATION_RESOURCE).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), LEDGER_SHA256)
        self.assertEqual(taxonomy.MIGRATION_SHA256, LEDGER_SHA256)
        self.assertEqual(self.ledger['baseline_commit'], '7e37be919ee97f1275249dcf745f9f55e951986a')
        self.assertEqual(self.ledger['baseline_software_version'], '0.34.0')
        self.assertEqual(self.ledger['taxonomy_policy_version'], '1.0.0')
        self.assertEqual(self.ledger['migration_id'], 'natural-biological-tissue-v1')
        self.assertEqual(tuple(self.ledger['categories']), taxonomy.PRIMARY_CATEGORIES)
        self.assertEqual(self.ledger['previous_categories'], ['metal', 'inorganic', 'polymer', 'composite'])
        self.assertEqual(set(self.ledger['migrated_identity_ids']), EXPECTED_IDS)
        self.assertEqual(len(self.ledger['migrated_identity_ids']), 10)

    def test_exactly_ten_identities_change_primary_category(self):
        before = {row['id']: row for row in self.old_materials['identities']}
        changed = {row['id']: (before[row['id']]['category'], row['category'])
                   for row in self.materials['identities'] if before[row['id']]['category'] != row['category']}
        self.assertEqual(set(changed), EXPECTED_IDS)
        self.assertEqual(Counter(pair[0] for pair in changed.values()), {'composite': 8, 'polymer': 2})
        self.assertEqual({pair[1] for pair in changed.values()}, {'natural'})
        self.assertEqual(Counter(row['category'] for row in self.materials['identities']),
                         {'metal': 14, 'inorganic': 16, 'polymer': 14, 'composite': 3, 'natural': 10})
        self.assertEqual(len(self.materials['identities']), 57)
        self.assertEqual(len(self.materials['grades']), 20)
        self.assertEqual(len(self.materials['records']), 57)
        self.assertEqual(len(self.properties['records']), 57)

    def test_ledger_matches_all_and_only_34_actual_leaf_edits(self):
        catalogs = {'materials': self.old_materials, 'reference_properties': self.old_properties}
        actual = []
        for name, old in catalogs.items():
            for path, before, after in leaf_differences(old, self.current[name]):
                self.assertEqual(len(path), 3)
                collection, index, field = path
                actual.append({'catalog': name, 'collection': collection,
                               'record_id': old[collection][index]['id'], 'field': field,
                               'before': before, 'after': after})
        self.assertEqual(actual, self.ledger['changes'])
        self.assertEqual(Counter((r['catalog'], r['collection'], r['field']) for r in actual), {
            ('materials', 'identities', 'category'): 10,
            ('materials', 'identities', 'identity_scope'): 10,
            ('materials', 'records', 'source_scope'): 7,
            ('reference_properties', 'records', 'scope_note'): 7,
        })

    def test_exact_baseline_files_and_migrated_files_round_trip(self):
        for name, before, after in (('materials', self.old_materials, self.materials),
                                    ('reference_properties', self.old_properties, self.properties)):
            pin = self.ledger['catalogs'][name]
            self.assertEqual(hashlib.sha256(serialized(before)).hexdigest(), pin['before_file_sha256'])
            self.assertEqual(hashlib.sha256(serialized(after)).hexdigest(), pin['after_file_sha256'])
        self.assertEqual(taxonomy.apply_taxonomy_migration(self.old_materials, self.old_properties),
                         (self.materials, self.properties))
        self.assertEqual(taxonomy.apply_taxonomy_migration(self.materials, self.properties, reverse=True),
                         (self.old_materials, self.old_properties))

    def test_every_nonclassification_field_is_unchanged(self):
        self.assertEqual(self.materials['grades'], self.old_materials['grades'])
        for collection in ('identities', 'records'):
            omitted = {'category', 'identity_scope'} if collection == 'identities' else {'source_scope'}
            for before, after in zip(self.old_materials[collection], self.materials[collection]):
                self.assertEqual({k: v for k, v in before.items() if k not in omitted},
                                 {k: v for k, v in after.items() if k not in omitted})
        for before, after in zip(self.old_properties['records'], self.properties['records']):
            self.assertEqual({k: v for k, v in before.items() if k != 'scope_note'},
                             {k: v for k, v in after.items() if k != 'scope_note'})
        for entry in self.ledger['changes']:
            if entry['field'] != 'category':
                self.assertIsInstance(entry['before'], str)
                self.assertIsInstance(entry['after'], str)

    def test_natural_does_not_mean_biogenic_feedstock_or_mineral_origin(self):
        identities = {row['id']: row for row in self.materials['identities']}
        for identifier in ('mat_smr10_bianchi2025_nr', 'mat_ewurum2025_indulin_at',
                           'mat_ewurum2025_biopbs', 'mat_abbasi2022_manure_phbv39',
                           'mat_mtibe2022_pbat_ecoflex_c1200', 'mat_mtibe2022_pbs_pbat_70_30'):
            self.assertEqual(identities[identifier]['category'], 'polymer')
        for identifier in ('mat_wubalem2025_carrara_marble', 'mat_jonczy2022_k1_quartz_arenite'):
            self.assertEqual(identities[identifier]['category'], 'inorganic')
        self.assertEqual(identities['mat_ewurum2025_pbs_lignin20']['category'], 'composite')
        for row in self.materials['identities']:
            self.assertNotIn('canonical_identity', row)
            self.assertNotIn('wfo_id', row)
        self.assertIn('independently curated', self.ledger['identity_policy'])

    def test_scope_replacements_remain_synchronized_and_no_old_classification_claims_remain(self):
        identities = {row['id']: row for row in self.materials['identities']}
        states = {row['id']: row for row in self.materials['records']}
        for prop in self.properties['records']:
            state = states[prop['material_state_id']]
            if state['identity_id'] not in EXPECTED_IDS:
                continue
            identity = identities[state['identity_id']]
            for text in (identity['identity_scope'], state['source_scope'], prop['scope_note']):
                for stale in ('Natural biological-composite classification', 'Composite is a broad',
                              'Polymer is a broad natural'):
                    self.assertNotIn(stale, text)
            if not state['identity_id'].startswith('mat_usda_'):
                self.assertEqual(identity['identity_scope'], state['source_scope'])
                self.assertEqual(state['source_scope'], prop['scope_note'])

    def test_current_runtime_natural_filter_and_four_language_views(self):
        from materials_boundaries.catalog import query_catalog
        from materials_boundaries.catalog_output import render_catalog
        from materials_boundaries.material_presentation import material_labels
        from materials_boundaries.material_references import CATEGORIES
        self.assertEqual(tuple(CATEGORIES), taxonomy.PRIMARY_CATEGORIES)
        selected = query_catalog('materials', category='natural')
        legacy_ids = {row['id'] for row in self.materials['identities']}
        self.assertEqual({row['id'] for row in selected['identities']} & legacy_ids, EXPECTED_IDS)
        self.assertTrue(all(row['category'] == 'natural' for row in selected['identities']))
        for lang in ('en', 'zh', 'ja', 'de'):
            text = render_catalog(selected, 'materials', lang)
            self.assertNotIn('[missing:', text)
            self.assertIn(material_labels(lang)['code_natural'], text)

    def test_replay_and_loading_never_mutate_inputs_or_share_returned_structures(self):
        materials, properties = deepcopy(self.old_materials), deepcopy(self.old_properties)
        result = taxonomy.apply_taxonomy_migration(materials, properties)
        self.assertEqual(materials, self.old_materials)
        self.assertEqual(properties, self.old_properties)
        result[0]['grades'][0]['name'] = 'independent mutation'
        self.assertEqual(materials, self.old_materials)
        ledger = taxonomy.load_taxonomy_migration()
        ledger['changes'].clear()
        self.assertEqual(len(taxonomy.load_taxonomy_migration()['changes']), 34)

    def test_repeated_mixed_incomplete_and_nonboolean_replay_fail_closed(self):
        cases = [(self.materials, self.properties, False),
                 (self.old_materials, self.old_properties, True),
                 (self.materials, self.old_properties, True),
                 (self.old_materials, self.properties, False),
                 ({}, self.old_properties, False),
                 (self.old_materials, self.old_properties, 1)]
        for materials, properties, reverse in cases:
            with self.subTest(reverse=reverse), self.assertRaises(ValueError):
                taxonomy.apply_taxonomy_migration(materials, properties, reverse=reverse)

    def test_arbitrary_retained_mutations_fail_full_object_pins(self):
        cases = [
            ('materials', lambda x: x['identities'][23].update(category='composite')),
            ('materials', lambda x: x['identities'][23].update(identity_scope='changed')),
            ('materials', lambda x: x['identities'][0].update(category='natural')),
            ('materials', lambda x: x['identities'][0]['evidence'][0].update(locator='changed')),
            ('materials', lambda x: x['grades'][0].update(version='9.9.9')),
            ('materials', lambda x: x['records'][0].update(grade_id=None)),
            ('materials', lambda x: x['records'][39].update(source_scope='changed')),
            ('reference_properties', lambda x: x['records'][0]['reported_value'].update(number='999')),
            ('reference_properties', lambda x: x['records'][0]['conditions']['temperature'].update(text='changed')),
            ('reference_properties', lambda x: x['records'][39].update(scope_note='changed')),
            ('reference_properties', lambda x: x['records'][0]['verification'].update(independent_scientific_review=True)),
            ('reference_properties', lambda x: x['records'].pop()),
        ]
        for name, mutate in cases:
            bad = deepcopy(self.current)
            mutate(bad[name])
            with self.subTest(name=name), self.assertRaises(ValueError):
                taxonomy.verify_taxonomy_migration(bad['materials'], bad['reference_properties'])

    def test_independent_appends_do_not_weaken_retained_preservation(self):
        extended = deepcopy(self.current)
        for name, catalog in extended.items():
            for collection in self.ledger['catalogs'][name]['collections']:
                catalog[collection].append({'id': 'synthetic_' + name + '_' + collection})
        taxonomy.verify_taxonomy_migration(extended['materials'], extended['reference_properties'])
        with self.assertRaises(ValueError):
            taxonomy.apply_taxonomy_migration(extended['materials'], extended['reference_properties'], reverse=True)
        extended['materials']['identities'][0]['category'] = 'natural'
        with self.assertRaises(ValueError):
            taxonomy.verify_taxonomy_migration(extended['materials'], extended['reference_properties'])

    def test_duplicates_reordering_invalid_ids_and_changed_metadata_fail(self):
        for mutate in (
            lambda x: x['identities'].append(deepcopy(x['identities'][0])),
            lambda x: x['identities'].append({'id': ''}),
            lambda x: x['identities'].append({'id': True}),
            lambda x: x['identities'].reverse(),
            lambda x: x.update(schema_version='2.0.0'),
            lambda x: x.update(extra='unreviewed'),
            lambda x: x.update(records={}),
        ):
            bad = deepcopy(self.materials)
            mutate(bad)
            with self.assertRaises(ValueError):
                taxonomy.verify_taxonomy_migration(bad, self.properties)

    def test_missing_tampered_or_duplicate_key_ledger_cannot_authorize_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'data').mkdir()
            target = root / 'data' / taxonomy.MIGRATION_RESOURCE
            with patch.object(taxonomy, 'files', return_value=root):
                with self.assertRaises(FileNotFoundError):
                    taxonomy.load_taxonomy_migration()
                for value in (b'{}', serialized(self.ledger) + b' ',
                              b'{"schema_version":"1.0.0","schema_version":"2.0.0"}'):
                    target.write_bytes(value)
                    with self.assertRaises(ValueError):
                        taxonomy.load_taxonomy_migration()
        with self.assertRaises(ValueError):
            taxonomy._unique_keys([('duplicate', 1), ('duplicate', 2)])


if __name__ == '__main__':
    unittest.main()
