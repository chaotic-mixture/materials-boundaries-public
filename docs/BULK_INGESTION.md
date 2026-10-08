# Offline staged bulk ingestion

This workflow is source-separated and table-driven. It never discovers arbitrary
research files or automatically promotes candidate rows to the runtime catalog.
New adapters require scientific, identity, provenance and rights review.

## Trust boundaries

1. A registered `SourceProfile` pins its adapter/version, complete release-file-
   license registry digest, allowed source-license policy and semantic validator
2. `stage_batch(batch, baseline=..., profiles=...)` validates candidates and
   records `proposed`, `held` or `source_supported` dispositions. It admits zero
3. An independent review supplies a digest and an explicit approved identity-key
   set. `admit_batch` replays staging and requires that independently supplied
   digest. Never read the trusted digest from the untrusted approval itself
4. An adapter materializes append-only catalog tables from a replay-valid
   admission. The wood adapter also requires the independent digest at this step
5. `merge_material_catalogs` merges approved append tables in memory. It preserves
   existing order/records, sorts new IDs, treats exact existing records as an
   idempotent rerun, and rejects conflicting IDs or canonical duplicate identities
6. A release build runs schema, scientific, historical-output, source-fidelity,
   broad mixed and installed-wheel checks before publication

The digest is a review-workflow boundary, not a digital signature. A caller with
permission to change the trusted code or supply a trusted digest remains
responsible for the actual review decision. Candidate-provided `reviewed` or
`admitted` labels do not grant approval.

## Data tables and preservation

A batch contains `registry` (releases, files, licenses), `materials`,
`observations` and `exclusions`. Material identity keys are separate from state,
accession, observation, derivation and alias identities. Conflicting rows for a
canonical identity quarantine together. Exact repeated rows cannot inflate
coverage. Reordering tables and unordered aliases/evidence leaves the staged
package unchanged; adding duplicate rows still changes the bound input digest.

Numeric measurements use bounded fixed-point strings, never binary floats,
NaN or Infinity. Original numeric/source strings remain intact in metadata.
`verify_source_files` checks complete file IDs, exact lengths and SHA-256 over
original bytes without decoding or replacing invalid text. Source-specific
parsers must explicitly handle encoding anomalies and preserve relevant fields.

Every graph operation validates actual inputs afresh. There is no global cache
of graph acceptance. Batch resolution validates once for its entire selection
and returns detached views. The source adapter rechecks packaged registry bytes
at every public operation before using its verified parsed metadata.

## First adapter: exact reviewed wood v2

The only registered production adapter initially accepts the exact reviewed
1,000-row CIRAD/GWDD source batch. The source batch hash, 33-entry dossier manifest,
review decision, original source caches and taxonomic dependencies are verified
before mapping. Per-row review pins prevent even plausible within-tolerance
numeric or taxonomy substitutions from inheriting the review decision.

Stage without admission:

```sh
python scripts/import_reviewed_wood.py \
  --dossier-dir PATH_TO_FROZEN_V2_DOSSIER \
  --review-dir PATH_TO_INDEPENDENT_V2_REVIEW \
  --output-dir PATH_TO_NEW_STAGE_DIRECTORY
```

This exports `wood-batch.json` and `wood-staged.json`. They are review artifacts,
not runtime catalog counts. Full source CSV/backbone/PDF caches remain external.
The reusable generic stage CLI additionally requires an explicit canonical
baseline JSON file:

```sh
python scripts/stage_material_batch.py batch.json \
  --baseline baseline.json --output staged.json
```

The later import invocation may additionally use `--approval approval.json` and
`--expected-review-digest DIGEST_FROM_INDEPENDENT_REVIEW`. It emits an admission
package and append tables to a separate directory, never overwrites production
catalogs, and refuses different existing output bytes. Approval JSON contains
`decision`, `reviewer`, `review_manifest_sha256` and `approved_identity_keys`.
Archive the exact approved digest/key set and canonical baseline snapshot alongside
the final source manifest. The review digest intentionally changes if the baseline
changes. After integrating the batch, reproducing the old approval therefore uses
the archived pre-admission baseline via `--baseline-materials`; it must not silently
substitute the enlarged live catalog. Reapplying already-approved append tables
through `merge_material_catalogs` is independently idempotent.

The source-supported preview API is explicitly labeled unadmitted and exists
only for pre-admission fidelity/display review. It cannot become quota evidence.
Original research status fields may remain in historical metadata; current
stage/admission status is the separate top-level disposition.

## Inspection and export

Canonical catalog subsets are dependency-bearing records, not self-contained
research archives. A source-complete inspection uses
`resolve_material(state_id, materials, properties, sources)` or the batch
`resolve_materials` API. These return identity, state, properties and all
referenced source records, including original/deposited files, grant evidence,
method citations and source-specific attribution. Keep the source registry and
admission/source manifest with a reusable exported audit package.

See [the scientific design](BULK_INGESTION_DESIGN.md),
[the biological-tissue taxonomy](MATERIAL_TAXONOMY.md), and
[third-party notices](../THIRD_PARTY_NOTICES.md).
