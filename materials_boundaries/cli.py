"""Data-first CLI; human labels can be localized, JSON identifiers stay stable."""
from __future__ import annotations

import argparse
import json
from functools import lru_cache, partial
import sys

from .catalog import CatalogLookupError, query_catalog
from .catalog_output import render_catalog
from .engine import evaluate
from .i18n import LANGUAGES, translate
from .validation import UNITS, ValidationError, load_json, validate_instance


def _render(result: dict, language: str) -> str:
    def t(key: str) -> str:
        return translate(key, language)
    def format_endpoint(value: float, quantity: str) -> str:
        # Round-trip Poisson text preserves the strict physical interval. A
        # fixed .12g could display an interior float as the excluded -1 or 0.5.
        return repr(value) if quantity == "effective_poissons_ratio" else f"{value:.12g}"

    lines = [t("summary_title"), f'{t("input_id")}: {result["instance_id"]}']
    for evaluation in result["evaluations"]:
        label = t({"hs_bulk_3d_two_phase": "hs_bulk", "reuss_bulk": "reuss_bulk", "voigt_bulk": "voigt_bulk",
                   "hs_shear_3d_two_phase": "hs_shear", "reuss_shear": "reuss_shear",
                   "voigt_shear": "voigt_shear", "youngs_modulus_outer": "youngs_modulus_outer",
                   "poissons_ratio_outer": "poissons_ratio_outer"}[evaluation["claim_id"]])
        value = evaluation["result"]
        if value is None:
            number = t("unavailable")
        elif "lower" in value and "upper" in value:
            number = f'{format_endpoint(value["lower"], evaluation["quantity"])} – {format_endpoint(value["upper"], evaluation["quantity"])} {value["unit"]}'
        else:
            side = "lower" if "lower" in value else "upper"
            number = f'{format_endpoint(value[side], evaluation["quantity"])} {value["unit"]}'
        lines.append(f'{label}: {number} ({t(evaluation["applicability"])})')
        for check in evaluation["checks"]:
            if check["state"] != "satisfied":
                lines.append(f'  {check["condition_id"]}: {t(check["state"])}')
        if evaluation["error"]:
            lines.append(f'  numerical_range_error: {evaluation["error"]}')
    lines.append(t("derived_outer_notice"))
    lines.append(t("poisson_range_notice"))
    lines.append(t("approximate_notice"))
    if result["input_provenance"]["kind"] == "synthetic":
        lines.append(t("synthetic_notice"))
    if result["input_provenance"]["kind"] == "literature_model":
        lines.append(t("literature_model_notice"))
    lines.append(t("verification_notice"))
    lines.append(t("translation_review_notice"))
    return "\n".join(lines)


class _LocalizedHelpFormatter(argparse.HelpFormatter):
    def __init__(self, *args, language: str = "en", **kwargs):
        self.language = language
        super().__init__(*args, **kwargs)

    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = translate("cli_usage", self.language)
        return super()._format_usage(usage, actions, groups, prefix)


class _LocalizedParser(argparse.ArgumentParser):
    def __init__(self, *args, language: str = "en", **kwargs):
        kwargs["add_help"] = False
        kwargs["formatter_class"] = partial(_LocalizedHelpFormatter, language=language)
        # Full option spellings keep query/filter parsing deterministic.
        kwargs["allow_abbrev"] = False
        super().__init__(*args, **kwargs)
        self._positionals.title = translate("cli_positionals", language)
        self._optionals.title = translate("cli_options", language)
        self.add_argument("-h", "--help", action="help", help=translate("cli_help", language))


def _build_parser(language: str) -> argparse.ArgumentParser:
    @lru_cache(maxsize=None)
    def t(key: str) -> str:
        return translate(key, language)

    parser = _LocalizedParser(description=t("cli_description"), language=language)

    def add_language(target):
        # Suppressing the subparser default preserves any root-level selection.
        target.add_argument("--lang", choices=LANGUAGES, default=argparse.SUPPRESS, help=t("cli_lang"))

    add_language(parser)
    sub = parser.add_subparsers(dest="command", required=True, title=t("cli_commands"),
                                parser_class=partial(_LocalizedParser, language=language))
    evaluate_parser = sub.add_parser("evaluate", help=t("cli_evaluate"), description=t("cli_evaluate"))
    evaluate_parser.add_argument("instance", help=t("cli_instance"))
    evaluate_parser.add_argument("--unit", choices=tuple(UNITS), default="GPa", help=t("cli_unit"))
    add_language(evaluate_parser)
    evaluate_parser.add_argument("--json", action="store_true", help=t("cli_json"))
    validate_parser = sub.add_parser("validate", help=t("cli_validate"), description=t("cli_validate"))
    validate_parser.add_argument("instance", help=t("cli_instance"))
    add_language(validate_parser)
    catalog_parser = sub.add_parser("catalog", help=t("cli_catalog"), description=t("cli_catalog"),
                                    epilog=t("cli_catalog_contract"))
    catalog_parser.add_argument("kind", choices=("claims", "sources", "observations", "predictions"), help=t("cli_kind"))
    add_language(catalog_parser)
    output = catalog_parser.add_mutually_exclusive_group()
    output.add_argument("--text", action="store_true", help=t("cli_text"))
    output.add_argument("--json", action="store_true", help=t("cli_json"))
    catalog_parser.add_argument("--id", dest="record_id", metavar="ID", help=t("cli_id"))
    catalog_parser.add_argument("--query", metavar="QUERY", help=t("cli_query"))
    catalog_parser.add_argument("--direction", choices=("interval", "lower", "upper", "prediction", "relation", "constraint"), help=t("cli_direction"))
    catalog_parser.add_argument("--claim-type", choices=("theoretical_bound", "derived_outer_envelope", "model_estimate", "model_relation", "stability_criterion"), help=t("cli_claim_type"))
    catalog_parser.add_argument("--source-id", metavar="ID", help=t("cli_source_id"))
    catalog_parser.add_argument("--quantity", metavar="QUANTITY", help=t("cli_observation_quantity"))
    catalog_parser.add_argument("--observation-type", choices=("experiment_derived_model_dependent", "experiment_derived_tensile_test_summary"), help=t("cli_observation_type"))
    catalog_parser.add_argument("--role", metavar="ROLE", help=t("cli_role"))
    catalog_parser.add_argument("--year", type=int, metavar="YEAR", help=t("cli_year"))
    catalog_parser.add_argument("--license", metavar="LICENSE", help=t("cli_license"))
    from .temperature_visualization import labels as temperature_labels
    tt = temperature_labels(language)
    temperature_parser = sub.add_parser("temperature", help=tt["command"], description=tt["command"])
    add_language(temperature_parser)
    temperature_sub = temperature_parser.add_subparsers(dest="temperature_command", required=True,
        parser_class=partial(_LocalizedParser, language=language))
    temperature_catalog = temperature_sub.add_parser("catalog", help=tt["catalog"])
    add_language(temperature_catalog)
    temperature_catalog.add_argument("--text", action="store_true", help=tt["text"])
    temperature_eval = temperature_sub.add_parser("evaluate", help=tt["evaluate"])
    add_language(temperature_eval)
    temperature_eval.add_argument("instance", help=tt["instance"])
    temperature_eval.add_argument("--json", action="store_true", help=tt["json"])
    temperature_plot = temperature_sub.add_parser("plot", help=tt["plot"])
    add_language(temperature_plot)
    temperature_plot.add_argument("--output", required=True, help=tt["output"])
    temperature_plot.add_argument("--points", type=int, default=101, help=tt["points"])
    from .predictions import DEFAULT_GROUP, prediction_labels
    pt = prediction_labels(language)
    prediction_parser = sub.add_parser("prediction", help=pt["command"], description=pt["command"])
    add_language(prediction_parser)
    prediction_sub = prediction_parser.add_subparsers(dest="prediction_command", required=True,
        parser_class=partial(_LocalizedParser, language=language))
    prediction_plot = prediction_sub.add_parser("plot", help=pt["plot"], description=pt["plot"])
    add_language(prediction_plot)
    prediction_plot.add_argument("--output", required=True, help=pt["output"])
    prediction_plot.add_argument("--group-id", default=DEFAULT_GROUP, help=pt["group"])
    from .observation_visualization import labels as observation_labels
    ot = observation_labels(language)
    observation_parser = sub.add_parser("observation", help=ot["command"], description=ot["command"])
    add_language(observation_parser)
    observation_sub = observation_parser.add_subparsers(dest="observation_command", required=True,
        parser_class=partial(_LocalizedParser, language=language))
    observation_inspect = observation_sub.add_parser("inspect", help=ot["inspect"], description=ot["inspect"])
    add_language(observation_inspect)
    observation_inspect.add_argument("--output", required=True, help=ot["output"])
    observation_inspect.add_argument("--id", dest="record_ids", action="append", metavar="ID", help=ot["id"])
    observation_inspect.add_argument("--source-id", metavar="ID", help=ot["source_id"])
    observation_inspect.add_argument("--quantity", metavar="QUANTITY", help=ot["quantity"])
    observation_inspect.add_argument("--group-by", choices=("study", "quantity"), default="study", help=ot["group_by"])
    from ._observation_temperature_labels import labels as observation_temperature_labels
    opt = observation_temperature_labels(language)
    observation_temperature = observation_sub.add_parser(
        "plot-temperature", help=opt["plot_temperature"], description=opt["plot_temperature"])
    add_language(observation_temperature)
    observation_temperature.add_argument(
        "--dataset-id", required=True,
        choices=("ciganas-2026-pa12-cf15-fff-uts-temperature",), help=opt["dataset_id"])
    observation_temperature.add_argument("--output", required=True, help=opt["output"])
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Select the help language before argparse's help action exits. The real
    # parser still validates all syntax and unsupported language codes.
    language_parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    language_parser.add_argument("--lang", choices=LANGUAGES, default="en")
    language, _ = language_parser.parse_known_args(argv)
    parser = _build_parser(language.lang)
    args = parser.parse_args(argv)
    if not hasattr(args, "lang"):
        args.lang = "en"
    try:
        if args.command == "observation":
            if args.observation_command == "plot-temperature":
                from .observation_temperature_plot import export_observation_temperature_plot
                artifacts = export_observation_temperature_plot(
                    args.output, dataset_id=args.dataset_id, lang=args.lang)
                print(json.dumps({"output": args.output, "artifacts": artifacts}, ensure_ascii=False))
                return 0
            from .observation_visualization import export_observation_inspection
            artifacts = export_observation_inspection(
                args.output, record_ids=args.record_ids, source_id=args.source_id,
                quantity=args.quantity, group_by=args.group_by, lang=args.lang)
            print(json.dumps({"output": args.output, "artifacts": artifacts}, ensure_ascii=False))
            return 0
        if args.command == "prediction":
            from .prediction_visualization import export_prediction_comparison
            artifacts = export_prediction_comparison(args.output, lang=args.lang, group_id=args.group_id)
            print(json.dumps({"output":args.output,"artifacts":artifacts}, ensure_ascii=False))
            return 0
        if args.command == "temperature":
            from .catalog import read_catalog
            from .temperature import evaluate_temperature, render_prediction, validate_model_catalog
            from .temperature_visualization import export_temperature_comparison
            if args.temperature_command == "catalog":
                catalog = validate_model_catalog(read_catalog("temperature_models"))
                print("\n".join(r["id"] + ": " + r["descriptions"][args.lang] for r in catalog["records"]) if args.text else json.dumps(catalog, ensure_ascii=False, indent=2, allow_nan=False))
            elif args.temperature_command == "evaluate":
                result = evaluate_temperature(load_json(args.instance))
                print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) if args.json else render_prediction(result, args.lang))
            else:
                artifacts = export_temperature_comparison(args.output, lang=args.lang, points_per_branch=args.points)
                print(json.dumps({"output":args.output,"artifacts":artifacts}, ensure_ascii=False))
            return 0
        if args.command == "catalog":
            try:
                catalog = query_catalog(args.kind, record_id=args.record_id, query=args.query,
                                        direction=args.direction, claim_type=args.claim_type, source_id=args.source_id,
                                        role=args.role, year=args.year, license=args.license,
                                        quantity=args.quantity, observation_type=args.observation_type)
            except CatalogLookupError as exc:
                print(json.dumps({"error": "catalog_id_not_found", "detail": str(exc)}, ensure_ascii=False), file=sys.stderr)
                return 2
            except ValueError as exc:
                print(json.dumps({"error": "invalid_catalog_query", "detail": str(exc)}, ensure_ascii=False), file=sys.stderr)
                return 2
            print(render_catalog(catalog, args.kind, args.lang) if args.text else
                  json.dumps(catalog, ensure_ascii=False, indent=2, allow_nan=False))
            return 0
        instance = load_json(args.instance)
        validate_instance(instance)
        if args.command == "validate":
            # A successful structural check deliberately makes no scientific assertion.
            print(f'{translate("input_id", args.lang)}: {instance["id"]}\n{translate("validation", args.lang)}: {translate("valid", args.lang)}')
            return 0
        result = evaluate(instance, output_unit=args.unit)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) if args.json else _render(result, args.lang))
        if any(item["computation"] == "numerical_range_error" for item in result["evaluations"]):
            return 3
        return 0
    except (ValidationError, OSError) as exc:
        print(json.dumps({"error": "invalid_input", "detail": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
