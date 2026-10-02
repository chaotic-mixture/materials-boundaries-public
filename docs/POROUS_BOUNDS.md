# Catalog-only isotropic solid/void bounds

Version 0.6.0 added three reusable knowledge records, bringing that release to **22 claims and 19 sources**. Current v0.8.0 retains those records and appends four strict [stability predicates](ELASTIC_STABILITY.md), for 26 claims under schema 1.6.0, while retaining 20 sources and the separate [observation catalog](OBSERVATIONS.md) with two properties from one study. The three porous records describe finite-porosity Hashin–Shtrikman (HS) bulk/shear envelopes and a derived Young's-modulus outer envelope. They are all `evaluation_support: catalog_only`: no porous-material input API, numerical evaluator, specimen-applicability check or chart is added. The existing positive-phase calculator still returns its original eight evaluations.

| Claim ID | Classification | Dependencies |
| --- | --- | --- |
| `hs_porous_bulk_3d_solid_void` | `theoretical_bound`, `scalar_modulus_bound` | None |
| `hs_porous_shear_3d_solid_void` | `theoretical_bound`, `scalar_modulus_bound` | None |
| `hs_porous_youngs_outer_3d_solid_void` | `derived_outer_envelope` for both claim type and bound kind | The two porous K/G claims |

All three use `direction: interval`, `quantity_dimension: pressure` and `si_unit: Pa`. A `rule_id` identifies catalog metadata; it does not register an executable rule. These records do not replace the two-positive-phase HS claims.

## Parameters and admitted material class

- `Ks > 0` and `Gs > 0` are finite bulk and shear moduli of one homogeneous isotropic solid in a common unit and reference state
- `p` is **void volume fraction**, with `0 <= p <= 1`; solid fraction is `1-p`
- The void has zero bulk and shear stiffness and traction-free pore surfaces
- The response is three-dimensional, homogenized, homogeneous at the effective scale, macroscopically isotropic, small-strain, static and linear elastic
- The reference state is unstressed, with no contact changes. Classical local continuum elasticity is assumed, without surface elasticity
- Geometry is unrestricted within this class, including disconnected solid regions. No connectivity, minimum strut thickness or manufacturing constraint is silently imposed
- The positive-stiffness regularization used to justify the void limit must preserve the declared effective isotropy

Constituent isotropy and effective isotropy are separate assumptions. A fortuitously isotropic response of an otherwise anisotropic regularization family is not certified by the short limiting argument below. Statistically homogeneous isotropic microstructures are an example of a class supporting the isotropy premise, not a property verified for an input specimen by this catalog.

Gas pressure, fluid saturation, capillarity, surface elasticity, prestress, nonlocal effects, inertia, resonance, buckling, contact closure, damage, yield, fracture and strength predictions are outside the claims. The formulas are conditional theoretical restrictions, not measured values, fitted constitutive laws or predictions for a particular pore geometry.

## Finite-porosity formulas

With all moduli in the same pressure unit, define

```text
K_upper(p) = 4 Ks Gs (1-p) / (4 Gs + 3 Ks p)
G_upper(p) = Gs (1-p) (9 Ks + 8 Gs)
             / (9 Ks + 8 Gs + 6 p (Ks + 2 Gs))

Es   = 9 Ks Gs / (3 Ks + Gs)
nu_s = (3 Ks - 2 Gs) / (2 (3 Ks + Gs))
C    = (1 + nu_s) (13 - 15 nu_s) / (2 (7 - 5 nu_s))
E_upper(p) = Es (1-p) / (1 + C p)
```

For positive `Ks,Gs`, `-1 < nu_s < 0.5` and the displayed denominators are positive throughout `0 <= p <= 1`. These are full finite-porosity formulas, not dilute-pore or low-density approximations. The inequalities are non-strict and allow equality within the declared ideal class.

For `p < 1`, the Young envelope independently simplifies to

```text
E_upper = 9 K_upper G_upper / (3 K_upper + G_upper)
```

This follows because `E(K,G)` is increasing in each nonnegative modulus, using its continuous zero extension where needed. It is a conservative outer envelope of compatible separate K/G bounds. Neither this monotonicity argument nor the catalog asserts that one microstructure simultaneously reaches the K/G upper corner. There is no promise of a tight joint attainable region or a finite, manufacturable realization of an extremum. Porous extremal-construction proofs have not received independent review in this project.

### Lower bounds and endpoints

| Porosity | Bulk and shear | Young's modulus | Interpretation |
| --- | --- | --- | --- |
| `p = 0` | `K_eff = Ks`, `G_eff = Gs` | `E_eff = Es` | Remove the absent void phase; both interval endpoints collapse to the pure solid |
| `0 < p < 1` | `0 <= K_eff <= K_upper`, `0 <= G_eff <= G_upper` | `0 <= E_eff <= E_upper` | Arbitrary geometry includes disconnected solid, so no positive universal lower endpoint is available |
| `p = 1` | `K_eff = G_eff = 0` formally | `E_eff = 0` by continuous extension | Empty-domain stiffness convention, not a load-bearing material |

An isolated solid region cannot transmit macroscopic static load through surrounding void. Thus zero is an admissible geometry-unrestricted lower endpoint at every strictly intermediate porosity. This does not say that every connected porous material is floppy, and it supplies no topology-specific lower bound.

The sharp lower endpoint at `p=0` is the positive solid modulus, **not zero**. Removing the void phase is a distinct endpoint operation: first taking its stiffness to zero at fixed positive porosity, then sending porosity to zero, does not recover the sharp pure-solid lower bound. At `p=1`, do not evaluate `9KG/(3K+G)` as `0/0`. Empty space has no defined Poisson ratio or mass-specific modulus; no effective Poisson-ratio bound is added by this batch.

## Why zero-phase substitution needs a limit

The supporting positive-phase HS formulas are not directly formulas for a strictly zero-stiffness phase. For `eta > 0`, replace void by `(K_void,G_void) = (eta Ks, eta Gs)`, preserving the effective-isotropy premise. Nonnegative strain-energy minimization orders the void effective tensor below the regularized tensor in quadratic-form order. Applying the positive-phase HS upper bounds and taking `eta` down to zero gives the displayed K/G upper expressions.

For fixed `0<p<1`, the positive-phase lower formulas tend to zero; nonnegative elastic energy also supplies the nonnegative lower bound. The shear-shift term must be treated as a limit of

```text
G_void (9 K_void + 8 G_void) / (6 (K_void + 2 G_void))
```

and never by inserting zero into an undefined `0*(0/0)`. This is the project's explicit zero-phase specialization and endpoint argument. Formula inspection and algebra checks are not an independent proof review. They do not establish material-specific applicability or authorize treating an active void as a positive phase in the runtime calculator.

## Density and the low-density limit

Only if the same fixed solid has density `rho_s` and the void carries no mass does mass balance give

```text
rho_eff = (1-p) rho_s
```

This is an additional conditional relation, not a universal density law when solid composition, solid density or pore contents vary. For `p<1` it permits dividing the stiffness bounds by a positive effective density. At `p=1`, zero density makes specific moduli undefined; a finite limiting ratio is not a property assigned to empty space.

Let `r=1-p` tend to zero. The first-order upper-curve expansions are

```text
K_upper = [4 Ks Gs / (3 Ks + 4 Gs)] r + O(r^2)
G_upper = [Gs (9 Ks + 8 Gs) / (15 Ks + 20 Gs)] r + O(r^2)
```

The linear terms lie below their corresponding full curves at finite `0<r<1`. They therefore **must not replace the full formulas as rigorous finite-density upper bounds**. They describe the asymptotic slope only, even when a density relation is available.

## Evidence, fraction convention and rights

- [Kochmann–Milton, arXiv:1401.4142v1](https://arxiv.org/abs/1401.4142v1): upper bulk Eq. (117), PDF/printed p. 18; upper shear Eq. (118), p. 19; lower Eqs. (134) and (135), p. 20. The research for this batch visually checked PDF pp. 18–20, including Eq. (127). The porous expressions are project algebraic specializations and limits of these positive-phase equations; no independent proof review is claimed. The existing source record is preserved, with this additional inspection scope documented here
- [Roberts–Garboczi (2002)](https://doi.org/10.1098/rspa.2001.0900), *Computation of the linear elastic properties of random porous materials with a wide variety of microstructure*, *Proceedings of the Royal Society of London A* **458**, issue 2021, pp. 1033–1054. The [NIST-hosted reprint](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=916993), Section 2(b), Eq. (2.8), printed p. 1037 / PDF p. 6, independently cross-checks the Young upper expression. **The source's `p` is solid fraction**, defined on printed p. 1034 / PDF p. 3: substitute `p_source = 1-p_catalog`. The isotropic identities appear on printed p. 1035 / PDF p. 4. The cover and printed pp. 1033–1038 were visually inspected; this is not a full-paper or independent proof review
- [Hashin–Shtrikman (1963)](https://doi.org/10.1016/0022-5096(63)90060-7): historical attribution only; the original equation locations and proof remain uninspected

The NIST reprint cover describes the contribution as not subject to copyright, while printed article p. 1033 carries a 2002 Royal Society copyright notice. Both observations are retained. No blanket reuse right or license identifier is inferred from the conflicting notices or public availability. The new source contains bibliographic metadata and original notes only; no PDF, article text or figure is bundled. Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md).

## Read the records and synthetic illustration

```sh
python -m materials_boundaries catalog claims --id hs_porous_bulk_3d_solid_void --text --lang en
python -m materials_boundaries catalog claims --query porous --direction interval --json
python -m materials_boundaries catalog sources --id roberts_garboczi_2002_porous --text --lang en
```

[`examples/catalog/porous-synthetic.json`](../examples/catalog/porous-synthetic.json) is a **documentation-only synthetic illustration**, not an accepted `validate`/`evaluate` input, measurement, literature material record or plot input. It uses `Ks=100 GPa`, `Gs=40 GPa` and the optional fixed-solid `rho_s=2500 kg/m^3` assumption. At `p=0.5`, the full upper formulas give approximately `K=25.8064516129 GPa`, `G=13.8636363636 GPa`, `E=35.2742751586 GPa`, with conditional density `1250 kg/m^3`; all three geometry-unrestricted lower endpoints are zero. At `p=0`, they collapse to the solid values; at `p=1`, formal stiffness is zero with no Poisson ratio or specific moduli. These rounded sample numbers are illustrations, not certified outward-rounded intervals.

The positive-phase evaluator must continue to report violated conditions and no numbers for active zero-modulus phases. See [migration](MIGRATION_v0.6.0.md), [catalog contract](CATALOG.md), [source ledger](SOURCES.md) and [unchanged numerical model](MODEL.md).
