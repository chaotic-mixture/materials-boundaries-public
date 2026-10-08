# Opt-in validated local catalog

Query service and umbrella platform are experimental prerelease 0.2.0.dev0. Unchanged federation/lifecycle remain 0.1.0. Health and OpenAPI report the prerelease; existing provider response schema IDs remain 0.1.0 because those wire contracts are unchanged.

This isolated experimental revision adds installed-core reads. It does not change the production core, source data, validators, existing external provider behavior, or CI. The default `materials_query.app:app` remains provider-only; catalog endpoints respond with an explicit disabled state. No dependency on a package-index distribution named `materials-boundaries` is added, downloaded or automatically installed.

## Local installation and startup

Use a trusted checkout of this repository (https://github.com/chaotic-mixture/materials-boundaries-public), not an unrelated package-index name. Start in its repository root, with Python 3.11+, a virtual environment and setuptools >=68 already available. Install the repository core from that local path:

```sh
python -m pip install --no-index --no-deps --no-build-isolation .
cd experimental/platform
python -m pip install -c requirements-lock.txt ./federation ./query-service ./lifecycle .
python -m uvicorn materials_query.app:create_catalog_app --factory --host 127.0.0.1 --port 8765
```

For this scratch revision, use its `platform` directory instead of `experimental/platform` after installing the core from the trusted repository root. Core installation uses local source only; the other platform dependencies use the configured package index. Do not run installation directly inside a read-only source freeze: copy the verified checkout to a writable build directory first. No credentials are needed.

Open http://127.0.0.1:8765/catalog. If core is absent, the opt-in factory remains usable for provider discovery and reports `core_not_installed`. If imports, resource fingerprinting, reading, source-loader checks or full graph validation fail, it reports `core_initialization_failed`. No partial snapshot is served. Inspect/fix the local installation and restart; HTTP never takes source file paths. Initialization failure details and filesystem paths are not reflected to clients.

One captured snapshot is fully validated per opted-in app construction. Multiple worker processes independently pay that cost; do not infer one global shared validation/cache. Startup includes strict parsing, PA12 and PAHT loader preservation validators, unchanged full material graph validation, full content hashing, package/runtime fingerprinting, freezing and indexing. The snapshot implementation is byte-for-byte the independently reviewed prototype, SHA-256 `75f63efb42f419eeae0fd08db63369350d603c52f01c4149915f048d74d6cc12`.

## Pinned read-only API

`GET /api/catalog/status` returns availability, content and runtime digests, the version pin, bounds, and three distinct counts. `local_catalog_unique_material_count` counts validated identity IDs, while material-state and property counts are separate. It is never combined with NOMAD/MP entry counts and does not imply external discovery admission or quota credit.

All POST reads require the exact 64-character version from status. Stale selections return 409. Results repeat that version and both digests. Missing records return 404; invalid bounded search semantics return 400; invalid schema or extra fields return 422; disabled catalog reads return 503; over two concurrent local operations return 429. Existing cross-origin and 32 KiB body limits apply. No HTTP refresh, mutation, path input, upload or source-selection endpoint exists.

- `/api/catalog/exact`: `version`, `kind` (`materials` or `reference-properties`), `record_id`; canonical catalog subset, preserving existing exact-query output shape.
- `/api/catalog/record`: `version`, `kind` (`identities`, `grades`, `materials`, `reference-properties`, `sources`), `record_id`; one detached record.
- `/api/catalog/resolve`: `version`, `state_id`; exact source-complete identity, grade, state, linked properties and original source ordering.
- `/api/catalog/search`: `version`, `kind` (default `materials`), `query`, `limit` (default 20, maximum 100); literal casefolded AND substring matching, maximum 256 characters and 16 terms, packaged record order, truncation flag. Internal search remains O(N).

Search indexes state ID/name/English name, identity ID/name/English name/category, source designation, grade ID/designation, and linked property ID/state ID/quantity/source ID/source property label/evidence kind/reporting basis. It does not cover aliases, non-English authored names, arbitrary descriptions or all CLI filters. Neither term matching nor existing graph validity establishes scientific suitability or substitutes for a source-ledger/release audit.

The pin is historical captured content, not filesystem freshness. Reads do not revalidate or reread sources. Restart explicitly to build a new fully validated pin. Multi-file capture requires a coherent quiescent installation and is not atomic against file replacement. Runtime fingerprinting covers package Python/JSON resources plus the snapshot module; it is not a signature, factual certification, or full OS/environment fingerprint. Changing core code requires restart.

## UI and verification limits

The separate English catalog page shows its version and local counts, performs bounded search, and selects exact source-complete material states or property subsets. It uses text-only DOM assignment for server data and blocks submit until status is enabled. Provider discovery stays on its existing page with unchanged provider paths, disabled live MP behavior and separate fixture demo.

API tests and static JavaScript syntax/safety assertions have been run. Real browser rendering, accessibility, click/download behavior and responsive layout remain unverified because browser execution is blocked. Do not call this a browser pass or a deployed web performance benchmark.

The extra `query-service/catalog-tests/test_local_catalog.py` suite runs when this repository core is importable; it skips as a module when the optional core is absent. Run it separately with `python -m unittest discover -s query-service/catalog-tests -v`. The original four suites remain 83 tests with zero skips and retain their prior behavior; existing CI does not yet run the optional suite. Review artifacts outside the package include exhaustive snapshot parity replay, fresh-process loopback HTTP measurements, installed-wheel checks, exact source manifests and the isolated diff. No production acceptance, deployment, source mutation, GitHub update or CI activation is part of this revision.
