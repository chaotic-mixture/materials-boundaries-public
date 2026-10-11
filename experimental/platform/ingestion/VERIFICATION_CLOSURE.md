# Incremental workflow closure verification, 2026-10-11

## Outcome and verification boundary

The Windows catalog error reported in the
[initial incremental verification](VERIFICATION_INCREMENTAL.md) was reproduced on
the exact original `main`, then corrected with one production-code line. The
final source-tree catalog run passed **90 tests, with zero errors, failures or
skips**. This closes that reproduced Windows manifest-key issue. It does not
turn the earlier failing run into a pass or establish a Linux Python-suite pass.

Independent review also identified inconsistent read-only SQLite snapshots and
additional malformed-number/source-metadata cases. All four review findings were
addressed, and the eight added independent closure tests pass. Final regression
verification passed **286 distinct tests, with zero failures, errors or skips**
across seven suites, including the rebuilt installed-wheel catalog and API
checks. Repeated source/reviewer runs are not added to that total.

[verification_closure.json](verification_closure.json) contains the machine-readable
summary and evidence hashes. It also confirms that the exact-main reproduction
and the earlier experimental attempt failed on the same 33 test IDs.

The closure work is based on experimental branch revision
`87205077163a7d2cfb2427cb06d07a9a05775737`, following original `main`
`4c5656cf6ba0ad1a54b736e0568e97abe4815c29`. The exact-main reproduction used a
separate detached checkout, `materials-boundaries-main-repro`. The fixes were
developed separately; the original main revision and its source data were not
rewritten. Test source hashes below distinguish the before/after implementations.

Formal admissions remain **1081 = 1057 legacy identities + 24 reviewed computed
composition buckets**. The 62 additional computed examples remain unadmitted.
The historical pending NOMAD group still requires scientific and rights review
and contributes zero formal admissions. DOI registration and public deployment
remain deferred. This closure performs no push, installs no schedule, changes no
permissions, creates no credentials and performs no new live NOMAD request.

## Exact-main reproduction and Windows correction

The detached exact-main checkout ran the existing optional computed/local catalog
suite on Windows. Its result was **86 tests: 53 passed, 33 errors, zero failures
and zero skips**. Every error ended with
`ValueError: Installed legacy baseline differs from the recovery anchor`.
The source path and SHA-256 in `exact-main-catalog-result.json` confirm that the
original registry implementation was imported, rather than the experimental
implementation or an accidentally shadowing installed package.

`computed_registry.baseline_digest()` keyed its manifest with
`str(p.relative_to(root))`. Windows therefore generated backslash-separated keys,
while the frozen recovery manifest uses POSIX separators. The production fix is
exactly the key expression `p.relative_to(root).as_posix()`. It preserves the
file enumeration, source bytes, SHA-256 computation, pinned manifest and strict
whole-manifest comparison. It does not weaken validation to a count-only check,
regenerate a pin, exclude files or accept missing/extra data.

Four new portability tests invoke the actual validator using both Windows and
POSIX relative-path flavors. They require identical baseline digests for
identical files and rejection of altered bytes, a missing file and an extra
file. These tests do not replace the separate real Linux filesystem check below.
Four existing SQLite-tampering fixture connection sites now use
`contextlib.closing` as well as the transaction context, so Windows file handles
are released before temporary-directory cleanup. Their tampering assertions
remain in place; these are test resource-lifetime fixes.

| Stage | Source registry SHA-256 | Executed result |
| --- | --- | --- |
| Exact original main | `3ba042ca99ae8d4c2ee5927946e6977b3a5e5ddffed4d416cd11f65fefbcbd83` | 86 tests; 33 errors; 0 failures; 0 skips; failed |
| Final corrected source tree | `1d33ab4e9bc62b538e2aa6f2a232a71b112d9003bc9ac3d1883e1b8f528a8a54` | 90 tests; 0 errors; 0 failures; 0 skips; passed |

The four added tests explain the change from 86 to 90. The 90-test result in this
table is source-tree evidence; a separate fresh installed-wheel check is recorded
below.
Evidence: `exact-main-catalog-result.json`, `exact-main-catalog.log`,
`fixed-catalog-final-result.json` and `fixed-catalog-final.log`. Earlier partial
verification attempts remain in the evidence directory and are not added to the
passing-test total.

## Real Linux filesystem check and its limit

The existing WSL2 Linux environment enumerated the baseline files and ran Linux
`sha256sum` against both the exact-main and experimental trees. In each tree,
**64 of 64 expected files matched**, relative keys matched the frozen manifest,
and those keys used POSIX separators. Both trees used the same pinned manifest
SHA-256:
`259d5d0e87635fec6f87ce544c8a252494038cbb1643228eeb685d5501f17897`.

This was a real Linux filesystem/hash-tool check, with zero network requests and
no repository-file changes. It was not a Python test suite. The available
`docker-desktop` WSL distribution had no Python interpreter, and none was
downloaded or installed. **Linux Python tests: NOT RUN.** The missing interpreter
is an outstanding environment limit; the successful hash check must not be
reported as cross-platform runtime-suite completion.

Evidence: `linux-path-check.json`, `linux-path-check.log`,
`linux-path-exact_main.sha256` and `linux-path-experimental_branch.sha256`.

## Independent incremental-workflow review

The initial five independent process/checkpoint tests exposed two failures:
`report` could combine a previous cycle with a newly committed baseline, and
`status` could combine an earlier cycle state with later history. These were
inconsistent reads during a concurrent writer commit. The other three initial
tests passed. A read-only SQLite connection now begins a read transaction before
integrity checks and data access, keeping each offline read in one database
snapshot. Writers still use the existing exclusive update lock and transaction
checkpoints.

The same review added narrow input-integrity fixes:

- JSON exponent overflow such as `1e400` is rejected as a non-finite value before
  it can enter the successful response cache.
- A huge integer density that overflows `math.isfinite()` is quarantined as
  `invalid_density` instead of escaping normalization and breaking recovery.
- Source version, commit, processing time and mainfile fields, and the DFT
  program name, must be nonempty strings rather than merely truthy values.

The read-snapshot and exponent-cache issues belong to the new incremental flow.
The huge-integer and truthy-source-field behavior was inherited from the shared
`nomad_batch.py` normalizer on exact main; this closure tightens those existing
gates rather than attributing all findings to the new implementation.

The completed independent suite ran **8 tests, zero failures, errors or skips**.
It covers real child-process termination and in-flight reservation durability,
real-process lock release, completion-checkpoint rollback and cached replay,
consistent `report` and `status` snapshots across a concurrent commit, exponent
overflow, huge integer density, and nonempty textual provenance/method fields.
The initial failure log is retained alongside the passing log:
`independent-closure-before.log` and `independent-closure-after.log`.

The reviewer subsequently reran the full 86-test ingestion discovery under the
repository's strict offline guard. It passed, and the final independent review
reported no remaining blockers. `independent-review-result.json` records that
command, successful exit status, implementation hashes and the hash of
`independent-ingestion-after.log`. These repeated checks are supporting evidence,
not additional unique tests in the final total.

These are offline fault/invalid-input fixtures. No adverse upstream condition
was induced against the live provider. Strict text validation does not establish
the historical scientific correctness of the source metadata, and finite
positive density still requires scientific and unit/schema review.

A bounded scan-window omission still cannot assert upstream deletion. A validated,
exhaustive public exact-ID recheck is required even to propose
`withdrawal_pending_review`; that proposal never revokes a formal admission.

## Final installed artifact and regression checks

The query-service package was rebuilt as
`materials_boundaries_query_service-0.5.0.dev0-py3-none-any.whl` and installed into
the isolated Windows CPython 3.11 environment. Its wheel SHA-256 is
`4af987e8a04227f18b5b956040c09073da1f39b4a264032e85eace813d4b6689`.
The build and install logs both report success. `pip check` reported no broken
requirements. This closure rebuilt the changed query-service package; it does
not claim a fresh rebuild of all six repository packages.

Both `installed-catalog-result.json` and `closure-api-result.json` confirm imports
from `.venv/Lib/site-packages/materials_query/computed_registry.py`, with SHA-256
`1d33ab4e9bc62b538e2aa6f2a232a71b112d9003bc9ac3d1883e1b8f528a8a54`.
That hash matches the corrected source implementation above. Thus these checks
exercise the newly installed artifact rather than silently substituting the
source-tree registry.

| Final suite | Passed | Failures/errors/skips | Evidence |
| --- | ---: | --- | --- |
| Complete ingestion discovery, including the eight closure tests | 86 | 0 / 0 / 0 | `closure-ingestion.log` |
| Installed-wheel computed/local catalog | 90 | 0 / 0 / 0 | `installed-catalog-result.json` |
| Installed-wheel query service API/transport fixtures | 37 | 0 / 0 / 0 | `closure-api-result.json`, `closure-api.log` |
| Federation provider fixtures | 19 | 0 / 0 / 0 | `closure-provider.log` |
| Lifecycle | 25 | 0 / 0 / 0 | `closure-lifecycle.log` |
| Linked integration and independent component checks | 18 | 0 / 0 / 0 | `closure-linked.log` |
| Formal catalog core and pin/count boundaries | 11 | 0 / 0 / 0 | `closure-formal.log` |
| **Distinct final regression total** | **286** | **0 / 0 / 0** | Sum of the seven rows above |

The source-tree 90-test run, separate independent eight-test run and reviewer's
86-test rerun overlap these suites and are not added again. The exact-main
86-test failure reproduction is also not a passing regression result. The Linux
filesystem/hash check is separate supporting evidence; **Linux Python tests
remain NOT RUN** because the existing WSL distribution has no interpreter.

The 11-test formal catalog suite includes count boundaries, detached pagination
and rejection of pin drift. Formal admissions remain 1081, the 62 unadmitted
examples remain excluded, and the formal catalog snapshot stays
`efea82e0f3ec2847a37807febe6bacffbd9624de2940f6e28bd481f75e9a6c14`.
Build/install evidence is in `closure-wheel-build.log`,
`closure-wheel-install.log` and the local `closure-wheels` directory.

## Historical live evidence and retained artifacts

There were **zero additional live NOMAD requests during this closure**. The
earlier capped experiment remains the complete live evidence: **8 HTTP requests,
18,268 response bytes, zero retries**, two small windows each read twice. It
showed one new pending provider group and a repeat cycle with no input/candidate
increment; it added zero formal materials. Its budgets, timestamps, source IDs,
response/report hashes and limitations remain in
[VERIFICATION_INCREMENTAL.md](VERIFICATION_INCREMENTAL.md) and
[verification_incremental.json](verification_incremental.json). Those observations
are historical and must not be presented as a fresh live revalidation of this
closure patch.

All evidence filenames in this report refer to the local sibling directory
`../incremental-evidence` relative to the repository root. The closure source and
test patch includes no raw provider payloads, SQLite databases, credentials or
structure assets. Logs and result summaries are retained locally; they are not a
published scientific dataset.

The completed local checks and patch are ready for parent-thread review before
any coordinated experimental-branch push. The Linux Python-suite gap must remain
visible until a suitable authorized runtime executes it. Independent
scientific/license review of candidates, the five-category material/property
coverage goal, broader interoperability, additional calculations and interface
work remain outside this closure's completed scope.
