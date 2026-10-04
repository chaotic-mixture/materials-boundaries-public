"""Historical evidence cannot silently disappear or acquire stronger provenance.

The ID-keyed data fixture records the reviewed historical declarations. New
records, reordered entries, and added evidence/notes/gaps are welcome. An
intentional correction is first checked against its exact reviewed successor,
then reversed solely for comparison with the untouched historical fixture.
Source curation provenance and every unrelated declaration stay exact.
"""
import json
from pathlib import Path
import unittest

from source_evidence_preservation import previous_catalog
from materials_boundaries.catalog import read_catalog
from catalog_fixtures import select_records


BASELINE = json.loads((Path(__file__).parent / 'fixtures/historical_provenance.json').read_text(encoding='utf-8'))


class HistoricalProvenanceTests(unittest.TestCase):
    def test_source_read_rights_and_bundled_scope_are_not_silently_upgraded(self):
        for source in select_records(previous_catalog('sources', read_catalog('sources')), BASELINE['sources']):
            expected = BASELINE['sources'][source['id']]
            for field in ('read_status', 'license', 'bundled_content', 'provenance'):
                with self.subTest(source=source['id'], field=field):
                    self.assertEqual(source[field], expected[field])

    def test_existing_source_notes_and_links_are_retained_as_subsets(self):
        for source in select_records(previous_catalog('sources', read_catalog('sources')), BASELINE['sources']):
            for field in ('claim_notes', 'urls'):
                for entry in BASELINE['sources'][source['id']][field]:
                    with self.subTest(source=source['id'], field=field, entry=entry):
                        self.assertIn(entry, source[field])

    def test_existing_claim_and_observation_evidence_is_an_exact_subset(self):
        for kind in ('claims', 'observations'):
            for record in select_records(previous_catalog(kind, read_catalog(kind)), BASELINE[kind]):
                for evidence in BASELINE[kind][record['id']]['evidence']:
                    with self.subTest(kind=kind, record=record['id'], evidence=evidence):
                        self.assertIn(evidence, record['evidence'])

    def test_review_declarations_and_existing_gaps_are_retained(self):
        for kind in ('claims', 'observations'):
            for record in select_records(previous_catalog(kind, read_catalog(kind)), BASELINE[kind]):
                expected = BASELINE[kind][record['id']]['verification']
                for field, value in expected.items():
                    with self.subTest(kind=kind, record=record['id'], field=field):
                        if field == 'gaps':
                            for gap in value:
                                self.assertIn(gap, record['verification']['gaps'])
                        else:
                            self.assertEqual(record['verification'][field], value)


if __name__ == '__main__':
    unittest.main()
