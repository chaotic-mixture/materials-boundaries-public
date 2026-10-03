# v0.24.0: four annealed PAHT-CF source observations

This bounded release adds four catalog-only median UTS observations and one
source: 16 observations from five studies, 53 sources, 36 claims, five
temperature-model records and 12 computational-prediction records. The eight
executable claim/rule pairs remain unchanged.

The [source guide](PAHT_CF_ANNEALED_OBSERVATIONS.md) states exact cells, median/SD
semantics, contextual SD units, reported n=5, preparation ambiguity, 10 mm/s rate,
unknown stress/geometry/moisture/temperature details, version limits and rights.
No new plot or cross-study comparison is enabled.

- New family: `zach_2025_paht_cf_annealed_tensile_temperature_v1`
- New source: `zach_dudescu2025jcs9110624`
- New dataset: `zach-2025-paht-cf-annealed-fff-uts-temperature`
- Four source rows: annealed, ±45°, 25/50/100/150 °C
- Median strings and separate SD strings retained; SD MPa unit is contextual,
  and SI SD scaling is conditional. No median ± SD interval is presented
- Four-language text, HTML, SVG, JSON and CSV inspection; conditional CSV
  median/SD columns do not change old-only CSV output shape
- Additive closed schema branches retain observation 1.3.0 and inspection
  1.1.0; legacy branches and Ciganas plot schema/profile stay closed and unchanged
- Quantity-only UTS filters now return both studies. Add `--source-id` for one
  source. Record/source IDs and metadata remain explicit in every view
- Regenerate saved inspection/plot bundles when upgrading because their
  engine-version field changes; published example files are historical artifacts

All old scientific records, source records, preexisting fixtures, executable
semantics and generated examples are retained unchanged. Historical PA12
tests now use an exact source selector, positive membrane-type selectors and
exact record/source IDs in place of positional assumptions. Their original
scientific assertions are retained. The new exact test-lineage ledger records
these narrow scope repairs and the necessary acyclic helper transitions across
five old test/helper files, rather than rewriting prior fixture hashes. Preservation tests
separately establish old-record and old-output parity; they do not certify
science, metrology, license clearance or cross-study equivalence.
