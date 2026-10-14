# Materials Boundaries · local candidate query service

English-only, isolated first API/UI, 2026-10-08. This package depends on the sibling `federation` package; no adapter implementation is vendored. It does not modify the frozen release or connect to production admission.

## Run locally

Python 3.11+:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install ../federation .
python -m uvicorn materials_query.app:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765. Bind only to loopback. This preview has no user authentication, deployment configuration, persistent database, accounts or credentials. Do not expose it to a network. Browser requests from other origins and untrusted Host headers are rejected. The page uses only local assets and renders provider values as text, not HTML.

Exact direct runtime dependencies are pinned in `pyproject.toml`; transitive dependencies are not yet a reproducible lock. The environment used FastAPI 0.141.1, Pydantic 2.13.4, HTTPX 0.28.1, Uvicorn 0.52.1. Installing this package installs HTTPX's declared SOCKS extra. No new account, key discovery, credential installation or authentication configuration is performed.

## Endpoints

- GET `/api/health`: local liveness, explicitly not upstream health.
- GET `/api/capabilities`: exact feature/resource limits and unsupported capabilities.
- GET `/openapi.json`: machine-readable API schema. External-CDN Swagger/Redoc UIs are disabled to keep the local-only content policy.
- POST `/api/search`: `{ "provider": "nomad", "formula": "CaFe2Re", "limit": 1, "evidence_kind": "all", "enrich_first": false }`.
- POST `/api/batch`: `{ "queries": [{ "formula": "CaFe2Re", "limit": 1 }] }`. At most 3 queries, at most 25 requested entries total. Preserves request/result pairs and explicit success/partial/failed statuses. No enrichment in batches.
- POST `/api/demo`: `{ "provider": "nomad" }` or `{ "provider": "materials_project" }`. Strictly separate fixture route, no upstream call. MP fixture is synthetic; NOMAD is a minimized replay. Neither proves a live connection.
- GET `/api/records/{snapshot_id}`: cached normalized candidate JSON, original structure and field-level provenance included. Cache is process-local and bounded to 250 snapshots / 25 million serialized JSON characters; eviction or restart yields 404. A hash is not an admission token.

Single queries request 1–25 entries from one fixed provider endpoint. Optional first-record archive enrichment adds exactly one request; failure preserves the original search snapshot with a warning. Successful enrichment retains the original search snapshot in the cache and reports its ID. Search totals still describe search entries. NOMAD's provider total is never called a unique-material total. A full returned page is conservatively possibly truncated. Cursors are retained without automatically following them.

MP live search returns 503 `not_configured`; no official client is constructed and no environment key is inspected. A provider failure returns sanitized 502 without assuming results. A partial batch stays HTTP 200 with per-query status; consumers must inspect it. Two simultaneous query operations maximum; excess requests get 429. Upstream reads use the adapter's 20-second timeout **per network I/O phase**, a 5 MB response bound and no retries or redirects. This is not a strict end-to-end wall-clock deadline; batch reads are sequential. Request bodies are limited to 32 KiB. This is a local preview, not hardened multiuser service.

## Batch / ML consumption

```sh
python -m materials_query.client example-batch.json --output candidate-batch.json
```

The included example intentionally combines public NOMAD with unavailable MP to show partial results. The client accepts a local port only, validates bounds before sending, and writes the complete JSON envelope. It does not flatten incompatible quantities into a training matrix. Null uncertainty/state remains null; computed/experimental/unknown classification is property-level. No unit conversion, featurization, deduplication, dataset splitting or license approval occurs. JSON was chosen over lossy CSV for this first release. A production ML export needs a separately reviewed versioned feature contract and reuse rights.

## Scientific and provenance boundaries

Every candidate has `canonical_material_id=null`, `review_status=pending_review`, `quota_credit=0`. Counts separately expose provider matching entries, fetched entries, displayed entries, unknown unique-material count, and zero admitted materials. Candidates can represent duplicate calculations or provider groupings. Formula equality never merges identities.

Filters select candidates with any matching property evidence in the returned page and retain all properties of those candidates. A candidate with no mapped properties is unknown for this selection. The upstream total is unfiltered. The UI explicitly says that experimental ingestion is not implemented; unknown method never becomes experimental. Calculated density does not become experimental from a database linkage.

The normalized candidate preserves original native structure representations and units (NOMAD built-in structure coordinates in metres and density kg/m³, MP properties in their mapped source units). Search structures may be partial. License declarations, retrieval time, raw payload digest, source ID/URL and field paths are exported; a source-declared license does not establish a redistribution review. The complete raw upstream response is **not** retained/exported by this API; its hash alone cannot reconstruct it. Use the separate lifecycle workflow when immutable raw capture is required. No CIF, ontology conformance, AiiDA plugin, DOI registration, qualified-material quota change, or public publication is claimed.

## Verification

```sh
python -m unittest discover -s tests -v
# Optional real browser test against a running local server:
python tests/browser_smoke.py
```

See the parent README for verified and blocked stages. Tests use deterministic HTTPX mock transport except the separately saved bounded live smoke. The sibling federation package preserves the prototype's 19 tests; API tests cover boundaries, provenance, fixture/live separation, failure/partial behavior, filtering, origin/host handling, exports, UI assets and schema. UI browser automation is provided separately and is not counted as passed unless an actual browser run succeeds. Nothing was pushed, deployed or publicly hosted.

## Optional local catalog

The default app remains provider-only. The explicit `materials_query.app:create_catalog_app --factory` startup captures and validates this repository's locally installed core once. See `../LOCAL_CATALOG.md` for local-only installation, pinned read-only API contracts and the separate `/catalog` page. No core package is automatically fetched and no local/external counts are summed. Browser rendering remains unverified.

## Local NBS review candidate, 2026-10-14

This experimental branch contains a proposed addition of three source-qualified
NBS identities (LiF, KCl and CaF2), each with one crystallographic-density
reference. Its candidate snapshot contains 1084 entries: 1060 source-qualified
identities plus the unchanged 24 reviewed computed compositions. Candidate core
inorganic coverage is 19; the proposed combined inorganic count is 31.

The main baseline remains 1081 entries: 1057 source-qualified identities plus
24 reviewed computed compositions. Its combined inorganic count is 28. The
proposed 1084 snapshot is awaiting review and is not an approved formal release. In this
branch, the API field `formal_project_admission_count` still reports the candidate
total 1084; the field name and proposed resource pins do not confer formal
admission. Nb is outside this candidate. The 62 second-tranche examples and the
two held NOMAD overlay candidates remain excluded from both totals.

The query UI reads the proposed counts from the captured candidate catalog.
Its relationship view has 1065 supported memberships across 1060 identities and
still one identity relationship; each new NBS identity contributes only its explicit
inorganic membership. Unknown classifications remain unknown.

The computed registry pins the complete installed core manifest, including the
two appended catalog resources. Its new canonical baseline anchor is
`586b973ccf35a8e7050a9296ec5a241c138549d0decac85de619a6dbd23b2452`.
A registry created against the earlier 1057-identity baseline is rejected in
this installation. There is no automatic migration or old-anchor fallback.
Keep existing databases with their original installation; use a distinct new
local registry when explicitly exercising this baseline. Reviews, input-file
pins and admission decisions remain independent of the catalog baseline.
This integration neither opens existing user databases nor changes frozen
computed review files.

The focused baseline tests use temporary synthetic databases and verify old
anchor rejection, unchanged database bytes, portable manifest path spelling,
and rejection of changed catalog content even when identity counts match:

```sh
python -m unittest discover -s catalog-tests -p test_catalog_baseline.py -v
```

Catalog contract and API tests additionally cover the three exact NBS states,
source reuse, reported density units and temperatures, unknown uncertainty,
and the boundary between the proposed catalog snapshot and computed examples.
The source-derived values are catalog references; scientific validation and
engineering-allowable status remain false. This local experimental candidate
awaits review; no public deployment or DOI registration is included.
