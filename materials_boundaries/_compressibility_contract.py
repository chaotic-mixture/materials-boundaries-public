"""Closed catalog metadata guards, with no tensor or numerical evaluator.

Scientific contracts are fixed independently of mutable packaged records.
Display formulas are never executed. Validation certifies metadata shape, not
source inspection, physical realizability or independent scientific peer review.
"""
import json

DEFINITION_RULE = 'directional_linear_compressibility_hydrostatic_relation_v1'
RANGE_RULE = 'normalized_directional_compressibility_range_v1'
COMPRESSIBILITY_CONTRACTS = {'directional_linear_compressibility_hydrostatic_relation_v1': {'quantity': 'directional_linear_compressibility',
                                                                'direction': 'relation',
                                                                'claim_type': 'model_relation',
                                                                'bound_kind': None,
                                                                'quantity_dimension': 'inverse_pressure',
                                                                'si_unit': 'Pa^-1',
                                                                'evaluation_support': 'catalog_only',
                                                                'formula_display': 'beta(n)=n_i*n_j*S_ijkk=nn:S:I; '
                                                                                   'kappa=I:S:I>0; '
                                                                                   'sum_a '
                                                                                   'beta(n_a)=kappa '
                                                                                   'for any '
                                                                                   'orthonormal '
                                                                                   'triad; '
                                                                                   'beta_min=lambda_min(S:I), '
                                                                                   'beta_max=lambda_max(S:I)',
                                                                'required_assumptions': {'spatial_dimension': 3,
                                                                                         'loading': 'static_hydrostatic_stress',
                                                                                         'stress': 'sigma=-p*I, '
                                                                                                   'p>0_sufficiently_small',
                                                                                         'pressure_sign': 'compression_positive',
                                                                                         'stress_sign': 'tension_positive',
                                                                                         'strain_sign': 'extension_positive',
                                                                                         'kinematics': 'infinitesimal_strain',
                                                                                         'constitutive_law': 'classical_local_linear_elastic',
                                                                                         'reference_state': 'stress_free_equilibrium',
                                                                                         'elastic_tensor': 'finite_real_with_minor_and_major_symmetries',
                                                                                         'stability': 'full_stiffness_positive_definite_on_all_nonzero_symmetric_strains_equivalently_full_compliance_SPD',
                                                                                         'compliance': 'full_inverse_of_stiffness_on_symmetric_tensors',
                                                                                         'directions': 'unit_vector_n_in_orthonormal_cartesian_axes',
                                                                                         'elastic_symmetry': 'no_additional_symmetry_required_for_definitions_and_necessary_constraints',
                                                                                         'thermal_condition': 'fixed_temperature_isothermal_elastic_response; '
                                                                                                              'no_temperature_change_or_thermal_expansion',
                                                                                         'matrix_convention': 'engineering_Voigt_order_11_22_33_23_13_12',
                                                                                         'engineering_strain': '(epsilon11,epsilon22,epsilon33,2epsilon23,2epsilon13,2epsilon12)',
                                                                                         'stress_vector': '(sigma11,sigma22,sigma33,sigma23,sigma13,sigma12)',
                                                                                         'matrix_relation': 'e=S_eng*s; '
                                                                                                            's=C_eng*e; '
                                                                                                            'S_eng=inverse(C_eng)',
                                                                                         'shear_conversion': 'S_eng_IJ=d_I*d_J*S_tensor_ij_kl, '
                                                                                                             'd=(1,1,1,2,2,2); '
                                                                                                             'C_eng_IJ=C_tensor_ij_kl',
                                                                                         'compliance_units': 'Pa^-1',
                                                                                         'stiffness_units': 'Pa'},
                                                                'hydrostatic_compressibility_contract': {'kind': 'definition_trace_and_fixed_tensor_range',
                                                                                                         'definition': {'beta': '-d(epsilon_nn)/dp=nn:S:I',
                                                                                                                        'kappa': '-d(tr(epsilon))/dp=I:S:I',
                                                                                                                        'B': 'B_ij=S_ijkk; '
                                                                                                                             'B=S:I; '
                                                                                                                             'symmetric '
                                                                                                                             'second-order '
                                                                                                                             'tensor',
                                                                                                                        'pressure_loading': 'sigma=-p*I',
                                                                                                                        'strain_response': 'epsilon=-p*B'},
                                                                                                         'volume_positivity': {'expression': 'kappa>0',
                                                                                                                               'strict': True,
                                                                                                                               'zero_excluded': True,
                                                                                                                               'basis': 'full_SPD_and_I_nonzero'},
                                                                                                         'orthonormal_sum': {'expression': 'beta(n1)+beta(n2)+beta(n3)=kappa',
                                                                                                                             'scope': 'every_orthonormal_triad_in_the_same_tensor'},
                                                                                                         'fixed_tensor_extrema': {'scope': 'one_fixed_finite_full_SPD_3D_tensor',
                                                                                                                                  'minimum': 'smallest_eigenvalue_of_B',
                                                                                                                                  'maximum': 'largest_eigenvalue_of_B',
                                                                                                                                  'both_finite': True,
                                                                                                                                  'both_attained': True,
                                                                                                                                  'entire_range': 'closed_interval_between_minimum_and_maximum'},
                                                                                                         'sign_constraints': {'negative_directional_beta_allowed': True,
                                                                                                                              'negative_volume_kappa_allowed': False,
                                                                                                                              'at_least_one_positive_principal_beta': True,
                                                                                                                              'all_three_orthonormal_betas_nonpositive_allowed': False,
                                                                                                                              'negative_principal_beta_count_maximum': 2,
                                                                                                                              'warning': 'Do '
                                                                                                                                         'not '
                                                                                                                                         'translate '
                                                                                                                                         'this '
                                                                                                                                         'as '
                                                                                                                                         'at '
                                                                                                                                         'most '
                                                                                                                                         'two '
                                                                                                                                         'negative '
                                                                                                                                         'directions: '
                                                                                                                                         'an '
                                                                                                                                         'open '
                                                                                                                                         'set '
                                                                                                                                         'of '
                                                                                                                                         'directions '
                                                                                                                                         'can '
                                                                                                                                         'have '
                                                                                                                                         'beta<0.',
                                                                                                                              'nonpositive_principal_beta_count_maximum': 2},
                                                                                                         'trace_extrema_inequality': 'beta_min<=kappa/3<=beta_max',
                                                                                                         'equality_condition': 'beta_min=beta_max '
                                                                                                                               'iff '
                                                                                                                               'B=(kappa/3)*I; '
                                                                                                                               'hydrostatic-response '
                                                                                                                               'isotropy '
                                                                                                                               'does '
                                                                                                                               'not '
                                                                                                                               'imply '
                                                                                                                               'full '
                                                                                                                               'elastic '
                                                                                                                               'isotropy',
                                                                                                         'proof_ids': ['P1_definition_volume_trace',
                                                                                                                       'P2_fixed_tensor_spectrum'],
                                                                                                         'engineering_convention_audit': {'h': '(1,1,1,0,0,0)^T',
                                                                                                                                          'g': 'g=S_eng*h',
                                                                                                                                          'B_diagonal': '(B11,B22,B33)=(g1,g2,g3)',
                                                                                                                                          'B_off_diagonal': '(B23,B13,B12)=(g4,g5,g6)/2',
                                                                                                                                          'direction_weights': 'v(n)=(n1^2,n2^2,n3^2,n2*n3,n1*n3,n1*n2)^T',
                                                                                                                                          'beta_matrix': 'beta(n)=v(n)^T*S_eng*h',
                                                                                                                                          'kappa_matrix': 'kappa=h^T*S_eng*h',
                                                                                                                                          'component_formula': 'beta=n1^2*g1+n2^2*g2+n3^2*g3+n2*n3*g4+n1*n3*g5+n1*n2*g6',
                                                                                                                                          'volume_formula': 'kappa=S11+S22+S33+2*(S12+S13+S23), '
                                                                                                                                                            'using '
                                                                                                                                                            'engineering '
                                                                                                                                                            'S_eng',
                                                                                                                                          'orthotropic_specialization': 'g4=g5=g6=0 '
                                                                                                                                                                        'in '
                                                                                                                                                                        'the '
                                                                                                                                                                        'symmetry '
                                                                                                                                                                        'frame; '
                                                                                                                                                                        'diagonal-only '
                                                                                                                                                                        'formula '
                                                                                                                                                                        'is '
                                                                                                                                                                        'not '
                                                                                                                                                                        'general '
                                                                                                                                                                        'for '
                                                                                                                                                                        'lower '
                                                                                                                                                                        'symmetry',
                                                                                                                                          'tensor_shear_warning': 'S_eng_44=4*S2323; '
                                                                                                                                                                  'S_eng_41=2*S2311; '
                                                                                                                                                                  'full '
                                                                                                                                                                  'tensor '
                                                                                                                                                                  'contractions '
                                                                                                                                                                  'automatically '
                                                                                                                                                                  'include '
                                                                                                                                                                  'both '
                                                                                                                                                                  'index '
                                                                                                                                                                  'orders',
                                                                                                                                          'units': {'S_B_beta_kappa': 'Pa^-1',
                                                                                                                                                    'C_E_p': 'Pa',
                                                                                                                                                    'normalized_beta': '1',
                                                                                                                                                    '1_GPa^-1_in_Pa^-1': '1e-9',
                                                                                                                                                    '1_TPa^-1_in_Pa^-1': '1e-12'},
                                                                                                                                          'basis_warning': 'Crystallographic '
                                                                                                                                                           'lattice '
                                                                                                                                                           'vectors '
                                                                                                                                                           'need '
                                                                                                                                                           'not '
                                                                                                                                                           'be '
                                                                                                                                                           'orthogonal; '
                                                                                                                                                           'the '
                                                                                                                                                           'triad '
                                                                                                                                                           'identity '
                                                                                                                                                           'requires '
                                                                                                                                                           'orthonormal '
                                                                                                                                                           'Cartesian '
                                                                                                                                                           'unit '
                                                                                                                                                           'directions.',
                                                                                                                                          'optional_poisson_cross_check': 'For '
                                                                                                                                                                          'any '
                                                                                                                                                                          'orthonormal '
                                                                                                                                                                          'n,m,l '
                                                                                                                                                                          'and '
                                                                                                                                                                          'the '
                                                                                                                                                                          'existing '
                                                                                                                                                                          'project '
                                                                                                                                                                          'nu '
                                                                                                                                                                          'convention: '
                                                                                                                                                                          'beta(n)=[1-nu(n,m)-nu(n,l)]/E(n), '
                                                                                                                                                                          'by '
                                                                                                                                                                          'major '
                                                                                                                                                                          'symmetry. '
                                                                                                                                                                          'NLC '
                                                                                                                                                                          'along '
                                                                                                                                                                          'n '
                                                                                                                                                                          'means '
                                                                                                                                                                          'that '
                                                                                                                                                                          'sum '
                                                                                                                                                                          'exceeds '
                                                                                                                                                                          '1; '
                                                                                                                                                                          'do '
                                                                                                                                                                          'not '
                                                                                                                                                                          'confuse '
                                                                                                                                                                          'beta '
                                                                                                                                                                          'with '
                                                                                                                                                                          'a '
                                                                                                                                                                          'Poisson '
                                                                                                                                                                          'ratio '
                                                                                                                                                                          'or '
                                                                                                                                                                          'copy '
                                                                                                                                                                          'the '
                                                                                                                                                                          'different '
                                                                                                                                                                          'Miller '
                                                                                                                                                                          'subscript '
                                                                                                                                                                          'convention.'},
                                                                                                         'derivation_status': 'original_project_algebra_not_independent_scientific_peer_review',
                                                                                                         'scope_exclusions': ['prestress',
                                                                                                                              'finite_strain_tangent_response',
                                                                                                                              'two_dimensional_elasticity',
                                                                                                                              'plane_stress_or_plane_strain_constitutive_reductions',
                                                                                                                              'singular_positive_semidefinite_or_indefinite_compliance',
                                                                                                                              'complex_viscoelastic_nonlocal_or_Cosserat_response',
                                                                                                                              'phase_transition_or_branch_switching',
                                                                                                                              'internal_instabilities',
                                                                                                                              'metastable_or_constrained_negative_bulk_systems',
                                                                                                                              'pressure_medium_infiltration_mass_exchange_swelling',
                                                                                                                              'active_or_nonconservative_systems',
                                                                                                                              'imposed_isotropic_strain_or_volume_control'],
                                                                                                         'source_attribution': {'published_definitions': 'Ortiz_2012_Eqs_2_3_beta_and_E_visually_verified; '
                                                                                                                                                         'Miller_2015_manuscript_Eqs_1_2_volume_and_orthotropic_definition_text_only',
                                                                                                                                'trace_spectral_energy_and_all_real_range': 'original_project_proofs_not_attributed_to_source_equations',
                                                                                                                                'scientific_peer_review_certified': False,
                                                                                                                                'physical_realizability_certified': False}},
                                                                'parameters': [{'symbol': 'S',
                                                                                'quantity': 'full_elastic_compliance_tensor',
                                                                                'dimension': 'inverse_pressure',
                                                                                'si_unit': 'Pa^-1',
                                                                                'meaning': 'Full '
                                                                                           'fourth-order '
                                                                                           'inverse '
                                                                                           'of '
                                                                                           'finite '
                                                                                           'full-SPD '
                                                                                           'stiffness '
                                                                                           'on '
                                                                                           'symmetric '
                                                                                           'tensors.'},
                                                                               {'symbol': 'kappa',
                                                                                'quantity': 'hydrostatic_volumetric_compressibility',
                                                                                'dimension': 'inverse_pressure',
                                                                                'si_unit': 'Pa^-1',
                                                                                'meaning': 'I:S:I=-d(tr '
                                                                                           'epsilon)/dp '
                                                                                           'at the '
                                                                                           'stress-free '
                                                                                           'reference '
                                                                                           'state, '
                                                                                           'strictly '
                                                                                           'positive.'},
                                                                               {'symbol': 'p',
                                                                                'quantity': 'hydrostatic_pressure',
                                                                                'dimension': 'pressure',
                                                                                'si_unit': 'Pa',
                                                                                'meaning': 'Positive '
                                                                                           'compressive '
                                                                                           'infinitesimal '
                                                                                           'applied '
                                                                                           'pressure; '
                                                                                           'sigma=-p '
                                                                                           'I.'}]},
 'normalized_directional_compressibility_range_v1': {'quantity': 'normalized_directional_linear_compressibility',
                                                     'direction': 'relation',
                                                     'claim_type': 'model_relation',
                                                     'bound_kind': None,
                                                     'quantity_dimension': 'dimensionless',
                                                     'si_unit': '1',
                                                     'evaluation_support': 'catalog_only',
                                                     'formula_display': 'r(n)=beta(n)/kappa; '
                                                                        'unrestricted finite '
                                                                        'full-SPD 3D tensor-class '
                                                                        'range is all finite real '
                                                                        'numbers; '
                                                                        'beta(n)^2<kappa/E(n), '
                                                                        'equivalently '
                                                                        'r(n)^2<1/(kappa*E(n))',
                                                     'required_assumptions': {'spatial_dimension': 3,
                                                                              'loading': 'static_hydrostatic_stress',
                                                                              'stress': 'sigma=-p*I, '
                                                                                        'p>0_sufficiently_small',
                                                                              'pressure_sign': 'compression_positive',
                                                                              'stress_sign': 'tension_positive',
                                                                              'strain_sign': 'extension_positive',
                                                                              'kinematics': 'infinitesimal_strain',
                                                                              'constitutive_law': 'classical_local_linear_elastic',
                                                                              'reference_state': 'stress_free_equilibrium',
                                                                              'elastic_tensor': 'finite_real_with_minor_and_major_symmetries',
                                                                              'stability': 'full_stiffness_positive_definite_on_all_nonzero_symmetric_strains_equivalently_full_compliance_SPD',
                                                                              'compliance': 'full_inverse_of_stiffness_on_symmetric_tensors',
                                                                              'directions': 'unit_vector_n_in_orthonormal_cartesian_axes',
                                                                              'elastic_symmetry': 'no_additional_symmetry_required_for_definitions_and_necessary_constraints',
                                                                              'thermal_condition': 'fixed_temperature_isothermal_elastic_response; '
                                                                                                   'no_temperature_change_or_thermal_expansion',
                                                                              'matrix_convention': 'engineering_Voigt_order_11_22_33_23_13_12',
                                                                              'engineering_strain': '(epsilon11,epsilon22,epsilon33,2epsilon23,2epsilon13,2epsilon12)',
                                                                              'stress_vector': '(sigma11,sigma22,sigma33,sigma23,sigma13,sigma12)',
                                                                              'matrix_relation': 'e=S_eng*s; '
                                                                                                 's=C_eng*e; '
                                                                                                 'S_eng=inverse(C_eng)',
                                                                              'shear_conversion': 'S_eng_IJ=d_I*d_J*S_tensor_ij_kl, '
                                                                                                  'd=(1,1,1,2,2,2); '
                                                                                                  'C_eng_IJ=C_tensor_ij_kl',
                                                                              'compliance_units': 'Pa^-1',
                                                                              'stiffness_units': 'Pa'},
                                                     'hydrostatic_compressibility_contract': {'kind': 'normalized_tensor_class_range_and_necessary_energy_constraint',
                                                                                              'definition': {'normalized_response': 'r(n)=beta(n)/kappa',
                                                                                                             'kappa_strictly_positive': True},
                                                                                              'material_class_range': {'scope': 'varying_finite_full_SPD_3D_compliance_tensors_and_unit_directions; '
                                                                                                                                'no_restriction_to_each_crystal_symmetry_subclass',
                                                                                                                       'attainable_set': 'all_finite_real_numbers',
                                                                                                                       'lower': {'status': 'unbounded_below',
                                                                                                                                 'infinity_attained': False},
                                                                                                                       'upper': {'status': 'unbounded_above',
                                                                                                                                 'infinity_attained': False},
                                                                                                                       'constructive_subclass': 'at_least_orthotropic_in_displayed_frame',
                                                                                                                       'valid_even_at_any_fixed_positive_kappa': True},
                                                                                              'fixed_tensor_range': {'minimum': 'lambda_min(B)/kappa',
                                                                                                                     'maximum': 'lambda_max(B)/kappa',
                                                                                                                     'finite_and_attained': True,
                                                                                                                     'minimum_at_most_one_third': True,
                                                                                                                     'maximum_at_least_one_third': True},
                                                                                              'necessary_energy_constraint': {'expression': 'beta(n)^2<kappa*(nn:S:nn)=kappa/E(n)',
                                                                                                                              'equivalent_normalized': 'r(n)^2<1/(kappa*E(n))',
                                                                                                                              'strict': True,
                                                                                                                              'equality_attained': False,
                                                                                                                              'sufficient_for_full_SPD': False,
                                                                                                                              'universal_finite_numerical_bound': False},
                                                                                              'symmetry_warning': 'Unboundedness '
                                                                                                                  'over '
                                                                                                                  'the '
                                                                                                                  'unrestricted '
                                                                                                                  'tensor '
                                                                                                                  'class '
                                                                                                                  'is '
                                                                                                                  'not '
                                                                                                                  'unboundedness '
                                                                                                                  'in '
                                                                                                                  'every '
                                                                                                                  'symmetry '
                                                                                                                  'class. '
                                                                                                                  'Full-SPD '
                                                                                                                  'cubic '
                                                                                                                  'and '
                                                                                                                  'isotropic '
                                                                                                                  'elasticity '
                                                                                                                  'have '
                                                                                                                  'r(n)=1/3 '
                                                                                                                  'for '
                                                                                                                  'every '
                                                                                                                  'n.',
                                                                                              'proof_ids': ['P3_orthotropic_construction',
                                                                                                            'P4_strict_energy_constraint',
                                                                                                            'P5_cubic_isotropic_check'],
                                                                                              'engineering_convention_audit': {'h': '(1,1,1,0,0,0)^T',
                                                                                                                               'g': 'g=S_eng*h',
                                                                                                                               'B_diagonal': '(B11,B22,B33)=(g1,g2,g3)',
                                                                                                                               'B_off_diagonal': '(B23,B13,B12)=(g4,g5,g6)/2',
                                                                                                                               'direction_weights': 'v(n)=(n1^2,n2^2,n3^2,n2*n3,n1*n3,n1*n2)^T',
                                                                                                                               'beta_matrix': 'beta(n)=v(n)^T*S_eng*h',
                                                                                                                               'kappa_matrix': 'kappa=h^T*S_eng*h',
                                                                                                                               'component_formula': 'beta=n1^2*g1+n2^2*g2+n3^2*g3+n2*n3*g4+n1*n3*g5+n1*n2*g6',
                                                                                                                               'volume_formula': 'kappa=S11+S22+S33+2*(S12+S13+S23), '
                                                                                                                                                 'using '
                                                                                                                                                 'engineering '
                                                                                                                                                 'S_eng',
                                                                                                                               'orthotropic_specialization': 'g4=g5=g6=0 '
                                                                                                                                                             'in '
                                                                                                                                                             'the '
                                                                                                                                                             'symmetry '
                                                                                                                                                             'frame; '
                                                                                                                                                             'diagonal-only '
                                                                                                                                                             'formula '
                                                                                                                                                             'is '
                                                                                                                                                             'not '
                                                                                                                                                             'general '
                                                                                                                                                             'for '
                                                                                                                                                             'lower '
                                                                                                                                                             'symmetry',
                                                                                                                               'tensor_shear_warning': 'S_eng_44=4*S2323; '
                                                                                                                                                       'S_eng_41=2*S2311; '
                                                                                                                                                       'full '
                                                                                                                                                       'tensor '
                                                                                                                                                       'contractions '
                                                                                                                                                       'automatically '
                                                                                                                                                       'include '
                                                                                                                                                       'both '
                                                                                                                                                       'index '
                                                                                                                                                       'orders',
                                                                                                                               'units': {'S_B_beta_kappa': 'Pa^-1',
                                                                                                                                         'C_E_p': 'Pa',
                                                                                                                                         'normalized_beta': '1',
                                                                                                                                         '1_GPa^-1_in_Pa^-1': '1e-9',
                                                                                                                                         '1_TPa^-1_in_Pa^-1': '1e-12'},
                                                                                                                               'basis_warning': 'Crystallographic '
                                                                                                                                                'lattice '
                                                                                                                                                'vectors '
                                                                                                                                                'need '
                                                                                                                                                'not '
                                                                                                                                                'be '
                                                                                                                                                'orthogonal; '
                                                                                                                                                'the '
                                                                                                                                                'triad '
                                                                                                                                                'identity '
                                                                                                                                                'requires '
                                                                                                                                                'orthonormal '
                                                                                                                                                'Cartesian '
                                                                                                                                                'unit '
                                                                                                                                                'directions.',
                                                                                                                               'optional_poisson_cross_check': 'For '
                                                                                                                                                               'any '
                                                                                                                                                               'orthonormal '
                                                                                                                                                               'n,m,l '
                                                                                                                                                               'and '
                                                                                                                                                               'the '
                                                                                                                                                               'existing '
                                                                                                                                                               'project '
                                                                                                                                                               'nu '
                                                                                                                                                               'convention: '
                                                                                                                                                               'beta(n)=[1-nu(n,m)-nu(n,l)]/E(n), '
                                                                                                                                                               'by '
                                                                                                                                                               'major '
                                                                                                                                                               'symmetry. '
                                                                                                                                                               'NLC '
                                                                                                                                                               'along '
                                                                                                                                                               'n '
                                                                                                                                                               'means '
                                                                                                                                                               'that '
                                                                                                                                                               'sum '
                                                                                                                                                               'exceeds '
                                                                                                                                                               '1; '
                                                                                                                                                               'do '
                                                                                                                                                               'not '
                                                                                                                                                               'confuse '
                                                                                                                                                               'beta '
                                                                                                                                                               'with '
                                                                                                                                                               'a '
                                                                                                                                                               'Poisson '
                                                                                                                                                               'ratio '
                                                                                                                                                               'or '
                                                                                                                                                               'copy '
                                                                                                                                                               'the '
                                                                                                                                                               'different '
                                                                                                                                                               'Miller '
                                                                                                                                                               'subscript '
                                                                                                                                                               'convention.'},
                                                                                              'derivation_status': 'original_project_algebra_not_independent_scientific_peer_review',
                                                                                              'scope_exclusions': ['prestress',
                                                                                                                   'finite_strain_tangent_response',
                                                                                                                   'two_dimensional_elasticity',
                                                                                                                   'plane_stress_or_plane_strain_constitutive_reductions',
                                                                                                                   'singular_positive_semidefinite_or_indefinite_compliance',
                                                                                                                   'complex_viscoelastic_nonlocal_or_Cosserat_response',
                                                                                                                   'phase_transition_or_branch_switching',
                                                                                                                   'internal_instabilities',
                                                                                                                   'metastable_or_constrained_negative_bulk_systems',
                                                                                                                   'pressure_medium_infiltration_mass_exchange_swelling',
                                                                                                                   'active_or_nonconservative_systems',
                                                                                                                   'imposed_isotropic_strain_or_volume_control'],
                                                                                              'source_attribution': {'published_definitions': 'Ortiz_2012_Eqs_2_3_beta_and_E_visually_verified; '
                                                                                                                                              'Miller_2015_manuscript_Eqs_1_2_volume_and_orthotropic_definition_text_only',
                                                                                                                     'trace_spectral_energy_and_all_real_range': 'original_project_proofs_not_attributed_to_source_equations',
                                                                                                                     'scientific_peer_review_certified': False,
                                                                                                                     'physical_realizability_certified': False}},
                                                     'parameters': [{'symbol': 'beta(n)',
                                                                     'quantity': 'directional_linear_compressibility',
                                                                     'dimension': 'inverse_pressure',
                                                                     'si_unit': 'Pa^-1',
                                                                     'meaning': 'nn:S:I for the '
                                                                                'same tensor S and '
                                                                                'unit n.'},
                                                                    {'symbol': 'kappa',
                                                                     'quantity': 'hydrostatic_volumetric_compressibility',
                                                                     'dimension': 'inverse_pressure',
                                                                     'si_unit': 'Pa^-1',
                                                                     'meaning': 'I:S:I>0 for the '
                                                                                'same S, not three '
                                                                                'times an '
                                                                                'arbitrary '
                                                                                'directional '
                                                                                'beta.'},
                                                                    {'symbol': 'E(n)',
                                                                     'quantity': 'directional_youngs_modulus',
                                                                     'dimension': 'pressure',
                                                                     'si_unit': 'Pa',
                                                                     'meaning': '1/(nn:S:nn)>0 '
                                                                                'under uniaxial '
                                                                                'stress in n for '
                                                                                'the same S. Used '
                                                                                'only in a '
                                                                                'necessary '
                                                                                'tensor-dependent '
                                                                                'inequality.'}]}}

_FIELDS = {'id', 'version', 'name', 'quantity', 'direction', 'rule_id',
           'formula_display', 'required_assumptions', 'evidence', 'verification',
           'limits', 'bound_kind', 'dependencies', 'claim_type',
           'quantity_dimension', 'si_unit', 'evaluation_support', 'parameters',
           'hydrostatic_compressibility_contract'}
_QUANTITIES = {'directional_linear_compressibility',
               'normalized_directional_linear_compressibility'}


def _canonical(value):
    # Reject nonfinite JSON and distinguish booleans from numeric constants.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_compressibility_records(records, *, resolve_dependencies=False):
    """Validate closed science while allowing fresh IDs and source curation.

    Full catalogs resolve normalized-response dependencies by definition family,
    not by one privileged record ID. Parameters may be reordered.
    """
    if not isinstance(records, (list, tuple)):
        raise ValueError('compressibility validation requires a record sequence')
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('claim metadata must be an object')
        for key in ('id', 'rule_id', 'quantity'):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ValueError('claim ' + key + ' must be a nonempty string')
    by_id = {record['id']: record for record in records}
    if len(by_id) != len(records):
        raise ValueError('duplicate claim IDs cannot shadow compressibility metadata')
    for record in records:
        rule = record.get('rule_id')
        if rule not in COMPRESSIBILITY_CONTRACTS:
            if ('hydrostatic_compressibility_contract' in record or
                    record.get('quantity') in _QUANTITIES):
                raise ValueError('compressibility metadata requires a supported family')
            continue
        prefix = 'compressibility claim ' + str(record.get('id'))
        if set(record) != _FIELDS:
            raise ValueError(prefix + ': missing or foreign fields')
        try:
            _canonical(record)
            for key, expected in COMPRESSIBILITY_CONTRACTS[rule].items():
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
        if rule == DEFINITION_RULE:
            if dependencies != []:
                raise ValueError(prefix + ': definition must have no dependencies')
        elif (not isinstance(dependencies, list) or len(dependencies) != 1 or
              not isinstance(dependencies[0], str) or not dependencies[0].strip()):
            raise ValueError(prefix + ': normalized response needs one definition dependency')
        elif resolve_dependencies and by_id.get(dependencies[0], {}).get('rule_id') != DEFINITION_RULE:
            raise ValueError(prefix + ': dependency must be a hydrostatic definition family')
