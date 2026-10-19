# Eight source-qualified NBS salt density candidates

This review-only packet proposes eight composition-level inorganic identities,
eight source-scoped states and eight numerical references against baseline
`efd4ca2a64c6b389c2a1fa9ba525f6fa77bbe93f`. It adds no grades or source records.
The existing NBS source object is frozen and reused exactly. Preparing this
packet does not modify runtime catalogs; `formal_admitted_delta` remains zero.

All values are source-reported measured-lattice-derived **crystallographic
density**. Each selected sentence expressly refers to NBS lattice or unit-cell
determinations. These are neither direct bulk measurements nor new calculations
by this project. Reported precision and temperatures are retained. Density-specific
uncertainty, independent specimen/repeat count, pressure, specimen porosity,
moisture content and conditioning duration remain unknown. A reported density
is not automatically a mean, engineering allowable or universal material value.

## Selected original NBS results

Units are grams per cubic centimeter (`g/cm^3`), explicitly defined in the
Introduction, printed page 2 / one-based PDF page 6. Each density temperature
comes from its own density sentence, separately from processing and pattern
measurement temperatures. The selected sections form one adjacent source group;
section 2.49 is excluded because its orthorhombic NaCN is the same composition.

| Composition and selected phase | Density | Temperature | Section | Density locator: printed / one-based PDF page |
| --- | --- | --- | --- | --- |
| Hg2Cl2, tetragonal | 7.176 | 26 degrees C | 2.43 | 73 / 77, bottom left below lattice table |
| HgCl2, orthorhombic | 5.49 | 26 degrees C | 2.44 | 74 / 78, upper left below lattice table |
| HgI2, tetragonal | 6.325 | 26 degrees C | 2.45 | 76 / 80, upper left |
| PbFCl, tetragonal | 7.13 | 26 degrees C | 2.46 | 76 / 80, right column below lattice table |
| KCN, face-centered cubic with disordered CN group | 1.555 | 25 degrees C | 2.47 | 78 / 82, lower left below lattice table |
| NaCN, face-centered cubic with disordered CN group | 1.591 | 26 degrees C | 2.48 | 79 / 83, left column below lattice table |
| Sr(NO3)2, simple cubic | 2.986 | 26 degrees C | 2.50 | 81 / 85, bottom left |
| Ba(NO3)2, simple cubic | 3.244 | 26 degrees C | 2.51 | 82 / 86, bottom left |

Sample provenance and limitations are independently attached to each state:

- **Hg2Cl2:** General Chemical Company label 1891, printed pages 72-73 / PDF
  pages 76-77. NBS spectrography reports Cu and Fe traces, faint Al/Mg/Si traces,
  and an alkali-element detection limit of about 0.05 percent. This is not a
  numerical total-purity specification. Sample processing is not established.
- **HgCl2:** J. T. Baker sample 101742, printed page 73 / PDF page 77, right
  column. NBS reports no individual impurity greater than 0.01 percent; this is
  not a bound on total impurities or a certified-grade claim.
- **HgI2:** Mallinckrodt sample, printed page 74 / PDF page 78, right column.
  The supplied sample was stated to be of ACS purity; NBS reports Fe and faint
  Ca/Cr/Mg/Si traces. Preserve the supplied-sample claim without granting
  certification. Only tetragonal HgI2 is selected; no red/alpha label is inferred.
- **PbFCl:** NBS chemical-laboratory material, printed page 76 / PDF page 80,
  left column, prepared for a project on precise fluorine determination. The
  source's high-purity description remains qualitative. No numerical assay,
  lot or synthesis recipe is invented. This is not the separately discussed
  natural Matlockite specimen or its historical mistaken Pb2OCl2 formula.
- **KCN:** Mallinckrodt lot GNB, printed page 77 / PDF page 81, lower left.
  NBS chemical-laboratory percent entries are Cl 0.05, PO4 0.005, SO4 (total S)
  0.005, Fe 0.03, Pb 0.0000 and Na less than 0.05. Printed zero is not proof of
  absence. The source's warning that unit-cell measurements have not been of
  very high accuracy does not supply a numerical density uncertainty. The
  density explicitly uses 25 degrees C, not the neighboring 26-degree condition.
- **NaCN:** J. T. Baker sample 121444, printed page 78 / PDF page 82, upper
  right. NBS reports ACS-standard conformity and percent entries NaCN 96.2,
  Cl 0.02, FeCN 0.00, SO4 0.00, S 0.003 and source label `Thiocyanite` 0.02;
  the remainder is described as CO3 and H2O. Labels and rounded zeros are
  preserved without chemical modernization or an exact remainder calculation.
  Printed page 79 / PDF page 83 records sodium-carbonate reflections and the
  strong orthorhombic NaCN line omitted from the cubic pattern table. The
  selected 1.591 is only the indexed cubic-phase crystallographic density,
  never a pure-sample or contaminated whole-specimen bulk-density claim.
- **Sr(NO3)2:** specially purified Mallinckrodt sample, printed pages 80-81 /
  PDF pages 84-85. The supplier's spectrographic analysis reports Ba and Na
  each below 0.01 percent, the only impurities reported as greater than traces.
  This is supplier analysis, not NBS analysis or an exact total-purity assay.
- **Ba(NO3)2:** specially purified Mallinckrodt sample, printed page 81 / PDF
  page 85, right column. The supplier's analysis reports Al/Na/Sr each below
  0.01 percent. Purification details, total purity, lot and certified grade
  remain unknown.

Unit-cell contents, averaged diffraction-line counts and the source's general
lattice error are not specimen counts or density uncertainty estimates.
Independent selected-source transcription review is recorded in
[source-review.json](source-review.json), SHA-256
`3541b95cd3ae46e6fa393c92184d7fc4878cdf57e8b6fb74e81ed1a3ebbcf8f2`.
It confirms all eight density/temperature pairs and records the focused visual
correction of the NaCN analysis label from a preliminary `SO3` transcription to
printed `SO4`. The reviewer did not repeat a rights review. Both
`independent_scientific_review` and `raw_data_reanalysis` remain false.

## Source bytes and frozen rights scope

Howard E. Swanson and Eleanor Tatge (1953), *Standard X-ray Diffraction Powder
Patterns, Volume I*, National Bureau of Standards Circular 539.
[DOI 10.6028/NBS.CIRC.539v1](https://doi.org/10.6028/NBS.CIRC.539v1) and
[official PDF](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf).
The retained complete 104-page PDF has 6,422,795 bytes and SHA-256
`003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c`.
Local retained path: `incremental-evidence/material-growth-20261014/sources/nbs-circular539-v1-complete.pdf`
(relative to the task workspace, outside this repository). Selected text and
page images were inspected; no fresh retrieval or whole-volume reassessment
was performed for this batch.

Source ID `swanson_tatge_1953_nbs_circ539v1` is the exact existing registry
object. Its canonical JSON record hash, including a trailing newline, is
`af69ed341f5d81b6cd651b984ce489462f8ea798dfa95a98ace78a91b153bade`.
The source registry's wording, date and rights decision are not modified.

The retained [NIST Technical Series rights notice](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications)
has 93,931 bytes and SHA-256
`7277db527945beefe164286cea84cb98c46d21c3194b007420961930df462e94`.
The existing employee-authored-work scope applies to the selected NBS-authored
facts: domestic public-domain treatment and the notice's worldwide perpetual
royalty-free reuse permission where NIST asserts foreign rights. This is not
CC0 or blanket permission for third-party content. Third-party comparison
patterns, lattice/optical values, full source tables, PDFs, images and raw
structural assets are excluded. Only selected facts, bibliographic information
and original source qualifications are curated.

Republished courtesy of the National Institute of Standards and Technology.

## Identity reconciliation and counting limits

The pinned baseline has 1092 core identities, including 32 inorganic identities,
and 24 accepted computed composition buckets: 1116 project identities. Its
separate 62 computed examples remain unadmitted. Names, aliases and source/state
composition descriptions were checked against the eight formulas. Accepted
computed reduced-element compositions were checked in the unchanged formal
computed-review registry, SHA-256
`a285523b2b2fdbf0d750ce6ac56e3abfb80d5c42056229a2352b016a787fd875`.
No standalone composition match was found for these eight candidates.

Hg2Cl2 (Hg:Cl 1:1) and HgCl2 (Hg:Cl 1:2) are different compositions. Supplier,
lot, phase, temperature and impurity mentions do not create additional identity
credit. Already admitted NBS salts NH4Cl, LiF, LiCl, NaF, KF, KCl, KBr, KI, CaF2
and BaF2, and the earlier oxide group, are excluded. Orthorhombic NaCN in section
2.49 (1.620 at 6-7 degrees C, printed page 80 / PDF page 84) is another state
of the same NaCN composition and is not included as a ninth material.

Separate review and integration would take core 1092 to 1100, project 1116 to
1124 and core inorganic 32 to 40. These are projections, not present admission
or publication claims. The packet supplies explicit English fallbacks in all
four required locale name slots; no native-language review is claimed.

## Reproducible preparation

The [packet specification](packet-spec.json) uses shared inorganic state and
density contexts with explicit per-row facts. The existing compiler is unchanged;
no per-record code or source-approval inference is introduced.

```sh
python scripts/prepare_formulation_packet.py \
  --spec experimental/material-batches/nbs-salt-densities-20261019/packet-spec.json \
  --baseline-dir /path/to/efd4ca2/materials_boundaries/data \
  --output experimental/material-batches/nbs-salt-densities-20261019/prepared-packet.json
```

The baseline must retain the exact pinned bytes. After integration, replay
requires a separate frozen baseline checkout. A machine-ready packet is not
scientific approval, a new rights grant or formal admission. Identical replay
must preserve bytes and modification time; a different artifact cannot replace
an existing output. Actual preparation results are recorded separately below.

The [actual preparation receipt](preparation-receipt.json) records one `Created`
invocation and one identical `Unchanged` replay, both exit zero, using the native
immutable writer. The 223,065-byte [prepared packet](prepared-packet.json) kept
SHA-256 `091239fd1cc6e4d7d8429aab381f1a9525f62293339fc4fbea230142f53b541f`
and modification time `1792445082951637900` ns across both runs. The compiler
report records eight identities, eight states, eight properties, zero grades,
zero sources and no pending machine gates; formal admitted delta is zero.
No product tests, source requests, runtime catalog writes, commits or pushes
were performed by this candidate-preparation task.
