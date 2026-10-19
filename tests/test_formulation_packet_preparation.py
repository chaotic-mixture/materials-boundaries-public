"""Offline formulation compilation: exact replay, explicit facts and closed gates.

The frozen source packets are a transcription oracle, not new scientific review.
Synthetic variants below exercise software ownership/counting rules only.
"""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import unittest

from evidence_batch_data_preservation import recover_pre_evidence_batch_catalogs
from scripts.prepare_formulation_packet import (
    build_packet, main, record_sha256, validate_prepared_packet, write_packet,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/formulation_packet_replay_20261019.json"
FILES = {"materials": "materials.json", "properties": "reference_properties.json", "sources": "sources.json"}
PIN_KEYS = {"materials": "materials", "properties": "reference_properties", "sources": "sources"}
PACKET_FILES = {"materials": "materials.append.json", "properties": "reference-properties.append.json",
                "sources": "sources.reused.json", "review": "review.json"}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def canonical_digest(value):
    return sha256((json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                              allow_nan=False) + "\n").encode("utf-8")).hexdigest()


def explicit_reference(record, shared, context):
    """Factor only fixture-selected fields; never manufacture a missing field."""
    fields = deepcopy(record)
    for key, value in shared.items():
        if isinstance(value, dict):
            for nested, expected in value.items():
                if fields[key].pop(nested) != expected:
                    raise AssertionError("fixture context is not shared: " + key + "." + nested)
            if not fields[key]:
                del fields[key]
        elif fields.pop(key) != value:
            raise AssertionError("fixture context is not shared: " + key)
    return {"context": context, "fields": fields}


def fixture_inputs():
    fixture = json.loads(FIXTURE.read_bytes())
    packets = []
    expected = {"materials": {"schema_version": "1.0.0", "identities": [], "grades": [], "records": []},
                "properties": {"schema_version": "1.0.0", "records": []},
                "sources": {"schema_version": "1.0.0", "records": []}}
    for descriptor in fixture["packets"]:
        packet = {}
        for table, filename in PACKET_FILES.items():
            raw = (ROOT / descriptor["directory"] / filename).read_bytes()
            if sha256(raw).hexdigest() != descriptor["sha256"][filename]:
                raise AssertionError("frozen replay packet changed: " + filename)
            packet[table] = json.loads(raw)
        if [row["id"] for row in packet["materials"]["identities"]] != descriptor["identity_ids"]:
            raise AssertionError("frozen identity selection changed")
        if [row["source_designation"] for row in packet["materials"]["records"]] != descriptor["source_designations"]:
            raise AssertionError("frozen source designations changed")
        for table in FILES:
            for field in expected[table]:
                if isinstance(expected[table][field], list):
                    expected[table][field].extend(deepcopy(packet[table][field]))
        packets.append(packet)
    return fixture, packets, expected


def replay_spec(fixture, packets):
    spec = {"schema": "formulation-packet-spec/1", "batch_id": "four_existing_formulations_replay",
            "baseline_sha256": deepcopy(fixture["baseline_sha256"]), "source_records": [],
            "contexts": {"identity": {}, "grade": {}, "state": {}, "property": {}},
            "formulations": [], "identity_crosswalk": [],
            "review": {"verification": {"independent_scientific_review": False, "raw_data_reanalysis": False},
                       "formal_admitted_delta": 0, "source_reviews": [],
                       "scope": "Frozen packet replay only; no fresh inspection or approval.",
                       "original_packet_reviews": [deepcopy(packet["review"]) for packet in packets]}}
    selected = fixture["context_fields"]
    for index, packet in enumerate(packets):
        context = "source_" + str(index)
        materials, properties = packet["materials"], packet["properties"]
        shared = {
            "identity": {key: deepcopy(materials["identities"][0][key]) for key in selected["identity"]},
            "state": {key: deepcopy(materials["records"][0][key]) for key in selected["state"]},
            "property": {key: deepcopy(properties["records"][0][key]) for key in selected["property"]},
        }
        shared["state"]["state"] = {key: deepcopy(materials["records"][0]["state"][key])
                                     for key in selected["state_facts"]}
        for kind in shared:
            spec["contexts"][kind][context] = deepcopy(shared[kind])
        source = packet["sources"]["records"][0]
        spec["source_records"].append({"record": deepcopy(source),
                                       "sha256": fixture["packets"][index]["source_record_sha256"]})
        spec["review"]["source_reviews"].append({"source_id": source["id"], "status": "selected_facts_checked",
                                                 "note": "Retain the frozen packet inspection and its limits."})
        for identity in materials["identities"]:
            states = [state for state in materials["records"] if state["identity_id"] == identity["id"]]
            row = {"identity": explicit_reference(identity, shared["identity"], context), "grades": [], "states": []}
            for state in states:
                props = [prop for prop in properties["records"] if prop["material_state_id"] == state["id"]]
                row["states"].append({"record": explicit_reference(state, shared["state"], context),
                                      "properties": [explicit_reference(prop, shared["property"], context)
                                                     for prop in props]})
            spec["formulations"].append(row)
            spec["identity_crosswalk"].append({"identity_id": identity["id"], "source_id": source["id"],
                "source_designations": [state["source_designation"] for state in states], "disposition": "existing",
                "evidence": deepcopy(identity["evidence"]),
                "note": "Explicit replay of the existing source-qualified identity; zero new material claims."})
    return spec


class FormulationPacketPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture, cls.packets, cls.expected = fixture_inputs()
        cls.original_spec = replay_spec(cls.fixture, cls.packets)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.baseline = self.root / "baseline"
        self.baseline.mkdir()
        self.spec = deepcopy(self.original_spec)
        self.write_baseline(self.expected)
        self.spec_path = self.root / "spec.json"
        self.output = self.root / "prepared.json"

    def write_baseline(self, graph):
        for table, filename in FILES.items():
            raw = encoded(graph[table])
            (self.baseline / filename).write_bytes(raw)
            self.spec["baseline_sha256"][PIN_KEYS[table]] = sha256(raw).hexdigest()

    def save_spec(self):
        self.spec_path.write_bytes(encoded(self.spec))

    def compile(self):
        self.save_spec()
        return build_packet(self.baseline, self.spec_path)

    def assert_refused(self, mutate, message=None):
        saved = deepcopy(self.spec)
        mutate(self.spec)
        self.save_spec()
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        assertion = self.assertRaises(ValueError) if message is None else self.assertRaisesRegex(ValueError, message)
        with assertion:
            write_packet(self.baseline, self.spec_path, self.output, repository_root=self.root)
        self.assertFalse(self.output.exists())
        self.assertEqual({path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}, before)
        self.spec = saved

    def test_frozen_four_formulation_replay_preserves_all_facts_and_zero_increment(self):
        self.spec = deepcopy(self.original_spec)
        current = {table: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes())
                   for table, filename in FILES.items()}
        frozen = recover_pre_evidence_batch_catalogs(current)
        self.write_baseline(frozen)
        for table, filename in FILES.items():
            self.assertEqual(sha256((self.baseline / filename).read_bytes()).hexdigest(),
                             self.fixture["baseline_sha256"][PIN_KEYS[table]])
        self.save_spec()
        packet = build_packet(self.baseline, self.spec_path)
        self.assertEqual(packet["schema"], "formulation-prepared-packet/1")
        self.assertEqual(packet["catalogs"], self.expected)
        self.assertEqual(packet["input"], self.spec)
        self.assertEqual(packet["review"], self.spec["review"])
        self.assertEqual(packet["spec_sha256"], canonical_digest(self.spec))
        for descriptor in self.spec["source_records"]:
            self.assertEqual(record_sha256(descriptor["record"]), descriptor["sha256"])
        report = packet["report"]
        self.assertTrue(report["handoff_ready"])
        self.assertEqual(report["before"], report["after"])
        self.assertEqual(report["after"]["categories"], self.fixture["expected_categories"])
        source_qualified = sum(report["after"]["categories"].values())
        self.assertEqual(source_qualified, self.fixture["expected_source_qualified_count"])
        self.assertEqual(source_qualified + self.fixture["reviewed_computed_count"], 1107)
        self.assertEqual(report["formal_admitted_delta"], 0)
        self.assertTrue(all(value == 0 for key, value in report["delta"].items() if key != "categories"))
        self.assertTrue(all(value == 0 for value in report["delta"]["categories"].values()))
        self.assertEqual([item["disposition"] for item in report["identity_crosswalk"]], ["existing"] * 4)
        self.assertEqual(packet["catalogs"]["materials"]["grades"], [])
        self.assertTrue(all(row["grade_id"] is None for row in packet["catalogs"]["materials"]["records"]))
        props = packet["catalogs"]["properties"]["records"]
        self.assertEqual(props[0]["summary_statistic"], "reported_mean")
        self.assertEqual(props[0]["uncertainty"]["type"], "reported_standard_deviation")
        for prop in props[1:]:
            self.assertEqual(prop["summary_statistic"], "reported_value")
            self.assertEqual(prop["uncertainty"]["type"], "reported_plus_minus_unspecified")
            self.assertIsNone(prop["source_document"]["sha256"])
        for prop in props:
            self.assertEqual(prop["conditions"]["temperature"]["status"], "not_reported_in_inspected_source")
            self.assertIsNone(prop["conditions"]["temperature"]["text"])
            self.assertFalse(prop["verification"]["independent_scientific_review"])
            self.assertFalse(prop["verification"]["raw_data_reanalysis"])

    def test_repeated_write_and_cli_keep_identical_bytes_and_mtime(self):
        self.save_spec()
        packet, created = write_packet(self.baseline, self.spec_path, self.output, repository_root=self.root)
        self.assertTrue(created)
        before = (self.output.read_bytes(), self.output.stat().st_mtime_ns)
        repeated, created = write_packet(self.baseline, self.spec_path, self.output, repository_root=self.root)
        self.assertFalse(created)
        self.assertEqual(repeated, packet)
        with redirect_stdout(io.StringIO()) as output:
            result = main(["--baseline-dir", str(self.baseline), "--spec", str(self.spec_path), "--output", str(self.output)])
        self.assertEqual(result, 0)
        self.assertIn("Unchanged", output.getvalue())
        self.assertEqual((self.output.read_bytes(), self.output.stat().st_mtime_ns), before)

    def test_shared_contexts_and_explicit_grade_multiple_states_do_not_multiply_identity(self):
        first = self.spec["formulations"][0]
        original = first["states"][0]
        extra = deepcopy(original)
        state = extra["record"]["fields"]
        prop = extra["properties"][0]["fields"]
        state["id"] += "_test_condition"
        prop["id"] += "_test_condition"
        prop["material_state_id"] = state["id"]
        state["property_ids"] = [prop["id"]]
        state["source_scope"] += " Synthetic software test condition, not a new source claim."
        grade_id = "grade_test_explicit_source_label"
        identity_id = first["identity"]["fields"]["id"]
        evidence = deepcopy(first["identity"]["fields"]["evidence"])
        for item in evidence:
            item["supports"] = ["grade"]
        grade = {"id": grade_id, "version": "1.0.0", "identity_id": identity_id,
                 "designation": "TEST_ONLY_EXPLICIT_LABEL", "authority": {"kind": "source_designation", "name": "Synthetic test"},
                 "manufacturer": {"status": "not_verified", "text": None, "evidence": [], "notes": "Test fixture only."},
                 "aliases": [], "evidence": evidence}
        self.spec["contexts"]["grade"]["explicit_grade"] = {"version": grade.pop("version")}
        first["grades"] = [{"context": "explicit_grade", "fields": grade}]
        state["grade_id"] = grade_id
        first["states"].append(extra)
        packet = self.compile()
        self.assertEqual(packet["report"]["delta"]["identities"], 0)
        self.assertEqual(packet["report"]["delta"]["grades"], 1)
        self.assertEqual(packet["report"]["delta"]["states"], 1)
        self.assertEqual(packet["report"]["delta"]["properties"], 1)
        self.assertEqual(packet["report"]["delta"]["categories"]["composite"], 0)
        self.assertEqual(len(packet["catalogs"]["materials"]["identities"]), 4)
        self.assertEqual(packet["catalogs"]["materials"]["records"][0]["grade_id"], None)
        self.assertEqual(packet["catalogs"]["materials"]["records"][1]["grade_id"], grade_id)

    def test_missing_crosswalk_review_and_license_remain_pending_without_upgrade(self):
        original = deepcopy(self.spec)
        for kind in ("crosswalk", "source_review"):
            self.spec = deepcopy(original)
            if kind == "crosswalk":
                self.spec["identity_crosswalk"] = []
            else:
                self.spec["review"]["source_reviews"][0]["status"] = "pending"
            with self.subTest(gate=kind):
                packet = self.compile()
                self.assertFalse(packet["report"]["handoff_ready"])
                self.assertTrue(packet["report"]["pending_gates"])
                self.assertEqual(packet["review"], self.spec["review"])
                self.assertEqual(packet["report"]["formal_admitted_delta"], 0)
        self.spec = deepcopy(original)
        baseline = deepcopy(self.expected)
        baseline["sources"]["records"][0]["license"] = {"status": "not_verified", "identifier": None}
        self.write_baseline(baseline)
        source = baseline["sources"]["records"][0]
        self.spec["source_records"][0] = {"record": deepcopy(source), "sha256": canonical_digest(source)}
        packet = self.compile()
        self.assertFalse(packet["report"]["handoff_ready"])
        self.assertTrue(packet["report"]["pending_gates"])
        self.assertEqual(packet["catalogs"]["sources"]["records"][0]["license"], source["license"])
        self.assertFalse(packet["review"]["verification"]["independent_scientific_review"])
        self.spec = deepcopy(original)
        self.write_baseline(self.expected)
        for field in ("independent_scientific_review", "raw_data_reanalysis"):
            with self.subTest(upgrade=field):
                self.assert_refused(lambda spec: spec["review"]["verification"].__setitem__(field, True))
        self.assert_refused(lambda spec: spec["review"].__setitem__("formal_admitted_delta", 4))

    def test_source_and_baseline_pins_reject_changed_inputs_before_writing(self):
        self.assert_refused(lambda spec: spec["baseline_sha256"].__setitem__("materials", "0" * 64), "hash")
        self.assert_refused(lambda spec: spec["source_records"][0].__setitem__("sha256", "0" * 64), "hash")

        def altered_source(spec):
            source = spec["source_records"][0]
            source["record"]["title"] += " silently changed"
            source["sha256"] = canonical_digest(source["record"])
        self.assert_refused(altered_source)

    def test_reidentified_designation_or_alias_cannot_evade_existing_identity(self):
        def reidentify(spec, alias):
            row = spec["formulations"][0]
            identity = row["identity"]["fields"]
            old_name = identity["name"]
            identity["id"] = "mat_test_reidentified_b45"
            identity["name"] = "Renamed display label"
            identity["names"] = {language: "Renamed display label" for language in identity["names"]}
            identity["identity_scope"] += " Reworded label must not evade source identity."
            state = row["states"][0]["record"]["fields"]
            prop = row["states"][0]["properties"][0]["fields"]
            state["id"] = "state_test_reidentified_b45"
            state["identity_id"] = identity["id"]
            state["name"] = "Renamed state label"
            state["names"] = {language: "Renamed state label" for language in state["names"]}
            state["aliases"] = []
            prop["id"] = "refprop_test_reidentified_b45"
            prop["material_state_id"] = state["id"]
            state["property_ids"] = [prop["id"]]
            crosswalk = spec["identity_crosswalk"][0]
            crosswalk["identity_id"] = identity["id"]
            crosswalk["disposition"] = "distinct"
            if alias:
                identity["aliases"] = [{"language": "en", "text": " " + old_name.upper() + " "}]
                state["source_designation"] = "TEST_RENAMED_CODE"
            else:
                state["source_designation"] = " b45 "
            crosswalk["source_designations"] = [state["source_designation"]]
        for alias in (False, True):
            with self.subTest(using_alias=alias):
                self.assert_refused(lambda spec: reidentify(spec, alias))

    def test_context_collisions_and_wrong_row_ownership_fail_atomically(self):
        cases = {
            "equal_leaf_collision": lambda spec: spec["formulations"][0]["identity"]["fields"].__setitem__("version", "1.0.0"),
            "nested_leaf_collision": lambda spec: spec["formulations"][0]["states"][0]["record"]["fields"]["state"].__setitem__(
                "conditioning", deepcopy(spec["contexts"]["state"]["source_0"]["state"]["conditioning"])),
            "unknown_context": lambda spec: spec["formulations"][0]["identity"].__setitem__("context", "missing"),
            "identity_owner": lambda spec: spec["formulations"][0]["states"][0]["record"]["fields"].__setitem__(
                "identity_id", "mat_bianchi2022_epdm_h_p20"),
            "property_owner": lambda spec: spec["formulations"][0]["states"][0]["properties"][0]["fields"].__setitem__(
                "material_state_id", "state_bianchi2022_epdm_h_p20"),
            "duplicate_formulation": lambda spec: spec["formulations"].append(deepcopy(spec["formulations"][0])),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                self.assert_refused(mutate)

    def test_missing_properties_wrong_units_and_untraceable_provenance_are_rejected(self):
        def wrong_unit(spec):
            value = spec["formulations"][0]["states"][0]["properties"][0]["fields"]["reported_value"]
            value["unit_code"] = value["unit_text"] = "kg/m^3"

        def missing_locator(spec):
            spec["formulations"][0]["states"][0]["properties"][0]["fields"]["evidence"][0]["locator"] = ""

        def wrong_source(spec):
            spec["formulations"][0]["states"][0]["properties"][0]["fields"]["source_id"] = "bianchi_2022_epdm_pcm"

        for name, mutate in {
            "no_property": lambda spec: spec["formulations"][0]["states"][0].__setitem__("properties", []),
            "wrong_unit": wrong_unit, "missing_locator": missing_locator, "cross_source": wrong_source,
            "unsupported_crosswalk": lambda spec: spec["identity_crosswalk"][0]["evidence"][0].__setitem__("supports", ["state"]),
        }.items():
            with self.subTest(case=name):
                self.assert_refused(mutate)

    def test_strict_json_rejects_duplicate_nonfinite_and_overflow_values(self):
        valid = encoded(self.spec).decode("utf-8")
        invalid = [valid.replace('{\n', '{"schema":"duplicate",\n', 1)]
        for token in ("NaN", "Infinity", "1e9999"):
            invalid.append(valid.replace('"formal_admitted_delta": 0', '"formal_admitted_delta": ' + token, 1))
        for index, raw in enumerate(invalid):
            with self.subTest(case=index):
                self.spec_path.write_text(raw, encoding="utf-8")
                with self.assertRaises(ValueError):
                    write_packet(self.baseline, self.spec_path, self.output, repository_root=self.root)
                self.assertFalse(self.output.exists())
        self.assert_refused(lambda spec: spec.__setitem__("unrecognized_extension", {}))

    def test_output_path_and_existing_artifact_refusals_preserve_input_bytes(self):
        self.save_spec()
        paths = [self.spec_path, self.baseline / "new.json",
                 self.root / "materials_boundaries/data/new.json",
                 self.root / "formal-catalog/materials_project_catalog/data/new.json"]
        original = self.spec_path.read_bytes()
        for path in paths:
            with self.subTest(output=path.relative_to(self.root).as_posix()):
                with self.assertRaises(ValueError):
                    write_packet(self.baseline, self.spec_path, path, repository_root=self.root)
                if path != self.spec_path:
                    self.assertFalse(path.exists())
                self.assertEqual(self.spec_path.read_bytes(), original)
        self.output.write_bytes(b"Existing unrelated artifact.\n")
        before = (self.output.read_bytes(), self.output.stat().st_mtime_ns)
        with self.assertRaises(ValueError):
            write_packet(self.baseline, self.spec_path, self.output, repository_root=self.root)
        self.assertEqual((self.output.read_bytes(), self.output.stat().st_mtime_ns), before)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(["--baseline-dir", str(self.baseline), "--spec", str(self.spec_path), "--output", str(self.output)])
        self.assertEqual(error.exception.code, 2)

    def test_prepared_packet_validation_recompiles_input_instead_of_trusting_report(self):
        packet = self.compile()
        frozen = deepcopy(packet)
        validate_prepared_packet(packet, self.baseline)
        self.assertEqual(packet, frozen)
        mutations = {
            "report": lambda value: value["report"]["delta"].__setitem__("identities", 99),
            "catalog": lambda value: value["catalogs"]["properties"]["records"][0]["reported_value"].__setitem__("number", "999"),
            "input": lambda value: value["input"].__setitem__("batch_id", "forged_input"),
            "digest": lambda value: value.__setitem__("spec_sha256", "0" * 64),
            "review": lambda value: value["review"]["verification"].__setitem__("raw_data_reanalysis", True),
            "extra_field": lambda value: value.__setitem__("trusted_external_approval", True),
        }
        for name, mutate in mutations.items():
            value = deepcopy(packet)
            mutate(value)
            with self.subTest(case=name), self.assertRaises(ValueError):
                validate_prepared_packet(value, self.baseline)
        pending = deepcopy(self.spec)
        pending["identity_crosswalk"] = []
        self.spec = pending
        forged = self.compile()
        forged["report"]["handoff_ready"] = True
        forged["report"]["pending_gates"] = []
        with self.assertRaises(ValueError):
            validate_prepared_packet(forged, self.baseline)


if __name__ == "__main__":
    unittest.main()
