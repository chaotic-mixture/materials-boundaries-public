# v0.28.2: composite source-metadata correction

This release corrects source evidence for the existing eight composite rules.
It adds no model, formula, data family, assumption, dependency, unit, numerical
policy or applicability gate. Instance 1.0.0, evaluation 1.1.0, composite-report
1.0.0 and all scientific catalog schemas remain unchanged.

## Corrected evidence and retained limits

- The `reuss_shear` locator and corresponding Kochmann–Milton note now correctly
  identify arXiv:1401.4142v1 section 4.4 equations (132)–(133), printed/PDF p. 20,
  as translated **bulk**-compliance relations. Equation (133) does not display
  the unshifted shear Reuss formula. The implementation retains contextual
  evidence from the introduction and `standard_formula_with_context_source`;
  an original Reuss equation locator has not been established.
- Meille–Garboczi equation (3), printed p. 374 / PDF p. 4, and its cover were
  visually checked on **2026-10-04** in the NIST-hosted publisher-typeset PDF.
  The source record and the two derived claims now record that completed check
  alongside the earlier extracted-text check, superseding the prior failed
  render attempt without backdating it. The original curation date remains.
  Only the 3D isotropic identities are used; the separate 2D equation (4) is not
  imported. The source record preserves the inspected file's format, page and
  byte counts and SHA256. No source PDF or rendered image is bundled.
- Only the two derived claims' obsolete visual-not-checked gaps are removed.
  Their `algebraic_derivation_from_cited_identities` classification and all
  remaining evidence qualifications stay in place. The E/ν corner construction
  and monotonicity reasoning remain project derivations, without a claim of
  joint attainability or sharpness.
- Hashin–Shtrikman (1963) retains historical attribution only, with original
  equation and proof locations uninspected and original locators null. The
  bounded unsuccessful search does not establish that no lawful copy exists.
  Applicability still relies on supplied assertions, not verified physical
  microstructure. All eight claims retain `software_tested_not_peer_reviewed`
  and `independent_scientific_review=false`.
- Reading and identity transcription do not constitute independent expert or
  proof review, source authentication or a grant of reuse rights. Existing
  copyright/license metadata and metadata-only distribution limits remain;
  NIST hosting does not grant permission to redistribute the article.

The nine approved evidence-field corrections affect three claim records and
two source records. The affected claims `reuss_shear`, `youngs_modulus_outer`
and `poissons_ratio_outer` separately receive patch versions **1.1.1** (formerly
1.1.0) to identify the revised metadata. Other claim versions do not change.
Sources have no record-version field; the dated correction, canonical record
digests and software release identify their successors. Historical snapshots
remain historical and are not rewritten to imply an earlier successful review.
The four new read-status labels coexist with the old labels for historical data;
four-language current report wording reflects the dated identity-only check.
Machine-assisted wording has not received independent native-language review.

The machine-readable [dated correction ledger](../tests/fixtures/source_evidence_correction_v0282.json)
records the nine exact before/after fields, the three separate version patches,
source-version/locator/hash evidence and complete predecessor/successor record
digests. The [compatibility tail](../tests/fixtures/source_evidence_updates_v0282.json)
records exact reversible integration edits against v0.28.1; all earlier fixture
bytes and review dates remain intact. These are current software/source-curation
checks, not retrospective scientific review.

## Existing reports fail strict current replay

Composite bundles embed complete claim and source snapshots and their hashes.
Correcting a locator, reading status or gap changes that contract even when
every number is identical. Version 0.28.2 also changes `engine_version`; the three claim-version
patches occur in catalog snapshots and comparison-series metadata, not in the
raw evaluator rows. Strict replay with the updated
installation therefore rejects an old bundle as **stale**; `composite verify`
returns exit code **4** for a well-shaped stale core. Public report rendering
also validates first. Schema validity or matching old file hashes alone does
not make an old bundle current.

There is **no automatic migration**, compatibility acceptance of stale report
provenance, or in-place hash repair. Do not change an old bundle's embedded
snapshots, versions or digests to make it pass. Preserve the entire old export
as a historical artifact; its original environment can replay its historical
contract without turning the old source statements into current evidence.

Explicitly regenerate a new report from the unchanged **original input** and
choose the same output unit and language for comparison. For example:

```sh
python -m materials_boundaries composite report old-report/input.json --output regenerated-report-0.28.2 --unit GPa --lang en
python -m materials_boundaries composite verify regenerated-report-0.28.2/bundle.json --json
```

The output must be a new or empty directory whose parent already exists. Use
the existing filesystem safeguards; do not overwrite the old export. If the
original input is unavailable, do not infer it from displayed endpoints or
silently replace missing evidence.

Regeneration recomputes the catalog digests, bundle digest, report text/HTML,
artifact hashes and manifest. The original input content and all numerical
endpoints, checks and availability states are unchanged for the same input and
output unit. Raw evaluation bytes change only through the software version label; their
rows contain no claim-version field and remain exactly unchanged. Catalog
snapshots and comparison series identify the three claim-version patches.
These are not numerical or scientific-model changes. Compare
every saved artifact's byte count and SHA256 with its new manifest, then replay
the new bundle. Successful replay establishes software reproduction only,
not physical-sample verification, theorem validity or scientific certification.

See [the current workflow](COMPOSITE_WORKFLOW.md), [model](MODEL.md) and
[source evidence](SOURCES.md) for the unchanged scientific and rights limits.
