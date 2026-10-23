"""Finite prose bridges preserve original pins, normalizers and rejection checks."""
import ast
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import unittest
from unittest.mock import patch

import legacy_document_recovery as recovery
import material_bulk_preservation as bulk
from material_append_history import recover_file, project_file_chain

ROOT = Path(__file__).resolve().parents[1]
HELPER_SHA256 = '8f9e40f41de596ebeffdad024dedc211def31bef008c4e3d1f442b6d2082c0e0'
CODE_PATHS = {
    'tests/material_bulk_preservation.py',
    'tests/material_class_counts_preservation.py',
    'tests/test_material_class_counts_preservation.py',
}


def digest(raw):
    return sha256(raw).hexdigest()


class LegacyDocumentRecoveryTests(unittest.TestCase):
    def test_helper_ledgers_and_call_site_inventory_are_byte_pinned(self):
        self.assertEqual(digest((ROOT / 'tests/legacy_document_recovery.py').read_bytes()), HELPER_SHA256)
        code = recovery.code_ledger()
        self.assertEqual(set(code['updates']), CODE_PATHS)
        self.assertEqual(code['baseline_commit'], 'e3ca1cab18851bf648ffee0277182ca80a33b123')
        document = recovery.load_frozen(ROOT, recovery.DOCUMENT_LEDGER, recovery.DOCUMENT_SHA256)
        self.assertEqual(len(document['ledgers']), 7)
        self.assertEqual({path for ledger in document['ledgers'] for path in ledger['updates']}, {'README.md', 'THIRD_PARTY_NOTICES.md'})

    def test_exact_document_chains_reach_unchanged_original_release_pins(self):
        frozen = recovery.load_frozen(ROOT, recovery.DOCUMENT_LEDGER, recovery.DOCUMENT_SHA256)
        expected = {entry['filename']: entry['sha256'] for entry in bulk.load_ledger()['approved_existing_updates']}
        for filename in ('README.md', 'THIRD_PARTY_NOTICES.md'):
            raw = (ROOT / filename).read_bytes()
            if filename == 'README.md':
                raw = bulk.truthful_readme(raw, bulk.load_ledger())
            self.assertEqual(digest(recovery.project_legacy_document_bytes(filename, raw)), expected[filename])
            entries = [ledger['updates'][filename] for ledger in frozen['ledgers'] if filename in ledger['updates']]
            self.assertEqual(len(entries), 3 if filename == 'README.md' else 4)
            for entry in entries:
                self.assertEqual(digest(raw), entry['sha256'])
                previous = recover_file(raw, entry)
                self.assertEqual(digest(previous), entry['previous_sha256'])
                for bad in (raw + b'!', raw[:-1], b'!' + raw[1:]):
                    with self.assertRaises(AssertionError):
                        recover_file(bad, entry)
                broken = deepcopy(entry)
                broken['edits'][0]['offset'] += 1
                with self.assertRaises(AssertionError):
                    recover_file(raw, broken)
                raw = previous
            self.assertEqual(digest(raw), expected[filename])
            self.assertEqual(recovery.project_legacy_document_bytes(filename, raw), raw)

    def test_modified_prose_and_attribution_still_fail_original_release_checks(self):
        for filename in ('README.md', 'THIRD_PARTY_NOTICES.md'):
            raw = (ROOT / filename).read_bytes()
            for changed in (raw + b'unknown prose\n', raw[:-1], b'!' + raw[1:],
                            raw.replace(b'Bruns', b'Unreviewed', 1)):
                self.assertNotEqual(changed, raw)
                with self.subTest(filename=filename), self.assertRaises(AssertionError):
                    bulk.release_bytes(filename, changed)
        for filename in ('LICENSE', '../README.md', None):
            with self.assertRaises(AssertionError):
                recovery.project_legacy_document_bytes(filename, b'anything')

    def test_exact_call_site_reversal_changes_no_old_assertion_or_normalizer(self):
        def assertions(raw):
            return [ast.dump(node) for node in ast.walk(ast.parse(raw))
                    if isinstance(node, ast.Assert) or
                    (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                     and node.func.attr.startswith('assert'))]
        for path, entry in recovery.code_ledger()['updates'].items():
            current = (ROOT / path).read_bytes()
            previous = recover_file(current, entry)
            self.assertEqual(assertions(previous), assertions(current))
            for raw in (current + b'!', current[:-1]):
                self.assertEqual(recovery.project_legacy_code_bytes(path, raw), raw)
        current = ast.parse((ROOT / 'tests/material_bulk_preservation.py').read_bytes())
        previous = ast.parse(recover_file((ROOT / 'tests/material_bulk_preservation.py').read_bytes(),
            recovery.code_ledger()['updates']['tests/material_bulk_preservation.py']))
        function = lambda tree: next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'truthful_readme')
        self.assertEqual(ast.dump(function(current)), ast.dump(function(previous)))

    def test_reordered_chains_and_forged_fixtures_fail_closed(self):
        frozen = recovery.load_frozen(ROOT, recovery.DOCUMENT_LEDGER, recovery.DOCUMENT_SHA256)
        with self.assertRaises(AssertionError):
            project_file_chain('THIRD_PARTY_NOTICES.md', b'', list(reversed(frozen['ledgers'])))
        with patch.object(recovery, 'DOCUMENT_SHA256', '0' * 64):
            with self.assertRaises(AssertionError):
                recovery.project_legacy_document_bytes('README.md', b'anything')
        with patch.object(recovery, 'CODE_SHA256', '0' * 64):
            with self.assertRaises(AssertionError):
                recovery.project_legacy_code_bytes('README.md', b'anything')


if __name__ == '__main__':
    unittest.main()
