# Tian runtime validation

Local native Windows / CPython 3.11.0 validation completed on implementation
`6cbd1a7f6cf85ce1709d14e1aafca175f3c07cb2`, tree `b610b90cfcacf7690d4b6c510b35e07ad693d69c`. Independent runtime review is pending. No Linux runtime,
hosted CI or publication success is claimed.

## Exact complete runs

The source-reviewed candidate is `497dcc8495c32b16f02cdedce8b99f6b7d05f2c4`; the data-only append is `f7086fc049dc40319d7daa9ffb9bd5fdece55856`.
One uninterrupted selected-core process passed **305 methods**, with zero failures,
errors or skips, in 2052.424 test seconds and
2055.625 process seconds within its 3000-second budget.
The complete core inventory has 1887 IDs. **1582 unselected methods were not run**,
neither passed nor skipped. The ledger includes every selected ID and exact fingerprints.

One separate uninterrupted fresh-installed process passed **561 methods across all
eight complete groups**, with zero failures, errors or skips, and finished the
independent installed CLI/API, linked-provenance, zero-admission and deterministic
archive smoke. It completed in 700.219 process
seconds within its 1800-second budget. Both processes began and ended at the same
clean commit/tree. Earlier focused or segmented outcomes are not substituted for
either complete run or added to these method totals.

| Installed group | Passed | Failures | Errors | Skips |
| --- | ---: | ---: | ---: | ---: |
| query | 233 | 0 | 0 | 0 |
| formal | 13 | 0 | 0 | 0 |
| ingestion | 202 | 0 | 0 | 0 |
| relationships | 14 | 0 | 0 | 0 |
| provider | 19 | 0 | 0 | 0 |
| transport | 37 | 0 | 0 | 0 |
| lifecycle | 25 | 0 | 0 | 0 |
| integration | 18 | 0 | 0 | 0 |

Six wheels were built offline and their exact bytes were verified before fresh
installation. The density smoke checked **16 CLI outputs**, using full JSON equality
and text value/caveat checks, not whole-text byte equality. It preserved both exact
nominal-composite identity/state/density joins, the literal `1 wt Ti` label, eight
ordered authors, unknown density conditions and uncertainty, exact resource and
snapshot pins, unchanged computed admission and 62 excluded examples.

## Earlier failures and limited evidence

The initial default-Python catalog check could not import `jsonschema` and was
not a completed validation. Only a task record survives for that attempt; no
original log hash, duration or exit code is invented. The later catalog validation
passed in 8.000 seconds before the immutable implementation freeze.

The first ingestion/relationship focused attempt had 14 passes and one import
error because that environment lacked `jsonschema`. Only the affected hBN case
was rerun in the existing dependency environment and passed. The first candidate
history attempt had 17 passes and one `WinError 5` at `os.link`; only that replay
case was rerun natively and passed. These were two-segment focused checks on a
dirty implementation worktree, not uninterrupted full-suite passes at the final
commit. Original failed receipts and log hashes are retained separately.

The earlier five-method source query attempt timed out after 600 seconds with
zero methods completed. A bounded sandbox diagnostic also timed out: the first
TestClient request waited in Windows proactor `socketpair` initialization at
`accept`; sandbox cleanup failed and a further cleanup wait timed out. Its
unfinished receipt still said running. A later read-only process check was
reported to find no matching process; no independent process-query log was saved.
The same current tree/interpreter/dependencies returned HTTP 200 in 2.750 seconds
outside the sandbox (3.000 seconds total). This isolated diagnostic is not five
tests passed and does not explain any older historical smoke timeout. The original
failed attempts remain failed/incomplete; no assertion or timeout was weakened.

Earlier two-method baseline compatibility and 60-method CI-contract checks passed
and overlap the complete inventories. The original seven preservation and five
legacy-document results have tool receipts only, without saved raw logs; no log
hashes are invented for them. Their later execution belongs to the complete core
run above. Mocked installed-completion messages in CI unit-test output are not
fresh-install evidence. Exact private-log hashes and evidence limitations are
recorded in `integration-validation-results.json`; private logs and commands are
not published.

## Data and publication boundaries

All nine candidate artifacts remain byte-identical to the corrected candidate.
The earlier editor-as-author finding, correction and exact eight-author regression
remain in the unchanged candidate validation record. Runtime admission adds exactly
two composite identities, two states, two measured density records, one source and
zero grades. No theoretical density, tensile measurements or unreinforced AZ31
comparator is admitted. Nominal loading is not an analyzed final composition;
density temperature, pressure, humidity, specimen count, repetitions, aggregation,
uncertainty, density basis and porosity remain unknown.

The local source-qualified graph contains **1161 identities, 31 grades, 1162 states,
1173 properties and 127 sources**. Categories are natural 1010, metal 32, inorganic
59, polymer 30 and composite 30. Gaps to 1000 are respectively 0, 968, 941, 970 and
970. The local combined projection is **1185 = 1161 source-qualified identities +
24 unchanged computed records**. Candidate rows, state counts and calculations are
not additional identities. The last published experimental projection is 1183;
main remains 1081. The saved read-only remote-ref check recorded main at
`4c5656cf6ba0ad1a54b736e0568e97abe4815c29` and no Tian experiment ref. This is a remote observation at the recorded
time, not a claim that a local main checkout was read. There has been no push for this batch, main merge, deployment,
DOI registration, raw-asset upload or credential change.

The validation successor changes only this document and its JSON ledger. All
tested code/data/fixtures remain attributed to `6cbd1a7f6cf85ce1709d14e1aafca175f3c07cb2`; the new documentation
bytes are not described as tested. The proposed branch is
`experimental/tian2023-composite-runtime`, with Ubuntu 3.11 and Windows 3.12 jobs
pending independent runtime review and later authorized experimental publication.
The local finite artifact audit inspected 78 distinct changed UTF-8 blobs across
four commits, found no bounded private-pattern/raw-asset issue, and confirmed
unchanged candidate artifacts and historical engine bytes. The parked replay
optimization is excluded. This is not independent runtime review.

## Reproduction

Use the supported Python environment and already-provisioned locked build
dependencies, with separate wheel and dependency directories:

```text
python -X utf8 scripts/validate_catalogs.py
python -X utf8 scripts/run_tian_nano_ti_ci.py --validate-scope
python -X utf8 scripts/run_tian_nano_ti_ci.py --targeted-core
python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir wheelhouse . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform
python -X utf8 scripts/run_tian_nano_ti_ci.py --wheel-dir wheelhouse --dependency-dir dependency-wheelhouse
```
