"""Pin the dated core snapshot and preserve every older README/code contract."""
from collections import Counter
from copy import deepcopy
import importlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import material_bulk_preservation as bulk
import material_class_counts_preservation as bridge
from materials_boundaries.material_references import material_coverage
from evidence_batch_data_preservation import pre_evidence_batch_catalog_bytes, pre_evidence_batch_readme_bytes
from evidence_batch_workflow_preservation import pre_evidence_batch_workflow_bytes


ROOT = Path(__file__).resolve().parents[1]
HELPER_SHA256 = '74d3ec919c4ed769e2e0fc6b10149b27a3375f703646e10850084fed3812fe26'
BASELINE_README_SHA256 = '1f0edd6058cb7b163bc89018b3ca5cf0f5cf69d22660ec0bf1981377695036dc'
SNAPSHOT_COUNTS = {'natural': 1010, 'metal': 22, 'inorganic': 26, 'polymer': 15, 'composite': 10}
SNAPSHOT_RESOURCES = {
    'materials.json': '193f431190af502eb5c2121ff077bf59ddc9b708ae5ad786160bdc8287c83c83',
    'reference_properties.json': '03f9d1062c7e94f6c5078eea2309f016da0eac1c305fde6afeff1029757bf22d',
    'sources.json': '3d8b8c6d4891400504ea9bedbafaa06d05698b5324e9cbd7f5686ebc1ac1736f',
}


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


class MaterialClassCountsPreservationTests(unittest.TestCase):
    def test_helper_ledger_and_three_snapshot_resources_are_pinned(self):
        self.assertEqual(bridge.digest(pre_evidence_batch_workflow_bytes(
            'tests/material_class_counts_preservation.py', (ROOT / 'tests/material_class_counts_preservation.py').read_bytes())),
                         HELPER_SHA256)
        ledger = bridge.load_ledger()
        self.assertEqual(ledger['baseline_commit'], 'a592c89ede0dcced22579e56fc68b6fab4c55f49')
        self.assertEqual(ledger['snapshot']['data_commit'], bridge.DATA_COMMIT)
        self.assertEqual(ledger['snapshot']['catalog_sha256'], SNAPSHOT_RESOURCES)
        for filename, expected in SNAPSHOT_RESOURCES.items():
            self.assertEqual(bridge.digest(pre_evidence_batch_catalog_bytes(
                filename, (ROOT / 'materials_boundaries/data' / filename).read_bytes())), expected)

    def test_snapshot_sentence_matches_actual_core_classes_and_only_natural_reaches_goal(self):
        materials = json.loads(pre_evidence_batch_catalog_bytes(
            'materials.json', (ROOT / 'materials_boundaries/data/materials.json').read_bytes()))
        counts = dict(Counter(row['category'] for row in materials['identities']))
        self.assertEqual(counts, SNAPSHOT_COUNTS)
        self.assertEqual(sum(counts.values()), 1083)
        self.assertEqual([name for name, count in counts.items() if count >= 1000], ['natural'])
        ledger = bridge.load_ledger()
        self.assertEqual(ledger['snapshot']['core_category_counts'], counts)
        self.assertEqual(ledger['snapshot']['core_identity_count'], 1083)
        raw = (ROOT / 'README.md').read_bytes()
        text = pre_evidence_batch_readme_bytes(raw).decode('utf-8')
        self.assertEqual(text.count(bridge.SNAPSHOT_CLASS_SENTENCE), 1)
        self.assertNotIn(bridge.HISTORICAL_CLASS_SENTENCE, text)
        self.assertIn('**1083 material identities**', text)
        self.assertIn('**1083 source-scoped states**', text)
        self.assertIn('**1083 reference properties**', text)
        self.assertIn('experimental core snapshot', text)
        self.assertIn(bridge.DATA_COMMIT, text)
        bulk.release_bytes('README.md', raw)

    def test_wrong_class_counts_dates_duplicate_sentences_and_prose_fail_closed(self):
        raw = (ROOT / 'README.md').read_bytes()
        mutations = (
            raw.replace(b'metal 22', b'metal 34'),
            raw.replace(b'inorganic 26', b'inorganic 38'),
            raw.replace(b'polymer 15', b'polymer 16'),
            raw.replace(b'composite 10', b'composite 9'),
            raw.replace(b'natural 1,010', b'natural 1,011'),
            raw.replace(b'2026-10-19 experimental core snapshot', b'2026-10-20 experimental core snapshot'),
            raw.replace(bridge.DATA_COMMIT.encode(), b'0' * 40),
            raw.replace(b'Only natural reaches', b'Every class reaches'),
            raw + bridge.SNAPSHOT_CLASS_SENTENCE.encode(),
            raw.replace(bridge.SNAPSHOT_CLASS_SENTENCE.encode(), bridge.HISTORICAL_CLASS_SENTENCE.encode()),
            raw + b'Unreviewed prose',
        )
        for index, changed in enumerate(mutations):
            with self.subTest(mutation=index):
                with self.assertRaises(AssertionError):
                    bulk.release_bytes('README.md', changed)

    def test_readme_exact_recovery_and_all_seven_original_material_chains(self):
        raw = (ROOT / 'README.md').read_bytes()
        previous = bridge.pre_class_counts_bytes('README.md', raw)
        self.assertEqual(bridge.digest(previous), BASELINE_README_SHA256)
        self.assertIn(b'**1079 material identities**', previous)
        self.assertIn(bridge.HISTORICAL_CLASS_SENTENCE.encode(), previous)
        self.assertEqual(bridge.normalize_readme_snapshot(previous), previous.decode('utf-8'))
        for module_name, function in (
            ('material_bulk_preservation', 'pre_material_bulk_bytes'),
            ('material_polymer_preservation', 'pre_material_polymer_bytes'),
            ('material_porous_preservation', 'pre_material_porous_bytes'),
            ('material_measures_preservation', 'pre_material_measures_bytes'),
            ('material_fiber_preservation', 'pre_material_fiber_bytes'),
            ('material_batch_preservation', 'pre_material_batch_bytes'),
            ('material_catalog_preservation', 'pre_material_bytes'),
        ):
            with self.subTest(layer=module_name):
                module = importlib.import_module(module_name)
                recovered = getattr(module, function)('README.md', raw)
                self.assertEqual(bridge.digest(recovered), module.load_ledger()['baseline_sha256']['README.md'])

    def test_snapshot_is_fixed_while_marked_totals_follow_an_append_rehearsal(self):
        from test_material_reference_contract import synthetic_material_catalog
        original = (ROOT / 'README.md').read_bytes()
        expected = bulk.release_bytes('README.md', original)
        extra = synthetic_material_catalog()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'materials_boundaries/data'
            shutil.copytree(ROOT / 'materials_boundaries/data', folder)
            graphs = {}
            for name, append in zip(('materials', 'reference_properties', 'sources'), extra):
                path = folder / (name + '.json')
                graphs[name] = json.loads(path.read_text(encoding='utf-8'))
                for field, rows in append.items():
                    if isinstance(rows, list):
                        graphs[name][field].extend(deepcopy(rows))
                path.write_bytes(serialized(graphs[name]))
            coverage = material_coverage(graphs['materials'], graphs['reference_properties'])
            text = original.decode('utf-8')
            for label, key in (('material identities', 'material_identity_count'),
                               ('qualified grades', 'grade_count'),
                               ('source-scoped states', 'material_state_count'),
                               ('reference properties', 'property_record_count')):
                text, count = re.subn(r'\*\*\d+ ' + label + r'\*\*', f'**{coverage[key]} {label}**', text)
                self.assertEqual(count, 1)
            sources = graphs['sources']['records']
            synthetic = sum(item['role'] == 'synthetic_demo_provenance' for item in sources)
            text = re.sub(r'\*\*\d+ source records\*\*', f'**{len(sources)} source records**', text)
            text = re.sub(r'The \d+ sources comprise \d+ bibliographic/source records plus \d+ original synthetic-demo provenance record',
                          f'The {len(sources)} sources comprise {len(sources)-synthetic} bibliographic/source records plus {synthetic} original synthetic-demo provenance record', text)
            self.assertEqual(text.count(bridge.SNAPSHOT_CLASS_SENTENCE), 1)
            self.assertEqual(bulk.release_bytes('README.md', text.encode('utf-8'), root=root), expected)
            with self.assertRaises(AssertionError):
                bulk.release_bytes('README.md', original, root=root)

    def test_five_exact_predecessors_round_trip_including_ci_and_helpers(self):
        entries = bridge.validate_ledger(bridge.load_ledger())
        self.assertEqual(set(entries), {
            'README.md', '.github/workflows/ci.yml', 'tests/material_bulk_preservation.py',
            'tests/presentation_fast_path_preservation.py', 'tests/test_presentation_fast_path_preservation.py',
        })
        for filename, entry in entries.items():
            with self.subTest(filename=filename):
                current = (ROOT / filename).read_bytes()
                if filename == 'README.md':
                    current = pre_evidence_batch_readme_bytes(current)
                elif filename == '.github/workflows/ci.yml':
                    current = pre_evidence_batch_workflow_bytes(filename, current)
                previous = bridge.pre_class_counts_bytes(filename, current)
                self.assertEqual(bridge.digest(current), entry['sha256'])
                self.assertEqual(bridge.digest(previous), entry['previous_sha256'])
                self.assertEqual(bridge.apply_exact_edits(previous, entry['edits']), current)
                self.assertEqual(bridge.pre_class_counts_bytes(filename, previous), previous)

    def test_changed_bytes_paths_types_and_before_images_cannot_use_the_bridge(self):
        for filename, entry in bridge.validate_ledger(bridge.load_ledger()).items():
            current = (ROOT / filename).read_bytes()
            previous = bridge.pre_class_counts_bytes(filename, current)
            for changed in (current + b'!', current[:-1], b'arbitrary', current.decode('utf-8'),
                            bytearray(current), memoryview(current)):
                with self.subTest(filename=filename, input_type=type(changed).__name__):
                    with self.assertRaises(AssertionError):
                        bridge.pre_class_counts_bytes(filename, changed)
            for mutate in (lambda x: x[0].update(offset=True),
                           lambda x: x[0].update(offset=len(previous) + 1),
                           lambda x: x[0].update(before=x[0]['before'] + '!'),
                           lambda x: x.append(deepcopy(x[0]))):
                edits = deepcopy(entry['edits'])
                mutate(edits)
                with self.assertRaises(AssertionError):
                    bridge.apply_exact_edits(previous, edits)
        for filename in ('../README.md', 'materials_boundaries/data/materials.json', None, []):
            with self.assertRaises(AssertionError):
                bridge.pre_class_counts_bytes(filename, b'unknown')

    def test_all_old_ledgers_remain_unchanged_and_new_ledger_mutations_fail(self):
        original = bridge.load_ledger()
        for filename, expected in original['preserved_ledger_sha256'].items():
            self.assertEqual(bridge.digest((ROOT / filename).read_bytes()), expected)
        for mutate in (
            lambda x: x.update(extra=True),
            lambda x: x.update(schema_version=True),
            lambda x: x.update(baseline_commit='0' * 40),
            lambda x: x['updates'].pop(),
            lambda x: x['updates'].append(deepcopy(x['updates'][0])),
            lambda x: x['updates'][0].update(sha256='0' * 64),
            lambda x: x['updates'][0]['edits'][0].update(offset=True),
            lambda x: x['snapshot']['core_category_counts'].update(composite=11),
            lambda x: x['preserved_ledger_sha256'].clear(),
        ):
            changed = deepcopy(original)
            mutate(changed)
            with self.assertRaises(AssertionError):
                bridge.validate_ledger(changed)
        with self.assertRaises(AssertionError):
            bridge.unique_keys([('updates', []), ('updates', [])])
        self.assertEqual(bridge.load_ledger(), original)


if __name__ == '__main__':
    unittest.main()
