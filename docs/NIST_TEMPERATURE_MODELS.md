# NIST temperature-conditioned empirical fits

Five NIST empirical models cover 6061-T6 aluminum, 304 stainless steel, 5083 aluminum (5083-O in the NIST material index), Invar (Fe-36Ni), and 316 stainless steel. Their seven equation branches coexist with five synthetic demonstrations. The evaluated quantity is Young's modulus within the selected equation's temperature range.

## Scientific meaning

All five models are **compiled empirical predictions of Young's modulus**, not
measurements, theoretical bounds, material standards, strength limits, certified
reference values or design allowables. Calling the evaluator selects a named
source fit; it does not establish applicability to a real specimen. Unknown
specimen metadata stays unknown rather than being supplied from general knowledge.

Every branch uses ordinary absolute temperature, not a logarithmic thermal fit:

`E_GPa = a + b*T_K + c*T_K^2 + d*T_K^3 + e*T_K^4`

The exact source strings are stored in coefficient order a–e. Their dimensions
are GPa, GPa/K, GPa/K², GPa/K³ and GPa/K⁴ respectively. Decimal/Horner arithmetic
has its own fixed context and returns finite positive binary64 values in GPa.
Extra output digits support arithmetic reproducibility, not measurement precision.
Formula strings are display-only; no eval, exec, downloaded formula code or
arbitrary expression interpreter is used. The `T_low` and `f` entries in the
new sources' second tables do not contain modulus values; the neighboring
linear-expansion piecewise formula does not create another modulus branch.

| Model / branch | Exact coefficients a, b, c, d, e | Equation range (K) | Source data range (K) |
|---|---|---|---|
| 6061-T6 aluminum | 7.771221E1, 1.030646E-2, -2.924100E-4, 8.993600E-7, -1.070900E-9 | 2–295 | 0–299 |
| 304 stainless, low branch | 2.098145E2, 1.217019E-1, -1.146999E-2, 3.605430E-4, -3.017900E-6 | 5–57 | 5–65 |
| 304 stainless, high branch | 2.100593E2, 1.534883E-1, -1.617390E-3, 5.117060E-6, -6.154600E-9 | 57–293 | 48–293 |
| 5083 aluminum (index: 5083-O) | 8.083212E1, 1.061708E-2, -3.016100E-4, 7.561340E-7, -6.994800E-10 | 2–295 | 0–300 |
| Invar (Fe-36Ni) | 1.41565E2, 2.54435E-2, -1.00842E-3, 6.72797E-6, -1.08230E-8 | 3–298 | 1–298 |
| 316 stainless, low branch | 2.084729E2, -1.358965E-1, 8.368629E-3, -1.381700E-4, 6.831930E-7 | 8–50 | 5–60 |
| 316 stainless, high branch | 2.079488E2, 7.394241E-2, -9.627200E-4, 2.845560E-6, -3.240800E-9 | 50–294 | 48–294 |

The source data range does not authorize extrapolation outside the equation
range, or establish a measurement at every listed endpoint. The two aluminum
data intervals beginning at 0 K are not proof of actual measurements at 0 K.
The source-data-only regions stay excluded from their respective equation
branches, including 5083 below 2 K or above 295 K, Invar below 3 K, and 316's
low branch at 5–<8 K or >50–60 K and high branch at 48–<50 K. A different branch
may still apply: at 48 K only the 316 low branch applies; at 60 K only its high
branch applies. There are no gaps inside the equation-interval unions of these
five models. No extrapolation fills temperatures outside those unions.

### Material identity and unknown conditions

- 6061-T6 does not silently include T651 or other tempers
- 304 does not include 304L, 316 or other grades; its temper is unspecified
- The official material index calls the 5083 page **5083-O**, UNS A95083. The
  property-page heading and Young's-modulus reference say 5083 without a temper.
  `temper: O` records index metadata only, not independently verified annealing
  or specimen history. No other 5083 temper is inferred
- Invar is the source's Fe-36Ni label, UNS K93600. Treatment, compositional
  tolerances and magnetic state are not inferred
- 316 is UNS S31600 in the index, with unspecified treatment. It does not
  establish 316L applicability

Pressure, direction, grain size, texture, porosity, product form, specimen
geometry, cold work, test method, rate/frequency and measurement uncertainty stay
unknown. No pressure dependence or experimental configuration is invented.
The original Mann charts have not been retrieved, and independent scientific
and native-language translation review have not been completed.

### Overlaps and nonmonotonicity

Endpoints are inclusive as a catalog interpretation of the source's range
notation. At shared endpoints the tables supply no branch-selection rule. The
evaluator returns `ambiguous_overlap` and **both** branch predictions:

| Model / temperature | Low branch (GPa) | High branch (GPa) | Absolute mismatch (GPa) |
|---|---|---|---|
| 304 at 57 K | 214.3985951711 | 214.4359087188254 | 0.0373135477254 |
| 316 at 50 K | 209.59835375 | 209.5745605 | 0.02379325 |

These are branch-fit mismatches, not evidence of physical discontinuities.
There is no selection, averaging, smoothing or splicing. Immediately below or
above an overlap only the matching low or high branch applies. Outside every
equation interval the status is `out_of_range` with an empty predictions list.

No monotonicity is imposed. For example, Invar's synthetic fitted values are
141.632435498527 GPa at 3 K, 141.72259408 at 20 K, 139.67082 at 100 K and
152.289880435872 at 298 K. The 5083 curve and lower-temperature 316 branch also
have increases and decreases. These are arithmetic features of the published
polynomials, not newly measured trends, exact extrema or a claimed mechanism.

### Error distinctions

All seven current branches report **1% curve-fit error relative to source
data**. This is the modulus-column value; error percentages in neighboring
thermal or expansion columns do not apply. The statistical definition (maximum
residual, RMS, etc.), confidence level, measurement uncertainty and total
prediction uncertainty are unspecified. No ±1% confidence, measurement-error,
worst-case prediction or design-safety band is produced. NIST's 2006 database
paper separates fit accuracy from overall data accuracy. Future supported
models must carry their own reported fit error; the renderer does not assume
every model has 1% error or NIST provenance.

## Offline CLI and Python contracts

```sh
python -m materials_boundaries temperature catalog
python -m materials_boundaries temperature catalog --text --lang zh
python -m materials_boundaries temperature evaluate examples/temperature/al5083-77k.json --json
python -m materials_boundaries temperature evaluate examples/temperature/invar-100k.json --lang de
python -m materials_boundaries temperature evaluate examples/temperature/ss316-overlap-50k.json --lang ja
python -m materials_boundaries temperature evaluate examples/temperature/al5083-outside-300k.json --json
python -m materials_boundaries temperature evaluate examples/temperature/invar-outside-1k.json --json
python -m materials_boundaries temperature evaluate examples/temperature/ss316-outside-5k.json --json
python -m materials_boundaries temperature plot --output /tmp/temperature-plots --lang en --points 101
```

A temperature input is separate from a two-phase composite instance:

```json
{"schema_version":"1.0.0","model_id":"nist_ss316_young_temperature","temperature":{"value":50,"unit":"K"}}
```

Only finite nonnegative JSON numbers with unit `K` are accepted. Booleans,
strings, nulls, negative temperatures, nonfinite values, duplicate JSON keys,
unknown fields/IDs and implicit Celsius conversions are rejected. Unknown or
invalid input exits with code 2. An out-of-range fit lookup is a successful
non-prediction (exit 0); it never extrapolates. A result snapshots its exact
input, model, source records and unresolved condition metadata, with a stable
content-derived ID. Predictions have a branch ID, value, GPa unit and range.
No scalar winning value exists for an overlap.

```python
from materials_boundaries.temperature import evaluate_temperature
from materials_boundaries.temperature_visualization import (
    build_temperature_comparison, comparison_json, comparison_csv,
    render_temperature_svg, render_temperature_html,
)
result = evaluate_temperature({"schema_version":"1.0.0",
    "model_id":"nist_ss316_young_temperature",
    "temperature":{"value":50,"unit":"K"}})
# Omitted IDs select the current catalog; the API has no fixed model count.
bundle = build_temperature_comparison(points_per_branch=101)
svg = render_temperature_svg(bundle, lang="en", width=1100)
# Preserve an explicit historical selection when needed.
old_pair = build_temperature_comparison([
    "nist_al6061_t6_young_temperature", "nist_ss304_young_temperature"],
    points_per_branch=101)
```

`temperature_models.json` and `temperature_input.schema.json` remain version
1.0.0. The development validator checks local schemas, source resolution,
cross-catalog unique IDs, five finite coefficient strings, equation/data ranges,
fixed family identity, fit-error meaning and four-language descriptions/UI keys.
Existing composite schemas and science are unchanged. A deliberately reviewed
new-ID contribution under the same complete family is supported; this is not
permission to import unverified coefficients or introduce new science unnoticed.

## Presentation metadata and plot/export semantics

Localized presentation is separate from immutable scientific model records.
The optional `model_presentation` map in `temperature_locales.json` is keyed by
model ID. Its four-language `names`, exact `material_snapshot`,
`temper_evidence`, linked `temper_source_id`, `primary_source_id`,
`reuse_status_snapshot` and `rights_review` are checked by a dependency-free
presentation validator. This is a closed metadata contract: unexpected fields,
incomplete language maps, stale snapshots and inconsistent temper/evidence/source
combinations fail validation. Temper evidence distinguishes `property_page`,
`material_index_only` and `not_specified`. It cannot silently turn 5083's
index-only label into verified specimen history. Rights metadata currently uses
`public_reuse_terms_unverified` and does not supply a license grant.

A model without authored presentation metadata retains its canonical name and
honest temper fallback: specified temper with evidence unverified, or temper
unspecified. It does not inherit 304 wording, NIST attribution or 1% error.
Current generic notices derive overlap temperatures/values, intervals and fit
information from each model. Every shared overlap endpoint is printed dynamically;
these endpoint annotations are not an exhaustive list of every temperature in a
possible overlap interval. Visible numerical plot values use six decimal places;
canonical JSON/CSV retain the evaluator's numerical precision. Display rounding
never replaces source coefficient strings or changes branch selection.
Historical locale strings are retained separately
from the active `current_*` labels so presentation improvements do not rewrite
old fixtures or scientific records. Localized names/prose are display metadata,
not translated coefficients or independent scientific review.

The CLI writes deterministic canonical JSON, CSV, SVG, a narrow static SVG,
and self-contained static HTML. HTML needs no network scripts; source links
are ordinary optional external links. JSON is the full provenance/condition
export. CSV is a branch-sample view and should travel with that JSON because it
does not duplicate every source detail.

- Each material is a separate facet, never an overlay. Temperature axes align;
  modulus scales differ and are labeled GPa. This does not assert matched
  physical conditions or an apples-to-apples specimen comparison
- Chosen samples are generated within each equation branch, including its exact
  endpoints. They are not measurements or experimental sample counts
- SVG segments connect samples within one branch only. Separate polylines never
  bridge gaps or merge overlapping branches. Exact endpoints are marked; both
  values appear at 304's 57 K and 316's 50 K overlap
- No statistical band or theoretical-bound fill is drawn. Unknown conditions,
  interpretation limits, attribution and review limitations are disclosed
- Renderers recreate the full expected bundle from packaged models and sources,
  rejecting modified numerical values, removed overlap branches, forged
  provenance, stale snapshots, unknown fields and changed policies
- Four authored languages change presentation only. Canonical JSON, IDs,
  coefficients, intervals and physical units are language-independent

The historical two-model demo remains separate at
`examples/temperature/nist-visualization/`. The five-model demo is at
`examples/temperature/nist-catalog-visualization/`; the omitted-ID default includes
all currently packaged models, with no permanently fixed five-model limit.
Static SVG pixel inspection is not browser/HTML interaction testing or proof of
a mobile web layout.

## Sources and reuse

- [NIST 6061-T6 Aluminum](https://trc.nist.gov/cryogenics/materials/6061%20Aluminum/6061_T6Aluminum_rev.htm): second table, Young's-modulus a–e, data/equation ranges, fit error and equation below
- [NIST 304 Stainless](https://trc.nist.gov/cryogenics/materials/304Stainless/304Stainless_rev.htm): second table, both modulus columns and equation
- [NIST 5083 Aluminum](https://trc.nist.gov/cryogenics/materials/5083%20Aluminum/5083Aluminum_rev.htm): second table, first property column; the property heading omits temper
- [NIST Invar](https://trc.nist.gov/cryogenics/materials/Invar(Fe-36Ni)/Invar_rev.htm): second table, first property column; Fe-36Ni and UNS K93600 in heading
- [NIST 316 Stainless](https://trc.nist.gov/cryogenics/materials/316Stainless/316Stainless_rev.htm): second table, first and second modulus columns; separate equation intervals and shared endpoint
- [NIST material index](https://trc.nist.gov/cryogenics/materials/materialproperties.htm): 5083-O/A95083, Invar/K93600 and 316/S31600 identities
- [Reference list](https://trc.nist.gov/cryogenics/materials/references.htm): Mann, *LNG Materials and Fluids*, first edition 1977; charts 1009 for both aluminum entries, 1005 for Invar, and 1016 for both stainless entries. The `6/1/1979` annotations on Invar/316 are retained without inventing their significance. Original charts were **not retrieved**; primary measurement methods/uncertainties remain unverified
- [Bradley, Radebaugh and Lewis, 2006](https://trc.nist.gov/cryogenics/Papers/Material_Properties/2006-Cryogenic_Material_Properties_Database-Update_2006-ICEC21_Prague.pdf): printed p.3 Eq.6, p.5 Table 2, p.6 reference 5 and New Features
- [NIST Cryogenic Technology Resources](https://trc.nist.gov/cryogenics/), item 3: correlations developed under a past NIST SRD project; no product-specific license or SRD identifier established
- [NIST web reuse policy](https://www.nist.gov/copyrights-disclaimers) and [SRD/non-SRD reuse distinctions](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications)

Coefficients and validity intervals come from NIST Cryogenic Material Properties
Database, retrieved 2026-10-02. Transcription, fixed evaluator, synthetic
arithmetic fixtures and plots are original curation/software work and are not
endorsed by NIST. Information is supplied AS IS, without warranties. The
correlations originated under a past Standard Reference Data (SRD) project.
Project-specific public redistribution/relicensing terms are **not verified;
review is pending**. General web guidance, absent page-level copyright markers,
attribution and the 2006 paper's own contribution notice do not establish
database-wide rights. No public-domain or CC0 claim is made.

The current catalog includes five empirical Young's modulus models from the NIST Cryogenic Material Properties Database alongside five synthetic demonstrations. The NIST records include selected coefficients, equation ranges and calculated examples. Source-specific redistribution and relicensing terms remain unverified. The project MIT license covers original project work. NIST retains its applicable rights. See [third-party notices](../THIRD_PARTY_NOTICES.md).
