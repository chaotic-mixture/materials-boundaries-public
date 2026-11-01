# PolyOmics：1000 条聚合物计算密度来源事实提案

状态：**已冻结来源事实；化学身份、方法与基线重叠尚未独立审阅；接纳增量为零。**
这不是原生运行包，`handoff_ready=false`。不得把 1000 个操作性图键当已接纳材料。
当前 JARVIS 完整回归输入保持冻结，本包只写 experimental 与外部缓存。

作者数据：[RadonPy Consortium / PolyOmics，DOI 10.57967/hf/7475](https://doi.org/10.57967/hf/7475)，
固定提交 `cbab9483395a32dd968fbeb047808031fb0f3a13`；
[固定作者说明](https://huggingface.co/datasets/yhayashi1986/PolyOmics/blob/cbab9483395a32dd968fbeb047808031fb0f3a13/README.md)
明确给数据集标记 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。
修改说明：选取公开计算 PFAS 表的事实、按待审周期图方法分组并选最小 UUID 代表，
保留原标量、条件及未知项，没有计算新均值，不暗示作者认可。
许可不从软件推断；PoLyInfo 实验验证数据及小分子子集不在本次取得范围。

## 固定输入与实际选择

- `PFAS.csv` 原始 5810 行，SHA-256
  `2e80ce549bd6c6e4dfc765d842416278a18422d169859939dd88ec41b61c5529`。
- 既有未独立审阅的完整周期图索引 SHA-256
  `2ca48363c749d58a84fb23b0c1a6a76d84a4cd51905b7367a0ce18f75a5a027d`。
- [冻结事实](source-fact-candidates.json) SHA-256
  `3e89ef4c7b7b41c99acbc330f53b0d6a00f44aa9216dfdbe03f47eb1959e5b61`。
- [37 个现有聚合物交叉核验输入](baseline-polymer-crosswalk.json)，包含身份、牌号与状态
  组成范围，尚不是“不重叠”结论。基线来自包含待验 JARVIS 追加的工作图，但聚合物仍为 37。

筛选固定 RadonPy `0.2.10`、eq preset `0.2.1`、GAFF2_mod、源温压 token `300.0/1.0`、
`check_eq=True`，要求重复图有 F 原子，并对源 nematic order parameter 作有限 0–0.1
筛选。得到 **2019 个源记录、1789 个操作性图组**；阈值是本批明示的筛选规则，
不是独立的平衡、各向同性或收敛认证。

按图键字典序取前 1000 组，每组取符合队列的最小 UUID；不按密度高低选择，
不平均重复行。每条保留源 UUID、SMILES、源密度字面值、原始条件、输入链/原子/分子数、
`ini_density`、软件版本、电荷/量化方法及源字段摘要。数据记录号明确区分 0 基索引和
不含表头的 1 基记录号；字段规范化 JSON 摘要不是原始 CSV 行字节摘要。

## 尚未解决的科学门槛

周期图键继承[原型与现有有限验证](../quota1000-polyomics-source-audit-20261027/README.md)，
不是已经证明的无限周期聚合物规范身份。显式立体化学、多组分、离子净电荷及不支持连接
形式的适用范围须独立核验；不能把 UUID、状态、立构标签或软件版本计成新材料。

[分子模拟密度契约提案](MD_DENSITY_CONTRACT.zh.md)尚未实现或批准。论文的 `m/mean(V)`
与代码的瞬时密度滑动平均存在定义差异；逐记录实际 CSV 聚合、窗口、生成提交、
空白 LAMMPS 版本及 preset 版本关系均保持未知。源模拟链数不是独立实物试样数。
300 K、1 atm 仅有来源工作流与源字段的相互佐证，不是实际轨迹核验。

## 已做的生产者验证

八项来源/选择检查通过，0 失败、0 跳过；包括所有 1000 条原始字段及记录号、
另写的队列/最小 UUID 复算、F 原子/单组分/净电荷/连接点范围、引用许可随包携带，
以及完整选择与交叉核验输入的逐字节重放。这些是同一生产者的测试，不是独立审阅。

最初两个生产者版本已无损保存在 `producer-r1/`、`producer-r2/`；后续版本增加了原表
`ini_density` 输入 token、随包署名许可及固定来源说明/解析器摘要检查，没有改变源密度。
[验证收据](VALIDATION.json)与[审阅范围清单](REVIEW_MANIFEST.json)固定当前文件。

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH='PATH_TO_ISOLATED_RDKIT_SITE_PACKAGES'
python -B select_source_candidates.py --cache PATH_TO_FIXED_POLYOMICS_CACHE
python -B -m unittest discover -s . -p test_source_candidates.py -v
```
