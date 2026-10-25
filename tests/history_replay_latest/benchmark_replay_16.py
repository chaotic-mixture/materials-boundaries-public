"""Pinned sixteen-ledger adapter for the unchanged bounded replay benchmark.

The original fourteen-ledger script and evidence stay immutable. This adapter
uses its process budgets, cleanup, counters, byte comparisons, and receipts;
only the finite baseline, inventory and engine gates are specialized. Inputs
must be stable within an invocation. No atomic concurrent-edit guarantee or
cross-call graph/packet cache is introduced.
"""
from hashlib import sha256
import json
from pathlib import Path
from types import ModuleType
import sys
import tempfile

TESTS = Path(__file__).resolve().parents[1]
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
from curaua_history import checkpoint_bytes, checkpoint_catalogs, CATALOG_PATHS

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = "tests/history_replay_latest/benchmark_replay_16.py"
CONFIG_PATH = "tests/fixtures/material_append_replay_16_20261024.json"
CONFIG_SHA256 = "a6c7e6ac420f68eb6cf226af8ff2fd9cc1a2e2dcf031e0b9fc449d9a65fbd08c"
BASE_COMMIT = "826333c73a420b7d254c469d9f6f65155983cde1"


def digest(raw):
    return sha256(raw).hexdigest()


def unique_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise AssertionError("Duplicate sixteen-ledger configuration key")
        value[key] = item
    return value


def load_config(root=ROOT):
    raw = (root / CONFIG_PATH).read_bytes()
    if digest(raw) != CONFIG_SHA256:
        raise AssertionError("Unreviewed sixteen-ledger configuration")
    config = json.loads(raw, object_pairs_hook=unique_keys)
    if (config["schema_version"] != 1 or config["baseline_commit"] != BASE_COMMIT
            or len(config["ledgers"]) != 16
            or len({entry["path"] for entry in config["ledgers"]}) != 16
            or config["stages"] != {"current": 0, "after5": 5, "oldest": 16}):
        raise AssertionError("Unexpected finite sixteen-ledger configuration")
    return config


def build_runner():
    config = load_config()
    shared_raw = (ROOT / config["shared_benchmark_path"]).read_bytes()
    if digest(shared_raw) != config["shared_benchmark_sha256"]:
        raise AssertionError("The shared bounded benchmark changed")
    runner = ModuleType("pinned_sixteen_ledger_benchmark")
    runner.__file__ = str(ROOT / config["shared_benchmark_path"])
    exec(compile(shared_raw, runner.__file__, "exec"), runner.__dict__)
    # The unchanged launcher must invoke this adapter in each fresh process.
    runner.__file__ = str(ROOT / SCRIPT_PATH)
    runner.ROOT = ROOT
    runner.BASE_COMMIT = BASE_COMMIT
    runner.SCRIPT_PATH = SCRIPT_PATH
    runner.OLD_ENGINE_SHA256 = config["old_engine_sha256"]
    runner.LEDGER_NAMES = tuple(Path(entry["path"]).name for entry in config["ledgers"])
    runner.STAGES = dict(config["stages"])
    runner.CASES = tuple(stage + "-" + name for stage in runner.STAGES for name in runner.FILES)
    original_engines = runner.engines

    def engines():
        fresh = load_config()
        candidate = (ROOT / runner.ENGINE_PATH).read_bytes()
        if digest(candidate) != fresh["candidate_engine_sha256"]:
            raise AssertionError("The exact reviewed candidate engine changed")
        return original_engines()

    def inventory(old):
        fresh = load_config()
        manifest, ledgers, packets = {}, [], set()
        for entry in fresh["ledgers"]:
            relative = entry["path"]
            raw = (ROOT / relative).read_bytes()
            if (digest(raw) != entry["sha256"]
                    or raw != runner.git_bytes("show", BASE_COMMIT + ":" + relative)):
                raise AssertionError("A sixteen-ledger input differs from its frozen baseline")
            manifest[relative] = digest(raw)
            ledger = json.loads(raw, object_pairs_hook=old.unique_keys)
            ledgers.append(ledger)
            for descriptor in ledger["packets"]:
                path = (ROOT / descriptor["path"]).resolve()
                if not path.is_relative_to((ROOT / "experimental/material-batches").resolve()):
                    raise AssertionError("A benchmark packet escapes the reviewed directory")
                raw_packet = path.read_bytes()
                if digest(raw_packet) != descriptor["sha256"]:
                    raise AssertionError("A benchmark packet differs from its frozen hash")
                manifest[path.relative_to(ROOT).as_posix()] = digest(raw_packet)
                packets.add(path)
        old._ordered_catalog_ledgers(ledgers)
        for table, filename in runner.FILES.items():
            relative = "materials_boundaries/data/" + filename
            raw = checkpoint_bytes(relative, (ROOT / relative).read_bytes())
            if digest(raw) != ledgers[0]["current_sha256"][table]:
                raise AssertionError("A disk catalog differs from the frozen Tian image")
            manifest[relative] = digest(raw)
        for path in (runner.ENGINE_PATH, SCRIPT_PATH, CONFIG_PATH, fresh["shared_benchmark_path"]):
            manifest[path] = digest((ROOT / path).read_bytes())
        if manifest[runner.ENGINE_PATH] != fresh["candidate_engine_sha256"]:
            raise AssertionError("The candidate engine changed during inventory verification")
        if manifest[fresh["shared_benchmark_path"]] != fresh["shared_benchmark_sha256"]:
            raise AssertionError("The shared bounded benchmark changed during verification")
        if manifest[CONFIG_PATH] != CONFIG_SHA256:
            raise AssertionError("The sixteen-ledger configuration changed during verification")
        return ledgers, manifest, packets

    original_measure = runner.measure

    def check_inputs(manifest):
        after = {name: digest(checkpoint_bytes(name, (ROOT / name).read_bytes()))
                 if name in CATALOG_PATHS.values() else digest((ROOT / name).read_bytes())
                 for name in manifest}
        if after != manifest:
            raise AssertionError("Benchmark input bytes changed during execution")
        return after

    def prepare_raw(old, ledgers, stage, name):
        graph = checkpoint_catalogs()
        for ledger in ledgers[:runner.STAGES[stage]]:
            graph = old.recover_catalogs(ROOT, graph, ledger)
        return old.encoded(graph[name])

    def measure(module, filename, raw, ledgers, packet_paths):
        # Materialize the exact Tian image per measurement, outside projection
        # timing. The old engine and original counters run against real files.
        # This retains the sixteen-layer experiment; it is not a new timing
        # claim for the seventeen-layer Curaua catalog.
        graph = checkpoint_catalogs()
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory)
            for table, relative in CATALOG_PATHS.items():
                target = checkpoint / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(module.encoded(graph[table]))
            copied = set()
            for source in packet_paths:
                target = checkpoint / source.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
                copied.add(target.resolve())
            original_root = runner.ROOT
            try:
                runner.ROOT = checkpoint
                result, output = original_measure(module, filename, raw, ledgers, copied)
            finally:
                runner.ROOT = original_root
        if checkpoint_catalogs() != graph:
            raise AssertionError("Benchmark input bytes changed during execution")
        result["curaua_checkpoint_preparation_excluded_from_projection_timing"] = True
        return result, output

    runner.engines = engines
    runner.input_inventory = inventory
    runner.check_inputs = check_inputs
    runner.prepare_raw = prepare_raw
    runner.measure = measure
    return runner


RUNNER = build_runner()


if __name__ == "__main__":
    raise SystemExit(RUNNER.main())
