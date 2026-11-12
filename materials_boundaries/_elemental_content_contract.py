"""Source-reported XRF elemental mass contents, not a complete composition."""
from copy import deepcopy
from decimal import Decimal
import json

QUANTITY = "source_reported_elemental_mass_content_percentage"
UNIT = "percent_elemental_mass_content"
FACT_FIELDS = ('instrument_and_analysis_method', 'reported_calibration_statement', 'reference_materials_and_traceability', 'sample_preparation_and_reaction_context', 'measurement_environment', 'mass_denominator_and_normalization', 'spectral_reduction_and_matrix_effects', 'detection_quantification_limits', 'replication_and_statistics', 'sampling_depth_and_representativeness')
LABEL_KEYS = ("code_" + QUANTITY, "elemental_content_definition", "elemental_content_reference_notice",
              "elemental_analyte", *("elemental_content_" + n for n in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref("evidence"), 1)
    unknown = {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]}
    definitions["elemental_content_fact"] = {"oneOf": [
        obj(dict(status={"const": "reported"}, text=text, evidence=evidence, notes=text)),
        obj(dict(status=unknown, text={"type": "null"}, evidence=evidence, notes=text)),
    ]}
    cell_text = deepcopy(text)
    cell_text["pattern"] = (r"^(?!\s)" + text["pattern"][1:]).replace(
        r"(?![\s\S])", r"(?<!\s)(?![\s\S])")
    definitions["elemental_content_cell"] = obj({
        "table_id": cell_text, "row_key": cell_text, "column_key": cell_text, "evidence": evidence,
    })
    definitions["elemental_content_definition"] = obj({
        "basis": {"const": "source_reported_elemental_mass_content_percentage"},
        "state_basis": {"const": "source_resin_elemental_characterization_context"},
        "method_family": {"const": "source_reported_XRF"},
        "source_result_cell": ref("elemental_content_cell"),
        **{n: ref("elemental_content_fact") for n in FACT_FIELDS},
        "evidence": evidence, "notes": text,
    })
    nonnegative = {"type": "string", "maxLength": 49,
        "pattern": r"^(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])"}
    definitions["elemental_analyte"] = obj({
        "status": {"const": "reported"}, "symbol": {"enum": ["P", "Cl"]},
        "evidence": evidence, "notes": text,
    })
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"]
                  if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"].update(unit_code={"const": UNIT}, number=nonnegative)
    definitions["elemental_content_reported_value"] = scalar

    def specialize(value):
        if isinstance(value, dict):
            if value.get("$ref") == "#/$defs/reported_measure":
                value["$ref"] = "#/$defs/elemental_content_reported_measure"
            fields = value.get("properties", {})
            if "enum" in fields.get("unit_code", {}): fields["unit_code"] = {"const": UNIT}
            for child in value.values(): specialize(child)
        elif isinstance(value, list):
            for child in value: specialize(child)
    for old, new in (("reported_measure", "elemental_content_reported_measure"),
                     ("uncertainty", "elemental_content_uncertainty")):
        definitions[new] = deepcopy(definitions[old]); specialize(definitions[new])
    branch = deepcopy(base); fields = branch["properties"]
    fields.update(quantity={"const": QUANTITY}, quantity_dimension={"const": "dimensionless"},
                  reported_value=ref("elemental_content_reported_value"),
                  elemental_content_definition=ref("elemental_content_definition"),
                  elemental_analyte=ref("elemental_analyte"),
                  uncertainty={"anyOf": [ref("elemental_content_uncertainty"), {"type": "null"}]},
                  evidence_kind={"const": "published_experimental_reference"},
                  reporting_basis={"const": "reported_summary"},
                  determination_basis={"const": "source_reports_measurement"}, density_basis={"type": "null"})
    fields.pop("derivation", None)
    fields["method_definition"]["properties"].update(type={"const": "source_reported_conventional"},
                                                   extraction_window={"type": "null"})
    branch["required"].extend(["elemental_content_definition", "elemental_analyte"])
    return branch


def validate(prop, fail):
    if prop["quantity"] != QUANTITY: return
    if Decimal(prop["reported_value"]["number"]) > 100:
        fail(prop["id"], "elemental mass content above100 requires source review, not clipping")
    source, document = prop["source_id"], prop["source_document"]["url"]
    def require(item, roles):
        for role in roles:
            if not any(e["source_id"] == source and e["url"] == document and role in e["supports"]
                       for e in item["evidence"]):
                fail(prop["id"], "elemental content facts need primary inspected-document " + role + " evidence")
    definition = prop["elemental_content_definition"]
    for name, fact in [("definition", definition), *((n, definition[n]) for n in FACT_FIELDS)]:
        if not fact["notes"].strip(): fail(prop["id"], "elemental content facts require scope notes")
        reported = fact.get("status") == "reported"
        if reported and not fact["text"].strip(): fail(prop["id"], "reported elemental facts require text")
        require(fact, ("method", "condition") if reported or name == "definition" else ("condition",))
    if prop["conditions"]["direction"]["status"] == "not_applicable":
        fail(prop["id"], "elemental mass content does not establish direction inapplicability")
    cell = definition["source_result_cell"]
    if any(not cell[n].strip() or cell[n] != cell[n].strip()
           for n in ("table_id", "row_key", "column_key")):
        fail(prop["id"], "elemental content source cell requires canonical unpadded table,row,column")
    require(cell, ("reported_value", "classification"))
    cells = {e["locator"] for e in prop["evidence"] if e["source_id"] == source and
             e["url"] == document and "reported_value" in e["supports"]}
    if not any(e["locator"] in cells and {"reported_value", "classification"} <= set(e["supports"])
               and e["source_id"] == source and e["url"] == document for e in cell["evidence"]):
        fail(prop["id"], "source cell must identify selected elemental content value evidence")
    analyte = prop["elemental_analyte"]
    if not analyte["notes"].strip(): fail(prop["id"], "elemental analyte requires scope notes")
    require(analyte, ("reported_value", "classification"))
    if cell["column_key"] != analyte["symbol"]:
        fail(prop["id"], "elemental analyte must match canonical P/Cl source column")
    if not any(e["source_id"] == source and e["url"] == document and e["locator"] in cells
               and {"reported_value", "classification"} <= set(e["supports"]) for e in analyte["evidence"]):
        fail(prop["id"], "elemental analyte requires selected primary source-cell evidence")
    if definition["measurement_environment"]["status"] != "reported":
        for name in ("temperature", "conditioning"):
            if prop["conditions"][name]["status"] in ("reported", "not_applicable"):
                fail(prop["id"], "unknown XRF environment cannot inherit other-method conditions")
    if prop["conditions"]["loading_rate"]["status"] in ("reported", "not_applicable"):
        fail(prop["id"], "XRF elemental contents do not inherit mechanical or rheology loading rates")


def guard_cell(prop, seen):
    if prop["quantity"] != QUANTITY: return
    cell = prop["elemental_content_definition"]["source_result_cell"]
    key = "elemental_content_cell:" + json.dumps([prop["source_id"], prop["source_document"]["url"],
        *(cell[n] for n in ("table_id", "row_key", "column_key"))], ensure_ascii=False)
    if key in seen: raise ValueError(prop["id"] + ": same elemental content source cell must be revised, not duplicated")
    seen.add(key)
    # A changed declared address/analyte cannot turn the same inspected value
    # locator into a second result. Distinct P/Cl columns need distinct cells.
    source, document = prop["source_id"], prop["source_document"]["url"]
    locators = {e["locator"].strip() for e in prop["evidence"]
                if e["source_id"] == source and e["url"] == document and "reported_value" in e["supports"]}
    for locator in locators:
        key = "elemental_content_locator:" + json.dumps([source, document, locator], ensure_ascii=False)
        if key in seen:
            raise ValueError(prop["id"] + ": same inspected elemental value locator must be revised, not duplicated")
        seen.add(key)


def validate_state_context(prop, state):
    if prop["quantity"] != QUANTITY: return
    definition = prop["elemental_content_definition"]
    if definition["sample_preparation_and_reaction_context"]["status"] != "reported":
        for name in ("processing", "conditioning", "temper_or_heat_treatment"):
            if state["state"][name]["status"] in ("reported", "not_applicable"):
                raise ValueError(prop["id"] + ": unknown XRF preparation cannot inherit another specimen history")
