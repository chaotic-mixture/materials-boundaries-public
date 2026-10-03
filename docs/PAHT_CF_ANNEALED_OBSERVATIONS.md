# Annealed PAHT-CF: source-specific catalog admission (v0.24.0)

Four discrete observations from Zach and Dudescu (2025) are **catalog-only**.
They are separate from the Ciganas PA12 CF15 study and cannot enter its closed
temperature plot. No cross-study ranking, shared fit, interpolation, extrapolation,
pooled estimate, normalized-retention comparison or engineering allowable is added.

## Evidence and exact selected cells

Theodor Florian Zach and Mircea Cristian Dudescu, *Effect of Annealing on High
Temperature Tensile Performance of 3D Printed Polyamide Carbon Fiber: A Comparative
Study*, Journal of Composites Science 9(11), 624 (2025),
[DOI 10.3390/jcs9110624](https://doi.org/10.3390/jcs9110624).
The numeric source is live publisher [Appendix A, Table A1](https://www.mdpi.com/2504-477X/9/11/624#jcs-09-00624-t0A1),
expanded container `table_body_display_jcs-09-00624-t0A1`.
Select Annealed = annealed and Orientation = ±45° in each temperature block.

Section 3.1 explicitly describes **medians with standard deviations**. The SD
column has **no separately printed unit**. Its catalog MPa unit is a contextual,
dimensional interpretation from the associated UTS column. SD-to-Pa conversion
is conditional on that interpretation. Exact scaling by 1,000,000 adds no
measurement precision. Median and SD remain separate fields and labels; a
median ± SD coverage interval is not constructed.

Five specimens per orientation × temperature × annealing combination are reported
(200 total). Raw values were not obtained. Replicate independence, exclusions and
sample-versus-population SD formula remain unknown. SD is not SEM, a confidence
interval, uncertainty of the median, an endpoint range, a hard bound or a full
uncertainty budget. No confidence interval is calculated from n = 5.

| Reported chamber condition | Median UTS string, MPa | Separate SD string | Exact median Pa | Conditional SD Pa |
|---|---:|---:|---:|---:|
| 25 °C | 58.91 | 3.44 | 58910000 | 3440000 |
| 50 °C | 40.87 | 4.59 | 40870000 | 4590000 |
| 100 °C | 29.64 | 0.72 | 29640000 | 720000 |
| 150 °C | 19.03 | 0.67 | 19030000 | 670000 |

Separate readers reproduced all eight selected numeric strings. This establishes
reading agreement, not experimental replication, measurement accuracy or external
scientific validation. The source's external scientific-review flag remains false.

## Conditions and unresolved details

- Commercial Bambu Lab PAHT-CF is described as PA12 with 15% mass short carbon
  fiber. This is a declared formulation, not an independent assay; it is not the
  same commercial formulation as Fiberlogy PA12 CF15
- Flat FFF printing on an enclosed Bambu Lab X1 Carbon, dehumidified AMS and
  ±45° infill are reported. Table 2 settings include a 0.4 mm nozzle, 0.2 mm
  layer, 0.16 mm top/bottom layer thickness, 100% infill, 100 mm/s printing speed,
  290 °C extrusion, 100 °C plate and 45 °C chamber. Infill is a setting, not
  measured zero porosity; quantitative porosity was not measured
- Predrying at 80 °C for 12 h and dehumidified storage are described. Selected
  specimens receive 80 °C annealing for 12 h and natural-convection cooling to
  room temperature in a vacuum-sealed dehumidified container. Section 2.2 says
  annealing was performed for all specimens, while Table A1 and Section 2.3
  distinguish groups. Only explicitly annealed rows are admitted; untreated
  history is not inferred from this ambiguous wording
- Actual moisture and test RH, batch, fiber distribution, density, crystallinity
  and measured porosity remain unestablished. Predrying does not prove dryness
- Instron 5967, force sensor 2580–10 KN/131510 and extensometer 2663-901 are
  reported. **10 mm/s displacement rate is retained as printed**. The control
  channel and measured local strain rate are unknown; no correction to mm/min
- Source references ISO 23529 Type 1, ISO 37 and ISO 527 are assertions, not
  independently verified compliance. Drawing labels 115, 25 ± 1, 33 ± 2 and
  2.5 ± 0.2 are nominal geometry context. The inspected caption does not
  independently state their unit. Actual dimensions, narrow width, stress area,
  extensometer gauge length and grip separation are unknown. The central
  straight-length label is not converted into gauge length
- Thirty minutes at each relevant Instron 3119-610 thermal-chamber condition is
  reported after room-temperature cooling. Direct specimen temperature,
  calibration, sensor location, stability/tolerance and heating rate are unknown
- Engineering versus true stress, nominal versus actual area basis and exact UTS
  extraction remain unestablished. The quantity is ultimate tensile strength
  **as reported**, without automatic scientific normalization

## Version and reuse boundary

The inspected component is
`publisher_html_updated_2026_09_02_inspected_2026_10_03`. Publisher
[version notes](https://www.mdpi.com/2504-477X/9/11/624/notes) report an HTML
update on 2 September 2026 03:21 CEST, original HTML on 11 November 2025 05:36
CET, updated PDF on 11 November 2025 05:35 CET and original PDF on 10 November
2025 15:16 CET. Neither PDF was inspected. There is no HTML/PDF-equivalence,
immutable-source URL or source-artifact-hash claim. Search-rendered prose differed
in its discussion arrangement; no selected-cell discrepancy was found.

The article copyright block explicitly links
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), © 2025 the authors,
MDPI as licensee. No selected Table A1 third-party credit line was found. Attribute
Zach and Dudescu, the article, year and DOI; four rows were selected/reorganized,
exact SI-prefix re-expression and original curator caveats added. Source rights
remain separate from MIT-licensed original project contributions; no author
endorsement is implied. Supplier Table 1, other source assets and raw data are
excluded. Table 2 separately credits references [28,31]; its third-party assets
are not redistributed or relicensed. The repository contains selected factual
numbers, short labels, references and original curation, not publisher HTML,
PDFs, screenshots, source figures or lengthy source passages.

The prior related [Polymers study](https://doi.org/10.3390/polym17131732) is not
counted as another independent confirmation: non-annealed data may overlap and
no raw-data overlap audit was possible. The new selection uses only annealed
rows. Source identity distinguishes studies, not statistical independence.

## Inspection and compatibility

```sh
python -m materials_boundaries catalog observations --source-id zach_dudescu2025jcs9110624 --text --lang en
python -m materials_boundaries observation inspect --source-id zach_dudescu2025jcs9110624 --output /tmp/paht-inspection --lang en
```

Repeat with `zh`, `ja` and `de`. HTML/SVG are source-ordered text inspections,
with warnings before values and no quantitative axes. JSON/CSV retain original
records, source snapshots, source-cell identity, unit evidence and unknowns.
When PAHT is selected, CSV uses separate median/SD columns; its legacy
`plus_minus` fields are null for PAHT. Old-only selections retain their earlier
CSV shape. Catalog schema 1.3.0 and inspection schema 1.1.0 receive a separate
closed family; saved bundles must be regenerated for the new engine release.
The existing six-cell Ciganas plot profile/schema and generated example bytes
remain unchanged. A quantity-only UTS filter now includes both studies; use an
explicit source ID for a single study.
