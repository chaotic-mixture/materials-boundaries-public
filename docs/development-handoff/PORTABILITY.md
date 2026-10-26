# Synthetic fixture portability correction

This corrects the local handoff-kit check harness from commit `f8c83a08868594f7dc27bf5ea490f645b19b811a`. It does not change `dispatch_preflight.py`, its schema, strict baseline hashing, material records, runtime behavior or workflows. A native Windows rerun of the correction is still required; Linux Git-setting emulation is not Windows certification.

## Preserved failure

The original harness was reported to execute **45 cases on Windows: 40 reported passes and 5 failures**. The resolved-interpreter-alias condition did not apply, so no 46th case ran. All five intended positive controls failed at `Baseline bytes mismatch: materials`; 20 cases reached that same early gate. The old harness accepted any rejection for a negative case, so those early failures did not establish the intended later rejection coverage.

The publisher's byte diagnostic found `{}` followed by CRLF in the temporary worktree (`7b7d0d0a`), but LF in its Git blob (`7b7d0a`). Windows text-mode `write_text()` generated CRLF while the existing `core.autocrlf=true` normalized the committed blob. Original Windows logs remain with the publisher; this summary does not claim to reproduce or replace that native run.

## Narrow correction

- All owned synthetic fixture writes use explicit UTF-8 bytes. Authored LF bytes are not translated by platform text mode. Expected baseline hashes still come from the actual fixture bytes and must match the committed bytes; no production hash is normalized or repinned to conceal a mismatch.
- Every negative case has a fixed expected rejection: schema validator plus instance location, or exception type plus the specific gate message. A different earlier rejection fails the case.
- A negative case is certified only when its matching positive control succeeds and fixture bytes match the Git baseline. Deliberately injecting the old CRLF writer now produces failures rather than misleading negative-case passes.
- The inventory always lists **46 planned cases**. The `cases` count includes only executions. If the interpreter has no distinct resolved alias target, that one case is `not_applicable`, with `passed: null`; it is not an executed pass. Thus a valid run may have **45 passes and 1 not-applicable case**, or **46 passes and none not applicable**.

No global Git configuration is changed. The CRLF profile uses process-scoped Git configuration for disposable synthetic repositories only. The normal runner uses the caller's existing configuration.

## Actual correction evidence

| Local profile | Planned | Executed | Passed | Failed | Not applicable | Certified negative gates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Linux CPython 3.12.14, existing Git settings | 46 | 46 | 46 | 0 | 0 | 41 |
| Linux, process-scoped `core.autocrlf=true`, `core.eol=crlf` | 46 | 46 | 46 | 0 | 0 | 41 |
| Linux, provisioned direct interpreter with no distinct alias target | 46 | 45 | 45 | 0 | 1 | 40 |

All three profiles passed their five positive controls and had zero unexpected-gate rejections. The direct-interpreter profile is a controlled test of the applicability branch, not advice to substitute a base interpreter for a task's required virtual environment.

An intentionally faulty temporary copy replaced the corrected fixture writer with CRLF emission under the CRLF Git settings. It exited with failure: 46 executions, zero passes, all five positive controls failed and zero certified negative gates. This confirms that an unrelated baseline failure cannot masquerade as successful negative coverage. It is an expected fault experiment, not a passing product test.

Exact profile outcomes and hashes are in [the portability validation record](portability-validation.json), [the default Linux outcomes](preflight-case-results.json), [the CRLF Git-setting outcomes](preflight-case-results-autocrlf.json) and [the non-alias outcomes](preflight-case-results-no-alias.json). The unbundled native Windows failure and the Linux emulation are explicitly separate evidence.

Run the corrected harness only in an authorized environment with existing development dependencies. Use the same pinned kit checkout and selected interpreter described in [onboarding](ONBOARDING.md). Record the actual planned/executed/not-applicable counts and intended-gate results; never require a fixed 46 executions on every platform or interpret a denial from the wrong gate as success.
