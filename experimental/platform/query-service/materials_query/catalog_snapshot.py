"""Opt-in, in-process prototype. Does not replace any package entry point.

A snapshot is historical captured content, never a claim of current file state.
Changing validator code requires a process restart. No persisted validation cache.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from threading import RLock
from types import MappingProxyType
import json

from materials_boundaries import material_references as contracts
from materials_boundaries.catalog import CatalogLookupError
from materials_boundaries.validation import _unique_pairs, _reject_constant, _strict_float, _strict_int

FORMAT_VERSION = "validated-catalog-snapshot-prototype/1"
PACKAGE_ROOT = Path(contracts.__file__).resolve().parent


def _runtime_manifest():
    # Deliberately conservative: includes every Python and JSON package resource,
    # including schemas, taxonomy and conventions. Not path/mtime based.
    return tuple((str(p.relative_to(PACKAGE_ROOT)), sha256(p.read_bytes()).hexdigest())
                 for p in sorted(PACKAGE_ROOT.rglob('*'))
                 if p.is_file() and p.suffix in {'.py', '.json'})


_RUNTIME_MANIFEST = _runtime_manifest()
RUNTIME_DIGEST = sha256(json.dumps((_RUNTIME_MANIFEST, sha256(Path(__file__).read_bytes()).hexdigest()), separators=(',', ':')).encode()).hexdigest()


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _copy(value):
    if isinstance(value, Mapping):
        return {k: _copy(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_copy(v) for v in value]
    return value


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':')).encode('utf-8')


def _parse(raw):
    return json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant,
                      parse_float=_strict_float, parse_int=_strict_int)


def _id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('record_id must be a nonempty string')


def _evidence_sources(value):
    if isinstance(value, Mapping):
        if 'source_id' in value:
            yield value['source_id']
        for child in value.values():
            yield from _evidence_sources(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _evidence_sources(child)


@dataclass(frozen=True, slots=True, init=False)
class CatalogSnapshot:
    version: str
    content_digest: str
    runtime_digest: str
    _graph: object
    _indexes: object
    _search: object
    _resolved_sources: object

    def __init__(self, materials, properties, sources):
        # Own inputs without JSON-coercing invalid tuples/keys into valid shapes.
        # Caller must not concurrently mutate during this initial capture.
        graph = deepcopy({'materials': materials, 'reference_properties': properties, 'sources': sources})
        if _runtime_manifest() != _RUNTIME_MANIFEST:
            raise RuntimeError('Package resources changed; restart with a coherent package before building')
        # Preserve loader-level source contracts as well as graph validation.
        # No historical ledger audit is introduced; these are the existing
        # read_catalog('sources') checks used by the current exact-query path.
        from materials_boundaries._pa12_cf15_observation_contract import validate_pa12_sources
        from materials_boundaries._paht_cf_observation_contract import validate_paht_sources
        validate_pa12_sources(graph['sources']['records'])
        validate_paht_sources(graph['sources']['records'])
        contracts.validate_material_catalog(graph['materials'], graph['reference_properties'], graph['sources'])
        if _runtime_manifest() != _RUNTIME_MANIFEST:
            raise RuntimeError('Package resources changed during validation; snapshot rejected')
        raw = _canonical(graph)
        # Enforce plain JSON ownership after the original validator accepted the
        # actual captured Python shapes; no custom mutable objects can survive.
        graph = _parse(raw)
        digest = sha256(raw).hexdigest()
        version = sha256(_canonical([FORMAT_VERSION, RUNTIME_DIGEST, digest])).hexdigest()
        graph = _freeze(graph)
        mats, props, src = (graph[k] for k in ('materials', 'reference_properties', 'sources'))
        indexes = {'identities': {x['id']: x for x in mats['identities']},
                   'grades': {x['id']: x for x in mats['grades']},
                   'materials': {x['id']: x for x in mats['records']},
                   'reference-properties': {x['id']: x for x in props['records']},
                   'sources': {x['id']: x for x in src['records']}}
        sources_by_state = {}
        search = {'materials': {}, 'reference-properties': {}}
        for state in mats['records']:
            identity = indexes['identities'][state['identity_id']]
            grade = indexes['grades'].get(state['grade_id'])
            linked = [indexes['reference-properties'][pid] for pid in state['property_ids']]
            referenced = set(_evidence_sources([identity, grade, state, linked]))
            sources_by_state[state['id']] = tuple(s['id'] for s in src['records'] if s['id'] in referenced)
            fields = [state['id'], state.get('name', ''), state.get('names', {}).get('en', ''),
                      identity['id'], identity.get('name', ''), identity.get('names', {}).get('en', ''),
                      identity['category'], state['source_designation']]
            if grade:
                fields += [grade['id'], grade['designation']]
            # Deliberately bounded documented fields, not a full CLI search clone.
            def property_fields(prop):
                return [prop[k] for k in ('id', 'material_state_id', 'quantity', 'source_id',
                                         'source_property_label', 'evidence_kind', 'reporting_basis')]
            search['materials'][state['id']] = tuple(f.casefold() for f in fields + [f for p in linked for f in property_fields(p)])
            for prop in linked:
                search['reference-properties'][prop['id']] = tuple(f.casefold() for f in fields + property_fields(prop))
        for key, value in {'version': version, 'content_digest': digest, 'runtime_digest': RUNTIME_DIGEST,
                           '_graph': graph, '_indexes': _freeze(indexes), '_search': _freeze(search),
                           '_resolved_sources': _freeze(sources_by_state)}.items():
            object.__setattr__(self, key, value)

    @classmethod
    def from_json_bytes(cls, materials: bytes, properties: bytes, sources: bytes):
        """Parse the exact captured buffers; duplicate keys/nonfinite numbers rejected."""
        return cls(*(_parse(raw) for raw in (materials, properties, sources)))

    @classmethod
    def from_packaged(cls):
        """Capture three package files once, then validate captured content.

        Caller must use a quiescent, coherent installed package. Multi-file atomic
        filesystem capture is not promised. No source rereads occur in queries.
        """
        raw = [(PACKAGE_ROOT / 'data' / (name + '.json')).read_bytes()
               for name in ('materials', 'reference_properties', 'sources')]
        return cls.from_json_bytes(*raw)

    def record(self, kind, record_id):
        """Exact identity, grade, material state, property or source; detached copy."""
        _id(record_id)
        if kind not in self._indexes:
            raise ValueError('unsupported record kind: ' + str(kind))
        try:
            return _copy(self._indexes[kind][record_id])
        except KeyError:
            raise CatalogLookupError(f'unknown {kind} ID: {record_id}') from None

    def query_exact(self, kind, record_id):
        """Canonical exact-ID subset, equal to query_catalog for these two kinds."""
        if kind not in ('materials', 'reference-properties'):
            raise ValueError('exact catalog query supports materials or reference-properties')
        record = self.record(kind, record_id)
        raw = self._graph['materials' if kind == 'materials' else 'reference_properties']
        out = {key: _copy(value) for key, value in raw.items() if key not in ('records', 'identities', 'grades')}
        out['records'] = [record]
        if kind == 'materials':
            out['identities'] = [self.record('identities', record['identity_id'])]
            out['grades'] = [] if record['grade_id'] is None else [self.record('grades', record['grade_id'])]
        return out

    def resolve(self, state_id):
        """Source-complete result with the existing resolve_material shape."""
        state = self.record('materials', state_id)
        return {'schema_version': '1.0.0', 'identity': self.record('identities', state['identity_id']),
                'grade': None if state['grade_id'] is None else self.record('grades', state['grade_id']),
                'state': state, 'properties': [self.record('reference-properties', pid) for pid in state['property_ids']],
                'sources': [self.record('sources', sid) for sid in self._resolved_sources[state_id]]}

    def search_english(self, kind, query, *, limit=20):
        """Literal AND substring search. O(N); bounded input/output, packaged order."""
        if kind not in self._search:
            raise ValueError('search supports materials or reference-properties')
        if not isinstance(query, str) or not query.strip() or len(query) > 256:
            raise ValueError('query must contain 1 to 256 characters')
        terms = query.casefold().split()
        if len(terms) > 16:
            raise ValueError('at most 16 terms')
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('limit must be an integer from 1 to 100')
        ids = []
        # Iterate the original records index; property_ids may have different order.
        for rid in self._indexes[kind]:
            fields = self._search[kind][rid]
            if all(any(term in field for field in fields) for term in terms):
                ids.append(rid)
                if len(ids) > limit:
                    break
        return {'version': self.version, 'records': [self.record(kind, rid) for rid in ids[:limit]],
                'truncated': len(ids) > limit}


@dataclass(frozen=True, slots=True)
class Selection:
    version: str
    kind: str
    record_id: str


class LatestCatalog:
    """Latest explicitly validated refresh, NOT automatically latest disk bytes.

    Failed refresh leaves the prior good historical snapshot usable. Refresh does
    full validation even when content is unchanged; no global acceptance cache.
    """
    def __init__(self, snapshot):
        if type(snapshot) is not CatalogSnapshot:
            raise TypeError('expected a CatalogSnapshot')
        self._current = snapshot
        self._lock = RLock()

    @property
    def current(self):
        with self._lock:
            return self._current

    def refresh(self, materials, properties, sources):
        with self._lock:
            new = CatalogSnapshot(materials, properties, sources)
            self._current = new
            return new

    def select(self, kind, record_id):
        with self._lock:
            self._current.record(kind, record_id)
            return Selection(self._current.version, kind, record_id)

    def read_selected(self, selection):
        with self._lock:
            if selection.version != self._current.version:
                raise ValueError('stale selection: select again against the refreshed version')
            return self._current.record(selection.kind, selection.record_id)
