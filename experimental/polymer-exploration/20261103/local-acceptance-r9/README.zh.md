# 规定伸长率下拉伸应力：r9 本地接纳（2026-11-03）

来源/概念、实际代码/schema/四语言/测试/两条映射、实际隔离安装均获只读独审批准后应用。当前新量`tensile_stress_at_specified_elongation`为pressure，必需typed `specified_elongation`；其他量禁止该字段。新增2条既有REF性质，身份/状态/牌号/来源增量0，旧5243性质对象全部不变。本轮未提交、推送、main合并、稳定发布或部署。

原生快照`06d8e433c7c28c7b3b10c7a8f9432082a6ccad789f3e0aac7fb50c08d717c7c5`，实际5180身份、31牌号、5195状态、5245性质、133来源。聚合物1037身份、1052状态、1086性质（1000计算来源、86实验来源标签，不是科学认证）。

## 新事实与表示

| 原文标签 | 来源百分比目标 | 应力/MPa | 所报±/MPa |
| --- | --- | --- | --- |
| M100 | 100% | 2.46 | 0.71 |
| M200 | 200% | 3.87 | 1.14 |

值来自Tamás-Bényei/Sántha2025原文Table4 REF及§3.3，沿用保留XML SHA-256 `2d8008e2b16dd3fe14b91a6747fb3632c70b461ccee4ccc8dea546dc3c272347`。本轮无新PDF。CC BY4.0事实署名沿用，Figure1第三方内容排除，标准/原文全文不打包。

[ISO官方摘要](https://www.iso.org/standard/86892.html)及[GSO公开的ISO作者术语预览§3.7](https://gso-sims-preview-doc-aws.s3-eu-west-1.amazonaws.com/iso-37-2024-en.html)只辅助区分橡胶M称呼与应力—应变斜率。它们不识别论文作者所用标准版本，也不证明符合性；不分发标准正文。MPa值直接保留，不除以百分比，不计算Young、切线或割线模量，不作最大/屈服/断裂应力重分类。

`specified_elongation`保留value_text/number、%/percent、source_reported_percent_elongation、主来源condition证据及notes。它是来源给定的参数，不认证每个试样实际达到目标、工程/真实/对数应变实现或伸长比。中心结果仍为压力单位，percent只用于目标。正目标可大于100。平均、逐目标参与人数、方向权重、点提取/平均顺序及±类型未知，n不从方向数或其他试验移用，也不假定与强度组样本相同。原温湿度、调湿、标距未知保持；source-level摘要/表格强度矛盾不替作者修正。

## 实际核验

| 范围 | 结果 |
| --- | --- |
| 具体实现独审 | 两封闭互斥schema分支、正有限目标/原数值一致性/百分比单位/basis/主来源证据；10个独立内存负例拒绝 |
| 去重 | 100与100.0不能凭格式增记录，100与200可区分；低精度Decimal context不舍入目标身份 |
| 专项单测 | 本轮实际119执行/119通过，失败0、错误0、跳过0，含7项新型契约用例和既有相关组；原始日志绑定 |
| 全图与三表schema | 当前5245图契约、Draft2020-12及format检查通过；旧5243完整property不变 |
| 增量 | 全局执行；来源变化导致reuse0，执行全部5245性质检查并通过 |
| 查询/四语言/导出 | 独审者实际四语渲染正确显示100%/200%及原MPa；before8/after10的完整joined对象与独立查询一致 |
| 实际安装 | 69source/stage、65payload、6元数据、wheel71/installed76个带hash RECORD项及来源/版本核验通过 |
| 当前原生等值 | 三表字节相同；当前65payload仅隔离版本标记不同；原生10条joined记录等于安装导出 |
| 未执行 | 完整历史回归，本轮提交/推送/远端CI、main合并、稳定发布、部署 |

全部记录catalog_only、非界、非许用值，没有新增engine/conversion接线或自动计算器输入。119项为本轮真实执行，不反写r8当时“继承112、未重跑”的历史收据。

wheel SHA-256 `ba976c15019f6e6e0c431ff0d8c0ba3481598748dadd9146bd4f143395fd7ffa`；仅隔离副本版本`0.35.0+polymerpreview.20261103.r9`，仓库仍0.35.0。wheel含应用前r8 README，不声称包含后续r9文档。direct_url.archive_info为空，来源证明依据本地URL、独立哈希和安装字节一致性。

应用前恢复表见APPLICATION_INTENT_R9；五份更新前文档见PREACCEPTANCE_DOCUMENT_BINDING_R9；旧r8代码/schema/locale/test哈希可由HISTORICAL_CODE_BINDING_R9的Git8735dfc解析。冻结候选保留原阶段，最终状态由具名批准/应用/复核收据决定。本轮远端最新未核实，继续积累较大本地进展后统一交付。
