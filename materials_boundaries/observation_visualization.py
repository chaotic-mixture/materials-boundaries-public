"""Offline inspection of source-reported observations; no numerical comparison.

The closed bundle is rebuilt from the current packaged catalogs before every
output. Formulas remain inert text. This module never imports an evaluator.
"""
from copy import deepcopy
import csv
import hashlib
from html import escape
import io
import json
import math
from pathlib import Path
import unicodedata
from urllib.parse import urlsplit

from .catalog import read_catalog
from ._observation_contract import MOS2_FAMILY, validate_observation_records
from ._hbn_observation_contract import HBN_FAMILY
from ._pa12_cf15_observation_contract import PA12_FAMILY, validate_pa12_sources
from ._paht_cf_observation_contract import PAHT_FAMILY, validate_paht_sources
from ._paht_observation_labels import PAHT_LABELS, PAHT_CAVEATS, PAHT_DISPLAY_BASIS
from .i18n import translate
from .validation import ValidationError

QUANTITY_LABELS = {'in_plane_stiffness_2d': 'stiffness',
                   'breaking_strength_2d': 'strength',
                   'ultimate_tensile_strength_as_reported_3d': 'pa12_strength'}
QUANTITIES = tuple(QUANTITY_LABELS)
LEE_FAMILY = 'lee_2008_legacy_indentation_v1'
# Integrity of the two legacy source-defined scientific payloads, not paper
# hashes. IDs/names remain appendable and evidence order is immaterial.
LEE_SCIENTIFIC_PAYLOAD_SHA256 = {'in_plane_stiffness_2d': '4fbf98b62f6b011869561e5ec20f65fa2dec6e48c7845483f404b9c327f75f44', 'breaking_strength_2d': '0a26d5ebc57eea2d0ba1b8f26b479d380fd14b5e7ddebfc81e414708c58ea08e'}
MOS2_SCIENTIFIC_PAYLOAD_SHA256 = {'in_plane_stiffness_2d': 'cdc809aaf360a6f421e834132fc30a679facee3f5a0c14c98e7a228c633056a4', 'breaking_strength_2d': '36bc7c51b4e0b57c49bcaa26f87551c93a95621b759111dfe9e3bbc14930260f'}
DISPLAY_BASIS = 'catalog_reported_result_value_and_uncertainty_value_in_N_per_m_not_verbatim_source'
PA12_DISPLAY_BASIS = 'catalog_exact_reported_MPa_strings_not_additional_measurement_precision'
PA12_CAVEATS = ['pa12_temperature_warning', 'pa12_process_warning',
                'pa12_stress_statistic_warning', 'pa12_sd_count_warning',
                'pa12_scope_warning']
POLICY = {
    'purpose': 'inspection_only', 'display': 'source_ordered_text_facets',
    'overlay_allowed': False, 'aggregation_allowed': False,
    'unknown_conditions_equivalent': False, 'ranking_allowed': False,
    'quantitative_axes_allowed': False, 'uncertainty_endpoints_calculated': False,
    'thickness_conversion_allowed': False, 'formula_execution_allowed': False,
    'evaluation_support': 'catalog_only', 'quantities_remain_distinct': True,
    'associated_study_summaries_are_independent_replications': False,
    'snapshot_digests_identify': 'bundled_catalog_metadata_not_original_source_artifact_bytes',
    'csv_missing_scalar': 'null',
}


class ObservationInspectionError(ValidationError):
    """An inspection selection or bundle is invalid, altered, or stale."""


def _require(condition, message):
    if not condition:
        raise ObservationInspectionError(message)


def _json_safe(value):
    if type(value) is str:
        _require(all(ord(c) in (9, 10, 13) or 0x20 <= ord(c) <= 0xD7FF
                     or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF
                     for c in value), 'XML-illegal character in inspection text')
        return
    if value is None or type(value) in (bool, int):
        return
    if type(value) is float:
        _require(math.isfinite(value), 'nonfinite JSON number')
        return
    if type(value) is list:
        for item in value:
            _json_safe(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            _require(type(key) is str, 'JSON object keys must be strings')
            _json_safe(key)
            _json_safe(item)
        return
    raise ObservationInspectionError('non-JSON value in inspection')


def _canonical(value, pretty=False):
    _json_safe(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      indent=2 if pretty else None,
                      separators=None if pretty else (',', ':'))


def _digest(value):
    return hashlib.sha256(_canonical(value).encode('utf-8')).hexdigest()


def labels(lang='en'):
    from ._observation_inspection_labels import LABELS
    _require(type(lang) is str and lang in LABELS, 'unsupported inspection language')
    return {**LABELS[lang], **PAHT_LABELS[lang]}


def _selector(value, name):
    _require(type(value) is str and bool(value) and value == value.strip()
             and not any(ord(c) < 32 or ord(c) == 127 for c in value),
             name + ' must be a nonempty exact string without control characters')


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
        raise ObservationInspectionError('invalid source URL') from exc
    return value


def _validate_links(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('source_url', 'url', 'license_url', 'version_notes_url', 'doi_url', 'publisher_url') and item is not None:
                _safe_url(item)
            elif key == 'urls':
                for url in item:
                    _safe_url(url)
            else:
                _validate_links(item)
    elif isinstance(value, list):
        for item in value:
            _validate_links(item)


def _family(record):
    # validate_observation_records has already admitted the explicit family or
    # the source-specific legacy Lee shape. Never infer a family from its name.
    return record.get('method_family', LEE_FAMILY)


def _validate_source_display(record):
    family = _family(record)
    if family not in (LEE_FAMILY, MOS2_FAMILY):
        return
    # Existing catalog readers admit the legacy/partly constrained branches;
    # this view additionally closes the source semantics its labels rely on.
    # A newly reviewed scientific payload needs a new explicit family rather
    # than inheriting Lee's uncertainty, count or stress/strain conventions.
    payload = deepcopy({key: value for key, value in record.items() if key not in ('id', 'name')})
    payload['evidence'] = sorted(payload['evidence'], key=_canonical)
    expected = LEE_SCIENTIFIC_PAYLOAD_SHA256 if family == LEE_FAMILY else MOS2_SCIENTIFIC_PAYLOAD_SHA256
    _require(_digest(payload) == expected.get(record['quantity']),
             'source-defined scientific observation payload changed')


def _caveats(record):
    family, quantity = _family(record), record['quantity']
    if family == MOS2_FAMILY:
        return ['mos2_warning', 'catalog_mos2_source_notice', 'sd_warning']
    if family == HBN_FAMILY:
        return [('hbn_strength_warning' if quantity == QUANTITIES[1]
                 else 'hbn_stiffness_warning'), 'catalog_hbn_sd_notice', 'sd_warning']
    if family == PA12_FAMILY:
        return list(PA12_CAVEATS)
    if family == PAHT_FAMILY:
        return list(PAHT_CAVEATS)
    if family == LEE_FAMILY:
        return ['graphene_warning']
    raise ObservationInspectionError('unsupported observation method family')


def _caveat_text(code, lang):
    return translate(code, lang) if code.startswith('catalog_') else labels(lang)[code]


def _number(value):
    _require(type(value) in (int, float), 'reported values must be numbers, not Boolean')
    try:
        _require(math.isfinite(value), 'reported values must be finite')
    except OverflowError as exc:
        raise ObservationInspectionError('reported number outside finite range') from exc
    # Python's round-trip spelling retains the stored precision, including 23.6
    # and 1.8. No fixed decimals, endpoint calculation or thickness conversion.
    return str(value)


def _membrane_facet(r):
    _require(r['quantity'] in QUANTITIES[:2] and r['si_unit'] == 'N/m'
             and r['quantity_dimension'] == 'force_per_length'
             and r['observation_type'] == 'experiment_derived_model_dependent'
             and r['evaluation_support'] == 'catalog_only', 'unsupported scientific observation contract')
    result, uncertainty = r['reported_result'], r['reported_result']['uncertainty']
    _require(result['unit'] == uncertainty['unit'] == 'N/m', 'unsupported observation unit')
    _require(uncertainty['notation'] == 'plus_minus', 'unsupported uncertainty notation')
    expected = 'reported_plus_minus_unspecified' if _family(r) == LEE_FAMILY else 'reported_standard_deviation'
    _require(uncertainty['type'] == expected, 'source-specific uncertainty type changed')
    central, spread = _number(result['value']), _number(uncertainty['value'])
    _require(result['value'] > 0 and uncertainty['value'] >= 0, 'invalid reported value range')
    return {'id': 'observation-' + _digest([r['study_id'], r['quantity'], r['id']]),
           'record_id': r['id'], 'record_version': r['version'],
           'study_id': r['study_id'], 'quantity': r['quantity'],
           'method_family': _family(r), 'unit': 'N/m',
           'normalized_display': central + ' ± ' + spread + ' N/m',
           'display_basis': DISPLAY_BASIS, 'required_caveat_codes': _caveats(r),
           'uncertainty_type': uncertainty['type']}


def _pa12_facet(r):
    """A separate pressure-valued branch; no membrane shape or unit fallback."""
    _require(_family(r) == PA12_FAMILY and r['quantity'] == QUANTITIES[2]
             and r['quantity_dimension'] == 'pressure' and r['si_unit'] == 'Pa'
             and r['observation_type'] == 'experiment_derived_tensile_test_summary'
             and r['evaluation_support'] == 'catalog_only', 'unsupported tensile observation contract')
    result, u, si = r['reported_result'], r['reported_result']['uncertainty'], r['si_result']
    _require(result['unit'] == u['unit'] == 'MPa' and si['unit'] == 'Pa', 'unsupported tensile unit')
    # Exact strings and SI scaling were admitted by the source-specific guard.
    # The view does not calculate a material property or uncertainty endpoints.
    return {'id': 'observation-' + _digest([r['study_id'], r['quantity'], r['id']]),
            'record_id': r['id'], 'record_version': r['version'], 'study_id': r['study_id'],
            'quantity': r['quantity'], 'quantity_dimension': r['quantity_dimension'],
            'method_family': PA12_FAMILY, 'observation_type': r['observation_type'],
            'model_status': r['model_status'], 'dataset_id': r['dataset_id'],
            'protocol_id': r['protocol_id'], 'source_cell': deepcopy(r['source_cell']),
            'temperature': deepcopy(r['conditions']['temperature']),
            'temperature_basis': r['conditions']['temperature']['basis'],
            'unit': 'MPa', 'si_unit': 'Pa',
            'reported_value_string': result['value_string'],
            'reported_plus_minus_string': u['value_string'],
            'normalized_display': result['value_string'] + ' ± ' + u['value_string'] + ' MPa',
            'display_basis': PA12_DISPLAY_BASIS,
            'si_display': str(int(si['value'])) + ' ± ' + str(int(si['uncertainty_value'])) + ' Pa',
            'si_value': int(si['value']), 'si_uncertainty_value': int(si['uncertainty_value']),
            'normalization': deepcopy(si['normalization']),
            'required_caveat_codes': _caveats(r), 'uncertainty_type': u['type']}


def _paht_facet(r):
    """Source-specific median and separate SD; no plus/minus interpretation."""
    _require(_family(r) == PAHT_FAMILY and r['quantity'] == QUANTITIES[2]
             and r['quantity_dimension'] == 'pressure' and r['si_unit'] == 'Pa'
             and r['observation_type'] == 'experiment_derived_tensile_test_summary'
             and r['evaluation_support'] == 'catalog_only', 'unsupported PAHT tensile contract')
    result, u, si = r['reported_result'], r['reported_result']['uncertainty'], r['si_result']
    _require(result['summary_statistic'] == 'median_as_reported'
             and u['notation'] == 'separate_sd'
             and result['unit'] == u['unit'] == 'MPa' and si['unit'] == si['uncertainty_unit'] == 'Pa'
             and u['unit_basis'] == 'contextual_inference_from_associated_uts_column'
             and u['header_unit_explicit'] is False
             and si['uncertainty_unit_basis'] == 'conditional_on_contextual_MPa_inference',
             'unsupported PAHT median/SD or unit semantics')
    return {'id': 'observation-' + _digest([r['study_id'], r['quantity'], r['id']]),
            'record_id': r['id'], 'record_version': r['version'], 'study_id': r['study_id'],
            'quantity': r['quantity'], 'quantity_dimension': r['quantity_dimension'],
            'method_family': PAHT_FAMILY, 'observation_type': r['observation_type'],
            'model_status': r['model_status'], 'dataset_id': r['dataset_id'],
            'protocol_id': r['protocol_id'], 'source_cell': deepcopy(r['source_cell']),
            'temperature': deepcopy(r['conditions']['temperature']),
            'temperature_basis': r['conditions']['temperature']['basis'],
            'unit': 'MPa', 'si_unit': 'Pa', 'summary_statistic': result['summary_statistic'],
            'reported_median_string': result['value_string'], 'reported_sd_string': u['value_string'],
            'normalized_display': 'Median: ' + result['value_string'] + ' MPa; SD: '
                + u['value_string'] + ' MPa (unit contextually inferred)',
            'display_basis': PAHT_DISPLAY_BASIS,
            'si_display': 'Median: ' + str(int(si['value'])) + ' Pa; SD: '
                + str(int(si['uncertainty_value'])) + ' Pa (source unit contextually inferred)',
            'si_value': int(si['value']), 'si_sd_value': int(si['uncertainty_value']),
            'normalization': deepcopy(si['normalization']),
            'required_caveat_codes': _caveats(r), 'uncertainty_type': u['type'],
            'uncertainty_notation': u['notation'], 'sd_unit': u['unit'],
            'sd_unit_basis': u['unit_basis'], 'sd_header_unit_explicit': u['header_unit_explicit'],
            'si_sd_unit': si['uncertainty_unit'], 'si_sd_unit_basis': si['uncertainty_unit_basis']}


def _paht_identity_lines(record, lang):
    t = labels(lang)
    return [t['paht_identity'] + ' | ' + record['material']['name'],
            t['paht_dataset'] + ': ' + record['dataset_id'],
            t['paht_protocol'] + ': ' + record['protocol_id'],
            t['paht_temperature'] + ': ' + record['conditions']['temperature']['value_string'] + ' °C',
            t['paht_temperature_basis']]


def _paht_detail_lines(record, lang):
    """All original structured conditions and SD-unit provenance stay visible."""
    t = labels(lang)
    lines = [(t['paht_cell'] + ': ' + _canonical(record['source_cell']), None)]
    for key, label in (('material', 'paht_material'), ('method', 'paht_method'),
                       ('conditions', 'paht_conditions'), ('sample_metadata', 'paht_counts'),
                       ('reported_result', 'paht_reported_display'), ('si_result', 'paht_si_display'),
                       ('verification', 'paht_source_version'), ('limits', 'paht_details')):
        lines.append((t[label], None))
        value = record[key]
        if isinstance(value, dict):
            lines.extend((field + ': ' + _canonical(item), None) for field, item in value.items())
        else:
            lines.append((_canonical(value), None))
    url = record['verification']['rights']['license_url']
    lines.append((url, url))
    return lines


def _classification(record, lang):
    key = {PA12_FAMILY: 'pa12_classification', PAHT_FAMILY: 'paht_classification'}.get(_family(record), 'classification')
    return labels(lang)[key]


def _pa12_identity_lines(record, lang):
    t = labels(lang)
    return [t['pa12_identity'] + ' | ' + record['material']['name'],
            t['pa12_dataset'] + ': ' + record['dataset_id'],
            t['pa12_protocol'] + ': ' + record['protocol_id'],
            t['pa12_temperature'] + ': ' + record['conditions']['temperature']['value_string'] + ' °C',
            t['pa12_temperature_basis']]


def _pa12_detail_lines(record, lang):
    """Complete protocol context stays visible, including unknown/null states."""
    t = labels(lang)
    lines = [(t['source_wording'] + ': ' + record['reported_result']['source_value_string'] + ' MPa', None),
             (t['pa12_cell'] + ': ' + _canonical(record['source_cell']), None)]
    for key, label in (('material', 'pa12_material'), ('method', 'pa12_method'),
                       ('conditions', 'pa12_conditions'), ('sample_metadata', 'pa12_counts')):
        # Render each top-level structured component separately for wrapping;
        # none is hidden behind the full-snapshot disclosure control.
        lines.append((t[label], None))
        for field, value in record[key].items():
            lines.append((field + ': ' + _canonical(value), None))
    lines.append((t['pa12_standard_warning'], None))
    lines.append((t['pa12_version_warning'], None))
    lines.append((t['pa12_source_version'] + ': ' + _canonical(record['verification']['source_inspection']), None))
    lines.extend((gap, None) for gap in record['verification']['gaps'])
    lines.append((t['pa12_rights_warning'], None))
    rights = record['verification']['rights']
    lines.append((t['rights'] + ': ' + _canonical(rights), None))
    lines.append((rights['license_url'], rights['license_url']))
    return lines


def build_observation_inspection(record_ids=None, source_id=None, quantity=None, group_by='study'):
    """Select exact records in packaged order; filters combine with AND."""
    from . import __version__
    _require(type(group_by) is str and group_by in ('study', 'quantity'), 'unknown grouping')
    if record_ids is not None:
        _require(type(record_ids) in (list, tuple) and bool(record_ids), 'record_ids must be a nonempty list or tuple')
        for rid in record_ids:
            _selector(rid, 'record ID')
        _require(len(set(record_ids)) == len(record_ids), 'duplicate record IDs')
    for name, value in (('source ID', source_id), ('quantity', quantity)):
        if value is not None:
            _selector(value, name)
    _require(quantity is None or quantity in QUANTITIES, 'unsupported observation quantity')
    try:
        catalog, source_catalog = read_catalog('observations'), read_catalog('sources')
        _require(catalog['schema_version'] == '1.3.0' and source_catalog['schema_version'] == '1.0.0',
                 'unsupported observation/source catalog schema version')
        validate_observation_records(catalog['records'])
        validate_pa12_sources(source_catalog['records'])
        validate_paht_sources(source_catalog['records'])
        _json_safe(catalog); _json_safe(source_catalog)
        records, sources = catalog['records'], source_catalog['records']
        all_ids = [r['id'] for r in records]
        source_ids = [s['id'] for s in sources]
        _require(len(all_ids) == len(set(all_ids)), 'duplicate packaged observation IDs')
        _require(len(source_ids) == len(set(source_ids)), 'duplicate packaged source IDs')
        for rid in record_ids or ():
            _require(rid in all_ids, 'unknown observation ID: ' + rid)
        _require(source_id is None or source_id in source_ids, 'unknown observation source ID')
        selected = [r for r in records if (record_ids is None or r['id'] in record_ids)
                    and (source_id is None or any(e['source_id'] == source_id for e in r['evidence']))
                    and (quantity is None or r['quantity'] == quantity)]
        _require(bool(selected), 'observation inspection selection is empty')
        referenced = set()
        facets = []
        for r in selected:
            _validate_source_display(r)
            for key in ('id', 'study_id', 'version'):
                _selector(r[key], key)
            referenced.add(r['study_id'])
            referenced.update(e['source_id'] for e in r['evidence'])
            builder = {PA12_FAMILY: _pa12_facet, PAHT_FAMILY: _paht_facet}.get(_family(r), _membrane_facet)
            facets.append(builder(r))
        _require(referenced.issubset(source_ids), 'missing referenced observation source')
        selected_sources = [s for s in sources if s['id'] in referenced]
        _validate_links(selected); _validate_links(selected_sources)
        groups = []
        group_values = list(dict.fromkeys(f['study_id' if group_by == 'study' else 'quantity'] for f in facets))
        for identity in group_values:
            groups.append({'id': group_by + ':' + identity, 'kind': group_by, 'identity': identity,
                           'facet_ids': [f['id'] for f in facets if f['study_id' if group_by == 'study' else 'quantity'] == identity]})
        return {'schema_version': '1.1.0', 'kind': 'observation_inspection', 'engine_version': __version__,
                'catalog_schema_versions': {'observations': catalog['schema_version'], 'sources': source_catalog['schema_version']},
                'selection': {'requested_record_ids': None if record_ids is None else list(record_ids),
                              'source_id': source_id, 'quantity': quantity,
                              'resolved_record_ids': [r['id'] for r in selected]},
                'group_by': group_by, 'groups': groups, 'facets': facets,
                'record_snapshots': deepcopy(selected), 'source_snapshots': deepcopy(selected_sources),
                'record_digests': [{'record_id': r['id'], 'record_version': r['version'], 'sha256': _digest(r)} for r in selected],
                'source_digests': [{'source_id': s['id'], 'sha256': _digest(s)} for s in selected_sources],
                'presentation_policy': deepcopy(POLICY)}
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ObservationInspectionError('invalid observation inspection: ' + str(exc)) from exc


def validate_observation_inspection(bundle):
    """Reject all altered/stale fields, including extras, by canonical rebuild."""
    try:
        _require(type(bundle) is dict, 'inspection must be an object')
        _json_safe(bundle)
        selection = bundle['selection']
        rebuilt = build_observation_inspection(selection['requested_record_ids'],
            selection['source_id'], selection['quantity'], bundle['group_by'])
        _require(_canonical(bundle) == _canonical(rebuilt),
                 'noncanonical or stale inspection; regenerate from packaged catalogs')
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ObservationInspectionError('invalid observation inspection: ' + str(exc)) from exc


def inspection_json(bundle):
    validate_observation_inspection(bundle)
    return _canonical(bundle, pretty=True) + '\n'


def _uncertainty_evidence(record):
    uncertainty = record['reported_result']['uncertainty']
    # MoS2's property SD sentence is located by its own value evidence. Lee's
    # absent definition remains absent, never borrowed from another source.
    if _family(record) == LEE_FAMILY:
        return None
    return uncertainty.get('evidence', record['evidence'][0])


def inspection_csv(bundle):
    """One row per selected record; identities and caveats precede values.

    Result columns retain reported units. Separate SI columns are exact prefix
    scaling for PA12 and PAHT, and identity normalization for historic N/m records.
    PAHT adds separate median/SD columns only when selected; its SD-to-Pa
    scaling is conditional on the explicitly retained inferred source unit.
    Missing scalars remain literal ``null``; snapshots retain complete types.
    """
    validate_observation_inspection(bundle)
    columns = ['record_id', 'record_version', 'study_id', 'quantity', 'unit',
        'classification', 'evaluation_support', 'method_family', 'model_status',
        'dataset_id', 'protocol_id', 'source_cell_json', 'temperature_value',
        'temperature_value_string', 'temperature_unit', 'temperature_basis',
        'temperature_json', 'required_caveat_codes_json', 'essential_caveats',
        'presentation_policy_json', 'normalized_display_basis', 'normalized_display',
        'central_value', 'plus_minus_value', 'reported_value_string',
        'reported_plus_minus_string', 'si_unit', 'si_central_value', 'si_plus_minus_value',
        'normalization_json', 'uncertainty_type', 'uncertainty_interpretation',
        'uncertainty_evidence_json', 'summary_statistic', 'source_value_string',
        'sample_metadata_json', 'conditions_json', 'method_json', 'evidence_json',
        'verification_json', 'engine_version', 'inspection_schema_version',
        'observation_schema_version', 'source_schema_version', 'record_snapshot_sha256',
        'source_snapshot_digests_json', 'selection_json', 'group_by',
        'scalar_missing_convention', 'record_snapshot_json', 'source_snapshots_json']
    has_paht = any(_family(r) == PAHT_FAMILY for r in bundle['record_snapshots'])
    if has_paht:
        before = columns.index('normalized_display_basis')
        columns[before:before] = ['uncertainty_notation', 'sd_unit', 'sd_unit_basis',
            'sd_header_unit_explicit', 'si_sd_unit', 'si_sd_unit_basis']
        before = columns.index('central_value')
        columns[before:before] = ['median_value', 'reported_median_string', 'sd_value',
            'reported_sd_string', 'si_median_value', 'si_sd_value']
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    digests = {d['record_id']: d['sha256'] for d in bundle['record_digests']}
    for r, f in zip(bundle['record_snapshots'], bundle['facets']):
        result, u = r['reported_result'], r['reported_result']['uncertainty']
        ids = {r['study_id'], *(e['source_id'] for e in r['evidence'])}
        paht = _family(r) == PAHT_FAMILY
        tensile = _family(r) in (PA12_FAMILY, PAHT_FAMILY)
        temperature = r['conditions']['temperature'] if tensile else None
        si = r['si_result'] if tensile else {'value': result['value'],
            'uncertainty_value': u['value'], 'unit': 'N/m',
            'normalization': {'kind': 'identity_no_unit_conversion', 'from_unit': 'N/m',
                              'to_unit': 'N/m', 'factor_string': '1', 'offset_string': '0',
                              'adds_measurement_precision': False}}
        row = dict(record_id=r['id'], record_version=r['version'], study_id=r['study_id'],
            quantity=r['quantity'], unit=result['unit'], classification=r['observation_type'],
            evaluation_support=r['evaluation_support'], method_family=f['method_family'],
            model_status=r.get('model_status', 'source_reported_model_dependent'),
            dataset_id=r.get('dataset_id', 'null'), protocol_id=r.get('protocol_id', 'null'),
            source_cell_json=_canonical(r.get('source_cell')),
            temperature_value=temperature['value_string'] if tensile else 'null',
            temperature_value_string=temperature['value_string'] if tensile else 'null',
            temperature_unit=temperature['unit'] if tensile else 'null',
            temperature_basis=temperature['basis'] if tensile else 'null',
            temperature_json=_canonical(temperature),
            required_caveat_codes_json=_canonical(f['required_caveat_codes']),
            essential_caveats=' '.join(_caveat_text(c, 'en') for c in f['required_caveat_codes']),
            presentation_policy_json=_canonical(bundle['presentation_policy']),
            normalized_display_basis=f['display_basis'], normalized_display=f['normalized_display'],
            central_value=_number(result['value']), plus_minus_value=_number(u['value']),
            reported_value_string=result.get('value_string', 'null'),
            reported_plus_minus_string=u.get('value_string', 'null'), si_unit=si['unit'],
            si_central_value=str(int(si['value'])) if tensile else _number(si['value']),
            si_plus_minus_value=str(int(si['uncertainty_value'])) if tensile else _number(si['uncertainty_value']),
            normalization_json=_canonical(si['normalization']), uncertainty_type=u['type'],
            uncertainty_interpretation=u['interpretation'],
            uncertainty_evidence_json=_canonical(_uncertainty_evidence(r)),
            summary_statistic=result.get('summary_statistic', 'null'),
            source_value_string=result.get('source_value_string', 'null'),
            sample_metadata_json=_canonical(r['sample_metadata']), conditions_json=_canonical(r['conditions']),
            method_json=_canonical(r['method']), evidence_json=_canonical(r['evidence']),
            verification_json=_canonical(r['verification']), engine_version=bundle['engine_version'],
            inspection_schema_version=bundle['schema_version'],
            observation_schema_version=bundle['catalog_schema_versions']['observations'],
            source_schema_version=bundle['catalog_schema_versions']['sources'],
            record_snapshot_sha256=digests[r['id']],
            source_snapshot_digests_json=_canonical([d for d in bundle['source_digests'] if d['source_id'] in ids]),
            selection_json=_canonical(bundle['selection']), group_by=bundle['group_by'],
            scalar_missing_convention='null', record_snapshot_json=_canonical(r),
            source_snapshots_json=_canonical([s for s in bundle['source_snapshots'] if s['id'] in ids]))
        if has_paht:
            row.update(uncertainty_notation=u['notation'], sd_unit=u['unit'] if paht else 'null',
                sd_unit_basis=u['unit_basis'] if paht else 'null',
                sd_header_unit_explicit='false' if paht else 'null',
                si_sd_unit=si['uncertainty_unit'] if paht else 'null',
                si_sd_unit_basis=si['uncertainty_unit_basis'] if paht else 'null',
                median_value=_number(result['value']) if paht else 'null',
                reported_median_string=result['value_string'] if paht else 'null',
                sd_value=_number(u['value']) if paht else 'null',
                reported_sd_string=u['value_string'] if paht else 'null',
                si_median_value=str(int(si['value'])) if paht else 'null',
                si_sd_value=str(int(si['uncertainty_value'])) if paht else 'null')
        if paht:
            # A separate SD must never acquire an inherited ± column meaning.
            row.update(plus_minus_value='null', reported_plus_minus_string='null',
                       si_plus_minus_value='null')
        writer.writerow(row)
    return out.getvalue()


def _status(value, lang):
    if value is None:
        return labels(lang)['unknown']
    key = 'catalog_status_' + value
    translated = translate(key, lang)
    return value if translated == '[missing:' + key + ']' else translated + ' [' + value + ']'


def _detail_lines(record, lang):
    """Visible scientific context, not raw-JSON-only warnings."""
    if _family(record) == PA12_FAMILY:
        return _pa12_detail_lines(record, lang)
    if _family(record) == PAHT_FAMILY:
        return _paht_detail_lines(record, lang)
    t = labels(lang)
    c = lambda key: translate('catalog_' + key, lang)
    family = _family(record)
    result, method = record['reported_result'], record['method']
    u, sample, conditions = result['uncertainty'], record['sample_metadata'], record['conditions']
    lines = []
    def field(label, value):
        lines.append((label + ': ' + str(value), None))
    def notice(key):
        lines.append((translate(key, lang), None))
    field(t['uncertainty'], _status(u['type'], lang))
    lines.append((u['interpretation'], None))
    field(t['statistic'], _status(result.get('summary_statistic'), lang))
    if family == HBN_FAMILY and record['quantity'] == QUANTITIES[1]:
        field(c('hbn_central_statistic'), t['statistic_unknown'])
    field(c('coverage_factor'), t['unknown'])
    field(c('confidence_level'), t['unknown'])
    field(c('averaging_convention'), t['unknown'])
    field(t['model'], method['inference'])
    field(c('poissons_ratio_assumed'), method['poissons_ratio_assumed'])
    for assumption in method['model_assumptions']:
        field(c('model_assumptions'), assumption)
    field(c('stress_measure'), _status(method['stress_measure'], lang))
    field(c('strain_measure'), _status(method['strain_measure'], lang))
    if family == MOS2_FAMILY:
        q = method['q_source_report']
        for label, key in [('q_formula', 'formula_as_printed'), ('q_nu', 'nu_as_printed'),
                           ('q_reported', 'q_as_printed'), ('q_arithmetic', 'audit_arithmetic_value')]:
            field(c(label), q[key])
        field(c('q_used'), t['unknown'])
        field(c('locator'), q['locator'])
        notice('catalog_geometry_uncertainty_notice')
        field(c('preparation_notes'), record['material']['preparation_notes'])
    elif family == HBN_FAMILY:
        notice('catalog_hbn_diagnostic_notice' if record['quantity'] == QUANTITIES[1] else 'catalog_hbn_q_notice')
        if record['quantity'] == QUANTITIES[0]:
            field(c('q_formula'), method['q_source_report']['formula_as_printed'])
            field(c('q_used'), t['unknown'])
            field(c('locator'), method['fit_force_law']['source_locator'])
        notice('catalog_hbn_stress_strain_notice')
        notice('catalog_hbn_thickness_notice')
        if record['quantity'] == QUANTITIES[1]:
            notice('catalog_hbn_fem_input_notice')
            fem = method['finite_element_model']
            for label, key in (('hbn_fem_depth', 'applied_indentation_depth'),
                               ('hbn_fem_increment', 'displacement_increment')):
                setting = fem[key]
                field(c(label), str(setting['value']) + ' ' + setting['unit'] + ' | ' + setting['role'])
    field(t['sample'], t['unknown'] if sample is None else _status(sample['scope'], lang))
    if sample is not None:
        count_labels = {'force_displacement_fits': 'fit_count', 'membranes': 'membrane_count', 'flakes': 'flake_count',
            'study_monolayer_membranes': 'study_monolayer_count', 'force_displacement_curves': 'curve_count',
            'distinct_parent_flakes': 'parent_flake_count', 'failure_events': 'failure_count',
            'membranes_explicitly_associated_with_stiffness_average': 'stiffness_membrane_count',
            'study_monolayer_tested_sheets': 'hbn_tested_sheet_count',
            'force_displacement_curves_acquired': 'hbn_acquired_curve_count',
            'force_displacement_curves_retained': 'hbn_retained_curve_count',
            'force_displacement_curves_excluded': 'hbn_excluded_curve_count',
            'tested_sheets_explicitly_associated_with_stiffness_average': 'hbn_stiffness_sheet_count'}
        for key, value in sample['counts'].items():
            field(c(count_labels[key]), t['unknown'] if value is None else value)
        if family == LEE_FAMILY:
            distribution = sample['fitted_distribution']
            field(c('distribution_mean'), str(distribution['mean']) + ' N/m')
            field(c('distribution_sd'), str(distribution['standard_deviation']) + ' N/m')
        if family == HBN_FAMILY:
            notice('catalog_hbn_count_notice')
        lines.extend((note, None) for note in sample['notes'])
    for key in ('temperature', 'atmosphere', 'humidity'):
        field(c(key), t['unknown'] if conditions[key] is None else _canonical(conditions[key]))
    if 'pressure' in conditions:
        field(c('pressure'), t['unknown'] if conditions['pressure'] is None else _canonical(conditions['pressure']))
    rate = conditions['loading_rate']
    field(c('loading_rate'), t['unknown'] if rate is None else str(rate['value']) + ' ' + rate['unit'] + ' [' + rate['quantity'] + ']')
    if family == MOS2_FAMILY:
        notice('catalog_probe_speed_notice')
    elif family == HBN_FAMILY:
        field(c('hbn_environment'), conditions['environment_description'])
        notice('catalog_hbn_conditions_notice'); notice('catalog_hbn_velocity_notice')
    lines.extend((note, None) for note in conditions.get('notes', []))
    field(t['verification'], _status(record['verification']['status'], lang))
    lines.extend((gap, None) for gap in record['verification']['gaps'])
    if family == MOS2_FAMILY:
        notice('catalog_mos2_transcription_notice')
    elif family == HBN_FAMILY:
        notice('catalog_hbn_inspection_notice')
    field(t['source_wording'], result.get('source_value_string', t['source_wording_absent']))
    lines.append((t['original_context'], None))
    return lines


def _evidence_lines(record, source, lang):
    t = labels(lang)
    lines = []
    evidence = [(t['evidence'], e) for e in record['evidence']]
    if _family(record) == PAHT_FAMILY:
        evidence.append((t['statistic'], record['reported_result']['statistic_evidence']))
    uncertainty = _uncertainty_evidence(record)
    if uncertainty is not None:
        evidence.append((t['uncertainty_evidence'], uncertainty))
    else:
        lines.append((t['uncertainty_evidence'] + ': ' + t['unknown'], None))
    sample = record['sample_metadata']
    if sample and 'count_definition_source' in sample:
        count_key = {PA12_FAMILY: 'pa12_counts', PAHT_FAMILY: 'paht_counts'}.get(_family(record))
        count_label = labels(lang)[count_key] if count_key else translate('catalog_hbn_count_evidence', lang)
        evidence.append((count_label, sample['count_definition_source']))
    for label, ev in evidence:
        artifact = ev.get('artifact', record['verification'].get('source_inspection', {}).get('artifact', source['read_status']))
        url = ev.get('source_url')
        # Lee evidence lacks a component URL; retain that absence and offer
        # source-record links separately, without pretending they identify it.
        lines.append((label + ' | ' + ev['source_id'] + ' | ' + artifact + ' | ' + ev['locator'], url))
        lines.append((ev['verified_as'] + ' [' + ev['verification_status'] + ']', None))
    return lines


def _glyph_units(char):
    if unicodedata.combining(char):
        return 0
    if unicodedata.east_asian_width(char) in 'WF':
        return 2
    if char in 'MW@%&':
        return 1.8
    if char in 'mw':
        return 1.6
    if char.isupper():
        return 1.4
    return 1


def _wrapped(value, columns):
    """Conservative glyph-aware wrap, including unbroken IDs/URLs and CJK."""
    lines, line, units = [], '', 0
    for word in str(value).split(' '):
        weight = sum(_glyph_units(c) for c in word)
        if line and weight <= columns and units + 1 + weight > columns:
            lines.append(line); line = ''; units = 0
        for char in (' ' if line else '') + word:
            step = _glyph_units(char)
            if units + step > columns:
                lines.append(line); line = ''; units = 0
            line += char; units += step
    if line:
        lines.append(line)
    return lines


def _ordered_groups(bundle):
    facets = {f['id']: f for f in bundle['facets']}
    records = {r['id']: r for r in bundle['record_snapshots']}
    for group in bundle['groups']:
        yield group, [(facets[fid], records[facets[fid]['record_id']]) for fid in group['facet_ids']]


def render_observation_svg(bundle, lang='en', width=1100):
    validate_observation_inspection(bundle)
    t = labels(lang)
    _require(type(width) is int and 320 <= width <= 1600, 'SVG width must be an integer in [320,1600]')
    sources = {s['id']: s for s in bundle['source_snapshots']}
    elements = []
    margin = 20 if width >= 700 else 14
    def para(value, x, y, available, size=13, color='#20374a', bold=False, url=None):
        # A deliberately conservative width protects long German words and
        # fallback CJK fonts; layout depends on text, never property magnitude.
        lines = _wrapped(value, max(12, int(available / (size * .68))))
        for line in lines:
            text = f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{color}"' + (' font-weight="700"' if bold else '') + '>' + escape(line) + '</text>'
            if url:
                text = '<a href="' + escape(_safe_url(url), quote=True) + '">' + text + '</a>'
            elements.append(text)
            y += size * 1.55
        return y + 9
    y = para('MATERIALS BOUNDARIES · v' + bundle['engine_version'], margin, 27, width-2*margin, 11)
    y = para(t['title'], margin, y, width-2*margin, 25, bold=True)
    for key in ('subtitle', 'policy', 'translation_notice'):
        y = para(t[key], margin, y, width-2*margin)
    for group, pairs in _ordered_groups(bundle):
        heading = sources[group['identity']]['title'] if group['kind'] == 'study' else t[QUANTITY_LABELS[group['identity']]]
        y = para(t['group_' + group['kind']] + ': ' + heading, margin, y+15, width-2*margin, 18, bold=True)
        columns = 2 if width >= 900 else 1
        gap = 18
        card_width = (width - 2*margin - gap*(columns-1)) / columns
        for row in range(0, len(pairs), columns):
            bottoms = []
            for col, (facet, record) in enumerate(pairs[row:row+columns]):
                x = margin + col*(card_width+gap)
                source = sources[record['study_id']]
                start = len(elements)
                cy = y + 25
                cx, space = x+15, card_width-30
                cy = para(t[QUANTITY_LABELS[record['quantity']]], cx, cy, space, 18, bold=True)
                for identity in (record['name'], t['record'] + ': ' + record['id'],
                                 t['record_version'] + ': ' + record['version'],
                                 t['study'] + ': ' + record['study_id'], _classification(record, lang)):
                    cy = para(identity, cx, cy, space, 12)
                if _family(record) == PA12_FAMILY:
                    for identity in _pa12_identity_lines(record, lang):
                        cy = para(identity, cx, cy, space, 12)
                if _family(record) == PAHT_FAMILY:
                    for identity in _paht_identity_lines(record, lang):
                        cy = para(identity, cx, cy, space, 12)
                cy = para(t['primary_warning'], cx, cy, space, 13, '#744000', True)
                for code in facet['required_caveat_codes']:
                    cy = para(_caveat_text(code, lang), cx, cy, space, 13, '#744000')
                if _family(record) == PAHT_FAMILY:
                    cy = para(t['paht_reported_display'], cx, cy, space, 13, bold=True)
                    cy = para(t['paht_reported_notice'], cx, cy, space, 12)
                    cy = para(t['paht_reported_median'] + ': ' + facet['reported_median_string'] + ' MPa', cx, cy, space, 23, bold=True)
                    cy = para(t['paht_reported_sd'] + ': ' + facet['reported_sd_string'] + ' MPa', cx, cy, space, 18, bold=True)
                    cy = para(t['paht_si_display'], cx, cy, space, 13, bold=True)
                    cy = para(t['paht_si_notice'], cx, cy, space, 12)
                    cy = para(t['paht_si_median'] + ': ' + str(facet['si_value']) + ' Pa', cx, cy, space, 18, bold=True)
                    cy = para(t['paht_si_sd'] + ': ' + str(facet['si_sd_value']) + ' Pa', cx, cy, space, 18, bold=True)
                else:
                    tensile = _family(record) == PA12_FAMILY
                    cy = para(t['pa12_reported_display' if tensile else 'normalized'], cx, cy, space, 13, bold=True)
                    cy = para(t['pa12_reported_notice' if tensile else 'normalized_notice'], cx, cy, space, 12)
                    cy = para(facet['normalized_display'], cx, cy, space, 23, bold=True)
                    if tensile:
                        cy = para(t['pa12_si_display'], cx, cy, space, 13, bold=True)
                        cy = para(t['pa12_si_notice'], cx, cy, space, 12)
                        cy = para(facet['si_display'], cx, cy, space, 18, bold=True)
                for value, url in _detail_lines(record, lang) + _evidence_lines(record, source, lang):
                    cy = para(value, cx, cy, space, 12, url=url)
                cy = para(t['digest'] + ': ' + _digest(record), cx, cy, space, 10)
                cy += 10
                elements.insert(start, f'<rect x="{x:g}" y="{y:g}" width="{card_width:g}" height="{cy-y:g}" rx="9" fill="white" stroke="#b9cbd6"/>')
                # Identity is escaped even though the stable DOM ID is a hash.
                elements.insert(start, '<g id="' + facet['id'] + '" data-record-id="' + escape(record['id'], quote=True) + '">')
                elements.append('</g>')
                bottoms.append(cy)
            y = max(bottoms) + 22
    y = para(t['source_links'], margin, y+10, width-2*margin, 20, bold=True)
    for source in bundle['source_snapshots']:
        y = para(source['id'] + ' | ' + source['title'], margin, y, width-2*margin, 14, bold=True)
        y = para(t['rights'] + ': ' + _canonical(source['license']), margin, y, width-2*margin, 12)
        if source['id'] == 'falin_et_al_2017_hbn_mechanical_properties':
            y = para(translate('catalog_hbn_rights_notice', lang), margin, y, width-2*margin, 12)
        for url in source['urls']:
            y = para(url, margin, y, width-2*margin, 11, url=url)
        y = para(t['digest'] + ': ' + _digest(source), margin, y, width-2*margin, 11)
    for key in ('snapshot_notice', 'rights_notice', 'no_comparison'):
        y = para(t[key], margin, y, width-2*margin, 12)
    height = math.ceil(y+12)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{escape(t["title"])}</title><desc>{escape(t["subtitle"] + " " + t["policy"])}</desc><rect width="100%" height="100%" fill="#f3f7fa"/><style>text{{font-family:DejaVu Sans,Noto Sans CJK JP,sans-serif}}</style>\n' + '\n'.join(elements) + '\n</svg>\n'


def render_observation_html(bundle, lang='en'):
    validate_observation_inspection(bundle)
    t = labels(lang)
    sources = {s['id']: s for s in bundle['source_snapshots']}
    out = ['<!doctype html><html lang="' + lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + escape(t['title']) + '</title><style>',
        'body{font-family:system-ui,sans-serif;max-width:1100px;margin:auto;padding:14px;color:#20374a;background:#f3f7fa;line-height:1.55}*{box-sizing:border-box}h1{font-size:1.9rem}h2{font-size:1.35rem}h3{font-size:1.15rem}p,li,h1,h2,h3,a,pre{overflow-wrap:anywhere;min-width:0}p{margin:.6em 0}.facets{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;align-items:start}article{background:white;border:1px solid #b9cbd6;border-radius:9px;padding:16px;min-width:0}.warning{border-left:4px solid #955400;padding-left:12px;color:#744000}.value{font-size:1.65rem;font-weight:700}.identity{font-size:.85rem}a{color:#065579}pre{white-space:pre-wrap;font-size:.8rem}summary{cursor:pointer}section{margin:28px 0}@media(max-width:899px){.facets{grid-template-columns:minmax(0,1fr)}}',
        '</style></head><body><header><p>MATERIALS BOUNDARIES · v' + escape(bundle['engine_version']) + '</p><h1>' + escape(t['title']) + '</h1>']
    def p(value, url=None, cls=None):
        text = escape(str(value))
        if url:
            text = '<a href="' + escape(_safe_url(url), quote=True) + '">' + text + '</a>'
        out.append('<p' + (' class="' + cls + '"' if cls else '') + '>' + text + '</p>')
    for key in ('subtitle', 'policy', 'translation_notice'):
        p(t[key])
    out.append('</header><main>')
    for group, pairs in _ordered_groups(bundle):
        heading = sources[group['identity']]['title'] if group['kind'] == 'study' else t[QUANTITY_LABELS[group['identity']]]
        out.append('<section><h2>' + escape(t['group_' + group['kind']] + ': ' + heading) + '</h2><div class="facets">')
        for facet, record in pairs:
            out.append('<article id="' + facet['id'] + '" data-record-id="' + escape(record['id'], quote=True) + '"><h3>' + escape(t[QUANTITY_LABELS[record['quantity']]]) + '</h3>')
            for identity in (record['name'], t['record'] + ': ' + record['id'], t['record_version'] + ': ' + record['version'], t['study'] + ': ' + record['study_id'], _classification(record, lang)):
                p(identity, cls='identity')
            if _family(record) == PA12_FAMILY:
                for identity in _pa12_identity_lines(record, lang):
                    p(identity, cls='identity')
            if _family(record) == PAHT_FAMILY:
                for identity in _paht_identity_lines(record, lang):
                    p(identity, cls='identity')
            out.append('<div class="warning"><h3>' + escape(t['primary_warning']) + '</h3>')
            for code in facet['required_caveat_codes']:
                p(_caveat_text(code, lang))
            if _family(record) == PAHT_FAMILY:
                out.append('</div><h3>' + escape(t['paht_reported_display']) + '</h3>')
                p(t['paht_reported_notice'])
                p(t['paht_reported_median'] + ': ' + facet['reported_median_string'] + ' MPa', cls='value')
                p(t['paht_reported_sd'] + ': ' + facet['reported_sd_string'] + ' MPa', cls='value')
                out.append('<h3>' + escape(t['paht_si_display']) + '</h3>')
                p(t['paht_si_notice'])
                p(t['paht_si_median'] + ': ' + str(facet['si_value']) + ' Pa', cls='si-value')
                p(t['paht_si_sd'] + ': ' + str(facet['si_sd_value']) + ' Pa', cls='si-value')
            else:
                tensile = _family(record) == PA12_FAMILY
                out.append('</div><h3>' + escape(t['pa12_reported_display' if tensile else 'normalized']) + '</h3>')
                p(t['pa12_reported_notice' if tensile else 'normalized_notice']); p(facet['normalized_display'], cls='value')
                if tensile:
                    out.append('<h3>' + escape(t['pa12_si_display']) + '</h3>')
                    p(t['pa12_si_notice']); p(facet['si_display'], cls='si-value')
            for value, url in _detail_lines(record, lang) + _evidence_lines(record, sources[record['study_id']], lang):
                p(value, url)
            p(t['digest'] + ': ' + _digest(record), cls='identity')
            out.append('</article>')
        out.append('</div></section>')
    out.append('<section><h2>' + escape(t['source_links']) + '</h2>')
    for source in bundle['source_snapshots']:
        out.append('<h3>' + escape(source['id'] + ' | ' + source['title']) + '</h3>')
        p(t['rights'] + ': ' + _canonical(source['license']))
        if source['id'] == 'falin_et_al_2017_hbn_mechanical_properties':
            p(translate('catalog_hbn_rights_notice', lang))
        for url in source['urls']:
            p(url, url)
        p(t['digest'] + ': ' + _digest(source))
    for key in ('snapshot_notice', 'rights_notice', 'no_comparison'):
        p(t[key])
    out.append('</section><details><summary>' + escape(t['details']) + '</summary><pre id="inspection-json">' + escape(_canonical(bundle, pretty=True)) + '</pre></details></main></body></html>\n')
    return ''.join(out)


def export_observation_inspection(directory, *, record_ids=None, source_id=None, quantity=None, group_by='study', lang='en'):
    bundle = build_observation_inspection(record_ids, source_id, quantity, group_by)
    # Every serializer and both layouts finish validation before any directory
    # or target exists. Invalid selections/locales/metadata leave no artifacts.
    artifacts = {'observation-inspection.json': inspection_json(bundle),
        'observation-inspection.csv': inspection_csv(bundle),
        f'observation-inspection.{lang}.svg': render_observation_svg(bundle, lang=lang),
        f'observation-inspection.narrow.{lang}.svg': render_observation_svg(bundle, lang=lang, width=380),
        f'observation-inspection.{lang}.html': render_observation_html(bundle, lang=lang)}
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        (target/name).write_text(content, encoding='utf-8')
    return list(artifacts)
