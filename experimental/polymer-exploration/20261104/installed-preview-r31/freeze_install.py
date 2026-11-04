"""Freeze completed install, consumer evidence and guarded local application."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[4]
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
INSTALL=ROOT.parent/'open-database-evidence/polymer-installed-preview-20261104-r31'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    assert not (OUT/'REVIEW_INPUTS_R31.json').exists()
    result=read(INSTALL/'INSTALLED_VALIDATION_R31.json')
    consumer=read(INSTALL/'consumer/CURRENT_CONSUMER_VALIDATION_R31.json')
    observation=read(INSTALL/'CONSUMER_PROCESS_OBSERVATION_R31.json')
    assert observation['returncode']==0 and not observation['stderr']
    assert consumer['core_snapshot']==result['installed']['snapshot']=='b4c2f6c279400bd67848c4ec049a7050f9c984ad4c247702693596b1da74a306'
    assert consumer['complete_resolved_states_equal_core']==9 and consumer['new_properties_exact_record_and_query_equal']==18
    assert read(INSTALL/'ARTIFACT_RECORDS_AND_EXPORT_R31.json')['status']=='artifact_records_and_complete_export_passed'
    shutil.copyfile(INSTALL/'INSTALLED_VALIDATION_R31.json',OUT/'INSTALLED_VALIDATION_R31.json')
    (OUT/'README.zh.md').write_text('# r31 弯曲性质隔离安装核验\n\n18条弯曲强度／模量均值与SD、9个来源限定试验上下文的真实离线安装完成。固定69输入，65包载荷与6元数据逐项核对；只替换三表及隔离版本。快照b4c2f6c279400bd67848c4ec049a7050f9c984ad4c247702693596b1da74a306，5371性质／5245状态；原生尚未应用本批。\n\n71项wheel、76项installed RECORD哈希／大小及50项缓存代码对象与源码一致。实际安装保留5353旧性质、5236旧状态及全部身份／牌号，新18个均值与SD、n=8来源共享组、9上下文和唯一来源追加声明完整匹配。55条完整来源导出与预览逐字节一致，四语言保留18个ID、均值、SD及边界说明。既有15条Tg、11条熔融峰不变。\n\nproduct_form、几何、跨距、方向、成形路线、温湿度、调湿和与既有试样的关联保持未知。新增上下文记录不证明独立物理覆盖、批次或材料；两项性质共享8次来源试验组，不计16次独立试验。保留MPa精度及源SD舍入，Tukey字母和显著性不作CI，ASTM引用不作修订后缀或合规认证。\n\n冻结进程内辅助查询组件使用真实已安装内核，核9上下文／18性质／55导出、副本隔离、过期选择拒绝及三表不变。组件版本不是数据库快照；父捕获命令、返回值与原始输出不冒称独立OS轨迹，不启动或认证HTTP和完整平台。\n\n应用方案要求精确mapping及本安装独审，写前核全部输入、图结果同字节继承、旧对象保持及条件限制，先保存恢复副本／意图再复制三表。预览METADATA沿用应用前README，不能作公开发布文档。本批原生应用、接纳后22项检查及完整历史回归尚未运行；未推送、合并main、稳定发布或部署。入口REVIEW_INPUTS_R31.json。\n',encoding='utf-8',newline='\n')
    mapping=AREA/'pbs-existing-flexural-native-r1'
    repo=set(p for p in OUT.iterdir() if p.is_file())|set((AREA/'local-acceptance-r31').glob('*.py'))|{mapping/'REVIEW_INPUTS_R1.json',mapping/'INDEPENDENT_MAPPING_REVIEW_R1.json',ROOT/'experimental/platform/query-service/materials_query/catalog_snapshot.py'}
    native={ROOT/'materials_boundaries/data'/n for n in ['materials.json','reference_properties.json','sources.json']}
    external=set(p for p in INSTALL.iterdir() if p.is_file())|set((INSTALL/'dist').glob('*.whl'))|set((INSTALL/'installed-export-ewurum_mcdonald_2025_pbs_lignin').glob('*'))|set((INSTALL/'consumer').glob('*'))
    external|={Path(n) for n in read(mapping/'REVIEW_INPUTS_R1.json')['external_files_sha256']}
    entry={'schema':'PBS-flexural-install-consumer-local-application-review/1','repo_files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(repo)},'native_files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(native)},'external_files_sha256':{str(p):sha(p) for p in sorted(external) if p.is_file()},'external_install_directory_hint':str(INSTALL),'preview_snapshot':result['installed']['snapshot'],'native_applied':False,'pushed':False,'scope':'Exact actual installation, frozen in-process consumer evidence and static guarded local application. No full platform,HTTP,release or scientific certification.'}
    write(OUT/'REVIEW_INPUTS_R31.json',entry)
    print(json.dumps({'review_inputs_sha256':sha(OUT/'REVIEW_INPUTS_R31.json'),'repo_files':len(entry['repo_files_sha256']),'external_files':len(entry['external_files_sha256'])}))

if __name__=='__main__':main()
