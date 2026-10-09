# Bounded NOMAD candidate ingestion

This standalone, standard-library-only candidate tool extends the experimental
platform at commit `6a7bb7c84fa030d7f1527bd18e8e124bee743960`. It does not
change any package, service, workflow, reviewed seed, frozen baseline or remote
ref. It does not perform automatic admission. All emitted records require an
independent scientific and rights review.

## Identity and counting contract

- A calculation is identified by NOMAD `entry_id`. It is **not** a material.
- Candidate materials are groups of NOMAD `results.material.material_id`, a
  provider structure identity. Different methods/runs inside a group count once.
- Formula is used only for composition consistency and classification. Formula
  alone never establishes identity. Different provider IDs sharing a formula
  remain separate *provider groups*, not proven distinct global materials.
- Every duplicate entry ID is quarantined in full, before provenance binding.
- Inconsistent reduced composition or space group within a group quarantines
  the entire eligible group. Identical IDs already in the seven-record reviewed
  computed seed are excluded. No correspondence with legacy experimental,
  supplier-qualified, natural-material or other-provider identities is claimed.
- Provider identity grouping is version-dependent and can conflate physically
  meaningful states. Structural equivalence across provider IDs is unverified.
  Therefore global unique-material coverage is explicitly null, admitted count
  is zero, and no candidate counts toward the five-category >=1,000 goal yet.
- `metal` is a proposed category for all-metal elemental composition, not a
  measured assertion of metallic behavior. Other carbon-free bulk structures
  are inorganic candidates. Carbon-bearing entries are held for taxonomy review;
  this conservative rule omits valid carbides and does not classify polymers.

## Property interpretation and rights

Each passing group contains one finite positive provider-reported density in
kg/m^3 from `results.properties.structures.structure_original.mass_density`.
It is computed cell density for the provider's original structure representation,
not an experimental bulk density. `original` does not establish initial versus
relaxed geometry. Temperature, pressure, stability, convergence, ground state,
experimental existence, mechanical properties and isotope-resolved mass are
unverified. Records retain DFT code/method, source processing version/commit/time,
source ID, named authors, references, exact query, retrieval time and hashes.

Only entries explicitly reporting OQMD origin and `CC BY 4.0` pass the rights
gate. Unknown or different rights are quarantined. The scope is scalar density,
method and attribution metadata; **no geometry, atomic positions, lattice
vectors, raw VASP files or POTCAR is requested or redistributed**. ICSD-derived
source paths may occur. This does not grant upstream ICSD structural rights.
The metadata packet must not be used to infer geometry redistribution rights.
Source numerical values are unchanged; selection, unit labels, category
proposals and normalization are our changes. Preserve authors, references,
source URLs and the CC BY 4.0 link with any later approved distribution.

## Reproduce

From this directory, Python 3.11+:

```sh
python -m unittest -v
python nomad_batch.py collect /absolute/fresh/evidence --pages 10
python nomad_batch.py normalize /absolute/fresh/evidence candidates.json \
  --seed ../examples/reviewed-computed-seed/scoped-review-input.json
```

The network command reads only the official public NOMAD API, with no account,
credentials or paid service. Maximum 10 pages x 100 archive entries; maximum
32 HTTP attempts, 30 MB total response bytes, 3 MB per response, 90-second timeout
and 1-second inter-request pause. A source error stops the run and is recorded.
Use a fresh directory; an existing acquisition is never overwritten. Pass
`--after ENTRY_ID` to continue a later bounded window using the final archive
response cursor; then review cross-batch identity overlaps before admission. The optional
`repair-attribution EVIDENCE` command re-fetches only IDs lacking named authors,
within the same budget. It exists because an initial `authors` projection yielded
empty objects; the current collector requests `authors.*` directly. Acquisition
logs preserve those initial requests and their corrected responses transparently.

The live dataset is mutable and not a transactional snapshot. A future collection
may differ. Offline normalization of the archived bytes is deterministic; it
checks every response hash first. Sorted `entry_id` pagination is bounded and
not representative sampling. The selected observation is the first *eligible*
entry in this acquired sample, not the provider's globally first entry or the
lowest-energy calculation. Exclusion counts partition acquired entry rows;
repeated calculations are excluded rows, not additional materials.

## Primary references

- NOMAD REST API: https://docs.nomad-lab.eu/develop/howto/manage/program/api.html
- NOMAD terms, metadata/content distinction and attribution:
  https://nomad-lab.eu/nomad-lab/terms.html
- CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
- NOMAD pagination and rate limits: https://nomad-lab.eu/nomad-lab/faqs.html
- MatID symmetry/material IDs:
  https://fairmat-nfdi.github.io/matid/docs/learn/symmetry-analysis/
- NOMAD schema (`mass_density` unit declaration):
  https://raw.githubusercontent.com/nomad-coe/nomad/develop/nomad/datamodel/results.py

The current schema is corroborating unit documentation, not a reimplementation
of the older per-record processing commit. No DFT is rerun. No exact numerical
recomputation is possible from this geometry-free projection; that limitation
must remain visible in review.
