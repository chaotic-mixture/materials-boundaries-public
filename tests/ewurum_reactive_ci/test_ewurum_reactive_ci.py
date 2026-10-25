"""EwurumReactive validation contracts; explicitly executed outside frozen core discovery."""
import ast
from contextlib import redirect_stdout
from copy import deepcopy
from hashlib import sha256
import io
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_ewurum_reactive_runtime_ci as ci


def git_bytes(path):
    return subprocess.check_output(['git', 'show', ci.BASE_COMMIT + ':' + path], cwd=ROOT, timeout=30)


def recorded_result(ids):
    return types.SimpleNamespace(testsRun=len(ids), started_ids=list(ids), passed_ids=list(ids),
             failures=[], errors=[], skipped=[], expectedFailures=[], unexpectedSuccesses=[], wasSuccessful=lambda: True)


class EwurumReactiveCIContracts(unittest.TestCase):
    def test_whole_group_inventories_are_explicit_and_have_no_missing_or_duplicate_ids(self):
        manifest = ci.load_manifest()
        self.assertEqual(tuple(manifest['source_groups']), ci.SOURCE_GROUPS)
        self.assertEqual(tuple(manifest['installed_groups']), ci.INSTALLED_GROUPS)
        for group in [*manifest['source_groups'].values(), *manifest['installed_groups'].values()]:
            if group.get('selection') == 'frozen_replay_profile':
                frozen = json.loads((ROOT / 'tests/history_replay_latest/ci-inventory.json').read_bytes())
                self.assertEqual(group['ids'], frozen['ids'])
                self.assertEqual(group['count'], 70)
                self.assertEqual(group['sha256'], frozen['fingerprint'])
                self.assertEqual(group['modules'], sorted({x.split('.')[0] for x in group['ids']}))
                continue
            expected = []
            directory = ROOT / group['directory']
            for module in group['modules']:
                for node in ast.parse((directory / (module + '.py')).read_bytes()).body:
                    if isinstance(node, ast.ClassDef):
                        expected.extend(module + '.' + node.name + '.' + child.name for child in node.body
                            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith('test'))
            with self.subTest(directory=group['directory']):
                self.assertEqual(sorted(expected), group['ids'])
                self.assertEqual(len(expected), group['count'])
                self.assertEqual(ci.fingerprint(expected), group['sha256'])
                if group.get('selection') != 'explicit_whole_modules':
                    self.assertEqual(group['modules'], sorted(p.stem for p in directory.glob('test*.py')))

    def test_frozen_inventory_rejects_missing_extra_duplicate_substituted_ids(self):
        group = ci.load_manifest()['source_groups']['candidate']
        expected = group['ids']
        for ids in (expected[:-1], expected + ['test_foreign.C.test_x'], expected + [expected[0]],
                    ['test_foreign.C.test_x'] + expected[1:]):
            with self.subTest(ids=ids), self.assertRaises(RuntimeError):
                ci.validate_inventory(group, ids, group['modules'])
        with self.assertRaises(RuntimeError):
            ci.validate_inventory(group, expected, group['modules'] + ['test_unknown'])

    def test_manifest_byte_hash_and_group_shape_fail_closed(self):
        original = (ROOT / ci.MANIFEST_PATH).read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / ci.MANIFEST_PATH
            path.parent.mkdir(parents=True)
            path.write_bytes(original + b' ')
            with patch.object(ci, 'ROOT', root), self.assertRaises(RuntimeError):
                ci.load_manifest()
        for mutation in ('empty', 'count', 'hash', 'duplicate', 'missing_group', 'core', 'replay'):
            value = ci.load_manifest()
            group = value['source_groups']['candidate']
            if mutation == 'empty': group['ids'] = []
            elif mutation == 'count': group['count'] += 1
            elif mutation == 'hash': group['sha256'] = '0' * 64
            elif mutation == 'duplicate': group['ids'].append(group['ids'][0])
            elif mutation == 'missing_group': del value['installed_groups']['query']
            elif mutation == 'core': value['core_inventory']['methods'] -= 1
            else: value['replay_inventory_count'] = 69
            with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                ci.validate_manifest(value)

    def test_general_full_partition_and_replay_workflows_are_unchanged(self):
        for path in ('.github/workflows/ci.yml', '.github/workflows/history-replay-latest.yml',
                     'tests/core_partition/manifest.json'):
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes(), git_bytes(path))
        workflow = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
        self.assertIn('partition: [0, 1, 2, 3]', workflow)
        self.assertIn('python-version: [\'3.11\', \'3.12\']', workflow)
        self.assertIn('unit-and-schema-aggregate:', workflow)
        self.assertNotIn(ci.BRANCH_REF, workflow)

    def test_dedicated_workflow_has_exact_two_platforms_offline_six_wheels_and_no_general_suppression(self):
        manifest = ci.load_manifest()
        ci.validate_workflow(manifest)
        raw = (ROOT / ci.WORKFLOW_PATH).read_text(encoding='utf-8')
        self.assertIn('branches: [experimental/ewurum2025-reactive-runtime]', raw)
        self.assertEqual(raw.count('os: ubuntu-latest'), 1)
        self.assertEqual(raw.count('os: windows-latest'), 1)
        self.assertIn('fetch-depth: 0', raw)
        self.assertIn('persist-credentials: false', raw)
        self.assertIn('fail-fast: false', raw)
        self.assertIn('timeout-minutes: 90', raw)
        self.assertNotIn('continue-on-error', raw)
        self.assertNotIn('workflow_dispatch', raw)
        self.assertNotIn('cancel-in-progress', raw)
        for command in ('--validate-scope', '--validate-inventory', '--source-tests',
                        '--wheel-dir dist --dependency-dir dist/dependencies'):
            self.assertEqual(raw.count('python scripts/run_ewurum_reactive_runtime_ci.py ' + command), 1)
        build = 'python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir dist . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform'
        self.assertEqual(raw.count(build), 1)

    def test_workflow_mutations_cannot_hide_missing_core_or_installed_checks(self):
        manifest = ci.load_manifest()
        general = (ROOT / '.github/workflows/ci.yml').read_bytes()
        dedicated = (ROOT / ci.WORKFLOW_PATH).read_bytes()
        mutations = ((general + b' ', dedicated),
                     (general, dedicated.replace(b'--source-tests', b'--validate-inventory')),
                     (general, dedicated.replace(b'fetch-depth: 0', b'fetch-depth: 1')),
                     (general, dedicated.replace(b'--wheel-dir dist --dependency-dir dist/dependencies', b'--validate-scope')),
                     (general, dedicated.replace(b'fail-fast: false', b'fail-fast: true')))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.github/workflows').mkdir(parents=True)
            for old, new in mutations:
                (root / '.github/workflows/ci.yml').write_bytes(old)
                (root / ci.WORKFLOW_PATH).write_bytes(new)
                with patch.object(ci, 'ROOT', root), patch.object(ci, 'git', return_value=general), self.assertRaises(RuntimeError):
                    ci.validate_workflow(manifest)

    def test_actions_metadata_requires_exact_event_ref_sha_and_clean_tree(self):
        metadata = {'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_NAME': 'push',
                    'GITHUB_REF': ci.BRANCH_REF, 'GITHUB_SHA': 'a' * 40}
        with patch.dict(os.environ, metadata, clear=True), patch.object(ci, 'git', return_value=b''):
            ci.validate_event('a' * 40)
        for key, value in (('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_REF', 'refs/heads/main'), ('GITHUB_SHA', 'b' * 40)):
            with patch.dict(os.environ, {**metadata, key: value}, clear=True), patch.object(ci, 'git', return_value=b''), self.assertRaises(RuntimeError):
                ci.validate_event('a' * 40)
        with patch.dict(os.environ, metadata, clear=True), patch.object(ci, 'git', return_value=b' M file\n'), self.assertRaises(RuntimeError):
            ci.validate_event('a' * 40)

    def test_scope_rejects_unlisted_deleted_nonfile_and_outside_paths(self):
        manifest = {'approved_paths': ['allowed.py', 'directory', '../outside.py']}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'allowed.py').write_text('pass\n', encoding='utf-8')
            (root / 'directory').mkdir()
            ci.validate_paths({'allowed.py'}, manifest, root=root)
            for names in ({'unknown.py'}, {'missing.py'}, {'directory'}, {'../outside.py'}, {None}):
                with self.subTest(names=names), self.assertRaises(RuntimeError):
                    ci.validate_paths(names, manifest, root=root)

    def test_results_require_every_started_and_successful_id_without_skips(self):
        ids = ['test_one.C.test_a', 'test_one.C.test_b']
        self.assertEqual(ci.validate_result(ids, recorded_result(ids))['passed'], 2)
        for field, value in (('testsRun', 1), ('started_ids', ids[:1]), ('passed_ids', ids[:1]),
                             ('passed_ids', ids + [ids[0]]), ('skipped', [(object(), 'known elsewhere')]),
                             ('expectedFailures', [(object(), 'expected')]), ('unexpectedSuccesses', [object()]),
                             ('errors', [(object(), 'fixture error')]), ('failures', [(object(), 'subtest failure')])):
            result = recorded_result(ids)
            setattr(result, field, value)
            with self.subTest(field=field, value=value), self.assertRaises(RuntimeError):
                ci.validate_result(ids, result)

    def test_real_class_fixture_and_subtest_errors_never_emit_a_complete_result(self):
        class FixtureError(unittest.TestCase):
            @classmethod
            def setUpClass(cls): raise RuntimeError('synthetic class setup error')
            def test_one(self): pass
        class SubtestError(unittest.TestCase):
            def test_one(self):
                with self.subTest(case='synthetic'):
                    self.assertEqual(1, 2)
        for case in (FixtureError, SubtestError):
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
            ids = list(ci.test_ids(suite))
            result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=ci.ExactResult).run(suite)
            with self.subTest(case=case.__name__), self.assertRaises(RuntimeError):
                ci.validate_result(ids, result)
        module = types.ModuleType('ewurum_reactive_synthetic_fixture_error')
        def set_up_module():
            raise RuntimeError('synthetic module setup error')
        module.setUpModule = set_up_module
        case = type('ModuleFixtureError', (unittest.TestCase,),
                    {'__module__': module.__name__, 'test_one': lambda self: None})
        with patch.dict(sys.modules, {module.__name__: module}):
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(case)
            ids = list(ci.test_ids(suite))
            result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=ci.ExactResult).run(suite)
        self.assertEqual(result.testsRun, 0)
        self.assertEqual(len(result.errors), 1)
        with self.assertRaises(RuntimeError):
            ci.validate_result(ids, result)

    def test_exact_append_rejects_count_preserving_partial_reordered_and_metadata_drift(self):
        payload = ci.installation_payload()
        candidate = payload['candidate']
        before, current = {}, {}
        for key, filename in (('materials', 'materials.json'), ('properties', 'reference_properties.json'), ('sources', 'sources.json')):
            before[key] = json.loads(git_bytes('materials_boundaries/data/' + filename))
            current[key] = json.loads((ROOT / 'materials_boundaries/data' / filename).read_bytes())
        ci.validate_append(candidate, before, current)
        for mutation in ('previous_value', 'partial', 'order', 'metadata', 'duplicate_candidate'):
            changed, supplied = deepcopy(current), deepcopy(candidate)
            if mutation == 'previous_value': changed['materials']['identities'][0]['name'] += ' drift'
            elif mutation == 'partial': changed['properties']['records'].pop()
            elif mutation == 'order': changed['materials']['identities'][-2:] = reversed(changed['materials']['identities'][-2:])
            elif mutation == 'metadata': changed['sources']['schema_version'] = 'unreviewed'
            else: supplied['materials']['identities'].append(deepcopy(supplied['materials']['identities'][0]))
            with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                ci.validate_append(supplied, before, changed)

    def test_installed_smoke_keeps_literal_source_oracles_and_does_not_infer_uncertainty(self):
        compile(ci.INSTALLED_SMOKE, '<installed-smoke>', 'exec')
        for row in ("('r10', 'R10', '10', '751', '40', 'b\\u2032', '4.7')",
                    "('r20', 'R20', '20', '716', '49', 'b\\u2032', '4.3')",
                    "('r30', 'R30', '30', '910', '85', 'b', '12.7')",
                    "('r45', 'R45', '45', '1256', '162', 'a', '26.2')"):
            self.assertIn(row, ci.INSTALLED_SMOKE)
        self.assertIn("prop['uncertainty']['type'] == 'reported_standard_deviation'", ci.INSTALLED_SMOKE)
        self.assertIn("prop['sample_count']['value'] == 10", ci.INSTALLED_SMOKE)
        self.assertIn('ASTM D1708-18 (2018), source-cited edition in reference [32]', ci.INSTALLED_SMOKE)
        self.assertIn('not the injection-molded tensile dog-bones', ci.INSTALLED_SMOKE)
        self.assertIn("expected['delta_counts']['source'] == 0", ci.INSTALLED_SMOKE)
        self.assertIn('len(previous) == 6', ci.INSTALLED_SMOKE)
        self.assertIn('== 10', ci.INSTALLED_SMOKE)
        self.assertIn('full JSON equality and text value/caveat checks', ci.INSTALLED_SMOKE)
        self.assertIn('outputs == 32', ci.INSTALLED_SMOKE)

    def test_installed_protocol_retains_six_wheels_strict_offline_groups_and_independent_smoke(self):
        import inspect
        source = inspect.getsource(ci.check_installed)
        self.assertEqual(len(ci.PACKAGES), 6)
        self.assertIn('system_site_packages=False', source)
        self.assertIn("'--no-index', '--no-deps'", source)
        self.assertIn("'-I', '-B'", source)
        self.assertIn("'experimental/platform/ci/check_offline.py', 'installed-smoke'", source)
        self.assertEqual(ci.INSTALLED_GROUPS, ('query', 'formal', 'ingestion', 'relationships', 'provider', 'transport', 'lifecycle', 'integration'))
        self.assertEqual(ci.load_manifest()['installed_groups']['query']['count'], 249)
        self.assertEqual(sum(v['count'] for v in ci.load_manifest()['installed_groups'].values()), 577)
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / 'synthetic.whl').write_bytes(b'synthetic')
            output = io.StringIO()
            with patch.object(ci, 'verify_wheels', return_value=[directory / 'synthetic.whl'] * 6), \
                    patch.object(ci.venv.EnvBuilder, 'create'), \
                    patch.object(ci, 'run', side_effect=RuntimeError('synthetic installed failure')), \
                    redirect_stdout(output), self.assertRaisesRegex(RuntimeError, 'synthetic installed failure'):
                ci.check_installed(directory, directory)
            self.assertNotIn('EWURUM_REACTIVE_INSTALLED_COMPLETE', output.getvalue())

    def test_installed_required_ids_keep_all_previous_entries_and_exact_new_eight(self):
        path = 'experimental/platform/ci/required_test_ids.json'
        old, new = json.loads(git_bytes(path)), json.loads((ROOT / path).read_bytes())
        self.assertEqual(set(old), set(new))
        for key in old:
            with self.subTest(group=key):
                self.assertEqual(new[key][:len(old[key])], old[key])
                self.assertEqual(len(new[key]), len(set(new[key])))
                if key != 'local-catalog': self.assertEqual(new[key], old[key])
        added = new['local-catalog'][len(old['local-catalog']):]
        self.assertEqual(len(added), 8)
        self.assertTrue(all(identifier.startswith(('test_ewurum_reactive.EwurumReactiveQuery.',
            'test_baseline_compatibility.BaselineCompatibility.test_ewurum_reactive_')) for identifier in added))
        self.assertTrue(set(added) <= set(ci.load_manifest()['installed_groups']['query']['ids']))

    def test_cli_modes_reject_conflicts_and_misplaced_dependencies(self):
        for args in ([], ['--source-tests', '--validate-inventory'], ['--validate-scope', '--dependency-dir', 'wheels'],
                     ['--source-group', 'missing'], ['--installed-group', 'candidate']):
            with self.subTest(args=args), patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit):
                ci.main(args)

    def test_reused_source_requires_exact_existing_object_without_source_growth(self):
        candidate = ci.installation_payload()['candidate']
        before, current = {}, {}
        for key, filename in (('materials', 'materials.json'), ('properties', 'reference_properties.json'), ('sources', 'sources.json')):
            before[key] = json.loads(git_bytes('materials_boundaries/data/' + filename))
            current[key] = json.loads((ROOT / 'materials_boundaries/data' / filename).read_bytes())
        self.assertEqual(len(candidate['sources']['records']), 1)
        self.assertEqual(ci.CANDIDATE_COUNTS['source'], 1)
        self.assertEqual(ci.DELTA_COUNTS['source'], 0)
        self.assertEqual(current['sources'], before['sources'])
        ci.validate_append(candidate, before, current)
        for mutation in ('missing', 'duplicate', 'new_id', 'authors', 'license', 'source_append', 'source_metadata', 'source_order'):
            supplied, changed = deepcopy(candidate), deepcopy(current)
            if mutation == 'missing': supplied['sources']['records'].clear()
            elif mutation == 'duplicate': supplied['sources']['records'] *= 2
            elif mutation == 'new_id': supplied['sources']['records'][0]['id'] += '_copy'
            elif mutation == 'authors': supplied['sources']['records'][0]['authors'].append('Luis Alves')
            elif mutation == 'license': supplied['sources']['records'][0]['license']['identifier'] = 'unverified'
            elif mutation == 'source_append': changed['sources']['records'].append(deepcopy(supplied['sources']['records'][0]))
            elif mutation == 'source_metadata': changed['sources']['schema_version'] = 'unreviewed'
            else: changed['sources']['records'] = list(reversed(changed['sources']['records']))
            with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                ci.validate_append(supplied, before, changed)

    def test_complete_historical_modules_and_replay_profile_are_explicitly_executed(self):
        manifest = ci.load_manifest()
        group = manifest['source_groups']['compatibility']
        self.assertEqual(group['modules'], sorted([
            'test_bruns_borosilicate_ci', 'test_tarasov_pna_bpf_ci', 'test_kapoor_phosphate_ci',
            'test_tian_nano_ti_ci', 'test_family_adjacency_history', 'test_formulation_packet_integration',
            'test_formulation_packet_preparation', 'test_legacy_document_recovery', 'test_tian_nano_ti_preservation']))
        self.assertEqual(group['count'], 156)
        self.assertEqual(group['sha256'], '88056fef34fbe1deb87b539ca523d8229ed658df93e5b144054c2c25c87bd3c8')
        replay = manifest['source_groups']['replay']
        self.assertEqual(replay['selection'], 'frozen_replay_profile')
        self.assertEqual(replay['count'], 70)
        self.assertEqual(len(set(replay['ids']) & set(group['ids'])), 4)
        for key, count in (('prior-candidate', 18), ('prior-preservation', 12), ('prior-contracts', 15)):
            self.assertEqual(manifest['source_groups'][key]['count'], count)
        source = inspect.getsource(ci.load_group)
        self.assertIn('replay.load_suite()', source)
        self.assertIn('replay.validate_discovery(ids, frozen)', source)
        self.assertNotIn('replay.validate_context()', source)


if __name__ == '__main__':
    unittest.main()
