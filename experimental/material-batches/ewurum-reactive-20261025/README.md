# Ewurum reactive PBS/lignin candidate formulations

This candidate-only packet selects R10, R20, R30 and R45 from Ewurum and McDonald (2025), *Lignin Reinforcement in Polybutylene Succinate Copolymers*, DOI [10.3390/polym17020194](https://doi.org/10.3390/polym17020194). It proposes four composite identities, four injection-molded states and four measured Young's modulus properties, with zero new sources and zero grades. **Actual admitted delta: zero.** Independent candidate review, identity adjudication, runtime integration and publication remain pending. No product test result is claimed by this source packet.

The frozen baseline is `8ccd217599fd462d13d7435bdfb02a0825e4eacd`. Existing scientific records and historical candidate evidence are not changed by these files. The 24 accepted computed compositions and 62 unadmitted examples are outside this selection.

## Four selected original measurements

| Table 6 label | Nominal lignin loading, wt.% | Young's modulus, MPa | SD, MPa | Tukey group |
| --- | ---: | ---: | ---: | --- |
| R10 | 10 | 751 | 40 | b′ |
| R20 | 20 | 716 | 49 | b′ |
| R30 | 30 | 910 | 85 | b |
| R45 | 45 | 1256 | 162 | a |

Table 6 on PDF p.12 explicitly reports mean plus/minus standard deviation. Its footnote says SD is rounded up to the mean's reported precision where necessary. Values and displayed precision are retained; no unrounded observations, confidence intervals or standard errors are reconstructed. Tukey superscripts are comparison-group labels, not uncertainty units or extra identities.

Section 2.9 on p.5 reports injection-molded microtensile dog-bone specimens, 10 tensile replicates, source-cited ASTM D1708-18 (2018; reference [32] on p.15), an Instron 5500R-1132 with Bluehill v3.3, an Epsilon 3542 extensometer and 1 mm/min crosshead speed. Ten replicates do not establish independent manufacturing batches. Numerical test temperature, pressure, relative humidity, post-molding conditioning, gauge geometry and modulus-fit interval remain unknown. The source identifies the cited standard edition; independent standard compliance remains unverified. No dimensions or conditioning are inferred from the standard. The properties are source-qualified catalog references, not universal constants, automatic calculator inputs or engineering allowables.

## Composition and identity boundary

Section 2.3 on p.3 identifies two series: Bxx simple blends and Rxx reaction-extruded formulations containing DCP. The selected R recipes contain 10, 20, 30 or 45 wt.% Indulin AT softwood kraft lignin relative to total polymer mass. Preserve the reported phrase **0.25 wt.% DCP added to PBS** without resolving its denominator or normalizing a complete mass-fraction recipe.

Section 3.1 and Table 1 on p.5 report nonzero gel fractions of 4.7, 4.3, 12.7 and 26.2% for R10, R20, R30 and R45. These contextual observations and the explicit DCP formulation support a source-qualified chemical-formulation/reaction distinction. They do not establish exact final stoichiometry, retained DCP, conversion, crosslink density or molecular architecture. Gel fractions are contextual identity evidence only and are not additional admitted properties. Section 2.4 (PDF p.4) determines contextual gel fractions on hot-pressed DCP cross-linked PBS-lignin material, not the injection-molded tensile dog-bones. These results support formulation-level reaction context only and do not determine the tensile specimens’ gel fraction or final network.

The PBS input is reported as BioPBS FZ91PM/FZ91PB. The individual grade is unresolved, so grade remains null. DCP input purity does not establish final-product purity. The composite category describes lignin-containing polymer formulations; Rxx labels are study labels, not certified grades. Processing, specimens, suppliers and translated names do not create additional identities.

At the frozen baseline, the existing source's property/state/identity joins represent B0, Indulin AT and B10/B20/B30/B45. The B-blend scopes explicitly distinguish their reactive R counterparts. Earlier B-series packets excluded Rxx as outside those packets; that history is preserved and is not prior approval of Rxx. Complete current-catalog alias/equivalence screening remains a separate gate. Exclude R0 from this bounded candidate because its identity distinction from neat PBS requires separate adjudication.

## Selected preparation state

DCP was dissolved in acetone and mixed with milled PBS, followed by 24 h in a fume hood and 12 h at 80 degrees C in a vacuum oven. Separate 50 g formulations were extruded at 140 degrees C into strands and pelletized. Portions were compounded with a Dynisco Lab Mixer Molder/Extruder at 100 rpm for 10 min at 140 degrees C, then injection-molded into dog-bone specimens. The compounding temperature is not a separately reported injection-mold temperature or tensile-test temperature.

The separate 120 degrees C hot-pressed-disc route, 75 mm die and 3.1 mm disc thickness are excluded from tensile geometry. Drying and preparation temperatures do not supply missing post-molding conditioning or test conditions.

## Cached primary evidence and reuse terms

Authors: Nnaemeka Ewurum and Armando G. McDonald. Academic editor Luis Alves is not an author.

The retained official publisher PDF is 3,211,541 bytes, 16 pages, SHA-256 `766d17f0e92c7e93cd57a3a5e97dddff0cb66a84bba6bf9118fbd0796d4c2e6f`. Its original publisher URL is recorded in `source-review.json`. The existing receipt records one HTTP 200 request on 2026-10-17, zero retries and no automatic redirects. This review reused cached evidence, recomputed the PDF hash and visually inspected cached pages 1, 3, 5 and 12. It made no new request for this source and does not claim fresh retrieval or a comprehensive errata/retraction audit.

Article p.1 explicitly grants [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). No separate third-party credit or reuse restriction appears on the inspected selected tables and their relevant captions or footnotes. Selected facts, attribution and authored scope qualifications are curated adaptations. Other studies' comparison values, complete tables, article prose dumps, figures, raw PDF, screenshots and raw measurements are excluded. Source assets remain outside the repository; no project MIT relicensing of those assets is claimed.

Reuse source `ewurum_mcdonald_2025_pbs_lignin` unchanged. Its canonical sorted compact UTF-8 JSON plus terminal LF has SHA-256 `358d6486d107da45ed76c3aa7c7a448213957c7b94afc811e9ad75e294641ca0`. This separate review augments the selection evidence without rewriting the historical source record.

Retained receipt hashes are `4b965f840935008b4d0449a182c27e9cf56cbaed01ed2dec22a7458f8d1357f7` for the publisher-read receipt and `a7cb6b87d2cff4b0679d80b6dd3b7778078f6f5a6a0972f33826680dc5984e04` for the selected-page-render receipt. These hashes identify private retained evidence; neither receipt nor its private local path is bundled here.

This review supports source transcription and explicit qualification. It is not independent scientific peer review, experimental replication, raw-data reanalysis or legal clearance. Runtime admissions, independent review and publication require their separate gates.

## Candidate review correction

The earlier candidate `f55af18be0f809b5c8f06fba3fcbeb9db5fb1206` incorrectly marked the standard edition unknown. Reference [32] explicitly cites ASTM D 1708-18 (2018), linked from section 2.9. Cached PDF pages 4 and 15 were visually checked for this correction and the separate gel-test specimen scope. Values, SDs and tensile replicate counts are unchanged. Historical B-series records remain untouched.
