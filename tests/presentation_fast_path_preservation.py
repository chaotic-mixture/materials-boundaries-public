"""Test-only exact reversal of the unchanged-presentation fast path to 73f3b0b.

Only four reviewed successor files are accepted. The existing deduplication
and release ledgers and their pins remain unchanged. Production never imports
this layer; it neither caches validation nor grants runtime baseline acceptance.
"""
import hashlib
import json
from pathlib import Path
from material_class_counts_preservation import pre_class_counts_bytes

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = '73f3b0b56f764736e1d4368d0da8fabf1cdf9c7b'
LEDGER_PATH = 'tests/fixtures/presentation_fast_path_updates_v1.json'
LEDGER_SHA256 = 'cb21d602f80d59f66889908de1c8a025de5080570c76db4eb4cf5ae3df437544'
LEDGER_CANONICAL_SHA256 = '925f5c759e124ba868b2979a8a1001491c8481d701c329b4cd9c822fd1e746a0'
ALLOWED_PATHS = frozenset({
    'materials_boundaries/material_presentation.py',
    'tests/material_bulk_preservation.py',
    'tests/test_material_bulk_preservation.py',
    'tests/test_evidence_dedup_preservation.py',
})


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError('Duplicate presentation-fast-path ledger key')
        result[key] = value
    return result


def load_ledger():
    raw = (ROOT / LEDGER_PATH).read_bytes()
    if digest(raw) != LEDGER_SHA256:
        raise AssertionError('Unreviewed presentation-fast-path ledger bytes')
    value = json.loads(raw, object_pairs_hook=unique_keys)
    validate_ledger(value)
    return value


def validate_ledger(ledger):
    if (type(ledger) is not dict
            or set(ledger) != {'schema_version', 'baseline_commit', 'updates'}
            or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
            or ledger['baseline_commit'] != BASELINE_COMMIT
            or type(ledger['updates']) is not list):
        raise AssertionError('Invalid presentation-fast-path ledger envelope')
    try:
        content_digest = digest(canonical(ledger))
    except (TypeError, ValueError) as exc:
        raise AssertionError('Invalid presentation-fast-path ledger content') from exc
    if content_digest != LEDGER_CANONICAL_SHA256:
        raise AssertionError('Unreviewed presentation-fast-path ledger content')
    entries = {item['filename']: item for item in ledger['updates']}
    if set(entries) != ALLOWED_PATHS or len(entries) != len(ledger['updates']):
        raise AssertionError('Incomplete presentation-fast-path path inventory')
    return entries


def apply_exact_edits(previous, edits):
    if type(previous) is not bytes or type(edits) is not list or not edits:
        raise AssertionError('Invalid presentation-fast-path edit input')
    cursor, previous_offset, chunks = 0, -1, []
    for edit in edits:
        if (type(edit) is not dict or set(edit) != {'offset', 'before', 'after'}
                or type(edit['offset']) is not int
                or edit['offset'] < cursor or edit['offset'] <= previous_offset
                or type(edit['before']) is not str or type(edit['after']) is not str
                or edit['before'] == edit['after']):
            raise AssertionError('Invalid presentation-fast-path exact edit')
        offset = edit['offset']
        before, after = edit['before'].encode('utf-8'), edit['after'].encode('utf-8')
        if offset > len(previous) or previous[offset:offset + len(before)] != before:
            raise AssertionError('Presentation-fast-path before image mismatch')
        chunks.extend((previous[cursor:offset], after))
        cursor, previous_offset = offset + len(before), offset
    return b''.join(chunks) + previous[cursor:]


def pre_presentation_fast_path_bytes(filename, current, *, ledger=None):
    if type(filename) is not str or filename not in ALLOWED_PATHS or type(current) is not bytes:
        raise AssertionError('Unknown presentation-fast-path file or input type')
    entries = validate_ledger(load_ledger() if ledger is None else ledger)
    entry = entries[filename]
    if digest(current) == entry['previous_sha256']:
        return current
    if filename == 'tests/material_bulk_preservation.py':
        current = pre_class_counts_bytes(filename, current)
    if digest(current) != entry['sha256']:
        raise AssertionError('Unreviewed presentation-fast-path successor bytes')
    chunks, cursor, shift = [], 0, 0
    for edit in entry['edits']:
        before, after = edit['before'].encode('utf-8'), edit['after'].encode('utf-8')
        offset = edit['offset'] + shift
        if offset < cursor or current[offset:offset + len(after)] != after:
            raise AssertionError('Presentation-fast-path after image mismatch')
        chunks.extend((current[cursor:offset], before))
        cursor = offset + len(after)
        shift += len(after) - len(before)
    previous = b''.join(chunks) + current[cursor:]
    if (digest(previous) != entry['previous_sha256']
            or apply_exact_edits(previous, entry['edits']) != current):
        raise AssertionError('Presentation-fast-path exact round trip failed')
    return previous
