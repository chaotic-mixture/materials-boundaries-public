# Migration to v0.35.0

Baseline: v0.34.0 commit `7e37be919ee97f1275249dcf745f9f55e951986a`,
tree `98b67e0632fb0595079c6c11b78c202c53dda0ac` (402 tracked files).

## Intentional changes

- Add the mutually exclusive `natural` class, explicitly biological tissue/fiber
- Apply the versioned `natural-biogenic-v1` taxonomy policy to ten existing
  identities: ten categories and 24 classification-scope text fields change
- Preserve every prior numerical property, statistic, uncertainty, condition,
  grade, original source, source identity and all eight evaluator rules
- Add optional closed canonical-taxon and empirical-derivation contracts without
  coercing older records into these evidence classes
- Add table-driven offline source staging, quarantine/deduplication, explicit
  digest-bound reviewed admission and five-class quota reporting
- Batch resolution validates the actual input graph once per request; every
  subsequent call revalidates and returned views are detached

`materials_boundaries/data/taxonomy_migration_v1.json` records exact changed
fields and complete retained-object before/after pins. It is not a broad waiver
for arbitrary changes. Existing mineral/rock, processed biopolymer, rubber,
extracted lignin and engineered composite categories remain composition-based.

## Export and replay

Software version advances to 0.35.0. Historical reports retain their recorded
engine version; current strict replay must reject older-version reports. Explicit
regeneration from retained original inputs preserves prior numerical results.
Taxonomy-related categories and classification prose are versioned intentional
output changes. Other previously selected material outputs remain unchanged.
New canonical optional fields are present only for admitted bulk biological
records. JSON stays independent of display language.

## Admission boundary

Only an exact reviewed source package can pass the first registered wood adapter.
The held v1 research package is never admitted. Source-supported candidates and
benchmark-only synthetic rows are not runtime material coverage. Rights,
source-deposited precision, canonical taxon IDs, null specimen conditions and
conversion-derived evidence must survive export. Source caches/PDFs/images are
not bundled.

Final release verification records the actual admitted digest/IDs, full source
and Git manifests, schema/unit/mixed checks, baseline numerical/output recovery,
scale benchmarks and installed offline wheel result. Passing a focused test or
source review alone does not complete release admission or authorize deployment.

## Development-validator diagnostic order

The complete claim-family identity and assumption checks now also run immediately
after the claims schema passes. If both a claim and another catalog are invalid,
claim-local semantics may therefore reject first. The historical later claim
guard remains in place. Every successful call still validates every catalog
schema, source/link relationship and scientific contract against its actual
inputs. This is diagnostic ordering only: no input validation result is cached,
and old valid outputs and numerical values are unchanged.
