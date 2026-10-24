# Tian 2023 nano-Ti composite candidates

This review-only packet is based on exact published commit
`5a9a85c573f590d206cddb4cb7c085f334a0fbc0`. It proposes two
study-qualified nominal metal-matrix composite formulations. It makes **zero
runtime admissions** and changes no existing catalog, source registry, package,
workflow or count document. The parked historical-replay optimization is not
included.

The experimental project remains **1183 = 1159 source-qualified identities +
24 existing computed records**: natural 1010, metal 32, inorganic 59, polymer 30
and composite 28. Main remains 1081. The 62 unadmitted computed examples remain
excluded. A future accepted append would add two composite identities, two
states, two measured density properties and one source, with zero grades. The
compiler's hypothetical after-count of 1161 source-qualified identities is not
an actual catalog count or a publication claim.

## Selected facts

Wei Tian, Pengfei Gao, Shengli Han, Xiaohong Chen, Fuwei Zhang, Yuhui Zhang,
Tiegang Luo and Kaihong Zheng (2023), *Effect of Nano-Ti Particles on
Microstructure and Mechanical Properties of Mg-3Al-1Zn Matrix Composites*,
Materials 16(6), 2407, [DOI 10.3390/ma16062407](https://doi.org/10.3390/ma16062407).

| Literal Table 2 label | Nominal nano-Ti loading from methods | Actual Density (g/cm3) |
| --- | --- | --- |
| 0.5 wt% Ti | 0.5 wt% | 1.7425 |
| 1 wt Ti | 1 wt% | 1.7442 |

The second table label omits the percent symbol. It is preserved literally;
sections 2.1 and 2.2 establish the separate nominal-loading qualification.
These are Mg-3Al-1Zn (AZ31) matrix composites in the as-extruded state, not
analyzed final compositions or certified grades. Extrusion and measurement
states do not create extra identities.

Section 2.2 reports a digital densimeter. Density temperature, pressure,
humidity, specimen count, repetitions, aggregation, uncertainty, density basis
and porosity are unknown. The tensile sample count of three and tensile room
temperature from section 2.3 are not assigned to density. Theoretical density,
tensile data and the unreinforced comparator are excluded. No porosity is
calculated from the actual/theoretical difference.

## Source and identity evidence

The [official Europe PMC XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10054318/fullTextXML),
archive version `PMC10054318.1`, was read and hashed: 143168 bytes, SHA-256
`80b9020e8a4878adf439977478551214b1130982331d81a17fc85a072f2ac598`.
It corroborates the article identity, selected cells, methods and article-specific
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) notice.

A separate source reviewer visually checked pages 1 and 4 of the
publisher-formatted [mirror PDF](https://pdfs.semanticscholar.org/f581/6846789d5f4cf89555778ceca9a2a6435347.pdf).
Its locally verified 5497847 bytes and MD5
`aea07249f6eb98a284067ea7a466012a` match the official archive PDF manifest.
Its SHA-256 is
`8df98d0b465e5bef857d9eaa0ff0969e0c22b4f35aa5a7c64e6e59150b08afad`.
Direct primary-host PDF download and primary-host SHA-256 byte equivalence
remain unverified. Manifest corroboration is not described as that verification.

Copyright 2023 by the authors; licensee MDPI, Basel, Switzerland. Changes:
selected factual values and qualifications were transcribed into structured
candidate records. Attribution and license links are retained; no endorsement
is implied. No raw PDF, XML full text, images or private evidence assets are
included.

The reproducible finite identity review reads 22 exact baseline Git objects,
covering 14111 label occurrences, 8241 normalized labels and all 32 metal and
28 composite identities. It preserves contextual hits and the computed and
relationship inventories. No matching reinforced identity or candidate DOI was
found within this scope. `mat_chen2023_az31` remains a different-study
unreinforced comparator; no same-lot claim or new comparator identity is made.
This finite screen is not proof of global chemical uniqueness.

## Reproduce without source assets or network access

From the exact baseline checkout with this candidate commit applied, in Linux
or PowerShell:

```text
python -X utf8 experimental/material-batches/tian-nano-ti-composites-20261024/build_identity_review.py --check
python -X utf8 scripts/prepare_formulation_packet.py --spec experimental/material-batches/tian-nano-ti-composites-20261024/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/tian-nano-ti-composites-20261024/prepared-packet.json
python -X utf8 -m unittest discover -s tests -p test_tian_nano_ti_packet.py -v
git diff --check
```

Repeat generation verifies identical bytes without modifying the output mtime;
different existing bytes are refused. Baseline drift is rejected.
`handoff_ready` means the compiler's explicit source/identity gates passed. It
does not grant scientific approval, runtime admission or publication authority.
Independent scientific review and raw-data reanalysis remain false. Parent
candidate review is required before a separate runtime implementation. See
`source-review.json`, `identity-review.json`, `preparation-receipt.json` and
`VALIDATION.md` for the evidence and actual validation boundaries.
