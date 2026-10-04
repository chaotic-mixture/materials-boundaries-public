"""Closed scalar viscoelastic catalog metadata; no constitutive evaluator.

Literal contracts are independent of mutable catalogs. Original project proofs
are documented separately; metadata validation is not scientific peer review.
"""
import json

DEFINITION_RULE = 'scalar_viscoelastic_creep_relaxation_duality_v1'
PRODUCT_RULE = 'scalar_viscoelastic_creep_relaxation_product_bound_v1'
VISCOELASTIC_CONTRACTS = {'scalar_viscoelastic_creep_relaxation_duality_v1': {'quantity': 'normalized_scalar_creep_relaxation_convolution',
                                                     'direction': 'relation',
                                                     'claim_type': 'model_relation',
                                                     'bound_kind': None,
                                                     'quantity_dimension': 'dimensionless',
                                                     'si_unit': '1',
                                                     'evaluation_support': 'catalog_only',
                                                     'formula_display': '(1/t)*integral_0^t R(t-s)*J(s) ds=1, finite '
                                                                        't>0; p^2*R_hat(p)*J_hat(p)=1, p>0',
                                                     'required_assumptions': {'channel': 'one_matched_scalar_reciprocal_stress_strain_channel',
                                                                              'kinematics': 'small_strain',
                                                                              'constitutive_law': 'causal_linear_time_translation_invariant_hereditary',
                                                                              'material_state': 'fixed_state_temperature_moisture_phase_and_chemistry',
                                                                              'prehistory': 'zero_stress_and_strain_before_zero; '
                                                                                            'initial_jumps_retained',
                                                                              'relaxation_kernel': 'ordinary_nonzero_completely_monotone_R_on_positive_time',
                                                                              'instantaneous_relaxation': 'finite_strictly_positive_R0=R(0+)',
                                                                              'newtonian_term': 'N=0; '
                                                                                                'no_additive_Dirac_impulse_in_relaxation',
                                                                              'creep_function': 'unique_reciprocal_Bernstein_J_in_the_declared_scalar_class',
                                                                              'loading_rates': 'may_change_under_the_same_fixed_linear_time_invariant_kernel',
                                                                              'time_domain': 'finite_t>0_for_normalized_identity_and_product_bound',
                                                                              'laplace_domain': 'real_p>0'},
                                                     'parameters': [{'symbol': 'R(t)',
                                                                     'quantity': 'scalar_relaxation_modulus',
                                                                     'dimension': 'pressure',
                                                                     'si_unit': 'Pa',
                                                                     'meaning': 'Ordinary nonzero completely monotone '
                                                                                'relaxation kernel; finite '
                                                                                'R0=R(0+)>0.'},
                                                                    {'symbol': 'J(t)',
                                                                     'quantity': 'reciprocal_scalar_creep_compliance',
                                                                     'dimension': 'inverse_pressure',
                                                                     'si_unit': 'Pa^-1',
                                                                     'meaning': 'Unique Bernstein reciprocal for the '
                                                                                'same scalar channel and fixed '
                                                                                'conditions; J0=1/R0.'},
                                                                    {'symbol': 't',
                                                                     'quantity': 'elapsed_time',
                                                                     'dimension': 'time',
                                                                     'si_unit': 's',
                                                                     'meaning': 'Finite strictly positive elapsed '
                                                                                'time; zero and infinity are limiting '
                                                                                'endpoints only.'},
                                                                    {'symbol': 'p',
                                                                     'quantity': 'laplace_variable',
                                                                     'dimension': 'inverse_time',
                                                                     'si_unit': 's^-1',
                                                                     'meaning': 'Real strictly positive Laplace '
                                                                                'variable; not a cyclic loading '
                                                                                'frequency.'}],
                                                     'viscoelastic_contract': {'class_definitions': {'complete_monotonicity': '(-1)^n '
                                                                                                                              'R^(n)(t)>=0 '
                                                                                                                              'for '
                                                                                                                              'every '
                                                                                                                              'integer '
                                                                                                                              'n>=0 '
                                                                                                                              'and '
                                                                                                                              'every '
                                                                                                                              't>0',
                                                                                                     'bernstein': 'J>=0 '
                                                                                                                  'and '
                                                                                                                  'J_prime '
                                                                                                                  'is '
                                                                                                                  'completely '
                                                                                                                  'monotone '
                                                                                                                  'on '
                                                                                                                  't>0',
                                                                                                     'weak_monotonicity': 'R '
                                                                                                                          'is '
                                                                                                                          'nonincreasing; '
                                                                                                                          'J '
                                                                                                                          'is '
                                                                                                                          'nondecreasing',
                                                                                                     'relaxation_spectrum': 'R(t)=integral_[0,infinity) '
                                                                                                                            'exp(-r*t) '
                                                                                                                            'mu(dr); '
                                                                                                                            '0<mu([0,infinity))=R0<infinity'},
                                                                               'causal_conventions': {'convolution': '(R*J)(t)=integral_0^t '
                                                                                                                     'R(t-s)*J(s) '
                                                                                                                     'ds',
                                                                                                      'constitutive_laws': 'sigma=R*D(epsilon); '
                                                                                                                           'epsilon=J*D(sigma), '
                                                                                                                           'with '
                                                                                                                           'causal '
                                                                                                                           'distributional '
                                                                                                                           'derivatives '
                                                                                                                           'including '
                                                                                                                           'initial '
                                                                                                                           'jumps',
                                                                                                      'initial_creep_jump': 'D(HJ)=J0*delta_0+H(t)*J_prime(t); '
                                                                                                                            'HJ '
                                                                                                                            'denotes '
                                                                                                                            'pointwise '
                                                                                                                            'causal '
                                                                                                                            'extension',
                                                                                                      'newtonian_caution': 'N=0 '
                                                                                                                           'excludes '
                                                                                                                           'an '
                                                                                                                           'additive '
                                                                                                                           'relaxation '
                                                                                                                           'impulse, '
                                                                                                                           'not '
                                                                                                                           'every '
                                                                                                                           'dashpot; '
                                                                                                                           'the '
                                                                                                                           'Maxwell '
                                                                                                                           'series '
                                                                                                                           'dashpot '
                                                                                                                           'is '
                                                                                                                           'admitted'},
                                                                               'units': {'R': 'Pa',
                                                                                         'J': 'Pa^-1',
                                                                                         't_and_R_convolved_with_J': 's',
                                                                                         'p': 's^-1',
                                                                                         'R_hat': 'Pa*s',
                                                                                         'J_hat': 'Pa^-1*s',
                                                                                         'normalized_convolution_and_same_time_product': '1'},
                                                                               'finite_interval_regularity': {'bernstein_representation': 'J(t)=J0+b*t+integral_(0,infinity) '
                                                                                                                                          '(1-exp(-r*t)) '
                                                                                                                                          'nu(dr); '
                                                                                                                                          'b>=0; '
                                                                                                                                          'integral '
                                                                                                                                          'min(1,r) '
                                                                                                                                          'nu(dr)<infinity',
                                                                                                              'integrable_derivative': 'For '
                                                                                                                                       'every '
                                                                                                                                       'finite '
                                                                                                                                       'T>0, '
                                                                                                                                       'Tonelli '
                                                                                                                                       'gives '
                                                                                                                                       'integral_0^T '
                                                                                                                                       'J_prime(s) '
                                                                                                                                       'ds=b*T+integral '
                                                                                                                                       '(1-exp(-r*T)) '
                                                                                                                                       'nu(dr)=J(T)-J0<infinity',
                                                                                                              'absolute_continuity': 'J(t)=J0+integral_0^t '
                                                                                                                                     'J_prime(s) '
                                                                                                                                     'ds, '
                                                                                                                                     'so '
                                                                                                                                     'J '
                                                                                                                                     'is '
                                                                                                                                     'absolutely '
                                                                                                                                     'continuous '
                                                                                                                                     'on '
                                                                                                                                     'every '
                                                                                                                                     '[0,T]',
                                                                                                              'finite_initial_slope_required': False,
                                                                                                              'differentiation': 'R '
                                                                                                                                 'is '
                                                                                                                                 'continuous '
                                                                                                                                 'on '
                                                                                                                                 '[0,T]; '
                                                                                                                                 'write '
                                                                                                                                 'R*J=J0*integral_0^t '
                                                                                                                                 'R(u) '
                                                                                                                                 'du+integral_0^t '
                                                                                                                                 '(R*J_prime)(u) '
                                                                                                                                 'du. '
                                                                                                                                 'The '
                                                                                                                                 'latter '
                                                                                                                                 'convolution '
                                                                                                                                 'is '
                                                                                                                                 'continuous, '
                                                                                                                                 'so '
                                                                                                                                 '1=J0*R(t)+(R*J_prime)(t) '
                                                                                                                                 'for '
                                                                                                                                 'every '
                                                                                                                                 't>0'},
                                                                               'endpoint_limits': {'initial': 'R0*J0=1',
                                                                                                   'positive_equilibrium_modulus': 'If '
                                                                                                                                   'Rinf>0 '
                                                                                                                                   'then '
                                                                                                                                   'Jinf=1/Rinf '
                                                                                                                                   'and '
                                                                                                                                   'lim_(t->infinity) '
                                                                                                                                   'R(t)*J(t)=1',
                                                                                                   'zero_equilibrium_modulus': 'If '
                                                                                                                               'Rinf=0 '
                                                                                                                               'then '
                                                                                                                               'Jinf=infinity; '
                                                                                                                               'no '
                                                                                                                               'universal '
                                                                                                                               'product '
                                                                                                                               'limit '
                                                                                                                               'is '
                                                                                                                               'inferred '
                                                                                                                               'from '
                                                                                                                               '0 '
                                                                                                                               'times '
                                                                                                                               'infinity',
                                                                                                   'pointwise_reciprocity_claimed': False},
                                                                               'source_attribution': {'duality': 'Hanyga '
                                                                                                                 '2018 '
                                                                                                                 'arXiv:1805.07275v1 '
                                                                                                                 'section '
                                                                                                                 '3 '
                                                                                                                 'Theorems '
                                                                                                                 '1-2; '
                                                                                                                 'Hanyga '
                                                                                                                 '2019 '
                                                                                                                 'arXiv:1903.03814v8 '
                                                                                                                 'section '
                                                                                                                 '2 '
                                                                                                                 'Eqs '
                                                                                                                 '(5)-(7), '
                                                                                                                 'N=0',
                                                                                                      'product_bound': 'original_project_proof_from_the_restricted_duality_not_a_separately_printed_Hanyga_theorem',
                                                                                                      'same_author_sources_are_independent_validation': False,
                                                                                                      'scientific_peer_review_certified': False,
                                                                                                      'passivity_equivalence_claimed': False},
                                                                               'scope_exclusions': ['aging_or_two_time_kernels',
                                                                                                    'nonlinear_or_finite_strain_response',
                                                                                                    'history_or_state_dependent_changes_to_the_kernel',
                                                                                                    'changing_material_state_or_temperature',
                                                                                                    'damage_plasticity_tertiary_creep_or_rupture',
                                                                                                    'singular_at_zero_relaxation_or_additive_Newtonian_impulse',
                                                                                                    'tensor_componentwise_substitution',
                                                                                                    'unmatched_channels_specimens_histories_or_conditions',
                                                                                                    'unverified_instrument_inertia_or_wave_effects'],
                                                                               'experimental_validation': False,
                                                                               'creep_strength_or_rupture_prediction': False,
                                                                               'numerical_evaluator': False,
                                                                               'kind': 'normalized_convolution_duality',
                                                                               'identity': '(R*J)(t)=t; (R*J)(t)/t=1 '
                                                                                           'for finite t>0; '
                                                                                           'p^2*R_hat(p)*J_hat(p)=1 '
                                                                                           'for p>0',
                                                                               'reciprocal_existence_and_uniqueness': 'Hanyga '
                                                                                                                      'Theorem '
                                                                                                                      '1 '
                                                                                                                      'with '
                                                                                                                      'beta=0 '
                                                                                                                      'supplies '
                                                                                                                      'Bernstein '
                                                                                                                      'J; '
                                                                                                                      'Laplace '
                                                                                                                      'uniqueness '
                                                                                                                      'within '
                                                                                                                      'the '
                                                                                                                      'stated '
                                                                                                                      'ordinary '
                                                                                                                      'continuous/Bernstein '
                                                                                                                      'class '
                                                                                                                      'fixes '
                                                                                                                      'it',
                                                                               'proof_ids': ['V1_restricted_duality',
                                                                                             'V2_finite_interval_AC_and_jump']}},
 'scalar_viscoelastic_creep_relaxation_product_bound_v1': {'quantity': 'scalar_creep_relaxation_same_time_product',
                                                           'direction': 'interval',
                                                           'claim_type': 'theoretical_bound',
                                                           'bound_kind': 'dimensionless_response_product_bound',
                                                           'quantity_dimension': 'dimensionless',
                                                           'si_unit': '1',
                                                           'evaluation_support': 'catalog_only',
                                                           'formula_display': '0<R(t)*J(t)<=1, for each finite t>0',
                                                           'required_assumptions': {'channel': 'one_matched_scalar_reciprocal_stress_strain_channel',
                                                                                    'kinematics': 'small_strain',
                                                                                    'constitutive_law': 'causal_linear_time_translation_invariant_hereditary',
                                                                                    'material_state': 'fixed_state_temperature_moisture_phase_and_chemistry',
                                                                                    'prehistory': 'zero_stress_and_strain_before_zero; '
                                                                                                  'initial_jumps_retained',
                                                                                    'relaxation_kernel': 'ordinary_nonzero_completely_monotone_R_on_positive_time',
                                                                                    'instantaneous_relaxation': 'finite_strictly_positive_R0=R(0+)',
                                                                                    'newtonian_term': 'N=0; '
                                                                                                      'no_additive_Dirac_impulse_in_relaxation',
                                                                                    'creep_function': 'unique_reciprocal_Bernstein_J_in_the_declared_scalar_class',
                                                                                    'loading_rates': 'may_change_under_the_same_fixed_linear_time_invariant_kernel',
                                                                                    'time_domain': 'finite_t>0_for_normalized_identity_and_product_bound',
                                                                                    'laplace_domain': 'real_p>0'},
                                                           'parameters': [{'symbol': 'R(t)',
                                                                           'quantity': 'scalar_relaxation_modulus',
                                                                           'dimension': 'pressure',
                                                                           'si_unit': 'Pa',
                                                                           'meaning': 'Ordinary nonzero completely '
                                                                                      'monotone relaxation kernel; '
                                                                                      'finite R0=R(0+)>0.'},
                                                                          {'symbol': 'J(t)',
                                                                           'quantity': 'reciprocal_scalar_creep_compliance',
                                                                           'dimension': 'inverse_pressure',
                                                                           'si_unit': 'Pa^-1',
                                                                           'meaning': 'Unique Bernstein reciprocal for '
                                                                                      'the same scalar channel and '
                                                                                      'fixed conditions; J0=1/R0.'},
                                                                          {'symbol': 't',
                                                                           'quantity': 'elapsed_time',
                                                                           'dimension': 'time',
                                                                           'si_unit': 's',
                                                                           'meaning': 'Finite strictly positive '
                                                                                      'elapsed time; zero and infinity '
                                                                                      'are limiting endpoints only.'},
                                                                          {'symbol': 'p',
                                                                           'quantity': 'laplace_variable',
                                                                           'dimension': 'inverse_time',
                                                                           'si_unit': 's^-1',
                                                                           'meaning': 'Real strictly positive Laplace '
                                                                                      'variable; not a cyclic loading '
                                                                                      'frequency.'}],
                                                           'viscoelastic_contract': {'class_definitions': {'complete_monotonicity': '(-1)^n '
                                                                                                                                    'R^(n)(t)>=0 '
                                                                                                                                    'for '
                                                                                                                                    'every '
                                                                                                                                    'integer '
                                                                                                                                    'n>=0 '
                                                                                                                                    'and '
                                                                                                                                    'every '
                                                                                                                                    't>0',
                                                                                                           'bernstein': 'J>=0 '
                                                                                                                        'and '
                                                                                                                        'J_prime '
                                                                                                                        'is '
                                                                                                                        'completely '
                                                                                                                        'monotone '
                                                                                                                        'on '
                                                                                                                        't>0',
                                                                                                           'weak_monotonicity': 'R '
                                                                                                                                'is '
                                                                                                                                'nonincreasing; '
                                                                                                                                'J '
                                                                                                                                'is '
                                                                                                                                'nondecreasing',
                                                                                                           'relaxation_spectrum': 'R(t)=integral_[0,infinity) '
                                                                                                                                  'exp(-r*t) '
                                                                                                                                  'mu(dr); '
                                                                                                                                  '0<mu([0,infinity))=R0<infinity'},
                                                                                     'causal_conventions': {'convolution': '(R*J)(t)=integral_0^t '
                                                                                                                           'R(t-s)*J(s) '
                                                                                                                           'ds',
                                                                                                            'constitutive_laws': 'sigma=R*D(epsilon); '
                                                                                                                                 'epsilon=J*D(sigma), '
                                                                                                                                 'with '
                                                                                                                                 'causal '
                                                                                                                                 'distributional '
                                                                                                                                 'derivatives '
                                                                                                                                 'including '
                                                                                                                                 'initial '
                                                                                                                                 'jumps',
                                                                                                            'initial_creep_jump': 'D(HJ)=J0*delta_0+H(t)*J_prime(t); '
                                                                                                                                  'HJ '
                                                                                                                                  'denotes '
                                                                                                                                  'pointwise '
                                                                                                                                  'causal '
                                                                                                                                  'extension',
                                                                                                            'newtonian_caution': 'N=0 '
                                                                                                                                 'excludes '
                                                                                                                                 'an '
                                                                                                                                 'additive '
                                                                                                                                 'relaxation '
                                                                                                                                 'impulse, '
                                                                                                                                 'not '
                                                                                                                                 'every '
                                                                                                                                 'dashpot; '
                                                                                                                                 'the '
                                                                                                                                 'Maxwell '
                                                                                                                                 'series '
                                                                                                                                 'dashpot '
                                                                                                                                 'is '
                                                                                                                                 'admitted'},
                                                                                     'units': {'R': 'Pa',
                                                                                               'J': 'Pa^-1',
                                                                                               't_and_R_convolved_with_J': 's',
                                                                                               'p': 's^-1',
                                                                                               'R_hat': 'Pa*s',
                                                                                               'J_hat': 'Pa^-1*s',
                                                                                               'normalized_convolution_and_same_time_product': '1'},
                                                                                     'finite_interval_regularity': {'bernstein_representation': 'J(t)=J0+b*t+integral_(0,infinity) '
                                                                                                                                                '(1-exp(-r*t)) '
                                                                                                                                                'nu(dr); '
                                                                                                                                                'b>=0; '
                                                                                                                                                'integral '
                                                                                                                                                'min(1,r) '
                                                                                                                                                'nu(dr)<infinity',
                                                                                                                    'integrable_derivative': 'For '
                                                                                                                                             'every '
                                                                                                                                             'finite '
                                                                                                                                             'T>0, '
                                                                                                                                             'Tonelli '
                                                                                                                                             'gives '
                                                                                                                                             'integral_0^T '
                                                                                                                                             'J_prime(s) '
                                                                                                                                             'ds=b*T+integral '
                                                                                                                                             '(1-exp(-r*T)) '
                                                                                                                                             'nu(dr)=J(T)-J0<infinity',
                                                                                                                    'absolute_continuity': 'J(t)=J0+integral_0^t '
                                                                                                                                           'J_prime(s) '
                                                                                                                                           'ds, '
                                                                                                                                           'so '
                                                                                                                                           'J '
                                                                                                                                           'is '
                                                                                                                                           'absolutely '
                                                                                                                                           'continuous '
                                                                                                                                           'on '
                                                                                                                                           'every '
                                                                                                                                           '[0,T]',
                                                                                                                    'finite_initial_slope_required': False,
                                                                                                                    'differentiation': 'R '
                                                                                                                                       'is '
                                                                                                                                       'continuous '
                                                                                                                                       'on '
                                                                                                                                       '[0,T]; '
                                                                                                                                       'write '
                                                                                                                                       'R*J=J0*integral_0^t '
                                                                                                                                       'R(u) '
                                                                                                                                       'du+integral_0^t '
                                                                                                                                       '(R*J_prime)(u) '
                                                                                                                                       'du. '
                                                                                                                                       'The '
                                                                                                                                       'latter '
                                                                                                                                       'convolution '
                                                                                                                                       'is '
                                                                                                                                       'continuous, '
                                                                                                                                       'so '
                                                                                                                                       '1=J0*R(t)+(R*J_prime)(t) '
                                                                                                                                       'for '
                                                                                                                                       'every '
                                                                                                                                       't>0'},
                                                                                     'endpoint_limits': {'initial': 'R0*J0=1',
                                                                                                         'positive_equilibrium_modulus': 'If '
                                                                                                                                         'Rinf>0 '
                                                                                                                                         'then '
                                                                                                                                         'Jinf=1/Rinf '
                                                                                                                                         'and '
                                                                                                                                         'lim_(t->infinity) '
                                                                                                                                         'R(t)*J(t)=1',
                                                                                                         'zero_equilibrium_modulus': 'If '
                                                                                                                                     'Rinf=0 '
                                                                                                                                     'then '
                                                                                                                                     'Jinf=infinity; '
                                                                                                                                     'no '
                                                                                                                                     'universal '
                                                                                                                                     'product '
                                                                                                                                     'limit '
                                                                                                                                     'is '
                                                                                                                                     'inferred '
                                                                                                                                     'from '
                                                                                                                                     '0 '
                                                                                                                                     'times '
                                                                                                                                     'infinity',
                                                                                                         'pointwise_reciprocity_claimed': False},
                                                                                     'source_attribution': {'duality': 'Hanyga '
                                                                                                                       '2018 '
                                                                                                                       'arXiv:1805.07275v1 '
                                                                                                                       'section '
                                                                                                                       '3 '
                                                                                                                       'Theorems '
                                                                                                                       '1-2; '
                                                                                                                       'Hanyga '
                                                                                                                       '2019 '
                                                                                                                       'arXiv:1903.03814v8 '
                                                                                                                       'section '
                                                                                                                       '2 '
                                                                                                                       'Eqs '
                                                                                                                       '(5)-(7), '
                                                                                                                       'N=0',
                                                                                                            'product_bound': 'original_project_proof_from_the_restricted_duality_not_a_separately_printed_Hanyga_theorem',
                                                                                                            'same_author_sources_are_independent_validation': False,
                                                                                                            'scientific_peer_review_certified': False,
                                                                                                            'passivity_equivalence_claimed': False},
                                                                                     'scope_exclusions': ['aging_or_two_time_kernels',
                                                                                                          'nonlinear_or_finite_strain_response',
                                                                                                          'history_or_state_dependent_changes_to_the_kernel',
                                                                                                          'changing_material_state_or_temperature',
                                                                                                          'damage_plasticity_tertiary_creep_or_rupture',
                                                                                                          'singular_at_zero_relaxation_or_additive_Newtonian_impulse',
                                                                                                          'tensor_componentwise_substitution',
                                                                                                          'unmatched_channels_specimens_histories_or_conditions',
                                                                                                          'unverified_instrument_inertia_or_wave_effects'],
                                                                                     'experimental_validation': False,
                                                                                     'creep_strength_or_rupture_prediction': False,
                                                                                     'numerical_evaluator': False,
                                                                                     'kind': 'conditional_same_time_product_bound',
                                                                                     'range': {'lower': {'value': 0,
                                                                                                         'inclusive': False,
                                                                                                         'attained': False,
                                                                                                         'is_infimum': True},
                                                                                               'upper': {'value': 1,
                                                                                                         'inclusive': True,
                                                                                                         'attained_by': 'pure_elastic_member'},
                                                                                               'quantifier': 'across_the_declared_class_at_each_fixed_finite_t>0',
                                                                                               'absolute_modulus_or_compliance_bound': False},
                                                                                     'original_proof': {'difference_identity': '1-R(t)*J(t)=integral_0^t '
                                                                                                                               '[R(t-s)-R(t)]*J_prime(s) '
                                                                                                                               'ds>=0',
                                                                                                        'strict_positivity': 'R(t)>0 '
                                                                                                                             'at '
                                                                                                                             'every '
                                                                                                                             'finite '
                                                                                                                             'time '
                                                                                                                             'from '
                                                                                                                             'its '
                                                                                                                             'nonzero '
                                                                                                                             'nonnegative '
                                                                                                                             'finite '
                                                                                                                             'spectrum; '
                                                                                                                             'J(t)>=J0>0',
                                                                                                        'initial_jump_term_retained': True},
                                                                                     'synthetic_examples': {'maxwell': {'conditions': 'R0>0; '
                                                                                                                                      'tau>0',
                                                                                                                        'R': 'R0*exp(-t/tau)',
                                                                                                                        'J': '(1+t/tau)/R0',
                                                                                                                        'product': '(1+x)*exp(-x), '
                                                                                                                                   'x=t/tau',
                                                                                                                        'sharpness': 'At '
                                                                                                                                     'fixed '
                                                                                                                                     't>0, '
                                                                                                                                     'varying '
                                                                                                                                     'tau '
                                                                                                                                     'realizes '
                                                                                                                                     'every '
                                                                                                                                     'product '
                                                                                                                                     'in '
                                                                                                                                     '(0,1); '
                                                                                                                                     'a '
                                                                                                                                     'pure '
                                                                                                                                     'spring '
                                                                                                                                     'realizes '
                                                                                                                                     '1; '
                                                                                                                                     'zero '
                                                                                                                                     'is '
                                                                                                                                     'not '
                                                                                                                                     'attained'},
                                                                                                            'standard_linear_solid': {'conditions': 'E>0; '
                                                                                                                                                    'tau>0',
                                                                                                                                      'R': 'E*(1+exp(-t/tau))',
                                                                                                                                      'J': '(1-0.5*exp(-t/(2*tau)))/E',
                                                                                                                                      'gap': '1-R(t)*J(t)=q*(1-q)^2/2, '
                                                                                                                                             'q=exp(-t/(2*tau))',
                                                                                                                                      'nonmonotone_product': True},
                                                                                                            'measured_data': False},
                                                                                     'proof_ids': ['V2_finite_interval_AC_and_jump',
                                                                                                   'V3_product_bound_and_sharpness',
                                                                                                   'V4_nonmonotone_SLS_product']}}}

_FIELDS = {'id', 'version', 'name', 'quantity', 'direction', 'rule_id',
           'formula_display', 'required_assumptions', 'evidence', 'verification',
           'limits', 'bound_kind', 'dependencies', 'claim_type',
           'quantity_dimension', 'si_unit', 'evaluation_support', 'parameters',
           'viscoelastic_contract'}
_QUANTITIES = {'normalized_scalar_creep_relaxation_convolution',
               'scalar_creep_relaxation_same_time_product'}


def _canonical(value):
    # Reject nonfinite JSON and distinguish booleans from numeric constants.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_viscoelastic_records(records, *, resolve_dependencies=False):
    """Validate closed science while allowing fresh IDs and source curation.

    Full catalogs resolve product-bound dependencies by definition family,
    not by one privileged record ID. Parameters may be reordered.
    """
    if not isinstance(records, (list, tuple)):
        raise ValueError('viscoelastic validation requires a record sequence')
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('claim metadata must be an object')
        for key in ('id', 'rule_id', 'quantity'):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ValueError('claim ' + key + ' must be a nonempty string')
    by_id = {record['id']: record for record in records}
    if len(by_id) != len(records):
        raise ValueError('duplicate claim IDs cannot shadow viscoelastic metadata')
    for record in records:
        rule = record.get('rule_id')
        if rule not in VISCOELASTIC_CONTRACTS:
            if ('viscoelastic_contract' in record or
                    record.get('quantity') in _QUANTITIES or
                    record.get('bound_kind') == 'dimensionless_response_product_bound' or
                    any(isinstance(p, dict) and p.get('dimension') in {'time', 'inverse_time'}
                        for p in (record.get('parameters') if isinstance(record.get('parameters'), list) else []))):
                raise ValueError('viscoelastic metadata requires a supported family')
            continue
        prefix = 'viscoelastic claim ' + str(record.get('id'))
        if set(record) != _FIELDS:
            raise ValueError(prefix + ': missing or foreign fields')
        try:
            _canonical(record)
            for key, expected in VISCOELASTIC_CONTRACTS[rule].items():
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
            raise ValueError(prefix + ': product bound needs one definition dependency')
        elif resolve_dependencies and by_id.get(dependencies[0], {}).get('rule_id') != DEFINITION_RULE:
            raise ValueError(prefix + ': dependency must be a scalar duality family')
