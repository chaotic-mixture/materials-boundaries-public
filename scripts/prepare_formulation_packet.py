#!/usr/bin/env python3
"""Compile explicit source-family facts into one immutable review-only packet.

This checkout tool expands authored context; it does not infer identity,
chemistry, units, conditions, grades, rights or scientific approval.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from materials_boundaries.bulk_ingestion import canonical_json_bytes
from materials_boundaries.material_references import merge_material_catalogs, validate_material_catalog
from scripts.integrate_material_candidates import (
    FILES, PIN_KEYS, counts, difference, digest, nonempty_text, object_keys,
    read_document, require, write_immutable_package,
)

SPEC_KEYS = {"schema", "batch_id", "baseline_sha256", "source_records", "contexts",
             "formulations", "identity_crosswalk", "review"}
PACKET_KEYS = {"schema", "spec_sha256", "input", "catalogs", "review", "report"}
KINDS = ("identity", "grade", "state", "property")


def record_sha256(value):
    """Hash canonical JSON, not an original research document's bytes."""
    return sha256(canonical_json_bytes(value)).hexdigest()


def array(value, label, *, nonempty=False):
    require(isinstance(value, list) and (bool(value) or not nonempty), label + ": expected list")


def _combine(shared, fields, label):
    require(isinstance(shared, dict) and isinstance(fields, dict), label + ": expected objects")
    result = deepcopy(shared)
    for key, value in fields.items():
        if key not in result:
            result[key] = deepcopy(value)
        else:
            require(isinstance(result[key], dict) and isinstance(value, dict),
                    label + ": context field cannot be overwritten: " + key)
            result[key] = _combine(result[key], value, label + "." + key)
    return result


def _expand(reference, kind, contexts):
    object_keys(reference, {"context", "fields"}, kind + " reference")
    nonempty_text(reference["context"], kind + " context")
    require(reference["context"] in contexts[kind], "unknown " + kind + " context")
    return _combine(contexts[kind][reference["context"]], reference["fields"], kind)


def _catalogs(spec, baseline):
    contexts = spec["contexts"]
    object_keys(contexts, KINDS, "contexts")
    for kind in KINDS:
        require(isinstance(contexts[kind], dict), kind + " contexts must be an object")
        for name, fields in contexts[kind].items():
            nonempty_text(name, "context name")
            require(isinstance(fields, dict), "context fields must be an object")
    array(spec["formulations"], "formulations", nonempty=True)
    materials = {"schema_version": "1.0.0", "identities": [], "grades": [], "records": []}
    properties = {"schema_version": "1.0.0", "records": []}
    for row in spec["formulations"]:
        object_keys(row, {"identity", "grades", "states"}, "formulation")
        identity = _expand(row["identity"], "identity", contexts)
        require(identity.get("category") in {"polymer", "composite"}, "formulation must be polymer or composite")
        materials["identities"].append(identity)
        array(row["grades"], "grades")
        for item in row["grades"]:
            grade = _expand(item, "grade", contexts)
            require(grade.get("identity_id") == identity.get("id"), "grade identity link differs from its formulation")
            materials["grades"].append(grade)
        array(row["states"], "states", nonempty=True)
        for item in row["states"]:
            object_keys(item, {"record", "properties"}, "state row")
            state = _expand(item["record"], "state", contexts)
            require(state.get("identity_id") == identity.get("id"), "state identity link differs from its formulation")
            materials["records"].append(state)
            array(item["properties"], "properties", nonempty=True)
            state_properties = []
            for reference in item["properties"]:
                prop = _expand(reference, "property", contexts)
                require(prop.get("material_state_id") == state.get("id"), "property state link differs from its state")
                properties["records"].append(prop)
                state_properties.append(prop.get("id"))
            require(isinstance(state.get("property_ids"), list)
                    and sorted(state["property_ids"]) == sorted(state_properties),
                    "state property_ids must name exactly its supplied properties")
    array(spec["source_records"], "source_records", nonempty=True)
    sources = {"schema_version": "1.0.0", "records": []}
    existing = {source["id"]: source for source in baseline["sources"]["records"]}
    for entry in spec["source_records"]:
        object_keys(entry, {"record", "sha256"}, "source record descriptor")
        digest(entry["sha256"], "source record SHA-256")
        require(record_sha256(entry["record"]) == entry["sha256"], "source record hash mismatch")
        source = entry["record"]
        require(isinstance(source, dict), "source record must be an object")
        if source.get("id") in existing:
            require(source == existing[source["id"]], "existing source record cannot be rewritten")
        sources["records"].append(deepcopy(source))
    result = {"materials": materials, "properties": properties, "sources": sources}
    validate_material_catalog(materials, properties, sources)
    return result


def _labels(record):
    # Conservative textual collisions are not chemical-equivalence decisions.
    values = [record.get("name"), record.get("source_designation"), record.get("designation")]
    values.extend(record.get("names", {}).values())
    values.extend(alias["text"] for alias in record.get("aliases", []))
    return {value.strip().casefold() for value in values if isinstance(value, str) and value.strip()}


def _source_owners(graph):
    properties = {row["id"]: row for row in graph["properties"]["records"]}
    pairs = {}
    for state in graph["materials"]["records"]:
        sources = {properties[key]["source_id"] for key in state["property_ids"]}
        for source in sources:
            pairs.setdefault((state["identity_id"], source), []).append(state)
    return pairs


def validate_identity_collisions(baseline, catalogs):
    """Refuse source-scoped textual collisions, including between packet batches."""
    # Build from validated live source/state/property links, not a supplied
    # baseline crosswalk that could omit a known designation or alias.
    seen = {}
    for graph in (baseline, catalogs):
        graph_ids = {row["id"]: row for row in graph["materials"]["identities"]}
        label_groups = []
        for (identity_id, source_id), states in _source_owners(graph).items():
            labels = _labels(graph_ids[identity_id])
            for state in states:
                labels.update(_labels(state))
            label_groups.append((identity_id, source_id, labels))
        grades = {row["id"]: row for row in graph["materials"]["grades"]}
        for state in graph["materials"]["records"]:
            if state["grade_id"] is None:
                continue
            grade = grades[state["grade_id"]]
            # A grade can be evidenced by a supplier source distinct from the
            # property's primary paper. Index only its actual grade evidence,
            # never assign a supplier label to an unrelated measurement source.
            grade_sources = {entry["source_id"] for entry in grade["evidence"] if "grade" in entry["supports"]}
            for source_id in grade_sources:
                label_groups.append((state["identity_id"], source_id, _labels(grade)))
        for identity_id, source_id, labels in label_groups:
            for label in labels:
                key = (source_id, label)
                if graph is catalogs:
                    require(not (seen.get(key, set()) - {identity_id}),
                            "source designation/name/alias collides with another identity: " + label)
                seen.setdefault(key, set()).add(identity_id)


def _identity_checks(spec, baseline, catalogs):
    identities = {row["id"]: row for row in catalogs["materials"]["identities"]}
    old_ids = {row["id"] for row in baseline["materials"]["identities"]}
    sources = {row["id"]: row for row in catalogs["sources"]["records"]}
    owners = _source_owners(catalogs)
    validate_identity_collisions(baseline, catalogs)
    array(spec["identity_crosswalk"], "identity_crosswalk")
    checked = {}
    for row in spec["identity_crosswalk"]:
        object_keys(row, {"identity_id", "source_id", "source_designations", "disposition", "evidence", "note"},
                    "identity crosswalk")
        for key in ("identity_id", "source_id", "disposition", "note"):
            nonempty_text(row[key], "crosswalk " + key)
        pair = (row["identity_id"], row["source_id"])
        require(pair in owners and pair not in checked, "unknown or duplicate crosswalk identity/source pair")
        array(row["source_designations"], "crosswalk designations", nonempty=True)
        for code in row["source_designations"]:
            nonempty_text(code, "crosswalk designation")
        expected = {state["source_designation"] for state in owners[pair]}
        require(len(set(row["source_designations"])) == len(row["source_designations"])
                and set(row["source_designations"]) == expected,
                "crosswalk must cover exactly the linked source designations")
        require(row["disposition"] in {"existing", "distinct", "pending"}, "unknown identity disposition")
        if row["disposition"] == "existing":
            require(pair[0] in old_ids, "existing crosswalk identity is absent from pinned baseline")
        if row["disposition"] == "distinct":
            require(pair[0] not in old_ids, "distinct crosswalk identity already exists in pinned baseline")
        array(row["evidence"], "crosswalk evidence", nonempty=True)
        for evidence in row["evidence"]:
            object_keys(evidence, {"source_id", "url", "locator", "supports"}, "crosswalk evidence")
            require(evidence["source_id"] == pair[1] and evidence["url"] in sources[pair[1]]["urls"],
                    "crosswalk evidence source or URL is not registered")
            nonempty_text(evidence["locator"], "crosswalk locator")
            array(evidence["supports"], "crosswalk supports", nonempty=True)
            require("material_identity" in evidence["supports"], "crosswalk must evidence material identity")
        require(any(e["source_id"] == pair[1] and "material_identity" in e["supports"]
                    for e in identities[pair[0]]["evidence"]), "crosswalk source lacks identity evidence")
        for state in owners[pair]:
            require(any(e["source_id"] == pair[1] and "state" in e["supports"] for e in state["evidence"]),
                    "crosswalk source lacks linked state evidence")
        checked[pair] = deepcopy(row)
    pending, report = [], []
    for pair in sorted(owners):
        if pair not in checked:
            report.append({"identity_id": pair[0], "source_id": pair[1], "disposition": "pending"})
            pending.append("Missing identity crosswalk: " + " / ".join(pair))
        else:
            report.append(checked[pair])
            if checked[pair]["disposition"] == "pending":
                pending.append("Pending identity review: " + " / ".join(pair))
    return report, pending


def _review_checks(review, sources):
    require(isinstance(review, dict), "review must be an object")
    require({"verification", "formal_admitted_delta", "source_reviews"} <= set(review), "missing review boundary fields")
    verification = review["verification"]
    require(isinstance(verification, dict)
            and verification.get("independent_scientific_review") is False
            and verification.get("raw_data_reanalysis") is False, "compiler cannot upgrade scientific review or raw-data reanalysis")
    require(type(review["formal_admitted_delta"]) is int and review["formal_admitted_delta"] == 0,
            "prepared packets admit zero formal materials")
    array(review["source_reviews"], "source_reviews")
    source_ids = {row["id"] for row in sources["records"]}
    reviewed = {}
    for row in review["source_reviews"]:
        object_keys(row, {"source_id", "status", "note"}, "source review")
        require(row["source_id"] in source_ids and row["source_id"] not in reviewed, "unknown or duplicate source review")
        require(row["status"] in {"selected_facts_checked", "pending"}, "unknown source review status")
        nonempty_text(row["note"], "source review note")
        reviewed[row["source_id"]] = row["status"]
    pending = []
    for source in sources["records"]:
        license = source.get("license")
        if (not isinstance(license, dict) or license.get("status") != "explicit_reuse_license_verified"
                or not isinstance(license.get("identifier"), str) or not license["identifier"].strip()):
            pending.append("Source-specific rights remain pending: " + source["id"])
        if reviewed.get(source["id"]) != "selected_facts_checked":
            pending.append("Selected-source transcription/rights scope remains pending: " + source["id"])
    return pending


def compile_spec(spec, baseline_dir):
    """Validate and expand an explicit spec; return detached deterministic data."""
    object_keys(spec, SPEC_KEYS, "spec")
    require(spec["schema"] == "formulation-packet-spec/1", "unsupported formulation spec schema")
    nonempty_text(spec["batch_id"], "batch_id")
    spec_hash = record_sha256(spec)
    object_keys(spec["baseline_sha256"], set(PIN_KEYS.values()), "baseline_sha256")
    baseline = {key: read_document(Path(baseline_dir) / filename, spec["baseline_sha256"][PIN_KEYS[key]])[0]
                for key, filename in FILES.items()}
    validate_material_catalog(baseline["materials"], baseline["properties"], baseline["sources"])
    catalogs = _catalogs(spec, baseline)
    crosswalk, pending = _identity_checks(spec, baseline, catalogs)
    pending.extend(_review_checks(spec["review"], catalogs["sources"]))
    merged = merge_material_catalogs(baseline["materials"], baseline["properties"], baseline["sources"], catalogs)
    before, after = counts(baseline), counts(merged)
    return {"schema": "formulation-prepared-packet/1", "spec_sha256": spec_hash,
            "input": deepcopy(spec), "catalogs": catalogs, "review": deepcopy(spec["review"]),
            "report": {"baseline_sha256": deepcopy(spec["baseline_sha256"]),
                       "before": before, "after": after, "delta": difference(after, before),
                       "formal_admitted_delta": 0, "handoff_ready": not pending,
                       "pending_gates": pending, "identity_crosswalk": crosswalk}}


def build_packet(baseline_dir, spec_path):
    spec, _ = read_document(spec_path)
    return compile_spec(spec, baseline_dir)


def validate_prepared_packet(packet, baseline_dir):
    """Replay every field; a forged ready flag or hash is not an approval."""
    object_keys(packet, PACKET_KEYS, "prepared packet")
    require(packet["schema"] == "formulation-prepared-packet/1", "unsupported prepared packet schema")
    digest(packet["spec_sha256"], "spec SHA-256")
    replay = compile_spec(packet["input"], baseline_dir)
    require(canonical_json_bytes(packet) == canonical_json_bytes(replay), "prepared packet differs from exact replay")
    return replay


def write_packet(baseline_dir, spec_path, output, *, repository_root=ROOT):
    output = Path(output).absolute()
    resolved = output.resolve()
    require(resolved != Path(spec_path).resolve(), "output must differ from spec")
    require(not resolved.is_relative_to(Path(baseline_dir).resolve()), "output must be outside baseline")
    repository_root = Path(repository_root).resolve()
    for relative in ("materials_boundaries/data", "formal-catalog/materials_project_catalog/data"):
        require(not resolved.is_relative_to(repository_root / relative), "output must not target runtime catalog data")
    packet = build_packet(baseline_dir, spec_path)
    return packet, write_immutable_package(output, packet)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="single new immutable candidate JSON artifact")
    args = parser.parse_args(argv)
    try:
        packet, created = write_packet(args.baseline_dir, args.spec, args.output)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f"formulation preparation failed: {exc}\n")
    print(("Created" if created else "Unchanged") + " review-only formulation packet: " + str(args.output))
    print("Candidate identity delta: " + str(packet["report"]["delta"]["identities"]))
    print("Handoff ready: " + ("yes" if packet["report"]["handoff_ready"] else "no; identity/source review pending"))
    print("Formal admitted delta: 0. Source transcription is not scientific approval; runtime catalogs unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
