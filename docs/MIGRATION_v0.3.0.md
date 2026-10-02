# Migrating from v0.2.0 to v0.3.0

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


Version 0.3.0 adds two catalog-only Griffith/LEFM central-through-crack model estimates for critical remote tensile stress, one for plane stress and one for plane strain. It adds explicit claim classification, quantity dimensions, canonical SI units, and executable-support metadata to the claims catalog. This is a knowledge-catalog extension: it does not add a fracture calculator, new numerical material inputs, or specimen validation.

## Versioned contracts

| Contract | v0.2.0 | v0.3.0 |
| --- | --- | --- |
| Package version | 0.2.0 | 0.3.0 |
| Claims catalog/schema | 1.1.0, eight records | 1.2.0, ten records |
| Evaluation output schema | 1.1.0, eight evaluations | Unchanged: 1.1.0, eight evaluations |
| Input instance schema | Existing composite input | Unchanged |
| Sources catalog/schema | 1.0.0 | 1.0.0, additional source metadata |
| Locale dictionary schema | 1.0.0 | 1.0.0, more keys |

The original eight claim records advance their per-record `version` from `1.0.0` to `1.1.0` for the added metadata; their scientific definitions are unchanged. The two new model records begin at per-record `version: 1.0.0`. These record versions are separate from package and catalog schema versions.

Existing composite inputs, examples, output IDs, rule IDs, numerical result shapes, ordering, units, applicability states, and computation states retain their v0.2.0 contract. The evaluation envelope reports `engine_version: "0.3.0"`, so the complete JSON payload is not byte-identical to a v0.2.0 run; its eight scientific evaluation payloads remain unchanged. `evaluate()` and `evaluate` CLI output do not gain fracture evaluations or catalog classification fields. Do not assume that evaluation and catalog schema versions must be equal. The earlier three-to-eight evaluation migration remains documented in [v0.2.0 migration](MIGRATION_v0.2.0.md).

## New catalog fields and categories

Every catalog claim has `claim_type`, `quantity_dimension`, `si_unit`, and `evaluation_support`:

| Records | `claim_type` | `quantity_dimension` / `si_unit` | `evaluation_support` |
| --- | --- | --- | --- |
| Six HS/Reuss/Voigt K/G bounds | `theoretical_bound` | `pressure` / `Pa` | `composite_evaluate` |
| Young's modulus outer envelope | `derived_outer_envelope` | `pressure` / `Pa` | `composite_evaluate` |
| Poisson's ratio outer envelope | `derived_outer_envelope` | `dimensionless` / `1` | `composite_evaluate` |
| Two critical-stress fracture models | `model_estimate` | `pressure` / `Pa` | `catalog_only` |

`bound_kind` is retained for compatibility. The six K/G records still use `scalar_modulus_bound` and E/ν still use `derived_outer_envelope`; the two model records use null. Its old values are not renamed to the new `claim_type` codes. Existing `direction` values stay unchanged; model records use `prediction`. Existing dependency lists remain unchanged, and the models have no composite HS dependencies. The fracture E parameter is not automatically taken from a composite envelope.

Model records include a `parameters` array whose entries have `symbol`, `quantity`, `dimension`, `si_unit`, and `meaning`. E, Gc, and a mean positive Young's modulus, positive critical energy release rate, and positive half of total crack length 2a; ν with −1 < ν < 0.5 is additionally specified for plane strain. Canonical parameter unit IDs are `Pa`, `J/m^2`, `m`, and dimensionless `1`. Keep their stored machine-readable spellings unchanged. Top-level `quantity_dimension` describes the output quantity, while each parameter has its own dimension.

## Formula and applicability boundary

σc = sqrt(E_prime Gc/(πa)), where E_prime = E for plane stress and E_prime = E/(1−ν²) for plane strain. The idealized central through-crack is loaded in remote mode-I tension in a sufficiently wide/infinite homogeneous isotropic linear-elastic body. The linear-elastic approximation requires a sufficiently small yielding/process zone and excludes large-scale plasticity. Gc is not generally 2γ; that equality applies only to the ideal purely brittle special case with surface creation as the only dissipation.

The equation estimates critical remote stress conditional on these premises. It is not a universal upper bound on tensile strength, an engineering allowable, a prediction for arbitrary geometry, or a valid continuum limit as a approaches atomic dimensions or zero. Historical Griffith attribution and a modern formula cross-check are different evidence roles; preserve each source's actual reading scope and verification gaps.

The records are `catalog_only`. They do not check a supplied instance, emit applicability states, or compute numerical predictions. A schema-valid record and a displayed premise do not establish that premise for a real body. Unknown or violated premises cannot justify use. The existing composite evaluator continues to withhold numerical values for unknown/violated prerequisites under its existing rules.

## Search and Python API

The additive claims-only filter `--claim-type` accepts exactly `theoretical_bound`, `derived_outer_envelope`, or `model_estimate`. `--direction` also accepts `prediction`. The Python keyword is `claim_type`. Values are case-sensitive, are identical in all four languages, and combine with other filters using AND. Unsupported values and applying a claims-only filter to sources are errors. Empty matches remain successful queries.

```sh
python -m materials_boundaries catalog claims --claim-type model_estimate --text --lang en
python -m materials_boundaries catalog claims --direction prediction --json
python -m materials_boundaries catalog claims --query "model_estimate Griffith" --text --lang zh
```

```python
from materials_boundaries.catalog import query_catalog

models = query_catalog("claims", claim_type="model_estimate", direction="prediction")
assert models["schema_version"] == "1.2.0"
assert len(models["records"]) == 2
assert all(record["evaluation_support"] == "catalog_only" for record in models["records"])
```

`claim_type` is also included in the existing literal, case-folded, all-terms free-text query. Display translations are not indexed. No full-text paper search, ranking, inference, network request, or formula execution is added. See the complete [catalog reference](CATALOG.md).

## Downstream checklist

- Accept claims schema 1.2.0 and ten catalog records; keep evaluation output schema 1.1.0 and eight evaluations
- Classify statements with `claim_type`; preserve legacy `bound_kind` and handle null on model records
- Inspect `evaluation_support` before routing a record to a calculator; never execute `formula_display` or infer support from `rule_id`
- Preserve dimension/unit pairs, model parameter meanings, plane-stress/strain distinction, and half-crack convention
- Keep model estimates separate from theoretical bounds, derived outer envelopes, measured strengths, and engineering allowables
- Compare filtered JSON across en/zh/ja/de and keep filter codes untranslated
- Retain source locators, reading limits, reuse restrictions, and independent-review gaps

No paper full text, publisher PDF, measurement dataset, or new reuse permission is introduced. Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md). Software/schema checks and formula cross-checks are not independent scientific or native-language review.
