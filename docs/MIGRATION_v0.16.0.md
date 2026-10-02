# Migration to v0.16.0

**0.16.0 is the first public release**, retaining the version of an unpublished
development snapshot. Earlier versioned notes describe development history,
not prior public releases. The public repository is
[chaotic-mixture/materials-boundaries-public](https://github.com/chaotic-mixture/materials-boundaries-public).

The release contains **34 mechanics claims, 47 source records, 2 observations,
5 synthetic temperature demos / 7 branches, and 6 computational predictions**.
The exact eight executable composite claim/rule pairs retain their numerical
behavior. Two catalog-only hydrostatic-compressibility relations remain part
of the scientific catalog, as described below.

## Public release and temperature transition

- Original project code, documentation, synthetic data and original curation
  use [MIT](../LICENSE), under maintainer handle chaotic-mixture. Source works
  and scientific facts are not relicensed; see [third-party notices](../THIRD_PARTY_NOTICES.md)
- All five NIST cryogenic coefficient datasets, their historical coefficient
  fixtures and every derived sample/plot are omitted conservatively pending
  clarification. This is not a finding of prohibited redistribution
- The 46 bibliographic/source identities remain; one original synthetic
  provenance record, `materials_boundaries_synthetic_temperature_demo`, makes 47
- Five openly authored synthetic demos exercise linear, quadratic, quartic,
  shared-endpoint and interval-overlap behavior. Artificial coefficients and
  ranges are not material measurements, source fits or engineering allowables
- Use `synthetic_*_temperature` model IDs and current `synthetic-*.json` inputs.
  Removed real-material IDs are not silently aliased to synthetic models
- Regenerate temperature result/plot bundles. Their models, provenance,
  classifications and result IDs intentionally differ from development output
- Other scientific datasets, including graphene observations and Ni/Si
  computational predictions, retain their numerical facts, attribution and
  source-specific caveats. The NIST decision does not remove unrelated facts

See [the exact synthetic model contract and commands](TEMPERATURE_MODELS.md).
No third-party PDF, figure, full text or raw measurement collection is bundled.

## New claims and units

- `directional_linear_compressibility_hydrostatic_relation` defines
  β(n)=nn:S:I and κ=I:S:I>0 under σ=−pI, with positive compressive p. Every
  orthonormal triad sums to κ. For a fixed finite tensor, B=S:I has finite
  attained eigenvalue extrema; at most two principal values can be negative
- `normalized_directional_compressibility_range` defines r=β/κ. Across
  unrestricted finite full-SPD 3D tensors, every finite real r is attainable,
  even at any prescribed positive κ. Each fixed tensor still has a finite
  attained directional range. β²<κ/E(n) is strict, necessary and not sufficient
  for full SPD, using the same S and n. Cubic and isotropic r is exactly 1/3

Both are `model_relation`, `direction: relation`, `bound_kind: null` and
`evaluation_support: catalog_only`. The dimensional quantity is
`directional_linear_compressibility`, with the new canonical pair
`inverse_pressure` / `Pa^-1`; the normalized quantity is
`normalized_directional_linear_compressibility`, `dimensionless` / `1`.
Dimensional β, κ and compliance parameters cannot use Pa or `1`. No tensor-input,
inversion, eigenvalue, extremum-search, material-prediction or plotting API is added.

## Closed scientific metadata contract

The new `hydrostatic_compressibility_contract` has separate closed families for
(1) definition, trace and fixed-tensor range, and (2) normalized tensor-class range
and the necessary energy inequality. It preserves the source-research structure,
engineering-convention audit, original-derivation status, explicit scope exclusions
and source attribution. Definitions supported by inspected sources are separate
from the original project proofs. No permissive relabeling of Poisson or anisotropy
metadata is used.

A dependency-free metadata guard is called when reading and rendering these
records and by development validation. It checks scientific structure and finite
JSON without computing tensors or interpreting formula strings. Scientific fields
remain fixed by family; parameter order may vary. Fresh claim/source IDs and
properly recorded evidence are supported. A normalized-family record has exactly
one dependency, which must resolve by stable ID to a hydrostatic-definition family
record; it is not pinned to one production ID or catalog ordering. Full validation
also checks references, authored four-language labels and the exact executable
registry. These checks establish metadata consistency, not scientific peer review.

Full finite real 3D SPD, minor/major symmetries, full inverse compliance,
orthonormal Cartesian directions, stress-free infinitesimal response, fixed
temperature and hydrostatic stress are mandatory. Engineering Voigt uses
(11,22,33,23,13,12), with doubled shear strains: for g=S_eng(1,1,1,0,0,0)ᵀ,
(B23,B13,B12)=(g4,g5,g6)/2. Fixed-tensor endpoints must be finite and attained;
class-wide unboundedness must not become unknown endpoints or attained infinity.
The principal-value count must not become a count of arbitrary negative directions.

## Versions and compatibility

- Software/package/engine version: 0.16.0; claims schema: 1.10.0
- The comparison schema's embedded claims snapshot and exact claims-schema
  reference advance together to 1.10.0; its numerical contract is unchanged
- Other scientific schema versions remain unchanged. Regenerate comparison
  bundles carrying an earlier claims snapshot before current-version validation
- Engine labels and result identifiers derived from those labels follow the new
  software version; this is not a numerical model change
- Catalog formulas remain non-executable. The existing directional-Poisson,
  anisotropy, isotropic/composite, fatigue, temperature and prediction contracts
  remain distinct, including the earlier cubic-Poisson unboundedness result
- Authored en/zh/ja/de names and scientific caveats accompany the new records;
  canonical IDs, formulas, quantities, units and JSON remain language-independent

Non-temperature historical scientific fixtures retain their meaning; excluded
temperature fixtures are replaced by clearly labeled synthetic tests. Release
acceptance includes metadata preflight, complete catalog validation, the full test
suite, exact synthetic algebra and mutation checks, fresh-ID appendability,
isolated installed-wheel smoke, and four-language catalog rendering. A requested
or listed check is not a claim that it passed; consult the release validation
report for actual outcomes.

```sh
python -m unittest discover -s tests -p test_release_metadata.py -v
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
python -m materials_boundaries catalog claims --query compressibility --text --lang en
python -m materials_boundaries catalog claims --id normalized_directional_compressibility_range --text --lang zh
python -m materials_boundaries catalog claims --id directional_linear_compressibility_hydrostatic_relation --text --lang ja
python -m materials_boundaries catalog sources --id miller_evans_marmier_2015_linear_compressibility --text --lang de
```

## Evidence, scope and rights

Ortiz et al. (2012) published equation pages were visually checked: printed
195502-2 Eqs. (2)–(3), plus printed 195502-4 for cubic β and the local-elastic
caveat. Miller et al. (2015) institutional author-manuscript p. 4 Eqs. (1)–(2)
were checked as text only, with canonical metadata corroborated through Crossref.
The attempted page-image check failed and direct download returned HTTP 403;
no visual verification or published-pagination equivalence is claimed.

The full-SPD construction at fixed positive κ, trace/spectral consequences and
strict Cauchy–Schwarz proof are original project derivations. Neither source is
credited with an inspected universal normalized-range theorem. Algebra checks,
software tests and machine-assisted translations are not independent scientific
or native-language review; these review statuses remain unperformed.

The full exclusions are in [the scientific guide](DIRECTIONAL_COMPRESSIBILITY.md).
In particular, NLC is not negative volume compressibility, thermal expansion or
auxeticity; neither full homogeneous SPD nor the necessary energy inequality
certifies complete material stability or realizability. Only bibliographic facts,
mathematical formulas and original notes are bundled. No source PDF, page image,
figure or extracted full text enters the repository or release package. The MIT
license covers original project work only. NIST's current curated-collection
status, former SRD 152 identity and unverified express redistribution grant are
recorded in [the third-party notices](../THIRD_PARTY_NOTICES.md); coefficients and
derived outputs are omitted without claiming they are prohibited.
