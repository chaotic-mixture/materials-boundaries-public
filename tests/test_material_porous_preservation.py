"""Exact v0.32 release recovery and open-ID v0.33 material admission pins."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

import material_porous_preservation as history
from materials_boundaries.catalog import read_catalog
from materials_boundaries.engine import BASE_RULES, DERIVED_RULES
from materials_boundaries.material_references import validate_material_catalog

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SHA256 = 'c9fdb94a8d4f2e730cf76e72f1bff2292071b4d6de0642547ff99a4d041bcdf3'
HELPER_SHA256 = '31d28465234bed6d26ac6713319da5d7f71be10f2b1ac4ca88099b6ecb001173'
ADMISSION_SHA256 = '9c3da341ff6c0ef62af78aaa28d29ea2dcda3e088a1ed7eb8f1f4564a2a93d0e'


def declarations(raw):
    tree = ast.parse(raw)
    return {node.name + '.' + item.name for node in tree.body if isinstance(node, ast.ClassDef)
            for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))} | {
            node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


class MaterialPorousPreservationTests(unittest.TestCase):
    def test_ledger_helper_admission_and_accepted_tree_are_pinned(self):
        for filename, expected in ((history.LEDGER_PATH, LEDGER_SHA256),
                                   ('tests/material_porous_preservation.py', HELPER_SHA256),
                                   (history.ADMISSION_PATH, ADMISSION_SHA256)):
            self.assertEqual(history.digest((ROOT / filename).read_bytes()), expected)
        ledger = history.load_ledger()
        history.validate_ledger(ledger)
        self.assertEqual(ledger['baseline_commit'], '14d4c26054b77aa4a431a6c1cc0de3458a0c63c1')
        self.assertEqual(ledger['baseline_tree'], '342da27ca3d781e55d0153a88171d0b2b3f7dd31')
        self.assertEqual(len(ledger['baseline_sha256']), 383)
        self.assertEqual({r[0] for r in (*BASE_RULES, *DERIVED_RULES)}, history.EXECUTABLE_IDS)
        self.assertEqual(len(BASE_RULES) + len(DERIVED_RULES), 8)

    def test_all_383_predecessor_files_round_trip_exactly(self):
        ledger = history.load_ledger(); entries = history.validate_ledger(ledger)
        for filename, expected in ledger['baseline_sha256'].items():
            with self.subTest(filename=filename):
                actual = (ROOT / filename).read_bytes()
                release = history.release_bytes(filename, actual, ledger=ledger)
                before = history.pre_material_porous_bytes(filename, actual, ledger=ledger)
                self.assertEqual(history.digest(before), expected)
                self.assertEqual(history.apply_exact_edits(before, entries[filename]['edits'])
                                 if filename in entries else before, release)
                if filename.startswith(('tests/fixtures/', 'examples/')) or filename == 'materials_boundaries/engine.py':
                    self.assertEqual(actual, before)
                if filename.startswith('tests/') and filename.endswith('.py'):
                    self.assertLessEqual(declarations(before), declarations(actual))

    def test_every_exact_update_rejects_arbitrary_bytes_and_wrong_edits(self):
        ledger = history.load_ledger()
        for entry in ledger['approved_existing_updates']:
            with self.subTest(filename=entry['filename']):
                current = history.release_bytes(entry['filename'], (ROOT / entry['filename']).read_bytes(), ledger=ledger)
                previous = history.reverse_exact_edits(current, entry)
                self.assertEqual(history.apply_exact_edits(previous, entry['edits']), current)
                for bad in (current + b'!', b'unreviewed replacement'):
                    with self.assertRaises((AssertionError, ValueError)):
                        history.pre_material_porous_bytes(entry['filename'], bad, ledger=ledger)
                wrong = deepcopy(entry['edits']); wrong[0]['before'] += 'unreviewed'
                with self.assertRaises(AssertionError):
                    history.apply_exact_edits(previous, wrong)
        with self.assertRaises(AssertionError):
            history.pre_material_porous_bytes('../README.md', b'unknown', ledger=ledger)

    def test_corrupt_incomplete_duplicate_or_foreign_ledgers_fail(self):
        mutations = [lambda x: x.update(extra=True), lambda x: x.update(schema_version=True),
                     lambda x: x.update(baseline_commit='0' * 40), lambda x: x.update(baseline_tree='0' * 40),
                     lambda x: x['baseline_sha256'].pop('LICENSE'),
                     lambda x: x['approved_existing_updates'].pop(),
                     lambda x: x['approved_existing_updates'].append(deepcopy(x['approved_existing_updates'][0])),
                     lambda x: x['approved_existing_updates'][0].update(filename='foreign.py'),
                     lambda x: x['approved_existing_updates'][0].update(previous_sha256='0' * 64),
                     lambda x: x['approved_existing_updates'][0].update(reason=' '),
                     lambda x: x['approved_existing_updates'][0]['edits'][0].update(offset=True),
                     lambda x: x['readme_summaries'].update(extra='unexpected'),
                     lambda x: x['catalog_preservation'].pop('materials_boundaries/data/materials.json'),
                     lambda x: x['catalog_preservation']['materials_boundaries/data/materials.json']['records']['record_digests'].update(forged='bad')]
        for mutation in mutations:
            bad = deepcopy(history.load_ledger()); mutation(bad)
            with self.assertRaises(AssertionError):
                history.validate_ledger(bad)
        with self.assertRaises(AssertionError):
            json.loads('{"duplicate":1,"duplicate":2}', object_pairs_hook=history.unique_keys)

    def test_every_prior_catalog_object_and_metadata_is_preserved(self):
        admission = json.loads((ROOT / history.ADMISSION_PATH).read_text(encoding='utf-8'))
        baseline = admission['baseline_catalog_preservation']
        history.validate_catalog_pins(baseline)
        manifest = history.load_ledger()['baseline_sha256']
        for filename in baseline:
            with self.subTest(filename=filename):
                actual = json.loads((ROOT / filename).read_text(encoding='utf-8'))
                previous = history.project_catalog(filename, actual, baseline)
                self.assertEqual(history.digest(serialized(previous)), manifest[filename])
        self.assertEqual(len(baseline['materials_boundaries/data/materials.json']['identities']['record_digests']), 43)
        self.assertEqual(len(baseline['materials_boundaries/data/materials.json']['records']['record_digests']), 43)
        self.assertEqual(len(baseline['materials_boundaries/data/reference_properties.json']['records']['record_digests']), 43)

    def test_eight_new_material_admissions_are_exact_independent_subsets(self):
        admission = json.loads((ROOT / history.ADMISSION_PATH).read_text(encoding='utf-8'))
        self.assertEqual(admission['release'], '0.33.0')
        self.assertEqual(admission['baseline_commit'], history.BASELINE_COMMIT)
        self.assertEqual(admission['baseline_tree'], history.BASELINE_TREE)
        admitted = admission['admitted_record_digests']
        for kind, fields in admitted.items():
            actual = read_catalog(kind)
            for field, pins in fields.items():
                index = {record['id']: record for record in actual[field]}
                self.assertEqual(len(index), len(actual[field]))
                for identifier, expected in pins.items():
                    self.assertEqual(history.digest(history.canonical(index[identifier])), expected)
        for kind, field in (('materials', 'identities'), ('materials', 'records'), ('reference_properties', 'records')):
            self.assertEqual(len(admitted[kind][field]), 8)
        validate_material_catalog(read_catalog('materials'), read_catalog('reference_properties'), read_catalog('sources'))

    def test_fixed_objects_cannot_be_mutated_removed_or_duplicated(self):
        ledger = history.load_ledger(); pins = ledger['catalog_preservation']
        for kind, field in (('materials', 'identities'), ('materials', 'grades'), ('materials', 'records'),
                            ('reference_properties', 'records'), ('sources', 'records'), ('claims', 'records')):
            filename = 'materials_boundaries/data/' + kind + '.json'
            for mutate in (lambda rows: rows[0].update(unreviewed=True), lambda rows: rows.pop(0),
                           lambda rows: rows.append(deepcopy(rows[0])),
                           lambda rows: rows.__setitem__(slice(0, 2), list(reversed(rows[:2])))):
                current = read_catalog(kind); mutate(current[field])
                with self.assertRaises(AssertionError):
                    history.project_catalog(filename, current, pins)
        current = read_catalog('materials'); current['schema_version'] = '99.0.0'
        with self.assertRaises(AssertionError):
            history.project_catalog('materials_boundaries/data/materials.json', current, pins)
        current = read_catalog('material_locales'); label = next(iter(current['languages']['en']))
        current['languages']['en'][label] += ' altered'
        with self.assertRaises(AssertionError):
            history.project_catalog('materials_boundaries/data/material_locales.json', current, pins)

    def test_independent_catalog_appends_recover_pinned_release_without_mutating_inputs(self):
        ledger = history.load_ledger()
        for name, fields in (('materials', ('identities', 'grades', 'records')),
                            ('reference_properties', ('records',)), ('sources', ('records',)),
                            ('claims', ('records',)), ('observations', ('records',)),
                            ('computational_predictions', ('records', 'protocols', 'comparison_groups'))):
            current = read_catalog(name)
            for field in fields:
                extra = deepcopy(current[field][0]); extra['id'] = 'synthetic_append_only_' + field
                current[field].append(extra)
            saved = deepcopy(current)
            filename = 'materials_boundaries/data/' + name + '.json'
            self.assertEqual(history.release_bytes(filename, serialized(current), ledger=ledger),
                             history.release_bytes(filename, (ROOT / filename).read_bytes(), ledger=ledger))
            self.assertEqual(current, saved)
        filename = 'materials_boundaries/data/material_locales.json'
        current = read_catalog('material_locales')
        for labels in current['languages'].values():
            labels['synthetic_append_only_label'] = 'Independent synthetic test label'
        self.assertEqual(history.release_bytes(filename, serialized(current), ledger=ledger),
                         history.release_bytes(filename, (ROOT / filename).read_bytes(), ledger=ledger))

    def test_existing_catalog_only_claim_evidence_append_contract_is_retained(self):
        ledger = history.load_ledger(); filename = 'materials_boundaries/data/claims.json'
        current = read_catalog('claims')
        claim = next(r for r in current['records'] if r['id'] not in history.EXECUTABLE_IDS)
        item = deepcopy(claim['evidence'][0]); item['locator'] = 'Independent synthetic append probe'
        claim['evidence'].append(item)
        history.release_bytes(filename, serialized(current), ledger=ledger)
        claim['evidence'][0]['locator'] = 'Changed pinned evidence'
        with self.assertRaises(AssertionError):
            history.release_bytes(filename, serialized(current), ledger=ledger)
        current = read_catalog('claims')
        executable = next(r for r in current['records'] if r['id'] in history.EXECUTABLE_IDS)
        executable['evidence'].append(item)
        with self.assertRaises(AssertionError):
            history.release_bytes(filename, serialized(current), ledger=ledger)

    def test_readme_rejects_untrue_counts_changed_prose_and_missing_markers(self):
        ledger = history.load_ledger(); actual = (ROOT / 'README.md').read_bytes()
        history.release_bytes('README.md', actual, ledger=ledger)
        for bad in (actual.replace(b' material identities**', b' unsupported identities**', 1),
                    re.sub(rb'\*\*\d+ source-scoped states\*\*', b'**99999 source-scoped states**', actual),
                    actual.replace(b'<!-- material-catalog-summary:start -->', b'<!-- wrong -->'),
                    actual + b'Unreviewed prose'):
            with self.assertRaises(AssertionError):
                history.release_bytes('README.md', bad, ledger=ledger)

    def test_future_material_appends_require_truthful_live_readme_counts(self):
        ledger = history.load_ledger(); actual = (ROOT / 'README.md').read_bytes()
        canonical_release = history.release_bytes('README.md', actual, ledger=ledger)
        from materials_boundaries.material_references import material_coverage
        from test_material_reference_contract import synthetic_material_catalog
        extra_materials, extra_properties, extra_sources = synthetic_material_catalog()
        synthetic = {'materials': extra_materials, 'reference_properties': extra_properties, 'sources': extra_sources}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'materials_boundaries/data', root / 'materials_boundaries/data')
            for name, fields in (('materials', ('identities', 'grades', 'records')),
                                ('reference_properties', ('records',)), ('sources', ('records',))):
                path = root / 'materials_boundaries/data' / (name + '.json')
                value = json.loads(path.read_text(encoding='utf-8'))
                for field in fields:
                    value[field].extend(deepcopy(synthetic[name][field]))
                path.write_bytes(serialized(value))
            def catalog(name):
                return json.loads((root / 'materials_boundaries/data' / (name + '.json')).read_text(encoding='utf-8'))
            coverage = material_coverage(catalog('materials'), catalog('reference_properties'))
            text = actual.decode('utf-8')
            counts = [('material identities', coverage['material_identity_count']), ('qualified grades', coverage['grade_count']),
                      ('source-scoped states', coverage['material_state_count']), ('reference properties', coverage['property_record_count'])]
            for label, count in counts:
                text, n = re.subn(r'\*\*\d+ ' + label + r'\*\*', f'**{count} {label}**', text)
                self.assertEqual(n, 1)
            sources = catalog('sources')['records']; synthetic = sum(s['role'] == 'synthetic_demo_provenance' for s in sources)
            text = re.sub(r'\*\*\d+ source records\*\*', f'**{len(sources)} source records**', text)
            text = re.sub(r'The \d+ sources comprise \d+ bibliographic/source records plus \d+ original synthetic-demo provenance record',
                          f'The {len(sources)} sources comprise {len(sources)-synthetic} bibliographic/source records plus {synthetic} original synthetic-demo provenance record', text)
            with patch.object(history, 'ROOT', root):
                self.assertEqual(history.release_bytes('README.md', text.encode('utf-8'), ledger=ledger), canonical_release)
                with self.assertRaises(AssertionError):
                    history.release_bytes('README.md', actual, ledger=ledger)

    def test_historical_normalizer_allows_only_exact_reviewed_summary(self):
        ledger = history.load_ledger()
        actual = (ROOT / 'README.md').read_bytes()
        canonical_release = history.release_bytes('README.md', actual, ledger=ledger)
        before, _, after = history._section(actual.decode('utf-8'), 'current-catalog-summary')
        historical = ledger['readme_summaries']['historical-current-catalog-summary']
        intermediate = (before + historical + after).encode('utf-8')
        self.assertEqual(history.release_bytes('README.md', intermediate, ledger=ledger,
                                              allow_historical_summary=True), canonical_release)
        with self.assertRaises(AssertionError):
            history.release_bytes('README.md', intermediate, ledger=ledger)
        for bad in (intermediate.replace(b'mechanics claims**', b'unsupported claims**', 1),
                    re.sub(rb'\*\*\d+ source-scoped states\*\*', b'**99999 source-scoped states**', intermediate),
                    intermediate + b'Unreviewed prose'):
            with self.assertRaises(AssertionError):
                history.release_bytes('README.md', bad, ledger=ledger, allow_historical_summary=True)

    def test_nested_material_append_compares_canonical_release_not_live_readme(self):
        """Exercise the old false-failure with an already-appended outer checkout.

        The inner test must compare the normalized release with canonical bytes,
        while rejecting stale live counts. No frozen README fixture is rewritten.
        """
        from test_material_reference_contract import synthetic_material_catalog
        from materials_boundaries.material_references import material_coverage
        ledger = history.load_ledger()
        original = (ROOT / 'README.md').read_bytes()
        canonical_release = history.release_bytes('README.md', original, ledger=ledger)
        entry = next(e for e in ledger['approved_existing_updates'] if e['filename'] == 'README.md')
        self.assertEqual(history.digest(canonical_release), entry['sha256'])
        graph = synthetic_material_catalog()
        ids = {record['id'] for data in graph for rows in data.values()
               if isinstance(rows, list) for record in rows}
        mapping = {identifier: identifier + '_outer_readme_probe' for identifier in ids}
        def rename(value):
            if isinstance(value, str): return mapping.get(value, value)
            if isinstance(value, list): return [rename(item) for item in value]
            if isinstance(value, dict): return {key: rename(item) for key, item in value.items()}
            return value
        graph = rename(list(graph))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'materials_boundaries/data', root / 'materials_boundaries/data')
            def catalog(name):
                return json.loads((root / 'materials_boundaries/data' / (name + '.json')).read_text())
            for name, extra in zip(('materials', 'reference_properties', 'sources'), graph):
                current = catalog(name)
                for field, rows in extra.items():
                    if isinstance(rows, list): current[field].extend(rows)
                (root / 'materials_boundaries/data' / (name + '.json')).write_bytes(serialized(current))
            coverage = material_coverage(catalog('materials'), catalog('reference_properties'))
            text = original.decode('utf-8')
            for label, key in (('material identities', 'material_identity_count'),
                               ('qualified grades', 'grade_count'), ('source-scoped states', 'material_state_count'),
                               ('reference properties', 'property_record_count')):
                text, count = re.subn(r'\*\*\d+ ' + label + r'\*\*', f'**{coverage[key]} {label}**', text)
                self.assertEqual(count, 1)
            sources = catalog('sources')['records']
            synthetic = sum(s['role'] == 'synthetic_demo_provenance' for s in sources)
            text = re.sub(r'\*\*\d+ source records\*\*', f'**{len(sources)} source records**', text)
            text = re.sub(r'The \d+ sources comprise \d+ bibliographic/source records plus \d+ original synthetic-demo provenance record',
                          f'The {len(sources)} sources comprise {len(sources)-synthetic} bibliographic/source records plus {synthetic} original synthetic-demo provenance record', text)
            live = text.encode('utf-8')
            self.assertNotEqual(live, canonical_release)
            (root / 'README.md').write_bytes(live)
            with patch.dict(globals(), ROOT=root), patch.object(history, 'ROOT', root), \
                    patch.object(history, 'load_ledger', return_value=ledger):
                self.assertEqual(history.release_bytes('README.md', live, ledger=ledger), canonical_release)
                self.test_future_material_appends_require_truthful_live_readme_counts()
                with self.assertRaises(AssertionError):
                    history.release_bytes('README.md', original, ledger=ledger)

    def test_production_modules_have_no_test_preservation_imports(self):
        for path in (ROOT / 'materials_boundaries').glob('*.py'):
            tree = ast.parse(path.read_bytes())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or '']
                else:
                    continue
                for name in names:
                    self.assertNotIn('preservation', name, str(path))
                    self.assertFalse(name == 'tests' or name.startswith('tests.'), str(path))


if __name__ == '__main__':
    unittest.main()
