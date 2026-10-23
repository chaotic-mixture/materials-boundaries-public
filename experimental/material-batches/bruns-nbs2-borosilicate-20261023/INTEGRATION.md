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

## Validation results and limits

The machine-readable record is [integration-validation-results.json](integration-validation-results.json).
It keeps the exact final source IDs, outcomes, all skip IDs/reasons, execution
hashes, six-wheel metadata, earlier failure evidence and distinct snapshot bounds.

- The original candidate stage passed 44 tests. Catalog/schema validation,
  deterministic compiler/integrator replay, predecessor recovery and four-recipe
  source-qualified lookup checks passed.
- On immutable `9b354ef37433878ec1e976c9c7f66b378d70b3b6`, all 1716 source IDs
  are accounted for: **1698 passed, 18 unavailable, zero failures or errors**.
  The unavailable cases are 17 native-Windows cases on Linux and one external
  wood-dossier opt-in case. That wood case separately passed with its frozen
  external fixture; this does not erase the skip inside the aggregate.
- Source coverage was completed across three guarded executions after two
  transport interruptions: 373, 1038 and 305 disjoint terminal IDs. Unfinished
  cases were rerun, not counted as passes. All 895 tracked inputs, dependency
  bytes and interpreter were checked unchanged; abandoned logs/journals and
  terminal markers remained guarded. This establishes exact-ID segmented
  coverage, **not uninterrupted execution or process-global-state equivalence**.
  Abandoned-process closure remains unknown. The observed span, including
  interruptions and recovery, was 24808.496 seconds, not a single-run runtime.
- The initial incomplete run exposed 16 failing cases with 24 failure events.
  Every one reproduced on the clean original baseline. A finite historical
  document-image recovery repair retained the original release pins and
  fail-closed behavior; all 16 cases then passed in final source coverage.
  Original failures remain recorded rather than being relabeled as skips.
- The fresh isolated six-wheel/offline installed aggregate passed all **535**
  cases with zero skips, plus package/license-byte verification, `pip check`,
  32 localized density CLI outputs and the independent installed smoke checks.
  Those tested package bytes remain identical at the later CI checkpoint.
  Separately executed checkout-source platform groups also cover all 535 IDs;
  they are not represented as one aggregate invocation.
- The later CI checkpoint `cc651206d794a1890d3d7101f3541aa9fc79dc38` has a
  1731-case full inventory and a 131-case complete-module hosted selection.
  The initial 131-case targeted benchmark passed with zero skips in 1420.598
  seconds. After the timeout/ledger-only delta, 31 runner cases and 36 exact
  affected workflow/preservation cases passed, with unchanged-input evidence
  for the retained benchmark. These are separate results, **not a full 1731-case
  run or a claim that the final targeted bytes were all rerun together**.
- Hosted CI is explicitly targeted: 131 selected source cases plus all 535
  installed cases per matrix cell. Its 1600 unselected full-source cases are
  **not run**, not passed or skipped. The bounded 90-minute timeout uses twice
  measured targeted-plus-installed runtime plus ten minutes setup margin,
  rounded up. Ubuntu/Python 3.11 and Windows/Python 3.12 hosted cells remain
  **not run at this local checkpoint**; local execution used Linux/Python 3.12.14.

The complete source reproduction path remains:

```sh
python scripts/run_bruns_borosilicate_ci.py --test
```

At this later checkpoint it discovers 1731 source IDs. The distinct bounded
hosted selection is `--targeted-core`; neither mode silently substitutes for
the other. The workflow builds all six local packages and runs the installed
contract with `--wheel-dir dist --dependency-dir dist/dependencies`.

This is an experimental local-validation record, not a main release,
deployment, DOI action or independent scientific approval. No push has
occurred at this checkpoint. Publication and its hosted CI result require
separate confirmation by their actual commit/run evidence.
