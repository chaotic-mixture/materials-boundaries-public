# Evidence-backed overlapping material families

This additive read-only prototype builds on experimental platform 0.5.0.dev0
at published commit `6a7bb7c84fa030d7f1527bd18e8e124bee743960`. It is a new,
bounded implementation, not a restoration of the lost earlier graph.

The adjacency extension described below starts from experimental commit
`7248dcd06e7ab4bc5f3fae1f3f21a7d9e0dbad3c`. It changes query code, documentation
and tests only. It admits no identities and changes no source or catalog data.

## Scope and evidence

Existing identities keep their IDs and their single legacy `category`. The
view adds independent `member_of` assertions across these axes:

- Family: metal, alloy, inorganic, ceramic, polymer, composite, natural
- Electronic class: semiconductor
- Application role: battery, catalyst
- Morphology: two_dimensional, nanoscale

A concept's status is either `supported` or `unknown`. Unknown means this
policy has no reviewed supporting assertion. It does not mean the material
cannot belong to that concept. Membership is not inferred from formula,
supplier name, presence in a source title, a constituent, or another state.
Battery and catalyst refer to application roles; they are not intrinsic claims
about all samples of a chemistry. Bulk graphite does not become 2D graphene.

All 1,144 categories at that experimental baseline are exposed as explicit catalog-category evidence,
not newly re-audited primary-source classifications. Five extra assertions are
supported by exact, pinned English catalog text:

- Hydro 6061 and TIMETAL 6-4: alloy as well as metal
- Ożóg AlN and Lukianova Si3N4 study formulations: ceramic as well as inorganic
- Ewurum B20: polymer as well as composite

The B20 blend also has one directed `has_constituent` edge to the existing
Indulin AT identity, limited to the B20 simple-blend series. This does not
assert identity equivalence, property inheritance, a converse edge, or
transitive membership. Other relationships remain unreviewed.

The finite overlay in `materials_query/pins/family_relationships.json` pins
supporting identity content, exact quotes, and the constituent target. Evidence
includes catalog field/quote, source ID, URL and locator copied from the frozen
validated catalog. These inherited locators establish traceability; this task
makes no claim to have re-audited the primary sources. Evidence drift detected
during initialization disables the relationship view while preserving the
legacy catalog APIs. Queries use captured historical content; they do not read
files again or claim that files have remained unchanged since capture.

## Exact coverage

Coverage below is for the 1,144 source-qualified identities at experimental
commit `7248dcd`. These are overlapping counts; they must not be summed into a
unique-material total. The 24 separately admitted computed records are outside
this view. The experimental project total remains 1,168; this extension does
not change the last verified main total of 1,081.

| Concept | Supported | Unknown |
| --- | ---: | ---: |
| Metal | 32 | 1,112 |
| Alloy | 2 | 1,142 |
| Inorganic | 49 | 1,095 |
| Ceramic | 2 | 1,142 |
| Polymer | 26 | 1,118 |
| Composite | 28 | 1,116 |
| Natural | 1,010 | 134 |
| Semiconductor | 0 | 1,144 |
| Battery | 0 | 1,144 |
| Catalyst | 0 | 1,144 |
| Two-dimensional | 0 | 1,144 |
| Nanoscale | 0 | 1,144 |

There are 1,149 supported memberships and one identity-to-identity edge across
1,144 unchanged identities. Five identities have two supported memberships.
This is partial classification, not comprehensive review. The view admits zero
new identities and does not scientifically deduplicate materials from different
sources. The separate 62 unadmitted computed examples are not included.

## API

Enable the existing optional local catalog factory:

```python
from materials_query.app import create_app
app = create_app(enable_local_catalog=True)
```

Read `GET /api/catalog/relationships/status`. It reports coverage,
`catalog_version`, and `relationship_version`. The latter binds the catalog
pin, policy, overlay, and implementation bytes. It is independent of the
legacy catalog API version. Old catalog responses and data stay unchanged.

All three POST endpoints require `version` (the catalog pin) and
`relationship_version` (the relationship pin). Copy these exact strings from
status; stale pins return 409 and missing pins return 422.

```json
{
  "version": "<catalog_version from status>",
  "relationship_version": "<relationship_version from status>",
  "identity_id": "mat_ewurum2025_pbs_lignin20"
}
```

Send this to `/api/catalog/relationships/identity`. The response's
`result.data` contains all twelve concept statuses and outgoing identity
relationships, each supported assertion carrying its evidence. The response
retains the existing catalog envelope and adds `result.relationship_version`.

For `/api/catalog/relationships/search`, replace `identity_id` with:

```json
{"concepts": ["polymer", "composite"], "match": "all", "limit": 20}
```

`any` (default) performs union and `all` performs intersection of supported
memberships. Repeated concepts and overlapping memberships never duplicate an
identity. The response reports exact matching and returned unique-ID counts
and an explicit truncation flag. Limits are 1–100 returned IDs, at most twelve
requested concepts, a 32 KiB request body, and the same two-operation semaphore
and origin/host/transport protections as the existing catalog routes. There is
no pagination in this bounded first version. Unknown concepts are rejected;
unknown memberships are inspectable through the identity endpoint but are not
search matches.

### Single-hop relationship adjacency

For `POST /api/catalog/relationships/neighbors`, use the same two pins and:

```json
{
  "identity_id": "mat_ewurum2025_indulin_at",
  "direction": "incoming",
  "limit": 20
}
```

`direction` accepts `outgoing`, `incoming`, or `both` (default). `limit` is a
strict integer from 1 to 100, default 20. The endpoint shares the existing
request body, host, origin and two-operation concurrency guards. It performs
exactly one hop; there is no recursion, path search, pagination, source fetch,
property inheritance or membership propagation.

`result.data` contains `identity_id`, `direction`, `max_hops: 1`,
`matching_relation_count`, `returned_relation_count`, `truncated`, `records`,
`count_scope` and `traversal_scope`. Counts describe unique directed assertions,
not material identities. A known identity with no matching assertions returns
200 with empty records and zero counts; an unknown identity returns 404.
Unsupported directions, out-of-range or noninteger limits, unknown fields and
missing pins return 422. Stale catalog or relationship pins return 409.

Each record contains the original `source_identity_id`, `relation`,
`target_identity_id`, `status`, `scope` and `evidence`, plus the reviewed
`source_identity_sha256` and `target_identity_sha256`. `neighbor_identity_id`
identifies the other endpoint for navigation. `traversal_directions` describes
how this query reached the assertion, not a scientific predicate. An incoming
query from Indulin AT therefore returns the original B20 `has_constituent`
Indulin AT assertion. It does not assert that Indulin AT has B20 as a
constituent. The existing identity endpoint still returns only outgoing
relationships and its response shape is unchanged.

The `relation_key` is `family-relation:` followed by the SHA-256 digest of
canonical JSON containing `source_identity_id`, `relation`, and
`target_identity_id`. It identifies that original directed endpoint/predicate
triple. It is stable across traversal direction and overlay order, and is not
a globally adjudicated scientific identifier or an evidence-revision digest.
Scope or evidence can change while the key stays the same: caches must use both
snapshot pins together with the key. Both endpoint hashes are validated at
initialization; the relationship version also binds the entire overlay and
implementation. A restart is required to capture new content or code.

Results are deduplicated by relation key, then sorted by source ID, relation
and target ID before truncation. A self-loop, if supported by a future reviewed
overlay, would appear once for `both`, with `traversal_directions` equal to
`["outgoing", "incoming"]`. Cycles do not trigger additional traversal. Duplicate
assertions in the overlay still fail initialization. Every returned record,
including nested evidence, is a defensive copy of the captured assertion.

The default service does not load the core catalog. A disabled catalog or
invalid relationship overlay returns 503 for this view. Source resources are
never refreshed or mutated automatically. Restart after source/policy changes.

## Verification

The code-only adjacency experiment is based on
`7248dcd06e7ab4bc5f3fae1f3f21a7d9e0dbad3c`. Its exact runner selects 114 tests:
17 release, workflow and history checks, plus 97 installed-package checks
(23 adjacency, 20 existing family, 35 existing local catalog, 16 transport and
3 catalog baseline tests). This is a bounded affected suite, not the full
repository suite. Selected skips, expected failures, missing or duplicated
case IDs are failures.

From a checkout with the development dependencies installed:

```sh
python scripts/run_family_adjacency_ci.py --test
python scripts/validate_catalogs.py
python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir dist . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform
python scripts/run_family_adjacency_ci.py --wheel-dir dist --dependency-dir dependency-wheels
```

Use an empty wheel output directory. The dependency directory must contain the
wheels from the platform's pinned requirement and projection locks; the exact
preparation commands are in the `family-adjacency-targeted` CI job. The runner
verifies all six package file sets, bytes, versions and license files, installs
without an index in a fresh environment, verifies import origins and catalog
byte parity, and runs each installed test group in a separate process under the
existing offline guard. It checks the unchanged 1,168 experimental project
admissions (1,144 source-qualified identities plus 24 reviewed computations).
No source data or scientific assertions are added by this query.

The two CI matrix targets are Ubuntu/Python 3.11 and Windows/Python 3.12. Older
job steps remain intact and the exact experiment branch selects this affected
suite. A configured check is not a claim that a run passed. The suite includes
no live-provider acquisition, browser verification, main merge or deployment.
