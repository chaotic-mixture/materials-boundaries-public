# Kapoor runtime validation

Local native Windows / CPython 3.11 validation is complete. Independent parent
implementation review is still required before any experimental push. No hosted
CI or Linux runtime result is claimed. The earlier Linux and Windows candidate
checks belong to the unchanged-runtime candidate checkpoint.

## Exact versions and coverage

The source-reviewed candidate is `c275ae6051277ad6d08077b2937527907eb2380f`. The data-only
append is `76cae67a9401b916c1409ad3c2212fa3c103be6f`. The full selected core run used
`852f0978de91b8c3cb96263b58f9e995e717128f`. It completed **250 methods: 250 passed,
0 failures, 0 errors and 0 skips**, in 1618.500 seconds within
its 1800-second process budget. The complete core inventory contains 1832 methods;
**1582 unselected methods were not run**, neither passed nor skipped.

The original installed attempt on that implementation failed. Its query group
ran 226 methods in 520.275 seconds: **221 passed and
5 failed**, with no errors or skips. The other 326 installed methods and final
independent smoke had not started. The initial 48 density CLI outputs had passed;
those outputs did not cover computed-registry envelope counts. The whole failed
attempt returned exit 1 after 641.204 seconds, without a
timeout. Its original logs and wheels were retained separately.

Both computed-registry envelope schemas still returned the prior literal
`legacy_unique_material_count = 1153` while their pin identified 1159 source-qualified
identities. The repair `53bf501667c4915e6ea1c592420df7d22d1d3aaf` changes only those
two literals to 1159. It leaves material data, scientific qualifiers, review
records, database anchors, admission rules and all five failing assertions intact.
The five original failures then passed against proven source imports from the
repair checkout, with zero failures, errors or skips. They are not additional
distinct tests to add to the installed total below.

Six wheels were rebuilt offline from the production repair. In the next fresh
environment, **query 226 and formal 13 passed**, but ingestion ran 200 methods
with **199 passed and 1 failed** in 70.521 seconds.
The other 113 methods and final independent smoke had not started. This whole
attempt returned exit 1 after 690.219 seconds, without
a timeout; it is not reported as an installed-suite pass.

That failure was a stale CLI expectation: the Al2O3 literal-text probe expected
seven possible matches while the existing API assertion correctly required the
old seven plus these six glass identities. Independent exact-set comparison
retained all seven old IDs and found only the six approved Kapoor additions.
There are still zero confirmed overlaps and 1170 unable-to-compare rows. Even
the three reported zero-Al2O3 rows contain the literal token; this establishes
no nonzero constituent, pure phase or physical equivalence. Test-only commit
`77146d0a6d015d5eecdf3751c0df2ad6b47b40e8` changes that one expected
literal from 7 to 13. Every UTF-8, deterministic-byte, no-stderr, input-hash and
read-only assertion remains intact. The original CLI failure then passed on
that commit, with no skips, errors or failures.

The unchanged production wheels were installed into another fresh environment
for **all six remaining groups, 313 methods**, followed by the separate installed
CLI/API, linked-provenance and deterministic-archive smoke. This segment returned
exit 0 in 186.063 seconds within its 1800-second budget.
The same initial **48 exact density CLI outputs** passed in each fresh attempt;
repeated outputs are not additional distinct coverage. Package origins, exact
packet objects, resource hashes, counts and query baseline were checked.

Together, the two complete-group segments cover **all 552 installed method IDs**
with successful final outcomes and no skips. **There was no single uninterrupted
full installed-runner pass.** Query and formal remain attributed to the production
repair; the other six groups are attributed to the test-only successor. Neither
failed attempt is erased or converted into a skip.

| Installed group | Passed | Failures | Errors | Skips |
| --- | ---: | ---: | ---: | ---: |
| query | 226 | 0 | 0 | 0 |
| formal | 13 | 0 | 0 | 0 |
| ingestion | 200 | 0 | 0 | 0 |
| relationships | 14 | 0 | 0 | 0 |
| provider | 19 | 0 | 0 | 0 |
| transport | 37 | 0 | 0 | 0 |
| lifecycle | 25 | 0 | 0 | 0 |
| integration | 18 | 0 | 0 | 0 |

The two repairs do not change any of the 22 selected core modules, their fixtures
or their dependencies under test. None calls or pins the changed computed-envelope
implementation; the corrected CLI method is in the separate installed ingestion
inventory. The expensive 250-method core selection was therefore not repeated.
Its successful result remains explicitly attached to the earlier implementation;
the direct regressions and complete installed-group results remain attached to
their actual repair commits. The final successor
changes only this document and `integration-validation-results.json`; it does
not change tested code, data or assertions.

## Preserved evidence and remaining boundaries

Strict catalog validation, exact old-object/order checks, an unchanged second
merge, both offline six-wheel builds and strict 58-path scope validation passed.
Earlier focused checks included 15 query/overlap/stale-store methods, 7 append
preservation methods, 5 legacy-document methods and 30 CI-contract methods, all
with zero failures, errors or skips. These overlap the selected or installed
inventory and are not summed as extra completed coverage. Exact IDs, fingerprints,
artifact and log SHA-256 values, elapsed times and failed-attempt history are in
`integration-validation-results.json`.

All nine original candidate batch artifacts remain byte-for-byte unchanged. The
17 original candidate test methods retain their assertions through a finite
historical-baseline adapter. Old catalog bytes, record order, source caveats,
documentation and workflow evidence remain recoverable. The historical replay
engine is unchanged; the isolated unpublished optimization is not an ancestor.
This task does not attribute an earlier fresh-install timeout to that engine.

The actual local source-qualified graph is **1159 identities, 31 grades,
1160 states, 1171 properties and 126 sources**. Category identity counts are
natural **1010**, metal **32**, inorganic **59**, polymer **30** and composite
**28**. Only natural meets the 1000-identity target. The remaining category gaps
are 968 metals, 941 inorganics, 970 polymers and 972 composites. These source-qualified
counts exclude computed records. The local combined projection is **1183 =
1159 source-qualified identities + 24 unchanged computed records**; 62 examples
remain excluded. The actual new rows are six inorganic identities, six states,
six measured density facts, one source and no grades. Candidate counts, states
and calculations are not additional identities.

The last published experimental project remains 1177; main remains 1081. No
experimental push, main merge, deployment, DOI registration, raw-asset upload or
credential change has occurred. No full-core pass, Linux runtime pass or hosted
CI pass is claimed. The proposed branch is
`experimental/kapoor2019-glass-runtime`, whose workflow selects Ubuntu 3.11 and
Windows 3.12 after a separately reviewed and authorized publication.

## Reproduction

These commands are portable between a configured Linux shell and PowerShell
with the supported Python and already-provisioned locked build dependencies.
Use separate wheel and dependency directories. The installed runner creates
a fresh environment, checks package origins and installs without an index.

```text
python -X utf8 scripts/validate_catalogs.py
python -X utf8 scripts/run_kapoor_phosphate_ci.py --validate-scope
python -X utf8 scripts/run_kapoor_phosphate_ci.py --targeted-core
python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir wheelhouse . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform
python -X utf8 scripts/run_kapoor_phosphate_ci.py --wheel-dir wheelhouse --dependency-dir dependency-wheelhouse
```

The ledger also retains private-preflight failures that changed no artifacts:
an incorrect append-order expectation, a nonexistent scope constant and an
incorrect wheel filename prefix. Correcting those private
invocations did not change production behavior or weaken assertions. The genuine
five-test query failure and the later one-test ingestion failure are recorded
separately with their narrow repairs and complete-group reruns; neither is
converted into a skip or erased by the later successful segments.
