# Local database continuation checks — 2026-11-02

Baseline: `a35928deaf3a1b5ad89211a798bcf0eaf5e02929`,
branch `experimental/open-database`. This record describes subsequent local work,
not hosted CI or a stable release. The native tables were not changed.

Database fingerprint:
`b931d7f94c8e40a73fcc918f47c9a8e9a0cffd5e5f31224aa97dafd48e045ff4`.

| Check | Actual result |
| --- | --- |
| Final database behavior/incremental tests | 18 passed, zero failures/errors/skips; Windows Python 3.11 |
| Three complete native table schemas | Draft 2020-12 with format checking passed; three undeclared-field controls rejected |
| Current material graph | All 5,197 properties passed current scientific contracts |
| SCC source/native replay | 1,000 candidates matched; value/disclosure/identity-key corruption rejected |
| Installed wheel | 65 package files equal source and wheel bytes |
| Installed summary CLI | Full, composite and copper selections equal source API results |
| Installed copper download | Export/verify passed; JSONL and manifest equal source export |
| Installed full download | 5,197 records exported and verified as a local candidate snapshot |

The scientific contracts are data checks, not independent scientific review.
SCC's [independent data-review decision](../experimental/material-batches/scc-fresh-flow-recipes-20261029/DATABASE_DATA_REVIEW.json)
approved the exact 1,000 candidate identities/states/properties and one source as
reviewed data at 2026-11-02 03:03:21 UTC. The reviewer rehashed the 38-file closure
and checked the exact ID list, without rerunning the full checks. Original failed,
cancelled and incomplete historical software regression remains historical; none
is converted into a passing result by these checks. No new full historical run
was started for this database continuation.

Wheel SHA-256:
`07cbaf5e4c395801071a65854beb79f47c9842279127afe081750abfd8519e3f`.
Its build succeeded with the existing isolated setuptools 80.9.0 / wheel 0.45.1
tools. Two earlier build attempts failed because the old shared environment lacked
`bdist_wheel` and the database install environment lacked `build.__main__`.
Neither failed attempt is counted as a successful build; no shared tool environment
was modified.

The full candidate JSONL contains 124,440,968 bytes, SHA-256
`8f97e712450f9d5989c988113ed27d7233b30273a809e00663c750a8210c6503`;
its manifest SHA-256 is
`974375d58af3c70b46d687a983287d0caf1aa816678a69c89aefbac4badf5ebf`.
It remains `exported_local_snapshot_not_release_acceptance`, with source rights
preserved per source. The download and full local audit assets are retained in
the external evidence package, not added as raw assets to this repository.

Evidence artifact hashes, retained for handoff:

- `database-tests-final-r1.log`: `42d1c5ba7c0a971586929a8c1f0deec6dc6b4e2009d7dc97b2dc79286bb677cb`
- `summary-installed-validation-r3.json`: `aac11d7189848f9a9637e58acfdbb6b2de8f7a9fcd70310b5547bbeae085386a`
- `scc-current-data-review-r2.json`: `2e9b303b6ef993b8e751173a6b27c9d1e35b5c20f7f971d9428dc53f6bd279f1`

The [SCC review input](../experimental/material-batches/scc-fresh-flow-recipes-20261029/DATABASE_REVIEW_INPUTS.json)
lists exact affected records and source/code/schema pins. Publishing these
subsequent changes still requires the consolidated experimental delivery and
checks for its exact commit. This file does not claim a push, main merge,
release tag or deployment.
