"""Exact code-only recovery without changing any historical fixture or pin."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(ROOT / "tests"))
import material_append_history as history
import material_append_replay_compat as compatibility

BASE_COMMIT = "196995256836db2d8f870ac9a91f664bfdd03e7f"
HELPER_SHA256 = "653239fb0418a0261dfab53af106e267131e2774cf0138bca55d2d2c81be7288"
LEDGER_SHA256 = "b09510228cfcf6d3ae07833ce979636fb2334db84a2d586c1b0b313c718647dd"
CURRENT_SHA256 = "2379867c0fe4ec89cf4f450b10bf84e48986783d50396c6f593316de78ad3251"
PREVIOUS_SHA256 = "38d9b1768121f84cc5b45d21d8d992b8d62cf6ed62ad0ed1ec78f7760ece9ea9"
PUR_LEDGER_PATH = "tests/fixtures/pur_formulation_files_20261019.json"
PUR_LEDGER_SHA256 = "da273be57628bc69a55ae3cacaea4c07370fa56cd2dec6678f062b551acf7dba"


def baseline_bytes(path):
    return subprocess.run(["git", "show", BASE_COMMIT + ":" + path], cwd=ROOT,
                          check=True, capture_output=True, timeout=30).stdout


def digest(raw):
    return sha256(raw).hexdigest()


class ReplayCodeCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = (ROOT / compatibility.ENGINE_PATH).read_bytes()
        cls.previous = baseline_bytes(compatibility.ENGINE_PATH)
        cls.ledger_raw = (ROOT / compatibility.LEDGER_PATH).read_bytes()
        cls.ledger = json.loads(cls.ledger_raw)

    def test_helper_ledger_and_two_engine_images_are_exactly_pinned(self):
        self.assertEqual(digest((ROOT / "tests/material_append_replay_compat.py").read_bytes()),
                         HELPER_SHA256)
        self.assertEqual(digest(self.ledger_raw), LEDGER_SHA256)
        self.assertEqual(digest(self.current), CURRENT_SHA256)
        self.assertEqual(digest(self.previous), PREVIOUS_SHA256)
        self.assertEqual(compatibility.BASE_COMMIT, BASE_COMMIT)
        self.assertEqual(compatibility.LEDGER_SHA256, LEDGER_SHA256)
        self.assertEqual(compatibility.CURRENT_SHA256, CURRENT_SHA256)
        self.assertEqual(compatibility.PREVIOUS_SHA256, PREVIOUS_SHA256)
        self.assertEqual(set(self.ledger), {"schema_version", "baseline_commit", "updates"})
        self.assertEqual(self.ledger["baseline_commit"], BASE_COMMIT)
        self.assertEqual(set(self.ledger["updates"]), {compatibility.ENGINE_PATH})
        self.assertEqual(len(self.ledger["updates"][compatibility.ENGINE_PATH]["edits"]), 1)

    def test_exact_new_and_old_bytes_round_trip_without_authorizing_other_paths(self):
        entry = self.ledger["updates"][compatibility.ENGINE_PATH]
        self.assertEqual(history.recover_file(self.current, entry), self.previous)
        self.assertEqual(compatibility.project_engine_bytes(self.current), self.previous)
        self.assertEqual(compatibility.project_engine_bytes(self.previous), self.previous)
        self.assertEqual(history.project_file_chain(compatibility.ENGINE_PATH, self.current, []),
                         self.previous)
        with patch.object(compatibility, "project_engine_bytes") as bridge:
            for path in ("README.md", "unrelated.py", "../tests/material_append_history.py",
                         "tests/material_append_history.py "):
                with self.subTest(path=path):
                    self.assertEqual(history.project_file_chain(path, self.current, []), self.current)
            bridge.assert_not_called()

    def test_unknown_or_changed_bytes_pass_unchanged_to_old_rejection(self):
        old = history.load_frozen(ROOT, PUR_LEDGER_PATH, PUR_LEDGER_SHA256)
        entry = old["updates"][compatibility.ENGINE_PATH]
        for raw in (self.current + b"!", self.current[:-1], b"!" + self.current[1:],
                    b"", b"unknown engine bytes", b"{}"):
            with self.subTest(digest=digest(raw)):
                with patch.object(history, "load_frozen", side_effect=AssertionError("must stay lazy")):
                    self.assertIs(compatibility.project_engine_bytes(raw), raw)
                    self.assertIs(history.project_file_chain(compatibility.ENGINE_PATH, raw, []), raw)
                with self.assertRaises(AssertionError):
                    history.recover_file(raw, entry)
        for raw in (None, bytearray(self.current), [], "engine"):
            with self.subTest(raw_type=type(raw).__name__), self.assertRaises(AssertionError):
                compatibility.project_engine_bytes(raw)

    def test_later_matching_calls_reread_root_and_reject_changed_ledger_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / compatibility.LEDGER_PATH
            path.parent.mkdir(parents=True)
            path.write_bytes(self.ledger_raw)
            with patch.object(compatibility, "ROOT", root):
                self.assertEqual(compatibility.project_engine_bytes(self.current), self.previous)
                path.write_bytes(self.ledger_raw + b" ")
                with self.assertRaisesRegex(AssertionError, "Unreviewed append-history ledger"):
                    compatibility.project_engine_bytes(self.current)
                path.write_bytes(self.ledger_raw)
                self.assertEqual(compatibility.project_engine_bytes(self.current), self.previous)
                path.unlink()
                with self.assertRaises(FileNotFoundError):
                    compatibility.project_engine_bytes(self.current)
                self.assertEqual(compatibility.project_engine_bytes(b"unknown"), b"unknown")
        with patch.object(compatibility, "ROOT", ROOT / "nonexistent-replay-root"):
            with self.assertRaises(FileNotFoundError):
                compatibility.project_engine_bytes(self.current)

    def test_ledger_shape_image_edit_and_duplicate_key_mutations_fail_closed(self):
        mutations = []
        for name in ("baseline", "extra_path", "current_sha", "previous_sha",
                     "offset", "before", "after"):
            value = deepcopy(self.ledger)
            entry = value["updates"][compatibility.ENGINE_PATH]
            if name == "baseline":
                value["baseline_commit"] = "0" * 40
            elif name == "extra_path":
                value["updates"]["unreviewed.py"] = deepcopy(entry)
            elif name == "current_sha":
                entry["sha256"] = "0" * 64
            elif name == "previous_sha":
                entry["previous_sha256"] = "0" * 64
            elif name == "offset":
                entry["edits"][0]["offset"] += 1
            else:
                entry["edits"][0][name] += "!"
            mutations.append((name, history.encoded(value)))
        mutations.append(("duplicate_key", self.ledger_raw.replace(
            b'"schema_version": 1,', b'"schema_version": 1, "schema_version": 1,', 1)))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / compatibility.LEDGER_PATH
            path.parent.mkdir(parents=True)
            for name, raw in mutations:
                path.write_bytes(raw)
                with self.subTest(mutation=name), patch.object(compatibility, "ROOT", root):
                    with self.assertRaises(AssertionError):
                        compatibility.project_engine_bytes(self.current)
                    # Exercise the inner shape/round-trip checks independently
                    # of the unchanged real frozen-ledger digest gate.
                    with patch.object(compatibility, "LEDGER_SHA256", digest(raw)):
                        with self.assertRaises(AssertionError):
                            compatibility.project_engine_bytes(self.current)

    def test_invalid_input_and_wrong_chain_fail_before_the_bridge(self):
        entry = deepcopy(self.ledger["updates"][compatibility.ENGINE_PATH])
        chain = [{"updates": {compatibility.ENGINE_PATH: entry}},
                 {"updates": {compatibility.ENGINE_PATH: deepcopy(entry)}}]
        with patch.object(compatibility, "project_engine_bytes") as bridge:
            with self.assertRaisesRegex(AssertionError, "not adjacent or ordered"):
                history.project_file_chain(compatibility.ENGINE_PATH, self.current, chain)
            for filename, raw, ledgers in ((None, self.current, []),
                                          (compatibility.ENGINE_PATH, bytearray(self.current), []),
                                          (compatibility.ENGINE_PATH, self.current, iter([]))):
                with self.subTest(filename=filename, raw_type=type(raw).__name__):
                    with self.assertRaisesRegex(AssertionError, "Invalid finite file projection input"):
                        history.project_file_chain(filename, raw, ledgers)
            bridge.assert_not_called()

    def test_unchanged_pur_fixture_and_assertion_pins_accept_only_exact_recovery(self):
        raw = (ROOT / PUR_LEDGER_PATH).read_bytes()
        self.assertEqual(raw, baseline_bytes(PUR_LEDGER_PATH))
        self.assertEqual(digest(raw), PUR_LEDGER_SHA256)
        old = history.load_frozen(ROOT, PUR_LEDGER_PATH, PUR_LEDGER_SHA256)
        entry = old["updates"][compatibility.ENGINE_PATH]
        self.assertEqual(entry["sha256"], PREVIOUS_SHA256)
        self.assertEqual(entry["previous_sha256"],
                         "486056844e48131a38258db48275ae6c5a0c3f6a3721e54e4fb60798f0e8c4cb")
        recovered = history.project_file_chain(compatibility.ENGINE_PATH, self.current, [old])
        self.assertEqual(digest(recovered), entry["previous_sha256"])
        self.assertEqual(recovered, history.recover_file(self.previous, entry))
        for name in ("tests/test_pur_formulation_preservation.py",
                     "tests/pur_formulation_preservation.py", "tests/material_append_successors.py"):
            with self.subTest(path=name):
                if name == "tests/material_append_successors.py":
                    # This new test's original 196995 snapshot remains separately
                    # pinned; the latest integration binds the newer registry.
                    previous = baseline_bytes(name)
                    self.assertEqual(digest(previous), "0602463777d7d61f2ae5de3d81c61e350db7301b5e65f298648d67a7eb63fb99")
                    latest = subprocess.run(
                        ["git", "show", "826333c73a420b7d254c469d9f6f65155983cde1:" + name],
                        cwd=ROOT, check=True, capture_output=True, timeout=30).stdout
                    self.assertEqual(digest(latest), "df5250b9d9e7b67bd8ec92cdfbc2d2efce99db5ff1a4dea0631431cbad5d886f")
                    from replay_checkout_history import project_checkout_file
                    from ci_partition_history import project_partition_file
                    self.assertEqual(project_checkout_file(name, project_partition_file(name, (ROOT / name).read_bytes())), latest)
                else:
                    self.assertEqual((ROOT / name).read_bytes(), baseline_bytes(name))


if __name__ == "__main__":
    unittest.main()
