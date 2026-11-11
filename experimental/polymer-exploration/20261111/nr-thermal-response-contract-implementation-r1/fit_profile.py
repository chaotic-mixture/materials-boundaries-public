"""Concrete cited-method fit contract,to be copied into the reviewed runtime."""
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
