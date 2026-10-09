# Evidence-backed overlapping material families

This additive read-only prototype builds on experimental platform 0.5.0.dev0
at published commit `6a7bb7c84fa030d7f1527bd18e8e124bee743960`. It is a new,
bounded implementation, not a restoration of the lost earlier graph.

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

All 1,057 legacy categories are exposed as explicit catalog-category evidence,
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
makes no claim to have re-audited the primary sources. Evidence drift disables
the relationship view while preserving the legacy catalog APIs.

## Exact coverage

Coverage is per existing catalog identity ID. These are overlapping counts;
they must not be summed into a unique-material total.

| Concept | Supported | Unknown |
| --- | ---: | ---: |
| Metal | 14 | 1,043 |
| Alloy | 2 | 1,055 |
| Inorganic | 16 | 1,041 |
| Ceramic | 2 | 1,055 |
| Polymer | 15 | 1,042 |
| Composite | 3 | 1,054 |
| Natural | 1,010 | 47 |
| Semiconductor | 0 | 1,057 |
| Battery | 0 | 1,057 |
| Catalyst | 0 | 1,057 |
| Two-dimensional | 0 | 1,057 |
| Nanoscale | 0 | 1,057 |

There are 1,062 supported memberships and one identity-to-identity edge across
1,057 unchanged identities. Five identities have two supported memberships.
Among the user's requested metal/alloy/ceramic/polymer/electronic/role/morphology
concepts, 31 distinct identities have at least one supported membership; 1,026
have none. This is partial classification, not comprehensive review. The view
admits zero new identities, does not include the seven separately staged
computed identities, and does not scientifically deduplicate materials from
different sources.

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

Both POST endpoints require `version` (the catalog pin) and
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

The default service does not load the core catalog. A disabled catalog or
invalid relationship overlay returns 503 for this view. Source resources are
never refreshed or mutated automatically. Restart after source/policy changes.

## Verification

Run the dedicated tests with the repository's optional-core installation:

```sh
python -m unittest discover -s experimental/platform/query-service/catalog-tests -v
python experimental/platform/ci/run_recovery_ci.py
```

Tests cover overlap, union/intersection deduplication, unknowns, exact coverage,
all asserted source references, pinned quotes and evidence drift, constituent
scope, detached results, version conflicts, input/transport bounds, disabled
mode, and unchanged legacy categories. The recovery CI builds and tests fresh
wheels, including the packaged overlay, under the existing offline guard.
No live-provider, browser, remote CI, merge or deployment claim is made here.
