"""Opt-in installed-core boundary. Never installs, refreshes or writes source data."""
from importlib.util import find_spec
from typing import Literal
from threading import BoundedSemaphore
from fastapi import HTTPException
from pydantic import Field
from materials_federation.models import Model

Kind = Literal['materials', 'reference-properties']
RecordKind = Literal['identities', 'grades', 'materials', 'reference-properties', 'sources']

class Pinned(Model):
    version: str = Field(pattern=r'^[0-9a-f]{64}$')

class RelationshipPinned(Pinned):
    relationship_version: str = Field(pattern=r'^[0-9a-f]{64}$')

class RelationshipIdentityRequest(RelationshipPinned):
    identity_id: str = Field(min_length=1, max_length=512)

class RelationshipSearchRequest(RelationshipPinned):
    concepts: list[Literal['metal', 'alloy', 'inorganic', 'ceramic', 'polymer',
        'composite', 'natural', 'semiconductor', 'battery', 'catalyst',
        'two_dimensional', 'nanoscale']] = Field(min_length=1, max_length=12)
    match: Literal['any', 'all'] = 'any'
    limit: int = Field(default=20, ge=1, le=100, strict=True)

class ExactRequest(Pinned):
    kind: Kind
    record_id: str = Field(min_length=1, max_length=512)

class RecordRequest(Pinned):
    kind: RecordKind
    record_id: str = Field(min_length=1, max_length=512)

class ResolveRequest(Pinned):
    state_id: str = Field(min_length=1, max_length=512)

class CatalogSearch(Pinned):
    kind: Kind = 'materials'
    query: str = Field(min_length=1, max_length=256)
    limit: int = Field(default=20, ge=1, le=100, strict=True)


def load_installed_snapshot():
    # Absence is handled without importing anything from a package index.
    try:
        if find_spec('materials_boundaries') is None:
            return None, 'core_not_installed'
        from .catalog_snapshot import CatalogSnapshot
        return CatalogSnapshot.from_packaged(), None
    except Exception:
        # Fail closed; no arbitrary source paths or potentially sensitive traces
        # are reflected over HTTP. Correct the installation, then restart.
        return None, 'core_initialization_failed'


def install_routes(app, *, enabled=False):
    snapshot, error = load_installed_snapshot() if enabled else (None, 'not_enabled')
    # Plain detached metadata, computed once from the successfully validated graph.
    metadata = {'enabled': snapshot is not None, 'reason': error,
        'version': None, 'content_digest': None, 'runtime_digest': None,
        'counts': None, 'freshness': 'historical process pin; restart to capture installed content',
        'search': 'English literal casefolded AND substring; bounded fields; not full CLI equivalence',
        'bounds': {'query_characters':256, 'query_terms':16, 'returned_records':100, 'concurrent_operations':2},
        'provider_counts_combined': False, 'source_mutation':False, 'automatic_refresh':False}
    if snapshot is not None:
        graph = snapshot._graph
        metadata.update(version=snapshot.version, content_digest=snapshot.content_digest,
            runtime_digest=snapshot.runtime_digest,
            counts={'local_catalog_unique_material_count':len(graph['materials']['identities']),
                    'local_material_state_count':len(graph['materials']['records']),
                    'local_reference_property_count':len(graph['reference_properties']['records'])})

    from .formal_catalog import install_routes as install_formal
    install_formal(app, enabled=snapshot is not None)

    def ready(version):
        if snapshot is None:
            raise HTTPException(503, 'Local catalog disabled: ' + error + '. Install this repository core locally and restart the opt-in factory.')
        if version != snapshot.version:
            raise HTTPException(409, 'Catalog version differs; inspect status and select against the current pin')
        return snapshot

    slots = BoundedSemaphore(2)

    def result(version, operation):
        current = ready(version)
        from materials_boundaries.catalog import CatalogLookupError
        if not slots.acquire(blocking=False):
            raise HTTPException(429, 'Two local catalog operations are active; retry later')
        try:
            return {'version':current.version, 'content_digest':current.content_digest,
                    'runtime_digest':current.runtime_digest, 'result':operation(current)}
        except CatalogLookupError:
            raise HTTPException(404, 'Unknown local catalog record') from None
        except ValueError:
            raise HTTPException(400, 'Invalid local catalog query') from None
        finally:
            slots.release()

    @app.get('/api/catalog/status')
    def status():
        from copy import deepcopy
        return deepcopy(metadata)

    @app.post('/api/catalog/exact')
    def exact(req: ExactRequest):
        return result(req.version, lambda s:s.query_exact(req.kind, req.record_id))

    @app.post('/api/catalog/record')
    def record(req: RecordRequest):
        return result(req.version, lambda s:s.record(req.kind, req.record_id))

    @app.post('/api/catalog/resolve')
    def resolve(req: ResolveRequest):
        return result(req.version, lambda s:s.resolve(req.state_id))

    @app.post('/api/catalog/search')
    def search(req: CatalogSearch):
        return result(req.version, lambda s:s.search_english(req.kind, req.query, limit=req.limit))

    # This additive view shares the validated catalog and its concurrency guard.
    # Overlay drift disables this view only; established catalog APIs survive.
    relationships = None
    relationship_error = error
    if snapshot is not None:
        try:
            from .family_relationships import FamilyRelationships
            relationships = FamilyRelationships(snapshot)
            relationship_error = None
        except Exception:
            relationship_error = 'relationship_initialization_failed'

    @app.get('/api/catalog/relationships/status')
    def relationship_status():
        data = {'enabled': relationships is not None, 'reason': relationship_error}
        if relationships is not None:
            data.update(relationships.status())
        return data

    def relationship_result(req, operation):
        def query(current):
            if relationships is None:
                raise HTTPException(503, 'Material relationships unavailable: ' + relationship_error)
            if req.relationship_version != relationships.version:
                raise HTTPException(409, 'Relationship version differs; inspect relationship status')
            return {'relationship_version': relationships.version, 'data': operation(relationships)}
        return result(req.version, query)

    @app.post('/api/catalog/relationships/identity')
    def relationship_identity(req: RelationshipIdentityRequest):
        return relationship_result(req, lambda r: r.identity(req.identity_id))

    @app.post('/api/catalog/relationships/search')
    def relationship_search(req: RelationshipSearchRequest):
        return relationship_result(req, lambda r: r.select(req.concepts, match=req.match, limit=req.limit))
