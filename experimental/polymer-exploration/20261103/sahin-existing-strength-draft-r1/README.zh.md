# Şahin 2026：五个既有打印聚合物状态的强度补充

来源：Anıl Şahin，*Integrated Evaluation of Electrical Breakdown Strength and Mechanical Properties of 3D-Printed Polymers, Supplemented by ImageJ-Based Surface Damage Analysis*（2026），[DOI 10.3390/polym18111345](https://doi.org/10.3390/polym18111345)。

本轮重新取得 [原文 XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13259274/fullTextXML)，128622字节，SHA-256 `0570b4cad935fcbf7363999960e40333d6a46fd2d113b3c9f87e7da9c4a9e7d3`，与原生登记一致。核对 §§2.1–2.3、Tables 2–4、统计说明和文章 CC BY 4.0 权限。无新 PDF 页图检查、原始数据重分析或独立审阅；原文资产保留在仓库外。

## 调湿缺口的结论

原文仅报告打印前丝材干燥：PLA 50°C/6h，ABS 65°C/10h，PETG 60°C/6h，ASA与PC/ABS各65°C/10h。打印后试样的调湿、存放间隔和湿度仍未知。打印环境23°C与拉伸测试23°C分别有原文声明；不把喷嘴、热床、打印腔或干燥温度填作测试温度。原有5条模量的未知调湿字段保持不变。

## 本轮新增草案

Table 4 的 s_M 是作者报告的 tensile strength，与 s_B stress at break 分列。下面为5个既有状态补充强度，不新建身份、牌号、状态或来源，不以供应商 Table 1 替代实验值。

| 来源材料组 | s_M 均值 ± SD / MPa |
| --- | --- |
| PLA | 46.44 ± 0.36 |
| ABS | 34.46 ± 0.42 |
| PETG | 38.63 ± 0.76 |
| ASA | 32.32 ± 0.60 |
| PC/ABS | 33.10 ± 0.77 |

§2.3和Table 4明确n=5、均值和SD；不是5个已知生产批次，不将SD转换为CI。测试使用Zwick/Roell Z020、10kN载荷元、5.0 mm/min横梁速率，作者声明ASTM D638-14；不自行认证符合性或换算应变率。SKU、批号、颜色、成分/添加物、打印方向与栅格方向关系、伸长测量细节、应力归约实现及调湿仍按未知处理。100%切片填充不是零孔隙率证明。

原文§3.1的断裂伸长表号引用疑点保留；本草案按Table 4选中强度单元格。s_B、E_Sec、断裂伸长、电击穿及表面损伤数据均未混入本次强度草案。

`build_draft.py` 先核对原有5条模量的均值/SD，再提取s_M而非s_B；5个状态只修订反向性质链接和补丁版本。既有性质、身份、牌号和来源对象全部保持不变。`frozen-r1/VALIDATION_R1.json` 记录独立预览5206条性质的当前图检查通过；这不是组合r2的数量，也不改变原生5201条性质的基线。完整历史回归未运行。

**状态：冻结草案，待独立审阅，未应用、未接纳、未推送。** 此前授权不自动扩展到本来源；本轮未启动子代理。审核应重点核对五组状态、s_M/s_B分离、调湿未知及原记录保留情况。
