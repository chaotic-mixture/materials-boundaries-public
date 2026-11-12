"""Source-qualified flexural DMA channels and explicit measurement coordinates."""
from copy import deepcopy
from decimal import Decimal
import json

QUANTITIES = {
    'dma_flexural_storage_modulus': ('GPa_dma_flexural_storage', 'pressure'),
    'dma_flexural_loss_tangent': ('ratio_dma_flexural_loss_tangent', 'dimensionless'),
}
FACT_FIELDS = ('apparatus_and_bending_geometry', 'strain_amplitude_and_convention',
               'temperature_program_and_control', 'frequency_protocol',
               'signal_channel_and_reduction', 'specimen_preparation_and_lineage',
               'replication_and_statistics', 'conditioning_and_corrections')
LABEL_KEYS = (*(f'code_{q}' for q in QUANTITIES), 'dma_definition', 'dma_reference_notice',
              'dma_measurement_temperature', 'dma_oscillation_frequency',
              *(f'dma_{name}' for name in FACT_FIELDS))


def schema_branches(definitions, base, *, text, obj, array, ref):
    evidence = array(ref('evidence'), 1)
    unknown_status = {'type': 'string', 'enum': ['not_reported_in_inspected_source', 'not_verified']}
    definitions['dma_fact'] = {'oneOf': [
        obj(dict(status={'const': 'reported'}, text=text, evidence=evidence, notes=text)),
        obj(dict(status=unknown_status, text={'type': 'null'}, evidence=evidence, notes=text)),
    ]}
    definitions['dma_definition'] = obj({
        'basis': {'const': 'source_reported_flexural_DMA'},
        **{name: ref('dma_fact') for name in FACT_FIELDS}, 'evidence': evidence, 'notes': text,
    })
    nonnegative = {'type': 'string', 'maxLength': 49,
        'pattern': r'^(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])'}
    positive = {**nonnegative, 'pattern': r'^(?=[0-9.]*[1-9])(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])'}
    signed = {'type': 'string', 'maxLength': 50,
        'pattern': r'^-?(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])'}
    for field, number, unit, spelling in (
            ('dma_measurement_temperature', signed, {'enum': ['degC', 'K']}, text),
            ('dma_oscillation_frequency', positive, {'const': 'Hz'}, {'const': 'Hz'})):
        definitions[field] = {'oneOf': [
            obj(dict(status={'const': 'reported'}, number=number, value_text=text,
                     unit_code=unit, unit_text=spelling, evidence=evidence, notes=text)),
            obj({'status': unknown_status,
                 **{key: {'type': 'null'} for key in ('number', 'value_text', 'unit_code', 'unit_text')},
                 'evidence': evidence, 'notes': text}),
        ]}
    branches = []
    for quantity, (unit, dimension) in QUANTITIES.items():
        prefix = quantity
        scalar = next(deepcopy(v) for v in definitions['reported_value']['oneOf']
                      if v['properties']['kind'].get('const') == 'scalar')
        scalar['properties'].update(unit_code={'const': unit}, number=nonnegative)
        definitions[prefix + '_reported_value'] = scalar

        def specialize(value):
            if isinstance(value, dict):
                if value.get('$ref') == '#/$defs/reported_measure':
                    value['$ref'] = '#/$defs/' + prefix + '_reported_measure'
                fields = value.get('properties', {})
                if 'enum' in fields.get('unit_code', {}):fields['unit_code'] = {'const': unit}
                for child in value.values():specialize(child)
            elif isinstance(value, list):
                for child in value:specialize(child)
        for old, suffix in (('reported_measure', '_reported_measure'), ('uncertainty', '_uncertainty')):
            definitions[prefix + suffix] = deepcopy(definitions[old])
            specialize(definitions[prefix + suffix])
        branch = deepcopy(base);fields = branch['properties']
        fields.update(quantity={'const': quantity}, quantity_dimension={'const': dimension},
            reported_value=ref(prefix + '_reported_value'), dma_definition=ref('dma_definition'),
            dma_measurement_temperature=ref('dma_measurement_temperature'),
            dma_oscillation_frequency=ref('dma_oscillation_frequency'),
            uncertainty={'anyOf': [ref(prefix + '_uncertainty'), {'type': 'null'}]},
            evidence_kind={'const': 'published_experimental_reference'},
            reporting_basis={'const': 'reported_summary'},
            determination_basis={'const': 'source_reports_measurement'}, density_basis={'type': 'null'})
        fields.pop('derivation', None)
        fields['method_definition']['properties']['type'] = {'const': 'source_reported_conventional'}
        fields['method_definition']['properties']['extraction_window'] = {'type': 'null'}
        branch['required'].extend(['dma_definition', 'dma_measurement_temperature', 'dma_oscillation_frequency'])
        branches.append(branch)
    return branches


def validate(prop, fail, numeric_token_matches, validate_temperature):
    if prop['quantity'] not in QUANTITIES:return
    if Decimal(prop['reported_value']['number']) < 0:fail(prop['id'], 'DMA central result must be nonnegative')
    if prop['conditions']['direction']['status'] == 'not_applicable':
        fail(prop['id'], 'a scalar DMA channel does not establish orientation inapplicability')
    source, document = prop['source_id'], prop['source_document']['url']
    definition = prop['dma_definition']
    for name, fact in [('dma_definition', definition), *((n, definition[n]) for n in FACT_FIELDS)]:
        if not fact['notes'].strip():fail(prop['id'], 'DMA facts require scope notes')
        known = fact.get('status') == 'reported'
        if known and not fact['text'].strip():fail(prop['id'], 'reported DMA facts require text')
        for role in (('method', 'condition') if known or name == 'dma_definition' else ('condition',)):
            if not any(e['source_id'] == source and e['url'] == document and role in e['supports'] for e in fact['evidence']):
                fail(prop['id'], 'DMA facts require primary inspected-document ' + role + ' evidence')
    cells = {e['locator'] for e in prop['evidence']
             if e['source_id'] == source and e['url'] == document and 'reported_value' in e['supports']}
    for field in ('dma_measurement_temperature', 'dma_oscillation_frequency'):
        coordinate = prop[field]
        if not coordinate['notes'].strip():fail(prop['id'], 'DMA coordinates require scope notes')
        if not any(e['source_id'] == source and e['url'] == document and 'condition' in e['supports'] for e in coordinate['evidence']):
            fail(prop['id'], 'DMA coordinate requires primary inspected-document condition evidence')
        if coordinate['status'] != 'reported':continue
        if not any(e['source_id'] == source and e['url'] == document and e['locator'] in cells
                   and {'condition', 'classification'} <= set(e['supports']) for e in coordinate['evidence']):
            fail(prop['id'], 'reported DMA coordinate must bind selected source cell')
        if field == 'dma_measurement_temperature':
            validate_temperature({'kind': 'scalar', **{k: coordinate[k] for k in ('number', 'value_text', 'unit_code', 'unit_text')}}, prop['id'] + '.' + field)
        elif Decimal(coordinate['number']) <= 0 or not numeric_token_matches(coordinate['value_text'], coordinate['number']):
            fail(prop['id'], 'DMA cyclic frequency must preserve a positive source Hz value')


def cell_key(signature):
    """Source cell identity outranks annotation or condition-text enrichment."""
    value = json.loads(signature)
    value['conditions'] = {}
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
