"""Exact old and newly admitted source-qualified four-language CLI details.

The old snapshot was produced from the independent immutable v0.32.0 tree.
New snapshots are presentation regressions, not scientific source validation.
"""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import unittest

from materials_boundaries.catalog import query_catalog
from materials_boundaries.cli import main
from material_bulk_preservation import predecessor_output

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = 'tests/fixtures/material_porous_outputs_v0330.json'
FIXTURE_SHA256 = '178a5a4f902c33f3bdbc5ecda1c56b6fda41c38e8debd6602c07a35a2b69d869'
LANGUAGES = ('en', 'zh', 'ja', 'de')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def snapshot_case(kind, identifier, source_id):
    case = {'kind': kind, 'id': identifier, 'source_id': source_id, 'languages': {}}
    selected = query_catalog(kind, record_id=identifier, source_id=source_id)
    if [row['id'] for row in selected['records']] != [identifier]:
        raise AssertionError('Source-qualified detail query lost its exact record')
    for language in LANGUAGES:
        case['languages'][language] = {}
        for flag in ('--json', '--text'):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = main(['catalog', kind, '--id', identifier, '--source-id', source_id,
                               '--lang', language, flag])
            text = stdout.getvalue()
            if status != 0 or '[missing:' in text:
                raise AssertionError('Source-qualified CLI detail failed')
            if flag == '--json' and json.loads(text) != selected:
                raise AssertionError('Language changed source-qualified JSON')
            # Exact versioned migration is checked before comparing the untouched old fixture.
            historical = predecessor_output(kind, identifier, source_id, language, flag[2:], text)
            case['languages'][language][flag[2:] + '_sha256'] = digest(historical.encode('utf-8'))
    return case


class MaterialPorousOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / FIXTURE).read_text(encoding='utf-8'))

    def test_snapshot_fixture_and_independent_predecessor_are_pinned(self):
        self.assertEqual(digest((ROOT / FIXTURE).read_bytes()), FIXTURE_SHA256)
        self.assertEqual(self.fixture['release'], '0.33.0')
        self.assertEqual(self.fixture['baseline_commit'], '14d4c26054b77aa4a431a6c1cc0de3458a0c63c1')
        self.assertEqual(self.fixture['baseline_tree'], '342da27ca3d781e55d0153a88171d0b2b3f7dd31')
        self.assertEqual(len(self.fixture['old_details']), 86)
        self.assertEqual(len(self.fixture['admitted_details']), 16)
        for key in ('old_details', 'admitted_details'):
            ids = [(case['kind'], case['id'], case['source_id']) for case in self.fixture[key]]
            self.assertEqual(len(ids), len(set(ids)))

    def test_all_43_prior_states_and_properties_keep_exact_text_and_json(self):
        for case in self.fixture['old_details']:
            with self.subTest(kind=case['kind'], id=case['id'], source=case['source_id']):
                self.assertEqual(snapshot_case(case['kind'], case['id'], case['source_id']), case)

    def test_eight_added_states_and_properties_keep_source_qualified_snapshots(self):
        for case in self.fixture['admitted_details']:
            with self.subTest(kind=case['kind'], id=case['id'], source=case['source_id']):
                self.assertEqual(snapshot_case(case['kind'], case['id'], case['source_id']), case)

    def test_snapshots_do_not_depend_on_whole_current_catalog_sizes(self):
        from materials_boundaries.catalog import read_catalog
        index = {row['id']: row for row in read_catalog('reference_properties')['records']}
        for case in self.fixture['old_details'] + self.fixture['admitted_details']:
            if case['kind'] == 'reference-properties':
                self.assertEqual(index[case['id']]['source_id'], case['source_id'])
                self.assertEqual(set(case['languages']), set(LANGUAGES))
                for value in case['languages'].values():
                    self.assertEqual(set(value), {'json_sha256', 'text_sha256'})


if __name__ == '__main__':
    unittest.main()
