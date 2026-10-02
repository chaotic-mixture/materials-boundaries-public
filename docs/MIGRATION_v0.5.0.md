# v0.5.0 migration: catalog-only elastic stability

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


## Preserved contracts

- The original 15 claims and 17 sources are unchanged; four stability claims and one primary source are appended, for totals of 19 and 18
- The fixed composite evaluator still returns the same eight numerical evaluations under evaluation schema 1.1.0. All four bundled input fixtures give identical payloads apart from `engine_version: 0.5.0`
- Instance schema 1.0.0, source schema 1.0.0 and comparison schema 1.0.0 retain their identities. The comparison schema embeds the current claims schema snapshot, but each comparison still selects only eight executable claims
- No stability computation, stiffness input, strength assessment, phonon calculation or new plotted series is added

## Claims schema 1.4.0

Consumers must recognize the new `claim_type: stability_criterion` and `direction: constraint`. They are distinct from upper/lower bounds, estimates and model relations. The quantity is `homogeneous_elastic_stability`, its `quantity_dimension` is `logical_predicate`, and its `si_unit` is **null because no physical output unit applies**, not because an unknown numeric unit should be filled in. The required `bound_kind` remains null and `dependencies` stays empty. All four records are `catalog_only`.

Each stiffness parameter has pressure dimension and SI unit Pa; the parameter array grows to a maximum of nine entries to support the orthorhombic family. Every existing model family retains its exact parameter signature. The new family validates exact symbols, quantity roles, units and symmetry assumptions.

New `criterion` metadata records:

- Engineering-Voigt index order, strain/stress vectors, constitutive relation and energy density
- Symbolic 6×6 stiffness matrix, explicitly symmetric with the matching reduced-template couplings
- `combination: all` and `strict_boundary: equality_does_not_satisfy_strict_stability`
- Inequalities with `expression`, `operator: >`, `rhs: 0`, `dimension`, `si_unit`; margins use pressure/pressure_squared/pressure_cubed and Pa/Pa^2/Pa^3

These are display-only records, not expression-language inputs or callable rules. Matrix layout has physical meaning, while parameter and inequality ordering is not an executable argument order. The schema rejects missing/duplicate/wrong parameters, weakened comparison signs, dropped inequalities, incorrect symmetry matrices, incompatible units, runtime-output fields and reclassification as executable bounds. It does not prove that a real specimen satisfies the premises, inspect uncertainty or provide numerical stability states.

Only stability records may carry `criterion`; earlier bounds and models cannot acquire the field. `rule_id` remains a catalog identifier and is not an execution promise. Null output units render as localized “not applicable”; the full matrix, conventions, strict inequalities and a criterion-specific warning appear in `--text` output.

## Reader checklist

- Accept claims envelope schema 1.4.0 rather than assuming 1.3.0
- Do not assume every claim is a scalar numeric quantity, every SI unit is a string, or `direction` means a bound direction
- Preserve pressure-powered inequality units and distinguish them from the unitless logical predicate
- Keep exact source/version/read/license metadata, strict positivity, all-condition conjunction, stress-free harmonic scope, symmetry axes and engineering shear factors
- A zero inequality does not automatically mean a marginal positive-semidefinite matrix; indefinite cases may also contain equalities. No automatic tolerance or higher-order conclusion is supplied
- Do not send these records to the existing `evaluate()` API or fabricate plotted results from catalog metadata
- Four-language label/query support is presentation only; it does not translate or execute canonical formulas

Read [scientific definitions and limits](ELASTIC_STABILITY.md), [catalog API](CATALOG.md) and [source ledger](SOURCES.md). Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md).
