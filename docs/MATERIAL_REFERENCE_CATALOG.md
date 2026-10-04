# Concrete material identities and reference properties

Version 0.29.0 adds a separate, offline catalogue of concrete source-scoped
materials. Each admitted material state resolves at least one numerical property
with its original value/unit strings, source URL and precise locator. These
records are not added to the existing mathematical claims, specimen-observation
families or computational predictions. No reference value becomes a calculator
input automatically.

## Browse and inspect

```sh
python -m materials_boundaries catalog materials --text --lang en
python -m materials_boundaries catalog materials --category polymer --text --lang zh
python -m materials_boundaries catalog materials --query "graphite" --text --lang ja
python -m materials_boundaries catalog reference-properties --quantity mass_density --text --lang de
python -m materials_boundaries catalog materials --json
```

Use `--id` for an exact state/property ID, `--source-id` for a primary property
source, and `--quantity` or `--evidence-kind` for the supported exact property
filters. Materials additionally accept `--identity-id`, `--grade-id` and
`--category`. Reference properties additionally accept `--material-id` (the
state ID) and `--reporting-basis`. All supplied filters combine with AND. When a
material query supplies several property filters, the same linked property must
satisfy all of them. An unrecognized or inapplicable filter fails rather than
silently disappearing.

Search is literal Unicode-casefold, all-term substring matching across IDs,
canonical names, authored English/Chinese/Japanese/German names, explicit
aliases, grade designations and source property labels. It does not infer
chemical equivalence or translate a query. The selected display language never
changes canonical JSON, scientific source wording, numeric precision or units.
Exact IDs and filter codes remain case-sensitive. `--help --lang LANG` describes
the new routes in each supported language.

Text output resolves property-specific conditions and citations. Unknown test
temperature, temper, orientation, porosity, conditioning and uncertainty remain
explicit unknowns. A processing temperature is not a measurement temperature.
A source’s disclaimer, limited inspection scope and reuse-license evidence must
be read with the property.

[Initial selected materials and exact source values](MATERIAL_COVERAGE_v0.29.0.md)

## What is counted

- An **identity** is the curated source-supported material composition or
  formulation. Broad categories, names, translations and aliases do not add
  identities
- A **grade** is a qualified source designation belonging to an identity. A
  missing grade remains null; it is not an invented generic grade
- A **state** is the source-scoped product/form/processing context. Another
  state or another temperature is not another material identity
- A **property** is one source-reported value for one state. Two properties do
  not count as two materials

The `material_coverage(materials, properties)` API derives reachable identity,
grade, state and property counts from the actual registry. Exact structural clones are rejected even when IDs or display aliases change.
Chemical equivalence and genuinely distinct formulations still require source-based
curation; software counts validated registry identities, not independently proven
chemical species. No production count or material-name whitelist limits later
valid contributions. The initial
release deliberately selects one independently cross-checked property per
identity. These are coverage counts, not counts of independent replications or
claims that whole chemical families have known universal properties.

## Evidence and interpretation

Manufacturer and technical-association references remain reference values,
even when the source mentions a measurement. A typical value, guideline range
or specification limit is not a theoretical material bound or an engineering
allowable. Published experimental summaries keep their separate evidence class.
Source-reported calculation is never silently relabelled measurement.

The printed-polymer tensile results retain the source’s mean, a separate
reported standard deviation and exact test-group n=5. SD is neither SEM nor a
confidence interval. The supplier product and print/drying/testing recipe limit
applicability; 100% slicer infill does not establish zero physical porosity.
Missing product SKU and lot information is not filled in by guessing.

The ceramic entries are particular study specimens, including their additives,
processing and porosity context, rather than constants for pure ceramic
families. Apparent, bulk, Archimedes-method and helium-pycnometric density scopes
are retained without treating them as interchangeable. A method name alone does
not establish an unsupported density-basis classification.

Every record remains `catalog_only`, with `universal_bound: false` and
`engineering_allowable: false`. There is no autofill, numerical conversion,
interpolation, fitted curve, ranking, mixing calculation or engineering
comparison. The eight pre-existing executable composite rules are unchanged.

## Storage and validation

`materials_boundaries/data/materials.json` holds identities, grades and states.
`reference_properties.json` holds the separate source-reported facts.
`material_locales.json` holds four-language interface labels; material names
are authored in the registry. Bibliography reuses the existing append-only
source registry.

The new closed schemas and dependency-free runtime validator check record
shape, supported quantities/units, finite decimal lexical values, evidence and
source integrity, reciprocal state/property ownership, unique IDs and reachable
identities/grades. They reject orphan states, dangling sources, unknown fields,
incorrect SD units and unsupported evaluator capabilities. Every state needs at
least one resolved property. A malformed unselected record is rejected before
filtering. Validation is not independent scientific peer review, a specimen
check, native-language certification or legal clearance.

`resolve_material(state_id, materials, properties, sources)` supplies an
inspection envelope containing the identity, nullable grade, state, properties
and referenced source records. This is an in-process inspection API; there is
no separate stable inspection-file schema or engineering input format in this
release.

## Source and rights scope

Only brief attributed facts, source locators and original curation are bundled.
No source PDF, screenshot, copied table, article full text or extracted research
prose is included. CC BY sources are attributed and linked; their articles are
not relicensed by the project. Manufacturer/association sources with no verified
open license retain that unknown status. Limited factual curation is not a
blanket reuse permission or legal-clearance claim. Rights-held candidates stay
outside the package. See [third-party notices](../THIRD_PARTY_NOTICES.md).

## Add a material without a new Python family

1. Identify and evidence a genuinely distinct identity, or reuse an existing
   one. Qualify a real grade only when the source supplies it
2. Create the source-scoped state, explicit unknowns and a nonempty property
   list; append a bibliographic source only if it is genuinely new
3. Preserve original values, decimal precision, unit strings, statistics,
   comparators/ranges and per-property conditions. Never infer missing test
   conditions or convert a source range into uncertainty
4. Use only the already supported quantity/unit/representation contract. A new
   scientific capability requires schema/runtime review, but a valid new grade
   ID with supported facts requires no material-specific code
5. Record source inspection, source-version/hash status, identity-distinction
   rationale and rights admission. Provide all four authored names and retain
   the machine-assisted/not-scientifically-reviewed label status
6. Run `python scripts/validate_catalogs.py`, the complete unittest suite, wheel
   metadata checks and an installed-wheel smoke test. Refresh only marked
   current summary counts in a disposable contribution rehearsal

Old scientific records and historical fixtures must remain unchanged. Source
inspection and factual transcription review do not upgrade
`independent_scientific_review` or claim raw-data reanalysis.

## v0.30.0 second material batch

The [v0.30.0 coverage](MATERIAL_COVERAGE_v0.30.0.md) adds seven distinct
source-scoped identities and keeps the v0.29.0 discussion above as the initial
release history. The additions use the same identity/grade/state/property graph,
closed fields, source-preserving display and catalog-only safeguards.

### Compilation and measured-input derivation

`published_handbook_reference` with
`determination_basis: source_reports_compiled_measurements` identifies a
published handbook or analogous explicit compilation of empirical results.
Its required method type, `source_reported_compilation`, explains the compilation
and the selected property's method/reference-condition scope using source
evidence. Compilation can include aggregation, source-side unit conversion and
reference-condition adjustment; it is not a claim of new experimentation at
publication or direct testing at every stated condition.

`published_measurement_derived_reference` with
`determination_basis: source_reports_calculation` separates properties explicitly
derived from measured inputs from direct measured properties and purely
computational predictions. The v0.30.0 supported combination is deliberately
limited to `mass_density`, `density_basis: crystallographic` and
`method_definition.type: source_reported_crystallographic_derivation`.
The definition and evidence explain the measured unit-cell inputs, adopted cell
content/atomic masses and the source's derivation. This gate is generic by
physical method, not by material ID. Other measured-input-derived methods need
an explicit reviewed contract before admission.

`crystallographic` density is distinct from `bulk`, `apparent`, powder packing
and a silently inferred `true` density. An experimental calibration correction
or ordinary data reduction does not alone require this derived class: the
historical silicon recalibration remains `published_experimental_reference`
with `source_reports_measurement` and `source_reported_conventional`.
The method-definition object still has only its existing keys. These new enums
do not unlock calculation, mixing, interpolation or evaluator use.

Examples of the new exact evidence filters:

```sh
python -m materials_boundaries catalog materials --evidence-kind published_handbook_reference --text --lang en
python -m materials_boundaries catalog reference-properties --evidence-kind published_measurement_derived_reference --text --lang de
```

Source lexical fidelity also permits ASCII spaces between fractional digit
groups in a decimal-point token: `2.329 1289` retains that `value_text`, while
`number` is `2.3291289`. The first fractional group has three digits, any
intermediate groups have three, and the final group has one to four; each
separation is exactly one ASCII space. Matching preserves every digit and decimal
place; it is not arbitrary whitespace removal, arithmetic parsing or permission
to discard trailing zeroes. Existing integer thousands-grouping syntax stays separate.
The unit spelling `grams per cubic centimeter` maps to `g/cm^3` without changing
the number or original unit string.

### Conditions belong to the selected result

- Historical NBS silicon crystal X2 uses the corrected 1975 assigned value.
  The direct 20 °C reference statement is in the 1974 companion; the 1975
  introduction and §7 connect the same crystals to correction-only
  recalculation. The chain establishes a reference basis, not a claim that the
  1975 value table prints 20 °C or every determination occurred at 20 °C. X2 is
  one physical crystal; repeated determinations are not additional specimens.
  The value is not current certification, and old uncertainty is not carried
  into the revised value
- Germanium source number 4065 has a 25 °C crystallographic density derived
  from measured powder-XRD lattice data. The diffraction-pattern temperature
  of 26 °C has a different role. The identifier is not proven to be a batch,
  stock code, unique specimen or grade; physical-specimen count is unknown.
  It is neither weighed bulk density, powder packing density nor a DFT result
- Sugar maple, northern red oak and Sitka spruce are species-average handbook
  flexural references on a common 12% moisture basis. Some dry data were
  adjusted by the source; direct-versus-adjusted history for each cell is
  unknown. The simply supported center-loaded beam has span/depth 14:1, and
  the reported longitudinal bending modulus includes shear deflection. No
  approximate 10% correction is applied. This is not an axial or isotropic
  Young's modulus. ASTM D 143 is a source-stated procedural basis, without a
  cell-specific edition/compliance claim. The generic 22% green-wood
  coefficient of variation is not these cells' SD or uncertainty
- NC1 concrete is the study's nominal 28-day water-saturated formulation,
  with a reported mean over three cylinders. Its 20 °C curing/storage
  condition is not a density-test temperature. Preserve the source's nominal
  age despite the demolding/storage chronology ambiguity; do not repair it to
  29 days. CEM I 42.5 R identifies a cement constituent, not a concrete grade.
  The maximum individual deviation statement is not SD or uncertainty
- Carrara marble's bulk density belongs to disk specimen 13, not a pooled
  group mean. Density procedure, instrument, temperature, moisture and
  uncertainty remain unknown. Tabulated mass/dimensions do not establish a
  geometric method; dry/environmental-temperature wording concerns P-wave
  testing. The source's group-SD reversal and unselected group-geometry
  conflict are recorded without assigning either group SD to this specimen

All numerical-source hashes refer to the actual inspected asset. In particular,
NC1's selected-value digest identifies Europe PMC XML, not publisher HTML/PDF.
The 1974 silicon companion has inspected web-text support but no retained-byte
hash; no checksum is invented. Recorded hashes require a null `hash_note`;
revision/erratum information belongs in revision or inspection scope.

Only selected facts, precise citations and original qualifications are included.
NIST/NBS Technical Series, scoped USDA government-authored content and two
article-specific CC BY 4.0 sources retain their distinct rights evidence in the
[third-party supplement](../THIRD_PARTY_NOTICES.md#second-material-reference-batch-v0300).
The independent check was source-transcription review, not independent
scientific peer review or raw-data reanalysis. Optional GaAs remains excluded
behind its indentation-specific quantity/method gate.


## v0.31.0 fiber and elastomer batch

Six further concrete identities add two tensile moduli, one Young's modulus and
three mass-density values. Read the [source-specific limits](MATERIAL_COVERAGE_v0.31.0.md)
before using any selected fact. All prior 28 records retain their original data.
The material/reference envelopes remain 1.0.0, as in the preceding additive
extension; clients must upgrade runtime, schema and locale labels together.

### Closed uncertainty variants

A numerical uncertainty has a matching `uncertainty_status` and `uncertainty.type`,
a nonnegative finite exact-decimal amplitude, matching result unit, source evidence
and a source-scoped note. It requires a scalar central result. It is never stored
as a physical min/max range or confidence endpoints.

- `reported_standard_deviation` retains the existing explicit `reported_mean`
  evidence requirement and null confidence-level/coverage metadata
- `reported_confidence_interval` stores a source-reported symmetric ± amplitude
  plus `confidence_level` (`value_text`, exact decimal-string `number`,
  `unit_code: percent`). The level is strictly between 0 and 100, with matching
  percent text. `estimand` and `construction` are evidence-backed reported facts,
  or explicitly not reported with explanatory notes. There is no default mean
  estimand, distribution, formula, SD/SE conversion or coverage factor. A CI with
  an unreported confidence level is not admitted by this version
- `reported_plus_minus_unspecified` retains a reported ± amplitude whose
  statistical meaning is unspecified. Confidence level and coverage factor stay
  null. It does not require or imply arithmetic-mean aggregation

The complete source expression belongs in `uncertainty_note`, alongside separate
central and amplitude strings. Null uncertainty is allowed only for the existing
nonnumerical statuses. Four-language text dispatches the actual kind, CI level,
unknown estimand/construction and type-appropriate notice. Old SD output is
unchanged. Source truth still requires independent review: structural validation
cannot determine whether free text truthfully describes an experiment.

### Source windows and normalization

`method_definition.extraction_window` is null or a reported fact with text,
evidence and optional notes. Non-null windows require primary method support;
a linked primary-source entry can establish the supporting article's role, with
actual detailed methods attributed to that article. Source strain units and
qualifiers remain in the text. This field is not an executable fit definition,
range evaluator or permission to reinterpret finite-extension rubber stress as
Young's modulus.

Normalization and correction facts use the existing condition/fact fields.
Unknown, not verified and not applicable remain distinct. The source's applied
Sylgard geometry/strain correction is not applied again. A circular-area formula
for basalt strength does not verify its modulus-area estimator. T700S's selected
dataset cell is not recomputed from diameter or replaced by a manufacturer value.

Fresh, independently source-qualified identities can reuse these generic
contracts, with new IDs and evidence. Holds for Kevlar 49, Dyneema SK76 and
Sylgard 527 describe this batch's unresolved evidence only; there is no permanent
ID or chemical-family ban. The eight-rule evaluator, existing scientific
families, old observations/predictions and catalog-only boundary are unchanged.
