# Bruns 2020 NBS2 borosilicate candidate packet

This review-only packet is pinned to
`46674771ab851d4c267425b985c8f29c8aea25df`. It proposes four source-qualified
nominal oxide-recipe identities, no grades, four furnace-cooled states, four
measured density means with separate standard deviations, and one source.
The runtime, formal catalog, query baseline, predecessor packets and CI workflow
are unchanged. Prepared and isolated-integrated artifacts both report
`formal_admitted_delta: 0`; the existing release count is not increased.

Source: Sebastian Bruns, Tobias Uesbeck, Dominik Weil, Doris Möncke,
Leo van Wüllen, Karsten Durst and Dominique de Ligny (2020),
*Influence of Al2O3 Addition on Structure and Mechanical Properties of
Borosilicate Glasses*, Frontiers in Materials 7:189.
[Article and DOI](https://doi.org/10.3389/fmats.2020.00189),
[original publisher PDF](https://www.frontiersin.org/journals/materials/articles/10.3389/fmats.2020.00189/pdf),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Copyright 2020 the authors. Changes consist of selected structured factual
transcription, explicit state/measurement qualifications and original review
notes. No endorsement, legal clearance or independent scientific review is claimed.

The reviewed 14-page PDF has SHA-256
`c6268f9f14320e9355bfe04bf02f47eb3d7ca00e30c7281a16fd3b1289913da6`.
Table 1 on PDF p.4 and Table 3 on p.8 were visually checked, alongside
preparation/density methods on pp.2-3 and the rights notice on p.14.
The publisher copyright link resolves to CC BY 4.0. No raw PDF, page image,
full source text, figure or raw measurement is included.

## Selected facts and limits

- Nominal Al2O3 1.0, 1.5, 2.0 and 4.0 mol% recipes have density means
  2.131, 2.133, 2.130 and 2.137 g/cm³, respectively. Corresponding SDs are
  0.006, 0.010, 0.002 and 0.004 g/cm³. Trailing decimal precision is retained.
- Table 1 nominal and ICP-OES compositions are explicitly separate. The
  authors discuss analysis discrepancies and sodium loss. Nominal recipes are
  not certified final stoichiometry; no correction or normalization is made.
- Density is measured by Archimedes displacement in toluene. The source uses
  at least five pieces of 0.1-1.0 g, not a verified five independent replicates.
  Exact n, batch count and readings per piece stay unknown. Mean and SD are
  not converted into a range, confidence interval or standard error.
- The unmarked Table 3 rows inherit the source's furnace-cooled default.
  The 4.0 mol% melt stayed in its crucible, was cooled in a preheated furnace,
  and was drilled out. This exception is not assigned graphite-mold casting,
  a numerical preheat or a separately verified 30 K/h cooling rate.
- Density-test temperature, pressure, humidity and conditioning are unknown.
  Room temperature and about 33% RH for nanoindentation do not transfer.
  The density basis remains `not_stated`, without an assumed true/bulk/apparent
  classification, zero porosity, engineering allowable or calculator use.
- The four identities are distinguished by nominal recipes, not pieces,
  temperature, source branding, density differences or cooling history.
  No quenched state is added. A bounded discovery review found no match in
  1144 legacy identities, 24 admitted computed compositions or 62 excluded
  examples. Related BOROFLOAT 33 is retained unchanged; finite comparison
  is not global proof of chemical inequivalence.

## Reproduce without changing runtime data

Use a Python environment with the repository development dependencies. From
this checkout:

```sh
python scripts/prepare_formulation_packet.py \
  --spec experimental/material-batches/bruns-nbs2-borosilicate-20261023/packet-spec.json \
  --baseline-dir materials_boundaries/data \
  --output /tmp/bruns-prepared-packet.json
python scripts/integrate_material_candidates.py \
  --manifest experimental/material-batches/bruns-nbs2-borosilicate-20261023/integration.json \
  --baseline-dir materials_boundaries/data \
  --output /tmp/bruns-isolated-integration.json
python -m unittest discover -s tests -p test_bruns_borosilicate_packet.py -v
```

Use absent output paths for first creation. Identical replay is a no-op;
nonidentical existing outputs are refused. The integration manifest names the
actual candidate commit. Its result is a detached local package, not a runtime
catalog update. Compiler readiness means only that supplied review gates pass,
not parent approval or scientific admission. The tests verify exact source
facts, qualifications, append-only predecessor preservation, deterministic
replay, immutability, ownership/unit/hash failures and pending review gates.
Actual execution results are recorded separately in `VALIDATION.md`.

Parent review is still required before publication. Runtime/formal/query
integration, main merge, deployment and DOI registration are not performed.
