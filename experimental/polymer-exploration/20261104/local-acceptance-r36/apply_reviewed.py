"""Apply four exact reviewed DMA Tg records locally; no runtime or Git writes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
AREA = OUT.parent
EXT = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r36'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def write(path, value):
    with path.open('xb') as stream:
        stream.write(encoded(value))


def verify(folder, receipt):
    entry = folder / 'REVIEW_INPUTS_R1.json'
    approval = read(folder / receipt)
    assert approval['decision'] == 'approved' and approval['review_inputs_sha256'] == sha(entry)
    for field in ['repo_files_sha256', 'native_files_sha256', 'external_files_sha256']:
        for name, digest in read(entry).get(field, {}).items():
            path = Path(name) if field == 'external_files_sha256' else ROOT / name
            assert sha(path) == digest, name
    return {'entry_sha256': sha(entry), 'approval_sha256': sha(folder / receipt)}


def main():
    assert not (OUT / 'APPLICATION_INTENT_R36.json').exists()
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == '13c6fa6480bac5bf1ea63442a571a1658b0e4cf3'
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    source = AREA / 'pur-dma-tg-tga-followup-source-r1'
    mapping = AREA / 'pur-dma-tg-native-mapping-r1'
    approvals = {'source': verify(source, 'INDEPENDENT_SOURCE_REVIEW_R1.json'), 'mapping': verify(mapping, 'INDEPENDENT_MAPPING_REVIEW_R1.json')}
    before = {n: read(ROOT / f'materials_boundaries/data/{n}.json') for n in ['materials', 'reference_properties', 'sources']}
    after = deepcopy(before)
    new_states = read(mapping / 'NEW_STATES_R1.json')
    new_properties = read(mapping / 'NEW_PROPERTIES_R1.json')
    assert len(new_states) == len(new_properties) == 4
    after['materials']['records'].extend(new_states)
    after['reference_properties']['records'].extend(new_properties)
    proposal = read(mapping / 'SOURCE_UPDATE_PROPOSAL_R1.json')
    original = next(s for s in before['sources']['records'] if s['id'] == proposal['source_id'])
    assert original == proposal['baseline_source']
    after['sources']['records'] = [proposal['proposed_source'] if s['id'] == proposal['source_id'] else s for s in before['sources']['records']]
    canonical = json.dumps(after, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    snapshot = hashlib.sha256(canonical).hexdigest()
    assert snapshot == read(mapping / 'VALIDATION_R1.json')['preview_snapshot']
    planned = {f'materials_boundaries/data/{n}.json': encoded(v) for n, v in after.items()}
    backup = EXT / 'baseline-tables'
    backup.mkdir(parents=True, exist_ok=False)
    before_hashes = {}
    for name in planned:
        path = ROOT / name
        before_hashes[name] = sha(path)
        shutil.copyfile(path, backup / path.name)
        assert sha(backup / path.name) == before_hashes[name]
    write(OUT / 'APPLICATION_INTENT_R36.json', {'baseline_snapshot': read(mapping / 'VALIDATION_R1.json')['baseline_snapshot'], 'target_snapshot': snapshot, 'approvals': approvals, 'before_sha256': before_hashes, 'after_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in planned.items()}, 'backup_hint': str(backup), 'only_write': list(planned), 'runtime_schema_changes': 0})
    try:
        for name, content in planned.items():
            (ROOT / name).write_bytes(content)
        assert all((ROOT / n).read_bytes() == b for n, b in planned.items())
    except BaseException:
        for name in planned:
            shutil.copyfile(backup / Path(name).name, ROOT / name)
        raise
    write(OUT / 'APPLICATION_R36.json', {'status': 'exact_reviewed_four_DMA_Tg_records_applied_locally', 'snapshot': snapshot, 'after_sha256': {n: sha(ROOT / n) for n in planned}, 'new_properties': 4, 'new_states': 4, 'new_identities_grades_sources': 0, 'all_old5380properties5254states_unchanged': True, 'source_updates': 1, 'runtime_schema_changes': 0, 'DSC2_TGA28_not_admitted': True, 'tests_installation': 'pending_exact_current_checks', 'pushed': False, 'merged_main': False, 'deployed': False})
    print(json.dumps({'new_properties_states': [4, 4], 'snapshot': snapshot, 'written_tables': 3, 'runtime_changes': 0}), flush=True)


if __name__ == '__main__':
    main()
