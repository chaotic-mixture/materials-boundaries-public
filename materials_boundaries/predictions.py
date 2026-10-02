"""Published discrete computational predictions, isolated from bound evaluation.

No atomistic calculation, strain interpolation, uncertainty estimate or automatic
cross-study matching is performed. A comparison is an explicitly curated group.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from importlib.resources import files
import json
import math
import re
from urllib.parse import urlsplit

from .catalog import CatalogLookupError, read_catalog
from .validation import ValidationError
from .silicon_predictions import (SILICON_FAMILY, SILICON_QUANTITY, SILICON_PROTOCOL_CONTRACT,
    SILICON_RECORD_CONTRACT, SILICON_GROUP_CONTRACT, validate_silicon_record, critical_strain_evidence, instability_mode_evidence)

LANGUAGES = ('en', 'zh', 'ja', 'de')
FAMILY = 'shimanek_v2_pure_alias_12atom_v1'
DEFAULT_GROUP = 'shimanek_v2_table2_ni_al_co'
ELEMENTS = set('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split())
ID = re.compile(r'^[a-z][a-z0-9_]*$')
DECIMAL = re.compile(r'^[0-9]+\.[0-9]+$')


class PredictionError(ValidationError):
    """Invalid reported-prediction data or unsupported comparison."""


def canonical_json(value, *, pretty=False):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      indent=2 if pretty else None, separators=None if pretty else (',', ':'))


def require(condition, message):
    if not condition:
        raise PredictionError(message)


def _keys(value, expected, label):
    require(isinstance(value, dict) and set(value) == set(expected), label+': unexpected or missing fields')


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _finite_positive(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value > 0
    except OverflowError:
        return False


def _names(value):
    return isinstance(value, dict) and set(value) == set(LANGUAGES) and all(_text(s) for s in value.values())


def _list_index(records, label, *, nonempty=True):
    require(isinstance(records, list) and (bool(records) or not nonempty), label+': list required')
    index = {}
    for record in records:
        require(isinstance(record, dict), label+': object required')
        rid = record.get('id')
        require(isinstance(rid, str) and ID.fullmatch(rid) and rid not in index, label+': duplicate or invalid ID')
        index[rid] = record
    return index


def _evidence(entries, source_id):
    require(isinstance(entries, list) and bool(entries), 'evidence: nonempty list required')
    for entry in entries:
        _keys(entry, ('source_id', 'locator', 'url', 'supports'), 'evidence')
        require(entry['source_id'] == source_id and _text(entry['locator']), 'evidence source or locator mismatch')
        url = entry['url']
        require(isinstance(url, str) and urlsplit(url).scheme == 'https' and bool(urlsplit(url).netloc), 'evidence: HTTPS URL required')
        require(isinstance(entry['supports'], list) and bool(entry['supports']) and all(_text(s) for s in entry['supports']), 'evidence supports required')


def value_evidence(record):
    require(isinstance(record.get('quantity'),str), 'strength evidence quantity must be a string')
    support = {'ideal_shear_strength':'reported_ideal_shear_strength', SILICON_QUANTITY:'reported_tensile_first_instability_strength'}.get(record['quantity'])
    require(support is not None, 'unsupported strength evidence quantity')
    entries = [e for e in record['evidence'] if support in e['supports']]
    require(len(entries) == 1, 'exactly one primary reported-strength evidence entry required')
    return entries[0]


def method_evidence(protocol):
    entries = [e for e in protocol['evidence'] if 'cell construction' in e['supports']]
    require(len(entries) == 1, 'exactly one cell-construction method evidence entry required')
    return entries[0]


# This closed scientific family is independent of mutable catalog data. Another
# geometry, cell or known-state protocol requires deliberate schema/guard review.
PROTOCOL_CONTRACT = {'source_sections': ['2.1', '2.2', '3.1'],
 'property': 'ideal_shear_strength',
 'property_interpretation': 'Maximum shear stress along the reported '
                            'constrained-relaxation strain path',
 'evidence_type': 'published_computational_prediction',
 'material_representation': 'periodic_atomic_supercell_model',
 'commercial_alloy_grade': False,
 'structure': {'host_lattice': 'fcc Ni',
               'initial_cell_geometry': 'orthorhombic',
               'atoms_per_cell': 12,
               'atomic_layers_along_111': 3,
               'substitution_location': 'one Ni site within the shear plane '
                                        'for Ni11X'},
 'geometry': {'slip_plane_miller_indices': [1, 1, 1],
              'slip_direction_indices': [1, 1, -2],
              'slip_direction_display': '[1,1,-2]',
              'transverse_in_plane_direction_indices': [-1, 1, 0],
              'normal_direction_indices': [1, 1, 1]},
 'loading': {'type': 'pure_alias_shear',
             'shear_parameter_sign': 'positive',
             'deformation_matrix_as_printed': [['1', '0', '0'],
                                               ['0', '1', '0'],
                                               ['epsilon', '0', '1']],
             'matrix_convention_note': 'Retain the source matrix as printed; '
                                       'do not silently transpose it based on '
                                       'a different vector convention.',
             'strain_definition': 'engineering shear displacement divided by '
                                  'supercell height',
             'displacement_regime': 'initial relative displacement of one '
                                    'atomic layer, then relaxation',
             'fixed_quantity': 'prescribed shear angle',
             'relaxed_quantities': ['atomic positions',
                                    'non-prescribed cell parameters'],
             'geometry_optimizer': 'Gadget',
             'peak_search': 'incremental shear; additional calculations near '
                            'the stress maximum/drop',
             'full_loading_history_or_strain_step_schedule_verified': False},
 'calculation': {'framework': 'static DFT constrained-geometry calculations',
                 'software': 'VASP',
                 'pseudopotential_method': 'PAW',
                 'exchange_correlation_reported': 'GGA parameterized by Perdew '
                                                  'et al., reference 43 (Phys. '
                                                  'Rev. B 46 (1992) 6671-6687)',
                 'exchange_correlation_label_caution': 'Do not substitute PBE. '
                                                       'The paper identifies '
                                                       'its GGA through '
                                                       'reference 43; raw '
                                                       'input tags have not '
                                                       'been inspected.',
                 'plane_wave_cutoff_eV': 350,
                 'k_mesh': [9, 8, 7],
                 'k_mesh_center': 'Gamma',
                 'electronic_self_consistency_tolerance_eV_per_supercell': 5e-06,
                 'electronic_smearing': {'scheme': 'Methfessel-Paxton',
                                         'width_eV': 0.2,
                                         'is_physical_temperature': False},
                 'framework_status': 'Classification from the reported '
                                     'constrained-geometry DFT procedure; no '
                                     'numeric physical temperature inferred'},
 'numerical_controls': {'strength_peak_convergence_reported_GPa': 0.08,
                        'strength_peak_convergence_semantics': 'Author-reported '
                                                               'convergence '
                                                               'criterion, not '
                                                               'a standard '
                                                               'deviation, '
                                                               'confidence '
                                                               'interval, or '
                                                               'per-record '
                                                               'error bar',
                        'non_imposed_stress_component_threshold_GPa': 0.15,
                        'atomic_force_threshold_eV_per_angstrom': 0.03,
                        'statistical_uncertainty': None,
                        'systematic_model_error': None},
 'state_fields': {'physical_temperature_K': None,
                  'physical_temperature_status': 'not_verified_in_inspected_content',
                  'pressure_GPa': None,
                  'pressure_status': 'not_verified_as_a_scalar_thermodynamic_state_in_inspected_content',
                  'normal_stress_condition': 'Other relaxed stress components '
                                             'reported below 0.15 GPa; do not '
                                             'replace this residual threshold '
                                             'with an exact external pressure '
                                             'value.',
                  'magnetic_state': None,
                  'spin_polarization': None,
                  'magnetic_state_status': 'not_verified_in_inspected_content',
                  'static_DFT_is_not_a_temperature_measurement': True},
 'family': 'shimanek_v2_pure_alias_12atom_v1',
 'version': '1.0.0'}

RECORD_KEYS = ('id', 'formula', 'cell_composition', 'stoichiometry_in_model_cell', 'source_table_label', 'source_value_string', 'value_GPa', 'unit', 'reported_decimal_places', 'precision_note', 'source_id', 'source_table', 'source_pdf_page_1_based', 'protocol_id', 'evidence_type', 'material_representation', 'commercial_alloy_grade', 'uncertainty_GPa', 'universal_upper_bound', 'cell_composition_status', 'version', 'name', 'quantity', 'evaluation_support', 'comparison_group_id', 'names', 'evidence', 'verification', 'uncertainty_reason')
RECORD_CONTRACT = {'version': '1.0.0',
 'quantity': 'ideal_shear_strength',
 'evaluation_support': 'reported_discrete_prediction',
 'evidence_type': 'published_computational_prediction',
 'material_representation': 'periodic_atomic_supercell_model',
 'commercial_alloy_grade': False,
 'uncertainty_GPa': None,
 'universal_upper_bound': False,
 'unit': 'GPa',
 'verification': {'status': 'source_table_visually_checked',
                  'independent_scientific_review': False,
                  'raw_inputs_audited': False}}
GROUP_KEYS = ('id', 'source_id', 'protocol_id', 'record_ids', 'verification_level', 'basis', 'qualifier', 'unknown_conditions_equivalent', 'raw_inputs_audited', 'cross_study_comparison_allowed', 'excluded_interpretations', 'names')
GROUP_CONTRACT = {'verification_level': 'reported_method_only',
 'unknown_conditions_equivalent': False,
 'raw_inputs_audited': False,
 'cross_study_comparison_allowed': False,
 'excluded_interpretations': ['experimental observation',
                              'commercial alloy grade',
                              'ultimate tensile strength',
                              'hardness',
                              'macroscopic yield strength',
                              'universal rigorous strength upper bound',
                              'complete stability envelope over all modes']}


def validate_prediction_catalog(catalog, sources=None):
    """Dependency-free semantic guard, with no inferred unknown-state equality."""
    _keys(catalog, ('schema_version', 'records', 'protocols', 'comparison_groups'), 'computational_predictions')
    require(catalog['schema_version'] in ('1.0.0','1.1.0'), 'unsupported prediction schema')
    records = _list_index(catalog['records'], 'predictions')
    protocols = _list_index(catalog['protocols'], 'protocols')
    groups = _list_index(catalog['comparison_groups'], 'comparison groups')
    all_ids = [*records, *protocols, *groups]
    require(len(all_ids) == len(set(all_ids)), 'prediction, protocol and group IDs must be distinct')
    sources = _list_index((read_catalog('sources') if sources is None else sources)['records'], 'sources')
    require(not set(all_ids) & set(sources), 'prediction metadata ID collides with a source')
    for protocol in protocols.values():
        require(isinstance(protocol.get('family'),str), 'prediction protocol family must be a string')
        contract = {FAMILY:PROTOCOL_CONTRACT, SILICON_FAMILY:SILICON_PROTOCOL_CONTRACT}.get(protocol.get('family'))
        require(contract is not None, 'unsupported prediction protocol family')
        require(catalog['schema_version']=='1.1.0' or protocol['family']==FAMILY, 'silicon requires prediction schema 1.1.0')
        _keys(protocol, (*contract, 'id', 'source_id', 'evidence', 'verification', 'unknown_field_reasons'), 'protocol')
        for key, expected in contract.items():
            require(canonical_json(protocol[key]) == canonical_json(expected), 'unsupported protocol contract: '+key)
        sid = protocol['source_id']
        require(isinstance(sid, str) and sid in sources, 'unresolved protocol source')
        _evidence(protocol['evidence'], sid)
        method_evidence(protocol)
        verification = protocol['verification']
        _keys(verification, ('status', 'raw_inputs_audited', 'independent_scientific_review', 'gaps'), 'protocol verification')
        require(verification['status'] == 'published_method_inspected' and verification['raw_inputs_audited'] is False and verification['independent_scientific_review'] is False, 'unsupported protocol verification')
        require(isinstance(verification['gaps'], list) and bool(verification['gaps']) and all(_text(s) for s in verification['gaps']), 'protocol gaps required')
        reasons = protocol['unknown_field_reasons']
        _keys(reasons, ('magnetic_state', 'temperature', 'pressure', 'uncertainty', 'raw_protocol'), 'unknown reasons')
        require(all(_text(s) for s in reasons.values()), 'all unknown reasons required')
    for record in records.values():
        silicon = record.get('quantity') == SILICON_QUANTITY
        extra = ('direction','critical_engineering_strain','first_instability','reported_strength_definition','descriptions') if silicon else ()
        _keys(record, (*RECORD_KEYS,*extra), 'prediction')
        contract = SILICON_RECORD_CONTRACT if silicon else RECORD_CONTRACT
        for key, value in contract.items():
            require(canonical_json(record[key]) == canonical_json(value), 'unsupported prediction contract: '+key)
        require(_names(record['names']) and _text(record['name']), 'four authored prediction names required')
        pid, sid, gid = record['protocol_id'], record['source_id'], record['comparison_group_id']
        require(isinstance(pid, str) and pid in protocols and isinstance(sid, str) and sid in sources and protocols[pid]['source_id'] == sid, 'prediction protocol/source mismatch')
        require(isinstance(gid, str) and gid in groups, 'unresolved comparison group')
        require(protocols[pid]['family'] == (SILICON_FAMILY if silicon else FAMILY), 'record quantity/protocol family mismatch')
        if silicon:
            validate_silicon_record(record)
        composition = record['stoichiometry_in_model_cell']
        if not silicon:
            require(isinstance(composition, dict) and composition and set(composition) <= ELEMENTS and all(type(n) is int and n > 0 for n in composition.values()) and sum(composition.values()) == 12, 'invalid 12-atom composition')
            if composition == {'Ni':12}:
                require((record['formula'], record['cell_composition'], record['source_table_label'], record['cell_composition_status']) == ('Ni','Ni12','Ni, pure','inferred_from_shared_12_atom_host_setup'), 'pure Ni identity mismatch')
            else:
                require(composition.get('Ni') == 11 and len(composition) == 2, 'Ni11X substitution required')
                solute = next(k for k in composition if k != 'Ni')
                require((record['formula'], record['cell_composition'], record['source_table_label'], record['cell_composition_status']) == ('Ni11'+solute,'Ni11'+solute,solute,'explicit_Ni11X_model_from_methods'), 'Ni11X identity mismatch')
        value, string, places = record['value_GPa'], record['source_value_string'], record['reported_decimal_places']
        require(_finite_positive(value), 'finite positive strength required')
        require(isinstance(string, str) and DECIMAL.fullmatch(string) and type(places) is int and 1 <= places <= 12 and len(string.split('.')[1]) == places, 'source decimal precision mismatch')
        try:
            require(Decimal(string) == Decimal(str(value)), 'source decimal and numeric value differ')
        except InvalidOperation as exc:
            raise PredictionError('invalid source decimal') from exc
        require(type(record['source_pdf_page_1_based']) is int and record['source_pdf_page_1_based'] > 0 and _text(record['source_table']), 'source table locator required')
        require(_text(record['precision_note']) and _text(record['uncertainty_reason']), 'precision and uncertainty explanations required')
        _evidence(record['evidence'], sid)
        value_evidence(record)
    for group in groups.values():
        silicon = group.get('comparison_axis') == 'loading_direction_family'
        _keys(group, (*GROUP_KEYS, *(('comparison_axis',) if silicon else ())), 'comparison group')
        contract = SILICON_GROUP_CONTRACT if silicon else GROUP_CONTRACT
        for key, expected in contract.items():
            require(canonical_json(group[key]) == canonical_json(expected), 'unsupported comparison semantics: '+key)
        require(_names(group['names']) and _text(group['basis']) and _text(group['qualifier']), 'group names and published-method basis required')
        members = group['record_ids']
        require(isinstance(members, list) and bool(members) and all(isinstance(r, str) and r in records for r in members) and len(set(members)) == len(members), 'unknown or duplicate comparison member')
        require(isinstance(group['protocol_id'], str) and group['protocol_id'] in protocols and group['source_id'] == protocols[group['protocol_id']]['source_id'], 'group protocol/source mismatch')
        require(protocols[group['protocol_id']]['family'] == (SILICON_FAMILY if silicon else FAMILY), 'comparison axis/protocol family mismatch')
        if silicon:
            directions=[canonical_json(records[rid].get('direction',{}).get('family_indices')) for rid in members]
            require(len(directions)==len(set(directions)), 'duplicate direction in silicon comparison')
        for rid in members:
            record = records[rid]
            require(record['comparison_group_id'] == group['id'] and record['protocol_id'] == group['protocol_id'] and record['source_id'] == group['source_id'], 'mixed protocol, source or group comparison')
    for record in records.values():
        require(record['id'] in groups[record['comparison_group_id']]['record_ids'], 'prediction not included in its explicit group')
    return catalog


def query_predictions(*, record_id=None, query=None, source_id=None, quantity=None):
    for name, value in (('record_id',record_id),('source_id',source_id),('quantity',quantity)):
        require(value is None or _text(value), name+': nonempty string required')
    require(query is None or isinstance(query, str), 'query: string required')
    catalog = validate_prediction_catalog(read_catalog('computational_predictions'))
    records = catalog['records']
    if record_id is not None:
        records = [r for r in records if r['id'] == record_id]
        if not records:
            raise CatalogLookupError('unknown predictions ID: '+record_id)
    terms = (query or '').casefold().split()
    def matches(r):
        fields = [r[k] for k in ('id','name','formula','cell_composition','quantity','evidence_type','source_id','protocol_id','comparison_group_id')] + list(r['names'].values())
        return (source_id is None or r['source_id'] == source_id) and (quantity is None or r['quantity'] == quantity) and all(any(t in f.casefold() for f in fields) for t in terms)
    # Metadata is retained verbatim; group record_ids refer to the full catalog,
    # never a false claim that a filtered result is a new complete comparison.
    catalog['records'] = [r for r in records if matches(r)]
    return catalog


def prediction_labels(lang='en', *, family=FAMILY):
    require(lang in LANGUAGES, 'unsupported language')
    labels=json.loads(files('materials_boundaries').joinpath('data/prediction_locales.json').read_text(encoding='utf-8'))['languages'][lang]
    require(family in (FAMILY,SILICON_FAMILY), 'unsupported prediction label family')
    if family==SILICON_FAMILY:
        labels.update({k.removeprefix('silicon_'):v for k,v in list(labels.items()) if k.startswith('silicon_')})
    return labels


def render_predictions(catalog, lang='en'):
    if any(r['quantity']==SILICON_QUANTITY for r in catalog['records']):
        return _render_mixed_predictions(catalog,lang)
    t = prediction_labels(lang)
    lines = [t['catalog']+': '+str(len(catalog['records'])), t['model_notice'], t['comparison_notice']]
    if not catalog['records']:
        lines.append(t['empty'])
    for r in catalog['records']:
        evidence=value_evidence(r)
        protocol=next(p for p in catalog['protocols'] if p['id']==r['protocol_id'])
        method=method_evidence(protocol)
        lines.extend(['',r['id'],r['names'][lang]+': '+r['source_value_string']+' GPa',
                      t['cell']+': '+r['cell_composition'],t['source_label']+': '+r['source_table_label'],
                      t['geometry']+': (111) [1,1,-2]',t['protocol']+': '+r['protocol_id'],
                      t['table']+': '+evidence['locator']+' | '+evidence['url'],
                      t['methods']+': '+method['locator']+' | '+method['url']])
    lines.extend([t[k] for k in ('unknown_notice','convergence_notice','precision_notice','review_notice')])
    return '\n'.join(lines)


REQUIRED_LABELS = frozenset(('title', 'subtitle', 'catalog', 'empty', 'command', 'plot', 'output', 'group', 'x_axis', 'cell', 'source_label', 'geometry', 'protocol', 'table', 'methods', 'details', 'model_notice', 'comparison_notice', 'unknown_notice', 'convergence_notice', 'precision_notice', 'review_notice', 'finite_cell_notice', 'points_notice', 'method_notice', 'source_notice', 'legend', 'quantity', 'value', 'unknown'))


def _render_mixed_predictions(catalog,lang):
    base=prediction_labels(lang)
    lines=[base['catalog']+': '+str(len(catalog['records']))]
    for r in catalog['records']:
        protocol=next(p for p in catalog['protocols'] if p['id']==r['protocol_id'])
        t=prediction_labels(lang,family=protocol['family'])
        evidence=value_evidence(r);method=method_evidence(protocol)
        silicon=r['quantity']==SILICON_QUANTITY
        geometry=r['direction']['display'] if silicon else '(111) [1,1,-2]'
        lines.extend(['',r['id'],r['names'][lang]+': '+r['source_value_string']+' GPa',
            t['model_notice'],t['comparison_notice'],t['cell']+': '+r['cell_composition'],
            t['source_label']+': '+r['source_table_label'],t['geometry']+': '+geometry,
            t['protocol']+': '+r['protocol_id'],t['table']+': '+evidence['locator']+' | '+evidence['url'],
            t['methods']+': '+method['locator']+' | '+method['url']])
        if silicon:
            strain=r['critical_engineering_strain'];se=critical_strain_evidence(r);me=instability_mode_evidence(r)
            lines.extend([r['descriptions'][lang],t['criterion_notice'],
                t['critical_strain']+': '+strain['source_value_string']+'% ('+str(strain['value'])+'; '+strain['unit']+')',
                t['table']+': '+se['locator']+' | '+se['url'],
                t['table']+': '+me['locator']+' | '+me['url']])
        lines.extend(t[k] for k in ('unknown_notice','convergence_notice','precision_notice','review_notice'))
    return '\n'.join(lines)

SILICON_LABEL_KEYS = frozenset(('title','subtitle','x_axis','geometry','model_notice','comparison_notice',
    'convergence_notice','finite_cell_notice','method_notice','points_notice','quantity','critical_strain',
    'direction','criterion_notice'))
REQUIRED_LABELS = REQUIRED_LABELS | frozenset('silicon_'+k for k in SILICON_LABEL_KEYS)
