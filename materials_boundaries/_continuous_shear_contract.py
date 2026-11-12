"""Source-qualified continuous shear viscosity, not a steady-state assertion."""
from copy import deepcopy
from decimal import Decimal
import json

QUANTITY = "source_reported_continuous_shear_viscosity"
UNIT = "Pa_s_continuous_shear_viscosity"
FACT_FIELDS = ("rheometer_and_geometry", "temperature_and_sweep_protocol", "shear_protocol",
               "measurement_and_reduction", "sample_preparation_conditioning",
               "replicate_and_piece_relationship", "instrument_corrections", "hardener_and_reaction_context")
LABEL_KEYS = ("code_" + QUANTITY, "continuous_shear_definition", "continuous_shear_reference_notice",
              "shear_rate", "shear_temperature", *("continuous_shear_" + n for n in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref("evidence"), 1)
    unknown = {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]}
    definitions["continuous_shear_fact"] = {"oneOf": [
        obj(dict(status={"const": "reported"}, text=text, evidence=evidence, notes=text)),
        obj(dict(status=unknown, text={"type": "null"}, evidence=evidence, notes=text)),
    ]}
    cell_text = deepcopy(text)
    cell_text["pattern"] = (r"^(?!\s)" + text["pattern"][1:]).replace(
        r"(?![\s\S])", r"(?<!\s)(?![\s\S])")
    definitions["continuous_shear_cell"] = obj({
        "table_id": cell_text, "row_key": cell_text, "column_key": cell_text, "evidence": evidence,
    })
    definitions["continuous_shear_definition"] = obj({
        "basis": {"const": "source_reported_continuous_shear_viscosity"},
        "state_basis": {"const": "source_resin_rheology_context"},
        "source_result_cell": ref("continuous_shear_cell"),
        **{n: ref("continuous_shear_fact") for n in FACT_FIELDS},
        "evidence": evidence, "notes": text,
    })
    nonnegative = {"type": "string", "maxLength": 49,
        "pattern": r"^(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])"}
    positive = {**nonnegative,
        "pattern": r"^(?=[0-9.]*[1-9])(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])"}
    signed = {"type": "string", "maxLength": 50,
        "pattern": r"^-?(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])"}
    for name, number, unit, spelling in (
            ("shear_rate", positive, {"const": "per_s_continuous_shear_rate"}, {"enum": ["s^-1", "s⁻¹", "1/s"]}),
            ("shear_temperature", signed, {"enum": ["degC", "K"]}, text)):
        definitions[name] = {"oneOf": [
            obj(dict(status={"const": "reported"}, number=number, value_text=text,
                     unit_code=unit, unit_text=spelling, evidence=evidence, notes=text)),
            obj({"status": unknown, **{k: {"type": "null"} for k in
                ("number", "value_text", "unit_code", "unit_text")}, "evidence": evidence, "notes": text}),
        ]}
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"]
                  if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"].update(unit_code={"const": UNIT}, number=nonnegative)
    definitions["continuous_shear_reported_value"] = scalar

    def specialize(value):
        if isinstance(value, dict):
            if value.get("$ref") == "#/$defs/reported_measure":
                value["$ref"] = "#/$defs/continuous_shear_reported_measure"
            fields = value.get("properties", {})
            if "enum" in fields.get("unit_code", {}): fields["unit_code"] = {"const": UNIT}
            for child in value.values(): specialize(child)
        elif isinstance(value, list):
            for child in value: specialize(child)
    for old, new in (("reported_measure", "continuous_shear_reported_measure"),
                     ("uncertainty", "continuous_shear_uncertainty")):
        definitions[new] = deepcopy(definitions[old]); specialize(definitions[new])
    branch = deepcopy(base); fields = branch["properties"]
    fields.update(quantity={"const": QUANTITY}, quantity_dimension={"const": "pressure_time"},
                  reported_value=ref("continuous_shear_reported_value"),
                  continuous_shear_definition=ref("continuous_shear_definition"),
                  shear_rate=ref("shear_rate"), shear_temperature=ref("shear_temperature"),
                  uncertainty={"anyOf": [ref("continuous_shear_uncertainty"), {"type": "null"}]},
                  evidence_kind={"const": "published_experimental_reference"},
                  reporting_basis={"const": "reported_summary"},
                  determination_basis={"const": "source_reports_measurement"}, density_basis={"type": "null"})
    fields.pop("derivation", None)
    fields["method_definition"]["properties"].update(type={"const": "source_reported_conventional"},
                                                   extraction_window={"type": "null"})
    branch["required"].extend(["continuous_shear_definition", "shear_rate", "shear_temperature"])
    return branch


def validate(prop, fail, numeric_token_matches, validate_temperature):
    if prop["quantity"] != QUANTITY: return
    source, document = prop["source_id"], prop["source_document"]["url"]
    def require(item, roles):
        for role in roles:
            if not any(e["source_id"] == source and e["url"] == document and role in e["supports"]
                       for e in item["evidence"]):
                fail(prop["id"], "continuous shear facts need primary inspected-document " + role + " evidence")
    definition = prop["continuous_shear_definition"]
    for name, fact in [("definition", definition), *((n, definition[n]) for n in FACT_FIELDS)]:
        if not fact["notes"].strip(): fail(prop["id"], "continuous shear facts require scope notes")
        reported = fact.get("status") == "reported"
        if reported and not fact["text"].strip(): fail(prop["id"], "reported shear facts require text")
        require(fact, ("method", "condition") if reported or name == "definition" else ("condition",))
    if prop["conditions"]["direction"]["status"] == "not_applicable":
        fail(prop["id"], "scalar viscosity does not establish direction inapplicability")
    cell = definition["source_result_cell"]
    if any(not cell[n].strip() or cell[n] != cell[n].strip()
           for n in ("table_id", "row_key", "column_key")):
        fail(prop["id"], "continuous shear source cell requires canonical unpadded table,row,column")
    require(cell, ("reported_value", "classification"))
    cells = {e["locator"] for e in prop["evidence"] if e["source_id"] == source and
             e["url"] == document and "reported_value" in e["supports"]}
    if not any(e["locator"] in cells and {"reported_value", "classification"} <= set(e["supports"])
               and e["source_id"] == source and e["url"] == document for e in cell["evidence"]):
        fail(prop["id"], "source cell must identify selected viscosity value evidence")
    for name in ("shear_rate", "shear_temperature"):
        coordinate = prop[name]; require(coordinate, ("condition",))
        if not coordinate["notes"].strip(): fail(prop["id"], "shear coordinates require scope notes")
        if coordinate["status"] != "reported": continue
        if name == "shear_rate":
            if Decimal(coordinate["number"]) <= 0 or not numeric_token_matches(coordinate["value_text"], coordinate["number"]):
                fail(prop["id"], "shear rate must preserve a positive source inverse-second coordinate")
        else:
            validate_temperature({**coordinate, "kind": "scalar"}, prop["id"] + ".shear_temperature")
            if prop["conditions"]["temperature"]["status"] != "reported":
                fail(prop["id"], "reported shear temperature needs reported condition context")
        if not any(e["source_id"] == source and e["url"] == document and e["locator"] in cells
                   and {"condition", "classification"} <= set(e["supports"]) for e in coordinate["evidence"]):
            fail(prop["id"], "reported shear coordinates must identify selected source value cell")


def guard_cell(prop, seen):
    if prop["quantity"] != QUANTITY: return
    cell = prop["continuous_shear_definition"]["source_result_cell"]
    key = "continuous_shear_cell:" + json.dumps([prop["source_id"], prop["source_document"]["url"],
        *(cell[n] for n in ("table_id", "row_key", "column_key"))], ensure_ascii=False)
    if key in seen: raise ValueError(prop["id"] + ": same continuous shear source cell must be revised, not duplicated")
    seen.add(key)


def validate_state_context(prop, state):
    if prop["quantity"] != QUANTITY: return
    # This initial role is scoped to source resin rheology, not cured specimens.
    if state["state"]["temper_or_heat_treatment"]["status"] in ("reported", "not_applicable"):
        raise ValueError(prop["id"] + ": resin rheology cannot inherit a cured specimen heat treatment")
    definition = prop["continuous_shear_definition"]
    if definition["sample_preparation_conditioning"]["status"] != "reported":
        for name in ("processing", "conditioning"):
            if state["state"][name]["status"] in ("reported", "not_applicable"):
                raise ValueError(prop["id"] + ": unknown rheology preparation cannot inherit specimen preparation")
