"""Freeze the concrete consolidated content before building the final wheel."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
AREA = 'experimental/polymer-exploration/20261103/'
BASE = '676df1abd3379f6c6d28bffe8c3685edd63d9b10'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    assert subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
    for stage in ('r19', 'r20', 'r21', 'r22'):
        folder = OUT.parent / ('local-acceptance-' + stage)
        entry = folder / ('REVIEW_INPUTS_' + stage.upper() + '.json')
        receipt = read(folder / ('INDEPENDENT_ACCEPTANCE_REVIEW_' + stage.upper() + '.json'))
        assert receipt['decision'] in {'approved', 'clear'} and receipt['review_inputs_sha256'] == sha(entry)
    tests = read(OUT / 'SCOPED_TESTS_R19_R22.json')
    assert tests['successful'] and tests['tests_run'] == 146 and not any(tests[k] for k in ('failures', 'errors', 'skipped'))
    assert tests['inputs_unchanged_during_run'] == 108
    assert read(OUT / 'HISTORICAL_INPUT_RESOLUTION_R19_R22.json')['unresolved_entries'] == 0
    directories = [AREA + name + '/' for name in (
        'pbs-pbat-break-elongation-draft-r1', 'pbs-pbat-break-elongation-native-r1',
        'elongation-table-exclusions-r19', 'nr-unit-status-audit-r2',
        'nr-shore-a-source-contract-proposal-r1', 'nr-shore-a-native-r1',
        'sylgard-hardness-source-draft-r1', 'sylgard-hardness-native-r1',
        'sylgard-compression-source-contract-r1', 'sylgard-compression-native-r1', 'delivery-r19-r22')]
    directories += [AREA + prefix + stage + '/' for stage in ('r19', 'r20', 'r21', 'r22')
                    for prefix in ('installed-preview-', 'local-acceptance-', 'condition-gaps-r3/native-')]
    named = {AREA + 'LOCAL_PROGRESS_' + stage.upper() + '.zh.md' for stage in ('r19', 'r20', 'r21', 'r22')}
    named |= {'README.md', 'HANDOFF.md', 'docs/DATABASE_COVERAGE.zh.md', 'docs/MATERIAL_SOURCE_CONDITIONS.zh.md',
              'docs/OPEN_DATABASE_ROADMAP.zh.md', 'docs/MATERIAL_REFERENCE_CATALOG.md',
              'materials_boundaries/material_references.py', 'materials_boundaries/material_presentation.py',
              'materials_boundaries/data/material_locales.json', 'materials_boundaries/data/materials.json',
              'materials_boundaries/data/reference_properties.json', 'materials_boundaries/data/sources.json',
              'schemas/reference_properties.schema.json', 'tests/test_shore_a_hardness_contract.py',
              'tests/test_compression_reference_contract.py'}
    raw = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=ROOT)
    entries = [entry for entry in raw.split(b'\0') if entry]
    assert not any(entry[:2] in (b'R ', b' R', b'C ', b' C') for entry in entries)
    paths = [entry[3:].decode('utf-8').replace('\\', '/') for entry in entries]
    assert len(paths) == len(set(paths))
    for name in paths:
        assert name in named or any(name.startswith(prefix) for prefix in directories), name
        assert (ROOT / name).is_file() and (ROOT / name).resolve().is_relative_to(ROOT)
        assert (ROOT / name).stat().st_size < 100 * 1024 * 1024
        assert (ROOT / name).suffix.lower() not in {'.pdf', '.xml', '.png', '.html', '.xlsx', '.whl', '.zip'}
    result = {'schema': 'polymer-r19-r22-consolidated-content-review/1', 'baseline_commit': BASE,
              'branch': 'experimental/open-database', 'native_snapshot': read(OUT / 'NATIVE_DELTA_R19_R22.json')['current_snapshot'],
              'repo_files_sha256': {name: sha(ROOT / name) for name in sorted(paths)},
              'scope': 'Consolidated four-round delta, contract/schema/locales/tests, main documents, frozen history, retained external evidence and prospective final package/consumer helpers. Not final install or commit approval.',
              'fresh_tests': tests, 'final_install': 'not_run_pending_content_approval',
              'full_history_regression': 'not_run', 'HTTP': 'not_run', 'remote_CI': 'pending_exact_commit',
              'pushed': False, 'merged_main': False, 'stable_release': False, 'deployed': False}
    target = OUT / 'REVIEW_INPUTS_R19_R22.json'
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'review_inputs_sha256': sha(target), 'content_files': len(paths)}))


if __name__ == '__main__':
    main()
