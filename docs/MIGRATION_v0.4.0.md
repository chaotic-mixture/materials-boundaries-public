# Migrating v0.3.0 to v0.4.0

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


This is a content-first catalog extension: five model records, six bibliographic source records, and curated display/search names. No strength or fracture evaluator is added. All ten previous claim records and eleven previous source records remain unchanged; the eight existing scientific evaluation payloads and ordering remain unchanged.

| Contract | v0.3.0 | v0.4.0 |
| --- | --- | --- |
| Package / reported engine version | 0.3.0 | 0.4.0 |
| Claims catalog/schema | 1.2.0; 10 records | 1.3.0; 15 records |
| Sources catalog/schema | 1.0.0; 11 records | 1.0.0; 17 records |
| Evaluation schema and scientific payloads | 1.1.0; 8 evaluations | Unchanged |
| Instance schema and examples | Existing composite inputs | Unchanged |
| Locale schema | 1.0.0 | 1.0.0; added labels/names |
| Comparison envelope schema | 1.0.0 | 1.0.0; embedded claims schema/reference updated to 1.3.0 |

The new claim records begin at per-record version 1.0.0. No previous per-record version changes. The evaluator's `engine_version` changes, so its entire JSON envelope is not byte-identical; its eight `evaluations` remain identical on the bundled examples.

## Categories, quantities and parameters

Six K/G `theoretical_bound` records and two E/nu `derived_outer_envelope` records remain executable. Four `model_estimate` records (two earlier Griffith critical stresses, Frenkel shear, UBER cohesive peak) use `direction: prediction`. Three new `model_relation` records (central-crack K_I, Mode-I G–K identity, finite-width geometry factor) use `direction: relation`. All seven model entries are `catalog_only`, have `bound_kind: null`, and have no dependencies on composite-bound results.

`model_relation` means a conditional model identity or documented analytical approximation, not a lower/upper bound or critical failure value. Read the exactness/approximation statement and limits for each record. The finite-width secant factor is explicitly approximate.

New quantities are `ideal_resolved_shear_stress` (Pa), `ideal_normal_cohesive_stress` (Pa), `mode_i_stress_intensity_factor` (`Pa*m^0.5`), `mode_i_energy_release_rate` (`J/m^2`), and `finite_width_geometry_factor` (`1`). New top-level dimensions are `stress_intensity` and `energy_per_area`. Dimensions and unit IDs are not translated. Pressure and dimensionless quantities retain their existing conventions.

The `parameters` object shape is unchanged: symbol, quantity, dimension, SI unit and meaning. The schema now supports each new model family's exact required parameter set and dimension/unit pairs. It preserves the previous E/Gc/a and E/Gc/a/nu Griffith sets and plane-state requirement. Parameter array order is descriptive, not executable argument order; reordering the same required set remains schema-valid. Parameters are **definitions**, not new numerical inputs accepted by `evaluate`. G_slip is slip-specific; W_sep is positive work of separation; UBER lambda/delta are local cohesive variables; a is half-crack length; W is full sheet width. An energy-release identity has no automatic toughness or fracture criterion.

## Search and display

`--claim-type` / Python `claim_type` adds `model_relation`; `--direction` / Python `direction` adds `relation`. Existing choices and AND semantics remain. These additions are canonical case-sensitive codes in all languages.

The five new records have `catalog_name_<claim_id>` entries in the existing en/zh/ja/de locale dictionary. Text output shows the translated display name alongside the original canonical record name. Free-text claim queries also search these authored display names in all four languages as literal case-folded aliases. No locale is selected for the search itself; `--lang` still changes only the presentation. Source titles/DOIs and source search are unchanged. There is no automatic translation, inferred synonym expansion or full-text search. Existing claims without authored names retain their canonical-name behavior.

```python
from materials_boundaries.catalog import query_catalog
relations = query_catalog('claims', claim_type='model_relation', direction='relation')
assert relations['schema_version'] == '1.3.0'
assert len(relations['records']) == 3
assert all(r['evaluation_support'] == 'catalog_only' for r in relations['records'])
assert query_catalog('claims', query='有限宽度')['records'][0]['id'] == 'lefm_center_crack_finite_width_secant_factor'
```

## Visualization and downstream checks

No visualization runtime logic or quantity set changes. The builder joins only the eight fixed evaluator outputs; seven catalog-only models must never be plotted as computed predictions. The exported comparison schema embeds the current claims schema and resolves its new 1.3.0 identifier offline. Regenerate a v0.3.0 comparison export with the installed version rather than relabeling its old metadata; reproducibility validation intentionally checks current engine/catalog data. The checked-in v0.3.0 static overview preview remains a historical illustration of the unchanged elastic calculations, not a v0.4.0 model visualization.

- Accept 15 catalog claims separately from 8 evaluations and 17 source records
- Handle `model_relation` / `relation`, null `bound_kind`, and all four output dimension/unit pairs
- Gate execution on fixed supported evaluator IDs and `evaluation_support`; never execute `formula_display`
- Preserve model-local parameter meanings, UBER energy sign/reference and full/half width/crack conventions
- Keep original titles, DOI, version-specific locators, reading limits and source reuse statements
- Expect new curated-name search matches; filtered JSON remains identical across display languages
- Regenerate comparison exports; do not reinterpret historical previews as additional model computations

The [new content overview](MECHANICS_CATALOG.md) documents derivations, the finite-width source discrepancy and exclusions. Formula checks and software tests are not independent scientific or language review; no universal strength theorem or engineering allowable is introduced.
