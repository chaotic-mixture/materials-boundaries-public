"""Freeze an approved exact publication set; final receipt remains external."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    entry = OUT / 'REVIEW_INPUTS_R33_R35_R2.json'
    frozen = json.loads(entry.read_bytes())
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == frozen['baseline_git_commit']
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    assert subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0
    approval = OUT / 'INDEPENDENT_CONTENT_REVIEW_R33_R35.json'
    review = json.loads(approval.read_bytes())
    assert review['decision'] == 'approved' and review['review_inputs_sha256'] == sha(entry)
    pins = dict(frozen['repo_files_sha256'])
    pins[entry.relative_to(ROOT).as_posix()] = sha(entry)
    pins[approval.relative_to(ROOT).as_posix()] = sha(approval)
    tracked = subprocess.check_output(['git', 'diff', '--name-only', '-z'], cwd=ROOT).decode().split('\0')
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    actual = {name for name in tracked + untracked if name}
    assert actual == set(pins), (actual - set(pins), set(pins) - actual)
    files = {}
    for name, digest in pins.items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT) and sha(path) == digest
        files[name] = {'sha256': digest, 'bytes': path.stat().st_size}
    value = {'schema': 'r33-r35-exact-experimental-delivery-manifest/1', 'baseline_commit': frozen['baseline_git_commit'], 'snapshot': frozen['snapshot'], 'files': dict(sorted(files.items())), 'scope': 'All current approved worktree changes plus frozen content entry/approval;no rawsourceassets', 'self_exclusion': 'This manifest is added to exact publication set separately;final manifest review/staging/commit/push/CI receipts remain external to avoid recursive mutation', 'expected_publication_files_including_self': len(files) + 1, 'branch': 'experimental/open-database', 'merge_main_release_deploy': False}
    path = OUT / 'DELIVERY_MANIFEST_R33_R35.json'
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'manifest_sha256': sha(path), 'manifested_files': len(files), 'publication_files': len(files) + 1}), flush=True)


if __name__ == '__main__':
    main()
