"""Freeze completed install, consumer evidence and guarded local application."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[4]
AREA=ROOT/'experimental/polymer-exploration/20261104'
OUT=Path(__file__).resolve().parent
INSTALL=ROOT.parent/'open-database-evidence/polymer-installed-preview-20261104-r30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    assert not (OUT/'REVIEW_INPUTS_R30.json').exists()
    result=read(INSTALL/'INSTALLED_VALIDATION_R30.json')
    consumer=read(INSTALL/'consumer/CURRENT_CONSUMER_VALIDATION_R30.json')
    observation=read(INSTALL/'CONSUMER_PROCESS_OBSERVATION_R30.json')
    assert observation['returncode']==0 and not observation['stderr']
    assert consumer['core_snapshot']==result['installed']['snapshot']=='1ea75d1cee10a186eabbd44e96c04625716450490c55614492d316acb5139020'
    assert consumer['complete_resolved_states_equal_core']==consumer['new_properties_exact_record_and_query_equal']==9
    assert read(INSTALL/'ARTIFACT_RECORDS_AND_EXPORT_R30.json')['status']=='artifact_records_and_complete_export_passed'
    shutil.copyfile(INSTALL/'INSTALLED_VALIDATION_R30.json',OUT/'INSTALLED_VALIDATION_R30.json')
    (OUT/'README.zh.md').write_text('# r30 DMA Tg 隔离安装核验\n\n9条既有配方DMA tanδ最大值Tg和9个物理条形状态的真实离线隔离安装完成。固定69输入、65包载荷及6元数据；预览只替换三表及隔离版本号。实际安装快照1ea75d1cee10a186eabbd44e96c04625716450490c55614492d316acb5139020，5353性质／5236状态；仓库原生表尚未应用。\n\n71项wheel与76项安装RECORD哈希／大小、50项缓存代码对象与源码编译的一致性通过。实际安装中5344条旧性质、5227个旧状态、身份和牌号完整保持；9条新DMA Tg、9个状态和来源单次追加说明精确匹配。全局Tg15条、旧熔融峰11条、37条完整来源导出及四语展示通过，导出与预览逐字节相同。\n\n共同DMA三次重复作为方法背景保留，选定scalar n、汇总和不确定度未知。频率、应变、温度扫描、几何、夹具及软件保存；不把DMA当DSC、静态拉伸、均值或独立批次。现有闭合温度分支不变，不声称物理可比、标准合规或工程准入。\n\n真实已安装内核及冻结进程内辅助查询组件核验9状态／9性质／37导出、副本隔离、stale拒绝及三表不变。组件版本与核心数据快照不同。父捕获命令和return0/stdout/stderr绑定执行结果，不冒称独立OS轨迹；不启动或认证HTTP及完整平台。\n\n预览METADATA使用应用前README，不能作本批公开发布文档。应用工具需精确mapping与本安装独审通过，核全部输入、安装表与旧对象，保存恢复副本及意图后才复制三表。尚未应用本批、运行接纳后套件或完整历史回归；未推送、合并main、稳定发布或部署。独审入口REVIEW_INPUTS_R30.json。\n',encoding='utf-8',newline='\n')
    mapping=AREA/'pbs-existing-dma-tg-native-r1'
    repo=set(p for p in OUT.iterdir() if p.is_file())|set((AREA/'local-acceptance-r30').glob('*.py'))|{mapping/'REVIEW_INPUTS_R1.json',mapping/'INDEPENDENT_MAPPING_REVIEW_R1.json',ROOT/'experimental/platform/query-service/materials_query/catalog_snapshot.py'}
    native={ROOT/'materials_boundaries/data'/n for n in ['materials.json','reference_properties.json','sources.json']}
    external=set(p for p in INSTALL.iterdir() if p.is_file())|set((INSTALL/'dist').glob('*.whl'))|set((INSTALL/'installed-export-ewurum_mcdonald_2025_pbs_lignin').glob('*'))|set((INSTALL/'consumer').glob('*'))
    external|={Path(n) for n in read(mapping/'REVIEW_INPUTS_R1.json')['external_files_sha256']}
    entry={'schema':'PBS-DSC-install-consumer-local-application-review/1','repo_files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(repo)},'native_files_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(native)},'external_files_sha256':{str(p):sha(p) for p in sorted(external) if p.is_file()},'external_install_directory_hint':str(INSTALL),'preview_snapshot':result['installed']['snapshot'],'native_applied':False,'pushed':False,'scope':'Exact actual installation, frozen in-process consumer evidence and static guarded local application. No full platform,HTTP,release or scientific certification.'}
    write(OUT/'REVIEW_INPUTS_R30.json',entry)
    print(json.dumps({'review_inputs_sha256':sha(OUT/'REVIEW_INPUTS_R30.json'),'repo_files':len(entry['repo_files_sha256']),'external_files':len(entry['external_files_sha256'])}))

if __name__=='__main__':main()
