"""Freeze current complete worktree content and actual consolidated evidence."""
from pathlib import Path
import csv
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
AREA = HERE.parent
EVIDENCE = ROOT.parent / 'open-database-evidence'
INSTALL = EVIDENCE / 'polymer-native-acceptance-20261104-delivery-r36-r38'
CACHE = {}


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    path = path.resolve()
    if path not in CACHE:
        CACHE[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return CACHE[path]


def main():
    baseline = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert baseline == '13c6fa6480bac5bf1ea63442a571a1658b0e4cf3'
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'experimental/open-database'
    assert subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0
    tests = read(HERE / 'SCOPED_TESTS_R36_R38_R2.json')
    assert tests['successful'] and tests['tests_run'] == 218 and tests['failures'] == tests['errors'] == tests['skipped'] == 0
    inputs = read(HERE / 'SCOPED_TEST_INPUTS_R36_R38_R2.json')['repo_files_sha256']
    assert all(sha(ROOT / name) == digest for name, digest in inputs.items())
    approvals = {}
    for folder, entry_name, receipt_name in [
        ('local-acceptance-r36', 'REVIEW_ACCEPTANCE_INPUTS_R36.json', 'INDEPENDENT_ACCEPTANCE_REVIEW_R36.json'),
        ('local-acceptance-r37', 'REVIEW_ACCEPTANCE_INPUTS_R37_R2.json', 'INDEPENDENT_ACCEPTANCE_REVIEW_R37_R2.json'),
        ('local-acceptance-r38', 'REVIEW_INTEGRATION_INPUTS_R38.json', 'INDEPENDENT_INTEGRATION_REVIEW_R38.json')]:
        entry = AREA / folder / entry_name
        receipt = AREA / folder / receipt_name
        review = read(receipt)
        assert review['decision'] == 'approved' and review['review_inputs_sha256'] == sha(entry)
        approvals[folder] = {'entry_sha256': sha(entry), 'approval_sha256': sha(receipt)}
    external = set()
    history = read(HERE / 'HISTORICAL_INPUT_RESOLUTION_R36_R38.json')
    assert history['context_count'] == 155 and history['bindings'] == 10580 and history['unresolved'] == 0
    assert len(history['historical_absence_conditions']) == 2
    for context in history['contexts']:
        assert sha(ROOT / context['entry']) == context['entry_sha256']
        for item in context['resolved'].values():
            path = Path(item['resolved_path_hint'])
            assert sha(path) == item['sha256']
            if not path.is_relative_to(ROOT):
                external.add(path)
    package = read(HERE / 'PACKAGE_INPUTS_R36_R38.json')
    assert all(sha(ROOT / name) == digest for name, digest in package.items())
    installed = read(HERE / 'INSTALLED_VALIDATION_R36_R38.json')
    assert installed['native_package_inputs_unchanged'] and installed['installed_probe']['properties'] == 5412
    for folder in [EVIDENCE / 'polymer-consolidated-delivery-20261104-r36-r38', INSTALL]:
        # Exclude installed environment bulk; add only this distribution below.
        for path in folder.rglob('*'):
            if path.is_file() and 'venv' not in path.relative_to(folder).parts:
                external.add(path)
    site = INSTALL / 'installed-check/venv/Lib/site-packages'
    record = site / 'materials_boundaries-0.35.0+polymerlocal.20261104.delivery3638.dist-info/RECORD'
    for row in csv.reader(record.read_text(encoding='utf-8').splitlines()):
        path = (site / row[0]).resolve()
        assert path.is_relative_to(INSTALL / 'installed-check/venv')
        external.add(path)
    actual = set()
    for args in [['diff', '--name-only', '-z'], ['ls-files', '--others', '--exclude-standard', '-z']]:
        actual |= {name for name in subprocess.check_output(['git', *args], cwd=ROOT).decode().split('\0') if name}
    allowed = set(read(HERE / 'BEFORE_DOCUMENT_BYTES_R36_R38.json'))
    allowed |= {'docs/MATERIAL_REFERENCE_CATALOG.md', 'materials_boundaries/material_references.py', 'materials_boundaries/material_presentation.py',
        'materials_boundaries/data/material_locales.json', 'materials_boundaries/data/materials.json', 'materials_boundaries/data/reference_properties.json',
        'materials_boundaries/data/sources.json', 'schemas/reference_properties.schema.json'}
    for name in actual:
        assert name in allowed or name.startswith('tests/test_') or name.startswith('experimental/polymer-exploration/20261104/'), name
        assert (ROOT / name).suffix in {'.md', '.json', '.py', '.log'}, name
    manifest = {'schema': 'r36-r38-consolidated-content-review/1', 'baseline_commit': baseline,
        'snapshot': installed['installed_probe']['snapshot'], 'repo_files_sha256': {name: sha(ROOT / name) for name in sorted(actual)},
        'external_files_sha256': {str(path): sha(path) for path in sorted(external)},
        'approved_batch_entries': approvals, 'current_tests': tests,
        'scope': 'Complete current r36-r38 content/new32properties8states/closedTGAcontract/currentinstalled/latestmetadata/navigation/history;not remoteCI',
        'review_constraints': 'Readonly ownhash/JSON/diff/schema/RECORD and bounded existinginstalled queries only;no authorhelpers/testmodules/suites/fullgraph/history/write/install/push'}
    output = HERE / 'REVIEW_CONTENT_INPUTS_R36_R38.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'entry_sha256': sha(output), 'repo_files': len(actual), 'external_files': len(external)}))


if __name__ == '__main__':
    main()
