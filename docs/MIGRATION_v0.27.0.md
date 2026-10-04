# Migration to v0.27.0

This catalog-only release appends exactly three claims and two sources.
Production totals become **41 claims and 57 sources**. Observations remain
**16 from five studies**; published computational predictions remain **12 in
two scientific families and three explicit groups**; five original synthetic
temperature demos retain seven branches. Exactly eight composite calculation
rules remain executable. No new material values, NIST coefficients, JARVIS
mirror, observation, prediction, fitted curve or source asset is admitted.

## New records and closed scientific contracts

- `von_mises_initial_yield_relation`: `model_relation`, `direction: relation`,
  `bound_kind: null`, pressure-valued `von_mises_equivalent_stress`, SI unit Pa
- `tresca_initial_yield_relation`: `model_relation`, `direction: relation`,
  `bound_kind: null`, pressure-valued `tresca_equivalent_stress`, SI unit Pa
- `tresca_von_mises_equivalent_stress_ratio_bound`: `theoretical_bound`,
  `direction: interval`, `bound_kind: criterion_function_comparison`,
  dimensionless `tresca_von_mises_equivalent_stress_ratio`, SI unit 1

All three remain `evaluation_support: catalog_only`; their scientific rule IDs
are descriptors, not callable runtime rules. The ratio's dependencies identify
the admitted von Mises and Tresca function-definition families. They do not
create numerical dependency evaluations or applicability states.

Claims schema advances **1.12.0 → 1.13.0**. The new
`yield_criterion_contract` is closed and restricted to its three quantity
families. Exact definitions, tensor/shear/sign/unit conventions, mathematical
versus physical premises, nonhydrostatic ratio domain, inclusive sharp
endpoints, original proof role, calibration and exclusions remain mandatory.
Do not weaken a family guard to admit a new yield model or arbitrary equation.
The parameter vocabulary adds `pressure_squared` / `Pa^2` for J2, restricted by
the yield-family contract; existing families are not broadened. Stress
quantities remain pressure/Pa, and normalized ratios remain dimensionless/1.

The comparison schema's embedded claims snapshot and exact local reference
advance with the standalone claims schema; its own version remains unchanged.
Previously saved comparison outputs carrying the older claims-catalog envelope
must be regenerated for validation against the new embedded claims schema.
Numerical outputs and visualization contracts otherwise stay unchanged. Source
schema remains **1.0.0**. Observation, computational-prediction, temperature,
input and evaluation scientific schemas do not change.

## Scientific distinctions that consumers must preserve

1. `q_VM = sqrt(3*J2)`, `q_T = sigma_max-sigma_min = 2*tau_max`; dimensional
   `f=q-Y` defines a model boundary with Y > 0. Source A's `sigma_eq=q/Y` and
   `Lambda=f/Y` are dimensionless, not directly interchangeable with Pa-valued q/f
2. For the same nonhydrostatic finite real symmetric 3D Cauchy stress tensor,
   `1 <= q_T/q_VM <= 2/sqrt(3)`. The division-free inequality applies also to
   hydrostatic stress, where both functions vanish and the ratio is undefined
3. Hydrostatic `p=tr(sigma)/3` is signed tension-positive normal stress, opposite
   to compression-positive pressure. A shift `h*I` uses the signed increment h
4. The exact comparison and endpoint proof are original project algebra using
   source-supported definitions. This is not a theorem bracketing actual
   material yield, independent expert peer review or empirical validation
5. Physical initial-yield interpretation is separately restricted to declared
   isotropic, pressure-insensitive, tension/compression-symmetric small-strain,
   quasistatic, rate-independent models at fixed state/temperature with a
   matching uniaxial tensile Y calibration and declared yield convention
6. A proof stress retains its offset; same-shear calibration is not same-Y
   calibration. No hardening, flow rule, associated flow, backstress evolution,
   loading/unloading integration, post-yield strain, damage or safety claim follows
7. The optional threshold consequence is confined to one fixed local
   proportional ray `sigma(lambda)=lambda*Sigma`, lambda >= 0, nonhydrostatic
   Sigma and common fixed Y > 0. Its approximately 15.47% maximum difference is
   relative to the Tresca threshold, not a universal error or safety margin

See [the complete scientific guide](YIELD_CRITERIA.md) for the exact proof,
endpoint examples, hydrostatic non-limit, physical exclusions, pure-shear
substitutions, source locators, inspected-byte hashes and four-language usage.

## Source and rights additions

Exactly two new source IDs are added:

- `giraldo_londono_paulino_2020_yield_criteria`: the inspected author-hosted
  publisher-layout 2020 paper, with selected equations visually checked, exact
  byte hash and no verified permissive reuse license
- `wierzbicki_2013_structural_plasticity`: the official MIT OCW Fall 2013 Lecture
  12, selected equations visually checked, exact byte hash and the recorded
  CC BY-NC-SA 4.0 terms, without relicensing source assets under MIT

In the inspected MIT notes, Eq. (12.22) omits a square root and Eq. (12.46)
repeats a principal pair. These are observed printing defects, not a verified
official errata publication. Neither is used. The rounded p. 12-15 comparison
is not used as proof. No source PDF, extracted prose, screenshot, figure,
experimental plot data or other source asset enters repository, package or
release artifacts. See [source ledger](SOURCES.md) and
[third-party notices](../THIRD_PARTY_NOTICES.md).

## Preservation and verification checklist

The software label advances to **0.27.0**. Preserve all 38 previous claim
objects and all 55 previous source objects, all other scientific catalogs,
previous locale values, historical migration guides, fixtures and generated
examples. Add en/zh/ja/de names and the narrowly needed output labels without
changing canonical IDs, formulas or units. Current README counts and narrative
advance; historical release counts remain historical.

Run release metadata preflight, strict offline catalog validation, the full
test suite, closed-contract/adversarial yield tests, exact/synthetic algebra
checks, four-language CLI smoke and installed-wheel checks. Rehearse fresh-ID
append-only reuse in a disposable copy and preserve unrelated scientific
families and executable pairs. These are release gates, not a claim here that
every gate has already run. Arithmetic, schema and translation checks do not
constitute scientific or native-language review or a material-strength
certification. This release introduces no numerical plasticity solver.
