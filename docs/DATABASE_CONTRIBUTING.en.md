# Contribute and update data

A data record describes one property for one material state reported by one source. It is not a context-free material constant. Keep material identities, grades, states, and properties under stable IDs. Revise an existing fact under its existing ID and increment its record version. Use a new record for an independent source or a distinct material state.

## What to include

1. The source URL or DOI, exact page, table, or cell locator, source version, and date checked.
2. Material identity and state, property name, source-reported value, and original unit. Do not present a converted value as the source's original value.
3. Temperature, direction, method, specimen count, and uncertainty. Preserve an explicit unknown when the source does not report a condition.
4. The source's reuse status and the exact scope of content included. Do not claim an open license unless it has been verified.
5. The reason for the change and a list of affected, added, revised, or removed records. Explain removals. Do not hide corrections by changing IDs.

The machine-readable formats are defined in `schemas/materials.schema.json`, `schemas/reference_properties.schema.json`, and `schemas/sources.schema.json`. A record that passes schema or database relationship checks is not thereby scientifically validated.

## Three stages

- **Candidate**: Data and a change report in a pull request. They can be discussed and corrected, but are not part of the published snapshot.
- **Reviewed**: A reviewer checks the source, transcription, conditions, relationships, and reuse scope. Record the reviewer, date, conclusion, and exact data fingerprint. Checking a transcription is not independent scientific validation.
- **Published**: Build a snapshot from the exact reviewed data. Keep its manifest, checksums, and change record. Track the database content fingerprint separately from the software version.

The export command creates a local snapshot. It does not assign reviewed or published status automatically.

## Routine checks

Start with a summary to locate records, then inspect the original conditions and source. Summaries report stored states as they are. They do not turn unknown values into reported facts or grant review or release status. Reuse-status counts are deduplicated by linked source.

```sh
python -m materials_boundaries.database summary --category composite
python -m materials_boundaries.database query --query C11000 --quantity mass_density
python -m materials_boundaries.database check
python -m materials_boundaries.database verify --snapshot new-snapshot
python -m materials_boundaries.database diff --before old-snapshot --snapshot new-snapshot
```

Compare snapshots using the same filters. The diff reports added, changed, and removed records and affected sources. A source metadata change propagates to associated exported records. Changes to an unreferenced source do not appear as property changes, although the full database fingerprint still changes.

Data changes receive structural, reference, and affected scientific-constraint checks. Tool changes receive focused tests. Public contracts, calculation engines, and releases receive additional regression checks according to their impact. Historical replay is reserved for explicit compatibility or release work. A diff report does not replace scientific-constraint checks.

## Language versions

This guide describes the data contribution process in English. Other language guides and the four-language interface are available from the [project language support page](I18N.md).
