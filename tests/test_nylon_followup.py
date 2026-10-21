"""One historical family bridge preserves the measured state's unknown chemistry."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from scripts.extract_curated_filament_cells import (
    Cell, DATASET_SOURCE_ID, HEADERS, SERIES_STATEMENT,
    extract_filament_facts, verify_spec_values,
)
from scripts.integrate_material_candidates import write_immutable_package
from scripts.prepare_formulation_packet import (
    CLASSIFICATION_ONLY_SOURCES, NYLON_IDENTITY_SOURCES,
    TOUGH_PLA_CLASSIFICATION_SOURCE, _references_source, _review_checks,
    _source_rights_available, record_sha256, validate_identity_collisions,
)

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "experimental/material-batches/zenodo-8089569-nylon-followup-20261021"
PRIOR = ROOT / "experimental/material-batches/zenodo-8089569-tough-pla-followup-20261021"
IDENTITY = "mat_aniskevich_2023_ultimaker_nylon"
STATE = "state_aniskevich_2023_ultimaker_nylon_transparent_filament"
SDS = "ultimaker_nylon_sds_20190114"
PRICING = "ultimaker_nylon_pricing_20210504"
PA12 = "mat_zakrecki2025_pa12_pa2200"
VALUES = ("2774.8837867501061", "39.07712093742888", "209.43237576723914", "3.6781068579660881")


def document(name):
    return json.loads((CANDIDATE / name).read_bytes())


def fixture():
    # Independent selected-cell transcription; no original source assets ship.
    measured = {address: Cell(value, "s") for address, value in HEADERS.items()}
    measured["B9"] = Cell("PA (Nylon) Transparent", "s")
    measured["C9"] = Cell("579")
    measured.update({column + "9": Cell(value) for column, value in zip("EFGH", VALUES)})
    sheets = {"Tested materials": {"B25": Cell("Polyamide", "s"),
                                  "C25": Cell("PA, Nylon Transparent 1647", "s"),
                                  "D25": Cell("Ultimaker", "s")},
              "Tensile modulus": measured, "Samples": {"C27": Cell(SERIES_STATEMENT, "s")}}
    selection = [{"identity_id": IDENTITY, "states": [{
        "material_state_id": STATE, "tested_row": 25,
        "tested_designation": "PA, Nylon Transparent 1647", "measurement_row": 9,
        "measurement_designation": "PA (Nylon) Transparent"}]}]
    return sheets, selection


class NylonFollowupTests(unittest.TestCase):
    def test_one_historical_family_binds_original_measured_cells(self):
        sheets, selection = fixture()
        facts = extract_filament_facts(sheets, selection)
        spec = document("packet-spec.json")
        self.assertEqual(spec["review"]["workbook_selection"], selection)
        self.assertEqual(facts["schema"], "curated-filament-cells/2")
        self.assertEqual(len(facts["selected"]), 1)
        row = facts["selected"][0]
        self.assertEqual((row["identity_id"], row["material_state_id"]), (IDENTITY, STATE))
        self.assertEqual((row["tested_row"], row["measurement_row"]), (25, 9))
        self.assertEqual([item["value_text"] for item in row["measurements"]], [VALUES[0], VALUES[2]])
        self.assertEqual([item["reported_companion"]["value_text"] for item in row["measurements"]],
                         [VALUES[1], VALUES[3]])
        self.assertTrue(all(item["unit_text"] == "MPa " for item in row["measurements"]))
        self.assertTrue(all(item["reported_companion"]["statistical_type"] is None for item in row["measurements"]))
        self.assertIsNone(facts["protocol"]["exact_sample_count"])
        self.assertIsNone(facts["protocol"]["measured_test_standard"])
        verify_spec_values(facts, spec)
        altered = deepcopy(sheets)
        altered["Tensile modulus"]["C9"] = Cell("999999")
        altered["Tensile modulus"]["I9"] = Cell("888888")
        self.assertEqual(extract_filament_facts(altered, selection), facts)

    def test_grouped_ownership_and_missing_measurements_fail_closed(self):
        sheets, selection = fixture()
        for variant in ("duplicate identity", "duplicate state", "empty states", "wrong join", "missing join"):
            with self.subTest(selection=variant):
                altered = deepcopy(selection)
                source = deepcopy(sheets)
                states = altered[0]["states"]
                if variant == "duplicate identity":
                    altered.append(deepcopy(altered[0]))
                elif variant == "duplicate state":
                    states.append(deepcopy(states[0]))
                elif variant == "empty states":
                    states.clear()
                elif variant == "wrong join":
                    source["Tested materials"]["C25"] = Cell("PA, Nylon Transparent 1648", "s")
                else:
                    source["Tensile modulus"].pop("B9")
                with self.assertRaises(ValueError):
                    extract_filament_facts(source, altered)
        facts = extract_filament_facts(sheets, selection)
        for variant in ("duplicate identity", "missing state", "duplicate state", "identity owner",
                        "property owner", "property membership", "missing property", "wrong designation"):
            with self.subTest(authored=variant):
                spec = document("packet-spec.json")
                formulation = spec["formulations"][0]
                state = formulation["states"][0]
                fields = state["record"]["fields"]
                if variant == "duplicate identity":
                    spec["formulations"].append(deepcopy(formulation))
                elif variant == "missing state":
                    formulation["states"].clear()
                elif variant == "duplicate state":
                    formulation["states"].append(deepcopy(state))
                elif variant == "identity owner":
                    fields["identity_id"] = PA12
                elif variant == "property owner":
                    state["properties"][0]["fields"]["material_state_id"] = "state_test_other"
                elif variant == "property membership":
                    fields["property_ids"].pop()
                elif variant == "missing property":
                    state["properties"].pop()
                else:
                    fields["source_designation"] = "PA (Nylon) Transparent"
                with self.assertRaises(ValueError):
                    verify_spec_values(facts, spec)

    def test_measured_columns_units_zeros_and_deviations_fail_closed(self):
        sheets, selection = fixture()
        facts = extract_filament_facts(sheets, selection)
        for column in "EFGH":
            for variant in ("missing", "blank", "zero", "negative", "formula"):
                with self.subTest(column=column, value=variant):
                    altered = deepcopy(sheets)
                    cells = altered["Tensile modulus"]
                    if variant == "missing":
                        cells.pop(column + "9")
                    else:
                        value = {"blank": "", "zero": "0", "negative": "-1", "formula": VALUES[0]}[variant]
                        cells[column + "9"] = Cell(value, formula=variant == "formula")
                    with self.assertRaises(ValueError):
                        extract_filament_facts(altered, selection)
            for unit in ("GPa", "unknown", ""):
                with self.subTest(column=column, unit=unit):
                    altered = deepcopy(sheets)
                    altered["Tensile modulus"][column + "4"] = Cell(unit, "s")
                    with self.assertRaises(ValueError):
                        extract_filament_facts(altered, selection)
        for variant in ("reference value", "reference locator", "wrong unit", "wrong deviation", "typed uncertainty"):
            with self.subTest(authored=variant):
                spec = document("packet-spec.json")
                prop = spec["formulations"][0]["states"][0]["properties"][0]["fields"]
                if variant == "reference value":
                    prop["reported_value"].update(value_text="579", number="579")
                elif variant == "reference locator":
                    prop["evidence"][0]["locator"] = "Tensile modulus!C9; Tensile modulus!F9"
                elif variant == "wrong unit":
                    spec["contexts"]["property"]["filament"]["reported_value"]["unit_code"] = "GPa"
                elif variant == "wrong deviation":
                    prop["uncertainty_note"] = "Source avedev = 1 MPa at Tensile modulus!F9"
                else:
                    spec["contexts"]["property"]["filament"]["uncertainty"] = {"type": "reported_standard_deviation"}
                with self.assertRaises(ValueError):
                    verify_spec_values(facts, spec)

    def test_frozen_packet_counts_and_historical_unknowns(self):
        packet = document("prepared-packet.json")
        graph = packet["catalogs"]
        self.assertEqual([len(graph["materials"][key]) for key in ("identities", "grades", "records")], [1, 0, 1])
        self.assertEqual(len(graph["properties"]["records"]), 2)
        self.assertEqual([packet["report"]["delta"][key]
                          for key in ("identities", "grades", "states", "properties", "sources")], [1, 0, 1, 2, 2])
        self.assertTrue(packet["report"]["handoff_ready"])
        self.assertEqual(packet["input"]["review"]["formal_admitted_delta"], 0)
        identity = graph["materials"]["identities"][0]
        state = graph["materials"]["records"][0]
        self.assertEqual((identity["id"], identity["category"]), (IDENTITY, "polymer"))
        self.assertEqual((state["id"], state["identity_id"], state["grade_id"]), (STATE, IDENTITY, None))
        composition = state["state"]["composition_or_purity"]
        self.assertEqual((composition["status"], composition["text"], composition["evidence"]),
                         ("not_reported_in_inspected_source", None, []))
        self.assertIn("not supplier, SKU, color or measured values", identity["identity_scope"])
        self.assertIn("not the exact studied lot", identity["identity_scope"])
        sources = {row["id"]: row for row in graph["sources"]["records"]}
        self.assertEqual(set(sources), {DATASET_SOURCE_ID, SDS, PRICING})
        old = json.loads((PRIOR / "prepared-packet.json").read_bytes())["catalogs"]["sources"]["records"]
        self.assertEqual(sources[DATASET_SOURCE_ID], next(row for row in old if row["id"] == DATASET_SOURCE_ID))
        summary = document("source-review.json")
        for source_id in (SDS, PRICING):
            source = sources[source_id]
            self.assertEqual(record_sha256(source), NYLON_IDENTITY_SOURCES[source_id]["sha256"])
            external = json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            self.assertEqual(sha256(external).hexdigest(),
                             summary["external_review_record_sha256_without_trailing_newline"][source_id])
            self.assertIsNone(source["license"]["identifier"])
            self.assertNotEqual(source["license"]["status"], "explicit_reuse_license_verified")
            self.assertTrue(_source_rights_available(source, {}, graph))
            for record in [state, *graph["materials"]["grades"], *graph["properties"]["records"]]:
                self.assertFalse(_references_source(record, source_id, set(source["urls"])))
        self.assertEqual(summary["identity_review"]["relevant_existing_identity"], PA12)
        pricing = next(row for row in summary["verified_historical_facts"] if row["source_id"] == PRICING)
        self.assertFalse(pricing["description_token_is_chemical_grade"])
        self.assertIsNone(pricing["package_mass"])
        self.assertEqual(summary["acquisition_accounting"]["failures"], 1)
        self.assertEqual(summary["acquisition_accounting"]["retries"], 0)
        for prop in graph["properties"]["records"]:
            self.assertEqual(prop["source_id"], DATASET_SOURCE_ID)
            self.assertEqual((prop["reporting_basis"], prop["summary_statistic"]), ("reported_summary", "reported_mean"))
            self.assertIsNone(prop["uncertainty"])
            self.assertIsNone(prop["sample_count"]["value"])
            self.assertIsNone(prop["conditions"]["test_standard"]["text"])
            self.assertEqual(prop["conditions"]["loading_rate"]["text"], "10 mm/min")
        self.assertEqual(set(CLASSIFICATION_ONLY_SOURCES), {
            "protopasta_conductive_pla_faq", "addnorth_product_catalogue_2022", "makerbot_method_materials_20191119"})
        old_graph = json.loads((PRIOR / "prepared-packet.json").read_bytes())["catalogs"]
        tough = next(row for row in old_graph["sources"]["records"] if row["id"] == TOUGH_PLA_CLASSIFICATION_SOURCE["id"])
        self.assertTrue(_source_rights_available(tough, {}, old_graph))

    def test_dual_sources_require_both_exact_identity_only_records(self):
        original = document("prepared-packet.json")["catalogs"]
        original_review = document("prepared-packet.json")["input"]["review"]
        self.assertEqual(_review_checks(original_review, original, {}), [])
        for variant in ("remove both", "rename both and forge licenses"):
            with self.subTest(whole_bridge=variant):
                graph, review = deepcopy(original), deepcopy(original_review)
                if variant == "remove both":
                    graph["sources"]["records"] = [row for row in graph["sources"]["records"] if row["id"] == DATASET_SOURCE_ID]
                    graph["materials"]["identities"][0]["evidence"] = [
                        row for row in graph["materials"]["identities"][0]["evidence"] if row["source_id"] == DATASET_SOURCE_ID]
                    review["source_reviews"] = [row for row in review["source_reviews"] if row["source_id"] == DATASET_SOURCE_ID]
                else:
                    for row in graph["sources"]["records"]:
                        if row["id"] in (SDS, PRICING):
                            row["id"] += "_renamed"
                            row["license"] = {"status": "explicit_reuse_license_verified", "identifier": "CC-BY-4.0"}
                    for row in graph["materials"]["identities"][0]["evidence"] + review["source_reviews"]:
                        if row["source_id"] in (SDS, PRICING):
                            row["source_id"] += "_renamed"
                self.assertIn("Historical Nylon identity requires both exact identity-only sources.",
                              _review_checks(review, graph, {}))
        for target in (SDS, PRICING):
            for variant in ("missing record", "missing citation", "duplicate record", "notice", "license",
                            "source id", "category", "other identity", "extra identity", "support tag",
                            "property source", "source document", "state evidence", "grade evidence"):
                with self.subTest(source=target, variant=variant):
                    graph = deepcopy(original)
                    source = next(row for row in graph["sources"]["records"] if row["id"] == target)
                    identity = graph["materials"]["identities"][0]
                    reference = next(row for row in identity["evidence"] if row["source_id"] == target)
                    if variant == "missing record":
                        graph["sources"]["records"].remove(source)
                    elif variant == "missing citation":
                        identity["evidence"].remove(reference)
                    elif variant == "duplicate record":
                        graph["sources"]["records"].append(deepcopy(source))
                    elif variant == "notice":
                        source["claim_notes"].append("Rehashing cannot expand the reviewed fact scope.")
                    elif variant == "license":
                        source["license"] = {"status": "explicit_reuse_license_verified", "identifier": "CC-BY-4.0"}
                    elif variant == "source id":
                        source["id"] += "_other_revision"
                    elif variant == "category":
                        identity["category"] = "composite"
                    elif variant == "other identity":
                        identity["id"] = PA12
                    elif variant == "extra identity":
                        extra = deepcopy(identity)
                        extra["id"] += "_black"
                        graph["materials"]["identities"].append(extra)
                    elif variant == "support tag":
                        reference["supports"] = ["material_identity", "classification"]
                    elif variant == "property source":
                        graph["properties"]["records"][0]["source_id"] = target
                    elif variant == "source document":
                        graph["properties"]["records"][0]["source_document"]["url"] = source["urls"][0]
                    elif variant == "state evidence":
                        graph["materials"]["records"][0]["evidence"].append({**reference, "supports": ["state"]})
                    else:
                        graph["materials"]["grades"].append({"id": "grade_test_nylon_promotion",
                            "identity_id": IDENTITY, "evidence": [{**reference, "supports": ["grade"]}]})
                    # Mutating either partner must close the gate for both; a
                    # surviving frozen partner cannot pass the bridge alone.
                    for source_id in (SDS, PRICING):
                        selected = next((row for row in graph["sources"]["records"] if row["id"] == source_id),
                                        next(row for row in original["sources"]["records"] if row["id"] == source_id))
                        self.assertFalse(_source_rights_available(selected, {}, graph))

    def test_source_scoped_alias_collisions_and_sparse_replay(self):
        graph = document("prepared-packet.json")["catalogs"]
        # Simulate another identity already owning this measured-source label.
        # This is a structural collision fixture, not an assertion that the
        # actual PA12 measurement source is the Zenodo workbook.
        for variant in ("designation", "alias"):
            with self.subTest(collision=variant):
                baseline = deepcopy(graph)
                baseline["materials"]["identities"][0]["id"] = PA12
                baseline["materials"]["records"][0]["identity_id"] = PA12
                candidate = deepcopy(graph)
                identity = candidate["materials"]["identities"][0]
                state = candidate["materials"]["records"][0]
                identity.update(name="A changed display name", names={"en": "Another display name"}, aliases=[])
                state.update(name="Another measured state", names={"en": "Renamed state"})
                if variant == "alias":
                    state["source_designation"] = "Renamed source designation"
                    identity["aliases"] = [{"language": "en", "text": "  PA, Nylon Transparent 1647  "}]
                with self.assertRaisesRegex(ValueError, "collides with another identity"):
                    validate_identity_collisions(baseline, candidate)
        sheets, selection = fixture()
        facts = extract_filament_facts(sheets, selection)
        spec = document("packet-spec.json")
        spec["formulations"][0]["states"][0]["properties"].reverse()
        spec["source_records"].reverse()
        verify_spec_values(facts, spec)
        self.assertEqual(extract_filament_facts(sheets, spec["review"]["workbook_selection"]), facts)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "facts.json"
            self.assertTrue(write_immutable_package(output, facts))
            before = output.read_bytes(), output.stat().st_mtime_ns
            self.assertFalse(write_immutable_package(output, extract_filament_facts(sheets, selection)))
            self.assertEqual((output.read_bytes(), output.stat().st_mtime_ns), before)


if __name__ == "__main__":
    unittest.main()
