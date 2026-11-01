# JARVIS 计算密度：2000 条冻结来源事实候选

**金属 1000 条、无机 1000 条来源事实提案，接纳增量为零。**
这不是运行目录包；`handoff_ready=false`。新计算密度方法尚未实现，具体身份、分类与
重叠处理仍待独立核验，不能把这 2000 条加入材料配额。

输入是[已经独立核验的完整来源审计](../quota1000-jarvis-source-audit-20261027/REVIEW_STATUS.md)
中的固定组成索引。候选文件 SHA-256：
`70e6664d18250098ac28cb2e7fd7eff745427a30cbdf69cf972c01529976afdb`。

每个组成组保留最小数字 JID 的原报告模型与密度字面值；不同物相、晶胞或重复源行不增加
该组成的提案数。不选择最低能量、不计算跨行平均、不宣称最稳定相或实验存在。
源行索引与原始行文本摘要保留在每条候选中。

候选准备基线是 HEAD `f13586759af6a391635fa81da20c73eb6a6c1c6c` 的本地工作图，
包含尚待最终接纳的 5 个 Sanchez 铝合金。三个目录和原有 24 个正式计算组成分别固定摘要，
未修改它们。后续运行整合必须先关闭当前铝合金回归，并重新核对基线字节。

筛选先排除已有 24 个正式计算组成，另对现有无机化合物和合金家族设置保守的配方/元素组
排除。这些排除只是把可能重叠项留待处理，不表示这些材料化学等价，也不替代完整身份审核。
只选择 2–4 元素的全金属组，以及 2–3 元素、含 O 且不含 C/H 的组。
经这些规则后储备为金属 13,934 组、无机 3,848 组，各按数字 JID 顺序取前 1000 条。

温度、压力、逐记录收敛、物相稳定性和实验存在均保留未知。拟用单位为 g/cm³，
拟用证据类为 `published_computational_reference`，并依赖已审阅但未实现的
`source_reported_computational_structure_density` 方法；不会将计算晶胞密度改标为实测值。

```sh
python -B experimental/material-batches/jarvis-density-candidates-20261027/select_candidates.py --index PATH_TO_VERIFIED_COMPLETE_SOURCE_INDEX --output PATH_TO_NEW_FROZEN_CANDIDATES
python -B -m unittest discover -s experimental/material-batches/jarvis-density-candidates-20261027 -p test_selection.py -v
```

具体候选与全部排除规则见 [source-fact-candidates.json](source-fact-candidates.json)。
原始数据 ZIP 与完整组成索引仍保存在仓库外，本包只包含选择后的事实与原创整理。
