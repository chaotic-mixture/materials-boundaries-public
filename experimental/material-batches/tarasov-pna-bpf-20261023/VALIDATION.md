# Tarasov candidate validation

This is a local review packet on `experimental/polymer-growth-tarasov2022`,
based on `faa002c55b7ad2d1bd962e905275894231ab8350`. Candidate source files are
frozen at `eb044bb024dff2a99c514605d3942a1769f77f80`. No runtime catalog,
formal catalog, product pin, existing test, CI workflow or remote ref is changed.

## Actual execution

Native Windows CPython 3.11.0 ran these complete focused modules with
`python -X utf8 -m unittest discover -s tests -p MODULE.py -v`:

| Module | Passed | Failed/errors | Skipped |
| --- | ---: | ---: | ---: |
| `test_tarasov_pna_bpf_packet` | 12 | 0 | 0 |
| `test_formulation_packet_preparation` | 11 | 0 | 0 |
| `test_formulation_packet_integration` | 7 | 0 | 0 |
| `test_material_append_merge` | 4 | 0 | 0 |
| `test_release_metadata` | 5 | 0 | 0 |
| Unique final tests | 39 | 0 | 0 |

The new module checks the independently transcribed five rows and decimal
precision, null grades, measured versus inferred quantities, all three source
contradictions, missing statistical/condition data, finite review boundaries,
immutable input hashes, exact baseline bytes, pending review/rights rejection,
alias and designation collisions, duplicate-state refusal, state versus identity
counts, malformed-property/unit/owner refusal, and deterministic immutable replay.

The existing full catalog validator passed against the unchanged baseline and
against the detached merged candidate graph, including local Draft 2020-12,
format and integrity checks. The preparation CLI created the frozen packet and
then reported `Unchanged`. Isolated integration was created outside the
repository; its identical repeat preserved both bytes and modification time.
Only its incremental report is retained here, not the full duplicate catalog.

An offline core wheel build passed with `--no-index --no-deps
--no-build-isolation`. Inspection confirmed exact baseline catalog bytes and
exclusion of candidate files and raw source assets. The separate fresh-installed
wheel smoke check exceeded its 900-second budget with `subprocess.TimeoutExpired`.
It did not return a terminal success result and is not passed. The remaining
task-owned worker was verified and stopped; no unrelated process was changed.
No retry was started. At the final process snapshot the worker had consumed
about 890 seconds of user CPU and held about 303 MiB of working set; these are
not peak-memory measurements or proof of any assertion result. Recheck this
existing smoke command boundedly on dot before publication acceptance.

`validation-results.json` records module results, log digests, input hashes and
the precise tested scope. Original execution logs remain local evidence.

## Preserved unsuccessful attempts and limits

The existing preparation module initially ran in the restricted Windows
sandbox: 10 passed and one errored at `os.link` with `PermissionError [WinError
5]`. A task-owned temporary directory produced the same result. Both original
failure logs are preserved. The complete unchanged module then passed all 11
tests in native Windows execution with hard-link support. No assertion, atomic
writer behavior or skip policy was changed.

An initial discovery-only command without UTF-8 mode encountered the existing
`test_composite_acceptance` fixture's implicit GBK decoding error. Discovery
with the same `-X utf8` mode as the actual test commands succeeded: 1743 core
methods, with an exact ID fingerprint recorded in the JSON receipt. Discovery
is not execution. The other 1704 core methods and all 535 tests in the full
installed test groups were not run in this candidate phase. No new hosted CI
run exists, and previous Bruns CI success is not attributed to this patch.

## Counts and remaining work

The detached graph has a candidate delta of five source-qualified polymer
identities, zero grades, five states, five strength properties and one source.
Its 1153 source-qualified identities are a proposed result, not admitted growth.
Both artifacts retain `formal_admitted_delta: 0`.

The actual experimental project remains 1148 source-qualified identities plus
24 computed records = 1172. Source-qualified category counts remain natural
1010, metal 32, inorganic 53, polymer 25 and composite 28. Main remains 1081;
62 computed examples remain excluded. Specimens, states, properties, source
records and calculations are never added to material-identity counts.

Parent independent review is pending. A subsequent approved runtime append
still needs exact history preservation, product pin/query/formal integration,
fresh-installed API regression coverage and a new bounded CI profile before
experimental publication. This candidate does not merge main, deploy, register
a DOI, upload original assets, or certify independent scientific review.
