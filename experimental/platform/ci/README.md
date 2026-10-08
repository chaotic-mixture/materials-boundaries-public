# Experimental offline CI

This is an independent, experimental-platform-only test job. It does not replace,
relax, or modify `.github/workflows/ci.yml`, frozen v035 data, main release gates,
production admission, or scientific review. Applying this proposal and activating
GitHub Actions requires separate approval. There are no schedules, provider
credentials, live integration jobs, deployments, external dataset uploads, or
artifact publication steps.

## Coverage

The job targets Ubuntu 24.04 and CPython 3.11 and 3.12. Every matrix
entry builds the same four local packages using a pinned build tool environment,
installs only their wheels into a separate clean virtual environment, and runs:

- `pip check` after exact-pinned runtime and QA dependencies and local wheels.
- Exact LICENSE and THIRD_PARTY_NOTICES.md wheel bytes and License-File metadata.
- Provider synthetic fixtures: minimum 19 tests, no live provider verification.
- Query API fixture/mocked transport tests: minimum 21 tests.
- Local lifecycle tests: minimum 25 tests.
- Independent API/lifecycle and linked-demo tests: minimum 18 tests.
- Installed CLI and in-process API smoke from outside the checkout, checking
  module origins, OpenAPI, synthetic MP demo, and disabled MP live path.
- Two installed linked-demo CLI executions with exact raw/typed/review binding,
  zero canonical/scientific-property admission, and byte-identical dataset.tar.
- Installed lifecycle CLI fixture capture and staging.

The 83-test minimum is split by suite to catch accidental discovery loss while
allowing new tests. Failures, errors, skips and expected failures fail the job.
Some inherited independent tests explicitly import source; the separate installed
smoke ensures wheel-installed interfaces work without package-source imports.
API/TestClient checks are not a real browser, accessibility, mobile, deployed API,
or live-provider pass. Local demo archives are not published and are deleted with
the temporary directory. They remain non-self-contained raw replay bundles.

## Local equivalent

From the repository root on Linux with Python 3.11+:

```sh
python experimental/platform/ci/run_ci.py
```

Run that command separately with each supported interpreter to reproduce the
matrix. It creates fresh build and runtime virtual environments and removes them
on completion. Dependency installation needs package-index access. All external
runtime/QA versions come from the existing requirements-lock.txt; build tools and
packaging are pinned in build-requirements.txt. `--no-deps` prevents unpinned
transitive resolution, `--only-binary=:all:` refuses external source builds, and
`pip check` fails on missing/incompatible dependencies. Local wheels build with
`--no-build-isolation` so the pinned backend is used. This is version-pinned
reproducibility, not a hash-locked, cross-platform supply-chain guarantee. Python
patch releases and hosted runner images are not immutable.

After installation, a required sitecustomize audit hook blocks Python socket
connect/DNS/sendto events in test and CLI subprocesses. Its DNS fail-closed check
runs in every verification process. This catches accidental live requests; it is
not a security sandbox for malicious code. No provider key is configured, and
known inherited MP key environment variables are removed. Dependency downloads
are deliberately outside this fixture-only guard.

## Trigger and trust boundaries

Pushes run only on `experimental/platform-integration`; pull requests run only
when targeting that branch. Both are additionally filtered to changes under
`experimental/platform/**` or the new workflow file. Other production changes
alone do not trigger this job. Manual dispatch has no arbitrary inputs, and its
job guard also restricts execution to the experimental branch. The token is
contents:read only; checkout does not retain credentials. Official checkout and
setup-python actions are pinned to verified full release commit SHAs. There is
no pull_request_target, untrusted event-text shell interpolation, self-hosted
runner, secret reference, or shell command generated from a provider response.

GitHub requires a workflow_dispatch workflow to exist on the default branch for
manual dispatch availability. Declaring it here does not promise the Run workflow
button on this experimental-only branch. Do not add it to main just to enable
that button without separate approval; scoped pushes/PRs are the activation path.
Do not make this path-filtered experimental job a main required check: skipped
workflows may leave required checks pending. Baseline CI still has its existing
broad triggers and may also run for the same push.

## Primary references

- [GitHub workflow syntax: paths, branches, permissions and dispatch](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub manual dispatch default-branch requirement](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [Checkout v6.0.2 verified commit](https://github.com/actions/checkout/commit/de0fac2e4500dabe0009e67214ff5f5447ce83dd)
- [Setup Python v6.2.0 verified commit](https://github.com/actions/setup-python/commit/a309ff8b426b58ec0e2a45f0f869d46889d02405)
- [pip repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/)

Real GitHub execution is still needed to verify event/path filtering, token
permissions, hosted image/action compatibility, setup-python availability and
both matrix environments. Local YAML parsing validates structure, not
GitHub's scheduler or expression engine.

Python 3.13/3.14 matrix expansion is deferred until the pinned binary dependency
set and full suite have been verified on those interpreters. Package metadata
states Python >=3.11; that alone is not evidence of tested compatibility.


## Proposed prerelease catalog extension

Query-service and umbrella-platform wheels are now expected at 0.2.0.dev0; federation/lifecycle remain 0.1.0. The original four-wheel job preserves all83 tests, zero-skips checks and existing assertions. Only those two exact wheel-version expectations change.

The separate optional-core-catalog job builds this repository root locally as core0.35.0 alongside those four wheels, installs them into a fresh isolated runtime, checks all five wheel licenses and installed imports, applies the existing offline socket guard, and runs query-service/catalog-tests: 21 tests with no skips or expected failures. Core is never fetched from a package index. The two jobs cover104 tests together.

Both proposed runners passed locally on Python3.12.14. Python3.11, remote Actions runs, browser rendering, live providers, production acceptance and deployment remain pending or outside scope. No original83 green result alone validates the added snapshot integration.
