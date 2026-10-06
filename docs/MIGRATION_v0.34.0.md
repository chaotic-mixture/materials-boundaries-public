# Migration to v0.34.0

This catalog-only batch adds six identities, six states, six experimental
properties, one qualified source-designated grade (Ecoflex C1200) and three
original sources. Totals are **57 identities, 20 grades, 57 states, 57
properties and 108 source records**. It uses the existing schema/runtime
contract; material/reference envelope versions remain 1.0.0.

## Preserve scientific and statistical scope

- B0/B20 Young's moduli are 575 ± 65 / 960 ± 77 MPa, explicit mean ± SD,
  n=10. Keep the unresolved FZ91PM/FZ91PB designation with no grade selection.
  DCP preparation and hot-pressed discs do not define their tensile states.
- Indulin AT density is 1.226 g/cm³ by nitrogen pycnometry. Source density
  basis, center aggregation, n, temperature and uncertainty remain unknown.
- PHBV-39 Young's modulus is 0.87 ± 0.04 GPa, mean ± SD, **n≥5**. The suffix
  is operational day. Purity/HV composition ± values have unknown statistical
  semantics and do not inherit the mechanical SD definition. Loading is
  **3 N/min**, not a displacement/strain rate; room temperature has no numeric
  setpoint. Purified does not imply chemical purity.
- PBAT / PBS-PBAT 70/30 tensile moduli are 52.01 ± 28.78 / 253.49 ± 13.40
  MPa. Five specimens, 25 °C test and 48 h at 25 °C conditioning are explicit;
  center aggregation and ± meaning are not. Keep `reported_value` with
  `reported_plus_minus_unspecified`. The blend ratio basis is unspecified.
- No unit conversion, SD-to-SE/CI calculation, interval construction,
  density-strength inference, automatic evaluator input or ranking is added.
  PCL and biaxial-flexural-strength glass-ceramic candidates remain excluded.

## Compatibility and validation

All prior 51 identities/states/properties, 19 grades, 105 sources, schemas,
runtime code, scientific fixtures and eight executable rules are preserved.
The test-only successor layer records exact edits and recovers every file of
the 394-file v0.33.0 baseline, commit
`8ed6fa18369b43719174fc407f76bc073e265d7c`, tree
`754ff52504b8f661214a717c35d2155512f3e951`. Historical tests keep their original
assertions; their nearest preservation helper delegates through this exact
successor layer. It is never imported by production code or replay.

The existing same-size schema-cache mutation test now reads and writes bytes,
preserving its original LF or CRLF line endings on Windows. Previously, a text
write could enlarge an LF fixture before the cache assertions ran. The intended
equal-length type substitution and every size, timestamp and rejection assertion
are unchanged; the exact test edit is included in the reversible successor layer.
No schema or validator/cache implementation changes for this correction.
The v0.29 test helper also rechecks its exact predecessor hash after a reviewed
successor reversal, so a later change to a formerly unchanged file can recover
that exact baseline. Historical hashes and ledgers stay fixed; a regression test
checks successful exact recovery and rejection of altered or forged bytes.

Fresh reports carry software version 0.34.0. Strict replay requires the matching
software/catalog snapshot; regenerate reports explicitly from retained inputs,
without rewriting historical outputs or loosening replay. English, Chinese,
Japanese and German names retain source qualifications, while canonical JSON
remains language-independent.

Before release, run metadata preflight, development schema/graph validation,
the complete unit suite, old detail-output parity, six-fact source-semantic
guards, four-language queries, wheel metadata/isolated installation and the
visualization smoke check. Rehearse a fresh synthetic append in a disposable
copy with truthful current README counts and run its full suite as well.
These are verification requirements, not declarations of completed checks.

Only selected facts and original curation are public. The three original CC BY
4.0 PDFs, extracts and rendered pages remain outside the checkout. See
[coverage](MATERIAL_COVERAGE_v0.34.0.md) and
[rights/attribution](../THIRD_PARTY_NOTICES.md#polymer-and-biogenic-references-v0340).
No remote push, merge, release or deployment is performed by this change.
