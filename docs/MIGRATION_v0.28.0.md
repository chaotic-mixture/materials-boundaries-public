# v0.28.0: offline single-case composite workflow

The release adds `composite init`, `composite report`, `composite verify`, four
language static reports and a closed composite-report 1.0.0 bundle. It introduces
no scientific records, calculation rules, source review upgrades or runtime
dependencies. There remain 41 claims, 57 sources and exactly eight executable
composite rules. Claims 1.13.0, sources 1.0.0, instance 1.0.0 and evaluation 1.1.0
schemas are unchanged, as are earlier APIs and outputs apart from the package
version label. See [complete workflow/API/limits](COMPOSITE_WORKFLOW.md).

Existing valid inputs can be passed directly to `composite report`. The original
instance and unchanged evaluation payload are saved alongside the canonical
report. Fractions are evaluated exactly as supplied, with the existing explicit
normalization policy; this route does not substitute a fraction sweep. Existing
literature-model input evidence is preserved without generic E/ν intake editing.

The new `verify` command returns 4 for an altered or stale report and 2 for
malformed input. It compares the complete rebuild, not just hashes/schema.
It never silently migrates. A future package/catalog change may make a saved
bundle stale; preserve the matching installed version for exact replay or
explicitly generate a new report in a separate directory from the original
input. Successful replay is software reproduction, not scientific certification.

Destination directories must be new or empty and have an existing parent.
Symlinks/parent traversal are rejected. Staging stays within the destination;
ordinary exceptions roll back invocation-owned outputs and the manifest is
published last. This is not crash-safe or concurrent-writer transactionality.
No hosting, source PDF/figure redistribution, external sharing, CSV, measurement
uncertainty analysis, property inference or new scientific model is introduced.
