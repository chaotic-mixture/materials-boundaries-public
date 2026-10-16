# Authorized local experimental increment

This decision packet selects the exact Nb and four-halide candidate inputs for
this authorized local experiment. It is not a human scientific review, rights
certification or main release approval. All five are integrated in this branch;
formal main admission remains pending. The previous three NBS identities remain
unchanged. The released main total stays 1081; this experimental project has 1089.

`integration.json` is the runnable command input. Its digests bind the exact
d4e9cf3 baseline and frozen candidate files. `runtime-status-adjustments.json`
records the two editorial-only Nb runtime changes; the same expected/new strings
are embedded in the command manifest. Candidate-stage review files are historical
inputs and remain byte-identical to their original commits.

Run `scripts/integrate_material_candidates.py` from the repository root with the
pinned baseline, this manifest and a new output file. Review the emitted report
and full graph together. Identical reruns preserve the output bytes and mtime;
changed inputs or conflicting outputs fail before replacing any artifact.

See [the integration guide](../../../docs/MATERIAL_GROWTH_20261016.md) for exact
facts, conditions, all five category counts, commands, review boundaries and
verification requirements. Actual test results are supplied in the handoff;
this packet does not label merely prescribed checks as passed.
