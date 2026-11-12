"""Source-qualified closed-cell volume content, independent of total porosity."""
from copy import deepcopy
from decimal import Decimal

QUANTITY = "closed_cell_content_volume_percentage"
UNIT = "percent_closed_cell_content_volume"
FACT_FIELDS = ("volume_reference_basis", "measurement_principle", "test_gas",
               "test_temperature_pressure", "specimen_geometry", "cut_surface_correction",
               "preconditioning")
LABEL_KEYS = ("code_" + QUANTITY, "closed_cell_definition",
              "closed_cell_reference_notice",
              *("closed_cell_" + name for name in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref("evidence"), 1)
    definitions["closed_cell_fact"] = {"oneOf": [
        obj({"status": {"const": "reported"}, "text": text,
             "evidence": evidence, "notes": text}),
        obj({"status": {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]},
             "text": {"type": "null"}, "evidence": evidence, "notes": text}),
    ]}
    definitions["closed_cell_definition"] = obj({
        "basis": {"const": "source_reported_closed_cell_volume_percentage"},
        **{name: ref("closed_cell_fact") for name in FACT_FIELDS},
        "evidence": evidence, "notes": text,
    })
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"]
                  if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"]["unit_code"] = {"const": UNIT}
    scalar["properties"]["number"] = {"type": "string", "maxLength": 28,
        "pattern": r"^(?:(?:0|[1-9][0-9]?)(?:\.[0-9]{1,24})?|100(?:\.0{1,24})?)(?![\s\S])"}
    definitions["closed_cell_reported_value"] = scalar

    # Keep every legacy definition unchanged. Only this branch can use its
    # dedicated absolute percentage scale, including multiple reported measures.
    def specialize(value):
        if isinstance(value, dict):
            if value.get("$ref") == "#/$defs/reported_measure":
                value["$ref"] = "#/$defs/closed_cell_reported_measure"
            fields = value.get("properties", {})
            unit = fields.get("unit_code", {})
            if "enum" in unit:
                fields["unit_code"] = {"const": UNIT}
            for child in value.values():
                specialize(child)
        elif isinstance(value, list):
            for child in value:
                specialize(child)
    for old, new in (("reported_measure", "closed_cell_reported_measure"),
                     ("uncertainty", "closed_cell_uncertainty")):
        definitions[new] = deepcopy(definitions[old])
        specialize(definitions[new])
    branch = deepcopy(base)
    fields = branch["properties"]
    fields.update(quantity={"const": QUANTITY}, quantity_dimension={"const": "dimensionless"},
                  reported_value=ref("closed_cell_reported_value"),
                  closed_cell_definition=ref("closed_cell_definition"),
                  uncertainty={"anyOf": [ref("closed_cell_uncertainty"), {"type": "null"}]},
                  evidence_kind={"const": "published_experimental_reference"},
                  reporting_basis={"const": "reported_summary"},
                  determination_basis={"const": "source_reports_measurement"},
                  density_basis={"type": "null"})
    fields.pop("derivation", None)
    fields["method_definition"]["properties"]["type"] = {"const": "source_reported_conventional"}
    fields["method_definition"]["properties"]["extraction_window"] = {"type": "null"}
    branch["required"].append("closed_cell_definition")
    return branch


def validate(prop, fail):
    if prop["quantity"] != QUANTITY:
        return
    if not 0 <= Decimal(prop["reported_value"]["number"]) <= 100:
        fail(prop["id"], "closed cell central content must lie between 0 and 100; do not clamp source anomalies")
    if prop["conditions"]["direction"]["status"] == "not_applicable":
        fail(prop["id"], "scalar closed cell content does not establish direction inapplicability")
    definition = prop["closed_cell_definition"]
    source, document = prop["source_id"], prop["source_document"]["url"]
    for name, fact in [("closed_cell_definition", definition),
                       *((name, definition[name]) for name in FACT_FIELDS)]:
        if not fact["notes"].strip():
            fail(prop["id"], "closed cell facts require explanatory notes")
        reported = fact.get("status") == "reported"
        if reported and not fact["text"].strip():
            fail(prop["id"], "reported closed cell facts require text")
        roles = ("method", "condition") if reported or name == "closed_cell_definition" else ("condition",)
        for role in roles:
            if not any(e["source_id"] == source and e["url"] == document
                       and role in e["supports"] for e in fact["evidence"]):
                fail(prop["id"], "closed cell facts require primary inspected-document " + role + " evidence")
