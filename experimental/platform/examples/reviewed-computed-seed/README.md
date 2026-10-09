# Optional reviewed computed-metadata seed

Seven independently reviewed new NOMAD acquisitions, not restoration of lost historical records. This optional seed preserves provider-reported computed cell mass density, formula, method, entry/material IDs, source links, attribution, license/change notice and scientific caveats. It excludes geometry, raw archives/calculation assets and SQLite runtime state. The default API remains computed-disabled with zero added records.

Review input SHA-256: `298e94d77f5166650f66c17ff83e859c6e654f6739745d779a4461310437bb33`.

The pin is an independent identity check, not a cryptographic reviewer signature. The original geometry/phase/stability/experimental claims remain excluded. Twelve AFLOW records are not included. Seven distinct source-qualified project IDs coexist with 1,057 unchanged legacy identities; 1,064 is not a scientifically deduplicated cross-namespace total.

## Reproduce locally

Install the repository core and experimental packages with the locked dependencies according to the platform instructions. From the repository root, run the following only in a local working directory. It creates a new local registry in `computed-seed-local/` and prints a fully version-pinned read-only export. Repeating admission against the same unchanged review is idempotent.

```python
import json
from pathlib import Path
from hashlib import sha256
from materials_query.computed_registry import ComputedRegistry
from materials_query.app import create_app
from fastapi.testclient import TestClient

seed = Path('experimental/platform/examples/reviewed-computed-seed/scoped-review-input.json')
trusted = '298e94d77f5166650f66c17ff83e859c6e654f6739745d779a4461310437bb33'
raw = seed.read_bytes()
assert sha256(raw).hexdigest() == trusted
review = json.loads(raw)
output = Path('computed-seed-local')
output.mkdir(exist_ok=True)
registry = ComputedRegistry(output / 'registry.sqlite3', review, trusted_review_sha256=trusted)
registry.admit([record['candidate_id'] for record in review['records']])
client = TestClient(create_app(computed_registry=registry))
status = client.get('/api/computed/status').json()
pin = {'namespace': 'computed', **{key: status[key] for key in
       ('baseline_version', 'overlay_version', 'review_version')}}
response = client.post('/api/computed/export', json=pin)
response.raise_for_status()
(output / 'normalized-export.json').write_bytes(response.content)
print(json.dumps(status, indent=2))
first = review['records'][0]
response = client.post('/api/computed/property', json=pin | {
    'project_material_id': first['project_material_id'], 'property': 'density'})
response.raise_for_status()
print(json.dumps(response.json(), indent=2))
```

HTTP routes are read-only: list/search/exact/property/source/export require explicit namespace and baseline/overlay/review pins. Local admission is deliberately separate from HTTP. Never publish runtime directories, raw evidence or acquired geometry. Production deployment is outside this example.
