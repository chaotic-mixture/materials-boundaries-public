# Delgado PLA/PCL experimental runtime validation

This report records local runtime integration of the seven independently
reviewed nominal PLA/PCL formulations from candidate 73a5d872c210bbde5b3c0548d710869e87626691.
The exact tested implementation is 4565e2358020fac9b23afa331bf78afdb15de2a9, tree 484ee535d0cbdd72c847e4041872b62ad6888472.
A later evidence-only commit may add this document and runtime-validation-results.json;
it must preserve all 68 implementation hashes recorded in that JSON.

## Result and boundary

The local experimental catalog contains **1199 = 1175 source-qualified identities
+ 24 unchanged reviewed computed records**. The exact append adds seven polymer
identities, seven injection-molded states, seven measured Young moduli and one
source, with no new grades. Published experimental scope remains 1192 at report
preparation; main remains 1081. No push, main merge, deployment, DOI registration
or new credential creation is part of this report.

| Category | Local source-qualified identities | Gap to 1000 |
|---|---:|---:|
| Natural | 1010 | 0 |
| Metal | 32 | 968 |
| Inorganic | 59 | 941 |
| Polymer | 37 | 963 |
| Composite | 37 | 963 |

The 62 unadmitted computed examples remain excluded. Candidate rows, states,
repeated measurements and test executions are not additional materials.

## Source and interpretation

Delgado-Aguilar et al., [DOI 10.3390/ma13112655](https://doi.org/10.3390/ma13112655),
provides the seven nominal PLA/PCL ratios and original experimental Table 2
Young moduli under article-specific CC BY 4.0. Values remain in **GPa**. The
source identifies absolute SD but does not state central aggregation or sample
count. The records retain reported_measures, summary_statistic not_stated and
unknown sample count; no mean, SEM, confidence or final composition assay is
inferred. Preparation conflicts, tensile unknowns, attribution and the
source-qualified identity limitations remain intact.

Official PMC HTML and Europe PMC XML support the selected content. The producer
recorded their hashes; independent candidate review did not independently
reverify those raw source bytes or PDF bytes. The PDF route returned CAPTCHA
and was not bypassed. No PDF pixels, PDF/HTML equivalence, independent scientific
replication or raw-data reanalysis is claimed. Finite catalog deduplication is
bounded by incompletely disclosed existing commercial PLA products.

## Accepted producer execution

Producer execution used **native Windows CPython 3.11.0**. Each full protocol
was one successful orchestrator invocation with fresh group processes. These
are grouped executions, not one uninterrupted unittest process. Each group
requires exact discovered, started and passed IDs. Skips, fixture errors,
subtest failures, expected failures, unexpected successes and incomplete
results cannot produce a successful completion record.

The final source protocol passed **439 method executions / 435 distinct
methods**, zero failures, errors or skips, in 2509.000
seconds of outer process time. Four methods overlap the replay profile.

| Source group | Passed | Failures | Errors | Skips |
|---|---:|---:|---:|---:|
| candidate | 22 | 0 | 0 | 0 |
| preservation | 15 | 0 | 0 | 0 |
| contracts | 17 | 0 | 0 | 0 |
| compatibility | 156 | 0 | 0 | 0 |
| partition-contracts | 50 | 0 | 0 | 0 |
| prior-candidate | 20 | 0 | 0 | 0 |
| prior-preservation | 12 | 0 | 0 | 0 |
| prior-contracts | 17 | 0 | 0 | 0 |
| curaua-candidate | 18 | 0 | 0 | 0 |
| curaua-preservation | 12 | 0 | 0 | 0 |
| curaua-contracts | 15 | 0 | 0 | 0 |
| statistics | 10 | 0 | 0 | 0 |
| metadata | 5 | 0 | 0 | 0 |
| replay | 70 | 0 | 0 | 0 |

Fresh installed-package verification passed **585 methods** across all eight
complete groups, zero failures, errors or skips, in
1580.672 seconds of outer process time. Six wheels
were installed in a fresh isolated environment using offline dependencies.
The 56 candidate CLI outputs check **full JSON equality and text value/caveat
checks**, not whole-text byte equality. The separate terminal CLI/API fixture
smoke also passed.

| Installed group | Passed | Failures | Errors | Skips |
|---|---:|---:|---:|---:|
| query | 257 | 0 | 0 | 0 |
| formal | 13 | 0 | 0 | 0 |
| ingestion | 202 | 0 | 0 | 0 |
| relationships | 14 | 0 | 0 | 0 |
| provider | 19 | 0 | 0 | 0 |
| transport | 37 | 0 | 0 | 0 |
| lifecycle | 25 | 0 | 0 | 0 |
| integration | 18 | 0 | 0 | 0 |

Standalone catalog validation also passed for 129 sources, 1176 material states
and 1187 reference properties. It certifies structural/integrity checks only,
not scientific applicability or reuse rights. These catalog bytes are unchanged
by the later test-only repairs.

The selected source scope covers **172 of 1887 frozen root IDs**; **1715 root
methods remain unrun**. Replay70 is actually executed in this dedicated
protocol. No Linux runtime, second Python-version runtime, hosted CI or
full-root-suite pass is claimed.

The separate unchanged core-wheel smoke passed in **1320.407 seconds** before
the test-only repairs. All 319 package/build/core-smoke input hashes match the
final implementation exactly, so that evidence is carried with those bindings;
the smoke was not repeated. The six final wheels contain exact catalog bytes
and synchronized source notices. Wheel hashes and all input hashes are retained
in the machine-readable report.

## Preserved failures and repairs

The initial tested working files were subsequently sealed as e0d12767b7e8f9a6f1c620e10c9a7a14aac9ec97.
They remain available to reproduce the original failures:

- Initial source protocol: 354 executed, 353 passed, one Curaua CI subtest
  failure; 85 methods were not reached. Outer duration 1473.437 seconds.
  The historical caller supplied frozen 249 IDs against the current 257-ID
  file image, so strict mixed-image validation rejected it. The repair first
  validates the complete current image, then recovers exact historical IDs
  and paths. Negative subtests retain the fixed fingerprints and rejection
  boundaries.
- Initial installed protocol: query group 257 executed, 254 passed, three
  failures; the remaining 328 methods were not reached. Outer duration
  904.281 seconds. Five reviewed current count/hash/category test oracles
  were corrected. Previous anchors remain explicit stale rejection cases,
  and method IDs are unchanged.
- Two native current-oracle failures were separately reproduced before repair.
  All 51 methods in the five corrected modules passed afterward.
- New preservation development initially passed 14 of 15 methods, then the
  focused conflict test failed once more. Its mutation hit positivity and
  scalar-text checks before the intended conflict check. A valid names.en
  mutation now exercises strict conflict rejection; the focused test and
  later preservation group pass. Both failed attempts remain recorded.
- Initial overlap validation passed 37 of 41 methods with four finite-count
  failures. All 41 passed after exact count correction.
- Initial sandbox query setup completed zero methods and exhausted a
  600-second budget. Its 20-second cleanup wait also raised TimeoutExpired,
  leaving the outer receipt incomplete. A separate 35-second setup diagnostic
  showed socketpair-related blocking. These are not passes or skips. Native
  diagnostics and eight final native query methods passed separately.

Earlier scoped passes are supplementary evidence, not additions to the final
439/585 totals. Raw logs and environment-specific process records remain private.
Safe evidence labels, hashes, counts and exact final method IDs are recorded
in runtime-validation-results.json.

## Preservation and review status

All nine candidate evidence artifacts, 122 old fixtures, five old workflows
and 23 old CI runners are byte-identical to the candidate baseline. General
partition CI retains 1887 root IDs and four partitions per Python version.
The original scientific records, order and metadata recover exactly through
the append boundary. Finite history bridges reject unknown bytes, incorrect
counts, changed files and incomplete inventories.

Only the two final validation documents are added after the tested
implementation. Independent final runtime audit and experimental publication
remain pending. Candidate eligibility review is not experimental replication
or approval to merge main.

## Reproduction

Use a fresh full-history checkout of the exact tested implementation. These
commands do not push or deploy. Linux commands are a reproduction recipe,
not an executed Linux result.

Windows PowerShell:

~~~powershell
py -3.11 -m venv .venv
$python = Join-Path $PWD '.venv/Scripts/python.exe'
& $python -m pip install --no-deps --only-binary=:all: -r experimental/platform/ci/build-requirements.txt
& $python -m pip install --no-build-isolation -e '.[dev]'
& $python -X utf8 scripts/run_delgado_pla_pcl_runtime_ci.py --validate-scope
& $python -X utf8 scripts/run_delgado_pla_pcl_runtime_ci.py --validate-inventory
& $python -X utf8 scripts/run_delgado_pla_pcl_runtime_ci.py --source-tests
& $python scripts/validate_catalogs.py
& $python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir dist . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform
& $python -m pip download --no-deps --only-binary=:all: --dest dist/dependencies -r experimental/platform/requirements-lock.txt -r experimental/platform/ci/projection-requirements.txt
& $python -X utf8 scripts/run_delgado_pla_pcl_runtime_ci.py --wheel-dir dist --dependency-dir dist/dependencies
& $python -X utf8 scripts/check_wheel_metadata.py dist/materials_boundaries-0.35.0-py3-none-any.whl
~~~

Linux shell:

~~~sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --no-deps --only-binary=:all: -r experimental/platform/ci/build-requirements.txt
python -m pip install --no-build-isolation -e '.[dev]'
python -X utf8 scripts/run_delgado_pla_pcl_runtime_ci.py --validate-scope
python -X utf8 scripts/run_delgado_pla_pcl_runtime_ci.py --validate-inventory
python -X utf8 scripts/run_delgado_pla_pcl_runtime_ci.py --source-tests
python scripts/validate_catalogs.py
python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir dist . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform
python -m pip download --no-deps --only-binary=:all: --dest dist/dependencies -r experimental/platform/requirements-lock.txt -r experimental/platform/ci/projection-requirements.txt
python -X utf8 scripts/run_delgado_pla_pcl_runtime_ci.py --wheel-dir dist --dependency-dir dist/dependencies
python -X utf8 scripts/check_wheel_metadata.py dist/materials_boundaries-0.35.0-py3-none-any.whl
~~~

The producer used a 3600-second outer budget for each final source/installed
protocol, with durable logs and task-owned timeout cleanup. A timeout or
missing terminal record must remain incomplete.
