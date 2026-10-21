#!/usr/bin/env python3
"""Replay a reviewed selection of Zenodo 8089569 filament cells, offline.

This checkout-only adapter emits sparse source facts for the existing formulation
packet workflow. It does not infer identities, grades, statistics or admission.
The original workbook remains external to the checkout and package.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal
from hashlib import md5, sha256
from io import BytesIO
from pathlib import Path
import posixpath
import re
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.integrate_material_candidates import read_document, require, write_immutable_package
from scripts.prepare_formulation_packet import _expand

WORKBOOK_NAME = "Annex 3.1. Characterisation of mechanical properties.xlsx"
WORKBOOK_BYTES = 1391320
WORKBOOK_MD5 = "c4842898d2c389ccd7a902691d8a4fa3"
WORKBOOK_SHA256 = "830b2c9277dcc2d03265b63e311a5e7089c258ebb6a389b45d07601ae4b2e4e7"
DATASET_SOURCE_ID = "aniskevich_bulderberga_2023_polymer_mechanical_characterisation"
WORKBOOK_URL = "https://zenodo.org/api/records/8089569/files/Annex%203.1.%20Characterisation%20of%20mechanical%20properties.xlsx/content"
SHEETS = ("Tested materials", "Tensile modulus", "Samples")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
HEADERS = {
    "E2": "Reference filament 2.8 mm", "E3": "E-mod", "F3": "avedev",
    "G3": "Tensile strength", "H3": "avedev",
    **{column + "4": "MPa " for column in "EFGH"},
    "E5": "data from 10 mm/min tests", "G5": "data from 10 mm/min tests",
}
SERIES_STATEMENT = (
    "Testing: Three to five specimens were tested for each series, and average data were used. "
)
SELECTION_KEYS = {"identity_id", "tested_row", "tested_designation", "measurement_row", "measurement_designation"}
STATE_SELECTION_KEYS = (SELECTION_KEYS - {"identity_id"}) | {"material_state_id"}


@dataclass(frozen=True)
class Cell:
    value: str | None
    kind: str = "n"
    formula: bool = False


def read_xlsx_cells(raw, sheet_names=SHEETS):
    """Read stored cell lexemes, never calculate formulas or apply display rounding."""
    with ZipFile(BytesIO(raw)) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ["".join(item.itertext()) for item in
                      ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", NS)]
        relationships = {row.attrib["Id"]: row for row in
                         ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        sheets = ET.fromstring(archive.read("xl/workbook.xml")).findall("m:sheets/m:sheet", NS)
        result = {}
        for sheet in sheets:
            name = sheet.attrib["name"]
            if name not in sheet_names:
                continue
            require(name not in result, "duplicate worksheet name: " + name)
            relation = relationships[sheet.attrib["{" + REL + "}id"]]
            require(relation.attrib.get("TargetMode") != "External", "external worksheet is unsupported")
            target = relation.attrib["Target"]
            member = posixpath.normpath(target.lstrip("/") if target.startswith("/")
                                       else posixpath.join("xl", target))
            require(member.startswith("xl/") and "\\" not in member, "invalid worksheet member")
            cells = {}
            for node in ET.fromstring(archive.read(member)).findall("m:sheetData/m:row/m:c", NS):
                address = node.attrib["r"]
                require(address not in cells, "duplicate cell: " + name + "!" + address)
                kind = node.attrib.get("t", "n")
                value = node.findtext("m:v", default=None, namespaces=NS)
                if kind == "s" and value is not None:
                    value = shared[int(value)]
                elif kind == "inlineStr":
                    inline = node.find("m:is", NS)
                    value = "".join(inline.itertext()) if inline is not None else None
                cells[address] = Cell(value, kind, node.find("m:f", NS) is not None)
            result[name] = cells
        require(set(result) == set(sheet_names), "required worksheet is missing")
        return result


def _text(cells, address):
    cell = cells.get(address)
    require(cell is not None and not cell.formula and cell.kind in {"s", "inlineStr", "str"}
            and isinstance(cell.value, str) and bool(cell.value.strip()), "missing literal text at " + address)
    return cell.value


def _number(cells, address):
    cell = cells.get(address)
    require(cell is not None and not cell.formula and cell.kind == "n"
            and isinstance(cell.value, str)
            and re.fullmatch(r"(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?:[Ee][+-]?[0-9]{1,2})?", cell.value) is not None,
            "missing or unsupported literal numeric cell: " + address)
    require(Decimal(cell.value) > 0, "zero or negative selected value requires separate review: " + address)
    return cell.value


def _selection_rows(selection):
    """Keep legacy identities unique; grouped selections name each state explicitly."""
    require(isinstance(selection, list) and selection, "explicit nonempty workbook selection is required")
    if all(isinstance(choice, dict) and set(choice) == SELECTION_KEYS for choice in selection):
        return selection, False
    require(all(isinstance(group, dict) and set(group) == {"identity_id", "states"} for group in selection),
            "unexpected selection fields")
    identities, rows = set(), []
    for group in selection:
        identity_id = group["identity_id"]
        require(isinstance(identity_id, str) and re.fullmatch(r"mat_[a-z0-9_]+", identity_id),
                "selection must name an explicitly reviewed identity")
        require(identity_id not in identities, "duplicate identity selection group")
        identities.add(identity_id)
        require(isinstance(group["states"], list) and group["states"], "selection group requires explicit states")
        for state in group["states"]:
            require(isinstance(state, dict) and set(state) == STATE_SELECTION_KEYS, "unexpected state selection fields")
            require(isinstance(state["material_state_id"], str)
                    and re.fullmatch(r"state_[a-z0-9_]+", state["material_state_id"]),
                    "selection must name an explicitly reviewed state")
            rows.append({"identity_id": identity_id, **state})
    return rows, True


def extract_filament_facts(sheets, selection):
    """Apply explicit reviewed row pairs; no fuzzy joins or state-to-identity inference."""
    choices, grouped = _selection_rows(selection)
    materials, measured, samples = (sheets[name] for name in SHEETS)
    for address, expected in HEADERS.items():
        require(_text(measured, address) == expected, "filament header changed: " + address)
    require(_text(samples, "C27") == SERIES_STATEMENT, "series-average statement changed")
    unique_keys = STATE_SELECTION_KEYS if grouped else SELECTION_KEYS
    seen = {key: set() for key in unique_keys}
    selected = []
    for choice in choices:
        require(isinstance(choice["identity_id"], str) and re.fullmatch(r"mat_[a-z0-9_]+", choice["identity_id"]),
                "selection must name an explicitly reviewed identity")
        for key in unique_keys:
            value = choice[key]
            require(isinstance(value, (str, int)) and not isinstance(value, bool), "invalid selection key: " + key)
            require(value not in seen[key], "duplicate identity or source/state selection: " + key)
            seen[key].add(value)
        source_row, row = choice["tested_row"], choice["measurement_row"]
        require(type(source_row) is int and 10 <= source_row <= 28
                and type(row) is int and 6 <= row <= 24, "selection is outside reviewed source rows")
        require(_text(materials, "C" + str(source_row)) == choice["tested_designation"],
                "exact Tested materials designation mismatch")
        require(_text(measured, "B" + str(row)) == choice["measurement_designation"],
                "exact Tensile modulus designation mismatch")
        facts = []
        for column, deviation, quantity in (("E", "F", "tensile_modulus"), ("G", "H", "tensile_strength")):
            facts.append({"quantity": quantity, "source_label": HEADERS[column + "3"],
                          "value_text": _number(measured, column + str(row)),
                          "number": format(Decimal(_number(measured, column + str(row))), "f"),
                          "unit_text": HEADERS[column + "4"], "unit_code": "MPa",
                          "locator": "Tensile modulus!" + column + str(row),
                          "reported_companion": {"source_label": "avedev",
                              "value_text": _number(measured, deviation + str(row)),
                              "unit_text": HEADERS[deviation + "4"], "unit_code": "MPa",
                              "locator": "Tensile modulus!" + deviation + str(row),
                              "statistical_type": None}})
        selected.append({**choice, "supplier": _text(materials, "D" + str(source_row)),
                         "identity_locator": "Tested materials!B" + str(source_row) + ":D" + str(source_row),
                         "state": "reference_filament_2_8_mm", "measurements": facts})
    selected.sort(key=lambda row: row["measurement_row"])
    return {"schema": "curated-filament-cells/2" if grouped else "curated-filament-cells/1", "workbook": WORKBOOK_NAME,
            "extraction_policy": {
                "selection": "Explicit reviewed row pairs with both exact source labels; no fuzzy joins.",
                "measurements": "Only literal positive E/F/G/H cells; no formula evaluation or display rounding.",
                "reference_column": "Column C and its ISO 527-2 reference are excluded from measured properties and methods.",
                "state_boundary": "Only reference filament; extruded fibers, dogbones, angles and layers do not add identities.",
                "statistics": "Source avedev remains undefined; it is not SD, SEM, confidence interval or printed plus/minus.",
                "missingness": "Blank, missing, zero and formula-backed selected cells require separate review; no zero stiffness inference.",
            }, "protocol": {"product_form": HEADERS["E2"], "loading_rate_statement": HEADERS["E5"],
                            "series_statement": SERIES_STATEMENT, "exact_sample_count": None,
                            "measured_test_standard": None}, "selected": selected}


def verify_spec_values(facts, specification):
    """Bind selected original cells to authored values, units, sources and locators."""
    formulations = specification.get("formulations", [])
    grouped = facts["schema"] == "curated-filament-cells/2"
    by_identity = {}
    for choice in facts["selected"]:
        by_identity.setdefault(choice["identity_id"], []).append(choice)
    require(len(formulations) == len(by_identity), "workbook selection must cover exactly the authored formulations")
    authored_identities = set()
    for row in formulations:
        identity_id = row["identity"]["fields"]["id"]
        require(identity_id in by_identity and identity_id not in authored_identities,
                "unknown or duplicate authored identity")
        authored_identities.add(identity_id)
        choices = by_identity[identity_id]
        if grouped:
            selected_states = {choice["material_state_id"]: choice for choice in choices}
            authored_states = [_expand(item["record"], "state", specification["contexts"])["id"]
                               for item in row["states"]]
            require(len(set(authored_states)) == len(authored_states)
                    and set(authored_states) == set(selected_states),
                    "selection must cover exactly the authored states of its identity")
        else:
            require(len(choices) == len(row["states"]) == 1,
                    "each selected identity must have exactly one authored filament state")
        for item in row["states"]:
            state = _expand(item["record"], "state", specification["contexts"])
            selected = selected_states[state["id"]] if grouped else choices[0]
            properties = [_expand(prop, "property", specification["contexts"]) for prop in item["properties"]]
            if grouped:
                property_ids = [prop["id"] for prop in properties]
                require(len(set(property_ids)) == len(property_ids)
                        and set(state["property_ids"]) == set(property_ids)
                        and all(prop["material_state_id"] == state["id"] for prop in properties),
                        "authored property ownership differs from selected state")
            _verify_state_values(selected, state, properties, identity_id)


def _verify_state_values(selected, state, properties, identity_id):
    require(state["identity_id"] == identity_id
            and state["source_designation"] == selected["tested_designation"],
            "authored state does not match the reviewed source identity join")
    require(len(properties) == 2 and {prop["quantity"] for prop in properties}
            == {"tensile_modulus", "tensile_strength"}, "exactly two measured filament properties are required")
    for measured in selected["measurements"]:
        prop = next(prop for prop in properties if prop["quantity"] == measured["quantity"])
        expected = {"kind": "scalar", **{key: measured[key] for key in ("value_text", "number", "unit_text", "unit_code")}}
        require(prop["reported_value"] == expected and prop["source_property_label"] == measured["source_label"],
                "authored property differs from selected measured cell: " + measured["locator"])
        require(prop["source_id"] == DATASET_SOURCE_ID and prop["source_document"]["url"] == WORKBOOK_URL
                and prop["source_document"]["sha256"] == WORKBOOK_SHA256, "measured property source differs from pinned workbook")
        locators = {part.strip() for entry in prop["evidence"]
                    if entry["source_id"] == DATASET_SOURCE_ID and entry["url"] == WORKBOOK_URL
                    for part in entry["locator"].split(";")}
        companion = measured["reported_companion"]
        require(measured["locator"] in locators and companion["locator"] in locators
                and not any(re.search(r"Tensile modulus!C[0-9]", locator) for locator in locators),
                "authored measured-property locator differs from E/F/G/H selection")
        require(prop["uncertainty"] is None and prop["uncertainty_status"] == "not_reported_in_inspected_source"
                and ("avedev = " + companion["value_text"] + " MPa at " + companion["locator"]) in prop["uncertainty_note"],
                "authored avedev note differs from source or invents a statistical type")


def build_selection(workbook, spec):
    workbook = Path(workbook).resolve()
    require(not workbook.is_relative_to(ROOT), "original workbook must remain outside the checkout")
    raw = workbook.read_bytes()
    require(len(raw) == WORKBOOK_BYTES and md5(raw).hexdigest() == WORKBOOK_MD5
            and sha256(raw).hexdigest() == WORKBOOK_SHA256, "workbook fingerprint mismatch")
    specification, _ = read_document(spec)
    selection = specification.get("review", {}).get("workbook_selection")
    facts = extract_filament_facts(read_xlsx_cells(raw), selection)
    verify_spec_values(facts, specification)
    facts["source_document"] = {"bytes": len(raw), "md5": WORKBOOK_MD5, "sha256": WORKBOOK_SHA256}
    return facts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new sparse fact artifact outside the checkout")
    args = parser.parse_args(argv)
    try:
        require(not args.output.resolve().is_relative_to(ROOT), "sparse source extraction must remain outside the checkout")
        require(args.output.resolve() not in {args.workbook.resolve(), args.spec.resolve()}, "output must differ from inputs")
        facts = build_selection(args.workbook, args.spec)
        created = write_immutable_package(args.output, facts)
    except (OSError, ValueError, TypeError, KeyError, IndexError, ET.ParseError) as exc:
        parser.exit(2, "curated filament extraction failed: " + str(exc) + "\n")
    print(("Created" if created else "Unchanged") + " sparse filament facts: " + str(args.output))
    print("No identity classification, source approval, packet preparation or runtime admission is performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
