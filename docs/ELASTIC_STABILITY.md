# Strict homogeneous elastic stability: catalog-only criteria

Historical v0.8.0 contained **eight catalog-only stability criteria**: the general, cubic, hexagonal and orthorhombic records introduced in v0.5.0, plus tetragonal I/II and rhombohedral I/II. At that release the catalog had **26 claims, 20 sources and two observations from one study**, with claims schema **1.6.0**. The original 22 claims, all 20 source records and both observations are preserved unchanged; no source is added. All eight stability records are `stability_criterion`, `direction: constraint`, `evaluation_support: catalog_only`, `bound_kind: null`. They are logical predicates, so `quantity_dimension: logical_predicate` and `si_unit: null` mean **no physical output dimension/unit**, not unknown pressure or dimensionless measured data.

There is **no stability calculator, stiffness-input API, eigensolver, material assessment or new plotted result**. The eight existing isotropic composite evaluations are unchanged. `criterion` holds display-only symbolic matrices and inequality metadata; formulas are never interpreted as code.

## Evidence, version and rights

Félix Mouhat and François-Xavier Coudert, [“Necessary and sufficient elastic stability conditions in various crystal systems”](https://doi.org/10.1103/PhysRevB.90.224104), *Physical Review B* **90**, 224104 (2014), published 5 December 2014. The [published author-hosted PDF](https://www.coudert.name/papers/10.1103_PhysRevB.90.224104.pdf) was read in full and the relevant equations visually inspected. [arXiv:1410.0065v3](https://arxiv.org/abs/1410.0065v3) is dated 5 December 2014; its DOI 10.48550/arXiv.1410.0065 is distinct from the published article DOI.

The paper bears © 2014 American Physical Society. No general CC/reuse license was established. The [arXiv nonexclusive-distribution license](https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html) is not a general license to redistribute the article. Only bibliographic metadata and original factual curation notes are bundled, not article text, figures, pages or PDFs. Source inspection and software tests are not independent scientific peer review of this catalog.

## Common scope and notation

These conditions are necessary and sufficient only for **strict elastic stability against homogeneous infinitesimal strains in the harmonic energy expansion about a stress-free equilibrium**, with a real symmetric three-dimensional elastic stiffness matrix. Special templates require axes aligned with the declared symmetry. The general full-matrix condition can use any orthonormal Cartesian orientation.

This catalog explicitly chooses engineering Voigt notation:

- Index order: xx, yy, zz, yz, xz, xy
- Strain vector e = (εxx, εyy, εzz, 2εyz, 2εxz, 2εxy)
- Stress vector s = (σxx, σyy, σzz, σyz, σxz, σxy)
- s = C e; harmonic energy density Δu = ½ eᵀ C e
- Each Cij has pressure units; e is dimensionless and Δu has units Pa = J/m³

Source footnote 19, p. 224104-4, specifies the index order. The full engineering factor-of-two convention is our explicit metadata convention, not a claim that the footnote writes out those factors. Do not mix engineering Voigt, unscaled tensor shear and Mandel numerical matrices. Positive-definiteness is invariant under the corresponding nonsingular changes of strain coordinates; numerical eigenvalue magnitudes are representation dependent.

Use a single pressure unit before multiplying coefficients. Catalog SI units are Pa, Pa² and Pa³ for linear, quadratic and cubic margins. The predicate itself has no SI unit. Different-dimensional margins must not be reduced to one raw numeric minimum.

Exclude residual/prestress or finite external load, finite-strain strength, yield, fracture, full phonon/dynamical stability, universal finite-temperature stability, 2D moduli and thin-film plane-stress reductions. Loaded-state Eq. (20) and its constant-load qualification in footnote 28 are not implemented. Elastic positivity alone does not establish all phonon modes are stable.

## Eight strict criteria

All displayed inequalities within a record must hold. Equality does **not** satisfy the strict criterion. A marginal harmonic case has a positive-semidefinite stiffness matrix with at least one zero eigenvalue; an equality together with a negative eigenvalue is not merely marginal. Nonnegative leading principal minors alone do not certify positive semidefiniteness when some vanish. Harmonic marginality alone does not settle higher-order stability or finite-amplitude failure. Near-zero rounded/uncertain coefficients require an uncertainty treatment; the catalog does not classify them.

### General positive definiteness

`general_stiffness_positive_definite` records C ≻ 0, equivalently λmin(C) > 0, or eᵀCe > 0 for every real nonzero e. Equivalently all six **leading** principal determinants Dk = det(C[1:k, 1:k]) are strictly positive. Dk has units Pa^k. The generic displayed matrix is symmetric with Cij = Cji and does not impose a crystal symmetry.

Locator: p. 224104-1, Section II, Eqs. (2)–(3) and the following numbered equivalent conditions. Positive diagonal entries by themselves are insufficient.

### Cubic

`cubic_born_stability`:

- C11 − C12 > 0
- C11 + 2 C12 > 0
- C44 > 0

C22 = C33 = C11; C13 = C23 = C12; C55 = C66 = C44. All normal-shear and off-diagonal shear couplings vanish. This is a three-independent-constant template, not three selected entries from an arbitrary anisotropic matrix.

Locator: matrix Eq. (5) and criteria Eq. (6), p. 224104-2; also Eq. (1), p. 224104-1.

### Hexagonal

`hexagonal_born_stability`:

- C11 > |C12|
- C33 (C11 + C12) − 2 C13² > 0
- C44 > 0

C22 = C11; C23 = C13; C55 = C44; C66 = (C11 − C12)/2. All other displayed couplings vanish. The C66 > 0 inequality is redundant under the first condition. The hexagonal elastic template corresponds to Laue classes 6/m and 6/mmm and has five independent constants. Do not use it for a generic five-number matrix or silently discard symmetry-breaking coefficients.

Locator: Eqs. (7)–(9), p. 224104-2.

### Orthorhombic

`orthorhombic_born_stability`:

- C11 > 0
- C11 C22 − C12² > 0
- C11 C22 C33 + 2 C12 C13 C23 − C11 C23² − C22 C13² − C33 C12² > 0
- C44 > 0; C55 > 0; C66 > 0

The normal 3×3 block is symmetric and unrestricted within these conditions; the shear block is diagonal. All normal-shear couplings vanish. These nine independent constants require the full cubic determinant condition. Checking just diagonal terms, pairwise minors or commonly quoted linear combinations is insufficient.

Locator: matrix Eq. (16), criteria Eq. (18), p. 224104-3.

### Tetragonal and rhombohedral settings

The source's **I/II labels and Laue classes are retained**: tetragonal I is 4/mmm (six independent constants), tetragonal II is 4/m (seven), rhombohedral I is −3m (six), and rhombohedral II is −3 (seven). “Trigonal” is an alias for the rhombohedral elastic templates, not an extra record. The class names and counts are from Table I, p. 224104-2.

Use right-handed **orthonormal Cartesian** axes with z along the principal fourfold axis (tetragonal) or threefold axis (rhombohedral/trigonal). For I templates, basal x is along a Laue twofold axis, equivalently the relevant Laue vertical-mirror normal. This places the trigonal coupling at C14 and sets C15=0. For II templates, fix the basal x,y orientation and retain the allowed C16 or C15; do not zero them for convenience. “Rhombohedral” does not require a nonorthogonal primitive lattice basis. A different setting requires a full tensor transformation, not a one-entry sign edit. This detailed axis prescription is an explicit project convention consistent with the matrices; it is not attributed verbatim to the paper.

For the matrices below, write a=C11, b=C12, c=C13, d=C33, e=C44, f=C66, g=C14, h=C16, j=C15, u=a+b and v=a−b. The shorthand e in these matrices denotes C44, not the engineering strain vector used above. A displayed zero is a constrained vanishing entry. All four templates require:

- C11 > |C12| (equivalently u>0 and v>0)
- C33(C11+C12) − 2C13² > 0
- C44 > 0

Each additionally requires its own fourth condition below. Every condition is strict and the full symmetry template must hold; these are not tests on selected entries of an arbitrary matrix.

### Tetragonal I: Laue 4/mmm

`tetragonal_i_born_stability`, six independent constants (a,b,c,d,e,f):

```text
[a b c 0 0 0]
[b a c 0 0 0]
[c c d 0 0 0]
[0 0 0 e 0 0]
[0 0 0 0 e 0]
[0 0 0 0 0 f]
```

Fourth condition: **C66 > 0**. C66 is independent: the hexagonal identity C66=(C11−C12)/2 must not be imposed.

Locator: matrix Eq. (7), criteria Eq. (9), p. 224104-2. Eq. (8) is the hexagonal specialization, not a tetragonal constraint.

### Tetragonal II: Laue 4/m

`tetragonal_ii_born_stability`, seven independent constants (a,b,c,d,e,f,h):

```text
[a  b c 0 0  h]
[b  a c 0 0 -h]
[c  c d 0 0  0]
[0  0 0 e 0  0]
[0  0 0 0 e  0]
[h -h 0 0 0  f]
```

Fourth condition: **C66(C11−C12) − 2C16² > 0**. C66 remains independent; checking C66>0 alone is insufficient. Preserve C26=−C16 and the factor 2 in the coupled condition.

Locator: matrix Eq. (10), criteria Eq. (11), p. 224104-2.

### Rhombohedral I / trigonal: Laue −3m

`rhombohedral_i_born_stability`, six independent constants (a,b,c,d,e,g):

```text
[a  b c  g 0  0]
[b  a c -g 0  0]
[c  c d  0 0  0]
[g -g 0  e 0  0]
[0  0 0  0 e  g]
[0  0 0  0 g v/2]
```

Fourth condition: **C44(C11−C12) − 2C14² > 0**. Here C66=(C11−C12)/2 is dependent; C24=−C14 and C56=C14 in the stated axes.

Locator: matrix Eq. (12), criteria Eq. (13), p. 224104-3.

### Rhombohedral II / trigonal: Laue −3

`rhombohedral_ii_born_stability`, seven independent constants (a,b,c,d,e,g,j):

```text
[a  b c  g  j  0]
[b  a c -g -j  0]
[c  c d  0  0  0]
[g -g 0  e  0 -j]
[j -j 0  0  e  g]
[0  0 0 -j  g v/2]
```

Fourth condition: **C44(C11−C12) − 2(C14²+C15²) > 0**. C66=(C11−C12)/2 remains dependent. Preserve C24=−C14, C25=−C15, C46=−C15 and C56=C14. The **sum** of coupling squares must be bounded with the factor 2; separate C14 and C15 inequalities are insufficient.

Locator: matrix Eq. (14), criteria Eq. (15), p. 224104-3.

### Why a determinant-only test is insufficient

Set N=d(a+b)−2c². For both rhombohedral templates,

det(C) = N [e(a−b)−2r]²/2,

where r=g² for I and r=g²+j² for II. A negative coupling margin can therefore give a positive determinant while the matrix has two negative eigenvalues. Full joint strict conditions are essential. The determinant has units Pa^6; squaring a margin does not remove its sign requirement.

As a counterexample, rhombohedral II with (a,b,c,d,e,g,j)=(150,50,40,180,60,40,40) GPa passes both separate tests g²<e(a−b)/2 and j²<e(a−b)/2: 1600<3000 GPa². Their sum is 3200 GPa², so the actual coupling margin is −400 GPa² and the matrix has two negative eigenvalues despite a positive determinant. These are invented coefficients, not a material record.

## Invented arithmetic examples, not measured materials

The following values are synthetic and used only for independent arithmetic checks in the tests. They are not accepted as evaluator inputs and yield no runtime specimen classification. Every input coefficient below is in GPa, so degree-two/three expressions use GPa²/GPa³.

- General: diag(100,100,100,40,50,60) is positive definite with λmin = 40 GPa. Adding C12 = C21 = 120 GPa gives eigenvalues −20, 40, 50, 60, 100, 220 GPa, despite every diagonal being positive. Setting the original C66 to zero fails strict positivity
- Cubic (C11,C12,C44) = (200,100,80) gives margins (100,400,80) GPa. (100,−60,40) fails the second margin at −20 GPa. (200,200,80) has a zero first margin
- Hexagonal (C11,C12,C13,C33,C44) = (150,50,40,180,60) gives 100 GPa, 32800 GPa², 60 GPa and C66 = 50 GPa. Replacing C13 by 150 gives −9000 GPa² for the quadratic margin. The exact symbolic boundary C13² = 18000 GPa² gives zero; a rounded square root is not used to assert exact equality
- Orthorhombic (C11,C22,C33,C12,C13,C23,C44,C55,C66) = (150,120,100,40,30,20,45,35,25) gives D2 = 16400 GPa² and D3 = 1520000 GPa³. (100,100,100,80,80,−80,45,35,25) has all positive diagonal terms and positive pair minors, but D3 = −1944000 GPa³. The normal block [[100,0,0],[0,100,100],[0,100,100]] with positive shear entries has D3 = 0 and fails strict positivity

These hand-checked fixtures are distinct from analytic proof and real-material validation. Tests do not parse catalog formula text or add a public stability API.

### Exact new-template boundaries and independent checks

These additional invented coefficients are in GPa; they are documentation/test fixtures, not stiffness inputs or material observations. Each row gives an exactly positive-semidefinite matrix with zero modes, so each **fails strict** stability:

| Template and parameter order | Coefficients in GPa | Exact spectrum in GPa |
| --- | --- | --- |
| Tetragonal I (a,b,c,d,e,f) | (6,2,0,3,2,0) | {0,2,2,3,4,8} |
| Tetragonal II (a,b,c,d,e,f,h) | (6,2,0,3,2,2,2) | {0,2,2,3,6,8} |
| Rhombohedral I (a,b,c,d,e,g) | (6,2,0,3,2,2) | {0,0,3,4,6,8} |
| Rhombohedral II (a,b,c,d,e,g,j) | (7,3,0,3,50,6,8) | {0,0,3,10,52,54} |

In every row, changing d=3 to d=−1 preserves the zero modes but replaces the eigenvalue 3 by −1. Such a matrix is indefinite, not positive semidefinite; equality or a zero eigenvalue alone does not justify “marginal.”

Original research checks expanded all four full matrices independently: exact leading principal minors, symbolic characteristic-polynomial factorizations, and 70-decimal-digit symmetric eigenvalue cross-checks for 1,024 synthetic integer matrices (256 per class) agreed with the strict predicates with zero mismatches. Exact-zero random draws were replaced; boundaries were checked with exact fixtures separately. Symbolic energy-invariance checks also verified the fourfold/threefold z rotations and the basal x twofold rotation for I (not generic II), supporting the declared axes and coupling signs. These are checks of transcription and synthetic algebra, not a distribution of real materials, a new runtime eigensolver, independent proof review, scientific peer review or material-specific validation.

The checked-in [crystal-stability synthetic fixture](../examples/catalog/crystal-stability-synthetic.json) contains 16 invented pass/fail/PSD/zero-plus-negative cases across the four templates. It is not accepted by `validate`, `evaluate` or comparison builders and is not measured/computed material data. The separate checked-in [regression suite](../tests/test_crystal_stability_catalog.py) independently builds matrices and uses standard-library `Fraction` arithmetic, including 1,024 seeded matrices (256 per class), without a runtime eigensolver or executing formula strings. This exact regression suite is distinct from the earlier 70-digit research cross-check described above.

## Anisotropic Poisson-ratio caveat

Do not impose the isotropic interval −1 < ν < 1/2 on every directional anisotropic Poisson response. In an anisotropic solid ν(n,m) depends on both the axial loading direction n and the transverse strain direction m, with n perpendicular to m. Positive elastic energy does not imply the isotropic range for each pair.

Supporting primary sources for this documentation-only caveat: [Ting and Chen (2005)](https://doi.org/10.1093/qjmamj/hbh021), publisher abstract inspected (full text unavailable); and [Norris (2006), “Poisson’s ratio in cubic materials”](https://doi.org/10.1098/rspa.2006.1726), [published author-hosted PDF](https://coewww.rutgers.edu/~norris/papers/2006_RSPA_462_3385-3405.pdf), pp. 3385–3387, §2(a), Eq. (2.3), defining ν(n,m) = −s′12/s′11. Relevant sections were reviewed. No text or PDF is bundled, and no open reuse license is inferred.

This caveat is not an additional catalog claim, an anisotropic calculator or a change to the existing **explicitly isotropic** composite evaluator’s −1 < ν < 0.5 gate.

## Search and rendering

```sh
python -m materials_boundaries catalog claims --claim-type stability_criterion --direction constraint --text --lang en
python -m materials_boundaries catalog claims --query "正交晶系" --text --lang zh
python -m materials_boundaries catalog claims --query "六方晶" --text --lang ja
python -m materials_boundaries catalog claims --query "Positivdefinitheitskriterium" --text --lang de
python -m materials_boundaries catalog sources --id mouhat_coudert_2014_elastic_stability --json
```

The same canonical JSON is returned in every language. Four-language authored display names are literal search aliases. Scientific translations remain unreviewed; original source title, DOI, locators and evidence text are preserved. [The original migration](MIGRATION_v0.5.0.md) explains typed predicate metadata; [v0.8.0 migration](MIGRATION_v0.8.0.md) covers the four additional explicit templates and schema 1.6.0.


The v0.15.0 [directional Poisson guide](DIRECTIONAL_POISSON.md) now gives explicit
catalog contracts, a constructive proof for every finite real value, the fixed-
tensor compactness distinction, and the strict reciprocal pair constraints.
Those necessary constraints do not replace the full stability predicates above.
