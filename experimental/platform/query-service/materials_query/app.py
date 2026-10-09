"""Local, read-only candidate query API. No production admission or credentials."""
from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import Literal
import json
from fastapi import HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import Field, field_validator, model_validator
from materials_federation.models import Model, Query, SearchPage, now
from materials_federation.normalize import normalize_mp, normalize_nomad
from materials_federation.providers import NomadAdapter, ProviderError

from . import __version__
from .transport import REQUEST_TIMEOUT_SECONDS, TransportBoundedFastAPI

ROOT = Path(__file__).parent

class SearchRequest(Model):
    provider: Literal['nomad', 'materials_project'] = 'nomad'
    formula: str = Field(min_length=1, max_length=120)
    limit: int = Field(default=5, ge=1, le=25, strict=True)
    evidence_kind: Literal['all', 'computed', 'experimental', 'unknown'] = 'all'
    enrich_first: bool = Field(default=False, strict=True)

    @field_validator('formula')
    @classmethod
    def formula_scope(cls, v):
        if not v.strip() or any(ord(c) < 32 for c in v):
            raise ValueError('Use a nonempty formula without control characters')
        Query(formula=v, limit=1)
        return v.strip()

class BatchRequest(Model):
    queries: list[SearchRequest] = Field(min_length=1, max_length=3)
    @model_validator(mode='after')
    def bound(self):
        if sum(q.limit for q in self.queries) > 25:
            raise ValueError('Batch limit is 25 requested entries across at most 3 queries')
        if any(q.enrich_first for q in self.queries):
            raise ValueError('Batch archive enrichment is disabled; use a single search')
        return self

class DemoRequest(Model):
    provider: Literal['nomad', 'materials_project'] = 'nomad'


def create_app(adapter=None, *, enable_local_catalog=False, computed_registry=None,
               transport_timeout_seconds=REQUEST_TIMEOUT_SECONDS):
    app = TransportBoundedFastAPI(transport_timeout_seconds=transport_timeout_seconds, docs_url=None, redoc_url=None, title='Materials Boundaries · Candidate Query', version=__version__,
                  description='Local review-only discovery. Entries are not admitted materials.')
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', '[::1]', 'testserver'])
    app.mount('/static', StaticFiles(directory=ROOT/'static'), name='static')
    provider = adapter or NomadAdapter()
    snapshots = OrderedDict()
    lock = Lock()

    def remember(c):
        with lock:
            snapshots[c.snapshot_id] = c.model_dump(mode='json')
            snapshots.move_to_end(c.snapshot_id)
            while len(snapshots) > 250 or sum(len(json.dumps(v)) for v in snapshots.values()) > 25_000_000:
                snapshots.popitem(last=False)

    def envelope(page, request, warnings=()):
        data = page.model_dump(mode='json')
        # Selection only: preserve every property and its evidence kind in a selected record.
        def kinds(c):
            return {p.evidence_kind for p in c.properties} or {'unknown'}
        selected = [c for c in page.candidates if request.evidence_kind == 'all' or request.evidence_kind in kinds(c)]
        for c in selected:
            remember(c)
        data['candidates'] = [c.model_dump(mode='json') for c in selected]
        return {'schema_version':'query_service/0.1.0', 'status':'success', 'page':data,
                'selection':{'evidence_kind':request.evidence_kind, 'scope':'returned page only; any matching property; unfiltered properties retained'},
                'counts':{'matching_provider_entries':page.matching_provider_entries,
                    'fetched_entries':len(page.candidates), 'returned_entries':len(selected),
                    'unique_material_count':None, 'admitted_material_count':0, 'quota_credit':0},
                'warnings':list(warnings) + ['Discovery is not exhaustive. Provider totals are entries, not unique materials.',
                    'All candidates remain pending review; export is not a license or admission approval.']}

    def search(req):
        if req.provider == 'materials_project':
            return {'status':'not_configured', 'provider':'materials_project',
                    'message':'No authorized MP client is configured. The separate fixture demo is synthetic.', 'quota_credit':0}
        try:
            page = provider.search(Query(formula=req.formula, limit=req.limit))
            warnings = []
            if req.enrich_first and page.candidates:
                try:
                    enriched = provider.enrich_archive(page.candidates[0])
                    remember(page.candidates[0])
                    warnings.append('First record archive is a separate snapshot; search_snapshot_id=' + page.candidates[0].snapshot_id)
                    page = page.model_copy(update={'candidates':(enriched,) + page.candidates[1:]})
                except (ProviderError, ValueError, TypeError, KeyError, AttributeError):
                    warnings.append('Archive enrichment failed; original search snapshot retained.')
            return envelope(page, req, warnings)
        except (ProviderError, ValueError, TypeError, KeyError, AttributeError):
            return {'status':'provider_error', 'provider':'nomad',
                    'message':'Public upstream read failed or timed out; no result is assumed. No automatic retry.', 'quota_credit':0}

    @app.get('/', include_in_schema=False)
    def ui():
        return FileResponse(ROOT/'static/index.html')

    @app.get('/catalog', include_in_schema=False)
    def catalog_ui():
        return FileResponse(ROOT/'static/catalog.html')

    @app.get('/api/health')
    def health():
        return {'status':'ok', 'service_version':__version__, 'mode':'local_review_only', 'upstream_health':'not_checked'}

    @app.get('/api/capabilities')
    def capabilities():
        return {'providers':{'nomad':'public_read_enabled', 'materials_project':'not_configured'},
                'bounds':{'entries_per_query':25, 'queries_per_batch':3, 'entries_per_batch':25,
                          'concurrent_operations':2, 'upstream_timeout_seconds_per_io_phase':20,
                          'upstream_response_bytes':5000000, 'snapshot_cache_entries':250, 'snapshot_cache_json_characters':25000000},
                'exports':['normalized JSON with original structure, units, and provenance'],
                'evidence_filter':'current returned page, not upstream total; property-level classification',
                'experimental_adapter':'not implemented; unknown is never assumed experimental',
                'raw_provider_payload_export':False, 'production_admission':False,
                'canonical_ids_assigned':False, 'doi_registration':False, 'fixture_demo':'separate endpoint'}

    @app.post('/api/search')
    def single(req: SearchRequest):
        result = search(req)
        code = 503 if result['status']=='not_configured' else 502 if result['status']=='provider_error' else 200
        return JSONResponse(content=result, status_code=code)

    @app.post('/api/batch')
    def batch(req: BatchRequest):
        results = [{'query':q.model_dump(), 'result':search(q)} for q in req.queries]
        success = sum(r['result']['status']=='success' for r in results)
        return {'schema_version':'query_batch/0.1.0', 'status':'success' if success==len(results) else 'partial' if success else 'failed',
                'results':results, 'unique_material_count':None, 'quota_credit':0,
                'warning':'No deduplication, aggregate material count, ML split or training license is inferred.'}

    @app.post('/api/demo')
    def demo(req: DemoRequest):
        mp = req.provider=='materials_project'
        raw = json.loads((ROOT/'fixtures'/('mp_summary.json' if mp else 'nomad_archive_projected.json')).read_text())
        c = normalize_mp(raw, fixture=True) if mp else normalize_nomad(raw, fixture=True)
        query = Query(formula=c.formula, limit=1)
        page = SearchPage(provider=req.provider, query=query, candidates=(c,), retrieved_at=now(),
                          possibly_truncated=False, fixture=True, matching_provider_entries=None)
        return envelope(page, SearchRequest(provider=req.provider, formula=c.formula, limit=1),
                        ['FIXTURE ONLY: synthetic MP or replayed NOMAD; no live provider query occurred.'])

    @app.get('/api/records/{snapshot_id}')
    def record(snapshot_id: str):
        with lock:
            item = snapshots.get(snapshot_id)
        if item is None:
            raise HTTPException(404, 'Snapshot absent or evicted; repeat its bounded query')
        return JSONResponse(content=item, headers={'Content-Disposition':f'attachment; filename="{snapshot_id}.json"'})
    from .local_catalog import install_routes
    install_routes(app, enabled=enable_local_catalog)
    from .computed_catalog import install_routes as install_computed
    install_computed(app, registry=computed_registry)
    return app


def create_catalog_app():
    """Explicit opt-in: one full installed-core snapshot construction per app."""
    return create_app(enable_local_catalog=True)


app = create_app()
