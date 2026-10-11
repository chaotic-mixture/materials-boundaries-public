# Resumable NOMAD review-queue updates

`nomad_incremental.py` extends the existing bounded NOMAD collector and candidate
normalizer. It maintains a local observation baseline and produces a reviewable
delta after each complete acquisition cycle. It uses Python 3.11+ and the standard
library; it does not require a service, account or credentials.

Automatic acquisition is not scientific review, license clearance or admission.
The formal project total remains **1081 = 1057 legacy identities + 24 reviewed
computed composition buckets**. The 62 unadmitted computed examples, the older
seven-record example and their known related provider IDs are excluded from new
candidate admission claims. This command never changes the formal catalog.
Candidate groups and calculations contribute **zero** admissions and do not count
toward the goal of at least 1000 materials in each of five categories.

## Collection scope

Initialize one immutable profile per store. The default profile revisits one page
of two public OQMD bulk entries, ordered by `entry_id`, on every complete cycle.
`--after` fixes the starting cursor; subsequent page cursors are persisted while
that cycle runs. The next cycle restarts at the configured starting cursor so
changes to previously observed entries can be detected. It does not automatically
walk the entire provider dataset or represent a transactional snapshot.

Alternatively, repeat `--entry-id` to follow a small, fixed public entry cohort.
The unique cohort must fit `--page-size`, with `--pages 1` and no `--after`.
Exact-ID responses still undergo the OQMD origin and all other eligibility gates.

Previously observed IDs missing from the new window receive bounded, public
exact-ID archive checks. Only a validated, exhaustive exact-ID response can mark
an ID `withdrawal_pending_review`. That state means the public query did not
return it; it does not prove deletion or revoke an approved material. An entry
that moves outside the scanned window but remains publicly readable is retained
through these rechecks. A changed or reappearing record is reported separately.
Rechecks share the same cycle budget, so a growing observation history can exhaust
that budget instead of silently expanding acquisition.

## Reproduce a small local cycle

Run from `experimental/platform/ingestion`. Choose a persistent local store
outside the checkout; the following paths are examples.

```sh
python nomad_incremental.py init /absolute/local-data/nomad-small --pages 1 --page-size 2 --max-requests 8 --max-bytes 2000000 --max-response 500000 --retries 1
python nomad_incremental.py update /absolute/local-data/nomad-small
python nomad_incremental.py status /absolute/local-data/nomad-small
python nomad_incremental.py report /absolute/local-data/nomad-small > /absolute/local-data/nomad-small-report.json
python nomad_incremental.py report /absolute/local-data/nomad-small --cycle 1 > /absolute/local-data/nomad-small-cycle-1.json
```

`init`, `status`, `report` and `abandon` are offline commands. Only `update`
performs public network reads. Output is JSON on standard output; argument or
store errors are written to standard error. In PowerShell, use a Windows path
such as `C:\local-data\materials-boundaries\nomad-small` in place of the example
store path.

`status` includes a `history` list with each cycle's `id`, `status`, `requests`,
`bytes_charged` and `started_utc`, alongside the latest cycle state. Use one of
those IDs with `report STORE --cycle N` to retrieve an earlier cycle's report
offline. Omitting `--cycle` selects the latest cycle; a nonexistent cycle is an
error. Completed and abandoned reports remain available after later updates.

To configure a fixed cohort, initialize a separate store and replace the example
IDs with verified public NOMAD entry IDs:

```sh
python nomad_incremental.py init /absolute/local-data/nomad-cohort --pages 1 --page-size 2 --entry-id ENTRY_ID_1 --entry-id ENTRY_ID_2 --max-requests 8 --max-bytes 2000000 --max-response 500000 --retries 1
python nomad_incremental.py update /absolute/local-data/nomad-cohort
```

Rerun `update` on the same store. If the previous cycle completed, this starts a
new bounded cycle and compares its source content with the committed baseline.
Unchanged input yields no input or candidate delta, even though the new cycle has
its own retrieval evidence and timestamps. If the previous cycle is incomplete,
the command resumes it using the durable cursor and successful response cache.
Partial cycles never advance the committed baseline.

The example limits above are also the defaults. Supported limits are:

| Option | Meaning | Allowed range |
| --- | --- | --- |
| `--pages` | Initial window page limit | 1..10 |
| `--page-size` | Maximum entries per request | 1..100 |
| `--max-requests` | HTTP attempts per cycle, including retries and rechecks | 1..32 |
| `--max-bytes` | Total charged response bytes per cycle | 1..30,000,000 |
| `--max-response` | Response byte limit, no larger than `--max-bytes` | 1..3,000,000 |
| `--retries` | Additional attempts per logical request | 0..3 |

The HTTP timeout is 30 seconds. An interrupted in-flight request keeps its
reserved request count and response-byte allowance charged, even if no response
was committed. This conservative accounting prevents restarts from restoring
spent budget. A size-limit probe may read one extra byte to detect overflow and
then rejects that response; it does not accept an oversized response as evidence.
The profile cannot be overwritten by repeating `init`. Any intentional new scope
or limits require a separate store and a separately reviewed acquisition plan.

## Recovery and scheduling behavior

The store contains `incremental.sqlite3` and `.update.lock`. SQLite persists the
profile and its hash, the pinned review boundary and its hash, cycle state,
request reservations, exact accepted response bytes and hashes, acquisition
records, and the last complete observation baseline. An archive response is
committed before its attribution request; a restart can reuse it. Keep the whole
store for audit and recovery, and back it up only when no update is running.

An exclusive, nonblocking OS file lock permits one writer per store. A concurrent
writer is rejected, and the OS releases the lock after process termination. The
presence of `.update.lock` alone is not a stale-lock error; deleting it is not a
recovery procedure. Use local storage with working SQLite and OS locking.

| Result | CLI exit code | Operator action |
| --- | --- | --- |
| Complete `update` | `0` | Inspect the report; the next update starts a new cycle. |
| Paused or cooldown `update` | `2` | Inspect `status`; rerun after the recorded cooldown, if any. |
| Exhausted or blocked `update` | `2` | Investigate and explicitly abandon the incomplete cycle if a new attempt is appropriate. |
| Invalid arguments, invalid store or lock conflict | `2` | Correct the reported error; no successful cycle is implied. |
| Successful offline command | `0` | Inspect its JSON output; this does not imply acquisition completed. |

HTTP 429 and 503 responses persist `Retry-After` as an absolute cooldown, including
HTTP-date values. The command returns without waiting through that cooldown. A
repeated job during cooldown performs no new request. Public requests also use a
persisted last-dispatch time for one-second request spacing; this pacing may
sleep for up to one second. Transport failures retain the partial cycle;
remaining attempts are consumed only by later invocations. Per-request retries
and cycle budgets persist across process restarts. Repeated scheduling must not
silently reset exhausted budgets or abandon failed cycles.

After investigating a blocked or exhausted cycle, an operator may explicitly
record abandonment:

```sh
python nomad_incremental.py abandon /absolute/local-data/nomad-small --reason "Reviewed incomplete cycle; author endpoint failed within the fixed retry budget"
python nomad_incremental.py update /absolute/local-data/nomad-small
```

Abandonment preserves the cycle, evidence and reason, leaves the last complete
baseline unchanged, and permits the next `update` to start a new bounded cycle.
The provider cooldown survives abandonment. Do not put `abandon` in a recurring
job or treat it as a way to bypass `Retry-After`.

## Local scheduling examples

These examples describe optional operator setup; this implementation installs no
schedule. Initialize the store and inspect a manual run before scheduling the
same `update` command. Hourly examples keep acquisition small; each invocation
remains subject to the persisted profile, retry limits and cooldown. There is no
cloud scheduler, deployment, credential generation or permission change.

For Windows Task Scheduler, replace the no-space executable, checkout and store
paths below with the actual local paths. This is an example registration command,
not an action performed by the project:

```powershell
schtasks.exe /Create /TN "Materials Boundaries Incremental Review" /SC HOURLY /MO 1 /TR "C:\Python311\python.exe C:\src\materials-boundaries-public\experimental\platform\ingestion\nomad_incremental.py update C:\local-data\materials-boundaries\nomad-small"
```

For paths containing spaces, configure the action in Task Scheduler with the
Python executable in **Program/script** and the quoted script and store paths in
**Add arguments**, for example:

```text
"C:\work projects\materials-boundaries-public\experimental\platform\ingestion\nomad_incremental.py" update "C:\local data\materials-boundaries\nomad-small"
```

Choose **Do not start a new instance** if the task is already running. The store
lock also protects manual/scheduled overlap. Task Scheduler result `0x2` requires
checking the offline `status` or `report`; it may mean a persisted cooldown or a
blocked cycle, not an empty successful update. Task history alone is not the
acquisition audit record.

For Linux cron, an equivalent hourly crontab entry is:

```cron
0 * * * * /usr/bin/python3 /srv/materials-boundaries-public/experimental/platform/ingestion/nomad_incremental.py update /var/local/materials-boundaries/nomad-small >> /var/local/materials-boundaries/nomad-small-job.log 2>&1
```

Use an existing writable local directory and a Python 3.11+ executable. The log
collects separate JSON reports across runs and is not itself one JSON document.
Inspect `report` for a single current report. Neither scheduler example performs
scientific approval or modifies catalog entries.

## Review the delta and evidence

`report` verifies stored evidence hashes and reads the selected cycle without a
network request. A completed report is retained with the cycle; an incomplete
report is provisional and must not be treated as a committed update. Historical
reports preserve their recorded state and cooldown, while `status` reports the
current store cooldown. Review:

- `complete`, `baseline_committed`, `status` and `stop_reason` before any counts.
- `input_changes` for new, changed, reappeared and withdrawal-pending entries,
  including old/new source-content hashes. These hashes exclude retrieval time.
- `candidate_changes` for new or changed provider groups and removals from the
  candidate queue pending review. Queue removal is not formal catalog revocation.
- `gate_exclusions` and `diagnostics` for missing evidence, identity conflicts,
  rights issues, overlapping reviewed/example identities and duplicate input.
- `candidate_packet` for the property, method, provenance, attribution and
  unresolved scientific/identity limitations attached to each proposed group.
- `acquisition`, `budget`, `limits` and `not_before_utc` for exact query scope,
  response hashes, failures, retries, resource usage and provider cooldown.

Identical repeated upstream rows are coalesced before normalization and reported
as diagnostics. Conflicting archive or attribution variants for the same entry
are quarantined. In the incremental packet, `acquired_entry_rows` counts distinct
observed entry IDs after identical-row coalescing, including held entries;
`acquired_entry_rows_basis` states that convention. It is not a raw response-row
count, a material count or an admission count.

Provider `material_id` groups repeated calculations; formula alone never creates
a global material identity. The pinned exclusion boundary includes primary and
known related entry/material IDs from the reviewed 24, the unadmitted 62 and the
earlier seven examples. If a known entry is observed with a different upstream
`material_id`, that entire provider group is held, including other calculations
in that group. Completed cycles persist these observed material-ID aliases, so
the hold survives later omission of the original known entry. The conservative
hold may exclude additional candidates if the upstream mapping conflates groups;
it requires human identity review and never creates an admission. Composition
overlap remains advisory and does not prove identity. Neither bounded sampling
nor these exclusions establishes equivalence with every legacy or other-provider
record.

Eligibility reuses the existing normalizer: explicit OQMD origin and `CC BY 4.0`,
named attribution, source processing provenance, consistent formula/elements,
bulk three-dimensional structure metadata, valid symmetry, a supported DFT method
and one finite positive density are required. Missing or invalid evidence is held
out of the candidate queue. Changes in eligibility remain visible in the delta;
an old passing result is not automatic approval of changed input.

The property is the provider's computed cell density at
`results.properties.structures.structure_original.mass_density`, whose source
schema declares a bare scalar in `kg/m^3`. Explicit alternative units and quantity
envelopes are rejected rather than converted or relabeled. A wrongly labeled
bare upstream scalar cannot be detected from this projection alone. The current
schema does not validate every historical processing commit. Temperature,
pressure, convergence, stability, equilibrium geometry and experimental existence
remain unverified. Scientific review and historical schema/source review are
still necessary.

Only the fixed official public NOMAD archive and attribution endpoints are read.
No cookies, authentication, environment proxies, alternate endpoints, redirects
or compressed responses are used. The projection requests scalar density and
metadata; geometry and raw structure/calculation assets are outside scope and
rejected if present. No source assets are uploaded. A provider license declaration
does not establish upstream ICSD structural rights or complete a rights audit.
Preserve source references, named authors, URLs, license and stated modifications
with any later approved distribution.

See the existing [collector interpretation and primary references](README.md)
for the scientific and rights limits, and the
[formal catalog policy](../../../docs/FORMAL_PROJECT_CATALOG.md) for admission
counting. DOI registration and public deployment remain deferred.

## Verification evidence

Run the offline ingestion tests from this directory with:

```sh
python -m unittest -v
```

The implementation's actual executed test results and explicitly budgeted public
NOMAD observations are recorded separately in
[VERIFICATION_INCREMENTAL.md](VERIFICATION_INCREMENTAL.md). That record must
distinguish fixture tests from live reads, complete cycles from partial failures,
and candidates from admissions. This usage document does not assert that a live
run succeeded or that every future run returns unchanged data.
