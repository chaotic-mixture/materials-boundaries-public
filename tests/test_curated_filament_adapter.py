"""Synthetic workbook cells test curated extraction; no original workbook is bundled."""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from scripts.extract_curated_filament_cells import (
    Cell, DATASET_SOURCE_ID, HEADERS, SERIES_STATEMENT, WORKBOOK_SHA256, WORKBOOK_URL,
    build_selection, extract_filament_facts, read_xlsx_cells, verify_spec_values,
)
from scripts.integrate_material_candidates import write_immutable_package
from scripts.prepare_formulation_packet import CLASSIFICATION_ONLY_SOURCES, _source_rights_available, record_sha256

PACKET = Path(__file__).resolve().parents[1] / "experimental/material-batches/zenodo-8089569-filaments-20261021/prepared-packet.json"


def fixture():
    measured = {address: Cell(value, "s") for address, value in HEADERS.items()}
    materials = {}
    selection = []
    for source_row, row, name in ((22, 6, "Alpha"), (23, 12, "Beta")):
        materials.update({"C" + str(source_row): Cell(name + ", source product", "s"),
                          "D" + str(source_row): Cell("Synthetic supplier", "s")})
        measured["B" + str(row)] = Cell(name, "s")
        for column, value in zip("EFGH", ("2100.1250", "12.50", "62.625", "0.3750")):
            measured[column + str(row)] = Cell(value)
        selection.append({"identity_id": "mat_test_" + name.lower(), "tested_row": source_row,
                          "tested_designation": name + ", source product", "measurement_row": row,
                          "measurement_designation": name})
    return {"Tested materials": materials, "Tensile modulus": measured,
            "Samples": {"C27": Cell(SERIES_STATEMENT, "s")}}, selection


def authored_fixture(facts):
    spec = {"contexts": {"state": {"test": {}}, "property": {"test": {}}}, "formulations": []}
    for row in facts["selected"]:
        properties = []
        for measured in row["measurements"]:
            companion = measured["reported_companion"]
            properties.append({"context": "test", "fields": {
                "quantity": measured["quantity"], "source_property_label": measured["source_label"],
                "reported_value": {"kind": "scalar", **{key: measured[key] for key in ("value_text", "number", "unit_text", "unit_code")}},
                "source_id": DATASET_SOURCE_ID,
                "source_document": {"url": WORKBOOK_URL, "sha256": WORKBOOK_SHA256},
                "evidence": [{"source_id": DATASET_SOURCE_ID, "url": WORKBOOK_URL,
                              "locator": measured["locator"] + "; " + companion["locator"]}],
                "uncertainty": None, "uncertainty_status": "not_reported_in_inspected_source",
                "uncertainty_note": "Source avedev = " + companion["value_text"] + " MPa at " + companion["locator"]}})
        spec["formulations"].append({"identity": {"fields": {"id": row["identity_id"]}}, "states": [{
            "record": {"context": "test", "fields": {"identity_id": row["identity_id"], "source_designation": row["tested_designation"]}},
            "properties": properties}]})
    return spec


class CuratedFilamentAdapterTests(unittest.TestCase):
    def test_frozen_classification_sources_only_support_reviewed_identities(self):
        graph = json.loads(PACKET.read_bytes())["catalogs"]
        sources = {source["id"]: source for source in graph["sources"]["records"]}
        self.assertEqual(set(CLASSIFICATION_ONLY_SOURCES), {
            "protopasta_conductive_pla_faq", "addnorth_product_catalogue_2022", "makerbot_method_materials_20191119"})
        for source_id, approved in CLASSIFICATION_ONLY_SOURCES.items():
            with self.subTest(source=source_id):
                source = sources[source_id]
                self.assertEqual(record_sha256(source), approved["sha256"])
                self.assertEqual(source["license"], {
                    "status": "no_explicit_reuse_license_verified_limited_factual_curation_only", "identifier": None})
                self.assertTrue(_source_rights_available(source, {}, graph))
                users = [identity for identity in graph["materials"]["identities"]
                         if any(entry["source_id"] == source_id for entry in identity["evidence"])]
                self.assertEqual({identity["id"] for identity in users}, approved["identity_ids"])
                self.assertTrue(all(identity["category"] == "composite" for identity in users))
                self.assertTrue(all(prop["source_id"] != source_id for prop in graph["properties"]["records"]))

    def test_frozen_classification_sources_reject_rewrites_and_promotions(self):
        original = json.loads(PACKET.read_bytes())["catalogs"]
        for source_id in CLASSIFICATION_ONLY_SOURCES:
            for variant in ("notice", "new license", "extra identity", "category", "support tag",
                            "numerical property", "source document", "state condition", "grade"):
                with self.subTest(source=source_id, variant=variant):
                    graph = deepcopy(original)
                    source = next(row for row in graph["sources"]["records"] if row["id"] == source_id)
                    identity = next(row for row in graph["materials"]["identities"]
                                    if any(entry["source_id"] == source_id for entry in row["evidence"]))
                    evidence = next(entry for entry in identity["evidence"] if entry["source_id"] == source_id)
                    if variant == "notice":
                        source["claim_notes"].append("Expanded permission claim cannot be accepted by rehashing input.")
                    elif variant == "new license":
                        source["license"] = {"status": "explicit_reuse_license_verified", "identifier": "CC-BY-4.0"}
                    elif variant == "extra identity":
                        extra = deepcopy(identity)
                        extra["id"] += "_extra"
                        graph["materials"]["identities"].append(extra)
                    elif variant == "category":
                        identity["category"] = "polymer"
                    elif variant == "support tag":
                        evidence["supports"] = ["material_identity", "classification"]
                    elif variant == "numerical property":
                        graph["properties"]["records"][0]["source_id"] = source_id
                    elif variant == "source document":
                        graph["properties"]["records"][0]["source_document"]["url"] = source["urls"][0]
                    elif variant == "state condition":
                        state = graph["materials"]["records"][0]
                        state["state"]["conditioning"] = {
                            "status": "reported", "text": "Manufacturer condition", "notes": None,
                            "evidence": [{**evidence, "supports": ["state"]}]}
                    else:
                        graph["materials"]["grades"].append({
                            "id": "grade_test_manufacturer_promotion", "version": "1.0.0",
                            "identity_id": identity["id"], "designation": "Test-only grade",
                            "authority": {"kind": "manufacturer", "name": "Test-only source"},
                            "manufacturer": {"status": "reported", "text": "Test-only source", "notes": None,
                                             "evidence": [{**evidence, "supports": ["grade"]}]},
                            "aliases": [], "evidence": [{**evidence, "supports": ["grade"]}]})
                    self.assertFalse(_source_rights_available(source, {}, graph))

    def test_measured_columns_exclude_iso_reference_and_print_states(self):
        sheets, selection = fixture()
        measured = sheets["Tensile modulus"]
        measured.update({"C6": Cell("999999"), "C5": Cell("(ISO 527-2)", "s"),
                         "I6": Cell("888888"), "Q6": Cell("777777"), "U6": Cell("666666")})
        facts = extract_filament_facts(sheets, selection)
        selected = facts["selected"][0]
        self.assertEqual(selected["state"], "reference_filament_2_8_mm")
        self.assertEqual([row["quantity"] for row in selected["measurements"]],
                         ["tensile_modulus", "tensile_strength"])
        self.assertEqual([row["value_text"] for row in selected["measurements"]], ["2100.1250", "62.625"])
        self.assertEqual([row["locator"] for row in selected["measurements"]],
                         ["Tensile modulus!E6", "Tensile modulus!G6"])
        companion = selected["measurements"][0]["reported_companion"]
        self.assertEqual(companion["value_text"], "12.50")
        self.assertEqual(companion["source_label"], "avedev")
        self.assertIsNone(companion["statistical_type"])
        self.assertIsNone(facts["protocol"]["exact_sample_count"])
        self.assertIsNone(facts["protocol"]["measured_test_standard"])
        measured["C6"] = Cell("1")
        measured["I6"] = Cell("2")
        self.assertEqual(extract_filament_facts(sheets, selection), facts)
        measured["H6"] = Cell("7.6524603101136623E-2")
        self.assertEqual(extract_filament_facts(sheets, selection)["selected"][0]["measurements"][1]
                         ["reported_companion"]["value_text"], "7.6524603101136623E-2")
        measured["E2"] = Cell("Dog-bone specimens", "s")
        with self.assertRaisesRegex(ValueError, "filament header"):
            extract_filament_facts(sheets, selection)
        measured["E2"] = Cell(HEADERS["E2"], "s")
        measured["G4"] = Cell("GPa", "s")
        with self.assertRaisesRegex(ValueError, "filament header"):
            extract_filament_facts(sheets, selection)

    def test_blanks_zero_and_formula_values_fail_closed(self):
        for address in ("E6", "F6", "G6", "H6"):
            for value in (None, Cell(None), Cell(""), Cell("0"), Cell("-1"),
                          Cell("123", "s"), Cell("123", formula=True)):
                with self.subTest(address=address, value=value):
                    sheets, selection = fixture()
                    if value is None:
                        del sheets["Tensile modulus"][address]
                    else:
                        sheets["Tensile modulus"][address] = value
                    with self.assertRaises(ValueError):
                        extract_filament_facts(sheets, selection)

    def test_exact_join_rejects_missing_duplicate_or_state_keys(self):
        sheets, selection = fixture()
        for field, value in (("tested_designation", "Alpha"), ("measurement_designation", "alpha"),
                             ("measurement_row", 7), ("tested_row", 9)):
            with self.subTest(field=field):
                altered = deepcopy(selection)
                altered[0][field] = value
                with self.assertRaises(ValueError):
                    extract_filament_facts(sheets, altered)
        for field in ("identity_id", "tested_row", "tested_designation", "measurement_row", "measurement_designation"):
            with self.subTest(duplicate=field):
                altered = deepcopy(selection)
                altered[1][field] = altered[0][field]
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    extract_filament_facts(sheets, altered)
        altered = deepcopy(selection)
        altered[0]["state"] = "dogbone_0_degrees"
        with self.assertRaisesRegex(ValueError, "selection fields"):
            extract_filament_facts(sheets, altered)

    def test_sparse_replay_is_deterministic_and_immutable(self):
        sheets, selection = fixture()
        facts = extract_filament_facts(sheets, selection)
        self.assertEqual(extract_filament_facts(sheets, list(reversed(selection))), facts)
        spec = authored_fixture(facts)
        verify_spec_values(facts, spec)
        for variant in ("reference value", "reference locator", "avedev", "typed uncertainty", "source"):
            with self.subTest(spec_change=variant):
                altered = deepcopy(spec)
                prop = altered["formulations"][0]["states"][0]["properties"][0]["fields"]
                if variant == "reference value":
                    prop["reported_value"].update(value_text="999999", number="999999")
                elif variant == "reference locator":
                    prop["evidence"][0]["locator"] = "Tensile modulus!C6; Tensile modulus!F6"
                elif variant == "avedev":
                    prop["uncertainty_note"] = "Source avedev = 99 MPa at Tensile modulus!F6"
                elif variant == "typed uncertainty":
                    prop["uncertainty"] = {"type": "reported_standard_deviation"}
                else:
                    prop["source_document"]["sha256"] = "0" * 64
                with self.assertRaises(ValueError):
                    verify_spec_values(facts, altered)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "selected.json"
            self.assertTrue(write_immutable_package(output, facts))
            before = output.read_bytes(), output.stat().st_mtime_ns
            self.assertFalse(write_immutable_package(output, extract_filament_facts(sheets, selection)))
            self.assertEqual((output.read_bytes(), output.stat().st_mtime_ns), before)
            sheets["Tensile modulus"]["G6"] = Cell("63.125")
            with self.assertRaisesRegex(ValueError, "different content"):
                write_immutable_package(output, extract_filament_facts(sheets, selection))
            self.assertEqual((output.read_bytes(), output.stat().st_mtime_ns), before)

    def test_xlsx_reader_keeps_numeric_lexemes_and_resolves_shared_strings(self):
        raw = BytesIO()
        main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        relationships = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        with ZipFile(raw, "w") as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns="' + main + '" xmlns:r="' + relationships +
                             '"><sheets><sheet name="Selected" sheetId="1" r:id="rId1"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rId1" '
                             'Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/sharedStrings.xml", '<sst xmlns="' + main + '"><si><r><t>Exact </t></r>'
                             '<r><t>label</t></r></si></sst>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="' + main + '"><sheetData><row r="1">'
                             '<c r="A1" t="s"><v>0</v></c><c r="B1"><v>2100.1250</v></c>'
                             '<c r="C1" t="inlineStr"><is><t>avedev</t></is></c>'
                             '<c r="D1"><f>B1*2</f><v>4200.2500</v></c>'
                             '</row></sheetData></worksheet>')
        cells = read_xlsx_cells(raw.getvalue(), ("Selected",))["Selected"]
        self.assertEqual(cells["A1"], Cell("Exact label", "s"))
        self.assertEqual(cells["B1"], Cell("2100.1250"))
        self.assertEqual(cells["C1"], Cell("avedev", "inlineStr"))
        self.assertEqual(cells["D1"], Cell("4200.2500", formula=True))
        with self.assertRaisesRegex(ValueError, "worksheet is missing"):
            read_xlsx_cells(raw.getvalue(), ("Missing",))
        with tempfile.TemporaryDirectory() as temporary:
            workbook = Path(temporary) / "wrong.xlsx"
            workbook.write_bytes(raw.getvalue())
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                build_selection(workbook, Path(temporary) / "not-read.json")


if __name__ == "__main__":
    unittest.main()
