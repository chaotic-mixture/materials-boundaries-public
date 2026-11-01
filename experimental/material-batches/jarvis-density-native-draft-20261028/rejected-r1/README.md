# JARVIS native mapping and computational-density method draft

**Unadmitted, unapplied and pending independent review.** This batch maps the
already source-reviewed 2,000 facts into native-shaped catalogs. It does not
modify live runtime data or change quota counts. There are 1,000 metal category
proposals and 1,000 inorganic category proposals, not approved identities.

The prior five-alloy batch has now closed its local gates; its exact accepted
catalog hashes still match this draft's preparation baseline. No commit, push,
main merge or deployment was performed.

## Frozen inputs and output

- [Source-fact selection review](../jarvis-density-candidates-20261027/REVIEW_STATUS.md).
- [native-candidate.json](native-candidate.json), SHA-256
  `58de2ef4ab0ba6b87101fa4b9daf14f4460369e7ebbb3f5c29e0f55faeee4e20`.
- [Four-file isolated implementation patch](implementation.patch) and
  [original/draft hashes](draft-manifest.json). The method uses computational
  evidence with crystallographic density and preserves the old measured-input
  derivation branch. Four language labels are included; translation remains
  machine assisted, without scientific translation review.
- [Producer validation](VALIDATION.json) binds each artifact and scoped log.

Kamal Choudhary, [JARVIS-DFT Figshare v11](https://doi.org/10.6084/m9.figshare.6815699.v11),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Changes: selected factual fields structured into proposed catalogs, conservative
composition grouping and minimum-numeric-JID selection, unknown conditions
retained. No endorsement is implied. Dataset rights are separate from software
rights; parent database IDs are citations, not redistributed parent assets.

## Identity and source boundaries

Identity IDs derive from the exact reduced composition key, not source row
counts, JID counts or property values. One composition proposes one identity;
selected JID, functional, source space group, parent reference, fixed release,
member digest and exact raw-row digest bind its state. Space group alone does
not identify a complete structure. Unselected alternate phases do not create
additional quota entries or imply chemical equivalence.

Final classification remains unresolved: all-metal composition alone does not
prove metallic electronic behavior (including Mg2Sn and ZrNiSn). A proposed
category field in a structurally valid preview does not settle that question.
The current 24 formal computed compositions and conservative current-catalog
formula/element-set guards remain excluded as in the reviewed source selection.

Original density tokens are preserved. Units follow official method/code
documentation; the JSON row itself contains no explicit unit string. No density
was recomputed. Temperature, pressure, convergence, stability, uncertainty,
sample count and experimental existence remain unknown. A model is not an
independent physical specimen, and the scalar is not relabelled as a mean.

## Checks and remaining gates

Six producer preview tests, ten new-method contract tests and 29 original
contract tests passed with zero failures/errors/skips in the isolated r2 stage.
The preview validated all 2,000 proposed records and a complete in-memory
baseline-plus-draft graph without modifying the baseline. It did not call the
admitted quota reporter on that unapproved graph. The eight language/kind
renders used an explicitly mocked catalog reader, not an installed CLI.

Independent native mapping, final identity/taxonomy and implementation review
are not run. Runtime historical preservation, full regression, real installed
checks and integration are not run for this method. The earlier Sanchez full
regression does not certify these new files. `handoff_ready=false` and
`admitted_increment=0` remain in force.

```powershell
python -B build_native_draft.py --output native-candidate.json
python -B test_native_preview.py --stage PATH_TO_ISOLATED_R2_STAGE -v
```
