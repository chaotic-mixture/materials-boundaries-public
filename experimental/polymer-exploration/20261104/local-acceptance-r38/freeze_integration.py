"""Freeze actual source-only integration and before-source byte resolution."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r38'
AUDIT = HERE.parent / 'epoxy-supplement-condition-followup-r1'
CACHE = {}


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    path = path.resolve()
    if path not in CACHE:
        CACHE[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return CACHE[path]


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    result = read(HERE / 'TEST_RESULTS_R38.json')
    assert result['successful'] and result['tests_run'] == 19 and result['inputs_unchanged'] and not result['skipped']
    inputs = read(HERE / 'EXECUTION_INPUTS_R38.json')
    assert all(sha(ROOT / name) == digest for name, digest in inputs.items())
    application = read(HERE / 'APPLICATION_R38.json')
    consumer = read(HERE / 'CURRENT_CONSUMER_R38.json')
    assert consumer['status'] == 'passed' and consumer['snapshot'] == application['snapshot']
    assert application['all_material_property_bytes_unchanged'] and consumer['complete_source_records'] == 40
    mapping_entry = HERE / 'REVIEW_MAPPING_INPUTS_R38.json'
    mapping = read(mapping_entry)
    approval = HERE / 'INDEPENDENT_METADATA_MAPPING_REVIEW_R38.json'
    assert read(approval)['decision'] == 'approved' and read(approval)['review_inputs_sha256'] == sha(mapping_entry)
    source_path = 'materials_boundaries/data/sources.json'
    backup = EXT / 'baseline-source/sources.json'
    resolution = []
    for folder, filename, field in [
        (HERE.parent / 'local-acceptance-r37', 'REVIEW_ACCEPTANCE_INPUTS_R37_R2.json', 'repo_files_sha256'),
        (HERE.parent / 'local-acceptance-r37', 'NATIVE_TEST_INPUTS_R37.json', None),
        (HERE.parent / 'local-acceptance-r37', 'PACKAGE_INPUTS_R37.json', None),
        (AUDIT, 'REVIEW_INPUTS_R1.json', 'native_files_sha256'),
        (HERE, 'REVIEW_MAPPING_INPUTS_R38.json', 'native_files_sha256')]:
        entry = folder / filename
        obj = read(entry)
        digest = obj[field][source_path] if field else obj[source_path]
        assert sha(backup) == digest
        resolution.append({'entry': entry.relative_to(ROOT).as_posix(), 'entry_sha256': sha(entry),
            'field': field or 'plain_hash_map', 'repository_path': source_path, 'expected_sha256': digest,
            'resolved_path_hint': str(backup), 'scope': 'Expected before-r38 source bytes,not current source hash'})
    r37 = read(HERE.parent / 'local-acceptance-r37/REVIEW_ACCEPTANCE_INPUTS_R37_R2.json')
    unchanged = {name: digest for name, digest in r37['repo_files_sha256'].items() if name != source_path}
    assert all(sha(ROOT / name) == digest for name, digest in unchanged.items())
    write('BEFORE_SOURCE_CONTEXT_RESOLUTION_R38.json', {'contexts': resolution,
        'unaffected_r37_repo_bindings': len(unchanged), 'unaffected_r37_repo_bindings_match': True,
        'historical_entries_rewritten': False, 'old_installation_not_updated_or_claimed_as_r38': True,
        'full_historical_replay': 'not_run'})
    repo = {ROOT / name for name in mapping['repo_files_sha256']}
    repo |= {ROOT / name for name in inputs}
    repo |= {path for path in HERE.iterdir() if path.is_file()}
    repo.add(mapping_entry)
    external = {Path(name) for name in mapping['external_files_sha256']}
    external.add(backup)
    external |= {path for path in (EXT / 'accepted-source-forty').rglob('*') if path.is_file()}
    entry = {'schema': 'source-only-actual-native-integration-review/1',
        'repo_files_sha256': {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(repo)},
        'external_files_sha256': {str(path): sha(path) for path in sorted(external)},
        'snapshot': application['snapshot'], 'scope': 'Actual1sourceURL+1note,unchangedallmaterial/propertybytes,19DBchecks,40completejoins',
        'installation': 'not_run_for_metadata_only_update;r37install notr38evidence',
        'review_constraints': 'Readonly owninlinehash/JSON/schema/bounded currentquery/exports checks;no authorhelpers/testmodules/suites/fullgraph/history/write/install/push'}
    write('REVIEW_INTEGRATION_INPUTS_R38.json', entry)
    print(json.dumps({'entry_sha256': sha(HERE / 'REVIEW_INTEGRATION_INPUTS_R38.json'), 'repo_files': len(repo), 'external_files': len(external)}))


if __name__ == '__main__':
    main()
