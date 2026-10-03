# Getting started: Materials Boundaries

## Current v0.21.0: six additional Ni11X model predictions

Exactly six published ideal-shear predictions are added: **Ni11Cr 4.90,
Ni11Mn 5.12, Ni11Fe 5.20, Ni11Cu 4.51, Ni11Si 4.17 and Ni11Ti 4.24 GPa**.
They come from Shimanek et al., arXiv:2108.06412v2, Table 2, PDF/printed p. 27.
The catalog now has **12 predictions, 2 scientific families and 3 explicit
groups**, alongside the unchanged 36 claims, 51 sources, 6 observations from
3 studies and 5 synthetic temperature demos (7 branches). Exactly 8 composite
rules remain executable. No runtime, scientific schema or source record changes.

The new group is **Ni11X periodic models: Cr, Mn, Fe, Cu, Si and Ti**.
Select it explicitly; the Ni/Ni11Al/Ni11Co default remains three points and the
separate three-point Si first-instability group is unchanged. Ni11Si shear is
not pure-Si tensile first instability. The unfiltered prediction catalog returns
12 records; selecting the Shimanek source returns nine, not a new plotted group.

These are 12-atom, three-layer fcc-derived periodic Ni11X models with one
in-plane substitution: (111)[1,1,-2] positive pure-alias shear, prescribed shear
angle, relaxed atomic positions and non-prescribed cell parameters. Comparability
is **published-method-only**, not audited equality of raw inputs or unknown
conditions. They are not pure-X strengths, commercial grades, experiments or
universal bounds.

The six bare table labels have no printed pv/sv suffix; that does not identify
PAW datasets or valence configurations or prove the absence of semicore states.
Physical temperature, scalar pressure, magnetism/spin polarization and
statistical/total uncertainty remain unknown. The reported GGA follows
**Perdew et al. (1992), not an inferred PBE assignment**. **0.08 GPa peak
convergence is not an error bar**; 4.90 and 5.20 retain source formatting, not
uncertainty. Source PDFs, full text and figures are not republished. Translation
and source checks do not establish scientific or native-language review.

```sh
python -m materials_boundaries catalog predictions --query shimanek_v2_table2_cr_mn_fe_cu_si_ti --text --lang en
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six-en --lang en
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_ni_al_co --output /tmp/ni-original-en --lang en
python -m materials_boundaries prediction plot --group-id dubois_2006_si_directional_instability --output /tmp/si-first-instability-en --lang en
```

[Method, source and limits](COMPUTATIONAL_PREDICTIONS.md) · [Migration](MIGRATION_v0.21.0.md)

## Earlier v0.20.0: offline observation inspection

Inspect the six existing model-dependent summaries from three studies as
source-ordered cards/tables. No scientific records change: 36 claims, 51 sources,
six observations, six computational predictions and five synthetic temperature
demos (seven branches) remain. Exactly eight composite rules are executable.
The new inspection bundle schema is 1.0.0; observations stay 1.2.0.

```sh
python -m materials_boundaries observation inspect --output /tmp/observations --lang en
python -m materials_boundaries observation inspect --output /tmp/hbn --source-id falin_et_al_2017_hbn_mechanical_properties --group-by quantity --lang en
python -m materials_boundaries observation inspect --output /tmp/selected --id lee_2008_graphene_in_plane_stiffness_2d --id falin_2017_hbn_monolayer_breaking_strength_2d --lang en
python -m materials_boundaries observation inspect --help --lang en
```

Repeat `--id` for exact IDs; `--source-id` and `--quantity` are exact and
case-sensitive. All filters combine with AND; valid quantities are
`in_plane_stiffness_2d` and `breaking_strength_2d`. Default grouping is `study`;
`quantity` changes navigation only. Packaged order is retained, never value order.
Unknown/duplicate/malformed IDs, unsupported selectors/families and empty results
are rejected before files are written.

Exports: `observation-inspection.json`, `.csv`, `.en.svg`, `.narrow.en.svg` and
`.en.html`. Open HTML locally; it is standalone and script-free, with source
links followed only by the reader. JSON/CSV, source wording, numbers, IDs and
digests are language-independent. Normalized catalog display is separate from
source strings; it is not a verbatim quotation or a new thickness conversion.

Warnings precede values: MoS2 retains the unresolved printed-q discrepancy and
unknown actual fit q with no refit/correction; graphene's ± statistical meaning
is unverified; hBN strength is FEM volume-averaged under-indenter stress with
exact central statistic/component unspecified. hBN SD/count evidence remains
the peer-review author response, PDF p. 8; stiffness counts do not become
strength failure counts. Unknown conditions do not establish equivalence.

No observation evaluator, matched-condition comparison, axes, error bars,
aggregation, ranking or overlay is added. Regenerate stale inspection bundles;
do not relabel their versions. Source PDFs, figures and raw data are not bundled.
Translations are not independently scientifically or native-speaker reviewed.
[Inspection guide](OBSERVATION_INSPECTION.md) · [Migration](MIGRATION_v0.20.0.md)

## Historical v0.19.0: catalog-only monolayer hBN observations

Exactly two Falin et al. (2017) records and one source are added: **36 mechanics
claims, 51 sources, 6 observations from 3 studies**. Observations schema advances
**1.1.0 → 1.2.0** with a separate closed hBN family. Six computational predictions,
five synthetic temperature demos (seven branches) and exactly eight executable
composite rules remain unchanged; claims schema stays 1.11.0.

The source explicitly prints **289 ± 24 N/m in-plane stiffness** and
**23.6 ± 1.8 N/m breaking strength**. The SD definition comes from the
publisher-linked **peer-review author response, PDF p. 8, Reviewer #1 question 3**,
not the main text's ± notation alone. These are not SEMs, confidence intervals,
bounds or a complete uncertainty budget. Exact replicate weighting remains unknown.
**N=11 is tested sheets explicitly associated with the stiffness average**;
curve counts and failure-event counts remain unknown. Typically five indentations
per sheet does not mean exactly 55 curves or eleven verified strength replicates.

Stiffness is inferred by a circular-membrane AFM fit. Breaking strength uses
nonlinear FEM **volume-averaged stresses beneath a finite-radius indenter**,
not the **maximum Von Mises stress** diagnostic in Supplementary Fig. S5 or
a directly measured uniform tensile strength. Finite-strain stress/strain measures
remain unknown. Source formula **q=1/(1.049−0.15ν−0.16ν²)** with **ν=0.211** gives
**0.9898768854482001 by curator arithmetic only**; no separately printed numerical
q or actual fit constant is verified. No hBN q mismatch or correction is asserted.

“Ambient” supplies no numerical temperature, pressure, gas composition or humidity.
**0.5 μm/s** is loading/unloading probe translation velocity, not strain rate.
Both N/m summaries are source-printed; **0.334 nm** is the source's model-thickness
convention only. No automatic thickness conversion, refit, ranking, comparison,
plot or composite overlay is added. Previous graphene/MoS2 records are preserved,
including the prominent MoS2 printed-q inconsistency below.

The article is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); separate
supplement and peer-review-file license scope is unverified. No source PDFs,
full text, figures, screenshots, peer-review reports or raw-data collections are
bundled. Source transcription and software tests are not independent scientific
or native-language review. See [full hBN evidence and limits](OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)
and [v0.19.0 migration](MIGRATION_v0.19.0.md).

```sh
python -m materials_boundaries catalog observations --source-id falin_et_al_2017_hbn_mechanical_properties --text --lang en
python -m materials_boundaries catalog observations --query "hBN stiffness" --json
```

## Historical v0.18.0: catalog-only bulk elastic waves

This release adds exactly two relations and two sources: **36 mechanics claims,
50 sources**, claims schema **1.11.0**. The four observations from two studies,
six computational predictions, five synthetic temperature demos (seven branches)
and exactly eight executable composite rules remain unchanged. No wave evaluator,
material input, tensor eigensolver or wave plot is added.

For a stress-free, homogeneous unbounded 3D classical local linear-elastic
nondissipative medium with finite positive isotropic K,G and scalar density ρ,
**c_L²=(K+4G/3)/ρ**, **c_T²=G/ρ** and
**c_L/c_T∈(√(4/3),∞)**. This is the ratio range across the finite positive-energy
material class: the lower infimum is not attained and no finite common upper
bound exists; infinity is not a material value. Each fixed material has finite
direction-independent c_L and c_T, with twofold transverse degeneracy.

For the declared real tensor symmetries, **Q_ik=C_ijkl n_j n_l** has units Pa,
**Γ=Q/ρ** has units m² s⁻², and Q a=ρc²a. Phase normal n and displacement
polarization a are different variables. Strict strong ellipticity means Q(n)
is SPD for every unit n, equivalently all three squared speeds are strictly
positive in every direction. Full symmetric-strain energy SPD implies it, but
not conversely: the original project example **K=−G/3, G>0** gives Q=GI and
three equal positive squared speeds, yet negative hydrostatic strain energy.
It is not a proposed stable material. Existing full-energy stability criteria
retain their stronger meaning.

Generic anisotropic modes need not be exactly longitudinal/transverse and have
no universal fastest-longitudinal ordering. Phase speed is not a claim about
ray/group velocity. Static or isothermal moduli cannot be substituted
automatically; no thermodynamic conversion, prestress or finite-strain
extension is supplied. Chevrot–van der Hilst (2003), p. 498 Eqs. (1)–(4), and
Xiang–Qi–Wei arXiv v2, pp. 2, 4–5, support the equations; the interval and
energy proofs are original project derivations. No source figures/full text
or independent scientific/native-language review is supplied. See
[full assumptions, proofs, versions and exclusions](BULK_ELASTIC_WAVES.md) and
[v0.18.0 migration](MIGRATION_v0.18.0.md).

```sh
python -m materials_boundaries catalog claims --id isotropic_bulk_plane_wave_speeds_and_ratio --text --lang en
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang en
```

**The previous v0.17.0 release** added one study with two catalog-only monolayer MoS2
records: at that release, **4 observations from 2 studies, 48 sources**, observation schema
**1.1.0**. Existing graphene records are unchanged. MoS2 stiffness
**180 ± 60 N/m** and breaking strength **15 ± 3 N/m** use reported standard
deviations. **The printed q formula conflicts with stated q=0.95; the actual
fit constant is unresolved, and no refit is made.** See
[SD semantics, source evidence and q caveat](OBSERVATIONS.md#monolayer-mos2-bertolazzi-et-al-2011-new-records).

**Historical first-public-release baseline, 0.16.0:** 34 mechanics claims, 47 source records,
2 observations, 6 computational predictions and 5 synthetic temperature demos
(7 branches). The eight executable composite rules remain unchanged. Claims
schema was 1.10.0 at that baseline; schema versions and software versions are independent.

Original project code, documentation and original curation are [MIT-licensed](../LICENSE).
Third-party works and scientific facts are not relicensed. NIST cryogenic
coefficients and derived examples are omitted conservatively pending reuse
clarification, not because a prohibition was established. Bibliographic links
remain; see [third-party notices](../THIRD_PARTY_NOTICES.md).

The temperature models contain intentionally invented coefficients and artificial
ranges. They do not represent real materials or measured data. The linear demo
returns 15 GPa at 50 K; the overlap demo returns both 25 and 32.5 GPa at 50 K.
No branch selection, averaging, extrapolation or uncertainty band is supplied.
[Temperature guide](TEMPERATURE_MODELS.md)

```sh
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-linear-50k.json --lang en
python -m materials_boundaries temperature evaluate examples/temperature/synthetic-overlap-50k.json --lang en
python -m materials_boundaries temperature plot --output /tmp/temperature-demos --lang en
```

[Compressibility](DIRECTIONAL_COMPRESSIBILITY.md) · [Directional Poisson ratio](DIRECTIONAL_POISSON.md) · [Elastic stability](ELASTIC_STABILITY.md) · [Anisotropy](ELASTIC_ANISOTROPY.md) · [Fatigue](FATIGUE_GROWTH.md) · [Computational predictions](COMPUTATIONAL_PREDICTIONS.md) · [Bulk elastic waves](BULK_ELASTIC_WAVES.md) · [Release scope](MIGRATION_v0.21.0.md)

## Run locally

Use Python 3.10 or newer. From the repository root, these commands need no third-party runtime packages or network access:

```sh
python -m materials_boundaries validate examples/synthetic-two-phase.json --lang en
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang en --unit GPa
python -m materials_boundaries evaluate examples/synthetic-two-phase.json --lang en --json
```

Use `--lang zh`, `--lang ja`, or `--lang de` for another display language. JSON keys, enum values, formulas, numbers, and unit IDs remain unchanged. Missing translated labels fall back to English; keys absent in English receive an explicit missing marker.

## Read the synthetic result

The example is illustrative, not measured material data:

- Phase 1: `f1 = 0.5`, `K1 = 10 GPa`, `G1 = 5 GPa`
- Phase 2: `f2 = 0.5`, `K2 = 30 GPa`, `G2 = 15 GPa`
- Bulk K: Reuss `15 GPa`; HS `16.25–17.5 GPa`; Voigt `20 GPa`
- Shear G: Reuss `7.5 GPa`; HS approximately `8.37837837838–9.04761904762 GPa`; Voigt `10 GPa`
- Young's modulus E derived outer envelope: approximately `21.4488468362–23.1528046422 GPa`
- Poisson's ratio ν derived outer envelope: approximately `0.265190525232–0.293562708102`, dimensionless unit `1`

The HS interval is a theoretical constraint, not a model prediction, measurement uncertainty interval, or engineering acceptance limit. Output numbers are floating-point approximations, without interval certification.

## Interpret the derived envelopes

For the same material system, E = 9KG/(3K+G) and ν = (3K−2G)/(2(3K+G)). E uses (Klow,Glow) and (Khigh,Ghigh); ν uses (Klow,Ghigh) and (Khigh,Glow). The separate HS intervals need not have simultaneously attainable endpoints: these are conservative outer envelopes, not tight joint bounds. Unknown or violated prerequisites suppress numeric results. Unordered phases do not trigger a Reuss/Voigt fallback for E or ν.

`--unit` changes K/G/E units only; ν always uses unit `1` and must satisfy −1 < ν < 0.5. Negative or zero ν is valid. Floating-point rounding onto either excluded boundary produces `numerical_range_error` with a null result, not a clipped physical endpoint. A numerical error in either required HS result also makes dependent envelopes unavailable. Decimal computation does not certify outward-rounded endpoints.

Evaluation output has contained eight records since v0.2.0 and retains those eight scientific evaluations in v0.8.0. Select by `claim_id` and `quantity`, not by an assumed list length. Existing bulk IDs, rule IDs and numeric result shapes remain; typed metadata and evaluation schema version 1.1.0 were introduced in v0.2.0. Input schema and examples remain valid. See [v0.2.0 migration](MIGRATION_v0.2.0.md) and [model/equations](MODEL.md).

## Check applicability before using a bound

- `satisfied`: all required premises are supported by the supplied inputs and assertions within the implemented checks
- `violated`: at least one premise conflicts with the inputs; do not use the affected bound
- `unknown`: evidence for at least one premise is missing; do not assume the bound applies

Constituent isotropy and effective-medium isotropy are separate premises. All active K/G must be positive. HS and derived E/ν also require consistent ordering: `K1 <= K2` and `G1 <= G2` after labeling complete phase records, preserving each phase's paired K/G and fraction. Reuss/Voigt do not require that ordering. Read the complete assumptions in the claim catalog; the program does not independently verify specimen microstructure. Numerical strength, failure and plasticity calculations remain outside the evaluator. The fracture records below are catalog-only.

```sh
python -m materials_boundaries evaluate examples/unknown-isotropy.json --lang en
python -m materials_boundaries evaluate examples/anisotropic-constituent.json --lang en
python -m materials_boundaries catalog claims
python -m materials_boundaries catalog sources
```

For your own input, copy an example and preserve the schema's canonical keys and enum values. Use `null` or omit an optional observation when unknown; do not invent a value or turn missing evidence into `satisfied`. Unit IDs are case-sensitive: `Pa`, `kPa`, `MPa`, `GPa`. In JSON, use a decimal point. Run `validate` before `evaluate`; structural validity alone does not establish physical applicability.

See [terminology](TERMINOLOGY.md) for the four scientific categories and [language support](I18N.md) for the translation contract and QA.

## Search the read-only catalogs

Catalogs search only bundled curated records, without network access or changes to data. Existing `catalog claims` and `catalog sources` commands still return canonical JSON; `--json` explicitly selects the same output. Use `--text` for localized labels and core evidence-status explanations. Original bibliographic titles, evidence wording, and canonical IDs remain intact.

```sh
python -m materials_boundaries catalog claims --id hs_bulk_3d_two_phase --text --lang en
python -m materials_boundaries --lang en catalog claims --direction interval --text
python -m materials_boundaries catalog claims --query "bulk kochmann" --source-id kochmann_milton_2014 --json
python -m materials_boundaries catalog sources --query "Milton moduli" --year 2014 --text --lang en
python -m materials_boundaries catalog sources --role changed_assumption_comparison --license CC-BY-4.0 --text --lang en
python -m materials_boundaries --lang en catalog --help
```

`--lang` works before or after the command; if repeated, the last occurrence wins. Help labels and descriptions are localized, while command syntax and IDs remain canonical.

`--id` is an exact, case-sensitive lookup. `--query` case-folds whitespace-separated terms and requires each term to be a literal substring of the searchable stored fields: ID and title/name, plus source authors/DOI/role or claim quantity/direction/claim_type/rule/source IDs. The sixteen v0.4.0–v0.6.0 and v0.8.0 records’ curated display names are also literal search aliases in all four languages. There is no stemming, ranking, fuzzy matching, automatic translation, or network search.

Claim filters are `--direction interval|lower|upper|prediction|relation|constraint`, `--claim-type theoretical_bound|derived_outer_envelope|model_estimate|model_relation|stability_criterion`, and `--source-id` for an exact evidence source reference. Source filters are `--role`, integer `--year`, and `--license` for an exact license identifier or status. String filters are case-sensitive; all filters combine with AND and retain catalog order. An empty result is valid (exit 0); an unknown `--id`, invalid filter, or filter for the wrong catalog kind is an error (exit 2).

Reading a source, checking a formula, or passing software tests is not independent scientific proof or permission to reuse content. A search match does not establish physical applicability, and a license filter only matches recorded metadata. Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md). See [Catalog reference](CATALOG.md) for the Python API and source/claim contribution checklist.

## Catalog-only fracture models

Version 0.3.0 adds two Griffith/linear elastic fracture mechanics (LEFM) records for critical remote tensile stress: `griffith_central_crack_plane_stress` and `griffith_central_crack_plane_strain`. Both have `claim_type: model_estimate`, `direction: prediction`, `bound_kind: null`, and `evaluation_support: catalog_only`. They describe models and their assumptions; they are not new numerical evaluations.

The formula is σc = sqrt(E_prime Gc/(πa)), where E_prime = E in plane stress and E_prime = E/(1−ν²) in plane strain. E is Young's modulus in Pa, Gc is critical energy release rate in J/m², and a is half of the total central through-crack length 2a in m. Plane strain also needs dimensionless ν. The `parameters` array records each symbol, quantity, dimension, SI unit and meaning. Gc is not automatically 2γ; that equality is only the ideal purely brittle special case where creating two surfaces is the only dissipation.

The model assumes a homogeneous isotropic linear-elastic body, a central through-crack in a sufficiently wide/infinite plate, remote mode-I tension and a small yielding/process zone. Other geometries and large-scale plasticity are outside this model. Its critical stress is not a universal tensile-strength upper bound or an engineering allowable. Do not extrapolate the continuum formula to atomic crack sizes or a → 0.

Catalog retrieval does not establish any premise for a supplied specimen, produce `satisfied`/`violated`/`unknown` states, or calculate stress. Unknown or violated premises cannot justify use. `evaluate()` still returns the same eight composite evaluations under schema 1.1.0. The current claims schema is 1.11.0; stability predicates have no physical output unit. In v0.3.0 the ten-record claims catalog moved to schema 1.2.0; v0.4.0 has fifteen claims under schema 1.3.0; every claim now has explicit `claim_type`, `quantity_dimension`, `si_unit`, and `evaluation_support`.

```sh
python -m materials_boundaries catalog claims --claim-type model_estimate --direction prediction --text --lang en
python -m materials_boundaries catalog claims --id griffith_central_crack_plane_strain --json
python -m materials_boundaries catalog claims --query "model_estimate Griffith" --text --lang en
```

The canonical codes above work unchanged in every language; search does not translate display labels. The six K/G bounds use `theoretical_bound`, while E/ν retain their `derived_outer_envelope` classification. Historical Griffith attribution is separate from the modern formula cross-check. See [fracture models and evidence](FRACTURE_MODELS.md), [sources](SOURCES.md), and [v0.3.0 migration](MIGRATION_v0.3.0.md). The v0.3.0 fracture extension added no full text, publisher PDF, measurement data or reuse permission; original project work is now MIT-licensed and independent scientific review is still outstanding.

## One literature-model example

A separate [epoxy/glass example](LITERATURE_EXAMPLE.md) retains published model E/ν inputs and project-derived K/G. The 20% glass fraction, effective isotropy and perfect bonding are calculator assumptions, not specimen measurements. Temperature and material context remain unspecified.

```sh
python -m materials_boundaries evaluate examples/literature-epoxy-glass-model.json --lang en
```

```sh
python -m materials_boundaries catalog claims --claim-type stability_criterion --direction constraint --text --lang en
```

```sh
python -m materials_boundaries catalog claims --query porous --direction interval --text --lang en
```

## Search observations

`catalog observations` uses the same canonical JSON default and `--text` language selection. Observation queries search ID, name, `quantity`, `observation_type`, `study_id`, `material.name`, evidence source IDs and curated display names in all four languages. They use the same literal all-term matching. `--source-id` is shared by claims and observations; `--quantity` and `--observation-type experiment_derived_model_dependent` are observation-only, exact and case-sensitive. All filters combine with AND; unsupported catalog/filter combinations are errors. Two property records with the same study ID remain one study.

```sh
python -m materials_boundaries catalog observations --observation-type experiment_derived_model_dependent --query graphene --text --lang en
```

## Published ideal-shear predictions (v0.12.0)

Use `catalog predictions --query shimanek_v2_table2_ni_al_co --text --lang en` for three source-verified periodic
models, and `prediction plot --output /tmp/ideal-shear --lang en` for discrete
point exports. Ni / Ni11Al / Ni11Co: 5.13 / 4.58 / 5.46 GPa. This is one study's
published computational method, not commercial-alloy measurements or universal
bounds. Physical temperature, scalar pressure, magnetism and uncertainty remain
unknown; 0.08 GPa convergence is not an error bar.
[Method, provenance and limits](COMPUTATIONAL_PREDICTIONS.md).
