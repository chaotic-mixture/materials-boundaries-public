"""Presentation-only, source-preserving views for the reference-material lane."""
from copy import deepcopy
from ._extension_contract import LABEL_KEYS as EXTENSION_LABELS
from ._water_absorption_contract import LABEL_KEYS as WATER_LABELS, FACT_FIELDS as WATER_FACTS
from ._dma_flexural_contract import LABEL_KEYS as DMA_LABELS, FACT_FIELDS as DMA_FACTS
from ._gel_fraction_contract import LABEL_KEYS as GEL_FRACTION_LABELS, FACT_FIELDS as GEL_FRACTION_FACTS
from ._closed_cell_contract import LABEL_KEYS as CLOSED_CELL_LABELS, FACT_FIELDS as CLOSED_CELL_FACTS
from ._complex_viscosity_contract import LABEL_KEYS as COMPLEX_VISCOSITY_LABELS, FACT_FIELDS as COMPLEX_VISCOSITY_FACTS
from ._dsc_enthalpy_contract import LABEL_KEYS as DSC_ENTHALPY_LABELS, FACT_FIELDS as DSC_ENTHALPY_FACTS
from ._cell_anisotropy_contract import LABEL_KEYS as CELL_ANISOTROPY_LABELS, FACT_FIELDS as CELL_ANISOTROPY_FACTS
from ._foam_event_contract import LABEL_KEYS as FOAM_EVENT_LABELS, FACT_FIELDS as FOAM_EVENT_FACTS
import json
import math


LANGUAGES = ("en", "zh", "ja", "de")
WORK_LABELS = ("code_volumetric_tensile_work_to_break", "work_reference_basis", "work_reference_notice")
TGA_QUANTITIES = (
    "thermal_degradation_onset_temperature", "temperature_at_specified_mass_loss",
    "thermal_degradation_rate_peak_temperature", "tga_residue_percentage",
)
REQUIRED_LABELS = frozenset(('materials', 'reference_properties', 'count', 'empty', 'unknown', 'identity', 'grade', 'category', 'state', 'original_name', 'source_designation', 'source_scope', 'identity_scope', 'authority', 'manufacturer', 'product_form', 'processing', 'temper_or_heat_treatment', 'conditioning', 'composition_or_purity', 'reinforcement', 'porosity', 'orientation', 'property_label', 'quantity', 'evidence_kind', 'reporting_basis', 'determination_basis', 'basis_note', 'reported_value', 'conditions', 'temperature', 'test_standard', 'test_method', 'direction', 'loading_rate', 'density_basis', 'summary_statistic', 'uncertainty', 'uncertainty_status', 'uncertainty_note', 'standard_deviation', 'confidence_interval', 'plus_minus_unspecified', 'confidence_level', 'estimand', 'construction', 'reported_uncertainty_notice', 'sample_count', 'scope', 'method_definition', 'source_document', 'source_discrepancies', 'verification', 'scope_note', 'evaluation_support', 'source', 'source_title', 'source_locator', 'source_url', 'source_read_status', 'source_rights', 'evidence', 'caveat', 'reference_notice', 'statistics_notice', 'unknown_notice', 'range_notice', 'comparison_notice', 'translation_notice', 'cli_catalog_extra', 'cli_material_id', 'cli_identity_id', 'cli_grade_id', 'cli_category', 'cli_evidence_kind', 'cli_reporting_basis', 'cli_source_id', 'cli_quantity', 'cli_filter_notice', 'code_catalog_only', 'code_reported', 'code_not_reported_in_inspected_source', 'code_not_verified', 'code_not_applicable', 'code_manufacturer_reference', 'code_technical_association_reference', 'code_published_experimental_reference', 'code_published_computational_reference', 'code_typical', 'code_nominal', 'code_guideline', 'code_specification_limit', 'code_reported_summary', 'code_not_stated', 'code_source_reports_measurement', 'code_source_reports_calculation', 'code_mixed_or_unclear', 'code_reported_mean', 'code_reported_value', 'code_mass_density', 'code_youngs_modulus', 'code_tensile_modulus', 'code_flexural_modulus', 'code_elastic_modulus_unspecified', 'code_tensile_strength', 'code_metal', 'code_polymer', 'code_inorganic', 'code_composite', 'code_apparent', 'code_bulk', 'code_true', 'code_published_handbook_reference', 'code_published_measurement_derived_reference', 'code_source_reports_compiled_measurements', 'code_crystallographic', 'code_source_reported_compilation', 'code_source_reported_crystallographic_derivation'))
REQUIRED_LABELS |= frozenset(("code_thermal_degradation_endset_temperature", "degradation_endset_definition"))
REQUIRED_LABELS |= frozenset(EXTENSION_LABELS)
REQUIRED_LABELS |= frozenset(WATER_LABELS)
REQUIRED_LABELS |= frozenset(CLOSED_CELL_LABELS)
REQUIRED_LABELS |= frozenset(GEL_FRACTION_LABELS)
REQUIRED_LABELS |= frozenset(DMA_LABELS)
REQUIRED_LABELS |= frozenset(FOAM_EVENT_LABELS)
REQUIRED_LABELS |= frozenset(CELL_ANISOTROPY_LABELS)
REQUIRED_LABELS |= frozenset(DSC_ENTHALPY_LABELS)
REQUIRED_LABELS |= frozenset(COMPLEX_VISCOSITY_LABELS)
REQUIRED_LABELS |= frozenset(('code_source_reported_computational_structure_density',))
REQUIRED_LABELS |= frozenset(('code_source_reported_molecular_simulation_density', 'code_simulation_cell'))
REQUIRED_LABELS |= frozenset(('code_slump_flow_spread',))
REQUIRED_LABELS |= frozenset(('code_tensile_yield_strength', 'code_flexural_strength', 'code_tensile_stress_at_break'))
REQUIRED_LABELS |= frozenset(('code_tensile_stress_at_specified_elongation', 'specified_elongation'))
REQUIRED_LABELS |= frozenset(('code_tensile_elongation_at_break',))
REQUIRED_LABELS |= frozenset(('code_tensile_elongation_at_strength',))
REQUIRED_LABELS |= frozenset(('code_flexural_elongation_at_break',))
REQUIRED_LABELS |= frozenset(('code_shore_a_hardness', 'code_compressive_modulus', 'code_compressive_strength',))
REQUIRED_LABELS |= frozenset(('code_tear_strength',))
REQUIRED_LABELS |= frozenset(('code_izod_impact_strength',))
REQUIRED_LABELS |= frozenset(('code_glass_transition_temperature',))
REQUIRED_LABELS |= frozenset(('code_melting_peak_temperature',))
REQUIRED_LABELS |= frozenset(('code_crystallization_peak_temperature', 'thermal_scan_definition',
                             'code_nonisothermal_temperature_scan', 'thermal_scan_phase',
                             'code_heating', 'code_cooling', 'thermal_phase_occurrence_ordinal'))
REQUIRED_LABELS |= frozenset(('code_dielectric_breakdown_strength',))
REQUIRED_LABELS |= frozenset(('code_thermal_conductivity',))
REQUIRED_LABELS |= frozenset('code_' + quantity for quantity in TGA_QUANTITIES)
REQUIRED_LABELS |= frozenset(WORK_LABELS)
REQUIRED_LABELS |= frozenset(("code_mass_specific_heat_capacity", "code_thermal_diffusivity", "thermal_mass_reference_basis"))
REQUIRED_LABELS |= frozenset(("specified_mass_loss", "degradation_peak_ordinal",
                             "residue_endpoint_temperature", "mass_reference_basis", "tga_reference_notice"))
REQUIRED_LABELS |= frozenset(('coverage', 'coverage_notice', 'coverage_target', 'coverage_admitted', 'coverage_remaining'))
REQUIRED_LABELS |= frozenset(('code_natural', 'code_basic_wood_density', 'code_source_reported_empirical_conversion', 'code_oven_dry_mass_over_fresh_or_water_saturated_volume', 'derivation', 'canonical_taxon', 'derived_notice'))
REQUIRED_LABELS |= frozenset((
    'coefficient_of_variation', 'standard_error_of_mean', 'estimated_inaccuracy',
    'measure_availability', 'measure_basis', 'measure_qualifier', 'measure_note',
    'code_reported_measures', 'code_numeric_reported', 'code_graphical_only',
    'code_absolute', 'code_relative_to_reported_value', 'code_approximately',
    'code_not_qualified_in_source', 'graphical_amplitude_unavailable',
    'central_aggregation_unknown_notice', 'reported_measures_notice',
))


def validate_material_locales(locales: dict) -> None:
    """Reject incomplete labels rather than silently hiding a scientific caveat."""
    if (not isinstance(locales, dict) or set(locales) != {
            "schema_version", "default_language", "translation_review", "languages"}
            or locales["schema_version"] != "1.0.0"
            or locales["default_language"] != "en"
            or locales["translation_review"] != "machine_assisted_not_scientifically_reviewed"):
        raise ValueError("material locales: invalid metadata")
    languages = locales["languages"]
    if not isinstance(languages, dict) or set(languages) != set(LANGUAGES):
        raise ValueError("material locales: exactly en, zh, ja and de are required")
    for language, labels in languages.items():
        if not isinstance(labels, dict) or set(labels) != REQUIRED_LABELS:
            raise ValueError(f"material locales: incomplete or unknown labels for {language}")
        if any(not isinstance(value, str) or not value.strip() or "[missing:" in value
               or any(_unsafe_display_codepoint(char) for char in value)
               for value in labels.values()):
            raise ValueError(f"material locales: invalid label for {language}")


REQUIRED_LABELS |= frozenset(('code_source_reported_thermal_transport_product','source_product_derivation','source_product_notice'))


REQUIRED_LABELS |= frozenset(('code_thermal_response_characteristic_time','thermal_response_phase','code_post_stretching_hold','code_post_retraction_recovery','thermal_convection','code_natural_convection','code_forced_convection','code_source_reported_thermal_response_fit','thermal_response_fit_notice','thermal_response_derivation'))


def material_labels(language: str = "en") -> dict:
    from .catalog import _read_reference_resource
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    locales = _read_reference_resource("material_locales")
    validate_material_locales(locales)
    return locales["languages"][language]


def _same_json_value(left, right, depth=0):
    """Conservatively recognize unchanged plain JSON without coercing types."""
    if depth > 64 or type(left) is not type(right):
        return False
    if type(left) is dict:
        if (any(type(key) is not str for key in left)
                or any(type(key) is not str for key in right)
                or tuple(left) != tuple(right)):
            return False
        return all(_same_json_value(left[key], right[key], depth + 1) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(
            _same_json_value(a, b, depth + 1) for a, b in zip(left, right))
    if type(left) is float:
        return math.isfinite(left) and math.isfinite(right) and left.hex() == right.hex()
    if type(left) in (str, int, bool, type(None)):
        return left == right
    return False


def _resolved_graph(catalog: dict, kind: str) -> tuple[dict, dict, dict]:
    """Resolve a canonical subset against the complete validated offline graph.

    Incoming records replace records of the same ID. Changed or uncertain
    inputs require full graph validation again. An exact unchanged subset
    reuses only the complete graph freshly read and validated in this call.
    Catalogues remain raw envelopes; resolved objects never become records.
    """
    from .catalog import read_catalog
    from .material_references import validate_material_catalog
    materials = read_catalog("materials")
    properties = read_catalog("reference_properties")
    sources = read_catalog("sources")
    validate_material_catalog(materials, properties, sources)
    keys = {"schema_version", "records"}
    if kind == "materials":
        keys |= {"identities", "grades"}
    if not isinstance(catalog, dict) or set(catalog) != keys or catalog["schema_version"] != "1.0.0":
        raise ValueError("material presentation: invalid canonical catalogue envelope")
    original = materials if kind == "materials" else properties
    for key in keys - {"schema_version"}:
        incoming = catalog[key]
        if not isinstance(incoming, list):
            raise ValueError(f"material presentation: {key} must be a list")
        if any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in incoming):
            raise ValueError(f"material presentation: invalid {key} record")
        identifiers = [item["id"] for item in incoming]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(f"material presentation: duplicate {key} ID")

    unchanged = (type(catalog) is dict and type(catalog["schema_version"]) is str
                 and all(type(key) is str for key in catalog))
    for key in keys - {"schema_version"}:
        incoming = catalog[key]
        if type(incoming) is not list:
            unchanged = False
            continue
        index = {item["id"]: (position, item) for position, item in enumerate(original[key])}
        previous_position = -1
        for item in incoming:
            if (type(item) is not dict or type(item["id"]) is not str
                    or item["id"] not in index):
                unchanged = False
                break
            position, original_item = index[item["id"]]
            if position <= previous_position or not _same_json_value(item, original_item):
                unchanged = False
                break
            previous_position = position
    if unchanged:
        return materials, properties, sources

    target = deepcopy(original)
    for key in keys - {"schema_version"}:
        incoming = catalog[key]
        replacements = {item["id"]: item for item in incoming}
        existing = {item["id"] for item in target[key]}
        target[key] = [deepcopy(replacements[item["id"]]) if item["id"] in replacements else item
                       for item in target[key]]
        target[key].extend(deepcopy(item) for item in incoming if item["id"] not in existing)
    if kind == "materials":
        materials = target
    else:
        properties = target
    validate_material_catalog(materials, properties, sources)
    return materials, properties, sources


def render_material_catalog(catalog: dict, kind: str, language: str = "en") -> str:
    """Show exact source strings, explicit unknowns and mandatory caveats."""
    if kind not in {"materials", "reference-properties"}:
        raise ValueError(f"unknown material presentation: {kind}")
    materials, properties, sources = _resolved_graph(catalog, kind)
    labels = material_labels(language)
    source_index = {source["id"]: source for source in sources["records"]}
    state_index = {state["id"]: state for state in materials["records"]}
    identity_index = {identity["id"]: identity for identity in materials["identities"]}
    grade_index = {grade["id"]: grade for grade in materials["grades"]}
    property_index = {prop["id"]: prop for prop in properties["records"]}
    lines = [labels[kind.replace("-", "_")], f'{labels["count"]}: {len(catalog["records"])}',
             labels["caveat"], labels["reference_notice"], labels["unknown_notice"],
             labels["translation_notice"]]
    if not catalog["records"]:
        lines.append(labels["empty"])

    def code(value):
        if value is None:
            return labels["unknown"]
        uncertainty_labels = {"reported_standard_deviation": "standard_deviation",
                              "reported_confidence_interval": "confidence_interval",
                              "reported_plus_minus_unspecified": "plus_minus_unspecified"}
        label = labels[uncertainty_labels[value]] if value in uncertainty_labels else labels.get("code_" + value)
        return f"{label} [{value}]" if label else value

    def raw(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)

    def field(key, value, indent="  "):
        return f'{indent}{labels.get(key, key)}: {labels["unknown"] if value is None else value}'

    def evidence(items, indent="    "):
        output = []
        for item in items:
            source = source_index[item["source_id"]]
            output.extend([field("source", source["id"], indent),
                           field("source_title", source["title"], indent),
                           field("source_url", item["url"], indent),
                           field("source_locator", item["locator"], indent)])
        return output

    def fact(key, item, indent="    "):
        text = item["text"] if item["text"] is not None else labels["unknown"]
        output = [field(key, f'{text} ({code(item["status"])})', indent)]
        if item["notes"] is not None:
            output.append(field("scope_note", item["notes"], indent + "  "))
        output.extend(evidence(item["evidence"], indent + "  "))
        return output

    def property_view(prop, indent="  "):
        source = source_index[prop["source_id"]]
        result = prop["reported_value"]
        output = [f'{indent}{prop["id"]}',
                  field("property_label", prop["source_property_label"], indent + "  "),
                  field("quantity", code(prop["quantity"]), indent + "  "),
                  field("reported_value", f'{result["value_text"]} {result["unit_text"]}', indent + "  ")]
        for key in ("evidence_kind", "reporting_basis", "determination_basis", "summary_statistic",
                    "evaluation_support"):
            output.append(field(key, code(prop[key]), indent + "  "))
        output.append(field("basis_note", prop["basis_note"], indent + "  "))
        if prop["density_basis"] is not None:
            output.append(field("density_basis", code(prop["density_basis"]), indent + "  "))
        output.append(field("conditions", "", indent + "  "))
        if "reaction_time_definition" in prop:
            event = prop["reaction_event"]
            output.append(field("reaction_event", code(event["code"]), indent + "    "))
            output.append(field("scope_note", event["notes"], indent + "      "))
            output.extend(evidence(event["evidence"], indent + "      "))
            definition = prop["reaction_time_definition"]
            output.append(field("reaction_time_definition", "", indent + "    "))
            output.append(field("scope_note", definition["notes"], indent + "      "))
            output.extend(evidence(definition["evidence"], indent + "      "))
            for name in FOAM_EVENT_FACTS:
                output.extend(fact("reaction_time_" + name, definition[name], indent + "      "))
            output.append(indent + "    " + labels["reaction_time_reference_notice"])
        if "dma_definition" in prop:
            for coordinate_name in ("dma_measurement_temperature", "dma_oscillation_frequency"):
                coordinate = prop[coordinate_name]
                displayed = coordinate["value_text"] + " " + coordinate["unit_text"] if coordinate["status"] == "reported" else code(coordinate["status"])
                output.append(field(coordinate_name, displayed, indent + "    "))
                output.append(field("scope_note", coordinate["notes"], indent + "      "))
                output.extend(evidence(coordinate["evidence"], indent + "      "))
            definition = prop["dma_definition"]
            output.append(field("dma_definition", "", indent + "    "))
            output.append(field("scope_note", definition["notes"], indent + "      "))
            output.extend(evidence(definition["evidence"], indent + "      "))
            for name in DMA_FACTS:
                output.extend(fact("dma_" + name, definition[name], indent + "      "))
            output.append(indent + "    " + labels["dma_reference_notice"])
        if "complex_viscosity_definition" in prop:
            coordinate = prop["oscillation_frequency"]
            displayed_frequency = coordinate["value_text"] + " " + coordinate["unit_text"] if coordinate["status"] == "reported" else code(coordinate["status"])
            output.append(field("oscillation_frequency", displayed_frequency, indent + "    "))
            output.append(field("scope_note", coordinate["notes"], indent + "      "))
            output.extend(evidence(coordinate["evidence"], indent + "      "))
            definition = prop["complex_viscosity_definition"]
            output.append(field("complex_viscosity_definition", "", indent + "    "))
            output.append(field("scope_note", definition["notes"], indent + "      "))
            output.extend(evidence(definition["evidence"], indent + "      "))
            for name in COMPLEX_VISCOSITY_FACTS:
                output.extend(fact("complex_viscosity_" + name, definition[name], indent + "      "))
            output.append(indent + "    " + labels["complex_viscosity_reference_notice"])
        if "dsc_enthalpy_definition" in prop:
            definition = prop["dsc_enthalpy_definition"]
            output.append(field("dsc_enthalpy_definition", "", indent + "    "))
            output.append(field("scope_note", definition["notes"], indent + "      "))
            output.extend(evidence(definition["evidence"], indent + "      "))
            for name in DSC_ENTHALPY_FACTS:
                output.extend(fact("dsc_enthalpy_" + name, definition[name], indent + "      "))
            output.append(indent + "    " + labels["dsc_enthalpy_reference_notice"])
        if "cell_anisotropy_definition" in prop:
            definition = prop["cell_anisotropy_definition"]
            output.append(field("cell_anisotropy_definition", "", indent + "    "))
            output.append(field("scope_note", definition["notes"], indent + "      "))
            output.extend(evidence(definition["evidence"], indent + "      "))
            for name in CELL_ANISOTROPY_FACTS:
                output.extend(fact("cell_anisotropy_" + name, definition[name], indent + "      "))
            output.append(indent + "    " + labels["cell_anisotropy_reference_notice"])
        if "gel_fraction_definition" in prop:
            definition = prop["gel_fraction_definition"]
            output.append(field("gel_fraction_definition", "", indent + "    "))
            output.append(field("scope_note", definition["notes"], indent + "      "))
            output.extend(evidence(definition["evidence"], indent + "      "))
            for name in GEL_FRACTION_FACTS:
                output.extend(fact("gel_fraction_" + name, definition[name], indent + "      "))
            output.append(indent + "    " + labels["gel_fraction_reference_notice"])
        if "closed_cell_definition" in prop:
            definition = prop["closed_cell_definition"]
            output.append(field("closed_cell_definition", "", indent + "    "))
            output.append(field("scope_note", definition["notes"], indent + "      "))
            output.extend(evidence(definition["evidence"], indent + "      "))
            for name in CLOSED_CELL_FACTS:
                output.extend(fact("closed_cell_" + name, definition[name], indent + "      "))
            output.append(indent + "    " + labels["closed_cell_reference_notice"])
        if "water_absorption_definition" in prop:
            definition = prop["water_absorption_definition"]
            output.append(field("water_absorption_definition", "", indent + "    "))
            output.append(field("scope_note", definition["notes"], indent + "      "))
            output.extend(evidence(definition["evidence"], indent + "      "))
            for name in WATER_FACTS:
                output.extend(fact("water_absorption_" + name, definition[name], indent + "      "))
            output.append(indent + "    " + labels["water_absorption_reference_notice"])
        if "extension_definition" in prop:
            definition = prop["extension_definition"]
            output.append(field("extension_definition", "", indent + "    "))
            output.append(field("extension_correction_basis", code(definition["correction_basis"]), indent + "      "))
            output.append(field("scope_note", definition["notes"], indent + "      "))
            output.extend(evidence(definition["evidence"], indent + "      "))
            for name in ("measurement_channel", "reference_length", "failure_criterion"):
                output.extend(fact("extension_" + name, definition[name], indent + "      "))
            output.append(indent + "    " + labels["extension_reference_notice"])
        for key in ("specified_mass_loss", "residue_endpoint_temperature"):
            if key in prop:
                target = prop[key]
                output.append(field(key, f'{target["value_text"]} {target["unit_text"]}', indent + "    "))
                output.append(field("scope_note", target["notes"], indent + "      "))
                output.extend(evidence(target["evidence"], indent + "      "))
        if "degradation_peak_ordinal" in prop:
            target = prop["degradation_peak_ordinal"]
            ordinal = str(target["value"]) if target["value"] is not None else code(target["status"])
            output.append(field("degradation_peak_ordinal", ordinal, indent + "    "))
            output.append(field("scope_note", target["notes"], indent + "      "))
            output.extend(evidence(target["evidence"], indent + "      "))
        if "thermal_scan_definition" in prop:
            program = prop["thermal_scan_definition"]
            output.append(field("thermal_scan_definition", code(program["kind"]), indent + "    "))
            output.append(field("scope_note", program["notes"], indent + "      "))
            output.extend(evidence(program["evidence"], indent + "      "))
            for key, value_key in (("thermal_scan_phase", "code"), ("thermal_phase_occurrence_ordinal", "value")):
                if key not in prop:
                    continue
                descriptor = prop[key]
                value = (code(descriptor[value_key]) if value_key == "code" else str(descriptor[value_key])) if descriptor["status"] == "reported" else code(descriptor["status"])
                output.append(field(key, value, indent + "    "))
                output.append(field("scope_note", descriptor["notes"], indent + "      "))
                output.extend(evidence(descriptor["evidence"], indent + "      "))
        if "thermal_response_phase" in prop:
            phase=prop["thermal_response_phase"];boundary=prop["thermal_convection"]
            output.append(field("thermal_response_phase",code(phase["code"]),indent+"    "))
            output.append(field("scope",phase["notes"],indent+"    "))
            output.extend(evidence(phase["evidence"],indent+"      "))
            output.append(field("thermal_convection",code(boundary["regime"] if boundary["status"]=="reported" else boundary["status"]),indent+"    "))
            output.append(field("scope",boundary["notes"],indent+"    "))
            output.extend(evidence(boundary["evidence"],indent+"      "))
        if "thermal_mass_reference_basis" in prop:
            output.extend(fact("thermal_mass_reference_basis", prop["thermal_mass_reference_basis"], indent + "    "))
        if "work_reference_basis" in prop:
            output.extend(fact("work_reference_basis", prop["work_reference_basis"], indent + "    "))
            output.append(indent + "    " + labels["work_reference_notice"])
        if "mass_reference_basis" in prop:
            output.extend(fact("mass_reference_basis", prop["mass_reference_basis"], indent + "    "))
        if "degradation_endset_definition" in prop:
            output.extend(fact("degradation_endset_definition", prop["degradation_endset_definition"], indent + "    "))
        if prop["quantity"] in TGA_QUANTITIES or prop["quantity"] == "thermal_degradation_endset_temperature":
            output.append(indent + "    " + labels["tga_reference_notice"])
        if "specified_elongation" in prop:
            target = prop["specified_elongation"]
            output.append(field("specified_elongation", f'{target["value_text"]} {target["unit_text"]}', indent + "    "))
            output.append(field("scope_note", target["notes"], indent + "      "))
            output.extend(evidence(target["evidence"], indent + "      "))
        for key, condition in prop["conditions"].items():
            if key == "additional_conditions":
                for extra in condition:
                    output.extend(fact(extra["name"], extra["fact"], indent + "    "))
            else:
                output.extend(fact(key, condition, indent + "    "))
        uncertainty = prop["uncertainty"]
        if uncertainty is not None and uncertainty["type"] == "reported_measures":
            for measure in uncertainty["measures"]:
                value = measure["reported_value"]
                display = (labels["graphical_amplitude_unavailable"] if value is None else
                           f'{value["value_text"]} {value["unit_text"]}')
                output.append(field(measure["kind"], display, indent + "  "))
                for key in ("availability", "basis", "qualifier"):
                    output.append(field("measure_" + key, code(measure[key]), indent + "    "))
                output.append(field("scope", measure["scope"], indent + "    "))
                if measure["note"] is not None:
                    output.append(field("measure_note", measure["note"], indent + "    "))
                if measure["kind"] == "standard_deviation" and prop["summary_statistic"] != "reported_mean":
                    output.append(indent + "    " + labels["central_aggregation_unknown_notice"])
                output.extend(evidence(measure["evidence"], indent + "    "))
        elif uncertainty is not None:
            label = {"reported_standard_deviation": "standard_deviation",
                     "reported_confidence_interval": "confidence_interval",
                     "reported_plus_minus_unspecified": "plus_minus_unspecified"}[uncertainty["type"]]
            output.append(field(label,
                                f'{uncertainty["value_text"]} {uncertainty["unit_text"]}', indent + "  "))
            if uncertainty["type"] == "reported_confidence_interval":
                output.append(field("confidence_level", uncertainty["confidence_level"]["value_text"], indent + "  "))
                for key in ("estimand", "construction"):
                    output.extend(fact(key, uncertainty[key], indent + "  "))
            output.append(field("scope", uncertainty["scope"], indent + "  "))
            output.extend(evidence(uncertainty["evidence"], indent + "    "))
        else:
            output.append(field("uncertainty", None, indent + "  "))
        output.extend([field("uncertainty_status", code(prop["uncertainty_status"]), indent + "  "),
                       field("uncertainty_note", prop["uncertainty_note"], indent + "  "),
                       field("sample_count", raw(prop["sample_count"]), indent + "  ")])
        if uncertainty is not None and uncertainty["type"] == "reported_measures":
            output.append(indent + "  " + labels["reported_measures_notice"])
        elif uncertainty is not None and uncertainty["type"] != "reported_standard_deviation":
            output.append(indent + "  " + labels["reported_uncertainty_notice"])
        elif uncertainty is not None or prop["summary_statistic"] == "reported_mean":
            output.append(indent + "  " + labels["statistics_notice"])
        if result["kind"] == "interval":
            output.append(indent + "  " + labels["range_notice"])
        elif result["kind"] == "comparison":
            output.append(indent + "  " + labels["comparison_notice"])
        for key in ("method_definition", "source_document", "source_discrepancies", "verification"):
            value = raw(prop[key])
            if key == "method_definition" and prop[key]["type"] != "source_reported_conventional":
                value = code(prop[key]["type"]) + ": " + value
            output.append(field(key, value, indent + "  "))
        if "derivation" in prop:
            product = prop["method_definition"]["type"] == "source_reported_thermal_transport_product"
            fit = prop["method_definition"]["type"] == "source_reported_thermal_response_fit"
            output.append(indent + "  " + labels["thermal_response_fit_notice" if fit else "source_product_notice" if product else "derived_notice"])
            output.append(field("thermal_response_derivation" if fit else "source_product_derivation" if product else "derivation", raw(prop["derivation"]), indent + "  "))
        output.append(field("scope_note", prop["scope_note"], indent + "  "))
        output.extend(evidence(prop["evidence"], indent + "  "))
        output.extend([field("source_read_status", source["read_status"], indent + "  "),
                       field("source_rights", raw(source["license"]), indent + "  ")])
        return output

    for record in catalog["records"]:
        state = record if kind == "materials" else state_index[record["material_state_id"]]
        identity = identity_index[state["identity_id"]]
        grade = grade_index.get(state["grade_id"])
        lines.extend(["", f'{record["id"]}: {state["names"][language]}',
                      field("identity", f'{identity["names"][language]} [{identity["id"]}]'),
                      field("category", code(identity["category"])),
                      field("grade", None if grade is None else f'{grade["designation"]} [{grade["id"]}]'),
                      field("state", state["id"]), field("original_name", state["name"]),
                      field("source_designation", state["source_designation"]),
                      field("identity_scope", identity["identity_scope"]),
                      field("source_scope", state["source_scope"]),
                      field("evaluation_support", code(state["evaluation_support"]))])
        if "canonical_taxon" in identity:
            lines.append(field("canonical_taxon", raw(identity["canonical_taxon"])))
        if grade is not None:
            lines.extend([field("authority", raw(grade["authority"])),
                          field("manufacturer", raw(grade["manufacturer"]))])
        for key, item in state["state"].items():
            lines.extend(fact(key, item))
        lines.extend(evidence(identity["evidence"]))
        if grade is not None:
            lines.extend(evidence(grade["evidence"]))
        lines.extend(evidence(state["evidence"]))
        selected = ([property_index[identifier] for identifier in state["property_ids"]]
                    if kind == "materials" else [record])
        for prop in selected:
            lines.extend(property_view(prop))
    # Legacy source metadata does not forbid terminal/bidi controls or lone
    # surrogates. Escape unsafe characters inside each assembled line; only the
    # separators added here remain actual newlines. Valid multilingual text,
    # source JSON and source numeric precision are never rewritten.
    return "\n".join(_escape_terminal_controls(line) for line in lines)


def _unsafe_display_codepoint(char: str) -> bool:
    value = ord(char)
    return (value < 32 or 127 <= value <= 159
            or 0x202A <= value <= 0x202E or 0x2066 <= value <= 0x2069
            or 0xD800 <= value <= 0xDFFF)


def _escape_terminal_controls(text: str) -> str:
    return "".join(f"\\u{ord(char):04x}" if _unsafe_display_codepoint(char)
                   else char for char in text)
