# Bounded oxide source-family growth

This experiment starts at `c90188dcd5ac3a19863be0b49419722571b17eff` and adds
six distinct composition identities from one retained primary source: NBS
Circular 539, Volume I (1953). The packet generator and v2 integration path
prepare and replay one coherent batch. Source documents and raw structures
are not bundled. Source retrieval used zero new network requests.

| Identity | Crystallographic density (g/cm^3) | Density temperature (degrees C) |
| --- | ---: | ---: |
| BeO | 3.008 | 26 |
| MgO | 3.581 | 25 |
| CaO | 3.345 | 27 |
| TiO2, rutile state | 4.250 | 26 |
| CuO | 6.51 | 26 |
| CeO2 | 7.215 | 26 |

These values were calculated in the source from measured lattice parameters.
They are not direct bulk density measurements, DFT predictions, independent
replications, or engineering allowables. Reported precision and temperature
are retained. Sample counts, uncertainty and unreported specimen conditions
are not inferred. Anatase remains outside this batch and would be a state of
the same TiO2 identity, not an additional material.

The selected factual rows reuse the exact existing NBS source record. Its
specific employee-authored government-work notice retains a null license
identifier. The compiler checks the pinned source object, document and narrow
crystallographic density scope; it does not create a general government-data
exception or assign an SPDX license. Selected-source transcription review
does not replace scientific review or source-specific licensing review.

Experimental core totals are 1090 identities, 21 grades, 1090 states,
1090 properties and 116 sources. The project total is 1114, consisting of
1090 source-qualified identities and the unchanged 24 reviewed computed
compositions. The other 62 computed examples remain unadmitted and excluded.

| Primary category | Core | Project including reviewed computed | Gap to 1000 |
| --- | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 0 |
| Metal | 22 | 34 | 966 |
| Inorganic | 32 | 44 | 956 |
| Polymer | 16 | 16 | 984 |
| Composite | 10 | 10 | 990 |

Only the inorganic category grows, by six. The released main count remains
1081 and the packet's formal admitted delta remains zero. Main merge, DOI
registration and public deployment are outside this experiment.

The reusable test-only `material_append_history.py` engine recovers a finite
predecessor from pinned packets, exact newly added IDs and full catalog
hashes. Shared sources are retained, not removed with the candidates. The
new frozen data and file ledgers preserve c901 and every older ledger. They
reject partial additions, changed objects, reordered successors and unrelated
changes rather than accepting arbitrary append data.

Run the bounded checks with
`python scripts/run_source_family_growth_ci.py --test`.
The companion `--validate-scope` checks the exact change inventory
and workflow; `--wheel-dir` and `--dependency-dir` exercise all six built
wheels in a fresh installed environment. Actual results are recorded in the
parent handoff and branch CI, without claiming a full repository regression.

See the [batch evidence and source limits](../experimental/material-batches/nbs-oxide-density-20261019/README.md)
and [generator contract](FORMULATION_PACKET_PREPARATION.md). The next useful
batch should extend other source-qualified compositions; neither extra
phases, repeated calculations nor pending candidates close category targets.
