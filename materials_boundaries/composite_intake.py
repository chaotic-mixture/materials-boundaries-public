"""Explicit, local-only preparation of the unchanged two-phase instance contract.

The interactive wizard never writes a file, evaluates a case, or retrieves data.
It returns a valid draft only after an explicit review confirmation. The caller
owns local output preflight and atomic saving. ``/back`` revisits the preceding
field; within a two-question field it revisits that field's first question.
``/edit N`` edits one complete field from the review. Previously entered values
are displayed on revisiting, but never used as silent defaults: a blank
observation replaces that observation with unknown.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
import json
import math
import re
import sys
from typing import Any, TextIO

from ._composite_intake_labels import CONDITION_REASONS, LABELS
from .engine import EXPECTED
from .validation import FRACTION_TOLERANCE, UNITS, ValidationError, validate_instance

__all__ = [
    "IntakeCancelled", "blank_composite_instance", "original_demo_instance",
    "interactive_composite_instance",
]

_JSON_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")


class IntakeCancelled(Exception):
    """The draft was discarded, explicitly or through EOF/interrupt; no write occurred."""


class _Back(Exception):
    pass


class _BadInput(Exception):
    """Carries a translated-label key, not an English-only parser error."""


def blank_composite_instance() -> dict:
    """Return a fresh valid template with no assumed observations or provenance."""
    return {
        "schema_version": "1.0.0",
        "id": "untitled-composite-case",
        "conditions": {field: None for field in EXPECTED},
        "phases": [
            {"id": phase_id, "volume_fraction": None,
             "bulk_modulus": None, "shear_modulus": None}
            for phase_id in ("phase_1", "phase_2")
        ],
        "provenance": {"kind": "unspecified", "source_ids": []},
    }


def original_demo_instance() -> dict:
    """Return the original fictitious acceptance case, never real material data."""
    return {
        "schema_version": "1.0.0",
        "id": "original-composite-workflow-case",
        "conditions": dict(EXPECTED),
        "phases": [
            {"id": "phase_a", "volume_fraction": 0.25,
             "bulk_modulus": {"value": 12, "unit": "GPa"},
             "shear_modulus": {"value": 6, "unit": "GPa"}},
            {"id": "phase_b", "volume_fraction": 0.75,
             "bulk_modulus": {"value": 36, "unit": "GPa"},
             "shear_modulus": {"value": 18, "unit": "GPa"}},
        ],
        "provenance": {
            "kind": "synthetic",
            "note": "Original workflow acceptance fixture; no actual material, measured data, or literature parameters.",
        },
    }


def _unknown(text: str) -> bool:
    return text.strip().casefold() in {"", "unknown", "null", "?", "未知", "不明", "unbekannt"}


def _number(text: str) -> int | float:
    """Use JSON numeric semantics without float-coercing integer lexemes."""
    raw = text.strip()
    # Reject non-numeric JSON before parsing it. In particular, a deeply nested
    # array must not turn a simple invalid terminal answer into RecursionError.
    if not _JSON_NUMBER.fullmatch(raw):
        raise _BadInput("number_invalid")
    try:
        value = json.loads(raw)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError
        if not math.isfinite(value):
            raise ValueError
        if value == 0 and Decimal(raw) != 0:
            raise ValueError
    except (ValueError, OverflowError, ArithmeticError) as exc:
        raise _BadInput("number_invalid") from exc
    return value


@dataclass(frozen=True)
class _Field:
    label: str
    path: tuple
    kind: str
    phase: int | None = None


def _fields() -> list[_Field]:
    fields = [
        _Field("case_id", ("id",), "id"),
        _Field("origin", ("provenance", "kind"), "origin"),
    ]
    for index in range(2):
        base = ("phases", index)
        fields.extend([
            _Field("phase_id", base + ("id",), "id", index),
            _Field("fraction_value", base + ("volume_fraction",), "fraction", index),
            _Field("bulk", base + ("bulk_modulus",), "quantity", index),
            _Field("shear", base + ("shear_modulus",), "quantity", index),
        ])
    fields.extend(_Field(key, ("conditions", key), "condition") for key in EXPECTED)
    fields.extend([
        _Field("sources", ("provenance", "source_ids"), "sources"),
        _Field("note", ("provenance", "note"), "note"),
    ])
    return fields


class _Wizard:
    def __init__(self, lang: str, input_stream: TextIO, output_stream: TextIO):
        self.lang = lang
        self.labels = LABELS[lang]
        self.input = input_stream
        self.output = output_stream
        self.draft = blank_composite_instance()
        self.fields = _fields()
        # Template IDs are placeholders, not user answers. Unanswered fields
        # cannot be bypassed using an early review/save command.
        self.answered: set[int] = set()

    def say(self, text: str) -> None:
        self.output.write(text + "\n")
        self.output.flush()

    def label(self, key: str, **values: Any) -> str:
        return self.labels[key].format(**values)

    def ask(self, prompt: str, *, review: bool = False) -> str:
        while True:
            self.say(prompt)
            self.output.write("> ")
            self.output.flush()
            line = self.input.readline()
            if line == "":
                raise IntakeCancelled(self.labels["cancelled"])
            text = line.rstrip("\r\n")
            command = text.strip().casefold()
            if command in {"/cancel", "cancel"}:
                raise IntakeCancelled(self.labels["cancelled"])
            if command in {"/back", "back"}:
                raise _Back
            if not review and (command in {"/save", "save", "/edit", "edit"}
                               or command.startswith(("/edit ", "edit "))):
                self.say(self.labels["navigation"])
                continue
            return text

    def value(self, field: _Field) -> Any:
        at: Any = self.draft
        for key in field.path[:-1]:
            at = at[key]
        return at.get(field.path[-1])

    def put(self, field: _Field, value: Any) -> None:
        at: Any = self.draft
        for key in field.path[:-1]:
            at = at[key]
        if field.kind == "note" and value is None:
            at.pop(field.path[-1], None)
        else:
            at[field.path[-1]] = value

    def field_label(self, field: _Field) -> str:
        if field.kind == "condition":
            return self.label("condition", field=field.label, expected=EXPECTED[field.label])
        return self.label(field.label, phase=(field.phase + 1) if field.phase is not None else "")

    def choice(self, prompt: str, choices: dict[str, Any], *, unknown: bool = False) -> Any:
        while True:
            text = self.ask(prompt).strip().casefold()
            if unknown and _unknown(text):
                return None
            if text in choices:
                return choices[text]
            self.say(self.labels["choice_invalid" if text or unknown else "choice_required"])

    def origin(self) -> str:
        self.say(self.labels["origin_warning"])
        while True:
            choice = self.choice(self.labels["origin"], {
                "1": "synthetic", "hypothetical": "synthetic", "synthetic": "synthetic",
                "2": "user", "user": "user",
            })
            if choice == "synthetic":
                return choice
            try:
                return self.choice(self.labels["user_origin"], {
                    "1": "measured", "measured": "measured",
                    "2": "unspecified", "unspecified": "unspecified",
                })
            except _Back:
                continue

    def fraction(self, field: _Field) -> int | float | None:
        while True:
            basis = self.choice(self.label("basis", phase=field.phase + 1), {
                "1": "volume", "volume": "volume", "2": "mass", "mass": "mass",
                "3": None,
            }, unknown=True)
            if basis is None:
                return None
            if basis == "mass":
                self.say(self.labels["mass_unsupported"])
                continue
            try:
                while True:
                    raw = self.ask(self.field_label(field))
                    if _unknown(raw):
                        return None
                    try:
                        number = _number(raw)
                        if not 0 <= number <= 1:
                            raise _BadInput("fraction_range")
                        return number
                    except _BadInput as exc:
                        self.say(self.labels[str(exc)])
            except _Back:
                continue

    def condition(self, field: _Field) -> Any:
        self.say(CONDITION_REASONS[self.lang][field.label])
        while True:
            choice = self.choice(self.field_label(field), {
                "1": "supported", "supported": "supported",
                "2": "other", "other": "other", "3": None,
            }, unknown=True)
            if choice is None:
                return None
            if choice == "supported":
                return EXPECTED[field.label]
            try:
                while True:
                    raw = self.ask(self.label("other_condition", field=field.label))
                    if _unknown(raw):
                        return None
                    try:
                        value: Any = raw
                        if field.label == "dimension":
                            value = _number(raw)
                            if value <= 0 or value != int(value):
                                raise _BadInput("dimension_invalid")
                            value = int(value)
                        if value == EXPECTED[field.label]:
                            raise _BadInput("different_required")
                        return value
                    except _BadInput as exc:
                        self.say(self.labels[str(exc)])
            except _Back:
                continue

    def collect(self, index: int) -> None:
        field = self.fields[index]
        self.say(f"\n{self.labels['field']} {index + 1}/{len(self.fields)}")
        if index in self.answered:
            self.say(self.labels["stored"] + ": " + json.dumps(self.value(field), ensure_ascii=False))
        if field.kind == "origin":
            value = self.origin()
        elif field.kind == "fraction":
            value = self.fraction(field)
        elif field.kind == "condition":
            value = self.condition(field)
        else:
            while True:
                raw = self.ask(self.field_label(field))
                try:
                    value = self.parse(field, raw)
                    break
                except _BadInput as exc:
                    self.say(self.labels[str(exc)])
        # A multi-question field commits only once all its questions complete.
        self.put(field, value)
        self.answered.add(index)

    def parse(self, field: _Field, raw: str) -> Any:
        if field.kind == "id":
            if not raw.strip():
                raise _BadInput("required")
            if field.phase is not None:
                other = 1 - field.phase
                other_id_index = 2 + other * 4
                if other_id_index in self.answered and raw == self.draft["phases"][other]["id"]:
                    raise _BadInput("duplicate_id")
            return raw
        if field.kind == "quantity":
            if _unknown(raw):
                return None
            parts = raw.split()
            if len(parts) != 2 or parts[1] not in UNITS:
                raise _BadInput("quantity_invalid")
            return {"value": _number(parts[0]), "unit": parts[1]}
        if field.kind == "sources":
            if not raw.strip():
                return []
            source_ids = [part.strip() for part in raw.split(",")]
            if any(not part for part in source_ids):
                raise _BadInput("sources_invalid")
            return source_ids
        if field.kind == "note":
            return raw if raw.strip() else None
        raise AssertionError("unsupported wizard field")

    def validation_error(self) -> str | None:
        # Translate the known cross-field failures; parsers have already checked
        # local field types. Still use the unchanged validator as the final gate.
        fractions = [phase["volume_fraction"] for phase in self.draft["phases"]]
        with localcontext(Context(prec=80)):
            total = sum((Decimal(str(value)) for value in fractions if value is not None), Decimal(0))
            if total > 1 + FRACTION_TOLERANCE:
                return self.labels["fraction_exceed"]
            if all(value is not None for value in fractions) and abs(total - 1) > FRACTION_TOLERANCE:
                return self.labels["fraction_sum"]
        try:
            validate_instance(self.draft)
        except ValidationError:
            return self.labels["review_invalid"]
        return None

    def edit_index(self, raw: str) -> int | None:
        try:
            if not raw.isascii() or not raw.isdecimal():
                raise ValueError
            value = int(raw)
        except ValueError:
            self.say(self.labels["edit_invalid"])
            return None
        if not 1 <= value <= len(self.fields):
            self.say(self.labels["edit_invalid"])
            return None
        return value - 1

    def review(self) -> tuple[str, int | None]:
        self.say("\n" + self.labels["review"])
        self.say(self.labels["review_notice"])
        self.say(self.labels["condition_basis"])
        for index, field in enumerate(self.fields):
            self.say(f"{index + 1}. {self.field_label(field)}")
            self.say("   " + self.labels["stored"] + ": " + json.dumps(self.value(field), ensure_ascii=False))
        self.say(json.dumps(self.draft, indent=2, ensure_ascii=False, allow_nan=False))
        error = self.validation_error()
        if error:
            self.say(error)
        while True:
            try:
                raw = self.ask(self.labels["review_action"], review=True).strip().casefold()
            except _Back:
                return "back", len(self.fields) - 1
            if raw in {"/save", "save"}:
                if error:
                    self.say(self.labels["cannot_save"])
                    continue
                return "save", None
            if raw in {"/edit", "edit"}:
                try:
                    raw = "/edit " + self.ask(self.labels["edit_prompt"]).strip()
                except _Back:
                    continue
            if raw.startswith(("/edit ", "edit ")):
                index = self.edit_index(raw.split(maxsplit=1)[1])
                if index is not None:
                    return "edit", index
            else:
                self.say(self.labels["choice_required"])

    def run(self) -> dict:
        for key in ("title", "notice", "scope", "navigation", "import_guidance", "quantity_notice"):
            self.say(self.labels[key])
        index = 0
        editing = False
        while True:
            if index == len(self.fields):
                action, target = self.review()
                if action == "save":
                    validate_instance(self.draft)
                    return deepcopy(self.draft)
                index = target
                editing = action == "edit"
                continue
            try:
                self.collect(index)
            except _Back:
                if editing:
                    # Discard the uncommitted edit and keep the reviewed value.
                    index = len(self.fields)
                    editing = False
                elif index:
                    index -= 1
                else:
                    self.say(self.labels["first_field"])
                continue
            if editing:
                index = len(self.fields)
                editing = False
            else:
                index += 1


def interactive_composite_instance(
    lang: str = "en", input_stream: TextIO | None = None, output_stream: TextIO | None = None,
) -> dict:
    """Collect a reviewed valid draft, or raise :class:`IntakeCancelled`.

    Both streams must be TTYs. Unsupported language/non-TTY use raises
    ``ValidationError`` before consuming any input. EOF and Ctrl-C are always
    cancellation, including during review/editing. This function has no save,
    overwrite, import, network, or evidence-classification side effects.
    """
    if not isinstance(lang, str) or lang not in LABELS:
        raise ValidationError("unsupported language; expected en, zh, ja or de")
    input_stream = sys.stdin if input_stream is None else input_stream
    output_stream = sys.stdout if output_stream is None else output_stream
    try:
        tty = bool(input_stream.isatty()) and bool(output_stream.isatty())
    except (AttributeError, OSError, ValueError):
        tty = False
    if not tty:
        raise ValidationError(LABELS[lang]["tty_required"])
    try:
        return _Wizard(lang, input_stream, output_stream).run()
    except KeyboardInterrupt as exc:
        raise IntakeCancelled(LABELS[lang]["cancelled"]) from exc
