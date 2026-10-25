"""Replay a finite Curaua composite candidate audit from frozen Git objects.

No network request, source-rights approval or runtime admission is performed.
--write creates only the adjacent review and refuses different existing bytes.
--check rereads every input and compares every output byte. No cross-call cache.
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
BASELINE = "ee8c2cd3d410db10449951fa069e746804d1c937"
BATCH = "czlonka-curaua-20261025"
DOI = "10.3390/ijms222011203"
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
    ("mat_czlonka2021_curaua_cf0p1", "CF 0.1", "0.1", "38.4"),
    ("mat_czlonka2021_curaua_cf0p5", "CF 0.5", "0.5", "37.9"),
    ("mat_czlonka2021_curaua_cf1", "CF 1", "1", "37.6"),
)
# Family, botanical/filler and generic CF terms are retained as context, not
# treated as identity-equivalence evidence or as proof of global uniqueness.
CONTEXT_PATTERN = (
    r"curau[a\u00e1]|ananas|bromeli|polyurethane|Cz[l\u0142]onka|"
    r"(?<![A-Za-z0-9])(?:RPUF|PUR|PUF|CF\s*0[.]1|CF\s*0[.]5|CF\s*1|CF)(?![A-Za-z0-9])|"
    r"Lupranol|Polycat|PM200|Polios|10[.]3390/ijms222011203"
)
CONTEXT = re.compile(CONTEXT_PATTERN, re.IGNORECASE)
SPECIFIC = re.compile(r"curau[a\u00e1]|ananas|bromeli", re.IGNORECASE)


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def ascii_key(text):
    return re.sub("[^a-z0-9]", "", normalized(text))


def raw_text(value):
    return unicodedata.normalize("NFKC", json.dumps(value, ensure_ascii=False, sort_keys=True))


def record_key(record):
    for key in ("id", "candidate_id", "project_material_id", "identity_id"):
        if key in record:
            return record[key]
    return None


def record_hash(record):
    return sha256(json.dumps(record, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")).hexdigest()


def labels(record):
    for field in ("name", "source_designation", "designation"):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            yield field, value
    for locale, value in record.get("names", {}).items():
        if isinstance(value, str) and value.strip():
            yield "names." + locale, value
    for index, alias in enumerate(record.get("aliases", [])):
        if alias["text"].strip():
            yield "aliases[" + str(index) + "].text", alias["text"]


def contextual_hits(rows, pattern=CONTEXT):
    return [{"id": record_key(row), "matched_terms": sorted(set(
                match.group(0).casefold() for match in pattern.finditer(raw_text(row)))),
             "record_sha256": record_hash(row)}
            for row in rows if pattern.search(raw_text(row))]


def build_review():
    documents, descriptors, whole_file_matches = {}, [], {}
    for path in INPUTS:
        raw = subprocess.check_output(["git", "show", BASELINE + ":" + path],
                                      cwd=ROOT, timeout=60)
        text = raw.decode("utf-8")
        descriptors.append({"path": path, "bytes": len(raw), "sha256": sha256(raw).hexdigest()})
        whole_file_matches[path] = {
            "candidate_doi_occurrences": text.casefold().count(DOI),
            "candidate_identity_id_occurrences": sum(text.count(row[0]) for row in ROWS),
            "context_terms": dict(sorted(Counter(match.group(0).casefold() for match in
                CONTEXT.finditer(unicodedata.normalize("NFKC", text))).items())),
        }
        if path.endswith(".json"):
            documents[path] = json.loads(text)
    materials, properties, sources = (documents[path] for path in INPUTS[:3])
    all_labels, occurrence_counts, alias_counts = [], {}, {}
    for collection in ("identities", "grades", "records"):
        occurrence_counts[collection] = 0
        alias_counts[collection] = sum(len(row.get("aliases", [])) for row in materials[collection])
        for row in materials[collection]:
            for field, label in labels(row):
                all_labels.append({"collection": collection, "id": row["id"], "field": field, "text": label})
                occurrence_counts[collection] += 1
    collisions = {}
    for label in ("CF 0.1", "CF 0.5", "CF 1", "CF0.1", "CF0.5", "CF1", "CF", "Curaua", "Curauá", "RPUF", "PUR"):
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
    record_screen = {
        name: {"records_scanned": len(rows), "contextual_hits": contextual_hits(rows),
               "botanical_or_fiber_name_hits": contextual_hits(rows, SPECIFIC)}
        for name, rows in (("identities", materials["identities"]), ("grades", materials["grades"]),
                           ("states", materials["records"]), ("reference_properties", properties["records"]),
                           ("sources", sources["records"]))
    }
    inventory = []
    for identity in materials["identities"]:
        if identity["category"] not in {"polymer", "composite"}:
            continue
        states = [state for state in materials["records"] if state["identity_id"] == identity["id"]]
        inventory.append({
            "id": identity["id"], "category": identity["category"], "name": identity["name"],
            "aliases": identity["aliases"], "identity_scope": identity["identity_scope"],
            "evidence": identity["evidence"], "record_sha256": record_hash(identity),
            "states": [{"id": state["id"], "source_designation": state["source_designation"],
                        "grade_id": state["grade_id"], "composition_or_purity": state["state"]["composition_or_purity"],
                        "reinforcement": state["state"]["reinforcement"], "record_sha256": record_hash(state)}
                       for state in states],
        })
    computed = []
    for path, scope in ((INPUTS[6], "24 existing admitted computed records; not measured source-qualified identities"),
                        (INPUTS[11], "62 excluded examples; no automatic admission"),
                        (INPUTS[13], "7 historical seed records; not additional formal growth")):
        rows = documents[path]["records"]
        computed.append({
            "path": path, "scope": scope, "records": len(rows),
            "categories": dict(sorted(Counter(row.get("primary_category", "legacy_scope_unspecified") for row in rows).items())),
            "formula_inventory": [{"id": record_key(row), "formula": row["formula"]} for row in rows],
            "contextual_hits": contextual_hits(rows),
            "recorded_overlap_relations": [{"id": record_key(row), "relations": row["overlap_relations"],
                                            "canonical_relations_sha256": record_hash(row["overlap_relations"])}
                                           for row in rows if row.get("overlap_relations")],
            "limitation": "A finite computed formula or elemental overlap does not establish a formulated polymer/fiber composite identity. No provider query or chemical-equivalence calculation is performed.",
        })
    relationship, examples = documents[INPUTS[14]], documents[INPUTS[15]]
    decisions = [{
        "identity_id": identity_id, "source_designation": label,
        "proposed_name": "Rigid polyurethane foam with nominal " + loading + " wt% bleached Curauá fiber (Członka 2021)",
        "category": "composite", "grade_id": None,
        "nominal_formulation": {"matrix": "study rigid polyurethane foam formulation",
                                "reinforcement": "bleached Curaua fibers",
                                "fiber_loading_wt_percent": loading,
                                "loading_basis": "source-reported total RPUF mass",
                                "composition_basis": "nominal formulation label; not analyzed final composition",
                                "locator": "PDF p.5 Table 2; p.11 method; p.12 total-mass basis; separately verified in source-review.json"},
        "apparent_density_kg_m3": density,
        "decision": "conditionally_distinct_source_qualified_composite_formulation_candidate",
        "reason": "Different nominal bleached Curaua fiber loadings distinguish the three formulations. No matching fiber/matrix formulation is recorded in the finite frozen inventory. Source author/year, labels, processing states and density differences alone do not justify new identities.",
        "label_matches": collisions[label],
        "scope_limit": "No final measured fiber fraction, cellulose purity, cured-network stoichiometry, exact lot equivalence or global chemical uniqueness is established. Bleaching, foam geometry and measurement conditions do not add identities.",
    } for identity_id, label, loading, density in ROWS]
    source_counts = Counter(row["category"] for row in materials["identities"])
    return {
        "schema": "material-batch-finite-identity-review/1", "batch_id": BATCH, "baseline_commit": BASELINE,
        "review_date": "2026-10-25",
        "review_scope": "Finite frozen-catalog identity, alias, formulation-context, source and recorded-relationship audit for three review-only composite candidates. No runtime admission.",
        "scientific_review": False, "scientific_replication": False, "global_chemical_uniqueness_established": False,
        "primary_source_and_rights_review_performed_by_this_audit": False,
        "baseline_counts": {"source_qualified_identities": len(materials["identities"]), "grades": len(materials["grades"]),
                            "states": len(materials["records"]), "reference_properties": len(properties["records"]), "sources": len(sources["records"]),
                            "source_qualified_categories": dict(sorted(source_counts.items())),
                            "existing_formal_computed_records": len(documents[INPUTS[6]]["records"]),
                            "experimental_project_total": len(materials["identities"]) + len(documents[INPUTS[6]]["records"]),
                            "new_admissions_in_this_audit": 0},
        "immutable_inputs": descriptors,
        "input_scope_note": "The established 22-path finite inventory is reacquired at exact ee8c2cd. Published Tian additions are included. This is a declared finite scope, not every external synonym or chemical-equivalence record.",
        "reproduction": {"helper": Path(__file__).resolve().relative_to(ROOT).as_posix(), "helper_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                         "input_acquisition": "git show <baseline_commit>:<POSIX repository path>; hash original bytes; decode strict UTF-8. No working-tree data substitution.",
                         "labels": "All name/source_designation/designation/names values/aliases[].text in every identity, grade and state. Occurrences are not identity counts.",
                         "comparison": "strip/casefold exact; NFKC/casefold/collapsed-whitespace exact; ASCII-alphanumeric exact; separate bounded-token matches. These comparisons are not a chemical-equivalence engine.",
                         "full_record_screen": CONTEXT_PATTERN,
                         "composition_review": "All 30 polymer and 30 composite identity scopes, aliases, evidence, state composition and reinforcement facts are preserved below. Full records across all categories, sources, computed formulas and recorded relationships are screened separately.",
                         "gate": "Existing source-scoped alias/designation and structural-clone compiler gates remain required. This artifact does not replace those checks."},
        "label_inventory": {"field_occurrences_by_collection": occurrence_counts, "field_occurrences_total": len(all_labels),
                            "unique_nfkc_casefold_whitespace_labels": len({normalized(item["text"]) for item in all_labels}),
                            "alias_records_by_collection": alias_counts},
        "candidate_label_comparison": collisions, "full_record_text_screen": record_screen,
        "contextual_hit_dispositions": [
            {"identity_ids": ["mat_ivdre2024_lpo1_rigid_pur", "mat_ivdre2024_lpo2_rigid_pur",
                              "mat_ivdre2024_spo2_rigid_pur", "mat_ivdre2024_spo3_rigid_pur"],
             "disposition": "Existing reactive rigid PUR formulations have explicit Lupranol or suberin/tall-oil-polyol feed recipes and no recorded bleached Curaua-fiber reinforcement. Their recorded recipes are not these three fiber/matrix formulations. Shared polyurethane, catalyst or foam-family context does not establish equivalence; unknown reinforcement fields are not evidence of universally fiber-free chemistry."},
            {"identity_ids": ["mat_aniskevich_2023_ultimaker_tpu95a"],
             "disposition": "Source-qualified thermoplastic polyurethane filament, not a recorded Curaua-reinforced reactive rigid-foam formulation. This is a formulation/family comparison; supplier, color and filament versus foam state alone are not a novelty basis."},
            {"identity_ids": ["mat_kosenko2022_amd5_sps_foam"],
             "disposition": "Polyurethane is a template in the aluminium-foam source context, not the selected material matrix and not Curaua reinforcement."}],
        "whole_input_screen": whole_file_matches,
        "polymer_and_composite_identity_inventory": inventory,
        "composition_and_granularity_review": {
            "candidate_nominal_loadings_are_pairwise_distinct": len({row[2] for row in ROWS}) == len(ROWS),
            "inventory_category_counts": dict(sorted(Counter(row["category"] for row in inventory).items())),
            "assessment": "The finite inventory records no bleached Curaua/rigid-polyurethane formulation. Existing PUR recipes, TPU filament, NBR/carbon-fiber composites, lignin/polyester mixtures, clay/rubber composites, conductive printing compounds, concrete and metal-matrix composites retain their different source-qualified constituents and scopes. No existing generic matrix or plant-fiber identity is duplicated as a candidate.",
            "carbon_fiber_comparison": {"identity_ids": [row["id"] for row in inventory if row["id"].startswith("mat_tamas_benyei2025_nbr_mcf")],
                                        "disposition": "The full inventory includes recycled milled carbon fiber in NBR. Those are different named constituents from bleached Curaua plant fiber in rigid polyurethane; neither CF terminology nor a generic filled-polymer category establishes equivalence."},
            "unreinforced_control": "The source's unreinforced RPUF comparator is excluded; a different study, recipe label or density alone does not justify another polyurethane identity.",
            "limitation": "This does not prove absence of unknown additives or global equivalence. No final lot chemistry, biological equivalence, independent scientific review or raw-data reanalysis is established."},
        "computed_inventory": computed,
        "relationship_inventory": {"runtime_overlay_path": INPUTS[14], "runtime_memberships": len(relationship["memberships"]),
                                   "runtime_relationships": len(relationship["relationships"]), "example_path": INPUTS[15], "example_edges": len(examples),
                                   "runtime_contextual_memberships": contextual_hits(relationship["memberships"]),
                                   "runtime_contextual_relationships": contextual_hits(relationship["relationships"]),
                                   "example_contextual_hits": contextual_hits(examples),
                                   "result": "Finite relationship inputs have no candidate DOI or identity endpoint. Family membership or a constituent link does not create candidate equivalence, inverse scientific claims or propagated properties."},
        "taxonomy_and_wood_inventory": {"taxonomy_migrated_identities": len(documents[INPUTS[3]]["migrated_identity_ids"]),
                                       "baseline_crosswalk_rows": len(documents[INPUTS[4]]),
                                       "reviewed_wood_row_hashes": len(documents[INPUTS[5]]["reviewed_row_sha256"]),
                                       "wood_physical_locators": len(documents[INPUTS[5]]["gwdd_physical_locators"]),
                                       "result": "Taxonomy/wood objects are screened for the candidate DOI, identity IDs and named-fiber context. A botanical name would be constituent context, not this processed fiber/matrix formulation."},
        "candidate_decisions": decisions,
        "candidate_delta": {"identities": 3, "composite": 3, "grades": 0, "states": 3, "properties": 3, "sources": 1},
        "formal_admitted_delta": 0,
        "required_preserved_qualifications": [
            "Nominal 0.1, 0.5 and 1 wt% bleached Curaua additions relative to source-reported total RPUF mass are not analyzed final mass fractions or certified cellulose purity.",
            "Use study-qualified identity names and aliases; literal CF 0.1, CF 0.5 and CF 1 remain source designations. Compact CF0.1/CF0.5/CF1 variants are screened separately. CF does not imply carbon fiber in this source.",
            "One selected apparent-density cell per formulation; processing, foaming, bleaching, specimen geometry and measured value differences do not create additional identities.",
            "The unreinforced control, theoretical density, other properties and unverified statistical interpretations are excluded from this candidate scope.",
            "All measurement conditions, missingness and source/rights details must be preserved in the separate reviewed packet. This identity audit does not independently validate source transcription or licensing."],
        "acceptance_dependencies": ["Separate source-byte, exact authorship, attribution and rights review.",
                                    "Strict compiler/catalog replay and focused candidate regression tests.",
                                    "Independent parent review before runtime admission or experimental publication."],
        "execution_scope": {"artifact": "Candidate-only finite identity audit and reproducible inventory helper", "runtime_catalog_modified": False,
                            "raw_source_assets_included": False, "independent_scientific_review": False, "network_queries": False,
                            "tests_run_by_this_helper": [], "formal_admitted_delta": 0},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Create adjacent review; refuse different existing bytes.")
    mode.add_argument("--check", action="store_true", help="Rebuild frozen inputs and compare every output byte.")
    args = parser.parse_args()
    review = build_review()
    encoded = (json.dumps(review, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
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
                      "labels": review["label_inventory"], "sha256": sha256(encoded).hexdigest()},
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
