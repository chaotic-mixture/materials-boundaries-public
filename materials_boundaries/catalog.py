"""Read immutable packaged records. Textual formulas are never executed."""
from importlib.resources import files
import json


def read_catalog(name: str) -> dict:
    if name not in {"claims", "sources", "observations", "locales", "temperature_models", "computational_predictions"}:
        raise ValueError(f"unknown catalog: {name}")
    catalog = json.loads(files("materials_boundaries").joinpath("data", name + ".json").read_text(encoding="utf-8"))
    if name == "claims":
        from ._wave_contract import validate_wave_records
        from ._compressibility_contract import validate_compressibility_records
        from ._directional_contract import validate_directional_records
        validate_wave_records(catalog["records"])
        validate_compressibility_records(catalog["records"], resolve_dependencies=True)
        validate_directional_records(catalog["records"], resolve_dependencies=True)
    if name == "observations":
        from ._observation_contract import validate_observation_records
        validate_observation_records(catalog["records"])
        from ._pa12_cf15_observation_contract import validate_pa12_dataset
        validate_pa12_dataset(catalog["records"], require_complete=True)
    if name == "sources":
        from ._pa12_cf15_observation_contract import validate_pa12_sources
        validate_pa12_sources(catalog["records"])
    return catalog


class CatalogLookupError(ValueError):
    """An exact record ID is absent from the selected catalog."""


def query_catalog(
    kind: str,
    *,
    record_id: str | None = None,
    query: str | None = None,
    direction: str | None = None,
    claim_type: str | None = None,
    source_id: str | None = None,
    quantity: str | None = None,
    observation_type: str | None = None,
    role: str | None = None,
    year: int | None = None,
    license: str | None = None,
) -> dict:
    """Return a canonical subset, in packaged order, without changing records.

    Exact filters are case-sensitive and combine with AND. Query terms are
    whitespace-separated, casefolded literal substrings; every term must match
    one of the documented search fields. There is no ranking, interpretation,
    automatic translation, formula execution, or network access. Curated display
    names in the packaged locale dictionary are literal claim/observation aliases.
    """
    if not isinstance(kind, str) or kind not in {"claims", "sources", "observations", "predictions"}:
        raise ValueError(f"unknown searchable catalog: {kind}")
    filters = {"direction": direction, "claim_type": claim_type, "source_id": source_id,
               "role": role, "year": year, "license": license,
               "quantity": quantity, "observation_type": observation_type}
    allowed = {"claims": {"direction", "claim_type", "source_id"},
               "sources": {"role", "year", "license"},
               "observations": {"source_id", "quantity", "observation_type"},
               "predictions": {"source_id", "quantity"}}[kind]
    for key, value in filters.items():
        if value is not None and key not in allowed:
            raise ValueError(f"filter {key} is not valid for {kind}")
    for key, value in {"record_id": record_id, "direction": direction,
                       "claim_type": claim_type,
                       "source_id": source_id, "role": role, "license": license,
                       "quantity": quantity, "observation_type": observation_type}.items():
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{key} must be a nonempty string")
    if query is not None and not isinstance(query, str):
        raise ValueError("query must be a string")
    if year is not None and (not isinstance(year, int) or isinstance(year, bool)):
        raise ValueError("year must be an integer")
    if direction is not None and direction not in {"interval", "lower", "upper", "prediction", "relation", "constraint"}:
        raise ValueError(f"unknown direction: {direction}")
    if claim_type is not None and claim_type not in {"theoretical_bound", "derived_outer_envelope", "model_estimate", "model_relation", "stability_criterion"}:
        raise ValueError(f"unknown claim_type: {claim_type}")

    if observation_type is not None and observation_type not in {"experiment_derived_model_dependent", "experiment_derived_tensile_test_summary"}:
        raise ValueError(f"unknown observation_type: {observation_type}")

    if kind == "predictions":
        from .predictions import query_predictions
        return query_predictions(record_id=record_id, query=query, source_id=source_id, quantity=quantity)
    catalog = read_catalog(kind)
    records = catalog["records"]
    if record_id is not None:
        records = [record for record in records if record["id"] == record_id]
        if not records:
            raise CatalogLookupError(f"unknown {kind} ID: {record_id}")
    terms = (query or "").casefold().split()
    # These are authored labels, not automatic query translation or source-title
    # rewrites. Search all languages equally; canonical JSON stays unchanged.
    labels = read_catalog("locales")["languages"].values() if kind in {"claims", "observations"} else ()

    def matches(record: dict) -> bool:
        if kind == "claims":
            evidence_ids = [item["source_id"] for item in record["evidence"]]
            if direction is not None and record["direction"] != direction:
                return False
            if claim_type is not None and record["claim_type"] != claim_type:
                return False
            if source_id is not None and source_id not in evidence_ids:
                return False
            fields = [record["id"], record["name"], record["quantity"],
                      record["direction"], record["claim_type"], record["rule_id"], *evidence_ids]
            fields.extend(locale.get("catalog_name_" + record["id"], "") for locale in labels)
        elif kind == "observations":
            evidence_ids = [item["source_id"] for item in record["evidence"]]
            if source_id is not None and source_id not in evidence_ids:
                return False
            if quantity is not None and record["quantity"] != quantity:
                return False
            if observation_type is not None and record["observation_type"] != observation_type:
                return False
            fields = [record["id"], record["name"], record["quantity"],
                      record["observation_type"], record["study_id"], record["material"]["name"], *evidence_ids]
            fields.extend(locale.get("catalog_name_" + record["id"], "") for locale in labels)
        else:
            if role is not None and record["role"] != role:
                return False
            if year is not None and record["year"] != year:
                return False
            if license is not None and license not in (
                record["license"]["identifier"], record["license"]["status"]
            ):
                return False
            fields = [record["id"], record["title"], record["doi"] or "",
                      record["role"], *record["authors"]]
        searchable = [field.casefold() for field in fields]
        return all(any(term in field for field in searchable) for term in terms)

    catalog["records"] = [record for record in records if matches(record)]
    return catalog
