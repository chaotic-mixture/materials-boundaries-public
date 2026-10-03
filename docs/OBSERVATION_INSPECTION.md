# Offline observation inspection

Version **0.23.0** preserves the v0.22.0 packaged-catalog-ordered inspection cards/tables for **12
observations from four studies**: six unchanged 2D model-dependent summaries
and the six PA12 CF15 3D tensile-test summaries added in v0.22.0. Inspection schema **1.1.0**
references observation schema **1.3.0**. Every family retains its own quantity,
units, method and source-specific evidence. This is catalog inspection, with no
evaluator, fitted result, matched-condition comparison, material ranking or
engineering allowable. Exactly eight executable composite rules remain. See
[source-specific evidence](OBSERVATIONS.md), the [PA12 CF15 guide](PA12_CF15_TEMPERATURE_OBSERVATIONS.md)
and [v0.22.0 migration](MIGRATION_v0.22.0.md).

All no-axes/no-whiskers restrictions in this guide apply to **generic inspection**.
The separate [v0.23.0 temperature-observation plot](OBSERVATION_TEMPERATURE_PLOT.md)
has a closed six-cell admission contract and its own 1.0.0 schema; it does not
change this route's inspection-only purpose, selectors, packaged ordering or
scientific policy.

## Export and select

From the repository root with Python 3.10+, without runtime dependencies:

```sh
python -m materials_boundaries observation inspect --output /tmp/observations --lang en
python -m materials_boundaries observation inspect --output /tmp/hbn --source-id falin_et_al_2017_hbn_mechanical_properties --lang zh
python -m materials_boundaries observation inspect --output /tmp/strength --quantity breaking_strength_2d --group-by quantity --lang ja
python -m materials_boundaries observation inspect --output /tmp/selected --id lee_2008_graphene_in_plane_stiffness_2d --id falin_2017_hbn_monolayer_breaking_strength_2d --lang de
python -m materials_boundaries observation inspect --source-id ciganas2026polym18050563 --output /tmp/pa12-cf15 --lang en
python -m materials_boundaries observation inspect --id ciganas2026-pa12cf15-uts-60c --output /tmp/pa12-cf15-60c --lang de
python -m materials_boundaries observation inspect --help --lang de
```

`--id` is repeatable, with one exact, case-sensitive ID per occurrence.
`--source-id` and `--quantity` are exact, case-sensitive filters; all selectors
combine with **AND**. Supported quantities are `in_plane_stiffness_2d`,
`breaking_strength_2d` and `ultimate_tensile_strength_as_reported_3d`. The default
selects all 12 records; the PA12 source or quantity selects six. Selection retains
catalog order, even when IDs are requested in reverse order. It does not sort by
value, rank materials or perform free-text matching. Use `catalog observations`
for the separate literal text-search interface.

`--group-by study` is the default: separate study sections contain separate
quantity facets. `--group-by quantity` changes navigation/order only and retains
packaged catalog order within each quantity. It establishes no common scientific basis.
Malformed, duplicate or unknown IDs, unknown sources/quantities, unsupported
scientific families and empty filter intersections fail before output files are
written. Valid record identities do not need a presentation record-ID whitelist;
an unknown scientific family is rejected. The PA12 scientific family itself
is closed to six source cells. Subsets and renamed IDs are accepted with the
unchanged payload; full-catalog duplicate cell aliases are rejected. Existing
supported-family appendability is preserved under those families' contracts.

Each export produces five files (English example):

- `observation-inspection.json`: canonical, language-independent audit bundle
- `observation-inspection.csv`: one complete record per row, language-independent
- `observation-inspection.en.svg`: wide, standalone inspection view
- `observation-inspection.narrow.en.svg`: narrow, stacked inspection view
- `observation-inspection.en.html`: standalone responsive inspection page

Select `en`, `zh`, `ja` or `de`; only SVG/HTML filenames and authored human labels
change. Use separate directories to retain different selections. All content is
built and validated before writing any target; invalid input must not leave
misleading partial output. This is not a guarantee of atomic rollback on disk or
permission failure during a valid write.

Open HTML directly in a browser. It is script-free and uses no external fonts,
images or automatic network loads. Source links are ordinary HTTP(S) links,
followed only when the reader chooses. The full JSON bundle is embedded as
escaped inert data. Long evidence/context sections may be expandable; essential
scientific warnings remain visible before values. SVG retains visible summaries
and evidence references without depending on an HTML details panel.

## Read each value together with its caveats

For the older 2D families, the primary value is explicitly labeled
**normalized catalog display**. It uses
the exact stored central/± values in N/m, without fixed-decimal rounding, added
precision, thickness conversion or source correction. It is not a verbatim
quotation. Original source wording/context is retained separately: the hBN
strength string contains both GPa and N/m, but this does not add a selected 3D
result. Graphene has no `source_value_string`; this absence remains explicit.

Stiffness and breaking strength are different quantities despite sharing N/m.
A study's property/condition summaries are associated records, not independent
replications. Central values are not all labeled means: graphene has no
`summary_statistic`, and hBN strength's exact central-statistic label is unknown.

### PA12 CF15: chamber condition, reported MPa and exact SI Pa

Each of the six text-only facets presents the specific 3D printed-material,
dataset/protocol and reported chamber condition before a property value. The
30-minute stabilization does not establish direct specimen temperature or a
verified stability tolerance. Horizontal alternating +45°/−45° FFF, filament
drying, declared 15 wt.% formulation, 100% infill setting and 1 mm/min crosshead
rate remain specific protocol context. Actual moisture/RH and local strain rate
are unknown; drying and infill do not establish measured dry state or zero porosity.

Before every MPa/Pa property display, including a single-condition card, the view
states that stress convention/area basis, central statistic and aggregation are
unknown. Three tensile tests are reported per condition; ± is reported SD, not
CI, SEM or bounds. There is no raw-data reanalysis or universal allowable.

The primary **Catalog display in reported units** uses the exact MPa strings,
such as **32.70 ± 1.18 MPa**. A separate **exact SI unit re-expression** uses
**32700000 ± 1180000 Pa**, with 1 MPa = 1000000 Pa and no added measurement
precision or geometry/thickness calculation. Source strings/context remain
separate. No N/m-to-Pa conversion is applied to the older 2D records.

Complete process, nominal geometry, protocol, scoped count and component evidence
remain visible. The source-version note preserves the inspected HTML revision,
PDF noninspection and the cached/live discrepancy in unselected Table 4. Only
the selected Table 3 UTS/SD cells have HTML/visual/second-transcription agreement.
Article-specific CC BY 4.0 attribution does not extend to excluded manufacturer
Table 1. See [all six conditions and source limits](PA12_CF15_TEMPERATURE_OBSERVATIONS.md).

### MoS2: retain the unresolved q discrepancy

Before every MoS2 value, including a strength-only selection, the view states
that the result is **source-reported, with an unresolved printed-q discrepancy,
unknown actual fit q, and no refit or correction**. Strength inherits the fitted
stiffness/model caveat. The normalized summaries are **180 ± 60 N/m** stiffness
and **15 ± 3 N/m** strength. Their reported-SD definition comes from the inspected
main-text uncertainty sentence, not hBN evidence. Geometry ± tolerances have no
verified statistical definition.

The inspected EPFL main-text PDF is proof-formatted, with pages A–G. Locators
retain one-based PDF pages and printed letters. Identity with final publisher
text and final-pagination equivalence remain unverified. The printed formula,
ν=0.27, and separately printed q=0.95 remain source context. Approximately
1.002168693051764 is curator arithmetic only; it is not the actual fitted q,
a corrected observation or a new measurement. The formula is never executed to
refit values. Strength uses the source finite-spherical-tip local maximum stress
model, distinct from its stiffness point-load fit and the graphene/hBN nonlinear
FEM models. Stress/strain conventions remain unknown.

Nine monolayer membranes are study/stiffness counts, not a separately verified
failure-event count. Force-curve and parent-flake totals remain unknown.
2 μm/s is vertical probe translation speed, not strain/force/stress rate.
400 °C for four hours in vacuum is preparation, not indentation temperature or
atmosphere. Numerical test temperature, atmosphere and humidity remain unknown.

### Graphene: the ± meaning is unverified

Before **340 ± 50 N/m** stiffness and **42 ± 4 N/m** strength, the view states
that the statistical meaning of the reported ± is unverified. It is not SD,
SEM, a confidence interval, a hard bound or a certified uncertainty endpoint.
The separate stiffness-fit distribution mean of 342 N/m and SD of 30 N/m must
not replace or explain 340 ± 50. Its 67 fits, 23 membranes and 2 flakes are
stiffness-only metadata; strength sample metadata remains null.

The source's second-Piola–Kirchhoff stress/Lagrangian strain convention is
preserved for graphene alone. The stiffness point-load fit and nonlinear
finite-radius FEM failure inference remain distinct. Test temperature,
atmosphere, humidity and loading rate remain unverified. The supplement was not
inspected. Passage checks are not raw-data reanalysis or replication.

### hBN: volume-average strength and separate SD evidence

Before **23.6 ± 1.8 N/m** hBN strength, the view identifies the source-reported
nonlinear FEM **volume-averaged under-indenter stress**, with the exact
central-statistic label and stress component unspecified. It is not direct
uniform tension, a local-maximum formula or the maximum Von Mises diagnostic in
Supplementary Fig. S5. That diagnostic's 25.7% model-sensitivity discussion is
not an uncertainty correction or multiplier. Stiffness remains **289 ± 24 N/m**.

Both SD definitions and tested-sheet count semantics rely on the separate
publisher-linked peer-review author response, **PDF p. 8, Reviewer #1 question 3**.
Keep that artifact and locator separate from publisher HTML and supplement
locators. **N=11** is explicitly associated with the stiffness average and is
study context for strength; it is not a verified strength-summary replicate or
failure-event count. Typically five indentations per sheet does not mean exactly
five or a 55-curve dataset. Acquired/retained/excluded curve totals, parent-flake
count and failure-event count remain null.

Ambient does not establish numerical temperature, pressure, gas composition or
humidity. 0.5 μm/s is loading/unloading translation velocity, not strain rate.
The FEM 0.1 nm step is numerical discretization and the 100 nm endpoint is not a
measured mean fracture displacement. The source's 0.334 nm model thickness is
not the illustrated 0.48 nm apparent AFM height or a conversion default.

The printed hBN q formula has no separately printed numerical q to compare;
no MoS2-style mismatch is asserted. Stored q arithmetic is curator arithmetic
only; the actual implementation q is unknown. Finite-strain stress/strain
measures remain unspecified.

### Shared boundaries

Reported SD is not SEM, a confidence interval, 68% coverage, a hard bound or a
full uncertainty budget. No averaging/replicate weighting, coverage or missing
specimen/condition assumption is invented. Unknown conditions never establish
equivalence, including when two records both contain null. Generic inspection has **no axes,
bars, points, error whiskers, endpoint calculations, shared scales or
magnitude-dependent styling**. No averaging, ratios, ranking, interpolation,
refitting or cross-dimensional conversion is performed. PA12 alone adds the
explicit exact MPa-to-Pa scale described above. All records remain `catalog_only`
experiment-derived summaries; older 2D model-dependent records and the new 3D
tensile-test family retain distinct classifications. Neither is a theoretical
bound or executable composite input.

## Audit bundle and CSV

The inspection bundle retains explicit resolved selection and grouping, full
unchanged observation/source snapshots, observation record versions, catalog
schema versions, engine version, stable facet/record/study/quantity references,
required caveats, family-specific reported/normalized display strings and their
catalog-derived basis. PA12 facets additionally preserve dataset, protocol,
source-cell and temperature identity, reported units, SI units and normalization.
Presentation policy is inspection-only, with `overlay_allowed=false`,
`aggregation_allowed=false`, and `unknown_conditions_equivalent=false`.

Deterministic canonical SHA-256 digests identify **bundled metadata snapshots**,
not the original paper bytes. Sources have no individual version field; none is
invented. The existing MoS2 inspected-artifact hash stays provenance for that
artifact only. IDs/digests do not depend on language or numerical ranking.
There are no generated timestamps or random identifiers.

CSV places identity, model status, temperature basis and essential caveats before
property-value columns. `unit`, `central_value` and `plus_minus_value` use reported
result units (N/m for older records; MPa for PA12), not uniformly SI units. New
`si_unit`, `si_central_value`, `si_plus_minus_value` and `normalization_json`
columns explicitly distinguish exact Pa re-expression from the original MPa
strings; older records retain N/m with identity normalization. Additional columns
include `reported_value_string`, `reported_plus_minus_string`, `dataset_id`,
`protocol_id`, `source_cell_json` and `temperature_value`, `temperature_value_string`, `temperature_unit`,
`temperature_basis`, `temperature_json` fields. Read
columns by name, not fixed position. Source strings preserve trailing zeros.
Uncertainty meaning/evidence, scoped counts, conditions, locators, versions and
digests accompany each row. Compact JSON columns retain complete record/source
snapshots, including null unknowns. The policy declares scalar missing values as
the literal `null`; missing cells must never be interpreted as zero. CSV is an inspection
format, not a ready-to-aggregate measured dataset.

## Python API and validation

```python
from materials_boundaries.observation_visualization import (
    build_observation_inspection, validate_observation_inspection,
    inspection_json, inspection_csv, render_observation_svg,
    render_observation_html, export_observation_inspection,
)

bundle = build_observation_inspection(
    source_id="bertolazzi_brivio_kis_2011",
    quantity="breaking_strength_2d",
    group_by="study",
)
validate_observation_inspection(bundle)
json_text = inspection_json(bundle)
csv_text = inspection_csv(bundle)
svg = render_observation_svg(bundle, lang="en", width=1100)
html = render_observation_html(bundle, lang="en")
paths = export_observation_inspection("/tmp/mos2-strength",
    source_id="bertolazzi_brivio_kis_2011", quantity="breaking_strength_2d", lang="en")
```

`record_ids=None`, `source_id=None`, `quantity=None`, and `group_by="study"`
are builder/export defaults; the export locale defaults to `en`.
Renderers and exports validate by canonical rebuilding from the resolved
selection and currently packaged catalogs. Altered values, evidence wording,
snapshots, selection, caveats, policy, facets, digests or schema/software versions
are rejected with `ValidationError`. Stale bundles must be explicitly regenerated;
do not edit their version labels. This dependency-free admission check is
separate from optional development-time JSON Schema validation. No observation
formula or composite evaluator is called by the inspection builder.

The inspection layer also checks the complete Lee and MoS2 source-defined
scientific payloads; the existing hBN guard already performs that check. These
older families retain their supported ID/name appendability and evidence-order
semantics. The new PA12 guard pins complete six-cell scientific payloads and
source provenance, including metadata gaps, rights and inspected revision. Its
subset/renamed-ID admission must not be confused with full-catalog cell duplication.
Changing scientific values or semantics needs a reviewed source contract rather
than silently inheriting existing caveats. XML-illegal characters are rejected
before export rather than removed from evidence or snapshot text.

## Evidence, rights and review

Source passage inspection and a second transcription check do not constitute
raw-data reanalysis, independent scientific review or replication. Inspection
gaps and artifact-specific licensing remain visible. No source PDF, full text,
figure, screenshot or raw measurement collection is redistributed. The hBN main
article's CC BY 4.0 does not establish the license of the supplement or peer-review
file. PA12 article CC BY 4.0 is verified at the article copyright block; it is
not extended to excluded third-party manufacturer content. See [source ledger](SOURCES.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).

Authored English, Chinese, Japanese and German labels/notices are working
translations, not independently scientifically or native-speaker reviewed.
Source wording, identifiers, numbers, evidence, selection and digests remain
language-independent. Static SVG pixel review and actual browser reflow QA are
different checks; successful software tests alone prove neither. Record the
checks actually performed for each release rather than treating this guide as
a report of successful browser or independent scientific review.
