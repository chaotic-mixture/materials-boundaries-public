"""Deterministic, offline views of canonical conditional elastic evaluations.

No new physical model is implemented here. Fraction sweeps call engine.evaluate
at every point. Cases are always faceted; compatibility never turns unknown
context into equality. Renderers accept only reproducible bundles of this engine.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from html import escape
from importlib.resources import files
import json
import math
from typing import Any

from . import __version__
from .catalog import read_catalog
from .engine import EXPECTED, evaluate
from .validation import UNITS, ValidationError, validate_instance

SCHEMA_VERSION = "1.0.0"
QUANTITIES = {
    "effective_bulk_modulus": ("pressure", "K"),
    "effective_shear_modulus": ("pressure", "G"),
    "effective_youngs_modulus": ("pressure", "E"),
    "effective_poissons_ratio": ("dimensionless", "ν"),
}
CONTEXT_FIELDS = ("temperature_k", "material_grade", "cure_state", "measurement_uncertainty")
DEFAULT_FRACTIONS = tuple(i / 20 for i in range(21))


class VisualizationError(ValueError):
    """Unsupported comparison input or a non-reproducible comparison bundle."""


def _json(value: Any, *, pretty: bool = False) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      indent=2 if pretty else None, separators=None if pretty else (",", ":"))


def _id(*parts: str) -> str:
    return sha256(_json(parts).encode("utf-8")).hexdigest()[:20]


def _text(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise VisualizationError(f"{field}: expected a nonempty string")


def _number(value: Any) -> bool:
    try:
        return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        return False


def convert_value(value: float | None, from_unit: str, to_unit: str,
                  quantity: str) -> float | None:
    """Convert only supported modulus units; ν requires dimensionless unit '1'."""
    if quantity not in QUANTITIES:
        raise VisualizationError(f"unsupported quantity: {quantity}")
    dimension = QUANTITIES[quantity][0]
    units = {"1": Decimal(1)} if dimension == "dimensionless" else UNITS
    if from_unit not in units or to_unit not in units:
        raise VisualizationError(f"unit incompatible with {quantity}: {from_unit} -> {to_unit}")
    if value is None:
        return None
    if not _number(value):
        raise VisualizationError("value must be finite or null")
    with localcontext(Context(prec=80)):
        result = float(Decimal(str(value)) * units[from_unit] / units[to_unit])
    if not math.isfinite(result) or (value != 0 and result == 0):
        raise VisualizationError("unit conversion is outside finite nonzero float range")
    return result


def _context(instance: dict) -> dict:
    evidence = instance["provenance"].get("model_evidence", {})
    return {key: deepcopy(evidence.get(key)) for key in CONTEXT_FIELDS}


def compatibility_gate(left: dict, right: dict) -> dict:
    """Explain cross-case compatibility without permitting an overlay.

    Case objects are from build_comparison. Compatibility is a necessary data
    gate, never a certification of equal physical materials or joint attainability.
    Different phases or conditions are incompatible; unspecified context is unknown.
    """
    checks = []

    def check(key: str, a: Any, b: Any, *, allow_unknown: bool = True) -> None:
        state = "unknown" if allow_unknown and (a is None or b is None) else (
            "satisfied" if a == b else "violated")
        checks.append({"condition_id": key, "state": state, "left": a, "right": b})

    check("quantity_dimensions", left["quantity_dimensions"], right["quantity_dimensions"])
    # Units must have a known conversion for every quantity, not just matching text.
    conversions = []
    valid_units = True
    for quantity in QUANTITIES:
        try:
            factor = convert_value(1, left["units"][quantity], right["units"][quantity], quantity)
            conversions.append({"quantity": quantity, "from": left["units"][quantity],
                                "to": right["units"][quantity], "factor": factor})
        except (VisualizationError, KeyError):
            valid_units = False
    checks.append({"condition_id": "unit_conversion", "state": "satisfied" if valid_units else "violated",
                   "conversions": conversions})
    check("axis_definition", left["axis"], right["axis"])
    for key in EXPECTED:
        check("conditions." + key, left["conditions"].get(key), right["conditions"].get(key))
    for key in CONTEXT_FIELDS:
        check("context." + key, left["context"].get(key), right["context"].get(key))
    check("input_provenance_kind", left["input_provenance"]["kind"], right["input_provenance"]["kind"])
    # Phase names alone never establish equal parameterization. Original fractions
    # are omitted deliberately because the sweep replaces them in every case.
    check("phase_definition", left["phase_definition"], right["phase_definition"])
    states = {item["state"] for item in checks}
    state = "incompatible" if "violated" in states else "unknown" if "unknown" in states else "compatible"
    return {"left_case_id": left["id"], "right_case_id": right["id"], "status": state,
            "overlay_allowed": False, "display": "separate_case_facets", "checks": checks,
            "interpretation": "Necessary metadata gate only; no physical equivalence or joint attainability certified."}


def build_comparison(instances: list[dict], *, fractions: list[float] | tuple = DEFAULT_FRACTIONS,
                     output_unit: str = "GPa", labels: dict[str, str] | None = None) -> dict:
    """Build an N-case second-phase fraction sweep from canonical engine results.

    Stable case IDs are input IDs; stable series IDs depend on case + claim IDs,
    not list order or language. Input fixtures are retained unchanged. Fractions
    are explicit chosen parameter values, never observations or sample counts.
    """
    if not isinstance(instances, list) or not 1 <= len(instances) <= 50:
        raise VisualizationError("instances: expected 1–50 cases")
    if not isinstance(fractions, (list, tuple)) or not 2 <= len(fractions) <= 501:
        raise VisualizationError("fractions: expected 2–501 increasing values")
    if any(not _number(x) or not 0 <= x <= 1 for x in fractions):
        raise VisualizationError("fractions: finite values in [0, 1] required")
    if any(a >= b for a, b in zip(fractions, fractions[1:])):
        raise VisualizationError("fractions: values must be strictly increasing and unique")
    if output_unit not in UNITS:
        raise VisualizationError("output_unit: expected Pa, kPa, MPa or GPa")
    labels = {} if labels is None else labels
    if not isinstance(labels, dict):
        raise VisualizationError("labels: expected a case-ID to text mapping")
    ids = set()
    for instance in instances:
        validate_instance(instance)
        if len(instance["phases"]) != 2:
            raise VisualizationError("fraction sweeps require exactly two declared phases")
        if instance["id"] in ids:
            raise VisualizationError("duplicate case ID")
        ids.add(instance["id"])
    if set(labels) - ids:
        raise VisualizationError("labels contains an unknown case ID")
    for label in labels.values():
        _text(label, "label")
    claims_catalog = read_catalog("claims")
    sources_catalog = read_catalog("sources")
    claim_records = {record["id"]: record for record in claims_catalog["records"]}
    used_claims, used_sources = set(), set()
    cases, series = [], []
    for instance in instances:
        case_id = instance["id"]
        context = _context(instance)
        phase_definition = deepcopy(instance["phases"])
        for phase in phase_definition:
            phase.pop("volume_fraction", None)
            for prop in ("bulk_modulus", "shear_modulus"):
                if phase.get(prop) is not None:
                    value = phase[prop]["value"]
                    if value is not None:
                        # Exact canonical Pa text also covers inputs too large for
                        # binary floats; the engine can report those as null gaps.
                        number = Decimal(str(value))
                        sign, digits, exponent = number.as_tuple()
                        number = Decimal((sign, digits, exponent + UNITS[phase[prop]["unit"]].adjusted()))
                        value = format(number, "f")
                        if "." in value:
                            value = value.rstrip("0").rstrip(".")
                    phase[prop] = {"value": value, "unit": "Pa"}
        case = {"id": case_id, "label": labels.get(case_id, case_id), "input": deepcopy(instance),
                "conditions": deepcopy(instance["conditions"]), "context": context,
                "input_provenance": deepcopy(instance["provenance"]), "phase_definition": phase_definition,
                "axis": {"quantity": "phase_volume_fraction", "unit": "1", "phase_id": instance["phases"][1]["id"],
                         "complement_phase_id": instance["phases"][0]["id"],
                         "definition": "second_declared_phase_fraction_f2; first_declared_phase_fraction=1-f2",
                         "basis": "calculator_selected_parameter_sweep"},
                "quantity_dimensions": {key: value[0] for key, value in QUANTITIES.items()},
                "units": {key: "1" if dim == "dimensionless" else output_unit for key, (dim, _) in QUANTITIES.items()},
                "unknown_context": [key for key, value in context.items() if value is None],
                "samples": []}
        by_claim = {}
        for index, fraction in enumerate(fractions):
            sample = deepcopy(instance)
            with localcontext(Context(prec=80)):
                sample["phases"][0]["volume_fraction"] = float(Decimal(1) - Decimal(str(fraction)))
            sample["phases"][1]["volume_fraction"] = fraction
            result = evaluate(sample, output_unit=output_unit)
            case["samples"].append({"id": "point-" + _id(case_id, str(fraction)), "x": fraction,
                                    "fractions": [p["volume_fraction"] for p in sample["phases"]],
                                    "evaluation": result})
            for item in result["evaluations"]:
                claim_id, quantity = item["claim_id"], item["quantity"]
                claim = claim_records[claim_id]
                used_claims.add(claim_id)
                used_sources.update(evidence["source_id"] for evidence in claim["evidence"])
                if claim_id not in by_claim:
                    by_claim[claim_id] = {"id": "series-" + _id(case_id, claim_id), "case_id": case_id,
                        "claim_id": claim_id, "claim_version": claim["version"], "rule_id": item["rule_id"],
                        "quantity": quantity, "dimension": QUANTITIES[quantity][0], "unit": case["units"][quantity],
                        "semantics": "derived_outer_envelope" if item["bound_kind"] == "derived_outer_envelope" else "theoretical_bound",
                        "direction": claim["direction"], "source_ids": [e["source_id"] for e in claim["evidence"]],
                        "points": []}
                numeric = item["result"]
                by_claim[claim_id]["points"].append({"x": fraction, "sample_index": index,
                    "lower": numeric.get("lower") if numeric else None,
                    "upper": numeric.get("upper") if numeric else None,
                    "applicability": item["applicability"], "computation": item["computation"]})
        used_sources.update(instance["provenance"].get("source_ids", []))
        cases.append(case)
        series.extend(by_claim.values())
    source_ids = {record["id"] for record in sources_catalog["records"]}
    return {"schema_version": SCHEMA_VERSION, "kind": "conditional_elastic_bound_comparison",
            "engine_version": __version__, "evaluation_schema_version": "1.1.0",
            "axis_values": list(fractions), "output_unit": output_unit,
            "policy": {"display": "separate_case_facets", "axis_alignment": "same_selected_fraction_values",
                       "interval_semantics": "conditional_theoretical_bounds_or_derived_outer_envelopes_not_confidence_intervals",
                       "sample_semantics": "chosen_parameter_values_not_observations",
                       "missing_values": "null_gap_no_interpolation_across_unavailable_points",
                       "numerical_policy": "canonical engine rounded outputs; not certified outward-rounded endpoints",
                       "scientific_verification": "software tests and equation cross-checks; not independent scientific peer review"},
            "cases": cases, "series": series,
            "compatibility": [compatibility_gate(a, b) for i, a in enumerate(cases) for b in cases[i + 1:]],
            "catalogs": {"claims": {"schema_version": claims_catalog["schema_version"],
                                     "records": [r for r in claims_catalog["records"] if r["id"] in used_claims]},
                         "sources": {"schema_version": sources_catalog["schema_version"],
                                      "records": [r for r in sources_catalog["records"] if r["id"] in used_sources]},
                         "unresolved_source_ids": sorted(used_sources - source_ids)}}


def validate_comparison(bundle: dict) -> None:
    """Fail closed on altered values, conditions, metadata, versions or claims.

    An import from a different engine/catalog release requires explicit migration,
    not silent relabeling. JSON Schema alone does not establish provenance.
    """
    try:
        if not isinstance(bundle, dict) or bundle.get("schema_version") != SCHEMA_VERSION:
            raise VisualizationError("unsupported comparison schema")
        cases = bundle["cases"]
        rebuilt = build_comparison([case["input"] for case in cases], fractions=bundle["axis_values"],
                                   output_unit=bundle["output_unit"], labels={case["id"]: case["label"] for case in cases})
        if _json(rebuilt) != _json(bundle):
            raise VisualizationError("comparison does not reproduce with current engine/catalog; altered or stale bundle")
    except (KeyError, TypeError, ValidationError, OverflowError) as exc:
        raise VisualizationError("invalid comparison bundle") from exc


def comparison_json(bundle: dict) -> str:
    validate_comparison(bundle)
    return _json(bundle, pretty=True) + "\n"


def _locale(lang: str) -> dict:
    locales = json.loads(files("materials_boundaries").joinpath("data", "visualization_locales.json").read_text(encoding="utf-8"))
    if lang not in locales:
        raise VisualizationError("lang: expected en, zh, ja or de")
    return locales[lang]


def _runs(points: list[dict], keys: tuple[str, ...]) -> list[list[dict]]:
    """Contiguous finite computed runs; unavailable points are never bridged."""
    result, run = [], []
    for point in points:
        valid = (point["applicability"] == "satisfied" and point["computation"] == "computed"
                 and all(_number(point.get(key)) for key in keys))
        if valid:
            run.append(point)
        elif run:
            result.append(run)
            run = []
    if run:
        result.append(run)
    return result


def _fmt(value: float) -> str:
    return "0" if value == 0 else format(value, ".4g")


def _domain(bundle: dict, quantity: str, include_classical: bool) -> tuple[Decimal, Decimal]:
    values = [value for series in bundle["series"] if series["quantity"] == quantity
              and (include_classical or series["direction"] == "interval") for point in series["points"]
              for key in ("lower", "upper") if (value := point[key]) is not None]
    if not values:
        return Decimal(0), Decimal(1)
    low, high = Decimal(str(min(values))), Decimal(str(max(values)))
    padding = (high - low) * Decimal("0.08") if high != low else (abs(low) * Decimal("0.08") if low else Decimal("0.01"))
    floor = max(Decimal(0), low - padding) if QUANTITIES[quantity][0] == "pressure" else low - padding
    return floor, high + padding


def _svg(bundle: dict, case: dict, quantity: str, lang: str, width: int,
         include_classical: bool) -> str:
    with localcontext(Context(prec=80)):
        return _svg_decimal(bundle, case, quantity, lang, width, include_classical)


def _svg_decimal(bundle: dict, case: dict, quantity: str, lang: str, width: int,
                 include_classical: bool) -> str:
    labels = _locale(lang)
    height = 330 if width >= 500 else 310
    left, right, top, bottom = 68, width - 18, 42, height - 60
    ymin, ymax = _domain(bundle, quantity, include_classical)
    xmin, xmax = bundle["axis_values"][0], bundle["axis_values"][-1]
    x = lambda value: left + (value - xmin) / (xmax - xmin) * (right - left)
    y = lambda value: bottom - float((Decimal(str(value)) - ymin) / (ymax - ymin)) * (bottom - top)
    title = f'{labels[quantity]} ({case["units"][quantity]})'
    desc = f'{case["label"]}. {labels["band_note"]} {labels["gaps"]}'
    sid = _id(case["id"], quantity, str(width), lang)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t-{sid} d-{sid}" class="bound-chart">',
           f'<title id="t-{sid}">{escape(title)}</title><desc id="d-{sid}">{escape(desc)}</desc>',
           '<rect width="100%" height="100%" fill="#fff"/>',
           f'<text x="{left}" y="23" font-size="16" font-weight="600" fill="#173449">{escape(title)}</text>',
           f'<defs><clipPath id="clip-{sid}"><rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}"/></clipPath></defs>']
    ticks = 5 if width >= 500 else 4
    for index in range(ticks):
        frac = index / (ticks - 1)
        xv, yv = xmin + frac * (xmax - xmin), ymin + Decimal(str(frac)) * (ymax - ymin)
        px, py = x(xv), y(yv)
        out += [f'<line x1="{left}" y1="{py:.3f}" x2="{right}" y2="{py:.3f}" stroke="#dce5e9"/>',
                f'<text x="{left-9}" y="{py+4:.3f}" text-anchor="end" font-size="13" fill="#294650">{escape(_fmt(yv))}</text>',
                f'<text x="{px:.3f}" y="{bottom+23}" text-anchor="middle" font-size="13" fill="#294650">{escape(_fmt(xv))}</text>']
    out += [f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="none" stroke="#607781"/>',
            f'<text x="{(left+right)/2}" y="{height-12}" text-anchor="middle" font-size="14" fill="#173449">{escape(labels["axis_short"])}</text>']
    selected = [s for s in bundle["series"] if s["case_id"] == case["id"] and s["quantity"] == quantity
                and (include_classical or s["direction"] == "interval")]
    has_values = False
    for series in selected:
        color = "#087f8c" if series["direction"] == "interval" else "#ac4d18" if series["direction"] == "lower" else "#6948a8"
        out.append(f'<g data-series-id="{series["id"]}" clip-path="url(#clip-{sid})">')
        if series["direction"] == "interval":
            for run in _runs(series["points"], ("lower", "upper")):
                has_values = True
                coords = [(x(p["x"]), y(p["lower"])) for p in run] + [(x(p["x"]), y(p["upper"])) for p in reversed(run)]
                out.append('<polygon points="' + " ".join(f"{a:.3f},{b:.3f}" for a, b in coords) + f'" fill="{color}" fill-opacity="0.18" data-band-semantics="{series["semantics"]}"/>')
        keys = ("lower", "upper") if series["direction"] == "interval" else (series["direction"],)
        for key in keys:
            for run in _runs(series["points"], (key,)):
                has_values = True
                points = " ".join(f'{x(p["x"]):.3f},{y(p[key]):.3f}' for p in run)
                dash = "" if series["direction"] == "interval" else ' stroke-dasharray="7 4"' if key == "lower" else ' stroke-dasharray="2 4"'
                out.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"{dash} data-endpoint="{key}"/>')
                # Dots encode evaluated parameter points, not measured observations.
                for p in run:
                    out.append(f'<circle cx="{x(p["x"]):.3f}" cy="{y(p[key]):.3f}" r="2.1" fill="{color}"/>')
        out.append('</g>')
    if not has_values:
        out.append(f'<text x="{(left+right)/2}" y="{(top+bottom)/2}" text-anchor="middle" font-size="14" fill="#5f676b">{escape(labels["no_values"])}</text>')
    out.append('</svg>')
    return "\n".join(out)


def render_svg(bundle: dict, case_id: str, quantity: str = "effective_bulk_modulus", *,
               lang: str = "en", width: int = 560, include_classical: bool = True) -> str:
    """Render one case/quantity; common quantity domains keep case facets aligned."""
    validate_comparison(bundle)
    if quantity not in QUANTITIES:
        raise VisualizationError("unsupported quantity")
    if not isinstance(width, int) or isinstance(width, bool) or not 300 <= width <= 1600:
        raise VisualizationError("width must be an integer from 300 to 1600")
    case = next((c for c in bundle["cases"] if c["id"] == case_id), None)
    if case is None:
        raise VisualizationError("unknown case ID")
    return _svg(bundle, case, quantity, lang, width, include_classical)


def render_html(bundle: dict, *, lang: str = "en", include_classical: bool = True) -> str:
    """Render a self-contained, no-script document with traceability tables."""
    validate_comparison(bundle)
    labels = _locale(lang)
    esc = escape
    out = [f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
           '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:; base-uri \'none\'; form-action \'none\'">',
           f'<title>{esc(labels["title"])}</title>',
           '<style>body{font:16px/1.55 system-ui,sans-serif;color:#173449;background:#f7fafb;margin:0}main{max-width:1140px;margin:auto;padding:30px 20px}h1{font-size:clamp(26px,4vw,38px);line-height:1.15;margin:8px 0 14px}h2{font-size:23px;margin:35px 0 6px}h3{font-size:18px}p{max-width:85ch}.eyebrow{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#52656f}.note{border-left:4px solid #087f8c;padding-left:14px}.warning{color:#80390e}.charts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}figure{margin:0}svg{width:100%;height:auto;display:block}.mobile{display:none}.legend{display:flex;flex-wrap:wrap;gap:8px 22px;font-size:14px;margin:12px 0 18px}.legend span:before{content:"";display:inline-block;width:24px;border-top:3px solid #087f8c;vertical-align:middle;margin-right:6px}.legend .reuss:before{border-color:#ac4d18;border-top-style:dashed}.legend .voigt:before{border-color:#6948a8;border-top-style:dotted}details{margin:16px 0}summary{cursor:pointer;font-weight:600;padding:8px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.45 monospace;background:#edf3f6;padding:14px}table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:7px;text-align:left;border-bottom:1px solid #d9e3e7;overflow-wrap:anywhere}code{overflow-wrap:anywhere}.table-scroll{overflow-x:auto}li{margin:4px 0}.muted{color:#52656f}footer{border-top:1px solid #cbd8de;padding-top:15px;font-size:14px} @media(max-width:650px){main{padding:20px 12px}.charts{grid-template-columns:1fr;gap:14px}.desktop{display:none}.mobile{display:block}h2{font-size:21px}table{font-size:13px}td,th{padding:5px}}</style></head><body><main>',
           f'<div class="eyebrow">Materials Boundaries · v{esc(bundle["engine_version"])}</div>',
           f'<h1>{esc(labels["title"])}</h1><p class="note">{esc(labels["intro"])}</p>',
           f'<p>{esc(labels["band_note"])} {esc(labels["derived_note"])}</p>',
           f'<p class="muted">{esc(labels["axis_note"])} {esc(labels["gaps"])}</p>']
    for case in bundle["cases"]:
        out += [f'<section aria-labelledby="case-{_id(case["id"])}"><h2 id="case-{_id(case["id"])}">{esc(case["label"])}</h2>',
                f'<p>{esc(labels["input_kind"])}: <strong>{esc(labels["kind_" + case["input_provenance"]["kind"]])}</strong><br>',
                f'{esc(labels["axis_phase"])}: <code>{esc(case["axis"]["phase_id"])}</code>; {esc(labels["complement"])}: <code>{esc(case["axis"]["complement_phase_id"])}</code></p>',
                f'<p class="warning">{esc(labels["unknown_context"])}: {esc(", ".join(labels["context_" + key] for key in case["unknown_context"])) or esc(labels["none"])}. {esc(labels["facets_note"])}</p>',
                f'<div class="legend"><span>{esc(labels["hs_legend"])}</span>']
        if include_classical:
            out += [f'<span class="reuss">{esc(labels["reuss_legend"])}</span><span class="voigt">{esc(labels["voigt_legend"])}</span>']
        out.append('</div><div class="charts">')
        for quantity in QUANTITIES:
            out += ['<figure><div class="desktop">', _svg(bundle, case, quantity, lang, 550, include_classical),
                    '</div><div class="mobile">', _svg(bundle, case, quantity, lang, 340, include_classical), '</div>',
                    f'<figcaption class="muted">{esc(labels["derived_caption"] if quantity in list(QUANTITIES)[2:] else labels["bound_caption"])}</figcaption></figure>']
        out.append('</div>')
        out += [f'<details><summary>{esc(labels["values"])}</summary><p>{esc(labels["table_note"])}</p><div class="table-scroll"><table><thead><tr><th>f₂</th>']
        for quantity in QUANTITIES:
            out.append(f'<th>{esc(QUANTITIES[quantity][1])} ({esc(case["units"][quantity])})</th>')
        out.append('</tr></thead><tbody>')
        by_quantity = {s["quantity"]: s for s in bundle["series"] if s["case_id"] == case["id"] and s["direction"] == "interval"}
        for i, value in enumerate(bundle["axis_values"]):
            out.append(f'<tr><td>{_fmt(value)}</td>')
            for quantity in QUANTITIES:
                point = by_quantity[quantity]["points"][i]
                label = f'{_fmt(point["lower"])} – {_fmt(point["upper"])}' if point["lower"] is not None and point["upper"] is not None else f'{labels["gap"]} ({point["applicability"]}; {point["computation"]})'
                out.append(f'<td>{esc(label)}</td>')
            out.append('</tr>')
        out += ['</tbody></table></div></details>',
                f'<details><summary>{esc(labels["traceability"])}</summary><p>{esc(labels["trace_note"])}</p>',
                '<pre>' + esc(_json({key: case[key] for key in ("id", "input", "conditions", "context", "axis")}, pretty=True)) + '</pre></details></section>']
    out += [f'<details><summary>{esc(labels["compatibility"])}</summary><p>{esc(labels["facets_note"])}</p><pre>{esc(_json(bundle["compatibility"], pretty=True))}</pre></details>',
            f'<details><summary>{esc(labels["sources"])}</summary><pre>{esc(_json(bundle["catalogs"], pretty=True))}</pre></details>',
            f'<footer><p>{esc(labels["footer"])}</p><p>{esc(labels["bundle_note"])}</p></footer></main>',
            # JSON is inert; escape HTML-significant characters to prevent closing-tag injection.
            '<script type="application/json" id="comparison-bundle">' + _json(bundle).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e") + '</script>',
            '</body></html>']
    return "\n".join(out)
