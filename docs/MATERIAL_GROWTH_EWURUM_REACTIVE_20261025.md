# Ewurum reactive PBS/lignin runtime integration

This local experimental append uses the corrected candidate reviewed at
`29a33009d763c0ef52943c1bce28e24c436c74ac`. Its candidate input catalogs
remain bound to `8ccd217599fd462d13d7435bdfb02a0825e4eacd`; their bytes are
identical at the reviewed candidate. The catalog-only append commit is
`e6d39e39184ab333045ae3ae2d001ab6b41bd53f`.

Four source-defined R10/R20/R30/R45 reactive PBS/lignin formulations add four
composite identities, four injection-molded states and four measured Young's
moduli. Grades and source counts do not increase. The existing
`ewurum_mcdonald_2025_pbs_lignin` source is reused byte-for-byte, as are all old
catalog objects, their order and metadata. Its six previous property records
remain distinct from the four added records. The same packet can be reapplied
without a new identity or changed graph. The local append is subject to final
implementation review and is not a main release or independent scientific
approval.

| Category | Before source-qualified identities | Local runtime identities | Gap to 1000 |
| --- | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 0 |
| Metal | 32 | 32 | 968 |
| Inorganic | 59 | 59 | 941 |
| Polymer | 30 | 30 | 970 |
| Composite | 33 | 37 | 963 |

The graph contains 1168 source-qualified identities, 31 grades, 1169 states,
1180 properties and 128 sources. The unchanged 24 reviewed computed
composition records give an experimental project total of 1192. The 62
unadmitted computed examples remain excluded. Published main remains 1081.
No new family membership or property propagation is inferred from constituents.

## Source and measurement scope

Nnaemeka Ewurum and Armando G. McDonald, *Lignin Reinforcement in Polybutylene
Succinate Copolymers*, Polymers 2025, 17, 194,
[DOI 10.3390/polym17020194](https://doi.org/10.3390/polym17020194), Table 6
(PDF p. 12), report the following tensile Young's moduli as mean plus or minus
standard deviation. There are ten tensile replicates, not ten known production
batches.

| Formulation | Lignin nominal loading, total polymer mass | Modulus, MPa | SD, MPa | Tukey group |
| --- | ---: | ---: | ---: | --- |
| R10 | 10 wt% | 751 | 40 | b′ |
| R20 | 20 wt% | 716 | 49 | b′ |
| R30 | 30 wt% | 910 | 85 | b |
| R45 | 45 wt% | 1256 | 162 | a |

These DCP-added source formulations differ from the previously catalogued
B-series physical blends. Reported DCP addition is 0.25 wt%, but its mass
denominator, final residue, final chemistry and network architecture remain
unresolved. No final crosslink density or measured final composition is claimed.
The inconsistent FZ91PM/FZ91PB PBS grade designation remains unresolved; no
grade is created. R0 and other unselected results are excluded.

Section 2.9 specifies injection-molded microtensile specimens, 1 mm/min,
Instron 5500R-1132, Bluehill v3.3 and an Epsilon 3542 extensometer. Reference
[32] explicitly cites ASTM D1708-18 (2018). This is the source-cited edition;
independent standard compliance is unverified. Dimensions, conditioning or
fit windows are not inferred from the standard. Tensile temperature, pressure,
relative humidity, post-molding conditioning and modulus fit window remain
unknown.

The reactive precursor treatment is 24 h in a fume hood and then 80 °C under
vacuum for 12 h. Tensile preparation includes 140 °C extrusion, Dynisco LMM at
100 rpm for 10 min at 140 °C, followed by injection molding. The separately
described 120 °C hot-pressed material is not the tensile dog-bone state. Table 1
gel fractions are contextual evidence measured on hot-pressed material under
section 2.4; they are not appended properties or transferred to the tensile
specimens.

The article is CC BY 4.0. Attribution and the transcription/curation notice
remain explicit. The producer reused a retained official publisher PDF,
3211541 bytes, SHA-256
`766d17f0e92c7e93cd57a3a5e97dddff0cb66a84bba6bf9118fbd0796d4c2e6f`.
Independent source review corroborated indexed official text; it did not
independently verify current raw PDF bytes. No raw PDF or screenshots are
distributed. The finite 22-input identity audit is not global chemical
equivalence proof, scientific replication or engineering qualification.

## Preserved evidence and validation boundaries

The nine candidate evidence files remain immutable, including their original
candidate-only zero-admission report and correction history. The separate
integration manifest/report describe this later append. Original ASTM-edition
and gel-state defects remain visible in prior history, with rejection evidence
retained by the corrected candidate.

General core partition CI, its 1887 root IDs, historical fixtures and the
70-method replay inventory are preserved. New scoped checks execute explicitly
outside frozen root discovery. Exact historical adapters preserve old file
images and assertions; they do not relax current runtime validation. The full
Bruns, Tarasov, Kapoor and family historical modules are included in scoped
validation to cover nested query inventory and registry boundaries.

Executed, failed, skipped and unrun coverage is recorded separately in
[INTEGRATION_VALIDATION.md](../experimental/material-batches/ewurum-reactive-20261025/INTEGRATION_VALIDATION.md).
No main merge, deployment, DOI registration or new authentication is included.
