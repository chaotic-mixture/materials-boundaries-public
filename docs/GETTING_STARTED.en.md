# Getting started: Materials Boundaries

**Current v0.17.0** adds one study with two catalog-only monolayer MoS2
records: **4 observations from 2 studies, 48 sources**, observation schema
**1.1.0**. Existing graphene records are unchanged. MoS2 stiffness
**180 ± 60 N/m** and breaking strength **15 ± 3 N/m** use reported standard
deviations. **The printed q formula conflicts with stated q=0.95; the actual
fit constant is unresolved, and no refit is made.** See
[SD semantics, source evidence and q caveat](OBSERVATIONS.md#monolayer-mos2-bertolazzi-et-al-2011-new-records).

**Historical first-public-release baseline, 0.16.0:** 34 mechanics claims, 47 source records,
2 observations, 6 computational predictions and 5 synthetic temperature demos
(7 branches). The eight executable composite rules remain unchanged. Claims
schema is 1.10.0; schema versions and software versions are independent.

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

[Compressibility](DIRECTIONAL_COMPRESSIBILITY.md) · [Directional Poisson ratio](DIRECTIONAL_POISSON.md) · [Elastic stability](ELASTIC_STABILITY.md) · [Anisotropy](ELASTIC_ANISOTROPY.md) · [Fatigue](FATIGUE_GROWTH.md) · [Computational predictions](COMPUTATIONAL_PREDICTIONS.md) · [Release scope](MIGRATION_v0.17.0.md)

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

Catalog retrieval does not establish any premise for a supplied specimen, produce `satisfied`/`violated`/`unknown` states, or calculate stress. Unknown or violated premises cannot justify use. `evaluate()` still returns the same eight composite evaluations under schema 1.1.0. The current claims schema is 1.6.0; stability predicates have no physical output unit. In v0.3.0 the ten-record claims catalog moved to schema 1.2.0; v0.4.0 has fifteen claims under schema 1.3.0; every claim now has explicit `claim_type`, `quantity_dimension`, `si_unit`, and `evaluation_support`.

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

Use `catalog predictions --text --lang en` for three source-verified periodic
models, and `prediction plot --output /tmp/ideal-shear --lang en` for discrete
point exports. Ni / Ni11Al / Ni11Co: 5.13 / 4.58 / 5.46 GPa. This is one study's
published computational method, not commercial-alloy measurements or universal
bounds. Physical temperature, scalar pressure, magnetism and uncertainty remain
unknown; 0.08 GPa convergence is not an error bar.
[Method, provenance and limits](COMPUTATIONAL_PREDICTIONS.md).
