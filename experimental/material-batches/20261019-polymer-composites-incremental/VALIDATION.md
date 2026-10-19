# Executed local validation, 2026-10-19

The bounded increment adds four source-qualified composite identities, states
and properties to the exact a592 catalog. It adds no source or grade, changes
no pre-existing catalog object, and does not admit a computed example. The
experimental project count is 1107 = 1083 + 24. Released main remains 1081.

## Actual test evidence

| Executed boundary | Actual outcome |
| --- | --- |
| Six core increment/source/history modules | 62 passed, 0 skipped; 191.010 seconds reported by unittest |
| New README snapshot bridge, presentation preservation and three selected bulk cases | 17 passed, 0 skipped; includes the actual 402-file round trip; 16.984 + 10.178 seconds |
| Seventeen affected platform/formal modules against the current checkout | 275 different test IDs passed, 0 skipped after bounded recovery of the initial failures described below |
| Full catalog structural/integrity validator | Passed: 41 claims, 115 sources, 1083 identities and reference properties, exactly 8 composite executable rules, four languages |
| Six freshly built wheels | All package file sets and bytes matched source: core 64 files, formal 4, federation 8, query 20, lifecycle 3, platform 3; metadata, licenses and notices checked |
| Fresh offline installation | Dependency consistency passed; four new records and 32 CLI outputs across English, Chinese, Japanese and German passed; exact core/project/count pins matched |
| Affected tests in that fresh installation | Query 105, ingestion 145, hBN projection 14, formal catalog 11: 275 passed, 0 skipped |

The local source checks cover **354 different test IDs: 62 + 17 + 275**.
The installed run repeats the 275 affected platform tests in a distinct
installation boundary; those repeats do not increase the unique-test count.
The earlier standalone 12-case source-facts run is already included in the 62.
No skipped case is counted as a pass.

The core run was observed from 17:06:06 to 17:09:17 UTC. Fresh package building
completed from 17:13:13 to 17:13:21 UTC without network downloads. The fresh
installation/check process ran from 17:13:39 to 17:16:55 UTC and exited zero.
The preservation command did not capture absolute start/end timestamps; its
reported unittest durations are retained without invented wall-clock times.

The first platform source run had 77 actual passes, nine case-level environment
errors and three `setUpClass` errors because the Linux offline socket guard
also blocked Windows' standard-library socketpair construction. Its failed
outputs were retained. A narrow Windows socketpair-only exception allowed the
internal loopback pair while still refusing DNS, other loopback connections,
external connections and `sendto`. The subsequent 53-case recovery had 52 passes
and one genuine stale test expectation (`composite=6`); that expectation was
corrected to 10. The corrected case and six ingestion modules then passed
146/146. Per-ID reconciliation proves all 275 intended source cases actually
passed. The later complete installed 275-case run also passed without errors.
No production networking policy or existing platform CI guard was changed.

## Integrity and negative cases

The reusable offline integration command created one hash-bound artifact. Its
identical second run preserved bytes and modification time. Tests exercise
repeated merge/no increment, complete predecessor recovery, missing properties,
wrong quantity units, changed existing properties, partial-batch atomicity and
unchanged source/grade records. The affected NOMAD tests cover resumability,
partial failure, duplicate/changed upstream observations, retry budgets and
rate limits, missing/wrong-unit properties and unchanged admission exclusions.
These are deterministic fixtures; this batch makes no new live NOMAD claim.

The a592 catalog is recovered byte-for-byte before the older historical
recovery chain. The query tests independently recover its complete 64-file
manifest, preserve older pins, and reject incompatible database anchors. Old
NOMAD state remains readable with its saved boundary but cannot be updated or
abandoned under the new data boundary. No state is silently migrated.

The dated README class sentence is bound to the exact four-record data commit.
It does not purport to describe arbitrary later synthetic append fixtures.
Its finite reversal preserves the pre-existing README and all nine earlier
preservation ledgers. The same bridge reverses the exact scoped workflow edit
before the historical 402-file check; old hash constants are not replaced.

The CI scope guard passed on the actual checkout. Isolated negative probes
rejected an out-of-scope production-file change and an extra edit to an existing
full CI job. Native Windows probes allowed only the intended socketpair/asyncio
operation and confirmed the remaining socket prohibitions.

## Reproducible artifacts and limits

The candidate packet commit is `5b42017bfd54057203e20170c4bc006fef643039`;
the applied data commit is `5396fd1cc9df72507785a112a21c2990fb4a7c50`.
The immutable offline package SHA-256 is
`1ac8716e5d6e350716e308728c195fb750fdbd48068295bc644fc39363963620`.
The unchanged source-registry SHA-256 is
`3d8b8c6d4891400504ea9bedbafaa06d05698b5324e9cbd7f5686ebc1ac1736f`.
The current query anchor is
`3782f403f120f22b5287e01f4e207419e2f576a28dfda33a89a85580b936c0f6`.

Detailed commands, raw execution logs, case IDs and input hashes are retained
in the parent delivery under `incremental-evidence/polymer-composites-20261019/`:
`core-tests.json`, `preservation/result.json`,
`platform-targeted-20261019T170729Z/PLATFORM_TARGETED_RESULTS.json`, and
`installed/build.json` plus `installed/checks.json`. Their supporting logs
remain outside the published repository along with the retained source PDF.

The exact experimental branch runs scoped Ubuntu 3.11 and Windows 3.12 CI;
all PRs, main and other branches keep the original full jobs. The four original
matrix executions are intentionally not run for this exact experimental push
and must not be reported as passes. Remote run IDs/conclusions are recorded in
the final immutable parent handoff after publication; this document does not
claim an unobserved remote outcome.

No new multi-hour full regression, exhaustive wheel smoke, browser check,
deployment, DOI registration, credential creation or permission change was
performed. The successful full a592 verification remains historical evidence,
not a full pass on this increment. Source transcription/software validation
does not establish independent scientific review or raw-data reanalysis.
Main release approval and the remaining per-class material gaps are unresolved.
