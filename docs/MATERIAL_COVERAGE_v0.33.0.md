# Porous, natural and mineral material references: v0.33.0

This additive batch adds **eight source-qualified identities and eight selected
experimental density facts** to the prior [43 selections](MATERIAL_COVERAGE_v0.32.0.md):
**43 + 8 = 51 identities**, one selected property per identity. The catalog graph
contains **51 identities, 19 qualified grades, 51 states and 51 properties**.
Categories are **16 inorganic, 14 metal, 11 polymer and 10 composite**. Evidence
classes are **11 manufacturer, 36 published experimental, 3 published handbook
and 1 published measurement-derived reference**. Seven original articles support
the eight additions; the full source registry is **105** (104 bibliographic/source
records and one original synthetic-demo provenance record).

All eight properties use the existing `mass_density` quantity and existing
representation. No schema, runtime capability, uncertainty alternative, physical
quantity, unit or scientific evaluator is added. The prior 43 identities and
properties remain unchanged. Source formulation/type labels LPO-1, CP and K1,
and the AMD5 precursor designation, do not create new qualified finished-material
grades. A specimen, treatment, alias or translation is not another identity.

## Selected source facts

1. **Lupranol-based LPO-1 rigid polyurethane foam, Ivdre 2024**:
   **apparent density 43.2 kg/m³**, a reported scalar with unknown density
   aggregation, count and uncertainty. [Table 10, LPO-1 × Apparent density](https://pmc.ncbi.nlm.nih.gov/articles/PMC11013755/#polymers-16-00942-t010)
   reports the experimentally characterized optimized foam, not only a modeled
   response. Table 9 specifies the source recipe; LPO-1 is not the article's
   suberin-based SPO formulation. The larger mold is 30 × 30 × 10 cm and cure
   is 24 h at room temperature. Section 2.8 reports ISO 845:2006, without a
   detailed density subprocedure or independently verified compliance.
   **40 kg/m³ is the compression-normalization density**, not this measurement;
   the modeled target 45 kg/m³ is also not the selected result. The reported
   94 vol.% closed-cell content is not total porosity. Cup-test n=3/81 per series
   and six mechanical cylinders do not supply density n. Cure temperature,
   10 °C thermal testing and 25 °C polyol rheometry do not establish the
   density-test temperature. Do not import normalized compression properties
   as tensile or generic Young's moduli, or count LPO-2/LPO-3 as new identities
2. **AMD5-derived open-cell Al–Mg–Ti SPS foam, Kosenko 2022**:
   **density 0.45 g/cm³**, a reported scalar with unknown density aggregation,
   count and uncertainty. [Table 4, SPS × Density](https://pmc.ncbi.nlm.nih.gov/articles/PMC8839437/#materials-15-00931-t004)
   is the selected g/cm³ source; Table 6's repeated g/m³ label is a retained
   discrepancy. Input powder is Al 94.8 / Mg 4.8 / Ti 0.4 wt.%, not a final
   bulk phase assay or the existing Hydro 6061 identity. NaCl space holders
   of 500–1000 µm use powder/salt mass ratio 10:90; initial pressing is 5 MPa,
   followed by SPS at 550 °C / 38 MPa / 5 min and hot-water leaching for 12 h.
   Section 3.3 describes paraffin-sealed Archimedes weighing in air and ethanol:
   a pore-inclusive measurement, not skeletal density. The source does not
   explicitly name apparent/bulk basis, so `density_basis` stays `not_stated`.
   Coating-volume correction details are absent. Table 4's “Underwater Weight”
   label conflicts with the ethanol method; do not infer water immersion.
   The ethanol reference density at 25 °C is not an explicit specimen-test
   setpoint. Three compression samples/electrical locations do not fix density
   n; mechanical-coupon dimensions do not establish density-coupon dimensions.
   Source-calculated 83% porosity uses an approximately 2.7 g/cm³ dense-aluminum
   reference, not an independently measured open-pore fraction. Do not import
   the ASD6 replication-route results, Figure 9 mechanical results or the
   third-party Table 6 comparison
3. **Quercus suber natural reproduction cork, study untreated control**:
   **density 0.17 g/cm³; separately reported SD 0.01 g/cm³**, ten specimens
   in the selected species/treatment group.
   [Prasetia et al., Table 5, Qs RC / Untreated / Density](https://pmc.ncbi.nlm.nih.gov/articles/PMC10914824/#Tab5),
   PDF p.9, explicitly defines the parentheses as SD, but does not explicitly
   call the central values means. Preserve `summary_statistic: reported_value`
   with `reported_measures`, numeric absolute SD and an explicit unnamed-center
   qualification. Table 2 p.3 supports n=10 for this group, not n=40 or ten trees.
   Two planks came from the Castelo Branco cork forest of Amorim Group,
   Portugal, via FC Korea Land Co., Ltd. Cubes are 20 mm in radial, tangential
   and longitudinal directions. After oven drying they were conditioned at
   **25 ± 5 °C and 60 ± 5% RH**; these are not exact test conditions. The
   selected air-dried moisture is **4.61%, SD 0.34 percentage points**, not
   another selected property or the density SD. Equation (3), PDF pp.3–4,
   defines air-dried mass divided by air-dried specimen volume and cites
   KS F 2198, but supplies no volume-measurement subprocedure. Keep density
   basis `not_stated`, without an exclusively geometric or skeletal method.
   “Untreated” means no study boiling intervention; commercial history is
   unestablished. Do not count boiled cork as another identity, import the
   other species' green density 0.39 g/cm³, relabel the center as a mean, or
   turn the SD into a min/max range, confidence interval or allowable
4. **Phyllostachys edulis (Moso) bamboo culms from China**:
   **reported species-average density 746 kg/m³**, six specimens, three nodal
   and three internodal from separate culms.
   [Drury et al., Table 1, Moso × ρ](https://www.mdpi.com/2071-1050/15/8/6472#table_body_display_sustainability-15-06472-t001),
   PDF p.6, labels the physical properties averaged. Density uncertainty and
   the exact averaging estimator are not stated. No borax treatment is
   reported for Moso, but its shipping container was fumigated
5. **Guadua angustifolia bamboo culms from Colombia**:
   **reported species-average density 655 kg/m³**, six specimens, three nodal
   and three internodal from separate culms.
   [The same Table 1, Guadua × ρ](https://www.mdpi.com/2071-1050/15/8/6472#table_body_display_sustainability-15-06472-t001)
   provides this distinct botanical identity's result. Guadua was dipped in
   borax solution after harvest/before shipping; internal nodes were pierced.
   Shipping containers for all tested species were fumigated for up to 24 h.
   Both species underwent one year of laboratory equilibration away from
   sunlight/water with air circulation. **15.8% moisture is the study-wide
   average**, not an exact species/specimen condition. Exact temperature, RH,
   harvest age and fumigant identity remain unknown. Six specimens underlie
   each species summary; repeated density-measurement count is not stated.
   Section 2.1 p.5 supplies dimensional measurements to 0.1 mm and ISO
   22157:2019 specimen-length context, but no density-specific weighing
   procedure, formula or standard. Both density bases remain `not_stated`.
   Do not label either bamboo generically untreated, assign 15.8% moisture to
   either species, invent a room-temperature setpoint, count nodal/internodal
   states as distinct identities, reconstruct density from ratios of Table 1
   mean geometry/mass, use mechanical CoVs as density uncertainty, or claim
   skeletal density or density including the hollow central lumen
6. **Al-Taouab CP unfilled laboratory plaster formulation**:
   **apparent density 1103.13 kg/m³**, a reported scalar with unknown density
   count, aggregation and uncertainty.
   [Saad Azzem and Bellel, §4.3.1 first paragraph](https://www.mdpi.com/2075-5309/12/8/1119#sec4dot3dot1-buildings-12-01119),
   supported by Figure 11 and §3.2 Eq. (2), uses specimen mass divided by
   external volume calculated from dimensions. This is pore-inclusive,
   not skeletal density. CP contains zero wheat straw at water/plaster 0.7;
   specimens spent 72 h in molds and 28 days in the laboratory at room
   temperature. Ambient conditioning is not certified oven drying. Source
   “pure plaster” does not establish pure calcium-sulfate dihydrate or
   measured hydrated-phase fractions. Do not borrow straw-only 60 °C/24 h
   drying, thermal-coupon dimensions, thermal-test 20–30 °C or its 5% setup
   accuracy for density. Exact density temperature/RH and moisture remain unknown
7. **Boral-supplied brick-soil 100% control, laboratory-fired clay brick**:
   **bulk density 2122 kg/m³**, a reported value with unknown density-specific
   aggregation, count and uncertainty.
   [Mohajerani et al., Table 4, Bulk Density × Control Bricks](https://www.mdpi.com/2075-5309/9/1/14#table_body_display_buildings-09-00014-t004),
   corroborated by §3.3, reports the **0% biosolids** control, not a marketed
   Boral grade. Raw soil was dried 105 °C/24 h, mixed 20 min and compacted at
   240 kPa; green bricks were air-dried 48 h, oven-dried 105 °C/24 h, ramped
   0.7 °C/min to 1100 °C, held 3 h and furnace-cooled. These are preparation
   conditions, not density-test setpoints. The global triplicate/average
   statement occurs in the initial raw-material testing paragraph; its density
   applicability is unclear. **Do not assert density-specific n=3 or a reported
   density mean**. The separate shrinkage count does not resolve this scope.
   Cited Australian masonry standards do not establish a specific density
   submethod or independently verified compliance. Exact density-test climate
   and post-firing moisture conditioning remain unknown. Do not import the
   strength-row parenthetic 25% as control composition, use Table 11 as the
   selected measurement, or import Table 4's regression-estimated thermal
   conductivity 1.09 W/(m K) as a measured property
8. **Upper Silesian Carboniferous K1 sandstone, quartz arenite**:
   **bulk density 2.34 ± 0.01 g/cm³**, a **reported average of five replicates**.
   [Jonczy and Mucha, Table 3, γs × K1](https://www.mdpi.com/1996-1073/15/7/2692#table_body_display_energies-15-02692-t003),
   with averaging scope in §4.2, does not explicitly name an arithmetic
   estimator or define ± as SD, SE, confidence interval, range or instrument
   error. Preserve `reported_mean` and `reported_plus_minus_unspecified`;
   do not derive 2.33–2.35 as observed limits. Section 3.2 Eq. (4) uses dry
   specimen mass / specimen volume. The density paragraph mentions dimensions,
   while Eq. (2) defines volume hydrostatically; the exact volume subprocedure
   remains ambiguous. Five cylinders per type have diameter and height
   50 ± 0.5 mm, which is not density uncertainty. Exact K1 mine/site, drying
   temperature/time, density temperature and RH are unknown. Petrographic
   proportions are not mass percentages. Contextual state metadata retain
   effective/open porosity **5.5 ± 0.6%**, a reported average of five with
   undefined ± from Table 3; this is not an additional reference-property
   record or total porosity. Do not impose an exclusively
   geometric or hydrostatic method, reinterpret this as grain/skeletal
   density, or transfer EN 1926:2007 / PN-G-04303:1997 mechanical standards
   to density

## Identity, representation and review limits

The existing broad `composite` category for cork and the two bamboos is a
qualified curation mapping for hierarchical natural tissue. It does not claim
an engineered resin binder, laminate, artificial reinforcement or homogeneous
composition. The natural cork is not northern-red-oak wood or an agglomerated
binder product; the bamboos are distinct species, not duplicate states. The
source-qualified PUR formulation and Al–Mg–Ti precursor chemistry support the
foam identities independently of porous architecture. Plaster, fired control
brick and K1 sandstone are distinct from existing concrete, marble and ceramics.

No new grade is inferred from LPO-1, CP, K1, botanical name, supplier or AMD5
precursor. No supplementary thermal, compressive or porosity result becomes a
ninth property. All eight exact density-test temperatures remain unknown.
Source rounding, method scope, conditions and statistical meanings remain
separate from any exact unit re-expression. See the [existing-contract
application](MATERIAL_REFERENCE_CATALOG.md#v0330-porous-natural-and-mineral-batch)
and [migration guidance](MIGRATION_v0.33.0.md).

Independent **source-transcription review** on 5 October 2026 accepted all eight
selected values without numerical correction, after direct inspection of the
original source XML, PDFs or publisher HTML. It corrected the proposal's
v0.3.2 baseline typo to **v0.32.0**, natural-material exclusions to explicit
“Do not” wording, Boral's overstrong average implication, and K1's overstrong
arithmetic-estimator wording. These are evidence-fidelity checks, not
independent scientific validation, raw-data reanalysis, experimental replication,
standard-compliance certification or a comprehensive errata/retraction audit.

All new records remain `catalog_only`, `universal_bound: false`,
`engineering_allowable: false`, `independent_scientific_review: false` and
`raw_data_reanalysis: false`. No density-strength inference, cross-material
ranking, general porous relation, universal bound or evaluator input is
created. All eight executable rules and earlier scientific families remain
unchanged. Exact-payload admission, old-record/output parity, four-language
inspection, full tests and installed-wheel verification are separate release
gates, not results implied by source-transcription acceptance.

## Provenance and rights

All seven original articles carry article-specific
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) notices inspected on
5 October 2026. The selected facts are presented as the authors' own
experimental results, without a separately credited third-party exception at
the selected cells. Full citations, DOI/source links, precise locators and the
limited authored transcription/qualification are recorded in
[third-party notices](../THIRD_PARTY_NOTICES.md#porous-natural-and-mineral-references-v0330).
Bamboo's generic HTML metadata mentions CC BY 3.0, but the article-specific
footer and PDF explicitly state CC BY 4.0; that discrepancy remains documented.
The cork review applies to the inspected PDF marked “corrected publication 2024”.

The public payload contains selected facts and original curation, never the
local audit sources: no source PDF, full HTML/XML, source dump, complete source
table, figure or screenshot is redistributed. The project's MIT license does
not relicense the articles or imply author/publisher endorsement. Source
integrity/rights review does not establish scientific truth or permission for
unrelated or separately credited material. No publication is implied by these
release documents.
