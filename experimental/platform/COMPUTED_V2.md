# Metadata-preserving computed registry, version 2

This is an opt-in, local-only, independently reviewed metadata contract. It does
not change the 1057 legacy identities or the separately pinned seven-record
`computed-review-recovery/1` tranche. It makes no claim of a reconciled global
unique-material total. No import is automatic, and no HTTP admission, filesystem,
refresh, merge or deployment route is added.

## Distinct identities and counts

`computed-review/2`, `computed-registry/2` and `computed-overlay/2` explicitly
identify the new contracts. A provider-bound `project_material_id` identifies a
model record, not an independently unique physical material. `formula` retains
the source spelling, including unreduced integer formulas. The validator parses
that formula, verifies element symbols, reduces integer coefficients by their
GCD, and requires exact agreement with `canonical_composition` and the
lexicographically ordered `conservative_count_bucket`.

The structured `computed-count-policy/1` rule counts at most one accepted bucket
per reduced composition **within one pinned review tranche**. Equal buckets do
not establish identical phases, site ordering, electronic behavior or global
cross-provider equivalence. An explicit later scientific adjudication and new
versioned policy would be necessary to split composition buckets.

Status and export distinguish:

- `scoped_accepted_identity_bucket_count`: unique accepted composition buckets
- `selected_model_count`: distinct selected provider model identifiers
- `selected_entry_count`: admitted selected source entries
- `related_source_calculation_count`: union of related calculation entry IDs
- `related_source_provider_group_count`: union of related provider group IDs

Related groups and calculations are provenance, never implicit admissions. These
counts cannot be added to the legacy count or the prior seven to produce a
scientifically reconciled global total. Bounded formula-index query completeness
is preserved separately from global completeness, which remains unasserted.

## Metadata and unknowns

The recursive explicit allowlist is in `materials_query/computed_schema_v2.py`.
It preserves composition category and its basis; unknown electronic behavior;
prototype and provider-reported symmetry; unknown experimental existence,
stability, equilibrium and convergence; null temperature and pressure; structured
method; named attribution; exact source URL, references, license and modification
notices; confidence; evidence hashes; and bounded overlap relations.

This version intentionally supports the reviewed hypothetical-model scope only.
Known temperature, pressure, stability or electronic claims require a future
scientifically reviewed contract rather than silently converting unknowns.
DFT geometry-optimization method parameters are not convergence results.

`rights.changes` retains the original source/packet modification notice;
`rights.project_changes` records the project normalization changes. Rights scope
must be reviewed for identity/provenance metadata, scalar density and method.
The validator is a structural and consistency gate, not rights clearance.
Raw geometry, source archives, cell vectors, positions and calculation/potential
files are not schema fields. Geometry hashes and diagnostic scalar checks are
permitted evidence; neither is an invariant physical-material identity.

List, search, exact, property and source endpoints preserve the complete rich
record rather than stripping qualifiers from scalar or attribution projections.
Export preserves the same record bytes under canonical JSON serialization.
Search handles structured method metadata without string coercion of unknowns.

## Trust and migration

Construct `ComputedRegistry(database, review, trusted_review_sha256=...,
input_file_bytes=...)` explicitly. For v2, the exact input-file bytes must hash to
`input_file_sha256`; `trusted_review_sha256` must equal the SHA-256 of canonical
normalized review JSON. Export calls this second anchor
`canonical_review_sha256` and retains `review_version` for request pinning.
A byte pin proves identity, not scientific correctness or reviewer authentication.
Scientific review must independently approve the normalized artifact.

V1 remains available with its historical signature and semantics. There is no
implicit migration or combined registry. A v2 review must use a new database;
opening a pinned v1 database with v2 (or vice versa), replacing the initial
review, or changing the installed legacy baseline fails closed. This preserves
prior admissions rather than reinterpreting them. Re-review a legacy tranche
explicitly before ever assigning a different count policy to it.

The review is copied at initialization, admissions are atomic and idempotent,
SQLite write transactions serialize concurrent replay, and every read validates
stored payloads and ledger anchors. API snapshots remain process-pinned: restart
the explicitly enabled app after local admissions. The 1 MiB canonical review
and export budget remains enforced; API record selection remains bounded.
SQLite detects the covered changes but is not a cryptographically tamper-proof
append-only ledger against an attacker replacing all local state.

## Verification

`query-service/catalog-tests/test_computed_v2.py` adds synthetic tests for formula
reduction, composition counts, unknowns, complete projections, nested allowlists,
trust anchors, atomic/concurrent replay, incompatible migration and storage
changes. Existing v1, baseline and family-relationship tests remain unchanged.
The existing installed-wheel `ci/run_catalog_ci.py` discovers the additive suite
under the offline DNS/socket guard, with no source-package imports.
A separate source-pinned transcription check is required for every real tranche;
synthetic contract tests do not constitute scientific acceptance.
