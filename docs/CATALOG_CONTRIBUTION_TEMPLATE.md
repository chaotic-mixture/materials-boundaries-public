# Catalog contribution review template

Copy this checklist into the contribution description. It is a human review
template, not a new JSON schema or a production catalog record. Never fill a gap
by copying a verification or license assertion from another source.

## Identity and scope

- Contribution type: evidence enrichment / distinct existing-contract record /
  proposed new scientific contract
- Existing claim or observation ID(s) and source ID(s):
- Proposed new IDs, if necessary, and why the existing record cannot hold the evidence:
- Matching schema branch and scientific guide:
- Exact quantity, dimension, SI unit and classification:
- Formula and every parameter's meaning, dimension, unit and valid domain:
- Geometry, axes, loading, constitutive regime and full required assumptions:
- Dependencies and why they refer to the same compatible scientific system:
- Boundary cases, exclusions, uncertainty and limits:
- Why no new runtime, rendering, schema or CLI work is required, or why this is
  instead a separate new-contract proposal:

## Evidence and rights

- Source bibliographic metadata, DOI/official URL and edition/version:
- What was accessed: abstract / main text / supplement / displayed equations:
- Exact page, figure, equation or passage locators actually checked:
- What this source supports, and what is historical attribution only:
- Study identity and whether purported corroboration is actually the same study:
- Uninspected materials, unresolved inconsistencies and unknown conditions:
- Read status, evidence verification status and independent-review status:
- License identifier only when verified; supporting rights notice or explicit
  unknown/conflicting status:
- Bundled content and why no unlicensed source text/images are redistributed:

## Four-language presentation

- Authored `catalog_name_<id>` labels: en / zh / ja / de
- Canonical IDs, parameter symbols, units and quantities remain unchanged:
- Unknown conditions, model dependence, nonexecution and review/rights caveats
  retain the same meaning in every language:
- Independent scientific/native-language review performed, or explicitly pending:

## Validation evidence

- `python scripts/validate_catalogs.py` result:
- `python -m unittest discover -s tests -v` result:
- Exact eight executable claim/rule pairs and unchanged existing numeric outputs:
- New-ID/source/labels or evidence-only append test:
- Negative tests for units, assumptions, classification, references and execution:
- Packaging and visualization smoke result, when preparing a release:

Passing software checks establishes structural consistency only. It does not
certify scientific truth, applicability to a specimen, independent scientific
review, translation quality or permission to reuse a source.

## Hydrostatic compressibility review (when applicable, v0.16.0)

- Exact `hydrostatic_compressibility_contract` family and definition dependency:
- Dimensional `inverse_pressure` / `Pa^-1` versus normalized `dimensionless` / `1`:
- Finite real full-SPD 3D, full inverse, stress-free infinitesimal, fixed-temperature
  setting; orthonormal Cartesian axes; compression-positive p and σ=−pI:
- Engineering shear audit, including B off-diagonals (g4,g5,g6)/2:
- Positive κ, orthonormal triad sum, fixed-tensor finite attained extrema:
- Varying-class all-finite-real normalized range at fixed κ>0, unattained infinities,
  cubic/isotropic 1/3 exception and principal-value versus direction-count warning:
- Strict same-S β²<κ/E; necessary and not sufficient for full SPD:
- Original project proofs versus source-supported definitions; source-specific
  visual/text-only inspection and unknown reuse rights:
- Full exclusions, catalog-only scope, four-language caveats and independent-review gaps:
- Fresh-ID dependency resolution, reordered parameters, malformed-unit/shear/sign/
  endpoint/attribution rejection, and unchanged executable registry checks:

Use [the scientific guide](DIRECTIONAL_COMPRESSIBILITY.md); never attach source
inspection PDFs, page images or full extracted article text to the contribution.
