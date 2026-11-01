# 聚合物来源链与 COD 无机来源核查

本页补充本轮[来源盘点](README.md)，不接纳新身份，也不改变五类配额。
下列文件摘要和检查结果来自本地固定输入；未知项不按来源规模推定完成。

## 聚合物 Tg 来源链

已固定 PolyMetriX 仓库提交 `5b89d4e7487959cfa2f7a47e876cb4066d630d2d` 的
[`docs/datasets.md`](https://github.com/lamalab-org/PolyMetriX/blob/5b89d4e7487959cfa2f7a47e876cb4066d630d2d/docs/datasets.md)。
其说明将 `labels.Exp_Tg(K)` 定义为贡献值中位数，而不是统一测量协议下的单次实测 Tg。
对本地固定 CSV 的核算：279 行显式贡献值列表均与 `meta.num_of_points` 和精确十进制
中位数一致，未发现列表长度或中位数不符。其余行没有显式贡献列表，本轮未复算原始测量。
贡献条目数与跨来源离散性不能转成独立试样 n、生产批次数或单次试验误差。

GREA 当前[固定 README](https://github.com/liugangcode/GREA/blob/ce02bf1930fa01161dacca0f4cca74c0a31a26aa/README.md)
记载 NIMS MatNavi 要求移除 GlassTemp、MeltingTemp 和 PolyDensit 数据的通知；同提交
说明为 `delete polymer datasets`，当前树已没有其 Tg CSV。暂存表中 7170 行标记 GREA，
这些行暂不进入接纳；另外 197 行也没有因此自动通过权利审核。单个 `meta.source` 标签
不列举一个聚合值的全部上游贡献。本轮没有恢复或下载已删除的上游文件。

已把六个现存标签映射到作者提供的来源链接。Qiu 的原数据路径已不在当前树中，
两个 ACS 链接返回 403；Xie 数据与 Uchicago 页面可读，但逐行匹配及许可范围仍未核实。
访问状况、固定提交和待审项见[证据记录](polymer-lineage-evidence.json)。

下载记录 `15789599`、当前文档默认记录 `15210035` 与论文数据声明 `14980914`
是不同 Zenodo 标识；本轮没有认定三者字节或事实等价。
下游 CC BY 标记和上游软件 MIT 许可均不能替代尚未解决的来源链审核。

## RadonPy 的另一组聚合物来源

已取得[作者仓库固定数据](https://github.com/RadonPy/RadonPy/blob/8834b9071ae93d9af36558a3c24545dd52e5ba1a/data/PI1070.csv)，
这是 MD 计算数据方向，不是对 Tg 数据的实测替代。
源文件长度 1598888 字节，SHA-256
`4ee41d526db3d03eb5b83010672b4e63a4d51a114871a2187ca7fd57d30556a4`，
并与官方 Git blob `109a773f3da95043cc7861aad3e4e67140865ace` 一致。

实际 CSV 含 1077 行、1077 个不同 ID 及 SMILES 字符串；文件名和 README 的 PI1070
字样不能代替实际核算。其规范身份数、与现有目录的重叠、与论文 1070 集合的关系均未知。
密度中心列均位于源 min/max 之间，count 列为正整数；这仅说明内部数值一致性。
`temp` 字面值均为 `300`，`press` 均为 `1`；单位、统计量、模拟版本关联需要按原方法审阅。
未选取 PoLyInfo 的实验验证值，未重新运行 MD，也未把模拟副本数当作实物样本数。

相关论文为 Hayashi、Shiomi、Morikawa 与 Yoshida（2022），
[RadonPy 方法论文](https://www.nature.com/articles/s41524-022-00906-4)。
仓库 BSD-3-Clause 与论文 CC BY 4.0 已观察到；数据文件的适用范围及结构来源仍待审核。
现有参考目录支持 `published_computational_reference` 分类，但来源规模、文件可读和
软件校验均不构成材料接纳。本组目前接纳增量为零。

## COD 无机材料来源

[COD 官方主页](https://www.crystallography.net/cod/)声明数据库及贡献数据为 CC0，
并要求致谢原始结构作者。[官方 API 文档](https://wiki.crystallography.net/RESTful_API/)
支持元素筛选、JSON 元数据、CIF ZIP 和按 SVN 修订读取单个 CIF。
已读取有限查询：ID 以 1 开头、含 O、不含 C、最多三个元素。

- 元数据：3902 条；2833 个不同的原始化学式字符串。
- 精确有理数组成比筛选：2788 组；仅合并元素顺序和整体倍数，不推断材料或物相等价。
- 原始元数据 SHA-256：`d193614fafc30fa1ace4e83f9a308f780a5e049c324cbbd1b15852c8dadcca07`。
- 可行性样本：50 个不同组成组的 CIF；逐文件摘要已保留，全部头部修订号与元数据一致。
- 其中 8 个文件有密度标签行，包含衍射计算密度及测量密度两种标签；原字面值保持区分。
  这是标签可用性盘点，尚未进行完整 CIF 语义、单位、不确定度及原始文献审阅。
- 样本 ZIP SHA-256：`20b8db98cc4a5f133a5c95ea3d3272f52a90f915d41fa9c73a05ee533577c4ec`。

因此，2788 不是已接纳材料数，也不能宣称已有 2788 个可接纳密度值。
缺失密度没有从晶胞参数自行补算。下一步需扩大具有可核实属性的筛选，使用完整 CIF
解析器，核实具体修订、量的定义与来源，并与已有 59 个无机身份交叉映射。
详细样本记录见 [COD 盘点结果](cod-source-probe.json)。

## 离线复现

所有命令从项目根目录运行，输出到新的文件路径；程序不发网络请求、不写运行目录。

```sh
python -B experimental/material-batches/quota1000-source-audit-20261027/audit_polymer_lineage.py --tg PATH_TO_PINNED_TG_CSV --radonpy PATH_TO_PINNED_PI1070_CSV --output NEW_POLYMER_AUDIT_JSON
python -B experimental/material-batches/quota1000-source-audit-20261027/audit_cod_probe.py --metadata PATH_TO_COD_JSON --archive PATH_TO_PROBE_ZIP --output NEW_COD_AUDIT_JSON
python -B -m unittest discover -s experimental/material-batches/quota1000-source-audit-20261027 -p "test_*.py" -v
```

完整输入仍保存在仓库外本地缓存；仓库内只有选取事实、摘要、原始定位与审核脚本。
新增检查覆盖十进制中位数、错误计数、非有限值、来源摘要变更、组成倍数去重与歧义拒绝。
它们不替代独立科学审核、接纳、完整运行回归、安装检查或远端 CI。
