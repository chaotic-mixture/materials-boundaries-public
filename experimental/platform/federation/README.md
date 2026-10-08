# Materials database federation: isolated prototype

English-only development deliverable, 2026-10-08. Online database adapters are the direction; offline use and caching are optional. This directory is not installed into or imported by the frozen Materials Boundaries release. It has no path that writes or admits production materials.

## Implemented

- `Provider.search(Query)` returns a bounded page of normalized, pending-review candidates. `federated_search` combines configured providers without merging identities and reports partial provider/authentication failures explicitly.
- Materials Project: explicitly injected, already-authorized official `MPRester` client; uses `materials.summary.search`, advertised fields, `deprecated=False`, `include_gnome=False`, one chunk, 1–25 records. No construction of a client, environment-key discovery, login, key collection or persistent credential configuration occurs here.
- NOMAD: anonymous public-only native API search, selected metadata fields, 1–25 entries, 20-second timeout, 5 MB response cap, no redirects, no automatic pagination/retries. It respects the execution environment’s standard proxy/CA settings; no site authentication is configured. A separate `enrich_archive(candidate)` reads exactly one projected archive for full original structure, density, method and source-declared license. Search and archive are independently traceable snapshots.
- Pydantic v2 contracts, HTTPX transport and mock transport tests. Established `mp-api` and `pymatgen` are declared optional integration dependencies, not reinvented scientific clients. Neither optional dependency was installed or executed for this prototype.
- Optional normalized-result cache, explicit TTL, integrity hashes, adapter/provider-version-aware keys and visible cache-hit status. Cache is local working data, never a redistribution grant or scientific verification.
- Review package and relationship hints. No canonical material assignment, automatic merging, source support upgrade, calculator input, production import or material-count credit.

## Run

Use Python 3.11+ with the dependencies in `pyproject.toml` (tested here with Python 3.12, HTTPX 0.28.1 and Pydantic 2.13.4).

```sh
python -m unittest discover -s tests -v
python -m materials_federation --formula CaFe2Re --limit 1 --enrich-first --output nomad-review.json
```

Install this package normally to include the declared HTTPX SOCKS extra.

The second command performs actual public API reads and requires a permitted network transport. It is never invoked by tests. Authentication-enabled MP execution remains a future secure user step. Do not put keys in arguments, files, fixtures or chat. Construct an authorized official client only in the user's approved credential-handling context, then inject it into `MaterialsProjectAdapter`. Query integration is not proof that such a context exists.

## Identity and evidence rules

A candidate snapshot ID is a hash of provider, provider-record ID, provider version and selected JSON payload hash. It identifies a provider representation, not a new canonical material. A changed projection may produce a new snapshot without a scientific revision; timestamps and hashes must not inflate identity counts.

MP material IDs and NOMAD entry/material IDs retain separate namespaces. A NOMAD entry is a calculation/measurement archive; `results.material.material_id` is retained only as an external reference. MP database references and NOMAD imported-database lineage remain visible. Two matching formulas are only a candidate relationship. No string formula parser or homemade structure matcher is used. Different formula spellings do not prove different compositions. Phase, structure, composition, sample processing and physical state require independent evidence.

Every mapped formula/composition/structure and numerical property records its source path, retrieval time, payload hash, record version, provider version when known, source-declared license, method metadata and task references when verified. MP origin names are preserved; only the documented `structure` origin is linked automatically. Other property-to-task mappings remain unresolved. Source-specific terms and attribution must still be reviewed before redistribution.

MP computed properties remain computed even when `theoretical=false` or the record links to ICSD. MP density is retained in g/cm³, band gap in eV, energies in eV/atom, separate Voigt/Reuss/VRH moduli in GPa. NOMAD native built-in archive quantities retain SI: density kg/m³, structure positions/lattice vectors m. OPTIMADE uses a different unit contract and is not substituted silently. No units are inferred for custom NOMAD schemas. Unknown uncertainty/temperature/pressure remain unknown, not zero.

A partial search structure remains a provider representation, not a validated full structure. No structure matcher runs here. Future pymatgen/ASE conversion must validate lattice, occupancy, coordinates, units and dimensionality first, record tool versions and tolerances, and emit reviewable hints rather than identity merges. Periodic computed structures are not physical specimens. A measured-material relation does not make its computed property experimental.

`review_package` emits `federated_review/0.1.0`, deliberately incompatible with the existing bulk admission package. Its content digest is an audit hash, never an approval token. Candidates always have `canonical_material_id=null`, `review_status=pending_review`, `quota_credit=0`.

## Fixture versus live evidence

- `tests/fixtures/mp_summary.json`: entirely synthetic; numbers are test values, structure is intentionally incomplete. It is not a real Materials Project record. No authenticated MP read was performed.
- `tests/fixtures/nomad_archive_projected.json`: minimized replay of the research worker's actual public NOMAD archive response. Tests label it fixture data even though its underlying values were retrieved live. The original response, query evidence and acquisition manifest are in the sibling NOMAD research directory.
- Unit tests use HTTPX MockTransport, never network.
- The actual HTTPX adapter was exercised against NOMAD once successfully (one bounded search plus one projected archive): one of 73 matching CaFe2Re entries, calculated density 9469.043880966017 kg/m³, and source-declared CC BY 4.0. These are provider entries, not 73 admitted or distinct materials. The live results are in `live_checks/`.
- 19 implementation tests and 12 independent regression tests pass; schema validation and an isolated wheel smoke pass. All 430 frozen source-manifest files remain unchanged.
- See `VERIFICATION.json` for the final exact test count, transport/live-check result and frozen data checks. Do not interpret a fixture test as a working authenticated connection.

## Additive migration plan

1. Keep frozen production commit `753705d22be9f37b6a7deeae734ddd806fe3fb00` and its 1,057 source-qualified identities unchanged. The existing five catalogs and legacy ingestion path remain available. Do not overwrite baseline semantics to satisfy new API-shaped tests.
2. Add an optional federation package/service and English-only search/review UI. Existing runtime functions need no dependency-free guarantee for this new feature. Introduce HTTPX/Pydantic as normal feature dependencies; add mp-api/pymatgen after version-pinned compatibility tests.
3. Keep query results in separate public-source snapshots/candidate storage. Display source, calculation versus experiment, units, unknown conditions, license/reuse status and provider refresh time. Formula search is discovery, never exhaustive material coverage.
4. Resolve candidate identities and scientific contracts through the relationship model in `material-relationships-design`. Map snapshots to external_record nodes; use candidate_matches, represents_structure, reports_prediction/reports_observation, describes_state with reviewable evidence. Canonical identity, state, specimen, observation and prediction remain separate nodes.
5. Add reviewed mappings for well-supported fields first. Existing material references and source-specific bulk admission require valid source/registry/license evidence and trusted review separately. New scientific prediction/measurement families need their own schema contract rather than being forced into unrelated legacy record IDs.
6. Add bounded live compatibility tests with secured MP access only when explicitly available; establish a reproducible dependency lock and API schema baseline. Validate installed wheels and the new feature, then run the unchanged relevant regression suite in a disposable integration checkout.
7. Introduce pagination, incremental refresh, backoff and larger caches only with explicit resource budgets. NOMAD cursors are opaque; preserve them without guessing. MP summary timestamp filtering is not assumed supported. Refresh by documented provider version and explicit records. Large public MP OpenData downloads are not an automatic fallback.
8. Publish only after separate approval, source-specific reuse review and staged integration. This task did not commit, push, deploy or change GitHub.

## Scientific coverage limits

The input audit records metal 14, polymer 14, inorganic 16, natural 1,010 and composite 3, leaving 3,953 across the four unfinished class targets. Federation does not change those counts. MP and NOMAD can substantially improve crystalline/computational discovery; they do not automatically fill manufacturer grades, processed polymers, specimen mechanics, composites or application-role evidence. A bulk modulus is not tensile strength; computed elastic properties are not universal bounds.

## References checked

- [MP SummaryRester](https://materialsproject.github.io/api/_autosummary/mp_api.client.routes.materials.summary.SummaryRester.html)
- [MP SummaryDoc](https://materialsproject.github.io/emmet/_reference/emmet.core.summary.SummaryDoc.html)
- [MP PropertyOrigin](https://materialsproject.github.io/emmet/_reference/emmet.core.material.PropertyOrigin.html)
- [MP EmmetMeta](https://materialsproject.github.io/emmet/_reference/emmet.core.base.EmmetMeta.html)
- [NOMAD API](https://nomad-lab.eu/prod/v1/api/v1/extensions/docs)
- [HTTPX transports](https://www.python-httpx.org/advanced/transports/)
- [Pydantic models](https://pydantic.dev/docs/validation/latest/concepts/models/)

Provider URLs above are supporting references. This package does not bundle external research reports.

## Platform extension boundaries

The prototype is the acquisition/normalization boundary for a broader platform, not that platform's implementation. A future API can serialize `Query` and `SearchPage` contracts; snapshot storage can persist SourceRef and content-addressed provider representations; a review service can consume review packages and produce independently approved identity/evidence mappings. None of those hooks assign DOI/version releases or expose private data automatically. Dataset citation, contribution governance, workflow engines, CIF/ontology conversion, uncertainty-aware mechanics and a web UI require separate contracts and validation. Larger bulk/ML exports must be versioned, licensed and budgeted separately. Background updates remain unimplemented; no recurring acquisition was configured.
