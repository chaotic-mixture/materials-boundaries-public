# PolyOmics 聚合物来源审计

状态：**仅来源审计，接纳增量为零**。完整 CSV 与作者说明保存在仓库外；这里保存
复现程序、文件核验收据和实际核算结果，不修改当前铝合金回归输入。

固定作者数据仓库提交 `cbab9483395a32dd968fbeb047808031fb0f3a13`，
数据 DOI [10.57967/hf/7475](https://doi.org/10.57967/hf/7475)。
[该提交说明](https://huggingface.co/datasets/yhayashi1986/PolyOmics/blob/cbab9483395a32dd968fbeb047808031fb0f3a13/README.md)
明确将 CC BY 4.0 用于数据集，由 RadonPy Consortium 发布；不是仅据软件许可推断数据许可。
关联研究为 Yoshida、Hayashi 等人的[PolyOmics 论文](https://arxiv.org/abs/2511.11626)。
本审计没有下载 PoLyInfo 实验验证数据或小分子子集，也没有认定它与旧 PI1070 文件等价。

## 已核验的实际文件

| 文件 | 字节 | 实际行数 | 单组分且两个星号的字面筛选行 | 该筛选内不同 `smiles_1` 字符串 |
| --- | ---: | ---: | ---: | ---: |
| PFAS.csv | 13,714,504 | 5,810 | 4,868 | 3,817 |
| biodegradable_candidate_polyester.csv | 778,096 | 372 | 372 | 323 |

PFAS 文件 SHA-256 与官方 LFS 摘要一致：
`2e80ce549bd6c6e4dfc765d842416278a18422d169859939dd88ec41b61c5529`。
聚酯表与官方 Git blob 一致；SHA-256：
`fd94f1d2c15640ad13b99ba1821fc9e75191db38cd2f40cdbeb433609d4eb91d`。
两个文件合计 6,182 个不同 UUID，无跨文件 UUID 重复或所选事实冲突。
说明页的 PFAS 3,821、聚酯/聚碳酸酯 383 等汇总不能替代本提交文件的实际行数。

全部源行的密度字段为正有限十进制数，`check_eq` 字面值为 `True`。
这表示源程序报告的状态，不是本项目重新验证平衡、实验成功或性能认证。
两表 `temp` 均为 `300.0`、`press` 均为 `1.0`、力场均为 `GAFF2_mod`；
新增[方法核查](MD_METHOD_NOTES.zh.md)已以固定论文和代码佐证密度单位与常规目标温压，
同时记录了密度统计定义差异及版本链缺项；逐记录窗口与 CSV 聚合仍未知。
软件/预设版本与立构标签逐值保留在[审计结果](source-audit.json)，不将它们计作新身份。

PFAS 表有 942 行包含多组分、多连接点的来源表示，其中可见纤维素衍生物的连接与取代信息。
它们没有进入简单线性重复单元的字面筛选，也没有被删除或自动改类。
多个模拟 UUID、不同立构状态和软件版本可以共享同一个聚合物；它们不是独立材料数。

## 接纳前仍需解决

规范聚合物身份数保持 **未知**。仅字符串去重或计算星号数量不能完成化学身份审核：

- 需要解析连接点、端点反向、原子映射与周期平移，处理非最小重复单元和表示等价性。
- 需要与现有聚合物、牌号和混合物的有限交叉映射，避免把同一材料的状态当新增身份。
- 需要完成逐记录版本链、时间/模拟聚合及条件适用范围。不能把 MD 值改标实验值，
  也不能把 UUID 数量当实物试样数或误差估计。
- 形成冻结候选后需独立来源与身份审阅，再执行运行、历史保留和安装核验。

本包提供了面向每类 1000 目标的可核验聚合物来源储备；它还不证明可新增的独立身份数量。

## 周期图去重原型的实际进展

已在独立工具目录安装固定 RDKit 2025.09.6、NumPy 2.2.6、Pillow 11.3.0，
核对官方 PyPI 摘要；未改变项目运行依赖或共享虚拟环境。

原型对 4,140 个不同单组分源表示进行化学图处理。保留 4,635 个模拟源行，得到
**3,690 个操作性周期图分组**；942 行多组件模型、549 行显式键立体化学、55 行显式
原子立体化学及 1 行离子模型留待专门审阅。源值与条件继续逐 UUID 保留，没有计算新平均值。
3 个源重复单元可由严格开放链重建检查约简；不因非最小单元增加数量。

方法按连接点处理线性重复图，以开放链精确重建确认可约简单元，再比较四重复环图。
端点反向、重复单元边界平移、原子映射和真实同位素均有相应用例。
思路参考 [RadonPy 的公开最小单元化与周期匹配实现](https://github.com/RadonPy/RadonPy/blob/8834b9071ae93d9af36558a3c24545dd52e5ba1a/radonpy/core/poly.py)；
本原型的化学适用范围和等价规则仍需独立审阅。

实际验证为 **9 项图用例通过**，并对全部 3,690 个保留源表示的反向编号及循环编号
进行了 **7,380 次一致性比较，0 失败**。这验证了本批表示变换下的算法一致性，
不能替代无限周期图等价性、化学身份、源方法、基线去重或材料接纳的审核。
规范材料身份数量和可接纳新增数仍未知。完整图索引存放在仓库外，只将
[小型汇总](periodic-graph-summary.json)、[变换核验](relabeling-verification.json)
及[工具来源](tool-provenance.json)保存在这里。

这些附加检查需要向本次进程提供隔离 RDKit 的路径，然后运行：

```sh
python -B -m unittest discover -s experimental/material-batches/quota1000-polyomics-source-audit-20261027 -p test_periodic_repeat_graph.py -v
python -B experimental/material-batches/quota1000-polyomics-source-audit-20261027/normalize_polyomics.py --cache PATH_TO_VERIFIED_EXTERNAL_CACHE --output-dir PATH_TO_NEW_EXTERNAL_GRAPH_DIRECTORY
python -B experimental/material-batches/quota1000-polyomics-source-audit-20261027/verify_periodic_invariance.py --index PATH_TO_GRAPH_INDEX --summary PATH_TO_GRAPH_SUMMARY --output PATH_TO_NEW_VERIFICATION
```

## 复现和实际检查

```sh
python -B experimental/material-batches/quota1000-polyomics-source-audit-20261027/inspect_polyomics.py --cache PATH_TO_VERIFIED_EXTERNAL_CACHE --output PATH_TO_NEW_AUDIT_JSON
python -B -m unittest discover -s experimental/material-batches/quota1000-polyomics-source-audit-20261027 -p test_inspect_polyomics.py -v
```

实际检查：**7 项通过、0 失败、0 跳过**。覆盖 CSV 列结构、数值/UUID 原文保留、
非法/缺失值、源平衡标签与身份计数边界。化学规范化和独立审阅未运行。
首次命令因编码名称拼写错误失败，修正后重跑成功，见 [VALIDATION.json](VALIDATION.json)。
原始文件及许可说明的摘要见[下载收据](download-receipt.json)、
[聚酯收据](polyester-download-receipt.json)与[来源证据](source-evidence.json)。
