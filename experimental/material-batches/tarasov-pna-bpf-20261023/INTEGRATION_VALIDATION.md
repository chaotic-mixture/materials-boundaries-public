# Tarasov runtime validation ledger

This ledger records completed local validation and preserves unsuccessful or
interrupted attempts. Independent parent review is still required before any
push; this record is not approval to publish. The exact outcomes,
method IDs, input hashes and retained-log hashes are in
[integration-validation-results.json](integration-validation-results.json).

## Confirmed local results

| Check | Actual result |
| --- | --- |
| Complete source modules | 188 passed across 18 complete modules; 0 failures, errors or skips in these final module runs |
| Class-count recovery | 6 prior individual successes plus 2 fresh single-case passes; no complete 8-method rerun is claimed |
| Targeted aggregate | All 196 distinct target methods have passing evidence across the recorded segments; 0 skips |
| Fresh installed suites | 544 passed across all 8 groups; 0 failures, errors or skips; 647.218 seconds |
| Installed CLI selections | 40 exact outputs: 5 records, 4 languages, JSON and text |
| Scope validation | Passed; 1.454 seconds |
| Separate full legacy core-wheel smoke | Passed on the new runtime wheel; exit code 0; 1,157.359 seconds within the 1,500-second cap |
| Full core inventory | 1,778 methods; target is 196; the other 1,582 were not run and are neither passes nor skips |

The installed groups contain query 220, formal 13, ingestion 198,
relationships 14, provider 19, transport 37, lifecycle 25 and integration 18
methods. Import origins, `pip check`, offline guards and the separate
installed CLI/API smoke passed. Existing CLI subprocess parity coverage is
retained. Method totals do not include synthetic tests invoked by runner
regression tests, duplicate focused checks, historical candidate checks,
CLI output counts or catalog record counts.

The six wheel hashes bind the installed benchmark. Independent read-only
review matched all 102 packaged runtime files to the current checkout and
verified their wheel RECORD digests; the core METADATA README matches after
CRLF normalization. Subsequent edits concern historical test recovery, the
CI budget/path allowlist, and documentation or reports. Runtime package
implementation and data bytes have not changed since that benchmark. This
does not claim that later test/helper/report edits were in the earlier run.

The source tests ran in separate complete-module processes. Their test-file
hashes are recorded. Historical document and workflow recovery were repaired
between segments; this is not represented as a single run on one final
immutable tree. The two remaining class-count methods completed in fresh
processes in 205.656 and 1.187 seconds. Along with the six successful methods
in the interrupted log, they complete the exact eight-method inventory. This
does not convert the interrupted process into a successful complete run.

The full runtime-wheel smoke completed in a separate fresh installation.
All selected local validation is complete, with the exact execution boundaries
above. Independent parent review of the final implementation and immutable
bundle remains required. No hosted Tarasov CI run exists.

Code checkpoint `3f16d45bf7a50d0c068f8557ebdecbc3d8482333` preserves the
implementation before these final reports. The eventual enclosing commit and
external bundle receipt bind these reports without a self-referential commit
hash. Neither local checkpoint grants publication approval.

## Failed and interrupted attempts

The original composite preservation run executed 13 methods and reported
6 failure events across 5 methods. Its document recovery chain did not yet
recognize the new Tarasov README and attribution images. After the finite
recovery repair, the same complete 13-method module passed. The historical
family adjacency CI module then reported 1 failure among 6 methods because
the current workflow was passed directly to the earlier Bruns ledger. The
minimal successor projection repair passed all 6 methods. Original failure
IDs and logs remain separately recorded; reruns do not erase them.

The historical candidate's 900-second full core-wheel smoke timed out. A
separate instrumented diagnostic failed with Windows access violation
`0xC0000005`; that cause remains unresolved and it did not reproduce the
original timeout. An unchanged baseline control completed in 1,176.344
seconds. That duration does not establish the exact original timeout cause
or stop location. The first new-runtime smoke had no terminal result after
the execution disconnect; a stale `running` receipt is not a pass or proof
of a timeout. No matching task process remained when execution resumed.

The resumed full legacy core-wheel smoke passed in 1,157.359 seconds, with
exit code zero and its final structured output. It freshly installed the
new runtime wheel SHA-256
`b9a93ab32449f8a5ed8f24f9c90304fbaf8bfc9bad339db50e15ceb7bd77fe16`.
Its selected historical summary is unchanged, so its log hash equals the
baseline control log hash; the distinct wheel hash was checked before this
new installation. This legacy smoke contributes no additional Tarasov test
method count and does not erase any previous failure or interruption.

The first six-wheel build failed with sandbox `WinError 5` during metadata
atomic rename. The native offline build subsequently passed. These attempts
are recorded separately. No assertion, skip contract or CLI subprocess check
was removed to obtain a pass.

## Narrow recovery repairs

Document recovery prepends one exact image ledger for the new README and
attribution text, plus an independent ledger that recovers the helper's
original bytes. The original seven document ledgers, their ordering, original
helper hash, count normalizer and historical assertions remain unchanged.
Existing test methods gained subtests that reject unknown bytes, changed
content, wrong ordering and forged ledger content.

The workflow repair changes only the input to the existing Bruns recovery:

```diff
-            (ROOT / '.github/workflows/ci.yml').read_bytes(),
+            successors.project_successor_file(
+                '.github/workflows/ci.yml', (ROOT / '.github/workflows/ci.yml').read_bytes(),
+                before=successors.BRUNS_BATCH_ID),
```

It preserves the following Bruns recovery and every original assertion.
Repeated prefix replay in `tests/material_append_history.py` is not optimized
in this batch. Those historical test helpers are not imported by the fresh
installed smoke, so their cost is not evidence for the original smoke cause.

## Count and publication boundaries

The installed local projection is 1,177 = 1,153 source-qualified identities
plus 24 unchanged reviewed computed records. Source-qualified categories are
natural 1,010, metal 32, inorganic 53, polymer 30 and composite 28. These include
conversion-derived reference properties and must not all be called direct
measurements. The last verified published experiment is 1,172 and main is
1,081. The 62 excluded computed examples remain excluded. Historical candidate
39-test results remain separate from this runtime validation.

Source caveats, nominal formulation labels, missing statistics, `66.0` MPa
precision and all three source discrepancies remain unchanged. Source and
rights review is not independent scientific review or experimental replication.

## Reproduction

Use the checkout's declared supported Python and existing dependency locks.
The commands below work in PowerShell and a POSIX shell after the environment
has been prepared. The wheel/dependency paths are local example destinations;
no network, credentials or raw source assets are required for the offline run.

```text
python -X utf8 scripts/validate_catalogs.py
python -X utf8 scripts/run_tarasov_pna_bpf_ci.py --validate-scope
python -X utf8 scripts/run_tarasov_pna_bpf_ci.py --targeted-core
python -m pip --isolated wheel --no-index --no-deps --no-build-isolation --wheel-dir wheelhouse . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform
python -X utf8 scripts/run_tarasov_pna_bpf_ci.py --wheel-dir wheelhouse --dependency-dir dependency-wheelhouse
python -X utf8 scripts/check_wheel_metadata.py wheelhouse/materials_boundaries-0.35.0-py3-none-any.whl
```

The final full command is a separate legacy core-wheel smoke. The targeted CI
job's 90-minute ceiling does not claim a full 1,778-method core run. Its frozen
technical validation status grants no publication authority. Independent parent
review of the final immutable implementation is required before any push.
