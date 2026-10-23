"""Exact data-anchor and code-successor compatibility with synthetic reviews.

The predecessor fixtures reverse only exact evidence and presentation hunks.
Their integrated data anchor remains distinct from the recovered historical
catalog. Complete 64-file trees are hashed by the production baseline validator;
neither that validator nor any digest calculation is replaced by these tests.
"""
from contextlib import closing, contextmanager
from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from materials_query import computed_registry as registry
from test_computed_recovery import review_fixture as legacy_review
from test_computed_v2 import INPUT, review_fixture as rich_review


PIN_SHA256 = '259d5d0e87635fec6f87ce544c8a252494038cbb1643228eeb685d5501f17897'
INTEGRATED_PIN_SHA256 = 'f1a1e3e379f9b7befba595b54477f15a26364548798b28dd65be8bc4326c0df4'
PRE_EVIDENCE_BATCH_PIN_SHA256 = '3782f403f120f22b5287e01f4e207419e2f576a28dfda33a89a85580b936c0f6'
PRE_GROWTH_BATCH_PIN_SHA256 = '8fda4f7a4355c88f0e4e9e713c01f236a907985b4720454e338d8d95eff4770e'
PRE_PUR_BATCH_PIN_SHA256 = '0d2f515260b78841249f5b48331f8a80fc9164bd58bb57c592f7adfed3d96277'
PRE_TABLE_BATCH_PIN_SHA256 = '73b8b455042290c0f752e784f23687eaf3bbc8dc7631ced311af7af216f08d6e'
PRE_RCA_BATCH_PIN_SHA256 = '9090f061483cefde2d6255f057078b7700d3e22c85db7191ec00bc30de78f2ad'
PRE_BINARY_BATCH_PIN_SHA256 = '148c38cfa1819b8103ffa6c0f856d824b9fc54a3e9f8a5eecc50943fd19b27bd'
PRE_MTIBE_BATCH_PIN_SHA256 = '15c0619c3a55984550ecd564692c4588f777a10d60a4e9a01b91079c12978c2f'
PRE_NR_BATCH_PIN_SHA256 = 'c127bf69ccca825e1b2ca3fd496f6ead65bf68478fc232d27f087b7e551b6909'
PRE_NBR_BATCH_PIN_SHA256 = '7dd99df2a6ec06d6a0d6f72b31378cff5b49908113df4d78bee2ee3ffec09112'
PRE_OUTOKUMPU_BATCH_PIN_SHA256 = '8c47bf8592437932508298417ed4c6e93e92091a0e25266bee3816acec797da8'
PRE_FILAMENT_BATCH_PIN_SHA256 = 'b228d514b2b1dbb8bad428d6f0be7f300947ee2e1c3c64a6f9f0e55df132ade7'
PRE_TOUGH_PLA_PIN_SHA256 = '393af99b3a9ef08e6d73c87bde302af74e66dd59628e86b368b88882462057a5'
PRE_NYLON_PIN_SHA256 = 'a6b5e9835807a397c81f668cb3c1f19fe70d62074899bdf6365892543220d4b2'
PRE_BRUNS_PIN_SHA256 = '124044eb8afcaf927ec9ff4770da66dfedc641391cd58e4b873735ee7424db4e'
PRE_TARASOV_PIN_SHA256 = '09b57c7410b7b6c858abd566153dd932a451c9b5d4ed56b0963cbe4064543a05'
CURRENT_PIN_SHA256 = 'f77658c4df1434de7dd9d9d8d0e9d4ab31eef200477ec748f80c1a7acd371dbf'
GROWTH_ROOT = Path(__file__).resolve().parents[4]
GROWTH_LEDGER = GROWTH_ROOT / 'tests/fixtures/source_family_growth_data_20261019.json'
GROWTH_LEDGER_SHA256 = '9dfc8d71e89041f05e11a870ad29aea34cb3ab90586bcea8f1d717adc9878ac3'
GROWTH_PACKET = GROWTH_ROOT / 'experimental/material-batches/nbs-oxide-density-20261019/prepared-packet.json'
GROWTH_PACKET_SHA256 = '21aaed2df59b0ab9301d1573aabd6fd8bd87354c01fdf11323cdee62b600aab3'
PRE_GROWTH_BATCH_DATA_SHA256 = {
    'materials.json': '410efabb24dad7ed377ac7b94d35bccc40afe91194f0323e0298f500314e02f3',
    'reference_properties.json': 'c3f69e692a0dfb4ced72aea30794a7ee7b032ac99231db517397e0575dbc4bb0',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
GROWTH_COLLECTIONS = (
    ('materials.json', 'materials', 'identities', 'identities'),
    ('materials.json', 'materials', 'grades', 'grades'),
    ('materials.json', 'materials', 'records', 'states'),
    ('reference_properties.json', 'properties', 'records', 'properties'),
    ('sources.json', 'sources', 'records', 'sources'),
)
PUR_LEDGER = GROWTH_ROOT / 'tests/fixtures/pur_formulation_data_20261019.json'
PUR_LEDGER_SHA256 = '541a4e325834ed992246489846bcfcf83480bfb86494ec2a212d78de821bf167'
PUR_PACKET = GROWTH_ROOT / 'experimental/material-batches/pur-formulations-20261019/prepared-packet.json'
PUR_PACKET_SHA256 = '2c5320856ba07892eac6b35d6b881bb3ab21126e801beefa2b887c77abd93be7'
PRE_PUR_BATCH_DATA_SHA256 = {
    'materials.json': '1241e7e60513cbf1df4929d4b2bbc972b8b6a1c592e22cfbfa1c9e39ce8a7471',
    'reference_properties.json': '5d275d4de23a2fe28541c739b91c1c496ab4bc69ed63f8843fc5a1902c72025d',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
TABLE_LEDGER = GROWTH_ROOT / 'tests/fixtures/primary_table_growth_data_20261019.json'
TABLE_LEDGER_SHA256 = 'faa453c3d57bb4a9040fac084cb9a96ad6c3437c237f80ea8eff4cc3e3fe261f'
TABLE_PACKET = GROWTH_ROOT / 'experimental/material-batches/nbs-salt-densities-20261019/prepared-packet.json'
TABLE_PACKET_SHA256 = '091239fd1cc6e4d7d8429aab381f1a9525f62293339fc4fbea230142f53b541f'
PRE_TABLE_BATCH_DATA_SHA256 = {
    'materials.json': 'e0ee99ff62bb2d982a260da2a89f6d8b3068277ac9ba304aad4f2669810b9598',
    'reference_properties.json': '03e76d2afa3854ecb9cf5c745f9af59b3abb76fe6d6f8e7430cd25648b5478f2',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
RCA_LEDGER = GROWTH_ROOT / 'tests/fixtures/primary_table_growth_2_data_20261019.json'
RCA_LEDGER_SHA256 = 'f3fcc3e8fdcdb292a2f3cf0b13c50de6bc90604ed2ac28b8938c9334e45933fc'
RCA_PACKET = GROWTH_ROOT / 'experimental/material-batches/nbs-rca-density-20261019/prepared-packet.json'
RCA_PACKET_SHA256 = '6d906eec144e3908941f7c6f3c91646d4d905a7134fdc5086a95c4e59f1ca41c'
PRE_RCA_BATCH_DATA_SHA256 = {
    'materials.json': '86a5e6253ebb6a93154fef86280b94efd332a5a2eab8eb6c92827ce4e25c6590',
    'reference_properties.json': '6c6007825f5e3a4942f434a52e0fed9f5a039a9e80a30fbbd7f4d0225b61a91f',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
BINARY_LEDGER = GROWTH_ROOT / 'tests/fixtures/primary_table_growth_3_data_20261019.json'
BINARY_LEDGER_SHA256 = '4ae9986cc914d9ff06a40875c19d606c0502a28527488151e6c71ec5f27eb0fe'
BINARY_PACKET = GROWTH_ROOT / 'experimental/material-batches/nbs-binary-oxide-density-20261019/prepared-packet.json'
BINARY_PACKET_SHA256 = '0511e82ef9279928629f8e05076ba5050988de4e18081593d3bb8cbd1bfaa28e'
PRE_BINARY_BATCH_DATA_SHA256 = {
    'materials.json': '0113657bc3c6ac7acf82944198f0be3c3c245fc8d59575194fd676fe1dbfe522',
    'reference_properties.json': 'f9caa99826b7bb2436974f3550bc9076c80363606491ae3454c7b26baac46f69',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
MTIBE_LEDGER = GROWTH_ROOT / 'tests/fixtures/primary_table_growth_4_data_20261019.json'
MTIBE_LEDGER_SHA256 = 'd57a1014e6d9e66f3f6c031e3a56abda909acc924fb9ab16835948989f4ce89c'
MTIBE_PACKET = GROWTH_ROOT / 'experimental/material-batches/mtibe-pbs-pbat-hybrids-20261019/prepared-packet.json'
MTIBE_PACKET_SHA256 = '8c0dad86412f0708f72a3866cae5a7766db01be99df38f85defd3ba052da388c'
PRE_MTIBE_BATCH_DATA_SHA256 = {
    'materials.json': 'd7517f3c4abb76e7275a7291381459e2123eb165d67710744209a979ef20f61b',
    'reference_properties.json': '4ca430bf31f24321527f42098b0009aa2648efa14c794c4a6e93617fca9f54b0',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
NR_LEDGER = GROWTH_ROOT / 'tests/fixtures/primary_table_growth_5_data_20261020.json'
NR_LEDGER_SHA256 = 'ced45ed6989e8988d461b0256c3ef7781c0f04b8364c6c991e3cacf36b064ff9'
NR_PACKET = GROWTH_ROOT / 'experimental/material-batches/bianchi-nr-nanoclay-20261020/prepared-packet.json'
NR_PACKET_SHA256 = 'a09f6d768b71667e045efa85d3c79de8ce3db49a926dcda55eb5421efc99d55f'
PRE_NR_BATCH_DATA_SHA256 = {
    'materials.json': 'ef824b85d31554f5d72aa1de7463d7d8187168419709dd676b7aee35cca433ee',
    'reference_properties.json': '2074da4cb05a106d338a704bb11c5d448cd476bb5b110def3d4cce358f5013be',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
NBR_LEDGER = GROWTH_ROOT / 'tests/fixtures/primary_table_growth_6_data_20261020.json'
NBR_LEDGER_SHA256 = '3d3335edadae838524756ad1b33efb733d48893a123e6637c461dc79d59861b5'
NBR_PACKET = GROWTH_ROOT / 'experimental/material-batches/tamas-benyei-nbr-rcf-20261020/prepared-packet.json'
NBR_PACKET_SHA256 = 'ae401d2ab8b565acf5772bba10833176f46293ec025a9552d15aafd6a68c8ee3'
PRE_NBR_BATCH_DATA_SHA256 = {
    'materials.json': '8d5489af4e090f5310c22d21c6f385020f6d9b1d097b3d4b6ac964178e6afa81',
    'reference_properties.json': 'd0e0ad9c2036b4617842525951db51257623c564ad4b1ffcfaa36eaa28481407',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
OUTOKUMPU_LEDGER = GROWTH_ROOT / 'tests/fixtures/primary_table_growth_7_data_20261020.json'
OUTOKUMPU_LEDGER_SHA256 = '26c80c5274504af2e0adbb55b4346d395e7c13e7009c504229f9c9dc32ca01fe'
OUTOKUMPU_PACKET = GROWTH_ROOT / 'experimental/material-batches/outokumpu-core-moduli-20261020/prepared-packet.json'
OUTOKUMPU_PACKET_SHA256 = 'c7317758ae4c1a4025ac00c6b288770e61cf33056caaf1771a638af66d32b84f'
PRE_OUTOKUMPU_BATCH_DATA_SHA256 = {
    'materials.json': 'f32c62bab9e950f8cd4f3fbe19c3c5b9a8e915a0e086be48c7108b54b8f30312',
    'reference_properties.json': '9a9cdfebe0f660d7a6266f8a7b51fb99b23bc7996fff58564cbe9f05ae6c91f2',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
FILAMENT_LEDGER = GROWTH_ROOT / 'tests/fixtures/primary_table_growth_8_data_20261021.json'
FILAMENT_LEDGER_SHA256 = 'de662ffe08378402a224b4ee4180252b620278dfb79164b58a20884d68e82c51'
FILAMENT_PACKET = GROWTH_ROOT / 'experimental/material-batches/zenodo-8089569-filaments-20261021/prepared-packet.json'
FILAMENT_PACKET_SHA256 = 'aaa94bd1f752e00f37268f8b786326dcb98011648985f8bc77cb92362f4c57e8'
PRE_FILAMENT_BATCH_DATA_SHA256 = {
    'materials.json': 'e784d9deffb496ff097f3b888c9e16e0fb64780272644aa6a6731d5cd5233b5d',
    'reference_properties.json': '81a7af1d8f522c41307fedbf0e3258b2b1cdaa40b142b4d4982544a17a5d727b',
    'sources.json': '4ba9dcd9258cd1e2d9e17bdf20b4fdaa39e081e77779d12eb726ee91b19835ae',
}
TOUGH_PLA_LEDGER = GROWTH_ROOT / 'tests/fixtures/tough_pla_followup_data_20261021.json'
TOUGH_PLA_LEDGER_SHA256 = '46d33c7bfc8abb32b341a5c026ed8cb03e47350feeb17e2b0c478999aeacf1f4'
TOUGH_PLA_PACKET = GROWTH_ROOT / 'experimental/material-batches/zenodo-8089569-tough-pla-followup-20261021/prepared-packet.json'
TOUGH_PLA_PACKET_SHA256 = '919c387b4cf0b586c36e2d922a45b0a64832831d659f755049a4be3bbea3be44'
PRE_TOUGH_PLA_DATA_SHA256 = {
    'materials.json': '07ee36eaffda8a76dbffe275caa7b875dfa7a3dbcb0bfb642003c55330b5b223',
    'reference_properties.json': 'b46d6a378e8e1195a99514954e75060dd3992703069ea655f66f0638171f8170',
    'sources.json': '8a045cfc13fc62f292ca3e488edf6823045721b9f884967773eba1707faabe1c',
}
NYLON_LEDGER = GROWTH_ROOT / 'tests/fixtures/nylon_followup_data_20261021.json'
NYLON_LEDGER_SHA256 = '88f7303d6e8b4234555548ea39fdfb286380c72ea2f7f5edce990e1a0d733b97'
NYLON_PACKET = GROWTH_ROOT / 'experimental/material-batches/zenodo-8089569-nylon-followup-20261021/prepared-packet.json'
NYLON_PACKET_SHA256 = 'b18d7fc70bc5da537672f20a1682594c36c8d2d1e4c9e0ac05f9647d586e5172'
PRE_NYLON_DATA_SHA256 = {
    'materials.json': 'a3dc74dc74dfd6c667ab44bd127379f37d9b79f4b3e79c1051d3474e75c4db56',
    'reference_properties.json': '0bc8608de3150e11b578e151d2c6d3b8f6179c9136ef10b4eff7ffce62d9afb1',
    'sources.json': '6e23776fd59ac3f8153f589378b00877c80cbe4d061aa22e3bc41f358daf373f',
}
BRUNS_LEDGER = GROWTH_ROOT / 'tests/fixtures/bruns_borosilicate_data_20261023.json'
BRUNS_LEDGER_SHA256 = '6eded8614db38dcd26ad1e570d7ad783110dd690296e59a9270300bfd3a0a016'
BRUNS_PACKET = GROWTH_ROOT / 'experimental/material-batches/bruns-nbs2-borosilicate-20261023/prepared-packet.json'
BRUNS_PACKET_SHA256 = '7bc0fb2ba2dc3512abb95b7bf27b9f25d12c868d4bba041f667421572e5eccde'
PRE_BRUNS_DATA_SHA256 = {
    'materials.json': 'd228c3b8f0c45fd56809891213d1d1acd73964357b579c51f8b9c731031a3ec5',
    'reference_properties.json': '66802278a29cdcc4a5fe468b5681d87893a8a10a7c6c4c57f83c4753fe807839',
    'sources.json': '67e068041af0cd8dbaba1126e6ffe2e39d2f8d26f8d2c8ceefc42240e5eefe76',
}
TARASOV_LEDGER = GROWTH_ROOT / 'tests/fixtures/tarasov_pna_bpf_data_20261023.json'
TARASOV_LEDGER_SHA256 = 'ff13299c063b805d4cb36e73fe8db1521e88cab51aff2af13d2f4afab0a30773'
TARASOV_PACKET = GROWTH_ROOT / 'experimental/material-batches/tarasov-pna-bpf-20261023/prepared-packet.json'
TARASOV_PACKET_SHA256 = 'e9096077c7d6a206cf3a54a14272f838722187e10481588a1e3c07e5ab345997'
PRE_TARASOV_DATA_SHA256 = {
    'materials.json': '9df59cfdf94b35854255222d2a75f419859b269c5670c8eb18d8e9dc5eaa7a70',
    'reference_properties.json': '728c863756c35860b4dee25b64f5df10c1b5273bcb83ed1f35d60cf6ad85aa77',
    'sources.json': 'c06c9bcee46eac59839c51f84b252970f1da46f98cf2f2c08de0b33479b5ba71',
}
PRE_EVIDENCE_BATCH_DATA_SHA256 = {
    'materials.json': '193f431190af502eb5c2121ff077bf59ddc9b708ae5ad786160bdc8287c83c83',
    'reference_properties.json': '03f9d1062c7e94f6c5078eea2309f016da0eac1c305fde6afeff1029757bf22d',
    'sources.json': '3d8b8c6d4891400504ea9bedbafaa06d05698b5324e9cbd7f5686ebc1ac1736f',
}
EVIDENCE_BATCH_PACKET = (Path(__file__).resolve().parents[4] / 'experimental'
    / 'material-batches/20261019-pa12-source-family/prepared-packet.json')
EVIDENCE_BATCH_PACKET_SHA256 = '50f979965279a87410843518040429a59cc32a2204a5926478126024b32bc08c'
EVIDENCE_BATCH_COLLECTIONS = (
    ('materials.json', 'materials', 'identities'),
    ('materials.json', 'materials', 'grades'),
    ('materials.json', 'materials', 'records'),
    ('reference_properties.json', 'properties', 'records'),
    ('sources.json', 'sources', 'records'),
)
A592_DATA_SHA256 = {
    'materials.json': 'd078f1fb726289bdd6c7faff6f9a4a84d46eed5cd83ba586cd9c2f6ae0256739',
    'reference_properties.json': '4a5242f87beab3e07b0e5667e2fdb77b4b984baa71468978aec01092bb0aaad8',
    'sources.json': '3d8b8c6d4891400504ea9bedbafaa06d05698b5324e9cbd7f5686ebc1ac1736f',
}
# Independent of candidate manifests and core preservation helpers so these
# checks also run against installed wheels without importing repository tests.
COMPOSITE_ADDITIONS = frozenset({
    'ewurum2025_pbs_lignin45', 'bianchi2022_epdm_h_p20',
    'bianchi2022_epdm_h_p40', 'bianchi2022_epdm_h_p60',
})
COMPOSITE_PROPERTIES = frozenset({
    'refprop_ewurum2025_pbs_lignin45_youngs_modulus',
    'refprop_bianchi2022_epdm_h_p20_mass_density',
    'refprop_bianchi2022_epdm_h_p40_mass_density',
    'refprop_bianchi2022_epdm_h_p60_mass_density',
})
HISTORICAL_DATA_SHA256 = {
    'materials.json': 'ffd27ae7a927494083cbdcb173847502283f9ff0f69b8b7321abe0b042824dc1',
    'reference_properties.json': '7430901a0f401aca384debb8706a124ac43ad6d043165beff1b8d186641fddef',
    'sources.json': '4240f52ef96bbe34a8a677e2f995296a6c72ac8ab14fc3f8978c043540fcef93',
}
# Fixed removals recover the actual 4c5656c resources. Candidate manifests cannot
# enlarge this set, and every recovered resource must match its historical hash.
INTEGRATED_ADDITIONS = frozenset({
    'mat_nbs1953_caf2_stockbarger_mit', 'mat_nbs1953_kcl_mallinckrodt_kyd1',
    'mat_nbs1953_lif_harshaw', 'mat_watanabe2026_niobium_cylinder',
    'mat_nbs1953_baf2', 'mat_nbs1953_kbr', 'mat_nbs1953_ki', 'mat_nbs1953_naf',
    'mat_nbs1953_ag', 'mat_nbs1953_pd', 'mat_nbs1953_sn', 'mat_nbs1953_au',
    'mat_nbs1953_pb', 'mat_nbs1953_pt', 'mat_nbs1953_ta', 'mat_nbs1953_kf',
    'mat_nbs1953_licl', 'mat_nbs1953_nh4cl', 'mat_domagala2024_nc2_concrete',
    'mat_ivdre2024_spo2_rigid_pur', 'mat_ewurum2025_pbs_lignin10',
    'mat_ewurum2025_pbs_lignin30',
})
PREDECESSOR_SHA256 = 'f485759f92bac90a655cbdf9328855c6a863552c258e645e63171dc3a625f82e'
SUCCESSOR_SHA256 = 'c22295a7e8ab4e360201eb57cb6fc13eba7f8b8ac5e419f35fcf42e8aa81a264'
PREDECESSOR_HUNK = b'''    """Stable factual signature; evidence/support array ordering is immaterial."""
    if isinstance(value, dict):
        return {key: _structural_signature(item, key) for key, item in sorted(value.items())}
    if isinstance(value, list):
        values = [_structural_signature(item) for item in value]
        if field in {"evidence", "supports"}:
'''
SUCCESSOR_HUNK = b'''    """Stable factual signature; repeated evidence and evidence/support order are immaterial."""
    if isinstance(value, dict):
        return {key: _structural_signature(item, key) for key, item in sorted(value.items())}
    if isinstance(value, list):
        values = [_structural_signature(item) for item in value]
        if field == "evidence":
            unique = {json.dumps(item, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":")): item for item in values}
            return [unique[key] for key in sorted(unique)]
        if field == "supports":
'''


PRESENTATION_PREDECESSOR_SHA256 = '55de108d53fea5ac74dbaad21807a8ff38247d534410d6513173664c56c7610c'
PRESENTATION_SUCCESSOR_SHA256 = 'd4a74cbf65db1f457b8df0e77ae56fa25379b3c5ff09fefb4a1e823cb9685050'
# Independent exact hunks; no production or preservation helper is imported.
PRESENTATION_REVERSE_EDITS = (
    (
        (
            b'from copy import deepcopy\n'
            b'import json\n'
            b'import math\n'
            b'\n'
            b'\n'
        ),
        (
            b'from copy import deepcopy\n'
            b'import json\n'
            b'\n'
            b'\n'
        ),
    ),
    (
        (
            b'\n'
            b'\n'
            b'def _same_json_value(left, right, depth=0):\n'
            b'    """Conservatively recognize unchanged plain JSON without coercing types."""\n'
            b'    if depth > 64 or type(left) is not type(right):\n'
            b'        return False\n'
            b'    if type(left) is dict:\n'
            b'        if (any(type(key) is not str for key in left)\n'
            b'                or any(type(key) is not str for key in right)\n'
            b'                or tuple(left) != tuple(right)):\n'
            b'            return False\n'
            b'        return all(_same_json_value(left[key], right[key], depth + 1) for key in left)\n'
            b'    if type(left) is list:\n'
            b'        return len(left) == len(right) and all(\n'
            b'            _same_json_value(a, b, depth + 1) for a, b in zip(left, right))\n'
            b'    if type(left) is float:\n'
            b'        return math.isfinite(left) and math.isfinite(right) and left.hex() == right.hex()\n'
            b'    if type(left) in (str, int, bool, type(None)):\n'
            b'        return left == right\n'
            b'    return False\n'
            b'\n'
            b'\n'
            b'def _resolved_graph(catalog: dict, kind: str) -> tuple[dict, dict, dict]:\n'
            b'    """Resolve a canonical subset against the complete validated offline graph.\n'
            b'\n'
            b'    Incoming records replace records of the same ID. Changed or uncertain\n'
            b'    inputs require full graph validation again. An exact unchanged subset\n'
            b'    reuses only the complete graph freshly read and validated in this call.\n'
            b'    Catalogues remain raw envelopes; resolved objects never become records.\n'
            b'    """\n'
        ),
        (
            b'\n'
            b'\n'
            b'def _resolved_graph(catalog: dict, kind: str) -> tuple[dict, dict, dict]:\n'
            b'    """Resolve a canonical subset against the complete validated offline graph.\n'
            b'\n'
            b'    Incoming records replace records of the same ID. The resulting entire\n'
            b'    graph is validated again, so display cannot bypass semantic protections.\n'
            b'    Catalogues remain raw envelopes; resolved objects never become records.\n'
            b'    """\n'
        ),
    ),
    (
        (
            b'    if not isinstance(catalog, dict) or set(catalog) != keys or catalog["schema_version"] != "1.0.0":\n'
            b'        raise ValueError("material presentation: invalid canonical catalogue envelope")\n'
            b'    original = materials if kind == "materials" else properties\n'
            b'    for key in keys - {"schema_version"}:\n'
            b'        incoming = catalog[key]\n'
        ),
        (
            b'    if not isinstance(catalog, dict) or set(catalog) != keys or catalog["schema_version"] != "1.0.0":\n'
            b'        raise ValueError("material presentation: invalid canonical catalogue envelope")\n'
            b'    target = deepcopy(materials if kind == "materials" else properties)\n'
            b'    for key in keys - {"schema_version"}:\n'
            b'        incoming = catalog[key]\n'
        ),
    ),
    (
        (
            b'        if len(identifiers) != len(set(identifiers)):\n'
            b'            raise ValueError(f"material presentation: duplicate {key} ID")\n'
            b'\n'
            b'    unchanged = (type(catalog) is dict and type(catalog["schema_version"]) is str\n'
            b'                 and all(type(key) is str for key in catalog))\n'
            b'    for key in keys - {"schema_version"}:\n'
            b'        incoming = catalog[key]\n'
            b'        if type(incoming) is not list:\n'
            b'            unchanged = False\n'
            b'            continue\n'
            b'        index = {item["id"]: (position, item) for position, item in enumerate(original[key])}\n'
            b'        previous_position = -1\n'
            b'        for item in incoming:\n'
            b'            if (type(item) is not dict or type(item["id"]) is not str\n'
            b'                    or item["id"] not in index):\n'
            b'                unchanged = False\n'
            b'                break\n'
            b'            position, original_item = index[item["id"]]\n'
            b'            if position <= previous_position or not _same_json_value(item, original_item):\n'
            b'                unchanged = False\n'
            b'                break\n'
            b'            previous_position = position\n'
            b'    if unchanged:\n'
            b'        return materials, properties, sources\n'
            b'\n'
            b'    target = deepcopy(original)\n'
            b'    for key in keys - {"schema_version"}:\n'
            b'        incoming = catalog[key]\n'
            b'        replacements = {item["id"]: item for item in incoming}\n'
            b'        existing = {item["id"] for item in target[key]}\n'
        ),
        (
            b'        if len(identifiers) != len(set(identifiers)):\n'
            b'            raise ValueError(f"material presentation: duplicate {key} ID")\n'
            b'        replacements = {item["id"]: item for item in incoming}\n'
            b'        existing = {item["id"] for item in target[key]}\n'
        ),
    ),
)


def manifest(root):
    return {p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and p.suffix in {'.py', '.json'}}


def frozen_append_inventory(descriptor):
    """Read a closed, pinned test descriptor independently of core recovery code."""
    label = descriptor['label']
    raw = descriptor['ledger'].read_bytes()
    if sha256(raw).hexdigest() != descriptor['ledger_sha256']:
        raise AssertionError(label + ' ledger bytes differ')
    ledger = json.loads(raw)
    names = {'materials.json': 'materials', 'reference_properties.json': 'properties',
             'sources.json': 'sources'}
    if (ledger['baseline_commit'] != descriptor['parent_commit']
            or ledger['baseline_sha256'] != {names[k]: v for k, v in descriptor['parent_data'].items()}
            or len(ledger['packets']) != 1):
        raise AssertionError(label + ' parent or packet inventory differs')
    packet_info = ledger['packets'][0]
    if (packet_info['path'] != descriptor['packet'].relative_to(GROWTH_ROOT).as_posix()
            or packet_info['sha256'] != descriptor['packet_sha256']):
        raise AssertionError(label + ' packet binding differs')
    raw = descriptor['packet'].read_bytes()
    if sha256(raw).hexdigest() != descriptor['packet_sha256']:
        raise AssertionError(label + ' packet bytes differ')
    packet = json.loads(raw)
    packet_parent = packet['input']['baseline_sha256']
    if packet_parent != {'materials': ledger['baseline_sha256']['materials'],
                         'reference_properties': ledger['baseline_sha256']['properties'],
                         'sources': ledger['baseline_sha256']['sources']}:
        raise AssertionError(label + ' packet parent resources differ')
    additions = {}
    for filename, section, collection, kind in GROWTH_COLLECTIONS:
        identifiers = packet_info['added_ids'][kind]
        rows = [row for row in packet['catalogs'][section][collection]
                if row['id'] in identifiers]
        if len(set(identifiers)) != len(identifiers) or len(rows) != len(identifiers):
            raise AssertionError(label + ' duplicate or missing addition')
        additions[kind] = rows
    if {kind: len(rows) for kind, rows in additions.items()} != descriptor['addition_counts']:
        raise AssertionError(label + ' exact addition counts differ')
    return ledger, additions


def recover_exact_append_catalogs(current, descriptor):
    """Accept only the complete predecessor or successor of one frozen append."""
    ledger, additions = frozen_append_inventory(descriptor)
    label = descriptor['label']
    names = {'materials.json': 'materials', 'reference_properties.json': 'properties',
             'sources.json': 'sources'}
    def hashes(catalogs):
        return {names[name]: sha256((json.dumps(value, ensure_ascii=False, indent=2,
                allow_nan=False) + '\n').encode('utf-8')).hexdigest()
                for name, value in catalogs.items()}
    actual = hashes(current)
    if actual == ledger['baseline_sha256']:
        return deepcopy(current)
    catalogs = deepcopy(current)
    for filename, section, collection, kind in GROWTH_COLLECTIONS:
        candidates = additions[kind]
        identifiers = {row['id'] for row in candidates}
        rows = catalogs[filename][collection]
        for candidate in candidates:
            matches = [row for row in rows if row['id'] == candidate['id']]
            if len(matches) != 1 or registry.canonical(matches[0]) != registry.canonical(candidate):
                raise AssertionError(label + ' requires every unchanged addition')
        # Shared source rows are absent from added_ids and always retained.
        catalogs[filename][collection] = [row for row in rows if row['id'] not in identifiers]
    if hashes(catalogs) != ledger['baseline_sha256']:
        raise AssertionError(label + ' predecessor catalog bytes differ')
    if actual != ledger['current_sha256']:
        raise AssertionError(label + ' successor catalog order or bytes differ')
    return catalogs


def growth_batch_descriptor():
    return {'label': 'Growth batch', 'ledger': GROWTH_LEDGER,
            'ledger_sha256': GROWTH_LEDGER_SHA256, 'packet': GROWTH_PACKET,
            'packet_sha256': GROWTH_PACKET_SHA256,
            'parent_commit': 'c90188dcd5ac3a19863be0b49419722571b17eff',
            'parent_data': PRE_GROWTH_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 6, 'grades': 0, 'states': 6,
                                'properties': 6, 'sources': 0}}


def growth_batch_inventory():
    return frozen_append_inventory(growth_batch_descriptor())


def recover_pre_growth_batch_catalogs(current):
    """Retain the exact c901-to-six-oxide scope; later appends are not accepted."""
    return recover_exact_append_catalogs(current, growth_batch_descriptor())


def pur_batch_descriptor():
    return {'label': 'PUR batch', 'ledger': PUR_LEDGER,
            'ledger_sha256': PUR_LEDGER_SHA256, 'packet': PUR_PACKET,
            'packet_sha256': PUR_PACKET_SHA256,
            'parent_commit': '2509ee231edb62872ed323e8346895bd55c36c92',
            'parent_data': PRE_PUR_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 2, 'grades': 0, 'states': 2,
                                'properties': 2, 'sources': 0}}


def pur_batch_inventory():
    return frozen_append_inventory(pur_batch_descriptor())


def recover_pre_pur_batch_catalogs(current):
    return recover_exact_append_catalogs(current, pur_batch_descriptor())


def table_batch_descriptor():
    return {'label': 'Table batch', 'ledger': TABLE_LEDGER,
            'ledger_sha256': TABLE_LEDGER_SHA256, 'packet': TABLE_PACKET,
            'packet_sha256': TABLE_PACKET_SHA256,
            'parent_commit': 'efd4ca2a64c6b389c2a1fa9ba525f6fa77bbe93f',
            'parent_data': PRE_TABLE_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 8, 'grades': 0, 'states': 8,
                                'properties': 8, 'sources': 0}}


def table_batch_inventory():
    return frozen_append_inventory(table_batch_descriptor())


def recover_pre_table_batch_catalogs(current):
    return recover_exact_append_catalogs(current, table_batch_descriptor())


def tarasov_descriptor():
    return {'label': 'Tarasov PNA-BPF', 'ledger': TARASOV_LEDGER,
            'ledger_sha256': TARASOV_LEDGER_SHA256, 'packet': TARASOV_PACKET,
            'packet_sha256': TARASOV_PACKET_SHA256,
            'parent_commit': 'faa002c55b7ad2d1bd962e905275894231ab8350',
            'parent_data': PRE_TARASOV_DATA_SHA256,
            'addition_counts': {'identities': 5, 'grades': 0, 'states': 5, 'properties': 5, 'sources': 1}}


def tarasov_inventory():
    return frozen_append_inventory(tarasov_descriptor())


def recover_pre_tarasov_catalogs(current):
    return recover_exact_append_catalogs(current, tarasov_descriptor())


def bruns_descriptor():
    return {'label': 'Bruns borosilicate', 'ledger': BRUNS_LEDGER,
            'ledger_sha256': BRUNS_LEDGER_SHA256, 'packet': BRUNS_PACKET,
            'packet_sha256': BRUNS_PACKET_SHA256,
            'parent_commit': '46674771ab851d4c267425b985c8f29c8aea25df',
            'parent_data': PRE_BRUNS_DATA_SHA256,
            'addition_counts': {'identities': 4, 'grades': 0, 'states': 4, 'properties': 4, 'sources': 1}}


def bruns_inventory():
    return frozen_append_inventory(bruns_descriptor())


def recover_pre_bruns_catalogs(current):
    return recover_exact_append_catalogs(current, bruns_descriptor())


def nylon_descriptor():
    return {'label': 'Nylon follow-up', 'ledger': NYLON_LEDGER,
            'ledger_sha256': NYLON_LEDGER_SHA256, 'packet': NYLON_PACKET,
            'packet_sha256': NYLON_PACKET_SHA256,
            'parent_commit': '2c8ddac78f5cd43dfa071ad23639b826561a043b',
            'parent_data': PRE_NYLON_DATA_SHA256,
            'addition_counts': {'identities': 1, 'grades': 0, 'states': 1, 'properties': 2, 'sources': 2}}

def nylon_inventory():
    return frozen_append_inventory(nylon_descriptor())

def recover_pre_nylon_catalogs(current):
    return recover_exact_append_catalogs(current, nylon_descriptor())

def tough_pla_descriptor():
    return {'label': 'Tough PLA follow-up', 'ledger': TOUGH_PLA_LEDGER,
            'ledger_sha256': TOUGH_PLA_LEDGER_SHA256, 'packet': TOUGH_PLA_PACKET,
            'packet_sha256': TOUGH_PLA_PACKET_SHA256,
            'parent_commit': '5cc1418392696dc8115581ad693dabfc2695422e',
            'parent_data': PRE_TOUGH_PLA_DATA_SHA256,
            'addition_counts': {'identities': 1, 'grades': 0, 'states': 2, 'properties': 4, 'sources': 1}}

def tough_pla_inventory():
    return frozen_append_inventory(tough_pla_descriptor())

def recover_pre_tough_pla_catalogs(current):
    return recover_exact_append_catalogs(current, tough_pla_descriptor())

def filament_batch_descriptor():
    return {'label': 'Filament batch', 'ledger': FILAMENT_LEDGER,
            'ledger_sha256': FILAMENT_LEDGER_SHA256, 'packet': FILAMENT_PACKET,
            'packet_sha256': FILAMENT_PACKET_SHA256,
            'parent_commit': '5e8d63dc9b7832cab893a5d849346d42b02e3c85',
            'parent_data': PRE_FILAMENT_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 8, 'grades': 0, 'states': 8, 'properties': 16, 'sources': 4}}

def filament_batch_inventory():
    return frozen_append_inventory(filament_batch_descriptor())

def recover_pre_filament_batch_catalogs(current):
    return recover_exact_append_catalogs(current, filament_batch_descriptor())

def outokumpu_batch_descriptor():
    return {'label': 'Outokumpu batch', 'ledger': OUTOKUMPU_LEDGER,
            'ledger_sha256': OUTOKUMPU_LEDGER_SHA256, 'packet': OUTOKUMPU_PACKET,
            'packet_sha256': OUTOKUMPU_PACKET_SHA256,
            'parent_commit': 'eee77b5033d7671bbaa2d3b4eca57c88d52fc411',
            'parent_data': PRE_OUTOKUMPU_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 10, 'grades': 10, 'states': 10,
                                'properties': 10, 'sources': 0}}

def outokumpu_batch_inventory():
    return frozen_append_inventory(outokumpu_batch_descriptor())

def recover_pre_outokumpu_batch_catalogs(current):
    return recover_exact_append_catalogs(current, outokumpu_batch_descriptor())

def nbr_batch_descriptor():
    return {'label': 'NBR batch', 'ledger': NBR_LEDGER,
            'ledger_sha256': NBR_LEDGER_SHA256, 'packet': NBR_PACKET,
            'packet_sha256': NBR_PACKET_SHA256,
            'parent_commit': 'f5bdcc44a4743f7da6220871dbf3857224a925b0',
            'parent_data': PRE_NBR_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 6, 'grades': 0, 'states': 6,
                                'properties': 6, 'sources': 0}}

def nbr_batch_inventory():
    return frozen_append_inventory(nbr_batch_descriptor())

def recover_pre_nbr_batch_catalogs(current):
    return recover_exact_append_catalogs(current, nbr_batch_descriptor())

def nr_batch_descriptor():
    return {'label': 'NR batch', 'ledger': NR_LEDGER,
            'ledger_sha256': NR_LEDGER_SHA256, 'packet': NR_PACKET,
            'packet_sha256': NR_PACKET_SHA256,
            'parent_commit': '8981840519f611e62490ce4e9a614381201fe7e3',
            'parent_data': PRE_NR_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 6, 'grades': 0, 'states': 6,
                                'properties': 6, 'sources': 0}}

def nr_batch_inventory():
    return frozen_append_inventory(nr_batch_descriptor())

def recover_pre_nr_batch_catalogs(current):
    return recover_exact_append_catalogs(current, nr_batch_descriptor())

def mtibe_batch_descriptor():
    return {'label': 'Mtibe batch', 'ledger': MTIBE_LEDGER,
            'ledger_sha256': MTIBE_LEDGER_SHA256, 'packet': MTIBE_PACKET,
            'packet_sha256': MTIBE_PACKET_SHA256,
            'parent_commit': 'a5cc3f6c47954033db5de7f50220d182cfcff459',
            'parent_data': PRE_MTIBE_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 3, 'grades': 0, 'states': 3,
                                'properties': 3, 'sources': 0}}

def mtibe_batch_inventory():
    return frozen_append_inventory(mtibe_batch_descriptor())

def recover_pre_mtibe_batch_catalogs(current):
    return recover_exact_append_catalogs(current, mtibe_batch_descriptor())

def binary_batch_descriptor():
    return {'label': 'Binary batch', 'ledger': BINARY_LEDGER,
            'ledger_sha256': BINARY_LEDGER_SHA256, 'packet': BINARY_PACKET,
            'packet_sha256': BINARY_PACKET_SHA256,
            'parent_commit': '4db4ab591c0ee7b0a3580898b9f2ec75a2a52337',
            'parent_data': PRE_BINARY_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 6, 'grades': 0, 'states': 6,
                                'properties': 6, 'sources': 0}}

def binary_batch_inventory():
    return frozen_append_inventory(binary_batch_descriptor())

def recover_pre_binary_batch_catalogs(current):
    return recover_exact_append_catalogs(current, binary_batch_descriptor())

def rca_batch_descriptor():
    return {'label': 'RCA batch', 'ledger': RCA_LEDGER,
            'ledger_sha256': RCA_LEDGER_SHA256, 'packet': RCA_PACKET,
            'packet_sha256': RCA_PACKET_SHA256,
            'parent_commit': '799ca7a74fe1d0d92ac588b08350a39e2d0a9a79',
            'parent_data': PRE_RCA_BATCH_DATA_SHA256,
            'addition_counts': {'identities': 3, 'grades': 0, 'states': 3,
                                'properties': 3, 'sources': 0}}


def rca_batch_inventory():
    return frozen_append_inventory(rca_batch_descriptor())


def recover_pre_rca_batch_catalogs(current):
    return recover_exact_append_catalogs(current, rca_batch_descriptor())


def evidence_batch_catalogs():
    """Read the immutable append graph without importing a compiler or core helper."""
    raw = EVIDENCE_BATCH_PACKET.read_bytes()
    if sha256(raw).hexdigest() != EVIDENCE_BATCH_PACKET_SHA256:
        raise AssertionError('Evidence batch packet bytes differ')
    packet = json.loads(raw)
    expected = {name.removesuffix('.json'): digest
                for name, digest in PRE_EVIDENCE_BATCH_DATA_SHA256.items()}
    if packet['input']['baseline_sha256'] != expected:
        raise AssertionError('Evidence batch parent resource pins differ')
    return packet['catalogs']


def recover_pre_evidence_batch_catalogs(current):
    """Recover exact 12cb bytes only from the whole pinned append graph or parent."""
    appended = evidence_batch_catalogs()
    catalogs = deepcopy(current)
    observed, required = 0, 0
    for filename, section, collection in EVIDENCE_BATCH_COLLECTIONS:
        candidates = appended[section][collection]
        identifiers = {row['id'] for row in candidates}
        if len(identifiers) != len(candidates):
            raise AssertionError('Evidence batch duplicate candidate IDs')
        required += len(candidates)
        rows = catalogs[filename][collection]
        for candidate in candidates:
            matches = [row for row in rows if row['id'] == candidate['id']]
            if len(matches) > 1 or (matches and registry.canonical(matches[0]) != registry.canonical(candidate)):
                raise AssertionError('Evidence batch candidate rows differ')
            observed += len(matches)
        catalogs[filename][collection] = [row for row in rows if row['id'] not in identifiers]
    if not required or observed not in (0, required):
        raise AssertionError('Evidence batch is incomplete')
    for name, expected in PRE_EVIDENCE_BATCH_DATA_SHA256.items():
        raw = (json.dumps(catalogs[name], ensure_ascii=False, indent=2,
                          allow_nan=False) + '\n').encode('utf-8')
        if sha256(raw).hexdigest() != expected:
            raise AssertionError('Recovered pre-evidence-batch catalog bytes differ: ' + name)
    return catalogs


def recover_a592_catalogs(current):
    """Remove only this fixed batch and require every parent resource byte."""
    catalogs = deepcopy(current)
    materials = catalogs['materials.json']
    identities = {'mat_' + suffix for suffix in COMPOSITE_ADDITIONS}
    states = {'state_' + suffix for suffix in COMPOSITE_ADDITIONS}
    materials['identities'] = [row for row in materials['identities']
                              if row['id'] not in identities]
    materials['records'] = [row for row in materials['records'] if row['id'] not in states]
    catalogs['reference_properties.json']['records'] = [
        row for row in catalogs['reference_properties.json']['records']
        if row['id'] not in COMPOSITE_PROPERTIES]
    for name, expected in A592_DATA_SHA256.items():
        raw = (json.dumps(catalogs[name], ensure_ascii=False, indent=2,
                          allow_nan=False) + '\n').encode('utf-8')
        if sha256(raw).hexdigest() != expected:
            raise AssertionError('Recovered a592 catalog bytes differ: ' + name)
    return catalogs


class BaselineCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.fixture.cleanup)
        cls.fixture_root = Path(cls.fixture.name)
        cls.current_root = cls.fixture_root / 'current'
        cls.dedup_root = cls.fixture_root / 'dedup-predecessor'
        cls.original_root = cls.fixture_root / 'original'
        installed_root = Path(files('materials_boundaries'))
        for source in installed_root.rglob('*'):
            if source.is_file() and source.suffix in {'.py', '.json'}:
                target = cls.current_root / source.relative_to(installed_root)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
        raw = (cls.current_root / 'material_references.py').read_bytes()
        if sha256(raw).hexdigest() != SUCCESSOR_SHA256 or raw.count(SUCCESSOR_HUNK) != 1:
            raise AssertionError('Compatibility tests require the exact reviewed successor bytes')
        predecessor = raw.replace(SUCCESSOR_HUNK, PREDECESSOR_HUNK)
        if sha256(predecessor).hexdigest() != PREDECESSOR_SHA256:
            raise AssertionError('Reconstructed predecessor differs from the historical anchor')
        presentation = (cls.current_root / 'material_presentation.py').read_bytes()
        if sha256(presentation).hexdigest() != PRESENTATION_SUCCESSOR_SHA256:
            raise AssertionError('Compatibility tests require the exact presentation successor')
        for after, before in PRESENTATION_REVERSE_EDITS:
            if presentation.count(after) != 1:
                raise AssertionError('Presentation reversal hunk differs from the reviewed bytes')
            presentation = presentation.replace(after, before)
        if sha256(presentation).hexdigest() != PRESENTATION_PREDECESSOR_SHA256:
            raise AssertionError('Reconstructed presentation differs from the historical anchor')
        shutil.copytree(cls.current_root, cls.dedup_root)
        (cls.dedup_root / 'material_presentation.py').write_bytes(presentation)
        shutil.copytree(cls.dedup_root, cls.original_root)
        (cls.original_root / 'material_references.py').write_bytes(predecessor)
        cls.pin_bytes = files('materials_query').joinpath('pins/legacy_baseline.json').read_bytes()
        if sha256(cls.pin_bytes).hexdigest() != CURRENT_PIN_SHA256:
            raise AssertionError('Current data pin bytes differ from the reviewed increment')
        cls.expected = json.loads(cls.pin_bytes)
        cls.original_identity = sha256(json.dumps(
            cls.expected, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
            allow_nan=False).encode()).hexdigest()
        cls.recover_tarasov_anchor()
        cls.recover_bruns_anchor()
        cls.recover_nylon_anchor()
        cls.recover_tough_pla_anchor()
        cls.recover_filament_anchor()
        cls.recover_outokumpu_anchor()
        cls.recover_nbr_anchor()
        cls.recover_nr_anchor()
        cls.recover_mtibe_anchor()
        cls.recover_binary_anchor()
        cls.recover_rca_anchor()
        cls.recover_table_anchor()
        cls.recover_pur_anchor()
        cls.recover_growth_anchor()
        cls.recover_integrated_anchor()
        cls.recover_historical_anchor()

    @classmethod
    def recover_tarasov_anchor(cls):
        """Recover the exact faa002c data before the unchanged Bruns anchor."""
        cls.tarasov_parent_root = cls.fixture_root / 'pre-tarasov-batch-data'
        shutil.copytree(cls.original_root, cls.tarasov_parent_root)
        data_root = cls.tarasov_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_TARASOV_DATA_SHA256}
        for name, value in recover_pre_tarasov_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.tarasov_parent_pin = registry.canonical(manifest(cls.tarasov_parent_root))
        if sha256(cls.tarasov_parent_pin).hexdigest() != PRE_TARASOV_PIN_SHA256:
            raise AssertionError('Recovered faa002c complete pin bytes differ')
        cls.tarasov_parent_query_root = cls.fixture_root / 'pre-tarasov-batch-query'
        (cls.tarasov_parent_query_root / 'pins').mkdir(parents=True)
        (cls.tarasov_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.tarasov_parent_pin)

    @classmethod
    def recover_bruns_anchor(cls):
        """Recover the exact 4667477 data and complete pin before older append layers."""
        cls.bruns_parent_root = cls.fixture_root / 'pre-bruns-batch-data'
        shutil.copytree(cls.tarasov_parent_root, cls.bruns_parent_root)
        data_root = cls.bruns_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_BRUNS_DATA_SHA256}
        for name, value in recover_pre_bruns_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.bruns_parent_pin = registry.canonical(manifest(cls.bruns_parent_root))
        if sha256(cls.bruns_parent_pin).hexdigest() != PRE_BRUNS_PIN_SHA256:
            raise AssertionError('Recovered 4667477 complete pin bytes differ')
        cls.bruns_parent_query_root = cls.fixture_root / 'pre-bruns-batch-query'
        (cls.bruns_parent_query_root / 'pins').mkdir(parents=True)
        (cls.bruns_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.bruns_parent_pin)

    @classmethod
    def recover_nylon_anchor(cls):
        """Recover the exact 2c8ddac data and complete pin before older append layers."""
        cls.nylon_parent_root = cls.fixture_root / 'pre-nylon-batch-data'
        shutil.copytree(cls.bruns_parent_root, cls.nylon_parent_root)
        data_root = cls.nylon_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_NYLON_DATA_SHA256}
        for name, value in recover_pre_nylon_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.nylon_parent_pin = registry.canonical(manifest(cls.nylon_parent_root))
        if sha256(cls.nylon_parent_pin).hexdigest() != PRE_NYLON_PIN_SHA256:
            raise AssertionError('Recovered 2c8ddac complete pin bytes differ')
        cls.nylon_parent_query_root = cls.fixture_root / 'pre-nylon-batch-query'
        (cls.nylon_parent_query_root / 'pins').mkdir(parents=True)
        (cls.nylon_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.nylon_parent_pin)

    @classmethod
    def recover_tough_pla_anchor(cls):
        """Recover the exact 5cc1418 data and complete pin before older append layers."""
        cls.tough_pla_parent_root = cls.fixture_root / 'pre-tough-pla-batch-data'
        shutil.copytree(cls.nylon_parent_root, cls.tough_pla_parent_root)
        data_root = cls.tough_pla_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_TOUGH_PLA_DATA_SHA256}
        for name, value in recover_pre_tough_pla_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.tough_pla_parent_pin = registry.canonical(manifest(cls.tough_pla_parent_root))
        if sha256(cls.tough_pla_parent_pin).hexdigest() != PRE_TOUGH_PLA_PIN_SHA256:
            raise AssertionError('Recovered 5cc1418 complete pin bytes differ')
        cls.tough_pla_parent_query_root = cls.fixture_root / 'pre-tough-pla-batch-query'
        (cls.tough_pla_parent_query_root / 'pins').mkdir(parents=True)
        (cls.tough_pla_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.tough_pla_parent_pin)

    @classmethod
    def recover_filament_anchor(cls):
        """Recover the exact 5e8d63d data and complete pin before older append layers."""
        cls.filament_parent_root = cls.fixture_root / 'pre-filament-batch-data'
        shutil.copytree(cls.tough_pla_parent_root, cls.filament_parent_root)
        data_root = cls.filament_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_FILAMENT_BATCH_DATA_SHA256}
        for name, value in recover_pre_filament_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.filament_parent_pin = registry.canonical(manifest(cls.filament_parent_root))
        if sha256(cls.filament_parent_pin).hexdigest() != PRE_FILAMENT_BATCH_PIN_SHA256:
            raise AssertionError('Recovered 5e8d63d complete pin bytes differ')
        cls.filament_parent_query_root = cls.fixture_root / 'pre-filament-batch-query'
        (cls.filament_parent_query_root / 'pins').mkdir(parents=True)
        (cls.filament_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.filament_parent_pin)

    @classmethod
    def recover_outokumpu_anchor(cls):
        """Recover the exact eee77b5 data and complete pin before older append layers."""
        cls.outokumpu_parent_root = cls.fixture_root / 'pre-outokumpu-batch-data'
        shutil.copytree(cls.filament_parent_root, cls.outokumpu_parent_root)
        data_root = cls.outokumpu_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_OUTOKUMPU_BATCH_DATA_SHA256}
        for name, value in recover_pre_outokumpu_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.outokumpu_parent_pin = registry.canonical(manifest(cls.outokumpu_parent_root))
        if sha256(cls.outokumpu_parent_pin).hexdigest() != PRE_OUTOKUMPU_BATCH_PIN_SHA256:
            raise AssertionError('Recovered eee77b5 complete pin bytes differ')
        cls.outokumpu_parent_query_root = cls.fixture_root / 'pre-outokumpu-batch-query'
        (cls.outokumpu_parent_query_root / 'pins').mkdir(parents=True)
        (cls.outokumpu_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.outokumpu_parent_pin)

    @classmethod
    def recover_nbr_anchor(cls):
        """Recover the exact f5bdcc4 data and complete pin before older append layers."""
        cls.nbr_parent_root = cls.fixture_root / 'pre-nbr-batch-data'
        shutil.copytree(cls.outokumpu_parent_root, cls.nbr_parent_root)
        data_root = cls.nbr_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_NBR_BATCH_DATA_SHA256}
        for name, value in recover_pre_nbr_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.nbr_parent_pin = registry.canonical(manifest(cls.nbr_parent_root))
        if sha256(cls.nbr_parent_pin).hexdigest() != PRE_NBR_BATCH_PIN_SHA256:
            raise AssertionError('Recovered f5bdcc4 complete pin bytes differ')
        cls.nbr_parent_query_root = cls.fixture_root / 'pre-nbr-batch-query'
        (cls.nbr_parent_query_root / 'pins').mkdir(parents=True)
        (cls.nbr_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.nbr_parent_pin)

    @classmethod
    def recover_nr_anchor(cls):
        """Recover the exact 8981840 data and complete pin before older append layers."""
        cls.nr_parent_root = cls.fixture_root / 'pre-nr-batch-data'
        shutil.copytree(cls.nbr_parent_root, cls.nr_parent_root)
        data_root = cls.nr_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_NR_BATCH_DATA_SHA256}
        for name, value in recover_pre_nr_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.nr_parent_pin = registry.canonical(manifest(cls.nr_parent_root))
        if sha256(cls.nr_parent_pin).hexdigest() != PRE_NR_BATCH_PIN_SHA256:
            raise AssertionError('Recovered 8981840 complete pin bytes differ')
        cls.nr_parent_query_root = cls.fixture_root / 'pre-nr-batch-query'
        (cls.nr_parent_query_root / 'pins').mkdir(parents=True)
        (cls.nr_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.nr_parent_pin)

    @classmethod
    def recover_mtibe_anchor(cls):
        """Recover the exact a5cc3f6 data and complete pin before older append layers."""
        cls.mtibe_parent_root = cls.fixture_root / 'pre-mtibe-batch-data'
        shutil.copytree(cls.nr_parent_root, cls.mtibe_parent_root)
        data_root = cls.mtibe_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_MTIBE_BATCH_DATA_SHA256}
        for name, value in recover_pre_mtibe_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.mtibe_parent_pin = registry.canonical(manifest(cls.mtibe_parent_root))
        if sha256(cls.mtibe_parent_pin).hexdigest() != PRE_MTIBE_BATCH_PIN_SHA256:
            raise AssertionError('Recovered a5cc3f6 complete pin bytes differ')
        cls.mtibe_parent_query_root = cls.fixture_root / 'pre-mtibe-batch-query'
        (cls.mtibe_parent_query_root / 'pins').mkdir(parents=True)
        (cls.mtibe_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.mtibe_parent_pin)

    @classmethod
    def recover_binary_anchor(cls):
        """Recover the exact 4db4ab5 data and complete pin before older append layers."""
        cls.binary_parent_root = cls.fixture_root / 'pre-binary-batch-data'
        shutil.copytree(cls.mtibe_parent_root, cls.binary_parent_root)
        data_root = cls.binary_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_BINARY_BATCH_DATA_SHA256}
        for name, value in recover_pre_binary_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.binary_parent_pin = registry.canonical(manifest(cls.binary_parent_root))
        if sha256(cls.binary_parent_pin).hexdigest() != PRE_BINARY_BATCH_PIN_SHA256:
            raise AssertionError('Recovered 4db4ab5 complete pin bytes differ')
        cls.binary_parent_query_root = cls.fixture_root / 'pre-binary-batch-query'
        (cls.binary_parent_query_root / 'pins').mkdir(parents=True)
        (cls.binary_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.binary_parent_pin)

    @classmethod
    def recover_rca_anchor(cls):
        """Recover the exact 799ca7a data and complete pin before older append layers."""
        cls.rca_parent_root = cls.fixture_root / 'pre-rca-batch-data'
        shutil.copytree(cls.binary_parent_root, cls.rca_parent_root)
        data_root = cls.rca_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_RCA_BATCH_DATA_SHA256}
        for name, value in recover_pre_rca_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.rca_parent_pin = registry.canonical(manifest(cls.rca_parent_root))
        if sha256(cls.rca_parent_pin).hexdigest() != PRE_RCA_BATCH_PIN_SHA256:
            raise AssertionError('Recovered 799ca7a complete pin bytes differ')
        cls.rca_parent_query_root = cls.fixture_root / 'pre-rca-batch-query'
        (cls.rca_parent_query_root / 'pins').mkdir(parents=True)
        (cls.rca_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.rca_parent_pin)

    @classmethod
    def recover_table_anchor(cls):
        """Recover the exact efd4ca2 data and complete pin before older append layers."""
        cls.table_parent_root = cls.fixture_root / 'pre-table-batch-data'
        shutil.copytree(cls.rca_parent_root, cls.table_parent_root)
        data_root = cls.table_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_TABLE_BATCH_DATA_SHA256}
        for name, value in recover_pre_table_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.table_parent_pin = registry.canonical(manifest(cls.table_parent_root))
        if sha256(cls.table_parent_pin).hexdigest() != PRE_TABLE_BATCH_PIN_SHA256:
            raise AssertionError('Recovered efd4ca2 complete pin bytes differ')
        cls.table_parent_query_root = cls.fixture_root / 'pre-table-batch-query'
        (cls.table_parent_query_root / 'pins').mkdir(parents=True)
        (cls.table_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.table_parent_pin)

    @classmethod
    def recover_pur_anchor(cls):
        """Recover the exact 2509 data and complete pin before older append layers."""
        cls.pur_parent_root = cls.fixture_root / 'pre-pur-batch-data'
        shutil.copytree(cls.table_parent_root, cls.pur_parent_root)
        data_root = cls.pur_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_PUR_BATCH_DATA_SHA256}
        for name, value in recover_pre_pur_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.pur_parent_pin = registry.canonical(manifest(cls.pur_parent_root))
        if sha256(cls.pur_parent_pin).hexdigest() != PRE_PUR_BATCH_PIN_SHA256:
            raise AssertionError('Recovered 2509 complete pin bytes differ')
        cls.pur_parent_query_root = cls.fixture_root / 'pre-pur-batch-query'
        (cls.pur_parent_query_root / 'pins').mkdir(parents=True)
        (cls.pur_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.pur_parent_pin)

    @classmethod
    def recover_growth_anchor(cls):
        """Recover the exact c901 data and complete pin before older append layers."""
        cls.growth_parent_root = cls.fixture_root / 'pre-growth-batch-data'
        shutil.copytree(cls.pur_parent_root, cls.growth_parent_root)
        data_root = cls.growth_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_GROWTH_BATCH_DATA_SHA256}
        for name, value in recover_pre_growth_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.growth_parent_pin = registry.canonical(manifest(cls.growth_parent_root))
        if sha256(cls.growth_parent_pin).hexdigest() != PRE_GROWTH_BATCH_PIN_SHA256:
            raise AssertionError('Recovered c901 complete pin bytes differ')
        cls.growth_parent_query_root = cls.fixture_root / 'pre-growth-batch-query'
        (cls.growth_parent_query_root / 'pins').mkdir(parents=True)
        (cls.growth_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.growth_parent_pin)

    @classmethod
    def recover_integrated_anchor(cls):
        """Recover the exact 12cb parent before the existing a592/historical chain."""
        cls.evidence_parent_root = cls.fixture_root / 'pre-evidence-batch-data'
        shutil.copytree(cls.growth_parent_root, cls.evidence_parent_root)
        data_root = cls.evidence_parent_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in PRE_EVIDENCE_BATCH_DATA_SHA256}
        for name, value in recover_pre_evidence_batch_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.evidence_parent_pin = registry.canonical(manifest(cls.evidence_parent_root))
        if sha256(cls.evidence_parent_pin).hexdigest() != PRE_EVIDENCE_BATCH_PIN_SHA256:
            raise AssertionError('Recovered pre-evidence-batch complete pin bytes differ')
        cls.evidence_parent_query_root = cls.fixture_root / 'pre-evidence-batch-query'
        (cls.evidence_parent_query_root / 'pins').mkdir(parents=True)
        (cls.evidence_parent_query_root / 'pins/legacy_baseline.json').write_bytes(cls.evidence_parent_pin)
        cls.integrated_root = cls.fixture_root / 'a592-data'
        shutil.copytree(cls.evidence_parent_root, cls.integrated_root)
        data_root = cls.integrated_root / 'data'
        current = {name: json.loads((data_root / name).read_bytes())
                   for name in A592_DATA_SHA256}
        for name, value in recover_a592_catalogs(current).items():
            (data_root / name).write_bytes((json.dumps(value, ensure_ascii=False,
                indent=2, allow_nan=False) + '\n').encode('utf-8'))
        cls.integrated_pin = registry.canonical(manifest(cls.integrated_root))
        if sha256(cls.integrated_pin).hexdigest() != INTEGRATED_PIN_SHA256:
            raise AssertionError('Recovered a592 complete pin bytes differ')
        cls.integrated_query_root = cls.fixture_root / 'a592-query'
        (cls.integrated_query_root / 'pins').mkdir(parents=True)
        (cls.integrated_query_root / 'pins/legacy_baseline.json').write_bytes(cls.integrated_pin)

    @classmethod
    def recover_historical_anchor(cls):
        """Reconstruct historical bytes without changing a production trust pin."""
        cls.historical_root = cls.fixture_root / 'historical-data'
        shutil.copytree(cls.integrated_root, cls.historical_root)
        data_root = cls.historical_root / 'data'
        catalogs = {name: json.loads((data_root / name).read_bytes())
                    for name in HISTORICAL_DATA_SHA256}
        materials = catalogs['materials.json']
        found = {row['id'] for row in materials['identities']
                 if row['id'] in INTEGRATED_ADDITIONS}
        if len(INTEGRATED_ADDITIONS) != 22 or found != INTEGRATED_ADDITIONS:
            raise AssertionError('Integrated identity removals differ from the fixed set')
        states = {row['id'] for row in materials['records']
                  if row['identity_id'] in INTEGRATED_ADDITIONS}
        properties = catalogs['reference_properties.json']['records']
        if len(states) != 22 or sum(row['material_state_id'] in states
                                    for row in properties) != 22:
            raise AssertionError('Integrated state/property removals differ from the fixed set')
        materials['identities'] = [row for row in materials['identities']
                                  if row['id'] not in INTEGRATED_ADDITIONS]
        materials['records'] = [row for row in materials['records'] if row['id'] not in states]
        catalogs['reference_properties.json']['records'] = [
            row for row in properties if row['material_state_id'] not in states]
        catalogs['sources.json']['records'] = [row for row in catalogs['sources.json']['records']
            if row['id'] != 'watanabe2026_niobium_thermophysical']
        for name, value in catalogs.items():
            raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
            if sha256(raw).hexdigest() != HISTORICAL_DATA_SHA256[name]:
                raise AssertionError('Recovered historical catalog bytes differ: ' + name)
            (data_root / name).write_bytes(raw)
        cls.historical_pin = registry.canonical(manifest(cls.historical_root)) + b'\n'
        if sha256(cls.historical_pin).hexdigest() != PIN_SHA256:
            raise AssertionError('Recovered historical pin bytes differ')
        cls.historical_query_root = cls.fixture_root / 'historical-query'
        (cls.historical_query_root / 'pins').mkdir(parents=True)
        (cls.historical_query_root / 'pins/legacy_baseline.json').write_bytes(cls.historical_pin)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        if self._testMethodName == 'test_bruns_parent_manifest_and_catalog_recovery_remain_exact':
            self.current_root = self.tarasov_parent_root
        if self._testMethodName == 'test_nylon_parent_manifest_and_catalog_recovery_remain_exact':
            self.current_root = self.bruns_parent_root
        if self._testMethodName == 'test_tough_pla_parent_manifest_and_catalog_recovery_remain_exact':
            self.current_root = self.nylon_parent_root
        if self._testMethodName == 'test_filament_batch_parent_manifest_and_catalog_recovery_remain_exact':
            self.current_root = self.tough_pla_parent_root

    @contextmanager
    def resources(self, core_root, query_root=None):
        # Only resource locations change. Production traversal, hashing, pin
        # authentication, full-manifest matching and database code remain live.
        def resource_root(package):
            if package == 'materials_boundaries':
                return core_root
            if package == 'materials_query' and query_root is not None:
                return query_root
            return files(package)
        with patch.object(registry, 'files', resource_root):
            yield

    def copied_root(self, original=False):
        target = self.work / ('original' if original else 'current')
        shutil.copytree(self.original_root if original else self.current_root, target)
        return target

    def make_registry(self, path, review, rich):
        options = {'input_file_bytes': INPUT} if rich else {}
        return registry.ComputedRegistry(path, review,
            trusted_review_sha256=registry.digest(review), **options)

    def review(self, rich, second=False):
        review = rich_review() if rich else legacy_review()
        if second:
            extra = deepcopy(review['records'][0])
            extra.update(candidate_id='second', provider_entry_id='entry2',
                source_url='https://nomad-lab.eu/prod/v1/gui/entry/id/entry2')
            review['records'].append(extra)
        return review

    def database_rows(self, path):
        with closing(sqlite3.connect(path)) as database:
            return {table: database.execute('SELECT * FROM ' + table + ' ORDER BY 1').fetchall()
                    for table in ('metadata', 'entries', 'admissions')}

    def assert_manifest_rejected(self, mutate):
        for source in (self.original_root, self.dedup_root, self.current_root):
            with self.subTest(manifest=source.name):
                root = self.work / source.name
                shutil.copytree(source, root)
                mutate(root)
                with self.resources(root), self.assertRaisesRegex(
                        ValueError, 'Installed legacy baseline differs'):
                    registry.baseline_digest()

    def test_original_and_corrected_manifests_keep_historical_identity(self):
        self.assertEqual(len(self.expected), 64)
        self.assertEqual(manifest(self.original_root), self.expected)
        expected_successor = dict(self.expected, **{'material_references.py': SUCCESSOR_SHA256})
        self.assertEqual(manifest(self.dedup_root), expected_successor)
        expected_successor['material_presentation.py'] = PRESENTATION_SUCCESSOR_SHA256
        self.assertEqual(manifest(self.current_root), expected_successor)
        self.assertEqual(self.expected['material_references.py'], PREDECESSOR_SHA256)
        self.assertEqual(self.expected['material_presentation.py'], PRESENTATION_PREDECESSOR_SHA256)
        self.assertEqual(registry.BASELINE_PIN, CURRENT_PIN_SHA256)
        for root in (self.original_root, self.dedup_root, self.current_root):
            with self.subTest(root=root.name), self.resources(root):
                self.assertEqual(registry.baseline_digest(), self.original_identity)

    def test_installed_package_uses_corrected_manifest_without_resource_override(self):
        self.assertEqual(manifest(Path(files('materials_boundaries'))), manifest(self.current_root))
        self.assertEqual(registry.baseline_digest(), self.original_identity)
        review = legacy_review()
        database = self.make_registry(self.work / 'installed.db', review, False)
        self.assertEqual(database.admit(['fixture-entry'])['baseline_version'], self.original_identity)

    def test_a592_complete_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in A592_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.integrated_root)), 64)
        self.assertEqual(manifest(self.integrated_root), expected)
        parent = {name: json.loads((self.integrated_root / 'data' / name).read_bytes())
                  for name in A592_DATA_SHA256}
        self.assertEqual(recover_a592_catalogs(parent), parent)
        changed = deepcopy(parent)
        changed['materials.json']['identities'][0]['name'] += ' unreviewed'
        with self.assertRaisesRegex(AssertionError, 'Recovered a592 catalog bytes differ'):
            recover_a592_catalogs(changed)

    def test_tarasov_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_TARASOV_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.tarasov_parent_root)), 64)
        self.assertEqual(manifest(self.tarasov_parent_root), expected)
        current = {name: json.loads((self.current_root / 'data' / name).read_bytes())
                   for name in PRE_TARASOV_DATA_SHA256}
        parent = {name: json.loads((self.tarasov_parent_root / 'data' / name).read_bytes())
                  for name in PRE_TARASOV_DATA_SHA256}
        self.assertEqual(recover_pre_tarasov_catalogs(current), parent)
        self.assertEqual(recover_pre_tarasov_catalogs(parent), parent)
        self.assertEqual(current['sources.json']['records'][:-1], parent['sources.json']['records'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        self.assertEqual(len(parent['materials.json']['identities']), 1148)
        self.assertEqual(len(current['materials.json']['identities']), 1153)
        with self.assertRaisesRegex(AssertionError, 'Bruns borosilicate predecessor catalog bytes differ'):
            recover_pre_bruns_catalogs(current)
        ledger, additions = tarasov_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Tarasov PNA-BPF'):
                        recover_pre_tarasov_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Tarasov PNA-BPF predecessor catalog bytes differ'):
                recover_pre_tarasov_catalogs(changed)
        for filename, collection, label in [('materials.json', 'identities', 'identities'),
                                             ('materials.json', 'records', 'states'),
                                             ('reference_properties.json', 'records', 'properties')]:
            changed = deepcopy(current)
            self.assertEqual(len(additions[label]), 5)
            self.assertEqual({row['id'] for row in changed[filename][collection][-5:]},
                             {row['id'] for row in additions[label]})
            changed[filename][collection][-5:] = reversed(changed[filename][collection][-5:])
            self.assertNotEqual(changed, current)
            with self.subTest(order=label), self.assertRaisesRegex(
                    AssertionError, 'Tarasov PNA-BPF successor catalog order or bytes differ'):
                recover_pre_tarasov_catalogs(changed)
        original_read = Path.read_bytes
        for target in (TARASOV_LEDGER, TARASOV_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Tarasov PNA-BPF .* bytes differ'):
                recover_pre_tarasov_catalogs(current)
        with self.resources(self.tarasov_parent_root, self.tarasov_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_TARASOV_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_TARASOV_PIN_SHA256)
        with self.resources(self.tarasov_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_tarasov_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('faa002c-v2.db' if rich else 'faa002c-legacy.db')
                with self.resources(self.tarasov_parent_root, self.tarasov_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_TARASOV_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_bruns_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_BRUNS_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.bruns_parent_root)), 64)
        self.assertEqual(manifest(self.bruns_parent_root), expected)
        current = {name: json.loads((self.current_root / 'data' / name).read_bytes())
                   for name in PRE_BRUNS_DATA_SHA256}
        parent = {name: json.loads((self.bruns_parent_root / 'data' / name).read_bytes())
                  for name in PRE_BRUNS_DATA_SHA256}
        self.assertEqual(recover_pre_bruns_catalogs(current), parent)
        self.assertEqual(recover_pre_bruns_catalogs(parent), parent)
        self.assertEqual(current['sources.json']['records'][:-1], parent['sources.json']['records'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'Nylon follow-up predecessor catalog bytes differ'):
            recover_pre_nylon_catalogs(current)
        ledger, additions = bruns_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Bruns borosilicate'):
                        recover_pre_bruns_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Bruns borosilicate predecessor catalog bytes differ'):
                recover_pre_bruns_catalogs(changed)
        for filename, collection, label in [('materials.json', 'identities', 'identities'),
                                             ('materials.json', 'records', 'states'),
                                             ('reference_properties.json', 'records', 'properties')]:
            changed = deepcopy(current)
            self.assertEqual(len(additions[label]), 4)
            self.assertEqual({row['id'] for row in changed[filename][collection][-4:]},
                             {row['id'] for row in additions[label]})
            changed[filename][collection][-4:] = reversed(changed[filename][collection][-4:])
            self.assertNotEqual(changed, current)
            with self.subTest(order=label), self.assertRaisesRegex(
                    AssertionError, 'Bruns borosilicate successor catalog order or bytes differ'):
                recover_pre_bruns_catalogs(changed)
        original_read = Path.read_bytes
        for target in (BRUNS_LEDGER, BRUNS_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Bruns borosilicate .* bytes differ'):
                recover_pre_bruns_catalogs(current)
        with self.resources(self.bruns_parent_root, self.bruns_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_BRUNS_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_BRUNS_PIN_SHA256)
        with self.resources(self.bruns_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_bruns_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('4667477-v2.db' if rich else '4667477-legacy.db')
                with self.resources(self.bruns_parent_root, self.bruns_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_BRUNS_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_nylon_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_NYLON_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.nylon_parent_root)), 64)
        self.assertEqual(manifest(self.nylon_parent_root), expected)
        current = {name: json.loads((self.current_root / 'data' / name).read_bytes())
                   for name in PRE_NYLON_DATA_SHA256}
        parent = {name: json.loads((self.nylon_parent_root / 'data' / name).read_bytes())
                  for name in PRE_NYLON_DATA_SHA256}
        self.assertEqual(recover_pre_nylon_catalogs(current), parent)
        self.assertEqual(recover_pre_nylon_catalogs(parent), parent)
        self.assertEqual(current['sources.json']['records'][:-2], parent['sources.json']['records'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'Tough PLA follow-up predecessor catalog bytes differ'):
            recover_pre_tough_pla_catalogs(current)
        ledger, additions = nylon_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Nylon follow-up'):
                        recover_pre_nylon_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Nylon follow-up predecessor catalog bytes differ'):
                recover_pre_nylon_catalogs(changed)
        for filename, label in [('reference_properties.json', 'properties'), ('sources.json', 'sources')]:
            changed = deepcopy(current)
            self.assertEqual(len(additions[label]), 2)
            self.assertEqual({row['id'] for row in changed[filename]['records'][-2:]},
                             {row['id'] for row in additions[label]})
            changed[filename]['records'][-2:] = reversed(changed[filename]['records'][-2:])
            self.assertNotEqual(changed, current)
            with self.subTest(order=label), self.assertRaisesRegex(
                    AssertionError, 'Nylon follow-up successor catalog order or bytes differ'):
                recover_pre_nylon_catalogs(changed)
        original_read = Path.read_bytes
        for target in (NYLON_LEDGER, NYLON_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Nylon follow-up .* bytes differ'):
                recover_pre_nylon_catalogs(current)
        with self.resources(self.nylon_parent_root, self.nylon_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_NYLON_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_NYLON_PIN_SHA256)
        with self.resources(self.nylon_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_nylon_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('2c8ddac-v2.db' if rich else '2c8ddac-legacy.db')
                with self.resources(self.nylon_parent_root, self.nylon_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_NYLON_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_tough_pla_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_TOUGH_PLA_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.tough_pla_parent_root)), 64)
        self.assertEqual(manifest(self.tough_pla_parent_root), expected)
        current = {name: json.loads((self.current_root / 'data' / name).read_bytes())
                   for name in PRE_TOUGH_PLA_DATA_SHA256}
        parent = {name: json.loads((self.tough_pla_parent_root / 'data' / name).read_bytes())
                  for name in PRE_TOUGH_PLA_DATA_SHA256}
        self.assertEqual(recover_pre_tough_pla_catalogs(current), parent)
        self.assertEqual(recover_pre_tough_pla_catalogs(parent), parent)
        self.assertEqual(current['sources.json']['records'][:-1], parent['sources.json']['records'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'Filament batch predecessor catalog bytes differ'):
            recover_pre_filament_batch_catalogs(current)
        ledger, additions = tough_pla_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Tough PLA follow-up'):
                        recover_pre_tough_pla_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Tough PLA follow-up predecessor catalog bytes differ'):
                recover_pre_tough_pla_catalogs(changed)
        changed = deepcopy(current)
        self.assertEqual({row['id'] for row in changed['materials.json']['records'][-2:]},
                         {row['id'] for row in additions['states']})
        changed['materials.json']['records'][-2:] = reversed(changed['materials.json']['records'][-2:])
        with self.assertRaisesRegex(AssertionError, 'Tough PLA follow-up successor catalog order or bytes differ'):
            recover_pre_tough_pla_catalogs(changed)
        original_read = Path.read_bytes
        for target in (TOUGH_PLA_LEDGER, TOUGH_PLA_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Tough PLA follow-up .* bytes differ'):
                recover_pre_tough_pla_catalogs(current)
        with self.resources(self.tough_pla_parent_root, self.tough_pla_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_TOUGH_PLA_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_TOUGH_PLA_PIN_SHA256)
        with self.resources(self.tough_pla_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_tough_pla_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('5cc1418-v2.db' if rich else '5cc1418-legacy.db')
                with self.resources(self.tough_pla_parent_root, self.tough_pla_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_TOUGH_PLA_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_filament_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_FILAMENT_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.filament_parent_root)), 64)
        self.assertEqual(manifest(self.filament_parent_root), expected)
        current = {name: json.loads((self.current_root / 'data' / name).read_bytes())
                   for name in PRE_FILAMENT_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.filament_parent_root / 'data' / name).read_bytes())
                  for name in PRE_FILAMENT_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_filament_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_filament_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json']['records'][:-4], parent['sources.json']['records'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'Outokumpu batch predecessor catalog bytes differ'):
            recover_pre_outokumpu_batch_catalogs(current)
        ledger, additions = filament_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Filament batch'):
                        recover_pre_filament_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Filament batch predecessor catalog bytes differ'):
                recover_pre_filament_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-8 :] = reversed(changed['materials.json']['identities'][-8 :])
        with self.assertRaisesRegex(AssertionError, 'Filament batch successor catalog order or bytes differ'):
            recover_pre_filament_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (FILAMENT_LEDGER, FILAMENT_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Filament batch .* bytes differ'):
                recover_pre_filament_batch_catalogs(current)
        with self.resources(self.filament_parent_root, self.filament_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_FILAMENT_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_FILAMENT_BATCH_PIN_SHA256)
        with self.resources(self.filament_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_filament_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('5e8d63d-v2.db' if rich else '5e8d63d-legacy.db')
                with self.resources(self.filament_parent_root, self.filament_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_FILAMENT_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_outokumpu_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_OUTOKUMPU_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.outokumpu_parent_root)), 64)
        self.assertEqual(manifest(self.outokumpu_parent_root), expected)
        current = {name: json.loads((self.filament_parent_root / 'data' / name).read_bytes())
                   for name in PRE_OUTOKUMPU_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.outokumpu_parent_root / 'data' / name).read_bytes())
                  for name in PRE_OUTOKUMPU_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_outokumpu_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_outokumpu_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json'], parent['sources.json'])
        self.assertEqual(len(current['materials.json']['grades']), len(parent['materials.json']['grades']) + 10)
        self.assertEqual(current['materials.json']['grades'][:-10], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'NBR batch predecessor catalog bytes differ'):
            recover_pre_nbr_batch_catalogs(current)
        ledger, additions = outokumpu_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Outokumpu batch'):
                        recover_pre_outokumpu_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Outokumpu batch predecessor catalog bytes differ'):
                recover_pre_outokumpu_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-10:] = reversed(changed['materials.json']['identities'][-10:])
        with self.assertRaisesRegex(AssertionError, 'Outokumpu batch successor catalog order or bytes differ'):
            recover_pre_outokumpu_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (OUTOKUMPU_LEDGER, OUTOKUMPU_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Outokumpu batch .* bytes differ'):
                recover_pre_outokumpu_batch_catalogs(current)
        with self.resources(self.outokumpu_parent_root, self.outokumpu_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_OUTOKUMPU_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_OUTOKUMPU_BATCH_PIN_SHA256)
        with self.resources(self.outokumpu_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_outokumpu_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('eee77b5-v2.db' if rich else 'eee77b5-legacy.db')
                with self.resources(self.outokumpu_parent_root, self.outokumpu_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_OUTOKUMPU_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_nbr_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_NBR_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.nbr_parent_root)), 64)
        self.assertEqual(manifest(self.nbr_parent_root), expected)
        current = {name: json.loads((self.outokumpu_parent_root / 'data' / name).read_bytes())
                   for name in PRE_NBR_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.nbr_parent_root / 'data' / name).read_bytes())
                  for name in PRE_NBR_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_nbr_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_nbr_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json'], parent['sources.json'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'NR batch predecessor catalog bytes differ'):
            recover_pre_nr_batch_catalogs(current)
        ledger, additions = nbr_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'NBR batch'):
                        recover_pre_nbr_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'NBR batch predecessor catalog bytes differ'):
                recover_pre_nbr_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-6:] = reversed(changed['materials.json']['identities'][-6:])
        with self.assertRaisesRegex(AssertionError, 'NBR batch successor catalog order or bytes differ'):
            recover_pre_nbr_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (NBR_LEDGER, NBR_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'NBR batch .* bytes differ'):
                recover_pre_nbr_batch_catalogs(current)
        with self.resources(self.nbr_parent_root, self.nbr_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_NBR_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_NBR_BATCH_PIN_SHA256)
        with self.resources(self.nbr_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_nbr_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('f5bdcc4-v2.db' if rich else 'f5bdcc4-legacy.db')
                with self.resources(self.nbr_parent_root, self.nbr_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_NBR_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_nr_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_NR_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.nr_parent_root)), 64)
        self.assertEqual(manifest(self.nr_parent_root), expected)
        current = {name: json.loads((self.nbr_parent_root / 'data' / name).read_bytes())
                   for name in PRE_NR_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.nr_parent_root / 'data' / name).read_bytes())
                  for name in PRE_NR_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_nr_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_nr_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json'], parent['sources.json'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'Mtibe batch predecessor catalog bytes differ'):
            recover_pre_mtibe_batch_catalogs(current)
        ledger, additions = nr_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'NR batch'):
                        recover_pre_nr_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'NR batch predecessor catalog bytes differ'):
                recover_pre_nr_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-6:] = reversed(changed['materials.json']['identities'][-6:])
        with self.assertRaisesRegex(AssertionError, 'NR batch successor catalog order or bytes differ'):
            recover_pre_nr_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (NR_LEDGER, NR_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'NR batch .* bytes differ'):
                recover_pre_nr_batch_catalogs(current)
        with self.resources(self.nr_parent_root, self.nr_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_NR_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_NR_BATCH_PIN_SHA256)
        with self.resources(self.nr_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_nr_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('8981840-v2.db' if rich else '8981840-legacy.db')
                with self.resources(self.nr_parent_root, self.nr_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_NR_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_mtibe_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_MTIBE_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.mtibe_parent_root)), 64)
        self.assertEqual(manifest(self.mtibe_parent_root), expected)
        current = {name: json.loads((self.nr_parent_root / 'data' / name).read_bytes())
                   for name in PRE_MTIBE_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.mtibe_parent_root / 'data' / name).read_bytes())
                  for name in PRE_MTIBE_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_mtibe_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_mtibe_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json'], parent['sources.json'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'Binary batch predecessor catalog bytes differ'):
            recover_pre_binary_batch_catalogs(current)
        ledger, additions = mtibe_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Mtibe batch'):
                        recover_pre_mtibe_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Mtibe batch predecessor catalog bytes differ'):
                recover_pre_mtibe_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-3:] = reversed(changed['materials.json']['identities'][-3:])
        with self.assertRaisesRegex(AssertionError, 'Mtibe batch successor catalog order or bytes differ'):
            recover_pre_mtibe_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (MTIBE_LEDGER, MTIBE_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Mtibe batch .* bytes differ'):
                recover_pre_mtibe_batch_catalogs(current)
        with self.resources(self.mtibe_parent_root, self.mtibe_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_MTIBE_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_MTIBE_BATCH_PIN_SHA256)
        with self.resources(self.mtibe_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_mtibe_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('a5cc3f6-v2.db' if rich else 'a5cc3f6-legacy.db')
                with self.resources(self.mtibe_parent_root, self.mtibe_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_MTIBE_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_binary_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_BINARY_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.binary_parent_root)), 64)
        self.assertEqual(manifest(self.binary_parent_root), expected)
        current = {name: json.loads((self.mtibe_parent_root / 'data' / name).read_bytes())
                   for name in PRE_BINARY_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.binary_parent_root / 'data' / name).read_bytes())
                  for name in PRE_BINARY_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_binary_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_binary_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json'], parent['sources.json'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'RCA batch predecessor catalog bytes differ'):
            recover_pre_rca_batch_catalogs(current)
        ledger, additions = binary_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Binary batch'):
                        recover_pre_binary_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Binary batch predecessor catalog bytes differ'):
                recover_pre_binary_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-6:] = reversed(changed['materials.json']['identities'][-6:])
        with self.assertRaisesRegex(AssertionError, 'Binary batch successor catalog order or bytes differ'):
            recover_pre_binary_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (BINARY_LEDGER, BINARY_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Binary batch .* bytes differ'):
                recover_pre_binary_batch_catalogs(current)
        with self.resources(self.binary_parent_root, self.binary_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_BINARY_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_BINARY_BATCH_PIN_SHA256)
        with self.resources(self.binary_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_binary_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('4db4ab5-v2.db' if rich else '4db4ab5-legacy.db')
                with self.resources(self.binary_parent_root, self.binary_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_BINARY_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_rca_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_RCA_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.rca_parent_root)), 64)
        self.assertEqual(manifest(self.rca_parent_root), expected)
        current = {name: json.loads((self.binary_parent_root / 'data' / name).read_bytes())
                   for name in PRE_RCA_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.rca_parent_root / 'data' / name).read_bytes())
                  for name in PRE_RCA_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_rca_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_rca_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json'], parent['sources.json'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'Table batch predecessor catalog bytes differ'):
            recover_pre_table_batch_catalogs(current)
        ledger, additions = rca_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'RCA batch'):
                        recover_pre_rca_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'RCA batch predecessor catalog bytes differ'):
                recover_pre_rca_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-3:] = reversed(changed['materials.json']['identities'][-3:])
        with self.assertRaisesRegex(AssertionError, 'RCA batch successor catalog order or bytes differ'):
            recover_pre_rca_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (RCA_LEDGER, RCA_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'RCA batch .* bytes differ'):
                recover_pre_rca_batch_catalogs(current)
        with self.resources(self.rca_parent_root, self.rca_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_RCA_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_RCA_BATCH_PIN_SHA256)
        with self.resources(self.rca_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_rca_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('799ca7a-v2.db' if rich else '799ca7a-legacy.db')
                with self.resources(self.rca_parent_root, self.rca_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_RCA_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_table_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_TABLE_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.table_parent_root)), 64)
        self.assertEqual(manifest(self.table_parent_root), expected)
        current = {name: json.loads((self.rca_parent_root / 'data' / name).read_bytes())
                   for name in PRE_TABLE_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.table_parent_root / 'data' / name).read_bytes())
                  for name in PRE_TABLE_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_table_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_table_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json'], parent['sources.json'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'PUR batch predecessor catalog bytes differ'):
            recover_pre_pur_batch_catalogs(current)
        ledger, additions = table_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Table batch'):
                        recover_pre_table_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Table batch predecessor catalog bytes differ'):
                recover_pre_table_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-8:] = reversed(changed['materials.json']['identities'][-8:])
        with self.assertRaisesRegex(AssertionError, 'Table batch successor catalog order or bytes differ'):
            recover_pre_table_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (TABLE_LEDGER, TABLE_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Table batch .* bytes differ'):
                recover_pre_table_batch_catalogs(current)
        with self.resources(self.table_parent_root, self.table_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_TABLE_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_TABLE_BATCH_PIN_SHA256)
        with self.resources(self.table_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_table_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('efd4ca2-v2.db' if rich else 'efd4ca2-legacy.db')
                with self.resources(self.table_parent_root, self.table_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_TABLE_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_pur_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_PUR_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.pur_parent_root)), 64)
        self.assertEqual(manifest(self.pur_parent_root), expected)
        current = {name: json.loads((self.table_parent_root / 'data' / name).read_bytes())
                   for name in PRE_PUR_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.pur_parent_root / 'data' / name).read_bytes())
                  for name in PRE_PUR_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_pur_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_pur_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json'], parent['sources.json'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        with self.assertRaisesRegex(AssertionError, 'Growth batch predecessor catalog bytes differ'):
            recover_pre_growth_batch_catalogs(current)
        ledger, additions = pur_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'PUR batch'):
                        recover_pre_pur_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'PUR batch predecessor catalog bytes differ'):
                recover_pre_pur_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-2:] = reversed(changed['materials.json']['identities'][-2:])
        with self.assertRaisesRegex(AssertionError, 'PUR batch successor catalog order or bytes differ'):
            recover_pre_pur_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (PUR_LEDGER, PUR_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'PUR batch .* bytes differ'):
                recover_pre_pur_batch_catalogs(current)
        with self.resources(self.pur_parent_root, self.pur_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_PUR_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_PUR_BATCH_PIN_SHA256)
        with self.resources(self.pur_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_pur_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('2509-v2.db' if rich else '2509-legacy.db')
                with self.resources(self.pur_parent_root, self.pur_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_PUR_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_growth_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_GROWTH_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.growth_parent_root)), 64)
        self.assertEqual(manifest(self.growth_parent_root), expected)
        current = {name: json.loads((self.pur_parent_root / 'data' / name).read_bytes())
                   for name in PRE_GROWTH_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.growth_parent_root / 'data' / name).read_bytes())
                  for name in PRE_GROWTH_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_growth_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_growth_batch_catalogs(parent), parent)
        self.assertEqual(current['sources.json'], parent['sources.json'])
        self.assertEqual(current['materials.json']['grades'], parent['materials.json']['grades'])
        ledger, additions = growth_batch_inventory()
        for filename, section, collection, label in GROWTH_COLLECTIONS:
            if not additions[label]:
                continue
            candidate = additions[label][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=label, mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Growth batch'):
                        recover_pre_growth_batch_catalogs(changed)
        for filename, collection in [('materials.json', 'identities'), ('sources.json', 'records')]:
            changed = deepcopy(current)
            changed[filename][collection][0]['version'] = 'unreviewed'
            with self.subTest(retained_collection=collection), self.assertRaisesRegex(
                    AssertionError, 'Growth batch predecessor catalog bytes differ'):
                recover_pre_growth_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][-6:] = reversed(changed['materials.json']['identities'][-6:])
        with self.assertRaisesRegex(AssertionError, 'Growth batch successor catalog order or bytes differ'):
            recover_pre_growth_batch_catalogs(changed)
        original_read = Path.read_bytes
        for target in (GROWTH_LEDGER, GROWTH_PACKET):
            def replaced(path):
                return original_read(path) + (b' ' if path == target else b'')
            with self.subTest(binding=target.name), patch.object(Path, 'read_bytes', replaced), \
                    self.assertRaisesRegex(AssertionError, 'Growth batch .* bytes differ'):
                recover_pre_growth_batch_catalogs(current)
        with self.resources(self.growth_parent_root, self.growth_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_GROWTH_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_GROWTH_BATCH_PIN_SHA256)
        with self.resources(self.growth_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_growth_batch_parent_database_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('c901-v2.db' if rich else 'c901-legacy.db')
                with self.resources(self.growth_parent_root, self.growth_parent_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PRE_GROWTH_BATCH_PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                raw = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_evidence_batch_parent_manifest_and_catalog_recovery_remain_exact(self):
        expected = dict(self.expected)
        expected.update({'data/' + name: digest for name, digest in PRE_EVIDENCE_BATCH_DATA_SHA256.items()})
        self.assertEqual(len(manifest(self.evidence_parent_root)), 64)
        self.assertEqual(manifest(self.evidence_parent_root), expected)
        current = {name: json.loads((self.growth_parent_root / 'data' / name).read_bytes())
                   for name in PRE_EVIDENCE_BATCH_DATA_SHA256}
        parent = {name: json.loads((self.evidence_parent_root / 'data' / name).read_bytes())
                  for name in PRE_EVIDENCE_BATCH_DATA_SHA256}
        self.assertEqual(recover_pre_evidence_batch_catalogs(current), parent)
        self.assertEqual(recover_pre_evidence_batch_catalogs(parent), parent)
        appended = evidence_batch_catalogs()
        for filename, section, collection in EVIDENCE_BATCH_COLLECTIONS:
            candidate = appended[section][collection][0]
            for mutation in ('missing', 'changed', 'duplicate'):
                with self.subTest(collection=(filename, collection), mutation=mutation):
                    changed = deepcopy(current)
                    rows = changed[filename][collection]
                    row = next(row for row in rows if row['id'] == candidate['id'])
                    if mutation == 'missing':
                        rows.remove(row)
                    elif mutation == 'changed':
                        row['version'] = 'unreviewed'
                    else:
                        rows.append(deepcopy(row))
                    with self.assertRaisesRegex(AssertionError, 'Evidence batch'):
                        recover_pre_evidence_batch_catalogs(changed)
        changed = deepcopy(current)
        changed['materials.json']['identities'][0]['name'] += ' unreviewed'
        with self.assertRaisesRegex(AssertionError, 'Recovered pre-evidence-batch catalog bytes differ'):
            recover_pre_evidence_batch_catalogs(changed)
        original_read = Path.read_bytes
        def replaced_packet(path):
            return original_read(path) + (b' ' if path == EVIDENCE_BATCH_PACKET else b'')
        with patch.object(Path, 'read_bytes', replaced_packet), self.assertRaisesRegex(
                AssertionError, 'Evidence batch packet bytes differ'):
            recover_pre_evidence_batch_catalogs(current)
        with self.resources(self.evidence_parent_root, self.evidence_parent_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', PRE_EVIDENCE_BATCH_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), PRE_EVIDENCE_BATCH_PIN_SHA256)
        with self.resources(self.evidence_parent_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_a592_pin_cannot_replace_current_anchor(self):
        self.assertNotEqual(CURRENT_PIN_SHA256, INTEGRATED_PIN_SHA256)
        with self.resources(self.integrated_root, self.integrated_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            with patch.object(registry, 'BASELINE_PIN', INTEGRATED_PIN_SHA256):
                self.assertEqual(registry.baseline_digest(), INTEGRATED_PIN_SHA256)
        with self.resources(self.integrated_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_a592_registry_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                path = self.work / ('a592-v2.db' if rich else 'a592-legacy.db')
                review = self.review(rich)
                with self.resources(self.integrated_root, self.integrated_query_root), \
                        patch.object(registry, 'BASELINE_PIN', INTEGRATED_PIN_SHA256):
                    previous = self.make_registry(path, review, rich)
                    before = previous.admit([review['records'][0]['candidate_id']])
                database_bytes = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), database_bytes)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(previous.snapshot(), before)

    def test_historical_pin_cannot_replace_integrated_anchor(self):
        self.assertNotEqual(PIN_SHA256, INTEGRATED_PIN_SHA256)
        self.assertEqual(len(manifest(self.historical_root)), 64)
        with self.resources(self.historical_root, self.historical_query_root):
            with self.assertRaisesRegex(ValueError, 'Baseline pin was replaced'):
                registry.baseline_digest()
            # Reproduce the historical trust configuration only inside this
            # test. Production still accepts exactly the integrated data pin.
            with patch.object(registry, 'BASELINE_PIN', PIN_SHA256):
                historical_identity = registry.baseline_digest()
        self.assertNotEqual(historical_identity, self.original_identity)
        self.assertEqual(historical_identity, registry.digest(json.loads(self.historical_pin)))

    def test_integrated_pin_rejects_historical_catalog_bytes(self):
        with self.resources(self.historical_root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_historical_data_registry_rejected_without_migration(self):
        for rich in (False, True):
            with self.subTest(rich=rich):
                path = self.work / ('historical-data-v2.db' if rich else 'historical-data-legacy.db')
                review = self.review(rich)
                with self.resources(self.historical_root, self.historical_query_root), \
                        patch.object(registry, 'BASELINE_PIN', PIN_SHA256):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                database_bytes = path.read_bytes()
                rows = self.database_rows(path)
                with self.assertRaisesRegex(ValueError, 'Initial baseline and review input cannot be replaced'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), database_bytes)
                self.assertEqual(self.database_rows(path), rows)
                self.assertEqual(historical.snapshot(), before)

    def test_unknown_reference_bytes_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'material_references.py').write_bytes(
            (root / 'material_references.py').read_bytes() + b'\n# Unreviewed change\n'))

    def test_unknown_presentation_bytes_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'material_presentation.py').write_bytes(
            (root / 'material_presentation.py').read_bytes() + b'\n# Unreviewed change\n'))

    def test_presentation_only_hybrid_manifest_rejected(self):
        root = self.copied_root(original=True)
        (root / 'material_presentation.py').write_bytes(
            (self.current_root / 'material_presentation.py').read_bytes())
        hybrid = dict(self.expected, **{'material_presentation.py': PRESENTATION_SUCCESSOR_SHA256})
        self.assertEqual(manifest(root), hybrid)
        with self.resources(root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_changed_other_python_file_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / '_version.py').write_bytes(
            (root / '_version.py').read_bytes() + b'\n# Unreviewed change\n'))

    def test_changed_catalog_bytes_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'data/materials.json').write_bytes(
            (root / 'data/materials.json').read_bytes() + b' '))

    def test_missing_manifest_file_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'data/materials.json').unlink())

    def test_extra_manifest_file_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'data/unreviewed.json').write_bytes(b'{}'))

    def test_replaced_pin_rejected(self):
        query_root = self.work / 'query'
        (query_root / 'pins').mkdir(parents=True)
        changed = dict(self.expected, **{'material_references.py': SUCCESSOR_SHA256})
        for raw in (self.pin_bytes + b' ', registry.canonical(changed)):
            with self.subTest(pin_sha256=sha256(raw).hexdigest()):
                (query_root / 'pins/legacy_baseline.json').write_bytes(raw)
                with self.resources(self.current_root, query_root), self.assertRaisesRegex(
                        ValueError, 'Baseline pin was replaced'):
                    registry.baseline_digest()

    def assert_old_database_reopens(self, rich, predecessor=None):
        path = self.work / 'historical.db'
        review = self.review(rich)
        candidate = review['records'][0]['candidate_id']
        with self.resources(self.original_root if predecessor is None else predecessor):
            old = self.make_registry(path, review, rich)
            before = old.admit([candidate])
        rows = self.database_rows(path)
        database_bytes = path.read_bytes()
        self.assertEqual(dict(rows['metadata'])['baseline'], self.original_identity)
        self.assertEqual(len(rows['entries']), 1)
        self.assertEqual(len(rows['admissions']), 1)
        with self.resources(self.current_root):
            reopened = self.make_registry(path, review, rich)
            self.assertEqual(reopened.snapshot(), before)
            self.assertEqual(self.database_rows(path), rows)
            self.assertEqual(path.read_bytes(), database_bytes)
            self.assertEqual(reopened.admit([candidate]), before)
            self.assertEqual(self.database_rows(path), rows)
            self.assertEqual(path.read_bytes(), database_bytes)

    def test_original_manifest_legacy_database_reopens_without_changes(self):
        self.assert_old_database_reopens(False)

    def test_original_manifest_v2_database_reopens_without_changes(self):
        self.assert_old_database_reopens(True)

    def test_dedup_predecessor_legacy_database_reopens_without_changes(self):
        self.assert_old_database_reopens(False, self.dedup_root)

    def test_dedup_predecessor_v2_database_reopens_without_changes(self):
        self.assert_old_database_reopens(True, self.dedup_root)

    def assert_new_registry_replay(self, rich):
        review = self.review(rich)
        path = self.work / 'new.db'
        # No resource adapter: this exercises the actual source or installed
        # package manifest selected by the caller's Python environment.
        created = self.make_registry(path, review, rich)
        self.assertEqual(created.snapshot()['records'], [])
        self.assertEqual(created.baseline, self.original_identity)
        admitted = created.admit([review['records'][0]['candidate_id']])
        self.assertEqual(admitted['records'], [review['records'][0]])
        self.assertEqual(created.admit([review['records'][0]['candidate_id']]), admitted)
        self.assertEqual(self.make_registry(path, review, rich).snapshot(), admitted)

    def test_new_legacy_registry_admission_and_replay(self):
        self.assert_new_registry_replay(False)

    def test_new_v2_registry_admission_and_replay(self):
        self.assert_new_registry_replay(True)

    def assert_failed_transaction_recovers(self, rich):
        path = self.work / 'interrupted.db'
        review = self.review(rich, second=True)
        with self.resources(self.original_root):
            historical = self.make_registry(path, review, rich)
            before = historical.admit([review['records'][0]['candidate_id']])
        rows = self.database_rows(path)
        with closing(sqlite3.connect(path)) as database, database:
            database.execute("CREATE TRIGGER fail_admission BEFORE INSERT ON admissions "
                             "WHEN NEW.id='second' BEGIN "
                             "SELECT RAISE(ABORT, 'synthetic transaction abort'); END")
        with self.resources(self.current_root):
            current = self.make_registry(path, review, rich)
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'synthetic transaction abort'):
                current.admit(['second'])
            self.assertEqual(self.database_rows(path), rows)
            self.assertEqual(current.snapshot(), before)
            reopened = self.make_registry(path, review, rich)
            self.assertEqual(reopened.snapshot(), before)
            with closing(sqlite3.connect(path)) as database, database:
                database.execute('DROP TRIGGER fail_admission')
            recovered = reopened.admit(['second'])
            self.assertEqual(len(recovered['records']), 2)
            self.assertEqual(recovered['baseline_version'], self.original_identity)
            self.assertEqual(reopened.admit(['second']), recovered)
            self.assertEqual(self.make_registry(path, review, rich).snapshot(), recovered)
            self.assertEqual(self.database_rows(path)['metadata'], rows['metadata'])

    def test_failed_legacy_transaction_rolls_back_and_reopens(self):
        self.assert_failed_transaction_recovers(False)

    def test_failed_v2_transaction_rolls_back_and_reopens(self):
        self.assert_failed_transaction_recovers(True)

    def test_rejected_unknown_baseline_leaves_existing_database_unchanged(self):
        root = self.copied_root()
        (root / 'material_references.py').write_bytes(b'# Unknown successor\n')
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('existing-v2.db' if rich else 'existing-legacy.db')
                with self.resources(self.original_root):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                database_bytes = path.read_bytes()
                with self.resources(root), self.assertRaisesRegex(
                        ValueError, 'Installed legacy baseline differs'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), database_bytes)
                self.assertEqual(self.make_registry(path, review, rich).snapshot(), before)

    def test_registry_with_unknown_baseline_never_creates_database(self):
        root = self.copied_root()
        (root / 'material_references.py').write_bytes(b'# Unknown successor\n')
        for rich in (False, True):
            with self.subTest(rich=rich):
                path = self.work / ('new-v2.db' if rich else 'new-legacy.db')
                with self.resources(root), self.assertRaisesRegex(
                        ValueError, 'Installed legacy baseline differs'):
                    self.make_registry(path, self.review(rich), rich)
                self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
