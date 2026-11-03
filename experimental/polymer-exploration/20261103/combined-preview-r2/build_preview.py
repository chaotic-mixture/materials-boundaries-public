"""Compose existing polymer proposals into isolated tables without acceptance."""
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
BASELINE = 'aa8308dbec8817ee6551078ed91bedb2a9fb05c7924fd76a9131cc680617a95f'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8') as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write('\n')


def bind(directory, filename, key):
    manifest_path = directory / filename
    manifest = read(manifest_path)
    hashes = {manifest_path.relative_to(ROOT).as_posix(): sha(manifest_path)}
    for name, expected in manifest[key].items():
        path = (directory / name.replace('\\', '/')).resolve()
        assert path.is_relative_to(directory.resolve())
        assert sha(path) == expected, name
        hashes[path.relative_to(ROOT).as_posix()] = expected
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior-preview-dir', type=Path, required=True,
                        help='Directory holding the three hash-bound r1 native tables')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    assert not output.exists()
    assert not output.is_relative_to((ROOT / 'materials_boundaries').resolve())
    before = Database()
    assert before.snapshot == BASELINE
    old_manifest_path = AREA / 'combined-preview-r1/REVIEW_INPUTS_R1.json'
    old = read(old_manifest_path)
    inputs = {old_manifest_path.relative_to(ROOT).as_posix(): sha(old_manifest_path)}
    for name, expected in old['repo_files_sha256'].items():
        path = ROOT / name
        assert sha(path) == expected, name
        inputs[name] = expected
    external_hashes = {Path(name).name: h for name, h in old['external_preview_hints'].items()}
    assert set(external_hashes) == {'materials.json','sources.json','reference_properties.json'}
    data = {}
    for name, expected in external_hashes.items():
        path = args.prior_preview_dir / name
        assert sha(path) == expected, name
        data[path.stem] = read(path)
    prior = Database(data)
    assert prior.snapshot == old['combined_preview_snapshot']
    pbs_dir = AREA / 'pbs-existing-tensile-draft-r1'
    pur_dir = AREA / 'pur-existing-density-audit-r1'
    inputs.update(bind(pbs_dir, 'REVIEW_INPUTS_R1.json', 'files_sha256'))
    inputs.update(bind(pur_dir, 'AUDIT_INPUTS_R1.json', 'files_sha256'))
    pbs = read(pbs_dir / 'frozen-r1/native-candidate-r1.json')
    pur = read(pur_dir / 'source-correction-candidate-r1.json')
    assert pbs['baseline_snapshot'] == BASELINE
    assert sha(ROOT / 'materials_boundaries/data/sources.json') == pur['baseline_sources_sha256']
    # Replacements must still match the native baseline at the target key.
    # This stops an unrelated earlier proposal being overwritten silently.
    for name, changes in [('materials', pbs['materials']['records']), ('sources', pbs['sources']['records'])]:
        native = {r['id']: r for r in before.data[name]['records']}
        current = {r['id']: r for r in data[name]['records']}
        for proposed in changes:
            assert current[proposed['id']] == native[proposed['id']], 'Overlapping proposal: ' + proposed['id']
            current[proposed['id']] = deepcopy(proposed)
        data[name]['records'] = [current[r['id']] for r in data[name]['records']]
    new_properties = pbs['reference_properties']['records']
    assert not set(prior.properties) & {p['id'] for p in new_properties}
    data['reference_properties']['records'].extend(deepcopy(new_properties))
    source = next(s for s in data['sources']['records'] if s['id'] == pur['source_id'])
    assert source == before.sources[pur['source_id']], 'PUR source overlaps prior amendments'
    assert source['claim_notes'].count(pur['old_text']) == 1
    source['claim_notes'][source['claim_notes'].index(pur['old_text'])] = pur['new_text']
    after = Database(data)
    contracts = after.validate_scientific_contracts()
    assert after.identities == before.identities and after.grades == before.grades
    added_states = set(after.states) - set(before.states)
    added_props = set(after.properties) - set(before.properties)
    modified_states = [sid for sid in before.states if after.states[sid] != before.states[sid]]
    modified_props = [pid for pid in before.properties if after.properties[pid] != before.properties[pid]]
    modified_sources = [sid for sid in before.sources if after.sources[sid] != before.sources[sid]]
    assert (len(added_states), len(added_props), len(modified_states), len(modified_props), len(modified_sources)) == (5,17,20,22,4)
    assert set(before.properties) <= set(after.properties)
    for pid in modified_props:
        for key in ('reported_value','uncertainty','sample_count','quantity','summary_statistic'):
            assert after.properties[pid][key] == before.properties[pid][key], (pid,key)
        assert after.properties[pid]['conditions']['loading_rate']['status'] == 'not_verified'
    assert Database().snapshot == BASELINE
    output.mkdir(parents=True)
    native = output / 'native-tables'
    native.mkdir()
    for table, value in data.items():
        write(native / (table + '.json'), value)
    report = {'schema':'polymer-combined-preview/2','stage':'producer_preview_pending_independent_review',
              'baseline_snapshot':BASELINE,'prior_snapshot':prior.snapshot,'preview_snapshot':after.snapshot,
              'input_files_sha256':inputs,'preview_files_sha256':{p.name:sha(p) for p in native.iterdir()},
              'counts':{'identities':len(after.identities),'states':len(after.states),'properties':len(after.properties)},
              'changes':{'new_states':len(added_states),'new_properties':len(added_props),
                         'modified_states':len(modified_states),'modified_properties':len(modified_props),
                         'modified_sources':len(modified_sources),'new_identities':0},
              'existing_property_numeric_objects_unchanged':True,'contracts':contracts,
              'native_applied':False,'full_history_regression':'not_run','independent_review':'pending',
              'published':False,'source_scientific_validation':False}
    write(output / 'COMBINED_VALIDATION_R2.json', report)
    print(json.dumps({'snapshot':after.snapshot,'counts':report['counts'],'changes':report['changes'],'contracts':contracts}))


if __name__ == '__main__':
    main()
