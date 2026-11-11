"""Closed source-applied conversion profiles; never evaluator rules.

Decimal arithmetic audits deposited values without replacing them. The profile
registry can be extended only with an explicit scientific contract and tests.
"""
from decimal import Decimal, localcontext
import re

PROFILE = 'gwdd_airdry_sg_to_basic_density_v2_1'
TISSUE = 'collection_woody_tissue_anatomy_unspecified'
BASIS = 'oven_dry_mass_over_fresh_or_water_saturated_volume'
FORMULA_ID = 'gwdd_v2_1_basic_from_airdry_sg'
FORMULA_EXPRESSION = 'deposited basic density = source-rounded (air-dry specific gravity * 0.8281316 * water-density convention 1 g/cm^3)'
ROUNDING_AUDIT_POLICY = 'absolute_difference_less_than_half_deposited_rounding_increment; halfway_ties_held'
INPUT_BASIS = 'air_dry_mass_over_air_dry_volume_relative_to_water_same_conditions'
# Quantity/method coupling is declarative; no row-specific scientific exceptions.
PROFILES = {
    PROFILE: {'quantity': 'basic_wood_density', 'method': 'source_reported_empirical_conversion',
              'density_basis': BASIS, 'coefficient': '0.8281316', 'nominal_moisture_percent': '12',
              'rounding_increment': '0.01', 'input_quantity': 'air_dry_specific_gravity'},
}


def _wood_definitions(text, decimal, https, null, obj, array, enum):
    sha = {'type': 'string', 'pattern': r'^[0-9a-f]{64}$', 'maxLength': 64}
    integer = {'type': 'integer', 'minimum': 1}
    wfo = {'type': 'string', 'pattern': r'^wfo-[0-9]{10}$', 'maxLength': 14}
    evidence = array({'$ref': '#/$defs/evidence'}, 1)
    original = obj({'taxon_id': wfo, 'scientific_name': text, 'authorship': text,
                    'rank': {'const': 'species'}, 'status': enum(('Accepted', 'Synonym'))})
    chain = obj({'source_name_wfo_id': wfo, 'wfo_chain_ids': array(wfo, 1, True),
                 'accepted_terminal_wfo_id': wfo, 'error': null})
    file_locator = obj({'source_id': text, 'release_doi': text, 'release_version': text,
                        'file_id': text, 'file_name': text, 'sha256': sha, 'url': https,
                        'record_id': text, 'data_record_1based': integer,
                        'physical_line_start': integer, 'physical_line_end': integer,
                        'fields': array(text, 1, True)})
    return {
        'canonical_taxon': obj({
            'identity_key': text, 'tissue_scope': {'const': TISSUE}, 'accepted_taxon_id': wfo,
            'accepted_name': text, 'accepted_authority': text, 'accepted_full_name': text,
            'original_full_name': text, 'original_name_records': array(original, 1),
            'source_to_accepted_chains': array(chain, 1), 'mapping_method': text,
            'mapping_disposition': {'const': 'reviewed_supported_historical_backbone'},
            'rank': {'const': 'species'}, 'hybrid': {'const': False},
            'backbone': obj({'doi': text, 'version': text, 'archive_sha256': sha,
                             'archive_member': text, 'accepted_record_1based': integer,
                             'accepted_physical_line_start': integer, 'accepted_physical_line_end': integer}),
            'source_taxonomic_reference': text,
        }),
        'derivation': obj({
            'schema_version': {'const': '1.0.0'},
            'kind': {'const': 'conversion_derived_estimate_from_measured_input'},
            'profile_id': enum(PROFILES), 'profile_version': {'const': '1.0.0'},
            'formula_id': {'const': FORMULA_ID},
            'input': obj({'quantity': {'const': 'air_dry_specific_gravity'}, 'basis': {'const': INPUT_BASIS}, 'number': decimal,
                          'value_text': text, 'unit_code': {'const': 'dimensionless'},
                          'source_property_label': text, 'deposited_quantity_label': text,
                          'evidence_type': {'const': 'source_reported_measured_input'}}),
            'deposited_output': obj({'number': decimal, 'unit_code': {'const': 'g/cm^3'},
                                     'rounding_increment': decimal}),
            'si_output': obj({'number': decimal, 'unit_code': {'const': 'kg/m^3'},
                              'rounding_increment': decimal}),
            'formula': obj({'expression': {'const': FORMULA_EXPRESSION}, 'coefficient': decimal,
                            'coefficient_source_id': text, 'coefficient_source_field': text,
                            'calibration_source_id': text, 'basis_convention_source_id': text,
                            'water_density_convention_g_cm3': decimal,
                            'nominal_conversion_moisture_percent': decimal,
                            'measured_specimen_moisture_percent': null,
                            'calibration_context': text, 'rounding_audit_policy': {'const': ROUNDING_AUDIT_POLICY},
                            'moisture_percent_basis': {'const': 'water_mass_over_oven_dry_mass'}}),
            'specimen_scope': obj({'accession': text, 'selection': {'const': 'selected_collection_accession'},
                                   'tissue_subtype': null, 'sample_anatomical_location': null,
                                   'orientation': null, 'exact_test_temperature': null,
                                   'exact_moisture': null, 'treatment': null,
                                   'collection_date': null, 'measurement_date': null,
                                   'missingness_reason': text}),
            'counts': obj({'plants_sampled_as_reported': text, 'verified_independent_plants': null,
                           'collection_accessions_selected': {'const': 1},
                           'v1_mechanically_eligible_source_record_count': integer,
                           'count_scope_note': text}),
            'uncertainty': obj({'record_measurement_uncertainty': null,
                                'source_method_uncertainty_note': text,
                                'conversion_uncertainty': null, 'conversion_uncertainty_note': text,
                                'species_variation': null, 'rounding_is_uncertainty': {'const': False}}),
            'provenance': obj({'original': file_locator, 'deposited': file_locator,
                               'reviewed_batch_sha256': sha, 'reviewed_candidate_key': text,
                               'original_citation': text, 'normalized_citation': text,
                               'license_identifiers': array(text, 1, True),
                               'attribution': text, 'source_scope_note': text}),
            'evidence': evidence,
        }),
    }


def canonical_identity_key(identity):
    taxon = identity.get('canonical_taxon')
    return taxon['identity_key'] if taxon else 'catalog:' + identity['id']


def validate_taxon(identity):
    taxon = identity.get('canonical_taxon')
    if taxon is None:
        return
    if identity['category'] != 'natural':
        raise ValueError('canonical biological tissue identity must be natural')
    key = 'wfo:' + taxon['accepted_taxon_id'] + ':' + taxon['tissue_scope']
    if taxon['identity_key'] != key:
        raise ValueError('canonical taxon identity key mismatch')
    def normalized(value):
        return re.sub(r'[.\s]', '', value)
    def hybrid(value):
        return '×' in value or bool(re.search(r'(^|\s)[xX](?=\s|$)', value))
    for key in ('original_full_name', 'accepted_name', 'accepted_full_name'):
        if hybrid(taxon[key]):
            raise ValueError('hybrid name is outside admitted species-only scope')
    if normalized(taxon['accepted_full_name']) != normalized(taxon['accepted_name'] + ' ' + taxon['accepted_authority']):
        raise ValueError('accepted full name/authority mismatch')
    records = taxon['original_name_records']
    chains = taxon['source_to_accepted_chains']
    if len(records) != 1 or len(chains) != 1:
        raise ValueError('ambiguous original full-name mapping is held')
    record, chain = records[0], chains[0]
    if normalized(record['scientific_name'] + ' ' + record['authorship']) != normalized(taxon['original_full_name']):
        raise ValueError('original name/authority mismatch')
    if (chain['source_name_wfo_id'] != record['taxon_id']
            or chain['wfo_chain_ids'][0] != record['taxon_id']
            or chain['wfo_chain_ids'][-1] != taxon['accepted_taxon_id']
            or chain['accepted_terminal_wfo_id'] != taxon['accepted_taxon_id']):
        raise ValueError('original-to-accepted taxon chain mismatch')
    from urllib.parse import urlsplit
    reference = urlsplit(taxon['source_taxonomic_reference'])
    if reference.scheme not in {'http', 'https'} or not reference.netloc:
        raise ValueError('original taxonomic reference must retain a valid HTTP(S) URL')
    backbone = taxon['backbone']
    if backbone['accepted_physical_line_end'] < backbone['accepted_physical_line_start']:
        raise ValueError('invalid taxonomic backbone line range')


def _validate_empirical_derivation(prop, identity=None, sources=None):
    """Audit the declared conversion without inventing measurement precision."""
    derived = prop.get('derivation')
    empirical = prop['method_definition']['type'] == 'source_reported_empirical_conversion'
    if empirical != (derived is not None):
        raise ValueError('empirical conversion requires its typed derivation and vice versa')
    if prop['density_basis'] == BASIS and not empirical:
        raise ValueError('basic-density mass/volume basis requires empirical basic-density profile')
    if derived is None:
        return
    profile = PROFILES[derived['profile_id']]
    if (prop['quantity'] != profile['quantity'] or prop['density_basis'] != profile['density_basis']
            or prop['evidence_kind'] != 'published_measurement_derived_reference'
            or prop['determination_basis'] != 'source_reports_calculation'
            or prop['summary_statistic'] != 'reported_value'
            or prop['reporting_basis'] != 'not_stated'):
        raise ValueError('empirical conversion quantity/basis/evidence/scope mismatch')
    source, deposited, si, formula = (derived[k] for k in ('input', 'deposited_output', 'si_output', 'formula'))
    if (formula['coefficient'] != profile['coefficient']
            or formula['nominal_conversion_moisture_percent'] != profile['nominal_moisture_percent']
            or formula['water_density_convention_g_cm3'] != '1'
            or deposited['rounding_increment'] != profile['rounding_increment']):
        raise ValueError('conversion profile coefficient/assumption mismatch')
    if source['value_text'] != source['number']:
        raise ValueError('original specific-gravity string must be retained exactly')
    with localcontext() as context:
        context.prec = 80
        original = Decimal(source['number'])
        value = Decimal(deposited['number'])
        increment = Decimal(deposited['rounding_increment'])
        if original <= 0 or value <= 0:
            raise ValueError('source conversion inputs/output must be positive')
        product = original * Decimal(formula['coefficient']) * Decimal(formula['water_density_convention_g_cm3'])
        # Equality is rejected: no source-supported tie-breaking rule is asserted.
        if abs(value - product) >= increment / 2 or value % increment != 0:
            raise ValueError('deposited conversion fails documented rounding-resolution audit')
        if Decimal(si['number']) != value * 1000 or Decimal(si['rounding_increment']) != increment * 1000:
            raise ValueError('SI value must convert the deposited rounded value exactly')
    result = prop['reported_value']
    if (result['kind'] != 'scalar' or result['number'] != deposited['number']
            or result['value_text'] != deposited['number'] or result['unit_code'] != 'g/cm^3'):
        raise ValueError('reported result must retain deposited g/cm3 value/string')
    if prop['uncertainty'] is not None or prop['uncertainty_status'] != 'not_reported_in_inspected_source':
        raise ValueError('record-level conversion uncertainty is not established')
    if prop['sample_count']['value'] is not None or prop['sample_count']['relation'] != 'not_reported':
        raise ValueError('source record/plants count cannot become validated independent sample n')
    for name in ('temperature', 'direction', 'conditioning'):
        if prop['conditions'][name]['status'] != 'not_reported_in_inspected_source':
            raise ValueError('source-method climate/nominal moisture cannot become specimen condition')
    for name in ('original', 'deposited'):
        loc = derived['provenance'][name]
        if loc['physical_line_end'] < loc['physical_line_start']:
            raise ValueError('invalid source physical line range')
    if identity is not None:
        if not identity.get('canonical_taxon'):
            raise ValueError('biological conversion requires canonical taxon provenance')
        if derived['provenance']['reviewed_candidate_key'] != 'wood-' + identity['canonical_taxon']['accepted_taxon_id']:
            raise ValueError('derived property and canonical taxon disagree')

    if sources is not None:
        references = {item['source_id'] for item in derived['evidence']}
        required = {formula['coefficient_source_id'], formula['calibration_source_id'], formula['basis_convention_source_id']}
        required.update(derived['provenance'][name]['source_id'] for name in ('original', 'deposited'))
        if not required <= set(sources) or not required <= references:
            raise ValueError('derivation source dependencies must resolve through explicit evidence')
        for key in ('coefficient_source_id', 'calibration_source_id', 'basis_convention_source_id'):
            if not any(item['source_id'] == formula[key] and 'method' in item['supports'] for item in derived['evidence']):
                raise ValueError('formula source dependency needs explicit method evidence')
        for name in ('original', 'deposited'):
            loc = derived['provenance'][name]
            source = sources[loc['source_id']]
            if loc['url'] not in source['urls'] or loc['release_doi'] != source['doi']:
                raise ValueError('file provenance URL/DOI differs from its source registry')
            license_id = source['license']['identifier']
            if license_id not in derived['provenance']['license_identifiers']:
                raise ValueError('source license not propagated to derived property')
            if not any(item['source_id'] == loc['source_id'] and item['url'] == loc['url']
                       for item in derived['evidence']):
                raise ValueError('file provenance must resolve to matching explicit source evidence')
        deposited_loc = derived['provenance']['deposited']
        if (prop['source_id'] != deposited_loc['source_id']
                or prop['source_document']['url'] != deposited_loc['url']
                or prop['source_document']['sha256'] != deposited_loc['sha256']):
            raise ValueError('deposited result must bind its primary source document and hash')


def validate_baseline_exclusions(materials):
    """Conservative reviewed taxon/tissue exclusions, not new legacy taxonomy.

    A historical author abbreviation may remain unreconciled. These mappings
    block duplicate counting only, without replacing old identities or names.
    """
    import hashlib
    import json
    from importlib.resources import files
    raw = files('materials_boundaries').joinpath('data', 'wood_baseline_crosswalk_v2.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != 'cddecb6f388814c0e85f64ab580cb9e551673240d2a182929a48e40b94079afa':
        raise ValueError('reviewed baseline taxon/tissue exclusion artifact changed')
    crosswalk = json.loads(raw)
    present = {row['id'] for row in materials['identities']}
    excluded = {taxon for row in crosswalk if row['baseline_identity_id'] in present
                and row['disposition'] == 'exclude_all_these_accepted_ids_from_new_wood_count'
                for taxon in row['accepted_wfo_ids']}
    for identity in materials['identities']:
        taxon = identity.get('canonical_taxon')
        if taxon and taxon['tissue_scope'] == TISSUE and taxon['accepted_taxon_id'] in excluded:
            raise ValueError('canonical imported tissue duplicates a retained baseline identity')


TRANSPORT_PROFILE='thermal_transport_product_unpaired_context_v1'
TRANSPORT_METHOD='source_reported_thermal_transport_product'
TRANSPORT_KIND='source_reported_product_from_measurements'
TRANSPORT_EXPRESSION='lambda = alpha * cp * rho'
TRANSPORT_ROLES=('thermal_diffusivity','mass_specific_heat_capacity','mass_density')
TRANSPORT_UNKNOWNS=('actual_paired_input_values','actual_specimen_pairing','density_temperature_alignment',
          'input_aggregation_order','input_covariance','source_uncertainty_propagation_method')

def _thermal_product_definition(text,https,null,obj,array,enum):
    """No input numbers or compute flags can masquerade as verified raw inputs."""
    evidence=array({'$ref':'#/$defs/evidence'},1)
    inputs={q:obj({'quantity':{'const':q},'role':{'const':'source_context_not_verified_actual_input'},
                    'source_property_label':text,'evidence':evidence}) for q in TRANSPORT_ROLES}
    return obj({'schema_version':{'const':'1.0.0'},'profile_id':{'const':TRANSPORT_PROFILE},
        'profile_version':{'const':'1.0.0'},'kind':{'const':TRANSPORT_KIND},
        'formula':obj({'expression':{'const':TRANSPORT_EXPRESSION},'evidence':evidence}),
        'contextual_inputs':obj(inputs),
        'input_provenance':obj({**{q:null for q in TRANSPORT_UNKNOWNS},'unknown_scope_note':text}),
        'software_calculation_performed':{'const':False},
        'software_uncertainty_propagation_performed':{'const':False}})

def _validate_thermal_product(prop):
    """Semantic half;caller must first apply the closed schema definition."""
    derived=prop.get('derivation')
    product=prop['method_definition']['type']==TRANSPORT_METHOD
    tagged=isinstance(derived,dict) and derived.get('profile_id')==TRANSPORT_PROFILE
    if product!=tagged:raise ValueError('source thermal product requires its profile and vice versa')
    if not product:return
    if (prop['quantity']!='thermal_conductivity' or prop['density_basis'] is not None or
        prop['evidence_kind']!='published_measurement_derived_reference' or
        prop['determination_basis']!='source_reports_calculation'):
        raise ValueError('source thermal product quantity,basis or provenance class mismatch')
    if prop['reported_value']['unit_code'] not in ('W/(m*K)','mW/(m*K)'):
        raise ValueError('source thermal product output must retain conductivity units')
    sid=prop['source_id'];url=prop['source_document']['url']
    for group,tag in [(derived['formula']['evidence'],'method')]+[(derived['contextual_inputs'][q]['evidence'],'reported_value') for q in TRANSPORT_ROLES]:
        if not group or any(e['source_id']!=sid or e['url']!=url or tag not in e['supports'] for e in group):
            raise ValueError('product formula and contextual summaries require same primary-document evidence')
    # No Decimal operation,product,rounding audit,source refit or error propagation.


def definitions(text,decimal,https,null,obj,array,enum):
    result=_wood_definitions(text,decimal,https,null,obj,array,enum)
    result['derivation']={'oneOf':[result['derivation'],_thermal_product_definition(text,https,null,obj,array,enum),_thermal_fit_definition(text,https,null,obj,array,enum)]}
    return result


def validate_derivation(prop,identity=None,sources=None):
    derived=prop.get('derivation')
    if (prop['quantity']==FIT_QUANTITY or prop['method_definition']['type']==FIT_METHOD or
        isinstance(derived,dict) and derived.get('profile_id')==FIT_PROFILE):
        _validate_thermal_fit(prop,sources)
        return
    if (prop['method_definition']['type']==TRANSPORT_METHOD or
        isinstance(derived,dict) and derived.get('profile_id')==TRANSPORT_PROFILE):
        _validate_thermal_product(prop)
        return
    _validate_empirical_derivation(prop,identity,sources)


FIT_PROFILE='thermal_temperature_decay_fit_with_cited_method_v1'
FIT_METHOD='source_reported_thermal_response_fit'
FIT_QUANTITY='thermal_response_characteristic_time'
FIT_EXPRESSION='T(t)=Tf+(T0-Tf)*exp(-t/tau_c)'
FIT_UNKNOWNS=('raw_temperature_curves','fit_window','optimizer_and_weighting',
    'baseline_temperature_treatment','fit_aggregation_order','per_cell_fit_count')
FIT_PHASES=('post_stretching_hold','post_retraction_recovery')
FIT_REGIMES=('natural_convection','forced_convection')

def _thermal_fit_definition(text,https,null,obj,array,enum):
    evidence=array({'$ref':'#/$defs/evidence'},1)
    sha={'type':'string','pattern':r'^[0-9a-f]{64}$','maxLength':64}
    return obj({'schema_version':{'const':'1.0.0'},'profile_id':{'const':FIT_PROFILE},
        'profile_version':{'const':'1.0.0'},'kind':{'const':'source_reported_temperature_response_fit'},
        'model':{'const':FIT_EXPRESSION},
        'definition':{'const':'absolute_temperature_deviation_to_fluid_decays_to_initial_divided_by_e'},
        'primary_delegation':obj({'primary_doi':text,'cited_source_id':text,'cited_doi':text,'cited_document_url':https,'cited_document_sha256':sha,'evidence':evidence}),
        'method_reference':obj({'source_id':text,'doi':text,'url':https,'sha256':sha,
            'inspected_on':{'type':'string','format':'date','pattern':r'^\d{4}-\d{2}-\d{2}$'},
            'inspection_scope':text,'use_role':{'const':'method_definition_only_not_current_protocol_or_numeric_input'},'evidence':evidence}),
        'model_context':obj({'fluid_temperature':{'const':'reference_model_assumes_constant'},
            'heat_transfer_coefficient':{'const':'reference_model_assumes_uniform_constant'},
            'radiation':{'const':'reference_model_neglects_radiation'},
            'actual_applicability_certified':{'const':False}}),
        'unverified_fit_inputs':obj({**{k:null for k in FIT_UNKNOWNS},'unknown_scope_note':text}),
        'software_fit_performed':{'const':False},'software_inverse_performed':{'const':False}})

def _validate_thermal_fit(prop,sources=None):
    derived=prop.get('derivation')
    if not (prop['quantity']==FIT_QUANTITY and prop['method_definition']['type']==FIT_METHOD
            and isinstance(derived,dict) and derived.get('profile_id')==FIT_PROFILE):
        raise ValueError('thermal response time requires its fit method and profile and vice versa')
    if (prop['evidence_kind']!='published_measurement_derived_reference' or
            prop['determination_basis']!='source_reports_calculation' or prop['density_basis'] is not None):
        raise ValueError('thermal response fit classification or basis mismatch')
    value=prop['reported_value']
    if value['kind']!='scalar' or value['unit_code'] not in ('s','ms'):
        raise ValueError('thermal response fit requires scalar time units')
    primary=prop['source_id'];document=prop['source_document'];delegation=derived['primary_delegation'];reference=derived['method_reference']
    if (document['hash_status']!='recorded' or document['sha256'] is None or
        reference['source_id']==primary or reference['url']==document['url'] or reference['sha256']==document['sha256'] or
        delegation['cited_source_id']!=reference['source_id'] or delegation['cited_doi']!=reference['doi'] or
        delegation['cited_document_url']!=reference['url'] or delegation['cited_document_sha256']!=reference['sha256']):
        raise ValueError('thermal fit needs distinct inspected documents and an explicit cited-method binding')
    def bound(items,sid,url,tag):
        if not items or any(e['source_id']!=sid or e['url']!=url or tag not in e['supports'] for e in items):
            raise ValueError('thermal fit evidence source,document or role mismatch')
    bound(delegation['evidence'],primary,document['url'],'method')
    bound(reference['evidence'],reference['source_id'],reference['url'],'method')
    bound(prop['thermal_response_phase']['evidence'],primary,document['url'],'condition')
    convection=prop['thermal_convection']
    if convection['status']=='reported':bound(convection['evidence'],primary,document['url'],'condition')
    if (derived['software_fit_performed'] is not False or derived['software_inverse_performed'] is not False
        or derived['model_context']['actual_applicability_certified'] is not False):
        raise ValueError('source fit contract does not perform or certify calculations')
    if sources is not None:
        if primary not in sources or reference['source_id'] not in sources:
            raise ValueError('thermal fit both source roles must resolve')
        if (sources[primary].get('doi')!=delegation['primary_doi'] or
            sources[reference['source_id']].get('doi')!=reference['doi'] or
            document['url'] not in sources[primary]['urls'] or
            reference['url'] not in sources[reference['source_id']]['urls']):
            raise ValueError('thermal fit DOI or document differs from source registry')
    # No fit,inverse,unit conversion,half-life or numeric example reconstruction.
