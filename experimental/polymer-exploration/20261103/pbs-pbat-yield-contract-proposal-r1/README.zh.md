# 既有PBS/PBAT材料：屈服强度来源与字段提案

Mtibe等（2022），[DOI 10.3390/polym14235065](https://doi.org/10.3390/polym14235065)，[原文XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9739168/fullTextXML)，117806字节，SHA-256 `aa495787abc73a0d98b8c8adbb3c887816afe57076873010b04d41a6730b7f32`，文章CC BY4.0。本轮不捆绑原文或补充资料，不声明新PDF视觉核对。

Table 3的明确表头为 **Tensile Strength at Yield (MPa)**，不应填成最大拉伸强度、断裂应力或Young模量。对应两个已有聚合物状态：PBAT为8.38±0.11 MPa，PBS/PBAT(70/30)为26.99±0.32 MPa。其他来源行不新增身份或候选；本提案不带入3个复合材料行。

§2.6.2给出每组5试样、25°C测试、测试前25°C/48h条件处理及作者声明ASTM D638。未给出数值加载速率、RH、精确屈服判据/偏移量、标准版本或独立批次数。原文选中段落没有定义机械±的统计构造或中心值汇总方式，继续使用reported_value及reported_plus_minus_unspecified，不推为均值±SD、SE或CI。其他测试的平均扫描次数或粒径不借用。

## 拟增量契约

提议新增 `tensile_yield_strength`，维度pressure，仅表示来源明确标注的拉伸屈服强度。现有 `tensile_strength` 不因本提案被扩义；所有既有值与类别不重标。来源未报告屈服判据时，`additional_conditions.yield_criterion`明确未知，不自动补0.2%偏移、上/下屈服、比例极限或工程许用值。

原生字段结构继续1.0，拟做quantity枚举的增量扩展，并由现有定义生成公开schema；实际受影响文件需在实现时检查，不能以提案代替已验证实现。新量仅支持catalog_only，仍非普适界/工程许用值，不自动进入线弹性引擎或做安全系数推导。力学维度相同不等于量的物理定义相同。

实施必须分别验证压力单位、类型/统计/未知条件、导出与查询对新量的完整保留、旧目录兼容性，并独审具体补丁及冻结映射。当前仅为来源事实与契约提案，**尚未修改枚举、schema、原生记录或机械计算器**，未跑此新量的图检查，未推送。

`SOURCE_FACTS_R1.json`中的两个映射只复用既有身份/状态，并与同一来源的旧模量数值核对以确认行对应。旧模量及其未定义±全部保持，不将屈服数据复制到旧属性。PHBV原文直到yield的方法与表中通用strength标签也不能自动套用本提案；其强度在获得明确分类前不收录。
