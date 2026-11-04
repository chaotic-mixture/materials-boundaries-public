"""Apply exact reviewed electric-field code and five native references locally."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
AREA = OUT.parent
EXT = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r33'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def write_new(path, value):
    with path.open('xb') as stream:
        stream.write(encoded(value))


def check_review(folder, review_name):
    entry = folder / 'REVIEW_INPUTS_R1.json'
    review = read(folder / review_name)
    assert review['decision'] == 'approved' and review['review_inputs_sha256'] == sha(entry)
    frozen = read(entry)
    for field in ('repo_files_sha256', 'native_files_sha256', 'native_before_sha256', 'external_files_sha256'):
        for name, expected in frozen.get(field, {}).items():
            path = Path(name) if field == 'external_files_sha256' else ROOT / name
            if expected is None:
                assert not path.exists(), name
            else:
                assert sha(path) == expected, name
    return {'entry_sha256': sha(entry), 'approval_sha256': sha(folder / review_name)}


def main():
    assert not (OUT / 'APPLICATION_INTENT_R33.json').exists()
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == '53dba9694df201957ea300bd768f785ce959183a'
    contract = AREA / 'ac-breakdown-contract-implementation-r1'
    mapping = AREA / 'sahin-ac-breakdown-native-mapping-r1'
    source = AREA / 'sahin-ac-breakdown-source-contract-r1'
    approvals = {
        'source': check_review(source, 'INDEPENDENT_SOURCE_REVIEW_R1.json'),
        'implementation': check_review(contract, 'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json'),
        'mapping': check_review(mapping, 'INDEPENDENT_MAPPING_REVIEW_R1.json')}
    changes = read(contract / 'PATCH_INPUTS_R1.json')['files']
    planned = {}
    for name, info in changes.items():
        target = ROOT / name
        assert (sha(target) if target.exists() else None) == info['before_sha256']
        payload = contract / 'payload' / name
        assert sha(payload) == info['after_sha256']
        planned[name] = payload.read_bytes()
    before_tables = {n: read(ROOT / f'materials_boundaries/data/{n}.json') for n in ('materials', 'reference_properties', 'sources')}
    after = deepcopy(before_tables)
    states = read(mapping / 'NEW_STATES_R1.json')
    properties = read(mapping / 'NEW_PROPERTIES_R1.json')
    assert len(states) == len(properties) == 5
    after['materials']['records'].extend(states)
    after['reference_properties']['records'].extend(properties)
    proposal = read(mapping / 'SOURCE_UPDATE_PROPOSAL_R1.json')
    rows = after['sources']['records']
    original = next(s for s in rows if s['id'] == proposal['source_id'])
    assert original == proposal['baseline_source']
    rows[rows.index(original)] = proposal['proposed_source']
    canonical = json.dumps(after, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    expected_snapshot = read(mapping / 'VALIDATION_R1.json')['candidate_tables_canonical_sha256']
    assert hashlib.sha256(canonical).hexdigest() == expected_snapshot
    for name, value in after.items():
        planned[f'materials_boundaries/data/{name}.json'] = encoded(value)
    backup = EXT / 'baseline-files'
    backup.mkdir(parents=True, exist_ok=False)
    initial = {}
    for name in planned:
        path = ROOT / name
        initial[name] = sha(path) if path.exists() else None
        if path.exists():
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, saved)
            assert sha(saved) == initial[name]
    write_new(OUT / 'APPLICATION_INTENT_R33.json', {'scope': '13 reviewed code/schema/docs/test files plus3 native tables', 'approvals': approvals, 'before_sha256': initial, 'after_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in planned.items()}, 'backup_hint': str(backup), 'target_snapshot': expected_snapshot, 'new_properties_states': [5, 5], 'push_merge_deploy': False})
    try:
        for name, content in planned.items():
            (ROOT / name).write_bytes(content)
        assert all((ROOT / n).read_bytes() == content for n, content in planned.items())
    except BaseException:
        for name, old_hash in initial.items():
            target = ROOT / name
            if old_hash is None:
                if target.exists():
                    target.unlink()
            else:
                shutil.copyfile(backup / name, target)
        raise
    write_new(OUT / 'APPLICATION_R33.json', {'status': 'exact_reviewed_code_and_five_references_applied_locally', 'applied_at_utc': datetime.now(timezone.utc).isoformat(), 'snapshot': expected_snapshot, 'changed_files': len(planned), 'native_properties': 5376, 'native_states': 5250, 'new_properties': 5, 'new_states': 5, 'new_identities_grades_sources': 0, 'source_metadata_updates': 1, 'all_old_properties_states_preserved': True, 'after_sha256': {n: sha(ROOT / n) for n in planned}, 'validation_scope': 'Exact reviewed preview tables/code,not fresh installed verification', 'installed_validation': 'not_run', 'full_history': 'not_run', 'pushed': False, 'merged_main': False, 'deployed': False})
    print(json.dumps({'applied_files': len(planned), 'snapshot': expected_snapshot, 'new_properties': 5, 'new_states': 5}))


if __name__ == '__main__':
    main()
