# Experimental integration, 2026-10-19

This branch merges the complete histories of the reviewed data integration
`5a11cac383f2a7dc87500e24f22ad0b1f9d9c1d0` and the incremental, compatibility,
and hBN projection work at `7c749ab9ff8b92c9c25247d1f38108fbf4ad8232`.
It is an experimental integration, not a main release or deployment.

The data parent's catalog bytes and baseline pin are unchanged. The project
summary remains **1103 identities = 1079 source-qualified catalog entries + 24
reviewed computed compositions**, distributed as natural 1010, metal 34,
inorganic 38, polymer 15, and composite 6. The 62 unadmitted computed examples
remain excluded. Projection nodes, candidate records, calculations, observations,
and repeated imports do not add formal identities. The hBN projection adds zero
admissions; its retained historical review records keep their original counts.

The computed registry retains the current `f1a1e3e379f9b7befba595b54477f15a26364548798b28dd65be8bc4326c0df4`
baseline pin and exact compatibility rules for the accepted evidence-dedup and
presentation code successors. Historical data and historical pins cannot replace
this anchor. Three additional regressions verify old-pin rejection, old-data
rejection, and rejection of an old-data database without modifying it. Existing
regression IDs remain required by CI.

The ingestion overlap boundary also binds the current data parent's exact bytes
and 1103-project/1079-source counts. Saved historical stores retain their original
scope in read-only status, reports, and comparisons. A historical store cannot
silently resume acquisition against the current catalog; use a new state
directory for the current boundary. No saved scientific evidence is relabeled.

The incremental NOMAD command, persistent checkpoints, retry and request budgets,
deduplication, withdrawal/change reports, and review gates are documented in
[INCREMENTAL.md](../experimental/platform/ingestion/INCREMENTAL.md). The
[offline CI guide](../experimental/platform/ci/README.md) describes the strict
platform checks. The integration branch is explicitly allowed by that workflow;
its permissions, job matrices, and pinned actions are unchanged. The core CI
workflow is byte-identical to the data parent.

Local acceptance uses a frozen source manifest, focused regressions, strict
platform checkers, a fresh installation of six local wheels, and one final full
core regression. Execution receipts, actual pass/skip counts, and hosted CI
results are separate evidence; this document does not claim execution before
those checks complete. This integration does not fetch new scientific data,
register a DOI, deploy a public service, create credentials, change permissions,
or alter scientific or license approval boundaries.
