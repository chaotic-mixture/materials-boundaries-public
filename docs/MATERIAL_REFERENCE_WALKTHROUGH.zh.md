# 材料参考：从检索到证据阅读

本页帮助你在已有目录中找到材料、定位某个状态的属性，并读懂数值附带的条件与来源。
传统配方示例依据实验提交 `f13586759af6a391635fa81da20c73eb6a6c1c6c` 中的已接纳记录；
计算来源入口及字段按各自固定来源版本说明，接纳状态以对应验收决定为准。本文
不新增材料、属性或科学结论，也不代表 main 或新版本发布。

## 先选对内容入口

| 你想查什么 | 入口 | 阅读时需要区分 |
| --- | --- | --- |
| 某种材料、牌号、加工状态及其参考属性 | `catalog materials`、`catalog reference-properties` | 身份、牌号、状态和属性是不同对象 |
| 文献中的特定试样观测 | `catalog observations` | 试样与方法限制不能外推到整个材料家族 |
| 计算来源参考密度（JARVIS、PolyOmics） | `catalog reference-properties --evidence-kind published_computational_reference` | 保留具体模型、密度基础、方法和未知条件 |
| 预测目录中的模型结果 | `catalog predictions` | 预测对象与材料参考对象分别阅读 |
| 数学界、力学关系及适用假设 | `catalog claims` | 目录中的关系并不都能执行计算 |
| 用明确输入做复合材料计算 | `composite` 工作流 | 仅使用已有八条规则；目录数值不会自动成为输入 |

计算来源参考密度的固定版本与使用边界，见[来源和条件说明](MATERIAL_SOURCE_CONDITIONS.zh.md)。

材料参考的完整接口见[材料目录指南](MATERIAL_REFERENCE_CATALOG.md)，
计算入口见[复合材料工作流](COMPOSITE_WORKFLOW.md)。

## 第一步：检索材料，再保留精确 ID

在含有 `materials_boundaries` 的项目根目录运行以下命令；`python` 应指向已配置好的
Python 3.10 或更高版本环境。查询命令只读目录，不写入报告文件。

先按材料名称找线索：

```sh
python -m materials_boundaries catalog materials --query "PLA/PCL" --category polymer --text --lang zh
```

名称检索是大小写折叠后的字面包含匹配，不推断化学等价，也不自动翻译关键词。
类别代码、精确 ID 和属性代码区分大小写。多个筛选条件按 AND 组合。

找到目标后改用精确 ID。例如，B95/5 是 Delgado-Aguilar 2020 研究限定的
PLA/PCL 标称质量配比，不代表所有商业 PLA/PCL 95/5 产品：

```sh
python -m materials_boundaries catalog materials --identity-id mat_delgado2020_pla_pcl_b95_5 --text --lang zh
```

此身份对应的注塑状态 ID 为
`state_delgado2020_pla_pcl_b95_5_injection_molded`。保留身份和状态两个 ID，
可以避免以后把同名材料、不同来源或加工状态混在一起。

## 第二步：定位该状态的某个属性

用状态 ID、属性名称和来源共同定位 Young's modulus：

```sh
python -m materials_boundaries catalog reference-properties --material-id state_delgado2020_pla_pcl_b95_5_injection_molded --quantity youngs_modulus --source-id delgado_aguilar_2020_pla_pcl --text --lang zh
```

这里的 `--material-id` 接收**状态 ID**，不是身份 ID。
精确属性 ID 为 `refprop_delgado2020_pla_pcl_b95_5_youngs_modulus`，
可直接读取规范 JSON：

```sh
python -m materials_boundaries catalog reference-properties --id refprop_delgado2020_pla_pcl_b95_5_youngs_modulus --json
```

`--lang zh` 改变文字界面，不能把来源没有报告的条件补齐；切换语言也不会改变规范 JSON
中的数值、单位和来源措辞。筛选无结果时先检查 ID、来源与属性是否确实属于同一个状态，
不要把空结果当作材料没有该物理属性的证明。

## 第三步：把数值、统计含义与未知条件一起读

以下内容来自该提交的目录转录。本页未重新检查原始论文，也未重新核验原始文件哈希。

| B95/5 记录中的项目 | 已有记录 | 应保留的解释 |
| --- | --- | --- |
| Young's modulus | `3.70 GPa` | 保留来源字符串与尾零 |
| 标准差 SD | `0.13 GPa` | 与中心值分开记录；不是 SEM 或置信区间 |
| 中心统计量 | `not_stated` | 不能据 SD 存在而补写“均值”或“中位数” |
| 试样／测量数 | 未报告，值为 `null` | 不能推断重复数或独立生产批次数 |
| 横梁速度 | `2 mm/min` | 不是局部试样应变率 |
| 夹具间距 | `115 mm` | 不能当作引伸计标距来推算应变率 |
| 拉伸试验温度、湿度、压力 | 未报告 | 不能用加工温度、注塑压力或所谓标准默认值代填 |
| 引用的试验标准 | `ISO 527-1:2012` | 表示论文引用该版本；独立符合性核验未完成 |

继续阅读 JSON 中的 `method_definition`、`conditions`、`sample_count`、
`uncertainty`、`evidence` 和 `source_document`。来源定位说明 Table 2 的模量列，
通过体积分数行与 Table 1 的 B95/5 配方关联；SD 的解释来自第 3.2 节式 (6) 后的段落。
体积分数在这里用于来源表格关联，不能当作新增的实测属性。

来源记录标识为 `delgado_aguilar_2020_pla_pcl`。目录记录了官方 XML 与 HTML 的有限检查，
没有核实原始 PDF 字节、页面或 PDF 与 HTML 的等价性。文件哈希有记录也不等于本页
已经重取原文并独立复核。更详细的加工条件、权利说明和证据限制见
[PLA/PCL 集成说明](MATERIAL_GROWTH_DELGADO_PLA_PCL_20261026.md#source-and-measurement-scope)。
该文档中的历史发布状态须结合[交接入口](../HANDOFF.md)及对应提交理解。

## 如何记录一次可复查的引用

在自己的研究笔记中至少保留以下内容：

1. 仓库完整提交 SHA、身份 ID、状态 ID、属性 ID。
2. 来源 ID、具体表格／章节定位、目录记载的来源版本和检查范围。
3. 原始数值字符串、单位、中心统计量、单独的 SD 或其他不确定度说明。
4. 已报告的测试方法、加工条件，以及仍未知的温度、方向、调湿与样本数。
5. 哪些是文献转录、哪些是目录软件校验、哪些尚未独立复核。

参考属性保持 `catalog_only`、`universal_bound: false` 和
`engineering_allowable: false`。单个参考数值不能自动提供设计许用值、材料排名或
通用强度界；不同协议的数值也不能直接据此作同条件比较。

## 数量与覆盖应怎样理解

上述固定提交的材料注册表包含 1175 个身份、31 个牌号、1176 个来源限定状态和
1187 条参考属性；共享来源注册表有 129 条记录。这些对象不是可以相加的材料数。
身份包含某种材料，不意味着其全部属性、温度区间或失效模式已知。

```sh
python -m materials_boundaries coverage --text --lang zh
```

`coverage` 提供目录中定义的覆盖统计。实验项目另记的 24 条已审核计算组成，
与上述来源限定身份分别计数；1199 是交接文档定义的实验项目总量，
不是 1199 个来源限定身份，也不是此时 main 的实时数量。
main、release 或部署现状需要针对实际远端版本另行核实。

## 继续阅读

- [PLA/PCL、反应型 PBS/木质素与 curauá/RPUF 的来源、条件和使用说明](MATERIAL_SOURCE_CONDITIONS.zh.md)
- [材料参考目录：筛选规则、数据模型与贡献流程](MATERIAL_REFERENCE_CATALOG.md)
- [五类材料分类与身份边界](MATERIAL_TAXONOMY.md)
- [批量导入：候选、保留与明确接纳](BULK_INGESTION.md)
- [科学及来源审核关卡](BULK_INGESTION_DESIGN.md)
- [中文快速开始：计算与观测工具](GETTING_STARTED.zh.md)
- [交接入口及暂停范围](../HANDOFF.md)


## 检索鲜态配方的流动扩展度

SCC 文献汇编记录从 `reference-properties` 读取，筛选独立长度量 `slump_flow_spread`，不能改走压缩强度、密度或计算预测入口。单状态示例：

```sh
python -m materials_boundaries catalog reference-properties --source-id scc_zenodo_10569517_v1 --material-id state_scc10569517_04cd95308a290a9191e0e255_reported_fresh --quantity slump_flow_spread --text --lang zh
```

核对 mm 原标量、compiled 汇编证据、原引文、CSV/工作簿差异和未知 n/标准/温度；项目风险分组信息在策展范围说明中，不充当作者试验条件。见[来源与条件说明](MATERIAL_SOURCE_CONDITIONS.zh.md#scc-鲜态配方的流动扩展度)。这条检索命令和隔离目录计数不构成最终接纳或发布证据。
