# Materials Boundaries small task contract

## One task one stopping point

A task must name one source family, one supported scientific contract, a closed set of selected records, one baseline commit and one stage. Prefer one source with a few explicitly enumerated formulations; split by uncertainty or contract, not by arbitrary token counts. The worker may finish less than requested with a precise blocker. It must not choose the next material, broaden a source search, change CI, publish, or start the next stage.

The coordinator fills `task-input.example.json` before execution. The schema and `dispatch_preflight.py` jointly check readiness; schema success alone is insufficient. The worker must refuse draft/archival inputs, placeholders or any failed preflight. A passing preflight never grants authority: require a current coordinator dispatch after the pause, with an exact selected stage. Exact read and write paths are required; a broad `scripts/**`, `tests/**` or whole-repository write allowance is not a small-task contract. If runtime integration genuinely needs more paths, the responsible engineer explains and obtains that scope before editing them.

### Nonnegotiable invariants

- Identity, grade, state, property, source and computed-composition counts are separate. A paper, translated label, test specimen, processing state or extra measurement is not automatically a new identity.
- Use the existing full quantity/unit/representation contract. Keep exact source number strings, statistics, measurement method and per-result conditions. Preserve explicit unknowns. New scientific/schema behavior is a separate senior-reviewed task.
- Every reference stays `catalog_only`, with `universal_bound: false` and `engineering_allowable: false`. Do not add calculator inputs or a ninth executable composite rule.
- Do not upgrade independent scientific review, raw-data reanalysis, translation review, standard compliance or reuse rights merely because validation passes.
- Existing scientific objects, ordering, source records, historical fixtures and candidate evidence remain unchanged unless a separately approved correction explicitly identifies them. Never rewrite a failure as a pass.
- No raw paper, screenshot, full table, article text dump, private local path or credential enters a repository/release artifact. Store audit assets outside the repository; use approved evidence references in handoffs.

## Gates and owners

| Gate | Responsible role | Required evidence | Exit and stop condition |
| --- | --- | --- | --- |
| G0 Assignment | Coordinator | Explicit authorization, current-stage closeout if resuming after pause, exact baseline/tree and data hashes, existing contract, allowed paths, expected outputs and check inventory | Issue one ready manifest or keep it blocked |
| G1 Candidate | Lower-cost worker | Authored packet spec, source/rights/identity evidence, four name slots, exact proposed deltas, immutable prepared packet and receipt | Candidate-ready or candidate-blocked; actual admitted delta remains zero |
| G2 Independent review | Reviewer not the packet author | Immutable packet/spec hashes, direct evidence cross-check, finite identity audit, rights scope, negative/unknown cases and reproduction evidence | Accept exact artifact, request bounded correction, or reject; any edit invalidates the old approval |
| G3 Runtime integration | Explicitly authorized integration engineer | G2 approval, pinned baseline, version-2 integration manifest, exact append diff and current count evidence | Local runtime candidate only; do not publish or advance counts on main |
| G4 Validation and implementation review | Engineer plus independent reviewer | Final code/input image, approved test inventory, exact outcomes, unchanged protected bytes, actual isolated wheel/CLI evidence | State precisely which scopes passed and what remains unrun; no substitute for required acceptance gates |
| G5 Publication | Coordinator with explicit authority | Before push: exact experimental target/ref, independent approval of exact commit/tree, completed required local validation, privacy/asset boundary and named expected CI | After authorized push: verify remote SHA and that SHA’s required jobs to terminal state. Push-triggered CI is not required to exist before push. Stop; main merge, release, deployment and DOI remain separate permissions |

The worker's checklist is useful error prevention, not G2 or independent implementation review. A reviewer can use a lower-cost model for deterministic cross-checks, but ambiguous identity, source rights, new contracts and disputed historical compatibility must be escalated to a responsible reviewer with adequate expertise.

## Source and identity evidence checklist

Use one row per fact or consequential decision in `source-review.json` or the selected existing evidence format. Do not invent another per-batch schema when an adequate format already exists.

- **Document**: title/authors/version, official URL/DOI, actual access route and date, retained-byte hash if bytes were inspected. Distinguish PDF, XML, HTML and indexed text. A source-record canonical hash is not a document hash.
- **Locator**: table/row/column and footnote for numbers; section/passage for method and composition; explicit join keys if facts span tables. If a locator is unknown, say so rather than filling a plausible page.
- **Fact**: original string/unit, comparator/range, central statistic, SD/SEM/CI identity, replicate count and whether independent batches are known. A preparation temperature is not a test temperature.
- **State**: material/formulation, ingredient versus finished-product grade, processing route, specimen and exact per-result conditions. Do not borrow geometry or conditioning from a cited standard or another property test.
- **Identity**: baseline inventory files and hashes searched; actual source→property→state→identity joins; aliases/designations and candidate-to-candidate collisions; existing/distinct/pending disposition with evidence and limits. Unknown additives do not prove non-equivalence. A finite absence search is not global chemical uniqueness.
- **Rights**: inspected article-specific license/notice, selected-content and third-party-credit scope, attribution and excluded assets. Availability, DOI or citation is not permission. Apply existing narrowly documented source profiles only when every condition matches; otherwise hold.
- **Review**: what the author actually inspected, what the independent reviewer actually inspected, unresolved facts and correction history. Do not copy predecessor review flags.

Reference: `docs/MATERIAL_REFERENCE_CATALOG.md` sections “What is counted”, “Evidence and interpretation”, and “Add a material without a new Python family”; `docs/FORMULATION_PACKET_PREPARATION.md`.

## Reproducible handoff

Freeze the candidate before G2. Supply: manifest, exact checkout commit/tree or dirty-patch digest, separately pinned catalog baseline commit/tree, input raw hashes, spec/packet hashes, short evidence decisions, all output paths/hashes, exact commands and environment, full logs or verified references, and remaining gates. A reviewed candidate checkout and its older catalog baseline may differ; do not collapse them into one SHA. Hashes identify bytes; they do not authenticate claims without the independently reviewed source and baseline.

The consumer must confirm that every supplied file actually exists and is readable in its own environment. A producer's workspace path is not a transfer. Use an approved transfer mechanism when needed, verify raw hashes after materialization, and preserve a retrieval failure as blocked. Do not silently fetch substitutes or reconstruct unavailable scientific evidence from prose.

For old packet replay, archive the three baseline catalog files from the pinned commit, not the current enlarged runtime data directory. Existing output must be byte-identical for idempotent reuse; a changed immutable output is an error, not an overwrite opportunity. The compiler's `handoff_ready` checks authored declarations and machine contracts; it does not constitute reviewer approval.

## Verified command catalog

**Reference only. Public availability of this kit does not authorize executing these commands.** All commands run from the repository root using the approved interpreter and already available dependencies. Uppercase path names and `YOUR_BATCH` are placeholders, not existing paths. The operator must resolve them and approve the exact `argv` list. Missing dependencies block execution; do not initiate downloads or install packages without authorization.

### Candidate preparation

Verified in `docs/FORMULATION_PACKET_PREPARATION.md` and `scripts/prepare_formulation_packet.py`:

```sh
python scripts/prepare_formulation_packet.py --spec experimental/material-batches/YOUR_BATCH/packet-spec.json --baseline-dir PATH_TO_PINNED_BASELINE_DATA --output experimental/material-batches/YOUR_BATCH/prepared-packet.json
```

The output directory must exist, and output must be outside baseline/runtime data and separate from the spec. Exact contract: `schema`, `batch_id`, `baseline_sha256`, `source_records`, `contexts`, `formulations`, `identity_crosswalk`, `review`; see the repository guide rather than copying the full spec into this envelope.

The existing generic compiler regression command is documented in the Ewurum candidate `VALIDATION.md`:

```sh
python -X utf8 -m unittest discover -s tests -p test_formulation_packet_preparation.py -v
```

This tests the compiler, not every new scientific selection. A new task also needs its approved exact candidate assertions/inventory; do not invent a generic batch runner or claim the historical Ewurum test covers new material facts.

### Local integration artifact

Verified in `docs/FORMULATION_PACKET_PREPARATION.md` and `scripts/integrate_material_candidates.py`:

```sh
python scripts/integrate_material_candidates.py --baseline-dir PATH_TO_PINNED_BASELINE_DATA --manifest experimental/material-batches/YOUR_INTEGRATION/integration.json --output PATH_TO_NEW_INTEGRATION_ARTIFACT.json
```

This creates an immutable combined catalog/report artifact; **it does not modify runtime catalogs**. Version 2 binds packet bytes and the same baseline, allows no status adjustments and replays the embedded spec. Any actual runtime append is a separately assigned exact diff, not an imagined `--publish` step.

### Repository acceptance checks

Verified in `CONTRIBUTING.md`:

```sh
python -m unittest discover -s tests -p test_release_metadata.py -v
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
python -m pip wheel --no-deps --wheel-dir dist .
python scripts/check_wheel_metadata.py dist/materials_boundaries-<version>-py3-none-any.whl
```

`<version>` is a placeholder read from the approved checkout, not a shell-ready token. The documented wheel command can require build dependencies/network; do not run it under an offline-only task. The already-documented offline six-wheel build used for Ewurum appears in `WORKED_EWURUM.md`; it requires a prepared build environment. The repository's release/acceptance requirements are not waived by this template. Focused development checks may run first, but cannot be relabelled as a full-root pass.

General Ubuntu production partitions require actual GitHub Actions context and eight matching receipts (two Python versions × four partitions), plus a successful aggregate. Do not forge Actions variables locally. The unchanged 70-method replay is a separate scope. Reference: `docs/CORE_PARTITION_CI_20261024.md` and actual workflows.

## Exact result accounting

Record one attempt per command; retain unsuccessful/interrupted attempts. `result.template.json` is the lightweight envelope; detailed ordered IDs and event lines can remain in hashed files.

- Pin actual commit/tree, clean/dirty state, exact patch and all relevant input hashes, interpreter/platform, dependency-lock hashes and wheel hashes. Recheck inputs after the command. A later edit invalidates affected results; equivalent inputs may be explained, not presented as a clean-HEAD run.
- Separate expected, discovered, started and completed method IDs. Separate passed, failed, errored, skipped, interrupted and unstarted/unknown. If evidence cannot distinguish unstarted from interrupted, record unknown rather than guessing.
- Count executions across reruns separately from distinct IDs. Root coverage is the intersection of completed distinct IDs and the frozen root inventory. Subtests, CLI outputs, script checks and simulated outcomes are not extra unittest methods.
- A count without exact inventory/completion evidence is insufficient. Missing logs, terminal markers or required matrix receipts mean incomplete, not pass. Preserve exact allowed skip IDs/reasons; do not relax skips to fit the result.
- Record CLI cases by language, command/format, source selection and equality semantics. Canonical output order is part of the oracle when established; never sort actual output to make an assertion pass. Record smoke scripts separately from test methods.
- State validation reach: candidate only, scoped source, full root, installed packages, hosted platforms, source-transcription review, raw source bytes and publication. These are independent claims.

## Failure and escalation decision tree

1. **Wrong baseline, missing file, changed hash or ambiguous worktree?** Stop dependent work. Report expected/observed identity and preserve the artifact. Coordinator reissues/rebases the task; do not silently repin.
2. **Unknown chemistry, grade, statistic, rights or scientific contract?** Keep unknown/pending. If the current supported contract can represent it faithfully, ask the reviewer to decide; otherwise escalate. Never weaken schema/guards or infer facts to pass.
3. **Access denied or credential/CAPTCHA requirement?** Stop that action. Report exact action, target, reason, completed work and denied/pending/uncertain state. If execution is uncertain, inspect status first. After a denial, at most one retry with materially new relevant evidence and only where policy permits; no executor switch, alternate route or security-setting change to bypass a restriction.
4. **Validation failure with authorized narrow repair?** Preserve the failure, diagnose exact input and assertion, make only the allowed correction, invalidate affected evidence, repeat approved affected checks. If the repair touches historical adapters, CI, shared validators or unapproved files, escalate before editing.
5. **Timeout, unexpected scope/cost growth or full-suite cancellation?** Preserve partial IDs/logs. No blind full rerun, automatic retry storm, silent test dropping or new historical projection layer. A maintainer selects the necessary complete affected scope; any CI redesign is a separate task.
6. **Remote write status uncertain?** Read target ref/job before retrying. A publication failure does not authorize another destination, merge or release.

The preflight is a finite accidental-error guard, not a sandbox or general command-security validator. It never executes a listed argv; passing it does not certify what arbitrary script/build internals will do. The coordinator must review the literal argv and rely on the execution environment’s actual permissions.

Every blocker handoff ends with: `action | target | expected vs observed | completed work | dependent work paused | specific decision needed`. Safe independent inspection may continue; blocked dependent work must not.

## Cost discipline without weaker evidence

Observed at the pinned snapshot: 23 `scripts/run_*ci.py` files; 96 files matching history/preservation names under `tests`; 1,887 frozen root IDs; general Ubuntu runs previously hit six hours. These are structural warning signs, not proof that every file is unnecessary. Ewurum required 370 scoped executions/366 distinct methods, 577 installed methods and separate wheel smoke despite adding only four identities.

For each new task:

- Start with manifest + relevant contract sections + one worked example + selected evidence. Read an index/grep before opening long ledgers. Do not paste all chat history, whole source text or all prior batch docs into every worker context.
- Reuse the unchanged compiler and manifest-v2 lane. Worker additions should be data/evidence and narrowly justified tests. Do not make a cloned runner/workflow/historical inventory projection the standard output of a batch.
- Coordinator obtains a dependency-based test selection before expensive work. During iteration, run approved focused checks; at the final immutable image, run the complete required acceptance scopes once. Do not suppress required full acceptance to save money.
- Treat a change requiring many historical bindings as a maintainer escalation, not routine low-cost-model work. Preserve existing historical assertions; a separate design may later reduce coupling, but this kit neither implements nor authorizes it.
- Report estimated and actual wall time, iterations and changed-path count. Stop for a new scope decision when the agreed budget is exhausted; do not invent passing outcomes. A cost cap cannot terminate an already-authorized external process without accounting for its actual state.

At stage completion, write one concise handoff and stop. No next-batch research, recurring schedule, background watcher or publication is implied. Public readers inherit no private account access or standing authorization.
