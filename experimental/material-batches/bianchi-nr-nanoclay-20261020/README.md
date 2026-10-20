# Bianchi NR/nanoclay composite formulations

This review-only batch proposes six source-qualified composite identities, six states and six mass-density properties. It adds no grades or sources and admits zero formal materials. The 24 accepted computed compositions and 62 unadmitted examples are unchanged.

The baseline is 8981840519f611e62490ce4e9a614381201fe7e3: 1112 core / 1136 project identities, 13 composites, 21 grades and 116 sources. Successful integration would give 1118 core / 1142 project / 19 composites. These are proposed catalog deltas; this directory does not edit runtime catalogs.

## Six original density facts

| Table 8 formulation | Clay input, phr | Table 1 density, g/cm³ |
| --- | --- | --- |
| NR_1MMT | MMT 1.0 | 0.960 ± 0.003 |
| NR_3MMT | MMT 3.0 | 0.973 ± 0.001 |
| NR_5MMT | MMT 5.0 | 0.981 ± 0.005 |
| NR_1O-MMT | O-MMT 1.0 | 0.959 ± 0.001 |
| NR_3O-MMT | O-MMT 3.0 | 0.966 ± 0.001 |
| NR_5O-MMT | O-MMT 5.0 | 0.971 ± 0.003 |

Table 8 on PDF p.17 explicitly defines phr as parts per hundred rubber. Every selected formulation uses SMR 10 natural rubber 100.0, sulfur 1.5, ZnO 5.0, stearic acid 2.0 and ZDBC 0.7 phr. It then adds one of the two clay inputs at 1.0, 3.0 or 5.0 phr, with a dash for the other clay column. No normalization to total-composite percentages is performed.

Section 3.1 on p.16 identifies MMT as natural montmorillonite (Cloisite Na+) and O-MMT as organo-modified montmorillonite (Cloisite 20A). The authors discuss organic amine groups in the latter on pp.3–4. Thus the two families differ in the input composition as well as the three stated loadings, rather than only specimen, branding or final treatment. Exact modifier chemistry and complete mineral or final-composite stoichiometry are not established within the selected article-authored evidence. The modifier fraction remains unspecified. Table 7 contains a producer-derived modifier drawing that is outside this selection; this is not a claim that the complete PDF lacks a structure drawing. Input trade names do not create a finished-composite grade, and no source grade is transferred from the existing unfilled NR identity.

Table 1 on p.4 actually prints NR_3MMsT, while Table 8 prints NR_3MMT. The density value 0.973 ± 0.001 is explicitly linked to the unique 3 phr natural-MMT recipe using §3.2 nomenclature. The printed typo remains in the property locator, state alias and source_discrepancies; it is not silently corrected or counted as another material.

## Method and limits

Section 3.3.1 on p.17 reports ASTM D792 Archimedes weighing in air and methanol with a Mettler ME-33340 kit. Three specimens per composition were tested. The temperature is only “room temperature”; no numerical temperature is assigned. Density-specific conditioning, ambient humidity, test pressure and ASTM edition are not established.

The density center and ± amplitude are preserved as reported_summary, reported_value and reported_plus_minus_unspecified. The source does not establish arithmetic mean, SD, SE or a confidence interval for these density cells. The p.19 mean/SD statement explicitly covers mechanical properties. Four crosslinking-density specimens and their acetone/toluene pretreatment are a different method and are not imported.

The density basis stays not_stated: Archimedes does not establish a source-unstated true, skeletal, apparent or bulk classification. Nonfoamed sheet preparation does not prove zero porosity. Processing temperatures and the 120 °C / 3 bar cure are not density-test conditions; cure time is unspecified. All entries are catalog_only, non-universal and non-allowable, with independent_scientific_review=false and raw_data_reanalysis=false. No mechanical or elastocaloric performance is admitted through these density rows.

## Source, rights and independent checks

Bianchi, M.; Fambri, L.; Bortolotti, M.; Pegoretti, A.; Dorigato, A. Elastocaloric Performance of Natural Rubber: The Role of Nanoclay Addition. Molecules 2025, 30, 3035.
DOI: https://doi.org/10.3390/molecules30143035
Registered publisher PDF: https://www.mdpi.com/1420-3049/30/14/3035/pdf

The 23-page original PDF has SHA-256 2e729bb58b361568d27ab772ec1c031648cb6a858f58a6e4ece9ce45b74c3ea2 and 3,263,494 bytes. One bounded GET from the publisher's mdpi-res delivery endpoint returned HTTP 200 with exactly the already-frozen hash. No second PDF, retry or metadata query was used. Retained source assets and request evidence remain outside the repository under incremental-evidence/primary-table-growth-5-20261020/source-research/.

Article p.1 grants CC BY 4.0. The full existing source bianchi_2025_nr_nanoclay is reused unchanged, canonical SHA-256 16404406aa2c9a98f15dd099fec5747f6dea02250b5c817035b162b59a1f7865. Attribution applies to selected original Table 1 density facts, Table 8 recipes and author-authored methods/qualifications. Table 7 explicitly attributes its information to producers: its filler densities, spacings, modifier structure and quantitative supplier claims are excluded. No raw PDF, screenshot, complete source table, figure or source dump is published or relicensed under project MIT.

Exact selected locators are p.1 rights notice; pp.3–4 author discussion of organic input composition; p.4 Table 1 six Density (g/cm³) cells; p.16 §§3.1–3.2 material inputs and processing; p.17 Table 8 and §3.3.1; p.19 mechanical statistical scope. The separate reviewer checked the original PDF and rendered tables, including the typo and composition distinction. source-review.json is frozen independent transcription evidence, not scientific peer review, experimental replication, raw-data reanalysis or legal clearance.

Independent catalog novelty evidence is incremental-evidence/primary-table-growth-5-20261020/novelty/nr-nanoclay-novelty.json, SHA-256 cd159fd1796d8ee757c055b52b68d8936c5a993a6b1f6d44c227d2734475cefc. The scan covers all strings in 1112 identities, 21 grades, 1112 states/properties and the 24 accepted computed records. The sole related NR baseline explicitly contains no nanoclay. Absence from this frozen catalog is not a claim of worldwide novelty.

## Reproducible review packet

packet-spec.json uses shared identity, state and property contexts with explicit per-formulation values and links. Names use a declared English fallback in all four required language slots; no native translation review is claimed. The unchanged compiler validates the complete scientific graph, exact baseline hashes, frozen source and identity crosswalk. It does not infer chemistry, statistics, units, rights or scientific approval.

From the repository root:
python scripts/prepare_formulation_packet.py --spec experimental/material-batches/bianchi-nr-nanoclay-20261020/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/bianchi-nr-nanoclay-20261020/prepared-packet.json

preparation-receipt.json records the actual first immutable creation and identical repeat, exit codes, stdout, SHA-256 and unchanged modification time. This verifies generation and contracts; it is not a product test or scientific admission. Runtime integration, scoped testing, packaging and parent approval remain separate.
