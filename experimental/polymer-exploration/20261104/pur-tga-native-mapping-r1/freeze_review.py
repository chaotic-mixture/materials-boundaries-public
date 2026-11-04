"""Freeze unapplied mapping and complete bounded consumer evidence."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
IMPL = HERE.parent / 'pur-tga-contract-implementation-r1'
EXTERNAL = ROOT.parent / 'open-database-evidence/polymer-pur-tga-native-mapping-20261104-r1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def main():
    entry = IMPL / 'REVIEW_INPUTS_R1.json'
    assert sha(entry) == 'c0ab151b950ce95a63fd13cb84a065af7bfe89fc42dbb7280cfcb0ff6158f34d'
    previous = read(entry)
    assert all(sha(ROOT / name) == digest for name, digest in previous['repo_files_sha256'].items())
    approval = IMPL / 'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json'
    assert read(approval)['decision'] == 'approved' and read(approval)['review_inputs_sha256'] == sha(entry)
    validation = read(HERE / 'VALIDATION_R1.json')
    consumer = read(HERE / 'CANDIDATE_CONSUMER_R1.json')
    assert validation['new_properties_states'] == [28, 4] and validation['native_applied'] is False
    assert validation['candidate_snapshot'] == consumer['candidate_snapshot']
    assert consumer['all28mapping_objects_exact'] and [c['records'] for c in consumer['checks']] == [28, 40]
    files = {ROOT / name for name in previous['repo_files_sha256']}
    files |= {entry, approval}
    files |= {p for p in HERE.iterdir() if p.is_file()}
    external = {Path(name) for name in previous['external_files_sha256']}
    external |= {p for p in EXTERNAL.rglob('*') if p.is_file()}
    assert all(sha(Path(name)) == digest for name, digest in previous['external_files_sha256'].items())
    manifest = {
        'schema': 'PUR-TGA-native-mapping-review/1',
        'repo_files_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)},
        'external_files_sha256': {str(p): sha(p) for p in sorted(external)},
        'scope': '28unapplied native properties/4states/source-note/complete28and40joins;not installation/native admission',
        'implementation_entry_sha256': sha(entry), 'implementation_approval_sha256': sha(approval),
        'baseline_snapshot': validation['baseline_snapshot'], 'candidate_snapshot': validation['candidate_snapshot'],
        'native_applied': False, 'new_identities_grades_sources': 0,
        'review_constraints': 'Readonly own inlinehash/JSON/schema/limited source/visual checks;no author helpers/testmodules/suites/fullgraph/history/writes/install/push',
    }
    output = HERE / 'REVIEW_INPUTS_R1.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'entry_sha256': sha(output), 'repo_files': len(files), 'external_files': len(external)}))


if __name__ == '__main__':
    main()
