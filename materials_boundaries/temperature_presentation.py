"""Authored display metadata kept separate from scientific model snapshots.

No lookup entry upgrades evidence, specimen applicability or source rights.
Uncurated appended models retain their own canonical names and temper values.
"""
from importlib.resources import files
import json
from string import Formatter

from .temperature import LANGUAGES, TemperatureError, _require, canonical_json

ALIASES = {key: 'current_' + key for key in
           ('subtitle', 'fit_notice', 'overlap_notice', 'endpoint_notice', 'source_notice', 'review_notice')}
TEMPLATES = {
    'condition_unspecified': set(),
    'condition_page': {'temper'}, 'condition_index': {'temper'},
    'condition_unreviewed': {'temper'}, 'overlap_at': {'temperature'},
    'branch_fit': {'branch', 'error'}, 'branch_value': {'branch', 'value'},
    'branch_synthetic': {'branch'}, 'condition_synthetic': set(),
    'rights_synthetic': set(), 'data_not_applicable': set(),
    'source_attribution': {'source'}, 'condition_evidence': {'source'},
}
REQUIRED_LABELS = frozenset(('title', 'subtitle', 'temperature', 'modulus', 'status',
    'fit_notice', 'unknown_notice', 'overlap_notice', 'review_notice', 'known',
    'unknown', 'temper_unknown', 't6_known', 'x_axis', 'y_axis', 'scale_notice',
    'range_notice', 'branch', 'equation_range', 'data_range', 'coefficients',
    'overlap_values', 'source_notice', 'details', 'catalog', 'evaluate', 'plot',
    'instance', 'output', 'lang', 'json', 'text', 'points', 'command',
    'endpoint_notice', 'precision_notice', 'condition_unspecified',
    'rights_unverified', 'rights_unreviewed', 'overlap_endpoint_notice', 'rights_label',
    *ALIASES.values(), *TEMPLATES))


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and '[missing:' not in value


def read_locales():
    return json.loads(files('materials_boundaries').joinpath('data/temperature_locales.json').read_text(encoding='utf-8'))


def validate_temperature_locales(catalog, models=None, sources=None):
    _require(isinstance(catalog, dict) and
             {'schema_version', 'translation_review', 'languages'} <= set(catalog) <=
             {'schema_version', 'translation_review', 'languages', 'model_presentation'},
             'temperature locales: invalid envelope')
    _require(catalog['schema_version'] == '1.0.0' and
             catalog['translation_review'] == 'machine_assisted_not_scientifically_reviewed',
             'temperature locales: invalid schema/review status')
    languages = catalog['languages']
    _require(isinstance(languages, dict) and set(languages) == set(LANGUAGES),
             'temperature locales: four languages required')
    _require(isinstance(languages['en'], dict), 'temperature locales.en: object required')
    for lang, messages in languages.items():
        _require(isinstance(messages, dict) and set(messages) == set(languages['en']) and
                 REQUIRED_LABELS <= set(messages) and all(_text(s) for s in messages.values()),
                 f'temperature locales.{lang}: missing/invalid labels or key parity')
        for key, expected in TEMPLATES.items():
            try:
                parts = list(Formatter().parse(messages[key]))
                actual = {field for _, field, _, _ in parts if field is not None}
                _require(actual == expected and all(not spec and conversion is None
                         for _, field, spec, conversion in parts if field is not None),
                         f'temperature locales.{lang}.{key}: unsupported placeholders')
                messages[key].format(**{name: 'value' for name in expected})
            except (KeyError, ValueError, IndexError) as exc:
                raise TemperatureError(f'temperature locales.{lang}.{key}: malformed template') from exc
    presentation = catalog.get('model_presentation', {})
    _require(isinstance(presentation, dict), 'temperature model presentation: object required')
    model_index = {m['id']: m for m in models['records']} if models is not None else None
    source_index = {s['id']: s for s in sources['records']} if sources is not None else None
    required = {'material_snapshot', 'names', 'temper_evidence', 'temper_source_id',
                'primary_source_id', 'reuse_status_snapshot', 'rights_review'}
    for mid, entry in presentation.items():
        _require(_text(mid) and isinstance(entry, dict) and set(entry) == required,
                 'temperature model presentation: unexpected or missing fields')
        _require(isinstance(entry['names'], dict) and set(entry['names']) == set(LANGUAGES)
                 and all(_text(name) for name in entry['names'].values()),
                 f'{mid}: four material names required')
        _require(entry['temper_evidence'] in ('property_page', 'material_index_only', 'not_specified', 'synthetic_demo'),
                 f'{mid}: unsupported temper evidence')
        synthetic = entry['temper_evidence'] == 'synthetic_demo'
        _require(_text(entry['primary_source_id']) and _text(entry['reuse_status_snapshot']) and
                 entry['rights_review'] == ('project_authored_synthetic' if synthetic else 'public_reuse_terms_unverified'),
                 f'{mid}: unsupported presentation source/rights review')
        material = entry['material_snapshot']
        _require(isinstance(material, dict) and set(material) == {'name', 'UNS', 'temper', 'temper_status',
                                                          *(('identity_status',) if synthetic else ())}
                 and _text(material['name']) and
                 ((material['UNS'] is None and material['identity_status'] == 'synthetic_demo')
                  if synthetic else _text(material['UNS'])),
                 f'{mid}: invalid presentation material snapshot')
        unspecified = entry['temper_evidence'] in ('not_specified', 'synthetic_demo')
        _require((unspecified and material['temper'] is None and material['temper_status'] == ('not_applicable_synthetic_demo' if synthetic else 'not specified')
                  and entry['temper_source_id'] is None) or
                 (not unspecified and _text(material['temper']) and material['temper_status'] == 'specified'
                  and _text(entry['temper_source_id'])), f'{mid}: inconsistent temper evidence')
        if model_index is not None:
            _require(mid in model_index, f'{mid}: unresolved presentation model')
            model = model_index[mid]
            _require((model['classification'] == 'synthetic_demo') == synthetic,
                     f'{mid}: classification differs from presentation evidence')
            _require(canonical_json(material) == canonical_json(model['material']) and
                     entry['reuse_status_snapshot'] == model['reuse']['status'],
                     f'{mid}: stale material or reuse presentation snapshot')
            _require(entry['primary_source_id'] in model['source_ids'] and
                     (unspecified or entry['temper_source_id'] in model['source_ids']),
                     f'{mid}: presentation source is not linked to the model')
        if source_index is not None:
            _require(entry['primary_source_id'] in source_index and
                     (unspecified or entry['temper_source_id'] in source_index),
                     f'{mid}: unresolved presentation source')
    return catalog


def labels(lang):
    _require(lang in LANGUAGES, 'unsupported language')
    catalog = validate_temperature_locales(read_locales())
    result = dict(catalog['languages'][lang])
    # Active consumers share generalized notices through compatibility aliases.
    # The public catalog includes only newly authored synthetic demonstrations.
    for key, replacement in ALIASES.items():
        result[key] = result[replacement]
    return result


def presentation_for(model, sources, lang):
    from .catalog import read_catalog
    catalog = read_locales()
    # Validate the complete lookup, not just the requested ID. This also prevents
    # a stale entry from silently relabeling a changed scientific record.
    validate_temperature_locales(catalog, read_catalog('temperature_models'), read_catalog('sources'))
    t = labels(lang)
    entry = catalog.get('model_presentation', {}).get(model['id'])
    if entry is None:
        synthetic = model['classification'] == 'synthetic_demo'
        condition = (t['condition_synthetic'] if synthetic else t['condition_unspecified']) if model['material']['temper'] is None else \
                    t['condition_unreviewed'].format(temper=model['material']['temper'])
        return {'name': model['material']['name'], 'condition': condition,
                'rights': t['rights_synthetic'] if synthetic else t['rights_unreviewed'], 'source_id': None, 'condition_source_id': None}
    _require(canonical_json(entry['material_snapshot']) == canonical_json(model['material']) and
             entry['reuse_status_snapshot'] == model['reuse']['status'] and
             entry['primary_source_id'] in {source['id'] for source in sources},
             f'{model["id"]}: displayed model/source differs from presentation evidence')
    key = {'property_page':'condition_page', 'material_index_only':'condition_index',
           'not_specified':'condition_unspecified', 'synthetic_demo':'condition_synthetic'}[entry['temper_evidence']]
    return {'name': entry['names'][lang],
            'condition': t[key].format(temper=model['material']['temper']),
            'rights': t['rights_synthetic'] if model['classification'] == 'synthetic_demo' else t['rights_unverified'], 'source_id': entry['primary_source_id'],
            'condition_source_id': entry['temper_source_id']}


def branch_fit_label(branch, messages):
    """Null synthetic error is not a percentage, estimate or uncertainty claim."""
    if branch['reported_fit_error'].get('status') == 'not_applicable_synthetic_demo':
        return messages['branch_synthetic'].format(branch=branch['id'])
    return messages['branch_fit'].format(branch=branch['id'],
                                         error=f"{branch['reported_fit_error']['value']:g}")


def branch_data_label(branch, messages):
    if branch['source_data_range_K'] is None:
        return messages['data_not_applicable']
    low, high = branch['source_data_range_K']
    return f"{low:g}–{high:g} K"
