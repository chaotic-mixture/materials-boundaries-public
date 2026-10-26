# Worked Ewurum reactive PBS lignin handoff

This is a retrospective example of a completed locally validated runtime integration, not an instruction to rerun it. Publication is not established by the local evidence summarized here. It illustrates the reusable contract; its batch-specific CI runner and historical adapters are **not** mandatory patterns for future batches.

## Frozen inputs and outputs

| Item | Verified identity |
| --- | --- |
| Catalog baseline | `8ccd217599fd462d13d7435bdfb02a0825e4eacd` |
| Corrected candidate | `29a33009d763c0ef52943c1bce28e24c436c74ac` |
| Catalog-only append | `e6d39e39184ab333045ae3ae2d001ab6b41bd53f` |
| Final implementation referenced by producer validation | `dba9336698aa4114f3bf144919d1d1d8789633d8` |
| Evidence-only successor independently audited here | `437950c414ea340eda340babe7b63dee9fcee535` |
| Audited tree | `1131a517c7dcf6b0bea74b1951df45d1d18a2e45` |
| Prepared packet raw SHA-256 | `e36ecbe9e46d097e0bd28471e743d2b1760f1d015190962f0f6cd7e3f1383467` |
| Reused source canonical-record SHA-256 | `358d6486d107da45ed76c3aa7c7a448213957c7b94afc811e9ad75e294641ca0` |

The candidate files are in `experimental/material-batches/ewurum-reactive-20261025/`. Read `packet-spec.json`, `prepared-packet.json`, `source-review.json`, `identity-review.json`, `integration.json` and the two distinct candidate/runtime validation reports. Do not rewrite the original candidate report to say that its later runtime append was already admitted.

The raw baseline catalog hashes are:

```json
{
  "materials": "f65d332bc0a67838bbba0f936ba8134243e75123d720417fa7af873502c0976b",
  "reference_properties": "1feeaec49643cf3ee560c29f91f91eb7674a8ee769639558930dfc8b4cfbd3c2",
  "sources": "c5eecc0e7c64d9ef4af623f0800d947cec8a7f91570633b45b053d6ecb0c75aa"
}
```

These hashes are already in the spec; a replay must supply the archived baseline bytes. The enlarged `materials_boundaries/data` at `437950c` is not a valid substitute for the old baseline.

## Small task selection

Reuse source `ewurum_mcdonald_2025_pbs_lignin`; curate only four DCP-added reactive R-series formulations. Identity IDs use the prefix `mat_ewurum2025_pbs_lignin_` followed by `r10`, `r20`, `r30`, `r45`. Each has one injection-molded state and one measured Young's modulus reference. No grade or new source is added.

| Source Table 6 row | Nominal lignin wt% of total polymer mass | Modulus MPa | Reported SD MPa | Tukey group |
| --- | ---: | ---: | ---: | --- |
| R10 | 10 | 751 | 40 | b′ |
| R20 | 20 | 716 | 49 | b′ |
| R30 | 30 | 910 | 85 | b |
| R45 | 45 | 1256 | 162 | a |

The source is Ewurum and McDonald, *Lignin Reinforcement in Polybutylene Succinate Copolymers*, Polymers 2025, 17, 194, DOI `10.3390/polym17020194`. Table 6, PDF p.12, supplies mean and SD. Section 2.9 reports ten tensile replicates, not ten established production batches. Reference [32] supplies the source-cited ASTM D1708-18 (2018) edition; compliance is unverified.

The author reused an official publisher PDF recorded as 3,211,541 bytes, document SHA-256 `766d17f0e92c7e93cd57a3a5e97dddff0cb66a84bba6bf9118fbd0796d4c2e6f`. The independent source review corroborated official indexed text, not current raw PDF bytes. These are different evidence claims. The recorded article-specific license is CC BY 4.0; original PDF, figures and complete tables are excluded. This template author did not re-open that source.

## Decisions a worker must not improvise

- Existing B-series physical blends remain distinct from the selected reactive formulations, supported by source formulation/reaction context. The finite 22-input identity audit is not global chemical equivalence proof.
- Reported 0.25 wt% DCP has an unresolved denominator, final residue and final chemistry. Do not normalize a complete final recipe or infer crosslink density.
- FZ91PM/FZ91PB is unresolved ingredient-grade information; no finished-product grade is invented.
- Table 1 gel fractions concern separate hot-pressed material. They support contextual identity discussion only; they are not added properties and not transferred to injection-molded tensile dog-bones.
- Tensile temperature, pressure, humidity, post-molding conditioning and modulus fit window remain unknown. Compounding at 140 °C is not tensile test temperature.
- Exclude R0 and unselected properties. Four selected moduli do not license the rest of the paper.

Independent review corrected an earlier candidate's “unknown standard edition” and made gel-versus-tensile specimen scope explicit. Numerical values and SDs did not change. Preserve that correction history rather than presenting a first-pass flawless result.

## Counts and immutable boundaries

| Registry | Baseline | Runtime after append | Delta |
| --- | ---: | ---: | ---: |
| Source-qualified identities | 1164 | 1168 | 4 |
| Grades | 31 | 31 | 0 |
| States | 1165 | 1169 | 4 |
| Properties | 1176 | 1180 | 4 |
| Sources | 128 | 128 | 0 |

Afterward, category identities are natural 1010, metal 32, inorganic 59, polymer 30, composite 37. The unchanged 24 reviewed computed compositions produce 1192 experimental project records; 62 unadmitted examples remain excluded. The documented published-main count remains 1081 in this evidence snapshot, not 1192.

The candidate holds one existing source descriptor but has zero **new** sources. Every old object/order/metadata value and the source catalog raw bytes remain unchanged. The audit records unchanged 9 candidate files, 122 historical fixtures, 22 old runners and 4 old workflows. New runtime totals do not retrospectively alter the candidate's `formal_admitted_delta: 0`.

## What the committed software validation actually establishes

The public evidence is `experimental/material-batches/ewurum-reactive-20261025/INTEGRATION_VALIDATION.md` and `integration-validation-results.json` at `437950c`. The producer records native Windows CPython 3.11.0 validation on final implementation `dba9336698aa4114f3bf144919d1d1d8789633d8`, retained by the evidence-only successor. Read its input-image qualifications and unsuccessful earlier attempts; do not combine them into a fictitious clean uninterrupted run.

| Scope | Committed evidence | Limit |
| --- | --- | --- |
| Source groups | 370 successful executions, 366 distinct methods, 0 failures/errors/skips | Four duplicate IDs across groups; nine fresh-process groups, not full-root execution |
| Root coverage including metadata | 162 distinct completed root IDs of 1887 | 1725 root IDs unrun locally |
| Installed suite | 577 executions and distinct IDs, 0 failures/errors/skips | Eight groups in a fresh offline six-wheel installation |
| Metadata | 5 methods passed on an earlier input image with explicitly unchanged relevant inputs | Not a final whole-preflight rerun; do not double count root overlap |
| CLI checks | 32 JSON/text outputs plus tail CLI/API check | Output cases are not unittest methods; full values/caveats checked, not whole text-byte identity |
| Wheel smoke | Passed in 1199.375 seconds after a recorded failed attempt | Script check; qualified unchanged 319 input hashes, not an invented method count |
| Hosted CI | Not run for the implementation at the time of this report | No inference of hosted matrix success |

Source group counts: candidate 20, preservation 12, contracts 17, compatibility 156, partition contracts 50, prior candidate 18, prior preservation 12, prior contracts 15, replay 70. Installed groups: query 249, formal 13, ingestion 202, relationships 14, provider 19, transport 37, lifecycle 25, integration 18. Exact inventories are in `tests/ewurum_reactive_ci/manifest.json` and the committed evidence, not just these totals.

The candidate-only archival command selects exactly `/final_validation/separate_process_groups/0/expected_ids` from its hash-pinned `validation-results.json` (20 IDs). Group 1 is the separate retained compiler module; other historical attempts are not added to that selection.

A separate independent audit was available to the original coordinator, but its private receipts and environment are not bundled here. This public example does not ask a new reader to trust inaccessible receipt contents or reproduce that private environment. Use the committed evidence for reproducible claims; perform a new independently authorized review if needed. Neither source documents nor raw measurements are included.

## Historical reproduction commands

These exact commands are documented in the batch's runtime validation report. **Do not run them as part of adopting this kit**, and do not use this batch-specific runner for a new batch. Full history, the matching environment, available offline build requirements and a dependency cache satisfying the two named lock files are prerequisites.

```sh
python scripts/validate_catalogs.py
python scripts/run_ewurum_reactive_runtime_ci.py --validate-scope
python scripts/run_ewurum_reactive_runtime_ci.py --validate-inventory
python scripts/run_ewurum_reactive_runtime_ci.py --source-tests
python -m pip wheel --no-index --no-deps --no-build-isolation --wheel-dir dist . ./formal-catalog ./experimental/platform/federation ./experimental/platform/query-service ./experimental/platform/lifecycle ./experimental/platform
python scripts/check_wheel_metadata.py dist/materials_boundaries-0.35.0-py3-none-any.whl
python scripts/run_ewurum_reactive_runtime_ci.py --wheel-dir dist --dependency-dir dependency-cache
```

The cache requirements are `experimental/platform/requirements-lock.txt` and `experimental/platform/ci/projection-requirements.txt`. No download command is authorized here. Platform-specific atomic-write/transport tests need their supported permitted environment; a denial must not be “fixed” by weakening the assertion or bypassing a restriction.

## Copy the discipline not the accumulated scaffolding

Reuse the existing compiler, immutable candidate, exact append proof and independent review. Do not require every small future batch to reproduce Ewurum's historical compatibility layers. If unchanged legacy expectations force shared test/historical edits, the coordinator must make that cost visible and assign a separate narrowly reviewed maintenance decision. A cheap worker should not be asked to independently redesign the test architecture while transcribing four values.
