"""Bounded workflow behavior and scope rejection for the six-oxide branch."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("source_family_growth_ci", ROOT / "scripts/run_source_family_growth_ci.py")
ci = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci)


class SourceFamilyGrowthCITests(unittest.TestCase):
    def test_previous_jobs_keep_every_step_and_only_new_branch_is_gated(self):
        prior = ci.git("show", ci.BASE_COMMIT + ":.github/workflows/ci.yml").decode("utf-8")
        current = (ROOT / ".github/workflows/ci.yml").read_bytes().decode("utf-8")
        self.assertEqual(current, ci.expected_workflow(prior))
        restored = current.removesuffix(ci.TARGETED_JOB).replace(ci.FULL_JOB_IF, ci.PREVIOUS_FULL_JOB_IF)
        self.assertEqual(restored, prior)
        self.assertEqual(current.count("  source-family-growth-targeted:\n"), 1)
        self.assertEqual(ci.FULL_JOB_IF.count(ci.BRANCH_REF), 1)
        self.assertIn("github.event_name != 'push'", ci.FULL_JOB_IF)
        self.assertIn("github.event_name == 'push'", ci.TARGETED_JOB)
        self.assertIn("persist-credentials: false", ci.TARGETED_JOB)
        self.assertIn("python-version: '3.11'", ci.TARGETED_JOB)
        self.assertIn("python-version: '3.12'", ci.TARGETED_JOB)

    def test_scope_rejects_unlisted_paths_deleted_files_and_nonfiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            allowed = "scripts/run_source_family_growth_ci.py"
            (root / "scripts").mkdir()
            (root / allowed).write_text("fixture", encoding="utf-8")
            ci.validate_names([allowed], root=root)
            for names in (["credentials.json"], ["../outside"], [None]):
                with self.subTest(names=names), self.assertRaises(RuntimeError):
                    ci.validate_names(names, root=root)
            (root / allowed).unlink()
            with self.assertRaises(RuntimeError):
                ci.validate_names([allowed], root=root)
            (root / allowed).mkdir()
            with self.assertRaises(RuntimeError):
                ci.validate_names([allowed], root=root)
        for raw in (b"D\0README.md\0", b"R100\0old\0new\0", b"M\0", b"A\0one\0M\0"):
            with self.subTest(raw=raw), self.assertRaises(RuntimeError):
                ci.changed_paths(raw)

    def test_ci_requires_exact_event_branch_sha_and_clean_checkout(self):
        expected = {"GITHUB_ACTIONS": "true", "GITHUB_EVENT_NAME": "push",
                    "GITHUB_REF": ci.BRANCH_REF, "GITHUB_SHA": "f" * 40}
        with patch.dict(ci.os.environ, expected, clear=True), patch.object(ci, "git", return_value=b""):
            ci.validate_event("f" * 40)
        for key, value in (("GITHUB_EVENT_NAME", "pull_request"), ("GITHUB_REF", "refs/heads/main"),
                           ("GITHUB_REF", ci.PREVIOUS_BRANCH_REF), ("GITHUB_SHA", "e" * 40)):
            with self.subTest(key=key, value=value), patch.dict(ci.os.environ, {**expected, key: value}, clear=True):
                with patch.object(ci, "git", return_value=b""), self.assertRaises(RuntimeError):
                    ci.validate_event("f" * 40)
        with patch.dict(ci.os.environ, expected, clear=True), patch.object(ci, "git", return_value=b" M README.md\n"):
            with self.assertRaises(RuntimeError):
                ci.validate_event("f" * 40)

    def test_ambiguous_yaml_scalars_and_index_package_builds_fail(self):
        ci.validate_targeted_run_scalars(ci.TARGETED_JOB)
        ci.validate_wheel_command(ci.BUILD_COMMAND)
        for verb in ("install", "download"):
            marker = '      - run: "python -m pip ' + verb
            line = next(line for line in ci.TARGETED_JOB.splitlines() if line.startswith(marker))
            malformed = ci.TARGETED_JOB.replace(line, line.replace('run: "', 'run: ', 1)[:-1])
            with self.subTest(verb=verb), self.assertRaises(RuntimeError):
                ci.validate_targeted_run_scalars(malformed)
        for command in (ci.BUILD_COMMAND.replace("./formal-catalog", "formal-catalog"),
                        ci.BUILD_COMMAND.replace("--no-index ", ""),
                        ci.BUILD_COMMAND.replace("./experimental/platform/lifecycle", "https://example.invalid/package")):
            with self.subTest(command=command), self.assertRaises(RuntimeError):
                ci.validate_wheel_command(command)

    def test_unknown_predecessor_workflow_shapes_are_rejected(self):
        prior = ci.git("show", ci.BASE_COMMIT + ":.github/workflows/ci.yml").decode("utf-8")
        for value in (prior.replace(ci.PREVIOUS_FULL_JOB_IF, "", 1),
                      prior.replace("  evidence-batch-targeted:\n", "  missing-job:\n"),
                      prior.replace("  polymer-composites-targeted:\n", "  missing-job:\n"),
                      prior + ci.TARGETED_JOB):
            with self.subTest(length=len(value)), self.assertRaises(RuntimeError):
                ci.expected_workflow(value)


if __name__ == "__main__":
    unittest.main()
