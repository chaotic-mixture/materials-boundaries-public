"""Presentation-only, source-preserving views for the reference-material lane."""
from copy import deepcopy
import json


LANGUAGES = ("en", "zh", "ja", "de")
REQUIRED_LABELS = frozenset(('materials', 'reference_properties', 'count', 'empty', 'unknown', 'identity', 'grade', 'category', 'state', 'original_name', 'source_designation', 'source_scope', 'identity_scope', 'authority', 'manufacturer', 'product_form', 'processing', 'temper_or_heat_treatment', 'conditioning', 'composition_or_purity', 'reinforcement', 'porosity', 'orientation', 'property_label', 'quantity', 'evidence_kind', 'reporting_basis', 'determination_basis', 'basis_note', 'reported_value', 'conditions', 'temperature', 'test_standard', 'test_method', 'direction', 'loading_rate', 'density_basis', 'summary_statistic', 'uncertainty', 'uncertainty_status', 'uncertainty_note', 'standard_deviation', 'sample_count', 'scope', 'method_definition', 'source_document', 'source_discrepancies', 'verification', 'scope_note', 'evaluation_support', 'source', 'source_title', 'source_locator', 'source_url', 'source_read_status', 'source_rights', 'evidence', 'caveat', 'reference_notice', 'statistics_notice', 'unknown_notice', 'range_notice', 'comparison_notice', 'translation_notice', 'cli_catalog_extra', 'cli_material_id', 'cli_identity_id', 'cli_grade_id', 'cli_category', 'cli_evidence_kind', 'cli_reporting_basis', 'cli_source_id', 'cli_quantity', 'cli_filter_notice', 'code_catalog_only', 'code_reported', 'code_not_reported_in_inspected_source', 'code_not_verified', 'code_not_applicable', 'code_manufacturer_reference', 'code_technical_association_reference', 'code_published_experimental_reference', 'code_published_computational_reference', 'code_typical', 'code_nominal', 'code_guideline', 'code_specification_limit', 'code_reported_summary', 'code_not_stated', 'code_source_reports_measurement', 'code_source_reports_calculation', 'code_mixed_or_unclear', 'code_reported_mean', 'code_reported_value', 'code_mass_density', 'code_youngs_modulus', 'code_tensile_modulus', 'code_flexural_modulus', 'code_elastic_modulus_unspecified', 'code_tensile_strength', 'code_metal', 'code_polymer', 'code_inorganic', 'code_composite', 'code_apparent', 'code_bulk', 'code_true', 'code_published_handbook_reference', 'code_published_measurement_derived_reference', 'code_source_reports_compiled_measurements', 'code_crystallographic', 'code_source_reported_compilation', 'code_source_reported_crystallographic_derivation'))


def validate_material_locales(locales: dict) -> None:
    """Reject incomplete labels rather than silently hiding a scientific caveat."""
    if (not isinstance(locales, dict) or set(locales) != {
            "schema_version", "default_language", "translation_review", "languages"}
            or locales["schema_version"] != "1.0.0"
            or locales["default_language"] != "en"
            or locales["translation_review"] != "machine_assisted_not_scientifically_reviewed"):
        raise ValueError("material locales: invalid metadata")
    languages = locales["languages"]
    if not isinstance(languages, dict) or set(languages) != set(LANGUAGES):
        raise ValueError("material locales: exactly en, zh, ja and de are required")
    for language, labels in languages.items():
        if not isinstance(labels, dict) or set(labels) != REQUIRED_LABELS:
            raise ValueError(f"material locales: incomplete or unknown labels for {language}")
        if any(not isinstance(value, str) or not value.strip() or "[missing:" in value
               or any(_unsafe_display_codepoint(char) for char in value)
               for value in labels.values()):
            raise ValueError(f"material locales: invalid label for {language}")


def material_labels(language: str = "en") -> dict:
    from .catalog import _read_reference_resource
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    locales = _read_reference_resource("material_locales")
    validate_material_locales(locales)
    return locales["languages"][language]


def _resolved_graph(catalog: dict, kind: str) -> tuple[dict, dict, dict]:
    """Resolve a canonical subset against the complete validated offline graph.

    Incoming records replace records of the same ID. The resulting entire
    graph is validated again, so display cannot bypass semantic protections.
    Catalogues remain raw envelopes; resolved objects never become records.
    """
    from .catalog import read_catalog
    from .material_references import validate_material_catalog
    materials = read_catalog("materials")
    properties = read_catalog("reference_properties")
    sources = read_catalog("sources")
    validate_material_catalog(materials, properties, sources)
    keys = {"schema_version", "records"}
    if kind == "materials":
        keys |= {"identities", "grades"}
    if not isinstance(catalog, dict) or set(catalog) != keys or catalog["schema_version"] != "1.0.0":
        raise ValueError("material presentation: invalid canonical catalogue envelope")
    target = deepcopy(materials if kind == "materials" else properties)
    for key in keys - {"schema_version"}:
        incoming = catalog[key]
        if not isinstance(incoming, list):
            raise ValueError(f"material presentation: {key} must be a list")
        if any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in incoming):
            raise ValueError(f"material presentation: invalid {key} record")
        identifiers = [item["id"] for item in incoming]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(f"material presentation: duplicate {key} ID")
        replacements = {item["id"]: item for item in incoming}
        existing = {item["id"] for item in target[key]}
        target[key] = [deepcopy(replacements.get(item["id"], item)) for item in target[key]]
        target[key].extend(deepcopy(item) for item in incoming if item["id"] not in existing)
    if kind == "materials":
        materials = target
    else:
        properties = target
    validate_material_catalog(materials, properties, sources)
    return materials, properties, sources


def render_material_catalog(catalog: dict, kind: str, language: str = "en") -> str:
    """Show exact source strings, explicit unknowns and mandatory caveats."""
    from .material_references import resolve_material
    if kind not in {"materials", "reference-properties"}:
        raise ValueError(f"unknown material presentation: {kind}")
    materials, properties, sources = _resolved_graph(catalog, kind)
    labels = material_labels(language)
    source_index = {source["id"]: source for source in sources["records"]}
    state_index = {state["id"]: state for state in materials["records"]}
    identity_index = {identity["id"]: identity for identity in materials["identities"]}
    grade_index = {grade["id"]: grade for grade in materials["grades"]}
    lines = [labels[kind.replace("-", "_")], f'{labels["count"]}: {len(catalog["records"])}',
             labels["caveat"], labels["reference_notice"], labels["unknown_notice"],
             labels["translation_notice"]]
    if not catalog["records"]:
        lines.append(labels["empty"])

    def code(value):
        if value is None:
            return labels["unknown"]
        label = labels["standard_deviation"] if value == "reported_standard_deviation" else labels.get("code_" + value)
        return f"{label} [{value}]" if label else value

    def raw(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)

    def field(key, value, indent="  "):
        return f'{indent}{labels.get(key, key)}: {labels["unknown"] if value is None else value}'

    def evidence(items, indent="    "):
        output = []
        for item in items:
            source = source_index[item["source_id"]]
            output.extend([field("source", source["id"], indent),
                           field("source_title", source["title"], indent),
                           field("source_url", item["url"], indent),
                           field("source_locator", item["locator"], indent)])
        return output

    def fact(key, item, indent="    "):
        text = item["text"] if item["text"] is not None else labels["unknown"]
        output = [field(key, f'{text} ({code(item["status"])})', indent)]
        if item["notes"] is not None:
            output.append(field("scope_note", item["notes"], indent + "  "))
        output.extend(evidence(item["evidence"], indent + "  "))
        return output

    def property_view(prop, indent="  "):
        source = source_index[prop["source_id"]]
        result = prop["reported_value"]
        output = [f'{indent}{prop["id"]}',
                  field("property_label", prop["source_property_label"], indent + "  "),
                  field("quantity", code(prop["quantity"]), indent + "  "),
                  field("reported_value", f'{result["value_text"]} {result["unit_text"]}', indent + "  ")]
        for key in ("evidence_kind", "reporting_basis", "determination_basis", "summary_statistic",
                    "evaluation_support"):
            output.append(field(key, code(prop[key]), indent + "  "))
        output.append(field("basis_note", prop["basis_note"], indent + "  "))
        if prop["density_basis"] is not None:
            output.append(field("density_basis", code(prop["density_basis"]), indent + "  "))
        output.append(field("conditions", "", indent + "  "))
        for key, condition in prop["conditions"].items():
            if key == "additional_conditions":
                for extra in condition:
                    output.extend(fact(extra["name"], extra["fact"], indent + "    "))
            else:
                output.extend(fact(key, condition, indent + "    "))
        uncertainty = prop["uncertainty"]
        if uncertainty is not None:
            output.append(field("standard_deviation",
                                f'{uncertainty["value_text"]} {uncertainty["unit_text"]}', indent + "  "))
            output.append(field("scope", uncertainty["scope"], indent + "  "))
            output.extend(evidence(uncertainty["evidence"], indent + "    "))
        else:
            output.append(field("uncertainty", None, indent + "  "))
        output.extend([field("uncertainty_status", code(prop["uncertainty_status"]), indent + "  "),
                       field("uncertainty_note", prop["uncertainty_note"], indent + "  "),
                       field("sample_count", raw(prop["sample_count"]), indent + "  ")])
        if uncertainty is not None or prop["summary_statistic"] == "reported_mean":
            output.append(indent + "  " + labels["statistics_notice"])
        if result["kind"] == "interval":
            output.append(indent + "  " + labels["range_notice"])
        elif result["kind"] == "comparison":
            output.append(indent + "  " + labels["comparison_notice"])
        for key in ("method_definition", "source_document", "source_discrepancies", "verification"):
            value = raw(prop[key])
            if key == "method_definition" and prop[key]["type"] != "source_reported_conventional":
                value = code(prop[key]["type"]) + ": " + value
            output.append(field(key, value, indent + "  "))
        output.append(field("scope_note", prop["scope_note"], indent + "  "))
        output.extend(evidence(prop["evidence"], indent + "  "))
        output.extend([field("source_read_status", source["read_status"], indent + "  "),
                       field("source_rights", raw(source["license"]), indent + "  ")])
        return output

    for record in catalog["records"]:
        state = record if kind == "materials" else state_index[record["material_state_id"]]
        identity = identity_index[state["identity_id"]]
        grade = grade_index.get(state["grade_id"])
        lines.extend(["", f'{record["id"]}: {state["names"][language]}',
                      field("identity", f'{identity["names"][language]} [{identity["id"]}]'),
                      field("category", code(identity["category"])),
                      field("grade", None if grade is None else f'{grade["designation"]} [{grade["id"]}]'),
                      field("state", state["id"]), field("original_name", state["name"]),
                      field("source_designation", state["source_designation"]),
                      field("identity_scope", identity["identity_scope"]),
                      field("source_scope", state["source_scope"]),
                      field("evaluation_support", code(state["evaluation_support"]))])
        if grade is not None:
            lines.extend([field("authority", raw(grade["authority"])),
                          field("manufacturer", raw(grade["manufacturer"]))])
        for key, item in state["state"].items():
            lines.extend(fact(key, item))
        lines.extend(evidence(identity["evidence"]))
        if grade is not None:
            lines.extend(evidence(grade["evidence"]))
        lines.extend(evidence(state["evidence"]))
        selected = (resolve_material(state["id"], materials, properties, sources)["properties"]
                    if kind == "materials" else [record])
        for prop in selected:
            lines.extend(property_view(prop))
    # Legacy source metadata does not forbid terminal/bidi controls or lone
    # surrogates. Escape unsafe characters inside each assembled line; only the
    # separators added here remain actual newlines. Valid multilingual text,
    # source JSON and source numeric precision are never rewritten.
    return "\n".join(_escape_terminal_controls(line) for line in lines)


def _unsafe_display_codepoint(char: str) -> bool:
    value = ord(char)
    return (value < 32 or 127 <= value <= 159
            or 0x202A <= value <= 0x202E or 0x2066 <= value <= 0x2069
            or 0xD800 <= value <= 0xDFFF)


def _escape_terminal_controls(text: str) -> str:
    return "".join(f"\\u{ord(char):04x}" if _unsafe_display_codepoint(char)
                   else char for char in text)
