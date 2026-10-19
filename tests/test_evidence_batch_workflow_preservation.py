"""Keep branch selection and all predecessor workflow/test bytes explicit."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import evidence_batch_workflow_preservation as history
from source_family_growth_preservation import project_growth_file
from scripts import check_evidence_batch_scope as scope


ROOT = Path(__file__).resolve().parents[1]
HELPER_SHA256 = 'e43052745c55e1636766ffd65d33cd40d63e7e758c9b44fc1e406c0fd2784dc4'


class EvidenceBatchWorkflowPreservationTests(unittest.TestCase):
    def test_helper_ledger_and_all_previous_ledgers_are_pinned(self):
        self.assertEqual(history.digest(project_growth_file("tests/evidence_batch_workflow_preservation.py", (ROOT / "tests/evidence_batch_workflow_preservation.py").read_bytes())),
                         HELPER_SHA256)
        ledger = history.load_ledger()
        self.assertEqual(ledger["baseline_commit"], "12cb89ca82b48ba444bdb921674c3d232d448720")
        self.assertEqual(len(ledger["preserved_ledger_sha256"]), 10)
        self.assertEqual(ledger["preserved_ledger_sha256"]["tests/fixtures/material_class_counts_updates_20261019.json"],
                         "6903abbfe027266b2e8f3ea90261600fd72982390c2431e836861b92a17fd894")
        for path, expected in ledger["preserved_ledger_sha256"].items():
            self.assertEqual(history.digest((ROOT / path).read_bytes()), expected)

    def test_three_complete_predecessor_files_round_trip_exactly(self):
        entries = history.validate_ledger(history.load_ledger())
        self.assertEqual(set(entries), {
            ".github/workflows/ci.yml", "tests/material_class_counts_preservation.py",
            "tests/test_material_class_counts_preservation.py",
        })
        for path, entry in entries.items():
            with self.subTest(path=path):
                raw = (ROOT / path).read_bytes()
                raw = project_growth_file(path, raw)
                previous = history.pre_evidence_batch_workflow_bytes(path, raw)
                self.assertEqual(history.digest(raw), entry["sha256"])
                self.assertEqual(history.digest(previous), entry["previous_sha256"])
                self.assertEqual(history.apply_exact_edits(previous, entry["edits"]), raw)
                self.assertEqual(history.pre_evidence_batch_workflow_bytes(path, previous), previous)

    def test_changed_bytes_paths_types_and_before_images_fail_closed(self):
        for path, entry in history.validate_ledger(history.load_ledger()).items():
            raw = (ROOT / path).read_bytes()
            previous = history.pre_evidence_batch_workflow_bytes(path, raw)
            for changed in (raw + b"!", raw[:-1], b"arbitrary", raw.decode("utf-8"), bytearray(raw), memoryview(raw)):
                with self.subTest(path=path, kind=type(changed).__name__):
                    with self.assertRaises(AssertionError):
                        history.pre_evidence_batch_workflow_bytes(path, changed)
            for mutate in (lambda x: x[0].update(offset=True),
                           lambda x: x[0].update(before=x[0]["before"] + "!"),
                           lambda x: x.append(deepcopy(x[0]))):
                edits = deepcopy(entry["edits"])
                mutate(edits)
                with self.assertRaises(AssertionError):
                    history.apply_exact_edits(previous, edits)
        for path in ("../README.md", "README.md", None, []):
            with self.assertRaises(AssertionError):
                history.pre_evidence_batch_workflow_bytes(path, b"unknown")

    def test_ledger_drift_and_duplicate_keys_fail_without_mutating_original(self):
        original = history.load_ledger()
        for mutate in (lambda x: x.update(extra=True), lambda x: x.update(schema_version=True),
                       lambda x: x.update(baseline_commit="0" * 40), lambda x: x["updates"].pop(),
                       lambda x: x["updates"].append(deepcopy(x["updates"][0])),
                       lambda x: x["updates"][0].update(sha256="0" * 64),
                       lambda x: x["preserved_ledger_sha256"].clear()):
            changed = deepcopy(original)
            mutate(changed)
            with self.assertRaises(AssertionError):
                history.validate_ledger(changed)
        with self.assertRaises(AssertionError):
            history.unique_keys([("updates", []), ("updates", [])])
        self.assertEqual(history.load_ledger(), original)

    def test_old_jobs_and_previous_experiment_are_preserved_exactly(self):
        raw = (ROOT / ".github/workflows/ci.yml").read_bytes()
        raw = project_growth_file(".github/workflows/ci.yml", raw)
        previous = history.pre_evidence_batch_workflow_bytes(".github/workflows/ci.yml", raw).decode("utf-8")
        text = raw.decode("utf-8")
        self.assertEqual(text, scope.expected_workflow(previous))
        old_job = previous[previous.index("  polymer-composites-targeted:\n"):]
        self.assertEqual(text[text.index("  polymer-composites-targeted:\n"):text.index("  evidence-batch-targeted:\n")], old_job)
        self.assertEqual(text.count(scope.FULL_JOB_IF), 2)
        self.assertEqual(text.removesuffix(scope.TARGETED_JOB).replace(scope.FULL_JOB_IF, scope.PREVIOUS_FULL_JOB_IF), previous)
        self.assertIn("permissions:\n  contents: read\n", text)
        self.assertNotIn("contents: write", text)

    def test_unquoted_yaml_scalars_and_nonlocal_wheel_arguments_are_rejected(self):
        for command in (
            "python -m pip install --no-deps --only-binary=:all: -r experimental/platform/ci/build-requirements.txt",
            "python -m pip download --no-deps --only-binary=:all: --dest dist/dependencies -r experimental/platform/requirements-lock.txt -r experimental/platform/ci/projection-requirements.txt",
        ):
            quoted = '      - run: "' + command + '"'
            self.assertIn(quoted, scope.TARGETED_JOB)
            with self.assertRaises(RuntimeError):
                scope.validate_targeted_run_scalars(scope.TARGETED_JOB.replace(quoted, "      - run: " + command))
        for changed in (scope.BUILD_COMMAND.replace("./formal-catalog", "formal-catalog"),
                        scope.BUILD_COMMAND.replace(" --no-index", ""),
                        scope.BUILD_COMMAND.replace("./experimental/platform/lifecycle", "other-project")):
            with self.assertRaises(RuntimeError):
                scope.validate_wheel_command(changed)

    def test_scope_rejects_unknown_paths_deletions_and_nonfiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / ".github/workflows/ci.yml"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"synthetic test-only file")
            scope.validate_names([".github/workflows/ci.yml"], root=root)
            for names in (["../outside"], ["materials_boundaries/engine.py"], [None]):
                with self.assertRaises(RuntimeError):
                    scope.validate_names(names, root=root)
            path.unlink()
            path.mkdir()
            with self.assertRaises(RuntimeError):
                scope.validate_names([".github/workflows/ci.yml"], root=root)
        for raw in (b"D\0README.md\0", b"R100\0old\0new\0", b"M\0"):
            with self.assertRaises(RuntimeError):
                scope.changed_paths(raw)


if __name__ == "__main__":
    unittest.main()
