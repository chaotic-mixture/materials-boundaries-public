"""Dependency-free closure for six source-defined PA12 CF15 tensile cells.

This contract checks transcription and metadata integrity. It does not calculate
UTS, fit a temperature law, infer missing experimental details or certify a test.
The hashes below identify curated JSON payloads, never publisher article bytes.
Record IDs and display names may change; source cells cannot become new tests.
"""
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
import math

PA12_FAMILY = "ciganas_2026_pa12_cf15_fff_tensile_temperature_v1"
PA12_SOURCE = "ciganas2026polym18050563"
PA12_DATASET = "ciganas-2026-pa12-cf15-fff-uts-temperature"
PA12_PROTOCOL = "ciganas2026-pa12-cf15-quasistatic-tension"
PA12_QUANTITY = "ultimate_tensile_strength_as_reported_3d"
PA12_DOI = "10.3390/polym18050563"
PA12_MAIN = "https://www.mdpi.com/2073-4360/18/5/563"
PA12_ARTIFACT = "publisher_html_updated_2026_09_03_inspected_2026_10_03"
PA12_SOURCE_TITLE = "Thermo-Mechanical and Fatigue Behavior of 3D-Printed PA12 CF15 for Engineering Application"
PA12_TEMPERATURES = ("23", "40", "60", "80", "100", "120")
# temperature: (source central string, source SD string, exact Pa, exact Pa SD)
PA12_CELLS = {
    "23": ("49.07", "0.88", 49070000, 880000),
    "40": ("40.31", "0.72", 40310000, 720000),
    "60": ("32.70", "1.18", 32700000, 1180000),
    "80": ("26.60", "1.15", 26600000, 1150000),
    "100": ("22.78", "0.97", 22780000, 970000),
    "120": ("18.68", "0.91", 18680000, 910000),
}

PA12_SCIENTIFIC_PAYLOAD_SHA256 = {'23': 'cf9c6ce10cf848135d6b99021a3567525307bdaf209c2f7b556244c99099ef4d', '40': '4d2ea83bd9dec34d3572c526fd6801f6c7728b3f0cacaed50b3e2d82c02230ab', '60': '8e8272b7d5977065900de8e10b42cd08ebdf499b760b6b2cec03f5dce385b478', '80': '3c096bef738843f5a56a7eccb019c7fd430e997d548b6c693d3957f9ad9e813d', '100': 'd41ae134cdda84540377d3e160777b3a7391e98cc6b0c4e040f53946a18e40e1', '120': 'e8e035492d623b78a2c8d93dca003f03c3d9bccd19f4cbd988770e9293bb35f0'}
PA12_SOURCE_PAYLOAD_SHA256 = 'b94f112a4befb0e79094da49a6b45fabf2737328dd0add25d8eaa6a840fcc764'


def _require(ok, message):
    if not ok:
        raise ValueError("PA12 CF15 observation contract: " + message)


def _canonical(value):
    """Normalize JSON-equivalent integral floats without conflating Booleans."""
    if isinstance(value, dict):
        _require(all(isinstance(key, str) for key in value), "non-JSON metadata key")
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if type(value) is float:
        _require(math.isfinite(value), "nonfinite metadata number")
        return int(value) if value.is_integer() else value
    _require(type(value) in (str, int, bool, type(None)), "non-JSON metadata value")
    return value


def _digest(value):
    try:
        data = json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError("PA12 CF15 observation contract: invalid scientific payload") from exc
    return hashlib.sha256(data).hexdigest()


def _has_marker(value, markers):
    if isinstance(value, dict):
        return any(_has_marker(item, markers) for item in value.values())
    if isinstance(value, list):
        return any(_has_marker(item, markers) for item in value)
    return isinstance(value, str) and value in markers


def is_pa12_record(record):
    """Detect source/family/dataset claims even after another label is removed."""
    # Shared UTS/dataset fields also occur in the separately reviewed median/SD
    # family. Exempt it only after its full source-specific guard succeeds.
    from ._paht_cf_observation_contract import PAHT_FAMILY, validate_paht_record
    if isinstance(record, dict) and record.get('method_family') == PAHT_FAMILY:
        validate_paht_record(record)
        return False
    return isinstance(record, dict) and (
        _has_marker(record, {PA12_FAMILY, PA12_SOURCE, PA12_DATASET, PA12_PROTOCOL,
                            PA12_QUANTITY, PA12_ARTIFACT, PA12_DOI, PA12_MAIN,
                            PA12_MAIN + "#polymers-18-00563-t003",
                            "PA12 CF15", "Fiberlogy",
                            "experiment_derived_tensile_test_summary"})
        or any(key in record for key in ("dataset_id", "protocol_id", "source_cell", "si_result"))
    )


def _exact(actual, expected):
    if isinstance(expected, dict):
        _require(isinstance(actual, dict), "missing structured metadata")
        for key, value in expected.items():
            _require(key in actual, "missing " + key)
            _exact(actual[key], value)
    elif type(expected) in (int, float):
        _require(type(actual) in (int, float) and actual == expected
                 and (type(actual) is int or math.isfinite(actual)), "source numeric identity changed")
    else:
        _require(type(actual) is type(expected) and actual == expected,
                 "source/method identity changed")


def _exact_pa(source_string):
    # A caller's global Decimal precision/traps must not change catalog admission.
    # Thirty-two digits are ample for these six closed two-decimal source cells.
    with localcontext(Context(prec=32)):
        return Decimal(source_string) * Decimal("1000000")


def validate_pa12_record(record):
    """Validate one admitted source cell, independently of record ID or name."""
    _require(isinstance(record, dict), "invalid record shape")
    _require(all(isinstance(record.get(key), str) and record[key].strip()
                 for key in ("id", "name")), "missing record identity")
    _exact(record, {
        "version": "1.0.0", "method_family": PA12_FAMILY,
        "study_id": PA12_SOURCE, "dataset_id": PA12_DATASET,
        "protocol_id": PA12_PROTOCOL, "quantity": PA12_QUANTITY,
        "quantity_dimension": "pressure", "si_unit": "Pa",
        "evaluation_support": "catalog_only",
        "observation_type": "experiment_derived_tensile_test_summary",
        "model_status": "source_reported_tensile_summary_with_explicit_metadata_gaps",
        "material": {"dimensionality": 3, "commercial_grade_as_reported": "PA12 CF15",
            "isotropy_established": False, "measured_porosity": None,
            "reinforcement_mass_fraction": {"value": 15, "unit": "wt.%",
                "basis": "declared_formulation", "independently_assayed_fraction": None}},
        "source_cell": {"table": "3", "table_container_id": "polymers-18-00563-t003",
            "expanded_table_id": "table_body_display_polymers-18-00563-t003",
            "row": "Ultimate tensile strength, MPa ± SD"},
        "reported_result": {"unit": "MPa", "summary_statistic": "reported_central_value",
            "central_statistic_explicitly_named": None, "aggregation_convention": None,
            "uncertainty": {"unit": "MPa", "notation": "plus_minus",
                "type": "reported_standard_deviation",
                "definition_basis": "publisher_html_table_header",
                "sample_or_population_formula": None, "coverage_factor": None,
                "confidence_level": None, "averaging_convention": None,
                "evidence": {"source_id": PA12_SOURCE, "artifact": PA12_ARTIFACT,
                    "component_id": "polymers-18-00563-t003"}}},
        "si_result": {"unit": "Pa", "normalization": {
            "kind": "exact_decimal_unit_scale", "from_unit": "MPa", "to_unit": "Pa",
            "factor_string": "1000000", "offset_string": "0",
            "basis": "SI_prefix_only_no_geometry_or_thickness", "adds_measurement_precision": False}},
        "method": {"technique": "quasi_static_uniaxial_tension", "stress_measure": None,
            "stress_area_basis": None, "uts_extraction_criterion": None,
            "local_strain_rate_per_s": None, "standard_as_cited": "ISO 527",
            "standard_compliance_independently_verified": False, "standard_url_validated": False,
            "loading_rate": {"value": 1, "value_string": "1", "unit": "mm/min",
                "source_label": "load rate", "quantity": "displacement_crosshead_rate"},
            "strain_reference_length": {"value": 110, "unit": "mm",
                "basis": "full_grip_separation_including_transition_regions"},
            "specimen": {"gauge_length_mm_as_reported": 80,
                "measured_cross_section_for_stress": None, "dimensional_tolerances": None},
            "preparation": {"printing_parameters": {"raster_angle_table_label": "45",
                "raster_methods_description": "+45°/-45°", "infill_setting_percent": 100,
                "build_orientation": "horizontal on heated bed", "printing_chamber_temperature": None}}},
        "conditions": {"atmosphere": None, "pressure": None,
            "temperature": {"unit": "degC", "basis": "reported_chamber_test_condition",
                "stabilization_duration_min": 30, "direct_specimen_temperature_measurement": None,
                "sensor_type_and_location": None, "stability_tolerance": None, "tensile_heating_rate": None},
            "humidity": {"relative_humidity_percent": None, "humidity_tolerance": None,
                "specimen_moisture_content": None}},
        "sample_metadata": {"count": 3, "scope": "tensile_tests_per_temperature_condition",
            "raw_replicate_values_available": False, "replicate_independence": None,
            "aggregation_convention": None, "independently_characterized_specimen_count": None},
        "verification": {"independent_scientific_review": False,
            "source_inspection": {"artifact": PA12_ARTIFACT, "publication_date": "2026-02-26",
                "access_date": "2026-10-03", "html_latest_update_as_reported": "3 September 2026 02:53 CEST",
                "pdf_upload_as_reported": "26 February 2026 11:36 CET",
                "pdf_inspected": False, "pdf_pagination": None, "pdf_equivalence_claimed": False,
                "separate_reader_transcription_checked": True, "selected_cells_transcription_agree": True,
                "raw_data_reanalysis": False, "raw_replicate_sd_recomputed": False,
                "stress_area_recomputed": False, "plot_digitization": False, "independent_replication": False},
            "rights": {"license_identifier": "CC-BY-4.0", "article_license_verified": True,
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "source_assets_redistributed": False,
                "selected_table_third_party_credit_line_present": False}},
    })
    column = record["source_cell"].get("temperature_column")
    _require(isinstance(column, str) and column in PA12_CELLS, "unsupported source temperature cell")
    central, sd, pa, sd_pa = PA12_CELLS[column]
    _exact(record["conditions"]["temperature"], {"value": int(column), "value_string": column})
    result = record["reported_result"]
    _exact(result, {"value_string": central, "source_value_string": central + " ± " + sd,
                    "uncertainty": {"value_string": sd}})
    # Decimal operates on exact reported strings, never binary-float products.
    try:
        for number, source_string, si_number in (
                (result.get("value"), central, record["si_result"].get("value")),
                (result["uncertainty"].get("value"), sd, record["si_result"].get("uncertainty_value"))):
            _require((type(number) is int or (type(number) is float and math.isfinite(number))), "invalid reported number")
            _require((type(si_number) is int or (type(si_number) is float and math.isfinite(si_number))), "invalid normalized number")
            _require(Decimal(str(number)) == Decimal(source_string), "numeric/source-string mismatch")
            _require(_exact_pa(source_string) == Decimal(str(si_number)),
                     "incorrect exact SI prefix normalization")
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("PA12 CF15 observation contract: invalid exact decimal normalization") from exc
    _exact(record["si_result"], {"value": pa, "uncertainty_value": sd_pa})
    payload = {key: value for key, value in record.items() if key not in ("id", "name")}
    _require(_digest(payload) == PA12_SCIENTIFIC_PAYLOAD_SHA256[column],
             "source-defined scientific payload changed")


def validate_pa12_dataset(records, require_complete=False):
    """Validate subsets; packaged admission additionally needs the complete six-cell set.

    Scientific aliases never count as an additional observation. Duplicate
    dataset/quantity/source-cell identities are invalid even with different IDs.
    """
    _require(isinstance(records, (list, tuple)), "records must be a sequence")
    _require(type(require_complete) is bool, "invalid completeness flag")
    seen = set()
    selected = []
    for record in records:
        _require(isinstance(record, dict), "invalid record shape")
        if not is_pa12_record(record):
            continue
        validate_pa12_record(record)
        identity = (record["dataset_id"], record["quantity"],
                    json.dumps(record["source_cell"], ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        _require(identity not in seen, "duplicate dataset/quantity/source cell, including aliases")
        seen.add(identity)
        selected.append(record["source_cell"]["temperature_column"])
    if require_complete:
        _require(len(selected) == len(PA12_TEMPERATURES) and set(selected) == set(PA12_TEMPERATURES),
                 "packaged dataset must contain exactly six unique approved source cells")


def validate_pa12_sources(sources):
    """Check the actual referenced source object, not a canonical replacement.

    Unrelated historical source records are untouched. Subsets without this
    study are allowed; a renamed source retaining its DOI/title/URL fails closed.
    The caller still checks cross-catalog reference resolution.
    """
    _require(isinstance(sources, (list, tuple)), "sources must be a sequence")
    matches = []
    markers = {PA12_SOURCE, PA12_DOI, "https://doi.org/" + PA12_DOI,
               PA12_MAIN, PA12_MAIN + "/notes", PA12_SOURCE_TITLE}
    for source in sources:
        _require(isinstance(source, dict), "invalid source shape")
        if not _has_marker(source, markers):
            continue
        _exact(source, {"id": PA12_SOURCE, "doi": PA12_DOI, "title": PA12_SOURCE_TITLE,
            "authors": ["Justas Ciganas", "Tomas Kalinauskis", "Urte Cigane"], "year": 2026,
            "urls": ["https://doi.org/" + PA12_DOI, PA12_MAIN, PA12_MAIN + "/notes",
                     "https://creativecommons.org/licenses/by/4.0/"],
            "license": {"identifier": "CC-BY-4.0"}})
        _require(_digest(source) == PA12_SOURCE_PAYLOAD_SHA256, "source bibliography/version/rights payload changed")
        matches.append(source)
    _require(len(matches) <= 1, "duplicate or aliased source")
