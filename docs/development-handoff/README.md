# Materials Boundaries bounded development kit

Use a lower-cost model for one explicitly bounded task, then obtain an independent review of its immutable output. Reuse the existing formulation-packet compiler and integration manifest; do not create a new framework or historical CI wrapper for each batch.

This public handoff kit provides instructions and local readiness checks, not standing authority, credentials or a new material-development assignment. Material expansion is paused at the stated stage boundary. The kit does not establish that the current stage has finished; see [the timestamped pause state](pause-state.json) and the repository-root [handoff entry](../../HANDOFF.md).

## Start here

1. Read [portable onboarding](ONBOARDING.md) or [the concise Chinese operator guide](OPERATOR.zh.md).
2. The coordinator fills [one task input](task-input.example.json), using [the envelope schema](task-input.schema.json), exact authorized scope and consumer-local evidence. The envelope is a kit format, not a runtime catalog schema.
3. Select one stage, exact allowed files and checks from [the task contract](TASK_CONTRACT.md).
4. Run the read-only [dispatch preflight](dispatch_preflight.py). It refuses draft/archival manifests, unresolved placeholders, wrong input/checkout hashes, unsafe paths and missing stage approvals. It does not execute listed commands or verify user authority.
5. Give the assigned role only the ready manifest, selected evidence, relevant repository instructions and its [prompt](PROMPTS.md). Independent reviewers receive immutable artifacts and cannot repair their own reviewed work.
6. Keep a [result receipt](result.template.json), retain failures and stop at the assigned stage boundary.

The [worked Ewurum example](WORKED_EWURUM.md) and [filled archival manifest](task-input.ewurum.archival.json) show source, identity, count and validation boundaries. They are not a request to replay the batch and are intentionally not dispatchable.

## Scope and reproducibility

The underlying repository contracts were inspected at `437950c414ea340eda340babe7b63dee9fcee535`, tree `1131a517c7dcf6b0bea74b1951df45d1d18a2e45`. The handoff publication base is runtime commit `3829ec97e396a73168951b7868b9a03d533948b8` (tree `2846e3a7e80ca81e96849f7b1f9a6a7db419018a`), containing 1199 experimental project records. Its dedicated CI has passed; its general CI was still in progress at the timestamp in `pause-state.json`. The material stage is not declared closed. The earlier candidate is `73a5d872c210bbde5b3c0548d710869e87626691`. Current task inputs must be pinned independently; do not reuse these historical hashes as a default baseline.

The optional [synthetic preflight cases](check_preflight_cases.py) exercise the kit guards without running project tests or task commands. Project test commands in the guides were verified against repository documentation/scripts, not executed as part of writing this kit. A successful template check is not software acceptance, scientific review, reuse permission or publication approval.

## Platform validation

The synthetic harness has a [documented Windows fixture correction](PORTABILITY.md). It always plans 46 cases but executes 45 or 46 according to interpreter-alias applicability. A negative case must reach its intended rejection gate with a passing positive control. Linux and process-scoped CRLF Git-setting checks are recorded separately from the still-pending corrected native Windows rerun.
