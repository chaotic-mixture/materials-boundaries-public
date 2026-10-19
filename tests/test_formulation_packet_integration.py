"""Single-artifact v2 handoff; fictional records exercise no scientific approval."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from scripts.integrate_material_candidates import FILES, PIN_KEYS, build_package, write_package
from scripts.prepare_formulation_packet import compile_spec, record_sha256
from test_material_reference_contract import synthetic_material_catalog
from test_material_append_merge import append_fixture


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def save(path, value):
    path.write_bytes(encoded(value))
    return sha256(path.read_bytes()).hexdigest()


class FormulationPacketIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.baseline = self.root / "baseline"
        self.baseline.mkdir()
        self.packet_dir = self.root / "experimental/material-batches/fixture"
        self.packet_dir.mkdir(parents=True)
        self.packet_path = self.packet_dir / "prepared.json"
        self.manifest_path = self.packet_dir / "integration.json"
        self.output = self.root / "integrated.json"
        graph = dict(zip(FILES, synthetic_material_catalog()))
        graph["materials"]["identities"][0]["category"] = "polymer"
        # This is an explicit fictional source assertion, not a test-only
        # validation bypass or a real legal/source decision.
        source = graph["sources"]["records"][0]
        source["license"] = {"status": "explicit_reuse_license_verified", "identifier": "SYNTHETIC-TEST-ONLY"}
        pins = {PIN_KEYS[key]: save(self.baseline / FILES[key], value) for key, value in graph.items()}
        append = append_fixture()
        identity = append["materials"]["identities"][0]
        state = append["materials"]["records"][0]
        grade = append["materials"]["grades"][0]
        identity["category"] = "polymer"
        for record in (identity, state):
            record["name"] = "Fictional formulation B"
            record["names"] = {language: record["name"] for language in ("en", "zh", "ja", "de")}
        state["source_designation"] = "SYN-B"
        grade["designation"] = "SYN-B"
        reference = lambda fields: {"context": "common", "fields": deepcopy(fields)}
        self.spec = {
            "schema": "formulation-packet-spec/1", "batch_id": "fictional-b",
            "baseline_sha256": pins,
            "source_records": [{"record": source, "sha256": record_sha256(source)}],
            "contexts": {kind: {"common": {}} for kind in ("identity", "grade", "state", "property")},
            "formulations": [{"identity": reference(identity), "grades": [reference(grade)],
                              "states": [{"record": reference(state),
                                          "properties": [reference(append["properties"]["records"][0])]}]}],
            "identity_crosswalk": [{"identity_id": identity["id"], "source_id": source["id"],
                                    "source_designations": ["SYN-B"], "disposition": "distinct",
                                    "evidence": deepcopy(identity["evidence"]), "note": "Fictional plumbing fixture only."}],
            "review": {"verification": {"independent_scientific_review": False, "raw_data_reanalysis": False},
                       "formal_admitted_delta": 0,
                       "source_reviews": [{"source_id": source["id"], "status": "selected_facts_checked",
                                           "note": "Synthetic facts and license marker; no real approval."}]},
        }
        self.packet = compile_spec(self.spec, self.baseline)
        self.batch = {"id": self.spec["batch_id"], "candidate_commit": "0" * 40,
                      "packet": {"path": "prepared.json", "sha256": save(self.packet_path, self.packet)}}
        self.manifest = {"schema": "experimental-material-integration/2", "scope": "local-experimental-only",
                         "baseline_sha256": pins, "batches": [self.batch], "status_adjustments": [],
                         "pending_gates": ["Experimental artifact only; release remains separate."],
                         "released_main_count": 1081}
        self.flush()

    def flush(self):
        save(self.manifest_path, self.manifest)

    def replace_packet(self, packet):
        self.batch["packet"]["sha256"] = save(self.packet_path, packet)
        self.flush()

    def integrate(self):
        return write_package(self.baseline, self.manifest_path, self.output, repository_root=self.root)

    def assert_rejected_without_output(self):
        snapshot = {path: path.read_bytes() for path in self.root.rglob("*.json")}
        with self.assertRaises((ValueError, TypeError, KeyError)):
            self.integrate()
        self.assertFalse(self.output.exists())
        self.assertEqual(snapshot, {path: path.read_bytes() for path in self.root.rglob("*.json")})

    def test_single_packet_replays_then_integrates_idempotently(self):
        package, created = self.integrate()
        self.assertTrue(created)
        self.assertEqual(package["report"]["delta"]["identities"], 1)
        self.assertEqual(package["report"]["formal_admitted_delta"], 0)
        self.assertEqual(package["report"]["batches"][0]["inputs"], {"packet": self.batch["packet"]})
        saved, timestamp = self.output.read_bytes(), self.output.stat().st_mtime_ns
        again, created = self.integrate()
        self.assertFalse(created)
        self.assertEqual(again, package)
        self.assertEqual(self.output.read_bytes(), saved)
        self.assertEqual(self.output.stat().st_mtime_ns, timestamp)

    def test_rehashed_tampering_cannot_replace_full_packet_replay(self):
        for field in ("ready", "count", "catalog", "source", "review", "extra"):
            with self.subTest(field=field):
                packet = deepcopy(self.packet)
                if field == "ready":
                    packet["report"]["handoff_ready"] = False
                elif field == "count":
                    packet["report"]["delta"]["identities"] = 1000
                elif field == "catalog":
                    packet["catalogs"]["properties"]["records"][0]["reported_value"]["number"] = "4.00"
                elif field == "source":
                    packet["catalogs"]["sources"]["records"][0]["title"] = "Forged source"
                elif field == "review":
                    packet["review"]["verification"]["independent_scientific_review"] = True
                else:
                    packet["unreviewed"] = True
                self.replace_packet(packet)
                self.assert_rejected_without_output()

    def test_missing_crosswalk_is_reportable_but_not_integrable(self):
        spec = deepcopy(self.spec)
        spec["identity_crosswalk"] = []
        packet = compile_spec(spec, self.baseline)
        self.assertFalse(packet["report"]["handoff_ready"])
        self.replace_packet(packet)
        self.assert_rejected_without_output()
        packet["report"]["handoff_ready"] = True
        packet["report"]["pending_gates"] = []
        self.replace_packet(packet)
        self.assert_rejected_without_output()

    def test_closed_manifest_binding_hash_and_no_adjustment_contract(self):
        for field in ("batch_id", "hash", "extra", "adjustment", "schema", "baseline"):
            with self.subTest(field=field):
                saved = deepcopy(self.manifest)
                if field == "batch_id":
                    self.batch["id"] = "wrong-batch"
                elif field == "hash":
                    self.batch["packet"]["sha256"] = "f" * 64
                elif field == "extra":
                    self.batch["materials"] = self.batch["packet"]
                elif field == "adjustment":
                    self.manifest["status_adjustments"] = [{"reason": "not allowed"}]
                elif field == "schema":
                    self.manifest["schema"] = "experimental-material-integration/3"
                else:
                    self.manifest["baseline_sha256"]["materials"] = "f" * 64
                self.flush()
                self.assert_rejected_without_output()
                self.manifest = saved
                self.batch = self.manifest["batches"][0]
                self.flush()

    def test_cross_batch_source_designation_collision_is_atomic(self):
        other = json.loads(json.dumps(self.spec).replace("synthetic_b", "synthetic_c")
                           .replace("Fictional formulation B", "Fictional formulation C")
                           .replace("Another fictional", "Third fictional"))
        other["batch_id"] = "fictional-c"
        other_packet = compile_spec(other, self.baseline)
        path = self.packet_dir / "other.json"
        self.manifest["batches"].append({"id": other["batch_id"], "candidate_commit": "1" * 40,
                                         "packet": {"path": "other.json", "sha256": save(path, other_packet)}})
        self.flush()
        self.assert_rejected_without_output()

    def test_linked_grade_designation_and_alias_cannot_create_another_identity(self):
        for collision in ("designation", "alias"):
            with self.subTest(scope="baseline", collision=collision):
                spec = deepcopy(self.spec)
                grade = spec["formulations"][0]["grades"][0]["fields"]
                if collision == "designation":
                    grade["designation"] = "SYN-A"
                else:
                    grade["aliases"] = [{"language": "und", "text": "SYN-A"}]
                with self.assertRaisesRegex(ValueError, "collides with another identity"):
                    compile_spec(spec, self.baseline)
        other = json.loads(json.dumps(self.spec).replace("synthetic_b", "synthetic_c")
                           .replace("Fictional formulation B", "Fictional formulation C")
                           .replace("Another fictional", "Third fictional"))
        other["batch_id"] = "fictional-c"
        other["formulations"][0]["states"][0]["record"]["fields"]["source_designation"] = "RENAMED-STATE-C"
        other["identity_crosswalk"][0]["source_designations"] = ["RENAMED-STATE-C"]
        for collision in ("designation", "alias", None):
            with self.subTest(scope="cross_batch", collision=collision):
                spec = deepcopy(other)
                grade = spec["formulations"][0]["grades"][0]["fields"]
                grade["designation"] = "SYN-B" if collision == "designation" else "SYN-C"
                grade["aliases"] = [{"language": "und", "text": "SYN-B"}] if collision == "alias" else []
                packet = compile_spec(spec, self.baseline)
                path = self.packet_dir / "other.json"
                self.manifest["batches"] = [self.batch, {"id": spec["batch_id"], "candidate_commit": "1" * 40,
                    "packet": {"path": "other.json", "sha256": save(path, packet)}}]
                self.flush()
                if collision:
                    self.assert_rejected_without_output()
                else:
                    result = build_package(self.baseline, self.manifest_path, repository_root=self.root)
                    self.assertEqual(result["report"]["delta"]["identities"], 2)
                    self.assertFalse(self.output.exists())

    def test_v1_still_accepts_its_original_four_descriptors_and_encoding(self):
        original_batch = {"id": self.spec["batch_id"], "candidate_commit": "0" * 40}
        for name, value in {**self.packet["catalogs"], "review": self.packet["review"]}.items():
            path = self.packet_dir / (name + ".json")
            original_batch[name] = {"path": path.name, "sha256": save(path, value)}
        self.manifest["schema"] = "experimental-material-integration/1"
        self.manifest["batches"] = [original_batch]
        self.flush()
        package, created = self.integrate()
        self.assertTrue(created)
        self.assertEqual(list(package["report"]["batches"][0]["inputs"]), ["materials", "properties", "sources", "review"])
        self.assertEqual(package["catalogs"]["materials"]["identities"][-1]["id"], "mat_synthetic_b")
        expected = (json.dumps(package, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        self.assertEqual(self.output.read_bytes(), expected)


if __name__ == "__main__":
    unittest.main()
