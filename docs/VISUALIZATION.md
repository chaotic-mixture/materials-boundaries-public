# Offline, traceable elastic comparison views

## Current v0.22.0: mixed 2D and 3D observation inspection

[Observation inspection](OBSERVATION_INSPECTION.md) now contains 12 source-ordered
text facets from four studies. Six PA12 CF15 facets represent six reported
chamber conditions from one tensile-test protocol; the older six 2D facets
retain their original scientific contracts. Inspection schema 1.1.0 distinguishes
reported MPa display from exact SI Pa re-expression. No N/m-to-Pa conversion is
added for older observations. Regenerate old bundles rather than relabel them.

Every new facet shows chamber basis, preparation/rate, unknown stress/statistic,
three-test scope and reported-SD caveats before its property values. There are
no temperature axes, bars, points, whiskers, connecting curves, magnitude styling,
interpolation, ranking, aggregation or cross-dimensional comparison. Study or
quantity grouping changes navigation only. The five synthetic temperature models,
12 computational predictions and eight-rule composite comparison remain unchanged.

```sh
python -m materials_boundaries observation inspect --source-id ciganas2026polym18050563 --output /tmp/pa12-cf15 --lang en
```

See [source/protocol limits](PA12_CF15_TEMPERATURE_OBSERVATIONS.md) and
[migration](MIGRATION_v0.22.0.md). Historical sections below describe their own
release scope. Static pixel inspection and browser reflow remain separate checks.

## Earlier v0.21.0: explicit six-point Ni11X group

The prediction catalog now has 12 records in two scientific families and three
explicit groups. The new six-point group `shimanek_v2_table2_cr_mn_fe_cu_si_ti`
uses the unchanged prediction renderer and must be selected with `--group-id`.
The original three-point Ni/Al/Co default and three-point Si first-instability
group remain unchanged. No automatic nine-point overlay is introduced.

```sh
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six --lang en
```

These are published-method-only Ni11X predictions on a zero-origin GPa axis,
not pure-solute measurements, commercial grades or universal bounds. Unknown
conditions and uncertainty remain unresolved; 0.08 GPa convergence supplies no
error bars. Bare source labels do not establish PAW datasets or valence states.
See [prediction evidence and limits](COMPUTATIONAL_PREDICTIONS.md) and
[v0.21.0 migration](MIGRATION_v0.21.0.md). Historical checked-in previews are
preserved; source figures are not reproduced.

## Earlier v0.20.0: separate observation inspection

[Observation inspection](OBSERVATION_INSPECTION.md) adds source-ordered,
non-quantitative cards/tables for the six existing experiment-derived,
model-dependent summaries. It exports JSON/CSV and wide/narrow SVG plus offline
HTML, with exact ID/source/quantity filters and study/quantity grouping. Primary
source-specific warnings precede values; normalized catalog displays remain
separate from original source strings. The closed inspection schema is 1.0.0;
scientific records and existing comparison schemas remain unchanged.

There are no observation axes, bars, points, error whiskers, shared scales,
rankings, aggregation, endpoint calculations or magnitude-dependent styling.
Unknown conditions never establish equivalence. This is no observation evaluator
or matched-condition comparison and does not authorize overlays into the existing
composite, prediction or synthetic-temperature pipelines. The existing eight
composite rules and scientific results remain unchanged.

```sh
python -m materials_boundaries observation inspect --output /tmp/observations --lang en
python -m materials_boundaries observation inspect --output /tmp/strength --quantity breaking_strength_2d --group-by quantity --lang de
```

See [v0.20.0 migration](MIGRATION_v0.20.0.md). The historical visualization notes
below describe their own pipelines and release-specific exclusions; they are not
claims that v0.20.0 lacks an observation inspection view. Static SVG inspection
and actual browser reflow QA remain distinct verification activities.

## Existing composite visualization layer

This first visualization layer plots the existing canonical elastic engine only:
conditional Hashin–Shtrikman (HS) K/G intervals, optional Reuss/Voigt lower/upper
bounds, and derived E/ν outer envelopes. It adds no physical calculator and does
not plot the catalog-only strength/fracture models, stability predicates, porous solid/void records or separate observation summaries.

## Open the demo

From the repository root, Python 3.10+, without runtime dependencies:

```sh
python scripts/generate_visualization_demo.py
# Optional choices:
python scripts/generate_visualization_demo.py --lang zh
python scripts/generate_visualization_demo.py --output /tmp/materials-demo --without-classical
```

The generated exports are intentionally excluded from version control to avoid
repeating the full evidence bundle in four HTML files. The source, schema and
generators retain the complete traceability contract. The default writes:

- `examples/visualization/comparison.en.html`, `.zh.html`, `.ja.html`, `.de.html`
- `examples/visualization/comparison.json`, the deterministic comparison bundle
- `examples/visualization/synthetic-two-phase.bulk.svg`
- `examples/visualization/literature-epoxy-glass-model.bulk.svg`

Open an HTML file directly in a browser. All charts and numeric/provenance details
are local. There are no network requests, external fonts, package downloads, or
executable scripts. Native expandable sections expose numeric values, original
inputs, compatibility checks and source evidence. The complete bundle is embedded
as inert, escaped JSON. `--lang all` makes English standalone SVGs; selecting one
language makes SVGs in that language. Locale selection never changes numbers.

The checked-in Chinese overview, `preview.desktop.zh.svg` and
`preview.desktop.zh.png`, is a historical static preview from the visualization
release, rendered through Inkscape. Its version label is not the current catalog
version; regenerate the comparison bundle and previews for current-release QA. Other PNG/SVG previews (including narrow arrangements) remain generated
local outputs. These are static review artifacts, not browser screenshots or an
alternative scientific data source. Rebuild the English previews with
`python scripts/render_visualization_preview.py` if Inkscape is already installed.
First generate `comparison.json` with the ordinary demo generator above.
Previously generated local bundles may retain old engine/catalog versions and
are not automatically migrated; regenerate them after a release update.
Add `--lang zh` for the Chinese overview (`preview.desktop.zh.png` /
`preview.mobile.zh.png`).
The labeled overview helper is restricted to the two unchanged bundled demo
inputs; use `render_svg` for other cases. The ordinary demo generator needs no
Inkscape and does not generate PNGs.

Static chart rendering has been inspected. Browser-based desktop/mobile HTML
layout QA remains unverified in this execution environment: Chromium could not
start due to local IPC restrictions, and the cloud browser does not support local
file URLs. The HTML has responsive wide/narrow chart layouts, but this limitation
must not be described as a successful browser check. Rebuilding HTML/SVG and JSON
is deterministic; PNG appearance can vary with fonts and renderer version.

## What the curves mean

The two demo cases are the synthetic fixture and the literature epoxy/glass
constituent-model fixture. The second phase fraction is sampled at 21 chosen
values from 0 to 1. The complementary first phase is `1 − f₂`. This is an explicit
calculator-selected parameterization, **not a measured composition series**, a
published experimental curve, or a new material-performance prediction. The
original fixture fractions and complete source input records remain unchanged in
the bundle; each sample records its actual fractions and canonical evaluation.

Shaded regions are **conditional theoretical bound intervals**, not confidence
bands or measurement uncertainty. Dots mark evaluated parameter choices, not
observations. Straight segments connect adjacent available computed points for
visual guidance only; they are not independently evaluated or certified bounds
between samples. E/ν envelopes are conservative images of separate K/G intervals;
neither tightness nor joint attainment of their endpoints is asserted.

Each point calls `engine.evaluate`, including f₂ = 0 and 1. Pure-phase endpoints
must still meet the engine's conditions. Unknown or violated applicability,
numerical overflow and other unavailable canonical outputs remain null gaps.
The renderer never fills or connects through those gaps; isolated valid endpoints
remain isolated marks. Invalid input structure is rejected before evaluation.

Literature constituent inputs retain their original E/ν values, K/G conversion,
source locator and stated calculator assumptions. They are not represented as a
measured specimen. Temperature, grade, cure state and measurement uncertainty are
unspecified in the supplied examples and are prominently flagged. The original
source metadata/rights statements remain attached; no paper or figure is bundled.

## Python API

```python
from materials_boundaries import load_json
from materials_boundaries.visualization import (
    build_comparison, comparison_json, render_html, render_svg,
    validate_comparison, compatibility_gate, convert_value,
)

inputs = [load_json("examples/synthetic-two-phase.json"),
          load_json("examples/literature-epoxy-glass-model.json")]
bundle = build_comparison(inputs, fractions=[0, .1, .2, .5, 1],
                          output_unit="GPa",
                          labels={"synthetic-two-phase": "Synthetic illustration"})
html = render_html(bundle, lang="en", include_classical=True)
svg = render_svg(bundle, "synthetic-two-phase", "effective_shear_modulus",
                 lang="en", width=560)
json_text = comparison_json(bundle)
```

- 1–50 cases, each with exactly two declared phases; original instance IDs are
  stable, unique case IDs. Duplicate cases must be given distinct input IDs
- 2–501 finite, strictly increasing, unique sweep values within [0, 1]
- Series IDs are stable hashes of case and claim IDs, unaffected by case order,
  labels or language. Point IDs include the case and exact supplied x text
- Physical quantities, rule/claim IDs, claim versions, source IDs and records,
  input provenance, conditions, per-point checks, numerical state, actual fractions,
  evaluation schema version and engine version are all retained
- Each quantity uses a common y-axis domain across all case facets in a bundle;
  quantities have separate axes. The same selected x values align all cases
- Moduli support Pa, kPa, MPa and GPa. Poisson's ratio is dimensionless unit `1`,
  including negative or zero values. Dimension-incompatible/unknown conversions
  are rejected; no unit is guessed. Canonical phase comparison uses exact Pa text
- `include_classical=False` hides Reuss/Voigt from views without deleting their
  values or evidence from the bundle
- `render_svg` exports one case and quantity, width 300–1600. HTML uses separate
  narrow/wide layouts and retains all four quantities
- Labels and all metadata are escaped. Arbitrary formulas or scripts are never
  executed. Formula text remains data

## Comparison gate and future N-case extension

Cases are **always separate facets in this release**, even if a gate passes.
Nothing automatically overlays a model and an experiment as interchangeable.
The pairwise gate checks quantity/dimension, known unit conversion, the complete
axis definition (including swept/complementary phase IDs), engine conditions,
context, provenance kind and phase definitions. Any known mismatch gives
`incompatible`. Without a mismatch, any unknown condition/context gives `unknown`;
two nulls never establish equality. Only fully matching known metadata gives
`compatible`, which is still not a scientific certification of physical identity.
`overlay_allowed` is always false.

Different phase identities and model-input bases make the supplied demo cases
incompatible for a common physical overlay. Their side-by-side views remain
useful for inspecting different conditional model envelopes. Shared axis scales
are a visual convention, not evidence of equal temperature, material processing,
measurement method, or comparable uncertainty.

The bundle is deliberately ready for N-case selection/faceting, stable series
references and future explicit axis definitions. This release does not import
arbitrary measured series, fit models, compute uncertainty, interpolate missing
points, compare fracture strength to elasticity, or supply a general dashboard.
Changing the axis meaning or adding measured-series contracts requires a new,
explicitly reviewed extension.

## Schema, reproducibility and validation

`schemas/comparison.schema.json` is JSON Schema 2020-12, comparison schema 1.0.0.
It embeds snapshots of the existing input/evaluation/claim/source contracts for
standalone, network-free validation. Update those snapshots when the referenced
contracts change; tests ensure the snapshot stays in sync.

JSON Schema checks structure. `validate_comparison` additionally rebuilds all
points from retained inputs using the currently installed engine/catalog and
compares the complete deterministic payload. Altered values, changed checks,
misleading labels of scientific semantics, stale claim/source records or other
metadata/version changes fail closed. Renderers run this validation first. To use
an older bundle with a new release, explicitly regenerate from its retained
inputs and review the version change; do not silently relabel it.

There are no timestamps or random numbers in the generated bundle. Engine
outputs retain their existing rounded-float numerical policy; this layer does
not certify outward rounding. Exported coordinates are computed in Decimal before
conversion to bounded pixel positions so extreme finite values cannot overflow
axis construction. Displayed tables use four significant digits; the bundle
retains the full canonical numbers.

Run the full suite:

```sh
python -m unittest discover -s tests -v
```

Dedicated tests cover canonical point reproduction, four languages, stable IDs,
source/claim provenance, conditions at pure endpoints, missing/violated/numerical
gaps, no gap bridging, unit conversion, dimensionless ν, unknown context,
incompatible axes/conditions, extreme finite coordinates, deterministic exports,
untrusted labels, schema validation and fail-closed tamper detection. Optional
`jsonschema` tests explicitly skip when that development dependency is absent.

Translations are working labels, not independently scientifically or
native-speaker reviewed. Software tests and equation cross-checks do not replace
independent scientific peer review.

## Historical v0.5.0 compatibility

The four new stability criteria are catalog-only predicates and never become plotted curves or evaluation results. The comparison bundle continues to include only the eight executable composite claims, although its embedded claims schema is updated to 1.4.0. No stability chart, eigensolver or anisotropic Poisson-ratio calculation is introduced.


## Historical v0.6.0 compatibility

The three new porous solid/void intervals are `catalog_only` and are never plotted as computed results, even though their quantities and bound types also occur in executable records. The comparison bundle still contains only the original eight composite evaluations, with no porous curves, density axis, empty-domain Poisson ratio or new chart/API. Active zero-modulus phases remain outside the evaluator's supported conditions.

The embedded claims-schema snapshot advances to 1.5.0; comparison schema 1.0.0 and the instance/evaluation/source identifiers are unchanged. The original 19 claim records and 18 sources are preserved. Regenerate existing comparison exports for engine 0.6.0 rather than relabeling stale bundles; the same valid inputs retain their eight evaluation results apart from engine version.

[`examples/catalog/porous-synthetic.json`](../examples/catalog/porous-synthetic.json) is a documentation-only synthetic calculation illustration, not an instance, comparison bundle, measured series or input accepted by these rendering APIs. See [porous scope and endpoint conventions](POROUS_BOUNDS.md) and [migration](MIGRATION_v0.6.0.md).

## Historical v0.7.0 observation separation

The new observation catalog contains two model-dependent N/m summaries from one graphene AFM study. It is not a measured volume-fraction series, a composite instance or a comparison bundle. Neither its stiffness nor its breaking strength can be added as an overlay to the existing pressure-valued elastic sweeps. Shared unit labels alone would not establish comparable quantities, material state, dimensionality, method, conditions or stress/strain conventions.

No observation curves, uncertainty bars, default thickness, N/m-to-GPa conversion or observation-rendering API are added. In particular, the unverified ±50 and ±4 meanings must not be drawn as confidence bands or theoretical bound endpoints. The separate stiffness distribution SD and sample counts do not describe breaking-strength uncertainty or sample size.

The comparison contract remains schema 1.0.0 and selects only the eight executable claims and their evidence. Claims schema stays 1.5.0 and source schema 1.0.0; the observation schema is not embedded as a new comparison input. Regenerate exports using engine 0.7.0 from the same valid composite instances rather than relabeling stale bundles. Numeric results remain unchanged apart from engine version. See [observations](OBSERVATIONS.md) and [migration](MIGRATION_v0.7.0.md).

## v0.8.0 crystal-stability separation

Four additional tetragonal I/II and rhombohedral I/II stability predicates bring the complete catalog to 26 claims, including eight catalog-only stability records. They do not become plotted curves, numerical classifications, new input parameters or comparison series. All 20 source records and both separate observations remain unchanged.

The embedded claims-schema snapshot advances to **1.6.0** while comparison schema remains **1.0.0**, evaluation remains 1.1.0 and source schema remains 1.0.0. The comparison bundle still selects only the original eight executable composite claims and their evidence; it never evaluates predicate formula text. Regenerate exports from retained valid composite instances using **engine 0.8.0** rather than editing version labels in a stale bundle. The same inputs retain their numeric results, conditions and evaluation order. Historical checked-in previews remain historical and are not evidence of current-release browser QA. See [v0.8.0 migration](MIGRATION_v0.8.0.md).

## v0.9.0 fatigue separation

The two new empirical fatigue records do not enter comparison bundles or plots. Exactly the original eight executable elastic series remain. The embedded claims-schema snapshot advances to 1.7.0 and engine to 0.9.0; comparison schema remains 1.0.0. Regenerate from valid retained composite inputs; do not relabel old bundles. No coefficient fitting, fatigue evaluation, lifetime integration or fatigue chart is implemented.

## v0.11.0 anisotropy boundary

The two anisotropy indices remain catalog-only and never enter comparison
bundles or plots. Exactly eight composite rules remain, and the isolated
temperature renderer is unchanged. New bundles embed claims schema 1.8.0 and
engine 0.11.0; numerical series are unchanged. Historical bundled visualization
examples remain historical and are not relabeled.

## Separate computational point comparisons (v0.12.0)

`python -m materials_boundaries prediction plot --output /tmp/ideal-shear --lang zh`
exports unconnected source-specific model points with preserved original decimal
strings and full provenance. The comparison is restricted to the shared reported
method; unknown conditions are not treated as proven equal. It supplies no
stress–strain interpolation, invented error bars or universal bounds. This
separate renderer does not change the composite or temperature visualizations.
See [computational predictions](COMPUTATIONAL_PREDICTIONS.md).

## v0.19.0 hBN observations remain outside composite plots

At v0.19.0 the catalog contained six observations from three studies after adding
the two monolayer hBN summaries. All remain `catalog_only` and are excluded
from composite comparison builders/renderers, overlays, rankings and uncertainty
bands. The hBN N/m stiffness and model-dependent FEM strength are distinct
quantities; source SDs are not certified bounds or plot-ready confidence bands.
The eight executable rules and their numerical comparison behavior are unchanged.
No hBN plot, thickness conversion or cross-study matched-condition comparison
is introduced. See [observation evidence and limits](OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)
and [migration](MIGRATION_v0.19.0.md).
