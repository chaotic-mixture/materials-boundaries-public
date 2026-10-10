# Second independently reviewed, metadata-only computed tranche

This separate, explicit opt-in example contains 62 hypothetical computed models:
47 compositionally metal-family and 15 inorganic records. It preserves 62 reduced
composition-count buckets, 133 related provider groups and 444 related calculations.
Twenty-two compositions have multiple related groups. These are scoped counts,
not evidence of 62 experimentally existing materials or a universal unique total.
Electronic behavior, physical conditions, stability, equilibrium and convergence
remain unknown. Prototype and symmetry are provider-reported, not independently
reconstructed. Eight unreduced source formulas remain unchanged.

## Exact reviewed artifacts

- `eligible-metadata-input.json`: exact metadata-only eligibility input, SHA-256
  `41d0691a8289c6d30fc24a5ecaef1f3b3e4b3ded57eac15ea8d64adc8a8398d6`.
- `normalized-review.json`: exact independently accepted derivative, file SHA-256
  `f47b5612797661aae68f5d360aeee85c7b6eb3945dad4aeb210b65933bfcc279`;
  canonical review SHA-256
  `318f12f676ff2db9d2429fa1cfb937cb08d9fa89292dff2a46be87171e113115`.
- `acceptance-pin.json`: the unchanged independent scope/count/hash pin reviewed
  against runtime `835cfb9599753a858db26a33b4b1c263f6af8039`.

The input retains its preparation-stage held decisions; the accepted derivative
and independent pin record subsequent bounded approval. A digest identifies bytes,
not reviewer authentication, legal ownership or independent scientific validity.
Source snapshots were acquired on 9 October 2026; later source changes are not
covered by this pin. Private snapshots and geometry evidence are not included.

## Rights and scientific limits

Exact provider density in kg/m^3, formulas, method, authors, references, license
links, modification notices and complete related-group/calculation metadata are
preserved. The extra project-change notice describes normalization and composition
bucketing. Source metadata is attributed under CC BY 4.0; see each record for its
named authors, exact source URL, license URL and references. Some related groups
have ICSD lineage. This acceptance covers attributed metadata and computed scalar
density only, and does not license redistribution of upstream ICSD geometry,
lattices, coordinates, raw archives, calculation files or potentials. None is
included. Geometry diagnostics were private consistency checks, not proof of
physical existence, stability or globally unique identity.

CaCo3 remains held outside this example: three related calculations lack provider
group and symmetry metadata required by v2. Do not invent identifiers or drop
relations to admit it. Prior seven and prior 24 examples remain separate and
unchanged. No main catalog admission or change to its 1057 identities is implied.

## Local opt-in use

Requires the exact installed legacy core baseline. Run from the repository root:

```python
from pathlib import Path
import json
from materials_query.computed_registry import ComputedRegistry

example = Path('experimental/platform/examples/reviewed-computed-v2-second')
review = json.loads((example / 'normalized-review.json').read_text())
pin = json.loads((example / 'acceptance-pin.json').read_text())
registry = ComputedRegistry(
    'new-second-tranche-local.sqlite', review,
    trusted_review_sha256=pin['canonical_review_sha256'],
    input_file_bytes=(example / 'eligible-metadata-input.json').read_bytes(),
)
result = registry.admit([record['candidate_id'] for record in review['records']])
assert result['scoped_accepted_identity_bucket_count'] == 62
assert result['related_source_calculation_count'] == 444
```

Use a new database. An existing registry is pinned to its own review and cannot
be reinterpreted as this batch. Replaying the same accepted IDs is idempotent.
Nothing enables the example by default. Explicitly passing the registry to
`create_app` captures a read-only process-pinned API snapshot.

The regression suite checks every field through 186 per-record HTTP projections,
list/export, process pinning, replay/reopen, cross-batch database isolation and
identity/relation duplication. A disposable combined structural fixture checks
prior 24 plus new 62 = 86 buckets, 163 groups and 562 calculations below the
existing 1 MiB limit. That fixture is not a newly accepted combined source review;
its input hash does not establish combined provenance. It is never published as
an accepted example or persisted outside a temporary test database. The previous
seven-record example is excluded from those cumulative counts. Global chemical
equivalence remains unresolved. See `../../COMPUTED_V2.md` for the runtime contract.
