"""Source-qualified extension lengths, independent of strain and force."""
from copy import deepcopy

QUANTITY = "tensile_extension_at_failure"
FACT_FIELDS = ("measurement_channel", "reference_length", "failure_criterion")
LABEL_KEYS = (
    "code_" + QUANTITY, "extension_definition", "extension_correction_basis",
    "code_source_reported_uncorrected", "extension_measurement_channel",
    "extension_reference_length", "extension_failure_criterion", "extension_reference_notice",
)


def schema_branch(definitions, base, *, text, obj, array, ref):
    """Append a closed scalar-mm branch without changing legacy definitions."""
    evidence = array(ref("evidence"), 1)
    definitions["extension_fact"] = {"oneOf": [
        obj({"status": {"const": "reported"}, "text": text,
             "evidence": evidence, "notes": text}),
        obj({"status": {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]},
             "text": {"type": "null"}, "evidence": evidence, "notes": text}),
    ]}
    definitions["extension_definition"] = obj({
        "correction_basis": {"const": "source_reported_uncorrected"},
        **{name: ref("extension_fact") for name in FACT_FIELDS},
        "evidence": evidence, "notes": text,
    })
    scalar = next(deepcopy(value) for value in definitions["reported_value"]["oneOf"]
                  if value["properties"]["kind"].get("const") == "scalar")
    scalar["properties"]["unit_code"] = {"const": "mm"}
    definitions["extension_reported_value"] = scalar
    branch = deepcopy(base)
    fields = branch["properties"]
    fields.update(quantity={"const": QUANTITY}, quantity_dimension={"const": "length"},
                  reported_value=ref("extension_reported_value"),
                  extension_definition=ref("extension_definition"),
                  evidence_kind={"const": "published_experimental_reference"},
                  reporting_basis={"const": "reported_summary"},
                  determination_basis={"const": "source_reports_measurement"},
                  density_basis={"type": "null"})
    fields.pop("derivation", None)
    fields["method_definition"]["properties"]["type"] = {"const": "source_reported_conventional"}
    # A modulus fit window cannot stand in for a failure criterion.
    fields["method_definition"]["properties"]["extraction_window"] = {"type": "null"}
    branch["required"].append("extension_definition")
    return branch


def validate(prop, fail):
    """Check declared evidence scope; never infer a channel or normalize length."""
    if prop["quantity"] != QUANTITY:
        return
    source, document = prop["source_id"], prop["source_document"]["url"]
    definition = prop["extension_definition"]
    for name, fact in [("extension_definition", definition),
                       *((name, definition[name]) for name in FACT_FIELDS)]:
        if not fact["notes"].strip():
            fail(prop["id"], "extension definitions and unknowns need explanatory notes")
        reported = fact.get("status") == "reported"
        if reported and not fact["text"].strip():
            fail(prop["id"], "reported extension facts need nonblank text")
        roles = ("method", "condition") if name == "extension_definition" or reported else ("condition",)
        for role in roles:
            if not any(item["source_id"] == source and item["url"] == document
                       and role in item["supports"] for item in fact["evidence"]):
                fail(prop["id"], "extension facts need primary inspected-document " + role + " evidence")
