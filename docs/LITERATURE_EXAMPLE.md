# One literature-model example: epoxy and glass

This example uses constituent inputs from [Genin & Birman (2009), DOI 10.1016/j.ijsolstr.2008.08.010](https://doi.org/10.1016/j.ijsolstr.2008.08.010), *International Journal of Solids and Structures* 46(10), 2136–2150. The inspected [author-hosted PDF](https://web.mst.edu/vbirman/papers/Micromechanics%20and%20response%20of%20FGM%20particulate%20fiber-reinforced%20composites_IJSS%202009.pdf) is an uncorrected proof dated 30 August 2008, distinct from the 2009 journal citation. An [author manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC3714223/) provides corroborating context.

The source locator is proof PDF page 8, Section 5, printed lines 381–383 / Fig. 1 for the epoxy and spherical-glass parameters; page 2, Section 2, printed line 101 states the constituent model's isotropic, linear-elastic assumptions. The example takes only the particulate-matrix submodel, not the complete fiber-reinforced or graded laminate. It is a literature-model input example, **not measured material data, a reported specimen, or an independent material validation**.

## Raw inputs and project calculations

| Model constituent | Source E (GPa) | Source ν | Derived K (GPa, approximate) | Derived G (GPa, approximate) |
| --- | ---: | ---: | ---: | ---: |
| epoxy | 3.12 | 0.38 | 4.333333333333334 | 1.1304347826086958 |
| glass | 76.0 | 0.25 | 50.666666666666664 | 30.4 |

The stored K/G values are project-derived, not values claimed to have been measured or tabulated by the source. The fixed conversion rule `isotropic_young_poisson_to_bulk_shear_v1` uses K = E/[3(1−2ν)] and G = E/[2(1+ν)], retaining E's unit. It supports E > 0 and −1 < ν < 0.5. The 80-digit Decimal helper and ordinary binary-float arithmetic can differ in the last ~1e-15 digits; stored derived values are checked with relative tolerance 1e-12 after unit conversion. This tolerance is a numerical consistency check, not measurement uncertainty.

## Explicitly chosen conditions

Glass volume fraction 0.20 and epoxy fraction 0.80 are a calculator illustration within the plotted range, not a specimen reported by the paper. Effective isotropy, perfect bonding, static loading, small strain and the 3D homogenized interpretation are calculator assumptions. Source-model constituent isotropy and linear elasticity are marked separately. Temperature, material grade, cure state and measurement uncertainty remain `null`; room temperature is never inferred.

```sh
python -m materials_boundaries validate examples/literature-epoxy-glass-model.json --lang en
python -m materials_boundaries evaluate examples/literature-epoxy-glass-model.json --lang en
python -m materials_boundaries evaluate examples/literature-epoxy-glass-model.json --json
```

Expected conditional results in v0.2.0, rounded here:

| Quantity | Reuss lower | HS interval | Voigt upper |
| --- | ---: | ---: | ---: |
| K (GPa) | 5.30327428878 | 5.59472179063–9.407756984 | 13.6 |
| G (GPa) | 1.40002834065 | 1.69577678689–4.55086141565 | 6.98434782609 |

- Effective E derived outer envelope: approximately 4.62050115425–11.7568508016 GPa
- Effective ν derived outer envelope: approximately 0.180042955115–0.414981746661, dimensionless unit `1`

The source E/ν in the constituent table and these effective-composite envelopes are different physical quantities. Effective E/ν are project derivations from same-system HS K/G intervals, not output values reported by Genin–Birman. They are conservative outer envelopes, not tight joint attainable bounds: the two marginal HS endpoints may not be attained by one microstructure. No experimental uncertainty interval is implied. All endpoints are numerical approximations, without certified outward rounding.

`satisfied` means the declared source-model/calculator assumptions match the implemented rules. It does not establish the real-world applicability of these numbers. Replacing an unsupported condition with `null` and its evidence basis with `unknown` suppresses numeric bounds, as for synthetic examples.

## Provenance contract

`provenance.kind = literature_model` requires `model_evidence`: a source ID included in `source_ids`, an exact locator, one raw E/ν record for every phase, the fixed conversion ID, per-condition evidence bases, an explicit fraction basis, context fields and a scope note. `source_model`, `calculator_assumption` and `unknown` are distinct labels. Unknown bases must match missing/null conditions. Runtime validation rejects unknown metadata keys, broken source/phase links and inconsistent K/G derivations. Citation presence does not independently verify the external source's truth.

The published work is copyright Elsevier, all rights reserved. Only citations, numeric facts and original project calculations/notes are included; the repository contains no source PDF, text body or figure. Original project code, documentation and original curation use the [MIT License](../LICENSE); third-party works and scientific facts are not relicensed. See [notices](../THIRD_PARTY_NOTICES.md).
