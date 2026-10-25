# Offline formal-review gap report

`formal_review_gaps.py` produces a deterministic, machine-readable deficiency
report for the held `AlGa2Sc` and `O8Re2Ru4` review priority. It reuses the exact
historically accepted second-tranche metadata and identifies evidence still
unverified for a new formal release. It makes no source request, performs no
directory search, and creates no approval or admission.

The 62-record historical metadata acceptance remains intact: 47 metal-family
and 15 inorganic examples, all outside the formal catalog. The proposed two-row
subset is always **held**, with **zero formal admissions** from this command.
Current experimental counts are **1192 = 1168 + 24**; the separate `CaEr2Eu` candidate remains
held. Original input, review, acceptance pins and formal resources are read-only.

## Reproduce

From the repository root, using Python 3.11+:

```sh
python experimental/platform/ingestion/formal_review_gaps.py > /absolute/local-evidence/formal-review-gaps.json
```

Create the output directory beforehand and keep generated reports outside the
checkout. The command writes UTF-8 JSON to standard output; shell redirection writes
the report. There is no output-path option. An alternate checkout can be selected
explicitly:

```sh
python experimental/platform/ingestion/formal_review_gaps.py --repo-root /absolute/materials-boundaries-checkout > /absolute/local-evidence/formal-review-gaps.json
```

`--repo-root` does not accept a replacement trust policy. The selected checkout
must contain the exact trusted artifacts. Changed source bytes, modified pins or
unexpected selected-record identities fail the binding checks.

An exit code of `0` means the held report was generated; it is not approval or a
readiness pass. An exit code of `2` indicates an argument or source-binding error.
The report schema is `formal-admission-gaps/1`. Repeating the command with the same
bound inputs and local artifact bytes yields the same report; there is no live
query, current-time observation or automatically changing provider state.

## Optional local artifact checks

Supply an existing file only when its role is known. Repeat `--artifact LABEL=PATH`
to compare that file's SHA-256 with the corresponding historical reference:

```sh
python experimental/platform/ingestion/formal_review_gaps.py --artifact frozen_source_response_sha256=/absolute/private-evidence/source-snapshot.json --artifact attribution_response_sha256=/absolute/private-evidence/attribution-snapshot.json > /absolute/local-evidence/formal-review-gaps-with-artifacts.json
```

For a path containing spaces, quote the complete `LABEL=PATH` argument. These are
explicit local filesystem paths, not URLs or download instructions. The command
does not discover files, retrieve missing snapshots or upload their contents.
Each supplied target is checked for regular-file status before opening it for
reading. A regular file is hashed only if it is at most 32,000,000 bytes; one
extra byte may be read to detect an oversized file. Raw contents and local file
paths are not included in the report. Do not commit or publish raw evidence
merely to make an availability check pass. Unknown or repeated labels are
argument errors.

Supported labels distinguish the five per-record evidence references from the
two other historical acceptance references:

| Artifact label | Historical reference |
| --- | --- |
| `candidate_packet_sha256` | Selected record's candidate packet |
| `archive_response_sha256` | Selected record's archive response |
| `relations_response_sha256` | Selected record's relation response |
| `frozen_source_response_sha256` | Selected record's frozen source response |
| `attribution_response_sha256` | Selected record's attribution response |
| `source_unit_definition_snapshot_sha256` | Acceptance pin's unit-definition snapshot |
| `acceptance_candidate_file_sha256` | Acceptance pin's candidate file |

`candidate_packet_sha256` and `acceptance_candidate_file_sha256` are distinct
references; do not substitute one file for the other based on a similar name.
The two selected records share their five per-record reference hashes, which
makes a small explicitly supplied evidence set useful for both.

Each `evidence_observations` item records its expected hash, parent JSON pointers,
availability, actual hash when computed and bytes read:

| `availability` | Meaning |
| --- | --- |
| `reference_only_not_provided` | No local file was supplied for this reference. |
| `missing` | The explicitly supplied local file was not found. |
| `not_regular_file` | The supplied target is a directory, FIFO, device or other non-regular file; its contents are not opened. |
| `read_error` | The file could not be read; local paths and OS error details are omitted. |
| `size_limit_exceeded` | The size probe exceeded the permitted hashing bound. |
| `digest_match` | Supplied bytes match the historical hash reference. |
| `digest_mismatch` | Supplied bytes do not match that reference. |

These observations are reported with exit code `0` when the trusted parent
bindings are valid; they do not make the report an approval or failure verdict.
A matching digest proves equality to the recorded bytes; it does not authenticate
the original reviewer, establish license ownership, repeat geometry diagnostics
or approve a new release. Even if every supplied file matches, the new formal
release remains held.

## Read the report without upgrading its claims

The report binds the parent input, normalized review, canonical review,
acceptance pin and each selected normalized record to trusted exact hashes. It
also checks the pinned formal/review boundary, including the formal 24 and the
unadmitted 62. These bindings prevent a locally rewritten review from silently
becoming the trusted source of its own approval.

The selected metadata is identified as historical parent-review content. Its
recorded `accepted` decision and historical diagnostic booleans retain that
scope. They do not become a new scientific verification by this command. The
report separates historical acceptance, evidence availability and unresolved
requirements for a new formal release instead of replacing those distinctions
with a single success flag.

All six `gaps` retain `status: unverified_for_new_release`:

Each gap names the exact two selected `candidate_ids` and its
`related_evidence_labels`. Those labels provide context for evidence review;
they do not mean a hash match closes the gap or replaces an applicable identified
prior-review receipt. Neither these links nor artifact availability changes the
held status.

| Gap ID | Review still required for a new release |
| --- | --- |
| `source_snapshot_review` | Exact-subset source evidence or applicable identified prior-review receipts |
| `numerical_semantics_review` | Computed density, source field, units and method scope |
| `identity_scope_review` | Selected/related groups, composition buckets and unresolved equivalence |
| `scientific_review_authority` | Reviewer identity, independence, conflicts, authority and applicability |
| `scoped_reuse_review` | Attribution, modifications and scoped access/retention/export/redistribution |
| `formal_release_decision` | Separate authorized release decision, policy, exact pins and artifact checks |

`formal_release.state` remains `held`, `admitted_delta` remains `0`, and
`release_authorized_by_this_report` remains `false`. `report_sha256` hashes the
canonical JSON report before that hash field is added; it is an integrity binding,
not a signature or a reviewer decision. It differs from a hash of the formatted
stdout file.

Unknown temperature, pressure, electronic behavior, experimental existence,
stability, equilibrium and convergence are valid preserved limits for these
hypothetical computed models. They are not missing fields to invent or fill with
ambient/ground-state assumptions. `O8Re2Ru4` remains the source formula, while its
reduced composition bucket is `O4ReRu2`. The scalar property is provider-reported
computed cell density in `kg/m^3`, not an experimental measurement.

The historical CC BY 4.0 statement is scoped to the selected metadata and scalar
density. It does not license upstream ICSD geometry, cell vectors, coordinates,
raw archives, calculation files or potentials. Intentionally unpublished geometry
does not invalidate the historical metadata acceptance. Conversely, provider
license labels, generic reviewer strings and hash matches do not independently
authenticate scoped reuse approval for a new release.

Existing identified scientific/reuse review records may be reused when their
authority, independence, exact content binding and scope can be verified. The
remaining release work requires the applicable review references, an exact subset
decision and a separately authorized formal release with new pins. This report
does not infer that earlier evidence never existed or that the provider's license
is invalid. It provides a reproducible account of what the local inputs do and
do not establish.

The command has no catalog-write, DOI-registration, deployment or publication
operation. Any future source acquisition or release remains a separate activity;
the report itself never increases formal counts.

See [the held subset readiness note](../examples/reviewed-computed-v2-second/REVIEW_READINESS.md),
[computed-v2 trust contract](../COMPUTED_V2.md),
[data contribution requirements](../lifecycle/CONTRIBUTING_DATA.md) and
[formal admission policy](../../../docs/FORMAL_PROJECT_CATALOG.md). Executed
regression results and generated reports are recorded separately; this usage
document does not claim that missing evidence has been obtained.
