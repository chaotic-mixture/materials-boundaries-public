# Second material-reference batch: v0.30.0

This batch adds seven distinct identities, seven source-scoped states and seven
selected properties, with no new grades. The seven identities are two elemental
crystalline materials, three wood species, one concrete formulation and one
natural carbonate rock. Source-number labels and repeated determinations do not
create extra material identities. Existing silicon strength predictions remain
separate from the new density reference.

The validated registry now contains **28 identities, 11 qualified grades,
28 states and 28 selected properties**, covering four quantities. Categories
are **11 inorganic, 8 metal, 5 polymer and 4 composite**. Property evidence
classes are 11 manufacturer references, 13 published experimental references,
3 published handbook references and 1 published measurement-derived reference.
The material lane resolves **26 primary/evidence source records**; this release
appends **10** bibliography records, bringing the full source registry to **83**.
These counts are derived from the assembled validated graph, not the number of
articles or named specimens. The
[initial 21 selections](MATERIAL_COVERAGE_v0.29.0.md) are retained unchanged.

## Selected facts and limits

1. **Historical NBS single-crystal silicon X2**: mass density
   **2.329 1289 g/cm³**, canonical number `2.3291289`.
   `refprop_nbs_silicon_x2_1975_mass_density`.
   [Bowman, Schoonover and Carroll, 1975](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir75-768.pdf),
   PDF p.19 / printed p.13, §7D, X2 new accepted value. Original experimental
   metrology with corrected reduction, not a computational prediction. The
   20 °C reference basis comes from the
   [1974 companion](https://pmc.ncbi.nlm.nih.gov/articles/PMC6728515/),
   §2.5.3, §2.6 and Table 6, linked to the same crystals by the 1975
   introduction/§7. This does not claim that the 1975 table prints temperature
   or all measurements occurred at 20 °C. One physical crystal, no revised
   numerical uncertainty; not a modern certified standard or universal silicon
   value. Dopant, quantitative purity, orientation and polymorph are unestablished
2. **Germanium, Johnson Matthey source number 4065**: crystallographic mass
   density **5.325 grams per cubic centimeter**, at **25 °C**.
   `refprop_nbs_ge4065_crystallographic_density`.
   [Swanson and Tatge, 1953](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf),
   PDF pp.22–23 / printed pp.18–19, §2.6; unit definition on PDF p.6 /
   printed p.2. The source calculates density from experimentally measured
   powder-XRD lattice data and adopted cubic cell content, not specimen weighing
   or DFT. The 26 °C diffraction-pattern temperature is separate from the 25 °C
   density basis. Number 4065 does not establish a supplier stock code, batch,
   unique physical specimen or grade. Specimen count and density uncertainty
   remain unknown
3. **Sugar maple, Acer saccharum Marsh.**: flexural modulus
   **12,600 MPa** on a **12% moisture-content reference basis**.
   `refprop_usda2010_sugar_maple_mc12_flexural_modulus`.
   [Kretschmann, 2010, Table 5–3a](https://research.fs.usda.gov/download/treesearch/37427.pdf),
   PDF p.5 / printed p.5–5, Maple / Sugar, 12% row, static-bending modulus
   column; [species identification](https://research.fs.usda.gov/silvics/sugar-maple)
4. **Northern red oak, Quercus rubra L.**: flexural modulus
   **12,500 MPa** on a **12% moisture-content reference basis**.
   `refprop_usda2010_northern_red_oak_mc12_flexural_modulus`.
   [Kretschmann, 2010, Table 5–3a](https://research.fs.usda.gov/download/treesearch/37427.pdf),
   PDF p.5 / printed p.5–5, Oak, red / Northern red, 12% row, static-bending
   modulus column; [species identification](https://research.fs.usda.gov/silvics/northern-red-oak)
5. **Sitka spruce, Picea sitchensis (Bong.) Carr.**: flexural modulus
   **10,800 MPa** on a **12% moisture-content reference basis**.
   `refprop_usda2010_sitka_spruce_mc12_flexural_modulus`.
   [Kretschmann, 2010, Table 5–3a](https://research.fs.usda.gov/download/treesearch/37427.pdf),
   PDF p.8 / printed p.5–8, Spruce / Sitka, 12% row, static-bending modulus
   column; [species identification](https://research.fs.usda.gov/silvics/sitka-spruce)
6. **NC1 normal-weight concrete, nominal 28-day water-saturated state**:
   mean mass density **2330 kg/m³**, **n=3** cylinders.
   `refprop_domagala2024_nc1_28d_saturated_mass_density`.
   [Domagała, Margańska and Miazgowicz, 2024](https://doi.org/10.3390/ma17153722),
   Table 3 NC1 / D_w, with §2/Table 2 for specimen program and §3.1 for mean
   scope. The hashed numerical asset is
   [Europe PMC XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11313055/fullTextXML),
   table ID `materials-17-03722-t003`. EN 12390-7:2019 is reported, but the
   exact volume/mass subprocedure and density basis are not stated. The 20 °C
   curing/storage condition is not density-test temperature. No SD or density
   uncertainty is assigned; the source's maximum individual deviation from the
   mean is not either statistic. The cement designation is not a concrete grade
7. **Carrara marble, disk specimen 13**: bulk mass density **2760 kg/m³**,
   **n=1** physical specimen; repeat count unknown.
   `refprop_wubalem2025_carrara_marble_specimen13_mass_density`.
   [Wubalem, Caselle, Taboni and Umili, 2025](https://doi.org/10.3390/geosciences15040145),
   PDF p.3, Table 2, specimen 13; §3.1 calls densities measured. Diameter
   43 mm, height 16.0 mm and mass 64.0 g identify the selected disk but do not
   establish its density procedure. Temperature, moisture, method, porosity and
   uncertainty are unknown. Dry/environmental-temperature wording belongs to
   P-wave tests. Source group-SD and unselected group-geometry discrepancies do
   not change this cell or supply an uncertainty for it

The three wood values are **compiled species averages**, not new experiments
performed in 2010. The metric table converts Table 5–3b; some dry test results
were adjusted to a common 12% moisture basis, with each selected cell's
history unknown. All use clear, straight-grained wood and a simply supported,
center-loaded beam with span/depth 14:1. The bending-derived longitudinal
modulus includes shear deflection; no suggested approximate 10% correction is
applied. It is not isotropic or axial Young's modulus. Test temperature,
specimen/tree count, cell-specific uncertainty, exact rate and growth-ring
loading plane remain unknown. The generic 22% coefficient of variation for a
different green-wood population is not assigned. Biological-composite category
does not mean an engineered resin/laminate or a structural grade.

## Admission scope

All seven are `catalog_only`, with no universal bound, engineering allowable,
evaluator autofill, conversion or extrapolation. Numerical-source transcriptions
were independently checked; `independent_scientific_review: false` and
`raw_data_reanalysis: false` remain accurate. Numerical sources have retained-byte
hashes; the separately inspected 1974 silicon companion does not, and that gap
is explicit. GaAs is excluded behind its indentation-method contract gate.

Only selected facts, bibliographic metadata, locators and original qualifications
are bundled, without PDFs, source images, XML/HTML dumps or full tables.
[Contract supplement](MATERIAL_REFERENCE_CATALOG.md#v0300-second-material-batch) ·
[Migration](MIGRATION_v0.30.0.md) ·
[Source rights](../THIRD_PARTY_NOTICES.md#second-material-reference-batch-v0300)
