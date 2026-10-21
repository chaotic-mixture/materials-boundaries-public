# Reviewed reference-filament measurements

This review-only packet proposes **eight identities, zero grades, eight states,
sixteen measured properties and four sources**. Five identities are polymers and
three are composites. The source contains nineteen candidate product rows;
nineteen is not a net material increment. The prepared packet admits zero formal
materials and does not itself change runtime catalogs.

The pinned predecessor is `5e8d63dc9b7832cab893a5d849346d42b02e3c85`:
1134 core identities, 1158 project identities including the unchanged 24 accepted
computed compositions, 31 grades and 116 sources. The proposed successor has
1142 core / 1166 project identities, 31 grades and 120 sources. The 62 excluded
computed examples remain excluded.

## Selected identity and cell scope

| Exact Tested materials designation | Supplier | Category | Identity row | Measured E/F/G/H row |
| --- | --- | --- | --- | --- |
| PC, White 1642 | Ultimaker | polymer | 22 | 6 |
| PP, Natural | Ultimaker | polymer | 23 | 12 |
| TPU95A, White 1755 | Ultimaker | polymer | 24 | 11 |
| PLA conductive, CDP12805 Batch 171201 | Proto-pasta | composite | 16 | 17 |
| ABS ESD | KIMYA | composite | 20 | 21 |
| Koltron G1 | Add:North | composite | 26 | 20 |
| PEKK, Antero 800NA | Stratasys | polymer | 27 | 24 |
| PEI, ULTEM 9085 CG | Stratasys | polymer | 28 | 23 |

Each accepted identity has one source-scoped **reference filament 2.8 mm** state
and two properties: `tensile_modulus` from E and `tensile_strength` from G on
the `Tensile modulus` worksheet. F and H contain the respective source-labelled
`avedev` values. All original MPa unit strings, including their trailing source
space, and underlying XML numeric strings are preserved. Excel display rounding
is not substituted for the stored values. Numerical precision is not a claim
about measurement accuracy.

The `Tested materials` and `Tensile modulus` row order and labels differ.
`packet-spec.json` records both exact labels and both row numbers in
`review.workbook_selection`; the adapter never performs fuzzy matching or assumes
a constant row offset. Merged family cells B10:B16 and B19:B20 are located
explicitly in the authored evidence. The source-designation field retains the
complete product/color/code/batch wording.

The finite novelty review covers the pinned core catalog, 31 grades, the 24
accepted computed compositions and retained candidate packets: 1536 selected
files, 298 unique payloads, and no parse errors. Its external inventory SHA-256 is
`95f73069e9c3b5a1da46d6b14d61e0e4d726e327064a3c8f853f0676cef86fef`;
the final review SHA-256 is
`459d8c537e6643d7b08eb54e05bca2bb976e7d98d701e7902bee8802bf98f093`.
The packet embeds all nineteen decisions and their limits. This is a finite
catalog novelty decision, not proof of global chemical novelty or equivalence.

Six ordinary/Tough PLA rows, two PET-G rows, ordinary ABS, unresolved CPE and
unspecified nylon are deferred. Supplier, color, SKU, batch, filament/fiber form,
dogbone geometry, angle and layer thickness do not create identities. CPE means
the workbook's co-polyester, not an inferred chlorinated polyethylene; the nylon
subtype remains unknown. `Natural` in the PP label is not biological-tissue
classification. ULTEM's `CG` suffix is not expanded, and neither PEI nor PEKK
commercial products are asserted to be chemically pure. All grades remain null:
the mixed `Short name, grade` heading does not distinguish a grade from a product,
SKU, color or batch code.

## Measurement and uncertainty boundaries

The measured header says `data from 10 mm/min tests`. This is retained as a
loading/test rate without claiming explicitly reported crosshead or strain rate.
`Samples!C27` says three to five specimens were tested per series and average data
were used. The properties preserve `reported_mean` and `reported_summary`; exact
row-specific n remains null. No pooling weights or independent replication count
are inferred.

The `avedev` label has no explicit statistical definition in the inspected cells.
Each F/H value and locator is retained verbatim in `uncertainty_note`, including
scientific notation where stored. It is not relabelled SD, SEM, confidence
interval or printed plus/minus. `uncertainty: null` and its qualified status mean
that a supported statistical uncertainty type is unavailable, **not** that no
deviation was reported. No runtime schema is expanded for this batch.

The ISO 527-2-labelled reference column C is excluded. It supplies neither a
measured value nor a test-standard claim for E:H. Temperature, humidity,
conditioning, gauge length, grip separation, extensometry, extraction window and
source-specific direction remain unknown. Nozzle/bed temperatures and layer
thickness describe printing, not testing of the selected reference filament.
Single extruded fibers, printed dogbones, angles, layer settings, density and
ambiguous zero cells are excluded. No zero stiffness or zero porosity is inferred.
The source's `E-mod` remains tensile modulus rather than an asserted universal
isotropic Young's modulus. Tensile strength receives no invented yield/ultimate
qualifier.

## Attribution and classification evidence

Aniskevich Andrey and Bulderberga Olga (2023), *Characterisation of mechanical
properties of materials used in 3D printing*, Zenodo dataset,
[version DOI 10.5281/zenodo.8089569](https://doi.org/10.5281/zenodo.8089569),
[concept DOI 10.5281/zenodo.8089568](https://doi.org/10.5281/zenodo.8089568).
Official version and concept metadata identify
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The source workbook has 1,391,320 bytes, published MD5
`c4842898d2c389ccd7a902691d8a4fa3`, and independently computed SHA-256
`830b2c9277dcc2d03265b63e311a5e7089c258ebb6a389b45d07601ae4b2e4e7`.
`source-review.json` is an unchanged copy of the frozen independent review,
SHA-256 `1d8b8574c662bc2a638e4e26723e4f042fb31e47932e0050e44d96b623b3420e`.
The raw workbook, full worksheets, source images, specimen data and inspection
dumps remain outside the repository and package.

Three separate manufacturer records support only the composite identities:

- [Protopasta Conductive PLA FAQ](https://proto-pasta.com/pages/conductive-pla):
  PLA, dispersant and conductive carbon black. Official-page text was inspected
  through directed search; direct retrieval returned HTTP 429, so original bytes
  and a source-document hash are unavailable.
- [Add North product catalogue 2022](https://storage.googleapis.com/addnorth-com-public/catalog/addnorth_product_catalogue_2022.pdf),
  PDF page 19 / printed page 37: Koltron G1 incorporates graphene. The workbook
  supplies the PVDF family identification. The adjacent Adamant S1 description
  is not transferred to Koltron G1.
- [MakerBot/Stratasys announcement, 2019-11-19](https://investors.stratasys.com/news-events/press-releases/detail/537/makerbot-launches-method-materials-development-program):
  the exact KIMYA ABS ESD product is described as ABS containing carbon nanotubes.
  This is historical manufacturer-platform partner context, not a study-lot
  composition assay or proof of unchanged formulations across revisions.

No manufacturer numerical property, filler fraction, purity, printing condition
or grade is imported. These sources retain unverified open-license status and
limited factual-curation notices. The existing compiler has a closed exception
for the three exact source-record hashes and their three explicit composite
identity IDs. Only `material_identity` evidence is permitted; altered notices,
new identities, classification changes, manufacturer properties, state conditions
or grade use fail. This does not create a generic manufacturer rights exemption
or assign CC BY to manufacturer material. Source attribution and original
curation remain separate from the project's code license.

## Reproduction

The checkout-only adapter uses Python's standard library; no spreadsheet package
or network call is required. Obtain the exact original workbook independently
and keep it outside the checkout. From the repository root, replace the external
paths below with your retained workbook and an existing external output directory:

```sh
python scripts/extract_curated_filament_cells.py --workbook "PATH_OUTSIDE_CHECKOUT/Annex 3.1. Characterisation of mechanical properties.xlsx" --spec experimental/material-batches/zenodo-8089569-filaments-20261021/packet-spec.json --output PATH_OUTSIDE_CHECKOUT/selected-filament-facts.json
```

The adapter checks the byte count, MD5 and SHA-256, exact headers, explicit row
joins and literal numeric cells. It compares the extracted E/G values, units,
source labels, E/F/G/H locators, source identity/hash and exact F/H `avedev` notes
against the expanded authored specification. A manually substituted C-column
value or locator fails. Missing, blank, zero or formula-backed selected cells
require separate review. The sparse output contains no full worksheet and is
written immutably outside the checkout; identical replay leaves it unchanged.

The reviewed specification uses the existing formulation compiler and importer:

```sh
python scripts/prepare_formulation_packet.py --spec experimental/material-batches/zenodo-8089569-filaments-20261021/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/zenodo-8089569-filaments-20261021/prepared-packet.json
```

Use the pinned predecessor catalogs when replaying after integration. The first
publication reports `Created`; an identical repetition reports `Unchanged` with
the same bytes and modification time. Different content is never overwritten.
`preparation-receipt.json` records the actual successful native creation/replay
and preserves the earlier failed authoring attempts: a missing evidence tag,
then a sandbox OS hard-link denial. The corrected documentary fields and native
execution did not change source values or identity decisions. Packet SHA-256:
`aaa94bd1f752e00f37268f8b786326dcb98011648985f8bc77cb92362f4c57e8`.

The seven focused adapter/gate tests cover reference-column exclusion, original
numeric lexemes, exact joins, unknown/zero handling, authored-spec binding,
deterministic replay and the closed manufacturer classification boundary.
Existing compiler/integrator tests cover state-versus-identity counting and alias
collisions. Product validation and runtime integration are separate root-owned
steps. Source transcription, software validation and four-language display names
do not claim scientific approval, raw-data reanalysis, native-language review,
legal clearance or engineering suitability. All properties remain catalog-only,
non-universal and non-allowable; translations are machine-assisted curation.
