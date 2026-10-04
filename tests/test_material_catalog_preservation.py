"""Exact release lineage and admitted-object pins, open to later valid appends."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

import material_catalog_preservation as history
from materials_boundaries.catalog import read_catalog
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES
from materials_boundaries.material_references import material_coverage, validate_material_catalog

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SHA256 = 'a6dbb49725c2c527bc02340e252c111bfd1ce9e393b0163aaf48f53ed156bb52'
HELPER_SHA256 = '3c0d51c97eac87f121ab967bd7e5dc175f7bef27c30f522172f52c526cdfcb33'
ADMISSION_SHA256 = '238b5dd0cb99d7c62b0f93333e8f8061964c40aa1c761b2ab76a65ef6d5e5a12'


def canonical(record):
    return json.dumps(record, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def declarations(raw):
    tree = ast.parse(raw)
    return {node.name + '.' + item.name for node in tree.body if isinstance(node, ast.ClassDef)
            for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))} | {
            node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


class MaterialCatalogPreservationTests(unittest.TestCase):
    def test_new_ledger_helper_and_admission_are_pinned(self):
        for filename, digest in [(history.LEDGER_PATH, LEDGER_SHA256),
                                 ('tests/material_catalog_preservation.py', HELPER_SHA256),
                                 ('tests/fixtures/material_catalog_admission_v0290.json', ADMISSION_SHA256)]:
            self.assertEqual(history.digest((ROOT / filename).read_bytes()), digest)
        ledger = history.load_ledger()
        history.validate_ledger(ledger)
        self.assertEqual(ledger['baseline_commit'], history.BASELINE_COMMIT)
        self.assertEqual(ledger['baseline_tree'], history.BASELINE_TREE)
        self.assertEqual(len(ledger['baseline_sha256']), 339)
        self.assertEqual(len(BASE_RULES) + len(DERIVED_RULES), 8)

    def test_all_old_noncatalog_files_recover_exact_accepted_bytes(self):
        ledger = history.load_ledger()
        for filename, expected in ledger['baseline_sha256'].items():
            if filename.startswith('materials_boundaries/data/'):
                continue
            actual = (ROOT / filename).read_bytes()
            with self.subTest(filename=filename):
                before = history.pre_material_bytes(filename, actual)
                self.assertEqual(history.digest(before), expected)
                if filename.startswith(('tests/fixtures/', 'examples/', 'schemas/')):
                    self.assertEqual(actual, before)
                if filename.startswith('tests/') and filename.endswith('.py'):
                    self.assertLessEqual(declarations(before), declarations(actual))

    def test_successors_round_trip_and_arbitrary_bytes_fail(self):
        ledger = history.load_ledger()
        for entry in ledger['approved_existing_updates']:
            actual = (ROOT / entry['filename']).read_bytes()
            if entry['filename'] == 'README.md':
                actual, _ = history._truthful_readme(actual, ledger)
            before = history.reverse_exact_edits(actual, entry)
            self.assertEqual(history.apply_exact_edits(before, entry['edits']), actual)
            with self.assertRaises(AssertionError):
                history.pre_material_bytes(entry['filename'], actual + b'!')

    def test_corrupt_or_incomplete_ledgers_fail(self):
        changes = [lambda x: x.update(extra=True), lambda x: x.update(schema_version=True),
                   lambda x: x.update(baseline_commit='0' * 40),
                   lambda x: x['baseline_sha256'].pop('LICENSE'),
                   lambda x: x['approved_existing_updates'].append(deepcopy(x['approved_existing_updates'][0])),
                   lambda x: x['approved_existing_updates'][0].update(previous_sha256='0' * 64),
                   lambda x: x['approved_existing_updates'][0]['edits'][0].update(offset=-1),
                   lambda x: x['readme_summaries'].update(extra='unexpected')]
        for change in changes:
            bad = deepcopy(history.load_ledger()); change(bad)
            with self.assertRaises(AssertionError):
                history.validate_ledger(bad)

    def test_baseline_sources_and_initial_admitted_records_are_exact_subsets(self):
        pins = json.loads((ROOT / 'tests/fixtures/material_catalog_admission_v0290.json').read_text(encoding='utf-8'))
        sources = {r['id']: r for r in read_catalog('sources')['records']}
        for identifier, expected in pins['baseline_source_digests'].items():
            self.assertEqual(history.digest(canonical(sources[identifier])), expected)
        for kind, fields in pins['admitted_record_digests'].items():
            data = read_catalog(kind)
            for field, records in fields.items():
                actual = {r['id']: r for r in data[field]}
                self.assertEqual(len(actual), len(data[field]))
                for identifier, expected in records.items():
                    self.assertEqual(history.digest(canonical(actual[identifier])), expected)
        validate_material_catalog(read_catalog('materials'), read_catalog('reference_properties'), read_catalog('sources'))

    def test_current_material_summary_is_derived_from_actual_registry(self):
        coverage = material_coverage(read_catalog('materials'), read_catalog('reference_properties'))
        text = (ROOT / 'README.md').read_text(encoding='utf-8')
        summary = history._section(text, 'material-catalog-summary')[1]
        for code, label in [('material_identity_count', 'material identities'), ('grade_count', 'qualified grades'),
                            ('material_state_count', 'source-scoped states'), ('property_record_count', 'reference properties')]:
            self.assertIn(f'**{coverage[code]} {label}**', summary)
        self.assertEqual(coverage['material_state_count'], len(read_catalog('materials')['records']))

    def test_readme_normalization_rejects_changed_prose_and_untrue_counts(self):
        actual = (ROOT / 'README.md').read_bytes()
        history.pre_material_readme(actual)
        for bad in [actual.replace(b'material identities**', b'materials**', 1),
                    actual.replace(b' source-scoped states**', b' universally validated states**', 1),
                    actual + b'changed prose']:
            with self.assertRaises(AssertionError):
                history.pre_material_readme(bad)


if __name__ == '__main__':
    unittest.main()
