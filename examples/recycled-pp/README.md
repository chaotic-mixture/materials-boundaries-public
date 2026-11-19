# 再生 PP 复合材料的拉伸强度比较

在仓库根目录运行 `python examples/recycled-pp/compare.py`。数据来自 García 与 Febres 的[原文表 2](https://doi.org/10.3390/polym18111384)，随案例提供。

两组均为消费后再生 PP 与玉米秸秆纤维，每组五个试件。纤维质量分数由 10% 增至 30% 时，平均拉伸强度从 14.56 ± 0.42 MPa 变为 12.96 ± 1.30 MPa（均值 ± SD）。程序核对来源、基体、纤维、工艺、性质、单位和统计量，列出相同条件、冲突与缺项。可比时返回后组减前组的均值差。独立制备批次与孔隙率的证据不足，结论限于该研究试样。
## 跨来源比较

从仓库根目录运行 `python examples/recycled-pp/compare_sources.py strength` 或将参数改为 `strain`。前者并列 García 的 Corn10 与 Cunha 的 CS10：[García & Febres](https://doi.org/10.3390/polym18111384) 和 [Cunha et al.](https://doi.org/10.3390/polym18222856)。两者同为名义 10 wt.% 且量为拉伸强度，但树脂流、是否含 MAPP、填料身份、混炼/成型路线、标准版本和加载速率均不同；批次也未报告。因此只展示来源值，不把均值差解释为材料或 MAPP 的因果效应。两文的 n=5 与 n=10 都是试件数，不能当作独立配混批数。

`strain` 案例保留 García Table 2 的原标签 “Max. Elongation”，与 Cunha 的 “Nominal strain at tensile strength” 比较。端点没有对齐，García 值不自动改称断裂伸长；程序应明确拒绝直接比较数值。García 的拉伸方法为 ASTM D638-03、5.5 mm/min，Cunha 为 ASTM D638-22、1 mm/min，且 Cunha 的名义应变由横梁位移估算。Cunha 的 S1 数值仍是待独立审核的研究转录，输出须保留此状态。
