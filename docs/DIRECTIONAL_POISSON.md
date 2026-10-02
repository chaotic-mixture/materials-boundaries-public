# Directional Poisson ratio: definition, range and paired constraints

v0.15.0 adds exactly two **catalog-only** `model_relation` / `relation` records:

- `directional_poissons_ratio_definition_and_range`
- `directional_poisson_reciprocity_energy_constraint`

Both use the distinct dimensionless quantity `directional_poissons_ratio`, SI
unit `1`, `bound_kind: null` and `evaluation_support: catalog_only`. The second
record depends on the first as a definition reference. Neither is registered
as an executable composite rule. Displayed formulas and directional metadata
are never evaluated. These are conditional mathematical relations, not measured
material properties, an engineering allowable or a strength prediction.

## Conditions and the directional definition

Use classical local, real, three-dimensional, infinitesimal linear elasticity
about a stress-free equilibrium. Stiffness C is finite, has minor and major
symmetries, and is strictly positive definite on **all** nonzero symmetric
strains. Compliance S is the full tensor inverse C⁻¹ on symmetric tensors;
equivalently its full engineering matrix is positive definite. No additional
material symmetry is required. Axes are orthonormal Cartesian axes.

Let n be the loading direction and m the transverse measurement direction,
with n·n = m·m = 1 and n·m = 0. Apply static uniaxial **stress**
σ = t(n⊗n), where t is nonzero and sufficiently small. All other applied stress
components vanish in the loading frame. With tensile stress and extensional
strain positive, ε = S:σ, so

- longitudinal strain: εnn = n·εn = t(nn:S:nn)
- transverse strain: εmm = m·εm = t(mm:S:nn)
- directional Young modulus: E(n) = 1/(nn:S:nn) > 0
- directional Poisson ratio: ν(n,m) = −εmm/εnn = −(mm:S:nn)/(nn:S:nn)

Here nn means n⊗n, and contractions use the full fourth-order compliance tensor.
The positive denominator is guaranteed by full strict positivity. The t cancels;
changing its sign consistently does not change the linear ratio. Uniaxial stress
may also induce shear strain in an anisotropic material. The definition imposes
neither zero shear strain nor constrained transverse displacement. It does not
describe uniaxial strain.

The existing `effective_poissons_ratio` output uses the separate isotropic
identity ν(K,G) = (3K−2G)/(2(3K+G)). Do not insert a directional value into that
identity or reuse its −1 < ν < 1/2 interval as a general anisotropic bound.

## Tensor and engineering-matrix conventions

Use engineering-Voigt order (11,22,33,23,13,12), with

- e = (ε11,ε22,ε33,2ε23,2ε13,2ε12)
- s = (σ11,σ22,σ33,σ23,σ13,σ12)
- e = S_eng s, s = C_eng e, and S_eng = (C_eng)⁻¹
- elastic energy density = eᵀ C_eng e / 2 = sᵀ S_eng s / 2
- C_eng,IJ = C_ijkl and S_eng,IJ = dI dJ S_ijkl, d = (1,1,1,2,2,2)

In particular, C_eng,44 = C2323 but S_eng,44 = 4S2323. Full matrix inversion
is required; componentwise reciprocals are wrong. S has units Pa⁻¹ and C and
E have units Pa. The ratio is dimensionless. Kelvin/Mandel shear scaling is
different and must be converted consistently before using these entries.
Norris's general paper Eq. (1) writes raw tensor s66 = S1212 and G = 1/(4s66);
that s66 is not engineering S_eng,66.

## Every finite real ratio: an original project construction

This construction and its algebra are **project derivations**, not a transcription
of a numbered source equation. Choose any finite real q and s0 > 0 with units
Pa⁻¹. In the engineering convention above, define

```text
           [ 1   −q       0  0  0  0 ]
           [−q   1+q²     0  0  0  0 ]
S_eng = s0 [ 0    0       1  0  0  0 ]
           [ 0    0       0  1  0  0 ]
           [ 0    0       0  0  1  0 ]
           [ 0    0       0  0  0  1 ]
```

For every nonzero real stress vector x,

xᵀ S_eng x = s0[(x1−qx2)² + x2² + x3² + x4² + x5² + x6²] > 0.

Thus S_eng is finite real SPD for every finite q, and its full inverse is also
finite real SPD. The inverse upper-left 2×2 block is
s0⁻¹ [[1+q²,q],[q,1]]; the remaining diagonal entries are s0⁻¹. The engineering
conversion constructs a fourth-order tensor with the required minor and major
symmetries. It has at least orthotropic symmetry in the displayed frame; no
assertion of exactly orthotropic symmetry for every special q is needed.

Under σ = t(e1⊗e1), the response is ε = s0 t diag(1,−q,0), hence

- ν(e1,e2) = q
- E(e1) = 1/s0 and E(e2) = 1/[s0(1+q²)]
- ν(e2,e1) = q/(1+q²)
- ν(e1,e2)ν(e2,e1) = q²/(1+q²) < 1

For any chosen sufficiently small dimensionless η > 0, choose
t = η/[s0√(1+q²)]. The Frobenius norm of ε is then η for every finite q.
Arbitrarily large ratios do not require a large strain in this construction.

Consequently the range **over the stated tensor class and orthonormal pairs**
is all finite real numbers. It is unbounded below and above; neither infinity
is attained. This is a mathematical statement about elasticity tensors, not
proof of microscopic realizability for every q. For example, q = −1 and q = 1/2
both give strictly positive-definite tensors. Those values are excluded endpoints
of the finite-positive-modulus isotropic interval, but are ordinary allowed values
in this larger anisotropic class.

## A fixed finite tensor has finite attained extrema

This compactness argument is an original project derivation from the definition.
For a fixed finite full-SPD S, define

V = {(n,m) ∈ R³×R³ : n·n = m·m = 1, n·m = 0}.

V is closed and bounded, therefore compact. The denominator a(n) = nn:S:nn
is continuous and positive on the unit sphere. It has a strictly positive
minimum there, because its attained minimum cannot be zero under SPD.
The numerator mm:S:nn is continuous. Thus ν is continuous on V and attains
a finite minimum and finite maximum.

No finite universal bound across varying tensors does **not** mean an infinite
response of a fixed finite SPD tensor. A sequence can approach a singular
boundary while each member remains SPD, but the singular limit is outside scope.
The catalog adds no extremum-search algorithm or sampled extrema.

## Reciprocity and the strict energy-pair constraint

The following general-direction proof is an original project derivation from
major symmetry and full-SPD Cauchy–Schwarz. It is not attributed to a numbered
Norris equation or to an inspected Lempriere original.

Let A = n⊗n, B = m⊗m, a = A:S:A, b = B:S:A and c = B:S:B.
Major symmetry gives b = A:S:B. Full SPD makes ⟨X,Y⟩S = X:S:Y an inner
product on the six-dimensional space of symmetric tensors. A and B are linearly
independent: contracting αA+βB = 0 with A and B gives α = β = 0, since
A:A = B:B = 1 and A:B = (n·m)² = 0. Strict Cauchy–Schwarz therefore gives

a > 0, c > 0, and b² < ac.

Substitute E(n) = 1/a, E(m) = 1/c, ν(n,m) = −b/a and ν(m,n) = −b/c:

- ν(n,m)/E(n) = −b = ν(m,n)/E(m)
- |ν(n,m)| < √[E(n)/E(m)]
- 0 ≤ ν(n,m)ν(m,n) = b²/(ac) < 1

The upper inequalities are strict. Equality in the modulus-dependent bound or
pair product = 1 is impossible under full SPD with orthogonal directions.
Product zero is allowed exactly when b = 0, so both ratios vanish. Otherwise
the exchanged ratios share a sign; they need not have equal magnitudes.

These are **necessary paired constraints**, not sufficient tests for the entire
3D elasticity tensor. For example, positive compliance on the e1,e2 normal-stress
subspace with zero coupling can satisfy the displayed pair constraints while a
negative remaining diagonal compliance component makes the full tensor
indefinite. Such an indefinite tensor is not in either claim's scope.
The modulus ratio E(n)/E(m) can vary without a universal upper bound over the
stated class, so the inequality supplies no finite universal numerical limit
on ν(n,m). Reversed-direction values must use the same full S.

## Cubic corroboration, with its narrower scope kept explicit

Cubic symmetry also permits both signs without finite universal bounds when all
orthogonal direction pairs are allowed; cube-axis-only ratios have additional
restrictions. The following is a project specialization of visually checked
Norris (2006) cubic equations, not a measured material example.

Choose M > 0 in Pa, κ = μ1 = M, μ2 = δM, and 0 < δ < 1/41. The cubic
engineering stiffness has C11 = M(1+4δ/3), C12 = M(1−2δ/3), C44 = M.
Its strict cubic conditions hold: C11+2C12 = 3M > 0, C11−C12 = 2δM > 0,
and C44 = M > 0. Norris's Eqs. (2.14), (3.19)–(3.20) specialize to

- ν111 = 1/8
- ν− = [1−√(12/δ−11)]/16
- ν+ = [9+√(12/δ+37)]/16

The associated directions are

- p− = √[(ν−+1/2)/(ν−−1/4)], n− = (1,1,p−)/√(2+p−²),
  m− = (1,−1,0)/√2
- p+ = √[(ν+−3/2)/(ν+−3/4)], n+ = (1,1,p+)/√(2+p+²),
  m+ = (p+,p+,−2)/√(2p+²+4)

Each pair is orthonormal in the stated δ interval. As δ tends to zero through
positive values, ν− tends to negative infinity and ν+ to positive infinity.
δ = 0 is excluded. At δ = 0.01 the synthetic formulas give approximately
−2.0926174562 and 2.7606881744; these are rounded examples, not measurements.
The algebraic limit establishes unboundedness, not numerical sampling.
Norris Eq. (5.1a) requires μ1/μ2 > 25 for νmin < −1: the threshold is strict,
not equality, despite the looser wording in the paper's abstract.

## Exclusions, evidence and reuse

Exclude 2D elasticity, plane-stress/plane-strain constitutive reductions,
finite-strain tangent ratios, prestressed states, complex viscoelastic response,
singular, positive-semidefinite or indefinite tensors, and nonlocal/Cosserat
theories. Strict homogeneous elastic energy positivity is not complete phonon,
finite-amplitude, strength or thermodynamic stability. No specimen validation,
tensor-input API, inversion service, numerical evaluator, extremum search or
material-specific prediction is added.

- [Ting and Chen (2005), QJMAM 58(1), 73–82](https://doi.org/10.1093/qjmamj/hbh021):
  publisher abstract and bibliographic/rights notice inspected. The abstract
  supports two-sided unboundedness under positive-definite strain energy.
  The full text was **not inspected**; no full-proof verification is attributed
  to it. ©2005 Oxford University Press, all rights reserved; no reuse license
  was verified.
- [Norris (2006), Proceedings A 462, 3385–3405](https://doi.org/10.1098/rspa.2006.1726):
  relevant author-hosted published PDF pages visually inspected: pp. 3386–3388,
  3394 and 3398, Eqs. (2.1)–(2.3), (2.14), (3.19)–(3.20), (5.1). The p. 3386
  discussion of the inequality is historical attribution concerning principal
  directions; that passage alone does not verify the general-direction extension.
  Lempriere's original was not inspected. ©2006 The Royal Society; no general
  reuse license verified.
- [Norris (2006), JMMS 1(4), 793–812](https://doi.org/10.2140/jomms.2006.1.793):
  publisher citation metadata and relevant publisher PDF pages visually checked.
  Section 2, printed pp. 795–796 (PDF pp. 4–5), defines orthonormal directions,
  uniaxial stress and the strain/compliance relation; Eq. (1) uses raw tensor
  shear compliance. The publisher page identifies ©2006 Mathematical Sciences
  Publishers, all rights reserved; no general reuse license verified.

Only bibliographic facts, mathematical formulas and original project curation /
derivation notes are bundled. No source PDFs, extracted article text, HTML or
figures are included. Equation-page inspection and project algebraic checks are
not independent scientific peer review. The records, project derivations and
machine-assisted translations have no independent scientific or native-speaker
review; physical realizability and finite-temperature constraints were not
systematically assessed.

## Closed catalog contract and lookup

Claims schema 1.9.0 introduces `directional_contract` only for these two scientific
families. The first records the material-class range with explicit
`unbounded_below` / `unbounded_above` statuses and `all_finite_real_numbers`;
there are no unknown or null numeric endpoints, or attained infinities. The
fixed-tensor property is separate. The second records strict, necessary-only
paired constraints. Scientific assumptions, formulas and metadata remain
language-neutral; English, Chinese, Japanese and German names and explanatory
labels are display text. Same-family extensions require the same closed
scientific contract and authored labels; different scope needs scientific and
schema review.

```sh
python -m materials_boundaries catalog claims --id directional_poissons_ratio_definition_and_range --json
python -m materials_boundaries catalog claims --id directional_poisson_reciprocity_energy_constraint --text --lang de
python -m materials_boundaries catalog claims --query '方向 ポアソン' --text --lang ja
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
```

There is no directional Poisson solver command. Existing isotropic/composite,
anisotropy-index and temperature numerical behavior is separate.

## Four-language core summary

### English

For finite real, full-SPD 3D linear elasticity about a stress-free state, under
small uniaxial stress along a unit vector n and transverse measurement along an
orthogonal unit vector m, ν(n,m) = −(mm:S:nn)/(nn:S:nn), with full S = C⁻¹.
Across this tensor class every finite real ratio is possible; a fixed finite SPD
tensor has finite attained directional extrema. Major symmetry gives reciprocity,
and strict positive energy gives |ν(n,m)| < √[E(n)/E(m)] and
0 ≤ ν(n,m)ν(m,n) < 1. These necessary pair constraints do not establish full
tensor stability. Catalog only; no numerical evaluator or specimen prediction.
The project proofs and translations have not had independent scientific or
native-speaker review.

### 中文

在无初始应力、有限实数且完整张量严格正定的三维线性小应变弹性范围内，
沿单位向量 n 施加单轴应力，沿与之正交的单位向量 m 测量横向应变。
方向泊松比为 ν(n,m) = −(mm:S:nn)/(nn:S:nn)，其中 S = C⁻¹ 是完整柔度张量。
在此张量类中变化材料和方向时，可得到任意有限实数；对每个固定的有限正定
张量，方向极小值和极大值均为有限值且可取到。主对称性给出互易关系，
严格正定能量给出 |ν(n,m)| < √[E(n)/E(m)] 和
0 ≤ ν(n,m)ν(m,n) < 1。这些成对必要条件不足以判定整个张量的稳定性。
仅供目录查询，不提供数值求解器或试样预测。项目推导和翻译尚未经过独立
科学审查或母语审校。

### 日本語

無応力の基準状態における、有限な実数成分と完全な正定値性を持つ三次元の
微小ひずみ線形弾性を対象とする。単位ベクトル n 方向に単軸応力を加え、
それに直交する単位ベクトル m 方向の横ひずみを測定する。方向別ポアソン比は
ν(n,m) = −(mm:S:nn)/(nn:S:nn) であり、S = C⁻¹ は完全なコンプライアンス
テンソルである。このテンソル集合全体では任意の有限実数を取り得るが、
固定した有限の正定値テンソルでは方向に関する最小値と最大値は有限で、
実際に達成される。主対称性から相反関係が、厳密な正定値性から
|ν(n,m)| < √[E(n)/E(m)] および 0 ≤ ν(n,m)ν(m,n) < 1 が得られる。
これらは方向の組に対する必要条件であり、テンソル全体の安定性の十分条件
ではない。カタログ情報のみで、数値計算機能や試験片の予測は提供しない。
本プロジェクトの導出と翻訳は、独立した科学的査読・母語話者の校閲を受けていない。

### Deutsch

Für endliche reelle, vollständig positiv definite 3D-Elastizität bei kleinen
Dehnungen um einen spannungsfreien Zustand gilt unter einachsigem Spannungszustand
in Einheitsrichtung n und Querdehnungsmessung in der dazu orthogonalen
Einheitsrichtung m: ν(n,m) = −(mm:S:nn)/(nn:S:nn), mit der vollständigen
Nachgiebigkeit S = C⁻¹. Über diese Tensorklasse ist jeder endliche reelle Wert
möglich; ein fester endlicher SPD-Tensor hat endliche, angenommene Richtungsextrema.
Die Hauptsymmetrie liefert die Reziprozität; strikte positive Energie liefert
|ν(n,m)| < √[E(n)/E(m)] und 0 ≤ ν(n,m)ν(m,n) < 1. Diese paarweisen notwendigen
Bedingungen reichen nicht aus, um die Stabilität des gesamten Tensors
festzustellen. Nur Katalogangaben, kein numerischer Löser und keine
Probenvorhersage. Die Projektherleitungen und Übersetzungen wurden weder
unabhängig wissenschaftlich noch muttersprachlich geprüft.
