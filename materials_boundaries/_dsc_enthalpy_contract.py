"""Source-reported DSC peak-area specific enthalpy; no sign or mass inference."""
from copy import deepcopy
from decimal import Decimal

QUANTITY = "dsc_reported_melting_specific_enthalpy"
UNIT = "J_per_g_dsc_melting_enthalpy"
FACT_FIELDS = ("thermal_program", "cycle_assignment", "integration_scope", "normalization_mass_basis",
               "baseline_and_limits", "apparatus_and_calibration", "sample_replication_conditioning",
               "sign_convention")
LABEL_KEYS = ("code_" + QUANTITY, "dsc_enthalpy_definition",
              "dsc_enthalpy_reference_notice",
              *("dsc_enthalpy_" + name for name in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref("evidence"), 1)
    definitions["dsc_enthalpy_fact"] = {"oneOf": [
        obj({"status": {"const": "reported"}, "text": text,
             "evidence": evidence, "notes": text}),
        obj({"status": {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]},
             "text": {"type": "null"}, "evidence": evidence, "notes": text}),
    ]}
    definitions["dsc_enthalpy_definition"] = obj({
        "basis": {"const": "source_reported_dsc_melting_peak_area_specific_enthalpy"},
        **{name: ref("dsc_enthalpy_fact") for name in FACT_FIELDS},
        "evidence": evidence, "notes": text,
    })
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"]
                  if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"]["unit_code"] = {"const": UNIT}
    scalar["properties"]["number"] = {"type": "string", "maxLength": 50,
        "pattern": r"^-?(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])"}
    definitions["dsc_enthalpy_reported_value"] = scalar

    # Keep every legacy definition unchanged. Only this branch can use its
    # dedicated absolute enthalpy unit, including multiple reported measures.
    def specialize(value):
        if isinstance(value, dict):
            if value.get("$ref") == "#/$defs/reported_measure":
                value["$ref"] = "#/$defs/dsc_enthalpy_reported_measure"
            fields = value.get("properties", {})
            unit = fields.get("unit_code", {})
            if "enum" in unit:
                fields["unit_code"] = {"const": UNIT}
            for child in value.values():
                specialize(child)
        elif isinstance(value, list):
            for child in value:
                specialize(child)
    for old, new in (("reported_measure", "dsc_enthalpy_reported_measure"),
                     ("uncertainty", "dsc_enthalpy_uncertainty")):
        definitions[new] = deepcopy(definitions[old])
        specialize(definitions[new])
    branch = deepcopy(base)
    fields = branch["properties"]
    fields.update(quantity={"const": QUANTITY}, quantity_dimension={"const": "energy_per_mass"},
                  reported_value=ref("dsc_enthalpy_reported_value"),
                  dsc_enthalpy_definition=ref("dsc_enthalpy_definition"),
                  uncertainty={"anyOf": [ref("dsc_enthalpy_uncertainty"), {"type": "null"}]},
                  evidence_kind={"const": "published_experimental_reference"},
                  reporting_basis={"const": "reported_summary"},
                  determination_basis={"const": "source_reports_measurement"},
                  density_basis={"type": "null"})
    fields.pop("derivation", None)
    fields["method_definition"]["properties"]["type"] = {"const": "source_reported_conventional"}
    fields["method_definition"]["properties"]["extraction_window"] = {"type": "null"}
    branch["required"].append("dsc_enthalpy_definition")
    return branch


def validate_value(value, path, fail, signed_token_matches):
    """Signed source scalar only; no old-domain relaxation or temperature floor."""
    if value["kind"] != "scalar" or value["unit_code"] != UNIT or value["unit_text"].strip() not in {"J/g", "J g^-1", "J g−1"}:
        fail(path, "DSC melting enthalpy requires its dedicated J/g scalar role")
    if not Decimal(value["number"]).is_finite():
        fail(path, "DSC melting enthalpy must be finite")
    if not signed_token_matches(value["value_text"], value["number"]):
        fail(path, "DSC enthalpy text must preserve source sign and precision")


def validate(prop, fail):
    if prop["quantity"] != QUANTITY:
        return
    if prop["conditions"]["direction"]["status"] == "not_applicable":
        fail(prop["id"], "scalar DSC enthalpy does not establish direction inapplicability")
    definition = prop["dsc_enthalpy_definition"]
    source, document = prop["source_id"], prop["source_document"]["url"]
    for name, fact in [("dsc_enthalpy_definition", definition),
                       *((name, definition[name]) for name in FACT_FIELDS)]:
        if not fact["notes"].strip():
            fail(prop["id"], "DSC enthalpy facts require explanatory notes")
        reported = fact.get("status") == "reported"
        if reported and not fact["text"].strip():
            fail(prop["id"], "reported DSC enthalpy facts require text")
        roles = ("method", "condition") if reported or name == "dsc_enthalpy_definition" else ("condition",)
        for role in roles:
            if not any(e["source_id"] == source and e["url"] == document
                       and role in e["supports"] for e in fact["evidence"]):
                fail(prop["id"], "DSC enthalpy facts require primary inspected-document " + role + " evidence")
