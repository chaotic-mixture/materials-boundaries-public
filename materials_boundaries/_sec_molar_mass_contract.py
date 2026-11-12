"""Source-qualified SEC moments and reported dispersity, never chromatogram computation."""
from copy import deepcopy
from decimal import Decimal
import json

MOMENTS = ('sec_weight_average_molar_mass', 'sec_number_average_molar_mass')
DISPERSITY = 'sec_source_reported_molar_mass_dispersity'
QUANTITIES = (*MOMENTS, DISPERSITY)
MOMENT_UNITS = ('g_per_mol_sec_molar_mass', 'kg_per_mol_sec_molar_mass',
                'ten5_g_per_mol_sec_molar_mass')
RATIO_UNIT = 'ratio_sec_molar_mass_dispersity'
UNITS = (*MOMENT_UNITS, RATIO_UNIT)
MOMENT_METHOD = 'source_reported_sec_molar_mass'
RATIO_METHOD = 'source_reported_sec_molar_mass_dispersity'
PROFILE = 'source_sec_molar_mass_dispersity_v1'
FACT_FIELDS = ('sec_column_and_geometry_source_notation',
               'sample_solution_preparation_and_concentration', 'eluent_flow_and_temperature',
               'detector_types_pairing_and_optical_configuration', 'calibrants_and_calibration_pathway',
               'dn_dc_and_concentration_reduction', 'chromatogram_integration_and_moment_reduction',
               'sample_conditioning_storage_and_history', 'replication_and_statistics',
               'instrument_corrections_and_quality_controls')
VERIFICATIONS = ('value_precision', 'identity_cell', 'protocol_equivalence', 'reuse_license')
ORIGIN_STATUSES = ('direct_primary_report', 'original_attribution_unresolved',
                   'explicitly_reproduced_from_cited_work')
LABEL_KEYS = (*(f'code_{q}' for q in QUANTITIES), 'code_' + MOMENT_METHOD,
              'code_' + RATIO_METHOD, 'sec_definition', 'sec_notice',
              'sec_reported_common_context', 'sec_actual_original_context', 'sec_origin',
              'sec_cited_original', 'sec_original_result', 'sec_measurement_basis',
              'sec_dispersity_derivation', 'sec_reported_formula', 'sec_source_cell', 'code_sec_original_verified',
              *(f'code_{s}' for s in ORIGIN_STATUSES),
              'code_source_reported_relative_calibration', 'code_source_reported_absolute_reduction',
              *(f'sec_{n}' for n in FACT_FIELDS), *(f'sec_{n}' for n in VERIFICATIONS))


def schema_branches(definitions, base, *, text, https, obj, array, ref):
    evidence = array(ref('evidence'), 1)
    unknown = {'enum': ['not_reported_in_inspected_source', 'not_verified']}
    definitions['sec_fact'] = {'oneOf': [
        obj(dict(status={'const': 'reported'}, text=text, evidence=evidence, notes=text)),
        obj(dict(status=unknown, text={'type': 'null'}, evidence=evidence, notes=text)),
    ]}
    definitions['sec_context'] = obj({**{n: ref('sec_fact') for n in FACT_FIELDS}})
    definitions['sec_source_cell'] = obj(dict(table_id=text, row_key=text, column_key=text,
                                              evidence=evidence, notes=text))
    # Preserve the shared source-text control/surrogate and strict-end rules;
    # the lookahead adds DOI syntax without weakening that common contract.
    doi = deepcopy(text)
    doi.update(maxLength=256, pattern=r'^(?=10\.[0-9]{4,9}/\S+(?![\s\S]))' + text['pattern'][1:])
    original_url = deepcopy(https);original_url['maxLength'] = 4096
    definitions['sec_original_reference'] = obj(dict(
        doi=doi,
        title=text, year={'type': 'integer', 'minimum': 1600, 'maximum': 9999},
        evidence=evidence, notes=text))
    original_fields = ('original_source_id', 'document_url', 'sha256', 'table_id', 'row_key', 'column_key')
    definitions['sec_original_result'] = {'oneOf': [
        obj(dict(status={'const': 'verified'}, original_source_id=text,
                 document_url=original_url,
                 sha256={'type': 'string', 'pattern': r'^[0-9a-f]{64}$', 'maxLength': 64},
                 table_id=text, row_key=text, column_key=text, evidence=evidence, notes=text)),
        obj({'status': unknown, **{n: {'type': 'null'} for n in original_fields},
             'evidence': evidence, 'notes': text}),
    ]}
    definitions['sec_origin'] = obj(dict(
        status={'enum': list(ORIGIN_STATUSES)},
        original_reference={'anyOf': [ref('sec_original_reference'), {'type': 'null'}]},
        original_result=ref('sec_original_result'),
        verification=obj({n: ref('sec_fact') for n in VERIFICATIONS}), evidence=evidence, notes=text))
    definitions['sec_basis'] = {'oneOf': [
        obj(dict(status={'enum': ['source_reported_relative_calibration', 'source_reported_absolute_reduction']},
                 text=text, evidence=evidence, notes=text)),
        obj(dict(status={'const': 'not_verified'}, text={'type': 'null'}, evidence=evidence, notes=text)),
    ]}
    definitions['sec_definition'] = obj(dict(
        source_result_cell=ref('sec_source_cell'), origin=ref('sec_origin'),
        reported_common_context=ref('sec_context'), actual_original_result_context=ref('sec_context'),
        measurement_basis=ref('sec_basis'), evidence=evidence, notes=text))
    definitions['sec_dispersity_derivation'] = obj(dict(
        schema_version={'const': '1.0.0'}, profile_id={'const': PROFILE},
        profile_version={'const': '1.0.0'}, executor={'const': 'source_reported_only'},
        formula_family={'const': 'source_weight_over_number_average_molar_mass'},
        numerator_role={'const': MOMENTS[0]}, denominator_role={'const': MOMENTS[1]},
        reported_formula=ref('sec_fact'), evidence=evidence, notes=text))
    positive = {'type': 'string', 'maxLength': 49,
                'pattern': r'^(?=[0-9.]*[1-9])(?:0|[1-9][0-9]{0,23})(?:\.[0-9]{1,24})?(?![\s\S])'}
    scalar = next(deepcopy(v) for v in definitions['reported_value']['oneOf']
                  if v['properties']['kind'].get('const') == 'scalar')
    branches = []
    for name, quantities, units, method, dimension, derived in [
        ('sec_moment', MOMENTS, MOMENT_UNITS, MOMENT_METHOD, 'mass_per_amount', False),
        ('sec_dispersity', (DISPERSITY,), (RATIO_UNIT,), RATIO_METHOD, 'dimensionless', True),
    ]:
        value = deepcopy(scalar);value['properties'].update(number=deepcopy(positive), unit_code={'enum': list(units)})
        definitions[name + '_reported_value'] = value
        def specialize(node):
            if isinstance(node, dict):
                if node.get('$ref') == '#/$defs/reported_measure':node['$ref'] = '#/$defs/' + name + '_reported_measure'
                fields = node.get('properties', {})
                if 'enum' in fields.get('unit_code', {}):fields['unit_code'] = {'enum': list(units)}
                for child in node.values():specialize(child)
            elif isinstance(node, list):
                for child in node:specialize(child)
        for old, suffix in [('reported_measure', '_reported_measure'), ('uncertainty', '_uncertainty')]:
            definitions[name + suffix] = deepcopy(definitions[old]);specialize(definitions[name + suffix])
        branch = deepcopy(base);fields = branch['properties']
        fields.update(quantity={'enum': list(quantities)}, quantity_dimension={'const': dimension},
                      reported_value=ref(name + '_reported_value'), density_basis={'type': 'null'},
                      evidence_kind={'const': 'published_measurement_derived_reference' if derived else 'published_experimental_reference'},
                      determination_basis={'const': 'source_reports_calculation' if derived else 'source_reports_measurement'},
                      reporting_basis={'const': 'reported_summary'}, sec_definition=ref('sec_definition'),
                      uncertainty={'anyOf': [ref(name + '_uncertainty'), {'type': 'null'}]})
        fields['method_definition']['properties']['type'] = {'const': method}
        fields['method_definition']['properties']['extraction_window'] = {'type': 'null'}
        branch['required'].append('sec_definition')
        if derived:
            fields['derivation'] = ref('sec_dispersity_derivation');branch['required'].append('derivation')
        else:
            fields.pop('derivation', None)
        branches.append(branch)
    return branches


def applies(prop):
    d = prop.get('derivation')
    return (prop.get('quantity') in QUANTITIES or 'sec_definition' in prop
            or prop.get('method_definition', {}).get('type') in (MOMENT_METHOD, RATIO_METHOD)
            or isinstance(d, dict) and d.get('profile_id') == PROFILE)


def validate(prop, identity=None, sources=None):
    if not applies(prop):return
    def fail(message):raise ValueError(prop['id'] + ': ' + message)
    ratio = prop['quantity'] == DISPERSITY
    if (prop['quantity'] not in QUANTITIES or prop['method_definition']['type'] != (RATIO_METHOD if ratio else MOMENT_METHOD)
            or prop['evidence_kind'] != ('published_measurement_derived_reference' if ratio else 'published_experimental_reference')
            or prop['determination_basis'] != ('source_reports_calculation' if ratio else 'source_reports_measurement')):
        fail('SEC quantity/method and source measurement/derived roles must agree')
    value = Decimal(prop['reported_value']['number'])
    if not value.is_finite() or value <= 0 or ratio and value < 1:
        fail('SEC result outside admitted source domain; do not clamp anomalies')
    if (not ratio and 'derivation' in prop) or ratio and (
            prop.get('derivation', {}).get('profile_id') != PROFILE
            or prop.get('derivation', {}).get('executor') != 'source_reported_only'):
        fail('SEC dispersity profile and source-only executor must agree')
    source, document = prop['source_id'], prop['source_document']['url']
    def require(item, roles, sid=source, url=document):
        if not item['notes'].strip():fail('SEC provenance needs scope notes')
        for role in roles:
            if not any(e['source_id'] == sid and e['url'] == url and role in e['supports'] for e in item['evidence']):
                fail('SEC provenance needs inspected-document ' + role + ' evidence')
    def fact(item, sid=source, url=document):
        reported = item['status'] == 'reported'
        require(item, ('method', 'condition') if reported else ('condition',), sid, url)
        if reported and not item['text'].strip():fail('reported SEC fact needs source text')
    definition = prop['sec_definition'];require(definition, ('method', 'classification'))
    cell = definition['source_result_cell'];require(cell, ('reported_value', 'classification'))
    for n in ('table_id', 'row_key', 'column_key'):
        if not cell[n].strip() or cell[n] != cell[n].strip():fail('source cell address must be stable and nonblank')
    origin = definition['origin'];require(origin, ('classification',))
    ref, original = origin['original_reference'], origin['original_result']
    if origin['status'] != 'original_attribution_unresolved' and ref is None:
        fail('known SEC origin requires its explicit original citation')
    if origin['status'] == 'original_attribution_unresolved' and ref is not None:
        fail('retained original attribution cannot be hidden as wholly unresolved')
    if ref is not None:
        require(ref, ('classification',))
        if not ref['title'].strip():fail('original reference needs a title')
    verified = original['status'] == 'verified'
    if verified:
        if ref is None:fail('verified original result needs its original citation')
        sid, url = original['original_source_id'], original['document_url']
        require(original, ('reported_value', 'classification'), sid, url)
        for n in ('table_id', 'row_key', 'column_key'):
            if not original[n].strip() or original[n] != original[n].strip():fail('verified original cell address must be stable')
        if sources is not None:
            if sid not in sources:fail('verified original source must be registered')
            record = sources[sid]
            if url not in record['urls'] or (record.get('doi') or '').casefold() != ref['doi'].casefold():
                fail('verified original DOI/document must match its registered source')
            if (origin['verification']['reuse_license']['status'] == 'reported'
                    and record['license']['status'] != 'explicit_reuse_license_verified'):
                fail('reported original reuse license requires verified registered original rights')
    else:
        sid, url = source, document;require(original, ('condition',))
    if origin['status'] == 'direct_primary_report':
        if not verified or original['original_source_id'] != source or original['document_url'] != document or original['sha256'] != prop['source_document']['sha256']:
            fail('direct report must be its verified inspected original document')
        if any(original[n] != cell[n] for n in ('table_id', 'row_key', 'column_key')):
            fail('direct report original cell must equal inspected cell')
    for item in origin['verification'].values():
        if item['status'] == 'reported' and not verified:fail('unverified original cannot assert original verification')
        fact(item, sid if item['status'] == 'reported' else source, url if item['status'] == 'reported' else document)
    protocol_verified = verified and origin['verification']['protocol_equivalence']['status'] == 'reported'
    for item in definition['reported_common_context'].values():fact(item)
    for item in definition['actual_original_result_context'].values():
        if item['status'] == 'reported' and not protocol_verified:
            fail('common reproducing method cannot become actual original result conditions')
        fact(item, sid if item['status'] == 'reported' else source, url if item['status'] == 'reported' else document)
    if not protocol_verified:
        for name, item in prop['conditions'].items():
            items = [v['fact'] for v in item] if name == 'additional_conditions' else [item]
            if any(v['status'] in ('reported', 'not_applicable') for v in items):
                fail('unverified original protocol requires unknown actual property conditions')
    basis = definition['measurement_basis']
    if basis['status'] != 'not_verified':
        if not protocol_verified or not basis['text'].strip():fail('reported reduction basis needs verified original protocol and source text')
        require(basis, ('method', 'classification'), sid, url)
    else:require(basis, ('condition',))
    if ratio:
        d = prop['derivation'];require(d, ('method', 'classification'));fact(d['reported_formula'])
        if d['reported_formula']['status'] != 'reported':fail('source dispersity requires its explicit ordered Mw/Mn formula')


def validate_state_context(prop, state):
    if prop['quantity'] not in QUANTITIES:return
    o = prop['sec_definition']['origin']
    if o['original_result']['status'] == 'verified' and o['verification']['protocol_equivalence']['status'] == 'reported':return
    for name in ('processing', 'temper_or_heat_treatment', 'conditioning', 'porosity', 'orientation'):
        if state['state'][name]['status'] in ('reported', 'not_applicable'):
            raise ValueError(prop['id'] + ': unverified SEC original protocol cannot inherit physical specimen history')


def guard_cell(prop, seen, identity_id):
    """Reject parallel revisions and hold uncertain second publication representations."""
    if prop['quantity'] not in QUANTITIES:return
    d = prop['sec_definition'];cell = d['source_result_cell'];origin = d['origin']
    key = 'sec_cell:' + json.dumps([prop['material_state_id'], prop['quantity'], prop['source_document']['url'],
                                   *(cell[n] for n in ('table_id', 'row_key', 'column_key'))], ensure_ascii=False)
    if key in seen:raise ValueError(prop['id'] + ': same SEC source cell must be revised, not duplicated')
    seen.add(key)
    original = origin['original_result'];ref = origin['original_reference']
    if ref is None:return
    doi = ref['doi'].casefold()
    address = [original[n] for n in ('table_id', 'row_key', 'column_key')] if original['status'] == 'verified' else None
    if address is not None:
        confirmed = 'sec_original:' + json.dumps([doi, prop['quantity'], address], ensure_ascii=False)
        if confirmed in seen:raise ValueError(prop['id'] + ': same confirmed original SEC datum cannot be duplicated across publications')
        seen.add(confirmed)
    record = [identity_id, prop['quantity'], doi, prop['source_document']['url'], address]
    for item in tuple(seen):
        if not item.startswith('sec_origin_record:'):continue
        old = json.loads(item[len('sec_origin_record:'):])
        if old[:3] == record[:3] and old[3] != record[3] and (old[4] is None or address is None):
            raise ValueError(prop['id'] + ': possible duplicate original SEC datum; resolve before a second publication representation')
    seen.add('sec_origin_record:' + json.dumps(record, ensure_ascii=False))
