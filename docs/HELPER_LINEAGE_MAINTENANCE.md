# Test-helper lineage maintenance (2026-10-03)

This repair closes a test-only helper self-lineage gap. Package and citation
version remain 0.23.0. Runtime code, scientific catalogs, scientific assertions,
schemas, examples and every pre-existing fixture are unchanged. Passing these
checks is not independent scientific validation, experimental confirmation or
reuse clearance.

The first public helper entered Git at
[`6476616c662fe6ff5f6b1ecf68800653f9aad166`](https://github.com/chaotic-mixture/materials-boundaries-public/commit/6476616c662fe6ff5f6b1ecf68800653f9aad166),
blob `7e36208d4afcc95911ea4c9a5347c59d80713793` (6,497 bytes).
Its parent contains only LICENSE. Reversing the four exact public-bootstrap edits
reconstructs the 5,012-byte helper whose SHA-256 matches the preserved v0.16
ledger endpoint. That predecessor is **reconstructed**, not a retrieved earlier
public Git blob. This is a current review of the omitted edge, not a claim that
it was reviewed when originally introduced.

`tests/fixtures/helper_bootstrap_bridge_20261003.json` retains the public source,
exact reversal edits, exact forward diff, public commit/blob identifiers and
compact source edits reproducing every later public helper endpoint. It includes
only source-code evidence and existing fixture/function digests, not private
archives, publisher works or excluded scientific datasets. The helper pins this
artifact and applies its single-file edge immediately after PUBLIC_BASELINE and
before the observation ledger. All old ledger guards remain in place.

`tests/fixtures/helper_maintenance_updates_20261003.json` separately records the
current helper and direct-guard transitions from the accepted public 0.23.0
snapshot. The temperature-plot preservation test applies only this current tail
after its unchanged direct baseline and reviewed ordering deltas. The full
historical helper API still starts at its first applicable recorded predecessor;
it is not a resume-from-any-release API.

The new regression test pins the current tail and compares both successor hashes
to actual file bytes. The reviewed repository snapshot is the external trust
anchor; these mutable files do not authenticate themselves. This acyclic layout
avoids embedding the helper's own successor hash in its source. Future changes
need another explicitly reviewed transition, not a historical fixture rewrite.

Run the focused checks with:

```sh
python -m unittest discover -s tests -p test_helper_lineage.py -v
python -m unittest discover -s tests -p test_temperature_plot_preservation.py -v
```

The full catalog, production suite, mixed appendability suite, isolated wheel and
public-exclusion checks remain separate acceptance requirements.
