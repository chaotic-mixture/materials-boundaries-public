"""Strict, dependency-free validator for instance schema 1.0.0.

Unknown (null or an omitted observation) is valid data. Invalid types, units,
nonfinite numbers, duplicate JSON keys and contradictory fractions are not.
"""
from __future__ import annotations

import json
import math
from decimal import Context, Decimal, localcontext
from pathlib import Path
from typing import Any

UNITS = {"Pa": Decimal(1), "kPa": Decimal(1000), "MPa": Decimal(1000000), "GPa": Decimal(1000000000)}
CONDITION_TYPES = {
    "dimension": int,
    "constituent_symmetry": str,
    "effective_symmetry": str,
    "kinematics": str,
    "constitutive_law": str,
    "loading": str,
    "interface": str,
}
FRACTION_TOLERANCE = Decimal("1e-12")


class ValidationError(ValueError):
    """An input does not conform to the supported instance contract."""


def _error(path: str, message: str) -> None:
    raise ValidationError(f"{path}: {message}")


def _object(value: Any, path: str, allowed: set[str], required: set[str]) -> None:
    if not isinstance(value, dict):
        _error(path, "expected an object")
    missing = required - value.keys()
    extra = value.keys() - allowed
    if missing:
        _error(path, f"missing fields: {', '.join(sorted(missing))}")
    if extra:
        _error(path, f"unsupported fields: {', '.join(sorted(extra))}")


def _string(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        _error(path, "expected a nonempty string")


def _number(value: Any, path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _error(path, "expected a finite number or null")
    # math.isfinite(very_large_int) may overflow before reporting a useful error.
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        _error(path, "nonfinite or out-of-range number")


def _quantity(value: Any, path: str) -> None:
    if value is None:
        return
    _object(value, path, {"value", "unit"}, {"value", "unit"})
    if value["value"] is not None:
        _number(value["value"], path + ".value")
    if not isinstance(value["unit"], str) or value["unit"] not in UNITS:
        _error(path + ".unit", "expected Pa, kPa, MPa or GPa (case-sensitive)")


def validate_instance(instance: Any) -> None:
    """Validate deterministically, independent of the caller's Decimal context."""
    with localcontext(Context(prec=80)):
        _validate_instance(instance)


def _validate_instance(instance: Any) -> None:
    """Validate structural and cross-field constraints; never infer physics."""
    _object(instance, "$", {"schema_version", "id", "conditions", "phases", "provenance"},
            {"schema_version", "id", "conditions", "phases", "provenance"})
    if instance["schema_version"] != "1.0.0":
        _error("$.schema_version", "expected 1.0.0")
    _string(instance["id"], "$.id")
    conditions = instance["conditions"]
    _object(conditions, "$.conditions", set(CONDITION_TYPES), set())
    for key, expected in CONDITION_TYPES.items():
        value = conditions.get(key)
        if value is not None:
            if expected is int:
                _number(value, f"$.conditions.{key}")
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or value < 1 or value != int(value)):
                    _error(f"$.conditions.{key}", "expected a positive integer or null")
            else:
                _string(value, f"$.conditions.{key}")
    phases = instance["phases"]
    if not isinstance(phases, list) or not phases:
        _error("$.phases", "expected at least one phase")
    ids = set()
    for index, phase in enumerate(phases):
        path = f"$.phases[{index}]"
        _object(phase, path, {"id", "volume_fraction", "bulk_modulus", "shear_modulus"}, {"id"})
        _string(phase["id"], path + ".id")
        if phase["id"] in ids:
            _error(path + ".id", "duplicate phase id")
        ids.add(phase["id"])
        fraction = phase.get("volume_fraction")
        if fraction is not None:
            _number(fraction, path + ".volume_fraction")
            if not 0 <= fraction <= 1:
                _error(path + ".volume_fraction", "expected a value in [0, 1]")
        for prop in ("bulk_modulus", "shear_modulus"):
            _quantity(phase.get(prop), path + "." + prop)
    fractions = [p.get("volume_fraction") for p in phases]
    known_total = sum((Decimal(str(f)) for f in fractions if f is not None), Decimal(0))
    if known_total > 1 + FRACTION_TOLERANCE:
        _error("$.phases", "known volume fractions exceed 1")
    if all(f is not None for f in fractions) and abs(known_total - 1) > FRACTION_TOLERANCE:
        _error("$.phases", "volume fractions must sum to 1 (absolute tolerance 1e-12)")
    provenance = instance["provenance"]
    _object(provenance, "$.provenance", {"kind", "note", "source_ids", "model_evidence"}, {"kind"})
    if provenance["kind"] not in ("synthetic", "literature", "literature_model", "computed", "measured", "unspecified"):
        _error("$.provenance.kind", "unsupported provenance kind")
    if "note" in provenance:
        _string(provenance["note"], "$.provenance.note")
    if "source_ids" in provenance:
        if not isinstance(provenance["source_ids"], list):
            _error("$.provenance.source_ids", "expected an array of source identifiers")
        for source in provenance["source_ids"]:
            _string(source, "$.provenance.source_ids[]")
    if provenance["kind"] == "literature_model":
        if "model_evidence" not in provenance:
            _error("$.provenance", "literature_model requires model_evidence")
        _validate_model_evidence(instance)
    elif "model_evidence" in provenance:
        _error("$.provenance.model_evidence", "requires kind literature_model")


def _validate_model_evidence(instance: dict) -> None:
    """Validate declared provenance and conversions, not source truth or specimens."""
    from .conversions import CONVERSION_RULE_ID, isotropic_moduli

    path = "$.provenance.model_evidence"
    evidence = instance["provenance"]["model_evidence"]
    fields = {"source_id", "locator", "parameter_basis", "raw_parameters", "conversion_rule_id",
              "condition_basis", "fraction_basis", "temperature_k", "material_grade", "cure_state",
              "measurement_uncertainty", "scope_note"}
    _object(evidence, path, fields, fields)
    for field in ("source_id", "locator", "scope_note"):
        _string(evidence[field], path + "." + field)
    if evidence["source_id"] not in instance["provenance"].get("source_ids", []):
        _error(path + ".source_id", "must occur in provenance.source_ids")
    if evidence["parameter_basis"] != "literature_model_inputs":
        _error(path + ".parameter_basis", "expected literature_model_inputs")
    if evidence["conversion_rule_id"] != CONVERSION_RULE_ID:
        _error(path + ".conversion_rule_id", "unsupported conversion rule")
    if evidence["fraction_basis"] != "calculator_choice":
        _error(path + ".fraction_basis", "this example contract supports calculator_choice only")
    temperature = evidence["temperature_k"]
    if temperature is not None:
        _number(temperature, path + ".temperature_k")
        if temperature <= 0:
            _error(path + ".temperature_k", "expected positive Kelvin or null")
    for field in ("material_grade", "cure_state", "measurement_uncertainty"):
        if evidence[field] is not None:
            _string(evidence[field], path + "." + field)
    bases = evidence["condition_basis"]
    _object(bases, path + ".condition_basis", set(CONDITION_TYPES), set(CONDITION_TYPES))
    for key, basis in bases.items():
        if basis not in ("source_model", "calculator_assumption", "unknown"):
            _error(path + ".condition_basis." + key, "unsupported evidence basis")
        if (basis == "unknown") != (instance["conditions"].get(key) is None):
            _error(path + ".condition_basis." + key, "unknown basis must match a null/missing condition")
    records = evidence["raw_parameters"]
    if not isinstance(records, list) or not records:
        _error(path + ".raw_parameters", "expected nonempty parameter records")
    phases = {p["id"]: p for p in instance["phases"]}
    seen = set()
    for index, record in enumerate(records):
        here = f"{path}.raw_parameters[{index}]"
        _object(record, here, {"phase_id", "youngs_modulus", "poissons_ratio"},
                {"phase_id", "youngs_modulus", "poissons_ratio"})
        _string(record["phase_id"], here + ".phase_id")
        phase_id = record["phase_id"]
        if phase_id not in phases or phase_id in seen:
            _error(here + ".phase_id", "must reference a unique instance phase")
        seen.add(phase_id)
        young = record["youngs_modulus"]
        _quantity(young, here + ".youngs_modulus")
        if young is None or young["value"] is None:
            _error(here + ".youngs_modulus", "this conversion requires known E")
        try:
            derived = isotropic_moduli(young["value"], record["poissons_ratio"])
        except ValueError as exc:
            _error(here, str(exc))
        for key, expected in zip(("bulk_modulus", "shear_modulus"), derived):
            quantity = phases[phase_id].get(key)
            if quantity is None or quantity["value"] is None:
                _error(here, f"derived {key} must be present in phase inputs")
            expected_pa = Decimal(str(expected)) * UNITS[young["unit"]]
            actual_pa = Decimal(str(quantity["value"])) * UNITS[quantity["unit"]]
            if abs(actual_pa - expected_pa) > abs(expected_pa) * Decimal("1e-12"):
                _error(here, f"phase {key} disagrees with fixed E/nu conversion (relative tolerance 1e-12)")
    if seen != set(phases):
        _error(path + ".raw_parameters", "one raw parameter record is required for every phase")


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValidationError(f"non-standard JSON numeric constant: {value}")


def _strict_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise ValidationError("JSON integer exceeds supported input range") from exc
    _number(number, "JSON integer")
    return number


def _strict_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValidationError(f"JSON number outside finite float input range: {value}")
    if number == 0 and Decimal(value) != 0:
        raise ValidationError(f"JSON number underflows float input range: {value}")
    return number


def load_json(path: str | Path) -> Any:
    """Read JSON without silently accepting duplicate keys, NaN or Infinity."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"),
                          object_pairs_hook=_unique_pairs, parse_constant=_reject_constant, parse_float=_strict_float, parse_int=_strict_int)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError(f"invalid JSON: {exc}") from exc
