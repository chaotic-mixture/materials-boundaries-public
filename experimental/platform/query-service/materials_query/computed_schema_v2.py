"""Strict metadata-only, composition-scoped hypothetical-model review contract.

Version 2 does not assert physical equivalence, phase stability or global novelty.
It deliberately admits only the scientific scope represented by this contract;
changing that scope requires an explicitly reviewed future schema/policy.
"""
import math
import re
from functools import reduce
from urllib.parse import urlsplit

SCHEMA = 'computed-review/2'
COUNT_POLICY = {
    'schema': 'computed-count-policy/1',
    'rule': 'one-per-reduced-integer-composition',
    'scope': 'accepted records in this independently pinned review tranche only',
    'equivalence': 'unresolved phase/site-order and cross-provider equivalence; buckets are counting conventions, not physical identities',
    'max_count_per_composition': 1,
}
ELEMENTS = set('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split())
# Conservative ordinary compositional metals. Ambiguous/metalloid membership is
# excluded; adding a new classification requires review, not an electronic claim.
METALS = set('Li Be Na Mg Al K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr'.split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return type(value) is str and 0 < len(value) <= 4096 and bool(value.strip()) and not any(ord(c) < 32 for c in value)


def identifier(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value) is not None


def hash256(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def positive(value):
    return number(value) and value > 0


def nonnegative(value):
    return number(value) and value >= 0


def integer(value):
    return type(value) is int and 1 <= value <= 1000000


def url(value):
    if not text(value):
        return False
    try:
        p = urlsplit(value)
        return p.scheme in ('https', 'http') and bool(p.hostname) and p.username is None and p.password is None
    except ValueError:
        return False


def enum(*values):
    return lambda value: type(value) is str and value in values


def array(check, maximum=1000, minimum=0):
    return lambda value: type(value) is list and minimum <= len(value) <= maximum and all(check(x) for x in value)


def shape(value, required, optional=None):
    optional = optional or {}
    require(type(value) is dict and set(required) <= set(value) <= set(required) | set(optional), 'Unexpected metadata shape')
    for key, item in value.items():
        require((required | optional)[key](item), 'Invalid metadata field: ' + key)
    return True


def obj(required, optional=None):
    return lambda value: shape(value, required, optional)


def composition(value):
    return type(value) is dict and 1 <= len(value) <= 32 and all(k in ELEMENTS and integer(v) for k, v in value.items()) and reduce(math.gcd, value.values()) == 1


def reduced_composition(formula):
    require(type(formula) is str and 0 < len(formula) <= 256, 'Invalid source formula')
    tokens = re.findall(r'([A-Z][a-z]?)([1-9][0-9]{0,5})?', formula)
    require(tokens and ''.join(a+b for a,b in tokens) == formula, 'Unsupported integer formula syntax')
    counts = {}
    for element, n in tokens:
        require(element in ELEMENTS and element not in counts, 'Invalid or repeated formula element')
        counts[element] = int(n or 1)
    divisor = reduce(math.gcd, counts.values())
    return {e: counts[e] // divisor for e in sorted(counts)}


def composition_bucket(counts):
    require(composition(counts), 'Expected reduced integer composition')
    return 'computed-composition:' + ''.join(e + (str(n) if n != 1 else '') for e,n in sorted(counts.items()))


DENSITY = obj({'value': positive, 'unit': enum('kg/m^3'), 'evidence_kind': enum('computed'),
    'source_path': enum('results.properties.structures.structure_original.mass_density')})
SCOPE = obj({'kind': enum('hypothetical_computed_crystal_model'), 'prototype_aflow_id': identifier,
    'space_group_number_provider_reported': lambda v: type(v) is int and 1 <= v <= 230,
    'provider_material_id': identifier, 'phase_identity_confidence': text,
    **{k: enum('unknown') for k in ('experimental_existence','phase_stability','equilibrium','convergence')},
    'temperature_K': lambda v: v is None, 'pressure_Pa': lambda v: v is None})
METHOD = obj({'parameter_variation_id': identifier, 'method_name': enum('DFT'), 'simulation': obj({
    'program_name': text, 'program_version': text, 'dft': obj({
        'basis_set_type': text, 'core_electron_treatment': text, 'scf_threshold_energy_change': positive,
        'xc_functional_type': text, 'xc_functional_names': array(text, 32, 1)})}, {
    'geometry_optimization': obj({'type': text, 'convergence_tolerance_energy_difference': positive})})})
PROVENANCE = obj({**{k: text for k in ('external_db','last_processing_time','license','mainfile','nomad_commit','nomad_version')},
    'references': array(url, 100), 'upload_id': identifier})
ATTRIBUTION = array(obj({'user_id': identifier, 'name': text}), 100, 1)
RIGHTS = obj({'license': enum('CC BY 4.0'), 'license_url': enum('https://creativecommons.org/licenses/by/4.0/'),
    'scope': text, 'changes': text, 'project_changes': text})
CHECKS = obj({**{k: lambda v: type(v) is bool for k in (
    'entry_set_complete','source_formula_and_material_match','formula_site_composition_match',
    'source_density_exact_match','source_method_exact_match','source_symmetry_exact_match',
    'source_license_exact_match','source_mainfile_exact_match','periodic_3d','positions_and_sites_match',
    'finite_geometry','finite_positive_density','density_mass_diagnostic_pass','no_duplicate_periodic_sites')},
    **{k: nonnegative for k in ('volume_relative_error','atomic_density_relative_error','density_mass_diagnostic_relative_error')},
    'density_mass_diagnostic_tolerance': positive, 'minimum_pair_distance_m': positive, 'geometry_sha256': hash256})
EVIDENCE = obj({k: hash256 for k in ('candidate_packet_sha256','archive_response_sha256','relations_response_sha256',
    'frozen_source_response_sha256','attribution_response_sha256')})
CONFIDENCE = obj({'traceability': enum('high'), 'composition_and_cell_density_consistency': enum('high'),
    'real_world_predictive_validity': enum('unassessed')})
GROUP = obj({'provider_material_id': identifier, 'entry_count': integer, 'selected_group': lambda v: type(v) is bool,
    'space_groups': array(lambda v: type(v) is int and 1 <= v <= 230, 230, 1), 'mainfiles': array(text, 1000, 1)})
RELATIONS = obj({'same_composition_rows_current_OQMD': integer,
    'same_composition_provider_groups': lambda v: type(v) is dict and 1 <= len(v) <= 100 and all(identifier(k) and array(identifier,1000,1)(a) for k,a in v.items()),
    'query_complete': lambda v: type(v) is bool, 'query_scope': text, 'group_details': array(GROUP,100,1),
    'relation_to_other_same_composition_groups': enum('potential_same_material_or_polymorph; not additional count without structural adjudication'),
    **{k: array(text,1000) for k in ('prior_seven_hits','other_batch_same_composition_hits','baseline_identifier_or_formula_hits')},
    'baseline_comparison_scope': text,
    'cross_provider_global_equivalence': enum('unresolved; no global novelty or universal uniqueness claim')})
RECORD = {
    'candidate_id': identifier, 'decision': enum('accepted','held'), 'reason': text,
    'project_material_id': text, 'formula': text, 'provider': enum('nomad'),
    'provider_entry_id': identifier, 'provider_material_id': identifier, 'source_url': url,
    'canonical_composition': composition, 'conservative_count_bucket': text,
    'primary_category': enum('metal','inorganic'), 'category_basis': text, 'electronic_behavior': enum('unknown'),
    'material_scope': SCOPE, 'density': DENSITY, 'method': METHOD, 'provenance': PROVENANCE,
    'attribution': ATTRIBUTION, 'rights': RIGHTS, 'checks': CHECKS,
    'overlap_relations': RELATIONS, 'scientific_confidence': CONFIDENCE, 'evidence': EVIDENCE,
}


def validate_review_v2(review):
    shape(review, {'schema': enum(SCHEMA), 'input_file_sha256': hash256, 'reviewer': text,
        'rationale': text, 'count_policy': lambda v: type(v) is dict and v == COUNT_POLICY and type(v.get('max_count_per_composition')) is int,
        'records': array(lambda r: shape(r, RECORD), 1000)})
    candidates, entries, group_compositions, entry_groups = set(), set(), {}, {}
    for r in review['records']:
        require(r['candidate_id'] not in candidates and r['provider_entry_id'] not in entries, 'Duplicate candidate or selected entry ID')
        candidates.add(r['candidate_id']); entries.add(r['provider_entry_id'])
        require(r['project_material_id'] == 'computed:nomad:' + r['provider_material_id'], 'Project ID must bind provider model')
        require(r['source_url'] == 'https://nomad-lab.eu/prod/v1/gui/entry/id/' + r['provider_entry_id'], 'Source URL must bind selected entry')
        require(r['canonical_composition'] == reduced_composition(r['formula']), 'Source formula/composition mismatch')
        bucket = composition_bucket(r['canonical_composition'])
        require(r['conservative_count_bucket'] == bucket, 'Composition bucket mismatch')
        elements = set(r['canonical_composition'])
        require((r['primary_category'] == 'metal' and elements <= METALS) or
                (r['primary_category'] == 'inorganic' and 'O' in elements and 'C' not in elements), 'Category/composition mismatch')
        require(r['material_scope']['provider_material_id'] == r['provider_material_id'], 'Scope/model mismatch')
        require(r['provenance']['license'] == r['rights']['license'], 'Provenance/license mismatch')
        checks = r['checks']
        require(all(v for v in checks.values() if type(v) is bool), 'Scientific checks did not pass')
        require(checks['density_mass_diagnostic_relative_error'] <= checks['density_mass_diagnostic_tolerance'], 'Density diagnostic failed')
        relations = r['overlap_relations']; groups = relations['same_composition_provider_groups']
        all_entries = [e for es in groups.values() for e in es]
        require(len(set(all_entries)) == len(all_entries) == relations['same_composition_rows_current_OQMD'], 'Relation calculation count mismatch')
        require(r['provider_entry_id'] in groups.get(r['provider_material_id'], []), 'Selected entry missing from selected group')
        details = relations['group_details']
        require(len(details) == len(groups) and {g['provider_material_id'] for g in details} == set(groups), 'Group details mismatch')
        for g in details:
            mid = g['provider_material_id']
            require(g['entry_count'] == len(groups[mid]) and g['selected_group'] == (mid == r['provider_material_id']), 'Group detail count/selection mismatch')
            require(group_compositions.setdefault(mid,bucket) == bucket, 'Provider group has conflicting compositions')
            for eid in groups[mid]:
                require(entry_groups.setdefault(eid,mid) == mid, 'Calculation maps to multiple provider groups')
