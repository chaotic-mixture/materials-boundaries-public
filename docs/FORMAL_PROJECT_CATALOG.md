# Formal project catalog admission policy

This additive release read model admits exactly the independently reviewed
24-record computed metadata tranche into a formal **project-scoped admission
count** alongside 1057 unchanged legacy source-qualified identities. It reports
1081 admissions: natural 1010, metal 26, inorganic 28, polymer 14, composite 3.
This is the versioned `formal-project-count-policy/1` convention, not a claim of
1081 universally distinct physical materials, experimentally observed materials,
or scientifically equivalent levels of evidence.

## Two immutable indexes, one explicit project policy

The legacy index preserves every existing identity and all its reference-property,
source, grade and state APIs. Its historic coverage count remains 1057. Legacy
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
example's acceptance pin covers normalized metadata, not formal admission; this
new policy and read model are the separate release admission decision. The
review's earlier preparation-stage wording is retained rather than rewritten.
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

The read model is a separate `materials_project_catalog` add-on distribution. It does not change any Python/JSON resource in `materials_boundaries`,
preserving the existing computed registry baseline and previously admitted local
databases. Both the legacy CLI and legacy integrity checks remain unchanged.

Install the add-on explicitly after the exact legacy core: `pip install ./formal-catalog`.
The optional installed-wheel catalog CI installs both packages. The core wheel and
its historical packaging/README remain byte-identical. Without the add-on installed,
the legacy catalog works normally and formal status reports unavailable.

## Read interfaces

- `materials-project-catalog`: formal status, category counts and policy
- `materials-project-catalog --list --offset 0 --limit 100`: admissions
- `materials-project-catalog --partition reviewed-computed`: all 24 models
- `materials-project-catalog --query Ag2AlCo`: bounded literal lookup
- `materials-boundaries coverage`: unchanged legacy-only quota coverage

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

Core tests cover exact count/category arithmetic, unchanged legacy coverage,
review bytes and full metadata equality, 30/118 provenance cardinalities,
unknowns, detached pagination, selection limits, fail-closed resource drift and
CLI outputs. Optional API tests cover default-off behavior, legacy separation,
stale/missing pins, unknown IDs, bounds, forbidden fields/routes, drift isolation
and safe UI text rendering. Existing full core and optional catalog suites must
also pass. Browser interaction coverage is separate from static UI assertions.
