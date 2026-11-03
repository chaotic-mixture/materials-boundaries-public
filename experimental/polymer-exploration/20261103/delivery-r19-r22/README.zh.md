# 聚合物r19-r22统一实验交付

本入口汇总experimental/open-database上的四轮本地成果，基线提交676df1abd3379f6c6d28bffe8c3685edd63d9b10。来源／契约、具体实现／映射、各批实际安装和本地接纳均独审通过；统一内容、最终安装及具体交付清单仍按本目录独审回执实际裁定。提交、推送、远端CI以精确Git／GitHub收据为准，不预先宣称通过。不合并main、不稳定发布／标签、不部署，广泛聚合物探索目标继续。

| 接纳轮次 | 新增性质／状态 | 统计与使用边界 |
| --- | --- | --- |
| [r19](../local-acceptance-r19/README.zh.md) | 2断裂伸长，沿用2既有状态 | PBS/PBAT未填充组，n5；中心统计及±定义不推定mean/SD |
| [r20](../local-acceptance-r20/README.zh.md) | NR Shore A 1性质／1状态 | 38.0±0.8 mean/SD、n5；来源名义3mm，1mm制样差异和具体路径未知 |
| [r21](../local-acceptance-r21/README.zh.md) | Sylgard Shore A 5性质／5状态 | 来源95%CI，n4每样8点，不算32独立试样；确切硬度固化时长、测试环境未知 |
| [r22](../local-acceptance-r22/README.zh.md) | Sylgard压缩模量／极限强度10性质／5状态 | 来源MPa／95%CI，压缩n未知；单位／范围及Ec异常提取关系逐条保留 |

累计18性质、11新试样状态，无新身份／牌号／来源。全部5298前驱性质完整对象不变；2既有状态仅version/property_ids/source_scope修订，3来源仅追加claim_notes，原备注保留。见NATIVE_DELTA_R19_R22.json。快照25d66658d21c8aebad75b875b2da82c121a99f893ddde3965a837cc955f12ba6，全库5180身份、31牌号、5206状态、5316性质、133来源；聚合物1037身份、1063状态、1157性质，1000计算与157实验参考只是证据分类标签，不当科学认证或独立试验组数。

新增三个quantity：shore_a_hardness、compressive_modulus、compressive_strength。硬度是无量纲经验标尺，shore_a_scale为应用上下文码，不是新物理单位；中央0至100含端点，绝对SD／CI用标尺点，95%置信水平typed percent另列。两种压缩量复用pressure和正值语义，无新单位／维度／schema分支；四个互斥分支保持，旧伸长原文百分数、绝对百分点、相对percent及压力目标规则不变。不跨硬度标尺或端点换算，不借强度／汇总伸长／Young值反算模量或本构。

压缩Table3／Table5的MPa不消除摘要UCS的GPa冲突；摘要40%适用范围与正文约55%近线性描述均不是明确拟合窗或失效判据。五条Ec明确保留作者约高于Young两个数量级、温度趋势相反的主张及与Figure6实际提取关系未知，不作物理认证、千倍／导数／割线／泊松比修复。压缩自己的20°C39%RH平均环境、20mm/min及油润滑不移给硬度；22°C冷却不作测试环境或湿度平衡。硬度4样×8点不补32独立样／批次，压缩n不从总60／拉伸6／硬度4推算。

原文未知几何、调湿、速率／应变约定、校准、标准合规、统计及独立批次继续未知。NR断裂伸长mm/mm疑点、三条高PCL断裂及两条PA12统计暂缓记录继续保留；登记状态不当更正／撤稿不存在或单位已澄清。来源限定目录不输入计算器，不作工程许用值、普适界或科学认证。

[当前条件清单](../condition-gaps-r3/native-r22/README.zh.md)覆盖157实验参考、12主要来源：100温度、105调湿字段未报告，67条有确切n，86条n为空、4条仅下限，确切n未确认90条。按性质对象计数，不能当独立试验／缺失事件数，也不计算完整率；reported可能仅处理／冷却时间，不证明RH完整或湿度平衡。

本次统一交付在当前5316性质、最新运行时及主文档上重新执行146相关测试，失败0、错误0、跳过0，108输入执行前后不变。每日数据库19项是其中子集，不累加；当前全图、C11000示例导出及完整性校验通过，见SCOPED_TESTS_R19_R22.json及DATABASE_CI_LOCAL_EQUIVALENT_R19_R22.json。不把各批旧146／140／单独6试跑累计为新测试数量。完整历史回归、HTTP／平台全量及旧批次CI未运行。

最终验证包拟用当前原生三表和本次README，隔离版本0.35.0+polymerdelivery.20261103.r19r22，原生软件仍0.35.0。内容批准后才构建最终包；实际结果与安装独审以INSTALLED_VALIDATION_R19_R22、NATIVE_INSTALLED_EQUIVALENCE_R19_R22及对应回执为准，不能用旧预览代替最终文档安装。只验证用wheel，不是稳定发布。

当前消费者核验拟限定实际最终安装core与冻结的进程内CatalogSnapshot：13个受影响状态、18新性质、3来源（Mtibe9／Bianchi12／Johnston25）共46完整关联查询／导出。实际执行以CURRENT_CONSUMER_VALIDATION_R19_R22收据为准；组件版本不同于数据库快照，不声称HTTP、联邦平台或固定历史平台套件通过。历史测试／pin保持原样，不重写为新基线。

五份主要说明先归档再更新。HISTORICAL_INPUT_RESOLUTION_R19_R22解析29组冻结历史上下文、996项绑定，零未解析；包括旧测试前后输入。核心／schema／文档解析至精确上下文存档，旧三表至各批恢复副本，旧阶段“待安装／尚未实现”只代表其冻结时点。最终当前69项package输入另行绑定；最终新增证明文件以当前精确字节复核，不冒充历史执行。

EXTERNAL_SOURCE_BINDING_R19_R22核对35组外部上下文、118个唯一保留文件、219项绑定；当前整合CLI／远端基线6文件另绑EXTERNAL_EXECUTION_BINDING。首次外部绑定检查因r19使用baseline_directory_hint命名而在写收据前停止，按其明确声明的目录续验，未放宽路径／SHA校验，见EVIDENCE_BINDING_ATTEMPT。原文、页图、三表恢复／预览、wheel和日志在仓库外，仅绑定哈希，不打包进仓库或wheel；404诊断体不会因.xml后缀变成文章证据。本整合未刷新原文／PDF视觉，最新通知、修订、更正／撤稿覆盖完整性未知。

WORKFLOW_SCOPE_R19_R22记录未改动的分支push配置：database-checks Python3.11/3.12，每日19子集加当前图／导出／校验和示例artifact；不把远端日常CI说成146全套或完整历史。其余专用分支／tag／手动任务不由本交付主动触发。DELIVERY_MANIFEST_R19_R22定义后续具体交付路径；真正提交前须统一内容／安装／清单独审，推送前重查远端且仅实验分支，无force、main合并、稳定tag或部署。
