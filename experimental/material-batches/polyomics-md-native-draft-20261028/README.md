# Isolated PolyOmics MD density method implementation draft

**Independently reviewed within the four-file implementation scope; unapplied and unadmitted.** The
[source/finite-model-identity/contract proposal review](../polyomics-density-candidates-20261028/REVIEW_STATUS.md)
alone does not approve implementation. The later
[independent implementation review](independent-implementation-review.json)
approves this frozen four-file draft only.

The [four-file patch](implementation.patch) and
[original/draft hashes](draft-manifest.json) introduce a finite molecular-
simulation density method and `simulation_cell` basis, bind them in both
directions, require computational evidence/calculation/mass density and retain
the measured-crystal, DFT-crystal, empirical and compilation branches. Four
language labels are present; translation remains machine assisted and has no
independent scientific translation review.

[Producer checks](VALIDATION.json): ten new contract tests and 29 original
contract tests passed, with zero failures/skips. They cover scientific class
confusion, wrong basis/method/quantity/evidence, retained old branches, unchanged
3180-record working graph validation, generated public schema and four-language
synthetic rendering. No native 1,000-record MD mapping, real installed MD check
or full MD regression has run.

The independent reviewer ran ten focused tests successfully and additionally
compared 1050 old-branch combinations with zero accept/reject changes, plus 240
MD combinations enforcing the new class/basis coupling. Public schema and four
language labels agree with the draft. This does not approve unseen integration.

The public schema also normalizes CRLF to LF. The patch represents normalized
text differences; the manifest binds the actual original/draft byte images.
It must not be described as only two raw-byte enum insertions. Future application
must reproduce the bound complete schema image or regenerate and verify it.

All changes are in an external isolated stage. The live runtime remains the
frozen JARVIS full-root regression snapshot. Do not apply this patch during that
run. Recheck its original hashes after the current stage closes; source/facts,
native mapping, new history and runtime/installed gates remain separate.

```powershell
python -B test_isolated_md_contract.py --stage PATH_TO_ISOLATED_MD_STAGE -v
```
