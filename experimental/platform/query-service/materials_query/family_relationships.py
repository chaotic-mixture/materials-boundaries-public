"""Read-only, overlapping views of a validated catalog; never identity admission.

Only explicit catalog categories and a finite reviewed overlay yield assertions.
Unknown means unreviewed/insufficient evidence, never a negative classification.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

POLICY_VERSION = 'material-family-relationships/0.1.0'
CONCEPTS = {
    'metal': 'family', 'alloy': 'family', 'inorganic': 'family',
    'ceramic': 'family', 'polymer': 'family', 'composite': 'family',
    'natural': 'family', 'semiconductor': 'electronic_class',
    'battery': 'application_role', 'catalyst': 'application_role',
    'two_dimensional': 'morphology', 'nanoscale': 'morphology',
}
PRIMARY = frozenset(('metal', 'inorganic', 'polymer', 'composite', 'natural'))
OVERLAY = Path(__file__).with_name('pins') / 'family_relationships.json'
_IMPLEMENTATION_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate relationship overlay key')
        result[key] = value
    return result


def _fields(value, required):
    if type(value) is not dict or set(value) != set(required):
        raise ValueError('Invalid relationship overlay fields')


def _load_overlay():
    overlay = json.loads(OVERLAY.read_bytes(), object_pairs_hook=_unique_pairs)
    _fields(overlay, ('policy_version', 'baseline_commit', 'review_scope', 'memberships', 'relationships'))
    for key in ('policy_version', 'baseline_commit', 'review_scope'):
        if type(overlay[key]) is not str or not overlay[key]:
            raise ValueError('Invalid relationship overlay metadata')
    for key in ('memberships', 'relationships'):
        if type(overlay[key]) is not list:
            raise ValueError('Invalid relationship overlay collection')
        for assertion in overlay[key]:
            fields = ('identity_id', 'identity_sha256', 'field', 'quote')
            fields += (('concept',) if key == 'memberships' else
                       ('target_identity_id', 'target_identity_sha256', 'relation', 'scope'))
            _fields(assertion, fields)
            if any(type(v) is not str or not v for v in assertion.values()):
                raise ValueError('Invalid relationship assertion value')
    return overlay


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class FamilyRelationships:
    """Build once from the already validated historical snapshot, without I/O writes.

    The overlay pins each supporting identity, not just its formula or name. No
    membership propagation, formula classifier, external fetch or negative tags.
    API output is detached; callers cannot mutate the captured graph.
    """
    def __init__(self, snapshot):
        if sha256(Path(__file__).read_bytes()).hexdigest() != _IMPLEMENTATION_SHA256:
            raise ValueError('Relationship implementation changed; restart required')
        overlay = _load_overlay()
        if overlay['policy_version'] != POLICY_VERSION:
            raise ValueError('Relationship policy mismatch')
        identities = {i['id']: snapshot.record('identities', i['id'])
                      for i in snapshot._graph['materials']['identities']}
        rows = {}
        for identity_id, identity in identities.items():
            category = identity['category']
            if category not in PRIMARY:
                raise ValueError('Unsupported catalog category')
            rows[identity_id] = {
                'identity_id': identity_id, 'legacy_category': category,
                'memberships': {}, 'relationships': [],
            }
            rows[identity_id]['memberships'][category] = self._membership(
                identity, category, 'explicit_catalog_category', 'category', category)
        for assertion in overlay['memberships']:
            identity = self._checked_identity(identities, assertion)
            concept = assertion['concept']
            if concept not in CONCEPTS or concept in rows[identity['id']]['memberships']:
                raise ValueError('Invalid or duplicate overlay membership')
            rows[identity['id']]['memberships'][concept] = self._membership(
                identity, concept, 'reviewed_catalog_text', assertion['field'], assertion['quote'])
        relationship_keys = set()
        for assertion in overlay['relationships']:
            identity = self._checked_identity(identities, assertion)
            target = identities[assertion['target_identity_id']]
            if digest(target) != assertion['target_identity_sha256']:
                raise ValueError('Relationship target changed; review required')
            if assertion['relation'] != 'has_constituent':
                raise ValueError('Unsupported identity relationship')
            edge = {'relation': assertion['relation'], 'target_identity_id': target['id'],
                    'status': 'supported', 'scope': assertion['scope'],
                    'evidence': self._evidence(identity, 'reviewed_catalog_text',
                                               assertion['field'], assertion['quote'])}
            key = (identity['id'], edge['relation'], target['id'])
            if key in relationship_keys:
                raise ValueError('Duplicate identity relationship')
            relationship_keys.add(key)
            rows[identity['id']]['relationships'].append(edge)
        for row in rows.values():
            if 'alloy' in row['memberships'] and 'metal' not in row['memberships']:
                raise ValueError('Reviewed alloy must have explicit metal membership')
            row['memberships'] = [row['memberships'].get(concept, {
                'relation': 'member_of', 'concept': concept, 'axis': axis,
                'status': 'unknown', 'evidence': [],
                'reason': 'No reviewed supporting assertion in this policy; not evidence of absence',
            }) for concept, axis in CONCEPTS.items()]
        if sha256(Path(__file__).read_bytes()).hexdigest() != _IMPLEMENTATION_SHA256:
            raise ValueError('Relationship implementation changed during initialization')
        self._rows = rows
        self.catalog_version = snapshot.version
        self.version = digest({'policy': POLICY_VERSION, 'catalog_version': snapshot.version,
            'overlay': overlay, 'implementation_sha256': _IMPLEMENTATION_SHA256})

    @staticmethod
    def _checked_identity(identities, assertion):
        identity = identities[assertion['identity_id']]
        if digest(identity) != assertion['identity_sha256']:
            raise ValueError('Relationship evidence changed; review required')
        if assertion['field'] not in ('name', 'identity_scope'):
            raise ValueError('Unsupported evidence field')
        if not assertion['quote'] or assertion['quote'] not in identity[assertion['field']]:
            raise ValueError('Relationship quote does not match captured identity')
        return identity

    @staticmethod
    def _evidence(identity, basis, field, quote):
        if not identity['evidence']:
            raise ValueError('Relationship requires source-backed identity')
        return [{'basis': basis, 'catalog_record_id': identity['id'],
                 'catalog_field': field, 'catalog_quote': quote,
                 'identity_sha256': digest(identity),
                 'source_id': e['source_id'], 'url': e['url'], 'locator': e['locator'],
                 'scope': 'Inherited catalog evidence; no new source audit or broader material claim'}
                for e in identity['evidence']]

    @classmethod
    def _membership(cls, identity, concept, basis, field, quote):
        return {'relation': 'member_of', 'concept': concept, 'axis': CONCEPTS[concept],
                'status': 'supported', 'evidence': cls._evidence(identity, basis, field, quote)}

    def identity(self, identity_id):
        from materials_boundaries.catalog import CatalogLookupError
        if identity_id not in self._rows:
            raise CatalogLookupError('Unknown material identity')
        return deepcopy(self._rows[identity_id])

    def select(self, concepts, *, match='any', limit=20):
        if (not isinstance(concepts, (list, tuple)) or not concepts
                or any(c not in CONCEPTS for c in concepts)
                or match not in ('any', 'all') or type(limit) is not int or not 1 <= limit <= 100):
            raise ValueError('Invalid relationship selection')
        selected = []
        requested = set(concepts)
        for row in self._rows.values():
            supported = {m['concept'] for m in row['memberships'] if m['status'] == 'supported'}
            if (bool(requested & supported) if match == 'any' else requested <= supported):
                selected.append(row)
        return {'match': match, 'concepts': sorted(requested),
                'matching_unique_identity_count': len(selected),
                'returned_unique_identity_count': min(limit, len(selected)),
                'truncated': len(selected) > limit,
                'records': deepcopy(selected[:limit]),
                'count_scope': 'Unique existing catalog identity IDs; no scientific deduplication across sources'}

    def status(self):
        coverage = {}
        for concept, axis in CONCEPTS.items():
            n = sum(any(m['concept'] == concept and m['status'] == 'supported'
                        for m in r['memberships']) for r in self._rows.values())
            coverage[concept] = {'axis': axis, 'supported': n, 'unknown': len(self._rows) - n}
        return {'policy_version': POLICY_VERSION, 'relationship_version': self.version,
                'catalog_version': self.catalog_version, 'unique_identity_count': len(self._rows),
                'membership_assertion_count': sum(c['supported'] for c in coverage.values()),
                'identity_relationship_count': sum(len(r['relationships']) for r in self._rows.values()),
                'coverage': coverage, 'overlapping_memberships': True,
                'unknown_is_negative': False, 'new_identities_admitted': 0,
                'provider_counts_combined': False,
                'scope': 'Partial reviewed overlay; source-qualified catalog identities only. No original graph restoration.'}
