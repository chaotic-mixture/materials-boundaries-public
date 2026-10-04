# Migration to v0.32.0

This additive catalog batch adds nine identities and nine source-qualified
experimental properties: **34 + 9 = 43**, one selected property per identity.
It adds no evaluator, material-specific scientific branch, physical quantity,
unit conversion, statistical calculator, ranking or universal material bound.
The material/reference envelope schema versions remain **1.0.0**. Upgrade the
runtime, generated reference-property schema and four-language locale labels
together; a v0.31 reader does not understand the new uncertainty alternative or
the newly accepted scientific-notation source strings.

## One closed uncertainty alternative

The existing `reported_standard_deviation`, `reported_confidence_interval` and
`reported_plus_minus_unspecified` alternatives remain unchanged. The added
`reported_measures` alternative must exactly match `uncertainty_status` and has
a nonempty `measures` array. It is not an open metadata bag, a nested uncertainty
envelope, a physical min/max range or a set of confidence endpoints. It requires
a scalar central `reported_value`.

Each descriptor has these fields:

- `kind`: `standard_deviation`, `coefficient_of_variation`,
  `standard_error_of_mean` or `estimated_inaccuracy`
- `availability`: `numeric_reported` or `graphical_only`
- `basis`: `absolute` or `relative_to_reported_value`
- `reported_value`: for numeric measures, source-preserved `number`,
  `value_text`, `unit_text` and `unit_code`; for graph-only SD, **null**
- `qualifier`: `approximately` or `not_qualified_in_source`
- `scope` and `evidence`: required population/measurement-specific description
  and nonempty primary-source evidence with exact source, URL and locator
- `confidence_level` and `coverage_factor`: both **null** in this extension
- `note`: nullable in general, but a substantive explanation is required for
  graphical-only amplitude unavailability or unnamed central aggregation

Numeric amplitudes retain the bounded, finite, nonnegative exact-decimal
contract. Absolute SD must match the central result's physical unit. CV, SEM
and estimated inaccuracy use **relative percent** in this first capability;
`percent` is not added as a pressure, modulus, strength or density result unit.
CV is numeric, with no arbitrary 100% ceiling. Relative SEM requires explicit
source-supported `reported_mean`; source evidence for a measure kind cannot
itself establish the central aggregation. Exact duplicate descriptors are
rejected, while distinct measures are not merged merely because their values
coincide. Unsupported combinations, unknown keys, signs, nonfinite tokens,
excessive precision and mismatched source text/numbers remain invalid.

### Preserve the source's actual meaning

- **Flax/hemp:** numeric CV **56.12% / 72.02%**, respectively, accompanies
  mean chord moduli. No SD, SEM, absolute interval or accuracy estimate is
  derived from either CV
- **Silk:** SD is `graphical_only`, `basis: absolute`, with
  `reported_value: null`, an exact Figure 4b/caption locator and an explicit
  no-digitization/unavailable-numeric-amplitude note. Null does not mean zero
  and does not erase the reported SD type
- **Wool:** numeric absolute SD **23 MPa** accompanies an explicitly unknown
  central aggregation (`summary_statistic: not_stated`). The separate source
  evidence identifies SD without turning **163 MPa** into a reported mean.
  The legacy mean-plus-SD branch is not weakened
- **Molybdenum:** numeric relative SEM **0.02%** and **approximately 0.1%**
  estimated inaccuracy remain two descriptors in one property's envelope.
  The latter is not specimen spread, mean uncertainty, certified maximum
  error or a confidence interval

There is no quadrature, summation, SD-to-SEM, CV-to-SD, confidence construction,
absolute/relative conversion or numerical digitization. In particular, do not
flatten `reported_measures` into one ± amplitude or label it absent uncertainty.
Four-language text must show kind, availability, basis, qualifiers and unknowns;
original source-language qualifications remain canonical. Machine-assisted
labels do not constitute native-language or scientific review.

## Scientific notation preserves printed precision

The generic source-value matcher accepts narrowly bounded source forms using a
mantissa multiplied by an integer power of ten, and validates exact equivalence
to the fixed-point canonical decimal. The new source examples are:

- Molybdenum: `value_text: "10.21 × 10^3"`, `number: "10210"`
- Tungsten: `value_text: "19.23 × 10^3"`, `number: "19230"`

Both retain source `unit_text: "kg m−3"` and canonical `unit_code: "kg/m^3"`.
The original source strings, including mantissa digits, remain in JSON and text
output. Equivalent numerical magnitude does not authorize replacing them with
bare integers or rewriting the measured precision. This is notation validation,
not a unit conversion, floating-point parser or general expression evaluator.
Mantissa/exponent and expanded length stay resource-bounded; only explicitly
supported spellings are admitted. Arbitrary expressions, overflow and altered
number/text pairs remain invalid. This gate affects tungsten as well as
molybdenum, even though tungsten needs no new uncertainty kind.

## Source corrections and compatibility

The [coverage note](MATERIAL_COVERAGE_v0.32.0.md) supplies exact source locators,
conditions, all nine facts and rights. Important migration qualifications are:

- AZ31 is the **unreinforced as-extruded comparator**. Detailed SPS/extrusion
  settings are study context, not an independently itemized AZ31 protocol;
  nano-TC4 preparation is not transferred. The PDF extraction duplication
  does not make the independently rendered method page unreadable
- Flax/hemp's chord definition and no-compliance rationale are on **p.8**,
  with Figure 6 on p.7. Record the methods C1557-03 / bibliography C1557
  (2020) discrepancy without claiming exact-edition compliance
- Silk sampling concerns **intraspecific and intraindividual variability**;
  thirty samples came from five chosen cocoons. Record the §2.7 ANOVA /
  Figure 4 t-test discrepancy without a significance claim
- Existing `composite` applies to flax/hemp only as a qualified natural
  hierarchical bundle mapping; existing `polymer` applies to silk/wool as
  natural protein fibers. No `natural_fiber` enum, resin-composite identity or
  purified-protein claim is introduced
- Qualitative room/ambient temperatures remain qualitative. Wool's 55 °C
  cleaning, AZ31's 6 mm/s extrusion and NBS pulse-heating/vacuum conditions
  are not transferred to selected tests. Unknown methods, counts, pressure,
  humidity, aggregation and density/annealing chronology remain unknown

The compatibility requirement preserves all prior 34 identities, grades, states,
properties, source records and their rendered outputs, along with the existing
eight-rule evaluator, model/claim/prediction catalogs, scientific fixtures and
examples. New records remain catalog-only, with non-universal/non-allowable
flags and no independent scientific-review or raw-data-reanalysis claim.

Fresh evaluations/reports use package version **0.32.0**. Strict replay requires
its matching software/catalog snapshot; explicitly regenerate an older report
from retained inputs when needed. Historical outputs are not rewritten.

## Verification and publication gates

Independent source-transcription acceptance is not software-test success or
release admission. Before admission, validate the exact new catalog graph in
both generated schema and runtime; test all allowed and rejected descriptor
combinations, evidence linkage, scientific notation and precision limits;
compare all old records/outputs; check four-language JSON/text; run the full
unit suite, catalog validators, wheel metadata and installed-wheel smoke tests.
These are required gates, not a claim here that they have already passed.

Six CC BY 4.0 sources and two separately scoped NBS Technical Series sources
retain their [attributions and reuse limits](../THIRD_PARTY_NOTICES.md#metals-and-natural-fiber-references-v0320).
No source PDF, HTML/XML, complete table, figure, screenshot or source dump is
redistributed. No publication, repository push or release completion is implied
by these migration instructions.
