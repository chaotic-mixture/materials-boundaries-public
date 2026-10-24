"""Bounded, test-only old/new replay measurements over the frozen real catalog.

Each selected case runs in a fresh child process, builds its historical image
sequentially, and measures the old engine before the new engine. Input hashing
and image preparation are outside the timed/counted projection. No full catalog
graphs are cached between cases or calls. This is a single observation per case,
not a cold-cache guarantee or an extrapolated speed claim. Inputs must remain
stable within each invocation. This benchmark does not diagnose the earlier
installed smoke timeout and does not run installed smoke or CLI coverage.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import tempfile
from time import perf_counter
from types import ModuleType
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "196995256836db2d8f870ac9a91f664bfdd03e7f"
ENGINE_PATH = "tests/material_append_history.py"
SCRIPT_PATH = "tests/history_replay/benchmark_replay.py"
OLD_ENGINE_SHA256 = "38d9b1768121f84cc5b45d21d8d992b8d62cf6ed62ad0ed1ec78f7760ece9ea9"
FILES = {"materials": "materials.json", "properties": "reference_properties.json",
         "sources": "sources.json"}
LEDGER_NAMES = (
    "tarasov_pna_bpf_data_20261023.json",
    "bruns_borosilicate_data_20261023.json",
    "nylon_followup_data_20261021.json",
    "tough_pla_followup_data_20261021.json",
    "primary_table_growth_8_data_20261021.json",
    "primary_table_growth_7_data_20261020.json",
    "primary_table_growth_6_data_20261020.json",
    "primary_table_growth_5_data_20261020.json",
    "primary_table_growth_4_data_20261019.json",
    "primary_table_growth_3_data_20261019.json",
    "primary_table_growth_2_data_20261019.json",
    "primary_table_growth_data_20261019.json",
    "pur_formulation_data_20261019.json",
    "source_family_growth_data_20261019.json",
)
STAGES = {"current": 0, "after5": 5, "oldest": 14}
CASES = tuple(stage + "-" + name for stage in STAGES for name in FILES)


def digest(raw):
    return sha256(raw).hexdigest()


def git_bytes(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, timeout=30).stdout


def load_engine(raw, label):
    module = ModuleType(label)
    exec(compile(raw, label + ":" + ENGINE_PATH, "exec"), module.__dict__)
    return module


def engines():
    old_raw = git_bytes("show", BASE_COMMIT + ":" + ENGINE_PATH)
    if digest(old_raw) != OLD_ENGINE_SHA256:
        raise AssertionError("The complete old engine differs from its fixed hash")
    new_raw = (ROOT / ENGINE_PATH).read_bytes()
    return (load_engine(old_raw, "frozen_predecessor"),
            load_engine(new_raw, "current_candidate"), digest(new_raw))


def input_inventory(old):
    """Pin every ledger to Git, every packet to its ledger, and all disk tables."""
    manifest, ledgers, packet_paths = {}, [], set()
    for filename in LEDGER_NAMES:
        relative = "tests/fixtures/" + filename
        raw = (ROOT / relative).read_bytes()
        if raw != git_bytes("show", BASE_COMMIT + ":" + relative):
            raise AssertionError("A benchmark ledger differs from the frozen baseline")
        manifest[relative] = digest(raw)
        ledger = json.loads(raw, object_pairs_hook=old.unique_keys)
        ledgers.append(ledger)
        for descriptor in ledger["packets"]:
            path = (ROOT / descriptor["path"]).resolve()
            if not path.is_relative_to((ROOT / "experimental/material-batches").resolve()):
                raise AssertionError("A benchmark packet escapes the reviewed directory")
            packet = path.read_bytes()
            if digest(packet) != descriptor["sha256"]:
                raise AssertionError("A benchmark packet differs from its frozen hash")
            manifest[path.relative_to(ROOT).as_posix()] = digest(packet)
            packet_paths.add(path)
    old._ordered_catalog_ledgers(ledgers)
    if len(ledgers) != 14:
        raise AssertionError("The benchmark requires the exact fourteen-ledger chain")
    for name, filename in FILES.items():
        relative = "materials_boundaries/data/" + filename
        raw = (ROOT / relative).read_bytes()
        manifest[relative] = digest(raw)
        if digest(raw) != ledgers[0]["current_sha256"][name]:
            raise AssertionError("A disk catalog differs from the frozen current image")
    manifest[ENGINE_PATH] = digest((ROOT / ENGINE_PATH).read_bytes())
    manifest[SCRIPT_PATH] = digest((ROOT / SCRIPT_PATH).read_bytes())
    return ledgers, manifest, packet_paths


def check_inputs(manifest):
    after = {name: digest((ROOT / name).read_bytes()) for name in manifest}
    if after != manifest:
        raise AssertionError("Benchmark input bytes changed during execution")
    return after


def prepare_raw(old, ledgers, stage, name):
    if not STAGES[stage]:
        return (ROOT / "materials_boundaries/data" / FILES[name]).read_bytes()
    graph = {key: json.loads((ROOT / "materials_boundaries/data" / filename).read_bytes(),
                             object_pairs_hook=old.unique_keys)
             for key, filename in FILES.items()}
    for ledger in ledgers[:STAGES[stage]]:
        graph = old.recover_catalogs(ROOT, graph, ledger)
    return old.encoded(graph[name])


def safe_error(error):
    # Native errors can embed absolute paths. Report their type/code without
    # leaking machine paths; our assertion messages are fixed, path-free text.
    result = {"type": type(error).__name__}
    if isinstance(error, AssertionError):
        result["message"] = str(error)
    elif isinstance(error, OSError):
        result["errno"] = error.errno
    elif isinstance(error, subprocess.CalledProcessError):
        result["returncode"] = error.returncode
    return result


def measure(module, filename, raw, ledgers, packet_paths):
    counts = {"recover_catalogs": 0, "appended_rows": 0,
              "catalog_read_bytes": 0, "packet_read_bytes": 0, "other_read_bytes": 0}
    original_recover, original_rows = module.recover_catalogs, module.appended_rows
    original_read = Path.read_bytes
    catalog_paths = {(ROOT / "materials_boundaries/data" / name).resolve()
                     for name in FILES.values()}

    def counted_recover(*args, **kwargs):
        counts["recover_catalogs"] += 1
        return original_recover(*args, **kwargs)

    def counted_rows(*args, **kwargs):
        counts["appended_rows"] += 1
        return original_rows(*args, **kwargs)

    def counted_read(path):
        resolved = path.resolve()
        key = ("catalog_read_bytes" if resolved in catalog_paths else
               "packet_read_bytes" if resolved in packet_paths else "other_read_bytes")
        counts[key] += 1
        return original_read(path)

    output, error = None, None
    with ExitStack() as stack:
        stack.enter_context(patch.object(module, "recover_catalogs", counted_recover))
        stack.enter_context(patch.object(module, "appended_rows", counted_rows))
        stack.enter_context(patch.object(Path, "read_bytes", counted_read))
        started = perf_counter()
        try:
            output = module.project_catalog_bytes_chain(ROOT, filename, raw, ledgers)
            if type(output) is not bytes:
                raise AssertionError("A projection did not return bytes")
        except Exception as caught:
            error = safe_error(caught)
        elapsed = perf_counter() - started
    result = {"status": "failed" if error else "passed", "elapsed_seconds": elapsed,
              "counts": counts, "output_sha256": None if output is None else digest(output),
              "output_bytes": None if output is None else len(output)}
    if error:
        result["error"] = error
    return result, output


def save_json(path, value):
    pending = path.with_name(path.name + ".pending")
    pending.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending.replace(path)


def worker(case, output):
    stage, name = case.split("-", 1)
    result = {"case": case, "stage_after_ledgers": STAGES[stage], "table": name,
              "status": "running", "phase": "input_verification"}
    save_json(output, result)
    try:
        old, new, new_hash = engines()
        ledgers, manifest, packet_paths = input_inventory(old)
        if manifest[ENGINE_PATH] != new_hash:
            raise AssertionError("Candidate engine changed during initial verification")
        result["candidate_engine_sha256"] = new_hash
        result["input_sha256_before"] = manifest
        result["phase"] = "historical_image_preparation"
        save_json(output, result)
        started = perf_counter()
        raw = prepare_raw(old, ledgers, stage, name)
        result["preparation_seconds_not_timed_as_projection"] = perf_counter() - started
        result["input_raw_sha256"] = digest(raw)
        result["input_raw_bytes"] = len(raw)
        ledger_bytes = old.encoded(ledgers)
        check_inputs(manifest)
        result["phase"] = "old_projection"
        save_json(output, result)
        result["old"], old_output = measure(old, FILES[name], raw, ledgers, packet_paths)
        check_inputs(manifest)
        if old.encoded(ledgers) != ledger_bytes:
            raise AssertionError("The old projection changed the supplied ledger objects")
        result["phase"] = "new_projection"
        save_json(output, result)
        result["new"], new_output = measure(new, FILES[name], raw, ledgers, packet_paths)
        if old.encoded(ledgers) != ledger_bytes:
            raise AssertionError("The new projection changed the supplied ledger objects")
        result["input_sha256_after"] = check_inputs(manifest)
        result["inputs_unchanged"] = True
        result["byte_equal"] = (result["old"]["status"] == result["new"]["status"] == "passed"
                                and old_output == new_output)
        result["status"] = "passed" if result["byte_equal"] else "failed"
        result["phase"] = "completed"
    except Exception as error:
        result["status"] = "failed"
        result["error"] = safe_error(error)
    save_json(output, result)
    return 0 if result["status"] == "passed" else 1


def run_bounded_worker(command, timeout):
    """Own the launcher and terminate its child tree if its budget expires."""
    options = {"cwd": ROOT, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
    else:
        options["start_new_session"] = True
    outcome = {"timed_out": False, "returncode": None,
               "termination": {"attempted": False}}
    try:
        process = subprocess.Popen(command, **options)
    except Exception as error:
        outcome["launch_error"] = safe_error(error)
        return outcome
    try:
        outcome["returncode"] = process.wait(timeout=timeout)
        return outcome
    except subprocess.TimeoutExpired:
        outcome["timed_out"] = True
    termination = outcome["termination"] = {
        "attempted": False, "task_owned_launcher_pid": process.pid,
        "launcher_exit_confirmed": False, "tree_cleanup_confirmed": False,
    }
    # Only target the process started above, while its owned handle still
    # reports it alive. Never select a PID from a process-name search.
    if process.poll() is not None:
        outcome["returncode"] = process.returncode
        termination["launcher_exit_confirmed"] = True
        termination["status"] = "launcher_exited_before_cleanup; descendant state unconfirmed"
        return outcome
    termination["attempted"] = True
    try:
        if os.name == "nt":
            termination["method"] = "taskkill /PID owned_launcher /T /F"
            stopped = subprocess.run(
                ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            termination["command_returncode"] = stopped.returncode
        else:
            termination["method"] = "SIGKILL to the worker's new process group"
            os.killpg(process.pid, signal.SIGKILL)
            termination["group_signal_sent"] = True
    except Exception as error:
        termination["error"] = safe_error(error)
    try:
        outcome["returncode"] = process.wait(timeout=10)
        termination["launcher_exit_confirmed"] = True
    except subprocess.TimeoutExpired:
        termination["status"] = "launcher still alive after bounded cleanup wait"
        return outcome
    if os.name == "nt":
        termination["tree_cleanup_confirmed"] = termination.get("command_returncode") == 0
    elif termination.get("group_signal_sent"):
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            termination["tree_cleanup_confirmed"] = True
        except OSError as error:
            termination["group_check_error"] = safe_error(error)
    termination["status"] = ("owned tree cleanup confirmed" if termination["tree_cleanup_confirmed"]
                             else "launcher exited; descendant cleanup unconfirmed")
    return outcome


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="+", choices=CASES, default=list(CASES),
                        help="Finite case subset; default: all nine real-catalog cases")
    parser.add_argument("--output", type=Path, help="New JSON report path outside the repository")
    parser.add_argument("--case-timeout-seconds", type=int, default=600,
                        help="Per-case child budget including preparation, old and new (default: 600)")
    parser.add_argument("--total-budget-seconds", type=int, default=1800,
                        help="Total child execution budget (default: 1800)")
    parser.add_argument("--_worker", choices=CASES, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.output is None:
        parser.error("--output is required")
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error("--output must be outside the repository")
    if args._worker:
        return worker(args._worker, output)
    if output.exists():
        parser.error("--output already exists; choose a new evidence path")
    if len(set(args.cases)) != len(args.cases):
        parser.error("--cases must not contain duplicates")
    if not 1 <= args.case_timeout_seconds <= 3600 or not 1 <= args.total_budget_seconds <= 14400:
        parser.error("budgets must be positive and at most 3600 per case / 14400 total")
    if not output.parent.is_dir():
        parser.error("--output parent directory must already exist")
    report = {"schema": "material-history-replay-benchmark/1",
              "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
              "baseline_commit": BASE_COMMIT, "old_engine_sha256": OLD_ENGINE_SHA256,
              "candidate_engine_sha256": digest((ROOT / ENGINE_PATH).read_bytes()),
              "benchmark_script_sha256": digest(Path(__file__).read_bytes()),
              "platform": {"system": platform.system(), "python": platform.python_version(),
                           "implementation": platform.python_implementation()},
              "selected_cases": args.cases, "case_timeout_seconds": args.case_timeout_seconds,
              "total_budget_seconds": args.total_budget_seconds,
              "timeout_cleanup_grace_seconds": 25,
              "scope": "Single observations of test-only projections; no installed smoke or CLI tests",
              "limitations": ["Inputs must remain stable during each invocation.",
                              "Cold OS or filesystem caches are not guaranteed; old always runs first.",
                              "Measured times include counter instrumentation, but exclude image preparation and input hashing.",
                              "No speed claim is extrapolated beyond the selected observations.",
                              "This optimization does not establish the cause of the original installed smoke timeout."],
              "cases": [], "status": "running"}
    started = perf_counter()
    stopped = False
    first_inputs = None
    save_json(output, report)
    with tempfile.TemporaryDirectory(prefix="history-replay-benchmark-", dir=output.parent) as temporary:
        for index, case in enumerate(args.cases):
            remaining = args.total_budget_seconds - (perf_counter() - started)
            if stopped or remaining <= 0:
                report["cases"].append({"case": case, "status": "not_run",
                                        "reason": "earlier failure or total budget exhausted"})
                stopped = True
                continue
            progress = Path(temporary) / (str(index) + ".json")
            command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                       "--_worker", case, "--output", str(progress)]
            execution = run_bounded_worker(command, min(args.case_timeout_seconds, remaining))
            timed_out, returncode = execution["timed_out"], execution["returncode"]
            result = (json.loads(progress.read_text(encoding="utf-8")) if progress.exists()
                      else {"case": case, "status": "failed", "phase": "worker_start"})
            result["worker_returncode"] = returncode
            result["worker_termination"] = execution["termination"]
            if "launch_error" in execution:
                result["worker_launch_error"] = execution["launch_error"]
            if timed_out:
                result["status"] = "timed_out"
            elif returncode != 0:
                result["status"] = "failed"
            if result.get("candidate_engine_sha256") not in (None, report["candidate_engine_sha256"]):
                result["status"] = "failed"
                result["input_error"] = "Candidate engine changed between cases"
            inputs = result.get("input_sha256_before")
            if inputs is not None and inputs[SCRIPT_PATH] != report["benchmark_script_sha256"]:
                result["status"] = "failed"
                result["input_error"] = "Benchmark script changed between cases"
            if first_inputs is None and inputs is not None:
                first_inputs = inputs
            elif inputs is not None and inputs != first_inputs:
                result["status"] = "failed"
                result["input_error"] = "Catalog, packet, ledger or engine inputs changed between cases"
            report["cases"].append(result)
            stopped = result["status"] != "passed"
            if stopped:
                report["status"] = "failed"
            save_json(output, report)
    report["status"] = "passed" if all(item["status"] == "passed" for item in report["cases"]) else "failed"
    try:
        report["inputs_unchanged_through_final_check"] = (first_inputs is not None
                                                         and check_inputs(first_inputs) == first_inputs)
        if not report["inputs_unchanged_through_final_check"]:
            report["status"] = "failed"
    except Exception as error:
        report["status"] = "failed"
        report["final_input_error"] = safe_error(error)
    report["elapsed_seconds_including_preparation_and_checks"] = perf_counter() - started
    save_json(output, report)
    print(json.dumps({"status": report["status"], "cases_passed": sum(
        item["status"] == "passed" for item in report["cases"]), "cases_selected": len(args.cases)}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
