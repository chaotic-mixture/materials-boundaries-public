"""Closed contract for the Dubois silicon first-instability prediction family.

These constants define supported semantics independently of mutable catalog data.
No scientific computation or automatic cross-family comparison is performed.
"""
SILICON_FAMILY = 'dubois_2006_si_uniaxial_deformation_v1'

SILICON_GROUP = 'dubois_2006_si_directional_instability'

SILICON_QUANTITY = 'tensile_first_instability_strength'

SILICON_PROTOCOL_CONTRACT = {'family': 'dubois_2006_si_uniaxial_deformation_v1',
 'version': '1.0.0',
 'source_sections': ['II', 'III.A', 'III.B', 'III.C'],
 'property': 'tensile_first_instability_strength',
 'property_interpretation': 'Reported tensile stress at the first detected structural instability '
                            'under fixed transverse strain',
 'evidence_type': 'published_computational_prediction',
 'material_representation': 'periodic_atomic_primitive_cell_model',
 'commercial_alloy_grade': False,
 'structure': {'composition': 'Si',
               'cell_type_reported': 'primitive',
               'atoms_per_cell': 2,
               'lattice_constant_reported_bohr': 10.201,
               'source_for_lattice_constant': 'Table I, page 235203-2',
               'crystal_structure_reported': None,
               'crystal_structure_normalized': 'diamond_cubic',
               'crystal_structure_normalization_status': 'Inferred standard bulk silicon structure '
                                                         'from the reported two-atom primitive '
                                                         'cell and cubic directions; diamond-cubic '
                                                         'is not explicitly named in the inspected '
                                                         'source text. Preserve this inference '
                                                         'label or keep the normalized field null '
                                                         'if explicit-only ingestion is required.',
               'space_group_number': None,
               'defect_model': 'perfect_periodic_crystal'},
 'geometry': {'comparison_variable': 'loading_direction_family',
              'notation': 'crystallographically_equivalent_direction_family_not_a_specific_signed_vector',
              'supported_direction_family_indices': [[1, 0, 0], [1, 1, 0], [1, 1, 1]]},
 'loading': {'source_name': 'uniaxial deformation',
             'source_alias': 'unrelaxed tension',
             'imposed_strain_equation_as_printed': 'epsilon_tension = epsilon_11 (e_1 tensor e_1)',
             'equation_number': 1,
             'strain_measure_for_tabulated_critical_strain': 'engineering',
             'e_1': 'unit vector in loading direction',
             'fixed_during_relaxation': 'lattice vectors at each imposed strain',
             'relaxed': 'relative atomic positions only',
             'transverse_strain_constraint': 'zero imposed transverse strain components',
             'transverse_stress': 'not relaxed to zero',
             'exact_strain_schedule': None,
             'stress_measure': 'DFT stress as reported; no explicit Cauchy/nominal classification '
                               'verified'},
 'calculation': {'method': 'DFT_and_density_functional_perturbation_theory',
                 'software': 'ABINIT',
                 'exchange_correlation': 'LDA_Teter_Pade',
                 'pseudopotential': 'separable_norm_conserving_Troullier_Martins',
                 'plane_wave_cutoff': {'value': 10, 'unit': 'hartree'},
                 'kpoint_mesh': [12, 12, 12],
                 'kpoint_scheme': 'Monkhorst_Pack',
                 'smearing': {'scheme': 'cold_smearing',
                              'value': 0.01,
                              'unit': 'hartree',
                              'physical_temperature': False},
                 'phonon_qpoint_mesh': [6, 6, 6],
                 'phonon_check': 'Interpolated dynamical matrices; suspect high-symmetry phonon '
                                 'modes recalculated explicitly',
                 'calculation_regime': 'static_constrained_geometry_DFT_inferred_from_method_not_a_reported_temperature'},
 'numerical_controls': {'author_numerical_stress_error_estimate_GPa': {'qualifier': 'less_than_approximately',
                                                                       'value': 0.05,
                                                                       'scope': 'smearing_finite_basis_kpoint_sampling',
                                                                       'is_statistical_or_total_uncertainty': False},
                        'relaxed_loading_residual_stress_threshold_GPa': {'value': 0.02,
                                                                          'applies_to_this_fixed_lattice_batch': False},
                        'statistical_uncertainty_GPa': None,
                        'total_model_uncertainty_GPa': None},
 'state_fields': {'physical_temperature_K': None,
                  'pressure_GPa': None,
                  'magnetic_state': None,
                  'spin_polarization': None,
                  'temperature_note': 'Table I contains experimental room-temperature/77 K '
                                      'references, not temperatures for the selected DFT '
                                      'calculations. Do not infer 0 K from static geometry '
                                      'optimization or smearing.',
                  'pressure_note': 'Anisotropic transverse stresses are allowed by this loading '
                                   'protocol; do not assign exact zero hydrostatic pressure.',
                  'magnetic_note': 'Not verified in inspected paper; do not infer a spin setup.'},
 'strength_criterion': {'reported': 'first structural instability detected using phonon spectra '
                                    'and stiffness tensor',
                        'selected_rows_first_mode': 'elastic_tensile_mode_along_the_imposed_direction',
                        'complete_stability_analysis': 'reported by authors; not independently '
                                                       'reproduced',
                        'stress_path_peak': 'qualitatively consistent with Figure 2(b), no '
                                            'graph-derived numbers'}}

SILICON_RECORD_CONTRACT = {'version': '1.0.0',
 'quantity': 'tensile_first_instability_strength',
 'evaluation_support': 'reported_discrete_prediction',
 'evidence_type': 'published_computational_prediction',
 'material_representation': 'periodic_atomic_primitive_cell_model',
 'commercial_alloy_grade': False,
 'uncertainty_GPa': None,
 'universal_upper_bound': False,
 'unit': 'GPa',
 'formula': 'Si',
 'cell_composition': 'Si2',
 'stoichiometry_in_model_cell': {'Si': 2},
 'cell_composition_status': 'explicit_two_atom_silicon_primitive_cell',
 'reported_strength_definition': 'computed_stress_at_first_detected_instability',
 'verification': {'status': 'source_table_visually_checked',
                  'independent_scientific_review': False,
                  'raw_inputs_audited': False}}

SILICON_GROUP_CONTRACT = {'verification_level': 'reported_method_only',
 'unknown_conditions_equivalent': False,
 'raw_inputs_audited': False,
 'cross_study_comparison_allowed': False,
 'comparison_axis': 'loading_direction_family',
 'excluded_interpretations': ['experimental observation',
                              'commercial alloy grade',
                              'ultimate tensile strength',
                              'hardness',
                              'macroscopic yield strength',
                              'universal rigorous strength upper bound',
                              'complete stability envelope over all modes',
                              'fully relaxed uniaxial tension',
                              'ideal shear strength',
                              'generic stress path maximum']}

CRITICAL_STRAIN_CONTRACT = {'quantity': 'critical_engineering_strain_at_first_instability',
 'unit': '1',
 'source_unit': '%',
 'reported_decimal_places': 0,
 'uncertainty': None,
 'definition': 'engineering_strain_at_the_same_reported_first_instability_as_the_strength'}


def validate_silicon_record(record):
    from decimal import Decimal, InvalidOperation
    import re
    from .predictions import (_keys, _names, _text, _finite_positive, _evidence,
                              require, canonical_json, PredictionError)
    require(_names(record['descriptions']), 'four authored silicon descriptions required')
    direction=record['direction']
    _keys(direction, ('family_indices','display','notation'), 'silicon direction')
    supported={canonical_json(v):'⟨'+''.join(map(str,v))+'⟩' for v in ([1,0,0],[1,1,0],[1,1,1])}
    key=canonical_json(direction['family_indices'])
    require(key in supported and direction['display']==supported[key], 'unsupported direction family or notation')
    require(direction['notation']==SILICON_PROTOCOL_CONTRACT['geometry']['notation'], 'direction family cannot be a signed vector')
    require(record['source_table_label']==direction['display']+' uniaxal deformation', 'silicon source row must be uniaxial deformation')
    strain=record['critical_engineering_strain']
    _keys(strain, (*CRITICAL_STRAIN_CONTRACT,'value','source_value_string','precision_note','evidence'), 'critical strain')
    for key,expected in CRITICAL_STRAIN_CONTRACT.items():
        require(canonical_json(strain[key])==canonical_json(expected), 'unsupported critical strain contract: '+key)
    require(_finite_positive(strain['value']), 'finite positive critical engineering strain required')
    string=strain['source_value_string']
    require(isinstance(string,str) and re.fullmatch(r'[1-9][0-9]*',string) is not None, 'original integer percentage string required')
    try:
        require(Decimal(string+'e-2')==Decimal(str(strain['value'])), 'critical strain percent conversion mismatch')
    except InvalidOperation as exc:
        raise PredictionError('invalid critical strain decimal') from exc
    require(_text(strain['precision_note']), 'critical strain precision explanation required')
    _evidence(strain['evidence'],record['source_id'])
    require(sum('reported_critical_engineering_strain' in e['supports'] for e in strain['evidence'])==1, 'one primary critical strain evidence required')
    mode=record['first_instability']
    _keys(mode, ('type','phonon_wavevector_location','mode','source_table','source_pdf_page_1_based','evidence'), 'first instability')
    require(mode['type']=='elastic' and mode['phonon_wavevector_location']=='Brillouin_zone_center' and mode['mode']==direction['display']+' tension', 'silicon first mode must be direction-matched tensile elastic instability')
    require(_text(mode['source_table']) and type(mode['source_pdf_page_1_based']) is int and mode['source_pdf_page_1_based']>0, 'first-instability source locator required')
    _evidence(mode['evidence'],record['source_id'])
    require(sum('reported_first_instability_mode' in e['supports'] for e in mode['evidence'])==1, 'one primary instability-mode evidence required')


def critical_strain_evidence(record):
    from .predictions import require
    entries=[e for e in record['critical_engineering_strain']['evidence'] if 'reported_critical_engineering_strain' in e['supports']]
    require(len(entries)==1,'one primary critical strain evidence required')
    return entries[0]


def instability_mode_evidence(record):
    from .predictions import require
    entries=[e for e in record['first_instability']['evidence'] if 'reported_first_instability_mode' in e['supports']]
    require(len(entries)==1,'one primary instability-mode evidence required')
    return entries[0]
