"""Replay the finite Ewurum reactive-formulation candidate identity audit.

The 22 canonical inputs are read from exact frozen Git objects. Two earlier
packet reviews are separately hash-bound evidence of their limited scope.
No source download, license approval, scientific review or admission occurs.
--write creates only the adjacent review and refuses different existing bytes.
--check rereads all inputs and compares every output byte. No cross-call cache.
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
BASELINE = "8ccd217599fd462d13d7435bdfb02a0825e4eacd"
BATCH = "ewurum-reactive-20261025"
DOI = "10.3390/polym17020194"
SOURCE_ID = "ewurum_mcdonald_2025_pbs_lignin"
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
PRIOR_SCOPE_INPUTS = (
    "experimental/material-batches/20261017-pbs-lignin-blends/review.json",
    "experimental/material-batches/20261019-pbs-lignin45/review.json",
)
ROWS = (
    ("mat_ewurum2025_pbs_lignin_r10", "R10", "10"),
    ("mat_ewurum2025_pbs_lignin_r20", "R20", "20"),
    ("mat_ewurum2025_pbs_lignin_r30", "R30", "30"),
    ("mat_ewurum2025_pbs_lignin_r45", "R45", "45"),
)
EXISTING_SOURCE_IDENTITIES = {
    "mat_ewurum2025_biopbs": "B0",
    "mat_ewurum2025_indulin_at": "Lignin; Indulin AT",
    "mat_ewurum2025_pbs_lignin10": "B10",
    "mat_ewurum2025_pbs_lignin20": "B20",
    "mat_ewurum2025_pbs_lignin30": "B30",
    "mat_ewurum2025_pbs_lignin45": "B45",
}
CONTEXT_PATTERN = (
    r"Ewurum|lignin|lignosulphonate|lignosulfonate|Indulin|Bio\s*PBS|"
    r"polybutylene\s+succinate|dicumyl|FZ\s*91|"
    r"(?<![A-Za-z0-9])(?:PBS|PBAT|DCP|R0|R10|R20|R30|R45|B0|B10|B20|B30|B45)(?![A-Za-z0-9])|"
    r"10[.]3390/polym17020194"
)
CONTEXT = re.compile(CONTEXT_PATTERN, re.IGNORECASE)
SPECIFIC = re.compile(
    r"Ewurum|Indulin|dicumyl|(?<![A-Za-z0-9])(?:DCP|R0|R10|R20|R30|R45)(?![A-Za-z0-9])|"
    r"10[.]3390/polym17020194", re.IGNORECASE
)


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
    for label in ("R0", "R10", "R20", "R30", "R45", "R 10", "R 20", "R 30", "R 45",
                  "B0", "B10", "B20", "B30", "B45", "PBS", "DCP", "Indulin AT", "BioPBS"):
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
               "source_or_reactive_formulation_hits": contextual_hits(rows, SPECIFIC)}
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
    source_matches = [source for source in sources["records"] if source["id"] == SOURCE_ID]
    if len(source_matches) != 1 or source_matches[0].get("doi") != DOI:
        raise ValueError("The existing source identity and DOI must match exactly.")
    reused_source = source_matches[0]
    source_properties = [row for row in properties["records"] if row["source_id"] == SOURCE_ID]
    source_state_ids = {row["material_state_id"] for row in source_properties}
    source_states = [row for row in materials["records"] if row["id"] in source_state_ids]
    source_map = {row["identity_id"]: row["source_designation"] for row in source_states}
    if source_map != EXISTING_SOURCE_IDENTITIES or len(source_states) != len(EXISTING_SOURCE_IDENTITIES):
        raise ValueError("The complete existing Ewurum source/property/state/identity join changed.")
    if any(row[0] in {identity["id"] for identity in materials["identities"]} for row in ROWS):
        raise ValueError("A proposed identity already exists in the frozen baseline.")
    source_join = []
    for state in source_states:
        identity = next(row for row in materials["identities"] if row["id"] == state["identity_id"])
        source_join.append({
            "identity_id": identity["id"], "identity_sha256": record_hash(identity),
            "identity_scope": identity["identity_scope"], "aliases": identity["aliases"],
            "state_id": state["id"], "state_sha256": record_hash(state),
            "source_designation": state["source_designation"],
            "composition_or_purity": state["state"]["composition_or_purity"],
            "properties": [{"id": prop["id"], "record_sha256": record_hash(prop)}
                           for prop in source_properties if prop["material_state_id"] == state["id"]],
        })
    prior_scope = []
    for path in PRIOR_SCOPE_INPUTS:
        raw = frozen_bytes(path)
        review = json.loads(raw.decode("utf-8"))
        prior_scope.append({"path": path, "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
                            "identity_policy": review["identity_policy"], "excluded": review["excluded"],
                            "specific_unresolved_admission_gaps": review["specific_unresolved_admission_gaps"]})
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
            "limitation": "Finite computed formulas and elemental overlap do not establish formulated PBS/lignin/DCP identity. No provider query or chemical-equivalence calculation is performed.",
        })
    relationship, examples = documents[INPUTS[14]], documents[INPUTS[15]]
    decisions = [{
        "identity_id": identity_id, "source_designation": label,
        "proposed_name": "DCP-reactive PBS / " + loading + " wt.% Indulin AT kraft-lignin formulation, " + label + " (Ewurum 2025)",
        "category": "composite", "grade_id": None,
        "nominal_formulation": {"matrix": "source BioPBS FZ91PM/FZ91PB; single grade unresolved",
                                "reinforcement": "Indulin AT softwood kraft lignin",
                                "lignin_loading_wt_percent": loading,
                                "loading_basis": "source-reported total polymer mass",
                                "reactive_additive": "source-reported 0.25 wt.% dicumyl peroxide addition to PBS",
                                "dcp_denominator_resolved": False,
                                "composition_basis": "source-qualified nominal reactive formulation; not analyzed final composition",
                                "locator": "PDF p.3 sections 2.1-2.3; source distinctions and Table 1 gel fractions reviewed separately"},
        "decision": "conditionally_distinct_source_qualified_composite_formulation_candidate",
        "reason": "The R-series includes the DCP reactive additive absent from the separately cataloged B-series recipes. The source reports nonzero gel fractions for these four lignin-containing reactive formulations, supporting reaction distinction without establishing exact final network chemistry. Different nominal lignin loadings distinguish the four candidates. Processing alone, author/year, labels, and property differences do not justify new identities.",
        "label_matches": collisions[label],
        "scope_limit": "No exact final DCP residue, graft yield, crosslink density, network architecture, analyzed final mass fractions or single BioPBS grade is established. Gel fraction is supporting source context, not an extra admitted property in this batch.",
    } for identity_id, label, loading in ROWS]
    source_counts = Counter(row["category"] for row in materials["identities"])
    return {
        "schema": "material-batch-finite-identity-review/1", "batch_id": BATCH, "baseline_commit": BASELINE,
        "review_date": "2026-10-25",
        "review_scope": "Finite frozen-catalog identity, alias, formulation-context, reused-source and recorded-relationship audit for four review-only reactive PBS/lignin candidates. No runtime admission.",
        "scientific_review": False, "scientific_replication": False, "global_chemical_uniqueness_established": False,
        "primary_source_and_rights_review_performed_by_this_audit": False,
        "baseline_counts": {"source_qualified_identities": len(materials["identities"]), "grades": len(materials["grades"]),
                            "states": len(materials["records"]), "reference_properties": len(properties["records"]), "sources": len(sources["records"]),
                            "source_qualified_categories": dict(sorted(source_counts.items())),
                            "existing_formal_computed_records": len(documents[INPUTS[6]]["records"]),
                            "experimental_project_total": len(materials["identities"]) + len(documents[INPUTS[6]]["records"]),
                            "new_admissions_in_this_audit": 0},
        "immutable_inputs": descriptors,
        "input_scope_note": "The established 22-path canonical inventory is reread at exact 8ccd217. Two older packet reviews are separately bound below as scope evidence, not additional canonical catalogs. This is a declared finite scope, not every external synonym or chemical-equivalence record.",
        "reproduction": {"helper": Path(__file__).resolve().relative_to(ROOT).as_posix(), "helper_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                         "record_sha256_method": "SHA-256 of compact sorted JSON encoded as UTF-8 with ensure_ascii=False, sort_keys=True and separators=(',', ':'), without a trailing LF. This is not the compiler record pin, whose serialized input includes a trailing LF.",
                         "input_acquisition": "git show <baseline_commit>:<POSIX repository path>; hash original bytes; decode strict UTF-8. No working-tree data substitution.",
                         "labels": "All name/source_designation/designation/names values/aliases[].text in every identity, grade and state. Occurrences are not identity counts.",
                         "comparison": "strip/casefold exact; NFKC/casefold/collapsed-whitespace exact; ASCII-alphanumeric exact; separate bounded-token matches. These comparisons are not a chemical-equivalence engine.",
                         "full_record_screen": CONTEXT_PATTERN,
                         "composition_review": "All current polymer/composite scopes, aliases, evidence, state composition and reinforcement facts are retained below. All-category records, sources, computed formulas and relationships are screened separately.",
                         "gate": "Existing source-scoped alias/designation and structural-clone compiler gates remain required. This artifact does not replace those checks."},
        "label_inventory": {"field_occurrences_by_collection": occurrence_counts, "field_occurrences_total": len(all_labels),
                            "unique_nfkc_casefold_whitespace_labels": len({normalized(item["text"]) for item in all_labels}),
                            "alias_records_by_collection": alias_counts},
        "candidate_label_comparison": collisions, "full_record_text_screen": record_screen,
        "whole_input_screen": whole_file_matches,
        "polymer_and_composite_identity_inventory": inventory,
        "existing_source_review": {"source_id": SOURCE_ID, "doi": DOI, "source_record_sha256": record_hash(reused_source),
                                   "source_record_reused_unchanged": True, "source_record": reused_source,
                                   "existing_source_property_state_identity_join": source_join,
                                   "disposition": "The DOI, source and six existing identities are expected contextual matches. A matching paper is not itself an identity collision, and a new source record is neither necessary nor proposed."},
        "prior_packet_scope_evidence": prior_scope,
        "prior_exclusion_disposition": "The earlier B10/B30 and B45 packets excluded reactive Rxx formulations from those packets. The B45 review explicitly says they are outside that packet. These exclusions are preserved; they neither establish a permanent scientific rejection nor automatically approve a later R-series admission.",
        "contextual_hit_dispositions": [
            {"identity_ids": sorted(EXISTING_SOURCE_IDENTITIES),
             "disposition": "Existing B0, B10, B20, B30, B45 and Indulin AT are excluded. Corresponding B identity/state/property records explicitly say not DCP-reactive Rxx; those Rxx mentions are exclusions, not recorded reactive identities or aliases. PBS/lignin constituents alone would duplicate B identities unless the reviewed DCP-containing nominal formulation distinction is retained."},
            {"identity_ids": [row["id"] for row in inventory if row["id"].startswith("mat_mtibe2022_")],
             "disposition": "Mtibe records include PBAT, PBS/PBAT 70/30 and lignosulphonate/ZnO hybrid formulations. Their recorded matrix/filler/additive recipes differ from PBS/Indulin AT kraft-lignin/DCP recipes. Supplier differences or different study labels alone are not a novelty basis; unreported additives do not prove universal absence."}],
        "composition_and_granularity_review": {
            "candidate_nominal_loadings_are_pairwise_distinct": len({row[2] for row in ROWS}) == len(ROWS),
            "inventory_category_counts": dict(sorted(Counter(row["category"] for row in inventory).items())),
            "assessment": "The finite current inventory contains the Ewurum simple blends and constituent references, but no R10/R20/R30/R45 reactive formulation identity. Conditional novelty rests on the explicitly source-qualified DCP-containing recipe and different lignin loadings, not a processing-state recount or automatic inference of exact reaction products.",
            "unreinforced_control": "R0 is outside this four-composite candidate scope; B0 and Indulin AT already exist. No decision admitting or permanently rejecting R0 is made here.",
            "limitation": "This does not prove global uniqueness, exact lot equivalence, final chemical architecture or absence of unknown additives. No independent scientific review or raw-data reanalysis is established."},
        "computed_inventory": computed,
        "relationship_inventory": {"runtime_overlay_path": INPUTS[14], "runtime_memberships": len(relationship["memberships"]),
                                   "runtime_relationships": len(relationship["relationships"]), "example_path": INPUTS[15], "example_edges": len(examples),
                                   "runtime_contextual_memberships": contextual_hits(relationship["memberships"]),
                                   "runtime_contextual_relationships": contextual_hits(relationship["relationships"]),
                                   "example_contextual_hits": contextual_hits(examples),
                                   "result": "Existing source and constituent/family context is retained as context. No new candidate identity endpoint is recorded in the frozen inputs. Family membership or a constituent link does not create equivalence, inverse scientific claims or propagated properties."},
        "taxonomy_and_wood_inventory": {"taxonomy_migrated_identities": len(documents[INPUTS[3]]["migrated_identity_ids"]),
                                       "baseline_crosswalk_rows": len(documents[INPUTS[4]]),
                                       "reviewed_wood_row_hashes": len(documents[INPUTS[5]]["reviewed_row_sha256"]),
                                       "wood_physical_locators": len(documents[INPUTS[5]]["gwdd_physical_locators"]),
                                       "result": "Taxonomy and wood inputs are screened for the source DOI, proposed identity IDs and formulation context. A wood or lignin-family mention is not this processed PBS/lignin/DCP formulation."},
        "candidate_decisions": decisions,
        "candidate_delta": {"identities": 4, "composite": 4, "grades": 0, "states": 4, "properties": 4, "sources": 0},
        "formal_admitted_delta": 0,
        "required_preserved_qualifications": [
            "Nominal 10, 20, 30 and 45 wt.% Indulin AT lignin relative to total polymer mass and source-reported DCP addition are not analyzed final composition or an exact cured-network formula. The 0.25 wt.% DCP denominator is not explicitly resolved and must not be assigned to PBS mass or total polymer mass.",
            "Use study-qualified identity names and aliases; literal R10, R20, R30 and R45 are source designations, not globally unique grades. The unresolved BioPBS FZ91PM/FZ91PB designation must not be silently reduced to one grade.",
            "The source-reported reactive-additive recipe distinguishes the R-series from the separately recorded simple blends. Extrusion, injection molding, specimen geometry and measured-value differences alone do not create new identities.",
            "One selected Young's-modulus result per formulation. R0, B-series comparators, Indulin AT, other properties and raw source assets are outside this candidate addition.",
            "Preserve the exact reused source record and its CC BY 4.0 attribution. Separate source review must check the selected original cells, DCP and loading bases, method, sample/statistical scope and unknown conditions. This audit does not approve source transcription or licensing."],
        "acceptance_dependencies": ["Separate source-byte, exact authorship, attribution and rights review.",
                                    "Strict compiler/catalog replay and focused candidate regression tests, including existing-source reuse and B/R identity distinction.",
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
