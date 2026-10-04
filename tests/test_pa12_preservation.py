"""Historic payload and display parity against the accepted v0.21 snapshot.

Metadata hashes do not identify article bytes or independently validate science.
Additional claim evidence is allowed only after every baseline item is found
unchanged. Whole-file/object equality is checked separately on the release tree.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from viscoelastic_preservation import pre_viscoelastic_bytes
import unittest

from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.i18n import translate
from materials_boundaries._pa12_cf15_observation_contract import PA12_SOURCE, PA12_QUANTITY
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries.observation_visualization import build_observation_inspection

ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((ROOT / 'tests/fixtures/pre_pa12_v0220.json').read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class PA12HistoricPreservation(unittest.TestCase):
    def test_every_old_scientific_record_is_unchanged(self):
        for kind, expected in BASELINE['record_sha256'].items():
            records = {r['id']: r for r in read_catalog(kind)['records']}
            for identifier, expected_hash in expected.items():
                with self.subTest(kind=kind, identifier=identifier):
                    record = deepcopy(records[identifier])
                    if kind == 'claims':
                        evidence = {digest(e): e for e in record['evidence']}
                        record['evidence'] = [evidence[h] for h in BASELINE['claim_evidence_sha256'][identifier]]
                    self.assertEqual(digest(record), expected_hash)

    def test_old_prediction_protocols_and_groups_are_unchanged(self):
        for kind, fields in BASELINE['metadata_sha256'].items():
            catalog = read_catalog(kind)
            for field, expected in fields.items():
                actual = {r['id']: r for r in catalog[field]}
                for identifier, expected_hash in expected.items():
                    with self.subTest(kind=kind, field=field, identifier=identifier):
                        self.assertEqual(digest(actual[identifier]), expected_hash)

    def test_old_observation_text_bytes_in_all_four_languages(self):
        catalog = read_catalog('observations')
        actual = {r['id']: r for r in catalog['records']}
        catalog['records'] = [actual[rid] for rid in BASELINE['record_sha256']['observations']]
        for language, expected in BASELINE['old_observation_catalog_text_sha256'].items():
            with self.subTest(language=language):
                text = render_catalog(catalog, 'observations', language)
                self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), expected)

    def test_reviewed_test_hash_ledger_is_closed(self):
        from unittest.mock import patch
        import provenance_corrections as history
        ledger = deepcopy(history.PA12_TEST_UPDATES)
        filename = 'tests/test_catalog_translation_snapshot.py'
        change = ledger['approved_test_updates'][filename]
        # This file has no older overrides; the new predecessor must match
        # exactly before the reviewed current hash can be used.
        self.assertEqual(history.reviewed_test_hash(filename, change['previous_sha256']), change['sha256'])
        self.assertEqual(hashlib.sha256(pre_viscoelastic_bytes(filename, (ROOT / filename).read_bytes())).hexdigest(), change['sha256'])
        for mutation in ('foreign_file', 'missing_file', 'wrong_predecessor', 'blank_reason'):
            altered = deepcopy(ledger)
            if mutation == 'foreign_file':
                altered['approved_test_updates']['unreviewed.py'] = deepcopy(change)
            elif mutation == 'missing_file':
                del altered['approved_test_updates']['tests/provenance_corrections.py']
            elif mutation == 'wrong_predecessor':
                altered['approved_test_updates'][filename]['previous_sha256'] = '0' * 64
            else:
                altered['approved_test_updates'][filename]['reason'] = ' '
            with self.subTest(mutation=mutation), patch.object(history, 'PA12_TEST_UPDATES', altered):
                with self.assertRaises(AssertionError):
                    history.reviewed_test_hash(filename, change['previous_sha256'])

    def test_old_facets_have_identical_scientific_fields(self):
        ids = list(BASELINE['record_sha256']['observations'])
        bundle = build_observation_inspection(ids)
        actual = {f['record_id']: f for f in bundle['facets']}
        self.assertEqual(digest([actual[rid] for rid in ids]), BASELINE['old_inspection_facets_sha256'])


class PA12CatalogIntegration(unittest.TestCase):
    def test_exact_six_new_records_are_catalog_only(self):
        selected = query_catalog('observations', source_id=PA12_SOURCE)
        self.assertEqual(len(selected['records']), 6)
        self.assertEqual(selected['records'], [r for r in read_catalog('observations')['records']
                                              if r.get('study_id') == PA12_SOURCE])
        self.assertEqual({r['conditions']['temperature']['value'] for r in selected['records']},
                         {23, 40, 60, 80, 100, 120})
        self.assertTrue(all(r['evaluation_support'] == 'catalog_only' for r in selected['records']))
        self.assertEqual({r['quantity'] for r in selected['records']}, {PA12_QUANTITY})
        self.assertEqual({r['si_unit'] for r in selected['records']}, {'Pa'})
        filtered = query_catalog('observations', quantity=PA12_QUANTITY,
            observation_type='experiment_derived_tensile_test_summary', source_id=PA12_SOURCE)
        self.assertEqual(filtered, selected)
        self.assertEqual(query_catalog('observations', source_id=PA12_SOURCE,
            quantity='breaking_strength_2d')['records'], [])

    def test_all_localized_warnings_precede_each_reported_value(self):
        for r in query_catalog('observations', source_id=PA12_SOURCE)['records']:
            for language in ('en', 'zh', 'ja', 'de'):
                with self.subTest(record=r['id'], language=language):
                    text = render_catalog({'schema_version':'1.3.0','records':[r]}, 'observations', language)
                    display = r['reported_result']['value_string'] + ' ± ' + r['reported_result']['uncertainty']['value_string'] + ' MPa'
                    self.assertNotIn('[missing:', text)
                    for key in ('classification','identity','temperature','process','stress','sample'):
                        warning = translate('catalog_pa12_' + key, language)
                        self.assertIn(warning, text)
                        self.assertLess(text.index(warning), text.index(display))
                    self.assertIn(str(r['si_result']['value']) + ' ± ' + str(r['si_result']['uncertainty_value']) + ' Pa', text)
                    self.assertIn(translate('catalog_pa12_normalization', language), text)
                    self.assertIn(translate('catalog_pa12_source_version', language), text)
                    self.assertIn(translate('catalog_pa12_rights', language), text)
                    self.assertNotIn('poissons_ratio_assumed', text)
                    self.assertNotIn('layer_count', text)

    def test_localized_alias_search_is_literal_and_language_independent(self):
        for r in query_catalog('observations', source_id=PA12_SOURCE)['records']:
            for language in ('en', 'zh', 'ja', 'de'):
                alias = translate('catalog_name_' + r['id'], language)
                self.assertNotIn('[missing:', alias)
                # Every term is a literal substring of any documented field;
                # e.g. "80" also occurs in the shared DOI-derived study ID.
                self.assertIn(r['id'], [v['id'] for v in query_catalog('observations', query=alias)['records']])
                self.assertEqual([v['id'] for v in query_catalog('observations', query=alias,
                    record_id=r['id'])['records']], [r['id']])


if __name__ == '__main__':
    unittest.main()
