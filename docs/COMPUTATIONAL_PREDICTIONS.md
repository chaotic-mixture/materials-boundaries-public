# Published computational predictions

The isolated `computational_predictions.json` catalog contains published
computational predictions, separate from theoretical claims, experimental
observations and synthetic temperature demonstrations. No DFT calculation is executed.
The first public release, v0.16.0, has six predictions in two closed scientific families and two
explicit comparison groups. A common GPa unit does not make their strength
criteria or loading protocols interchangeable.

## Ni ideal-shear family (introduced in v0.12.0)

The original three published discrete ideal-shear maxima come from
[Shimanek et al., arXiv:2108.06412v2](https://arxiv.org/abs/2108.06412v2).

| Model | Original Table 2 label | Reported strength |
|---|---|---|
| Ni (12-atom reference cell inferred from the shared host setup) | Ni, pure | 5.13 GPa |
| Ni11Al (one Al substitution) | Al | 4.58 GPa |
| Ni11Co (one Co substitution) | Co | 5.46 GPa |

The Al and Co table labels name solutes in Ni11X, not pure Al or pure Co.
`source_value_string` retains the original two decimal places independently of
the numeric value. Those digits are formatting precision, not uncertainty.

### Ni shared reported method and unresolved conditions

[Table 2, PDF page 27](https://arxiv.org/pdf/2108.06412v2#page=27) supplies values;
[sections 2.1–2.2, pages 5–7](https://arxiv.org/pdf/2108.06412v2#page=5) supply the
method. Section 3.1, page 9 identifies the current pure-Ni reference. The version
read was the official arXiv v2; the journal typeset version was not independently
inspected. The associated raw calculation inputs/outputs were not inspected.

The models use a periodic 12-atom, three-layer orthorhombic cell based on fcc Ni.
Ni11X replaces one in-plane Ni site. Pure-alias shear has slip plane (111) and
integer direction **[1,1,-2]**; their dot product is zero. The reported deformation
matrix is stored as printed without silently transposing conventions. A prescribed
positive shear angle is held while atomic positions and non-prescribed cell
parameters relax. Strength denotes the maximum along that reported constrained
path, not stability against every possible mode or a universal material bound.

The shared protocol retains static DFT, VASP/PAW, a 350 eV cutoff, Gamma-centered
9×8×7 mesh, 5e-6 eV electronic convergence and 0.2 eV Methfessel–Paxton smearing.
The paper identifies GGA through **Perdew et al. (1992), reference 43**. We do not
substitute PBE or claim to have checked actual input tags. Electronic smearing is
not a measurement or assignment of physical temperature.

Physical temperature, scalar thermodynamic pressure, magnetic state, spin
polarization, statistical uncertainty and systematic model error remain null,
with explicit reasons. A residual non-imposed stress threshold of 0.15 GPa is not
an exact 0 GPa pressure. The reported **0.08 GPa peak-convergence criterion is not
an error bar, standard deviation or confidence interval**. The source explicitly
notes layer-count dependence; three layers do not establish a bulk limit.

## Si tensile first-instability family (introduced in v0.13.0)

[Dubois, Rignanese, Pardoen and Charlier (2006), *Ideal strength of silicon: An
ab initio study*, Physical Review B 74, 235203](https://doi.org/10.1103/PhysRevB.74.235203)
supplies a separate closed family, `dubois_2006_si_uniaxial_deformation_v1`, with
quantity `tensile_first_instability_strength`. The explicit comparison group is
`dubois_2006_si_directional_instability`.

| Record ID | Loading-direction family | Stress at first detected instability | Engineering strain at that instability |
|---|---|---|---|
| `dubois2006_si_100_uniaxial_deformation` | ⟨100⟩ | 27.8 GPa | 31% (0.31) |
| `dubois2006_si_110_uniaxial_deformation` | ⟨110⟩ | 22.6 GPa | 25% (0.25) |
| `dubois2006_si_111_uniaxial_deformation` | ⟨111⟩ | 20.7 GPa | 19% (0.19) |

All six numbers come from the **Computed values** column of
[Table II, printed page 235203-3 / PDF page 3](https://perso.uclouvain.be/gian-marco.rignanese/publications/A029.pdf#page=3).
The selected rows are *uniaxial deformation*, also called *unrelaxed tension* in
the source, rather than its separately tabulated *uniaxial tension* cases.
`source_value_string` preserves the one-decimal stress values. The critical
engineering strain is a **separate typed record field**, `critical_engineering_strain`,
with quantity `critical_engineering_strain_at_first_instability`, a dimensionless
`value` of 0.31, 0.25 or 0.19 and `unit: "1"`. Its `source_value_string` is
`"31"`, `"25"` or `"19"`, `source_unit` is `"%"`,
`reported_decimal_places` is 0, uncertainty remains null and its own evidence
locates Table II. It is not a second stress value or an uncertainty.
Direction labels are crystallographically equivalent families, not verified
specific signed loading vectors.

### Strength definition and stability evidence

The quantitative definition is **computed stress at the first detected
instability** in the authors' phonon/stiffness analysis. Table III on the same
page identifies a direction-matched tensile elastic mode for each selected row:
⟨100⟩ tension, ⟨110⟩ tension and ⟨111⟩ tension. The reported instabilities occur
at the Brillouin-zone center. Section III.C discusses their interpretation.

[Figure 2(b), PDF page 2](https://perso.uclouvain.be/gian-marco.rignanese/publications/A029.pdf#page=2)
provides only qualitative visual consistency between the markers and path
peaks. No numbers are digitized from it and no maximum is independently
recomputed. Do not replace the first-instability definition with a generic
stress-path maximum. The authors' stability analysis is reported, not reproduced
by this software, and is not a universal bound or an experimental tensile test.

### Si reported method, inferences and unknowns

Section II, Eq. (1) and Figure 1(b), printed pages 235203-1–2, establish a
**two-atom primitive Si cell** and a uniaxial imposed strain with **zero transverse
strain components**. At each imposed strain the lattice vectors remain fixed
while the relative atomic positions relax. Transverse stresses are **not**
relaxed to zero. The fully relaxed loading residual-stress criterion of 0.02 GPa
does not apply to this fixed-lattice batch.

The two-atom primitive cell is directly reported. The normalized
**diamond-cubic** structure is an explicitly labeled inference from that cell
and the cubic directions; the inspected primary text does not explicitly name
it. No space-group number is inferred. The models are perfect periodic crystals,
not specimens with defects or measured commercial material.

The shared method preserves DFT/DFPT with ABINIT, LDA using the Teter–Padé
parametrization, separable norm-conserving Troullier–Martins pseudopotentials,
a 10 hartree plane-wave cutoff, a 12×12×12 Monkhorst–Pack mesh, a 6×6×6 phonon
q-point mesh and 0.01 hartree cold smearing. Suspect high-symmetry phonon modes
were explicitly recalculated by the authors. The exact strain schedule, force
relaxation tolerance and original DFT inputs were not verified. The stress is
retained as reported DFT stress; no verified Cauchy/nominal classification is
invented.

Physical temperature, scalar pressure, magnetic state, spin polarization,
statistical uncertainty and total/systematic model error remain **null**.
Static geometry optimization and electronic smearing do not establish a physical
0 K temperature. Experimental reference temperatures in Table I do not apply to
these predictions. Fixed transverse strain allows anisotropic stress and does
not establish zero scalar pressure.

The authors' **less than approximately 0.05 GPa** numerical stress-error estimate
covers smearing, finite basis and k-point sampling. Its qualifier and scope are
retained as numerical-control metadata; it is not a standard deviation,
confidence interval, total uncertainty or an error bar. Decimal places likewise
do not establish uncertainty.

### Si comparison boundary

Only the three selected direction families share this curated group. Direction
is the intended comparison axis; other common reported method details do not
make unresolved physical-state fields verified equal. Strength points share a
zero-origin GPa axis. Critical engineering strains remain separate labeled table
and CSV values, never a mixed stress/strain axis or an inferred stress–strain
curve. No interpolation, fitted envelope, uncertainty band or error bars are
added.

Do not pool these records with relaxed uniaxial tension, relaxed shear, Ni
pure-alias shear, experimental UTS, hardness or yield strength. No automatic
cross-family comparison, averaging or merging is supported. The prior Ni group
and its default plot selection remain unchanged; select the Si group explicitly.

## Search and export

```sh
python -m materials_boundaries catalog predictions --text --lang en
python -m materials_boundaries catalog predictions --query "理想剪切" --text --lang zh
python -m materials_boundaries catalog predictions --query "せん断" --text --lang ja
python -m materials_boundaries catalog predictions --query "Scherfestigkeit" --text --lang de
python -m materials_boundaries catalog predictions --source-id shimanek_2022_arxiv_2108_06412_v2 --quantity ideal_shear_strength --json
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_ni_al_co --output /tmp/ideal-shear --lang zh
python -m materials_boundaries catalog predictions --quantity tensile_first_instability_strength --text --lang en
python -m materials_boundaries prediction plot --group-id dubois_2006_si_directional_instability --output /tmp/si-first-instability --lang en
```

Search uses literal whitespace-separated, casefolded AND terms across IDs,
canonical/localized names, composition, quantity, classification and source,
protocol and group identifiers. Exact filters are case-sensitive. Unsupported
filters fail. Unknown exact IDs fail with exit 2; empty filtered results succeed.
Language affects text/help only; canonical JSON does not change.

A filtered catalog preserves the complete protocol/group metadata verbatim;
group member IDs refer to the **full installed catalog**, not necessarily the
filtered records. A search result does not create a new curated comparison.

The plot command exports canonical JSON, CSV, wide SVG, narrow SVG and a responsive
standalone HTML file. Its explicit group membership determines category order.
It never auto-joins studies, treats missing state fields as proven equal, or
automatically plots new records. Within each group, its three points share the
reported method in one source, with **published-method-only** comparability and unresolved conditions
visible. This is not an input-level audit or a reproducibility claim.

Points remain unconnected on a common zero-origin GPa scale. There is no
stress–strain curve, interpolation, uncertainty band or error bar. The CSV retains
classification, exact strings, provenance, unknown-state markers and convergence
semantics. For Si, strength and critical engineering strain have separate CSV
values and explicit units; strain is not plotted on the strength axis. JSON
contains complete immutable snapshots; renderers reconstruct the
canonical bundle from installed records and reject tampering/stale snapshots.
Regenerate exports after changing the software or any relevant metadata.

```python
from materials_boundaries.prediction_visualization import (
    build_prediction_comparison, comparison_json, comparison_csv,
    render_prediction_svg, render_prediction_html,
)
bundle = build_prediction_comparison('shimanek_v2_table2_ni_al_co')
svg = render_prediction_svg(bundle, lang='de', width=380)
```

## Contribution and validation boundary

The prediction catalog envelope/schema is 1.1.0; individual records and
protocols retain 1.0.0. The Ni comparison bundle stays at 1.0.0 and the Si
comparison bundle uses 1.1.0. The schema uses closed alternatives for records,
protocols and comparison groups rather than a permissive generic extension:

- `shimanek_v2_pure_alias_12atom_v1`: the preserved Ni12/Ni11X ideal-shear
  contract, including its shared reported method and path-maximum semantics
- `dubois_2006_si_uniaxial_deformation_v1`: the two-atom Si, fixed-transverse-strain,
  internal-relaxation contract with tensile first-instability semantics and a
  separate typed critical engineering strain

Runtime and development guards check each complete physical/calculation
contract, composition, source decimal text, reference integrity, explicit group
membership and non-equivalence of unknowns. Fresh record, protocol and group IDs
under a complete supported contract are appendable without changing existing
tests. Families cannot be mixed merely because both use GPa. A different
geometry, relaxation constraint, stability definition, cell size, known state or
error model requires reviewed schema/guard work, not a weakened family or
catch-all branch. Structural support is not source verification.

Never copy verification or rights assertions merely because a record validates.
Real source records are independently pinned by source-transcription
fixtures; synthetic appendability fixtures remain tests only. All previous
scientific prediction records and composite outputs are preserved apart from
current software-version labels. Public temperature demos use new synthetic
data; see [the separate contract](TEMPERATURE_MODELS.md).

No source PDF, full text, rendered pages or source figures are bundled. The
verified arXiv license is non-exclusive distribution permission, not a verified
CC license or blanket republication permission. For Dubois et al., the inspected
author-hosted published-layout PDF carries ©2006 The American Physical Society;
no open reuse license or full-text redistribution permission was verified. Only
factual values, bibliographic metadata and original curatorial paraphrases are
included. Source PDFs, rendered page images and extracted full text remain
private audit materials and are not redistribution assets. Software tests and
source checks are not independent scientific review; four-language translations remain
machine-assisted and not independently scientifically/native-speaker reviewed.

## Static preview and QA

An original [Chinese SVG preview](../examples/predictions/preview.zh.svg) is
included as a historical v0.12.0 rendering, not a new scientific source. Rebuild
exports for the current installed version. For that v0.12.0 preview, wide and
narrow SVGs in all four languages were rendered with Inkscape and visually
inspected. Browser-rendered HTML/mobile interaction QA for that historical batch
was unverified: its cloud environment prevented Chromium startup because local IPC sockets were not permitted. Static rendering
and structural/responsive HTML tests do not substitute for a browser check.


The original [Si directional preview](../examples/predictions/silicon-first-instability.zh.svg)
is a v0.13.0 rendering of the separately curated first-instability group. Its
wide and narrow SVG exports in all four languages were rendered with Inkscape
and visually inspected. Strength uses one zero-origin GPa axis; critical
engineering strains and their provenance are listed separately. This release
does not claim browser-rendered HTML/mobile QA or independent scientific review.
