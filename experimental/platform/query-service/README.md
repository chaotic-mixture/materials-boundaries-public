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

The preceding eight-salt snapshot contained **1124 project entries = 1100 source-qualified
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

That complete query manifest anchor is `9090f061483cefde2d6255f057078b7700d3e22c85db7191ec00bc30de78f2ad`,
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

## Final RCA reference increment, 2026-10-19

The preceding RCA snapshot contained **1127 project entries = 1103 source-qualified
identities + 24 reviewed computed compositions**. ZnB2O4, Mg2SiO4 and MgWO4 add
three inorganic identities, states and properties. Core/project inorganic counts
are 43/55; natural 1010, metal 22/34, polymer 18 and composite 10 are unchanged.
There are 116 sources and 21 grades. The relationship view has 1103 identities,
1108 supported memberships and the same one identity relationship; memberships
remain overlapping evidence.

All three API references preserve their exact g/cm^3 values and 26 degrees C
density temperature, crystallographic-density classification and source-reported
calculation basis. The Mg2SiO4 and MgWO4 preparation temperatures remain separate;
ZnB2O4 preparation is unreported. Purity remains qualitative, uncertainty and
specimen count unknown, and scientific-review/raw-reanalysis flags false.
The 62 computed examples remain excluded. Validation is bounded to this batch.

That query manifest anchor is `148c38cfa1819b8103ffa6c0f856d824b9fc54a3e9f8a5eecc50943fd19b27bd`,
bound to data commit `3ea9e25aa67226518282e7804c8e98c89453046d`. The preceding
`9090f061483cefde2d6255f057078b7700d3e22c85db7191ec00bc30de78f2ad`
anchor stays historical. One new frozen descriptor reuses the unchanged exact-
append helper and binds the three-record RCA packet and ledger. It recovers the
exact 799ca7a resources and 64-file manifest before the existing eight-salt and
older layers. Shared source rows and grades remain intact; all previous wrappers
retain their exact scope. Partial, changed, duplicated, reordered or unrelated
edits fail closed. Old registry and NOMAD stores retain their saved scope.
See the [RCA packet](../../material-batches/nbs-rca-density-20261019/README.md).

## Six binary-oxide references, 2026-10-19

The preceding binary-oxide snapshot contained **1133 project entries = 1109 source-qualified
identities + 24 reviewed computed compositions**. NiO, GeO2, As2O3, SeO2, SnO2
and ThO2 add six inorganic identities, states and properties. Core/project
inorganic counts are 49/61; natural 1010, metal 22/34, polymer 18 and composite
10 are unchanged. There are 116 sources and 21 grades. The relationship view has
1109 identities, 1114 supported memberships and the same one identity relationship.

All six API references preserve exact reported g/cm^3 values, crystallographic
density, source-reported calculation basis and source-specific temperature text.
The GeO2 and SnO2 temperature text explicitly identifies the NBS unit-cell
determination. Unknown uncertainty and sample count, catalog-only scope and false
scientific-review/raw-reanalysis flags remain. Existing elemental Ni, Ge and Sn
references stay distinct; the 62 computed examples remain excluded. Validation
is bounded to this batch.

The binary-oxide data commit is `9cdbdbdee580df356ba0133b6723a3819777dc4d`. The exact 64-file query
pin is `15c0619c3a55984550ecd564692c4588f777a10d60a4e9a01b91079c12978c2f`.
The independent recovery descriptor binds the frozen packet and data ledger and
recovers the complete `4db4ab5` predecessor before the existing RCA layer;
historical pins remain test-only and are rejected by the current registry.
See the [binary-oxide packet](../../material-batches/nbs-binary-oxide-density-20261019/README.md).

## Three Mtibe hybrid formulations, 2026-10-19

The preceding Mtibe snapshot contained **1136 project entries = 1112 source-qualified
identities + 24 reviewed computed compositions**. The three PBS/PBAT-matrix
lignosulphonate/ZnO recipes add three composite identities, states and modulus
references, bringing composites to 13. All other category counts, 116 sources,
21 grades and the 62 excluded computed examples remain unchanged.

API references preserve tensile moduli 261.88, 304.52 and 347.44 MPa, the
reported plus/minus strings 14.78, 5.22 and 16.92 MPa, five specimens, testing
at 25 degrees C and 48 h conditioning at that temperature. The central statistic
remains a reported value and the plus/minus meaning remains unspecified; no mean,
standard deviation or confidence interval is inferred. Catalog-only and false
scientific-review/raw-reanalysis flags remain.

Printed recipes 95/5/1.5, 90/10/1.5 and 85/15/1.5 sum to 101.5 and are not
normalized. Matrix PBS/PBAT 70/30 ratio basis and ZnO percentage denominator
remain unspecified. The existing PBAT and unfilled PBS/PBAT references and
Ewurum PBS/kraft-lignin blends retain their separate source-qualified scope.

The Mtibe data commit is `b21f405f5ec59033a2c31cc83616cbd16e59fed0`. The exact 64-file query
pin is `c127bf69ccca825e1b2ca3fd496f6ead65bf68478fc232d27f087b7e551b6909`.
The independent recovery descriptor binds the frozen packet and data ledger and
recovers the complete `a5cc3f6` predecessor before the existing binary-oxide layer.
Historical pins remain test-only and are rejected by the current registry.
See the [Mtibe hybrid packet](../../material-batches/mtibe-pbs-pbat-hybrids-20261019/README.md).

## Six NR/nanoclay formulations, 2026-10-20

The NR/nanoclay snapshot contains **1142 project entries = 1118 source-qualified
identities + 24 reviewed computed compositions**. MMT and organically modified
O-MMT at 1, 3 and 5 phr add six NR-based composite identities, states and
mass-density references, bringing composites to 19. All other category counts,
116 sources, 21 grades and the 62 excluded computed examples are unchanged.

The six density strings are 0.960, 0.973, 0.981, 0.959, 0.966 and 0.971 g/cm^3,
with corresponding reported plus/minus strings 0.003, 0.001, 0.005, 0.001, 0.001
and 0.003. Three specimens apply to density; four crosslinking-density specimens
do not. Room temperature has no assigned numerical value. The central statistic
remains a reported value and the plus/minus meaning is unspecified. The API
retains catalog-only scope and false scientific-review/raw-reanalysis flags.

O-MMT is a different source-described organic-modifier-containing input, not a
second identity for processing the same finished specimen. Modifier fraction and
complete cured composition remain unknown. Shared SMR 10 and raw filler brands
do not become finished-material grades. The NR_3MMsT source-table typo maps only
to NR_3MMT and adds no identity. The unfilled NR baseline stays distinct.

The NR/nanoclay data commit is `e4f2118050379e860e7c2fdcdb4646f70dbd6f97`. The exact 64-file query
pin is `7dd99df2a6ec06d6a0d6f72b31378cff5b49908113df4d78bee2ee3ffec09112`.
The independent recovery descriptor binds the frozen packet and data ledger and
recovers the complete `8981840` predecessor before the existing Mtibe layer.
Historical pins remain test-only and are rejected by the current registry.
See the [NR/nanoclay packet](../../material-batches/bianchi-nr-nanoclay-20261020/README.md).

## Six solid NBR/mCF formulations, 2026-10-20

Six solid NBR/milled-recycled-carbon-fibre formulations (Table 3 B-G) add six
composite identities, states and tensile-strength references. The NBR/mCF core
contains **1124 identities** and the project view **1148 = 1124 + 24** entries,
including 25 composites. Other categories, 116 sources, 21 grades and 62 excluded
computed examples remain unchanged. Loadings are 5, 10, 20, 30, 40 and 50 phr;
the existing REF (0 phr), D_Fo foam and direction-specific specimens add no identities.

Table 4 retains 5.26, 5.11, 5.33, 5.47, 4.60 and 4.57 MPa with reported plus/minus
0.78, 1.27, 0.74, 1.05, 0.68 and 0.72 MPa. The source reports means pooled across
two orthogonal specimen directions. The plus/minus statistic, sample count,
numerical test temperature, humidity and conditioning remain unknown. The
abstract's improvement statement is retained as a discrepancy with the selected
Table 4 values; no improvement or isotropy is inferred. Supplier constituent
grades and ACTMIX S-80 product input do not become new finished-material grades.

The NBR/mCF data commit is `13703d881836a50f290865448a8e8289779c5bd1`. The exact 64-file query
pin is `8c47bf8592437932508298417ed4c6e93e92091a0e25266bee3816acec797da8`. The independent descriptor binds
the frozen packet and data ledger and recovers the complete `f5bdcc4` predecessor
before the existing NR/nanoclay layer. Historical pins remain test-only and are
rejected by the current registry.
See the [NBR/mCF packet](../../material-batches/tamas-benyei-nbr-rcf-20261020/README.md).

## Ten Outokumpu Core alloy references, 2026-10-20

Ten source-qualified Outokumpu Core alloy formulations add ten identities, grades,
states and Young's-modulus references. The current core contains **1134 identities**
and the project view **1158 = 1134 + 24** entries. Metals total 32 in the core and
44 in the project view; grades total 31. Other category counts, 116 sources,
24 accepted computed compositions and 62 excluded examples remain unchanged.

The selected Table 7 modulus references retain GPa units and the reported
20 degrees C condition. Their source basis distinguishes EN reference rows from
the manufacturer-tested footnoted row; it does not turn all entries into new
measurements. Table 1 typical mass percentages are not specification limits or
complete alloy formulas. Dashes are not zero and an iron remainder is not inferred.

Core 201/4372 and Core 201LN/4372 retain the shared EN 1.4372 designation with
separate qualified EN/UNS aliases. Different source-reported UNS and typical
C/Cr/Ni/N values support two formulations. Core CLI search for `1.4372` matches
both through their qualified aliases. The bounded local API search uses `4372`,
the shared fragment in their indexed designations; aliases and composition prose
are outside its search fields. The shared code is not a unique identity key.
Existing 304L/4307 and 441/4509
are retained; 304L/4306 and unresolved 439M add no new identities. Grade records
are linked designations, not an additional material count.

The Outokumpu data commit is `7f814e4905ad58bcc66999046d04ca1311ceba9d`. The exact 64-file query
pin is `b228d514b2b1dbb8bad428d6f0be7f300947ee2e1c3c64a6f9f0e55df132ade7`. The independent descriptor binds the
frozen packet and data ledger and recovers the complete `eee77b5` predecessor
before the existing NBR/mCF layer. Historical pins remain test-only and are
rejected by the current registry. Existing source rights metadata is unchanged;
only limited factual references and original curation are included.
See the [Outokumpu Core packet](../../material-batches/outokumpu-core-moduli-20261020/README.md).

## Measured commercial filaments, 2026-10-21

The reviewed filament packet adds 8 source-qualified identities,
0 linked grades, 8 filament states and
16 measured tensile-property references. The current core
contains **1142 identities** and the project view **1166 = 1142 + 24** entries.
The core has 31 grades and 120 sources. The 24 accepted
computed compositions and 62 excluded examples remain separate.

The source reports filament tensile modulus and tensile strength. Workbook
`avedev` labels remain literal source descriptions; they are not standard deviations
or inferred confidence intervals. Source-average sample counts do not establish
an exact per-record sample count. These values describe the measured filament
states and do not establish printed-part properties or engineering allowables.

The filament data commit is `f1163db5030e81b163bd4cb90041d28e5961155c`. The exact 64-file query pin is
`393af99b3a9ef08e6d73c87bde302af74e66dd59628e86b368b88882462057a5`. The independent descriptor binds the frozen packet and data
ledger and recovers the complete `5e8d63d` predecessor before the unchanged
Outokumpu and earlier history. Historical pins remain test-only and are rejected
by the current registry.
See the [measured filament packet](../../material-batches/zenodo-8089569-filaments-20261021/README.md).

## Tough PLA identity follow-up, 2026-10-21

The reviewed follow-up within the same Zenodo workbook adds one polymer identity
with two separate measured filament states and four tensile-property references.
The preceding Tough PLA snapshot contains **1143 identities, 1144 states, 1154 properties,
31 grades and 121 sources**. The project view contains **1167 = 1143 + 24**
identity entries; the 62 excluded examples remain separate.

The exact source designations `PLA Tough White 20231` and
`PLA Tough Black 202300` remain separate states of one source-qualified Tough PLA
identity. The workbook codes are unverified literals, not authenticated product
SKUs. Both grades remain null. No averaging, code correction, PMMA assignment,
composition fraction or printed-part property is inferred. The 2022 SDS supports
classification only; the existing Zenodo record supports the measured values.
Nylon remains deferred.

The actual DATA commit is `0338481fe3492476d8fe046ed6dd9a733662a076` and the exact 64-file
query pin is `a6b5e9835807a397c81f668cb3c1f19fe70d62074899bdf6365892543220d4b2`. A new finite descriptor recovers the complete
`5cc1418` batch8 predecessor before all unchanged older layers. Historical
pins and the original filament test facts remain unchanged.
See the [reviewed follow-up packet](../../material-batches/zenodo-8089569-tough-pla-followup-20261021/README.md).

## Nylon historical-family follow-up, 2026-10-21

The reviewed continuation of the same Zenodo workbook adds one manufacturer-family
polymer identity, one measured reference-filament state and two tensile properties.
The preceding Nylon snapshot contains **1144 identities, 1145 states, 1156 properties,
31 grades and 123 sources**. The project view contains **1168 = 1144 + 24**
identity entries; the 62 excluded examples remain separate and main stays at 1081.

The 2019 manufacturer SDS supports a family described as based on PA6/PA66;
the 2021 manufacturer pricing submission maps stock code 1647 to Transparent
Nylon. These historical sources do not identify the study lot, establish recipe
continuity, composition ratio or molecular architecture. The state composition
remains unknown and its grade is null. Neither source supplies numerical
properties: the unchanged Zenodo source supports both measured filament values.
ISO reference values and printed or extruded states do not replace those values.
The two new identity-only sources and one reused numerical source are counted
separately. Manufacturer PDFs and the workbook are not distributed.

The actual DATA commit is `cbd68da88d7bba461dce15ee5a71e43ef577e8c3` and the exact 64-file
query pin is `124044eb8afcaf927ec9ff4770da66dfedc641391cd58e4b873735ee7424db4e`. The new finite descriptor recovers the complete
`2c8ddac` predecessor before the unchanged Tough, batch8 and older layers.
Historical evidence, pins and dedicated prior tests remain unchanged.
See the [reviewed follow-up packet](../../material-batches/zenodo-8089569-nylon-followup-20261021/README.md).

## Bruns NBS2 borosilicate recipes, 2026-10-23

The reviewed append adds four source-qualified nominal oxide recipes, each with
one furnace-cooled state and one measured mass-density reference. The current
core contains **1148 identities, 1149 states, 1160 properties, 31 grades and
124 sources**. Formal project admissions total **1172 = 1148 + 24**, with
metal 44, inorganic 65, polymer 25, composite 28 and natural 1010. The 24
computed buckets, 62 excluded examples and released main count of 1081 are
unchanged. Core inorganic identities increase from 49 to 53.

Nominal Al2O3 recipes of 1.0, 1.5, 2.0 and 4.0 mol% retain Table 3 density
means of 2.131, 2.133, 2.130 and 2.137 g/cm³ and reported standard deviations
of 0.006, 0.010, 0.002 and 0.004 g/cm³ respectively. These are not bounds,
confidence intervals, SEMs or engineering allowables. Density-test temperature,
pressure, conditioning and exact independent sample count remain unknown.
The 4.0 mol% preparation exception is retained; neither graphite-mold casting
nor the other recipes' cooling rate is assigned to it. Nominal and ICP-OES
compositions remain distinct, without asserting final stoichiometry.

The runtime DATA commit is `2d940bcbbe13aa0cd0c0726bb5766e98edf62306`. The
new complete 64-file query pin is `09b57c7410b7b6c858abd566153dd932a451c9b5d4ed56b0963cbe4064543a05`.
The finite Bruns descriptor recovers the exact `46674771` predecessor before
the unchanged Nylon and older layers. Earlier databases are rejected without
implicit migration or metadata rewrites; use a separate registry for this
snapshot. Existing code-only successor compatibility remains exact.

Only selected attributed facts and original qualifications are included under
the article-specific CC BY 4.0 notice. Source PDFs, figures and raw measurements
are not distributed. See the [reviewed Bruns packet](../../material-batches/bruns-nbs2-borosilicate-20261023/README.md).

## Tarasov PNA-BPF nominal formulations, 2026-10-23

The runtime append contains five source-qualified polymer formulations, each
with one DDS-cured state and one Table 7 tensile-strength reference. That
core snapshot contained **1153 identities, 1154 states, 1165 properties, 31 grades and
125 sources**. That experimental formal project view was **1177 = 1153 + 24**,
with metal 44, inorganic 65, polymer 30, composite 28 and natural 1010. The 24
reviewed computed records remain separate; the 62 unadmitted examples and main
count of 1081 remain unchanged. Publication and validation status are recorded
separately from these local runtime counts.

PNA-BPF-1 through PNA-BPF-5 preserve strengths of 66.7, 66.0, 70.2, 74.5 and
72.7 MPa respectively. Their HCP:BPF:ECH labels of 1:8:16, 1:9:16, 1:12:16,
1:18:16 and 1:24:16 remain author-reported nominal labels. The inconsistent ECH
ratios, PNA-BPF-2 HCP mass/mole entry and KOH/NaOH descriptions remain explicit
discrepancies. They do not establish exact stoichiometry, final composition,
purity, conversion or molecular architecture. PNA-BPF-S and DGEBA/DGEBF controls
are excluded; its changed alkali delivery does not prove PNA-BPF-S identical
to PNA-BPF-1. No grade or reinforcing phase is inferred.

The selected state is cured at 180 deg C for 8 h. Tensile testing retains the
reported GOST 11262-2017 (ISO 527-2:2012) citation, 10 mm/min stretching speed
and source plate thickness of 4 mm. Test temperature, humidity, sample count,
aggregation and uncertainty remain unknown. These are measured-source scalars,
not declared means, engineering allowables or independently reviewed science.

DATA commit `ff28631faf1d1af804171378953b570313e35b83` appends the exact approved
candidate facts. Query manifest `f77658c4df1434de7dd9d9d8d0e9d4ab31eef200477ec748f80c1a7acd371dbf`
changes only the three catalog entries of the existing 64-file anchor. The
Tarasov recovery descriptor restores the exact `faa002c` Bruns predecessor
before the unchanged historical recovery chain. Earlier persistent registries
are rejected without automatic migration or metadata rewriting.

Only selected attributed facts and original curation are distributed under the
article-specific CC BY 4.0 notice. The PDF and rendered pages are excluded.
See the [reviewed candidate packet](../../material-batches/tarasov-pna-bpf-20261023/README.md)
and its separate runtime integration evidence for testing and review status.


## Kapoor analyzed phosphate glasses, 2026-10-24

The local runtime append adds six inorganic formulations with one as-prepared,
annealed/reannealed state and one reported measured density each, no grades,
and one attributed CC BY 4.0 source. The Kapoor checkpoint core counts were 1159 identities,
1160 states, 1171 properties, 31 grades and 126 sources. The experimental
project view at that checkpoint was 1183 = 1159 source-qualified identities + 24 unchanged reviewed
computed records: metal 44, inorganic 71, polymer 30, composite 28, natural 1010.
The excluded 62 examples and main's 1081 entries remain separate.

P60/P50/P46/Al5/Al10/Al15 retain 2.521/2.654/2.718/2.614/2.585/2.583 g/cm3
respectively. ICP-OES oxide mol% is analyzed composition, not a nominal recipe
or independently validated final stoichiometry. Density uses air/ethanol
Archimedes weighing at room temperature. At least ten repetitions per sample
is not an independent specimen count; <=0.002 g/cm3 is a source-wide SD bound,
not six measured SDs. Aggregation, individual uncertainty, specimen count,
exact temperature, pressure, humidity and porosity remain unknown. Compressed
states, calculated molar volumes and packing densities are excluded. P60 is
study-qualified and does not alias the unrelated EPDM_H_P60 identity.

The data append is `76cae67a9401b916c1409ad3c2212fa3c103be6f`. Query pin
`23be9c9f3716f824ea79872167ff5f80d991ea5d222d702ad41d40188c871f4a`
changes only the three data entries; the other 61 manifest entries and exact
code compatibility remain unchanged. Kapoor recovery restores the exact
196995 Tarasov snapshot before the retained older recovery chain. Old stores
fail closed without migration, while saved historical reports keep their scope.

The [unchanged candidate packet](../../material-batches/kapoor-phosphate-glasses-20261024/README.md)
retains its zero-admission history. Runtime validation and publication require
separate evidence and review; local counts do not claim a main release.
Source assets are not distributed.

## Tian 2023 nominal nano-Ti composite increment

The Tian checkpoint core counts are 1161 identities, 1162 states, 1173 properties, 31 grades
and 127 source/provenance records. The experimental project projection is
1185 = 1161 source-qualified identities + 24 unchanged computed records; main
remains 1081. The two new composite formulations use study-qualified IDs and
nominal nano-Ti loadings of 0.5 wt% and 1 wt%, each with one Table 2 Actual
Density in the as-extruded state. They do not add alloy/nanoscale family
memberships, scientific inverse claims or propagated properties.

Installed query/CLI regression tests bind the complete resolved objects and
correct eight-author attribution. They preserve literal `1 wt Ti`, all density
unknowns, source-rights and mirror/manifest limitations. Theoretical densities,
tensile-only test conditions and the unreinforced comparator are excluded.
Stale catalog versions and old computed stores remain rejected without migration.

## Curaua 2021 nominal foam-composite increment

The current experimental graph contains 1164 source-qualified identities,
1165 source-scoped states, 1176 reference properties, 31 grades and 128 source
records. Primary category counts are natural 1010, metal 32, inorganic 59,
polymer 30 and composite 33. The project view is 1188 = 1164 source-qualified
identities + 24 unchanged reviewed computed buckets. Main remains 1081.

Three study-qualified bleached Curaua/RPUF nominal formulations each contribute
one apparent-density mean: CF 0.1, CF 0.5 and CF 1. Fiber loading is relative to
total RPUF mass, not analyzed final composition. ISO 845 and ten density samples
per group are recorded. Literal CV superscripts have unknown units; they are
not percent CV, SD or zero uncertainty. Density measurement age remains unknown
across the source's 24 h cure and at least 7 day post-cure statements. Temperature,
pressure, humidity and independently produced specimen counts are not inferred.
Only composite membership is supported; no constituent membership, scientific
inverse relationship or property propagation is added.

The exact query baseline is
`974f22632699247d5821a57323ab5de0d559b99959086e32ebdb660197db9431`.
Old computed stores remain rejected without migration. The unchanged reviewed
candidate retains its zero-admission history; current runtime admission is a
separate step. Source PDF visual evidence remains producer evidence, with the
official XML independently verified. CC BY 4.0 attribution and all scientific
limitations remain explicit. This experimental integration is not a main merge
or deployment.
