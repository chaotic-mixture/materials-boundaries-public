# Fiber and elastomer material references: v0.31.0

Six source-qualified industrial products/formulations add six identities, grades,
states and selected properties. The registry contains **34 identities,
17 qualified grades, 34 states and 34 properties**, with four quantities.
Categories are 13 inorganic, 8 metal, 8 polymer and 5 composite; evidence classes
are 11 manufacturer references, 19 published experimental references,
3 published handbook references and 1 published measurement-derived reference.
The material lane resolves 33 source records. Seven bibliography additions bring
the full source registry to **90** (89 bibliographic/source records and one
original synthetic-demo provenance record). These counts are derived from the
validated graph, without aliases, sizing alternatives, cure schedules or specimens
adding identities. The prior [28 selections](MATERIAL_COVERAGE_v0.30.0.md) remain intact.

## Selected source facts

1. **Toray T700S single carbon filament, Mesquita specimen 1**:
   **249.8300317 GPa tensile modulus**, one individual result, n=1.
   `refprop_toray_t700s_mesquita2021_specimen1_tensile_modulus`.
   [Mendeley dataset V1](https://data.mendeley.com/datasets/ygyym4vy6b/1),
   T700/T700-analysed_data.dat, physical line 2, column 6. The exact inspected
   member URL/hash supplies the numeric cell; the explicitly linked
   [methods article](https://pmc.ncbi.nlm.nih.gov/articles/PMC8114124/), §§1–2.2,
   supplies detailed methods. Selected diameter 6.8300000 µm and measured gauge
   12.1010000 mm remain exact strings. The window is **0.1 to 0.6% strain**,
   rate 0.6 mm/min, after source machine-compliance calibration. Filament-axis
   tension is method-supported; isotropy and crystal orientation are not asserted.
   Cross-sectional-area shape estimator, temperature, RH, sizing and lot remain
   unknown. This is neither the 217-row mean nor manufacturer nominal 230 GPa.
   Preserved source digits do not claim corresponding experimental accuracy
2. **Deutsche Basalt Faser, A76.9.2-sized single filament group**:
   **56.1 ± 11.5 GPa tensile modulus**, reported mean ± SD.
   `refprop_deutsche_basalt_faser_a76_9_2_messmer2024_tensile_modulus`.
   [Messmer et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11053685/),
   §§2.1–2.2 and Table 1, Sizing Type 1. Twenty fibres were prepared/tested,
   but pre-test loading breakages leave successful retained n unknown.
   Nominal gauge 12 mm, rate 2 mm/min, 20 N load cell; optical diameters at
   three positions. The circular-area equation is explicitly for strength,
   and does not verify modulus normalization. Modulus fit window, compliance
   correction, test temperature and RH remain unknown
3. **Dow Corning Sylgard 184, commercial 10:1-parts formulation, 100 °C/48 min
   tensile cure**: **2.05 ± 0.12 MPa Young's modulus**, reported **95% CI**.
   `refprop_dow_corning_sylgard184_johnston2014_100c_youngs_modulus`.
   [Johnston et al., 2014](https://doi.org/10.1088/0960-1317/24/3/035017),
   PDF pp.3–5, Table 1, §§3.1/4/4.1 and Table 2. Six test samples were averaged,
   but CI estimand, construction and fit/averaging order are unspecified.
   No mean-specific CI, SD, SE or coverage factor is inferred. Ten-to-one parts
   is not expressly mass or volume. The selected tensile cure is 48 minutes;
   53 minutes belongs to compression. Tests average 21 °C/39% RH at 254 mm/min.
   The source linear region is **below 40% strain**, with no specified lower
   endpoint or exact fitting algorithm. Its 0.40 dumbbell-end geometry/strain
   correction was already applied; it is not applied again. The formulation
   is not relabelled pure PDMS, an isotropic proof or a global hyperelastic constant
4. **SMR 10 study NR vulcanizate**: **0.958 ± 0.006 g/cm³ density**.
   `refprop_smr10_bianchi2025_nr_mass_density`.
   [Bianchi et al., 2025](https://doi.org/10.3390/molecules30143035),
   Table 1 NR density, Table 8 formulation and §3.3.1. Recipe in phr:
   SMR10 100 / sulfur 1.5 / ZnO 5 / stearic acid 2 / ZDBC 0.7, no nanoclay.
   Cure 120 °C/3 bar; numerical cure duration unspecified. ASTM D792
   Archimedes weighing in air/methanol at unspecified numerical room temperature,
   three density specimens. Adjacent solvent extraction/swelling and n=4 are
   crosslinking-density procedures, not conditioning/count for this mass density
5. **Vistalon 2504/N550 study unfoamed EPDM vulcanizate**:
   **0.996 ± 0.02 g/cm³ geometrical density, ρgeom**.
   `refprop_vistalon2504_n550_bianchi2022_epdm_mass_density`.
   [Bianchi et al., 2022, v2](https://doi.org/10.3390/polym14194058),
   Tables 1/3/5 and §2.3.2. Recipe in phr: EPDM100 / sulfur3 / ZnO3 /
   stearic acid1 / N550 carbon black20 / TMTD0.87 / ZDBC2.50. No paraffin,
   blowing agent, NaCl or PEG is added to the selected unfoamed state.
   Cure 170 °C/8 bar; ten minutes refers to compounding, not a verified cure
   duration. Ten square specimens use balance mass / caliper external volume,
   including any void volume. Pycnometry's 23 °C and 60 repetitions do not apply.
   Discussion that theoretical ρbulk lacks SD is retained as a contextual clue;
   it does not explicitly define the selected ρgeom ± or its central aggregation.
   Methods ρbulk=1.042 versus Table 5 0.996 remains an unresolved source
   discrepancy; no correction or porosity derivation is made
6. **PERBUNAN 3445 F study NBR REF vulcanizate**:
   **1.031 ± 0.001 g/cm³ density**.
   `refprop_perbunan3445f_tamas_benyei2025_ref_mass_density`.
   [Tamás-Bényei et al., 2025](https://doi.org/10.1021/acsomega.5c05493),
   §§2.1–2.3, Table 3 and §3.4. Recipe in phr: NBR100 / PEG4000 4 /
   stearic acid1 / ZnO5 / Sul1.5 / MBTS2.5; no recycled carbon fibre.
   Sul is the listed ACTMIX S-80 input, not an independently established
   pure-sulfur dose. Cure 170 °C/200 bar, 2 mm sheets, compound-specific t90;
   exact REF duration is not transcribed. Density-specific method, count,
   temperature, conditioning and statistics remain unknown. Mechanical-test
   metadata is not borrowed; selected REF is neither raw NBR nor D_Fo foam

All three rubber values retain **reported ± with unspecified statistical meaning**
and **unspecified central aggregation**. Their amplitudes are not removed,
marked unreported, called SD, converted to ranges or silently made means.
Rubber finite-extension M100/M200/M300 measures and finite-strain slopes do not
become Young's modulus. No rubber modulus is added by this batch.

## Scope, held candidates and rights

All six are catalog-only, with `universal_bound: false`,
`engineering_allowable: false`, `independent_scientific_review: false` and
`raw_data_reanalysis: false`. Independent source-transcription review is separate
from scientific validation, raw-data analysis, engineering suitability or legal
clearance. No shared chemical family becomes a generalized numerical constant.

This batch excludes Kevlar 49 (prose GPa versus figure CN/dtex conflict),
Dyneema SK76/UHMWPE (no qualifying pinned measured scalar/source rights in this
selected package) and Sylgard 527 (unresolved cure conflict). These holds are
scoped evidence decisions, not a global ban on future independently qualified IDs.

The selected original Johnston work is CC BY 3.0; the other selected articles
and the actual Mendeley V1 dataset have inspected CC BY 4.0 notices. Attribution,
DOI/source links, license links and transcription/organization changes are kept.
NBR's separately credited Figure 1 is excluded. Public payload contains selected
facts and authored qualifications, without PDFs, screenshots, full tables,
figures, source dumps or dataset archives. MIT packaging does not relicense source
assets. See [source-specific notices](../THIRD_PARTY_NOTICES.md),
[contract](MATERIAL_REFERENCE_CATALOG.md#v0310-fiber-and-elastomer-batch) and
[migration](MIGRATION_v0.31.0.md).
