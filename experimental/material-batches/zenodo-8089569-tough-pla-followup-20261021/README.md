# Tough PLA identity follow-up

This review-only candidate proposes **one polymer identity, zero grades, two
source-specific filament states, and four measured properties**. It references
two sources: the unchanged, already registered Zenodo dataset and one new
manufacturer SDS. Preparing this packet admits zero runtime or formal materials.

The predecessor is `5cc1418392696dc8115581ad693dabfc2695422e`. Its 1,142 core
identities, 1,142 states, 1,150 properties, 31 grades and 120 sources would become
1,143 identities, 1,144 states, 1,154 properties, 31 grades and 121 sources after
validated integration. The 24 accepted computed compositions remain unchanged;
the 62 excluded computed examples remain excluded. Formal identity growth is one,
independent of the two state records.

## One identity, two original series

The 22 December 2022 Ultimaker Tough PLA SDS names polylactic acid and an
unspecified acrylic polymer, and covers both Black and White. This supports one
source-qualified formulation family, represented by both original workbook
measurement groups. It does not establish identical complete color recipes,
historical lot composition, a constituent fraction, PMMA, or the acrylic
polymer's function. It does not establish that other PLA products lack additives.
Supplier, product name, color, code and measured differences alone are not the
basis for a new identity.

| Exact workbook designation | Tested materials row | Tensile modulus row | State |
| --- | --- | --- | --- |
| `PLA Tough White 20231` | 10 | 8 | White reference filament |
| `PLA Tough Black 202300` | 11 | 7 | Black reference filament |

Both states link to `mat_aniskevich_2023_ultimaker_tough_pla`. The distinct source
series are preserved without averaging or pooling. The literal codes `20231`
and `202300` are neither corrected nor authenticated as manufacturer SKUs. Grade
IDs remain null. All four display languages are machine-assisted curation;
native-language and independent scientific review are not claimed.

`PA, Nylon Transparent 1647` remains deferred: current PA6/66 descriptions do not
establish the historical study product's subtype or resolve overlap with PA12.
The workbook's CPE and all other prior decisions remain unchanged. This is a
bounded reconsideration of the same candidate set, not another dataset or a
nineteen-material increment.

## Measurements and unknowns

Each state retains `tensile_modulus` from E and `tensile_strength` from G in the
`Tensile modulus` sheet. Original XML decimal strings and the source unit
`MPa `, including its trailing space, are preserved. F/H `avedev` numbers and
locators remain in qualified notes; their statistical meaning is undefined, so
typed uncertainty stays null. No SD, SEM, confidence interval, or printed
plus/minus interpretation is introduced.

The source describes reference filament 2.8 mm and tests at 10 mm/min. It reports
averages of three to five specimens per series; exact row n remains unknown.
Column C's ISO 527-2 reference is excluded from measured values and test-standard
claims. Temperature, humidity, conditioning, direction convention, gauge length,
grip separation, extensometry and modulus extraction window remain unknown.
Printing settings, extruded-fiber results, dogbone results, density and ambiguous
zeros are excluded. Tensile modulus is not asserted to be a universal isotropic
Young's modulus, and tensile strength receives no invented yield/ultimate label.

## Sources and evidence availability

Aniskevich Andrey and Bulderberga Olga (2023), *Characterisation of mechanical
properties of materials used in 3D printing*,
[Zenodo version DOI 10.5281/zenodo.8089569](https://doi.org/10.5281/zenodo.8089569),
is registered under source-specific CC BY 4.0 metadata. The workbook has
1,391,320 bytes, MD5 `c4842898d2c389ccd7a902691d8a4fa3`, and SHA-256
`830b2c9277dcc2d03265b63e311a5e7089c258ebb6a389b45d07601ae4b2e4e7`.
Its existing source record is reused exactly, without metadata amendments.

Ultimaker, [Tough PLA Safety Data Sheet, version 2.0, revised 2022-12-22](https://um-support-files.ultimaker.com/materials/2.85mm/sds/TOUGH-PLA/UM_Tough%20PLA_EU_en_SDSv2.0.pdf),
PDF page 1 section 1.1 and page 2 section 3.2, supplies only product-family and
constituent identity evidence. Original PDF SHA-256 is
`3b97d600b92f44da56a4c5c8bae029dddbc4b2d400d3c7501cafed9b7aaf69cf`.
The fixed curated source-record hash is
`c7cab63a20b2db1b692a066f30f8c22f04600b7e7acb7408c07b7e54aa2e9023`.
No open reuse license was verified for this SDS. The compiler permits only its
exact reviewed record, the one Tough PLA identity, category `polymer`, and
`material_identity` evidence. Manufacturer numerical properties, state
conditions, grades and extra identities are excluded. The dataset license does
not extend to the SDS.

`source-review.json` is an original, public-safe curation of the independent
reviews, not a byte-identical copy of the full local reports. Its SHA-256 is
`25fb93bd5529d28779cd3e985dd315da2fdacf1229169e83096a53983f12de02`.
Embedded external review and finite-inventory hashes are provenance identifiers,
not public download links. Full local inventories, acquisition receipts, raw
workbooks/PDFs, rendered pages and full extracted text are not bundled. The
[prior evidence-availability sidecar](../zenodo-8089569-filaments-20261021/EVIDENCE_AVAILABILITY.md)
explains this boundary and the limits of independent public replay. Original
batch-8 candidate files and their historical decisions remain unchanged.

## Replay the extraction and packet

Use the exact original workbook downloaded from the registered Zenodo file URL
and keep it outside the checkout. Supply an external directory containing the
three baseline catalog files (`materials.json`, `reference_properties.json`,
`sources.json`) exported as unchanged bytes from the predecessor above. Their
hashes are pinned in `packet-spec.json`; the post-integration live catalog is not
the replay baseline. Set the example paths below to external locations.

```powershell
$Workbook = 'C:\external-evidence\Annex 3.1. Characterisation of mechanical properties.xlsx'
$Baseline = 'C:\external-evidence\baseline-5cc1418'
$Sparse = 'C:\external-evidence\tough-filament-cells.json'
$Replay = 'C:\external-evidence\tough-prepared-packet.json'
$Spec = 'experimental/material-batches/zenodo-8089569-tough-pla-followup-20261021/packet-spec.json'
python scripts/extract_curated_filament_cells.py --workbook $Workbook --spec $Spec --output $Sparse
python scripts/prepare_formulation_packet.py --baseline-dir $Baseline --spec $Spec --output $Replay
```

The adapter verifies the workbook fingerprint, exact headers and source row
joins, then binds the extracted values, units, E/F/G/H locators and avedev notes
to the authored spec. Grouped selections explicitly name each state under the
single identity; duplicate groups, state IDs and row reuse fail. Legacy batch-8
flat selections keep their original uniqueness rules and deterministic output.
The compiler then applies the existing crosswalk, source, scientific and
structural-clone checks. Neither command changes runtime catalogs. Repeating
identical commands yields `Unchanged`; a differing immutable output is refused.
The checked-in preparation receipt records actual execution separately from
tests and admission. No local source assets are required for ordinary installed
catalog use.
