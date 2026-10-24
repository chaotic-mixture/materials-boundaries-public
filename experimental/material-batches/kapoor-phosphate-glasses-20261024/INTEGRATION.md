# Kapoor 2019 experimental runtime integration

The independently reviewed candidate checkpoint is
`c275ae6051277ad6d08077b2937527907eb2380f`, tree
`8a627e6b647ecf6d8a7f9d33f1301c2c5ebb4236`. Its nine batch artifacts remain
unchanged, including their historical zero-admission statements. Its 17-method
candidate test needs only an exact historical-baseline adapter after the append;
the original test bytes, scientific assertions and pins remain recoverable.

The local data-only append is commit
`76cae67a9401b916c1409ad3c2212fa3c103be6f`, with the reviewed candidate as its
parent. Runtime predecessor data is the published
`196995256836db2d8f870ac9a91f664bfdd03e7f` checkpoint. The append changes only
the three catalog JSON tables, adding 2,153 lines and deleting none. Strict
schema/integrity validation passed. Every previous object and its order remain
unchanged, and a second exact merge produces no further increment. Implementation
validation and independent parent review remain separate from candidate review.

## Local counts and scientific scope

The validated source-qualified graph contains **1159 identities, 31 grades,
1160 states, 1171 properties and 126 source/provenance records**. Its primary
categories are natural 1010, metal 32, inorganic 59, polymer 30 and composite 28.
The append is exactly six inorganic identities, six states, six measured
densities, one source and zero grades. Existing computed records remain 24;
the local combined projection is 1183 once verified through the installed
product. The 62 excluded examples are not admitted. The last published
experimental project remains 1177, and main remains 1081. No experimental push,
main merge, deployment or DOI registration is performed by this document.

The six study-qualified labels are P60, P50, P46, Al5, Al10 and Al15. Their
Table 1 densities remain 2.521, 2.654, 2.718, 2.614, 2.585 and 2.583 g/cm3,
respectively, linked by exact identity/state/property IDs. Compositions remain
analyzed ICP-OES mol%, not nominal recipes, mass fractions, certified purity or
validated final stoichiometry. Each grade is null. The selected state is
as-prepared, annealed and reannealed, not pressure-compressed.

At least ten measurement repetitions per sample do not establish the number of
independent specimens. The source-wide maximum SD of 0.002 g/cm3 is a bound,
not six individual SD values. Numerical uncertainty and independent sample count
remain null; an arithmetic mean is not inferred. Temperature remains only
"room temperature". Exact temperature, pressure, humidity, porosity and
row-specific melt schedules remain unknown. Hardness humidity and the viscosity
standard are not borrowed. Calculated molar volumes, packing densities and
compressed-state measurements are excluded. P60's unrelated EPDM token collision
and the historical salt PO4 impurity contexts remain explained in the frozen
finite identity review.

## Deterministic append and exact history

The existing production merge sorts newly appended records by ID. The paper's
source-row order remains unchanged in the candidate packet; runtime append order
is Al10, Al15, Al5, P46, P50, P60. Facts are joined by IDs, not zipped by position.
The unchanged historical engine preserves packet row order, so the new finite
data ledger uses six descriptors pointing to the same exact prepared packet,
each selecting one identity/state/property in runtime order. Only the first
descriptor selects the one source. These descriptors are neither six sources
nor additional admissions. Strict checks require each approved record exactly
once and reject partial, reordered, duplicate or substituted additions.

The new data/file ledgers and finite document bridge recover predecessor
catalog bytes, the candidate test bytes, documentation, workflow and product
pins. Historical counts and assertions stay bound to their original snapshots.
Live README counts must still match the live catalog before normalized prose is
projected backward; false-count rejection is retained. The historical engine and
the isolated unpublished `a6d3e5e` optimization are not changed or incorporated.

The detached `integration-report.json` retains the existing integrator's zero
formal/main-admission marker. It describes the proposed append graph; this file
records its subsequent local experimental application. Neither file grants
publication authority or turns source transcription into independent science.

## Reproduce and inspect

```text
python -X utf8 scripts/validate_catalogs.py
python -X utf8 -m materials_boundaries catalog materials --identity-id mat_kapoor2019_p60 --json
python -X utf8 -m materials_boundaries catalog reference-properties --material-id state_kapoor2019_p60_as_prepared --json
python -X utf8 experimental/material-batches/kapoor-phosphate-glasses-20261024/build_identity_review.py --check
```

Run the source candidate compiler against a separate exact `1969952` baseline,
not the advanced runtime tables. The preservation tests reconstruct and verify
that baseline for the unchanged packet. The runtime source, query, installed
package and CLI validation ledger will report actual terminal outcomes and
unexecuted coverage separately. Candidate Windows/Linux test passes are
historical evidence for the candidate checkout, not runtime test results.

Only curated facts, attribution, code, tests and documentation are distributed.
Original source assets, credentials and private execution notes are excluded.
