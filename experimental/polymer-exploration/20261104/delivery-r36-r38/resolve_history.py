"""Resolve immutable historical inputs after current docs/test/source updates."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
AREA = HERE.parent
EVIDENCE = ROOT.parent / 'open-database-evidence'
CACHE = {}


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    path = path.resolve()
    if path not in CACHE:
        CACHE[path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return CACHE[path]


def main():
    previous = read(AREA / 'local-acceptance-r37/HISTORICAL_INPUT_RESOLUTION_R37_R2.json')
    pool = {Path(item['resolved_path_hint']) for context in previous['contexts'] for item in context['resolved'].values()}
    for folder in ['polymer-native-acceptance-20261104-r38/baseline-source',
                   'polymer-consolidated-delivery-20261104-r36-r38/before-docs',
                   'polymer-consolidated-delivery-20261104-r36-r38/before-tests-fix',
                   'polymer-native-acceptance-20261104-delivery-r36-r38/installed-check/before-copy-probe-fix']:
        pool |= {path for path in (EVIDENCE / folder).rglob('*') if path.is_file()}
    by_hash = {}
    for path in sorted(pool):
        if path.is_file():
            by_hash.setdefault(sha(path), path)
    contexts = []

    def add(entry, field, pins, expected=None):
        if expected:
            assert sha(entry) == expected
        resolved = {}
        for name, digest in pins.items():
            if digest is None:
                continue
            current = Path(name) if Path(name).is_absolute() else ROOT / name
            path = current if current.is_file() and sha(current) == digest else by_hash.get(digest)
            assert path is not None and path.is_file() and sha(path) == digest, (str(entry), name)
            by_hash.setdefault(digest, path)
            resolved[name] = {'sha256': digest, 'resolved_path_hint': str(path), 'current': path.resolve() == current.resolve()}
        contexts.append({'entry': entry.relative_to(ROOT).as_posix(), 'entry_sha256': sha(entry), 'field': field, 'resolved': resolved})

    for context in previous['contexts']:
        add(ROOT / context['entry'], context['field'], {name: item['sha256'] for name, item in context['resolved'].items()}, context['entry_sha256'])
    for name, fields in [
        ('local-acceptance-r37/REVIEW_ACCEPTANCE_INPUTS_R37.json', ['repo_files_sha256', 'external_files_sha256']),
        ('local-acceptance-r37/REVIEW_ACCEPTANCE_INPUTS_R37_R2.json', ['repo_files_sha256', 'external_files_sha256']),
        ('epoxy-supplement-condition-followup-r1/REVIEW_INPUTS_R1.json', ['repo_files_sha256', 'native_files_sha256', 'external_files_sha256']),
        ('local-acceptance-r38/REVIEW_MAPPING_INPUTS_R38.json', ['repo_files_sha256', 'native_files_sha256', 'external_files_sha256']),
        ('local-acceptance-r38/REVIEW_INTEGRATION_INPUTS_R38.json', ['repo_files_sha256', 'external_files_sha256']),
        ('local-acceptance-r38/EXECUTION_INPUTS_R38.json', [None]),
        ('delivery-r36-r38/SCOPED_TEST_INPUTS_R36_R38.json', ['repo_files_sha256']),
        ('delivery-r36-r38/SCOPED_TEST_INPUTS_R36_R38_R2.json', ['repo_files_sha256']),
        ('delivery-r36-r38/PACKAGE_INPUTS_R36_R38.json', [None]),
    ]:
        entry = AREA / name
        obj = read(entry)
        for field in fields:
            add(entry, field or 'plain_hash_map', obj[field] if field else obj)
    output = {'schema': 'r36-r38-consolidated-historical-input-resolution/1', 'contexts': contexts,
        'context_count': len(contexts), 'bindings': sum(len(context['resolved']) for context in contexts), 'unresolved': 0,
        'historical_absence_conditions': previous['historical_absence_conditions'],
        'scope': 'Exactbeforebytes for phase-specific inputs;currentdata/docs/tests/install verification separate;no historical tests replayed'}
    with (HERE / 'HISTORICAL_INPUT_RESOLUTION_R36_R38.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'contexts': len(contexts), 'bindings': output['bindings'], 'unresolved': 0}), flush=True)


if __name__ == '__main__':
    main()
