"""Dependency-free guard for Falin's closed monolayer hBN observation family.

No inference is executed. Family dispatch is independent of record IDs. Source
component provenance, unknown states and averaging definitions fail closed even
when callers render a subset without the optional JSON Schema validator.
"""

import hashlib
import json

HBN_FAMILY = "falin_2017_hbn_monolayer_indentation_v1"
HBN_SOURCE = "falin_et_al_2017_hbn_mechanical_properties"
HBN_MAIN = "https://www.nature.com/articles/ncomms15815"
HBN_SUPPLEMENT = "https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fncomms15815/MediaObjects/41467_2017_BFncomms15815_MOESM442_ESM.pdf"
HBN_REVIEW = "https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fncomms15815/MediaObjects/41467_2017_BFncomms15815_MOESM443_ESM.pdf"


# The schema fixes the complete scientific payload for these two source-defined
# contracts. Keep that closure in dependency-free readers too: even a changed
# caveat can falsely turn SD into SEM or an unspecified measure into certainty.
# These are curated-payload integrity hashes, not source-artifact hashes.
# IDs/names remain appendable and component-evidence order is immaterial.
# JSON-equivalent integral floats are normalized; Boolean values stay distinct.
# The readable assertions below document the indispensable scientific content.
HBN_SCIENTIFIC_PAYLOAD_SHA256 = {'in_plane_stiffness_2d': '3d410cceb120420eecb93dbec3d545411667146fcceeba5de68a2273660ca179', 'breaking_strength_2d': '3435e2d4dd8b31ffca65e37a96ca7ffeb486afab13bdbd90a7922d8557c92bb6'}

HBN_LABELS = frozenset(['catalog_hbn_acquired_curve_count', 'catalog_hbn_ambient', 'catalog_hbn_apparent_height', 'catalog_hbn_central_statistic', 'catalog_hbn_conditions_notice', 'catalog_hbn_count_evidence', 'catalog_hbn_count_notice', 'catalog_hbn_curve_selection_notice', 'catalog_hbn_diagnostic_notice', 'catalog_hbn_effective_thickness', 'catalog_hbn_environment', 'catalog_hbn_equations_checked', 'catalog_hbn_exact_protocol_count', 'catalog_hbn_excluded_curve_count', 'catalog_hbn_fem_depth', 'catalog_hbn_fem_elastic_input', 'catalog_hbn_fem_element', 'catalog_hbn_fem_element_count', 'catalog_hbn_fem_geometry', 'catalog_hbn_fem_increment', 'catalog_hbn_fem_input_notice', 'catalog_hbn_fem_software', 'catalog_hbn_fem_third_order_input', 'catalog_hbn_independent_replication', 'catalog_hbn_inference_model', 'catalog_hbn_inspection_notice', 'catalog_hbn_instrument', 'catalog_hbn_main_pdf_inspected', 'catalog_hbn_model_notice', 'catalog_hbn_peer_response_inspected', 'catalog_hbn_peer_response_pages', 'catalog_hbn_plot_digitization', 'catalog_hbn_poisson_notice', 'catalog_hbn_probe_velocity', 'catalog_hbn_q_notice', 'catalog_hbn_q_nu', 'catalog_hbn_raw_reanalysis', 'catalog_hbn_retained_curve_count', 'catalog_hbn_rights_notice', 'catalog_hbn_sd_evidence', 'catalog_hbn_sd_notice', 'catalog_hbn_second_reader', 'catalog_hbn_source_component', 'catalog_hbn_specimen_notice', 'catalog_hbn_stiffness_notice', 'catalog_hbn_stiffness_sheet_count', 'catalog_hbn_strain_rate', 'catalog_hbn_strength_notice', 'catalog_hbn_strength_reduction', 'catalog_hbn_stress_component', 'catalog_hbn_stress_strain_notice', 'catalog_hbn_summary_statistic', 'catalog_hbn_supplement_inspected', 'catalog_hbn_supplement_pages', 'catalog_hbn_tested_sheet_count', 'catalog_hbn_thickness_notice', 'catalog_hbn_tip_notice', 'catalog_hbn_tip_radii', 'catalog_hbn_typical_indentations', 'catalog_hbn_velocity_notice', 'catalog_hbn_well_radius', 'catalog_pressure', 'catalog_status_AFM_height_profile', 'catalog_status_Raman_characterization', 'catalog_status_axisymmetric', 'catalog_status_brief_factual_numerical_values_bibliographic_metadata_equations_source_locators_and_original_curation_notes_only', 'catalog_status_circular_membrane_force_deflection_fit', 'catalog_status_explicit_publisher_open_license_verified_for_main_article_only_supplement_and_peer_review_scope_unverified', 'catalog_status_frictionless', 'catalog_status_nonlinear_finite_element_volume_averaged_under_indenter_stress', 'catalog_status_peer_review_author_response', 'catalog_status_publisher_html', 'catalog_status_publisher_main_text_and_relevant_supplement_and_peer_review_checked', 'catalog_status_publisher_main_text_equations_and_selected_supplement_and_peer_review_passages_checked', 'catalog_status_publisher_main_text_passage_checked', 'catalog_status_publisher_peer_review_author_response', 'catalog_status_publisher_peer_review_author_response_text_and_visual_passage_checked', 'catalog_status_publisher_supplement_text_and_visual_passage_checked', 'catalog_status_reported_average', 'catalog_status_reported_strength_summary', 'catalog_status_rigid_sphere', 'catalog_status_source_reported_model_dependent_with_explicit_metadata_gaps', 'catalog_status_supplement', 'catalog_status_tested_sheet_count_not_raw_curve_or_separately_enumerated_failure_count', 'catalog_status_volume_average_of_under_indenter_element_stresses_at_experimental_fracture_load'])

def _canonical_numbers(value):
    if isinstance(value, dict):
        return {key: _canonical_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonical_numbers(item) for item in value]
    if type(value) is float and value.is_integer():
        return int(value)
    return value


def validate_hbn_records(records):
    def require(ok, message):
        if not ok:
            raise ValueError("hBN observation contract: " + message)

    def exact(actual, expected):
        if isinstance(expected, dict):
            require(isinstance(actual, dict), "missing structured metadata")
            for key, value in expected.items():
                require(key in actual, "missing " + key)
                exact(actual[key], value)
        elif type(expected) in (int, float):
            require(type(actual) in (int, float) and actual == expected, "source numeric identity changed")
        else:
            require(type(actual) is type(expected) and actual == expected, "source/method identity changed")

    def component(evidence, artifact, url, locator):
        exact(evidence, {"artifact": artifact, "source_id": HBN_SOURCE,
                         "source_url": url, "locator": locator,
                         "verification_status": "publisher_peer_review_author_response_text_and_visual_passage_checked"})
        require(isinstance(evidence.get("verified_as"), str) and bool(evidence["verified_as"].strip()),
                "missing component evidence interpretation")
        require(isinstance(evidence.get("verification_status"), str) and
                bool(evidence["verification_status"].strip()), "missing component inspection status")

    for record in records:
        require(isinstance(record, dict) and isinstance(record.get("material"), dict),
                "invalid record/material shape")
        if not (record.get("method_family") == HBN_FAMILY or
                record.get("study_id") == HBN_SOURCE or record.get("material", {}).get("formula") == "BN"):
            continue
        require(all(isinstance(record.get(key), str) and record[key].strip() for key in ("id", "name")),
                "missing record identity")
        require(isinstance(record.get("quantity"), str) and record["quantity"] in HBN_SCIENTIFIC_PAYLOAD_SHA256,
                "unsupported quantity")
        payload = _canonical_numbers({key: value for key, value in record.items() if key not in ("id", "name")})
        try:
            payload["evidence"] = sorted(payload["evidence"], key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
            encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":"), allow_nan=False).encode()
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("hBN observation contract: invalid scientific payload") from exc
        require(hashlib.sha256(encoded).hexdigest() == HBN_SCIENTIFIC_PAYLOAD_SHA256.get(record.get("quantity")),
                "source-defined scientific payload changed")
        exact(record, {
            "method_family": HBN_FAMILY, "study_id": HBN_SOURCE,
            "observation_type": "experiment_derived_model_dependent",
            "model_status": "source_reported_model_dependent_with_explicit_metadata_gaps",
            "evaluation_support": "catalog_only", "quantity_dimension": "force_per_length", "si_unit": "N/m",
            "material": {"formula": "BN", "phase": "hexagonal", "dimensionality": 2,
                "layer_count": 1, "specimen_form": "suspended_membrane", "crystal_orientation": None,
                "suspended_well_radius": {"value": 650, "unit": "nm", "uncertainty": None},
                "suspended_well_diameter": {"value": 1.3, "unit": "um", "source_reports_explicitly": True},
                "example_afm_apparent_height": {"value": .48, "unit": "nm"},
                "defect_status": {"quantitative_defect_census": None}},
            "reported_result": {"unit": "N/m", "uncertainty": {"notation": "plus_minus", "unit": "N/m",
                "type": "reported_standard_deviation", "definition_basis": "publisher_peer_review_author_response",
                "coverage_factor": None, "confidence_level": None, "averaging_convention": None}},
            "method": {"technique": "afm_central_indentation", "instrument": "Cypher AFM",
                "indenter_material": "diamond", "poissons_ratio_assumed": .211,
                "stress_measure": None, "strain_measure": None,
                "tip_radii": {"values": [5.6, 6.3], "unit": "nm", "uncertainty": None, "per_sheet_assignment": None},
                "displacement_relation": {"equation_number": 1, "formula_as_printed": "δ = ΔZ_piezo − δ_tip", "visually_verified": True},
                "effective_thickness_convention": {"value": .334, "unit": "nm"}},
            "conditions": {"temperature": None, "atmosphere": None, "humidity": None, "pressure": None,
                "environment_description": "ambient conditions",
                "verification_status": "ambient_descriptor_and_translation_velocity_reported",
                "loading_rate": {"quantity": "reported_loading_and_unloading_translation_velocity", "value": .5,
                    "unit": "um/s", "source_scope": "all measurements", "strain_rate": None}},
            "sample_metadata": {"scope": "tested_sheet_count_not_raw_curve_or_separately_enumerated_failure_count",
                "counts": {"study_monolayer_tested_sheets": 11, "force_displacement_curves_acquired": None,
                    "force_displacement_curves_retained": None, "force_displacement_curves_excluded": None,
                    "distinct_parent_flakes": None, "failure_events": None},
                "typical_protocol": {"indentations_per_sheet_typically": 5, "exact_count": False}},
            "verification": {"status": "publisher_main_text_and_relevant_supplement_and_peer_review_checked",
                "independent_scientific_review": False, "source_inspection": {"main_artifact": "publisher_html",
                    "main_pdf_inspected": False, "equations_visually_checked": [1, 2, 4],
                    "supplement_inspected": True, "supplement_visual_pages": [4, 5],
                    "peer_review_author_response_inspected": True, "peer_review_visual_pages": [8],
                    "separate_reader_transcription_checked": True, "raw_data_reanalysis": False,
                    "plot_digitization": False, "independent_replication": False}},
        })
        quantity = record.get("quantity")
        require(quantity in ("in_plane_stiffness_2d", "breaking_strength_2d"), "unsupported quantity")
        stiffness = quantity == "in_plane_stiffness_2d"
        result, method, sample = record["reported_result"], record["method"], record["sample_metadata"]
        exact(result, {"value": 289 if stiffness else 23.6,
            "summary_statistic": "reported_average" if stiffness else "reported_strength_summary",
            "uncertainty": {"value": 24 if stiffness else 1.8}})
        if not stiffness:
            exact(result, {"central_statistic_explicitly_named": None})
        expected_result_keys = {"value", "unit", "source_value_string", "summary_statistic", "uncertainty"}
        if not stiffness:
            expected_result_keys.add("central_statistic_explicitly_named")
        require(set(result) == expected_result_keys, "unsupported result field")
        require(set(result["uncertainty"]) == {"notation", "value", "unit", "type", "definition_basis",
                "coverage_factor", "confidence_level", "averaging_convention", "interpretation", "evidence"},
                "unsupported uncertainty field")
        component(result["uncertainty"]["evidence"], "peer_review_author_response", HBN_REVIEW,
                  "PDF p. 8, Reviewer #1 question 3, author response")
        component(sample["count_definition_source"], "peer_review_author_response", HBN_REVIEW,
                  "PDF p. 8, author response to Reviewer #1 question 3")
        count_keys = {"study_monolayer_tested_sheets", "force_displacement_curves_acquired",
                      "force_displacement_curves_retained", "force_displacement_curves_excluded",
                      "distinct_parent_flakes", "failure_events"}
        if stiffness:
            count_keys.add("tested_sheets_explicitly_associated_with_stiffness_average")
            exact(sample["counts"], {"tested_sheets_explicitly_associated_with_stiffness_average": 11})
        require(set(sample["counts"]) == count_keys, "unsupported or misplaced count")
        if stiffness:
            exact(method, {"inference_model": "circular_membrane_force_deflection_fit",
                "constitutive_model": "effective_isotropic_elastic_membrane_for_stiffness_fit",
                "fit_force_law": {"equation_number": 2, "formula_as_printed": "F = σ₀²ᴰ(πa)(δ/a) + E²ᴰ(q³a)(δ/a)³", "visually_verified": True},
                "q_source_report": {"formula_as_printed": "q = 1/(1.049 − 0.15ν − 0.16ν²)",
                    "nu_as_printed": .211, "q_as_printed": None,
                    "audit_arithmetic_value": .9898768854482001, "fit_constant_actually_used": None}})
            require("finite_element_model" not in method and "constitutive_relation" not in method,
                    "failure model copied into stiffness fit")
        else:
            exact(method, {"inference_model": "nonlinear_finite_element_volume_averaged_under_indenter_stress",
                "constitutive_model": "source_nonlinear_elastic_quadratic_stress_strain_relation",
                "constitutive_relation": {"equation_number": 4, "formula_as_printed": "σ = Eε + Dε²", "visually_verified": True,
                    "E": {"value": 865, "unit": "GPa"}, "D": {"value": -2035, "unit": "GPa"}},
                "finite_element_model": {"software": "ABAQUS", "indenter": "rigid_sphere", "contact": "frictionless",
                    "membrane": "axisymmetric", "radius": {"value": 650, "unit": "nm"},
                    "initial_thickness": {"value": .334, "unit": "nm", "scope": "monolayer BN"},
                    "element_type": "MAX1 two-node linear axisymmetric membrane", "element_count": 1663,
                    "mesh_spacing": {"centre": .1, "outermost": 1.0, "unit": "nm"},
                    "applied_indentation_depth": {"value": 100, "unit": "nm"},
                    "displacement_increment": {"value": .1, "unit": "nm"},
                    "strength_reduction": "volume_average_of_under_indenter_element_stresses_at_experimental_fracture_load",
                    "reported_stress_component_or_invariant_for_this_average": None},
                "diagnostic_not_selected_result": {"source": "Supplementary Figure S5, PDF p. 5",
                    "plotted_quantity": "maximum Von Mises stress", "source_reported_linear_model_overestimate_percent": 25.7}})
            require("q_source_report" not in method and "fit_force_law" not in method, "stiffness fit copied into failure model")
        for metadata, fields in ((method, ("inference", "stress_strain_measure_status", "poissons_ratio_role", "curve_selection")),
                                 (result["uncertainty"], ("interpretation",)),
                                 (method["effective_thickness_convention"], ("role", "selected_2d_values_status"))):
            for field in fields:
                require(isinstance(metadata.get(field), str) and bool(metadata[field].strip()), "missing source caveat " + field)
        for metadata, field in ((record, "limits"), (record["verification"], "gaps"),
                                (sample, "notes"), (method, "model_assumptions"), (record["conditions"], "notes")):
            require(isinstance(metadata.get(field), list) and len(metadata[field]) >= 3 and
                    all(isinstance(item, str) and item.strip() for item in metadata[field]), "missing source caveats " + field)
        evidence = record.get("evidence")
        require(isinstance(evidence, list) and len(evidence) >= 5, "missing component evidence")
        for item in evidence:
            artifact = item.get("artifact")
            urls = {"publisher_html": HBN_MAIN, "supplement": HBN_SUPPLEMENT, "peer_review_author_response": HBN_REVIEW}
            require(artifact in urls, "unsupported evidence component")
            exact(item, {"source_id": HBN_SOURCE, "source_url": urls[artifact],
                "verification_status": {"publisher_html": "publisher_main_text_passage_checked",
                    "supplement": "publisher_supplement_text_and_visual_passage_checked",
                    "peer_review_author_response": "publisher_peer_review_author_response_text_and_visual_passage_checked"}[artifact]})
            require(isinstance(item.get("locator"), str) and item["locator"].strip(), "missing component locator")
        require({e["artifact"] for e in evidence} == {"publisher_html", "supplement", "peer_review_author_response"},
                "missing inspected source component")
        for field in ("claim_type", "rule_id", "direction", "result", "default_thickness"):
            require(field not in record, "observation acquired executable/bound field")
        for field in ("default_thickness", "thickness", "youngs_modulus_3d"):
            require(field not in record["material"], "invented conversion field")
