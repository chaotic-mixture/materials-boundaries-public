# Delgado-Aguilar PLA/PCL candidate formulations

This candidate-only packet selects seven nominal binary thermoplastic PLA/PCL blends from Marc Delgado-Aguilar, Rita Puig, Ilija Sazdovski and Pere Fullana-i-Palmer, *Polylactic Acid/Polycaprolactone Blends: On the Path to Circular Economy, Substituting Single-Use Commodity Plastic Products*, **Materials** 2020, 13(11), 2655, DOI [10.3390/ma13112655](https://doi.org/10.3390/ma13112655). It proposes seven polymer identities, seven injection-molded states, seven measured Young's modulus properties, one source and zero grades. **Actual admitted identity delta: zero.** Parent candidate review, runtime integration and publication remain pending.

The frozen baseline is `437950c414ea340eda340babe7b63dee9fcee535` on branch `experimental/delgado2020-pla-pcl-candidates`. Baseline source-qualified identities are natural 1010 + metal 32 + inorganic 59 + polymer 30 + composite 37 = 1168. With 24 accepted computed compositions the public experimental total is 1192; the main-line total remains 1081. The 62 unadmitted examples are excluded. These candidates add seven only if later gates clear. Existing catalogs, schemas, runtime, historical packets and accepted computed compositions remain unchanged.

## Seven selected original measurements

| Table 1 label | Nominal PLA/PCL, wt% | Calculated V_PCL join | Young's modulus, GPa | SD, GPa |
| --- | ---: | ---: | ---: | ---: |
| B95/5 | 95/5 | 0.054 | 3.70 | 0.13 |
| B90/10 | 90/10 | 0.108 | 3.60 | 0.26 |
| B85/15 | 85/15 | 0.162 | 3.38 | 0.27 |
| B80/20 | 80/20 | 0.214 | 3.20 | 0.19 |
| B60/40 | 60/40 | 0.421 | 2.55 | 0.09 |
| B40/60 | 40/60 | 0.621 | 1.86 | 0.11 |
| B20/80 | 20/80 | 0.814 | 1.13 | 0.05 |

Table 1 supplies the sample labels and nominal mass recipes. Section 2.2 says PCL volume fraction was calculated from density measurements; those exact volume-fraction strings join Table 1 to the matching Table 2 rows. The calculated fraction is contextual evidence, not an extra measured property or final composition assay. Leading zeros and trailing precision are retained. Pure B100/0 and B0/100, all other properties, rule-of-mixtures/Voigt-Reuss results and commercial comparison values are excluded.

Section 3.2, paragraph following Equation (6), explicitly identifies the Table 2 Young's modulus variability as standard deviation. The central aggregation and sample count are not stated. Preserve the numeric absolute SD independently of the unknown central statistic; do not infer mean, median, SEM, confidence interval, coverage factor, population, independent batches or replicate count. The existing `reported_measures` contract stores one numeric absolute `standard_deviation` per result with `summary_statistic: not_stated` and `reporting_basis: not_stated`; the legacy mean-requiring SD alternative is not used.

## Identity and specimen scope

The finite 22-input audit at baseline 437950c414ea340eda340babe7b63dee9fcee535 is reproducible with the adjacent build_identity_review.py and identity-review.json. The seven explicit nominal PLA/PCL mass recipes are absent from recorded formulation scopes. Existing Porima PLA, Ultimaker Tough PLA and Proto-pasta conductive PLA have incomplete full-composition disclosure; unknown additives do not prove PCL absence or global non-equivalence. Tough PLA is one identity with Black and White states and unspecified acrylic chemistry, not verified PMMA. Nominal recipe differences support conditional distinct candidate identities; source year, labels, suppliers, processing, specimens and differing modulus values alone do not.

Section 2.1 names PLA literally as Ingeos Biopolymer 4043D supplied by Nature Works LLC, and PCL Capa 6500 supplied by Perstorp Specialty Chemicals AB. These are ingredient context only, not a finished-blend grade, certified purity or exact tested-lot identification. The Introduction states that no coupling agent was incorporated; this does not establish that all commercial additives are absent. All finished-blend `grade_id` values are null; aliases are empty. English fallback names occupy all four required locales, with no native-language review claimed. The broad classification is `polymer`: two thermoplastic phases are blended without a separate external reinforcement ingredient in the reported recipe. Section 3.2's model discussion calling PCL a filler does not establish an externally reinforced composite or exact phase/network chemistry.

Materials were dried at 60 degrees C until constant weight. PLA and then PCL were mixed at 190 degrees C and 80 rpm until constant torque, pelletized through a knife mill with 10-mm mesh, and stored in a 60 degrees C oven to prevent moisture absorption. These steps do not specify post-molding test conditioning. Section 2.3 lists five heating zones at 175, 180, 185, 185 and 190 degrees C and an injection-pressure range of 330-600 bar. Section 3.1 says both injection-molding temperature and pressure were modified according to blend melt flow index. Retain these as reported setup/range context only; exact per-formulation temperature and pressure settings are unresolved, and no universal molding recipe is assigned to the seven states.

Source-reported conventional tensile Young's modulus from injection-molded specimens, tested on an Instron 1122 with a 5-kN load cell according to source-cited ISO 527-1:2012, at a crosshead speed of 2 mm/min and a clamp separation of 115 mm. The modulus-fit interval, strain estimator and extensometer gauge length are not stated. Test temperature, humidity, pressure, post-molding conditioning, specimen type/dimensions, orientation, count and independent production batches remain unknown. The 115-mm clamp separation is not an extensometer gauge length. No standard-derived defaults or independent compliance are claimed. MFI's 210 degrees C / 2.16 kg, impact ISO 179 and flexural ISO 178 conditions are excluded from tensile-modulus conditions. The selected properties are catalog-only references, not universal constants, automatic calculator inputs or engineering allowables.

## Inspected source and reuse scope

The cached [official Europe PMC XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7321633/fullTextXML) is 157502 bytes, SHA-256 `1fc618818e73292837129bd4bf9885b71982974d5e7fead0056276fb28f8cb6b`. The [official PMC article HTML](https://pmc.ncbi.nlm.nih.gov/articles/PMC7321633/) is 256628 bytes, SHA-256 `dd24715210b6aae58c9a2c38ec352e03492ff822fd21bc5a275353dc88014d23`. Each recorded acquisition was one bounded HTTP 200 read, with 45-second timeout, 5,000,000-byte ceiling, no redirects and no retry. The retained private access receipt SHA-256 is `f268d03a5d28e49b6f3dcfdf9ff62641e6c17b6af4623f00c9efa2373b6a758f`. This packet author reused cached evidence and made no network request.

Selected XML and HTML table cells agree. Article-specific HTML and JATS permissions explicitly grant [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); copyright is 2020 by the authors, with MDPI as licensee. No separate third-party credit or restriction was observed for the selected Tables 1-2. Curation changes comprise selected factual transcription, structured metadata and authored scope/unknown qualifications. Attribution and license links are preserved; no author or publisher endorsement is implied.

**No original PDF was verified.** The PDF link returned a reCAPTCHA interstitial; no bypass was attempted. No PDF bytes, SHA-256, rendered pixels or PDF equivalence to the inspected XML/HTML are claimed. Archive revision and comprehensive correction/retraction status remain unverified. Raw PDF/XML/HTML, screenshots, article text dumps, full source tables, figures, private paths and raw measurements are excluded from the repository and release artifacts. No source content is relicensed under project MIT.

The independent selected-source and contract audit passed (private audit SHA-256 `aa24116d1f26304d3fd96944a34526ede66f2cb459560f174e77daa2e3f7ab28`). This supports bounded transcription and compatibility with the unchanged contract. It is not scientific peer review, experimental replication, raw-data reanalysis or legal clearance.

## Candidate files and review boundary

`packet-spec.json` contains explicit source facts and shared contexts for the unchanged `scripts/prepare_formulation_packet.py` compiler. `source-review.json` records the source, rights, join, method, statistics and exclusion evidence. The adjacent `identity-review.json` and `build_identity_review.py` reproduce the finite baseline identity audit. Prepared packet, receipt and focused validation evidence are assembled separately during candidate preparation and remain subject to independent parent review.

No test or artifact result is asserted by these authored source files. Candidate tests, source checks and compiler replay do not grant admission, scientific approval, reuse rights beyond the article-specific terms or publication approval.
