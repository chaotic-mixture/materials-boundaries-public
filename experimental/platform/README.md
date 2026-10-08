# Experimental Materials Platform

An English-only, local experimental addition. The frozen 1,057-identity catalog, production code, version and CI are unchanged. This is not a dataset publication or a production platform.

## Quickstart

From this directory, Python 3.11+:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -c requirements-lock.txt ./federation ./query-service ./lifecycle .
materials-platform --output demo-store
python -m uvicorn materials_query.app:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765. Bind only to loopback: no authenticated accounts or multiuser hardening exist. Use a new output directory for each demo. Offline fixture execution requires no key and makes no network requests. Package installation requires a configured package index. Direct runtime versions are constrained; the provided lock records the verified dependency environment, not a cross-platform hash-locked supply-chain guarantee.

## One linked demo

The original synthetic NOMAD-shaped golden fixture is captured byte-for-byte. The federation adapter creates a typed candidate including property-level provenance, native structure/units, source identity and a pending-review state. A content-addressed binding links its digest to the raw response digest and the lifecycle staging record. The explicit demo review binds that binding digest in its rationale; immutable release metadata binds the exact review digest. The demo only approves a synthetic source envelope for a local demo. The typed candidate remains pending and no scientific property is admitted. Automatic canonical-material admission and quota credit remain zero.

The adapter hashes ordinary JSON values; lifecycle preserves numeric lexical strings. Their parsed-payload hashes can differ truthfully. The binding records both and joins them by exact captured response bytes and provider record ID. It never equates them or converts units.

IMPORTANT: dataset.tar omits raw blobs, typed candidates and the binding sidecar. It is not a self-contained raw replay archive or DOI-ready deposit. Keep the complete demo store. demo-summary.json lists relative logical replay objects; the acquisition manifest lists raw hashes. Future licensed raw-bundle export is not implemented. Never publish an actual provider store without specific rights review.

## Layout and interfaces

- federation/: one shared typed adapter implementation. NOMAD bounded public search/archive mapping; Materials Project official-client adapter with synthetic tests only. No MP credential configured or live verification.
- query-service/: FastAPI and local English web UI using the shared adapter dependency. Health, capabilities, search, bounded batch, separate fixture demo, record JSON export and OpenAPI. See its README for exact limits and failure statuses.
- lifecycle/: standalone standard-library capture, content-addressed cache/stage, exact-subset local review, immutable versioned release and correction-event CLI.
- materials_platform/: offline end-to-end integration entrypoint and synthetic golden fixture.
- relationships/: proposed typed graph schemas and examples, not an installed graph database or production identity mapping.
- tests/: integration and independent regression checks.

API batch export preserves full result envelopes for downstream ML consumption. It does not provide features, model training, uncertainty calibration, unit harmonization or train/test splitting. Experimental measurements and reference-provider scientific mappings are not complete. Formula equality is never identity equivalence.

## Tests

```sh
python -m pip install PyYAML
python -m unittest discover -s federation/tests -v
python -m unittest discover -s query-service/tests -v
python -m unittest discover -s lifecycle/tests -v
python -m unittest discover -s tests -v
python -m pip check
```

Independent component review passed for bounded local scope. Final integrated test evidence is summarized in VERIFICATION.md. Real browser rendering, accessibility, download behavior and mobile overflow remain unverified due to browser execution restrictions. API/static/JavaScript logic checks are not a browser pass. NOMAD live evidence is separate from fixtures; no MP live claim, deployment, DOI, public upload or workflow activation is made.

Lifecycle reviewer authentication and production regression gates remain not_run. Source-envelope mapping is not scientific property normalization. Correction reopening, release-parent lineage, automatic semantic-version eligibility and reference-provider admission remain future work. See SNAPSHOT_POLICY.md, CONTRIBUTING.md and THIRD_PARTY_NOTICES.md.
