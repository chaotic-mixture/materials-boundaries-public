"""Finite test-only engine recovery; never rewrite unknown historical bytes.

Only one reviewed whole-file image is mapped to its exact predecessor. This
code-only bridge changes no data ledger, material registry or admission claim.
Every matching call rereads the pinned ledger; there is no cross-call cache.
"""
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "196995256836db2d8f870ac9a91f664bfdd03e7f"
ENGINE_PATH = "tests/material_append_history.py"
LEDGER_PATH = "tests/fixtures/material_append_replay_code_20261024.json"
LEDGER_SHA256 = "b09510228cfcf6d3ae07833ce979636fb2334db84a2d586c1b0b313c718647dd"
CURRENT_SHA256 = "2379867c0fe4ec89cf4f450b10bf84e48986783d50396c6f593316de78ad3251"
PREVIOUS_SHA256 = "38d9b1768121f84cc5b45d21d8d992b8d62cf6ed62ad0ed1ec78f7760ece9ea9"


def project_engine_bytes(raw):
    """Recover the exact reviewed image; let old checks reject unknown bytes."""
    if type(raw) is not bytes:
        raise AssertionError("Replay compatibility input must be bytes")
    if sha256(raw).hexdigest() != CURRENT_SHA256:
        return raw
    # Import lazily: the history engine calls this helper, while its unchanged
    # primitives validate this independent, non-self-referential code ledger.
    from material_append_history import load_frozen, recover_file
    ledger = load_frozen(ROOT, LEDGER_PATH, LEDGER_SHA256)
    if (set(ledger) != {"schema_version", "baseline_commit", "updates"}
            or ledger["schema_version"] != 1 or ledger["baseline_commit"] != BASE_COMMIT
            or set(ledger["updates"]) != {ENGINE_PATH}):
        raise AssertionError("Unexpected finite replay code ledger")
    entry = ledger["updates"][ENGINE_PATH]
    if entry["sha256"] != CURRENT_SHA256 or entry["previous_sha256"] != PREVIOUS_SHA256:
        raise AssertionError("Replay code ledger images differ from frozen pins")
    previous = recover_file(raw, entry)
    if sha256(previous).hexdigest() != PREVIOUS_SHA256:
        raise AssertionError("Replay code predecessor bytes changed")
    return previous
