# 修正后完整新环境路径的后续核验

冻结的 `build_and_verify.py` 已在第二个全新仓库外目录完成构建、安装、负载/元数据核对、快照读取和CLI导出/校验，未使用 `--resume-existing`。不重跑来源审计或完整历史回归。

`CLEAN_RUN_VALIDATION_R3.json` 保存本轮完整新运行结果；`CLEAN_RUN_COMPARISON_R3.json` 比较两次实际构建。69个构建输入、wheel内所有成员名称及逐成员字节相同，数据库快照均为 `ea288ee80aae4b5bba931b5e62cb32cf6b3c8b805bf457084f52bde54a585b4f`。归档时间戳不同，两个wheel的文件哈希分别保留，不声称归档逐字可复现。

本次新wheel SHA-256为 `c8896d6556dc28e19d85b344047fdcd308abdc782b060d00a168638410aa24ae`。早先wheel及两次记录脚本失败均未替换或删除。

这一补充证明修正后的新建流程与恢复流程均实际通过，不改变任何候选的独审、接纳或发布状态。原生库、Git索引及版本文件保持不变。未推送、合并main或部署。
