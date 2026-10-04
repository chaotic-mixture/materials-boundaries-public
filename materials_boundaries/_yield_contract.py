"""Closed initial-yield criterion metadata; no stress or plasticity evaluator.

The literals below are independent of mutable catalog records. The sharp
comparison is original project algebra, not a source-printed theorem, material
strength guarantee, or independently peer-reviewed scientific result.
"""
import json

VON_MISES_RULE = 'von_mises_initial_yield_relation_v1'
TRESCA_RULE = 'tresca_initial_yield_relation_v1'
RATIO_RULE = 'tresca_von_mises_equivalent_stress_ratio_bound_v1'

_STRESS_CONVENTIONS = {
    'tensor': 'one_finite_real_symmetric_3D_Cauchy_stress_tensor_at_one_material_point',
    'sign': 'tension_positive',
    'principal_stresses': 'sigma1,sigma2,sigma3_are_eigenvalues_of_the_same_Cauchy_tensor',
    'ordering': 'sigma1>=sigma2>=sigma3_when_ordered_gaps_or_maximum_minus_minimum_are_used',
    'tensor_shear': 'ordinary_tensor_shear_components_not_doubled_engineering_strain_components',
    'contraction': 's:s=sum_i(s_ii^2)+2*sum_(i<j)(s_ij^2)',
    'deviator': 's=sigma-tr(sigma)*I/3; J2=(s:s)/2',
    'hydrostatic_sign': 'sigma=p*I_has_p=tr(sigma)/3; p_is_signed_hydrostatic_normal_stress_opposite_to_compression_positive_pressure',
}
_UNITS = {
    'sigma_principal_stresses_s_q_VM_q_T_tau_max_Y_and_dimensional_f': 'Pa',
    'J2': 'Pa^2',
    'q_over_Y_Lambda_equivalent_stress_ratio_and_load_multiplier': '1',
}
_NORMALIZATION = {
    'catalog': 'q_VM_and_q_T_are_dimensional_equivalent_stresses; f_VM=q_VM-Y; f_T=q_T-Y',
    'source_sigma_eq': 'sigma_eq_VM=q_VM/Y; sigma_eq_T=q_T/Y; both_are_dimensionless',
    'source_Lambda': 'Lambda_VM=f_VM/Y; Lambda_T=f_T/Y; both_are_dimensionless',
    'anchor': 'Giraldo-Londono_and_Paulino_2020_section_2_Eqs_(2.5),(2.8)-(2.11),(2.15)',
}
_PHYSICAL_INTERPRETATION = {
    'scope': 'only_for_interpretation_as_material_initial_yield_models_not_premises_of_the_mathematical_function_comparison',
    'continuum': 'ordinary_classical_Cauchy_stress_without_couple_stress_effects',
    'model_symmetry': 'phenomenological_isotropic_pressure_insensitive_tension_compression_symmetric',
    'kinematics': 'small_strain',
    'loading': 'quasistatic_rate_independent_initial_yield',
    'material_state': 'fixed_material_state_and_temperature',
    'calibration': 'Y>0_declared_uniaxial_tensile_yield_calibration_matching_state_temperature_rate_regime_stress_measure_and_yield_definition',
    'calibration_not_supplied': 'Y_is_neither_supplied_nor_inferred_from_elastic_constants',
    'common_calibration': 'same_Y_for_both_models_when_comparing_yield_thresholds',
    'shear_calibration_caution': 'equal_measured_pure_shear_calibration_gives_Y_T=2*tau_c_and_Y_VM=sqrt(3)*tau_c_so_same_Y_threshold_order_does_not_transfer',
    'proof_stress': 'a_proof_stress_requires_its_declared_offset_and_is_not_an_experimentally_demonstrated_sharp_onset',
    'surface': 'centered_initial_yield_surface_with_no_modeled_backstress_evolution',
    'no_post_yield_law': 'no_hardening_law_plastic_flow_direction_associated_flow_assertion_loading_unloading_integration_or_post_yield_strain',
    'scope_exclusions': [
        'anisotropic_yielding', 'tension_compression_asymmetry',
        'pressure_sensitive_yielding', 'porous_damage', 'evolving_material_state',
        'finite_strain_constitutive_evolution', 'cyclic_plasticity',
        'rate_dependent_flow',
    ],
    'hydrostatic_caution': 'function_invariance_does_not_establish_survival_against_hydrostatic_damage_cavitation_phase_change_or_other_failure',
    'admission_scope_attribution': 'deliberately_restricted_project_scope_not_an_assertion_that_each_source_states_every_exclusion',
}
_HYDROSTATIC = {
    'shift': 'adding_any_signed_hydrostatic_increment_h*I_leaves_both_equivalent_stresses_unchanged',
    'zero': 'q_VM=q_T=0_if_and_only_if_sigma=p*I',
    'ratio_at_zero': 'undefined_0/0; no_hydrostatic_ratio_value_or_unique_limit_is_assigned',
}
_ATTRIBUTION = {
    'function_definitions': 'Giraldo-Londono_and_Paulino_2020_and_selected_sound_Wierzbicki_2013_equations',
    'comparison_proof': 'original_project_algebra_not_a_separately_printed_source_theorem',
    'source_warnings': 'Wierzbicki_inspected_PDF_Eq_(12.22)_omits_the_square_root_and_Eq_(12.46)_repeats_a_principal_pair; neither_is_used; no_official_erratum_is_asserted',
    'rounded_comparison': 'Wierzbicki_printed_p_12-15_rounded_comparison_is_not_used_as_the_exact_bound_proof',
    'scientific_peer_review_certified': False,
    'native_language_scientific_review_performed': False,
}
_BOUNDARY = {
    'numerical_evaluator': False,
    'instance_premises_checked': False,
    'instance_satisfied_violated_unknown_states': False,
    'experimental_validation': False,
    'material_strength_or_safety_certification': False,
    'plasticity_solver': False,
    'measured_values_or_fitted_Y_supplied': False,
}
_MATH_ASSUMPTIONS = {
    'stress_tensor': 'finite_real_symmetric_3D_Cauchy_tensor_at_one_material_point',
    'stress_measure': 'same_Cauchy_tensor_and_same_stress_measure_for_all_functions_and_principal_values',
    'stress_sign': 'tension_positive',
    'shear_convention': 'ordinary_tensor_shear_components',
    'definitions': 'exact_unsmoothed_q_VM=sqrt(3*J2)_and_q_T=2*tau_max',
}


def _parameter(symbol, quantity, dimension, si_unit, meaning):
    return dict(symbol=symbol, quantity=quantity, dimension=dimension,
                si_unit=si_unit, meaning=meaning)


_SIGMA = _parameter('sigma', 'cauchy_stress_tensor', 'pressure', 'Pa',
                    'Finite real symmetric 3D Cauchy stress tensor at one material point; tension positive.')
_PRINCIPAL = _parameter('sigma1,sigma2,sigma3', 'principal_cauchy_stresses', 'pressure', 'Pa',
                        'Eigenvalues of sigma; ordered sigma1>=sigma2>=sigma3 when an ordered representation is used.')
_S = _parameter('s', 'deviatoric_cauchy_stress_tensor', 'pressure', 'Pa',
                's=sigma-tr(sigma)*I/3, with ordinary tensor shear components.')
_J2 = _parameter('J2', 'second_deviatoric_stress_invariant', 'pressure_squared', 'Pa^2',
                 'J2=(s:s)/2; s:s=sum_i(s_ii^2)+2*sum_(i<j)(s_ij^2).')
_QVM = _parameter('q_VM', 'von_mises_equivalent_stress', 'pressure', 'Pa',
                  'Dimensional nonnegative q_VM=sqrt(3*J2); not the source dimensionless sigma_eq.')
_QT = _parameter('q_T', 'tresca_equivalent_stress', 'pressure', 'Pa',
                 'Dimensional nonnegative maximum absolute principal-stress difference; q_T=2*tau_max.')
_Y = _parameter('Y', 'declared_uniaxial_tensile_yield_calibration', 'pressure', 'Pa',
                'Strictly positive declared uniaxial tensile yield calibration for the restricted model; no value is supplied or inferred.')


def _base_contract(kind):
    return {
        'kind': kind,
        'stress_conventions': _STRESS_CONVENTIONS,
        'units': _UNITS,
        'source_normalization': _NORMALIZATION,
        'physical_interpretation': _PHYSICAL_INTERPRETATION,
        'hydrostatic_behavior': _HYDROSTATIC,
        'source_attribution': _ATTRIBUTION,
        'catalog_boundary': _BOUNDARY,
    }


_VM_CONTRACT = dict(_base_contract('von_mises_initial_yield_relation'), **{
    'definition': {
        'equivalent_stress': 'q_VM=sqrt(3*J2)=sqrt(((sigma1-sigma2)^2+(sigma2-sigma3)^2+(sigma3-sigma1)^2)/2)',
        'yield_function': 'f_VM=q_VM-Y',
        'initial_boundary': 'f_VM=0',
        'model_classification': 'f_VM<0_is_inside_and_f_VM>0_is_outside_the_model_elastic_domain; no_specimen_state_is_evaluated',
        'pure_shear_substitution': 'tau_VM=Y/sqrt(3); symbolic_model_substitution_not_measured_shear_strength',
    },
    'proof_ids': ['Y1_stress_definitions_and_normalization'],
})
_T_CONTRACT = dict(_base_contract('tresca_initial_yield_relation'), **{
    'definition': {
        'equivalent_stress': 'q_T=max(abs(sigma1-sigma2),abs(sigma2-sigma3),abs(sigma3-sigma1))',
        'ordered_form': 'sigma1>=sigma2>=sigma3_implies_q_T=sigma1-sigma3=2*tau_max',
        'yield_function': 'f_T=q_T-Y',
        'initial_boundary': 'f_T=0',
        'model_classification': 'f_T<0_is_inside_and_f_T>0_is_outside_the_model_elastic_domain; no_specimen_state_is_evaluated',
        'pure_shear_substitution': 'tau_T=Y/2; symbolic_model_substitution_not_measured_shear_strength',
        'smoothing': 'exact_Tresca_no_smoothed_or_rounded_variant',
    },
    'proof_ids': ['Y1_stress_definitions_and_normalization'],
})
_RATIO_CONTRACT = dict(_base_contract('sharp_equivalent_stress_ratio_bound'), **{
    'mathematical_domain': {
        'ratio': 'nonhydrostatic_sigma; q_VM>0',
        'division_free': 'all_finite_real_symmetric_3D_Cauchy_tensors_including_hydrostatic_sigma',
        'material_fit_required': False,
        'physical_isotropy_required': False,
        'yield_calibration_Y_required': False,
    },
    'range': {
        'ratio': 'q_T/q_VM',
        'lower': {'value': 1, 'inclusive': True, 'attained': True,
                  'attained_when': 'a*b=0_and_a+b>0; two_principal_stresses_coincide'},
        'upper': {'exact_value': '2/sqrt(3)', 'inclusive': True, 'attained': True,
                  'attained_when': 'a=b>0; sigma2=(sigma1+sigma3)/2'},
        'division_free': 'q_VM<=q_T<=(2/sqrt(3))*q_VM',
        'actual_material_yield_bracket': False,
    },
    'original_proof': {
        'ordered_gaps': 'a=sigma1-sigma2>=0; b=sigma2-sigma3>=0',
        'equivalent_stresses': 'q_T=a+b; q_VM^2=a^2+a*b+b^2',
        'lower_difference_identity': 'q_T^2-q_VM^2=a*b>=0',
        'upper_difference_identity': '(4/3)*q_VM^2-q_T^2=(a-b)^2/3>=0',
        'square_roots': 'q_T_and_q_VM_are_nonnegative_so_the_squared_inequalities_imply_the_division_free_bound',
        'division': 'divide_by_q_VM_only_in_the_nonhydrostatic_branch',
        'sharpness': 'both_endpoint_conditions_are_attainable_nonhydrostatic_stress_states_so_neither_constant_can_be_tightened',
    },
    'synthetic_examples': {
        'lower_endpoint': 'sigma=diag(S,0,0), S>0: q_T=q_VM=S',
        'upper_endpoint': 'sigma=diag(T,0,-T), T>0: q_T=2*T; q_VM=sqrt(3)*T',
        'hydrostatic_shift': 'either_example_plus_any_h*I_has_the_same_function_values',
        'measured_data': False,
    },
    'conditional_loading_consequence': {
        'path': 'one_local_proportional_ray_sigma(lambda)=lambda*Sigma; lambda>=0; Sigma_nonhydrostatic',
        'calibration': 'one_common_fixed_Y>0; physical_yield_interpretation_also_requires_the_separate_model_scope',
        'thresholds': 'lambda_T=Y/q_T(Sigma); lambda_VM=Y/q_VM(Sigma)',
        'ratio': '1<=lambda_VM/lambda_T=q_T(Sigma)/q_VM(Sigma)<=2/sqrt(3)',
        'maximum_relative_excess': '2/sqrt(3)-1_approximately_15.47_percent_relative_to_the_Tresca_threshold',
        'hydrostatic_ray': 'neither_function_reaches_positive_Y; no_finite_threshold_ratio',
        'exclusions': 'no_automatic_extension_to_different_calibrations_residual_stress_paths_nonproportional_histories_or_evolving_plasticity',
        'interpretation': 'model_threshold_comparison_not_material_error_safety_margin_or_bracket_on_actual_yield',
    },
    'proof_ids': ['Y1_stress_definitions_and_normalization',
                  'Y2_sharp_comparison_and_endpoints', 'Y3_conditional_proportional_loading'],
})

YIELD_CONTRACTS = {
    VON_MISES_RULE: {
        'quantity': 'von_mises_equivalent_stress', 'direction': 'relation',
        'claim_type': 'model_relation', 'bound_kind': None,
        'quantity_dimension': 'pressure', 'si_unit': 'Pa',
        'evaluation_support': 'catalog_only',
        'formula_display': 'q_VM=sqrt(3*J2)=sqrt(((sigma1-sigma2)^2+(sigma2-sigma3)^2+(sigma3-sigma1)^2)/2); f_VM=q_VM-Y; initial yield: f_VM=0',
        'required_assumptions': dict(_MATH_ASSUMPTIONS, interpretation='physical_yield_meaning_requires_the_separate_closed_model_scope_and_Y>0'),
        'parameters': [_SIGMA, _PRINCIPAL, _S, _J2, _QVM, _Y,
                       _parameter('f_VM', 'von_mises_dimensional_yield_function', 'pressure', 'Pa',
                                  'Dimensional f_VM=q_VM-Y; the initial model boundary is f_VM=0.')],
        'yield_criterion_contract': _VM_CONTRACT,
    },
    TRESCA_RULE: {
        'quantity': 'tresca_equivalent_stress', 'direction': 'relation',
        'claim_type': 'model_relation', 'bound_kind': None,
        'quantity_dimension': 'pressure', 'si_unit': 'Pa',
        'evaluation_support': 'catalog_only',
        'formula_display': 'q_T=max(abs(sigma1-sigma2),abs(sigma2-sigma3),abs(sigma3-sigma1))=2*tau_max; f_T=q_T-Y; initial yield: f_T=0',
        'required_assumptions': dict(_MATH_ASSUMPTIONS, interpretation='physical_yield_meaning_requires_the_separate_closed_model_scope_and_Y>0'),
        'parameters': [_SIGMA, _PRINCIPAL, _QT,
                       _parameter('tau_max', 'maximum_shear_stress', 'pressure', 'Pa',
                                  'tau_max=(max(sigma_i)-min(sigma_i))/2=q_T/2.'),
                       _Y,
                       _parameter('f_T', 'tresca_dimensional_yield_function', 'pressure', 'Pa',
                                  'Dimensional f_T=q_T-Y; the initial model boundary is f_T=0.')],
        'yield_criterion_contract': _T_CONTRACT,
    },
    RATIO_RULE: {
        'quantity': 'tresca_von_mises_equivalent_stress_ratio', 'direction': 'interval',
        'claim_type': 'theoretical_bound', 'bound_kind': 'criterion_function_comparison',
        'quantity_dimension': 'dimensionless', 'si_unit': '1',
        'evaluation_support': 'catalog_only',
        'formula_display': '1<=q_T/q_VM<=2/sqrt(3), nonhydrostatic sigma; q_VM<=q_T<=(2/sqrt(3))*q_VM for all finite real symmetric 3D Cauchy tensors',
        'required_assumptions': dict(_MATH_ASSUMPTIONS,
                                     ratio_domain='nonhydrostatic_sigma_with_q_VM>0',
                                     division_free_domain='all_finite_real_symmetric_3D_Cauchy_tensors_including_hydrostatic_sigma',
                                     physical_model_fit_required=False,
                                     yield_calibration_Y_required=False),
        'parameters': [_SIGMA, _PRINCIPAL, _QVM, _QT,
                       _parameter('q_T/q_VM', 'tresca_von_mises_equivalent_stress_ratio', 'dimensionless', '1',
                                  'Defined only for nonhydrostatic sigma; no Y or physical material fit is required.')],
        'yield_criterion_contract': _RATIO_CONTRACT,
    },
}

_FIELDS = {'id', 'version', 'name', 'quantity', 'direction', 'rule_id',
           'formula_display', 'required_assumptions', 'evidence', 'verification',
           'limits', 'bound_kind', 'dependencies', 'claim_type',
           'quantity_dimension', 'si_unit', 'evaluation_support', 'parameters',
           'yield_criterion_contract'}
_QUANTITIES = {contract['quantity'] for contract in YIELD_CONTRACTS.values()}
_DEFINITION_RULES = {VON_MISES_RULE, TRESCA_RULE}


def _canonical(value):
    # Reject nonfinite JSON and distinguish booleans from numeric constants.
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def validate_yield_records(records, *, resolve_dependencies=False):
    """Validate closed science, permitting fresh IDs and evidence curation.

    Catalog-wide dependency resolution requires one member of each stress
    definition family. Parameter and dependency order carries no meaning.
    This checks metadata only; it never evaluates a supplied stress state.
    """
    if not isinstance(records, (list, tuple)):
        raise ValueError('yield criterion validation requires a record sequence')
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('claim metadata must be an object')
        for key in ('id', 'rule_id', 'quantity'):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ValueError('claim ' + key + ' must be a nonempty string')
    by_id = {record['id']: record for record in records}
    if len(by_id) != len(records):
        raise ValueError('duplicate claim IDs cannot shadow yield criterion metadata')
    for record in records:
        rule = record['rule_id']
        if rule not in YIELD_CONTRACTS:
            parameters = record.get('parameters')
            if ('yield_criterion_contract' in record or
                    record['quantity'] in _QUANTITIES or
                    record.get('bound_kind') == 'criterion_function_comparison' or
                    any(isinstance(p, dict) and p.get('dimension') == 'pressure_squared'
                        for p in (parameters if isinstance(parameters, list) else []))):
                raise ValueError('yield criterion metadata requires a supported family')
            continue
        prefix = 'yield criterion claim ' + record['id']
        if set(record) != _FIELDS:
            raise ValueError(prefix + ': missing or foreign fields')
        try:
            _canonical(record)
            for key, expected in YIELD_CONTRACTS[rule].items():
                actual = record[key]
                if key == 'parameters':
                    if (not isinstance(actual, list) or
                            sorted(map(_canonical, actual)) != sorted(map(_canonical, expected))):
                        raise ValueError(prefix + ': parameter contract differs')
                elif _canonical(actual) != _canonical(expected):
                    raise ValueError(prefix + ': ' + key + ' differs from closed contract')
        except (TypeError, OverflowError) as exc:
            raise ValueError(prefix + ': metadata is not finite JSON') from exc
        dependencies = record['dependencies']
        if rule in _DEFINITION_RULES:
            if dependencies != []:
                raise ValueError(prefix + ': definition must have no dependencies')
        elif (not isinstance(dependencies, list) or len(dependencies) != 2 or
              any(not isinstance(dep, str) or not dep.strip() for dep in dependencies) or
              len(set(dependencies)) != 2):
            raise ValueError(prefix + ': ratio needs two distinct definition dependencies')
        elif resolve_dependencies and {by_id.get(dep, {}).get('rule_id') for dep in dependencies} != _DEFINITION_RULES:
            raise ValueError(prefix + ': dependencies must be one von Mises and one Tresca family')
