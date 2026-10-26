# Materials Boundaries development handoff

Start with the [bounded development kit](docs/development-handoff/README.md) and its [portable onboarding guide](docs/development-handoff/ONBOARDING.md). They provide ready-manifest checks, small-task contracts, independent reviewer prompts and reproducible evidence accounting. The [Chinese operator guide](docs/development-handoff/OPERATOR.zh.md) gives the short operational version.

## Current material boundary

Material expansion is paused. The runtime base for this documentation addition is [`3829ec97e396a73168951b7868b9a03d533948b8`](https://github.com/chaotic-mixture/materials-boundaries-public/commit/3829ec97e396a73168951b7868b9a03d533948b8), on `experimental/delgado2020-pla-pcl-runtime`. It contains **1199 experimental project records = 1175 source-qualified identities + 24 reviewed computed compositions**; 62 unadmitted examples remain excluded. This is not a main release.

The [dedicated PLA/PCL run](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/40264855280) and [general test run](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/40264855167) both completed successfully for that exact runtime base. General CI finished at **2026-10-26 07:21:32 UTC**; independent log/aggregate reconciliation completed at **07:30:04 UTC**. **The current seven-PLA/PCL material stage is closed; engineering and material expansion remain paused.**

- Ubuntu Python 3.11 and 3.12: each completed 1887 root IDs, comprising 1869 passes and 18 policy skips; the hosted aggregate reconciled all 8 partition receipts, with zero incomplete IDs.
- Windows Python 3.10 and 3.13: each completed the selected 526-method subset (512 passes, 14 platform skips) plus wheel smoke. This is not full-root Windows coverage.
- Dedicated runtime profiles: each recorded 439 source executions / 435 distinct methods and 585 installed tests, with no failures/errors/skips. Replay methods are already included, not additional passes.

These material results do not certify later handoff or documentation commits. Conditional/skipped jobs are not passes; scopes are not added into a fictitious total.

The [timestamped pause state](docs/development-handoff/pause-state.json) records the closure evidence, exact scopes and continued stop boundary. Existing validation evidence is in the [runtime report](experimental/material-batches/delgado-pla-pcl-20261026/INTEGRATION_VALIDATION.md); reported scoped checks must not be relabelled as a full-root pass. This handoff changes no material data, scientific contract, runtime or workflow file.

## Hand off one task

1. Pin separate kit and task checkouts as described in onboarding; old task commits may predate this kit.
2. Obtain a current coordinator instruction. Fill one exact manifest with selected records, consumer-local inputs and hashes, permitted files, literal check argv and a stopping point.
3. Run the read-only preflight. A successful result is an accidental-error guard, not user authorization, a security sandbox or scientific approval. Draft and archival examples are not dispatchable.
4. Give the worker only the selected context. Freeze its output for a different reviewer; a reviewer does not repair and approve their own change.
5. Report exact outcomes and unrun scope, then stop. Do not start the next material batch automatically.

Public access transfers no credentials, private evidence or standing permissions. Main merges, releases, deployments and DOI actions require separate authorization. Reading or publishing this kit does not resume material development or make pending CI successful.

## Platform check scope

The [fixture-portability correction](docs/development-handoff/PORTABILITY.md) is validated at published kit commit `62e6395be066a2c69f33920c0f8567ee8f7965f3`: Linux default/CRLF profiles passed 46/46, and the no-alias profile passed 45 plus 1 N/A. The native Windows executor reported 45 passes, zero failures and one explicitly not-applicable alias case, with all 5 positive controls and 40 negative gates correct. The original failure remains recorded. See the report for platform, source hashes and evidence-access limits.

**The kit is ready within this verified scope for a newly authorized bounded task, not automatic resumption.** This final status snapshot does not embed a self-referential CI pass: verify its actual remote commit and hosted CI after publication. No extra commit is required merely to record that check.
