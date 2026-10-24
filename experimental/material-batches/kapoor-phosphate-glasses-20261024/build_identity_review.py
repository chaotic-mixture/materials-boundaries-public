"""Reproduce the finite Kapoor candidate audit from one immutable Git commit.

This batch-local evidence tool does not validate scientific truth, admit records,
query providers, or change runtime data. Run --write once, then --check to compare
the entire generated review. Only the adjacent identity-review.json is writable.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import unicodedata


ROOT = Path(__file__).resolve().parents[3]
BASELINE = "196995256836db2d8f870ac9a91f664bfdd03e7f"
BATCH = "kapoor-phosphate-glasses-20261024"
DOI = "10.3389/fmats.2019.00063"
INPUTS = (
    "materials_boundaries/data/materials.json",
    "materials_boundaries/data/reference_properties.json",
    "materials_boundaries/data/sources.json",
    "materials_boundaries/data/taxonomy_migration_v1.json",
    "materials_boundaries/data/wood_baseline_crosswalk_v2.json",
    "materials_boundaries/data/wood_source_registry_v2.json",
    "formal-catalog/materials_project_catalog/data/formal_computed_review.json",
    "experimental/platform/examples/reviewed-computed-v2/eligible-metadata-input.json",
    "experimental/platform/examples/reviewed-computed-v2/normalized-review.json",
    "experimental/platform/examples/reviewed-computed-v2/acceptance-pin.json",
    "experimental/platform/examples/reviewed-computed-v2-second/eligible-metadata-input.json",
    "experimental/platform/examples/reviewed-computed-v2-second/normalized-review.json",
    "experimental/platform/examples/reviewed-computed-v2-second/acceptance-pin.json",
    "experimental/platform/examples/reviewed-computed-seed/scoped-review-input.json",
    "experimental/platform/query-service/materials_query/pins/family_relationships.json",
    "experimental/platform/relationships/typed_edge_examples.json",
    "experimental/platform/relationships/hbn_projection_review.json",
    "docs/MATERIAL_REFERENCE_CATALOG.md",
    "scripts/prepare_formulation_packet.py",
    "materials_boundaries/material_references.py",
    "experimental/platform/query-service/materials_query/family_relationships.py",
    "formal-catalog/materials_project_catalog/catalog.py",
)
ROWS = (
    ("P60", ("0", "40.4", "59.6")),
    ("P50", ("0", "49.9", "50.1")),
    ("P46", ("0", "53.9", "46.1")),
    ("Al5", ("5.0", "40.2", "54.8")),
    ("Al10", ("10.0", "30.1", "59.9")),
    ("Al15", ("14.8", "20.0", "65.2")),
)
CONTEXT_PATTERN = r"kapoor|aluminophosph|calcium[ -]+phosph|phosphat|apatite|po4|p2o5|10\.3389/fmats\.2019\.00063"
CONTEXT = re.compile(CONTEXT_PATTERN, re.IGNORECASE)


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def ascii_key(text):
    return re.sub("[^a-z0-9]", "", normalized(text))


def labels(record):
    for field in ("name", "source_designation", "designation"):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            yield field, value
    for locale, value in record.get("names", {}).items():
        if isinstance(value, str) and value.strip():
            yield "names." + locale, value
    for index, alias in enumerate(record.get("aliases", [])):
        value = alias["text"]
        if value.strip():
            yield "aliases[" + str(index) + "].text", value


def raw_text(value):
    return unicodedata.normalize("NFKC", json.dumps(value, ensure_ascii=False, sort_keys=True))


def record_key(record):
    return record.get("id", record.get("candidate_id", record.get("project_material_id")))


def build_review():
    documents, descriptors, whole_file_matches = {}, [], {}
    for path in INPUTS:
        raw = subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT, timeout=60)
        text = raw.decode("utf-8")
        descriptors.append({"path": path, "bytes": len(raw), "sha256": sha256(raw).hexdigest()})
        whole_file_matches[path] = {
            "candidate_doi_occurrences": text.casefold().count(DOI),
            "candidate_identity_id_occurrences": sum(text.count("mat_kapoor2019_" + label.casefold()) for label, _ in ROWS),
            "context_terms": dict(sorted(Counter(match.group(0).casefold() for match in CONTEXT.finditer(unicodedata.normalize("NFKC", text))).items())),
        }
        if path.endswith(".json"):
            documents[path] = json.loads(text)
    materials, properties, sources = (documents[path] for path in INPUTS[:3])
    all_labels = []
    occurrence_counts, alias_counts = {}, {}
    for collection in ("identities", "grades", "records"):
        occurrence_counts[collection] = 0
        alias_counts[collection] = sum(len(row.get("aliases", [])) for row in materials[collection])
        for row in materials[collection]:
            for field, label in labels(row):
                all_labels.append({"collection": collection, "id": row["id"], "field": field, "text": label})
                occurrence_counts[collection] += 1
    collisions = {}
    for label, _ in ROWS:
        matches = []
        token = re.compile(r"(?<![A-Za-z0-9])" + re.escape(label) + r"(?![A-Za-z0-9])", re.IGNORECASE)
        for item in all_labels:
            modes = []
            if item["text"].strip().casefold() == label.casefold():
                modes.append("strip_casefold_exact")
            if normalized(item["text"]) == normalized(label):
                modes.append("nfkc_casefold_whitespace_exact")
            if ascii_key(item["text"]) == ascii_key(label):
                modes.append("ascii_alphanumeric_exact")
            if token.search(unicodedata.normalize("NFKC", item["text"])):
                modes.append("bounded_token")
            if modes:
                matches.append({**item, "comparison_modes": modes})
        collisions[label] = matches
    record_screen = {}
    for name, rows in (("identities", materials["identities"]), ("grades", materials["grades"]),
                       ("states", materials["records"]), ("reference_properties", properties["records"]),
                       ("sources", sources["records"])):
        record_screen[name] = {
            "records_scanned": len(rows),
            "contextual_hits": [{"id": record_key(row), "matched_terms": sorted(set(match.group(0).casefold() for match in CONTEXT.finditer(raw_text(row))))}
                                for row in rows if CONTEXT.search(raw_text(row))],
        }
    inorganic = []
    for identity in materials["identities"]:
        if identity["category"] != "inorganic":
            continue
        states = [state for state in materials["records"] if state["identity_id"] == identity["id"]]
        inorganic.append({"id": identity["id"], "name": identity["name"], "aliases": identity["aliases"],
                          "identity_scope": identity["identity_scope"], "evidence": identity["evidence"],
                          "states": [{"id": state["id"], "source_designation": state["source_designation"],
                                      "grade_id": state["grade_id"], "composition_or_purity": state["state"]["composition_or_purity"]}
                                     for state in states]})
    computed = []
    for path, scope in ((INPUTS[6], "24 existing admitted computed records; not measured source-qualified identities"),
                        (INPUTS[11], "62 excluded examples; no automatic admission"),
                        (INPUTS[13], "7 historical seed records; not additional formal growth")):
        rows = documents[path]["records"]
        computed.append({
            "path": path, "scope": scope, "records": len(rows),
            "categories": dict(sorted(Counter(row.get("primary_category", "legacy_scope_unspecified") for row in rows).items())),
            "formula_inventory": [{"id": record_key(row), "formula": row["formula"]} for row in rows],
            "contextual_hits": [record_key(row) for row in rows if CONTEXT.search(raw_text(row))],
            "contains_calcium_phosphorus_and_oxygen": [record_key(row) for row in rows
                if {"Ca", "P", "O"}.issubset(set(re.findall(r"[A-Z][a-z]?", row["formula"])))],
            "recorded_overlap_relations": [{"id": record_key(row),
                                            "canonical_relations_sha256": sha256(json.dumps(row["overlap_relations"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                                            "prior_seven_hits": row["overlap_relations"].get("prior_seven_hits", []),
                                            "other_batch_same_composition_hits": row["overlap_relations"].get("other_batch_same_composition_hits", []),
                                            "baseline_identifier_or_formula_hits": row["overlap_relations"].get("baseline_identifier_or_formula_hits", []),
                                            "cross_provider_global_equivalence": row["overlap_relations"].get("cross_provider_global_equivalence")}
                                           for row in rows if row.get("overlap_relations")],
            "limitation": "Formula and recorded overlap screens concern finite historical metadata; no new provider lookup or glass equivalence calculation was performed.",
        })
    relationship = documents[INPUTS[14]]
    examples = documents[INPUTS[15]]
    bianchi = next(row for row in materials["identities"] if row["id"] == "mat_bianchi2022_epdm_h_p60")
    decisions = []
    for label, composition in ROWS:
        decisions.append({
            "identity_id": "mat_kapoor2019_" + label.casefold(), "source_designation": label,
            "proposed_name": ("Calcium phosphate" if label.startswith("P") else "Calcium aluminophosphate") + " glass " + label + " (Kapoor 2019)",
            "category": "inorganic", "grade_id": None,
            "analyzed_composition": {"method": "ICP-OES", "basis": "source-reported analyzed oxide mol%", "components": dict(zip(("Al2O3", "CaO", "P2O5"), composition)),
                                     "locator": "Original article PDF p.3, Table 1, " + label + " row"},
            "decision": "conditionally_distinct_source_qualified_glass_formulation_candidate",
            "reason": "Different reported analyzed oxide compositions distinguish the six source-qualified formulations within this study. The finite current catalog contains no calcium phosphate or calcium aluminophosphate glass identity/alias/source match. Source labels, density differences, annealing histories and repeated specimens alone do not establish novelty.",
            "label_matches": collisions[label],
            "scope_limit": "Analyzed oxide composition is not a nominal recipe, certified purity, exact final molecular/phase identity, or proof of global chemical uniqueness. Compressed states do not create additional identities.",
        })
    return {
        "schema": "material-batch-finite-identity-review/1", "batch_id": BATCH, "baseline_commit": BASELINE,
        "review_date": "2026-10-24",
        "review_scope": "Finite frozen-catalog identity, alias, composition-context, source and relationship audit for a review-only six-candidate packet. No runtime admission is performed.",
        "scientific_review": False, "scientific_replication": False, "global_chemical_uniqueness_established": False,
        "primary_source_and_rights_review_performed_by_this_audit": False,
        "baseline_counts": {"source_qualified_identities": len(materials["identities"]), "grades": len(materials["grades"]),
                            "states": len(materials["records"]), "reference_properties": len(properties["records"]), "sources": len(sources["records"]),
                            "source_qualified_categories": dict(sorted(Counter(row["category"] for row in materials["identities"]).items())),
                            "existing_formal_computed_records": len(documents[INPUTS[6]]["records"]),
                            "experimental_project_total": len(materials["identities"]) + len(documents[INPUTS[6]]["records"]),
                            "new_admissions_in_this_audit": 0},
        "immutable_inputs": descriptors,
        "input_scope_note": "The same 22-path finite inventory as the Tarasov audit was reacquired at 1969952. The three runtime tables already include the published Tarasov additions; no old counts or hashes were reused and no additional baseline inputs were needed.",
        "reproduction": {"helper": Path(__file__).resolve().relative_to(ROOT).as_posix(), "helper_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                         "input_acquisition": "git show <baseline_commit>:<POSIX repository path>; hash original bytes; decode JSON/text as strict UTF-8. No current working-tree data substitution.",
                         "labels": "All name/source_designation/designation/names values/aliases[].text in every identity, grade and state. Multilingual occurrences are not identities.",
                         "comparison": "strip/casefold exact; NFKC/casefold/collapsed-whitespace exact; ASCII-alphanumeric exact; separate bounded-token matches. Token collisions are not exact-label collisions.",
                         "full_record_screen": CONTEXT_PATTERN,
                         "composition_review": "Inspect all 53 inorganic identity scopes and their state composition facts, all source records, all six analyzed composition tuples, and finite computed formula/overlap inventories. Text normalization is not a chemical-equivalence engine.",
                         "gate": "Retain prepare_formulation_packet.py source-scoped label collision checks and material_references.py structural-clone checks; this artifact does not replace those gates."},
        "label_inventory": {"field_occurrences_by_collection": occurrence_counts, "field_occurrences_total": len(all_labels),
                            "unique_nfkc_casefold_whitespace_labels": len({normalized(item["text"]) for item in all_labels}),
                            "alias_records_by_collection": alias_counts},
        "candidate_label_comparison": collisions, "full_record_text_screen": record_screen,
        "contextual_hit_dispositions": [
            {"state_id": "state_nbs1953_kcl_mallinckrodt_kyd1_xrd", "identity_id": "mat_nbs1953_kcl_mallinckrodt_kyd1",
             "matched_term": "PO4", "source_entry": "PO4 0.002 percent in the accompanying KCl chemical analysis; percentage basis unspecified",
             "disposition": "An impurity-analysis entry in crystalline KCl does not identify a calcium phosphate glass or a Kapoor formulation."},
            {"state_id": "state_nbs1953_kcn_mallinckrodt_gnb_xrd", "identity_id": "mat_nbs1953_kcn",
             "matched_term": "PO4", "source_entry": "PO4 0.005 percent in the KCN chemical analysis; percentage basis unspecified",
             "disposition": "An impurity-analysis entry in crystalline KCN does not identify a calcium phosphate glass or a Kapoor formulation."}],
        "whole_input_screen": whole_file_matches,
        "inorganic_identity_inventory": inorganic,
        "composition_and_granularity_review": {
            "candidate_composition_tuples_are_pairwise_distinct": len({tuple(values) for _, values in ROWS}) == len(ROWS),
            "existing_glass_contexts": [row["id"] for row in inorganic if "glass" in normalized(row["name"] + " " + row["identity_scope"])],
            "assessment": "Existing named silicate/borosilicate/fused-silica products and Bruns nominal borosilicate recipes do not identify calcium phosphate/aluminophosphate compositions. The NBS CaO single-compound identity and alumina ceramic identity are not identities for every mixture containing CaO or Al2O3. A component overlap is not material equivalence.",
            "p60_collision": {"kind": "bounded token/suffix collision, not an exact bare-label alias match", "existing_identity_id": bianchi["id"],
                              "existing_name": bianchi["name"], "existing_identity_scope": bianchi["identity_scope"],
                              "disposition": "EPDM_H_P60 is a carbon-black-filled EPDM/paraffin/Hostatron composite. Preserve Kapoor's literal source designation P60, use study-qualified identity names/aliases and mat_kapoor2019_p60, and do not assert equivalence from the shared token."},
            "limitation": "No global equivalence registry, unrecorded composition, exact phase/lot chemistry, independent scientific review or raw-data reanalysis is established. Source-specific labels alone never justify a new identity."},
        "computed_inventory": computed,
        "relationship_inventory": {"runtime_overlay_path": INPUTS[14], "runtime_memberships": len(relationship["memberships"]),
                                   "runtime_relationships": len(relationship["relationships"]), "example_path": INPUTS[15], "example_edges": len(examples),
                                   "result": "The finite runtime, typed-edge and hBN projection inputs have no Kapoor/phosphate-glass candidate endpoint or recorded equivalence. Constituent, membership and state links do not propagate equivalence or properties."},
        "taxonomy_and_wood_inventory": {"taxonomy_migrated_identities": len(documents[INPUTS[3]]["migrated_identity_ids"]),
                                       "baseline_crosswalk_rows": len(documents[INPUTS[4]]),
                                       "reviewed_wood_row_hashes": len(documents[INPUTS[5]]["reviewed_row_sha256"]),
                                       "wood_physical_locators": len(documents[INPUTS[5]]["gwdd_physical_locators"]),
                                       "result": "Finite taxonomy/wood inputs contain no candidate DOI, identity ID or phosphate-glass context hit."},
        "candidate_decisions": decisions,
        "candidate_delta": {"identities": 6, "inorganic": 6, "grades": 0, "states": 6, "properties": 6, "sources": 1},
        "formal_admitted_delta": 0,
        "required_preserved_qualifications": [
            "All oxide values are source-reported analyzed ICP-OES mol%, not nominal recipes, mass fractions, independently verified assays or normalized final stoichiometry.",
            "P60, P50, P46, Al5, Al10 and Al15 are literal source designations; identity names and aliases must be study-qualified and grades remain null.",
            "Annealed/reannealed as-prepared states qualify formulations. Compressed-state variants and repeated measurements do not add identities.",
            "Source-wide maximum SD <=0.002 g/cm^3 is not six row-specific SDs; retain null numerical uncertainty and the source qualification.",
            "At least ten repetitions per sample is not a known independent-specimen count. Exact temperature, pressure, humidity, porosity, independent count and row-specific melt schedules remain unestablished.",
            "No calculated molar volume, packing density, compressed-state density, pure molecular species or engineering-allowable claim enters this six-density proposal."],
        "acceptance_dependencies": ["Separate source-byte, attribution and rights review.", "Strict compiler/catalog replay and focused candidate regression tests.",
                                    "Independent parent review before any runtime admission or experimental publication."],
        "execution_scope": {"artifact": "Candidate-only finite identity audit and reproducible inventory helper", "runtime_catalog_modified": False,
                            "raw_source_assets_included": False, "independent_scientific_review": False, "network_queries": False,
                            "tests_run_by_this_helper": [], "formal_admitted_delta": 0},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Create the adjacent immutable review; refuse different existing bytes.")
    mode.add_argument("--check", action="store_true", help="Rebuild from frozen Git inputs and compare every output byte.")
    args = parser.parse_args()
    review = build_review()
    encoded = (json.dumps(review, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output = Path(__file__).with_name("identity-review.json")
    if output.exists():
        if output.read_bytes() != encoded:
            raise SystemExit("Existing identity review differs from exact replay; not overwritten.")
        action = "Verified unchanged"
    elif args.check:
        raise SystemExit("Identity review is absent; --check does not create files.")
    else:
        with output.open("xb") as stream:
            stream.write(encoded)
        action = "Created"
    print(action + ": " + output.name)
    print(json.dumps({"baseline": BASELINE, "inputs": len(INPUTS), "counts": review["baseline_counts"],
                      "labels": review["label_inventory"], "sha256": sha256(encoded).hexdigest()}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
