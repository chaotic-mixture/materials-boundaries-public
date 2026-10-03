# Migration to v0.22.0

Version **0.22.0** adds six catalog-only PA12 CF15 tensile-test summaries and
one Ciganas et al. (2026) source, together with a closed 3D observation contract
and mixed-family offline inspection. This note does not assert a published tag,
release date, software DOI or successful test run.

## Versions, counts and preservation

| Component | Previous | v0.22.0 |
| --- | --- | --- |
| Software/package/engine | 0.21.0 | 0.22.0 |
| Observation envelope/schema | 1.2.0 | 1.3.0 |
| Observation inspection schema | 1.0.0 | 1.1.0 |
| Observations / studies | 6 / 3 | 12 / 4 |
| Source records | 51 | 52 |

Each new record has version **1.0.0**. Claims schema **1.11.0**, source schema
**1.0.0**, evaluation schema **1.1.0**, computational-prediction contracts and
synthetic-temperature contracts remain unchanged. All six older observation
objects and all 51 older source objects are preserved. The **36 claims,
12 computational predictions, five synthetic temperature models and seven
branches** are unchanged. Exactly the original **eight composite rule pairs**
remain executable, with the original eight-series comparison boundary.
Historical release counts and examples remain historical.

## New family and result units

The six records are `ciganas2026-pa12cf15-uts-23c`, `-40c`, `-60c`, `-80c`,
`-100c` and `-120c` (the same prefix applies to each suffix). Source/study
`ciganas2026polym18050563` supports dataset
`ciganas-2026-pa12-cf15-fff-uts-temperature`, protocol
`ciganas2026-pa12-cf15-quasistatic-tension`, and family
`ciganas_2026_pa12_cf15_fff_tensile_temperature_v1`.

The new exact quantity is `ultimate_tensile_strength_as_reported_3d`, dimension
`pressure`, with `si_unit: Pa` and observation type
`experiment_derived_tensile_test_summary`. Do not route every observation to a
2D indentation renderer or the `experiment_derived_model_dependent` label.
The new type describes table parameters calculated from tensile tests, not raw
force/area measurements or independently verified engineering/true stress.

`reported_result` retains **MPa** numeric fields and exact source strings,
including trailing zeros; `si_result` carries exact integer **Pa** values and
explicit decimal unit-scaling metadata. **1 MPa = 1000000 Pa** adds no measurement
precision or new observation and does not use specimen geometry. Older N/m
records remain N/m; no thickness-based pressure conversion is added. Their
source wording may mention 3D units without making those selected 3D results.

Each temperature remains a reported chamber condition in `degC` (display °C),
not an established direct specimen temperature. Three tensile tests per condition
and SD do not justify a CI or a particular central statistic. Stress convention,
area basis, aggregation, actual moisture and other source gaps remain explicit.
See [the exact six cells and full source contract](PA12_CF15_TEMPERATURE_OBSERVATIONS.md).

## Catalog selection and inspection migration

```sh
python -m materials_boundaries catalog observations --source-id ciganas2026polym18050563 --text --lang en
python -m materials_boundaries catalog observations --quantity ultimate_tensile_strength_as_reported_3d --json
python -m materials_boundaries catalog observations --observation-type experiment_derived_tensile_test_summary --json
python -m materials_boundaries observation inspect --output /tmp/all-observations --lang en
python -m materials_boundaries observation inspect --source-id ciganas2026polym18050563 --output /tmp/pa12-cf15 --lang zh
python -m materials_boundaries observation inspect --id ciganas2026-pa12cf15-uts-60c --output /tmp/pa12-cf15-60c --lang ja
```

Default catalog/inspection now select **12 records**; the new source, quantity
or observation-type catalog filter selects six. Exact selectors retain AND
semantics and packaged source order, including reversed requested IDs. Study
and quantity grouping remain navigation only. Existing 2D quantities and source
filters preserve their scientific results.

**Regenerate saved inspection bundles with the intended selection. Do not edit
schema/software labels on a stale bundle.** Inspection canonical rebuilding
rejects altered/stale facets, snapshots, digests, labels, units, normalization,
source metadata and resolved selection. Digests identify bundled metadata,
not publisher file bytes. Language-independent JSON/CSV and authored en/zh/ja/de
HTML/SVG labels remain distinct; translations are not independently reviewed.

CSV keeps `unit`, `central_value` and `plus_minus_value` as **reported-result
units and values**: N/m for older records, MPa for PA12 CF15. Additive fields
include `si_unit`, `si_central_value`, `si_plus_minus_value`,
`normalization_json`, `reported_value_string`, `reported_plus_minus_string`,
`dataset_id`, `protocol_id`, `source_cell_json` and `temperature_value`, `temperature_value_string`, `temperature_unit`,
`temperature_basis`, `temperature_json` columns. Consumers must select columns by name, not fixed column position or an
assumption that all results use N/m or that `unit == si_unit`. Source strings
preserve formatting; complete JSON snapshots retain all metadata. Missing scalar
values remain literal `null`, never zero. Identity, temperature basis and caveats
precede property-value columns. Older records' SI columns use unchanged N/m
values and explicit identity normalization.

Every PA12 text/card view shows material/protocol, chamber basis, preparation,
unknown stress/statistic, scoped count and SD limitations before its MPa/Pa
property values. No quantitative temperature plot, fit, interpolation, SD
endpoints, ranking, comparison to 2D membrane values, evaluator or new synthetic
model is introduced. Invalid input is rejected before output writes; a valid
write's disk/permission failure does not have transactional rollback guarantees.

## Closed dataset versus existing appendability

The new schema/runtime contract binds exactly six Table 3 cells to their source,
protocol and complete scientific metadata. Subsets and renamed record identities
are valid when the payload is unchanged; presentation is record-ID agnostic.
Full-catalog validation requires all six cells in source-column order and rejects duplicate
`(dataset_id, quantity, source_cell)` aliases even with different record IDs.
An alias does not create independent evidence. Additional temperatures, protocols,
materials, stress definitions or metadata changes require reviewed admission.

This dataset-specific closure does **not** revoke appendability under existing
supported scientific contracts. Preserve those regressions and historical
scientific fixtures. Change only deliberate version/envelope/CSV assertions;
never regenerate old science or remove a guard to make a new family pass.
The new source-specific runtime guard also checks bibliography, inspected version,
PDF noninspection, revision discrepancy and rights on source reads/rendering.
Generic source-schema validity alone does not establish those semantics.

## Source and release checks

The publisher HTML was inspected on 3 October 2026, with reported update
3 September 2026 02:53 CEST. The PDF upload metadata is retained but **the PDF
was not inspected**. A cached/live discrepancy in unselected Table 4 is recorded;
only selected Table 3 cells have current-HTML/visual/second-transcription
agreement. No blanket artifact-equivalence claim or raw-data reproduction is made.
The article's own copyright block verifies CC BY 4.0; author/title/DOI attribution
and reorganization/unit-re-expression notices remain. Manufacturer Table 1 is
excluded. No publisher assets, full text or raw measurement collection is shipped.

Required release checks (record their actual outcomes separately):

- Release-metadata preflight, full catalog validator and complete unit suite
- Exact six-cell/source facts, decimal Pa scaling, all nulls and negative
  schema/runtime mutations; complete-dataset versus subset/alias behavior
- Old observation/source object identity, existing-family appendability,
  unchanged claims/predictions/synthetic catalogs and eight-rule behavior
- Default/new-only/old-only/mixed/single-condition selection in all four locales;
  deterministic JSON/CSV, tamper rejection and invalid-input no-write behavior
- Per-card caveat-before-value ordering, text-only wide/narrow SVG pixel review,
  plus separate browser HTML reflow at desktop and narrow mobile widths
- Wheel metadata and isolated installed-wheel smoke outside the checkout, with
  no runtime/development dependencies; source-asset/excluded-data inspection
- CI on Python 3.11 and 3.12 for the exact published commit before declaring
  publication checks complete

```sh
python -m unittest discover -s tests -p test_release_metadata.py -v
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
python -m pip wheel --no-deps --wheel-dir dist .
python scripts/check_wheel_metadata.py dist/materials_boundaries-0.22.0-py3-none-any.whl
```

Source checks and software validation do not establish independent scientific
review, replication, native-language review or legal clearance.
[Inspection guide](OBSERVATION_INSPECTION.md) · [Sources](SOURCES.md) ·
[Third-party notices](../THIRD_PARTY_NOTICES.md).
