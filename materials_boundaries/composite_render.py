"""Deterministic, inert text/HTML rendering of verified single-case reports.

No user/source string becomes markup, an attribute, a filename, or a command.
Bibliographic URLs deliberately remain plain text; there are no active links,
forms, external assets, executable scripts, or browser-side number conversions.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
from html import escape
import json
from typing import Any

from ._composite_labels import LABELS, LANGUAGES, label
from .engine import EXPECTED
from .validation import UNITS


_CSS = """html{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#fafaf8;color:#1d2928;font-family:system-ui,sans-serif;line-height:1.6}main{max-width:76rem;margin:auto;padding:clamp(1rem,4vw,3rem);min-width:0}h1{font-size:clamp(1.7rem,5vw,2.6rem);line-height:1.15}h2{margin-top:2.5rem;border-bottom:2px solid #506f67;padding-bottom:.4rem}h3{margin-top:1.8rem}h4{margin:.2rem 0 .8rem;font-size:1.1rem}p,li,h1,h2,h3,h4{overflow-wrap:anywhere;white-space:pre-wrap}ul{padding-left:1.3rem}.result{border:1px solid #859a93;border-left:4px solid #426b60;border-radius:.3rem;background:white;padding:1rem;margin:1rem 0}.record{font-family:ui-monospace,monospace;font-size:.92rem;white-space:pre-wrap;overflow-wrap:anywhere;max-width:100%;margin:.6rem 0}.notice{background:#eef3ef;border-left:4px solid #59735f;padding:.8rem 1rem}strong{font-weight:650}.audit{margin-top:2rem;border-top:1px solid #859a93;padding-top:1rem}summary{cursor:pointer;overflow-wrap:anywhere}summary:focus-visible{outline:3px solid #426b60;outline-offset:4px}@media(max-width:35rem){main{padding:1rem}.result{padding:.75rem}.record{font-size:.85rem}}@media print{body{background:white}main{max-width:none;padding:0}.result{break-inside:avoid}h2,h3,h4{break-after:avoid}}"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _value(value: Any) -> str:
    # str(int) preserves arbitrary-precision inputs; repr(float) round-trips even
    # at Poisson boundaries. Never use a shared 12-digit display formatter.
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        return repr(value)
    return _json(value)


class _Document:
    """Build both presentations from one semantic sequence; never interpolate HTML."""

    def __init__(self, lang: str):
        self.lang = lang
        self.parts: list[tuple[str, str]] = []
        self.audit_bundle: dict | None = None

    def add(self, kind: str, text: str) -> None:
        self.parts.append((kind, text))

    def heading(self, key: str, level: int = 2) -> None:
        self.add("h" + str(level), label(key, self.lang))

    def paragraph(self, text: str, *, notice: bool = False) -> None:
        self.add("notice" if notice else "p", text)

    def wording(self, key: str, *, notice: bool = False) -> None:
        self.paragraph(label(key, self.lang), notice=notice)

    def field(self, key: str, value: Any) -> None:
        self.paragraph(label(key, self.lang) + ": " + _value(value))

    def output(self, format: str) -> str:
        if format == "text":
            return "\n".join(text for kind, text in self.parts if kind not in {"open_result", "close_result"}) + "\n"
        title = escape(label("title", self.lang), quote=True)
        html = ["<!doctype html>", '<html lang="' + self.lang + '">', "<head>",
                '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">',
                '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
                "<title>" + title + "</title>", "<style>" + _CSS + "</style>", "</head>", "<body><main>"]
        for kind, text in self.parts:
            safe = escape(text, quote=True)
            if kind == "open_result":
                html.append('<article class="result">')
            elif kind == "close_result":
                html.append("</article>")
            elif kind == "notice":
                html.append('<p class="notice">' + safe + "</p>")
            elif kind == "record":
                html.append('<pre class="record">' + safe + "</pre>")
            else:
                html.append("<" + kind + ">" + safe + "</" + kind + ">")
        if self.audit_bundle is not None:
            html.extend(['<details class="audit">',
                         "<summary>" + escape(label("full_records", self.lang), quote=True) + "</summary>",
                         '<pre class="record">' + escape(json.dumps(self.audit_bundle, ensure_ascii=False,
                            sort_keys=True, allow_nan=False, indent=2), quote=True) + "</pre>", "</details>"])
        html.extend(["</main></body>", "</html>"])
        return "\n".join(html) + "\n"


def _status(state: str, lang: str) -> str:
    return label(state, lang) + " (" + state + ")"


def _counts(items: list[dict], field: str, states: tuple[str, ...], lang: str) -> str:
    counts = Counter(item[field] for item in items)
    return "; ".join(_status(state, lang) + ": " + str(counts[state]) for state in states)


def _checks(items: list[dict]) -> list[dict]:
    # Retain engine order and distinct observations; common repeated checks are
    # consolidated visually only. Per-result full checks stay in the bundle.
    seen = set()
    result = []
    for item in items:
        for check in item["checks"]:
            identity = _json(check)
            if identity not in seen:
                result.append(check)
                seen.add(identity)
    return result


def _pa(quantity: dict | None) -> str | None:
    if quantity is None or quantity["value"] is None:
        return None
    number = Decimal(str(quantity["value"]))
    sign, digits, exponent = number.as_tuple()
    # Tuple construction is exact and independent of ambient decimal context.
    return str(Decimal((sign, digits, exponent + UNITS[quantity["unit"]].adjusted())))


def render_composite_report(bundle: dict, lang: str = "en", format: str = "text") -> str:
    """Render only a bundle that reproduces with the installed engine/catalog.

    Both formats use deterministic round-trip numbers and preserve source/user
    wording. Unsupported formats/languages are errors, not silent fallbacks.
    """
    from .composite import validate_composite_report

    _options(lang, format)
    validate_composite_report(bundle)
    return _render_composite_report(bundle, lang=lang, format=format)


def _options(lang: str, format: str) -> None:
    if lang not in LANGUAGES:
        raise ValueError("lang: expected en, zh, ja or de")
    if format not in ("text", "html"):
        raise ValueError("format: expected text or html")


_SHORT_CLAIMS = {
    "hs_bulk_3d_two_phase": "K HS", "reuss_bulk": "K Reuss", "voigt_bulk": "K Voigt",
    "hs_shear_3d_two_phase": "G HS", "reuss_shear": "G Reuss", "voigt_shear": "G Voigt",
    "youngs_modulus_outer": "E", "poissons_ratio_outer": "ν",
}


def _unique(values):
    """Stable de-duplication of wording, never truncate original evidence."""
    return list(dict.fromkeys(values))


def _basis_key(check: dict, model: dict) -> str:
    key = check["condition_id"]
    if key in EXPECTED:
        return model.get("condition_basis", {}).get(key, "supplied_assertion")
    return "same_case" if key == "compatible_bulk_shear_bounds" else "numerical_check"


def _term(prefix: str, key: str, lang: str) -> str:
    return label(prefix + key, lang) + " (" + key + ")"


def _local_value(value: Any, lang: str) -> str:
    if value is None:
        return _term("value_", "null", lang)
    if isinstance(value, str) and "value_" + value in LABELS[lang]:
        return _term("value_", value, lang)
    return _value(value)  # User-supplied unknown enums keep their exact wording.


def _condition_name(key: str, lang: str) -> str:
    return _term("condition_name_", key, lang)


def _required(check: dict, lang: str) -> str:
    key = "required_" + check["condition_id"]
    return label(key, lang) if key in LABELS[lang] else _local_value(check["expected"], lang)


def _observed(check: dict, lang: str) -> str:
    """Short localized ledger cells; arbitrary user strings stay unchanged."""
    observed = check["observed"]
    if check["condition_id"] == "well_ordered_phases" and observed is None:
        return label("paired_input_check", lang)
    if isinstance(observed, list) and check["condition_id"] == "volume_fractions_known":
        return "[" + ", ".join(_local_value(value, lang) for value in observed) + "]"
    if check["condition_id"] in ("positive_bulk_moduli", "positive_shear_moduli"):
        return "; ".join(row["phase_id"] + "=" + _local_value(row["value_pa"], lang)
                         + " Pa" for row in observed)
    if check["condition_id"] == "compatible_bulk_shear_bounds":
        return ("instance_id=" + observed["instance_id"] + "; " + "; ".join(
            _SHORT_CLAIMS[row["claim_id"]] + "=" + _term("state_", row["applicability"], lang)
            + "/" + _term("state_", row["computation"], lang) for row in observed["claims"]))
    return _local_value(observed, lang)


def _render_composite_report(bundle: dict, lang: str = "en", format: str = "text") -> str:
    """Internal exporter path: caller must have just built/validated the bundle.

    The concise visible narrative retains essential evidence and all original
    user text. Full machine records remain lossless in the bundle and in closed
    HTML audit details, rather than overwhelming the researcher-facing report.
    """
    _options(lang, format)
    doc = _Document(lang)
    doc.audit_bundle = bundle
    instance = bundle["input"]
    evaluation = bundle["evaluation"]
    items = evaluation["evaluations"]
    claim_records = bundle["catalogs"]["claims"]["records"]
    claims = {record["id"]: record for record in claim_records}
    provenance = instance["provenance"]
    model = provenance.get("model_evidence", {})
    checks = _checks(items)
    blockers = [check for check in checks if check["state"] != "satisfied"]
    normalization = evaluation["fraction_normalization"]
    normalized = normalization["normalized_fractions"]

    doc.heading("title", 1)
    doc.heading("question")
    doc.paragraph(label("case_id", lang) + ": " + instance["id"] + " | "
                  + label("input_origin", lang) + ": " + provenance["kind"] + " | "
                  + label("output_unit", lang) + ": " + bundle["output_unit"])
    if "note" in provenance:
        doc.field("note", provenance["note"])
    doc.field("input_sources", provenance.get("source_ids", []))
    if model:
        doc.heading("raw_parameters", 3)
        for raw in model["raw_parameters"]:
            doc.paragraph(raw["phase_id"] + ": E=" + _value(raw["youngs_modulus"]["value"])
                          + " " + raw["youngs_modulus"]["unit"] + "; ν=" + _value(raw["poissons_ratio"]))
        doc.wording("model_distinction")
    doc.heading("converted_inputs" if model else "phase_inputs", 3)
    for phase in instance["phases"]:
        properties = []
        for key, symbol in (("bulk_modulus", "K"), ("shear_modulus", "G")):
            quantity = phase.get(key)
            raw = "null" if quantity is None else _value(quantity["value"]) + " " + quantity["unit"]
            properties.append(symbol + "=" + raw)
        doc.paragraph(phase["id"] + ": " + label("original_fraction", lang) + "="
                      + _value(phase.get("volume_fraction")) + "; " + "; ".join(properties))
    # Physical/source limitations precede any computed endpoint.
    for key in ("scope_notice", "source_notice", "numerical_notice", "joint_notice"):
        doc.wording(key, notice=True)
    doc.heading("states", 3)
    doc.field("structure", label("valid_structure", lang))
    doc.field("applicability", _counts(items, "applicability", ("satisfied", "unknown", "violated"), lang))
    doc.field("availability", _counts(items, "computation", ("computed", "not_computed", "numerical_range_error"), lang))
    doc.field("review", label("review_state", lang))
    if bundle["catalogs"]["unresolved_source_ids"]:
        doc.field("unresolved", bundle["catalogs"]["unresolved_source_ids"])
    doc.wording("unknown_notice")
    if blockers:
        doc.field("early_blockers", "; ".join(_condition_name(check["condition_id"], lang) + ": " + _term("state_", check["state"], lang) for check in blockers))
    else:
        doc.wording("no_blockers")

    doc.heading("answer")
    doc.wording("ordering_display")
    group = None
    group_keys = {"effective_bulk_modulus": "quantity_k", "effective_shear_modulus": "quantity_g",
                  "effective_youngs_modulus": "quantity_e", "effective_poissons_ratio": "quantity_nu"}
    collapsed = []
    for index, item in enumerate(items, 1):
        if item["quantity"] != group:
            group = item["quantity"]
            doc.heading(group_keys[group], 3)
        claim_id = item["claim_id"]
        claim = claims[claim_id]
        result = item["result"]
        failures = [check for check in item["checks"] if check["state"] != "satisfied"]
        if result is not None:
            answer = "; ".join(side + " ≈ " + _value(result[side])
                               for side in ("lower", "upper") if side in result) + " " + result["unit"]
            if "lower" in result and "upper" in result and result["lower"] == result["upper"]:
                collapsed.append(_SHORT_CLAIMS[claim_id])
        else:
            answer = label("unavailable", lang)
            if item["computation"] == "numerical_range_error":
                answer += "; " + label("primary_reason", lang) + ": " + _term("state_", "numerical_range_error", lang)
            elif failures:
                primary = next((check for check in failures if check["state"] == "violated"), failures[0])
                answer += "; " + label("primary_reason", lang) + ": " + _condition_name(primary["condition_id"], lang)
        doc.add("open_result", "")
        doc.add("h4", str(index) + ". " + label(claim_id, lang) + " [" + claim_id + "]")
        # Status meanings are localized once above; machine status tokens and
        # directions remain explicit on every compact result row.
        doc.paragraph(answer + " | " + label("applicability", lang) + ": " + _term("state_", item["applicability"], lang)
                      + " | " + label("availability", lang) + ": " + _term("state_", item["computation"], lang)
                      + " | " + label("direction", lang) + ": " + _status(claim["direction"], lang)
                      + " | rule_id=" + item["rule_id"])
        doc.add("close_result", "")
    if collapsed:
        doc.paragraph(", ".join(collapsed) + ": " + label("collapsed", lang))
    errors = {}
    for item in items:
        if item["error"]:
            errors.setdefault(item["error"], []).append(_SHORT_CLAIMS[item["claim_id"]])
    if errors:
        doc.heading("numerical_error_detail", 3)
        for error, identifiers in errors.items():
            doc.paragraph(", ".join(identifiers) + ": " + error)

    doc.heading("ledger")
    doc.wording("ledger_columns")
    for check in checks:
        doc.paragraph(_condition_name(check["condition_id"], lang) + " | " + _observed(check, lang) + " | "
                      + _required(check, lang) + " | " + _term("state_", check["state"], lang) + " | "
                      + _term("basis_", _basis_key(check, model), lang))
    used_bases = _unique(_basis_key(check, model) for check in checks)
    doc.field("basis_legend", "; ".join(_status(basis, lang) for basis in used_bases))
    doc.heading("check_explanations", 3)
    # Explain a violated/unknown condition in full and preserve short-scope
    # cautions even for successful reports; explanations appear only once.
    explain = _unique([check["condition_id"] for check in blockers] + [
        "constituent_symmetry", "effective_symmetry", "positive_bulk_moduli", "well_ordered_phases"])
    for key in explain:
        doc.paragraph(_condition_name(key, lang) + ": " + label("condition_" + key, lang))

    doc.heading("next")
    if any(check["state"] == "unknown" for check in blockers):
        doc.wording("next_unknown")
    if any(check["state"] == "violated" for check in blockers):
        doc.wording("next_violated")
    if errors:
        doc.wording("next_numeric")
    if not blockers and not errors:
        doc.wording("next_satisfied")

    doc.heading("trace")
    doc.wording("conversion_notice")
    doc.wording("normalization_notice")
    if model:
        doc.paragraph("conversion_rule_id: " + model["conversion_rule_id"])
    for index, phase in enumerate(instance["phases"]):
        doc.paragraph(phase["id"] + ": K=" + _value(_pa(phase.get("bulk_modulus")))
                      + " Pa; G=" + _value(_pa(phase.get("shear_modulus"))) + " Pa | "
                      + label("fraction_summary", lang) + ": " + _value(phase.get("volume_fraction"))
                      + " → " + _value(normalized[index] if normalized is not None else None))
    doc.paragraph("fraction_basis: " + _status(model.get("fraction_basis", "supplied_assertion"), lang))
    doc.paragraph("fraction_normalization: original_sum=" + _value(normalization["original_sum"])
                  + "; performed=" + _value(normalization["performed"])
                  + "; absolute_tolerance=" + normalization["absolute_tolerance"])
    doc.wording("corner_notice")
    doc.paragraph("instance_id=" + instance["id"] + "; hs_bulk_3d_two_phase + hs_shear_3d_two_phase"
                  + " → youngs_modulus_outer + poissons_ratio_outer; joint_attainability=not_asserted")
    for item in items:
        if "dependencies" in item:
            doc.paragraph(claims[item["claim_id"]]["formula_display"])

    doc.heading("evidence")
    doc.heading("phase_evidence", 3)
    if model:
        doc.paragraph("source_id: " + model["source_id"] + " | locator: " + model["locator"])
        doc.paragraph("parameter_basis: " + model["parameter_basis"])
        doc.paragraph("; ".join(key + "=" + _value(model[key]) for key in
                                ("temperature_k", "material_grade", "cure_state", "measurement_uncertainty")))
        doc.paragraph(model["scope_note"])
    else:
        doc.wording("context_unknown")
    doc.wording("citation_notice")
    doc.heading("sources", 3)
    for source in bundle["catalogs"]["sources"]["records"]:
        doc.add("h4", source["id"] + " · " + source["title"])
        doc.paragraph("year=" + _value(source.get("year")) + "; DOI=" + _value(source.get("doi"))
                      + "; " + label("source_metadata", lang) + ": " + source["read_status"]
                      + "; license=" + _json(source["license"]))
        # Group repeated claim-level evidence by its exact content. Source-wide
        # reading status never replaces these narrower claim inspection states.
        evidence_groups = {}
        for claim in claim_records:
            for evidence in claim["evidence"]:
                if evidence["source_id"] == source["id"]:
                    identity = (evidence["locator"], evidence["verification_status"], evidence["verified_as"])
                    evidence_groups.setdefault(identity, []).append(_SHORT_CLAIMS[claim["id"]])
        for (locator, status, verified_as), identifiers in evidence_groups.items():
            doc.paragraph(source["id"] + " · " + " / ".join(identifiers) + ": locator=" + _value(locator) + "; " + status
                          + "; " + verified_as)
        # An input-only citation needs its original specific source caveats;
        # formula-source caveats are fully represented by the visible evidence
        # groups, review gaps and common source notice.
        if not evidence_groups:
            for note in source.get("claim_notes", []):
                doc.paragraph(note)
    doc.heading("review_gaps", 3)
    for gap in _unique(gap for claim in claim_records for gap in claim["verification"]["gaps"]):
        doc.paragraph(gap)
    doc.heading("shared_limits", 3)
    for limit in _unique(limit for claim in claim_records for limit in claim["limits"]):
        doc.paragraph(limit)
    doc.wording("comparison_notice", notice=True)
    doc.wording("rights_notice")
    doc.wording("translation_notice")
    doc.wording("record_guide")

    doc.heading("reproduce")
    doc.paragraph("engine_version=" + bundle["engine_version"] + "; report_version=" + bundle["report_version"]
                  + "; composite_report schema_version=" + bundle["schema_version"]
                  + "; instance_schema_version=" + bundle["instance_schema_version"]
                  + "; evaluation_schema_version=" + bundle["evaluation_schema_version"])
    doc.paragraph("claim versions: " + "; ".join(_SHORT_CLAIMS[claim["id"]] + "=" + claim["version"] for claim in claim_records)
                  + "; claims_schema=" + bundle["catalogs"]["claims"]["schema_version"]
                  + "; sources_schema=" + bundle["catalogs"]["sources"]["schema_version"])
    digests = bundle["digests"]
    doc.paragraph("digests: " + digests["algorithm"] + "; " + digests["serialization"])
    for key in ("input", "evaluation", "claims", "sources"):
        doc.paragraph(key + ": " + digests[key])
    doc.wording("relative_command")
    doc.paragraph("materials-boundaries composite report input.json --output replay-report --unit "
                  + bundle["output_unit"] + " --lang " + lang)
    doc.paragraph("materials-boundaries composite verify bundle.json --json")
    doc.wording("replay_notice", notice=True)
    if lang != "en":
        doc.paragraph(label("replay_notice", "en"))
    doc.wording("hash_notice")
    return doc.output(format)
