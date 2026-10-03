"""Closed descriptive juxtaposition of two reviewed temperature source groups.

This separate presentation never infers matched conditions or turns reported SD
into uncertainty endpoints. Catalog snapshots retain their historical policies;
this named display profile alone authorizes the new central-summary panels.
"""
from copy import deepcopy
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from .catalog import read_catalog
from ._observation_contract import validate_observation_records
from ._pa12_cf15_observation_contract import (
    PA12_SOURCE, PA12_DATASET, PA12_PROTOCOL, PA12_FAMILY, PA12_QUANTITY,
    PA12_TEMPERATURES, validate_pa12_dataset, validate_pa12_sources,
)
from ._paht_cf_observation_contract import (
    PAHT_SOURCE, PAHT_DATASET, PAHT_PROTOCOL, PAHT_FAMILY,
    PAHT_TEMPERATURES, validate_paht_dataset, validate_paht_sources,
)
from .validation import ValidationError

SCHEMA_VERSION = '1.0.0'
PROFILE_ID = 'ciganas-zach-uts-temperature-v1'
PROFILE_VERSION = '1.0.0'
WARNING_CODES = ('scope_comparison', 'scope_material', 'scope_unknowns',
                 'scope_temperature', 'scope_sd', 'scope_limits')
POLICY = {
    'purpose': 'descriptive_juxtaposition_of_two_reviewed_source_groups',
    'evaluation_support': 'catalog_only',
    'matched_conditions_established': False, 'unknown_conditions_equivalent': False,
    'statistical_independence_established': False,
    'profile_scope': 'separately_curated_presentation_preserves_historical_source_snapshots',
    'axes': {
        'x': {'quantity': 'reported_chamber_test_condition', 'unit': 'degC',
              'scale': 'linear', 'domain': [15, 155], 'ticks': [20, 40, 60, 80, 100, 120, 140]},
        'y': {'quantity': PA12_QUANTITY, 'unit': 'MPa', 'scale': 'linear',
              'domain': [0, 65], 'ticks': [0, 10, 20, 30, 40, 50, 60]},
    },
    'axis_domains_are_display_padding_not_validated_ranges_or_material_limits': True,
    'axis_ticks_are_reference_coordinates_not_observations': True,
    'zero_y_is_display_baseline_not_experimental_bound': True,
    'point_style': 'unconnected_equal_radius_equal_color_no_jitter',
    'point_center': 'source_reported_central_summary_with_source_specific_statistic',
    'sd_display': 'always_visible_separate_source_exact_column',
    'sd_is_uncertainty_of_central_statistic': False,
    'uncertainty_endpoints_calculated': False, 'temperature_whiskers_allowed': False,
    'no_temperature_whiskers_means': 'temperature_uncertainty_unreported_not_zero',
    'overlay_allowed': False, 'additional_groups_allowed': False,
    'fit_allowed': False, 'connecting_lines_allowed': False,
    'interpolation_allowed': False, 'extrapolation_allowed': False,
    'pooling_allowed': False, 'normalization_allowed': False,
    'retention_ratios_allowed': False, 'deltas_allowed': False,
    'ranking_allowed': False, 'significance_test_allowed': False,
    'material_prediction_allowed': False, 'design_allowable_allowed': False,
    'geometry_or_thickness_conversion_allowed': False, 'formula_execution_allowed': False,
    'panel_order': 'fixed_source_order_ciganas_then_zach_not_magnitude_or_quality',
    'source_precision_preserved': True,
    'si_values_role': 'source_exact_metadata_only_conditional_SD_basis_preserved_no_added_precision',
    'required_warning_codes': list(WARNING_CODES),
    'metadata_digests_identify': 'bundled_catalog_or_curated_policy_not_publisher_artifact_bytes',
    'csv_missing_scalar': 'null',
    'csv_text_import_required': 'identity_source_and_JSON_fields_may_be_formula_like_import_as_text',
    'locale_review': 'machine_assisted_not_independently_scientifically_or_native_language_reviewed',
}
# These authored fact categories resolve source fields independently. Equality,
# shared missing values and common units never generate compatibility claims.
COMMON_PATHS = {
    'preparation': ('material', 'method.preparation'),
    'printing': ('method.preparation.printer', 'method.preparation.printing_parameters'),
    'geometry': ('method.instrument', 'method.specimen', 'method.strain_reference_length'),
    'rate': ('method.loading_rate', 'method.local_strain_rate_per_s'),
    'statistic': ('reported_result.summary_statistic', 'reported_result.central_statistic_explicitly_named', 'sample_metadata'),
    'sd': ('reported_result.uncertainty',),
    'temperature': ('conditions.temperature', 'conditions.humidity', 'method.standard_as_cited', 'method.standard_compliance_independently_verified'),
}
GROUPS = (
    ('ciganas', PA12_SOURCE, PA12_DATASET, PA12_PROTOCOL, PA12_FAMILY, PA12_TEMPERATURES),
    ('zach', PAHT_SOURCE, PAHT_DATASET, PAHT_PROTOCOL, PAHT_FAMILY, PAHT_TEMPERATURES),
)


class ObservationStudyComparisonError(ValidationError):
    """Unsupported, altered, stale or unsafe named study comparison."""


def _require(condition, message):
    if not condition:
        raise ObservationStudyComparisonError(message)


def _json_safe(value):
    if type(value) is str:
        _require(all(ord(c) in (9, 10, 13) or 0x20 <= ord(c) <= 0xD7FF
                     or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF
                     for c in value), 'XML-illegal character in study-comparison text')
    elif value is None or type(value) in (bool, int):
        return
    elif type(value) is float:
        _require(math.isfinite(value), 'nonfinite JSON number')
    elif type(value) is list:
        for item in value:
            _json_safe(item)
    elif type(value) is dict:
        for key, item in value.items():
            _require(type(key) is str, 'JSON keys must be strings')
            _json_safe(key); _json_safe(item)
    else:
        raise ObservationStudyComparisonError('non-JSON study-comparison value')


def _canonical(value, pretty=False):
    _json_safe(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      indent=2 if pretty else None, separators=None if pretty else (',', ':'))


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
        raise ObservationStudyComparisonError('invalid source URL') from exc
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


def _at(record, path):
    result = record
    for part in path.split('.'):
        result = result[part]
    return deepcopy(result)


def _facts(record):
    return [{'fact_id': key, 'evidence_paths': list(paths),
             'evidence_values': [_at(record, path) for path in paths]}
            for key, paths in COMMON_PATHS.items()]


def _point(record, panel_id):
    result = record['reported_result']
    # Do not invent source fields to align different schemas. The presentation
    # interpretation is explicitly separate; reported_sd stays source-exact.
    sd_presentation = {
        'kind': 'curated_presentation_interpretation',
        'unit': result['uncertainty']['unit'],
        'basis': ('explicit_Table_3_UTS_MPa_plus_minus_SD_row' if panel_id == 'ciganas'
                  else 'contextual_inference_from_associated_UTS_column_not_explicit_SD_header'),
        'evidence': deepcopy(result['uncertainty']['evidence']),
    }
    return {
        'record_id': record['id'], 'record_version': record['version'],
        'source_cell': deepcopy(record['source_cell']),
        'temperature': deepcopy(record['conditions']['temperature']),
        'central_value_string': result['value_string'], 'central_unit': result['unit'],
        'summary_statistic': result['summary_statistic'],
        'central_statistic_explicitly_named': result['central_statistic_explicitly_named'],
        'source_value_string': result['source_value_string'],
        'reported_sd': deepcopy(result['uncertainty']),
        'sd_unit_presentation': sd_presentation,
        'sample_metadata': deepcopy(record['sample_metadata']),
        'si_result': deepcopy(record['si_result']),
    }


def build_observation_study_comparison(*, profile_id):
    """Resolve exactly the reviewed pair, retaining independent source order."""
    from . import __version__
    _require(type(profile_id) is str and profile_id == PROFILE_ID,
             'unsupported study-comparison profile; explicit reviewed profile ID required')
    try:
        catalog, source_catalog = read_catalog('observations'), read_catalog('sources')
        _json_safe(catalog); _json_safe(source_catalog)
        _require(catalog['schema_version'] == '1.3.0' and source_catalog['schema_version'] == '1.0.0',
                 'unsupported observation/source catalog schema')
        records, sources = catalog['records'], source_catalog['records']
        validate_observation_records(records)
        validate_pa12_dataset(records, require_complete=True)
        validate_paht_dataset(records, require_complete=True)
        validate_pa12_sources(sources); validate_paht_sources(sources)
        ids, source_ids = [r['id'] for r in records], [s['id'] for s in sources]
        _require(len(ids) == len(set(ids)), 'duplicate observation IDs')
        _require(len(source_ids) == len(set(source_ids)), 'duplicate source IDs')
        selected, panels = [], []
        for panel_id, study, dataset, protocol, family, temperatures in GROUPS:
            candidates = [r for r in records if r.get('dataset_id') == dataset]
            _require(len(candidates) == len(temperatures), 'incomplete or extra source group')
            by_cell = {r['source_cell']['temperature_column']: r for r in candidates}
            ordered = [by_cell[t] for t in temperatures]
            referenced = {r['study_id'] for r in ordered}
            referenced.update(e['source_id'] for r in ordered for e in r['evidence'])
            _require(referenced == {study}, 'unreviewed group source reference')
            selected.extend(ordered)
            panels.append({
                'panel_id': panel_id, 'study_id': study, 'dataset_id': dataset,
                'protocol_id': protocol, 'method_family': family, 'quantity': PA12_QUANTITY,
                'warning_codes': list(WARNING_CODES),
                'plot_policy': {'axes': deepcopy(POLICY['axes']),
                                'central_only': True, 'unconnected': True,
                                'sd_text_always_visible': True, 'uncertainty_endpoints_calculated': False},
                'protocol_facts': _facts(ordered[0]),
                'points': [_point(r, panel_id) for r in ordered],
            })
        _require({PA12_SOURCE, PAHT_SOURCE}.issubset(source_ids), 'missing actual referenced source')
        actual_sources = [next(s for s in sources if s['id'] == group[1]) for group in GROUPS]
        _require(len(actual_sources) == 2, 'exactly two actual sources required')
        validate_pa12_sources(actual_sources); validate_paht_sources(actual_sources)
        _validate_links(selected); _validate_links(actual_sources)
        return {
            'schema_version': SCHEMA_VERSION, 'kind': 'observation_study_comparison',
            'engine_version': __version__,
            'catalog_schema_versions': {'observations': catalog['schema_version'], 'sources': source_catalog['schema_version']},
            'selection': {'profile_id': profile_id, 'profile_version': PROFILE_VERSION,
                          'resolved_record_ids': [r['id'] for r in selected],
                          'resolved_source_cells': [deepcopy(r['source_cell']) for r in selected]},
            'comparison_scope': POLICY['purpose'], 'matched_conditions_established': False,
            'unknown_conditions_equivalent': False,
            'presentation_policy': deepcopy(POLICY), 'policy_digest_sha256': _digest(POLICY),
            'panels': panels, 'record_snapshots': deepcopy(selected), 'source_snapshots': deepcopy(actual_sources),
            'record_digests': [{'record_id': r['id'], 'record_version': r['version'], 'sha256': _digest(r)} for r in selected],
            'source_digests': [{'source_id': s['id'], 'sha256': _digest(s)} for s in actual_sources],
        }
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ObservationStudyComparisonError('invalid study comparison: ' + str(exc)) from exc


def validate_observation_study_comparison(bundle):
    """Every public output requires equality with a fresh canonical rebuild."""
    try:
        _require(type(bundle) is dict, 'study comparison must be an object')
        _json_safe(bundle)
        rebuilt = build_observation_study_comparison(profile_id=bundle['selection']['profile_id'])
        _require(_canonical(bundle) == _canonical(rebuilt),
                 'noncanonical or stale study comparison; rebuild from current catalogs')
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ObservationStudyComparisonError('invalid study comparison: ' + str(exc)) from exc


def observation_study_comparison_json(bundle):
    validate_observation_study_comparison(bundle)
    return _canonical(bundle, pretty=True) + '\n'


CSV_COLUMNS = (
    'profile_id', 'profile_version', 'comparison_scope', 'matched_conditions_established',
    'unknown_conditions_equivalent', 'study_id', 'dataset_id', 'protocol_id', 'method_family',
    'panel_id', 'record_id', 'record_version', 'quantity', 'source_cell_json',
    'required_warning_codes_json', 'essential_caveats', 'protocol_facts_json',
    'summary_statistic', 'central_statistic_explicitly_named', 'sd_type', 'sd_notation',
    'sd_unit', 'sd_unit_presentation_json', 'sd_source_metadata_json',
    'sample_count_scope', 'replicate_independence', 'temperature_basis',
    'temperature_uncertainty', 'temperature_value_string', 'temperature_unit',
    'central_value_string', 'central_unit', 'sd_value_string', 'source_value_string',
    'sample_count', 'si_result_json', 'source_inspection_json', 'rights_json',
    'engine_version', 'comparison_schema_version', 'catalog_schema_versions_json',
    'scalar_missing_convention', 'selection_json', 'presentation_policy_json',
    'policy_digest_sha256', 'record_snapshot_sha256', 'source_snapshot_digests_json',
    'record_snapshot_json', 'source_snapshots_json',
)


def observation_study_comparison_csv(bundle):
    """Ten long-form rows, never a temperature join or pooled/pivoted table.

    Import identity/source/JSON fields as text: formula-like strings are retained
    verbatim for scientific interchange. Missing scalar values are literal null.
    """
    from ._observation_study_comparison_labels import labels
    validate_observation_study_comparison(bundle)
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator='\n')
    writer.writeheader()
    t = labels('en')
    scalar = lambda value: 'null' if value is None else str(value).lower() if type(value) is bool else value
    snapshots = {r['id']: r for r in bundle['record_snapshots']}
    digests = {r['record_id']: r['sha256'] for r in bundle['record_digests']}
    for panel in bundle['panels']:
        for point in panel['points']:
            r = snapshots[point['record_id']]
            sd, sample, temp = point['reported_sd'], point['sample_metadata'], point['temperature']
            writer.writerow(dict(
                profile_id=PROFILE_ID, profile_version=PROFILE_VERSION,
                comparison_scope=bundle['comparison_scope'], matched_conditions_established='false', unknown_conditions_equivalent='false',
                study_id=panel['study_id'], dataset_id=panel['dataset_id'], protocol_id=panel['protocol_id'],
                method_family=panel['method_family'], panel_id=panel['panel_id'], record_id=r['id'], record_version=r['version'],
                quantity=panel['quantity'], source_cell_json=_canonical(point['source_cell']),
                required_warning_codes_json=_canonical(list(WARNING_CODES)), essential_caveats=' '.join(t[k] for k in WARNING_CODES),
                protocol_facts_json=_canonical(panel['protocol_facts']), summary_statistic=point['summary_statistic'],
                central_statistic_explicitly_named=scalar(point['central_statistic_explicitly_named']),
                sd_type=sd['type'], sd_notation=sd['notation'], sd_unit=sd['unit'],
                sd_unit_presentation_json=_canonical(point['sd_unit_presentation']), sd_source_metadata_json=_canonical(sd),
                sample_count_scope=sample['scope'], replicate_independence=scalar(sample['replicate_independence']),
                temperature_basis=temp['basis'], temperature_uncertainty='null', temperature_value_string=temp['value_string'], temperature_unit=temp['unit'],
                central_value_string=point['central_value_string'], central_unit=point['central_unit'], sd_value_string=sd['value_string'],
                source_value_string=point['source_value_string'], sample_count=sample['count'], si_result_json=_canonical(point['si_result']),
                source_inspection_json=_canonical(r['verification']['source_inspection']), rights_json=_canonical(r['verification']['rights']),
                engine_version=bundle['engine_version'], comparison_schema_version=SCHEMA_VERSION,
                catalog_schema_versions_json=_canonical(bundle['catalog_schema_versions']), scalar_missing_convention='null',
                selection_json=_canonical(bundle['selection']), presentation_policy_json=_canonical(bundle['presentation_policy']),
                policy_digest_sha256=bundle['policy_digest_sha256'], record_snapshot_sha256=digests[r['id']],
                source_snapshot_digests_json=_canonical(bundle['source_digests']), record_snapshot_json=_canonical(r),
                source_snapshots_json=_canonical(bundle['source_snapshots']),
            ))
    return out.getvalue()


def render_observation_study_comparison_svg(bundle, *, lang='en', width=1100):
    from ._observation_study_comparison_rendering import render_observation_study_comparison_svg as render
    return render(bundle, lang=lang, width=width)


def render_observation_study_comparison_html(bundle, *, lang='en'):
    from ._observation_study_comparison_rendering import render_observation_study_comparison_html as render
    return render(bundle, lang=lang)


def export_observation_study_comparison(directory, *, profile_id, lang='en'):
    """Preflight all artifacts before writes; later disk failure is not atomic."""
    bundle = build_observation_study_comparison(profile_id=profile_id)
    prefix = 'observation-study-comparison'
    artifacts = {
        f'{prefix}.json': observation_study_comparison_json(bundle),
        f'{prefix}.csv': observation_study_comparison_csv(bundle),
        f'{prefix}.{lang}.svg': render_observation_study_comparison_svg(bundle, lang=lang),
        f'{prefix}.narrow.{lang}.svg': render_observation_study_comparison_svg(bundle, lang=lang, width=380),
        f'{prefix}.{lang}.html': render_observation_study_comparison_html(bundle, lang=lang),
    }
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        (target / name).write_text(content, encoding='utf-8', newline='\n')
    return list(artifacts)
