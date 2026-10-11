# Readiness of a held formal-candidate subset

The existing second tranche contains **62 historically accepted, scoped computed
metadata examples: 47 metal-family and 15 inorganic records**. Its exact input,
normalized review and acceptance pin remain unchanged. This note reuses that
historical review to prioritize preparation of a small **held** formal-candidate
subset. It is neither a replacement acceptance record nor a formal admission.

Formal project admissions remain **1081 = 1057 legacy identities + 24 reviewed
computed composition buckets**, with **zero admission delta** from this work:

| Formal category | Current admissions |
| --- | ---: |
| Metal | 26 |
| Polymer | 14 |
| Inorganic | 28 |
| Natural | 1010 |
| Composite | 3 |

All 62 examples remain outside the formal catalog. The separate `CaEr2Eu`
candidate remains held. Provider groups, calculation counts and proposed subsets
do not increase any formal category count or satisfy the five-category coverage
goal.

## What the existing acceptance establishes

The repository contains a content-bound acceptance decision,
`accepted_exact_scoped_metadata_only`, for this derivative and the source
snapshot reviewed on 2026-10-09. The normalized review preserves named source
authors, source URLs and processing provenance, exact scalar density, method,
related-group metadata, declared license, modification notices and explicit
unknowns. Its rationale explicitly excludes persistent catalog admission; the
acceptance pin records `persistent_admissions: 0`.

The following byte hashes were checked against the files and the acceptance pin
during this local review:

| Artifact | SHA-256 |
| --- | --- |
| `eligible-metadata-input.json` | `41d0691a8289c6d30fc24a5ecaef1f3b3e4b3ded57eac15ea8d64adc8a8398d6` |
| `normalized-review.json` | `f47b5612797661aae68f5d360aeee85c7b6eb3945dad4aeb210b65933bfcc279` |
| Canonical normalized review | `318f12f676ff2db9d2429fa1cfb937cb08d9fa89292dff2a46be87171e113115` |
| `acceptance-pin.json` | `47d21e9237a62ce4b2eda806cd2163b7d7bc576f1577deff623caf5e54efd543` |

All 62 records retain input-to-review equality for provider IDs, source formula,
method, provenance, attribution, source URL, source evidence hashes, check results
and overlap relations. This is a transcription and artifact-identity check. It
does not mean the historical geometry diagnostics or upstream source comparisons
were recomputed in this audit.

The prior metadata acceptance remains usable evidence for preparing a held
subset. Intentionally unpublished raw geometry is not, by itself, a defect or a
reason to invalidate that acceptance; the formal 24-record tranche also follows
a scoped metadata pattern. Do not rewrite the historical 62-record pin to imply
that this new review repeated the original scientific work.

## A minimal two-record review priority

`AlGa2Sc` and `O8Re2Ru4` are a compact starting point for a subsequent release
review. They span metal-family and inorganic categories, each has one preserved
provider group with two related calculations, and they reference the same frozen
source and attribution snapshots. That reduces the evidence needed for a focused
follow-up without inventing new identities or discarding related calculations.
Neither has an ICSD token in its preserved related mainfile paths; this is a
limited path observation, not proof of unrestricted rights or exhaustive lineage.

| Field | Metal-family priority | Inorganic priority |
| --- | --- | --- |
| Original source formula | `AlGa2Sc` | `O8Re2Ru4` |
| Reduced composition | `AlGa2Sc` | `O4ReRu2` |
| Review record pointer | `/records/4` | `/records/60` |
| Candidate ID | `nomad_computed_79d7f2436fdc66a5` | `nomad_computed_a7cbfee72baf6866` |
| Selected NOMAD entry ID | `-5LW53UJmjl7Yx6ZVYqax21coPqa` | `-4u4Uiq7DNzbzFH3yAJiOnsOGQ5F` |
| Provider material ID | `t1m1ZKOG0OhN-VM7zE63EuwCfj6A` | `ALB2r8sh6dNKM8oAC5R4cTuZP4JJ` |
| Related second entry ID | `wKFzeqc8RZvN4tjYVFUXPsqKUll3` | `1gJU1C1E7aVysjDAWVVjzEhzOIlL` |
| Reported density, kg/m^3 | `4891.042649446121` | `9258.190380098826` |
| Provider-reported space group | `225` | `227` |
| Selected source mainfile | `oqmd/heusler/Ga/Al_Sc/standard/OUTCAR` | `oqmd/spinel/O/Re_Ru/static/vasprun.xml` |

The density values are copied from the existing accepted metadata at
`results.properties.structures.structure_original.mass_density`; they are
computed cell densities, not experimental bulk-property measurements. Preserve
the original `O8Re2Ru4` formula even though the count bucket is
`computed-composition:O4ReRu2`. Metal-family membership is compositional;
electronic behavior remains unknown. Temperature and pressure remain null, and
experimental existence, stability, equilibrium and convergence remain unknown.

Exact selected-record canonical SHA-256 values are:

- `AlGa2Sc`: `70189c104e4dfb57d561623fee7930fb6277799e7ade35afaffc41b0c7c57adf`.
- `O8Re2Ru4`: `eb14fd8ff979b157e979618945997940b03876ed1cc4ba3ac651d43ccff1ee19`.

The two records contain the following shared evidence references. These values
were verified against both records; the underlying source-response bytes were
not located and rehashed during this audit:

| Evidence field | Recorded SHA-256 |
| --- | --- |
| `candidate_packet_sha256` | `d3bd3467da146e8a555c77c43b7fe9c3bd3af0b7aea9a003b937687569b7b8b0` |
| `archive_response_sha256` | `eb837352e3f75508f68ca0251977b62a6be2b4009c14f2b0e116929a7876a330` |
| `relations_response_sha256` | `bca8618f56386d8b2b4713a37fa69ebb3e58c463b5732c2037afdeef15904be4` |
| `frozen_source_response_sha256` | `1bf524fa3bae5d2f94163469c9dac6a59286f191779c21d01a910d1474b096ab` |
| `attribution_response_sha256` | `6f979597ac76a0fe0de552e425dc67a3e16658be79aab10935d5ddec1e10d3de` |

This is a review priority, not evidence that these two records have a stronger
license grant than the other 60 or are ready for immediate formal admission.

## Reuse evidence available to this audit

All 62 records preserve an OQMD origin and provider-reported `CC BY 4.0`, named
authors, source references, a license URL and the same scoped rights/modification
notice. Common wording is appropriate to a common-source tranche and is not
itself a defect. The accepted derivative extends the preparation input's
scalar/method wording to identity/prototype descriptors, attribution and provenance
metadata, while continuing to exclude geometry and raw calculation assets.
The historical pin binds that derivative's exact bytes.

The retained reviewer field is a descriptive label, and the local pin does not
authenticate that reviewer or document their authority and conflict-of-interest
status. Source-license-match booleans and response hashes preserve historical
assertions and bindings, but are not independent authentication by this audit.
The inspected local artifacts did not include a separate identified reuse-review
receipt or the referenced original source/terms snapshots. That limits what this
audit can independently verify; it does not prove that such evidence never
existed or invalidate the historical scoped acceptance.

The preserved CC BY rights statement is scoped to selected metadata and scalar density only.
It does not grant upstream ICSD geometry rights, nor authorize redistribution of
cell vectors, coordinates, raw archives, calculation files or potentials. No raw
structure asset is included in this preparation. Source/publication references
and a generic license URL are not a new legal ownership determination. This note
makes no independent legal clearance claim.

## Remaining artifacts before a new formal release

The existing review can be reused; a new release still needs a decision for the
exact subset under the current formal policy. Prepare or locate:

- A separate held subset artifact and selection manifest binding the chosen IDs,
  exact parent input/review/pin hashes, related calculation IDs, original source
  formula/property values, attribution, rights notices and unknowns. Keep the
  original 62-record artifacts unchanged.
- A reference to the original independent scientific and scoped reuse review,
  with the release operator's verification of reviewer identity, independence,
  authority and applicability to the exact subset. If those existing records
  cannot be verified, obtain an explicit subset review rather than filling in
  acceptance or confidence fields to satisfy a schema.
- Available source/relation/attribution and license/terms evidence or review
  receipts bound to the recorded snapshot and metadata scope. Keep private
  evidence private; publication of raw geometry is not required by this note.
- An explicit review of selected-group identity, source semantics, attribution,
  modification notices and the access/retention/derived-export/redistribution
  scope. Preserve unresolved physical equivalence and conditions.
- A separately authorized, reviewed formal release decision, applicable count
  policy and new exact pins, followed by the required source/installed artifact
  verification. An experimental acceptance pin cannot update formal counts.

The selected-group consistency checks in `computed_schema_v2.py` now require the
record's provider-reported space group to occur in the selected group's
`space_groups`, and its source mainfile to occur in that group's `mainfiles`.
These are local software consistency checks. They do not independently determine
symmetry, validate an upstream mainfile, repeat scientific review or clear reuse
rights. Actual test results are recorded separately; this note does not treat a
new assertion or passing schema as scientific reapproval.

See [the existing tranche record](README.md),
[the computed-v2 trust contract](../../COMPUTED_V2.md),
[experimental contribution rules](../../CONTRIBUTING.md),
[data contribution/reviewer requirements](../../lifecycle/CONTRIBUTING_DATA.md)
and [formal admission policy](../../../../docs/FORMAL_PROJECT_CATALOG.md).
The local audit receipt is
`incremental-evidence/independent-unadmitted62-reuse-audit.json` outside the
repository. This preparation used existing local evidence only, with no fresh
source request, Library operation, DOI registration or public deployment.
