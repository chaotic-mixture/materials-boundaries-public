"""Finite latest-baseline gates and sixteen-layer synthetic differential checks.

No real-catalog timing is performed by this module. Real measurements are
separate bounded invocations of benchmark_replay_16.py. Stable inputs within
one invocation remain a requirement; no concurrency atomicity is claimed.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_replay_16 as adapter


def load_synthetic_helpers():
    config = adapter.load_config()
    path = ROOT / config["original_synthetic_path"]
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != config["original_synthetic_sha256"]:
        raise AssertionError("The original differential helpers changed")
    module = ModuleType("pinned_original_synthetic_helpers")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


synthetic = load_synthetic_helpers()


class SixteenLayerConfigurationTests(unittest.TestCase):
    def test_exact_configuration_ledgers_engine_and_shared_runner_pins(self):
        config = adapter.load_config()
        self.assertEqual(adapter.CONFIG_SHA256,
                         "a6c7e6ac420f68eb6cf226af8ff2fd9cc1a2e2dcf031e0b9fc449d9a65fbd08c")
        self.assertEqual(config["baseline_commit"], "826333c73a420b7d254c469d9f6f65155983cde1")
        self.assertEqual(len(config["ledgers"]), 16)
        self.assertEqual([Path(item["path"]).name for item in config["ledgers"][:2]],
                         ["tian_nano_ti_data_20261024.json", "kapoor_phosphate_data_20261024.json"])
        old, new, new_hash = adapter.RUNNER.engines()
        self.assertEqual(new_hash, config["candidate_engine_sha256"])
        self.assertEqual(old.FILES, new.FILES)
        ledgers = []
        for entry in config["ledgers"]:
            with self.subTest(path=entry["path"]):
                raw = (ROOT / entry["path"]).read_bytes()
                self.assertEqual(sha256(raw).hexdigest(), entry["sha256"])
                self.assertEqual(raw, adapter.RUNNER.git_bytes("show", adapter.BASE_COMMIT + ":" + entry["path"]))
                ledgers.append(json.loads(raw, object_pairs_hook=old.unique_keys))
        old._ordered_catalog_ledgers(ledgers)
        self.assertEqual(adapter.RUNNER.STAGES, {"current": 0, "after5": 5, "oldest": 16})
        self.assertEqual(len(adapter.RUNNER.CASES), 9)
        self.assertEqual(adapter.RUNNER.SCRIPT_PATH, adapter.SCRIPT_PATH)
        self.assertEqual(Path(adapter.RUNNER.__file__), ROOT / adapter.SCRIPT_PATH)
        # Reuse executable budget and comparison functions without editing the
        # original source or accidentally launching the fourteen-layer script.
        self.assertEqual(adapter.RUNNER.main.__code__.co_filename,
                         str(ROOT / config["shared_benchmark_path"]))
        self.assertEqual(adapter.RUNNER.run_bounded_worker.__code__.co_filename,
                         str(ROOT / config["shared_benchmark_path"]))

    def test_configuration_rereads_and_rejects_byte_shape_and_order_drift(self):
        raw = (ROOT / adapter.CONFIG_PATH).read_bytes()
        config = json.loads(raw)
        changes = [raw + b" ", raw[:-1], b"{}"]
        for name in ("reverse", "duplicate", "missing", "baseline", "oldest"):
            value = deepcopy(config)
            if name == "reverse": value["ledgers"].reverse()
            elif name == "duplicate": value["ledgers"].append(deepcopy(value["ledgers"][0]))
            elif name == "missing": value["ledgers"].pop()
            elif name == "baseline": value["baseline_commit"] = "0" * 40
            else: value["stages"]["oldest"] = 14
            changes.append((json.dumps(value, indent=2) + "\n").encode())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / adapter.CONFIG_PATH
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
            self.assertEqual(adapter.load_config(root), config)
            for changed in changes:
                with self.subTest(digest=sha256(changed).hexdigest()):
                    path.write_bytes(changed)
                    with self.assertRaisesRegex(AssertionError, "Unreviewed sixteen-ledger configuration"):
                        adapter.load_config(root)
            path.write_bytes(raw)
            self.assertEqual(adapter.load_config(root), config)
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                adapter.load_config(root)

    def test_shared_runner_and_candidate_engine_drift_fail_before_measurement(self):
        config = adapter.load_config()
        original_read = Path.read_bytes
        for target, message in ((config["shared_benchmark_path"], "shared bounded benchmark changed"),
                                ("tests/material_append_history.py", "exact reviewed candidate engine changed")):
            def changed_read(path):
                raw = original_read(path)
                return raw + b"!" if path == ROOT / target else raw
            with self.subTest(target=target), patch.object(Path, "read_bytes", changed_read):
                with self.assertRaisesRegex(AssertionError, message):
                    if target == config["shared_benchmark_path"]:
                        adapter.build_runner()
                    else:
                        adapter.RUNNER.engines()

    def test_inventory_binds_all_sixteen_inputs_and_rereads_drift(self):
        old, _, _ = adapter.RUNNER.engines()
        config = adapter.load_config()
        ledgers, manifest, packets = adapter.RUNNER.input_inventory(old)
        self.assertEqual(len(ledgers), 16)
        self.assertEqual(len(packets), 16)
        self.assertEqual(manifest[adapter.CONFIG_PATH], adapter.CONFIG_SHA256)
        self.assertEqual(manifest[config["shared_benchmark_path"]], config["shared_benchmark_sha256"])
        for table, filename in adapter.RUNNER.FILES.items():
            self.assertEqual(manifest["materials_boundaries/data/" + filename], ledgers[0]["current_sha256"][table])
        self.assertEqual(adapter.RUNNER.check_inputs(manifest), manifest)
        original_read = Path.read_bytes
        targets = (config["ledgers"][0]["path"], ledgers[0]["packets"][0]["path"],
                   "materials_boundaries/data/sources.json")
        for target in targets:
            def changed_read(path):
                raw = original_read(path)
                return raw + b" " if path == ROOT / target else raw
            with self.subTest(target=target), patch.object(Path, "read_bytes", changed_read):
                with self.assertRaises(AssertionError):
                    adapter.RUNNER.input_inventory(old)
                with self.assertRaisesRegex(AssertionError, "input bytes changed"):
                    adapter.RUNNER.check_inputs(manifest)
        self.assertEqual(adapter.RUNNER.input_inventory(old)[1], manifest)


class SixteenLayerDifferentialTests(unittest.TestCase):
    # Only helper methods are reused; imported old test classes are never
    # exposed to discovery as another copy of the old test inventory.
    outcome = synthetic.MaterialAppendReplayTests.outcome
    compare = synthetic.MaterialAppendReplayTests.compare

    @classmethod
    def setUpClass(cls):
        cls.previous, _, _ = adapter.RUNNER.engines()

    def chain(self, count=16, source_steps=None):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        if source_steps is None:
            source_steps = {1, 4, 8, 15, 16}
        return synthetic.build_chain(Path(directory.name), count, source_steps)

    def test_all_seventeen_images_and_source_gaps_match_exactly(self):
        case = self.chain()
        self.assertEqual(len(case.ledgers), 16)
        before = deepcopy(case.graphs)
        for stage, graph in enumerate(case.graphs):
            for table, filename in synthetic.current.FILES.items():
                with self.subTest(stage=stage, table=table):
                    self.assertEqual(self.compare(case, filename, synthetic.current.encoded(graph[table])),
                                     ("ok", synthetic.current.encoded(case.graphs[0][table])))
        self.assertEqual(case.graphs, before)
        self.assertEqual(case.graphs[8]["sources"], case.graphs[14]["sources"])

    def test_selected_disk_and_supplied_historical_crossings_preserve_outcomes(self):
        case = self.chain()
        outcomes = set()
        for disk_stage in (0, 8, 16):
            synthetic.write_graph(case.root, case.graphs[disk_stage])
            for raw_stage in (0, 7, 16):
                for table, filename in synthetic.current.FILES.items():
                    with self.subTest(disk_stage=disk_stage, raw_stage=raw_stage, table=table):
                        outcome = self.compare(case, filename, synthetic.current.encoded(case.graphs[raw_stage][table]))
                        outcomes.add(outcome[0])
        self.assertEqual(outcomes, {"ok", "error"})

    def test_mutated_duplicate_missing_reordered_additions_and_disk_corruption(self):
        synthetic.MaterialAppendReplayTests.test_mutated_missing_duplicate_and_reordered_disk_additions_are_rejected(self)
        synthetic.MaterialAppendReplayTests.test_valid_raw_must_not_hide_corrupted_disk_table_from_later_prefix(self)
        synthetic.MaterialAppendReplayTests.test_corrupted_disk_metadata_json_and_duplicate_keys_are_rejected(self)

    def test_unknown_bytes_and_wrong_chains_keep_old_rejection(self):
        synthetic.MaterialAppendReplayTests.test_unknown_and_noncanonical_bytes_pass_to_historical_rejection_without_io(self)
        synthetic.MaterialAppendReplayTests.test_wrong_reordered_duplicate_and_partial_chains_fail_equally(self)
        synthetic.MaterialAppendReplayTests.test_invalid_arguments_and_empty_chain_preserve_behavior(self)

    def test_later_calls_and_other_roots_reread_graph_packet_and_ledger(self):
        synthetic.MaterialAppendReplayTests.test_repeated_calls_reread_changed_graph_packet_and_ledger(self)
        synthetic.MaterialAppendReplayTests.test_alternate_roots_do_not_share_graph_or_packet_state(self)
        synthetic.MaterialAppendReplayTests.test_packet_bytes_paths_and_collection_inventories_keep_strict_checks(self)

    def test_sixteen_step_operation_counts_retain_separate_disk_validation(self):
        case = self.chain(source_steps=range(1, 17))
        raw = synthetic.current.encoded(case.graphs[-1]["materials"])
        expected = synthetic.current.encoded(case.graphs[0]["materials"])
        counts = []
        original_read = Path.read_bytes
        for module in (self.previous, synthetic.current):
            reads = []
            def counted_read(path):
                if path.parent == case.root / "materials_boundaries/data":
                    reads.append(path.name)
                return original_read(path)
            with patch.object(module, "recover_catalogs", wraps=module.recover_catalogs) as recovered:
                with patch.object(Path, "read_bytes", counted_read):
                    self.assertEqual(module.project_catalog_bytes_chain(case.root, "materials.json", raw, case.ledgers), expected)
                counts.append((recovered.call_count, len(reads)))
        self.assertEqual(counts, [(136, 48), (31, 3)])


if __name__ == "__main__":
    unittest.main()
