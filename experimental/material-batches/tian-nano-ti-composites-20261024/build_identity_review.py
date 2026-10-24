"""Reproduce a finite Tian candidate identity audit from frozen Git objects.

This local evidence helper performs no network request or runtime admission.
--write creates only the adjacent review; existing different bytes are refused.
--check rereads all inputs and compares every review byte. No cross-call cache.
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
BASELINE = "5a9a85c573f590d206cddb4cb7c085f334a0fbc0"
BATCH = "tian-nano-ti-composites-20261024"
DOI = "10.3390/ma16062407"
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
# Literal table labels and source-qualified nominal loadings are separate facts.
ROWS = (
    ("mat_tian2023_az31_ti_0p5wt", "0.5 wt% Ti", "0.5", "1.7425"),
    ("mat_tian2023_az31_ti_1wt", "1 wt Ti", "1", "1.7442"),
)
CONTEXT_PATTERN = (
    r"(?<![A-Za-z0-9])(?:AZ31|Ti|Tian)(?![A-Za-z0-9])|"
    r"titanium|magnesium|nano[- ]?Ti|Mg[- \u2013]3Al[- \u2013]1Zn|10\.3390/ma16062407"
)
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
        if alias["text"].strip():
            yield "aliases[" + str(index) + "].text", alias["text"]


def raw_text(value):
    return unicodedata.normalize("NFKC", json.dumps(value, ensure_ascii=False, sort_keys=True))


def record_key(record):
    return record.get("id", record.get("candidate_id", record.get("project_material_id", record.get("identity_id"))))


def record_hash(record):
    return sha256(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def contextual_hits(rows):
    return [{"id": record_key(row), "matched_terms": sorted(set(
                match.group(0).casefold() for match in CONTEXT.finditer(raw_text(row)))),
             "record_sha256": record_hash(row)}
            for row in rows if CONTEXT.search(raw_text(row))]


def build_review():
    documents, descriptors, whole_file_matches = {}, [], {}
    for path in INPUTS:
        raw = subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT, timeout=60)
        text = raw.decode("utf-8")
        descriptors.append({"path": path, "bytes": len(raw), "sha256": sha256(raw).hexdigest()})
        whole_file_matches[path] = {
            "candidate_doi_occurrences": text.casefold().count(DOI),
            "candidate_identity_id_occurrences": sum(text.count(row[0]) for row in ROWS),
            "context_terms": dict(sorted(Counter(match.group(0).casefold() for match in CONTEXT.finditer(
                unicodedata.normalize("NFKC", text))).items())),
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
    # Include the literal labels, normalized nominal loading label and matrix
    # context. A bare matrix hit is retained, never treated as candidate novelty.
    for label in ("0.5 wt% Ti", "1 wt Ti", "1 wt% Ti", "AZ31", "Mg-3Al-1Zn"):
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
        name: {"records_scanned": len(rows), "contextual_hits": contextual_hits(rows)}
        for name, rows in (("identities", materials["identities"]), ("grades", materials["grades"]),
                           ("states", materials["records"]), ("reference_properties", properties["records"]),
                           ("sources", sources["records"]))
    }
    inventory = []
    for identity in materials["identities"]:
        if identity["category"] not in {"metal", "composite"}:
            continue
        states = [state for state in materials["records"] if state["identity_id"] == identity["id"]]
        inventory.append({
            "id": identity["id"], "category": identity["category"], "name": identity["name"],
            "aliases": identity["aliases"], "identity_scope": identity["identity_scope"],
            "evidence": identity["evidence"],
            "states": [{"id": state["id"], "source_designation": state["source_designation"],
                        "grade_id": state["grade_id"], "composition_or_purity": state["state"]["composition_or_purity"],
                        "reinforcement": state["state"]["reinforcement"]} for state in states],
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
            "contains_magnesium_and_titanium": [record_key(row) for row in rows
                if {"Mg", "Ti"}.issubset(set(re.findall(r"[A-Z][a-z]?", row["formula"])))],
            "recorded_overlap_relations": [{"id": record_key(row), "relations": row["overlap_relations"],
                                            "canonical_relations_sha256": record_hash(row["overlap_relations"])}
                                           for row in rows if row.get("overlap_relations")],
            "limitation": "Finite formula and overlap metadata do not establish a processed metal-matrix composite identity. No provider query or chemical-equivalence calculation is performed.",
        })
    relationship, examples = documents[INPUTS[14]], documents[INPUTS[15]]
    comparator = next(row for row in inventory if row["id"] == "mat_chen2023_az31")
    decisions = [{
        "identity_id": identity_id, "source_designation": label,
        "proposed_name": "Mg-3Al-1Zn / " + loading + " wt% nano-Ti composite (Tian 2023)",
        "category": "composite", "grade_id": None,
        "nominal_formulation": {"matrix": "Mg-3Al-1Zn (AZ31)", "reinforcement": "nano-Ti",
                                "reinforcement_loading_wt_percent": loading,
                                "composition_basis": "author-reported nominal reinforcement loading; not analyzed final composition",
                                "locator": "Sections 2.1-2.2 and original Table 2, PDF page 4"},
        "actual_density_g_cm3": density,
        "decision": "conditionally_distinct_source_qualified_composite_formulation_candidate",
        "reason": "The two nominal Ti reinforcement loadings distinguish source-qualified formulations, not specimens or processing states. The finite baseline has no matching reinforced identity, candidate DOI or exact formulation-label collision. Density differences and a new study citation alone do not establish identity novelty.",
        "label_matches": collisions[label],
        "scope_limit": "The named matrix and nominal reinforcement loading are not certified purity, measured final mass fractions, exact lot chemistry, or global chemical uniqueness. As-extruded state does not add another identity.",
    } for identity_id, label, loading, density in ROWS]
    return {
        "schema": "material-batch-finite-identity-review/1", "batch_id": BATCH, "baseline_commit": BASELINE,
        "review_date": "2026-10-24",
        "review_scope": "Finite frozen-catalog identity, alias, composition-context, source and recorded-relationship audit for two review-only composite candidates. No runtime admission.",
        "scientific_review": False, "scientific_replication": False, "global_chemical_uniqueness_established": False,
        "primary_source_and_rights_review_performed_by_this_audit": False,
        "baseline_counts": {"source_qualified_identities": len(materials["identities"]), "grades": len(materials["grades"]),
                            "states": len(materials["records"]), "reference_properties": len(properties["records"]), "sources": len(sources["records"]),
                            "source_qualified_categories": dict(sorted(Counter(row["category"] for row in materials["identities"]).items())),
                            "existing_formal_computed_records": len(documents[INPUTS[6]]["records"]),
                            "experimental_project_total": len(materials["identities"]) + len(documents[INPUTS[6]]["records"]),
                            "new_admissions_in_this_audit": 0},
        "immutable_inputs": descriptors,
        "input_scope_note": "The established 22-path finite inventory was reacquired at exact 5a9a85c. Published Kapoor additions are included; no old input hashes or counts are substituted. This is a declared finite scope, not every possible external synonym or equivalence record.",
        "reproduction": {"helper": Path(__file__).resolve().relative_to(ROOT).as_posix(), "helper_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                         "input_acquisition": "git show <baseline_commit>:<POSIX repository path>; hash original bytes; decode strict UTF-8. No working-tree data substitution.",
                         "labels": "All name/source_designation/designation/names values/aliases[].text in every identity, grade and state. Occurrences are not identity counts.",
                         "comparison": "strip/casefold exact; NFKC/casefold/collapsed-whitespace exact; ASCII-alphanumeric exact; separate bounded-token matches. Literal and normalized source labels are screened separately.",
                         "full_record_screen": CONTEXT_PATTERN,
                         "composition_review": "All 32 metal and 28 composite identity scopes, evidence, state composition and reinforcement facts are preserved below for review. Full records in all categories, source records, finite computed formulas and recorded relationships are screened. Text normalization is not a chemical-equivalence engine.",
                         "gate": "Retain source-scoped label collisions and structural-clone rejection in the existing compiler/catalog. This artifact does not replace those checks."},
        "label_inventory": {"field_occurrences_by_collection": occurrence_counts, "field_occurrences_total": len(all_labels),
                            "unique_nfkc_casefold_whitespace_labels": len({normalized(item["text"]) for item in all_labels}),
                            "alias_records_by_collection": alias_counts},
        "candidate_label_comparison": collisions, "full_record_text_screen": record_screen,
        "contextual_hit_dispositions": [
            {"identity_ids": ["mat_chen2023_az31"],
             "disposition": "Different-study unreinforced AZ31 identity and its grade/state/property/source context; no Ti reinforcement is assigned to that comparator. The existing source discusses nano-TC4 composites, but neither those contextual composites nor Tian's unreinforced comparator are proposed here."},
            {"identity_ids": ["mat_hydro_6061", "mat_puga2015_az91d"],
             "disposition": "Aluminium-magnesium-silicon 6061 and AZ91D are different named alloy formulations; a magnesium component or magnesium-alloy family word does not identify an AZ31/nano-Ti composite."},
            {"identity_ids": ["mat_timet_timetal6_4_grade5"],
             "disposition": "TIMETAL 6-4 is a titanium-aluminium-vanadium alloy, not Ti nanoparticles reinforcing a Mg-3Al-1Zn matrix. Its source and alloy-membership contexts do not establish candidate equivalence."},
            {"identity_ids": ["mat_kosenko2022_amd5_sps_foam"],
             "disposition": "The AMD5 input is 94.8 wt.% Al, 4.8 wt.% Mg and 0.4 wt.% Ti, with salt-space-holder processing. An aluminium-based foam containing Mg/Ti is not either selected Mg-3Al-1Zn/nano-Ti formulation; input composition is not a final bulk assay."},
            {"identity_ids": ["mat_nbs1953_mgo", "mat_nbs1953_tio2", "mat_nbs1953_mg2sio4", "mat_nbs1953_mgwo4"],
             "disposition": "The magnesium/titanium oxide and silicate/tungstate composition-level inorganic identities are component-context hits, not these reinforced metallic formulations."},
            {"identity_ids": ["mat_nbs1953_pb"],
             "disposition": "Faint magnesium traces in the NBS lead state do not identify an AZ31 matrix or a Ti-reinforced formulation."},
            {"identity_ids": ["mat_outokumpu_321", "mat_outokumpu_4622"],
             "disposition": "The typical steel-composition Others cells contain Ti (and for 4622, Nb/Cu); these unquantified additions do not identify a Mg-3Al-1Zn/nano-Ti composite."}],
        "whole_input_screen": whole_file_matches,
        "metal_and_composite_identity_inventory": inventory,
        "composition_and_granularity_review": {
            "candidate_nominal_loadings_are_pairwise_distinct": len({row[2] for row in ROWS}) == len(ROWS),
            "inventory_category_counts": dict(sorted(Counter(row["category"] for row in inventory).items())),
            "assessment": "Existing composites are concrete or polymer-matrix formulations; none in the finite inventory is the selected Mg-3Al-1Zn/nano-Ti formulation. The AZ31 comparator, AZ91D alloy, titanium alloy, Al-Mg-Ti foam and trace/component Ti or Mg references are not recorded matches for either reinforced formulation. A matrix or constituent overlap does not establish equivalence.",
            "az31_context": {"existing_identity_id": comparator["id"], "existing_name": comparator["name"],
                             "existing_identity_scope": comparator["identity_scope"],
                             "disposition": "The Chen 2023 identity is an unreinforced different-study AZ31 comparator. Do not assert identical historical lot/composition with Tian's comparator, add the Tian unreinforced comparator as growth, or confuse Chen's source-context nano-TC4 composites with these nominal nano-Ti loadings."},
            "limitation": "No global equivalence registry, unrecorded composition, exact lot chemistry, independent scientific review or raw-data reanalysis is established. Source-specific labels alone never justify a new identity."},
        "computed_inventory": computed,
        "relationship_inventory": {"runtime_overlay_path": INPUTS[14], "runtime_memberships": len(relationship["memberships"]),
                                   "runtime_relationships": len(relationship["relationships"]), "example_path": INPUTS[15], "example_edges": len(examples),
                                   "runtime_contextual_memberships": contextual_hits(relationship["memberships"]),
                                   "runtime_contextual_relationships": contextual_hits(relationship["relationships"]),
                                   "example_contextual_hits": contextual_hits(examples),
                                   "result": "No candidate DOI or candidate identity endpoint occurs in the finite relationship inputs. The recorded titanium-alloy membership context and other family/constituent links do not create inverse identity claims, candidate equivalence or propagated properties."},
        "taxonomy_and_wood_inventory": {"taxonomy_migrated_identities": len(documents[INPUTS[3]]["migrated_identity_ids"]),
                                       "baseline_crosswalk_rows": len(documents[INPUTS[4]]),
                                       "reviewed_wood_row_hashes": len(documents[INPUTS[5]]["reviewed_row_sha256"]),
                                       "wood_physical_locators": len(documents[INPUTS[5]]["gwdd_physical_locators"]),
                                       "result": "Finite taxonomy/wood inputs contain no candidate DOI or candidate identity ID. Context-term counts, including any incidental author/name strings, remain visible in whole_input_screen."},
        "candidate_decisions": decisions,
        "candidate_delta": {"identities": 2, "composite": 2, "grades": 0, "states": 2, "properties": 2, "sources": 1},
        "formal_admitted_delta": 0,
        "required_preserved_qualifications": [
            "The Mg-3Al-1Zn matrix and 0.5/1 wt% nano-Ti loadings are source-qualified nominal formulations, not analyzed final compositions or certified grades.",
            "Retain the literal Table 2 labels '0.5 wt% Ti' and '1 wt Ti'; the second omits the percent sign, while the methods establish nominal 1 wt%. Use study-qualified identity names and aliases.",
            "One as-extruded state and one Actual Density cell per formulation; no new identity for extrusion, measurement repeats or a density value.",
            "Digital densimeter is the reported density method. Temperature, pressure, humidity, specimen count, repeats, aggregation, uncertainty, density basis and porosity remain unspecified for density.",
            "Do not transfer tensile sample count n=3 or tensile room temperature to density. Do not include theoretical density, tensile data or the unreinforced AZ31 comparator.",
            "Source-byte, archive-manifest and license evidence are in the separate source review; this finite identity audit does not independently validate those facts."],
        "acceptance_dependencies": ["Separate source-byte, attribution and rights review.", "Strict compiler/catalog replay and focused candidate regression tests.",
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
