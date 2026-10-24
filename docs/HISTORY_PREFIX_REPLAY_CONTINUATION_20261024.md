# Historical prefix replay: bounded continuation

The implementation is unchanged from `a6d3e5e384c7cb6cc29c5d56ba51d6bd959dff96`, based on `196995256836db2d8f870ac9a91f664bfdd03e7f`.
This continuation adds verification records only. It preserves the original
checkpoint document and ledger, including every failed or incomplete attempt.
No catalog, workflow, installed smoke, CLI coverage, or historical assertion
has changed. The isolated original catalog remains 1,177 records; this branch
does not replace or reduce the separately published Tian catalog.

## Completed correctness checks

Native Windows CPython 3.11.0 passed 73 methods in this
continuation: 35 differential/bridge/budget methods, the 37 previously unrun
historical methods, and the previously timed-out PUR byte-projection method.
There were zero failures, errors, or test skips in these completed runs.
Two exact inventory checks remain supported by the unchanged original logs.
Together this is 75 distinct methods: 35 explicit new methods and all 40
planned existing methods. Repeated methods are not counted twice. Execution
used multiple fresh processes, not one uninterrupted full suite.

The single diagnostic PUR retry completed in 649.903
process seconds within its fixed 1,800-second budget. The method, assertion
bytes, and implementation were unchanged. Progress observations and 120-second
stack snapshots were retained locally. The earlier 600.018-second timeout
remains an incomplete attempt, not a retroactive pass. This successful retry
does not establish a unique explanation for the earlier elapsed time.

All 111 baseline fixture files, seven code/test pins, catalog inputs, packets,
and ledgers remain byte exact. Unknown bytes retain historical rejection,
corrupt disk graphs cannot be repaired by supplied raw bytes, and repeated
calls reread inputs. No cross-call cache was added.

## Complete finite benchmark inventory

All nine cases now have directly byte-equal old/new outputs and unchanged
input hashes. The current-materials case retains the original observation;
the other eight were measured sequentially after correctness work ended.
Each row is one observation, with old measured before new. Times include
instrumentation and exclude historical-image preparation and input hashing.
Filesystem caches and unrelated machine load were not controlled.

| Case | Recovery calls old / new | Catalog reads old / new | Packet reads old / new | Seconds old / new |
| --- | ---: | ---: | ---: | ---: |
| current-materials | 105 / 27 | 42 / 3 | 196 / 40 | 172.786 / 46.853 |
| current-properties | 105 / 27 | 42 / 3 | 196 / 40 | 174.498 / 47.844 |
| current-sources | 15 / 9 | 15 / 3 | 25 / 13 | 24.864 / 14.394 |
| after5-materials | 90 / 22 | 27 / 3 | 171 / 35 | 143.556 / 35.871 |
| after5-properties | 90 / 22 | 27 / 3 | 171 / 35 | 151.520 / 38.315 |
| after5-sources | 0 / 0 | 0 / 0 | 0 / 0 | 0.001 / 0.001 |
| oldest-materials | 0 / 0 | 0 / 0 | 0 / 0 | 0.048 / 0.049 |
| oldest-properties | 0 / 0 | 0 / 0 | 0 / 0 | 0.132 / 0.145 |
| oldest-sources | 0 / 0 | 0 / 0 | 0 / 0 | 0.001 / 0.001 |

These operation counts demonstrate removal of redundant prefixes on this
fixed chain. They do not establish a general speed factor. Oldest images may
need no projection; their small timings are not performance claims. The
machine-readable continuation ledger contains complete per-case manifests,
hashes, counts, process budgets, and exact executed method IDs.

## Boundaries and next review

The other 1,738 methods of the 1,778-method baseline core inventory were not
run for this task. No complete full/targeted suite, installed-package smoke,
CLI subprocess suite, native Linux run, or hosted CI was performed. Simulated
POSIX budget tests are not native POSIX evidence. Existing installed smoke
and CLI contracts are unchanged. This test-only optimization does not establish
the cause of the historical 900-second installed wheel-smoke timeout.

The isolated patch is ready for independent review on its original baseline,
but is not a drop-in latest-Tian change. Both
`tests/test_kapoor_phosphate_preservation.py:111` and
`tests/test_tian_nano_ti_preservation.py:106` directly hash the old engine.
Latest integration needs separately reviewed finite recovery at those call
sites while retaining their original hashes and assertions, plus a pinned
16-ledger benchmark and fresh validation. The present benchmark deliberately
requires the original 14 ledgers and original disk hashes. No latest-baseline
integration, push, main merge, deployment, or new material admission occurred.

## Reproduce

From the original isolated checkout, run the 35 new methods explicitly:

```text
python -B -m unittest discover -s tests/history_replay -p "test_*.py" -v
```

The following single-method command works from the checkout root in both
Windows PowerShell and a Linux shell. It runs the unchanged former timeout
case and rejects errors, failures, skips, and incomplete method counts:

```text
python -B -c "import sys,unittest; sys.path[:0]=['tests','.']; s=unittest.defaultTestLoader.loadTestsFromName('test_pur_formulation_preservation.PURFormulationPreservationTests.test_catalog_byte_projection_aligns_current_and_predecessor_graphs'); r=unittest.TextTestRunner(verbosity=2).run(s); assert r.wasSuccessful() and r.testsRun==1 and not(r.skipped or r.expectedFailures or r.unexpectedSuccesses)"
```

The remaining exact method IDs and grouping are in the continuation ledger;
pass each explicit ID to the same loader. Preserve the original assertions
and verify complete selected IDs. Use a bounded process runner appropriate
to the host: recorded group ceilings were 900 or 1,800 seconds, with a
7,200-second overall budget for the 37-method continuation. These are
ceilings, not a prediction for another machine. The command above has no
built-in timeout; an external runner must impose the chosen budget.

For the eight previously unmeasured cases, create the output directory outside
the checkout first, then run this unchanged benchmark command in either a
Windows or Linux shell (only native Windows was executed here):

```text
python -I -B tests/history_replay/benchmark_replay.py --cases current-properties current-sources after5-materials after5-properties after5-sources oldest-materials oldest-properties oldest-sources --output ../history-replay-evidence/remaining.json --case-timeout-seconds 600 --total-budget-seconds 3600
```

Do not overwrite existing receipts or silently rerun completed measurements.
The original document gives the separate current-materials command.
