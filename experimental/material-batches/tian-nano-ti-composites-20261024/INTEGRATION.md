# Tian 2023 experimental runtime integration

The independently reviewed corrected candidate is commit
`497dcc8495c32b16f02cdedce8b99f6b7d05f2c4`, tree
`846840acedb9eb6a6eac41ee151c9411c5a48b7d`. Its nine batch artifacts remain
byte-identical, including their historical zero-admission statements and
authorship review history. The candidate test receives only a strict historical
baseline adapter; its original bytes and all scientific assertions remain
recoverable.

The local data-only append is commit
`f7086fc049dc40319d7daa9ffb9bd5fdece55856`, directly following that candidate.
The runtime predecessor is published commit
`5a9a85c573f590d206cddb4cb7c085f334a0fbc0`. Only the three catalog tables
changed in the append: 714 added lines and zero deleted lines. All predecessor
objects and their order are preserved. The existing strict integrator validated
the graph and an exact second merge produced no increment. Product/package
validation and independent implementation review are separate gates.

## Local source-qualified scope

The appended source graph contains **1161 identities, 31 grades, 1162 states,
1173 properties and 127 source/provenance records**. Category counts are natural
1010, metal 32, inorganic 59, polymer 30 and composite 30. The exact increment is
two composite identities, two states, two measured density properties, one
source and zero grades. Existing computed records remain 24; the combined local
projection is 1185 subject to the installed product checks reported separately.
The 62 excluded computed examples are not admitted. Published experimental
baseline remains 1183; main remains 1081. No push, main merge, deployment or DOI
registration is performed by this implementation document.

The two formulations are source-qualified Mg-3Al-1Zn (AZ31) matrix composites
with nominal 0.5 wt% and 1 wt% nano-Ti additions. These are distinct nominal
reinforcement loadings, not analyzed final compositions or certified grades.
Each has one as-extruded state and one Table 2 Actual Density: 1.7425 and
1.7442 g/cm3 respectively. The literal second label `1 wt Ti` retains its missing
percent sign; sections 2.1 and 2.2 separately establish nominal 1 wt%.

Density temperature, pressure, humidity, specimen count, repetitions,
aggregation, uncertainty, density basis and porosity remain unknown. The
reported method is a digital densimeter. Tensile room temperature and the three
tensile specimens do not qualify density. Theoretical densities, derived
porosity, tensile properties and the unreinforced comparator are excluded.
`mat_chen2023_az31` remains the different-study unreinforced comparator; no
same-lot equivalence or comparator count growth is asserted.

The source record has exactly eight ordered authors. Bolv Xiao is Academic
Editor and is excluded from authorship. The original attribution defect,
expected failing regression and corrected candidate validation remain in the
unchanged candidate evidence. Source transcription and software tests do not
establish independent scientific review or replication.

## Source bytes, rights and exact preservation

The official Europe PMC XML, version `PMC10054318.1`, is the archived article
evidence for identity, methods, values and article-specific CC BY 4.0. The
publisher-formatted mirror PDF's size and MD5 match the official archive PDF
manifest. Direct primary-host PDF download and primary-host SHA-256 byte
equivalence remain unverified. Attribution, curation notice and this distinction
are preserved. Original PDF/XML assets, screenshots and private execution notes
are not distributed.

Source order and runtime ID order agree for these two rows. One finite packet
descriptor therefore identifies the exact two identity/state/property additions
and the single source. Hash-bound recovery preserves predecessor bytes and
rejects partial, duplicated, reordered or substituted additions. The historical
engine is unchanged; the parked `a6d3e5e` optimization is not incorporated.

Finite file and document recovery retains predecessor workflow, product pins,
tests and documentation. Existing current-count validation still runs before
historical prose projection; false-count rejection is not relaxed. Candidate
statements remain attached to their historical candidate snapshot rather than
rewritten as runtime completion claims.

The detached `integration-report.json` retains the existing integrator's zero
formal/main-admission marker. It describes the proposed graph; this document
records its subsequent local experimental application. Neither grants
publication authority.

## Reproduce and review

```text
python -X utf8 scripts/validate_catalogs.py
python -X utf8 -m materials_boundaries catalog materials --identity-id mat_tian2023_az31_ti_0p5wt --json
python -X utf8 -m materials_boundaries catalog reference-properties --material-id state_tian2023_az31_ti_1wt_as_extruded --json
python -X utf8 experimental/material-batches/tian-nano-ti-composites-20261024/build_identity_review.py --check
```

Use an environment with the repository's development dependencies for schema
validation. Recompile the unchanged candidate against a separate exact `5a9a85c`
catalog, not the advanced runtime tables. The preservation tests reconstruct
that baseline. `INTEGRATION_VALIDATION.md` and
`integration-validation-results.json` report actual runtime execution, retained
failures and unrun coverage. Historical candidate Windows/Linux passes are not
runtime test results. Independent implementation review precedes any push.
