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

The experiment extends the NC2 snapshot by one SPO-2 rigid PUR foam and two
PBS/lignin simple-blend formulations B10/B30. It contains 1103 project entries:
1079 source-qualified identities plus the unchanged 24 reviewed computed
compositions. Core categories are natural 1010, metal 22, inorganic 26, polymer
15 and composite 6; project categories are natural 1010, metal 34, inorganic 38,
polymer 15 and composite 6. See [the incremental record](../../../docs/MATERIAL_GROWTH_FORMULATIONS_20261017.md).

This is one lineage from 1100 to 1103. Main remains 1081 = 1057 + 24, and the
62 unadmitted examples and held NOMAD candidates remain excluded. The existing
API field `formal_project_admission_count` describes the installed experimental
snapshot; it does not publish a main release. New facts retain source-specific
CC BY 4.0 attribution, unknown conditions and false scientific-review and
raw-reanalysis flags. SPO-1, PA2200 and other unselected leads contribute zero.
Main release, DOI registration and public deployment remain deferred.

The relationship view retains its original reviewed overlay and one identity
relationship. Its 1079 identities have 1084 supported memberships. The three
new identities contribute their primary categories only; the new blends do
not automatically acquire additional polymer memberships or constituent edges.
The UI reads captured catalog counts. Browser rendering was not tested here.

The computed registry pins the complete installed core manifest. Its canonical
baseline anchor is recorded in the integration review and packaged manifest.
Earlier baselines, including the immediate NC2 anchor
`a38937d66a5d6c8f99eae6c05747e60a90f7647a737a1dc4d1cebc983fafcca3`,
are rejected. Keep old databases with their original installation and use a
separate registry for this snapshot; no automatic migration, fallback or
database rewrite is provided. Source registry and frozen computed reviews
remain unchanged. Review/input pins remain separate from catalog baseline pins.

Focused tests retain the earlier anchor-rejection cases and add the NC2
predecessor while checking unchanged database bytes, portable manifest paths
and rejection of content drift even when counts match:

```sh
python -m unittest discover -s catalog-tests -p test_catalog_baseline.py -v
```

The increment also checks source-qualified values and unknowns, complete graph
validation, exact predecessor recovery, idempotent CLI replay and installed
package/API behavior. Actual test outcomes are retained in delivery evidence;
no additional full-suite, browser or completed remote-CI run is implied.

## Local composite increment, 2026-10-19

The preceding experiment added the source-qualified PBS/lignin B45 formulation and
EPDM_H_P20/P40/P60 composites. That snapshot contained 1107 project
entries: 1083 source-qualified identities plus the unchanged 24 reviewed
computed compositions. Core categories are natural 1010, metal 22, inorganic
26, polymer 15 and composite 10; project categories are natural 1010, metal 34,
inorganic 38, polymer 15 and composite 10. See the
[B45 packet](../../material-batches/20261019-pbs-lignin45/README.md),
[EPDM packet](../../material-batches/20261019-epdm-pcm-hostatron/README.md) and
[integration manifest](../../material-batches/20261019-polymer-composites-incremental/integration.json).
Both packets reuse registered sources; the source registry remains unchanged.
The relationship overlay remains unchanged: 1083 identities have 1088 supported
memberships and one identity relationship. The four composites contribute
their primary category only; additional polymer memberships or constituent
edges require separate evidence and review.

That snapshot's complete core manifest anchor is
`3782f403f120f22b5287e01f4e207419e2f576a28dfda33a89a85580b936c0f6`.
The preceding a592 catalog anchor
`f1a1e3e379f9b7befba595b54477f15a26364548798b28dd65be8bc4326c0df4`
and earlier data anchors remain historical. Keep their databases with their
original installation and initialize a separate registry for this snapshot.
Compatibility checks recover the exact a592 catalog bytes and its complete
64-file logical manifest before recovering the earlier released catalog;
production does not accept the preceding data anchor or migrate old databases.
The existing exact code-only successor rules remain unchanged.

This local experiment does not change the released main total of 1081, admit
the 62 excluded computed examples, fetch raw assets, publish a release, register
a DOI or deploy a service. Candidate review records retain their explicit
scientific-review and raw-reanalysis limitations. Targeted test outcomes belong
to this batch's validation evidence; no new full-suite or browser pass is implied.

## Source-family packet increment, 2026-10-19

The preceding experiment added one EOS PA2200 source-qualified PA12 identity with
one source-designated grade, processed reference state, tensile-strength property
and source. The packet does not count another supplier label as a second PA12
identity. See the [source-family packet](../../material-batches/20261019-pa12-source-family/README.md).
That snapshot contained **1108 project entries = 1084 source-qualified
identities + 24 reviewed computed compositions**. Core categories are natural
1010, metal 22, inorganic 26, polymer 16 and composite 10; project categories
are natural 1010, metal 34, inorganic 38, polymer 16 and composite 10. The
relationship view has 1084 identities, 1089 supported memberships (including
17 polymer memberships) and the same one identity relationship. Memberships
are overlapping evidence and do not add identities.

That complete core manifest anchor is
`8fda4f7a4355c88f0e4e9e713c01f236a907985b4720454e338d8d95eff4770e`.
The preceding `3782f403f120f22b5287e01f4e207419e2f576a28dfda33a89a85580b936c0f6`
anchor remains historical. Compatibility checks bind the immutable prepared
packet, remove only its complete unchanged append graph, and recover the exact
12cb predecessor resources and 64-file manifest before the older a592/main
recovery chain. Partial additions, modified rows and unrelated resource edits
are refused. Keep old databases with their original installation and create a
separate registry for this snapshot; no automatic migration is provided.

The local API resolves the single PA2200 identity with the selected 43.72 MPa
tensile strength, its reported 1.03 MPa standard deviation and six-specimen
scope. The value remains catalog-only with unknown tensile-test temperature,
independent scientific review false and raw-data reanalysis false. Released
main remains at 1081; the 62 excluded computed examples remain excluded.

## Six-oxide source-family growth, 2026-10-19

The preceding six-oxide snapshot contained **1114 project entries = 1090 source-qualified
identities + 24 reviewed computed compositions** after six NBS oxide references:
BeO, MgO, CaO, rutile TiO2, CuO and CeO2. Core categories are natural 1010,
metal 22, inorganic 32, polymer 16 and composite 10; project categories are
natural 1010, metal 34, inorganic 44, polymer 16 and composite 10. The relationship
view has 1090 identities and 1095 supported memberships, with 32 inorganic
memberships and the same one identity relationship. Memberships overlap and do
not create identities. There are 1090 reference states and properties, 21 grades
and 116 sources; the six records reuse an existing source.

The exact query manifest anchor is
`0d2f515260b78841249f5b48331f8a80fc9164bd58bb57c592f7adfed3d96277`,
bound to data commit `bc7bdeeff498c4186cdf86c33e88943c45ecfc75`.
The independent query test reads the frozen six-oxide ledger and packet, removes
only the 6 identities, 6 states and 6 properties listed as additions, and recovers
the exact c901 resources and 64-file manifest before the PA12-to-12cb and older
historical chain. Shared source rows and all grades are retained. Partial,
modified, duplicated or reordered additions and unrelated edits are rejected.
Old pins and databases are not rewritten or migrated.

Each API result preserves one source-reported measured-lattice-derived density,
its exact g/cm^3 value and temperature, unknown uncertainty and specimen count,
and catalog-only scope. It is neither a direct bulk-density measurement nor a
DFT prediction, experimental replication or independent scientific review.
See the [six-oxide packet](../../material-batches/nbs-oxide-density-20261019/README.md).
Released main and the 62 excluded computed examples remain unchanged. Validation
is reported in the batch evidence; this section does not claim a new full-suite,
live-provider or browser run.

## Bounded PUR formulation increment, 2026-10-19

The preceding PUR snapshot contained **1116 project entries = 1092 source-qualified
identities + 24 reviewed computed compositions**. The two new polymer identities
are the source-defined LPO-2 and SPO-3 reactive-polyol formulations, with reported
apparent densities of 43.5 and 43.2 kg/m^3. Their main reactive-polyol input ratios
distinguish them from existing LPO-1 and SPO-2 references. Study labels are not
certified grades, and precursor-feed ratios are not final foam composition.

Core categories are natural 1010, metal 22, inorganic 32, polymer 18 and composite
10; project categories are natural 1010, metal 34, inorganic 44, polymer 18 and
composite 10. The relationship view has 1092 identities and 1097 supported
memberships, including 19 polymer memberships and the same one identity
relationship. Overlapping memberships do not add materials. There are 1092
states and properties, 21 grades and 116 sources; both new records reuse the
same registered source and create no grade.

The API preserves the source-reported ISO 845:2006 method, exact density values,
apparent-density classification and source-specific formulation prose.
Uncertainty, density-specific sample count, test temperature, humidity, pressure
and density-specimen dimensions remain unknown. The 24-hour room-temperature
cure is a preparation condition, not an assigned density-test temperature.
Catalog-only scope and false scientific-review/raw-reanalysis flags remain.
See the [PUR formulation packet](../../material-batches/pur-formulations-20261019/README.md).
Released main and the 62 excluded computed examples remain unchanged. Validation
is recorded with this bounded batch; no full-suite, browser or live-provider
validation is implied.

That complete query manifest anchor is `73b8b455042290c0f752e784f23687eaf3bbc8dc7631ced311af7af216f08d6e`,
bound to data commit `4361b6018fcac09571b261983ce286c84f3841e5`. The preceding
`0d2f515260b78841249f5b48331f8a80fc9164bd58bb57c592f7adfed3d96277`
anchor stays historical. Independent query tests bind the PUR ledger and packet,
remove only their two identities, two states and two properties, and recover the
exact 2509 resources and complete 64-file manifest before the existing
six-oxide-to-c901, PA12-to-12cb and older layers. Shared source rows and grades
remain intact. The older recovery layer retains its exact original scope;
partial, modified, duplicated, reordered or unrelated changes fail closed.
Old registry and NOMAD state directories stay in their original scope and are
not silently migrated or relabeled.

## Eight-salt primary-table increment, 2026-10-19

The current local snapshot contains **1124 project entries = 1100 source-qualified
identities + 24 reviewed computed compositions** after eight NBS salt references:
Hg2Cl2, HgCl2, HgI2, PbFCl, KCN, cubic NaCN, Sr(NO3)2 and Ba(NO3)2. Core categories
are natural 1010, metal 22, inorganic 40, polymer 18 and composite 10; project
categories are natural 1010, metal 34, inorganic 52, polymer 18 and composite 10.
The relationship view has 1100 identities and 1105 supported memberships,
including 40 inorganic memberships and the same one identity relationship.
Overlapping memberships do not add materials. There are 1100 states and
properties, 21 grades and 116 sources; the eight references reuse one source.

The API preserves exact reported g/cm^3 values and temperatures, source-qualified
identities, crystallographic density and source-reported calculation labels.
The NaCN result retains the 96.2-percent sample composition and carbonate/
orthorhombic reflection notes alongside its indexed-cubic-phase density.
These measured-lattice-derived references are not direct bulk-density
measurements, DFT predictions or scientific replication. Uncertainty and sample
counts remain unknown; all eight references retain catalog-only scope and false
scientific-review/raw-reanalysis flags. Released main and the 62 excluded
computed examples remain unchanged. Validation belongs to this bounded batch;
no full-suite, browser or live-provider run is implied.

The current complete query manifest anchor is `9090f061483cefde2d6255f057078b7700d3e22c85db7191ec00bc30de78f2ad`,
bound to data commit `0d642c6773263ab36f52c9ace5b27133a05f8bf0`. The preceding
`73b8b455042290c0f752e784f23687eaf3bbc8dc7631ced311af7af216f08d6e`
anchor stays historical. The independent query test adds one frozen descriptor
to the existing exact-append helper, verifies the table ledger and packet, and
removes only their eight identities, eight states and eight properties. It
recovers the exact efd4ca2 resources and complete 64-file manifest before the
existing PUR-to-2509, six-oxide-to-c901 and older layers. Shared source rows and
all grades remain intact. Previous wrappers retain their exact historical scope;
partial, modified, duplicated, reordered or unrelated changes fail closed.
Old registry and NOMAD stores retain their saved scope without migration.
See the [eight-salt packet](../../material-batches/nbs-salt-densities-20261019/README.md).
