"""Adversarial receipt checks without executing any frozen core test."""
from copy import deepcopy
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'partition_receipt_contract_runner', ROOT / 'scripts/run_full_core_partition_ci.py')
ci = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ci
SPEC.loader.exec_module(ci)


class PartitionReceiptContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = ci.load_manifest()

    def context(self, version='3.11', dossier=False):
        return {
            'sha': '1' * 40, 'tree': '2' * 40, 'run_id': '40000000001',
            'run_attempt': '2', 'python_version': version,
            'python_full_version': version + '.99',
            'platform': {'system': 'Linux', 'os_name': 'posix',
                         'sys_platform': 'linux', 'machine': 'x86_64'},
            'manifest_sha256': sha256((ROOT / 'tests/core_partition/manifest.json').read_bytes()).hexdigest(),
            'runner_sha256': sha256((ROOT / 'scripts/run_full_core_partition_ci.py').read_bytes()).hexdigest(),
            'wood_review_dossier_present': dossier,
        }

    def receipt(self, partition=0, version='3.11', dossier=False):
        context = self.context(version, dossier)
        receipt = ci.new_receipt(self.manifest, partition, context,
                                 ci.manifest_ids(self.manifest))
        receipt['started_ids'] = list(receipt['expected_ids'])
        policy = ci.skip_contract(self.manifest, dossier)
        receipt['completed'] = [
            {'test_id': identifier,
             'status': 'skipped' if identifier in policy else 'passed',
             'reason': policy.get(identifier)}
            for identifier in receipt['expected_ids']]
        receipt['terminal'] = True
        receipt['terminal_status'] = 'completed'
        receipt['journal_sha256'] = '3' * 64
        return receipt

    def receipts(self, dossier=False):
        return [self.receipt(partition, version, dossier)
                for version in ('3.11', '3.12') for partition in range(4)]

    def validate(self, receipt, version='3.11', dossier=False):
        return ci.validate_receipt(receipt, self.manifest, self.context(version, dossier),
                                   expected_python=version)

    def aggregate(self, receipts, matrix_result='success', dossier=False):
        return ci.aggregate_receipts(receipts, self.manifest,
                                     self.context(dossier=dossier), matrix_result)

    def write_artifacts(self, directory, dossier=False):
        directory.mkdir()
        for receipt in self.receipts(dossier):
            context = receipt['context']
            child = directory / ('full-core-' + context['python_version'] + '-' +
                                 str(receipt['partition']) + '-' + context['run_id'] +
                                 '-' + context['run_attempt'])
            child.mkdir()
            events = [{'event': 'header', 'context': context, 'partition': receipt['partition']}]
            for record in receipt['completed']:
                events.append({'event': 'started', 'test_id': record['test_id']})
                events.append({'event': 'outcome', **record})
                events.append({'event': 'completed', **record})
            events.append({'event': 'terminal', 'terminal_status': 'completed'})
            for number, event in enumerate(events):
                event.update(sequence=number, monotonic_ns=number)
            raw = ''.join(json.dumps(event, sort_keys=True) + '\n' for event in events).encode('utf-8')
            receipt['journal_sha256'] = sha256(raw).hexdigest()
            (child / 'journal.jsonl').write_bytes(raw)
            (child / 'receipt.json').write_text(json.dumps(receipt), encoding='utf-8')
        return sorted(directory.iterdir())[0]

    @staticmethod
    def replace_journal(child, events, *, resequence=True):
        if resequence:
            for number, event in enumerate(events):
                event['sequence'] = number
                event['monotonic_ns'] = number
        raw = ''.join(json.dumps(event, sort_keys=True) + '\n' for event in events).encode('utf-8')
        (child / 'journal.jsonl').write_bytes(raw)
        receipt = json.loads((child / 'receipt.json').read_bytes())
        receipt['journal_sha256'] = sha256(raw).hexdigest()
        (child / 'receipt.json').write_text(json.dumps(receipt), encoding='utf-8')

    def test_complete_eight_receipts_cover_every_id_once_per_python(self):
        receipts = self.receipts()
        before = deepcopy((receipts, self.manifest))
        for version in ('3.11', '3.12'):
            selected = [row for row in receipts if row['context']['python_version'] == version]
            combined = [identifier for row in selected for identifier in row['expected_ids']]
            self.assertEqual(len(combined), 1887)
            self.assertEqual(len(set(combined)), 1887)
            self.assertEqual(set(combined), set(ci.manifest_ids(self.manifest)))
            for row in selected:
                self.validate(row, version)
        self.assertIsInstance(self.aggregate(receipts), dict)
        self.assertEqual((receipts, self.manifest), before)

    def test_missing_duplicate_extra_and_replaced_partition_receipts_fail(self):
        good = self.receipts()
        cases = {'missing': good[:-1], 'duplicate': good + [deepcopy(good[0])],
                 'replaced': good[:-1] + [deepcopy(good[0])], 'empty': []}
        extra = deepcopy(good)
        extra.append(self.receipt())
        extra[-1]['partition'] = 4
        cases['extra_unknown_partition'] = extra
        for label, receipts in cases.items():
            with self.subTest(case=label), self.assertRaises(RuntimeError):
                self.aggregate(receipts)

    def test_later_matrix_failure_cannot_be_hidden_by_complete_core_receipts(self):
        for state in ('failure', 'cancelled', 'skipped', '', None, True, 'success\n'):
            with self.subTest(matrix_result=state), self.assertRaises(RuntimeError):
                self.aggregate(self.receipts(), state)

    def test_each_receipt_is_bound_to_sha_tree_run_attempt_and_input_hashes(self):
        mutations = {
            'sha': 'a' * 40, 'tree': 'b' * 40, 'run_id': '40000000002',
            'run_attempt': '1', 'manifest_sha256': 'a' * 64,
            'runner_sha256': 'b' * 64,
        }
        for key, value in mutations.items():
            rows = self.receipts()
            rows[0]['context'][key] = value
            with self.subTest(field=key), self.assertRaises(RuntimeError):
                self.aggregate(rows)

    def test_wrong_python_platform_and_mixed_patch_versions_fail(self):
        for key, value in (
                ('python_version', '3.10'), ('python_version', '3.12'),
                ('python_full_version', '3.10.99'),
                ('platform', {'system': 'Windows', 'os_name': 'nt',
                              'sys_platform': 'win32', 'machine': 'AMD64'})):
            bad = self.receipt()
            bad['context'][key] = value
            with self.subTest(field=key, value=value), self.assertRaises(RuntimeError):
                self.validate(bad)
        rows = self.receipts()
        rows[0]['context']['python_full_version'] = '3.11.98'
        with self.assertRaises(RuntimeError):
            self.aggregate(rows)

    def test_missing_terminal_cancelled_and_incomplete_records_never_pass(self):
        for key, value in (('terminal', False), ('terminal', 1),
                           ('terminal_status', 'running'), ('terminal_status', 'cancelled'),
                           ('terminal_status', 'interrupted'), ('terminal_status', 'failed'),
                           ('journal_sha256', None), ('journal_sha256', 'not-a-hash')):
            bad = self.receipt()
            bad[key] = value
            with self.subTest(field=key, value=value), self.assertRaises(RuntimeError):
                self.validate(bad)
        for key in ('terminal', 'terminal_status', 'started_ids', 'completed', 'journal_sha256'):
            bad = self.receipt(); del bad[key]
            with self.subTest(missing=key), self.assertRaises(RuntimeError):
                self.validate(bad)

    def test_expected_failure_unexpected_success_and_nonpassing_outcomes_fail(self):
        for status in ('expected_failure', 'unexpected_success', 'failure', 'error',
                       'failed', 'cancelled', 'not_run', 'unknown'):
            bad = self.receipt()
            bad['completed'][0] = {'test_id': bad['expected_ids'][0],
                                   'status': status, 'reason': None}
            with self.subTest(status=status), self.assertRaises(RuntimeError):
                self.validate(bad)

    def test_fixture_subtest_and_protocol_errors_cannot_hide_under_passed_methods(self):
        for key in ('fixture_errors', 'subtest_errors', 'protocol_errors'):
            bad = self.receipt()
            bad[key] = [{'test_id': bad['expected_ids'][0], 'message': 'intentional fixture error'}]
            with self.subTest(field=key), self.assertRaises(RuntimeError):
                self.validate(bad)

    def test_missing_duplicate_unknown_and_reordered_started_ids_fail(self):
        good = self.receipt()
        ids = good['started_ids']
        cases = [ids[:-1], ids + [ids[0]], ids[:-1] + ['test_unreviewed.Case.test_x'],
                 list(reversed(ids))]
        for changed in cases:
            bad = deepcopy(good); bad['started_ids'] = changed
            with self.subTest(length=len(changed), first=changed[:1]), self.assertRaises(RuntimeError):
                self.validate(bad)

    def test_missing_duplicate_unknown_and_reordered_completed_ids_fail(self):
        good = self.receipt()
        records = good['completed']
        cases = [records[:-1], records + [records[0]], list(reversed(records))]
        replaced = deepcopy(records)
        replaced[-1]['test_id'] = 'test_unreviewed.Case.test_x'
        cases.append(replaced)
        for changed in cases:
            bad = deepcopy(good); bad['completed'] = changed
            with self.subTest(length=len(changed)), self.assertRaises(RuntimeError):
                self.validate(bad)

    def test_expected_declared_and_discovered_ids_reject_count_preserving_substitution(self):
        for field in ('expected_ids', 'declared_ids', 'discovered_ids'):
            for operation in ('substitute', 'drop', 'duplicate', 'reverse'):
                bad = self.receipt()
                ids = bad[field]
                if operation == 'substitute': ids[-1] = 'test_unreviewed.Case.test_x'
                elif operation == 'drop': ids.pop()
                elif operation == 'duplicate': ids[-1] = ids[0]
                else: ids.reverse()
                with self.subTest(field=field, operation=operation), self.assertRaises(RuntimeError):
                    self.validate(bad)

    def test_only_exact_environment_skip_ids_and_reasons_are_accepted(self):
        absent = ci.skip_contract(self.manifest, False)
        present = ci.skip_contract(self.manifest, True)
        self.assertEqual(len(absent), 18)
        self.assertEqual(len(present), 17)
        self.assertEqual(set(absent) - set(present), {
            'test_wood_bulk_adapter.ReviewedWoodAdapterTests.test_full_external_dossier_source_support_without_admission'})
        self.aggregate(self.receipts(dossier=True), dossier=True)
        for label in ('wrong_reason', 'missing_expected_skip', 'unlisted_skip'):
            rows = self.receipts()
            if label == 'unlisted_skip':
                outcome = next(item for row in rows for item in row['completed']
                               if item['status'] == 'passed')
                outcome.update(status='skipped', reason='requires actual native Windows on local NTFS')
            else:
                outcome = next(item for row in rows for item in row['completed']
                               if item['status'] == 'skipped')
                if label == 'wrong_reason': outcome['reason'] += ' (changed)'
                else: outcome.update(status='passed', reason=None)
            with self.subTest(case=label), self.assertRaises(RuntimeError):
                self.aggregate(rows)

    def test_environment_profile_cannot_change_between_partitions(self):
        rows = self.receipts()
        rows[0]['context']['wood_review_dossier_present'] = True
        with self.assertRaises(RuntimeError):
            self.aggregate(rows)
        rows = self.receipts(dossier=True)
        policy = ci.skip_contract(self.manifest, False)
        wood = next(identifier for identifier in policy if identifier not in ci.skip_contract(self.manifest, True))
        outcome = next(item for row in rows for item in row['completed'] if item['test_id'] == wood)
        outcome.update(status='skipped', reason=policy[wood])
        with self.assertRaises(RuntimeError):
            self.aggregate(rows, dossier=True)

    def test_unknown_fields_and_boolean_partition_are_not_accepted_as_ordinary_values(self):
        for key, value in (('partition', True), ('partition', -1), ('partition', '0'),
                           ('unreviewed_success', True)):
            bad = self.receipt(); bad[key] = value
            with self.subTest(field=key, value=value), self.assertRaises(RuntimeError):
                self.validate(bad)
        bad = self.receipt()
        bad['context']['unreviewed_override'] = True
        with self.assertRaises(RuntimeError):
            self.validate(bad)

    def test_later_manifest_reads_recheck_changed_bytes(self):
        source = ROOT / 'tests/core_partition/manifest.json'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / 'tests/core_partition/manifest.json'
            target.parent.mkdir(parents=True)
            target.write_bytes(source.read_bytes())
            self.assertEqual(ci.load_manifest(root), self.manifest)
            target.write_bytes(source.read_bytes() + b' ')
            with self.assertRaises(RuntimeError):
                ci.load_manifest(root)

    def test_manifest_semantic_drift_and_count_preserving_reassignment_fail(self):
        for operation in ('reverse_canonical', 'substitute', 'duplicate', 'partition',
                          'skip_reason', 'skip_id', 'unknown_field', 'boolean_count'):
            bad = deepcopy(self.manifest)
            if operation == 'reverse_canonical': bad['canonical_ids'].reverse()
            elif operation == 'substitute': bad['canonical_ids'][-1] = 'test_foreign.Case.test_x'
            elif operation == 'duplicate': bad['canonical_ids'][-1] = bad['canonical_ids'][0]
            elif operation == 'partition':
                bad['modules'][0]['partition'] = (bad['modules'][0]['partition'] + 1) % 4
            elif operation == 'skip_reason': bad['skip_rules'][0]['reason'] += ' changed'
            elif operation == 'skip_id': bad['skip_rules'][0]['test_ids'][0] = bad['canonical_ids'][0]
            elif operation == 'unknown_field': bad['allow_missing'] = True
            else: bad['test_count'] = True
            with self.subTest(operation=operation), self.assertRaises(RuntimeError):
                ci.validate_manifest(bad)

    def test_filesystem_collection_accepts_only_complete_journal_bound_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'artifacts'
            self.write_artifacts(directory)
            receipts = ci.load_receipts(directory, self.context())
            self.assertEqual(len(receipts), 8)
            result = self.aggregate(receipts)
            self.assertEqual(result['receipt_count'], 8)
            self.assertEqual({row['python_version'] for row in result['versions']}, {'3.11', '3.12'})
            self.assertTrue(all(row['completed'] == 1887 and row['passed'] == 1869 and
                                row['skipped'] == 18 and row['not_completed'] == 0
                                for row in result['versions']))

    def test_rehashed_empty_hidden_error_and_noncanonical_progress_journals_fail(self):
        mutations = ('empty_progress', 'hidden_fixture_error', 'hidden_subtest_error',
                     'unknown_start', 'duplicate_start', 'reordered_start',
                     'unknown_outcome', 'duplicate_outcome', 'changed_outcome',
                     'unknown_completion', 'duplicate_completion', 'missing_completion',
                     'middle_terminal', 'wrong_terminal')
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary) / 'artifacts'
                child = self.write_artifacts(directory)
                events = [json.loads(line) for line in (child / 'journal.jsonl').read_bytes().splitlines()]
                if mutation == 'empty_progress': events = [events[0], events[-1]]
                elif mutation == 'hidden_fixture_error':
                    events.insert(-1, {'event': 'fixture_error', 'test_id': 'setUpClass(Fixture)',
                                       'status': 'error', 'reason': None})
                elif mutation == 'hidden_subtest_error':
                    events.insert(-1, {'event': 'subtest_error', 'test_id': events[1]['test_id'],
                                       'subtest_id': 'intentional subtest', 'detail': {}})
                elif mutation == 'unknown_start': events[1]['test_id'] = 'test_foreign.Case.test_x'
                elif mutation == 'duplicate_start': events.insert(2, deepcopy(events[1]))
                elif mutation == 'reordered_start':
                    events[1]['test_id'], events[4]['test_id'] = events[4]['test_id'], events[1]['test_id']
                elif mutation == 'unknown_outcome': events[2]['test_id'] = 'test_foreign.Case.test_x'
                elif mutation == 'duplicate_outcome': events.insert(3, deepcopy(events[2]))
                elif mutation == 'changed_outcome': events[2].update(status='skipped', reason='unlisted')
                elif mutation == 'unknown_completion': events[3]['test_id'] = 'test_foreign.Case.test_x'
                elif mutation == 'duplicate_completion': events.insert(4, deepcopy(events[3]))
                elif mutation == 'missing_completion': events.pop(3)
                elif mutation == 'middle_terminal': events.insert(4, deepcopy(events[-1]))
                else: events[-1]['terminal_status'] = 'cancelled'
                # Rebind the digest: these are semantic protocol failures, not
                # merely a raw-byte checksum mismatch.
                self.replace_journal(child, events)
                with self.assertRaises(RuntimeError):
                    ci.load_receipts(directory, self.context())

    def test_collection_rejects_tampered_truncated_and_duplicate_key_files(self):
        for mutation in ('hash', 'truncated', 'duplicate_key', 'sequence', 'timestamp_type'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary) / 'artifacts'
                child = self.write_artifacts(directory)
                journal = child / 'journal.jsonl'
                if mutation == 'hash': journal.write_bytes(journal.read_bytes() + b' ')
                elif mutation == 'truncated':
                    raw = journal.read_bytes()[:-1]
                    journal.write_bytes(raw)
                    receipt = json.loads((child / 'receipt.json').read_bytes())
                    receipt['journal_sha256'] = sha256(raw).hexdigest()
                    (child / 'receipt.json').write_text(json.dumps(receipt), encoding='utf-8')
                elif mutation == 'duplicate_key':
                    receipt = child / 'receipt.json'
                    raw = receipt.read_text(encoding='utf-8')
                    receipt.write_text(raw[:-1] + ', "partition": 0}', encoding='utf-8')
                else:
                    events = [json.loads(line) for line in journal.read_bytes().splitlines()]
                    if mutation == 'sequence': events[1]['sequence'] = True
                    else: events[1]['monotonic_ns'] = True
                    self.replace_journal(child, events, resequence=False)
                with self.assertRaises((RuntimeError, ValueError)):
                    ci.load_receipts(directory, self.context())

    def test_collection_rejects_missing_extra_stale_and_misnamed_artifacts(self):
        for mutation in ('missing_receipt', 'missing_journal', 'extra_json',
                         'extra_directory', 'stale_directory', 'wrong_name_identity'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary) / 'artifacts'
                child = self.write_artifacts(directory)
                if mutation == 'missing_receipt': (child / 'receipt.json').unlink()
                elif mutation == 'missing_journal': (child / 'journal.jsonl').unlink()
                elif mutation == 'extra_json': (child / 'extra.json').write_text('{}', encoding='utf-8')
                elif mutation == 'extra_directory': (directory / 'duplicate-artifact').mkdir()
                elif mutation == 'stale_directory': child.rename(child.with_name(child.name + '-stale'))
                else:
                    receipt = json.loads((child / 'receipt.json').read_bytes())
                    receipt['partition'] = (receipt['partition'] + 1) % 4
                    (child / 'receipt.json').write_text(json.dumps(receipt), encoding='utf-8')
                with self.assertRaises(RuntimeError):
                    ci.load_receipts(directory, self.context())

    def test_aggregate_directory_preserves_a_rejection_when_matrix_failed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / 'artifacts'
            self.write_artifacts(directory)
            output = root / 'aggregate.json'
            stdout = io.StringIO()
            with patch.object(ci, 'load_manifest', return_value=self.manifest), \
                    patch.object(ci, 'production_context', return_value=self.context()), \
                    redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                code = ci.aggregate_directory(directory, 'failure', output, root)
            self.assertEqual(code, 1)
            report = json.loads(output.read_bytes())
            self.assertTrue(report['terminal'])
            self.assertEqual(report['terminal_status'], 'failed')
            self.assertEqual(report['matrix_result'], 'failure')
            self.assertNotIn('FULL_CORE_PARTITIONS_COMPLETE', stdout.getvalue())
            self.assertNotIn('versions', report)


if __name__ == '__main__':
    unittest.main()
