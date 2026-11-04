"""Freeze completed install, consumer evidence and guarded local application."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[4]
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
INSTALL=ROOT.parent/'open-database-evidence/polymer-installed-preview-20261104-r29'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    assert not (OUT/'REVIEW_INPUTS_R29.json').exists()
    result=read(INSTALL/'INSTALLED_VALIDATION_R29.json')
    consumer=read(INSTALL/'consumer/CURRENT_CONSUMER_VALIDATION_R29.json')
    observation=read(INSTALL/'CONSUMER_PROCESS_OBSERVATION_R29.json')
    assert observation['returncode']==0 and not observation['stderr']
    assert consumer['core_snapshot']==result['installed']['snapshot']=='82e9840bca99bc36b273c1df7542f5d1019d4be3141df4584432eef88e399abc'
    assert consumer['complete_resolved_states_equal_core']==consumer['new_properties_exact_record_and_query_equal']==9
    assert read(INSTALL/'ARTIFACT_RECORDS_AND_EXPORT_R29.json')['status']=='artifact_records_and_complete_export_passed'
    shutil.copyfile(INSTALL/'INSTALLED_VALIDATION_R29.json',OUT/'INSTALLED_VALIDATION_R29.json')
    (OUT/'README.zh.md').write_text('''# r29 PBS DSC 隔离安装核验

9条既有配方熔融温度映射的真实离线隔离安装完成。构建配方固定69个输入，包内65个载荷文件逐一核对；预览只替换三张数据表及隔离版本号。实际安装快照为82e9840bca99bc36b273c1df7542f5d1019d4be3141df4584432eef88e399abc，5344性质／5227状态。仓库原生表尚未应用。

71项wheel RECORD、76项安装RECORD哈希／大小核验通过；50项安装生成缓存的代码对象与其源码编译结果一致，未执行缓存对象。首次把marshal字节序列当规范比较导致检查中止，失败helper和修正说明保留；后改为比较所有代码字段和嵌套代码对象，没有重建或重装。

实际安装中所有5335条旧性质、5218个旧状态、身份和牌号保持；9条新性质、9个新状态及唯一来源追加声明精确匹配。9条新性质查询、全库11个熔融峰、6个Tg、四语言9个ID、28条完整来源导出及校验通过；导出与预览逐字节相同。实际安装当前图契约核验通过，无套件或完整历史回归。

冻结的进程内辅助查询组件使用真实已安装内核，核对9状态、9新性质和28导出对象、副本隔离、过期选择拒绝及三表不变。组件版本与数据库快照区分；不启动或认证HTTP和完整平台。执行结果是父会话捕获的进程观察，不冒称独立OS轨迹。

本包是本地候选预览，METADATA沿用当时基线README，不能作新版本公开发布文档。应用工具只在精确mapping及本安装独审均通过后，保存三表恢复副本和写入意图，再复制精确预览三表并核对本地数据库。未推送、合并main、稳定发布或部署。独审入口REVIEW_INPUTS_R29.json。
''',encoding='utf-8')
    mapping=AREA/'pbs-existing-dsc-native-r1'
    repo=set(p for p in OUT.iterdir() if p.is_file())|set((AREA/'local-acceptance-r29').glob('*.py'))|{mapping/'REVIEW_INPUTS_R1.json',mapping/'INDEPENDENT_MAPPING_REVIEW_R1.json',ROOT/'experimental/platform/query-service/materials_query/catalog_snapshot.py'}
    native={ROOT/'materials_boundaries/data'/n for n in ['materials.json','reference_properties.json','sources.json']}
    external=set(p for p in INSTALL.iterdir() if p.is_file())|set((INSTALL/'dist').glob('*.whl'))|set((INSTALL/'installed-export-ewurum_mcdonald_2025_pbs_lignin').glob('*'))|set((INSTALL/'consumer').glob('*'))
    external|={Path(n) for n in read(mapping/'REVIEW_INPUTS_R1.json')['external_files_sha256']}
    entry={'schema':'PBS-DSC-install-consumer-local-application-review/1','repo_files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(repo)},'native_files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(native)},'external_files_sha256':{str(p):sha(p) for p in sorted(external) if p.is_file()},'external_install_directory_hint':str(INSTALL),'preview_snapshot':result['installed']['snapshot'],'native_applied':False,'pushed':False,'scope':'Exact actual installation, frozen in-process consumer evidence and static guarded local application. No full platform,HTTP,release or scientific certification.'}
    write(OUT/'REVIEW_INPUTS_R29.json',entry)
    print(json.dumps({'review_inputs_sha256':sha(OUT/'REVIEW_INPUTS_R29.json'),'repo_files':len(entry['repo_files_sha256']),'external_files':len(entry['external_files_sha256'])}))

if __name__=='__main__':main()
