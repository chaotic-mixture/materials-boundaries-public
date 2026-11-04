"""Freeze actual application/install evidence and historical byte contexts."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
MAPPING = HERE.parent / 'pur-tga-native-mapping-r1'
EXT = ROOT.parent / 'open-database-evidence/polymer-native-acceptance-20261104-r37'
CACHE = {}


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    path = path.resolve()
    if path not in CACHE:
        CACHE[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return CACHE[path]


def main():
    application = read(HERE / 'APPLICATION_R37.json')
    assert all(sha(ROOT / name) == digest for name, digest in application['after_sha256'].items())
    test = read(HERE / 'NATIVE_TEST_RESULTS_R37.json')
    assert test['successful'] and test['tests_run'] == 34 and test['inputs_unchanged'] and not test['skipped']
    installed = read(HERE / 'INSTALLED_VALIDATION_R37.json')
    assert installed['native_package_inputs_unchanged'] and installed['installed_probe']['snapshot'] == application['snapshot']
    assert installed['installed_probe']['new_TGA_records'] == 28 and installed['installed_probe']['complete_source_records'] == 40
    mapping_entry = MAPPING / 'REVIEW_INPUTS_R1.json'
    previous = read(mapping_entry)
    approval = MAPPING / 'INDEPENDENT_MAPPING_REVIEW_R1.json'
    assert read(approval)['decision'] == 'approved' and read(approval)['review_inputs_sha256'] == sha(mapping_entry)
    repo = {ROOT / name for name in previous['repo_files_sha256']}
    repo |= {mapping_entry, approval} | {p for p in HERE.iterdir() if p.is_file()}
    external = {Path(name) for name in previous['external_files_sha256']}
    contexts = read(HERE / 'HISTORICAL_INPUT_RESOLUTION_R37.json')
    for context in contexts['contexts']:
        entry = ROOT / context['entry']
        assert sha(entry) == context['entry_sha256']
        repo.add(entry)
        for item in context['resolved'].values():
            path = Path(item['resolved_path_hint'])
            assert sha(path) == item['sha256']
            if path.is_relative_to(ROOT):
                repo.add(path)
            else:
                external.add(path)
    for name in read(HERE / 'NATIVE_TEST_INPUTS_R37.json'):
        repo.add(ROOT / name)
    package = read(HERE / 'PACKAGE_INPUTS_R37.json')
    assert all(sha(ROOT / name) == digest for name, digest in package.items())
    stage = EXT / 'installed-check/source'
    external |= {stage / name for name in package}
    site = EXT / 'installed-check/venv/Lib/site-packages'
    record = site / 'materials_boundaries-0.35.0+polymerlocal.20261104.r37.dist-info/RECORD'
    for row in csv.reader(record.read_text(encoding='utf-8').splitlines()):
        path = (site / row[0]).resolve()
        assert path.is_relative_to(EXT / 'installed-check/venv')
        external.add(path)
    external |= {p for p in (EXT / 'baseline-tables').iterdir() if p.is_file()}
    external |= {p for p in (EXT / 'installed-check').iterdir() if p.is_file()}
    external |= {p for p in (EXT / 'installed-check/dist').iterdir() if p.is_file()}
    for folder in [EXT / 'accepted-new-twenty-eight', EXT / 'accepted-complete-source-forty',
                   EXT / 'installed-check/installed-twenty-eight-export', EXT / 'installed-check/installed-source-forty-export']:
        external |= {p for p in folder.rglob('*') if p.is_file()}
    entry = {'schema': 'r37-real-native-installation-integration-review/1',
        'repo_files_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(repo)},
        'external_files_sha256': {str(p): sha(p) for p in sorted(external)},
        'snapshot': application['snapshot'], 'actual_applied_properties_states': [28, 4],
        'current_native_tests': test, 'actual_installed_wheel_sha256': installed['wheel_sha256'],
        'scope': 'Actual applied3tables/currentruntime/newisolatedinstallation/28and40boundedjoins/historicalbytepins',
        'review_constraints': 'Readonly owninlinehash/JSON/wheel-RECORD/source-byte checks and bounded existing-installed queries only;no author helpers/testmodules/suites/fullgraph/history/write/install/push'}
    output = HERE / 'REVIEW_ACCEPTANCE_INPUTS_R37.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(entry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'entry_sha256': sha(output), 'repo_files': len(repo), 'external_files': len(external)}))


if __name__ == '__main__':
    main()
