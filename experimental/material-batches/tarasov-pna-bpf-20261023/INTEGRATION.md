# Tarasov PNA-BPF experimental runtime integration

This records the local runtime implementation after source, finite-identity
and privacy review of candidate checkpoint
`97f45f07fcdc7ef6f1b0cc72d8d68491438abab4`. The candidate packet and its
historical zero-admission statements remain unchanged. Runtime implementation
and package validation require separate review before experimental publication.
No main release, deployment or DOI registration is authorized by this record.

The data-only append is local commit
`ff28631faf1d1af804171378953b570313e35b83`, with candidate checkpoint as its
parent and runtime predecessor `faa002c55b7ad2d1bd962e905275894231ab8350`.
It adds exactly five identities, five DDS-cured states, five tensile-strength
records, one source and no grade. The three data files contain 2,008 inserted
lines and no deleted lines. Existing merge and exact predecessor recovery
checks pass; no scientific assertion or older catalog record is changed.

## Local count scope

The source-qualified graph contains 1,153 identities, 31 grades, 1,154 states,
1,165 properties and 125 source/provenance records. Its primary categories are
metal 32, inorganic 53, polymer 30, composite 28 and natural 1,010.
The unchanged 24 reviewed computed records are separate from these
source-qualified reference records. Fresh installed-package checks verify the
local project projection of 1,177 = 1,153 + 24. The last published experimental
projection remains 1,172, and main remains 1,081; this local implementation
requires independent review before publication. The 62 excluded computed examples remain
excluded. Neither candidates, aliases, process states nor test cases add
material identities.

The five identities `mat_tarasov2022_pna_bpf_1` through
`mat_tarasov2022_pna_bpf_5` are study-qualified mixed phosphazene-containing
epoxy formulations. Their single selected strength records retain 66.7, 66.0,
70.2, 74.5 and 72.7 MPa respectively. The author-reported nominal feed labels
are not validated stoichiometry, final composition, purity or molecular species.
The DDS cure and measured state remain explicit; the generic grade is null.
No PNA-BPF-S or DGEBA/DGEBF control is admitted. Excluding PNA-BPF-S does not
assert identical final chemistry with PNA-BPF-1.

Table 1 ECH mole/ratio inconsistencies, the PNA-BPF-2 HCP entry and the
section 2.1 KOH versus synthesis NaOH discrepancy remain disclosed.
Test temperature, humidity, sample count, aggregation and uncertainty remain
unknown. The cited test standards do not supply missing experimental values.
Source transcription and rights review do not establish independent scientific
review or experimental replication.

## Exact predecessor recovery

The new finite ledgers are
`tests/fixtures/tarasov_pna_bpf_data_20261023.json` and
`tests/fixtures/tarasov_pna_bpf_files_20261023.json`.
The existing successor registry projects Tarasov, Bruns, Nylon and earlier
data checkpoints in order; the separate adjacency-only workflow boundary
retains its original location. Partial, reordered, substituted or duplicated
appends must fail. The original candidate's 22 frozen input hashes and every
previous ledger remain unchanged. Current pins advance together; predecessor
stores must not silently gain a different count or write permission.

## Lookup and validation boundaries

```sh
python -X utf8 -m materials_boundaries catalog materials --identity-id mat_tarasov2022_pna_bpf_2 --json
python -X utf8 -m materials_boundaries catalog reference-properties --material-id state_tarasov2022_pna_bpf_2_dds_cured --json
python -X utf8 scripts/validate_catalogs.py
```

Strict runtime schema/integrity validation passed after the append. The
candidate's 39 focused tests are historical results for its unchanged-runtime
tree, not results for this implementation. New preservation, current query,
product-pin, installed and CI checks must be reported separately with exact
IDs and immutable input hashes. See
[INTEGRATION_VALIDATION.md](INTEGRATION_VALIDATION.md) and its machine-readable
receipt for actual completion, failed attempts and unexecuted scope. No hosted
Tarasov result exists at this stage.

The candidate's original fresh core-wheel smoke timed out at 900 seconds;
it remains incomplete. The unchanged baseline control subsequently completed
in 1,176.344 seconds. See [SMOKE_DIAGNOSTIC.md](SMOKE_DIAGNOSTIC.md) for
the bounded baseline diagnostic, the separate runtime-wheel check and their
limits. These are distinct executions; later success does not erase the
original timeout or the separately recorded diagnostic access violation.

All distributed changes are curated facts, provenance, code, tests and
documentation. The publisher PDF, rendered pages, full text, raw measurements,
credentials and private execution notes are excluded.
