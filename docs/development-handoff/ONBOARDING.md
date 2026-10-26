# Start a bounded Materials Boundaries task

This public kit lets a new person or agent reconstruct the handoff contract. It does **not** give access to private evidence, another user's accounts, credentials, source rights or authority to resume material development. The published kit is not itself a dispatched task. First obtain the coordinator's current instruction and exact target stage.

The installation location used below is `docs/development-handoff/`. Run project commands from the repository root. Full Git history is required for pinned baseline/history checks; a shallow export or source ZIP is insufficient. Commands containing `REPLACE_...` are templates and must not be executed unchanged.

## Obtain the exact checkout

Keep the **pinned kit checkout separate from the task checkout**. An older task commit may predate this kit; checking it out in the kit directory would remove the preflight files. From an approved parent task workspace, with permission to access the public repository:

```sh
git clone https://github.com/chaotic-mixture/materials-boundaries-public.git materials-boundaries-kit
git -C materials-boundaries-kit checkout --detach REPLACE_APPROVED_KIT_COMMIT
git -C materials-boundaries-kit rev-parse HEAD
git clone https://github.com/chaotic-mixture/materials-boundaries-public.git materials-boundaries-task
cd materials-boundaries-task
git checkout --detach REPLACE_APPROVED_TASK_COMMIT
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git status --porcelain
```

The coordinator must identify the full kit commit and the task's checkout and catalog-baseline commits. They may differ. Preserve the kit checkout unchanged and invoke its script by the sibling path shown below. Do not substitute main, a moving branch tip or the historical worked-example SHA. Stop if a referenced object is unavailable. No protected-resource access, push, release or credential change is implied by cloning.

Clone/checkout and environment creation are standard Git/Python bootstrap steps added by this guide, not project validation performed during kit authoring. Project dependencies and acceptance commands are grounded in `pyproject.toml`, `CONTRIBUTING.md` and pinned repository documents.

## Choose an explicit development interpreter

At snapshot `437950c414ea340eda340babe7b63dee9fcee535`, Python **3.10+** is required, build tooling requires **setuptools>=68**, and the development extra requires **jsonschema[format-nongpl]>=4.18,<5**. The installed core runtime has no third-party dependencies. Read the selected checkout's `pyproject.toml` again if it differs.

Create a disposable environment with an already installed compatible Python. These are optional bootstrap operations requiring permission to write the environment; dependency installation may use the network and requires separate approval. They are not worker-manifest check commands.

POSIX:

```sh
python -m venv .venv
./.venv/bin/python -m pip install -e '.[dev]'
```

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
```

If network/install access is unavailable, use a preprovisioned compatible interpreter with the complete development extra and build requirements already available. Do not silently install, switch interpreters or bypass an access denial. The platform installed-wheel caches in `experimental/platform/requirements-lock.txt` and `experimental/platform/ci/projection-requirements.txt` are separate; they are **not** a complete replacement for the catalog validator's development format-checker dependencies. A plain `jsonschema` import alone does not establish that required URI format checks are installed.

Record the consumer-local absolute interpreter invocation path, `sys.prefix` as `python_prefix`, and absolute repository cwd in `execution`. Do not resolve a venv interpreter symlink to its base executable: that can silently discard the venv dependencies. The guard checks the invocation path without dereferencing symlinks and checks the running prefix. Invoke preflight with that same interpreter; `python` from an unknown PATH is deliberately insufficient for a ready command. No private environment path is supplied or required by this kit. A bootstrap-only read can show the two exact values (this is not a supported task-check argv):

```sh
./.venv/bin/python -c "import sys; print(sys.executable); print(sys.prefix)"
```

In PowerShell use `.\.venv\Scripts\python.exe` with the same `-c` argument. Keep the printed invocation path; do not replace it with a resolved base-Python symlink target.

## Prepare one ready manifest

Copy `task-input.example.json` to a coordinator-selected task location. It is deliberately non-dispatchable. Fill:

- Exact checkout and baseline commits/trees, baseline catalog hashes and selected source/record IDs.
- `assignee_id` for the current worker and `artifact_author_id` for the artifact under review. Independent review requires different identities and the named reviewer assignment.
- Actual current authority references and allowed action **enum values** for this one stage. A reference is not proof of authority; the coordinator verifies its provenance outside this file.
- Exact normalized repository-relative read/write/output files. No wildcards, traversal, whole directories or missing output coverage. Keep private primary-source assets outside the repository, within the approved task workspace.
- Consumer-local paths, raw hashes and roles for required inputs. At least one input must actually be required. Candidate gates require exactly one required `candidate_packet`; later implementation gates also require one `implementation_subject`. Other roles are `source_evidence`, `test_inventory` and `other`. `consumer_path` is absolute or relative to `--workspace`; repository read/write/output paths are relative to `execution.cwd`.
- Pre-existing dependency policy, limits and fully qualified Python `argv` string arrays. Do not embed shell quoting inside an argument: each array member is one literal argument, including Windows paths containing spaces/backslashes. Classify each as `script`, `unittest` or `build`. Build entries use the documented no-index/no-deps/no-build-isolation flags and preinstalled tooling. This is a finite argument-shape check, not a network sandbox or proof of build-script behavior; the coordinator must review the exact arguments and the execution environment must enforce its real permissions.
- For each unittest command: a hashed inventory JSON file plus `inventory_json_pointer` selecting exactly one nonempty, unique method-ID array. Empty pointer means the file's root is that array. Counts or a receipt containing several attempts without a selector do not suffice. Runtime execution must still reconcile the actual discovered/completed IDs with that selection.
- Independent approval receipts for later gates. Runtime integration/validation/implementation review require candidate approval; publication additionally requires implementation approval for the exact checkout commit/tree.


Supported action values are stage-specific; free text cannot add new capabilities:

| Stage | Allowed action values |
| --- | --- |
| candidate | `read_inputs`, `write_candidate`, `run_approved_checks` |
| independent candidate or implementation review | `read_inputs`, `write_review`, `run_approved_checks` |
| runtime integration | `read_inputs`, `write_runtime`, `run_approved_checks` |
| validation | `read_inputs`, `write_validation`, `run_approved_checks` |
| publication | `read_inputs`, `push_exact_reviewed_commit`, `observe_remote_and_ci`, `write_validation` |

An approval descriptor in `independent_review.approval_receipts` has `stage`, repository-relative `path`, receipt raw SHA-256 and `subject_sha256`. The receipt itself has this minimal shape:

```json
{
  "decision": "accept",
  "stage": "candidate",
  "reviewer_id": "REPLACE_INDEPENDENT_REVIEWER",
  "author_id": "REPLACE_ARTIFACT_AUTHOR",
  "subject_sha256": "REPLACE_REQUIRED_INPUT_RAW_SHA256",
  "commit": "REPLACE_REVIEWED_COMMIT",
  "tree": "REPLACE_REVIEWED_TREE"
}
```

`stage` is `candidate` or `implementation`; only a real independent reviewer can issue acceptance. The candidate descriptor must bind the exact required `candidate_packet`, not an unrelated evidence file. The implementation descriptor must bind the exact required `implementation_subject`. That subject is a JSON manifest containing at least `commit`, `tree` and `author_id`; all must match the current checkout and declared implementation author. The implementation approval must name the same commit/tree/author. Preserve richer findings and limitations alongside these minimal fields. A hash and two different names do not authenticate a reviewer: the coordinator must confirm who produced the receipt and what was actually inspected. Copying or fabricating an acceptance file does not satisfy the human gate.

After all unresolved items are closed, the coordinator may set `status` to `ready`. `draft` and `archival` must never be dispatched. The worked Ewurum input is archival and intentionally fails dispatch even though it passes structural schema validation.

## Run the read only preflight

With existing development dependencies, from the repository root:

```sh
./.venv/bin/python ../materials-boundaries-kit/docs/development-handoff/dispatch_preflight.py REPLACE_READY_TASK.json --workspace ..
```

PowerShell equivalent:

```powershell
.\.venv\Scripts\python.exe ..\materials-boundaries-kit\docs\development-handoff\dispatch_preflight.py REPLACE_READY_TASK.json --workspace ..
```

`--workspace ..` refers to the approved parent directory containing both sibling checkouts and any separate audit input directory. `execution.cwd` remains the absolute task-checkout directory, not the kit directory. Adjust these paths only to the actual approved layout. Preflight never downloads files, installs dependencies, creates pipeline work, executes task commands or publishes. It only reads files and performs fixed read-only Git identity/baseline checks. It fails closed on missing dependencies, malformed JSON, wrong identity/hash, missing approval and unresolved readiness.

The guard catches accidental handoff mistakes; it is not a sandbox, general command-security validator, authentication mechanism or substitute for independently reviewing the literal argv and selected scripts. It accepts only named Python scripts, `-m unittest`, and `-m pip wheel` check entrypoints (with optional `-B` / `-X utf8`). It does not prove that arbitrary script internals are safe.

A successful result contains `dispatch_ready: true`, **`authorization_verified: false`** and `commands_executed: 0`. Require actual current coordinator authorization before using the selected role prompt. Never treat a successful schema check alone as a dispatch decision.

The optional `check_preflight_cases.py` checks the kit using disposable synthetic local Git fixtures; it does not run Materials Boundaries tests or task commands. Its results are a guard regression check, not a scientific, project-CI or permission certificate.

## Complete only the assigned stage

Use `PROMPTS.md` and `TASK_CONTRACT.md`; return `result.template.json` with real evidence and stop. Candidate workers never publish. Independent reviewers never fix their own reviewed artifact. A subsequent stage requires a new assignment.

For an explicitly authorized experimental publication, pre-push gates are the exact reviewed image, local acceptance, target and authority. Push-triggered hosted CI is checked **after** push: verify the remote commit, named expected workflows/jobs and terminal results for that exact SHA. An unavailable/failed job is not a pass. No main merge, tag/release, deployment or DOI is authorized by this kit. New materials remain paused until the coordinator explicitly resumes them.
