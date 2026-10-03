"""Dependency-free display guard for the closed source/method observation contracts.

Full structural admission lives in observations.schema.json. This guard also
keeps the indispensable caveat/SD/count semantics fail-closed in runtime catalog
reads and caller-supplied text views. It neither evaluates nor corrects a model.
"""
import math

MOS2_FAMILY = "bertolazzi_2011_mos2_monolayer_indentation_v1"
MOS2_SOURCE = "bertolazzi_brivio_kis_2011"
MOS2_LABELS = frozenset({
    "catalog_mos2_model_notice", "catalog_model_status", "catalog_q_formula",
    "catalog_q_nu", "catalog_q_reported", "catalog_q_arithmetic", "catalog_q_used",
    "catalog_mos2_source_notice", "catalog_sd_notice", "catalog_geometry_uncertainty_notice",
    "catalog_probe_speed_notice", "catalog_mos2_transcription_notice",
    "catalog_study_monolayer_count", "catalog_stiffness_membrane_count",
    "catalog_curve_count", "catalog_failure_count", "catalog_parent_flake_count", "catalog_averaging_convention",
    "catalog_preparation_notes", "catalog_geometry_tolerance", "catalog_tip_radius",
    "catalog_stress_strain_status", "catalog_probe_speed",
    "catalog_status_reported_standard_deviation",
    "catalog_status_source_reported_unresolved_model_discrepancy",
})


def validate_mos2_records(records):
    """Keep same-family IDs appendable; never dispatch scientific models by ID."""
    def require(ok, message):
        if not ok:
            raise ValueError("MoS2 observation contract: " + message)

    def exact(value, expected):
        # Python equality alone conflates True with 1; scientific types matter.
        if isinstance(expected, dict):
            require(isinstance(value, dict), "missing structured metadata")
            for key, item in expected.items():
                require(key in value, "missing " + key)
                exact(value[key], item)
        elif type(expected) in (float, int):
            require(type(value) in (float, int) and value == expected, "source numeric identity changed")
        else:
            require(type(value) is type(expected) and value == expected, "source/method identity changed")

    for record in records:
        family = record.get("method_family")
        material = record.get("material", {})
        is_mos2 = (family == MOS2_FAMILY or material.get("formula") == "MoS2"
                   or record.get("study_id") == MOS2_SOURCE)
        if not is_mos2:
            continue  # Historical graphene schema/records remain unchanged.
        exact(record, {
            "method_family": MOS2_FAMILY, "study_id": MOS2_SOURCE,
            "model_status": "source_reported_unresolved_model_discrepancy",
            "observation_type": "experiment_derived_model_dependent",
            "evaluation_support": "catalog_only", "si_unit": "N/m",
            "quantity_dimension": "force_per_length",
            "material": {"formula": "MoS2", "dimensionality": 2, "layer_count": 1,
                         "specimen_form": "suspended_membrane"},
            "reported_result": {"unit": "N/m", "summary_statistic": "reported_average",
                "uncertainty": {"unit": "N/m", "notation": "plus_minus",
                    "type": "reported_standard_deviation", "scope": "reported_property_experimental_values",
                    "coverage_factor": None, "confidence_level": None, "averaging_convention": None}},
            "method": {"technique": "afm_central_indentation", "poissons_ratio_assumed": .27,
                "stress_measure": None, "strain_measure": None,
                "constitutive_model": "isotropic_linear_elastic_membrane",
                "q_source_report": {"formula_as_printed": "q = 1/(1.05 − 0.15ν − 0.16ν²)",
                    "nu_as_printed": .27, "q_as_printed": .95, "internal_consistency": "inconsistent",
                    "audit_arithmetic_value": 1.002168693051764, "fit_constant_actually_used": None}},
            "conditions": {"temperature": None, "atmosphere": None, "humidity": None,
                "loading_rate": {"quantity": "vertical_probe_translation_speed", "unit": "um/s"},
                "verification_status": "partially_reported_primary_main_text"},
            "sample_metadata": {"scope": "study_membrane_counts_not_force_curve_or_failure_event_counts",
                "counts": {"study_monolayer_membranes": 9, "force_displacement_curves": None,
                           "distinct_parent_flakes": None, "failure_events": None}},
            "verification": {"status": "primary_institutional_main_text_checked_supplement_not_inspected",
                "independent_scientific_review": False,
                "source_inspection": {"artifact": "epfl_institutional_main_text",
                    "pagination": "proof_formatted_pdf_pages_A_to_G", "publisher_final_text_identity_verified": False,
                    "supplement_inspected": False, "separate_reader_transcription_checked": True,
                    "raw_data_reanalysis": False, "independent_replication": False}},
        })
        quantity = record["quantity"]
        require(quantity in {"in_plane_stiffness_2d", "breaking_strength_2d"}, "unsupported quantity")
        stiffness = quantity == "in_plane_stiffness_2d"
        exact(record["method"].get("inference_model"), "circular_membrane_elastic_force_deflection_fit" if stiffness
              else "finite_spherical_tip_large_load_maximum_local_stress")
        counts = record["sample_metadata"]["counts"]
        key = "membranes_explicitly_associated_with_stiffness_average"
        if stiffness:
            exact(counts, {key: 9})
        else:
            require(key not in counts, "stiffness sample count copied into breaking strength")
        for geometry in (material["suspended_span_diameters"], record["method"]["tip_radius"]):
            exact(geometry, {"unit": "nm", "uncertainty": {"unit": "nm",
                  "type": "reported_plus_minus_unspecified", "coverage_factor": None, "confidence_level": None}})
        result = record["reported_result"]
        for value, zero in ((result["value"], False), (result["uncertainty"]["value"], True),
                            (record["conditions"]["loading_rate"]["value"], False)):
            require(type(value) in (int, float) and math.isfinite(value)
                    and (value >= 0 if zero else value > 0), "invalid reported number")
        require(any(item.get("source_id") == MOS2_SOURCE for item in record["evidence"]), "missing study evidence")


def validate_observation_records(records):
    """Dispatch explicit families; unknown families never inherit another model."""
    from ._hbn_observation_contract import HBN_FAMILY, HBN_SOURCE, validate_hbn_records
    from ._pa12_cf15_observation_contract import PA12_FAMILY, validate_pa12_dataset
    validate_pa12_dataset(records)
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("material"), dict):
            raise ValueError("Observation contract: invalid record/material shape")
        family = record.get("method_family")
        if family not in (None, MOS2_FAMILY, HBN_FAMILY, PA12_FAMILY):
            raise ValueError("Observation contract: unsupported method family")
        if family is None:
            # The legacy branch is the existing Lee contract only. Relabeling
            # newer records must not bypass their source-specific safeguards.
            legacy_method_keys = {"inference", "model_assumptions", "poissons_ratio_assumed",
                                  "strain_measure", "stress_measure", "technique"}
            if (record.get("study_id") != "lee_wei_kysar_hone_2008"
                    or "formula" in record["material"]
                    or "model_status" in record or "method_family" in record
                    or not isinstance(record.get("method"), dict)
                    or set(record["method"]) != legacy_method_keys):
                raise ValueError("Observation contract: missing method family or unsupported legacy shape")
    validate_mos2_records(records)
    validate_hbn_records(records)
