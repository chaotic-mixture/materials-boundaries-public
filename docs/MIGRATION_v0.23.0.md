# Migration to v0.23.0

Version **0.23.0** adds the separate, explicitly selected
`observation plot-temperature` route for one closed PA12 CF15 dataset. It is a
descriptive transcription of six source-reported condition summaries, not a
material model, scientific validation or newly admitted observation. This note
does not assert a published tag, release date, successful tests or remote CI.

## Versions and unchanged science

| Component | Previous | v0.23.0 |
| --- | --- | --- |
| Software/package/engine | 0.22.0 | 0.23.0 |
| Observation temperature plot schema | absent | 1.0.0 |
| Observation catalog schema | 1.3.0 | 1.3.0 |
| Observation inspection schema | 1.1.0 | 1.1.0 |
| Observations / studies / sources | 12 / 4 / 52 | 12 / 4 / 52 |

The **36 claims, 12 computational predictions, five synthetic temperature models,
seven branches and eight executable composite rules** are unchanged. Claims,
sources, evaluation, prediction and synthetic-temperature scientific schemas do
not change. All observation/source scientific objects, including all six older
2D records, remain unchanged and observations stay `catalog_only`.

`observation inspect` retains its selectors, packaged-catalog-ordered text-only cards,
1.1.0 schema and policy (`purpose=inspection_only`,
`quantitative_axes_allowed=false`, `uncertainty_endpoints_calculated=false`).
Its broad no-axes/no-whiskers statements describe that inspection route; they do
not forbid the new separately admitted dataset-specific display. Saved bundles
whose software envelope is stale must be regenerated from current catalogs,
not repaired by editing version labels. Historical examples remain historical.

## Explicit new route

```sh
python -m materials_boundaries observation plot-temperature \
  --dataset-id ciganas-2026-pa12-cf15-fff-uts-temperature \
  --output /tmp/pa12-temperature-plot --lang en
```

`--dataset-id` and `--output` are required, with exactly the ID above supported.
There is no default-all, arbitrary record/pressure-shaped input, subset, grouping,
SD-hiding or user-axis-limits option. Languages en/zh/ja/de retain final-occurrence
CLI precedence. Existing inspection filters and `inspect --id` remain separate.
Files use `observation-temperature-plot` rather than `observation-inspection`:
JSON, CSV, locale-specific 1100 px SVG, 380 px narrow SVG and responsive HTML.

The fixed source-unit axes preserve unequal numeric temperature spacing, with
six unconnected, equally styled central-value dots and visible capped ±SD
whiskers. Centers are not called means. Three tests per condition do not prove
replicate independence or justify SEM/CI, observed min–max, hard bounds, coverage
or material allowables. Chamber conditions are not direct specimen temperatures;
no x whisker means unreported uncertainty, not zero. The fixed 15–125 °C and
0–55 MPa domains are display padding/baseline, not validated material limits.
Exact source strings, including trailing zeros, remain in the table; Pa is exact
unit-re-expression metadata only. The compact SVG keeps all six essential scope
warnings, the adjacent legend, exact source table/record IDs, a shared protocol,
geometry and unknowns summary, DOI/exact Table 3 locators, and revision/rights
attribution. Complete metadata dictionaries, repeated per-record provenance and
six exact SI value/SD pairs remain lossless in unchanged canonical JSON/CSV and
inert expandable HTML details. Essential interpretation warnings are never
hidden there. This layout reduction changes no scientific data, schema, guard
or audit export. [Complete contract and API](OBSERVATION_TEMPERATURE_PLOT.md).

## Canonical validation and exports

The single group is closed to the six Table 3 UTS/SD cells in the reviewed
source-reported shared protocol. Source-cell identity supports unchanged-payload
ID/name renames. Reordered packaged records are restored to Table 3 order;
reordering canonical bundle glyphs is tampering. This ordering-only completeness
change admits a complete source-cell set while preserving generic inspection
order; it changes no scientific payload, cell count or duplicate guard. Missing/duplicate/extra cells,
unreviewed temperatures, new groups and scientific/source mutations are rejected.
Equal units, nulls, a paper name or a common object shape are insufficient admission.

Every new serializer/renderer rebuilds against current catalogs, the actual
referenced source and fixed policy, comparing the complete canonical JSON.
Snapshot hashes alone cannot authorize edits. Extra fields, stale versions,
changed warnings/domains/glyph endpoints and non-JSON or nonfinite values fail
closed. Derived endpoints are local decimal rendering arithmetic, not new
observations or a new material-model rule. Metadata hashes are not publisher
artifact byte hashes. JSON/CSV are deterministic and locale-independent.

CSV uses fixed documented columns and one full observation per row; read columns
by name. Scalar unknowns are literal `null`; full snapshots preserve JSON types.
Import source, ID and JSON columns as **text**, since formula-like prefixes are
preserved unmodified and CSV quoting does not ensure safe spreadsheet execution.
All artifacts are built and validated in memory before targets are created.
Invalid requests must leave output unchanged; a later disk/permission failure
during a valid write has **no all-file atomic rollback guarantee**.

## Evidence, rights and acceptance checks

The inspected HTML update/access metadata, PDF noninspection and discrepancy in
unselected Table 4 remain unchanged. Only selected Table 3 cells have
HTML/visual/second-transcription agreement. Preserve author/title/DOI attribution,
article CC BY 4.0, and the adaptation notice for discrete plotting, unit
re-expression and original curation. No source assets, manufacturer Table 1,
excluded data or raw measurements are added. Machine-assisted locale checks
are not independent scientific or native-language review. Browser QA remains
unverified; static SVG review and HTML structure tests do not establish it.

Release acceptance requires actual outcomes, separately recorded, for:

- Existing full suite, release-metadata and catalog/schema checks, retaining
  historical scientific fixtures and records; the ordering-only regression
  assertion is updated from rejecting to accepting a complete packaged permutation
- Closed-group positive/negative tests, source strings/unknowns/rights preservation,
  deterministic locale-independent exports, tamper rejection and no-write preflight
- Decimal-context isolation, numeric transforms, six center/whisker glyphs,
  warnings-before-values, safe text/URLs and width/language/selector validation
- All four locale wide/narrow SVG static pixel checks, including 320 px minimum
  width; browser layout QA explicitly reported as unverified if not performed
- Regenerated new deterministic examples and an isolated installed-wheel smoke
  outside the checkout; package-data, metadata, no-runtime-dependency and exclusion
  checks
- Python 3.11/3.12 remote CI for the exact approved published commit, only after
  explicit publication approval

[Scientific evidence](PA12_CF15_TEMPERATURE_OBSERVATIONS.md) ·
[Inspection contract](OBSERVATION_INSPECTION.md) ·
[Third-party notices](../THIRD_PARTY_NOTICES.md).
