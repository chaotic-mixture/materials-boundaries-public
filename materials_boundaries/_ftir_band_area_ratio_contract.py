"""Author-reported Gaussian carbonyl area ratios; no spectral computation."""
from copy import deepcopy
from decimal import Decimal
import json

QUANTITY = 'ftir_fitted_carbonyl_band_area_ratio'
UNIT = 'ratio_ftir_fitted_carbonyl_areas'
METHOD = 'source_reported_ftir_fitted_band_area_ratio'
PROFILE = 'source_ftir_fitted_carbonyl_band_area_ratio_v1'
WAVENUMBER_UNIT = 'cm_inverse_ftir_band_center'
FACT_FIELDS = ('reported_formula', 'spectrometer_and_acquisition_mode',
               'band_assignments_as_author_interpretation', 'baseline_and_normalization',
               'fit_model_width_constraints_and_intervals', 'integration_and_ratio_averaging_order',
               'sample_preparation_conditioning', 'source_data_attribution',
               'replication_and_statistics', 'instrument_corrections_and_calibration')
LABEL_KEYS = ('code_' + QUANTITY, 'code_' + METHOD, 'ftir_area_ratio_derivation',
              'ftir_area_ratio_notice', 'ftir_area_ratio_numerator', 'ftir_area_ratio_denominator',
              'ftir_area_ratio_source_cell', *(f'ftir_area_ratio_{n}' for n in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref('evidence'), 1)
    unknown = {'enum': ['not_reported_in_inspected_source', 'not_verified']}
    definitions['ftir_area_ratio_fact'] = {'oneOf': [
        obj(dict(status={'const': 'reported'}, text=text, evidence=evidence, notes=text)),
        obj(dict(status=unknown, text={'type': 'null'}, evidence=evidence, notes=text)),
    ]}
    positive = {'type': 'string', 'maxLength': 49,
        'pattern': r'^(?=[0-9.]*[1-9])(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])'}
    definitions['ftir_area_ratio_band'] = obj(dict(
        role={'const': 'gaussian_fitted_integrated_carbonyl_band_area'},
        number=positive, value_text=text,
        unit_code={'const': WAVENUMBER_UNIT}, unit_text={'const': 'cm⁻¹'},
        evidence=evidence, notes=text))
    # An explicit original result address survives locator rewording, definition
    # enrichment and corrected coordinates. It is not a new material identity.
    definitions['ftir_area_ratio_source_cell'] = obj(dict(
        table_id=text, row_key=text, column_key=text, evidence=evidence, notes=text))
    definitions['ftir_area_ratio_derivation'] = obj({
        'schema_version': {'const': '1.0.0'}, 'profile_id': {'const': PROFILE},
        'profile_version': {'const': '1.0.0'}, 'executor': {'const': 'source_reported_only'},
        'formula_family': {'const': 'source_ordered_fitted_area_ratio'},
        'lineshape': {'const': 'source_reported_gaussian'},
        'source_result_cell': ref('ftir_area_ratio_source_cell'),
        'numerator_band': ref('ftir_area_ratio_band'),
        'denominator_band': ref('ftir_area_ratio_band'),
        **{n: ref('ftir_area_ratio_fact') for n in FACT_FIELDS},
        'evidence': evidence, 'notes': text,
    })
    scalar = next(deepcopy(v) for v in definitions['reported_value']['oneOf']
                  if v['properties']['kind'].get('const') == 'scalar')
    scalar['properties'].update(unit_code={'const': UNIT}, number={
        'type': 'string', 'maxLength': 49,
        'pattern': r'^(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])'})
    definitions['ftir_area_ratio_reported_value'] = scalar

    def specialize(value):
        if isinstance(value, dict):
            if value.get('$ref') == '#/$defs/reported_measure':
                value['$ref'] = '#/$defs/ftir_area_ratio_reported_measure'
            fields = value.get('properties', {})
            if 'enum' in fields.get('unit_code', {}):
                fields['unit_code'] = {'const': UNIT}
            for child in value.values():specialize(child)
        elif isinstance(value, list):
            for child in value:specialize(child)
    for old, new in [('reported_measure', 'ftir_area_ratio_reported_measure'),
                     ('uncertainty', 'ftir_area_ratio_uncertainty')]:
        definitions[new] = deepcopy(definitions[old]);specialize(definitions[new])
    branch = deepcopy(base);fields = branch['properties']
    fields.update(quantity={'const': QUANTITY}, quantity_dimension={'const': 'dimensionless'},
                  reported_value=ref('ftir_area_ratio_reported_value'),
                  evidence_kind={'const': 'published_measurement_derived_reference'},
                  determination_basis={'const': 'source_reports_calculation'},
                  reporting_basis={'const': 'reported_summary'}, density_basis={'type': 'null'},
                  derivation=ref('ftir_area_ratio_derivation'),
                  uncertainty={'anyOf': [ref('ftir_area_ratio_uncertainty'), {'type': 'null'}]})
    fields['method_definition']['properties']['type'] = {'const': METHOD}
    fields['method_definition']['properties']['extraction_window'] = {'type': 'null'}
    branch['required'].append('derivation')
    return branch


def applies(prop):
    d = prop.get('derivation')
    return (prop.get('quantity') == QUANTITY or prop.get('method_definition', {}).get('type') == METHOD
            or isinstance(d, dict) and d.get('profile_id') == PROFILE)


def validate_derivation(prop):
    """Validate reported roles and evidence, never evaluate a fit or area ratio."""
    if not applies(prop):return
    def fail(message):raise ValueError(prop['id'] + ': ' + message)
    d = prop.get('derivation')
    if (prop['quantity'] != QUANTITY or prop['method_definition']['type'] != METHOD
            or not isinstance(d, dict) or d.get('profile_id') != PROFILE
            or d.get('executor') != 'source_reported_only'
            or prop['evidence_kind'] != 'published_measurement_derived_reference'
            or prop['determination_basis'] != 'source_reports_calculation'):
        fail('FTIR quantity/method/profile/source-calculation roles must agree')
    number = Decimal(prop['reported_value']['number'])
    if not number.is_finite() or number < 0:fail('FTIR ratio must be finite and nonnegative')
    if prop['conditions']['direction']['status'] == 'not_applicable':
        fail('scalar spectral ratio does not certify direction inapplicability')
    source, document = prop['source_id'], prop['source_document']['url']
    def require(value, roles):
        if not value['notes'].strip():fail('FTIR metadata requires scope notes')
        for role in roles:
            if not any(e['source_id'] == source and e['url'] == document and role in e['supports']
                       for e in value['evidence']):
                fail('FTIR metadata needs primary inspected-document ' + role + ' evidence')
    require(d, ('method', 'classification'))
    for name in FACT_FIELDS:
        fact = d[name];reported = fact['status'] == 'reported'
        require(fact, ('method', 'condition') if reported else ('condition',))
        if reported and not fact['text'].strip():fail('reported FTIR facts need attributed text')
    for name in ('reported_formula', 'fit_model_width_constraints_and_intervals'):
        if d[name]['status'] != 'reported':fail('source formula and Gaussian fitting method must be reported')
    cell = d['source_result_cell'];require(cell, ('reported_value', 'classification'))
    for name in ('table_id', 'row_key', 'column_key'):
        if not cell[name].strip() or cell[name] != cell[name].strip():
            fail('original source-cell address must be nonblank and stable')
    from .material_references import _numeric_token_matches
    for name in ('numerator_band', 'denominator_band'):
        band = d[name];require(band, ('method', 'classification'))
        number = Decimal(band['number'])
        if not number.is_finite() or number <= 0 or not _numeric_token_matches(band['value_text'], band['number']):
            fail('source band coordinate must preserve positive wavenumber precision')


def cell_key(prop):
    """Metadata or scalar corrections revise the original cell, never duplicate it."""
    cell = prop['derivation']['source_result_cell']
    return json.dumps([prop['material_state_id'], prop['quantity'], prop['source_document']['url'],
                       *(cell[n] for n in ('table_id', 'row_key', 'column_key'))], ensure_ascii=False)
