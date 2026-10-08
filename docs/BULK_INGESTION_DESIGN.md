# Staged bulk material admission and natural taxonomy (v0.35.0 design)

## Baseline and scope

The immutable baseline is commit 7e37be919ee97f1275249dcf745f9f55e951986a,
tree 98b67e0632fb0595079c6c11b78c202c53dda0ac: 57 material identities,
57 source-scoped states, 57 properties, 20 grades, 108 sources, eight executable
scientific rules and four interface languages. Main is not the baseline.
Nothing in this work enables new evaluator rules or engineering allowables.

The five mutually exclusive primary classes are metal, inorganic, polymer,
composite and natural. Here natural means retained biological tissue/fiber
architecture. Minerals and rocks remain inorganic; feedstock origin alone does
not move processed polymers, extracted lignin, rubber formulations or ceramics.
An exact versioned taxonomy ledger changes ten biological identities: three
USDA woods, flax/hemp technical fibers, native silk/wool, cork and two bamboo
species. Only their category and the obsolete classification sentence change.
Historical numeric facts and source evidence remain exact; authorized category
outputs have explicit versioned differences rather than an unchanged-byte claim.

## Separate source staging from catalog admission

A dependency-free bulk pipeline accepts tables for source releases, source
files, license attestations, material identity candidates, observations and
exclusions. An adapter has a registered ID/version, permitted rights profiles
and a property-specific scientific validator. Staging binds the complete input,
baseline canonical identity keys, profile versions and all output hashes.
Reordering cannot alter the staged package; identical duplicate rows cannot
inflate staged coverage, but their presence remains bound into the input digest. Conflicting
canonical identities are quarantined together, never resolved by row order.
An exact reviewed digest and exact approved identity-key set are required by a
separate admission call. A candidate-supplied status cannot grant admission.

Identity, taxon, collection accession, observation, derivation, source release,
citation and tissue scope are separate concepts. Counts include admitted unique
identity keys with at least one traceable numerical property. Grades, states,
aliases, measurements and source-row counts do not create identities. Legacy
curated identity IDs remain stable; biological imports use accepted WFO ID plus
the declared collection-tissue scope. Canonical baseline crosswalk prevents wood
reimport while preserving cork as distinct tissue. Coverage reports all five
classes and their remaining distance to 1,000; no unreviewed research source is
implicitly imported.

## Generic derived-property contract and first profile

The existing crystallographic derivation contract remains valid. A separately
typed empirical conversion method has explicit input quantity, unit, basis,
original string, deposited output string, SI display value, formula identifier,
version/source, factor provenance, an explicit GWDD-methods source dependency
for the basic-density definition and water-density convention, nominal assumptions,
rounding resolution, uncertainty and scope. Closed profile validation couples
quantity, dimensions, basis, evidence kind and method, rejecting relabels.

The first reviewed profile is basic_wood_density: oven-dry mass over fresh or
water-saturated volume. Input is measured dimensionless air-dry specific gravity.
The displayed result is the deposited GWDD value, a conversion-derived estimate,
not a directly measured basic density, species mean or engineering design value.
The audit checks SG × 0.8281316 × the source water-density convention 1 g/cm³
against the deposited value to its 0.01 g/cm³ resolution. No unestablished tie
policy is asserted. SI is exactly the deposited rounded g/cm³ string × 1,000.
The 2018 calibration database is distinct from the 2019 xylothèque collection:
its trunk/specimen counts, drying temperature, uncertainty and tree-level
shrinkage values are not copied into these collection accessions.
The coefficient is empirically calibrated; 0.828 is publication-rounded while
0.8281316 comes from the pinned GWDD dictionary. No fitted-model or calibration
summary becomes an evaluator bound. GWDD hierarchical wsg_est stays excluded.

Nominal conversion moisture is 12%; actual specimen moisture remains null.
Temperature, tissue subtype, anatomical location, orientation and record-level
uncertainty remain unknown. Approximate source-method uncertainty and conversion
calibration residuals are not record uncertainty. plants_sampled=1 is retained
as a source report, not verified independent n. The inherited v1 mechanically
eligible source-record count is explicitly renamed and never treated as v2
validated observations. Palm Cocos nucifera retains unspecified anatomy; the
catalog does not imply all selected collection tissue is secondary-growth wood.

## Pinned v2 adapter and required provenance

Only reviewed batch SHA-256
5e059c0565f13610b307d9f71b1a29c65bec46aff127392d0b10eba469aef032 is eligible.
The v1 hold remains. The adapter verifies its complete manifest dependencies,
source registry, original CIRAD file, GWDD release/file, WFO June 2023 backbone,
review decision and baseline crosswalk before producing a staged candidate set.
Original and accepted names/authors, WFO accepted IDs and chains, rank/hybrid
markers, source rows/physical lines/accessions/field names, file hashes and
release DOIs survive storage and export. Original deposited citation and
normalized Patrick Langbour / Sébastien Paradis / Bernard Thibaut attribution
remain separate. Source-specific rights propagate through derivation; held
BY-SA/PROSEA rows and aggregates that contain them are not imported. Source PDFs,
images and full raw caches are not published.

Four-language presentation shows evidence type, physical basis, selected-accession
scope, assumptions, missingness and attribution beside each value. Canonical
JSON remains language independent. Runtime graphs validate once per operation;
rendering must not revalidate the entire graph once per row.

## Gates and verification

1. Accept taxonomy policy and exact migration ledger
2. Independently review the generic derivation/scientific profile and labels
3. Stage exact v2 inputs; verify deterministic selection and all negative gates
4. Admit exact accepted digest, then run complete runtime/schema/mixed regressions,
   exact old-output migration comparisons, strict replay checks and offline wheel
5. Independently review frozen payload and evidence; no remote write or promotion

Tests cover nonfinite/invalid decimals, units/basis, unknown property profiles,
missing provenance, denied licenses, taxonomic homonyms and ambiguous chains,
hybrids, canonical duplicate/conflict handling, baseline exclusions, mutation of
reviewed bytes, status spoofing, deterministic reordering/idempotence, honest
unknowns and retained display/export qualifiers. Time, peak memory and file size
are measured at 1,000, 3,793 and 10,000 candidates. Synthetic scale rows are marked
benchmark-only and can never be used as real material coverage.
