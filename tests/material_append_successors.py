"""Finite test-only successor registry; never a runtime admission authority.

Descriptors are newest first and bind explicit immutable ledgers. Existing
historical wrappers prepend this registry to their unchanged older ledgers.
No directory discovery, candidate inference or unpinned input is accepted.
"""
from pathlib import Path

from material_append_history import (
    load_frozen, project_catalog_bytes_chain, project_catalog_chain,
    project_file_chain, recover_catalogs,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_LEDGER = "tests/fixtures/primary_table_growth_data_20261019.json"
DATA_SHA256 = "faa453c3d57bb4a9040fac084cb9a96ad6c3437c237f80ea8eff4cc3e3fe261f"
FILE_LEDGER = "tests/fixtures/primary_table_growth_files_20261019.json"
FILE_SHA256 = "5af92f8baeb78cf21ea0098b13bfc0241de3623df5989897964426f0ffb33938"
DATA_2_LEDGER = "tests/fixtures/primary_table_growth_2_data_20261019.json"
DATA_2_SHA256 = "f3fcc3e8fdcdb292a2f3cf0b13c50de6bc90604ed2ac28b8938c9334e45933fc"
FILE_2_LEDGER = "tests/fixtures/primary_table_growth_2_files_20261019.json"
FILE_2_SHA256 = "95553e15c07be8aa7d1540875e83c52505fd472a73417a4e78ff0a29edf6fb3c"
DATA_3_LEDGER = "tests/fixtures/primary_table_growth_3_data_20261019.json"
DATA_3_SHA256 = "4ae9986cc914d9ff06a40875c19d606c0502a28527488151e6c71ec5f27eb0fe"
FILE_3_LEDGER = "tests/fixtures/primary_table_growth_3_files_20261019.json"
FILE_3_SHA256 = "e5a33c0aeb3b3e6eb0bde2c6fc658735a373e29244a891e07d300b3e8b0a66d7"
DATA_4_LEDGER = "tests/fixtures/primary_table_growth_4_data_20261019.json"
DATA_4_SHA256 = "d57a1014e6d9e66f3f6c031e3a56abda909acc924fb9ab16835948989f4ce89c"
FILE_4_LEDGER = "tests/fixtures/primary_table_growth_4_files_20261019.json"
FILE_4_SHA256 = "a0bd763d3524ce9f453d53cc060c3ec993a69c011450db0a00bc76b13597e16b"
DATA_5_LEDGER = "tests/fixtures/primary_table_growth_5_data_20261020.json"
DATA_5_SHA256 = "ced45ed6989e8988d461b0256c3ef7781c0f04b8364c6c991e3cacf36b064ff9"
FILE_5_LEDGER = "tests/fixtures/primary_table_growth_5_files_20261020.json"
FILE_5_SHA256 = "1f2c64f12b385228a8f7360da50bb85e2746b6fbd7adfdb5fb64d3a6624d34a2"
DATA_6_LEDGER = "tests/fixtures/primary_table_growth_6_data_20261020.json"
DATA_6_SHA256 = "3d3335edadae838524756ad1b33efb733d48893a123e6637c461dc79d59861b5"
FILE_6_LEDGER = "tests/fixtures/primary_table_growth_6_files_20261020.json"
FILE_6_SHA256 = "e13d5e02e863da91ea6318b598c69df73cc37af72b092ba502d466adba7244ab"
DATA_7_LEDGER = "tests/fixtures/primary_table_growth_7_data_20261020.json"
DATA_7_SHA256 = "26c80c5274504af2e0adbb55b4346d395e7c13e7009c504229f9c9dc32ca01fe"
FILE_7_LEDGER = "tests/fixtures/primary_table_growth_7_files_20261020.json"
FILE_7_SHA256 = "9731afe6a6df8a668d2821f571e4cef337084c34dbfff60ccd4deb459c60d2ff"
DATA_8_LEDGER = "tests/fixtures/primary_table_growth_8_data_20261021.json"
DATA_8_SHA256 = "de662ffe08378402a224b4ee4180252b620278dfb79164b58a20884d68e82c51"
FILE_8_LEDGER = "tests/fixtures/primary_table_growth_8_files_20261021.json"
FILE_8_SHA256 = "ad37d06723db7e66a071fe1f6584f28f16f7a386626db8778e5fa3045f27d5ea"

TOUGH_DATA_LEDGER = "tests/fixtures/tough_pla_followup_data_20261021.json"
TOUGH_DATA_SHA256 = "46d33c7bfc8abb32b341a5c026ed8cb03e47350feeb17e2b0c478999aeacf1f4"
TOUGH_FILE_LEDGER = "tests/fixtures/tough_pla_followup_files_20261021.json"
TOUGH_FILE_SHA256 = "7c1ff7be1ffb8f5085e004f465ca52e936e9068bfc1357e46925e150eb08bfef"

NYLON_DATA_LEDGER = "tests/fixtures/nylon_followup_data_20261021.json"
NYLON_DATA_SHA256 = "88f7303d6e8b4234555548ea39fdfb286380c72ea2f7f5edce990e1a0d733b97"
NYLON_FILE_LEDGER = "tests/fixtures/nylon_followup_files_20261021.json"
NYLON_FILE_SHA256 = "b35d130af81b437dfc2248f55e0c99b01c31da71d74a562dc754334b96dfde93"

# This code-only successor changes no catalog, packet or admission chronology.
# Keep its finite workflow recovery separate from the material append registry.
CODE_FILE_LEDGER = "tests/fixtures/family_adjacency_files_20261023.json"
CODE_FILE_SHA256 = "5cf1cfe7b367b42703cc027a000a4da1673cf2ee9d1717aee3578f094e2785e1"

BRUNS_BATCH_ID = "bruns-nbs2-borosilicate-20261023"
BRUNS_DATA_LEDGER = "tests/fixtures/bruns_borosilicate_data_20261023.json"
BRUNS_DATA_SHA256 = "6eded8614db38dcd26ad1e570d7ad783110dd690296e59a9270300bfd3a0a016"
BRUNS_FILE_LEDGER = "tests/fixtures/bruns_borosilicate_files_20261023.json"
BRUNS_FILE_SHA256 = "90e4d8910339118162fea9eb96ecf1e3bfe4c4b6becb348f92bb0cab65ca3d2c"

TARASOV_BATCH_ID = "tarasov-pna-bpf-20261023"
TARASOV_DATA_LEDGER = "tests/fixtures/tarasov_pna_bpf_data_20261023.json"
TARASOV_DATA_SHA256 = "ff13299c063b805d4cb36e73fe8db1521e88cab51aff2af13d2f4afab0a30773"
TARASOV_FILE_LEDGER = "tests/fixtures/tarasov_pna_bpf_files_20261023.json"
TARASOV_FILE_SHA256 = "688774855249682624bda92b9cf0daf3c96f234d8eba7befee70676d1bcc4bec"

KAPOOR_BATCH_ID = "kapoor-phosphate-glasses-20261024"
KAPOOR_DATA_LEDGER = "tests/fixtures/kapoor_phosphate_data_20261024.json"
KAPOOR_DATA_SHA256 = "d30ed8fd0d823a96d2285b9ecbc9b1e25f40c963fc4a45576862568ddfd28e69"
KAPOOR_FILE_LEDGER = "tests/fixtures/kapoor_phosphate_files_20261024.json"
KAPOOR_FILE_SHA256 = "3e253f3397252c4fd923ed11f2a8f5d9eddb70daac35896ee527b5610f247f7f"

TIAN_BATCH_ID = "tian-nano-ti-composites-20261024"
TIAN_DATA_LEDGER = "tests/fixtures/tian_nano_ti_data_20261024.json"
TIAN_DATA_SHA256 = "242cb5734a0323fbda3684dc6409692b28696e85a3a1d165b0f6d9fd86e643ce"
TIAN_FILE_LEDGER = "tests/fixtures/tian_nano_ti_files_20261024.json"
TIAN_FILE_SHA256 = "4b2a98114a44f0d794f89b7e368859948b70789b12a25b6d70524e53360d3d83"

CURAUA_BATCH_ID = "czlonka-curaua-20261025"
CURAUA_DATA_LEDGER = "tests/curaua_runtime/data-history.json"
CURAUA_DATA_SHA256 = "ce10a8972b4935677db755e25e8b00239513207b83c877de57ae63218fbab375"
CURAUA_FILE_LEDGER = "tests/curaua_runtime/files-history.json"
CURAUA_FILE_SHA256 = "74ab59414a6ca31f3bd41688e89dfd4db965b9effb6485e5b97685a8f95fe617"

EWURUM_REACTIVE_BATCH_ID = "ewurum-reactive-20261025"
EWURUM_REACTIVE_DATA_LEDGER = "tests/ewurum_reactive_runtime/data-history.json"
EWURUM_REACTIVE_DATA_SHA256 = "1fc44b8bc6f121a3323b632a1cdce8f7511bdbd2421bd33768529f359976b513"
EWURUM_REACTIVE_FILE_LEDGER = "tests/ewurum_reactive_runtime/files-history.json"
EWURUM_REACTIVE_FILE_SHA256 = "2f7a1b0b71f4c35411bab466398df1dc3abfcef8bf74b14b6cff33717e032857"

FROZEN_SUCCESSORS = (
    {"batch_id": EWURUM_REACTIVE_BATCH_ID,
     "data": (EWURUM_REACTIVE_DATA_LEDGER, EWURUM_REACTIVE_DATA_SHA256),
     "files": (EWURUM_REACTIVE_FILE_LEDGER, EWURUM_REACTIVE_FILE_SHA256)},
    {"batch_id": CURAUA_BATCH_ID,
     "data": (CURAUA_DATA_LEDGER, CURAUA_DATA_SHA256), "files": (CURAUA_FILE_LEDGER, CURAUA_FILE_SHA256)},
    {"batch_id": TIAN_BATCH_ID,
     "data": (TIAN_DATA_LEDGER, TIAN_DATA_SHA256), "files": (TIAN_FILE_LEDGER, TIAN_FILE_SHA256)},
    {"batch_id": KAPOOR_BATCH_ID,
     "data": (KAPOOR_DATA_LEDGER, KAPOOR_DATA_SHA256), "files": (KAPOOR_FILE_LEDGER, KAPOOR_FILE_SHA256)},
    {"batch_id": TARASOV_BATCH_ID,
     "data": (TARASOV_DATA_LEDGER, TARASOV_DATA_SHA256), "files": (TARASOV_FILE_LEDGER, TARASOV_FILE_SHA256)},
    {"batch_id": BRUNS_BATCH_ID,
     "data": (BRUNS_DATA_LEDGER, BRUNS_DATA_SHA256), "files": (BRUNS_FILE_LEDGER, BRUNS_FILE_SHA256)},
    {"batch_id": "zenodo-8089569-nylon-followup-20261021",
     "data": (NYLON_DATA_LEDGER, NYLON_DATA_SHA256), "files": (NYLON_FILE_LEDGER, NYLON_FILE_SHA256)},
    {"batch_id": "zenodo-8089569-tough-pla-followup-20261021",
     "data": (TOUGH_DATA_LEDGER, TOUGH_DATA_SHA256), "files": (TOUGH_FILE_LEDGER, TOUGH_FILE_SHA256)},
    {"batch_id": "zenodo-8089569-filaments-20261021",
     "data": (DATA_8_LEDGER, DATA_8_SHA256), "files": (FILE_8_LEDGER, FILE_8_SHA256)},
    {"batch_id": "outokumpu-core-moduli-20261020",
     "data": (DATA_7_LEDGER, DATA_7_SHA256), "files": (FILE_7_LEDGER, FILE_7_SHA256)},
    {"batch_id": "tamas-benyei-nbr-rcf-20261020",
     "data": (DATA_6_LEDGER, DATA_6_SHA256), "files": (FILE_6_LEDGER, FILE_6_SHA256)},
    {"batch_id": "bianchi-nr-nanoclay-20261020",
     "data": (DATA_5_LEDGER, DATA_5_SHA256), "files": (FILE_5_LEDGER, FILE_5_SHA256)},
    {"batch_id": "mtibe-pbs-pbat-hybrids-20261019",
     "data": (DATA_4_LEDGER, DATA_4_SHA256), "files": (FILE_4_LEDGER, FILE_4_SHA256)},
    {"batch_id": "nbs-binary-oxide-density-20261019",
     "data": (DATA_3_LEDGER, DATA_3_SHA256), "files": (FILE_3_LEDGER, FILE_3_SHA256)},
    {"batch_id": "nbs-rca-density-20261019",
     "data": (DATA_2_LEDGER, DATA_2_SHA256), "files": (FILE_2_LEDGER, FILE_2_SHA256)},
    {"batch_id": "nbs-salt-densities-20261019",
     "data": (DATA_LEDGER, DATA_SHA256), "files": (FILE_LEDGER, FILE_SHA256)},
)


def _descriptors():
    if not isinstance(FROZEN_SUCCESSORS, tuple) or not FROZEN_SUCCESSORS:
        raise AssertionError("Frozen successors must be a nonempty finite tuple")
    names = [descriptor["batch_id"] for descriptor in FROZEN_SUCCESSORS]
    if len(set(names)) != len(names):
        raise AssertionError("Duplicate frozen successor batch")
    return FROZEN_SUCCESSORS


def _index(batch_id):
    indices = [index for index, descriptor in enumerate(_descriptors())
               if descriptor["batch_id"] == batch_id]
    if len(indices) != 1:
        raise AssertionError("Unknown or duplicate frozen successor batch")
    return indices[0]


def _prefix(before):
    return _descriptors() if before is None else _descriptors()[:_index(before)]


def data_ledger(batch_id=None):
    descriptor = _descriptors()[0 if batch_id is None else _index(batch_id)]
    return load_frozen(ROOT, *descriptor["data"])


def file_ledger(batch_id=None):
    descriptor = _descriptors()[0 if batch_id is None else _index(batch_id)]
    return load_frozen(ROOT, *descriptor["files"])


def data_ledgers(*, before=None):
    return [load_frozen(ROOT, *descriptor["data"]) for descriptor in _prefix(before)]


def file_ledgers(*, before=None):
    descriptors = _prefix(before)  # Reject unknown historical boundaries first.
    # The adjacency-only workflow boundary sits between Bruns and Nylon.
    # Insert it at that explicit chronological point, never before newer edits.
    # Full-chain callers also recover the finite documentation call sites.
    # Named material boundaries retain their original exact ledger views.
    from legacy_document_recovery import code_ledger
    from replay_checkout_history import code_ledger as checkout_code_ledger
    from ci_partition_history import code_ledger as partition_code_ledger
    from curaua_history import registry_ledger
    from ewurum_reactive_history import registry_ledger as ewurum_registry_ledger
    result = [ewurum_registry_ledger()] if any(item["batch_id"] == EWURUM_REACTIVE_BATCH_ID for item in descriptors) else []
    result += [load_frozen(ROOT, *descriptor["files"]) for descriptor in descriptors
               if descriptor["batch_id"] == EWURUM_REACTIVE_BATCH_ID]
    result += [registry_ledger()] if any(item["batch_id"] == CURAUA_BATCH_ID for item in descriptors) else []
    result += [load_frozen(ROOT, *descriptor["files"]) for descriptor in descriptors
              if descriptor["batch_id"] == CURAUA_BATCH_ID]
    result += [partition_code_ledger(), checkout_code_ledger()] + ([code_ledger()] if before is None else [])
    for descriptor in descriptors:
        if descriptor["batch_id"] in {EWURUM_REACTIVE_BATCH_ID, CURAUA_BATCH_ID}:
            continue
        result.append(load_frozen(ROOT, *descriptor["files"]))
        if descriptor["batch_id"] == BRUNS_BATCH_ID:
            result.append(load_frozen(ROOT, CODE_FILE_LEDGER, CODE_FILE_SHA256))
    return result


def recover_latest_catalogs(current):
    """Strictly accept the exact latest predecessor or complete successor."""
    return recover_catalogs(ROOT, current, data_ledger())


def project_successor_catalogs(current, *, before=None):
    """Project known successors; the historical caller still validates input."""
    return project_catalog_chain(ROOT, current, data_ledgers(before=before))


def project_successor_catalog_bytes(filename, raw, *, before=None):
    return project_catalog_bytes_chain(ROOT, filename, raw, data_ledgers(before=before))


def project_successor_file(filename, raw, *, before=None):
    return project_file_chain(filename, raw, file_ledgers(before=before))
