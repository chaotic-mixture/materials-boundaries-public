"""Explicit-input, no-write and real-terminal regressions for composite intake."""
import io
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from materials_boundaries import evaluate, validate_instance, ValidationError
from materials_boundaries._composite_intake_labels import CONDITION_REASONS, LABELS
from materials_boundaries.composite_intake import (
    IntakeCancelled, blank_composite_instance, interactive_composite_instance,
    original_demo_instance,
)
from materials_boundaries.engine import EXPECTED

try:
    import pty
except ImportError:
    pty = None

ROOT = Path(__file__).resolve().parents[1]


class Terminal(io.StringIO):
    def __init__(self, text="", interrupt_at=None):
        super().__init__(text)
        self.read_count = 0
        self.interrupt_at = interrupt_at

    def isatty(self):
        return True

    def readline(self, *args):
        self.read_count += 1
        if self.read_count == self.interrupt_at:
            raise KeyboardInterrupt
        return super().readline(*args)


def answers():
    return ["my-case", "1", "phase_a", "1", "0.25", "12 GPa", "6 GPa",
            "phase_b", "1", "0.75", "36 GPa", "18 GPa"] + ["1"] * 7 + ["", "", "/save"]


def run_intake(lines, lang="en", **kwargs):
    output = Terminal()
    value = interactive_composite_instance(
        lang, Terminal("\n".join(lines) + "\n", **kwargs), output)
    return value, output.getvalue()


class CompositeIntakeTests(unittest.TestCase):
    def test_blank_is_valid_unknown_and_fresh(self):
        value = blank_composite_instance()
        validate_instance(value)
        self.assertEqual(len(value["phases"]), 2)
        self.assertEqual(len(set(p["id"] for p in value["phases"])), 2)
        self.assertEqual(value["provenance"]["kind"], "unspecified")
        self.assertEqual(value["conditions"], dict.fromkeys(EXPECTED))
        self.assertTrue(all(p[k] is None for p in value["phases"]
                            for k in ("volume_fraction", "bulk_modulus", "shear_modulus")))
        self.assertTrue(all(r["applicability"] == "unknown" for r in evaluate(value)["evaluations"]))
        value["conditions"]["dimension"] = 3
        value["phases"][0]["volume_fraction"] = 1
        self.assertIsNone(blank_composite_instance()["conditions"]["dimension"])
        self.assertIsNone(blank_composite_instance()["phases"][0]["volume_fraction"])

    def test_original_fixture_is_fictitious_valid_and_fresh(self):
        value = original_demo_instance()
        validate_instance(value)
        self.assertEqual(value["id"], "original-composite-workflow-case")
        self.assertEqual(value["provenance"], {
            "kind": "synthetic", "note": "Original workflow acceptance fixture; no actual material, measured data, or literature parameters."})
        self.assertEqual([(p["volume_fraction"], p["bulk_modulus"]["value"], p["shear_modulus"]["value"])
                          for p in value["phases"]], [(0.25, 12, 6), (0.75, 36, 18)])
        self.assertTrue(all(r["applicability"] == "satisfied" for r in evaluate(value)["evaluations"]))
        value["phases"][0]["bulk_modulus"]["value"] = 999
        self.assertEqual(original_demo_instance()["phases"][0]["bulk_modulus"]["value"], 12)

    def test_all_locales_have_complete_labels_reasons_and_caveats(self):
        for lang in ("en", "zh", "ja", "de"):
            with self.subTest(lang=lang):
                self.assertEqual(set(LABELS[lang]), set(LABELS["en"]))
                self.assertEqual(set(CONDITION_REASONS[lang]), set(EXPECTED))
                self.assertTrue(all(isinstance(v, str) and v for v in LABELS[lang].values()))
                value, output = run_intake(answers(), lang)
                self.assertEqual(value, run_intake(answers())[0])
                self.assertIn(LABELS[lang]["notice"], output)
                self.assertIn(LABELS[lang]["import_guidance"], output)
                self.assertIn(LABELS[lang]["condition_basis"], output)
                for reason in CONDITION_REASONS[lang].values():
                    self.assertIn(reason, output)

    def test_non_tty_rejected_before_reading_input(self):
        for input_stream, output_stream in (
            (io.StringIO("/save\n"), Terminal()),
            (Terminal("/save\n"), io.StringIO()),
            (io.StringIO(), io.StringIO()),
        ):
            with self.subTest(input=input_stream.isatty(), output=output_stream.isatty()):
                with self.assertRaises(ValidationError):
                    interactive_composite_instance(input_stream=input_stream, output_stream=output_stream)
                self.assertEqual(input_stream.tell(), 0)
        with patch("sys.stdin", io.StringIO()), patch("sys.stdout", io.StringIO()):
            with self.assertRaises(ValidationError):
                interactive_composite_instance()

    def test_unsupported_language_rejected(self):
        for lang in ("fr", "", None, []):
            with self.subTest(lang=lang), self.assertRaises(ValidationError):
                interactive_composite_instance(lang, Terminal(), Terminal())

    def test_blank_observations_remain_unknown_without_defaults(self):
        data = ["case", "1", "a", "", "", "", "b", "", "", ""] + [""] * 7 + ["", "", "/save"]
        value, output = run_intake(data)
        self.assertEqual(value["conditions"], dict.fromkeys(EXPECTED))
        for phase in value["phases"]:
            self.assertIsNone(phase["volume_fraction"])
            self.assertIsNone(phase["bulk_modulus"])
            self.assertIsNone(phase["shear_modulus"])
        self.assertIn('"effective_symmetry": null', output)
        self.assertNotIn("note", value["provenance"])

    def test_mandatory_ids_and_origin_have_no_default(self):
        data = answers()
        data[:2] = ["", "my-case", "", "1"]
        value, output = run_intake(data)
        self.assertEqual(value["id"], "my-case")
        self.assertEqual(value["provenance"]["kind"], "synthetic")
        self.assertIn(LABELS["en"]["required"], output)
        self.assertIn(LABELS["en"]["choice_required"], output)

    def test_user_data_requires_explicit_origin_never_promotes_citations(self):
        for option, kind in (("1", "measured"), ("2", "unspecified")):
            data = answers()
            data[1:2] = ["2", "", option]
            data[-3] = "unknown_paper_source"
            value, output = run_intake(data)
            self.assertEqual(value["provenance"]["kind"], kind)
            self.assertEqual(value["provenance"]["source_ids"], ["unknown_paper_source"])
            self.assertNotIn("model_evidence", value["provenance"])
            self.assertIn(LABELS["en"]["origin_warning"], output)
            self.assertIn(LABELS["en"]["choice_required"], output)

    def test_missing_other_fraction_never_complemented_including_pure_phase(self):
        for first in ("0.25", "1"):
            data = answers()
            data[4] = first
            data[9] = ""
            value, _ = run_intake(data)
            self.assertIsNone(value["phases"][1]["volume_fraction"])
            self.assertTrue(all(row["applicability"] == "unknown" for row in evaluate(value)["evaluations"]))

    def test_mass_rejected_with_no_conversion(self):
        data = answers()
        data[3:5] = ["mass", "", ]
        value, output = run_intake(data)
        self.assertIsNone(value["phases"][0]["volume_fraction"])
        self.assertEqual(value["phases"][1]["volume_fraction"], 0.75)
        self.assertIn(LABELS["en"]["mass_unsupported"], output)
        self.assertNotIn("mass_fraction", json.dumps(value))

    def test_unique_ids_reprompt_and_raw_text_preserved(self):
        data = answers()
        data[7:8] = ["phase_a", "phase_b"]
        data[0] = '../<script>"案例</script>\x1b[31m'
        data[-2] = "  Original 日本語 note </script> & quotes ' \"  "
        value, output = run_intake(data)
        self.assertEqual(value["id"], data[0])
        self.assertEqual(value["provenance"]["note"], data[-2])
        self.assertIn(LABELS["en"]["duplicate_id"], output)
        self.assertNotIn("\x1b", output)  # Review JSON escapes executable terminal controls.

    def test_source_ids_preserved_and_empty_ids_rejected(self):
        data = answers()
        data[-3:-2] = ["a,,b", "user_unknown, javascript:unresolved, 引用"]
        value, output = run_intake(data)
        self.assertEqual(value["provenance"]["source_ids"], ["user_unknown", "javascript:unresolved", "引用"])
        self.assertIn(LABELS["en"]["sources_invalid"], output)

    def test_quantities_require_units_and_reject_nonfinite_and_underflow(self):
        invalid = ["12", "12 gpa", "NaN GPa", "Infinity GPa", "1e309 GPa", "1e-400 GPa", "true Pa", "[12] GPa",
                   "[" * 2000 + "12" + "]" * 2000 + " GPa", "9" * 5000 + " Pa"]
        data = answers()
        data[5:6] = invalid + ["12 GPa"]
        value, output = run_intake(data)
        self.assertEqual(value["phases"][0]["bulk_modulus"], {"value": 12, "unit": "GPa"})
        self.assertIn(LABELS["en"]["number_invalid"], output)
        self.assertIn(LABELS["en"]["quantity_invalid"], output)

    def test_known_unsupported_moduli_preserved_for_engine(self):
        for text, number in (("0 MPa", 0), ("-2 Pa", -2)):
            data = answers(); data[5] = text
            value, _ = run_intake(data)
            self.assertEqual(value["phases"][0]["bulk_modulus"]["value"], number)
            self.assertTrue(all(r["applicability"] == "violated" for r in evaluate(value)["evaluations"]))

    def test_large_integers_and_tiny_positive_values_not_rounded_away(self):
        data = answers()
        first, second = 10**110, 10**110 + 3
        data[5] = f"{first} Pa"; data[10] = f"{second} Pa"
        data[6] = "9 Pa"; data[11] = "4 Pa"
        value, output = run_intake(data)
        self.assertIsInstance(value["phases"][0]["bulk_modulus"]["value"], int)
        self.assertEqual(value["phases"][1]["bulk_modulus"]["value"], second)
        self.assertIn(str(second), output)
        data = answers(); data[4] = "1e-200"; data[9] = "1"
        value, _ = run_intake(data)
        self.assertEqual(value["phases"][0]["volume_fraction"], 1e-200)
        self.assertNotEqual(value["phases"][0]["volume_fraction"], 0)

    def test_all_seven_known_other_conditions_preserved(self):
        data = answers()
        others = ["2", "anisotropic", "anisotropic", "finite_strain", "plastic", "dynamic", "slipping"]
        data[12:19] = [item for other in others for item in ("2", other)]
        value, _ = run_intake(data)
        self.assertEqual(value["conditions"], dict(zip(EXPECTED, [2] + others[1:])))
        self.assertTrue(all(r["applicability"] == "violated" for r in evaluate(value)["evaluations"]))

    def test_other_dimension_requires_positive_integer_and_other_value(self):
        data = answers()
        data[12:13] = ["2", "0", "3.5", "3", "2"]
        value, output = run_intake(data)
        self.assertEqual(value["conditions"]["dimension"], 2)
        self.assertIn(LABELS["en"]["dimension_invalid"], output)
        self.assertIn(LABELS["en"]["different_required"], output)

    def test_review_rejects_invalid_total_until_explicit_edits(self):
        for second, key in (("0.8", "fraction_exceed"), ("0.2", "fraction_sum")):
            data = answers(); data[9] = second
            data[-1:] = ["/save", "/edit 8", "1", "0.75", "/save"]
            value, output = run_intake(data)
            self.assertEqual(value["phases"][1]["volume_fraction"], 0.75)
            self.assertIn(LABELS["en"][key], output)
            self.assertIn(LABELS["en"]["cannot_save"], output)

    def test_review_requires_save_and_supports_edit_menu(self):
        data = answers()
        data[-1:] = ["", "yes", "/edit", "0", "/edit", "1", "edited-case", "/save"]
        value, output = run_intake(data)
        self.assertEqual(value["id"], "edited-case")
        self.assertIn(LABELS["en"]["edit_invalid"], output)
        self.assertGreater(output.count(LABELS["en"]["review_notice"]), 1)

    def test_back_from_field_and_review_preserves_then_explicitly_replaces(self):
        data = answers()
        data[1:2] = ["/back", "changed-case", "1"]
        data[-1:] = ["/back", "new provenance note", "/save"]
        value, output = run_intake(data)
        self.assertEqual(value["id"], "changed-case")
        self.assertEqual(value["provenance"]["note"], "new provenance note")
        self.assertIn(LABELS["en"]["stored"], output)

    def test_back_in_multistep_fields_and_aborted_edit(self):
        # Back within provenance, fraction and known-other-condition subprompts;
        # the final aborted provenance edit preserves the earlier synthetic choice.
        data = ["case", "2", "/back", "1", "a", "1", "/back", "1", "0.25", "12 GPa", "6 GPa",
                "b", "1", "0.75", "36 GPa", "18 GPa", "2", "/back", "1"] + ["1"] * 6 + ["", "", "/edit 2", "2", "/back", "/back", "/save"]
        value, _ = run_intake(data)
        self.assertEqual(value["provenance"]["kind"], "synthetic")
        self.assertEqual(value["conditions"], EXPECTED)
        self.assertEqual(value["phases"][0]["volume_fraction"], 0.25)

    def test_editing_unknown_does_not_reuse_previous_value(self):
        data = answers()
        data[-1:] = ["/edit 5", "", "/edit 13", "", "/save"]
        value, _ = run_intake(data)
        self.assertIsNone(value["phases"][0]["bulk_modulus"])
        self.assertIsNone(value["conditions"]["effective_symmetry"])

    def test_early_save_cannot_skip_questions(self):
        data = answers(); data[:0] = ["/save", "/edit 5"]
        value, _ = run_intake(data)
        self.assertEqual(value["id"], "my-case")
        self.assertEqual(value["conditions"], EXPECTED)

    def test_cancel_eof_interrupt_at_every_prompt_and_during_edits(self):
        branch = answers()
        branch[1:2] = ["2", "1"]
        branch[13:20] = [item for other in ["2", "anisotropic", "anisotropic", "finite_strain", "plastic", "dynamic", "slipping"]
                         for item in ["2", other]]
        branch[-1:] = ["/edit 2", "2", "1", "/edit 4", "1", "0.25", "/edit", "19", "note", "/save"]
        # Verify this covers a genuine valid trajectory before perturbing it.
        run_intake(branch)
        for sequence in (answers(), branch):
            for index in range(len(sequence)):
                for mode in ("cancel", "eof", "interrupt"):
                    with self.subTest(index=index, mode=mode, branch=sequence is branch):
                        if mode == "cancel":
                            stream = Terminal("\n".join(sequence[:index] + ["/cancel"]) + "\n")
                        elif mode == "eof":
                            stream = Terminal("\n".join(sequence[:index]) + ("\n" if index else ""))
                        else:
                            stream = Terminal("\n".join(sequence) + "\n", interrupt_at=index + 1)
                        with self.assertRaises(IntakeCancelled), patch("builtins.open", side_effect=AssertionError("wizard must not open files")):
                            interactive_composite_instance(input_stream=stream, output_stream=Terminal())


@unittest.skipUnless(pty is not None and os.name == "posix", "requires POSIX pseudo-terminal")
class CompositeIntakePTYTests(unittest.TestCase):
    def start_cli(self, destination):
        master, slave = pty.openpty()
        process = subprocess.Popen(
            [sys.executable, "-m", "materials_boundaries", "composite", "init", "--interactive", "--output", str(destination)],
            stdin=slave, stdout=slave, stderr=slave, cwd=ROOT, start_new_session=True,
        )
        os.close(slave)
        return process, master

    def drain(self, process, master, *, until=None, timeout=10):
        deadline = time.monotonic() + timeout
        data = bytearray()
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.1)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                data.extend(chunk)
                if until and until.encode() in data:
                    return data.decode("utf-8", errors="replace")
            elif process.poll() is not None:
                break
        if until and until.encode() not in data:
            self.fail(f"Expected terminal prompt {until!r}; received {bytes(data)!r}")
        return data.decode("utf-8", errors="replace")

    def stop(self, process, master):
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        os.close(master)

    def test_real_terminal_cancel_and_sigint_leave_no_file(self):
        for mode in ("cancel", "sigint"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                destination = Path(folder) / "case.json"
                process, master = self.start_cli(destination)
                try:
                    self.drain(process, master, until="Case ID (required)")
                    if mode == "cancel":
                        os.write(master, b"/cancel\n")
                    else:
                        os.kill(process.pid, signal.SIGINT)
                    output = self.drain(process, master)
                    self.assertEqual(process.wait(timeout=5), 130, output)
                    self.assertFalse(destination.exists())
                    self.assertEqual(list(Path(folder).iterdir()), [])
                finally:
                    self.stop(process, master)

    def test_real_terminal_back_edit_and_confirm_save(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "case.json"
            process, master = self.start_cli(destination)
            try:
                self.drain(process, master, until="Case ID (required)")
                lines = answers()
                lines[1:2] = ["/back", "revisited-case", "1"]
                lines[-1:] = ["/edit 1", "final-reviewed-case", "/save"]
                os.write(master, ("\n".join(lines) + "\n").encode())
                output = self.drain(process, master)
                self.assertEqual(process.wait(timeout=5), 0, output)
                value = json.loads(destination.read_text(encoding="utf-8"))
                validate_instance(value)
                self.assertEqual(value["id"], "final-reviewed-case")
                self.assertEqual(value["conditions"], EXPECTED)
                self.assertEqual(list(Path(folder).iterdir()), [destination])
            finally:
                self.stop(process, master)

    def test_cli_redirected_input_is_rejected_without_file(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "case.json"
            result = subprocess.run(
                [sys.executable, "-m", "materials_boundaries", "composite", "init", "--interactive", "--output", str(destination)],
                input="\n".join(answers()) + "\n", text=True, capture_output=True, cwd=ROOT,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("TTY", result.stderr)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
