# Material coverage v0.35.0

The local v0.35.0 release candidate adds the exact independently accepted v2
CIRAD/GWDD batch: 1,000 distinct accepted historical WFO species identities,
1,000 selected accession states and 1,000 traceable conversion-derived
basic-density properties. This is not 1,000 species means, independent plant
replicates, commercial grades or engineering allowables.

## Actual catalog counts

- Material identities: 1,057
- Source-scoped states: 1,057
- Reference properties: 1,057
- Qualified grades: 20
- Source registry entries: 114
- Executable scientific rules: eight, unchanged
- Interface languages: English, Chinese, Japanese and German

Primary classes count each admitted identity once:

| Class | Admitted unique identities | Remaining to 1,000 |
|---|---:|---:|
| Metal | 14 | 986 |
| Inorganic | 16 | 984 |
| Polymer | 14 | 986 |
| Composite | 3 | 997 |
| Natural biological tissues/fibers | 1,010 | 0 |

Only the natural class reaches the requested target in this milestone. The other
four classes require further independently reviewed sources and admissions.
Aliases, states, multiple properties, source rows and benchmark fixtures do not
add identities. The 3,793 source-supported research pool is not silently
imported. No held v1, BY-SA/PROSEA rows, hierarchical `wsg_est`, aggregates or
unreviewed alloy/polymer/inorganic research is admitted.

The ten existing biological identities were migrated using an exact 34-field
category/classification-prose ledger. Existing numerical facts, conditions,
statistics, uncertainty and source records remain unchanged. Rocks/minerals
remain inorganic; processed biopolymers and extracted lignin remain polymer.

## Exact source and review identity

- Reviewed v2 candidate batch SHA-256:
  `5e059c0565f13610b307d9f71b1a29c65bec46aff127392d0b10eba469aef032`
- Independently recomputed approved stage review manifest:
  `277ddad3e67710b6ae15055dbbf9af1f8d57c3eb3be5673b6c4db41d96382b58`
- Accepted append-material table SHA-256:
  `831026a0bc234cf954c24bc18a3dca01ca70d4004127d8d8c51919d28dc49cd7`
- Accepted append-property table SHA-256:
  `168431492a9b1aeb5e21a2e93ad6d63184a14fa5cd99a25211ec06aabf7241fb`
- Accepted append-source table SHA-256:
  `bda893df4335e771bf724281458432ed3c1a93f1147f0331962963218d935ef8`

The source-fidelity review checked all 1,000 identities/values/provenance chains
and all source-complete inspection views. The scientific gate is source-specific
and historical; it does not assert experimental replication or broad material
suitability. Full regression, broad mixed-catalog rehearsal, installed offline
wheel verification and exact final-source manifests are separate release gates.

## Scientific meaning

The authoritative result is the deposited, rounded GWDD basic-density value in
g/cm³. Its mass/volume basis is oven-dry mass over fresh or water-saturated
volume. Input is measured dimensionless air-dry specific gravity. The source
applies coefficient 0.8281316 with nominal 12% conversion moisture and water-density
convention 1 g/cm³. Actual specimen moisture, exact test temperature, tissue
subtype, anatomical location and record uncertainty remain unknown.

A Decimal audit checks source rounding without inventing an upstream tie rule;
SI is exactly the already-rounded g/cm³ value multiplied by 1,000, with 10 kg/m³
resolution. The long intermediate audit product is not presented as measured
precision. The 2018 calibration cohort is distinct from the 2019 collection.

Cocos nucifera is retained without a false secondary-growth timber claim.
Source-reported plants=1 and inherited v1 mechanically eligible source-record
counts are not verified independent n. Original/accepted names and authorities,
actual WFO IDs/chains, source file names/DOIs/versions/hashes, locators/accessions,
original and corrected citations, rights and missingness survive inspection.

## Inspect and reproduce

```sh
python -m materials_boundaries coverage --text --lang zh
python -m materials_boundaries coverage --json
python -m materials_boundaries catalog materials --category natural --query "Cocos nucifera" --text --lang en
python -m materials_boundaries catalog reference-properties --quantity basic_wood_density --text --lang de
```

For source-complete programmatic export use `resolve_material` or
`resolve_materials` and retain the pinned source/admission manifests. A canonical
catalog subset is a dependency-bearing record, not a standalone audit archive.
See [bulk workflow](BULK_INGESTION.md) and [source notices](../THIRD_PARTY_NOTICES.md).

## Scale limits

Performance evidence distinguishes factual preview inputs from fictional scale
fixtures. The corrected 1,000-record preview plus 57 baseline records validates
in about one second in the recorded Linux/Python environment; full text rendering
is several seconds and roughly a quarter GiB peak RSS. Rich synthetic 10,000-row
full text output is memory-heavy (hundreds of MB of text and over one GiB peak
RSS). These are observed measurements, not a throughput guarantee. Filtered
inspection or compact quota output is preferable to printing an enormous catalog.
Benchmark-generated identities never become real material coverage.
