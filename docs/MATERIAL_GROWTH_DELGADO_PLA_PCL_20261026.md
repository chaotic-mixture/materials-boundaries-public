# Delgado 2020 PLA/PCL runtime integration

This local experimental append uses the seven-formulation candidate independently
reviewed at `73a5d872c210bbde5b3c0548d710869e87626691`. Its finite identity audit
remains bound to `437950c414ea340eda340babe7b63dee9fcee535`. The nine original
candidate evidence files remain unchanged, including their candidate-only zero
admission report. The separate integration manifest and report describe this
later exact append. Final implementation review and experimental publication
remain pending; this is not a main release or independent scientific replication.

Seven source-defined nominal PLA/PCL mass-ratio formulations add seven polymer
identities, seven injection-molded states, seven measured Young's moduli and one
source. There are no new grades. All old catalog objects, ordering and metadata
remain exact. The unchanged 24 reviewed computed records are separate; the
62 unadmitted computed examples remain excluded.

| Category | Previous source-qualified identities | Local runtime identities | Gap to 1000 |
| --- | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 0 |
| Metal | 32 | 32 | 968 |
| Inorganic | 59 | 59 | 941 |
| Polymer | 30 | 37 | 963 |
| Composite | 37 | 37 | 963 |

The local graph contains 1175 source-qualified identities, 31 grades, 1176 states,
1187 reference properties and 129 sources. With the unchanged 24 reviewed
computed records, the local experimental project total is 1199. The last
published experimental baseline remains 1192 until this implementation is
reviewed and its remote publication is verified. Published main remains 1081.

## Source and measurement scope

Marc Delgado-Aguilar, Rita Puig, Ilija Sazdovski and Pere Fullana-i-Palmer,
*Polylactic Acid/Polycaprolactone Blends: On the Path to Circular Economy,
Substituting Single-Use Commodity Plastic Products*, Materials 2020, 13, 2655,
[DOI 10.3390/ma13112655](https://doi.org/10.3390/ma13112655).
[Official PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC7321633/) and
[official full-text XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7321633/fullTextXML)
supply the inspected evidence. Article-specific CC BY 4.0 applies; attribution
and the transcription/curation notice are retained.

Table 1 gives nominal PLA/PCL mass recipes. Table 2 gives experimental modulus
and variability, identified as standard deviation by section 3.2 after Eq. (6).
The source does not state central aggregation or sample count. No mean, SEM,
confidence interval or independent specimen count is inferred.

| Source label / nominal PLA:PCL wt% | Calculated V_PCL join | Modulus, GPa | SD, GPa |
| --- | ---: | ---: | ---: |
| B95/5 | 0.054 | 3.70 | 0.13 |
| B90/10 | 0.108 | 3.60 | 0.26 |
| B85/15 | 0.162 | 3.38 | 0.27 |
| B80/20 | 0.214 | 3.20 | 0.19 |
| B60/40 | 0.421 | 2.55 | 0.09 |
| B40/60 | 0.621 | 1.86 | 0.11 |
| B20/80 | 0.814 | 1.13 | 0.05 |

GPa is preserved without conversion. SD is represented as a reported measure;
summary statistic and reporting basis remain `not_stated`. Calculated volume
fraction is only the source table join, not an admitted measured property.
Nominal ratios are not validated final composition assays. Commercial
ingredient labels do not create finished-blend grades or purity claims.

Section 2.4 cites ISO 527-1:2012, Instron 1122, a 5-kN load cell, 2 mm/min and
115-mm clamp separation; clamp separation is not asserted to be gauge length.
Temperature, pressure, relative humidity, conditioning, specimen dimensions,
sample count, strain estimator, modulus fit interval and orientation remain
unknown. Independent standards compliance is unverified.

Sections 2.1-2.3 describe drying at 60 degrees C to constant weight, mixing at
190 degrees C and 80 rpm to constant torque, knife milling with 10-mm mesh,
storage at 60 degrees C, five molding zones of 175/180/185/185/190 degrees C
and a reported pressure range of 330-600 bar. Section 3.1 says both molding
temperature and pressure varied with MFI. No exact per-formulation molding
settings are inferred. No deliberately added coupling agent is reported; this
does not establish that all commercial additives are absent.

Neat endpoints, modeled values, all other properties and supplementary
commercial comparisons are excluded. The study's analytic description of PCL
as a filler does not establish an externally reinforced composite. No new
family membership, inverse scientific relation or property propagation follows
from ingredients.

## Evidence boundaries and validation

The producer inspected official HTML and XML. The PDF link presented CAPTCHA,
which was not bypassed: PDF bytes, pages and equivalence remain unverified.
The independent candidate review verified official text, rights and statistics,
but did not independently repeat raw-source byte hashes or PDF inspection.
Raw HTML/XML/PDF and screenshots are not distributed.

The frozen 22-input identity review includes all 67 existing polymer/composite
identities. It does not prove global uniqueness or the absence of PCL from
incompletely disclosed existing PLA products. Study-qualified formulations and
bounded overlap notes remain explicit.

Existing general partition CI, all historical fixtures, the 1887 root IDs and
70 replay IDs are preserved. New scoped tests execute explicitly outside root
discovery. Finite exact historical projections preserve original assertions
and reject unknown images; no cross-call cache is introduced.

Executed, failed, skipped and unrun coverage is recorded separately in
[the integration validation report](../experimental/material-batches/delgado-pla-pcl-20261026/INTEGRATION_VALIDATION.md). No main merge, deployment, DOI registration
or new authentication is included.

