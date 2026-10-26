# Materials Boundaries development handoff

Start with the [bounded development kit](docs/development-handoff/README.md) and its [portable onboarding guide](docs/development-handoff/ONBOARDING.md). They provide ready-manifest checks, small-task contracts, independent reviewer prompts and reproducible evidence accounting. The [Chinese operator guide](docs/development-handoff/OPERATOR.zh.md) gives the short operational version.

## Current material boundary

Material expansion is paused. The runtime base for this documentation addition is [`3829ec97e396a73168951b7868b9a03d533948b8`](https://github.com/chaotic-mixture/materials-boundaries-public/commit/3829ec97e396a73168951b7868b9a03d533948b8), on `experimental/delgado2020-pla-pcl-runtime`. It contains **1199 experimental project records = 1175 source-qualified identities + 24 reviewed computed compositions**; 62 unadmitted examples remain excluded. This is not a main release.

At **2026-10-26 06:08:47 UTC**, the [dedicated PLA/PCL run](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/40264855280) had completed successfully, while the [general test run](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/40264855167) was still in progress. Both runs target the runtime base above. **The full material stage is not declared complete.** These observations do not certify a later documentation commit.

The [timestamped pause state](docs/development-handoff/pause-state.json) records the remaining gates. Existing validation evidence is in the [runtime report](experimental/material-batches/delgado-pla-pcl-20261026/INTEGRATION_VALIDATION.md); reported scoped checks must not be relabelled as a full-root pass. This handoff changes no material data, scientific contract, runtime or workflow file.

## Hand off one task

1. Pin separate kit and task checkouts as described in onboarding; old task commits may predate this kit.
2. Obtain a current coordinator instruction. Fill one exact manifest with selected records, consumer-local inputs and hashes, permitted files, literal check argv and a stopping point.
3. Run the read-only preflight. A successful result is an accidental-error guard, not user authorization, a security sandbox or scientific approval. Draft and archival examples are not dispatchable.
4. Give the worker only the selected context. Freeze its output for a different reviewer; a reviewer does not repair and approve their own change.
5. Report exact outcomes and unrun scope, then stop. Do not start the next material batch automatically.

Public access transfers no credentials, private evidence or standing permissions. Main merges, releases, deployments and DOI actions require separate authorization. Reading or publishing this kit does not resume material development or make pending CI successful.
