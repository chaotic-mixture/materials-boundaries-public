# Polymer formulation local increment

This manifest integrates two frozen packets from commit
`0dceb99d08f3c063a42c6cb3f084e9f82c9ebd2e` into the exact
`7388976fa914399a210322d019e3081f201ff08f` baseline. The existing offline command
reads SPO-2 first, followed by PBS/lignin B10 and B30. Every materials, properties,
reused-source and review input is bound by SHA-256.

The increment adds three identities, three source-scoped states and three
properties: one polymer and two composites. It adds no grade or source. The
complete source registry remains byte-identical. The candidate packets retain
the source-specific formulation distinctions, property transcription and rights:

- [SPO-2 rigid PUR](../20261017-spo2-rigid-pur/README.md): suberinic-acid/tall-oil
  polyols distinguish this formulation from existing Lupranol-based LPO-1.
  Its reported apparent density is 40.7 kg/m^3. Density aggregation, specimen
  count and uncertainty remain unknown. The separate SPO-1 table/prose
  discrepancy is retained; SPO-1 and other optimization variants are excluded.
- [PBS/lignin blends](../20261017-pbs-lignin-blends/README.md): separately prepared
  B10 and B30 contain 10 and 30 wt.% lignin on the source total-polymer-mass
  basis. Young's modulus means are 922 and 969 MPa, respectively, with SD 77 MPa
  and ten replicates for each. Existing B0, B20 and Indulin AT are not repeated.
  The grade ambiguity, unreported modulus fit window and unknown test climate
  remain explicit; no reactive Rxx counterparts are added.

The experimental core has 1079 identities. The project projection has 1103:
1079 source-qualified identities plus the unchanged 24 reviewed computed
composition buckets. Its categories are natural 1010, metal 34, inorganic 38,
polymer 15 and composite 6. The 62 excluded computed examples remain excluded.
Released main remains at 1081; the immutable report records
`formal_admitted_delta: 0`. Existing relationship-overlay evidence is unchanged,
so the new identities receive only their explicit primary catalog memberships.

The actual reproduction used baseline catalog bytes extracted from the exact
parent Git object into a separate evidence directory:

```text
python -B -X utf8 scripts/integrate_material_candidates.py --baseline-dir BASELINE_DIRECTORY --manifest experimental/material-batches/20261017-polymer-formulations-incremental/integration.json --output NEW_IMMUTABLE_PACKAGE.json
```

Two native Windows invocations of the unchanged command exited successfully.
The first created the package; the repeat reported unchanged, with identical
bytes and modification time. Native execution supports the existing atomic
hard-link publication, which the sandbox had denied in the previous NC2
increment. No publication logic or ACL was changed, and no new sandbox failure
is claimed for this increment. The resulting immutable package SHA-256 is
`4f972fd3e9f2007ae1ab300c430bc6e00acfa3610adcdd44ac85dd7184126072`.

Only the package's validated materials and properties catalogs were serialized
into runtime data. Removing the three appended identities, states and properties
recovers the exact parent bytes. The source registry and all earlier records
remain unchanged. Current resource pins and count expectations were refreshed;
all previous database-anchor rejection cases remain, including the NC2 anchor.
The new canonical query baseline anchor is
`f1a1e3e379f9b7befba595b54477f15a26364548798b28dd65be8bc4326c0df4`.

Both packets retain the inspected article-authored CC BY 4.0 scope, attribution,
asset hashes and original qualifications. No PDF, XML, table dump, figure,
screenshot or raw asset is bundled. Transcription review is not independent
scientific review or experimental replication. Scientific-review, raw-reanalysis,
universal-bound and engineering-allowable flags remain false, and every property
remains `catalog_only`.

`review.json` records the local integration and actual CLI validation scope.
Unit suites, installed-wheel checks and remote CI are separate evidence and are
not claimed by this manifest. Parent-coordinated experimental publication is
separate from local integration. No main merge, DOI registration or public
deployment occurs here.
