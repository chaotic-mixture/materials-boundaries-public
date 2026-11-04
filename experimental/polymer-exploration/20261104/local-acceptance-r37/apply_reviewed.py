"""Apply only exact independently approved TGA mapping; no Git/runtime writes."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
AREA = OUT.parent
EXT = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r37'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def write(path, obj):
    with path.open('xb') as stream:
        stream.write(encoded(obj))


def verify(folder, receipt, digest):
    entry = folder / 'REVIEW_INPUTS_R1.json'
    assert sha(entry) == digest
    approval = read(folder / receipt)
    assert approval['decision'] == 'approved' and approval['review_inputs_sha256'] == digest
    for field in ('repo_files_sha256', 'external_files_sha256'):
        for name, expected in read(entry)[field].items():
            path = Path(name) if field == 'external_files_sha256' else ROOT / name
            assert sha(path) == expected, name
    return {'entry_sha256': digest, 'approval_sha256': sha(folder / receipt)}


def main():
    assert not (OUT / 'APPLICATION_INTENT_R37.json').exists()
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == '13c6fa6480bac5bf1ea63442a571a1658b0e4cf3'
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    implementation = AREA / 'pur-tga-contract-implementation-r1'
    mapping = AREA / 'pur-tga-native-mapping-r1'
    approvals = {
        'implementation': verify(implementation, 'INDEPENDENT_IMPLEMENTATION_REVIEW_R1.json', 'c0ab151b950ce95a63fd13cb84a065af7bfe89fc42dbb7280cfcb0ff6158f34d'),
        'mapping': verify(mapping, 'INDEPENDENT_MAPPING_REVIEW_R1.json', 'b91ab30066155ea66cdabe982423ef581ad4b64c3a33ee325e67dddc50aa8031'),
    }
    before = {name: read(ROOT / f'materials_boundaries/data/{name}.json') for name in ('materials', 'reference_properties', 'sources')}
    after = deepcopy(before)
    states, properties = read(mapping / 'NEW_STATES_R1.json'), read(mapping / 'NEW_PROPERTIES_R1.json')
    assert len(states) == 4 and len(properties) == 28
    assert len(before['materials']['records']) == 5258 and len(before['reference_properties']['records']) == 5384
    after['materials']['records'].extend(states)
    after['reference_properties']['records'].extend(properties)
    proposal = read(mapping / 'SOURCE_UPDATE_PROPOSAL_R1.json')
    sid = proposal['baseline_source']['id']
    assert next(source for source in before['sources']['records'] if source['id'] == sid) == proposal['baseline_source']
    after['sources']['records'] = [proposal['proposed_source'] if source['id'] == sid else source for source in after['sources']['records']]
    canonical = json.dumps(after, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    snapshot = hashlib.sha256(canonical).hexdigest()
    assert snapshot == read(mapping / 'VALIDATION_R1.json')['candidate_snapshot']
    planned = {f'materials_boundaries/data/{name}.json': encoded(obj) for name, obj in after.items()}
    backup = EXT / 'baseline-tables'
    backup.mkdir(parents=True, exist_ok=False)
    before_hashes = {}
    for name in planned:
        before_hashes[name] = sha(ROOT / name)
        shutil.copyfile(ROOT / name, backup / Path(name).name)
        assert sha(backup / Path(name).name) == before_hashes[name]
    write(OUT / 'APPLICATION_INTENT_R37.json', {'approvals': approvals,
        'baseline_snapshot': read(mapping / 'VALIDATION_R1.json')['baseline_snapshot'],
        'target_snapshot': snapshot, 'before_sha256': before_hashes,
        'after_sha256': {name: hashlib.sha256(content).hexdigest() for name, content in planned.items()},
        'backup_hint': str(backup), 'only_write': list(planned), 'runtime_schema_writes_this_application': 0})
    try:
        for name, content in planned.items():
            (ROOT / name).write_bytes(content)
        assert all((ROOT / name).read_bytes() == content for name, content in planned.items())
    except BaseException:
        for name in planned:
            shutil.copyfile(backup / Path(name).name, ROOT / name)
        raise
    write(OUT / 'APPLICATION_R37.json', {'status': 'exact_reviewed_28TGA_records_applied_locally',
        'snapshot': snapshot, 'after_sha256': {name: sha(ROOT / name) for name in planned},
        'new_properties': 28, 'new_states': 4, 'new_identities_grades_sources': 0,
        'all_old5384properties5258states_unchanged': True, 'source_updates': 1,
        'runtime_schema_writes_this_application': 0, 'DSC2_not_admitted': True,
        'tests_installation_final_integration_review': 'pending_exact_current_checks',
        'pushed': False, 'merged_main': False, 'deployed': False})
    print(json.dumps({'new_properties_states': [28, 4], 'snapshot': snapshot, 'written_tables': 3}), flush=True)


if __name__ == '__main__':
    main()
