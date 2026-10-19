"""Offline private NOMAD original-structure consistency diagnostics (checkout CLI).

No network, admission, symmetry reconstruction, or scientific/rights approval.
Only scalar results, identities and content bindings leave the private input.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import stat
import sys
from urllib.parse import urlsplit

from materials_query.computed_schema_v2 import ELEMENTS, reduced_composition

ALGORITHM = 'private-original-structure-diagnostics/1.0.0'
MAX_BYTES = 1_000_000
MAX_SITES = 256
MAX_EVALUATIONS = 2_000_000
MAX_CONDITION = 1e6
VOLUME_TOLERANCE = 1e-8
ATOMIC_DENSITY_TOLERANCE = 1e-8
DENSITY_TOLERANCE = 0.002
DUPLICATE_DISTANCE_M = 1e-13
UNITS = {'lattice_vectors': 'm', 'cartesian_site_positions': 'm',
         'cell_volume': 'm^3', 'atomic_density': '1/m^3', 'mass_density': 'kg/m^3'}


class DiagnosticError(ValueError):
    """A fixed, safe error code; never includes private input values or paths."""


def require(condition, code):
    if not condition:
        raise DiagnosticError(code)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def positive(value):
    return finite(value) and value > 0


def identifier(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value) is not None


def hash_value(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def strict_load(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, 'input_size_limit')

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_json_key')
            result[key] = value
        return result

    def constant(_):
        raise DiagnosticError('nonfinite_json_number')

    def floating(value):
        result = float(value)
        require(math.isfinite(result), 'nonfinite_json_number')
        return result

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=floating)
    except DiagnosticError:
        raise
    except (UnicodeError, ValueError, RecursionError):
        raise DiagnosticError('invalid_json') from None


def bound_load(raw, expected):
    require(hash_value(expected) and sha256(raw) == expected, 'input_hash_mismatch')
    return strict_load(raw)


def source_reference(value):
    require(type(value) is dict and set(value) == {'url', 'version', 'sha256'}, 'source_reference_shape')
    require(hash_value(value['sha256']), 'source_reference_hash')
    require(type(value['version']) is str and re.fullmatch(r'[A-Za-z0-9_.+-]{1,128}', value['version']), 'source_reference_version')
    try:
        url = urlsplit(value['url'])
        valid = url.scheme in ('http', 'https') and bool(url.hostname) and url.username is None and url.password is None
    except (ValueError, TypeError, AttributeError):
        valid = False
    require(valid, 'source_reference_url')


def mass_contract(data):
    require(type(data) is dict and set(data) == {'schema', 'source', 'convention', 'masses_u', 'atomic_mass_constant_kg'}, 'mass_contract_shape')
    require(data['schema'] == 'geometry-masses/1', 'mass_contract_schema')
    require(data['convention'] in ('standard_atomic_weights', 'synthetic_test_only'), 'unsupported_mass_convention')
    source_reference(data['source'])
    masses = data['masses_u']
    require(type(masses) is dict and 1 <= len(masses) <= 118 and all(k in ELEMENTS and positive(v) for k, v in masses.items()), 'invalid_mass_table')
    constant = data['atomic_mass_constant_kg']
    require(type(constant) is dict and set(constant) == {'value', 'source'}, 'mass_constant_shape')
    require(positive(constant['value']), 'invalid_mass_constant')
    source_reference(constant['source'])
    return masses, constant['value']


def unit_contract(data):
    require(type(data) is dict and set(data) == {'schema', 'source', 'nomad_commit', 'units'}, 'unit_contract_shape')
    require(data['schema'] == 'nomad-geometry-units/1', 'unit_contract_schema')
    source_reference(data['source'])
    require(type(data['nomad_commit']) is str and re.fullmatch(r'[0-9a-f]{7,40}', data['nomad_commit']), 'unit_processing_commit')
    require(data['units'] == UNITS, 'unsupported_units')


def vector(value):
    return type(value) is list and len(value) == 3 and all(finite(x) for x in value)


def norm(value):
    return math.hypot(*value)


def multiply(row, matrix):
    return [math.fsum(row[k] * matrix[k][j] for k in range(3)) for j in range(3)]


def cell_data(cell):
    require(type(cell) is list and len(cell) == 3 and all(vector(row) for row in cell), 'invalid_lattice')
    scale = max(abs(x) for row in cell for x in row)
    require(positive(scale), 'singular_lattice')
    matrix = [[x / scale for x in row] for row in cell]
    (a, b, c), (d, e, f), (g, h, i) = matrix
    cof = [[e*i-f*h, c*h-b*i, b*f-c*e],
           [f*g-d*i, a*i-c*g, c*d-a*f],
           [d*h-e*g, b*g-a*h, a*e-b*d]]
    det = math.fsum([a*cof[0][0], b*cof[1][0], c*cof[2][0]])
    require(math.isfinite(det) and abs(det) > 1e-12, 'unstable_lattice')
    inverse = [[x / det for x in row] for row in cof]
    condition = norm([x for row in matrix for x in row]) * norm([x for row in inverse for x in row])
    require(math.isfinite(condition) and condition <= MAX_CONDITION, 'ill_conditioned_lattice')
    try:
        volume = abs(det) * scale**3
    except OverflowError:
        raise DiagnosticError('invalid_computed_volume') from None
    require(positive(volume), 'invalid_computed_volume')
    return matrix, inverse, scale, volume, condition


def minimum_periodic_distance(cell_m, positions_m, *, max_evaluations=MAX_EVALUATIONS):
    """Minimum over distinct sites and all nonzero self-images, all axes periodic.

    Rows are lattice vectors. A valid trial radius R bounds every closer image
    by abs(d_i+n_i) <= R*norm(column_i(A^-1)). The outward-padded integer box is
    exhaustively evaluated. No fixed 27-image or component-rounding assumption.
    """
    require(type(max_evaluations) is int and 1 <= max_evaluations <= MAX_EVALUATIONS, 'invalid_work_budget')
    matrix, inverse, scale, _, condition = cell_data(cell_m)
    require(type(positions_m) is list and 1 <= len(positions_m) <= MAX_SITES and all(vector(p) for p in positions_m), 'invalid_positions')
    positions = [[x / scale for x in p] for p in positions_m]
    require(all(abs(x) <= 1e6 for p in positions for x in p), 'excessive_coordinate_magnitude')
    inverse_norms = [norm([inverse[k][j] for k in range(3)]) for j in range(3)]
    evaluations = 0
    best = min(norm(row) for row in matrix)

    def closest(displacement, self_image):
        nonlocal evaluations
        frac = multiply(displacement, inverse)
        trial = min(norm(row) for row in matrix) if self_image else norm(multiply([x-round(x) for x in frac], matrix))
        require(math.isfinite(trial), 'nonfinite_distance')
        # We need the global minimum, not every individual pair minimum. The
        # already known physical image bounds the radius for improving it.
        trial = min(trial, best)
        bounds = []
        for x, inv_norm in zip(frac, inverse_norms):
            radius = trial * inv_norm
            pad = 128 * sys.float_info.epsilon * condition * max(1.0, abs(x), radius)
            lower = math.ceil(math.nextafter(-x-radius-pad, -math.inf))
            upper = math.floor(math.nextafter(-x+radius+pad, math.inf))
            bounds.append((lower, upper))
        count = math.prod(upper-lower+1 for lower, upper in bounds)
        if any(upper < lower for lower, upper in bounds):
            return trial
        require(evaluations + count <= max_evaluations, 'distance_work_budget_exceeded')
        result = trial
        for translation in itertools.product(*(range(lo, hi+1) for lo, hi in bounds)):
            evaluations += 1
            if self_image and translation == (0, 0, 0):
                continue
            distance = norm(multiply([frac[k]+translation[k] for k in range(3)], matrix))
            result = min(result, distance)
        return result

    best = min(best, closest([0.0, 0.0, 0.0], True))
    for i, first in enumerate(positions):
        for second in positions[i+1:]:
            best = min(best, closest([second[k]-first[k] for k in range(3)], False))
    value = best * scale
    require(finite(value), 'nonfinite_distance')
    return {'minimum_pair_distance_m': value, 'distance_evaluations': evaluations,
            'condition_estimate': condition, 'includes_nonzero_self_images': True}


def record_diagnostics(row, masses, constant, units, tolerances, max_evaluations):
    require(type(row) is dict and identifier(row.get('entry_id')), 'invalid_entry_id')
    try:
        archive = row['archive']; metadata = archive['metadata']; material = archive['results']['material']
        structure = archive['results']['properties']['structures']['structure_original']
    except (KeyError, TypeError):
        raise DiagnosticError('missing_original_structure') from None
    require(type(metadata) is dict and metadata.get('nomad_commit') == units['nomad_commit'], 'processing_commit_mismatch')
    if 'entry_id' in metadata:
        require(metadata['entry_id'] == row['entry_id'], 'metadata_entry_id_mismatch')
    require(type(material) is dict and identifier(material.get('material_id')), 'invalid_material_id')
    formula = material.get('chemical_formula_hill')
    try:
        composition = reduced_composition(formula)
    except (ValueError, TypeError):
        raise DiagnosticError('invalid_source_formula') from None
    if 'elements' in material:
        elements = material['elements']
        require(type(elements) is list and all(type(x) is str and x in ELEMENTS for x in elements)
                and len(set(elements)) == len(elements) and set(elements) == set(composition), 'material_elements_mismatch')
    require(type(structure) is dict, 'invalid_structure')
    require(structure.get('dimension_types') == [1, 1, 1] and all(type(x) is int for x in structure['dimension_types']), 'nonperiodic_structure')
    cell = structure.get('lattice_vectors'); positions = structure.get('cartesian_site_positions')
    _, _, _, volume, _ = cell_data(cell)
    require(type(positions) is list and 1 <= len(positions) <= MAX_SITES and all(vector(x) for x in positions), 'invalid_positions')
    labels = structure.get('species_at_sites')
    require(type(labels) is list and len(labels) == len(positions) and all(type(x) is str for x in labels), 'sites_positions_mismatch')
    if 'n_sites' in structure:
        require(type(structure['n_sites']) is int and structure['n_sites'] == len(positions), 'n_sites_mismatch')
    species = structure.get('species')
    require(type(species) is list and 1 <= len(species) <= MAX_SITES, 'invalid_species')
    mapping = {}
    for item in species:
        require(type(item) is dict and set(item) == {'name', 'chemical_symbols', 'concentration'}, 'unsupported_species_shape')
        name = item['name']; symbols = item['chemical_symbols']; weights = item['concentration']
        require(type(name) is str and 0 < len(name) <= 128 and name not in mapping, 'ambiguous_species')
        require(type(symbols) is list and len(symbols) == 1 and type(symbols[0]) is str and symbols[0] in ELEMENTS, 'unsupported_species')
        require(type(weights) is list and len(weights) == 1 and type(weights[0]) in (int, float) and weights[0] == 1, 'unsupported_occupancy')
        mapping[name] = symbols[0]
    require(set(labels) == set(mapping), 'species_mapping_mismatch')
    counts = Counter(mapping[x] for x in labels)
    divisor = math.gcd(*counts.values())
    reduced = {k: v//divisor for k, v in sorted(counts.items())}
    require(set(counts) <= set(masses), 'missing_element_mass')
    for key in ('cell_volume', 'atomic_density', 'mass_density'):
        require(positive(structure.get(key)), 'invalid_source_' + key)
    atom_density = len(positions)/volume
    density = math.fsum(counts[e]*masses[e]*constant for e in counts)/volume
    require(positive(atom_density) and positive(density), 'invalid_computed_density')
    errors = {'volume_relative_error': abs(volume-structure['cell_volume'])/structure['cell_volume'],
              'atomic_density_relative_error': abs(atom_density-structure['atomic_density'])/structure['atomic_density'],
              'density_mass_diagnostic_relative_error': abs(density-structure['mass_density'])/structure['mass_density']}
    require(all(finite(x) for x in errors.values()), 'nonfinite_relative_error')
    distance = minimum_periodic_distance(cell, positions, max_evaluations=max_evaluations)
    checks = {'formula_site_composition_match': reduced == composition, 'periodic_3d': True,
              'positions_and_sites_match': True, 'finite_geometry': True, 'finite_positive_density': True,
              'volume_consistency': errors['volume_relative_error'] <= tolerances['volume_relative'],
              'atomic_density_consistency': errors['atomic_density_relative_error'] <= tolerances['atomic_density_relative'],
              'density_mass_diagnostic_pass': errors['density_mass_diagnostic_relative_error'] <= tolerances['mass_density_relative'],
              'no_duplicate_periodic_sites': distance['minimum_pair_distance_m'] > DUPLICATE_DISTANCE_M}
    geometry_bytes = json.dumps(structure, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'entry_id': row['entry_id'], 'provider_material_id': material['material_id'], 'source_formula': formula,
            'geometry_projection_sha256': sha256(geometry_bytes), 'site_count': len(positions),
            'computed_volume_m3': volume, 'source_volume_m3': structure['cell_volume'],
            'computed_atomic_density_per_m3': atom_density, 'source_atomic_density_per_m3': structure['atomic_density'],
            'computed_mass_density_kg_m3': density, 'source_mass_density_kg_m3': structure['mass_density'],
            **distance, **errors, 'checks': checks, 'consistency_checks_passed': all(checks.values()), 'state': 'held'}


def diagnose(archive_bytes, mass_table_bytes, unit_contract_bytes, *, expected_archive_sha256,
             expected_mass_table_sha256, expected_unit_contract_sha256, expected_entry_ids,
             volume_tolerance=VOLUME_TOLERANCE, atomic_density_tolerance=ATOMIC_DENSITY_TOLERANCE,
             density_tolerance=DENSITY_TOLERANCE, max_evaluations=MAX_EVALUATIONS):
    """Return a safe held report. Invalid inputs return fixed reason codes, no data echo."""
    tolerances = {'volume_relative': volume_tolerance, 'atomic_density_relative': atomic_density_tolerance,
                  'mass_density_relative': density_tolerance, 'duplicate_distance_m': DUPLICATE_DISTANCE_M}
    report = {'schema': 'private-geometry-diagnostics/1', 'algorithm': ALGORITHM,
              'code_sha256': sha256(Path(__file__).read_bytes()),
              'composition_code_sha256': sha256((Path(__file__).parent/'materials_query/computed_schema_v2.py').read_bytes()),
              'input_sha256': {key: sha256(raw) if type(raw) is bytes else None for key, raw in
                               [('archive',archive_bytes), ('masses',mass_table_bytes), ('units',unit_contract_bytes)]},
              'state': 'held', 'scientific_review_approved': False,
              'rights_review_approved': False, 'admitted_delta': 0, 'records': []}
    try:
        require(all(type(raw) is bytes for raw in (archive_bytes,mass_table_bytes,unit_contract_bytes)), 'expected_input_bytes')
        require(all(positive(x) and x <= ceiling for x, ceiling in [(volume_tolerance,VOLUME_TOLERANCE), (atomic_density_tolerance,ATOMIC_DENSITY_TOLERANCE), (density_tolerance,DENSITY_TOLERANCE)]), 'invalid_tolerance')
        report['tolerances'] = tolerances
        require(type(expected_entry_ids) is list and 1 <= len(expected_entry_ids) <= 2 and all(identifier(x) for x in expected_entry_ids) and len(set(expected_entry_ids)) == len(expected_entry_ids), 'invalid_expected_cohort')
        data = bound_load(archive_bytes, expected_archive_sha256)
        mass_data = bound_load(mass_table_bytes, expected_mass_table_sha256)
        unit_data = bound_load(unit_contract_bytes, expected_unit_contract_sha256)
        masses, constant = mass_contract(mass_data); unit_contract(unit_data)
        require(type(data) is dict and type(data.get('data')) is list, 'invalid_archive_envelope')
        rows = data['data']; page = data.get('pagination')
        require(type(page) is dict and type(page.get('total')) is int and page['total'] == len(expected_entry_ids) and not page.get('next_page_after_value'), 'incomplete_cohort_pagination')
        require(len(rows) == len(expected_entry_ids) and all(type(row) is dict and identifier(row.get('entry_id')) for row in rows), 'invalid_cohort_rows')
        require(sorted(row['entry_id'] for row in rows) == sorted(expected_entry_ids), 'cohort_mismatch')
        for row in sorted(rows, key=lambda x: x['entry_id']):
            report['records'].append(record_diagnostics(row, masses, constant, unit_data, tolerances, max_evaluations))
        report['mass_convention'] = mass_data['convention']
        report['data_sources'] = {key: {'version': value['version'], 'sha256': value['sha256']} for key,value in [('masses',mass_data['source']), ('mass_constant',mass_data['atomic_mass_constant_kg']['source']), ('units',unit_data['source'])]}
        report['diagnostics_status'] = 'consistency_checks_passed' if all(r['consistency_checks_passed'] for r in report['records']) else 'held_checks_failed'
    except DiagnosticError as exc:
        report['diagnostics_status'] = 'held_invalid_input'; report['reason'] = str(exc)
    except (OverflowError, ZeroDivisionError, RecursionError):
        report['diagnostics_status'] = 'held_invalid_input'; report['reason'] = 'numerical_or_structure_limit'
    except (TypeError, KeyError, AttributeError, IndexError):
        report['diagnostics_status'] = 'held_invalid_input'; report['reason'] = 'invalid_structure_shape'
    return report


def read_private(path):
    try:
        p = Path(path)
        require(stat.S_ISREG(p.stat().st_mode) and p.stat().st_size <= MAX_BYTES, 'input_not_bounded_regular_file')
        with p.open('rb') as stream:
            raw = stream.read(MAX_BYTES+1)
        require(len(raw) <= MAX_BYTES, 'input_size_limit')
        return raw
    except OSError:
        raise DiagnosticError('input_file_unavailable') from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'masses', 'units'):
        parser.add_argument('--'+name, required=True)
        parser.add_argument('--'+name+'-sha256', required=True)
    parser.add_argument('--entry-id', action='append', required=True)
    args = parser.parse_args(argv)
    try:
        report = diagnose(read_private(args.archive), read_private(args.masses), read_private(args.units),
                          expected_archive_sha256=args.archive_sha256, expected_mass_table_sha256=args.masses_sha256,
                          expected_unit_contract_sha256=args.units_sha256, expected_entry_ids=args.entry_id)
    except DiagnosticError as exc:
        report = {'schema':'private-geometry-diagnostics/1', 'state':'held', 'admitted_delta':0,
                  'diagnostics_status':'held_invalid_input', 'reason':str(exc)}
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return {'consistency_checks_passed':0, 'held_checks_failed':1, 'held_invalid_input':2}[report['diagnostics_status']]


if __name__ == '__main__':
    raise SystemExit(main())
