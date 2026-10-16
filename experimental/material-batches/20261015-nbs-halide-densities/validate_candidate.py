"""Check an isolated four-halide candidate without writing catalog files.

These offline software checks are not scientific review, rights approval,
chemical-identity admission, or permission to publish. Generic catalog gates and
packet-specific checks against the supplied source-review handoff are reported
separately. This script neither opens source assets nor accesses the network.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

# Importing the package must not create __pycache__ inside the review checkout.
sys.dont_write_bytecode = True
import jsonschema


SOURCE_ID = "swanson_tatge_1953_nbs_circ539v1"
SOURCE_URL = "https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf"
SOURCE_SHA256 = "003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c"
EXPECTED_DENSITIES = {"kbr": "2.7533", "ki": "3.1257", "naf": "2.799", "baf2": "4.886"}
EXPECTED_TEMPERATURES = {"kbr": "25", "ki": "25", "naf": None, "baf2": "26"}
EXPECTED_BASELINE = {"identities": 1057, "grades": 20, "states": 1057, "properties": 1057, "sources": 114}
EXPECTED_DELTA = {"identities": 4, "grades": 0, "states": 4, "properties": 4, "sources": 0}
BASELINE_COMMIT = "4c5656cf6ba0ad1a54b736e0568e97abe4815c29"
BASELINE_BYTES = {
    "catalog/materials.json": "ffd27ae7a927494083cbdcb173847502283f9ff0f69b8b7321abe0b042824dc1",
    "catalog/reference_properties.json": "7430901a0f401aca384debb8706a124ac43ad6d043165beff1b8d186641fddef",
    "catalog/sources.json": "4240f52ef96bbe34a8a677e2f995296a6c72ac8ab14fc3f8978c043540fcef93",
    "schema/materials.schema.json": "b1bb12d436cd0580a1dbfddcb3854acbe233392950bee03d368094f3048255da",
    "schema/reference_properties.schema.json": "8ec45ae83b30d9ecc697d703aa1d903ef231ce0cd9123c23491694149edec268",
    "schema/sources.schema.json": "164016522283620c88831e36b7cd60abccf4203c1d9d3e2343054d3d0287abdf",
}
DOCUMENT_NAMES = ("nbs-materials.candidate.json", "nbs-reference-properties.candidate.json", "nbs-sources.reused.json")
SCHEMA_NAMES = ("materials", "reference_properties", "sources")


class CheckFailure(ValueError):
    """A positive check or expected-rejection check failed."""


def require(condition, message):
    """Use explicit exceptions so python -O does not disable validation."""
    if not condition:
        raise CheckFailure(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(value):
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def counts(graph):
    materials, properties, sources = graph
    return {"identities": len(materials["identities"]), "grades": len(materials["grades"]),
            "states": len(materials["records"]), "properties": len(properties["records"]),
            "sources": len(sources["records"])}


def graph_of(merged):
    return merged["materials"], merged["properties"], merged["sources"]


def by_formula(graph):
    """Resolve the four reviewed identities through graph links, never row order."""
    materials, properties, _ = graph
    expected_ids = {"mat_nbs1953_" + formula for formula in EXPECTED_DENSITIES}
    require({row["id"] for row in materials["identities"]} == expected_ids,
            "candidate identity IDs differ from this reviewed four-material scope")
    result = {}
    for formula in EXPECTED_DENSITIES:
        identity_id = "mat_nbs1953_" + formula
        identities = [row for row in materials["identities"] if row["id"] == identity_id]
        states = [row for row in materials["records"] if row["identity_id"] == identity_id]
        require(len(identities) == len(states) == 1, formula + ": expected one identity and one source-qualified state")
        selected_properties = [row for row in properties["records"] if row["material_state_id"] == states[0]["id"]]
        require(len(selected_properties) == 1, formula + ": expected one density reference")
        result[formula] = (identities[0], states[0], selected_properties[0])
    return result


def degrees_celsius(text):
    """Accept the packet's English spelling or the degree symbol, not 298 K inference."""
    normalized = re.sub(r"\s+", " ", text.strip()).casefold()
    match = re.fullmatch(r"([0-9]+)\s*(?:degrees?\s*c(?:elsius)?|\u00b0\s*c)", normalized)
    return match.group(1) if match else None


def check_source_facts(graph):
    """Check selected handoff facts, not general source truth or prose equivalence.
    """
    rows = by_formula(graph)
    require(counts(graph) == {"identities": 4, "grades": 0, "states": 4, "properties": 4, "sources": 1},
            "candidate graph counts differ from the reviewed scope")
    for formula, (identity, state, prop) in rows.items():
        require(identity["category"] == "inorganic", formula + ": category must remain inorganic")
        require(state["grade_id"] is None, formula + ": no qualified grade was supplied for admission")
        value = prop["reported_value"]
        require(value["kind"] == "scalar" and value["number"] == value["value_text"] == EXPECTED_DENSITIES[formula]
                and value["unit_code"] == "g/cm^3", formula + ": source density or precision changed")
        require(prop["quantity"] == "mass_density" and prop["quantity_dimension"] == "mass_per_volume",
                formula + ": density quantity changed")
        require(prop["evidence_kind"] == "published_measurement_derived_reference"
                and prop["determination_basis"] == "source_reports_calculation"
                and prop["density_basis"] == "crystallographic"
                and prop["method_definition"]["type"] == "source_reported_crystallographic_derivation",
                formula + ": source reports crystallographic derivation, not bulk measurement")
        require(prop["summary_statistic"] == "reported_value", formula + ": no source density mean established")
        require(prop["uncertainty"] is None and prop["uncertainty_status"] == "not_reported_in_inspected_source",
                formula + ": density uncertainty is unknown; lattice error is not a density envelope")
        require(prop["sample_count"]["value"] is None and prop["sample_count"]["relation"] == "not_reported",
                formula + ": independent specimen or density repeat count is unknown")
        temperature = prop["conditions"]["temperature"]
        expected_temperature = EXPECTED_TEMPERATURES[formula]
        if expected_temperature is None:
            require(temperature["status"] in {"not_reported_in_inspected_source", "not_verified"}
                    and temperature["text"] is None,
                    "naf: density temperature must remain unknown; lattice/pattern temperature cannot be copied")
        else:
            require(temperature["status"] == "reported" and degrees_celsius(temperature["text"]) == expected_temperature,
                    formula + ": source density reference temperature changed")
        doc = prop["source_document"]
        require(prop["source_id"] == SOURCE_ID and doc["url"] == SOURCE_URL
                and doc["sha256"] == SOURCE_SHA256 and doc["hash_status"] == "recorded"
                and doc["inspected_on"] == "2026-10-15",
                formula + ": inspected source identity or asset digest changed")
        require("four formula units per conventional cell" in prop["method_definition"]["definition"].casefold(),
                formula + ": the source's cell-content assumption must be retained")
        require(prop["evaluation_support"] == "catalog_only" and prop["universal_bound"] is False
                and prop["engineering_allowable"] is False
                and prop["verification"]["independent_scientific_review"] is False
                and prop["verification"]["raw_data_reanalysis"] is False,
                formula + ": candidate must not acquire scientific/admission claims")
        extras = {row["name"]: row["fact"] for row in prop["conditions"].get("additional_conditions", [])}
        pressure = extras.get("density_pressure", {})
        require(pressure.get("status") == "not_reported_in_inspected_source" and pressure.get("text") is None,
                formula + ": density pressure is unknown")
    naf_extras = {row["name"]: row["fact"] for row in rows["naf"][2]["conditions"]["additional_conditions"]}
    for name, value, context in (("lattice_reference_temperature", "25", "lattice"),
                                 ("xrd_pattern_temperature", "26", "powder pattern")):
        fact = naf_extras.get(name, {})
        text = fact.get("text") or ""
        require(fact.get("status") == "reported" and text.startswith(value + " degrees C")
                and context in text and "not" in text and "density" in text,
                "naf: lattice and pattern temperatures must remain separately scoped")
    ki_state = rows["ki"][1]["state"]
    conditioning = ki_state["conditioning"]
    require(conditioning["status"] in {"not_verified", "not_reported_in_inspected_source"}
            and conditioning["text"] is None,
            "ki: measured moisture content is unknown; presumed removal does not prove a water-free specimen")
    for field in ("processing", "temper_or_heat_treatment"):
        fact = ki_state[field]
        text = fact["text"] or ""
        require(fact["status"] == "reported" and "450 degrees C for 30 minutes" in text
                and "presume moisture removal" in text and "not proof of a water-free specimen" in text,
                "ki: annealing and the source's moisture-removal qualification must be retained")
    baf2_composition = rows["baf2"][1]["state"]["composition_or_purity"]
    text = baf2_composition["text"] or ""
    require(baf2_composition["status"] == "reported" and "0.01 to 0.1 percent" in text
            and "sodium and strontium" in text and "percentage basis and total purity are not established" in text
            and re.search(r"\b(?:weight|mass|atom|atomic)\s*(?:percent|%)", text, re.IGNORECASE) is None,
            "baf2: impurity basis and total purity are not established")
    return rows


class Checks:
    def __init__(self):
        self.results = []

    def run(self, name, group, action):
        try:
            details = action()
        except Exception as error:
            self.results.append({"name": name, "group": group, "status": "failed",
                                 "reason": str(error).splitlines()[0]})
            raise
        self.results.append({"name": name, "group": group, "status": "passed", **(details or {})})

    def reject(self, name, group, action, expected_text, precondition=None):
        def check():
            if precondition is not None:
                precondition()
            try:
                action()
            except (ValueError, jsonschema.ValidationError) as error:
                reason = str(error)
                require(expected_text in reason, name + ": rejection came from an unexpected gate: " + reason)
                details = {"rejected": True, "reason": reason.splitlines()[0]}
                if precondition is not None:
                    details["generic_contract_compatible_before_packet_guard"] = True
                return details
            raise CheckFailure(name + ": invalid mutation unexpectedly passed")
        self.run(name, group, check)


def run(packet, root, checks):
    sys.path.insert(0, str(root))
    from materials_boundaries.material_references import merge_material_catalogs, validate_material_catalog

    paths = [packet / name for name in DOCUMENT_NAMES]
    baseline_paths = [root / "materials_boundaries" / "data" / (name + ".json") for name in SCHEMA_NAMES]
    schema_paths = [root / "schemas" / (name + ".schema.json") for name in SCHEMA_NAMES]
    watched_paths = {**{"candidate/" + path.name: path for path in paths},
                     **{"catalog/" + path.name: path for path in baseline_paths},
                     **{"schema/" + path.name: path for path in schema_paths},
                     "candidate/review.json": packet / "review.json", "validator.py": Path(__file__).resolve()}
    before_bytes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in watched_paths.items()}
    checks.run("pinned_catalog_and_schema_bytes", "positive_preservation",
               lambda: require({name: before_bytes[name] for name in BASELINE_BYTES} == BASELINE_BYTES,
                               "baseline catalog/schema bytes differ from pinned main"))
    graph = [read(path) for path in paths]
    baseline = [read(path) for path in baseline_paths]
    contracts = [read(path) for path in schema_paths]
    saved_inputs = fingerprint([baseline, graph])

    def validate_schemas(selected_graph):
        for doc, contract in zip(selected_graph, contracts):
            jsonschema.Draft202012Validator(contract, format_checker=jsonschema.FormatChecker()).validate(doc)

    for index, name in enumerate(SCHEMA_NAMES):
        checks.run(name + "_schema", "positive_generic_contract", lambda index=index:
                   jsonschema.Draft202012Validator(contracts[index], format_checker=jsonschema.FormatChecker()).validate(graph[index]))
    checks.run("complete_runtime_graph", "positive_generic_contract", lambda: validate_material_catalog(*graph))
    checks.run("selected_source_handoff_facts", "positive_packet_source_facts", lambda: (check_source_facts(graph), None)[1])
    materials, properties, sources = graph
    payload = dict(zip(("materials", "properties", "sources"), graph))
    before_counts = counts(baseline)
    checks.run("pinned_baseline_counts", "positive_merge", lambda: require(before_counts == EXPECTED_BASELINE, "baseline counts differ from pinned main"))

    collisions = {}
    for label, base_doc, candidate_doc, field in (
        ("identity", baseline[0], materials, "identities"), ("grade", baseline[0], materials, "grades"),
        ("state", baseline[0], materials, "records"), ("property", baseline[1], properties, "records"),
        ("source", baseline[2], sources, "records"),
    ):
        collisions[label] = sorted({row["id"] for row in base_doc[field]} & {row["id"] for row in candidate_doc[field]})
    expected_collisions = {"identity": [], "grade": [], "state": [], "property": [], "source": [SOURCE_ID]}
    checks.run("only_intended_source_id_reuse", "positive_merge", lambda: require(collisions == expected_collisions, "unexpected baseline ID collisions"))
    baseline_source = [row for row in baseline[2]["records"] if row["id"] == SOURCE_ID]
    checks.run("reused_source_exactly_unchanged", "positive_merge", lambda: require(sources["records"] == baseline_source, "reused source differs from baseline record"))

    merged = merge_material_catalogs(*baseline, payload)
    first_counts = counts(graph_of(merged))
    first_delta = {key: first_counts[key] - before_counts[key] for key in first_counts}
    checks.run("first_disposable_merge_delta", "positive_merge", lambda: require(first_delta == EXPECTED_DELTA, "first merge delta differs from the four-material candidate"))
    repeated = merge_material_catalogs(*graph_of(merged), payload)
    repeat_delta = {key: counts(graph_of(repeated))[key] - first_counts[key] for key in first_counts}
    checks.run("repeated_merge_exactly_idempotent", "positive_merge", lambda: require(repeated == merged and all(value == 0 for value in repeat_delta.values()), "repeat merge changed graph or counts"))

    def original_records_unchanged():
        for field in ("identities", "grades", "records"):
            require(merged["materials"][field][:len(baseline[0][field])] == baseline[0][field], "pre-existing material records changed")
        require(merged["properties"]["records"][:len(baseline[1]["records"])] == baseline[1]["records"], "pre-existing properties changed")
        require(merged["sources"]["records"][:len(baseline[2]["records"])] == baseline[2]["records"], "pre-existing sources changed")
    checks.run("preexisting_records_preserved", "positive_merge", original_records_unchanged)

    def reject_graph(name, mutate, expected, *, schema=False, source_facts=False):
        changed = deepcopy(graph)
        mutate(*changed)
        if source_facts:
            # These mutations intentionally remain generic-contract compatible.
            # Their rejection must therefore come from the separate batch guard.
            def precondition():
                validate_schemas(changed)
                validate_material_catalog(*changed)
            action = lambda: check_source_facts(changed)
            group = "negative_packet_source_facts"
        else:
            precondition = None
            action = (lambda: validate_schemas(changed)) if schema else (lambda: validate_material_catalog(*changed))
            group = "negative_generic_contract"
        checks.reject(name, group, action, expected, precondition=precondition)

    reject_graph("missing_required_property", lambda m, p, s: p["records"].pop(), "property")
    reject_graph("wrong_density_unit", lambda m, p, s: p["records"][0]["reported_value"].update(unit_code="MPa", unit_text="MPa"), "dimension")
    reject_graph("unknown_primary_source", lambda m, p, s: p["records"][0].update(source_id="missing_source"), "unknown primary source")
    reject_graph("unregistered_evidence_url", lambda m, p, s: s["records"][0].update(urls=["https://example.invalid/test-only-document"]), "evidence URL absent")
    reject_graph("missing_inspection_date", lambda m, p, s: p["records"][0]["source_document"].pop("inspected_on"), "inspected_on")
    reject_graph("reported_uncertainty_without_envelope", lambda m, p, s: p["records"][0].update(uncertainty_status="reported_plus_minus_unspecified"), "nonnull envelope")
    reject_graph("unevidenced_density_repeat_count", lambda m, p, s: p["records"][0]["sample_count"].update(value=4, relation="exact", evidence=deepcopy(p["records"][0]["evidence"])), "sample_count")
    reject_graph("unevidenced_reported_mean", lambda m, p, s: p["records"][0].update(summary_statistic="reported_mean"), "summary_statistic")
    reject_graph("crystallographic_basis_changed_to_bulk", lambda m, p, s: p["records"][0].update(density_basis="bulk"), "crystallographic density")

    def clone_material(m, p, s):
        identity = deepcopy(m["identities"][0])
        original_state = next(row for row in m["records"] if row["identity_id"] == identity["id"])
        identity.update(id="mat_test_only_duplicate_halide", name="Test-only alternate supplier label")
        state = deepcopy(original_state)
        state.update(id="state_test_only_duplicate_halide", identity_id=identity["id"], property_ids=["refprop_test_only_duplicate_halide"])
        prop = deepcopy(next(row for row in p["records"] if row["material_state_id"] == original_state["id"]))
        prop.update(id="refprop_test_only_duplicate_halide", material_state_id=state["id"])
        m["identities"].append(identity)
        m["records"].append(state)
        p["records"].append(prop)

    def clone_state(m, p, s):
        state = deepcopy(m["records"][0])
        prop = deepcopy(next(row for row in p["records"] if row["material_state_id"] == state["id"]))
        state.update(id="state_test_only_duplicate_halide", name="Test-only alternate state label", property_ids=["refprop_test_only_duplicate_halide"])
        prop.update(id="refprop_test_only_duplicate_halide", material_state_id=state["id"])
        m["records"].append(state)
        p["records"].append(prop)

    reject_graph("relabeled_structural_identity_clone", clone_material, "duplicate structural identity")
    reject_graph("relabeled_structural_state_clone", clone_state, "duplicate structural state")
    merged_before = fingerprint(merged)
    for label, table, field in (("property", "properties", "scope_note"), ("source", "sources", "title")):
        conflicting = deepcopy(payload)
        conflicting[table]["records"][0][field] += " TEST-ONLY conflict."
        checks.reject("conflicting_existing_" + label, "negative_generic_merge",
                      lambda conflicting=conflicting: merge_material_catalogs(*graph_of(merged), conflicting),
                      "conflicting existing catalog record")
    checks.run("failed_merges_preserve_inputs", "positive_merge", lambda: require(fingerprint(merged) == merged_before, "failed merge mutated existing graph"))

    def change_temperature(formula, text, m, p, s):
        prop = by_formula((m, p, s))[formula][2]
        temperature = prop["conditions"]["temperature"]
        evidence = deepcopy(prop["evidence"][0])
        evidence["supports"] = ["condition"]
        temperature.update(status="reported", text=text, evidence=[evidence])

    reject_graph("naf_pattern_temperature_as_density_temperature",
                 lambda m, p, s: change_temperature("naf", "26 degrees C", m, p, s),
                 "naf: density temperature must remain unknown", source_facts=True)
    reject_graph("ki_annealing_temperature_as_density_temperature",
                 lambda m, p, s: change_temperature("ki", "450 degrees C", m, p, s),
                 "ki: source density reference temperature changed", source_facts=True)

    def invent_density_uncertainty(m, p, s):
        prop = by_formula((m, p, s))["kbr"][2]
        evidence = deepcopy(prop["evidence"][0])
        evidence["supports"] = ["uncertainty"]
        prop["evidence"].append(deepcopy(evidence))
        prop.update(uncertainty_status="reported_plus_minus_unspecified", uncertainty={
            "type": "reported_plus_minus_unspecified", "value_text": "0.0001", "number": "0.0001",
            "unit_text": "grams per cubic centimeter", "unit_code": "g/cm^3",
            "scope": "TEST ONLY: incorrectly treating a lattice error as a density uncertainty.",
            "confidence_level": None, "coverage_factor": None, "evidence": [evidence],
        })

    def claim_water_free(m, p, s):
        state = by_formula((m, p, s))["ki"][1]
        evidence = deepcopy(state["evidence"][0])
        evidence["supports"] = ["state"]
        state["state"]["conditioning"].update(status="reported", text="TEST ONLY: proven water-free specimen.", evidence=[evidence])

    def invent_impurity_basis(m, p, s):
        fact = by_formula((m, p, s))["baf2"][1]["state"]["composition_or_purity"]
        fact["text"] = fact["text"].replace("0.01 to 0.1 percent", "0.01 to 0.1 weight percent")

    def coherent_bulk_relabel(m, p, s):
        # Unlike changing density_basis alone, this relabel remains structurally
        # legal. The packet-specific source fact must reject the reinterpretation.
        prop = by_formula((m, p, s))["kbr"][2]
        prop.update(density_basis="bulk", evidence_kind="published_experimental_reference",
                    determination_basis="source_reports_measurement")
        prop["method_definition"].update(type="source_reported_conventional",
                                          definition="TEST ONLY: directly measured bulk density by pycnometry.")

    reject_graph("lattice_error_transferred_to_density_uncertainty", invent_density_uncertainty,
                 "density uncertainty is unknown", source_facts=True)
    reject_graph("ki_presumed_moisture_removal_as_proven_water_free", claim_water_free,
                 "ki: measured moisture content is unknown", source_facts=True)
    reject_graph("baf2_impurity_percent_as_weight_percent", invent_impurity_basis,
                 "baf2: impurity basis and total purity are not established", source_facts=True)
    reject_graph("coherent_bulk_relabel_of_source_crystallographic_density", coherent_bulk_relabel,
                 "source reports crystallographic derivation, not bulk measurement", source_facts=True)

    checks.run("all_input_objects_preserved", "positive_preservation", lambda: require(fingerprint([baseline, graph]) == saved_inputs, "validation mutated an input graph"))
    after_bytes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in watched_paths.items()}
    checks.run("all_watched_files_unchanged", "positive_preservation", lambda: require(before_bytes == after_bytes, "validation changed a watched file"))
    return {
        "status": "local_candidate_checks_passed_not_admitted", "candidate_counts": counts(graph),
        "baseline_catalog_and_schema_bytes_match_commit": BASELINE_COMMIT,
        "baseline_counts": before_counts, "first_in_memory_merge_counts": first_counts,
        "first_in_memory_merge_delta": first_delta, "repeat_merge_delta": repeat_delta,
        "repeat_graph_exactly_equal": True, "baseline_id_collisions": collisions,
        "existing_records_and_input_objects_preserved": True, "watched_files_unchanged": True,
        "watched_file_sha256": before_bytes, "formal_project_total_from_pinned_baseline": 1081,
        "admitted_delta": 0, "source_documents_read_live": 0,
        "limitations": [
            "Software compatibility and a disposable in-memory merge only; candidate records remain unadmitted.",
            "The formal project total is pinned baseline context, not a new formal census.",
            "Source-specific guards check selected supplied review facts; they do not inspect source pages or prove prose fidelity.",
            "No independent scientific review, rights approval, measurement replication, chemical-equivalence inference, or publication occurs.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args()
    packet = args.packet_dir.resolve()
    root = args.repo_root.resolve() if args.repo_root else packet.parents[2]
    checks = Checks()
    try:
        result = run(packet, root, checks)
        exit_code = 0
    except Exception as error:
        if not checks.results or checks.results[-1]["status"] != "failed":
            checks.results.append({"name": "execution_failure", "group": "execution", "status": "failed",
                                   "reason": str(error).splitlines()[0]})
        result = {"status": "local_candidate_checks_failed", "error_type": type(error).__name__,
                  "error": str(error), "remaining_checks_not_executed_after_failure": True,
                  "admitted_delta": 0}
        exit_code = 1
    result["checks"] = checks.results
    result["checks_passed"] = sum(row["status"] == "passed" for row in checks.results)
    result["checks_failed"] = sum(row["status"] == "failed" for row in checks.results)
    # After a failure the remaining actions were not reached; do not call that
    # a successful zero-skip run or invent a remaining-check count.
    result["checks_skipped"] = 0 if exit_code == 0 else None
    result["negative_checks_passed"] = sum(row["status"] == "passed" and row["group"].startswith("negative_") for row in checks.results)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
