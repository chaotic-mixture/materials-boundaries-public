"""Presentation-only catalog views; never translate or rewrite source records."""
from functools import lru_cache
import json

from .catalog import read_catalog
from .i18n import translate


def render_catalog(catalog: dict, kind: str, language: str = "en") -> str:
    """Render canonical records with localized labels and original source text."""
    if kind == "predictions":
        from .predictions import render_predictions
        return render_predictions(catalog, language)
    if kind == "observations":
        from ._observation_contract import validate_mos2_records
        validate_mos2_records(catalog["records"])
    if kind == "claims":
        from ._compressibility_contract import validate_compressibility_records
        from ._directional_contract import validate_directional_records
        validate_compressibility_records(catalog["records"])
        validate_directional_records(catalog["records"])
        # Filtered output may omit its definition dependency. Resolve it against
        # the packaged catalog plus the supplied records; fresh paired records
        # are supported when their fresh definition is supplied in the subset.
        definitions = {record["id"]: record for record in read_catalog("claims")["records"]}
        definitions.update({record["id"]: record for record in catalog["records"]})
        validate_directional_records(list(definitions.values()), resolve_dependencies=True)
        validate_compressibility_records(list(definitions.values()), resolve_dependencies=True)
    @lru_cache(maxsize=None)
    def t(key: str) -> str:
        return translate(key, language)

    def status(value: str | None) -> str:
        if value is None:
            return t("unknown")
        # Unknown future codes stay visible rather than acquiring an invented label.
        key = "catalog_status_" + value
        label = t(key)
        return value if label == f"[missing:{key}]" else f"{label} [{value}]"

    def value_or_unknown(value: object) -> str:
        return t("unknown") if value is None else str(value)

    def field(label: str, value: object, indent: str = "  ") -> str:
        return f"{indent}{t(label)}: {value_or_unknown(value)}"

    def source_summary(source: dict, indent: str = "  ") -> list[str]:
        return [
            field("catalog_original_title", source["title"], indent),
            f'{indent}DOI: {value_or_unknown(source["doi"])}',
            field("catalog_role", status(source["role"]), indent),
            field("catalog_read_status", status(source["read_status"]), indent),
            field("catalog_license_status", status(source["license"]["status"]), indent),
            field("catalog_license_id", source["license"]["identifier"], indent),
        ]

    lines = [t("catalog_" + kind), field("catalog_count", len(catalog["records"]), "")]
    if not catalog["records"]:
        lines.append(t("catalog_empty"))
    sources = {source["id"]: source for source in read_catalog("sources")["records"]} if kind in {"claims", "observations"} else {}
    for record in catalog["records"]:
        lines.extend(["", f'{t({"claims": "claim", "sources": "source", "observations": "observation"}[kind])}: {record["id"]}'])
        if kind == "sources":
            lines.extend(source_summary(record))
            lines.extend([
                field("catalog_authors", "; ".join(record["authors"])),
                field("catalog_year", record["year"]),
                field("catalog_urls", " ".join(record["urls"])),
                field("catalog_bundled_content", status(record["bundled_content"])),
                field("catalog_curation_date", record["provenance"]["curation_date"]),
                field("catalog_method", record["provenance"]["method"]),
                field("catalog_notes", ""),
            ])
            lines.extend("    - " + note for note in record["claim_notes"])
        elif kind == "observations":
            name_key = "catalog_name_" + record["id"]
            display_name = t(name_key)
            if display_name != f"[missing:{name_key}]":
                lines.append(field("catalog_display_name", display_name))
            result, material, method = record["reported_result"], record["material"], record["method"]
            uncertainty = result["uncertainty"]
            mos2 = record.get("method_family") == "bertolazzi_2011_mos2_monolayer_indentation_v1"
            if mos2:
                # Disclose the unresolved source model before the numerical result.
                q = method["q_source_report"]
                lines.extend([
                    "  " + t("catalog_mos2_model_notice"),
                    field("catalog_model_status", status(record["model_status"])),
                    field("catalog_q_formula", q["formula_as_printed"]),
                    field("catalog_q_nu", q["nu_as_printed"]),
                    field("catalog_q_reported", q["q_as_printed"]),
                    field("catalog_q_arithmetic", q["audit_arithmetic_value"]),
                    field("catalog_q_used", q["fit_constant_actually_used"]),
                    field("catalog_locator", q["locator"]),
                    "  " + t("catalog_mos2_source_notice"),
                ])
            lines.extend([
                field("catalog_original_name", record["name"]),
                field("catalog_version", record["version"]),
                field("catalog_study_id", record["study_id"]),
                field("catalog_observation_type", status(record["observation_type"])),
                field("catalog_quantity", status(record["quantity"])),
                field("catalog_quantity_dimension", status(record["quantity_dimension"])),
                field("catalog_si_unit", record["si_unit"]),
                field("catalog_evaluation_support", status(record["evaluation_support"])),
                "  " + t("catalog_observation_notice"),
                field("catalog_material", material["name"]),
                field("catalog_dimensionality", material["dimensionality"]),
                field("catalog_layer_count", material["layer_count"]),
                field("catalog_specimen_form", status(material["specimen_form"])),
                field("catalog_preparation", status(material["preparation"])),
                field("catalog_monolayer_identification", "; ".join(status(value) for value in material["monolayer_identification"])),
                field("catalog_span_diameters", f'{", ".join(str(value) for value in material["suspended_span_diameters"]["values"])} {material["suspended_span_diameters"]["unit"]}'),
                field("catalog_reported_result", f'{result["value"]} ± {uncertainty["value"]} {result["unit"]}'),
                field("catalog_uncertainty_type", status(uncertainty["type"])),
                field("catalog_coverage_factor", uncertainty["coverage_factor"]),
                field("catalog_confidence_level", uncertainty["confidence_level"]),
                "  " + t("catalog_sd_notice" if mos2 else "catalog_reported_uncertainty_notice"),
                field("catalog_uncertainty_interpretation", uncertainty["interpretation"]),
                field("catalog_measurement_method", status(method["technique"])),
                field("catalog_inference", method["inference"]),
                field("catalog_poissons_ratio_assumed", method["poissons_ratio_assumed"]),
                field("catalog_stress_measure", status(method["stress_measure"])),
                field("catalog_strain_measure", status(method["strain_measure"])),
                field("catalog_model_assumptions", ""),
            ])
            lines.extend("    - " + assumption for assumption in method["model_assumptions"])
            if mos2:
                lines.extend([
                    field("catalog_preparation_notes", material["preparation_notes"]),
                    field("catalog_geometry_tolerance", material["suspended_span_diameters"]["reported_value_string"]),
                    field("catalog_tip_radius", method["tip_radius"]["reported_value_string"]),
                    "  " + t("catalog_geometry_uncertainty_notice"),
                    field("catalog_averaging_convention", uncertainty["averaging_convention"]),
                    field("catalog_stress_strain_status", method["stress_strain_measure_status"]),
                ])
            lines.append(field("catalog_conditions", ""))
            for key in ("temperature", "atmosphere", "humidity", "loading_rate"):
                value = record["conditions"][key]
                if mos2 and key == "loading_rate":
                    lines.append(field("catalog_probe_speed", f'{value["value"]} {value["unit"]}', "    "))
                    lines.append("    " + t("catalog_probe_speed_notice"))
                    lines.append(field("catalog_locator", value["locator"], "    "))
                else:
                    lines.append(field("catalog_" + key, value, "    "))
            if mos2:
                lines.extend("    - " + note for note in record["conditions"]["notes"])
            sample = record["sample_metadata"]
            lines.append(field("catalog_sample_metadata", None if sample is None else ""))
            if sample is not None:
                lines.append(field("catalog_sample_scope", status(sample["scope"]), "    "))
                if mos2:
                    for key, label in (("study_monolayer_membranes", "catalog_study_monolayer_count"),
                                       ("force_displacement_curves", "catalog_curve_count"),
                                       ("distinct_parent_flakes", "catalog_parent_flake_count"),
                                       ("failure_events", "catalog_failure_count")):
                        lines.append(field(label, sample["counts"][key], "    "))
                    if "membranes_explicitly_associated_with_stiffness_average" in sample["counts"]:
                        lines.append(field("catalog_stiffness_membrane_count", sample["counts"]["membranes_explicitly_associated_with_stiffness_average"], "    "))
                    lines.append(field("catalog_locator", sample["locator"], "    "))
                else:
                    for key, label in (("force_displacement_fits", "catalog_fit_count"), ("membranes", "catalog_membrane_count"), ("flakes", "catalog_flake_count")):
                        lines.append(field(label, sample["counts"][key], "    "))
                    for key, label in (("mean", "catalog_distribution_mean"), ("standard_deviation", "catalog_distribution_sd")):
                        lines.append(field(label, f'{sample["fitted_distribution"][key]} {sample["fitted_distribution"]["unit"]}', "    "))
                lines.extend("    - " + note for note in sample["notes"])
            verification = record["verification"]
            lines.extend([
                field("catalog_observation_verification", status(verification["status"])),
                field("catalog_independent_review", t("catalog_yes" if verification["independent_scientific_review"] else "catalog_no")),
                field("catalog_gaps", ""),
            ])
            if mos2:
                lines.append("  " + t("catalog_mos2_transcription_notice"))
            lines.extend("    - " + gap for gap in verification["gaps"])
            lines.append(field("catalog_observation_evidence", ""))
            for evidence in record["evidence"]:
                lines.append(field("source", evidence["source_id"], "    "))
                if mos2:
                    lines.append(field("catalog_urls", evidence["source_url"], "      "))
                source = sources.get(evidence["source_id"])
                if source is not None:
                    lines.extend(source_summary(source, "      "))
                lines.extend([
                    field("catalog_evidence_status", status(evidence["verification_status"]), "      "),
                    field("catalog_locator", evidence["locator"], "      "),
                    field("catalog_verified_as", evidence["verified_as"], "      "),
                ])
            lines.append(field("catalog_limits", ""))
            lines.extend("    - " + limit for limit in record["limits"])
            lines.append("  " + t("catalog_observation_compatibility_notice"))
        else:
            name_key = "catalog_name_" + record["id"]
            display_name = t(name_key)
            if display_name != f"[missing:{name_key}]":
                lines.append(field("catalog_display_name", display_name))
            lines.extend([
                field("catalog_original_name", record["name"]),
                field("catalog_version", record["version"]),
                field("catalog_claim_type", status(record["claim_type"])),
                field("catalog_quantity", status(record["quantity"])),
                field("catalog_quantity_dimension", status(record["quantity_dimension"])),
                field("catalog_si_unit", record["si_unit"] if record["si_unit"] is not None else t("catalog_not_applicable")),
                field("catalog_evaluation_support", status(record["evaluation_support"])),
                field("catalog_bound_kind", status(record["bound_kind"]) if record["bound_kind"] is not None else t("catalog_not_applicable")),
                field("catalog_dependencies", json.dumps(record["dependencies"], ensure_ascii=False)),
                field("catalog_direction", status(record["direction"])),
                field("rule", record["rule_id"]),
                field("catalog_formula", record["formula_display"]),
            ])
            if record["evaluation_support"] == "catalog_only":
                notice = ("catalog_compressibility_notice" if "hydrostatic_compressibility_contract" in record
                          else "catalog_directional_notice" if "directional_contract" in record
                          else "catalog_index_notice" if "index_range" in record
                          else "catalog_criterion_notice" if record["claim_type"] == "stability_criterion"
                          else "catalog_bound_notice" if record["claim_type"] in {"theoretical_bound", "derived_outer_envelope"}
                          else "catalog_model_notice")
                lines.append("  " + t(notice))
            if "hydrostatic_compressibility_contract" in record:
                contract = record["hydrostatic_compressibility_contract"]
                for key in ("conditions", "fixed_tensor", "range", "energy", "symmetry", "limits"):
                    lines.append("  " + t("catalog_compressibility_" + key))
                lines.append("    hydrostatic_compressibility_contract: " + json.dumps(
                    contract, ensure_ascii=False, allow_nan=False))
            if "directional_contract" in record:
                contract = record["directional_contract"]
                lines.append("  " + t("catalog_directional_conditions"))
                if contract["kind"] == "definition_and_material_class_range":
                    lines.append("  " + t("catalog_directional_range"))
                    lines.append("  " + t("catalog_directional_fixed_tensor"))
                else:
                    lines.append("  " + t("catalog_directional_pair"))
                lines.append("  " + t("catalog_directional_limits"))
                lines.append("    directional_contract: " + json.dumps(contract, ensure_ascii=False, allow_nan=False))
            if "index_range" in record:
                index_range = record["index_range"]
                lower = index_range["lower"]
                left = "[" if lower["inclusive"] else "("
                lines.append(field("catalog_index_range", f'{left}{lower["value"]}, infinity); {t("catalog_index_upper_unbounded")}'))
                lines.append(field("catalog_index_isotropy", f'{index_range["isotropy"]["value"]}; {index_range["isotropy"]["condition"]}'))
                lines.append(f'    basis: {index_range["basis"]}')
            if "parameters" in record:
                lines.append(field("catalog_parameters", ""))
                for parameter in record["parameters"]:
                    lines.append(f'    {parameter["symbol"]}: {parameter["quantity"]}; {status(parameter["dimension"])}; {parameter["si_unit"]}; {parameter["meaning"]}')
            if "criterion" in record:
                criterion = record["criterion"]
                lines.append(field("catalog_criterion_convention", ""))
                for key in ("voigt_order", "strain_vector", "stress_vector", "constitutive_relation", "energy_density", "combination", "strict_boundary"):
                    lines.append(f'    {key}: {json.dumps(criterion[key], ensure_ascii=False)}')
                lines.append(field("catalog_stiffness_matrix", ""))
                lines.extend("    " + json.dumps(row, ensure_ascii=False) for row in criterion["stiffness_matrix"])
                lines.append(field("catalog_inequalities", ""))
                for inequality in criterion["inequalities"]:
                    lines.append(f'    {inequality["expression"]} {inequality["operator"]} {inequality["rhs"]}; {status(inequality["dimension"])}; {inequality["si_unit"]}')
            lines.append(field("catalog_assumptions", ""))
            for condition, value in record["required_assumptions"].items():
                lines.append(f'    {condition}: {json.dumps(value, ensure_ascii=False, allow_nan=False)}')
            verification = record["verification"]
            lines.extend([
                field("catalog_verification", status(verification["status"])),
                field("catalog_independent_review", t("catalog_yes" if verification["independent_scientific_review"] else "catalog_no")),
                field("catalog_gaps", ""),
            ])
            lines.extend("    - " + gap for gap in verification["gaps"])
            lines.append(field("catalog_evidence", ""))
            for evidence in record["evidence"]:
                lines.append(field("source", evidence["source_id"], "    "))
                source = sources.get(evidence["source_id"])
                if source is not None:
                    lines.extend(source_summary(source, "      "))
                lines.extend([
                    field("catalog_evidence_status", status(evidence["verification_status"]), "      "),
                    field("catalog_locator", evidence["locator"], "      "),
                    field("catalog_verified_as", evidence["verified_as"], "      "),
                ])
            lines.append(field("catalog_limits", ""))
            lines.extend("    - " + limit for limit in record["limits"])
    lines.extend(["", t("catalog_original_notice"), t("catalog_evidence_notice"), t("translation_review_notice")])
    return "\n".join(lines)
