"""Pinned, reviewed CIRAD/GWDD v2 wood adapter; no catalog writes.

The scientific review accepts one exact historical research batch. Hash pins
are not a substitute for that review: they ensure its decision cannot silently
be applied to a different dossier, source file, candidate, or taxonomic chain.
The generic pipeline remains responsible for separate staging and admission.
"""
from __future__ import annotations

from copy import deepcopy
import csv
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from . import _material_derivation as contract
from .bulk_ingestion import (IngestionError, SourceProfile, admit_batch,
                             canonical_json_bytes, registry_digest, sha256_json)

ADAPTER_ID = "gwdd_wood_v2"
ADAPTER_VERSION = "1.0.0"
REVIEWED_BATCH_SHA256 = "5e059c0565f13610b307d9f71b1a29c65bec46aff127392d0b10eba469aef032"
_REGISTRY_FILE_SHA256 = "c48e70d4b6406e569d7468285e5e2458d7ba8cca8972f6e96b8c4001bfce0c20"
_DATA_PATH = Path(__file__).with_name("data") / "wood_source_registry_v2.json"
CIRAD = "cirad_collection_4_1"
GWDD = "gwdd_v2_1"
WFO = "wfo_2023_06"
METHOD = "langbour_paradis_thibaut_2019_collection"
CALIBRATION = "vieilledent_2018_density_conversion"
GWDD_METHODS = "fischer_2026_gwdd_methods"
GWDD_METHODS_URL = "https://doi.org/10.1111/nph.70860"
GWDD_METHODS_PDF_URL = "https://research.chalmers.se/publication/550491/file/550491_Fulltext.pdf"
GWDD_METHODS_PDF_SHA256 = "dd237216441203ca80e62710687f82b58ad753d7e33ea682f60cfdd76492ee31"
CALIBRATION_URL = "https://bsapubs.onlinelibrary.wiley.com/doi/10.1002/ajb2.1175"
METHOD_URL = "https://revues.cirad.fr/index.php/BFT/article/view/31709"
SCOPE = ("Selected CIRAD collection accession; conversion-derived basic-density estimate, "
         "not a species mean or engineering design value. Oven-dry mass over fresh or "
         "water-saturated volume. Tissue subtype and anatomical location are unknown; "
         "no secondary-growth wood or trunk inference, including for palms.")
MISSING = ("Not established for this selected accession in the inspected sources. "
           "Nominal conversion moisture is not measured specimen moisture; approximate "
           "source-method climate does not establish an exact record condition.")


def _file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_registry_bytes():
    if _file_hash(_DATA_PATH) != _REGISTRY_FILE_SHA256:
        raise IngestionError("reviewed wood adapter registry bytes differ from the code pin")


@lru_cache(maxsize=1)
def _data():
    # Decoded metadata is cached, but every public operation rechecks file bytes.
    # A SourceProfile is an immutable registration for the verified operation.
    _verify_registry_bytes()
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


def source_registry():
    """Return a detached registered source/release/rights dependency graph."""
    _verify_registry_bytes()
    return deepcopy(_data()["registry"])


def reviewed_profiles():
    _verify_registry_bytes()
    return (SourceProfile(ADAPTER_ID, ADAPTER_VERSION,
                          registry_digest(_data()["registry"]),
                          frozenset(("CC-BY-4.0", "CC0-1.0")),
                          validate_wood_observation),)


def baseline_rows(materials):
    """Map known baseline woods canonically; cork stays a separate tissue."""
    _verify_registry_bytes()
    from ._material_derivation import canonical_identity_key
    crosswalk = {row["baseline_identity_id"]: row for row in _data()["baseline_crosswalk"]}
    rows = []
    for identity in materials["identities"]:
        cross = crosswalk.get(identity["id"])
        # The reviewed crosswalk also conservatively excludes two bamboo culms.
        # All six records remain distinct; cork is deliberately not mapped to wood.
        if cross and cross["disposition"] == "exclude_all_these_accepted_ids_from_new_wood_count":
            for taxon_id in cross["accepted_wfo_ids"]:
                rows.append({"identity_key": _identity_key(taxon_id), "primary_class": identity["category"]})
        else:
            rows.append({"identity_key": canonical_identity_key(identity), "primary_class": identity["category"]})
    return rows


def _identity_key(taxon_id):
    return "wfo:" + taxon_id + ":" + contract.TISSUE


def _require_hash(path, expected, size=None):
    path = Path(path)
    if not path.is_file():
        raise IngestionError("required reviewed dependency is missing: " + str(path))
    if size is not None and path.stat().st_size != size:
        raise IngestionError("reviewed dependency byte length differs: " + str(path))
    if _file_hash(path) != expected:
        raise IngestionError("reviewed dependency SHA-256 differs: " + str(path))


def _verify_manifest(root, manifest, count=None):
    entries = manifest["files"]
    if count is not None and len(entries) != count:
        raise IngestionError("reviewed manifest entry count differs")
    paths = set()
    for item in entries:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts or item["path"] in paths:
            raise IngestionError("manifest contains an unsafe or repeated dependency path")
        paths.add(item["path"])
        _require_hash(root / relative, item["sha256"], item["bytes"])


def verify_reviewed_dossier(dossier_dir, review_dir):
    """Verify reviewed manifests and every source-cache dependency before parsing.

    Source caches remain external. The v1 dossier is hash-checked solely as a
    provenance dependency; its held candidate records are never imported.
    """
    _verify_registry_bytes()
    dossier, review = Path(dossier_dir), Path(review_dir)
    pins = _data()["pins"]
    _require_hash(dossier / "manifest-v2.json", pins["manifest-v2.json"])
    _require_hash(review / "review-decision-v2.json", pins["review-decision-v2.json"])
    _require_hash(review / "REVIEW-v2.md", pins["REVIEW-v2.md"])
    manifest = json.loads((dossier / "manifest-v2.json").read_text(encoding="utf-8"))
    _verify_manifest(dossier, manifest, 33)
    decision = json.loads((review / "review-decision-v2.json").read_text(encoding="utf-8"))
    if (decision["decision"] != "ACCEPT_AS_SOURCE_SUPPORTED_RESEARCH_CANDIDATES_ONLY"
            or decision["batch_sha256"] != REVIEWED_BATCH_SHA256
            or decision["old_hold_still_applies"] is not True):
        raise IngestionError("v2 source-review decision does not authorize this source batch")
    inputs = json.loads((dossier / "evidence/input-hashes-v2.json").read_text(encoding="utf-8"))
    for item in inputs.values():
        _require_hash(dossier / item["path"], item["sha256"])
    _require_hash(dossier.parent / "wood-independent-review/source/gwdd-paper.pdf", GWDD_METHODS_PDF_SHA256)
    old = dossier.parent / "wood-admission-audit"
    old_manifest = json.loads((old / "manifest.json").read_text(encoding="utf-8"))
    _verify_manifest(old, old_manifest)
    _require_hash(dossier / "outputs/candidate-batch-1000-v2.json", REVIEWED_BATCH_SHA256, 4754628)
    # Explicitly bind grant metadata, original source bytes, dictionary and WFO.
    for item in json.loads((dossier / "qa/verified-inputs.json").read_text(encoding="utf-8")):
        _require_hash(dossier.parent / item["path"], item["sha256"], item["bytes"])
    return {"dossier_manifest_sha256": pins["manifest-v2.json"],
            "review_decision_sha256": pins["review-decision-v2.json"],
            "reviewed_batch_sha256": REVIEWED_BATCH_SHA256,
            "manifest_entries_verified": 33}


def _selected_csv(path, ids, id_field, delimiter=","):
    selected = {}
    with Path(path).open(encoding="utf-8", errors="surrogateescape", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=delimiter)
        reader.fieldnames
        previous = reader.line_num
        for number, row in enumerate(reader, 1):
            key = row[id_field]
            if key in ids:
                if key in selected:
                    raise IngestionError("selected source primary key is not unique: " + key)
                selected[key] = (row, {"row_number": number, "line_start": previous + 1,
                                       "line_end": reader.line_num})
            previous = reader.line_num
    if set(selected) != set(ids):
        raise IngestionError("reviewed accession is missing from original source")
    return selected


def build_wood_batch(dossier_dir, review_dir):
    """Build proposed generic records from the exact reviewed v2 bytes only."""
    verify_reviewed_dossier(dossier_dir, review_dir)
    dossier = Path(dossier_dir)
    old = dossier.parent / "wood-admission-audit"
    rows = json.loads((dossier / "outputs/candidate-batch-1000-v2.json").read_text(encoding="utf-8"))
    originals = _selected_csv(old / "source-rights/cirad-collection-data.csv",
                             {r["selected_original_specimen_id"].removeprefix("CTFT ") for r in rows},
                             "CTFT id", ";")
    deposited = _selected_csv(old / "source/gwdd_v2.1.csv", {r["selected_gwdd_id"] for r in rows}, "id")
    materials, observations = [], []
    for original in rows:
        candidate = deepcopy(original)
        candidate["v1_mechanically_eligible_source_record_count"] = candidate.pop("eligible_source_record_count")
        origin, loc = originals[candidate["selected_original_specimen_id"].removeprefix("CTFT ")]
        gwdd, deposited_loc = deposited[candidate["selected_gwdd_id"]]
        checks = ((origin["Specific gravity"], candidate["original_value_as_reported"]),
                  (origin["Species"], candidate["original_species_reference"]),
                  (loc["row_number"], candidate["original_csv_data_record_1based"]),
                  (loc["line_start"], candidate["original_physical_line_start"]),
                  (loc["line_end"], candidate["original_physical_line_end"]),
                  (gwdd["wsg"], candidate["density_g_cm3"]),
                  (gwdd["value_reference"], candidate["original_value_as_reported"]),
                  (gwdd["id_dboriginal"], candidate["selected_original_specimen_id"]),
                  (gwdd["wsg_conversion"], candidate["conversion_factor"]),
                  (gwdd["quantity_reference"], candidate["original_quantity"]),
                  (gwdd["source_long"], _data()["original_citation"]),
                  (deposited_loc["row_number"], candidate["selected_gwdd_csv_data_record_1based"]))
        if any(left != right for left, right in checks):
            raise IngestionError("selected original/deposited value or locator does not match reviewed record")
        metadata = {"reviewed_candidate": candidate, "deposited_locator": deposited_loc}
        material, observation = _generic_records(metadata)
        validate_wood_observation(observation, material, _data()["registry"])
        materials.append(material)
        observations.append(observation)
    return {"schema_version": "1.0.0", "batch_id": "reviewed_wood_1000_v2_" + REVIEWED_BATCH_SHA256[:12],
            "adapter_id": ADAPTER_ID, "registry": source_registry(),
            "materials": materials, "observations": observations, "exclusions": []}


def _taxon(candidate):
    return {"identity_key": _identity_key(candidate["accepted_wfo_taxon_id"]),
            "tissue_scope": contract.TISSUE, "accepted_taxon_id": candidate["accepted_wfo_taxon_id"],
            "accepted_name": candidate["accepted_name"], "accepted_authority": candidate["accepted_authority"],
            "accepted_full_name": candidate["accepted_full_scientific_name"],
            "original_full_name": candidate["original_full_scientific_name"],
            "original_name_records": deepcopy(candidate["original_wfo_name_records"]),
            "source_to_accepted_chains": deepcopy(candidate["source_to_accepted_wfo_chains"]),
            "mapping_method": candidate["taxonomy_mapping_method"],
            "mapping_disposition": "reviewed_supported_historical_backbone",
            "rank": "species", "hybrid": False, "backbone": deepcopy(candidate["taxonomic_backbone"]),
            "source_taxonomic_reference": candidate["source_taxonomic_reference"]}


def _generic_evidence(candidate, loc):
    return [
        {"file_id": "cirad_file_11836", "locator": "Selected accession; original Specific gravity and Species fields",
         "record_id": candidate["selected_original_specimen_id"], "accession": candidate["selected_original_specimen_id"],
         "row_number": candidate["original_csv_data_record_1based"], "line_start": candidate["original_physical_line_start"],
         "line_end": candidate["original_physical_line_end"], "fields": ["CTFT id", "Species", "Specific gravity"],
         "citation": _data()["normalized_citation"]},
        {"file_id": "gwdd_file_v2_1", "locator": "Selected GWDD id; deposited wsg and original measured-input lineage",
         "record_id": candidate["selected_gwdd_id"], "accession": candidate["selected_original_specimen_id"], **loc,
         "fields": ["id", "wsg", "value_reference", "quantity_reference", "moisture_airdry", "wsg_conversion", "id_dboriginal", "plants_sampled", "source_short", "source_long"],
         "citation": _data()["original_citation"]},
        {"file_id": "wfo_backbone_2023_06", "locator": "classification.csv; reviewed accepted target and source-to-accepted chain",
         "record_id": candidate["accepted_wfo_taxon_id"], "fields": ["taxonID", "scientificName", "scientificNameAuthorship", "acceptedNameUsageID", "taxonomicStatus", "taxonRank"],
         "row_number": candidate["taxonomic_backbone"]["accepted_record_1based"],
         "line_start": candidate["taxonomic_backbone"]["accepted_physical_line_start"],
         "line_end": candidate["taxonomic_backbone"]["accepted_physical_line_end"]},
        {"file_id": "gwdd_columns_v2_1", "locator": "Field wsg_conversion, nominal 12% SG coefficient 0.8281316", "record_id": "41", "fields": ["Field", "Description"]},
    ]


def _generic_records(metadata):
    candidate = metadata["reviewed_candidate"]
    key = _identity_key(candidate["accepted_wfo_taxon_id"])
    evidence = _generic_evidence(candidate, metadata["deposited_locator"])
    material = {"identity_key": key, "primary_class": "natural", "name": candidate["accepted_name"],
                "aliases": sorted(set((candidate["original_full_scientific_name"], candidate["accepted_full_scientific_name"]))),
                "taxon": _taxon(candidate), "evidence": deepcopy(evidence),
                "metadata": {"reviewed_candidate_key": candidate["candidate_key"], "tissue_scope": contract.TISSUE,
                             "source_batch_sha256": REVIEWED_BATCH_SHA256}}
    observation = {"observation_id": "gwdd_v2_1_" + candidate["selected_gwdd_id"], "identity_key": key,
                   "quantity": "basic_wood_density", "value": candidate["density_g_cm3"], "unit": "g/cm^3",
                   "evidence_kind": "published_measurement_derived_reference",
                   "state_key": candidate["selected_original_specimen_id"], "evidence": evidence,
                   "metadata": deepcopy(metadata)}
    return material, observation


def _unordered_evidence(row):
    row = deepcopy(row)
    row.pop("status", None)
    for item in row["evidence"]:
        item["fields"] = sorted(item["fields"])
    row["evidence"] = sorted(row["evidence"], key=canonical_json_bytes)
    if "aliases" in row:
        row["aliases"] = sorted(row["aliases"])
    return row


def validate_wood_observation(observation, material, registry):
    """Closed source-specific semantic gate, including exact reviewed lineage."""
    try:
        metadata = observation["metadata"]
        candidate = metadata["reviewed_candidate"]
        key = candidate["candidate_key"]
        if _data()["reviewed_row_sha256"].get(key) != sha256_json(metadata):
            raise IngestionError("candidate or source locator differs from exact reviewed v2 row")
        if registry_digest(registry) != registry_digest(_data()["registry"]):
            raise IngestionError("wood source registry does not match registered rights and provenance")
        expected_material, expected_observation = _generic_records(metadata)
        if (_unordered_evidence(material) != _unordered_evidence(expected_material)
                or _unordered_evidence(observation) != _unordered_evidence(expected_observation)):
            raise IngestionError("wood quantity, identity, scope or evidence differs from reviewed adapter mapping")
        if candidate["accepted_wfo_taxon_id"] in {
            taxon_id for row in _data()["baseline_crosswalk"]
            if row["disposition"] == "exclude_all_these_accepted_ids_from_new_wood_count"
            for taxon_id in row["accepted_wfo_ids"]}:
            raise IngestionError("reviewed baseline identity cannot create a new wood identity")
        identity, state, prop = _runtime_records(metadata)
        contract.validate_taxon(identity)
        contract.validate_derivation(prop, identity)
    except (KeyError, TypeError, IndexError) as exc:
        raise IngestionError("incomplete reviewed wood observation metadata") from exc


def _runtime_evidence(source_id, url, locator, supports):
    return {"source_id": source_id, "url": url, "locator": locator, "supports": supports}


def _file(fid):
    return next(row for row in _data()["registry"]["files"] if row["file_id"] == fid)


def _locator(candidate, loc, original):
    item = _file("cirad_file_11836" if original else "gwdd_file_v2_1")
    release = next(row for row in _data()["registry"]["releases"] if row["release_id"] == item["release_id"])
    return {"source_id": release["source_id"], "release_doi": release["immutable_id"].removeprefix("doi:"),
            "release_version": release["version"], "file_id": "11836" if original else item["file_id"],
            "file_name": item["file_name"], "sha256": item["sha256"], "url": item["download_url"],
            "record_id": candidate["selected_original_specimen_id"] if original else candidate["selected_gwdd_id"],
            "data_record_1based": candidate["original_csv_data_record_1based"] if original else loc["row_number"],
            "physical_line_start": candidate["original_physical_line_start"] if original else loc["line_start"],
            "physical_line_end": candidate["original_physical_line_end"] if original else loc["line_end"],
            "fields": ["CTFT id", "Species", "Specific gravity"] if original else
                      ["id", "wsg", "value_reference", "quantity_reference", "moisture_airdry", "wsg_conversion", "id_dboriginal", "plants_sampled", "source_short", "source_long"]}


def _unknown():
    return {"status": "not_reported_in_inspected_source", "text": None, "evidence": [], "notes": MISSING}


def _runtime_records(metadata):
    from .material_references import CONDITION_FIELDS, FACT_FIELDS, LANGUAGES
    c, loc = metadata["reviewed_candidate"], metadata["deposited_locator"]
    suffix = c["accepted_wfo_taxon_id"].replace("-", "_")
    mid, sid, pid = "mat_wood_" + suffix, "state_wood_" + suffix, "refprop_wood_" + suffix + "_basic_density"
    original = _locator(c, loc, True)
    deposited = _locator(c, loc, False)
    original_ev = _runtime_evidence(CIRAD, original["url"],
        f"File 11836; accession {c['selected_original_specimen_id']}; data record {original['data_record_1based']}; physical lines {original['physical_line_start']}–{original['physical_line_end']}; Species / Specific gravity",
        ["material_identity", "state", "reported_value", "method"])
    deposited_ev = _runtime_evidence(GWDD, deposited["url"],
        f"gwdd_v2.1.csv; id {c['selected_gwdd_id']}; data record {loc['row_number']}; physical lines {loc['line_start']}–{loc['line_end']}; wsg / value_reference / quantity_reference / wsg_conversion",
        ["reported_value", "method", "classification", "state", "sample_count"])
    backbone_ev = _runtime_evidence(WFO, _file("wfo_backbone_2023_06")["download_url"],
        f"classification.csv; accepted {c['accepted_wfo_taxon_id']}; record {c['taxonomic_backbone']['accepted_record_1based']}; reviewed original-name authority and accepted chain",
        ["material_identity", "classification"])
    dictionary_ev = _runtime_evidence(GWDD, _file("gwdd_columns_v2_1")["download_url"],
        "columns_gwdd_v2.1.csv; Field wsg_conversion (41), nominal 12% SG coefficient 0.8281316; wsg definition", ["method", "classification"])
    calibration_ev = _runtime_evidence(CALIBRATION, CALIBRATION_URL,
        "Abstract Methods and Key Results; Methods conversion-factor estimation; Results Db to D12 regression", ["method", "disclaimer"])
    method_ev = _runtime_evidence(METHOD, METHOD_URL,
        "2019 article printed p.11 Database density-table bullet; p.15 Distribution of specific gravity and footnote 5", ["method", "disclaimer"])
    basis_ev = _runtime_evidence(GWDD_METHODS, GWDD_METHODS_URL,
        "Printed p.6 / PDF p.7, Wood density definition and conversion factors: oven-dry mass / fresh or water-saturated volume; water-density convention 1 g/cm^3; inclusion of tree-like monocot tissues without secondary growth. This does not establish accession anatomy or palm-specific calibration accuracy.",
        ["method", "classification", "disclaimer"])
    method_evidence = [deposited_ev, dictionary_ev, calibration_ev, method_ev, basis_ev]
    identity = {"id": mid, "version": "1.0.0", "category": "natural", "name": c["accepted_name"],
                "names": {lang: c["accepted_name"] for lang in LANGUAGES},
                "aliases": [{"language": "und", "text": name} for name in sorted(set((c["original_full_scientific_name"], c["accepted_full_scientific_name"])))],
                "identity_scope": c["accepted_full_scientific_name"] + "; historical WFO June 2023 species identity and " + contract.TISSUE + ". " + SCOPE,
                "evidence": [original_ev, backbone_ev], "canonical_taxon": _taxon(c)}
    names = {"en": c["accepted_name"] + " — selected collection accession " + c["selected_original_specimen_id"],
             "zh": c["accepted_name"] + " — 选定馆藏标本 " + c["selected_original_specimen_id"],
             "ja": c["accepted_name"] + " — 選定された収蔵標本 " + c["selected_original_specimen_id"],
             "de": c["accepted_name"] + " — ausgewählter Sammlungsbeleg " + c["selected_original_specimen_id"]}
    state = {"id": sid, "version": "1.0.0", "identity_id": mid, "grade_id": None,
             "name": names["en"], "names": names, "aliases": [],
             "source_designation": c["selected_original_specimen_id"],
             "state": {field: _unknown() for field in FACT_FIELDS},
             "source_scope": SCOPE, "evidence": [original_ev, deposited_ev],
             "property_ids": [pid], "evaluation_support": "catalog_only"}
    derivation = {"schema_version": "1.0.0", "kind": "conversion_derived_estimate_from_measured_input",
        "profile_id": contract.PROFILE, "profile_version": "1.0.0",
        "formula_id": contract.FORMULA_ID,
        "input": {"quantity": "air_dry_specific_gravity", "number": c["original_value_as_reported"],
                  "value_text": c["original_value_as_reported"], "unit_code": "dimensionless",
                  "basis": contract.INPUT_BASIS,
                  "source_property_label": c["original_property_label"], "deposited_quantity_label": c["original_quantity"],
                  "evidence_type": "source_reported_measured_input"},
        "deposited_output": {"number": c["density_g_cm3"], "unit_code": "g/cm^3", "rounding_increment": c["reported_rounding_increment_g_cm3"]},
        "si_output": {"number": c["density_kg_m3"], "unit_code": "kg/m^3", "rounding_increment": c["reported_rounding_increment_kg_m3"]},
        "formula": {"expression": contract.FORMULA_EXPRESSION, "coefficient": c["conversion_factor"],
                    "coefficient_source_id": GWDD, "coefficient_source_field": "wsg_conversion",
                    "calibration_source_id": CALIBRATION, "basis_convention_source_id": GWDD_METHODS, "water_density_convention_g_cm3": "1",
                    "nominal_conversion_moisture_percent": "12", "measured_specimen_moisture_percent": None,
                    "moisture_percent_basis": "water_mass_over_oven_dry_mass",
                    "calibration_context": "Empirically calibrated conversion; publication-rounded coefficient 0.828, deposited dictionary coefficient 0.8281316. No GWDD hierarchical species prediction and no accession uncertainty inferred. The 2018 calibration database is distinct from the 2019 CIRAD collection; its trunk/specimen counts, drying temperature, uncertainty and per-tree shrinkage are not accession conditions.",
                    "rounding_audit_policy": contract.ROUNDING_AUDIT_POLICY},
        "specimen_scope": {"accession": c["selected_original_specimen_id"], "selection": "selected_collection_accession",
                           **deepcopy(c["unknown_specimen_conditions"]), "treatment": None, "collection_date": None,
                           "measurement_date": None, "missingness_reason": MISSING},
        "counts": {"plants_sampled_as_reported": c["plants_sampled_as_reported_by_gwdd"], "verified_independent_plants": None,
                   "collection_accessions_selected": 1, "v1_mechanically_eligible_source_record_count": c["v1_mechanically_eligible_source_record_count"],
                   "count_scope_note": "Inherited v1 mechanical source-record count, not a v2 validated observation count or independent sample n. plants_sampled is only the source report."},
        "uncertainty": {"record_measurement_uncertainty": None, "source_method_uncertainty_note": c["uncertainty_note"],
                        "conversion_uncertainty": None, "conversion_uncertainty_note": "No per-accession conversion uncertainty is established; calibration residuals do not supply one.",
                        "species_variation": None, "rounding_is_uncertainty": False},
        "provenance": {"original": original, "deposited": deposited, "reviewed_batch_sha256": REVIEWED_BATCH_SHA256,
                       "reviewed_candidate_key": c["candidate_key"], "original_citation": _data()["original_citation"],
                       "normalized_citation": _data()["normalized_citation"], "license_identifiers": ["CC-BY-4.0", "CC0-1.0"],
                       "attribution": "Patrick Langbour; Sébastien Paradis; Bernard Thibaut; CIRAD; Fischer and GWDD contributors; World Flora Online Consortium. Source-specific rights apply; structured factual adaptation only.",
                       "source_scope_note": SCOPE},
        "evidence": [original_ev, deposited_ev, backbone_ev, dictionary_ev, calibration_ev, method_ev, basis_ev]}
    inspection = "Pinned original CIRAD accession/value join, GWDD deposited value and conversion dictionary, WFO June 2023 authority-aware chain; independent v2 source-transcription review. Not experimental replication or engineering certification."
    prop = {"id": pid, "version": "1.0.0", "material_state_id": sid,
            "quantity": "basic_wood_density", "quantity_dimension": "mass_per_volume",
            "source_property_label": "wsg (GWDD basic wood density; source-converted)",
            "reported_value": {"kind": "scalar", "number": c["density_g_cm3"], "value_text": c["density_g_cm3"], "unit_code": "g/cm^3", "unit_text": "g/cm³"},
            "evidence_kind": "published_measurement_derived_reference", "reporting_basis": "not_stated",
            "determination_basis": "source_reports_calculation", "basis_note": SCOPE,
            "conditions": {field: _unknown() for field in CONDITION_FIELDS}, "density_basis": contract.BASIS,
            "summary_statistic": "reported_value", "uncertainty": None,
            "uncertainty_status": "not_reported_in_inspected_source", "uncertainty_note": c["uncertainty_note"],
            "sample_count": {"value": None, "relation": "not_reported", "scope": "Verified independent specimen count is unknown",
                             "source_statement": "GWDD plants_sampled=1 is retained as a source report only; v1 mechanically eligible records are not independent n.", "evidence": []},
            "method_definition": {"type": "source_reported_empirical_conversion", "definition": SCOPE + " " + derivation["formula"]["calibration_context"], "extraction_window": None, "evidence": method_evidence},
            "source_discrepancies": [], "source_id": GWDD,
            "evidence": [deposited_ev, original_ev, dictionary_ev],
            "source_document": {"url": deposited["url"], "revision": "GWDD deposited file v2.1; DOI 10.5281/zenodo.16919510",
                                "inspected_on": "2026-10-06", "sha256": deposited["sha256"], "hash_status": "recorded", "hash_note": None,
                                "inspection_scope": inspection, "inspection_status": "selected_content_inspected"},
            "scope_note": SCOPE, "evaluation_support": "catalog_only", "universal_bound": False, "engineering_allowable": False,
            "verification": {"source_inspection_scope": inspection, "transcription_cross_check": "completed",
                             "independent_scientific_review": False, "raw_data_reanalysis": False}, "derivation": derivation}
    return identity, state, prop


def _runtime_sources():
    records = []
    for release in _data()["registry"]["releases"]:
        license_record = next(row for row in _data()["registry"]["licenses"] if row["license_id"] == release["license_id"])
        files = [row for row in _data()["registry"]["files"] if row["release_id"] == release["release_id"]]
        urls = [license_record["grant_url"], *[row["download_url"] for row in files]]
        sid = release["source_id"]
        authors = {CIRAD: ["Patrick Langbour", "Sébastien Paradis", "Bernard Thibaut"],
                   GWDD: ["Fabian Jörg Fischer and Global Wood Density Database contributors"],
                   WFO: ["World Flora Online Consortium", "Alan Elliott", "Roger Hyam", "William Ulate"]}[sid]
        records.append({"id": sid, "title": release["citation"], "authors": authors,
            "year": {CIRAD: 2018, GWDD: 2025, WFO: 2023}[sid], "doi": release["immutable_id"].removeprefix("doi:"),
            "urls": urls, "read_status": "pinned_selected_source_facts_rights_and_independent_v2_transcription_review",
            "license": {"status": "explicit_reuse_license_verified", "identifier": license_record["identifier"]},
            "role": "published_measurement_derived_reference" if sid == GWDD else "primary_dataset_reference",
            "claim_notes": ["Release version " + release["version"] + ". " + license_record["scope"],
                            "Source-specific grant and attribution: " + json.dumps(license_record, ensure_ascii=False, sort_keys=True),
                            "Immutable file provenance: " + json.dumps(files, ensure_ascii=False, sort_keys=True),
                            *(["Original deposited source citation: " + _data()["original_citation"],
                               "Normalized verified methods citation: " + _data()["normalized_citation"],
                               "GWDD wsg_est and aggregates containing held BY-SA/PROSEA source rows are excluded. No source cache is bundled."]
                              if sid in (CIRAD, GWDD) else
                              ["Pinned historical WFO taxonomic facts only; source-specific CC0 grant retained. No current taxonomy claim and no source cache bundled."])],
            "provenance": {"curation_date": "2026-10-06", "method": "Pinned v2 dossier and independent source review; factual structured adaptation. No scientific peer-review or experimental replication claim."},
            "bundled_content": "selected_source_qualified_facts_bibliographic_metadata_and_original_curation_only_no_source_assets"})
    for sid,title,authors,year,doi,url,notes in [
        (METHOD,"Description of the Cirad wood collection in Montpellier, France, representing eight thousand identified species", ["Patrick Langbour", "Sébastien Paradis", "Bernard Thibaut"],2019,"10.19182/bft2019.339.a31709",METHOD_URL,
         "Original publisher PDF printed pages 11 and 15 inspected; SHA-256 34188a6c455ca8681a2c77faf105ab622fd9dc5c66e063b5dc9b4f0fe4a497a3; official PDF URL https://revues.cirad.fr/index.php/BFT/article/download/31709/31340. PDF label CC BY-ND 4.0 and landing CC BY 4.0 differ; the independently verified dataset CC BY 4.0 grant controls imported data. No paper text, image or PDF redistributed."),
        (CALIBRATION,"New formula and conversion factor to compute basic wood density of tree species using a global wood technology database", ["Ghislain Vieilledent", "Fabian Jörg Fischer", "Jérôme Chave", "Daniel Guibal", "Patrick Langbour", "Jean Gérard"],2018,"10.1002/ajb2.1175",CALIBRATION_URL,
         "Original publisher abstract/methods/results inspected for empirical calibration provenance. Publication-rounded 0.828 is distinct from exact GWDD dictionary coefficient 0.8281316. Bibliographic citation and independently authored factual method summary only; no article asset redistribution or new rights grant inferred.")]:
        records.append({"id":sid,"title":title,"authors":authors,"year":year,"doi":doi,"urls":[url],
                        "read_status":"selected_primary_method_sections_inspected",
                        "license":{"status":"bibliographic_reference_only_no_article_asset_reuse", "identifier":None},
                        "role":"conversion_method_reference","claim_notes":[notes],
                        "provenance":{"curation_date":"2026-10-06","method":"Original method inspected in source audit; source assets remain external."},
                        "bundled_content":"bibliographic_metadata_and_original_curation_only_no_source_assets"})
    records.append({
        "id": GWDD_METHODS,
        "title": "Beyond species means – the intraspecific contribution to global wood density variation",
        "authors": ["Fabian Jörg Fischer", "Jérôme Chave", "Amy Zanne"], "year": 2026,
        "doi": "10.1111/nph.70860", "urls": [GWDD_METHODS_URL, GWDD_METHODS_PDF_URL],
        "read_status": "original_methods_printed_p6_and_title_authors_printed_p1_inspected",
        "license": {"status": "bibliographic_reference_only_no_article_asset_reuse", "identifier": None},
        "role": "quantity_definition_and_conversion_convention_reference",
        "claim_notes": [
            "Author list is explicitly abbreviated to the first three authors verified on printed p.1 / PDF p.2; the source supplies the complete author list. Title and year verified against the retained original article and repository cover citation.",
            "Inspected PDF SHA-256 " + GWDD_METHODS_PDF_SHA256 + "; retained research copy URL " + GWDD_METHODS_PDF_URL + ". Printed p.6 / PDF p.7, Wood density definition and conversion factors: basic density uses oven-dry mass over fresh or water-saturated volume; the compilation applies a water-density convention of 1 g/cm^3 and includes tree-like monocot tissues without secondary growth.",
            "These are compilation definitions and conventions, not measured accession temperature, anatomy, or palm-specific calibration validation. The article describes conversion-derived wsg separately from hierarchical species-model estimates; no hierarchical prediction is imported.",
            "Bibliographic citation and independently authored factual method summary only. No article PDF, figure, image, full text or raw source cache is bundled; no article asset redistribution or new reuse grant is inferred."],
        "provenance": {"curation_date": "2026-10-07",
                       "method": "Verified retained original PDF checksum; checked title/authors and original printed p.6 methods text and page image. Prior independent source review and conversion-contract review provide matching locators."},
        "bundled_content": "bibliographic_metadata_and_original_curation_only_no_source_assets"})
    return {"schema_version": "1.0.0", "records": records}


def materialize_wood_records(admitted, *, expected_review_digest):
    """Return append-only catalog tables from a replay-valid admission package.

    This function does not write production data. A bare candidate status or
    manually relabeled stage is insufficient: deterministic admission replay
    and the independently approved identity-key set must match exactly.
    """
    _verify_registry_bytes()
    if admitted.get("input", {}).get("adapter_id") != ADAPTER_ID or "admission" not in admitted:
        raise IngestionError("wood materialization requires a separate reviewed admission")
    stage_keys = ("schema_version", "input", "baseline", "materials", "observations", "quarantine", "manifest", "review_manifest_sha256")
    staged = {key: deepcopy(admitted[key]) for key in stage_keys}
    # Replay staging, not a reversal of arbitrary caller-supplied statuses.
    from .bulk_ingestion import stage_batch
    staged = stage_batch(staged["input"], baseline=staged["baseline"], profiles=reviewed_profiles())
    replay = admit_batch(staged, admitted["admission"], expected_review_digest=expected_review_digest, profiles=reviewed_profiles())
    if canonical_json_bytes(replay) != canonical_json_bytes(admitted):
        raise IngestionError("admitted wood package differs from deterministic admission replay")
    return _runtime_tables(replay, "admitted")


def source_supported_preview(staged):
    """Validate and transform source-supported rows without admitting any identity."""
    _verify_registry_bytes()
    from .bulk_ingestion import stage_batch
    replay = stage_batch(staged["input"], baseline=staged["baseline"], profiles=reviewed_profiles())
    if canonical_json_bytes(replay) != canonical_json_bytes(staged):
        raise IngestionError("source-supported preview requires deterministic staging replay")
    return {"status": "source_supported_preview_not_admitted", "repository_admitted": 0,
            "review_manifest_sha256": replay["review_manifest_sha256"],
            "tables": _runtime_tables(replay, "source_supported")}


def _runtime_tables(package, status):
    materials = {"schema_version": "1.0.0", "identities": [], "grades": [], "records": []}
    properties = {"schema_version": "1.0.0", "records": []}
    for observation in sorted(package["observations"], key=lambda row: row["identity_key"]):
        if observation["status"] != status:
            continue
        identity, state, prop = _runtime_records(observation["metadata"])
        materials["identities"].append(identity)
        materials["records"].append(state)
        properties["records"].append(prop)
    sources = _runtime_sources()
    from .material_references import validate_material_catalog
    validate_material_catalog(materials, properties, sources)
    return {"materials": materials, "properties": properties, "sources": sources}
