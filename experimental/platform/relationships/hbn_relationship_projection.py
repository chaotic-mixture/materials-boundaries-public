"""Read-only projection of reviewed hBN catalog relationships; no admission.

This checkout command exposes one proposed material and its bounded study
context. Navigation never transfers observation properties to other nodes.
"""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'formal-catalog'))

from materials_boundaries.catalog import read_catalog
from materials_boundaries._hbn_observation_contract import (
    HBN_FAMILY, HBN_SOURCE, HBN_SCIENTIFIC_PAYLOAD_SHA256, validate_hbn_records,
)
from materials_project_catalog.catalog import formal_project_catalog

SCHEMA = 'hbn-relationship-projection/1'
REVIEW_PATH = Path(__file__).with_name('hbn_projection_review.json')
EXAMPLES_PATH = Path(__file__).with_name('typed_edge_examples.json')
REVIEW_SHA256 = '26466e3692777f782f69f7e40e9968d7806b57f929c83e6f301c50d45db42cb1'
SOURCE_IDS = {
    'in_plane_stiffness_2d': 'falin_2017_hbn_monolayer_in_plane_stiffness_2d',
    'breaking_strength_2d': 'falin_2017_hbn_monolayer_breaking_strength_2d',
}
MAX_RECORDS, MAX_BYTES, MAX_DEPTH = 1000, 12_000_000, 8


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return sha256(canonical(value)).hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def _constant(_):
    raise ValueError('Nonfinite JSON value')


def _load(path):
    raw = path.read_bytes()
    require(len(raw) <= MAX_BYTES, 'Relationship input exceeds byte limit')
    return raw, json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)


def _identifier(value):
    return (type(value) is str and 0 < len(value) <= 256
            and value.strip() == value and all(ord(c) >= 32 and ord(c) != 127 for c in value))


def _review():
    raw, review = _load(REVIEW_PATH)
    require(sha256(raw).hexdigest() == REVIEW_SHA256, 'Relationship review changed; review required')
    require(review['schema'] == 'hbn-relationship-review/1', 'Unsupported relationship review')
    mappings = review['source_observations']
    require(len(mappings) == len(SOURCE_IDS), 'Invalid reviewed observation mapping')
    by_quantity = {row['quantity']: row for row in mappings}
    require(set(by_quantity) == set(SOURCE_IDS), 'Invalid reviewed quantities')
    for quantity, source_id in SOURCE_IDS.items():
        row = by_quantity[quantity]
        require(row['source_observation_id'] == source_id and row['study_id'] == HBN_SOURCE
                and row['method_family'] == HBN_FAMILY
                and row['scientific_payload_sha256'] == HBN_SCIENTIFIC_PAYLOAD_SHA256[quantity],
                'Reviewed source observation no longer matches core contract')
    return review, by_quantity


def _checked_edges(typed_edges, review):
    if typed_edges is None:
        _, typed_edges = _load(EXAMPLES_PATH)
    require(type(typed_edges) is list, 'Typed examples must be a list')
    require(len(canonical(typed_edges)) <= MAX_BYTES, 'Typed examples exceed byte limit')
    expected = {row['id']: row['sha256'] for row in review['existing_edges']}
    require(len(expected) == 5, 'Expected five reviewed hBN examples')
    found, seen = {}, set()
    for edge in typed_edges:
        require(type(edge) is dict and _identifier(edge.get('id')), 'Invalid typed edge ID')
        require(edge['id'] not in seen, 'Duplicate typed edge ID')
        seen.add(edge['id'])
        relevant = (edge['id'] in expected
                    or any(HBN_SOURCE in str(edge.get(k, '')) for k in ('subject', 'object'))
                    or any(edge.get(k) in SOURCE_IDS.values() for k in ('subject', 'object'))
                    or any(type(e) is dict and e.get('source_id') == HBN_SOURCE
                           for e in edge.get('evidence', [])))
        if relevant:
            require(edge['id'] in expected and digest(edge) == expected[edge['id']],
                    'Unreviewed or changed hBN example edge')
            found[edge['id']] = deepcopy(edge)
    require(set(found) == set(expected), 'Missing reviewed hBN example edge')
    edges = list(found.values()) + deepcopy(review['bridge_edges'])
    require(len(edges) == 7 and len({e['id'] for e in edges}) == 7, 'Invalid reviewed edge set')
    for edge in edges:
        require(edge['status'] == 'supported' and edge['curation'] == 'proposed',
                'Relationship curation is not proposed')
        require(edge['subject'] != edge['object'], 'Self relationship is not supported')
    return edges


def _observation_groups(observations, mappings):
    if observations is None:
        observations = read_catalog('observations')
    if type(observations) is dict:
        observations = observations.get('records')
    require(type(observations) is list and len(observations) <= MAX_RECORDS,
            'Observations must be a bounded record list or catalog')
    require(len(canonical(observations)) <= MAX_BYTES, 'Observation input exceeds byte limit')
    records = deepcopy(observations)
    ids = [row.get('id') if type(row) is dict else None for row in records]
    require(all(_identifier(rid) for rid in ids), 'Invalid catalog observation ID')
    require(len(set(ids)) == len(ids), 'Duplicate catalog observation ID')
    selected = [row for row in records if row.get('method_family') == HBN_FAMILY
                or row.get('study_id') == HBN_SOURCE or row['id'] in SOURCE_IDS.values()]
    for row in selected:
        if row['id'] in SOURCE_IDS.values():
            require(row.get('study_id') == HBN_SOURCE and row.get('method_family') == HBN_FAMILY
                    and row['id'] == SOURCE_IDS.get(row.get('quantity')),
                    'Canonical source observation ID has conflicting content')
    validate_hbn_records(selected)
    groups = {}
    for row in selected:
        mapping = mappings[row['quantity']]
        # The existing core guard has already checked the complete payload,
        # ignoring append ID/name, evidence order and integral float spelling.
        key = (row['study_id'], row['method_family'], row['quantity'],
               HBN_SCIENTIFIC_PAYLOAD_SHA256[row['quantity']])
        require(key == (mapping['study_id'], mapping['method_family'], mapping['quantity'],
                        mapping['scientific_payload_sha256']), 'Unreviewed source observation')
        groups.setdefault(mapping['source_observation_id'], []).append(row)
    require(bool(groups), 'No reviewed hBN observations selected')
    return groups


def _evidence(items):
    unique = {canonical(item): deepcopy(item) for item in items}
    return [unique[key] for key in sorted(unique)]


def build_projection(observations=None, *, typed_edges=None):
    """Return detached proposed relationships for one or both reviewed quantities.

    Valid catalog aliases remain independently queryable in the core catalog;
    only this view groups them under their reviewed source observation ID.
    """
    review, mappings = _review()
    checked_edges = _checked_edges(typed_edges, review)
    groups = _observation_groups(observations, mappings)
    context_ids = {node['id'] for node in review['nodes']}
    require(not any(row['id'] in context_ids for records in groups.values() for row in records),
            'Catalog observation alias conflicts with a relationship context node')
    edges = [edge for edge in checked_edges
             if edge['predicate'] != 'observed_on' or edge['subject'] in groups]
    for edge in edges:
        edge['evaluation_support'] = 'catalog_only'
    edges.sort(key=lambda edge: edge['id'])
    nodes = []
    for definition in review['nodes']:
        node = deepcopy(definition)
        require(node['kind'] != 'observation', 'Unexpected reviewed observation node')
        node.update(curation='proposed', evaluation_support='catalog_only', properties={},
                    catalog_record_ids=[], catalog_records=[],
                    evidence=_evidence(evidence for edge in edges
                        if node['id'] in (edge['subject'], edge['object']) for evidence in edge['evidence']))
        nodes.append(node)
    aliases = {}
    for source_id, records in sorted(groups.items()):
        records.sort(key=lambda row: (row['id'] != source_id, row['id']))
        representative = records[0]
        mapping = mappings[representative['quantity']]
        catalog_records = [{'id': row['id'], 'sha256': digest(row)} for row in sorted(records, key=lambda r: r['id'])]
        aliases.update((row['id'], source_id) for row in records)
        nodes.append({'id': source_id, 'kind': 'observation',
                      'label': representative['quantity'].replace('_', ' '),
                      'curation': 'proposed', 'evaluation_support': 'catalog_only',
                      'source_observation_identity': deepcopy(mapping),
                      'catalog_record_ids': sorted(row['id'] for row in records),
                      'catalog_records': catalog_records,
                      'properties': {k: deepcopy(v) for k, v in representative.items()
                                     if k not in ('id', 'name', 'evidence')},
                      'evidence': _evidence(representative['evidence'])})
    nodes.sort(key=lambda node: node['id'])
    node_ids = {node['id'] for node in nodes}
    require(len(node_ids) == len(nodes), 'Duplicate projected node')
    require(all(edge['subject'] in node_ids and edge['object'] in node_ids for edge in edges),
            'Dangling projected relationship')
    kinds = Counter(node['kind'] for node in nodes)
    formal = formal_project_catalog()
    counts = {'node_count': len(nodes), 'edge_count': len(edges),
              'proposed_material_count': kinds['material_identity'], 'state_count': kinds['state'],
              'cohort_count': kinds['specimen_cohort'], 'feedstock_count': kinds['feedstock'],
              'unique_source_observation_count': len(groups),
              'catalog_observation_record_count': len(aliases), 'study_count': 1,
              'admitted_delta': 0, 'new_materials': 0, 'new_observations': 0}
    result = {'schema': SCHEMA, 'baseline_commit': review['baseline_commit'],
              'curation': 'proposed', 'evaluation_support': 'catalog_only',
              'review_sha256': REVIEW_SHA256, 'review_scope': review['review_scope'],
              'identity_mapping': deepcopy(review['identity_mapping']),
              'rights_scope': deepcopy(review['rights_scope']),
              'formal_counts': deepcopy(formal['counts']), 'formal_catalog_version': formal['version'],
              'formal_resource_sha256': deepcopy(formal['resource_sha256']), 'counts': counts,
              'nodes': nodes, 'edges': edges, 'observation_aliases': dict(sorted(aliases.items())),
              'limits': ['Proposed source-qualified companion mapping; no formal admission.',
                         'Relationships navigate context only; no property inheritance or scientific equivalence.',
                         'Shared study cohort does not establish individual specimen overlap or independent replication.',
                         'Inherited catalog evidence only; no new primary-source audit, raw data or observations.']}
    result['version'] = digest(result)
    return result


def traverse(projection, node_id, direction='outgoing', max_depth=4):
    """Navigate stored assertions once; preserve their orientation and IDs."""
    require(type(projection) is dict and projection.get('schema') == SCHEMA, 'Invalid projection')
    require(projection.get('version') == digest({k: v for k, v in projection.items() if k != 'version'}),
            'Projection content changed')
    require(_identifier(node_id), 'Invalid node ID')
    require(direction in ('outgoing', 'incoming', 'both'), 'Invalid traversal direction')
    require(type(max_depth) is int and 0 <= max_depth <= MAX_DEPTH, 'Invalid traversal depth')
    nodes = {node['id']: node for node in projection['nodes']}
    resolved = projection['observation_aliases'].get(node_id, node_id)
    require(resolved in nodes, 'Unknown projection node')
    visited, edge_ids, frontier = {resolved}, set(), {resolved}
    for _ in range(max_depth):
        next_frontier = set()
        for edge in projection['edges']:
            targets = []
            if direction in ('outgoing', 'both') and edge['subject'] in frontier:
                targets.append(edge['object'])
            if direction in ('incoming', 'both') and edge['object'] in frontier:
                targets.append(edge['subject'])
            if targets:
                edge_ids.add(edge['id'])
                next_frontier.update(set(targets) - visited)
        visited.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break
    selected_nodes = [node for node in projection['nodes'] if node['id'] in visited]
    selected_edges = [edge for edge in projection['edges'] if edge['id'] in edge_ids]
    return deepcopy({'schema': 'hbn-relationship-traversal/1', 'projection_version': projection['version'],
                     'requested_node_id': node_id, 'resolved_node_id': resolved,
                     'direction': direction, 'max_depth': max_depth,
                     'curation': 'proposed', 'evaluation_support': 'catalog_only',
                     'nodes': selected_nodes, 'edges': selected_edges,
                     'counts': {'visited_node_count': len(selected_nodes), 'visited_edge_count': len(selected_edges),
                                'visited_material_count': sum(n['kind'] == 'material_identity' for n in selected_nodes),
                                'visited_source_observation_count': sum(n['kind'] == 'observation' for n in selected_nodes),
                                'admitted_delta': 0},
                     'formal_counts': projection['formal_counts'], 'property_inheritance': False})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', help='Exact projection node or catalog observation ID')
    parser.add_argument('--direction', choices=('outgoing', 'incoming', 'both'), default='outgoing')
    parser.add_argument('--max-depth', type=int, choices=range(MAX_DEPTH + 1), default=4)
    args = parser.parse_args(argv)
    try:
        projection = build_projection()
        result = traverse(projection, args.node, args.direction, args.max_depth) if args.node else projection
        raw = canonical(result) + b'\n'
        require(len(raw) <= MAX_BYTES, 'Projection output exceeds byte limit')
    except (ValueError, TypeError, KeyError, OSError, RecursionError, UnicodeError):
        print('hBN relationship projection rejected invalid or unavailable input; no report emitted.', file=sys.stderr)
        return 2
    sys.stdout.buffer.write(raw)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
