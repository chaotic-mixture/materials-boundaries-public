# DFT 晶胞密度的待审接纳契约

状态：**提案；未实现、未独立审阅、未接纳**。本提案不修改运行目录、schema、
验证器或当前铝合金回归输入。

## 为什么现有字段组合不足

当前 `material_references.py` 支持 `published_computational_reference`，并要求其
`determination_basis` 为 `source_reports_calculation`。但是
`density_basis=crystallographic` 被双向限定为
`source_reported_crystallographic_derivation` 方法；该方法又被限定为
`published_measurement_derived_reference`。它描述现有实测晶胞输入的密度推导，
不能诚实表达 DFT 优化结构的计算密度。

不能为通过校验而把已知晶胞基础写成未知、实测体密度或测量输入推导，也不能把
DFT 密度归入实验值。本轮仅审计源事实，不生成冒称 schema 已通过的候选包。

## 拟增加的有限方法类型

建议增加独立方法类型
`source_reported_computational_structure_density`，保留物理基础
`density_basis=crystallographic`，但明确其结构是计算模型。

新增类型应同时满足：

1. `quantity=mass_density`，`quantity_dimension=mass_per_volume`。
2. `evidence_kind=published_computational_reference`，
   `determination_basis=source_reports_calculation`。
3. 原文实际报告该标量，保留原始数值 token、单位和精确记录定位。本项目不重新
   优化结构、不计算新密度、不用原子质量或体积重算值冒充报告值。
4. 方法与分类证据明确连接计算结构、密度字段和单位。记录泛函、源 JID、文件版本、
   字节摘要、行定位及该行的原文摘要。源报告的晶体对称性保留为源报告，不声称独立求解。
5. 原 `source_reported_crystallographic_derivation` 继续只接受实测输入推导；
   原经验转换、编译值与普通方法的双向分类限制保持。新类型不能解锁其他物理量。
6. 未报告的数值温度、压力、误差、试样数、稳定性与实验合成状态保持未知；不能把
   每个 JID 或一个计算值记为一个实物试样。静态 DFT 也不自动填为实测 0 K、室温或零压力。

`summary_statistic=reported_value` 可描述选定模型的源报告标量，不赋予平均值语义。
源文件没有给出此密度的误差时，保留未知误差，而非宣称误差为零。

## 身份与类别的边界

本轮的 14,028 个全金属元素组成组和 5,320 个不含 C/H 的含氧组成组只是筛选储备。
减少整倍数和改变元素顺序不能增加材料数；不同 JID、晶胞、空间群或计算状态也不能
自动计成新身份。组成分组本身不证明物相等价。

后续冻结名单须逐项保留完整精确组成键，并排除或处理：现有身份、牌号与配方的重叠，
已有 24 个正式计算组成，未解决的混合物/固溶体范围，以及类目不明确的情况。
全金属组成可提出金属族分类，但不据此宣称金属导电性、稳定性或实验存在。
含氧且无 C/H 的筛选桶也不是已批准的无机分类。

## 必须覆盖的负测与审阅

- 把计算晶胞密度改标为实验、手册或实测输入推导时拒绝；反向错标也拒绝。
- 将新增方法用于非密度量、非晶胞基础或不匹配的证据类时拒绝。
- 原始数值、单位、文件/行摘要、源 JID、组成与状态被修改时不能继承冻结审核。
- 源 `NaN`/`Infinity`、缺失、零与负密度不能进入运行数值；未选弹性字段的
  缺失标记只能留在来源审计，不能污染选定密度。
- 旧记录、分类限制、fixture、科学契约、输出与计算器行为需保留，并执行相应历史恢复。

实施前需要对本提案和冻结来源事实的独立审阅。实施后再运行 schema/runtime、来源忠实性、
身份去重、历史保留和安装核验。通过来源审计或本页描述，不等于通过这些门禁。

## 证据入口

- [固定 Figshare v11](https://doi.org/10.6084/m9.figshare.6815699.v11)，其元数据明确标记 CC BY 4.0。
- [官方方法文档](https://jarvis-materials-design.github.io/dbdocs/jarvisdft/)，
  说明优化结构与密度等派生标量的关系。
- [固定 Atoms.density 实现](https://github.com/usnistgov/jarvis/blob/3b0c9d0f0c15759135de857dbc93e010db01eb29/jarvis/core/atoms.py)，
  定义单位为 g/cm³。该代码提交与 2025 文件的实际生成版本关系尚未核实，不能倒填为已知。
- [来源证据记录](source-evidence.json)和[文件核验收据](download-receipt.json)。
