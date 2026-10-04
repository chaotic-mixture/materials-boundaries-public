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
