# Migration to v0.13.0

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


- Adds the closed computational-prediction family
  `dubois_2006_si_uniaxial_deformation_v1`, quantity
  `tensile_first_instability_strength`, three Si records and the explicit
  `dubois_2006_si_directional_instability` comparison group
- Adds one source. Release totals are 30 claims, 36 sources, 2 observations,
  2 temperature models and 6 computational predictions. Counts summarize this
  release; they are not fixed limits on future supported contributions
- Records `dubois2006_si_100_uniaxial_deformation`,
  `dubois2006_si_110_uniaxial_deformation` and
  `dubois2006_si_111_uniaxial_deformation` preserve Table II stresses of
  27.8, 22.6 and 20.7 GPa and separate critical engineering strains of
  31%, 25% and 19%, respectively
- Defines the new strength as stress at the first detected instability, under
  fixed transverse strain with internally relaxed atomic positions. Table III
  supplies the matching tensile elastic modes; Figure 2(b) is qualitative peak
  support only. The two-atom primitive cell is reported; diamond-cubic is
  explicitly inferred
- Advances the prediction catalog envelope/schema to 1.1.0; individual record
  and protocol versions remain 1.0.0. Existing Ni comparison bundles remain
  1.0.0; new Si comparison bundles use 1.1.0
- Uses closed family-specific schema alternatives and guards. Do not migrate
  the Ni records into the Si family or replace their shared protocol. A new
  physical contract still requires reviewed schema/guard work
- Preserves the prior Ni records, protocol and default plot group. Tensile and
  shear predictions never join automatically; request the Si group explicitly
- Adds the typed `critical_engineering_strain` field with quantity
  `critical_engineering_strain_at_first_instability`, dimensionless `value`
  0.31/0.25/0.19, `unit: "1"`, percent source strings `"31"`/`"25"`/`"19"`,
  `source_unit: "%"`, zero reported decimal places, null uncertainty and its
  own evidence. It stays separate from stress in records, tables and CSV. Plots retain discrete direction categories and
  a GPa strength axis, with no stress–strain curve or error bars
- Preserves null physical temperature, scalar pressure, magnetic state and
  uncertainty/error fields. The source's less-than-approximately 0.05 GPa
  numerical stress estimate is metadata about selected numerical controls,
  never total uncertainty
- Adds four-language names and explanations while keeping canonical identifiers
  and JSON language-independent. Scientific and native-language review remain
  pending
- Preserves existing scientific catalogs and all eight composite calculations
  and temperature-fit equations, values and conditions. Current software-version
  labels advance; identifiers derived from version-bearing output may change
- Candidate data directories continue to include all prior catalog and locale
  files, including `computational_predictions.json` and
  `prediction_locales.json`. The complete developer checks remain required
- Replaces four historical Ni test fixture-position selectors with stable IDs,
  preserving their scientific assertions and verifying both Ni/Si append orders
- Regenerate exported bundles after upgrading. Canonical snapshot checks reject
  stale or modified exports rather than silently rewriting their provenance
- Ships no source PDF, figure, rendered page or extracted full text. Dubois et
  al. carries ©2006 APS; open reuse or full-text redistribution permission has
  not been verified

```sh
python -m materials_boundaries catalog predictions --quantity tensile_first_instability_strength --text --lang en
python -m materials_boundaries prediction plot --group-id dubois_2006_si_directional_instability --output /tmp/si-first-instability --lang en
```

Use `--lang zh`, `--lang ja` or `--lang de` for the same data in another display
language. Omitting `--group-id` still selects the original Ni shear group.

See [the scientific, source and CLI contract](COMPUTATIONAL_PREDICTIONS.md).
