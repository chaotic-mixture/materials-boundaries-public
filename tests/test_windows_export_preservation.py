"""Independent v0.28.1 lineage checks for the 328-file public v0.28.0 tree.

The Windows export adaptation does not change scientific contracts or historical
fixtures. Existing catalog-only append rules remain the v0.28.0 adapter's rules.
These repository hashes do not establish independent scientific review.
"""
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

import composite_preservation as composite
import windows_export_preservation as preservation

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SHA256 = 'be6e881a632ab537e4fc852a1d0353a6b4e10fb55fbac02b97d577cd6048e529'
ADAPTER_SHA256 = '2a9efecf829cf4ade18393f9fb7772b7067bc8ddb0d4b4bfb8fde4beaff2f34a'
COMPATIBILITY_READERS = {
    'tests/composite_preservation.py', 'tests/test_composite_preservation.py',
}
POSIX_METHODS = frozenset({
    'test_symlink_output_and_ancestor_and_traversal_refused',
    'test_stage_failures_clean_only_own_data',
    'test_publish_failures_manifest_last_and_rollback',
    'test_concurrent_unrelated_file_is_preserved',
    'test_rollback_does_not_delete_replacement',
    'test_cleanup_failure_rolls_back_manifest_then_retries_owned_stage',
    'test_stage_open_failure_removes_created_empty_stage',
    'test_exclusive_name_collision_does_not_delete_other_input',
})


def sha(value):
    return hashlib.sha256(value).hexdigest()


def declarations(source):
    result = set()
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.add(node.name)
        elif isinstance(node, ast.ClassDef):
            result.update(node.name + '.' + item.name for item in node.body
                          if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
    return result


def assertion_signatures(source):
    """Compare each existing function's assertions, permitting only byte readers."""
    class Readers(ast.NodeTransformer):
        def visit_Call(self, node):
            node = self.generic_visit(node)
            if (isinstance(node.func, ast.Name) and node.func.id == 'pre_windows_export_bytes'
                    and len(node.args) == 2 and not node.keywords):
                return node.args[1]
            return node
    tree = Readers().visit(ast.parse(source))
    result = {}
    functions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append((node.name, node))
        elif isinstance(node, ast.ClassDef):
            functions.extend((node.name + '.' + item.name, item) for item in node.body
                             if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
    for name, function in functions:
        result[name] = Counter(ast.dump(node, include_attributes=False)
            for node in ast.walk(function)
            if isinstance(node, ast.Assert) or (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == 'self'
                and node.func.attr.startswith('assert')))
    return result


def expected_compatibility_update(filename, before):
    """Only the explicit v0.28.1-to-v0.28.0 byte-reader bridge is permitted."""
    if filename == 'tests/composite_preservation.py':
        result = before.replace('from pathlib import Path\n',
            'from pathlib import Path\nfrom windows_export_preservation import pre_windows_export_bytes\n')
        return result.replace('    entries = validate_ledger(ledger)\n    if filename in entries:\n',
            "    entries = validate_ledger(ledger)\n    accepted = entries[filename]['sha256'] if filename in entries else ledger['baseline_sha256'].get(filename)\n    if digest(current) != accepted:\n        current = pre_windows_export_bytes(filename, current)\n    if filename in entries:\n")
    if filename == 'tests/test_composite_preservation.py':
        result = before.replace('import composite_preservation as preservation\n',
            'import composite_preservation as preservation\nfrom windows_export_preservation import pre_windows_export_bytes\n')
        result = result.replace(
            "        return preservation.release_readme_bytes(current) if filename == 'README.md' else current\n",
            "        current = preservation.release_readme_bytes(current) if filename == 'README.md' else current\n        return pre_windows_export_bytes(filename, current)\n")
        return result.replace("sha((ROOT / 'tests/composite_preservation.py').read_bytes())",
            "sha(pre_windows_export_bytes('tests/composite_preservation.py', (ROOT / 'tests/composite_preservation.py').read_bytes()))")
    raise AssertionError('Unspecified prior-test transformation: ' + filename)


def expected_export_platform_update(before):
    """Retain POSIX test bodies verbatim; Windows has dedicated native coverage."""
    result = before
    decorator = '    @unittest.skipUnless(os.name == "posix", "POSIX backend; native Windows coverage is separate")\n'
    for method in POSIX_METHODS:
        declaration = '    def ' + method + '(self):\n'
        if result.count(declaration) != 1:
            raise AssertionError('Missing or duplicated POSIX test declaration: ' + method)
        result = result.replace(declaration, decorator + declaration)
    return result


def expected_acceptance_platform_update(before):
    """Preserve A30 assertions while choosing native staging and reparse fixtures."""
    edits = [
        ('import json\n', 'import json\nimport os\n'),
        ('        from materials_boundaries import composite_export as export\n',
         '        from materials_boundaries import composite_export as export\n'
         '        stage_backend = export\n'
         "        if os.name == 'nt':\n"
         '            from materials_boundaries import _composite_windows as stage_backend\n'),
        ("            outside = root / 'outside'; outside.mkdir(); symlink = root / 'alias'; symlink.symlink_to(outside, target_is_directory=True)\n",
         "            outside = root / 'outside'; outside.mkdir(); symlink = root / 'alias'\n"
         "            if os.name == 'nt':\n"
         "                subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(symlink), str(outside)],\n"
         "                               check=True, capture_output=True)\n"
         '            else:\n'
         '                symlink.symlink_to(outside, target_is_directory=True)\n'),
        ('                    calls.append(args[0])\n',
         '                    calls.append(Path(args[0]).name)\n'),
        ("            with patch.object(export, '_stage_file', side_effect=OSError('injected stage failure')), self.assertRaises(OSError):\n",
         "            with patch.object(stage_backend, '_stage_file', side_effect=OSError('injected stage failure')), self.assertRaises(OSError):\n"),
    ]
    result = before
    for old, new in edits:
        if result.count(old) != 1:
            raise AssertionError('Missing or duplicated A30 platform adaptation')
        result = result.replace(old, new)
    return result


class WindowsExportPreservationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = preservation.load_ledger()

    def release_bytes(self, filename):
        current = (ROOT / filename).read_bytes()
        return composite.release_readme_bytes(current) if filename == 'README.md' else current

    def test_independent_pins_and_exact_public_anchor(self):
        self.assertEqual(sha((ROOT / preservation.LEDGER_PATH).read_bytes()), LEDGER_SHA256)
        self.assertEqual(sha((ROOT / 'tests/windows_export_preservation.py').read_bytes()), ADAPTER_SHA256)
        self.assertEqual(preservation.BASELINE_COMMIT, '08ca206c1ae558643e38bde5dfc632cb65328c68')
        self.assertEqual(preservation.BASELINE_TREE, '203db3af3b54198b175ab631643f0a673b529716')
        self.assertEqual(self.ledger['review']['baseline_file_count'], 328)
        self.assertEqual(len(self.ledger['baseline_sha256']), 328)
        self.assertFalse(self.ledger['review']['historical_review_claimed'])
        entries = preservation.validate_ledger(self.ledger)
        self.assertEqual(set(entries), preservation.ALLOWED_PATHS)
        self.assertEqual({path for path in entries if path.startswith('tests/')},
                         COMPATIBILITY_READERS | {'tests/test_composite_export.py', 'tests/test_composite_acceptance.py'})
        self.assertFalse(any(path.startswith(('tests/fixtures/', 'examples/', 'schemas/',
                                             'materials_boundaries/data/')) for path in entries))

    def test_every_prior_noncatalog_file_is_exact_or_exactly_reversible(self):
        for filename, expected in self.ledger['baseline_sha256'].items():
            if filename.startswith('materials_boundaries/data/'):
                continue  # Existing v0.28.0 complete-object append rules are checked below.
            with self.subTest(filename=filename):
                before = preservation.pre_windows_export_bytes(filename, self.release_bytes(filename))
                self.assertEqual(sha(before), expected)

    def test_all_old_fixtures_examples_schemas_and_provenance_helper_are_exact(self):
        baseline = self.ledger['baseline_sha256']
        fixtures = {path: value for path, value in baseline.items() if path.startswith('tests/fixtures/')}
        examples = {path: value for path, value in baseline.items() if path.startswith('examples/')}
        schemas = {path: value for path, value in baseline.items() if path.startswith('schemas/')}
        self.assertEqual(len(fixtures), 44)
        self.assertEqual(len(examples), 75)
        self.assertTrue(schemas)
        for filename, expected in dict(fixtures, **examples, **schemas,
                **{'tests/provenance_corrections.py': baseline['tests/provenance_corrections.py']}).items():
            with self.subTest(filename=filename):
                self.assertEqual(sha((ROOT / filename).read_bytes()), expected)

    def test_scientific_catalog_preservation_uses_unchanged_prior_ledger(self):
        baseline = self.ledger['baseline_sha256']
        self.assertEqual(sha((ROOT / composite.LEDGER_PATH).read_bytes()), baseline[composite.LEDGER_PATH])
        prior = composite.load_ledger()
        catalogs = {path for path in baseline if path.startswith('materials_boundaries/data/')}
        self.assertEqual(catalogs, set(prior['catalog_preservation']))
        self.assertEqual(len(catalogs), 9)
        for filename in catalogs:
            with self.subTest(filename=filename):
                current = json.loads((ROOT / filename).read_text(encoding='utf-8'))
                self.assertTrue(composite.verify_catalog(filename, current))
        # New software work never expands this scientific execution boundary.
        self.assertEqual(composite.EXECUTABLE_IDS, {
            'hs_bulk_3d_two_phase', 'reuss_bulk', 'voigt_bulk',
            'hs_shear_3d_two_phase', 'reuss_shear', 'voigt_shear',
            'youngs_modulus_outer', 'poissons_ratio_outer',
        })

    def test_only_exact_reader_bridges_and_all_old_test_declarations_assertions_remain(self):
        entries = preservation.validate_ledger(self.ledger)
        for filename in COMPATIBILITY_READERS:
            current = (ROOT / filename).read_bytes()
            before = preservation.reverse_exact_edits(current, entries[filename])
            self.assertEqual(current, expected_compatibility_update(filename, before.decode('utf-8')).encode('utf-8'))
            self.assertEqual(declarations(before), declarations(current), filename)
        filename = 'tests/test_composite_export.py'
        current = (ROOT / filename).read_bytes()
        before = preservation.reverse_exact_edits(current, entries[filename])
        self.assertEqual(current, expected_export_platform_update(before.decode('utf-8')).encode('utf-8'))
        filename = 'tests/test_composite_acceptance.py'
        current = (ROOT / filename).read_bytes()
        before = preservation.reverse_exact_edits(current, entries[filename])
        self.assertEqual(current, expected_acceptance_platform_update(before.decode('utf-8')).encode('utf-8'))
        for filename in self.ledger['baseline_sha256']:
            if filename.startswith('tests/') and filename.endswith('.py'):
                current = (ROOT / filename).read_bytes()
                before = preservation.pre_windows_export_bytes(filename, current)
                self.assertLessEqual(declarations(before), declarations(current), filename)
                old_assertions, current_assertions = assertion_signatures(before), assertion_signatures(current)
                for function, expected in old_assertions.items():
                    with self.subTest(filename=filename, function=function):
                        self.assertFalse(expected - current_assertions[function])

    def test_wheel_smoke_checker_changes_only_utf8_readers_and_isolated_launcher(self):
        filename = 'scripts/check_wheel_metadata.py'
        current = (ROOT / filename).read_bytes()
        before = preservation.pre_windows_export_bytes(filename, current)
        self.assertEqual(before.count(b'.read_text()'), 9)
        expected = before.replace(b'.read_text()', b".read_text(encoding='utf-8')")
        old_launch = b'        result = subprocess.run([str(python), "-I", "-c", INSTALLED_CHECK, expected,\n'
        new_launch = (
            b"        # Windows CreateProcess has a command-line limit below this check's\n"
            b"        # length. Execute its exact UTF-8 bytes as a local isolated script.\n"
            b'        installed_check = work / "installed_check.py"\n'
            b'        installed_check.write_text(INSTALLED_CHECK, encoding="utf-8")\n'
            b'        result = subprocess.run([str(python), "-I", str(installed_check), expected,\n'
        )
        self.assertEqual(expected.count(old_launch), 1)
        self.assertEqual(current, expected.replace(old_launch, new_launch))

    def test_every_forward_reverse_round_trip_and_unreviewed_successor_fails(self):
        for entry in self.ledger['approved_existing_updates']:
            current = self.release_bytes(entry['filename'])
            before = preservation.reverse_exact_edits(current, entry)
            self.assertEqual(preservation.apply_exact_edits(before, entry['edits']), current)
            self.assertEqual(sha(before), self.ledger['baseline_sha256'][entry['filename']])
            for bad in (current + b'\n', b'!' + current[1:]):
                with self.subTest(filename=entry['filename']), self.assertRaises(AssertionError):
                    preservation.pre_windows_export_bytes(entry['filename'], bad)
            broken = deepcopy(entry); broken['previous_sha256'] = '0' * 64
            with self.assertRaises(AssertionError):
                preservation.reverse_exact_edits(current, broken)
            with self.assertRaises(AssertionError):
                preservation.reverse_exact_edits(before, entry)

    def test_older_adapter_chain_is_exact_and_unreviewed_bytes_fail_closed(self):
        import yield_preservation as older
        import viscoelastic_preservation as oldest
        prior = composite.load_ledger()
        for filename in preservation.ALLOWED_PATHS & set(prior['baseline_sha256']):
            actual = self.release_bytes(filename)
            accepted = preservation.pre_windows_export_bytes(filename, actual)
            original = composite.pre_composite_bytes(filename, actual)
            self.assertEqual(original, composite.pre_composite_bytes(filename, accepted), filename)
            self.assertEqual(sha(original), prior['baseline_sha256'][filename], filename)
            for adapter, reader in ((composite, composite.pre_composite_bytes),
                                    (older, older.pre_yield_bytes),
                                    (oldest, oldest.pre_viscoelastic_bytes)):
                if filename not in adapter.load_ledger()['baseline_sha256']:
                    continue
                self.assertEqual(reader(filename, actual), reader(filename, accepted), filename)
                with self.assertRaises(AssertionError):
                    reader(filename, actual + b'!')
        for adapter in (composite, older, oldest):
            self.assertEqual(sha((ROOT / adapter.LEDGER_PATH).read_bytes()),
                             self.ledger['baseline_sha256'][adapter.LEDGER_PATH])

    def test_malformed_foreign_duplicate_missing_and_forged_ledger_entries_fail(self):
        mutations = [
            lambda x: x.update(release='0.28.0'), lambda x: x.update(extra=True),
            lambda x: x.update(schema_version=True),
            lambda x: x['review'].update(historical_review_claimed=True),
            lambda x: x['review'].update(baseline_commit='0' * 40),
            lambda x: x['baseline_sha256'].pop(next(iter(x['baseline_sha256']))),
            lambda x: x['baseline_sha256'].update(LICENSE='not-a-hash'),
            lambda x: x['approved_existing_updates'].append(deepcopy(x['approved_existing_updates'][0])),
            lambda x: x['approved_existing_updates'].pop(0),
            lambda x: x['approved_existing_updates'][0].update(filename='unreviewed.py'),
            lambda x: x['approved_existing_updates'][0].update(filename=[]),
            lambda x: x['approved_existing_updates'][0].update(previous_sha256='0' * 64),
            lambda x: x['approved_existing_updates'][0].update(reason=' '),
            lambda x: x['approved_existing_updates'][0].update(sha256='wrong'),
            lambda x: x['approved_existing_updates'][0].update(edits=[]),
            lambda x: x['approved_existing_updates'][0]['edits'][0].update(offset=True),
        ]
        for mutate in mutations:
            bad = deepcopy(self.ledger); mutate(bad)
            with self.assertRaises(AssertionError):
                preservation.validate_ledger(bad)
        with self.assertRaises(AssertionError):
            json.loads('{"a":1,"a":2}', object_pairs_hook=preservation.unique_keys)
        with self.assertRaises(AssertionError):
            preservation.pre_windows_export_bytes('unreviewed.py', b'anything')
        with self.assertRaises(AssertionError):
            preservation.pre_windows_export_bytes('LICENSE', (ROOT / 'LICENSE').read_bytes() + b'!')

    def test_exact_edit_parser_rejects_bad_shapes_offsets_types_and_overlaps(self):
        edits = [{'offset': 1, 'before': 'b', 'after': 'B'}, {'offset': 3, 'before': 'd', 'after': 'D'}]
        self.assertEqual(preservation.apply_exact_edits(b'abcde', edits), b'aBcDe')
        bad_edits = [[], None, [dict(edits[0], offset=-1)], [dict(edits[0], offset=20)],
            [dict(edits[0], offset=True)], [dict(edits[0], before='wrong')],
            [dict(edits[0], after='b')], list(reversed(edits)), [edits[0], edits[0]],
            [dict(edits[0], extra=True)], [dict(edits[0], after=3)],
            [{'offset': 1, 'before': '', 'after': 'x'}, {'offset': 1, 'before': '', 'after': 'y'}]]
        for bad in bad_edits:
            with self.subTest(edits=bad), self.assertRaises(AssertionError):
                preservation.apply_exact_edits(b'abcde', bad)
        with self.assertRaises(AssertionError):
            preservation.apply_exact_edits('abcde', edits)
        edits = [{'offset': 2, 'before': 'β', 'after': '日'}]
        current = preservation.apply_exact_edits('αβγ'.encode('utf-8'), edits)
        self.assertEqual(current, 'α日γ'.encode('utf-8'))
        entry = {'filename': 'unicode.txt', 'sha256': sha(current),
                 'previous_sha256': sha('αβγ'.encode('utf-8')), 'edits': edits}
        self.assertEqual(preservation.reverse_exact_edits(current, entry), 'αβγ'.encode('utf-8'))
        bad = deepcopy(entry); bad['edits'][0]['offset'] = True
        with self.assertRaises(AssertionError):
            preservation.reverse_exact_edits(current, bad)


if __name__ == '__main__':
    unittest.main()
