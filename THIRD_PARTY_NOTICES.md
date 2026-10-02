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
