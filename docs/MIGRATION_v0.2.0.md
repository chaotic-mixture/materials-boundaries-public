# Migrating from v0.1.2 to v0.2.0

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


Version 0.2.0 adds HS/Reuss/Voigt shear-modulus bounds and two conservative derived outer envelopes for effective Young's modulus and Poisson's ratio. It retains the positive, 3D, isotropic, small-strain, static, linear-elastic and perfectly bonded implementation scope. Strength, failure and plasticity remain excluded. No paper full text, PDF, new measurements or new license permission is introduced.

## Versioned contracts

| Contract | v0.1.2 | v0.2.0 |
| --- | --- | --- |
| Package version | 0.1.2 | 0.2.0 |
| Evaluation output schema | 1.0.0 | 1.1.0 |
| Claims catalog/schema | 1.0.0 | 1.1.0 |
| Input instance schema | Unchanged | Unchanged |
| Sources catalog/schema | 1.0.0 | 1.0.0 |
| Locale dictionary schema | 1.0.0 | 1.0.0, more keys |

Existing example/input JSON remains valid without migration. No new input parameters or claims about real material applicability are inferred. CLI flags, input modulus units, language codes and error-state semantics remain canonical.

## Eight evaluations, stable initial order

The ordered output is now:

1. `hs_bulk_3d_two_phase`
2. `reuss_bulk`
3. `voigt_bulk`
4. `hs_shear_3d_two_phase`
5. `reuss_shear`
6. `voigt_shear`
7. `youngs_modulus_outer`
8. `poissons_ratio_outer`

The first three bulk claim IDs, executable rule IDs and numeric `result` shapes/endpoints are preserved for the supported existing fixtures. One applicability bug is corrected: phase ordering for integers with more than 80 significant digits is now compared after exact unit scaling, before bound arithmetic can round distinct values into equality. A crossed-order input previously misclassified in that extreme case is now suppressed. Consumers must nevertheless accept schema version 1.1.0, new metadata, and five additional records. Do not unpack exactly three records or assume every result is a bulk modulus. Select by canonical `claim_id` and verify `quantity` and `bound_kind`.

Every evaluation now has `quantity` and `bound_kind`. K, G, E and ν use `effective_bulk_modulus`, `effective_shear_modulus`, `effective_youngs_modulus` and `effective_poissons_ratio`, respectively. The six scalar K/G claims use `scalar_modulus_bound`; E/ν use `derived_outer_envelope`. Numerical results retain the `lower` and/or `upper` endpoint fields and `unit`. Only derived evaluations add this dependency object:

```json
{
  "instance_id": "the-input-instance-id",
  "claim_ids": ["hs_bulk_3d_two_phase", "hs_shear_3d_two_phase"],
  "compatibility": "same_instance_phase_pair_fractions_units_and_conditions",
  "joint_attainability": "not_asserted"
}
```

The object's `instance_id` is the actual input ID. Compatibility states that the dependency rules are evaluated from the same input system; it does not independently verify the physical specimen. The schema checks dependency IDs, required check presence and availability of computed HS dependencies, but does not compare nested/root instance IDs or recompute formulas. The engine constructs same-instance dependencies internally; arbitrary external JSON needs separate semantic validation. In the reusable claims catalog, `dependencies` is instead a list of those two claim IDs for derived records and an empty list for scalar records. All catalog claims also include `bound_kind`. Do not confuse catalog dependencies with per-instance evaluation evidence.

## Derived does not mean jointly attainable

For K ∈ [Klow,Khigh], G ∈ [Glow,Ghigh] from compatible same-system HS evaluations:

- E = 9KG/(3K+G): evaluate lower at (Klow,Glow), upper at (Khigh,Ghigh)
- ν = (3K−2G)/(2(3K+G)): evaluate lower at (Klow,Ghigh), upper at (Khigh,Glow)

These monotonicity-based intervals conservatively contain the permitted values but need not be tight. A corner of the separate K/G rectangle need not correspond to any common realizable microstructure. Keep the `derived_outer_envelope` label and the joint-attainability warning in downstream presentations. Do not relabel these as optimal joint bounds, experimental confidence intervals or specimen predictions.

HS and derived claims require well-ordering. Reuss/Voigt do not, but are not substituted into a derived claim when HS is unavailable. Unknown or violated prerequisites produce null numerical results. If a required HS evaluation encounters `numerical_range_error` in the chosen output unit, dependent E/ν results also report a numerical range error. Applicability can remain `satisfied` when computation fails.

## Units and numerical limits

`--unit Pa|kPa|MPa|GPa` affects only modulus outputs K/G/E. ν is always dimensionless with `unit: "1"`, even when a different modulus unit was selected. Do not apply a pressure-unit conversion to ν; `--unit 1` is not a supported CLI choice.

Positive K/G require −1 < ν < 0.5; negative ν and zero remain valid. If ordinary float rounding lands on −1 or 0.5, the program returns `numerical_range_error` and null rather than clipping or reporting an invalid boundary. Human-readable ν uses a round-trip float representation to avoid displaying a valid interior float as −1 or 0.5; modulus text retains 12 significant digits. Returned Decimal80-derived floats are approximations, not certified outward-rounded intervals. An outer-envelope formula alone does not provide numerical interval certification.

CLI exit codes retain their meanings: 0 for completed evaluation, including unknown/violated claims; 2 for invalid input/usage; 3 for a numerical range error. Check per-claim applicability and computation state as well as the process status.

## Downstream checklist

- Update stored output schemas and allow the eight claim IDs, typed quantities and both bound kinds
- Keep existing bulk lookups by ID; avoid positional length assumptions
- Distinguish dimensional K/G/E from dimensionless ν, including valid zero/negative ν
- Preserve null/unknown/violated and numerical-error states instead of filling them with values
- Display dependency provenance and the non-tight/joint-attainability limitation for derived envelopes
- Add shear, E/ν and localized-label snapshots; compare language-independent JSON across `en`, `zh`, `ja`, `de`
- Retain original evidence/read-status and license caveats; software tests and algebraic derivation are not independent scientific review

See [Model](MODEL.md) for equations and a rational synthetic fixture, [Catalog](CATALOG.md) for searches and schema-specific envelopes, and [Sources](SOURCES.md) for evidence boundaries.
