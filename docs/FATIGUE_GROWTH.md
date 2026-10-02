# Empirical fatigue crack-growth catalog

v0.9.0 adds two **catalog-only model estimates**. Neither is a rigorous upper or
lower bound, a threshold law, a safe-life guarantee, a calibrated material dataset
or executable fatigue solver. Walker is deferred. The existing eight elastic
composite evaluations and their plots are unchanged.

## Exact definitions and restricted scope

- `a` is the geometry-declared crack-tip advance coordinate. For a symmetric
  central through crack of total length `2a`, it is half-length; `da` is advance
  per tip. Another geometry needs its own consistent coordinate and K solution
- `N` counts complete load cycles, not reversals or elapsed seconds
- `DeltaK = Kmax-Kmin = (1-R)*Kmax`, `R = Kmin/Kmax`
- This initial contract requires `Kmax>0`, `DeltaK>0` and **0<=R<1**. Negative-R
  signed versus tensile-only ranges and closure effects need separate evidence;
  never silently clip `Kmin`
- Use modern Mode-I `K`: the leading singular opening-stress term ahead of the tip is
  `sigma_yy=K_I/sqrt(2*pi*r)` in the LEFM asymptotic field. A geometry-specific
  expression such as `K=Y*sigma*sqrt(pi*a)` must use a consistent `Y` and `a`;
  this catalog supplies no universal geometry factor
- Scope is long-crack, predominantly linear-elastic, small-scale-yielding,
  constant-amplitude Mode-I loading within a measured calibration interval

These are declared conditions, not software-checked specimen applicability.
Residual stress, closure or shielding must be represented in the chosen
calibration; they cannot be ignored when transferring the law.

## Paris–Erdogan: intermediate region

ID: `paris_erdogan_intermediate_growth`

`da/dN = C_P*(DeltaK)^m`

Use a positive fitted `C_P` and positive dimensionless `m` together for a fixed
calibrated R in the intermediate (Region II) growth interval. Wilson's Eq. (45)
calls the exponent `n`; the catalog deliberately renames it `m`. No exponent,
including 4, is universal. No explicit R term does **not** mean R-independent
behavior. Exclude the threshold and near-instability regimes.

## Forman: calibrated central/high-growth acceleration

ID: `forman_terminal_acceleration_growth`

`da/dN = C_F*(DeltaK)^n / ((1-R)*Kc-DeltaK)`

`(1-R)*Kc-DeltaK = (1-R)*(Kc-Kmax) > 0`

The fitted positive `C_F` and positive dimensionless `n` apply only to the
specified material, conditions and R interval. The exponent need not equal the
Paris exponent. `Kc` is independently established condition-, thickness- and
constraint-relevant toughness; it is **not automatically plane-strain KIc**.

Within 0<=R<1, the positive denominator is equivalent to Kmax<Kc. As Kmax tends
to Kc from below, the model diverges. This pole represents a model upturn toward
an excluded instability limit, **not a finite-rate prediction, upper bound or
safe-life guarantee**. Do not evaluate at/beyond the pole or integrate through
fracture. Positive denominator alone does not prove applicability or justify
extrapolation beyond calibration. This relation contains no threshold.

## Units are part of the fit

The schema records `quantity_dimension: length_per_cycle` and `si_unit:
m/cycle`. Here cycle is a **dimensionless counting annotation**, not a new SI
base dimension; the physical dimension is length per dimensionless count.
`N` consequently has dimensionless SI unit `1`. Keeping the operational
`m/cycle` label prevents accidental interpretation as m/s.

The coefficient parameters have a closed `coefficient_units` object and an
explicit SI-based symbolic unit string:

| Coefficient | Unit using m/cycle and Pa√m | Intensity exponent |
| --- | --- | --- |
| `C_P` | `m/cycle*(Pa*m^0.5)^(-m)` | `-m` |
| `C_F` | `m/cycle*(Pa*m^0.5)^(1-n)` | `1-n` |

These expressions are metadata, never evaluated code. The coefficient unit is
not fixed until its exponent is specified. In an MPa√m convention the Pa factor
must be replaced **and the coefficient number converted**. If one new intensity
unit is `s` old intensity units and growth-rate length units are unchanged,
`C_P,new=C_P,old*s^m` and `C_F,new=C_F,old*s^(n-1)`. These are unit-conversion
identities, not imported constants or a coefficient-conversion API. Changing
rate length units adds the corresponding numerical rate conversion. All K,
DeltaK and Kc entries must use the same intensity unit.

Do not transfer a number between alloys, heat treatments, environments,
thicknesses, orientations, equations, exponents or K normalizations. In Hudson's
historical lowercase convention, `K=sqrt(pi)*k` for matching geometry factors;
thus for the **same physical fit expressed in modern K**,
`C_P,modern=C_P,historical*pi^(-m/2)` and
`C_F,modern=C_F,historical*pi^((1-n)/2)`. This changes normalization, not merely
unit labels. No Hudson constants are imported and no geometry is silently
converted.

## Calibration evidence required for an application

Record the material/alloy, temper/heat treatment, orientation, thickness and
constraint, crack measurement convention, geometry/K solution, R range,
temperature, environment, frequency, waveform and loading history. Report the
fitted DeltaK interval, data quality, fit method, coefficient/exponent pair and
uncertainty, with independent relevant Kc for Forman. The catalog provides none
of those material-specific numbers and asserts no universal fit quality.

Excluded: crack initiation, small/short cracks, threshold extrapolation, gross
yielding, mixed mode, non-LEFM loading, variable-amplitude overload/retardation,
actual instability and uncalibrated residual stress, closure, shielding or
environmental effects. No life integration, failure date or fatigue plot exists.

## What was inspected, and what was not

- [Wilson, NASA-TM-103591 (1992)](https://ntrs.nasa.gov/citations/19920021173):
  modern Paris Eq. (45), printed p. 37/PDF p. 45; Forman Eq. (48), printed
  p. 40/PDF p. 48; DeltaK/R definitions Eqs. (43)–(44), printed p. 35/PDF p. 43.
  Relevant equations were visually inspected. The existing source ID and all
  source-level read/license/provenance fields remain unchanged; this newly
  checked scope is recorded in each new claim's evidence
- [Paris and Erdogan (1963)](https://doi.org/10.1115/1.3656900) and
  [Forman, Kearney and Engle (1967)](https://doi.org/10.1115/1.3609637): original
  historical attribution only. Publisher full texts were inaccessible; no exact
  original equation, page or derivation is claimed to have been inspected
- [Hudson, NASA-TN-D-5390 (1969)](https://ntrs.nasa.gov/citations/19690025326):
  Forman Eq. (6), printed p. 8/PDF p. 12; historical k definitions Eqs. (3)–(5),
  printed pp. 5–6. His Paris fourth-power variant is not a universal exponent.
  Thin 7075-T6 and 2024-T3 aluminum-sheet comparisons are qualitative support;
  frequencies differed and the 2024-T3 R=-1 data were excluded from fitting.
  No measured points, curves or fitted constants are imported
- [AFGROW handbook §5.1.2](https://www.afgrow.net/applications/dtdhandbook/sections/page5_1_2.aspx):
  modern equation cross-check, Paris Eq. (5.1.2) p. 5.1.8 and Forman Eq. (5.1.4)
  p. 5.1.9. Its inconsistent secondary Forman year is not adopted
- [ASTM E647-24 public page](https://store.astm.org/e0647-24.html): public Scope
  and Significance and Use, clauses 1.3, 5.1.1, 5.1.3–5.1.8, 5.2.1 and Note 4.
  Applicability cautions only, not equation or fit-validation authority. The full
  standard was not purchased/read; no compliance certification is claimed

NASA landing pages state US Government work/public use permitted. No blanket
ASME, ASTM or AFGROW reuse license is established. Only bibliographic metadata,
formula facts and original curation notes are included: no PDFs, figures or
raw datasets. Scientific peer review and independent native-language review
remain outstanding; internal software/source checks do not upgrade those claims.

## Four-language lookup

```sh
python -m materials_boundaries catalog claims --query "fatigue" --text --lang en
python -m materials_boundaries catalog claims --query "疲劳" --text --lang zh
python -m materials_boundaries catalog claims --query "疲労" --text --lang ja
python -m materials_boundaries catalog claims --query "Ermüdungsriss" --text --lang de
```

Language changes presentation labels only. Formula strings, units, IDs and
canonical JSON remain shared. See [migration](MIGRATION_v0.9.0.md) and the four
getting-started guides for localized cautions.
