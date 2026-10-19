# B45 PBS/lignin simple-blend candidate

This packet proposes one composite identity, one injection-molded tensile state
and one selected Young's-modulus property against experimental baseline
`a592c89ede0dcced22579e56fc68b6fab4c55f49`. It adds no grade or source.
Candidate preparation contributes **zero formal admissions** and does not modify
runtime catalogs or formal-component pins. The baseline has 1103 formal identities
(1079 source-qualified plus 24 reviewed computed); 62 computed examples remain
excluded. The proposed category increment is one composite, subject to integration.

## Selected identity and measured property

**B45** is PBS with **45 wt.% Indulin AT softwood kraft lignin**, where the loading
is relative to total polymer mass (PDF p.3, sections 2.1-2.3). The paper records
separately extruded 50 g formulations and distinguishes Bxx simple blends from
DCP-reactive Rxx. B45 differs in composition from existing B10, B20 and B30;
repeated specimens, processing conditions and translated labels are not new
identities. The unresolved BioPBS FZ91PM/FZ91PB designation remains explicit,
with `grade_id: null`. No single grade or complete chemical-purity assay is inferred.

PDF p.12, Table 6, B45 row, Young's Modulus column reports **1206 +/- 132 MPa**.
The center is the reported mean and 132 MPa is the reported standard deviation.
Table 6 footnote a gives mean/SD semantics and the rounding convention; the
superscript `a` on the numerical result is a Tukey grouping, not an uncertainty
code. No SD-to-SE/CI conversion, interpolation or derived endpoints are used.

Section 2.9 (p.5) specifies **ten tensile replicates**, ASTM D1708, an Instron
5500R-1132 with Bluehill v3.3, an Epsilon model 3542 extensometer and **1 mm/min**
crosshead speed. The selected specimens are injection-molded microtensile
dog-bones. Section 2.3 describes 140 C strand extrusion, pelletization, Dynisco
LMM compounding at 100 rpm for 10 minutes at 140 C, then injection molding.
The separate hot-pressed-disc route and DCP/acetone pretreatment are excluded
from this simple-blend tensile state. Test temperature, relative humidity,
post-molding conditioning and numerical modulus fit window/estimator remain
unknown. The processing temperature is not a tensile-test temperature.

## Source inspection and reuse

Nnaemeka Ewurum and Armando G. McDonald (2025), *Lignin Reinforcement in
Polybutylene Succinate Copolymers*, Polymers 17, 194,
[DOI 10.3390/polym17020194](https://doi.org/10.3390/polym17020194).
The [registered publisher PDF](https://mdpi-res.com/d_attachment/polymers/polymers-17-00194/article_deploy/polymers-17-00194.pdf)
has SHA-256 `766d17f0e92c7e93cd57a3a5e97dddff0cb66a84bba6bf9118fbd0796d4c2e6f`
and 3,211,541 bytes. The retained PDF hash was rechecked on 2026-10-19, and
retained text and page images for pages 1, 3, 5 and 12 were inspected.
The current public article-page request returned HTTP 429 and was not retried;
this packet does not claim a successful fresh full-text retrieval. The reused
source record remains unchanged; new inspection scope belongs to this packet
and the new property, not the historical source record.

Page 1 explicitly states [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The selected Table 6 result has no separate third-party credit. Attribution,
license and original curation changes are recorded in `review.json`.
Only selected factual transcription and authored metadata are included; no PDF,
full table, figure, screenshot, extracted full text or raw source asset is bundled
or relicensed under the project's code license. All four required locale slots
use English fallback labels without claiming native-language review.

## Integration boundary

The packet reuses the existing schemas and `merge_material_catalogs` contract.
It contains no runtime append or integration manifest. Experimental integration
and experimental branch publication are authorized and coordinated by the parent
after validation; main merge/release approval remains pending. DOI registration
and public deployment remain deferred. No tests were run in preparing this packet.

The companion fixture is
`tests/fixtures/pbs_lignin45_source_transcription_20261019.json`; it records selected
facts and limitations for the parent's focused validation. Source transcription
is not scientific approval, replication, raw-data reanalysis or engineering
qualification. `independent_scientific_review` and `raw_data_reanalysis` remain
false. The selected property is catalog-only, non-universal and non-allowable.
