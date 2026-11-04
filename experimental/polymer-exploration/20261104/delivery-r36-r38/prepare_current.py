"""Prepare a consolidated delivery against the actual published parent."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-consolidated-delivery-20261104-r36-r38'
BASELINE = '13c6fa6480bac5bf1ea63442a571a1658b0e4cf3'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASELINE
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    assert subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0
    EXT.mkdir(exist_ok=False)
    (EXT / 'baseline-tables').mkdir()
    before, after = {}, {}
    for name in ('materials', 'reference_properties', 'sources'):
        content = subprocess.check_output(['git', 'show', f'{BASELINE}:materials_boundaries/data/{name}.json'], cwd=ROOT)
        (EXT / f'baseline-tables/{name}.json').write_bytes(content)
        before[name] = json.loads(content)
        after[name] = read(ROOT / f'materials_boundaries/data/{name}.json')
    for resource, field in [('materials', 'records'), ('reference_properties', 'records')]:
        old = {item['id']: item for item in before[resource][field]}
        current = {item['id']: item for item in after[resource][field]}
        assert all(current[key] == value for key, value in old.items())
    assert before['materials']['identities'] == after['materials']['identities']
    assert before['materials']['grades'] == after['materials']['grades']
    old_props = {p['id'] for p in before['reference_properties']['records']}
    old_states = {s['id'] for s in before['materials']['records']}
    new_props = [p for p in after['reference_properties']['records'] if p['id'] not in old_props]
    new_states = [s for s in after['materials']['records'] if s['id'] not in old_states]
    assert len(new_props) == 32 and len(new_states) == 8
    src_before = {s['id']: s for s in before['sources']['records']}
    src_after = {s['id']: s for s in after['sources']['records']}
    assert src_before.keys() == src_after.keys()
    changed = {sid: [field for field in src_before[sid] if src_before[sid][field] != src_after[sid][field]]
               for sid in src_before if src_before[sid] != src_after[sid]}
    assert changed == {'ivdre_2024_lpo_rigid_pur': ['claim_notes'], 'tarasov_2022_pna_bpf_epoxy': ['urls', 'claim_notes']} or changed == {'tarasov_2022_pna_bpf_epoxy': ['urls', 'claim_notes'], 'ivdre_2024_lpo_rigid_pur': ['claim_notes']}
    snapshot = hashlib.sha256(json.dumps(after, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    assert snapshot == '40efed0fabc717d506fd6de8c00c4cb316081e7cd79fdf0243f341a887209c95'
    write('NATIVE_DELTA_R36_R38.json', {'baseline_commit': BASELINE, 'baseline_properties_states': [5380, 5254],
        'current_properties_states': [len(after['reference_properties']['records']), len(after['materials']['records'])],
        'snapshot': snapshot, 'new_properties': new_props, 'new_states': new_states,
        'new_properties_by_quantity': dict(Counter(p['quantity'] for p in new_props)),
        'all_old_properties_states_complete_unchanged': True, 'all_identities_grades_unchanged': True,
        'source_field_changes': changed, 'source_IDs_unchanged': True})
    write('APPLICATION_R36_R38.json', {'scope': 'Current consolidated table binding,not new application',
        'snapshot': snapshot, 'after_sha256': {f'materials_boundaries/data/{name}.json': sha(ROOT / f'materials_boundaries/data/{name}.json') for name in after}})
    names = ['README.md', 'HANDOFF.md', 'docs/DATABASE_COVERAGE.zh.md', 'docs/MATERIAL_SOURCE_CONDITIONS.zh.md', 'docs/OPEN_DATABASE_ROADMAP.zh.md']
    backups = {}
    for name in names:
        path = ROOT / name
        backup = EXT / 'before-docs' / name
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, backup)
        backups[name] = {'sha256': sha(backup), 'resolved_path_hint': str(backup)}
        text = path.read_text(encoding='utf-8')
        assert text.count('## 当前本地进展：r33–r35（尚未统一推送）') == 1
        text = text.replace('## 当前本地进展：r33–r35（尚未统一推送）', '## 当前聚合物进展：r36–r38', 1)
        text = text.replace('local-progress-r33-r35/README.zh.md', 'delivery-r36-r38/README.zh.md', 1)
        text = text.replace('旧安装和CI不覆盖本轮；未知项不补默认值。', '当前全库5412条性质、5262个状态；本轮累计新增32条性质、8个状态。安装与CI范围以交付入口的精确回执为准，未知项不补默认值。', 1)
        path.write_text(text, encoding='utf-8', newline='\n')
    write('BEFORE_DOCUMENT_BYTES_R36_R38.json', backups)
    print(json.dumps({'new_properties': len(new_props), 'new_states': len(new_states), 'snapshot': snapshot, 'updated_navigation_files': len(names)}), flush=True)


if __name__ == '__main__':
    main()
