"""Conservative native-field mapping. Absence never becomes zero or experiment."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from .models import Candidate, PropertyEvidence, Provenance, SourceRef, digest, now

MP_ENDPOINT = "https://api.materialsproject.org/materials/summary/"
NOMAD_ENDPOINT = "https://nomad-lab.eu/prod/v1/api/v1/entries"

def plain(value: Any) -> Any:
    """Convert official client's models via their public serialization methods."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "as_dict"):
        return value.as_dict()
    return value

def snapshot(source: SourceRef) -> str:
    return "external_record_" + digest([source.provider, source.record_id,
        source.provider_version, source.payload_sha256])

def normalize_mp(record: Any, *, database_version: str | None = None,
                 retrieved_at: datetime | None = None, fixture: bool = False) -> Candidate:
    d = plain(record)
    payload_hash = digest(d)  # rejects NaN/Infinity before any mapping
    if d.get("deprecated") is True:
        raise ValueError("Deprecated MP entry cannot be normalized into an active candidate")
    meta = d.get("builder_meta") or {}
    if meta.get("license") == "BY-NC":
        raise ValueError("MP BY-NC record is excluded from this prototype")
    source = SourceRef(provider="materials_project", record_id=str(d["material_id"]),
        endpoint=MP_ENDPOINT, source_url="https://materialsproject.org/materials/" + str(d["material_id"]),
        provider_version=database_version or meta.get("database_version"),
        record_updated=str(d["last_updated"]) if d.get("last_updated") else None,
        payload_sha256=payload_hash, retrieved_at=retrieved_at or now(), fixture=fixture,
        license_identifier=meta.get("license"),
        license_review="source_declared" if meta.get("license") else "unreviewed")
    origins = d.get("origins") or []
    def prov(path, origin_name=None):
        # Origin names are property-family names; preserve unmatched origins too.
        tasks = tuple(str(o["task_id"]) for o in origins
                      if origin_name is not None and o.get("name") == origin_name and o.get("task_id"))
        return Provenance(source=source, field_path=path, task_ids=tasks,
            method={"builder_meta": meta, "origins": origins},
            note="Task-to-method resolution requires the corresponding MP task document; no functional inferred.")
    properties = []
    for field, quantity, unit, family in (
        ("density", "mass_density", "g/cm^3", "structure"),
        ("band_gap", "band_gap", "eV", None),
        ("formation_energy_per_atom", "formation_energy_per_atom", "eV/atom", None),
        ("energy_above_hull", "energy_above_hull", "eV/atom", None),
    ):
        if d.get(field) is not None:
            properties.append(PropertyEvidence(quantity=quantity, value=d[field], unit=unit,
                evidence_kind="computed", provenance=prov(field, family)))
    for field in ("bulk_modulus", "shear_modulus"):
        values = d.get(field)
        if values is not None:
            if not isinstance(values, dict):
                raise ValueError("Expected named elastic averages")
            for average in ("voigt", "reuss", "vrh"):
                if values.get(average) is not None:
                    properties.append(PropertyEvidence(quantity=field + "_" + average,
                        value=values[average], unit="GPa", evidence_kind="computed",
                        provenance=prov(field + "." + average)))
    structure = d.get("structure")
    identity = {"formula": prov("formula_pretty")}
    if d.get("composition_reduced") is not None:
        identity["composition"] = prov("composition_reduced")
    if structure is not None:
        identity["structure"] = prov("structure", "structure")
    return Candidate(snapshot_id=snapshot(source), source=source, formula=d["formula_pretty"],
        composition=d.get("composition_reduced"), structure=structure,
        structure_format="pymatgen" if structure else "absent", identity_evidence=identity,
        state={"symmetry": d.get("symmetry"), "temperature_K": None,
               "pressure_Pa": None, "processing": None}, properties=tuple(properties),
        external_references={"database_IDs": d.get("database_IDs") or {},
            "theoretical": d.get("theoretical"), "is_metal": d.get("is_metal"),
            "is_stable": d.get("is_stable"), "warnings": d.get("warnings") or [],
            "builder_meta": meta, "origins": origins},
        limitations=Candidate.model_fields["limitations"].default + (
            "MP theoretical=false or ICSD linkage does not make computed properties experimental.",
            "MP summary fields can originate from different tasks; task methods unresolved.",
            "Raw provider units retained; no inference of tensile strength from elastic moduli.",))

def normalize_nomad(record: dict, *, retrieved_at: datetime | None = None,
                    api_version: str | None = None, fixture: bool = False) -> Candidate:
    """Accept a search entry or a projected archive (metadata + results)."""
    payload_hash = digest(record)
    archive = "metadata" in record
    meta = record["metadata"] if archive else record
    results = record.get("results") or {}
    material = results.get("material") or {}
    method = results.get("method") or {}
    prefix = "metadata." if archive else ""
    eid = meta["entry_id"]
    source = SourceRef(provider="nomad", record_id=eid,
        endpoint=NOMAD_ENDPOINT + ("/" + eid + "/archive/query" if archive else ""),
        source_url="https://nomad-lab.eu/prod/v1/gui/search/entries/entry/id/" + eid,
        provider_version=api_version, record_updated=meta.get("last_processing_time"),
        payload_sha256=payload_hash, retrieved_at=retrieved_at or now(), fixture=fixture,
        license_identifier=meta.get("license"),
        license_review="source_declared" if meta.get("license") else "unreviewed")
    def prov(path):
        return Provenance(source=source, field_path=path, method=method,
                          note="Native built-in NOMAD quantities use SI; custom schema units require separate validation.")
    kind = "computed" if method.get("simulation") else "unknown"
    # Experimental data need a dedicated measurement contract, never classification by absence of simulation.
    structures = (results.get("properties") or {}).get("structures") or {}
    structure = structures.get("structure_original")
    props = []
    if structure and structure.get("mass_density") is not None:
        props.append(PropertyEvidence(quantity="mass_density", value=structure["mass_density"],
            unit="kg/m^3", evidence_kind=kind,
            provenance=prov("results.properties.structures.structure_original.mass_density")))
    identity = {"formula": prov("results.material.chemical_formula_reduced")}
    if structure:
        identity["structure"] = prov("results.properties.structures.structure_original")
    return Candidate(snapshot_id=snapshot(source), source=source,
        formula=material["chemical_formula_reduced"], structure=structure,
        structure_format="nomad_results" if structure else "absent", identity_evidence=identity,
        state={"symmetry": material.get("symmetry"), "structural_type": material.get("structural_type"),
               "temperature_K": None, "pressure_Pa": None, "processing": None},
        properties=tuple(props), external_references={
            "material_id": material.get("material_id"), "upload_id": meta.get("upload_id"),
            "entry_hash": meta.get("entry_hash"), "datasets": meta.get("datasets") or [],
            "references": meta.get("references") or [],
            "external_db": meta.get("external_db") or meta.get("origin"),
            "processing_nomad_version": meta.get("nomad_version"),
            "processing_nomad_commit": meta.get("nomad_commit"), "method": method},
        limitations=Candidate.model_fields["limitations"].default + (
            "NOMAD material_id is a provider grouping, not a canonical project identity.",
            "Imported records may duplicate another provider; provenance must be reviewed.",
            "NOMAD native results coordinates are meters, not angstroms.",))
