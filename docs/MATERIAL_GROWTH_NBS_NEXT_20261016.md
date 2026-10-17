# Ten further NBS crystal references

This local experiment extends commit
`742890fb780142ad82e0b3a012498362c494d1ab` with ten new material identities,
ten source-scoped states and ten numerical density references. It adds seven
metal and three inorganic identities, no grades and no sources. All 1065 prior
core identities and their states/properties remain byte-recoverable; the entire
115-record source registry is unchanged. Main remains at 1081 project entries.

| Primary class | Released main project | Prior local project | Current local project | Increment | Remaining to 1000 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 1010 | 0 | 0 |
| Metal | 26 | 27 | 34 | +7 | 966 |
| Inorganic | 28 | 35 | 38 | +3 | 962 |
| Polymer | 14 | 14 | 14 | 0 | 986 |
| Composite | 3 | 3 | 3 | 0 | 997 |
| Total | 1081 | 1089 | 1099 | +10 | 3911 |

The core is 1075 identities: natural 1010, metal 22, inorganic 26, polymer 14 and
composite 3. The project add-on combines that core with exactly the unchanged 24
formal computed composition buckets. The separate 62 computed examples remain
unadmitted, and the earlier seven-record seed and held NOMAD candidates remain
excluded. Neither calculations nor source records inflate identity counts. Only
natural currently meets the five-class goal.

## Selected facts and source scope

All ten source-preserved values use grams per cubic centimeter (`g/cm^3`). They
are NBS calculations from measured X-ray lattice parameters, with
`published_measurement_derived_reference`, `source_reports_calculation` and
`density_basis: crystallographic`. They are not direct specimen bulk-density or
powder-packing measurements, DFT predictions or newly recomputed values.

| Identity | Selected sample | Exact density | Density temperature | Printed / one-based PDF page |
| --- | --- | --- | --- | --- |
| Palladium | Johnson, Matthey sponge | 12.04 | 25 degrees C | 21 / 25 |
| Silver | Johnson, Matthey, London | 10.500 | 25 degrees C | 24 / 28 |
| Tin | Johnson, Matthey white/beta sample | 7.286 | 26 degrees C | 26 / 30 |
| Tantalum | Johnson, Matthey, vacuum annealed | 16.626 | 25 degrees C | 31 / 35 |
| Platinum | NBS Chemistry Division | 21.472 | 25 degrees C | 31 / 35 |
| Gold | NBS-purified sample | 19.302 | 25 degrees C | 33 / 37 |
| Lead | American Smelting and Refining Company | 11.341 | 25 degrees C | 34 / 38 |
| Ammonium chloride | J. T. Baker, recrystallized by sublimation | 1.527 | 26 degrees C | 61 / 65 |
| Lithium chloride | Mallinckrodt label SDD | 2.074 | 25 degrees C | 62 / 66 |
| Potassium fluoride | J. T. Baker, dried sample | 2.524 | 26 degrees C | 65 / 69 |

The source is Howard E. Swanson and Eleanor Tatge (1953), *Standard X-ray
Diffraction Powder Patterns, Volume I*, NBS Circular 539,
[DOI 10.6028/NBS.CIRC.539v1](https://doi.org/10.6028/NBS.CIRC.539v1),
[official PDF](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular539v1.pdf).
The retained official PDF SHA-256 is
`003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c`.
The source agents inspected the new selected page images and compared the
transcriptions with extracted text. The existing source/rights finding was
reused without repeating a full-source audit. Introduction printed page 2 /
PDF page 6 supplies the density-unit convention. Packet reviews retain detailed
sample, phase, lattice, value and condition locators.

Only selected NBS-authored facts and original curation are included under the
already established government-work scope. Republished courtesy of the National
Institute of Standards and Technology. Third-party comparison content, source
PDFs, page images, complete tables, raw structures and extended source prose are
excluded. No separate source row, new license inference or approval gate is added.

## Identity and remaining unknowns

The frozen baseline was checked across all 1065 core identities, names, aliases,
grades and states, the 24 formal computed compositions and the 62 excluded
examples. These ten named compositions have no known existing identity collision.
An elemental impurity in another material or an element-containing compound is
not an elemental-material identity. Suppliers, sample labels, preparation and
temperature qualify states and properties; they do not add identities. Tin is
counted once, with beta as its selected state. No exact total sample stoichiometry
or certified purity is inferred from the composition used for deduplication.

Ge, Zn, Mo, W, Cu and Ni were not selected because source-qualified identities
already exist; the earlier LiF, KCl, CaF2, KBr, KI, NaF and BaF2 entries also remain
single identities. This is a focused selection, not an exhaustive review of all
materials in the publication.

Density uncertainty, pressure and independent specimen/repeat counts remain
unknown. Purity qualifiers and unspecified percentage bases are preserved.
Palladium's vacuum treatment is not its density temperature. Silver's purity
remains greater-than qualified. Tin's 99.997 percent is by difference, and its
160-degree anneal does not replace its 26-degree density temperature. Tantalum's
residual hydride, platinum's estimated purity, gold's approximate purity/possible
silver and lead's believed-greater-than purity remain explicit. The metals B
26-degree powder-pattern conditions remain separate from 25-degree densities.

NH4Cl cell content is not a specimen count. LiCl label SDD does not create a grade.
KF's sodium finding and NaF solid-solution discussion do not establish an exact
solid-solution composition or percentage basis. Its 220-degree drying is separate
from its 26-degree density temperature. Petrolatum mounting and loose packing do
not convert crystallographic density to a composite or packing-density result.

All locale slots retain explicit English fallback status. Source transcription
checking does not claim native-language review, independent human scientific
review or raw-data reanalysis. Those two scientific flags stay false; every
property remains `catalog_only`, `universal_bound: false` and
`engineering_allowable: false`. These are existing scope limits, not new blockers
or a request for an additional manual signature. No unresolved concrete source,
rights or identity hold was reported for these ten selected facts.

## Repeat the local increment

The three candidate packets are frozen at
`ba389d33c1fe53e16539dd7fc185c3bd0f444757`. The
[manifest](../experimental/material-batches/20261016-nbs-next-incremental/integration.json)
binds their material, property, reused-source and review bytes plus the three
742890f baseline files. Batches are ordered metals A, metals B, then inorganic;
no status adjustments are needed.

Use a separate checkout of 742890f for the baseline and an existing private output
directory. From this branch run:

```sh
python -B scripts/integrate_material_candidates.py \
  --baseline-dir /path/to/742890f-checkout/materials_boundaries/data \
  --manifest experimental/material-batches/20261016-nbs-next-incremental/integration.json \
  --output /path/to/private-output/nbs-next-increment.json
```

The existing command validates all input hashes and the complete graph, then
atomically writes one immutable catalog/report package. It does not overwrite
runtime or baseline data. An actual first run created the retained package; an
actual identical repeat returned unchanged with the same bytes and modification
time. Conflicting output and changed input remain rejected by the existing
contract. Runtime materials and properties are the package graphs serialized
with UTF-8, indent two and a trailing newline. Removing exactly the new ten
identities/states/properties recovers the baseline bytes. Sources are unchanged
and were not rewritten.

Formal resource pins and the query manifest match the new runtime bytes. The new
query anchor is `8da7a2000110021ad0a20b2a83dc1b02420a0bf9e3d1b68eb71b70f127965efe`.
Old SQLite anchors, including the immediately preceding c03c48c4 baseline, remain
rejected without migration or mutation of existing user databases. Use a distinct
local registry with this installation. Existing API field names such as
`formal_project_admission_count` report the local package's 1099 entries; they do
not announce a new main release. Relationship counts are 1075 identities, 1080
supported memberships and one unchanged identity relationship.

## Validation and publication boundary

The local integration report records ten new identities, ten states, ten
properties, zero grades and zero sources, with released-main delta zero. Focused
tests cover frozen inputs, exact prior-byte recovery, source reuse, replay,
property/condition contracts, category totals and old-anchor rejection. Actual
test outcomes are recorded in the handoff; this document does not turn planned
checks into passes. Earlier full-suite evidence remains historical and is not
reported as a new full-suite execution. Skips are never counted as passes.

Publication remains deferred; no new login flow,
push, main merge, remote CI, permission change, deployment or DOI registration
was performed. A later release remains coordinated by the parent thread. No
additional human-signature or repeat-license-review prerequisite was invented.
