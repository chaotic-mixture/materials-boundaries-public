# Mtibe PBS/PBAT-lignosulphonate-ZnO hybrid formulations

This review-only batch proposes exactly three composite identities, three states and three tensile-modulus properties. It adds zero grades and zero sources. Prepared packets admit zero formal materials. The 24 accepted computed compositions and 62 unadmitted examples are unchanged.

The pinned baseline is a5cc3f6c47954033db5de7f50220d182cfcff459: 1109 core identities, 1133 project identities, 10 composite identities, 21 grades and 116 sources. Successful integration would give 1112 core / 1136 project / 13 composites. These are planned catalog deltas, not a claim that this candidate directory changes runtime data.

## Selected original facts

| Source Table 2 formulation | Table 3 tensile modulus (MPa) | Specimens |
| --- | --- | --- |
| 95/5/1.5 | 261.88 ± 14.78 | 5 |
| 90/10/1.5 | 304.52 ± 5.22 | 5 |
| 85/15/1.5 | 347.44 ± 16.92 | 5 |

Table 2 columns are (PBS/PBAT), lignin and ZnO. The internal matrix ratio is PBS/PBAT 70/30. The source calls the lignosulphonate loadings 5, 10 and 15 wt.% and ZnO 1.5 wt.%, but the entries total 101.5 and the ZnO denominator is unspecified. The internal 70/30 ratio basis is also unspecified. These source-qualified formulation labels are retained without normalization or an invented complete mass-fraction formula. The explicit matrix/lignosulphonate changes distinguish three compositions; supplier, specimen, processing and measurement condition do not create extra identities.

The constituent polymers are Bio PBS FZ 91 and Eco flex C1200 (Table 1, p.3), and SAPPI supplied lignosulphonate (§2.1, p.2). This is not the separately cataloged Ewurum kraft-lignin/PBS series. Table 3 omits ZnO in its abbreviated row labels; Table 2 and §§2.3, 2.6.2 and 3.2 connect these three rows to the ZnO-containing hybrid group. This linkage is explicit curation, not an assertion that the abbreviated label alone specifies every constituent.

The source reports Instron tensile testing to ASTM D638 at 25 °C, after 48 h conditioning at 25 °C (§2.6.2, p.5). Five specimens were tested for each group. The table does not identify the central estimator or the meaning of ±: the packet uses reported_summary, reported_value and reported_plus_minus_unspecified, not mean/SD. Test and conditioning humidity, crosshead speed, gauge geometry, numerical modulus-fit interval and ASTM edition remain unknown. Preparation temperatures of 80 °C and 120–145 °C are not test temperatures. Catalog entries do not establish biomedical certification or clinical suitability.

## Evidence and rights

Mtibe et al., Fabrication of a Polybutylene Succinate (PBS)/Polybutylene Adipate-Co-Terephthalate (PBAT)-Based Hybrid System Reinforced with Lignin and Zinc Nanoparticles for Potential Biomedical Applications, Polymers 2022, 14, 5065.
DOI: https://doi.org/10.3390/polym14235065
Original PDF: https://mdpi-res.com/d_attachment/polymers/polymers-14-05065/article_deploy/polymers-14-05065.pdf

The original PDF is 1,922,433 bytes / 14 pages; SHA-256 fa72f3441329d8db6348926906817ebac7b3bd7077a90e836f75f8ecdb087287. One bounded GET returned HTTP 200 and exactly matched the previously frozen PDF hash. No retry, metadata request, second PDF or supplementary retrieval was used. The private retained path and download receipt are under incremental-evidence/primary-table-growth-4-20261019/source-research/.

Article p.1 gives author copyright and CC BY 4.0. This batch reuses source mtibe_2022_pbs_pbat_lignin_zno without modifying its full canonical record (SHA-256 dc976befcdcb03bc40cba9f6b4921f5f10666f7a67b2cd094d25edcc7a80f9f0). Existing source notes describe the earlier unfilled selection; this packet and source-review.json separately record the additional hybrid-row inspection. Selected authored facts and methods receive attribution; structured curation and explicit English fallback names are adaptations. No PDF, image, complete table, figure, supplementary asset or third-party comparison dataset is published or relicensed under project MIT.

Precise locators: p.2 §2.1; p.3 Tables 1–2 and §§2.2–2.3; p.5 §2.6.2; pp.6–7 §3.2 and p.7 Table 3, the 95/5, 90/10 and 85/15 rows under Tensile Modulus (MPa). An independent source-transcription reviewer checked the original PDF, including table images. This is not independent scientific peer review, raw-data reanalysis, experimental replication or legal clearance.

## Identity and generation boundary

Independent novelty evidence: incremental-evidence/primary-table-growth-4-20261019/novelty/mtibe-hybrid-novelty.json, SHA-256 fb835825f4cafb1c657e85a48cae8e72e97452d4cf6a2054cc6b80db3b06847d. It examines all strings in the 1109-identity catalog, states/properties/grades, relevant formulation families and the scope of 24 accepted computed compositions. Same-source PBAT and explicitly unfilled 100/0/0 PBS/PBAT are already present. Shared constituent names or ZnO additives in unrelated elastomers are not identical composite formulations. The conclusion is absence from this frozen catalog, not worldwide novelty.

The single packet-spec.json uses shared identity, state and property contexts. Its explicit identities, links, units, values, conditions and crosswalk are expanded by the unchanged scripts/prepare_formulation_packet.py. No per-material generator code or runtime catalog edit is introduced. Baseline raw hashes, complete frozen source record and review hashes are bound into the packet. Four language-name slots use an explicitly declared English fallback.

Generate from the repository root:
python scripts/prepare_formulation_packet.py --spec experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/prepared-packet.json

preparation-receipt.json records the actual first immutable creation and identical repeat, exit codes, stdout, SHA-256 and unchanged modification time. This is generator and contract validation, not a product test or scientific admission. Runtime integration, scoped tests, packaging and parent review remain separate.
