# Bounded source-family ingestion experiment, 2026-10-19

This experiment starts at `12cb89ca82b48ba444bdb921674c3d232d448720`.
It adds a checkout-only [source-family packet compiler](FORMULATION_PACKET_PREPARATION.md)
and a compatible version-2 handoff to the existing experimental integrator.
Shared context and explicit formulation rows produce one immutable packet.
The integrator reconstructs every field from the embedded input and the pinned
baseline before merging. A ready flag or a rehashed, edited report is insufficient.

The first packet contains one source-qualified PA12 identity, one source-designated
EOS PA2200 grade, one dyed SLS unaged reference state, one tensile-strength property
and one article source. Its frozen candidate commit is
`f2969c10f365c099d54f7cfe6c78c8ef54592237`.
The exact 1084-identity data image is committed separately as
`e2a8bc7f7297c95b9ddd883275a1c807ff4b038d`.
The [packet and review](../experimental/material-batches/20261019-pa12-source-family/README.md),
[integration manifest](../experimental/material-batches/20261019-pa12-source-family/integration.json)
and [incremental report](../experimental/material-batches/20261019-pa12-source-family/integration-report.json)
retain the input pins, additions, identity decision, unknowns and pending gates.

## Source and limits

Zakręcki and Cieślik, *Materials* 18(19), 4478 (2025),
[DOI 10.3390/ma18194478](https://doi.org/10.3390/ma18194478), Table 7, reports
43.72 MPa mean tensile strength, 1.03 MPa standard deviation and 2.36% CV
for the selected SLS reference group; the study describes six specimens per
technology/treatment/age group. The retained Europe PMC XML was rechecked with
SHA-256 `4d930d221c67d38199460f1f80b86a2a724a0b2986a77e09081172d5a83c42d7`.
No fresh network retrieval was used for this batch.

The selected result is article-original factual data under the article's stated
CC BY 4.0 terms. Manufacturer-derived comparison tables, full XML, figures, PDFs
and raw measurements are not included. These checks do not replace independent
scientific or source-specific licensing review. The conflicting modulus
statistics are recorded and excluded. Tensile-test temperature, humidity, full
additive package and precise strength-extraction rule remain unknown.
The source-described 115 mm test-section length is not relabeled as an
extensometer gauge length. No medical suitability claim is made.

HP PA12 is not counted as a second material. Trade names, printing methods,
ageing groups, repeated properties and alternate states do not establish
distinct chemical identities. The compiler checks source-scoped textual
collisions; chemical equivalence still requires curation.

## Experimental counts

The core catalog changes from 1083 to 1084 identities, with 21 grades,
1084 states, 1084 reference properties and 116 sources. The complete experimental
project is **1108 = 1084 source-qualified identities + 24 reviewed computed
composition buckets**. The 62 unadmitted computed examples remain excluded.
The packet and integration commands themselves admit zero formal materials;
main remains at its separately approved count of 1081.

| Primary class | Core | Experimental project | Remaining to 1000 |
| --- | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 0 |
| Metal | 22 | 34 | 966 |
| Inorganic | 26 | 38 | 962 |
| Polymer | 16 | 16 | 984 |
| Composite | 10 | 10 | 990 |

Relationship-supported memberships may overlap: supported polymer membership is
17 and the total membership assertion count is 1089. These are not extra unique
materials. Only natural materials meet the category target.

## Validation boundary

The bounded checks cover compiler expansion, missing properties, incompatible
units, source and baseline changes, duplicate/reidentified labels, pending
reviews, forged packet fields, immutable repeat writes and partial failure.
The actual PA12 packet is replayed into the exact predecessor and compared with
all three runtime catalog byte images. Exact predecessor recovery checks reject
partial additions, altered retained rows, extra rows and changed ordering.
Historical pins and dated count assertions remain unchanged behind finite
recovery bridges.

The exact-branch CI job exercises the selected affected contracts on Linux
Python 3.11 and Windows Python 3.12, validates catalog schemas, and builds and
installs six local wheels. Its build command explicitly names local directories
and disables index access and build isolation. The original jobs and previous
experiment job are retained; they are not reported as executed by this batch.
Actual local and CI results belong in the accompanying validation report.

Main integration, DOI registration, public deployment and further source batches
remain separate. This change does not add credentials, change permissions or
turn automated collection into scientific approval.
