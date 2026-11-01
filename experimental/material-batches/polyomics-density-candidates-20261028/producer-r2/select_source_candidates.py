"""Freeze source facts from one PolyOmics cohort; not canonical identity admission."""
import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / 'experimental/material-batches/quota1000-polyomics-source-audit-20261027'
sys.path.insert(0, str(AUDIT))
import inspect_polyomics as source
from periodic_repeat_graph import normalize, parse, METHOD, rdBase

INDEX_SHA = '2ca48363c749d58a84fb23b0c1a6a76d84a4cd51905b7367a0ce18f75a5a027d'
NORMALIZER_SHA = 'dc876ffd51f7aa303f09888229922097648f3937f933254856508357de75fb2d'
COHORT = {'RadonPy_ver': '0.2.10', 'preset_eq_ver': '0.2.1', 'forcefield': 'GAFF2_mod',
          'temp': '300.0', 'press': '1.0', 'check_eq': 'True'}
EXTRA_FIELDS = ['input_nchain', 'input_natom', 'n_mol', 'ini_density', 'nematic_order_parameter', 'Python_ver',
                'RDKit_ver', 'Psi4_ver', 'LAMMPS_ver', 'charge', 'qm_method']


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf8')


def cohort_hold(row, has_fluorine):
    if any(row[k] != value for k, value in COHORT.items()):
        return 'Outside fixed source-version/condition cohort'
    if not has_fluorine:
        return 'No fluorine atom in source repeat-unit graph'
    try:
        order = Decimal(row['nematic_order_parameter'])
    except InvalidOperation:
        return 'Missing or invalid source nematic-order token'
    if not order.is_finite() or not Decimal('0') <= order <= Decimal('0.1'):
        return 'Source nematic-order token outside explicit finite 0..0.1 screen'
    return None


def select(cache, limit=1000):
    if type(limit) is not int or limit < 1:
        raise ValueError('Positive integer limit required')
    if sha256((AUDIT / 'periodic_repeat_graph.py').read_bytes()).hexdigest() != NORMALIZER_SHA:
        raise ValueError('Different unreviewed graph prototype')
    if rdBase.rdkitVersion != '2025.09.6':
        raise ValueError('Use the fixed isolated RDKit tool')
    raw = (cache / 'PFAS.csv').read_bytes()
    digest, length = source.FILES['PFAS.csv']
    if sha256(raw).hexdigest() != digest or len(raw) != length:
        raise ValueError('Different fixed source CSV')
    index_raw = (cache / 'periodic-graph-prototype-r1/periodic-graph-index.json').read_bytes()
    if sha256(index_raw).hexdigest() != INDEX_SHA:
        raise ValueError('Different prototype index')
    index = json.loads(index_raw)
    by_uuid = {}
    for key, group in index['groups'].items():
        if key != group['periodic_graph']['periodic_graph_key_sha256']:
            raise ValueError('Prototype index key mismatch')
        for record in group['source_records']:
            if record['source_file'] == 'PFAS.csv':
                if record['uuid'] in by_uuid:
                    raise ValueError('Repeated source UUID in graph index')
                by_uuid[record['uuid']] = (key, record)
    groups, held, seen, parsed = {}, Counter(), set(), {}
    source_rows = 0
    for row_index, row in source.read_rows(raw):
        source_rows += 1
        if row['UUID'] in seen:
            raise ValueError('Duplicate source UUID')
        seen.add(row['UUID'])
        if row['UUID'] not in by_uuid:
            held['Outside restricted periodic-graph prototype'] += 1
            continue
        key, indexed = by_uuid[row['UUID']]
        facts = source.selected_facts(row)
        if (facts['source_smiles_1'] != indexed['source_smiles_1']
                or facts['source_density_literal'] != indexed['source_density_literal']
                or facts['source_conditions'] != indexed['source_conditions']
                or row_index != indexed['source_row_index']):
            raise ValueError('Source facts differ from fixed graph index')
        smiles = row['smiles_1']
        if smiles not in parsed:
            molecule = parse(smiles)
            parsed[smiles] = any(a.GetAtomicNum() == 9 for a in molecule.GetAtoms())
        reason = cohort_hold(row, parsed[smiles])
        if reason:
            held[reason] += 1
            continue
        facts.update(source_file='PFAS.csv', source_record_index_0_based=row_index,
                     source_record_number_1_based_excluding_header=row_index + 1,
                     source_row_fields_canonical_json_sha256=sha256(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf8')).hexdigest(),
                     additional_source_literals={k: row[k] for k in EXTRA_FIELDS})
        groups.setdefault(key, []).append(facts)
    if len(groups) < limit:
        raise ValueError('Insufficient operational groups; this is not an identity count')
    candidates = []
    for key in sorted(groups)[:limit]:
        rows = sorted(groups[key], key=lambda r: r['uuid'])
        chosen = rows[0]
        graph = normalize(chosen['source_smiles_1'])
        if graph['periodic_graph_key_sha256'] != key:
            raise ValueError('Chosen source representation does not reproduce prototype key')
        candidates.append({
            'candidate_status': 'source_fact_proposal_pending_independent_graph_identity_and_method_review',
            'proposed_category': 'polymer', 'operational_graph_key_sha256': key,
            'unreviewed_periodic_graph': graph, 'selected_source_record': chosen,
            'cohort_rows_sharing_operational_key': len(rows),
            'selected_quantity': 'mass_density', 'proposed_unit_code': 'g/cm^3',
            'evidence_kind': 'published_computational_reference',
            'statistical_aggregation': 'not_established_for_this_csv_export',
            'uncertainty': None, 'independent_specimen_count': None,
            'physical_experimental_existence': 'unknown',
            'canonical_polymer_identity': 'unresolved', 'existing_identity_overlap': 'pending',
            'admitted_increment': 0,
        })
    materials_raw = (ROOT / 'materials_boundaries/data/materials.json').read_bytes()
    materials = json.loads(materials_raw)
    identities = [r for r in materials['identities'] if r['category'] == 'polymer']
    ids = {r['id'] for r in identities}
    baseline = {'schema': 'polyomics-existing-polymer-crosswalk-input/1',
                'scope': 'Frozen existing 37 polymer identities and source-scoped states for future finite overlap review, not an overlap decision.',
                'working_materials_sha256': sha256(materials_raw).hexdigest(),
                'identities': identities, 'grades': [r for r in materials['grades'] if r['identity_id'] in ids],
                'states': [r for r in materials['records'] if r['identity_id'] in ids],
                'overlap_decision': 'not_run'}
    if len(identities) != 37:
        raise ValueError('Different polymer baseline; requires fresh crosswalk scope')
    result = {'schema': 'polyomics-frozen-source-fact-proposals/1',
              'status': 'held_pending_independent_source_graph_identity_and_method_review',
              'source_revision': source.REVISION, 'source_doi': '10.57967/hf/7475',
              'source_file': 'PFAS.csv', 'source_sha256': digest, 'source_rows_checked': source_rows,
              'prototype_index_sha256': INDEX_SHA, 'prototype_method': METHOD,
              'normalizer_sha256': NORMALIZER_SHA, 'rdkit_version': rdBase.rdkitVersion,
              'cohort_required_literals': dict(COHORT),
              'cohort_eligible_source_rows': sum(map(len, groups.values())),
              'available_operational_graph_groups': len(groups), 'held_source_rows': dict(held),
              'proposed_count': len(candidates), 'canonical_polymer_identity_count': None,
              'selection': 'First requested operational graph keys in lexicographic order; minimum source UUID within each cohort group. No density ranking or averaging.',
              'nematic_screen_scope': 'Finite 0..0.1 heuristic on the reported token; not independent isotropy, equilibrium or convergence certification.',
              'baseline_polymer_crosswalk_sha256': sha256(encoded(baseline)).hexdigest(),
              'handoff_ready': False, 'admitted_increment': 0, 'candidates': candidates,
              'pending': ['Independent source and rights audit', 'Restricted periodic equivalence/identity and existing baseline overlap review',
                          'MD density basis, unit and unknown aggregation contract', 'Native mapping and runtime/history/installed gates']}
    return result, baseline


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    result, baseline = select(args.cache)
    for name, value in [('source-fact-candidates.json', result), ('baseline-polymer-crosswalk.json', baseline)]:
        path = Path(__file__).with_name(name)
        raw = encoded(value)
        if path.exists() and path.read_bytes() != raw:
            raise ValueError('Refusing a different frozen output: ' + name)
        path.write_bytes(raw)
    print(json.dumps({'proposed': result['proposed_count'], 'eligible_rows': result['cohort_eligible_source_rows'],
                      'operational_groups_not_identities': result['available_operational_graph_groups'],
                      'sha256': sha256(encoded(result)).hexdigest(), 'admitted_increment': 0}))
