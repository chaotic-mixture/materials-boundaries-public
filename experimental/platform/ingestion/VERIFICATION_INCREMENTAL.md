# Incremental update verification, 2026-10-11

Historical report: the Windows catalog failure and original test results below
describe the first verification stage. See [closure verification](VERIFICATION_CLOSURE.md)
for the exact-main reproduction, subsequent fixes, final checks and remaining
platform limits. The live NOMAD observations below have not been repeated.

## Outcome and scope

The bounded local update loop was implemented and exercised against public NOMAD.
It extends `nomad_batch.py` normalization with durable SQLite acquisition cycles;
it does not add another service, registry, admission path or deployment.

Remote `main` was verified as `4c5656cf6ba0ad1a54b736e0568e97abe4815c29` before
cloning into a separate work directory and creating
`experiment/nomad-incremental-review`. Existing local work was inspected read-only;
the older bulk-staging checkout's untracked `docs/BULK_STAGING_DESIGN.md` was
preserved. No `AGENTS.md` or `.agents/skills` was found in this checkout or its
ancestor directories. The experimental contribution guides were read.

The new clone initially inherited Windows CRLF conversion. Its tracked files were
restored from the exact Git archive with local `core.autocrlf=false` before tests;
no frozen hash or source data was changed to accommodate a mismatch.

Formal admissions remain **1081 = 1057 + 24**. The formal catalog snapshot is
`efea82e0f3ec2847a37807febe6bacffbd9624de2940f6e28bd481f75e9a6c14`.
The 62 additional examples remain unadmitted. The earlier seven examples and
known related provider identities are also excluded from new-candidate claims.
Neither calculation counts nor candidate counts establish formal completion.

## Executed offline checks

Environment: Windows, CPython 3.11.0. The six repository packages were built as
wheels, installed into an isolated virtual environment, and `pip check` passed.
Runtime dependencies follow `experimental/platform/requirements-lock.txt`.
The standalone incremental command uses only the standard library.

| Suite | Executed result |
| --- | --- |
| Ingestion, including incremental engine and independent review | 78 passed, 0 skipped |
| Federation provider fixtures | 19 passed, 0 skipped |
| Query service API/transport fixtures | 37 passed, 0 skipped |
| Lifecycle | 25 passed, 0 skipped |
| Linked integration and independent component checks | 18 passed, 0 skipped |
| Formal catalog core | 11 passed, 0 skipped |
| Broader optional computed/local catalog suite | 86 ran: 53 passed, 33 errors, 0 skipped; **not a suite pass** |

The six passing suites total **188 tests**, including **53 new ingestion tests**
(37 engine, 9 independent protocol/boundary tests and 7 unit/boundary tests).
The existing offline CI ingestion discovery automatically includes the new tests.
`git diff --check` also passed.

Coverage includes cached archive/attribution recovery after interruption,
multi-page partial failure without baseline commit, interrupted request budget
reservation, repeat runs with zero delta, duplicate/coalesced/conflicting inputs,
known-entry material-ID remapping across cycles, missing properties and authors,
wrong explicit units, license changes, exact-ID absence/reappearance, malformed
or missing cursors, HTTP 429/503 seconds/date cooldown, exhausted retries across
restarts, abandonment retaining cooldown, evidence tampering and writer locking.
These adverse upstream conditions were injected fixtures, not induced against
the live provider.

Two Windows environment issues were handled without changing project behavior:
the sandbox's temporary-directory rename restriction was avoided with a workspace
temporary directory, and its local event-loop pipe restriction required running
fixture tests with local loopback available. A verification-only audit guard
allowed Python's Windows `socketpair` loopback pipe while still blocking external
DNS and socket connections. The repository's unmodified strict guard was used
for the complete ingestion suite. Initial failed attempts are retained in the
local evidence directory; they are not counted as passes.

The remaining 33 optional-suite errors all report
`Installed legacy baseline differs from the recovery anchor` in the pre-existing
`computed_registry.baseline_digest()`. On Windows that function constructs
backslash-separated keys, while its frozen manifest uses POSIX keys. All **64**
installed baseline file hashes match when keys are represented with
`Path.as_posix()`; **15** keys contain separators on Windows. The existing
registry implementation and its pins were left unchanged. This is a separate
portability follow-up, not a successful wider catalog regression run.

The parent-owned main CI run **38096862915** was not retriggered or substituted
with this local evidence. No new remote workflow was started.

## Real public reads

The live experiment was capped at **8 total HTTP attempts**, two entries per
window, **1,000,000 response bytes per cycle**, **500,000 per response**, and a
30-second request timeout. Only the fixed official public archive projection and
attribution queries were sent. No credentials, structures, raw calculation files,
uploads, account operations or mutations were involved.

The default window used a per-cycle ceiling of four requests and one retry;
the second window, starting after literal cursor `0`, used two requests and no
retries. The overall eight-attempt experimental cap was enforced by the operator:
the first window consumed four attempts, leaving four for the second. No further
live requests were made.

| Window / cycle | Requests | Response bytes | Input changes | Candidate changes | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Default, cycle 1 | 2 | 4448 | 2 new observations | 0 | Both entries held by known-example boundary |
| Default, cycle 2 | 2 | 4448 | 0 | 0 | Idempotent repeat |
| After `0`, cycle 1 | 2 | 4686 | 2 new observations | 1 new pending group | One other entry held for carbon-category review |
| After `0`, cycle 2 | 2 | 4686 | 0 | 0 | Same pending group retained without duplicate increment |

Actual use: **8 requests, 18,268 bytes, 0 retries**, all HTTP 200. Captured UTC
times run from `2026-10-11T00:23:16.102631+00:00` through
`2026-10-11T00:26:36.626444+00:00`. Both stores passed SQLite integrity checks,
every retained response hash was verified, and historical `report --cycle`
replayed the saved JSON reports identically as parsed objects.

The one new group has provider material ID `q2WygBCnRWfQihBF4pa2-mSsYov4`, from
[NOMAD entry 0-0kf7ojgFG1q72oDQdMfaEBp-hB](https://nomad-lab.eu/prod/v1/gui/entry/id/0-0kf7ojgFG1q72oDQdMfaEBp-hB)
(source formula `CaEr2Eu`). It passed the automatic computed-density, provenance,
attribution and declared-license gates; **scientific and rights review remain
pending**. This is not a finding of experimental existence, global uniqueness,
mechanical validity or full redistribution clearance. It added **zero** formal
materials. The other entry was held for taxonomy review. The two default-window
entries matched the older seven-record example boundary.

Reproduce from the repository root with fresh local stores:

```sh
python experimental/platform/ingestion/nomad_incremental.py init STORE_A --pages 1 --page-size 2 --max-requests 4 --max-bytes 1000000 --max-response 500000 --retries 1
python experimental/platform/ingestion/nomad_incremental.py update STORE_A
python experimental/platform/ingestion/nomad_incremental.py update STORE_A
python experimental/platform/ingestion/nomad_incremental.py init STORE_B --pages 1 --page-size 2 --after 0 --max-requests 2 --max-bytes 1000000 --max-response 500000 --retries 0
python experimental/platform/ingestion/nomad_incremental.py update STORE_B
python experimental/platform/ingestion/nomad_incremental.py update STORE_B
python experimental/platform/ingestion/nomad_incremental.py report STORE_B --cycle 1
```

The provider is mutable; reproduction may return changed records or a bounded
failure. An operator must track the total experimental budget across stores and
stop on a failed cycle before extending the experiment. Repeating these commands
is not permission to perform an unbounded scan.

## Evidence and remaining work

[verification_incremental.json](verification_incremental.json) records exact
request/response/report SHA-256 values, counts, UTC times and test-log hashes.
Full reports, exact projected response bytes inside the two SQLite stores, wheel
and test logs, and verification scripts remain in the local sibling directory
`../incremental-evidence` relative to the repository root. Raw provider payloads
and SQLite stores are not part of this code patch or a published dataset.

The bounded scope does not cover all upstream changes, and public exact-ID
absence only proposes withdrawal review. The pinned boundary and conservative
remap aliases require operator review when changing scope or release policy.
No human review/admission UI, general scheduler service, full-provider change
feed or automatic catalog revocation was added. Scheduling commands are usage
examples; no OS scheduled task was installed.

Next: review this patch and the pending candidate, address the separate Windows
registry manifest-key issue, then let the parent coordinate any experimental
branch push. Five categories with at least 1000 formally admitted materials and
one traceable property each, broader interoperability, additional calculations
and interface work remain future objectives. DOI registration and public
deployment remain deferred.
