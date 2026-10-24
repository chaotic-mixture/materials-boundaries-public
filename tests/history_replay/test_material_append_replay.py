"""Differential checks for invocation-local historical prefix replay.

The oracle is the complete, hash-pinned predecessor module. Tiny synthetic
packets exercise recovery semantics without claiming new catalog admissions.
Disk inputs are stable during one call; changed inputs are reread on later calls.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tests") not in sys.path:
    sys.path.insert(0, str(ROOT / "tests"))
import material_append_history as current
BASE_COMMIT = "196995256836db2d8f870ac9a91f664bfdd03e7f"
OLD_MODULE_SHA256 = "38d9b1768121f84cc5b45d21d8d992b8d62cf6ed62ad0ed1ec78f7760ece9ea9"


def load_predecessor():
    raw = subprocess.run(
        ["git", "show", BASE_COMMIT + ":tests/material_append_history.py"],
        cwd=ROOT, check=True, capture_output=True, timeout=30,
    ).stdout
    if sha256(raw).hexdigest() != OLD_MODULE_SHA256:
        raise AssertionError("Unexpected differential oracle bytes")
    module = ModuleType("material_append_replay_predecessor")
    exec(compile(raw, BASE_COMMIT + ":tests/material_append_history.py", "exec"), module.__dict__)
    return module


def empty_graph():
    return {"materials": {"identities": [], "grades": [], "records": []},
            "properties": {"records": []}, "sources": {"records": []}}


def write_graph(root, graph):
    directory = root / "materials_boundaries/data"
    directory.mkdir(parents=True, exist_ok=True)
    for name, filename in current.FILES.items():
        (directory / filename).write_bytes(current.encoded(graph[name]))


def build_chain(root, count=4, source_steps=None):
    """Create all five collections, with explicit unchanged-source gaps."""
    source_steps = {1, count} if source_steps is None else set(source_steps)
    graph = empty_graph()
    for collection, (table, field) in current.TABLES.items():
        graph[table][field].append({"id": collection + "-base", "value": "baseline"})
    graphs, ledgers = [deepcopy(graph)], []
    for step in range(1, count + 1):
        before = current.graph_hashes(graph)
        additions = empty_graph()
        identifiers = {}
        for collection, (table, field) in current.TABLES.items():
            rows = [] if collection == "sources" and step not in source_steps else [
                {"id": f"{collection}-{step}-{index}", "value": f"reported-{step}-{index}"}
                for index in range(2)]
            identifiers[collection] = [row["id"] for row in rows]
            additions[table][field] = deepcopy(rows)
            graph[table][field].extend(deepcopy(rows))
        relative = f"experimental/material-batches/synthetic-replay/{step}.json"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        packet = current.encoded({"catalogs": additions})
        path.write_bytes(packet)
        ledgers.append({"baseline_sha256": before, "current_sha256": current.graph_hashes(graph),
                        "packets": [{"path": relative, "sha256": current.digest(packet),
                                     "added_ids": identifiers}]})
        graphs.append(deepcopy(graph))
    write_graph(root, graph)
    return SimpleNamespace(root=root, graphs=graphs, ledgers=list(reversed(ledgers)))


class MaterialAppendReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous = load_predecessor()

    def chain(self, count=4, source_steps=None):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return build_chain(Path(directory.name), count, source_steps)

    def outcome(self, module, case, filename, raw, ledgers=None):
        ledgers = case.ledgers if ledgers is None else ledgers
        snapshot = deepcopy(ledgers)
        try:
            value = module.project_catalog_bytes_chain(case.root, filename, raw, ledgers)
            result = ("ok", value)
        except Exception as error:
            result = ("error", type(error).__name__, str(error))
        self.assertEqual(ledgers, snapshot, "Projection mutated caller-owned ledgers")
        return result

    def compare(self, case, filename, raw, ledgers=None, error=False):
        old = self.outcome(self.previous, case, filename, raw, ledgers)
        new = self.outcome(current, case, filename, raw, ledgers)
        self.assertEqual(new, old)
        if error:
            self.assertEqual(old[0], "error")
        return old

    def test_all_current_and_historical_table_images_match_exactly(self):
        case = self.chain()
        before = deepcopy(case.graphs)
        for stage, graph in enumerate(case.graphs):
            for table, filename in current.FILES.items():
                raw = current.encoded(graph[table])
                with self.subTest(stage=stage, table=table):
                    self.assertEqual(self.compare(case, filename, raw),
                                     ("ok", current.encoded(case.graphs[0][table])))
        self.assertEqual(case.graphs, before)

    def test_unchanged_source_gaps_keep_complete_graph_alignment(self):
        case = self.chain(count=6, source_steps={1, 3, 6})
        for table, filename in current.FILES.items():
            for stage in range(7):
                with self.subTest(table=table, stage=stage):
                    self.assertEqual(self.compare(case, filename, current.encoded(case.graphs[stage][table])),
                                     ("ok", current.encoded(case.graphs[0][table])))
        self.assertEqual(case.graphs[3]["sources"], case.graphs[5]["sources"])

    def test_disk_and_supplied_historical_stages_have_identical_outcomes(self):
        case = self.chain()
        outcomes = set()
        for disk_stage, disk_graph in enumerate(case.graphs):
            write_graph(case.root, disk_graph)
            for raw_stage, graph in enumerate(case.graphs):
                for table, filename in current.FILES.items():
                    with self.subTest(disk_stage=disk_stage, raw_stage=raw_stage, table=table):
                        outcome = self.compare(case, filename, current.encoded(graph[table]))
                        outcomes.add(outcome[0])
        self.assertEqual(outcomes, {"ok", "error"})

    def test_late_first_match_and_unmatched_tail_keep_legacy_behavior(self):
        late = self.chain(count=6, source_steps={1, 3})
        raw = current.encoded(late.graphs[-1]["sources"])
        self.assertEqual(self.compare(late, "sources.json", raw),
                         ("ok", current.encoded(late.graphs[0]["sources"])))
        tail = self.chain(count=6, source_steps={4, 6})
        untouched_packet = tail.root / tail.ledgers[-1]["packets"][0]["path"]
        untouched_packet.write_bytes(b"unreviewed unmatched tail")
        raw = current.encoded(tail.graphs[-1]["sources"])
        # No later table match requests this tail. The projection must not
        # invent extra recovery or read a packet the predecessor never reads.
        self.assertEqual(self.compare(tail, "sources.json", raw),
                         ("ok", current.encoded(tail.graphs[0]["sources"])))

    def test_single_match_keeps_exact_raw_substitution_without_extra_rejection(self):
        case = self.chain(count=1)
        for table, filename in current.FILES.items():
            broken = deepcopy(case.graphs[-1])
            broken[table]["unexpected_root_field"] = True
            write_graph(case.root, broken)
            with self.subTest(table=table):
                self.assertEqual(self.compare(case, filename, current.encoded(case.graphs[-1][table])),
                                 ("ok", current.encoded(case.graphs[0][table])))

    def test_empty_prefix_still_checks_nan_and_duplicate_keys_before_substitution(self):
        case = self.chain(count=1)
        for table, filename in current.FILES.items():
            path = case.root / "materials_boundaries/data" / filename
            for mutation in ("nan", "duplicate"):
                write_graph(case.root, case.graphs[-1])
                if mutation == "nan":
                    broken = deepcopy(case.graphs[-1][table])
                    broken["nonfinite"] = float("nan")
                    path.write_bytes(json.dumps(broken, allow_nan=True).encode())
                else:
                    path.write_bytes(b'{"records": [], "records": []}')
                with self.subTest(table=table, mutation=mutation):
                    self.compare(case, filename, current.encoded(case.graphs[-1][table]), error=True)

    def test_unknown_and_noncanonical_bytes_pass_to_historical_rejection_without_io(self):
        case = self.chain()
        for table, filename in current.FILES.items():
            known = current.encoded(case.graphs[-1][table])
            unknown = (known + b"!", known[:-1], b"{}", b"not JSON",
                       json.dumps(case.graphs[-1][table], separators=(",", ":")).encode())
            for raw in unknown:
                with self.subTest(table=table, tail=raw[-8:]):
                    with patch.object(Path, "read_bytes", side_effect=AssertionError("Unexpected disk read")):
                        result = self.compare(case, filename, raw)
                    self.assertEqual(result, ("ok", raw))
                    # The historical caller still owns rejection of unknown bytes.
                    entry = {"previous_sha256": current.digest(current.encoded(case.graphs[0][table])),
                             "sha256": current.digest(known), "edits": []}
                    for module in (self.previous, current):
                        with self.assertRaisesRegex(AssertionError, "Unreviewed append-history file bytes"):
                            module.recover_file(result[1], entry)

    def test_invalid_arguments_and_empty_chain_preserve_behavior(self):
        case = self.chain()
        raw = current.encoded(case.graphs[-1]["materials"])
        for filename, value in (("unknown.json", raw), (None, raw), ("materials.json", bytearray(raw)),
                                ("materials.json", None), ("materials.json", raw.decode())):
            with self.subTest(filename=filename, value_type=type(value).__name__):
                self.compare(case, filename, value, error=True)
        for invalid in ({}, "chain", None):
            # None normally means the default in this test helper, so call directly.
            old = self.previous.project_catalog_bytes_chain
            new = current.project_catalog_bytes_chain
            for function in (old, new):
                with self.assertRaisesRegex(AssertionError, "explicit finite sequence"):
                    function(case.root, "materials.json", raw, invalid)
        self.assertEqual(self.compare(case, "materials.json", raw, []), ("ok", raw))
        self.assertEqual(self.compare(case, "materials.json", raw, tuple(case.ledgers))[0], "ok")

    def test_wrong_reordered_duplicate_and_partial_chains_fail_equally(self):
        case = self.chain()
        chains = [list(reversed(case.ledgers)), case.ledgers[:1] + case.ledgers[2:],
                  case.ledgers[:1] + case.ledgers, case.ledgers[1:]]
        changed = deepcopy(case.ledgers)
        changed[1]["current_sha256"]["materials"] = "0" * 64
        chains.append(changed)
        for index, ledgers in enumerate(chains):
            with self.subTest(chain=index):
                self.compare(case, "materials.json", current.encoded(case.graphs[-1]["materials"]),
                             ledgers, error=index != 3)
        # Omitting the newest prefix leaves unknown bytes unchanged, not admitted.
        raw = current.encoded(case.graphs[-1]["materials"])
        self.assertEqual(self.compare(case, "materials.json", raw, case.ledgers[1:]), ("ok", raw))

    def test_mutated_missing_duplicate_and_reordered_disk_additions_are_rejected(self):
        case = self.chain()
        for collection, (table, field) in current.TABLES.items():
            for mutation in ("changed", "missing", "duplicate", "reordered"):
                graph = deepcopy(case.graphs[-1])
                rows = graph[table][field]
                if mutation == "changed":
                    rows[-1]["value"] = "unreviewed"
                elif mutation == "missing":
                    rows.pop()
                elif mutation == "duplicate":
                    rows.append(deepcopy(rows[-1]))
                else:
                    rows[-2], rows[-1] = rows[-1], rows[-2]
                write_graph(case.root, graph)
                # A different supplied table cannot replace the corrupted table.
                target = "properties" if table != "properties" else "materials"
                with self.subTest(collection=collection, mutation=mutation):
                    self.compare(case, current.FILES[target], current.encoded(case.graphs[-1][target]), error=True)
        write_graph(case.root, case.graphs[-1])

    def test_valid_raw_must_not_hide_corrupted_disk_table_from_later_prefix(self):
        case = self.chain()
        for table, filename in current.FILES.items():
            broken = deepcopy(case.graphs[-1])
            broken[table]["unexpected_root_field"] = True
            write_graph(case.root, broken)
            with self.subTest(table=table):
                # The first substitution alone repairs this table, but a later
                # prefix must still validate the unmodified disk-derived graph.
                self.compare(case, filename, current.encoded(case.graphs[-1][table]), error=True)
        write_graph(case.root, case.graphs[-1])

    def test_corrupted_disk_metadata_json_and_duplicate_keys_are_rejected(self):
        case = self.chain()
        for table, filename in current.FILES.items():
            path = case.root / "materials_boundaries/data" / filename
            valid = path.read_bytes()
            for bad in (b"{", b'{"records": [], "records": []}'):
                path.write_bytes(bad)
                with self.subTest(table=table, bad=bad):
                    self.compare(case, "materials.json", current.encoded(case.graphs[-1]["materials"]), error=True)
                path.write_bytes(valid)

    def test_packet_bytes_paths_and_collection_inventories_keep_strict_checks(self):
        case = self.chain()
        raw = current.encoded(case.graphs[-1]["materials"])
        descriptor = case.ledgers[0]["packets"][0]
        path = case.root / descriptor["path"]
        valid = path.read_bytes()
        for content in (valid + b" ", valid[:-1], b"{}"):
            path.write_bytes(content)
            self.compare(case, "materials.json", raw, error=True)
        path.write_bytes(valid)
        for mutation in ("outside", "missing", "missing-collection", "duplicate-id", "missing-id",
                         "duplicate-packet", "changed-hash"):
            ledgers = deepcopy(case.ledgers)
            item = ledgers[0]["packets"][0]
            if mutation == "outside":
                item["path"] = "outside.json"
            elif mutation == "missing":
                item["path"] += ".missing"
            elif mutation == "missing-collection":
                del item["added_ids"]["states"]
            elif mutation == "duplicate-id":
                item["added_ids"]["states"].append(item["added_ids"]["states"][0])
            elif mutation == "missing-id":
                item["added_ids"]["states"][0] = "absent"
            elif mutation == "duplicate-packet":
                ledgers[0]["packets"].append(deepcopy(item))
            else:
                item["sha256"] = "0" * 64
            with self.subTest(mutation=mutation):
                self.compare(case, "materials.json", raw, ledgers, error=True)
        duplicate_json = b'{"catalogs": {}, "catalogs": {}}'
        path.write_bytes(duplicate_json)
        ledgers = deepcopy(case.ledgers)
        ledgers[0]["packets"][0]["sha256"] = current.digest(duplicate_json)
        self.compare(case, "materials.json", raw, ledgers, error=True)

    def test_repeated_calls_reread_changed_graph_packet_and_ledger(self):
        case = self.chain()
        raw = current.encoded(case.graphs[-1]["materials"])
        expected = ("ok", current.encoded(case.graphs[0]["materials"]))
        self.assertEqual(self.compare(case, "materials.json", raw), expected)
        broken = deepcopy(case.graphs[-1])
        broken["properties"]["records"][-1]["value"] = "changed between calls"
        write_graph(case.root, broken)
        self.compare(case, "materials.json", raw, error=True)
        write_graph(case.root, case.graphs[-1])
        self.assertEqual(self.compare(case, "materials.json", raw), expected)
        packet = case.root / case.ledgers[0]["packets"][0]["path"]
        before = packet.read_bytes()
        packet.write_bytes(before + b" ")
        self.compare(case, "materials.json", raw, error=True)
        packet.write_bytes(before)
        self.assertEqual(self.compare(case, "materials.json", raw), expected)
        mutated = deepcopy(case.ledgers)
        mutated[-1]["packets"][0]["added_ids"]["sources"].append("unreviewed")
        self.compare(case, "materials.json", raw, mutated, error=True)
        self.assertEqual(self.compare(case, "materials.json", raw), expected)

    def test_alternate_roots_do_not_share_graph_or_packet_state(self):
        good = self.chain()
        bad = self.chain()
        raw = current.encoded(good.graphs[-1]["materials"])
        expected = self.compare(good, "materials.json", raw)
        broken = deepcopy(bad.graphs[-1])
        broken["sources"]["records"][0]["value"] = "wrong root"
        write_graph(bad.root, broken)
        self.compare(bad, "materials.json", raw, error=True)
        self.assertEqual(self.compare(good, "materials.json", raw), expected)

    def test_thirteen_step_counts_preserve_separate_disk_validation(self):
        case = self.chain(count=13, source_steps=range(1, 14))
        raw = current.encoded(case.graphs[-1]["materials"])
        expected = current.encoded(case.graphs[0]["materials"])
        counts = []
        original_read = Path.read_bytes
        for module in (self.previous, current):
            graph_reads = []

            def counted_read(path):
                if path.parent == case.root / "materials_boundaries/data":
                    graph_reads.append(path.name)
                return original_read(path)

            with patch.object(module, "recover_catalogs", wraps=module.recover_catalogs) as recovered:
                with patch.object(Path, "read_bytes", counted_read):
                    self.assertEqual(module.project_catalog_bytes_chain(case.root, "materials.json", raw,
                                                                       case.ledgers), expected)
                counts.append((recovered.call_count, len(graph_reads)))
        # 13 substitutions plus 12 incremental disk-prefix validations are
        # required; retaining the substituted graph would incorrectly use 13.
        self.assertEqual(counts, [(91, 39), (25, 3)])


if __name__ == "__main__":
    unittest.main()
