# 既有PBS/PBAT两条断裂伸长率：本地接纳 r19

来源／复用契约、具体映射和实际隔离安装均获独审批准。原生应用、恢复及安装等值已通过生产者核验；最终接纳独审以INDEPENDENT_ACCEPTANCE_REVIEW_R19.json为准，该回执产生前仅称生产者接纳核验通过。

| 既有状态 | 原文Tensile Strain at Break % | 来源统计与n |
| --- | --- | --- |
| PBAT Ecoflex C1200 | 1040±9.76% | reported_value，±定义未知；组n5 |
| 未填充PBS/PBAT70/30 | 367.01±86.87% | 同上 |

复用tensile_elongation_at_break/dimensionless/percent_elongation；原数不除100、不截100，±为原百分数尺度的绝对伸长百分点，不作相对误差或SD/SE/CI。n5不定义中心统计量、配对曲线、排除样本或独立批次，未宣称均值。没有规定伸长目标；新断裂记录移除从屈服基准复制的yield_criterion，旧屈服记录及其未知判据完整保留。

§2.6.2明确25°C测试、25°C/48h处理、5试样/组、Instron与ASTMD638引用。RH、数值速率、实际标距/应变估计/约定/断裂选点、标准版本/独立符合性、批次和含水平衡未确认。成型、商业牌号和配方不证明纯化学成分；不增新纯PBS、填充ZnO/木质素或其它配比状态，不把模量/屈服强度换成断裂伸长、能量、韧度或许用值，不接引擎。

原文§3.2的15wt%填料伸长下降约167%叙述作为未核实来源上下文保留；不修复所选表值，不接纳相对性能指标或填充材料效果。来源是保留CC-BY4.0官方XML，SHA256 aa495787abc73a0d98b8c8adbb3c887816afe57076873010b04d41a6730b7f32；无新下载/PDF视觉/最新修订、更正或撤稿核验，相关状态未知。

[选定表格排除证据](../elongation-table-exclusions-r19/README.zh.md)另经只读独审：EwurumPBS Table6、AbbasiPHBV Table9没有明确伸长率/应变列，不能由这些表形成该量记录。只限所选两表，不证明全文/补充材料缺数据，不做曲线数字化或强度/模量相除；既有PHBV四性质保持。

当前原生快照35c10b8bcde2e5d0c5c1266dc98e428962683009d0a4d4511ba3f2f301cf6153：全库5180身份、31牌号、5195状态、5300性质、133来源；聚合物1037身份、1052状态、1141性质，其中1000计算及141实验参考仅为证据分类。全部5298旧性质完整对象保持，无新身份/grade/状态/来源；仅2状态version/property_ids/source_scope、1来源追加claim_note变化。

本批三表schema/format、当前图、完整来源7→9导出及四语通过；接纳5300条性质检查实际执行、复用0。运行时/schema/本地化未改，未重跑套件，不将已推送676df检查点的135项测试和远端CI冒称本批新测。完整历史回归、HTTP/完整平台、本批远端CI未运行。

实际隔离版本0.35.0+polymerpreview.20261103.r19，wheel SHA256 7f08c2981f5250de282db4aa5aa928564c90a7b379d5f4f38df3f4de0ddcc137。69输入、65载荷、6元数据及本地wheel来源已核验；除隔离版本外64原生载荷逐字节一致，3表及全部5300性质等同实际安装。该来源9条完整joined对象逐对象一致，其中3条为原有复合材料记录，不全是聚合物新增。wheel含应用前README，不冒称包含后续接纳文档。

APPLICATION_R19、APPLICATION_INTENT_R19、INCREMENTAL_VALIDATION_R19及NATIVE_INSTALLED_EQUIVALENCE_R19记录真实应用、恢复及等值；旧69包输入的3张表解析至r19恢复副本，其余当前字节保持。[当前R3条件清单](../condition-gaps-r3/native-r19/README.zh.md)覆盖141实验性质/12主来源：95温度、104调湿未报告；61来源报告确切n、76数值为空、4仅下限，确切n未确认80。按性质对象计数，非独立试验组、批次或材料；reported也不证明完整调湿/RH。

分支experimental/open-database，HEAD676df1abd3379f6c6d28bffe8c3685edd63d9b10。本批未提交/推送，继续本地积累后统一交付；不合并main、不稳定发布、不部署。旧冻结草案保留各阶段原貌。
