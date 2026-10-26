"""Replay the finite Delgado PLA/PCL blend candidate identity audit.

All 22 canonical inputs are reread from frozen Git objects on every invocation.
No network request, source-rights approval, scientific review or admission occurs.
--write creates only the adjacent review and refuses different existing bytes.
--check compares every output byte and never creates or replaces the review.
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
BASELINE = "437950c414ea340eda340babe7b63dee9fcee535"
BATCH = "delgado-pla-pcl-20261026"
DOI = "10.3390/ma13112655"
SOURCE_ID = "delgado_aguilar_2020_pla_pcl"
SOURCE_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC7321633/"
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
    ("mat_delgado2020_pla_pcl_b95_5", "B95/5", "95", "5"),
    ("mat_delgado2020_pla_pcl_b90_10", "B90/10", "90", "10"),
    ("mat_delgado2020_pla_pcl_b85_15", "B85/15", "85", "15"),
    ("mat_delgado2020_pla_pcl_b80_20", "B80/20", "80", "20"),
    ("mat_delgado2020_pla_pcl_b60_40", "B60/40", "60", "40"),
    ("mat_delgado2020_pla_pcl_b40_60", "B40/60", "40", "60"),
    ("mat_delgado2020_pla_pcl_b20_80", "B20/80", "20", "80"),
)
# Family and constituent matches are context, not equivalence decisions.
CONTEXT_PATTERN = (
    r"Delgado|polylacti[cd]|poly[\s(\-]*lactic|poly[\s(\-]*caprolactone|"
    r"caprolactone|Capa\s*6500|4043\s*D|Ingeos|Ingeo|NatureWorks|"
    r"Tough\s*PLA|acryl|conductive|"
    r"(?<![A-Za-z0-9])(?:PLA|PCL|B\s*95\s*[/_-]\s*5|B\s*90\s*[/_-]\s*10|"
    r"B\s*85\s*[/_-]\s*15|B\s*80\s*[/_-]\s*20|B\s*60\s*[/_-]\s*40|"
    r"B\s*40\s*[/_-]\s*60|B\s*20\s*[/_-]\s*80)(?![A-Za-z0-9])|"
    r"10[.]3390/ma13112655"
)
CONTEXT = re.compile(CONTEXT_PATTERN, re.IGNORECASE)
SPECIFIC_PATTERN = (
    r"Delgado|poly[\s(\-]*caprolactone|caprolactone|Capa\s*6500|4043\s*D|"
    r"(?<![A-Za-z0-9])PCL(?![A-Za-z0-9])|10[.]3390/ma13112655"
)
SPECIFIC = re.compile(SPECIFIC_PATTERN, re.IGNORECASE)
COMPARISON_LABELS = tuple(row[1] for row in ROWS) + tuple(
    row[1].replace("/", "_") for row in ROWS
) + tuple(row[1].replace("/", "") for row in ROWS) + (
    "PLA", "PCL", "PLA/PCL", "PLA-PCL", "polylactic acid", "polylactide",
    "polycaprolactone", "Capa 6500", "Capa6500", "4043D",
    "Ingeos Biopolymer 4043D", "Tough PLA", "ToughPLA", "acrylic",
    "conductive PLA", "Protopasta", "Proto-pasta",
)


def normalized(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def ascii_key(text):
    return re.sub("[^a-z0-9]", "", normalized(text))


def raw_text(value):
    return unicodedata.normalize("NFKC", json.dumps(value, ensure_ascii=False, sort_keys=True))


def record_key(record):
    if not isinstance(record, dict):
        return None
    for key in ("id", "candidate_id", "project_material_id", "identity_id", "source_observation_id"):
        if key in record:
            return record[key]
    return None


def record_hash(record):
    return sha256(json.dumps(record, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")).hexdigest()


def record_inventory(rows):
    return {"records": len(rows), "canonical_collection_sha256": record_hash(rows),
            "record_hashes": [{"index": index, "id": record_key(row),
                               "record_sha256": record_hash(row)}
                              for index, row in enumerate(rows)]}


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
    return [{"index": index, "id": record_key(row), "matched_terms": sorted(set(
                match.group(0).casefold() for match in pattern.finditer(raw_text(row)))),
             "record_sha256": record_hash(row)}
            for index, row in enumerate(rows) if pattern.search(raw_text(row))]


def frozen_bytes(path):
    return subprocess.check_output(["git", "show", BASELINE + ":" + path],
                                   cwd=ROOT, timeout=60)


def build_review():
    documents, descriptors, whole_file_matches = {}, [], {}
    for path in INPUTS:
        raw = frozen_bytes(path)
        text = raw.decode("utf-8")
        descriptors.append({"path": path, "bytes": len(raw), "sha256": sha256(raw).hexdigest()})
        whole_file_matches[path] = {
            "candidate_doi_occurrences": text.casefold().count(DOI),
            "candidate_source_id_occurrences": text.count(SOURCE_ID),
            "candidate_identity_id_occurrences": sum(text.count(row[0]) for row in ROWS),
            "context_terms": dict(sorted(Counter(match.group(0).casefold() for match in
                CONTEXT.finditer(unicodedata.normalize("NFKC", text))).items())),
        }
        if path.endswith(".json"):
            documents[path] = json.loads(text)
    materials, properties, sources = (documents[path] for path in INPUTS[:3])
    collections = (("identities", materials["identities"]), ("grades", materials["grades"]),
                   ("states", materials["records"]), ("reference_properties", properties["records"]),
                   ("sources", sources["records"]))
    all_labels, occurrence_counts, alias_counts = [], {}, {}
    for collection in ("identities", "grades", "records"):
        occurrence_counts[collection] = 0
        alias_counts[collection] = sum(len(row.get("aliases", [])) for row in materials[collection])
        for row in materials[collection]:
            for field, label in labels(row):
                all_labels.append({"collection": collection, "id": row["id"], "field": field, "text": label})
                occurrence_counts[collection] += 1
    collisions = {}
    for label in COMPARISON_LABELS:
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
               "candidate_source_or_constituent_grade_hits": contextual_hits(rows, SPECIFIC)}
        for name, rows in collections
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
    source_matches = [row for row in sources["records"] if row["id"] == SOURCE_ID
                      or DOI in raw_text(row).casefold()]
    if source_matches:
        raise ValueError("The proposed new source ID or DOI is already recorded in the frozen baseline.")
    existing_ids = {row["id"] for _, rows in collections for row in rows}
    proposed_state_ids = ["state_" + row[0][4:] + "_injection_molded" for row in ROWS]
    if existing_ids.intersection([row[0] for row in ROWS] + proposed_state_ids):
        raise ValueError("A proposed identity or state ID already exists in the frozen baseline.")
    computed = []
    for path, scope, expected_count in (
            (INPUTS[6], "24 existing formally admitted computed records; not measured source-qualified identities", 24),
            (INPUTS[11], "62 excluded examples; metadata acceptance is not catalog admission", 62),
            (INPUTS[13], "7 historical seed records; not additional formal growth", 7)):
        rows = documents[path]["records"]
        if len(rows) != expected_count:
            raise ValueError("Unexpected frozen computed record count: " + path)
        computed.append({
            "path": path, "scope": scope, **record_inventory(rows),
            "categories": dict(sorted(Counter(row.get("primary_category", "legacy_scope_unspecified") for row in rows).items())),
            "formula_inventory": [{"id": record_key(row), "formula": row["formula"]} for row in rows],
            "contextual_hits": contextual_hits(rows),
            "recorded_overlap_relations": [{"id": record_key(row), "relations": row["overlap_relations"],
                                            "canonical_relations_sha256": record_hash(row["overlap_relations"])}
                                           for row in rows if row.get("overlap_relations")],
            "limitation": "A finite computed formula or elemental overlap does not establish a source-qualified binary polymer blend identity. No provider query, molecular-structure search or chemical-equivalence calculation is performed.",
        })
    relationship, examples, hbn = (documents[path] for path in INPUTS[14:17])
    relationship_collections = {
        "runtime_memberships": relationship["memberships"],
        "runtime_relationships": relationship["relationships"], "example_edges": examples,
        "hbn_source_observations": hbn["source_observations"], "hbn_existing_edges": hbn["existing_edges"],
        "hbn_bridge_edges": hbn["bridge_edges"], "hbn_nodes": hbn["nodes"],
    }
    decisions = [{
        "identity_id": identity_id, "source_designation": label,
        "state_id": "state_" + identity_id[4:] + "_injection_molded",
        "proposed_name": "Nominal PLA/PCL " + pla + "/" + pcl + " mass blend (Delgado-Aguilar 2020)",
        "category": "polymer", "grade_id": None,
        "nominal_formulation": {
            "constituents": ["source PLA, Ingeos Biopolymer 4043D", "source PCL, Capa 6500"],
            "pla_wt_percent": pla, "pcl_wt_percent": pcl,
            "composition_basis": "source-reported nominal binary blend mass percentages; not measured final composition",
            "locator": "Table 1, row " + label + "; section 2.1 constituent designations",
            "grade_scope": "Constituent product designations do not establish a commercial grade for the blend.",
            "coupling_agent": "Source reports no coupling agent; this is not a claim of analytical purity or absence of all unknown additives.",
        },
        "property_scope": {"quantity": "youngs_modulus", "selected_properties": 1,
                           "locator": "Table 2, composition linked to Table 1 row " + label},
        "decision": "conditionally_distinct_source_qualified_binary_polymer_blend_candidate",
        "reason": "The explicitly specified PLA/PCL nominal mass ratio distinguishes this binary blend from the other six candidate ratios. The finite inventory does not record this source-qualified binary recipe. Source author/year, bare labels, different processing, injection-molded geometry and measured-value differences alone are not identity evidence.",
        "label_matches": collisions[label],
        "scope_limit": "Unknown formulations of existing PLA products prevent a global chemical-inequivalence claim. Neither final composition, purity, lot equivalence nor universal uniqueness is established. Constituent grades are context only, not new grade records.",
    } for identity_id, label, pla, pcl in ROWS]
    source_counts = Counter(row["category"] for row in materials["identities"])
    return {
        "schema": "material-batch-finite-identity-review/1", "batch_id": BATCH, "baseline_commit": BASELINE,
        "review_date": "2026-10-26",
        "review_scope": "Finite frozen-catalog identity, alias, formulation, source and recorded-relationship audit for seven candidate-only PLA/PCL polymer blends. No runtime admission.",
        "scientific_review": False, "scientific_replication": False, "global_chemical_uniqueness_established": False,
        "primary_source_and_rights_review_performed_by_this_audit": False,
        "baseline_counts": {
            "source_qualified_identities": len(materials["identities"]), "grades": len(materials["grades"]),
            "states": len(materials["records"]), "reference_properties": len(properties["records"]),
            "sources": len(sources["records"]), "source_qualified_categories": dict(sorted(source_counts.items())),
            "existing_formal_computed_records": len(documents[INPUTS[6]]["records"]),
            "excluded_computed_examples": len(documents[INPUTS[11]]["records"]),
            "experimental_project_total": len(materials["identities"]) + len(documents[INPUTS[6]]["records"]),
            "new_admissions_in_this_audit": 0,
        },
        "immutable_inputs": descriptors,
        "input_scope_note": "The established 22-path canonical inventory is reacquired at exact 437950c414ea340eda340babe7b63dee9fcee535. File-byte hashes cover complete inputs; record inventories cover every material identity, grade, state, property, source, admitted/excluded computed row and listed relationship record. This is a declared finite scope, not every external synonym or chemical-equivalence database.",
        "reproduction": {
            "helper": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "helper_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "record_sha256_method": "SHA-256 of compact sorted JSON encoded as UTF-8 with ensure_ascii=False, sort_keys=True and separators=(',', ':'), without a trailing LF. This is not the compiler record pin, whose serialized input includes a trailing LF.",
            "input_acquisition": "git show <baseline_commit>:<POSIX repository path>; hash original bytes; decode strict UTF-8. No working-tree data substitution or cross-call cache.",
            "labels": "All name/source_designation/designation/names values/aliases[].text in every identity, grade and state. Occurrences are not identity counts.",
            "comparison": "strip/casefold exact; NFKC/casefold/collapsed-whitespace exact; ASCII-alphanumeric exact; separate bounded-token matches. Slash, underscore and compact candidate labels are screened explicitly. These comparisons are not a chemical-equivalence engine.",
            "full_record_screen": CONTEXT_PATTERN, "specific_constituent_screen": SPECIFIC_PATTERN,
            "composition_review": "All current polymer/composite scopes, aliases, evidence, state composition and reinforcement facts are retained below. All-category records, sources, computed formulas and relationships are screened separately.",
            "gate": "Existing source-scoped alias/designation and structural-clone compiler gates remain required. This artifact does not replace those checks.",
        },
        "full_record_inventory": {name: record_inventory(rows) for name, rows in collections},
        "label_inventory": {
            "field_occurrences_by_collection": occurrence_counts, "field_occurrences_total": len(all_labels),
            "unique_nfkc_casefold_whitespace_labels": len({normalized(item["text"]) for item in all_labels}),
            "alias_records_by_collection": alias_counts,
        },
        "candidate_label_comparison": collisions, "full_record_text_screen": record_screen,
        "whole_input_screen": whole_file_matches, "polymer_and_composite_identity_inventory": inventory,
        "source_identity_review": {
            "proposed_source_id": SOURCE_ID, "doi": DOI, "official_url": SOURCE_URL,
            "exact_source_id_or_doi_matches": source_matches,
            "disposition": "No existing source ID or matching DOI occurs in the finite frozen source registry. One new source is proposed, subject to separate source/rights review; a new paper alone does not establish new material identities.",
        },
        "contextual_hit_dispositions": [
            {
                "identity_ids": ["mat_porima_pla_sahin_2026"],
                "disposition": "This is a source-qualified Porima PLA product with unreported full formulation, molecular chemistry, SKU, grade and additives. Its PLA and PLA-filament aliases are family/product context, not a recorded PLA/PCL mass-ratio recipe. Do not relabel it pure PLA, infer absence of PCL, or establish distinction from it merely by supplier, year or injection molding versus printing.",
            },
            {
                "identity_ids": ["mat_aniskevich_2023_ultimaker_tough_pla"],
                "disposition": "Existing Tough PLA is one source-qualified PLA/unspecified-acrylic-polymer formulation family with Black and White states, not two identities. The recorded constituent context differs from the candidate PLA/PCL binary recipes, but the acrylic chemistry, fractions, pigments, full recipes and lot equivalence remain unknown. Acrylic polymer is not automatically PMMA; an unknown additional constituent is not proven absent. Tough PLA and PLA Tough aliases do not establish equivalence to any candidate ratio.",
            },
            {
                "identity_ids": ["mat_aniskevich_2023_protopasta_conductive_pla"],
                "disposition": "Existing Proto-pasta conductive PLA has verified PLA/dispersant/conductive-carbon-black constituent context, with unestablished full recipe and constituent fractions. Its verified carbon-black context distinguishes the recorded formulation scope from the candidate binary PLA/PCL recipes. Conductivity, SKU, batch label, color, supplier and different modulus values alone are not identity evidence; no universal absence of PCL in unknown additives is inferred.",
            },
            {
                "identity_ids": ["mat_arbelaiz2024_latxa_wool"],
                "disposition": "PLA appears in source context and in an explicit exclusion. The admitted identity is standalone soap-cleaned Latxa wool; the paper's PLA composites are not admitted under that wool identity and provide no candidate binary-blend equivalence.",
            },
            {
                "identity_ids": [],
                "disposition": "No recorded PCL/polycaprolactone, Capa 6500 or 4043D constituent or grade match occurs in the screened baseline identity, grade, state, property or source records. This finite absence does not admit neat endpoints, prove global uniqueness or justify a separate blend grade. Complete matching modes, contextual hits and record hashes are retained for review.",
            },
        ],
        "composition_and_granularity_review": {
            "candidate_mass_ratios_are_pairwise_distinct": len({(row[2], row[3]) for row in ROWS}) == len(ROWS),
            "candidate_mass_percent_pairs_each_sum_to_100": all(int(row[2]) + int(row[3]) == 100 for row in ROWS),
            "inventory_category_counts": dict(sorted(Counter(row["category"] for row in inventory).items())),
            "assessment": "The finite inventory has no recorded candidate PLA/PCL binary mass-ratio recipe. Candidate identities rest on explicit nominal constituent ratios, with study qualification limiting the claim. Existing unknown commercial recipes remain unknown; lack of a recorded PCL alias is not evidence of universal absence of PCL.",
            "classification": "Binary thermoplastic polymer blends are classified polymer. Blending two polymers alone is not evidence for a reinforced-composite classification.",
            "neat_endpoints": "Neat PLA and neat PCL are excluded. No new endpoint identity, grade, state or property is proposed, even where a constituent grade is absent from the finite inventory.",
            "table_2_volume_fraction": "Table 2 PCL volume fractions are source-calculated from density and serve only the reviewed composition-row join. They are not measured final compositions, additional identities or substituted mass fractions.",
            "limitation": "No analytical final composition, exact lot equivalence, global chemical uniqueness, independent scientific review or raw-data reanalysis is established. Different processing or measurement alone does not create a new identity.",
        },
        "computed_inventory": computed,
        "computed_metadata_lineage_inventory": {
            path: record_inventory(documents[path]["records"])
            for path in (INPUTS[7], INPUTS[8], INPUTS[10])
        },
        "computed_acceptance_scope": {
            "formal_admitted_count": 24, "excluded_example_count": 62,
            "first_acceptance_pin": documents[INPUTS[9]], "second_acceptance_pin": documents[INPUTS[12]],
            "disposition": "The 24 existing formal computed records remain separate from measured source-qualified materials. The 62 second-batch examples have exact metadata acceptance only and remain excluded from formal counts. Historical seven-record seed metadata are not counted as new growth. None is newly admitted by this audit.",
        },
        "relationship_inventory": {
            "runtime_overlay_path": INPUTS[14], "runtime_memberships": len(relationship["memberships"]),
            "runtime_relationships": len(relationship["relationships"]), "example_path": INPUTS[15],
            "example_edges": len(examples), "hbn_projection_path": INPUTS[16],
            "complete_collection_inventories": {name: record_inventory(rows) for name, rows in relationship_collections.items()},
            "contextual_hits_by_collection": {name: contextual_hits(rows) for name, rows in relationship_collections.items()},
            "result": "No candidate identity endpoint is recorded in the frozen relationships. Family membership, shared constituents, an alias or a computed formula does not imply blend equivalence, inverse scientific claims or inherited properties. No new relationship is asserted here.",
        },
        "taxonomy_and_wood_inventory": {
            "taxonomy_migrated_identities": len(documents[INPUTS[3]]["migrated_identity_ids"]),
            "baseline_crosswalk_rows": len(documents[INPUTS[4]]),
            "reviewed_wood_row_hashes": len(documents[INPUTS[5]]["reviewed_row_sha256"]),
            "wood_physical_locators": len(documents[INPUTS[5]]["gwdd_physical_locators"]),
            "result": "Complete taxonomy and wood file bytes are hash-bound and screened for source DOI, candidate IDs and formulation context. Generic natural-polymer or constituent context does not establish a PLA/PCL binary blend identity.",
        },
        "candidate_decisions": decisions,
        "candidate_delta": {"identities": 7, "polymer": 7, "grades": 0, "states": 7, "properties": 7, "sources": 1},
        "formal_admitted_delta": 0,
        "required_preserved_qualifications": [
            "Table 1 nominal PLA/PCL mass percentages distinguish the seven candidates. Do not substitute source-calculated Table 2 volume fractions or claim measured final compositions.",
            "Retain source-qualified names and aliases. B95/5, B90/10, B85/15, B80/20, B60/40, B40/60 and B20/80 are study designations, not globally unique grades.",
            "PLA Ingeos Biopolymer 4043D and PCL Capa 6500 are constituent context only; each newly formulated blend has grade_id null. No neat endpoint is admitted.",
            "Existing Tough PLA and other products with unknown formulations remain unresolved for global equivalence; absence of a recorded matching recipe is a finite catalog conclusion only.",
            "One source-reported Young's-modulus property per injection-molded blend state. Processing, geometry, test conditions and measured values do not supply new-identity evidence.",
            "Separate source review must preserve the printed central values, reported SD and unknown central aggregation, measurement and sample scope without inferring means or replicate counts. No source assets or other properties are included by this audit.",
        ],
        "acceptance_dependencies": [
            "Separate primary-source, exact authorship, formulation-row join, attribution and rights review.",
            "Strict compiler/catalog replay and focused candidate regression tests including alias/structural-clone gates.",
            "Independent parent review before any runtime admission or publication.",
        ],
        "execution_scope": {
            "artifact": "Candidate-only finite identity audit and reproducible inventory helper",
            "runtime_catalog_modified": False, "raw_source_assets_included": False,
            "independent_scientific_review": False, "network_queries": False,
            "tests_run_by_this_helper": [], "formal_admitted_delta": 0,
        },
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
