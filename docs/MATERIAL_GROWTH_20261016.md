# Local incremental integration: Nb and four NBS halides

This local experimental branch adds five source-qualified identities, five states,
five numerical properties and one bibliographic source to the exact `d4e9cf3`
three-reference integration. It adds no grades and does not change main. The
released main baseline is `4c5656cf6ba0ad1a54b736e0568e97abe4815c29`.

| Primary class | Released main project | Prior d4e9cf3 experiment | This local experiment | This increment |
| --- | ---: | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 1010 | 0 |
| Metal | 26 | 26 | 27 | +1 |
| Inorganic | 28 | 31 | 35 | +4 |
| Polymer | 14 | 14 | 14 | 0 |
| Composite | 3 | 3 | 3 | 0 |
| Total | 1081 | 1084 | 1089 | +5 |

The experimental core alone contains 1065 identities: natural 1010, metal 15,
inorganic 23, polymer 14 and composite 3. The separate add-on reuses exactly the
same 24 reviewed computed composition buckets. The 62 unadmitted computed examples
and held NOMAD candidates remain excluded. Counts describe the project's curated
identity convention, not universal chemical equivalence. The five-category goal
is incomplete; only natural currently reaches 1000.

## Integrated facts

| Identity | Exact reported density | Density temperature | Primary locator |
| --- | --- | --- | --- |
| `mat_watanabe2026_niobium_cylinder` | 8587.6 kg/m3 | 293 K | Watanabe 2026, Section 2.1.1, PDF pp. 4-5 |
| `mat_nbs1953_kbr` | 2.7533 g/cm^3 | 25 degrees C | NBS Circular 539 I, printed p. 67 / PDF p. 71 |
| `mat_nbs1953_ki` | 3.1257 g/cm^3 | 25 degrees C | NBS Circular 539 I, printed p. 69 / PDF p. 73 |
| `mat_nbs1953_naf` | 2.799 g/cm^3 | Not reported | NBS Circular 539 I, printed p. 64 / PDF p. 68 |
| `mat_nbs1953_baf2` | 4.886 g/cm^3 | 26 degrees C | NBS Circular 539 I, printed p. 72 / PDF p. 76 |

The frozen packets come from Nb commit
`1c1394854fb92c801d74f8642a21fdb17edf2ad0` and halide commit
`9b1c3249545f533ff12a8c3e7566c499dae88f53`. Their review and validation files retain
historical candidate-stage language and actual earlier results. They are copied
without changing their bytes; a previous test result is not a new execution.
The [integration manifest](../experimental/material-batches/20261016-nb-halide-incremental/integration.json)
binds the three baseline files, each candidate payload and its review by SHA-256.

The Nb identity is the reported cylinder containing at least 99.5 mass% Nb and
about 0.12 wt% Ta. It is not a pure-Nb or exact Nb:1 identity. Archimedes density
remains a source-reported measurement; six heating runs are not six density
measurements. Density basis, uncertainty, repeat count and unspecified measurement
conditions remain unknown. The inspected publication hash is honestly unavailable.

The four NBS values are crystallographic densities derived by the source from
measured lattice data, not direct bulk measurements or DFT predictions. NaF's
unknown density temperature is not replaced by a lattice or diffraction-table
temperature. KI's 450-degree preparation temperature and the unselected KBr
pycnometric comparison do not become density conditions. BaF2's impurity percent
basis remains unknown. All four reuse the single existing
`swanson_tatge_1953_nbs_circ539v1` source. LiF, KCl and CaF2 remain unchanged and
are counted once each.

## Authorization and remaining review

The existing [material contribution contract](MATERIAL_REFERENCE_CATALOG.md#add-a-material-without-a-new-python-family)
allows these supported quantities, methods and explicit unknowns. The user
authorized integration of eligible records in a separate local experiment after
the retained source, identity and reuse findings were checked. This is the
integration decision for this branch; the merge function and manifest hashes do
not grant scientific or legal approval. No wood-adapter approval is invented.

All five records now occur in this branch's runtime catalogs. Independent human
scientific review, final source/rights admission and a separately authorized
reviewed main release remain pending for these five and the preceding three NBS
references. `independent_scientific_review` and `raw_data_reanalysis` remain false;
all properties remain `catalog_only`, with no universal-bound or engineering-
allowable claim. Nb's four locale slots retain their documented English fallback.

Two exact, manifest-bound status-only replacements describe the Nb runtime copy
as locally integrated instead of an unpackaged candidate. They change only its
property `scope_note` and source `bundled_content`; the frozen input text and all
scientific fields remain preserved. The command permits only those two field/ID
combinations and requires the exact old text.

The retained parent source inspection establishes the article-specific CC BY 4.0
basis for the selected Watanabe fact. Existing NIST Technical Series findings
cover only the selected NBS-authored facts, not third-party comparison tables.
Attribution and source terms survive in the runtime records and notices. No PDF,
figure, complete table, supplement or raw structure asset is bundled. No new
source download, login, push, DOI registration or public deployment is part of
this increment.

## Reproduce the increment offline

Use a separate checkout of `d4e9cf3c48e25b9f8e2036c60dfa32c70bbbfcc0` as the
baseline. From this new branch, run:

```sh
python -B scripts/integrate_material_candidates.py \
  --baseline-dir /path/to/d4e9cf3-checkout/materials_boundaries/data \
  --manifest experimental/material-batches/20261016-nb-halide-incremental/integration.json \
  --output /path/to/private-output/nb-halide-increment.json
```

The output parent directory must already exist. The command performs no network
access and never rewrites the baseline or runtime catalogs. It emits one atomic,
immutable JSON package containing the three merged catalogs and a per-batch
incremental report. The manifest's ordered batches are Nb, then four halides.
Repeated execution with identical inputs and output returns unchanged. An
interruption before publication leaves no partial accepted package; rerun the
same command. An existing different output, changed pinned input, conflicting
record, missing property or unsupported unit fails closed. Choose a new output
only after separately reviewing changed input; do not edit hashes to imply review.

This branch's three runtime files are the serialized `catalogs.materials`,
`catalogs.properties` and `catalogs.sources` from that same result, using the
repository's existing UTF-8/indent-2/newline encoding. Tests require exact equality
and recover the original d4e9cf3 bytes by removing only these five additions.
The prior three-record NBS preservation checks still recover the main baseline.
The command's report distinguishes the actual local increment of five from the
unchanged released-main admission increment of zero.

Formal-component resource pins and the query manifest match the new runtime
bytes. Old SQLite baseline anchors remain incompatible; existing user databases
are not migrated or opened. Use a new explicit local database for this snapshot.
The add-on/API field name `formal_project_admission_count` reports 1089 in this
candidate installation; its name does not announce a new main release.

## Verification

Focused tests exercise the actual five-record increment, frozen inputs, exact
prior-byte recovery, idempotent merge/output, changed-input rejection, missing
properties, wrong units, source reuse and five-category totals. Project-required
checks additionally cover release metadata, complete catalog/schema validation,
the complete core test discovery, relevant formal/query catalogs, wheel metadata
and isolated installed-wheel behavior. Actual results and recovery artifacts are
reported in the handoff; this checklist alone is not evidence of success. Skips
remain explicitly unverified and are never counted as passes.


## Local experimental Nb and NBS increment, 2026-10-16

The local experiment retains the earlier LiF, KCl and CaF2 facts and adds KBr,
KI, NaF and BaF2 from Howard E. Swanson and Eleanor Tatge (1953),
*Standard X-ray Diffraction Powder Patterns, Volume I*, NBS Circular 539,
[DOI 10.6028/NBS.CIRC.539v1](https://doi.org/10.6028/NBS.CIRC.539v1).
The existing scoped NIST Technical Series reuse findings apply only to the
selected NBS-authored facts. Third-party comparison tables are not reproduced.
Republished courtesy of the National Institute of Standards and Technology.

The additional Nb fact is attributed to H. Watanabe (2026), *Thermophysical Properties of Niobium (1000–2700 K): Multi-stepwise Pulse-Heating Measurements with Consistency Validation via a Revised Emissivity–Resistivity Relation*,
International Journal of Thermophysics 47, 95,
[DOI 10.1007/s10765-026-03765-z](https://doi.org/10.1007/s10765-026-03765-z).
The retained parent inspection reports article-specific
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); local integration
does not claim a fresh inspection or independent rights certification.
Section 2.1.1 supplies the selected cylinder's density fact. Adaptations consist
of selected factual transcription, structured provenance, original scope and
missingness notes, and English fallback labels in four interface slots. The
numerical value is unchanged; source terms are not replaced by project MIT.
No endorsement, independent scientific review or engineering suitability is
implied. Final rights admission and a reviewed main release remain pending.

Only brief numerical facts, locators, attribution and original curation are
bundled. Source PDFs, figures, complete tables, supplements and raw structures
remain outside the repository. See [the integration record](MATERIAL_GROWTH_20261016.md).
