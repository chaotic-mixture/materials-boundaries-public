# v0.7.0 migration: separate observational context

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


## Preserved contracts

- All **22 claim records are unchanged**; claims schema remains **1.5.0**
- The original **19 source records are unchanged**; one new source gives **20 sources**, still under source schema **1.0.0**
- A new, separate **observation schema 1.0.0** contains **two records from one Lee–Wei–Kysar–Hone (2008) study**
- The composite evaluator still produces the original **eight evaluations**, with the same values, order, conditions and evidence. The intended evaluation-payload change is only `engine_version: 0.7.0`
- Instance schema 1.0.0, evaluation schema 1.1.0, comparison schema 1.0.0 and locale schema 1.0.0 are unchanged
- No observation execution, thickness conversion, new composite input, numerical strength API or observation overlay is introduced. Historical migration documents retain their original release counts and versions

## New catalog and fields

The new file is `materials_boundaries/data/observations.json`, exported under `schemas/observations.schema.json` with identifier `urn:materials-boundaries:schema:observations:1.0.0`. It uses the existing `{schema_version, records}` envelope but a distinct record contract, rather than extending the claims enum with a measurement type.

Each observation retains a stable `id`, `name`, `version`, shared `study_id`, `observation_type`, `quantity`, dimension, SI unit and `catalog_only` support. Material context, `reported_result` and its uncertainty notation, method/assumptions, conditions, sample metadata, verification gaps, source locators and limits stay attached. A null condition means unverified, not a default experimental setting.

The new IDs are `lee_2008_graphene_in_plane_stiffness_2d` and `lee_2008_graphene_breaking_strength_2d`. Both use `study_id` and source ID `lee_wei_kysar_hone_2008`, and `observation_type: experiment_derived_model_dependent`. Their distinct quantities are `in_plane_stiffness_2d` and `breaking_strength_2d`, both `force_per_length` in `N/m`.

## Query migration

```sh
python -m materials_boundaries catalog observations --source-id lee_wei_kysar_hone_2008 --json
python -m materials_boundaries catalog observations --quantity in_plane_stiffness_2d --text --lang en
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query graphene --text --lang ja
```

- `catalog observations` is additive; existing `catalog claims` and `catalog sources` retain their meanings and default JSON behavior
- `--id` and `--query` work for every catalog; `--source-id` works for claims and observations
- New `--quantity` and `--observation-type` are observation-only. The supported type is `experiment_derived_model_dependent`; unknown nonempty quantities simply match no records
- Python `query_catalog("observations", quantity=..., observation_type=..., source_id=...)` uses the same keyword-only filters
- Unsupported catalog/filter combinations are usage errors (CLI exit 2; Python `ValueError`), not silently ignored filters
- Exact structured filters are case-sensitive and AND-combined. Literal all-term query behavior and original catalog order are unchanged; an empty result succeeds
- Observation query fields are ID, name, quantity, observation type, study ID, material name, evidence source IDs and authored en/zh/ja/de display-name aliases. `--lang` changes presentation, never the match set or canonical JSON

## Scientific reader checklist

- Preserve the source-reported **340 ± 50 N/m** stiffness and **42 ± 4 N/m** model-inferred breaking strength as different quantities, not universal bounds or engineering allowables
- Preserve `reported_plus_minus_unspecified`: neither ± value has a verified type, confidence level or coverage factor. Do not convert it to SD, confidence bands or bound endpoints
- Keep the separate stiffness distribution **mean 342 N/m, SD 30 N/m, 67 fits, 23 membranes, 2 flakes** distinct from the reported stiffness summary. Never use those counts as breaking-test sample sizes
- Retain AFM indentation/membrane-model assumptions and assumed ν = 0.165. Breaking strength depends on the nonlinear/finite-element inference using second Piola–Kirchhoff stress and Lagrangian strain, not a directly measured uniform tensile stress
- Keep temperature, atmosphere, humidity and loading rate unknown; the inaccessible supplement was not read
- Keep canonical N/m and no default thickness or GPa conversion. Equal dimensions alone do not justify property comparisons
- Group by the shared study ID before counting independent studies: two records do not mean two confirmations
- Preserve passage-inspection status and absent independent scientific/translation review. ©2008 AAAS, all rights reserved; no paper, PDF, figures or raw data are bundled

## Comparison exports

Observation records are not instances or comparison series. The existing comparison bundle continues to contain only the eight executable composite claims and their evidence; no graphene observation overlay is accepted. Its claims/source schema snapshots retain their existing versions.

Regenerate old comparison bundles from their retained valid composite inputs using engine 0.7.0. Fail-closed validation checks the engine/catalog payload; changing a version label alone is not a migration. The numeric curves remain unchanged for the same valid inputs.

See [observations and evidence](OBSERVATIONS.md), [catalog reference](CATALOG.md), [model scope](MODEL.md), [source rights](SOURCES.md) and [visualization](VISUALIZATION.md). Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md).
