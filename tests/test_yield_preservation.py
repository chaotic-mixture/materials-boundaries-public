"""Independent v0.27 compatibility proof anchored to the 302-file public tree."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest

import yield_preservation as preservation

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SHA256 = '98f60054354141c6a37e58961a2826daac2590c333f121d047e1d621b89c78a7'
ADAPTER_SHA256 = '1d6a67066b77636f71cbd5df4ae61ef8d8dece007bdaa4f7607e7810080f06d7'
VERSION_ONLY = {
    'tests/test_anisotropy_catalog.py', 'tests/test_bulk_wave_catalog.py',
    'tests/test_catalog_search.py', 'tests/test_directional_compressibility_catalog.py',
    'tests/test_directional_poisson_catalog.py', 'tests/test_fatigue_catalog.py',
    'tests/test_mechanical.py', 'tests/test_mechanics_catalog_expansion.py',
    'tests/test_observation_catalog.py', 'tests/test_viscoelastic_catalog.py',
}
COMPATIBILITY_READERS = {
    'tests/test_fracture_catalog.py', 'tests/viscoelastic_preservation.py',
    'tests/test_viscoelastic_preservation.py',
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


def expected_compatibility_update(filename, before):
    """Only reviewed schema-envelope and exact lineage-bridge edits are allowed."""
    if filename in VERSION_ONLY:
        return before.replace('1.12.0', '1.13.0')
    if filename == 'tests/test_fracture_catalog.py':
        s = before
        s=s.replace("    'scalar_viscoelastic_creep_relaxation_duality_v1',\n", "    'scalar_viscoelastic_creep_relaxation_duality_v1',\n    'von_mises_initial_yield_relation_v1', 'tresca_initial_yield_relation_v1',\n")
        s=s.replace("            else:\n                self.assertEqual(record['evaluation_support'], 'composite_evaluate' if record['id'] in EXECUTABLE_IDS else 'catalog_only')\n", "            elif record['rule_id'] == 'tresca_von_mises_equivalent_stress_ratio_bound_v1':\n                self.assertEqual(record['claim_type'], 'theoretical_bound')\n                self.assertEqual(record['direction'], 'interval')\n                self.assertEqual(record['bound_kind'], 'criterion_function_comparison')\n                self.assertEqual(record['evaluation_support'], 'catalog_only')\n                self.assertEqual(len(record['dependencies']), 2)\n                self.assertEqual({by_id[dependency]['rule_id'] for dependency in record['dependencies']},\n                                 {'von_mises_initial_yield_relation_v1', 'tresca_initial_yield_relation_v1'})\n            else:\n                self.assertEqual(record['evaluation_support'], 'composite_evaluate' if record['id'] in EXECUTABLE_IDS else 'catalog_only')\n")
        return s
    if filename == 'tests/viscoelastic_preservation.py':
        s = before
        s=s.replace('from pathlib import Path\n','from pathlib import Path\nfrom yield_preservation import pre_yield_bytes, historical_claims_envelope as pre_yield_envelope\n')
        s=s.replace("    entries = validate_ledger(ledger)\n    if filename in entries:\n", "    entries = validate_ledger(ledger)\n    accepted = entries[filename]['sha256'] if filename in entries else ledger['baseline_sha256'].get(filename)\n    if digest(current) != accepted:\n        current = pre_yield_bytes(filename, current)\n    if filename in entries:\n")
        s=s.replace("    if catalog.get('schema_version') != '1.12.0':\n", "    catalog = pre_yield_envelope(catalog)\n    if catalog.get('schema_version') != '1.12.0':\n")
        return s
    if filename == 'tests/test_viscoelastic_preservation.py':
        s = before
        s=s.replace('import viscoelastic_preservation as preservation\n','import viscoelastic_preservation as preservation\nfrom yield_preservation import pre_yield_bytes, release_readme_bytes\n')
        s=s.replace("sha((ROOT / 'tests/viscoelastic_preservation.py').read_bytes())", "sha(pre_yield_bytes('tests/viscoelastic_preservation.py', (ROOT / 'tests/viscoelastic_preservation.py').read_bytes()))")
        lines=s.splitlines(keepends=True)
        node=next(n for cls in ast.parse(s).body if isinstance(cls,ast.ClassDef) for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_release_readme')
        lines[node.lineno-1:node.end_lineno]=['    def _release_readme(self, actual):\n', "        return pre_yield_bytes('README.md', release_readme_bytes(actual))\n"]
        s=''.join(lines)
        s=s.replace("                if filename == 'README.md':\n                    actual = self._release_readme(actual)\n", "                if filename == 'README.md':\n                    actual = self._release_readme(actual)\n                else:\n                    actual = pre_yield_bytes(filename, actual)\n")
        s=s.replace("            current = (ROOT / filename).read_bytes()\n            before = preservation.reverse_exact_edits(current, entry)\n", "            current = pre_yield_bytes(filename, (ROOT / filename).read_bytes())\n            before = preservation.reverse_exact_edits(current, entry)\n")
        s=s.replace("            if entry['filename'] == 'README.md':\n                current = self._release_readme(current)\n", "            if entry['filename'] == 'README.md':\n                current = self._release_readme(current)\n            else:\n                current = pre_yield_bytes(entry['filename'], current)\n")
        s=s.replace("original = {'schema_version': '1.12.0',", "original = {'schema_version': '1.13.0',")
        s=s.replace("for version in ('1.11.0', '1.13.0', None, 1.12):", "for version in ('1.11.0', '1.12.0', '1.14.0', None, 1.13):")
        return s
    raise AssertionError('Unspecified old-test transformation: ' + filename)


class YieldPreservationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = preservation.load_ledger()

    def test_independent_ledger_adapter_pins_and_exact_public_anchor(self):
        self.assertEqual(sha((ROOT / preservation.LEDGER_PATH).read_bytes()), LEDGER_SHA256)
        self.assertEqual(sha((ROOT / 'tests/yield_preservation.py').read_bytes()), ADAPTER_SHA256)
        entries = preservation.validate_ledger(self.ledger)
        self.assertTrue(VERSION_ONLY | COMPATIBILITY_READERS <= set(entries))
        self.assertEqual(len(self.ledger['baseline_sha256']), 302)
        self.assertNotIn('tests/provenance_corrections.py', entries)
        self.assertFalse(any(path.startswith('tests/fixtures/') for path in entries))
        self.assertFalse(self.ledger['review']['historical_review_claimed'])

    def test_all_forty_one_preexisting_fixtures_and_provenance_helper_are_exact(self):
        baseline = self.ledger['baseline_sha256']
        fixtures = {path: value for path, value in baseline.items() if path.startswith('tests/fixtures/')}
        self.assertEqual(len(fixtures), 41)
        fixtures['tests/provenance_corrections.py'] = baseline['tests/provenance_corrections.py']
        for filename, expected in fixtures.items():
            with self.subTest(filename=filename):
                self.assertEqual(sha((ROOT / filename).read_bytes()), expected)

    def _release_readme(self, actual):
        # Rehearsals update only the exact current-summary count statements.
        text = actual.decode()
        start, end = '<!-- current-catalog-summary:start -->', '<!-- current-catalog-summary:end -->'
        self.assertEqual(text.count(start), 1); self.assertEqual(text.count(end), 1)
        before, selected = text.split(start); summary, after = selected.split(end)
        release = self.ledger['release_readme_summary']
        def catalog(name):
            return json.loads((ROOT / 'materials_boundaries/data' / (name + '.json')).read_text())
        claims, sources, observations = (catalog(name)['records'] for name in ('claims', 'sources', 'observations'))
        predictions = catalog('computational_predictions')
        demos = [r for r in catalog('temperature_models')['records'] if r['classification'] == 'synthetic_demo']
        synthetic = sum(r['role'] == 'synthetic_demo_provenance' for r in sources)
        pairs = [
            (r'\*\*\d+ mechanics claims\*\*', f'**{len(claims)} mechanics claims**'),
            (r'\*\*\d+ source records\*\*', f'**{len(sources)} source records**'),
            (r'\*\*\d+ observations from \d+ studies\*\*', f'**{len(observations)} observations from {len({r["study_id"] for r in observations})} studies**'),
            (r'\*\*\d+ published computational predictions in \d+ scientific families and \d+ explicit groups\*\*',
             f'**{len(predictions["records"])} published computational predictions in {len({p["family"] for p in predictions["protocols"]})} scientific families and {len(predictions["comparison_groups"])} explicit groups**'),
            (r'\*\*\d+ synthetic temperature demos with \d+ branches\*\*', f'**{len(demos)} synthetic temperature demos with {sum(len(r["branches"]) for r in demos)} branches**'),
            (r'The \d+ sources comprise \d+ bibliographic/source records plus \d+ original synthetic-demo provenance record',
             f'The {len(sources)} sources comprise {len(sources)-synthetic} bibliographic/source records plus {synthetic} original synthetic-demo provenance record'),
        ]
        expected = release
        for pattern, value in pairs:
            expected, count = re.subn(pattern, lambda match: value, expected)
            self.assertEqual(count, 1, pattern)
        self.assertEqual(summary, expected, 'only truthful current-summary counts may differ in a rehearsal')
        result = (before + start + release + end + after).encode()
        self.assertEqual(preservation.release_readme_bytes(actual), result)
        return result

    def test_every_old_noncatalog_file_has_exact_accepted_bytes_or_exact_reversal(self):
        for filename, expected in self.ledger['baseline_sha256'].items():
            if filename.startswith('materials_boundaries/data/'):
                continue  # Every pre-existing object is independently checked below.
            with self.subTest(filename=filename):
                actual = (ROOT / filename).read_bytes()
                if filename == 'README.md':
                    actual = self._release_readme(actual)
                before = preservation.pre_yield_bytes(filename, actual)
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
                            record = deepcopy(index[identifier])
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
            current = (ROOT / filename).read_bytes()
            before = preservation.reverse_exact_edits(current, entry)
            self.assertEqual(declarations(before), declarations(current), filename)
            self.assertEqual(current, expected_compatibility_update(filename, before.decode()).encode(), filename)

    def test_every_forward_reverse_round_trip_and_changed_successor_fails(self):
        for entry in self.ledger['approved_existing_updates']:
            current = (ROOT / entry['filename']).read_bytes()
            if entry['filename'] == 'README.md':
                current = self._release_readme(current)
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
            preservation.pre_yield_bytes(entry['filename'],
                (ROOT / entry['filename']).read_bytes(), ledger=missing)
        with self.assertRaises(AssertionError):
            preservation.pre_yield_bytes('unreviewed.py', b'anything')
        with self.assertRaises(AssertionError):
            preservation.pre_yield_bytes('LICENSE', (ROOT / 'LICENSE').read_bytes() + b'!')

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
        original = {'schema_version': '1.13.0', 'records': [{'id': 'unchanged', 'value': '1.13.0'}]}
        before = deepcopy(original)
        self.assertEqual(preservation.historical_claims_envelope(original),
            {'schema_version': '1.12.0', 'records': original['records']})
        self.assertEqual(original, before)
        for version in ('1.11.0', '1.12.0', '1.14.0', None, 1.13):
            with self.assertRaises(AssertionError):
                preservation.historical_claims_envelope(dict(original, schema_version=version))

    def test_legacy_chain_is_exact_and_unreviewed_bytes_fail_closed(self):
        import viscoelastic_preservation as old
        previous = old.load_ledger()
        for filename, entry in preservation.validate_ledger(self.ledger).items():
            if filename not in previous['baseline_sha256']:
                continue
            actual = (ROOT / filename).read_bytes()
            if filename == 'README.md':
                actual = self._release_readme(actual)
            accepted = preservation.pre_yield_bytes(filename, actual)
            original = old.pre_viscoelastic_bytes(filename, actual)
            self.assertEqual(original, old.pre_viscoelastic_bytes(filename, accepted), filename)
            self.assertEqual(sha(original), previous['baseline_sha256'][filename], filename)
            with self.assertRaises(AssertionError):
                old.pre_viscoelastic_bytes(filename, actual + b'!')
        self.assertEqual(sha((ROOT / old.LEDGER_PATH).read_bytes()),
                         self.ledger['baseline_sha256'][old.LEDGER_PATH])

    def test_readme_normalization_rejects_untrue_counts_and_summary_prose_changes(self):
        actual = (ROOT / 'README.md').read_bytes()
        normalized = preservation.release_readme_bytes(actual)
        self.assertEqual(sha(preservation.pre_yield_bytes('README.md', normalized)),
                         self.ledger['baseline_sha256']['README.md'])
        for bad in (
            actual.replace(b'mechanics claims', b'unsupported claims', 1),
            re.sub(rb'\*\*\d+ mechanics claims\*\*', b'**0 mechanics claims**', actual, count=1),
            actual.replace(b'<!-- current-catalog-summary:start -->', b'', 1),
        ):
            with self.assertRaises(AssertionError):
                preservation.release_readme_bytes(bad)
        # Outside-marker changes are retained, so exact byte reversal rejects them.
        changed = preservation.release_readme_bytes(actual + b'Unreviewed addition\n')
        with self.assertRaises(AssertionError):
            preservation.pre_yield_bytes('README.md', changed)

if __name__ == '__main__':
    unittest.main()
