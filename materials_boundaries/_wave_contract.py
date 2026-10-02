"""Closed non-executable bulk-wave metadata; no numerical tensor API.

Contracts are independent of mutable packaged catalogs. Display formulas are
never executed. Metadata validation is not scientific peer review.
"""
import json

ISOTROPIC_RULE = 'isotropic_bulk_plane_wave_speeds_and_ratio_v1'
CHRISTOFFEL_RULE = 'christoffel_tensor_strong_ellipticity_v1'
WAVE_CONTRACTS = {'isotropic_bulk_plane_wave_speeds_and_ratio_v1': {'quantity': 'isotropic_bulk_phase_speed_ratio',
                                                   'direction': 'relation',
                                                   'claim_type': 'model_relation',
                                                   'bound_kind': None,
                                                   'quantity_dimension': 'dimensionless',
                                                   'si_unit': '1',
                                                   'evaluation_support': 'catalog_only',
                                                   'formula_display': 'cL^2=(K+4*G/3)/rho; cT^2=G/rho; '
                                                                      'cL/cT=sqrt(K/G+4/3)',
                                                   'required_assumptions': {'spatial_dimension': 3,
                                                                            'reference_state': 'stress_free_equilibrium',
                                                                            'kinematics': 'infinitesimal_strain',
                                                                            'constitutive_law': 'classical_local_linear_elastic_purely_mechanical_nondissipative',
                                                                            'medium': 'homogeneous_unbounded_continuum_bulk_plane_waves',
                                                                            'elastic_tensor': 'finite_real_spatially_constant_C_ijkl',
                                                                            'tensor_symmetries': 'C_ijkl=C_jikl=C_ijlk=C_klij',
                                                                            'density': 'finite_constant_scalar_mass_density_rho>0',
                                                                            'axes': 'orthonormal_Cartesian',
                                                                            'indices': 'i,j,k,l=1,2,3; '
                                                                                       'repeated_indices_summed',
                                                                            'constitutive_relation': 'sigma_ij=C_ijkl*epsilon_kl; '
                                                                                                     'epsilon_kl=(u_k,l+u_l,k)/2',
                                                                            'wave_convention': 'u(x,t)=Re[A*a*exp(i*k*(n '
                                                                                               'dot '
                                                                                               'x-c*t))]; '
                                                                                               'k>0; '
                                                                                               '|n|=1; '
                                                                                               'a_nonzero_real_eigenpolarization; '
                                                                                               'positive_phase_speed_root_when_c_squared>0',
                                                                            'directions': 'n_is_phase_normal_wavevector_direction; '
                                                                                          'a_is_particle_displacement_polarization',
                                                                            'modulus_scope': 'operative_tensor_of_declared_ideal_mechanical_model; '
                                                                                             'no_automatic_static_isothermal_to_adiabatic_or_frequency_conversion',
                                                                            'phase_velocity_scope': 'no_claim_about_anisotropic_ray_group_or_energy_velocity',
                                                                            'elastic_symmetry': 'isotropic',
                                                                            'moduli': 'finite_K>0_and_finite_G>0',
                                                                            'stability': 'full_strain_energy_positive_for_every_nonzero_symmetric_strain'},
                                                   'parameters': [{'symbol': 'K',
                                                                   'quantity': 'bulk_modulus',
                                                                   'dimension': 'pressure',
                                                                   'si_unit': 'Pa',
                                                                   'meaning': 'Finite strictly positive '
                                                                              'operative isotropic bulk '
                                                                              'modulus.'},
                                                                  {'symbol': 'G',
                                                                   'quantity': 'shear_modulus',
                                                                   'dimension': 'pressure',
                                                                   'si_unit': 'Pa',
                                                                   'meaning': 'Finite strictly positive '
                                                                              'operative isotropic '
                                                                              'shear modulus.'},
                                                                  {'symbol': 'rho',
                                                                   'quantity': 'mass_density',
                                                                   'dimension': 'mass_density',
                                                                   'si_unit': 'kg m^-3',
                                                                   'meaning': 'Finite constant strictly '
                                                                              'positive scalar mass '
                                                                              'density.'},
                                                                  {'symbol': 'cL',
                                                                   'quantity': 'longitudinal_phase_speed',
                                                                   'dimension': 'speed',
                                                                   'si_unit': 'm s^-1',
                                                                   'meaning': 'Positive phase-speed '
                                                                              'root with displacement '
                                                                              'polarization parallel to '
                                                                              'n.'},
                                                                  {'symbol': 'cT',
                                                                   'quantity': 'transverse_phase_speed',
                                                                   'dimension': 'speed',
                                                                   'si_unit': 'm s^-1',
                                                                   'meaning': 'Positive phase-speed '
                                                                              'root with displacement '
                                                                              'polarization '
                                                                              'perpendicular to n; '
                                                                              'multiplicity two.'},
                                                                  {'symbol': 'R',
                                                                   'quantity': 'longitudinal_to_transverse_phase_speed_ratio',
                                                                   'dimension': 'dimensionless',
                                                                   'si_unit': '1',
                                                                   'meaning': 'cL/cT for the same '
                                                                              'material; density '
                                                                              'cancels.'}],
                                                   'bulk_wave_contract': {'units': {'C_K_G_lambda_Q': 'Pa',
                                                                                    'rho': 'kg m^-3',
                                                                                    'c': 'm s^-1',
                                                                                    'Gamma_and_c_squared': 'm^2 '
                                                                                                           's^-2',
                                                                                    'n_and_a': '1',
                                                                                    'dimension_check': 'Pa/(kg '
                                                                                                       'm^-3)=m^2 '
                                                                                                       's^-2'},
                                                                          'scope_exclusions': ['prestress_and_residual_stress',
                                                                                               'finite_strain_incremental_or_tangent_moduli',
                                                                                               'complex_viscoelasticity_damping_and_material_dispersion',
                                                                                               'thermoelastic_coupling_or_isothermal_to_adiabatic_conversion',
                                                                                               'poroelasticity_or_heterogeneous_effective_medium_wave_assumptions',
                                                                                               'negative_or_tensorial_dynamic_effective_density',
                                                                                               'nonlocal_strain_gradient_Cosserat_or_micromorphic_media',
                                                                                               'two_dimensional_reductions_or_thin_film_plane_stress_plane_strain',
                                                                                               'surface_Rayleigh_Love_or_guided_waves',
                                                                                               'finite_body_boundary_resonances',
                                                                                               'material_specific_speed_prediction',
                                                                                               'full_phonon_or_thermodynamic_stability'],
                                                                          'derivation_status': 'original_project_algebra_not_independent_scientific_peer_review',
                                                                          'source_attribution': {'published_equations': 'Chevrot_van_der_Hilst_2003_p498_Eqs_1_to_4_plane_wave_eigenproblem',
                                                                                                 'preprint_equations': 'Xiang_Qi_Wei_arXiv_1708.04876v2_pp2_4_5_strong_ellipticity_and_isotropic_speeds; '
                                                                                                                       'journal_publication_not_verified',
                                                                                                 'project_results': 'index_relabeling_ratio_range_SPD_implication_counterexample_and_compactness_are_original_project_derivations',
                                                                                                 'scientific_peer_review_certified': False,
                                                                                                 'physical_realizability_certified': False},
                                                                          'kind': 'isotropic_speeds_and_positive_energy_class_ratio',
                                                                          'isotropic_tensor': 'C_ijkl=(K-2*G/3)*delta_ij*delta_kl+G*(delta_ik*delta_jl+delta_il*delta_jk)',
                                                                          'acoustic_tensor': 'Q(n)=G*I+(K+G/3)*(n '
                                                                                             'tensor '
                                                                                             'n), |n|=1',
                                                                          'modes': {'longitudinal_polarization': 'a_parallel_n',
                                                                                    'transverse_polarization': 'a_perpendicular_n',
                                                                                    'longitudinal_multiplicity': 1,
                                                                                    'transverse_multiplicity': 2,
                                                                                    'fixed_material_speeds_finite': True,
                                                                                    'direction_independent': True},
                                                                          'material_class_range': {'quantity': 'cL/cT',
                                                                                                   'attainable_set': '(sqrt(4/3), '
                                                                                                                     'infinity)',
                                                                                                   'scope': 'varying_all_finite_positive_K_G_rho',
                                                                                                   'lower': {'value': 'sqrt(4/3)',
                                                                                                             'inclusive': False,
                                                                                                             'attained': False,
                                                                                                             'status': 'strict_unattained_infimum'},
                                                                                                   'upper': {'finite_bound_exists': False,
                                                                                                             'infinity_attained': False},
                                                                                                   'density_cancels': True,
                                                                                                   'fixed_material': 'one_finite_cL_and_one_finite_doubly_degenerate_cT',
                                                                                                   'basis': 'original_project_derivation_from_source_equations'},
                                                                          'endpoint_exclusions': {'K=0': 'outside_strict_positive_energy_class_even_though_SE_for_G>0',
                                                                                                  'K=infinity': 'not_a_finite_parameter_material'},
                                                                          'proof_ids': ['W1_isotropic_contraction',
                                                                                        'W2_positive_energy_ratio_range']},
                                                   'dependencies': []},
 'christoffel_tensor_strong_ellipticity_v1': {'quantity': 'bulk_phase_speed_squared',
                                              'direction': 'relation',
                                              'claim_type': 'model_relation',
                                              'bound_kind': None,
                                              'quantity_dimension': 'speed_squared',
                                              'si_unit': 'm^2 s^-2',
                                              'evaluation_support': 'catalog_only',
                                              'formula_display': 'Q_ik(n)=C_ijkl*n_j*n_l; '
                                                                 'Gamma_ik(n)=Q_ik(n)/rho; '
                                                                 'Q*a=rho*c^2*a; Gamma*a=c^2*a',
                                              'required_assumptions': {'spatial_dimension': 3,
                                                                       'reference_state': 'stress_free_equilibrium',
                                                                       'kinematics': 'infinitesimal_strain',
                                                                       'constitutive_law': 'classical_local_linear_elastic_purely_mechanical_nondissipative',
                                                                       'medium': 'homogeneous_unbounded_continuum_bulk_plane_waves',
                                                                       'elastic_tensor': 'finite_real_spatially_constant_C_ijkl',
                                                                       'tensor_symmetries': 'C_ijkl=C_jikl=C_ijlk=C_klij',
                                                                       'density': 'finite_constant_scalar_mass_density_rho>0',
                                                                       'axes': 'orthonormal_Cartesian',
                                                                       'indices': 'i,j,k,l=1,2,3; '
                                                                                  'repeated_indices_summed',
                                                                       'constitutive_relation': 'sigma_ij=C_ijkl*epsilon_kl; '
                                                                                                'epsilon_kl=(u_k,l+u_l,k)/2',
                                                                       'wave_convention': 'u(x,t)=Re[A*a*exp(i*k*(n '
                                                                                          'dot '
                                                                                          'x-c*t))]; '
                                                                                          'k>0; |n|=1; '
                                                                                          'a_nonzero_real_eigenpolarization; '
                                                                                          'positive_phase_speed_root_when_c_squared>0',
                                                                       'directions': 'n_is_phase_normal_wavevector_direction; '
                                                                                     'a_is_particle_displacement_polarization',
                                                                       'modulus_scope': 'operative_tensor_of_declared_ideal_mechanical_model; '
                                                                                        'no_automatic_static_isothermal_to_adiabatic_or_frequency_conversion',
                                                                       'phase_velocity_scope': 'no_claim_about_anisotropic_ray_group_or_energy_velocity',
                                                                       'elastic_symmetry': 'any_3D_classical_elastic_symmetry',
                                                                       'stability': 'none_required_for_real_symmetric_eigenproblem; '
                                                                                    'strict_SE_required_for_positive_squared_speeds_in_every_direction'},
                                              'parameters': [{'symbol': 'C',
                                                              'quantity': 'operative_elastic_stiffness_tensor',
                                                              'dimension': 'pressure',
                                                              'si_unit': 'Pa',
                                                              'meaning': 'Finite real fourth-order '
                                                                         'tensor with both minor and '
                                                                         'major symmetries.'},
                                                             {'symbol': 'Q',
                                                              'quantity': 'unnormalized_acoustic_tensor',
                                                              'dimension': 'pressure',
                                                              'si_unit': 'Pa',
                                                              'meaning': 'Q_ik=C_ijkl*n_j*n_l. Do not '
                                                                         'replace with C_ijkl*n_k*n_l.'},
                                                             {'symbol': 'rho',
                                                              'quantity': 'mass_density',
                                                              'dimension': 'mass_density',
                                                              'si_unit': 'kg m^-3',
                                                              'meaning': 'Finite constant strictly '
                                                                         'positive scalar mass '
                                                                         'density.'},
                                                             {'symbol': 'Gamma',
                                                              'quantity': 'density_normalized_Christoffel_tensor',
                                                              'dimension': 'speed_squared',
                                                              'si_unit': 'm^2 s^-2',
                                                              'meaning': 'Gamma=Q/rho; its eigenvalues '
                                                                         'are c_alpha(n)^2.'},
                                                             {'symbol': 'c^2',
                                                              'quantity': 'bulk_phase_speed_squared',
                                                              'dimension': 'speed_squared',
                                                              'si_unit': 'm^2 s^-2',
                                                              'meaning': 'Eigenvalue of Gamma; strictly '
                                                                         'positive in every unit '
                                                                         'direction exactly when strict '
                                                                         'strong ellipticity holds.'},
                                                             {'symbol': 'n',
                                                              'quantity': 'phase_normal_direction',
                                                              'dimension': 'dimensionless',
                                                              'si_unit': '1',
                                                              'meaning': 'Real unit vector giving '
                                                                         'propagation wavevector '
                                                                         'direction, not polarization '
                                                                         'or ray direction.'},
                                                             {'symbol': 'a',
                                                              'quantity': 'displacement_polarization',
                                                              'dimension': 'dimensionless',
                                                              'si_unit': '1',
                                                              'meaning': 'Nonzero real '
                                                                         'eigenpolarization; amplitude '
                                                                         'A supplies displacement '
                                                                         'units.'}],
                                              'bulk_wave_contract': {'units': {'C_K_G_lambda_Q': 'Pa',
                                                                               'rho': 'kg m^-3',
                                                                               'c': 'm s^-1',
                                                                               'Gamma_and_c_squared': 'm^2 '
                                                                                                      's^-2',
                                                                               'n_and_a': '1',
                                                                               'dimension_check': 'Pa/(kg '
                                                                                                  'm^-3)=m^2 '
                                                                                                  's^-2'},
                                                                     'scope_exclusions': ['prestress_and_residual_stress',
                                                                                          'finite_strain_incremental_or_tangent_moduli',
                                                                                          'complex_viscoelasticity_damping_and_material_dispersion',
                                                                                          'thermoelastic_coupling_or_isothermal_to_adiabatic_conversion',
                                                                                          'poroelasticity_or_heterogeneous_effective_medium_wave_assumptions',
                                                                                          'negative_or_tensorial_dynamic_effective_density',
                                                                                          'nonlocal_strain_gradient_Cosserat_or_micromorphic_media',
                                                                                          'two_dimensional_reductions_or_thin_film_plane_stress_plane_strain',
                                                                                          'surface_Rayleigh_Love_or_guided_waves',
                                                                                          'finite_body_boundary_resonances',
                                                                                          'material_specific_speed_prediction',
                                                                                          'full_phonon_or_thermodynamic_stability'],
                                                                     'derivation_status': 'original_project_algebra_not_independent_scientific_peer_review',
                                                                     'source_attribution': {'published_equations': 'Chevrot_van_der_Hilst_2003_p498_Eqs_1_to_4_plane_wave_eigenproblem',
                                                                                            'preprint_equations': 'Xiang_Qi_Wei_arXiv_1708.04876v2_pp2_4_5_strong_ellipticity_and_isotropic_speeds; '
                                                                                                                  'journal_publication_not_verified',
                                                                                            'project_results': 'index_relabeling_ratio_range_SPD_implication_counterexample_and_compactness_are_original_project_derivations',
                                                                                            'scientific_peer_review_certified': False,
                                                                                            'physical_realizability_certified': False},
                                                                     'kind': 'Christoffel_eigenproblem_and_strict_strong_ellipticity',
                                                                     'contraction': {'unnormalized': 'Q_ik=C_ijkl*n_j*n_l',
                                                                                     'normalized': 'Gamma_ik=Q_ik/rho',
                                                                                     'equations': ['Q*a=rho*c^2*a',
                                                                                                   'Gamma*a=c^2*a'],
                                                                                     'source_index_mapping': 'Chevrot_Gamma_jk=C_ijkl*n_i*n_l/rho; '
                                                                                                             'first_pair_minor_symmetry_and_dummy_index_relabeling_give_project_Q_ik/rho'},
                                                                     'strict_criterion': {'expression': 'C_ijkl*a_i*n_j*a_k*n_l>0',
                                                                                          'quantifier': 'every_nonzero_real_a_and_every_nonzero_real_n',
                                                                                          'equivalent': 'Q(n)_SPD_for_every_unit_n',
                                                                                          'zero_vectors_excluded': True,
                                                                                          'zero_eigenvalues_excluded': True,
                                                                                          'nonnegative_is_sufficient': False},
                                                                     'spectrum': {'eigenvalue_count_with_multiplicity': 3,
                                                                                  'Q_real_symmetric': True,
                                                                                  'orthonormal_real_eigenbasis': True,
                                                                                  'strict_SE_iff_all_c_squared_positive_in_every_unit_direction': True,
                                                                                  'distinct_eigenvalues_required': False,
                                                                                  'degenerate_eigenbasis': 'nonunique_within_repeated_eigenspaces',
                                                                                  'generic_exact_longitudinal_transverse_labels': False,
                                                                                  'generic_fastest_longitudinal_ordering': False},
                                                                     'energy_relation': {'full_symmetric_strain_energy_SPD_implies_SE': True,
                                                                                         'converse': False,
                                                                                         'rank_one_identity': 'a^T*Q(n)*a=e:C:e, '
                                                                                                              'e=sym(a '
                                                                                                              'tensor '
                                                                                                              'n)',
                                                                                         'nonzero_symmetric_strain': '||e||^2=(|a|^2*|n|^2+(a '
                                                                                                                     'dot '
                                                                                                                     'n)^2)/2>0 '
                                                                                                                     'for '
                                                                                                                     'a!=0,n!=0'},
                                                                     'isotropic_specialization': {'Q': 'G*I+(K+G/3)*(n '
                                                                                                       'tensor '
                                                                                                       'n), '
                                                                                                       '|n|=1',
                                                                                                  'SE': 'G>0 '
                                                                                                        'AND '
                                                                                                        'K+4*G/3>0',
                                                                                                  'full_energy_SPD': 'G>0 '
                                                                                                                     'AND '
                                                                                                                     'K>0',
                                                                                                  'negative_K_allowed_by_SE': True,
                                                                                                  'SE_is_bulk_energy_stability': False},
                                                                     'counterexample': {'conditions': 'finite_G>0; '
                                                                                                      'K=-G/3; '
                                                                                                      'finite_rho>0',
                                                                                        'lambda': '-G',
                                                                                        'Q': 'G*I_for_every_unit_n',
                                                                                        'c_squared': 'G/rho_with_multiplicity_three',
                                                                                        'hydrostatic_strain': 'epsilon=alpha*I, '
                                                                                                              'alpha!=0',
                                                                                        'energy': 'W=(9/2)*K*alpha^2=-(3/2)*G*alpha^2<0',
                                                                                        'full_strain_energy_SPD': False,
                                                                                        'division_by_K_plus_G_over_3': False},
                                                                     'fixed_tensor_bounds': {'scope': 'one_fixed_finite_strictly_SE_tensor_and_positive_finite_rho',
                                                                                             'minimum_squared_phase_speed': 'strictly_positive_attained_over_unit_sphere',
                                                                                             'maximum_squared_phase_speed': 'finite_attained_over_unit_sphere',
                                                                                             'basis': 'project_continuity_and_compactness_proof',
                                                                                             'universal_numerical_speed_bound': False},
                                                                     'proof_ids': ['W3_plane_wave_and_index_mapping',
                                                                                   'W4_SPD_implies_SE_and_counterexample',
                                                                                   'W5_fixed_tensor_compactness']},
                                              'dependencies': []}}
_FIELDS = {'quantity_dimension', 'required_assumptions', 'id', 'dependencies', 'claim_type', 'evidence', 'name', 'formula_display', 'si_unit', 'version', 'bulk_wave_contract', 'evaluation_support', 'quantity', 'direction', 'bound_kind', 'parameters', 'limits', 'verification', 'rule_id'}
_QUANTITIES = {contract['quantity'] for contract in WAVE_CONTRACTS.values()}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_wave_records(records, *, resolve_dependencies=False):
    """Reject altered science; allow fresh stable IDs, evidence and parameter order.

    Both relations are self-contained and have no claim dependencies. The
    keyword matches other catalog guards without adding a resolution engine.
    """
    if not isinstance(records, (list, tuple)):
        raise ValueError('wave validation requires a record sequence')
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('claim metadata must be an object')
        for key in ('id', 'rule_id', 'quantity'):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ValueError('claim ' + key + ' must be a nonempty string')
    if len({record['id'] for record in records}) != len(records):
        raise ValueError('duplicate claim IDs cannot shadow wave metadata')
    for record in records:
        rule = record['rule_id']
        if rule not in WAVE_CONTRACTS:
            if 'bulk_wave_contract' in record or record['quantity'] in _QUANTITIES:
                raise ValueError('bulk wave metadata requires a supported family')
            continue
        prefix = 'bulk wave claim ' + record['id']
        if set(record) != _FIELDS:
            raise ValueError(prefix + ': missing or foreign fields')
        try:
            _canonical(record)
            for key, expected in WAVE_CONTRACTS[rule].items():
                actual = record[key]
                if key == 'parameters':
                    if (not isinstance(actual, list) or
                            sorted(map(_canonical, actual)) != sorted(map(_canonical, expected))):
                        raise ValueError(prefix + ': parameter contract differs')
                elif _canonical(actual) != _canonical(expected):
                    raise ValueError(prefix + ': ' + key + ' differs from closed contract')
        except (TypeError, OverflowError) as exc:
            raise ValueError(prefix + ': metadata is not finite JSON') from exc
