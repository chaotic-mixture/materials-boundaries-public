# Migration to v0.33.0

This is a catalog-only addition of eight source-qualified identities and eight
experimental density facts: **43 + 8 = 51 identities**, with **19 qualified
grades, 51 states and 51 properties**. Seven original sources bring the full
source registry from **98 to 105**. No new grade is inferred from a study
formulation/type label, supplier or precursor designation.

There is **no schema or runtime capability extension**. Material and reference-
property envelope versions remain **1.0.0**. Existing density units, evidence
classes, method types and uncertainty alternatives represent every addition.
There is no new physical quantity, evaluator, material-specific branch, unit
conversion feature, statistical calculator or ranking. Upgrade catalog data
and software release metadata together; consumers already implementing the
v0.32.0 contract do not need a new schema alternative for these records.

## Preserve the selected facts and their meanings

- LPO-1 PUR: **43.2 kg/m³**, apparent density, reported value, unknown n and
  uncertainty. The Lupranol recipe is distinct from the suberin-based SPO
  series. **40 kg/m³** is compression normalization and **94 vol.%** is
  closed-cell content, not the selected density or total porosity
- AMD5-derived Al–Mg–Ti SPS foam: **0.45 g/cm³**, reported value, unknown
  density n and uncertainty. Keep `density_basis: not_stated` with the
  paraffin-sealed, pore-inclusive Archimedes/ethanol method. Preserve Table 4
  “Underwater Weight” / ethanol and Table 6 g/m³ / Table 4 g/cm³ discrepancies
- Quercus suber reproduction cork: **0.17 g/cm³**, `reported_value`,
  **n=10** in the selected species/treatment group. Its existing
  `reported_measures` envelope contains numeric absolute **SD 0.01 g/cm³**,
  with evidence and a note that the central aggregation is not stated.
  Do not relabel it a reported mean, use the legacy mean-only SD alternative,
  erase the known SD or construct confidence/min-max endpoints
- Moso / Guadua bamboo: **746 / 655 kg/m³**, separate reported species
  averages, **six specimens each** (three nodal and three internodal),
  no reported density uncertainty. The exact averaging estimator and repeated
  density-measurement count are not stated. Do not reconstruct values from
  mean geometry/mass, transfer mechanical CoVs or split nodal/internodal
  specimens into additional identities
- Al-Taouab CP plaster: **1103.13 kg/m³**, apparent density, reported value,
  unknown density n/aggregation/uncertainty. Zero wheat straw and
  water/plaster 0.7 define the selected laboratory formulation. Do not claim
  chemical purity, a measured single hydrate phase or certified oven-dry state
- Boral-soil control brick: **2122 kg/m³**, bulk density, `reported_value`,
  unknown density-specific n/aggregation/uncertainty. The global triplicate/
  average statement lies in the raw-material tests paragraph; its density
  applicability is unclear. **Do not claim a density-specific mean or n=3**.
  The laboratory control is 100% soil / 0% biosolids, not a marketed Boral grade
- K1 quartz arenite: **2.34 ± 0.01 g/cm³**, bulk density, `reported_mean`,
  **five replicates**. Say **reported average**, not explicitly arithmetic
  average. Keep the existing `reported_plus_minus_unspecified` alternative;
  do not label ± as SD, SE, CI or range or derive 2.33–2.35 as measured limits.
  Preserve the dimensions / hydrostatic-volume ambiguity in the density method

The [coverage note](MATERIAL_COVERAGE_v0.33.0.md) gives exact cell locators,
preparation, density-method scope and source-specific exclusions. Apparent/bulk
and unknown source labels remain distinct from an interpretation of the physical
measurement. Foam/cork/bamboo do not become skeletal-density records. Cork and
both bamboos use the existing broad `composite` category only as hierarchical
natural tissue, without an engineered resin-binder or laminate claim.

## Conditions and exclusions remain explicit

Every new exact density-test temperature is unknown. Do not replace it with a
cure, drying, firing, conditioning, thermal-test or reference-fluid temperature.
Cork's **25 ± 5 °C / 60 ± 5% RH** is conditioning. Bamboo's **15.8%** moisture
is a study-wide average; species/specimen values remain unknown. Moso and Guadua
shipping containers were fumigated; Guadua also had borax treatment and pierced
internal nodes. Do not label either bamboo generically untreated. Cork's
“untreated” means no study boiling intervention, not verified lifelong absence
of commercial treatment.

Do not import boiled cork as a second identity, the other cork species' green
density 0.39 g/cm³, other PUR formulations or aluminum-foam routes, or
supplementary compression/thermal/porosity results as additional reference-
property records in this batch. Qualified contextual state metadata remain
separate: LPO-1 closed-cell content, AMD5 source-calculated porosity and K1
reported effective/open porosity do not create extra property records. Do not
import Boral's regression-estimated thermal conductivity as a measured property.
Do not infer density-specific standards
from bamboo specimen/compression or sandstone mechanical standards. Unknown
counts, methods, moisture, exact temperature and statistical aggregation remain
unknown; absence of reported uncertainty does not mean zero uncertainty.

## Compatibility and verification gates

The compatibility requirement preserves all prior **43** identities, **19**
grades, **43** states and **43** properties, their source records and rendered
outputs. Earlier schemas, runtime behavior, eight executable rules, claim/model/
observation/prediction families, scientific fixtures and examples are not
expanded or rewritten. New English, Chinese, Japanese and German material
labels retain source qualifications; canonical machine JSON remains language-
independent. Machine-assisted labels do not establish native-language review.

Fresh evaluations/reports carry package version **0.33.0**. Strict replay needs
its matching software/catalog snapshot. Regenerate older reports explicitly
from retained inputs when needed; do not rewrite historical outputs or loosen
replay to disguise the version change.

Independent source-transcription review accepted the eight selected values
without numerical corrections. This does not establish independent scientific
review, raw-data reanalysis, software validation or release completion. Before
admission, validate the exact final graph with runtime and generated schemas;
check source/evidence links, identity/grade/count semantics and all exact value
strings; compare prior records and outputs; verify four-language text/JSON and
scientific-scope mutation refusals; run the full unit suite, catalog validators,
wheel metadata and isolated installed-wheel checks. These are release gates,
not an assertion in this document that they have already passed.

All new facts remain `catalog_only`, with non-universal/non-allowable flags and
`independent_scientific_review: false`, `raw_data_reanalysis: false`. Seven
article-specific CC BY 4.0 notices retain full [attribution and reuse scope](../THIRD_PARTY_NOTICES.md#porous-natural-and-mineral-references-v0330),
including the bamboo generic-metadata/license discrepancy. Only selected facts
and original curation belong in the public package; source PDFs, full HTML/XML,
whole tables, figures, screenshots and source dumps remain excluded. No
repository push, publication or release completion is implied here.
