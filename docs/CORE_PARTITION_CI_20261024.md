# Whole-module Ubuntu core partitions: local review candidate

This test-only change partitions the existing general Ubuntu core run into four
whole-module jobs for each of Python 3.11 and 3.12. It preserves the complete
1,887-method inventory and requires eight matching completion receipts plus a
successful matrix before aggregation can pass. It is a local candidate for
independent review, not a successful hosted CI result or a material admission.

The parent is `bf1c7a86068c37c2733ac4d25c268144090f9aad`. Implementation commit
`a40dbc30772dd7626c122b529aa5e990656bd7de` has tree
`56309769d7bfe0229f4b99e376073844047ad2f4`. The tests below ran against the same
implementation bytes before that commit; recorded input hashes were checked
against the committed blobs. Its successor adds only this explanation and the
[machine-readable validation record](core-partition-ci-20261024-results.json).

## Why the full run needs partitioning

The original [general run 40085112884](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/40085112884)
at `bf1c7a8` was cancelled. Both Ubuntu annotations explicitly report
`The job has exceeded the maximum execution time of 6h0m0s`.

| Original job | Full core completion evidence | Missing completion evidence | Terminal result |
| --- | --- | --- | --- |
| Ubuntu 3.11, 120846350336 | 1,771 passed, 17 native-Windows skips | 99 IDs | Cancelled at six hours |
| Ubuntu 3.12, 120846350303 | 1,450 passed, 17 native-Windows skips | 420 IDs | Cancelled at six hours |
| Windows 3.10, 120846350321 | 512 passed, 14 platform skips from a 526-method selection | 1,361 root methods not selected | Success |
| Windows 3.13, 120846350148 | 512 passed, 14 platform skips from a 526-method selection | 1,361 root methods not selected | Success |

The Ubuntu 3.12 preflight also passed five release-metadata methods not reached
in its full run: its unique job-level evidence is therefore 1,455 passes,
17 skips and 415 IDs without completion evidence. Ubuntu 3.11 preflight methods
overlap its full-run prefix. These different scopes must not be added twice.
There were no observed unittest failures or errors in the partial output, but
neither Ubuntu suite completed. Missing completion cannot distinguish unstarted
methods from interrupted work and is never a skip or pass.

The last completed Ubuntu 3.11 method was
`test_viscoelastic_catalog.ViscoelasticCatalogTests.test_required_scope_and_meaning_reject_all_public_paths`
at 16:14:02 UTC. Ubuntu 3.12 last completed
`test_primary_table_growth_ci.PrimaryTableGrowthCITests.test_unknown_predecessor_workflow_shapes_are_rejected`
at 16:04:43 UTC. The cancellation tails are unassigned; the next static ID is
not proof of the interrupted method. All four general core-wheel smoke steps
passed, but this was not the separate 561-method installed-package suite.
Nineteen branch-conditional jobs were skipped; Ubuntu evaluation steps were
not reached after cancellation.

The separate [replay run 40085112900](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/40085112900)
passed all 70 selected methods on Ubuntu 3.11 and Windows 3.12. It did not certify
the incomplete general core runs. No cancelled hosted run was retried for this
candidate.

## Frozen coverage and order

[manifest.json](../tests/core_partition/manifest.json) records all 147 module
filenames, their ordered method IDs and their exact partition assignments.
The unchanged root fingerprint is
`19a735217c29533c1137a6cfd95b2b58cf88e8cf649848e41012c510434446f7`.
The frozen assignment is SHA-256 of the UTF-8 module name, interpreted as a
big-endian integer modulo four.

| Partition | Whole modules | Methods |
| --- | --- | --- |
| 0 | 39 | 459 |
| 1 | 36 | 492 |
| 2 | 30 | 417 |
| 3 | 42 | 519 |

The runner checks frozen manifest bytes and content, independent source
declarations, actual discovery and exact module filenames, including rejection
of an extra empty test module. It filters the canonical discovered nested suite,
preserving relative method order and module/class fixture behavior within each
partition. Global order and process isolation change: modules in different
partitions run in separate jobs. Each Python version must independently cover
the exact disjoint 1,887-ID union. Counts alone cannot satisfy the gate.

[Module timing evidence](core-partition-module-timings-20261024.json) retains
per-ID completion timestamps and explicit missing/censored observations from
all four original general jobs. The observed Ubuntu entry-interval sums by
partition were 1,870/7,700/2,920/7,456 seconds for 3.11 and
1,954/5,731/3,596/7,457 seconds for 3.12. They are lower-bound timing proxies,
not complete partition forecasts. The longest observed whole-module span was
`test_material_sixth_batch`: approximately 2,555/3,498 seconds on Ubuntu and
3,759/4,169 seconds on Windows. No observed whole-module span reached six hours;
censored work remains unknown. Repeated setup, build and smoke costs remain in
each partition. There is no guarantee that every job will fit the unchanged
six-hour ceiling. A whole module exceeding that ceiling requires a separately
reviewed plan, not silent method splitting or a removed test.

## Completion, skip and workflow contracts

The only existing job changed is general Ubuntu. Its original event and branch
eligibility, full-history checkout, preflight, install, wheel build, metadata
and wheel smoke, catalog validation, and evaluation remain in their original
relative order. The matrix is two Python versions by four partitions, with
`timeout-minutes: 360` and `fail-fast: false`. Windows jobs, all existing targeted
jobs and the dedicated replay workflow remain unchanged. There is no automatic
retry or `continue-on-error`.

The new contract directory is explicitly executed before core partition
execution. It is outside ordinary root discovery and the frozen 70-method
replay inventory. Its workflow checks inspect the actual new workflow before
any historical projection, rejecting old unsharded images, missing aggregation,
disabled partitions, changed eligibility and permissive receipt handling.

Production execution requires a real matching GitHub Actions job, Linux x86_64,
Python 3.11 or 3.12, the checked-out SHA/tree, the expected ancestor, clean tracked
inputs and matching committed runner/manifest bytes. Context is checked again
after the suite. Temporary receipt output is the only newly allowed untracked
output. A receipt and flushed JSONL journal preserve expected, discovered,
started and completed IDs, outcomes, fixture/subtest errors, terminal status,
Python/platform, SHA/tree, runner/manifest hashes, partition, run ID and attempt.
Abrupt termination may leave only partial diagnostics and never constitutes
success.

Normally POSIX permits exactly 18 skips: 17 named Windows/NTFS methods plus the
wood-dossier method when `WOOD_REVIEW_DOSSIER` is absent. With that input present,
only the 17 native-Windows skips are permitted. The manifest binds exact IDs,
reasons and conditions; each partition and the aggregate validate their exact
intersection. Only a presence boolean is recorded, not a dossier path.
Expected failures, unexpected successes, fixture/subtest errors, changed skip
reasons, cancellation, incomplete execution and missing terminal records fail.

Each job uploads its receipt and journal as a uniquely named current-run and
attempt artifact, including failure diagnostics where available. Aggregation
runs after failure where possible, with the same eligibility boundary as the
general Ubuntu matrix. Downloads retain separate artifact directories. Success
requires exactly four valid receipts per Python version, eight total, and the
actual matrix result `success`; a core receipt cannot hide a later evaluation,
wheel smoke or artifact-upload failure. Missing, extra, duplicate, stale,
cross-SHA, mixed-attempt and wrong-version artifacts fail. A missing or cancelled
aggregate is not a green result. The aggregator checks strict event order and
exact receipt/journal agreement, not just a journal checksum. Full patch versions
must agree within each Python minor group; they need not match the aggregate
interpreter's patch version. Artifacts are run outputs, not caches.

## Historical preservation

The patch changes seven existing files and adds nine implementation/evidence
files. A finite seven-image compatibility ledger recovers exact predecessor
code bytes for historical readers. Existing hashes and assertions are retained;
unknown bytes remain subject to the old rejection paths. The registry and the
direct Tian, replay and checkout-history callers receive narrow input adapters.
There is no cross-call cache and no runtime catalog or validation change.

All 119 original Tian fixture files and the three already published replay
fixtures remain byte-identical, as do all 985 other baseline paths outside the
seven modified paths. The original 70-method inventory, replay engine,
benchmarks, old ledgers and material data remain unchanged. New contracts test
whole-image mutation, malformed edits, unknown code, changed roots/ledgers,
actual registry order, and preservation of the old assertion ASTs.

## Actual local validation and retained failures

Native Windows CPython 3.11.0 with the existing development environment passed
**177 distinct selected methods, zero failures, errors or skips** in the final
selected scope:

| Scope | Execution mode | Passed | Measured time |
| --- | --- | --- | --- |
| Unchanged replay inventory | One uninterrupted invocation | 70 | 37.143 seconds unittest time |
| Additional historical compatibility | 25 fresh process groups, no overlap with the 70 | 57 | Exact per-group durations in the JSON record |
| New receipt, runner, workflow and history contracts | One uninterrupted explicit-directory invocation | 50 | 6.260 seconds unittest time |

This is 62 existing root methods plus 65 existing explicit replay methods and
50 new explicit contracts. **1,825 of the frozen 1,887 root methods were not run**
in this local validation. Final discovery verified all 147 module paths, all
1,887 IDs and the four complete selections in 1.860 seconds; discovery executed
zero methods. The machine-readable record lists every executed and unrun ID,
input hashes and log digests. Duplicate development reruns are not additional
unique passes.

Earlier attempts remain distinct from these final results:

- An initial discovery interpreter lacked `jsonschema`; it executed no methods.
- One initial workflow-contract helper raised a str/bytes `TypeError`; the helper
  was corrected and the final eight workflow methods passed.
- An initial synthetic discovery-negative fixture caused one failed method
  with three failed subtests. It mutated a manifest field rather than actual
  discovery. The fixture was corrected without relaxing production assertions.
- Independent review found a real draft aggregator defect: eight fabricated
  successful receipts with header/terminal-only journals were accepted. The
  final runner requires the exact method event sequence. One positive and seven
  negative synthetic probes then behaved as expected; these are not real core
  method passes. The original draft bytes, probe script and raw probe log were
  not separately retained. Their retrospective record derives from the original
  execution output; that evidence limitation is explicit.
- A static audit initially assumed 119 total baseline fixtures. It was corrected
  to the actual 119 original plus three published replay fixtures; all 122 hashes
  were checked without changing repository assertions.

The final runner SHA-256 is
`6fce86a0347932a7a8f8053c63c22b4a2a3cb22d9737629311eb5c0f38183765`.
No real Linux execution, complete production partition, hosted eight-job matrix,
artifact transfer, fresh wheel validation, separate 561-method installed suite
or new real-data benchmark has been run for this candidate. Local synthetic
contracts do not establish hosted integration success or a universal speedup.

## Reproduction and next gate

Use a clean checkout with complete Git history and the project's development
dependencies. The following commands work from the repository root with the
chosen Python interpreter on Windows or Linux:

```text
python -B -X utf8 -m unittest discover -s tests/core_partition -v
python -B -X utf8 scripts/run_history_replay_latest_ci.py --tests
```

The 57 additional exact IDs and their 25 process groups are listed in the JSON
record. They can be selected by setting `PYTHONPATH=tests` for the child process
and passing each group's IDs to `python -B -X utf8 -m unittest -v`. Use a distinct
task-owned temporary directory per child. This describes a segmented rerun,
not an uninterrupted full suite.

The actual workflow uses `run_full_core_partition_ci.py run --partition N
--output-dir core-ci-results` and its `aggregate` subcommand. Those production
commands intentionally reject fabricated local Actions context. Review the
immutable candidate before any experimental publication, then verify the exact
published SHA, all eight real matrix jobs and the aggregate to terminal status.
Do not infer completion from the earlier Windows profile or dedicated replay
workflow. If a whole module still exceeds six hours, preserve its partial
evidence and return a separate bounded plan.

No material counts change: the last verified experiment had 1,185 records
(1,161 source-qualified identities plus 24 computed records). The last verified
main was 1,081 at `4c5656cf6ba0ad1a54b736e0568e97abe4815c29`. This candidate has not been
pushed, merged, deployed or used to register a DOI.
