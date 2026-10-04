"""Deterministic single-case reports over the unchanged elastic-bound engine.

A successful replay establishes software reproduction, not physical truth,
source authentication, permissions, or scientific review. No catalog formula is
executed and no source is fetched. Use validation.load_json for strict file
parsing; the Python APIs accept already-parsed JSON values.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
import re
from typing import Any

from ._version import __version__
from .catalog import read_catalog
from .engine import BASE_RULES, DERIVED_RULES, evaluate
from .validation import UNITS, ValidationError, validate_instance

SCHEMA_VERSION = "1.0.0"
REPORT_VERSION = "1.0.0"
INSTANCE_SCHEMA_VERSION = "1.0.0"
EVALUATION_SCHEMA_VERSION = "1.1.0"
CLAIM_IDS = tuple(rule[0] for rule in (*BASE_RULES, *DERIVED_RULES))
SERIALIZATION = "sorted_keys_utf8_compact_json_finite_numbers"
_POLICY = {
    "input_structure": "existing_instance_contract",
    "assumption_basis": "supplied_assertions_not_sample_verification",
    "base_rule_scope": "all_six_base_rules_require_known_positive_active_K_and_G",
    "hs_ordering": "paired_non_strict_K_and_G_ordering",
    "derived_dependencies": "same_instance_HS_bulk_and_shear_only_no_fallback",
    "joint_attainability": "not_asserted",
    "interval_semantics": "conditional_theoretical_bounds_or_derived_outer_envelopes_not_confidence_intervals",
    "numerical_policy": "decimal80_rounded_binary_float_not_certified_outward_rounding",
    "unknown_values": "preserved_not_inferred_or_filled",
    "input_citations": "user_supplied_catalog_IDs_not_verified_input_evidence",
    "scientific_review": "recorded_claim_level_limits_preserved",
    "independent_scientific_review": False,
    "replay_scope": "software_replay_only_not_physical_sample_verification_or_theorem_proof",
    "hash_scope": "content_identity_not_authorship_source_truth_or_permissions",
    "rights": "bibliographic_metadata_only_no_third_party_content_relicensing",
}
_ROOT_FIELDS = {
    "schema_version", "kind", "report_version", "engine_version",
    "instance_schema_version", "evaluation_schema_version", "instance_id",
    "output_unit", "input", "evaluation", "catalogs", "policy", "digests",
}


class CompositeReplayError(ValueError):
    """A well-shaped report is altered or stale under the installed contract."""


def _fail(path: str, message: str) -> None:
    raise ValidationError(f"{path}: {message}")


def _json_tree(value: Any) -> None:
    """Reject non-JSON Python values, cycles, excessive depth and nonfinite data.

    An iterative walk avoids leaking RecursionError for hostile Python callers.
    Shared objects are allowed (the existing evaluation shares check objects).
    The input contract's finite range is retained without converting its integers.
    """
    active: set[int] = set()
    stack = [(value, "$", 0, False)]
    while stack:
        item, path, depth, leaving = stack.pop()
        if leaving:
            active.remove(id(item))
            continue
        if depth > 128:
            _fail(path, "JSON nesting exceeds the supported report structure")
        if isinstance(item, (dict, list)):
            if id(item) in active:
                _fail(path, "cyclic values are not JSON")
            active.add(id(item))
            stack.append((item, path, depth, True))
            if isinstance(item, dict):
                for key, child in item.items():
                    if not isinstance(key, str):
                        _fail(path, "JSON object keys must be strings")
                    try:
                        key.encode("utf-8")
                    except UnicodeEncodeError as exc:
                        raise ValidationError(f"{path}: invalid Unicode object key") from exc
                    stack.append((child, path + "." + key, depth + 1, False))
            else:
                for index, child in enumerate(item):
                    stack.append((child, f"{path}[{index}]", depth + 1, False))
        elif item is None or isinstance(item, bool):
            continue
        elif isinstance(item, str):
            try:
                item.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ValidationError(f"{path}: invalid Unicode text") from exc
        elif isinstance(item, (int, float)):
            try:
                finite = math.isfinite(item)
            except OverflowError:
                finite = False
            if not finite:
                _fail(path, "nonfinite or out-of-range number")
        else:
            _fail(path, "expected a JSON value")


def canonical_json(value: Any, *, pretty: bool = False) -> str:
    """Sorted-key finite UTF-8 JSON, preserving input integer precision.

    Compact serialization is the digest input, without a final newline. Pretty
    serialization is for artifacts only. This is not an RFC 8785/JCS claim;
    notably JSON integers retain their original arbitrary precision.
    """
    _json_tree(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      indent=2 if pretty else None,
                      separators=None if pretty else (",", ":"))


def _digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def build_composite_report(instance: dict, output_unit: str = "GPa") -> dict:
    """Evaluate exactly one original case once, then join fixed public records.

    engine.evaluate performs the existing structural validation exactly once.
    Neither fractions nor missing/null fields nor provenance are rewritten.
    Applicability failure and numerical unavailability still yield valid reports.
    """
    _json_tree(instance)
    if not isinstance(output_unit, str) or output_unit not in UNITS:
        _fail("output_unit", "expected Pa, kPa, MPa or GPa")
    original = deepcopy(instance)
    evaluation = evaluate(original, output_unit=output_unit)
    claims_catalog = read_catalog("claims")
    sources_catalog = read_catalog("sources")
    by_id = {record["id"]: record for record in claims_catalog["records"]}
    claims = [deepcopy(by_id[item["claim_id"]]) for item in evaluation["evaluations"]]
    referenced = {evidence["source_id"] for claim in claims for evidence in claim["evidence"]}
    referenced.update(original["provenance"].get("source_ids", []))
    available = {record["id"] for record in sources_catalog["records"]}
    catalogs = {
        "claims": {"schema_version": claims_catalog["schema_version"], "records": claims},
        "sources": {"schema_version": sources_catalog["schema_version"],
                    "records": [deepcopy(record) for record in sources_catalog["records"]
                                if record["id"] in referenced]},
        "unresolved_source_ids": sorted(referenced - available),
    }
    return {
        "schema_version": SCHEMA_VERSION, "kind": "composite_report",
        "report_version": REPORT_VERSION, "engine_version": __version__,
        "instance_schema_version": INSTANCE_SCHEMA_VERSION,
        "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
        "instance_id": original["id"], "output_unit": output_unit,
        "input": original, "evaluation": evaluation, "catalogs": catalogs,
        "policy": deepcopy(_POLICY),
        "digests": {"algorithm": "sha256", "serialization": SERIALIZATION,
                    "input": _digest(original), "evaluation": _digest(evaluation),
                    "claims": _digest(catalogs["claims"]),
                    "sources": _digest(catalogs["sources"])},
    }


def _object(value: Any, path: str, required: set[str], optional: set[str] | None = None) -> None:
    if not isinstance(value, dict):
        _fail(path, "expected an object")
    missing = required - value.keys()
    extra = value.keys() - required - (optional or set())
    if missing:
        _fail(path, "missing fields: " + ", ".join(sorted(missing)))
    if extra:
        _fail(path, "unsupported fields: " + ", ".join(sorted(extra)))


def _text(value: Any, path: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        _fail(path, "expected a nonempty string" + (" or null" if nullable else ""))


def _array(value: Any, path: str, *, length: int | None = None) -> None:
    if not isinstance(value, list):
        _fail(path, "expected an array")
    if length is not None and len(value) != length:
        _fail(path, f"expected {length} records")


def _texts(value: Any, path: str) -> None:
    _array(value, path)
    for index, item in enumerate(value):
        _text(item, f"{path}[{index}]")


def _boolean(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        _fail(path, "expected a boolean")


def _numeric(value: Any, path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(path, "expected a finite number")


def _evaluation_shape(evaluation: Any, instance: dict) -> None:
    path = "$.evaluation"
    strings = {"schema_version", "engine_version", "instance_id", "output_unit",
               "numerical_policy", "assumption_policy", "scientific_verification"}
    _object(evaluation, path, strings | {"input_provenance", "fraction_normalization", "evaluations"})
    for field in strings:
        _text(evaluation[field], path + "." + field)
    # Apply the unmodified provenance contract including literature-model fields.
    provenance_instance = {**instance, "provenance": evaluation["input_provenance"]}
    validate_instance(provenance_instance)
    norm = evaluation["fraction_normalization"]
    here = path + ".fraction_normalization"
    _object(norm, here, {"performed", "original_sum", "absolute_tolerance", "normalized_fractions"})
    _boolean(norm["performed"], here + ".performed")
    _text(norm["original_sum"], here + ".original_sum", nullable=True)
    _text(norm["absolute_tolerance"], here + ".absolute_tolerance")
    if norm["normalized_fractions"] is not None:
        _texts(norm["normalized_fractions"], here + ".normalized_fractions")
    _array(evaluation["evaluations"], path + ".evaluations", length=8)
    for index, item in enumerate(evaluation["evaluations"]):
        here = f"{path}.evaluations[{index}]"
        names = {"claim_id", "rule_id", "quantity", "bound_kind", "applicability", "computation"}
        _object(item, here, names | {"checks", "result", "error"}, {"dependencies"})
        for field in names:
            _text(item[field], here + "." + field)
        _text(item["error"], here + ".error", nullable=True)
        _array(item["checks"], here + ".checks")
        for check in item["checks"]:
            _object(check, here + ".checks[]", {"condition_id", "state", "observed", "expected"})
            _text(check["condition_id"], here + ".checks[].condition_id")
            _text(check["state"], here + ".checks[].state")
        if item["result"] is not None:
            result = item["result"]
            _object(result, here + ".result", {"unit"}, {"lower", "upper"})
            if not ({"lower", "upper"} & result.keys()):
                _fail(here + ".result", "expected at least one endpoint")
            _text(result["unit"], here + ".result.unit")
            for side in ("lower", "upper"):
                if side in result:
                    _numeric(result[side], here + ".result." + side)
        if "dependencies" in item:
            deps = item["dependencies"]
            _object(deps, here + ".dependencies", {"instance_id", "claim_ids", "compatibility", "joint_attainability"})
            for field in ("instance_id", "compatibility", "joint_attainability"):
                _text(deps[field], here + ".dependencies." + field)
            _texts(deps["claim_ids"], here + ".dependencies.claim_ids")


def _claim_shape(claim: Any, path: str) -> None:
    names = {"id", "version", "name", "quantity", "direction", "rule_id", "formula_display",
             "bound_kind", "claim_type", "quantity_dimension", "si_unit", "evaluation_support"}
    _object(claim, path, names | {"required_assumptions", "evidence", "verification", "limits", "dependencies"})
    for field in names:
        _text(claim[field], path + "." + field)
    if not isinstance(claim["required_assumptions"], dict):
        _fail(path + ".required_assumptions", "expected an object")
    for value in claim["required_assumptions"].values():
        if not isinstance(value, (str, int, float, bool)):
            _fail(path + ".required_assumptions", "expected scalar assumption values")
    _array(claim["evidence"], path + ".evidence")
    for evidence in claim["evidence"]:
        here = path + ".evidence[]"
        _object(evidence, here, {"source_id", "locator", "verification_status", "verified_as"})
        for field in ("source_id", "verification_status", "verified_as"):
            _text(evidence[field], here + "." + field)
        _text(evidence["locator"], here + ".locator", nullable=True)
    verification = claim["verification"]
    _object(verification, path + ".verification", {"status", "independent_scientific_review", "gaps"})
    _text(verification["status"], path + ".verification.status")
    _boolean(verification["independent_scientific_review"], path + ".verification.independent_scientific_review")
    _texts(verification["gaps"], path + ".verification.gaps")
    for field in ("limits", "dependencies"):
        _texts(claim[field], path + "." + field)


def _source_shape(source: Any, path: str) -> None:
    names = {"id", "title", "read_status", "role", "bundled_content"}
    _object(source, path, names | {"authors", "year", "doi", "urls", "license", "claim_notes", "provenance"})
    for field in names:
        _text(source[field], path + "." + field)
    for field in ("authors", "urls", "claim_notes"):
        _texts(source[field], path + "." + field)
    year = source["year"]
    if year is not None and (isinstance(year, bool) or not isinstance(year, int)):
        _fail(path + ".year", "expected an integer or null")
    _text(source["doi"], path + ".doi", nullable=True)
    _object(source["license"], path + ".license", {"status", "identifier"})
    _text(source["license"]["status"], path + ".license.status")
    _text(source["license"]["identifier"], path + ".license.identifier", nullable=True)
    _object(source["provenance"], path + ".provenance", {"curation_date", "method"})
    for field in ("curation_date", "method"):
        _text(source["provenance"][field], path + ".provenance." + field)


def _report_shape(bundle: Any) -> None:
    _json_tree(bundle)
    _object(bundle, "$", _ROOT_FIELDS)
    for field in _ROOT_FIELDS - {"input", "evaluation", "catalogs", "policy", "digests"}:
        _text(bundle[field], "$." + field)
    if bundle["output_unit"] not in UNITS:
        _fail("$.output_unit", "expected Pa, kPa, MPa or GPa")
    validate_instance(bundle["input"])
    _evaluation_shape(bundle["evaluation"], bundle["input"])
    catalogs = bundle["catalogs"]
    _object(catalogs, "$.catalogs", {"claims", "sources", "unresolved_source_ids"})
    for kind, validator in (("claims", _claim_shape), ("sources", _source_shape)):
        path = "$.catalogs." + kind
        catalog = catalogs[kind]
        _object(catalog, path, {"schema_version", "records"})
        _text(catalog["schema_version"], path + ".schema_version")
        _array(catalog["records"], path + ".records", length=8 if kind == "claims" else None)
        for index, record in enumerate(catalog["records"]):
            validator(record, f"{path}.records[{index}]")
    _texts(catalogs["unresolved_source_ids"], "$.catalogs.unresolved_source_ids")
    _object(bundle["policy"], "$.policy", set(_POLICY))
    for field, expected in _POLICY.items():
        if isinstance(expected, bool):
            _boolean(bundle["policy"][field], "$.policy." + field)
        else:
            _text(bundle["policy"][field], "$.policy." + field)
    digests = bundle["digests"]
    _object(digests, "$.digests", {"algorithm", "serialization", "input", "evaluation", "claims", "sources"})
    for field in digests:
        _text(digests[field], "$.digests." + field)
        if field not in {"algorithm", "serialization"} and not re.fullmatch(r"[0-9a-f]{64}", digests[field]):
            _fail("$.digests." + field, "expected a lowercase SHA-256 hex digest")


def validate_composite_report(bundle: dict) -> None:
    """Strict closed replay, without changing or silently migrating the bundle.

    Malformed JSON/Python values and invalid embedded inputs raise
    ValidationError. Well-shaped differences (including stale versions, IDs,
    endpoints, source/review metadata, policies, or digests) raise the distinct
    CompositeReplayError. Digests are never accepted in place of re-evaluation.
    """
    _report_shape(bundle)
    rebuilt = build_composite_report(bundle["input"], output_unit=bundle["output_unit"])
    if canonical_json(rebuilt) != canonical_json(bundle):
        raise CompositeReplayError(
            "composite report does not reproduce with the installed engine/catalog; altered or stale bundle")
