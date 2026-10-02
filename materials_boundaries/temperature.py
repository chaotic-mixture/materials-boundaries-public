"""Isolated fixed quartic model arithmetic, never bound evaluations.

Bundled synthetic demonstrations are separate from supported empirical fits.

Source formula strings are display-only. Every applicable branch is evaluated;
no overlap tie-break, smoothing, monotonicity assumption or extrapolation exists.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import math
import re

from .catalog import read_catalog
from .validation import ValidationError

SCHEMA_VERSION = '1.0.0'
LANGUAGES = ('en', 'zh', 'ja', 'de')
FAMILY = 'temperature_quartic_v1'
FORMULA = 'E_GPa = a + b*T_K + c*T_K^2 + d*T_K^3 + e*T_K^4'
OVERLAP_POLICY = 'retain_all_matching_branches_without_selection_averaging_or_smoothing'
DECIMAL = re.compile(r'^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?$')
ID = re.compile(r'^[a-z][a-z0-9_]*$')
UNKNOWN_CONDITIONS = ('pressure', 'test_direction', 'grain_size', 'texture', 'porosity',
                      'product_form', 'specimen_geometry', 'cold_work', 'test_method',
                      'strain_rate_or_frequency', 'measurement_uncertainty',
                      'fit_error_statistical_definition', 'confidence_level')


class TemperatureError(ValidationError):
    """A temperature input or fixed model contract is invalid."""


def canonical_json(value, *, pretty=False):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      indent=2 if pretty else None, separators=None if pretty else (',', ':'))


def _require(condition, message):
    if not condition:
        raise TemperatureError(message)


def finite_number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _keys(value, expected, name, *, optional=()):
    required = set(expected)
    _require(isinstance(value, dict) and required <= set(value) <= required | set(optional),
             f'{name}: unexpected or missing fields')


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _text_list(value, name, *, unique=False):
    _require(isinstance(value, list) and bool(value) and all(_text(item) for item in value),
             f'{name}: nonempty authored string list required')
    _require(not unique or len(value) == len(set(value)), f'{name}: duplicate entries')


def _date_text(value):
    # fromisoformat alone also accepts compact and ISO-week dates on Python 3.11.
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_model_catalog(catalog):
    """Dependency-free closed scientific and metadata guard.

    Authored disclosures remain flexible text; structural validation cannot
    establish source inspection, specimen applicability or redistribution rights.
    Data and equation intervals stay separate, with no monotonicity assumption.
    """
    _keys(catalog, ('schema_version', 'records'), 'temperature_models')
    _require(catalog['schema_version'] == SCHEMA_VERSION, 'unsupported temperature catalog schema')
    _require(isinstance(catalog['records'], list) and bool(catalog['records']), 'models: nonempty list required')
    seen, branches = set(), set()
    for model in catalog['records']:
        _require(isinstance(model, dict), 'model: object required')
        synthetic = model.get('classification') == 'synthetic_demo'
        provenance_key = 'author_provenance' if synthetic else 'original_reference'
        _keys(model, ('id', 'version', 'name', 'descriptions', 'classification',
                      'evaluation_support', 'equation_family', 'quantity', 'input_unit',
                      'output_unit', 'equation_display', 'coefficient_order', 'coefficient_units',
                      'material', 'branches', 'unknown_conditions', 'overlap_policy', 'source_ids',
                      'source_locator', provenance_key, 'scope_exclusions', 'verification',
                      'reuse', 'curation_date', 'range_interpretation'), 'model')
        mid = model['id']
        _require(isinstance(mid, str) and ID.fullmatch(mid) and mid not in seen, 'duplicate or invalid model ID')
        seen.add(mid)
        for field, value in {'version':'1.0.0', 'classification':'synthetic_demo' if synthetic else 'empirical_fit_prediction',
                             'evaluation_support':'temperature_quartic', 'equation_family':FAMILY,
                             'quantity':'youngs_modulus', 'input_unit':'K', 'output_unit':'GPa',
                             'equation_display':FORMULA, 'coefficient_order':['a','b','c','d','e'],
                             'coefficient_units':['GPa','GPa/K','GPa/K^2','GPa/K^3','GPa/K^4'],
                             'overlap_policy':OVERLAP_POLICY}.items():
            _require(model.get(field) == value, f'{mid}: unsupported {field}')
        for field in ('name', 'source_locator', 'range_interpretation'):
            _require(_text(model[field]), f'{mid}: nonempty {field} required')
        _require(_date_text(model['curation_date']), f'{mid}: curation_date must be a valid YYYY-MM-DD date')
        descriptions = model['descriptions']
        _require(isinstance(descriptions, dict) and set(descriptions) == set(LANGUAGES)
                 and all(_text(s) for s in descriptions.values()),
                 f'{mid}: four authored descriptions required')
        material = model['material']
        _keys(material, ('name', 'UNS', 'temper', 'temper_status',
                         *(('identity_status',) if synthetic else ())), f'{mid}: material')
        _require(_text(material['name']), f'{mid}: material name required')
        if synthetic:
            _require(material['UNS'] is None and material['temper'] is None and
                     material['temper_status'] == 'not_applicable_synthetic_demo' and
                     material['identity_status'] == 'synthetic_demo',
                     f'{mid}: synthetic identity cannot imply a real material or temper')
        else:
            _require(_text(material['UNS']), f'{mid}: material UNS required')
            _require((material['temper_status'] == 'specified' and _text(material['temper'])) or
                     (material['temper_status'] == 'not specified' and material['temper'] is None),
                     f'{mid}: material temper and status must agree')
        unknown = model['unknown_conditions']
        _keys(unknown, UNKNOWN_CONDITIONS, f'{mid}: unknown conditions')
        for field in UNKNOWN_CONDITIONS:
            condition = unknown[field]
            _keys(condition, ('value', 'status'), f'{mid}: unknown {field}')
            _require(condition['value'] is None and _text(condition['status']) and
                     (not synthetic or condition['status'] == 'not_applicable_synthetic_demo'),
                     f'{mid}: unknown {field} requires null value and authored status')
        _text_list(model['source_ids'], f'{mid}: source IDs', unique=True)
        _text_list(model['scope_exclusions'], f'{mid}: scope exclusions')
        if synthetic:
            provenance = model['author_provenance']
            _keys(provenance, ('author', 'creation_method', 'is_empirical',
                              'derived_from_measurements'), f'{mid}: author provenance')
            _require(_text(provenance['author']) and
                     provenance['creation_method'] == 'independently_authored_demonstration_polynomial' and
                     provenance['is_empirical'] is False and
                     provenance['derived_from_measurements'] is False,
                     f'{mid}: synthetic provenance must not claim empirical derivation')
            review_flags = {'synthetic_arithmetic_checked': True,
                            'independent_scientific_review': False, 'empirical_validation': False}
        else:
            reference = model['original_reference']
            reference_text = ('title', 'editor', 'institution', 'edition', 'chart', 'reference_list_locator')
            _keys(reference, (*reference_text, 'reference_chart_retrieved'), f'{mid}: original reference',
                  optional=('source_date_annotation',))
            _require(all(_text(reference[field]) for field in reference_text) and
                     ('source_date_annotation' not in reference or _text(reference['source_date_annotation'])),
                     f'{mid}: nonempty original-reference text required')
            _require(reference['reference_chart_retrieved'] is False,
                     f'{mid}: unsupported original-reference retrieval status')
            review_flags = {'source_equation_checked': True, 'synthetic_arithmetic_checked': True,
                            'independent_scientific_review': False, 'original_charts_retrieved': False}
        verification = model['verification']
        _keys(verification, (*review_flags, 'translation_review'), f'{mid}: verification')
        _require(all(verification[field] is value for field, value in review_flags.items()) and
                 _text(verification['translation_review']), f'{mid}: unsupported verification status')
        reuse = model['reuse']
        _keys(reuse, ('status', 'caveats', 'recommended_attribution'), f'{mid}: reuse')
        _require(_text(reuse['status']) and _text(reuse['recommended_attribution']),
                 f'{mid}: authored reuse status and attribution required')
        _text_list(reuse['caveats'], f'{mid}: reuse caveats')
        _require(isinstance(model['branches'], list) and 1 <= len(model['branches']) <= 20,
                 f'{mid}: 1–20 branches required')
        for branch in model['branches']:
            _keys(branch, ('id','coefficients_text','source_data_range_K','equation_range_K','endpoints','reported_fit_error',
                           *(('range_status',) if synthetic else ())), 'branch')
            bid = branch['id']
            _require(isinstance(bid, str) and ID.fullmatch(bid) and bid not in branches, 'duplicate or invalid branch ID')
            branches.add(bid)
            cs = branch['coefficients_text']
            _require(isinstance(cs, list) and len(cs) == 5, f'{bid}: exactly five coefficients required')
            for c in cs:
                _require(isinstance(c, str) and bool(DECIMAL.fullmatch(c)), f'{bid}: coefficient must be finite decimal text')
                try:
                    number = Decimal(c)
                    valid = number.is_finite() and math.isfinite(float(number)) and (number == 0 or float(number) != 0)
                except (InvalidOperation, ValueError, OverflowError):
                    valid = False
                _require(valid, f'{bid}: coefficient outside finite representable range')
            if synthetic:
                _require(branch['source_data_range_K'] is None and
                         branch['range_status'] == 'artificial_demonstration_interval',
                         f'{bid}: synthetic ranges are artificial, with no source data')
            for field in (('equation_range_K',) if synthetic else ('source_data_range_K','equation_range_K')):
                interval = branch[field]
                _require(isinstance(interval, list) and len(interval) == 2 and
                         all(finite_number(n) and n >= 0 for n in interval) and interval[0] < interval[1],
                         f'{bid}: invalid {field}')
            _require(branch['equation_range_K'][0] > 0, f'{bid}: positive absolute equation temperatures required')
            _require(branch['endpoints'] == 'inclusive', f'{bid}: endpoints must be inclusive')
            fit = branch['reported_fit_error']
            _keys(fit, ('value','unit','statistic','confidence_level','is_measurement_uncertainty','is_confidence_interval','is_validated_maximum_error_bound',
                        *(('status',) if synthetic else ())), 'fit error')
            error_valid = (fit['value'] is None and fit['unit'] is None and
                           fit['status'] == 'not_applicable_synthetic_demo') if synthetic else (
                           finite_number(fit['value']) and fit['value'] >= 0 and
                           fit['unit'] == 'percent_relative_to_source_data')
            _require(error_valid and
                     fit['statistic'] is None and fit['confidence_level'] is None and
                     all(fit[key] is False for key in ('is_measurement_uncertainty','is_confidence_interval','is_validated_maximum_error_bound')),
                     f'{bid}: unsupported fit error interpretation')
    return catalog


def validate_input(instance):
    _keys(instance, ('schema_version','model_id','temperature'), 'temperature input')
    _require(instance['schema_version'] == SCHEMA_VERSION, 'unsupported temperature input schema')
    _require(isinstance(instance['model_id'], str) and bool(instance['model_id'].strip()), 'model_id: nonempty string required')
    _keys(instance['temperature'], ('value','unit'), 'temperature')
    _require(instance['temperature']['unit'] == 'K', 'temperature unit must be K; no implicit Celsius conversion')
    value = instance['temperature']['value']
    _require(finite_number(value) and value >= 0, 'temperature must be a finite nonnegative number in K')


def get_model(model_id):
    models = validate_model_catalog(read_catalog('temperature_models'))
    found = next((r for r in models['records'] if r['id'] == model_id), None)
    _require(found is not None, f'unknown temperature model ID: {model_id}')
    return deepcopy(found)


def _quartic(coefficients, temperature):
    # Fixed arithmetic, independent of caller decimal context; never eval/exec.
    with localcontext(Context(prec=60)):
        t = Decimal(str(temperature))
        value = Decimal(coefficients[4])
        for coefficient in reversed(coefficients[:4]):
            value = value * t + Decimal(coefficient)
        result = float(value)
    _require(math.isfinite(result) and result > 0, 'polynomial output outside finite positive modulus range')
    return result


def _predict(model, temperature):
    predictions = []
    for branch in model['branches']:
        low, high = branch['equation_range_K']
        if low <= temperature <= high:
            predictions.append({'branch_id':branch['id'], 'value':_quartic(branch['coefficients_text'], temperature),
                                'unit':'GPa', 'equation_range_K':deepcopy(branch['equation_range_K'])})
    return {'status':'ambiguous_overlap' if len(predictions) > 1 else 'prediction' if predictions else 'out_of_range',
            'predictions':predictions}


def model_sources(model):
    by_id = {source['id']:source for source in read_catalog('sources')['records']}
    _require(all(sid in by_id for sid in model['source_ids']), 'unresolved temperature source ID')
    return [deepcopy(by_id[sid]) for sid in model['source_ids']]


def evaluate_temperature(instance):
    """Evaluate only inside equation ranges, retaining every matching branch.

    Synthetic output is demonstration arithmetic, not a physical prediction.
    Empirical output does not establish applicability to a physical specimen.
    """
    from . import __version__
    validate_input(instance)
    model = get_model(instance['model_id'])
    synthetic = model['classification'] == 'synthetic_demo'
    result = {'schema_version':SCHEMA_VERSION, 'engine_version':__version__, 'input':deepcopy(instance),
              'classification':model['classification'], 'quantity':'youngs_modulus',
              **_predict(model, instance['temperature']['value']),
              'model_snapshot':model, 'source_snapshots':model_sources(model),
              'specimen_applicability':'not_applicable_synthetic_demo' if synthetic else 'not_established', 'uncertainty_band':None,
              'interpretation':('SYNTHETIC demonstration arithmetic only; artificial coefficients and intervals do not represent a real material, measurements or empirical evidence. Fit error is not applicable. All matching branches retained.' if synthetic else 'Source fit predictions only; fit error is not measurement uncertainty or a confidence interval. All matching branches retained; no physical discontinuity inferred.')}
    result['id'] = sha256(canonical_json(result).encode()).hexdigest()[:20]
    return result


def render_prediction(result, lang='en'):
    _require(lang in LANGUAGES, 'unsupported language')
    # Do not present arbitrary imported values as canonical predictions.
    _require(isinstance(result, dict) and 'input' in result and canonical_json(result) == canonical_json(evaluate_temperature(result['input'])),
             'noncanonical temperature evaluation')
    from .temperature_presentation import labels, presentation_for, branch_fit_label
    t = labels(lang)
    model = result['model_snapshot']
    display = presentation_for(model, result['source_snapshots'], lang)
    lines = [display['name'], model['descriptions'][lang], display['condition'],
             f"{t['temperature']}: {result['input']['temperature']['value']} K",
             f"{t['status']}: {result['status']}"]
    for row in result['predictions']:
        lines.append(t['branch_value'].format(branch=row['branch_id'], value=f"{row['value']:.12g}"))
    for branch in model['branches']:
        lines.append(branch_fit_label(branch, t))
    lines.extend([display['rights'], t['fit_notice'], t['unknown_notice'],
                  t['overlap_notice'], t['endpoint_notice'], t['precision_notice'], t['review_notice']])
    return '\n'.join(lines)
