"""Explicit read-only computed namespace; process-pinned overlay, no filesystem HTTP."""
from copy import deepcopy
from typing import Literal
from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import Field
from materials_federation.models import Model
from .computed_registry import canonical, MAX_EXPORT_BYTES

class Pin(Model):
    namespace: Literal['computed']
    baseline_version: str = Field(pattern=r'^[0-9a-f]{64}$')
    overlay_version: str = Field(pattern=r'^[0-9a-f]{64}$')
    review_version: str = Field(pattern=r'^[0-9a-f]{64}$')

class Selection(Pin):
    offset: int = Field(default=0, ge=0, le=1000, strict=True)
    limit: int = Field(default=20, ge=1, le=100, strict=True)

class Search(Selection):
    query: str = Field(min_length=1, max_length=256)

class Exact(Pin):
    project_material_id: str = Field(min_length=1, max_length=160)

class Property(Exact):
    property: Literal['density']


def install_routes(app, *, registry=None):
    # Capture once. A restart is necessary after local admission; no refresh route.
    snapshot = registry.snapshot() if registry is not None else None
    pins = ('baseline_version', 'overlay_version', 'review_version')

    def ready(req):
        if snapshot is None:
            raise HTTPException(503, 'Computed registry is not enabled')
        if any(getattr(req, k) != snapshot[k] for k in pins):
            raise HTTPException(409, 'Computed baseline, overlay or review version differs')
        return snapshot

    def envelope(req, records):
        s = ready(req)
        return {'namespace':'computed', **{k:s[k] for k in pins}, **({k:deepcopy(s[k]) for k in ('schema','count_policy','input_file_sha256','canonical_review_sha256')} if s['schema'] == 'computed-overlay/2' else {}), 'records':deepcopy(records)}

    def exact_records(req):
        records = [r for r in ready(req)['records'] if r['project_material_id'] == req.project_material_id]
        if not records:
            raise HTTPException(404, 'Unknown computed project material')
        return records

    @app.get('/api/computed/status')
    def status():
        if snapshot is None:
            return {'enabled':False, 'namespace':'computed', 'reason':'not_enabled'}
        return {k:deepcopy(v) for k,v in snapshot.items() if k != 'records'} | {
            'enabled':True, 'freshness':'process pin; restart after local admission',
            'http_admission':False, 'arbitrary_paths':False, 'refresh':False,
            'bounds':{'query_characters':256, 'query_terms':16, 'returned_records':100, 'export_bytes':MAX_EXPORT_BYTES}}

    @app.post('/api/computed/list')
    def listing(req: Selection):
        s = ready(req)
        return envelope(req, s['records'][req.offset:req.offset+req.limit])

    @app.post('/api/computed/search')
    def search(req: Search):
        terms = req.query.casefold().split()
        if not terms or len(terms) > 16 or any(ord(c)<32 for c in req.query):
            raise HTTPException(400, 'Use 1–16 English literal search terms without controls')
        records = [r for r in ready(req)['records'] if all(t in ' '.join(r[k] if isinstance(r[k], str) else canonical(r[k]).decode() for k in
                   ('formula','project_material_id','provider_entry_id','provider_material_id','method')).casefold() for t in terms)]
        return envelope(req, records[req.offset:req.offset+req.limit])

    @app.post('/api/computed/exact')
    def exact(req: Exact):
        return envelope(req, exact_records(req))

    def project(r, kind):
        # Rich records stay whole in both projections: method and scalar values
        # cannot become detached from scope, unknowns, rights or overlap caveats.
        if snapshot['schema'] == 'computed-overlay/2':
            return deepcopy(r)
        keys = ('candidate_id','project_material_id','density','source_url','attribution','method','reason','rights') if kind == 'property' else (
            'candidate_id','provider','provider_entry_id','provider_material_id','source_url','attribution','rights','reason')
        return {k:deepcopy(r[k]) for k in keys}

    @app.post('/api/computed/property')
    def property_record(req: Property):
        return envelope(req, [project(r, 'property') for r in exact_records(req)])

    @app.post('/api/computed/source')
    def source(req: Exact):
        return envelope(req, [project(r, 'source') for r in exact_records(req)])

    @app.post('/api/computed/export')
    def export(req: Pin):
        raw = canonical(ready(req))
        return Response(raw, media_type='application/json', headers={'Content-Disposition':'attachment; filename="computed-overlay-recovery.json"'})
