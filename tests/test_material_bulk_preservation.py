"""v0.35 exact predecessor recovery, finite migration and fresh-graph guards.

The predecessor is the independently retained 402-file accepted v0.34 tree.
No old fixture is regenerated. Admission pins protect complete selected new
objects, while the predecessor layer permits unrelated append-only growth.
"""
import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import material_bulk_preservation as history
from materials_boundaries.catalog import read_catalog
from materials_boundaries import material_references as references

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SHA256 = 'fa5b5d010dff9dd12e859a41ad02077b5350acc01bac50d001e1fa48184747d4'
HELPER_SHA256 = '19c340da6daff24910d271b81dec3fc24bd8c5a87bc4b3a7f6514fa7cc289b27'
ADMISSION_SHA256 = '8bb9e093c02de51723ee62efa37fcbc226cf2fb41eba0a284145e0ebf5ea7a1d'


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def declarations(raw):
    tree = ast.parse(raw)
    return {node.name + '.' + item.name for node in tree.body if isinstance(node, ast.ClassDef)
            for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))} | {
            node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


class MaterialBulkPreservationTests(unittest.TestCase):
    def test_accepted_tree_ledger_helper_and_admission_are_pinned(self):
        for filename, expected in ((history.LEDGER_PATH, LEDGER_SHA256),
                                   ('tests/material_bulk_preservation.py', HELPER_SHA256),
                                   (history.ADMISSION_PATH, ADMISSION_SHA256)):
            self.assertEqual(history.digest((ROOT / filename).read_bytes()), expected)
        ledger = history.load_ledger()
        history.validate_ledger(ledger)
        self.assertEqual(ledger['baseline_commit'], '7e37be919ee97f1275249dcf745f9f55e951986a')
        self.assertEqual(ledger['baseline_tree'], '98b67e0632fb0595079c6c11b78c202c53dda0ac')
        self.assertEqual(len(ledger['baseline_sha256']), 402)

    def test_all_402_predecessor_files_round_trip_exactly(self):
        ledger = history.load_ledger(); entries = history.validate_ledger(ledger)
        for filename, expected in ledger['baseline_sha256'].items():
            with self.subTest(filename=filename):
                actual = (ROOT / filename).read_bytes()
                release = history.release_bytes(filename, actual, ledger=ledger)
                previous = history.pre_material_bulk_bytes(filename, actual, ledger=ledger)
                self.assertEqual(history.digest(previous), expected)
                self.assertEqual(history.apply_exact_edits(previous, entries[filename]['edits'])
                                 if filename in entries else previous, release)
                if filename.startswith(('tests/fixtures/', 'examples/')) or filename == 'materials_boundaries/engine.py':
                    self.assertEqual(actual, previous)
                if filename.startswith('tests/') and filename.endswith('.py'):
                    self.assertLessEqual(declarations(previous), declarations(actual))

    def test_exact_edits_reject_changed_successor_before_image_and_offsets(self):
        ledger = history.load_ledger()
        for entry in ledger['approved_existing_updates']:
            with self.subTest(filename=entry['filename']):
                current = history.release_bytes(entry['filename'], (ROOT / entry['filename']).read_bytes(), ledger=ledger)
                previous = history.reverse_exact_edits(current, entry)
                self.assertEqual(history.apply_exact_edits(previous, entry['edits']), current)
                for bad in (current + b'!', b'unreviewed replacement'):
                    with self.assertRaises((AssertionError, ValueError)):
                        history.pre_material_bulk_bytes(entry['filename'], bad, ledger=ledger)
                wrong = deepcopy(entry['edits']); wrong[0]['before'] += 'unreviewed'
                with self.assertRaises(AssertionError):
                    history.apply_exact_edits(previous, wrong)
        with self.assertRaises(AssertionError):
            history.pre_material_bulk_bytes('../README.md', b'unknown', ledger=ledger)

    def test_malformed_incomplete_duplicate_and_foreign_ledgers_are_rejected(self):
        mutations = [lambda x: x.update(extra=True), lambda x: x.update(schema_version=True),
                     lambda x: x.update(baseline_commit='0' * 40), lambda x: x.update(baseline_tree='0' * 40),
                     lambda x: x['baseline_sha256'].pop('LICENSE'),
                     lambda x: x['approved_existing_updates'].pop(),
                     lambda x: x['approved_existing_updates'].append(deepcopy(x['approved_existing_updates'][0])),
                     lambda x: x['approved_existing_updates'][0].update(filename='foreign.py'),
                     lambda x: x['approved_existing_updates'][0].update(previous_sha256='0' * 64),
                     lambda x: x['approved_existing_updates'][0].update(reason=' '),
                     lambda x: x['approved_existing_updates'][0]['edits'][0].update(offset=True),
                     lambda x: x['catalog_preservation'].pop('materials_boundaries/data/materials.json')]
        for mutate in mutations:
            ledger = deepcopy(history.load_ledger()); mutate(ledger)
            with self.assertRaises(AssertionError): history.validate_ledger(ledger)
        with self.assertRaises(AssertionError):
            json.loads('{"duplicate":1,"duplicate":2}', object_pairs_hook=history.unique_keys)

    def test_every_retained_object_metadata_and_label_is_checked_before_projection(self):
        ledger = history.load_ledger()
        for kind, field in (('materials', 'identities'), ('materials', 'grades'), ('materials', 'records'),
                            ('reference_properties', 'records'), ('sources', 'records'), ('claims', 'records')):
            filename = 'materials_boundaries/data/' + kind + '.json'
            for mutate in (lambda rows: rows[0].update(unreviewed=True), lambda rows: rows.pop(0),
                           lambda rows: rows.append(deepcopy(rows[0])),
                           lambda rows: rows.__setitem__(slice(0, 2), list(reversed(rows[:2])))):
                current = read_catalog(kind); mutate(current[field])
                with self.assertRaises(AssertionError):
                    history.project_catalog(filename, current, ledger['catalog_preservation'])
        current = read_catalog('materials'); current['schema_version'] = '99.0.0'
        with self.assertRaises(AssertionError):
            history.project_catalog('materials_boundaries/data/materials.json', current, ledger['catalog_preservation'])
        current = read_catalog('material_locales'); current['languages']['en']['unknown_notice'] += ' omitted'
        with self.assertRaises(AssertionError):
            history.project_catalog('materials_boundaries/data/material_locales.json', current, ledger['catalog_preservation'])

    def test_independent_suffix_appends_do_not_mutate_or_hide_retained_data(self):
        ledger = history.load_ledger()
        for kind, field in (('materials', 'records'), ('reference_properties', 'records'),
                            ('sources', 'records'), ('observations', 'records')):
            filename = 'materials_boundaries/data/' + kind + '.json'
            current = read_catalog(kind); extra = deepcopy(current[field][0]); extra['id'] = 'synthetic_independent_append'
            current[field].append(extra); before = deepcopy(current)
            self.assertEqual(history.release_bytes(filename, serialized(current), ledger=ledger),
                             history.release_bytes(filename, (ROOT / filename).read_bytes(), ledger=ledger))
            self.assertEqual(current, before)
            current[field][0]['unreviewed'] = True
            with self.assertRaises(AssertionError):
                history.release_bytes(filename, serialized(current), ledger=ledger)

    def test_new_admissions_pin_complete_objects_without_a_live_registry_ceiling(self):
        admission = json.loads((ROOT / history.ADMISSION_PATH).read_text(encoding='utf-8'))
        self.assertEqual(admission['baseline_commit'], history.BASELINE_COMMIT)
        self.assertEqual(admission['taxonomy_migration_sha256'],
                         history.digest((ROOT / 'materials_boundaries/data/taxonomy_migration_v1.json').read_bytes()))
        admitted = admission['admitted_record_digests']
        for kind, fields in admitted.items():
            current = read_catalog(kind)
            for field, pins in fields.items():
                index = {r['id']: r for r in current[field]}
                self.assertEqual(len(index), len(current[field]))
                for key, expected in pins.items():
                    self.assertEqual(history.digest(history.canonical(index[key])), expected)
        for kind, field in (('materials', 'identities'), ('materials', 'records'), ('reference_properties', 'records')):
            self.assertEqual(len(admitted[kind][field]), 1000)
        for kind, languages in admission['admitted_label_digests'].items():
            current = read_catalog(kind)['languages']
            for language, pins in languages.items():
                for key, expected in pins.items():
                    self.assertEqual(history.digest(history.canonical(current[language][key])), expected)

    def test_bridge_restores_only_the_pinned_finite_taxonomy_and_labels(self):
        ledger = history.load_ledger()
        for kind in ('materials', 'reference_properties', 'material_locales'):
            filename = 'materials_boundaries/data/' + kind + '.json'
            current = read_catalog(kind); before = deepcopy(current)
            previous = history.predecessor_catalog(filename, current)
            self.assertEqual(history.digest(history.pre_material_bulk_bytes(filename, serialized(previous))),
                             ledger['baseline_sha256'][filename])
            self.assertEqual(current, before)
        current = read_catalog('materials')
        target = next(r for r in current['identities'] if r['id'] == 'mat_usda_sugar_maple')
        target['identity_scope'] += ' unreviewed scientific claim'
        with self.assertRaises(AssertionError):
            history.predecessor_catalog('materials_boundaries/data/materials.json', current)

    def test_readme_counts_and_noncount_prose_remain_checked(self):
        actual = (ROOT / 'README.md').read_bytes()
        history.release_bytes('README.md', actual)
        for bad in (actual + b'Unreviewed prose',
                    actual.replace(b' material identities**', b' unsupported identities**', 1),
                    actual.replace(b'<!-- material-catalog-summary:start -->', b'<!-- wrong -->')):
            with self.assertRaises(AssertionError): history.release_bytes('README.md', bad)

    def test_no_production_module_imports_test_preservation(self):
        for path in (ROOT / 'materials_boundaries').glob('*.py'):
            self.assertNotIn('material_bulk_preservation', path.read_text(encoding='utf-8'))


class FreshGraphResolutionTests(unittest.TestCase):
    def graph(self):
        from test_material_catalog_views import synthetic_catalogs
        values = synthetic_catalogs()
        return values['materials'], values['reference_properties'], values['sources']

    def test_one_validation_per_operation_and_fresh_validation_on_repeat(self):
        materials, properties, sources = self.graph()
        ids = [r['id'] for r in materials['records']]
        with patch.object(references, 'validate_material_catalog', wraps=references.validate_material_catalog) as validate:
            first = references.resolve_materials(ids, materials, properties, sources)
            self.assertEqual(validate.call_count, 1)
            second = references.resolve_materials(ids, materials, properties, sources)
            self.assertEqual(validate.call_count, 2)
            self.assertEqual(first, second)
            properties['records'][-1]['engineering_allowable'] = True
            with self.assertRaises(ValueError): references.resolve_materials([ids[0]], materials, properties, sources)
            self.assertEqual(validate.call_count, 3)

    def test_no_cached_success_after_any_graph_component_is_mutated(self):
        mutations = ((0, lambda x: x['identities'][-1].update(category='invented')),
                     (0, lambda x: x['records'][-1].update(property_ids=[])),
                     (1, lambda x: x['records'][-1]['reported_value'].update(number='-1')),
                     (2, lambda x: x['records'][-1].update(urls=[])))
        for index, mutate in mutations:
            graph = self.graph(); state = graph[0]['records'][0]['id']
            references.resolve_materials([state], *graph)
            mutate(graph[index])
            with self.assertRaises(ValueError): references.resolve_materials([state], *graph)

    def test_results_are_detached_and_ordered_and_do_not_mutate_inputs(self):
        graph = self.graph(); before = deepcopy(graph)
        ids = [r['id'] for r in graph[0]['records']][::-1]
        result = references.resolve_materials(ids, *graph)
        self.assertEqual([r['state']['id'] for r in result], ids)
        result[0]['properties'][0]['reported_value']['number'] = '99999'
        result[0]['identity']['category'] = 'invented'
        self.assertEqual(graph, before)
        self.assertNotEqual(references.resolve_materials(ids, *graph), result)


class ExactOutputMigrationTests(unittest.TestCase):
    def test_output_ledger_is_finite_and_anchored_to_untouched_v034_snapshot(self):
        ledger = history.load_output_ledger()
        self.assertEqual(ledger['baseline_commit'], history.BASELINE_COMMIT)
        self.assertEqual(ledger['baseline_tree'], history.BASELINE_TREE)
        self.assertEqual(len(ledger['output_sha256']), 912)
        self.assertEqual(len(ledger['approved_output_updates']), 148)
        self.assertEqual(len({item['identity_id'] for item in ledger['approved_output_updates']}), 10)
        fixture = json.loads((ROOT / 'tests/fixtures/material_polymer_outputs_v0340.json').read_text())
        expected = {}
        for case in fixture['old_details'] + fixture['admitted_details']:
            for language, formats in case['languages'].items():
                for format, digest in formats.items():
                    key = '|'.join((case['kind'], case['id'], case['source_id'], language, format.removesuffix('_sha256')))
                    expected[key] = digest
        self.assertEqual({key: pins['before_sha256'] for key, pins in ledger['output_sha256'].items()}, expected)
        self.assertEqual(sum(pins['before_sha256'] == pins['after_sha256'] for pins in ledger['output_sha256'].values()), 764)
        self.assertEqual(ledger['taxonomy_ledger_sha256'], history.digest((ROOT / 'materials_boundaries/data/taxonomy_migration_v1.json').read_bytes()))

    def test_each_migration_has_exact_reversible_nonempty_byte_edits(self):
        ledger = history.load_output_ledger()
        keys = set()
        for entry in ledger['approved_output_updates']:
            self.assertNotIn(entry['filename'], keys); keys.add(entry['filename'])
            history.validate_edits(entry['edits'])
            pins = ledger['output_sha256'][entry['filename']]
            self.assertEqual(entry['previous_sha256'], pins['before_sha256'])
            self.assertEqual(entry['sha256'], pins['after_sha256'])
            self.assertNotEqual(entry['previous_sha256'], entry['sha256'])
            with self.assertRaises(AssertionError):
                history.predecessor_output(*entry['filename'].split('|'), 'unreviewed replacement')

    def test_source_fidelity_bridge_drops_no_unlisted_field(self):
        current = read_catalog('materials')
        identity = next(r for r in current['identities'] if r['id'] == 'mat_usda_sugar_maple')
        changed = deepcopy(identity); changed['extra_metadata'] = {'must': 'survive'}
        previous = history.predecessor_record('materials', 'identities', changed)
        self.assertEqual(previous['extra_metadata'], changed['extra_metadata'])
        self.assertEqual(previous['category'], 'composite')
        self.assertEqual(changed['category'], 'natural')
        changed['category'] = 'polymer'
        with self.assertRaises(AssertionError): history.predecessor_record('materials', 'identities', changed)


class InstalledWheelAppendGuardTests(unittest.TestCase):
    def guard(self):
        from scripts.check_wheel_metadata import INSTALLED_CHECK, require
        from materials_boundaries._pa12_cf15_observation_contract import PA12_FAMILY
        tree = ast.parse(INSTALLED_CHECK)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'historical_observation_rows')
        scope = {'require': require, 'PA12_FAMILY': PA12_FAMILY}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<installed observation guard>', 'exec'), scope)
        return scope['historical_observation_rows']

    def test_exact_historical_cohorts_survive_unrelated_mixed_appends(self):
        rows = read_catalog('observations')['records']
        baseline, old, pa12 = self.guard()(rows)
        extra = deepcopy(old[0]); extra['id'] = 'synthetic_independent_wheel_observation'
        self.assertEqual(self.guard()(list(reversed(rows)) + [extra]), (baseline, old, pa12))
        self.assertEqual((len(baseline), len(old), len(pa12)), (16, 6, 6))

    def test_each_missing_historical_id_duplicate_or_relabel_is_rejected(self):
        rows = read_catalog('observations')['records']; guard = self.guard()
        baseline, old, pa12 = guard(rows)
        for item in baseline:
            with self.assertRaises(RuntimeError): guard([r for r in rows if r['id'] != item['id']])
        with self.assertRaises(RuntimeError): guard(rows + [deepcopy(rows[0])])
        for target, field in ((old[0], 'observation_type'), (pa12[0], 'method_family')):
            changed = deepcopy(rows)
            next(r for r in changed if r['id'] == target['id'])[field] = 'unreviewed'
            with self.assertRaises(RuntimeError): guard(changed)
