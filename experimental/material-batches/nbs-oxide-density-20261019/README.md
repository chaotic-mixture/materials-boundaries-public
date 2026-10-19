# Six source-qualified NBS oxide density candidates

This review-only packet proposes six composition-level inorganic identities,
six source-scoped states and six numerical density references against baseline
`c90188dcd5ac3a19863be0b49419722571b17eff`. It adds no grades or source records.
The existing NBS source object is reused unchanged. Runtime catalogs are not
changed by preparing this packet, and `formal_admitted_delta` remains zero.

All six values are **source-reported measured-lattice-derived crystallographic
density**, not direct bulk or powder-packing density measurements, DFT
predictions, newly recalculated densities, engineering allowables or universal
material values. A reported value is not automatically a mean. Density-specific
uncertainty, pressure, independent specimen/repeat count, porosity, moisture
content and conditioning duration remain unknown.

## Selected original NBS results

Units are grams per cubic centimeter (`g/cm^3`), explicitly defined in the
Introduction, printed page 2 / one-based PDF page 6. These are the exact reported
numerical strings, including the final zero in `4.250`. Each temperature is
stated in the density sentence; preparation temperatures are separate.

| Composition and selected phase | Density | Density temperature | Section | Density locator: printed / one-based PDF page |
| --- | --- | --- | --- | --- |
| BeO, hexagonal | 3.008 | 26 degrees C | 2.17 | 37 / 41, left column below unit-cell table |
| MgO, face-centered cubic | 3.581 | 25 degrees C | 2.18 | 39 / 43, upper left below unit-cell table |
| CaO, face-centered cubic | 3.345 | 27 degrees C | 2.21 | 44 / 48, lower left below unit-cell table |
| TiO2, tetragonal rutile | 4.250 | 26 degrees C | 2.22 | 46 / 50, upper right |
| CuO, monoclinic tenorite | 6.51 | 26 degrees C | 2.25 | 49 / 53, lower right below unit-cell table |
| CeO2, face-centered cubic fluorite type | 7.215 | 26 degrees C | 2.30 | 57 / 61, upper left below unit-cell table |

Sample identity and preparation are located separately:

- **BeO:** printed page 36 / PDF page 40, upper left. Brush Beryllium Company
  No. 1743-1747, described as fluorescent grade, prepared at a furnace temperature
  of 1150 degrees C; duration unknown. NBS reports about 0.03 percent Al, less
  than 0.01 percent each Ca, Fe, Mg and Si, and traces of Cu, Pb and Sn. The grade
  wording is preserved as a source description without creating a certified or
  separately normalized grade record.
- **MgO:** printed page 37 / PDF page 41, right column. Radio Corporation of
  America sample for phosphor research, crystallized in a graphite crucible at
  1800 degrees C for three hours. Retain the reported impurity ranges despite
  the source's qualitative word "pure". Table 19 records a 26-degree powder
  pattern; the selected density explicitly uses 25 degrees C. The Introduction
  explains lattice-temperature normalization, so these temperatures are not
  silently made equal.
- **CaO:** printed page 43 / PDF page 47, upper right. No. 121647 belongs to
  J. T. Baker's calcium-carbonate precursor, calcined in platinum at 925 degrees
  C for one hour. Petrolatum mounting minimized hydration; it does not establish
  an anhydrous specimen or a mounting-mixture density. Preserve the grouped
  impurity entries and separate NBS/supplier analyses, without allocating grouped
  values to individual constituents or inventing a percentage basis.
- **TiO2 rutile:** printed page 44 / PDF page 48, lower right, and page 45 /
  PDF page 49, upper left. National Lead Company Sample MP 559, initially chiefly
  anatase, heated at 1000 degrees C for two hours and cooled slowly to obtain
  rutile. The NBS statement that no impurity exceeds 0.001 percent is not a
  total-purity guarantee; numerical cooling rate is unknown.
- **CuO:** printed page 49 / PDF page 53, lower left. Johnson, Matthey sample
  No. 3257; NBS spectrography reports faint Fe and Mg traces. Numeric purity,
  detection threshold and sample-specific processing are not established.
- **CeO2:** printed page 56 / PDF page 60, upper left. NBS spectrographic
  laboratory label No. 41-9100, explicitly of unknown origin; approximately
  99.99 percent pure with Pr and Cu traces. Preserve "approximately" and the
  unknown percentage basis. The immediate source is not an inferred manufacturer.

The source's general lattice/spacing error is not a density uncertainty. Unit-cell
contents and averaged diffraction-line counts are not independent sample counts.
No impurity-free or certified-grade claims are made for any row.

## Source, retained bytes and rights scope

Howard E. Swanson and Eleanor Tatge (1953), *Standard X-ray Diffraction Powder
Patterns, Volume I*, National Bureau of Standards Circular 539.
[DOI 10.6028/NBS.CIRC.539v1](https://doi.org/10.6028/NBS.CIRC.539v1) and
[official PDF](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf).
The retained complete PDF has 104 pages, 6,422,795 bytes and SHA-256
`003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c`.
Selected page images and extracted text were inspected locally on 2026-10-19;
this is not a fresh retrieval or a new audit of the entire volume.

Source ID `swanson_tatge_1953_nbs_circ539v1` is reused as the exact existing
registry object. Its canonical JSON record hash, with a trailing newline, is
`af69ed341f5d81b6cd651b984ce489462f8ea798dfa95a98ace78a91b153bade`.

The retained [NIST Technical Series rights notice](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications)
has 93,931 bytes and SHA-256
`7277db527945beefe164286cea84cb98c46d21c3194b007420961930df462e94`.
Its employee-authored-work scope supports the existing scoped reuse basis for
the selected NBS-authored facts. It is not a blanket CC0 license or permission
for separately credited third-party content. Only selected factual values,
bibliographic information and original qualifications are curated. Third-party
comparison patterns, lattice/optical values, complete tables, source PDF/page
images and raw structural assets are excluded.

Republished courtesy of the National Institute of Standards and Technology.

## Identity reconciliation and exclusions

The pinned baseline contains 1084 core identities, including 26 inorganic
identities, plus exactly 24 accepted computed composition buckets (1108 project
identities). The separate 62 computed examples remain unadmitted. Core names,
aliases and source/state composition descriptions were checked alongside the
reduced elemental compositions in the formal computed review registry.

All six selected binary oxide compositions lack a standalone identity in this
baseline. MgO/CaO impurity mentions in alumina do not constitute separately
admitted MgO/CaO identities. The computed ternary compositions, such as
`BeCa2O4`, are distinct from the selected binary oxides. SiO2 already occurs in
the catalog and is excluded; existing NBS salt and elemental identities are
also excluded. Sample numbers, suppliers, phases and temperatures do not create
additional identity credit. No source-qualified representative implies that
all samples of its composition share its reported density.

TiO2 anatase is deliberately excluded. Its source-reported density is 3.899 at
26-27 degrees C (section 2.23, printed page 47 / PDF page 51), and the source
notes two weak rutile lines omitted from its powder-pattern table. Any later
curation would be evidence for another state under the same TiO2 identity, not
a seventh material identity or a pure-anatase bulk-density claim.

If separately reviewed and integrated, the six identities would take core
1084 to 1090 and project 1108 to 1114, with core inorganic 26 to 32. These are
projected counts, not a claim of current admission or publication. English names
are explicit fallbacks in all four locale slots; no native-language review is
claimed. `independent_scientific_review` and `raw_data_reanalysis` remain false.

## Reproducible candidate preparation

The authored [packet-spec.json](packet-spec.json) uses named shared contexts for
the existing inorganic crystallographic-density contract, with explicit per-row
values, temperatures, provenance and specimen limitations. Contexts do not infer
scientific fields or upgrade review/rights status. The shared compiler creates
one review-only artifact:

```sh
python scripts/prepare_formulation_packet.py \
  --spec experimental/material-batches/nbs-oxide-density-20261019/packet-spec.json \
  --baseline-dir /path/to/c90188d/materials_boundaries/data \
  --output experimental/material-batches/nbs-oxide-density-20261019/prepared-packet.json
```

The baseline must retain the pinned bytes; use a separate frozen checkout after
runtime integration. Exact repeats preserve artifact bytes and modification
time; conflicting outputs are rejected. A machine-ready result is not scientific
approval or formal admission. Execution results and checks belong in the actual
handoff evidence rather than being inferred from this command example.

The retained [preparation receipt](preparation-receipt.json) records the actual
first `Created` result and one identical `Unchanged` replay, both exit zero.
The 162,627-byte [prepared packet](prepared-packet.json) retained SHA-256
`21aaed2df59b0ab9301d1573aabd6fd8bd87354c01fdf11323cdee62b600aab3`
and modification time across both runs. Its report has six identities, six
states, six properties, zero grades, zero sources and no pending machine gates;
formal admitted delta remains zero. No product tests or network requests were
performed by this candidate-preparation task. The separate
[source transcription review](source-review.json) preserves the independent
six-row check and its scientific-review limitations.
