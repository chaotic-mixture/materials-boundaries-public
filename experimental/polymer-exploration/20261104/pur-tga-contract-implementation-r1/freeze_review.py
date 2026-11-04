"""Freeze concrete implementation, bounded execution and prior-byte resolution."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXTERNAL = ROOT.parent / 'open-database-evidence/polymer-tga-contract-20261104-r1'
BASE = EXTERNAL / 'baseline'
PROPOSAL = HERE.parent / 'pur-tga-endpoint-contract-proposal-r2'


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def resolve(pins):
    aliases = {
        'tests/test_tga_endpoint_contract.py': BASE / 'initial_test_tga_endpoint_contract.py',
        (HERE / 'validate_implementation.py').relative_to(ROOT).as_posix(): BASE / 'initial_validate_implementation.py',
    }
    resolutions = []
    for name, digest in pins.items():
        current = ROOT / name
        old = aliases.get(name, BASE / Path(name).name)
        resolved = current if current.is_file() and sha(current) == digest else old
        assert resolved.is_file() and sha(resolved) == digest, name
        resolutions.append({'repository_path': name, 'sha256': digest, 'resolved_path': str(resolved)})
    return resolutions


def main():
    result = read(HERE / 'TEST_RESULTS_R2.json')
    assert result['successful'] and result['tests_run'] == 142
    assert result['failures'] == result['errors'] == result['skipped'] == 0 and result['inputs_unchanged']
    current_inputs = read(HERE / 'EXECUTION_INPUTS_R2.json')
    assert all(sha(ROOT / name) == digest for name, digest in current_inputs.items())
    entry = PROPOSAL / 'REVIEW_INPUTS_R2.json'
    assert sha(entry) == '428532f1177fd700e7f371a814f307ae17915a97396d48db0d082721fcf35ee1'
    approval = PROPOSAL / 'INDEPENDENT_CONCEPT_REVIEW_R2.json'
    assert read(approval)['decision'] == 'approved'
    previous = read(entry)
    native = previous['native_files_sha256']
    assert all(sha(ROOT / name) == digest for name, digest in native.items())
    write('HISTORICAL_INPUT_RESOLUTION_R1.json', {
        'concept_R2': resolve(previous['repo_files_sha256']),
        'first_failed_execution_R1': resolve(read(HERE / 'EXECUTION_INPUTS_R1.json')),
        'old_manifest_files_rewritten': False,
    })
    old_schema = read(BASE / 'reference_properties.schema.json')
    schema = read(ROOT / 'schemas/reference_properties.schema.json')
    assert schema['$defs']['property']['oneOf'][:7] == old_schema['$defs']['property']['oneOf']
    assert schema['$defs']['legacy_reported_value'] == old_schema['$defs']['legacy_reported_value']
    write('SCHEMA_PRESERVATION_R1.json', {'prior_branch_count': 7, 'current_branch_count': 11,
        'old_seven_branch_objects_equal': True, 'legacy_central_value_domain_equal': True,
        'native_table_hashes_unchanged': native, 'new_real_TGA_records': 0,
        'prior_runtime_schema_locales_and_tests': 'Exact external baseline bytes retained',
        'installation_native_mapping_admission': 'not_run'})
    files = {ROOT / name for name in current_inputs}
    files |= {ROOT / name for name in previous['repo_files_sha256']}
    files |= {entry, approval}
    files |= {p for p in HERE.iterdir() if p.is_file()}
    external_files = {Path(name) for name in previous['external_files_sha256']}
    external_files |= {p for p in BASE.iterdir() if p.is_file()}
    external_files.add(EXTERNAL / 'initial-tests.log')
    manifest = {
        'schema': 'TGA-endpoint-concrete-implementation-review/1',
        'repo_files_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)},
        'external_files_sha256': {str(p): sha(p) for p in sorted(external_files)},
        'scope': 'Concrete runtime/schema/render/locales/affected tests and bounded native regression;not28real mapping/install/admission',
        'concept_review_entry_sha256': sha(entry), 'concept_approval_sha256': sha(approval),
        'current_tests': result, 'native_table_hashes_unchanged': native,
        'review_constraints': 'Readonly own inline hashes/JSON/schema/limited independent synthetic checks only;no author helpers/test modules/suites/fullgraph/history/writes/install/push',
    }
    write('REVIEW_INPUTS_R1.json', manifest)
    print(json.dumps({'entry_sha256': sha(HERE / 'REVIEW_INPUTS_R1.json'), 'repo_files': len(manifest['repo_files_sha256']), 'external_files': len(external_files)}))


if __name__ == '__main__':
    main()
