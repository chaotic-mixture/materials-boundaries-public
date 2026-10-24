# Full-history checkout correction for replay review

This is a local, unpublished successor to `e39b6d8a19576a05408b7da0e3faa8499b9f35f6`.
Independent review must precede publication. The earlier artifact and its six
historical evidence documents remain unchanged; their original run boundaries
must not be read as validation of this correction.

## Reproduced problem and exact correction

A clean one-commit clone of the original artifact failed
`TianNanoTiCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated`:
`git show 5a9a85c573f590d206cddb4cb7c085f334a0fbc0:.github/workflows/ci.yml`
returned 128. Fetching the same local clone's full history made the same
unmodified test pass, with the original commit and clean worktree unchanged.
The failed attempt and subsequent pass are separate records.

The general Ubuntu job runs full discovery but had a depth-one checkout.
Only `with: fetch-depth: 0` is added to its checkout and the generic Windows
checkout. All 21 job names, conditions, commands and matrices remain exact;
the 19 branch-specific jobs already requested full history. Windows currently
selects historical byte/ledger tests; no matching Git-object failure was
reproduced for that job. Its full-history setting is a bounded symmetric choice.
The dedicated replay workflow already fetches all history. The two independent
experimental-platform jobs run installed suites, do not execute the affected
root historical tests and remain unchanged.

## Exact compatibility boundaries

`tests/replay_checkout_history.py` loads one hash-pinned ledger containing
exact before/after images for the workflow, successor registry and Tian test
caller. The registry prepends this finite code ledger to named and full file
chains; material descriptors, data ledgers and admission chronology do not
change. Unknown bytes pass unchanged to the old rejecting assertions.
Each call rereads the ledger; there is no cross-call cache.

The Tian caller receives only a byte-reader wrapper. AST comparison removes
that one wrapper/import and proves every original assertion remains. All
historical hashes remain intact. The replay runner requires the actual corrected
workflow hash before comparing its recovered bytes to the pinned predecessor;
an old uncorrected workflow is rejected too. The helper's own ROOT preserves
the original adjacency negative test's old-ledger-drift cause; a separate
regression checks this rather than accepting an earlier missing-file failure.

The replay engine, original compatibility bridge, 14-layer benchmark,
16-layer adapter/configuration, 119 Tian fixtures and all runtime/catalog
files remain byte-identical. This correction does not alter the stable-input
per-invocation contract or claim protection against concurrent within-call edits.

## Actual validation and retained failures

Native Windows CPython 3.11.0 completed 127 distinct methods: 47 historical
methods in six fresh groups, the actual uninterrupted 70-method replay command,
and 11 earlier workflow/Windows preservation methods. One Tian method overlaps
the groups and is counted once. The separate 10-method helper probe overlaps
the 70 and adds no unique passes. Final selected scope: zero failures, errors
or skips. The machine-readable record lists exact IDs, input hashes, elapsed
times and raw-log digests.

The first 70-method attempt remains failed: 66 methods passed, four budget
methods produced six unittest error entries, with no assertion failures or
skips. Atomic report replacement raised WinError 5 in the sandbox temporary
directory. An identical minimal `Path.replace` probe failed there and passed
in a task-owned writable directory. The bounded repeat set only child-process
TEMP/TMP to that directory, with no test-logic, assertion or system-setting
change. Only the runner's explanatory output wording was clarified between
attempts; the two complete source trees are not claimed byte-identical. The
repeat passed all 70. The initial MSYS local-clone and DNS-thread setup
failures are also recorded separately from test outcomes.

Only 62 of 1,887 existing core methods ran; 1,825 remain unrun. The full core,
complete 305-method targeted core, 561 installed tests, native Linux and hosted
CI were not run for this correction. No real benchmark was repeated: the old
14-layer and four e39b6d8 16-layer measurements retain their original scope.
No universal speed factor or installed-smoke explanation is claimed.

## Review and reproduction

From a full-history clone, the same commands work in PowerShell and Linux:

```text
python -B -X utf8 scripts/run_history_replay_latest_ci.py --validate-inventory
python -B -X utf8 scripts/run_history_replay_latest_ci.py --tests
```

The first command validates the frozen 70-ID manifest and executes zero tests.
The second actually executes all 70 and rejects failures, skips, substituted
IDs and incomplete runs. Use an existing writable temporary directory if the
execution sandbox denies atomic replacements; do not change assertions.

A future push still runs the generic full-core/Windows jobs as well as the
dedicated replay job. Broader cost and correctness validation remain separate;
this artifact does not claim all hosted jobs pass or promise a total duration.
No push, main merge, deployment, DOI operation or credential grant occurred.
The experimental catalog remains 1,185 = 1,161 source-qualified identities
plus 24 separately computed records. Main remains 1,081. No material growth
is attributed to this test-only correction.
