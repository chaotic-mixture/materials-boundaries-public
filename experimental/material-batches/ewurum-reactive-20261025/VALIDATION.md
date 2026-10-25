# Candidate validation

The candidate is prepared against `8ccd217599fd462d13d7435bdfb02a0825e4eacd` and remains outside runtime catalogs.
Actual admission delta is **zero**. The compiler's hypothetical merge is four
composite identities, four states and four measured modulus records, with zero
new sources and zero grades. Independent immutable candidate review is pending.

## Executed checks

Native Windows, CPython 3.11.0, separate bounded fresh processes:

| Group | Final methods passed | Failures/errors/skips | Elapsed seconds |
| --- | ---: | --- | ---: |
| New candidate suite | 20 | 0 / 0 / 0 | 95.312 |
| Complete existing formulation compiler module | 11 | 0 / 0 / 0 | 36.812 |

These are 31 distinct final passing methods, not one uninterrupted full-core
run. The compiler module includes the frozen four-formulation replay. The new
suite binds source rows, means/SDs, authorship, nominal composition, unknowns,
source reuse, state/identity counts, exact joins, all 22 canonical inventory
inputs, output replay, byte/mtime idempotence, and negative gates for drift,
aliases, clones, missing properties, wrong units and forged reports.

The first candidate run completed 20 methods: 19 passed and one errored in a
synthetic test fixture. Its exact duplicate state was correctly rejected by the
existing structural-clone guard. The repaired test first requires this rejection,
then tests a deliberately synthetic different geometry under the same identity.
No synthetic fixture is written into the packet. The unchanged production guard
was not relaxed. The full 20-method candidate suite was rerun after the fix.
Original failing logs, IDs, hashes and timings remain recorded separately.

The first preparation attempt failed at Windows atomic replacement with
`WinError 5`; no candidate output or temporary file remained. A normal approved
execution of the unchanged compiler created the candidate. Repeating it preserved
every output byte and modification time. That initial failure is not counted as
a pass or skip. See `preparation-receipt.json` for exact input/output bindings.

## Preservation and unrun scope

All **1030** baseline Git blobs are unchanged; this total **includes 122**
historical fixtures. Scientific catalogs, source records, workflows, 147-module /
1887-ID root inventory, 459/492/417/519 partitions, and 70-ID replay inventory are
unaltered. The identity audit rereads 22 exact baseline inputs and two separately
bound prior packet reviews, covering 14171 label occurrences, 8261 normalized
labels and all 63 polymer/composite identity scopes.

Only 11 of the 1887 frozen root IDs were executed here; **1876 remain unrun**.
The 20 new methods are explicitly discovered outside that inventory. The 70
replay methods, fresh installed package/API/CLI suites, wheel smoke, hosted CI,
Linux and other Python versions were not run for this candidate. None are skips
or passes. No runtime admission, remote push or scientific replication occurred.

Current experiment counts remain 1164 source-qualified identities plus 24 reviewed
computed records = **1188**; source-qualified categories are natural 1010, metal
32, inorganic 59, polymer 30 and composite 33. Their gaps to 1000 are 0, 968, 941,
970 and 967 respectively. Main remains at its last verified 1081; 62 excluded
computed examples are not admissions. Proposed counts are not reported as growth.

## Reproduce locally

Use the repository's existing test dependencies from the repository root. These
commands work with a selected Python executable on Linux or Windows:

```text
python -X utf8 experimental/material-batches/ewurum-reactive-20261025/build_identity_review.py --check
python -X utf8 scripts/prepare_formulation_packet.py --spec experimental/material-batches/ewurum-reactive-20261025/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/ewurum-reactive-20261025/prepared-packet.json
python -X utf8 -m unittest discover -s tests/ewurum_reactive_candidate -p test_ewurum_reactive_packet.py -v
python -X utf8 -m unittest discover -s tests -p test_formulation_packet_preparation.py -v
git diff --check
```

The existing baseline and full Git objects are required. The JSON ledger includes
exact test IDs, executable scopes, hashes, final outcomes, previous failure and
every unrun boundary. No raw PDF, screenshots, private paths or source dumps are
included. Cached source verification is described separately in `source-review.json`.
