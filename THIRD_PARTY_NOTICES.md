# Third-party notices and license scope

## Original project work

Copyright (c) 2026 chaotic-mixture. The [MIT License](LICENSE) covers original
project code, documentation, translations, synthetic examples and original
curation/derivation text to the extent those contributions are copyrightable.
It does not purport to license scientific facts or relicense third-party
publications, datasets, figures, software or other source works. Each source
retains its own rights and attribution. No author, publisher, NIST or other
institution is represented as endorsing this project.

The public repository contains brief attributed numerical facts, bibliographic
metadata, mathematical relations and original explanatory notes. It does not
bundle source PDFs, article full text, source page images, publisher figures,
scraped source compilations or raw experimental collections. A source being
publicly readable is not a blanket redistribution license. The source catalog's
license fields describe recorded evidence, not an independent permission grant.

## NIST cryogenic material properties

The five NIST cryogenic coefficient datasets used during development and all
their derived sample outputs are **omitted from the first public release**.
The packaged temperature examples instead use five original synthetic models
(seven branches), visibly labeled as invented demonstrations of software
behavior. NIST bibliographic records and links remain for provenance.

This is a conservative release choice pending clarification, **not a finding
that redistribution is prohibited**. Official evidence, checked 2026-10-02:

- [NIST's curated data collections](https://www.nist.gov/srd/related-data-products-and-links/curated-data-collections)
  lists the Cryogenic Material Properties Database as formerly SRD 152
- [NIST's related-data-products explanation](https://www.nist.gov/srd/related-data-products-and-links)
  distinguishes curated collections from products meeting current SRD
  critical-evaluation criteria
- The [Cryogenic Technology Resources homepage](https://trc.nist.gov/cryogenics/)
  records the correlations' origin in a past SRD project
- [General NIST copyright guidance](https://www.nist.gov/copyrights-disclaimers)
  and [SRD/data/software policy](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications)
  provide policy context and distinguish different classes of NIST works

Former SRD status and current reclassification are both recorded. Neither the
reclassification, public access nor attribution establishes a verified express
grant to redistribute or relicense these particular correlations. No CC0,
public-domain, NIST certification or database-wide rights claim is made.

## Literature facts and source-specific qualifications

The omission above is limited to the NIST cryogenic coefficient datasets and
their derived outputs. It is not a general exclusion of attributed numerical
facts from literature. The following remain, with their exact scientific scope
and source-specific caveats:

- Graphene observation summaries from [Lee et al. (2008)](https://doi.org/10.1126/science.1157996):
  ©2008 AAAS; model-dependent two-dimensional results, not raw experimental data
  or third-party figures. See [observation provenance](docs/OBSERVATIONS.md)
- Monolayer MoS2 observation summaries from [Bertolazzi, Brivio and Kis (2011)](https://doi.org/10.1021/nn203879f):
  publisher metadata states ©2011 American Chemical Society; the inspected
  [EPFL proof-formatted PDF](https://infoscience.epfl.ch/server/api/core/bitstreams/5af84a4c-55a4-4151-9d85-d5c215d848a4/content)
  has lettered pages A–G and an ACS notice with a placeholder year. Repository
  “openaccess” / “Published version” labels establish neither verified final-text
  identity nor an open-reuse license. The final publisher text and supplement
  remain unverified; no general reuse permission is inferred. Only two brief
  factual monolayer numerical summaries, metadata, locators and original
  curation are included. The printed-q discrepancy, unresolved actual fit
  constant, source-reported SD semantics and unknown conditions are preserved;
  no correction, refit, plot or conversion is claimed. No PDF, full text, figure,
  screenshot or raw measurement collection is redistributed. MIT does not
  relicense this paper or its factual material. See [observation provenance](docs/OBSERVATIONS.md)
- Ni-family ideal-shear and silicon first-instability computational predictions:
  brief published values with methods and unknown conditions preserved; no
  article redistribution or universal-bound claim. See [prediction provenance](docs/COMPUTATIONAL_PREDICTIONS.md)
- The [Genin–Birman literature-model example](docs/LITERATURE_EXAMPLE.md):
  source model parameters and original conversions, not a measured specimen
- Mechanics source metadata and original paraphrases: APS, ASME, AAAS, IOP,
  Royal Society, Oxford University Press and other notices remain source-specific.
  Public author copies and the arXiv nonexclusive distribution license do not
  become a general reuse license
- Sources with recorded Creative Commons or government-public-use notices keep
  those specific notices; no blanket license or unsupported license identifier
  is inferred for other works

Consult [SOURCES.md](docs/SOURCES.md), the scientific guides and the packaged
`materials_boundaries/data/sources.json` records for precise locators, inspected
scope, rights evidence and unresolved gaps. Software/schema checks and formula
cross-checks are not independent scientific peer review or legal clearance.

## Bulk elastic-wave relations (v0.18.0)

Exactly two new bibliographic sources support the catalog-only wave records:

- [Chevrot and van der Hilst (2003)](https://doi.org/10.1046/j.1365-246X.2003.01865.x),
  *Geophysical Journal International* 152(2), 497–505: ©2003 RAS. The inspected
  university-hosted journal-layout PDF was visually checked at printed p. 498,
  Eqs. (1)–(4). Public author/university access does not establish a general
  reuse license; none was verified
- [Xiang, Qi and Wei, arXiv:1708.04876v2](https://arxiv.org/abs/1708.04876v2):
  specifically the January 2018 v2 preprint, with pp. 2, 4–5 visually checked;
  no verified journal-version claim. Its arXiv nonexclusive distribution
  permission does not grant general republication or relicensing permission

The repository includes bibliographic metadata, mathematical relations and
original explanatory proofs, including the speed-ratio interval and the
strong-ellipticity/strain-energy counterexample. It does not redistribute the
papers, full text, PDF pages, screenshots or figures. No source author or
publisher is credited with the project's original interval or counterexample
proof, nor represented as endorsing it. MIT covers original project work only.
Source inspection, formula checks and tests are not independent scientific
review or legal clearance. Existing source-specific notices and the conservative
NIST omissions remain unchanged. See [wave provenance and proofs](docs/BULK_ELASTIC_WAVES.md)
and [source ledger](docs/SOURCES.md).

## Monolayer hBN observations (v0.19.0)

The added source is Aleksey Falin, Qiran Cai, Elton J. G. Santos, Declan Scullion,
Dong Qian, Rui Zhang, Zhi Yang, Shaoming Huang, Kenji Watanabe, Takashi Taniguchi,
Matthew R. Barnett, Ying Chen, Rodney S. Ruoff and Lu Hua Li,
[“Mechanical properties of atomically thin boron nitride and the role of interlayer interactions”](https://doi.org/10.1038/ncomms15815),
*Nature Communications* 8, 15815 (2017). The publisher article is ©2017 The
Author(s) under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/),
subject to contrary third-party credit lines. The license is linked in the
publisher's [Rights and permissions](https://www.nature.com/articles/ncomms15815#rightslink).

Exactly two selected monolayer summaries are curated: stiffness 289 ± 24 N/m
and breaking strength 23.6 ± 1.8 N/m. These are source-printed numerical facts,
with original notes and precise source locators, not refits or a redistributed
experimental dataset. The SD and tested-sheet definitions are specifically
attributed to the publisher-linked peer-review author response, PDF p. 8,
Reviewer #1 question 3; they are not represented as definitions printed in the
main article. Nonlinear FEM volume-averaged under-indenter strength is kept
distinct from the supplement's diagnostic maximum Von Mises stress.

**Separate license scope for the supplementary information and public peer-review
file is unverified.** The article's CC BY 4.0 status is not automatically applied
to either artifact. No source PDF, full text, figure, screenshot, peer-review
report or raw-data collection is redistributed. The MIT license covers original
project work only and does not replace source licensing or imply author/publisher
endorsement. Source inspection and software tests do not establish scientific
peer review or legal clearance. See [observation provenance](docs/OBSERVATIONS.md#monolayer-hbn-falin-et-al-2017-new-records)
and [source ledger](docs/SOURCES.md).

## Six additional Ni11X predictions (v0.21.0)

The additional Ni11Cr 4.90, Ni11Mn 5.12, Ni11Fe 5.20, Ni11Cu 4.51,
Ni11Si 4.17 and Ni11Ti 4.24 GPa entries are brief factual results attributed to
Shimanek, Shang, Beese and Liu, [arXiv:2108.06412v2, Table 2, p. 27](https://arxiv.org/pdf/2108.06412v2#page=27).
They reuse the existing source record; no new license or republication permission
is asserted. The earlier arXiv non-exclusive distribution-license evidence is
inherited, and its licensing page was not newly inspected for this batch. That
license does not establish a general third-party right to redistribute the paper.

Only these selected numbers, exact locators, bibliographic attribution and
original method/limitation paraphrases are included. No cached PDF, full extracted
text, rendered source page, table artwork, screenshot or source figure is
redistributed. Project MIT licensing does not relicense the publication or
scientific facts and does not imply endorsement. Source/transcription checks are
not scientific peer review or legal clearance.

All six are periodic Ni11X model predictions, not pure-solute measurements,
commercial grades or universal bounds. A bare table label does not establish a
PAW dataset, a valence configuration or absence of semicore states. Unknown
conditions and uncertainty remain explicit; published-method-only comparison is
not an input audit. [Source scope](docs/SOURCES.md#v0210-ni11x-six-record-addition-existing-source-new-inspected-cells)
· [Scientific qualifications](docs/COMPUTATIONAL_PREDICTIONS.md).


## PA12 CF15 tensile-test summaries (v0.22.0)

Justas Ciganas, Tomas Kalinauskis and Urte Cigane (2026),
[“Thermo-Mechanical and Fatigue Behavior of 3D-Printed PA12 CF15 for Engineering Application”](https://doi.org/10.3390/polym18050563),
*Polymers* 18(5), 563. The [article copyright block](https://www.mdpi.com/2073-4360/18/5/563#html-copyright)
was inspected on 3 October 2026 and identifies ©2026 by the authors, MDPI as
licensee, under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
No third-party credit line was shown for selected Table 3.

The six selected UTS/SD cells at reported chamber conditions 23, 40, 60, 80,
100 and 120 °C are attributed to Table 3 of this article. They were reorganized
into discrete observations: source numbers and SD strings are preserved, exact
MPa-to-Pa unit re-expression is added, and curator notes are original summaries.
This is not raw-data reanalysis, independent replication or a universal allowable.
The article's Table 1 is manufacturer-provided and excluded; article licensing
is not assumed to relicense that third-party content.

Inspected HTML revision metadata and the cached/live discrepancy in unselected
Table 4 are retained. The PDF was not inspected and no PDF equivalence is claimed.
No publisher PDF, screenshot, figure, HTML dump, long passage or raw measurement
collection is redistributed. The MIT license covers original project
contributions only and does not replace source rights or imply author/publisher
endorsement. See [source and scientific limits](docs/PA12_CF15_TEMPERATURE_OBSERVATIONS.md)
and [source ledger](docs/SOURCES.md).


### v0.23.0 descriptive PA12 CF15 plotting adaptation

The separate [temperature-observation plot](docs/OBSERVATION_TEMPERATURE_PLOT.md)
uses the same six attributed Table 3 UTS/SD cells and unchanged source rights.
It preserves the source numbers and SD strings while reorganizing and plotting
them as discrete source summaries. Vertical glyph endpoints are explicit
central-value ±reported-SD arithmetic; exact SI unit re-expression and original
curator notes remain separate. The adaptation is not raw-data reanalysis,
statistical validation, independent replication or a material-model claim.

Retain Ciganas, Kalinauskis and Cigane (2026), the article title and DOI above,
Table 3 locators, inspected HTML revision, PDF noninspection, unselected Table 4
revision caveat and article-specific CC BY 4.0 notice. No new rights are asserted
for excluded manufacturer Table 1 or any other unselected content. No source
assets or raw measurements are redistributed; the MIT license applies to
original project contributions and no author/publisher endorsement is implied.
