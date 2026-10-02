# Migration to v0.11.0

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


- Package/engine 0.10.0 → 0.11.0; claims schema 1.7.0 → 1.8.0
- Add two catalog-only dimensionless elastic anisotropy definitions under existing
  `model_relation` / `relation`: cubic Zener A and universal AU
- Add four source records; preserve all 28 prior claims, 30 prior sources, both
  observations and both isolated temperature models
- `index_range` explicitly separates the definition from its scoped mathematical
  range. Zener lower zero is open; AU lower zero is closed. Both upper endpoints
  are explicitly unbounded over their tensor class, not unknown or nonfinite JSON
- New closed families require strict finite real 3D positive-definite elasticity,
  exact component/averaging conventions and complete parameter contracts
- Sources and observations retain schema 1.0.0; temperature schemas stay 1.0.0;
  composite evaluation remains 1.1.0; comparison remains 1.0.0 with embedded
  claims schema 1.8.0
- Exactly eight composite executable pairs remain. No anisotropy solver, tensor
  input schema, specimen applicability assessment or automatic plot is added
- Regenerate new comparison bundles from valid inputs. Do not relabel old
  bundles; historical visualization artifacts remain historical
- Only live claims-schema version assertions advance in existing tests. All
  scientific assertions, source provenance, arithmetic and prior outputs remain
  intact. Fresh same-family append tests use the unmodified complete suite

See [scientific conditions, derivations and source QA](ELASTIC_ANISOTROPY.md),
[contribution rules](../CONTRIBUTING.md) and [catalog usage](CATALOG.md).

The development validator also uses a bounded, process-local cache for successful
schema meta-validation, keyed by exact canonical schema content under unchanged
inspectable validation settings. Unsupported or changed settings use uncached
checking. Strict schema/catalog loading, required format-checker availability,
offline registries and instance validators remain fresh on every call; failures
are never cached. No installed runtime behavior or scientific outputs change.
