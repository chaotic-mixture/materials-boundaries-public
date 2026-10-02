# Contributing catalog knowledge

Contributions are welcome through [issues](https://github.com/chaotic-mixture/materials-boundaries-public/issues) and pull requests to [the public repository](https://github.com/chaotic-mixture/materials-boundaries-public). Use a focused change with source locators, explicit limitations and reproducible tests. Original contributed code, documentation and curation are covered by the project [MIT License](LICENSE); do not submit third-party works as though you own their rights. Preserve [source-specific notices](THIRD_PARTY_NOTICES.md).

Version 0.16.0 is the first public release. Earlier versioned guides describe development milestones. For a release, keep one version source, validate clean source and installed-wheel behavior, include both license files, and inspect generated artifacts for excluded data. A requested check is not a claim that it passed.

The catalog can grow without changing the calculator. First decide whether the
contribution adds evidence to an existing scientific claim, adds a distinct
record under an **already supported full scientific contract**, or introduces a
new scientific contract. A shared `claim_type` alone is not a shared contract.

## Prefer evidence enrichment

Search existing claims and sources before creating IDs. When the quantity,
formula, parameter definitions, geometry, assumptions, and limitations match an
existing claim, normally add a precisely located `evidence` entry to that claim.
Add a source record only if the source is genuinely new. Do not duplicate the
same science merely to increase the claim count. Independent sources, records
and studies are different concepts; one study is not two independent replications.

Use [the contribution template](docs/CATALOG_CONTRIBUTION_TEMPLATE.md) to record
what was actually inspected and which scientific contract is being reused.

## Existing-contract additions

1. Read the relevant guide and the complete matching branch in
   `schemas/claims.schema.json` or `schemas/observations.schema.json`. Preserve
   quantities, dimensions, SI units, parameter meanings, geometry, conventions,
   required assumptions, classification, dependency meaning and limitations.
   Retain the existing family's `rule_id`; the development validator also checks
   its closed family-assumption and structural-identity guards in
   `scripts/validate_catalogs.py`. Existing LEFM and stability branches support
   new record IDs; the currently
   ID-specific porous branches do not. A new geometry, symmetry or inference
   method is separate schema/scientific work, even if its top-level type matches.
2. Edit only the applicable production catalog files and accompanying authored
   documentation for an ordinary data contribution. Use stable unique IDs.
   Source and study references must resolve; claim dependencies must resolve and
   be acyclic. Do not add unsupported fields to bypass a schema constraint.
3. For every new claim or observation, add `catalog_name_<id>` labels in **en,
   zh, ja and de** in `materials_boundaries/data/locales.json`. Preserve canonical
   formulas, IDs and units. Ten explicitly named pre-alias claims retain their
   historical canonical names; this is not an exemption for new records.
4. Retain `evaluation_support: catalog_only` for an additional catalog-only
   record. A textual `rule_id` is a scientific descriptor, not executable code.
   Exactly the existing eight claim/rule pairs remain executable and plotted.
   No runtime, CLI, renderer or public-schema edit is needed for a supported
   existing-contract contribution.
5. Record source access, equation/passages inspected, bibliographic attribution,
   reuse-license evidence and remaining gaps separately. `null` is preferable to
   an invented locator or license. Software validation neither inspects a paper
   nor proves a theorem, verifies a specimen, upgrades review status or grants
   reuse rights. Do not copy a predecessor's inspected/reviewed status without
   independent supporting evidence. Keep translation review limitations explicit.

## Required offline checks

From the repository root:

```sh
python -m unittest discover -s tests -p test_release_metadata.py -v
python -m pip install -e '.[dev]'
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
```

`jsonschema` with its `format-nongpl` extra is a required **development** dependency
for this workflow. The validator exits unsuccessfully if it or any format checker
required by the local schemas is missing, and CI runs it before tests.
The release metadata preflight uses only the standard library and runs before
dependency installation in CI. It checks the single software-version source,
runtime engine labels, README release label, static comparison-schema snapshots
and their exact local references. It does not replace full schema validation.
The installed runtime remains dependency-free. The development validator is a
checkout script, not a new public CLI subcommand or a packaged runtime API.

The validator strictly loads JSON (including rejection of duplicate keys,
nonfinite and out-of-range numbers), applies local Draft 2020-12 schemas with
format checks and no network-reference retrieval, checks complete development-only
family assumptions and structural identities, unique IDs and source /
study / dependency references, detects dependency cycles, verifies the exact
eight executable claim/rule pairs, and checks four-language key/placeholder
parity and nonempty authored name labels. Unsupported schema families fail
closed. The development family guards supplement older schema branches that only
require distinguishing premises, without changing any public schema. Formula
wording, parameter meaning, limits and evidence still require human scientific
review. Translation checks are structural, not scientific or native-speaker review.

Validate a disposable candidate directory without touching production data:

```sh
python scripts/validate_catalogs.py --data-dir /path/to/candidate/data
```

That directory contains all current catalogs: `claims.json`, `sources.json`,
`observations.json`, `locales.json`, `temperature_models.json`,
`temperature_locales.json`, `computational_predictions.json` and
`prediction_locales.json`; schemas always come from this checkout. The command does not
modify the candidate. Its success output explicitly describes its limits.

## Reproduce the appendability regression

`tests/fixtures/contributions/lefm.json` is **synthetic test data only**, with a
reserved invalid-domain URL, no claimed paper inspection, no independent review,
and no inferred license. It contains a supported LEFM record with a fresh ID, a
fresh source, four authored labels, and an extra evidence entry for an existing
claim. It must never be promoted to the real catalog or counted as scientific
enrichment. The stability regression also exercises a fresh ID under its existing
contract. These fixtures deliberately duplicate science solely to test plumbing.

The contribution tests check the append path, the preferred evidence-only path,
canonical queries and four-language rendering, unchanged runtime evaluation and
the exact eight-series visualization boundary. Independent mutations of units,
required assumptions, classification, source references and execution support
must fail. Missing labels, invalid dates/URLs, duplicate IDs, missing study links
and unsupported scientific families must also fail.

For an end-to-end release acceptance check, copy the checkout to a disposable
directory, append a fresh synthetic fixture and labels to that copy, then run
the validator and **the entire existing test suite without editing prior tests**.
Run an isolated wheel install and the visualization demo from outside the source
tree as the release smoke check. Leave the real catalogs unchanged.

Historical scientific tests select explicit record IDs rather than assume that
the live catalog has a fixed count or order. Exact-set query tests use controlled
fixtures; generic integrity tests cover all current records. The executable set
is intentionally fixed. For a software release, update the literal in
`materials_boundaries/_version.py` and the current README release label.
Setuptools reads that literal through its dynamic `attr` configuration; no
runtime import of build tooling, checkout files or installed distribution
metadata is needed. Historical batches need no new package-version pins.
Scientific schema and record versions remain independent of software releases.
When a scientific contract changes, update its static schema and any comparison
snapshot/reference deliberately; never rewrite historical fixtures to satisfy
the current release label.

Build and check the actual wheel separately (the smoke check creates a disposable
venv, installs only that wheel without dependencies or index access, and runs
outside the source tree):

```sh
python -m pip wheel --no-deps --wheel-dir dist .
python scripts/check_wheel_metadata.py dist/materials_boundaries-<version>-py3-none-any.whl
```

The smoke check compares wheel METADATA, the packaged version literal, the
installed package and all output engine labels, and exercises JSON/text output
in en, zh, ja and de. Build dependencies are needed only when building the wheel.

## A genuinely new scientific contract

Do not weaken a branch, remove required assumptions, relabel units or introduce a
permissive catch-all schema to make a new record pass. Prepare the scientific
definitions, sources, uncertainty/limitations, schema design and tests as a
separate reviewed change. Executable support is an additional deliberate
engineering and scientific decision, never a side effect of catalog growth.

## Fatigue contract additions (v0.9.0)

The two reviewed fatigue families have closed schema 1.7.0 branches and complete development family guards. A same-family contribution must preserve modern K normalization, complete-cycle counting, 0<=R<1 scope, calibration conditions and exponent-dependent coefficient_units. A different R convention, unit contract, equation or growth regime needs new scientific/schema review. Do not treat a calibrated empirical model as a bound or executable rule. See [fatigue guide](docs/FATIGUE_GROWTH.md) and [migration](docs/MIGRATION_v0.9.0.md).

## Synthetic temperature demonstrations and future model contributions

The public `temperature_models.json` catalog contains five original synthetic
models, seven branches and one original-provenance source. The fixed polynomial
family and separate temperature CLI do not create a ninth composite rule.
Candidate directories also need `temperature_models.json` and
`temperature_locales.json` alongside the other current catalogs.

Keep invented coefficients explicitly `synthetic_demo`, with synthetic material
identity, `author_provenance`, artificial branch ranges, null source-data ranges
and no claimed fit error. Do not relabel a demo as an empirical fit, a source
transcription, a measurement or a real alloy. Its arithmetic fixtures test
software behavior only. See [the exact demo contract](docs/TEMPERATURE_MODELS.md).

Preserve coefficient strings and inclusive branch intervals. Return every
applicable branch at a shared endpoint or throughout an overlap interval;
never choose, smooth, average or extrapolate. Preserve nonmonotonic behavior.
For any future empirical contribution, a reported fit error must remain
separate from measurement uncertainty, confidence or design-safety bounds.
Such data require independent source/provenance and reuse review; public
availability and attribution alone do not authorize copying a compilation.

Localized names and condition presentation live in `temperature_locales.json`.
Keep four-language names and descriptions, material/source/rights snapshots and
condition-evidence statuses consistent with canonical records. Unsupported
metadata, stale snapshots and incomplete language maps must fail validation.
No generic renderer may presume a particular institution, alloy, fit error,
endpoint or model count. Six-decimal plot labels never replace coefficient
strings or canonical arithmetic precision. Generated examples must use only
the current public models.

NIST cryogenic coefficients and derived outputs are omitted conservatively,
not adjudged prohibited. Do not restore them through historical fixtures,
migration examples, screenshots or generated output without a separate review.
Bibliographic references may remain. [Rights boundary](THIRD_PARTY_NOTICES.md)

## Elastic-anisotropy index contracts (v0.11.0)

The two catalog-only `model_relation` families have closed claims-schema 1.8.0
branches and complete development guards. Keep the defining formula, strict
real 3D positive-definite domain, engineering-Voigt/shear conventions, parameter
identity, full-inverse/uniform-SO(3) averaging where applicable, and exact
`index_range` lower inclusion, unbounded upper status and isotropy equality.
Same-family fresh IDs with four labels are supported. Do not turn a definition
into a strength/ductility prediction or an unbounded tensor class into a claim
of material realization. [Scientific guide](docs/ELASTIC_ANISOTROPY.md).

### Repeated developer validation

v0.11.0 memoizes only successful schema meta-validation in a bounded process-local
content-keyed cache under unchanged inspectable validation settings. Schema files
and catalogs are strictly loaded each call; format availability, offline registry,
instance validation, family guards and locale/reference checks are not skipped.
A changed or unsupported checker configuration falls back to normal uncached
meta-validation. This development optimization is not an installed runtime API
or a license/scientific-review assertion.

## Separate computational predictions (v0.12.0)

Candidate directories also include `computational_predictions.json` and
`prediction_locales.json`. A complete supported prediction contract has authored
four-language names, exact source decimal strings, material-cell stoichiometry,
shared method provenance, explicit unknown-state reasons and curated comparison
membership. New IDs in an existing reviewed family are appendable; new physics
needs new schema/guard review. A common unit or matching null values cannot
establish comparison eligibility. Keep reported computational predictions
separate from observations and bounds. See the [prediction guide](docs/COMPUTATIONAL_PREDICTIONS.md).

## Silicon first-instability contributions (v0.13.0)

The prediction schema now has closed alternatives for the existing
`shimanek_v2_pure_alias_12atom_v1` family and the new
`dubois_2006_si_uniaxial_deformation_v1` family. Preserve both complete contracts;
a shared GPa unit never authorizes mixing tensile first-instability strengths
with shear path maxima. Existing Ni source records, shared protocol and default
comparison group remain unchanged.

For the Si family, keep the two-atom primitive cell as directly reported and
label diamond-cubic as an inference. Retain fixed transverse strain, fixed
lattice vectors at each imposed strain, internal atomic relaxation, and the
quantity `tensile_first_instability_strength`. Table II supports the exact
stress and engineering-strain strings; Table III supports the direction-matched
tensile elastic modes. Figure 2(b) is qualitative corroboration only. Do not
promote it to a numerical source, recomputed maximum or stress–strain curve.

Critical engineering strain must retain a separate typed field and separate
table/CSV values, including its percent source unit and dimensionless numeric
meaning. Physical temperature, scalar pressure, magnetic/spin settings and
uncertainty/error fields stay null when unverified. Keep the source's
less-than-approximately 0.05 GPa numerical stress estimate scoped to numerical
controls; do not create an uncertainty or apply the different fully relaxed
protocol's 0.02 GPa criterion to this fixed-lattice family.

New IDs may extend a complete supported family with explicit curated comparison
membership and four-language labels. A new relaxation constraint, stress or
stability definition, cell model, physical-state assignment or error model is
new scientific/schema work. Reject unsupported families and cross-family groups
rather than relaxing the guards. Matching nulls are never proof of comparability.

Retain independent source-transcription fixtures for real records and keep
synthetic appendability cases clearly synthetic. Source PDFs, rendered pages,
figures and full extracted text are audit-only and must not be copied into the
repository or release artifacts. Factual values, attribution, source links and
original paraphrases do not establish a redistribution license or independent
scientific review. See [the full prediction guide](docs/COMPUTATIONAL_PREDICTIONS.md)
and [v0.13.0 migration](docs/MIGRATION_v0.13.0.md).

## Directional Poisson relations (v0.15.0)

Two closed `model_relation` families in claims schema 1.9.0 use
`directional_poissons_ratio` and a dedicated `directional_contract`. Preserve the
entire full-SPD, finite real 3D, full-inverse, orthogonal-unit, uniaxial-stress
contract and engineering-shear conversion. Material-class unboundedness must not
be replaced by fixed-tensor unboundedness, unknown endpoints or attainable
infinity. Pair inequalities remain strict, necessary and insufficient alone for
full stability. Do not reuse isotropic `effective_poissons_ratio` or `index_range`.

Fresh IDs, evidence and sources are supported under either exact rule family.
A paired-relation record has exactly one dependency, resolving by ID to a
same-contract directional definition; ordering in the catalog is irrelevant.
The internal dependency-free metadata guard supplements JSON Schema, and filtered
rendering resolves definition dependencies from the supplied subset and packaged
catalog. It neither inverts a tensor nor executes a formula. Every new record
requires names in all four languages; shared localized conditions and limits
remain mandatory even when key parity would otherwise pass. New contracts
require explicit schema, guard and test review. See
[the scientific guide](docs/DIRECTIONAL_POISSON.md).

When revising the claims schema, refresh the comparison schema's embedded claims
snapshot and exact reference together; run the standard-library metadata preflight
before the complete validation and unit suite. Scientific review, native-speaker
review and permission to redistribute source publications are separate from
software validation. Original project proofs must remain labeled as such.

## Hydrostatic compressibility relations (v0.16.0)

Claims schema 1.10.0 adds two closed `hydrostatic_compressibility_contract`
families. Read [the scientific guide](docs/DIRECTIONAL_COMPRESSIBILITY.md) before
reusing either. Dimensional β, κ and compliance use `inverse_pressure` / `Pa^-1`;
normalized β/κ uses `dimensionless` / `1`. Preserve all finite real full-SPD,
3D stress-free, infinitesimal, fixed-temperature, full-inverse and orthonormal
Cartesian assumptions. Compression-positive p means σ=−pI, not +pI or an
imposed isotropic strain. Hydrostatic stress may induce shear strain.

Keep the full engineering shear audit: order (11,22,33,23,13,12), doubled shear
strain, S_eng,IJ=dI dJ S_ijkl, and for g=S_eng(1,1,1,0,0,0)ᵀ,
(B23,B13,B12)=(g4,g5,g6)/2. The strict same-tensor inequality β²<κ/E is
necessary, not sufficient. Finite attained eigenvalue extrema belong to one
fixed tensor; all finite normalized real values belong to the unrestricted
varying tensor class, even at fixed positive κ. Cubic/isotropic β/κ=1/3 and the
principal-value count must remain explicit. Never substitute “two negative
directions” for “at most two negative principal values.”

Fresh IDs, source records and evidence are allowed under an unchanged complete
family. A normalized record has exactly one dependency resolving to the
hydrostatic-definition family by stable ID; neither the production ID nor list
position is the contract. Parameter order may vary, but scientific field
meanings may not. Runtime reading/rendering and full development validation use
a metadata-only, dependency-free guard; no formula evaluation is introduced.
A new symmetry claim, loading condition, output dimension or range theorem needs
separate scientific/schema review. No ninth executable composite rule is implied.

Record source-specific inspection honestly: Ortiz's relevant published pages
were visually checked; Miller's institutional author-manuscript equations were
checked only as text. New evidence cannot inherit either access assertion without
its own support. The general all-real construction, spectral/trace proof and
strict energy proof are original project derivations, not source theorems or
independent scientific peer review. Retain exact source locators, rights gaps and
pending scientific/native-language review in every language. Never copy inspection
PDFs, page images or extracted source full text into the repository or package.
Use [the migration checklist](docs/MIGRATION_v0.16.0.md) for version/snapshot,
negative-mutation, exact-algebra, appendability and installed-wheel checks.
