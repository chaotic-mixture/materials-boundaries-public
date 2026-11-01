# Quota source audit, 2026-10-27

Goal: at least 1,000 admitted unique identities in **each** of metal, inorganic,
polymer, composite and natural. This package inventories public source files;
it is not a source profile registration, scientific approval or admission packet.

The [baseline coverage](baseline-coverage.json) pins commit and runtime input hashes.
[MPEA inventory](mpea-inventory.json) and [polymer inventory](polymetrix-inventory.json)
record raw byte digests, literal-key counts, source-label frequencies and the
SHA-256 of the external held-record payload. All 8,912 rows are held; the admitted
increment is zero. Canonical identity and baseline-overlap counts remain unknown.

## Sources and attribution

- Kunchapu, Sreekanth; Jablonka, Kevin Maik. *Curated Glass Transition Temperature
  for Polymers*, published 2025-07-02, DOI
  [10.5281/zenodo.15789599](https://zenodo.org/records/15789599).
  Zenodo record metadata identifies CC BY 4.0. File:
  `LAMALAB_CURATED_Tg_structured_polymerclass_with_embeddings.csv`;
  43,615,282 bytes; depositor MD5 `31400a5f499394e3a6e0658488a464bb`;
  SHA-256 `e3064f5d55830a93b4d43d8a709a4fbada7742c19a311c69c0aada6793422a91`.
  Metadata bytes SHA-256:
  `097d1d05591e36c27de0bbbc53a22f5f8368fc7dc051c2d6e4428b17d328a504`.
- Borg, C. K. H., et al. *Expanded dataset of mechanical properties and observed
  phases of multi-principal element alloys*, Scientific Data 7, 430 (2020), DOI
  [10.1038/s41597-020-00768-9](https://doi.org/10.1038/s41597-020-00768-9).
  [Source repository](https://github.com/CitrineInformatics/MPEA_dataset/tree/d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e),
  commit `d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e`, file `MPEA_dataset.csv`;
  332,126 bytes; SHA-256
  `c5504d93fd324d1be26cf814d0694ee9ee95578d68a0b38aba6813b939fa2c5d`.
  Repository LICENSE is Apache-2.0, SHA-256
  `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`.

Changes: selected source fields copied into external held inventories; row
ordinals and hashes added; literal-string/frequency/numerical-presence summaries
generated. No author endorsement, upstream rights clearance, original-paper
transcription review or specimen-level statistical interpretation is claimed.
Full source assets and held facts are not bundled in this package. Missing local
caches must be reacquired from the stated source and match the fixed pins.

## Offline reproduction

From the project root with its Python environment configured:

```sh
python -B experimental/material-batches/quota1000-source-audit-20261027/inspect_sources.py --profile mpea --source PATH_TO_MPEA_CSV --output-dir NEW_MPEA_AUDIT_DIR
python -B experimental/material-batches/quota1000-source-audit-20261027/inspect_sources.py --profile polymetrix --source PATH_TO_POLYMER_CSV --output-dir NEW_POLYMER_AUDIT_DIR
python -B -m unittest discover -s experimental/material-batches/quota1000-source-audit-20261027 -p test_inspect_sources.py -v
```

The inspector makes no network requests. It verifies source bytes before parsing,
requires expected headers and well-formed records, refuses an existing output
directory, preserves exact selected strings, and never writes runtime catalogs.
The CSV ordinal counts logical records after the header, not physical lines.
`raw_row_sha256` hashes the deterministic JSON rendering of all parsed row fields,
not the original CSV line bytes; the complete source digest binds those bytes.
PSMILES/formula equality here is literal string equality, not chemical identity.
Positive numerical presence includes only finite values greater than zero; it
does not classify blank, zero or negative cells as universally invalid science.

On the verified files both commands succeeded. Six focused tests passed, covering
changed/incomplete source rejection, malformed rows, absent fields, duplicate
counting, nonfinite values, and experimental/calculated field separation.
Full runtime regressions and hosted CI were not run for this inventory package.
Scientific, identity, upstream-rights and independent-review gates remain open.

See the [five-class growth record](../../../docs/MATERIAL_GROWTH_1000_PER_CLASS.zh.md)
for class deficits and the separate inorganic/composite acquisition queue.
