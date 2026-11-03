"""Freeze exact reviewed content and final proof paths before Git mutation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = '676df1abd3379f6c6d28bffe8c3685edd63d9b10'


def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    target = OUT / 'DELIVERY_MANIFEST_R19_R22.json'
    assert not target.exists()
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert git('branch', '--show-current').decode().strip() == 'experimental/open-database'
    assert git('diff', '--cached', '--name-only') == b''
    for entry, receipt in [('REVIEW_INPUTS_R19_R22_R2.json', 'INDEPENDENT_CONTENT_REVIEW_R19_R22_R2.json'),
                           ('REVIEW_INSTALL_INPUTS_R19_R22.json', 'INDEPENDENT_INSTALL_REVIEW_R19_R22.json')]:
        inputs, review = read(OUT / entry), read(OUT / receipt)
        assert review['decision'] == 'approved' and review['review_inputs_sha256'] == sha(OUT / entry)
        for name, digest in inputs['repo_files_sha256'].items(): assert sha(ROOT / name) == digest, name
    content = read(OUT / 'REVIEW_INPUTS_R19_R22_R2.json')
    extras = ['REVIEW_INPUTS_R19_R22_R2.json', 'INDEPENDENT_CONTENT_REVIEW_R19_R22_R2.json',
              'INSTALLED_VALIDATION_R19_R22.json', 'NATIVE_INSTALLED_EQUIVALENCE_R19_R22.json',
              'CURRENT_CONSUMER_VALIDATION_R19_R22.json', 'CURRENT_CONSUMER_EXECUTION_BINDING_R19_R22.json',
              'FINAL_LOCAL_STATUS_R19_R22.zh.md', 'freeze_install.py', 'REVIEW_INSTALL_INPUTS_R19_R22.json',
              'INDEPENDENT_INSTALL_REVIEW_R19_R22.json', 'freeze_delivery_manifest.py']
    allowed = set(content['repo_files_sha256']) | {(OUT / n).relative_to(ROOT).as_posix() for n in extras}
    entries = [e for e in git('status', '--porcelain=v1', '-z', '--untracked-files=all').split(b'\0') if e]
    assert not any(e[:2] in (b'R ', b' R', b'C ', b' C') for e in entries)
    paths = [e[3:].decode('utf-8').replace('\\', '/') for e in entries]
    assert len(paths) == len(set(paths)) and set(paths) == allowed
    consumer = read(OUT / 'CURRENT_CONSUMER_VALIDATION_R19_R22.json')
    assert consumer['complete_resolved_states_equal_core'] == 13 and consumer['new_properties_exact_record_and_query_equal'] == 18
    assert sum(consumer['complete_source_query_and_joined_export_counts'].values()) == 46
    assert consumer['detached_mutation_isolated'] and consumer['stale_selection_rejected']
    files = {name: {'sha256': sha(ROOT / name), 'bytes': (ROOT / name).stat().st_size} for name in sorted(paths)}
    assert all(v['bytes'] < 100 * 1024 * 1024 for v in files.values())
    assert not any(Path(name).suffix.lower() in {'.pdf', '.xml', '.png', '.html', '.xlsx', '.whl', '.zip'} for name in files)
    result = {'schema': 'polymer-experimental-delivery-manifest/2', 'baseline_commit': BASE,
              'branch': 'experimental/open-database', 'native_snapshot': consumer['core_snapshot'],
              'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'files': files,
              'file_count_excluding_self': len(files),
              'content_review_sha256': sha(OUT / 'INDEPENDENT_CONTENT_REVIEW_R19_R22_R2.json'),
              'install_review_sha256': sha(OUT / 'INDEPENDENT_INSTALL_REVIEW_R19_R22.json'),
              'consumer_receipt_sha256': sha(OUT / 'CURRENT_CONSUMER_VALIDATION_R19_R22.json'),
              'fresh_scoped_tests': read(OUT / 'SCOPED_TESTS_R19_R22.json'), 'validation_python': sys.version.split()[0],
              'full_history_regression': 'not_run', 'HTTP': 'not_run', 'remote_CI': 'pending_exact_commit',
              'pushed': False, 'merged_main': False, 'stable_release': False, 'deployed': False,
              'note': 'Manifest self hash and precise NUL pathspec are external to avoid recursive hashing; commit/push/CI claims require subsequent exact receipts.'}
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'manifest_sha256': sha(target), 'files_excluding_self': len(files), 'delivery_paths': len(files) + 1}))


if __name__ == '__main__':
    main()
