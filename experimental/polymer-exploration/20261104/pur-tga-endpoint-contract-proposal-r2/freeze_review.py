"""Freeze revised concept and preserve exact prior review context."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
R1 = HERE.parent / 'pur-tga-endpoint-contract-proposal-r1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old_entry = R1 / 'REVIEW_INPUTS_R1.json'
    assert sha(old_entry) == '1b293895d664f39e90baa0594a962c854280e4c9d0724356b261dbe91a33736b'
    old = json.loads(old_entry.read_bytes())
    for field in ('repo_files_sha256', 'native_files_sha256'):
        for path, digest in old[field].items():
            assert sha(ROOT / path) == digest, path
    for path, digest in old['external_files_sha256'].items():
        assert sha(Path(path)) == digest, path
    files = dict(old['repo_files_sha256'])
    for path in [old_entry, R1 / 'INDEPENDENT_CONCEPT_REVIEW_R1.json', *HERE.iterdir()]:
        if path.is_file():
            files[path.relative_to(ROOT).as_posix()] = sha(path)
    entry = {
        'schema': 'TGA-endpoint-contract-concept-review/2',
        'repo_files_sha256': files,
        'native_files_sha256': old['native_files_sha256'],
        'external_files_sha256': old['external_files_sha256'],
        'scope': 'Revised concept and28unchanged partialexamples;not implementation/mapping/install/admission approval',
        'native_snapshot': old['native_snapshot'],
        'new_native_records': 0,
        'review_constraints': old['review_constraints'],
    }
    output = HERE / 'REVIEW_INPUTS_R2.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(entry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'entry_sha256': sha(output), 'repo_files': len(files), 'native_files': 3, 'external_files': len(entry['external_files_sha256'])}))


if __name__ == '__main__':
    main()
