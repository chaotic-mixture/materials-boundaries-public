# Development history: v0.14.0

This was not a public release. The first public release is **0.16.0**; its
[scope](MIGRATION_v0.16.0.md) and [license notices](../THIRD_PARTY_NOTICES.md)
are authoritative for the public package.

This development milestone expanded model-specific four-language presentation
and generalized branch/overlap handling in the separate temperature evaluator.
The first public release retains those software capabilities with five original
synthetic demonstrations and seven artificial branches. The earlier NIST
coefficient datasets and their derived results are omitted, including in this
history. See [the current temperature contract](TEMPERATURE_MODELS.md).

## Public migration checklist

- Select current `synthetic_*_temperature` IDs; no former real-material model ID
  is silently remapped to invented data
- Use the `synthetic-*.json` input files in `examples/temperature/`
- Preserve all overlapping branch predictions, nonmonotonic polynomials and
  out-of-range non-predictions; never average, select or extrapolate
- Keep synthetic identity, null measurement/data-range fields, no claimed fit
  error and original author provenance visible in all four languages
- Regenerate both example plot directories from public models; do not copy
  earlier provenance snapshots, fixtures or derived values into public output
- Keep canonical data language-independent and validate presentation snapshots
  against the selected models; defaults select the current catalog

NIST bibliographic references remain. Omission of coefficients is conservative
pending clarification, not proof that redistribution is prohibited. The
collection is currently listed by NIST as curated, formerly SRD 152; no express
redistribution grant was verified. [Official evidence and license scope](../THIRD_PARTY_NOTICES.md)
