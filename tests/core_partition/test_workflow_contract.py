"""Validate the actual partitioned workflow before any historical projection.

These explicit-directory contracts do not add methods to the frozen root or
replay inventories. The original generic steps and eligibility are immutable
inputs; only the documented Ubuntu partition and aggregation wiring is added.
"""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = 'bf1c7a86068c37c2733ac4d25c268144090f9aad'
WORKFLOW_PATH = '.github/workflows/ci.yml'
BASE_WORKFLOW_SHA256 = '126dda53574573de098826a39a3d4c6dab373012193563e3760cd84e6f100982'
FULL_DISCOVERY = '      - run: python -m unittest discover -s tests -v\n'
CONTRACT_AND_PARTITION = (
    '      - run: python -m unittest discover -s tests/core_partition -v\n'
    '      - run: python scripts/run_full_core_partition_ci.py run --partition '
    '${{ matrix.partition }} --output-dir core-ci-results\n'
)
UPLOAD_PARTITION = '''      - name: Preserve full core partition diagnostics
        if: ${{ always() }}
        uses: actions/upload-artifact@v4
        with:
          name: full-core-${{ matrix.python-version }}-${{ matrix.partition }}-${{ github.run_id }}-${{ github.run_attempt }}
          path: |
            core-ci-results/receipt.json
            core-ci-results/journal.jsonl
          if-no-files-found: error
'''
AGGREGATE_BODY = '''    needs: unit-and-schema
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/download-artifact@v4
        with:
          pattern: full-core-*-${{ github.run_id }}-${{ github.run_attempt }}
          path: core-ci-receipts
          merge-multiple: false
      - name: Verify every full core partition and later matrix steps
        run: >-
          python scripts/run_full_core_partition_ci.py aggregate
          --receipts-dir core-ci-receipts
          --matrix-result "${{ needs.unit-and-schema.result }}"
          --output core-ci-aggregate.json
      - name: Preserve full core aggregation diagnostics
        if: ${{ always() }}
        uses: actions/upload-artifact@v4
        with:
          name: full-core-aggregate-${{ github.run_id }}-${{ github.run_attempt }}
          path: core-ci-aggregate.json
          if-no-files-found: error
'''


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def git_file(relative):
    return subprocess.run(
        ['git', 'show', BASE_COMMIT + ':' + relative], cwd=ROOT,
        capture_output=True, timeout=30, check=True,
    ).stdout


def job_blocks(raw):
    require(type(raw) is bytes and b'\r' not in raw, 'Expected LF workflow bytes')
    matches = list(re.finditer(rb'^  ([a-z0-9-]+):\n', raw, re.MULTILINE))
    require(matches, 'Workflow jobs are missing')
    names = [match[1].decode('ascii') for match in matches]
    require(len(set(names)) == len(names), 'Duplicate job names')
    return raw[:matches[0].start()], {
        name: raw[match.start():matches[index + 1].start()
                  if index + 1 < len(matches) else len(raw)]
        for index, (name, match) in enumerate(zip(names, matches))
    }


def expected_partition_jobs(baseline):
    require(sha256(baseline).hexdigest() == BASE_WORKFLOW_SHA256,
            'Unreviewed baseline workflow')
    _, original_jobs = job_blocks(baseline)
    original = original_jobs['unit-and-schema'].decode('utf-8')
    before = ('    runs-on: ubuntu-latest\n'
              '    strategy:\n'
              '      matrix:\n'
              "        python-version: ['3.11', '3.12']\n")
    after = ('    runs-on: ubuntu-latest\n'
             '    timeout-minutes: 360\n'
             '    strategy:\n'
             '      fail-fast: false\n'
             '      matrix:\n'
             "        python-version: ['3.11', '3.12']\n"
             '        partition: [0, 1, 2, 3]\n')
    require(original.count(before) == original.count(FULL_DISCOVERY) == 1,
            'Unexpected original generic execution shape')
    unit = original.replace(before, after).replace(FULL_DISCOVERY, CONTRACT_AND_PARTITION)
    unit += UPLOAD_PARTITION
    eligibility_lines = [line for line in original.splitlines()
                         if line.startswith('    if: ${{ ') and line.endswith(' }}')]
    require(len(eligibility_lines) == 1, 'Original eligibility is ambiguous')
    eligibility = eligibility_lines[0][len('    if: ${{ '):-len(' }}')]
    aggregate = ('  unit-and-schema-aggregate:\n'
                 '    if: ${{ always() && (' + eligibility + ') }}\n'
                 + AGGREGATE_BODY)
    return unit.encode('utf-8'), aggregate.encode('utf-8')


def expected_workflow(baseline):
    header, original_jobs = job_blocks(baseline)
    unit, aggregate = expected_partition_jobs(baseline)
    return header + b''.join(
        unit + aggregate if name == 'unit-and-schema' else raw
        for name, raw in original_jobs.items()
    )


def validate_actual_workflow(raw, baseline):
    """Reject changed actual execution, including an old projected workflow."""
    header, actual = job_blocks(raw)
    old_header, original = job_blocks(baseline)
    unit, aggregate = expected_partition_jobs(baseline)
    names = list(original)
    names.insert(names.index('unit-and-schema') + 1, 'unit-and-schema-aggregate')
    require(header == old_header, 'Event coverage or permissions changed')
    require(list(actual) == names, 'A job is missing, duplicated, added or reordered')
    require(actual['unit-and-schema'] == unit,
            'Actual Ubuntu partitions or original ordered steps differ')
    require(actual['unit-and-schema-aggregate'] == aggregate,
            'Actual aggregate eligibility, receipts or matrix-result gate differs')
    for name, old in original.items():
        if name != 'unit-and-schema':
            require(actual[name] == old, 'An unrelated job changed: ' + name)
    require(raw == expected_workflow(baseline), 'Unknown workflow content')
    return actual


class FullCorePartitionWorkflowContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = git_file(WORKFLOW_PATH)
        cls.actual = (ROOT / WORKFLOW_PATH).read_bytes()

    def test_actual_workflow_has_all_eight_partitions_and_successful_matrix_aggregation(self):
        jobs = validate_actual_workflow(self.actual, self.baseline)
        unit = jobs['unit-and-schema']
        aggregate = jobs['unit-and-schema-aggregate']
        self.assertIn(b"python-version: ['3.11', '3.12']\n", unit)
        self.assertIn(b'partition: [0, 1, 2, 3]\n', unit)
        self.assertIn(b'timeout-minutes: 360\n', unit)
        self.assertIn(b'fail-fast: false\n', unit)
        self.assertIn(b'needs: unit-and-schema\n', aggregate)
        self.assertIn(b'--matrix-result "${{ needs.unit-and-schema.result }}"', aggregate)
        self.assertIn(b'merge-multiple: false\n', aggregate)
        self.assertNotIn(b'continue-on-error', unit + aggregate)
        self.assertNotIn(b'actions/cache', unit + aggregate)

    def test_all_original_non_root_steps_and_relative_order_are_preserved(self):
        _, old = job_blocks(self.baseline)
        jobs = validate_actual_workflow(self.actual, self.baseline)
        old_lines = old['unit-and-schema'].splitlines()
        old_runs = [line for line in old_lines if line.startswith(b'      - run: ')
                    and line != FULL_DISCOVERY.encode().rstrip(b'\n')]
        current = jobs['unit-and-schema']
        positions = [current.index(line + b'\n') for line in old_runs]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(old_runs), 6)
        self.assertEqual(current.count(CONTRACT_AND_PARTITION.encode()), 1)
        self.assertGreater(current.index(UPLOAD_PARTITION.encode()), positions[-1])
        for name, raw in old.items():
            if name != 'unit-and-schema':
                with self.subTest(job=name):
                    self.assertEqual(jobs[name], raw)

    def test_original_event_eligibility_is_exact_for_partitions_and_aggregate(self):
        _, old = job_blocks(self.baseline)
        jobs = validate_actual_workflow(self.actual, self.baseline)
        old_condition = next(line for line in old['unit-and-schema'].splitlines()
                             if line.startswith(b'    if: '))
        condition = old_condition[len(b'    if: ${{ '):-len(b' }}')]
        self.assertIn(old_condition + b'\n', jobs['unit-and-schema'])
        self.assertIn(b'    if: ${{ always() && (' + condition + b') }}\n',
                      jobs['unit-and-schema-aggregate'])
        self.assertEqual(condition.count(b"github.ref != '"), 19)
        self.assertTrue(self.actual.startswith(b'name: tests\non: [push, pull_request]\n'))

    def test_artifacts_preserve_diagnostics_and_bind_run_attempt_without_cache(self):
        jobs = validate_actual_workflow(self.actual, self.baseline)
        unit, aggregate = jobs['unit-and-schema'], jobs['unit-and-schema-aggregate']
        self.assertIn(UPLOAD_PARTITION.encode(), unit)
        self.assertIn(b'full-core-*-${{ github.run_id }}-${{ github.run_attempt }}', aggregate)
        self.assertEqual(unit.count(b'if-no-files-found: error'), 1)
        self.assertEqual(aggregate.count(b'if-no-files-found: error'), 1)
        self.assertEqual(unit.count(b'fetch-depth: 0'), 1)
        self.assertEqual(aggregate.count(b'fetch-depth: 0'), 1)
        self.assertIn(b'persist-credentials: false', aggregate)
        self.assertNotIn(b'github-token:', unit + aggregate)
        self.assertNotIn(b'retry', unit + aggregate)
        # Equal receipt basenames must remain in eight separate artifact roots.
        template = ('full-core-${{ matrix.python-version }}-${{ matrix.partition }}-'
                    '${{ github.run_id }}-${{ github.run_attempt }}')
        self.assertIn(('          name: ' + template + '\n').encode(), unit)
        artifact_names = {
            template.replace('${{ matrix.python-version }}', version)
            .replace('${{ matrix.partition }}', str(partition))
            .replace('${{ github.run_id }}', '12345')
            .replace('${{ github.run_attempt }}', '1')
            for version in ('3.11', '3.12') for partition in range(4)
        }
        self.assertEqual(len(artifact_names), 8)
        self.assertEqual(len({name + '/receipt.json' for name in artifact_names}), 8)

    def test_unsharded_projected_unknown_and_modified_baselines_fail_closed(self):
        for raw in (self.baseline, self.actual + b' ', self.actual[:-1], b'unknown'):
            with self.subTest(length=len(raw)), self.assertRaises(RuntimeError):
                validate_actual_workflow(raw, self.baseline)
        for baseline in (self.baseline + b' ', self.actual, b'unknown'):
            with self.subTest(length=len(baseline)), self.assertRaises(RuntimeError):
                validate_actual_workflow(self.actual, baseline)

    def test_disabled_partition_changed_policy_and_permissive_result_wiring_fail_closed(self):
        mutations = (
            (b'partition: [0, 1, 2, 3]', b'partition: [0, 1, 2]'),
            (b"python-version: ['3.11', '3.12']", b"python-version: ['3.11']"),
            (b'timeout-minutes: 360', b'timeout-minutes: 720'),
            (b'fail-fast: false', b'fail-fast: true'),
            (b'    strategy:\n', b'    continue-on-error: true\n    strategy:\n'),
            (b'fetch-depth: 0', b'fetch-depth: 1'),
            (b'on: [push, pull_request]', b'on: [push]'),
            (b"github.event_name != 'push'", b"github.event_name == 'pull_request'"),
            (b'--partition ${{ matrix.partition }}', b'--partition 0'),
            (b'--output-dir core-ci-results', b'--output-dir core-ci-results --allow-incomplete'),
            (b'needs: unit-and-schema', b'needs: windows-composite'),
            (b'if: ${{ always() && (', b'if: ${{ success() && ('),
            (b'--matrix-result "${{ needs.unit-and-schema.result }}"', b'--matrix-result success'),
            (b'merge-multiple: false', b'merge-multiple: true'),
            (b'merge-multiple: false', b'merge-multiple: false\n          run-id: 999'),
            (b'merge-multiple: false', b'merge-multiple: false\n          repository: other/repository'),
            (b'merge-multiple: false', b'merge-multiple: false\n          github-token: token'),
            (b'if-no-files-found: error', b'if-no-files-found: ignore'),
            (b'if-no-files-found: error', b'if-no-files-found: error\n          overwrite: true'),
            (b'${{ github.run_attempt }}', b'1'),
            (b'python -m unittest discover -s tests/core_partition -v', b'echo contracts skipped'),
            (b'python scripts/run_full_core_partition_ci.py aggregate', b'echo aggregate skipped'),
            (b'--receipts-dir core-ci-receipts', b'--receipts-dir core-ci-receipts --allow-missing'),
            (b'--output core-ci-aggregate.json', b'--output core-ci-aggregate.json || true'),
        )
        for before, after in mutations:
            self.assertIn(before, self.actual)
            changed = self.actual.replace(before, after, 1)
            with self.subTest(change=before), self.assertRaises(RuntimeError):
                validate_actual_workflow(changed, self.baseline)

    def test_missing_or_reordered_aggregate_and_receipt_diagnostics_are_rejected(self):
        _, blocks = job_blocks(self.actual)
        unit = blocks['unit-and-schema']
        aggregate = blocks['unit-and-schema-aggregate']
        mutations = (
            self.actual.replace(aggregate, b'', 1),
            self.actual.replace(unit + aggregate, aggregate + unit, 1),
            self.actual.replace(UPLOAD_PARTITION.encode(), b'', 1),
            self.actual.replace(b'            core-ci-results/journal.jsonl\n', b'', 1),
            self.actual.replace(b'            core-ci-results/receipt.json\n', b'', 1),
            self.actual.replace(b'        if: ${{ always() }}\n', b'', 1),
        )
        for raw in mutations:
            with self.subTest(digest=sha256(raw).hexdigest()), self.assertRaises(RuntimeError):
                validate_actual_workflow(raw, self.baseline)

    def test_explicit_contracts_do_not_replace_frozen_root_or_replay_execution(self):
        self.assertFalse((Path(__file__).resolve().parent / '__init__.py').exists())
        for relative in (
            '.github/workflows/history-replay-latest.yml',
            '.github/workflows/experimental-platform.yml',
            'tests/history_replay_latest/ci-inventory.json',
        ):
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), git_file(relative))
        self.assertEqual(len(json.loads(
            (ROOT / 'tests/history_replay_latest/ci-inventory.json').read_bytes())['ids']), 70)


if __name__ == '__main__':
    unittest.main()
