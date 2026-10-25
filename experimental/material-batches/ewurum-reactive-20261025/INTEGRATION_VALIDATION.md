# Ewurum reactive runtime validation

The locally tested implementation is `dba9336698aa4114f3bf144919d1d1d8789633d8` (tree `51db0acf94cf2695f342ddb7ac24cc8f2e4ca49d`).
The report is prepared for an evidence-only commit retaining these implementation bytes. No push,
main merge, deployment, DOI registration or new authentication has occurred.
Independent final implementation review remains required before publication.

## Actual completed checks

Native Windows CPython 3.11.0 completed the full scoped source command in
1010.312 seconds: **370 successful executions / 366 distinct
methods**, zero failures, errors or skips. Nine groups ran in fresh processes:
candidate 20, preservation 12, new contracts 17, historical compatibility 156,
partition contracts 50, old Curaua candidate 18/preservation 12/contracts 15,
and unchanged replay 70. Four replay/compatibility IDs overlap. This is a scoped
multi-process run, not an uninterrupted single-process or full-root run.
The historical group includes every Bruns 31, Tarasov 30, Kapoor 30 and family 5
method, plus Tian 30 and the other unchanged selected modules.

Fresh offline installation of all six wheels completed **577 methods** in
846.266 seconds: query 249, formal 13, ingestion 202,
relationships 14, provider 19, transport 37, lifecycle 25 and integration 18.
Every group passed with zero failures, errors or skips. Package imports were
checked against the isolated environment. The additional 32 CLI outputs compare
complete JSON and text values/caveats, not whole text bytes. That smoke uses
in-process CLI calls; installed query tests separately exercise native UTF-8
subprocess CLI/API equality and stale-store rejection.
The independent CLI/API smoke also completed after all eight groups. Its
terminal marker, 577 distinct discovered/outcome/completed IDs in exact group
order, per-group durations and reconciliation receipt are all hash-bound.

Five release metadata methods passed on clean `a8efe451`, before the later
CLI-order and overlap-count corrections. Their package, schema, example, README, build
configuration and metadata-test inputs remain byte-identical at the final
implementation; no metadata rerun or whole-preflight equivalence is claimed.
The predecessor's actual discovery confirmed 147 modules,
1887 root IDs and partitions 459/492/417/519 without executing those discovered
methods. Source coverage plus metadata executes **162/1887 root IDs**;
**1725 root IDs remain unrun** locally. Discovery, simulations, conditional
skips and inspected assertions are never counted as executed passes.

The unchanged full core-wheel installation smoke passed in
1199.375 seconds after the environment issue below.
It is recorded as a script check, not an invented number of unittest methods.
All 319 package/build/smoke input hashes and six wheel hashes are recorded and
verified unchanged. Catalog validation and exact append/preservation checks pass.
The core smoke ran against the exact wheels built at `62d22520`. An unrelated
historical test method was edited late in that run; the worktree therefore did
not remain clean. All 319 actual package/build/smoke input hashes stayed equal,
and the final fresh installed test run uses the same six wheel bytes. This
qualified equivalence is recorded rather than claiming a clean whole-tree run.

## Preserved failures and corrections

The initial sandboxed wheel smoke failed after
89.031 seconds. A parent UTF-8 decoder initially
obscured the child error. The bounded raw-byte diagnostic reproduced native
`WinError 5` at the existing atomic hard-link publication operation. The smoke
implementation, assertions and subprocess coverage remained unchanged; the
successful retry used the authorized execution environment outside the sandbox.
Neither failed wheel attempt is a pass or a skip.

The first full source command recorded **284 passes, one failure and 85 unrun**.
The old Curaua document test had projected to old 1164 counts before calling the
unchanged live 1168-count normalizer. The narrow repair validates current counts
first, then applies exact normalized-document projection. The old false-count
and unknown-prose assertions remain, with an added current false-count rejection.
The originally failing method and the entire 12-method module then passed
(13 executions, 12 distinct methods), on an input image exactly matching the
later `a8efe451` commit. Those targeted receipts did not record checkout state;
the later bridge/binding input differences are listed explicitly. Earlier passes do not directly
certify the final image. The complete final source command repeats these
methods. Process, ledger, log and input hashes retain that distinction.

The first installed run completed environment setup but failed its initial
source-union smoke before any of the 577 methods or complete 32-output check. The
ten complete property objects were correct; the expected list had globally
sorted them instead of retaining the CLI's established catalog order. The
repair preserves the old six-record prefix followed by four R records, keeps
the independently pinned sorted aggregate hash, and adds a literal canonical
order oracle. Actual CLI output is never sorted to make the test pass.
The second source command was intentionally stopped before this input edit:
49 group-certified passes, 3 further method completions, 1 interrupted method
and 317 unstarted. It is not a successful suite or a skip. All task-owned
processes were confirmed stopped. Focused fresh installation then exercised
the 32-output smoke and all six new query methods in
105.032 seconds on a dirty `a8efe451` working tree.
The recorded five-file patch and each changed-file hash exactly match the
`8df0cb57` intermediate implementation; this is not a clean-HEAD execution claim
or certification of later repairs. Targeted receipt and log hashes retain the
actual tested image and later input differences.

The third source command on clean `8df0cb57` terminated with status
**passed** after 1016.312 seconds,
with 370 group-certified passes. Its exact
group results and method outcome lines remain recorded independently of the
fifth source command on the final implementation.

The second installed command on clean `8df0cb57` failed after
838.250 seconds: **464 methods executed,
462 passed, two failed, zero errors or skips, and 113 unrun**. Query 249 and
formal 13 passed; ingestion 202 completed with 200 passes and two stale
`unable_to_compare` count assertions (1179 versus 1175 and 1191 versus 1187).
Its initial 32-output smoke passed, but the later independent CLI/API smoke
was not reached. The original failure log and exact reconciliation receipt
remain hash-bound. The final source-370-05 and installed-577-03 runs both passed
on the same clean final commit; earlier successes did not replace them.

The fourth source command on clean `dba93366` failed after
106.031 seconds under the tool sandbox: **20 methods executed,
19 passed, one error, zero assertion failures or skips, and 350 unrun**.
The packet replay/idempotent-write test reached the unchanged `os.link` call
and received `PermissionError [WinError 5]`. The log and all method outcomes
remain hash-bound. No code, assertions, credentials or system security settings
changed. The fifth source command used the authorized native execution route
outside the sandbox on the same clean commit. Execution modes come from the
orchestration context; the receipts independently establish each result and
commit/tree. The sandbox failure remains a failed attempt, never a skipped or
passing test.

Before changing the two expectations, the read-only diagnostic on clean
`8df0cb57` made two actual queries and checked all eight complete new-relation
objects: each of the four R identities is `unable_to_compare` for both probes,
with physical equivalence unasserted and no evidence or conflict fabricated.
The original 13 possible-overlap IDs and one exact copper record-reference
relation remain unchanged. This diagnostic took
1.015 seconds and executed zero unittest methods.

The repair changes one assertion file and five exact historical bindings,
retaining all method IDs and old predecessor assertions. The full 41-method
overlap module passed in 9.016 seconds;
four historical binding checks passed in
3.000 seconds. Both were run on the same
dirty six-file image based on `8df0cb57`, with all 327 input hashes unchanged
before and after and byte-equivalent to later commit `dba93366`. The exact
six-file patch SHA256 is `3ef414a948d7375625b9f7735593879235dc6cb9efff27899e5cd169c6352406`. These are 45 targeted
method executions, not extra full-root coverage. Three private history methods
are outside the frozen inventories; the remaining checks are repeated by the
final scoped commands. Their 102 and 369 successful subtests are diagnostic
counts, not additional test methods. Exact predecessor recovery, corrupt-byte,
inventory and offset rejection remain exercised; no scientific record changes.

The historical README normalizer initially rejected new prose inside its fixed
count block. Moving that prose outside preserved the old guard. Wheels were
rebuilt after this documentation correction. An initial private required-ID audit
also confused a required subset with the full query inventory; the corrected
audit checks the exact old 118 prefix plus 8 additions within 249. No test contract
was relaxed. Early 17 contract and 3 history passes are covered again by the final
source run and are not extra distinct coverage.

## Evidence and limits

All nine candidate evidence files, 122 historical fixtures, 22 old runners,
four old workflows, source catalog bytes and frozen core/replay inventories
remain unchanged. The old six Ewurum properties and every prior catalog object,
order and metadata value are preserved. Four identities/states/moduli are added;
the source is reused unchanged, giving **1168 source-qualified + 24 computed =
1192 experimental records**, while main remains 1081. Source-qualified counts
are natural 1010, metal 32, inorganic 59, polymer 30 and composite 37; gaps to 1000
are 0/968/941/970/963. The 62 unadmitted examples remain excluded.

The read-only native remote check at `2026-10-25T19:35:27.646092+00:00` returned
main at `4c5656cf6ba0ad1a54b736e0568e97abe4815c29` and the Curaua experimental
branch at `8ccd217599fd462d13d7435bdfb02a0825e4eacd`. The planned Ewurum branch
was not returned by that query. An earlier sandboxed lookup failed with
`getaddrinfo() thread failed to start`; its failed receipt is preserved without
assigning an unverified cause. This is point-in-time read evidence, not a push
or a guarantee of later remote state.

The bounded implementation privacy audit examined 100 changed text blobs across
the candidate/correction/append/implementation history. Its 4 token-shaped
changed-blob findings were adjudicated as unchanged explicit synthetic
redaction-test sentinels and their exact historical copies. No raw assets, binary additions or unresolved
private-path/credential-pattern hits were found; this is not an exhaustive
security guarantee. Original candidate failure/review history remains retained.

Independent source review corroborated official indexed text, not current raw
PDF bytes. Source-cited ASTM D1708-18 (2018), separate hot-pressed gel specimen
scope and all unresolved conditions/composition qualifiers remain unchanged.
No independent scientific replication or engineering qualification is claimed.

Exact group IDs, manifests, hashes, terminal results, failed attempts and unrun
scope are in [integration-validation-results.json](integration-validation-results.json).
Reproduce locally using the new scoped runner's `--validate-scope`,
`--validate-inventory`, `--source-tests`, and `--wheel-dir` with
`--dependency-dir`. Windows atomic-write and local transport assertions require
an execution environment that permits those operations. The dedicated workflow
declares Ubuntu with Python 3.11 and Windows with Python 3.12; neither hosted job has run for this local
implementation. The full general partition workflow remains unchanged.

With the existing development dependencies installed and an offline wheel
cache matching the two locked requirements files, the same commands work in
PowerShell and a POSIX shell (use that environment's Python executable):

```text
python scripts/validate_catalogs.py
python scripts/run_ewurum_reactive_runtime_ci.py --validate-scope
python scripts/run_ewurum_reactive_runtime_ci.py --validate-inventory
python scripts/run_ewurum_reactive_runtime_ci.py --source-tests
python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir dist . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform
python scripts/check_wheel_metadata.py dist/materials_boundaries-0.35.0-py3-none-any.whl
python scripts/run_ewurum_reactive_runtime_ci.py --wheel-dir dist --dependency-dir dependency-cache
```

The cache must satisfy `experimental/platform/requirements-lock.txt` and
`experimental/platform/ci/projection-requirements.txt`. Each installed run
creates a new isolated environment; it does not rely on an editable checkout.
