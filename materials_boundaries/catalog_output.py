"""Presentation-only catalog views; never translate or rewrite source records."""
from functools import lru_cache
import json

from .catalog import read_catalog
from .i18n import _catalog_translation_lookup
from ._paht_cf_observation_contract import PAHT_FAMILY, validate_paht_sources
from ._paht_observation_labels import PAHT_LABELS, PAHT_CAVEATS


def render_catalog(catalog: dict, kind: str, language: str = "en") -> str:
    """Render canonical records with localized labels and original source text."""
    if kind in {"materials", "reference-properties"}:
        from .material_presentation import render_material_catalog
        return render_material_catalog(catalog, kind, language)
    if kind == "predictions":
        from .predictions import render_predictions
        return render_predictions(catalog, language)
    if kind == "observations":
        from ._observation_contract import validate_observation_records
        validate_observation_records(catalog["records"])
    if kind == "claims":
        from ._yield_contract import validate_yield_records
        from ._viscoelastic_contract import validate_viscoelastic_records
        from ._wave_contract import validate_wave_records
        from ._compressibility_contract import validate_compressibility_records
        from ._directional_contract import validate_directional_records
        validate_wave_records(catalog["records"])
        validate_yield_records(catalog["records"])
        validate_viscoelastic_records(catalog["records"])
        validate_compressibility_records(catalog["records"])
        validate_directional_records(catalog["records"])
        # Filtered output may omit its definition dependency. Resolve it against
        # the packaged catalog plus the supplied records; fresh paired records
        # are supported when their fresh definition is supplied in the subset.
        definitions = {record["id"]: record for record in read_catalog("claims")["records"]}
        definitions.update({record["id"]: record for record in catalog["records"]})
        validate_yield_records(list(definitions.values()), resolve_dependencies=True)
        validate_viscoelastic_records(list(definitions.values()), resolve_dependencies=True)
        validate_directional_records(list(definitions.values()), resolve_dependencies=True)
        validate_compressibility_records(list(definitions.values()), resolve_dependencies=True)
    lookup = _catalog_translation_lookup(language)

    @lru_cache(maxsize=None)
    def t(key: str) -> str:
        return lookup(key)

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

    def pa12_observation(record: dict) -> list[str]:
        """Dedicated 3D tensile-summary display; no membrane conversion path."""
        result = record["reported_result"]
        uncertainty = result["uncertainty"]
        temperature = record["conditions"]["temperature"]
        si = record["si_result"]
        if record["study_id"] not in sources:
            raise ValueError("PA12 observation contract: missing referenced source")
        rendered = [
            field("catalog_original_name", record["name"]),
            field("catalog_version", record["version"]),
            field("catalog_study_id", record["study_id"]),
            "  " + t("catalog_pa12_classification"),
            "  " + t("catalog_pa12_identity"),
            field("catalog_pa12_dataset", record["dataset_id"]),
            field("catalog_pa12_protocol", record["protocol_id"]),
            field("catalog_quantity", record["quantity"]),
            field("catalog_quantity_dimension", record["quantity_dimension"]),
            "  " + t("catalog_pa12_temperature"),
            field("catalog_temperature", f'{temperature["value_string"]} °C [{temperature["basis"]}]'),
            "  " + t("catalog_pa12_process"),
            "  " + t("catalog_pa12_stress"),
            "  " + t("catalog_pa12_sample"),
            field("catalog_pa12_reported", f'{result["value_string"]} ± {uncertainty["value_string"]} MPa'),
            field("catalog_pa12_si", f'{int(si["value"])} ± {int(si["uncertainty_value"])} Pa'),
            "  " + t("catalog_pa12_normalization"),
            field("catalog_pa12_cell", json.dumps(record["source_cell"], ensure_ascii=False, sort_keys=True)),
            "  " + t("catalog_pa12_source_version"),
            "  " + t("catalog_pa12_rights"),
            field("catalog_pa12_details", ""),
        ]
        # All source-specific process, geometry, unknowns, counts, component
        # evidence and rights remain visible. Keys and source metadata are
        # language-neutral; authored warnings/labels above are localized.
        for key in ("material", "method", "conditions", "sample_metadata",
                    "reported_result", "si_result", "verification", "evidence", "limits"):
            rendered.append("    " + key + ": " + json.dumps(record[key], ensure_ascii=False, sort_keys=True))
        rendered.extend(source_summary(sources[record["study_id"]], "    "))
        rendered.append("    " + json.dumps(sources[record["study_id"]], ensure_ascii=False, sort_keys=True))
        return rendered

    def paht_observation(record: dict) -> list[str]:
        """The source median and SD keep separate labels and unit evidence."""
        wording = PAHT_LABELS[language]
        result, si = record['reported_result'], record['si_result']
        uncertainty, temperature = result['uncertainty'], record['conditions']['temperature']
        if record['study_id'] not in sources:
            raise ValueError('PAHT observation contract: missing referenced source')

        def local(key, value=None):
            return '  ' + wording[key] + (': ' + str(value) if value is not None else '')

        rendered = [field('catalog_original_name', record['name']),
            field('catalog_version', record['version']), field('catalog_study_id', record['study_id']),
            local('paht_classification'), local('paht_identity'),
            local('paht_dataset', record['dataset_id']), local('paht_protocol', record['protocol_id']),
            field('catalog_quantity', record['quantity']),
            field('catalog_quantity_dimension', record['quantity_dimension']),
            local('paht_temperature', temperature['value_string'] + ' °C'),
            local('paht_temperature_basis')]
        rendered.extend(local(code) for code in PAHT_CAVEATS)
        rendered.extend([local('paht_reported_display'), local('paht_reported_notice'),
            local('paht_reported_median', result['value_string'] + ' MPa'),
            local('paht_reported_sd', uncertainty['value_string'] + ' MPa'),
            local('paht_si_display'), local('paht_si_notice'),
            local('paht_si_median', str(int(si['value'])) + ' Pa'),
            local('paht_si_sd', str(int(si['uncertainty_value'])) + ' Pa'),
            local('paht_cell', json.dumps(record['source_cell'], ensure_ascii=False, sort_keys=True)),
            local('paht_details')])
        for key in ('material', 'method', 'conditions', 'sample_metadata',
                    'reported_result', 'si_result', 'verification', 'evidence', 'limits'):
            rendered.append('    ' + key + ': ' + json.dumps(record[key], ensure_ascii=False, sort_keys=True))
        rendered.extend(source_summary(sources[record['study_id']], '    '))
        rendered.append('    ' + json.dumps(sources[record['study_id']], ensure_ascii=False, sort_keys=True))
        return rendered

    def hbn_observation(record: dict) -> list[str]:
        """Render the Falin family without borrowing graphene/MoS2 conventions."""
        material, method = record["material"], record["method"]
        result, sample = record["reported_result"], record["sample_metadata"]
        uncertainty, conditions = result["uncertainty"], record["conditions"]
        strength = record["quantity"] == "breaking_strength_2d"

        def evidence_lines(evidence: dict, indent: str = "    ") -> list[str]:
            return [
                field("source", evidence["source_id"], indent),
                field("catalog_hbn_source_component", status(evidence["artifact"]), indent),
                field("catalog_urls", evidence["source_url"], indent),
                field("catalog_evidence_status", status(evidence["verification_status"]), indent),
                field("catalog_locator", evidence["locator"], indent),
                field("catalog_verified_as", evidence["verified_as"], indent),
            ]

        def physical_value(value: dict) -> str:
            return f'{value["value"]} {value["unit"]}'

        rendered = [
            field("catalog_original_name", record["name"]),
            field("catalog_version", record["version"]),
            field("catalog_study_id", record["study_id"]),
            field("catalog_observation_type", status(record["observation_type"])),
            field("catalog_quantity", status(record["quantity"])),
            field("catalog_quantity_dimension", status(record["quantity_dimension"])),
            field("catalog_si_unit", record["si_unit"]),
            field("catalog_evaluation_support", status(record["evaluation_support"])),
            "  " + t("catalog_observation_notice"),
            field("catalog_model_status", status(record["model_status"])),
            "  " + t("catalog_hbn_model_notice"),
            field("catalog_material", material["name"]),
            field("catalog_dimensionality", material["dimensionality"]),
            field("catalog_layer_count", material["layer_count"]),
            field("catalog_specimen_form", status(material["specimen_form"])),
            field("catalog_preparation", material["preparation"]),
            field("catalog_monolayer_identification", "; ".join(status(value) for value in material["monolayer_identification"])),
            field("catalog_hbn_well_radius", physical_value(material["suspended_well_radius"])),
            field("catalog_span_diameters", physical_value(material["suspended_well_diameter"])),
            field("catalog_locator", material["suspended_well_diameter"]["locator"]),
            field("catalog_hbn_apparent_height", physical_value(material["example_afm_apparent_height"])),
            field("catalog_hbn_effective_thickness", physical_value(method["effective_thickness_convention"])),
            "  " + t("catalog_hbn_thickness_notice"),
            "  " + t("catalog_hbn_specimen_notice"),
            field("catalog_reported_result", f'{result["value"]} ± {uncertainty["value"]} {result["unit"]}'),
            field("catalog_hbn_summary_statistic", status(result["summary_statistic"])),
        ]
        if strength:
            rendered.append(field("catalog_hbn_central_statistic", result["central_statistic_explicitly_named"]))
        rendered.extend([
            field("catalog_uncertainty_type", status(uncertainty["type"])),
            "  " + t("catalog_hbn_sd_notice"),
            field("catalog_coverage_factor", uncertainty["coverage_factor"]),
            field("catalog_confidence_level", uncertainty["confidence_level"]),
            field("catalog_averaging_convention", uncertainty["averaging_convention"]),
            field("catalog_uncertainty_interpretation", uncertainty["interpretation"]),
            field("catalog_hbn_sd_evidence", status(uncertainty["definition_basis"])),
        ])
        rendered.extend(evidence_lines(uncertainty["evidence"]))
        rendered.extend([
            field("catalog_measurement_method", status(method["technique"])),
            field("catalog_hbn_instrument", method["instrument"]),
            field("catalog_hbn_tip_radii", f'{", ".join(str(value) for value in method["tip_radii"]["values"])} {method["tip_radii"]["unit"]}'),
            field("catalog_locator", method["tip_radii"]["locator"]),
            "  " + t("catalog_hbn_tip_notice"),
            field("catalog_hbn_inference_model", status(method["inference_model"])),
            field("catalog_inference", method["inference"]),
            field("catalog_poissons_ratio_assumed", method["poissons_ratio_assumed"]),
            "  " + t("catalog_hbn_poisson_notice"),
            field("catalog_stress_measure", method["stress_measure"]),
            field("catalog_strain_measure", method["strain_measure"]),
            "  " + t("catalog_hbn_stress_strain_notice"),
            field("catalog_stress_strain_status", method["stress_strain_measure_status"]),
        ])
        if strength:
            relation, fem = method["constitutive_relation"], method["finite_element_model"]
            rendered.extend([
                "  " + t("catalog_hbn_strength_notice"),
                field("catalog_formula", relation["formula_as_printed"]),
                field("catalog_hbn_fem_elastic_input", physical_value(relation["E"])),
                field("catalog_hbn_fem_third_order_input", physical_value(relation["D"])),
                field("catalog_hbn_fem_software", fem["software"]),
                field("catalog_hbn_fem_geometry", "; ".join(status(fem[key]) for key in ("membrane", "indenter", "contact"))),
                field("catalog_hbn_strength_reduction", status(fem["strength_reduction"])),
                field("catalog_hbn_stress_component", fem["reported_stress_component_or_invariant_for_this_average"]),
                field("catalog_hbn_fem_element", fem["element_type"]),
                field("catalog_hbn_fem_element_count", fem["element_count"]),
                field("catalog_hbn_fem_depth", physical_value(fem["applied_indentation_depth"])),
                field("catalog_hbn_fem_increment", physical_value(fem["displacement_increment"])),
                "  " + t("catalog_hbn_fem_input_notice"),
                "  " + t("catalog_hbn_diagnostic_notice"),
                field("catalog_locator", method["diagnostic_not_selected_result"]["source"]),
            ])
        else:
            q, force_law = method["q_source_report"], method["fit_force_law"]
            rendered.extend([
                "  " + t("catalog_hbn_stiffness_notice"),
                field("catalog_formula", force_law["formula_as_printed"]),
                field("catalog_locator", force_law["source_locator"]),
                field("catalog_q_formula", q["formula_as_printed"]),
                field("catalog_hbn_q_nu", q["nu_as_printed"]),
                field("catalog_q_reported", q["q_as_printed"]),
                field("catalog_q_arithmetic", q["audit_arithmetic_value"]),
                field("catalog_q_used", q["fit_constant_actually_used"]),
                "  " + t("catalog_hbn_q_notice"),
            ])
        rendered.append(field("catalog_model_assumptions", ""))
        rendered.extend("    - " + assumption for assumption in method["model_assumptions"])
        rendered.extend([
            "  " + t("catalog_hbn_curve_selection_notice"),
            field("catalog_conditions", ""),
            field("catalog_hbn_environment", t("catalog_hbn_ambient"), "    "),
            "    " + t("catalog_hbn_conditions_notice"),
        ])
        for key in ("temperature", "atmosphere", "humidity", "pressure"):
            rendered.append(field("catalog_" + key, conditions[key], "    "))
        rendered.extend([
            field("catalog_hbn_probe_velocity", physical_value(conditions["loading_rate"]), "    "),
            field("catalog_hbn_strain_rate", conditions["loading_rate"]["strain_rate"], "    "),
            "    " + t("catalog_hbn_velocity_notice"),
            field("catalog_locator", conditions["loading_rate"]["locator"], "    "),
            field("catalog_sample_metadata", ""),
            field("catalog_sample_scope", status(sample["scope"]), "    "),
            "    " + t("catalog_hbn_count_notice"),
        ])
        for key, label in (
            ("study_monolayer_tested_sheets", "catalog_hbn_tested_sheet_count"),
            ("force_displacement_curves_acquired", "catalog_hbn_acquired_curve_count"),
            ("force_displacement_curves_retained", "catalog_hbn_retained_curve_count"),
            ("force_displacement_curves_excluded", "catalog_hbn_excluded_curve_count"),
            ("distinct_parent_flakes", "catalog_parent_flake_count"),
            ("failure_events", "catalog_failure_count"),
            ("tested_sheets_explicitly_associated_with_stiffness_average", "catalog_hbn_stiffness_sheet_count"),
        ):
            if key in sample["counts"]:
                rendered.append(field(label, sample["counts"][key], "    "))
        rendered.extend([
            field("catalog_hbn_typical_indentations", sample["typical_protocol"]["indentations_per_sheet_typically"], "    "),
            field("catalog_hbn_exact_protocol_count", t("catalog_yes" if sample["typical_protocol"]["exact_count"] else "catalog_no"), "    "),
            field("catalog_hbn_count_evidence", "", "    "),
        ])
        rendered.extend(evidence_lines(sample["count_definition_source"], "      "))
        rendered.extend("    - " + note for note in sample["notes"])
        verification = record["verification"]
        inspected = verification["source_inspection"]
        rendered.extend([
            field("catalog_observation_verification", status(verification["status"])),
            field("catalog_independent_review", t("catalog_yes" if verification["independent_scientific_review"] else "catalog_no")),
            "  " + t("catalog_hbn_inspection_notice"),
            field("catalog_hbn_source_component", status(inspected["main_artifact"])),
        ])
        for key, label in (
            ("main_pdf_inspected", "catalog_hbn_main_pdf_inspected"),
            ("supplement_inspected", "catalog_hbn_supplement_inspected"),
            ("peer_review_author_response_inspected", "catalog_hbn_peer_response_inspected"),
            ("separate_reader_transcription_checked", "catalog_hbn_second_reader"),
            ("raw_data_reanalysis", "catalog_hbn_raw_reanalysis"),
            ("plot_digitization", "catalog_hbn_plot_digitization"),
            ("independent_replication", "catalog_hbn_independent_replication"),
        ):
            rendered.append(field(label, t("catalog_yes" if inspected[key] else "catalog_no"), "    "))
        for key, label in (
            ("equations_visually_checked", "catalog_hbn_equations_checked"),
            ("supplement_visual_pages", "catalog_hbn_supplement_pages"),
            ("peer_review_visual_pages", "catalog_hbn_peer_response_pages"),
        ):
            rendered.append(field(label, ", ".join(str(value) for value in inspected[key]), "    "))
        rendered.append(field("catalog_gaps", ""))
        rendered.extend("    - " + gap for gap in verification["gaps"])
        rendered.append(field("catalog_observation_evidence", ""))
        source = sources.get(record["study_id"])
        if source is not None:
            rendered.extend(source_summary(source, "    "))
        for evidence in record["evidence"]:
            rendered.extend(evidence_lines(evidence))
        rendered.extend([
            "  " + t("catalog_hbn_rights_notice"),
            field("catalog_limits", ""),
        ])
        rendered.extend("    - " + limit for limit in record["limits"])
        rendered.append("  " + t("catalog_observation_compatibility_notice"))
        return rendered

    lines = [t("catalog_" + kind), field("catalog_count", len(catalog["records"]), "")]
    if not catalog["records"]:
        lines.append(t("catalog_empty"))
    sources = {source["id"]: source for source in read_catalog("sources")["records"]} if kind in {"claims", "observations"} else {}
    from ._pa12_cf15_observation_contract import validate_pa12_sources
    if kind == "sources":
        validate_pa12_sources(catalog["records"])
        validate_paht_sources(catalog["records"])
    elif kind in {"claims", "observations"}:
        validate_pa12_sources(list(sources.values()))
        validate_paht_sources(list(sources.values()))
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
            if record.get("method_family") == PAHT_FAMILY:
                lines.extend(paht_observation(record))
                continue
            if record.get("method_family") == "ciganas_2026_pa12_cf15_fff_tensile_temperature_v1":
                lines.extend(pa12_observation(record))
                continue
            if record.get("method_family") == "falin_2017_hbn_monolayer_indentation_v1":
                lines.extend(hbn_observation(record))
                continue
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
                notice = ("catalog_yield_notice" if "yield_criterion_contract" in record
                          else "catalog_viscoelastic_notice" if "viscoelastic_contract" in record
                          else "catalog_wave_notice" if "bulk_wave_contract" in record
                          else "catalog_compressibility_notice" if "hydrostatic_compressibility_contract" in record
                          else "catalog_directional_notice" if "directional_contract" in record
                          else "catalog_index_notice" if "index_range" in record
                          else "catalog_criterion_notice" if record["claim_type"] == "stability_criterion"
                          else "catalog_bound_notice" if record["claim_type"] in {"theoretical_bound", "derived_outer_envelope"}
                          else "catalog_model_notice")
                lines.append("  " + t(notice))
            if "yield_criterion_contract" in record:
                for key in ("tensor", "normalization", "math_scope", "physical_scope", "attribution", "limits"):
                    lines.append("  " + t("catalog_yield_" + key))
                lines.append("    yield_criterion_contract: " + json.dumps(
                    record["yield_criterion_contract"], ensure_ascii=False, allow_nan=False))
            if "viscoelastic_contract" in record:
                for key in ("conditions", "regularity", "attribution", "range", "limits"):
                    lines.append("  " + t("catalog_viscoelastic_" + key))
                lines.append("    viscoelastic_contract: " + json.dumps(
                    record["viscoelastic_contract"], ensure_ascii=False, allow_nan=False))
            if "bulk_wave_contract" in record:
                for key in ("conditions", "normalization", "polarization", "energy", "range", "limits"):
                    lines.append("  " + t("catalog_wave_" + key))
                lines.append("    bulk_wave_contract: " + json.dumps(
                    record["bulk_wave_contract"], ensure_ascii=False, allow_nan=False))
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
