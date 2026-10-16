"""Validate the local Nb candidate and rehearse a merge without writing catalogs.

Success establishes software-contract compatibility, never scientific review,
rights approval, formal admission, or permission to publish.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import jsonschema

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from materials_boundaries.material_references import merge_material_catalogs, validate_material_catalog


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def counts(graph):
    materials, properties, sources = graph
    return {"identities": len(materials["identities"]), "grades": len(materials["grades"]),
            "states": len(materials["records"]), "properties": len(properties["records"]),
            "sources": len(sources["records"])}


def graph_of(merged):
    return merged["materials"], merged["properties"], merged["sources"]


def main():
    paths = [HERE / name for name in (
        "nb-materials.candidate.json", "nb-reference-properties.candidate.json", "nb-sources.candidate.json")]
    graph = [read(path) for path in paths]
    schemas = [read(ROOT / "schemas" / (name + ".schema.json"))
               for name in ("materials", "reference_properties", "sources")]
    for doc, schema in zip(graph, schemas):
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(doc)
    validate_material_catalog(*graph)

    materials, properties, sources = graph
    state, prop, source = materials["records"][0], properties["records"][0], sources["records"][0]
    assert counts(graph) == {"identities": 1, "grades": 0, "states": 1, "properties": 1, "sources": 1}
    assert prop["reported_value"] == {"kind": "scalar", "value_text": "8587.6", "unit_text": "kg/m³", "unit_code": "kg/m^3", "number": "8587.6"}
    assert prop["conditions"]["temperature"]["text"] == "293 K"
    assert prop["sample_count"]["value"] is None and prop["sample_count"]["relation"] == "not_reported"
    assert prop["uncertainty"] is None and prop["uncertainty_status"] == "not_reported_in_inspected_source"
    assert prop["density_basis"] == prop["summary_statistic"] == prop["reporting_basis"] == "not_stated"
    assert prop["source_document"]["inspected_on"] == "2026-10-15"
    assert prop["source_document"]["sha256"] is None and prop["source_document"]["hash_status"] == "unavailable"
    assert prop["verification"]["independent_scientific_review"] is False
    assert prop["verification"]["raw_data_reanalysis"] is False
    assert state["grade_id"] is None and source["license"]["identifier"] == "CC-BY-4.0"
    for key in ("processing", "reinforcement", "porosity", "orientation"):
        assert state["state"][key]["status"] == "not_verified"
    for key in ("test_standard", "direction", "loading_rate"):
        assert prop["conditions"][key]["status"] == "not_verified"

    review = read(HERE / "review.json")
    source_check = review["source_check_record"]
    assert source["title"] == review["parent_verified_findings"]["article_title"]
    assert not review["required_handoff_gaps"]
    assert [item["accessed_at"] for item in source_check["captures"]] == [
        "2026-10-15T00:17:09Z", "2026-10-15T00:17:33Z", "2026-10-15T00:17:37Z"]
    assert source_check["supplement_checks_completed_by"] == "2026-10-15T00:18:07Z"
    assert source_check["final_article_cross_check_completed_by"] == "2026-10-15T00:18:32Z"
    assert source_check["independent_human_scientific_review"] is False

    # This is a disposable local rehearsal, not an admitted release build.
    baseline_paths = [ROOT / "materials_boundaries/data" / (name + ".json")
                      for name in ("materials", "reference_properties", "sources")]
    baseline = [read(path) for path in baseline_paths]
    disk_paths = baseline_paths + paths
    before_bytes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in disk_paths}
    saved_inputs = fingerprint([baseline, graph])
    payload = dict(zip(("materials", "properties", "sources"), graph))
    before_counts = counts(baseline)
    collisions = {}
    for label, base_doc, candidate_doc, field in (
        ("identity", baseline[0], materials, "identities"), ("grade", baseline[0], materials, "grades"),
        ("state", baseline[0], materials, "records"), ("property", baseline[1], properties, "records"),
        ("source", baseline[2], sources, "records"),
    ):
        collisions[label] = sorted({row["id"] for row in base_doc[field]} & {row["id"] for row in candidate_doc[field]})
        assert not collisions[label], (label, collisions[label])

    merged = merge_material_catalogs(*baseline, payload)
    first_counts = counts(graph_of(merged))
    expected_delta = {"identities": 1, "grades": 0, "states": 1, "properties": 1, "sources": 1}
    assert {key: first_counts[key] - before_counts[key] for key in first_counts} == expected_delta
    repeated = merge_material_catalogs(*graph_of(merged), payload)
    assert repeated == merged
    assert fingerprint([baseline, graph]) == saved_inputs
    for field in ("identities", "grades", "records"):
        assert merged["materials"][field][:len(baseline[0][field])] == baseline[0][field]
    assert merged["properties"]["records"][:len(baseline[1]["records"])] == baseline[1]["records"]
    assert merged["sources"]["records"][:len(baseline[2]["records"])] == baseline[2]["records"]

    rejected = {}

    def reject(name, mutate, expected, schema=False):
        changed = deepcopy(graph)
        mutate(*changed)
        try:
            if schema:
                for doc, contract in zip(changed, schemas):
                    jsonschema.Draft202012Validator(contract).validate(doc)
            else:
                validate_material_catalog(*changed)
        except (ValueError, jsonschema.ValidationError) as error:
            assert expected in str(error), (name, str(error))
            rejected[name] = {"rejected": True, "reason": str(error).splitlines()[0]}
        else:
            raise AssertionError(name + " unexpectedly passed")

    reject("missing_property", lambda m, p, s: p["records"].clear(), "property")
    reject("wrong_density_unit", lambda m, p, s: p["records"][0]["reported_value"].update(unit_code="MPa", unit_text="MPa"), "dimension")
    reject("unknown_primary_source", lambda m, p, s: p["records"][0].update(source_id="missing_source"), "unknown primary source")
    reject("source_url_not_registered", lambda m, p, s: s["records"][0].update(urls=["https://example.invalid/other-document"]), "evidence URL absent")
    reject("unsupported_six_density_repeats", lambda m, p, s: p["records"][0]["sample_count"].update(value=6, relation="exact", evidence=deepcopy(p["records"][0]["evidence"])), "sample_count")
    reject("unsupported_reported_mean", lambda m, p, s: p["records"][0].update(summary_statistic="reported_mean"), "reported mean")
    reject("reported_uncertainty_without_envelope", lambda m, p, s: p["records"][0].update(uncertainty_status="reported_standard_deviation"), "nonnull envelope")
    reject("missing_source_inspection_date", lambda m, p, s: p["records"][0]["source_document"].update(inspected_on=None), "inspected_on")
    reject("missing_source_title", lambda m, p, s: s["records"][0].update(title=None), "not of type", schema=True)

    def clone_identity(m, p, s):
        identity = deepcopy(m["identities"][0])
        identity.update(id="mat_test_only_duplicate_nb", name="Alternate test-only display label")
        state_clone = deepcopy(m["records"][0])
        state_clone.update(id="state_test_only_duplicate_nb", identity_id=identity["id"], property_ids=["refprop_test_only_duplicate_nb"])
        property_clone = deepcopy(p["records"][0])
        property_clone.update(id="refprop_test_only_duplicate_nb", material_state_id=state_clone["id"])
        m["identities"].append(identity)
        m["records"].append(state_clone)
        p["records"].append(property_clone)

    def clone_state(m, p, s):
        state_clone = deepcopy(m["records"][0])
        state_clone.update(id="state_test_only_duplicate_nb", name="Alternate test-only state label", property_ids=["refprop_test_only_duplicate_nb"])
        property_clone = deepcopy(p["records"][0])
        property_clone.update(id="refprop_test_only_duplicate_nb", material_state_id=state_clone["id"])
        m["records"].append(state_clone)
        p["records"].append(property_clone)

    reject("relabeled_duplicate_nb_identity", clone_identity, "duplicate structural identity")
    reject("relabeled_duplicate_nb_state", clone_state, "duplicate structural state")
    conflicting = deepcopy(payload)
    conflicting["sources"]["records"][0]["title"] = "TEST ONLY: conflicting title, never retained in candidate data"
    merged_before = fingerprint(merged)
    try:
        merge_material_catalogs(*graph_of(merged), conflicting)
    except ValueError as error:
        assert "conflicting existing catalog record" in str(error)
        rejected["conflicting_existing_source"] = {"rejected": True, "reason": str(error)}
    else:
        raise AssertionError("Conflicting source unexpectedly merged")
    assert fingerprint(merged) == merged_before
    assert fingerprint([baseline, graph]) == saved_inputs
    after_bytes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in disk_paths}
    assert before_bytes == after_bytes
    print(json.dumps({
        "status": "local_candidate_checks_passed_not_admitted", "complete_graph_valid": True,
        "schema_documents_passed": 3, "runtime_graph_valid": True,
        "candidate_counts": counts(graph), "baseline_counts": before_counts,
        "first_in_memory_merge_counts": first_counts, "first_in_memory_merge_delta": expected_delta,
        "repeat_merge_delta": {key: 0 for key in expected_delta}, "repeat_graph_exactly_equal": True,
        "existing_records_and_input_objects_preserved": True, "disk_catalogs_unchanged": True,
        "baseline_id_collisions": collisions, "negative_checks": rejected,
        "negative_checks_passed": len(rejected), "formal_project_total": 1081, "admitted_delta": 0,
        "limitations": "Software checks and disposable merge only. No independent human scientific/rights review or formal admission. Chemical equivalence is not inferred from IDs or automated clone checks.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
