# Strength and fracture knowledge records

This guide documents five **catalog-only** entries introduced during v0.4.0 development. The current v0.19.0 release has 36 mechanics claims and 51 source records in total. Eight elastic-bound/envelope evaluations remain executable. These additions do not implement a strength/fracture calculator or certify a specimen's premises. Unknown parameters are not filled from elastic-bound endpoints.

| Record | Class | Output / SI unit | Evidence anchor |
| --- | --- | --- | --- |
| `frenkel_slip_specific_ideal_shear` | `model_estimate` | Ideal resolved shear stress / Pa | Shimanek et al., arXiv v2, eq. (1), p. 2; §3.3, p. 11 |
| `uber_normal_cohesive_strength` | `model_estimate` | Ideal normal cohesive traction peak / Pa | Azócar Guzmán et al. (2020), eqs. (2)–(3), p. 4; Van der Ven–Ceder (2004), eq. (14), p. 1228 |
| `lefm_central_crack_mode_i_stress_intensity` | `model_relation` | K_I / `Pa*m^0.5` | Wilson (1992), eq. (4), printed p. 3 |
| `lefm_mode_i_energy_release_relation` | `model_relation` | G_I / `J/m^2` | Wilson, eqs. (5)–(6), printed pp. 3–4 |
| `lefm_center_crack_finite_width_secant_factor` | `model_relation` | Geometry correction Y / `1` | Wilson, §3.4.1 case 1, p. 21; Pierce–Sullivan (1969), p. 6 |

All have `bound_kind: null`, `evaluation_support: catalog_only`, and no dependency on the composite calculator. `model_relation` includes conditional identities and documented analytical approximations; it does **not** mean a rigorous bound, a critical value or independent validation. Its `direction` is `relation`. The two strength estimates use `direction: prediction`.

## 1. Slip-specific Frenkel estimate

The sinusoidal restoring-traction approximation gives

**tau_ideal = G_slip b / (2 pi h)**

Here G_slip (Pa) is the initial shear stiffness for the specified crystal orientation, slip mode, relaxation treatment and loading constraints. b (m) is the Burgers-vector magnitude for that slip model; h (m) is its slip-plane spacing. All three are positive. With tau(u)=tau_ideal sin(2 pi u/b) and shear strain u/h, matching the initial tangent to G_slip gives the expression above; this explanatory derivative is project algebra, not a quoted original Frenkel derivation.

The modern source is [Shimanek et al., arXiv:2108.06412v2, 10 June 2022](https://arxiv.org/pdf/2108.06412v2), corresponding to *Computational Materials Science* 212 (2022), 111564, [DOI](https://doi.org/10.1016/j.commatsci.2022.111564). Equation (1), manuscript p. 2, and §3.3, p. 11, were checked in text and rendered pages. Its particular {111}<112> partial-slip setup uses rotated C55 and b/h=1/sqrt(2). Neither that elastic component nor that ratio is universal.

Do not replace G_slip with a Hill/polycrystal-average modulus by default, or simplify the estimate to G/(2 pi) unless b/h=1. Dislocations, cracks, competing instabilities, temperature/rate effects and changed transverse constraints can defeat an interpretation as bulk strength. This sinusoidal model is not a rigorous upper-bound theorem.

[Frenkel (1926)](https://doi.org/10.1007/BF01397292) is historical attribution only: the publisher metadata and abstract were inspected; original equations/full text were not. The modern source does not repair that historical verification gap.

## 2. Normal UBER cohesive-traction peak

For a specified planar cleavage/interface under a fitted two-parameter universal binding energy relation (UBER), choose zero binding energy at infinite separation:

- e_b(delta) = −W_sep (1 + delta/lambda) exp(−delta/lambda)
- sigma(delta) = de_b/d(delta) = (W_sep/lambda)(delta/lambda) exp(−delta/lambda)
- sigma_max = W_sep/(e lambda), at delta=lambda

W_sep>0 is work of separation per area (J/m²), lambda>0 is the interaction length (m), and delta≥0 is local opening from equilibrium (m). e_b(0)=−W_sep and e_b(infinity)=0. Differentiating the energy and traction gives the peak; **the traction and peak are project analytic derivatives**, not mislabeled separately printed source equations.

[Azócar Guzmán et al. (2020)](https://doi.org/10.3390/ma13245785), *Materials* 13(24), 5785, §2.1 eq. (1), p. 3; §2.1.2 eqs. (2)–(3), p. 4; §§2.1.3–2.1.4, pp. 5–6, provides the energy law, curvature and modeling constraints. The publisher PDF `version=1608279623` was inspected, including a visual check of p. 4. One prose sentence has a sign ambiguity; the displayed law fixes the positive W_sep convention explicitly. [Van der Ven and Ceder (2004)](https://doi.org/10.1016/j.actamat.2003.11.007), *Acta Materialia* 52, 1223–1235, §3.2 eq. (14), p. 1228 / PDF p. 6, independently supplies the same energy form after an energy-zero shift. Its excess-variable definitions are in §2.4 eq. (11), p. 1226, and §3.2 eqs. (12)–(13), p. 1227.

For clean symmetric cleavage under matching conditions, W_sep=2 gamma. A general interface needs its own work of separation. Neither a dissipative macroscopic Gc nor bulk Young modulus may be substituted silently. The initial normal stiffness k_n=W_sep/lambda² has units **Pa/m**, so sigma_max=sqrt(W_sep k_n)/e only when k_n belongs to this same law.

Declare the crystallographic plane, lateral constraints, relaxation treatment, temperature and impurity ensemble. The 2020 calculation fixes transverse dimensions without Poisson contraction. Relaxation releases elastic energy, so the peak stress inferred from raw RGSrel total-energy/extension curves depends on supercell size and is not automatically intrinsic cohesive strength. Its same-stress excess energy/opening treatment matters. Raw cell elongation is not automatically local cohesive opening. Reconstruction, plasticity, other failure paths and non-UBER traction shapes are outside the estimate.

[Rose, Ferrante and Smith (1981)](https://doi.org/10.1103/PhysRevLett.47.675) is included for historical UBER origin. Only abstract/metadata were inspected; its original full-text equations were not verified. No universal tensile-strength bound is claimed.

## 3. Central-crack Mode-I stress intensity

**K_I = sigma sqrt(pi a)** for an infinite homogeneous isotropic small-strain linear-elastic plate, central traction-free through crack of full length **2a**, and uniform remote tension sigma normal to the crack. Loading is quasi-static and the process zone is negligible on crack/body scales. Wilson's Fig. 1 (printed p. 2 / PDF p. 10) and eq. (4) (printed p. 3 / PDF p. 11) were visually inspected.

K_I is a loading/geometry amplitude with unit Pa·sqrt(m). It is not bulk modulus K, critical toughness K_Ic or a failure criterion. Finite width, other crack geometries, residual/mixed/dynamic loading and significant yielding need other models. No toughness or strength follows from this relation alone.

## 4. Mode-I G–K relation

**G_I = K_I²/E_prime**, with E_prime=E for plane stress and E_prime=E/(1−nu²) for plane strain. E>0, and a stable 3D isotropic elastic solid has −1<nu<0.5. nu is used only in the plane-strain branch. Wilson eqs. (5)–(6) and the printed p. 4 plane-state definitions (PDF pp. 11–12) were visually inspected.

Unlike the central-crack K expression, this parameter identity does not require an infinite central-crack geometry: the supplied K_I must match the actual supported geometry/loading. G_I is energy release per projected crack area, not shear modulus G or critical resistance Gc. It is the Mode-I contribution, not the total mixed-mode G. It does not cover anisotropic/interface, dynamic or substantially inelastic fracture. The identity never sets G_I=2 gamma; fracture initiation requires a separate criterion and supplied resistance.

Dimensions: (Pa·sqrt(m))²/Pa = Pa·m = J/m². Do not erase the distinction between the fracture symbols K_I/G_I and elastic moduli K/G.

## 5. Finite-width secant correction and a source discrepancy

For a centered through crack in a finite-width strip under uniform remote gross tension,

**Y = sqrt(sec(pi a/W)); K_I approximately Y sigma sqrt(pi a)**

W is the **full** sheet width; full crack length is 2a. Adopt **0<2a/W≤0.8**, equivalently 0<a/W≤0.4. End/loading-boundary effects and plasticity must be negligible; edge/eccentric cracks, holes and other geometries are excluded. Y is dimensionless and is an approximation, not a material bound.

[Wilson (1992)](https://ntrs.nasa.gov/citations/19920021173), §3.4.1 case 1 following eq. (31), printed p. 21 / PDF p. 29, shows this factor and the full-width geometry, but prints **a/W≤0.8**. That range is internally inconsistent with its geometry and is **not adopted**. [Pierce and Sullivan, NASA TN D-5140 (April 1969)](https://ntrs.nasa.gov/citations/19690012030), printed p. 6 / PDF p. 9, immediately before eq. (1), explicitly gives **2a/W≤0.8**. Symbols on printed pp. 2–3 confirm half-crack a and full-width W.

The latter report states agreement of the secant expression with an Isida polynomial to within 0.3% over that range. This is a reported formula comparison, not measured uncertainty or an independently certified error bound. We did not independently reproduce that comparison. Its eq. (1) also uses a plasticity-corrected a_bar=a+K²/(2 pi sigma_ys²). This entry instead uses Wilson's uncorrected expression, explicitly sets **a_bar=a**, and requires negligible plasticity. It neither solves that implicit correction nor imports the report's measured aluminum data.

## Read, search and preserve the boundary

```sh
python -m materials_boundaries catalog claims --claim-type model_relation --direction relation --text --lang en
python -m materials_boundaries catalog claims --query '理想剪切' --text --lang zh
python -m materials_boundaries catalog claims --query '垂直凝集' --text --lang ja
python -m materials_boundaries catalog claims --query 'Sekanskorrekturfaktor' --text --lang de
```

The five new records have curated display names in en/zh/ja/de. These names are literal search aliases in all languages, independent of `--lang`. The canonical name, original source titles, DOI, equations, IDs and evidence remain unchanged. Labels and explanations are machine-assisted and await independent scientific/native-language review. Other source text and arbitrary translated terminology are not automatically indexed or translated.

A schema-valid entry, a matching query, formula inspection and software tests do not prove a specimen's premises or replace independent scientific review. No full texts, figures, publisher PDFs, measured dataset or new executable rule are bundled. Rights are source-specific: the 2020 paper has verified CC BY 4.0; arXiv access and public author copies are not general redistribution licenses; NASA public-use statements are recorded without inventing license identifiers. Original project code, documentation and original curation are licensed under the [MIT License](../LICENSE). Third-party works and factual source material are not relicensed; see [Third-party notices](../THIRD_PARTY_NOTICES.md).

See [source ledger](SOURCES.md), [catalog contract](CATALOG.md), and [v0.4.0 migration](MIGRATION_v0.4.0.md).

## Historical v0.16.0 hydrostatic-compressibility addition

The v0.4.0 records above remained unchanged. The v0.16.0 baseline had 34 mechanics
claims and 47 sources. Its two new catalog-only `model_relation` / `relation` records add
hydrostatic directional linear compressibility β(n)=nn:S:I (`inverse_pressure`,
`Pa^-1`) and normalized β/κ (`dimensionless`, `1`). Both have null `bound_kind`;
no strength or material-specific prediction is implied.

For static σ=−pI, p>0 compressive, finite real full-SPD 3D stress-free isothermal
small-strain elasticity gives κ=I:S:I>0. Every orthonormal triad sums to κ even
when one or two principal responses are negative. This counts principal values,
not arbitrary negative directions. B=S:I has finite attained eigenvalue extrema
for a fixed tensor. Across unrestricted tensors all finite β/κ are attainable,
even at fixed positive κ, while cubic/isotropic β/κ is exactly 1/3. The strict
same-tensor inequality β²<κ/E is necessary, not sufficient for full SPD.
Engineering shear recovery uses B23=g4/2, B13=g5/2, B12=g6/2 for g=S_eng h.

The [full compressibility guide](DIRECTIONAL_COMPRESSIBILITY.md) gives original
project proofs, engineering conventions, exclusions and four-language scientific
summaries. Ortiz's published equation pages were visually checked; Miller's
author-manuscript equations were text-checked only. Neither is credited with
proving the original unrestricted normalized-range theorem. No independent
scientific/native-language review, source-reuse license, tensor evaluator or
additional executable composite rule is added.

## v0.18.0 bulk elastic-wave addition

The earlier mechanics entries retain their definitions and evidence. Two new
catalog-only `model_relation` / `relation` records are
`isotropic_bulk_plane_wave_speeds_and_ratio` and
`christoffel_tensor_strong_ellipticity`. With finite positive K,G,ρ, isotropic
c_L²=(K+4G/3)/ρ and c_T²=G/ρ imply the exact class ratio (√(4/3),∞),
not attained endpoints. A fixed material has finite direction-independent
speeds and two transverse polarizations sharing c_T.

In the shared finite real 3D stress-free homogeneous mechanical model,
Q_ik=C_ijkl n_j n_l has units Pa and Γ=Q/ρ has speed-squared units.
All-direction strict Q-SPD is equivalent to three strictly positive c² values
counting multiplicity. Full symmetric-strain energy SPD is stronger: the
original K=−G/3 counterexample has Q=GI but negative hydrostatic energy.
Phase normal and polarization differ; generic anisotropic modes have no
universal exact L/T ordering, and phase speed is not a ray/group-speed claim.
No static/isothermal modulus substitution is automatic.

The [bulk-wave guide](BULK_ELASTIC_WAVES.md) gives original proofs, precise
source/version locators and exclusions. Chevrot–van der Hilst (2003), printed
p. 498 Eqs. (1)–(4), and Xiang–Qi–Wei arXiv v2, pp. 2, 4–5, are the two added
sources. The 36-claim/50-source catalog adds no evaluator, tensor solver,
strength prediction or wave plot. Existing full-energy stability criteria,
observations and eight executable composite rules remain unchanged.
