"""Recover a pinned predecessor from a complete immutable append packet.

This test-only bridge uses one finite ledger, exact candidate objects and exact
whole-catalog hashes. It neither authorizes new records nor accepts arbitrary
append data. Historical release pins remain in their original test layers.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from evidence_dedup_preservation import apply_exact_edits
from source_family_growth_preservation import (
    project_growth_catalogs, project_growth_catalog_bytes, project_growth_file,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "12cb89ca82b48ba444bdb921674c3d232d448720"
LEDGER_PATH = "tests/fixtures/evidence_batch_data_updates_20261019.json"
LEDGER_SHA256 = "1abccc91ab7bf6a068fd86e042a30892a45977acf52b2b76aabc2e465efdf12b"
FILES = {"materials": "materials.json", "properties": "reference_properties.json", "sources": "sources.json"}
TABLES = {"identities": ("materials", "identities"), "grades": ("materials", "grades"),
          "states": ("materials", "records"), "properties": ("properties", "records"),
          "sources": ("sources", "records")}


def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def digest(raw):
    return sha256(raw).hexdigest()


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError("Duplicate evidence-batch JSON key")
        result[key] = value
    return result


def load_ledger():
    raw = (ROOT / LEDGER_PATH).read_bytes()
    if not LEDGER_SHA256 or digest(raw) != LEDGER_SHA256:
        raise AssertionError("Unreviewed evidence-batch data ledger")
    ledger = json.loads(raw, object_pairs_hook=unique_keys)
    if (set(ledger) != {"schema_version", "baseline_commit", "baseline_sha256", "current_sha256", "packets", "readme"}
            or type(ledger["schema_version"]) is not int or ledger["schema_version"] != 1
            or ledger["baseline_commit"] != BASELINE_COMMIT
            or set(ledger["baseline_sha256"]) != set(FILES)
            or set(ledger["current_sha256"]) != set(FILES)):
        raise AssertionError("Invalid evidence-batch data ledger")
    return ledger


def appended_rows(ledger=None):
    """Read only hash-pinned packets and their finite integration-added IDs."""
    ledger = load_ledger() if ledger is None else ledger
    result = {key: [] for key in TABLES}
    for descriptor in ledger["packets"]:
        raw = (ROOT / descriptor["path"]).read_bytes()
        if digest(raw) != descriptor["sha256"]:
            raise AssertionError("Unreviewed evidence-batch packet bytes")
        packet = json.loads(raw, object_pairs_hook=unique_keys)
        for name, (table, field) in TABLES.items():
            ids = descriptor["added_ids"][name]
            rows = [row for row in packet["catalogs"][table][field] if row["id"] in ids]
            if len(rows) != len(ids) or {row["id"] for row in rows} != set(ids):
                raise AssertionError("Incomplete packet addition inventory")
            result[name].extend(deepcopy(rows))
    return result


def has_evidence_batch(current):
    rows = appended_rows()
    return any(any(row.get("id") in {item["id"] for item in rows[name]}
                   for row in current[table][field])
               for name, (table, field) in TABLES.items())


def recover_pre_evidence_batch_catalogs(current):
    """Accept exact predecessor or exactly the complete reviewed append only."""
    current = project_growth_catalogs(current)
    ledger = load_ledger()
    if type(current) is not dict or set(current) != set(FILES):
        raise AssertionError("Incomplete evidence-batch graph")
    actual = {name: digest(serialized(current[name])) for name in FILES}
    if actual == ledger["baseline_sha256"]:
        return deepcopy(current)
    rows = appended_rows(ledger)
    recovered = deepcopy(current)
    for name, (table, field) in TABLES.items():
        expected = {row["id"]: row for row in rows[name]}
        selected = [row for row in current[table][field] if row.get("id") in expected]
        if (len(selected) != len(expected) or {row["id"] for row in selected} != set(expected)
                or any(serialized(row) != serialized(expected[row["id"]]) for row in selected)):
            raise AssertionError("Evidence-batch recovery requires every complete pinned addition")
        recovered[table][field] = [row for row in recovered[table][field] if row.get("id") not in expected]
    if {name: digest(serialized(recovered[name])) for name in FILES} != ledger["baseline_sha256"]:
        raise AssertionError("Evidence-batch predecessor catalog bytes changed")
    if actual != ledger["current_sha256"]:
        raise AssertionError("Unreviewed evidence-batch successor catalog order or bytes")
    return recovered


def pre_evidence_batch_catalog_bytes(filename, raw):
    if filename not in FILES.values() or type(raw) is not bytes:
        raise AssertionError("Unknown evidence-batch catalog path or input type")
    raw = project_growth_catalog_bytes(filename, raw)
    ledger = load_ledger()
    name = next(key for key, value in FILES.items() if value == filename)
    if digest(raw) == ledger["baseline_sha256"][name]:
        return raw
    if digest(raw) != ledger["current_sha256"][name]:
        raise AssertionError("Unreviewed evidence-batch catalog bytes")
    graph = {key: json.loads((ROOT / "materials_boundaries/data" / path).read_bytes(), object_pairs_hook=unique_keys)
             for key, path in FILES.items()}
    graph = project_growth_catalogs(graph)
    graph[name] = json.loads(raw, object_pairs_hook=unique_keys)
    return serialized(recover_pre_evidence_batch_catalogs(graph)[name])


def pre_evidence_batch_readme_bytes(raw):
    if type(raw) is not bytes:
        raise AssertionError("Evidence-batch README input must be bytes")
    raw = project_growth_file("README.md", raw)
    entry = load_ledger()["readme"]
    if digest(raw) == entry["previous_sha256"]:
        return raw
    if digest(raw) != entry["sha256"]:
        raise AssertionError("Unreviewed evidence-batch README bytes")
    reverse, shift = [], 0
    for edit in entry["edits"]:
        reverse.append({"offset": edit["offset"] + shift, "before": edit["after"], "after": edit["before"]})
        shift += len(edit["after"].encode("utf-8")) - len(edit["before"].encode("utf-8"))
    previous = apply_exact_edits(raw, reverse)
    if digest(previous) != entry["previous_sha256"] or apply_exact_edits(previous, entry["edits"]) != raw:
        raise AssertionError("Evidence-batch README exact recovery failed")
    return previous
