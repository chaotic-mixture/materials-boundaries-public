# Preparing source-family formulation packets

This checkout-only compiler expands explicitly authored shared context and
per-formulation facts into one immutable JSON artifact. It does not fetch papers,
infer chemical equivalence, convert units or fractions, infer grades or missing
conditions, approve source rights, change scientific-review flags, or write
runtime catalogs. It uses the existing material validator and merge operation.

Use it to avoid repeating a paper's common method, conditions and qualifications
in every candidate record. Scientific facts and their locators still need to be
authored and checked. One identity can have several explicit grades, states and
properties; extra processing conditions or specimens do not create identities.

## Command and frozen inputs

```sh
python scripts/prepare_formulation_packet.py \
  --spec experimental/material-batches/YOUR_BATCH/packet-spec.json \
  --baseline-dir PATH_TO_PINNED_BASELINE_DATA \
  --output experimental/material-batches/YOUR_BATCH/prepared-packet.json
```

The baseline directory contains `materials.json`, `reference_properties.json`
and `sources.json`. Its exact file hashes must match the spec. Archive this
baseline before integration. After the runtime catalog grows, reproducing an
earlier packet requires that archived baseline; the compiler never silently
rebinds an old spec to the enlarged catalog.

The output's parent directory must exist. The output must be separate from the
spec, baseline and runtime data directories. All validation finishes before the
existing exclusive hard-link writer publishes one file. Identical reruns retain
bytes and modification time; changed existing output is refused. A pending
identity/source decision produces a clearly pending review artifact, which the
integration handoff refuses. Malformed or conflicting facts produce no artifact.

## Explicit spec contract

The top-level object has exactly these fields:

| Field | Contract |
| --- | --- |
| `schema` | `formulation-packet-spec/1` |
| `batch_id` | Nonempty stable batch label |
| `baseline_sha256` | Raw file SHA-256 under keys `materials`, `reference_properties`, `sources` |
| `source_records` | List of `{record, sha256}`; each record is a complete source registry object |
| `contexts` | Four maps named `identity`, `grade`, `state`, `property`; each maps context names to explicit field objects |
| `formulations` | Explicit identity, grade, state and property references described below |
| `identity_crosswalk` | Source-designation mappings and bounded human identity judgments |
| `review` | Preserved source review and limitation statements; never compiler-generated approval |

A record reference is `{"context": "NAME", "fields": {...}}`. The compiler
deeply combines the named context and the row's fields. Both may supply different
members of the same nested object, but neither may overwrite an existing leaf,
even with an equal value. Use a different context when conditions differ. Empty
named contexts allow complete explicit records without sharing. Lists are
authored whole, never concatenated or normalized.

Each formulation has exactly:

```json
{
  "identity": {"context": "identity_common", "fields": {}},
  "grades": [],
  "states": [
    {
      "record": {"context": "state_common", "fields": {}},
      "properties": [{"context": "property_common", "fields": {}}]
    }
  ]
}
```

This is a shape illustration, not a complete scientific fixture. The expanded
records must satisfy the existing material-reference schemas. All IDs, names in
four language slots, links, source designations, original numeric strings,
units, method/condition evidence, statistics and explicit unknowns are authored.
The compiler does not fill missing schema fields. It accepts polymer, composite
and inorganic identities. Grades remain explicit; an unknown grade stays null.
Several compositions may share one source record and common explicitly authored
context. An empty `grades` list and one state per identity require no special
case. Composition, phase and sample qualifiers still require source evidence;
the compiler does not infer chemical equivalence or a new identity from a sample.

Each grade and state must belong to its enclosing identity. Every property must
belong to its enclosing state, whose `property_ids` must name exactly the supplied
properties. At least one numeric, source-linked property is required per state.
The validator checks source URLs, property dimensions/units, source documents,
evidence support and the existing catalog-only scientific limitations.

`source_records[].sha256` hashes the **canonical registry record**, not a PDF:

```python
from scripts.prepare_formulation_packet import record_sha256
source_pin = record_sha256(complete_source_record)
```

Canonical encoding is UTF-8, sorted keys, compact separators, no nonfinite values,
and one final newline. The packet's `spec_sha256` uses the same encoding over the
complete parsed spec. Original source-document hashes and whether those bytes
were retained remain separate, explicit property/source evidence. Existing
source IDs must match the pinned baseline record exactly; changed attribution
or license text cannot silently replace an existing source.

## Identity and source-review boundaries

Each crosswalk entry has exactly `identity_id`, `source_id`,
`source_designations`, `disposition`, `evidence`, and `note`:

- `source_designations` lists exactly the states linked to that identity/source
  through their property records. Multiple states may share one designation.
- `disposition` is `existing`, `distinct`, or `pending`. Existing identities must
  occur in the pinned baseline; distinct IDs must be absent. These are supplied
  human judgments, not scientific equivalence inferred by the compiler.
- `evidence` is a nonempty list of ordinary source/URL/locator/support objects
  supporting `material_identity`. The registered source must also support the
  emitted identity and state, with the linked properties resolving to that source.
- `note` records the bounded identity decision and unresolved distinctions.

The compiler builds a collision index from the actual pinned baseline's
source/state/property links. Reusing a source designation, name or alias under
another identity is refused, including collisions between different packets in
one integration manifest. Linked grades' designations and aliases are indexed
under their actual grade-supporting evidence sources, which may differ from a
property's primary paper. Unrelated supplier labels are not assigned to that paper.
Comparison trims and case-folds text conservatively;
it does not normalize chemical names or fractions. Ambiguous collisions require
an explicit curation decision outside this compiler, not an override switch.
Changing every label or using another source can still conceal equivalence;
machine checks do not replace the source-qualified identity review. Missing
crosswalks are reported as pending, never silently treated as unique.

`review` must include `formal_admitted_delta: 0`, a `verification` object with
`independent_scientific_review: false` and `raw_data_reanalysis: false`, and
`source_reviews`. Other original review fields are preserved. Each source-review
row has exactly `source_id`, `status` (`selected_facts_checked` or `pending`), and
a nonempty `note` stating the inspection and rights scope. Unknown/missing rights
or missing/pending source review keeps handoff pending. Normally this bounded lane
requires an explicit source reuse-license status and identifier; it does not infer
a grant from a URL, DOI, hash, or a compiler-generated label.

One existing source-specific notice can also be reused: the complete registry
record `swanson_tatge_1953_nbs_circ539v1`, canonical SHA-256
`af69ed341f5d81b6cd651b984ce489462f8ea798dfa95a98ace78a91b153bade`,
must already occur unchanged in the pinned baseline. Its NIST employee-authored
government-work notice and null license identifier remain unchanged. This is not
a general government-publication exception or an SPDX license assignment.
The bounded compiler lane accepts only inorganic, source-calculated
crystallographic `mass_density` references with the existing derived-evidence
contract. Each linked property must identify the original NBS Circular 539,
Volume I PDF URL and document SHA-256
`003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c`.
Changed source records, a missing baseline source or references outside that
scope keep the handoff pending, including when the caller rehashes its inputs.

The authored `selected_facts_checked` source-review note must still describe the
actual selected NBS-authored passages and rights scope. Separately credited
third-party comparisons remain excluded, and the existing NIST attribution is
retained. These machine checks do not determine a passage's authorship, repeat a
source inspection, grant rights or establish scientific approval. No original
PDF, image, full table or extended source text is added to the packet.
Density values and units remain exactly authored; direct bulk measurement,
crystallographic calculation and empirical conversion are distinct contracts.
Thermal conductivity and its units are not supported by the current runtime
property contract and cannot be introduced through a context or category change.

The `handoff_ready` report means these authored declarations and machine contracts
passed. It is not independent scientific review, legal certification, main
admission, or permission to publish. The report distinguishes baseline/candidate
counts from its always-zero formal admitted delta. In the 12cb baseline, 1083
source-qualified identities plus 24 reviewed computed buckets give 1107 project
identities; 62 computed examples remain excluded. The compiler does not touch
those computed registries or count candidates as completed project materials.

## Single-artifact integration handoff

The prepared artifact has exactly `schema`, `spec_sha256`, `input`, `catalogs`,
`review`, and `report`. `catalogs` holds append tables, not an enlarged runtime
snapshot. `input` preserves the full spec. Integration manifest version 2 accepts
one packet descriptor per batch:

```json
{
  "schema": "experimental-material-integration/2",
  "scope": "local-experimental-only",
  "baseline_sha256": {
    "materials": "BASELINE_MATERIALS_SHA256",
    "reference_properties": "BASELINE_PROPERTIES_SHA256",
    "sources": "BASELINE_SOURCES_SHA256"
  },
  "batches": [{
    "id": "YOUR_BATCH_ID",
    "candidate_commit": "FULL_CANDIDATE_COMMIT_SHA",
    "packet": {"path": "../YOUR_BATCH/prepared-packet.json", "sha256": "RAW_PACKET_FILE_SHA256"}
  }],
  "status_adjustments": [],
  "pending_gates": ["Experimental integration only; main release remains separate."],
  "released_main_count": 1081
}
```

Replace every placeholder with the actual archived value. Packet paths remain
inside `experimental/material-batches`. The manifest binds raw packet bytes,
batch identity and the same baseline pins. Version 2 permits no status adjustment.
The integrator calls `validate_prepared_packet` to reconstruct the full packet
from the embedded spec and pinned baseline, compares every output field, and
requires a ready result before using the existing merge and immutable writer.
Rehashing a modified report, catalog or review cannot bypass that replay.

```sh
python scripts/integrate_material_candidates.py \
  --baseline-dir PATH_TO_PINNED_BASELINE_DATA \
  --manifest experimental/material-batches/YOUR_INTEGRATION/integration.json \
  --output PATH_TO_NEW_INTEGRATION_ARTIFACT.json
```

Version 1 manifests retain their four independent packet descriptors and existing
artifact contract. Version 2 emits the same combined catalog/report artifact;
each batch's `inputs.packet` records its raw packet descriptor, and `added_ids`
and `existing_ids` remain available for audit and exact predecessor recovery.
Neither command changes runtime data or publishes the artifact.
