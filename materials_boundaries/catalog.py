"""Read immutable packaged records. Textual formulas are never executed."""
from importlib.resources import files
import json


def read_catalog(name: str) -> dict:
    if name not in {"claims", "sources", "observations", "locales", "temperature_models", "computational_predictions",
                    "materials", "reference_properties", "material_locales"}:
        raise ValueError(f"unknown catalog: {name}")
    if name in {"materials", "reference_properties", "material_locales"}:
        return _read_reference_resource(name)
    catalog = json.loads(files("materials_boundaries").joinpath("data", name + ".json").read_text(encoding="utf-8"))
    if name == "claims":
        from ._yield_contract import validate_yield_records
        from ._viscoelastic_contract import validate_viscoelastic_records
        from ._wave_contract import validate_wave_records
        from ._compressibility_contract import validate_compressibility_records
        from ._directional_contract import validate_directional_records
        validate_wave_records(catalog["records"])
        validate_yield_records(catalog["records"], resolve_dependencies=True)
        validate_viscoelastic_records(catalog["records"], resolve_dependencies=True)
        validate_compressibility_records(catalog["records"], resolve_dependencies=True)
        validate_directional_records(catalog["records"], resolve_dependencies=True)
    if name == "observations":
        from ._observation_contract import validate_observation_records
        validate_observation_records(catalog["records"])
        from ._pa12_cf15_observation_contract import validate_pa12_dataset
        validate_pa12_dataset(catalog["records"], require_complete=True)
        from ._paht_cf_observation_contract import validate_paht_dataset
        validate_paht_dataset(catalog["records"], require_complete=True)
    if name == "sources":
        from ._pa12_cf15_observation_contract import validate_pa12_sources
        validate_pa12_sources(catalog["records"])
        from ._paht_cf_observation_contract import validate_paht_sources
        validate_paht_sources(catalog["records"])
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
    material_id: str | None = None,
    identity_id: str | None = None,
    grade_id: str | None = None,
    category: str | None = None,
    evidence_kind: str | None = None,
    reporting_basis: str | None = None,
) -> dict:
    """Return a canonical subset, in packaged order, without changing records.

    Exact filters are case-sensitive and combine with AND. Query terms are
    whitespace-separated, casefolded literal substrings; every term must match
    one of the documented search fields. There is no ranking, interpretation,
    automatic translation, formula execution, or network access. Curated display
    names in the packaged locale dictionary are literal claim/observation aliases.
    """
    if not isinstance(kind, str) or kind not in {"claims", "sources", "observations", "predictions",
                                               "materials", "reference-properties"}:
        raise ValueError(f"unknown searchable catalog: {kind}")
    filters = {"direction": direction, "claim_type": claim_type, "source_id": source_id,
               "role": role, "year": year, "license": license,
               "quantity": quantity, "observation_type": observation_type,
               "material_id": material_id, "identity_id": identity_id,
               "grade_id": grade_id, "category": category,
               "evidence_kind": evidence_kind, "reporting_basis": reporting_basis}
    allowed = {"claims": {"direction", "claim_type", "source_id"},
               "sources": {"role", "year", "license"},
               "observations": {"source_id", "quantity", "observation_type"},
               "predictions": {"source_id", "quantity"},
               "materials": {"identity_id", "grade_id", "category", "source_id", "quantity", "evidence_kind"},
               "reference-properties": {"material_id", "source_id", "quantity", "evidence_kind", "reporting_basis"}}[kind]
    for key, value in filters.items():
        if value is not None and key not in allowed:
            raise ValueError(f"filter {key} is not valid for {kind}")
    for key, value in {"record_id": record_id, "direction": direction,
                       "claim_type": claim_type,
                       "source_id": source_id, "role": role, "license": license,
                       "quantity": quantity, "observation_type": observation_type,
                       "material_id": material_id, "identity_id": identity_id,
                       "grade_id": grade_id, "category": category,
                       "evidence_kind": evidence_kind, "reporting_basis": reporting_basis}.items():
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

    if kind in {"materials", "reference-properties"}:
        return _query_material_catalog(kind, record_id=record_id, query=query,
                                       source_id=source_id, quantity=quantity,
                                       material_id=material_id, identity_id=identity_id,
                                       grade_id=grade_id, category=category,
                                       evidence_kind=evidence_kind, reporting_basis=reporting_basis)
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


def _query_material_catalog(kind: str, **filters) -> dict:
    """Validate the complete reference graph before applying exact filters.

    Search covers state/identity/grade/property/source IDs, canonical names,
    all authored names and explicit aliases, grade designations, quantities,
    categories, evidence kinds, reporting bases and original property labels.
    It does not search source titles, prose scope notes or inferred synonyms.
    """
    from .material_references import (CATEGORIES, EVIDENCE_KINDS, QUANTITY_DIMENSIONS,
                                      REPORTING_BASES, validate_material_catalog)
    for key, choices in (("category", CATEGORIES), ("quantity", QUANTITY_DIMENSIONS),
                         ("evidence_kind", EVIDENCE_KINDS), ("reporting_basis", REPORTING_BASES)):
        if filters[key] is not None and filters[key] not in choices:
            raise ValueError(f"unknown {key}: {filters[key]}")
    materials = read_catalog("materials")
    properties = read_catalog("reference_properties")
    sources = read_catalog("sources")
    validate_material_catalog(materials, properties, sources)
    identities = {item["id"]: item for item in materials["identities"]}
    grades = {item["id"]: item for item in materials["grades"]}
    states = {item["id"]: item for item in materials["records"]}
    property_index = {item["id"]: item for item in properties["records"]}
    catalog = materials if kind == "materials" else properties
    records = catalog["records"]
    if filters["record_id"] is not None:
        records = [item for item in records if item["id"] == filters["record_id"]]
        if not records:
            raise CatalogLookupError(f"unknown {kind} ID: {filters['record_id']}")
    terms = (filters["query"] or "").casefold().split()

    def names(item):
        return [item["id"], item.get("name", ""), *item.get("names", {}).values(),
                *(alias["text"] for alias in item["aliases"])]

    def state_fields(state):
        identity = identities[state["identity_id"]]
        fields = [*names(state), *names(identity), identity["category"], state["source_designation"]]
        if state["grade_id"] is not None:
            grade = grades[state["grade_id"]]
            fields.extend([*names(grade), grade["designation"], grade["authority"]["name"]])
        return fields

    def property_fields(prop):
        return [prop[key] for key in ("id", "material_state_id", "quantity", "source_id",
                                     "source_property_label", "evidence_kind", "reporting_basis")]

    def property_matches(prop):
        return all(filters[key] is None or prop[key] == filters[key]
                   for key in ("source_id", "quantity", "evidence_kind", "reporting_basis"))

    def matches(item):
        if kind == "materials":
            identity = identities[item["identity_id"]]
            if any(filters[key] is not None and item[key] != filters[key]
                   for key in ("identity_id", "grade_id")):
                return False
            if filters["category"] is not None and identity["category"] != filters["category"]:
                return False
            linked = [property_index[identifier] for identifier in item["property_ids"]]
            # One linked record must satisfy the entire property conjunction.
            if not any(property_matches(prop) for prop in linked):
                return False
            fields = state_fields(item)
            fields.extend(field for prop in linked for field in property_fields(prop))
        else:
            if filters["material_id"] is not None and item["material_state_id"] != filters["material_id"]:
                return False
            if not property_matches(item):
                return False
            fields = [*property_fields(item), *state_fields(states[item["material_state_id"]])]
        searchable = [field.casefold() for field in fields]
        return all(any(term in field for field in searchable) for term in terms)

    catalog["records"] = [item for item in records if matches(item)]
    if kind == "materials":
        identity_ids = {state["identity_id"] for state in catalog["records"]}
        grade_ids = {state["grade_id"] for state in catalog["records"]}
        catalog["identities"] = [item for item in catalog["identities"] if item["id"] in identity_ids]
        catalog["grades"] = [item for item in catalog["grades"] if item["id"] in grade_ids]
    return catalog


def _read_reference_resource(name: str) -> dict:
    """Read only the new lane's resources with strict JSON lexical checks."""
    from .validation import _unique_pairs, _reject_constant, _strict_float, _strict_int
    if name not in {"materials", "reference_properties", "material_locales"}:
        raise ValueError(f"unknown reference resource: {name}")
    text = files("materials_boundaries").joinpath("data", name + ".json").read_text(encoding="utf-8")
    return json.loads(text, object_pairs_hook=_unique_pairs,
                      parse_constant=_reject_constant,
                      parse_float=_strict_float, parse_int=_strict_int)
