# Bulk elastic plane waves: speeds, polarization and strict strong ellipticity

Version **0.18.0** adds exactly two **catalog-only** `model_relation` / `relation`
claims, with null `bound_kind`:

- `isotropic_bulk_plane_wave_speeds_and_ratio`
- `christoffel_tensor_strong_ellipticity`

These records describe conditional continuum identities and their mathematical
consequences. They add no material inputs, density/modulus conversion API,
tensor evaluator, eigensolver, directional plot, specimen classification or new
executable rule. The existing eight composite rules remain unchanged. The
v0.18.0 catalog contained 36 mechanics claims and 50 sources; claims schema is
1.11.0. The current v0.22.0 has 52 sources and twelve observations from four
studies; the wave claims and their scientific contracts are unchanged.
Source-supported equations and **original project derivations** are identified
separately below. No independent scientific peer review is claimed.

## 1. Shared model and units

Work in a homogeneous, unbounded, three-dimensional, purely mechanical,
classical local linear-elastic nondissipative continuum, about a **stress-free
equilibrium**, with infinitesimal strain. In orthonormal Cartesian axes, use a
finite, real, spatially constant stiffness with both minor and major symmetries:

- σ_ij = C_ijkl ε_kl; ε_kl = (u_k,l + u_l,k)/2
- C_ijkl = C_jikl = C_ijlk = C_klij
- Finite constant scalar mass density ρ > 0
- Indices i,j,k,l run from 1 to 3; repeated indices are summed

C, bulk modulus K, shear modulus G and Lamé parameter λ have units Pa;
ρ has units kg m⁻³. A plane wave is

**u(x,t) = Re[A a exp(i k(n·x − c t))]**, with k > 0, |n| = 1.

Here a is a nonzero real displacement eigenpolarization, A is a nonzero amplitude,
and the positive phase-speed root c has units m s⁻¹. The **phase normal n**
is the wavevector direction; **polarization a** is particle displacement.
They are different variables. Generic anisotropic eigenpolarizations need be
neither parallel nor perpendicular to n.

The tensor C is the operative constitutive tensor of this ideal mechanical
model. An unrelated static or isothermal stiffness is **not automatically** the
appropriate acoustic stiffness. No isothermal-to-adiabatic conversion,
thermoelastic coupling, frequency correction or dynamic homogenization is
asserted or implemented. The earlier static, fixed-temperature
[compressibility](DIRECTIONAL_COMPRESSIBILITY.md) and
[homogeneous energy-stability](ELASTIC_STABILITY.md) contracts keep their own
assumptions.

## 2. Canonical acoustic/Christoffel normalization

The project uses

**Q_ik(n) = C_ijkl n_j n_l**, with units **Pa**,

**Γ_ik(n) = Q_ik(n)/ρ**, with units **m² s⁻²**,

**Q(n)a = ρ c² a**, equivalently **Γ(n)a = c² a**.

Names such as acoustic tensor and Christoffel tensor vary among sources;
normalization and units must always accompany them. The contraction is over
j and l. C_ijkl n_k n_l with free indices i,j is not the tensor defined here.
Density may be omitted only if stiffness has explicitly already been
density-normalized. The SI check is Pa/(kg m⁻³) = m² s⁻².

### Source support and index mapping

[Chevrot and van der Hilst (2003)](https://doi.org/10.1046/j.1365-246X.2003.01865.x),
*Geophysical Journal International* 152(2), 497–505, §2, printed p. 498 / PDF
p. 2, Eqs. (1)–(4), supplies the homogeneous equation of motion, plane-wave
substitution, density-normalized Christoffel tensor and squared-phase-speed
eigenproblem. Its Eq. (3) writes Γ_jk = C_ijkl n_i n_l /ρ. First-pair minor
symmetry, followed by relabeling the free and dummy indices, gives exactly the
project convention above. Only the general equations before the paper's
weak-transverse-isotropy specialization support this catalog record.

### Original project derivation

Minor symmetry converts the equation of motion to
ρ u_i,tt = C_ijkl u_k,lj. Substitution of the stated plane wave and cancellation
of the common nonzero factor −k² gives
C_ijkl n_j n_l a_k = ρ c² a_i. Major symmetry and exchange of the contracted
dummy indices make Q real symmetric. Thus Γ has three real eigenvalues,
counting multiplicity, and an orthonormal real eigenbasis at each n.

**Reality of squared eigenvalues is not positivity.** Negative c² does not
supply a real nonzero phase speed, and c²=0 fails the strict criterion below.
Repeated eigenvalues are allowed; bases within their eigenspaces are nonunique.
This record does not require three distinct speeds.

## 3. Isotropic speeds and the material-class ratio

For isotropy,

C_ijkl = λ δ_ij δ_kl + G(δ_ik δ_jl + δ_il δ_jk), with λ = K − 2G/3.

Contraction gives, for |n|=1,

**Q(n) = G I + (K + G/3) n⊗n**.

With **finite K > 0, G > 0 and ρ > 0**, the exact longitudinal eigenmode has
a parallel to n, while the two-dimensional transverse eigenspace has a
perpendicular to n:

- **c_L² = (K + 4G/3)/ρ**
- **c_T² = G/ρ**, with **twofold transverse degeneracy**
- **c_L/c_T = √(K/G + 4/3)**

[Xiang, Qi and Wei, arXiv:1708.04876v2](https://arxiv.org/abs/1708.04876v2),
§2, printed/PDF pp. 4–5, gives the isotropic tensor, the Lamé/bulk relation,
and the unnumbered v_P and v_S equations on p. 5. The inspected artifact is
specifically the v2 preprint submitted 22 January 2018 (PDF title date
23 January 2018). Journal publication or journal-version verification is not
claimed. The following range proof is this project's derivation from those
identities, not a source-quoted interval theorem.

### Original project proof of the exact range

Let R=c_L/c_T. The speed identities imply R²=4/3+K/G.

1. Finite positive K/G gives **R > √(4/3)**. As K/G approaches 0 from above,
   R approaches √(4/3), but the endpoint is never attained in this class
2. For any finite R > √(4/3), choose any finite G > 0 and set
   K=G(R²−4/3). Then K is finite and positive, realizing that ratio
3. Across the class, finite K/G can grow without a common finite upper bound.
   Thus the exact class range is **(√(4/3), ∞)**. Infinity is not an attained
   value; density cancels from the ratio

One **fixed** material with finite positive K,G,ρ has one finite,
direction-independent c_L and one finite, direction-independent c_T, the latter
with multiplicity two. The class interval is not directional variation of one
isotropic material and is not a measured uncertainty interval. It provides no
universal numerical speed bounds without modulus/density bounds.

K=0 is excluded from the strict positive-energy class even though both speeds
remain positive for G>0. The incompressible K=∞ idealization is likewise outside
the finite-parameter class. The endpoint and class restrictions must not be
silently replaced by weak inequalities or incompressibility.

## 4. Strict strong ellipticity and full strain-energy positivity

**Strict strong ellipticity** means

**C_ijkl a_i n_j a_k n_l > 0 for every nonzero real a and n**.

Equivalently, Q(n) is symmetric positive definite (SPD) for **every unit n**.
Because ρ>0, this is equivalent to **all three c_α(n)² being strictly positive
for every propagation direction n**. Testing a finite set of directions does
not by itself prove this all-direction statement. Nonnegative eigenvalues or
one zero eigenvalue describe a different, marginal condition and do not pass
strict strong ellipticity.

Xiang–Qi–Wei v2, p. 2, provides the rank-one condition and tensor symmetries;
pp. 4–5 discusses positive definiteness, its implication and isotropic
specialization. The catalog makes the nonzero-vector quantifiers explicit:
including zero vectors in a strict inequality would be impossible. It also
restricts full strain-energy positivity to nonzero **symmetric** strains; the
source's p. 4 prose about arbitrary nonsymmetric matrices is not adopted,
because pure skew strain is annihilated by the minor symmetries.

Full homogeneous strain-energy positivity means

**W(e) = ½ e:C:e > 0 for every nonzero real symmetric e**.

This is the existing [general stiffness and Born stability](ELASTIC_STABILITY.md)
meaning, which is preserved. It implies strong ellipticity; the converse is
false. Strong ellipticity therefore must not replace those existing criteria.

### Original project proof of the implication

For nonzero a,n, set e=sym(a⊗n). Minor symmetry gives

aᵀQ(n)a = e:C:e,

while ||e||² = (|a|²|n|²+(a·n)²)/2 > 0.

Thus full symmetric-strain energy SPD makes this rank-one contraction strictly
positive, proving the implication under the declared symmetries.

### Original project counterexample to the converse

Take finite G>0 and ρ>0, and **K=−G/3**, hence λ=−G. Direct contraction gives

**Q(n)=G I** for every unit n.

It is strictly SPD and all three squared speeds equal G/ρ: **triple degeneracy
is compatible with strict strong ellipticity**. But for hydrostatic strain
e=αI with α≠0,

**W = (9/2)Kα² = −(3/2)Gα² < 0**.

This tensor has strict strong ellipticity and negative hydrostatic energy, so
it fails full strain-energy SPD. It is a mathematical counterexample within
the stated constitutive model, not a proposed stable material or a
physical-realizability claim. Direct contraction remains valid at K+G/3=0;
no division by that quantity or nonorthogonal-case M-eigenvalue derivation is
used.

For isotropy the two different conditions are:

- Strict strong ellipticity: **G>0 and K+4G/3>0**, equivalently
  μ=G>0 and λ+2μ>0
- Full symmetric-strain energy SPD: **G>0 and K>0**

The latter follows also from W=G e_dev:e_dev + (K/2)(tr e)².
Strong ellipticity alone permits K=0 and negative K>-4G/3. As auxiliary
original discussion, not an additional catalog claim, its isotropic speed
ratio therefore has the separate range **(0,∞)**: for any finite R>0 choose
G>0 and K=G(R²−4/3), which satisfies the strict wave criterion. In particular
c_L need not exceed c_T. This original project observation must not be
substituted for the positive-energy class interval (√(4/3),∞).

### Original fixed-tensor boundedness argument

For one fixed finite tensor C and fixed ρ>0 satisfying strict strong
ellipticity, Γ(n) is continuous on the compact unit sphere. Its smallest
eigenvalue has a positive attained minimum, and its largest has a finite
attained maximum. Taking positive square roots gives finite fixed-tensor phase
speed extrema with a strictly positive lower endpoint. This existence argument
is not a universal numerical bound over tensors and is not an implemented
extremum solver.

## 5. Anisotropic interpretation and exclusions

In general anisotropy, report eigenpolarizations and eigenvalues with their
direction and multiplicity. Do not declare every mode exactly longitudinal or
transverse, or assert that a universally defined longitudinal mode is fastest.
Quasi-longitudinal/transverse names need their own conventions; eigenvalue
ordering alone does not supply exact polarization character, and degeneracies
can prevent unique branch labels.

These c values are **phase speeds along phase normals**. In anisotropy the
ray/group/energy direction need not coincide with n. No group-velocity,
energy-velocity or ray-surface formula, numerical prediction or equality with
phase velocity is supplied here.

Excluded are prestress/residual stress; finite-strain incremental or tangent
moduli; complex viscoelasticity, damping and material dispersion; thermoelastic
or poroelastic coupling; heterogeneous effective-medium wave assumptions;
negative or tensorial dynamic effective density; nonlocal/strain-gradient,
Cosserat or micromorphic media; 2D, thin-film, plane-stress or plane-strain
reductions; surface Rayleigh/Love or guided waves; finite-body resonances;
material-specific predictions; strength, fracture, full phonon and complete
thermodynamic stability. No constitutive or experimental information needed
for those problems is inferred from catalog presence.

## 6. Verification, attribution and rights

The source audit visually checked Chevrot–van der Hilst printed p. 498,
Eqs. (1)–(4), and Xiang–Qi–Wei v2 printed/PDF pp. 2, 4–5. The inspected
Chevrot artifact is an [author/university-hosted journal-layout PDF](https://hilst.mit.edu/wp-content/uploads/2017/05/2003_gji_152-497-505.pdf).
Bibliographic identity, version, equation locators and limits are recorded in
[the source ledger](SOURCES.md). Only these two new sources support this batch;
no uninspected chapter or unrelated generalized-continuum result is imported.

The project independently writes the contraction/index mapping, interval proof,
energy implication/counterexample, fixed-tensor compactness argument and SI
check above. Symbolic algebra cross-checks and software tests are verification
aids, **not independent scientific review, experimental validation or a proof
of material realizability**. Existing full-energy criteria retain their earlier
source attribution; this batch does not claim a new audit of those sources.

Chevrot–van der Hilst carries ©2003 RAS; no general reuse license was verified.
The arXiv nonexclusive distribution permission for Xiang–Qi–Wei is not a
general republication or relicensing grant. Only bibliographic metadata,
mathematical relations and original project notes are included. No source PDF,
page image, figure or article full text is redistributed. MIT covers the
project's original contributions only. See [third-party notices](../THIRD_PARTY_NOTICES.md).

## 7. Read the records

```sh
python -m materials_boundaries catalog claims --id isotropic_bulk_plane_wave_speeds_and_ratio --text --lang en
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang zh
python -m materials_boundaries catalog claims --source-id chevrot_vanderhilst_2003 --json
python -m materials_boundaries catalog sources --id xiang_qi_wei_2018_arxiv_v2 --text --lang ja
```

Canonical JSON, identifiers and units are independent of display language.
The four getting-started guides provide substantive localized summaries:
[English](GETTING_STARTED.en.md), [中文](GETTING_STARTED.zh.md),
[日本語](GETTING_STARTED.ja.md), [Deutsch](GETTING_STARTED.de.md).
Translations, including English scientific prose, remain machine-assisted and
not independently scientifically or natively reviewed. See [migration](MIGRATION_v0.18.0.md)
and [the language contract](I18N.md).
