# Two ratio-qualified rigid polyurethane formulations

This review-only packet selects Ivdre et al. (2024) formulations **LPO-2** and
**SPO-3** against baseline `2509ee231edb62872ed323e8346895bd55c36c92`.
It proposes two polymer identities, two source-scoped states and two measured
apparent-density references, with no grades or source additions. Preparation
does not change runtime catalogs or admit materials; `formal_admitted_delta`
remains zero. Both independent scientific-review and raw-reanalysis flags remain
false.

## Composition-based selection

LPO-2 uses Lupranol 3300/3422 inputs of **66/34 g**, compared with the existing
LPO-1 **40/60 g**. SPO-3 uses SA-C_TOFA(50:50)/TMP and
SA-E_ETOFA(50:50)/TMP inputs of **40/60 g**, compared with the existing SPO-2
**67/33 g**. The principal reactive polyol proportions support the new
formulation distinction; product names, study labels and catalyst/blowing-agent
changes alone do not establish additional identities. The `50:50` strings
describe precursor feeds, not the final foam's principal-polyol ratio.

The current 1090 core identities include only LPO-1 and SPO-2 as corresponding
PUR formulations; the unchanged 24 accepted computed compositions contain no
polymer formulation. The 62 computed examples remain unadmitted. This packet
does not infer a final cured-network molecular formula, elemental composition,
chemical purity or equivalence among all polyurethane foams. Both codes are
study formulation labels, not certified grades.

All Table 9 masses below are formulation inputs in grams:

| Ingredient | LPO-2 | SPO-3 |
| --- | ---: | ---: |
| Lupranol 3300 | 66 | — |
| Lupranol 3422 | 34 | — |
| SA-C_TOFA(50:50)/TMP | — | 40 |
| SA-E_ETOFA(50:50)/TMP | — | 60 |
| Total water | 2.0 | 0.74 |
| Opteon 1100 | 14.8 | 23.6 |
| Polycat NP10 | 4 | 3.03 |
| PC CAT TKA 30 | 0.5 | 0.5 |
| L-6915 | 2.5 | 2.5 |
| TCPP | 24.5 | 21.5 |
| pMDI | 158 | 117 |
| **Table 10 apparent density, kg/m³** | **43.5** | **43.2** |

Dashes identify the table's absent-family entries; no final-composition assay
is inferred. Table 9 footnotes state that TCPP was adjusted to 8 wt.% of total
foam mass and pMDI for NCO/OH = 1.2. These stated design bases are retained
without recomputing or repairing the rounded input table. Section 2.4 identifies
pMDI as Desmodur 44 V20 L and the surfactant as Niax Silicone L-6915. Table 9
uses `Polycat NP10`, while section 2.4 uses `PC CAT NP10`; the naming difference
does not establish an independently certified supplier equivalence.

## Exact source and conditions

Ivdre et al. (2024), *Rigid Polyurethane Foams' Development and Optimization from
Polyols Based on Depolymerized Suberin and Tall Oil Fatty Acids*, **Polymers**
16(7), 942, published 2024-03-29.
[DOI 10.3390/polym16070942](https://doi.org/10.3390/polym16070942),
[primary XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11013755/fullTextXML).
The retained XML is 184,537 bytes, SHA-256
`4e0c1a91a9ae26d814576961a3805f9371b46498d4861fb578e7a413bb4c726d`.
This is reuse of inspected retained bytes, not a new download.

- Table 9, XML ID `polymers-16-00942-t009`, LPO-2 and SPO-3 columns, all
  ingredient rows and footnotes: formulations.
- Table 10, XML ID `polymers-16-00942-t010`, `Apparent density, kg/m3` row,
  selected columns: **43.5** and **43.2 kg/m³**. No mean or density uncertainty
  is assigned to these reported values.
- Section 2.4, `sec2dot4-polymers-16-00942`: petroleum-based LP and synthesized
  suberin/tall-oil-based SP polyol families and other inputs.
- Section 2.7, `sec2dot7-polymers-16-00942`: approximately 2 min mixing at
  2000 rpm, physical blowing agent added last and mixed approximately 1 min,
  pMDI mixed 10 s, larger 30 × 30 × 10 cm mold, and 24 h room-temperature cure.
- Section 2.8, `sec2dot8-polymers-16-00942`, density-method paragraph:
  **ISO 845:2006**. Source-reported standard compliance is not independently
  certified; no unreported subprocedure is supplied.
- Section 3.4, `sec3dot4-polymers-16-00942`: experimental characterization of
  the optimized formulations, distinguished from modeled targets.

Density-test temperature, humidity, pressure, specimen dimensions, sample count,
aggregation and uncertainty remain unreported. Mold dimensions are not specimen
dimensions. Room-temperature curing is not a density-test temperature. Do not
borrow MRSM cup-test n=3, the six compression cylinders, TGA replicates or
thermal-conductivity plate temperatures. The 45 kg/m³ optimization target and
40 kg/m³ compression-normalization value are not selected density measurements.
Closed-cell contents of 93 and 95 vol.% are retained as source state context;
they are not total void fractions or additional numerical property records.

## Historical scope and excluded labels

The exact existing source object `ivdre_2024_lpo_rigid_pur` is frozen, including
its prior scope text:

> Only the optimized Lupranol-based LPO-1 rigid PUR formulation characterized in this study. Lupranol 3300/3422 polyether polyols and polymeric MDI distinguish this formulation; it is not the suberin-based SPO series despite the article title. LPO-1 is a study formulation, not a certified product grade. Do not count LPO-2/LPO-3 as extra identities or substitute modeled target/normalization densities.

The [specification](packet-spec.json) also retains the exact old LPO-1 and SPO-2
identity scopes in its review record. Those historical selections are not
silently expanded or rewritten. This separate review supplies the Table 9
principal-reactive-polyol-ratio evidence for precisely two new formulations;
the old labels alone do not authorize these additions.

**LPO-3 is excluded:** it shares LPO-1's 40/60 principal-polyol ratio.
**SPO-1 is excluded:** it shares SPO-3's 40/60 principal-polyol ratio and its
Table 10 density **43.9 kg/m³** conflicts with section 3.4's stated overall
range **40.7–43.5 kg/m³**. The complete recipes in both pairs differ; this
conservative identity policy does not assert their chemical equivalence. The
unselected SPO-1 discrepancy is preserved without changing either source value.
LPO-2 and SPO-3 fall within the stated range, which does not establish that the
whole article is internally consistent.

## Rights and review boundary

The article permissions explicitly state author copyright 2024 and
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The selected original
Table 9/10 cells have no separate third-party credit in their captions or
footnotes. Attribution is retained; adaptations comprise selected factual
transcription and original structured metadata and qualifications. Source
numbers and units remain unchanged. No complete table, raw XML, PDF, screenshot,
figure or other source asset is bundled or relicensed as project MIT.

The exact reused source object's canonical JSON hash, including a trailing
newline, is `d97a5b38a0084d2c8dbb5d0c51b2978e032c5b68dbcf8ef232f11176533b3328`.
The [independent source transcription review](source-review.json) records actual
checks of the retained primary source; it is not scientific approval, replication
or a new rights grant. English fallback names fill all four locale slots; no
native-language review is claimed.

## Candidate compilation

```sh
python scripts/prepare_formulation_packet.py \
  --spec experimental/material-batches/pur-formulations-20261019/packet-spec.json \
  --baseline-dir /path/to/2509ee2/materials_boundaries/data \
  --output experimental/material-batches/pur-formulations-20261019/prepared-packet.json
```

The shared compiler expands explicit contexts and validates source, identity and
catalog contracts without altering the frozen baseline. Use a separate baseline
checkout after runtime integration. Machine readiness is not formal admission.
If separately reviewed and integrated, the projected core count is 1092 and
project count 1116, with polymers increasing from 16 to 18. These projections
do not claim a release or completed admission. Actual first-write and unchanged
replay results are recorded separately in the preparation receipt.

The actual [preparation receipt](preparation-receipt.json) records `Created` and
one identical `Unchanged` replay, both exit zero. The 78,468-byte
[prepared packet](prepared-packet.json) retained SHA-256
`2c5320856ba07892eac6b35d6b881bb3ab21126e801beefa2b887c77abd93be7`
and modification time across both invocations. The report has no pending machine
gates and proposes exactly two identities, two states and two properties, with
zero grade/source additions and zero formal admission. Candidate preparation ran
no product tests and made no network requests; compiler success is not reported
as a scientific test pass.
