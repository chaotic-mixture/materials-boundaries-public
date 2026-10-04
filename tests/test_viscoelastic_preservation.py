"""Independent v0.26 compatibility proof anchored to the 295-file public tree."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from source_evidence_preservation import pre_evidence_bytes, previous_record
import re
import unittest

import viscoelastic_preservation as preservation
from yield_preservation import pre_yield_bytes, release_readme_bytes

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SHA256 = 'b588e3cb4d019c7b5299697e76ee05a9d3f5dfd45ed594208a564c8b26b18972'
ADAPTER_SHA256 = '041ffa7a3f67005bfe6c861c41b7a21adfa1826518b8176206e6e1f53082f832'
VERSION_ONLY = {
    'tests/test_anisotropy_catalog.py', 'tests/test_bulk_wave_catalog.py',
    'tests/test_catalog_search.py', 'tests/test_directional_compressibility_catalog.py',
    'tests/test_directional_poisson_catalog.py', 'tests/test_fatigue_catalog.py',
    'tests/test_mechanical.py', 'tests/test_mechanics_catalog_expansion.py',
    'tests/test_observation_catalog.py',
}
COMPATIBILITY_READERS = {
    'tests/test_silicon_predictions.py', 'tests/test_temperature_plot_preservation.py',
    'tests/test_pa12_preservation.py', 'tests/test_study_comparison_preservation.py',
    'tests/test_helper_lineage.py', 'tests/test_paht_test_lineage.py',
    'tests/test_nickel_prediction_batch.py',
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def declarations(source):
    """Keep every pre-existing top-level function and test method."""
    result = set()
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.add(node.name)
        elif isinstance(node, ast.ClassDef):
            result.update(node.name + '.' + item.name for item in node.body
                          if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
    return result


class ViscoelasticPreservationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = preservation.load_ledger()

    def test_independent_ledger_adapter_pins_and_exact_public_anchor(self):
        self.assertEqual(sha((ROOT / preservation.LEDGER_PATH).read_bytes()), LEDGER_SHA256)
        self.assertEqual(sha(pre_yield_bytes('tests/viscoelastic_preservation.py', (ROOT / 'tests/viscoelastic_preservation.py').read_bytes())), ADAPTER_SHA256)
        entries = preservation.validate_ledger(self.ledger)
        self.assertTrue(VERSION_ONLY | COMPATIBILITY_READERS <= set(entries))
        self.assertEqual(len(self.ledger['baseline_sha256']), 295)
        self.assertNotIn('tests/provenance_corrections.py', entries)
        self.assertFalse(any(path.startswith('tests/fixtures/') for path in entries))
        self.assertFalse(self.ledger['review']['historical_review_claimed'])

    def test_all_forty_preexisting_fixtures_and_provenance_helper_are_exact(self):
        baseline = self.ledger['baseline_sha256']
        fixtures = {path: value for path, value in baseline.items() if path.startswith('tests/fixtures/')}
        self.assertEqual(len(fixtures), 40)
        fixtures['tests/provenance_corrections.py'] = baseline['tests/provenance_corrections.py']
        for filename, expected in fixtures.items():
            with self.subTest(filename=filename):
                self.assertEqual(sha(pre_evidence_bytes(filename, (ROOT / filename).read_bytes())), expected)

    def _release_readme(self, actual):
        return pre_yield_bytes('README.md', release_readme_bytes(actual))

    def test_every_old_noncatalog_file_has_exact_accepted_bytes_or_exact_reversal(self):
        for filename, expected in self.ledger['baseline_sha256'].items():
            if filename.startswith('materials_boundaries/data/'):
                continue  # Every pre-existing object is independently checked below.
            with self.subTest(filename=filename):
                actual = (ROOT / filename).read_bytes()
                if filename == 'README.md':
                    actual = self._release_readme(actual)
                else:
                    actual = pre_yield_bytes(filename, actual)
                before = preservation.pre_viscoelastic_bytes(filename, actual)
                self.assertEqual(sha(before), expected)

    def test_every_record_locale_value_and_nonrecord_catalog_field_is_preserved(self):
        for filename, fields in self.ledger['catalog_preservation'].items():
            current = json.loads((ROOT / filename).read_text())
            if filename.endswith('/claims.json'):
                current = preservation.historical_claims_envelope(current)
            for key, baseline in fields.items():
                with self.subTest(filename=filename, field=key):
                    if 'record_digests' in baseline:
                        index = {r['id']: r for r in current[key]}
                        for identifier, expected in baseline['record_digests'].items():
                            record = previous_record(Path(filename).stem, index[identifier])
                            if 'evidence_digests' in baseline:
                                evidence = {sha(canonical(e)): e for e in record['evidence']}
                                record['evidence'] = [evidence[h] for h in baseline['evidence_digests'][identifier]]
                            self.assertEqual(sha(canonical(record)), expected, identifier)
                    elif 'locale_label_digests' in baseline:
                        for language, labels in baseline['locale_label_digests'].items():
                            for label, expected in labels.items():
                                self.assertEqual(sha(canonical(current[key][language][label])), expected, (language, label))
                    else:
                        self.assertEqual(sha(canonical(current[key])), baseline['sha256'])

    def test_test_edits_are_exact_compatibility_transformations_and_drop_no_tests(self):
        entries = preservation.validate_ledger(self.ledger)
        for filename, entry in entries.items():
            if not filename.startswith('tests/'):
                continue
            current = pre_yield_bytes(filename, (ROOT / filename).read_bytes())
            before = preservation.reverse_exact_edits(current, entry)
            self.assertEqual(declarations(before), declarations(current), filename)
            expected = before.decode()
            if filename in VERSION_ONLY:
                expected = expected.replace('1.11.0', '1.12.0')
            elif filename in COMPATIBILITY_READERS:
                expected = expected.replace('from pathlib import Path\n',
                    'from pathlib import Path\nfrom viscoelastic_preservation import pre_viscoelastic_bytes\n')
                for expr, variable in [("(ROOT / filename).read_bytes()", 'filename'),
                                       ("(ROOT / change['filename']).read_bytes()", "change['filename']")]:
                    expected = expected.replace(expr, f'pre_viscoelastic_bytes({variable}, {expr})')
                if filename.endswith('test_study_comparison_preservation.py'):
                    expected = expected.replace('from viscoelastic_preservation import pre_viscoelastic_bytes\n',
                        'from viscoelastic_preservation import pre_viscoelastic_bytes, historical_claims_envelope\n')
                    expected = expected.replace('            current = json.loads((ROOT / filename).read_text())\n',
                        "            current = json.loads((ROOT / filename).read_text())\n            if filename == 'materials_boundaries/data/claims.json':\n                current = historical_claims_envelope(current)\n")
            elif filename.endswith('test_fracture_catalog.py'):
                expected = expected.replace("    'christoffel_tensor_strong_ellipticity_v1',\n",
                    "    'christoffel_tensor_strong_ellipticity_v1',\n    'scalar_viscoelastic_creep_relaxation_duality_v1',\n")
                expected = expected.replace(
                    "            else:\n                self.assertEqual(record['evaluation_support'], 'composite_evaluate' if record['id'] in EXECUTABLE_IDS else 'catalog_only')\n",
                    "            elif record['rule_id'] == 'scalar_viscoelastic_creep_relaxation_product_bound_v1':\n"
                    "                self.assertEqual(record['claim_type'], 'theoretical_bound')\n"
                    "                self.assertEqual(record['direction'], 'interval')\n"
                    "                self.assertEqual(record['bound_kind'], 'dimensionless_response_product_bound')\n"
                    "                self.assertEqual(record['evaluation_support'], 'catalog_only')\n"
                    "                self.assertEqual(len(record['dependencies']), 1)\n"
                    "                self.assertEqual(by_id[record['dependencies'][0]]['rule_id'],\n"
                    "                                 'scalar_viscoelastic_creep_relaxation_duality_v1')\n"
                    "            else:\n                self.assertEqual(record['evaluation_support'], 'composite_evaluate' if record['id'] in EXECUTABLE_IDS else 'catalog_only')\n")
            elif filename.endswith('test_catalog_translation_snapshot.py'):
                expected = expected.replace('from materials_boundaries.catalog import query_catalog, read_catalog\n',
                    'from materials_boundaries.catalog import query_catalog, read_catalog\nfrom viscoelastic_preservation import historical_claims_envelope\n')
                expected = expected.replace('                    historic = copy.deepcopy(catalog)\n',
                    '                    historic = copy.deepcopy(catalog)\n                    if kind == "claims":\n                        historic = historical_claims_envelope(historic)\n')
            else:
                self.fail('Unspecified old-test transformation: ' + filename)
            self.assertEqual(current, expected.encode(), filename)

    def test_every_forward_reverse_round_trip_and_changed_successor_fails(self):
        for entry in self.ledger['approved_existing_updates']:
            current = (ROOT / entry['filename']).read_bytes()
            if entry['filename'] == 'README.md':
                current = self._release_readme(current)
            else:
                current = pre_yield_bytes(entry['filename'], current)
            before = preservation.reverse_exact_edits(current, entry)
            self.assertEqual(preservation.apply_exact_edits(before, entry['edits']), current)
            for bad in (current + b'\n', b'!' + current[1:]):
                with self.subTest(filename=entry['filename']), self.assertRaises(AssertionError):
                    preservation.reverse_exact_edits(bad, entry)
            broken = deepcopy(entry); broken['previous_sha256'] = '0' * 64
            with self.assertRaises(AssertionError):
                preservation.reverse_exact_edits(current, broken)

    def test_malformed_foreign_duplicate_and_forged_ledger_entries_fail(self):
        mutations = [lambda x: x.update(release='0.25.0'), lambda x: x.update(extra=True),
            lambda x: x['review'].update(historical_review_claimed=True),
            lambda x: x['baseline_sha256'].pop(next(iter(x['baseline_sha256']))),
            lambda x: x['approved_existing_updates'].append(deepcopy(x['approved_existing_updates'][0])),
            lambda x: x['approved_existing_updates'][0].update(filename='unreviewed.py'),
            lambda x: x['approved_existing_updates'][0].update(previous_sha256='0' * 64),
            lambda x: x['approved_existing_updates'][0].update(reason=''),
            lambda x: x['approved_existing_updates'][0].update(sha256='wrong')]
        for mutate in mutations:
            bad = deepcopy(self.ledger); mutate(bad)
            with self.assertRaises(AssertionError):
                preservation.validate_ledger(bad)
        with self.assertRaises(AssertionError):
            json.loads('{"a":1,"a":2}', object_pairs_hook=preservation.unique_keys)
        entry = self.ledger['approved_existing_updates'][0]
        missing = deepcopy(self.ledger); missing['approved_existing_updates'].pop(0)
        with self.assertRaises(AssertionError):
            preservation.pre_viscoelastic_bytes(entry['filename'],
                (ROOT / entry['filename']).read_bytes(), ledger=missing)
        with self.assertRaises(AssertionError):
            preservation.pre_viscoelastic_bytes('unreviewed.py', b'anything')
        with self.assertRaises(AssertionError):
            preservation.pre_viscoelastic_bytes('LICENSE', (ROOT / 'LICENSE').read_bytes() + b'!')

    def test_exact_edit_parser_rejects_bad_offsets_shapes_types_and_overlap(self):
        edits = [{'offset': 1, 'before': 'b', 'after': 'B'}, {'offset': 3, 'before': 'd', 'after': 'D'}]
        self.assertEqual(preservation.apply_exact_edits(b'abcde', edits), b'aBcDe')
        for bad in ([dict(edits[0], offset=-1)], [dict(edits[0], offset=20)],
                    [dict(edits[0], offset=True)], [dict(edits[0], before='wrong')],
                    [dict(edits[0], after='b')], list(reversed(edits)), [edits[0], edits[0]],
                    [dict(edits[0], extra=True)], [dict(edits[0], after=3)]):
            with self.subTest(edits=bad), self.assertRaises(AssertionError):
                preservation.apply_exact_edits(b'abcde', bad)

    def test_envelope_alignment_is_narrow_nonmutating_and_rejects_stale_inputs(self):
        original = {'schema_version': '1.13.0', 'records': [{'id': 'unchanged', 'value': '1.12.0'}]}
        before = deepcopy(original)
        self.assertEqual(preservation.historical_claims_envelope(original),
            {'schema_version': '1.11.0', 'records': original['records']})
        self.assertEqual(original, before)
        for version in ('1.11.0', '1.12.0', '1.14.0', None, 1.13):
            with self.assertRaises(AssertionError):
                preservation.historical_claims_envelope(dict(original, schema_version=version))


if __name__ == '__main__':
    unittest.main()
