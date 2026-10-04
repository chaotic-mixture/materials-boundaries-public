"""Explicit historical fixtures, separate from the open-ended live catalog.

Historical science is selected by ID, never position. Exact search expectations
use an isolated snapshot with fixed evidence memberships: adding another source,
record, or evidence link to the packaged catalog must not close its growth path.
"""
import copy
from contextlib import contextmanager
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from source_evidence_preservation import current_provenance
from materials_boundaries.catalog import read_catalog

EXECUTABLE_IDS = (
    'hs_bulk_3d_two_phase',
    'reuss_bulk',
    'voigt_bulk',
    'hs_shear_3d_two_phase',
    'reuss_shear',
    'voigt_shear',
    'youngs_modulus_outer',
    'poissons_ratio_outer',
)

GRIFFITH_IDS = (
    'griffith_central_crack_plane_stress',
    'griffith_central_crack_plane_strain',
)

MECHANICS_IDS = (
    'frenkel_slip_specific_ideal_shear',
    'uber_normal_cohesive_strength',
    'lefm_central_crack_mode_i_stress_intensity',
    'lefm_mode_i_energy_release_relation',
    'lefm_center_crack_finite_width_secant_factor',
)

CORE_STABILITY_IDS = (
    'general_stiffness_positive_definite',
    'cubic_born_stability',
    'hexagonal_born_stability',
    'orthorhombic_born_stability',
)

POROUS_IDS = (
    'hs_porous_bulk_3d_solid_void',
    'hs_porous_shear_3d_solid_void',
    'hs_porous_youngs_outer_3d_solid_void',
)

CRYSTAL_STABILITY_IDS = (
    'tetragonal_i_born_stability',
    'tetragonal_ii_born_stability',
    'rhombohedral_i_born_stability',
    'rhombohedral_ii_born_stability',
)

HISTORICAL_SOURCE_IDS = (
    'hashin_shtrikman_1963',
    'kochmann_milton_2014',
    'berger_2017',
    'milton_2018_comment',
    'berger_2018_reply',
    'singh_lai_2024',
    'materials_project_elasticity',
    'genin_birman_2009',
    'meille_garboczi_2001',
    'griffith_1921',
    'wilson_1992_nasa_tm_103591',
    'frenkel_1926',
    'shimanek_2022_ideal_shear',
    'rose_ferrante_smith_1981',
    'van_der_ven_ceder_2004',
    'azocar_guzman_2020_hydrogen',
    'pierce_sullivan_1969_nasa_tn_d_5140',
    'mouhat_coudert_2014_elastic_stability',
    'roberts_garboczi_2002_porous',
    'lee_wei_kysar_hone_2008',
)

OBSERVATION_IDS = (
    'lee_2008_graphene_in_plane_stiffness_2d',
    'lee_2008_graphene_breaking_strength_2d',
)

HISTORICAL_CLAIM_IDS = (
    EXECUTABLE_IDS + GRIFFITH_IDS + MECHANICS_IDS + CORE_STABILITY_IDS +
    POROUS_IDS + CRYSTAL_STABILITY_IDS
)

_HISTORICAL_EVIDENCE_IDS = {
    'hs_bulk_3d_two_phase': (
        'kochmann_milton_2014',
        'hashin_shtrikman_1963',
    ),
    'reuss_bulk': (
        'kochmann_milton_2014',
    ),
    'voigt_bulk': (
        'kochmann_milton_2014',
    ),
    'hs_shear_3d_two_phase': (
        'kochmann_milton_2014',
        'hashin_shtrikman_1963',
    ),
    'reuss_shear': (
        'kochmann_milton_2014',
    ),
    'voigt_shear': (
        'kochmann_milton_2014',
    ),
    'youngs_modulus_outer': (
        'kochmann_milton_2014',
        'meille_garboczi_2001',
    ),
    'poissons_ratio_outer': (
        'kochmann_milton_2014',
        'meille_garboczi_2001',
    ),
    'griffith_central_crack_plane_stress': (
        'wilson_1992_nasa_tm_103591',
        'griffith_1921',
    ),
    'griffith_central_crack_plane_strain': (
        'wilson_1992_nasa_tm_103591',
        'griffith_1921',
    ),
    'frenkel_slip_specific_ideal_shear': (
        'shimanek_2022_ideal_shear',
        'frenkel_1926',
    ),
    'uber_normal_cohesive_strength': (
        'azocar_guzman_2020_hydrogen',
        'van_der_ven_ceder_2004',
        'rose_ferrante_smith_1981',
    ),
    'lefm_central_crack_mode_i_stress_intensity': (
        'wilson_1992_nasa_tm_103591',
    ),
    'lefm_mode_i_energy_release_relation': (
        'wilson_1992_nasa_tm_103591',
    ),
    'lefm_center_crack_finite_width_secant_factor': (
        'wilson_1992_nasa_tm_103591',
        'pierce_sullivan_1969_nasa_tn_d_5140',
    ),
    'general_stiffness_positive_definite': (
        'mouhat_coudert_2014_elastic_stability',
    ),
    'cubic_born_stability': (
        'mouhat_coudert_2014_elastic_stability',
    ),
    'hexagonal_born_stability': (
        'mouhat_coudert_2014_elastic_stability',
    ),
    'orthorhombic_born_stability': (
        'mouhat_coudert_2014_elastic_stability',
    ),
    'hs_porous_bulk_3d_solid_void': (
        'kochmann_milton_2014',
        'hashin_shtrikman_1963',
    ),
    'hs_porous_shear_3d_solid_void': (
        'kochmann_milton_2014',
        'hashin_shtrikman_1963',
    ),
    'hs_porous_youngs_outer_3d_solid_void': (
        'roberts_garboczi_2002_porous',
    ),
    'tetragonal_i_born_stability': (
        'mouhat_coudert_2014_elastic_stability',
    ),
    'tetragonal_ii_born_stability': (
        'mouhat_coudert_2014_elastic_stability',
    ),
    'rhombohedral_i_born_stability': (
        'mouhat_coudert_2014_elastic_stability',
    ),
    'rhombohedral_ii_born_stability': (
        'mouhat_coudert_2014_elastic_stability',
    ),
    'lee_2008_graphene_in_plane_stiffness_2d': (
        'lee_wei_kysar_hone_2008',
    ),
    'lee_2008_graphene_breaking_strength_2d': (
        'lee_wei_kysar_hone_2008',
    ),
}


def select_records(catalog, identifiers):
    """Select every requested historical record, preserving explicit fixture order."""
    by_id = {record['id']: record for record in catalog['records']}
    return [by_id[identifier] for identifier in identifiers]


def historical_records(kind, identifiers):
    return select_records(read_catalog(kind), identifiers)


def evidence_for(record, source_id):
    """Find historical evidence even after same-source additions or reordering."""
    candidates = [item for item in record['evidence'] if item['source_id'] == source_id]
    identifier = record.get('id')
    for kind in ('claims', 'observations'):
        baseline = _provenance_baseline()[kind].get(identifier)
        expected = (current_provenance(kind, identifier, baseline).get('evidence', [])
                    if baseline is not None else [])
        for original in expected:
            if original['source_id'] == source_id and original in candidates:
                return next(item for item in candidates if item == original)
    return next(iter(candidates))


def scientific_digest(records):
    """Lock historical scientific metadata while allowing evidence to accumulate.

    Evidence, curation provenance, and review progress are independently tested
    where relevant; adding an evidence entry should not change a science digest.
    """
    projection = [{key: value for key, value in record.items()
                   if key not in {'evidence', 'provenance', 'verification', 'claim_notes'}}
                  for record in records]
    serialized = json.dumps(projection, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(serialized.encode()).hexdigest()


def historical_catalog(kind):
    """A controlled query fixture, not a count contract for packaged records."""
    catalog = read_catalog(kind)
    if kind == 'locales':
        # No new labels should change matching against the historical fixture.
        for labels in catalog['languages'].values():
            for key in list(labels):
                identifier = key.removeprefix('catalog_name_')
                if key.startswith('catalog_name_') and identifier not in HISTORICAL_CLAIM_IDS + OBSERVATION_IDS:
                    del labels[key]
        return catalog
    identifiers = {'claims': HISTORICAL_CLAIM_IDS, 'sources': HISTORICAL_SOURCE_IDS,
                   'observations': OBSERVATION_IDS}[kind]
    catalog['records'] = select_records(catalog, identifiers)
    for record in catalog['records']:
        if kind != 'sources':
            # Search only needs source membership. Pin it independently of any
            # added or reordered evidence in the live record.
            record['evidence'] = [copy.deepcopy(evidence_for(record, source_id))
                                  for source_id in _HISTORICAL_EVIDENCE_IDS[record['id']]]
    return catalog


@contextmanager
def isolated_catalogs():
    snapshots = {kind: historical_catalog(kind)
                 for kind in ('claims', 'sources', 'observations', 'locales')}
    with patch('materials_boundaries.catalog.read_catalog',
               side_effect=lambda kind: copy.deepcopy(snapshots[kind])):
        yield snapshots


@lru_cache(maxsize=1)
def _provenance_baseline():
    path = Path(__file__).parent / 'fixtures/historical_provenance.json'
    return json.loads(path.read_text(encoding='utf-8'))


def expected_provenance(kind, identifier):
    """Current expectations overlay only exact reviewed historical corrections."""
    return current_provenance(kind, identifier, _provenance_baseline()[kind][identifier])


def expected_evidence(kind, identifier, source_id):
    return evidence_for(expected_provenance(kind, identifier), source_id)
