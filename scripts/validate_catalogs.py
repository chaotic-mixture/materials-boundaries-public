#!/usr/bin/env python3
"""Development-only, offline catalog integrity checks; not scientific proof.

Requires the project's jsonschema development extra. Never adds execution
support, changes source/review/license status, fetches references, or writes data.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
import json
from pathlib import Path
import string
import sys
from threading import Lock
from types import FunctionType

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema import validators as _schema_validators
    from referencing import Registry, Resource
    from referencing.exceptions import NoSuchResource
except ImportError as exc:
    raise SystemExit("Catalog validation requires jsonschema; install with: python -m pip install -e '.[dev]'") from exc

from materials_boundaries.engine import BASE_RULES, DERIVED_RULES
from materials_boundaries.validation import ValidationError, load_json
from materials_boundaries._directional_contract import DIRECTIONAL_CONTRACTS, validate_directional_records
from materials_boundaries._wave_contract import WAVE_CONTRACTS, validate_wave_records
from materials_boundaries._compressibility_contract import COMPRESSIBILITY_CONTRACTS, validate_compressibility_records

CATALOGS = ("claims", "sources", "observations", "temperature_models", "computational_predictions")
LOCALE_CATALOGS = ("locales", "temperature_locales", "prediction_locales")
LANGUAGES = {"en", "zh", "ja", "de"}
# These pre-alias records retain canonical names. Every new record needs four
# authored labels; the exemption is by exact historical ID, never by family.
LEGACY_CANONICAL_NAMES = {
    "hs_bulk_3d_two_phase", "reuss_bulk", "voigt_bulk",
    "hs_shear_3d_two_phase", "reuss_shear", "voigt_shear",
    "youngs_modulus_outer", "poissons_ratio_outer",
    "griffith_central_crack_plane_stress", "griffith_central_crack_plane_strain",
}
EXPECTED_EXECUTABLE_PAIRS = {
    ("hs_bulk_3d_two_phase", "hs_bulk_3d_two_phase_v1"),
    ("reuss_bulk", "reuss_bulk_v1"), ("voigt_bulk", "voigt_bulk_v1"),
    ("hs_shear_3d_two_phase", "hs_shear_3d_two_phase_v1"),
    ("reuss_shear", "reuss_shear_v1"), ("voigt_shear", "voigt_shear_v1"),
    ("youngs_modulus_outer", "isotropic_youngs_modulus_outer_v1"),
    ("poissons_ratio_outer", "isotropic_poissons_ratio_outer_v1"),
}

# Development-only closed family contracts, independent of mutable candidate data.
# Some public schema branches constrain only their distinguishing assumptions;
# this guard also requires every shared premise and its exact value/type.
# A new scientific family requires explicit reviewed development/schema work.
SUPPORTED_FAMILY_ASSUMPTIONS = {'hs_bulk_3d_two_phase_v1': {'dimension': 3,
                             'constituent_symmetry': 'isotropic',
                             'effective_symmetry': 'isotropic',
                             'kinematics': 'small_strain',
                             'constitutive_law': 'linear_elastic',
                             'loading': 'static',
                             'interface': 'perfectly_bonded',
                             'two_phase_description': 2,
                             'positive_bulk_moduli': True,
                             'positive_shear_moduli': True,
                             'volume_fractions_known': True,
                             'well_ordered_phases': True},
 'reuss_bulk_v1': {'dimension': 3,
                   'constituent_symmetry': 'isotropic',
                   'effective_symmetry': 'isotropic',
                   'kinematics': 'small_strain',
                   'constitutive_law': 'linear_elastic',
                   'loading': 'static',
                   'interface': 'perfectly_bonded',
                   'two_phase_description': 2,
                   'positive_bulk_moduli': True,
                   'positive_shear_moduli': True,
                   'volume_fractions_known': True},
 'voigt_bulk_v1': {'dimension': 3,
                   'constituent_symmetry': 'isotropic',
                   'effective_symmetry': 'isotropic',
                   'kinematics': 'small_strain',
                   'constitutive_law': 'linear_elastic',
                   'loading': 'static',
                   'interface': 'perfectly_bonded',
                   'two_phase_description': 2,
                   'positive_bulk_moduli': True,
                   'positive_shear_moduli': True,
                   'volume_fractions_known': True},
 'hs_shear_3d_two_phase_v1': {'dimension': 3,
                              'constituent_symmetry': 'isotropic',
                              'effective_symmetry': 'isotropic',
                              'kinematics': 'small_strain',
                              'constitutive_law': 'linear_elastic',
                              'loading': 'static',
                              'interface': 'perfectly_bonded',
                              'two_phase_description': 2,
                              'positive_bulk_moduli': True,
                              'positive_shear_moduli': True,
                              'volume_fractions_known': True,
                              'well_ordered_phases': True},
 'reuss_shear_v1': {'dimension': 3,
                    'constituent_symmetry': 'isotropic',
                    'effective_symmetry': 'isotropic',
                    'kinematics': 'small_strain',
                    'constitutive_law': 'linear_elastic',
                    'loading': 'static',
                    'interface': 'perfectly_bonded',
                    'two_phase_description': 2,
                    'positive_bulk_moduli': True,
                    'positive_shear_moduli': True,
                    'volume_fractions_known': True},
 'voigt_shear_v1': {'dimension': 3,
                    'constituent_symmetry': 'isotropic',
                    'effective_symmetry': 'isotropic',
                    'kinematics': 'small_strain',
                    'constitutive_law': 'linear_elastic',
                    'loading': 'static',
                    'interface': 'perfectly_bonded',
                    'two_phase_description': 2,
                    'positive_bulk_moduli': True,
                    'positive_shear_moduli': True,
                    'volume_fractions_known': True},
 'isotropic_youngs_modulus_outer_v1': {'dimension': 3,
                                       'constituent_symmetry': 'isotropic',
                                       'effective_symmetry': 'isotropic',
                                       'kinematics': 'small_strain',
                                       'constitutive_law': 'linear_elastic',
                                       'loading': 'static',
                                       'interface': 'perfectly_bonded',
                                       'two_phase_description': 2,
                                       'positive_bulk_moduli': True,
                                       'positive_shear_moduli': True,
                                       'volume_fractions_known': True,
                                       'well_ordered_phases': True,
                                       'compatible_bulk_shear_bounds': True},
 'isotropic_poissons_ratio_outer_v1': {'dimension': 3,
                                       'constituent_symmetry': 'isotropic',
                                       'effective_symmetry': 'isotropic',
                                       'kinematics': 'small_strain',
                                       'constitutive_law': 'linear_elastic',
                                       'loading': 'static',
                                       'interface': 'perfectly_bonded',
                                       'two_phase_description': 2,
                                       'positive_bulk_moduli': True,
                                       'positive_shear_moduli': True,
                                       'volume_fractions_known': True,
                                       'well_ordered_phases': True,
                                       'compatible_bulk_shear_bounds': True},
 'griffith_central_crack_plane_stress_model_v1': {'material_symmetry': 'homogeneous_isotropic',
                                                  'constitutive_law': 'linear_elastic',
                                                  'kinematics': 'small_strain',
                                                  'geometry': 'infinite_plate_central_through_crack',
                                                  'crack_length_convention': 'a_is_half_total_length_2a',
                                                  'loading': 'remote_uniform_tension_normal_to_crack',
                                                  'crack_mode': 'mode_I',
                                                  'crack_faces': 'traction_free',
                                                  'loading_regime': 'quasi_static',
                                                  'plane_state': 'plane_stress',
                                                  'crack_tip_process_zone': 'negligible_relative_to_crack_and_body',
                                                  'fracture_criterion': 'G_reaches_supplied_positive_Gc',
                                                  'fracture_resistance': 'constant_Gc_at_initiation',
                                                  'positive_youngs_modulus': True,
                                                  'positive_crack_half_length': True,
                                                  'positive_critical_energy_release_rate': True,
                                                  'continuum_crack_scale': True},
 'griffith_central_crack_plane_strain_model_v1': {'material_symmetry': 'homogeneous_isotropic',
                                                  'constitutive_law': 'linear_elastic',
                                                  'kinematics': 'small_strain',
                                                  'geometry': 'infinite_plate_central_through_crack',
                                                  'crack_length_convention': 'a_is_half_total_length_2a',
                                                  'loading': 'remote_uniform_tension_normal_to_crack',
                                                  'crack_mode': 'mode_I',
                                                  'crack_faces': 'traction_free',
                                                  'loading_regime': 'quasi_static',
                                                  'plane_state': 'plane_strain',
                                                  'crack_tip_process_zone': 'negligible_relative_to_crack_and_body',
                                                  'fracture_criterion': 'G_reaches_supplied_positive_Gc',
                                                  'fracture_resistance': 'constant_Gc_at_initiation',
                                                  'positive_youngs_modulus': True,
                                                  'positive_crack_half_length': True,
                                                  'positive_critical_energy_release_rate': True,
                                                  'continuum_crack_scale': True,
                                                  'physical_poissons_ratio': True},
 'frenkel_slip_specific_ideal_shear_v1': {'crystal_state': 'ideal_defect_free',
                                          'slip_system': 'explicit_plane_and_direction',
                                          'restoring_traction': 'sinusoidal',
                                          'calibration': 'initial_slip_specific_shear_stiffness',
                                          'loading_and_relaxation_constraints': 'explicit_and_consistent_with_G_slip',
                                          'positive_G_slip': True,
                                          'positive_b': True,
                                          'positive_h': True},
 'uber_normal_cohesive_strength_v1': {'geometry': 'specified_planar_cleavage_or_interface',
                                      'opening_mode': 'constrained_normal_opening',
                                      'cohesive_law': 'two_parameter_UBER',
                                      'energy_reference': 'zero_at_infinite_separation',
                                      'opening_reference': 'equilibrium_separation',
                                      'tensile_branch': 'delta>=0',
                                      'positive_W_sep': True,
                                      'positive_lambda': True,
                                      'plane_constraints_relaxation_temperature_and_impurity_ensemble': 'explicitly_specified'},
 'lefm_central_crack_mode_i_stress_intensity_v1': {'material_symmetry': 'homogeneous_isotropic',
                                                   'strain_regime': 'small_strain',
                                                   'constitutive_behavior': 'linear_elastic',
                                                   'loading_regime': 'quasi_static',
                                                   'crack_mode': 'mode_I',
                                                   'crack_faces': 'traction_free',
                                                   'crack_tip_process_zone': 'negligible_relative_to_crack_and_body',
                                                   'geometry': 'infinite_plate_central_through_crack',
                                                   'crack_length_convention': 'a_is_half_total_length_2a',
                                                   'loading': 'remote_uniform_tension_normal_to_crack',
                                                   'positive_crack_half_length': True,
                                                   'continuum_crack_scale': True},
 'lefm_mode_i_energy_release_relation_v1': {'material_symmetry': 'homogeneous_isotropic',
                                            'strain_regime': 'small_strain',
                                            'constitutive_behavior': 'linear_elastic',
                                            'loading_regime': 'quasi_static',
                                            'crack_mode': 'mode_I',
                                            'crack_faces': 'traction_free',
                                            'crack_tip_process_zone': 'negligible_relative_to_crack_and_body',
                                            'plane_state': 'explicit_plane_stress_or_plane_strain',
                                            'positive_youngs_modulus': True,
                                            'physical_poissons_ratio_when_plane_strain': True,
                                            'stress_intensity_description': 'valid_for_the_selected_cracked_body'},
 'lefm_center_crack_finite_width_secant_factor_v1': {'material_symmetry': 'homogeneous_isotropic',
                                                     'strain_regime': 'small_strain',
                                                     'constitutive_behavior': 'linear_elastic',
                                                     'loading_regime': 'quasi_static',
                                                     'crack_mode': 'mode_I',
                                                     'crack_faces': 'traction_free',
                                                     'crack_tip_process_zone': 'negligible_relative_to_crack_and_body',
                                                     'geometry': 'centered_through_crack_in_finite_width_strip',
                                                     'crack_length_convention': 'a_is_half_total_length_2a',
                                                     'width_convention': 'W_is_full_sheet_width',
                                                     'range': '0<2a/W<=0.8',
                                                     'loading': 'remote_uniform_gross_tension_normal_to_crack',
                                                     'end_effects': 'negligible',
                                                     'plasticity_correction': 'none_a_bar_equals_a',
                                                     'continuum_crack_scale': True},
 'general_stiffness_positive_definite_v1': {'spatial_dimension': 3,
                                            'reference_state': 'stress_free_equilibrium',
                                            'strain_regime': 'infinitesimal',
                                            'energy_approximation': 'harmonic_quadratic',
                                            'perturbation_class': 'homogeneous_strain',
                                            'stiffness_symmetry': 'real_symmetric_6_by_6',
                                            'stiffness_convention': 'engineering_voigt',
                                            'axes': 'orthonormal_cartesian_any_orientation',
                                            'stiffness_units': 'common_pressure_unit',
                                            'elastic_symmetry': 'arbitrary_anisotropic'},
 'cubic_born_stability_v1': {'spatial_dimension': 3,
                             'reference_state': 'stress_free_equilibrium',
                             'strain_regime': 'infinitesimal',
                             'energy_approximation': 'harmonic_quadratic',
                             'perturbation_class': 'homogeneous_strain',
                             'stiffness_symmetry': 'real_symmetric_6_by_6',
                             'stiffness_convention': 'engineering_voigt',
                             'axes': 'aligned_with_declared_symmetry_template',
                             'stiffness_units': 'common_pressure_unit',
                             'elastic_symmetry': 'cubic'},
 'hexagonal_born_stability_v1': {'spatial_dimension': 3,
                                 'reference_state': 'stress_free_equilibrium',
                                 'strain_regime': 'infinitesimal',
                                 'energy_approximation': 'harmonic_quadratic',
                                 'perturbation_class': 'homogeneous_strain',
                                 'stiffness_symmetry': 'real_symmetric_6_by_6',
                                 'stiffness_convention': 'engineering_voigt',
                                 'axes': 'aligned_with_declared_symmetry_template',
                                 'stiffness_units': 'common_pressure_unit',
                                 'elastic_symmetry': 'hexagonal'},
 'orthorhombic_born_stability_v1': {'spatial_dimension': 3,
                                    'reference_state': 'stress_free_equilibrium',
                                    'strain_regime': 'infinitesimal',
                                    'energy_approximation': 'harmonic_quadratic',
                                    'perturbation_class': 'homogeneous_strain',
                                    'stiffness_symmetry': 'real_symmetric_6_by_6',
                                    'stiffness_convention': 'engineering_voigt',
                                    'axes': 'aligned_with_declared_symmetry_template',
                                    'stiffness_units': 'common_pressure_unit',
                                    'elastic_symmetry': 'orthorhombic'},
 'hs_porous_bulk_3d_solid_void_v1': {'dimension': 3,
                                     'constituent_symmetry': 'isotropic_solid',
                                     'effective_symmetry': 'isotropic',
                                     'kinematics': 'small_strain',
                                     'constitutive_law': 'linear_elastic',
                                     'loading': 'static',
                                     'reference_state': 'unstressed_without_contact_changes',
                                     'effective_scale': 'homogenized_macroscopic',
                                     'phase_description': 'one_homogeneous_elastic_solid_and_void',
                                     'positive_solid_bulk_modulus': True,
                                     'positive_solid_shear_modulus': True,
                                     'void_bulk_and_shear_moduli_zero': True,
                                     'porosity': 'known_void_volume_fraction_between_zero_and_one',
                                     'pore_surface': 'traction_free',
                                     'geometry_class': 'unrestricted_including_disconnected_solid',
                                     'continuum_model': 'local_classical_elasticity_without_surface_elasticity',
                                     'effective_homogeneity': 'homogeneous_in_the_homogenized_limit',
                                     'isotropic_zero_phase_limit': 'declared_isotropy_preserved_under_vanishing_positive_stiffness_regularization'},
 'hs_porous_shear_3d_solid_void_v1': {'dimension': 3,
                                      'constituent_symmetry': 'isotropic_solid',
                                      'effective_symmetry': 'isotropic',
                                      'kinematics': 'small_strain',
                                      'constitutive_law': 'linear_elastic',
                                      'loading': 'static',
                                      'reference_state': 'unstressed_without_contact_changes',
                                      'effective_scale': 'homogenized_macroscopic',
                                      'phase_description': 'one_homogeneous_elastic_solid_and_void',
                                      'positive_solid_bulk_modulus': True,
                                      'positive_solid_shear_modulus': True,
                                      'void_bulk_and_shear_moduli_zero': True,
                                      'porosity': 'known_void_volume_fraction_between_zero_and_one',
                                      'pore_surface': 'traction_free',
                                      'geometry_class': 'unrestricted_including_disconnected_solid',
                                      'continuum_model': 'local_classical_elasticity_without_surface_elasticity',
                                      'effective_homogeneity': 'homogeneous_in_the_homogenized_limit',
                                      'isotropic_zero_phase_limit': 'declared_isotropy_preserved_under_vanishing_positive_stiffness_regularization'},
 'hs_porous_youngs_outer_3d_solid_void_v1': {'dimension': 3,
                                             'constituent_symmetry': 'isotropic_solid',
                                             'effective_symmetry': 'isotropic',
                                             'kinematics': 'small_strain',
                                             'constitutive_law': 'linear_elastic',
                                             'loading': 'static',
                                             'reference_state': 'unstressed_without_contact_changes',
                                             'effective_scale': 'homogenized_macroscopic',
                                             'phase_description': 'one_homogeneous_elastic_solid_and_void',
                                             'positive_solid_bulk_modulus': True,
                                             'positive_solid_shear_modulus': True,
                                             'void_bulk_and_shear_moduli_zero': True,
                                             'porosity': 'known_void_volume_fraction_between_zero_and_one',
                                             'pore_surface': 'traction_free',
                                             'geometry_class': 'unrestricted_including_disconnected_solid',
                                             'continuum_model': 'local_classical_elasticity_without_surface_elasticity',
                                             'compatible_bulk_shear_bounds': True,
                                             'effective_homogeneity': 'homogeneous_in_the_homogenized_limit',
                                             'isotropic_zero_phase_limit': 'declared_isotropy_preserved_under_vanishing_positive_stiffness_regularization'},
 'tetragonal_i_born_stability_v1': {'spatial_dimension': 3,
                                    'reference_state': 'stress_free_equilibrium',
                                    'strain_regime': 'infinitesimal',
                                    'energy_approximation': 'harmonic_quadratic',
                                    'perturbation_class': 'homogeneous_strain',
                                    'stiffness_symmetry': 'real_symmetric_6_by_6',
                                    'stiffness_convention': 'engineering_voigt',
                                    'axes': 'aligned_with_declared_symmetry_template',
                                    'stiffness_units': 'common_pressure_unit',
                                    'elastic_symmetry': 'tetragonal_i'},
 'tetragonal_ii_born_stability_v1': {'spatial_dimension': 3,
                                     'reference_state': 'stress_free_equilibrium',
                                     'strain_regime': 'infinitesimal',
                                     'energy_approximation': 'harmonic_quadratic',
                                     'perturbation_class': 'homogeneous_strain',
                                     'stiffness_symmetry': 'real_symmetric_6_by_6',
                                     'stiffness_convention': 'engineering_voigt',
                                     'axes': 'aligned_with_declared_symmetry_template',
                                     'stiffness_units': 'common_pressure_unit',
                                     'elastic_symmetry': 'tetragonal_ii'},
 'rhombohedral_i_born_stability_v1': {'spatial_dimension': 3,
                                      'reference_state': 'stress_free_equilibrium',
                                      'strain_regime': 'infinitesimal',
                                      'energy_approximation': 'harmonic_quadratic',
                                      'perturbation_class': 'homogeneous_strain',
                                      'stiffness_symmetry': 'real_symmetric_6_by_6',
                                      'stiffness_convention': 'engineering_voigt',
                                      'axes': 'aligned_with_declared_symmetry_template',
                                      'stiffness_units': 'common_pressure_unit',
                                      'elastic_symmetry': 'rhombohedral_i'},
 'rhombohedral_ii_born_stability_v1': {'spatial_dimension': 3,
                                       'reference_state': 'stress_free_equilibrium',
                                       'strain_regime': 'infinitesimal',
                                       'energy_approximation': 'harmonic_quadratic',
                                       'perturbation_class': 'homogeneous_strain',
                                       'stiffness_symmetry': 'real_symmetric_6_by_6',
                                       'stiffness_convention': 'engineering_voigt',
                                       'axes': 'aligned_with_declared_symmetry_template',
                                       'stiffness_units': 'common_pressure_unit',
                                       'elastic_symmetry': 'rhombohedral_ii'}}

FAMILY_IDENTITY_FIELDS = ('quantity', 'direction', 'claim_type', 'bound_kind', 'quantity_dimension', 'si_unit', 'evaluation_support')
SUPPORTED_FAMILY_IDENTITIES = {'hs_bulk_3d_two_phase_v1': ('effective_bulk_modulus',
                             'interval',
                             'theoretical_bound',
                             'scalar_modulus_bound',
                             'pressure',
                             'Pa',
                             'composite_evaluate'),
 'reuss_bulk_v1': ('effective_bulk_modulus',
                   'lower',
                   'theoretical_bound',
                   'scalar_modulus_bound',
                   'pressure',
                   'Pa',
                   'composite_evaluate'),
 'voigt_bulk_v1': ('effective_bulk_modulus',
                   'upper',
                   'theoretical_bound',
                   'scalar_modulus_bound',
                   'pressure',
                   'Pa',
                   'composite_evaluate'),
 'hs_shear_3d_two_phase_v1': ('effective_shear_modulus',
                              'interval',
                              'theoretical_bound',
                              'scalar_modulus_bound',
                              'pressure',
                              'Pa',
                              'composite_evaluate'),
 'reuss_shear_v1': ('effective_shear_modulus',
                    'lower',
                    'theoretical_bound',
                    'scalar_modulus_bound',
                    'pressure',
                    'Pa',
                    'composite_evaluate'),
 'voigt_shear_v1': ('effective_shear_modulus',
                    'upper',
                    'theoretical_bound',
                    'scalar_modulus_bound',
                    'pressure',
                    'Pa',
                    'composite_evaluate'),
 'isotropic_youngs_modulus_outer_v1': ('effective_youngs_modulus',
                                       'interval',
                                       'derived_outer_envelope',
                                       'derived_outer_envelope',
                                       'pressure',
                                       'Pa',
                                       'composite_evaluate'),
 'isotropic_poissons_ratio_outer_v1': ('effective_poissons_ratio',
                                       'interval',
                                       'derived_outer_envelope',
                                       'derived_outer_envelope',
                                       'dimensionless',
                                       '1',
                                       'composite_evaluate'),
 'griffith_central_crack_plane_stress_model_v1': ('critical_remote_tensile_stress',
                                                  'prediction',
                                                  'model_estimate',
                                                  None,
                                                  'pressure',
                                                  'Pa',
                                                  'catalog_only'),
 'griffith_central_crack_plane_strain_model_v1': ('critical_remote_tensile_stress',
                                                  'prediction',
                                                  'model_estimate',
                                                  None,
                                                  'pressure',
                                                  'Pa',
                                                  'catalog_only'),
 'frenkel_slip_specific_ideal_shear_v1': ('ideal_resolved_shear_stress',
                                          'prediction',
                                          'model_estimate',
                                          None,
                                          'pressure',
                                          'Pa',
                                          'catalog_only'),
 'uber_normal_cohesive_strength_v1': ('ideal_normal_cohesive_stress',
                                      'prediction',
                                      'model_estimate',
                                      None,
                                      'pressure',
                                      'Pa',
                                      'catalog_only'),
 'lefm_central_crack_mode_i_stress_intensity_v1': ('mode_i_stress_intensity_factor',
                                                   'relation',
                                                   'model_relation',
                                                   None,
                                                   'stress_intensity',
                                                   'Pa*m^0.5',
                                                   'catalog_only'),
 'lefm_mode_i_energy_release_relation_v1': ('mode_i_energy_release_rate',
                                            'relation',
                                            'model_relation',
                                            None,
                                            'energy_per_area',
                                            'J/m^2',
                                            'catalog_only'),
 'lefm_center_crack_finite_width_secant_factor_v1': ('finite_width_geometry_factor',
                                                     'relation',
                                                     'model_relation',
                                                     None,
                                                     'dimensionless',
                                                     '1',
                                                     'catalog_only'),
 'general_stiffness_positive_definite_v1': ('homogeneous_elastic_stability',
                                            'constraint',
                                            'stability_criterion',
                                            None,
                                            'logical_predicate',
                                            None,
                                            'catalog_only'),
 'cubic_born_stability_v1': ('homogeneous_elastic_stability',
                             'constraint',
                             'stability_criterion',
                             None,
                             'logical_predicate',
                             None,
                             'catalog_only'),
 'hexagonal_born_stability_v1': ('homogeneous_elastic_stability',
                                 'constraint',
                                 'stability_criterion',
                                 None,
                                 'logical_predicate',
                                 None,
                                 'catalog_only'),
 'orthorhombic_born_stability_v1': ('homogeneous_elastic_stability',
                                    'constraint',
                                    'stability_criterion',
                                    None,
                                    'logical_predicate',
                                    None,
                                    'catalog_only'),
 'hs_porous_bulk_3d_solid_void_v1': ('effective_bulk_modulus',
                                     'interval',
                                     'theoretical_bound',
                                     'scalar_modulus_bound',
                                     'pressure',
                                     'Pa',
                                     'catalog_only'),
 'hs_porous_shear_3d_solid_void_v1': ('effective_shear_modulus',
                                      'interval',
                                      'theoretical_bound',
                                      'scalar_modulus_bound',
                                      'pressure',
                                      'Pa',
                                      'catalog_only'),
 'hs_porous_youngs_outer_3d_solid_void_v1': ('effective_youngs_modulus',
                                             'interval',
                                             'derived_outer_envelope',
                                             'derived_outer_envelope',
                                             'pressure',
                                             'Pa',
                                             'catalog_only'),
 'tetragonal_i_born_stability_v1': ('homogeneous_elastic_stability',
                                    'constraint',
                                    'stability_criterion',
                                    None,
                                    'logical_predicate',
                                    None,
                                    'catalog_only'),
 'tetragonal_ii_born_stability_v1': ('homogeneous_elastic_stability',
                                     'constraint',
                                     'stability_criterion',
                                     None,
                                     'logical_predicate',
                                     None,
                                     'catalog_only'),
 'rhombohedral_i_born_stability_v1': ('homogeneous_elastic_stability',
                                      'constraint',
                                      'stability_criterion',
                                      None,
                                      'logical_predicate',
                                      None,
                                      'catalog_only'),
 'rhombohedral_ii_born_stability_v1': ('homogeneous_elastic_stability',
                                       'constraint',
                                       'stability_criterion',
                                       None,
                                       'logical_predicate',
                                       None,
                                       'catalog_only')}


# v0.9.0 reviewed fatigue contracts: catalog-only; see docs/FATIGUE_GROWTH.md.
SUPPORTED_FAMILY_ASSUMPTIONS.update({'paris_erdogan_intermediate_growth_v1': {'material_scope': 'calibrated_material_temper_orientation_and_thickness',
                                          'crack_mode': 'mode_I',
                                          'crack_scale': 'long_crack_with_continuum_LEFM_description',
                                          'constitutive_regime': 'predominantly_linear_elastic_small_scale_yielding',
                                          'loading': 'constant_amplitude_cyclic_loading',
                                          'stress_intensity_convention': 'modern_K_I_sigma_yy_ahead_of_tip=K_I/sqrt(2*pi*r)',
                                          'geometry': 'explicit_geometry_valid_K_solution_and_crack_coordinate',
                                          'crack_coordinate': 'a_is_tip_advance_coordinate_half_length_for_symmetric_center_crack',
                                          'cycle_count': 'N_counts_complete_load_cycles_not_reversals_or_time',
                                          'range_definition': 'DeltaK=Kmax-Kmin=(1-R)*Kmax',
                                          'stress_ratio_definition': 'R=Kmin/Kmax',
                                          'stress_ratio_scope': '0<=R<1',
                                          'positive_Kmax_and_DeltaK': True,
                                          'calibration_conditions': 'matched_temperature_environment_frequency_waveform_and_loading_history',
                                          'coefficient_convention': 'equation_exponent_units_and_K_normalization_specific',
                                          'fit_parameters': 'supplied_positive_coefficient_and_positive_dimensionless_exponent',
                                          'threshold_model': 'none',
                                          'closure_and_residual_stress': 'no_unmodelled_closure_shielding_or_residual_stress_transfer',
                                          'growth_regime': 'calibrated_intermediate_region_II_away_from_threshold_and_instability',
                                          'stress_ratio_calibration': 'fixed_calibrated_R'},
 'forman_terminal_acceleration_growth_v1': {'material_scope': 'calibrated_material_temper_orientation_and_thickness',
                                            'crack_mode': 'mode_I',
                                            'crack_scale': 'long_crack_with_continuum_LEFM_description',
                                            'constitutive_regime': 'predominantly_linear_elastic_small_scale_yielding',
                                            'loading': 'constant_amplitude_cyclic_loading',
                                            'stress_intensity_convention': 'modern_K_I_sigma_yy_ahead_of_tip=K_I/sqrt(2*pi*r)',
                                            'geometry': 'explicit_geometry_valid_K_solution_and_crack_coordinate',
                                            'crack_coordinate': 'a_is_tip_advance_coordinate_half_length_for_symmetric_center_crack',
                                            'cycle_count': 'N_counts_complete_load_cycles_not_reversals_or_time',
                                            'range_definition': 'DeltaK=Kmax-Kmin=(1-R)*Kmax',
                                            'stress_ratio_definition': 'R=Kmin/Kmax',
                                            'stress_ratio_scope': '0<=R<1',
                                            'positive_Kmax_and_DeltaK': True,
                                            'calibration_conditions': 'matched_temperature_environment_frequency_waveform_and_loading_history',
                                            'coefficient_convention': 'equation_exponent_units_and_K_normalization_specific',
                                            'fit_parameters': 'supplied_positive_coefficient_and_positive_dimensionless_exponent',
                                            'threshold_model': 'none',
                                            'closure_and_residual_stress': 'no_unmodelled_closure_shielding_or_residual_stress_transfer',
                                            'growth_regime': 'calibrated_central_and_high_growth_before_instability',
                                            'stress_ratio_calibration': 'R_within_explicit_calibrated_range',
                                            'fracture_toughness': 'positive_condition_and_thickness_matched_Kc_not_automatically_KIc',
                                            'positive_denominator': '(1-R)*Kc-DeltaK>0_equivalently_Kmax<Kc',
                                            'instability_pole': 'excluded_not_a_finite_rate_prediction'}})
SUPPORTED_FAMILY_IDENTITIES.update({'paris_erdogan_intermediate_growth_v1': ('fatigue_crack_growth_rate',
                                          'prediction',
                                          'model_estimate',
                                          None,
                                          'length_per_cycle',
                                          'm/cycle',
                                          'catalog_only'),
 'forman_terminal_acceleration_growth_v1': ('fatigue_crack_growth_rate',
                                            'prediction',
                                            'model_estimate',
                                            None,
                                            'length_per_cycle',
                                            'm/cycle',
                                            'catalog_only')})

SUPPORTED_FAMILY_ASSUMPTIONS.update({'zener_cubic_elastic_anisotropy_index_v1': {'spatial_dimension': 3,
                                             'constitutive_law': 'linear_elastic',
                                             'strain_regime': 'infinitesimal',
                                             'reference_state': 'stress_free_equilibrium',
                                             'elastic_tensor': 'finite_real_with_minor_and_major_symmetries',
                                             'stability': 'strictly_positive_definite_on_symmetric_strains',
                                             'stiffness_units': 'common_pressure_unit',
                                             'stiffness_convention': 'engineering_voigt_order_11_22_33_23_13_12',
                                             'strain_vector': 'epsilon_11_epsilon_22_epsilon_33_2epsilon_23_2epsilon_13_2epsilon_12',
                                             'stress_vector': 'sigma_11_sigma_22_sigma_33_sigma_23_sigma_13_sigma_12',
                                             'shear_conversion': 'convert_Kelvin_or_Mandel_to_engineering_Voigt_before_component_use',
                                             'elastic_symmetry': 'cubic',
                                             'axes': 'natural_cubic_crystallographic_100_axes',
                                             'strict_cubic_conditions': 'C11-C12>0_and_C11+2*C12>0_and_C44>0'},
 'universal_elastic_anisotropy_index_v1': {'spatial_dimension': 3,
                                           'constitutive_law': 'linear_elastic',
                                           'strain_regime': 'infinitesimal',
                                           'reference_state': 'stress_free_equilibrium',
                                           'elastic_tensor': 'finite_real_with_minor_and_major_symmetries',
                                           'stability': 'strictly_positive_definite_on_symmetric_strains',
                                           'stiffness_units': 'common_pressure_unit',
                                           'stiffness_convention': 'engineering_voigt_order_11_22_33_23_13_12',
                                           'strain_vector': 'epsilon_11_epsilon_22_epsilon_33_2epsilon_23_2epsilon_13_2epsilon_12',
                                           'stress_vector': 'sigma_11_sigma_22_sigma_33_sigma_23_sigma_13_sigma_12',
                                           'shear_conversion': 'convert_Kelvin_or_Mandel_to_engineering_Voigt_before_component_use',
                                           'elastic_symmetry': 'any_3d_elastic_symmetry',
                                           'axes': 'orthonormal_cartesian',
                                           'compliance': 'full_tensor_inverse_equivalently_full_6_by_6_engineering_matrix_inverse',
                                           'orientation_average': 'uniform_normalized_SO3_full_orientation_average',
                                           'averaging_order': 'average_C_and_its_full_inverse_S_separately',
                                           'isotropic_projections': 'CV=3*KV*J+2*GV*D_and_SR=J/(3*KR)+D/(2*GR)',
                                           'positive_projection_moduli': True}})
SUPPORTED_FAMILY_IDENTITIES.update({'zener_cubic_elastic_anisotropy_index_v1': ('zener_elastic_anisotropy_index',
                                             'relation',
                                             'model_relation',
                                             None,
                                             'dimensionless',
                                             '1',
                                             'catalog_only'),
 'universal_elastic_anisotropy_index_v1': ('universal_elastic_anisotropy_index',
                                           'relation',
                                           'model_relation',
                                           None,
                                           'dimensionless',
                                           '1',
                                           'catalog_only')})

SUPPORTED_FAMILY_ASSUMPTIONS.update({rule: contract['required_assumptions']
                                    for rule, contract in DIRECTIONAL_CONTRACTS.items()})
SUPPORTED_FAMILY_IDENTITIES.update({rule: tuple(contract[field] for field in FAMILY_IDENTITY_FIELDS)
                                   for rule, contract in DIRECTIONAL_CONTRACTS.items()})

SUPPORTED_FAMILY_ASSUMPTIONS.update({rule: contract['required_assumptions']
                                    for rule, contract in COMPRESSIBILITY_CONTRACTS.items()})
SUPPORTED_FAMILY_IDENTITIES.update({rule: tuple(contract[field] for field in FAMILY_IDENTITY_FIELDS)
                                   for rule, contract in COMPRESSIBILITY_CONTRACTS.items()})


SUPPORTED_FAMILY_ASSUMPTIONS.update({rule: contract['required_assumptions']
                                    for rule, contract in WAVE_CONTRACTS.items()})
SUPPORTED_FAMILY_IDENTITIES.update({rule: tuple(contract[field] for field in FAMILY_IDENTITY_FIELDS)
                                   for rule, contract in WAVE_CONTRACTS.items()})

class CatalogValidationError(ValueError):
    """The supplied catalogs violate the supported local contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CatalogValidationError(message)


# Cache only successful meta-validation of schema contents. Candidate data,
# strict loads, format checkers, registries and instance validators stay fresh.
# Restrict reuse to the original, inspectable jsonschema configuration; custom
# callables/configurations run normally on every call rather than being guessed
# equivalent. The entry and key-size limits bound retained process-local memory.
_SCHEMA_META_CACHE_LIMIT = 32
_SCHEMA_META_CACHE_KEY_LIMIT = 1_000_000
_SCHEMA_META_SUCCESSES = OrderedDict()
_SCHEMA_META_CACHE_LOCK = Lock()


def _canonical_schema(schema):
    # json.dumps also accepts tuples and custom subclasses. Such patched loader
    # output is not strict JSON and must not alias a cached ordinary JSON tree.
    def plain_json(value):
        if type(value) is dict:
            return all(type(key) is str and plain_json(item) for key, item in value.items())
        if type(value) is list:
            return all(plain_json(item) for item in value)
        return type(value) in (str, int, float, bool, type(None))
    if not plain_json(schema):
        raise TypeError("non-JSON schema configuration")
    return json.dumps(schema, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _meta_function_state(function):
    if (type(function) is not FunctionType or function.__closure__ or function.__dict__ or
            not function.__module__.startswith("jsonschema.")):
        raise TypeError("custom meta-validation callable")
    # The default check_schema sentinel is immutable but not JSON data.
    defaults = tuple("<jsonschema unset>" if value is _schema_validators._UNSET else
                     _canonical_schema(value) for value in function.__defaults__ or ())
    return (function, function.__code__, defaults, _canonical_schema(function.__kwdefaults__))


def _meta_check_configuration():
    """Snapshot inspectable meta-check settings, or decline cache reuse."""
    try:
        cls = Draft202012Validator
        checker = cls.FORMAT_CHECKER
        if type(checker) is not _META_FORMAT_CHECKER_TYPE or set(vars(checker)) != {"checkers"}:
            return None
        methods = tuple((name, method, method.__code__,
                         _canonical_schema(list(method.__defaults__ or ())),
                         _canonical_schema(method.__kwdefaults__) if name != "__init__" else None)
                        for name, method in vars(cls).items() if type(method) is FunctionType)
        formats = tuple((name, _meta_function_state(function), raises)
                        for name, (function, raises) in sorted(checker.checkers.items()))
        keywords = tuple((name, _meta_function_state(function))
                         for name, function in sorted(cls.VALIDATORS.items()))
        types = tuple((name, _meta_function_state(function))
                      for name, function in sorted(cls.TYPE_CHECKER._type_checkers.items()))
        # check_schema chooses its validator through this mutable registration
        # table. A changed meta-schema or registration must never hit old success.
        registrations = tuple(sorted(_schema_validators._META_SCHEMAS.items()))
        # Default meta-reference resources are separate from each call's fresh,
        # explicitly offline runtime registry. Include their actual contents too.
        defaults = cls.__init__.__kwdefaults__
        registries = tuple((registry, tuple(sorted(
            (uri, _canonical_schema(resource.contents)) for uri, resource in registry.items())))
            for registry in (defaults["registry"], _schema_validators.SPECIFICATIONS))
        return (cls, _meta_function_state(cls.check_schema.__func__),
                _meta_function_state(_schema_validators.validator_for), registrations,
                _canonical_schema(cls.META_SCHEMA), methods, keywords,
                type(cls.TYPE_CHECKER), types, getattr(cls, "_APPLICABLE_VALIDATORS", None),
                _meta_function_state(type(cls.TYPE_CHECKER).is_type),
                _meta_function_state(type(checker).check), formats,
                cls.__init__.__defaults__, defaults.get("_resolver"), registries)
    except (AttributeError, TypeError, ValueError, KeyError, RuntimeError):
        # Optional dependency implementations may differ. Correct uncached
        # validation is preferable to an unsafe or brittle cache fingerprint.
        return None


_META_FORMAT_CHECKER_TYPE = FormatChecker
_META_CHECK_CONFIGURATION = _meta_check_configuration()


def _check_schema(schema):
    configuration = _meta_check_configuration()
    cacheable = configuration is not None and configuration == _META_CHECK_CONFIGURATION
    try:
        key = _canonical_schema(schema) if cacheable else None
    except (TypeError, ValueError):
        key = None
    if key is not None and len(key) > _SCHEMA_META_CACHE_KEY_LIMIT:
        key = None
    if key is not None:
        with _SCHEMA_META_CACHE_LOCK:
            if key in _SCHEMA_META_SUCCESSES:
                _SCHEMA_META_SUCCESSES.move_to_end(key)
                return
    Draft202012Validator.check_schema(schema)
    # Never remember failures or successes obtained under changed settings.
    if key is not None and _meta_check_configuration() == configuration:
        with _SCHEMA_META_CACHE_LOCK:
            _SCHEMA_META_SUCCESSES[key] = None
            _SCHEMA_META_SUCCESSES.move_to_end(key)
            while len(_SCHEMA_META_SUCCESSES) > _SCHEMA_META_CACHE_LIMIT:
                _SCHEMA_META_SUCCESSES.popitem(last=False)


def _no_remote_reference(uri: str):
    raise NoSuchResource(ref=uri)


def _formats(schema):
    if isinstance(schema, dict):
        if "format" in schema:
            yield schema["format"]
        for value in schema.values():
            yield from _formats(value)
    elif isinstance(schema, list):
        for value in schema:
            yield from _formats(value)


def _index(records: list[dict], kind: str) -> dict:
    result = {record["id"]: record for record in records}
    require(len(result) == len(records), f"{kind}: duplicate record ID")
    return result


def _validate_labels(locales: dict, names: set[str], *, index_present: bool = False,
                     directional_present: bool = False, compressibility_present: bool = False, mos2_present: bool = False, hbn_present: bool = False, wave_present: bool = False) -> None:
    require(isinstance(locales, dict), "locales: expected an object")
    require(set(locales) == {"schema_version", "default_language", "translation_review", "languages"},
            "locales: unsupported or missing envelope fields")
    require(locales["schema_version"] == "1.0.0", "locales: unsupported schema version")
    require(locales["default_language"] == "en", "locales: default language must be en")
    require(locales["translation_review"] == "machine_assisted_not_scientifically_reviewed",
            "locales: translation review status cannot be upgraded by validation")
    languages = locales["languages"]
    require(isinstance(languages, dict) and set(languages) == LANGUAGES,
            "locales: exactly en, zh, ja and de are required")
    require(all(isinstance(messages, dict) for messages in languages.values()),
            "locales: each language must be a dictionary")
    keys = set(languages["en"])
    if mos2_present:
        from materials_boundaries._observation_contract import MOS2_LABELS
        require(MOS2_LABELS <= keys, "locales: missing required MoS2 warning/display labels: " +
                ", ".join(sorted(MOS2_LABELS - keys)))
    if hbn_present:
        from materials_boundaries._hbn_observation_contract import HBN_LABELS
        require(HBN_LABELS <= keys, "locales: missing required hBN warning/display labels: " +
                ", ".join(sorted(HBN_LABELS - keys)))
    if wave_present:
        required_wave_keys = {"catalog_wave_" + key for key in
            ("notice", "conditions", "normalization", "polarization", "energy", "range", "limits")}
        required_wave_keys |= {"catalog_status_" + key for key in
            ("mass_density", "speed", "speed_squared", "isotropic_bulk_phase_speed_ratio", "bulk_phase_speed_squared")}
        require(required_wave_keys <= keys, "locales: missing required bulk wave display labels")
    if compressibility_present:
        required_compressibility_keys = {"catalog_compressibility_" + key for key in
            ("notice", "conditions", "limits", "fixed_tensor", "range", "energy", "symmetry")}
        required_compressibility_keys |= {"catalog_status_inverse_pressure",
            "catalog_status_directional_linear_compressibility",
            "catalog_status_normalized_directional_linear_compressibility"}
        require(required_compressibility_keys <= keys,
                "locales: missing required compressibility display labels: " +
                ", ".join(sorted(required_compressibility_keys - keys)))
    if directional_present:
        required_directional_keys = {"catalog_directional_notice", "catalog_directional_conditions",
                                     "catalog_directional_limits", "catalog_directional_range",
                                     "catalog_directional_fixed_tensor", "catalog_directional_pair",
                                     "catalog_status_directional_poissons_ratio"}
        require(required_directional_keys <= keys,
                "locales: missing required directional display labels: " +
                ", ".join(sorted(required_directional_keys - keys)))
    if index_present:
        required_index_keys = {"catalog_index_range", "catalog_index_isotropy",
                               "catalog_index_upper_unbounded", "catalog_index_notice"}
        require(required_index_keys <= keys,
                "locales: missing required anisotropy display labels: " +
                ", ".join(sorted(required_index_keys - keys)))
    required_names = {"catalog_name_" + name for name in names - LEGACY_CANONICAL_NAMES}
    require(required_names <= keys, "locales: missing authored catalog name labels: " + ", ".join(sorted(required_names - keys)))
    unknown_names = {key.removeprefix("catalog_name_") for key in keys if key.startswith("catalog_name_")} - names
    require(not unknown_names, "locales: labels reference unknown records: " + ", ".join(sorted(unknown_names)))
    formatter = string.Formatter()
    placeholders = {}
    for language in ("en", "zh", "ja", "de"):
        messages = languages[language]
        require(set(messages) == keys, f"locales.{language}: language key parity failed")
        for key, value in messages.items():
            require(isinstance(value, str) and bool(value.strip()) and "[missing:" not in value,
                    f"locales.{language}.{key}: expected a nonempty authored label")
            try:
                fields = {field for _, field, _, _ in formatter.parse(value) if field is not None}
            except ValueError as exc:
                raise CatalogValidationError(f"locales.{language}.{key}: invalid format string") from exc
            if language == "en":
                placeholders[key] = fields
            require(fields == placeholders[key], f"locales.{language}.{key}: placeholder parity failed")


def validate_catalogs(catalogs: dict, schema_dir: Path = ROOT / "schemas") -> dict[str, int]:
    """Check local structural/integrity contracts without mutating the input.

    Schema branches define supported scientific families. No generic fallback is
    supplied: a new geometry, symmetry, quantity or inference method needs its
    own reviewed schema work, outside a catalog-only contribution.
    """
    require(isinstance(catalogs, dict) and set(catalogs) == {*CATALOGS, *LOCALE_CATALOGS},
            "expected all scientific catalogs and the three locale dictionaries")
    schemas = {name: load_json(schema_dir / f"{name}.schema.json") for name in CATALOGS}
    checker = FormatChecker()
    formats = {name for schema in schemas.values() for name in _formats(schema)}
    missing = formats - checker.checkers.keys()
    require(not missing, "required format checkers unavailable: " + ", ".join(sorted(missing)) +
            "; install the complete development extra: python -m pip install -e '.[dev]'")
    registry = Registry(retrieve=_no_remote_reference).with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values())
    indexes = {}
    for kind in CATALOGS:
        schema = schemas[kind]
        _check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=checker, registry=registry)
        errors = list(validator.iter_errors(catalogs[kind]))
        if errors:
            error = errors[0]
            path = ".".join(map(str, error.absolute_path)) or "$"
            raise CatalogValidationError(f"{kind}.{path}: {error.message}")
        indexes[kind] = _index(catalogs[kind]["records"], kind)
    # IDs form one catalog namespace, so locale aliases and references cannot
    # silently point at another record kind.
    all_ids = [name for index in indexes.values() for name in index]
    require(len(all_ids) == len(set(all_ids)), "duplicate record ID across catalog kinds")
    claims, sources, observations = (indexes[name] for name in ("claims", "sources", "observations"))
    try:
        validate_wave_records(list(claims.values()))
        validate_directional_records(list(claims.values()), resolve_dependencies=True)
        validate_compressibility_records(list(claims.values()), resolve_dependencies=True)
    except ValueError as exc:
        raise CatalogValidationError(str(exc)) from exc
    for name, claim in claims.items():
        rule = claim["rule_id"]
        require(rule in SUPPORTED_FAMILY_ASSUMPTIONS, f"claims.{name}: unsupported scientific family {rule}")
        require(tuple(claim[field] for field in FAMILY_IDENTITY_FIELDS) == SUPPORTED_FAMILY_IDENTITIES[rule],
                f"claims.{name}: structural identity differs from supported family {rule}")
        expected = SUPPORTED_FAMILY_ASSUMPTIONS[rule]
        actual = claim["required_assumptions"]
        require(set(actual) == set(expected) and all(
            type(actual[key]) is type(value) and actual[key] == value for key, value in expected.items()),
            f"claims.{name}: required assumptions differ from the complete supported family {rule}")
    for kind in ("claims", "observations"):
        for name, record in indexes[kind].items():
            for evidence in record["evidence"]:
                require(evidence["source_id"] in sources,
                        f"{kind}.{name}: unresolved evidence source {evidence['source_id']}")
    from materials_boundaries._observation_contract import validate_observation_records
    try:
        validate_observation_records(list(observations.values()))
    except ValueError as exc:
        raise CatalogValidationError(str(exc)) from exc
    for name, observation in observations.items():
        study = observation["study_id"]
        require(study in sources, f"observations.{name}: unresolved study source {study}")
        require(study in {e["source_id"] for e in observation["evidence"]},
                f"observations.{name}: study source must be included in evidence")
    for name, claim in claims.items():
        for dependency in claim["dependencies"]:
            require(dependency in claims, f"claims.{name}: unresolved dependency {dependency}")
    # Iterative topological removal avoids accepting cycles or depending on the
    # recursion limit as the knowledge catalog grows.
    pending = {name: set(claim["dependencies"]) for name, claim in claims.items()}
    while pending:
        ready = {name for name, dependencies in pending.items() if not dependencies}
        require(bool(ready), "claims: cyclic dependencies among " + ", ".join(sorted(pending)))
        pending = {name: dependencies - ready for name, dependencies in pending.items() if name not in ready}
    runtime_pairs = [(row[0], row[1]) for row in (*BASE_RULES, *DERIVED_RULES)]
    require(len(runtime_pairs) == 8 and set(runtime_pairs) == EXPECTED_EXECUTABLE_PAIRS,
            "runtime registry differs from the exact eight approved claim/rule pairs")
    executable_pairs = {(name, record["rule_id"]) for name, record in claims.items()
                        if record["evaluation_support"] == "composite_evaluate"}
    require(executable_pairs == EXPECTED_EXECUTABLE_PAIRS,
            "claims: executable claim/rule pairs differ from the exact eight supported pairs")
    from materials_boundaries.temperature import validate_model_catalog
    try:
        validate_model_catalog(catalogs["temperature_models"])
    except ValidationError as exc:
        raise CatalogValidationError(str(exc)) from exc
    for model in catalogs["temperature_models"]["records"]:
        require(all(sid in sources for sid in model["source_ids"]),
                f"temperature_models.{model['id']}: unresolved source ID")
    from materials_boundaries.temperature_presentation import validate_temperature_locales
    try:
        validate_temperature_locales(catalogs['temperature_locales'], catalogs['temperature_models'], catalogs['sources'])
    except ValidationError as exc:
        raise CatalogValidationError(str(exc)) from exc
    from materials_boundaries.predictions import validate_prediction_catalog, REQUIRED_LABELS as PREDICTION_LABELS
    try:
        validate_prediction_catalog(catalogs["computational_predictions"], catalogs["sources"])
    except ValidationError as exc:
        raise CatalogValidationError(str(exc)) from exc
    metadata_ids = [r["id"] for field in ("protocols", "comparison_groups")
                    for r in catalogs["computational_predictions"][field]]
    require(not set(metadata_ids) & set(all_ids), "prediction metadata IDs collide with catalog records")
    prediction_locales = catalogs["prediction_locales"]
    require(isinstance(prediction_locales, dict) and set(prediction_locales) == {"schema_version", "translation_review", "languages"}, "prediction locales: invalid envelope")
    require(prediction_locales["schema_version"] == "1.0.0" and prediction_locales["translation_review"] == "machine_assisted_not_scientifically_reviewed", "prediction locales: invalid schema/review status")
    languages = prediction_locales["languages"]
    require(isinstance(languages, dict) and set(languages) == LANGUAGES, "prediction locales: four languages required")
    for language, messages in languages.items():
        require(isinstance(messages, dict) and set(messages) == set(languages["en"]) and PREDICTION_LABELS <= set(messages) and
                all(isinstance(value, str) and bool(value.strip()) and "[missing:" not in value for value in messages.values()),
                f"prediction locales.{language}: invalid labels or key parity")
    _validate_labels(catalogs["locales"], set(claims) | set(observations),
                     index_present=any("index_range" in claim for claim in claims.values()),
                     directional_present=any("directional_contract" in claim for claim in claims.values()),
                     compressibility_present=any("hydrostatic_compressibility_contract" in claim for claim in claims.values()),
                     mos2_present=any(record.get("method_family") == "bertolazzi_2011_mos2_monolayer_indentation_v1" for record in observations.values()),
                     hbn_present=any(record.get("method_family") == "falin_2017_hbn_monolayer_indentation_v1" for record in observations.values()),
                     wave_present=any("bulk_wave_contract" in claim for claim in claims.values()))
    return {kind: len(index) for kind, index in indexes.items()}


def load_catalogs(data_dir: Path) -> dict:
    """Strict loading rejects duplicate keys, nonfinite and out-of-range numbers."""
    return {name: load_json(data_dir / f"{name}.json") for name in (*CATALOGS, *LOCALE_CATALOGS)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "materials_boundaries" / "data",
                        help="candidate catalog directory; schemas always come from this checkout")
    args = parser.parse_args(argv)
    try:
        counts = validate_catalogs(load_catalogs(args.data_dir))
    except (CatalogValidationError, ValidationError, OSError, ValueError) as exc:
        print(f"Catalog validation failed: {exc}", file=sys.stderr)
        return 1
    print("PASS: " + ", ".join(f"{count} {kind}" for kind, count in counts.items()) + "; exactly 8 composite executable pairs; separate synthetic/empirical temperature contracts and discrete computational predictions; 4 languages")
    print("Structural and integrity checks only; scientific review, specimen applicability and reuse rights are not certified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
