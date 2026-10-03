# Migration to v0.21.0

Version **0.21.0** appends exactly six source-checked Ni11X periodic-model
ideal-shear predictions under the existing scientific contract. No DFT run,
new source, scientific schema, runtime API or evaluator is introduced. This
note does not assert a published tag, release date or software DOI.

## Version, counts and preserved contracts

- Software/package/engine version: **0.20.1 → 0.21.0**
- Computational predictions: **6 → 12**, across **2 scientific families**;
  explicit comparison groups: **2 → 3**
- Unchanged totals: **36 mechanics claims, 51 source records, 6 observations
  from 3 studies, 5 synthetic temperature demos with 7 branches**, and exactly
  **8 executable composite rules**
- Prediction catalog schema stays **1.1.0**; both Ni comparison bundles use
  **1.0.0**; the Si comparison bundle uses **1.1.0**; records/protocols retain
  **1.0.0**. Other scientific schemas are unchanged
- Original source, protocol, record and group objects are preserved. The default
  `shimanek_v2_table2_ni_al_co` remains the original three points; the separate
  `dubois_2006_si_directional_instability` group remains three points

Historical counts in earlier release notes remain historical. Existing checked-in
Ni/Si previews remain historical renderings and are not rewritten for this release.
Current exports carry the current engine version; regenerate saved bundles from
the intended explicit selection rather than relabeling older snapshots.

## Added records and explicit selection

All six use source `shimanek_2022_arxiv_2108_06412_v2`, protocol
`shimanek_v2_pure_alias_111_11m2_12atom`, quantity `ideal_shear_strength`, and
new group **`shimanek_v2_table2_cr_mn_fe_cu_si_ti`** in this order:

| Record ID | Model | Exact source label | Exact source strength |
|---|---|---|---|
| `shimanek2022_v2_ni11cr_111_11m2_pure_alias` | Ni11Cr | Cr | 4.90 GPa |
| `shimanek2022_v2_ni11mn_111_11m2_pure_alias` | Ni11Mn | Mn | 5.12 GPa |
| `shimanek2022_v2_ni11fe_111_11m2_pure_alias` | Ni11Fe | Fe | 5.20 GPa |
| `shimanek2022_v2_ni11cu_111_11m2_pure_alias` | Ni11Cu | Cu | 4.51 GPa |
| `shimanek2022_v2_ni11si_111_11m2_pure_alias` | Ni11Si | Si | 4.17 GPa |
| `shimanek2022_v2_ni11ti_111_11m2_pure_alias` | Ni11Ti | Ti | 4.24 GPa |

These are selected factual values from [Shimanek et al., arXiv:2108.06412v2,
Table 2, PDF/printed p. 27](https://arxiv.org/pdf/2108.06412v2#page=27).
Exact strings preserve two decimal places, including **4.90** and **5.20**;
numeric JSON values may be 4.9 and 5.2. Decimal precision is not uncertainty.

```sh
python -m materials_boundaries catalog predictions --query shimanek_v2_table2_cr_mn_fe_cu_si_ti --text --lang en
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six-en --lang en
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six-zh --lang zh
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six-ja --lang ja
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_cr_mn_fe_cu_si_ti --output /tmp/ni11x-six-de --lang de
python -m materials_boundaries prediction plot --group-id shimanek_v2_table2_ni_al_co --output /tmp/ni-original --lang en
python -m materials_boundaries prediction plot --group-id dubois_2006_si_directional_instability --output /tmp/si-first-instability --lang en
```

`--group-id` is exact and case-sensitive. Without it, `prediction plot` still
selects the old Ni/Al/Co group. The unfiltered prediction catalog now returns 12
records; the Shimanek source or ideal-shear quantity filter returns nine. Catalog
query results do not define a plotting group. No automatic nine-point overlay,
duplicate predictions, merged group or cross-family plot is added.

JSON/CSV preserve canonical data independently of display language. Localized
record/group names and human caveats support en/zh/ja/de. Explicit selection
exports canonical JSON, CSV, wide/narrow SVG and standalone HTML using the
existing interface. See the four [getting-started guides](GETTING_STARTED.en.md).

## Scientific and source boundaries

[Sections 2.1–2.2, pp. 5–7](https://arxiv.org/pdf/2108.06412v2#page=5) support
the common procedure: a 12-atom, three-layer fcc-derived orthorhombic cell with
one shear-plane Ni site replaced by X; (111)[1,1,-2] positive pure-alias shear;
a prescribed shear angle with relaxed atomic positions and non-prescribed cell
parameters. Strength is the maximum along that constrained path, not a complete
stability envelope. The source reports layer-count dependence.

The selected six labels have no printed pv/sv suffix. This does not verify
PAW/POTCAR dataset identity/version or a valence configuration and does not prove
absence of semicore states. Do not remove suffixes from other source labels to
force them through the existing contract. Other Table 2 cells are outside this
bounded addition.

Reported VASP/PAW, 350 eV, Gamma 9×8×7, 5e-6 eV and 0.2 eV
Methfessel–Paxton settings are retained. The GGA citation is **Perdew et al.
(1992), reference 43**, not an inferred PBE label. Exact physical temperature,
scalar pressure, magnetic state/spin polarization, PAW datasets, strain grids and
statistical/total uncertainty remain unverified. Static DFT/smearing do not mean
physical 0 K; a residual-stress threshold does not mean exact 0 GPa.
**0.08 GPa peak convergence is not an error bar, SD or confidence interval.**

Comparability is **published-method-only**. Unknown conditions are not proven
equal, and raw inputs were not audited. These are Ni11X model predictions, not
pure-X strengths, commercial-alloy grades, experimental measurements, engineering
allowables or universal upper bounds. Ni11Si shear does not belong to the
pure-Si tensile first-instability family.

The added evidence and group qualifier record the wider inspected-cell scope.
The preserved protocol's historical temperature-reason wording refers to the
original three calculations; new-six source review also leaves temperature
unknown. Its wording is not silently changed or taken as a verified temperature.

The official arXiv v2 cache was rechecked against prior provenance and pages
5–7/27 visually inspected. Two independent cell transcriptions and text extraction
agree; this is not independent scientific review. Raw inputs, the journal typeset
version and a new license page were not inspected. Existing arXiv non-exclusive
license evidence is not a new general republication grant. Source PDFs, full text,
table/page images and figures are not bundled. See [source scope](SOURCES.md)
and [third-party notices](../THIRD_PARTY_NOTICES.md).

## Validation and downstream migration checklist

```sh
python -m unittest discover -s tests -p test_release_metadata.py -v
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
```

- Pin added values, exact strings, compositions, locators, localized names and
  the new explicit membership/order; check duplicate IDs and reference integrity
- Preserve the original six record objects, both existing protocols/groups and
  source records. Test original Ni default and Si outputs separately, allowing
  only expected engine-version metadata changes
- Same-source additions legitimately expand a source-filtered query. A historical
  text digest must project its original record IDs rather than freeze the full
  current query to three. Retain a separate assertion that the live source query
  includes all nine; do not weaken the scientific guard or regenerate away a
  preservation failure
- Exercise schema validation, negative scientific mutations, JSON/CSV round trips,
  explicit/default CLI selection and all four localized outputs. Confirm six new
  group points, a zero-origin GPa axis, separate provenance, and no inferred error
  bars, interpolation, measured-strength or universal-bound labels
- Inspect actual SVG pixels at wide/narrow widths and all four locales; test
  browser HTML reflow separately where supported. Structural checks alone are
  not a visual or browser-QA pass
- Build/install the wheel and use `scripts/check_wheel_metadata.py` to check the
  packaged version, scientific catalogs, CLI and exactly eight composite rules

This checklist does not claim the checks have passed. Source checking, software
validation and machine-assisted translations do not constitute independent
scientific peer review, native-language review, replication or legal clearance.
