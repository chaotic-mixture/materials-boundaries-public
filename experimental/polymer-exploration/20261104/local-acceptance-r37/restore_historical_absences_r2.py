"""Restore two historical absence conditions without rewriting frozen R1."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    frozen = HERE / 'REVIEW_ACCEPTANCE_INPUTS_R37.json'
    assert sha(frozen) == 'd46e5068862eaa1ffbf1e8b00917212bda04967f13b7abeb3fa941d61b6219bd'
    prior_path = HERE.parent / 'local-acceptance-r36/HISTORICAL_INPUT_RESOLUTION_R36.json'
    prior = read(prior_path)
    original = read(HERE / 'HISTORICAL_INPUT_RESOLUTION_R37.json')
    assert len(prior['historical_absence_conditions']) == 2
    supplement = []
    for condition in prior['historical_absence_conditions']:
        entry = ROOT / condition['entry']
        assert read(entry)[condition['field']][condition['path']] is None
        assert (ROOT / condition['path']).is_file()
        supplement.append({**condition, 'entry_sha256': sha(entry),
            'current_path_exists': True,
            'interpretation': 'Null pin denotes absence at original freeze,not a current absence requirement. Subsequent reviewed implementation created the file;do not delete it or rewrite the historical null pin.'})
    revised = {**original, 'schema': 'r37-historical-context-resolution/2'}
    del revised['absent_baseline_paths']
    revised['historical_absence_conditions'] = supplement
    revised['supersedes_resolution_R1_sha256'] = sha(HERE / 'HISTORICAL_INPUT_RESOLUTION_R37.json')
    revised['revision_scope'] = 'Restore two omitted historical absence annotations only;139contexts7617bindings/currentnative/runtime/install unchanged'
    assert revised['contexts'] == original['contexts'] and revised['bindings'] == 7617 and revised['unresolved'] == 0
    write('HISTORICAL_INPUT_RESOLUTION_R37_R2.json', revised)
    write('HISTORICAL_ABSENCE_RESOLUTION_R37_R2.json', {'source_previous_resolution_sha256': sha(prior_path),
        'frozen_R1_acceptance_entry_sha256': sha(frozen), 'restored_conditions': supplement,
        'cause': 'R1 helper used absent_baseline_paths key instead of r36 historical_absence_conditions',
        'original_files_preserved': True, 'native_runtime_install_test_results_changed': False,
        'no_new_test_run': True})
    print(json.dumps({'restored_conditions': len(supplement), 'contexts': len(revised['contexts']), 'bindings': revised['bindings'], 'native_changed': False}))


if __name__ == '__main__':
    main()
