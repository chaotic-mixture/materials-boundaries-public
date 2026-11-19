# R12 与 R13 恢复审计

独立副本以 R13 为底，保留其全部原生对象。restored-data.json 包含已恢复的 265 条性质和关联材料、状态、牌号及来源。restored.csv、remapped.csv、pending.csv 分别列出恢复记录、16 对替代 ID 和 426 条待查记录。验证结果见 validation.json。恢复部分通过材料规则验证；R13 基线与恢复副本的全库校验均在原有 ZTA 弯曲强度记录处失败。此包用于恢复审阅。

莫来石重建脚本要求显式指定全新的输出目录，检查输入指纹和消失的性质 ID。公开目录的 GitHub 检查按提交基线逐 ID 对账。确需撤销或替换时，在 docs/catalog-transitions/<基线完整 SHA>.json 中按旧 ID 记录 action（remove、rename 或 merge）、evidence 和替代 target（适用于 rename、merge）。
