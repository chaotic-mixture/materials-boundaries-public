# Candidate validation, 2026-10-23

Executed on the dot cloud computer in an isolated worktree using Python 3.12.14.
Baseline: `46674771ab851d4c267425b985c8f29c8aea25df`.
Candidate packet commit: `068a3d504783e042e2d7258014ddbf0ce1981db1`.

## Passed

- Candidate materials, reference-property and source schemas, Draft 2020-12
  with format checking.
- Candidate/compiler/integrator replay: **8 tests**, 150.993 seconds.
- Existing four formulation compiler/integrator suites: **30 tests**,
  39.425 seconds.
- Existing exact Nylon predecessor recovery and all adjacency-history tests:
  **6 tests**, 48.171 seconds.
- `scripts/validate_catalogs.py` against the unchanged runtime catalogs:
  41 claims, 123 sources, 16 observations, 5 temperature models,
  12 computational predictions, 1145 material states and
  1156 reference properties; eight executable composite pairs, four languages.
- `git diff --check` and bounded changed-path review.

Total executed unit tests: **44 passed**, no failures or skips.
The candidate tests cover all four source recipe/assay/value/SD tuples, exact
unknown n, method and temperature qualification, the 4.0 mol% cooling exception,
source attribution and checksums, schema-valid ownership, negative
hash/unit/statistic/ownership controls, pending review rejection, immutability,
deterministic compiler/integrator replay and exact predecessor-byte recovery.

The detached integration package proposes **+4 identities, +4 states,
+4 density properties, +1 source and no grade**. Its resulting graph has
1148 identities, 31 grades, 1149 states, 1160 properties and 124 sources.
Inorganic identities would rise from 49 to 53. These are verified detached
package counts, **not live runtime or formal admissions**. Every old catalog
record and byte survives exact predecessor recovery.

Prepared packet SHA-256:
`7bc0fb2ba2dc3512abb95b7bf27b9f25d12c868d4bba041f667421572e5eccde`.
Detached integration package SHA-256:
`e8bd87cd547253333a2912cb61f350898e3a5e8a7bd52b0e6b10cec0b6173306`.
The full detached package is an external local validation artifact, not bundled
in this repository. Its report is retained in `integration-report.json`.
Machine-readable execution details are in `validation-results.json`.

## Scope and next stage

Runtime/formal/query catalogs, their pins, all existing packet and history
artifacts, compiler/runtime code and CI workflow are unchanged. The original
baseline checkout is untouched. No branch was pushed, and no main merge,
deployment or DOI action was performed.

The full repository aggregate suite and six-package installed-wheel/offline
checks were not run in this candidate-only stage. They must be included in the
subsequent experimental-integration validation, alongside exact query/CLI
lookups and old-database refusal checks. This result is not a full aggregate
pass or scientific approval.

The next local stage is to append the exact graph, add a strict predecessor
ledger, refresh current query/formal/ingestion data pins and count projections,
and verify experimental catalog usability. Existing historical hashes and
counts must remain intact through the established preservation chain.
Internal implementation review is not a request for new user authorization;
main merge, deployment and DOI activity remain separately approval-gated.
