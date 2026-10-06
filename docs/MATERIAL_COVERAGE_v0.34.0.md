# Polymer and biogenic material references: v0.34.0

This batch adds six distinct source-qualified identities and one selected
experimental property for each: **51 + 6 = 57 identities**, **20 qualified
grades**, **57 states** and **57 properties**. Three original articles bring
the source registry to **108** records (107 bibliographic/source records and
one synthetic-demo provenance record). Categories are 16 inorganic, 14 metal,
16 polymer and 11 composite. Evidence classes are 11 manufacturer, 42 published
experimental, three published handbook and one measurement-derived reference.

There is no schema or runtime extension. The selections use one mass density,
three Young's moduli and two tensile moduli, with the existing exact/at-least
sample-count and SD/undefined-plus-minus representations. All previous records
remain unchanged; material/reference envelope versions remain 1.0.0.

## Selected facts and source conditions

1. **BioPBS, study B0**: Young's modulus **575 ± 65 MPa**, mean ± SD, ten
   tensile replicates. Ewurum and McDonald, Table 6 p.12 and footnote a;
   preparation §2.3 p.3 and test §2.9 p.5. Source material is Mitsubishi
   Chemical Group BioPBS, designated **FZ91PM/FZ91PB**. The combined designation
   is unresolved: no single or newly invented combined qualified grade is
   assigned. B0 is the neat comparator, not the DCP-reactive R0 material.
2. **PBS / 20 wt.% Indulin AT kraft-lignin blend, B20**: Young's modulus
   **960 ± 77 MPa**, mean ± SD, ten tensile replicates, same Table 6. The
   20 wt.% is relative to total polymer mass (§2.3), explicitly unlike the
   unspecified ratio basis of the PBS/PBAT study below. It is the simple-blend
   B20 series, not DCP-reactive R20. The broad composite category describes a
   lignin-filled polymer; no continuous-fiber laminate is implied.

Both tensile selections use injection-molded dog-bones. The source describes
140 °C strand extrusion/pelletization and Dynisco LMM compounding at 100 rpm,
140 °C for 10 min before injection molding. It reports ASTM D1708, an Instron
5500R-1132, Epsilon 3542 extensometer and crosshead speed 1 mm/min. The modulus
fit window, actual test temperature/RH and post-molding conditioning remain
unknown. Do not transfer the separate 120 °C hot-pressed-disc route or the
DCP/acetone pretreatment to these tensile specimens. SD is rounded up to the
mean precision where necessary; superscript letters are Tukey groups, not
uncertainty tokens. No SD-to-SE/CI conversion is made.

3. **Indulin AT softwood kraft lignin**: density **1.226 g/cm³**, Table 1 p.5,
   Lignin row. The Westvaco-supplied lignin was measured by nitrogen gas
   pycnometry using 2 g on a Quantachrome ultra-pycnometer 1000 (§2.2 p.3).
   The source does not name a density basis, so it remains `not_stated`;
   neither bulk nor skeletal/true density is invented. Aggregation, replicate
   count, temperature, pressure and uncertainty are unknown. The sample mass
   is not n=2. The broad polymer category does not claim a chemically pure,
   uniform molecular species. Indulin AT is retained in the identity; no
   independently qualified grade is inferred from this trade name alone.

These three selections are from [Ewurum and McDonald (2025), *Lignin
Reinforcement in Polybutylene Succinate Copolymers*, Polymers 17, 194](https://doi.org/10.3390/polym17020194).

4. **Dairy-manure-derived PHBV, sample PHBV-39**: Young's modulus
   **0.87 ± 0.04 GPa**, mean ± SD, **at least five replicates**, Table 9 p.15
   and footnote a. It is PHBV produced by mixed microbial consortia fed
   fermented dairy manure. The suffix **39 is operational day**, not HV%,
   grade, sample count or another polymer family. Sections 2.1–2.2.1 pp.2–3
   describe biomass extraction and purification; Table 1 gives purified
   PHBV-39 purity **88.5 ± 4.7%** and GC-MS 3HV molar fraction **0.21 ± 0.01**.
   Their ± semantics are not defined and do not inherit the mechanical-table
   SD definition. Purified does not mean 100% pure; the NMR comparison is
   attributed to earlier work and does not replace the selected GC-MS context.
   Section 2.2.8 pp.4–5 describes 60 °C vacuum drying overnight, 180 °C hot
   pressing and 10 × 2.5 × 0.5 mm specimens. A DMA Q800 applies 3 N/min until
   yield at source-described room temperature, with 10 mm gauge length.
   Preserve the force ramp, not crosshead speed, and the lower-bound count,
   not exactly five. Numerical room temperature, RH, fit window and a tensile
   standard remain unknown. No selected tensile-strength/yield reinterpretation
   or extra flexural property is added.

Source: [Abbasi et al. (2022), *Effect of 3-Hydroxyvalerate Content on Thermal,
Mechanical, and Rheological Properties of Poly(3-hydroxybutyrate-co-3-hydroxyvalerate)
Biopolymers Produced from Fermented Dairy Manure*, Polymers 14, 4140](https://doi.org/10.3390/polym14194140).

5. **BASF Ecoflex C1200 PBAT**: tensile modulus **52.01 ± 28.78 MPa**,
   Table 3 p.7, PBAT row. Table 1 p.3 prints the trade designation
   “Eco flex C1200” and BASF, Ludwigshafen, Germany. This supports one new
   source-designated qualified grade; the article spelling is retained as an
   alias. No chemical-purity or biobased-feedstock claim is inferred.
6. **BioPBS FZ91 / Ecoflex C1200 PBS/PBAT 70/30 blend**: tensile modulus
   **253.49 ± 13.40 MPa**, same table, PBS-PBAT (70/30) row. The ratio basis
   is not explicitly stated: **do not label it wt/wt, mass or volume fraction**.
   Table 2 p.3 identifies the selected unfilled 100/0/0 formulation, with
   no added lignin or ZnO. Constituent trade names do not establish a finished-
   blend grade. It is classified broadly as a polymer blend.

For both, §2.3 p.3 reports overnight 80 °C polymer drying, 120–145 °C extrusion,
pellet drying at 80 °C for 24 h and 120–145 °C injection molding of dog-bones.
Section 2.6.2 p.5 reports **five specimens per group**, conditioning **48 h at
25 °C**, then Instron testing at **25 °C**, citing ASTM D638. The source does
not define the central aggregation or ± kind: use `reported_value` and
`reported_plus_minus_unspecified`, never an inferred mean, SD, SE or CI.
Crosshead speed, RH and the modulus fit window are unknown. Retain the label
**tensile modulus**, without upgrading it to generic/isotropic Young's modulus.
The table's adjacent yield-strength column is not imported. The parent review
reported supplementary agreement, but the locally retained/hash-identified
asset is the main PDF only; no supplementary-file inspection/hash is claimed.

Source: [Mtibe et al. (2022), *Fabrication of a Polybutylene Succinate
(PBS)/Polybutylene Adipate-Co-Terephthalate (PBAT)-Based Hybrid System Reinforced
with Lignin and Zinc Nanoparticles for Potential Biomedical Applications*,
Polymers 14, 5065](https://doi.org/10.3390/polym14235065).

## Identity, rights and verification boundaries

The two blends differ in constituents, not merely processing state. Other lignin
loadings, reactive counterparts, PHBV operational days and PBS/PBAT ratios are
not counted as additional identities. The other study's neat PBS is not added
again. PCL remains on hold pending modulus-scale/fit clarification; leucite
glass-ceramic B3 remains on hold for the unsupported biaxial-flexural-strength
quantity and source discrepancy. Neither is in production data.

All three retained publisher PDFs explicitly state CC BY 4.0 on p.1. Full
attribution, adaptation scope and asset hashes are in the [third-party
notices](../THIRD_PARTY_NOTICES.md#polymer-and-biogenic-references-v0340).
Source assets, extracted pages, screenshots and full tables stay outside the
public checkout/package. No restricted vendor documents, JARVIS mirrors or
NIST cryogenic coefficient data are imported.

Independent original-PDF transcription review accepted the six numbers without
correction; local rereading and selected-table rendering followed. This is not
independent scientific peer review, raw-data reanalysis, verified standards
compliance or experimental replication. All facts remain catalog-only,
non-universal and non-allowable. Four-language names are machine-assisted;
structural parity is not native-speaker or scientific translation review.

See [migration and validation gates](MIGRATION_v0.34.0.md). Source acceptance
does not establish software-test, publication, CI or deployment success.
