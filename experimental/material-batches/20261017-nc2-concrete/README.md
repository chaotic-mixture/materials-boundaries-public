# NC2 concrete: one source-qualified candidate

This packet proposes one composite identity, one nominal 28-day water-saturated
state and one measured density reference against experimental baseline
`eaf16e1eb1edad17fbf78ac7385566f6a4e86a94`. It adds no grade or source. It does not
modify runtime catalogs, formal-component pins or released main's 1081 admissions.
Candidate preparation contributes zero formal admissions.

The source is Lucyna Domagała, Maria Margańska and Marek Miazgowicz (2024),
*Moisture Impact on Static and Dynamic Modulus of Elasticity in Structural
Normal-Weight Concretes*, Materials 17(15), 3722,
[DOI 10.3390/ma17153722](https://doi.org/10.3390/ma17153722).
Its [retained primary XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11313055/fullTextXML)
was independently reread on 2026-10-17. SHA-256
`8eee9708ea9e257dc060117f6b7c20a031443c982ecb98aa92cf5227e7479ec5`
matches the existing registered source asset. The source record is reused
unchanged; this packet's new inspection is recorded in the property and review.

Table 1 distinguishes NC2 from the already cataloged NC1 formulation. NC2 uses
470 kg/m^3 cement, 174 kg/m^3 water and 1.9 kg/m^3 superplasticizer, with reported
nominal w/c 0.37. NC1 uses 377, 208 and 0 kg/m^3 respectively, with w/c 0.55.
Both have 1140 kg/m^3 coarse aggregate and 570 kg/m^3 fine aggregate. This is a
composition-level mixture distinction; moisture states, curing ages, aliases and
additional properties do not create extra identities. CEM I 42.5 R identifies the
cement constituent, not a certified final-concrete grade.

Table 3 reports NC2 `D_w = 2340 kg/m³` as a mean at nominal age 28 days.
Section 2 and Table 2 identify three cylinders per concrete series, measured
sequentially when saturated and then oven-dry under EN 12390-7:2019. The shared
count is three, not six. Only the saturated mean is proposed here.

The original unknowns remain explicit: density-test temperature, density
basis terminology, exact measurement subprocedure, instrument, SD and confidence
interval. The reported 20 °C concerns curing/storage. The maximum individual
density deviation of 20 kg/m³ is neither an SD nor an uncertainty interval.
The text describes 24-hour demolding followed by 28-day water storage while
calling the testing age 28 days; the packet preserves the nominal designation
without repairing that chronology. No porosity is inferred from absorption.

The XML permissions grant [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
for the article-authored content. The selected original study tables have no
separate third-party credit. Attribution, the license link and these original
curation qualifications are retained. Only selected factual metadata is bundled;
no XML, PDF, figure, full table, screenshot or raw asset is included. The source
is not relicensed under the project's code license. All four required locale
slots use English fallback names without claiming native-language review.

The packet reuses the existing identity/state/property schema and
`merge_material_catalogs` validation. An integration manifest can bind these
files by hash for `scripts/integrate_material_candidates.py`; parent-coordinated
integration is a separate step. Source transcription is not independent
scientific review, replication, raw-data reanalysis or engineering qualification.
All scientific-review, universal-bound and engineering-allowable flags remain
false, with `evaluation_support: catalog_only`.
