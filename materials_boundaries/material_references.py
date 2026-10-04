"""Closed, dependency-free contracts for source-reported material references.

These records are catalog-only source transcriptions, never evaluator inputs,
engineering allowables, certified specimens, or universal physical bounds.
Schemas describe structure; generic cross-record checks describe the graph.
Exact structural identity/grade/state clones cannot inflate coverage. Chemical or
formulation equivalence beyond those exact facts remains a source-backed curation
decision; there is no fuzzy matching or automatic material ontology. Neither these
checks nor the schemas verify source truth, licensing, or translations.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import date
from decimal import Decimal
import json
import re
from urllib.parse import urlsplit

LANGUAGES = ("en", "zh", "ja", "de")
CATEGORIES = ("metal", "polymer", "inorganic", "composite")
QUANTITY_DIMENSIONS = {
    "mass_density": "mass_per_volume",
    "youngs_modulus": "pressure",
    "tensile_modulus": "pressure",
    "flexural_modulus": "pressure",
    "elastic_modulus_unspecified": "pressure",
    "tensile_strength": "pressure",
}
UNIT_DIMENSIONS = {
    "g/cm^3": "mass_per_volume", "kg/m^3": "mass_per_volume",
    "kg/dm^3": "mass_per_volume", "lb/in^3": "mass_per_volume",
    "MPa": "pressure", "GPa": "pressure", "N/mm^2": "pressure",
    "kN/mm^2": "pressure",
}
EVIDENCE_KINDS = (
    "manufacturer_reference", "technical_association_reference",
    "published_experimental_reference", "published_computational_reference",
    "published_handbook_reference", "published_measurement_derived_reference",
)
REPORTING_BASES = (
    "typical", "nominal", "guideline", "specification_limit",
    "reported_summary", "not_stated",
)
FACT_FIELDS = (
    "product_form", "processing", "temper_or_heat_treatment", "conditioning",
    "composition_or_purity", "reinforcement", "porosity", "orientation",
)
CONDITION_FIELDS = (
    "temperature", "test_standard", "test_method", "direction",
    "conditioning", "loading_rate",
)
SUPPORT_TAGS = (
    "material_identity", "grade", "state", "reported_value", "method",
    "condition", "classification", "disclaimer", "summary_statistic",
    "uncertainty", "sample_count", "source_discrepancy",
)
# Fixed-point only, bounded to 24 integer and 24 fractional digits. Decimal
# preserves significant trailing zeroes; exponents and signed zero are excluded.
DECIMAL_PATTERN = r"^(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])"
# Source/display strings must never inject terminal commands or hidden control
# sequences or malformed UTF-16 surrogates that cannot be UTF-8 encoded.
# Multiline/tabbed labels are not part of this minimal contract.
_CONTROL_PATTERN = r"[\x00-\x1f\x7f-\x9f\ud800-\udfff]"
TEXT = {"type": "string", "minLength": 1,
        "pattern": r"^(?=.*\S)[^\x00-\x1f\x7f-\x9f\ud800-\udfff]+(?![\s\S])"}
NULL = {"type": "null"}
NULLABLE_TEXT = {"anyOf": [TEXT, NULL]}
DECIMAL = {"type": "string", "maxLength": 49, "pattern": DECIMAL_PATTERN}
HTTPS = {"type": "string", "format": "uri", "pattern": r"^(?![\s\S]*[\x00-\x1f\x7f-\x9f\ud800-\udfff])https://[^\s/?#]+(?:[/?#][^\s]*)?(?![\s\S])"}


def _enum(values):
    return {"type": "string", "enum": list(values)}


def _array(items, minimum=0, unique=False):
    result = {"type": "array", "items": items, "minItems": minimum}
    if unique:
        result["uniqueItems"] = True
    return result


def _object(properties, optional=()):
    return {"type": "object", "additionalProperties": False,
            "properties": properties,
            "required": [key for key in properties if key not in optional]}


def _ref(name):
    return {"$ref": "#/$defs/" + name}


def _id(prefix):
    return {"type": "string", "pattern": "^" + prefix + r"_[a-z0-9][a-z0-9_]*(?![\s\S])", "maxLength": 160}


def _defs():
    evidence = _object({"source_id": TEXT, "url": HTTPS, "locator": TEXT,
                        "supports": _array(_enum(SUPPORT_TAGS), 1, True)})
    evidence_list = _array(_ref("evidence"), 1)
    facts = []
    for status in ("reported", "not_reported_in_inspected_source", "not_verified", "not_applicable"):
        facts.append(_object({
            "status": {"const": status}, "text": TEXT if status == "reported" else NULL,
            "evidence": evidence_list if status == "reported" else _array(_ref("evidence")),
            "notes": TEXT if status == "not_applicable" else NULLABLE_TEXT,
        }))
    return {
        "evidence": evidence,
        "fact": {"oneOf": facts},
        "names": _object({lang: TEXT for lang in LANGUAGES}),
        "alias": _object({"language": _enum((*LANGUAGES, "und")), "text": TEXT}),
    }


def _make_materials_schema():
    definitions = _defs()
    common = {"version": {"const": "1.0.0"}}
    aliases = _array(_ref("alias"), unique=True)
    evidence = _array(_ref("evidence"), 1)
    definitions["identity"] = _object({
        "id": _id("mat"), **common, "category": _enum(CATEGORIES), "name": TEXT,
        "names": _ref("names"), "aliases": aliases, "identity_scope": TEXT,
        "evidence": evidence,
    })
    definitions["grade"] = _object({
        "id": _id("grade"), **common, "identity_id": _id("mat"),
        "designation": TEXT,
        "authority": _object({"kind": _enum(("manufacturer", "standard_designation", "source_designation")), "name": TEXT}),
        "manufacturer": _ref("fact"), "aliases": aliases, "evidence": evidence,
    })
    definitions["state"] = _object({
        "id": _id("state"), **common, "identity_id": _id("mat"),
        "grade_id": {"anyOf": [_id("grade"), NULL]}, "name": TEXT,
        "names": _ref("names"), "aliases": aliases, "source_designation": TEXT,
        "state": _object({key: _ref("fact") for key in FACT_FIELDS}),
        "source_scope": TEXT, "evidence": evidence,
        "property_ids": _array(_id("refprop"), 1, True),
        "evaluation_support": {"const": "catalog_only"},
    })
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:materials-boundaries:schema:materials:1.0.0",
        "title": "Catalog-only concrete material registry v1",
        **_object({"schema_version": {"const": "1.0.0"},
                   "identities": _array(_ref("identity")), "grades": _array(_ref("grade")),
                   "records": _array(_ref("state"))}), "$defs": definitions,
    }


def _make_properties_schema():
    definitions = _defs()
    evidence = _array(_ref("evidence"), 1)
    unit = _enum(UNIT_DIMENSIONS)
    common_value = {"value_text": TEXT, "unit_text": TEXT, "unit_code": unit}
    definitions["reported_value"] = {"oneOf": [
        _object({"kind": {"const": "scalar"}, **common_value, "number": DECIMAL}),
        _object({"kind": {"const": "interval"}, **common_value, "lower": DECIMAL, "upper": DECIMAL,
                 "endpoint_semantics": {"const": "source_reported_not_a_confidence_interval"}}),
        _object({"kind": {"const": "comparison"}, **common_value,
                 "operator": _enum((">", ">=", "<", "<=")), "number": DECIMAL}),
    ]}
    definitions["uncertainty"] = _object({
        "type": {"const": "reported_standard_deviation"}, **common_value,
        "number": DECIMAL, "scope": TEXT, "coverage_factor": NULL,
        "confidence_level": NULL, "evidence": evidence,
    })
    definitions["sample_count"] = {"oneOf": [
        _object({"value": {"type": "integer", "minimum": 1}, "relation": _enum(("exact", "at_least")),
                 "scope": TEXT, "source_statement": TEXT, "evidence": evidence}),
        _object({"value": NULL, "relation": {"const": "not_reported"},
                 "scope": TEXT, "source_statement": TEXT, "evidence": _array(_ref("evidence"))}),
    ]}
    definitions["source_document"] = _object({
        "url": HTTPS, "revision": NULLABLE_TEXT,
        "inspected_on": {"type": "string", "format": "date", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "sha256": {"anyOf": [{"type": "string", "pattern": r"^[0-9a-f]{64}$", "maxLength": 64}, NULL]},
        "hash_status": _enum(("recorded", "not_retained", "unavailable")),
        "hash_note": NULLABLE_TEXT, "inspection_scope": TEXT,
        "inspection_status": {"const": "selected_content_inspected"},
    })
    conditions = {key: _ref("fact") for key in CONDITION_FIELDS}
    conditions["additional_conditions"] = _array(_object({"name": TEXT, "fact": _ref("fact")}))
    definitions["property"] = _object({
        "id": _id("refprop"), "version": {"const": "1.0.0"}, "material_state_id": _id("state"),
        "quantity": _enum(QUANTITY_DIMENSIONS),
        "quantity_dimension": _enum(sorted(set(QUANTITY_DIMENSIONS.values()))),
        "source_property_label": TEXT, "reported_value": _ref("reported_value"),
        "evidence_kind": _enum(EVIDENCE_KINDS), "reporting_basis": _enum(REPORTING_BASES),
        "determination_basis": _enum(("source_reports_measurement", "source_reports_calculation", "source_reports_compiled_measurements", "not_stated", "mixed_or_unclear")),
        "basis_note": TEXT, "conditions": _object(conditions, ("additional_conditions",)),
        "density_basis": {"anyOf": [_enum(("apparent", "bulk", "true", "crystallographic", "not_stated")), NULL]},
        "summary_statistic": _enum(("not_stated", "reported_value", "reported_mean")),
        "uncertainty": {"anyOf": [_ref("uncertainty"), NULL]},
        "uncertainty_status": _enum(("reported_standard_deviation", "not_reported_in_inspected_source", "not_applicable")),
        "uncertainty_note": TEXT, "sample_count": _ref("sample_count"),
        "method_definition": _object({"type": _enum(("source_reported_conventional", "source_reported_compilation",
                                                       "source_reported_crystallographic_derivation")),
                                       "definition": TEXT, "extraction_window": NULL, "evidence": evidence}),
        "source_discrepancies": _array(_object({"description": TEXT, "disposition": TEXT, "evidence": evidence})),
        "source_id": TEXT, "evidence": evidence, "source_document": _ref("source_document"),
        "scope_note": TEXT, "evaluation_support": {"const": "catalog_only"},
        "universal_bound": {"const": False}, "engineering_allowable": {"const": False},
        "verification": _object({"source_inspection_scope": TEXT,
                                  "transcription_cross_check": {"const": "completed"},
                                  "independent_scientific_review": {"const": False},
                                  "raw_data_reanalysis": {"const": False}}),
    })
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:materials-boundaries:schema:reference_properties:1.0.0",
        "title": "Catalog-only source-reported reference properties v1",
        **_object({"schema_version": {"const": "1.0.0"}, "records": _array(_ref("property"))}),
        "$defs": definitions,
    }


# Runtime structure and the checked-in JSON schemas share a small, explicit
# schema vocabulary. The test suite checks exact equality to prevent drift.
_MATERIALS_SCHEMA = _make_materials_schema()
_PROPERTIES_SCHEMA = _make_properties_schema()


def _fail(path, message):
    raise ValueError(f"{path}: {message}")


def _same(value, expected):
    # Python's True == 1 must not make a boolean satisfy numeric constants.
    return type(value) is type(expected) and value == expected


def _shape(value, schema, root, path):
    """Validate only the fixed schema vocabulary used above, without a dependency."""
    if "$ref" in schema:
        return _shape(value, root["$defs"][schema["$ref"].split("/")[-1]], root, path)
    for union in ("oneOf", "anyOf"):
        if union in schema:
            matches = 0
            for branch in schema[union]:
                try:
                    _shape(value, branch, root, path)
                    matches += 1
                except ValueError:
                    pass
            if not matches or (union == "oneOf" and matches != 1):
                _fail(path, "does not match the closed " + union + " contract")
    if "const" in schema and not _same(value, schema["const"]):
        _fail(path, "expected constant " + repr(schema["const"]))
    if "enum" in schema and not any(_same(value, item) for item in schema["enum"]):
        _fail(path, "unsupported value")
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int, "null": type(None)}
    if kind and type(value) is not types[kind]:
        _fail(path, "expected " + kind)
    if kind == "object":
        missing = set(schema["required"]) - value.keys()
        extra = value.keys() - schema["properties"].keys()
        if missing or extra:
            _fail(path, f"missing fields {sorted(missing)}; unsupported fields {sorted(extra, key=str)}")
        for key, item in value.items():
            _shape(item, schema["properties"][key], root, path + "." + key)
    elif kind == "array":
        if len(value) < schema.get("minItems", 0):
            _fail(path, "too few entries")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(set(encoded)) != len(encoded):
                _fail(path, "duplicate entries")
        for index, item in enumerate(value):
            _shape(item, schema["items"], root, f"{path}[{index}]")
    elif kind == "string":
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", float("inf")):
            _fail(path, "invalid string length")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            _fail(path, "invalid string syntax")
        if schema.get("format") == "date":
            try:
                date.fromisoformat(value)
            except ValueError:
                _fail(path, "invalid date")
        if schema.get("format") == "uri":
            _https(value, path)
    elif kind == "integer" and value < schema.get("minimum", value):
        _fail(path, "integer below minimum")



def validate_reference_text(value, path="text"):
    """Reject blank text, terminal controls and lone surrogates in display data.

    Valid Unicode scalar values, including astral symbols, remain unchanged.
    The new locale/presentation lane can reuse this exact text contract.
    """
    _shape(value, TEXT, {}, path)

def _https(value, path):
    if not isinstance(value, str) or re.search(_CONTROL_PATTERN, value) or any(char.isspace() for char in value):
        _fail(path, "expected an HTTPS URL")
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username
                 and not parsed.password and parsed.port in (None, 443))
    except ValueError:
        valid = False
    if not valid:
        _fail(path, "expected an HTTPS URL without embedded credentials")


def _all_evidence(value):
    if isinstance(value, dict):
        if set(value) == {"source_id", "url", "locator", "supports"}:
            yield value
        else:
            for item in value.values():
                yield from _all_evidence(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_evidence(item)


def _tagged(evidence, tag, source_id=None):
    return [entry for entry in evidence if tag in entry["supports"]
            and (source_id is None or entry["source_id"] == source_id)]


def _require_tag(evidence, tag, path, source_id=None):
    if not _tagged(evidence, tag, source_id):
        _fail(path, "missing primary evidence support: " + tag)


def _source_index(sources):
    # Source bibliographic shape stays owned by the unchanged source schema.
    # This lane validates the envelope, unique IDs and used HTTPS references.
    if not isinstance(sources, dict) or set(sources) != {"schema_version", "records"} or sources.get("schema_version") != "1.0.0" or not isinstance(sources.get("records"), list):
        _fail("sources", "expected source registry 1.0.0")
    result = {}
    for index, source in enumerate(sources["records"]):
        path = f"sources.records[{index}]"
        if not isinstance(source, dict) or not isinstance(source.get("id"), str) or not source["id"].strip() or re.search(_CONTROL_PATTERN, source["id"]):
            _fail(path, "missing source ID")
        if source["id"] in result:
            _fail(path, "duplicate source ID")
        if not isinstance(source.get("urls"), list) or not source["urls"] or not all(isinstance(url, str) and url.strip() for url in source["urls"]):
            _fail(path, "missing source URLs")
        result[source["id"]] = source
    return result


def _validate_structure(materials, properties):
    _shape(materials, _MATERIALS_SCHEMA, _MATERIALS_SCHEMA, "materials")
    _shape(properties, _PROPERTIES_SCHEMA, _PROPERTIES_SCHEMA, "reference_properties")
    indices = []
    seen = set()
    for name, rows in (("identities", materials["identities"]), ("grades", materials["grades"]),
                       ("states", materials["records"]), ("properties", properties["records"])):
        index = {}
        for row in rows:
            if row["id"] in seen:
                _fail(name, "duplicate ID " + row["id"])
            seen.add(row["id"])
            index[row["id"]] = row
        indices.append(index)
    _reject_structural_duplicates(materials)
    return indices



def _structural_signature(value, field=None):
    """Stable factual signature; evidence/support array ordering is immaterial."""
    if isinstance(value, dict):
        return {key: _structural_signature(item, key) for key, item in sorted(value.items())}
    if isinstance(value, list):
        values = [_structural_signature(item) for item in value]
        if field in {"evidence", "supports"}:
            values.sort(key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
        return values
    return value


def _reject_structural_duplicates(materials):
    """Reject exact factual clones, without inferring chemical equivalence.

    Names, translations, aliases and new IDs cannot create distinct materials.
    Genuinely distinct curated scopes still require source admission/review.
    """
    groups = (
        ("identity", materials["identities"], lambda record: {
            key: record[key] for key in ("category", "identity_scope", "evidence")}),
        ("grade", materials["grades"], lambda record: {
            "identity_id": record["identity_id"], "authority": record["authority"],
            "designation": record["designation"],
            "manufacturer": {key: record["manufacturer"][key] for key in ("status", "text")}}),
        ("state", materials["records"], lambda record: {
            key: record[key] for key in ("identity_id", "grade_id", "source_designation", "state", "source_scope", "evidence")}),
    )
    for kind, records, select in groups:
        seen = {}
        for record in records:
            signature = json.dumps(_structural_signature(select(record)), sort_keys=True, ensure_ascii=False)
            if signature in seen:
                _fail(record["id"], f"duplicate structural {kind} of {seen[signature]}; new IDs or display labels do not create distinct coverage")
            seen[signature] = record["id"]

def _validate_links(materials, properties, indices):
    identities, grades, states, props = indices
    reached_identities, reached_grades = set(), set()
    owners = {key: set() for key in states}
    for grade in grades.values():
        if grade["identity_id"] not in identities:
            _fail(grade["id"], "unknown identity")
    for prop in props.values():
        if prop["material_state_id"] not in states:
            _fail(prop["id"], "unknown material state")
        owners[prop["material_state_id"]].add(prop["id"])
    for state in states.values():
        if state["identity_id"] not in identities:
            _fail(state["id"], "unknown identity")
        reached_identities.add(state["identity_id"])
        grade_id = state["grade_id"]
        if grade_id is not None:
            if grade_id not in grades or grades[grade_id]["identity_id"] != state["identity_id"]:
                _fail(state["id"], "unknown grade or wrong grade identity")
            reached_grades.add(grade_id)
        if set(state["property_ids"]) != owners[state["id"]]:
            _fail(state["id"], "property links and ownership must be reciprocal and complete")
    if reached_identities != set(identities) or reached_grades != set(grades):
        _fail("materials", "orphan identity or grade")


# Only spelling/typography normalization; these mappings never change a unit or
# infer a quantity. Unknown spellings need deliberate capability review.
_UNIT_SPELLINGS = {
    "g/cm^3": {"g/cm^3", "g/cm³", "g/cm3", "g cm^-3", "g.cm-3", "g cm⁻³", "g·cm⁻³", "g cm−3", "g cm-3", "grams per cubic centimeter"},
    "kg/m^3": {"kg/m^3", "kg/m³", "kg/m3", "kg m^-3", "kg.m-3", "kg m⁻³", "kg·m⁻³", "kg m−3", "kg m-3"},
    "kg/dm^3": {"kg/dm^3", "kg/dm³", "kg/dm3", "kg dm^-3", "kg.dm-3", "kg dm⁻³", "kg·dm⁻³", "kg dm−3", "kg dm-3"},
    "lb/in^3": {"lb/in^3", "lb/in³", "lb/in3", "lb./in.³", "lb./in.3", "lb./in.^3"},
    "MPa": {"MPa"}, "GPa": {"GPa"},
    "N/mm^2": {"N/mm^2", "N/mm²", "N/mm2"},
    "kN/mm^2": {"kN/mm^2", "kN/mm²", "kN/mm2"},
}


def _numeric_token_matches(token, canonical):
    """Match only source lexical forms, including precision and grouped digits.

    Canonical strings disambiguate comma/point conventions; a source review must
    justify the convention. The validator refuses extra/removed significant
    decimal zeroes and cannot adjudicate an ambiguous source's typography.
    """
    token = token.strip()
    if not token or len(token) > 96:
        return False
    candidates = set()
    # Plain decimal or comma-decimal; preserve decimal precision exactly.
    if re.fullmatch(r"(?:0|[1-9][0-9]*)(?:[.,][0-9]+)?", token):
        candidates.add(token.replace(",", "."))
    # Explicit three-digit grouping, with optional opposite decimal separator.
    for grouping, decimal in ((",", "."), (".", ","), (" ", "."), (" ", ","),
                              ("\u00a0", "."), ("\u00a0", ","), ("\u202f", "."), ("\u202f", ",")):
        pattern = r"[1-9][0-9]{0,2}(?:" + re.escape(grouping) + r"[0-9]{3})+(?:" + re.escape(decimal) + r"[0-9]+)?"
        if re.fullmatch(pattern, token):
            candidates.add(token.replace(grouping, "").replace(decimal, "."))
    # Printed decimal fractional groups: exactly one ASCII space between
    # nonempty digit groups after one decimal point. The first fractional group
    # has three digits; subsequent groups have three digits except the final
    # group, which may have one to four. This covers scientific digit spacing
    # without deleting arbitrary whitespace or relaxing decimal precision.
    if re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{3}(?: [0-9]{3})* [0-9]{1,4}", token):
        candidates.add(token.replace(" ", ""))
    return canonical in candidates


def _validate_value(value, path, dimension=None, nonnegative=False):
    if dimension is not None and UNIT_DIMENSIONS[value["unit_code"]] != dimension:
        _fail(path, "unit does not match quantity dimension")
    if value["unit_text"].strip() not in _UNIT_SPELLINGS[value["unit_code"]]:
        _fail(path, "unit text is not an admitted spelling of unit code")
    kind = value.get("kind", "scalar")
    numbers = [value["lower"], value["upper"]] if kind == "interval" else [value["number"]]
    for number in numbers:
        decimal = Decimal(number)
        if decimal < 0 or (not nonnegative and decimal == 0):
            _fail(path, "value must be nonnegative" if nonnegative else "value must be positive")
    text = value["value_text"].strip()
    if kind == "interval":
        if Decimal(value["lower"]) >= Decimal(value["upper"]):
            _fail(path, "interval endpoints must be strictly ordered")
        pieces = re.split(r"\s*(?:–|—|−|-|\bto\b)\s*", text)
        if len(pieces) != 2 or not all(_numeric_token_matches(piece, number) for piece, number in zip(pieces, numbers)):
            _fail(path, "interval source text does not preserve parsed endpoints/precision")
    elif kind == "comparison":
        match = re.fullmatch(r"(>=|<=|>|<|≥|≤)\s*(.+)", text)
        if not match or {"≥": ">=", "≤": "<="}.get(match[1], match[1]) != value["operator"] or not _numeric_token_matches(match[2], value["number"]):
            _fail(path, "comparison source text does not preserve operator/value/precision")
    elif not _numeric_token_matches(text, value["number"]):
        _fail(path, "source text does not preserve scalar value/precision")


def _validate_property(prop):
    path = prop["id"]
    source = prop["source_id"]
    dimension = QUANTITY_DIMENSIONS[prop["quantity"]]
    if prop["quantity_dimension"] != dimension:
        _fail(path, "quantity dimension mismatch")
    _validate_value(prop["reported_value"], path + ".reported_value", dimension)
    if (prop["density_basis"] is not None) != (prop["quantity"] == "mass_density"):
        _fail(path, "density_basis required only for density")
    for tag in ("reported_value", "classification"):
        _require_tag(prop["evidence"], tag, path, source)
    value_evidence = _tagged(prop["evidence"], "reported_value", source)
    if not any(entry["url"] == prop["source_document"]["url"] for entry in value_evidence):
        _fail(path, "primary value evidence must identify inspected document")
    _require_tag(prop["method_definition"]["evidence"], "method", path, source)
    for fact in prop["conditions"].values():
        facts = [item["fact"] for item in fact] if isinstance(fact, list) else [fact]
        for item in facts:
            if item["status"] == "reported":
                _require_tag(item["evidence"], "condition", path, source)
    extras = prop["conditions"].get("additional_conditions", [])
    if len({item["name"] for item in extras}) != len(extras):
        _fail(path, "duplicate additional condition names")
    doc = prop["source_document"]
    document_url = urlsplit(doc["url"])
    if document_url.path in ("", "/") and not document_url.query and not document_url.fragment:
        _fail(path, "primary value needs a specific document/table page, not a homepage")
    if doc["hash_status"] == "recorded":
        if doc["sha256"] is None or doc["hash_note"] is not None:
            _fail(path, "recorded hash requires digest and null hash note")
    elif doc["sha256"] is not None or doc["hash_note"] is None:
        _fail(path, "unavailable/not-retained hash requires null digest and explanation")
    if prop["verification"]["source_inspection_scope"] != doc["inspection_scope"]:
        _fail(path, "verification and document inspection scope disagree")
    expected_basis = {"published_experimental_reference": "source_reports_measurement",
                      "published_computational_reference": "source_reports_calculation",
                      "published_handbook_reference": "source_reports_compiled_measurements",
                      "published_measurement_derived_reference": "source_reports_calculation"}
    if prop["evidence_kind"] in expected_basis and prop["determination_basis"] != expected_basis[prop["evidence_kind"]]:
        _fail(path, "published evidence class contradicts determination basis")
    # These method classes are generic physical/provenance contracts, never
    # material-ID exceptions. Both directions are checked: a relabel cannot turn
    # a compilation or crystallographic calculation into a direct experiment.
    method = prop["method_definition"]["type"]
    if ((prop["evidence_kind"] == "published_handbook_reference") !=
            (method == "source_reported_compilation")):
        _fail(path, "handbook evidence requires its compilation method class")
    if ((prop["determination_basis"] == "source_reports_compiled_measurements") !=
            (prop["evidence_kind"] == "published_handbook_reference")):
        _fail(path, "compiled measurements require handbook evidence")
    is_derived = prop["evidence_kind"] == "published_measurement_derived_reference"
    is_crystallographic = method == "source_reported_crystallographic_derivation"
    if is_derived != is_crystallographic:
        _fail(path, "measured-input-derived evidence requires an admitted derivation method")
    if (prop["density_basis"] == "crystallographic") != is_crystallographic:
        _fail(path, "crystallographic density requires its source-reported derivation method")
    if is_crystallographic and prop["quantity"] != "mass_density":
        _fail(path, "crystallographic derivation requires mass density")
    if method != "source_reported_conventional":
        _require_tag(prop["method_definition"]["evidence"], "classification", path, source)
    is_mean = prop["summary_statistic"] == "reported_mean"
    if is_mean:
        if prop["reporting_basis"] != "reported_summary" or prop["reported_value"]["kind"] != "scalar":
            _fail(path, "reported mean requires scalar reported_summary")
        _require_tag(prop["evidence"], "summary_statistic", path, source)
    uncertainty = prop["uncertainty"]
    if uncertainty is not None:
        if not is_mean or prop["uncertainty_status"] != "reported_standard_deviation":
            _fail(path, "SD requires explicit reported mean and uncertainty status")
        if uncertainty["unit_code"] != prop["reported_value"]["unit_code"]:
            _fail(path, "SD unit must equal result unit")
        _validate_value(uncertainty, path + ".uncertainty", dimension, nonnegative=True)
        _require_tag(uncertainty["evidence"], "uncertainty", path, source)
    elif prop["uncertainty_status"] == "reported_standard_deviation":
        _fail(path, "SD status requires numerical SD")
    count = prop["sample_count"]
    if count["value"] is not None:
        _require_tag(count["evidence"], "sample_count", path, source)
    for discrepancy in prop["source_discrepancies"]:
        _require_tag(discrepancy["evidence"], "source_discrepancy", path, source)
    if "apparent" in prop["source_property_label"].casefold() and prop["quantity"] != "mass_density":
        _fail(path, "source-defined apparent mechanical quantities are deferred")



def _unique_fact(prop, seen):
    value = prop["reported_value"]
    represented_value = {key: item for key, item in value.items() if key not in {"value_text", "unit_text"}}
    # An omitted optional array and an explicitly empty array encode the same
    # condition set. Its order is presentation only, never a new source fact.
    conditions = {"additional_conditions": []}
    for key, fact in prop["conditions"].items():
        if key == "additional_conditions":
            conditions[key] = sorted(
                ({"name": item["name"], "status": item["fact"]["status"], "text": item["fact"]["text"]} for item in fact),
                key=lambda item: item["name"],
            )
        else:
            conditions[key] = {"status": fact["status"], "text": fact["text"]}
    signature = json.dumps({
        "state": prop["material_state_id"], "quantity": prop["quantity"],
        "document": prop["source_document"]["url"],
        "locators": sorted({entry["locator"] for entry in _tagged(prop["evidence"], "reported_value", prop["source_id"])}),
        "value": represented_value, "conditions": conditions,
    }, sort_keys=True, ensure_ascii=False)
    if signature in seen:
        _fail(prop["id"], "duplicate source fact for the same material state")
    seen.add(signature)

def validate_material_catalog(materials: dict, properties: dict, sources: dict) -> None:
    """Validate the entire source-backed graph before filtering or rendering.

    Existing scientific/source shape contracts remain with their original
    validators. New IDs are prefixed and disjoint from this source registry;
    the release validator additionally checks historical record/metadata IDs.
    No input is mutated, no source is fetched, and no value is converted.
    """
    indices = _validate_structure(materials, properties)
    _validate_links(materials, properties, indices)
    source_index = _source_index(sources)
    new_ids = set().union(*(set(index) for index in indices))
    if new_ids.intersection(source_index):
        _fail("materials", "new record ID collides with source ID")
    for record in (*materials["identities"], *materials["grades"], *materials["records"], *properties["records"]):
        for evidence in _all_evidence(record):
            if evidence["source_id"] not in source_index:
                _fail(record["id"], "unknown evidence source " + evidence["source_id"])
            if evidence["url"] not in source_index[evidence["source_id"]]["urls"]:
                _fail(record["id"], "evidence URL absent from source registry")
            # A homepage with a generic locator cannot establish an inspected
            # numeric table cell. Source truth still needs independent readback.
            if evidence["locator"].strip().casefold() in {"website", "homepage", "home page", "source", "table", "page", "n/a", "unknown"}:
                _fail(record["id"], "evidence requires a specific locator")
    for identity in materials["identities"]:
        _require_tag(identity["evidence"], "material_identity", identity["id"])
    for grade in materials["grades"]:
        _require_tag(grade["evidence"], "grade", grade["id"])
    for state in materials["records"]:
        _require_tag(state["evidence"], "state", state["id"])
        for fact in state["state"].values():
            if fact["status"] == "reported":
                _require_tag(fact["evidence"], "state", state["id"])
    duplicate_facts = set()
    for prop in properties["records"]:
        if prop["source_id"] not in source_index:
            _fail(prop["id"], "unknown primary source")
        _validate_property(prop)
        source_class = source_index[prop["source_id"]].get("role", "").casefold()
        if "manufacturer" in source_class and prop["evidence_kind"] != "manufacturer_reference":
            _fail(prop["id"], "manufacturer source cannot become published specimen evidence")
        if "technical association" in source_class.replace("_", " ").replace("-", " ") and prop["evidence_kind"] != "technical_association_reference":
            _fail(prop["id"], "technical-association source must retain its reference evidence class")
        _unique_fact(prop, duplicate_facts)


def resolve_material(state_id: str, materials: dict, properties: dict, sources: dict) -> dict:
    """Return a detached, source-complete inspection view of one validated state."""
    validate_material_catalog(materials, properties, sources)
    if not isinstance(state_id, str):
        _fail("state_id", "expected state ID string")
    state = next((item for item in materials["records"] if item["id"] == state_id), None)
    if state is None:
        _fail("state_id", "unknown material state " + state_id)
    identity = next(item for item in materials["identities"] if item["id"] == state["identity_id"])
    grade = next((item for item in materials["grades"] if item["id"] == state["grade_id"]), None)
    props = {item["id"]: item for item in properties["records"]}
    selected = [props[key] for key in state["property_ids"]]
    referenced = {entry["source_id"] for entry in _all_evidence([identity, grade, state, selected])}
    referenced.update(item["source_id"] for item in selected)
    return deepcopy({"schema_version": "1.0.0", "identity": identity, "grade": grade,
                     "state": state, "properties": selected,
                     "sources": [item for item in sources["records"] if item["id"] in referenced]})


def material_coverage(materials: dict, properties: dict) -> dict:
    """Derive counts from a structurally complete graph (no source-truth claim).

    Call validate_material_catalog with sources before reporting release coverage.
    No total or accepted material ID is hardcoded.
    """
    indices = _validate_structure(materials, properties)
    _validate_links(materials, properties, indices)
    duplicate_facts = set()
    for prop in properties["records"]:
        _validate_property(prop)
        _unique_fact(prop, duplicate_facts)
    return {
        "material_identity_count": len(materials["identities"]),
        "grade_count": len(materials["grades"]),
        "material_state_count": len(materials["records"]),
        "property_record_count": len(properties["records"]),
        "quantity_count": len({item["quantity"] for item in properties["records"]}),
        "source_count": len({entry["source_id"] for entry in _all_evidence([materials, properties])}
                            | {item["source_id"] for item in properties["records"]}),
        "by_category": dict(sorted(Counter(item["category"] for item in materials["identities"]).items())),
        "by_evidence_kind": dict(sorted(Counter(item["evidence_kind"] for item in properties["records"]).items())),
    }
