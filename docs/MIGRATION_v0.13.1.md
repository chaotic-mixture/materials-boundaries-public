# Migration to v0.13.1

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


- One literal in `materials_boundaries/_version.py` now supplies package, build
  and engine release metadata. Source checkouts and installed wheels keep the
  same dependency-free runtime behavior
- Adds a standard-library metadata preflight before expensive CI validation,
  plus a separate clean installed-wheel smoke check
- Keeps published JSON schemas static and checks exact embedded comparison
  snapshots and references; scientific schema/record versions do not track the
  package version
- Preserves all v0.13.0 scientific data, equations, conditions, numerical values,
  four-language labels and historical scientific/output fixture hashes. The
  existing reviewed-test-update ledger records the expanded release metadata
  test without replacing its original historical hash. Current engine labels advance
  to 0.13.1; temperature result IDs derived from version-bearing output change
- No scientific data or schema migration is required
