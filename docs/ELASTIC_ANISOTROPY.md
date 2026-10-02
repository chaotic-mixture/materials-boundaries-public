# Elastic anisotropy indices: definitions and scoped ranges

v0.11.0 adds two **catalog-only index definitions** under `model_relation` /
`relation`. They are dimensionless (SI unit `1`), with `bound_kind: null` and
no numerical runtime dependency. The separate `index_range` object records a
conditional mathematical range; it does not reclassify a definition as a
strength/performance bound. Neither record is an empirical material fit.

| Record | Definition | Mathematical range | Isotropy equality |
|---|---|---|---|
| `zener_cubic_elastic_anisotropy_index` | A = 2 C44 / (C11 − C12) | (0, ∞) | A = 1 iff cubic elastic isotropy |
| `universal_elastic_anisotropy_index` | AU = 5 GV/GR + KV/KR − 6 | [0, ∞) | AU = 0 iff elastic isotropy |

These ranges concern the **stated finite real strictly positive-definite 3D
elastic-tensor model class**. “Unbounded” means this class has no finite upper
maximum. Every finite positive-definite input has a finite index. Infinity is
not an attained index, a JSON number, a measured value or a sampled maximum.
This statement does not assert a physically realizable material for every tensor
or include all additional microscopic material constraints.

## Shared conditions and conventions

The scope is infinitesimal, stress-free, real 3D linear elasticity with minor and
major tensor symmetries and strictly positive elastic energy for every nonzero
symmetric strain. Singular, positive-semidefinite and indefinite tensors,
complex viscoelastic moduli, 2D reductions and unchecked raw prestress elastic
coefficients are excluded. Homogeneous elastic stability alone is not a phonon,
full thermodynamic stability or material-suitability certificate.

Use engineering-Voigt order (11, 22, 33, 23, 13, 12):

- strain vector: (ε11, ε22, ε33, 2ε23, 2ε13, 2ε12)
- stress vector: (σ11, σ22, σ33, σ23, σ13, σ12)
- σ = C e and energy density = eᵀ C e / 2
- engineering C44 = C2323, but engineering S44 = 4 S2323
- S is the inverse of the **full** engineering 6×6 C, not componentwise reciprocals

Kelvin/Mandel has different shear scaling. If W = diag(1,1,1,√2,√2,√2),
C_K = W C_eng W and S_K = W⁻¹ S_eng W⁻¹. Convert consistently before using
engineering components; inserting a raw Kelvin C44 doubles the Zener numerator.
The maps are convention algebra, not an additional material model.

## Cubic Zener index

Use the natural cubic crystallographic frame with axes along ⟨100⟩. Strict cubic
stability requires C11−C12 > 0, C11+2C12 > 0 and C44 > 0. Consequently A > 0,
and A = 1 is equivalent to C11−C12 = 2C44, the isotropic condition within cubic
symmetry. **A can be below 1**; it is not necessarily a maximum/minimum ratio.

The range (0,∞) is derived from the definition and strict cubic-stability domain.
It is not attributed to a directly inspected theorem in the original Zener book.
A = 0 is excluded, as is a zero denominator; near-zero values require a separate
numerical tolerance policy if a solver is ever developed.

Definition evidence: Ranganathan and Ostoja-Starzewski (2008), printed 055504-1,
Eq. (1); Knowles and Howie (2015), p. 90, Eq. (10). The latter gives the mapping
and cubic isotropy condition on p. 89, Eqs. (3), (5). Strict stability uses the
Mouhat–Coudert 2014 source record, preserved unchanged; this batch’s supporting
equation checks use author-submitted arXiv v3, p. 2, Eqs. (5)–(6).

## Universal index: orientation average matters

Use normalized uniform full-orientation averaging over SO(3), equivalently the
Euler-angle measure sin(φ) dψ1 dψ2 dφ / (8π²), with ψ1, ψ2 in [0,2π] and
φ in [0,π]. Average the full stiffness C and its full inverse S **separately**:

- Cᵛ = ⟨C⟩ = 3 KV J + 2 GV D
- Sʳ = ⟨C⁻¹⟩ = J/(3 KR) + D/(2 GR)
- J is the hydrostatic projector; D = I_sym − J is the deviatoric projector
- generally ⟨C⁻¹⟩ ≠ ⟨C⟩⁻¹

The source calls the deviatoric projector bold K; that is not bulk modulus K.
KV, GV, KR, GR are positive orientation-derived moduli of one elastic tensor.
They are not the existing two-phase composite Reuss/Voigt output records, and
no dependency or inferred compatibility with those outputs is declared.
Texture-weighted averaging, averaging only directions, and averaging directional
Young moduli do not implement this contract.

AU ≥ 0, with equality iff isotropy in the stated domain. Zero is included. The
2008 PRL printed 055504-2 Eqs. (7a–b), (8), (9) define the construction; the 2011
follow-on printed 064501-1 Eqs. (2)–(4) spells out orientation averaging, and
064501-2 Eqs. (5)–(6), surrounding text and Fig. 1 support equality and range.

**Source QA:** extraction of the 2011 paper falsely rendered the upper end as
“1”. The visually checked page says infinity. Never ingest a maximum of 1.

## Published identity and project algebraic checks

The 2008 PRL printed 055504-2 Eq. (10) publishes the exact cubic identity
AU = (6/5)(√A − 1/√A)² and states KV = KR. Expanding gives
AU = (6/5)(A + 1/A − 2). Reciprocal A values therefore have equal AU;
AU alone does not reconstruct the tensor or its strength.

For project-only synthetic arithmetic, let d = C11−C12 and g = C44.
In the cubic tensor, the hydrostatic eigenvalue is C11+2C12, the two diagonal
deviatoric Kelvin eigenvalues are d, and the three off-diagonal Kelvin eigenvalues
are 2g. Isotropic projection averages those five deviatoric eigenvalues:
2GV = (2d+6g)/5. Separately averaging their inverse eigenvalues gives
1/(2GR) = (2/d+3/(2g))/5. Hence:

- KV = KR = (C11+2C12)/3
- GV = (d+3g)/5
- GR = 5dg/(4g+3d)

This is a project algebraic derivation from the averaging definition. It is not a
new source observation, primary measurement or numerical production API.

| Synthetic C11,C12,C44 (GPa) | A | AU |
|---|---|---|
| 200,100,50 | 1 | 0 |
| 200,100,25 | 1/2 | 3/5 |
| 200,100,100 | 2 | 3/5 |

The synthetic family C11=200, C12=100, C44=50t GPa, t>0, has strict stability,
A=t and AU=(6/5)(t+1/t−2). Its limits demonstrate unboundedness over this tensor
class, without asserting physical realization. Zero shear or C11=C12 leaves the
strict domain and is not a permitted limiting material input. Tests use exact
rational arithmetic; these checks never execute catalog formula strings.

## Sources, inspection and reuse

- [Ranganathan and Ostoja-Starzewski (2008), PRL 101, 055504](https://doi.org/10.1103/PhysRevLett.101.055504): author-hosted full paper read and defining pages visually checked; ©2008 APS; no open reuse license verified
- [Ranganathan, Ostoja-Starzewski and Ferrari (2011), JAM 78, 064501](https://doi.org/10.1115/1.4004553): author-hosted full paper read, equations and infinity symbol visually checked; ©2011 ASME; open reuse license unverified. 064501 is the article number, not DOI suffix 4004553
- [Knowles and Howie (2015), Journal of Elasticity 120, 87–108](https://doi.org/10.1007/s10659-014-9506-1): official publisher HTML/PDF inspected; p.107 states Creative Commons Attribution without a version in the inspected text. No version-specific identifier is invented
- [Zener (1948), Elasticity and Anelasticity of Metals](https://books.google.com/books/about/Elasticity_and_Anelasticity_of_Metals.html?id=FKcZAAAAIAAJ): metadata-only historical attribution; University of Chicago Press. Original body/equation/page not inspected, DOI unknown. The 1949 ACS item DOI 10.1021/j150474a017 is not the book DOI
- [Mouhat and Coudert (2014), PRB 90, 224104](https://doi.org/10.1103/PhysRevB.90.224104): existing 2014 stability source record preserved; this batch’s supporting checks use author-submitted arXiv v3. arXiv distribution terms are not a general CC reuse grant

No papers, PDFs or source figures are bundled. Equation/page checking, software
review and rational test arithmetic are distinct from independent scientific
peer review, native-language review and specimen validation; none is claimed.

## Schema, contribution and display boundary

Claims schema 1.8.0 adds only two closed scientific families, two dimensionless
quantities and `index_range`. Its finite lower endpoint has explicit inclusion;
the upper endpoint is `{ "status": "unbounded", "scope":
"stated_positive_definite_elastic_tensor_class" }`. That status is **not unknown**.
Null, unknown, finite or nonfinite upper values are rejected for these families.
Range basis and isotropy equality are separate from `formula_display` and from
`verification.independent_scientific_review`, which remains false.

Same-family contributions may use fresh IDs, sources, evidence and four authored
labels, while retaining the exact definition, assumptions, parameter contracts
and range. A different averaging scheme or symmetry requires scientific/schema
review. Index metadata cannot be attached to unrelated families.

```sh
python -m materials_boundaries catalog claims --query anisotropy --text --lang en
python -m materials_boundaries catalog claims --id zener_cubic_elastic_anisotropy_index --json
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
```

There is no anisotropy solver command, automatic plot or stiffness input schema.
All eight composite outputs and isolated temperature-fit numerical behavior stay
unchanged. The two temperature models remain a separate scientific contract.
