# Read-only hBN relationship projection

This checkout-only view connects the existing Falin monolayer hBN observations
to their proposed material, state, study cohort and physical feedstock context.
It is a bounded companion view, with `curation=proposed` and
`evaluation_support=catalog_only` throughout. It creates no catalog observation
or admitted material. The formal reader independently verifies its resource
hashes and reports the current experimental **1,177 = 1,153 legacy identities + 24 reviewed computed
composition admissions**. The separate 62 unadmitted computed examples remain
excluded. This change's admitted delta is **0**.

The current formal resource pins also include five Tarasov source-qualified nominal polymer formulations.
They do not change this hBN view's reviewed nodes, edges or historical review
anchor. Earlier 1,103-entry projection reports retain their original formal scope;
the retained main boundary remains 1,081 rather than this experimental count.

## Reviewed scope and missing joins

The five hBN entries in `typed_edge_examples.json` contain eight endpoint IDs
in three disconnected components. They did not previously establish complete
node records or the material/state/cohort joins. The pinned
[review record](hbn_projection_review.json) explicitly defines six context-node
kinds and adds only these two proposed mappings:

| Subject | Predicate | Object |
| --- | --- | --- |
| Existing proposed Falin material | `has_state` | Existing proposed monolayer state |
| Existing proposed Falin study cohort | `realizes_state` | That monolayer state |

All existing endpoint and edge IDs remain unchanged. The other five relations
are material `phase_of` BN chemical context, state `has_layer_state` monolayer,
state `derived_from` study feedstock, and two observations `observed_on` the
cohort. The full view has **8 nodes, 7 edges, 1 proposed material context,
1 state, 1 cohort, 1 feedstock, 1 study and 2 source observations**. These counts
have distinct meanings; neither graph nodes nor proposed contexts are admissions.

The retained identity review originally searched the main catalog's 1,057 identities,
20 grades and 1,057 states, plus the 24 formal computed admissions. It found no
hBN/cBN/BN identity or grade to map. A BN/AlN powder-bed and residual-phase
mention in `state_ozog2020_aln90_y6_a4_pressed` is incidental to an AlN material;
it does not identify Falin hBN. The broader local copy inventory inspected
487 catalog/archive copies representing 11 distinct byte contents with no read
errors. These are bounded local absence findings, not proof of global physical
uniqueness. Legacy identity, formal admission and feedstock ancestor mapping
remain null. The review record pins the audit receipt hash.

## Source identity and scientific limits

The view reuses exactly these canonical source-observation IDs:

- `falin_2017_hbn_monolayer_in_plane_stiffness_2d`: **289 +/- 24 N/m**.
- `falin_2017_hbn_monolayer_breaking_strength_2d`: **23.6 +/- 1.8 N/m**.

Records selected by the reviewed study, method family or canonical IDs must
first pass the existing closed hBN scientific contract. The projection identity
is `(study_id, method_family, quantity, scientific_payload_sha256)`. The existing
validator ignores only appended IDs/names, normalizes integral float spelling,
and tolerates reversal of top-level evidence order. Each quantity remains a
separate source observation. Every actual catalog ID and whole-record hash is
retained as an alias/reference; the catalog itself is neither rewritten nor
deduplicated. This preserves the core appendability regression. Unrelated
studies, including cubic BN, are outside this view; BN formula alone never
selects or merges a record. This is not a general catalog validator.

Selecting either one of the two properties still gives one proposed material.
Monolayer context and reverse traversal also do not add materials. Navigation
follows the original stored edges without creating inverse assertions or
transferring properties: only observation nodes carry scientific payloads.
In particular, `derived_from` records preparation lineage and never assigns
membrane stiffness or strength to bulk feedstock. hBN and cBN are not equated.

The two properties share a study context, not independent replication or known
individual specimens. `individual_specimen_overlap` remains `unknown`.
Eleven tested sheets do not establish eleven failure events, and typically five
indentations per sheet do not establish 55 curves. AFM apparent height
**0.48 nm** remains distinct from the **0.334 nm** effective model thickness.
Selected results stay in N/m; no converted GPa result is generated. Existing
GPa constants within the strength inference model are preserved as model inputs.
The source's distinct fitting/FEM methods, unknown numerical conditions and
reported-SD provenance remain attached to the observations.

The primary source is [Falin et al. (2017)](https://www.nature.com/articles/ncomms15815),
DOI 10.1038/ncomms15815. The main article is CC BY 4.0. Supplemental and
peer-review-file licenses remain unverified. Existing inspection metadata is
inherited, not a claim that this task repeated those inspections. This task had
bounded main-HTML access; follow-up requests failed. The two bridges rely on
fixed source-bound observations, inherited main-article locators and the
user-verified preparation context. No raw data, structure asset or article
asset is copied. Software validation is not scientific review or license clearance.

## Local use

From this repository checkout, using Python 3.11 or later:

```sh
python -B experimental/platform/relationships/hbn_relationship_projection.py
python -B experimental/platform/relationships/hbn_relationship_projection.py --node falin_2017_hbn_monolayer_in_plane_stiffness_2d --direction both --max-depth 8
```

The command reads local catalogs and emits deterministic JSON to stdout. It
does not fetch URLs, write reports or mutate catalogs. Shell redirection may
save a report when needed. Exact node IDs and catalog aliases are accepted;
directions are `outgoing`, `incoming` and `both`, with depth bounded to 0–8.
Invalid input exits 2 without a partial JSON report. The output contains
separate formal, context and observation counts, review/resource hashes and a
content version. The content hash detects accidental alteration; it is not an
authentication signature.

For Python checkout callers, `build_projection(observations=None,
typed_edges=...)` returns a detached dictionary; omit both inputs for the local
catalog. A list or a catalog `records` envelope may select one or both reviewed
quantities. Empty selection is rejected. `traverse(projection, node_id,
direction='outgoing', max_depth=4)` returns detached navigation results. Changed
scientific payloads, conflicting/duplicate IDs, context-ID alias collisions,
missing/changed hBN examples or a changed review pin fail closed. New source
quantities or relationship mappings require explicit review and code changes.

## Validation and remaining work

Run the focused projection checks and the existing hBN catalog regression:

```sh
python -B -m unittest discover -s experimental/platform/relationships -p test_hbn_relationship_projection.py -v
python -B -m unittest discover -s tests -p test_hbn_observation_catalog.py -v
```

The existing `experimental-platform-offline` workflow includes
`experiment/hbn-relationship-projection` in its exact push, pull-request target
and manual-dispatch branch scopes. Its `offline-fixtures-and-wheels` matrix
jobs on Ubuntu 24.04 with Python 3.11/3.12 run the complete 14-test module as
the `hbn-projection` stage, requiring all 14
pinned test IDs and rejecting failures, errors, skips and expected failures.
This checks source from the checkout, including the core and formal catalog
readers; it is not installed-wheel coverage. The stage runs in its own checker
process, so its source imports cannot affect the separate installed smoke.
The `optional-core-catalog` jobs retain their existing catalog suites.
The core `tests` workflow retains its exact original bytes and all checks.
The two matrix executions cover the same 14 distinct tests and do not increase
the distinct-test count. Hosted results must be checked for the exact commit;
this wiring alone does not establish a CI pass. See the
[offline CI instructions](../ci/README.md) for the guarded local command.

On Windows, set `$env:PYTHONUTF8 = '1'` in PowerShell before running the core
regression. Its existing multilingual CLI subprocess writes Unicode; a GBK
default cannot encode every source character. The new projection CLI writes
UTF-8 bytes directly and passed without that setting.

The focused checks cover alias preservation, property subsets, actual formal
counts, unchanged typed edges, reviewed bridges, cBN separation, bounded/reverse
navigation, non-inheritance, bad units/thickness/counts, review changes and CLI
failure behavior. The core regression independently retains
`test_same_family_ids_and_reversed_evidence_are_appendable`.

No general graph importer, relationship database, packaged API, web endpoint,
UI integration, material admission or additional source family is implemented.
Scientific/rights review and any future identity resolution remain separate
work. This local experiment does not register a DOI or deploy a service.
