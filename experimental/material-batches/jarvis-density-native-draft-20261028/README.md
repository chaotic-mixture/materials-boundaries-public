# JARVIS native mapping and computational-density method draft

**Independently reviewed; local working integration present; final acceptance pending.** This batch maps the
already source-reviewed 2,000 facts into native-shaped catalogs. It does not
establish final accepted quota counts. There are 1,000 metal category
proposals and 1,000 inorganic proposals, now approved within the finite
source-qualified hypothetical-model identity and compositional category scope.
This does not approve runtime admission.

The prior five-alloy batch has closed its local gates; its exact accepted
catalog hashes bind this draft's archived preparation baseline. The current
working graph has advanced to include the pending JARVIS integration. No commit, push,
main merge or deployment was performed.

## Frozen inputs and output

- [Source-fact selection review](../jarvis-density-candidates-20261027/REVIEW_STATUS.md).
- [native-candidate.json](native-candidate.json), SHA-256
  `82a2d8332f934b31567cac4d50960871792841321a94bd4357500604f6184e85`.
- [Four-file isolated implementation patch](implementation.patch) and
  [original/draft hashes](draft-manifest.json), now applied locally. The method uses computational
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

The [frozen identity/taxonomy sidecar](identity-taxonomy-decisions.json) received
scoped independent approval under the existing finite project convention:
source-qualified hypothetical computed crystal model identity, one exact
reduced-composition bucket, and compositional metal-family membership.
All-metal composition does not prove metallic electronic behavior (including
Mg2Sn and ZrNiSn); electronic behavior remains unknown. This is a project
classification and model-identity decision, not an experimental existence or
cross-provider phase-equivalence claim. The sidecar retains its original
producer-stage status as frozen evidence; the later decision is recorded in
[independent-review-r1.json](independent-review-r1.json).
The current 24 formal computed compositions and conservative current-catalog
formula/element-set guards remain excluded as in the reviewed source selection.

Original density tokens are preserved. Units follow official method/code
documentation; the JSON row itself contains no explicit unit string. No density
was recomputed. Temperature, pressure, convergence, stability, uncertainty,
sample count and experimental existence remain unknown. A model is not an
independent physical specimen, and the scalar is not relabelled as a mean.

## Checks and remaining gates

Nine revised producer preview tests, ten new-method contract tests and 29 original
contract tests passed with zero failures/errors/skips in the isolated r2 stage.
The preview validated all 2,000 proposed records and a complete in-memory
baseline-plus-draft graph without modifying the baseline. It did not call the
admitted quota reporter on that unapproved graph. The eight language/kind
renders used an explicitly mocked catalog reader, not an installed CLI.

The first independent review approved the four-file isolated implementation and
finite identity/taxonomy sidecar, but rejected the original native mapping:
all 2,000 locators labelled a zero-based index as one-based. The corrected r2
uses index + 1; an exhaustive locator test and a rejected-r1 negative regression
now pass. The original JSON is losslessly archived as
[rejected-r1/native-candidate.json.gz](rejected-r1/native-candidate.json.gz), with
its original hashes and source files retained. The
[independent r2 recheck](independent-review-r2.json) approved the repaired mapping:
all 10,000 repeated locators across 2,000 candidates are correct, and the only
byte changes from r1 are the record numbers incremented by one. Four read-only
local checks passed, with no failures or skips.

Current live integration, focused historical and installed results are recorded
in [the integration report](INTEGRATION_VALIDATION.md). The full-root regression
is running; its final aggregate remains unknown. Earlier Sanchez full regression
does not certify these new files. The original candidate's `handoff_ready=false`
and `admitted_increment=0` remain frozen stage evidence; final acceptance is
tracked separately and remains pending.

## Isolated compiler preparation

The unchanged generic compiler expanded the reviewed native mapping and explicit
identity crosswalk, then replayed the complete packet exactly in the isolated
method implementation. Its output catalogs equal the approved native graph.
The [preparation receipt](packet-preparation-validation.json) pins the external
spec, packet, implementation manifest and archive. A lossless copy is retained
as [prepared-packet.json.gz](prepared-packet.json.gz); decompress and check its
recorded SHA-256 before use.

The compiler's `report.handoff_ready=true` covers its finite source/identity
preparation checks only. It does not close the separate historical recovery,
runtime integration, full regression, installed or admission gates. This batch
still admits zero. The packet's original review metadata states these pending
gates explicitly.

The [independent packet review](independent-packet-review.json) also approved
this finite preparation scope: all 2,000 crosswalks/formulations, original
source/baseline/implementation hashes, exact native catalog equality and complete
in-memory compiler replay passed. The compiler and integrator helpers remain
byte-identical to current HEAD. This does not close any runtime admission gate.

## Prospective exact history recovery

An isolated integration image and [data history ledger](data-history-preview.json)
now exist outside the live checkout. The
[independent data review](independent-data-history-review.json) approved the
finite data-layer checks: every baseline object, order and root metadata is
retained; generic merge replay and idempotence pass; exact recovery returns the
1180-identity baseline bytes and then the adjacent 1175 checkpoint. Seven graph
mutation cases and three raw-whitespace images are rejected.

The independently counted **prospective** graph has 3180 identities, 31 grades,
3181 states, 3197 properties and 131 sources; categories would be metal 1037,
inorganic 1059, polymer 37, composite 37 and natural 1010. These are unadmitted
preview counts, not current quota evidence.

Separate [file](file-history-preview.json) and
[normalized-document](document-history-preview.json) recovery previews cover
the four method/schema/locale files plus prospective README and notices.
Producer checks recovered six exact file predecessors and two normalized
document predecessors, rejecting 18 unknown file images and six unknown
document images. The
[combined independent history-preview review](independent-history-preview-review.json)
approved these finite data, file and document recovery checks, including the
three overlapping file and two document ledger adjacencies. This preview phase
left live data/code unchanged. Subsequent registry/helper wiring and local
integration are now independently reviewed; scoped history and installed checks
passed, while full-root regression is running. Final admission remains open.

```powershell
python -B build_native_draft.py --output native-candidate.json
python -B test_native_preview.py --stage PATH_TO_ISOLATED_R2_STAGE -v
python -B prepare_packet_draft.py --stage PATH_TO_ISOLATED_R2_STAGE --output-dir FRESH_EXTERNAL_SOURCE_CACHE_DIRECTORY
python -B build_integration_history_preview.py --stage PATH_TO_ISOLATED_R2_STAGE --output-dir FRESH_EXTERNAL_HISTORY_PREVIEW
python -B build_file_history_preview.py --stage PATH_TO_ISOLATED_R2_STAGE --preview EXTERNAL_HISTORY_PREVIEW
```

Preparation commands above were executed against their frozen predecessor
snapshot. Reproduction after integration requires that archived baseline; current
live catalogs deliberately fail their original preparation-baseline guards.
