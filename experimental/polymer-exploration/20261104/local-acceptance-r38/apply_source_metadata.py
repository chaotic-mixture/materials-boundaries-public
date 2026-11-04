"""Apply exact reviewed source URL/note only; preserve every material/property."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent / 'epoxy-supplement-condition-followup-r1'
EXT = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r38'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def write(path, obj):
    with path.open('xb') as stream:
        stream.write(encode(obj))


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == '13c6fa6480bac5bf1ea63442a571a1658b0e4cf3'
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    entry = AUDIT / 'REVIEW_INPUTS_R1.json'
    assert sha(entry) == '7d75895ea7ac53f82ac5818791ca8686ad4078ad124f93467fa93a464e931f1d'
    approval = read(AUDIT / 'INDEPENDENT_SOURCE_REVIEW_R1.json')
    assert approval['decision'] == 'approved' and approval['review_inputs_sha256'] == sha(entry)
    mapping_entry = HERE / 'REVIEW_MAPPING_INPUTS_R38.json'
    mapping_approval = read(HERE / 'INDEPENDENT_METADATA_MAPPING_REVIEW_R38.json')
    assert mapping_approval['decision'] == 'approved' and mapping_approval['review_inputs_sha256'] == sha(mapping_entry)
    for field in ('repo_files_sha256', 'native_files_sha256', 'external_files_sha256'):
        for name, digest in read(mapping_entry)[field].items():
            assert sha(Path(name) if field == 'external_files_sha256' else ROOT / name) == digest, name
    for field in ('repo_files_sha256', 'native_files_sha256', 'external_files_sha256'):
        for name, digest in read(entry)[field].items():
            assert sha(Path(name) if field == 'external_files_sha256' else ROOT / name) == digest, name
    proposal = read(AUDIT / 'SOURCE_UPDATE_PROPOSAL_R1.json')
    assert set(proposal['changed_fields']) == {'urls', 'claim_notes'}
    before_source, after_source = proposal['baseline_source'], proposal['proposed_source']
    assert after_source['urls'][:-1] == before_source['urls'] and len(after_source['urls']) == len(before_source['urls']) + 1
    assert after_source['claim_notes'][:-1] == before_source['claim_notes'] and len(after_source['claim_notes']) == len(before_source['claim_notes']) + 1
    names = ['materials', 'reference_properties', 'sources']
    before_hashes = {f'materials_boundaries/data/{name}.json': sha(ROOT / f'materials_boundaries/data/{name}.json') for name in names}
    data = {name: read(ROOT / f'materials_boundaries/data/{name}.json') for name in names}
    assert next(source for source in data['sources']['records'] if source['id'] == proposal['source_id']) == before_source
    data['sources']['records'] = [after_source if source['id'] == proposal['source_id'] else source for source in data['sources']['records']]
    target = ROOT / 'materials_boundaries/data/sources.json'
    planned = encode(data['sources'])
    snapshot = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
    plan = read(HERE / 'METADATA_WRITE_PLAN_R38.json')
    assert sha(target) == plan['baseline_source_table_sha256'] and hashlib.sha256(planned).hexdigest() == plan['target_source_table_sha256']
    assert snapshot == plan['target_snapshot']
    backup = EXT / 'baseline-source'
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(target, backup / target.name)
    assert sha(backup / target.name) == before_hashes['materials_boundaries/data/sources.json']
    write(HERE / 'APPLICATION_INTENT_R38.json', {'only_write': 'materials_boundaries/data/sources.json',
        'before_sha256': before_hashes, 'target_source_sha256': hashlib.sha256(planned).hexdigest(),
        'target_snapshot': snapshot, 'backup': str(backup / target.name), 'source_review_entry_sha256': sha(entry)})
    try:
        target.write_bytes(planned)
        assert target.read_bytes() == planned
        assert all(sha(ROOT / name) == digest for name, digest in before_hashes.items() if not name.endswith('/sources.json'))
    except BaseException:
        shutil.copyfile(backup / target.name, target)
        raise
    write(HERE / 'APPLICATION_R38.json', {'status': 'exact_reviewed_source_URL_note_applied_locally',
        'snapshot': snapshot, 'after_sha256': {name: sha(ROOT / name) for name in before_hashes},
        'new_properties_states_identities': [0, 0, 0], 'unknowns_filled': 0,
        'changed_source': proposal['source_id'], 'changed_fields': ['urls', 'claim_notes'],
        'all_material_property_bytes_unchanged': True, 'runtime_schema_writes': 0,
        'validation_final_integration_review': 'pending', 'pushed': False, 'merged_main': False, 'deployed': False})
    print(json.dumps({'snapshot': snapshot, 'written_tables': 1, 'new_properties': 0, 'unknowns_filled': 0}), flush=True)


if __name__ == '__main__':
    main()
