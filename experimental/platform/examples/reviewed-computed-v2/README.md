# Independently reviewed, composition-scoped metadata example

This separate opt-in v2 tranche contains 24 hypothetical model records: 12
compositional metal-family and 12 inorganic oxide models. There are 24 accepted
composition-count buckets, 24 selected provider models/entries, 30 related
provider groups and 118 related calculations. The latter are provenance counts,
not additional admitted materials. Six same-composition relations remain
unresolved. No global unique-material total is asserted.

`eligible-metadata-input.json` is the exact metadata-only scientific eligibility
input, not a source archive. `normalized-review.json` is its strict v2 normalized
review. `acceptance-pin.json` independently pins both exact byte streams and the
canonical normalized review, with the verified implementation-source hashes.
The review text retains its original preparation-stage wording; this separate
acceptance pin records the subsequent independent normalized-artifact approval.
Hashes prove bytes, not reviewer authentication or upstream ownership.

Preserved information includes exact source formulas and density, structured
method, named authors and references, original modification notices, license
URLs, prototype, provider-reported symmetry, null/unknown physical conditions,
confidence, diagnostic scalars, evidence hashes and bounded overlap relations.
The normalized rights scope explicitly covers bounded identity/provenance
metadata, scalar density and method. The added project-change notice describes
composition reduction, count bucketing and overlap annotation. This does not
license ICSD geometry. No positions, cell vectors, geometry archives, raw
calculation or potential files are included.

A local-only example (requires an exact installed legacy core baseline):

```python
from pathlib import Path
import json
from materials_query.computed_registry import ComputedRegistry

example = Path('experimental/platform/examples/reviewed-computed-v2')
review = json.loads((example / 'normalized-review.json').read_text())
pin = json.loads((example / 'acceptance-pin.json').read_text())
registry = ComputedRegistry(
    'new-explicit-v2-local.sqlite', review,
    trusted_review_sha256=pin['canonical_review_sha256'],
    input_file_bytes=(example / 'eligible-metadata-input.json').read_bytes(),
)
result = registry.admit([record['candidate_id'] for record in review['records']])
assert result['scoped_accepted_identity_bucket_count'] == 24
```

Use a new database, never the previous v1 registry. Nothing enables this example
by default. Explicitly supplying the registry to `create_app` captures a read-only
process-pinned API snapshot. The legacy 1057 identities and the prior seven-record
tranche remain unchanged and separate. See `../../COMPUTED_V2.md` for the full
contract and limitations. Repository tests use only disposable local databases.
