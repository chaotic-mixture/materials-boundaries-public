# Initial-yield criteria and a sharp function comparison

Version 0.27.0 adds exactly three **catalog-only** records:

| Record | Classification | Quantity / SI unit |
| --- | --- | --- |
| `von_mises_initial_yield_relation` | `model_relation`, `direction: relation`, null `bound_kind` | von Mises equivalent stress / Pa |
| `tresca_initial_yield_relation` | `model_relation`, `direction: relation`, null `bound_kind` | Tresca equivalent stress / Pa |
| `tresca_von_mises_equivalent_stress_ratio_bound` | `theoretical_bound`, `direction: interval`, `bound_kind: criterion_function_comparison` | Tresca/von Mises equivalent-stress ratio / 1 |

These are two stress-function definitions with restricted initial-yield model
interpretations and one exact mathematical function comparison. They add no
numerical yield evaluator, material parameters, specimen checks, constitutive
integration, strength certification or new plotted output. All three have
`evaluation_support: catalog_only`; the existing eight composite calculation
rules remain the only executable rules. Reading a record does not manufacture
an instance with `satisfied`, `violated` or `unknown` applicability status.

## Stress, sign, units and tensor conventions

Use one **finite, real, symmetric three-dimensional Cauchy stress tensor**
`sigma` at one material point, with tension positive and ordinary continuum
stress, without couple-stress effects. Principal stresses are eigenvalues of
this same tensor. The stress-function algebra itself is defined for every such
tensor, independently of whether either yield model fits an actual material.

Define the deviator `s = sigma - tr(sigma)*I/3` and `J2 = (s:s)/2`. Components
are ordinary **tensor shear components**, not doubled engineering-strain
components:

```text
s:s = sum_i s_ii^2 + 2*sum_(i<j) s_ij^2
```

`sigma`, principal stresses, `s`, `q_VM`, `q_T`, `tau_max`, `Y` and the dimensional
yield functions `f_VM`, `f_T` have pressure units Pa. `J2` has units Pa^2.
Normalized `q/Y`, the comparison ratio and load multipliers are dimensionless.

At a hydrostatic state `sigma = p*I`, **p = tr(sigma)/3 is signed hydrostatic
normal stress under the tension-positive convention**. It is opposite in sign
to compression-positive hydrostatic pressure. In an arbitrary shift `h*I`, h
is the signed hydrostatic normal-stress increment. No compression-positive
pressure convention is silently substituted.

## Von Mises definition and model relation

```text
q_VM = sqrt(3*J2)
     = sqrt(((sigma1-sigma2)^2 + (sigma2-sigma3)^2
             + (sigma3-sigma1)^2)/2)
f_VM = q_VM - Y
```

For a declared fixed `Y > 0`, the model initial-yield boundary is `f_VM = 0`.
Negative f is the interior of the model's elastic domain; positive f is outside
that domain. These are definitions within the model, not catalog evaluations of
measured material behavior. No plastic-strain or post-yield prediction follows.

The primary equation anchors are Giraldo-Londoño–Paulino (2020), printed/PDF
p. 3 Eqs. (2.3)–(2.4) and p. 4 Eqs. (2.8)–(2.11), plus Wierzbicki (2013),
section 12.4, printed p. 12-6 / PDF p. 6, Eqs. (12.17)–(12.18).

## Tresca definition and model relation

```text
q_T = max(abs(sigma1-sigma2), abs(sigma2-sigma3), abs(sigma3-sigma1))
sigma1 >= sigma2 >= sigma3  =>  q_T = sigma1-sigma3 = 2*tau_max
f_T = q_T - Y
```

The same model interpretation of `f_T = 0`, `f_T < 0` and `f_T > 0` applies.
The equivalent stress is **twice maximum shear stress**; uniaxial calibration
gives the boundary `tau_max = Y/2`, not `tau_max = Y`. Use the exact, unsmoothed
Tresca criterion. Rounded or smoothed numerical approximations in a source are
not part of this admission.

Anchors: Giraldo-Londoño–Paulino section 2(b), p. 5 Eq. (2.15), using `alpha=1/Y`
from p. 4 Eq. (2.10); Wierzbicki section 12.8, printed p. 12-13 / PDF p. 13,
Eqs. (12.47)–(12.48).

### Source normalization is not a dimensional catalog parameter

In Giraldo-Londoño–Paulino, p. 4 Eq. (2.5) and Eqs. (2.8)–(2.11), (2.15),
`sigma_eq,VM = q_VM/Y` and `sigma_eq,T = q_T/Y` are **dimensionless**, and
`Lambda = f/Y`. This catalog's q and f are dimensional. A source's normalized
`sigma_eq` or `Lambda` must not be copied into a Pa-valued parameter unchanged.

## Restricted physical interpretation and calibration

The following conditions are conjunctive project admission restrictions for
using these functions as **phenomenological initial-yield models**. They are
not a claim that every cited source states every exclusion, or that every
ductile material obeys them:

1. Declare an isotropic, pressure-insensitive, tension/compression-symmetric
   model, restricted here to small strain, quasistatic loading and
   rate-independent response at a fixed material state and temperature
2. Supply **Y > 0** from a declared uniaxial tensile yield calibration with
   matching material state, temperature, rate regime, Cauchy stress measure
   and yield-definition convention. No elastic constant determines Y in this
   catalog, and no numerical Y or actual material calibration is supplied
3. A proof stress retains its stated offset convention. It is not silently
   promoted to an experimentally demonstrated sharp initial-yield onset;
   the source's introductory numerical offset discussion is not imported
4. Model-to-model yield-threshold comparison uses **the exact same Y**. A
   shared measured pure-shear calibration `tau_c` instead gives different
   uniaxial parameters `Y_T = 2*tau_c`, `Y_VM = sqrt(3)*tau_c`; it cannot justify
   the same-Y threshold-order statement below
5. These centered initial surfaces have no modeled backstress evolution.
   Neither `q-Y = 0` specifies hardening, plastic-flow direction, an
   associated-flow assertion, loading/unloading integration or post-yield strain
6. Anisotropic or pressure-sensitive yielding, tension/compression asymmetry,
   porous damage, evolving material state, finite-strain constitutive evolution,
   cyclic plasticity and rate-dependent flow lie outside this physical scope
7. Hydrostatic invariance describes the stress functions only. It does not
   establish survival against hydrostatic damage, cavitation, phase changes or
   other real-material failure modes

The mathematical comparison below does **not** require isotropy, a measured Y,
a material fit or satisfaction of these physical-model premises. It requires
the same supplied tensor, same stress measure and these exact function
definitions. Physical exclusions do not revoke that purely algebraic result.

## Exact comparison and hydrostatic domain

For a nonhydrostatic finite real symmetric 3D stress tensor:

```text
1 <= q_T/q_VM <= 2/sqrt(3)
```

Both endpoints are inclusive and attained. The equivalent **division-free**
form is valid for every such tensor, including hydrostatic states:

```text
q_VM <= q_T <= (2/sqrt(3))*q_VM
```

At `sigma = p*I`, `s = 0`, `q_VM = q_T = 0` and the ratio is **undefined**.
Do not replace 0/0 with 1 or supply an invented hydrostatic extension. There is
no unique limiting ratio there: uniaxial and pure-shear deviatoric approaches
reach the two different endpoints. The division-free inequalities simply have
equality throughout at zero.

### Original project proof and exact endpoints

The sources support the function definitions. The following sharp comparison
and proof are **original project algebra**, not a separately printed source
theorem or a claim of independent expert scientific review.

Order the principal stresses and put `a = sigma1-sigma2 >= 0`,
`b = sigma2-sigma3 >= 0`. Then

```text
q_T = a+b
q_VM^2 = a^2+a*b+b^2
q_T^2-q_VM^2 = a*b >= 0
(4/3)*q_VM^2-q_T^2 = (a-b)^2/3 >= 0
```

Nonnegativity permits taking square roots to obtain the division-free bound.
Division by q_VM is valid exactly in the nonhydrostatic branch. In that branch:

- The lower endpoint is attained exactly when `a*b = 0`, so two principal
  stresses coincide
- The upper endpoint is attained exactly when `a = b > 0`, so
  `sigma2 = (sigma1+sigma3)/2`

Neither constant can be tightened. Original symbolic examples, not
source-reported measurements, are:

- `diag(S,0,0)`, S > 0: `q_T = q_VM = S`
- `diag(T,0,-T)`, T > 0: `q_T = 2*T`, `q_VM = sqrt(3)*T`
- Adding any hydrostatic `h*I` leaves both stress functions unchanged

The admission check also verified both identities on 441 exact-rational gap
pairs `a=i/7`, `b=j/11`, i,j = 0,...,20. Such arithmetic checks supplement the
proof; they are neither its replacement nor empirical material validation.

### Optional consequence for one fixed local proportional stress ray

For `sigma(lambda) = lambda*Sigma`, lambda >= 0, **one fixed nonhydrostatic
Sigma and one common fixed Y > 0**, positive homogeneity yields

```text
lambda_T = Y/q_T(Sigma)
lambda_VM = Y/q_VM(Sigma)
1 <= lambda_VM/lambda_T <= 2/sqrt(3)
```

The von Mises model threshold is at most `2/sqrt(3)-1`, approximately **15.47%**,
above the Tresca model threshold **relative to the Tresca threshold**. This
is not a universal material error, guaranteed safety margin, real-strength
bracket or statement about arbitrary loading histories. It does not transfer
automatically to different calibrations, evolving plasticity, residual-stress
paths or nonproportional loading. For a hydrostatic ray neither function reaches
positive Y, so this finite-threshold ratio is inapplicable.

Under the same initial uniaxial Y, symbolic pure-shear substitution gives
`tau_T = Y/2`, `tau_VM = Y/sqrt(3)`. These are project substitutions into the
definitions, not measured shear strengths. No general loading-path capability
or numerical plasticity integration is introduced.

## Evidence ledger and rights

### Giraldo-Londoño and Paulino (2020)

Source ID: `giraldo_londono_paulino_2020_yield_criteria`.
Oliver Giraldo-Londoño and Glaucio H. Paulino, *A unified approach for topology
optimization with local stress constraints considering various failure criteria:
von Mises, Drucker–Prager, Tresca, Mohr–Coulomb, Bresler–Pister and
Willam–Warnke*, Proceedings of the Royal Society A 476(2238), 20190861.
[DOI](https://doi.org/10.1098/rspa.2019.0861) ·
[Inspected author-hosted PDF](https://paulino.scholar.princeton.edu/sites/g/files/toruqf6546/files/documents/RSPA_20_AUnifiedApproach.pdf).

The 26-page author-hosted publisher-layout PDF was available. The title page
and printed/PDF pp. 3–5 were visually checked and the cited definitions/equations
text-checked. No full-paper or numerical-study validation is claimed. No
explicit revision label is present; the inspected-byte SHA-256 is
`ca6e6d895fd16caa46ad3f68bcd1272425317c268cd332b837732d362bec482c`.
Current publisher retrieval failed, so equivalence to its current hosted bytes
is not asserted. The exact equation anchors and normalization are above.

The title page states ©2020 authors, published by the Royal Society, all rights
reserved. No permissive reuse license was verified. Author hosting is not a
redistribution grant. The evidence status identifies selected primary equations
as visually checked; the project comparison proof remains separate.

### Wierzbicki (2013), MIT Structural Mechanics Lecture 12

Source ID: `wierzbicki_2013_structural_plasticity`.
Tomasz Wierzbicki, *Fundamental Concepts in Structural Plasticity*, Lecture 12,
MIT 2.080J / 1.573J Structural Mechanics, Fall 2013.
[Official resource](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013/resources/mit2_080jf13_lecture12/) ·
[Official PDF](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013/30dc1a0f74debf21fb92a1df56616929_MIT2_080JF13_Lecture12.pdf).

The 20-page PDF was available; printed pp. 12-6, 12-8, 12-13 and 12-15
(PDF pp. 6, 8, 13 and 15) were visually checked. The official course
resource/footer establishes Fall 2013; running headers retain the unfilled
wording “Semester Yr.” Inspected-byte SHA-256:
`b4a19b30e6fa5a7f79ed8e003b06b4c434799ebc44c016aeb751e498f126ea49`.

**Observed printing defects in this inspected copy, not verified
publisher-issued errata:** Eq. (12.22) omits the square root and is dimensionally
inconsistent; Eq. (12.46) duplicates a principal-stress pair. Neither is used.
The admitted anchors are the sound squared von Mises Eqs. (12.17)–(12.18)
and Tresca Eqs. (12.47)–(12.48). The rounded, loosely specified comparison on
printed p. 12-15 is not the proof of the exact bound. Its introductory numerical
proof-stress-offset discussion is also excluded.

The [official MIT OCW terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/),
checked 2026-10-04, state [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
Its attribution, noncommercial and share-alike conditions are not an
unconditional grant to relicense adapted source assets under MIT.

### Redistribution and review limits

Only bibliographic metadata, exact links, independently expressed mathematical
facts, original curation and separately labeled project proof are admitted.
No source PDFs, screenshots, extracted prose, page images, figures,
experimental plot data or source assets enter the repository, package or release.
MIT covers original project work, not third-party works or scientific facts.
No NIST coefficients, JARVIS mirror, new material values or source graphics are
added. The two publications are distinct direct evidence sources; neither is a
verified historical-original publication of the classical criteria. Formula
agreement, project audits and software tests are not independent scientific
peer review, empirical validation, material-specific adequacy or legal clearance.
Scientific expert and native-language review remain unperformed.

## Four-language catalog usage

```sh
python -m materials_boundaries catalog claims --id von_mises_initial_yield_relation --text --lang en
python -m materials_boundaries catalog claims --id tresca_initial_yield_relation --text --lang zh
python -m materials_boundaries catalog claims --id tresca_von_mises_equivalent_stress_ratio_bound --text --lang ja
python -m materials_boundaries catalog claims --source-id giraldo_londono_paulino_2020_yield_criteria --text --lang de
python -m materials_boundaries catalog sources --id wierzbicki_2013_structural_plasticity --json
```

English: initial-yield relations and an exact stress-function comparison only;
no material-strength certification or numerical yield evaluation.

中文：仅收录初始屈服模型关系与等效应力函数的严格比较；不进行材料强度认证或数值屈服求解。静水状态下比值未定义。

日本語：初期降伏のモデル関係と等価応力関数の厳密な比較を収録するだけで、材料強度の認証や数値的な降伏判定は行いません。静水圧応力状態では比は未定義です。

Deutsch: Nur Anfangsfließmodelle und ein exakter Vergleich der
Vergleichsspannungsfunktionen; keine Festigkeitszertifizierung oder numerische
Fließbewertung. Bei hydrostatischer Spannung ist das Verhältnis undefiniert.

Canonical IDs, formulas and units are not translated. All new records have
authored en/zh/ja/de display names. Locale and placeholder checks do not imply
native-speaker or scientific translation review. See [migration](MIGRATION_v0.27.0.md),
[source ledger](SOURCES.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).
