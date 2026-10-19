# Incremental CI discovery and independent review, 2026-10-11

This follow-up closes CI coverage gaps on top of reviewed product revision
`2608f80873a4107a7ddd6a5f784c0bba6f6bfedb`. The product implementation and test
cases are unchanged. The Library batch remains `not_prepared`; its original
artifacts were not replaced or uploaded. No branch was pushed and no live NOMAD
request was made.

## CI gaps and narrow correction

The existing `test*.py` discovery could find every added test, but two gates were
insufficient:

1. The experimental workflow allowed only `experimental/platform-integration`.
   A push to `experiment/nomad-incremental-review` would not run it. The general
   workflow only discovers the core test tree, so it was not a substitute.
2. Ingestion still required only 25 tests, catalog only 85, and API only 21.
   Losing all 61 new ingestion tests or all four portability tests could still
   satisfy those old minima.

The workflow now also allows the exact incremental experiment branch for scoped
pushes, PR targets and its manual job guards. Main, the general CI workflow,
permissions, runners, Python matrix, path filters and pinned actions are unchanged.
Static YAML parsing verified both branches, job commands, manual guards, read-only
permissions and Ubuntu/Python settings. This is not GitHub scheduler execution.

The minima are now ingestion 86, catalog 90 and API 37. The shared discovery
checker also requires all 65 new IDs in
[required_test_ids.json](required_test_ids.json), rejects duplicate IDs and loader
errors, prints each actual discovery as JSON, and requires the executed count to
equal the discovered count. Existing rejection of failures, errors, skips and
expected failures remains in force. Additional tests are allowed; unrelated
additional tests cannot substitute for a required regression.

## Actual local CI-checker execution

The following revised checker commands ran outside the source checkout using the
existing isolated Windows CPython 3.11.0 environment and installed local wheels:

```text
check_offline.py provider-fixtures
check_offline.py api-fixtures
check_offline.py lifecycle
check_offline.py linked-integration
check_offline.py nomad-ingestion
check_catalog.py --wheel-dir <six-local-wheels>
```

| Suite | Discovered | Executed and passed | Skipped |
| --- | ---: | ---: | ---: |
| Provider fixtures | 19 | 19 | 0 |
| API fixtures | 37 | 37 | 0 |
| Lifecycle | 25 | 25 | 0 |
| Linked integration | 18 | 18 | 0 |
| NOMAD ingestion | 86 | 86 | 0 |
| Local/computed catalog | 90 | 90 | 0 |
| Formal catalog | 11 | 11 | 0 |
| **Distinct total** | **286** | **286** | **0** |

All seven suites had zero failures and errors. These reruns do not increase the
previously reported distinct total. The catalog checker also verified all six
wheel licenses and installed package origins. The updated query-service wheel
was checked byte-for-byte against its source. This follow-up reused the existing
verified wheels; it did not rebuild dependencies or run the fresh Linux runners.

Ingestion used the repository's unchanged strict socket audit guard. Windows API
checks used the previously documented verification-only exception for Python's
internal loopback `socketpair`, with external DNS/connect/sendto still blocked.
The production CI guard was not changed.

[verification_incremental_ci.json](verification_incremental_ci.json) records all
286 discovered test IDs, counts by module, corresponding successful executions,
test-log hashes and independent gate evidence. Ingestion comprises the original
25 batch tests plus 37 incremental, nine independent protocol, seven boundary and
eight independent closure tests. Catalog includes all four path-flavor integrity
tests. The latter reject changed bytes, missing files and extra files on both
Windows and POSIX path flavors, while requiring the same digest for identical
files.

## Independent review evidence

The independent reviewer rediscovered all 286 IDs under the strict offline guard
and verified that the required inventory contains exactly the 61 new ingestion
IDs plus four portability IDs. For each required ID, the reviewer removed it
from the discovered suite and added an unrelated case to preserve the count.
All **65 of 65** substitutions failed with the missing-ID gate. Duplicate IDs,
loader errors and reduced counts each failed in both protected suites: **six of
six** additional negative probes. These are discovery-gate probes, not additional
product tests in the 286 total.

The independent evidence file is
`../incremental-evidence/independent-ci-discovery-review.json` relative to the
repository root, SHA-256
`53b3294feb8bc85e0440a8ad4f7e083a01a362c34345a1881694cd5f4a88f6c7`.
The independently authored probe was rerun after normalizing the inventory's
line endings to LF; its parsed IDs were unchanged and all 71 probes still passed.
No unresolved blocker was found in the CI patch.

The final product review also found no unresolved blocker after these four P2
findings were fixed and independently rerun:

| Finding | Origin | Fix and regression evidence |
| --- | --- | --- |
| Report/status mixed data from concurrent commits | New incremental flow | Read-only `BEGIN`; both snapshot tests commit a writer between reader selections and retain a consistent snapshot. |
| JSON exponent overflow entered the successful cache | New incremental decoder | Reject non-finite parsed floats before caching; `1e400` and `-1e400` leave no accepted raw cache and remain reportable/abandonable. |
| Huge integer density escaped normalization | Shared normalizer on original main | Convert `math.isfinite` overflow into `invalid_density`; reporting and a zero-delta repeat cycle still work. |
| Non-string source/method fields passed truthiness gates | Shared normalizer on original main | Require nonempty strings; 25 field/value combinations remain excluded with zero admissions. |

The reviewer additionally verified:

- **Checkpoint atomicity:** request and byte reservations commit before dispatch.
  An actual child-process `os._exit(27)` preserves the reservation. Failure after
  the final baseline write but before the complete-cycle checkpoint rolls back
  the baseline; committed responses replay without another request.
- **Concurrency:** a real second process cannot acquire the writer lock. Killing
  its owner releases the OS lock. Read-only transactions address the separate
  report/status consistency issue.
- **Withdrawal:** a missing bounded-window ID is directly rechecked. Only an
  exhaustive, validated exact-ID response proposes `withdrawal_pending_review`.
  Incomplete/failed rechecks cannot advance the baseline or assert deletion.
- **Idempotence:** unchanged inputs produce zero input and candidate delta;
  identical duplicates coalesce, conflicting duplicates remain held, and known
  identity remaps cannot turn calculations into newly counted materials.
- **Property, unit and rights gates:** missing properties, wrong explicit units,
  unsupported quantity shapes, missing attribution, license changes and known
  formal/unadmitted identities remain excluded. Automation does not replace
  scientific or license review.

## Remaining execution boundary

Ubuntu 24.04 / Python 3.11 and 3.12 Actions jobs have **not run** for this patch.
The local WSL environment still lacks Python. Earlier real Linux filesystem
checks of 64 frozen files per tree are separate evidence and are not Linux
Python-test passes. The parent can coordinate the already-authorized experimental
branch push and then inspect both jobs for both interpreters; this does not
depend on Library delivery.

Formal admissions remain **1081 = 1057 + 24**; the 62 additional examples remain
unadmitted. No DOI, public deployment, production admission, credential or
permission change is included.
