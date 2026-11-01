# Sanchez 2019 cast aluminium alloy candidates

This held candidate proposes five source-qualified nominal alloy identities,
five cast states, ten properties and one source. **Admitted increment: zero.**
No runtime catalog, schema, evaluator or workflow has been edited. Independent
source/identity review and an explicit admission decision remain pending.

Source: Jon Mikel Sanchez, Iban Vicario, Joseba Albizuri, Teresa Guraya and Eva
Maria Acuña (2019), *Design, Microstructure and Mechanical Properties of Cast
Medium Entropy Aluminium Alloys*, Scientific Reports 9, 6792,
[DOI 10.1038/s41598-019-43329-w](https://doi.org/10.1038/s41598-019-43329-w).

The producer inspected [official Europe PMC XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6494811/fullTextXML),
Tables 1, 3 and 4, preparation/mechanical methods, authorship and permissions.
XML SHA-256: `9feae72296d930c220b99b57bf79047d9760911718ab007f6f95e2d3a6c0a8dc`.
The article-specific notice identifies CC BY 4.0, copyright The Author(s) 2019.
No separate restriction was observed for the selected original facts in the XML.
Changes: selected compositions and property facts transcribed with explicit
unknowns and discrepancy notes. No author endorsement is implied.
Full source assets, images and unrelated table columns are not bundled.
Original PDF bytes/page images and XML/PDF equivalence have not been checked.

## Primary facts and compilation discrepancies

| Original nominal composition, at.% | Density, g/cm³ | E center, GPa | E plus/minus term, literal | MPEA composition comparison |
| --- | ---: | ---: | --- | --- |
| Al65Cu5Fe5Mg5Si15Zn5 | 3.08 | 88.7 | 04 | Consistent within three-decimal ratio rounding |
| Al65Cu5Mg5Ni5Si15Zn5 | 3.15 | 107.8 | 17 | Consistent within three-decimal ratio rounding |
| Al70Cr5Cu5Mg5Si10Zn5 | 3.06 | 78.4 | 03 | Conflicts: compilation ratios correspond to Al65/Si15 |
| Al70Cu5Mg5Mn5Si10Zn5 | 2.98 | 114.1 | 02 | Conflicts: compilation ratios correspond to Al65/Si15 |
| Al70Cu5Mg5Si10Zn5Zr5 | 3.06 | 105.1 | 27 | Conflicts: compilation ratios correspond to Al65/Si15 |

The MPEA source is pinned to commit
`d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e`, CSV SHA-256
`c5504d93fd324d1be26cf814d0694ee9ee95578d68a0b38aba6813b939fa2c5d`.
The five central property pairs match its CSV; three nominal composition labels
do not match the original. No compiled formula is silently corrected in the raw
source cache. The candidate uses original nominal recipes and preserves both
representations in `primary_facts`. Ratio comparison is a finite consistency
check for these five rows, not a general canonical chemical identity resolver.

Table 1 measured SEM-EDS compositions, including oxygen and blank cells, remain
separate from nominal atomic-percent recipes. Blank cells are not inferred zero.
No certified grade, purity, final exact composition or additional identity is
created from SEM-EDS values, repeated specimens or a cast processing state.

Table 3 reports compressive modulus. Methods describe cylindrical compression
specimens (13 mm diameter, 26 mm height), specimen-mounted clip-on extensometry,
strain rate 0.001 s^-1 and at least five compression specimens. These facts do
not establish tensile modulus, a fitting window, independent production batches
or a density sample count. The Archimedes density method has no specified fluid,
correction procedure or density-specific specimen details.

RT remains a qualitative source label; the compilation's numeric 25 degrees C
is not adopted. Density-specific scope of the Table 3 RT caption remains marked
for review. Center statistic is not stated. The literal `04`, `17`, `03`, `02`
and `27` plus/minus terms retain unresolved meaning and leading-zero scale;
they are not converted to SD, SEM, CI, zero uncertainty or inferred decimals.

## Reproduction and validation

From the repository root using its configured Python environment:

```sh
python -B experimental/material-batches/sanchez-al-mea-20261027/build_candidate.py --xml PATH_TO_XML --mpea PATH_TO_FIXED_MPEA_CSV --output NEW_CANDIDATE_JSON
python -B -m unittest discover -s experimental/material-batches/sanchez-al-mea-20261027 -p test_candidate.py -v
```

The builder verifies both complete source digests before parsing and cross-checks
selected source cells, measured/nominal distinctions, compilation numerical pairs
and composition ratios. It validates the candidate graph using the existing
runtime contract but performs no merge or admission. A different existing output
is refused. All four name slots currently use explicit English fallback.

Seven focused checks passed. They cover the closed candidate graph, three
composition conflicts, density/compression count and rate separation, unresolved
plus/minus meaning, qualitative RT, changed primary-source rejection and unknown
evidence-source rejection. The final artifact replays exactly from pinned inputs.
Two earlier builder attempts failed existing gates (missing explanatory text for
an inapplicable density loading rate, then a missing condition evidence tag);
the authored candidate was corrected without changing validator rules.

Full baseline identity overlap/semantic equivalence review, independent source
review, scientific approval, runtime integration, broad regressions,
installed-wheel checks, hosted CI and publication are not completed by this
candidate package. The [validation receipt](VALIDATION.json) distinguishes these
open gates from the checks actually run.
