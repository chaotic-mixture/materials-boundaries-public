# Database development and release checks

`database.yml` runs on branch pushes and pull requests. It executes database
behavior tests, incremental-validation tests, one current-material graph check,
and export/verification of a source-qualified example on Python 3.11 and 3.12.
It does not run historical partitions. A passing database job is not evidence
that mechanics-engine changes or a whole release have passed all regression.

`ci.yml` retains the full regression jobs but now runs only when explicitly
dispatched or when a `v*` tag is pushed. Do not create a release tag merely to save
work. Historical branch-specific workflows remain available on their existing
branches; the new database development branch does not match those filters.

Before approving an engine, schema or broader contract change, reviewers must
identify and execute the affected regression or explicitly dispatch full
acceptance. Publishing a stable release requires the acceptance results for that
exact commit, not a previous green database job. Existing branch-protection
requirements are remote settings and have not been changed by this file.

The old historical tests contain exact file pins. Changes to README, validator
code or CI may require an explicit new historical adapter before a full current
release can pass. Daily development is intentionally decoupled from this work;
no historical pass or SCC admission is implied by these trigger changes.

Workflow dispatch/tag filters follow the official
[GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
Local actionlint validates syntax; hosted execution is separate evidence.
