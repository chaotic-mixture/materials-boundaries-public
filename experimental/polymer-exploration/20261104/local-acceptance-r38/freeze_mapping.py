"""Freeze an exact one-table metadata plan separately from source approval."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent / 'epoxy-supplement-condition-followup-r1'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    entry = AUDIT / 'REVIEW_INPUTS_R1.json'
    approval = AUDIT / 'INDEPENDENT_SOURCE_REVIEW_R1.json'
    assert sha(entry) == '7d75895ea7ac53f82ac5818791ca8686ad4078ad124f93467fa93a464e931f1d'
    assert read(approval)['decision'] == 'approved'
    previous = read(entry)
    for field in ('repo_files_sha256', 'native_files_sha256', 'external_files_sha256'):
        for name, digest in previous[field].items():
            assert sha(Path(name) if field == 'external_files_sha256' else ROOT / name) == digest
    proposal = read(AUDIT / 'SOURCE_UPDATE_PROPOSAL_R1.json')
    data = {name: read(ROOT / f'materials_boundaries/data/{name}.json') for name in ('materials', 'reference_properties', 'sources')}
    assert next(source for source in data['sources']['records'] if source['id'] == proposal['source_id']) == proposal['baseline_source']
    candidate = deepcopy(data)
    candidate['sources']['records'] = [proposal['proposed_source'] if source['id'] == proposal['source_id'] else source for source in candidate['sources']['records']]
    target = (json.dumps(candidate['sources'], ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    snapshot = hashlib.sha256(json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
    write('METADATA_WRITE_PLAN_R38.json', {'source_id': proposal['source_id'], 'only_write': 'materials_boundaries/data/sources.json',
        'baseline_source_table_sha256': sha(ROOT / 'materials_boundaries/data/sources.json'),
        'target_source_table_sha256': hashlib.sha256(target).hexdigest(), 'target_snapshot': snapshot,
        'changed_source_fields': ['urls', 'claim_notes'], 'new_URLs_notes': [1, 1],
        'unchanged_material_property_table_sha256': {name: digest for name, digest in previous['native_files_sha256'].items() if not name.endswith('/sources.json')},
        'new_properties_states_identities': [0, 0, 0], 'unknowns_filled': 0,
        'backup_rollback': 'One source-table backup beforewrite;restore on any write/verification exception',
        'actual_integration_validation': 'pending source40joins/exportroundtrip/copyisolation/19databasechecks then finalreadonlyreview;noinstall for thismetadata-only update',
        'native_applied': False, 'pushed': False})
    files = {ROOT / name for name in previous['repo_files_sha256']} | {entry, approval}
    files |= {path for path in HERE.iterdir() if path.is_file()}
    manifest = {'schema': 'source-only-metadata-native-plan-review/1',
        'repo_files_sha256': {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(files)},
        'native_files_sha256': previous['native_files_sha256'], 'external_files_sha256': previous['external_files_sha256'],
        'scope': 'Exact1sourceURL+1note/one-tablewriteplan;no numeric/condition/statistic edits;actualintegrationapproval separate',
        'review_constraints': 'Readonly ownhash/JSON/canonicalbyte reconstruction/schema checks;no authorhelpers/tests/fullgraph/history/write/install/push'}
    write('REVIEW_MAPPING_INPUTS_R38.json', manifest)
    print(json.dumps({'entry_sha256': sha(HERE / 'REVIEW_MAPPING_INPUTS_R38.json'), 'repo_files': len(files), 'target_snapshot': snapshot}))


if __name__ == '__main__':
    main()
