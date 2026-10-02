# Migration to v0.12.0

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


- Adds a separate computational-prediction catalog/schema 1.0.0, one reusable
  closed reported-method family, three records and one explicit comparison group
- Adds one source, preserving every existing scientific record; totals are
  30 claims, 35 sources, 2 observations, 2 temperature models and 3 computational
  predictions. Counts are release summaries, not appendability constraints
- Adds `catalog predictions` and `prediction plot`, four-language names/help,
  deterministic JSON/CSV and static SVG/HTML exports
- Claims schema remains 1.8.0; the eight composite rules, their formulas,
  numeric results and conditions, and temperature fits are unchanged. Only
  software-version output labels advance to 0.12.0; temperature evaluation IDs
  also change because their content hashes include that version
- Candidate validator directories also need `computational_predictions.json`
  and `prediction_locales.json`. The full dev extra is still required
- Rebuild old generated export bundles after updating; runtime canonical checks
  intentionally reject stale snapshots rather than rewriting provenance

See [the full scientific and CLI contract](COMPUTATIONAL_PREDICTIONS.md).
