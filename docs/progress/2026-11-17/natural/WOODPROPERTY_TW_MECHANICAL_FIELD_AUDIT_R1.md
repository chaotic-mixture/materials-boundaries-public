# WoodProperty.tw mechanical-field audit — R1

Date: 2026-11-17  
Disposition: metadata-based discovery audit; no property rows transcribed and no production changes.

## Source and current access

Su, Sheng-Hsin (2025), “WoodProperty.tw: a wood property database for tree and bamboo species in Taiwan,” *Taiwania* 70(1):58–64, DOI [10.6165/tai.2025.70.58](https://doi.org/10.6165/tai.2025.70.58). The version 1 public record is [Zenodo 13836163](https://zenodo.org/records/13836163), published 2025-01-15. Its description says the database covers 156 documents (1947–2018), 5,762 property records, 236 fields and 607 tree/bamboo species; it asks users to cite the source literature for data used.

The record exposes six CSVs, a SQL DDL, four appendices and a database-structure figure. The metadata CSV `wood property_metadata.csv` (49.4 kB, Zenodo MD5 `662a27bfde314e40dca816ddac9ea8a6`) was readable and has 237 lines including a header. The main `wood property.csv` (4.8 MB, MD5 `d4dcfcaa5979a7dcfe461d6fe02a0966`) exceeded the web retrieval service's content limit; the local network also could not resolve `zenodo.org`. Therefore no main-table records, row counts, species-property cross-tabs or actual candidate species are claimed here.

## Relevant field semantics from the published metadata

- Each source-derived row has `dataID` in `docID_number` form. `docID` is first-author surname plus year, with letter suffixes for duplicates; `number` is the database-assigned source-table row number. These provide traceability back to a document, but not a universal specimen identifier.
- Taxonomy includes species ID (`spID`), source-reported scientific name (`scientificName.ref`), source synonym/name fields, and a note on taxonomy. Preserve source naming and database taxonomy together until the original citation is checked.
- Sample context fields include tree age, DBH, height, locality, sampling position and notes. Several are free text and multiple values may be semicolon-delimited; they are not necessarily per-test specimen metadata.
- Moisture/density fields distinguish basic, oven-dry, air-dry and green specific gravity, with definitions tied to mass/volume state. Moisture content has air-dry and green fields. Do not merge them into one generic density or moisture number.
- Static-bending modulus of elasticity (`MOE`) and modulus of rupture (`MOR`) use kg/cm². Separate fields exist for min/max, green wood, radial/tangential/45° sections, and fiber stress at elastic limit. Metadata explicitly equates MOR with bending strength; it does not make these quantities interchangeable with tensile or compression strength.
- Compression parallel to grain (`compr.parall`) is defined as compression/crushing strength parallel to grain, in kg/cm², with min/max and other state-specific fields. Other strength families include tension parallel/perpendicular, shear (including radial/tangential/45°), cleavage and impact-bending energy; their differing dimensions and test meanings prohibit naive pooling.
- Brinell hardness is in kgf/mm²; the unit and method differ from indentation methods such as Vickers. Keep hardness families separate.
- Bamboo-specific shrinkage fields (`shrink.L`, `.W`, `.T`) are explicitly green-to-oven-dry length, width and thickness shrinkage. These describe dimensional response, not strength.

## Candidate-screening rules for a later row-level pass

1. Start from mechanical-field rows with nonempty `docID`, `dataID`, taxon, property value and source citation. A species appearing in the compiled database is a discovery signal, not itself a candidate material record.
2. Separate tree timber, native bamboo culm/strip and manufactured or processed bamboo products. Do not treat bamboo rows as directly comparable with timber or engineered bamboo composites.
3. Retain property direction, specimen form, green/air-dry/oven-dry condition, density convention, source units and reported test standard whenever available. Convert units only alongside the source unit and explicit conversion.
4. Treat a source table summary as group-level evidence unless the original document establishes specimen-level observations. Do not infer individual samples from a single compiled mean or range.
5. For any selected row, retrieve the linked source literature record and original paper/standard before promotion. The paper is the primary evidence for methods and context; cite Su's database as the discovery/index layer.

## Supported conclusion and next useful action

The database is a high-coverage, traceable index with unusually useful field definitions, including explicit separation of wood state, section direction and property family. Its metadata supports a sound extraction protocol and taxonomy-aware search design. It does not yet support a verified species shortlist or numeric candidate records because the main property table and linked source literature rows have not been inspected. Next, retrieve the Zenodo main CSV and source-literature CSV through a channel that permits the full downloads; verify the published MD5s, inspect the schema and row-level join keys, then calculate coverage by species and mechanical property without pooling incompatible states.

## Update R2 — license and mechanical-subset coverage verified (2026-11-17)

The primary data paper is openly accessible and explicitly releases WoodProperty.tw under CC BY 4.0. Its Figure 1 reports that the mechanical-property category contains 2,215 records across 417 species (80 data fields), within the full database of 5,762 records and 607 species. These counts support the database's value as a species-discovery index and correct the earlier uncertainty about the data-paper license.

This does not establish the license field for every repository object independently, nor does it expose the property rows. Zenodo still lists the main `wood property.csv` at 4.8 MB, but no rows were returned by the preview in this review and local host resolution remains unavailable. Therefore no species-property coverage, candidate ranking or numeric property value can yet be reported from the main table. Each selected wood/bamboo observation must still be traced through `docID`/`dataID` to its cited primary source before candidate use.

Updated sources: [primary data paper PDF](https://taiwania.ntu.edu.tw/pdf/tai.2025.70.58.pdf); [Zenodo dataset and file inventory](https://zenodo.org/records/13836163).
