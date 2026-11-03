"""Add the frozen Sahin proposal to the hash-bound combined r2 preview."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database

AREA = ROOT / 'experimental/polymer-exploration/20261103'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior-preview-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    assert not output.exists() and not output.is_relative_to(ROOT)
    prior_manifest_path = AREA / 'combined-preview-r2/REVIEW_INPUTS_R2.json'
    prior_manifest = read(prior_manifest_path)
    inputs = {prior_manifest_path.relative_to(ROOT).as_posix():sha(prior_manifest_path)}
    for name, expected in prior_manifest['repo_files_sha256'].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT) and sha(path) == expected, name
        inputs[name] = expected
    data = {}
    for name, expected in prior_manifest['external_preview_files_sha256'].items():
        assert name in {'materials.json','sources.json','reference_properties.json'}
        path = args.prior_preview_dir / name
        assert sha(path) == expected, name
        data[path.stem] = read(path)
    prior = Database(data)
    before = Database()
    assert prior.snapshot == prior_manifest['combined_preview_snapshot']
    assert before.snapshot == prior_manifest['baseline_snapshot']
    packet_dir = AREA / 'sahin-existing-strength-draft-r1'
    packet_manifest_path = packet_dir / 'REVIEW_INPUTS_R1.json'
    packet_manifest = read(packet_manifest_path)
    inputs[packet_manifest_path.relative_to(ROOT).as_posix()] = sha(packet_manifest_path)
    for name, expected in packet_manifest['files_sha256'].items():
        path = (packet_dir / name).resolve()
        assert path.is_relative_to(packet_dir) and sha(path) == expected, name
        inputs[path.relative_to(ROOT).as_posix()] = expected
    proposal = read(packet_dir / 'frozen-r1/native-candidate-r1.json')
    assert proposal['baseline_snapshot'] == before.snapshot
    assert proposal['sources']['records'] == []
    states = {s['id']:s for s in data['materials']['records']}
    for state in proposal['materials']['records']:
        assert states[state['id']] == before.states[state['id']], 'Overlapping state proposal'
        assert {k:v for k,v in state.items() if k not in ('version','property_ids')} == {k:v for k,v in before.states[state['id']].items() if k not in ('version','property_ids')}
        states[state['id']] = deepcopy(state)
    data['materials']['records'] = [states[s['id']] for s in data['materials']['records']]
    added = proposal['reference_properties']['records']
    assert len(added) == 5 and len({p['id'] for p in added}) == 5
    assert not set(prior.properties) & {p['id'] for p in added}
    data['reference_properties']['records'].extend(deepcopy(added))
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert after.identities == before.identities and after.grades == before.grades
    modified_properties = [pid for pid in before.properties if before.properties[pid] != after.properties[pid]]
    modified_states = [sid for sid in before.states if before.states[sid] != after.states[sid]]
    modified_sources = [sid for sid in before.sources if before.sources[sid] != after.sources[sid]]
    assert len(modified_properties) == 22 and len(modified_states) == 25 and len(modified_sources) == 4
    assert len(after.properties)-len(before.properties) == 22
    assert len(after.states)-len(before.states) == 5
    assert set(before.properties) <= set(after.properties) and set(before.states) <= set(after.states)
    for pid in modified_properties:
        for key in ('reported_value','uncertainty','sample_count','quantity','summary_statistic'):
            assert before.properties[pid][key] == after.properties[pid][key], (pid,key)
    assert Database().snapshot == before.snapshot
    output.mkdir(parents=True)
    tables = output / 'native-tables'
    tables.mkdir()
    for name, content in data.items(): write(tables / (name+'.json'), content)
    report = {'schema':'polymer-combined-preview/3','stage':'pending_independent_review_not_applied',
        'baseline_snapshot':before.snapshot,'prior_snapshot':prior.snapshot,'preview_snapshot':after.snapshot,
        'repo_input_sha256':inputs,'preview_file_sha256':{p.name:sha(p) for p in tables.iterdir()},
        'counts':{'identities':len(after.identities),'states':len(after.states),'properties':len(after.properties)},
        'changes':{'new_identities':0,'new_states':5,'new_properties':22,'modified_states':25,
                   'modified_properties':22,'modified_sources':4},'contracts':contracts,
        'native_applied':False,'full_history_regression':'not_run','independent_review':'pending','published':False}
    write(output / 'COMBINED_VALIDATION_R3.json', report)
    print(json.dumps({'snapshot':after.snapshot,'counts':report['counts'],'changes':report['changes'],'contracts':contracts}))


if __name__ == '__main__':
    main()
