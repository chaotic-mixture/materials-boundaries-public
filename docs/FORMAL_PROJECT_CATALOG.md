# Formal project catalog admission policy

The released main baseline `4c5656c` combines 1057 source-qualified identities
with exactly 24 independently reviewed computed composition buckets, for 1081
formal project admissions. That published count remains unchanged.

This unmerged experimental candidate retains seventeen NBS references, one Nb
reference, one NC2 concrete formulation and three polymer/composite formulations
from earlier increments, and adds four composite references plus one
source-qualified PA12 representative on 2026-10-19. It pairs its 1084
source-qualified identities with the same 24 computed buckets.
Its **proposed experimental total is 1108**, with natural 1010, metal 34,
inorganic 38, polymer 16 and composite 10. This is a candidate for a reviewed
release, not an authorized change to the main formal count. The candidate may
retain resource pins matching its new core bytes for reproducible testing.
Those proposed pins do not establish release approval.

The 2026-10-17 scope and evidence remain in the [earlier incremental integration record](MATERIAL_GROWTH_FORMULATIONS_20261017.md).
The 2026-10-19 increment adds B45 PBS/lignin and EPDM_H_P20, EPDM_H_P40 and
EPDM_H_P60; see the [B45 packet](../experimental/material-batches/20261019-pbs-lignin45/README.md),
[EPDM packet](../experimental/material-batches/20261019-epdm-pcm-hostatron/README.md)
and [integration manifest](../experimental/material-batches/20261019-polymer-composites-incremental/integration.json).
The subsequent [PA12 source-family packet](../experimental/material-batches/20261019-pa12-source-family/README.md)
adds one EOS PA2200 source-qualified PA12 identity with one selected tensile-strength
reference, 43.72 MPa. Its grade, processed state and property remain separate
records; they do not create additional identities. The packet does not establish
universal equivalence among PA12 brands or an engineering allowable.
The `formal-project-count-policy/1` convention does not claim global
physical uniqueness, experimental observation of every record, or equivalent
levels of scientific evidence.

## Two immutable indexes, one explicit project policy

The candidate source-qualified index preserves all 1057 predecessor identities,
states and properties and appends twenty-seven source-qualified references, for an experimental core
count of 1084: natural 1010, metal 22, inorganic 26, polymer 16 and composite 10.
The released main core remains 1057. Existing source, grade and
state APIs are unchanged. Legacy
entries retain their actual per-property evidence types; they are not all labeled
experimental. Existing consumers do not receive computed values disguised as
experimental measurements or legacy material-state records.

The formal computed index contains exactly one admission per reduced integer
composition in the 24-record review. Each entry retains the complete original
normalized model under `model`, including original formula, provider IDs,
conservative bucket, scalar computed density, method, attribution, references,
rights, modification notices, category basis, unknowns and overlap relations.
Metal membership is compositional; metallic electronic behavior remains unknown.

The packaged review has byte SHA-256
`a285523b2b2fdbf0d750ce6ac56e3abfb80d5c42056229a2352b016a787fd875`
and canonical review SHA-256
`8cc9ea2e0bf0006df29ec46c720e871b059d3b7b876976ec94bdd9cdfb6507de`.
It is byte-identical to the separately accepted experimental example. That
example's acceptance pin covers normalized metadata; the released main policy
separately admits these 24 computed buckets. Reusing them in this candidate does
not constitute a release decision for the twenty-seven new source-qualified references. The review's
earlier preparation-stage wording is retained rather than rewritten.
This candidate must be reviewed and authorized for release before it changes
published counts. Hashes prove artifact identity, not independent authenticity,
scientific truth or upstream rights ownership.

Project admission recognizes different documented scopes. Prior cross-baseline
review searched all 1057 identifiers and inspected the 57 legacy source-qualified
scopes without an identifier/formula collision. Biological tissues, named products,
formulations and hypothetical periodic crystal models are distinct project scopes;
that check does not establish universal composition/constituent non-overlap.
Phase/site-order and cross-provider equivalence remain unresolved. No extra credit
is granted for 30 related provider groups or 118 calculations. The prior seven
records remain separate and excluded. A future tranche, equivalence adjudication,
or legacy baseline change requires a new reviewed release and updated pins.

The read model remains a separate `materials_project_catalog` add-on distribution.
The unmerged candidate retains core-resource pins to match the appended
experimental data. These are proposed release pins; the released main pins are
unchanged. The query-service baseline manifest also pins the experimental core
bytes. Existing SQLite registry anchors are not migrated or rewritten: an old
baseline is rejected by the new environment. Computed review payloads, held
candidates and excluded examples retain their original bytes and status.

The existing catalog contract fixes `independent_scientific_review` to false.
For the 2026-10-17 increment, selected-source transcription checks and existing article-specific CC BY 4.0
licenses support the SPO-2 density and B10/B30 modulus facts. Prior source-specific
checks and limited NBS reuse findings remain applicable to the earlier nineteen additions. No unresolved concrete source, rights
or identity hold was reported for that increment, and no extra human-signature or
repeat-license-review prerequisite is added. Changing the published formal count
still requires the separately coordinated release above.

Install the add-on explicitly after the exact legacy core: `pip install ./formal-catalog`.
The optional installed-wheel catalog CI installs both packages. The core wheel includes the twenty-seven additional references; historical records and
fixtures are preserved, and only the marked current README material counts are
refreshed. Without the add-on installed,
the legacy catalog works normally and formal status reports unavailable.

## Read interfaces

- `materials-project-catalog`: packaged status, category counts and policy
- `materials-project-catalog --list --offset 0 --limit 100`: packaged records
- `materials-project-catalog --partition reviewed-computed`: all 24 models
- `materials-project-catalog --query Ag2AlCo`: bounded literal lookup
- `materials-boundaries coverage`: 1084 experimental source-qualified identities

In this candidate installation, these interfaces expose the proposed 1108-record
package. Existing formal API names and `admitted-by-packaged-policy` status refer
to its pinned package convention; they do not announce a new main release.

Python callers use `materials_project_catalog.catalog.formal_project_catalog()`
and `select_formal_catalog(...)`. Every read is detached and checked against exact
packaged resource hashes; any resource drift fails closed. Counts are computed
from the records, not hard-coded display totals. Literal selection searches only
ID, name/formula and category, preserves full record metadata, and allows 1–100
records per response. Exact admission IDs distinguish legacy identities from
computed composition buckets. Selected provider model IDs remain in their metadata.

The existing explicit `create_catalog_app()` local opt-in exposes
`GET /api/catalog/project/status` and version-required
`POST /api/catalog/project/list`. The `/catalog` page displays separate legacy
and formal sections, with partition/search/offset controls and complete record
details. Default app startup leaves both local views disabled. The independent
computed-registry API still requires its own explicit registry argument.

API data are captured once per process; restart after an authorized package
release. Failed formal pins disable only the formal view. There is no HTTP write,
file-path selection, admission, refresh or provider-count promotion route. No API
deployment is enabled by this change. The packaged artifact includes metadata
and scalar density only, with no cell vectors, positions, source archives,
calculation files or credentials. No live upstream request is needed.

## Verification

Core tests cover exact count/category arithmetic, preserved predecessor records,
review bytes and full metadata equality, 30/118 provenance cardinalities,
unknowns, detached pagination, selection limits, fail-closed resource drift and
CLI outputs. Optional API tests cover default-off behavior, legacy separation,
stale/missing pins, unknown IDs, bounds, forbidden fields/routes, drift isolation
and safe UI text rendering. Existing full core and optional catalog suites must
also pass. Browser interaction coverage is separate from static UI assertions.
The preceding 073643b full-core evidence is retained as historical validation:
1368 passed and 16 skipped, with no unresolved failures. The 2026-10-17 three-formulation
follow-up used focused validation; its actual results remain recorded in that
handoff. Evidence for the 2026-10-19 four-composite follow-up is recorded separately
in its packets and integration manifest. No new full-suite or remote-CI run is implied. Skips are not passes;
cross-platform conditions and the opt-in external source-cache check remain
unverified where not executed.
