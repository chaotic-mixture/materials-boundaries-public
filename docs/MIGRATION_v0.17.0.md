# Migration to v0.17.0

Version **0.17.0** adds one bounded monolayer MoS2 study with two catalog-only
observations. The v0.16.0 first public-release baseline is documented in
[its migration notes](MIGRATION_v0.16.0.md). This version declaration does not
claim a published tag, release date or software DOI.

## Catalog delta

- **34 mechanics claims**, unchanged
- **48 sources**, up from 47 through exactly one appended source:
  `bertolazzi_brivio_kis_2011`; every prior source record is unchanged
- **4 observation records from 2 studies**, up from 2 records in 1 study
- **6 computational predictions**, unchanged
- **5 original synthetic temperature demos / 7 branches**, unchanged
- Exactly **8 executable composite calculation rules**, with unchanged
  numerical behavior, applicability conditions, ordering and evidence

The two new observation IDs are:

- `bertolazzi_2011_mos2_monolayer_in_plane_stiffness_2d`: **180 ± 60 N/m**
- `bertolazzi_2011_mos2_monolayer_breaking_strength_2d`: **15 ± 3 N/m**

Both have `observation_type: experiment_derived_model_dependent`,
`evaluation_support: catalog_only`, `quantity_dimension: force_per_length`,
`si_unit: N/m`, and shared `study_id: bertolazzi_brivio_kis_2011`. Distinct
quantities from the same study do not supply independent confirmation.
Bilayer, graph-digitized and thickness-normalized 3D values are excluded.

## Envelope and downstream readers

- Software/package/engine version becomes **0.17.0**; `CITATION.cff` matches it
- Observation schema advances **1.0.0 → 1.1.0**. It retains a closed graphene
  family and adds a narrowly defined, closed monolayer MoS2 family
- Both old graphene record objects are preserved exactly. Do not migrate their
  statistical labels, assumed Poisson ratio, stress/strain convention, sample
  counts or unknown conditions to those of the new study
- Source schema remains **1.0.0**; claims schema remains **1.10.0**. Other
  scientific schemas and comparison snapshots are unchanged
- JSON keeps the `{schema_version, records}` envelope in every display language;
  update observation consumers that require the old version or assume two
  records, graphene-only preparation, null loading rate or one uncertainty type
- Use stable IDs and family-specific metadata. Unknown stress/strain measures,
  test temperature, atmosphere and humidity are valid and explicit MoS2 nulls;
  no cross-study convention is supplied by default
- Human-readable en/zh/ja/de names and labels preserve canonical IDs, units,
  numerical values, original source wording and verification gaps. Independent
  scientific and native-language review remain unperformed

A closed family is not a permissive generic material-import schema. Further
scientific contracts need separate review; copying a record and changing its
material label does not establish compatible methods, quantities or evidence.
Contribution forms and the existing contributor workflow are preserved.

## Important source-specific distinctions

The inspected source is the EPFL institutional copy of Bertolazzi, Brivio and
Kis, [“Stretching and Breaking of Ultrathin MoS2”](https://doi.org/10.1021/nn203879f),
*ACS Nano* 5(12), 9703–9709 (2011). It is **proof-formatted, with pages A–G**,
despite repository “Published version” / “openaccess” labels. Locators retain
one-based PDF pages plus printed letters. Final-publisher-text identity and
final-page equivalence are unverified; the supplement remains unread.

The source explicitly defines the property ± values as **standard deviations
of experimental values**. `reported_standard_deviation` therefore applies to
these two MoS2 summaries only. No SEM, confidence interval, 68% coverage,
coverage factor, certified bound or exact replicate weighting is inferred.
The old graphene ± values stay `reported_plus_minus_unspecified`; geometric
MoS2 ± tolerances do not automatically become SD.

The printed q metadata is retained in separate fields:

- q = 1/(1.05 − 0.15ν − 0.16ν²)
- assumed ν = 0.27, adopted from bulk MoS2 rather than measured in this study
- stated q = 0.95

The formula at that ν gives approximately **1.002168693051764** by curator
arithmetic. This explicit inconsistency is unresolved. The actual fit constant
used remains **null**, and the arithmetic is neither a replacement source
measurement nor an executable correction. Do not refit the curves, change the
reported stiffness or recompute strength. Strength inherits model dependence
through the fitted stiffness and finite spherical-tip failure model; it is not
the Lee graphene nonlinear constitutive/finite-element inference.

**Nine monolayer membranes** are verified study/stiffness counts, not a
separately verified number of failure events. Failure-event and force-curve
totals remain null. **2 μm/s** is vertical probe translation speed only, not
strain rate, force rate or stress rate. The **400 °C, four-hour vacuum anneal**
is preparation, not test temperature or atmosphere. Test environment and
stress/strain measures remain unknown. These gaps prohibit any presumption
of matched testing with graphene or another study.

## Unchanged execution and display boundaries

No observation evaluation, applicability decision, plot, uncertainty-bar
comparison, material ranking or 2D-to-3D conversion is added. There is no
default thickness and no N/m-to-Pa/GPa output. The composite evaluator and its
comparison builders continue to use only the existing eight elastic rules.
The new observation source does not enter their selected evidence automatically.
Prediction and temperature content and behavior remain separate and unchanged.

Engine labels and result identifiers derived from the software version can
change even when numerical results do not. Regenerate exports when a current
engine label is needed; do not relabel historical artifacts as newly evaluated
or newly checked. No newly generated plot is required by this catalog update.

## Provenance and rights

[The observation guide](OBSERVATIONS.md) records precise property, equation,
uncertainty, count and preparation locators. [Source notes](SOURCES.md) preserve
bibliographic identity, proof-format/version limits, the printed-q discrepancy,
and the publisher/supplement access gaps. All seven artifact pages were
text-checked and pp. 3–6 visually checked; a second transcription check of the
same artifact does not amount to independent scientific review or replication.

Publisher metadata states ©2011 American Chemical Society; the proof has an
ACS notice with a placeholder year. No explicit open-reuse license is verified.
Only brief numerical facts, metadata, source locators and original curation
are included. No paper PDF, full text, figure, screenshot or raw measurement
collection enters the repository or release package. MIT covers original
project contributions only; neither public access nor curation relicenses the
paper or scientific facts. No legal clearance is claimed. Existing NIST
omissions and all other source-specific rights boundaries remain unchanged;
see [third-party notices](../THIRD_PARTY_NOTICES.md).

## Verification checklist

Run from the repository root with the complete `.[dev]` extra installed:

```sh
python -m unittest discover -s tests -p test_release_metadata.py -v
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
python -m materials_boundaries catalog observations --source-id bertolazzi_brivio_kis_2011 --json
python -m materials_boundaries catalog observations --query "MoS2 stiffness" --text --lang en
python -m materials_boundaries catalog observations --source-id bertolazzi_brivio_kis_2011 --text --lang zh
python -m materials_boundaries catalog observations --source-id bertolazzi_brivio_kis_2011 --text --lang ja
python -m materials_boundaries catalog observations --source-id bertolazzi_brivio_kis_2011 --text --lang de
```

Check strict-family mutations, source references, original-record preservation,
canonical JSON language independence, actual guard use in reading/rendering,
and installed-wheel behavior. These are acceptance checks to run, not a claim
that they have passed. Tests and transcription checks do not replace independent
scientific or native-language review.
