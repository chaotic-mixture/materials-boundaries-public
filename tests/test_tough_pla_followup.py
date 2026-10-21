"""Two original color series retain one reviewed identity and separate measurements."""
from copy import deepcopy
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
    CLASSIFICATION_ONLY_SOURCES, TOUGH_PLA_CLASSIFICATION_SOURCE,
    _source_rights_available, record_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "experimental/material-batches/zenodo-8089569-tough-pla-followup-20261021"
PRIOR = ROOT / "experimental/material-batches/zenodo-8089569-filaments-20261021"
IDENTITY = "mat_aniskevich_2023_ultimaker_tough_pla"
SOURCE = "ultimaker_tough_pla_sds_20221222"
# Independently transcribed selected facts; original source assets are not bundled.
ROWS = (
    (10, 8, "white", "PLA Tough White 20231", "PLA Tough White",
     ("1952.8040383954526", "119.08536932981231", "48.770237778441711", "0.31063412976455568")),
    (11, 7, "black", "PLA Tough Black 202300", "PLA Tough Black",
     ("2251.0910289257272", "194.28002770731121", "41.745899122457502", "2.4433159119274221")),
)


def document(name):
    return json.loads((CANDIDATE / name).read_bytes())


def fixture():
    measured = {address: Cell(value, "s") for address, value in HEADERS.items()}
    materials, states = {}, []
    for tested_row, row, color, designation, measured_name, values in ROWS:
        materials["C" + str(tested_row)] = Cell(designation, "s")
        materials["D" + str(tested_row)] = Cell("Ultimaker", "s")
        measured["B" + str(row)] = Cell(measured_name, "s")
        measured.update({column + str(row): Cell(value) for column, value in zip("EFGH", values)})
        states.append({"material_state_id": "state_aniskevich_2023_ultimaker_tough_pla_" + color + "_filament",
                       "tested_row": tested_row, "tested_designation": designation,
                       "measurement_row": row, "measurement_designation": measured_name})
    return ({"Tested materials": materials, "Tensile modulus": measured,
             "Samples": {"C27": Cell(SERIES_STATEMENT, "s")}}, [{"identity_id": IDENTITY, "states": states}])


class ToughPlaFollowupTests(unittest.TestCase):
    def test_two_color_series_bind_one_identity_and_original_cells(self):
        sheets, selection = fixture()
        facts = extract_filament_facts(sheets, selection)
        spec = document("packet-spec.json")
        self.assertEqual(spec["review"]["workbook_selection"], selection)
        self.assertEqual(facts["schema"], "curated-filament-cells/2")
        self.assertEqual({row["identity_id"] for row in facts["selected"]}, {IDENTITY})
        self.assertEqual(len(facts["selected"]), 2)
        self.assertEqual(len({row["material_state_id"] for row in facts["selected"]}), 2)
        by_row = {row["measurement_row"]: row for row in facts["selected"]}
        for tested_row, row, _, designation, _, values in ROWS:
            selected = by_row[row]
            self.assertEqual((selected["tested_row"], selected["tested_designation"]), (tested_row, designation))
            self.assertEqual([item["value_text"] for item in selected["measurements"]], [values[0], values[2]])
            self.assertEqual([item["reported_companion"]["value_text"] for item in selected["measurements"]],
                             [values[1], values[3]])
            self.assertTrue(all(item["unit_text"] == "MPa " for item in selected["measurements"]))
        verify_spec_values(facts, spec)
        reordered = deepcopy(selection)
        reordered[0]["states"].reverse()
        self.assertEqual(extract_filament_facts(sheets, reordered), facts)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "facts.json"
            self.assertTrue(write_immutable_package(output, facts))
            before = output.read_bytes(), output.stat().st_mtime_ns
            self.assertFalse(write_immutable_package(output, extract_filament_facts(sheets, reordered)))
            self.assertEqual((output.read_bytes(), output.stat().st_mtime_ns), before)

    def test_grouped_selection_and_authored_ownership_fail_closed(self):
        sheets, selection = fixture()
        for variant in ("identity group", "state id", "tested row", "measurement row", "empty states", "mixed shape"):
            with self.subTest(selection=variant):
                altered = deepcopy(selection)
                states = altered[0]["states"]
                if variant == "identity group":
                    altered.append(deepcopy(altered[0]))
                elif variant in ("state id", "tested row", "measurement row"):
                    key = {"state id": "material_state_id", "tested row": "tested_row",
                           "measurement row": "measurement_row"}[variant]
                    states[1][key] = states[0][key]
                elif variant == "empty states":
                    states.clear()
                else:
                    altered.append({"identity_id": "mat_test_other", **states[0]})
                with self.assertRaises(ValueError):
                    extract_filament_facts(sheets, altered)
        facts = extract_filament_facts(sheets, selection)
        for variant in ("duplicate identity", "missing state", "duplicate state", "identity owner",
                        "property owner", "property membership", "missing property"):
            with self.subTest(authored=variant):
                spec = document("packet-spec.json")
                formulation = spec["formulations"][0]
                states = formulation["states"]
                if variant == "duplicate identity":
                    spec["formulations"].append(deepcopy(formulation))
                elif variant == "missing state":
                    states.pop()
                elif variant == "duplicate state":
                    states[1]["record"]["fields"]["id"] = states[0]["record"]["fields"]["id"]
                elif variant == "identity owner":
                    states[0]["record"]["fields"]["identity_id"] = "mat_test_other"
                elif variant == "property owner":
                    states[0]["properties"][0]["fields"]["material_state_id"] = states[1]["record"]["fields"]["id"]
                elif variant == "property membership":
                    states[0]["record"]["fields"]["property_ids"] = states[1]["record"]["fields"]["property_ids"]
                else:
                    states[0]["properties"].pop()
                with self.assertRaises(ValueError):
                    verify_spec_values(facts, spec)

    def test_grouped_binding_excludes_reference_units_and_invented_statistics(self):
        sheets, selection = fixture()
        facts = extract_filament_facts(sheets, selection)
        for row in (7, 8):
            sheets["Tensile modulus"]["C" + str(row)] = Cell("999999")
            sheets["Tensile modulus"]["I" + str(row)] = Cell("888888")
        self.assertEqual(extract_filament_facts(sheets, selection), facts)
        self.assertIsNone(facts["protocol"]["exact_sample_count"])
        self.assertIsNone(facts["protocol"]["measured_test_standard"])
        self.assertTrue(all(item["reported_companion"]["statistical_type"] is None
                            for row in facts["selected"] for item in row["measurements"]))
        for bad_unit in ("GPa", "unknown", ""):
            with self.subTest(unit=bad_unit):
                altered = deepcopy(sheets)
                altered["Tensile modulus"]["G4"] = Cell(bad_unit, "s")
                with self.assertRaises(ValueError):
                    extract_filament_facts(altered, selection)
        for variant in ("reference value", "reference locator", "wrong unit", "avedev", "typed uncertainty",
                        "other color value", "corrected code"):
            with self.subTest(binding=variant):
                spec = document("packet-spec.json")
                states = spec["formulations"][0]["states"]
                prop = states[0]["properties"][0]["fields"]
                if variant == "reference value":
                    prop["reported_value"].update(value_text="999999", number="999999")
                elif variant == "reference locator":
                    prop["evidence"][0]["locator"] = "Tensile modulus!C8; Tensile modulus!F8"
                elif variant == "wrong unit":
                    prop["reported_value"]["unit_code"] = "GPa"
                elif variant == "avedev":
                    prop["uncertainty_note"] = "Source avedev = 1 MPa at Tensile modulus!F8"
                elif variant == "typed uncertainty":
                    prop["uncertainty"] = {"type": "reported_standard_deviation"}
                elif variant == "other color value":
                    prop["reported_value"] = deepcopy(states[1]["properties"][0]["fields"]["reported_value"])
                else:
                    states[0]["record"]["fields"]["source_designation"] = "PLA Tough White 202301"
                with self.assertRaises(ValueError):
                    verify_spec_values(facts, spec)

    def test_frozen_packet_counts_sources_and_unknowns_remain_separate(self):
        packet = document("prepared-packet.json")
        graph = packet["catalogs"]
        self.assertEqual([len(graph["materials"][key]) for key in ("identities", "grades", "records")], [1, 0, 2])
        self.assertEqual(len(graph["properties"]["records"]), 4)
        self.assertEqual({row["id"] for row in graph["materials"]["identities"]}, {IDENTITY})
        self.assertEqual(graph["materials"]["identities"][0]["category"], "polymer")
        self.assertEqual({row["identity_id"] for row in graph["materials"]["records"]}, {IDENTITY})
        self.assertEqual({row["source_designation"] for row in graph["materials"]["records"]}, {row[3] for row in ROWS})
        delta = packet["report"]["delta"]
        self.assertEqual([delta[key] for key in ("identities", "grades", "states", "properties", "sources")], [1, 0, 2, 4, 1])
        self.assertTrue(packet["report"]["handoff_ready"])
        sources = {row["id"]: row for row in graph["sources"]["records"]}
        self.assertEqual(set(sources), {DATASET_SOURCE_ID, SOURCE})
        old_sources = json.loads((PRIOR / "prepared-packet.json").read_bytes())["catalogs"]["sources"]["records"]
        self.assertEqual(sources[DATASET_SOURCE_ID], next(row for row in old_sources if row["id"] == DATASET_SOURCE_ID))
        self.assertEqual(record_sha256(sources[SOURCE]), TOUGH_PLA_CLASSIFICATION_SOURCE["sha256"])
        self.assertTrue(_source_rights_available(sources[SOURCE], {}, graph))
        self.assertEqual(set(CLASSIFICATION_ONLY_SOURCES), {
            "protopasta_conductive_pla_faq", "addnorth_product_catalogue_2022", "makerbot_method_materials_20191119"})
        for prop in graph["properties"]["records"]:
            self.assertEqual(prop["source_id"], DATASET_SOURCE_ID)
            self.assertEqual((prop["reporting_basis"], prop["summary_statistic"]), ("reported_summary", "reported_mean"))
            self.assertIsNone(prop["uncertainty"])
            self.assertIsNone(prop["sample_count"]["value"])
            self.assertIsNone(prop["conditions"]["test_standard"]["text"])
            self.assertEqual(prop["conditions"]["loading_rate"]["text"], "10 mm/min")
        crosswalk = packet["input"]["identity_crosswalk"]
        self.assertEqual(len(crosswalk), 1)
        self.assertEqual(set(crosswalk[0]["source_designations"]), {row[3] for row in ROWS})
        review = packet["input"]["review"]["identity_review"]["decisions"]
        self.assertEqual(review["nylon_transparent_1647"]["disposition"], "defer_new_identity")

    def test_sds_gate_rejects_rewrites_other_identities_and_promotions(self):
        original = document("prepared-packet.json")["catalogs"]
        for variant in ("notice", "license", "source id", "category", "extra identity", "nylon", "cpe", "support tag",
                        "numerical property", "source document", "state condition", "grade"):
            with self.subTest(variant=variant):
                graph = deepcopy(original)
                source = next(row for row in graph["sources"]["records"] if row["id"] == SOURCE)
                identity = graph["materials"]["identities"][0]
                evidence = next(row for row in identity["evidence"] if row["source_id"] == SOURCE)
                if variant == "notice":
                    source["claim_notes"].append("An input rehash cannot expand this source's permission.")
                    self.assertNotEqual(record_sha256(source), TOUGH_PLA_CLASSIFICATION_SOURCE["sha256"])
                elif variant == "license":
                    source["license"] = {"status": "explicit_reuse_license_verified", "identifier": "CC-BY-4.0"}
                elif variant == "source id":
                    source["id"] += "_other_revision"
                elif variant == "category":
                    identity["category"] = "composite"
                elif variant == "extra identity":
                    extra = deepcopy(identity)
                    extra["id"] += "_black"
                    graph["materials"]["identities"].append(extra)
                elif variant in ("nylon", "cpe"):
                    identity["id"] = "mat_aniskevich_2023_ultimaker_" + variant
                elif variant == "support tag":
                    evidence["supports"] = ["material_identity", "classification"]
                elif variant == "numerical property":
                    graph["properties"]["records"][0]["source_id"] = SOURCE
                elif variant == "source document":
                    graph["properties"]["records"][0]["source_document"]["url"] = source["urls"][0]
                elif variant == "state condition":
                    graph["materials"]["records"][0]["state"]["conditioning"] = {
                        "status": "reported", "text": "Manufacturer condition", "notes": None,
                        "evidence": [{**evidence, "supports": ["state"]}]}
                else:
                    graph["materials"]["grades"].append({"id": "grade_test_tough_sds_promotion",
                        "identity_id": IDENTITY, "evidence": [{**evidence, "supports": ["grade"]}]})
                self.assertFalse(_source_rights_available(source, {}, graph))


if __name__ == "__main__":
    unittest.main()
