# PA12 CF15: a closed descriptive temperature-observation plot

Version **0.23.0** adds a separate, explicitly selected quantitative display of
**six source-reported condition summaries from one study and one shared
source-reported protocol**. It transcribes the selected Table 3 cells; it does
not independently validate the experiment or statistical summary. All twelve
observations remain `catalog_only`, and exactly eight composite calculation
rules remain executable. No scientific catalog record changes.

The existing `observation inspect` route stays text-only under schema **1.1.0**:
`purpose=inspection_only`, `quantitative_axes_allowed=false`, and
`uncertainty_endpoints_calculated=false`. The new route has its own closed
**observation-temperature-plot 1.0.0** schema and validation. It cannot turn an
inspection filter, arbitrary pressure record, shared unit, equal nulls or common
JSON shape into a compatible plot. The six older 2D records are unchanged.

## Scientific scope before the values

- One study of horizontally FFF-printed **Fiberlogy PA12 CF15**, with alternating
  **+45°/−45° raster** and a specific preparation, nominal geometry and
  **1 mm/min crosshead-rate** protocol. The latter is not local strain rate
- X is the **reported chamber test condition** after **30 minutes of
  stabilization**. Direct specimen temperature and temperature uncertainty are
  unreported. No horizontal whisker means **unknown uncertainty, not zero**;
  dot width does not represent temperature precision
- Dots are **source-reported central UTS values**. The central statistic,
  aggregation, stress convention and stress-area basis are unknown; the dots
  must not be relabeled means
- Visible vertical whiskers reproduce **central value ± source-reported standard
  deviation (SD)**. The source reports **three tensile tests per condition**;
  raw replicates and their independence are unverified. These are not six
  independently replicated studies. SD is not SEM, a confidence interval,
  observed min–max, measurement accuracy, a hard bound, coverage statement or
  complete uncertainty budget. The sample/population SD formula and averaging
  convention are unreported; no distribution or SD recomputation is assumed
- Drying at **80 °C for 12 h** does not establish measured moisture. Humidity and
  actual moisture are unknown. Declared **15 wt.%** fibers and **100% infill**
  do not establish assayed composition or zero porosity. No isotropy is inferred
- No interpolation, fit, extrapolation, trendline, ranking, normalization,
  significance test, cross-study comparison, material prediction, design
  allowable, safety threshold or universal material claim is added.
  Transcription/software checks are not independent scientific validation

Each standalone SVG and HTML places all six essential scope warnings before the
first quantitative plot/table property value and keeps a glyph legend next to
the plot. Tooltips, embedded JSON and expandable details do not replace those
warnings. The exact source table is available without scripts or a mouse.

The compact standalone SVG retains the plot, all six exact MPa/SD cells with
record IDs and concise Table 3 column identification, and a shared, readable
interpretation/protocol summary. That summary covers preparation, print settings,
nominal geometry, crosshead/strain-reference distinctions and the relevant
unknowns. DOI, exact row/container/expanded-table locators, inspected revision,
PDF noninspection, Table 4 caveat and rights/attribution remain visible. Every
essential warning stays in the SVG body; a smaller document must not depend on
opening another file to interpret the six dots and SD whiskers responsibly.

Complete curated metadata dictionaries, repeated per-record provenance, metadata
digests and the six exact SI value/SD pairs remain losslessly available in the
canonical JSON/CSV and inert expandable HTML details. They are not repeated as
full dictionary dumps in the SVG body. This is a presentation-only reduction:
scientific records, canonical bundle/schema, current-data guards, original source
strings and all audit-export metadata are unchanged. Exact SI remains metadata,
with 1 MPa = 1000000 Pa and no added precision, never an additional plotted series.

## Explicit CLI selection and artifacts

```sh
python -m materials_boundaries observation plot-temperature \
  --dataset-id ciganas-2026-pa12-cf15-fff-uts-temperature \
  --output /tmp/pa12-temperature-plot --lang en
python -m materials_boundaries observation plot-temperature --help --lang de
```

Both `--dataset-id` and `--output` are required. The displayed dataset is the
**only accepted dataset ID**. All six cells are always selected; there is no
implicit all-observations plot, arbitrary file/record input, subset selector,
`--group-by`, axis-limit option or SD-hiding option. Existing `inspect --id`
subsets remain independent. CLI `--lang en|zh|ja|de` defaults to `en`; it may occur
before or after commands, with the final occurrence taking precedence, including
help. Canonical command names, selectors, IDs, values and units do not translate.

Five outputs use a distinct prefix, avoiding the inspection filenames:

- `observation-temperature-plot.json`: deterministic language-independent bundle
- `observation-temperature-plot.csv`: deterministic one-observation-per-row export
- `observation-temperature-plot.en.svg`: standalone 1100 px wide view
- `observation-temperature-plot.narrow.en.svg`: standalone 380 px stacked view
- `observation-temperature-plot.en.html`: responsive, script-free offline page

Locale changes only SVG/HTML names and authored labels/warnings. The HTML uses
no external assets, fonts, scripts or automatic network loads; ordinary safe
source links are followed only when the reader chooses. Source titles,
bibliographic text, exact strings, IDs, decimal points and units stay canonical.

## Reproducible checked-in examples

From the repository root, regenerate only the new example directory:

```sh
python scripts/generate_observation_temperature_demo.py
```

The script fixes the approved dataset explicitly and preflights all four locales
before writing **14 files** to `examples/observation-temperature-plot`: shared
JSON/CSV plus wide SVG, narrow SVG and HTML per locale. `--output DIR` selects
another directory and `--lang en|zh|ja|de|all` defaults to `all`. This does not
regenerate historical examples. The output consists of original presentation
artifacts, not source-media copies. Repeated generation must produce identical
bytes; viewing/browser QA remains a separate check.

[English SVG](../examples/observation-temperature-plot/observation-temperature-plot.en.svg) ·
[中文 SVG](../examples/observation-temperature-plot/observation-temperature-plot.zh.svg) ·
[日本語 SVG](../examples/observation-temperature-plot/observation-temperature-plot.ja.svg) ·
[Deutsch SVG](../examples/observation-temperature-plot/observation-temperature-plot.de.svg).

## Numeric axes and exact source table

X is linear in reported chamber °C, preserving the **17 °C** first gap and
**20 °C** later gaps. Ticks are exactly **23, 40, 60, 80, 100, 120 °C**. The fixed
**15–125 °C** display domain provides glyph padding; it adds neither observed
conditions nor a validated temperature range. Only six conditions spanning
**23–120 °C** were selected. Y is linear source-reported UTS in **MPa**, with a
fixed **0–55 MPa** display domain and ticks **0, 10, 20, 30, 40, 50**. Zero is a
visual baseline, not an experimentally established bound, and display extrema
are not material limits.

Six equally styled dots have constant radius, color and opacity, with no jitter,
magnitude styling, good/bad color classification, connecting path, fill, second
axis, logarithmic transform or cross-dimensional N/m display. Whisker caps mark
arithmetic glyph endpoints, not measured extremes. Wide and narrow views use the
same scales. Source MPa values are plotted once; SI Pa stays separate metadata.

| Chamber condition (°C) | Exact source cell (MPa) | Reported tests per condition | Derived lower glyph endpoint (MPa) | Derived upper glyph endpoint (MPa) |
| ---: | --- | ---: | ---: | ---: |
| 23 | 49.07 ± 0.88 | 3 | 48.19 | 49.95 |
| 40 | 40.31 ± 0.72 | 3 | 39.59 | 41.03 |
| 60 | 32.70 ± 1.18 | 3 | 31.52 | 33.88 |
| 80 | 26.60 ± 1.15 | 3 | 25.45 | 27.75 |
| 100 | 22.78 ± 0.97 | 3 | 21.81 | 23.75 |
| 120 | 18.68 ± 0.91 | 3 | 17.77 | 19.59 |

All ± components in this table are source-reported **SD**. Endpoints are computed
from decimal source strings in an isolated local decimal context, identified by
`decimal_central_plus_minus_reported_sd_for_glyph_only`, and retained as
**derived glyph endpoints**, never new source values or observations. This
positioning arithmetic is not a ninth material-model rule. The rendered exact
source table retains trailing zeros, scoped counts, SD type and record/source-cell
identity. Source precision is not verified measurement resolution. Exact
**1 MPa = 1000000 Pa** re-expression adds no measurement precision and performs
no geometry, thickness or force/area operation. No Kelvin axis is introduced.

## Closed group compatibility and current-data validation

Admission binds these source-defined identities and their complete payloads:

- Admission profile: `ciganas-pa12-cf15-table3-uts-temperature-v1`, version `1.0.0`
- Source/study: `ciganas2026polym18050563`
- Dataset: `ciganas-2026-pa12-cf15-fff-uts-temperature`
- Protocol: `ciganas2026-pa12-cf15-quasistatic-tension`
- Family: `ciganas_2026_pa12_cf15_fff_tensile_temperature_v1`
- Quantity: `ultimate_tensile_strength_as_reported_3d`; dimensionality **3**,
  dimension `pressure`, reported unit **MPa**, exact SI unit **Pa**
- Artifact: `publisher_html_updated_2026_09_03_inspected_2026_10_03`
- Table 3, row `Ultimate tensile strength, MPa ± SD`, the six exact temperature
  columns in source order

The source-cell identity, rather than a presentation record ID/name, determines
admission. Unchanged-payload ID/name renames remain supported. A complete approved
set is restored to Table 3 column order even if packaged records are reordered;
changing the canonical bundle's glyph order is rejected. Missing cells, duplicate
aliases, a seventh cell, unreviewed temperatures, new groups, altered values,
statistics, process, unknowns or source/rights metadata fail closed. Full catalog
and actual referenced-source validation applies; an altered source is never
silently substituted with a canonical object.

This is **one source-reported shared-protocol group**. It does not establish
identical actual conditioning, replicate independence or material invariance.
Unknowns are not wildcards. Future groups require explicit schema/runtime/tests/
documentation review of material/process, geometry/orientation, loading/rate,
quantity/stress/area/extraction, temperature, moisture/conditioning, statistics,
counts, uncertainty and provenance. No automatic overlay or shared scale follows
from adding records; a reviewed group may need separate caveated facets.

Every public serializer, renderer and export validates by rebuilding from the
explicit selection, **current packaged catalogs and current fixed policy**, then
comparing complete canonical JSON. Recomputing a forged snapshot digest is not
validation. Extra fields, stale versions, changed selection/group, records,
source objects, warnings, domains, ticks, policy flags, derived endpoints and
non-JSON/nonfinite/boolean numeric values are rejected. Bundles are not mutated.
Metadata SHA-256 digests identify bundled metadata, **not publisher artifact
bytes**. Optional development JSON Schema checks supplement the dependency-free
runtime guard; they do not establish scientific validity.

## Python API

```python
from materials_boundaries.observation_temperature_plot import (
    build_observation_temperature_plot,
    validate_observation_temperature_plot,
    temperature_observation_plot_json,
    temperature_observation_plot_csv,
    render_observation_temperature_svg,
    render_observation_temperature_html,
    export_observation_temperature_plot,
)

dataset_id = "ciganas-2026-pa12-cf15-fff-uts-temperature"
bundle = build_observation_temperature_plot(dataset_id=dataset_id)
validate_observation_temperature_plot(bundle)
json_text = temperature_observation_plot_json(bundle)
csv_text = temperature_observation_plot_csv(bundle)
svg = render_observation_temperature_svg(bundle, lang="en", width=1100)
html = render_observation_temperature_html(bundle, lang="en")
paths = export_observation_temperature_plot(
    "/tmp/pa12-temperature-plot", dataset_id=dataset_id, lang="en")
```

Dataset selection is required in Python too. Renderers accept only a current
canonical bundle. SVG `width` is a strictly typed integer from **320 to 1600**;
booleans are not widths. Unsupported dataset/language/width, stale bundles and
scientific changes are rejected. The exporter builds and validates all artifacts
in memory before creating output targets, so invalid requests create or change
no output files. This preflight guarantee **does not promise all-file atomic
rollback** for a later filesystem, permission or disk failure during valid writes.

## JSON and CSV use

Canonical JSON uses sorted keys, UTF-8, no generated timestamps or random IDs,
and a final newline. JSON/CSV bytes are locale-independent. CSV has fixed column
order, normal CSV quoting and `\n` rows, one complete observation per row. Identity,
classification, protocol and caveats precede numeric columns. Exact source
strings, reported SD/evidence, three-test scope, null independence, chamber
basis/unknown uncertainty, source-cell/version/rights, exact SI values, endpoint
derivation, complete snapshots, selection/policy JSON and metadata digests remain
auditable. Scalar unknowns are the literal **`null`**, not blank, zero or false;
JSON snapshots preserve types.

**Import source, ID and JSON columns as text in spreadsheet software.** A source
or identity string beginning with `=`, `+`, `-` or `@` remains the original string;
CSV quoting alone may not stop formula interpretation. The exporter does not
silently prefix, strip or rewrite canonical scientific text for spreadsheet
import assumptions. Use a controlled text-import workflow rather than executing
formula-like source text. This is a descriptive audit export, not raw-replicate
data or a ready-to-aggregate dataset.

### CSV columns in fixed order

1. `classification`
2. `evaluation_support`
3. `dataset_id`
4. `profile_id`
5. `profile_version`
6. `study_id`
7. `protocol_id`
8. `method_family`
9. `quantity`
10. `quantity_dimension`
11. `record_id`
12. `record_version`
13. `source_cell_json`
14. `required_warning_codes_json`
15. `essential_caveats`
16. `temperature_basis`
17. `temperature_uncertainty`
18. `central_statistic_explicitly_named`
19. `aggregation_convention`
20. `stress_measure`
21. `stress_area_basis`
22. `uncertainty_type`
23. `uncertainty_interpretation`
24. `uncertainty_evidence_json`
25. `sample_count_scope`
26. `replicate_independence`
27. `source_artifact`
28. `source_inspection_json`
29. `rights_json`
30. `temperature_value_string`
31. `temperature_unit`
32. `source_value_string`
33. `central_value_string`
34. `sd_value_string`
35. `unit`
36. `sample_count`
37. `si_central_value`
38. `si_sd_value`
39. `si_unit`
40. `normalization_json`
41. `derived_glyph_lower_string`
42. `derived_glyph_upper_string`
43. `endpoint_derivation`
44. `conditions_json`
45. `method_json`
46. `sample_metadata_json`
47. `evidence_json`
48. `engine_version`
49. `plot_schema_version`
50. `observation_schema_version`
51. `source_schema_version`
52. `scalar_missing_convention`
53. `selection_json`
54. `group_json`
55. `presentation_policy_json`
56. `policy_digest_sha256`
57. `record_snapshot_sha256`
58. `source_snapshot_digests_json`
59. `record_snapshot_json`
60. `source_snapshots_json`

Consumers should select columns by name even though this version fixes their
order. Numeric-looking source strings remain strings in the source/snapshot
contract; CSV itself does not retain a column type system.

## Full protocol, provenance, rights and review limits

The [scientific observation guide](PA12_CF15_TEMPERATURE_OBSERVATIONS.md) retains
all print settings and nominal geometry: 150 mm overall length, **80 mm gauge
length**, 3 mm thickness, 10/20 mm narrow/wide widths and **110 mm grip separation**.
The source uses crosshead displacement over 110 mm for strain; substituting the
80 mm gauge or inferring a measured local strain rate is unsupported. Geometry
is not used to reconstruct stress. ISO 527 is cited by the source, but compliance
is unverified. Chamber atmosphere/pressure remain unknown. The DMA heating rate
is not transferred into the tensile protocol.

Attribution: **Justas Ciganas, Tomas Kalinauskis and Urte Cigane (2026)**,
[“Thermo-Mechanical and Fatigue Behavior of 3D-Printed PA12 CF15 for Engineering Application”](https://doi.org/10.3390/polym18050563),
*Polymers* **18**(5), 563,
[Table 3](https://www.mdpi.com/2073-4360/18/5/563#polymers-18-00563-t003),
expanded-table locator `table_body_display_polymers-18-00563-t003`, exact UTS/SD
row and temperature columns. Inspected publisher HTML reports an update on
**3 September 2026 02:53 CEST** and was accessed **3 October 2026**. The PDF was
not inspected; no PDF equivalence is claimed. The cached/live discrepancy belongs
to **unselected Table 4**. Only the six selected Table 3 cells have matching
HTML, visual and second-transcription evidence, not independent experimental
replication or source-wide consistency.

The article is **©2026 by the authors**, MDPI licensee, under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). No third-party credit
line was shown for the selected Table 3. Adaptation: source numbers/SD strings
are preserved, reorganized and plotted as discrete source summaries, exact SI
units are re-expressed, glyph endpoints use stated arithmetic, and curator notes
are original. Publisher/author endorsement is not implied. Manufacturer Table 1,
other result rows, source PDFs, figures, screenshots, HTML dumps, long passages,
raw measurements and excluded datasets are not redistributed. Project MIT
licensing does not broaden source rights; [third-party notices](../THIRD_PARTY_NOTICES.md)
and the [source ledger](SOURCES.md) continue to apply.

Labels in en/zh/ja/de are **machine-assisted working translations**, including
the English explanations, with no independent scientific/native-language review.
Static SVG structure/pixel checks and HTML structure checks are distinct from
browser interaction/layout QA. **Browser QA is unverified**; do not infer it from
software tests or static previews. Record actual release-test outcomes separately.
Neither this guide nor schema validity claims independent scientific validation,
legal clearance, a published tag or passing remote CI.
