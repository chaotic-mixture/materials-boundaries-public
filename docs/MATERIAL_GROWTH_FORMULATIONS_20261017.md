# Polymer formulation increment, 2026-10-17

This experiment extends NC2 baseline `7388976fa914399a210322d019e3081f201ff08f`
through the existing offline candidate integration command. It selects three
distinct study-defined formulations, with one state and one property each.

| Formulation | Category | Selected measured property | Primary source |
| --- | --- | --- | --- |
| SPO-2 suberin/tall-oil-polyol rigid polyurethane foam | Polymer | Apparent density 40.7 kg/m3 | Ivdre et al. (2024), Tables 9-10, [DOI 10.3390/polym16070942](https://doi.org/10.3390/polym16070942) |
| B10 PBS / 10 wt.% Indulin AT lignin simple blend | Composite | Young's modulus mean 922 MPa, SD 77 MPa, n=10 | Ewurum and McDonald (2025), Table 6, [DOI 10.3390/polym17020194](https://doi.org/10.3390/polym17020194) |
| B30 PBS / 30 wt.% Indulin AT lignin simple blend | Composite | Young's modulus mean 969 MPa, SD 77 MPa, n=10 | Same article, distinct B30 row |

SPO-2 uses different polymer-forming polyols from existing LPO-1. Its Table 9
inputs include 67 g SA-C_TOFA(50:50)/TMP and 33 g SA-E_ETOFA(50:50)/TMP.
These are formulation inputs, not a final composition assay. The source reports
ISO 845:2006 and free-rise preparation followed by 24-hour room-temperature
curing. Density aggregation, sample count, uncertainty, test temperature and
humidity remain unknown. Mechanical-test counts and thermal-conductivity
temperatures do not qualify this density measurement.

B10 and B30 are separately prepared and measured simple blends. Their lignin
percentages are relative to total polymer mass, distinct from current B20 and
from reaction-extruded DCP-containing R-series formulations. The selected
injection-molded microtensile specimens were tested under source-reported ASTM
D1708 using an Instron 5500R-1132, Epsilon 3542 extensometer and 1 mm/min
crosshead speed. Test temperature, humidity, post-molding conditioning and the
numerical modulus fitting window remain unknown. The source's PBS grade
FZ91PM/FZ91PB is unresolved; no new grade is assigned. Preserve mean and SD
as reported, without converting SD into confidence bounds or a design value.

Both original-study selections have explicit CC BY 4.0 licensing and no separate
third-party table credit. Attribute the authors and DOI and retain the license
link. Existing source records are reused unchanged; new per-property inspection
metadata records the selected content and exact source asset hash. Source
assets stay outside the product. English fallback names occupy the four required
locale slots without claiming reviewed translations. Independent scientific
review and raw-data reanalysis remain false; all facts remain catalog-only,
non-universal and unsuitable as engineering allowables.

SPO-1 is held because its table density 43.9 kg/m3 conflicts with the narrative
range ending at 43.5. SPO-3, other lignin loadings, reactive formulations and
additional properties are not included. Previously held PA2200/PCL leads remain
excluded. Source counts and repeated measurements do not increase material counts.

## Reproduction and recovery

The integration manifest under
`experimental/material-batches/20261017-polymer-formulations-incremental`
binds both immutable candidate packets and the three baseline resource files.
Use the exact baseline checkout's files without text-mode reserialization:

```sh
python scripts/integrate_material_candidates.py \
  --baseline-dir /path/to/7388976-checkout/materials_boundaries/data \
  --manifest experimental/material-batches/20261017-polymer-formulations-incremental/integration.json \
  --output /path/to/new-output/formulations-integration.json
```

A repeated command verifies identical content and leaves artifact bytes and
mtime unchanged. Full graph validation precedes output. Missing properties,
wrong units, changed source/record content and mismatched input hashes fail
closed. The command produces an experimental package and report; it does not
grant admission or rewrite the runtime catalog. This branch explicitly selects
its validated catalogs as a separate development step.

Removing only these three appended identities, states and properties recovers
the exact NC2 baseline resources. Earlier tests use that recovered snapshot and
retain their historical hash assertions. New runtime pins require a separate
local registry; earlier SQLite anchors are rejected without database mutation,
automatic migration or fallback. The source registry, grades, computed reviews,
held examples and earlier material rows are unchanged.

## Counts and verification boundary

| Category | Experimental core | Experimental project | Remaining to project target 1000 |
| --- | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 0 |
| Metal | 22 | 34 | 966 |
| Inorganic | 26 | 38 | 962 |
| Polymer | 15 | 15 | 985 |
| Composite | 6 | 6 | 994 |
| Total | 1079 | 1103 | Four categories remain below target |

This is growth from 1100 to 1103 in one experimental lineage, including the same
24 reviewed computed compositions. Other branches are not added to this total.
Released main remains **1081 = 1057 + 24**; all 62 unadmitted computed examples
remain excluded. Matching package pins and the API's existing
`formal_project_admission_count` field do not publish a main release.

Focused checks cover source facts and unknowns, exact predecessor recovery,
complete catalog validity, idempotent CLI replay, invalid-input rejection,
resource pins, local API counts and installed-package behavior. Actual commands
and outcomes are retained in the delivery evidence. No additional full core
suite, independent experimental replication or completed remote CI is implied.
DOI registration, main release and public deployment remain deferred. Standard
interoperability and further computation/interface work remain future work.
