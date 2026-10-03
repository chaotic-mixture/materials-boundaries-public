# Traceable, catalog-only observations

Version **0.23.0** retains the v0.22.0 catalog of **12 property records from four studies**: the six
unchanged graphene, monolayer MoS2 and monolayer hBN summaries, plus six PA12 CF15
tensile-test summaries at distinct reported chamber conditions from one study.
The three older pairs remain `experiment_derived_model_dependent` 2D records.
The new closed family is `experiment_derived_tensile_test_summary`, with 3D
pressure dimension. Every record remains `catalog_only`. Conditions or properties
from one study are associated records, not independent cross-study confirmations.
The catalog is neither a broad experimental database nor a source of universal
bounds, engineering allowables, fitted temperature laws or material rankings.

Observations schema remains **1.3.0** and the separate
[offline inspection view](OBSERVATION_INSPECTION.md) remains **1.1.0**.
Inspection retains packaged-catalog-ordered text cards/tables and auditable JSON/CSV/SVG/HTML,
with essential caveats before values. The catalog now has **36 mechanics claims
and 52 sources**, with the **12 predictions, five synthetic temperature models,
seven synthetic branches and eight executable composite rules unchanged**.
The six earlier observation objects and their scientific contracts remain exact;
graphene uncertainty, the MoS2 q discrepancy and hBN component-specific evidence
are neither generalized nor replaced. See [v0.22.0 migration](MIGRATION_v0.22.0.md).

The [v0.23.0 explicit temperature plot](OBSERVATION_TEMPERATURE_PLOT.md) separately
admits one complete six-cell PA12 dataset under plot schema 1.0.0. Numeric axes
and central-value ±reported-SD glyphs describe the source cells only, with no mean,
CI, hard-bound, direct-specimen-temperature or material-model claim. This does
not turn arbitrary observations or inspection selections into a plot; all
catalog-only classifications and generic inspection restrictions remain.

## PA12 CF15: Ciganas et al. (2026), six temperature conditions

The source-specific family contains only the six selected Table 3 ultimate
tensile-strength/SD cells at reported chamber conditions **23, 40, 60, 80, 100
and 120 °C**. It describes horizontally FFF-printed Fiberlogy PA12 CF15 with
alternating +45°/−45° raster, tested under one displacement-rate protocol.
Chamber conditions after 30 minutes of stabilization are not independently
verified direct specimen temperatures. The reported rate is 1 mm/min crosshead
motion, not a measured local strain rate. Actual moisture/RH, stress convention,
stress-area basis, exact central statistic and aggregation remain unknown.

Each condition reports three tensile tests. Its ± is **reported SD**, not SEM,
a confidence interval, hard bounds or a complete uncertainty budget. These are
six condition summaries from one study, not six independent studies. Values
retain MPa source strings (including trailing zeros) separately from exact
integer Pa re-expression by 1 MPa = 1000000 Pa. That unit scale adds no measured
precision, observation, geometry reconstruction or thickness assumption.

The current publisher HTML was inspected; PDF access did not yield an inspected
artifact. Revision metadata and a cached/live discrepancy in unselected Table 4
remain visible, without asserting all source versions agree. The six selected
Table 3 cells agree across current HTML, visual inspection and an independent
second transcription. This is not raw-data reanalysis or scientific replication.
See the [full PA12 CF15 source, values, protocol, rights and limits](PA12_CF15_TEMPERATURE_OBSERVATIONS.md).

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

## Monolayer hBN: Falin et al. (2017), new records

### Source identity, version and inspection

Aleksey Falin, Qiran Cai, Elton J. G. Santos, Declan Scullion, Dong Qian,
Rui Zhang, Zhi Yang, Shaoming Huang, Kenji Watanabe, Takashi Taniguchi,
Matthew R. Barnett, Ying Chen, Rodney S. Ruoff and Lu Hua Li,
[“Mechanical properties of atomically thin boron nitride and the role of interlayer interactions”](https://doi.org/10.1038/ncomms15815),
*Nature Communications* **8**, 15815, published 22 June 2017. Source and study
ID: `falin_et_al_2017_hbn_mechanical_properties`; the separate closed family is
`falin_2017_hbn_monolayer_indentation_v1`.

The inspected primary artifact is the [published publisher HTML](https://www.nature.com/articles/ncomms15815),
including visually checked equation images for Eqs. (1), (2) and (4). The main
article PDF was **not inspected**; main-text locators therefore use sections,
equations and figures, not guessed PDF page numbers. Relevant text in the
[publisher-linked supplement](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fncomms15815/MediaObjects/41467_2017_BFncomms15815_MOESM442_ESM.pdf)
was checked, with PDF pp. 4–5 / Figs. S4–S5 visually inspected. The
[publisher-linked peer-review author response](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fncomms15815/MediaObjects/41467_2017_BFncomms15815_MOESM443_ESM.pdf),
PDF p. 8, Reviewer #1 question 3, was text- and visually checked for SD and
sample-count semantics. A second reader checked transcription against these
same artifacts; that is not independent scientific review or replication.

### Exactly two source-printed 2D summaries

| Record ID | Quantity | Source-reported summary | Publisher HTML locator |
| --- | --- | --- | --- |
| `falin_2017_hbn_monolayer_in_plane_stiffness_2d` | `in_plane_stiffness_2d` | **289 ± 24 N/m** | Results, “Elastic modulus and breaking strength”, paragraph associated with Fig. 3; N=11 |
| `falin_2017_hbn_monolayer_breaking_strength_2d` | `breaking_strength_2d` | **23.6 ± 1.8 N/m** | Same section, paragraph associated with Fig. 4 |

Both are `experiment_derived_model_dependent`, `force_per_length`, `N/m` and
`catalog_only`. The stiffness central statistic is the reported average; the
strength is a reported summary whose exact central-statistic label and
replicate weighting remain unspecified. Two properties from one study are
not two independent confirmations. Matching N/m units do not make stiffness
and strength interchangeable or establish a matched-condition comparison.

The article separately prints the selected **N/m values**. No curator converts
or reconstructs them from 0.865 ± 0.073 TPa or 70.5 ± 5.5 GPa. The source's
**0.334 nm** thickness is recorded solely as its volumetric/FEM convention;
it is neither a default thickness nor the illustrated **0.48 nm apparent AFM
height**. Preserve each source-printed rounded value without “repairing” it by
multiplication. No new 3D observation or automatic N/m-to-Pa/GPa conversion is
introduced.

The specimens are suspended monolayer hexagonal BN, mechanically exfoliated
onto patterned SiO2/Si with 90 nm oxide. The reported well radius is **650 nm**
(diameter **1.3 μm**). Optical microscopy, AFM height profiles and Raman
characterization identify monolayers. The authors' high-quality single-crystal
description does not establish an independent quantitative defect census.
Orientation and distinct parent-flake count remain unknown.

### Stiffness fit and q arithmetic, without a mismatch claim

The Cypher AFM central-indentation protocol uses diamond tips with reported
TEM-measured radii **5.6 and 6.3 nm**. These are two radii, not a mean with an
uncertainty, and per-sheet assignment is unknown. Fig. S4's 12.6 nm diameter is
an example for one tip. Cantilever calibration combines thermal-noise and Sader
methods. Eq. (1) gives δ=ΔZ_piezo−δ_tip. The Eq. (2) circular-membrane fit is:

- F = σ₀²ᴰ(πa)(δ/a) + E²ᴰ(q³a)(δ/a)³
- q = 1/(1.049 − 0.15ν − 0.16ν²), with source-adopted **ν=0.211**

Pretension and membrane stretching are fitted; there is no bending term. The
isotropic membrane/central-load assumption belongs to this stiffness fit, not
to the finite-radius FEM strength reduction. The adopted ν is a model input
cited to earlier work, not a measurement of these specimens.

Evaluating the printed formula at ν=0.211 gives **0.9898768854482001**. This is
**curator arithmetic only**, not a source-reported fitted value or a replacement
constant. No separately printed numerical q was found, and the actual constant
used by the uninspected fit implementation remains unknown. There is therefore
**no hBN printed-q mismatch claim**. The separate, preserved MoS2 printed-q
inconsistency must not be copied into this family or erased by this distinction.

### Strength is a nonlinear FEM volume average

Methods, “Finite element analysis”, uses source Eq. (4), σ=Eε+Dε², with
**E=865 GPa** and **D=−2035 GPa** as source model constants. The latter is
reported as obtained from experimental results; neither becomes a new
standalone observation here. An equivalent elastic-plastic ABAQUS material
implementation represents assumed nonlinear elastic behavior; its name does
not establish physical plasticity.

The source uses an axisymmetric membrane, a rigid spherical indenter,
frictionless contact, 650 nm radius and 0.334 nm initial thickness, with
1663 MAX1 two-node linear axisymmetric membrane elements. At loading steps
matched to the experimental fracture load, the strength reduction uses the
**volume average of stresses in membrane elements directly beneath the
finite-radius indenter**. It is not a direct uniform-tension measurement,
a local maximum formula or the MoS2 finite-tip strength formula.

**Supplementary Fig. S5 plots maximum Von Mises stress**, a model-sensitivity
diagnostic distinct from that volume-averaged reported strength. Its reported
25.7% linear-model overestimate is neither an uncertainty correction nor a
multiplier applied to 23.6 ± 1.8 N/m. The stress component/invariant used in the
volume average is not explicitly identified. Eq. (4) does not explicitly define
finite-strain stress/strain measures, so both remain **null**; Fig. 5's nominal
strain label and S5's Von Mises label do not establish Cauchy, first/second
Piola–Kirchhoff or Lagrangian conventions for the strength result. In particular,
the graphene convention is not inherited.

### SD evidence, tested sheets and environmental unknowns

Both ±24 and ±1.8 are labeled `reported_standard_deviation` **because the
publisher-linked peer-review author response, PDF p. 8, Reviewer #1 question 3,
explicitly clarifies SDs and refers to Figs. 3–4**. The main article's ± notation
alone does not define this. The response is a distinct source artifact, not the
final article or a raw-data file. These are not SEMs, confidence intervals,
hard bounds or a full uncertainty budget. Coverage factor, confidence level,
exact averaging convention and replicate weighting remain unknown.

The same response defines N as **tested sheets**. **N=11** is printed with the
monolayer stiffness average; it is study context for the strength record,
not a separately verified strength-summary sample size or count of failure
events. A typical protocol of five increasing-load indentations per sheet does
not mean exactly five per sheet and **must not become a 55-curve dataset**.
Acquired, retained and excluded curve totals, parent-flake count and failure-event
count remain **null**. Curves with obvious/large hysteresis are excluded, but the
exact exclusion threshold and count are not reported.

Methods, “Materials and fabrication”, reports **ambient conditions** and
**0.5 μm/s loading/unloading probe translation velocity**. Numerical temperature,
pressure, gas composition and humidity remain **unknown**. A translation velocity
is not a strain, force or stress rate. The FEM displacement increment of
0.1 nm per step is numerical discretization, not experimental rate, and its
100 nm endpoint is not an experimental mean failure displacement. Neither the
paper's 800 °C oxidation discussion nor computational electronic temperature
is an indentation condition.

### Selection, verification and rights

This addition excludes bilayer/few-layer hBN, the paper's graphene controls,
DFT/interlayer/sliding predictions, graph digitization and new model evaluation.
No raw AFM curves, fit code or FEM input deck was reanalysed, no author was
contacted and no public source-data file was located. The article says supporting
data are available from the corresponding author on request; no request was made.
No universal bound, engineering allowable, material ranking, matched-environment
comparison, observation plot or composite overlay is supplied.

The publisher article is ©2017 The Author(s) under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), subject to contrary
third-party credit lines. Attribution, title and DOI are retained above. Separate
license scope for the supplement and peer-review file is **not verified**; the
article's license is not automatically assigned to them. The repository includes
brief attributed facts, locators and original curation only: **no source PDF,
full text, figure, screenshot, peer-review report or raw-data collection**.
MIT covers original project contributions and does not replace source licensing.
Scientific and native-language review remain outstanding. See
[v0.19.0 migration](MIGRATION_v0.19.0.md), [sources](SOURCES.md) and
[third-party notices](../THIRD_PARTY_NOTICES.md).

## Offline inspection (v0.22.0)

```sh
python -m materials_boundaries observation inspect --output /tmp/observations --lang en
python -m materials_boundaries observation inspect --source-id ciganas2026polym18050563 --output /tmp/pa12-cf15 --lang en
python -m materials_boundaries observation inspect --output /tmp/mos2-strength --source-id bertolazzi_brivio_kis_2011 --quantity breaking_strength_2d --lang zh
```

This separate interface preserves packaged catalog order and distinct study/quantity
facets. Repeat `--id` to select exact records; combine exact source/quantity
filters with AND. Grouping changes navigation only. JSON/CSV remain independent
of language; SVG/HTML support all four authored locales. Warnings, scoped counts,
unknown conditions and evidence remain visible. There is no common numeric axis,
uncertainty endpoint, aggregation or inferred equivalence. See the
[inspection contract and Python API](OBSERVATION_INSPECTION.md).

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
python -m materials_boundaries catalog observations --source-id falin_et_al_2017_hbn_mechanical_properties --text --lang en
python -m materials_boundaries catalog observations --query "hBN stiffness" --json
python -m materials_boundaries catalog observations --source-id ciganas2026polym18050563 --text --lang en
python -m materials_boundaries catalog observations --observation-type experiment_derived_tensile_test_summary --json
python -m materials_boundaries catalog observations --quantity ultimate_tensile_strength_as_reported_3d --json
```

Observation queries index `id`, `name`, `quantity`, `observation_type`, `study_id`, `material.name`, evidence source IDs and curated display-name aliases in all four languages. Search is literal, Unicode-casefolded and all-term; it is not paper search or automatic translation. `--id`, `--source-id`, `--quantity` and `--observation-type` use exact case-sensitive matches and combine with the query using AND. `--source-id` also works for claims; quantity/type filters are observation-only. No numerical value, uncertainty, method or condition search is implied. See [the full CLI/Python contract](CATALOG.md).

Default/`--json` output remains a canonical `{schema_version, records}` envelope with observation schema **1.3.0**, independent of display language. Human-readable output translates labels and authored display names while retaining IDs, units, values, original evidence wording and verification gaps. Independent scientific and native-language review of these translations remain pending.

## Keep the contracts separate

- `materials_boundaries/data/observations.json` stores summaries and context; it is neither `claims.json` nor an instance file
- `schemas/observations.schema.json` describes the closed graphene/MoS2/hBN and six-cell PA12 CF15 observation families; current claims schema is 1.11.0, sources 1.0.0 and evaluation 1.1.0
- `validate` and `evaluate` still accept composite instances only; they do not execute observation records or infer specimen applicability
- Composite comparison builders/renderers still use the original eight elastic evaluations. The separate observation inspection builder reads only observation/source catalogs; it does not execute formulas or add quantitative plots, overlays, uncertainty bars, ranking or matched-condition comparison
- The separate v0.23.0 temperature-observation builder admits only the complete reviewed PA12 dataset, uses its own closed schema and numeric axes, and calculates mandatory ±reported-SD glyph endpoints as display arithmetic only; it adds no scientific observations, material model or new executable rule
- The Ciganas source added in v0.22.0 supports six selected tensile summaries only; the 51 earlier source objects, six earlier observation objects, claims, predictions and synthetic temperature contents remain unchanged
- The new family is closed by dataset/quantity/source-cell identity. Subsets and renamed record identities remain valid when their scientific payload is unchanged; the full catalog rejects duplicate aliases for a selected cell and requires the complete six-cell set. Since v0.23.0, packaged permutations of that set are valid; generic inspection retains packaged order, while the explicit temperature plot restores Table 3 source order. Additional temperatures, materials or protocols require scientific review rather than automatic same-family appendability
- Existing supported-family appendability remains available under each complete pre-existing scientific contract

See [v0.23.0 migration](MIGRATION_v0.23.0.md), [v0.22.0 migration](MIGRATION_v0.22.0.md), [v0.19.0 migration](MIGRATION_v0.19.0.md), [v0.17.0 migration](MIGRATION_v0.17.0.md), [historical v0.7.0 migration](MIGRATION_v0.7.0.md), [source notes](SOURCES.md), [four-language terminology](TERMINOLOGY.md) and [visualization boundaries](VISUALIZATION.md).
