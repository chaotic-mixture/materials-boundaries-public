"""Exact test-only recovery of the dated README/CI change to a592c89.

This finite bridge precedes the existing presentation and material layers.
No historical ledger or pin is replaced. The dated class sentence describes
one hash-bound data snapshot; only the existing marked totals remain dynamic
when older tests construct independent append rehearsals.
"""
import hashlib
import json
from pathlib import Path

from evidence_dedup_preservation import apply_exact_edits


ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = 'a592c89ede0dcced22579e56fc68b6fab4c55f49'
DATA_COMMIT = '5396fd1cc9df72507785a112a21c2990fb4a7c50'
LEDGER_PATH = 'tests/fixtures/material_class_counts_updates_20261019.json'
LEDGER_SHA256 = '6903abbfe027266b2e8f3ea90261600fd72982390c2431e836861b92a17fd894'
LEDGER_CANONICAL_SHA256 = '33d1fab253949a36dd6b3adfb82a252c6e38791a93ba496aa7093992e50cecc6'
ALLOWED_PATHS = frozenset({
    'README.md', '.github/workflows/ci.yml',
    'tests/material_bulk_preservation.py',
    'tests/presentation_fast_path_preservation.py',
    'tests/test_presentation_fast_path_preservation.py',
})
HISTORICAL_CLASS_SENTENCE = (
    'Natural coverage is 1,010; metal 14, inorganic 16, polymer 14 and composite 3 '
    'remain below the 1,000-per-class goal.'
)
SNAPSHOT_CLASS_SENTENCE = (
    'The 2026-10-19 experimental core snapshot (data commit '
    '`5396fd1cc9df72507785a112a21c2990fb4a7c50`) has natural 1,010; '
    'metal 22, inorganic 26, polymer 15 and composite 10. '
    'Only natural reaches the 1,000-per-class goal in this snapshot.'
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError('Duplicate class-count preservation key')
        result[key] = value
    return result


def validate_ledger(ledger):
    if (type(ledger) is not dict or set(ledger) != {
            'schema_version', 'baseline_commit', 'snapshot',
            'historical_readme_sha256', 'preserved_ledger_sha256', 'updates'}
            or type(ledger['schema_version']) is not int or ledger['schema_version'] != 1
            or ledger['baseline_commit'] != BASELINE_COMMIT):
        raise AssertionError('Invalid class-count preservation ledger')
    try:
        content_digest = digest(canonical(ledger))
    except (TypeError, ValueError) as exc:
        raise AssertionError('Invalid class-count preservation content') from exc
    if content_digest != LEDGER_CANONICAL_SHA256:
        raise AssertionError('Unreviewed class-count preservation content')
    entries = {item['filename']: item for item in ledger['updates']}
    if set(entries) != ALLOWED_PATHS or len(entries) != len(ledger['updates']):
        raise AssertionError('Incomplete class-count path inventory')
    return entries


def load_ledger():
    raw = (ROOT / LEDGER_PATH).read_bytes()
    if digest(raw) != LEDGER_SHA256:
        raise AssertionError('Unreviewed class-count preservation ledger bytes')
    value = json.loads(raw, object_pairs_hook=unique_keys)
    validate_ledger(value)
    return value


def pre_class_counts_bytes(filename, current, *, ledger=None):
    """Reverse only enumerated whole-byte successors, with exact round trips."""
    if type(filename) is not str or filename not in ALLOWED_PATHS or type(current) is not bytes:
        raise AssertionError('Unknown class-count preservation path or input type')
    entries = validate_ledger(load_ledger() if ledger is None else ledger)
    entry = entries[filename]
    if digest(current) == entry['previous_sha256']:
        return current
    if digest(current) != entry['sha256']:
        raise AssertionError('Unreviewed class-count successor bytes')
    chunks, cursor, shift = [], 0, 0
    for edit in entry['edits']:
        before, after = edit['before'].encode('utf-8'), edit['after'].encode('utf-8')
        offset = edit['offset'] + shift
        if offset < cursor or current[offset:offset + len(after)] != after:
            raise AssertionError('Class-count after image mismatch')
        chunks.extend((current[cursor:offset], before))
        cursor = offset + len(after)
        shift += len(after) - len(before)
    previous = b''.join(chunks) + current[cursor:]
    if (digest(previous) != entry['previous_sha256']
            or apply_exact_edits(previous, entry['edits']) != current):
        raise AssertionError('Class-count exact round trip failed')
    return previous


def normalize_readme_snapshot(raw):
    """Restore one fixed dated statement; never accept arbitrary class counts.

    Historical statements are accepted only in complete byte-pinned README
    images. Other README prose is still checked by the original release hash.
    Dynamic totals are verified later against the caller's actual graph.
    """
    if type(raw) is not bytes:
        raise AssertionError('README snapshot input must be bytes')
    text = raw.decode('utf-8')
    if text.count(SNAPSHOT_CLASS_SENTENCE) == 1 and HISTORICAL_CLASS_SENTENCE not in text:
        return text.replace(SNAPSHOT_CLASS_SENTENCE, HISTORICAL_CLASS_SENTENCE, 1)
    if (text.count(HISTORICAL_CLASS_SENTENCE) == 1
            and digest(raw) in load_ledger()['historical_readme_sha256']):
        return text
    raise AssertionError('Only the exact dated core snapshot or a pinned historical README is accepted')
