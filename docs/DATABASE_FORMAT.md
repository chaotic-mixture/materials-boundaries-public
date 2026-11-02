# Database download format, version 1

Use `python -m materials_boundaries.database summary` to inspect the current
property selection before planning data updates. The query, quantity, category
and primary-source filters are the same as for query/export. The report binds
the full database fingerprint and counts selected properties, distinct joined
identities/states, evidence kinds, native condition statuses, uncertainty and
sample-count statuses. Source-license counts cover distinct referenced sources,
including secondary evidence; they are not property counts or a legal decision.
`__missing__` means a status field was absent, null or empty. It remains distinct
from source-reported unknown/not-applicable labels. Condition fields are the
union of status objects present in the selected records; list-valued extensions
such as `additional_conditions` are preserved in query/export, not interpreted
as missing status fields here. Absent fields in the status union are counted
as missing. Empty selections yield zero counts, not whole-database coverage.
These descriptive counts do not establish admission, scientific approval or
release. Identity counts cover identities with a selected property only.

```sh
python -m materials_boundaries.database summary --category composite
python -m materials_boundaries.database summary --query C11000 --quantity mass_density
```

`python -m materials_boundaries.database export --output snapshot` creates
`records.jsonl` and `manifest.json`. Each JSONL line is one source-qualified
property; it is not a universal material constant. JSON preserves native units,
numeric strings and explicit unknowns rather than silently converting them.

| Field | Meaning |
| --- | --- |
| `record_id`, `record_version` | Stable property identifier and its native revision |
| `database_snapshot` | SHA-256 of canonical content of all three database tables |
| `identity` | Source-qualified identity, category, names and aliases |
| `state` | Material state, identity/grade links, applicable property IDs |
| `grade` | Grade record, or null when no grade is assigned |
| `property` | Complete native property, value, units, conditions, uncertainty, sample count, source evidence and limitations |
| `sources` | Primary and secondary evidence sources with their original license metadata |
| `review` | Existing transcription status and independent scientific review flag; export does not promote either |
| `rights_note` | Reminder that software licensing does not relicense external sources |

Within the unchanged 1.0 native field contract, identity, grade, state and
property record revisions accept `1.0.N` (nonnegative patch number, no leading
zeros). Corrections retain IDs and increment the affected record's patch
revision. Table `schema_version` remains `1.0.0`; a record correction does not
change the database schema or software version. Incompatible field contracts,
prerelease labels and malformed versions are not authorized by this allowance.

Native table contracts: [materials](../schemas/materials.schema.json),
[properties](../schemas/reference_properties.schema.json),
[sources](../schemas/sources.schema.json). State `property_ids` may refer to
properties omitted by a filtered export: the export preserves the original state,
not a rewritten subset of its scientific record.

The [export envelope schema](../schemas/database-record.schema.json) checks the
wrapper fields and review types. It deliberately does not replace the linked
native table schemas or scientific contract checks for nested data.

The manifest specifies format, full-database fingerprint, selection filters,
exported property count and SHA-256 of the exact JSONL bytes. A filtered export's
fingerprint refers to the full local database; its file checksum identifies the
selected download. Verification checks internal consistency, not publisher
authenticity or source truth. For citation, retain repository commit/release,
database fingerprint, record ID/version and primary-source citation together.

`verify --snapshot PATH` checks exported integrity. `diff --before OLD --snapshot
NEW` requires the same filters and reports added, modified and deleted property
records, including changes to their joined metadata. It does not compare unused
sources or source-less identities as property changes.

`check --scientific-contracts` runs the existing complete current-material graph
contracts once: structure, source links, reported values, conditions and supported
derivations. It neither repeats historical regression nor certifies independent
scientific review.

For repeated updates, `ValidationSession(Database(...))` validates an in-memory
baseline once. Its `validate(candidate)` always repeats global shape, uniqueness,
ownership, evidence and source-class checks. Property-local value and derivation
checks are reused only when the complete property, state and identity match the
validated baseline. Any source-table change invalidates all property reuse.
There is no persisted pass cache to forge or accidentally reuse with a different
validator version. The default full validator remains available and unchanged
in scope.

```sh
python -m materials_boundaries.database validate-update --before old-native-tables --data-dir new-native-tables
```

Each directory contains `materials.json`, `reference_properties.json` and
`sources.json`. A fresh CLI invocation validates its baseline first, so it is not
a promise that a one-off invocation is faster. Long-lived ingestion sessions
reuse the baseline across candidate updates. Reports distinguish executed and
reused property checks and bind both content fingerprints. Filtered download
snapshots are not sufficient to establish a complete scientific baseline.
