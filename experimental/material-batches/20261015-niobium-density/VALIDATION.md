# Local candidate validation, 2026-10-15

Baseline: `4c5656cf6ba0ad1a54b736e0568e97abe4815c29`.
Only the independent Nb candidate packet changes. This is a complete local
review candidate, not an admitted append batch or a released material.

## Current complete-candidate results

- All three existing material, property and source JSON schemas pass.
- The existing runtime graph validator passes with one identity, no grade,
  one state, one density property and one source.
- The first disposable merge changes the baseline counts from 1057 identities,
  20 grades, 1057 states, 1057 properties and 114 sources to 1058 identities,
  20 grades, 1058 states, 1058 properties and 115 sources.
- Repeating the same merge adds zero records; the entire result is equal.
- Existing record content/order and caller input objects are preserved. The
  runtime catalog files remain unchanged; no merged catalog is written.
- No candidate ID conflicts with the existing identity, grade, state, property
  or source registries. Independent static review also found no existing same
  Nb specimen/DOI in main or the frozen `d4e9` candidate.
- Twelve deliberately invalid in-memory cases are rejected: missing property,
  wrong density unit, unknown primary source, unregistered evidence URL,
  unsupported six density repeats, unsupported mean, reported uncertainty
  without its envelope, missing inspection date, missing title, relabeled
  duplicate identity, relabeled duplicate state, and conflicting source ID.

`validation-results.json` records the actual complete-candidate results and
negative-case error messages. Negative mutations exist only in memory and never
enter the saved scientific records. The six-repeat case checks missing evidence
support; the software does not understand the article or independently decide
whether a cited heating run was a density measurement.

The original scientific unknowns remain null or `not_stated`; seven fields not
covered by the handoff remain `not_verified`. Source inspection is attributed
to the parent thread. Local transcription checks are not independent human
scientific review, raw-data reanalysis or a separate license determination.

## Reproduction

Use Python with the existing `jsonschema` development dependency. From the
repository root:

```text
python -B experimental/material-batches/20261015-niobium-density/validate_candidate.py
```

The script reads candidate and baseline files, validates and merges in memory,
runs the negative checks, prints a JSON result, and writes no catalog files.
The recorded run used a Python audit hook blocking socket connection, address
resolution and binding. No source was downloaded again.

## Earlier targeted regressions and held state

At the preceding held-draft stage, the unchanged existing test modules
`test_material_reference_contract` (26 tests) and `test_material_append_merge`
(4 tests) passed: **30 run, 0 failures, 0 errors, 0 skips**. They were not rerun
for this source-metadata-only completion. The prior result remains in commit
`0adb122d0d8937301eb4815a6f8fdadafe84ea3d`; the current result file concerns the
complete candidate and actual merge rehearsal, not another 30-test run.

The earlier held draft deliberately failed schema validation at null title and
null inspection date. Parent-supplied actual metadata resolves both failures.
No scientific null value was replaced to obtain a pass.

The first two earlier regression attempts encountered Windows Git CRLF conversion
of byte-pinned baseline data (2 failures and 18 errors each). Their receipts are
retained separately. The new work copy was restored to exact committed bytes;
neither pins nor validators were modified, and the final 30-test run passed.
No Git configuration or permission change was made.

## Limits and count discipline

The merge counts above describe a disposable hypothetical graph, not formal
project coverage. Formal coverage remains **1081 = 1057 + 24**, admitted delta
is **zero**, and the 62 excluded computed examples remain excluded. This is the
same previously held Nb candidate; a completed handoff is not a second candidate.

Runtime code, schemas, default catalogs, pins, main and `d4e9` are unchanged.
No full-suite, wheel, remote CI, independent scientific/rights approval, formal
admission, upload or publication result is claimed. Review and publication
decisions remain with the parent; no DOI or public deployment was attempted.
