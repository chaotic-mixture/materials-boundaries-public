# Solid NBR/recycled-carbon-fiber formulations

This review-only batch proposes six composite identities, six states and six Table 4 tensile-strength properties from one source family. It adds zero grades and zero sources, and the prepared packet admits zero formal materials. The 24 accepted computed compositions and 62 excluded examples remain unchanged.

The baseline is f5bdcc44a4743f7da6220871dbf3857224a925b0: 1118 core / 1142 project identities, 19 composites, 21 grades and 116 sources. Integration would give 1124 core / 1148 project / 25 composites. These are proposed deltas, not a claim that this candidate directory edits runtime data.

## Selected original values

| Table 3/4 label | Recycled milled CF input, phr | Tensile strength, MPa |
| --- | --- | --- |
| B | 5 | 5.26 ± 0.78 |
| C | 10 | 5.11 ± 1.27 |
| D | 20 | 5.33 ± 0.74 |
| E | 30 | 5.47 ± 1.05 |
| F | 40 | 4.60 ± 0.68 |
| G | 50 | 4.57 ± 0.72 |

Table 3 on PDF p.4 / article p.61279 gives the fixed inputs NBR 100, PEG 4, STA 1, ZnO 5, Sul 1.5 and MBTS 2.5 phr, with the six different mCF loadings above. Table 2 and §2.1 on p.3 identify PERBUNAN 3445 F NBR, PEG4000, Zoltek Type 45 recycled milled carbon fiber and the additive products. The Table 2 shorthand Perbunan 3445 is not a separate grade. Sul means ACTMIX S-80 input; it is not converted to pure elemental sulfur. Neither fiber input purity nor total-composite mass fractions are reconstructed.

The six different fiber loadings establish the source-defined composition distinctions. B–G labels, supplier names, cure, test direction and specimen count do not create identities. REF is already cataloged with mCF=0 and is excluded. D_Fo and the source foaming investigation are outside this batch; no extra identity is claimed for foam morphology or preparation.

## Method, statistics and unresolved conflict

The selected property column is Table 4 tensile strength (MPa), PDF p.6 / article p.61281. Section 2.2 on p.3 specifies ISO 37 Type 2 dumbbells, a Zwick Z005 machine with 5 kN load-cell capacity and 500 mm/min crosshead speed. Specimens were cut from nominally 2 mm vulcanized sheets and tested in two mutually perpendicular orientations. The paragraph below Table 4 explicitly says the tensile results were averaged across all specimens regardless of orientation.

The packet therefore preserves reported_summary with reported_mean, supported by that exact averaging statement. It does not infer an arithmetic estimator, weighting, sample count or universal isotropy. The tensile-strength ± type is not explicitly established: hardness/abrasion SD statements and adjacent strain-at-break SD language do not unambiguously define it. Each amplitude remains reported_plus_minus_unspecified. Numerical tensile specimen count, numerical test temperature, relative humidity and pre-test conditioning remain unknown; two orientations are not n=2. No ANOVA reconstruction or laboratory-default conditions are used.

The abstract says 20 phr rCF increased tensile strength by 15%, whereas Table 4 gives D = 5.33 MPa and REF = 6.01 MPa. This unresolved contradiction is retained in source_discrepancies for all six selected properties. Table values are transcribed without repair and no performance-improvement claim is made. The prose value 5.467 MPa for E is consistent with Table 4 rounding to 5.47; additional precision is not imported. M100/M200 are finite-extension rubber measures, not Young's modulus, and are excluded.

Section 2.3 describes internal mixing at 110 °C, first 15 rpm for 8 min then 40 rpm for 4 min, and pressing at 170 °C / 200 bar with compound-specific t90. These are preparation conditions, not tensile-test temperature/pressure. No exact cure duration is estimated from a plot. Nonfoamed preparation does not prove zero porosity. All selected properties remain catalog_only, non-universal and non-allowable; independent_scientific_review and raw_data_reanalysis remain false.

## Primary source and rights

Péter Tamás-Bényei and Péter Sántha. Sustainable Reinforcement for Rubbers—Potential Application of Recycled Carbon Fibers. ACS Omega 2025, 10, 61276–61287.
DOI: https://doi.org/10.1021/acsomega.5c05493
Original article PDF hosted by the authors' department:
https://www.pt.bme.hu/publikaciok/2010_publ_sustainable-reinforcement-for-rubbers-potential-application-of-recycled-carbon-fibers_1229.pdf

The PDF has 12 pages / 13,382,151 bytes and SHA-256 6922d25630c21c03062722a3efdf621b87129c40f06097625161364151c87aef, exactly matching the existing frozen source. The complete source record tamas_benyei_santha_2025_nbr_rcf is reused unchanged; canonical sorted compact UTF-8 JSON plus terminal LF has SHA-256 4d40efc4af60d0c10243e10b5ea9c6e9bc7d7afd6094746ee592c22a0f97363d.

Article p.1 explicitly licenses the article under CC-BY 4.0. It separately credits Ceresana Figure 1 with permission; that figure and its third-party values are excluded. The batch contains only selected original recipe/measurement facts, locators and authored curation with attribution. No PDF, screenshot, complete table, figure, source dump or watermark is published or relicensed under project MIT. Historical source notes about the earlier REF density selection remain frozen; this batch and its independent review document the additional bounded tensile-row inspection.

One authorized GET returned HTTP 200, with zero metadata queries and zero retries. The response stayed below 15 MB. The configured 40-second urllib socket timeout was not an overall-transfer deadline: actual wall time was 139.165238 seconds. The same request completed normally, without a second request or process termination. Exact start/end, URL, byte count and hash remain in external source-research/nbr-download-receipt.json. Original assets remain outside the repository under incremental-evidence/primary-table-growth-6-20261020/source-research/.

A separate reviewer inspected the original PDF tables, methods, article-specific rights and abstract conflict. source-review.json is an unchanged copy of the frozen independent review; it is source transcription evidence, not scientific peer review, raw-data reanalysis, replication or legal clearance.

Independent catalog novelty evidence is incremental-evidence/primary-table-growth-6-20261020/novelty/nbr-rcf-novelty.json, SHA-256 b2c7fe2427e9e9dd01b477a495580747396d726a6e9636e7241e75356f931573. It covers all strings in 1118 identities, 21 grades, 1118 states/properties and 24 accepted computed records. Existing NBR REF has mCF=0; a standalone Toray carbon-fiber identity is not an NBR composite. This is absence from the frozen catalog, not a global novelty claim.

## Reproducible candidate preparation

packet-spec.json contains one shared-context specification with explicit identities, links, recipes, units, statistics and source limitations. The six identities have authored English, Chinese, Japanese and German display names that retain recycled milled fiber and the original phr loading. Translations are machine-assisted; native-language review is not claimed. The existing compiler is unchanged.

From the repository root:
python scripts/prepare_formulation_packet.py --spec experimental/material-batches/tamas-benyei-nbr-rcf-20261020/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/tamas-benyei-nbr-rcf-20261020/prepared-packet.json

preparation-receipt.json records the actual native immutable first creation and one identical repeat, command, exit status, output hashes and unchanged modification time. Generator/contract validation is not a product test or formal scientific admission. Runtime integration, scoped tests, package checks and parent review remain separate.

The initial English-fallback candidate and its successful Created/Unchanged receipt were preserved byte-for-byte outside the repository under incremental-evidence/primary-table-growth-6-20261020/candidate-preparation/english-fallback-superseded/. Only display names and their translation note were revised before final preparation; all scientific fields and the frozen source review remain unchanged.
