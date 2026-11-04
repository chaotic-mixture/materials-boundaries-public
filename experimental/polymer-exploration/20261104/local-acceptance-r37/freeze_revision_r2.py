"""Freeze absence-metadata repair against unchanged actual integration R1."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def main():
    old_entry = HERE / 'REVIEW_ACCEPTANCE_INPUTS_R37.json'
    assert sha(old_entry) == 'd46e5068862eaa1ffbf1e8b00917212bda04967f13b7abeb3fa941d61b6219bd'
    old = read(old_entry)
    for name, digest in old['repo_files_sha256'].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in old['external_files_sha256'].items():
        assert sha(Path(name)) == digest, name
    receipt = HERE / 'INDEPENDENT_ACCEPTANCE_REVIEW_R37_R1.json'
    assert read(receipt)['decision'] == 'changes_required' and len(read(receipt)['findings']) == 1
    revision = read(HERE / 'HISTORICAL_INPUT_RESOLUTION_R37_R2.json')
    original = read(HERE / 'HISTORICAL_INPUT_RESOLUTION_R37.json')
    assert revision['contexts'] == original['contexts'] and len(revision['historical_absence_conditions']) == 2
    files = dict(old['repo_files_sha256'])
    for path in [old_entry, *HERE.iterdir()]:
        if path.is_file():
            files[path.relative_to(ROOT).as_posix()] = sha(path)
    entry = {**old, 'schema': 'r37-real-native-installation-integration-review/2',
        'repo_files_sha256': files, 'revision_of_entry_sha256': sha(old_entry),
        'prior_review_sha256': sha(receipt),
        'revision_scope': 'Restore2historicalabsenceannotations only;139ctx7617bindings/runtime/data/install/testbytes unchanged',
        'current_history_resolution': (HERE / 'HISTORICAL_INPUT_RESOLUTION_R37_R2.json').relative_to(ROOT).as_posix()}
    output = HERE / 'REVIEW_ACCEPTANCE_INPUTS_R37_R2.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(entry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'entry_sha256': sha(output), 'repo_files': len(files), 'external_files': len(entry['external_files_sha256'])}))


if __name__ == '__main__':
    main()
