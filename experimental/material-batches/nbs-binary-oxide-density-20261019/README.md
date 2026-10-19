# Six additional source-qualified NBS binary oxide densities

This review-only packet proposes six composition-level inorganic identities,
six source-scoped states and six numerical references against baseline
`4db4ab591c0ee7b0a3580898b9f2ec75a2a52337`. It adds no grades or sources. The
existing NBS source object, rights scope and compiler are unchanged. Preparing
this packet does not write runtime catalogs; `formal_admitted_delta` remains zero.

The first volume still contains these unrepresented binary oxides. This batch
is limited to sections 2.24, 2.26-2.29 and 2.31. Previously admitted salts,
oxides and RCA compounds are excluded. Calcium hydroxide remains outside this
binary-oxide family. No second volume, alternate source or new retrieval was
needed, and no sample or polymorph was counted as an additional composition.

## Selected NBS density facts and temperature attribution

All values are source-reported measured-lattice-derived **crystallographic
density**, in grams per cubic centimeter (`g/cm^3`). The established unit scope
in the Introduction, printed page 2 / one-based PDF page 6, is reused. Every
selected density statement expressly uses NBS lattice or unit-cell data.
Preserve the original strings and precision; no modern atomic-weight
substitution, density recalculation or uncertainty propagation is performed.

| Composition and selected phase | Density | Temperature and its precise source basis | Section | Density locator: printed / one-based PDF page |
| --- | --- | --- | --- | --- |
| NiO, historical NBS cubic classification | 6.806 | 26 degrees C, explicit density sentence | 2.24 | 49 / 53, left column below unit-cell comparison |
| GeO2, source-designated hexagonal | 4.280 | 26 degrees C, underlying NBS unit-cell row | 2.26 | 51 / 55, right column below unit-cell comparison |
| As2O3, cubic arsenolite | 3.8654 | 25 degrees C, explicit normalized cell/density condition | 2.27 | 53 / 57, upper right |
| SeO2, source-assigned tetragonal | 4.16 | 26 degrees C, explicit density sentence | 2.28 | 54 / 58, upper left above Table 29 |
| SnO2, tetragonal cassiterite | 6.995 | 26 degrees C, underlying NBS unit-cell row | 2.29 | 54 / 58, bottom right |
| ThO2, cubic fluorite type | 9.991 | 26 degrees C, explicit density sentence | 2.31 | 58 / 62, lower left above section 2.32 |

For GeO2 and SnO2, the density sentence does **not** separately state a
temperature. It references the NBS unit-cell dimensions whose adjacent row is
labeled 26 degrees C. Their condition text is therefore explicitly
`26 degrees C (NBS unit-cell determination)`, with notes retaining the limited
attribution. This is not an independently measured bulk-density temperature.
For As2O3, 25 degrees C is the source-normalized cell/density condition; it does
not establish that every raw diffraction spacing was measured at exactly 25.

The PDF OCR rendered the NiO density as `6.R06` and the SnO2 decimal mark as a
comma. Page images confirm `6.806` and `6.995`. GeO2 remains `4.280`, including
its final zero. Independent source-review records retain both numeric values
and these exact reported strings.

## Sample, phase and purity qualifications

- **NiO:** Johnson, Matthey No. 3087, printed page 47 / PDF page 51, right
  column. The supplier estimated 99.99 percent purity; the source describes
  NBS spectroscopic corroboration showing faint Mg, Si and Ca traces. This is
  not a separate quantitative NBS 99.99-percent assay or certified grade.
  Printed page 48 / PDF page 52 discusses Rooksby's interpretation of line
  splitting at 18 degrees C as a slight rhombohedral distortion. Page 49 /
  PDF page 53 says the doubling was not detected on the NBS chart. Retain the
  historical cubic classification and unresolved-distortion qualification;
  non-detection does not disprove another structure.
- **GeO2:** Johnson, Matthey No. 3662, printed page 51 / PDF page 55, upper
  left. The supplier's spectrographic analysis reports a faint Ca trace, with
  no numerical concentration or total purity. The right column identifies
  the NBS phase as hexagonal and discusses a historical ASTM card incorrectly
  labeled tetragonal. No universal value across GeO2 polymorphs is inferred.
- **As2O3:** Mallinckrodt No. 906487, printed page 53 / PDF page 57, left
  column. The supplier spectrographic report places Ca/Fe/Mg/Pb/Sb/Si in the
  range 0.001-0.01 percent. Preserve the grouped range without allocating a
  separate number to each element or inventing total purity. The material
  was recrystallized by sublimation before use; temperature, duration and a
  separate post-sublimation quantitative assay are not reported. The chosen
  cubic arsenolite specimen is distinct from the unselected monoclinic
  claudetite and natural-sample comparisons.
- **SeO2:** specially purified Mallinckrodt material, printed page 53 / PDF
  page 57, right column. NBS spectrography reports no impurity greater than
  0.001 percent; this per-impurity observation does not establish total purity
  or lack of hydration. The very hygroscopic sample was mixed with petrolatum.
  A few weak monohydrate reflections remained and were omitted from the
  reported pattern. Monohydrate and petrolatum fractions are unknown. The
  selected 4.16 belongs to the source-assigned tetragonal SeO2 lattice, not
  the bulk petrolatum/hydrate mixture. Historical monoclinic descriptions or
  probable space-group alternatives are not recast as new determinations.
- **SnO2:** Johnson, Matthey No. 2763, printed page 54 / PDF page 58, sample
  paragraph begins lower left and continues upper right. The accompanying
  spectrographic report shows no impurity lines stronger than faintly visible.
  Individual impurity identities, concentrations, numerical total purity and
  independent NBS quantitative assay are not established.
- **ThO2:** Lindsay Light and Chemical Company, West Chicago, printed page 57 /
  PDF page 61, upper right. The 99.99-percent purity is explicitly the supplier's
  statement; no independent NBS chemical assay, impurity breakdown or sample
  number is supplied. Missing temperatures for third-party comparison patterns
  do not erase the selected NBS density's explicit 26-degree condition.

All sample counts, density-specific uncertainty, standard deviations, pressure,
porosity, humidity and conditioning duration remain unknown. Unit-cell contents
and diffraction-line counts are not statistical specimen n; general lattice
error is not a density error bar. Reported density is not automatically a mean,
direct bulk measurement, engineering allowable or universal value. Supplier
purity statements do not become certified grades, and percentage bases are not
invented. No raw structure validation or experimental replication occurred.

## Retained primary source and independent checks

Howard E. Swanson and Eleanor Tatge (1953), *Standard X-ray Diffraction Powder
Patterns, Volume I*, National Bureau of Standards Circular 539.
[DOI 10.6028/NBS.CIRC.539v1](https://doi.org/10.6028/NBS.CIRC.539v1),
[official PDF](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf).
The retained 104-page PDF has 6,422,795 bytes and SHA-256
`003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c`.
Task-workspace retained path:
`incremental-evidence/material-growth-20261014/sources/nbs-circular539-v1-complete.pdf`.
Selected author-side page images remain outside this repository under
`incremental-evidence/primary-table-growth-3-20261019/source-inspection/`.
Neither the PDF, page images, complete source tables nor raw structural assets
are bundled in this candidate directory.

The [independent source-transcription review](source-review.json), SHA-256
`67e568ccab62e18557f7e6770557aca83c6014875770271d16f1045e08be5cec`,
confirms the six selected values and preserves sample/temperature limitations.
It retains the distinction between source transcription and scientific review:
`independent_scientific_review` and `raw_data_reanalysis` are both false.
The earlier source families were not rereviewed.

An independent frozen-catalog composition check is retained outside this
repository at
`incremental-evidence/primary-table-growth-3-20261019/novelty/binary-oxide-novelty.json`,
SHA-256 `8d7fcad1094a89f051127e074a96b51e625842c9e13f62e0bb8ee307b06b5a77`
(21,251 bytes). It searched all 1103 identity, state and property records for
formulas, common aliases and composition descriptions, and compared all 24
accepted computed canonical compositions. No corresponding composition was
found. Existing elemental Ge, Ni and Sn are distinct from their oxides;
constituent mentions and mixed formulations are not standalone oxide identities.
The unchanged formal computed-review registry SHA-256 is
`a285523b2b2fdbf0d750ce6ac56e3abfb80d5c42056229a2352b016a787fd875`.
These are frozen-catalog checks, not claims of globally new materials or
scientific approval. The 62 other computed examples remain unadmitted.

## Existing source and rights scope

Source ID `swanson_tatge_1953_nbs_circ539v1` is reused exactly. Its canonical
JSON record hash, including a trailing newline, is
`af69ed341f5d81b6cd651b984ce489462f8ea798dfa95a98ace78a91b153bade`.
No source wording, date or rights decision changes.

The retained [NIST Technical Series rights notice](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications)
has 93,931 bytes and SHA-256
`7277db527945beefe164286cea84cb98c46d21c3194b007420961930df462e94`.
The existing employee-authored-work decision is reused only within its original
scope: domestic public-domain treatment and the notice's worldwide perpetual
royalty-free reuse permission where NIST asserts foreign rights. This batch
performs no new license review, claims no CC0 license and grants no rights.
Only selected NBS-authored facts, bibliographic metadata and original
qualifications are curated. Separately credited comparison results and source
assets are excluded.

Republished courtesy of the National Institute of Standards and Technology.

## Counting and reproducible preparation

If separately reviewed and integrated, core 1103 would become 1109, project
1127 would become 1133, core inorganic 43 would become 49 and project inorganic
55 would become 61. The accepted computed contribution remains 24. These are
projections, not claims that preparation admits or publishes records. Explicit
English fallback names fill all four locale slots; native-language review is
not claimed.

The [packet specification](packet-spec.json) shares the inorganic identity,
state and density contexts while keeping values, temperatures, sample provenance
and limitations explicit per row. The existing compiler is unchanged and no
per-record implementation is introduced.

```sh
python scripts/prepare_formulation_packet.py \
  --spec experimental/material-batches/nbs-binary-oxide-density-20261019/packet-spec.json \
  --baseline-dir /path/to/4db4ab5/materials_boundaries/data \
  --output experimental/material-batches/nbs-binary-oxide-density-20261019/prepared-packet.json
```

The baseline must preserve the pinned bytes; use a separate frozen baseline
checkout after integration. Identical replay must retain bytes and modification
time, and conflicting output cannot replace an existing artifact. Machine
readiness is not scientific approval, a new rights grant or formal admission.
Actual preparation results are appended below after execution.

The [actual preparation receipt](preparation-receipt.json) records one `Created`
invocation and one identical `Unchanged` replay, both exit zero, using the native
immutable writer. The 202,095-byte [prepared packet](prepared-packet.json) retained
SHA-256 `0511e82ef9279928629f8e05076ba5050988de4e18081593d3bb8cbd1bfaa28e`
and modification time `1792452100574450600` ns across both runs. The report has
six identities, six states, six properties, zero grades, zero sources and no
pending machine gates; formal admitted delta is zero. No product tests, source
requests, runtime writes, commits, pushes or emails were performed by this
candidate-preparation task.
