# Read-only catalog reference

The packaged `claims`, `sources` and `observations` catalogs are curated metadata, not a complete literature index or a comprehensive material-property database. Current v0.22.0 contains 36 mechanics claims, 52 sources and twelve observations from four studies, alongside five separate synthetic temperature demonstrations (seven branches) and twelve computational predictions in two scientific families and three explicit groups. The v0.22.0 addition is six [PA12 CF15 tensile-test summaries](PA12_CF15_TEMPERATURE_OBSERVATIONS.md) and one source, with reported MPa separate from exact SI Pa. The earlier v0.21.0 addition was six Ni11X predictions in a new explicit group; see [prediction search and boundaries](COMPUTATIONAL_PREDICTIONS.md). The earlier v0.19.0 addition was exactly two [monolayer hBN observations](OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records) and one source. The two v0.18.0 claims describe bulk elastic plane-wave speeds and strict strong ellipticity; see [bulk-wave definitions and proofs](BULK_ELASTIC_WAVES.md). The earlier hydrostatic directional compressibility and normalized tensor-class range retain their [compressibility contracts](DIRECTIONAL_COMPRESSIBILITY.md). The earlier [directional Poisson relations](DIRECTIONAL_POISSON.md) remain distinct. Searching never changes a record, fetches a source, evaluates a material, or executes a formula string. A match does not establish applicability or verification; no match does not establish absence from the scientific literature.

## CLI

From the repository root with Python 3.10+:

```sh
python -m materials_boundaries catalog claims
python -m materials_boundaries catalog sources --json
python -m materials_boundaries catalog observations --quantity breaking_strength_2d --source-id lee_wei_kysar_hone_2008 --text --lang en
python -m materials_boundaries catalog claims --id hs_bulk_3d_two_phase --text --lang en
python -m materials_boundaries catalog claims --query "bulk kochmann" --direction interval --source-id kochmann_milton_2014
python -m materials_boundaries catalog sources --query "Milton moduli" --year 2014 --text --lang de
python -m materials_boundaries catalog sources --role changed_assumption_comparison --license CC-BY-4.0
python -m materials_boundaries --lang ja catalog --help
```

`materials-boundaries` is an equivalent entry point after installation. The three catalog kinds are `claims`, `sources` and `observations`.

- Default output remains canonical JSON for backward compatibility; `--json` explicitly requests the same format. The envelope is `{"schema_version": ..., "records": [...]}` even for one match or no matches: claims use `1.11.0`, sources retain `1.0.0`, and the separate observations catalog uses `1.3.0`. The separate evaluation output stays at `1.1.0`
- `--text` selects human-readable output. `--text` and `--json` are mutually exclusive
- `--lang en|zh|ja|de` selects display language; English is the default. It may appear globally before the command or after it, and the last occurrence wins
- Help labels and descriptions are localized. Syntax, flags, filter values, record IDs, and JSON remain canonical
- Human-readable labels and core evidence-status explanations are translated. Original titles, names, bibliographic details, and evidence wording are preserved, alongside canonical IDs and status codes. The display language does not change search results

### Lookup and search

`--id ID` selects an exact, case-sensitive record ID. An ID absent from the chosen catalog is an error, even though an ordinary search with no matches is valid. An existing ID combined with a nonmatching filter yields an empty result.

`--query TEXT` splits on whitespace, applies Unicode `casefold` to terms and searchable text, and requires **every term** to match a literal substring of the searchable fields. Terms can match different fields. Empty or whitespace-only query text adds no constraint. Punctuation is literal; quotation marks passed through to the query do not create a phrase operator.

Searchable fields are deliberately limited:

| Kind | Fields |
| --- | --- |
| All three | `id`, `title` or `name` |
| Sources | `authors`, `doi`, `role` |
| Claims | `quantity`, `direction`, `claim_type`, `rule_id`, each `evidence[].source_id`, and the eighteen v0.4.0–v0.6.0, v0.8.0 and v0.9.0 records’ curated display names in en/zh/ja/de |
| Observations | `quantity`, `observation_type`, `study_id`, `material.name`, each `evidence[].source_id`, and curated display names in en/zh/ja/de |

Source years, license metadata, full evidence notes, formulas, assumptions, other localized labels, and linked paper contents are not free-text search fields. A claim or observation's source reference is searched as an ID, not as a joined source title. Observation values, uncertainty, methods, conditions and sample metadata are not indexed. There is no stemming, ranking, fuzzy matching, automatic translation, or network search.

### Structured filters

| Kind | CLI filter | Match |
| --- | --- | --- |
| Claims | `--direction interval\|lower\|upper\|prediction\|relation\|constraint` | Exact `direction` |
| Claims | `--claim-type theoretical_bound\|derived_outer_envelope\|model_estimate\|model_relation\|stability_criterion` | Exact `claim_type` |
| Claims, observations | `--source-id ID` | Exact `evidence[].source_id` reference |
| Observations | `--quantity QUANTITY` | Exact `quantity`; any nonempty string is accepted, with no match returning an empty result |
| Observations | `--observation-type TYPE` | Exact `experiment_derived_model_dependent` or `experiment_derived_tensile_test_summary` |
| Sources | `--role ROLE` | Exact `role` |
| Sources | `--year INTEGER` | Exact integer `year`; unknown (`null`) years do not match |
| Sources | `--license VALUE` | Exact `license.identifier` **or** `license.status` |

All structured string comparisons are case-sensitive. All specified predicates, including `--id` and every query term, combine with AND. Results retain original catalog order; no relevance ordering is applied. A valid role, source-reference, or license filter with no matches returns no records; it is not a record-ID lookup. Filters unsupported for the selected kind are usage errors, not ignored options. In particular, `--quantity` is not a claims filter, and `--source-id` is not a sources filter.

Exit codes for catalog operations:

- `0`: successful lookup/search, including an empty `records` list
- `2`: invalid CLI usage/filter or an unknown exact record ID

For example, `catalog claims --query no_such_term` succeeds with no records; `catalog claims --id no_such_id` and `catalog claims --year 2014` fail with exit code 2. Catalog lookup/query errors emit JSON on stderr with canonical error codes `catalog_id_not_found` and `invalid_catalog_query`, respectively. Argument-parser syntax errors use ordinary usage diagnostics.

## Python API

```python
from materials_boundaries.catalog import CatalogLookupError, query_catalog

result = query_catalog(
    "claims",
    query="bulk kochmann",
    direction="interval",
    source_id="kochmann_milton_2014",
)
assert result["records"][0]["id"] == "hs_bulk_3d_two_phase"

models = query_catalog("claims", claim_type="model_estimate", direction="prediction")
assert all(record["evaluation_support"] == "catalog_only" for record in models["records"])

sources = query_catalog("sources", year=2014, role="equation_cross_check_source")
licensed = query_catalog("sources", license="CC-BY-4.0")

observations = query_catalog(
    "observations", quantity="breaking_strength_2d",
    observation_type="experiment_derived_model_dependent",
    source_id="lee_wei_kysar_hone_2008",
)
assert len(observations["records"]) == 1
```

Signature:

```python
query_catalog(
    kind,
    *,
    record_id=None,
    query=None,
    direction=None,
    claim_type=None,
    source_id=None,
    quantity=None,
    observation_type=None,
    role=None,
    year=None,
    license=None,
)
```

`kind` must be `"claims"`, `"sources"` or `"observations"`; all filter parameters are keyword-only. `record_id` corresponds to CLI `--id`; other parameters use the same predicates as their CLI counterparts. Pass an integer for `year` and strings for text filters; `None` omits a filter. The function returns the canonical `{"schema_version": ..., "records": [...]}` dictionary with original record values and catalog order. There is no language parameter because localization is presentation-only.

An unknown exact record ID raises `CatalogLookupError`, a subclass of `ValueError`. Invalid arguments, including an unsupported kind, invalid direction, claim type or observation type, bad filter type, or filter for the wrong catalog kind, raise `ValueError`. Empty results are ordinary return values.

## Mechanical claims in v0.2.0

Version 0.2.0 added five records after the three existing bulk claims: `hs_shear_3d_two_phase`, `reuss_shear`, `voigt_shear`, `youngs_modulus_outer` and `poissons_ratio_outer`. These eight records have `quantity`, `bound_kind` and `dependencies`. The six K/G records use `scalar_modulus_bound` and an empty dependency list. E/ν use `derived_outer_envelope` and list `hs_bulk_3d_two_phase` and `hs_shear_3d_two_phase`. These reusable links are distinct from an evaluation's same-instance dependency object.

```sh
python -m materials_boundaries catalog claims --id hs_shear_3d_two_phase --text --lang en
python -m materials_boundaries catalog claims --query "effective_youngs_modulus" --json
python -m materials_boundaries catalog claims --id poissons_ratio_outer --text --lang zh
```

Derived records describe conservative outer envelopes of separately bounded K/G. They do not assert tightness or simultaneous attainability. `algebraic_derivation_from_cited_identities` records an algebraic derivation, not a new independently reviewed joint-bound theorem. Unknown or violated prerequisites suppress numerical evaluation; catalog presence alone does not supply those prerequisites.

Bound-kind and dependency labels are localized in text output; canonical IDs and original evidence wording remain unchanged. `bound_kind` and `dependencies` are not dedicated filters or indexed fields. Version 0.3.0 adds indexed `claim_type` and its exact filter, so `--claim-type derived_outer_envelope` selected the two original derived records directly; it now also selects the catalog-only porous Young record. Always inspect `evaluation_support`. See the historical [v0.2.0 migration](MIGRATION_v0.2.0.md) and [v0.3.0 migration](MIGRATION_v0.3.0.md); the porous extension is in [v0.6.0 migration](MIGRATION_v0.6.0.md), the separate observation extension is in [v0.7.0 migration](MIGRATION_v0.7.0.md), and the historical strict-stability extension is in [v0.8.0 migration](MIGRATION_v0.8.0.md).

## Catalog-only fracture models in v0.3.0

The v0.3.0 claims catalog contained ten records: the eight executable composite claims and two Griffith/linear elastic fracture mechanics (LEFM) model estimates for a central through-crack under remote tensile loading: `griffith_central_crack_plane_stress` and `griffith_central_crack_plane_strain`. Their quantity is `critical_remote_tensile_stress`. Neither model is registered with `evaluate()`. This is a narrow knowledge-catalog extension, not a fracture simulator or a new material-input format.

Every catalog claim declares:

| Field | Meaning in this release |
| --- | --- |
| `claim_type` | `theoretical_bound` for six K/G bounds; `derived_outer_envelope` for E/ν; `model_estimate` for the two fracture models |
| `quantity_dimension` / `si_unit` | `pressure` / `Pa` for K/G/E and critical remote tensile stress; `dimensionless` / `1` for ν |
| `evaluation_support` | `composite_evaluate` for the existing eight; `catalog_only` for the fracture models |
| `bound_kind` | Existing `scalar_modulus_bound` or `derived_outer_envelope` values remain unchanged; fracture models use null |
| `direction` | Existing `interval`, `lower`, and `upper` remain unchanged; fracture models use `prediction` |

A model's `parameters` array describes symbols with `symbol`, `quantity`, `dimension`, `si_unit`, and `meaning`. E is positive Young's modulus in Pa, Gc is positive critical energy release rate in `J/m^2` (J/m²), and a is the positive half of total crack length 2a in m. Plane strain additionally requires dimensionless Poisson's ratio ν with −1 < ν < 0.5. These definitions are catalog metadata, not numerical inputs accepted by the current composite evaluator.

The documented equation is σc = sqrt(E_prime Gc/(πa)), with E_prime = E for plane stress and E_prime = E/(1−ν²) for plane strain. It describes a sufficiently wide/infinite homogeneous isotropic linear-elastic body with a central through-crack, mode-I remote tension, quasi-static small-strain loading normal to traction-free crack faces, and a negligible yielding/fracture-process zone relative to the crack and body dimensions. The approximation uses 2a much smaller than the plate width and a specified Gc at crack initiation. Finite-width, edge-crack, mixed-mode, dynamic, large-scale yielding, anisotropic, and atomistic cases require other models. Gc is not silently replaced by 2γ: Gc = 2γ is an ideal purely brittle special case in which creating the two new surfaces is the only dissipation.

A catalog equation and list of assumptions do not establish supplied conditions. These records produce no per-instance `satisfied`/`violated`/`unknown` state and no numerical result. Unknown or violated physical premises cannot justify using the equation. The predicted critical stress is neither a universal tensile-strength upper bound nor an engineering allowable; the continuum expression cannot be extrapolated to atomic crack sizes or a → 0.

```sh
python -m materials_boundaries catalog claims --claim-type model_estimate --direction prediction --text --lang en
python -m materials_boundaries catalog claims --query "model_estimate Griffith" --json
python -m materials_boundaries catalog claims --claim-type theoretical_bound --json
```

Each query selects the same records in every display language. The first query now also includes the two v0.4.0 ideal-strength estimates; the Griffith query remains specific to its two records. `claim_type` codes, units, record IDs, and query semantics are untranslated; curated display-name aliases added in v0.4.0 are searchable, but searching an arbitrary translated label is not equivalent to filtering by its canonical code. `evaluation_support`, dimensions, units, parameters, formulas, and assumptions are not additional indexed fields or dedicated filters. A catalog `rule_id` names a record's rule/model but does not promise executable support; inspect `evaluation_support`.

Historical Griffith attribution is distinct from verification of the modern Gc/LEFM formulation. Read the recorded source/version, locator, inspection scope, and remaining gaps in each model's evidence, the [fracture model guide](FRACTURE_MODELS.md), and the [source notes](SOURCES.md). Catalog inclusion does not upgrade historical metadata to full-text verification.

## Catalog-only strength and model relations in v0.4.0

The v0.4.0 catalog had 15 claims and 17 sources. Four `model_estimate` records use `direction: prediction`; three `model_relation` records use `direction: relation`. All seven are `catalog_only` with null `bound_kind`. Relations distinguish conditional identities or analytical approximations from a material-strength prediction or bound. The eight executable records are unchanged.

New quantities include ideal resolved shear stress and ideal cohesive traction (Pa), Mode-I stress intensity (`stress_intensity`, `Pa*m^0.5`), Mode-I energy release (`energy_per_area`, `J/m^2`), and finite-width geometry factor (`dimensionless`, `1`). Parameter signatures are validated per model family; schema validity does not certify physical applicability.

The five new records have curated `catalog_name_<id>` entries in the existing locale dictionary. Text output shows these alongside canonical names. Claim queries search all four languages’ authored names literally, with the same casefold/all-terms semantics; `--lang` never changes the matching set. Source search and source titles/DOIs are unchanged. These aliases are not automatic translation, inferred synonyms or full-text paper search. Translation review remains pending.

```sh
python -m materials_boundaries catalog claims --claim-type model_relation --direction relation --text --lang en
python -m materials_boundaries catalog claims --query "有限宽度" --text --lang zh
```

See [five-record scientific overview](MECHANICS_CATALOG.md) and [v0.4.0 migration](MIGRATION_v0.4.0.md), including the finite-width source discrepancy and UBER energy convention.

## Catalog-only stability criteria in v0.5.0

The v0.5.0 catalog had 19 claims and 18 sources. Four `stability_criterion` records use `direction: constraint`, `quantity: homogeneous_elastic_stability`, `quantity_dimension: logical_predicate` and `si_unit: null` (no physical output unit applies). They have null `bound_kind`, empty dependencies and `evaluation_support: catalog_only`. The prior 15 claims and 17 source records are unchanged.

The new `criterion` object holds engineering-Voigt conventions, the full symbolic stiffness matrix, an all-conditions conjunction and strict inequality metadata. Input C components use Pa; quadratic and cubic expressions use Pa^2 and Pa^3. They are display metadata and are never evaluated or plotted. Exact family contracts guard assumptions, parameters, matrix symmetry, inequalities and units. General positive definiteness allows any orthonormal Cartesian axes; the cubic, hexagonal and orthorhombic templates require symmetry-aligned axes.

Null output units render as localized “not applicable,” while the inequality units, matrices, conventions and criterion-specific warning remain visible. Four-language display-name aliases use the existing literal-search rules; `--query` does not search the new formulas, matrices or inequality expressions.

```sh
python -m materials_boundaries catalog claims --claim-type stability_criterion --direction constraint --text --lang en
python -m materials_boundaries catalog claims --query "正交晶系" --text --lang zh
```

There is no public stiffness-input or stability evaluator API. Strict positivity concerns stress-free homogeneous harmonic elasticity only, not phonons, finite load or strength. Equality does not satisfy the strict criterion and does not automatically establish a marginal positive-semidefinite matrix. See [scientific criteria and source](ELASTIC_STABILITY.md) and [v0.5.0 migration](MIGRATION_v0.5.0.md).

## Historical catalog-only porous intervals in v0.6.0

The v0.6.0 catalog had **22 claims and 19 sources** under claims schema **1.5.0**. The original 19 claim records and 18 source records are unchanged. Three new `catalog_only` records describe isotropic solid/void finite-porosity intervals: `hs_porous_bulk_3d_solid_void`, `hs_porous_shear_3d_solid_void` and `hs_porous_youngs_outer_3d_solid_void`.

Bulk and shear reuse `theoretical_bound` / `scalar_modulus_bound`; Young reuses `derived_outer_envelope` and depends on the two new porous claims. All use `direction: interval`, pressure dimension and Pa. Thus a bound type, pressure unit or interval direction does not imply executable support. `--claim-type theoretical_bound` now selects eight records; `--claim-type derived_outer_envelope` selects three. Only the original eight `composite_evaluate` records belong to the runtime registry.

Parameters are the same solid's positive `Ks,Gs` and dimensionless porosity `p` (void fraction). The source's solid fraction is `1-p`. At `0<p<1`, disconnected-solid geometries require zero universal lower endpoints; at `p=0`, both endpoints equal the pure-solid values. `p=1` has formal zero stiffness with no Poisson ratio or specific moduli. Isotropic positive-stiffness regularization, conditional density, full finite-porosity expressions and lack of a joint-attainment promise are part of the documented scope.

```sh
python -m materials_boundaries catalog claims --id hs_porous_bulk_3d_solid_void --text --lang en
python -m materials_boundaries catalog claims --query porous --direction interval --json
python -m materials_boundaries catalog sources --id roberts_garboczi_2002_porous --text --lang en
```

Four-language curated display names use the existing literal aliases, with no new filter or execution API. The [synthetic porous illustration](../examples/catalog/porous-synthetic.json) is documentation-only and must not be sent to `validate`, `evaluate` or comparison builders. Read [formulas, endpoints and source details](POROUS_BOUNDS.md) and [migration](MIGRATION_v0.6.0.md).

## Four additional strict stability templates in v0.8.0

Claims schema **1.6.0** appends `tetragonal_i_born_stability`, `tetragonal_ii_born_stability`, `rhombohedral_i_born_stability` and `rhombohedral_ii_born_stability`, bringing the total to **26 claims**, including **eight stability predicates**. All prior 22 records, all 20 sources and both observations remain unchanged. Each new claim cites the already-cataloged `mouhat_coudert_2014_elastic_stability` source with its own exact equation locator; there is no new source or source-record edit.

The existing predicate contract remains: `claim_type: stability_criterion`, `direction: constraint`, `quantity_dimension: logical_predicate`, null output `si_unit` and `bound_kind`, empty dependencies and `evaluation_support: catalog_only`. Explicit schema alternatives tie `elastic_symmetry` to its exact matrix, independent parameter set and full strict inequality set. Readers must not relax those alternatives or infer runtime support from a formula, crystal class, or recognized rule ID.

The source calls the classes tetragonal I (4/mmm), tetragonal II (4/m), rhombohedral I (−3m) and rhombohedral II (−3). Trigonal is an alias for the rhombohedral entries. Tetragonal C66 is independent; rhombohedral C66=(C11−C12)/2 is dependent. The rhombohedral II bound involves the combined C14²+C15², and the coupled bounds have an essential factor 2. Determinant positivity alone does not certify strict stability. Full matrices, Cartesian axis settings, engineering shear convention, PSD/equality distinctions and stress-free homogeneous harmonic exclusions remain attached to the records and documented in [Elastic stability](ELASTIC_STABILITY.md).

```sh
python -m materials_boundaries catalog claims --id tetragonal_ii_born_stability --text --lang en
python -m materials_boundaries catalog claims --query "rhombohedral" --text --lang de
python -m materials_boundaries catalog claims --claim-type stability_criterion --source-id mouhat_coudert_2014_elastic_stability --json
```

All four authored display names are literal aliases in each language; `--lang` changes presentation only. No new filter, stiffness-input API, applicability state, solver or plot is added. The original eight evaluator outputs retain values, ordering, conditions and evidence with only engine version 0.8.0. See [migration](MIGRATION_v0.8.0.md); translations and scientific curation still await independent review.

## Separate observations in v0.7.0

Two `experiment_derived_model_dependent` observations from the same Lee–Wei–Kysar–Hone (2008) study describe freestanding monolayer graphene: in-plane stiffness 340 ± 50 N/m and model-inferred breaking strength 42 ± 4 N/m. Both were introduced as `catalog_only` under observation schema 1.0.0 (their record objects remain unchanged in the current 1.3.0 envelope); no claim is added or reclassified. In v0.7.0 the 22 claims stayed unchanged under schema 1.5.0, and the source catalog appended one record to its unchanged original 19. The historical v0.8.0 claim count/schema were 26/1.6.0; both observation records and all 20 sources remain unchanged.

`reported_plus_minus_unspecified` means that the reported ± type and coverage are unverified, not a standard deviation, confidence interval or bound. A separate stiffness-fit distribution has mean 342 N/m, SD 30 N/m and 67 fits on 23 membranes from two flakes; these counts must not be used for breaking strength. Temperature, atmosphere, humidity and loading rate remain unknown. Main-text passages were checked; the supplement was inaccessible and unread.

```sh
python -m materials_boundaries catalog observations --id lee_2008_graphene_in_plane_stiffness_2d --text --lang en
python -m materials_boundaries catalog observations --query "graphene strength" --observation-type experiment_derived_model_dependent --json
```

The shared study ID does not supply independent replication. The source's AFM/membrane inference and second Piola–Kirchhoff/Lagrangian convention remain attached to the result. N/m quantities have no default thickness or GPa conversion; matching units alone do not establish comparable properties. Observation records are not executable instances, applicability checks or comparison overlays. See [observations and locators](OBSERVATIONS.md) and [v0.7.0 migration](MIGRATION_v0.7.0.md).

## Closed monolayer MoS2 addition in v0.17.0

At v0.17.0, the separate observations envelope advanced to **1.1.0**, retaining both
original graphene objects exactly and adding two closed-family MoS2 records
from `bertolazzi_brivio_kis_2011`. Values are **180 ± 60 N/m** stiffness and
**15 ± 3 N/m** breaking strength, with `reported_standard_deviation` and null
confidence/coverage fields. At that release four property records represented two studies.
Graphene's existing statistical type remains `reported_plus_minus_unspecified`.

The MoS2 branch keeps unknown stress/strain measures and test environment null,
a typed 2 μm/s vertical probe translation speed, and nine study/stiffness
membranes without inventing a failure-event count. Printed q formula
1/(1.05 − 0.15ν − 0.16ν²), assumed ν=0.27 and stated q=0.95 are separate,
inconsistent source statements; arithmetic approximately 1.002168693051764 is
only an audit note and actual fit q remains unresolved. They do not create an
executable fit, correction or conversion. The proof-formatted EPFL A–G artifact
is the inspected source; final publisher text and supplement are unverified.

```sh
python -m materials_boundaries catalog observations --source-id bertolazzi_brivio_kis_2011 --text --lang en
python -m materials_boundaries catalog observations --query "MoS2 stiffness" --json
```

Observation IDs, units and JSON stay language-independent. Existing literal
AND-based query and exact filters apply. No plots, composite overlays, material
ranking or default thickness are added; unknown conditions cannot establish
matched studies. See [full provenance and semantics](OBSERVATIONS.md) and
[version migration](MIGRATION_v0.17.0.md). This narrow scientific-contract change
does not alter contribution forms or the existing mechanics, predictions,
temperature and eight-rule composite contracts.

## Closed monolayer hBN addition in v0.19.0

The observation envelope advances to **1.2.0** through
`falin_2017_hbn_monolayer_indentation_v1`, a separate closed method family with
exactly two records from `falin_et_al_2017_hbn_mechanical_properties`:
**289 ± 24 N/m stiffness** and **23.6 ± 1.8 N/m breaking strength**. The new total
is six observations from three studies; all four earlier observation objects
are preserved.

SD meaning is backed specifically by the publisher-linked peer-review author
response, PDF p. 8, Reviewer #1 question 3, not main-text ± notation alone.
Eleven tested sheets are explicitly associated with the stiffness average;
curve/failure-event totals remain null, and typically five indentations per
sheet is not an exact 55-curve dataset. Source-printed N/m values are retained
without using 0.334 nm as a default conversion thickness.

The strength reduction is a nonlinear FEM **volume average of under-indenter
stresses**, distinct from the supplement's **maximum Von Mises stress**
diagnostic. Finite-strain stress/strain conventions remain unknown. Ambient is
qualitative; numeric temperature, pressure, humidity and gas composition stay
null. **0.5 μm/s** is probe translation velocity, not strain rate. The printed
q formula uses **1.049**, ν=0.211; **0.9898768854482001** is curator arithmetic
only, with no separate printed q or verified actual fit constant. No hBN
q-mismatch claim is made, and the MoS2 mismatch is preserved.

```sh
python -m materials_boundaries catalog observations --source-id falin_et_al_2017_hbn_mechanical_properties --text --lang en
python -m materials_boundaries catalog observations --query "hBN stiffness" --json
```

The existing literal AND query, exact filters, catalog order and canonical JSON
behavior are unchanged. There is no evaluator, refit, thickness conversion,
plot, ranking, comparison or composite overlay. The article's CC BY 4.0 status
does not establish separate supplement/peer-review licensing; no source-media
or report redistribution is added. See [full observation contract](OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)
and [migration](MIGRATION_v0.19.0.md).

## Evidence and reuse boundaries

Reading status records the inspected material and its limits. Formula cross-checking and software tests do not establish an independently reviewed scientific proof, verify a real specimen's premises, or imply peer review. The composite calculator retains its conservative positive isotropic scope and eight evaluations from v0.2.0. Version 0.3.0 added two fracture estimates; v0.4.0 adds two strength estimates and three model relations, all catalog-only. Version 0.5.0 appended four stability predicates and v0.6.0 adds three porous intervals without changing that calculator. Version 0.8.0 adds four further strict stability templates under the same catalog-only boundary. See [Model](MODEL.md) and [Sources](SOURCES.md).

A license filter is only a comparison against recorded metadata, not a permission decision. Access to a source, its presence in this catalog, or inspection of its text grants no reuse rights. Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md). The observation catalog adds brief published numerical summaries, not paper full text, PDFs, figures, raw experimental data or claims of scientific completeness. Translations remain machine-assisted and unreviewed; see [Language support](I18N.md).

## Minimal source/claim/observation contribution checklist

For the current development workflow, see the [contribution guide](../CONTRIBUTING.md)
and [review template](CATALOG_CONTRIBUTION_TEMPLATE.md). Run
`python scripts/validate_catalogs.py` with the complete `.[dev]` extra installed
before the full test suite. Supported existing-contract records and evidence
additions do not need old test-code, runtime, renderer, schema or CLI edits;
genuinely new scientific contracts remain separate reviewed changes.

- Preserve unique canonical IDs and schema fields; every claim or observation evidence reference must resolve to a source record, and every dependency claim ID must resolve to the appropriate reusable claim
- Record the exact source/version, bibliographic metadata, inspected location, reading scope, and provenance. Keep unknown values and verification gaps explicit; do not upgrade abstract access to full-text or proof review
- Set `claim_type`, `quantity_dimension`, `si_unit`, and `evaluation_support` explicitly. Preserve legacy `bound_kind` values on existing records; use null for model estimates, relations and stability criteria. A predicate has logical_predicate dimension and no physical output SI unit; its stiffness parameters and inequality margins retain explicit physical units. For a model, document every parameter and unit, geometry, loading, material idealization, and where its continuum assumptions fail
- State a claim's assumptions and implemented scope separately from a paper's broader subject. Distinguish formula evidence, historical attribution, context, and parameter provenance; do not label model inputs as measurements
- Verify and record the specific reuse terms, or leave permission unverified. Do not bundle full texts, figures, or third-party datasets without appropriate authorization; catalog inclusion does not extend the project MIT license to source works
- For observations, retain study identity, distinct quantity/dimension/unit, specimen/method context, the source's uncertainty notation, sample-statistic scope and unverified conditions. Do not relabel a model-dependent inference as a direct stress measurement or count two properties as independent studies
- Run the existing schema/reference and software tests, add focused search tests when relevant, and preserve four-language label parity and canonical data. Passing tests does not replace independent scientific or translation review

## Separate synthetic temperature demonstrations

Five original synthetic polynomial models with seven artificial branches live
in `temperature_models`, using the separate `temperature` CLI namespace. They
are not measurements, empirical source fits or theoretical bounds. They never
extend `composite_evaluate`. Use `temperature catalog` for canonical records and
`--text --lang` for authored descriptions. The v0.16.0 source catalog preserved 46
bibliographic records and added one original demonstration-provenance record.
The v0.17.0 MoS2 source brought the total to 48; the current v0.22.0 catalog has 52 sources, with the synthetic contents unchanged. NIST cryogenic coefficients and derived outputs are omitted
conservatively; bibliographic references remain. See [temperature contracts](TEMPERATURE_MODELS.md)
and [rights scope](../THIRD_PARTY_NOTICES.md).

## v0.11.0 catalog-only elastic anisotropy

Two `model_relation` definitions add no executable rules: Zener A and universal
AU. `index_range` distinguishes their scoped mathematical ranges from their
formulas: Zener lower zero is open; AU lower zero is closed. `unbounded` is an
explicit upper status, not unknown. Four-language text displays the range and
isotropy equality; canonical JSON and IDs remain language-independent.
See [the anisotropy guide](ELASTIC_ANISOTROPY.md) for full conditions, source QA,
strict schema contracts and unchanged numerical/plot boundaries.

## Separate computational predictions (v0.12.0)

`catalog predictions` supports `--id`, `--query`, `--source-id` and `--quantity`.
Four authored names are searchable, and `--text --lang zh|en|ja|de` selects display
labels without changing canonical JSON. It reads `computational_predictions.json`
under its own schema; no claim, observation or runtime-bound classification is
changed. Filtered views retain complete group/protocol metadata; group member IDs
refer to the full installed catalog, not necessarily the filtered records.
Only `prediction plot --group-id ID` produces an explicitly curated comparison.
See [the scientific, search and export contract](COMPUTATIONAL_PREDICTIONS.md).

## Directional Poisson contracts (v0.15.0)

The two new `model_relation` families use the distinct dimensionless quantity
`directional_poissons_ratio`. Their closed `directional_contract` separates
unbounded range over varying finite full-SPD 3D tensors from finite attained
extrema for each fixed tensor. It is neither the isotropic effective-ratio
interval nor the nonnegative anisotropy `index_range`. Unknown bounds and
attained infinity are not substitutes for unboundedness.

The second family records reciprocity and the strict modulus-dependent pair
constraint. Its one dependency must resolve to the directional definition family,
including when same-contract records use fresh IDs. The schema enforces record
shape and exact scientific metadata; dependency-free runtime guards also enforce
metadata types, finiteness and dependency family. Filtered text rendering resolves
omitted definitions against the packaged catalog. Full catalog validation still
checks references, aliases and the exact eight-rule registry. No display formula
is executed and no tensor API or directional plot is introduced.

```sh
python -m materials_boundaries catalog claims --query "directional Poisson" --text --lang en
python -m materials_boundaries catalog claims --id directional_poisson_reciprocity_energy_constraint --json
```

See [the complete derivations and source limits](DIRECTIONAL_POISSON.md).

## Hydrostatic compressibility contracts (v0.16.0)

Exactly two additional catalog-only `model_relation` records use
`direction: relation` and `bound_kind: null`:

| Record | Quantity | Dimension / canonical SI unit |
| --- | --- | --- |
| `directional_linear_compressibility_hydrostatic_relation` | `directional_linear_compressibility` | `inverse_pressure` / `Pa^-1` |
| `normalized_directional_compressibility_range` | `normalized_directional_linear_compressibility` | `dimensionless` / `1` |

The dedicated closed `hydrostatic_compressibility_contract` keeps dimensional
hydrostatic definitions separate from the normalized tensor-class theorem.
β(n)=nn:S:I may be negative although κ=I:S:I>0. Every orthonormal triad sums
to κ. For one fixed finite full-SPD tensor, B=S:I has finite attained spectral
extrema. Across unrestricted tensors every finite β/κ is attainable, even at
fixed positive κ; neither infinity is attained. Cubic/isotropic β/κ is exactly
1/3. The strict energy inequality β²<κ/E uses the same S and n and is necessary,
not sufficient for full SPD. At most two negative principal values is not a
restriction to two arbitrary negative directions.

A normalized record's one definition dependency resolves by ID to the matching
hydrostatic family, including supported fresh IDs. Record reading and text
rendering use a dependency-free metadata guard; full development validation also
checks cross-record references, labels and the exact eight executable pairs.
Formulas, engineering shear audit, source attribution, project-derivation status
and scope exclusions are scientific metadata, not a tensor calculator. The
closed contract must retain g/2 off-diagonals, σ=−pI, full inverse compliance,
finite real 3D SPD and the fixed-temperature stress-free infinitesimal scope.
No new filter, material-input format, evaluator or plot is added.

```sh
python -m materials_boundaries catalog claims --query compressibility --text --lang en
python -m materials_boundaries catalog claims --id directional_linear_compressibility_hydrostatic_relation --text --lang ja
python -m materials_boundaries catalog claims --id normalized_directional_compressibility_range --json
```

Authored en/zh/ja/de names remain literal aliases and display metadata; canonical
JSON and scientific IDs/units do not depend on language. See [definitions,
original proofs, source inspection limits and four-language caveats](DIRECTIONAL_COMPRESSIBILITY.md)
and [migration](MIGRATION_v0.16.0.md). No independent scientific or native-language
review, physical realization, or source-redistribution clearance is inferred.

## Bulk elastic-wave relations (v0.18.0)

Exactly two appended `model_relation` / `relation` records have null
`bound_kind` and `evaluation_support: catalog_only`:

- `isotropic_bulk_plane_wave_speeds_and_ratio`: c_L²=(K+4G/3)/ρ,
  c_T²=G/ρ and the original project ratio-range derivation
- `christoffel_tensor_strong_ellipticity`: Q_ik=C_ijkl n_j n_l,
  Γ=Q/ρ, Q a=ρc²a and the strict all-direction rank-one criterion

The model is finite real 3D, stress-free, homogeneous, local linear-elastic,
purely mechanical and nondissipative, with both minor and major stiffness
symmetries and finite positive scalar density. Q has units Pa; Γ and c² have
units m² s⁻². Phase normal n is distinct from displacement polarization a.
No static/isothermal-to-acoustic substitution is supplied.

For finite positive K,G,ρ the isotropic material-class ratio is the open range
(√(4/3),∞), with an unattained infimum and no attained infinity. Each fixed
material has finite direction-independent speeds and a twofold transverse
eigenspace. The all-direction criterion instead permits any tensor whose
Q(n) is SPD for every unit n; zero or negative squared speeds fail it. Full
symmetric-strain energy SPD implies this criterion, but not conversely:
K=−G/3, G>0 gives Q=GI and negative hydrostatic energy. Existing full-energy
stability records are not weakened. General anisotropic modes are not asserted
to be exact longitudinal/transverse modes with a universal speed ordering;
phase-speed relations do not supply ray/group velocities.

The closed `bulk_wave_contract` records the shared assumptions, exclusions,
strict criteria, tensor contraction/normalization, degeneracy and source-versus-
project attribution. Both additions have `dependencies: []`; neither draws
runtime composite-bound results into a wave prediction. The first uses quantity
`isotropic_bulk_phase_speed_ratio` with dimension `dimensionless` and SI unit
`1`; the second uses `bulk_phase_speed_squared` with `speed_squared` and
`m^2 s^-2`. Parameter metadata distinguishes `mass_density` (`kg m^-3`),
`speed` (`m s^-1`) and `speed_squared` (`m^2 s^-2`) from pressure moduli.

The claim envelope advances to 1.11.0 (36 claims); sources stay 1.0.0 (50
records). Authored four-language display names, cautions and literal aliases do
not change canonical IDs, equations, units, source identity or search semantics.
Neither displayed formula strings nor descriptive wave metadata are evaluated.
There is no wave material input, eigensolver, plot, specimen stability decision
or extra executable composite rule. Existing observations, including the
visible unresolved MoS2 q discrepancy, remain unchanged.

```sh
python -m materials_boundaries catalog claims --id isotropic_bulk_plane_wave_speeds_and_ratio --text --lang en
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang de
python -m materials_boundaries catalog sources --id chevrot_vanderhilst_2003 --json
```

See [the complete scientific/source contract](BULK_ELASTIC_WAVES.md) and
[migration](MIGRATION_v0.18.0.md). Source equation inspection and original
algebra are not independent scientific/native-language review or redistribution
permission; no source full text, PDF, page image or figure is bundled.


## Separate observation inspection exports (current v0.22.0)

`observation inspect --output DIR` exports source-ordered inspection cards/tables
for all 12 observation records, separately from `catalog` output. Inspection
schema 1.1.0 retains the six old 2D facets and adds six PA12 3D chamber-condition
facets with reported MPa and explicit exact SI Pa re-expression. It accepts
repeatable exact `--id`, exact `--source-id`, exact `--quantity` and
`--group-by study|quantity`; filters combine with AND and retain packaged order.
Unlike catalog queries, it rejects empty selections and does not accept
`--query`. JSON/CSV audit exports and localized SVG/HTML retain the source-specific
inference, uncertainty and evidence contract without numerical comparison,
aggregation or a new evaluator. Regenerate stale bundles; never relabel their
versions. CSV consumers must distinguish reported `unit` from `si_unit` and
read the new source-string, normalization, dataset/protocol/cell and temperature
columns by name. [Usage and audit contract](OBSERVATION_INSPECTION.md)


## Closed PA12 CF15 observation family (v0.22.0)

The exact quantity `ultimate_tensile_strength_as_reported_3d` and observation
type `experiment_derived_tensile_test_summary` select the six Table 3 summaries
from source `ciganas2026polym18050563`. They are 3D pressure-dimension records
in reported MPa, with exact SI Pa separately stored. The default catalog has
12 observations; older quantity/type/source selections preserve old science.
Exact selectors and literal search retain AND semantics and packaged order.

```sh
python -m materials_boundaries catalog observations --source-id ciganas2026polym18050563 --text --lang en
python -m materials_boundaries catalog observations --observation-type experiment_derived_tensile_test_summary --json
python -m materials_boundaries catalog observations --quantity ultimate_tensile_strength_as_reported_3d --json
```

No quantitative temperature-range query, interpolation, stress calculation,
N/m conversion, confidence interval or universal bound is implied. The full
catalog requires six unique approved dataset/quantity/source-cell identities
in source-column order;
renamed duplicates cannot add evidence. A selected subset or unchanged scientific
payload under a renamed ID is valid. Other temperatures, materials and protocols
require reviewed admission; existing supported-family appendability remains.
Source-specific guards also preserve revision/PDF/rights metadata. See the
[full source contract](PA12_CF15_TEMPERATURE_OBSERVATIONS.md) and
[migration](MIGRATION_v0.22.0.md).
