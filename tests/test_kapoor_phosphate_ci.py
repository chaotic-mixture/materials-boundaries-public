"""Fail-closed CI scope, complete inventories and exact Kapoor append contract."""
from copy import deepcopy
import contextlib
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('kapoor_phosphate_ci', ROOT / 'scripts/run_kapoor_phosphate_ci.py')
ci = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci)


class KapoorPhosphateCITests(unittest.TestCase):
    def test_previous_jobs_keep_every_step_and_only_new_branch_is_gated(self):
        prior = ci.git('show', ci.BASE_COMMIT + ':.github/workflows/ci.yml').decode('utf-8')
        current = ci.regression_checkpoint_bytes('.github/workflows/ci.yml').decode('utf-8')
        self.assertEqual(current, ci.expected_workflow(prior))
        restored = current.removesuffix(ci.TARGETED_JOB).replace(ci.FULL_JOB_IF, ci.PREVIOUS_FULL_JOB_IF)
        self.assertEqual(restored, prior)
        self.assertEqual(current.count('  kapoor-phosphate-targeted:\n'), 1)
        self.assertEqual(ci.FULL_JOB_IF.count(ci.BRANCH_REF), 1)
        self.assertIn("github.event_name != 'push'", ci.FULL_JOB_IF)
        self.assertIn("github.event_name == 'push'", ci.TARGETED_JOB)
        self.assertIn('persist-credentials: false', ci.TARGETED_JOB)
        self.assertIn("python-version: '3.11'", ci.TARGETED_JOB)
        self.assertIn("python-version: '3.12'", ci.TARGETED_JOB)
        self.assertEqual(ci.BRANCH_REF, 'refs/heads/experimental/kapoor2019-glass-runtime')

    def test_scope_rejects_unlisted_deleted_nonfile_and_symlink_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            allowed = 'scripts/run_kapoor_phosphate_ci.py'
            (root / 'scripts').mkdir()
            (root / allowed).write_text('fixture', encoding='utf-8')
            ci.validate_names([allowed], root=root)
            for names in (['credentials.json'], ['../outside'], [None],
                          ['experimental/platform/query-service/materials_query/pins/family_relationships.json'],
                          ['materials_boundaries/data/observations.json']):
                with self.subTest(names=names), self.assertRaises(RuntimeError):
                    ci.validate_names(names, root=root)
            with patch.object(Path, 'is_symlink', return_value=True), self.assertRaises(RuntimeError):
                ci.validate_names([allowed], root=root)
            (root / allowed).unlink()
            with self.assertRaises(RuntimeError):
                ci.validate_names([allowed], root=root)
            (root / allowed).mkdir()
            with self.assertRaises(RuntimeError):
                ci.validate_names([allowed], root=root)
        for raw in (b'D\0README.md\0', b'R100\0old\0new\0', b'M\0', b'A\0one\0M\0'):
            with self.subTest(raw=raw), self.assertRaises(RuntimeError):
                ci.changed_paths(raw)

    def test_ci_requires_exact_push_branch_sha_and_clean_checkout(self):
        expected = {'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_NAME': 'push',
                    'GITHUB_REF': ci.BRANCH_REF, 'GITHUB_SHA': 'f' * 40}
        with patch.dict(ci.os.environ, expected, clear=True), patch.object(ci, 'git', return_value=b''):
            ci.validate_event('f' * 40)
        for key, value in (('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_EVENT_NAME', 'workflow_dispatch'),
                           ('GITHUB_REF', 'refs/heads/main'), ('GITHUB_REF', ci.PREVIOUS_BRANCH_REF),
                           ('GITHUB_SHA', 'e' * 40), ('GITHUB_SHA', '')):
            with self.subTest(key=key, value=value), patch.dict(ci.os.environ, {**expected, key: value}, clear=True):
                with patch.object(ci, 'git', return_value=b''), self.assertRaises(RuntimeError):
                    ci.validate_event('f' * 40)
        with patch.dict(ci.os.environ, expected, clear=True), patch.object(ci, 'git', return_value=b' M README.md\n'):
            with self.assertRaises(RuntimeError):
                ci.validate_event('f' * 40)

    def test_ambiguous_yaml_scalars_and_index_package_builds_fail(self):
        ci.validate_targeted_run_scalars(ci.TARGETED_JOB)
        ci.validate_wheel_command(ci.BUILD_COMMAND)
        for verb in ('install', 'download'):
            marker = '      - run: "python -m pip ' + verb
            line = next(line for line in ci.TARGETED_JOB.splitlines() if line.startswith(marker))
            malformed = ci.TARGETED_JOB.replace(line, line.replace('run: "', 'run: ', 1)[:-1])
            with self.subTest(verb=verb), self.assertRaises(RuntimeError):
                ci.validate_targeted_run_scalars(malformed)
        for command in (ci.BUILD_COMMAND.replace('./formal-catalog', 'formal-catalog'),
                        ci.BUILD_COMMAND.replace('--no-index ', ''),
                        ci.BUILD_COMMAND.replace('./experimental/platform/lifecycle', 'https://example.invalid/package')):
            with self.subTest(command=command), self.assertRaises(RuntimeError):
                ci.validate_wheel_command(command)

    def test_unknown_predecessor_workflow_shapes_are_rejected(self):
        prior = ci.git('show', ci.BASE_COMMIT + ':.github/workflows/ci.yml').decode('utf-8')
        for value in (prior.replace(ci.PREVIOUS_FULL_JOB_IF, '', 1),
                      prior.replace('  evidence-batch-targeted:\n', '  missing-job:\n'),
                      prior.replace('  family-adjacency-targeted:\n', '  missing-job:\n'),
                      prior + ci.TARGETED_JOB):
            with self.subTest(length=len(value)), self.assertRaises(RuntimeError):
                ci.expected_workflow(value)

    def test_complete_inventories_preserve_every_predecessor_and_new_test(self):
        all_ids = []
        self.assertEqual(set(ci.TEST_GROUPS), {'core', 'query', 'formal', 'ingestion', 'relationships',
                                             'provider', 'transport', 'lifecycle', 'integration'})
        for name, (relative, _, _) in ci.TEST_GROUPS.items():
            with self.subTest(group=name):
                declared = ci.declared_test_ids(relative, regression_checkpoint=True)
                ci.validate_inventory(name, declared)
                prior = ci.declared_test_ids(relative, predecessor=True)
                self.assertTrue(prior)
                self.assertTrue(set(prior).issubset(declared))
                all_ids.extend(declared)
        self.assertEqual(len(all_ids), len(set(all_ids)))
        for module in ('test_kapoor_phosphate_packet', 'test_kapoor_phosphate_preservation',
                       'test_kapoor_phosphate_ci'):
            self.assertTrue(any(identifier.startswith(module + '.') for identifier in all_ids))
        required_path = 'experimental/platform/ci/required_test_ids.json'
        required = json.loads(ci.regression_checkpoint_bytes(required_path))
        prior_required = json.loads(ci.git('show', ci.DATA_BASE_COMMIT + ':' + required_path))
        self.assertEqual(set(required), set(prior_required))
        for group, old_ids in prior_required.items():
            self.assertEqual(required[group][:len(old_ids)], old_ids)
            self.assertEqual(len(required[group]), len(set(required[group])))
        extra = {group: required[group][len(old_ids):] for group, old_ids in prior_required.items()}
        self.assertEqual({group: len(ids) for group, ids in extra.items()},
                         {'hbn-projection': 0, 'nomad-ingestion': 2, 'local-catalog': 6})
        query_ids = ci.declared_test_ids('experimental/platform/query-service/catalog-tests', regression_checkpoint=True)
        ingestion_ids = ci.declared_test_ids('experimental/platform/ingestion', regression_checkpoint=True)
        self.assertEqual(set(extra['local-catalog']), {identifier for identifier in query_ids
                         if identifier.startswith('test_kapoor_phosphate.') or '.test_kapoor_' in identifier})
        self.assertEqual(set(extra['nomad-ingestion']), {identifier for identifier in ingestion_ids
                         if '.test_kapoor_' in identifier})

    def test_missing_duplicate_substituted_or_extra_inventory_ids_are_rejected(self):
        for name, (relative, _, _) in ci.TEST_GROUPS.items():
            ids = ci.declared_test_ids(relative, regression_checkpoint=True)
            for changed in (ids[:-1], ids + ids[:1], ids[1:] + ['different.Case.test_replacement'],
                            ids + ['different.Case.test_extra']):
                with self.subTest(group=name, count=len(changed)), self.assertRaises(RuntimeError):
                    ci.validate_inventory(name, changed)
        self.assertEqual(ci.inventory_fingerprint(['b', 'a']), ci.inventory_fingerprint(['a', 'b']))

    def test_current_payload_pins_exact_packet_data_baseline_and_unchanged_reviews(self):
        payload = ci.installation_payload(regression_checkpoint=True)
        self.assertEqual(payload['historical_regression_checkpoint'], ci.REGRESSION_CHECKPOINT)
        self.assertEqual(payload['delta_counts'], {'identity': 6, 'grade': 0, 'state': 6, 'property': 6, 'source': 1})
        self.assertEqual(payload['graph_counts'], {'identity': 1159, 'grade': 31, 'state': 1160, 'property': 1171, 'source': 126})
        self.assertEqual(payload['formal_counts']['formal_project_admission_count'], 1183)
        self.assertEqual(payload['formal_counts']['reviewed_computed_composition_count'], 24)
        self.assertEqual(len(payload['packages']), 6)
        self.assertEqual(set(payload['preserved_resources']), set(ci.PRESERVED_RESOURCES))
        for name in ('PACKET_SHA256', 'QUERY_BASELINE_SHA256'):
            with self.subTest(pin=name), patch.object(ci, name, '0' * 64), self.assertRaises(RuntimeError):
                ci.installation_payload(regression_checkpoint=True)
        with patch.dict(ci.RESOURCE_HASHES, {'materials.json': '0' * 64}), self.assertRaises(RuntimeError):
            ci.installation_payload(regression_checkpoint=True)

    def test_append_rejects_count_preserving_rewrite_partial_order_metadata_and_id_drift(self):
        before = {'materials': {'identities': [{'id': 'old', 'category': 'inorganic'}], 'grades': [], 'records': [], 'version': '1'},
                  'properties': {'records': []}, 'sources': {'records': []}}
        candidate = {'materials': {'identities': [{'id': 'new', 'category': 'inorganic'}], 'grades': [], 'records': []},
                     'properties': {'records': []}, 'sources': {'records': []}}
        current = deepcopy(before)
        current['materials']['identities'] += deepcopy(candidate['materials']['identities'])
        total = {'identity': 2, 'grade': 0, 'state': 0, 'property': 0, 'source': 0}
        delta = {**total, 'identity': 1}
        with patch.object(ci, 'GRAPH_COUNTS', total), patch.object(ci, 'DELTA_COUNTS', delta), \
                patch.object(ci, 'PRIMARY_COUNTS', {'inorganic': 2}):
            ci.validate_append(candidate, before, current)
            for mutation in ('partial', 'old_row', 'new_row', 'order', 'metadata'):
                altered = deepcopy(current)
                if mutation == 'partial':
                    altered['materials']['identities'].pop()
                elif mutation == 'old_row':
                    altered['materials']['identities'][0]['category'] = 'metal'
                elif mutation == 'new_row':
                    altered['materials']['identities'][1]['id'] = 'changed'
                elif mutation == 'order':
                    altered['materials']['identities'].reverse()
                else:
                    altered['materials']['version'] = '2'
                with self.subTest(mutation=mutation), self.assertRaises(RuntimeError):
                    ci.validate_append(candidate, before, altered)
            for rows in ([{'id': 'old'}], [{'id': 'new'}, {'id': 'new'}]):
                changed = deepcopy(candidate)
                changed['materials']['identities'] = rows
                with self.assertRaises(RuntimeError):
                    ci.validate_append(changed, before, current)
        candidate['materials']['identities'] = [
            {'id': 'new-z', 'category': 'inorganic'}, {'id': 'new-a', 'category': 'inorganic'},
        ]
        current = deepcopy(before)
        current['materials']['identities'].extend(reversed(candidate['materials']['identities']))
        with patch.object(ci, 'GRAPH_COUNTS', {**total, 'identity': 3}), \
                patch.object(ci, 'DELTA_COUNTS', {**delta, 'identity': 2}), \
                patch.object(ci, 'PRIMARY_COUNTS', {'inorganic': 3}):
            ci.validate_append(candidate, before, current)
            current['materials']['identities'][1:] = candidate['materials']['identities']
            with self.assertRaises(RuntimeError):
                ci.validate_append(candidate, before, current)

    def test_installed_protocol_is_six_wheels_no_index_and_all_complete_suites(self):
        calls = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dependency = root / 'deps'
            dependency.mkdir()
            (dependency / 'dependency.whl').write_bytes(b'fixture')
            wheels = [root / (str(index) + '.whl') for index in range(6)]
            with patch.object(ci, 'verify_wheels', return_value=wheels) as verified, \
                    patch.object(ci.venv.EnvBuilder, 'create'), patch.object(ci, 'installation_payload', return_value={}), \
                    patch.object(ci, 'run', side_effect=lambda command, **kwargs: calls.append((list(map(str, command)), kwargs))):
                ci.check_installed(root, dependency)
            verified.assert_called_once_with(root)
        install_calls = [command for command, _ in calls if 'install' in command]
        self.assertEqual(len(install_calls), 2)
        self.assertTrue(all('--no-index' in command and '--no-deps' in command and '--isolated' in command
                            for command in install_calls))
        self.assertTrue(all(str(wheel) in install_calls[1] for wheel in wheels))
        groups = [command[-1] for command, _ in calls if '--installed-group' in command]
        self.assertEqual(groups, [name for name in ci.TEST_GROUPS if name != 'core'])
        self.assertTrue(all('-I' in command for command, _ in calls if '--installed-group' in command))
        self.assertTrue(any(command[-1] == 'installed-smoke' for command, _ in calls))
        self.assertTrue(all(kwargs['cwd'] != ROOT for _, kwargs in calls))


def synthetic_result(ids, skips):
    skipped_ids = {identifier for identifier, _ in skips}
    return SimpleNamespace(
        testsRun=len(ids),
        started_ids=list(ids),
        passed_ids=[identifier for identifier in ids if identifier not in skipped_ids],
        skipped=[
            (SimpleNamespace(id=lambda identifier=identifier: identifier), reason)
            for identifier, reason in skips
        ],
        expectedFailures=[],
        unexpectedSuccesses=[],
        wasSuccessful=lambda: True,
    )


class KapoorPhosphateTargetedCoreTests(unittest.TestCase):
    def test_targeted_inventory_is_all_cases_from_exact_complete_modules(self):
        expected_modules = {
            'test_release_metadata', 'test_bruns_borosilicate_packet',
            'test_bruns_borosilicate_preservation', 'test_kapoor_phosphate_ci',
            'test_legacy_document_recovery', 'test_material_class_counts_preservation',
            'test_material_bulk_preservation', 'test_composite_preservation',
            'test_evidence_dedup_preservation', 'test_material_batch_preservation',
            'test_material_catalog_preservation', 'test_family_adjacency_history',
            'test_family_adjacency_ci', 'test_material_append_merge',
            'test_bruns_borosilicate_ci', 'test_formulation_packet_preparation',
            'test_formulation_packet_integration', 'test_kapoor_phosphate_packet',
            'test_kapoor_phosphate_preservation',
            'test_tarasov_pna_bpf_ci', 'test_tarasov_pna_bpf_packet',
            'test_tarasov_pna_bpf_preservation',
        }
        self.assertEqual(set(ci.TARGETED_CORE_MODULES), expected_modules)
        self.assertEqual(len(ci.TARGETED_CORE_MODULES), len(expected_modules))
        all_ids = ci.declared_test_ids('tests', regression_checkpoint=True)
        selected = [identifier for identifier in all_ids if identifier.split('.')[0] in expected_modules]
        self.assertEqual(tuple(selected), ci.TARGETED_CORE_IDS)
        self.assertEqual(len(selected), ci.TARGETED_CORE_COUNT)
        self.assertEqual(ci.inventory_fingerprint(selected), ci.TARGETED_CORE_SHA256)
        self.assertTrue(set(selected) < set(all_ids))
        ci.validate_inventory('core', all_ids)
        ci.validate_inventory('targeted-core', selected)
        self.assertIn(self.id().split('tests.')[-1], selected)

    def test_targeted_discovery_loads_complete_modules_not_individual_ids(self):
        with patch.object(ci.unittest.TestLoader, 'discover', autospec=True,
                          wraps=None) as discover, patch.object(ci, 'validate_inventory'):
            discover.return_value = unittest.TestSuite()
            ci.load_group('targeted-core')
        self.assertEqual([call.kwargs['pattern'] for call in discover.call_args_list],
                         [module + '.py' for module in ci.TARGETED_CORE_MODULES])
        self.assertTrue(all(call.args[1] == str(ROOT / 'tests') for call in discover.call_args_list))

    def test_real_targeted_discovery_matches_frozen_ids_without_running_cases(self):
        _, discovered = ci.load_group('targeted-core')
        self.assertEqual(tuple(sorted(discovered)), ci.TARGETED_CORE_IDS)
        self.assertEqual(len(discovered), len(set(discovered)))

    def test_targeted_inventory_rejects_missing_duplicate_substituted_and_extra_ids(self):
        ids = list(ci.TARGETED_CORE_IDS)
        for altered in (ids[:-1], ids + ids[:1], ids[1:] + ['replacement.Case.test_other'],
                        ids + ['test_kapoor_phosphate_ci.NewCase.test_new']):
            with self.subTest(count=len(altered)), self.assertRaises(RuntimeError):
                ci.validate_inventory('targeted-core', altered)
        with patch.object(ci, 'TARGETED_CORE_SHA256', '0' * 64), self.assertRaises(RuntimeError):
            ci.validate_inventory('targeted-core', ids)
        with patch.object(ci, 'TARGETED_CORE_COUNT', len(ids) - 1), self.assertRaises(RuntimeError):
            ci.validate_inventory('targeted-core', ids)

    def test_targeted_loading_errors_are_not_a_partial_pass(self):
        loader = SimpleNamespace(errors=['broken module'], discover=lambda *args, **kwargs: unittest.TestSuite())
        with patch.object(ci.unittest, 'TestLoader', return_value=loader), self.assertRaisesRegex(RuntimeError, 'loading failed'):
            ci.load_group('targeted-core')

    def test_full_mode_still_discovers_all_core_tests(self):
        with patch.object(ci.unittest.TestLoader, 'discover', return_value=unittest.TestSuite()) as discover, \
                patch.object(ci, 'validate_inventory') as validate:
            ci.load_group('core')
        discover.assert_called_once_with(str(ROOT / 'tests'), pattern='test*.py')
        validate.assert_called_once_with('core', [])

    def test_cli_selects_targeted_full_and_installed_modes_unambiguously(self):
        for arguments, selected in ((['--targeted-core'], 'targeted-core'), (['--test'], 'core'),
                                    (['--installed-group', 'query'], 'query')):
            with self.subTest(arguments=arguments), patch.object(ci, 'validate_scope') as scope, \
                    patch.object(ci, 'run_group') as run_group, patch.object(ci, 'check_installed') as installed:
                ci.main(arguments)
                run_group.assert_called_once_with(selected)
                self.assertEqual(scope.call_count, 0 if selected == 'query' else 1)
                installed.assert_not_called()
        with patch.object(ci, 'validate_scope') as scope, patch.object(ci, 'run_group') as group:
            ci.main(['--validate-scope'])
            scope.assert_called_once_with()
            group.assert_not_called()

    def test_cli_rejects_conflicting_modes_and_misplaced_dependencies(self):
        for arguments in (['--test', '--targeted-core'], ['--targeted-core', '--installed-group', 'query'],
                          ['--targeted-core', '--wheel-dir', 'dist'],
                          ['--targeted-core', '--dependency-dir', 'deps'],
                          ['--test', '--dependency-dir', 'deps'], ['--installed-group', 'targeted-core']):
            with self.subTest(arguments=arguments), patch.object(ci, 'validate_scope') as scope, \
                    patch.object(ci, 'run_group') as group, contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as error:
                ci.main(arguments)
            self.assertEqual(error.exception.code, 2)
            scope.assert_not_called()
            group.assert_not_called()

    def test_targeted_results_cannot_use_any_source_skip_exception(self):
        ids = list(ci.TARGETED_CORE_IDS)
        for reason in ('optional dependency missing', 'requires actual native Windows on local NTFS', None):
            result = synthetic_result(ids, [(ids[0], reason)])
            with self.subTest(reason=reason), self.assertRaises(RuntimeError):
                ci.validate_result('targeted-core', ids, result)
        contract = ci.source_skip_contract(platform_name='posix', dossier_enabled=False)
        with self.assertRaises(RuntimeError):
            ci.validate_result('targeted-core', ids, synthetic_result(ids, []), skip_contract=contract)

    def test_targeted_results_reject_unexecuted_duplicate_failed_or_unpassed_cases(self):
        ids = list(ci.TARGETED_CORE_IDS)
        for attribute, value in (('testsRun', len(ids) - 1), ('started_ids', ids[:-1]),
                                 ('started_ids', ids[:-1] + ids[:1]), ('passed_ids', ids[:-1]),
                                 ('passed_ids', ids[:-1] + ids[:1]), ('wasSuccessful', lambda: False),
                                 ('expectedFailures', [('test', 'expected')]), ('unexpectedSuccesses', ['test'])):
            result = synthetic_result(ids, [])
            setattr(result, attribute, value)
            with self.subTest(attribute=attribute), self.assertRaises(RuntimeError):
                ci.validate_result('targeted-core', ids, result)

    def test_targeted_summary_distinguishes_excluded_cases_from_passes_and_skips(self):
        ids = list(ci.TARGETED_CORE_IDS)
        summary = ci.validate_result('targeted-core', ids, synthetic_result(ids, []))
        self.assertEqual(summary['coverage'], 'targeted-core-only')
        self.assertFalse(summary['full_core_reproduction'])
        self.assertEqual(summary['passed'], ci.TARGETED_CORE_COUNT)
        self.assertEqual(summary['skipped'], 0)
        self.assertEqual(summary['not_selected_count'], ci.TEST_GROUPS['core'][1] - len(ids))
        self.assertGreater(summary['not_selected_count'], 0)
        self.assertEqual(summary['not_selected_status'], 'not run; neither passed nor skipped')
        self.assertEqual(ci.coverage_description('core')['coverage'], 'full-core')
        self.assertTrue(ci.coverage_description('core')['full_core_reproduction'])
        self.assertEqual(ci.coverage_description('query')['coverage'], 'complete-installed-group')
        self.assertFalse(ci.coverage_description('query')['full_core_reproduction'])

    def test_targeted_runner_emits_honest_coverage_and_never_requests_source_skips(self):
        ids = list(ci.TARGETED_CORE_IDS)
        output = io.StringIO()
        runner = SimpleNamespace(run=lambda suite: synthetic_result(ids, []))
        with patch.object(ci, 'install_offline_guard'), \
                patch('socket.getaddrinfo', side_effect=RuntimeError('Offline fixture CI')), \
                patch.object(ci, 'load_group', return_value=(unittest.TestSuite(), ids)), \
                patch.object(ci.unittest, 'TextTestRunner', return_value=runner), \
                patch.object(ci, 'source_skip_contract') as skips, \
                patch.object(ci, 'installed_origins') as origins, contextlib.redirect_stdout(output):
            ci.run_group('targeted-core')
        skips.assert_not_called()
        origins.assert_not_called()
        records = [json.loads(line.split(' ', 1)[1]) for line in output.getvalue().splitlines()]
        self.assertEqual(len(records), 2)
        for record in records:
            self.assertEqual(record['group'], 'targeted-core')
            self.assertEqual(record['coverage'], 'targeted-core-only')
            self.assertFalse(record['full_core_reproduction'])
            self.assertEqual(record['not_selected_status'], 'not run; neither passed nor skipped')
        self.assertEqual(records[-1]['passed'], len(ids))

    def test_failed_targeted_execution_cannot_emit_complete(self):
        ids = list(ci.TARGETED_CORE_IDS)
        failed = synthetic_result(ids, [])
        failed.wasSuccessful = lambda: False
        output = io.StringIO()
        with patch.object(ci, 'install_offline_guard'), \
                patch('socket.getaddrinfo', side_effect=RuntimeError('Offline fixture CI')), \
                patch.object(ci, 'load_group', return_value=(unittest.TestSuite(), ids)), \
                patch.object(ci.unittest, 'TextTestRunner', return_value=SimpleNamespace(run=lambda suite: failed)), \
                contextlib.redirect_stdout(output), self.assertRaises(RuntimeError):
            ci.run_group('targeted-core')
        self.assertNotIn('COMPLETE ', output.getvalue())

    def test_hosted_job_uses_targeted_core_and_keeps_installed_protocol(self):
        self.assertIn('run_kapoor_phosphate_ci.py --targeted-core\n', ci.TARGETED_JOB)
        self.assertNotIn('run_kapoor_phosphate_ci.py --test\n', ci.TARGETED_JOB)
        self.assertIn('run_kapoor_phosphate_ci.py --wheel-dir dist --dependency-dir dist/dependencies', ci.TARGETED_JOB)
        self.assertEqual(len(ci.TEST_GROUPS) - 1, 8)
        self.assertEqual(sum(count for name, (_, count, _) in ci.TEST_GROUPS.items() if name != 'core'), 552)
        self.assertEqual(len(ci.PACKAGES), 6)
        self.assertIn('    timeout-minutes: ' + str(ci.HOSTED_TIMEOUT_MINUTES) + '\n', ci.TARGETED_JOB)
        ci.require_frozen()

    def test_full_runner_keeps_exact_source_skip_policy(self):
        contract = ci.source_skip_contract(platform_name='posix', dossier_enabled=False)
        ids = sorted([*contract[0], 'extra.Case.test_pass'])
        result = synthetic_result(ids, list(contract[0].items()))
        with patch.object(ci, 'install_offline_guard'), \
                patch('socket.getaddrinfo', side_effect=RuntimeError('Offline fixture CI')), \
                patch.object(ci, 'load_group', return_value=(unittest.TestSuite(), ids)), \
                patch.object(ci.unittest, 'TextTestRunner', return_value=SimpleNamespace(run=lambda suite: result)), \
                patch.object(ci, 'source_skip_contract', return_value=contract) as skips, \
                contextlib.redirect_stdout(io.StringIO()):
            summary = ci.run_group('core')
        skips.assert_called_once_with()
        self.assertEqual(summary['coverage'], 'full-core')
        self.assertEqual(summary['passed'], 1)
        self.assertEqual(summary['skipped'], 18)


class KapoorCandidateAndFreezeTests(unittest.TestCase):
    def test_pending_profile_and_budget_cannot_authorize_scope(self):
        # A synthetic accepted budget isolates each negative gate; this is not
        # an approval or a benchmark of the actual pending draft profile.
        budget_line = next(line for line in ci.TARGETED_JOB.splitlines()
                           if line.startswith('    timeout-minutes: '))
        synthetic_budget = int(budget_line.split(':', 1)[1])
        with patch.object(ci, 'FINALIZATION_STATUS', 'reviewed-frozen'), \
                patch.object(ci, 'HOSTED_TIMEOUT_MINUTES', synthetic_budget):
            ci.require_frozen()
            for field, value in (('FINALIZATION_STATUS', 'pending-parent-freeze'),
                                 ('HOSTED_TIMEOUT_MINUTES', None),
                                 ('HOSTED_TIMEOUT_MINUTES', True),
                                 ('APPROVED_FILES', frozenset()),
                                 ('QUERY_BASELINE_SHA256', ''),
                                 ('TARGETED_CORE_COUNT', 0),
                                 ('TARGETED_CORE_SHA256', '')):
                with self.subTest(field=field, value=value), patch.object(ci, field, value):
                    with self.assertRaises(RuntimeError):
                        ci.require_frozen()
        with patch.object(ci, 'FINALIZATION_STATUS', 'pending-parent-freeze'), \
                patch.object(ci, 'git') as git, self.assertRaises(RuntimeError):
            ci.validate_scope()
        git.assert_not_called()

    def test_candidate_manifest_rejects_wrong_history_status_and_packet(self):
        manifest = json.loads((ROOT / ci.PACKET_PATH).with_name('integration.json').read_bytes())
        ci.validate_manifest(manifest)
        for field, value in (('released_main_count', 1177), ('status_adjustments', [{}]),
                             ('baseline_sha256', {}), ('batches', [])):
            changed = deepcopy(manifest)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                ci.validate_manifest(changed)
        for field, value in (('candidate_commit', ci.DATA_BASE_COMMIT),
                             ('packet', {'path': 'prepared-packet.json', 'sha256': '0' * 64})):
            changed = deepcopy(manifest)
            changed['batches'][0][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                ci.validate_manifest(changed)

    def test_candidate_artifacts_are_exact_and_not_promoted_to_completed_claims(self):
        self.assertEqual(len(ci.CANDIDATE_ARTIFACTS), 10)
        ci.validate_candidate_artifacts(regression_checkpoint=True)
        with patch.object(ci, 'git', return_value=b'changed candidate evidence'), self.assertRaises(RuntimeError):
            ci.validate_candidate_artifacts(regression_checkpoint=True)
        with patch.object(Path, 'is_symlink', return_value=True), self.assertRaises(RuntimeError):
            ci.validate_candidate_artifacts(regression_checkpoint=True)
        packet = json.loads((ROOT / ci.PACKET_PATH).read_bytes())
        self.assertEqual(packet['review']['formal_admitted_delta'], 0)
        self.assertEqual(packet['report']['formal_admitted_delta'], 0)
        self.assertFalse(packet['review']['verification']['independent_scientific_review'])
        self.assertFalse(packet['review']['verification']['raw_data_reanalysis'])

    def test_skip_contract_is_reused_without_a_new_exception(self):
        import run_tarasov_pna_bpf_ci as predecessor
        self.assertIs(ci.source_skip_contract, predecessor.source_skip_contract)
        for platform in ('nt', 'posix'):
            for dossier in (False, True):
                self.assertEqual(ci.source_skip_contract(platform_name=platform, dossier_enabled=dossier),
                                 predecessor.source_skip_contract(platform_name=platform, dossier_enabled=dossier))

    def test_installed_failure_cannot_emit_terminal_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            historical = directory / 'historical.json'
            historical.write_text(json.dumps({'historical_regression_checkpoint': ci.REGRESSION_CHECKPOINT}),
                                  encoding='utf-8')
            with patch.object(ci.sys, 'argv', ['installed-smoke', str(historical)]), \
                    self.assertRaisesRegex(RuntimeError, 'Installed smoke requires live payload'):
                exec(compile(ci.INSTALLED_SMOKE, '<installed-smoke>', 'exec'), {'__name__': '__main__'})
            (directory / 'fixture.whl').write_bytes(b'fixture')
            output = io.StringIO()
            with patch.object(ci, 'verify_wheels', return_value=[directory / 'fixture.whl'] * 6), \
                    patch.object(ci.venv.EnvBuilder, 'create'), \
                    patch.object(ci, 'run', side_effect=RuntimeError('bounded installed failure')), \
                    contextlib.redirect_stdout(output), self.assertRaisesRegex(RuntimeError, 'bounded installed failure'):
                ci.check_installed(directory, directory)
            self.assertNotIn('Complete Kapoor installed contract', output.getvalue())


if __name__ == '__main__':
    unittest.main()
