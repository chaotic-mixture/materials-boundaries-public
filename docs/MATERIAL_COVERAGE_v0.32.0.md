# Metals and natural-fiber material references: v0.32.0

This batch adds **nine source-qualified identities and nine selected original
experimental properties** to the prior [34 selections](MATERIAL_COVERAGE_v0.31.0.md):
**34 + 9 = 43 identities**, with one selected property per identity. The additions
are five tensile strengths, two mass densities and two chord Young's moduli,
supported by eight original sources. The catalog graph contains **43 identities,
19 qualified grades, 43 states and 43 properties**, using five of the existing supported quantities.
Categories are 13 inorganic, 13 metal, 10 polymer and 7 composite. Evidence
classes are 11 manufacturer, 28 published experimental, 3 published handbook
and 1 published measurement-derived reference. Eight appended source records
bring the full source registry to **98** (97 bibliographic/source records and
one original synthetic-demo provenance record). Two separately reported
uncertainty measures for one property do not create another property or identity.

AZ31 and AZ91D are distinct alloy compositions; flax, hemp, silk and wool are
separate biological fiber identities. A different treatment, gauge length, test
sample, cocoon, alias, source-year suffix or translation never increases the
identity count. These records identify the selected source-qualified materials,
not every product or specimen sharing an elemental, alloy or biological name.

## Selected source facts

1. **AZ91D magnesium alloy, non-ultrasonically-treated as-cast control**:
   **mean ultimate tensile strength 160 MPa**, ten tensile specimens.
   [Puga et al., 2015](https://doi.org/10.3390/met5042210), PDF p.7 / printed
   p.2216, §3 paragraph immediately below Table 2; Figure 5 on PDF p.8 supports
   the mean curve. Measured OES composition qualifies the alloy identity.
   Specimens were machined after cooling to room temperature; tensile testing
   was at qualitative room temperature and **0.02 s⁻¹**. Numerical temperature,
   humidity, loading direction and UTS uncertainty are not reported. The ±
   values for hardness or porosity do not describe this tensile result
2. **Zinc, stated 99.9% purity, annealed initial material**:
   **ultimate tensile strength 60 ± 6 MPa**.
   [Kulczyk et al., 2022](https://doi.org/10.3390/ma15144892), PDF p.7,
   Table 2, UTS row, column **0**. The selected initial material was annealed at
   **150 °C for 30 min**, before ECAP or hydrostatic extrusion. Testing was
   along the sample axis at qualitative room temperature and **0.008 s⁻¹**.
   Column 0 denotes the unprocessed control; it is not a zero tensile-test
   rate. Central aggregation, ± meaning and tensile replicate count remain
   unspecified. Grain-size CV/SD language does not define this tensile ±.
   This is not a universal zinc constant or a zinc-alloy result
3. **Unreinforced as-extruded AZ31 comparator**:
   **mean ultimate tensile strength 274 ± 4.9 MPa**, three tensile specimens.
   [Chen et al., 2023](https://doi.org/10.3390/ma16031139), PDF p.10,
   Table 2, AZ31 row / UTS column / “This work”. Tension was parallel to
   extrusion at qualitative room temperature. The ± kind remains unspecified;
   mean/variance wording does not establish SD. Tensile loading rate is unknown:
   **6 mm/s is extrusion speed**. Detailed SPS and 400 °C extrusion settings
   are study-process context from composite fabrication, not a separately
   itemized AZ31 preparation protocol. Nano-TC4/acetone preparation is not
   transferred to this unreinforced comparator. AZ31B certification is not
   inferred. PDF extraction contains duplicated/overlaid text, while the
   independently rendered p.4 is clean and legible
4. **Molybdenum, impurity-characterized NBS solid tube**:
   **density 10.21 × 10³ kg/m³ at 298 K**, reported mean of four density
   determinations by water displacement in a pycnometer.
   [Cezairliyan et al., 1970](https://doi.org/10.6028/jres.074A.010), printed
   p.72, §4.2(d) / PDF p.8. The source reports **relative standard error of
   the mean 0.02%** there and in Table 12, p.86, separately from
   **approximately 0.1% estimated inaccuracy**, p.84, §7.1(c) and Table 12.
   Neither is specimen SD, a confidence interval or an engineering bound;
   they are not combined or converted to absolute uncertainty. Four
   determinations do not establish four independent specimens. The source's
   impurity inventory, 360 < total < 560 ppm by weight, is not converted into
   a purity certificate. The density timing relative to pulse annealing and
   density-test pressure remain unknown
5. **Tungsten, impurity-characterized NBS solid tube**:
   **measured density 19.23 × 10³ kg/m³ at 293 K**.
   [Cezairliyan and McClure, 1971](https://doi.org/10.6028/jres.075A.027),
   printed p.284, §2 final paragraph before §3 / PDF p.2. Density procedure,
   replicate count and uncertainty are not supplied. Molybdenum's pycnometer
   procedure or uncertainty and the paper's high-temperature-property errors
   cannot be borrowed. The impurity inventory, 450 < total < 740 ppm by
   weight, is not a purity certificate. Timing relative to the approximately
   30 annealing pulses and later measurements remains unspecified; the pulse
   temperatures and vacuum pressure are not ambient-density test conditions
6. **Romanian flax technical-fiber bundles, Faltin/Suceava 2022**:
   **mean chord Young's modulus 31.75 GPa; CV 56.12%**, selected 10-mm
   gauge group, 25 tested fibers.
   [Stochioiu et al., 2024](https://doi.org/10.3390/ma17194871), PDF p.10,
   Table 4, Flax (10 mm), Average Stiffness and adjacent CV columns. These
   are mechanically extracted technical bundles containing elementary fibers,
   not isolated elementary fibers or engineered matrix-composite specimens
7. **Romanian hemp technical-fiber bundles, HempFlax/Sebeș 2023**:
   **mean chord Young's modulus 22.63 GPa; CV 72.02%**, selected 10-mm
   gauge group, 25 tested fibers. The same
   [Stochioiu article](https://doi.org/10.3390/ma17194871), PDF p.10,
   Table 4, Hemp (10 mm), supplies this separate plant identity's result.
   For both plant fibers, the chord interval is **0.1–0.2% strain**, with
   axial tension at **1.5 mm/min**, source slack correction and **no machine-
   compliance correction**. Circular minimum-area normalization ignores the
   lumen. The chord definition and no-compliance rationale are on **PDF p.8**;
   Figure 6 is on p.7, methods span pp.5–8 and statistics §2.2 is on p.8.
   Temperature, RH and successful/retained-test count remain unknown; 25
   tested fibers do not imply 25 independent plants or lots. Methods cite
   ASTM C1557-03 while the bibliography cites C1557 (2020); no exact-edition
   compliance is independently asserted. CV stays a relative descriptor,
   without calculated SD or an absolute ± interval
8. **Bombyx mori native silk fibroin, Chinese strain 932, degummed
   control-diet fibers**: **mean quasistatic ultimate tensile strength
   332 MPa**.
   [Cheng et al., 2019 issue](https://doi.org/10.3390/ma12010014), §3.4,
   PDF p.8; Figure 4b and caption on p.10 support mean and SD. The SD is
   explicitly graphical, but no numerical amplitude is supplied in inspected
   prose/tables. Its amplitude remains **null**, never zero or a digitized
   estimate, and it is not described as wholly unreported uncertainty.
   Thirty test samples came from five chosen cocoons, not thirty independent
   cocoons; a separate successful/retained-test count is not stated. The
   sampling rationale concerns **intraspecific and
   intraindividual variability**. Tests used a 6-mm gauge under ambient
   conditions. Numerical temperature, RH, strain rate and explicit area
   formula remain unknown. Section 2.7 names ANOVA whereas Figure 4 names an
   unpaired two-tailed t-test; no significance claim is selected. This is
   neither regenerated silk, cocoon wall, modified-diet composite nor the
   continuous-dynamic-analysis result. The 2019 issue article was published
   online on 20 December 2018
9. **Latxa sheep wool from Urnieta, soap-cleaned standalone fibers**:
   **tensile strength 163 ± 23 MPa**.
   [Arbelaiz et al., 2024](https://doi.org/10.3390/ma17194912), PDF p.7,
   Table 2, Soap cleaned / Strength / Current work. Adjacent text on pp.7–8
   explicitly identifies SD, but the selected center is not explicitly called
   an arithmetic mean. Preserve **SD 23 MPa with central aggregation
   unstated**, not mean ± SD. Fifteen fibers were tested at 10-mm gauge and
   **1 mm/min**, using a cylindrical-area approximation from optical diameter.
   The approximate average diameter is not used to recompute strength.
   **55 °C is soap-cleaning temperature**, not test temperature. Test RH,
   temperature, exact drying/equilibration and successful-test denominator
   remain unknown. ASTM D638-10 Type V concerns composite specimens, not this
   standalone-fiber test. No peroxide treatment or PLA-composite result is
   assigned to the selected fibers

The existing broad `composite` category for flax/hemp is qualified as natural
hierarchical lignocellulosic bundles, not engineered resin composites. The
`polymer` category for silk/wool is qualified as natural protein fibers, not
purified fibroin or keratin; residual lanolin is not ruled out for wool. These
curation mappings do not add a `natural_fiber` category or establish composition,
purity, isotropy or general applicability.

## Representation and review limits

The closed generic `reported_measures` uncertainty alternative preserves numeric
CV, graphical-only SD with null amplitude, SD with unnamed central aggregation,
and separate relative SEM and approximate estimated inaccuracy. Old uncertainty
variants remain distinct. Zinc and AZ31 retain their existing unspecified-±
representation; AZ91D and tungsten retain their genuine uncertainty unknowns.
See the [contract](MATERIAL_REFERENCE_CATALOG.md#v0320-metals-and-natural-fiber-batch)
and [migration guidance](MIGRATION_v0.32.0.md).

Molybdenum and tungsten keep the complete scientific-notation source strings
and mantissa precision in `value_text`; canonical fixed-point `number` strings
are `10210` and `19230`. Exact notation equivalence is a lexical check, not unit
conversion, a new measurement or permission to replace source display by bare
expanded integers. Both metals require this generic lexical support.

Independent source-transcription review accepted all nine selected numbers
without numerical correction. It required the AZ31 scope/extraction correction,
plant-fiber locator/category/standard-edition qualifications, silk sampling and
significance-method qualifications, and the generic representation described
above. Only AZ91D, zinc and corrected AZ31 use the previous contract without
new representation support; tungsten also needs the new source-notation matcher,
so six additions require generic support. Source-fact acceptance alone does not
establish final-payload admission, passing software tests or publication. Exact schema/runtime/output validation,
old-record parity and installed-wheel checks remain release gates.

All records remain `catalog_only`, with `universal_bound: false`,
`engineering_allowable: false`, `independent_scientific_review: false` and
`raw_data_reanalysis: false`. This adds no evaluator, material-specific formula,
new physical quantity, ranking, statistical reconstruction or general material
bound. A comprehensive errata/retraction audit, experimental replication and
raw-data reanalysis are not claimed.

## Provenance and rights

The eight original source PDFs were independently read back from publisher/NIST
and matched the inspected assets; three deposited fiber-paper XML files also
matched. The zinc publisher readback resolves its initial mirrored-PDF concern
without erasing that retrieval history. Source-identity/integrity checks do not
establish scientific truth or legal clearance.

Six article-specific notices explicitly identify
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The two NBS
employee-authored journal papers use the separate
[NIST Technical Series rights policy](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications),
with the required courtesy attribution; this is neither an assumed Creative
Commons license nor permission for SRD/cryogenic datasets or credited third-party
content. See [full source-specific notices](../THIRD_PARTY_NOTICES.md#metals-and-natural-fiber-references-v0320).

Only minimal authored, scoped facts, full citations, exact locators, rights
links and original qualifications belong in the public payload. Source PDFs,
HTML/XML, whole source tables, figures, screenshots, extracted source dumps and
failed-download responses are excluded. The project's MIT license does not
relicense source works or imply author, publisher or NIST endorsement.
