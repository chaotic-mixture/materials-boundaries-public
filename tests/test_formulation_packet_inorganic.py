"""Offline NBS packet replay and compiler gates, not new scientific review.

Frozen, already-curated halide rows exercise batch mechanics independently of
the growing runtime catalogs and this round's oxide source transcriptions.
Mutations below are software negative controls, never candidate materials.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_formulation_packet import compile_spec, record_sha256, write_packet

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "swanson_tatge_1953_nbs_circ539v1"
SOURCE_SHA256 = "af69ed341f5d81b6cd651b984ce489462f8ea798dfa95a98ace78a91b153bade"
FILES = {"materials": "materials.json", "properties": "reference_properties.json", "sources": "sources.json"}
PIN_KEYS = {"materials": "materials", "properties": "reference_properties", "sources": "sources"}
ORACLES = {
    "materials": ("experimental/material-batches/20261015-nbs-halide-densities/nbs-materials.candidate.json",
                  "55e4c6f97e84ab39d984acf37224e0a5e059e2570ec827aa95f850c658738486"),
    "properties": ("experimental/material-batches/20261015-nbs-halide-densities/nbs-reference-properties.candidate.json",
                   "64559d1d60bdafe72716921ac135a7bf8a77eae9fac9c05be6492d0735f91816"),
    "sources": ("experimental/material-batches/20261016-nbs-next-inorganic/sources.reused.json",
                "616bda4835a62120df3fa2c088bc3e3aa06158cd291fdeec81100d2d58150594"),
}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def selection(graph, indices):
    identities = [deepcopy(graph["materials"]["identities"][index]) for index in indices]
    identity_ids = {row["id"] for row in identities}
    states = [deepcopy(row) for row in graph["materials"]["records"] if row["identity_id"] in identity_ids]
    state_ids = {row["id"] for row in states}
    return {
        "materials": {"schema_version": "1.0.0", "identities": identities, "grades": [], "records": states},
        "properties": {"schema_version": "1.0.0", "records": [deepcopy(row)
                       for row in graph["properties"]["records"] if row["material_state_id"] in state_ids]},
        "sources": deepcopy(graph["sources"]),
    }


def reference(record, shared):
    fields = deepcopy(record)
    for key, value in shared.items():
        if fields.pop(key) != value:
            raise AssertionError("the frozen fixture does not share " + key)
    return {"context": "nbs", "fields": fields}


class InorganicFormulationPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = {}
        for table, (relative, expected) in ORACLES.items():
            raw = (ROOT / relative).read_bytes()
            if sha256(raw).hexdigest() != expected:
                raise AssertionError("frozen source-transcription oracle changed: " + relative)
            cls.oracle[table] = json.loads(raw)
        if record_sha256(cls.oracle["sources"]["records"][0]) != SOURCE_SHA256:
            raise AssertionError("frozen source record changed")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.baseline = self.root / "baseline"
        self.baseline.mkdir()
        self.baseline_graph = selection(self.oracle, [0])
        self.append = selection(self.oracle, [1, 2, 3])
        shared = {
            "identity": {"version": "1.0.0", "category": "inorganic"},
            "state": {"version": "1.0.0", "grade_id": None},
            "property": {"version": "1.0.0", "quantity": "mass_density", "quantity_dimension": "mass_per_volume"},
        }
        self.spec = {
            "schema": "formulation-packet-spec/1", "batch_id": "existing_nbs_halides_test_replay",
            "baseline_sha256": {}, "source_records": [
                {"record": deepcopy(self.oracle["sources"]["records"][0]), "sha256": SOURCE_SHA256}],
            "contexts": {kind: {"nbs": fields} for kind, fields in shared.items()},
            "formulations": [], "identity_crosswalk": [],
            "review": {
                "formal_admitted_delta": 0,
                "verification": {"independent_scientific_review": False, "raw_data_reanalysis": False},
                "source_reviews": [{"source_id": SOURCE_ID, "status": "selected_facts_checked",
                    "note": "Replay the frozen selected NBS-authored density statements only; exclude third-party "
                            "comparisons. Republished courtesy of the National Institute of Standards and Technology. "
                            "No new source inspection, scientific approval or asset redistribution."}],
            },
        }
        self.spec["contexts"]["grade"] = {}
        for identity in self.append["materials"]["identities"]:
            state = next(row for row in self.append["materials"]["records"] if row["identity_id"] == identity["id"])
            prop = next(row for row in self.append["properties"]["records"] if row["material_state_id"] == state["id"])
            self.spec["formulations"].append({
                "identity": reference(identity, shared["identity"]), "grades": [],
                "states": [{"record": reference(state, shared["state"]),
                            "properties": [reference(prop, shared["property"])]}],
            })
            self.spec["identity_crosswalk"].append({
                "identity_id": identity["id"], "source_id": SOURCE_ID,
                "source_designations": [state["source_designation"]], "disposition": "distinct",
                "evidence": deepcopy(identity["evidence"]),
                "note": "Frozen composition-level record replay against a deliberately smaller test baseline; "
                        "no new scientific identity claim or automatic composition inference.",
            })
        self.write_baseline(self.baseline_graph)

    def write_baseline(self, graph):
        for table, filename in FILES.items():
            raw = encoded(graph[table])
            (self.baseline / filename).write_bytes(raw)
            self.spec["baseline_sha256"][PIN_KEYS[table]] = sha256(raw).hexdigest()

    def assert_refused_without_write(self):
        spec_path, output = self.root / "spec.json", self.root / "packet.json"
        spec_path.write_bytes(encoded(self.spec))
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        with self.assertRaises(ValueError):
            write_packet(self.baseline, spec_path, output, repository_root=self.root)
        self.assertFalse(output.exists())
        self.assertEqual({path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}, before)

    def assert_pending(self):
        packet = compile_spec(self.spec, self.baseline)
        self.assertFalse(packet["report"]["handoff_ready"])
        self.assertTrue(packet["report"]["pending_gates"])
        self.assertEqual(packet["review"], self.spec["review"])
        self.assertEqual(packet["report"]["formal_admitted_delta"], 0)
        self.assertEqual(packet["catalogs"]["sources"]["records"][0], self.spec["source_records"][0]["record"])
        return packet

    def test_multiple_inorganic_rows_reuse_one_source_without_grades_or_fact_changes(self):
        packet = compile_spec(self.spec, self.baseline)
        self.assertTrue(packet["report"]["handoff_ready"])
        self.assertEqual(packet["catalogs"], self.append)
        self.assertEqual(packet["input"], self.spec)
        self.assertEqual(packet["review"], self.spec["review"])
        delta = packet["report"]["delta"]
        self.assertEqual({key: delta[key] for key in ("identities", "states", "properties", "grades", "sources")},
                         {"identities": 3, "states": 3, "properties": 3, "grades": 0, "sources": 0})
        self.assertEqual(delta["categories"]["inorganic"], 3)
        self.assertEqual(packet["report"]["formal_admitted_delta"], 0)
        self.assertIsNone(packet["catalogs"]["sources"]["records"][0]["license"]["identifier"])
        for prop in packet["catalogs"]["properties"]["records"]:
            self.assertEqual(prop["determination_basis"], "source_reports_calculation")
            self.assertEqual(prop["reported_value"]["unit_code"], "g/cm^3")
            self.assertFalse(prop["verification"]["independent_scientific_review"])

    def test_exact_repeat_against_enlarged_baseline_has_zero_increment(self):
        packet = compile_spec(self.spec, self.baseline)
        self.assertEqual(compile_spec(self.spec, self.baseline), packet)
        self.write_baseline(self.oracle)
        for row in self.spec["identity_crosswalk"]:
            row["disposition"] = "existing"
        replay = compile_spec(self.spec, self.baseline)
        self.assertTrue(replay["report"]["handoff_ready"])
        self.assertEqual(replay["catalogs"], packet["catalogs"])
        self.assertEqual(replay["report"]["before"], replay["report"]["after"])

    def test_source_scoped_designation_and_alias_collisions_refuse_atomic_output(self):
        original = deepcopy(self.spec)
        for kind in ("designation", "alias"):
            with self.subTest(kind=kind):
                self.spec = deepcopy(original)
                row = self.spec["formulations"][0]
                if kind == "designation":
                    label = self.baseline_graph["materials"]["records"][0]["source_designation"]
                    row["states"][0]["record"]["fields"]["source_designation"] = label
                    self.spec["identity_crosswalk"][0]["source_designations"] = [label]
                else:
                    label = self.baseline_graph["materials"]["identities"][0]["name"]
                    row["identity"]["fields"]["aliases"].append({"language": "en", "text": label})
                self.assert_refused_without_write()

    def test_bad_later_unit_or_unsupported_quantity_refuses_whole_batch(self):
        original = deepcopy(self.spec)
        for kind in ("wrong_density_unit", "unsupported_conductivity"):
            with self.subTest(kind=kind):
                self.spec = deepcopy(original)
                prop = self.spec["formulations"][-1]["states"][0]["properties"][0]["fields"]
                if kind == "wrong_density_unit":
                    prop["reported_value"].update(unit_text="MPa", unit_code="MPa")
                else:
                    self.spec["contexts"]["property"]["conductivity"] = {
                        "version": "1.0.0", "quantity": "thermal_conductivity", "quantity_dimension": "thermal_conductivity"}
                    self.spec["formulations"][-1]["states"][0]["properties"][0]["context"] = "conductivity"
                    prop["reported_value"].update(unit_text="W/(m K)", unit_code="W/(m K)")
                self.assert_refused_without_write()

    def test_source_pin_and_baseline_record_cannot_be_rewritten(self):
        original = deepcopy(self.spec)
        for kind in ("wrong_hash", "rehashed_rewrite"):
            with self.subTest(kind=kind):
                self.spec = deepcopy(original)
                descriptor = self.spec["source_records"][0]
                if kind == "wrong_hash":
                    descriptor["sha256"] = "0" * 64
                else:
                    descriptor["record"]["claim_notes"].append("Synthetic altered rights scope.")
                    descriptor["sha256"] = record_sha256(descriptor["record"])
                self.assert_refused_without_write()

    def test_rehashed_notice_or_claimed_license_cannot_replace_frozen_source_permission(self):
        original, baseline = deepcopy(self.spec), deepcopy(self.baseline_graph)
        for kind in ("changed_notice", "claimed_spdx", "another_government_source"):
            with self.subTest(kind=kind):
                self.spec, graph = deepcopy(original), deepcopy(baseline)
                if kind == "another_government_source":
                    self.spec = json.loads(json.dumps(self.spec).replace(SOURCE_ID, "fictional_government_source"))
                    graph = json.loads(json.dumps(graph).replace(SOURCE_ID, "fictional_government_source"))
                source = graph["sources"]["records"][0]
                if kind == "changed_notice":
                    source["claim_notes"].append("Synthetic extension to unreviewed comparisons.")
                elif kind == "claimed_spdx":
                    source["license"] = {"status": "explicit_reuse_license_verified", "identifier": "CC-BY-4.0"}
                self.spec["source_records"][0] = {"record": deepcopy(source), "sha256": record_sha256(source)}
                self.write_baseline(graph)
                self.assert_pending()

    def test_known_notice_requires_existing_baseline_source_and_exact_document_scope(self):
        original = deepcopy(self.spec)
        for kind in ("absent_baseline_source", "wrong_document_hash", "different_registered_url", "other_category"):
            with self.subTest(kind=kind):
                self.spec = deepcopy(original)
                self.write_baseline(self.baseline_graph)
                if kind == "absent_baseline_source":
                    empty = selection(self.oracle, [])
                    empty["sources"]["records"] = []
                    self.write_baseline(empty)
                elif kind == "other_category":
                    self.spec["contexts"]["identity"]["nbs"]["category"] = "polymer"
                else:
                    reference = self.spec["formulations"][-1]["states"][0]["properties"][0]
                    document = reference["fields"]["source_document"]
                    if kind == "wrong_document_hash":
                        document["sha256"] = "0" * 64
                    else:
                        # Keep primary-value evidence internally consistent so
                        # the source-specific scope, not a broken URL link,
                        # prevents this otherwise registered URL substitution.
                        reference["fields"] = json.loads(json.dumps(reference["fields"]).replace(
                            document["url"], "https://doi.org/10.6028/NBS.CIRC.539v1"))
                self.assert_pending()

    def test_nbs_source_review_stays_pending_and_scientific_flags_cannot_upgrade(self):
        self.spec["review"]["source_reviews"][0]["status"] = "pending"
        packet = self.assert_pending()
        self.assertTrue(any("transcription/rights scope" in reason for reason in packet["report"]["pending_gates"]))
        self.assertFalse(packet["review"]["verification"]["independent_scientific_review"])
        self.spec["review"]["verification"]["independent_scientific_review"] = True
        self.assert_refused_without_write()


if __name__ == "__main__":
    unittest.main()
