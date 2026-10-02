# Synthetic temperature-model demonstrations

The first-public-release baseline, **0.16.0**, introduced **five original synthetic models
with seven branches** in the separate temperature catalog. Their coefficients,
intervals and displayed GPa values are deliberately invented to demonstrate
software behavior. They are not measured or fitted material properties,
reference data, theoretical bounds, engineering allowables or NIST predictions.
No real material identity or physical applicability is implied.

At that historical **v0.16.0 baseline**, the 34 mechanics claims, two published
observations, six computational predictions and exactly eight executable
composite rules were separate. Its source catalog contained 47 records: the
46 existing source identities plus
`materials_boundaries_synthetic_temperature_demo`, which records original
author provenance rather than an external publication.

The current [v0.19.0 catalog expansion](MIGRATION_v0.19.0.md) has 51 sources
and six observations from three studies. These five synthetic temperature models
and their seven branches are unchanged.

## Polynomial and branch contract

Every branch uses the fixed quartic form, including lower-degree special cases:

`E_GPa = a + b*T_K + c*T_K^2 + d*T_K^3 + e*T_K^4`

Coefficient strings are stored in order a–e. Their dimensional roles are GPa,
GPa/K, GPa/K², GPa/K³ and GPa/K⁴. These labels exercise unit handling; they do
not make the artificial values scientifically calibrated. Decimal/Horner
arithmetic uses a fixed context before conversion to finite positive binary64
values. Extra digits support arithmetic reproducibility, not physical precision.
Formula strings are display-only; arbitrary expressions are never executed.

| Model ID | Branch ID | Authored coefficients a, b, c, d, e | Artificial inclusive range (K) |
|---|---|---|---|
| `synthetic_linear_temperature` | `synthetic_linear_10_100` | 10, 0.1, 0, 0, 0 | 10–100 |
| `synthetic_overlap_temperature` | `synthetic_overlap_20_50` | 20, 0.1, 0, 0, 0 | 20–50 |
| `synthetic_overlap_temperature` | `synthetic_overlap_50_100` | 30, 0.05, 0, 0, 0 | 50–100 |
| `synthetic_quadratic_temperature` | `synthetic_quadratic_25_125` | 40, -0.1, 0.001, 0, 0 | 25–125 |
| `synthetic_quartic_temperature` | `synthetic_quartic_10_200` | 100, -0.1, 0.001, -0.000001, 0.000000001 | 10–200 |
| `synthetic_interval_temperature` | `synthetic_interval_20_80` | 50, 0.05, 0, 0, 0 | 20–80 |
| `synthetic_interval_temperature` | `synthetic_interval_60_120` | 60, -0.025, 0, 0, 0 | 60–120 |

All records are `synthetic_demo`; `source_data_range_K` is null because no
measurements exist. Fit-error values are null with a synthetic/not-applicable
explanation. No error percentage, uncertainty band, source-transcription status,
real alloy designation, UNS number or treatment history is invented. Original
construction is disclosed as `author_provenance`.

### Reproducible arithmetic examples

- Linear demo at 50 K: **15 GPa**
- Shared-endpoint overlap demo at 50 K: **25 and 32.5 GPa**
- Quadratic demo at 75 K: **38.125 GPa**
- Quartic demo at 100 K: **99.1 GPa**
- Interval-overlap demo at 70 K: **53.5 and 58.25 GPa**

The quadratic has an interior minimum at 50 K; monotonicity is not imposed.
Both branches of the interval demo apply throughout 60–80 K, including the
endpoints. `ambiguous_overlap` retains every applicable branch; there is no
winner, average, smoothing or splicing. Artificial branch differences are not
physical discontinuities. Outside every branch range, `out_of_range` returns
an empty predictions list. No extrapolation is performed.

## Offline CLI and Python API

```sh
python -m materials_boundaries temperature catalog --text --lang en
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-linear-50k.json --json
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-overlap-50k.json --lang zh
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-quadratic-75k.json --lang ja
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-quartic-100k.json --lang de
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-interval-overlap-70k.json --json
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-linear-outside-5k.json --json
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-interval-outside-10k.json --json
python -m materials_boundaries temperature plot --output /tmp/temperature-demos --lang en --points 101
```

Inputs are separate from two-phase composite instances:

```json
{"schema_version":"1.0.0","model_id":"synthetic_overlap_temperature","temperature":{"value":50,"unit":"K"}}
```

Only finite nonnegative JSON numbers with explicit `K` units are accepted.
Booleans, strings, nulls, negative temperatures, nonfinite values, duplicate
keys, unsupported fields and unknown IDs are rejected. There is no implicit
Celsius conversion. Invalid input exits 2; an out-of-range lookup exits 0
without a value. Numerical-output range failures exit 3. Results snapshot the
input, model, sources and conditions and include stable content-derived IDs.
Branch predictions retain their own IDs, GPa values and ranges.

```python
from materials_boundaries.temperature import evaluate_temperature
from materials_boundaries.temperature_visualization import (
    build_temperature_comparison, comparison_json, comparison_csv,
    render_temperature_svg, render_temperature_html,
)

result = evaluate_temperature({
    "schema_version": "1.0.0",
    "model_id": "synthetic_overlap_temperature",
    "temperature": {"value": 50, "unit": "K"},
})
# Omitted IDs select all current models, not a permanently fixed model count.
bundle = build_temperature_comparison(points_per_branch=101)
svg = render_temperature_svg(bundle, lang="en", width=1100)
selected = build_temperature_comparison([
    "synthetic_linear_temperature", "synthetic_overlap_temperature"],
    points_per_branch=101)
```

The fixed polynomial evaluator and separate catalog/CLI structure remain intact.
Development validation checks local schemas, finite coefficient strings,
branch ranges, source resolution, scientific-family identity, synthetic
provenance and four-language metadata. A schema-valid demonstration is not a
scientifically validated material model. New empirical data would require
separate source, scientific and rights review.

## Presentation and exports

Localized presentation is kept separate from canonical model data. Names,
material snapshots, provenance, rights status and four-language descriptions
must agree with the models; stale or inconsistent snapshots fail validation.
Canonical JSON, IDs, coefficient strings, ranges and units do not change with
`--lang en|zh|ja|de`. Translation review is machine-assisted and has not been
independently scientifically or natively reviewed.

The CLI writes deterministic JSON, CSV, SVG, a narrow static SVG and
self-contained HTML. No network scripts are required. JSON includes the full
provenance/condition bundle; CSV is a branch-sample view and should accompany
that JSON.

- Separate facets keep the five artificial models distinct; aligned temperature
  axes and separate GPa scales do not imply comparable real specimens
- Samples are generated inside each branch and include endpoints; they are not
  measurements or experimental sample counts
- Polylines connect samples only within a branch and never bridge excluded
  regions or merge overlapping branches
- Shared overlap endpoints are annotated dynamically. An endpoint annotation
  is not a list of every temperature inside an overlap interval
- No uncertainty band or theoretical-bound fill is drawn
- Visible labels may round to six decimal places, while canonical exports
  preserve evaluator precision; display rounding never changes branch selection
- Canonical reconstruction rejects changed values, removed overlap branches,
  forged provenance, stale snapshots or unsupported policies

The two-model subset in `examples/temperature/visualization/` and the complete
catalog in `examples/temperature/catalog-visualization/` both use only synthetic
data. Regenerate result/plot bundles after model, source or version changes.
Static SVG inspection is not browser interaction testing or material validation.

## NIST bibliography and release boundary

The public package omits the five NIST cryogenic coefficient datasets and all
their derived evaluations, fixtures and plots. Their bibliographic source
records remain, but no runnable NIST model is supplied. This conservative
choice pending reuse clarification does not establish that redistribution is
prohibited and does not remove unrelated literature facts.

NIST currently lists the collection as a curated data collection, formerly
SRD 152. Its current classification and past-SRD origin are distinct facts;
neither alone provides a verified express redistribution/relicensing grant.
Official links and source-specific caveats are in [Third-party notices](../THIRD_PARTY_NOTICES.md#nist-cryogenic-material-properties)
and [source provenance](SOURCES.md). Original synthetic demonstrations and
project software are MIT-licensed; third-party works retain their own rights.
