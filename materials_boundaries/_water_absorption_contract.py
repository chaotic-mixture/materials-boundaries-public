"""Source-reported volumetric water absorption, without mass conversion."""
from copy import deepcopy

QUANTITY = "water_absorption_volume_percentage"
UNIT = "percent_water_absorption_volume"
FACT_FIELDS = ("volume_reference_basis", "immersion_exposure", "fluid",
               "specimen_geometry", "preconditioning", "water_temperature",
               "surface_water_treatment")
LABEL_KEYS = ("code_" + QUANTITY, "water_absorption_definition",
              "water_absorption_reference_notice",
              *("water_absorption_" + name for name in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref("evidence"), 1)
    definitions["water_absorption_fact"] = {"oneOf": [
        obj({"status": {"const": "reported"}, "text": text,
             "evidence": evidence, "notes": text}),
        obj({"status": {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]},
             "text": {"type": "null"}, "evidence": evidence, "notes": text}),
    ]}
    definitions["water_absorption_definition"] = obj({
        "basis": {"const": "source_reported_volume_percentage"},
        **{name: ref("water_absorption_fact") for name in FACT_FIELDS},
        "evidence": evidence, "notes": text,
    })
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"]
                  if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"]["unit_code"] = {"const": UNIT}
    definitions["water_absorption_reported_value"] = scalar

    # Keep every legacy definition unchanged. Only this branch can use its
    # dedicated absolute percentage scale, including multiple reported measures.
    def specialize(value):
        if isinstance(value, dict):
            if value.get("$ref") == "#/$defs/reported_measure":
                value["$ref"] = "#/$defs/water_absorption_reported_measure"
            fields = value.get("properties", {})
            unit = fields.get("unit_code", {})
            if "enum" in unit:
                fields["unit_code"] = {"const": UNIT}
            for child in value.values():
                specialize(child)
        elif isinstance(value, list):
            for child in value:
                specialize(child)
    for old, new in (("reported_measure", "water_absorption_reported_measure"),
                     ("uncertainty", "water_absorption_uncertainty")):
        definitions[new] = deepcopy(definitions[old])
        specialize(definitions[new])
    branch = deepcopy(base)
    fields = branch["properties"]
    fields.update(quantity={"const": QUANTITY}, quantity_dimension={"const": "dimensionless"},
                  reported_value=ref("water_absorption_reported_value"),
                  water_absorption_definition=ref("water_absorption_definition"),
                  uncertainty={"anyOf": [ref("water_absorption_uncertainty"), {"type": "null"}]},
                  evidence_kind={"const": "published_experimental_reference"},
                  reporting_basis={"const": "reported_summary"},
                  determination_basis={"const": "source_reports_measurement"},
                  density_basis={"type": "null"})
    fields.pop("derivation", None)
    fields["method_definition"]["properties"]["type"] = {"const": "source_reported_conventional"}
    fields["method_definition"]["properties"]["extraction_window"] = {"type": "null"}
    branch["required"].append("water_absorption_definition")
    return branch


def validate(prop, fail):
    if prop["quantity"] != QUANTITY:
        return
    definition = prop["water_absorption_definition"]
    source, document = prop["source_id"], prop["source_document"]["url"]
    for name, fact in [("water_absorption_definition", definition),
                       *((name, definition[name]) for name in FACT_FIELDS)]:
        if not fact["notes"].strip():
            fail(prop["id"], "water absorption facts require explanatory notes")
        reported = fact.get("status") == "reported"
        if reported and not fact["text"].strip():
            fail(prop["id"], "reported water absorption facts require text")
        roles = ("method", "condition") if reported or name == "water_absorption_definition" else ("condition",)
        for role in roles:
            if not any(e["source_id"] == source and e["url"] == document
                       and role in e["supports"] for e in fact["evidence"]):
                fail(prop["id"], "water absorption facts require primary inspected-document " + role + " evidence")
