# 聚合物方向：本地统一独审入口

本清单汇集已完成生产者核验、尚待独立审阅的具体成果。它不是接纳报告，不授予子代理权限，不声明各批已通过独审。以前针对其他批次的授权不自动覆盖这里的新范围。

原生快照仍为 `aa8308dbec8817ee6551078ed91bedb2a9fb05c7924fd76a9131cc680617a95f`。当前组合入口为[组合预览r3](combined-preview-r3/README.zh.md)，涉及22条新增性质和22条既有性质更正，身份不增加；PA12风化仅为来源审计，不在原生组合中。

| 序号 | 只读审阅范围 | 精确入口 |
| --- | --- | --- |
| 1 | 丝材绘图对象方法、1/10mm/min冲突、22条更正及11个状态说明 | [冻结输入](filament-drawing-method-audit/REVIEW_INPUTS_R1.json) |
| 2 | PA12风化论文/数据集许可、Table2与CSV/PDF对应、独立数值诊断和原文矛盾；不接纳原生数据 | [冻结输入](pa12-weathering-source-audit/REVIEW_INPUTS_R1.json)、[后续证据](pa12-weathering-source-audit/REVIEW_SUPPLEMENT_R1.json) |
| 3 | PA12老化方法、条件和统计边界、5状态/8性质原生草案 | [来源审计](pa12-ageing-source-audit/AUDIT_INPUTS_R1.json)、[原生草案](pa12-ageing-sls-native-draft/REVIEW_INPUTS_R1.json) |
| 4 | PBS的9条既有状态强度、均值/SD/n、修订号与链接；R0暂缓理由 | [冻结输入](pbs-existing-tensile-draft-r1/REVIEW_INPUTS_R1.json)、[R0边界](pbs-r0-identity-audit-r1/DECISION_R1.json) |
| 5 | PUR仅覆盖LPO-1的过期来源说明更正，已收录4配方的范围与未知条件 | [审计输入](pur-existing-density-audit-r1/AUDIT_INPUTS_R1.json) |
| 6 | Şahin的5条既有状态强度、s_M与s_B分离、打印前干燥与后调湿、状态链接修订 | [冻结输入](sahin-existing-strength-draft-r1/REVIEW_INPUTS_R1.json) |

六项之外，还需核对组合r3的具体实现、来源限定查询/导出、差异计数、冲突检查和原生基线不变。`LOCAL_REVIEW_INDEX_R1.json` 绑定各入口及组合精确哈希，不能将清单中的“待审”读作“已授权”或“已通过”。

审阅只读，不修改文件、不推送、不重跑完整历史回归；不运行来源附带代码，不接触部署或main。可检查本项目可信提取/检查脚本，但运行范围须与具体审阅相关。返回问题位置、证据、严重程度、建议及针对确切哈希的结论；主会话负责修正与落盘，修正后再复核。独立转录审阅不等于科学同行评审或实验复现。

已独审并应用的 Sylgard r2 不重复开发，原审阅保留。NBR、NR、环氧的本轮补查，以及原生条件缺口清单，仍标为策展审计；不因本次统一入口而升级为独立审阅。NR的7条有限应变模量仅为来源事实，不在本次接纳候选中。R0不新增身份、状态或性质。

后续顺序：取得相应只读独审授权 → 审阅并修正 → 新冻结快照与受影响回归 → 具体本地接纳及安装/交付核验 → 达到较大进度后统一推送。不得由图检查直接跳到接纳；未核实的结果保持未知。不合并main、不部署。
