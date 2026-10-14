# Three NBS crystal references: pending experimental candidate

This unmerged candidate adds three source-qualified material identities under
the existing crystallographic-density contract to the experimental core. It adds
three states and three properties, with no new grades or sources. It is based on
main commit
`4c5656cf6ba0ad1a54b736e0568e97abe4815c29` and the frozen review packet
`1668b8e3525294af8df7d3a1383651d7f8a4c5d2`. Experimental upload is authorized;
a formal reviewed release is still pending. Main remains at 1081 formal project
admissions. The proposed experimental total below is 1084.

| Project category | Released main baseline | Proposed experimental candidate | Difference |
| --- | ---: | ---: | ---: |
| Natural | 1010 | 1010 | 0 |
| Metal | 26 | 26 | 0 |
| Inorganic | 28 | 31 | +3 |
| Polymer | 14 | 14 | 0 |
| Composite | 3 | 3 | 0 |
| Total | 1081 | 1084 | +3 |

The core README retains the published v0.35.0 wood-batch narrative verbatim,
including its historical 1057-record category counts. Only its marked current
material summary is refreshed. The table above, this document and current CLI/API
outputs describe the experimental integration; the old narrative is not a new
claim that the experimental inorganic core count is still 16.

The experimental source-qualified core contains 1060 identities (natural 1010,
metal 14, inorganic 19, polymer 14, composite 3). The candidate add-on combines
those with the unchanged 24 reviewed computed composition buckets for testing;
1084 is not an authorized new main formal count. The 62 excluded examples,
earlier excluded tranche and two separate NOMAD candidates awaiting human review
receive no admission credit. The five-category goal is not complete.

## Candidate scope

| Identity | Published density at 25 degrees C | Source locator |
| --- | ---: | --- |
| `mat_nbs1953_lif_harshaw` | 2.638 g/cm^3 | Section 2.34, printed p.61 / PDF p.65 |
| `mat_nbs1953_kcl_mallinckrodt_kyd1` | 1.9865 g/cm^3 | Section 2.38, printed p.66 / PDF p.70 |
| `mat_nbs1953_caf2_stockbarger_mit` | 3.181 g/cm^3 | Section 2.41, printed p.70 / PDF p.74 |

The source is Howard E. Swanson and Eleanor Tatge, *Standard X-ray Diffraction
Powder Patterns*, NBS Circular 539, Volume I (1953),
[DOI 10.6028/NBS.CIRC.539v1](https://doi.org/10.6028/NBS.CIRC.539v1).
The complete inspected PDF is 6,422,795 bytes with SHA256
`003b872fbe7d403d38bbd1d752568ee92a96bdb010b6e381bdc82566929e2a6c`,
matching the existing source record. Nine actual page images were checked;
independent frozen-payload review found no substantive discrepancy. The original
[review packet](../experimental/material-batches/20261014-nb-nbs-crystals/README.nbs.txt)
retains the complete fields and source locators. Its pending-admission wording
records the preparation stage. The references are now included in the experimental
core; admission through a formal reviewed release remains pending.

These are source-reported calculations from experimental XRD lattice constants,
not direct bulk-density measurements or DFT predictions. LiF's diffraction
pattern is at 26 degrees C; its density reference is 25 degrees C. KYD-1 is a
supplier label, not a verified grade. CaF2's silica-gel dilution concerns XRD
intensity preparation, not a composite density. Density uncertainty, independent
specimen count and density-specific conditioning remain unreported.

## Admission and review boundary

The authorized existing-contract material-contribution route applies, as described
in [the material reference guide](MATERIAL_REFERENCE_CATALOG.md#add-a-material-without-a-new-python-family).
Independent source transcription, identity reconciliation and scoped reuse review
were completed. Human scientific review remains pending and does not add a
human-signature prerequisite to the already authorized experimental upload.
This authorization does not approve a new formal release. The bulk wood adapter
is a separate workflow and is not impersonated or extended for this batch.

The general contribution guide still requires human scientific review of scientific
meaning and evidence. This integration does not claim that review occurred.
The existing schema requires `independent_scientific_review: false`;
`raw_data_reanalysis` also remains false. All records remain `catalog_only`, and
universal-bound and engineering-allowable flags remain false. No reviewer
signature or human identity is fabricated.

The existing NIST Technical Series reuse basis applies only to the selected
NBS-authored facts and original qualifications. Earlier third-party comparison
tables are excluded. Republished courtesy of the National Institute of Standards
and Technology. Source PDFs, page images, raw structures and complete tables are
not included in the repository. The source terms are not replaced by MIT.

## Preservation and verification

All 1057 old identities, states and properties retain their complete content and
order; all grades and the source registry are unchanged. Removing only the three
new records recovers the exact baseline catalog bytes. The frozen review payloads
are unchanged. The unmerged candidate retains proposed formal-component pins
matching its new core bytes, alongside the experimental query-service manifest.
These pins make the candidate reproducible; they do not change the released main
pins or establish release approval. No pin check is bypassed. Old SQLite anchors
remain incompatible and are not migrated automatically.

`tests/test_nbs_crystal_admission.py` checks exact payload equality, complete
predecessor recovery, current coverage, repeated-append idempotency and retained
scientific limits. Run the complete core suite and catalog validator, the formal
suite and the query-service catalog suites, followed by wheel metadata and isolated
installed-wheel checks. Actual commands, results and exact final diff are retained
with the integration handoff; a prescribed check is not evidence that it passed.

## Historical validation of ad9ab01

Commit `ad9ab01b2d367ffbaf620c9abd660f42323e8912` was checked on native Windows
with Python 3.11. The following actual results belong to that candidate snapshot.
They remain historical evidence and do not establish a completed full-suite run
for the current follow-up.

| Check | Actual result |
| --- | --- |
| Release metadata | 5 passed, 0 skipped |
| Complete catalog/schema validator | Passed with 1060 identities, states and properties |
| Selected core regression, 22 modules | 247 passed; 2 POSIX-only RSS benchmark tests skipped |
| Query catalog suite | 91 passed, 0 skipped |
| Query API suite | 37 passed, 0 skipped |
| Fresh installation of all six project wheels | Offline installation and `pip check` passed |
| Tests importing those installed wheels | 91 catalog and 11 formal tests passed, 0 skipped |

The selected core checks cover all three exact append records, complete predecessor
recovery, unchanged earlier preservation chains, repeated-append idempotency,
source/reuse constraints, classification and count integrity, malformed units and
missing facts, whole-graph validation before filtering, the existing NBS germanium
precedent, and retained scientific limitations. The query checks exercise old
database-anchor rejection and content changes that preserve identity counts.
Installed imports were verified to come from the new environment, outside the
checkout. Source and installed runs overlap and must not be added as unique tests.

The first native query run had four Windows cleanup errors because existing test
SQLite context managers committed transactions without closing connections. The
two test modules now close those connections explicitly, retaining the same
transactions and tamper-rejection assertions; the complete rerun passed. Earlier
sandbox failures and the failed first native run remain in the private evidence.

The broad core suite for `ad9ab01` was deliberately interrupted while testing
unchanged scientific families and is **incomplete, not passed**. Its partial
output is retained. The two POSIX benchmarks were skipped. The completed
follow-up run below is separate evidence; neither these historical results nor
parent-tracked CI establish cross-platform acceptance of this candidate. The
package version remains unchanged for this unreleased experimental candidate.

## Completed follow-up validation

On 2026-10-14, the full core command `python -B -m unittest discover -s tests -v`
ran to natural completion on native Windows 10.0.26200 with Python 3.11.0 and
jsonschema 4.26.0. It ran from 15:41 to 18:16 UTC without an elapsed-time cutoff.

| Check | Actual result |
| --- | --- |
| Release metadata preflight | 5 passed, 0 skipped; exit 0 |
| Complete catalog/schema validator | Passed with 1060 identities, states and properties; exit 0 |
| Complete core suite | 1366 discovered: 1350 passed, 16 skipped, no failures; exit 0 |
| Core suite duration | 9291.710 seconds |
| NBS checks within the full suite | All 4 passed, including repeat-append deduplication and exact predecessor recovery |
| Existing platform CI branch conditions | 37 static trigger cases passed; no remote run claimed |

The 16 skips comprise eight POSIX export tests, three POSIX pseudo-terminal
tests, two POSIX RSS benchmark tests, one Windows symlink-privilege case, one
non-Windows guard and one opt-in external frozen wood source-cache integration.
These checks are not counted as passed. The metadata preflight and NBS checks
overlap the complete suite and are not additional unique tests. Cross-platform
CI and the opt-in source-cache check remain outstanding.

An earlier follow-up attempt lost its executor transport and did not complete;
its logs are retained separately. The successful run above restarted the whole
suite in a hidden background process and continued through later status-transport
recovery without restarting. The tracked-file hashes matched at run start and
completion; only documentation of the final results was then updated.

This follow-up changes four Markdown files and the existing platform workflow's
exact branch/ref conditions. Runtime code, data, tests, proposed resource pins,
permissions and admission rules remain byte-identical to `ad9ab01`. The five
changed paths are not wheel inputs, so the six existing wheel artifacts and their
historical installed-test evidence remain applicable without claiming a fresh
wheel build or another installed test run. All prior evidence remains retained.

The platform workflow adds only `experiment/material-growth-nbs-integrated` to
the existing push and pull-request base-branch filters and both manual-dispatch
job guards. Existing paths, permissions, jobs and action references are unchanged.
This local validation does not trigger remote CI, authorize a formal release or
change main's published count of 1081.

Niobium remains outside this integration because its inspectable PDF and linked
supplement have not been obtained. It does not block these three reviewed NBS
references. The separately authorized experimental upload does not authorize a
formal release, DOI registration or public deployment.
