# Experimental offline CI

This is an independent, experimental-platform-only workflow. It does not replace,
relax, or modify `.github/workflows/ci.yml`, frozen v035 data, main release gates,
production admission, or scientific review. Its two jobs run only within the
experimental branch and path boundaries below. There are no schedules, provider
credentials, live integration jobs, deployments, external dataset uploads or
artifact publication steps.

## Coverage

Both jobs target Ubuntu 24.04 with CPython 3.11 and 3.12. Each matrix entry builds
local packages using a pinned build tool environment and installs their wheels
into a separate clean runtime. The suite minima are:

| Job | Suite | Minimum tests |
| --- | --- | ---: |
| `offline-fixtures-and-wheels` | Provider synthetic fixtures | 19 |
| `offline-fixtures-and-wheels` | Query API fixtures and mocked transport | 37 |
| `offline-fixtures-and-wheels` | Local lifecycle | 25 |
| `offline-fixtures-and-wheels` | Independent API/lifecycle and linked integration | 18 |
| `offline-fixtures-and-wheels` | NOMAD ingestion, incremental recovery and offline formal-review gaps | 106 |
| First job subtotal | | **205** |
| `optional-core-catalog` | Optional installed-core/computed catalog and private geometry diagnostics | 117 |
| `optional-core-catalog` | Formal catalog add-on | 11 |
| Second job subtotal | | **128** |
| **Required minimum across both jobs per interpreter** | | **333** |

These numbers are discovery requirements, not a claim that the current complete
suite has executed. The verification history below identifies actual results.

The first job builds four local wheels: federation, query service, lifecycle and
the umbrella platform. The catalog job builds those four plus the repository's
core and formal catalog add-on, for six local wheels. Query-service and umbrella
versions remain `0.5.0.dev0`, core remains `0.35.0`, and federation, lifecycle and
the formal add-on remain `0.1.0`. Core is built locally, not fetched from a
package index. The jobs also check:

- `pip check` after exact-pinned runtime and QA dependencies and local wheels.
- Exact LICENSE and THIRD_PARTY_NOTICES.md wheel bytes and License-File metadata.
- Installed CLI and in-process API smoke from outside the checkout, checking
  module origins, OpenAPI, synthetic MP demo, and disabled MP live path.
- Two installed linked-demo CLI executions with exact raw/typed/review binding,
  zero canonical/scientific-property admission, and byte-identical dataset.tar.
- Installed lifecycle CLI fixture capture and staging.
- All six catalog-job wheel licenses and installed module origins before the
  optional catalog and formal add-on suites.

The suite minima detect reduced discovery while allowing added tests.
[required_test_ids.json](required_test_ids.json) additionally pins **112 required
IDs**: 61 earlier ingestion tests, 19 offline formal-review-gap tests, four
baseline path-portability tests, six selected-group consistency regressions and
21 private-geometry diagnostic tests, plus one Retry-After
representability and restart regression. The catalog runner also requires the
geometry test module to exist. Those 21 geometry tests exercise the checkout-only
diagnostic CLI with synthetic inputs; they do not install it as a wheel entry
point or load private geometry.
Unrelated extra tests cannot replace those regressions merely by preserving the
count. Each suite prints its actual discovered IDs as a `DISCOVERED` JSON record. Discovery
errors, duplicate discovered IDs, missing required IDs, a reduced count or a
discovered test that does not execute all fail the check. Failures, errors, skips
and expected failures also fail the job. Matrix repetitions and separate
verification reruns do not increase the distinct-test total.

Some inherited independent tests explicitly import source; the separate installed
smoke ensures wheel-installed interfaces work without package-source imports.
API/TestClient checks are not a real browser, accessibility, mobile, deployed API,
or live-provider pass. Local demo archives are not published and are deleted with
the temporary directory. They remain non-self-contained raw replay bundles.

## Local equivalent

From the repository root on Linux with Python 3.11+:

```sh
python experimental/platform/ci/run_ci.py
python experimental/platform/ci/run_catalog_ci.py
```

To run only the new offline report regression module from the repository root:

```sh
python -m unittest discover -s experimental/platform/ingestion -p test_formal_review_gaps.py -v
```

That targeted command covers 19 tests. It is not the full 106-test ingestion
suite, the 333-test combined minimum, or either installed-wheel CI runner.

The checkout-only geometry diagnostic has a separate focused command:

```sh
python -m unittest discover -s experimental/platform/query-service/catalog-tests -p test_geometry_diagnostics.py -v
```

Its 21 synthetic tests also run as part of the catalog job's 117-test discovery.
The normal catalog runner requires every discovered test to execute, with no
skips or expected failures. A focused pass is not a complete 333-test matrix pass.

Run the two CI runner commands with each supported interpreter to reproduce the
matrix. Each creates fresh build and runtime virtual environments and removes
them on completion. Dependency installation needs package-index access. All external
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

Pushes run only on `experimental/platform-integration` and
`experiment/nomad-incremental-review` and `experiment/reviewed-subset-audit`;
pull requests run only when targeting one
of those exact branches. Both event types are additionally filtered to
`experimental/platform/**`, `formal-catalog/**`, `materials_boundaries/**`,
`pyproject.toml`, `LICENSE`, `THIRD_PARTY_NOTICES.md` and
`.github/workflows/experimental-platform.yml`. Changes outside those paths alone
do not trigger this workflow. Manual dispatch has no arbitrary inputs, and both
job guards restrict it to the same three exact branch refs. The token is
contents:read only; checkout does not retain credentials. Official checkout and
setup-python actions are pinned to verified full release commit SHAs. There is
no pull_request_target, untrusted event-text shell interpolation, self-hosted
runner, secret reference, or shell command generated from a provider response.

GitHub requires a workflow_dispatch workflow to exist on the default branch for
manual dispatch availability. Declaring it here does not promise the Run workflow
button on these experimental branches. These jobs remain scoped to the three
experimental refs; a scoped push or pull request is the activation path.
Do not make this path-filtered experimental job a main required check: skipped
workflows may leave required checks pending. Baseline CI still has its existing
broad triggers and may also run for the same push.

## Primary references

- [GitHub workflow syntax: paths, branches, permissions and dispatch](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [GitHub manual dispatch default-branch requirement](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [Checkout v6.0.2 verified commit](https://github.com/actions/checkout/commit/de0fac2e4500dabe0009e67214ff5f5447ce83dd)
- [Setup Python v6.2.0 verified commit](https://github.com/actions/setup-python/commit/a309ff8b426b58ec0e2a45f0f869d46889d02405)
- [pip repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/)

## Verification history and current scope

The completed Windows CPython 3.11 local regression covered all **286 distinct
tests**, with zero failures, errors or skips, including the rebuilt installed
query-service wheel and catalog/API checks. Exact results and the Linux
filesystem-only check are recorded in
[closure verification](../ingestion/VERIFICATION_CLOSURE.md). This is evidence for
the local suites; it does not assert that these Linux CI runners already passed.

After that local verification, the Ubuntu 24.04 Python 3.11/3.12 matrix passed
for incremental commit `094b7a02b639850e8eb2d4021de2a407d83aa454` in
[run 38101758476](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/38101758476).
Each interpreter executed 286 tests with zero skips. Those results apply to the
earlier incremental tree.

The subsequent selected-group revision
`681293c515707ff52974cbbae780d0099d84b5f7` passed the Ubuntu 24.04 Python 3.11/3.12
experimental matrix in
[run 38111418493](https://github.com/chaotic-mixture/materials-boundaries-public/actions/runs/38111418493),
with **292 tests per interpreter**. That result covers the six selected-group
regressions and remains evidence for that exact revision.

For the offline formal-review-gap revision, **19 targeted tests passed locally
with zero failures, errors or skips**. At that verification step the **311-test** set had
**NOT BEEN RERUN** locally or established by a new hosted matrix result in this
verification step. The prior 286/292 results and the new targeted result are
separate evidence; their arithmetic does not constitute a 311-test suite pass.
The existing three-branch trigger allowlist is unchanged by this report-tool
work, and no new branch activation was asserted by that step.

The subsequent private-geometry implementation passed **21 focused synthetic
tests**, with zero failures, errors or skips. Its CI integration adds those exact
IDs and raises the catalog minimum to 117, making that revision's combined minimum
332. This discovery contract does not retroactively expand earlier run results.
A subsequent local Windows CPython 3.11 integration check executed **117 local
catalog tests and 11 formal catalog tests**, all passing without skips, including
all 21 geometry tests. It reused existing wheels after matching all 102 package
files against source and installed bytes, with external networking blocked. The
other 204 tests were discovered only. This is not a fresh Linux build or a
332-test execution result.

Publication to the already listed `experiment/reviewed-subset-audit` branch uses
the existing workflow filters; this integration adds no branch, trigger or
permission. See [geometry diagnostics](../GEOMETRY_DIAGNOSTICS.md) for the
checkout-only command, fixed numerical criteria and held-output boundary.

Python 3.13/3.14 matrix expansion is deferred until the pinned binary dependency
set and full suite have been verified on those interpreters. Package metadata
states Python >=3.11; that alone is not evidence of tested compatibility.
