"""Freeze reviewed local batches and exact current delivery evidence, no Git writes."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
AREA = OUT.parent


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    cache = {}
    def sha(path):
        path = path.resolve()
        if path not in cache:
            cache[path] = hashlib.sha256(path.read_bytes()).hexdigest()
        return cache[path]
    assert not (OUT / 'REVIEW_INPUTS_R33_R35.json').exists()
    baseline = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert baseline == '53dba9694df201957ea300bd768f785ce959183a'
    tests = read(OUT / 'SCOPED_TESTS_R33_R35.json')
    assert tests['successful'] and tests['tests_run'] == 203
    assert tests['failures'] == tests['errors'] == tests['skipped'] == 0
    execution = read(OUT / 'SCOPED_TEST_INPUTS_R33_R35.json')['repo_files_sha256']
    assert all(sha(ROOT / n) == h for n, h in execution.items())
    approvals = {}
    for n in [33, 34, 35]:
        folder = AREA / f'local-acceptance-r{n}'
        name = f'REVIEW_INPUTS_R{n}.json' if n == 34 else f'REVIEW_ACCEPTANCE_INPUTS_R{n}.json'
        review = read(folder / f'INDEPENDENT_ACCEPTANCE_REVIEW_R{n}.json')
        assert review['decision'] == 'approved' and review['review_inputs_sha256'] == sha(folder / name)
        approvals[str(n)] = {'entry_sha256': sha(folder / name), 'approval_sha256': sha(folder / f'INDEPENDENT_ACCEPTANCE_REVIEW_R{n}.json')}
    previous = read(AREA / 'local-acceptance-r35/HISTORICAL_INPUT_RESOLUTION_R35_DOCS.json')
    result = []
    for context in previous['contexts']:
        assert sha(ROOT / context['entry']) == context['entry_sha256']
        for name, bound in context['resolved'].items():
            assert sha(Path(bound['resolved_path_hint'])) == bound['sha256'], name
        result.append(context)
    for rel, field in [('local-acceptance-r35/REVIEW_ACCEPTANCE_INPUTS_R35.json', 'repo_files_sha256')]:
        entry = AREA / rel
        pins = read(entry)[field]
        binding = {}
        for name, digest in pins.items():
            assert sha(ROOT / name) == digest
            binding[name] = {'sha256': digest, 'resolved_path_hint': str(ROOT / name), 'current': True}
        result.append({'entry': entry.relative_to(ROOT).as_posix(), 'entry_sha256': sha(entry), 'field': field, 'resolved': binding})
    binding = {n: {'sha256': h, 'resolved_path_hint': str(ROOT / n), 'current': True} for n, h in execution.items()}
    entry = OUT / 'SCOPED_TEST_INPUTS_R33_R35.json'
    result.append({'entry': entry.relative_to(ROOT).as_posix(), 'entry_sha256': sha(entry), 'field': 'repo_files_sha256', 'resolved': binding})
    write(OUT / 'HISTORICAL_INPUT_RESOLUTION_R33_R35.json', {'schema': 'r33-r35-consolidated-historical-resolution/1', 'contexts': result, 'resolved_entries': sum(len(c['resolved']) for c in result), 'unresolved_entries': 0, 'historical_absence_conditions': previous['historical_absence_conditions'], 'policy': 'Exact existing archives/current bytes,not historical test replay or modified old manifests'})
    tracked = subprocess.check_output(['git', 'diff', '--name-only', '-z'], cwd=ROOT).decode().split('\0')
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    paths = sorted({name for name in tracked + untracked if name})
    assert all(Path(n).suffix in ('.md', '.json', '.py', '.patch', '.log') for n in paths)
    external = {}
    owners = {}
    for name in paths:
        if Path(name).suffix != '.json':
            continue
        data = read(ROOT / name)
        if not isinstance(data, dict):
            continue
        for path, digest in data.get('external_files_sha256', {}).items():
            assert isinstance(digest, str)
            assert sha(Path(path)) == digest, (name, path)
            assert external.get(path, digest) == digest
            external[path] = digest
            owners.setdefault(path, []).append(name)
    write(OUT / 'EXTERNAL_EVIDENCE_BINDING_R33_R35.json', {'scope': 'Exact external execution/source/artifact bytes already pinned by included review receipts;assets remain outside repository', 'files_sha256': external, 'owner_receipts': owners, 'files': len(external), 'all_hashes_match': True, 'asset_redistribution': False})
    installed = read(AREA / 'local-acceptance-r35/INSTALLED_VALIDATION_R35.json')
    consumer = read(OUT / 'ACTUAL_CONSUMER_R33_R35.json')
    assert consumer['exit_code'] == 0 and consumer['result']['total_complete_source_records'] == 50
    assert consumer['result']['all3native_installed_tables_byte_equal']
    write(OUT / 'CURRENT_INSTALL_REUSE_R33_R35.json', {'scope': 'Reuse exact independently approved r35 wheel/install;no rebuild/reinstall', 'review_inputs_sha256': sha(AREA / 'local-acceptance-r35/REVIEW_ACCEPTANCE_INPUTS_R35.json'), 'approval_sha256': sha(AREA / 'local-acceptance-r35/INDEPENDENT_ACCEPTANCE_REVIEW_R35.json'), 'wheel_sha256': installed['wheel_sha256'], 'version': installed['installed_probe']['version'], 'snapshot': installed['installed_probe']['snapshot'], 'package_manifest_sha256': sha(AREA / 'local-acceptance-r35/PACKAGE_INPUTS_R35.json'), 'all_package_inputs_current': True, 'new_records': 9, 'complete_source_records': 50, 'consumer_sha256': sha(OUT / 'ACTUAL_CONSUMER_R33_R35.json'), 'process_provenance_scope': 'Content/metadata/RECORD match,not cryptographic installation-process authentication'})
    paths += [(OUT / n).relative_to(ROOT).as_posix() for n in ['EXTERNAL_EVIDENCE_BINDING_R33_R35.json', 'CURRENT_INSTALL_REUSE_R33_R35.json']]
    repo = {n: sha(ROOT / n) for n in sorted(set(paths))}
    write(OUT / 'REVIEW_INPUTS_R33_R35.json', {'schema': 'r33-r35-current-consolidated-content-review/1', 'baseline_git_commit': baseline, 'snapshot': '6a8bd7f0c6591088dbd14ab1c91662dca789f4821577be3a855e17d97af2c1b2', 'repo_files_sha256': repo, 'external_files_sha256': external, 'local_acceptance_approvals': approvals, 'new_properties_states': [9, 9], 'source_append_updates': 3, 'test_scope': {'fresh_current': 203, 'daily_subset': 19, 'failures': 0, 'errors': 0, 'skipped': 0, 'stable_inputs': len(execution)}, 'installation': 'Exact reviewed r35 actual installation reused;new50source9additionconsumerevidence', 'publication': 'not_committed_or_pushed', 'review_constraints': 'Read-only own hash/JSON/schema/Gitdiff/installed small probes;no authorhelpers/suites/fullgraph/history/reinstall/writes/push'})
    print(json.dumps({'entry_sha256': sha(OUT / 'REVIEW_INPUTS_R33_R35.json'), 'repo_inputs': len(repo), 'external_inputs': len(external), 'historical_contexts': len(result), 'historical_bindings': sum(len(c['resolved']) for c in result), 'current_tests': 203}), flush=True)


if __name__ == '__main__':
    main()
