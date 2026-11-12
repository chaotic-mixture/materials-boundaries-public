"""Source-reported directional mean cell-size ratio; not material isotropy."""
from copy import deepcopy
from decimal import Decimal

QUANTITY = "foam_cell_geometric_anisotropy_ratio"
UNIT = "ratio_foam_cell_geometric_anisotropy"
FACT_FIELDS = ("numerator_direction_and_measure", "denominator_direction_and_measure",
               "imaging_and_analysis", "sectioning_and_sampling", "averaging_and_ratio_reduction",
               "cell_selection_and_count", "preconditioning")
LABEL_KEYS = ("code_" + QUANTITY, "cell_anisotropy_definition",
              "cell_anisotropy_reference_notice",
              *("cell_anisotropy_" + name for name in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref("evidence"), 1)
    definitions["cell_anisotropy_fact"] = {"oneOf": [
        obj({"status": {"const": "reported"}, "text": text,
             "evidence": evidence, "notes": text}),
        obj({"status": {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]},
             "text": {"type": "null"}, "evidence": evidence, "notes": text}),
    ]}
    definitions["cell_anisotropy_definition"] = obj({
        "basis": {"const": "source_reported_ratio_of_directional_mean_cell_sizes"},
        **{name: ref("cell_anisotropy_fact") for name in FACT_FIELDS},
        "evidence": evidence, "notes": text,
    })
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"]
                  if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"]["unit_code"] = {"const": UNIT}
    scalar["properties"]["number"] = {"type": "string", "maxLength": 28,
        "pattern": r"^(?=[0-9.]*[1-9])(?:0|[1-9][0-9]*)(?:\.[0-9]{1,24})?(?![\s\S])"}
    definitions["cell_anisotropy_reported_value"] = scalar

    # Keep every legacy definition unchanged. Only this branch can use its
    # dedicated absolute ratio scale, including multiple reported measures.
    def specialize(value):
        if isinstance(value, dict):
            if value.get("$ref") == "#/$defs/reported_measure":
                value["$ref"] = "#/$defs/cell_anisotropy_reported_measure"
            fields = value.get("properties", {})
            unit = fields.get("unit_code", {})
            if "enum" in unit:
                fields["unit_code"] = {"const": UNIT}
            for child in value.values():
                specialize(child)
        elif isinstance(value, list):
            for child in value:
                specialize(child)
    for old, new in (("reported_measure", "cell_anisotropy_reported_measure"),
                     ("uncertainty", "cell_anisotropy_uncertainty")):
        definitions[new] = deepcopy(definitions[old])
        specialize(definitions[new])
    branch = deepcopy(base)
    fields = branch["properties"]
    fields.update(quantity={"const": QUANTITY}, quantity_dimension={"const": "dimensionless"},
                  reported_value=ref("cell_anisotropy_reported_value"),
                  cell_anisotropy_definition=ref("cell_anisotropy_definition"),
                  uncertainty={"anyOf": [ref("cell_anisotropy_uncertainty"), {"type": "null"}]},
                  evidence_kind={"const": "published_experimental_reference"},
                  reporting_basis={"const": "reported_summary"},
                  determination_basis={"const": "source_reports_measurement"},
                  density_basis={"type": "null"})
    fields.pop("derivation", None)
    fields["method_definition"]["properties"]["type"] = {"const": "source_reported_conventional"}
    fields["method_definition"]["properties"]["extraction_window"] = {"type": "null"}
    branch["required"].append("cell_anisotropy_definition")
    return branch


def validate(prop, fail):
    if prop["quantity"] != QUANTITY:
        return
    if Decimal(prop["reported_value"]["number"]) <= 0:
        fail(prop["id"], "cell anisotropy central ratio must be strictly positive; do not clamp source anomalies")
    if prop["conditions"]["direction"]["status"] == "not_applicable":
        fail(prop["id"], "scalar cell anisotropy ratio does not establish direction inapplicability")
    definition = prop["cell_anisotropy_definition"]
    source, document = prop["source_id"], prop["source_document"]["url"]
    for name, fact in [("cell_anisotropy_definition", definition),
                       *((name, definition[name]) for name in FACT_FIELDS)]:
        if not fact["notes"].strip():
            fail(prop["id"], "cell anisotropy facts require explanatory notes")
        reported = fact.get("status") == "reported"
        if reported and not fact["text"].strip():
            fail(prop["id"], "reported cell anisotropy facts require text")
        roles = ("method", "condition") if reported or name == "cell_anisotropy_definition" else ("condition",)
        for role in roles:
            if not any(e["source_id"] == source and e["url"] == document
                       and role in e["supports"] for e in fact["evidence"]):
                fail(prop["id"], "cell anisotropy facts require primary inspected-document " + role + " evidence")
