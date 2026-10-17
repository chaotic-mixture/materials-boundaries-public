# NC2 concrete experimental increment, 2026-10-17

This increment adds one source-qualified composite formulation, one state and
one property to experimental baseline
`eaf16e1eb1edad17fbf78ac7385566f6a4e86a94`. It reuses the existing offline
integration command, catalog schema, source registry and admission boundaries.
No new ingestion platform or automatic scientific approval is introduced.

## Selected fact and identity

The identity is `mat_domagala2024_nc2_concrete`, the study-defined NC2 recipe in
Domagala, Marganska and Miazgowicz (2024), *Moisture Impact on Static and Dynamic
Modulus of Elasticity in Structural Normal-Weight Concretes*, Materials 17(15),
3722, [DOI 10.3390/ma17153722](https://doi.org/10.3390/ma17153722).

| Scope | Selected value |
| --- | --- |
| Property | Water-saturated mass density, source label `D_w` |
| Reported mean | 2340 kg/m3 |
| State | Nominal 28-day water-saturated concrete |
| Specimens | Three cylinders per concrete series, 150 mm diameter and 300 mm length |
| Method | EN 12390-7:2019; exact subprocedure and instrument unreported |
| Locator | Table 3, NC2 row, `D_w` column; preparation and count in section 2 and Table 2 |

NC2 is compositionally distinct from the existing NC1 entry. Table 1 reports
cement, water and superplasticizer inputs of 470, 174 and 1.9 kg/m3 for NC2,
compared with 377, 208 and 0 kg/m3 for NC1. Their reported water/cement ratios
are 0.37 and 0.55. Both use coarse aggregate 1140 and fine aggregate 570 kg/m3.
The material identity follows the recipe difference. Curing ages, moisture
states, additional properties, source aliases and strength classes are not
additional identities. CEM I 42.5 R identifies the cement constituent.

The selected property retains unknown density-test temperature, density basis
terminology, exact volume/mass subprocedure, instrument and statistical
uncertainty. The source's 20 C concerns curing/storage. Its maximum individual
density deviation of 20 kg/m3 is not an SD, confidence interval or measurement
uncertainty. The nominal 28-day label is preserved despite the source's wording
about demolding after 24 hours followed by 28 days of water storage. The shared
Table 2 count covers sequential wet and dry measurements on three cylinders,
not two separate groups of three.

## Source scope and review

The [primary Europe PMC XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11313055/fullTextXML)
was read again on 2026-10-17. SHA-256
`8eee9708ea9e257dc060117f6b7c20a031443c982ecb98aa92cf5227e7479ec5`
matches the already registered source. Its permissions explicitly identify
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), and the selected
original-study tables have no separate third-party credit. Attribution and the
license link are retained. Structured metadata, English fallback names and
source limitations are catalog curation; the selected numerical value and
precision are unchanged. The complete source registry remains byte-identical.
No article XML, PDF, figure, screenshot, structure or raw asset is bundled.

Selected-content transcription was cross-checked. Independent scientific review,
raw-data reanalysis, universal-bound and engineering-allowable flags remain
false. The property is catalog-only and is not a design value for concrete.
Existing NC1 records remain unchanged. Four required locale slots use English
fallback names without claiming native-language review.

A separate PA2200 lead from DOI `10.3390/ma18194478` was held. Its Table 7
reference row reports modulus mean 1.41 GPa, SD 0.04 GPa and CV 3.48 percent;
the CV does not agree with the mean and SD even allowing their displayed
rounding. This increment neither repairs those numbers nor admits that polymer.
Other inspected but unselected leads also contribute zero identities.

## Reproduction and recovery

The frozen candidate packet is commit
`e7a1f14af3ad0b290049319c16387589f831fa0b` under
`experimental/material-batches/20261017-nc2-concrete`. The integration manifest
binds its four JSON inputs and the three eaf baseline files by SHA-256.
Copy the exact baseline resources to a separate directory without text-mode
shell redirection, for example from a checkout of the named baseline:

```sh
python scripts/integrate_material_candidates.py \
  --baseline-dir /path/to/eaf-checkout/materials_boundaries/data \
  --manifest experimental/material-batches/20261017-nc2-incremental/integration.json \
  --output /path/to/new-output/nc2-integration.json
```

Run the same command again against the same output. The first run creates an
immutable combined catalog/report; the second verifies identical content and
returns unchanged without rewriting it. A baseline hash mismatch, changed
packet, missing property, incompatible unit or conflicting source/record is
rejected. The command does not write runtime data or grant formal admission.
Runtime materialization in this experimental branch is a separate explicit
selection of the validated package catalogs. No source discovery or network
request occurs during replay.

Removing exactly the NC2 identity, state and property recovers the three eaf
baseline resource bytes. Historical NBS tests use this recovered graph and
retain their earlier exact baselines. All previous identities, source records,
grades, properties, computed reviews and excluded examples are preserved.

Focused verification exercises source transcription and qualifications, distinct
recipe identity, validated coverage, predecessor-byte recovery, repeated merge,
actual CLI replay and failure without output. Catalog component tests check the
new resource pins and refusal of old SQLite baseline anchors. An old registry
must stay with its original installation; this increment adds no migration or
fallback. Actual commands and results are recorded in the delivery evidence,
and are not a claim of an additional full-suite run.

## Counts and release boundary

| Category | Experimental core | Experimental project | Remaining to project target 1000 |
| --- | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 0 |
| Metal | 22 | 34 | 966 |
| Inorganic | 26 | 38 | 962 |
| Polymer | 14 | 14 | 986 |
| Composite | 4 | 4 | 996 |
| Total | 1076 | 1100 | Four categories remain below target |

The experimental project total is 1076 source-qualified identities plus the same
24 reviewed computed composition buckets. Only one composite identity is new
relative to eaf; the earlier eighteen source-qualified additions are retained.
The 62 unadmitted computed examples remain excluded. Candidate counts, source
reads, test executions and multiple properties never add to material counts.

Released main remains **1081 = 1057 + 24**, with zero main increment from this
branch. Experimental publication, matching resource pins and an API field named
`formal_project_admission_count` do not approve a main release. DOI registration
and public deployment remain deferred. Standard interoperability, further
computation/interface work and the five-category target are not completed here.
