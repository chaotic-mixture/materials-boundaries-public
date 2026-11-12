"""Closed, dependency-free contracts for source-reported material references.

These records are catalog-only source transcriptions, never evaluator inputs,
engineering allowables, certified specimens, or universal physical bounds.
Schemas describe structure; generic cross-record checks describe the graph.
Exact structural identity/grade/state clones cannot inflate coverage. Chemical or
formulation equivalence beyond those exact facts remains a source-backed curation
decision; there is no fuzzy matching or automatic material ontology. Neither these
checks nor the schemas verify source truth, licensing, or translations.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import date
from decimal import Decimal
import json
import re
from urllib.parse import urlsplit

LANGUAGES = ("en", "zh", "ja", "de")
CATEGORIES = ("metal", "inorganic", "polymer", "composite", "natural")
HEAT_CAPACITY_UNITS = ("J/(g*K)", "J/(kg*K)", "kJ/(kg*K)")
DIFFUSIVITY_UNITS = ("mm^2/s", "m^2/s")
THERMAL_NEW_QUANTITIES = ("mass_specific_heat_capacity", "thermal_diffusivity")
RESPONSE_TIME_UNITS = ("s", "ms")
WORK_UNITS = ("J/cm^3", "MJ/m^3", "J/m^3")
QUANTITY_DIMENSIONS = {
    "source_reported_elemental_mass_content_percentage": "dimensionless",
    "source_reported_continuous_shear_viscosity": "pressure_time",
    "dsc_reference_normalized_crystallinity_percentage": "dimensionless",
    "ftir_fitted_carbonyl_band_area_ratio": "dimensionless",
    "sec_weight_average_molar_mass": "mass_per_amount",
    "sec_number_average_molar_mass": "mass_per_amount",
    "sec_source_reported_molar_mass_dispersity": "dimensionless",
    "dma_flexural_storage_modulus": "pressure",
    "dma_flexural_loss_tangent": "dimensionless",
    "solvent_extraction_gel_fraction_percentage": "dimensionless",
    "oscillatory_complex_viscosity_magnitude": "pressure_time",
    "dsc_reported_melting_specific_enthalpy": "energy_per_mass",
    "foam_cell_geometric_anisotropy_ratio": "dimensionless",
    "foam_reaction_event_time": "time",
    "closed_cell_content_volume_percentage": "dimensionless",
    "water_absorption_volume_percentage": "dimensionless",
    "tensile_extension_at_failure": "length",
    "thermal_degradation_endset_temperature": "temperature",
    "crystallization_peak_temperature": "temperature",
    "thermal_response_characteristic_time": "time",
    "mass_specific_heat_capacity": "energy_per_mass_temperature",
    "thermal_diffusivity": "area_per_time",
    "volumetric_tensile_work_to_break": "energy_per_volume",
    "thermal_degradation_onset_temperature": "temperature",
    "temperature_at_specified_mass_loss": "temperature",
    "thermal_degradation_rate_peak_temperature": "temperature",
    "tga_residue_percentage": "dimensionless",
    "thermal_conductivity": "power_per_length_temperature",
    "dielectric_breakdown_strength": "electric_field",
    "mass_density": "mass_per_volume",
    "basic_wood_density": "mass_per_volume",
    "youngs_modulus": "pressure",
    "tensile_modulus": "pressure",
    "flexural_modulus": "pressure",
    "flexural_strength": "pressure",
    "compressive_modulus": "pressure",
    "compressive_strength": "pressure",
    "tear_strength": "force_per_length",
    "izod_impact_strength": "energy_per_area",
    "glass_transition_temperature": "temperature",
    "melting_peak_temperature": "temperature",
    "elastic_modulus_unspecified": "pressure",
    "tensile_strength": "pressure",
    "tensile_stress_at_break": "pressure",
    "tensile_yield_strength": "pressure",
    "tensile_stress_at_specified_elongation": "pressure",
    "tensile_elongation_at_break": "dimensionless",
    "flexural_elongation_at_break": "dimensionless",
    "tensile_elongation_at_strength": "dimensionless",
    "shore_a_hardness": "dimensionless",
    "slump_flow_spread": "length",
}
UNIT_DIMENSIONS = {
    "percent_elemental_mass_content": "dimensionless",
    "Pa_s_continuous_shear_viscosity": "pressure_time",
    "percent_dsc_reference_crystallinity": "dimensionless",
    "ratio_ftir_fitted_carbonyl_areas": "dimensionless",
    "g_per_mol_sec_molar_mass": "mass_per_amount",
    "kg_per_mol_sec_molar_mass": "mass_per_amount",
    "ten5_g_per_mol_sec_molar_mass": "mass_per_amount",
    "ratio_sec_molar_mass_dispersity": "dimensionless",
    "GPa_dma_flexural_storage": "pressure",
    "ratio_dma_flexural_loss_tangent": "dimensionless",
    "percent_solvent_extraction_gel_fraction": "dimensionless",
    "kPa_s_complex_viscosity": "pressure_time",
    "J_per_g_dsc_melting_enthalpy": "energy_per_mass",
    "ratio_foam_cell_geometric_anisotropy": "dimensionless",
    "percent_closed_cell_content_volume": "dimensionless",
    "percent_water_absorption_volume": "dimensionless",
    **{u: "time" for u in RESPONSE_TIME_UNITS},
    **{u: "energy_per_mass_temperature" for u in HEAT_CAPACITY_UNITS},
    **{u: "area_per_time" for u in DIFFUSIVITY_UNITS},
    **{unit: "energy_per_volume" for unit in WORK_UNITS},
    "percent_tga_residue": "dimensionless",
    "W/(m*K)": "power_per_length_temperature", "mW/(m*K)": "power_per_length_temperature",
    "V/m": "electric_field", "kV/mm": "electric_field",
    "degC": "temperature", "K": "temperature",
    "mm": "length",
    "kJ/m^2": "energy_per_area", "J/m^2": "energy_per_area",
    "kN/m": "force_per_length", "N/m": "force_per_length", "N/mm": "force_per_length",
    "g/cm^3": "mass_per_volume", "kg/m^3": "mass_per_volume",
    "kg/dm^3": "mass_per_volume", "lb/in^3": "mass_per_volume",
    "MPa": "pressure", "GPa": "pressure", "N/mm^2": "pressure",
    "kN/mm^2": "pressure",
    "percent_elongation": "dimensionless",
    "shore_a_scale": "dimensionless",
}
THERMAL_CONDUCTIVITY_UNITS = ("W/(m*K)", "mW/(m*K)")
ELECTRIC_FIELD_UNITS = ("V/m", "kV/mm")
PERCENT_ELONGATION_QUANTITIES = (
    "tensile_elongation_at_break", "tensile_elongation_at_strength",
    "flexural_elongation_at_break",
)
EVIDENCE_KINDS = (
    "manufacturer_reference", "technical_association_reference",
    "published_experimental_reference", "published_computational_reference",
    "published_handbook_reference", "published_measurement_derived_reference",
)
NUMERICAL_UNCERTAINTIES = (
    "reported_standard_deviation", "reported_confidence_interval",
    "reported_plus_minus_unspecified",
)
REPORTED_UNCERTAINTIES = (*NUMERICAL_UNCERTAINTIES, "reported_measures")
REPORTING_BASES = (
    "typical", "nominal", "guideline", "specification_limit",
    "reported_summary", "not_stated",
)
FACT_FIELDS = (
    "product_form", "processing", "temper_or_heat_treatment", "conditioning",
    "composition_or_purity", "reinforcement", "porosity", "orientation",
)
CONDITION_FIELDS = (
    "temperature", "test_standard", "test_method", "direction",
    "conditioning", "loading_rate",
)
SUPPORT_TAGS = (
    "material_identity", "grade", "state", "reported_value", "method",
    "condition", "classification", "disclaimer", "summary_statistic",
    "uncertainty", "sample_count", "source_discrepancy",
)
# Fixed-point only, bounded to 24 integer and 24 fractional digits. Decimal
# preserves significant trailing zeroes; exponents and signed zero are excluded.
DECIMAL_PATTERN = r"^(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])"
# Source/display strings must never inject terminal commands or hidden control
# sequences or malformed UTF-16 surrogates that cannot be UTF-8 encoded.
# Multiline/tabbed labels are not part of this minimal contract.
_CONTROL_PATTERN = r"[\x00-\x1f\x7f-\x9f\ud800-\udfff]"
TEXT = {"type": "string", "minLength": 1,
        "pattern": r"^(?=.*\S)[^\x00-\x1f\x7f-\x9f\ud800-\udfff]+(?![\s\S])"}
NULL = {"type": "null"}
NULLABLE_TEXT = {"anyOf": [TEXT, NULL]}
DECIMAL = {"type": "string", "maxLength": 49, "pattern": DECIMAL_PATTERN}
# Signed coordinates belong only to the dedicated temperature-result branch.
# Signed zero retains source polarity; uncertainty magnitudes remain unsigned.
SIGNED_DECIMAL = {"type": "string", "maxLength": 50,
                  "pattern": r"^-?(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])"}
TEMPERATURE_UNITS = ("degC", "K")
TEMPERATURE_QUANTITIES = ("glass_transition_temperature", "melting_peak_temperature")
TGA_TEMPERATURE_QUANTITIES = (
    "thermal_degradation_onset_temperature", "temperature_at_specified_mass_loss",
    "thermal_degradation_rate_peak_temperature",
)
RESULT_TEMPERATURE_QUANTITIES = ("thermal_degradation_endset_temperature", *TEMPERATURE_QUANTITIES, "crystallization_peak_temperature", *TGA_TEMPERATURE_QUANTITIES)
TGA_QUANTITIES = (*TGA_TEMPERATURE_QUANTITIES, "tga_residue_percentage")
HTTPS = {"type": "string", "format": "uri", "pattern": r"^(?![\s\S]*[\x00-\x1f\x7f-\x9f\ud800-\udfff])https://[^\s/?#]+(?:[/?#][^\s]*)?(?![\s\S])"}


def _enum(values):
    return {"type": "string", "enum": list(values)}


def _array(items, minimum=0, unique=False):
    result = {"type": "array", "items": items, "minItems": minimum}
    if unique:
        result["uniqueItems"] = True
    return result


def _object(properties, optional=()):
    return {"type": "object", "additionalProperties": False,
            "properties": properties,
            "required": [key for key in properties if key not in optional]}


def _ref(name):
    return {"$ref": "#/$defs/" + name}


def _id(prefix):
    return {"type": "string", "pattern": "^" + prefix + r"_[a-z0-9][a-z0-9_]*(?![\s\S])", "maxLength": 160}


def _record_revision():
    """Allow factual corrections within the existing 1.0 record contract."""
    return {"type": "string", "pattern": r"^1\.0\.(0|[1-9][0-9]*)(?![\s\S])"}


def _defs():
    evidence = _object({"source_id": TEXT, "url": HTTPS, "locator": TEXT,
                        "supports": _array(_enum(SUPPORT_TAGS), 1, True)})
    evidence_list = _array(_ref("evidence"), 1)
    facts = []
    for status in ("reported", "not_reported_in_inspected_source", "not_verified", "not_applicable"):
        facts.append(_object({
            "status": {"const": status}, "text": TEXT if status == "reported" else NULL,
            "evidence": evidence_list if status == "reported" else _array(_ref("evidence")),
            "notes": TEXT if status == "not_applicable" else NULLABLE_TEXT,
        }))
    return {
        "evidence": evidence,
        "fact": {"oneOf": facts},
        "names": _object({lang: TEXT for lang in LANGUAGES}),
        "alias": _object({"language": _enum((*LANGUAGES, "und")), "text": TEXT}),
    }


def _bulk_definitions():
    from ._material_derivation import definitions
    return definitions(TEXT, DECIMAL, HTTPS, NULL, _object, _array, _enum)


def _make_materials_schema():
    definitions = {**_defs(), **_bulk_definitions()}
    common = {"version": _record_revision()}
    aliases = _array(_ref("alias"), unique=True)
    evidence = _array(_ref("evidence"), 1)
    definitions["identity"] = _object({
        "id": _id("mat"), **common, "category": _enum(CATEGORIES), "name": TEXT,
        "names": _ref("names"), "aliases": aliases, "identity_scope": TEXT,
        "evidence": evidence, "canonical_taxon": _ref("canonical_taxon"),
    }, ("canonical_taxon",))
    definitions["grade"] = _object({
        "id": _id("grade"), **common, "identity_id": _id("mat"),
        "designation": TEXT,
        "authority": _object({"kind": _enum(("manufacturer", "standard_designation", "source_designation")), "name": TEXT}),
        "manufacturer": _ref("fact"), "aliases": aliases, "evidence": evidence,
    })
    definitions["state"] = _object({
        "id": _id("state"), **common, "identity_id": _id("mat"),
        "grade_id": {"anyOf": [_id("grade"), NULL]}, "name": TEXT,
        "names": _ref("names"), "aliases": aliases, "source_designation": TEXT,
        "state": _object({key: _ref("fact") for key in FACT_FIELDS}),
        "source_scope": TEXT, "evidence": evidence,
        "property_ids": _array(_id("refprop"), 1, True),
        "evaluation_support": {"const": "catalog_only"},
    })
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:materials-boundaries:schema:materials:1.0.0",
        "title": "Catalog-only concrete material registry v1",
        **_object({"schema_version": {"const": "1.0.0"},
                   "identities": _array(_ref("identity")), "grades": _array(_ref("grade")),
                   "records": _array(_ref("state"))}), "$defs": definitions,
    }


def _make_properties_schema():
    definitions = {**_defs(), **_bulk_definitions()}
    evidence = _array(_ref("evidence"), 1)
    # Preserve the legacy value definitions and seven existing property branches.
    # The residue role enters only its dedicated central-value branch and the
    # shared uncertainty vocabulary, where same-role checks still apply.
    unit = _enum(code for code in UNIT_DIMENSIONS if code not in {"percent_elemental_mass_content", "Pa_s_continuous_shear_viscosity", "kPa_s_complex_viscosity", "J_per_g_dsc_melting_enthalpy", "ratio_foam_cell_geometric_anisotropy", "percent_tga_residue", "percent_water_absorption_volume", "GPa_dma_flexural_storage", "ratio_dma_flexural_loss_tangent", "percent_dsc_reference_crystallinity", "ratio_ftir_fitted_carbonyl_areas", "g_per_mol_sec_molar_mass", "kg_per_mol_sec_molar_mass", "ten5_g_per_mol_sec_molar_mass", "ratio_sec_molar_mass_dispersity", "percent_solvent_extraction_gel_fraction", "percent_closed_cell_content_volume"} and code not in (*RESPONSE_TIME_UNITS, *WORK_UNITS, *HEAT_CAPACITY_UNITS, *DIFFUSIVITY_UNITS))
    common_value = {"value_text": TEXT, "unit_text": TEXT, "unit_code": unit}
    definitions["reported_value"] = {"oneOf": [
        _object({"kind": {"const": "scalar"}, **common_value, "number": DECIMAL}),
        _object({"kind": {"const": "interval"}, **common_value, "lower": DECIMAL, "upper": DECIMAL,
                 "endpoint_semantics": {"const": "source_reported_not_a_confidence_interval"}}),
        _object({"kind": {"const": "comparison"}, **common_value,
                 "operator": _enum((">", ">=", "<", "<=")), "number": DECIMAL}),
    ]}
    # A source percentage elongation is a result, whereas the legacy percent
    # code denotes relative uncertainty, confidence or a loading target.
    # Keep result units closed and quantity-specific with the same vocabulary.
    definitions["legacy_reported_value"] = deepcopy(definitions["reported_value"])
    definitions["elongation_reported_value"] = deepcopy(definitions["reported_value"])
    definitions["shore_a_reported_value"] = deepcopy(definitions["reported_value"])
    definitions["temperature_reported_value"] = deepcopy(definitions["reported_value"])
    definitions["thermal_conductivity_reported_value"] = deepcopy(definitions["reported_value"])
    for branch in definitions["thermal_conductivity_reported_value"]["oneOf"]:
        branch["properties"]["unit_code"] = _enum(THERMAL_CONDUCTIVITY_UNITS)
    definitions["electric_field_reported_value"] = deepcopy(definitions["reported_value"])
    for branch in definitions["electric_field_reported_value"]["oneOf"]:
        branch["properties"]["unit_code"] = _enum(ELECTRIC_FIELD_UNITS)
    for branch in definitions["temperature_reported_value"]["oneOf"]:
        branch["properties"]["unit_code"] = _enum(TEMPERATURE_UNITS)
        for key in ("number", "lower", "upper"):
            if key in branch["properties"]:
                branch["properties"][key] = SIGNED_DECIMAL
    definitions["shore_a_reported_value"]["oneOf"] = definitions["shore_a_reported_value"]["oneOf"][:2]
    for branch in definitions["shore_a_reported_value"]["oneOf"]:
        branch["properties"]["unit_code"] = {"const": "shore_a_scale"}
    for branch in definitions["legacy_reported_value"]["oneOf"]:
        branch["properties"]["unit_code"] = _enum(
            code for code in UNIT_DIMENSIONS
            if code not in {*RESPONSE_TIME_UNITS, *HEAT_CAPACITY_UNITS, *DIFFUSIVITY_UNITS, *WORK_UNITS, "percent_elemental_mass_content", "Pa_s_continuous_shear_viscosity", "kPa_s_complex_viscosity", "J_per_g_dsc_melting_enthalpy", "ratio_foam_cell_geometric_anisotropy", "GPa_dma_flexural_storage", "ratio_dma_flexural_loss_tangent", "percent_dsc_reference_crystallinity", "ratio_ftir_fitted_carbonyl_areas", "g_per_mol_sec_molar_mass", "kg_per_mol_sec_molar_mass", "ten5_g_per_mol_sec_molar_mass", "ratio_sec_molar_mass_dispersity", "percent_solvent_extraction_gel_fraction", "percent_closed_cell_content_volume", "percent_water_absorption_volume", "percent_tga_residue", "percent_elongation", "shore_a_scale", *TEMPERATURE_UNITS, *ELECTRIC_FIELD_UNITS, *THERMAL_CONDUCTIVITY_UNITS})
    for branch in definitions["elongation_reported_value"]["oneOf"]:
        branch["properties"]["unit_code"] = {"const": "percent_elongation"}
    # Closed source-reported uncertainty variants. An amplitude alone never
    # establishes dispersion, mean aggregation or a confidence construction.
    # Keep the existing SD shape unchanged for old catalog/output compatibility.
    uncertainty_value = {**common_value, "unit_code": _enum(code for code in UNIT_DIMENSIONS if code not in {"percent_elemental_mass_content", "Pa_s_continuous_shear_viscosity", "kPa_s_complex_viscosity", "J_per_g_dsc_melting_enthalpy", "ratio_foam_cell_geometric_anisotropy", "percent_water_absorption_volume", "GPa_dma_flexural_storage", "ratio_dma_flexural_loss_tangent", "percent_dsc_reference_crystallinity", "ratio_ftir_fitted_carbonyl_areas", "g_per_mol_sec_molar_mass", "kg_per_mol_sec_molar_mass", "ten5_g_per_mol_sec_molar_mass", "ratio_sec_molar_mass_dispersity", "percent_solvent_extraction_gel_fraction", "percent_closed_cell_content_volume"})}
    uncertainty_common = {**uncertainty_value, "number": DECIMAL, "scope": TEXT,
                          "coverage_factor": NULL, "evidence": evidence}
    definitions["confidence_level"] = _object({
        "value_text": TEXT, "number": DECIMAL, "unit_code": {"const": "percent"},
    })
    definitions["uncertainty_fact"] = {"oneOf": [
        _object({"status": {"const": "reported"}, "text": TEXT,
                 "evidence": evidence, "notes": NULLABLE_TEXT}),
        _object({"status": {"const": "not_reported_in_inspected_source"}, "text": NULL,
                 "evidence": _array(_ref("evidence")), "notes": TEXT}),
    ]}
    definitions["reported_window"] = _object({
        "status": {"const": "reported"}, "text": TEXT,
        "evidence": evidence, "notes": NULLABLE_TEXT,
    })
    definitions["specified_elongation"] = _object({
        "value_text": TEXT, "number": DECIMAL, "unit_text": TEXT,
        "unit_code": {"const": "percent"},
        "basis": {"const": "source_reported_percent_elongation"},
        "evidence": evidence, "notes": TEXT,
    })
    # A descriptor is not a symmetric interval. In particular, relative
    # measurement error, CV and graphical SD cannot be collapsed into +/- SD.
    # Within uncertainty, percent belongs only to relative measures, never results.
    measure_common = {
        "qualifier": _enum(("approximately", "not_qualified_in_source")),
        "scope": TEXT, "evidence": evidence,
        "confidence_level": NULL, "coverage_factor": NULL,
    }
    absolute_measure_value = _object({**uncertainty_value, "number": DECIMAL})
    relative_measure_value = _object({
        "value_text": TEXT, "unit_text": TEXT,
        "unit_code": {"const": "percent"}, "number": DECIMAL,
    })
    measure_variants = []
    for kind in ("standard_deviation", "coefficient_of_variation",
                 "standard_error_of_mean", "estimated_inaccuracy"):
        absolute = kind == "standard_deviation"
        measure_variants.append(_object({
            "kind": {"const": kind}, "availability": {"const": "numeric_reported"},
            "basis": {"const": "absolute" if absolute else "relative_to_reported_value"},
            "reported_value": absolute_measure_value if absolute else relative_measure_value,
            **measure_common, "note": NULLABLE_TEXT,
        }))
    measure_variants.append(_object({
        "kind": {"const": "standard_deviation"},
        "availability": {"const": "graphical_only"}, "basis": {"const": "absolute"},
        "reported_value": NULL, **measure_common, "note": TEXT,
    }))
    definitions["reported_measure"] = {"oneOf": measure_variants}
    definitions["uncertainty"] = {"oneOf": [
        _object({"type": {"const": "reported_standard_deviation"},
                 **uncertainty_common, "confidence_level": NULL}),
        _object({"type": {"const": "reported_confidence_interval"},
                 **uncertainty_common, "confidence_level": _ref("confidence_level"),
                 "estimand": _ref("uncertainty_fact"), "construction": _ref("uncertainty_fact")}),
        _object({"type": {"const": "reported_plus_minus_unspecified"},
                 **uncertainty_common, "confidence_level": NULL}),
        _object({"type": {"const": "reported_measures"},
                 "measures": _array(_ref("reported_measure"), 1, True)}),
    ]}
    definitions["sample_count"] = {"oneOf": [
        _object({"value": {"type": "integer", "minimum": 1}, "relation": _enum(("exact", "at_least")),
                 "scope": TEXT, "source_statement": TEXT, "evidence": evidence}),
        _object({"value": NULL, "relation": {"const": "not_reported"},
                 "scope": TEXT, "source_statement": TEXT, "evidence": _array(_ref("evidence"))}),
    ]}
    definitions["source_document"] = _object({
        "url": HTTPS, "revision": NULLABLE_TEXT,
        "inspected_on": {"type": "string", "format": "date", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
        "sha256": {"anyOf": [{"type": "string", "pattern": r"^[0-9a-f]{64}$", "maxLength": 64}, NULL]},
        "hash_status": _enum(("recorded", "not_retained", "unavailable")),
        "hash_note": NULLABLE_TEXT, "inspection_scope": TEXT,
        "inspection_status": {"const": "selected_content_inspected"},
    })
    conditions = {key: _ref("fact") for key in CONDITION_FIELDS}
    conditions["additional_conditions"] = _array(_object({"name": TEXT, "fact": _ref("fact")}))
    definitions["property"] = _object({
        "id": _id("refprop"), "version": _record_revision(), "material_state_id": _id("state"),
        "quantity": _enum(QUANTITY_DIMENSIONS),
        "quantity_dimension": _enum(sorted({dimension for quantity, dimension in QUANTITY_DIMENSIONS.items()
                                             if quantity not in {"sec_weight_average_molar_mass", "sec_number_average_molar_mass", "sec_source_reported_molar_mass_dispersity", "source_reported_elemental_mass_content_percentage", "source_reported_continuous_shear_viscosity", "oscillatory_complex_viscosity_magnitude", "dsc_reported_melting_specific_enthalpy", "foam_reaction_event_time", "thermal_response_characteristic_time", *THERMAL_NEW_QUANTITIES, "dielectric_breakdown_strength", "thermal_conductivity", "volumetric_tensile_work_to_break"}})),
        "source_property_label": TEXT, "reported_value": _ref("legacy_reported_value"),
        "evidence_kind": _enum(EVIDENCE_KINDS), "reporting_basis": _enum(REPORTING_BASES),
        "determination_basis": _enum(("source_reports_measurement", "source_reports_calculation", "source_reports_compiled_measurements", "not_stated", "mixed_or_unclear")),
        "basis_note": TEXT, "conditions": _object(conditions, ("additional_conditions",)),
        "density_basis": {"anyOf": [_enum(("apparent", "bulk", "true", "crystallographic", "simulation_cell", "oven_dry_mass_over_fresh_or_water_saturated_volume", "not_stated")), NULL]},
        "summary_statistic": _enum(("not_stated", "reported_value", "reported_mean")),
        "uncertainty": {"anyOf": [_ref("uncertainty"), NULL]},
        "uncertainty_status": _enum((*REPORTED_UNCERTAINTIES, "not_reported_in_inspected_source", "not_applicable")),
        "uncertainty_note": TEXT, "sample_count": _ref("sample_count"),
        "method_definition": _object({"type": _enum(("source_reported_conventional", "source_reported_compilation",
                                                       "source_reported_crystallographic_derivation", "source_reported_empirical_conversion",
                                                       "source_reported_thermal_transport_product", "source_reported_thermal_response_fit",
                                                       "source_reported_computational_structure_density",
                                                       "source_reported_molecular_simulation_density")),
                                       "definition": TEXT, "extraction_window": {"anyOf": [_ref("reported_window"), NULL]}, "evidence": evidence}),
        "source_discrepancies": _array(_object({"description": TEXT, "disposition": TEXT, "evidence": evidence})),
        "source_id": TEXT, "evidence": evidence, "source_document": _ref("source_document"),
        "scope_note": TEXT, "evaluation_support": {"const": "catalog_only"},
        "universal_bound": {"const": False}, "engineering_allowable": {"const": False},
        "verification": _object({"source_inspection_scope": TEXT,
                                  "transcription_cross_check": {"const": "completed"},
                                  "independent_scientific_review": {"const": False},
                                  "raw_data_reanalysis": {"const": False}}),
        "derivation": _ref("derivation"),
        "specified_elongation": _ref("specified_elongation"),
    }, ("derivation", "specified_elongation"))
    # Disjoint complete branches keep the dependency-free shape validator and
    # public JSON Schema aligned without adding conditional schema vocabulary.
    stress = deepcopy(definitions["property"])
    stress["properties"]["quantity"] = {"const": "tensile_stress_at_specified_elongation"}
    stress["required"].append("specified_elongation")
    elongation = deepcopy(definitions["property"])
    elongation["properties"]["quantity"] = _enum(PERCENT_ELONGATION_QUANTITIES)
    elongation["properties"]["quantity_dimension"] = {"const": "dimensionless"}
    elongation["properties"]["reported_value"] = _ref("elongation_reported_value")
    del elongation["properties"]["specified_elongation"]
    shore = deepcopy(definitions["property"])
    shore["properties"]["quantity"] = {"const": "shore_a_hardness"}
    shore["properties"]["quantity_dimension"] = {"const": "dimensionless"}
    shore["properties"]["reported_value"] = _ref("shore_a_reported_value")
    del shore["properties"]["specified_elongation"]
    temperature = deepcopy(definitions["property"])
    temperature["properties"]["quantity"] = _enum(TEMPERATURE_QUANTITIES)
    temperature["properties"]["quantity_dimension"] = {"const": "temperature"}
    temperature["properties"]["reported_value"] = _ref("temperature_reported_value")
    del temperature["properties"]["specified_elongation"]
    electric = deepcopy(definitions["property"])
    electric["properties"]["quantity"] = {"const": "dielectric_breakdown_strength"}
    electric["properties"]["quantity_dimension"] = {"const": "electric_field"}
    electric["properties"]["reported_value"] = _ref("electric_field_reported_value")
    del electric["properties"]["specified_elongation"]
    thermal = deepcopy(definitions["property"])
    thermal["properties"]["quantity"] = {"const": "thermal_conductivity"}
    thermal["properties"]["quantity_dimension"] = {"const": "power_per_length_temperature"}
    thermal["properties"]["reported_value"] = _ref("thermal_conductivity_reported_value")
    del thermal["properties"]["specified_elongation"]
    other = definitions["property"]
    other["properties"]["quantity"] = _enum(
        q for q in QUANTITY_DIMENSIONS
        if q not in {"source_reported_elemental_mass_content_percentage", "source_reported_continuous_shear_viscosity", "oscillatory_complex_viscosity_magnitude", "dsc_reported_melting_specific_enthalpy", "foam_cell_geometric_anisotropy_ratio", "foam_reaction_event_time", "dma_flexural_storage_modulus", "dma_flexural_loss_tangent", "dsc_reference_normalized_crystallinity_percentage", "ftir_fitted_carbonyl_band_area_ratio", "sec_weight_average_molar_mass", "sec_number_average_molar_mass", "sec_source_reported_molar_mass_dispersity", "solvent_extraction_gel_fraction_percentage", "closed_cell_content_volume_percentage", "water_absorption_volume_percentage", "tensile_extension_at_failure", "thermal_degradation_endset_temperature", "crystallization_peak_temperature", "thermal_response_characteristic_time", *THERMAL_NEW_QUANTITIES, "thermal_conductivity", "dielectric_breakdown_strength", "tensile_stress_at_specified_elongation", "shore_a_hardness", *TEMPERATURE_QUANTITIES, *TGA_QUANTITIES, "volumetric_tensile_work_to_break"}
        and q not in PERCENT_ELONGATION_QUANTITIES)
    del other["properties"]["specified_elongation"]
    definitions["specified_mass_loss"] = _object({
        "kind": {"const": "scalar"}, "value_text": TEXT, "number": DECIMAL,
        "unit_text": TEXT, "unit_code": {"const": "percent_mass_loss"},
        "evidence": evidence, "notes": TEXT,
    })
    known_peak_ordinal = _object({
        "value": {"type": "integer", "minimum": 1}, "evidence": evidence, "notes": TEXT,
    })
    definitions["degradation_peak_ordinal"] = {"oneOf": [known_peak_ordinal, _object({
        "status": _enum(("not_reported_in_inspected_source", "not_verified")),
        "value": NULL, "evidence": evidence, "notes": TEXT,
    })]}
    definitions["residue_endpoint_temperature"] = _object({
        "kind": {"const": "scalar"}, "value_text": TEXT, "number": SIGNED_DECIMAL,
        "unit_text": TEXT, "unit_code": _enum(TEMPERATURE_UNITS),
        "evidence": evidence, "notes": TEXT,
    })
    # A mass reference is relevant even when unknown; 'not applicable' would
    # erase that distinction. Keep the existing fact shape for the other states.
    definitions["mass_reference_basis"] = {"oneOf": deepcopy(definitions["fact"]["oneOf"][:3])}
    definitions["tga_residue_reported_value"] = deepcopy(definitions["reported_value"])
    for branch in definitions["tga_residue_reported_value"]["oneOf"]:
        branch["properties"]["unit_code"] = {"const": "percent_tga_residue"}
    tga_branches = []
    for quantity, qualifiers in (
        ("thermal_degradation_onset_temperature", ()),
        ("temperature_at_specified_mass_loss", ("specified_mass_loss", "mass_reference_basis")),
        ("thermal_degradation_rate_peak_temperature", ("degradation_peak_ordinal",)),
        ("tga_residue_percentage", ("residue_endpoint_temperature", "mass_reference_basis")),
    ):
        branch = deepcopy(elongation if quantity == "tga_residue_percentage" else temperature)
        branch["properties"]["quantity"] = {"const": quantity}
        if quantity == "tga_residue_percentage":
            branch["properties"]["reported_value"] = _ref("tga_residue_reported_value")
        for qualifier in qualifiers:
            branch["properties"][qualifier] = _ref(qualifier)
            branch["required"].append(qualifier)
        tga_branches.append(branch)
    definitions["work_reference_basis"] = {"oneOf": deepcopy(definitions["fact"]["oneOf"][:3])}
    definitions["work_reported_value"] = deepcopy(definitions["reported_value"])
    for value in definitions["work_reported_value"]["oneOf"]:
        value["properties"]["unit_code"] = _enum(WORK_UNITS)
    work = deepcopy(other)
    work["properties"]["quantity"] = {"const": "volumetric_tensile_work_to_break"}
    work["properties"]["quantity_dimension"] = {"const": "energy_per_volume"}
    work["properties"]["reported_value"] = _ref("work_reported_value")
    work["properties"]["work_reference_basis"] = _ref("work_reference_basis")
    work["required"].append("work_reference_basis")
    definitions["thermal_mass_reference_basis"] = {"oneOf": deepcopy(definitions["fact"]["oneOf"][:3])}
    new_thermal = []
    for quantity, units in (("mass_specific_heat_capacity", HEAT_CAPACITY_UNITS), ("thermal_diffusivity", DIFFUSIVITY_UNITS)):
        value_name = quantity + "_reported_value"
        definitions[value_name] = deepcopy(definitions["reported_value"])
        for value in definitions[value_name]["oneOf"]:
            value["properties"]["unit_code"] = _enum(units)
        branch = deepcopy(other)
        branch["properties"]["quantity"] = {"const": quantity}
        branch["properties"]["quantity_dimension"] = {"const": QUANTITY_DIMENSIONS[quantity]}
        branch["properties"]["reported_value"] = _ref(value_name)
        if quantity == "mass_specific_heat_capacity":
            branch["properties"]["thermal_mass_reference_basis"] = _ref("thermal_mass_reference_basis")
            branch["required"].append("thermal_mass_reference_basis")
        new_thermal.append(branch)
    definitions["thermal_response_phase"] = _object({"code": _enum(("post_stretching_hold", "post_retraction_recovery")), "evidence": evidence, "notes": TEXT})
    definitions["thermal_convection"] = {"oneOf": [
        _object({"status": {"const": "reported"}, "regime": _enum(("natural_convection", "forced_convection")), "evidence": evidence, "notes": TEXT}),
        _object({"status": _enum(("not_reported_in_inspected_source", "not_verified")), "regime": NULL, "evidence": _array(_ref("evidence"), 0), "notes": TEXT}),
    ]}
    scalar = next(deepcopy(v) for v in definitions["reported_value"]["oneOf"] if v["properties"]["kind"].get("const") == "scalar")
    scalar["properties"]["unit_code"] = _enum(RESPONSE_TIME_UNITS)
    definitions["thermal_response_reported_value"] = scalar
    response = deepcopy(new_thermal[-1])
    response["properties"].update(quantity={"const": "thermal_response_characteristic_time"}, quantity_dimension={"const": "time"}, reported_value=_ref("thermal_response_reported_value"), thermal_response_phase=_ref("thermal_response_phase"), thermal_convection=_ref("thermal_convection"))
    response["required"].extend(("thermal_response_phase", "thermal_convection"))
    definitions["thermal_scan_definition"] = _object({
        "kind": {"const": "nonisothermal_temperature_scan"}, "evidence": evidence, "notes": TEXT,
    })
    definitions["thermal_scan_phase"] = {"oneOf": [
        _object({"status": {"const": "reported"}, "code": _enum(("heating", "cooling")), "evidence": evidence, "notes": TEXT}),
        _object({"status": _enum(("not_reported_in_inspected_source", "not_verified")), "code": NULL, "evidence": evidence, "notes": TEXT}),
    ]}
    definitions["thermal_phase_occurrence_ordinal"] = {"oneOf": [
        _object({"status": {"const": "reported"}, "value": {"type": "integer", "minimum": 1}, "evidence": evidence, "notes": TEXT}),
        _object({"status": _enum(("not_reported_in_inspected_source", "not_verified")), "value": NULL, "evidence": evidence, "notes": TEXT}),
    ]}
    crystallization = deepcopy(temperature)
    crystallization["properties"]["quantity"] = {"const": "crystallization_peak_temperature"}
    for qualifier in ("thermal_scan_definition", "thermal_scan_phase", "thermal_phase_occurrence_ordinal"):
        crystallization["properties"][qualifier] = _ref(qualifier)
        crystallization["required"].append(qualifier)
    definitions["degradation_endset_definition"] = {"oneOf": [
        _object({"status": {"const": "reported"}, "text": TEXT, "evidence": evidence, "notes": TEXT}),
        _object({"status": _enum(("not_reported_in_inspected_source", "not_verified")), "text": NULL, "evidence": evidence, "notes": TEXT}),
    ]}
    endset = deepcopy(temperature)
    endset["properties"]["quantity"] = {"const": "thermal_degradation_endset_temperature"}
    for qualifier in ("thermal_scan_definition", "degradation_endset_definition"):
        endset["properties"][qualifier] = _ref(qualifier)
        endset["required"].append(qualifier)
    from ._extension_contract import schema_branch
    extension = schema_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._water_absorption_contract import schema_branch as water_branch
    water = water_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._closed_cell_contract import schema_branch as closed_cell_branch
    closed_cell = closed_cell_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._foam_event_contract import schema_branch as foam_event_branch
    foam_event = foam_event_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._cell_anisotropy_contract import schema_branch as cell_anisotropy_branch
    cell_anisotropy = cell_anisotropy_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._dsc_enthalpy_contract import schema_branch as dsc_enthalpy_branch
    dsc_enthalpy = dsc_enthalpy_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._complex_viscosity_contract import schema_branch as complex_viscosity_branch
    complex_viscosity = complex_viscosity_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._gel_fraction_contract import schema_branch as gel_fraction_branch
    gel_fraction = gel_fraction_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._dma_flexural_contract import schema_branches as dma_schema_branches
    dma_branches = dma_schema_branches(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._dsc_crystallinity_contract import schema_branch as dsc_crystallinity_branch
    dsc_crystallinity = dsc_crystallinity_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._ftir_band_area_ratio_contract import schema_branch as ftir_area_ratio_branch
    ftir_area_ratio = ftir_area_ratio_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._sec_molar_mass_contract import schema_branches as sec_molar_mass_branches
    sec_branches = sec_molar_mass_branches(definitions, other, text=TEXT, https=HTTPS, obj=_object, array=_array, ref=_ref)
    from ._continuous_shear_contract import schema_branch as continuous_shear_branch
    continuous_shear = continuous_shear_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    from ._elemental_content_contract import schema_branch as elemental_content_branch
    elemental_content = elemental_content_branch(definitions, other, text=TEXT, obj=_object, array=_array, ref=_ref)
    definitions["property"] = {"oneOf": [other, stress, elongation, shore, temperature, electric, thermal, *tga_branches, work, *new_thermal, response, crystallization, endset, extension, water, closed_cell, foam_event, cell_anisotropy, dsc_enthalpy, complex_viscosity, gel_fraction, *dma_branches, dsc_crystallinity, ftir_area_ratio, *sec_branches, continuous_shear, elemental_content]}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:materials-boundaries:schema:reference_properties:1.0.0",
        "title": "Catalog-only source-reported reference properties v1",
        **_object({"schema_version": {"const": "1.0.0"}, "records": _array(_ref("property"))}),
        "$defs": definitions,
    }


# Runtime structure and the checked-in JSON schemas share a small, explicit
# schema vocabulary. The test suite checks exact equality to prevent drift.
_MATERIALS_SCHEMA = _make_materials_schema()
_PROPERTIES_SCHEMA = _make_properties_schema()


def _fail(path, message):
    raise ValueError(f"{path}: {message}")


def _same(value, expected):
    # Python's True == 1 must not make a boolean satisfy numeric constants.
    return type(value) is type(expected) and value == expected


_SCHEMA_TYPES = {"object": dict, "array": list, "string": str, "integer": int, "null": type(None)}


def _possible_branch(value, schema, root):
    """Cheap disjoint-branch pruning only; accepted branches still validate fully."""
    if "$ref" in schema:
        schema = root["$defs"][schema["$ref"].split("/")[-1]]
    kind = schema.get("type")
    if kind and type(value) is not _SCHEMA_TYPES[kind]:
        return False
    if "const" in schema and not _same(value, schema["const"]):
        return False
    if kind == "object":
        for key, field in schema["properties"].items():
            if "const" in field and key in value and not _same(value[key], field["const"]):
                return False
    return True


def _shape(value, schema, root, path):
    """Validate only the fixed schema vocabulary used above, without a dependency."""
    if "$ref" in schema:
        return _shape(value, root["$defs"][schema["$ref"].split("/")[-1]], root, path)
    for union in ("oneOf", "anyOf"):
        if union in schema:
            matches = 0
            for branch in schema[union]:
                if not _possible_branch(value, branch, root):
                    continue
                try:
                    _shape(value, branch, root, path)
                    matches += 1
                except ValueError:
                    pass
            if not matches or (union == "oneOf" and matches != 1):
                _fail(path, "does not match the closed " + union + " contract")
    if "const" in schema and not _same(value, schema["const"]):
        _fail(path, "expected constant " + repr(schema["const"]))
    if "enum" in schema and not any(_same(value, item) for item in schema["enum"]):
        _fail(path, "unsupported value")
    kind = schema.get("type")
    if kind and type(value) is not _SCHEMA_TYPES[kind]:
        _fail(path, "expected " + kind)
    if kind == "object":
        missing = set(schema["required"]) - value.keys()
        extra = value.keys() - schema["properties"].keys()
        if missing or extra:
            _fail(path, f"missing fields {sorted(missing)}; unsupported fields {sorted(extra, key=str)}")
        for key, item in value.items():
            _shape(item, schema["properties"][key], root, path + "." + key)
    elif kind == "array":
        if len(value) < schema.get("minItems", 0):
            _fail(path, "too few entries")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(set(encoded)) != len(encoded):
                _fail(path, "duplicate entries")
        for index, item in enumerate(value):
            _shape(item, schema["items"], root, f"{path}[{index}]")
    elif kind == "string":
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", float("inf")):
            _fail(path, "invalid string length")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            _fail(path, "invalid string syntax")
        if schema.get("format") == "date":
            try:
                date.fromisoformat(value)
            except ValueError:
                _fail(path, "invalid date")
        if schema.get("format") == "uri":
            _https(value, path)
    elif kind == "integer" and value < schema.get("minimum", value):
        _fail(path, "integer below minimum")



def validate_reference_text(value, path="text"):
    """Reject blank text, terminal controls and lone surrogates in display data.

    Valid Unicode scalar values, including astral symbols, remain unchanged.
    The new locale/presentation lane can reuse this exact text contract.
    """
    _shape(value, TEXT, {}, path)

def _https(value, path):
    if not isinstance(value, str) or re.search(_CONTROL_PATTERN, value) or any(char.isspace() for char in value):
        _fail(path, "expected an HTTPS URL")
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username
                 and not parsed.password and parsed.port in (None, 443))
    except ValueError:
        valid = False
    if not valid:
        _fail(path, "expected an HTTPS URL without embedded credentials")


def _all_evidence(value):
    if isinstance(value, dict):
        if set(value) == {"source_id", "url", "locator", "supports"}:
            yield value
        else:
            for item in value.values():
                yield from _all_evidence(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_evidence(item)


def _tagged(evidence, tag, source_id=None):
    return [entry for entry in evidence if tag in entry["supports"]
            and (source_id is None or entry["source_id"] == source_id)]


def _require_tag(evidence, tag, path, source_id=None):
    if not _tagged(evidence, tag, source_id):
        _fail(path, "missing primary evidence support: " + tag)


def _source_index(sources):
    # Source bibliographic shape stays owned by the unchanged source schema.
    # This lane validates the envelope, unique IDs and used HTTPS references.
    if not isinstance(sources, dict) or set(sources) != {"schema_version", "records"} or sources.get("schema_version") != "1.0.0" or not isinstance(sources.get("records"), list):
        _fail("sources", "expected source registry 1.0.0")
    result = {}
    for index, source in enumerate(sources["records"]):
        path = f"sources.records[{index}]"
        if not isinstance(source, dict) or not isinstance(source.get("id"), str) or not source["id"].strip() or re.search(_CONTROL_PATTERN, source["id"]):
            _fail(path, "missing source ID")
        if source["id"] in result:
            _fail(path, "duplicate source ID")
        if not isinstance(source.get("urls"), list) or not source["urls"] or not all(isinstance(url, str) and url.strip() for url in source["urls"]):
            _fail(path, "missing source URLs")
        result[source["id"]] = source
    return result


def _validate_structure(materials, properties):
    _shape(materials, _MATERIALS_SCHEMA, _MATERIALS_SCHEMA, "materials")
    _shape(properties, _PROPERTIES_SCHEMA, _PROPERTIES_SCHEMA, "reference_properties")
    indices = []
    seen = set()
    for name, rows in (("identities", materials["identities"]), ("grades", materials["grades"]),
                       ("states", materials["records"]), ("properties", properties["records"])):
        index = {}
        for row in rows:
            if row["id"] in seen:
                _fail(name, "duplicate ID " + row["id"])
            seen.add(row["id"])
            index[row["id"]] = row
        indices.append(index)
    _reject_structural_duplicates(materials)
    from ._material_derivation import canonical_identity_key, validate_taxon, validate_baseline_exclusions
    validate_baseline_exclusions(materials)
    keys = set()
    for identity in materials["identities"]:
        validate_taxon(identity)
        key = canonical_identity_key(identity)
        if key in keys:
            _fail(identity["id"], "duplicate canonical material identity")
        keys.add(key)
    return indices



def _structural_signature(value, field=None):
    """Stable factual signature; repeated evidence and evidence/support order are immaterial."""
    if isinstance(value, dict):
        return {key: _structural_signature(item, key) for key, item in sorted(value.items())}
    if isinstance(value, list):
        values = [_structural_signature(item) for item in value]
        if field == "evidence":
            unique = {json.dumps(item, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":")): item for item in values}
            return [unique[key] for key in sorted(unique)]
        if field == "supports":
            values.sort(key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
        return values
    return value


def _reject_structural_duplicates(materials):
    """Reject exact factual clones, without inferring chemical equivalence.

    Names, translations, aliases and new IDs cannot create distinct materials.
    Genuinely distinct curated scopes still require source admission/review.
    """
    groups = (
        ("identity", materials["identities"], lambda record: {
            key: record[key] for key in ("category", "identity_scope", "evidence")}),
        ("grade", materials["grades"], lambda record: {
            "identity_id": record["identity_id"], "authority": record["authority"],
            "designation": record["designation"],
            "manufacturer": {key: record["manufacturer"][key] for key in ("status", "text")}}),
        ("state", materials["records"], lambda record: {
            key: record[key] for key in ("identity_id", "grade_id", "source_designation", "state", "source_scope", "evidence")}),
    )
    for kind, records, select in groups:
        seen = {}
        for record in records:
            signature = json.dumps(_structural_signature(select(record)), sort_keys=True, ensure_ascii=False)
            if signature in seen:
                _fail(record["id"], f"duplicate structural {kind} of {seen[signature]}; new IDs or display labels do not create distinct coverage")
            seen[signature] = record["id"]

def _validate_links(materials, properties, indices):
    identities, grades, states, props = indices
    reached_identities, reached_grades = set(), set()
    owners = {key: set() for key in states}
    for grade in grades.values():
        if grade["identity_id"] not in identities:
            _fail(grade["id"], "unknown identity")
    for prop in props.values():
        if prop["material_state_id"] not in states:
            _fail(prop["id"], "unknown material state")
        owners[prop["material_state_id"]].add(prop["id"])
    for state in states.values():
        if state["identity_id"] not in identities:
            _fail(state["id"], "unknown identity")
        reached_identities.add(state["identity_id"])
        grade_id = state["grade_id"]
        if grade_id is not None:
            if grade_id not in grades or grades[grade_id]["identity_id"] != state["identity_id"]:
                _fail(state["id"], "unknown grade or wrong grade identity")
            reached_grades.add(grade_id)
        if set(state["property_ids"]) != owners[state["id"]]:
            _fail(state["id"], "property links and ownership must be reciprocal and complete")
    if reached_identities != set(identities) or reached_grades != set(grades):
        _fail("materials", "orphan identity or grade")


# Only spelling/typography normalization; these mappings never change a unit or
# infer a quantity. Unknown spellings need deliberate capability review.
_UNIT_SPELLINGS = {
    "percent_elemental_mass_content": {"wt.%", "wt%", "mass %"},
    "Pa_s_continuous_shear_viscosity": {"Pa.s", "Pa·s", "Pa s"},
    "kPa_s_complex_viscosity": {"kPa.s", "kPa·s", "kPa s"},
    "J_per_g_dsc_melting_enthalpy": {"J/g", "J g^-1", "J g−1"},
    "ratio_foam_cell_geometric_anisotropy": {"1", "ratio", "dimensionless"},
    "GPa_dma_flexural_storage": {"GPa"},
    "ratio_dma_flexural_loss_tangent": {"1", "dimensionless", "tan delta"},
    "percent_dsc_reference_crystallinity": {"%"},
    "ratio_ftir_fitted_carbonyl_areas": {"ratio"},
    "g_per_mol_sec_molar_mass": {"g/mol", "g·mol⁻¹"},
    "kg_per_mol_sec_molar_mass": {"kg/mol", "kg·mol⁻¹"},
    "ten5_g_per_mol_sec_molar_mass": {"×10^5 g/mol", "×10⁵ g·mol⁻¹"},
    "ratio_sec_molar_mass_dispersity": {"ratio"},
    "percent_solvent_extraction_gel_fraction": {"%"},
    "percent_closed_cell_content_volume": {"vol.%", "vol%", "V%"},
    "percent_water_absorption_volume": {"V%", "vol.%", "vol%"},
    "s": {"s"}, "ms": {"ms"},
    "J/(g*K)": {"J/(g*K)", "J/(g·K)", "J/g·K"},
    "J/(kg*K)": {"J/(kg*K)", "J/(kg·K)"},
    "kJ/(kg*K)": {"kJ/(kg*K)", "kJ/(kg·K)"},
    "mm^2/s": {"mm^2/s", "mm²/s", "mm2/s"},
    "m^2/s": {"m^2/s", "m²/s", "m2/s"},
    "J/cm^3": {"J/cm^3", "J/cm³", "J/cm3"},
    "MJ/m^3": {"MJ/m^3", "MJ/m³", "MJ/m3"},
    "J/m^3": {"J/m^3", "J/m³", "J/m3"},
    "percent_tga_residue": {"%"}, "percent_mass_loss": {"%"},
    "W/(m*K)": {"W/(m*K)", "W/(m·K)", "W/m·K"},
    "mW/(m*K)": {"mW/(m*K)", "mW/(m·K)"},
    "V/m": {"V/m"}, "kV/mm": {"kV/mm"},
    "degC": {"°C", "° C", "degC"}, "K": {"K"},
    "mm": {"mm"},
    "kJ/m^2": {"kJ/m^2", "kJ/m2", "kJ/m²"},
    "J/m^2": {"J/m^2", "J/m2", "J/m²"},
    "shore_a_scale": {"Shore A"},
    "kN/m": {"kN/m"}, "N/m": {"N/m"}, "N/mm": {"N/mm"},
    "g/cm^3": {"g/cm^3", "g/cm³", "g/cm3", "g cm^-3", "g.cm-3", "g cm⁻³", "g·cm⁻³", "g cm−3", "g cm-3", "grams per cubic centimeter"},
    "kg/m^3": {"kg/m^3", "kg/m³", "kg/m3", "kg m^-3", "kg.m-3", "kg m⁻³", "kg·m⁻³", "kg m−3", "kg m-3"},
    "kg/dm^3": {"kg/dm^3", "kg/dm³", "kg/dm3", "kg dm^-3", "kg.dm-3", "kg dm⁻³", "kg·dm⁻³", "kg dm−3", "kg dm-3"},
    "lb/in^3": {"lb/in^3", "lb/in³", "lb/in3", "lb./in.³", "lb./in.3", "lb./in.^3"},
    "MPa": {"MPa"}, "GPa": {"GPa"},
    "N/mm^2": {"N/mm^2", "N/mm²", "N/mm2"},
    "kN/mm^2": {"kN/mm^2", "kN/mm²", "kN/mm2"},
    # Relative measures and specified-elongation descriptors use this spelling;
    # UNIT_DIMENSIONS and central-result units deliberately exclude percent.
    "percent": {"%"},
    "percent_elongation": {"%"},
}


def _scientific_token_matches(token, canonical):
    """Validate exact bounded source notation, never a general expression.

    Admit a fixed-point mantissa, literal ASCII spaces around multiplication,
    and either caret or superscript integer power of ten. A Decimal tuple shifts
    the exponent exactly without ambient-context rounding. Formatting retains
    the mantissa's fractional precision after expansion; the source string is
    never rewritten. Both the mantissa and expanded value obey DECIMAL limits.
    """
    match = re.fullmatch(
        r"((?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?) × 10"
        r"(?:\^(-?(?:0|[1-9][0-9]?))|([⁻]?[⁰¹²³⁴⁵⁶⁷⁸⁹]{1,2}))", token)
    if not match or not re.fullmatch(DECIMAL_PATTERN, canonical):
        return False
    exponent_text = match[2] if match[2] is not None else match[3].translate(
        str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "-0123456789"))
    if not re.fullmatch(r"(?:0|[1-9][0-9]?|-[1-9][0-9]?)", exponent_text):
        return False
    power = int(exponent_text)
    if not -24 <= power <= 24:
        return False
    value = Decimal(match[1]).as_tuple()
    expanded = format(Decimal((value.sign, value.digits, value.exponent + power)), "f")
    return bool(re.fullmatch(DECIMAL_PATTERN, expanded)) and expanded == canonical


def _numeric_token_matches(token, canonical):
    """Match only source lexical forms, including precision and grouped digits.

    Canonical strings disambiguate comma/point conventions; a source review must
    justify the convention. The validator refuses extra/removed significant
    decimal zeroes and cannot adjudicate an ambiguous source's typography.
    """
    if "×" in token:
        return len(token) <= 96 and _scientific_token_matches(token, canonical)
    token = token.strip()
    if not token or len(token) > 96:
        return False
    candidates = set()
    # Plain decimal or comma-decimal; preserve decimal precision exactly.
    if re.fullmatch(r"(?:0|[1-9][0-9]*)(?:[.,][0-9]+)?", token):
        candidates.add(token.replace(",", "."))
    # Explicit three-digit grouping, with optional opposite decimal separator.
    for grouping, decimal in ((",", "."), (".", ","), (" ", "."), (" ", ","),
                              ("\u00a0", "."), ("\u00a0", ","), ("\u202f", "."), ("\u202f", ",")):
        pattern = r"[1-9][0-9]{0,2}(?:" + re.escape(grouping) + r"[0-9]{3})+(?:" + re.escape(decimal) + r"[0-9]+)?"
        if re.fullmatch(pattern, token):
            candidates.add(token.replace(grouping, "").replace(decimal, "."))
    # Printed decimal fractional groups: exactly one ASCII space between
    # nonempty digit groups after one decimal point. The first fractional group
    # has three digits; subsequent groups have three digits except the final
    # group, which may have one to four. This covers scientific digit spacing
    # without deleting arbitrary whitespace or relaxing decimal precision.
    if re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{3}(?: [0-9]{3})* [0-9]{1,4}", token):
        candidates.add(token.replace(" ", ""))
    # A source may print an integer SD as 04, 03 or 02. Preserve that source
    # token while matching its exact integer value; no decimal rescaling or
    # fractional-precision change is implied by leading integer zeroes.
    if re.fullmatch(r"0[0-9]+", token):
        candidates.add(token.lstrip("0") or "0")
    return canonical in candidates


def _validate_value(value, path, dimension=None, nonnegative=False):
    if dimension is not None and UNIT_DIMENSIONS[value["unit_code"]] != dimension:
        _fail(path, "unit does not match quantity dimension")
    if value["unit_text"].strip() not in _UNIT_SPELLINGS[value["unit_code"]]:
        _fail(path, "unit text is not an admitted spelling of unit code")
    kind = value.get("kind", "scalar")
    numbers = [value["lower"], value["upper"]] if kind == "interval" else [value["number"]]
    for number in numbers:
        decimal = Decimal(number)
        if decimal < 0 or (not nonnegative and decimal == 0):
            _fail(path, "value must be nonnegative" if nonnegative else "value must be positive")
    text = value["value_text"].strip()
    if kind == "interval":
        if Decimal(value["lower"]) >= Decimal(value["upper"]):
            _fail(path, "interval endpoints must be strictly ordered")
        pieces = re.split(r"\s*(?:–|—|−|-|\bto\b)\s*", text)
        if len(pieces) != 2 or not all(_numeric_token_matches(piece, number) for piece, number in zip(pieces, numbers)):
            _fail(path, "interval source text does not preserve parsed endpoints/precision")
    elif kind == "comparison":
        match = re.fullmatch(r"(>=|<=|>|<|≥|≤)\s*(.+)", text)
        if not match or {"≥": ">=", "≤": "<="}.get(match[1], match[1]) != value["operator"] or not _numeric_token_matches(match[2], value["number"]):
            _fail(path, "comparison source text does not preserve operator/value/precision")
    elif not _numeric_token_matches(value["value_text"], value["number"]):
        _fail(path, "source text does not preserve scalar value/precision")


def _temperature_token_matches(token, canonical):
    """Preserve temperature polarity; reuse exact unsigned magnitude spelling."""
    token = token.strip()
    negative = canonical.startswith("-")
    if negative:
        if not token.startswith(("-", "−")):
            return False
        return _numeric_token_matches(token[1:], canonical[1:])
    if token.startswith(("-", "−")):
        return False
    return _numeric_token_matches(token[1:] if token.startswith("+") else token, canonical)


def _validate_temperature_value(value, path):
    """Check source coordinates, not a thermal criterion or physical attainability."""
    unit = value["unit_code"]
    if unit not in TEMPERATURE_UNITS or value["unit_text"].strip() not in _UNIT_SPELLINGS[unit]:
        _fail(path, "unsupported temperature unit or spelling")
    kind = value["kind"]
    numbers = [value["lower"], value["upper"]] if kind == "interval" else [value["number"]]
    floor = Decimal("-273.15") if unit == "degC" else Decimal("0")
    if any(Decimal(n) < floor for n in numbers):
        _fail(path, "temperature coordinate below absolute zero")
    text = value["value_text"].strip()
    if kind == "interval":
        if Decimal(value["lower"]) >= Decimal(value["upper"]):
            _fail(path, "temperature interval endpoints must be strictly ordered")
        # Unary minus is never an unspaced separator for signed endpoints.
        # Distinct en/em dash, 'to', or a spaced hyphen are unambiguous.
        separators = r"\bto\b|[–—]|\s+[-−]\s+"
        if not any(n.startswith("-") for n in numbers):
            separators += r"|[-−]"
        matches = 0
        for sep in re.finditer(separators, text):
            if (_temperature_token_matches(text[:sep.start()], value["lower"])
                    and _temperature_token_matches(text[sep.end():], value["upper"])):
                matches += 1
        if matches != 1:
            _fail(path, "temperature interval text must preserve unambiguous signed endpoints/precision")
    elif kind == "comparison":
        match = re.fullmatch(r"(>=|<=|>|<|≥|≤)\s*(.+)", text)
        if (not match or {"≥": ">=", "≤": "<="}.get(match[1], match[1]) != value["operator"]
                or not _temperature_token_matches(match[2], value["number"])):
            _fail(path, "temperature comparison text must preserve operator/polarity/precision")
    elif not _temperature_token_matches(text, value["number"]):
        _fail(path, "temperature scalar text must preserve polarity/precision")


def _absolute_uncertainty_unit_matches(prop, unit):
    central = prop["reported_value"]["unit_code"]
    if prop["quantity"] == "thermal_degradation_endset_temperature":
        return unit == central
    return (unit == central or (prop["quantity"] in RESULT_TEMPERATURE_QUANTITIES
            and central in TEMPERATURE_UNITS and unit in TEMPERATURE_UNITS))


def _validate_reported_measures(prop, path):
    """Check declared measure metadata, not the truth of source prose.

    Evidence kind, qualifier, scope and explanatory-note fidelity remain a
    source-review obligation. These checks prevent structurally incompatible
    reinterpretation, invention of graphical amplitudes and silent conversion.
    """
    source = prop["source_id"]
    primary_evidence = {
        (item["source_id"], item["url"], item["locator"])
        for item in _tagged(prop["evidence"], "uncertainty", source)
    }
    seen = set()
    for index, measure in enumerate(prop["uncertainty"]["measures"]):
        measure_path = f"{path}.uncertainty.measures[{index}]"
        for item in measure["evidence"]:
            reference = (item["source_id"], item["url"], item["locator"])
            if "uncertainty" not in item["supports"] or reference not in primary_evidence:
                _fail(measure_path, "measure needs matching primary uncertainty source/URL/locator in property evidence")
            descriptor = (measure["kind"], measure["basis"], *reference)
            if descriptor in seen:
                _fail(measure_path, "duplicate reported measure kind/basis/source/locator")
            seen.add(descriptor)
        if measure["kind"] == "standard_error_of_mean" and prop["summary_statistic"] != "reported_mean":
            _fail(measure_path, "standard error of mean requires an independently evidenced reported mean")
        if measure["kind"] == "standard_deviation" and prop["summary_statistic"] != "reported_mean" and measure["note"] is None:
            _fail(measure_path, "SD with unspecified central aggregation requires an explicit explanatory note")
        if measure["availability"] == "graphical_only":
            if not any(re.search(r"\bfig(?:ure)?\.?\s*[0-9]+[a-z]?\b", item["locator"], re.IGNORECASE)
                       for item in measure["evidence"]):
                _fail(measure_path, "graphical SD requires an exact figure/panel/caption locator")
            continue
        value = measure["reported_value"]
        if measure["basis"] == "absolute":
            if not _absolute_uncertainty_unit_matches(prop, value["unit_code"]):
                _fail(measure_path, "absolute measure unit must equal result unit")
            _validate_value(value, measure_path, prop["quantity_dimension"], nonnegative=True)
        else:
            if prop["quantity"] in RESULT_TEMPERATURE_QUANTITIES and measure["note"] is None:
                _fail(measure_path, "relative temperature measure needs a source-scale/origin caveat")
            _validate_value(value, measure_path, nonnegative=True)


def _validate_property(prop):
    path = prop["id"]
    source = prop["source_id"]
    dimension = QUANTITY_DIMENSIONS[prop["quantity"]]
    if prop["quantity_dimension"] != dimension:
        _fail(path, "quantity dimension mismatch")
    if prop["quantity"] == "dsc_reported_melting_specific_enthalpy":
        from ._dsc_enthalpy_contract import validate_value as validate_dsc_enthalpy_value
        validate_dsc_enthalpy_value(prop["reported_value"], path + ".reported_value", _fail, _temperature_token_matches)
    elif prop["quantity"] in RESULT_TEMPERATURE_QUANTITIES:
        _validate_temperature_value(prop["reported_value"], path + ".reported_value")
    else:
        _validate_value(prop["reported_value"], path + ".reported_value", dimension,
                        nonnegative=(prop["quantity"] in PERCENT_ELONGATION_QUANTITIES or
                                     prop["quantity"] in {"source_reported_elemental_mass_content_percentage", "source_reported_continuous_shear_viscosity", "oscillatory_complex_viscosity_magnitude", "foam_reaction_event_time", "dma_flexural_storage_modulus", "dma_flexural_loss_tangent", "dsc_reference_normalized_crystallinity_percentage", "ftir_fitted_carbonyl_band_area_ratio", "sec_weight_average_molar_mass", "sec_number_average_molar_mass", "sec_source_reported_molar_mass_dispersity", "solvent_extraction_gel_fraction_percentage", "closed_cell_content_volume_percentage", "water_absorption_volume_percentage", "tensile_extension_at_failure", "shore_a_hardness", "tga_residue_percentage", "volumetric_tensile_work_to_break"}))
    from ._extension_contract import validate as validate_extension
    validate_extension(prop, _fail)
    from ._water_absorption_contract import validate as validate_water_absorption
    validate_water_absorption(prop, _fail)
    from ._dma_flexural_contract import validate as validate_dma
    validate_dma(prop, _fail, _numeric_token_matches, _validate_temperature_value)
    from ._gel_fraction_contract import validate as validate_gel_fraction
    validate_gel_fraction(prop, _fail)
    from ._closed_cell_contract import validate as validate_closed_cell
    validate_closed_cell(prop, _fail)
    from ._foam_event_contract import validate as validate_foam_event
    validate_foam_event(prop, _fail)
    from ._cell_anisotropy_contract import validate as validate_cell_anisotropy
    validate_cell_anisotropy(prop, _fail)
    from ._dsc_enthalpy_contract import validate as validate_dsc_enthalpy
    validate_dsc_enthalpy(prop, _fail)
    from ._complex_viscosity_contract import validate as validate_complex_viscosity
    validate_complex_viscosity(prop, _fail, _numeric_token_matches)
    from ._continuous_shear_contract import validate as validate_continuous_shear
    validate_continuous_shear(prop, _fail, _numeric_token_matches, _validate_temperature_value)
    from ._elemental_content_contract import validate as validate_elemental_content
    validate_elemental_content(prop, _fail)
    for field in ("specified_mass_loss", "degradation_peak_ordinal", "residue_endpoint_temperature", "mass_reference_basis"):
        if field not in prop:
            continue
        descriptor = prop[field]
        if field == "specified_mass_loss":
            _validate_value(descriptor, path + "." + field)
            if Decimal(descriptor["number"]) > 100:
                _fail(path, "fractional mass-loss percentage must not exceed 100")
        elif field == "residue_endpoint_temperature":
            _validate_temperature_value(descriptor, path + "." + field)
        if field != "mass_reference_basis" or descriptor["status"] == "reported":
            _require_tag(descriptor["evidence"], "condition", path + "." + field, source)
            if not any(e["url"] == prop["source_document"]["url"]
                       for e in _tagged(descriptor["evidence"], "condition", source)):
                _fail(path, "TGA qualifier needs primary inspected-document condition evidence")
    if prop["quantity"] == "thermal_degradation_endset_temperature":
        for field in ("thermal_scan_definition", "degradation_endset_definition"):
            descriptor = prop[field]
            roles = ("method", "condition") if field == "thermal_scan_definition" or descriptor.get("status") == "reported" else ("condition",)
            for role in roles:
                _require_tag(descriptor["evidence"], role, path + "." + field, source)
                if not any(e["url"] == prop["source_document"]["url"]
                           for e in _tagged(descriptor["evidence"], role, source)):
                    _fail(path, "TGA endset qualifiers need primary inspected-document evidence")
    if prop["quantity"] == "crystallization_peak_temperature":
        for field in ("thermal_scan_definition", "thermal_scan_phase", "thermal_phase_occurrence_ordinal"):
            descriptor = prop[field]
            roles = ("method", "condition") if field == "thermal_scan_definition" else ("condition",)
            for role in roles:
                _require_tag(descriptor["evidence"], role, path + "." + field, source)
                if not any(e["url"] == prop["source_document"]["url"]
                           for e in _tagged(descriptor["evidence"], role, source)):
                    _fail(path, "Crystallization scan qualifiers need primary inspected-document evidence")
    if "thermal_mass_reference_basis" in prop:
        basis = prop["thermal_mass_reference_basis"]
        if basis["status"] == "reported":
            _require_tag(basis["evidence"], "condition", path + ".thermal_mass_reference_basis", source)
            if not any(e["url"] == prop["source_document"]["url"] for e in _tagged(basis["evidence"], "condition", source)):
                _fail(path, "Thermal mass basis needs primary inspected-document condition evidence")
        elif not basis["notes"]:
            _fail(path, "Unknown thermal mass basis needs an explanatory note")
    if "work_reference_basis" in prop:
        basis = prop["work_reference_basis"]
        if basis["status"] == "reported":
            _require_tag(basis["evidence"], "condition", path + ".work_reference_basis", source)
            if not any(e["url"] == prop["source_document"]["url"] for e in _tagged(basis["evidence"], "condition", source)):
                _fail(path, "Work basis needs primary inspected-document condition evidence")
        elif not basis["notes"]:
            _fail(path, "Unknown work reference basis needs an explanatory note")
    if prop["quantity"] == "shore_a_hardness":
        value = prop["reported_value"]
        numbers = [value["lower"], value["upper"]] if value["kind"] == "interval" else [value["number"]]
        if any(Decimal(number) > 100 for number in numbers):
            _fail(path, "Shore A central values must be between 0 and 100 inclusive")
    if prop["quantity"] == "tensile_stress_at_specified_elongation":
        target = prop["specified_elongation"]
        _validate_value(target, path + ".specified_elongation")
        _require_tag(target["evidence"], "condition", path + ".specified_elongation", source)
    if (prop["density_basis"] is not None) != (prop["quantity"] in {"mass_density", "basic_wood_density"}):
        _fail(path, "density_basis required only for density")
    for tag in ("reported_value", "classification"):
        _require_tag(prop["evidence"], tag, path, source)
    value_evidence = _tagged(prop["evidence"], "reported_value", source)
    if not any(entry["url"] == prop["source_document"]["url"] for entry in value_evidence):
        _fail(path, "primary value evidence must identify inspected document")
    _require_tag(prop["method_definition"]["evidence"], "method", path, source)
    window = prop["method_definition"]["extraction_window"]
    if window is not None:
        _require_tag(window["evidence"], "method", path + ".extraction_window", source)
    for fact in prop["conditions"].values():
        facts = [item["fact"] for item in fact] if isinstance(fact, list) else [fact]
        for item in facts:
            if item["status"] == "reported":
                _require_tag(item["evidence"], "condition", path, source)
    extras = prop["conditions"].get("additional_conditions", [])
    if len({item["name"] for item in extras}) != len(extras):
        _fail(path, "duplicate additional condition names")
    doc = prop["source_document"]
    document_url = urlsplit(doc["url"])
    if document_url.path in ("", "/") and not document_url.query and not document_url.fragment:
        _fail(path, "primary value needs a specific document/table page, not a homepage")
    if doc["hash_status"] == "recorded":
        if doc["sha256"] is None or doc["hash_note"] is not None:
            _fail(path, "recorded hash requires digest and null hash note")
    elif doc["sha256"] is not None or doc["hash_note"] is None:
        _fail(path, "unavailable/not-retained hash requires null digest and explanation")
    if prop["verification"]["source_inspection_scope"] != doc["inspection_scope"]:
        _fail(path, "verification and document inspection scope disagree")
    expected_basis = {"published_experimental_reference": "source_reports_measurement",
                      "published_computational_reference": "source_reports_calculation",
                      "published_handbook_reference": "source_reports_compiled_measurements",
                      "published_measurement_derived_reference": "source_reports_calculation"}
    if prop["evidence_kind"] in expected_basis and prop["determination_basis"] != expected_basis[prop["evidence_kind"]]:
        _fail(path, "published evidence class contradicts determination basis")
    # These method classes are generic physical/provenance contracts, never
    # material-ID exceptions. Both directions are checked: a relabel cannot turn
    # a compilation or crystallographic calculation into a direct experiment.
    method = prop["method_definition"]["type"]
    if ((prop["evidence_kind"] == "published_handbook_reference") !=
            (method == "source_reported_compilation")):
        _fail(path, "handbook evidence requires its compilation method class")
    if ((prop["determination_basis"] == "source_reports_compiled_measurements") !=
            (prop["evidence_kind"] == "published_handbook_reference")):
        _fail(path, "compiled measurements require handbook evidence")
    is_derived = prop["evidence_kind"] == "published_measurement_derived_reference"
    is_crystallographic = method == "source_reported_crystallographic_derivation"
    is_empirical = method == "source_reported_empirical_conversion"
    is_thermal_product = method == "source_reported_thermal_transport_product"
    is_thermal_fit = method == "source_reported_thermal_response_fit"
    is_dsc_normalization = method == "source_reported_dsc_reference_normalization"
    is_ftir_area_ratio = method == "source_reported_ftir_fitted_band_area_ratio"
    is_sec_dispersity = method == "source_reported_sec_molar_mass_dispersity"
    if is_derived != (is_sec_dispersity or is_ftir_area_ratio or is_crystallographic or is_empirical or is_thermal_product or is_thermal_fit or is_dsc_normalization):
        _fail(path, "measured-input-derived evidence requires an admitted derivation method")
    is_computational_crystal = method == "source_reported_computational_structure_density"
    if (prop["density_basis"] == "crystallographic") != (is_crystallographic or is_computational_crystal):
        _fail(path, "crystallographic density requires its source-reported structural method")
    if (is_crystallographic or is_computational_crystal) and prop["quantity"] != "mass_density":
        _fail(path, "crystallographic density requires mass density")
    if is_computational_crystal and prop["evidence_kind"] != "published_computational_reference":
        _fail(path, "computed-structure density requires computational evidence")
    is_molecular_simulation = method == "source_reported_molecular_simulation_density"
    if (prop["density_basis"] == "simulation_cell") != is_molecular_simulation:
        _fail(path, "simulation-cell density requires its molecular-simulation method")
    if is_molecular_simulation and prop["quantity"] != "mass_density":
        _fail(path, "molecular-simulation density requires mass density")
    if is_molecular_simulation and prop["evidence_kind"] != "published_computational_reference":
        _fail(path, "molecular-simulation density requires computational evidence")
    from ._material_derivation import validate_derivation
    validate_derivation(prop)
    if prop["quantity"] == "basic_wood_density" and not is_empirical:
        _fail(path, "basic wood density requires an admitted basis-preserving derivation profile")
    if method != "source_reported_conventional":
        _require_tag(prop["method_definition"]["evidence"], "classification", path, source)
    is_mean = prop["summary_statistic"] == "reported_mean"
    if is_mean:
        if prop["reporting_basis"] != "reported_summary" or prop["reported_value"]["kind"] != "scalar":
            _fail(path, "reported mean requires scalar reported_summary")
        _require_tag(prop["evidence"], "summary_statistic", path, source)
    uncertainty = prop["uncertainty"]
    if uncertainty is not None:
        kind = uncertainty["type"]
        if prop["uncertainty_status"] != kind:
            _fail(path, "uncertainty status must match its reported numerical type")
        if prop["reported_value"]["kind"] != "scalar":
            _fail(path, "reported uncertainty requires a scalar central result")
        if kind == "reported_measures":
            _validate_reported_measures(prop, path)
        if kind == "reported_standard_deviation" and not is_mean:
            _fail(path, "SD requires explicit reported mean and uncertainty status")
        if kind != "reported_measures":
            if not _absolute_uncertainty_unit_matches(prop, uncertainty["unit_code"]):
                _fail(path, "uncertainty unit must equal result unit")
            _validate_value(uncertainty, path + ".uncertainty", dimension, nonnegative=True)
            _require_tag(uncertainty["evidence"], "uncertainty", path, source)
        if kind == "reported_confidence_interval":
            level = uncertainty["confidence_level"]
            if not Decimal("0") < Decimal(level["number"]) < Decimal("100"):
                _fail(path, "confidence level must be strictly between 0 and 100 percent")
            match = re.fullmatch(r"(.+?)\s*%", level["value_text"].strip())
            if not match or not _numeric_token_matches(match[1], level["number"]):
                _fail(path, "confidence-level text must preserve percent value and precision")
            for name in ("estimand", "construction"):
                if uncertainty[name]["status"] == "reported":
                    _require_tag(uncertainty[name]["evidence"], "uncertainty", path + "." + name, source)
    elif prop["uncertainty_status"] in REPORTED_UNCERTAINTIES:
        _fail(path, "reported uncertainty status requires its matching nonnull envelope")
    count = prop["sample_count"]
    if count["value"] is not None:
        _require_tag(count["evidence"], "sample_count", path, source)
    for discrepancy in prop["source_discrepancies"]:
        _require_tag(discrepancy["evidence"], "source_discrepancy", path, source)
    if "apparent" in prop["source_property_label"].casefold() and prop["quantity"] != "mass_density":
        _fail(path, "source-defined apparent mechanical quantities are deferred")



def _tga_coordinate_key(prop):
    """Typed coordinates only: evidence/notes cannot manufacture coverage."""
    result = {}
    for field in ("specified_mass_loss", "residue_endpoint_temperature"):
        if field in prop:
            value = prop[field]
            decimal = Decimal(value["number"])
            if decimal == 0:
                number = [0, [], 0]
            else:
                token = decimal.as_tuple()
                digits, exponent = list(token.digits), token.exponent
                while digits[-1] == 0:
                    digits.pop()
                    exponent += 1
                number = [token.sign, digits, exponent]
            result[field] = [value["unit_code"], number]
    if "degradation_peak_ordinal" in prop:
        result["degradation_peak_ordinal"] = prop["degradation_peak_ordinal"]["value"]
    if "mass_reference_basis" in prop:
        basis = prop["mass_reference_basis"]
        result["mass_reference_basis"] = (["reported", basis["text"]]
                                          if basis["status"] == "reported" else ["unknown", None])
    return result


def _coordinate_fact_base(signature, field, ordinal=None):
    """Exact same-cell/value/protocol key without the coordinates under review."""
    base = json.loads(signature)
    if ordinal is None:
        base[field] = {}
    else:
        base[field].pop(ordinal)
    for name in ("number", "lower", "upper"):
        if name not in base["value"]:
            continue
        token = Decimal(base["value"][name]).as_tuple()
        digits, exponent = list(token.digits), token.exponent
        if not any(digits):
            base["value"][name] = [0, [], 0]
        else:
            while digits[-1] == 0:
                digits.pop()
                exponent += 1
            base["value"][name] = [token.sign, digits, exponent]
    return json.dumps(base, sort_keys=True, ensure_ascii=False)


def _crystallization_coordinate_guard(prop, signature, seen):
    """Index partial coordinates without treating unknowns as new coverage."""
    base = _coordinate_fact_base(signature, "crystallization_coordinates")
    phase = prop["thermal_scan_phase"]["code"]
    ordinal = prop["thermal_phase_occurrence_ordinal"]["value"]
    def key(kind, *coordinates):
        return "crystallization:" + json.dumps([base, kind, *coordinates], ensure_ascii=False)
    if phase is None and ordinal is None:
        overlap = key("any") in seen
        additions = (key("uu"),)
    elif phase is None:
        overlap = any(k in seen for k in (key("uu"), key("pu_any"), key("uo", ordinal), key("po_ordinal", ordinal)))
        additions = (key("uo", ordinal), key("uo_any"))
    elif ordinal is None:
        overlap = any(k in seen for k in (key("uu"), key("uo_any"), key("pu", phase), key("po_phase", phase)))
        additions = (key("pu", phase), key("pu_any"))
    else:
        overlap = any(k in seen for k in (key("uu"), key("uo", ordinal), key("pu", phase), key("po", phase, ordinal)))
        additions = (key("po", phase, ordinal), key("po_phase", phase), key("po_ordinal", ordinal))
    if overlap:
        _fail(prop["id"], "duplicate source fact for overlapping crystallization coordinates")
    seen.update(additions)
    seen.add(key("any"))


def _unique_fact(prop, seen, identity_id=None):
    from ._sec_molar_mass_contract import guard_cell as guard_sec_cell
    guard_sec_cell(prop, seen, identity_id)
    from ._continuous_shear_contract import guard_cell as guard_continuous_shear_cell
    guard_continuous_shear_cell(prop, seen)
    from ._elemental_content_contract import guard_cell as guard_elemental_content_cell
    guard_elemental_content_cell(prop, seen)
    value = prop["reported_value"]
    represented_value = {key: item for key, item in value.items() if key not in {"value_text", "unit_text"}}
    # An omitted optional array and an explicitly empty array encode the same
    # condition set. Its order is presentation only, never a new source fact.
    conditions = {"additional_conditions": []}
    for key, fact in prop["conditions"].items():
        if key == "additional_conditions":
            conditions[key] = sorted(
                ({"name": item["name"], "status": item["fact"]["status"], "text": item["fact"]["text"]} for item in fact),
                key=lambda item: item["name"],
            )
        else:
            conditions[key] = {"status": fact["status"], "text": fact["text"]}
    # Decimal tuples avoid rounding under an ambient low-precision context.
    # Target typography is preserved in the record but cannot create a new fact.
    elongation_key = None
    if "specified_elongation" in prop:
        target = Decimal(prop["specified_elongation"]["number"]).as_tuple()
        digits, exponent = list(target.digits), target.exponent
        while digits and digits[-1] == 0:
            digits.pop()
            exponent += 1
        elongation_key = [target.sign, digits, exponent]
    signature = json.dumps({
        "state": prop["material_state_id"], "quantity": prop["quantity"],
        "document": prop["source_document"]["url"],
        "locators": sorted({entry["locator"] for entry in _tagged(prop["evidence"], "reported_value", prop["source_id"])}),
        "value": represented_value, "conditions": conditions,
        "specified_elongation": elongation_key,
        **({"thermal_response": [prop["thermal_response_phase"]["code"],
            prop["thermal_convection"]["regime"] if prop["thermal_convection"]["status"] == "reported" else "unknown"]}
            if "thermal_response_phase" in prop else {}),
        **({"thermal_mass_basis": (["reported", prop["thermal_mass_reference_basis"]["text"]]
                  if prop["thermal_mass_reference_basis"]["status"] == "reported" else ["unknown", None])}
           if "thermal_mass_reference_basis" in prop else {}),
        **({"work_basis": (["reported", prop["work_reference_basis"]["text"]]
                           if prop["work_reference_basis"]["status"] == "reported" else ["unknown", None])}
           if "work_reference_basis" in prop else {}),
        **({"tga_coordinates": _tga_coordinate_key(prop)} if prop["quantity"] in TGA_QUANTITIES else {}),
        **({"crystallization_coordinates": {
            "phase": prop["thermal_scan_phase"]["code"],
            "occurrence": prop["thermal_phase_occurrence_ordinal"]["value"],
        }} if prop["quantity"] == "crystallization_peak_temperature" else {}),
    }, sort_keys=True, ensure_ascii=False)
    if prop["quantity"] == "thermal_degradation_rate_peak_temperature":
        # Curation of an unnumbered source cell cannot create a second fact
        # merely by later assigning an ordinal. Numbered peaks remain distinct.
        key = _coordinate_fact_base(signature, "tga_coordinates", "degradation_peak_ordinal")
        unknown_key = "tga_ordinal_unknown:" + key
        known_key = "tga_ordinal_known:" + key
        unknown = prop["degradation_peak_ordinal"]["value"] is None
        if unknown_key in seen or (unknown and known_key in seen):
            _fail(prop["id"], "duplicate source fact for the same material state")
        seen.add(unknown_key if unknown else known_key)
    if prop["quantity"] == "crystallization_peak_temperature":
        _crystallization_coordinate_guard(prop, signature, seen)
    if prop["quantity"] == "thermal_degradation_endset_temperature":
        # Definition enrichment is a revision, not extra source coverage.
        key = "tga_endset:" + _coordinate_fact_base(signature, "endset_definition")
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same TGA endset cell")
        seen.add(key)
    if prop["quantity"] == "oscillatory_complex_viscosity_magnitude":
        key = "complex_viscosity:" + _coordinate_fact_base(signature, "complex_viscosity_definition")
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same complex viscosity cell")
        seen.add(key)
    if prop["quantity"] == "dsc_reported_melting_specific_enthalpy":
        key = "dsc_enthalpy:" + _coordinate_fact_base(signature, "dsc_enthalpy_definition")
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same DSC enthalpy source cell")
        seen.add(key)
    if prop["quantity"] == "foam_cell_geometric_anisotropy_ratio":
        key = "cell_anisotropy:" + _coordinate_fact_base(signature, "cell_anisotropy_definition")
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same cell anisotropy source cell")
        seen.add(key)
    if prop["quantity"] == "foam_reaction_event_time":
        # Re-labelling an event or enriching its definition cannot duplicate a cell.
        key = "foam_event:" + _coordinate_fact_base(signature, "reaction_time_definition")
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same reaction-event cell")
        seen.add(key)
    if prop["quantity"] == "ftir_fitted_carbonyl_band_area_ratio":
        from ._ftir_band_area_ratio_contract import cell_key as ftir_cell_key
        key = "ftir_area_ratio:" + ftir_cell_key(prop)
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same FTIR source cell; revise instead")
        seen.add(key)
    if prop["quantity"] == "dsc_reference_normalized_crystallinity_percentage":
        from ._dsc_crystallinity_contract import cell_key
        key = "dsc_crystallinity:" + cell_key(_coordinate_fact_base(signature, "derivation"))
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same DSC normalization source cell")
        seen.add(key)
    if prop["quantity"] in {"dma_flexural_storage_modulus", "dma_flexural_loss_tangent"}:
        from ._dma_flexural_contract import cell_key
        key = "dma:" + cell_key(_coordinate_fact_base(signature, "dma_definition"))
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same flexural DMA source cell")
        seen.add(key)
    if prop["quantity"] == "solvent_extraction_gel_fraction_percentage":
        key = "gel_fraction:" + _coordinate_fact_base(signature, "gel_fraction_definition")
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same extraction gel fraction source cell")
        seen.add(key)
    if prop["quantity"] == "closed_cell_content_volume_percentage":
        key = "closed_cell:" + _coordinate_fact_base(signature, "closed_cell_definition")
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same closed cell source cell")
        seen.add(key)
    if prop["quantity"] == "water_absorption_volume_percentage":
        key = "water_absorption:" + _coordinate_fact_base(signature, "water_absorption_definition")
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same water absorption cell")
        seen.add(key)
    if prop["quantity"] == "tensile_extension_at_failure":
        # Channel/reference/criterion enrichment revises the same source cell.
        key = "tensile_extension:" + _coordinate_fact_base(signature, "extension_definition")
        if key in seen:
            _fail(prop["id"], "duplicate source fact for the same extension cell")
        seen.add(key)
    if signature in seen:
        _fail(prop["id"], "duplicate source fact for the same material state")
    seen.add(signature)

def validate_material_catalog(materials: dict, properties: dict, sources: dict) -> None:
    """Validate the entire source-backed graph before filtering or rendering.

    Existing scientific/source shape contracts remain with their original
    validators. New IDs are prefixed and disjoint from this source registry;
    the release validator additionally checks historical record/metadata IDs.
    No input is mutated, no source is fetched, and no value is converted.
    """
    _validate_material_catalog(materials, properties, sources)


def _validate_material_catalog(materials, properties, sources, *, property_is_valid=None):
    """Internal hook for a previously validated, content-bound local baseline.

    All structural, global uniqueness, evidence and source-class checks still run.
    Only property-local scientific checks may reuse an exact dependency match.
    """
    indices = _validate_structure(materials, properties)
    _validate_links(materials, properties, indices)
    source_index = _source_index(sources)
    new_ids = set().union(*(set(index) for index in indices))
    if new_ids.intersection(source_index):
        _fail("materials", "new record ID collides with source ID")
    for record in (*materials["identities"], *materials["grades"], *materials["records"], *properties["records"]):
        for evidence in _all_evidence(record):
            if evidence["source_id"] not in source_index:
                _fail(record["id"], "unknown evidence source " + evidence["source_id"])
            if evidence["url"] not in source_index[evidence["source_id"]]["urls"]:
                _fail(record["id"], "evidence URL absent from source registry")
            # A homepage with a generic locator cannot establish an inspected
            # numeric table cell. Source truth still needs independent readback.
            if evidence["locator"].strip().casefold() in {"website", "homepage", "home page", "source", "table", "page", "n/a", "unknown"}:
                _fail(record["id"], "evidence requires a specific locator")
    from ._material_derivation import canonical_identity_key, validate_taxon, validate_derivation
    keys = set()
    for identity in materials["identities"]:
        validate_taxon(identity)
        key = canonical_identity_key(identity)
        if key in keys:
            _fail(identity["id"], "duplicate canonical material identity")
        keys.add(key)
        _require_tag(identity["evidence"], "material_identity", identity["id"])
    for grade in materials["grades"]:
        _require_tag(grade["evidence"], "grade", grade["id"])
    for state in materials["records"]:
        _require_tag(state["evidence"], "state", state["id"])
        for fact in state["state"].values():
            if fact["status"] == "reported":
                _require_tag(fact["evidence"], "state", state["id"])
    duplicate_facts = set()
    for prop in properties["records"]:
        if prop["source_id"] not in source_index:
            _fail(prop["id"], "unknown primary source")
        state = indices[2][prop["material_state_id"]]
        identity = indices[0][state["identity_id"]]
        if property_is_valid is None or not property_is_valid(prop, state, identity):
            _validate_property(prop)
            validate_derivation(prop, identity, source_index)
        source_class = source_index[prop["source_id"]].get("role", "").casefold()
        if "manufacturer" in source_class and prop["evidence_kind"] != "manufacturer_reference":
            _fail(prop["id"], "manufacturer source cannot become published specimen evidence")
        if "technical association" in source_class.replace("_", " ").replace("-", " ") and prop["evidence_kind"] != "technical_association_reference":
            _fail(prop["id"], "technical-association source must retain its reference evidence class")
        from ._sec_molar_mass_contract import validate_state_context as validate_sec_state_context
        validate_sec_state_context(prop, state)
        from ._continuous_shear_contract import validate_state_context as validate_shear_state_context
        validate_shear_state_context(prop, state)
        from ._elemental_content_contract import validate_state_context as validate_elemental_state_context
        validate_elemental_state_context(prop, state)
        _unique_fact(prop, duplicate_facts, identity["id"])


def resolve_materials(state_ids, materials: dict, properties: dict, sources: dict) -> list[dict]:
    """Resolve a batch from one freshly validated graph, without global caches.

    Every call validates its actual inputs. Returned objects are detached copies;
    a mutation after this call cannot silently alter any previous inspection.
    """
    validate_material_catalog(materials, properties, sources)
    if not isinstance(state_ids, (list, tuple)) or any(not isinstance(key, str) for key in state_ids):
        _fail("state_ids", "expected a list of material state ID strings")
    states = {item["id"]: item for item in materials["records"]}
    identities = {item["id"]: item for item in materials["identities"]}
    grades = {item["id"]: item for item in materials["grades"]}
    props = {item["id"]: item for item in properties["records"]}
    source_order = {item["id"]: index for index, item in enumerate(sources["records"])}
    source_index = {item["id"]: item for item in sources["records"]}
    results = []
    for state_id in state_ids:
        if state_id not in states:
            _fail("state_id", "unknown material state " + state_id)
        state = states[state_id]
        identity, grade = identities[state["identity_id"]], grades.get(state["grade_id"])
        selected = [props[key] for key in state["property_ids"]]
        referenced = {entry["source_id"] for entry in _all_evidence([identity, grade, state, selected])}
        referenced.update(item["source_id"] for item in selected)
        results.append(deepcopy({"schema_version": "1.0.0", "identity": identity, "grade": grade,
                                "state": state, "properties": selected,
                                "sources": [source_index[key] for key in sorted(referenced, key=source_order.get)]}))
    return results


def resolve_material(state_id: str, materials: dict, properties: dict, sources: dict) -> dict:
    """Return one detached, source-complete view after validating actual inputs."""
    return resolve_materials([state_id], materials, properties, sources)[0]


def material_coverage(materials: dict, properties: dict) -> dict:
    """Derive counts from a structurally complete graph (no source-truth claim).

    Call validate_material_catalog with sources before reporting release coverage.
    No total or accepted material ID is hardcoded.
    """
    indices = _validate_structure(materials, properties)
    _validate_links(materials, properties, indices)
    duplicate_facts = set()
    for prop in properties["records"]:
        _validate_property(prop)
        from ._sec_molar_mass_contract import validate_state_context as validate_sec_state_context
        state = indices[2][prop["material_state_id"]]
        validate_sec_state_context(prop, state)
        from ._continuous_shear_contract import validate_state_context as validate_shear_state_context
        validate_shear_state_context(prop, state)
        from ._elemental_content_contract import validate_state_context as validate_elemental_state_context
        validate_elemental_state_context(prop, state)
        _unique_fact(prop, duplicate_facts, state["identity_id"])
    return {
        "material_identity_count": len(materials["identities"]),
        "grade_count": len(materials["grades"]),
        "material_state_count": len(materials["records"]),
        "property_record_count": len(properties["records"]),
        "quantity_count": len({item["quantity"] for item in properties["records"]}),
        "source_count": len({entry["source_id"] for entry in _all_evidence([materials, properties])}
                            | {item["source_id"] for item in properties["records"]}),
        "by_category": dict(sorted(Counter(item["category"] for item in materials["identities"]).items())),
        "by_evidence_kind": dict(sorted(Counter(item["evidence_kind"] for item in properties["records"]).items())),
    }


def material_quota_coverage(materials: dict, properties: dict, sources: dict, target: int = 1000) -> dict:
    """Count admitted unique identities with traceable facts, never staged rows."""
    if type(target) is not int or target < 1:
        raise ValueError("target must be a positive integer")
    validate_material_catalog(materials, properties, sources)
    from ._material_derivation import canonical_identity_key
    groups = {category: set() for category in CATEGORIES}
    for identity in materials["identities"]:
        groups[identity["category"]].add(canonical_identity_key(identity))
    return {"taxonomy_policy_version": "natural-biogenic-v1", "status": "admitted",
            "target_per_class": target, "distinct_material_count": sum(map(len, groups.values())),
            "classes": {category: {"admitted_unique_identity_count": len(keys),
                                    "remaining": max(0, target - len(keys)),
                                    "target_met": len(keys) >= target}
                        for category, keys in groups.items()}}


def merge_material_catalogs(materials: dict, properties: dict, sources: dict, append: dict) -> dict:
    """Deterministically merge already admitted append tables, never grant admission.

    This in-memory release-building step does not write files or bless research.
    Callers obtain ``append`` only from their separately approved adapter. Exact
    existing records are idempotent; every conflicting existing ID fails closed.
    Existing order and objects are retained, while new records sort by stable ID.
    Both input graphs and the resulting graph are freshly validated.
    """
    if not isinstance(append, dict) or set(append) != {'materials', 'properties', 'sources'}:
        raise ValueError('append tables require materials, properties and sources')
    validate_material_catalog(materials, properties, sources)
    validate_material_catalog(append['materials'], append['properties'], append['sources'])
    result = {'materials': deepcopy(materials), 'properties': deepcopy(properties), 'sources': deepcopy(sources)}
    for name, fields in (('materials', ('identities', 'grades', 'records')),
                         ('properties', ('records',)), ('sources', ('records',))):
        for field in fields:
            existing = {row['id']: row for row in result[name][field]}
            new = {}
            for row in append[name][field]:
                identifier = row['id']
                if identifier in existing:
                    if existing[identifier] != row:
                        raise ValueError('conflicting existing catalog record: ' + identifier)
                else:
                    new[identifier] = row
            result[name][field].extend(deepcopy(new[key]) for key in sorted(new))
    validate_material_catalog(result['materials'], result['properties'], result['sources'])
    return result
