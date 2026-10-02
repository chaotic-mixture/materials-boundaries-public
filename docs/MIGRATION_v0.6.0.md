# v0.6.0 migration: catalog-only porous bounds

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


## Preserved contracts

- The original 19 claim records and 18 source records are preserved exactly. Three porous claims and one metadata-only source are appended, for totals of **22 claims and 19 sources**
- The fixed composite evaluator still returns its original eight evaluations with the same numbers, ordering, conditions and source evidence. The only intended evaluation-payload change is `engine_version: 0.6.0`
- Instance schema 1.0.0, evaluation schema 1.1.0, source schema 1.0.0 and comparison schema 1.0.0 retain their existing identifiers
- The comparison schema embeds the updated claims-schema snapshot for offline validation, while comparison bundles still select only the eight executable composite claims
- No new numerical rule, public runtime API, porosity/density input contract, applicability checker or chart is introduced. Active zero-stiffness phases remain outside the positive-phase evaluator
- Historical migration documents retain the counts and versions of their own releases

## Claims schema 1.5.0

The claims catalog and exported claims schema move from 1.4.0 to **1.5.0**, with identifier `urn:materials-boundaries:schema:claims:1.5.0`. The new records reuse existing claim-type and direction values:

| Claim | `claim_type` | `bound_kind` | `evaluation_support` |
| --- | --- | --- | --- |
| `hs_porous_bulk_3d_solid_void` | `theoretical_bound` | `scalar_modulus_bound` | `catalog_only` |
| `hs_porous_shear_3d_solid_void` | `theoretical_bound` | `scalar_modulus_bound` | `catalog_only` |
| `hs_porous_youngs_outer_3d_solid_void` | `derived_outer_envelope` | `derived_outer_envelope` | `catalog_only` |

All three have `direction: interval`, pressure dimension and SI unit Pa. Their parameter signatures use positive solid `Ks,Gs` in Pa and dimensionless void fraction `p` in unit `1`. The Young record depends on the two new porous K/G records, not the executable positive-phase claims. Their family contracts preserve the explicit solid/void, traction-free, geometry-unrestricted and isotropic-regularization assumptions. A schema-valid record describes scientific scope; it does not prove that a particular material satisfies it.

Do not infer executable support from `theoretical_bound`, `derived_outer_envelope`, an interval direction, a pressure unit or a `rule_id`. Those fields are now shared by executable and catalog-only records. Read `evaluation_support` explicitly. In particular, `--claim-type derived_outer_envelope` now returns three records, and `--claim-type theoretical_bound` returns eight; neither filter is an executable-registry query.

## Reader checklist

- Accept claims envelope schema 1.5.0; do not change the unrelated schema identifiers
- Keep original claim/source IDs, versions and content stable; retain the eight-entry numerical output contract
- Preserve `p = void fraction`, while the Roberts–Garboczi equation uses solid fraction `1-p`
- For `0<p<1`, keep zero lower endpoints because arbitrary geometry includes disconnected solid; at `p=0`, collapse to the positive solid values instead
- At `p=1`, use the formal empty-stiffness endpoint only, with no Poisson ratio or specific moduli. Do not evaluate an undefined `0/0`
- Retain the isotropy-preserving vanishing-positive-stiffness argument rather than directly substituting zero into singular positive-phase terms
- Keep the full finite-porosity formulas. Low-density first-order asymptotes are not substitute finite-density upper bounds
- Treat `rho_eff=(1-p)rho_s` as conditional on a fixed solid and massless void; do not apply it when composition or pore contents change
- Preserve the Young record's conservative-outer-envelope meaning and the absence of a joint K/G attainment promise
- Treat the new synthetic JSON as documentation only, not an instance or comparison input

Four-language curated display names and literal aliases are added for the three records; identifiers, formulas, units, source titles and DOI stay canonical. There are now twelve such aliases per language across the v0.4.0–v0.6.0 additions. Search remains read-only and independent of the selected display language. Translation and independent scientific review remain pending.

## Provenance and comparison exports

The additional source is `roberts_garboczi_2002_porous`, with exact equation/page locators and an explicit solid-fraction conversion. Its NIST cover and printed journal copyright notices differ; no blanket reuse permission is assumed. Existing source records remain unchanged; the additional Kochmann–Milton page inspection is documented in the new scientific guide. No paper, PDF, figure or material dataset is added.

Regenerate older comparison exports from their retained valid composite inputs with the installed version. Fail-closed comparison validation checks engine/catalog metadata; changing a version label alone is not a valid migration. The documentation-only porous sample must not be passed to the demo generator or represented as an engine-generated porous chart.

See [porous formulas, assumptions and evidence](POROUS_BOUNDS.md), [catalog reference](CATALOG.md), [sources](SOURCES.md) and [visualization](VISUALIZATION.md). Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md).
