"""Auditable evaluation of a small fixed registry of isotropic elastic bounds."""
from __future__ import annotations

from copy import deepcopy
from decimal import Context, Decimal, localcontext
import math
from typing import Any

from ._version import __version__
from .validation import UNITS, ValidationError, validate_instance

D = Decimal
EXPECTED = {
    "dimension": 3,
    "constituent_symmetry": "isotropic",
    "effective_symmetry": "isotropic",
    "kinematics": "small_strain",
    "constitutive_law": "linear_elastic",
    "loading": "static",
    "interface": "perfectly_bonded",
}


class NumericalRangeError(ArithmeticError):
    """A result cannot be safely represented in its declared output domain."""


def _check(key: str, state: str, observed: Any, expected: Any) -> dict:
    return {"condition_id": key, "state": state, "observed": observed, "expected": expected}


def _state(checks: list[dict]) -> str:
    states = {c["state"] for c in checks}
    return "violated" if "violated" in states else "unknown" if "unknown" in states else "satisfied"


def _quantity(phase: dict, name: str) -> Decimal | None:
    quantity = phase.get(name)
    if quantity is None or quantity.get("value") is None:
        return None
    value = D(str(quantity["value"]))
    # All supported units are integer powers of ten. Scale the coefficient
    # exactly so >80-digit integer inputs cannot lose phase-order evidence
    # before applicability is checked. Bound arithmetic still uses Decimal80.
    sign, digits, exponent = value.as_tuple()
    zeros = UNITS[quantity["unit"]].adjusted()
    return D((sign, digits + (0,) * zeros, exponent))


def _positive_float(value: Decimal) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise NumericalRangeError("positive result is outside finite, nonzero float range in the requested unit")
    return result


# Canonical registry order preserves the original three bulk evaluations first.
BASE_RULES = (
    ("hs_bulk_3d_two_phase", "hs_bulk_3d_two_phase_v1", "effective_bulk_modulus", True),
    ("reuss_bulk", "reuss_bulk_v1", "effective_bulk_modulus", False),
    ("voigt_bulk", "voigt_bulk_v1", "effective_bulk_modulus", False),
    ("hs_shear_3d_two_phase", "hs_shear_3d_two_phase_v1", "effective_shear_modulus", True),
    ("reuss_shear", "reuss_shear_v1", "effective_shear_modulus", False),
    ("voigt_shear", "voigt_shear_v1", "effective_shear_modulus", False),
)
DERIVED_RULES = (
    ("youngs_modulus_outer", "isotropic_youngs_modulus_outer_v1", "effective_youngs_modulus"),
    ("poissons_ratio_outer", "isotropic_poissons_ratio_outer_v1", "effective_poissons_ratio"),
)
DEPENDENCY_IDS = ("hs_bulk_3d_two_phase", "hs_shear_3d_two_phase")


def _rational_bound(values: list[Decimal], fractions: list[Decimal], c: Decimal) -> Decimal:
    """Positive HS form; no contrast division or cancellation subtraction."""
    x1, x2 = values
    f1, f2 = fractions
    arithmetic = f1 * x1 + f2 * x2
    swapped = f1 * x2 + f2 * x1
    return (x1 * x2 + c * arithmetic) / (swapped + c)


def _compute_decimal(rule_id: str, active: list[dict]) -> dict[str, Decimal]:
    """Compute in Pa, retaining Decimal endpoints for dependent rules."""
    values = [p["shear" if "shear" in rule_id else "bulk"] for p in active]
    fractions = [p["fraction"] for p in active]
    if len(active) == 1:
        lower = upper = values[0]
    elif rule_id == "hs_bulk_3d_two_phase_v1":
        shear = [p["shear"] for p in active]
        lower = _rational_bound(values, fractions, D(4) * min(shear) / D(3))
        upper = _rational_bound(values, fractions, D(4) * max(shear) / D(3))
    elif rule_id == "hs_shear_3d_two_phase_v1":
        # Sort whole phases, never K, G or their fractions independently.
        soft, hard = sorted(active, key=lambda p: (p["bulk"], p["shear"]))

        def zeta(phase: dict) -> Decimal:
            k, g = phase["bulk"], phase["shear"]
            return g * (D(9) * k + D(8) * g) / (D(6) * k + D(12) * g)

        lower = _rational_bound(values, fractions, zeta(soft))
        upper = _rational_bound(values, fractions, zeta(hard))
    elif rule_id in {"reuss_bulk_v1", "reuss_shear_v1"}:
        lower = upper = D(1) / sum((f / x for f, x in zip(fractions, values)), D(0))
    elif rule_id in {"voigt_bulk_v1", "voigt_shear_v1"}:
        lower = upper = sum((f * x for f, x in zip(fractions, values)), D(0))
    else:
        raise ValueError(f"rule not in executable registry: {rule_id}")
    if rule_id.startswith("hs_"):
        return {"lower": lower, "upper": upper}
    return {"lower" if rule_id.startswith("reuss_") else "upper": lower}


def _serialize_modulus(endpoints: dict[str, Decimal], unit: str) -> dict:
    return {**{side: _positive_float(value / UNITS[unit]) for side, value in endpoints.items()}, "unit": unit}


def _derive(rule_id: str, bulk: dict[str, Decimal], shear: dict[str, Decimal], unit: str) -> dict:
    """Monotonic images of a compatible K/G rectangle, not a joint feasible set."""
    kl, ku, gl, gu = bulk["lower"], bulk["upper"], shear["lower"], shear["upper"]
    if rule_id == "isotropic_youngs_modulus_outer_v1":
        def young(k: Decimal, g: Decimal) -> Decimal:
            return D(9) * k * g / (D(3) * k + g)
        return _serialize_modulus({"lower": young(kl, gl), "upper": young(ku, gu)}, unit)
    if rule_id != "isotropic_poissons_ratio_outer_v1":
        raise ValueError(f"rule not in executable registry: {rule_id}")

    def poisson(k: Decimal, g: Decimal) -> float:
        value = float((D(3) * k - D(2) * g) / (D(2) * (D(3) * k + g)))
        # Even a strictly physical Decimal ratio may round onto -1 or 0.5.
        # Do not clip: moving inward would pretend to provide a safer bound.
        if not math.isfinite(value) or not -1 < value < 0.5:
            raise NumericalRangeError("Poisson endpoint cannot be represented strictly inside (-1, 0.5); no clipping applied")
        return value

    return {"lower": poisson(kl, gu), "upper": poisson(ku, gl), "unit": "1"}


def evaluate(instance: dict, *, output_unit: str = "GPa") -> dict:
    """Return evaluations separately from the reusable claim catalog.

    satisfied means stated/numerically checked assumptions match this narrow
    implementation, not that an experiment or a microstructure was verified.
    """
    validate_instance(instance)
    if output_unit not in UNITS:
        raise ValidationError("output_unit: expected Pa, kPa, MPa or GPa")
    with localcontext(Context(prec=80)):
        return _evaluate(instance, output_unit)


def _evaluate(instance: dict, output_unit: str) -> dict:
    checks = []
    for key, expected in EXPECTED.items():
        observed = instance["conditions"].get(key)
        state = "unknown" if observed is None else "satisfied" if observed == expected else "violated"
        checks.append(_check(key, state, observed, expected))
    phases = instance["phases"]
    checks.append(_check("two_phase_description", "satisfied" if len(phases) == 2 else "violated", len(phases), 2))
    fractions_known = all(p.get("volume_fraction") is not None for p in phases)
    checks.append(_check("volume_fractions_known", "satisfied" if fractions_known else "unknown",
                         [p.get("volume_fraction") for p in phases], "all known; sum to 1"))
    total = sum((D(str(p["volume_fraction"])) for p in phases), D(0)) if fractions_known else None
    prepared = [{"id": p["id"],
                 "fraction": D(str(p["volume_fraction"])) / total if fractions_known else None,
                 "bulk": _quantity(p, "bulk_modulus"), "shear": _quantity(p, "shear_modulus")}
                for p in phases]
    # Exactly zero is inactive. A tiny positive fraction is never discarded.
    # For incomplete fractions use all not-known-zero phases conservatively.
    active = [p for p, raw in zip(prepared, phases) if raw.get("volume_fraction") != 0]
    for prop in ("bulk", "shear"):
        values = [p[prop] for p in active]
        state = "violated" if any(v is not None and v <= 0 for v in values) else (
            "unknown" if any(v is None for v in values) else "satisfied")
        checks.append(_check("positive_" + prop + "_moduli", state,
                             [{"phase_id": p["id"], "value_pa": str(p[prop]) if p[prop] is not None else None}
                              for p in active], "strictly positive for every active phase"))
    ordering = "unknown"
    if fractions_known and len(active) == 1:
        ordering = "satisfied"
    elif len(active) == 2:
        a, b = active
        if all(p[prop] is not None for p in active for prop in ("bulk", "shear")):
            increasing = a["bulk"] <= b["bulk"] and a["shear"] <= b["shear"]
            decreasing = a["bulk"] >= b["bulk"] and a["shear"] >= b["shear"]
            ordering = "satisfied" if increasing or decreasing else "violated"
    ordering_check = _check("well_ordered_phases", ordering, None,
                            "(K1-K2)*(G1-G2) >= 0, including equal-modulus and pure-phase limits")
    evaluations = []
    decimal_results = {}
    # Registry, not eval/exec: catalog text cannot introduce executable formulas.
    for claim_id, rule_id, quantity, needs_order in BASE_RULES:
        required = checks + ([ordering_check] if needs_order else [])
        state = _state(required)
        result = None
        error = None
        computation = "not_computed"
        if state == "satisfied":
            try:
                endpoints = _compute_decimal(rule_id, active)
                result = _serialize_modulus(endpoints, output_unit)
                decimal_results[claim_id] = endpoints
                computation = "computed"
            except NumericalRangeError as exc:
                computation = "numerical_range_error"
                error = str(exc)
        evaluations.append({"claim_id": claim_id, "rule_id": rule_id,
                            "quantity": quantity, "bound_kind": "scalar_modulus_bound",
                            "applicability": state, "checks": required,
                            "computation": computation, "result": result, "error": error})

    # Dependencies are from this evaluation only, never caller-supplied endpoints.
    dependencies = [item for item in evaluations if item["claim_id"] in DEPENDENCY_IDS]
    dependency_state = _state([{"state": item["applicability"]} for item in dependencies])
    dependency_check = _check("compatible_bulk_shear_bounds", dependency_state,
                              {"instance_id": instance["id"],
                               "claims": [{"claim_id": item["claim_id"], "applicability": item["applicability"],
                                           "computation": item["computation"]} for item in dependencies]},
                              "both HS bounds apply to the same phases, fractions, units and conditions")
    for claim_id, rule_id, quantity in DERIVED_RULES:
        required = checks + [ordering_check, dependency_check]
        state = _state(required)
        result = error = None
        computation = "not_computed"
        if state == "satisfied":
            try:
                if any(item["computation"] != "computed" for item in dependencies):
                    raise NumericalRangeError("dependent HS bulk/shear bounds are unavailable in the requested output unit")
                result = _derive(rule_id, decimal_results[DEPENDENCY_IDS[0]],
                                 decimal_results[DEPENDENCY_IDS[1]], output_unit)
                computation = "computed"
            except NumericalRangeError as exc:
                computation = "numerical_range_error"
                error = str(exc)
        evaluations.append({"claim_id": claim_id, "rule_id": rule_id,
                            "quantity": quantity, "bound_kind": "derived_outer_envelope",
                            "dependencies": {"instance_id": instance["id"], "claim_ids": list(DEPENDENCY_IDS),
                                             "compatibility": "same_instance_phase_pair_fractions_units_and_conditions",
                                             "joint_attainability": "not_asserted"},
                            "applicability": state, "checks": required,
                            "computation": computation, "result": result, "error": error})
    return {
        "schema_version": "1.1.0",
        "engine_version": __version__,
        "instance_id": instance["id"],
        "input_provenance": deepcopy(instance["provenance"]),
        "output_unit": output_unit,
        "numerical_policy": "80-digit decimal arithmetic; rounded binary-float output, not certified outward-rounded bounds",
        "fraction_normalization": {"performed": bool(fractions_known and total != 1),
                                   "original_sum": str(total) if total is not None else None,
                                   "absolute_tolerance": "1e-12",
                                   "normalized_fractions": [str(p["fraction"]) for p in prepared] if fractions_known else None},
        "assumption_policy": "conditions are supplied assertions; satisfied does not verify a physical sample",
        "scientific_verification": "equation cross-check and software tests; not independent scientific peer review",
        "evaluations": evaluations,
    }
