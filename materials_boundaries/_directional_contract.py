"""Closed, dependency-free catalog metadata guards; no tensor calculation.

Display formulas are never executed. These contracts distinguish a material-class
range from finite extrema for one tensor. Runtime checks certify metadata shape,
not proof, source inspection, microscopic realizability or peer review.
"""
import json

DEFINITION_RULE = 'directional_poissons_ratio_definition_and_range_v1'
PAIR_RULE = 'directional_poisson_reciprocity_energy_constraint_v1'
DIRECTIONAL_CONTRACTS = {'directional_poissons_ratio_definition_and_range_v1': {'quantity': 'directional_poissons_ratio',
                                                        'direction': 'relation',
                                                        'claim_type': 'model_relation',
                                                        'bound_kind': None,
                                                        'quantity_dimension': 'dimensionless',
                                                        'si_unit': '1',
                                                        'evaluation_support': 'catalog_only',
                                                        'formula_display': 'nu(n,m)=-(m_i*m_j*S_ijkl*n_k*n_l)/(n_i*n_j*S_ijkl*n_k*n_l); '
                                                                           'E(n)=1/(n_i*n_j*S_ijkl*n_k*n_l); '
                                                                           'range over finite '
                                                                           'full-SPD 3D S and unit '
                                                                           'n perpendicular m is R',
                                                        'required_assumptions': {'spatial_dimension': 3,
                                                                                 'loading': 'static_uniaxial_stress',
                                                                                 'kinematics': 'infinitesimal_strain',
                                                                                 'constitutive_law': 'classical_local_linear_elastic',
                                                                                 'reference_state': 'stress_free_equilibrium',
                                                                                 'elastic_tensor': 'finite_real_with_minor_and_major_symmetries',
                                                                                 'stability': 'full_stiffness_positive_definite_on_all_nonzero_symmetric_strains_equivalently_full_compliance_SPD',
                                                                                 'compliance': 'full_inverse_of_stiffness_on_symmetric_tensors',
                                                                                 'directions': 'orthogonal_unit_vectors_n_loading_m_transverse',
                                                                                 'stress_sign': 'tension_positive',
                                                                                 'strain_sign': 'extension_positive',
                                                                                 'stress': 'sigma=t*(n_tensor_n), '
                                                                                           't_nonzero_sufficiently_small; '
                                                                                           'all_other_applied_stress_components_zero_in_loading_frame',
                                                                                 'axes': 'orthonormal_cartesian',
                                                                                 'matrix_convention': 'engineering_Voigt_order_11_22_33_23_13_12',
                                                                                 'engineering_strain': '(epsilon11,epsilon22,epsilon33,2epsilon23,2epsilon13,2epsilon12)',
                                                                                 'stress_vector': '(sigma11,sigma22,sigma33,sigma23,sigma13,sigma12)',
                                                                                 'matrix_relation': 'e=S_eng*s; '
                                                                                                    's=C_eng*e; '
                                                                                                    'S_eng=inverse(C_eng)',
                                                                                 'shear_conversion': 'S_eng_IJ=d_I*d_J*S_tensor_ij_kl, '
                                                                                                     'd=(1,1,1,2,2,2); '
                                                                                                     'C_eng_IJ=C_tensor_ij_kl; '
                                                                                                     'in '
                                                                                                     'particular '
                                                                                                     'S_eng_44=4*S2323',
                                                                                 'compliance_units': 'Pa^-1',
                                                                                 'stiffness_units': 'Pa',
                                                                                 'elastic_symmetry': 'no_additional_symmetry_required'},
                                                        'directional_contract': {'kind': 'definition_and_material_class_range',
                                                                                 'definition': {'ratio': 'nu(n,m)=-(mm:S:nn)/(nn:S:nn)',
                                                                                                'youngs_modulus': 'E(n)=1/(nn:S:nn)',
                                                                                                'loading_direction': 'n',
                                                                                                'transverse_direction': 'm',
                                                                                                'contraction': 'nn=n_tensor_n; '
                                                                                                               'mm=m_tensor_m; '
                                                                                                               'full_tensor_contraction'},
                                                                                 'material_class_range': {'classification': 'mathematical_range_within_stated_scope',
                                                                                                          'basis': 'published_two_sided_unboundedness_and_original_project_SPD_construction',
                                                                                                          'scope': 'varying_finite_full_SPD_3D_compliance_tensors_and_orthonormal_direction_pairs',
                                                                                                          'values': 'all_finite_real_numbers',
                                                                                                          'lower': {'status': 'unbounded_below'},
                                                                                                          'upper': {'status': 'unbounded_above'},
                                                                                                          'infinite_values_attained': False},
                                                                                 'fixed_tensor_extrema': {'scope': 'one_fixed_finite_full_SPD_3D_compliance_tensor',
                                                                                                          'values': 'finite',
                                                                                                          'minimum_attained': True,
                                                                                                          'maximum_attained': True,
                                                                                                          'basis': 'continuity_on_compact_orthonormal_pair_space_with_positive_denominator'},
                                                                                 'derivation_status': 'original_project_algebra_not_independent_scientific_peer_review'},
                                                        'parameters': None},
 'directional_poisson_reciprocity_energy_constraint_v1': {'quantity': 'directional_poissons_ratio',
                                                          'direction': 'relation',
                                                          'claim_type': 'model_relation',
                                                          'bound_kind': None,
                                                          'quantity_dimension': 'dimensionless',
                                                          'si_unit': '1',
                                                          'evaluation_support': 'catalog_only',
                                                          'formula_display': 'nu(n,m)/E(n)=nu(m,n)/E(m); '
                                                                             '|nu(n,m)|<sqrt(E(n)/E(m)); '
                                                                             '0<=nu(n,m)*nu(m,n)<1',
                                                          'required_assumptions': {'spatial_dimension': 3,
                                                                                   'loading': 'static_uniaxial_stress',
                                                                                   'kinematics': 'infinitesimal_strain',
                                                                                   'constitutive_law': 'classical_local_linear_elastic',
                                                                                   'reference_state': 'stress_free_equilibrium',
                                                                                   'elastic_tensor': 'finite_real_with_minor_and_major_symmetries',
                                                                                   'stability': 'full_stiffness_positive_definite_on_all_nonzero_symmetric_strains_equivalently_full_compliance_SPD',
                                                                                   'compliance': 'full_inverse_of_stiffness_on_symmetric_tensors',
                                                                                   'directions': 'orthogonal_unit_vectors_n_loading_m_transverse',
                                                                                   'stress_sign': 'tension_positive',
                                                                                   'strain_sign': 'extension_positive',
                                                                                   'stress': 'sigma=t*(n_tensor_n), '
                                                                                             't_nonzero_sufficiently_small; '
                                                                                             'all_other_applied_stress_components_zero_in_loading_frame',
                                                                                   'axes': 'orthonormal_cartesian',
                                                                                   'matrix_convention': 'engineering_Voigt_order_11_22_33_23_13_12',
                                                                                   'engineering_strain': '(epsilon11,epsilon22,epsilon33,2epsilon23,2epsilon13,2epsilon12)',
                                                                                   'stress_vector': '(sigma11,sigma22,sigma33,sigma23,sigma13,sigma12)',
                                                                                   'matrix_relation': 'e=S_eng*s; '
                                                                                                      's=C_eng*e; '
                                                                                                      'S_eng=inverse(C_eng)',
                                                                                   'shear_conversion': 'S_eng_IJ=d_I*d_J*S_tensor_ij_kl, '
                                                                                                       'd=(1,1,1,2,2,2); '
                                                                                                       'C_eng_IJ=C_tensor_ij_kl; '
                                                                                                       'in '
                                                                                                       'particular '
                                                                                                       'S_eng_44=4*S2323',
                                                                                   'compliance_units': 'Pa^-1',
                                                                                   'stiffness_units': 'Pa',
                                                                                   'elastic_symmetry': 'no_additional_symmetry_required'},
                                                          'directional_contract': {'kind': 'reciprocity_and_energy_pair_constraint',
                                                                                   'definition': {'ratio': 'nu(n,m)=-(mm:S:nn)/(nn:S:nn)',
                                                                                                  'youngs_modulus': 'E(n)=1/(nn:S:nn)',
                                                                                                  'loading_direction': 'n',
                                                                                                  'transverse_direction': 'm',
                                                                                                  'contraction': 'nn=n_tensor_n; '
                                                                                                                 'mm=m_tensor_m; '
                                                                                                                 'full_tensor_contraction'},
                                                                                   'reciprocity': {'expression': 'nu(n,m)/E(n)=nu(m,n)/E(m)',
                                                                                                   'basis': 'major_symmetry_of_same_full_compliance'},
                                                                                   'magnitude_constraint': {'expression': 'abs(nu(n,m))<sqrt(E(n)/E(m))',
                                                                                                            'strict': True,
                                                                                                            'equality_attained': False},
                                                                                   'pair_product': {'expression': 'nu(n,m)*nu(m,n)',
                                                                                                    'lower': {'value': 0,
                                                                                                              'inclusive': True},
                                                                                                    'upper': {'value': 1,
                                                                                                              'inclusive': False},
                                                                                                    'zero_condition': 'if_and_only_if_both_directional_ratios_are_zero'},
                                                                                   'same_sign_unless_both_zero': True,
                                                                                   'stability_implication': 'necessary_not_sufficient_for_full_SPD',
                                                                                   'universal_finite_numerical_bound': False,
                                                                                   'basis': 'strict_Cauchy_Schwarz_on_independent_nn_and_mm_in_full_SPD_inner_product',
                                                                                   'derivation_status': 'original_project_algebra_not_independent_scientific_peer_review'},
                                                          'parameters': [{'symbol': 'E(n)',
                                                                          'quantity': 'directional_youngs_modulus_loading_n',
                                                                          'dimension': 'pressure',
                                                                          'si_unit': 'Pa',
                                                                          'meaning': '1/(nn:S:nn), '
                                                                                     'strictly '
                                                                                     'positive for '
                                                                                     'the same '
                                                                                     'full '
                                                                                     'compliance S '
                                                                                     'used in nu.'},
                                                                         {'symbol': 'E(m)',
                                                                          'quantity': 'directional_youngs_modulus_loading_m',
                                                                          'dimension': 'pressure',
                                                                          'si_unit': 'Pa',
                                                                          'meaning': '1/(mm:S:mm), '
                                                                                     'strictly '
                                                                                     'positive for '
                                                                                     'the same '
                                                                                     'full '
                                                                                     'compliance '
                                                                                     'S, with the '
                                                                                     'loading and '
                                                                                     'transverse '
                                                                                     'directions '
                                                                                     'exchanged.'}]}}

_BASE_FIELDS = {'id', 'version', 'name', 'quantity', 'direction', 'rule_id',
                'formula_display', 'required_assumptions', 'evidence', 'verification',
                'limits', 'bound_kind', 'dependencies', 'claim_type',
                'quantity_dimension', 'si_unit', 'evaluation_support', 'directional_contract'}


def _canonical(value):
    # JSON comparison separates booleans from numbers and rejects NaN/infinity.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_directional_records(records, *, resolve_dependencies=False):
    """Reject weakened directional metadata, including on catalog-only rendering.

    Fresh record IDs and evidence can be appended under either exact family.
    Full-catalog callers also require each pair claim to depend on a definition
    record from this contract, not an isotropic Poisson or unrelated record.
    """
    by_id = {record.get('id'): record for record in records}
    if len(by_id) != len(records):
        raise ValueError('duplicate claim IDs cannot shadow directional metadata')
    for record in records:
        rule = record.get('rule_id')
        if rule not in DIRECTIONAL_CONTRACTS:
            if ('directional_contract' in record or
                    record.get('quantity') == 'directional_poissons_ratio'):
                raise ValueError('directional metadata requires a supported directional family')
            continue
        prefix = 'directional claim ' + str(record.get('id'))
        expected = DIRECTIONAL_CONTRACTS[rule]
        fields = _BASE_FIELDS | ({'parameters'} if expected['parameters'] is not None else set())
        if set(record) != fields:
            raise ValueError(prefix + ': missing or foreign fields')
        try:
            _canonical(record)
            for key, value in expected.items():
                if key == 'parameters':
                    if value is not None:
                        actual = record[key]
                        if not isinstance(actual, list) or sorted(map(_canonical, actual)) != sorted(map(_canonical, value)):
                            raise ValueError(prefix + ': parameter contract differs')
                elif _canonical(record[key]) != _canonical(value):
                    raise ValueError(prefix + ': ' + key + ' differs from closed contract')
        except (TypeError, OverflowError) as exc:
            raise ValueError(prefix + ': metadata is not finite JSON') from exc
        dependencies = record['dependencies']
        if rule == DEFINITION_RULE:
            if dependencies != []:
                raise ValueError(prefix + ': definition must have no dependencies')
        elif (not isinstance(dependencies, list) or len(dependencies) != 1 or
              not isinstance(dependencies[0], str) or not dependencies[0].strip()):
            raise ValueError(prefix + ': pair relation needs one definition dependency')
        elif resolve_dependencies and by_id.get(dependencies[0], {}).get('rule_id') != DEFINITION_RULE:
            raise ValueError(prefix + ': dependency must be a directional definition family')
