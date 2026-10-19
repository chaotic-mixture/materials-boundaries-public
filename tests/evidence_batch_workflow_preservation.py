"""Finite test-only recovery of this experiment's workflow to 12cb89c.

The original class-count ledger and all older ledgers retain their bytes and
pins. This layer also recovers its two explicitly changed call sites, without
accepting arbitrary future workflow or test edits.
"""
import hashlib
import json
from pathlib import Path

from evidence_dedup_preservation import apply_exact_edits


ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "12cb89ca82b48ba444bdb921674c3d232d448720"
LEDGER_PATH = "tests/fixtures/evidence_batch_workflow_updates_20261019.json"
LEDGER_SHA256 = '9081f59d7c2b5f5ab60fef3b3f0837daf10b0e3d191c5320fe323e400fd14a11'
LEDGER_CANONICAL_SHA256 = 'c96586574644e56d031a606c6a582e153732cc91f651b7c2cb1760ea1e494804'
ALLOWED_PATHS = frozenset({
    ".github/workflows/ci.yml",
    "tests/material_class_counts_preservation.py",
    "tests/test_material_class_counts_preservation.py",
})


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError("Duplicate evidence-batch preservation key")
        result[key] = value
    return result


def validate_ledger(ledger):
    if (type(ledger) is not dict or set(ledger) != {
            "schema_version", "baseline_commit", "preserved_ledger_sha256", "updates"}
            or type(ledger["schema_version"]) is not int or ledger["schema_version"] != 1
            or ledger["baseline_commit"] != BASELINE_COMMIT):
        raise AssertionError("Invalid evidence-batch workflow ledger")
    try:
        content_digest = digest(canonical(ledger))
    except (TypeError, ValueError) as exc:
        raise AssertionError("Invalid evidence-batch workflow content") from exc
    if content_digest != LEDGER_CANONICAL_SHA256:
        raise AssertionError("Unreviewed evidence-batch workflow content")
    entries = {entry["filename"]: entry for entry in ledger["updates"]}
    if set(entries) != ALLOWED_PATHS or len(entries) != len(ledger["updates"]):
        raise AssertionError("Incomplete evidence-batch workflow path inventory")
    return entries


def load_ledger():
    raw = (ROOT / LEDGER_PATH).read_bytes()
    if digest(raw) != LEDGER_SHA256:
        raise AssertionError("Unreviewed evidence-batch workflow ledger bytes")
    value = json.loads(raw, object_pairs_hook=unique_keys)
    validate_ledger(value)
    return value


def pre_evidence_batch_workflow_bytes(filename, raw, *, ledger=None):
    """Restore only the pinned 12cb89c predecessor; reject all other bytes."""
    if type(filename) is not str or filename not in ALLOWED_PATHS or type(raw) is not bytes:
        raise AssertionError("Unknown evidence-batch workflow path or input type")
    entries = validate_ledger(load_ledger() if ledger is None else ledger)
    entry = entries[filename]
    if digest(raw) == entry["previous_sha256"]:
        return raw
    if digest(raw) != entry["sha256"]:
        raise AssertionError("Unreviewed evidence-batch workflow successor")
    chunks, cursor, shift = [], 0, 0
    for edit in entry["edits"]:
        before, after = edit["before"].encode("utf-8"), edit["after"].encode("utf-8")
        offset = edit["offset"] + shift
        if offset < cursor or raw[offset:offset + len(after)] != after:
            raise AssertionError("Evidence-batch workflow after image mismatch")
        chunks.extend((raw[cursor:offset], before))
        cursor = offset + len(after)
        shift += len(after) - len(before)
    previous = b"".join(chunks) + raw[cursor:]
    if (digest(previous) != entry["previous_sha256"]
            or apply_exact_edits(previous, entry["edits"]) != raw):
        raise AssertionError("Evidence-batch workflow exact round trip failed")
    return previous
