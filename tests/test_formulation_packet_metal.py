"""Bounded manufacturer-profile gates, not a new source or scientific review."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_formulation_packet import compile_spec, record_sha256, write_packet

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "experimental/material-batches/outokumpu-core-moduli-20261020/prepared-packet.json"
ORACLE_SHA256 = "c7317758ae4c1a4025ac00c6b288770e61cf33056caaf1771a638af66d32b84f"
SOURCE_ID = "outokumpu_core_1560en4_202211"
SOURCE_SHA256 = "8495de101d6ce62a9f720cf5c5245aad4349989b0b9a68fee8c81aca501e5154"
FILES = {"materials": "materials.json", "properties": "reference_properties.json", "sources": "sources.json"}
PIN_KEYS = {"materials": "materials", "properties": "reference_properties", "sources": "sources"}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


class MetalFormulationPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = ORACLE.read_bytes()
        if sha256(raw).hexdigest() != ORACLE_SHA256:
            raise AssertionError("frozen manufacturer-profile oracle changed")
        cls.oracle = json.loads(raw)
        source = cls.oracle["catalogs"]["sources"]["records"][0]
        if source["id"] != SOURCE_ID or record_sha256(source) != SOURCE_SHA256:
            raise AssertionError("frozen manufacturer source changed")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.baseline = self.root / "baseline"
        self.baseline.mkdir()
        catalog = self.oracle["catalogs"]
        source = deepcopy(catalog["sources"]["records"][0])
        self.graph = {
            "materials": {"schema_version": "1.0.0", "identities": [], "grades": [], "records": []},
            "properties": {"schema_version": "1.0.0", "records": []},
            "sources": {"schema_version": "1.0.0", "records": [source]},
        }
        self.spec = {
            "schema": "formulation-packet-spec/1", "batch_id": "frozen_outokumpu_profile_test_replay",
            "baseline_sha256": {},
            "source_records": [{"record": source, "sha256": SOURCE_SHA256}],
            "contexts": {kind: {"explicit": {}} for kind in ("identity", "grade", "state", "property")},
            "formulations": [], "identity_crosswalk": [], "review": deepcopy(self.oracle["review"]),
        }
        reference = lambda row: {"context": "explicit", "fields": deepcopy(row)}
        # One ordinary reference and the marked manufacturer-tested reference
        # cover both supported determination bases without replaying all ten.
        for determination in ("not_stated", "source_reports_measurement"):
            prop = next(row for row in catalog["properties"]["records"]
                        if row["determination_basis"] == determination)
            state = next(row for row in catalog["materials"]["records"] if row["id"] == prop["material_state_id"])
            identity = next(row for row in catalog["materials"]["identities"] if row["id"] == state["identity_id"])
            grade = next(row for row in catalog["materials"]["grades"] if row["id"] == state["grade_id"])
            self.spec["formulations"].append({
                "identity": reference(identity), "grades": [reference(grade)],
                "states": [{"record": reference(state), "properties": [reference(prop)]}],
            })
            crosswalk = next(row for row in self.oracle["input"]["identity_crosswalk"]
                             if row["identity_id"] == identity["id"])
            self.spec["identity_crosswalk"].append(deepcopy(crosswalk))
        self.write_baseline(self.graph)

    def write_baseline(self, graph):
        for table, filename in FILES.items():
            raw = encoded(graph[table])
            (self.baseline / filename).write_bytes(raw)
            self.spec["baseline_sha256"][PIN_KEYS[table]] = sha256(raw).hexdigest()

    def prop(self):
        return self.spec["formulations"][-1]["states"][0]["properties"][0]["fields"]

    def assert_pending(self):
        packet = compile_spec(self.spec, self.baseline)
        self.assertFalse(packet["report"]["handoff_ready"])
        self.assertTrue(packet["report"]["pending_gates"])
        self.assertEqual(packet["review"], self.spec["review"])
        self.assertEqual(packet["report"]["formal_admitted_delta"], 0)
        self.assertEqual(packet["catalogs"]["sources"]["records"][0], self.spec["source_records"][0]["record"])
        return packet

    def test_frozen_manufacturer_profile_keeps_qualified_grades_and_reference_semantics(self):
        packet = compile_spec(self.spec, self.baseline)
        self.assertTrue(packet["report"]["handoff_ready"])
        self.assertEqual(packet["report"]["pending_gates"], [])
        self.assertEqual(packet["input"], self.spec)
        self.assertEqual(packet["review"], self.spec["review"])
        delta = packet["report"]["delta"]
        self.assertEqual({key: delta[key] for key in ("identities", "grades", "states", "properties", "sources")},
                         {"identities": 2, "grades": 2, "states": 2, "properties": 2, "sources": 0})
        self.assertEqual(delta["categories"]["metal"], 2)
        self.assertEqual(packet["report"]["formal_admitted_delta"], 0)
        self.assertEqual(packet["catalogs"]["sources"]["records"][0]["license"], {
            "status": "no_explicit_reuse_license_verified_limited_factual_curation_only", "identifier": None})
        for row, prop, grade in zip(self.spec["formulations"], packet["catalogs"]["properties"]["records"],
                                    packet["catalogs"]["materials"]["grades"]):
            self.assertEqual(prop, row["states"][0]["properties"][0]["fields"])
            self.assertEqual(grade, row["grades"][0]["fields"])
            self.assertEqual(prop["evidence_kind"], "manufacturer_reference")
            self.assertEqual(prop["conditions"]["temperature"]["text"], "20 \u00b0C")
            self.assertEqual(prop["reported_value"]["unit_code"], "GPa")
            self.assertEqual(prop["evaluation_support"], "catalog_only")
            self.assertIsNone(prop["uncertainty"])
            self.assertIsNone(prop["sample_count"]["value"])
            self.assertFalse(prop["verification"]["independent_scientific_review"])
            self.assertFalse(prop["verification"]["raw_data_reanalysis"])

    def test_rehashed_source_claimed_license_or_another_manufacturer_stays_pending(self):
        original, graph = deepcopy(self.spec), deepcopy(self.graph)
        for kind in ("changed_notice", "claimed_license", "different_source", "absent_baseline_source"):
            with self.subTest(kind=kind):
                self.spec, baseline = deepcopy(original), deepcopy(graph)
                if kind == "different_source":
                    self.spec = json.loads(json.dumps(self.spec).replace(SOURCE_ID, "fictional_manufacturer"))
                    baseline = json.loads(json.dumps(baseline).replace(SOURCE_ID, "fictional_manufacturer"))
                source = baseline["sources"]["records"][0]
                if kind == "changed_notice":
                    source["claim_notes"].append("Synthetic change of factual-curation scope.")
                elif kind == "claimed_license":
                    source["license"] = {"status": "explicit_reuse_license_verified", "identifier": "CC-BY-4.0"}
                self.spec["source_records"][0] = {"record": deepcopy(source), "sha256": record_sha256(source)}
                if kind == "absent_baseline_source":
                    baseline["sources"]["records"] = []
                self.write_baseline(baseline)
                packet = self.assert_pending()
                self.assertTrue(any("Source-specific rights remain pending" in reason
                                    for reason in packet["report"]["pending_gates"]))

    def test_document_or_property_scope_drift_stays_pending_without_conversion(self):
        original = deepcopy(self.spec)
        for kind in ("pdf_hash", "revision", "quantity", "unit", "temperature", "category", "reporting_basis",
                     "summary_statistic", "determination", "test_method"):
            with self.subTest(kind=kind):
                self.spec = deepcopy(original)
                prop = self.prop()
                if kind == "pdf_hash":
                    prop["source_document"]["sha256"] = "0" * 64
                elif kind == "revision":
                    prop["source_document"]["revision"] = "Synthetic unreviewed revision"
                elif kind == "quantity":
                    prop["quantity"] = "tensile_strength"
                elif kind == "unit":
                    prop["reported_value"]["unit_code"] = prop["reported_value"]["unit_text"] = "MPa"
                elif kind == "temperature":
                    prop["conditions"]["temperature"]["text"] = "21 \u00b0C"
                elif kind == "category":
                    self.spec["formulations"][-1]["identity"]["fields"]["category"] = "inorganic"
                elif kind == "reporting_basis":
                    prop["reporting_basis"] = "typical"
                elif kind == "summary_statistic":
                    prop["summary_statistic"] = "reported_value"
                elif kind == "determination":
                    prop["determination_basis"] = "source_reports_calculation"
                else:
                    fact = deepcopy(prop["conditions"]["temperature"])
                    fact["text"] = "Synthetic asserted specimen method"
                    prop["conditions"]["test_method"] = fact
                packet = self.assert_pending()
                self.assertEqual(packet["catalogs"]["properties"]["records"][-1], prop)

    def test_pending_source_review_and_scientific_upgrade_cannot_become_ready(self):
        self.spec["review"]["source_reviews"][0]["status"] = "pending"
        self.assert_pending()
        for field in ("independent_scientific_review", "raw_data_reanalysis"):
            with self.subTest(field=field):
                self.spec["review"]["verification"][field] = True
                spec_path, output = self.root / "spec.json", self.root / "prepared.json"
                spec_path.write_bytes(encoded(self.spec))
                before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
                with self.assertRaises(ValueError):
                    write_packet(self.baseline, spec_path, output, repository_root=self.root)
                self.assertFalse(output.exists())
                self.assertEqual({path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}, before)
                self.spec["review"]["verification"][field] = False


if __name__ == "__main__":
    unittest.main()
