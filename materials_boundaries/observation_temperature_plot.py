"""Closed, descriptive display of six source-reported tensile summaries.

This separate route does not relax inspection policy or evaluate a material law.
Admission is by reviewed source cell, never by record name, units or JSON shape.
Every output rebuilds against the current catalogs; metadata hashes are not
publisher artifact hashes. Decimal subtraction/addition is glyph arithmetic only.
"""
from copy import deepcopy
import csv
from decimal import Context, Decimal, localcontext
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from .catalog import read_catalog
from ._observation_contract import validate_observation_records
from ._pa12_cf15_observation_contract import (
    PA12_ARTIFACT, PA12_DATASET, PA12_FAMILY, PA12_PROTOCOL, PA12_QUANTITY,
    PA12_SOURCE, PA12_TEMPERATURES, validate_pa12_dataset, validate_pa12_sources,
)
from .validation import ValidationError

SCHEMA_VERSION = '1.0.0'
PROFILE_ID = 'ciganas-pa12-cf15-table3-uts-temperature-v1'
DERIVATION = 'decimal_central_plus_minus_reported_sd_for_glyph_only'
WARNING_CODES = ('scope_protocol', 'scope_temperature', 'scope_statistic',
                 'scope_sd', 'scope_preparation', 'scope_limits')
POLICY = {
    'purpose': 'descriptive_source_reported_condition_summaries',
    'evaluation_support': 'catalog_only',
    'axes': {
        'x': {'quantity': 'reported_chamber_test_condition', 'unit': 'degC',
              'display_unit': '°C', 'scale': 'linear', 'domain': [15, 125],
              'ticks': [23, 40, 60, 80, 100, 120]},
        'y': {'quantity': PA12_QUANTITY, 'unit': 'MPa', 'scale': 'linear',
              'domain': [0, 55], 'ticks': [0, 10, 20, 30, 40, 50]},
    },
    'axis_domains_are_display_padding_not_material_limits': True,
    'zero_y_is_display_baseline_not_experimental_bound': True,
    'point_style': 'unconnected_equal_radius_equal_color_no_jitter',
    'point_center': 'source_reported_central_value_not_asserted_mean',
    'vertical_whisker': 'central_value_plus_minus_source_reported_standard_deviation',
    'whiskers_required': True,
    'derived_glyph_endpoints_are_observations': False,
    'endpoint_derivation': DERIVATION,
    'temperature_uncertainty': None,
    'no_horizontal_whisker_means': 'temperature_uncertainty_unreported_not_zero',
    'source_order': 'Table_3_temperature_columns_23_40_60_80_100_120',
    'source_precision_preserved': True,
    'raw_replicates_available': False,
    'replicate_independence': None,
    'standard_deviation_is_sem': False,
    'standard_deviation_is_confidence_interval': False,
    'standard_deviation_is_observed_min_max': False,
    'standard_deviation_is_hard_bound': False,
    'standard_deviation_asserts_coverage': False,
    'central_statistic_explicitly_named': None,
    'aggregation_convention': None,
    'unknown_conditions_equivalent': False,
    'overlay_allowed': False, 'additional_groups_allowed': False,
    'fit_allowed': False, 'connecting_lines_allowed': False,
    'interpolation_allowed': False, 'extrapolation_allowed': False,
    'aggregation_allowed': False, 'normalization_allowed': False,
    'ranking_allowed': False, 'percent_change_allowed': False,
    'significance_test_allowed': False, 'material_prediction_allowed': False,
    'design_allowable_allowed': False, 'safety_claim_allowed': False,
    'formula_execution_allowed': False, 'geometry_or_thickness_conversion_allowed': False,
    'second_plotted_series_allowed': False,
    'si_values_role': 'existing_exact_Pa_metadata_only_no_added_precision',
    'required_warning_codes': list(WARNING_CODES),
    'snapshot_digests_identify': 'bundled_catalog_metadata_not_original_source_artifact_bytes',
    'policy_digest_identifies': 'curated_presentation_contract_not_publisher_artifact_bytes',
    'csv_missing_scalar': 'null',
    'locale_review': 'machine_assisted_not_independently_scientifically_or_native_language_reviewed',
}
GROUP = {
    'profile_id': PROFILE_ID, 'profile_version': '1.0.0',
    'study_id': PA12_SOURCE, 'dataset_id': PA12_DATASET, 'protocol_id': PA12_PROTOCOL,
    'method_family': PA12_FAMILY, 'quantity': PA12_QUANTITY,
    'compatibility_basis': 'one_reviewed_source_reported_shared_protocol_and_complete_Table_3_UTS_cells',
    'limitations': [
        'descriptive_transcription_not_independent_scientific_validation',
        'source_reported_shared_protocol_not_proof_of_identical_conditioning',
        'unknowns_are_not_comparability_wildcards',
        'not_six_independent_studies_or_confirmations',
        'no_cross_study_or_universal_material_claim',
        'future_groups_need_explicit_reviewed_schema_runtime_tests_and_documentation',
    ],
}


class ObservationTemperaturePlotError(ValidationError):
    """Invalid, altered, stale or unsupported explicit temperature plot."""


def _require(condition, message):
    if not condition:
        raise ObservationTemperaturePlotError(message)


def _json_safe(value):
    if type(value) is str:
        _require(all(ord(c) in (9, 10, 13) or 0x20 <= ord(c) <= 0xD7FF
                     or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF
                     for c in value), 'XML-illegal character in temperature-plot text')
    elif value is None or type(value) in (bool, int):
        return
    elif type(value) is float:
        _require(math.isfinite(value), 'nonfinite JSON number')
    elif type(value) is list:
        for item in value:
            _json_safe(item)
    elif type(value) is dict:
        for key, item in value.items():
            _require(type(key) is str, 'JSON object keys must be strings')
            _json_safe(key)
            _json_safe(item)
    else:
        raise ObservationTemperaturePlotError('non-JSON value in temperature plot')


def _canonical(value, pretty=False):
    _json_safe(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      indent=2 if pretty else None,
                      separators=None if pretty else (',', ':'))


def _digest(value):
    return hashlib.sha256(_canonical(value).encode('utf-8')).hexdigest()


def _safe_url(value):
    _require(type(value) is str and bool(value)
             and not any(c.isspace() or ord(c) < 32 for c in value), 'unsafe source URL')
    try:
        parsed = urlsplit(value)
        _require(parsed.scheme in ('http', 'https') and bool(parsed.hostname)
                 and parsed.username is None and parsed.password is None,
                 'source links require HTTP(S) without credentials')
        _ = parsed.port
    except ValueError as exc:
        raise ObservationTemperaturePlotError('invalid source URL') from exc
    return value


def _validate_links(value):
    if type(value) is dict:
        for key, item in value.items():
            if key in ('source_url', 'url', 'license_url', 'version_notes_url', 'doi_url', 'publisher_url') and item is not None:
                _safe_url(item)
            elif key == 'urls':
                for url in item:
                    _safe_url(url)
            else:
                _validate_links(item)
    elif type(value) is list:
        for item in value:
            _validate_links(item)


def _glyph(record):
    result, temp = record['reported_result'], record['conditions']['temperature']
    central, sd = result['value_string'], result['uncertainty']['value_string']
    # Context() is fresh: neither global precision, rounding nor traps leak in.
    # No source field or record is changed, and these endpoints are not data.
    with localcontext(Context(prec=32)):
        lower = format(Decimal(central) - Decimal(sd), 'f')
        upper = format(Decimal(central) + Decimal(sd), 'f')
    return {
        'record_id': record['id'], 'source_cell': deepcopy(record['source_cell']),
        'temperature_value_string': temp['value_string'], 'temperature_unit': temp['unit'],
        'central_value_string': central, 'sd_value_string': sd,
        'source_value_string': result['source_value_string'], 'unit': result['unit'],
        'uncertainty_type': result['uncertainty']['type'],
        'sample_count': record['sample_metadata']['count'],
        'temperature_uncertainty': None,
        'derived_lower_string': lower, 'derived_upper_string': upper,
        'derivation': DERIVATION,
    }


def build_observation_temperature_plot(*, dataset_id):
    """Resolve the complete unique reviewed dataset and restore source order."""
    from . import __version__
    _require(type(dataset_id) is str and dataset_id == PA12_DATASET,
             'unsupported temperature-plot dataset; explicit reviewed dataset ID required')
    try:
        catalog, source_catalog = read_catalog('observations'), read_catalog('sources')
        _json_safe(catalog); _json_safe(source_catalog)
        _require(catalog['schema_version'] == '1.3.0' and source_catalog['schema_version'] == '1.0.0',
                 'unsupported observation/source catalog schema version')
        records, sources = catalog['records'], source_catalog['records']
        validate_observation_records(records)
        validate_pa12_dataset(records, require_complete=True)
        validate_pa12_sources(sources)
        all_ids, source_ids = [r['id'] for r in records], [s['id'] for s in sources]
        _require(len(all_ids) == len(set(all_ids)), 'duplicate packaged observation IDs')
        _require(len(source_ids) == len(set(source_ids)), 'duplicate packaged source IDs')
        selected = [r for r in records if r.get('dataset_id') == dataset_id]
        validate_pa12_dataset(selected, require_complete=True)
        by_cell = {r['source_cell']['temperature_column']: r for r in selected}
        selected = [by_cell[t] for t in PA12_TEMPERATURES]
        referenced = {r['study_id'] for r in selected}
        referenced.update(e['source_id'] for r in selected for e in r['evidence'])
        _require(referenced == {PA12_SOURCE} and referenced.issubset(source_ids),
                 'missing or unapproved referenced temperature-plot source')
        actual_source = [s for s in sources if s['id'] in referenced]
        _require(len(actual_source) == 1, 'one actual reviewed source required')
        validate_pa12_sources(actual_source)
        _validate_links(selected); _validate_links(actual_source)
        return {
            'schema_version': SCHEMA_VERSION, 'kind': 'observation_temperature_plot',
            'engine_version': __version__,
            'catalog_schema_versions': {'observations': catalog['schema_version'],
                                        'sources': source_catalog['schema_version']},
            'selection': {'dataset_id': dataset_id,
                          'resolved_record_ids': [r['id'] for r in selected],
                          'resolved_source_cells': [deepcopy(r['source_cell']) for r in selected]},
            'group': deepcopy(GROUP), 'presentation_policy': deepcopy(POLICY),
            'policy_digest_sha256': _digest(POLICY),
            'glyphs': [_glyph(r) for r in selected],
            'record_snapshots': deepcopy(selected), 'source_snapshots': deepcopy(actual_source),
            'record_digests': [{'record_id': r['id'], 'record_version': r['version'], 'sha256': _digest(r)} for r in selected],
            'source_digests': [{'source_id': s['id'], 'sha256': _digest(s)} for s in actual_source],
        }
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ObservationTemperaturePlotError('invalid observation temperature plot: ' + str(exc)) from exc


def validate_observation_temperature_plot(bundle):
    """Canonical rebuild closes every field, including unknowns and snapshots."""
    try:
        _require(type(bundle) is dict, 'temperature plot must be an object')
        _json_safe(bundle)
        rebuilt = build_observation_temperature_plot(dataset_id=bundle['selection']['dataset_id'])
        _require(_canonical(bundle) == _canonical(rebuilt),
                 'noncanonical or stale temperature plot; regenerate from current packaged catalogs')
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ObservationTemperaturePlotError('invalid observation temperature plot: ' + str(exc)) from exc


def temperature_observation_plot_json(bundle):
    validate_observation_temperature_plot(bundle)
    return _canonical(bundle, pretty=True) + '\n'


CSV_COLUMNS = (
    'classification', 'evaluation_support', 'dataset_id', 'profile_id', 'profile_version',
    'study_id', 'protocol_id', 'method_family', 'quantity', 'quantity_dimension',
    'record_id', 'record_version', 'source_cell_json', 'required_warning_codes_json',
    'essential_caveats', 'temperature_basis', 'temperature_uncertainty',
    'central_statistic_explicitly_named', 'aggregation_convention', 'stress_measure',
    'stress_area_basis', 'uncertainty_type', 'uncertainty_interpretation',
    'uncertainty_evidence_json', 'sample_count_scope', 'replicate_independence',
    'source_artifact', 'source_inspection_json', 'rights_json',
    'temperature_value_string', 'temperature_unit', 'source_value_string',
    'central_value_string', 'sd_value_string', 'unit', 'sample_count',
    'si_central_value', 'si_sd_value', 'si_unit', 'normalization_json',
    'derived_glyph_lower_string', 'derived_glyph_upper_string', 'endpoint_derivation',
    'conditions_json', 'method_json', 'sample_metadata_json', 'evidence_json',
    'engine_version', 'plot_schema_version', 'observation_schema_version', 'source_schema_version',
    'scalar_missing_convention', 'selection_json', 'group_json', 'presentation_policy_json',
    'policy_digest_sha256', 'record_snapshot_sha256', 'source_snapshot_digests_json',
    'record_snapshot_json', 'source_snapshots_json',
)


def temperature_observation_plot_csv(bundle):
    """Fixed, locale-independent complete rows; unknown scalars spell null.

    Source/identity/JSON strings remain verbatim, even if formula-like. Import
    these columns as text in spreadsheets; this is a scientific interchange CSV.
    """
    from ._observation_temperature_labels import labels
    validate_observation_temperature_plot(bundle)
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator='\n')
    writer.writeheader()
    t = labels('en')
    scalar = lambda value: 'null' if value is None else value
    for r, g, digest in zip(bundle['record_snapshots'], bundle['glyphs'], bundle['record_digests']):
        result, sample, method = r['reported_result'], r['sample_metadata'], r['method']
        u, temp, si = result['uncertainty'], r['conditions']['temperature'], r['si_result']
        writer.writerow(dict(
            classification=r['observation_type'], evaluation_support=r['evaluation_support'],
            dataset_id=r['dataset_id'], profile_id=bundle['group']['profile_id'], profile_version=bundle['group']['profile_version'],
            study_id=r['study_id'], protocol_id=r['protocol_id'], method_family=r['method_family'],
            quantity=r['quantity'], quantity_dimension=r['quantity_dimension'], record_id=r['id'], record_version=r['version'],
            source_cell_json=_canonical(r['source_cell']), required_warning_codes_json=_canonical(list(WARNING_CODES)),
            essential_caveats=' '.join(t[code] for code in WARNING_CODES), temperature_basis=temp['basis'],
            temperature_uncertainty='null', central_statistic_explicitly_named=scalar(result['central_statistic_explicitly_named']),
            aggregation_convention=scalar(result['aggregation_convention']), stress_measure=scalar(method['stress_measure']),
            stress_area_basis=scalar(method['stress_area_basis']), uncertainty_type=u['type'],
            uncertainty_interpretation=u['interpretation'], uncertainty_evidence_json=_canonical(u['evidence']),
            sample_count_scope=sample['scope'], replicate_independence=scalar(sample['replicate_independence']),
            source_artifact=PA12_ARTIFACT, source_inspection_json=_canonical(r['verification']['source_inspection']),
            rights_json=_canonical(r['verification']['rights']), temperature_value_string=g['temperature_value_string'],
            temperature_unit=g['temperature_unit'], source_value_string=g['source_value_string'],
            central_value_string=g['central_value_string'], sd_value_string=g['sd_value_string'], unit=g['unit'],
            sample_count=sample['count'], si_central_value=str(int(si['value'])), si_sd_value=str(int(si['uncertainty_value'])),
            si_unit=si['unit'], normalization_json=_canonical(si['normalization']),
            derived_glyph_lower_string=g['derived_lower_string'], derived_glyph_upper_string=g['derived_upper_string'],
            endpoint_derivation=g['derivation'], conditions_json=_canonical(r['conditions']), method_json=_canonical(method),
            sample_metadata_json=_canonical(sample), evidence_json=_canonical(r['evidence']),
            engine_version=bundle['engine_version'], plot_schema_version=bundle['schema_version'],
            observation_schema_version=bundle['catalog_schema_versions']['observations'], source_schema_version=bundle['catalog_schema_versions']['sources'],
            scalar_missing_convention='null', selection_json=_canonical(bundle['selection']), group_json=_canonical(bundle['group']),
            presentation_policy_json=_canonical(bundle['presentation_policy']), policy_digest_sha256=bundle['policy_digest_sha256'],
            record_snapshot_sha256=digest['sha256'], source_snapshot_digests_json=_canonical(bundle['source_digests']),
            record_snapshot_json=_canonical(r), source_snapshots_json=_canonical(bundle['source_snapshots']),
        ))
    return out.getvalue()


def render_observation_temperature_svg(bundle, *, lang='en', width=1100):
    from ._observation_temperature_rendering import render_observation_temperature_svg as render
    return render(bundle, lang=lang, width=width)


def render_observation_temperature_html(bundle, *, lang='en'):
    from ._observation_temperature_rendering import render_observation_temperature_html as render
    return render(bundle, lang=lang)


def export_observation_temperature_plot(directory, *, dataset_id, lang='en'):
    """Preflight every complete artifact before any target/directory is written.

    Later filesystem failures may leave partial files: this is not an all-file
    transaction or rollback guarantee. Prefixes do not collide with inspection.
    """
    bundle = build_observation_temperature_plot(dataset_id=dataset_id)
    artifacts = {
        'observation-temperature-plot.json': temperature_observation_plot_json(bundle),
        'observation-temperature-plot.csv': temperature_observation_plot_csv(bundle),
        f'observation-temperature-plot.{lang}.svg': render_observation_temperature_svg(bundle, lang=lang),
        f'observation-temperature-plot.narrow.{lang}.svg': render_observation_temperature_svg(bundle, lang=lang, width=380),
        f'observation-temperature-plot.{lang}.html': render_observation_temperature_html(bundle, lang=lang),
    }
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        (target / name).write_text(content, encoding='utf-8', newline='\n')
    return list(artifacts)
