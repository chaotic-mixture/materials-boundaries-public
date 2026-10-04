"""Bounded v0.28 compatibility: recover exact accepted bytes, never skip hashes.

The new independent preservation test pins this adapter and its ledger. Existing
historical fixtures and the provenance helper remain untouched. These hashes
identify repository payloads, not publisher artifacts or scientific review.
"""
from copy import deepcopy
import hashlib
import json
import re
from pathlib import Path
from source_evidence_preservation import previous_record
from windows_export_preservation import pre_windows_export_bytes

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = 'tests/fixtures/composite_updates_v0280.json'
BASELINE_COMMIT = '2fd1585423dd05478c24396bf6f0206db1b5ae9a'
BASELINE_TREE = 'e62c0cae498f35e460d0d8552998d624f8502640'
EXECUTABLE_IDS = frozenset({
    'hs_bulk_3d_two_phase', 'reuss_bulk', 'voigt_bulk',
    'hs_shear_3d_two_phase', 'reuss_shear', 'voigt_shear',
    'youngs_modulus_outer', 'poissons_ratio_outer',
})
ALLOWED_PATHS = frozenset({
    'CITATION.cff', 'CONTRIBUTING.md', 'README.md', 'THIRD_PARTY_NOTICES.md',
    'docs/GETTING_STARTED.de.md', 'docs/GETTING_STARTED.en.md',
    'docs/GETTING_STARTED.ja.md', 'docs/GETTING_STARTED.zh.md',
    'materials_boundaries/_version.py', 'materials_boundaries/cli.py',
    'scripts/check_wheel_metadata.py',
    'tests/yield_preservation.py', 'tests/test_yield_preservation.py',
})


def valid_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError('Duplicate v0.28 preservation key: ' + key)
        result[key] = value
    return result


def load_ledger():
    return json.loads((ROOT / LEDGER_PATH).read_text(encoding='utf-8'), object_pairs_hook=unique_keys)


def validate_ledger(ledger):
    expected_keys = {'schema_version', 'release', 'scope', 'review', 'baseline_sha256',
                     'approved_existing_updates', 'catalog_preservation', 'release_readme_summary'}
    if (not isinstance(ledger, dict) or set(ledger) != expected_keys
            or ledger['schema_version'] != 1 or ledger['release'] != '0.28.0'
            or ledger['scope'] != 'offline_composite_workflow_exact_compatibility'
            or ledger['review'] != {'kind': 'current_release_compatibility_review',
                'review_date': '2026-10-04', 'baseline_commit': BASELINE_COMMIT,
                'baseline_tree': BASELINE_TREE, 'baseline_file_count': 309,
                'historical_review_claimed': False}):
        raise AssertionError('Unexpected v0.28 preservation metadata')
    baseline = ledger['baseline_sha256']
    if (not isinstance(baseline, dict) or len(baseline) != 309
            or any(not isinstance(path, str) or not valid_digest(value)
                   for path, value in baseline.items())):
        raise AssertionError('Incomplete v0.28 baseline')
    entries = ledger['approved_existing_updates']
    if (not isinstance(entries, list) or not entries
            or any(not isinstance(e, dict) for e in entries)):
        raise AssertionError('Invalid v0.28 exact-edit ledger')
    names = [e.get('filename') for e in entries]
    if any(not isinstance(name, str) for name in names):
        raise AssertionError('Invalid v0.28 filename')
    if (len(set(names)) != len(names) or not set(names) <= ALLOWED_PATHS
            or not set(names) <= set(baseline)):
        raise AssertionError('Duplicate or unapproved v0.28 file')
    for entry in entries:
        if (set(entry) != {'filename', 'previous_sha256', 'sha256', 'reason', 'edits'}
                or entry['previous_sha256'] != baseline[entry['filename']]
                or not isinstance(entry['reason'], str) or not entry['reason'].strip()
                or not valid_digest(entry['sha256'])
                or not isinstance(entry['edits'], list) or not entry['edits']):
            raise AssertionError('Invalid v0.28 successor entry')
    validate_catalog_ledger(ledger['catalog_preservation'])
    if not isinstance(ledger['release_readme_summary'], str):
        raise AssertionError('Invalid v0.28 README summary')
    return {entry['filename']: entry for entry in entries}


def apply_exact_edits(source, edits):
    """Offsets are UTF-8 byte offsets in the complete predecessor."""
    if not isinstance(source, bytes) or not isinstance(edits, list):
        raise AssertionError('Expected bytes and exact edits')
    result, end = bytearray(), 0
    for edit in edits:
        if (not isinstance(edit, dict) or set(edit) != {'offset', 'before', 'after'}
                or not isinstance(edit['before'], str) or not isinstance(edit['after'], str)):
            raise AssertionError('Invalid v0.28 exact-edit fields')
        offset, before, after = edit['offset'], edit['before'].encode(), edit['after'].encode()
        if (type(offset) is not int or offset < end or offset > len(source)
                or source[offset:offset + len(before)] != before or before == after):
            raise AssertionError('Invalid or overlapping v0.28 exact edit')
        result.extend(source[end:offset]); result.extend(after)
        end = offset + len(before)
    result.extend(source[end:])
    return bytes(result)


def reverse_exact_edits(current, entry):
    if digest(current) != entry['sha256']:
        raise AssertionError('Unreviewed v0.28 current bytes: ' + entry['filename'])
    delta, reverse = 0, []
    for edit in entry['edits']:
        # Validate the complete edit contract before calculating its reverse.
        if (not isinstance(edit, dict) or set(edit) != {'offset', 'before', 'after'}
                or type(edit['offset']) is not int or edit['offset'] < 0
                or not isinstance(edit['before'], str) or not isinstance(edit['after'], str)):
            raise AssertionError('Invalid v0.28 reverse edit')
        before, after = edit['before'], edit['after']
        reverse.append({'offset': edit['offset'] + delta, 'before': after, 'after': before})
        delta += len(after.encode()) - len(before.encode())
    predecessor = apply_exact_edits(current, reverse)
    if (digest(predecessor) != entry['previous_sha256']
            or apply_exact_edits(predecessor, entry['edits']) != current):
        raise AssertionError('Broken v0.28 predecessor reconstruction: ' + entry['filename'])
    return predecessor


def pre_composite_bytes(filename, current, *, ledger=None):
    """Verify exact current bytes, then recover only a recorded predecessor."""
    ledger = load_ledger() if ledger is None else ledger
    entries = validate_ledger(ledger)
    accepted = entries[filename]['sha256'] if filename in entries else ledger['baseline_sha256'].get(filename)
    if digest(current) != accepted:
        current = pre_windows_export_bytes(filename, current)
    if filename in entries:
        return reverse_exact_edits(current, entries[filename])
    if filename not in ledger['baseline_sha256'] or digest(current) != ledger['baseline_sha256'][filename]:
        raise AssertionError('Unreviewed unchanged v0.28 baseline file: ' + str(filename))
    return current


def release_readme_bytes(actual):
    """Accept only truthful marked count refreshes; restore exact release counts."""
    text = actual.decode('utf-8')
    start, end = '<!-- current-catalog-summary:start -->', '<!-- current-catalog-summary:end -->'
    if text.count(start) != 1 or text.count(end) != 1:
        raise AssertionError('Expected exactly one current README summary')
    before, selected = text.split(start); summary, after = selected.split(end)
    release = load_ledger()['release_readme_summary']
    def catalog(name):
        return json.loads((ROOT / 'materials_boundaries/data' / (name + '.json')).read_text())
    claims, sources, observations = (catalog(name)['records'] for name in ('claims', 'sources', 'observations'))
    predictions = catalog('computational_predictions')
    demos = [r for r in catalog('temperature_models')['records'] if r['classification'] == 'synthetic_demo']
    synthetic = sum(r['role'] == 'synthetic_demo_provenance' for r in sources)
    pairs = [
        (r'\*\*\d+ mechanics claims\*\*', f'**{len(claims)} mechanics claims**'),
        (r'\*\*\d+ source records\*\*', f'**{len(sources)} source records**'),
        (r'\*\*\d+ observations from \d+ studies\*\*', f'**{len(observations)} observations from {len({r["study_id"] for r in observations})} studies**'),
        (r'\*\*\d+ published computational predictions in \d+ scientific families and \d+ explicit groups\*\*',
         f'**{len(predictions["records"])} published computational predictions in {len({p["family"] for p in predictions["protocols"]})} scientific families and {len(predictions["comparison_groups"])} explicit groups**'),
        (r'\*\*\d+ synthetic temperature demos with \d+ branches\*\*', f'**{len(demos)} synthetic temperature demos with {sum(len(r["branches"]) for r in demos)} branches**'),
        (r'The \d+ sources comprise \d+ bibliographic/source records plus \d+ original synthetic-demo provenance record',
         f'The {len(sources)} sources comprise {len(sources)-synthetic} bibliographic/source records plus {synthetic} original synthetic-demo provenance record'),
    ]
    expected = release
    for pattern, value in pairs:
        expected, count = re.subn(pattern, lambda match: value, expected)
        if count != 1:
            raise AssertionError('Invalid release README count template: ' + pattern)
    if summary != expected:
        raise AssertionError('Only truthful current-summary counts may differ in a rehearsal')
    return (before + start + release + end + after).encode('utf-8')


def validate_catalog_ledger(catalogs):
    """Pin whole prior objects and metadata; only independent entries may append."""
    expected = {
        'claims', 'computational_predictions', 'locales', 'observations',
        'prediction_locales', 'sources', 'temperature_locales',
        'temperature_models', 'visualization_locales',
    }
    if (not isinstance(catalogs, dict)
            or set(catalogs) != {'materials_boundaries/data/' + name + '.json' for name in expected}):
        raise AssertionError('Invalid v0.28 catalog inventory')
    for filename, fields in catalogs.items():
        if not isinstance(fields, dict) or not fields:
            raise AssertionError('Invalid v0.28 catalog fields')
        for field, entry in fields.items():
            claims = filename == 'materials_boundaries/data/claims.json' and field == 'records'
            if (not isinstance(entry, dict)
                    or (set(entry) != {'record_digests', 'evidence_digests'} if claims else len(entry) != 1)):
                raise AssertionError('Invalid v0.28 catalog contract')
            if claims:
                records, evidence = entry['record_digests'], entry['evidence_digests']
                if (not isinstance(records, dict) or not isinstance(evidence, dict)
                        or not EXECUTABLE_IDS <= set(records)
                        or set(records) - EXECUTABLE_IDS != set(evidence)
                        or any(not isinstance(hashes, list) or not hashes
                               or any(not valid_digest(value) for value in hashes)
                               or len(set(hashes)) != len(hashes) for hashes in evidence.values())):
                    raise AssertionError('Invalid v0.28 exact prior evidence digests')
            kind = 'record_digests' if claims else next(iter(entry))
            values = entry[kind]
            if kind == 'sha256':
                if not valid_digest(values):
                    raise AssertionError('Invalid v0.28 metadata digest')
            elif kind in ('record_digests', 'label_digests'):
                if (not isinstance(values, dict) or not values
                        or any(not isinstance(key, str) or not valid_digest(value)
                               for key, value in values.items())):
                    raise AssertionError('Invalid v0.28 object digests')
            elif kind == 'locale_label_digests':
                if (not isinstance(values, dict) or not values
                        or any(not isinstance(language, str) or not isinstance(labels, dict)
                               or not labels or any(not isinstance(label, str) or not valid_digest(value)
                                                    for label, value in labels.items())
                               for language, labels in values.items())):
                    raise AssertionError('Invalid v0.28 locale digests')
            else:
                raise AssertionError('Unknown v0.28 catalog contract')


def verify_catalog(filename, current, *, ledger=None):
    """Keep full prior objects exact; only catalog-only claim evidence may append.

    Original evidence objects and their order remain mandatory. Reconstructing
    that exact prefix removes only independently appended objects, never fields
    inside an old evidence object or any other prior record metadata.
    """
    ledger = load_ledger() if ledger is None else ledger
    validate_ledger(ledger)
    fields = ledger['catalog_preservation'].get(filename)
    if not fields or not isinstance(current, dict) or set(current) != set(fields):
        raise AssertionError('Unreviewed v0.28 catalog envelope: ' + str(filename))
    for key, baseline in fields.items():
        kind = 'record_digests' if 'record_digests' in baseline else next(iter(baseline))
        values = baseline[kind]
        actual = current[key]
        if kind == 'record_digests':
            if (not isinstance(actual, list)
                    or any(not isinstance(record, dict) or not isinstance(record.get('id'), str)
                           for record in actual)):
                raise AssertionError('Invalid v0.28 record collection')
            index = {record['id']: record for record in actual}
            if len(index) != len(actual):
                raise AssertionError('Duplicate v0.28 record identity')
            for identifier, expected in values.items():
                if identifier not in index:
                    raise AssertionError('Missing v0.28 prior object: ' + identifier)
                prior = previous_record(Path(filename).stem, index[identifier])
                if identifier in baseline.get('evidence_digests', {}):
                    pinned = baseline['evidence_digests'][identifier]
                    evidence = prior.get('evidence')
                    if (not isinstance(evidence, list)
                            or any(not isinstance(item, dict) for item in evidence)):
                        raise AssertionError('Invalid v0.28 claim evidence: ' + identifier)
                    hashes = [digest(canonical(item)) for item in evidence]
                    if hashes[:len(pinned)] != pinned or len(set(hashes)) != len(hashes):
                        raise AssertionError('Changed v0.28 prior evidence: ' + identifier)
                    prior['evidence'] = evidence[:len(pinned)]
                if digest(canonical(prior)) != expected:
                    raise AssertionError('Changed v0.28 prior object: ' + identifier)
        elif kind == 'locale_label_digests':
            if not isinstance(actual, dict):
                raise AssertionError('Invalid v0.28 locale collection')
            for language, labels in values.items():
                if language not in actual or not isinstance(actual[language], dict):
                    raise AssertionError('Missing v0.28 locale: ' + language)
                for label, expected in labels.items():
                    if label not in actual[language] or digest(canonical(actual[language][label])) != expected:
                        raise AssertionError('Changed v0.28 prior locale label: ' + language + '/' + label)
        elif kind == 'label_digests':
            if not isinstance(actual, dict):
                raise AssertionError('Invalid v0.28 label collection')
            for label, expected in values.items():
                if label not in actual or digest(canonical(actual[label])) != expected:
                    raise AssertionError('Changed v0.28 prior label: ' + label)
        elif digest(canonical(actual)) != values:
            raise AssertionError('Changed v0.28 catalog metadata: ' + key)
    return True
