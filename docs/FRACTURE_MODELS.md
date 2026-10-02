# Modern Griffith/LEFM central-crack model records

Version 0.3.0 added two **catalog-only model estimates**. They are source-backed definitions, not new executable rules. The existing composite `evaluate` command still computes its eight elastic-bound/envelope results. No fracture input schema, model applicability check, numerical fracture result, design allowable, or safety assessment is provided.

```sh
python -m materials_boundaries catalog claims --claim-type model_estimate --text --lang en
python -m materials_boundaries catalog claims --direction prediction --source-id wilson_1992_nasa_tm_103591
python -m materials_boundaries catalog sources --id wilson_1992_nasa_tm_103591 --text
```

The later v0.4.0 catalog adds separate K_I, G_I and finite-width relation records, plus two ideal-strength estimates; see [the new content overview](MECHANICS_CATALOG.md). The two Griffith definitions below are unchanged. To select only them, combine `--claim-type model_estimate --source-id wilson_1992_nasa_tm_103591`.

## Classification and geometry

The records `griffith_central_crack_plane_stress` and `griffith_central_crack_plane_strain` describe the critical **remote tensile stress** for onset of Mode-I crack extension in a homogeneous, isotropic, linear-elastic body under an infinite-plate idealization. A central through crack has total length **2a**. The far-field tension acts normally to the crack; the faces are traction-free. Quasi-static loading, small strain, and a negligible crack-tip process zone relative to the crack and body scales are assumed.

Their canonical `claim_type` is `model_estimate`, `direction` is `prediction`, `bound_kind` is `null`, and `evaluation_support` is `catalog_only`. The scalar quantity has dimension pressure/stress, SI unit Pa. It is a conditional model threshold, **not a universal upper bound on tensile strength**, ideal defect-free strength, or an engineering acceptance criterion. Neither record depends on a composite-bound result.

Finite-width plates, edge cracks, arbitrary geometry, significant plasticity, mixed-mode loading, crack interactions, residual stresses, and dynamic fracture are not modeled by these entries. An infinite plate is an idealization: the cited figure indicates 2a much smaller than the width W. A central crack's half-length must not be replaced by its full length or an edge-crack length. The small-crack divergence does not justify extrapolation to atomistic or zero crack size.

## Equations and dimensions

The modern relations are:

- K_I = sigma sqrt(pi a)
- G_I = K_I² / E_prime
- At initiation, G_I = Gc, hence sigma_c = sqrt(E_prime Gc / (pi a))
- Plane stress: E_prime = E
- Plane strain: E_prime = E / (1 − nu²)

`E` is the positive Young modulus of the homogeneous cracked body in Pa. `a` is its positive crack half-length in m. `Gc` is its supplied positive critical energy release rate, per projected crack area, in J/m². Plane strain additionally uses a supplied isotropic Poisson ratio `nu` with −1 < nu < 0.5 and dimensionless unit `1`.

Dimensional check: E has units Pa, Gc has units J/m² = Pa·m, and a has units m; E_prime Gc/a therefore has units Pa². The square root is a stress. The energy-release symbol G_I is **not** the shear modulus G in the composite evaluator. K_I is **not** the bulk modulus K. The energy criterion is evaluated at initiation with a specified Gc, not a crack-growth/R-curve or lifetime model.

For an ideal brittle surface-creation-only process, Gc = 2 gamma, where gamma is energy per area of one newly created surface. This is a **conditional specialization**, never a silent default. A separately supplied critical fracture energy can incorporate dissipation that is absent from the ideal surface-creation balance, subject to LEFM's applicability. Neither source presence nor an elastic modulus supplies that energy, crack size, or a measured fracture property.

## What was checked

[Christopher D. Wilson, *Linear Elastic Fracture Mechanics Primer*, NASA-TM-103591 (July 1992)](https://ntrs.nasa.gov/citations/19920021173) is the modern equation source. Printed pages 2–4 (PDF pages 10–12) were inspected in extracted text and in rendered page images:

- Figure 1: central through crack 2a with 2a much smaller than W
- Equation (3): critical plane-stress stress expression
- Equations (4)–(6): Mode-I K_I and G_I relations
- Printed page 4: plane-stress and plane-strain E_prime conventions

The plane-strain critical-stress expression is an algebraic specialization of the latter relations. We do not reproduce the report's equation (2) energy-derivative notation, whose two-tip normalization needs care. The direct critical-stress and energy/stress-intensity relations above are the cited model definitions.

[A. A. Griffith, *The Phenomena of Rupture and Flow in Solids*, Philosophical Transactions A 221, 163–198 (1921)](https://doi.org/10.1098/rsta.1921.0006) is credited for the historical origin. Its scanned header and final-page correction Note (printed p. 198) were inspected. That Note corrects an earlier strain-energy calculation. **The modern coefficients and plane-strain factor are not presented as a transcription of the 1921 equations**, whose derivation has not been independently checked here.

These are equation/source checks and software metadata tests, not independent scientific peer review or material-specific validation. NASA's official metadata records “Work of the US Gov. Public Use Permitted.” No general license identifier is inferred. The Griffith source has no verified explicit reuse license in this catalog. No paper/report PDF or article full text is bundled; original project work is MIT-licensed; third-party rights remain separate (see [notices](../THIRD_PARTY_NOTICES.md)).

## Unknown conditions and numerical illustration

The catalog stores **required** premises, not observations proving those premises. Querying a record does not establish `satisfied`, `unknown`, or `violated` for any specimen. This increment does not execute either model at all, so it cannot manufacture a numeric result from incomplete conditions. Unknown or violated premises do not justify applying the displayed formula. Downstream software must preserve this boundary; it must not infer a missing Gc, nu, geometry, or crack size.

For an independent arithmetic illustration only, take synthetic E = 70 GPa, Gc = 2 J/m², a = 1 mm (full crack length 2 mm), and nu = 0.22. The formulas give approximately:

- Plane stress: 6.675581178 MPa
- Plane strain: 6.843241471 MPa

These inputs are invented, not glass measurements, literature-model material data, or predictions for a specimen. Gc is specified directly; choosing gamma = 1 J/m² would recover it only after separately imposing the ideal surface-creation-only premise. These numbers are a documented arithmetic example, not output from a supported fracture calculator.

See [catalog and API](CATALOG.md), [v0.3.0 migration](MIGRATION_v0.3.0.md), and the [source ledger](SOURCES.md).
