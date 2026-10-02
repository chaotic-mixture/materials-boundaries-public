# Source curation, verification and rights

Reusable claims, observation summaries and the source manifest are separate records. Current v0.18.0 has 36 mechanics claims, 50 sources and four observations from two studies, alongside five synthetic temperature demos (seven branches) and six computational predictions. The v0.8.0 historical batch had 26 claims and 20 sources; its four new stability claims reused an existing source and preserved those 20 source records. Some claims are executable elastic bounds/envelopes; the strength/fracture models, stability criteria and porous solid/void intervals are catalog-only. A source being available or read does not establish every claim attributed to it. Each claim or observation retains its own locator, verification status and gaps. The repository includes brief numerical facts, bibliographic metadata and original curation notes; no publisher PDF, article full text, scraped body or unlicensed figure is bundled.

## Historical evidence ledger and later release additions

1. [Hashin–Shtrikman (1963)](https://doi.org/10.1016/0022-5096(63)90060-7): publisher abstract only. Historical attribution is recorded; original equation locations and proof remain uninspected.
2. [Kochmann–Milton (2014), arXiv:1401.4142v1](https://arxiv.org/abs/1401.4142v1), [journal DOI](https://doi.org/10.1016/j.jmps.2014.06.010): prior research inspected the 24-page version; the relevant HTML equations were rechecked for implementation. Upper bulk (117), PDF p. 18; lower bulk (134), PDF p. 20. Upper shear (118), PDF p. 19, and lower shear (135), PDF p. 20 support the v0.2.0 shear extension; these were only contextual records in the bulk-only v0.1.2 implementation. The implementation uses the well-ordered positive-phase specialization and an algebraically equivalent positive rational form. The arXiv nonexclusive distribution license is not treated as a general reuse license. The article's broader negative-stiffness results are outside this MVP.
3. [Berger, Wadley & McMeeking (2017)](https://doi.org/10.1038/nature21075): subscription preview and public seven-page supplement were available in prior research. No explicit reuse license was verified. The construction/attainability discussion is context, not numerical input data.
4. [Milton, “Stiff competition” (2018)](https://doi.org/10.1038/s41586-018-0724-8): publisher preview/context concerns historical novelty, not an invalidation of the HS theorem.
5. [“Berger et al. reply” (2018)](https://doi.org/10.1038/s41586-018-0725-7): publisher preview/context concerns historical novelty. The reply acknowledges prior constructions; it is not labeled an invalidation of the HS theorem.
6. [Singh & Lai, arXiv:2411.11332v1 (2024)](https://arxiv.org/abs/2411.11332v1): preprint with a verified [CC BY 4.0 license link](https://creativecommons.org/licenses/by/4.0/). Its anisotropic constituents change a central assumption; a macroscopically isotropic response alone does not make it a same-assumption refutation. No claim of peer-review certification is made.
7. [Materials Project elasticity methodology](https://docs.materialsproject.org/methodology/materials-methodology/elasticity): possible future source of computed parameters. No specific material IDs, records, data license or import were selected. A computed tensor or reported aggregate modulus does not automatically establish isotropic constituents.
8. [Genin & Birman (2009)](https://doi.org/10.1016/j.ijsolstr.2008.08.010): one epoxy/glass literature-model parameter example, from the author proof dated 30 August 2008. Parameter and constituent-assumption passages were inspected; the numeric inputs are not labeled measurements. Calculator fractions/assumptions and unknown temperature/material context are preserved separately. Copyright Elsevier, all rights reserved; only citation, numeric facts and original calculations/notes are bundled. See [the example's evidence contract](LITERATURE_EXAMPLE.md).

9. [Meille & Garboczi (2001), “Linear elastic properties of 2D and 3D models of porous materials made from elongated objects”](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=860321), *Modelling and Simulation in Materials Science and Engineering* 9, 371–390, [DOI 10.1088/0965-0393/9/5/303](https://doi.org/10.1088/0965-0393/9/5/303): the NIST-hosted primary paper's extracted text was checked at Section 2.2, equation (3), printed p. 374 / PDF page 4. It gives the 3D isotropic identities 9/E = 1/K + 3/G and ν = (3K−2G)/(2(3K+G)); the implemented E = 9KG/(3K+G) is an algebraic rearrangement. DOI metadata was corroborated against [the coauthor's institutional CV](https://cv.hal.science/sylvain-meille). Screenshot/render verification failed, so **visual equation verification is not claimed**. This source supports the isotropic identities only, not this project's interval-corner construction, HS applicability, or joint attainability. The PDF cover records copyright 2001 IOP Publishing Ltd; no open reuse license was verified. The ninth source record, `meille_garboczi_2001`, contains metadata and original notes only; no PDF or article content is bundled.

10. [Griffith (1921), “The Phenomena of Rupture and Flow in Solids”](https://doi.org/10.1098/rsta.1921.0006), *Philosophical Transactions A* 221, 163–198: historical attribution only. The primary scanned header and final-page correction Note (printed p. 198) were visually inspected. The Note corrects the earlier strain-energy calculation; the modern displayed coefficients and plane-strain factor are not claimed as a direct transcription of the original equations. The original derivation has not been independently checked. No explicit reuse license is recorded as verified.
11. [Christopher D. Wilson (1992), “Linear Elastic Fracture Mechanics Primer,” NASA-TM-103591](https://ntrs.nasa.gov/citations/19920021173): the modern Griffith/LEFM formula source. Printed pp. 2–4 / PDF pp. 10–12 were checked in extracted text and rendered images: Figure 1 gives central crack 2a, equation (3) gives critical plane-stress stress, equations (4)–(6) relate K_I and G_I, and printed p. 4 defines plane-state E_prime. The catalog's plane-strain critical stress is an algebraic specialization. The original report's equation (2) derivative notation is not reproduced because two-tip normalization needs care. Gc=2 gamma is confined to the ideal surface-creation-only specialization. NASA metadata states “Work of the US Gov. Public Use Permitted.” The identifier stays unknown rather than inventing a license; only metadata and original notes are bundled.

The v0.3.0 catalog had ten claims and eleven sources. Its two new records are explicitly `model_estimate` and `catalog_only`; they produce no fracture evaluation, applicability state, or numeric prediction. They do not assert a universal strength upper bound or an engineering allowable. See [fracture-model evidence and scope](FRACTURE_MODELS.md).

## v0.4.0 additions: six metadata-only sources

The v0.4.0 total was **15 claims and 17 sources**. All earlier source records remain unchanged. The five new claims cite these additions and the existing Wilson report; claim-level locators also document the newly inspected Wilson finite-width page.

12. [Frenkel (1926)](https://doi.org/10.1007/BF01397292), *Zur Theorie der Elastizitätsgrenze und der Festigkeit kristallinischer Körper*, Zeitschrift für Physik 37, 572–609: publisher metadata/abstract only; historical attribution, original equations uninspected. Subscription-preview access supplies no verified reuse right.
13. [Shimanek et al. (2022), arXiv:2108.06412v2](https://arxiv.org/pdf/2108.06412v2), [published DOI](https://doi.org/10.1016/j.commatsci.2022.111564): version dated 10 June 2022, manuscript p. 2 eq. (1) and §3.3 p. 11 inspected as text and rendered pages. Supports the slip-specific Frenkel estimate, including the cited study’s orientation-dependent stiffness convention. The arXiv nonexclusive license is not general third-party redistribution permission.
14. [Rose, Ferrante and Smith (1981)](https://doi.org/10.1103/PhysRevLett.47.675), *Universal Binding Energy Curves for Metals and Bimetallic Interfaces*: historical UBER origin, abstract/metadata only. Original full-text equations unverified. NASA public-distribution metadata says copyright Other and supplies no download; no redistribution right is inferred.
15. [Van der Ven and Ceder (2004)](https://doi.org/10.1016/j.actamat.2003.11.007), *The thermodynamics of decohesion*: author-hosted primary article §§2–3 inspected; eq. (14), p. 1228 / PDF p. 6, cross-checks the UBER energy form and energy-offset convention. Excess variables are specified in eq. (11), p. 1226, and eqs. (12)–(13), p. 1227. Copyright 2003 Acta Materialia Inc./Elsevier, all rights reserved.
16. [Azócar Guzmán et al. (2020)](https://doi.org/10.3390/ma13245785), *Hydrogen Embrittlement at Cleavage Planes and Grain Boundaries in Bcc Iron—Revisiting the First-Principles Cohesive Zone Model*: versioned publisher PDF `version=1608279623`, §2.1 eq. (1), p. 3; §2.1.2 eqs. (2)–(3), p. 4; §§2.1.3–2.1.4, pp. 5–6. Relevant text and p. 4 equations inspected, CC BY 4.0 footer verified on p. 16. The energy convention, fixed transverse constraints and local/excess opening are preserved. The traction and peak are project derivatives, not separately quoted source equations.
17. [Pierce and Sullivan, NASA TN D-5140 (April 1969)](https://ntrs.nasa.gov/citations/19690012030): printed p. 6 / PDF p. 9 and symbols pp. 2–3 inspected. The explicit range 2a/W≤0.8 with full-width W resolves Wilson p. 21’s inconsistent a/W≤0.8 wording. Its plasticity-corrected crack length is distinguished from this catalog’s strictly elastic a_bar=a expression. The reported 0.3% secant/polynomial comparison is not independently certified uncertainty. NTRS states US-government work/public use permitted; no license identifier is invented.

The [new model overview](MECHANICS_CATALOG.md) records exact dimensions, conditions, derivations and source discrepancies. None of these additions bundles article text, PDF, figures or experimental/computed material datasets. Metadata inspection and formula checks are not independent scientific validation.

The eight implemented claim records comprise HS/Reuss/Voigt for bulk and shear, plus derived E/ν outer envelopes. HS/Voigt equation cross-checks remain distinct from standard Reuss expressions and contextual citations; the original historical Reuss source has not been independently checked. The E/ν envelopes are project algebraic derivations from isotropic identities and monotonicity over separate compatible HS intervals, not independently reviewed tight joint bounds. Source constituent E/ν parameters are not evidence of an effective-composite E/ν prediction. A fabricated equation locator must never fill a verification gap.

The v0.2.0 increment added one metadata-only identity source; it adds no bundled paper text or PDF, reuse permission, or independent scientific review. The exact original 1963 equations and joint endpoint attainability remain unverified. See [Model](MODEL.md) for the derivation and [migration](MIGRATION_v0.2.0.md) for typed dependencies.

## v0.5.0 addition: strict elastic-stability source

18. [Mouhat and Coudert (2014), “Necessary and sufficient elastic stability conditions in various crystal systems”](https://doi.org/10.1103/PhysRevB.90.224104), *Physical Review B* 90, 224104, published 2014-12-05. The [published author-hosted PDF](https://www.coudert.name/papers/10.1103_PhysRevB.90.224104.pdf) was read in full and equations visually checked. The catalog records the distinct [arXiv:1410.0065v3](https://arxiv.org/abs/1410.0065v3), dated 2014-12-05. General: p. 1 Eqs. (2)–(3) and following equivalent conditions; cubic: p. 2 Eqs. (5)–(6); hexagonal: p. 2 Eqs. (7)–(9); orthorhombic: p. 3 Eqs. (16), (18). Footnote 19 p. 4 supplies the Voigt order; the full engineering shear convention is explicit project metadata. Copyright ©2014 APS; no general reuse license verified, and the arXiv distribution license is not a general CC license. Only metadata and original notes are bundled.

The v0.5.0 total was **19 claims, 18 sources**. The four new records are catalog-only logical stability predicates with no output unit, not scalar property bounds. They concern strict stress-free homogeneous harmonic elasticity; loaded Eq. (20), phonon stability and strength are excluded. All previous source records remain unchanged. Full definitions, boundary cautions and a documentation-only anisotropic Poisson-ratio caveat are in [Elastic stability](ELASTIC_STABILITY.md).

## v0.6.0 addition: finite-porosity cross-check

19. [Roberts and Garboczi (2002), “Computation of the linear elastic properties of random porous materials with a wide variety of microstructure”](https://doi.org/10.1098/rspa.2001.0900), *Proceedings of the Royal Society of London A* 458, issue 2021, 1033–1054; published online 3 April 2002. The [official NIST record](https://www.nist.gov/publications/computation-linear-elastic-properties-random-porous-materials-wide-variety-0) links the [NIST-hosted reprint](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=916993). Section 2(b), Eq. (2.8), printed p. 1037 / PDF p. 6, cross-checks the finite-porosity HS Young upper bound. Its p is **solid fraction**, defined on printed p. 1034 / PDF p. 3; use `p_source=1-p_catalog`. Isotropic identities are on printed p. 1035 / PDF p. 4. The cover and printed pp. 1033–1038 were visually inspected, not the full paper or proof. The cover describes the contribution as not subject to copyright, but printed p. 1033 carries a 2002 Royal Society copyright notice. Both notices remain explicit; no blanket reuse right or license identifier is inferred. Metadata and original notes only are bundled.

The v0.6.0 total was **22 claims and 19 sources**. All original 19 claims and 18 source records remain unchanged. The three porous records are catalog-only: two scalar-modulus bounds and one derived Young outer envelope. They add no numerical API or chart and do not certify a particular material or simultaneous K/G attainment.

Additional research for this batch visually checked Kochmann–Milton arXiv v1 PDF/printed pp. 18–20: upper Eqs. (117), p. 18, and (118), p. 19; lower Eqs. (134)/(135), p. 20; also Eq. (127). This additional inspection is documented here without rewriting the existing source record. The solid/void formulas and zero-phase endpoints are project algebraic specializations using an isotropy-preserving positive-stiffness limit, not a direct insertion of zero into singular expressions. Original Hashin–Shtrikman equations and an independent proof review remain unavailable. See [finite-porosity formulas, endpoints, density and derivation limits](POROUS_BOUNDS.md).

## v0.7.0 addition: one experimental study, two property summaries

20. [Lee, Wei, Kysar and Hone (2008), “Measurement of the Elastic Properties and Intrinsic Strength of Monolayer Graphene”](https://doi.org/10.1126/science.1157996), *Science* 321(5887), 385–388, 18 July 2008; [PubMed metadata](https://pubmed.ncbi.nlm.nih.gov/18635798/). Relevant main-text passages were checked in a coauthor-uploaded author PDF; supporting supplementary material was inaccessible and **not inspected**. Source ID `lee_wei_kysar_hone_2008` supports two separate catalog-only observations under the same study ID:

- p. 386 Eq. (2) and membrane discussion: clamped isotropic circular-membrane stiffness fitting, negligible bending, point-load approximation and assumed ν=0.165
- p. 386 final paragraph: 23 membranes from two flakes; p. 387 opening discussion: 67 fits, stiffness distribution mean 342 N/m and SD 30 N/m. These are stiffness-fit statistics, not breaking-test sample counts
- p. 387 final paragraph: reported in-plane stiffness 340 ± 50 N/m
- p. 386 Eq. (1) and following maximum-stress discussion: second Piola–Kirchhoff stress with Lagrangian strain, σ=E2D ε+D2D ε² and source-model maximum −E2D²/(4D2D)
- p. 387 final text column: nonlinear finite-element inference from failure force with finite-radius indentation; p. 388 opening paragraph: inferred breaking strength 42 ± 4 N/m, not a directly measured uniform tensile stress

The ± type, coverage factor and confidence level remain unverified for both summaries. Temperature, atmosphere, humidity and loading rate remain unknown; the separate SD 30 N/m does not explain or replace ±50 N/m. No independent replication, raw-data reanalysis, defect census or independent scientific review is claimed. Two properties from one study are not two independent confirmations.

Copyright ©2008 AAAS, all rights reserved; no open reuse license is verified. Public access to an author PDF does not permit redistribution. Only metadata, brief numerical facts and original notes are bundled; no PDF, figures or raw experimental data are included. The original 19 source records and all 22 claims remain unchanged. See [observation semantics and evidence](OBSERVATIONS.md) and [v0.7.0 migration](MIGRATION_v0.7.0.md).

## Licenses and release status

Version 0.16.0 was the first public-release baseline; version 0.17.0 adds only
the bounded monolayer MoS2 observation batch described below. Original project code, documentation
and original curation use the [MIT License](../LICENSE), under maintainer handle
chaotic-mixture. Scientific facts and third-party works are not relicensed.
Public readability, arXiv hosting, a supplement or a repository link does not
alone authorize republication. [Third-party notices](../THIRD_PARTY_NOTICES.md)
record the public-release boundary and source-specific rights caveats.

## Adding a claim or observation responsibly

Record the exact property, dimension, constituent and effective symmetries, constitutive regime, loading/interface assumptions, fraction conventions, source version, equation/page locator and license/read status. Distinguish a theorem, construction, conjecture, empirical fit and computed observation. Declare whether a record is catalog-only or supported by a fixed reviewed executable rule; textual formulas are never evaluated. Catalog-only records must not be presented as computed results or checked specimen applicability. Preserve theorem, outer-envelope and model-estimate, model-relation and stability-criterion classifications, dimensional metadata, and parameter conventions. Add independent fixtures and non-applicability tests. Keep unknown information explicit. Do not promote source-level metadata into claim-level scientific verification.

Observation curation additionally requires study-level identity, specimen and method context, explicit model dependence, statistical-notation limits and the correct scope of every sample count. Keep observations separate from reusable claims and executable inputs. Preserve N/m dimensionality and the source stress/strain convention; a unit match alone is not a valid material comparison.

## v0.8.0 extension: four predicates, no new sources

The catalog now has **26 claims, 20 sources and two observations from one study**. All prior 22 claims, all 20 source records and both observation records are preserved. The new claims refer to the existing Mouhat–Coudert (2014) source ID; the additional locators live in their claim-level evidence. This documentation records the inspection without editing the source-catalog record or expanding its rights.

The published author-hosted *Physical Review B* 90, 224104 PDF was accessed and its four already-available page renders visually inspected. Table I and Eqs. (7), (9)–(15) were checked directly:

- **Tetragonal I**, Laue 4/mmm, six independent constants: matrix Eq. (7), criteria Eq. (9), p. 224104-2. Eq. (8) is a hexagonal specialization; tetragonal C66 remains independent
- **Tetragonal II**, Laue 4/m, seven independent constants: matrix Eq. (10), criteria Eq. (11), p. 224104-2. Preserve C26=−C16 and the strict margin C66(C11−C12)−2C16²
- **Rhombohedral I / trigonal**, Laue −3m, six independent constants: matrix Eq. (12), criteria Eq. (13), p. 224104-3. C66=(C11−C12)/2 is dependent; the strict coupling margin is C44(C11−C12)−2C14²
- **Rhombohedral II / trigonal**, Laue −3, seven independent constants: matrix Eq. (14), criteria Eq. (15), p. 224104-3. Preserve the combined margin C44(C11−C12)−2(C14²+C15²) and all matrix signs; separate coupling bounds are insufficient

Table I supplies the source I/II classes and counts. Footnote 19 supplies Voigt ordering. The full engineering shear-vector and right-handed orthonormal Cartesian axis prescriptions are explicit project conventions consistent with the matrices, not claims that the paper spells out every coordinate choice. Full template matching is required. These are jointly necessary and sufficient strict stress-free homogeneous harmonic conditions, not claims of loaded-state, phonon or strength stability. The rhombohedral determinant's squared coupling margin makes a positive determinant alone insufficient; equality requires a separate PSD check before any harmonic-marginality language.

Original synthetic checks of full matrices include exact principal minors, characteristic factorizations, high-precision eigenvalues and rotation invariance. They support transcription/algebra checks, not independent scientific peer review, a proof review or material-specific validation. Existing APS copyright and absence of a verified general reuse license remain unchanged. No article prose, PDF, page, figure or raw material data is bundled. See [criteria and exact boundary fixtures](ELASTIC_STABILITY.md) and [migration](MIGRATION_v0.8.0.md).

## v0.9.0 fatigue provenance

The v0.9.0 development milestone had 28 claims, 25 sources and two observations from one study. The original 20 source records remain unchanged, including Wilson. Newly visually inspected Wilson fatigue pages are recorded in the two claim-level evidence entries: definitions Eqs. (43)–(44), printed p. 35; Paris Eq. (45), p. 37; Forman Eq. (48), p. 40. No global source-status upgrade is implied.

Five new source identities separate Paris–Erdogan 1963 and Forman–Kearney–Engle 1967 historical attribution (original full-text equations inaccessible), Hudson NASA-TN-D-5390 experimental context (historical k normalization, no transferred constants), AFGROW modern-equation cross-check and ASTM E647-24 public applicability guidance (full standard unread, no fit validation or compliance claim). See [precise locators and rights](FATIGUE_GROWTH.md). No PDFs, figures, raw data or fitted coefficients are bundled; independent scientific review remains false.

## v0.11.0 anisotropy source batch

Four new records support two catalog-only definitions: Zener’s 1948 book remains
metadata-only historical attribution with unknown DOI; Ranganathan and
Ostoja-Starzewski’s 2008 PRL and the 2011 Ranganathan–Ostoja-Starzewski–Ferrari
JAM paper were read with defining pages visually checked; Knowles–Howie 2015
provides primary cubic-convention support. Existing source records remain
unchanged. The 2011 infinity symbol was falsely extracted as 1; visual inspection
is authoritative. No finite maximum is stored. APS/ASME open reuse rights are
unverified; Knowles–Howie states CC Attribution without an inspected version.
No source PDFs or figures are bundled. Full locators and links are in the
[anisotropy guide](ELASTIC_ANISOTROPY.md).


## NIST cryogenic bibliography and conservative omission

The five NIST cryogenic coefficient datasets and all derived results are omitted
from this public release. Their bibliographic/source records remain to preserve
provenance. Omission pending reuse clarification is not a finding that
redistribution is prohibited, and it does not exclude unrelated literature
numerical facts such as the graphene observations or Ni/Si predictions.

NIST's [current curated-collection listing](https://www.nist.gov/srd/related-data-products-and-links/curated-data-collections)
identifies the database as formerly SRD 152. Its [related-products explanation](https://www.nist.gov/srd/related-data-products-and-links)
distinguishes curated collections from current SRD critical-evaluation criteria;
the [cryogenics homepage](https://trc.nist.gov/cryogenics/) also records a past-SRD
origin. These statuses do not themselves establish a verified express grant to
redistribute or relicense the particular correlations. No public-domain/CC0
claim or NIST endorsement is inferred. The [general policy](https://www.nist.gov/copyrights-disclaimers)
and [SRD/data policy](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications)
provide context, not a newly verified product-specific grant.

The retained source identities cover the five property pages, the reference
list, material index, 2006 database paper, general reuse guidance and provenance
homepage. No coefficient table, equation-range transcription or derived plot is
reproduced here. The runnable catalog instead uses original synthetic examples;
see [temperature contract](TEMPERATURE_MODELS.md) and [notices](../THIRD_PARTY_NOTICES.md).

## v0.16.0 hydrostatic-compressibility provenance

Two source identities accompany the two hydrostatic-compressibility claims.
The v0.16.0 first public-release baseline has 34 mechanics claims and 47 source records, including
the separate original synthetic-demo source. Existing bibliographic identities
and source-specific rights caveats are preserved. The proofs of the all-real normalized range at fixed
positive κ, trace/spectral consequences and strict same-tensor energy constraint
are **original project derivations**, not inspected primary-source theorems.

- `ortiz_2012_anisotropic_mof_elasticity`: Aurélie U. Ortiz, Anne Boutin,
  Alain H. Fuchs and François-Xavier Coudert (2012), “Anisotropic Elastic
  Properties of Flexible Metal-Organic Frameworks: How Soft are Soft Porous
  Crystals?”, Physical Review Letters 109, 195502, published 7 November 2012.
  [DOI and publisher record](https://doi.org/10.1103/PhysRevLett.109.195502),
  [author-hosted published PDF](https://www.coudert.name/papers/10.1103_PhysRevLett.109.195502.pdf).
  Relevant published pages were visually checked: printed 195502-2, Eqs. (2)–(3)
  give E(n), β(n) and the full-compliance convention; printed 195502-4 gives
  cubic β=1/(C11+2C12) and the local elastic-region limitation. Publisher
  bibliographic/rights metadata was checked. No material numbers, transition
  response or unrelated Hill/shear-convention wording is imported. ©2012 APS;
  no general reuse license verified.
- `miller_evans_marmier_2015_linear_compressibility`: W. Miller, K. E. Evans
  and A. Marmier (2015), “Negative linear compressibility in common materials”,
  Applied Physics Letters 106(23), 231903, published 8 June 2015.
  [DOI](https://doi.org/10.1063/1.4922460),
  [institutional author manuscript](https://uwe-repository.worktribe.com/index.php/preview/843503/NLC_CommMat.pdf),
  [publisher-deposited Crossref metadata](https://api.crossref.org/works/10.1063/1.4922460).
  Manuscript p. 4 Eq. (1), preceding isothermal pressure/length definitions and
  explicitly orthorhombic/orthotropic Eq. (2) were **text-checked only**; p. 5
  separates small-strain estimates from higher-pressure behavior. Do not apply
  the diagonal-only specialization to general normal–shear-coupled tensors.
  Equation-page images could not be checked; direct PDF access returned HTTP 403,
  which was respected. No visual verification, original published-pagination
  equivalence or full-SPD range proof is claimed. Crossref confirms canonical
  metadata but not paper inspection or a reuse license. No general reuse license
  was verified; its license field was absent, and the repository index reports
  ©2015 AIP Publishing LLC.

Only bibliographic facts, formulas and original notes are bundled. Temporary
source PDFs, page renders, figures and extracted article full text must remain
outside the repository and release artifacts. Neither public access nor formula
inspection grants redistribution rights. Independent scientific/native-language
review remains unperformed. Full scientific scope, source locators and the
attribution boundary are in [the compressibility guide](DIRECTIONAL_COMPRESSIBILITY.md).

## v0.17.0 addition: one monolayer MoS2 study, two summaries

Exactly one source record, `bertolazzi_brivio_kis_2011`, is appended to the
unchanged 47-record source catalog. All existing claims, two graphene
observations, predictions and synthetic temperature contents retain their
facts and contracts. The new records share one study identity:

Simone Bertolazzi, Jacopo Brivio and Andras Kis (2011),
[“Stretching and Breaking of Ultrathin MoS2”](https://doi.org/10.1021/nn203879f),
*ACS Nano* 5(12), 9703–9709. Publisher-indexed abstract,
[PubMed](https://pubmed.ncbi.nlm.nih.gov/22087740/) and
[EPFL metadata](https://infoscience.epfl.ch/entities/publication/e119e335-b8de-42b8-a8e3-ec8b6d3fd8ba)
corroborate bibliographic identity. Source online date is 16 November 2011;
issue date is 27 December 2011.

The inspected [institutional PDF](https://infoscience.epfl.ch/server/api/core/bitstreams/5af84a4c-55a4-4151-9d85-d5c215d848a4/content)
is proof-formatted: seven lettered pages A–G and placeholder journal footers,
despite EPFL's “Publisher’s Version”, “Published version” and “openaccess”
labels. Use PDF page plus printed letter, not unverified final-journal mapping.
Final publisher text and artifact equivalence remain unverified. The artifact
SHA-256 is `348f5d00676c252d79f3717802be4cc999349c7180b261219bd209ebbe17e9ca`.

- PDF p. 4 (D), right column: monolayer in-plane stiffness **180 ± 60 N/m**;
  the following sentence explicitly defines property uncertainties as SD
- PDF p. 5 (E), left column below Eq. (3): monolayer breaking strength
  **15 ± 3 N/m**. This is finite spherical-tip model inference of local central
  failure stress, not measured uniform tension or Lee's nonlinear FE model
- PDF p. 4 (D), upper-right after Eq. (1): printed
  **q = 1/(1.05 − 0.15ν − 0.16ν²)**, assumed **ν = 0.27**, stated **q = 0.95**.
  They are retained separately and explicitly flagged inconsistent. Curator
  arithmetic is approximately **1.002168693051764**, not a replacement source
  constant. The actual q used in fitting is unresolved; no refit or strength
  recomputation is performed
- PDF p. 3 (C) and p. 4 (D): **nine monolayer membranes** are study/stiffness
  counts; no separately verified failure-event total is reported. Six bilayer
  membranes are context only, outside the selected batch
- PDF p. 2 (B): **2 μm/s vertical probe translation speed** is not strain rate
  or force/stress rate. Actual test environment and stress/strain measures remain
  unknown; the 400 °C vacuum anneal is preparation only
- Main text reports 550 ± 10 nm spans and 12 ± 2 nm tip radius. Their tolerance
  type is unspecified; the property-SD definition is not transferred to geometry

All seven pages were text-checked and PDF pp. 3–6 visually inspected; a second
transcription check addressed the same artifact. These checks do not constitute
independent scientific review, raw-data reanalysis or replication. The publisher
full-text request returned HTTP 403; the official supplement route failed and
the supplement remains unread. The public EPFL copy had been located
independently before that failure; no blocked route was bypassed. Main-text
SEM-based tip-radius reporting is not independent inspection of the supplement.
The breaking-average body text points to Fig. 4 although summary bars are in
Fig. 5; evidence locators use the body paragraph. Bilayer and thickness-normalized
3D results are excluded, with no graph digitization or inferred replacement.

Publisher metadata states ©2011 American Chemical Society; the proof PDF has
an ACS notice with a placeholder year. No explicit open-reuse license is
verified. Only brief factual values, metadata, source locators and original
curation are included; **no PDF, article full text, figures, page screenshots
or raw measurement collection** is bundled. MIT does not relicense the paper
or scientific facts, and no legal clearance is claimed. SD does not imply SEM,
a confidence interval, 68% coverage or a complete uncertainty budget. The
existing graphene ± values remain statistically unspecified. See
[observation evidence and limits](OBSERVATIONS.md),
[migration](MIGRATION_v0.17.0.md) and [notices](../THIRD_PARTY_NOTICES.md).

## Complete public source index (v0.17.0)

These are the 48 packaged source identities, including one original synthetic
provenance record. A bibliographic record is not a bundled publication or dataset;
see each canonical record and the guides above for read/review and rights status.
Repeated works in distinct source roles are not independent studies.

- `hashin_shtrikman_1963`: [A variational approach to the theory of the elastic behaviour of multiphase materials](https://doi.org/10.1016/0022-5096(63)90060-7)
- `kochmann_milton_2014`: [Rigorous bounds on the effective moduli of composites and inhomogeneous bodies with negative-stiffness phases](https://doi.org/10.1016/j.jmps.2014.06.010)
- `berger_2017`: [Mechanical metamaterials at the theoretical limit of isotropic elastic stiffness](https://doi.org/10.1038/nature21075)
- `milton_2018_comment`: [Stiff competition](https://doi.org/10.1038/s41586-018-0724-8)
- `berger_2018_reply`: [Berger et al. reply](https://doi.org/10.1038/s41586-018-0725-7)
- `singh_lai_2024`: [Isotropic Metamaterial Stiffness Beyond Hashin-Shtrikman Upper Bound](https://arxiv.org/abs/2411.11332v1)
- `materials_project_elasticity`: [Materials Project documentation: Elasticity](https://docs.materialsproject.org/methodology/materials-methodology/elasticity)
- `genin_birman_2009`: [Micromechanics and structural response of functionally graded, particulate-matrix, fiber-reinforced composites](https://doi.org/10.1016/j.ijsolstr.2008.08.010)
- `meille_garboczi_2001`: [Linear elastic properties of 2D and 3D models of porous materials made from elongated objects](https://doi.org/10.1088/0965-0393/9/5/303)
- `griffith_1921`: [The Phenomena of Rupture and Flow in Solids](https://doi.org/10.1098/rsta.1921.0006)
- `wilson_1992_nasa_tm_103591`: [Linear Elastic Fracture Mechanics Primer](https://ntrs.nasa.gov/citations/19920021173)
- `frenkel_1926`: [Zur Theorie der Elastizitätsgrenze und der Festigkeit kristallinischer Körper](https://doi.org/10.1007/BF01397292)
- `shimanek_2022_ideal_shear`: [Insight into ideal shear strength of Ni-based dilute alloys using first-principles calculations and correlational analysis](https://doi.org/10.1016/j.commatsci.2022.111564)
- `rose_ferrante_smith_1981`: [Universal Binding Energy Curves for Metals and Bimetallic Interfaces](https://doi.org/10.1103/PhysRevLett.47.675)
- `van_der_ven_ceder_2004`: [The thermodynamics of decohesion](https://doi.org/10.1016/j.actamat.2003.11.007)
- `azocar_guzman_2020_hydrogen`: [Hydrogen Embrittlement at Cleavage Planes and Grain Boundaries in Bcc Iron—Revisiting the First-Principles Cohesive Zone Model](https://doi.org/10.3390/ma13245785)
- `pierce_sullivan_1969_nasa_tn_d_5140`: [Factors Influencing Low-Cycle Crack Growth in 2014-T6 Aluminum Sheet at -320°F (77 K)](https://ntrs.nasa.gov/citations/19690012030)
- `mouhat_coudert_2014_elastic_stability`: [Necessary and sufficient elastic stability conditions in various crystal systems](https://doi.org/10.1103/PhysRevB.90.224104)
- `roberts_garboczi_2002_porous`: [Computation of the linear elastic properties of random porous materials with a wide variety of microstructure](https://doi.org/10.1098/rspa.2001.0900)
- `lee_wei_kysar_hone_2008`: [Measurement of the Elastic Properties and Intrinsic Strength of Monolayer Graphene](https://doi.org/10.1126/science.1157996)
- `paris_erdogan_1963`: [A Critical Analysis of Crack Propagation Laws](https://doi.org/10.1115/1.3656900)
- `forman_kearney_engle_1967`: [Numerical Analysis of Crack Propagation in Cyclic-Loaded Structures](https://doi.org/10.1115/1.3609637)
- `hudson_1969_nasa_tn_d_5390`: [Effect of Stress Ratio on Fatigue-Crack Growth in 7075-T6 and 2024-T3 Aluminum-Alloy Specimens](https://ntrs.nasa.gov/citations/19690025326)
- `afgrow_dtd_handbook_fatigue_growth`: [AFGROW Damage Tolerant Design Handbook: Fatigue Crack-Growth Rate (FCGR) Descriptions](https://www.afgrow.net/applications/dtdhandbook/sections/page5_1_2.aspx)
- `astm_e647_24_public_scope`: [ASTM E647-24: Standard Test Method for Measurement of Fatigue Crack Growth Rates](https://store.astm.org/e0647-24.html)
- `nist_cryogenic_al6061_t6`: [NIST Cryogenic Material Properties: 6061-T6 Aluminum](https://trc.nist.gov/cryogenics/materials/6061%20Aluminum/6061_T6Aluminum_rev.htm)
- `nist_cryogenic_ss304`: [NIST Cryogenic Material Properties: 304 Stainless](https://trc.nist.gov/cryogenics/materials/304Stainless/304Stainless_rev.htm)
- `nist_cryogenic_reference_list`: [NIST Cryogenic Material Properties: Reference List](https://trc.nist.gov/cryogenics/materials/references.htm)
- `bradley_radebaugh_lewis_2006`: [Cryogenic Material Properties Database, Update 2006](https://trc.nist.gov/cryogenics/Papers/Material_Properties/2006-Cryogenic_Material_Properties_Database-Update_2006-ICEC21_Prague.pdf)
- `nist_public_information_reuse`: [NIST public-information reuse guidance](https://www.nist.gov/copyrights-disclaimers)
- `zener_1948_elasticity_anelasticity`: [Elasticity and Anelasticity of Metals](https://books.google.com/books/about/Elasticity_and_Anelasticity_of_Metals.html?id=FKcZAAAAIAAJ)
- `ranganathan_ostoja_starzewski_2008_anisotropy`: [Universal Elastic Anisotropy Index](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.101.055504)
- `ranganathan_ostoja_starzewski_ferrari_2011_anisotropy`: [Quantifying the Anisotropy in Biological Materials](https://doi.org/10.1115/1.4004553)
- `knowles_howie_2015_cubic_shear`: [The Directional Dependence of Elastic Stiffness and Compliance Shear Coefficients and Shear Moduli in Cubic Materials](https://link.springer.com/article/10.1007/s10659-014-9506-1)
- `shimanek_2022_arxiv_2108_06412_v2`: [Insight into Ideal Shear Strength of Ni-based Dilute Alloys using First-Principles Calculations and Correlational Analysis](https://arxiv.org/abs/2108.06412v2)
- `dubois_2006_prb_74_235203`: [Ideal strength of silicon: An ab initio study](https://doi.org/10.1103/PhysRevB.74.235203)
- `nist_cryogenic_al5083`: [NIST Cryogenic Material Properties: 5083-O Aluminum (NIST index label)](https://trc.nist.gov/cryogenics/materials/5083%20Aluminum/5083Aluminum_rev.htm)
- `nist_cryogenic_invar`: [NIST Cryogenic Material Properties: Invar (Fe-36Ni)](https://trc.nist.gov/cryogenics/materials/Invar(Fe-36Ni)/Invar_rev.htm)
- `nist_cryogenic_ss316`: [NIST Cryogenic Material Properties: 316 Stainless](https://trc.nist.gov/cryogenics/materials/316Stainless/316Stainless_rev.htm)
- `nist_cryogenic_material_index`: [NIST Cryogenic Material Properties Index](https://trc.nist.gov/cryogenics/materials/materialproperties.htm)
- `nist_cryogenic_srd_provenance`: [NIST Cryogenic Technology Resources: SRD project provenance](https://trc.nist.gov/cryogenics/)
- `ting_chen_2005_poisson_unbounded`: [Poisson's ratio for anisotropic elastic materials can have no bounds](https://doi.org/10.1093/qjmamj/hbh021)
- `norris_2006_cubic_poisson`: [Poisson's ratio in cubic materials](https://doi.org/10.1098/rspa.2006.1726)
- `norris_2006_anisotropic_extrema`: [Extreme values of Poisson's ratio and other engineering moduli in anisotropic materials](https://doi.org/10.2140/jomms.2006.1.793)
- `ortiz_2012_anisotropic_mof_elasticity`: [Anisotropic Elastic Properties of Flexible Metal-Organic Frameworks: How Soft are Soft Porous Crystals?](https://doi.org/10.1103/PhysRevLett.109.195502)
- `miller_evans_marmier_2015_linear_compressibility`: [Negative linear compressibility in common materials](https://doi.org/10.1063/1.4922460)
- `materials_boundaries_synthetic_temperature_demo`: [Materials Boundaries original SYNTHETIC temperature demonstrations](https://github.com/chaotic-mixture/materials-boundaries-public/blob/main/docs/TEMPERATURE_MODELS.md)

- `bertolazzi_brivio_kis_2011`: [Stretching and Breaking of Ultrathin MoS2](https://doi.org/10.1021/nn203879f)

## v0.18.0 bulk elastic-wave evidence and original derivations

This batch appends exactly two sources to the former 48, giving **50 source
records**. Both support catalog-only continuum relations, not measurements or
material-specific acoustic predictions. Existing source records retain their
original rights, inspection scope and verification gaps.

- `chevrot_vanderhilst_2003`: Sébastien Chevrot and Robert D. van der Hilst,
  “On the effects of a dipping axis of symmetry on shear wave splitting
  measurements in a transversely isotropic medium,” *Geophysical Journal
  International* **152(2)**, 497–505 (2003),
  [DOI 10.1046/j.1365-246X.2003.01865.x](https://doi.org/10.1046/j.1365-246X.2003.01865.x).
  The inspected [university-hosted journal-layout PDF](https://hilst.mit.edu/wp-content/uploads/2017/05/2003_gji_152-497-505.pdf)
  was visually checked at §2, printed p. 498 / PDF p. 2, Eqs. (1)–(4).
  These establish the homogeneous plane-wave equation, density-normalized
  Christoffel tensor, squared-phase-speed eigenvalue and displacement
  polarization. First-pair minor symmetry and index relabeling map its Eq. (3)
  to Q_ik=C_ijkl n_j n_l, Γ=Q/ρ. The paper's later weak-anisotropy perturbation,
  numerical cases and material results are not imported. ©2003 RAS; no general
  reuse license was verified
- `xiang_qi_wei_2018_arxiv_v2`: Hua Xiang, Liqun Qi and Yimin Wei,
  “On the M-eigenvalues of elasticity tensor and the strong ellipticity
  condition,” [arXiv:1708.04876v2](https://arxiv.org/abs/1708.04876v2),
  [versioned PDF](https://arxiv.org/pdf/1708.04876v2). The v2 record was
  submitted 22 January 2018; its PDF title date is 23 January 2018.
  Printed/PDF p. 2 (rank-one criterion and tensor symmetries) and pp. 4–5
  (positive-definiteness implication, isotropic tensor and unnumbered v_P/v_S
  identities) were visually checked. No journal-version verification is
  claimed. The arXiv nonexclusive distribution permission is not general
  republication or relicensing permission

Three source qualifications are scientifically important. The strict rank-one
quantifiers explicitly exclude zero vectors. Full positive strain energy is
restricted to nonzero **symmetric** strains, not arbitrary nonsymmetric matrices
whose skew part is annihilated by elasticity's minor symmetries. The catalog
does not reuse a derivation that divides by K+G/3 at its zero value: direct
contraction correctly handles K=−G/3 and its triple wave degeneracy.

The exact positive-energy isotropic class ratio (√(4/3),∞), its unattained
infimum/unbounded upper extent, index mapping, SPD-to-strong-ellipticity proof,
K=−G/3 hydrostatic-energy counterexample, fixed-tensor compactness bounds and
unit audit are **original project derivations**. They are written out in
[BULK_ELASTIC_WAVES.md](BULK_ELASTIC_WAVES.md), rather than attributed to a
source's interval theorem or independent peer review. The two claims do not
cite an uninspected book chapter or generalized-continuum corroboration.

The original full-energy stability sources are not newly re-audited by this
batch, and their existing claims are not redefined. No article PDF, full text,
page image or figure is included. Formula inspection and symbolic/software
checks establish neither physical realizability nor independent scientific
review. See [migration](MIGRATION_v0.18.0.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).
