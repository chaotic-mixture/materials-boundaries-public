# Three source-qualified RCA sample densities from NBS

This review-only packet proposes three composition-level inorganic identities,
three source-scoped states and three numerical references against baseline
`799ca7a74fe1d0d92ac588b08350a39e2d0a9a79`. It adds no grades or sources.
The existing NBS source object and compiler are unchanged. Preparation does not
write runtime catalogs; `formal_admitted_delta` remains zero.

These are the final three adjacent material sections, 2.52-2.54, of NBS Circular
539 Volume I. They form a bounded group of RCA-supplied inorganic specimens
characterized at NBS. The contents page ends the material sections at 2.54;
references and the cumulative index follow. This batch stops at these three
records rather than expanding to other sections, sources or nominal variants.

## Exact selected source facts

All three properties are source-reported measured-lattice-derived
**crystallographic density**, with units `g/cm^3`. The established density-unit
scope in the Introduction, printed page 2 / one-based PDF page 6, is reused.
Each selected density sentence expressly references the NBS lattice or cell
determination. RCA supplied the samples; the selected values are not recast as
supplier bulk-density measurements.

| Source composition and phase | Density | Density temperature | Sample | Exact narrative locator |
| --- | --- | --- | --- | --- |
| ZnB2O4, body-centered cubic | 3.605 | 26 degrees C | RCA XII-17 | Section 2.52, printed page 83 / PDF page 87, upper left immediately above Table 53 |
| Mg2SiO4, orthorhombic forsterite | 3.213 | 26 degrees C | RCA X-9 | Section 2.53, sentence starts at printed page 83 / PDF page 87 bottom right; value and temperature at page 84 / PDF page 88 top left |
| MgWO4, monoclinic | 6.897 | 26 degrees C | RCA No. 4 | Section 2.54, printed page 84 / PDF page 88, bottom right below the unit-cell comparison |

The selected density values are in narrative statements, not density columns
of Tables 53-55. Preserve their reported precision without recalculation,
atomic-weight substitution or uncertainty propagation. A reported value is not
automatically a mean. Independent specimen/repeat counts, density-specific
uncertainty, pressure, porosity, moisture content and conditioning duration are
not established. Counts of diffraction lines or molecules per cell are not
sample n; a general lattice-error statement is not a density error bar.

- **ZnB2O4:** section 2.52, printed page 83 / PDF page 87, upper left. The
  source identifies RCA phosphor preparation XII-17 and describes it as high
  purity. Its body-centered cubic cell is obtained from the NBS powder pattern;
  the last five diffraction lines are averaged for the lattice constant. Keep
  the printed formula ZnB2O4 exactly. No different zinc-borate composition,
  hydrate, numerical purity, certified grade, preparation temperature or
  treatment duration is inferred. Phosphor preparation describes research
  context without establishing a complete preparation procedure.
- **Mg2SiO4:** section 2.53, printed page 83 / PDF page 87, lower-left heading
  and right column. RCA sample X-9 was prepared for a phosphor project by a
  solid-state reaction at **1500 degrees C**; duration and complete synthesis
  recipe are unknown. The density separately uses **26 degrees C**. High
  purity remains qualitative. The source only presumes the forsterite space
  group by comparison with olivine; no independent space-group validation is
  claimed. Historical natural Vesuvius forsterite and iron-bearing olivine are
  comparison specimens, not the selected RCA material or evidence of iron in
  it. The NBS cell dimensions use spacings of planes parallel to one or more
  axes. The finely powdered description supplies no numerical particle size.
- **MgWO4:** section 2.54, printed page 84 / PDF page 88, right column. RCA
  material marked No. 4 was prepared at **1000 degrees C**; detailed method,
  duration and complete recipe are unknown. Its density separately uses
  **26 degrees C**. Exceptionally high purity is a qualitative source phrase,
  not a numerical assay or certified grade. Historical literature patterns
  and structure claims are not promoted to new NBS determinations. No numerical
  particle size is inferred from the finely powdered description.

## Primary-source and independent transcription evidence

Howard E. Swanson and Eleanor Tatge (1953), *Standard X-ray Diffraction Powder
Patterns, Volume I*, NBS Circular 539.
[DOI 10.6028/NBS.CIRC.539v1](https://doi.org/10.6028/NBS.CIRC.539v1),
[official PDF](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf).
The retained complete PDF has 104 pages, 6,422,795 bytes and SHA-256
`003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c`.
The task-workspace evidence path is
`incremental-evidence/material-growth-20261014/sources/nbs-circular539-v1-complete.pdf`.
Author-side page images remain outside this repository under
`incremental-evidence/primary-table-growth-2-20261019/source-inspection/`.
No PDF, page image, full source table or raw structural asset is bundled.

The [independent source-transcription review](source-review.json), SHA-256
`1d3c5cc27e13bf7603276dccff71102442b51b78942ddaa3c09a67fd955a2adb`,
visually confirms all three formulas, densities and temperatures on printed
pages 83-84 / PDF pages 87-88. It preserves sample and preparation limitations
and identifies the NBS calculation basis. It does not perform catalog-wide
deduplication, repeat the previous salt review or claim a newly reviewed license.
Both `independent_scientific_review` and `raw_data_reanalysis` remain false.
There was no experimental replication or independent structure validation.

## Frozen source and rights scope

Source ID `swanson_tatge_1953_nbs_circ539v1` is reused as the exact existing
registry object. Its canonical JSON hash, including a trailing newline, is
`af69ed341f5d81b6cd651b984ce489462f8ea798dfa95a98ace78a91b153bade`.
No source wording, date or rights decision changes.

The established [NIST Technical Series rights notice](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications)
is retained as 93,931 bytes, SHA-256
`7277db527945beefe164286cea84cb98c46d21c3194b007420961930df462e94`.
The existing employee-authored-work decision is reused within its existing
scope: domestic public-domain treatment and the notice's worldwide perpetual
royalty-free reuse permission where NIST asserts foreign rights. This batch
does not newly review or expand that decision, declare CC0, or grant rights.
Only selected NBS-authored factual results, bibliographic information and
original source qualifications are curated. Third-party pattern, cell,
structure and optical comparison results are excluded.

Republished courtesy of the National Institute of Standards and Technology.

## Composition reconciliation and projected counts

The pinned baseline contains 1100 core identities, including 40 inorganic
identities, plus 24 accepted computed composition buckets: 1124 project
identities. Its 62 other computed examples remain unadmitted. The author checked
core names, aliases and source/state composition descriptions for ZnB2O4,
Mg2SiO4, MgWO4 and their naming variants. None has a standalone admitted identity.
The accepted computed registry remains SHA-256
`a285523b2b2fdbf0d750ce6ac56e3abfb80d5c42056229a2352b016a787fd875`;
none of its 24 reduced-element compositions matches these three.

Existing MgO and SiO2 identities and constituent mentions are not Mg2SiO4;
other zinc-borate compositions or hydrates are not silently equated with
ZnB2O4. Historical natural forsterite and iron-bearing olivine are excluded
from the selected sample evidence. Sample numbers, suppliers, phases,
processing and temperatures do not add identity credit. All previous NBS salts
and oxides are outside this increment.

Separate review and integration would take core 1100 to 1103, project 1124 to
1127, core inorganic 40 to 43 and project inorganic 52 to 55. These are
projections, not claims that preparation has admitted or published records.
The packet supplies explicit English fallbacks in all four required locale
name slots; no native-language review is claimed.

## Reproducible preparation

The [packet specification](packet-spec.json) uses one shared inorganic identity
context and the existing shared state/density contracts, with explicit per-row
scientific fields. There is no per-record code, inferred source approval or
compiler change.

```sh
python scripts/prepare_formulation_packet.py \
  --spec experimental/material-batches/nbs-rca-density-20261019/packet-spec.json \
  --baseline-dir /path/to/799ca7a/materials_boundaries/data \
  --output experimental/material-batches/nbs-rca-density-20261019/prepared-packet.json
```

The baseline must preserve the pinned bytes. After integration, use a separate
frozen baseline checkout for replay. Identical output must preserve bytes and
modification time; conflicting output cannot replace an existing artifact.
Machine readiness is not scientific approval, a rights grant or formal admission.
Actual first-and-repeat results are recorded below after execution.

The [actual preparation receipt](preparation-receipt.json) records one `Created`
invocation and one identical `Unchanged` replay, both exit zero, using the native
immutable writer. The 104,737-byte [prepared packet](prepared-packet.json) kept
SHA-256 `6d906eec144e3908941f7c6f3c91646d4d905a7134fdc5086a95c4e59f1ca41c`
and modification time `1792448625562478600` ns across both invocations. The report
records three identities, three states, three properties, zero grades, zero
sources and no pending machine gates; formal admitted delta is zero. No product
tests, source requests, runtime writes, commits, pushes or emails were performed
by this candidate-preparation task.
