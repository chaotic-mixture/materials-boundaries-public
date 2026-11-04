"""Freeze only the independently approved exact experimental delivery set."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    entry = HERE / 'REVIEW_CONTENT_INPUTS_R36_R38.json'
    frozen = json.loads(entry.read_bytes())
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == frozen['baseline_commit']
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    assert subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0
    receipt = HERE / 'INDEPENDENT_CONTENT_REVIEW_R36_R38.json'
    approval = json.loads(receipt.read_bytes())
    assert approval['decision'] == 'approved' and approval['review_inputs_sha256'] == sha(entry)
    pins = dict(frozen['repo_files_sha256'])
    pins[entry.relative_to(ROOT).as_posix()] = sha(entry)
    pins[receipt.relative_to(ROOT).as_posix()] = sha(receipt)
    actual = set()
    for args in [['diff', '--name-only', '-z'], ['ls-files', '--others', '--exclude-standard', '-z']]:
        actual |= {name for name in subprocess.check_output(['git', *args], cwd=ROOT).decode().split('\0') if name}
    assert actual == set(pins), (actual - pins.keys(), pins.keys() - actual)
    for name, digest in pins.items():
        assert (ROOT / name).resolve().is_relative_to(ROOT) and sha(ROOT / name) == digest, name
    output = {'schema': 'r36-r38-exact-experimental-delivery-manifest/1',
        'baseline_commit': frozen['baseline_commit'], 'snapshot': frozen['snapshot'],
        'files': {name: {'sha256': digest, 'bytes': (ROOT / name).stat().st_size} for name, digest in sorted(pins.items())},
        'expected_publication_files_including_self': len(pins) + 1,
        'self_exclusion': 'Manifestself added separately;finalmanifestreview/staging/commit/push/CIreceipts external',
        'branch': 'experimental/open-database', 'merge_main_release_tag_deploy': False}
    path = HERE / 'DELIVERY_MANIFEST_R36_R38.json'
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'manifest_sha256': sha(path), 'files': len(pins), 'publication_files': len(pins) + 1}))


if __name__ == '__main__':
    main()
