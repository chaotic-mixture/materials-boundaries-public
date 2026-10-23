# Existing core-wheel smoke diagnostic

The original 900-second native Windows fresh-install smoke at candidate
`97f45f07fcdc7ef6f1b0cc72d8d68491438abab4` did not return a terminal result.
It is timed out and not passed. A verified task-owned orphan worker was
stopped; unrelated processes were not changed.

## Established evidence

All 64 packaged runtime files, totaling 34,653,078 bytes, match the unchanged
`faa002c55b7ad2d1bd962e905275894231ab8350` baseline, candidate checkout and
retained isolated installation byte for byte. The original wheel SHA-256 is
`d3b89cb53017f4187aa632bff81f6d8eed4d3b3cf7f555769839fba9e2592947`.
The smoke driver is also identical at both commits, SHA-256
`3527564441a31eda0c2fb003593e0c83be6a1e545165c92722de4a41ec945c42`.

The venv and offline installation completed. The installed script and inputs
were written at 20:24:25 UTC on 2026-10-23; four-language composite exports
were written by 20:25:37 UTC. The final worker snapshot recorded 890.1875
seconds of user CPU, 30.0625 seconds of kernel CPU and 318,083,072 working-set
bytes. This is neither peak memory nor a successful test result.

The script captures its output and prints its summary only at the end. Its
empty outer log cannot identify the exact final assertion. Static examination
of the subsequent material lane finds 930 full-graph validation entries:
745 normal checks and 185 expected rejections, which may fail early.
Repeated exact-ID queries read all three graph resources before filtering;
text CLI output performs query validation and then fresh render validation.
The large empirical-profile loop already has its intended single-profile
negative guard; it is not responsible for 1,000 negative validations.

An isolated read-only microprobe on Python 3.11.0 measured:

| Operation | Wall seconds |
| --- | ---: |
| Complete graph validation | 0.8343 |
| One exact property query | 1.0193 |
| One exact property render | 1.0522 |
| One exact JSON CLI | 1.2426 |
| One exact text CLI | 2.2538 |

The profiled validation spent most cumulative time in recursive structure
checking. Profiling itself increases runtime; its 2.898-second profiled
duration is not the uninstrumented validation cost. These measurements
support repeated CPU-bound graph scans as the main performance concern,
but do not establish the original 900-second stop location.

## Separate diagnostic failure and bounded control

A 180-second diagnostic attempt executing unchanged installed script bytes
with timing hooks terminated early with Windows access violation
`0xC0000005` in observation visualization, before the material lane.
Its stack was preserved. It did not reproduce the original timeout, and its
cause is unresolved. The worker exited; no duplicate instance remained.
The subsequent small uninstrumented material probe completed successfully.

One unmodified baseline fresh-install control completed successfully in
1,176.344 seconds within its 1,200-second external diagnostic cap. It used
the unchanged baseline script and a wheel whose 64 packaged runtime files
match that baseline exactly. The final structured result and exit code zero
were observed; its terminal log SHA-256 is
`168b3b91379600a248ec11f49aafbccd668f8532d4b287eef66391547eac9de7`.
This control took longer than 900 seconds for the unchanged workload on the
selected machine. It supports a budget shortfall as a plausible explanation,
but does not establish the exact cause or stop line of the original timeout.
The repository's scripts, assertions and skip policy were unchanged by the
control. The original 900-second failure is retained independently.

A separate fresh-install check of the new five-row runtime append uses the
same unmodified smoke script. Its 1,500-second external cap is based on the
observed 1,176.344-second control, with approximately 27.5 percent margin.
The exact core wheel SHA-256 is
`b9a93ab32449f8a5ed8f24f9c90304fbaf8bfc9bad339db50e15ceb7bd77fe16`.
The first 1,500-second attempt was interrupted by execution disconnection:
its saved receipt still said running, its outer log had no terminal output,
and no corresponding worker remained when the connection returned. It is
incomplete, not a confirmed timeout or pass. After inspecting those outcomes,
one fresh attempt resumed with the same 1,500-second cap; its terminal result
is pending. The successful baseline result is not counted as validation of
this new wheel.

The separate historical class-count test repeatedly replays prefixes of its
recovery ledger. Those test-only recovery helpers are not imported by the
fresh-install smoke and cannot explain its runtime. No recovery optimization
is included in this batch.

No whole-graph acceptance cache, dropped row/language assertion, substituted
fixture or new skip is proposed. A future performance change would require
separate review preserving every assertion and fail-closed input validation.
No performance patch or runtime acceptance cache is part of this batch.
