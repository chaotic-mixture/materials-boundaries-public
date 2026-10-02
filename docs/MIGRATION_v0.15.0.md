# Migration to v0.15.0

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


This is a bounded catalog-only expansion: exactly two directional Poisson-ratio
`model_relation` claims and three genuinely new primary sources. Existing
scientific records, source rights metadata, eight executable composite rules,
observations, temperature quartics and computational predictions are preserved.
Current totals are 32 mechanics claims, 44 sources, 2 observations, 5 temperature
models / 7 branches, and 6 computational predictions. Counts describe this release
and do not impose a catalog growth limit.

## New scientific contract

- `directional_poissons_ratio_definition_and_range` defines ν(n,m) under uniaxial
  stress along unit n with unit m perpendicular to n. Across finite real full-SPD
  3D elasticity tensors, every finite real value is possible. Each fixed tensor
  still has finite attained minimum and maximum over direction pairs
- `directional_poisson_reciprocity_energy_constraint` records
  ν(n,m)/E(n)=ν(m,n)/E(m), |ν(n,m)|<sqrt(E(n)/E(m)) and
  0≤ν(n,m)ν(m,n)<1. These are necessary pair conditions, not a sufficient full-SPD
  stability test; the zero product is attained when both ratios vanish

The dedicated dimensionless quantity `directional_poissons_ratio` and closed
`directional_contract` do not reuse isotropic `effective_poissons_ratio` or the
anisotropy `index_range`. Unboundedness over a material class does not mean an
unknown endpoint or attained infinity. All assumptions require a stress-free,
infinitesimal, real classical elastic setting and the full inverse compliance.
Engineering S44=4S2323; raw tensor shear entries cannot be substituted unchanged.
No tensor input, inversion service, extremum solver, specimen prediction or plot
is added. The existing isotropic interval −1<ν<1/2 remains unchanged.

## Versions, guards and compatibility

- Software/package/engine version becomes 0.15.0; claims schema becomes 1.9.0
- The comparison schema's embedded claims schema and its exact reference both
  advance to 1.9.0. Other scientific schema versions remain unchanged
- Current comparisons require the current claims snapshot; regenerate old bundles
  before validating them with this release. Engine-labeled result IDs also change
- Dependency-free runtime checks on reading/rendering directional records enforce
  the exact metadata, finite JSON and dependency-family meaning. Public schema
  checks alone do not resolve cross-record references. Full development validation
  also preserves the exact executable registry and complete locale labels
- Fresh IDs can reuse either exact directional family. Paired claims resolve their
  definition dependency by stable ID, even after catalog reordering. New scientific
  scope still requires reviewed schema/guard work
- Historical scientific tests use stable IDs. Prior assertions update the current
  claims-schema version and compare executable records by ID rather than catalog
  position; the exact eight-rule registry is still enforced. No old scientific
  fixture is rewritten. Dependency assertions are pinned to each known rule
  family; new same-family directional IDs are checked by family and stable ID.
  A separate, explicit before/after test-hash ledger records reviewed updates
- Four-language names, conditions and limitations accompany original project
  proofs. Tests cover exact rational algebra, endpoints, shear scaling, strictness,
  attribution, unsafe metadata mutations, appendability and unchanged calculations

## Evidence and reuse limits

Norris's general definition pages and cubic equation pages were visually checked.
Ting–Chen supports two-sided unboundedness through its inspected publisher
abstract only; its full proof was not inspected. The complete q-family, strict
Cauchy–Schwarz argument and compactness proof are explicitly original project
algebra, not attributed to numbered paper equations or independent peer review.
Lempriere is historical attribution through Norris, not a separately inspected
original source. Native-speaker translation review is not claimed.

Only bibliographic facts, formulas and original curation notes are included.
Source PDFs, extracted article text and figures remain outside the repository.
For the first public release, original project code, documentation and curation
use MIT; this does not grant rights over third-party sources. NIST cryogenic
coefficients are omitted conservatively pending clarification; see [the current
notices](../THIRD_PARTY_NOTICES.md).

See [the directional scientific guide](DIRECTIONAL_POISSON.md) for the complete
proofs, source locators, exclusions and four-language summaries.
