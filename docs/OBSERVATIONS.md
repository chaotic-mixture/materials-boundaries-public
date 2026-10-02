# Traceable, catalog-only observations

Version 0.7.0 adds a **separate observations catalog: two property records from one study**. It does not add two independent confirmations, a broad experimental database, a theoretical bound, an engineering allowable, an executable rule or a plot. That release kept the 22 claim records unchanged and brought the source catalog to 20 records. Current v0.8.0 has 26 claims under schema 1.6.0; all 20 sources and both observation records remain unchanged. The composite evaluator still returns the same eight evaluations.

## Source and inspection scope

Changgu Lee, Xiaoding Wei, Jeffrey W. Kysar and James Hone, [“Measurement of the Elastic Properties and Intrinsic Strength of Monolayer Graphene”](https://doi.org/10.1126/science.1157996), *Science* **321** (5887), 385–388, 18 July 2008. Source and study ID: `lee_wei_kysar_hone_2008`. [PubMed metadata](https://pubmed.ncbi.nlm.nih.gov/18635798/) corroborates the bibliographic identity.

The relevant main-text passages were checked in a coauthor-uploaded author PDF. Supporting supplementary material was inaccessible and **has not been inspected**. This is passage verification, not raw-data reanalysis, replication, independent scientific review or independent confirmation of specimen conditions. The article's attribution of intrinsic behavior to defect-free material remains a source interpretation, not an independently verified defect census.

Copyright ©2008 AAAS, all rights reserved. An accessible author PDF does not grant an open reuse license. Only brief numerical facts, bibliographic metadata and original curation notes are bundled; no PDF, article text, figures or raw experimental data are redistributed. Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md).

## Two distinct quantities

| Record ID | Quantity | Source-reported summary | Main-text locator |
| --- | --- | --- | --- |
| `lee_2008_graphene_in_plane_stiffness_2d` | `in_plane_stiffness_2d` | 340 ± 50 N/m | p. 387, final paragraph |
| `lee_2008_graphene_breaking_strength_2d` | `breaking_strength_2d` | 42 ± 4 N/m | p. 388, opening paragraph |

Both describe freestanding, suspended **monolayer graphene**, have `quantity_dimension: force_per_length`, `si_unit: N/m`, `observation_type: experiment_derived_model_dependent` and `evaluation_support: catalog_only`. The same `study_id` is essential: these are two properties of one study, not two replications.

The recorded preparation is mechanically deposited graphite flakes; optical microscopy and Raman spectroscopy identified monolayers, with 1 and 1.5 µm circular suspended spans (p. 385 and Fig. 1). These source-reported preparation details do not independently verify specimen defects or environmental conditions.

N/m is the canonical two-dimensional force-per-length unit. Equal units do not make stiffness and breaking strength interchangeable. Neither quantity is the three-dimensional effective composite Young's modulus produced by the elastic calculator. There is **no default thickness, pressure/GPa conversion or derived three-dimensional numerical output**. A compatible comparison would also need material state, dimensionality, quantity, method and stress/strain conventions, not merely a matching unit label.

## What the inference assumes

The experiment uses AFM central indentation of suspended membranes. The stiffness fit uses the clamped isotropic circular-membrane model in p. 386, Eq. (2): negligible bending stiffness, a point-load approximation and assumed Poisson ratio ν = 0.165. That ν is an input to the source model, not a measured Poisson ratio. Fitting an indentation force–displacement curve is a model-dependent inference of in-plane stiffness.

The breaking-strength result is inferred from AFM failure measurements using a nonlinear constitutive model and finite-element analysis with a finite-radius indenter. The p. 387 final text column describes inference of the nonlinear coefficient from mean failure force and a check with a different tip radius. Do not transfer the stiffness fit's point-load approximation to this failure analysis. The source's p. 386, Eq. (1), uses **second Piola–Kirchhoff stress and Lagrangian strain**:

- σ = E2D ε + D2D ε²
- Model maximum: σmax = −E2D²/(4D2D)

These expressions describe the source's inference, not a formula that this project executes. The source maximum is not a directly measured uniform tensile stress, a universal upper bound, or an interchangeable Cauchy/engineering stress. Retain the convention when reading the reported 42 ± 4 N/m result; do not silently turn it into a generic three-dimensional tensile strength.

## Uncertainty and sample counts

For **both** reported ± values, the statistical type, coverage factor and confidence level are unverified. The catalog stores `reported_plus_minus_unspecified` with null coverage fields. Do not label ±50 or ±4 as standard deviation, standard error, a confidence interval, lower/upper bounds or certified uncertainty endpoints. This release neither propagates nor recalculates uncertainty.

The stiffness-fit distribution is separate: p. 386, final paragraph, gives **23 membranes from 2 flakes**; p. 387, opening discussion, reports **67 force–displacement fits**, with **mean 342 N/m and standard deviation 30 N/m**. These statistics do not replace 340 ± 50 N/m or explain its ± notation. They describe stiffness fits only; **they are not breaking-test counts**. Breaking-strength `sample_metadata` remains null, rather than borrowing those counts.

Temperature, atmosphere, humidity and loading rate remain null/unverified for both records. Missing context is not room temperature, air, a particular humidity or quasi-static rate by default. No numerical model applicability status is assigned to these observations.

## Read-only access

```sh
python -m materials_boundaries catalog observations
python -m materials_boundaries catalog observations --id lee_2008_graphene_in_plane_stiffness_2d --text --lang en
python -m materials_boundaries catalog observations --source-id lee_wei_kysar_hone_2008 --json
python -m materials_boundaries catalog observations --quantity breaking_strength_2d --text --lang zh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query "graphene strength" --text --lang de
python -m materials_boundaries catalog sources --id lee_wei_kysar_hone_2008 --text --lang ja
```

Observation queries index `id`, `name`, `quantity`, `observation_type`, `study_id`, `material.name`, evidence source IDs and curated display-name aliases in all four languages. Search is literal, Unicode-casefolded and all-term; it is not paper search or automatic translation. `--id`, `--source-id`, `--quantity` and `--observation-type` use exact case-sensitive matches and combine with the query using AND. `--source-id` also works for claims; quantity/type filters are observation-only. No numerical value, uncertainty, method or condition search is implied. See [the full CLI/Python contract](CATALOG.md).

Default/`--json` output remains a canonical `{schema_version, records}` envelope with observation schema **1.0.0**, independent of display language. Human-readable output translates labels and authored display names while retaining IDs, units, values, original evidence wording and verification gaps. Independent scientific and native-language review of these translations remain pending.

## Keep the contracts separate

- `materials_boundaries/data/observations.json` stores summaries and context; it is neither `claims.json` nor an instance file
- `schemas/observations.schema.json` describes the new observation envelope; current claims schema is 1.6.0, sources 1.0.0 and evaluation 1.1.0
- `validate` and `evaluate` still accept composite instances only; they do not execute observation records or infer specimen applicability
- Comparison builders/renderers still use the original eight elastic evaluations. No observation overlays, uncertainty bars, material ranking or graphene/composite comparison are added
- The new source is evidence for these observations only; its presence does not alter the earlier claims or their source evidence

See [v0.7.0 migration](MIGRATION_v0.7.0.md), [source notes](SOURCES.md), [four-language terminology](TERMINOLOGY.md) and [visualization boundaries](VISUALIZATION.md).
