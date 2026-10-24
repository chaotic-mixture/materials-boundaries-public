# Historical catalog prefix replay

This test-only change starts from `196995256836db2d8f870ac9a91f664bfdd03e7f`.
It changes neither catalog data nor production validation. The experimental
catalog remains 1,177 records: 1,153 source-qualified identities and 24 existing
reviewed computed records. Main remains at 1,081. No installed-package smoke,
CLI subprocess coverage, source qualification, or admission rule is changed.

## Algorithm and rejection behavior

`tests/material_append_history.py::project_catalog_bytes_chain` previously
loaded the three catalog files and replayed the complete preceding ledger
prefix again whenever the supplied table matched another historical image.
The revised function keeps one disk graph and a processed-prefix index inside
one invocation. It loads the graph only at the first recognized table image,
then replays only the previously unprocessed prefix before each later match.

The cached graph must remain independent of the supplied table bytes. For each
match, a shallow top-level copy receives the exact supplied table, and the
unchanged `recover_catalogs` validates that selected graph. Its recovered table
becomes the next raw image; its graph is not cached. Consequently, a legitimate
supplied table cannot repair a corrupted disk table and hide a later rejection.
The processed index excludes the current match, preserving the next disk-prefix
validation. Empty prefixes still invoke the original graph checks. Unmatched
tail ledgers are not newly traversed.

Unknown and noncanonical byte images still pass unchanged to the historical
caller's rejection. Invalid chains retain their original checks and error
precedence. There is no cross-call cache: subsequent calls read changed root,
packet, or ledger inputs again. Inputs must be stable during an invocation;
neither implementation provides an atomic snapshot against concurrent edits.

## Exact code compatibility

The original PUR fixture pins the history engine itself. Its original bytes,
hashes, recovery assertions, registry order, and all other historical fixtures
remain unchanged. A new finite code ledger describes one exact reversible edit
of that engine only. `material_append_replay_compat.py` checks the complete new
image and ledger hash before using the unchanged byte recovery primitive.
Unknown bytes are not normalized or accepted. The hook runs after existing
input and chain-order checks, only for the exact engine path.

The old engine SHA-256 is
`38d9b1768121f84cc5b45d21d8d992b8d62cf6ed62ad0ed1ec78f7760ece9ea9`;
the revised engine SHA-256 is
`2379867c0fe4ec89cf4f450b10bf84e48986783d50396c6f593316de78ad3251`.
The bridge ledger contains no material data and does not authorize future
engine changes. Its independent helper and tests pin both exact images.

## Validation scope

The new differential and compatibility tests live in `tests/history_replay/`,
without a package marker. They require explicit discovery, preserving the
previously frozen full-core and targeted-core test inventories. The differential
oracle is the entire old module read from the fixed Git object and verified by
SHA-256; a missing object fails instead of skipping comparison.

The differential cases cover current and historical table images, disk/raw
stage combinations, unchanged-source gaps, unknown bytes, malformed chains,
partial/duplicate/reordered/mutated additions, packet and root corruption,
repeated calls, lazy loading, and retained historical rejection. An initial
naive implementation was rejected by these tests because it cached the graph
after substituting raw. That failed attempt is retained in the validation
evidence rather than counted as a pass.

This is a local review checkpoint, not a publication-ready validation claim.
Completed checks comprise 16 differential tests, 7 bridge tests, 12 mocked
benchmark-budget tests, and 2 existing frozen-inventory tests: 37 distinct
passes, with no skips in those completed checks. The bridge run has a recorded
terminal-result attestation; its original raw log was not retained. Windows and
POSIX process-control branches in the budget tests are simulated, not a claim
of native POSIX execution.

The first broader PUR regression group reached its 600-second budget after
600.018 seconds while its first method was still running. No method from that
group is counted as completed. Of the 40 planned existing checks, 2 inventory
checks subsequently passed, 1 method timed out, and 37 were not run. No blind
PUR rerun was launched. The failed initial naive implementation, the initial
budget-test metadata mock failure, and a later sandbox atomic-replace error
are retained in the ledger. The final 12 budget tests passed with unchanged
assertions under native Windows temporary-file semantics.

One representative real case completed on Windows CPython 3.11.0: the current
materials table over the complete 14-ledger chain. Both outputs contained
9,125,298 bytes and had SHA-256
`410efabb24dad7ed377ac7b94d35bccc40afe91194f0323e0298f500314e02f3`.
The comparison checked the bytes directly, as well as unchanged input hashes.

| Observed operation | Old engine | Revised engine |
| --- | ---: | ---: |
| `recover_catalogs` calls | 105 | 27 |
| Catalog file reads | 42 | 3 |
| Packet file reads | 196 | 40 |
| Instrumented projection seconds | 172.786458 | 46.852641 |

The separate 13-layer synthetic chain observed 91 to 25 recovery calls and
39 to 3 catalog reads. These counts support removal of repeated prefixes;
the timings describe only the single real observation. The other eight real
benchmark cases were not run. Broad historical, full-core, installed-package,
and hosted CI validation remain incomplete for this patch.

The machine-readable `history-prefix-replay-20261024-results.json` records the
exact completed IDs, retained failed attempts, not-run IDs, hashes, and the
representative benchmark. Raw execution logs remain local evidence outside the
repository. No push or merge is authorized by this checkpoint.

## Reproduce

Use a supported Python environment and retain the fixed baseline Git object.
From the checkout root, run the new tests explicitly:

```text
python -B -m unittest discover -s tests/history_replay -p "test_*.py" -v
```

Run the bounded real-catalog benchmark after other test workloads finish. The
output parent directory must already exist outside the checkout:

```text
python -I -B tests/history_replay/benchmark_replay.py --cases current-materials --output ../history-replay-evidence/benchmark.json --case-timeout-seconds 600 --total-budget-seconds 650
```

These commands work in Windows PowerShell and a Linux shell. Only execution on
the platforms identified in the result ledger is claimed. The benchmark's
optional nine-case inventory covers the current image, the image after five
ledgers, and the oldest image, for all three tables. Omitting `--cases` selects
all nine; the command above reproduces only the one measured case. Unselected
cases must not be reported as run.

Each benchmark case has its own child process and measures old then new once.
Reports include actual recovery and file-read counts, output bytes and hashes,
input hashes, and observed time. Timings include counter instrumentation and
exclude image preparation and input hashing. Filesystem cache state is not
controlled. No general speed factor is inferred from these observations.

This optimization concerns test-only history replay. It does not establish the
cause of the original 900-second wheel-smoke timeout; that failure and the
separate later successful smoke remain distinct historical evidence.
