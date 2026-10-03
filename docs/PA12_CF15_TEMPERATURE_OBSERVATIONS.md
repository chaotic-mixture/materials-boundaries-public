# PA12 CF15 temperature-conditioned tensile observations

Version **0.22.0** admitted exactly six **catalog-only** source-reported 3D
ultimate-tensile-strength summaries. They describe one study's specific printed
material and protocol at six reported chamber conditions. They do not define
a continuous temperature law, universal strength bound, engineering allowable,
service-life model or matched-condition comparison with any other study.

## Scope before values

The material is **Fiberlogy PA12 CF15**, manufactured by Fiberlab S.A., and
horizontally printed by fused filament fabrication (FFF), with alternating
+45°/−45° raster. Declared **15 wt.% short carbon fibers** is a formulation,
not a measured compositional assay; **100% infill** is a slicer setting, not
measured zero porosity. No isotropy is established. Drying at 80 °C for 12 hours
does not establish the actual specimen moisture at testing.

The six temperature labels are **reported chamber test conditions**, each after
30 minutes of stabilization. Direct specimen temperature, sensor/location,
stability/tolerance and tensile heating rate are unknown. The source-reported
**1 mm/min** rate is displacement/crosshead motion, not a measured local strain
rate. Numerical RH and actual specimen moisture are unknown. These preparation,
geometry, raster, rate and chamber conditions restrict every selected result.

The quantity is **ultimate tensile strength as reported**. The inspected source
does not explicitly define nominal/engineering versus true stress, its stress-area
basis or a mathematical extraction criterion. The central statistic and exact
aggregation convention are also unknown. **Three tensile tests per temperature
condition** are reported; their independence and raw replicate values are not
verified. The ± component is **reported standard deviation (SD)** from the Table 3
header, not SEM, a confidence interval, an endpoint range, a hard bound or a full
uncertainty budget. No SD-to-CI conversion is justified by the count alone.

## Six selected source cells and exact units

| Record ID | Reported chamber condition (°C) | Central value ± SD (MPa, source strings) | Exact central value (Pa) | Exact SD (Pa) |
| --- | ---: | --- | ---: | ---: |
| `ciganas2026-pa12cf15-uts-23c` | 23 | 49.07 ± 0.88 | 49070000 | 880000 |
| `ciganas2026-pa12cf15-uts-40c` | 40 | 40.31 ± 0.72 | 40310000 | 720000 |
| `ciganas2026-pa12cf15-uts-60c` | 60 | 32.70 ± 1.18 | 32700000 | 1180000 |
| `ciganas2026-pa12cf15-uts-80c` | 80 | 26.60 ± 1.15 | 26600000 | 1150000 |
| `ciganas2026-pa12cf15-uts-100c` | 100 | 22.78 ± 0.97 | 22780000 | 970000 |
| `ciganas2026-pa12cf15-uts-120c` | 120 | 18.68 ± 0.91 | 18680000 | 910000 |

These are the six selected cells of [publisher HTML Table 3](https://www.mdpi.com/2073-4360/18/5/563#polymers-18-00563-t003),
row `Ultimate tensile strength, MPa ± SD`, in source-column order. They are six
condition-level summaries from **one study**, not six independent confirmations.

`reported_result` keeps numeric values, exact `value_string` and
`source_value_string`, and the SD's exact `value_string` in **MPa**. In particular,
`32.70` and `26.60` retain their trailing zeros. Source formatting is not a
verified measurement resolution or accuracy. `si_result` separately keeps exact
integer Pa values. Normalization is only **1 MPa = 1000000 Pa**, with zero offset,
checked through decimal strings rather than binary-float multiplication. It adds
no measurement precision and does not recalculate stress, use geometry/thickness,
reconstruct force/area, or create another observation. °C labels remain reported
conditions; no Kelvin values are derived in this release.

## Scientific identity and admission boundary

- Source/study: `ciganas2026polym18050563`
- Dataset: `ciganas-2026-pa12-cf15-fff-uts-temperature`
- Protocol: `ciganas2026-pa12-cf15-quasistatic-tension`
- Family: `ciganas_2026_pa12_cf15_fff_tensile_temperature_v1`
- Quantity: `ultimate_tensile_strength_as_reported_3d`
- Dimension / SI unit: `pressure` / `Pa`; material dimensionality: `3`
- Type: `experiment_derived_tensile_test_summary`
- Model status: `source_reported_tensile_summary_with_explicit_metadata_gaps`
- Evaluation support: `catalog_only`; record version: `1.0.0`

Observations schema **1.3.0** adds a closed branch for these six exact cells.
Temperature, source cell, central/SD strings and numbers, exact Pa results,
dataset/protocol, preparation, unknowns, evidence, revision metadata and rights
are bound together. Each record contains its own complete protocol metadata;
there is no new shared protocol catalog. This family is not a generic admission
route for arbitrary pressure-valued observations.

Selected subsets and renamed record IDs/display names remain valid when their
scientific payload is unchanged. The full packaged catalog additionally requires
all six admitted source-cell identities and rejects duplicate `(dataset_id, quantity, source_cell)`
aliases even when their record IDs differ. An alias is not an additional
observation or independent confirmation. In v0.23.0, completeness is a source-cell
set check, so a packaged permutation of the same six cells is valid. Generic
inspection still preserves packaged order; the separately selected temperature
plot restores source Table 3 order. No scientific payload requirement is relaxed.
New temperatures, material states,
protocols, stress definitions or scientific changes need reviewed admission.
This narrowly closed dataset does not remove existing supported-family
appendability elsewhere in the catalog. Runtime guards validate metadata without
executing scientific equations; the referenced source also has a closed
source-specific provenance/rights check.

## Preparation, specimen and protocol

[Section 2.1 and Table 2](https://www.mdpi.com/2073-4360/18/5/563#sec2dot1-polymers-18-00563)
support drying, 30-minute chamber stabilization, unmeasured specimen moisture
and the source-reported preparation: Creality K1 MAX, 265 °C nozzle,
100 °C heated bed, 0.2 mm layers, 0.6 mm nozzle, five contours, linear 100% infill,
60 mm/s inner and outer wall settings, and 100% cooling setting. Table 2's
raster label `45` is retained separately from the methods' alternating
+45°/−45° description. Printing chamber temperature, postprint storage,
annealing and finishing remain unknown. Lot, fiber distributions, crystallinity,
assayed fiber fraction and measured porosity are not established. No Table 1
manufacturer property or manufacturer density is used.

Reported dog-bone dimensions are 150 mm overall length, 80 mm gauge length,
3 mm thickness, 10 mm narrow width, 20 mm wide width and 110 mm grip separation.
Measured stress cross-section and dimensional tolerances remain unknown.
These nominal dimensions provide context and never reconstruct the reported
stress. The 80 mm gauge length must not be substituted for the 110 mm grip
separation used by the source's strain calculation.

[Section 2.2](https://www.mdpi.com/2073-4360/18/5/563#sec2dot2-polymers-18-00563)
describes three tensile tests per temperature condition, a Step-Lab UD08 with
integrated thermal chamber and quasi-static uniaxial tension along the specimen
axis. The source labels 1 mm/min as a load
rate; its unit identifies displacement rate. Engineering strain uses crosshead
displacement over 110 mm, including transition regions. That strain wording does
not establish engineering stress, measured local strain or a local strain rate;
1/110 min⁻¹ is not introduced as a measured rate.

The article cites ISO 527. Its reference is retained as **source-reported**:
neither compliance nor the cited standard URL was independently verified, and
that URL is not promoted to a verified clickable source. The DMA-specific
1 °C/min ramp is not transferred to these tensile records. Constant-humidity
wording does not supply RH or moisture measurements. Chamber gas/atmosphere and
ambient pressure stay unknown, including at 23 °C; no room-air or ambient-pressure
default is supplied.

## Source components and revision limits

Justas Ciganas, Tomas Kalinauskis and Urte Cigane (2026),
[“Thermo-Mechanical and Fatigue Behavior of 3D-Printed PA12 CF15 for Engineering Application”](https://doi.org/10.3390/polym18050563),
*Polymers* **18**(5), article 563. Publication date: **26 February 2026**.
The inspected representation is publisher-rendered HTML, its expanded Tables 2
and 3, methods, references, copyright block and [version notes](https://www.mdpi.com/2073-4360/18/5/563/notes),
accessed **3 October 2026**.

The version notes report HTML updated **3 September 2026 02:53 CEST** and PDF
uploaded **26 February 2026 11:36 CET**. The PDF was **not retrieved or inspected**;
PDF page/pagination and PDF-equivalence claims remain absent. The component ID
`publisher_html_updated_2026_09_03_inspected_2026_10_03` describes observed
revision/access metadata, not a source-file hash or an immutable publisher URL.

Evidence resolves to specific components:

| Component | Publisher HTML locator |
| --- | --- |
| Materials, drying, stabilization and unmeasured moisture | `sec2dot1-polymers-18-00563` |
| Preparation parameters | `polymers-18-00563-t002`; expanded `table_body_display_polymers-18-00563-t002` |
| Three-test count, 1 mm/min rate and 110 mm crosshead strain | `sec2dot2-polymers-18-00563` |
| Tensile-results context (not the count locator) | `sec3dot1-polymers-18-00563` |
| Selected value and SD | `polymers-18-00563-t003`; expanded `table_body_display_polymers-18-00563-t003`, exact row and temperature column |
| Article rights | `html-copyright` |
| Revision record | `/notes` |

**Source-version discrepancy:** a search-rendered cached Table 4 reported
3500-RPM y acceleration **14** and z frequency **337**, whereas directly inspected
current publisher HTML Table 4 showed **13** and **336**, consistent with the
article's corresponding equations. Table 4 is unselected and contributes no
observation here. This discrepancy prevents a blanket claim that all source
representations agree; no equivalence with the uninspected PDF is assumed.
The narrow verified agreement is the six selected **Table 3 UTS/SD cells** across
current HTML, visual inspection and a second independent transcription.

The primary lineage is the authors' tensile experiments, not a manufacturer
lookup, a fitted temperature model, or a finite-element assumed-input table.
No excluded dataset supplies these observations. Independent transcription
checks reading of the same source, not independent experiment, scientific review
or reproduction. Raw per-test tensile results, force/area data, SD recomputation
and stress-area recomputation were unavailable.

## Selection, presentation and rights

Only Table 3's six selected UTS/SD cells are admitted. Other Table 3 rows,
manufacturer Table 1, Table 4, stress–strain digitization, fatigue, DMA,
finite-element application results and application-safety claims are excluded.
No decline fit, significance claim, extrapolation, safety factor or design
allowable is inferred. Real temperature-conditioned observations remain separate
from the five synthetic temperature models and their seven branches.

```sh
python -m materials_boundaries catalog observations --source-id ciganas2026polym18050563 --text --lang en
python -m materials_boundaries catalog observations --observation-type experiment_derived_tensile_test_summary --json
python -m materials_boundaries observation inspect --source-id ciganas2026polym18050563 --output /tmp/pa12-cf15 --lang en
python -m materials_boundaries observation inspect --id ciganas2026-pa12cf15-uts-60c --output /tmp/pa12-cf15-60c --lang de
```

Inspection schema **1.1.0** supports packaged-catalog-ordered, text-only temperature facets
alongside the unchanged 2D facets. Essential material, chamber, protocol, stress,
statistic and SD caveats precede every property value, including a single-card
selection. The primary label is **Catalog display in reported units** (MPa);
Pa is separately labeled **exact SI unit re-expression**. In generic inspection there are no axes,
points, bars, uncertainty whiskers/endpoints, magnitude styling, connecting
curves, ranking, aggregation or cross-dimensional N/m comparison. Study/quantity
grouping is navigation only. See [inspection and CSV contracts](OBSERVATION_INSPECTION.md).

Version **0.23.0** adds the **separate explicit** `observation plot-temperature`
route for the complete dataset above. It shows six unconnected reported central
UTS values on numeric chamber-temperature/MPa axes with visible ±reported-SD
whiskers and an exact source table. This is descriptive transcription, not a
material law or statistical validation. Centers are not asserted means, no x
whiskers does not mean zero temperature uncertainty, and fixed display domains
are not material limits. Derived whisker endpoints are display arithmetic only;
exact Pa stays metadata. Generic inspection remains unchanged. See the
[closed admission, API, source/SD caveats and export contract](OBSERVATION_TEMPERATURE_PLOT.md)
and [v0.23.0 migration](MIGRATION_v0.23.0.md).

The article's own copyright block identifies **©2026 by the authors**, with
MDPI as licensee, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
No third-party credit line was shown for selected Table 3. Attribution is to
Ciganas, Kalinauskis and Cigane, the title and DOI above. Values were reorganized
as discrete observations, with reported numbers/SD preserved, exact SI unit
re-expression added and original curator notes. Table 1 is manufacturer-provided
and excluded; the article license is not extended to that third-party content.

No source PDF, figure, screenshot, HTML dump, raw measurement collection or long
article passage is bundled. [Project MIT licensing](../LICENSE) covers original
contributions and does not replace source rights or imply endorsement. Scientific
and native-language review remain outstanding. [Source ledger](SOURCES.md) ·
[Third-party notices](../THIRD_PARTY_NOTICES.md) · [Migration](MIGRATION_v0.22.0.md).
