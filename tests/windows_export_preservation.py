"""Bounded v0.28.1 Windows-export bridge to the exact public v0.28.0 bytes.

This test-only adapter never accepts arbitrary replacements or rewrites an old
fixture. The independent preservation tests pin this adapter and its new ledger.
Repository digests are neither scientific review nor publisher-asset identity.
"""
import hashlib
import json
from pathlib import Path
from source_evidence_preservation import pre_evidence_bytes

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = 'tests/fixtures/windows_export_updates_v0281.json'
BASELINE_COMMIT = '08ca206c1ae558643e38bde5dfc632cb65328c68'
BASELINE_TREE = '203db3af3b54198b175ab631643f0a673b529716'
BASELINE_FILE_COUNT = 328
ALLOWED_PATHS = frozenset({
    '.github/workflows/ci.yml', 'CITATION.cff', 'README.md',
    'docs/COMPOSITE_WORKFLOW.md', 'materials_boundaries/_version.py',
    'materials_boundaries/composite_export.py', 'scripts/check_wheel_metadata.py',
    'tests/composite_preservation.py', 'tests/test_composite_preservation.py',
    'tests/test_composite_export.py', 'tests/test_composite_acceptance.py',
})


def digest(value):
    return hashlib.sha256(value).hexdigest()


def valid_digest(value):
    return (isinstance(value, str) and len(value) == 64
            and all(char in '0123456789abcdef' for char in value))


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError('Duplicate v0.28.1 preservation key: ' + key)
        result[key] = value
    return result


def load_ledger():
    return json.loads((ROOT / LEDGER_PATH).read_text(encoding='utf-8'),
                      object_pairs_hook=unique_keys)


def validate_edits(edits):
    if not isinstance(edits, list) or not edits:
        raise AssertionError('Expected nonempty v0.28.1 exact edits')
    end, previous_offset = 0, -1
    for edit in edits:
        if (not isinstance(edit, dict) or set(edit) != {'offset', 'before', 'after'}
                or type(edit['offset']) is not int
                or not isinstance(edit['before'], str)
                or not isinstance(edit['after'], str)
                or edit['before'] == edit['after']
                or edit['offset'] < end or edit['offset'] <= previous_offset):
            raise AssertionError('Invalid or overlapping v0.28.1 exact edit')
        previous_offset = edit['offset']
        end = previous_offset + len(edit['before'].encode('utf-8'))


def validate_ledger(ledger):
    expected_keys = {'schema_version', 'release', 'scope', 'review',
                     'baseline_sha256', 'approved_existing_updates'}
    if (not isinstance(ledger, dict) or set(ledger) != expected_keys
            or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
            or ledger['release'] != '0.28.1'
            or ledger['scope'] != 'windows_composite_export_exact_compatibility'
            or ledger['review'] != {
                'kind': 'current_release_compatibility_review',
                'review_date': '2026-10-04', 'baseline_commit': BASELINE_COMMIT,
                'baseline_tree': BASELINE_TREE, 'baseline_file_count': BASELINE_FILE_COUNT,
                'historical_review_claimed': False,
            }):
        raise AssertionError('Unexpected v0.28.1 preservation metadata')
    baseline = ledger['baseline_sha256']
    if (not isinstance(baseline, dict) or len(baseline) != BASELINE_FILE_COUNT
            or any(not isinstance(path, str) or not path
                   or path.startswith('/') or '\\' in path
                   or any(part in ('', '.', '..') for part in path.split('/'))
                   or not valid_digest(value) for path, value in baseline.items())):
        raise AssertionError('Incomplete v0.28.1 public baseline')
    entries = ledger['approved_existing_updates']
    if (not isinstance(entries, list) or not entries
            or any(not isinstance(entry, dict) for entry in entries)):
        raise AssertionError('Invalid v0.28.1 exact-edit ledger')
    names = [entry.get('filename') for entry in entries]
    if (any(not isinstance(name, str) for name in names)
            or len(set(names)) != len(names) or set(names) != ALLOWED_PATHS
            or not set(names) <= set(baseline)):
        raise AssertionError('Missing, duplicate or unapproved v0.28.1 file')
    for entry in entries:
        if (set(entry) != {'filename', 'previous_sha256', 'sha256', 'reason', 'edits'}
                or entry['previous_sha256'] != baseline[entry['filename']]
                or not valid_digest(entry['sha256'])
                or entry['sha256'] == entry['previous_sha256']
                or not isinstance(entry['reason'], str) or not entry['reason'].strip()):
            raise AssertionError('Invalid v0.28.1 successor entry')
        validate_edits(entry['edits'])
    return {entry['filename']: entry for entry in entries}


def apply_exact_edits(source, edits):
    """Apply ordered UTF-8 byte-offset replacements to a complete predecessor."""
    if not isinstance(source, bytes):
        raise AssertionError('Expected v0.28.1 source bytes')
    validate_edits(edits)
    result, end = bytearray(), 0
    for edit in edits:
        offset = edit['offset']
        before, after = edit['before'].encode('utf-8'), edit['after'].encode('utf-8')
        if offset > len(source) or source[offset:offset + len(before)] != before:
            raise AssertionError('Unreviewed v0.28.1 exact-edit source')
        result.extend(source[end:offset])
        result.extend(after)
        end = offset + len(before)
    result.extend(source[end:])
    return bytes(result)


def reverse_exact_edits(current, entry):
    if not isinstance(current, bytes) or digest(current) != entry['sha256']:
        raise AssertionError('Unreviewed v0.28.1 current bytes: ' + entry['filename'])
    validate_edits(entry['edits'])
    delta, reverse = 0, []
    for edit in entry['edits']:
        before, after = edit['before'], edit['after']
        reverse.append({'offset': edit['offset'] + delta,
                        'before': after, 'after': before})
        delta += len(after.encode('utf-8')) - len(before.encode('utf-8'))
    predecessor = apply_exact_edits(current, reverse)
    if (digest(predecessor) != entry['previous_sha256']
            or apply_exact_edits(predecessor, entry['edits']) != current):
        raise AssertionError('Broken v0.28.1 predecessor reconstruction: ' + entry['filename'])
    return predecessor


def pre_windows_export_bytes(filename, current, *, ledger=None):
    """Recover the exact v0.28.0 predecessor, rejecting any unreviewed bytes."""
    ledger = load_ledger() if ledger is None else ledger
    entries = validate_ledger(ledger)
    accepted = entries[filename]['sha256'] if filename in entries else ledger['baseline_sha256'].get(filename)
    if digest(current) != accepted:
        current = pre_evidence_bytes(filename, current)
    if filename in entries:
        return reverse_exact_edits(current, entries[filename])
    if (not isinstance(current, bytes) or filename not in ledger['baseline_sha256']
            or digest(current) != ledger['baseline_sha256'][filename]):
        raise AssertionError('Unreviewed unchanged v0.28.1 baseline file: ' + str(filename))
    return current
