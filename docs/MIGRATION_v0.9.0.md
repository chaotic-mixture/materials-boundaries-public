# v0.9.0 migration: two empirical fatigue-growth contracts

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


## Preserved data and execution

- Package/engine advances from 0.8.1 to **0.9.0**; claims schema advances from
  1.6.0 to **1.7.0**, urn:materials-boundaries:schema:claims:1.7.0
- **28 claims, 25 sources, two observations from one study**. The original 26
  claim records, all 20 source records and both observations are unchanged
- Add Paris–Erdogan and Forman empirical growth records; Walker remains deferred
- Reuse Wilson's existing source identity with new claim-level fatigue locators;
  no global source-status, license or provenance upgrade. Five source records
  distinguish original attribution, historical experimental context, modern
  handbook cross-check and public applicability guidance
- Existing eight executable claim/rule pairs, numerical values, applicability,
  ordering and evidence remain unchanged. Only engine_version changes in
  evaluation output. No fatigue solver, fit, integration or plot is introduced
- Instance/source/observation/locale/comparison schemas remain 1.0.0; evaluation
  remains 1.1.0. Comparison exports embed claims schema 1.7.0 but contain only
  the original eight evaluated elastic claims and their sources

## New closed scientific families

`paris_erdogan_intermediate_growth_v1` and
`forman_terminal_acceleration_growth_v1` each have an explicit schema branch and
complete development-validator family-assumption/structural-identity guards.
They use `model_estimate`, `prediction`, null `bound_kind`, empty dependencies
and `catalog_only`. Same-family records can use fresh IDs after evidence review;
new equations, R conventions, geometry assumptions or calibration contracts must
not be smuggled through permissive fields.

Output `fatigue_crack_growth_rate` uses the operational dimension
`length_per_cycle` and SI-based annotated unit `m/cycle`. Cycle is a dimensionless
complete-cycle count; N has dimensionless unit 1. This is not a time-rate input
or a new SI base dimension.

Coefficient parameters add a closed `coefficient_units` object containing the
rate unit, intensity unit, exponent symbol, symbolic intensity power and cycle
count convention. The coefficient dimension is
`length_per_cycle_times_stress_intensity_power`. Its `si_unit` is an explicit
symbolic expression: `m/cycle*(Pa*m^0.5)^(-m)` for C_P, or
`m/cycle*(Pa*m^0.5)^(1-n)` for C_F. The schema ties each coefficient to its exact
exponent, unit expression and equation; the object is forbidden on other
parameter dimensions. Readers must preserve these metadata, not simplify a
coefficient to a dimensionless scalar or ordinary pressure. Text rendering shows
the symbolic unit and its explanatory meaning; canonical JSON retains the full
structured object. No formula/unit string is executed.

Both contracts require consistent modern Mode-I K, declared crack-tip coordinate,
complete-cycle N, DeltaK=Kmax-Kmin=(1-R)Kmax, Kmax>0, DeltaK>0 and 0<=R<1.
Paris requires its fixed calibrated R and intermediate interval. Forman requires
matched Kc and positive denominator, with the instability pole excluded. Neither
predicts a threshold, finite instability rate, rigorous bound or safe life.
See [the fatigue guide](FATIGUE_GROWTH.md) for calibration and normalization details.

## Validation, growth and provenance

The new contract is a deliberate schema extension, not a weakening of v0.8.1's
appendability protections. Existing scientific branches and exact executable
allowlist stay closed. New tests independently mutate coefficient dimensions,
units/exponents, complete-cycle definitions, K normalization, R range,
classification, calibration, denominator and execution support; each must fail.
They also append a synthetic same-family record with a new ID and labels.
For this new schema release, four historical tests’ current claims-envelope
version assertions advance from 1.6.0 to 1.7.0; no scientific assertion or
appendability guard is weakened. The existing disposable LEFM whole-suite append
rehearsal uses these release tests unchanged. The historical provenance fixture is extended only for
the two new claims and five new sources; its old declarations remain unchanged.

Read by stable ID and evaluation_support, not fixed catalog length. Regenerate
comparison bundles from retained valid composite inputs with engine 0.9.0;
editing version labels in old bundles is not a supported migration. Historical
preview files remain historical. Runtime remains dependency-free; full release
QA uses the required development extra, validator, complete tests and an
isolated wheel install/visualization smoke test.

Four-language names and localized getting-started cautions are authored and
machine-assisted, not independently scientifically or natively reviewed. Source
inspection, structure validation, algebra tests and internal release review do
not certify empirical fits or confer reuse rights. Original project code, documentation and curation use MIT in the first public
release; third-party rights remain separate. No PDFs are included.
