"""Bounded, source-bound preflight. Never starts a full SCC partition."""
import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {'.git', '__pycache__', '.venv', '.pytest_cache'}
OWN_FILES = {'scripts/run_layered_validation.py', 'tests/test_layered_validation.py',
             'docs/LAYERED_VALIDATION.zh.md'}
VERSION_IDS = [
    'test_release_metadata.ReleaseMetadataTests.test_version_is_one_build_readable_literal',
    'test_release_metadata.ReleaseMetadataTests.test_build_configuration_and_readme_use_current_version',
]


def fingerprint(files):
    return sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError('Symlink is not a frozen input: ' + str(relative))
        if path.is_file():
            result[relative.as_posix()] = sha256(path.read_bytes()).hexdigest()
    return result


def baseline(path):
    value = json.loads(path.read_bytes())
    files = value['input_files_sha256']
    if not files or fingerprint(files) != value['input_fingerprint']:
        raise ValueError('Baseline fingerprint mismatch')
    for name, digest in files.items():
        p = PurePosixPath(name)
        if (p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name
                or p.as_posix() != name or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('Invalid baseline entry: ' + name)
    return files


def plan(previous, current):
    changed = sorted(p for p in previous.keys() | current.keys()
                     if previous.get(p) != current.get(p))
    # Only prose-only paths and this opt-in tool have a bounded policy.
    # Deleted documents, unknown files and scientific inputs require review.
    bounded = lambda p: (p in current and (p in OWN_FILES or
        p in {'README.md', 'HANDOFF.md', 'THIRD_PARTY_NOTICES.md'} or
        (p.startswith('docs/') and p.endswith('.md'))))
    broad = [p for p in changed if not bounded(p)]
    return {'changed_files': changed, 'requires_full_acceptance': bool(broad),
            'unmapped_or_broad_changes': broad,
            'targeted_modules': ['test_layered_validation'] if
                set(changed) & (OWN_FILES - {'docs/LAYERED_VALIDATION.zh.md'}) else [],
            'full_suite_started': False}


def run_tests(ids):
    suite = unittest.TestLoader().loadTestsFromNames(ids)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.testsRun == 0:
        raise RuntimeError('Targeted checks failed')


def history_checks():
    import material_append_successors as successors
    import material_bulk_preservation as bulk
    import scc_flow_history as scc
    from material_append_history import load_frozen, recover_file, digest
    # Verify every registered data/file ledger pin, without graph replay.
    ledgers = successors.file_ledgers()
    for descriptor in successors.FROZEN_SUCCESSORS:
        for key in ('data', 'files'):
            path, pin = descriptor[key]
            load_frozen(ROOT, path, pin)
    scc.predecessor_descriptors(successors.FROZEN_SUCCESSORS)
    # Exact current SCC code/document images must reverse to their old pins.
    ledgers += [scc.file_ledger(), scc.registry_ledger(),
                load_frozen(ROOT, scc.DIRECTORY + 'document-history.json', scc.DOCUMENTS_SHA256)]
    checked = 0
    for index, ledger in enumerate(ledgers[-3:]):
        for name, entry in ledger['updates'].items():
            raw = (ROOT / name).read_bytes()
            # Document history pins the truthful count-normalized README;
            # file history above pins its original live bytes separately.
            if index == 2 and name == 'README.md':
                raw = bulk.truthful_readme(raw, bulk.load_ledger())
            if digest(raw) != entry['sha256']:
                raise AssertionError('Unadapted current SCC bytes: ' + name)
            if digest(recover_file(raw, entry)) != entry['previous_sha256']:
                raise AssertionError('Historical recovery mismatch: ' + name)
            checked += 1
    # Exercise the actual route that failed in r5, plus README preservation.
    ledger = bulk.load_ledger()
    for name in ('README.md', 'THIRD_PARTY_NOTICES.md', 'tests/test_release_metadata.py'):
        print('history_release_check ' + name, flush=True)
        bulk.release_bytes(name, (ROOT / name).read_bytes(), ledger=ledger)
    # If installed in the separate performance candidate, verify its code bridge.
    if (ROOT / 'tests/scc_performance_history.py').exists():
        import scc_performance_history
        scc_performance_history.require_candidate()
    print(json.dumps({'ledger_pins': 'passed', 'exact_reversals': checked}), flush=True)


def worker(stage):
    sys.path[:0] = [str(ROOT), str(ROOT / 'tests'), str(ROOT / 'scripts')]
    if stage == 'version':
        run_tests(VERSION_IDS)
    elif stage == 'history':
        history_checks()
    elif stage == 'manifest':
        import run_full_core_partition_ci as core
        path = ROOT / core.MANIFEST_PATH
        if sha256(path.read_bytes()).hexdigest() != core.MANIFEST_SHA256:
            raise AssertionError('Core manifest pin mismatch')
        core.validate_manifest(json.loads(path.read_bytes()))
    elif stage == 'targeted':
        run_tests(['test_layered_validation'])


def execute_stage(stage, timeout):
    print(json.dumps({'event': 'stage_started', 'stage': stage}), flush=True)
    started = time.monotonic()
    try:
        result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()),
                                 '--worker', stage], cwd=ROOT, timeout=timeout)
        status = 'passed' if result.returncode == 0 else 'failed'
    except subprocess.TimeoutExpired:
        status = 'timeout'
    record = {'stage': stage, 'status': status, 'seconds': round(time.monotonic()-started, 3)}
    print(json.dumps({'event': 'stage_completed', **record}), flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output', type=Path, help='New report outside the source tree')
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--stage-timeout', type=float, default=120)
    parser.add_argument('--worker', choices=['version', 'history', 'manifest', 'targeted'],
                        help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return 0
    if not args.baseline or not args.output or args.stage_timeout <= 0:
        parser.error('--baseline, --output and positive timeout required')
    output = args.output.resolve()
    if output.is_relative_to(ROOT) or output.exists():
        parser.error('Report must be a new file outside the source tree')
    previous = baseline(args.baseline)
    before = inventory(ROOT)
    report = {'schema': 'layered-validation/1', 'scope': 'bounded_preflight_only',
              'baseline_fingerprint': fingerprint(previous),
              'input_fingerprint': fingerprint(before), 'input_files_sha256': before,
              **plan(previous, before), 'stages': [], 'scc_admitted': False}
    if not args.plan_only:
        stages = ['version', 'history', 'manifest']
        if report['targeted_modules']:
            stages.append('targeted')
        for stage in stages:
            record = execute_stage(stage, args.stage_timeout)
            report['stages'].append(record)
            if record['status'] != 'passed':
                break
    unchanged = inventory(ROOT) == before
    passed = bool(report['stages']) and all(x['status'] == 'passed' for x in report['stages'])
    report['inputs_unchanged'] = unchanged
    report['status'] = ('input_drift' if not unchanged else 'plan_only' if args.plan_only else
                        'preflight_failed' if not passed else
                        'full_acceptance_required' if report['requires_full_acceptance'] else
                        'bounded_checks_passed')
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != 'input_files_sha256'}), flush=True)
    return 0 if report['status'] in {'plan_only', 'bounded_checks_passed'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
