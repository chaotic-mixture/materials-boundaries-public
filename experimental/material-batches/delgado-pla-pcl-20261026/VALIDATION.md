# Candidate validation

This is a candidate-only result at implementation commit `aee355d07d28d4ffd577a203d6db6b6cc7c9311b`
(tree `0510f747a116ccdfa332cc8762ca8e747a170b47`), based on published
`437950c414ea340eda340babe7b63dee9fcee535`. The later evidence commit adds only this document and
`validation-results.json`; all eight tested implementation files remain hash-identical.
Actual admitted delta is **zero**. Runtime integration and publication require
independent parent review.

## Executed scope

Native Windows CPython 3.11.0 executed four separate bounded fresh processes:

| Complete module scope | Passed methods | Ledger duration |
| --- | ---: | ---: |
| candidate | 22 | 119.468 s |
| compiler | 11 | 37.266 s |
| measures | 10 | 3.766 s |
| metadata | 5 | 0.375 s |

The accepted evidence covers **48 distinct methods**, zero failures, errors, skips,
expected failures, unexpected successes or fixture/subtest errors. These are
four separate processes, not one uninterrupted suite. The final 22 candidate
methods ran on `aee355d07d28d4ffd577a203d6db6b6cc7c9311b`. The other 26 ran on `ba371aa8a1484ffb6b9f94a69f520d6d2d1c8f0a`; their code, data,
fixtures and dependencies remained unchanged when only the separate candidate
test module was strengthened. Those 26 were not rerun. The unchanged compiler
module includes its frozen four-formulation replay. The unchanged reported-measures
module includes numeric SD with unspecified central aggregation and its strict
negative guards; no schema or production validation was changed.

The candidate tests verify exact formulation/volume-key/modulus/SD joins, ordered
authorship, CC BY 4.0, source-document and receipt bindings, nominal versus analyzed
composition, unknown aggregation/count/conditions, variable molding settings,
aliases, duplicate IDs and fresh-ID exact factual identity clones,
state-versus-identity counts, missing properties,
wrong units/precision, source/baseline drift, rejected stale packets, and immutable
byte/mtime replay. Intentional invalid inputs are rejected within passing methods;
they are not extra tests, materials or successful admissions. The rehashed-source
mutation proves prepared-input/output replay consistency, not the scientific
rejection of a fully coherent reauthored source. Fixed source oracles and separate
source review provide bounded source-fidelity checks, not a general authenticity
test for arbitrary external science.

The initial 22-method candidate run also passed. Static review then identified
that its clone mutation principally exercised duplicate IDs. A test-only commit
added a fresh-ID/label clone with consistent links and required the existing
validator's exact structural-identity rejection. All original assertions and
22 method IDs were retained. The full 22-method candidate module was rerun and
passed. Thus recorded history is **70 executions / 48 distinct methods**; the
earlier 22 passes are preserved, not counted as 22 additional distinct methods.

Both actual compiler CLI calls exited zero and preserved output bytes and mtime
on repeat. The prepared packet is 261225 bytes,
SHA-256 `f617a9f279b285895545de7d74e082123a9879906af40f25eb81b3db48f1f481`. All eight bound inputs remained
unchanged. The complete existing runtime catalog validator also passed in
6.875 s. Its scope is structural/integrity validation,
not source truth, rights, scientific approval or a runtime append.

No compiler/test process failed or timed out. No automatic or failure retry was
performed; the explicit candidate rerun tested the newly added clone guard.
Exact IDs, starts/completions, file hashes, log hashes, timings and
separate process outcomes are recorded in `validation-results.json`.

## Preservation and unrun boundaries

All **1057 baseline files total** remain unchanged, including **122 fixtures**
and 935 other files. Catalog records/order, sources, schemas, production code,
old runners and validated workflows are unchanged. The 147-module / 1887-ID
core inventory, its 459/492/417/519 partitions and the separate 70-method replay
inventory are preserved. The new candidate directory has no package initializer
and is explicitly selected rather than added to frozen root discovery.

Executed root coverage is **26/1887**; **1861 root methods remain unrun** in this
candidate validation. The 22 new candidate methods are outside that inventory.
The separate replay70, fresh installed-package suites, wheel build/smoke, hosted
CI for this candidate, Linux and other Python versions were **not run**. The
published baseline's prior hosted success is separate evidence, not execution
of this new candidate.

The finite identity audit rereads 22 frozen Git-object inputs and reproduces
14215 label occurrences / 8273 normalized labels. It retains incomplete additive
disclosure of existing PLA products and does not establish global chemical
uniqueness. Official HTML and XML agree for the selected facts; both returned
HTTP 200 in one bounded read each. The PDF link presented reCAPTCHA and was not
bypassed. No PDF bytes, pixels, hash or PDF/text equivalence were verified. Raw
assets, full source text, private paths and credentials are excluded.

## Counts and review gate

Current public experimental total remains **1192 = 1168 source-qualified + 24
reviewed computed records**. Main remains last verified at **1081**. The 62
unadmitted computed examples remain excluded.

| Source-qualified category | Current | Gap to 1000 |
| --- | ---: | ---: |
| Natural | 1010 | 0 |
| Metal | 32 | 968 |
| Inorganic | 59 | 941 |
| Polymer | 30 | 970 |
| Composite | 37 | 963 |

The hypothetical candidate delta is seven polymer identities, seven states,
seven measured Young's-modulus properties, one source and zero grades. It is not
current growth. Parent source/identity/candidate review precedes any runtime
append. Scientific replication, independent peer review, final-composition
analysis, legal clearance and main merge/deployment/DOI authorization are not
established by these tests.

## Reproduction

Use the existing project development dependencies, including jsonschema and
the required URI-format checker. From the repository root with full baseline
Git objects available:

```text
python -X utf8 experimental/material-batches/delgado-pla-pcl-20261026/build_identity_review.py --check
python -X utf8 scripts/prepare_formulation_packet.py --spec experimental/material-batches/delgado-pla-pcl-20261026/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/delgado-pla-pcl-20261026/prepared-packet.json
python -X utf8 -m unittest discover -s tests/delgado_pla_pcl_candidate -p test_delgado_pla_pcl_packet.py -v
python -X utf8 -m unittest discover -s tests -p test_formulation_packet_preparation.py -v
python -X utf8 -m unittest discover -s tests -p test_material_reported_measures_contract.py -v
python -X utf8 -m unittest discover -s tests -p test_release_metadata.py -v
python -X utf8 scripts/validate_catalogs.py
git diff --check
```

These commands are valid on Linux and Windows, but only the recorded native
Windows process results are claimed here. No new dependency installation,
authentication, runtime admission or push occurred.
