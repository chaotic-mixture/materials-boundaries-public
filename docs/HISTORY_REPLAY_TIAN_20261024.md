# Replay integration on the Tian baseline

This isolated patch starts at `826333c73a420b7d254c469d9f6f65155983cde1`. It changes no material data,
production validation, installed smoke, or CLI coverage. The catalog remains
1,185 project records (1,161 source-qualified identities and 24 existing
computed records), with no admissions. The original 14-layer artifact
`2aef5569f630237ccf3f6a545114afed9ae6ff4f` remains separate and intact.
The four imported original verification documents describe that original
baseline only; their results must not be counted as latest-baseline passes.

## Exact compatibility and bounded scope

The reviewed engine and original finite engine-recovery helper are unchanged.
Only the Kapoor and Tian preservation methods wrap their engine-byte input
with that exact recovery before hashing. Their original `ENGINE_SHA256`
values and assertions remain. A separate two-file ledger pins both complete
caller images; tests reverse them exactly to the Tian baseline and compare
every AST node after removing only the single wrapper and its import.
Mutated callers, edit offsets, before/after images and engine bytes fail.
No old fixture hash is replaced; all 119 baseline fixture files
are byte-identical.

One newly imported replay test is adapted for the later successor registry:
it retains the 196995 registry pin and separately verifies the exact Tian
registry. The original 14-layer benchmark remains byte-identical. Its new
16-layer adapter pins Tian and Kapoor plus all original 14 ledgers, reuses
the exact bounded launcher/counters/comparisons, and rereads inputs. The
synthetic differential checks cover 17 graph images and unchanged-source gaps.
Inputs must be stable during one invocation. There is no atomic protection
against concurrent edits and no cross-call graph or packet cache.

## Actual validation

Native Windows CPython 3.11.0 executed the exact new CI command and passed
59 distinct methods with zero failures, errors or skips. Its raw log has
SHA-256 `9d41f69ad3a68db9eac180fe676aa84254f7a5cc636ab9a125f80b91f3703125`. The earlier 42-method initial gate,
10-method adapter gate and seven CI-contract checks overlap this run and
are not added to the distinct count. The initial seven CI-contract results
were terminal-attested without a separate raw log; the final 59-method run
retains complete raw coverage. Inventory-only validation executes zero tests.

Four selected real 16-layer cases passed direct byte equality, unchanged
input manifests, and frozen oldest-table output hashes:

| Case | Recoveries old / new | Catalog reads old / new | Seconds old / new |
| --- | ---: | ---: | ---: |
| current-properties | 136 / 31 | 48 / 3 | 233.406 / 56.212 |
| current-sources | 28 / 13 | 21 / 3 | 47.189 / 21.208 |
| after5-materials | 121 / 26 | 33 / 3 | 198.310 / 43.403 |
| oldest-sources | 0 / 0 | 0 / 0 | 0.001 / 0.001 |

These are single instrumented old-before-new observations; filesystem cache
state and unrelated machine load are not controlled. Timings exclude image
preparation and input hashing. No general speed factor is inferred.
Five other real cases were not run: current-materials, after5-properties,
after5-sources, oldest-materials and oldest-properties.

Only four methods from the existing 1,887-method core inventory were executed;
1,883 remain unrun here. Neither the complete 305-method targeted core suite
nor the 561 installed methods ran. No native Linux or hosted CI execution is
claimed for this latest patch. The independent Linux review of the original
artifact is separate evidence. Earlier failures and timeouts remain in the
archived original records; this work does not explain the installed-smoke timeout.

## CI execution and remaining publication boundary

The new `.github/workflows/history-replay-latest.yml` invokes explicit discovery
of both package-less replay directories plus two affected methods and two
latest inventory checks. Its manifest freezes all 59 IDs; the runner rejects
missing, duplicate, substituted or skipped methods and incomplete runs.
It selects Ubuntu 3.11 and Windows 3.12 for the exact experimental branch.

The existing `ci.yml` is byte-identical. A future push also triggers its general
Ubuntu and Windows jobs. This patch does not promise bounded-only total hosted
CI. Suppressing those jobs requires additional exact workflow recovery and
another Tian assertion call-site change; that expansion has not been made.
Independent review and a decision on broader validation precede publication.
No push, main merge, deployment, DOI operation or credential grant occurred.

## Reproduce

From the latest checkout, these commands work in PowerShell and a Linux shell:

```text
python -B scripts/run_history_replay_latest_ci.py --validate-inventory
python -B scripts/run_history_replay_latest_ci.py --tests
python -I -B tests/history_replay_latest/benchmark_replay_16.py --cases current-properties current-sources after5-materials oldest-sources --output ../replay-evidence/benchmark16.json --case-timeout-seconds 900 --total-budget-seconds 1800
```

Create the output directory outside the checkout first and use a new receipt
path. The local test process used a 600-second budget; the benchmark launcher
has the explicit budgets above. Only the platforms actually recorded are claimed.

To reproduce the original 14-layer benchmark, create a separate detached
checkout at `196995256836db2d8f870ac9a91f664bfdd03e7f`. Overlay only these
exact files from this reviewed patch: `tests/material_append_history.py`,
`tests/material_append_replay_compat.py`,
`tests/fixtures/material_append_replay_code_20261024.json`, and
`tests/history_replay/benchmark_replay.py`. Do not overlay current catalogs,
successor registries, or 16-layer configuration. Run the original benchmark
there with its documented budgets. Its frozen 14-ledger input gate will reject
the latest catalog if run directly against this checkout.
