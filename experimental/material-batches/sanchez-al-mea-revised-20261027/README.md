# Revised Sanchez 2019 aluminium alloy candidate

This revision addresses the independent read-only review of the
[original frozen candidate](../sanchez-al-mea-20261027/candidate.json), SHA-256
`0eb4fbab67abc0905cb928eb4dc458b563605063de25abcf56e4c201b50c20c5`.
That version is retained as a rejected historical artifact and must not be
admitted. The new candidate still proposes five identities, five cast states,
ten properties and one source; publication and runtime admission are separate.

The original-source bytes are unchanged: official Europe PMC XML SHA-256
`9feae72296d930c220b99b57bf79047d9760911718ab007f6f95e2d3a6c0a8dc`,
MPEA CSV SHA-256 `c5504d93fd324d1be26cf814d0694ee9ee95578d68a0b38aba6813b939fa2c5d`.
Source: Jon Mikel Sanchez, Iban Vicario, Joseba Albizuri, Teresa Guraya and
Eva Maria Acuña, Scientific Reports 9, 6792 (2019),
[10.1038/s41598-019-43329-w](https://doi.org/10.1038/s41598-019-43329-w).
Copyright The Author(s) 2019; article-specific
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Changes: selected original facts structured with source locators and unknowns;
no endorsement is implied. Full source assets are not redistributed.

## Corrected source interpretation

| Nominal atomic-percent recipe | Density, g/cm³ | Compression E, GPa | Printed SD | SD number, GPa |
| --- | ---: | ---: | --- | ---: |
| Al65Cu5Fe5Mg5Si15Zn5 | 3.08 | 88.7 | 04 | 4 |
| Al65Cu5Mg5Ni5Si15Zn5 | 3.15 | 107.8 | 17 | 17 |
| Al70Cr5Cu5Mg5Si10Zn5 | 3.06 | 78.4 | 03 | 3 |
| Al70Cu5Mg5Mn5Si10Zn5 | 2.98 | 114.1 | 02 | 2 |
| Al70Cu5Mg5Si10Zn5Zr5 | 3.06 | 105.1 | 27 | 27 |

Par25 explicitly identifies standard deviations. These use the existing
`reported_measures` representation because the central statistic remains
`not_stated`; no mean is inferred. Original SD strings and complete E cells
remain preserved. Leading integer zeroes do not introduce a decimal point.
The generic numeric validator now accepts this exact integer representation,
while still rejecting 04→0.4, 04→4.0 and arbitrary whitespace/extra characters.
Density cells have no per-value SD; their uncertainty and sample count remain
unknown. Compression n≥5, geometry and strain rate remain scoped to compression.

Par31 explicitly states as-cast material. Par14 reports shrinkage porosity for
Fe, Mn and Zr recipes. Par25 limits the Cr non-detection statement to Figure
2(e), not a global zero-porosity measurement. Ni-specific porosity remains
unknown. Nominal and SEM-EDS compositions stay separate, as do original and
three erroneous MPEA formula labels. RT remains qualitative; no 25°C default,
certified grade, final purity or density-derived mechanical property is added.

The first independent reviewer read all 32 baseline metal identities and their
state/composition scopes and found no same six-element recipe in that finite
baseline. This is not a proof of global chemical uniqueness. PDF text was read
by that reviewer, but raw PDF byte hashes and visual page inspection remain
unverified. Independent scientific peer review and raw-data reanalysis remain
false.

## Reproduce the frozen revision

```sh
python -B experimental/material-batches/sanchez-al-mea-revised-20261027/build_candidate.py --xml PATH_TO_PINNED_XML --mpea PATH_TO_PINNED_MPEA_CSV --output NEW_CANDIDATE_JSON
python -B -m unittest discover -s experimental/material-batches/sanchez-al-mea-revised-20261027 -p test_candidate.py -v
```

Read the [local integration verification record](INTEGRATION_VALIDATION.md)
and adjacent review/validation/integration receipts for their actual
outcomes; a valid candidate graph alone does not establish runtime admission,
complete regression coverage, hosted CI or publication.
