"""Test-only exact reversal of the evidence-signature correction to a360bd1.

Only five reviewed successor files are accepted. Historical ledgers and pins
remain unchanged; production readers never import this preservation layer.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = 'a360bd15291f6e197f7b7f97eb8dd9063017f63d'
LEDGER_PATH = 'tests/fixtures/evidence_dedup_updates_v1.json'
LEDGER_SHA256 = '3c7ecc146f216e113a99c636815cce7df9b4c1ee06ec55a736cc781f16c77890'
LEDGER_CANONICAL_SHA256 = 'b332e33c57b0d3821e2bff8cbdc7ea4e6a3ce1551840d174420601366ebd7452'
ALLOWED_PATHS = frozenset({
    'materials_boundaries/material_references.py',
    'tests/test_material_reference_contract.py',
    'docs/MATERIAL_REFERENCE_CATALOG.md',
    'tests/material_bulk_preservation.py',
    'tests/test_material_bulk_preservation.py',
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
            raise AssertionError('Duplicate evidence-dedup ledger key')
        result[key] = value
    return result


def load_ledger():
    raw = (ROOT / LEDGER_PATH).read_bytes()
    if digest(raw) != LEDGER_SHA256:
        raise AssertionError('Unreviewed evidence-dedup ledger bytes')
    value = json.loads(raw, object_pairs_hook=unique_keys)
    validate_ledger(value)
    return value


def validate_ledger(ledger):
    if (type(ledger) is not dict
            or set(ledger) != {'schema_version', 'baseline_commit', 'updates'}
            or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
            or ledger['baseline_commit'] != BASELINE_COMMIT
            or type(ledger['updates']) is not list
            or digest(canonical(ledger)) != LEDGER_CANONICAL_SHA256):
        raise AssertionError('Unreviewed evidence-dedup ledger content')
    entries = {item['filename']: item for item in ledger['updates']}
    if set(entries) != ALLOWED_PATHS or len(entries) != len(ledger['updates']):
        raise AssertionError('Incomplete evidence-dedup path inventory')
    return entries


def apply_exact_edits(previous, edits):
    if type(previous) is not bytes or type(edits) is not list or not edits:
        raise AssertionError('Invalid evidence-dedup edit input')
    cursor, previous_offset, chunks = 0, -1, []
    for edit in edits:
        if (type(edit) is not dict or set(edit) != {'offset', 'before', 'after'}
                or type(edit['offset']) is not int
                or edit['offset'] < cursor or edit['offset'] <= previous_offset
                or type(edit['before']) is not str or type(edit['after']) is not str
                or edit['before'] == edit['after']):
            raise AssertionError('Invalid evidence-dedup exact edit')
        offset = edit['offset']
        before, after = edit['before'].encode('utf-8'), edit['after'].encode('utf-8')
        if offset > len(previous) or previous[offset:offset + len(before)] != before:
            raise AssertionError('Evidence-dedup before image mismatch')
        chunks.extend((previous[cursor:offset], after))
        cursor, previous_offset = offset + len(before), offset
    return b''.join(chunks) + previous[cursor:]


def pre_evidence_dedup_bytes(filename, current, *, ledger=None):
    if type(filename) is not str or filename not in ALLOWED_PATHS or type(current) is not bytes:
        raise AssertionError('Unknown evidence-dedup file or input type')
    entries = validate_ledger(load_ledger() if ledger is None else ledger)
    entry = entries[filename]
    if digest(current) == entry['previous_sha256']:
        return current
    if digest(current) != entry['sha256']:
        raise AssertionError('Unreviewed evidence-dedup successor bytes')
    chunks, cursor, shift = [], 0, 0
    for edit in entry['edits']:
        before, after = edit['before'].encode('utf-8'), edit['after'].encode('utf-8')
        offset = edit['offset'] + shift
        if offset < cursor or current[offset:offset + len(after)] != after:
            raise AssertionError('Evidence-dedup after image mismatch')
        chunks.extend((current[cursor:offset], before))
        cursor = offset + len(after)
        shift += len(after) - len(before)
    previous = b''.join(chunks) + current[cursor:]
    if (digest(previous) != entry['previous_sha256']
            or apply_exact_edits(previous, entry['edits']) != current):
        raise AssertionError('Evidence-dedup exact round trip failed')
    return previous
