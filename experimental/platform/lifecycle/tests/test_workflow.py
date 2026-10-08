import copy
import json
from pathlib import Path
import tempfile
import unittest
from dataclasses import replace
from materials_lifecycle.workflow import Workflow, Profile, Response, LifecycleError, canonical, digest, read_json, strict_load

FIXTURE = Path(__file__).parents[1] / "fixtures/nomad_archive_projected.json"

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workflow = Workflow(self.temp.name)
        self.entry = json.loads(FIXTURE.read_bytes())
        self.rid = "nomad:" + self.entry["metadata"]["entry_id"]

    def acquire(self, entries=None, raw=None, workflow=None, query=None, pagination=None):
        raw = raw if raw is not None else canonical({"data": entries or [self.entry], "pagination": pagination or {"total": 9000}})
        return (workflow or self.workflow).capture(query or {"formula": "CaFe2Re", "limit": 25},
            fetch=lambda *a, **k: Response(raw), fixture=True)

    def stage(self, **kwargs):
        return self.workflow.stage(self.acquire(**kwargs))

    def review(self, batch, ids=None, **kwargs):
        return self.workflow.review(batch, approved_ids=ids or [self.rid], reviewer="independent-local-reviewer",
            contributor="fixture-author", rationale="Manually inspected exact candidate; demo only",
            rights_evidence="https://creativecommons.org/licenses/by/4.0/", demo=True, **kwargs)

    def build(self, batch, decision, **kwargs):
        return self.workflow.build(batch, decision, trusted_decision_sha256=decision.stem,
            version=kwargs.pop("version", "1.0.0"), title="Fixture demonstration", creators=["Prototype test"], **kwargs)

    def test_deterministic_repeat_and_raw_bytes(self):
        first, second = self.acquire(), self.acquire()
        self.assertNotEqual(first, second) # distinct acquisition attempts
        a, b = self.workflow.stage(first), self.workflow.stage(second)
        self.assertEqual(a, b)
        raw_hash = read_json(first)["pages"][0]["raw_sha256"]
        self.assertTrue((Path(self.temp.name) / "raw" / raw_hash).exists())

    def test_raw_whitespace_invalidates_batch(self):
        a = self.stage()
        b = self.stage(raw=b' ' + canonical({"data": [self.entry], "pagination": {"total": 9000}}))
        self.assertNotEqual(a, b)

    def test_parser_provider_revision_schema_query_invalidate(self):
        original = self.stage()
        for key, value in [("parser_version", "2"), ("provider_revision", "2027"), ("schema_version", "candidate-2")]:
            workflow = Workflow(Path(self.temp.name) / key, replace(Profile(), **{key: value}))
            batch = workflow.stage(self.acquire(workflow=workflow))
            self.assertNotEqual(original.stem, batch.stem)
        self.assertNotEqual(original, self.stage(query={"formula": "CaFe2Re2", "limit": 25}))

    def test_exact_subset_release_and_counts(self):
        second = copy.deepcopy(self.entry)
        second["metadata"]["entry_id"] = "second"
        batch = self.stage(entries=[self.entry, second])
        decision = self.review(batch)
        out = self.build(batch, decision)
        self.assertEqual(len(read_json(out / "records.json")), 1)
        manifest = read_json(out / "manifest.json")
        self.assertEqual(manifest["counts"]["material_identities"], 0)
        self.assertEqual(manifest["counts"]["source_records"], 1)
        self.assertEqual(manifest["citation"]["doi_status"], "unregistered")
        self.assertIsNone(manifest["citation"]["dataset_version_doi"])
        self.assertEqual(read_json(batch)["acquisition_content"]["pages"][0]["provider_total_entries"], "9000")

    def test_archive_deterministic(self):
        batch = self.stage()
        decision = self.review(batch)
        out = self.build(batch, decision)
        first = (out / "dataset.tar").read_bytes()
        self.assertEqual(first, (self.build(batch, decision) / "dataset.tar").read_bytes())

    def test_mutated_candidate_invalidates_review(self):
        batch = self.stage()
        decision = self.review(batch)
        value = read_json(batch)
        value["records"][0]["formula"] = "Changed"
        batch.write_bytes(canonical(value))
        with self.assertRaises(LifecycleError):
            self.build(batch, decision)

    def test_mutated_raw_invalidates_review(self):
        batch = self.stage()
        decision = self.review(batch)
        raw_hash = read_json(batch)["context"]["raw_hashes"][0]
        (Path(self.temp.name) / "raw" / raw_hash).write_bytes(b"{}")
        with self.assertRaises(LifecycleError):
            self.build(batch, decision)

    def test_changed_numeric_value_requires_new_review(self):
        batch = self.stage()
        decision = self.review(batch)
        self.entry["results"]["method"]["simulation"]["dft"]["scf_threshold_energy_change"] = 1.602176635e-23
        changed = self.stage()
        with self.assertRaises(LifecycleError):
            self.build(changed, decision)

    def test_unknown_license_held(self):
        del self.entry["metadata"]["license"]
        batch = self.stage()
        self.assertIn("license_unknown", read_json(batch)["records"][0]["holds"])
        with self.assertRaises(LifecycleError):
            self.review(batch)

    def test_fixture_not_scientific(self):
        batch = self.stage()
        with self.assertRaises(LifecycleError):
            self.workflow.review(batch, approved_ids=[self.rid], reviewer="r", contributor="c", rationale="x",
                rights_evidence="https://example.com/license", demo=False)

    def test_injection_cannot_claim_live(self):
        with self.assertRaises(LifecycleError):
            self.workflow.capture({"formula": "Fe"}, fetch=lambda *a, **k: Response(b"{}"))

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(LifecycleError):
            self.stage(entries=[self.entry, self.entry])

    def test_unknown_lane_held(self):
        self.entry["results"]["method"] = {}
        with self.assertRaises(LifecycleError):
            self.review(self.stage())

    def test_experimental_lane_separate(self):
        self.entry["results"]["method"] = {"experimental": {"method": "x"}}
        self.assertEqual(read_json(self.stage())["records"][0]["lane"], "experimental")

    def test_malformed_duplicate_nan_and_encoding_fail(self):
        for raw in [b'{"data":[],"data":[]}', b'{"data":[NaN]}', b'{"data":[Infinity]}', b'\xff', b'{']:
            with self.subTest(raw=raw), self.assertRaises(LifecycleError):
                self.acquire(raw=raw)

    def test_lexical_precision_and_missing(self):
        payload = strict_load(b'{"v":1.2300e-8,"zero":0,"missing":null}')
        self.assertEqual(payload, {"v": "1.2300e-8", "zero": "0", "missing": None})

    def test_http_denials_rate_limit_and_compression(self):
        for response in [Response(b"", 401), Response(b"", 403), Response(b"", 429), Response(b"{}", headers={"Content-Encoding": "gzip"})]:
            with self.assertRaises(LifecycleError):
                self.workflow.capture({"formula": "Fe"}, fetch=lambda *a, **k: response, fixture=True)

    def test_byte_bound(self):
        workflow = Workflow(Path(self.temp.name) / "small", replace(Profile(), max_bytes=8))
        with self.assertRaises(LifecycleError):
            self.acquire(workflow=workflow)

    def test_pagination_bound_and_loop(self):
        batch = self.stage(pagination={"total": 999999, "next_page_after_value": "cursor"}, query={"formula": "Fe", "limit": 1})
        self.assertEqual(read_json(batch)["acquisition_content"]["pagination_status"], "bounded")
        with self.assertRaises(LifecycleError):
            self.acquire(pagination={"next_page_after_value": "loop"})

    def test_query_and_endpoint_allowlist(self):
        for query in [{"formula": "Fe", "token": "secret"}, {"formula": "https://x?token=y"}, {"formula": "Fe", "limit": 999}]:
            with self.assertRaises(LifecycleError):
                self.acquire(query=query)
        with self.assertRaises(LifecycleError):
            Workflow(self.temp.name, replace(Profile(), endpoint="https://example.com"))

    def test_revision_diff_not_new_identity(self):
        first = self.stage()
        self.entry["metadata"]["entry_hash"] = "new"
        second = self.workflow.stage(self.acquire(), baseline=first)
        self.assertEqual(read_json(second)["diff"]["changed"], [self.rid])
        self.assertEqual(read_json(second)["counts"]["material_identities"], 0)

    def test_version_collision(self):
        batch = self.stage()
        self.build(batch, self.review(batch))
        self.entry["metadata"]["entry_hash"] = "new"
        changed = self.stage()
        with self.assertRaises(LifecycleError):
            self.build(changed, self.review(changed))

    def test_detached_retraction_preserves_release(self):
        batch = self.stage()
        out = self.build(batch, self.review(batch))
        original = (out / "manifest.json").read_bytes()
        event = self.workflow.status_event(out, record_id=self.rid, kind="withdrawn", reason="Source retracted", source_url="https://example.com/notice")
        self.assertEqual(read_json(event)["kind"], "withdrawn")
        self.assertEqual(original, (out / "manifest.json").read_bytes())

    def test_source_withdrawn_held(self):
        self.entry["metadata"]["retracted"] = True
        with self.assertRaises(LifecycleError):
            self.review(self.stage())

    def test_review_exact_ids_and_independence(self):
        batch = self.stage()
        for ids in [["unknown"], [self.rid, self.rid]]:
            with self.assertRaises(LifecycleError):
                self.review(batch, ids)
        with self.assertRaises(LifecycleError):
            self.workflow.review(batch, approved_ids=[self.rid], reviewer="same", contributor="same", rationale="x", rights_evidence="https://example.com", demo=True)

if __name__ == "__main__":
    unittest.main()
