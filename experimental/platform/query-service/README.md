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

## Local source-qualified increment, 2026-10-17

The experiment retains the eighteen earlier source-qualified additions and adds
one distinct NC2 concrete formulation with a nominal 28-day water-saturated
density mean of 2340 kg/m3. Its snapshot contains 1100 entries: 1076
source-qualified identities plus the unchanged 24 reviewed computed compositions.
Core counts are natural 1010, metal 22, inorganic 26, polymer 14 and composite 4;
project counts are natural 1010, metal 34, inorganic 38, polymer 14 and composite 4.
See [the incremental record](../../../docs/MATERIAL_GROWTH_NC2_20261017.md).

Main remains at 1081 entries: 1057 source-qualified identities plus 24 reviewed
computed compositions. In this experimental installation the existing API field
`formal_project_admission_count` reports 1100; its name and resource pins do not
publish a main release. The 62 unadmitted examples and held NOMAD candidates
remain excluded. NC2 reuses the existing article-specific CC BY 4.0 source after
selected-table, preparation and license checks. Scientific-review and
raw-reanalysis flags remain false. The PA2200 lead is held for inconsistent
reported modulus statistics and contributes zero identities. Main release, DOI
registration and public deployment remain deferred.

The query UI reads counts from the captured catalog. Its relationship view has
1081 supported memberships across 1076 identities and one identity relationship;
NC2 contributes only its existing primary-class membership. Unknown
classifications remain unknown. No browser rendering test is claimed here.

The computed registry pins the complete installed core manifest, including the
two newly appended catalog resources; the source registry is unchanged. Its
canonical baseline anchor is
`a38937d66a5d6c8f99eae6c05747e60a90f7647a737a1dc4d1cebc983fafcca3`.
Registries from earlier baselines are rejected, including the immediate eaf
anchor `8da7a2000110021ad0a20b2a83dc1b02420a0bf9e3d1b68eb71b70f127965efe`.
There is no automatic migration or old-anchor fallback; retain each database
with its original installation and use a distinct local registry for this
snapshot. Review and input pins remain separate from the catalog baseline.
Frozen computed reviews are unchanged.

Focused tests retain all earlier anchor-rejection cases and add the immediate
predecessor, unchanged database bytes, portable manifest paths and rejection of
content drift even when identity counts match:

```sh
python -m unittest discover -s catalog-tests -p test_catalog_baseline.py -v
```

The increment additionally checks frozen candidate payloads, source reuse,
per-property units and unknowns, exact predecessor-byte recovery, full graph
validation and idempotent offline CLI replay. Actual focused test results are
retained in the delivery evidence; a full-suite rerun is not claimed here.
