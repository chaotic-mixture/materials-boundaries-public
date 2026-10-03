# Two-study temperature summaries

Software v0.25.0 adds one explicitly selected, descriptive two-study presentation:
`ciganas-zach-uts-temperature-v1` (profile 1.0.0). It answers what each study
reported and under which protocol. It does not establish matched experiments,
statistical independence, equivalent materials or a ranking.

```sh
python -m materials_boundaries observation compare-temperature-studies \
  --profile-id ciganas-zach-uts-temperature-v1 --output /tmp/study-comparison --lang en
python scripts/generate_observation_study_comparison_demo.py --lang all
```

Both profile and output are required. The final `--lang` wins, including for
localized help. Authored labels are available in `en`, `zh`, `ja` and `de` with
no English fallback. Source strings, canonical identifiers, bibliography and
machine exports do not translate. Scientific wording and translations remain
machine-assisted, without external scientific or native-language review.

## Read protocols before values

Every standalone SVG and HTML page places essential warnings and both full
protocol summaries before any UTS value. The two source groups remain separate:

- Ciganas, Kalinauskis and Cigane (2026): Fiberlogy PA12 CF15, horizontal FFF,
  alternating +45°/−45° raster; drying 80 °C for 12 h; postprint annealing unknown.
  Creality K1 MAX, 0.6 mm nozzle and 265 °C extrusion. Step-Lab UD08; source-reported
  nominal geometry distinguishes 80 mm gauge from 110 mm grip/strain reference.
  Reported 1 mm/min displacement/crosshead rate. Three tests per temperature;
  central statistic and aggregation unnamed. Table 3 identifies UTS MPa ± SD
- Zach and Dudescu (2025): Bambu Lab PAHT-CF, flat FFF, ±45°, explicitly annealed
  rows. Predrying and annealing each 80 °C for 12 h. Natural-convection cooling to
  room temperature in a vacuum-sealed dehumidified container; no controlled
  cooling rate inferred. Section 2.2 preparation wording differs from the group
  distinctions in Table A1/Section 2.3; untreated history is not inferred.
  Bambu Lab X1 Carbon, 0.4 mm nozzle and 290 °C extrusion. Instron 5967; drawing
  labels are nominal annotations whose caption unit is not established, with
  narrow width, stress area, gauge and grip separation unknown. As-printed
  displacement rate 10 mm/s, control channel unknown. Five specimens per
  orientation × temperature × annealing group. Reported median, separate SD
  column with MPa contextually inferred from UTS, not printed in the SD header

Both use reported chamber conditions after 30 minutes, not directly verified
specimen-temperature readings. Temperature uncertainty is unknown. 23 °C is
not 25 °C; a shared 100 °C label does not prove matched conditioning. Actual
moisture/RH, stress convention/area and local strain rate remain unestablished.
Different commercial formulations remain distinct: declared PA12/15 wt.% is not
an assay, 100% infill is not measured zero porosity, and source-cited standards
are not verified compliance. No rate ratio or merged condition row is computed.

## Two panels, central summaries only

Fixed source order is Ciganas then Zach, unrelated to magnitudes or study quality.
There are six and four equally styled, unconnected dots in separate plot areas.
Each repeats its own source, preparation, statistic, units and SD notice.
Both use the reviewed display coordinates 15–155 °C and 0–65 MPa. These domains
are padding, not validated ranges or material limits. Numeric reference ticks
are 20/40/60/80/100/120/140 °C and 0/10/20/30/40/50/60 MPa, not observations.
Exact tested temperatures and source precision remain in separate visible tables:

| Ciganas chamber °C | Unspecified central UTS MPa | Reported SD MPa |
| --- | --- | --- |
| 23 | 49.07 | 0.88 |
| 40 | 40.31 | 0.72 |
| 60 | 32.70 | 1.18 |
| 80 | 26.60 | 1.15 |
| 100 | 22.78 | 0.97 |
| 120 | 18.68 | 0.91 |

| Zach chamber °C | Reported median UTS MPa | SD, MPa contextually inferred |
| --- | --- | --- |
| 25 | 58.91 | 3.44 |
| 50 | 40.87 | 4.59 |
| 100 | 29.64 | 0.72 |
| 150 | 19.03 | 0.67 |

SD is always visible as separate text. No uncertainty endpoints, whiskers or
median ± SD interval are calculated. SD is reported dispersion, not SEM, CI,
uncertainty of the median, observed min–max, coverage, hard bounds or a complete
uncertainty budget. Raw replicates, independence and SD formula are unverified;
counts do not justify computing a CI. No fit, interpolation, extrapolation,
pooling, retention ratio, difference, ranking, significance test, prediction,
allowable or geometry conversion is admitted. SI values are metadata only:
Zach SD scaling remains conditional on contextual MPa inference.

## Closed data and output contract

Schema `observation-study-comparison.schema.json` is 1.0.0. The public module is
`materials_boundaries.observation_study_comparison`:

- `build_observation_study_comparison(profile_id=...)`
- `validate_observation_study_comparison(bundle)`
- `observation_study_comparison_json(bundle)` and `observation_study_comparison_csv(bundle)`
- `render_observation_study_comparison_svg(bundle, lang='en', width=1100)`
- `render_observation_study_comparison_html(bundle, lang='en')`
- `export_observation_study_comparison(directory, profile_id=..., lang='en')`

Admission requires both existing independent source-family guards, exactly ten
unique source cells, both actual source objects, complete datasets, exact
protocol/source identities and no aliases. Catalog order and harmless display
ID/name changes do not reorder source cells. Unrelated supported catalog
additions neither enter this profile nor change its membership. There is no
free-form record input, subset mode, automatic all-studies mode or unit-based
admission. Future pairs require separate review and implementation.

All serializers, renderers and exporters rebuild against current packaged
catalogs and compare complete canonical JSON. Recomputed snapshot hashes cannot
authorize altered data. Unknown, stale, extra, nonfinite, Boolean-as-numeric,
non-JSON, XML-illegal and unsafe URL content fail closed. Caller data is not
mutated. JSON Schema complements runtime provenance checks; it cannot replace
canonical rebuilds. Digests identify curated metadata, never publisher bytes.

The prefix `observation-study-comparison` yields JSON, CSV, locale HTML and
1100/380 px SVG files. The demo emits exactly 14 files for four languages.
Strict integer SVG widths are 320–1600; panels stack below 900 px. HTML has
responsive grids, semantic always-visible tables and inert metadata details.
Standalone SVG is an atomic image with a complete ordered text alternative;
it does not promise navigable table cells. Use HTML for semantic table structure.
There are no scripts, external fonts, images or automatic requests. Safe
HTTP(S) evidence links are ordinary user-activated links. Full snapshots and
metadata digests stay in JSON/CSV and inert HTML details rather than flooding
static figures.

CSV has ten fixed long-form rows with source identity, protocol and caveats
before numeric columns. It has no temperature pivot, join, pooled row or delta.
Null scalar values spell `null`. Source strings and full snapshots are retained
losslessly, including original Ciganas plus-minus notation and Zach's separate
median/SD columns. Import identity, source and JSON columns as text in spreadsheet
software: formula-like strings are preserved for scientific interchange.

All artifact content is preflighted before writing output targets. Invalid
profile, language or catalog leaves absent/existing targets untouched. Later
filesystem failures can leave partial output; there is no multi-file rollback
guarantee. Exports are deterministic; JSON/CSV are locale-independent.

## Source, review and rights

- Ciganas et al., *Thermo-Mechanical and Fatigue Behavior of 3D-Printed PA12 CF15
  for Engineering Application*, Polymers 18(5), 563 (2026),
  [DOI 10.3390/polym18050563](https://doi.org/10.3390/polym18050563), Table 3 UTS
  MPa ± SD row, six temperature columns. HTML update reported 3 September 2026
  02:53 CEST, inspected 3 October 2026. Search-rendered/current HTML discrepancy concerns an
  unselected Table 4, not the selected Table 3 cells
- Zach and Dudescu, *Effect of Annealing on High Temperature Tensile Performance
  of 3D Printed Polyamide Carbon Fiber: A Comparative Study*, Journal of
  Composites Science 9(11), 624 (2025),
  [DOI 10.3390/jcs9110624](https://doi.org/10.3390/jcs9110624), Appendix A Table A1,
  explicitly annealed ±45° rows, four temperature blocks, UTS and separate SD
  columns. HTML update reported 2 September 2026 03:21 CEST, inspected 3 October
  2026. Search-rendered prose arrangement differed; no selected-cell discrepancy
  was found. Prior-study raw-data overlap was not audited

Neither PDF was inspected; no HTML/PDF equivalence is claimed. Reader agreement
checks transcription, not independent experiment, replication or scientific
validation. Source exact strings/locators, revision notes, evidence, rights and
unknowns remain in full immutable source snapshots.

Both selected tables are attributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
This adaptation reorganizes their selected central/SD summaries into separate
panels and preserves numbers, notation and source-specific qualifications.
No publisher endorsement is implied. MIT covers original project contributions,
not source rights. Supplier tables, figures, PDFs, screenshots, HTML dumps and
raw measurements are not redistributed. No source-media or new observation is
added, and no excluded dataset or denied mirror is used.

## Preservation and validation limits

The frozen Zach catalog limits include the v0.24 admission statement “No new
plot”. That historical source payload is unchanged. This separately curated
v0.25 named descriptive presentation supplies the new plotting permission;
it does not revise experimental evidence or elevate source scientific status.
The old generic inspection stays text-only, and the old six-cell Ciganas
±SD plot keeps its own unchanged policy and rejects Zach.

All prior scientific catalogs, old fixtures and checked-in examples remain
byte-identical. No evaluator or material-calculation rule is added. Release
checks cover catalog/schema integrity, focused/adversarial and full suites,
mixed supported-family appendability, dependency-free installed wheel,
historical output parity (software-version alignment only), public exclusions
and static SVG raster inspection. Browser/keyboard/zoom/print behavior requires
actual permitted browser QA; static images or DOM assertions do not certify it.
See [migration](MIGRATION_v0.25.0.md) for the current verification limits.
