# 数据贡献和更新

数据记录的基本单位是“某个来源中、某个材料状态下的一项性质”，不是脱离条件的材料常数。身份、牌号、状态和性质各自保留稳定 ID；修订已有事实保留 ID 并更新记录版本，独立来源或不同状态使用新记录。

## 提交内容

1. 来源 URL 或 DOI、具体页码/表格/单元格、来源版本与检查日期。
2. 材料身份与状态、性质名称、原始数值及单位，不把单位转换结果冒充原始值。
3. 温度、方向、方法、样本量及不确定度；来源未报告时保留明确的未知状态。
4. 来源许可状态和实际收录内容范围。没有核实的许可不得填写为已开放授权。
5. 修改理由、受影响记录及新增/修改/删除列表。删除需要解释；不以更换 ID 隐藏更正。

现有机器格式位于 `schemas/materials.schema.json`、`schemas/reference_properties.schema.json`、`schemas/sources.schema.json`。候选提交遵守这些字段约束，不能仅通过数据库关联检查便宣称科学上有效。

## 三个阶段

- **候选**：PR 中的数据及差异报告，可以讨论和纠错，不进入已发布快照。
- **已审核**：审核人确认来源、转录、条件、关联及收录范围；记录审核人、时间、结论和精确数据指纹。转录核对不等于独立科学验证。
- **已发布**：从审核通过的精确数据内容生成快照，保留 manifest、校验和及变更记录。数据库内容指纹与软件版本分别记录。

当前 export 命令生成本地快照，不会自动授予“已审核”或“已发布”状态。

## 日常验证

先用概览定位需要核对的现有记录，再查询原始条件及来源。概览直接统计原生状态，
不会把未知改为已报告，也不授予审核或发布状态；来源许可按关联来源去重统计。

```sh
python -m materials_boundaries.database summary --category composite
python -m materials_boundaries.database query --query C11000 --quantity mass_density
```

```sh
python -m materials_boundaries.database check
python -m materials_boundaries.database verify --snapshot new-snapshot
python -m materials_boundaries.database diff --before old-snapshot --snapshot new-snapshot
```

比较两份采用相同过滤条件的快照。差异报告列出新增、修改、删除和受影响来源；来源元数据变化会传递到关联的导出记录。未使用来源的变化不会伪装成性质变化；完整数据库指纹仍会变化。

数据更新执行结构、引用和受影响科学约束检查；工具修改执行对应专项测试；公共契约、计算引擎及发布变更按影响范围增加回归。历史回放用于明确的兼容性或发布任务，不自动附加到每个文档与数据 PR。差异报告本身不代替科学约束检查。
