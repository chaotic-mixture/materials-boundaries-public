# Outokumpu Core alloy modulus candidate

This review-only batch selects ten source-qualified stainless-steel alloy formulations from one already-curated manufacturer datasheet. It proposes ten identities, ten linked manufacturer grades, ten source-reference states and ten modulus values, with no new source. Grades do not add a second identity count. The compiler's formal admitted delta remains zero; runtime integration and validation are separate.

The baseline is `eee77b5033d7671bbaa2d3b4eca57c88d52fc411`: 1124 core identities plus 24 accepted computed compositions = 1148 project identities. The proposed result is 1134 core / 1158 project, with metal core 22 to 32, metal project 34 to 44, grades 21 to 31 and sources unchanged at 116. The 62 excluded computed examples remain excluded.

## Selected facts and identity scope

| Source product | Source EN / UNS | Modulus at 20 °C, GPa |
| --- | --- | --- |
| Core 304/4301 | 1.4301 / S30400 | 200 |
| Core 304LN/4311 | 1.4311 / S30453 | 200 |
| Core 305/4303 | 1.4303 / S30500 | 200 |
| Core 321/4541 | 1.4541 / S32100 | 200 |
| Core 347/4550 | 1.4550 / S34700 | 200 |
| Core 301LN/4318 | 1.4318 / S30153 | 200 |
| Core 301/4310 | 1.4310 / S30100 | 200 |
| Core 201/4372 | 1.4372 / S20100 | 200 |
| Core 201LN/4372 | 1.4372 / S20153 | 200 |
| Core 4622 | 1.4622 / S44330 | 220 |

The modulus cells are in PDF p.10 Table 7, the metric column headed Modulus of elasticity at 20 °C [GPa]. Values remain the source lexical strings 200 or 220. No extra precision or imperial conversion is imported. Composition/designation evidence is p.1 Table 1; named product descriptions and available form families are in pp.2–3 Table 2 and p.4 Table 3.

Table 1 explicitly labels its chemistry as typical percent by mass. These selected cells identify source-qualified alloy formulations, not certified compositions, complete stoichiometries or acceptance ranges. Printed dashes are retained and never treated as zero; no iron balance or normalization is inferred. Ti, Nb and Cu additions without amounts stay unquantified.

Core 201/4372 and Core 201LN/4372 share EN 1.4372 but have UNS S20100 and S20153, respectively. Their listed typical C/Cr/Ni/N values differ: 0.05/16.1/3.6/0.08 versus 0.02/16.2/4.1/0.16 percent by mass. This composition and UNS evidence supports separate source-qualified identities, without claiming universal EN/UNS equivalence. Their source Others cell is retained as `Cu 6.6Mn`: Cu has no stated amount and 6.6 is associated with Mn. Each grade alias qualifies the EN with its distinct UNS, while composition/scope notes retain the shared EN itself. A search for `1.4372` can match both; no duplicate bare-EN synonym or weakened collision rule is introduced.

Each actual Outokumpu designation has one manufacturer-authority grade record linked to its identity. Existing 304L/4307 and 441/4509 remain unchanged. 304L/4306 is excluded conservatively because S30403 overlaps the existing 304L identity; 439M is excluded because of overlap with 441 and matching selected Table 1 typical composition cells. Processing, stock form, brand spelling, translation and temperature do not create further identities.

## Property classification and unknowns

All ten values remain `manufacturer_reference`, with `reporting_basis` and `summary_statistic` set to `not_stated`. Table 7 attributes metric values to EN 10088-1; this does not verify the standard edition, specimen-test procedure or conformance. The nine selected unstarred austenitic rows keep `determination_basis=not_stated`.

Core 4622 carries an asterisk whose footnote identifies Outokumpu tested values. Its determination basis is therefore `source_reports_measurement`, while its evidence kind remains manufacturer reference. The footnote does not supply detailed method, sample count, uncertainty or a new independently validated experimental dataset.

Temperature is explicitly 20 °C for this column. Exact specimen form, heat treatment, lot, orientation, conditioning, humidity, loading rate, static/dynamic determination and modulus-fit interval are unknown. Sample count and uncertainty remain null; no mean, SD, isotropy or laboratory-default condition is inferred. Table 1 mechanical-performance minimum-value footnotes and general product forms are not transferred to the modulus measurement. All properties are `catalog_only`, with universal-bound, engineering-allowable, independent-scientific-review and raw-data-reanalysis flags false.

## Source, revision and rights

Outokumpu. *Core range datasheet: Stainless steels for corrosive environments*. Printed revision `1560EN:4. November, 2022.` on PDF p.16.

Official PDF: https://www.outokumpu.com/en/products/product-ranges/-/media/files/products/core/outokumpu-core-range-datasheet.pdf?hash=0DB21994AD31F93E9C62A531BE9C36E6&modified=20251117111909&revision=025e9931-a1d5-4c8f-8ff5-f881d38916da

The 16-page PDF is 563675 bytes, SHA-256 `91d2f4b1340562b0d692a3921a5b0ea2518ddcb6cbdcc9ec97a3d7ad886d7ad9`, exactly matching the previously bound source. Source ID `outokumpu_core_1560en4_202211` is reused unchanged; its sorted compact UTF-8 JSON plus terminal LF has SHA-256 `8495de101d6ce62a9f720cf5c5245aad4349989b0b9a68fee8c81aca501e5154`.

No explicit reuse license is verified. Page 16 contains information/suitability disclaimers and trademarks, not an open-license grant. This candidate includes only sparse original factual composition/designation and modulus cells, precise locators, attribution and original curation. It includes no source PDF, page image, complete table, extended prose or other source asset. The source is not relicensed under project MIT; limited factual curation is not legal clearance or a blanket redistribution right.

Exactly one authorized official GET returned HTTP 200 with no redirect, retry or metadata request. A 15 MB response cap, 40-second socket timeout and 90-second acquisition-process wall deadline were active. The observed process wall time was 5.89100000000326 seconds; neither timeout triggered. Raw assets and the acquisition receipt remain outside the repository in `incremental-evidence/primary-table-growth-7-20261020/source-research/`.

`source-review.json` is copied byte-for-byte from the independent LF-only review, SHA-256 `a952e53651273e91f46d77e7a45d8211f24db02f25d64ca5d023ea6fb804b8af`. The independent catalog reconciliation is `incremental-evidence/primary-table-growth-7-20261020/novelty/outokumpu-core-novelty.json`, SHA-256 `da1da7652e0a4274558dfedd2711112cdc58bafb1867e7f231b14ab22285d3b6`. Source transcription and catalog reconciliation do not substitute for scientific review or legal clearance.

## Reproducible preparation

`packet-spec.json` uses shared contexts with explicit source facts and links. The identities and source-reference states have authored English, Chinese, Japanese and German names; translations are machine-assisted, with no native-language review or certification claimed.

```sh
python scripts/prepare_formulation_packet.py --spec experimental/material-batches/outokumpu-core-moduli-20261020/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/outokumpu-core-moduli-20261020/prepared-packet.json
```

`preparation-receipt.json` records the actual native immutable creation and one same-input repeat, exact command, exit statuses, output bytes/hash and modification time. No successful preparation or runtime admission is implied before that receipt exists. Runtime integration, targeted tests, package checks and publication are owned by the parent workflow.
