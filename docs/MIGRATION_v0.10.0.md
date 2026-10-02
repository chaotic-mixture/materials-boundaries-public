# Development history: v0.10.0

This was not a public release. The first public release is **0.16.0**; its
[scope](MIGRATION_v0.16.0.md) and [license notices](../THIRD_PARTY_NOTICES.md)
are authoritative for the public package.

The development milestone introduced the separate `temperature catalog`,
`temperature evaluate` and `temperature plot` namespace, a fixed polynomial
evaluator, explicit Kelvin input and provenance-preserving output bundles.
It did not add an executable composite rule or turn source fits into bounds.

The first public release retains this API structure but packages only original
synthetic demonstrations. No former real-material model ID is a public API
alias. Use the IDs and sample inputs in [the current temperature guide](TEMPERATURE_MODELS.md).
Inputs still require finite nonnegative numbers with explicit Kelvin units.
Outside the authored branch range no result is extrapolated. Multiple matching
branches return `ambiguous_overlap` and all branch-specific predictions.

Result/plot bundles must be regenerated from the current public models and
sources. Historical NIST coefficient snapshots and derived outputs are not
included. This choice is conservative pending clarification, not a finding of
prohibited reuse. See [the third-party notices](../THIRD_PARTY_NOTICES.md).
