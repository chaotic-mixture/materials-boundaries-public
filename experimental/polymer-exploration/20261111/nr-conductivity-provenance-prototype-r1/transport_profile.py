"""Isolated source-calculation contract prototype;not imported by production."""
PROFILE='thermal_transport_product_unpaired_context_v1'
METHOD='source_reported_thermal_transport_product'
KIND='source_reported_product_from_measurements'
EXPRESSION='lambda = alpha * cp * rho'
ROLES=('thermal_diffusivity','mass_specific_heat_capacity','mass_density')
UNKNOWNS=('actual_paired_input_values','actual_specimen_pairing','density_temperature_alignment',
          'input_aggregation_order','input_covariance','source_uncertainty_propagation_method')

def definition(text,https,null,obj,array,enum):
    """No input numbers or compute flags can masquerade as verified raw inputs."""
    evidence=array({'$ref':'#/$defs/evidence'},1)
    inputs={q:obj({'quantity':{'const':q},'role':{'const':'source_context_not_verified_actual_input'},
                    'source_property_label':text,'evidence':evidence}) for q in ROLES}
    return obj({'schema_version':{'const':'1.0.0'},'profile_id':{'const':PROFILE},
        'profile_version':{'const':'1.0.0'},'kind':{'const':KIND},
        'formula':obj({'expression':{'const':EXPRESSION},'evidence':evidence}),
        'contextual_inputs':obj(inputs),
        'input_provenance':obj({**{q:null for q in UNKNOWNS},'unknown_scope_note':text}),
        'software_calculation_performed':{'const':False},
        'software_uncertainty_propagation_performed':{'const':False}})

def validate(prop):
    """Semantic half;caller must first apply the closed schema definition."""
    derived=prop.get('derivation')
    product=prop['method_definition']['type']==METHOD
    tagged=isinstance(derived,dict) and derived.get('profile_id')==PROFILE
    if product!=tagged:raise ValueError('source thermal product requires its profile and vice versa')
    if not product:return
    if (prop['quantity']!='thermal_conductivity' or prop['density_basis'] is not None or
        prop['evidence_kind']!='published_measurement_derived_reference' or
        prop['determination_basis']!='source_reports_calculation'):
        raise ValueError('source thermal product quantity,basis or provenance class mismatch')
    if prop['reported_value']['unit_code'] not in ('W/(m*K)','mW/(m*K)'):
        raise ValueError('source thermal product output must retain conductivity units')
    sid=prop['source_id'];url=prop['source_document']['url']
    for group,tag in [(derived['formula']['evidence'],'method')]+[(derived['contextual_inputs'][q]['evidence'],'reported_value') for q in ROLES]:
        if not group or any(e['source_id']!=sid or e['url']!=url or tag not in e['supports'] for e in group):
            raise ValueError('product formula and contextual summaries require same primary-document evidence')
    # No Decimal operation,product,rounding audit,source refit or error propagation.
