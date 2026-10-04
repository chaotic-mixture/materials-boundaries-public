# Supported model and numerical contract

## Scope is part of the claim

Version 0.8.0 preserves the eight evaluations introduced in v0.2.0: HS, Reuss and Voigt bounds for bulk modulus K and shear modulus G, followed by derived outer envelopes for Young's modulus E and Poisson's ratio ν. Inputs describe two constituents of a homogenized effective material, not a finite specimen or arbitrary apparent boundary-condition modulus. The supplied assertions are 3D, small-strain, static, linear elastic, perfectly bonded, constituent-isotropic and effectively isotropic. All active constituent K and G must be strictly positive. The HS registry additionally requires non-strict well-ordering: (K1−K2)(G1−G2) ≥ 0. The derived envelopes require both HS claims, so inherit that restriction. Reuss/Voigt use the same conservative positive-phase conditions without well-ordering. This implementation boundary is not the maximal domain of the underlying theory.

No code decides whether a proposed microstructure is effectively isotropic. In particular an isotropic macroscopic response made from anisotropic constituents cannot satisfy the constituent-isotropy assertion. Strength, failure, fracture, yield and plasticity are not supported. Neither negative stiffness, active void/zero-stiffness phases, anisotropic constituents, imperfect interfaces, dynamic/finite-strain behavior nor a joint attainable K/G region is implemented.

The separate [v0.6.0 porous catalog](POROUS_BOUNDS.md) records solid/void limits without extending this runtime scope. Its three pressure-valued intervals are `catalog_only`; no porous parameters, density calculation, empty-domain Poisson ratio or new chart are accepted here. Its documentation-only synthetic JSON is not a material-instance input.

The separate [v0.7.0 observations catalog](OBSERVATIONS.md) adds two model-dependent AFM property summaries from one graphene study, with canonical N/m units. It does not extend the evaluator, introduce thickness conversion, or accept measured observations as composite inputs. The source's nonlinear breaking-strength inference is catalog context, not executable failure behavior. Reported ± values with unverified statistical meaning are not theoretical bound endpoints or inputs to uncertainty propagation.

The historical [v0.8.0 stability extension](ELASTIC_STABILITY.md) brings the catalog to eight strict stability predicates and 26 total claims under schema 1.6.0. Tetragonal I/II and rhombohedral I/II remain display-only full-tensor templates. They neither accept stiffness inputs nor evaluate specimens, and they do not expand the explicitly isotropic scalar-modulus calculator. Its eight results change only in engine version 0.8.0; source and observation records remain unchanged.

## Scalar-modulus equations

For normalized volume fractions f1 + f2 = 1 and positive scalar phase moduli x1, x2, define

- A(x) = f1 x1 + f2 x2
- D(x) = f1 x2 + f2 x1
- R(x1,x2,c) = (x1 x2 + c A(x)) / (D(x) + c)
- Reuss(x) = 1 / (f1/x1 + f2/x2)
- Voigt(x) = A(x)

Apply Reuss and Voigt separately to x = K and x = G. For HS, label complete phase records so that K1 ≤ K2 and G1 ≤ G2 simultaneously, preserving the K/G/f association; never sort the two modulus arrays independently. Then

- K lower = R(K1,K2,4G1/3)
- K upper = R(K1,K2,4G2/3)
- ζ(K,G) = G(9K + 8G)/(6K + 12G)
- G lower = R(G1,G2,ζ(K1,G1))
- G upper = R(G1,G2,ζ(K2,G2))

The rational expression is algebraically equivalent to A(x) − f1 f2 (x1−x2)²/(D(x)+c). The bulk forms are cross-checked against [Kochmann–Milton, arXiv v1, equations (117)/(134)](https://arxiv.org/html/1401.4142v1); the shear forms use (118)/(135). This positive form avoids subtracting large nearly equal terms and never divides by a modulus contrast. It is an implementation rearrangement, not a new theoretical bound. Original Hashin–Shtrikman (1963) equation locations and proof remain uninspected; see [Sources](SOURCES.md).

The Reuss expressions retain contextual support from the Kochmann–Milton introduction; an original Reuss equation locator has not been established. Section 4.4 equations (132)–(133), printed/PDF p. 20 of arXiv v1, are translated **bulk**-compliance relations, not a displayed unshifted shear Reuss formula. They do not establish a direct specialization of the implemented shear expression.

For positive inputs R(x1,x2,0) = Reuss(x), and R increases toward Voigt as c grows. Equal K makes every bulk endpoint K; equal G makes both HS bulk endpoints coincide and every shear endpoint G. Equal K alone need not collapse the shear interval. Pure-phase fractions give the active K/G; E/ν follow the isotropic identities below. No geometry or simultaneous bulk/shear attainability is inferred.

## Derived E and ν outer envelopes

For a positive, isotropic effective material,

- E(K,G) = 9KG/(3K+G)
- ν(K,G) = (3K−2G)/(2(3K+G))

These identities are supported by [Meille & Garboczi (2001), Section 2.2, equation (3), printed p. 374 / PDF page 4](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=860321). The extracted text gives 9/E = 1/K + 3/G, rearranged above, and the displayed ν identity. On 2026-10-04 the rendered publisher-typeset NIST-hosted PDF was visually checked at equation (3), printed p. 374 / PDF p. 4, and at the cover. This completed identity-source check supersedes the earlier unsuccessful render attempt; it is not independent scientific or proof review. Only the 3D identities are used, not the separate 2D equation (4). The source supports the identities only: the outer-envelope construction and monotonicity argument below are project derivations, and the paper is not used to establish this composite's premises or tight joint bounds.

E is increasing in both K and G. ν is increasing in K and decreasing in G. Therefore separate compatible HS intervals K ∈ [Klow,Khigh] and G ∈ [Glow,Ghigh] imply

- E lower = E(Klow,Glow); E upper = E(Khigh,Ghigh)
- ν lower = ν(Klow,Ghigh); ν upper = ν(Khigh,Glow)

These are **conservative derived outer envelopes**, not independently established tight joint attainable limits. The rectangle formed from two marginal bounds may contain K/G pairs that no common microstructure can realize. In particular, computing an envelope corner does not prove simultaneous attainability of its component endpoints. These intervals are also not specimen predictions or propagated experimental uncertainty.

The fixed rules depend only on `hs_bulk_3d_two_phase` and `hs_shear_3d_two_phase`, evaluated for the same input instance, phase pairing, normalized fractions, units and conditions. There is no public operation combining arbitrary evaluated intervals from different systems. Derived output includes `quantity`, `bound_kind: derived_outer_envelope`, and dependency metadata with the input instance ID and both claim IDs; its `joint_attainability` value is `not_asserted`. Unknown or violated prerequisites suppress numeric results. Unordered phases do not trigger a Reuss/Voigt fallback for E or ν. If either HS dependency has a numerical range error in the selected output unit, dependent results are also unavailable rather than silently using a different dependency path.

### Synthetic exact-arithmetic fixture

For (K1,G1) = (10,5) GPa, (K2,G2) = (30,15) GPa, and f1 = f2 = 1/2:

| Quantity | Reuss lower | HS lower | HS upper | Voigt upper |
| --- | ---: | ---: | ---: | ---: |
| K (GPa) | 15 | 65/4 | 35/2 | 20 |
| G (GPa) | 15/2 | 310/37 | 190/21 | 10 |

The derived E envelope is [36270/1691, 11970/517] GPa, approximately [21.4488468362, 23.1528046422] GPa. The derived ν envelope is [515/1942, 529/1802], approximately [0.265190525232, 0.293562708102], with dimensionless unit `1`. These rational fixture values illustrate the formulas; serialized program output remains approximate.

## Applicability is independent of calculation status

Every evaluation retains a check list with the expected condition, observed value and state. Any violation dominates missing information; otherwise missing information produces unknown. Structural validity, applicability, numerical computability and scientific verification are separate concepts. A known nonpositive modulus is structurally valid data but violates this positive-phase implementation's scope. An unknown modulus is never assigned zero. Only `satisfied` claims can have numeric results.

The material-instance JSON schema allows missing/null input observations while rejecting unexpected property names. These input condition fields are distinct from records in the separate observations catalog. Runtime validation adds unique phase IDs, finite supported numeric values and fraction-sum constraints. Dimension accepts integral numbers such as 3 or 3.0, consistently with JSON Schema integer semantics; booleans are excluded. Provenance describes the input; it does not establish truth or licensing of future imported records. External source IDs remain user-supplied citations, not verified links.

## Numeric policy and limits

- The public Python API accepts finite int/float values, excluding booleans. JSON real numbers are read as binary floats; lexical overflow and nonzero lexical underflow are explicitly rejected. For example 1e-400 is rejected rather than becoming an absent phase. API callers must also avoid underflow before calling the function; a Python float already equal to 0 cannot reveal its earlier value
- Supported modulus units are Pa, kPa, MPa and GPa. Mixed input units are converted exactly to common Pa by decimal power-of-ten scaling; phase ordering is compared before 80-digit bound arithmetic can round a very long integer coefficient. K, G and E use the selected output unit; ν always uses dimensionless unit `1`. The CLI does not accept `--unit 1` as a modulus unit
- Each volume fraction must lie in [0,1]. A complete sum within absolute 1e-12 of 1 is accepted and normalized, with original sum, normalized fractions and whether normalization occurred in the result. Unknown fractions are not inferred from complements
- Only an exactly zero fraction removes a phase. A positive 1e-300 fraction remains active. Missing properties of an absent phase do not block a pure-phase calculation; active material and global conditions remain required
- Computation uses an 80-digit Decimal context and positive rational scalar-bound expressions. E/ν derivations use internal Decimal bounds, not an externally supplied pair of intervals. Supported float inputs keep intermediate exponents within the Decimal context's range
- Returned endpoints are ordinary rounded binary floats and human modulus text uses 12 significant digits; Poisson text uses a round-trip float representation so display rounding cannot replace an interior value with −1 or 0.5. They are numerical approximations, **not certified outward-rounded intervals**. The mathematical outer-envelope guarantee does not turn floating-point serialization into interval arithmetic. No experimental uncertainty propagation is implemented
- If a positive modulus output would overflow or underflow to zero in the requested unit, `computation` is `numerical_range_error`, `result` is null and the CLI exits 3. This does not change an otherwise satisfied applicability result
- For positive K/G, ν must lie strictly between −1 and 0.5. Negative ν and exact zero are valid. If conversion to float reaches either excluded boundary, the program reports `numerical_range_error` and a null result, without clipping to a fabricated physical endpoint

The evaluation JSON schema validates record shape, quantity domains, required dependency IDs/check presence, and that computed derived records have computed HS dependencies. Standard JSON Schema does not establish equality between a nested dependency instance ID and the root ID, recompute endpoints, or prove physical compatibility. `evaluate` creates all dependent records from one validated input internally; schema validation alone is not semantic or scientific validation of externally edited output.

Tests establish software behavior for stated cases and invariants. They neither prove the theorem nor replace independent scientific review. The [v0.2.0 migration guide](MIGRATION_v0.2.0.md) describes the expanded result list and typed output.

## Literature-model evidence extension

The optional strict `provenance.model_evidence` record is required when `kind` is `literature_model` and prohibited for other provenance kinds. It preserves raw E/ν, source/version locator, a fixed conversion rule, source-model versus calculator-assumption bases and unknown context. Known E/ν pairs must produce the declared K/G within relative tolerance 1e-12 in common units; every phase must be referenced exactly once. Missing temperature, grade, cure and measurement uncertainty remain null and are not used to invent physical applicability. This initial record contract supports calculator-selected fractions only. See [the bounded example](LITERATURE_EXAMPLE.md); it does not introduce a measured-material database or change the existing claim assumptions. Source constituent E/ν inputs and the new effective-composite E/ν output envelopes are different records with different meanings.

## v0.9.0 empirical fatigue catalog

Two catalog-only empirical models bring totals to 28 claims and 25 sources, retaining both observations. They estimate crack growth per complete cycle, with exponent-dependent coefficient units and a restricted 0<=R<1 scope. Forman requires a positive denominator and excludes its instability pole. Neither is a rigorous bound or safe-life guarantee. The original eight numerical evaluations are unchanged except engine version 0.9.0. No fatigue solver or plot is added. See [fatigue growth](FATIGUE_GROWTH.md) and [migration](MIGRATION_v0.9.0.md).
