# Traceable, catalog-only observations

Version **0.17.0** contains **four property records from two studies**: two
unchanged Lee–Wei–Kysar–Hone (2008) graphene records and two new
Bertolazzi–Brivio–Kis (2011) monolayer MoS2 records. Each pair describes two
quantities from one study, not two independent confirmations. The catalog is
neither a broad experimental database nor a source of universal bounds or
engineering allowables. All four records remain model-dependent and
`catalog_only`; no evaluator, observation plot, comparison or ranking is added.

The observations envelope advances from schema **1.0.0 to 1.1.0** through a
narrow, closed MoS2 family. Both original graphene record objects are preserved
exactly; their unknown uncertainty type and conditions do not inherit the new
study's metadata. The release has 34 unchanged mechanics claims and 48 source
records; exactly eight composite evaluations remain supported. See
[v0.17.0 migration](MIGRATION_v0.17.0.md).

## Graphene: Lee et al. (2008), existing records

### Source and inspection scope

Changgu Lee, Xiaoding Wei, Jeffrey W. Kysar and James Hone, [“Measurement of the Elastic Properties and Intrinsic Strength of Monolayer Graphene”](https://doi.org/10.1126/science.1157996), *Science* **321** (5887), 385–388, 18 July 2008. Source and study ID: `lee_wei_kysar_hone_2008`. [PubMed metadata](https://pubmed.ncbi.nlm.nih.gov/18635798/) corroborates the bibliographic identity.

The relevant main-text passages were checked in a coauthor-uploaded author PDF. Supporting supplementary material was inaccessible and **has not been inspected**. This is passage verification, not raw-data reanalysis, replication, independent scientific review or independent confirmation of specimen conditions. The article's attribution of intrinsic behavior to defect-free material remains a source interpretation, not an independently verified defect census.

Copyright ©2008 AAAS, all rights reserved. An accessible author PDF does not grant an open reuse license. Only brief numerical facts, bibliographic metadata and original curation notes are bundled; no PDF, article text, figures or raw experimental data are redistributed. Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md).

### Two distinct quantities

| Record ID | Quantity | Source-reported summary | Main-text locator |
| --- | --- | --- | --- |
| `lee_2008_graphene_in_plane_stiffness_2d` | `in_plane_stiffness_2d` | 340 ± 50 N/m | p. 387, final paragraph |
| `lee_2008_graphene_breaking_strength_2d` | `breaking_strength_2d` | 42 ± 4 N/m | p. 388, opening paragraph |

Both describe freestanding, suspended **monolayer graphene**, have `quantity_dimension: force_per_length`, `si_unit: N/m`, `observation_type: experiment_derived_model_dependent` and `evaluation_support: catalog_only`. The same `study_id` is essential: these are two properties of one study, not two replications.

The recorded preparation is mechanically deposited graphite flakes; optical microscopy and Raman spectroscopy identified monolayers, with 1 and 1.5 µm circular suspended spans (p. 385 and Fig. 1). These source-reported preparation details do not independently verify specimen defects or environmental conditions.

N/m is the canonical two-dimensional force-per-length unit. Equal units do not make stiffness and breaking strength interchangeable. Neither quantity is the three-dimensional effective composite Young's modulus produced by the elastic calculator. There is **no default thickness, pressure/GPa conversion or derived three-dimensional numerical output**. A compatible comparison would also need material state, dimensionality, quantity, method and stress/strain conventions, not merely a matching unit label.

### What the inference assumes

The experiment uses AFM central indentation of suspended membranes. The stiffness fit uses the clamped isotropic circular-membrane model in p. 386, Eq. (2): negligible bending stiffness, a point-load approximation and assumed Poisson ratio ν = 0.165. That ν is an input to the source model, not a measured Poisson ratio. Fitting an indentation force–displacement curve is a model-dependent inference of in-plane stiffness.

The breaking-strength result is inferred from AFM failure measurements using a nonlinear constitutive model and finite-element analysis with a finite-radius indenter. The p. 387 final text column describes inference of the nonlinear coefficient from mean failure force and a check with a different tip radius. Do not transfer the stiffness fit's point-load approximation to this failure analysis. The source's p. 386, Eq. (1), uses **second Piola–Kirchhoff stress and Lagrangian strain**:

- σ = E2D ε + D2D ε²
- Model maximum: σmax = −E2D²/(4D2D)

These expressions describe the source's inference, not a formula that this project executes. The source maximum is not a directly measured uniform tensile stress, a universal upper bound, or an interchangeable Cauchy/engineering stress. Retain the convention when reading the reported 42 ± 4 N/m result; do not silently turn it into a generic three-dimensional tensile strength.

### Uncertainty and sample counts

For **both** reported ± values, the statistical type, coverage factor and confidence level are unverified. The catalog stores `reported_plus_minus_unspecified` with null coverage fields. Do not label ±50 or ±4 as standard deviation, standard error, a confidence interval, lower/upper bounds or certified uncertainty endpoints. This release neither propagates nor recalculates uncertainty.

The stiffness-fit distribution is separate: p. 386, final paragraph, gives **23 membranes from 2 flakes**; p. 387, opening discussion, reports **67 force–displacement fits**, with **mean 342 N/m and standard deviation 30 N/m**. These statistics do not replace 340 ± 50 N/m or explain its ± notation. They describe stiffness fits only; **they are not breaking-test counts**. Breaking-strength `sample_metadata` remains null, rather than borrowing those counts.

Temperature, atmosphere, humidity and loading rate remain null/unverified for both records. Missing context is not room temperature, air, a particular humidity or quasi-static rate by default. No numerical model applicability status is assigned to these observations.

## Monolayer MoS2: Bertolazzi et al. (2011), new records

### Source identity and inspected artifact

Simone Bertolazzi, Jacopo Brivio and Andras Kis,
[“Stretching and Breaking of Ultrathin MoS2”](https://doi.org/10.1021/nn203879f),
*ACS Nano* **5** (12), 9703–9709 (2011). Source and study ID:
`bertolazzi_brivio_kis_2011`. The publisher-indexed abstract,
[PubMed record](https://pubmed.ncbi.nlm.nih.gov/22087740/) and
[EPFL institutional metadata](https://infoscience.epfl.ch/entities/publication/e119e335-b8de-42b8-a8e3-ec8b6d3fd8ba)
corroborate bibliographic identity. Online publication was 16 November 2011;
the journal issue is dated 27 December 2011. These dates are source metadata,
not a software-release date.

The inspected [EPFL PDF](https://infoscience.epfl.ch/server/api/core/bitstreams/5af84a4c-55a4-4151-9d85-d5c215d848a4/content)
has seven pages labeled **A–G**, with journal volume/issue/page/year placeholders
in its footer. Despite repository labels “Publisher’s Version”, “Published
version” and “openaccess”, this is a **proof-formatted artifact**. Locators below
use one-based PDF page numbers plus printed letters; final journal-page mapping
and final-publisher-text equivalence are **not verified**. Its SHA-256 is
`348f5d00676c252d79f3717802be4cc999349c7180b261219bd209ebbe17e9ca`.

All seven pages were text-checked; PDF pp. 3–6 were visually inspected. A second
reader checked the selected transcription and layout against the same artifact;
this is not independent scientific review or a separate experiment. The official
publisher full-text fetch returned HTTP 403, and the official supplement route
failed. Neither restriction was bypassed. The independently public EPFL copy
had already been located. The supplement, described by the main text as SEM
images of AFM probes, is **not inspected**; no raw-data reanalysis, independent
tip-radius reconstruction, replication or independent scientific review is claimed.

### Two distinct source-reported quantities

| Record ID | Quantity | Source-reported summary | Inspected-artifact locator |
| --- | --- | --- | --- |
| `bertolazzi_2011_mos2_monolayer_in_plane_stiffness_2d` | `in_plane_stiffness_2d` | 180 ± 60 N/m | PDF p. 4 (D), right column, fit-average paragraph |
| `bertolazzi_2011_mos2_monolayer_breaking_strength_2d` | `breaking_strength_2d` | 15 ± 3 N/m | PDF p. 5 (E), left column immediately below Eq. (3) |

Both describe freestanding, suspended **monolayer MoS2**, with
`observation_type: experiment_derived_model_dependent`,
`quantity_dimension: force_per_length`, `si_unit: N/m` and
`evaluation_support: catalog_only`. Equal units do not make stiffness and
strength the same quantity. The records share specimens, methods and model
assumptions. They are neither independent confirmations of each other nor
matched-condition comparisons with graphene.

The preparation is micromechanical exfoliation of naturally occurring
molybdenite with PVA/PMMA-assisted transfer to patterned SiO2. Optical contrast
and AFM thickness verification identify monolayers (PDF p. 2 (B) and pp. 5–6
(E–F), Materials and Methods). The source reports circular suspended spans of
550 ± 10 nm and a 12 ± 2 nm SEM-based tip-radius estimate. Those geometric
± tolerances remain statistically unspecified; the explicit SD definition for
property summaries is not automatically assigned to them. Crystal orientation
remains unknown. The source's interpretation of near-intrinsic/mostly defect-free
behavior is not an independently established defect census.

### AFM inference and the unresolved printed-q discrepancy

Stiffness is inferred by least-squares fitting AFM force–deflection curves,
using a clamped, prestretched, isotropic circular membrane and a linear material
constitutive assumption. It is not direct uniform tensile-modulus measurement.
The source's Eq. (1) is:

- F = σ0^(2D) πδ + E^(2D) q³ δ³/r²

Here the linear force term represents pretension and the cubic term membrane
stretching. Geometric nonlinearity of indentation is distinct from a nonlinear
material constitutive law. Bending-dominated plate behavior is not the fitted
regime. The stiffness fit uses the point-loading approximation, with reported
r_tip/r approximately 0.05.

PDF p. 4 (D), upper-right column after Eq. (1), separately prints:

- q = 1/(1.05 − 0.15ν − 0.16ν²)
- assumed ν = 0.27, adopted from bulk MoS2 rather than measured here
- stated q = 0.95

These printed statements are **internally inconsistent**. Curator arithmetic
on the printed formula at ν = 0.27 gives approximately **1.002168693051764**.
That number is an audit check, not a source-reported measurement, replacement
fit constant or corrected observation. The records retain the formula, assumed
ν and stated q separately and flag the inconsistency. **The q actually used
in the fits is unresolved**. No choice between them, raw-data refit, alteration
of 180 ± 60 N/m, or recomputation of 15 ± 3 N/m is made.

Failure inference uses the source's finite spherical-tip local-stress model,
not the stiffness fit's point-load model or Lee's nonlinear constitutive/finite-
element failure inference. Eq. (3), PDF p. 5 (E), is:

- σ_max^(2D) = sqrt(F_max E^(2D)/(4π r_tip))

Its source assumptions include a linearly elastic isotropic membrane, load large
compared with pretension and indenter radius small relative to membrane radius;
the source states κ < 0.02 in this regime. The result is an inferred maximum
local central stress at failure, not a measured uniform tensile stress. It
inherits uncertainty in fitted E2D, including the unresolved printed-q issue.
The inspected main text does not specify the stress/strain measures, so both
remain **null**. Do not transfer the graphene second-Piola/Lagrangian convention.
These equations are descriptive source context and are never executed here.

### SD semantics, sample scope and test conditions

The sentence following the stiffness averages on PDF p. 4 (D), right column,
explicitly defines the modulus and strength uncertainties as **standard
deviations of experimental values**. Thus ±60 and ±3 use
`reported_standard_deviation`. They are not standard errors, confidence
intervals, certified bounds or a complete uncertainty budget. Coverage factor,
confidence level and exact replicate/weighting convention remain unspecified;
in particular, no 68% interval is inferred. This SD label does not alter the
existing graphene `reported_plus_minus_unspecified` records.

The study reports **nine monolayer membranes** on PDF p. 3 (C), left column;
the stiffness average additionally names nine on PDF p. 4 (D), right column.
Six bilayer membranes are study context only, outside this monolayer batch.
Multiple indentation curves per hole do not establish a total force-curve
count. Distinct parent-flake count and separately enumerated **failure-event
count remain null**. Nine study/stiffness membranes must not become nine
verified breaking tests.

A reported **2 μm/s vertical probe translation speed** on PDF p. 2 (B) is a
probe-motion quantity only, not membrane strain rate, force rate or stress rate.
Test temperature, atmosphere and humidity remain **null**. An air temperature
controller used to reduce drift does not establish a numerical test temperature
or a controlled atmosphere. The **400 °C, four-hour vacuum anneal is preparation**,
not the indentation test environment. Missing conditions cannot be treated as
matched across studies.

### Selection and rights boundary

Only these two monolayer 2D summaries are included. Bilayer results,
thickness-normalized 3D statements and digitized graph values are not new
records. No default thickness, N/m-to-Pa/GPa conversion, strength correction,
plot, cross-study comparison or material ranking is introduced. The body
paragraph reporting breaking averages points to Fig. 4 although the summary
bars are in Fig. 5; locators use the explicit body paragraph directly. The
held-out bilayer text/figure discrepancy is not resolved by digitization.

Publisher metadata states ©2011 American Chemical Society; the inspected proof
carries an ACS notice with a placeholder year. No explicit open-reuse license
is verified. Public download and repository “openaccess” labeling are not reuse
permission. Only brief factual values, bibliographic metadata, locators and
original curation are bundled. **No paper PDF, full text, figures, page
screenshots or raw measurement collection** is included. MIT applies to
original project contributions only, not the paper or scientific facts; no
legal review is claimed. See [source notes](SOURCES.md) and
[third-party notices](../THIRD_PARTY_NOTICES.md).

## Read-only access

```sh
python -m materials_boundaries catalog observations
python -m materials_boundaries catalog observations --id lee_2008_graphene_in_plane_stiffness_2d --text --lang en
python -m materials_boundaries catalog observations --source-id lee_wei_kysar_hone_2008 --json
python -m materials_boundaries catalog observations --quantity breaking_strength_2d --text --lang zh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query "graphene strength" --text --lang de
python -m materials_boundaries catalog sources --id lee_wei_kysar_hone_2008 --text --lang ja
python -m materials_boundaries catalog observations --source-id bertolazzi_brivio_kis_2011 --text --lang en
python -m materials_boundaries catalog observations --query "MoS2 stiffness" --json
python -m materials_boundaries catalog sources --id bertolazzi_brivio_kis_2011 --text --lang de
```

Observation queries index `id`, `name`, `quantity`, `observation_type`, `study_id`, `material.name`, evidence source IDs and curated display-name aliases in all four languages. Search is literal, Unicode-casefolded and all-term; it is not paper search or automatic translation. `--id`, `--source-id`, `--quantity` and `--observation-type` use exact case-sensitive matches and combine with the query using AND. `--source-id` also works for claims; quantity/type filters are observation-only. No numerical value, uncertainty, method or condition search is implied. See [the full CLI/Python contract](CATALOG.md).

Default/`--json` output remains a canonical `{schema_version, records}` envelope with observation schema **1.1.0**, independent of display language. Human-readable output translates labels and authored display names while retaining IDs, units, values, original evidence wording and verification gaps. Independent scientific and native-language review of these translations remain pending.

## Keep the contracts separate

- `materials_boundaries/data/observations.json` stores summaries and context; it is neither `claims.json` nor an instance file
- `schemas/observations.schema.json` describes the closed graphene/MoS2 observation families; current claims schema is 1.10.0, sources 1.0.0 and evaluation 1.1.0
- `validate` and `evaluate` still accept composite instances only; they do not execute observation records or infer specimen applicability
- Comparison builders/renderers still use the original eight elastic evaluations. No observation plots, overlays, uncertainty bars, material ranking or graphene/MoS2/composite comparison are added
- The new MoS2 source is evidence for its two observations only; all earlier source records, claims, predictions and synthetic temperature contents remain unchanged

See [v0.17.0 migration](MIGRATION_v0.17.0.md), [historical v0.7.0 migration](MIGRATION_v0.7.0.md), [source notes](SOURCES.md), [four-language terminology](TERMINOLOGY.md) and [visualization boundaries](VISUALIZATION.md).
