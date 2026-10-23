# Tarasov candidate integration handoff

This document hands the next implementation stage to the dot execution
environment. It is an acceptance plan, not a record of runtime admission or
permission to publish. Parent review of the candidate must precede the five-row
runtime append. Use the existing packet, merge, history and package mechanisms;
no new ingestion platform, scientific schema or property API is needed.

## Immutable inputs and present status

- Runtime baseline: `faa002c55b7ad2d1bd962e905275894231ab8350`.
- Candidate source-packet commit: `eb044bb024dff2a99c514605d3942a1769f77f80`.
- Integration manifest: [integration.json](integration.json), schema
  `experimental-material-integration/2`, with the candidate commit and the
  exact baseline hashes. Keep `status_adjustments` empty.
- Prepared packet: [prepared-packet.json](prepared-packet.json), raw SHA-256
  `e9096077c7d6a206cf3a54a14272f838722187e10481588a1e3c07e5ab345997`.
- Review evidence: [source-review.json](source-review.json),
  [identity-review.json](identity-review.json), and
  [integration-report.json](integration-report.json). The latter describes a
  detached candidate graph, not the current product catalog.
- Execution evidence: [VALIDATION.md](VALIDATION.md) and
  [validation-results.json](validation-results.json). These are the authority
  for terminal test and wheel-smoke results; inspect them at the final handoff
  commit rather than infer completion from a running process.

The source-packet commit predates the validation tests, manifest, reports and
this handoff document. The parent must freeze those artifacts in a subsequent
reviewed handoff commit and provide its exact SHA before dot continues. Checking
out `eb044bb` alone does not supply every later validation artifact.

At preparation of this handoff, the candidate phase has 39 distinct focused
tests passed: 12 new packet tests and 27 existing preparation, integration,
append-merge and release-metadata tests, with zero failures, errors or skips
in the final runs. Baseline and detached-candidate strict
catalog validation, immutable preparation/integration replay, and core wheel
build/payload inspection passed. The separate native fresh-installed core-wheel
smoke reached its 900-second timeout without terminal success and is not passed.
The verified task-owned worker was stopped and no retry was started. Use the
final validation receipt for exact evidence; a bounded dot rerun remains required
before publication acceptance. Preserve this timeout, the earlier unsuccessful
Windows hard-link attempts and discovery-decoding attempt in the receipts.

Discovery found 1,743 core methods; the other 1,704 were not executed in this
candidate phase. All 535 methods in the existing eight full installed groups
were also not run. A successful core-wheel smoke would not replace those
groups. Previous Bruns CI results do not validate the Tarasov change, and no
Tarasov hosted CI result is claimed here.

The actual runtime remains 1,148 source-qualified identities plus 24 reviewed
computed records, giving 1,172 experimental project identities. Source-qualified
categories remain metal 32, inorganic 53, polymer 25, composite 28 and natural
1,010. Main remains 1,081, and 62 computed examples remain excluded.
`formal_admitted_delta` remains zero in this candidate packet and its report.

## Reproduce the candidate without changing runtime data

Use the final parent-delivered checkout containing the manifest and validation
artifacts. These one-line commands work in a Linux shell or Windows PowerShell
with Git and the repository development Python environment. `-X utf8` is
intentional. Do not install dependencies merely because an interpreter is
missing; select or provision the approved development environment first.

```sh
git rev-parse HEAD
git status --short
git merge-base --is-ancestor faa002c55b7ad2d1bd962e905275894231ab8350 HEAD
git merge-base --is-ancestor eb044bb024dff2a99c514605d3942a1769f77f80 HEAD
git worktree add --detach ../materials-boundaries-tarasov-baseline-faa002c faa002c55b7ad2d1bd962e905275894231ab8350
python -X utf8 -c "from pathlib import Path; Path('../materials-boundaries-tarasov-review-output').mkdir(exist_ok=True)"
python -X utf8 scripts/prepare_formulation_packet.py --spec experimental/material-batches/tarasov-pna-bpf-20261023/packet-spec.json --baseline-dir ../materials-boundaries-tarasov-baseline-faa002c/materials_boundaries/data --output ../materials-boundaries-tarasov-review-output/prepared-packet-replay.json
python -X utf8 -c "from pathlib import Path; assert Path('../materials-boundaries-tarasov-review-output/prepared-packet-replay.json').read_bytes() == Path('experimental/material-batches/tarasov-pna-bpf-20261023/prepared-packet.json').read_bytes(); print('Exact prepared-packet bytes match')"
python -X utf8 scripts/integrate_material_candidates.py --manifest experimental/material-batches/tarasov-pna-bpf-20261023/integration.json --baseline-dir ../materials-boundaries-tarasov-baseline-faa002c/materials_boundaries/data --output ../materials-boundaries-tarasov-review-output/integration-package.json
```

The two sibling paths are task-owned examples, not disposable existing user
directories. If either already exists, inspect its provenance and pending
processes before reuse; do not overwrite or delete it. An existing baseline
worktree can be reused after verifying its exact HEAD and clean catalog bytes.
The integration package stays outside the repository because it duplicates the
full catalog. Repeating the same writer command is an idempotence check only
after the previous process has reached a known terminal outcome; identical
outputs must preserve bytes and modification time. A changed existing output
must be refused. Do not silently rebind old packets to later runtime data.

To reproduce the five complete focused modules when needed on dot:

```sh
python -X utf8 -m unittest discover -s tests -p test_tarasov_pna_bpf_packet.py -v
python -X utf8 -m unittest discover -s tests -p test_formulation_packet_preparation.py -v
python -X utf8 -m unittest discover -s tests -p test_formulation_packet_integration.py -v
python -X utf8 -m unittest discover -s tests -p test_material_append_merge.py -v
python -X utf8 -m unittest discover -s tests -p test_release_metadata.py -v
```

Record platform, interpreter, exact commit, actual started/passed/failed/error/
skipped counts and log hashes. These commands describe reproducibility; they
were not rerun while authoring this document. A Windows hard-link permission
failure remains a failed execution, not a successful or conditionally skipped
test. Use supported task execution with hard-link support without changing the
writer, weakening assertions or changing system settings.

## Approved append and history preservation

After parent approval, work in a new isolated branch/worktree from the final
handoff commit. Preserve the candidate artifacts and their historical zero
admission statements. Record the later integration decision and result in new
dated evidence rather than rewriting candidate history.

1. Replay `integration.json` against the exact faa002c baseline. Reuse
   `scripts/integrate_material_candidates.py::build_package` and
   `materials_boundaries/material_references.py::merge_material_catalogs`.
   The existing integrator deliberately does not write runtime catalogs.
2. Apply only the approved append tables to
   `materials_boundaries/data/materials.json`, `reference_properties.json`,
   and `sources.json`. Preserve every predecessor record, its order and its
   recoverable byte image. Do not change computation reviews, scientific
   claims, schemas, source review flags, relationship membership or APIs.
3. Add exact frozen data and file ledgers, for example
   `tests/fixtures/tarasov_pna_bpf_data_20261023.json` and
   `tests/fixtures/tarasov_pna_bpf_files_20261023.json`. These are proposed
   successor files, not existing artifacts. Pin the packet, ordered added IDs,
   predecessor/current hashes and reversible documentation/workflow edits.
4. Prepend one explicit descriptor in
   `tests/material_append_successors.py::FROZEN_SUCCESSORS`. Reuse
   `tests/material_append_history.py::recover_catalogs`, `recover_file`,
   `project_catalog_chain`, `project_catalog_bytes_chain` and
   `project_file_chain`. The existing successor wrappers are
   `project_successor_catalogs`, `project_successor_catalog_bytes` and
   `project_successor_file`; pass a named historical boundary where required.
5. Retain every previous ledger and hash. Data chronology is Tarasov, Bruns,
   Nylon, then older material batches. File chronology additionally places
   the adjacency-only workflow change between Bruns and Nylon; it is not a
   material admission. Preserve the separate finite documentation call-site
   bridge used by full-chain recovery.

Acceptance requires exact predecessor recovery, unchanged predecessor IDs and
facts, deterministic repeat merge with no second delta, and rejection of
partial, reordered, substituted, duplicated or count-preserving rewritten
appends. The accepted result must have exactly the five approved identity IDs,
five states, five properties, zero grades and one source added. Only after that
separate implementation and review could counts become 1,153 source-qualified
identities plus the same 24 computed records, or 1,177 experimental project
identities; polymer would become 30. Counts for grades, states, properties and
sources must be read from the validated graph rather than used as identity
counts. Main and the 62 excluded examples stay unchanged.

## Keep Bruns assertions attached to their original checkpoint

Do not globally replace old 1,148/1,172 literals or loosen hash checks. The
following current files contain assumptions that Bruns is the newest batch.
Line positions are hints from faa002c; use the named methods when later edits
move them.

| Existing path and entry point | Required successor handling |
| --- | --- |
| `tests/test_bruns_borosilicate_packet.py`, `setUpClass` around line 49 | Project newer accepted data with `project_successor_catalogs(current, before=BRUNS_BATCH_ID)` before strict Bruns recovery. Keep the four source rows, counts and hashes unchanged. |
| `tests/test_bruns_borosilicate_preservation.py`, `setUpClass` around line 24 | Apply the same checkpoint projection before `recover_catalogs`; preserve original byte equality and scientific assertions. |
| The same preservation module: `test_exact_append_and_predecessor_bytes_keep_all_existing_materials`, `test_file_ledger_restores_exact_readme_and_workflow_and_rejects_drift`, `test_finite_registry_preserves_every_preexisting_descriptor_and_boundary` | Replace positional latest-batch views (`[0]`, `[1:]`, formerly empty `file_ledgers(before=Bruns)`) with explicit historical-boundary views. Keep all old descriptors and rejection cases. |
| `tests/test_bruns_borosilicate_ci.py`, workflow/inventory/payload/targeted-inventory tests around lines 20, 98, 124 and 290 | Supply narrowly pinned historical workflow, resource and inventory views. New files/test IDs must not invalidate the old contract or be hidden by changing historical expected values. |
| `tests/test_family_adjacency_ci.py` and `tests/test_family_adjacency_history.py` | Project newer file successors before undoing Bruns and the adjacency-only edit. Preserve exact old workflow bytes, data invariance and drift rejection. |
| `experimental/platform/query-service/catalog-tests/test_baseline_compatibility.py`: `bruns_descriptor`, `recover_pre_bruns_catalogs`, `recover_bruns_anchor` | Add the newer exact recovery layer before the existing Bruns anchor. Keep its historical manifest, record digests and failure cases. |
| `experimental/platform/query-service/catalog-tests/test_catalog_baseline.py` | Preserve the current Bruns anchor as a named predecessor; advance only the explicitly current anchor. |
| `experimental/platform/query-service/catalog-tests/test_bruns_borosilicate.py` | Advance assertions explicitly about live aggregate counts; retain all four exact Bruns object/property assertions. Historical snapshots keep historical totals. |

The new `tests/test_tarasov_pna_bpf_packet.py` must likewise continue to replay
its fixed faa002c baseline after runtime integration. Recover that baseline
through the approved successor ledger rather than alter the source oracle or
substitute newer input pins.

README and notice text require an additional exact recovery view.
`tests/material_bulk_preservation.py::truthful_readme` first checks actual live
counts and normalizes them; its caller then invokes
`tests/legacy_document_recovery.py::project_legacy_document_bytes` on a complete
normalized document image. New prose requires a precisely pinned successor for
that normalized image. Reversing raw README totals first would make the live
count check compare a predecessor number with a successor catalog. Preserve
the old normalizer, seven historical document ledgers and code-call-site
ledgers, including the helper hash protected by
`tests/test_legacy_document_recovery.py`. Do not broaden matching rules or
rewrite old text merely to make recovery succeed.

Carry forward both portability fixes: Git `commit:path` paths use
`.relative_to(ROOT).as_posix()`; CLI subprocesses explicitly use `-X utf8` and
`encoding='utf-8'`. An isolated `-I` interpreter ignores `PYTHONUTF8`, so an
environment variable alone does not preserve the CLI encoding contract.

## Product pins and predecessor stores

| Current product surface | Next-stage acceptance |
| --- | --- |
| `formal-catalog/materials_project_catalog/catalog.py::RESOURCE_SHA256` | Advance only the three appended catalog resource pins. Preserve `formal_computed_review.json` bytes, hash, 24-record policy and derived count behavior. |
| `experimental/platform/query-service/materials_query/pins/legacy_baseline.json` | Regenerate the existing exact 64-file manifest, changing only resources actually changed by the approved append. Retain predecessor manifests for recovery. |
| `experimental/platform/query-service/materials_query/computed_registry.py` | Advance `BASELINE_PIN` and the two explicitly current legacy-count literals. Do not promote computed examples or alter reviewed computation payloads. |
| `experimental/platform/ingestion/nomad_review_boundary.py` | Advance the data-integration commit, material hash, `LEGACY_COUNT` and `PROJECT_TOTAL`. The pin names the actual data-append commit, not an arbitrary later CI commit. |
| Ingestion overlap/review/incremental tests, especially `experimental/platform/ingestion/test_nomad_incremental.py` | Add the Bruns predecessor-store case: status/report/compare remain read-only; mutation must reject the stale boundary. Do not silently migrate or edit existing user stores. |
| Formal/query/combined/computed/family/adjacency and hBN projection tests | Update assertions explicitly about the current aggregate graph; preserve dated fixtures and exact historical records. Existing `formal_overlap_audit.py::load_inventory` needs no new production branch. |

Add installed query/CLI/formal tests for the five exact approved objects,
classification and source/state/property links, defensive copies and current
counts. Preserve exact unknowns, discrepancies and qualifications already in
the packet. Do not propagate properties or relationship membership. Update
`experimental/platform/ci/required_test_ids.json` for every new platform test
ID, with no removed predecessor IDs.

Run `python -X utf8 scripts/validate_catalogs.py` in the eventual integration
checkout, then affected complete modules and history chains. CONTRIBUTING's
full-suite expectation remains distinct from a deliberately bounded CI run:
report every full-suite case not executed; do not call selective success a
full-suite pass. Packaging checks use `tests/test_release_metadata.py` and
`scripts/check_wheel_metadata.py`; there is no `tests/test_pyproject.py` here.

## New bounded CI profile and fresh installation

Implement one batch profile, proposed as `scripts/run_tarasov_pna_bpf_ci.py`,
using `scripts/run_bruns_borosilicate_ci.py` as the contract reference. Reuse
`scripts/run_evidence_batch_ci.py` helpers (`ExactResult`, `PACKAGES`,
`clean_env`, `install_offline_guard`, `installed_origins`, `test_ids`,
`verify_wheels`, `run` and hash checks) and existing workflow/build validation
helpers. Avoid copying a second ingestion service or weakening the inherited
offline/installed checks.

The new profile must pin the base commit, candidate packet, approved changed
paths, runtime hashes, manifests, append IDs/counts, full sorted test-ID
inventories and complete-module targeted selection. Guard the exact approved
experimental branch and event/head SHA in `.github/workflows/ci.yml`; preserve
all older job bodies and only add the reviewed branch condition. Preserve the
Bruns profile's historical assertions through the checkpoint views above.

Discover fresh inventories after all implementation tests are written. The
candidate's 1,743 core methods and the predecessor's 131 targeted / 1,731 core /
535 installed numbers are evidence for their own trees, not target constants
for the new profile. Freeze the actual new IDs and fingerprints, retain every
existing method, and report separately targeted, not-run, allowed-skipped,
failed and errored cases. Exact permitted skips must keep their original IDs
and reasons; no source skip exemption applies to installed groups.

Require the six current project wheels, built from the exact reviewed tree,
and the existing locked offline dependencies. Verify wheel metadata, exact
catalog/pin bytes and absence of raw assets, candidate files and credentials.
Create a fresh isolated environment outside the checkout, install those wheels
with `--no-index --no-deps`, run `pip check`, and assert that imports originate
inside that environment. Run all eight complete groups: query, formal,
ingestion, relationships, provider, transport, lifecycle and integration.
Keep the independent installed smoke and its final completion marker.

The following is the required interface for the proposed new runner, not an
existing executable in this candidate checkout. After its implementation and
scope review, use the same one-line commands on Linux and Windows:

```sh
python -X utf8 scripts/run_tarasov_pna_bpf_ci.py --validate-scope
python -X utf8 scripts/run_tarasov_pna_bpf_ci.py --targeted-core
python -X utf8 scripts/run_tarasov_pna_bpf_ci.py --wheel-dir PATH_TO_EXACT_SIX_WHEELS --dependency-dir PATH_TO_LOCKED_DEPENDENCY_WHEELS
```

Resolve both wheel placeholders to inspected local directories. The profile
must retain a separate `--test` full-core mode; the targeted command must not
claim that mode was executed. Measure actual wall time before choosing a hosted
budget rather than inherit Bruns's timeout or minimum passing counts blindly.

For eventual authorized experimental publication, verify the exact remote
branch SHA and terminal Linux/Windows CI for that SHA. Decode the real logs:
each actual COMPLETE record must reconcile discovered, started, passed,
skipped, failed and errored cases. A synthetic marker printed by a runner unit
test is not the final installed completion marker. Missing, silent, timed-out
or merely queued work is not a pass. Preserve original failed attempts and
record corrective commits separately. Main merge, deployment and DOI actions
remain outside this handoff.

## Dot transfer and stop conditions

Supply dot the reviewed code/docs/curated-data commit or a verified code-only
Git bundle/patch with its baseline, exact SHA/hash and file list. Verify actual
consumer-local bytes before importing; a path from another environment is not
evidence that a file exists locally. Include validation receipts and the status
of any live process, and inspect uncertain outcomes before retrying. Do not
transfer credentials, original PDFs, rendered pages, extracted full source
text, private notes or the full detached duplicate catalog.

Software replay uses the curated packet and frozen Git baseline. Any unresolved
source question returns to the parent source review; unavailable raw assets do
not justify invented evidence. Stop dependent admission work on a source or
identity conflict, unexpected predecessor-byte drift, missing required test,
resource exhaustion or failed package/CI check. Report the exact blocker and
completed scope. The current candidate and earlier runtime remain intact until
the separately reviewed integration is complete.
