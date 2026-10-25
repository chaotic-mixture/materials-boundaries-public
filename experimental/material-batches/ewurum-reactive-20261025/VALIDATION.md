# Corrected candidate validation

This candidate remains outside runtime catalogs against baseline
`8ccd217599fd462d13d7435bdfb02a0825e4eacd`. Actual admission delta is **zero**.
The earlier immutable candidate `f55af18be0f809b5c8f06fba3fcbeb9db5fb1206` and its original bundle remain
available; this correction does not rewrite their source-review history.

## Independent-review correction

The original candidate incorrectly marked the standard edition unknown. Cached
publisher PDF p.15 reference [32], linked from p.5 section 2.9, explicitly cites
**ASTM D 1708-18 (2018)**. The corrected candidate records the source-cited
edition only. Independent standard compliance remains unverified; no dimensions,
conditioning or other omitted test conditions are inferred from the standard.

PDF p.4 section 2.4 measures gel fraction on hot-pressed material, separately
from the injection-molded tensile dog-bones. All candidate identity/state/property
scope notes now preserve this distinction. The contextual gel values support
formulation-level reaction context; they do not measure the tensile specimens'
gel fraction or final network. Modulus values, SDs, tensile n, identities,
category, source record and all historical B-series facts are unchanged.

Both additional pages were rendered and visually inspected from the same
hash-verified publisher cache. The optional text extractor was unavailable;
installed Poppler rendering succeeded. No source request, dependency installation
or raw-asset publication occurred.

## Executed checks and retained evidence

Native Windows CPython 3.11.0:

| Scope | Result | Timing |
| --- | --- | --- |
| Corrected candidate, same 20 method IDs | 20 passed; 0 failures/errors/skips | 94.906 s, ledger timing |
| Strengthened oracles against untouched original candidate | 3 methods: 1 passed; 2 rejected the two original defects; 0 errors/skips | 4.829 s |
| Complete existing compiler module | Earlier 11 passes retained; **not rerun this round** | 36.812 s, earlier ledger timing |

The negative probe had 10 assertion outcomes including subtests across its two
rejected methods. These are intentional original-candidate rejections, not
corrected-candidate passes, skips, expected-failure decorators or extra root
coverage. Its original input hashes, method IDs and log hash are recorded.

The available final positive evidence is 31 distinct methods: 20 on this
corrected candidate plus 11 from the prior unchanged compiler run. These are
separate processes and scopes, not an uninterrupted suite. The first candidate
attempt's 19 passes and one synthetic-fixture error, its subsequent 20-pass run,
and the initial WinError 5 atomic-write failure remain recorded. Across ordinary
suite attempts there were 71 method executions: 70 successful and one original
fixture error. The three-method rejection probe is reported separately.

The unchanged compiler created the corrected packet at a separate local path.
Only the new candidate artifact was then explicitly replaced; the old version
remains in Git. Repeating compilation preserved exact bytes and mtime. The
receipt binds all current inputs and the prior receipt hash. Semantic comparison
confirmed that only standard citation, gel specimen scope and inspection
provenance changed; the hypothetical merge delta remains 4 identities / 4 states /
4 properties / 0 grades / 0 sources, all composite and still candidate-only.

## Preservation and unrun scope

All **1030** baseline files, including **122** fixtures, remain byte-identical.
Existing source records, production code, workflows, 147-module / 1887-ID core
inventory, 459/492/417/519 partitions and 70-ID replay inventory are unchanged.
The finite identity audit still uses 22 canonical inputs plus two separately
bound prior-scope documents, 14171 label occurrences, 8261 normalized labels and
all 63 polymer/composite identities. It is not global chemical-equivalence proof.

Root coverage remains 11/1887 from the prior compiler run; **1876 root methods
remain unrun**. Twenty new candidate methods sit outside that frozen inventory.
The 70 replay methods, installed package/API/CLI tests, wheel smoke, hosted CI,
Linux and other Python versions were not run for this candidate correction.
No runtime admission or push occurred.

Current counts remain 1164 source-qualified plus 24 reviewed computed = **1188**.
Natural/metal/inorganic/polymer/composite counts remain 1010/32/59/30/33, with
gaps to 1000 of 0/968/941/970/967. Main remains last verified at 1081; 62 computed
examples stay excluded. Candidate counts are not formal growth.

## Reproduction

From the repository root with existing project test dependencies:

```text
python -X utf8 experimental/material-batches/ewurum-reactive-20261025/build_identity_review.py --check
python -X utf8 scripts/prepare_formulation_packet.py --spec experimental/material-batches/ewurum-reactive-20261025/packet-spec.json --baseline-dir materials_boundaries/data --output experimental/material-batches/ewurum-reactive-20261025/prepared-packet.json
python -X utf8 -m unittest discover -s tests/ewurum_reactive_candidate -p test_ewurum_reactive_packet.py -v
git diff --check
```

The complete prior compiler module can be reproduced separately with
`python -X utf8 -m unittest discover -s tests -p test_formulation_packet_preparation.py -v`.
Exact baseline Git objects are required for the finite audit. The current JSON
ledger binds tested file hashes, IDs, current outcomes, prior failures and unrun
scope. Independent immutable candidate review remains required before integration.
