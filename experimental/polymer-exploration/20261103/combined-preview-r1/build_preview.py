"""Compose frozen polymer proposals into a new external preview, never apply.

Curated manifest paths are normalized to repository-style slashes for portability.
Original manifests and all source values remain unchanged. Conflicting edits or
colliding IDs stop composition; contract checks do not grant source approval.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, compare_snapshots

BASELINE = 'aa8308dbec8817ee6551078ed91bedb2a9fb05c7924fd76a9131cc680617a95f'
AREA = ROOT/'experimental/polymer-exploration/20261103'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def bound_inputs(directory):
    manifest_path = directory/'REVIEW_INPUTS_R1.json'
    manifest = json.loads(manifest_path.read_bytes())
    result = {manifest_path.relative_to(ROOT).as_posix(): sha(manifest_path)}
    for name, expected in manifest['files_sha256'].items():
        path = (directory/name.replace('\\', '/')).resolve()
        assert path.is_relative_to(directory.resolve())
        assert sha(path) == expected, name
        result[path.relative_to(ROOT).as_posix()] = expected
    return result


def replace_records(data, table, rows):
    proposed = {row['id']: row for row in rows}
    assert len(proposed) == len(rows)
    assert set(proposed) <= {row['id'] for row in data[table]['records']}
    data[table]['records'] = [deepcopy(proposed.get(row['id'], row)) for row in data[table]['records']]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    assert not output.is_relative_to((ROOT/'materials_boundaries').resolve())
    assert not output.exists(), 'Create a new output directory; never overwrite another preview'
    correction_dir = AREA/'filament-drawing-method-audit'
    addition_dir = AREA/'pa12-ageing-sls-native-draft'
    inputs = {**bound_inputs(correction_dir), **bound_inputs(addition_dir)}
    correction_path = correction_dir/'native-correction-candidate-r1.json'
    addition_path = addition_dir/'frozen-r1/native-candidate-r1.json'
    correction = json.loads(correction_path.read_bytes())
    addition = json.loads(addition_path.read_bytes())
    before = Database()
    assert before.snapshot == correction['baseline_snapshot'] == addition['baseline_snapshot'] == BASELINE
    for table in ('materials', 'reference_properties', 'sources'):
        corrected = [row['id'] for row in correction[table]['records']]
        added = [row['id'] for row in addition[table]['records']]
        assert len(corrected) == len(set(corrected)) and len(added) == len(set(added))
        assert not set(corrected) & set(added), 'Overlapping proposals require an explicit new decision'
    data = deepcopy(before.data)
    for table in ('materials', 'reference_properties', 'sources'):
        replace_records(data, table, correction[table]['records'])
    for table in ('materials', 'reference_properties'):
        existing = {row['id'] for row in data[table]['records']}
        rows = addition[table]['records']
        assert not existing & {row['id'] for row in rows}
        data[table]['records'].extend(deepcopy(rows))
    replace_records(data, 'sources', addition['sources']['records'])
    assert data['materials']['identities'] == before.data['materials']['identities']
    assert data['materials']['grades'] == before.data['materials']['grades']
    after = Database(data)
    validation = after.validate_scientific_contracts()
    expected_properties = {row['id'] for row in correction['reference_properties']['records']}
    assert len(expected_properties) == 22
    for pid in expected_properties:
        old, new = before.properties[pid], after.properties[pid]
        for key in ('reported_value', 'sample_count', 'uncertainty', 'uncertainty_note',
                    'uncertainty_status', 'summary_statistic', 'quantity'):
            assert old[key] == new[key], (pid, key)
        assert new['conditions']['loading_rate']['status'] == 'not_verified'
        assert new['conditions']['loading_rate']['text'] is None
    assert len(after.states) == len(before.states)+5
    assert len(after.properties) == len(before.properties)+8
    output.mkdir(parents=True, exist_ok=False)
    preview = output/'native-tables'
    preview.mkdir()
    files = {}
    for table in data:
        native = ROOT/'materials_boundaries/data'/(table+'.json')
        raw = native.read_bytes()
        serialized = (json.dumps(before.data[table], ensure_ascii=False, indent=2)+'\n').encode()
        new = (json.dumps(data[table], ensure_ascii=False, indent=2)+'\n').encode()
        if raw == serialized:
            newline = 'LF'
        elif raw == serialized.replace(b'\n', b'\r\n'):
            newline = 'CRLF'
            new = new.replace(b'\n', b'\r\n')
        else:
            raise ValueError('Unrecognized native formatting: '+table)
        path = preview/native.name
        path.write_bytes(new)
        files[path.relative_to(output).as_posix()] = {'sha256': sha(path), 'newline_style': newline}
    diffs = {}
    for label, source in [('filament', 'aniskevich_bulderberga_2023_polymer_mechanical_characterisation'),
                          ('ageing', 'zakrecki_cieslik_2025_pa12_ageing')]:
        before.export(output/(label+'-before'), source=source)
        after.export(output/(label+'-after'), source=source)
        diffs[label] = compare_snapshots(output/(label+'-before'), output/(label+'-after'))
    assert len(diffs['filament']['modified']) == 22 and not diffs['filament']['added'] and not diffs['filament']['deleted']
    assert len(diffs['ageing']['added']) == 8 and len(diffs['ageing']['modified']) == 1 and not diffs['ageing']['deleted']
    report = {'schema':'polymer-combined-isolated-preview/1',
              'stage':'producer_validation_only_no_independent_approval_or_application',
              'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'baseline_snapshot':before.snapshot,'preview_snapshot':after.snapshot,
              'portable_repo_input_hashes':inputs,'script_sha256':sha(Path(__file__)),
              'current_graph_validation':validation,'identity_and_grade_objects_unchanged':True,
              'modified_states':11,'new_states':5,'modified_properties':22,'new_properties':8,
              'source_metadata_updates':2,'corrected_numeric_and_uncertainty_objects_unchanged':22,
              'unresolved_loading_rate_preserved':22,
              'projected_counts':{'identities':len(after.identities),'states':len(after.states),'properties':len(after.properties)},
              'projected_polymer_summary':after.summary(category='polymer'),
              'source_differences':diffs,'preview_files':files,
              'live_tables_applied':False,'independent_review':'not_started',
              'source_authenticity':'not_certified','full_history_replay':'not_run',
              'CI_scope':'Existing5baaf6c CI covers actual accepted graph,not this combined preview.',
              'permission_boundary':'No reviewer spawned; existing batch-specific authorization boundaries remain.',
              'push':'not_performed','main_merge':False,'release':False,'deployment':False}
    write(output/'COMBINED_VALIDATION_R1.json',report)
    assert Database().snapshot == before.snapshot
    print(json.dumps({'preview_snapshot':after.snapshot,'counts':report['projected_counts'],
                      'modified_properties':22,'added_properties':8,'applied':False}))


if __name__ == '__main__':
    main()
