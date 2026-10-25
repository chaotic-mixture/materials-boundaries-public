# Curaua runtime integration validation

The reviewed candidate `fa170104195e573c868c57006ac77e7d866c28e9` was appended locally and validated on
native Windows CPython 3.11.0. The tested implementation is
`04f4c7be4b67f29df4eae0f82a36f8f8ef592846`, tree `09b1c5c156c55f61585ad86b6bb5abb51fba3e41`. The checkout was clean and unchanged before and after
each final bounded run. A later documentation-only commit records these results;
all 67 changed non-report files are byte-bound in `integration-validation-results.json`.

This is a local experimental result pending independent runtime review. No push,
main merge, deployment, DOI registration or raw-asset publication occurred.

## Executed validation

| Scope | Passed | Failures | Errors | Skips |
| --- | ---: | ---: | ---: | ---: |
| Candidate | 18 | 0 | 0 | 0 |
| Append/history | 12 | 0 | 0 | 0 |
| New CI contracts | 15 | 0 | 0 | 0 |
| Complete selected legacy modules | 60 | 0 | 0 | 0 |
| Core partition contracts | 50 | 0 | 0 | 0 |
| Existing replay gate | 70 | 0 | 0 | 0 |
| Release metadata | 5 | 0 | 0 | 0 |
| Fresh installed groups | 569 | 0 | 0 | 0 |

The 155-method source run completed as one invocation with five fresh-process
groups, not one uninterrupted Python test process. The 70-method replay run is
separate and overlaps four source-selected methods. The five release metadata
methods are separate. These execute 66 distinct root IDs;
1821 of the 1887 root IDs were not executed locally. Discovery of
all 147 modules and 1887 IDs and the four disjoint partitions is not execution.
No skipped or merely discovered method is counted as a pass.

Six wheels were built offline at `05688153b9859fafa8089bc1e7df6ed6d99338a3`.
The full existing core wheel smoke passed in a separate fresh isolated
environment in 1152.344 seconds. A subsequent test-only expectation correction
preserved all six wheel hashes and all 319 protected build/smoke input files;
the exact seven changed test/history paths are recorded in the JSON ledger.
No package rebuild or repeated core wheel smoke was needed. All eight complete
installed groups passed in another fresh offline environment: 241 query,
13 formal, 202 ingestion, 14 relationships, 19 provider, 37 transport,
25 lifecycle and 18 integration methods. All 561 prior installed IDs remain;
the eight additions bring the total to 569. Installed package origins, resource
hashes and `pip check` passed. Existing independent API/CLI smoke and actual CLI
subprocess coverage remain intact. An additional 24 Curaua CLI outputs were
checked by full JSON equality and text value/caveat checks, not whole-text byte
equality. They are outputs, not distinct identities or additional test methods.

Catalog validation, exact append and reapplication checks, frozen scope,
runtime/query pins, stale-store rejection, candidate/source unknowns, prior
fixture recovery and strict negative cases passed. Exact machine-readable IDs,
durations, log hashes, budgets and input hashes are in the adjacent JSON ledger.

## Reproduce the checks

Use the pinned build and dependency requirements and the six package build
commands in `.github/workflows/curaua-runtime.yml`. On Linux or Windows, from
the checkout and an environment with the declared dependencies:

```text
python -X utf8 scripts/run_curaua_runtime_ci.py --validate-scope
python -X utf8 scripts/run_curaua_runtime_ci.py --validate-inventory
python -X utf8 scripts/run_curaua_runtime_ci.py --source-tests
python -X utf8 scripts/run_history_replay_latest_ci.py --tests
python -X utf8 scripts/validate_catalogs.py
python -X utf8 -m unittest discover -s tests -p test_release_metadata.py -v
python -X utf8 scripts/check_wheel_metadata.py <fresh-core-wheel>
python -X utf8 scripts/run_curaua_runtime_ci.py --wheel-dir <six-fresh-wheels> --dependency-dir <locked-dependency-wheels>
```

Angle-bracket arguments are local directories/files produced by the checked-in
workflow; they are not private paths or remote services. Full history is
required by the existing preservation checks. The wheel runner creates new
isolated environments and disallows installed-package fallback to the checkout.
Run durations above are observations, not portable timeout guarantees.

## Earlier unsuccessful attempts retained

Sandbox TestClient setup stalled in native Windows socketpair acceptance before
methods began; bounded task-owned processes were stopped, and subsequent native
runs passed without changing system settings or test contracts. An initial new
product test confused primary polymer 30 with overlapping family 31; the
existing PBS/lignin overlap was verified and only that new oracle was corrected.
An initial new document test wrongly required normalized prose to differ;
requiring its exact predecessor digest fixed the oracle while keeping the
false-count rejection.

The first full replay run on `47e46eebf8e82de7a70abfac0e0a95c79a5c9fbe`
completed 70 methods with 68 passes and two failed subtests. One old byte-equality
caller needed the finite pinned benchmark projection. The other already rejected
changed input but returned a different assertion message. The narrow repair
retains the original baseline equality and error contract, chains the original
rejection, and adds no fallback. The failed immutable commit and logs are
preserved. The repaired source and complete replay suites were rerun rather
than relabeling the earlier failure as a pass.

The first installed attempt on `05688153b9859fafa8089bc1e7df6ed6d99338a3`
passed query 241 and formal 13, then ran ingestion 202 with 199 passes and three
failures; the remaining 113 methods were unstarted. Two current overlap counts
and a snapshot anchor were stale. Complete before/after identity-set comparison
proved that the old 1185 classifications were unchanged and only the three new
text-qualified identities were added as unable to compare. Direct Git-object
comparison verified the current data anchor and material hash. Two related
current-hash assertions were also stale, one hidden by the first failing anchor
and one in a previously unstarted relationship method. Exactly five literals
in three tests were corrected, without changing any production behavior.
Historical predecessor hashes remain recoverable through the finite ledger.
The selected four methods passed, then the complete 155, 70 and 569 groups were
rerun on the final tested implementation. The failed attempt remains recorded;
its 113 unstarted methods were never counted as skips or passes.

## Scientific and release boundaries

The exact runtime delta is three source-qualified composites, three states,
three apparent-density properties and one source, with zero new grades or
computed records. Local totals are 1164 source-qualified plus 24 unchanged
computed records = 1188; main remains 1081. Primary source-qualified categories
are natural 1010, metal 32, inorganic 59, polymer 30 and composite 33. The 62
unadmitted computed examples remain excluded.

The nine approved candidate artifacts, 122 historical fixtures, full generic
partition workflow and 1887/70 frozen inventories remain intact. Test-only
historical projections retain old hash assertions and reject unknown images.
They do not alter runtime scientific claims or add a cross-call cache. There is
no claim of atomic protection against concurrent input edits within one call.

Independent review verified the official XML and facts; its publisher PDF
request returned 403. PDF hashes and page checks remain producer evidence.
Unknown CV units and density age remain explicit. Finite identity screening
is not global equivalence proof or independent scientific replication.

Hosted CI, other Python/OS combinations, the remaining root IDs, new real
17-layer performance cases and live-provider checks remain unrun. No new
performance factor is claimed. The original full core partition workflow must
complete after any separately reviewed experimental publication.


## Kapoor historical inventory correction

The published parent `434b7875dae88f95f6c5c279a29c4f562ec57a08` passed both Curaua-specific hosted jobs: each
platform completed 155 source and 569 installed methods, zero failures,
errors or skips, plus the independent CLI/API smoke. These jobs did not run
the separate 70-method replay profile.

The unchanged general workflow exposed a historical test input boundary bug.
Both Python 3.11 and 3.12 partition 0 jobs ran all 459 root methods: 439 passed,
18 policy skips, one root error and one invalid root outcome. The latter
contains a query subtest error and a root error, so the three unittest error
records belong to two root methods. The original failed logs, receipts and
journals are retained and hashed in the accompanying JSON. The other six
Ubuntu partitions and two Windows general jobs remain under observation at
this report; they are not recorded as passing here.

The Kapoor regression oracle received 241 current query IDs but validated its
Tian successor's frozen 233-ID boundary before its own 226-ID historical
boundary. The correction applies the existing exact Curaua checkpoint only
to the private Kapoor test runner's recursive current-ID read. It verifies
all current IDs, the exact file list and pinned bytes before projection. The
original Tian fingerprint, Kapoor historical checks, all 30 Kapoor methods
and 131 assert calls remain unchanged. Ordinary and predecessor reads and
the shared Tian module are unchanged; context cleanup restores the local
function on success and exceptions.

Tested implementation: `4031144bfa8679de7d3d2eb2e35373d4911ec098`; tree `ec3539837e3d903a3ccd35ad8f40d154fb91e2b8`. The eight-file
change adds one finite recovery entry for the exact original Kapoor test
image, preserves all 48 prior entries, and updates dependent hashes plus
one approved path. All 122 fixtures, material catalogs, workflows and frozen
1887/70/155/569 method inventories remain unchanged.

Native Windows CPython 3.11.0 validation used bounded fresh processes:

| Stage | Actual methods passed | Elapsed seconds |
| --- | ---: | ---: |
| Full Kapoor module, Tian imported first | 30 | 64.016 |
| Reverse import order and nested guards | 5 | 25.016 |
| Curaua source groups | 155 | 270.093 |
| Replay regression profile | 70 | 56.015 |
| Scope, inventory, catalog checks and metadata | 5 metadata methods | 17.000 |

Every final stage had zero failures, errors and skips and an identical clean
checkout before and after. This is segmented execution, not an uninterrupted
full suite. Overlapping methods are not additional coverage: 265 executions
represent 256 distinct methods, including 96 of 1887 root IDs; 1791 root IDs
were not executed locally for this repair. The original two-method failure
reproduction and the earlier three-method working-patch check are retained
separately and do not inflate final-commit coverage.

The nested historical call rejects missing, extra, duplicate, substituted or
reordered IDs, changed known bytes and an extra empty test file. Tests also
cover conflicting historical modes, exception restoration and unchanged
shared successor functions. Scope, exact inventories and catalog validation
passed. All 319 packaging/core-smoke inputs match the earlier tested bytes;
the 569 installed methods and full wheel smoke were not rerun for this
test-only repair. Earlier local and hosted results remain evidence for their
respective commits, not new repair executions. No hosted repair result exists.

No material growth accompanies this correction: the experiment remains
1188 = 1164 source-qualified identities + 24 reviewed computed records; main
remains 1081. The source's unknown CV units and density measurement age, and
the independent PDF access 403, remain unchanged limitations. The correction
is locally committed for independent review and has not been pushed.
