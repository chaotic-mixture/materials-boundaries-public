"""Closed Zach/Dudescu annealed PAHT-CF source-cell admission.

The source reports medians and a separate SD column whose unit is absent.
Conditional SI scaling preserves that distinction. Hashes identify curated
metadata, never publisher bytes, measurement truth or independent replication.
"""
from decimal import Context, Decimal, localcontext
import hashlib
import json
import math

PAHT_FAMILY = 'zach_2025_paht_cf_annealed_tensile_temperature_v1'
PAHT_SOURCE = 'zach_dudescu2025jcs9110624'
PAHT_DATASET = 'zach-2025-paht-cf-annealed-fff-uts-temperature'
PAHT_PROTOCOL = 'zach2025-paht-cf-annealed-pm45-tension'
PAHT_QUANTITY = 'ultimate_tensile_strength_as_reported_3d'
PAHT_DOI = '10.3390/jcs9110624'
PAHT_MAIN = 'https://www.mdpi.com/2504-477X/9/11/624'
PAHT_ARTIFACT = 'publisher_html_updated_2026_09_02_inspected_2026_10_03'
PAHT_SOURCE_TITLE = 'Effect of Annealing on High Temperature Tensile Performance of 3D Printed Polyamide Carbon Fiber: A Comparative Study'
PAHT_TEMPERATURES = ('25', '50', '100', '150')
PAHT_CELLS = {
    '25': ('58.91', '3.44', 58910000, 3440000),
    '50': ('40.87', '4.59', 40870000, 4590000),
    '100': ('29.64', '0.72', 29640000, 720000),
    '150': ('19.03', '0.67', 19030000, 670000),
}
PAHT_SCIENTIFIC_PAYLOAD_SHA256 = {'25': '06dfcdd62a1ad46fb2379d4b53f7b7e09720309e4ae6a77c3227201fd87b0e03', '50': '91ae3c07b5763f395a2bd12c1802d6a5bf10e7e604255e3e3b3c5122f92cb027', '100': '3793db202d5b1dfe5062f3134add3d884772d883e7f845e30a93462ef751e212', '150': '910a2e3b9c72cf5e709a22aed6115a5abe9bff9b5d7d951979bcb4b284e013ee'}
PAHT_SOURCE_PAYLOAD_SHA256 = '8fc9ad94401257875f8530d1983a7a305b6206ddd0b2bc4a3b4fb8e552dfd5b4'


def _require(ok, message):
    if not ok:
        raise ValueError('PAHT-CF observation contract: ' + message)


def _canonical(value):
    if isinstance(value, dict):
        _require(all(type(key) is str for key in value), 'non-JSON metadata key')
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if type(value) is float:
        _require(math.isfinite(value), 'nonfinite metadata number')
        return int(value) if value.is_integer() else value
    _require(type(value) in (str, int, bool, type(None)), 'non-JSON metadata value')
    return value


def _digest(value):
    try:
        return hashlib.sha256(json.dumps(_canonical(value), ensure_ascii=False,
            sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError('PAHT-CF observation contract: invalid payload') from exc


def _has_marker(value, markers):
    if isinstance(value, dict):
        return any(_has_marker(item, markers) for item in value.values())
    if isinstance(value, list):
        return any(_has_marker(item, markers) for item in value)
    return type(value) is str and value in markers


def is_paht_record(record):
    """Source-specific markers, never shared UTS units or generic dataset keys."""
    return isinstance(record, dict) and _has_marker(record, {
        PAHT_FAMILY, PAHT_SOURCE, PAHT_DATASET, PAHT_PROTOCOL, PAHT_DOI,
        PAHT_MAIN, PAHT_MAIN + '#jcs-09-00624-t0A1', PAHT_ARTIFACT,
        'PAHT-CF', PAHT_SOURCE_TITLE})


def validate_paht_record(record):
    """Permit renamed display IDs; every scientific field remains closed."""
    _require(isinstance(record, dict), 'invalid record shape')
    _require(all(type(record.get(key)) is str and record[key].strip()
                 for key in ('id', 'name')), 'missing record identity')
    try:
        temperature = record['source_cell']['temperature_column']
        _require(type(temperature) is str and temperature in PAHT_CELLS, 'unsupported source cell')
        median, sd, pa, sd_pa = PAHT_CELLS[temperature]
        result, si = record['reported_result'], record['si_result']
        dispersion = result['uncertainty']
        _require(result['value_string'] == median and dispersion['value_string'] == sd,
                 'source strings changed')
        # Never depend on a caller's Decimal context, precision or traps.
        with localcontext(Context(prec=32)):
            for number, string, normalized in ((result['value'], median, si['value']),
                                               (dispersion['value'], sd, si['uncertainty_value'])):
                _require(type(number) in (int, float) and type(normalized) in (int, float),
                         'numeric metadata must not be Boolean')
                _require(Decimal(str(number)) == Decimal(string), 'source/numeric mismatch')
                _require(Decimal(string) * Decimal('1000000') == Decimal(str(normalized)),
                         'incorrect exact prefix scaling')
        _require(si['value'] == pa and si['uncertainty_value'] == sd_pa, 'source-cell SI identity changed')
        payload = {key: value for key, value in record.items() if key not in ('id', 'name')}
        _require(_digest(payload) == PAHT_SCIENTIFIC_PAYLOAD_SHA256[temperature],
                 'source-defined median/SD scientific payload changed')
    except (KeyError, TypeError, ArithmeticError) as exc:
        raise ValueError('PAHT-CF observation contract: invalid or incomplete scientific payload') from exc


def validate_paht_dataset(records, require_complete=False):
    _require(type(records) in (list, tuple), 'records must be a sequence')
    _require(type(require_complete) is bool, 'invalid completeness flag')
    seen = set()
    for record in records:
        _require(isinstance(record, dict), 'invalid record shape')
        if not is_paht_record(record):
            continue
        validate_paht_record(record)
        cell = record['source_cell']['temperature_column']
        _require(cell not in seen, 'duplicate dataset/quantity/source cell, including aliases')
        seen.add(cell)
    if require_complete:
        _require(seen == set(PAHT_TEMPERATURES), 'packaged dataset must contain exactly four approved source cells')


def validate_paht_sources(sources):
    _require(type(sources) in (list, tuple), 'sources must be a sequence')
    count = 0
    markers = {PAHT_SOURCE, PAHT_DOI, 'https://doi.org/' + PAHT_DOI,
               PAHT_MAIN, PAHT_MAIN + '/notes', PAHT_SOURCE_TITLE}
    for source in sources:
        _require(isinstance(source, dict), 'invalid source shape')
        if _has_marker(source, markers):
            _require(_digest(source) == PAHT_SOURCE_PAYLOAD_SHA256,
                     'source bibliography/version/rights payload changed')
            count += 1
    _require(count <= 1, 'duplicate or aliased source')
