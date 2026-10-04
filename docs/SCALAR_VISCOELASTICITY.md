# Scalar creep–relaxation duality and a conditional product bound

v0.26.0 adds two **catalog-only** knowledge records. They do not add a constitutive
solver, fitted material values, observations, a passivity equivalence, or a
creep-strength/rupture prediction. The eight composite calculation rules remain
unchanged. Both quantities are dimensionless; their interpretation is different:

- `scalar_viscoelastic_creep_relaxation_duality`: normalized convolution identity
- `scalar_viscoelastic_creep_relaxation_product_bound`: same-time product bound,
  proved below as original project mathematics, **not a separately printed
  Hanyga theorem** and not a universal bound on material strength

## Conjunctive scope and notation

Use one matched scalar stress/strain channel with stress σ in Pa and strain ε
dimensionless. The response is causal, small-strain, linear and time-translation
invariant, with fixed state, temperature, moisture, phase and chemistry. Stress
and strain have zero prehistory; an initial jump is permitted. Changing loading
rates are allowed under this same fixed linear time-invariant kernel. Nonlinear
response or history/state-dependent changes to the kernel are excluded.

The relaxation kernel R is an ordinary, nonzero completely monotone (CM)
function on t>0, with finite positive R0=R(0+). Thus (-1)^n R^(n)(t)≥0 for
all integers n≥0. There is no additive instantaneous Newtonian viscosity term
N Dε: N=0 and the relaxation response contains no Dirac impulse. This does
**not** exclude all dashpots: the Maxwell series dashpot below is admitted.

Extend R continuously by R(0)=R0. J is the unique reciprocal creep function
in the stated ordinary continuous/Bernstein class. Bernstein means J≥0 and J′
is CM. R is **nonincreasing** and J is **nondecreasing**, so pure elasticity
is included. These function-class statements are not a passivity equivalence,
and positivity of an arbitrary fitted curve does not establish CM. Finite noisy
measurements cannot establish every derivative inequality.

The causal convolution is (R∗J)(t)=∫₀ᵗ R(t−s)J(s) ds. The constitutive laws
σ=R∗Dε and ε=J∗Dσ use distributional causal derivatives, including initial
jumps. H denotes the causal step; HJ is pointwise multiplication, not convolution.
The derivative D(HJ)=J0 δ₀+H J′ retains the initial compliance jump.

Units: R is Pa; J is Pa⁻¹; t and R∗J are s; real p>0 is s⁻¹; R̂ is Pa·s;
Ĵ is Pa⁻¹·s. Both (R∗J)/t and p²R̂Ĵ are dimensionless, as is R(t)J(t).
The normalized formula is never evaluated at t=0 or t=∞.

## V1. Restricted duality and reciprocal limits

Hanyga's May 2018 Theorem 1 with β=0 gives a Bernstein reciprocal satisfying
p² R̂(p) Ĵ(p)=1 for p>0, with J0=1/R0. R is bounded and J has at-most-linear
growth, so these transforms exist for every p>0. Laplace uniqueness fixes the
reciprocal in the declared class and gives

(R∗J)(t)=t, and hence (R∗J)(t)/t=1 for finite t>0.

The 2019 constitutive Eqs. (5)–(7) give the same identity with N explicitly set
to zero. Its infinite convolution upper limit is equivalent under causal zero
extension; this project uses the explicit interval [0,t].

The spectral representation R(t)=∫_[0,∞) exp(−rt) μ(dr) has a nonnegative
finite measure with total mass R0>0. It makes R(t)>0 for every finite t and
justifies continuity down to zero by dominated convergence.

The initial product limit is R0 J0=1. If R∞>0, then J∞=1/R∞ and the
long-time product limit is 1. If R∞=0, J tends to infinity; multiplying 0 by
infinity does not determine a product limit. No universal long-time product
limit is asserted in that branch. None of these endpoint statements means
J(t)=1/R(t) at finite positive times.

## V2. Finite-interval absolute continuity and the jump

This argument is original project exposition of the regularity needed for the
bound. It does **not** assume J′(0+) is finite. The Bernstein representation is

J(t)=J0+b t+∫_(0,∞) [1−exp(−rt)] ν(dr),

where b≥0 and ∫ min(1,r) ν(dr)<∞. For any finite T>0, the inequality
1−exp(−rT)≤max(1,T) min(1,r) makes the last integral finite. By Tonelli,

∫₀ᵀ J′(s) ds=bT+∫_(0,∞) [1−exp(−rT)] ν(dr)=J(T)−J0<∞.

Thus J′∈L¹(0,T) and J(t)=J0+∫₀ᵗ J′(s) ds: J is absolutely continuous on
every [0,T], even when its initial slope is infinite. For example, J0+a√t
with a>0 has the integrable, unbounded derivative a/(2√t). This is a
regularity illustration, not a fitted material law.

To justify differentiation without an unproved endpoint Leibniz rule, use
Fubini/Tonelli to write

(R∗J)(t)=J0∫₀ᵗ R(u)du+∫₀ᵗ (R∗J′)(u)du.

R is continuous and bounded on [0,T], J′∈L¹(0,T), and R∗J′ is continuous
there. The latter follows from uniform continuity of R on the overlapping
integration interval and absolute continuity of the J′ integral on the small
remaining interval. Differentiation therefore yields, for every t>0,

1=J0 R(t)+∫₀ᵗ R(t−s)J′(s) ds.

The term J0 R(t) is indispensable. Zero prehistory does not remove the initial
jump J0 δ₀. The same jump convention applies to Dε and Dσ in the input laws.

## V3. Original project product proof and sharpness

Subtract R(t)J(t) using the finite-interval representation of J:

1−R(t)J(t)=∫₀ᵗ [R(t−s)−R(t)]J′(s) ds≥0.

For 0≤s≤t, the first bracket is nonnegative because R is nonincreasing;
J′ is nonnegative. Also R(t)>0 by its nonzero nonnegative spectrum and
J(t)≥J0>0. Consequently **0<R(t)J(t)≤1 at every finite t>0**.

A pure spring, R=R0 and J=1/R0, attains 1. The analytic synthetic Maxwell
pair R=R0 exp(−t/τ), J=(1+t/τ)/R0, R0,τ>0, satisfies R∗J=t. Its transforms
are R̂=R0/(p+1/τ) and Ĵ=(1/p+1/(τp²))/R0; hence p²R̂Ĵ=1.
At fixed t>0, x=t/τ ranges over (0,∞) as τ varies. The product (1+x)exp(−x)
has derivative −x exp(−x)<0 and runs continuously from 1 toward 0.
Every value in (0,1) is attained within this class; zero is only an infimum.
Together with the pure spring, the attainable range across the class at each
fixed positive time is (0,1]. This is not an absolute modulus/compliance bound.

## V4. Original synthetic SLS counterexample to product monotonicity

For E,τ>0 let R=E[1+exp(−t/τ)] and
J=E⁻¹[1−½ exp(−t/(2τ))]. This standard-linear-solid pair has
R0=2E, J0=1/(2E), R∞=E and J∞=1/E. Its explicit rational transforms satisfy
p²R̂Ĵ=1. With q=exp(−t/(2τ)),

1−R(t)J(t)=q(1−q)²/2>0 for finite t>0.

The product tends to 1 at both endpoints and is lower between them, so it is
not monotone. R nonincreasing and J nondecreasing do not imply monotonicity of
their product. These Maxwell and SLS calculations are analytic synthetic checks,
not measured data or independent empirical validation.

## Sources, versions, limitations and rights

1. Andrzej Hanyga, *A simple proof of a duality theorem with applications in
   scalar and anisotropic viscoelasticity*, [arXiv:1805.07275v1](https://arxiv.org/abs/1805.07275v1),
   17 May 2018. Section 3, Theorem 1, printed/PDF p. 4, Eqs. (8)–(9) and
   spectral representation (11); construction p. 5; Theorem 2 p. 6;
   definitions pp. 12–13. The inspected [v1 PDF](https://arxiv.org/pdf/1805.07275v1)
   SHA-256 is ef3d0ebd899b5d66e971ef1a334c798b335b42624e67759db99c0182d8366fb8.
   No journal publication for this version was verified. This is the May
   preprint, not the April 1804.03690 preprint. Minor wording/notation defects
   in Theorem 2, Appendix A and Eq. (19) are not copied into the project proof.
2. Andrzej Hanyga, *Effects of Newtonian viscosity and relaxation on linear
   viscoelastic wave propagation*, [arXiv:1903.03814v8](https://arxiv.org/abs/1903.03814v8),
   2 November 2019. Section 2, printed/PDF p. 3, constitutive paragraph and
   Eqs. (5)–(7), N=0. The successfully inspected [official PDF URL](https://arxiv.org/pdf/1903.03814)
   was unversioned but its title page identified v8; SHA-256 is
   8082a81364c181ee079786462b7634c3fcb8b642df9e46e73df4396e0ca5f958.
   The checksum identifies inspected bytes, not future content of that URL.
   ArXiv associates this article with *Archive of Applied Mechanics* (2019),
   [DOI 10.1007/s00419-019-01620-2](https://doi.org/10.1007/s00419-019-01620-2).
   The publisher version was not inspected and version equivalence is not
   asserted. Its N=1/J′(0+) discussion belongs to the zero-initial-creep
   Newtonian branch and is not applied to the present Maxwell example.

The two sources share an author and are not independent validation. The
mathematical admission check and software tests do not certify scientific peer
review, real-material applicability, physical realizability, or native-language
scientific review. The sources establish constitutive duality/function classes;
the product proof, explicit regularity exposition and examples above are
original project work, not source quotation.

Both abstract pages link the [arXiv nonexclusive distribution license](https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html).
That grants distribution permission to arXiv; it is not CC BY or a general
project redistribution license. Only bibliographic metadata, links, mathematical
facts, original paraphrases and original project proofs are bundled. No source
PDF, extracted text dump, screenshot, figure or source TeX is redistributed.
The project's MIT license does not relicense these publications.

Excluded: aging/two-time kernels; nonlinear/finite-strain behavior; kernel changes
with history or state; changing temperature/material state; damage/plasticity,
tertiary creep or rupture; singular-at-zero relaxation and additive Newtonian
impulses; tensor/componentwise inverses; mismatched channels/specimens/conditions;
and unverified instrument inertia or wave corrections. No new NIST data,
denied-mirror source, observation, plot profile or fitted model is introduced.

## Inspecting the records

`python -m materials_boundaries catalog claims --query viscoelastic --text --lang en`

The same route supports `zh`, `ja` and `de`. Formulas, IDs, original source
metadata and closed contract detail stay canonical. Localized warnings retain
conditional scope, initial jump, source/project attribution and exclusions.
Translations are machine-assisted and not scientifically reviewed by native
speakers. Text formulas are never executed.
