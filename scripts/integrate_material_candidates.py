#!/usr/bin/env python3
"""Build one immutable offline experimental catalog and incremental report.

An explicit, hash-bound local manifest selects previously reviewed packets. This
command does not discover candidates, approve science or rights, fetch assets,
modify runtime catalogs, or increase the released main admission count.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from materials_boundaries.material_references import (
    material_quota_coverage, merge_material_catalogs, validate_material_catalog,
)
from materials_boundaries.validation import (
    _reject_constant, _strict_float, _strict_int, _unique_pairs,
)

FILES = {"materials": "materials.json", "properties": "reference_properties.json",
         "sources": "sources.json"}
PIN_KEYS = {"materials": "materials", "properties": "reference_properties", "sources": "sources"}
TABLES = {"identities": ("materials", "identities"), "grades": ("materials", "grades"),
          "states": ("materials", "records"), "properties": ("properties", "records"),
          "sources": ("sources", "records")}
STATUS_FIELDS = {
    ("properties", "refprop_watanabe2026_niobium_cylinder_mass_density", "scope_note"),
    ("sources", "watanabe2026_niobium_thermophysical", "bundled_content"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def object_keys(value, keys, label):
    require(isinstance(value, dict) and set(value) == set(keys), label + ": unexpected or missing fields")


def nonempty_text(value, label):
    require(isinstance(value, str) and bool(value.strip()), label + ": expected nonempty text")


def digest(value, label):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            label + ": expected SHA-256")


def read_document(path, expected=None):
    """Parse exactly the bytes whose digest was checked, using strict JSON rules."""
    data = Path(path).read_bytes()
    actual = sha256(data).hexdigest()
    if expected is not None:
        digest(expected, str(Path(path).name))
        require(actual == expected, "input hash mismatch: " + Path(path).name)
    value = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_pairs,
                       parse_constant=_reject_constant, parse_float=_strict_float,
                       parse_int=_strict_int)
    require(isinstance(value, dict), "expected JSON object: " + Path(path).name)
    return value, actual


def packet_path(manifest_path, descriptor, repository_root):
    object_keys(descriptor, {"path", "sha256"}, "packet descriptor")
    nonempty_text(descriptor["path"], "packet path")
    relative = Path(descriptor["path"])
    require(not relative.is_absolute() and not relative.drive, "packet path must be relative")
    path = (manifest_path.parent / relative).resolve()
    packet_root = (repository_root / "experimental/material-batches").resolve()
    require(path.is_relative_to(packet_root) and path.suffix == ".json",
            "packet path must remain inside experimental/material-batches and name JSON")
    return path


def counts(graph):
    coverage = material_quota_coverage(graph["materials"], graph["properties"], graph["sources"])
    return {**{name: len(graph[table][field]) for name, (table, field) in TABLES.items()},
            "categories": {name: item["admitted_unique_identity_count"]
                           for name, item in coverage["classes"].items()}}


def difference(after, before):
    return {**{name: after[name] - before[name] for name in TABLES},
            "categories": {name: after["categories"][name] - before["categories"][name]
                           for name in before["categories"]}}


def write_immutable_package(path, package):
    """Publish atomically without sorting the source graphs' ordered JSON keys.

    Strictly parsed inputs and ordered merges make this encoding deterministic.
    Retaining key order also lets callers recover the exact pinned catalog bytes
    using the repository's indent-two/newline encoding, without duplicate copies.
    """
    path = Path(path)
    data = (json.dumps(package, ensure_ascii=False, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")
    if path.exists():
        if not path.is_symlink() and path.is_file() and path.read_bytes() == data:
            return False
        raise ValueError("output already exists with different content; select a new output path")
    if not path.parent.is_dir():
        raise ValueError("output parent directory does not exist")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".material-integration-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Exclusive hard-link publication cannot overwrite a competing writer.
        os.link(temporary, path)
    except FileExistsError as exc:
        raise ValueError("output appeared during write; no existing artifact was overwritten") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def apply_status_adjustments(packets, adjustments):
    require(isinstance(adjustments, list), "status_adjustments must be a list")
    seen = set()
    for adjustment in adjustments:
        object_keys(adjustment, {"batch_id", "table", "record_id", "field", "expected", "value", "reason"},
                    "status adjustment")
        key = (adjustment["table"], adjustment["record_id"], adjustment["field"])
        require(all(isinstance(value, str) for value in key), "status adjustment fields must be text")
        require(key in STATUS_FIELDS, "unsupported status adjustment; scientific fields cannot be changed")
        batch_id = adjustment["batch_id"]
        nonempty_text(batch_id, "adjustment batch_id")
        require(batch_id in packets, "unknown adjustment batch_id")
        marker = (batch_id, *key)
        require(marker not in seen, "duplicate status adjustment")
        seen.add(marker)
        for name in ("expected", "value", "reason"):
            nonempty_text(adjustment[name], "adjustment " + name)
        rows = [row for row in packets[batch_id][key[0]]["records"] if row["id"] == key[1]]
        require(len(rows) == 1, "status adjustment must select exactly one record")
        require(rows[0].get(key[2]) == adjustment["expected"], "status adjustment old value mismatch")
        rows[0][key[2]] = adjustment["value"]


def build_package(baseline_dir, manifest_path, *, repository_root=ROOT):
    """Validate all pinned inputs before merging; return a detached artifact."""
    baseline_dir = Path(baseline_dir).resolve()
    manifest_path = Path(manifest_path).resolve()
    repository_root = Path(repository_root).resolve()
    manifest, manifest_digest = read_document(manifest_path)
    object_keys(manifest, {"schema", "scope", "baseline_sha256", "batches", "status_adjustments",
                           "pending_gates", "released_main_count"}, "manifest")
    require(manifest["schema"] == "experimental-material-integration/1", "unsupported manifest schema")
    require(manifest["scope"] == "local-experimental-only", "only local experimental integration is supported")
    require(type(manifest["released_main_count"]) is int and manifest["released_main_count"] == 1081,
            "released main count must remain 1081")
    object_keys(manifest["baseline_sha256"], set(PIN_KEYS.values()), "baseline_sha256")
    require(isinstance(manifest["pending_gates"], list) and manifest["pending_gates"],
            "pending review gates must remain explicit")
    for gate in manifest["pending_gates"]:
        nonempty_text(gate, "pending gate")
    baseline = {name: read_document(baseline_dir / filename, manifest["baseline_sha256"][PIN_KEYS[name]])[0]
                for name, filename in FILES.items()}
    batches = manifest["batches"]
    require(isinstance(batches, list) and batches, "batches must be a nonempty list")
    packets = {}
    for batch in batches:
        object_keys(batch, {"id", "candidate_commit", "materials", "properties", "sources", "review"}, "batch")
        nonempty_text(batch["id"], "batch id")
        require(batch["id"] not in packets, "duplicate batch id")
        require(isinstance(batch["candidate_commit"], str)
                and re.fullmatch(r"[0-9a-f]{40}", batch["candidate_commit"]) is not None,
                "candidate_commit must be a full commit ID")
        packet = {}
        for name in ("materials", "properties", "sources", "review"):
            path = packet_path(manifest_path, batch[name], repository_root)
            require(path != manifest_path and not path.is_relative_to(baseline_dir),
                    "candidate inputs must be separate from manifest and baseline")
            packet[name] = read_document(path, batch[name]["sha256"])[0]
        packets[batch["id"]] = packet
    # All original files have now been read and hash-verified. Adjustments modify
    # only two explicit editorial status fields, never the frozen packet bytes.
    apply_status_adjustments(packets, manifest["status_adjustments"])
    validate_material_catalog(baseline["materials"], baseline["properties"], baseline["sources"])
    before = counts(baseline)
    current = baseline
    reports = []
    for batch in batches:
        append = {name: packets[batch["id"]][name] for name in FILES}
        previous = current
        current = merge_material_catalogs(previous["materials"], previous["properties"], previous["sources"], append)
        added, existing = {}, {}
        for name, (table, field) in TABLES.items():
            old_ids = {row["id"] for row in previous[table][field]}
            new_ids = {row["id"] for row in append[table][field]}
            added[name], existing[name] = sorted(new_ids - old_ids), sorted(new_ids & old_ids)
        reports.append({"id": batch["id"], "candidate_commit": batch["candidate_commit"],
                        "inputs": {name: deepcopy(batch[name]) for name in (*FILES, "review")},
                        "added_ids": added, "existing_ids": existing,
                        "added_counts": {name: len(ids) for name, ids in added.items()},
                        "existing_counts": {name: len(ids) for name, ids in existing.items()},
                        "source_ids": sorted({row["source_id"] for row in append["properties"]["records"]})})
    after = counts(current)
    return {"schema": "experimental-material-integration-package/1", "scope": manifest["scope"],
            "status": "experimental_only_formal_admission_pending", "manifest_sha256": manifest_digest,
            "catalogs": current,
            "report": {"released_main_count": manifest["released_main_count"], "formal_admitted_delta": 0,
                       "baseline_sha256": deepcopy(manifest["baseline_sha256"]),
                       "before": before, "after": after, "delta": difference(after, before),
                       "batches": reports, "status_adjustments": deepcopy(manifest["status_adjustments"]),
                       "pending_gates": deepcopy(manifest["pending_gates"])}}


def write_package(baseline_dir, manifest_path, output, *, repository_root=ROOT):
    """Write a single immutable artifact only after all input validation succeeds."""
    output = Path(output).absolute()
    resolved_output = output.resolve()
    baseline_dir = Path(baseline_dir).resolve()
    repository_root = Path(repository_root).resolve()
    require(not resolved_output.is_relative_to(baseline_dir), "output must be outside the baseline directory")
    require(not resolved_output.is_relative_to(repository_root / "materials_boundaries/data"),
            "output must not target runtime catalog data")
    require(not resolved_output.is_relative_to(repository_root / "formal-catalog/materials_project_catalog/data"),
            "output must not target formal catalog data")
    require(resolved_output != Path(manifest_path).resolve(), "output must differ from manifest")
    package = build_package(baseline_dir, manifest_path, repository_root=repository_root)
    for batch in package["report"]["batches"]:
        for descriptor in batch["inputs"].values():
            path = packet_path(Path(manifest_path).resolve(), descriptor, repository_root)
            require(resolved_output != path, "output must differ from candidate input")
    return package, write_immutable_package(output, package)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, required=True, help="directory containing the three pinned catalog JSON files")
    parser.add_argument("--manifest", type=Path, required=True, help="explicit hash-bound local experimental integration manifest")
    parser.add_argument("--output", type=Path, required=True, help="new immutable combined catalog/report JSON file")
    args = parser.parse_args(argv)
    try:
        package, created = write_package(args.baseline_dir, args.manifest, args.output)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f"experimental integration failed: {exc}\n")
    print(("Created" if created else "Unchanged") + " experimental integration artifact: " + str(args.output))
    print("Recorded baseline-to-candidate identity delta: " + str(package["report"]["delta"]["identities"]))
    print("New artifact written: " + ("yes" if created else "no"))
    print("Released main remains 1081; local integration does not publish this artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
