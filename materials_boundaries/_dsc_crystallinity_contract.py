"""Author-reported DSC normalization, never software recomputation or phase resolution."""
from copy import deepcopy
from decimal import Decimal
import json

QUANTITY = 'dsc_reference_normalized_crystallinity_percentage'
UNIT = 'percent_dsc_reference_crystallinity'
METHOD = 'source_reported_dsc_reference_normalization'
PROFILE = 'source_dsc_reference_enthalpy_normalization_v1'
REFERENCE_UNIT = 'J_per_g_dsc_crystalline_reference'
FACT_FIELDS = ('reported_formula', 'reference_material_and_citation', 'fraction_factor_and_mass_basis',
               'thermal_signal_and_cycle_claims', 'integration_baseline_and_corrections',
               'instrument_program_and_calibration', 'source_data_attribution', 'replication_and_statistics')
LABEL_KEYS = ('code_' + QUANTITY, 'dsc_crystallinity_derivation', 'dsc_crystallinity_notice',
              'dsc_crystallinity_reference', 'dsc_crystallinity_formula_family',
              'dsc_crystallinity_cycle_status', 'dsc_crystallinity_claim',
              'code_source_reported_dsc_reference_normalization',
              'code_reported_source_assignment', 'code_conflicting_source_statements',
              'code_source_enthalpy_ratio', 'code_source_fraction_corrected_enthalpy_ratio',
              *(f'dsc_crystallinity_{name}' for name in FACT_FIELDS))


def schema_branch(definitions, base, *, text, obj, array, ref):
    evidence = array(ref('evidence'), 1)
    unknown = {'enum': ['not_reported_in_inspected_source', 'not_verified']}
    definitions['dsc_crystallinity_fact'] = {'oneOf': [
        obj(dict(status={'const': 'reported'}, text=text, evidence=evidence, notes=text)),
        obj(dict(status=unknown, text={'type': 'null'}, evidence=evidence, notes=text)),
    ]}
    positive = {'type': 'string', 'maxLength': 49,
        'pattern': r'^(?=[0-9.]*[1-9])(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])'}
    definitions['dsc_crystallinity_reference'] = {'oneOf': [
        obj(dict(status={'const': 'reported'}, number=positive, value_text=text,
                 unit_code={'const': REFERENCE_UNIT}, unit_text={'const': 'J/g'}, evidence=evidence, notes=text)),
        obj({'status': unknown, **{k: {'type': 'null'} for k in ('number', 'value_text', 'unit_code', 'unit_text')},
             'evidence': evidence, 'notes': text}),
    ]}
    definitions['dsc_crystallinity_claim'] = obj(dict(
        scope={'enum': ['reported_crystallinity_origin', 'reported_enthalpy_scan', 'reported_common_program']},
        phase={'enum': ['heating', 'cooling']},
        occurrence={'anyOf': [{'type': 'integer', 'minimum': 1}, {'type': 'null'}]},
        text=text, evidence=evidence, notes=text))
    definitions['dsc_crystallinity_cycle'] = obj(dict(
        status={'enum': ['reported_source_assignment', 'not_reported_in_inspected_source',
                         'not_verified', 'conflicting_source_statements']},
        assignment_text={'anyOf': [text, {'type': 'null'}]},
        claims=array(ref('dsc_crystallinity_claim')), evidence=evidence, notes=text))
    definitions['dsc_crystallinity_derivation'] = obj({
        'schema_version': {'const': '1.0.0'}, 'profile_id': {'const': PROFILE},
        'profile_version': {'const': '1.0.0'}, 'executor': {'const': 'source_reported_only'},
        'formula_family': {'enum': ['source_enthalpy_ratio', 'source_fraction_corrected_enthalpy_ratio']},
        'reference_specific_enthalpy': ref('dsc_crystallinity_reference'),
        'cycle_assignment': ref('dsc_crystallinity_cycle'),
        **{name: ref('dsc_crystallinity_fact') for name in FACT_FIELDS},
        'evidence': evidence, 'notes': text,
    })
    scalar = next(deepcopy(v) for v in definitions['reported_value']['oneOf']
                  if v['properties']['kind'].get('const') == 'scalar')
    scalar['properties'].update(unit_code={'const': UNIT}, number={'type': 'string', 'maxLength': 28,
        'pattern': r'^(?:(?:0|[1-9][0-9]?)(?:\.[0-9]{1,24})?|100(?:\.0{1,24})?)(?![\s\S])'})
    definitions['dsc_crystallinity_reported_value'] = scalar

    def specialize(value):
        if isinstance(value, dict):
            if value.get('$ref') == '#/$defs/reported_measure':
                value['$ref'] = '#/$defs/dsc_crystallinity_reported_measure'
            fields = value.get('properties', {})
            if 'enum' in fields.get('unit_code', {}):fields['unit_code'] = {'const': UNIT}
            for child in value.values():specialize(child)
        elif isinstance(value, list):
            for child in value:specialize(child)
    for old, new in [('reported_measure', 'dsc_crystallinity_reported_measure'), ('uncertainty', 'dsc_crystallinity_uncertainty')]:
        definitions[new] = deepcopy(definitions[old]);specialize(definitions[new])
    branch = deepcopy(base);fields = branch['properties']
    fields.update(quantity={'const': QUANTITY}, quantity_dimension={'const': 'dimensionless'},
                  reported_value=ref('dsc_crystallinity_reported_value'),
                  evidence_kind={'const': 'published_measurement_derived_reference'},
                  determination_basis={'const': 'source_reports_calculation'},
                  reporting_basis={'const': 'reported_summary'}, density_basis={'type': 'null'},
                  derivation=ref('dsc_crystallinity_derivation'),
                  uncertainty={'anyOf': [ref('dsc_crystallinity_uncertainty'), {'type': 'null'}]})
    fields['method_definition']['properties']['type'] = {'const': METHOD}
    fields['method_definition']['properties']['extraction_window'] = {'type': 'null'}
    branch['required'].append('derivation')
    return branch


def applies(prop):
    derivation = prop.get('derivation')
    return (prop.get('quantity') == QUANTITY or prop.get('method_definition', {}).get('type') == METHOD
            or isinstance(derivation, dict) and derivation.get('profile_id') == PROFILE)


def validate_derivation(prop):
    """Check declared provenance and shape semantics; do not evaluate source math."""
    if not applies(prop):return
    def fail(message):raise ValueError(prop['id'] + ': ' + message)
    d = prop.get('derivation')
    if (prop['quantity'] != QUANTITY or prop['method_definition']['type'] != METHOD
            or not isinstance(d, dict) or d.get('profile_id') != PROFILE
            or d.get('executor') != 'source_reported_only'
            or prop['evidence_kind'] != 'published_measurement_derived_reference'
            or prop['determination_basis'] != 'source_reports_calculation'):
        fail('DSC normalization quantity/method/profile/source-calculation role must agree')
    if not 0 <= Decimal(prop['reported_value']['number']) <= 100:fail('source Xc outside admitted percentage domain;do not clamp')
    if prop['conditions']['direction']['status'] == 'not_applicable':fail('scalar Xc does not certify direction inapplicability')
    source, document = prop['source_id'], prop['source_document']['url']
    def support(evidence, role):
        return any(e['source_id'] == source and e['url'] == document and role in e['supports'] for e in evidence)
    def require_notes(value):
        if not value['notes'].strip():fail('DSC normalization metadata requires scope notes')
    require_notes(d)
    for role in ('method', 'classification'):
        if not support(d['evidence'], role):fail('derivation needs primary inspected-document ' + role + ' evidence')
    for name in FACT_FIELDS:
        fact = d[name];require_notes(fact)
        reported = fact['status'] == 'reported'
        if reported and not fact['text'].strip():fail('reported DSC facts require text')
        for role in (('method', 'condition') if reported else ('condition',)):
            if not support(fact['evidence'], role):fail('DSC facts need primary inspected-document ' + role + ' evidence')
    if d['reported_formula']['status'] != 'reported':fail('source normalization requires its reported original formula')
    reference = d['reference_specific_enthalpy'];require_notes(reference)
    for role in (('method', 'classification') if reference['status'] == 'reported' else ('classification',)):
        if not support(reference['evidence'], role):fail('reference requires primary inspected-document ' + role + ' evidence')
    if reference['status'] == 'reported':
        from .material_references import _numeric_token_matches
        if Decimal(reference['number']) <= 0 or not _numeric_token_matches(reference['value_text'], reference['number']):
            fail('reference must preserve a positive source J/g scalar')
    cycle = d['cycle_assignment'];require_notes(cycle)
    if not support(cycle['evidence'], 'condition'):fail('cycle requires primary inspected-document condition evidence')
    reported_assignment = cycle['status'] == 'reported_source_assignment'
    if reported_assignment:
        if not isinstance(cycle['assignment_text'], str) or not cycle['assignment_text'].strip() or not cycle['claims']:
            fail('reported source assignment requires retained claims and text')
    elif cycle['assignment_text'] is not None:fail('unresolved cycle must not select a resolved assignment')
    keys = set()
    for claim in cycle['claims']:
        require_notes(claim)
        if not claim['text'].strip():fail('source cycle claims require attributed text')
        for role in ('condition', 'classification'):
            if not support(claim['evidence'], role):fail('source claims require primary ' + role + ' evidence')
        key = (claim['scope'], claim['phase'], claim['occurrence'])
        if key in keys:fail('reworded or aliased cycle claim is not another source statement')
        keys.add(key)
    if cycle['status'] == 'not_reported_in_inspected_source' and cycle['claims']:
        fail('known source statements cannot be hidden as wholly unreported')
    origins = {(c['phase'], c['occurrence']) for c in cycle['claims'] if c['scope'] == 'reported_crystallinity_origin'}
    inputs = {(c['phase'], c['occurrence']) for c in cycle['claims'] if c['scope'] == 'reported_enthalpy_scan'}
    def differs(a, b):
        return a[0] != b[0] or a[1] is not None and b[1] is not None and a[1] != b[1]
    tension = (any(differs(a, b) for a in origins for b in inputs)
               or any(differs(a, b) for a in origins for b in origins))
    if tension and cycle['status'] != 'conflicting_source_statements':
        fail('retained incompatible origin/input claims require explicit unresolved conflict')
    if cycle['status'] == 'conflicting_source_statements':
        if len(keys) < 2 or not tension:
            fail('conflict requires distinct and incompatible known source cycle claims')
        claim_locators = {e['locator'] for c in cycle['claims'] for e in c['evidence']
                          if e['source_id'] == source and e['url'] == document}
        if not any(support(item['evidence'], 'source_discrepancy')
                   and claim_locators <= {e['locator'] for e in item['evidence']
                       if e['source_id'] == source and e['url'] == document}
                   for item in prop['source_discrepancies']):
            fail('conflict requires corresponding primary-document source discrepancy')


def cell_key(signature):
    value = json.loads(signature);value['conditions'] = {}
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
