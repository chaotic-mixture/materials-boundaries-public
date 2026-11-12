"""Source-qualified oscillatory complex viscosity magnitude and cyclic frequency."""
from copy import deepcopy
from decimal import Decimal

QUANTITY = "oscillatory_complex_viscosity_magnitude"
UNIT = "kPa_s_complex_viscosity"
FACT_FIELDS = ("rheometer_and_geometry", "temperature_control", "strain_amplitude", "frequency_protocol",
               "measurement_and_reduction", "sample_preparation_conditioning",
               "replicate_and_piece_relationship", "instrument_corrections")
LABEL_KEYS = ("code_" + QUANTITY, "complex_viscosity_definition",
              "complex_viscosity_reference_notice", "oscillation_frequency",
              *("complex_viscosity_" + name for name in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref("evidence"), 1)
    definitions["complex_viscosity_fact"] = {"oneOf": [
        obj({"status": {"const": "reported"}, "text": text,
             "evidence": evidence, "notes": text}),
        obj({"status": {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]},
             "text": {"type": "null"}, "evidence": evidence, "notes": text}),
    ]}
    definitions["complex_viscosity_definition"] = obj({
        "basis": {"const": "source_reported_oscillatory_complex_viscosity_magnitude"},
        **{name: ref("complex_viscosity_fact") for name in FACT_FIELDS},
        "evidence": evidence, "notes": text,
    })
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"]
                  if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"]["unit_code"] = {"const": UNIT}
    definitions["complex_viscosity_reported_value"] = scalar

    # Keep every legacy definition unchanged. Only this branch can use its
    # dedicated absolute viscosity unit, including multiple reported measures.
    def specialize(value):
        if isinstance(value, dict):
            if value.get("$ref") == "#/$defs/reported_measure":
                value["$ref"] = "#/$defs/complex_viscosity_reported_measure"
            fields = value.get("properties", {})
            unit = fields.get("unit_code", {})
            if "enum" in unit:
                fields["unit_code"] = {"const": UNIT}
            for child in value.values():
                specialize(child)
        elif isinstance(value, list):
            for child in value:
                specialize(child)
    for old, new in (("reported_measure", "complex_viscosity_reported_measure"),
                     ("uncertainty", "complex_viscosity_uncertainty")):
        definitions[new] = deepcopy(definitions[old])
        specialize(definitions[new])
    positive = {"type": "string", "maxLength": 49,
        "pattern": r"^(?=[0-9.]*[1-9])(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])"}
    definitions["oscillation_frequency"] = {"oneOf": [
        obj({"status": {"const": "reported"}, "number": positive, "value_text": text,
             "unit_code": {"const": "Hz"}, "unit_text": {"const": "Hz"},
             "evidence": evidence, "notes": text}),
        obj({"status": {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]},
             **{key: {"type": "null"} for key in ("number", "value_text", "unit_code", "unit_text")},
             "evidence": evidence, "notes": text}),
    ]}
    branch = deepcopy(base)
    fields = branch["properties"]
    fields.update(quantity={"const": QUANTITY}, quantity_dimension={"const": "pressure_time"},
                  reported_value=ref("complex_viscosity_reported_value"),
                  complex_viscosity_definition=ref("complex_viscosity_definition"),
                  oscillation_frequency=ref("oscillation_frequency"),
                  uncertainty={"anyOf": [ref("complex_viscosity_uncertainty"), {"type": "null"}]},
                  evidence_kind={"const": "published_experimental_reference"},
                  reporting_basis={"const": "reported_summary"},
                  determination_basis={"const": "source_reports_measurement"},
                  density_basis={"type": "null"})
    fields.pop("derivation", None)
    fields["method_definition"]["properties"]["type"] = {"const": "source_reported_conventional"}
    fields["method_definition"]["properties"]["extraction_window"] = {"type": "null"}
    branch["required"].extend(["complex_viscosity_definition", "oscillation_frequency"])
    return branch


def validate(prop, fail, numeric_token_matches):
    if prop["quantity"] != QUANTITY:
        return
    if Decimal(prop["reported_value"]["number"]) < 0:
        fail(prop["id"], "source viscosity magnitude must be nonnegative; do not clamp anomalies")
    if prop["conditions"]["direction"]["status"] == "not_applicable":
        fail(prop["id"], "scalar viscosity does not establish direction inapplicability")
    definition = prop["complex_viscosity_definition"]
    source, document = prop["source_id"], prop["source_document"]["url"]
    for name, fact in [("complex_viscosity_definition", definition),
                       *((name, definition[name]) for name in FACT_FIELDS)]:
        if not fact["notes"].strip():
            fail(prop["id"], "complex viscosity facts require explanatory notes")
        reported = fact.get("status") == "reported"
        if reported and not fact["text"].strip():
            fail(prop["id"], "reported complex viscosity facts require text")
        roles = ("method", "condition") if reported or name == "complex_viscosity_definition" else ("condition",)
        for role in roles:
            if not any(e["source_id"] == source and e["url"] == document
                       and role in e["supports"] for e in fact["evidence"]):
                fail(prop["id"], "complex viscosity facts require primary inspected-document " + role + " evidence")

    coordinate = prop["oscillation_frequency"]
    if not coordinate["notes"].strip():
        fail(prop["id"], "frequency requires source scope notes")
    if not any(e["source_id"] == source and e["url"] == document and "condition" in e["supports"] for e in coordinate["evidence"]):
        fail(prop["id"], "frequency needs inspected primary document evidence")
    if coordinate["status"] == "reported":
        if Decimal(coordinate["number"]) <= 0 or not numeric_token_matches(coordinate["value_text"], coordinate["number"]):
            fail(prop["id"], "reported cyclic frequency must preserve a positive source Hz coordinate")
        cells = {e["locator"] for e in prop["evidence"] if e["source_id"] == source and e["url"] == document and "reported_value" in e["supports"]}
        if not any(e["source_id"] == source and e["url"] == document and e["locator"] in cells and {"condition", "classification"} <= set(e["supports"]) for e in coordinate["evidence"]):
            fail(prop["id"], "reported frequency must match selected source value cell")
