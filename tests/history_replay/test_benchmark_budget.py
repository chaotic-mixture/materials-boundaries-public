"""Mock-only budget contracts; no process starts, kills or real benchmarks.

Windows and POSIX branches are simulated. These tests do not certify native
POSIX execution or operating-system process-tree cleanup.
"""
from contextlib import ExitStack, contextmanager, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch


SCRIPT = Path(__file__).with_name("benchmark_replay.py")
SPEC = importlib.util.spec_from_file_location("history_replay_benchmark_budget_subject", SCRIPT)
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)
COMMAND = ["mock-python", "mock-worker"]


def timeout():
    return subprocess.TimeoutExpired(COMMAND, 3)


def owned_process(wait_results):
    process = Mock(pid=12345, returncode=None)
    process.wait.side_effect = wait_results
    process.poll.return_value = None
    return process


@contextmanager
def process_mocks(system, process):
    with ExitStack() as stack:
        stack.enter_context(patch.object(benchmark.os, "name", system))
        stack.enter_context(patch.object(benchmark.subprocess, "CREATE_NO_WINDOW", 0x08000000,
                                        create=True))
        stack.enter_context(patch.object(benchmark.signal, "SIGKILL", 9, create=True))
        popen = stack.enter_context(patch.object(benchmark.subprocess, "Popen", return_value=process))
        taskkill = stack.enter_context(patch.object(
            benchmark.subprocess, "run", return_value=SimpleNamespace(returncode=0)))
        killpg = stack.enter_context(patch.object(benchmark.os, "killpg", create=True))
        yield popen, taskkill, killpg


class BenchmarkProcessBudgetTests(unittest.TestCase):
    def test_normal_exit_never_attempts_cleanup_on_either_simulated_platform(self):
        for system in ("nt", "posix"):
            for code in (0, 7):
                with self.subTest(system=system, returncode=code):
                    process = owned_process([code])
                    with process_mocks(system, process) as (popen, taskkill, killpg):
                        result = benchmark.run_bounded_worker(COMMAND, 3)
                        self.assertEqual(result, {"timed_out": False, "returncode": code,
                                                  "termination": {"attempted": False}})
                        process.wait.assert_called_once_with(timeout=3)
                        process.poll.assert_not_called()
                        taskkill.assert_not_called()
                        killpg.assert_not_called()
                        self.assertEqual(popen.call_args.args, (COMMAND,))
                        self.assertNotIn("shell", popen.call_args.kwargs)
                        if system == "nt":
                            self.assertEqual(popen.call_args.kwargs["creationflags"], 0x08000000)
                        else:
                            self.assertIs(popen.call_args.kwargs["start_new_session"], True)

    def test_failed_launch_is_not_a_success_or_cleanup_target(self):
        process = owned_process([])
        with process_mocks("nt", process) as (popen, taskkill, killpg):
            popen.side_effect = OSError(5, "mock private path must not be reported")
            result = benchmark.run_bounded_worker(COMMAND, 3)
            self.assertIsNone(result["returncode"])
            self.assertEqual(result["launch_error"], {"type": "OSError", "errno": 5})
            self.assertFalse(result["termination"]["attempted"])
            process.wait.assert_not_called()
            taskkill.assert_not_called()
            killpg.assert_not_called()

    def test_windows_timeout_targets_only_the_live_owned_launcher_tree(self):
        process = owned_process([timeout(), 1])
        with process_mocks("nt", process) as (_, taskkill, killpg):
            result = benchmark.run_bounded_worker(COMMAND, 3)
            self.assertTrue(result["timed_out"])
            self.assertEqual(result["returncode"], 1)
            self.assertEqual(process.wait.call_args_list, [call(timeout=3), call(timeout=10)])
            process.poll.assert_called_once_with()
            taskkill.assert_called_once_with(
                ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15,
                creationflags=0x08000000)
            self.assertTrue(result["termination"]["launcher_exit_confirmed"])
            self.assertTrue(result["termination"]["tree_cleanup_confirmed"])
            self.assertEqual(result["termination"]["task_owned_launcher_pid"], process.pid)
            killpg.assert_not_called()

    def test_exited_launcher_is_never_retargeted_and_descendants_remain_unconfirmed(self):
        for system in ("nt", "posix"):
            with self.subTest(system=system):
                process = owned_process([timeout()])
                process.poll.return_value = process.returncode = 0
                with process_mocks(system, process) as (_, taskkill, killpg):
                    result = benchmark.run_bounded_worker(COMMAND, 3)
                    self.assertTrue(result["timed_out"])
                    self.assertFalse(result["termination"]["attempted"])
                    self.assertTrue(result["termination"]["launcher_exit_confirmed"])
                    self.assertFalse(result["termination"]["tree_cleanup_confirmed"])
                    taskkill.assert_not_called()
                    killpg.assert_not_called()

    def test_windows_cleanup_failure_or_timeout_does_not_confirm_tree_cleanup(self):
        for error in (None, subprocess.TimeoutExpired(["mock-taskkill"], 15), OSError(5, "denied")):
            with self.subTest(error=type(error).__name__):
                process = owned_process([timeout(), 1])
                with process_mocks("nt", process) as (_, taskkill, killpg):
                    if error is None:
                        taskkill.return_value.returncode = 128
                    else:
                        taskkill.side_effect = error
                    result = benchmark.run_bounded_worker(COMMAND, 3)
                    self.assertTrue(result["timed_out"])
                    self.assertTrue(result["termination"]["launcher_exit_confirmed"])
                    self.assertFalse(result["termination"]["tree_cleanup_confirmed"])
                    self.assertEqual(taskkill.call_count, 1)
                    killpg.assert_not_called()
                    if error is not None:
                        self.assertEqual(result["termination"]["error"]["type"], type(error).__name__)

    def test_cleanup_success_without_launcher_exit_still_remains_unconfirmed(self):
        process = owned_process([timeout(), timeout()])
        with process_mocks("nt", process) as (_, taskkill, _):
            result = benchmark.run_bounded_worker(COMMAND, 3)
            self.assertTrue(result["timed_out"])
            self.assertIsNone(result["returncode"])
            self.assertEqual(result["termination"]["command_returncode"], 0)
            self.assertFalse(result["termination"]["launcher_exit_confirmed"])
            self.assertFalse(result["termination"]["tree_cleanup_confirmed"])
            self.assertEqual(taskkill.call_count, 1)
            self.assertEqual(process.wait.call_args_list, [call(timeout=3), call(timeout=10)])

    def test_simulated_posix_uses_owned_new_group_and_requires_its_absence(self):
        process = owned_process([timeout(), -9])
        with process_mocks("posix", process) as (popen, taskkill, killpg):
            killpg.side_effect = [None, ProcessLookupError()]
            result = benchmark.run_bounded_worker(COMMAND, 3)
            self.assertIs(popen.call_args.kwargs["start_new_session"], True)
            self.assertEqual(killpg.call_args_list,
                             [call(process.pid, benchmark.signal.SIGKILL), call(process.pid, 0)])
            self.assertTrue(result["termination"]["launcher_exit_confirmed"])
            self.assertTrue(result["termination"]["tree_cleanup_confirmed"])
            self.assertTrue(result["timed_out"])
            taskkill.assert_not_called()

    def test_simulated_posix_signal_errors_existing_groups_and_check_errors_stay_unconfirmed(self):
        scenarios = ([PermissionError(13, "mock denial")],
                     [None, None], [None, PermissionError(13, "mock denial")])
        for effects in scenarios:
            with self.subTest(effects=len(effects), first=type(effects[0]).__name__):
                process = owned_process([timeout(), -9])
                with process_mocks("posix", process) as (_, taskkill, killpg):
                    killpg.side_effect = effects
                    result = benchmark.run_bounded_worker(COMMAND, 3)
                    self.assertTrue(result["termination"]["launcher_exit_confirmed"])
                    self.assertFalse(result["termination"]["tree_cleanup_confirmed"])
                    self.assertTrue(result["timed_out"])
                    taskkill.assert_not_called()


class BenchmarkScheduleBudgetTests(unittest.TestCase):
    def run_schedule(self, executions, *, ticks=None):
        """Write only tiny mock progress files; prohibit actual process launch."""
        outcomes = iter(executions)
        with tempfile.TemporaryDirectory(prefix="mock-history-budget-") as directory:
            output = Path(directory) / "report.json"
            inputs = {benchmark.ENGINE_PATH: benchmark.digest((benchmark.ROOT / benchmark.ENGINE_PATH).read_bytes()),
                      benchmark.SCRIPT_PATH: benchmark.digest(SCRIPT.read_bytes())}

            def fake_worker(command, budget):
                execution = next(outcomes)
                # Even an apparently passed progress file must not override a
                # timeout, launch failure or nonzero worker exit status.
                benchmark.save_json(Path(command[-1]), {
                    "case": command[-3], "status": "passed", "phase": "completed",
                    "candidate_engine_sha256": inputs[benchmark.ENGINE_PATH],
                    "input_sha256_before": inputs, "input_sha256_after": inputs,
                    "inputs_unchanged": True, "byte_equal": True})
                return execution

            with ExitStack() as stack:
                run = stack.enter_context(patch.object(benchmark, "run_bounded_worker", side_effect=fake_worker))
                stack.enter_context(patch.object(benchmark, "check_inputs", side_effect=lambda value: dict(value)))
                stack.enter_context(patch.object(benchmark.platform, "system", return_value="MockOS"))
                stack.enter_context(patch.object(benchmark.platform, "python_version", return_value="3.mock"))
                stack.enter_context(patch.object(benchmark.platform, "python_implementation", return_value="MockPython"))
                popen = stack.enter_context(patch.object(benchmark.subprocess, "Popen",
                                                         side_effect=AssertionError("Real process launch forbidden")))
                execute = stack.enter_context(patch.object(benchmark.subprocess, "run",
                                                           side_effect=AssertionError("Real subprocess forbidden")))
                killpg = stack.enter_context(patch.object(benchmark.os, "killpg", create=True,
                                                          side_effect=AssertionError("Real signal forbidden")))
                if ticks is not None:
                    stack.enter_context(patch.object(benchmark, "perf_counter", side_effect=ticks))
                stdout = stack.enter_context(redirect_stdout(io.StringIO()))
                code = benchmark.main(["--cases", "current-materials", "current-sources", "--output", str(output),
                                       "--case-timeout-seconds", "3", "--total-budget-seconds", "10"])
                report = json.loads(output.read_text(encoding="utf-8"))
                summary = json.loads(stdout.getvalue())
                popen.assert_not_called()
                execute.assert_not_called()
                killpg.assert_not_called()
                return code, report, summary, run.call_args_list

    def test_timeout_cannot_be_reported_as_passed_or_start_a_later_case(self):
        for confirmed in (False, True):
            execution = {"timed_out": True, "returncode": 0,
                         "termination": {"attempted": True, "tree_cleanup_confirmed": confirmed}}
            with self.subTest(cleanup_confirmed=confirmed):
                code, report, summary, calls = self.run_schedule([execution])
                self.assertEqual(code, 1)
                self.assertEqual(report["status"], "failed")
                self.assertEqual([case["status"] for case in report["cases"]], ["timed_out", "not_run"])
                self.assertEqual(summary["cases_passed"], 0)
                self.assertEqual(len(calls), 1)
                self.assertEqual(report["cases"][0]["worker_termination"], execution["termination"])

    def test_nonzero_exit_and_launch_failure_stop_following_cases(self):
        for execution in ({"timed_out": False, "returncode": 7, "termination": {"attempted": False}},
                          {"timed_out": False, "returncode": None, "termination": {"attempted": False},
                           "launch_error": {"type": "OSError", "errno": 5}}):
            with self.subTest(returncode=execution["returncode"]):
                code, report, summary, calls = self.run_schedule([execution])
                self.assertEqual(code, 1)
                self.assertEqual([case["status"] for case in report["cases"]], ["failed", "not_run"])
                self.assertEqual(summary["cases_passed"], 0)
                self.assertEqual(len(calls), 1)
                if "launch_error" in execution:
                    self.assertEqual(report["cases"][0]["worker_launch_error"], execution["launch_error"])

    def test_exhausted_total_budget_never_starts_a_worker(self):
        code, report, summary, calls = self.run_schedule([], ticks=[0, 11, 12, 13])
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        self.assertEqual([case["status"] for case in report["cases"]], ["not_run", "not_run"])
        self.assertEqual(summary["cases_passed"], 0)

    def test_budget_exhaustion_after_one_pass_preserves_partial_success(self):
        success = {"timed_out": False, "returncode": 0, "termination": {"attempted": False}}
        code, report, summary, calls = self.run_schedule([success], ticks=[0, 0, 11, 12])
        self.assertEqual(code, 1)
        self.assertEqual([case["status"] for case in report["cases"]], ["passed", "not_run"])
        self.assertEqual(summary["cases_passed"], 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[1], 3)


if __name__ == "__main__":
    unittest.main()
