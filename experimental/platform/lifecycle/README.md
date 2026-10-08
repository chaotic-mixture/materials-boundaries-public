# Local dataset lifecycle prototype

A runnable, isolated English-language implementation of bounded NOMAD acquisition → byte capture → deterministic staging/cache → exact review → immutable local release candidate. It does not modify the frozen Materials Boundaries software or its production catalog. Source identity counts remain zero. No accounts, CI installation, schedules, uploads or DOI registration are included.

## Install and run

Python 3.11+; zero third-party runtime dependencies.

```sh
python -m pip install . --no-build-isolation
python -m unittest discover -s tests -v
python -m materials_lifecycle --help
python demo.py
```

`demo.py` creates an inspectable `demo-store/` using the previously captured NOMAD archive projection wrapped as an injected HTTP response fixture. This is an exact hash of the **injected fixture bytes**, not a claim to preserve the historic live response. Demo reviewer names are explicitly test labels, not authenticated people. Generated archives are marked `local_demo`, cannot claim a scientific dataset publication, and contain no DOI. Original-source license declarations remain declarations; actual redistribution rights require human verification.

## CLI

```sh
materials-lifecycle --store work capture --formula CaFe2Re --limit 1 --fixture fixtures/nomad_response.json
materials-lifecycle --store work stage work/acquisitions/ACTUAL_HASH.json
materials-lifecycle --store work inspect work/batches/ACTUAL_HASH.json
materials-lifecycle --store work review work/batches/ACTUAL_HASH.json \
  --approve 'nomad:EXACT_ENTRY_ID' --reviewer 'ACTUAL_REVIEWER_REFERENCE' \
  --contributor 'ACTUAL_CONTRIBUTOR_REFERENCE' --rationale 'Scope and result of inspection' \
  --rights-evidence 'https://actual-rights-evidence.example/' --demo
materials-lifecycle --store work build work/batches/ACTUAL_HASH.json work/reviews/ACTUAL_HASH.json \
  --trusted-decision-sha256 ACTUAL_REVIEW_HASH --version 1.0.0 \
  --title 'Explicit dataset title' --creator 'Verified creator'
```

The uppercase values above are command placeholders, not identifiers in generated metadata. Omit `--fixture` only to request a real bounded public NOMAD GET. At most 25 entries, 2 pages and 5 MB are captured by default. Formula and count are the only user query inputs. No secret headers, cookies, arbitrary endpoints or arbitrary request parameters are supported. Capture uses identity content encoding, rejects redirects and compressed responses, and stops on rate limits, HTTP denial, timeout or changed payload shape. This MVP does not auto-retry; rerun after respecting provider Retry-After outside the tool. No live request was required for this implementation's verification.

## Inspectable store

- `raw/SHA256`: exact response bytes (fixture-labelled when injected)
- `acquisitions/SHA256.json`: distinct retrieval event, timestamps, provider/profile/parser/schema/code versions, bounded query, per-page headers/counts/hash and cursor state
- `attempts/SHA256.json`: failed attempts; captured raw objects are never overwritten
- `cache/CONTEXT_HASH.json`: deterministic normalization for raw bytes + query + provider profile + implementation + baseline
- `batches/SHA256.json`: source candidates, machine holds, explicit queue and baseline differences
- `lineage/SHA256.json`: links repeated acquisition events to stable candidate batch
- `reviews/SHA256.json`: explicit approved IDs, candidate and source digests, rationale and local reviewer references
- `releases/VERSION/`: selected records, provenance, rights ledger, review, citation JSON/CFF, manifest, checksums and deterministic tar
- `status_events/SHA256.json`: detached erratum/withdrawal/supersession events; old release bytes stay intact

A bounded-query disappearance is a missing result, never an automatic retraction. Provider revisions change source content, not material counts. Duplicate source IDs are held at acquisition/staging failure rather than silently deduplicated. Each new attempt is append-only. Reusing a dataset version for different bytes fails. Timestamps do not contaminate scientific candidate identity; original raw byte changes do, including whitespace.

## Explicit trust boundary

This is a local workflow, **not an authenticated multi-user review service**. Whoever can edit or run the local code/store controls local attestations. A digest proves content binding, not reviewer identity or honesty. Verify reviewer identity, independence, consent and authority outside the tool before accepting the supplied review digest. Reviewer-authentication gate is always `not_run`; no institutional or independent scientific validation is claimed by a passing test. Untrusted provider content never supplies approval. The CLI only accepts explicit reviewed subsets; unknown licenses, unknown lanes, retracted records and fixture-to-scientific promotion fail closed.

## Evidence and release scope

NOMAD simulation evidence routes to `calculated`; an explicit experimental section routes to `experimental`; absent/ambiguous methods are held. Native evidence and original numeric lexical strings are retained. There is no inference of temperature, uncertainty, unit conversion or specimen status. This initial normalizer does not implement a reference-provider mapper; reference/unknown providers require a reviewed profile, not a guessed lane. Synthetic fixture provenance stays separate and allows only a labelled demo artifact. Source formula is not a canonical identity. Properties/observations/grades/states/production identities remain zero in manifest counts because they are not normalized/admitted by this prototype.

Dataset SemVer is user-selected, separately from prototype software version 0.1.0 and candidate schema. Citation metadata names the exact local dataset version and leaves all DOI fields null with `unregistered` status. Raw files are not redistributed inside release archives; selected native source envelopes and source/license links are included only after the explicit rights attestation. There is no automatic MIT relicensing of source data. A local candidate can be inspected and reproduced, but authenticated reviews, full scientific mappings, reference adapters, production regression checks and external publication are separate future work.

## Correction limitations

Errata conservatively hold new use, as do withdrawals and supersessions. The current status registry keys the source record ID: it deliberately does not reopen a corrected revision automatically. An authenticated, reviewed correction/reinstatement flow is not implemented. Release `parent_snapshot` remains null; `baseline_batch_sha256` accurately identifies the compared staging baseline, which is not necessarily a published dataset. Changelog records before/after candidate hashes and says analysis impact needs human review. Dataset-major/minor/patch eligibility is a human policy decision, not automatically enforced.
