"""Independent v0.28 exact-lineage proof anchored to the 309-file public tree.

Canonical digests identify repository content, never independent scientific
review or publisher-asset identity. Independent evidence may append; every prior
evidence object, its order, and every other old field remain exact.
"""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

import composite_preservation as preservation

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SHA256 = '0e86e6bab32a18d7a01bd0ff04c7f05452bd27fd45057b37f4ba1f4ed2cdb30e'
ADAPTER_SHA256 = '7e9c266e3185040dcffb2428650e5130c9f0f92ede582fc4963ab5a1efc36468'
COMPATIBILITY_READERS = {'tests/yield_preservation.py', 'tests/test_yield_preservation.py'}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def declarations(source):
    """Every pre-existing top-level function and test method must remain."""
    result = set()
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.add(node.name)
        elif isinstance(node, ast.ClassDef):
            result.update(node.name + '.' + item.name for item in node.body
                          if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
    return result


def expected_compatibility_update(filename, before):
    """No changed assertions: only the exact v0.28-to-v0.27 byte bridge."""
    if filename == 'tests/yield_preservation.py':
        result = before.replace('from pathlib import Path\n',
                                'from pathlib import Path\nfrom composite_preservation import pre_composite_bytes\n')
        return result.replace(
            '    entries = validate_ledger(ledger)\n    if filename in entries:\n',
            "    entries = validate_ledger(ledger)\n    accepted = entries[filename]['sha256'] if filename in entries else ledger['baseline_sha256'].get(filename)\n    if digest(current) != accepted:\n        current = pre_composite_bytes(filename, current)\n    if filename in entries:\n")
    if filename == 'tests/test_yield_preservation.py':
        result = before.replace('import yield_preservation as preservation\n',
                                'import yield_preservation as preservation\nfrom composite_preservation import pre_composite_bytes\n')
        result = result.replace("sha((ROOT / 'tests/yield_preservation.py').read_bytes())",
                                "sha(pre_composite_bytes('tests/yield_preservation.py', (ROOT / 'tests/yield_preservation.py').read_bytes()))")
        result = result.replace(
            '            current = (ROOT / filename).read_bytes()\n            before = preservation.reverse_exact_edits(current, entry)\n',
            '            current = pre_composite_bytes(filename, (ROOT / filename).read_bytes())\n            before = preservation.reverse_exact_edits(current, entry)\n')
        return result.replace(
            "            before = preservation.reverse_exact_edits(current, entry)\n            self.assertEqual(preservation.apply_exact_edits(before, entry['edits']), current)\n",
            "            current = pre_composite_bytes(entry['filename'], current)\n            before = preservation.reverse_exact_edits(current, entry)\n            self.assertEqual(preservation.apply_exact_edits(before, entry['edits']), current)\n")
    raise AssertionError('Unspecified old-test transformation: ' + filename)


class CompositePreservationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = preservation.load_ledger()

    def release_bytes(self, filename):
        current = (ROOT / filename).read_bytes()
        return preservation.release_readme_bytes(current) if filename == 'README.md' else current

    def test_independent_ledger_adapter_pins_and_exact_public_anchor(self):
        self.assertEqual(sha((ROOT / preservation.LEDGER_PATH).read_bytes()), LEDGER_SHA256)
        self.assertEqual(sha((ROOT / 'tests/composite_preservation.py').read_bytes()), ADAPTER_SHA256)
        self.assertEqual(preservation.BASELINE_COMMIT, '2fd1585423dd05478c24396bf6f0206db1b5ae9a')
        self.assertEqual(preservation.BASELINE_TREE, 'e62c0cae498f35e460d0d8552998d624f8502640')
        self.assertEqual(self.ledger['review']['baseline_file_count'], 309)
        self.assertEqual(len(self.ledger['baseline_sha256']), 309)
        self.assertFalse(self.ledger['review']['historical_review_claimed'])
        entries = preservation.validate_ledger(self.ledger)
        self.assertEqual(set(entries), preservation.ALLOWED_PATHS)
        self.assertEqual({p for p in entries if p.startswith('tests/')}, COMPATIBILITY_READERS)
        self.assertFalse(any(p.startswith(('tests/fixtures/', 'examples/', 'schemas/', 'materials_boundaries/data/'))
                             for p in entries))

    def test_every_old_noncatalog_file_has_exact_accepted_bytes_or_exact_reversal(self):
        for filename, expected in self.ledger['baseline_sha256'].items():
            if filename.startswith('materials_boundaries/data/'):
                continue  # Every complete old object and metadata field is checked below.
            with self.subTest(filename=filename):
                self.assertEqual(sha(preservation.pre_composite_bytes(filename, self.release_bytes(filename))), expected)

    def test_every_old_fixture_example_and_provenance_helper_remains_byte_exact(self):
        baseline = self.ledger['baseline_sha256']
        fixtures = {p: h for p, h in baseline.items() if p.startswith('tests/fixtures/')}
        examples = {p: h for p, h in baseline.items() if p.startswith('examples/')}
        self.assertEqual(len(fixtures), 42)
        self.assertEqual(len(examples), 75)
        for filename, expected in dict(fixtures, **examples,
                **{'tests/provenance_corrections.py': baseline['tests/provenance_corrections.py']}).items():
            with self.subTest(filename=filename):
                self.assertEqual(sha((ROOT / filename).read_bytes()), expected)

    def test_every_prior_complete_object_locale_value_and_metadata_field_is_exact(self):
        self.assertEqual(len(self.ledger['catalog_preservation']), 9)
        for filename, fields in self.ledger['catalog_preservation'].items():
            current = json.loads((ROOT / filename).read_text())
            self.assertTrue(preservation.verify_catalog(filename, current))
            self.assertEqual(set(fields), set(current), filename)
            # A second implementation reconstructs the whole prior object from
            # its exact original evidence prefix, never dropping old metadata.
            for key, entry in fields.items():
                with self.subTest(filename=filename, field=key):
                    if 'record_digests' in entry:
                        index = {record['id']: record for record in current[key]}
                        self.assertEqual(len(index), len(current[key]))
                        for identifier, expected in entry['record_digests'].items():
                            prior = deepcopy(index[identifier])
                            if identifier in entry.get('evidence_digests', {}):
                                pinned = entry['evidence_digests'][identifier]
                                hashes = [sha(canonical(item)) for item in prior['evidence']]
                                self.assertEqual(hashes[:len(pinned)], pinned, identifier)
                                self.assertEqual(len(hashes), len(set(hashes)), identifier)
                                prior['evidence'] = prior['evidence'][:len(pinned)]
                            self.assertEqual(sha(canonical(prior)), expected, identifier)
                    elif 'locale_label_digests' in entry:
                        for language, labels in entry['locale_label_digests'].items():
                            for label, expected in labels.items():
                                self.assertEqual(sha(canonical(current[key][language][label])), expected)
                    elif 'label_digests' in entry:
                        for label, expected in entry['label_digests'].items():
                            self.assertEqual(sha(canonical(current[key][label])), expected)
                    else:
                        self.assertEqual(sha(canonical(current[key])), entry['sha256'])

    def test_only_exact_compatibility_transformations_and_no_removed_test_declarations(self):
        entries = preservation.validate_ledger(self.ledger)
        for filename in COMPATIBILITY_READERS:
            current = (ROOT / filename).read_bytes()
            before = preservation.reverse_exact_edits(current, entries[filename])
            self.assertEqual(current, expected_compatibility_update(filename, before.decode()).encode())
            self.assertEqual(declarations(before), declarations(current), filename)
        for filename in self.ledger['baseline_sha256']:
            if filename.startswith('tests/') and filename.endswith('.py'):
                current = (ROOT / filename).read_bytes()
                before = preservation.pre_composite_bytes(filename, current)
                self.assertEqual(declarations(before), declarations(current), filename)

    def test_every_forward_reverse_round_trip_and_changed_successor_fails(self):
        for entry in self.ledger['approved_existing_updates']:
            current = self.release_bytes(entry['filename'])
            before = preservation.reverse_exact_edits(current, entry)
            self.assertEqual(preservation.apply_exact_edits(before, entry['edits']), current)
            self.assertEqual(sha(before), self.ledger['baseline_sha256'][entry['filename']])
            for bad in (current + b'\n', b'!' + current[1:]):
                with self.subTest(filename=entry['filename']), self.assertRaises(AssertionError):
                    preservation.reverse_exact_edits(bad, entry)
            broken = deepcopy(entry); broken['previous_sha256'] = '0' * 64
            with self.assertRaises(AssertionError):
                preservation.reverse_exact_edits(current, broken)

    def test_malformed_foreign_duplicate_and_forged_ledger_entries_fail(self):
        mutations = [lambda x: x.update(release='0.27.0'), lambda x: x.update(extra=True),
            lambda x: x['review'].update(historical_review_claimed=True),
            lambda x: x['baseline_sha256'].pop(next(iter(x['baseline_sha256']))),
            lambda x: x['baseline_sha256'].update(LICENSE='not-a-hash'),
            lambda x: x['approved_existing_updates'].append(deepcopy(x['approved_existing_updates'][0])),
            lambda x: x['approved_existing_updates'][0].update(filename='unreviewed.py'),
            lambda x: x['approved_existing_updates'][0].update(filename=[]),
            lambda x: x['approved_existing_updates'][0].update(previous_sha256='0' * 64),
            lambda x: x['approved_existing_updates'][0].update(reason=''),
            lambda x: x['approved_existing_updates'][0].update(sha256='wrong'),
            lambda x: x['catalog_preservation'].pop(next(iter(x['catalog_preservation']))),
            lambda x: x['catalog_preservation']['materials_boundaries/data/claims.json'].update(schema_version={'sha256':'wrong'}),
            lambda x: x.update(release_readme_summary=None)]
        for mutate in mutations:
            bad = deepcopy(self.ledger); mutate(bad)
            with self.assertRaises(AssertionError):
                preservation.validate_ledger(bad)
        with self.assertRaises(AssertionError):
            json.loads('{"a":1,"a":2}', object_pairs_hook=preservation.unique_keys)
        entry = self.ledger['approved_existing_updates'][0]
        missing = deepcopy(self.ledger); missing['approved_existing_updates'].pop(0)
        with self.assertRaises(AssertionError):
            preservation.pre_composite_bytes(entry['filename'], self.release_bytes(entry['filename']), ledger=missing)
        with self.assertRaises(AssertionError):
            preservation.pre_composite_bytes('unreviewed.py', b'anything')
        with self.assertRaises(AssertionError):
            preservation.pre_composite_bytes('LICENSE', (ROOT / 'LICENSE').read_bytes() + b'!')

    def test_exact_edit_parser_rejects_bad_offsets_shapes_types_and_overlap(self):
        edits = [{'offset': 1, 'before': 'b', 'after': 'B'}, {'offset': 3, 'before': 'd', 'after': 'D'}]
        self.assertEqual(preservation.apply_exact_edits(b'abcde', edits), b'aBcDe')
        for bad in ([dict(edits[0], offset=-1)], [dict(edits[0], offset=20)],
                    [dict(edits[0], offset=True)], [dict(edits[0], before='wrong')],
                    [dict(edits[0], after='b')], list(reversed(edits)), [edits[0], edits[0]],
                    [dict(edits[0], extra=True)], [dict(edits[0], after=3)]):
            with self.subTest(edits=bad), self.assertRaises(AssertionError):
                preservation.apply_exact_edits(b'abcde', bad)
        edits = [{'offset': 2, 'before': 'β', 'after': '日'}]
        changed = preservation.apply_exact_edits('αβγ'.encode(), edits)
        self.assertEqual(changed, 'α日γ'.encode())
        entry = {'filename': 'unicode.txt', 'sha256': sha(changed),
                 'previous_sha256': sha('αβγ'.encode()), 'edits': edits}
        self.assertEqual(preservation.reverse_exact_edits(changed, entry), 'αβγ'.encode())

    def test_legacy_chain_is_exact_and_unreviewed_bytes_fail_closed(self):
        import yield_preservation as old
        import viscoelastic_preservation as older
        previous = old.load_ledger()
        for filename in preservation.ALLOWED_PATHS:
            if filename not in previous['baseline_sha256']:
                continue
            actual = self.release_bytes(filename)
            accepted = preservation.pre_composite_bytes(filename, actual)
            original = old.pre_yield_bytes(filename, actual)
            self.assertEqual(original, old.pre_yield_bytes(filename, accepted), filename)
            self.assertEqual(sha(original), previous['baseline_sha256'][filename], filename)
            self.assertEqual(older.pre_viscoelastic_bytes(filename, actual),
                             older.pre_viscoelastic_bytes(filename, accepted), filename)
            with self.assertRaises(AssertionError):
                old.pre_yield_bytes(filename, actual + b'!')
            with self.assertRaises(AssertionError):
                older.pre_viscoelastic_bytes(filename, actual + b'!')
        for adapter in (old, older):
            self.assertEqual(sha((ROOT / adapter.LEDGER_PATH).read_bytes()),
                             self.ledger['baseline_sha256'][adapter.LEDGER_PATH])

    def test_independent_appended_records_and_labels_pass_but_old_object_mutations_fail(self):
        filename = 'materials_boundaries/data/claims.json'
        original = json.loads((ROOT / filename).read_text())
        appended = deepcopy(original)
        new_record = deepcopy(original['records'][0]); new_record['id'] = 'original_independent_append_probe'
        appended['records'].append(new_record)
        before = deepcopy(appended)
        self.assertTrue(preservation.verify_catalog(filename, appended))
        self.assertEqual(appended, before)
        for mutate in (
            lambda x: x['records'][0].update(independent_review=True),
            lambda x: x['records'][0]['evidence'][0].update(verified_as='Unreviewed replacement'),
            lambda x: x['records'][0].pop('evidence'),
            lambda x: x['records'].append(deepcopy(x['records'][0])),
            lambda x: x['records'].pop(0),
            lambda x: x.update(schema_version='future'),
            lambda x: x.update(unreviewed_metadata=True),
        ):
            changed = deepcopy(appended); mutate(changed)
            with self.assertRaises(AssertionError):
                preservation.verify_catalog(filename, changed)
        filename = 'materials_boundaries/data/locales.json'
        labels = json.loads((ROOT / filename).read_text())
        labels['languages']['en']['original_independent_append_probe'] = 'New independent label'
        self.assertTrue(preservation.verify_catalog(filename, labels))
        old_label = next(iter(self.ledger['catalog_preservation'][filename]['languages']['locale_label_digests']['en']))
        labels['languages']['en'][old_label] = 'Unreviewed replacement'
        with self.assertRaises(AssertionError):
            preservation.verify_catalog(filename, labels)

    def test_evidence_appends_keep_exact_original_objects_order_and_other_metadata(self):
        filename = 'materials_boundaries/data/claims.json'
        original = json.loads((ROOT / filename).read_text())
        # The supported mixed contributor appends independent evidence to this
        # established claim; originals and their metadata stay byte-equivalent.
        identifier = 'lefm_central_crack_mode_i_stress_intensity'
        appended = deepcopy(original)
        record = next(item for item in appended['records'] if item['id'] == identifier)
        additional = {
            'source_id': 'original_independent_evidence_append_probe',
            'locator': None,
            'verification_status': 'synthetic_fixture_not_source_verification',
            'verified_as': 'Test-only append; no publication or scientific review is represented.',
        }
        record['evidence'].append(additional)
        before = deepcopy(appended)
        self.assertTrue(preservation.verify_catalog(filename, appended))
        self.assertEqual(appended, before)
        for mutate in (
            lambda r: r['evidence'][0].update(locator='Unreviewed changed locator'),
            lambda r: r['evidence'][0].pop('verification_status'),
            lambda r: r['evidence'][0].update(unreviewed_metadata=True),
            lambda r: r['evidence'].pop(0),
            lambda r: r['evidence'].reverse(),
            lambda r: r['evidence'].append(deepcopy(r['evidence'][0])),
            lambda r: r['evidence'].append('not an evidence object'),
            lambda r: r.update(independent_review=True),
        ):
            changed = deepcopy(appended)
            mutate(next(item for item in changed['records'] if item['id'] == identifier))
            with self.assertRaises(AssertionError):
                preservation.verify_catalog(filename, changed)
        # The eight executable claims remain completely pinned, including all
        # evidence, even when the appended object is independent and well-shaped.
        for executable_id in preservation.EXECUTABLE_IDS:
            changed = deepcopy(original)
            executable = next(item for item in changed['records'] if item['id'] == executable_id)
            executable['evidence'].append(deepcopy(additional))
            with self.subTest(executable_id=executable_id), self.assertRaises(AssertionError):
                preservation.verify_catalog(filename, changed)
        fields = self.ledger['catalog_preservation'][filename]['records']
        for mutation in ('missing', 'forged', 'duplicate', 'foreign'):
            ledger = deepcopy(self.ledger)
            entry = ledger['catalog_preservation'][filename]['records']
            if mutation == 'missing':
                entry.pop('evidence_digests')
            elif mutation == 'forged':
                entry['evidence_digests'][identifier] = ['not-a-digest']
            elif mutation == 'duplicate':
                entry['evidence_digests'][identifier] *= 2
            else:
                entry['evidence_digests']['unreviewed-id'] = fields['evidence_digests'][identifier]
            with self.assertRaises(AssertionError):
                preservation.validate_ledger(ledger)

    def test_readme_normalization_rejects_false_counts_changed_prose_and_outside_edits(self):
        actual = (ROOT / 'README.md').read_bytes()
        normalized = preservation.release_readme_bytes(actual)
        self.assertEqual(sha(preservation.pre_composite_bytes('README.md', normalized)),
                         self.ledger['baseline_sha256']['README.md'])
        for bad in (
            actual.replace(b'mechanics claims', b'unsupported claims', 1),
            re.sub(rb'\*\*\d+ mechanics claims\*\*', b'**0 mechanics claims**', actual, count=1),
            actual.replace(b'<!-- current-catalog-summary:start -->', b'', 1),
            actual.replace(b'<!-- current-catalog-summary:end -->', b'<!-- current-catalog-summary:end -->' * 2, 1),
        ):
            with self.assertRaises(AssertionError):
                preservation.release_readme_bytes(bad)
        changed = preservation.release_readme_bytes(actual + b'Unreviewed addition\n')
        with self.assertRaises(AssertionError):
            preservation.pre_composite_bytes('README.md', changed)

    def test_disposable_mixed_catalog_count_refresh_reverses_without_touching_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / 'materials_boundaries/data', root / 'materials_boundaries/data')
            (root / 'tests/fixtures').mkdir(parents=True)
            shutil.copyfile(ROOT / preservation.LEDGER_PATH, root / preservation.LEDGER_PATH)
            values = {}
            for filename in self.ledger['catalog_preservation']:
                values[filename] = json.loads((root / filename).read_text())
            for name, collection in (
                ('claims', 'records'), ('sources', 'records'), ('observations', 'records'),
                ('computational_predictions', 'records'), ('computational_predictions', 'protocols'),
                ('computational_predictions', 'comparison_groups'),
            ):
                filename = 'materials_boundaries/data/' + name + '.json'
                new = deepcopy(values[filename][collection][0]); new['id'] = 'original_append_probe_' + collection
                if name == 'observations':
                    new['study_id'] = 'original_independent_study_probe'
                if collection == 'protocols':
                    new['family'] = 'original_independent_family_probe'
                values[filename][collection].append(new)
            values['materials_boundaries/data/locales.json']['languages']['en']['original_append_probe'] = 'New label'
            for filename, current in values.items():
                self.assertTrue(preservation.verify_catalog(filename, current))
                (root / filename).write_text(json.dumps(current, ensure_ascii=False))
            actual = (ROOT / 'README.md').read_bytes()
            release = preservation.release_readme_bytes(actual)
            # Construct truthful counts independently from the normalizer.
            text = actual.decode()
            start, end = '<!-- current-catalog-summary:start -->', '<!-- current-catalog-summary:end -->'
            prefix, tail = text.split(start); summary, suffix = tail.split(end)
            data = lambda name: values['materials_boundaries/data/' + name + '.json']
            claims, sources, observations = (data(name)['records'] for name in ('claims', 'sources', 'observations'))
            predictions = data('computational_predictions')
            demos = [record for record in data('temperature_models')['records'] if record['classification'] == 'synthetic_demo']
            synthetic = sum(record['role'] == 'synthetic_demo_provenance' for record in sources)
            replacements = [
                (r'\*\*\d+ mechanics claims\*\*', f'**{len(claims)} mechanics claims**'),
                (r'\*\*\d+ source records\*\*', f'**{len(sources)} source records**'),
                (r'\*\*\d+ observations from \d+ studies\*\*', f'**{len(observations)} observations from {len({r["study_id"] for r in observations})} studies**'),
                (r'\*\*\d+ published computational predictions in \d+ scientific families and \d+ explicit groups\*\*',
                 f'**{len(predictions["records"])} published computational predictions in {len({r["family"] for r in predictions["protocols"]})} scientific families and {len(predictions["comparison_groups"])} explicit groups**'),
                (r'\*\*\d+ synthetic temperature demos with \d+ branches\*\*', f'**{len(demos)} synthetic temperature demos with {sum(len(r["branches"]) for r in demos)} branches**'),
                (r'The \d+ sources comprise \d+ bibliographic/source records plus \d+ original synthetic-demo provenance record',
                 f'The {len(sources)} sources comprise {len(sources)-synthetic} bibliographic/source records plus {synthetic} original synthetic-demo provenance record'),
            ]
            for pattern, value in replacements:
                summary, count = re.subn(pattern, lambda match: value, summary)
                self.assertEqual(count, 1)
            refreshed = (prefix + start + summary + end + suffix).encode()
            self.assertNotEqual(refreshed, actual)
            with patch.object(preservation, 'ROOT', root):
                self.assertEqual(preservation.release_readme_bytes(refreshed), release)
                self.assertEqual(sha(preservation.pre_composite_bytes('README.md', preservation.release_readme_bytes(refreshed))),
                                 self.ledger['baseline_sha256']['README.md'])
                with self.assertRaises(AssertionError):
                    preservation.release_readme_bytes(actual)


if __name__ == '__main__':
    unittest.main()
