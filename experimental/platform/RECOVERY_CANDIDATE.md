# 0.5.0.dev0 recovery candidate

This is new English-language implementation built from the verified public
f1301af API 0.2 baseline. It does not restore missing 0.3 or 0.4 source, relationship
work, historical seven material identities, or historical test counts. The core
0.35.0 package and its 1,057 identities remain byte-for-byte unchanged.

## Computed namespace

The optional local `ComputedRegistry` stores reviewed normalized facts separately
from legacy data. The default app keeps this namespace disabled. Provider search
and optional legacy catalog contracts remain separate. No cross-namespace count,
structural equivalence, stable phase, equilibrium geometry, experimental density,
relationship graph, or mechanical-bound claim is inferred.

An operator prepares a review document using schema `computed-review-recovery/1`,
independently reviews its exact contents, and supplies its canonical JSON SHA-256
to `ComputedRegistry(database, review, trusted_review_sha256=...)`. The hash pins
identity; it does not authenticate a reviewer or establish scientific correctness.
`admit(candidate_ids)` is local-only, atomic, append-only under the supported API,
and idempotent. Held records cannot be admitted. Initial review and baseline pins
cannot be replaced within an existing database. Multiple calculations with the
same NOMAD material ID share `computed:nomad:<material_id>` and count once. This
provider-based grouping does not prove structural equivalence.

A fresh app accepts `create_app(computed_registry=registry)`. Its process snapshot
is read-only and requires explicit `namespace="computed"` plus baseline, overlay
and review versions on every POST. Endpoints under `/api/computed/` are status,
list, search, exact, property, source and export. Searches are bounded English
casefolded literal AND matches. List/search return at most 100 provider records;
project unique counts are explicitly separate. Export is fixed to normalized
JSON, at most 1 MiB. There is no HTTP path, refresh, admission or upload operation.
Restart after local admission to capture another immutable overlay snapshot.

Density preserves the exact provider value in kg/m^3 and its path
`results.properties.structures.structure_original.mass_density`, labeled computed.
`original` identifies the NOMAD representation, not a verified unrelaxed or
stable structure. Entry-specific URLs, attribution, method and rights accompany
normalized exports. Geometry and raw calculation assets are not shipped here.

## Trust and integrity boundaries

The packaged baseline file manifest has a code-pinned digest and includes every
core Python/JSON resource. Changing a value without changing counts fails the
anchor. Review hashes cover source links, decisions and density. Registry reads
compare exact admitted payloads to pinned review input and an admission ledger,
rejecting deleted rows, forged held outcomes and changed sources. A malicious
local administrator can rewrite both database and program: this is not a signed,
remote or tamper-proof audit service. Back up the review, its independently stored
hash and registry together; treat filesystem permissions as a separate concern.

Outer pure-ASGI transport enforces a 32 KiB body limit during receive and keeps
a shared two-slot heavy-operation budget through actual response delivery, with a
60-second cooperative timeout,
disconnection and cancellation cleanup. Synchronous upstream work cannot be
forcibly killed by asyncio; adapter I/O timeouts remain required.

## Release scope

This source is a prerelease review candidate. No main-branch changes, remote push,
publication, automatic live admission or reconstruction of missing relationship
features has occurred. The accompanying external scoped review input covers seven independently
reviewed new acquisitions, admitted locally as normalized computed metadata only.
It is not installed in the default package. Geometry/raw redistribution remains
outside approval. Synthetic test admissions do not constitute live catalog entries. Fresh test results are recorded in the delivery report. Run
`python experimental/platform/ci/run_recovery_ci.py` to build five fresh wheels,
check exact query-wheel/source bytes, and verify all offline suites in a clean
installed environment.
