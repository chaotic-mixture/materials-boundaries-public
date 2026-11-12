"""Source-qualified process-event times; no shared clock or cure inference."""
from copy import deepcopy

QUANTITY = "foam_reaction_event_time"
EVENTS = ("foaming_start", "gel_string", "tack_free", "foam_rise")
FACT_FIELDS = ("clock_origin", "endpoint_criterion", "apparatus_or_observation_method",
               "mixing_reference", "reaction_test_geometry_charge", "reaction_test_environment",
               "replicate_and_piece_relationship")
LABEL_KEYS = ("code_" + QUANTITY, "reaction_event", "reaction_time_definition",
              "reaction_time_reference_notice", *("code_" + name for name in EVENTS),
              *("reaction_time_" + name for name in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref("evidence"), 1)
    definitions["reaction_time_fact"] = {"oneOf": [
        obj({"status": {"const": "reported"}, "text": text, "evidence": evidence, "notes": text}),
        obj({"status": {"type": "string", "enum": ["not_reported_in_inspected_source", "not_verified"]},
             "text": {"type": "null"}, "evidence": evidence, "notes": text}),
    ]}
    definitions["reaction_event"] = obj({
        "code": {"type": "string", "enum": list(EVENTS)}, "evidence": evidence, "notes": text,
    })
    definitions["reaction_time_definition"] = obj({
        "basis": {"const": "source_reported_process_event_time"},
        **{name: ref("reaction_time_fact") for name in FACT_FIELDS},
        "evidence": evidence, "notes": text,
    })
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"]
                  if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"]["unit_code"] = {"const": "s"}
    definitions["reaction_time_reported_value"] = scalar
    branch = deepcopy(base)
    fields = branch["properties"]
    fields.update(quantity={"const": QUANTITY}, quantity_dimension={"const": "time"},
                  reported_value=ref("reaction_time_reported_value"),
                  reaction_event=ref("reaction_event"),
                  reaction_time_definition=ref("reaction_time_definition"),
                  evidence_kind={"const": "published_experimental_reference"},
                  reporting_basis={"const": "reported_summary"},
                  determination_basis={"const": "source_reports_measurement"},
                  density_basis={"type": "null"})
    fields.pop("derivation", None)
    fields["method_definition"]["properties"]["type"] = {"const": "source_reported_conventional"}
    fields["method_definition"]["properties"]["extraction_window"] = {"type": "null"}
    branch["required"].extend(["reaction_event", "reaction_time_definition"])
    return branch


def validate(prop, fail):
    if prop["quantity"] != QUANTITY:
        return
    source, document = prop["source_id"], prop["source_document"]["url"]
    event = prop["reaction_event"]
    if not event["notes"].strip():
        fail(prop["id"], "reaction event requires explanatory notes")
    cells = {e["locator"] for e in prop["evidence"] if e["source_id"] == source
             and e["url"] == document and "reported_value" in e["supports"]}
    if not any(e["source_id"] == source and e["url"] == document
               and e["locator"] in cells and {"reported_value", "classification"} <= set(e["supports"])
               for e in event["evidence"]):
        fail(prop["id"], "reaction event needs matching primary source-cell value and classification evidence")
    if prop["conditions"]["direction"]["status"] == "not_applicable":
        fail(prop["id"], "a scalar reaction time does not establish direction inapplicability")
    definition = prop["reaction_time_definition"]
    for name, fact in [("reaction_time_definition", definition),
                       *((name, definition[name]) for name in FACT_FIELDS)]:
        if not fact["notes"].strip():
            fail(prop["id"], "reaction time facts require explanatory notes")
        reported = fact.get("status") == "reported"
        if reported and not fact["text"].strip():
            fail(prop["id"], "reported reaction time facts require text")
        roles = ("method", "condition") if reported or name == "reaction_time_definition" else ("condition",)
        for role in roles:
            if not any(e["source_id"] == source and e["url"] == document
                       and role in e["supports"] for e in fact["evidence"]):
                fail(prop["id"], "reaction time facts require primary inspected-document " + role + " evidence")
