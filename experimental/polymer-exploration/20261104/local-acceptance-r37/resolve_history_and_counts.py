"""Resolve historical byte pins and count current fields, without replaying tests."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
AREA = HERE.parent
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
    prior = read(AREA / 'local-acceptance-r36/HISTORICAL_INPUT_RESOLUTION_R36.json')
    candidates = set()
    for context in prior['contexts']:
        candidates |= {Path(item['resolved_path_hint']) for item in context['resolved'].values()}
    for folder in ['polymer-tga-contract-20261104-r1/baseline', 'polymer-native-acceptance-20261104-r37/baseline-tables']:
        candidates |= {p for p in (ROOT.parent / 'open-database-evidence' / folder).iterdir() if p.is_file()}
    by_hash = {}
    for path in sorted(candidates):
        if path.is_file():
            by_hash.setdefault(sha(path), path)
    contexts = []

    def add(entry_path, field, pins, expected_entry_sha=None):
        entry = ROOT / entry_path
        if expected_entry_sha:
            assert sha(entry) == expected_entry_sha, entry_path
        resolved = {}
        for name, digest in pins.items():
            current = Path(name) if Path(name).is_absolute() else ROOT / name
            path = current if current.is_file() and sha(current) == digest else by_hash.get(digest)
            assert path is not None and path.is_file() and sha(path) == digest, (entry_path, name)
            by_hash.setdefault(digest, path)
            resolved[name] = {'sha256': digest, 'resolved_path_hint': str(path), 'current': path.resolve() == current.resolve()}
        contexts.append({'entry': entry_path, 'entry_sha256': sha(entry), 'field': field, 'resolved': resolved})

    for context in prior['contexts']:
        add(context['entry'], context['field'], {name: item['sha256'] for name, item in context['resolved'].items()}, context['entry_sha256'])
    entries = [
        ('local-acceptance-r36/REVIEW_ACCEPTANCE_INPUTS_R36.json', ['repo_files_sha256', 'external_files_sha256']),
        ('local-acceptance-r36/NATIVE_TEST_INPUTS_R36.json', [None]),
        ('local-acceptance-r36/PACKAGE_INPUTS_R36.json', [None]),
        ('pur-tga-endpoint-contract-proposal-r1/REVIEW_INPUTS_R1.json', ['repo_files_sha256', 'native_files_sha256', 'external_files_sha256']),
        ('pur-tga-endpoint-contract-proposal-r2/REVIEW_INPUTS_R2.json', ['repo_files_sha256', 'native_files_sha256', 'external_files_sha256']),
        ('pur-tga-contract-implementation-r1/REVIEW_INPUTS_R1.json', ['repo_files_sha256', 'external_files_sha256']),
        ('pur-tga-contract-implementation-r1/EXECUTION_INPUTS_R1.json', [None]),
        ('pur-tga-contract-implementation-r1/EXECUTION_INPUTS_R2.json', [None]),
        ('pur-tga-native-mapping-r1/REVIEW_INPUTS_R1.json', ['repo_files_sha256', 'external_files_sha256']),
        ('local-acceptance-r37/NATIVE_TEST_INPUTS_R37.json', [None]),
        ('local-acceptance-r37/PACKAGE_INPUTS_R37.json', [None]),
    ]
    for relative, fields in entries:
        path = AREA / relative
        obj = read(path)
        for field in fields:
            add(path.relative_to(ROOT).as_posix(), field or 'plain_hash_map', obj[field] if field else obj)
    output = {'schema': 'r37-historical-context-resolution/1', 'contexts': contexts,
        'context_count': len(contexts), 'bindings': sum(len(c['resolved']) for c in contexts),
        'unresolved': 0, 'absent_baseline_paths': prior.get('absent_baseline_paths', []),
        'policy': 'Historical entries unchanged;before-r37 table bytes and before-TGA runtime/schema/locales/test bytes retained;no historical test replay'}
    write('HISTORICAL_INPUT_RESOLUTION_R37.json', output)
    materials = read(ROOT / 'materials_boundaries/data/materials.json')
    properties = read(ROOT / 'materials_boundaries/data/reference_properties.json')
    identities = {item['id'] for item in materials['identities'] if item['category'] == 'polymer'}
    states = {item['id'] for item in materials['records'] if item['identity_id'] in identities}
    all_polymer = [item for item in properties['records'] if item['material_state_id'] in states]
    experimental = [item for item in all_polymer if item['evidence_kind'] == 'published_experimental_reference']
    counts = {'snapshot': read(HERE / 'APPLICATION_R37.json')['snapshot'], 'polymer_identities': len(identities),
        'polymer_states': len(states), 'polymer_properties': len(all_polymer), 'experimental_labels': len(experimental),
        'temperature_not_reported': sum(p['conditions']['temperature']['status'] == 'not_reported_in_inspected_source' for p in experimental),
        'conditioning_not_reported': sum(p['conditions']['conditioning']['status'] == 'not_reported_in_inspected_source' for p in experimental),
        'exact_n': sum(p['sample_count']['relation'] == 'exact' for p in experimental),
        'n_null': sum(p['sample_count']['value'] is None for p in experimental),
        'exact_n_unconfirmed': sum(p['sample_count']['relation'] != 'exact' for p in experimental),
        'scope': 'Property labels,not independent specimen/batch counts or completenessrate'}
    write('CURRENT_POLYMER_CONDITION_COUNTS_R37.json', counts)
    print(json.dumps({'contexts': len(contexts), 'bindings': output['bindings'], 'polymer': counts}), flush=True)


if __name__ == '__main__':
    main()
