# Offline observation inspection

Version **0.20.0** adds source-ordered inspection cards/tables for the **six
existing model-dependent observations from three studies**. This is a separate
presentation of catalog evidence, with a closed inspection schema **1.0.0**.
It adds no observations, evaluator, fitted result, matched-condition comparison,
material ranking or engineering allowable. Exactly eight executable composite
rules remain. See [source-specific observation evidence](OBSERVATIONS.md) and
[v0.20.0 migration](MIGRATION_v0.20.0.md).

## Export and select

From the repository root with Python 3.10+, without runtime dependencies:

```sh
python -m materials_boundaries observation inspect --output /tmp/observations --lang en
python -m materials_boundaries observation inspect --output /tmp/hbn --source-id falin_et_al_2017_hbn_mechanical_properties --lang zh
python -m materials_boundaries observation inspect --output /tmp/strength --quantity breaking_strength_2d --group-by quantity --lang ja
python -m materials_boundaries observation inspect --output /tmp/selected --id lee_2008_graphene_in_plane_stiffness_2d --id falin_2017_hbn_monolayer_breaking_strength_2d --lang de
python -m materials_boundaries observation inspect --help --lang de
```

`--id` is repeatable, with one exact, case-sensitive ID per occurrence.
`--source-id` and `--quantity` are exact, case-sensitive filters; all selectors
combine with **AND**. Supported quantities are `in_plane_stiffness_2d` and
`breaking_strength_2d`. The default selects all six records. Selection retains
catalog order, even when IDs are requested in reverse order. It does not sort by
value, rank materials or perform free-text matching. Use `catalog observations`
for the separate literal text-search interface.

`--group-by study` is the default: separate study sections contain separate
quantity facets. `--group-by quantity` changes navigation/order only and retains
source order within each quantity. It establishes no common scientific basis.
Malformed, duplicate or unknown IDs, unknown sources/quantities, unsupported
scientific families and empty filter intersections fail before output files are
written. Future IDs in an already supported, validated family do not need a
presentation record-ID whitelist; an unknown scientific family is rejected.

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

The primary value is explicitly labeled **normalized catalog display**. It uses
the exact stored central/± values in N/m, without fixed-decimal rounding, added
precision, thickness conversion or source correction. It is not a verbatim
quotation. Original source wording/context is retained separately: the hBN
strength string contains both GPa and N/m, but this does not add a selected 3D
result. Graphene has no `source_value_string`; this absence remains explicit.

Stiffness and breaking strength are different quantities despite sharing N/m.
A study's two property summaries are associated records, not independent
replications. Central values are not all labeled means: graphene has no
`summary_statistic`, and hBN strength's exact central-statistic label is unknown.

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
equivalence, including when two records both contain null. There are **no axes,
bars, points, error whiskers, endpoint calculations, shared scales or
magnitude-dependent styling**. No averaging, ratios, ranking, interpolation,
refitting or conversion is performed. These remain `catalog_only`,
experiment-derived, model-dependent summaries, not theoretical bounds or
executable composite inputs.

## Audit bundle and CSV

The inspection bundle retains explicit resolved selection and grouping, full
unchanged observation/source snapshots, observation record versions, catalog
schema versions, engine version, stable facet/record/study/quantity references,
required caveats, normalized display strings and their catalog-derived basis.
Presentation policy is inspection-only, with `overlay_allowed=false`,
`aggregation_allowed=false`, and `unknown_conditions_equivalent=false`.

Deterministic canonical SHA-256 digests identify **bundled metadata snapshots**,
not the original paper bytes. Sources have no individual version field; none is
invented. The existing MoS2 inspected-artifact hash stays provenance for that
artifact only. IDs/digests do not depend on language or numerical ranking.
There are no generated timestamps or random identifiers.

CSV places identity, model status and essential caveats before value columns.
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
scientific payloads; the existing hBN guard already performs that check. Record
IDs and display names remain appendable, and evidence order is immaterial.
Changing scientific values or semantics needs a reviewed source contract rather
than silently inheriting existing caveats. XML-illegal characters are rejected
before export rather than removed from evidence or snapshot text.

## Evidence, rights and review

Source passage inspection and a second transcription check do not constitute
raw-data reanalysis, independent scientific review or replication. Inspection
gaps and artifact-specific licensing remain visible. No source PDF, full text,
figure, screenshot or raw measurement collection is redistributed. The hBN main
article's CC BY 4.0 does not establish the license of the supplement or peer-review
file. See [source ledger](SOURCES.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).

Authored English, Chinese, Japanese and German labels/notices are working
translations, not independently scientifically or native-speaker reviewed.
Source wording, identifiers, numbers, evidence, selection and digests remain
language-independent. Static SVG pixel review and actual browser reflow QA are
different checks; successful software tests alone prove neither. Record the
checks actually performed for each release rather than treating this guide as
a report of successful browser or independent scientific review.
