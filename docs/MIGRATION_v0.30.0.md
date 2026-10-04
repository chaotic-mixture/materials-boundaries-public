# Migration to v0.30.0

This additive release extends the separate material-reference lane by seven
source-scoped identities, seven states and seven selected properties. It adds no
grades, evaluator rules, automatic inputs or unit-conversion facility. See the
[batch coverage](MATERIAL_COVERAGE_v0.30.0.md) and
[contract supplement](MATERIAL_REFERENCE_CATALOG.md#v0300-second-material-batch).

## Generic contract additions

The material and reference-property envelope schema versions remain **1.0.0**.
Clients with hard-coded closed enums must accept the new values below, or
upgrade their runtime and generated schemas together before reading this batch.
Existing fields and records keep their meaning; no material-name special case
is introduced.

- `published_handbook_reference` is paired with
  `source_reports_compiled_measurements` and method type
  `source_reported_compilation`. It identifies an explicit compilation of
  empirical results, potentially aggregated, unit-converted or adjusted by the
  source to a reference condition. It does not assert a new experiment by the
  handbook author or direct testing at every displayed reference condition
- `published_measurement_derived_reference` is paired with
  `source_reports_calculation`. In this release its supported method type is
  `source_reported_crystallographic_derivation`, quantity `mass_density`, and
  density basis `crystallographic`: measured unit-cell inputs and source-adopted
  cell content/atomic masses support a source-reported density calculation.
  Method/classification evidence must identify that derivation. Other
  measured-input-derived methods remain deferred until their own generic
  contracts are reviewed. This class is neither direct bulk measurement nor
  first-principles prediction
- `source_reported_conventional` retains its prior role. Ordinary experimental
  reduction and a documented calibration correction do not automatically
  reclassify a direct experimental result as measurement-derived

The method-definition object gains no keys. The additions extend enum handling,
exact evidence-kind filters and English/Chinese/Japanese/German label coverage;
canonical source text and JSON codes remain unchanged by display language.
Translations remain machine-assisted and not scientifically reviewed.

## Exact source strings

`grams per cubic centimeter` is an accepted original spelling of `g/cm^3`,
used by the germanium source. It is retained as `unit_text`; no numerical
conversion occurs.

Fractional digit grouping is now accepted for decimal-point source strings such
as `2.329 1289`, with canonical `number: "2.3291289"`. Only ASCII spaces between
fractional digit groups are normalized for the exact lexical comparison: the
first group has three digits, intermediate groups have three, and the final
group has one to four, with exactly one space at each separation. `value_text`
itself is preserved. The digit sequence and decimal precision must match exactly. This is not arbitrary whitespace stripping and does not admit
signs, exponents, multiple decimal marks, arithmetic or lost trailing zeroes.
Existing supported integer thousands grouping remains separate.

## Preservation and interpretation

The seven additions are a historical silicon crystal, a source-numbered
crystalline germanium reference, three wood species, one concrete formulation
and one Carrara-marble study specimen. No specimen labels, repeat measurements
or moisture states inflate identity count. The silicon 20 °C reference basis
requires the explicitly qualified 1974/1975 evidence chain. The woods use a
compiled 12% moisture basis; the germanium density is XRD-derived. Concrete
curing temperature and marble P-wave conditions do not become density-test
conditions.

Existing mechanics claims, observations, predictions, synthetic demonstrations,
eight executable composite rules and historical fixtures are preserved. Old
source records remain unchanged by ID; new bibliography appends. Existing
silicon strength predictions remain distinct from this historical density
reference. This is not independent scientific review or raw-data reanalysis.

Fresh evaluations/reports identify package version **0.30.0**. Strict report
replay still requires the matching software/catalog snapshot; an older saved
report may require explicit regeneration from its original input. Historical
saved reports are not rewritten or invalidated by that requirement.

All new references remain `catalog_only`, `universal_bound: false` and
`engineering_allowable: false`. Hashes identify inspected source bytes, not
scientific truth or unrestricted reuse rights. No source assets are bundled.
