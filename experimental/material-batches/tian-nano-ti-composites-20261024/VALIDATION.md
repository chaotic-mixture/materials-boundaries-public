# Tian candidate validation

Baseline: `5a9a85c573f590d206cddb4cb7c085f334a0fbc0`.
Scope: candidate evidence, compiler input/output and focused tests only. There
is no runtime admission, catalog edit, package change, workflow change or push.

## Executed tests

Native Windows, CPython 3.11.0, with a 600-second budget per fresh process:

| Selection | Passed | Failed/errors/skipped | Unittest elapsed |
| --- | ---: | ---: | ---: |
| Complete `test_tian_nano_ti_packet.py` | 18 | 0/0/0 | 60.033 s |
| Existing compiler gate methods listed in `validation-results.json` | 10 | 0/0/0 | 1.591 s |

All 28 distinct methods completed with child exit code 0. Exact method IDs,
commands, start/end times, log hashes and before/after input hashes are retained
in `validation-results.json`. Input hashes remained unchanged during and after
the runs. Tests cover the two selected Actual Density cells, literal source
labels, nominal composition, state/identity separation, density unknowns,
tensile-condition isolation, source/rights gates, archive-manifest provenance,
finite identity inputs, baseline drift, aliases, missing properties, wrong
units, forged prepared output and deterministic/idempotent writes.

The private receipt wrapper initially returned 1 because its `^OK$` expression
did not accept raw Windows CRLF output. Both underlying unittest processes
returned 0. The unchanged original logs were reparsed with `splitlines`, checking
every expected method ID, terminal `OK`, zero failures/errors/skips and matching
input hashes. The original receipt hashes and the correction are retained.
No test was rerun or weakened to correct this receipt-only parser issue.

The historical full-prefix replay method in the existing compiler module was
not selected. Other core modules, installed-wheel/package/API suites, Linux
tests and hosted CI were not run for this candidate-only change. These are
unrun checks, not passing or skipped tests. Installed CLI coverage is unchanged.

## Reproduction and retained failed attempts

The finite audit's exact 22-object replay passed and left the generated review
bytes and mtime unchanged. It covers 14111 label occurrences, 8241 normalized
labels and all 60 existing metal/composite identities. Packet replay took
4.906 seconds and preserved both output bytes and mtime. The prepared packet
is 61469 bytes, SHA-256
`cf5df75a8f8fbe27ac380771d5f5b5fae70668ddf365414a029acaa952458f80`.
The three runtime tables match the exact baseline bytes; no Tian identity is
present in them.

Initial strict compilation rejected four authoring defects: a null explanatory
sample-count string, an incorrectly shaped discrepancy entry, missing inspected
document value evidence, and a missing condition-support tag. The candidate
input was corrected to the existing contracts; no validator changed. The
recorded hash-note shape was also aligned with the existing contract while the
mirror limitation remained explicit in inspection scope. A later sandbox
atomic-rename attempt failed with WinError 5 after validation. After verifying
that no output existed, the unchanged compiler succeeded with native filesystem
access. These attempts are preserved in `preparation-receipt.json`, not counted
as test passes.

Source acquisition initially failed under sandbox DNS restrictions. The bounded
native public reads then independently verified the official XML and mirror PDF
bytes recorded in `source-review.json`. Direct primary-host PDF download and
primary-host SHA-256 byte equivalence remain unverified. No raw asset is in this
candidate packet.

## Count and review boundary

The project remains **1183 = 1159 source-qualified identities + 24 existing
computed records**. Category counts remain natural 1010, metal 32, inorganic 59,
polymer 30 and composite 28. Main remains 1081. Actual admitted delta is zero.
Compiler output proposes only a hypothetical two-composite increment.

Independent parent review of the immutable candidate commit is pending. Source
transcription and software tests do not establish scientific replication or
independent scientific approval. Runtime integration and experimental publication
require the next separate review stage.
