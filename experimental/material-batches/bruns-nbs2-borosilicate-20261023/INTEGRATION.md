# Bruns NBS2 experimental runtime integration

This is the current integration record. The original `README.md`,
`VALIDATION.md`, packet, source review and preparation/integration receipts
remain byte-identical to candidate checkpoint
`ab458b08d388b0ac4009a7f9c98138211ae46fa4`; their candidate-only status describes
that earlier checkpoint, not the runtime integration documented here.

The exact four-recipe append was committed on the isolated experimental branch
at `2d940bcbbe13aa0cd0c0726bb5766e98edf62306`, based on
`46674771ab851d4c267425b985c8f29c8aea25df`. No existing catalog record was edited.
The append contains four inorganic identities, four furnace-cooled states,
four experimental density means with separate SDs, one source and no grade.

## Current experimental catalog

- Legacy source-qualified registry: 1148 identities, 31 grades,
  1149 states, 1160 properties and 124 source/provenance records.
- Primary categories: metal 32, inorganic 53, polymer 25, composite 28,
  natural 1010.
- Formal projection: 1172 entries, comprising those 1148 identities plus
  the same 24 reviewed computed composition buckets. Formal categories are
  metal 44, inorganic 65, polymer 25, composite 28 and natural 1010.
- The 62 excluded computed examples, older review artifacts and the
  released-main count of 1081 are unchanged. Experimental projections do
  not claim a main release, global chemical uniqueness or scientific approval.

The four source-qualified identity IDs are:

- `mat_bruns2020_nbs2_al1p0`
- `mat_bruns2020_nbs2_al1p5`
- `mat_bruns2020_nbs2_al2p0`
- `mat_bruns2020_nbs2_al4p0`

Each resolves to exactly one furnace-cooled state and density property.
Quenched rows do not create additional identities. The source's nominal and
ICP-OES compositions remain separate qualified text, not inferred final
stoichiometry. Exact independent n, density-test temperature and conditioning
remain unknown. The 4.0 mol% melt retains the crucible-cooling/drilling exception.
The full attribution, [source DOI](https://doi.org/10.3389/fmats.2020.00189),
[CC BY 4.0 link](https://creativecommons.org/licenses/by/4.0/), source PDF hash,
selected table locators and modification notice are retained in the frozen
packet and `THIRD_PARTY_NOTICES.md`. No original source asset is bundled.

## Exact recovery and usable lookup

The new data ledger is
`tests/fixtures/bruns_borosilicate_data_20261023.json`; the separate file ledger
is `tests/fixtures/bruns_borosilicate_files_20261023.json`.
The finite recovery sequence is Bruns, then the existing adjacency-only
workflow boundary, then Nylon and all earlier material batches. Unknown,
partial, reordered or modified additions still fail closed. Existing ledgers,
packets and source review records are not rewritten.

Current query, formal and ingestion pins are advanced together. Old databases
are not silently migrated or re-anchored. Tests keep predecessor-store access
read-only where supported and reject incompatible writes without migration.
Ingredient mentions such as Al2O3 remain advisory text relations, never proof
that a multicomponent glass is pure alumina or a computed composition identity.

For a concrete core CLI lookup:

```sh
python -m materials_boundaries catalog materials \
  --identity-id mat_bruns2020_nbs2_al1p0 --json
python -m materials_boundaries catalog reference-properties \
  --material-id state_bruns2020_nbs2_al4p0_furnace_cooled --json
```

Replaying the frozen candidate still requires its original baseline, not the
enlarged current catalogs. Recover that baseline through the pinned ledger or
read the three data files from commit `46674771ab851d4c267425b985c8f29c8aea25df`
into a separate directory, then use the existing compiler/integrator commands.

## Validation status

The prior candidate stage passed 44 tests. After runtime integration, current
catalog/schema validation, exact runtime/predecessor smoke checks, the 16-case
history/adjacency/preservation suite, the complete 196-case ingestion suite,
14-case relationship suite, 12-case formal suite, 37-case query transport suite
and the 161-case query catalog subset have passed. The full exact-inventory
source aggregate and fresh six-package installed/offline aggregate are in
progress; this checkpoint does not claim they have passed. Final execution
results will be recorded in `integration-validation-results.json`.

No push, main merge, deployment or DOI operation is part of this local record.
Publication remains withheld for the parent's post-integration implementation
review; this is an internal review checkpoint, not a request for additional
user permission for the already-authorized experimental work.
