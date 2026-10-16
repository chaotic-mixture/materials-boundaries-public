# Executed validation

Base: `4c5656cf6ba0ad1a54b736e0568e97abe4815c29`. All results below concern the isolated four-candidate packet. Production catalogs, schemas, the admission manifest and the existing NBS3/Nb1 candidates were not changed.

## Final execution on 2026-10-15 UTC

The frozen candidate validator SHA-256 is `2cb89a5683bb780acf5e2488b21214408f9b54ff38daff97577461f6ea796d0f`. A separate capture process ran it once after source corrections and static review, using Python 3.11 and jsonschema 4.26.0. Actual timestamps, precise dependency versions, per-check results, input hashes and log digest are in `validation-results.json`.

| Executed scope | Actual result |
| --- | --- |
| Candidate validation | 34 checks passed; 0 failed; 0 skipped |
| Included negative checks | 19 passed: 11 generic contract rejections, 2 merge conflicts, 6 source-fact guard rejections |
| Existing material reference contract suite | 26 tests passed; 0 failed; 0 skipped |
| Existing append-merge suite | 4 tests passed; 0 failed; 0 skipped |
| Early-failure reporting probe | Passed: a deliberately absent packet returned exit 1, one reported failure and unknown remaining/skip count |

The early-failure probe is an intentional invalid invocation, not a failed candidate-data test. It verifies that an exception before ordinary checks cannot look like a successful zero-failure/zero-skip run. Developmental executions are retained privately and excluded from the final totals.

Three candidate JSON schemas and the existing runtime graph contract passed. Six baseline catalog/schema byte digests were pinned to the base commit. The reused source object equals the existing source exactly. The final execution took approximately 8.59 seconds, exited 0 and emitted no stderr. A Python audit hook was loaded before the validation child to reject writes, filesystem mutations, network calls and subprocesses. It supplements the executor sandbox; it is not an OS security boundary. The capture process independently verified all 560 then-present tracked/candidate files remained byte-identical during both validation invocations; only afterward did that process write the result receipt and this document.

## Disposable merge results

| Count | Baseline | First in-memory merge | Repeated merge delta |
| --- | ---: | ---: | ---: |
| Composition identities | 1057 | 1061 | 0 |
| Qualified grades | 20 | 20 | 0 |
| Material states | 1057 | 1061 | 0 |
| Reference properties | 1057 | 1061 | 0 |
| Bibliographic sources | 114 | 114 | 0 |

The repeated merged graph was exactly equal. Existing record order/content, input objects and watched disk files were preserved. These are transient software rehearsal counts, not an admitted release. The formal total remains 1081 and formal admitted delta remains **0**.

Generic negative cases cover missing property linkage, incompatible units, missing/unknown source or unregistered URL, absent inspection date, unsupported specimen counts and reported means, uncertainty without its required envelope, relabeled structural identity/state clones, and conflicting existing property/source records.

The six factual mutations deliberately pass generic schema/runtime checks before separate packet-specific guards reject them: assigning a lattice/pattern temperature to NaF density; assigning KI's preparation temperature to its density; inventing density uncertainty from lattice error; asserting proven water-free KI; assigning a weight-percent basis to BaF2 impurities; and coherently relabeling the crystallographic result as direct bulk measurement. These guards check selected reviewed facts and wording. They do not inspect source pages, prove all prose correct or provide a general chemical-equivalence detector.

## Independent review and remaining scope

Independent source-packet review found two corrections, both resolved before final validation: NaF's structure locator needed printed p. 64 / PDF p. 68, and the review needed explicit identity-audit receipt bindings. It then confirmed source mapping, honest unknowns, original-source reuse and absence of source assets or credentials. A separate static review checked the validator's data flow, exception reporting, generic/source-specific separation and idempotent merge logic. Neither review is independent human scientific review or final source-specific rights approval.

The actual selected-page inspection also corrected KI's supplier to B. R. Elk & Company and retained KBr's literal face-centered cubic description. Private receipts are bound by SHA-256 in `review.json` or the local handoff manifest; source images remain outside the repository packet.

No transcription/schema hold remains. Independent scientific review, source-specific rights review, parent-thread patch review and any future formal-admission decision remain pending. Publication remains paused. No upload, push, DOI registration, public deployment, raw-structure transfer, credential creation or permission change occurred.

The full release suite, remote CI and live provider/API reads were **not run for this packet**. The parent-tracked CI run was not duplicated. The earlier NBS3/Nb1 checks are not counted as new tests. The two bounded regression commands and the stdout-only candidate validator are documented in `README.md`; the CLI alone does not regenerate caller-captured timing/audit metadata or execute those separate suites.
