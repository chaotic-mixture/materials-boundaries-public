"""Finite test-only documentation recovery after existing truthful normalization.

No count is parsed or erased here. The v0.35 normalizer must first validate its
own current/historical count contract. Only complete normalized byte images can
then recover their exact prose predecessor; the caller still enforces its old
release hash. Attribution recovery is whole-file exact and independent of data.
"""
from pathlib import Path
from material_append_history import load_frozen, project_file_chain

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_LEDGER = 'tests/fixtures/legacy_document_recovery_20261023.json'
DOCUMENT_SHA256 = '7262e5f5a7ba6e6ab7d0093f8bc612bd2008be536f20685c2beba7358c4a9001'
CODE_LEDGER = 'tests/fixtures/legacy_document_call_sites_20261023.json'
CODE_SHA256 = '9510bff71fdd667d35ae3798ed80948f2a6e807487551f7fc49f15d1fd9f47af'


def code_ledger():
    return load_frozen(ROOT, CODE_LEDGER, CODE_SHA256)


def project_legacy_code_bytes(filename, raw):
    """Project finite helper edits; never change an older assertion or ledger."""
    return project_file_chain(filename, raw, [code_ledger()])


def project_legacy_document_bytes(filename, raw):
    """Unknown or changed bytes pass through to the original fail-closed pin."""
    if filename not in {'README.md', 'THIRD_PARTY_NOTICES.md'}:
        raise AssertionError('Unknown legacy documentation path')
    ledger = load_frozen(ROOT, DOCUMENT_LEDGER, DOCUMENT_SHA256)
    return project_file_chain(filename, raw, ledger['ledgers'])
