# Migration to v0.31.0

This additive source-reference release adds six identities and six selected
properties. It adds no evaluator, physical model, automatic calculator input,
unit conversion, fit, ranking or universal material bound. The existing material
and reference-property envelope schema versions remain **1.0.0**; upgrade the
runtime, generated reference schema and four-language locale labels together.

## Generic metadata changes

`uncertainty` is a closed union of `reported_standard_deviation`,
`reported_confidence_interval` and `reported_plus_minus_unspecified`.
`uncertainty_status` must exactly match any non-null uncertainty type.
All amplitudes are source-preserved nonnegative decimal strings in exactly the
central result's unit. Non-null uncertainty requires a scalar central result.

The SD branch is unchanged and requires explicit mean evidence. CI and undefined
± do not require means. CI adds a known percent confidence-level object with
`value_text`, exact decimal-string `number`, and `unit_code: percent`, plus
`estimand` and `construction` fact objects. Unknown CI estimand/construction must
carry explanatory notes. Coverage factors remain null, and undefined ± cannot
carry confidence metadata. No SD, SE, confidence endpoints or distribution is
calculated. The complete source expression remains in `uncertainty_note`.

`method_definition.extraction_window` now accepts an evidence-backed reported
fact or null. Its source wording and percent units are not parsed into a fitting
procedure. Existing fact fields retain normalization/correction scopes and their
unknowns. Generic text output dispatches by uncertainty type in en/zh/ja/de;
it shows CI level, estimand/construction unknowns and type-appropriate notices.
Original source-language qualification text remains canonical across locales.
Machine-assisted labels are not native-language or scientific validation.

## Source-specific interpretation

- T700S: 249.8300317 GPa is one individual filament's reported modulus, n=1,
  linked from the dataset to its methods article; not the 217-row mean
- Basalt: 56.1 ± 11.5 GPa is reported mean ± SD; successful retained n is
  unknown despite twenty prepared/tested filaments
- Sylgard 184: 2.05 ± 0.12 MPa has reported 95% CI, unspecified estimand and
  construction, six test samples and source-applied geometry correction
- The three rubber mass-density ± amplitudes retain unspecified statistical
  meaning and unspecified central aggregation; no SD or mean is invented

See [complete selected scopes, rights and holds](MATERIAL_COVERAGE_v0.31.0.md).
The prior 28 material records, eight-rule engine, old science, fixtures and
examples remain intact. New source facts are catalog-only, not engineering
allowables, independent scientific review or raw-data reanalysis. No publication
PDF, screenshot, full table or source dataset is redistributed.

Fresh evaluations/reports identify package version **0.31.0**. Strict replay
requires its matching software/catalog snapshot; regenerate an older report
explicitly from retained inputs when necessary. Historical outputs are not
rewritten. Full production and disposable mixed-append suites, installed-wheel
four-language checks, source readback and old-output parity must pass against
an exact frozen candidate before release admission.
