# NC2 concrete local increment

This manifest integrates the frozen NC2 packet at
`e7a1f14af3ad0b290049319c16387589f831fa0b` into the exact
`eaf16e1eb1edad17fbf78ac7385566f6a4e86a94` core baseline using the existing
offline integration command. All four packet JSON inputs are bound by SHA-256.

The local increment adds one composite identity, one source-scoped state and one
density property. It adds no grade or source; the complete source registry is
byte-identical. NC2 differs from NC1 in its cement, water and superplasticizer
recipe. The selected result is a nominal 28-day water-saturated mean density of
2340 kg/m^3 from three cylinders shared with the sequential oven-dry density
measurement. Neither the extra moisture state nor an extra property counts as
another material identity.

The experimental core now has 1076 identities. Its project projection has 1100:
1076 source-qualified identities plus the unchanged 24 reviewed computed
composition buckets. The categories are natural 1010, metal 34, inorganic 38,
polymer 14 and composite 4. The 62 excluded computed examples remain excluded.
These local counts do not change released main's 1081 admissions. The immutable
integration report records `formal_admitted_delta: 0`.

The original command was invoked against three baseline files extracted from
the exact parent Git object into a separate evidence directory:

```text
python -B -X utf8 scripts/integrate_material_candidates.py --baseline-dir BASELINE_DIRECTORY --manifest experimental/material-batches/20261017-nc2-incremental/integration.json --output NEW_IMMUTABLE_PACKAGE.json
```

The first sandbox attempt failed when Windows denied the atomic hard-link
publication operation; its failure is retained. The unchanged command then ran
twice through native Windows execution using a new evidence output path. Both
native invocations exited successfully. The first created the artifact and the
repeat returned unchanged with identical bytes and modification time. No ACL or
atomic-publication logic was changed. The resulting package SHA-256 is
`d9c5362764c69704d60fe761db2b9067ac17764ab3dc077bc9a142aa5f75fd9c`.

Only the validated package's materials and reference-properties catalogs were
serialized into runtime data. Resource pins and current count expectations were
then refreshed; previous database anchors remain rejected without migration.
The new canonical query baseline anchor is
`a38937d66a5d6c8f99eae6c05747e60a90f7647a737a1dc4d1cebc983fafcca3`.
Removing this packet's appended rows recovers the exact baseline graph and bytes.

The [candidate packet](../20261017-nc2-concrete/README.md) retains source locators,
the XML hash, article attribution, CC BY 4.0 scope and explicit unknowns. The
source-specific inspection and existing reuse basis apply to the selected
original study facts. No source asset is bundled. The scientific-review and
raw-reanalysis flags remain false; the property stays catalog-only,
non-universal and non-allowable. No density SD, measurement temperature or
bulk/apparent/true density designation is inferred.

`review.json` records this local integration and actual CLI validation scope.
Unit suites, installed-wheel verification and remote CI are separate evidence;
this manifest does not claim that those checks passed. Parent-coordinated
experimental publication remains separate from this local integration. No main
merge, DOI registration or public deployment is performed.
